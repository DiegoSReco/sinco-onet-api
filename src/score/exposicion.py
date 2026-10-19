"""Metodo de exposicion (decision 001 sec. 4.3-4.5; rubrica v1). Funciones puras + CLI.

Cadena: anotaciones (clase por tarea) -> e_t (mapa de configuracion) -> E_o por O*NET-SOC
(por corrida) -> E_SINCO por crosswalk (por corrida) -> resumen entre corridas (PROVISIONAL).

Reglas: ningun numero se escribe a mano aqui; el mapa E0/E1/E2 se lee de src/annotate/config.toml;
los umbrales viven en src/score/config.toml. El CLI se niega a correr sobre el piloto salvo
--permitir-piloto (y entonces rotula 'PILOTO, NO RESULTADO'). No usa Frey-Osborne.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import tomllib
import typing
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pydantic import BaseModel, ConfigDict, ValidationError, create_model

from src.annotate import config as acfg
from src.annotate import schemas

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = Path(__file__).with_name("config.toml")
RUBRICA_PATH = ROOT / "docs" / "rubric.md"
CLASES = ("E0", "E1", "E2")


class EsquemaIncumplido(Exception):
    """Un entregable de entrada no cumple su esquema (regla 5: issue y detenerse)."""


class PilotoNoPermitido(Exception):
    """Las anotaciones son piloto y no se pasó --permitir-piloto."""


# --------------------------------------------------------------------------- configuracion
def cargar_config(path: Path | str = CONFIG_PATH) -> dict:
    with open(path, "rb") as f:
        cfg = tomllib.load(f)
    for sec in ("mapa", "rutas", "agregacion_onet", "entre_corridas", "cobertura", "crosswalk", "piloto"):
        if sec not in cfg:
            raise ValueError(f"config score: falta la seccion [{sec}]")
    for k in ("umbral_tareas_onet", "umbral_onet_sinco"):
        if not 0 <= cfg["cobertura"][k] <= 1:
            raise ValueError(f"config score: cobertura.{k} debe estar en [0, 1]")
    return cfg


def cargar_mapas(cfg: dict) -> dict[str, dict[str, float]]:
    """Mapa numerico desde la configuracion de annotate (no se copia a codigo)."""
    a = acfg.cargar(ROOT / cfg["mapa"]["fuente"])
    sec = a[cfg["mapa"]["seccion"]]
    mapas = {n: dict(sec[cfg["mapa"][n]]) for n in ("principal", "inferior", "superior")}
    for n, m in mapas.items():
        if set(m) != set(CLASES):
            raise ValueError(f"mapa {n}: claves distintas de {CLASES}")
    return mapas


def version_rubrica(path: Path = RUBRICA_PATH) -> str:
    """Version de la rubrica, leida del encabezado de docs/rubric.md ('versión N')."""
    primera = Path(path).read_text(encoding="utf-8-sig").splitlines()[0]
    m = re.search(r"vers\w+\s+(\d+)", primera)
    if not m:
        raise ValueError(f"no se pudo leer la version de la rubrica en {path}")
    return m.group(1)


# --------------------------------------------------------------------------- (1) carga
def _expandir(rutas) -> list[Path]:
    out: list[Path] = []
    for r in ([rutas] if isinstance(rutas, (str, Path)) else list(rutas)):
        p = Path(r)
        out.extend(sorted(p.glob("run_*.parquet")) if p.is_dir() else [p])
    if not out:
        raise FileNotFoundError("no se encontraron archivos de anotaciones")
    return out


def cargar_anotaciones(rutas) -> pd.DataFrame:
    """Lee una o varias corridas (esquema Annotation) y valida el esquema y la coherencia.

    Falla con EsquemaIncumplido si: una fila no cumple Annotation; hay (run_id, task_id) repetido
    entre archivos; o un run_id tiene metadatos de corrida inconsistentes.
    """
    frames = []
    for p in _expandir(rutas):
        try:
            recs = schemas.read_parquet(p)
        except (ValidationError, ValueError, OSError, pa.ArrowException) as e:
            raise EsquemaIncumplido(f"{p}: {e}") from e
        frames.append(pd.DataFrame([r.model_dump() for r in recs]))
    ann = pd.concat(frames, ignore_index=True)
    dup = ann.duplicated(["run_id", "task_id"], keep=False)
    if dup.any():
        raise EsquemaIncumplido(f"(run_id, task_id) repetido entre archivos: {ann.loc[dup, ['run_id', 'task_id']].drop_duplicates().values.tolist()[:5]}")
    for col in ("prompt_version", "prompt_sha256", "model", "run_date", "onet_version"):
        malos = ann.groupby("run_id")[col].nunique()
        if (malos > 1).any():
            raise EsquemaIncumplido(f"{col} inconsistente dentro de run_id: {list(malos[malos > 1].index)}")
    return ann


def cargar_pesos_ratings(ratings: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Ancho (onet_soc, task_id, peso_im, peso_rt) desde tareas_onet_ratings (escalas de configuracion)."""
    a = cfg["agregacion_onet"]
    esc = {a["escala_importancia"]: "peso_im", a["escala_relevancia"]: "peso_rt"}
    r = ratings[ratings["scale_id"].isin(esc)]
    if a["excluir_recommend_suppress"]:
        r = r[r["recommend_suppress"].fillna("N") != "Y"]
    if r.duplicated(["onet_soc_code", "task_id", "scale_id"]).any():
        raise EsquemaIncumplido("ratings: escala repetida para una misma (onet_soc, tarea)")
    w = r.pivot(index=["onet_soc_code", "task_id"], columns="scale_id", values="data_value").rename(columns=esc)
    for c in esc.values():
        if c not in w:
            w[c] = np.nan
    return w.reset_index().rename(columns={"onet_soc_code": "onet_soc"})[["onet_soc", "task_id", "peso_im", "peso_rt"]]


# --------------------------------------------------------------------------- (2) puntaje por tarea
def puntaje_tarea(clases: pd.Series, mapa: dict[str, float]) -> pd.Series:
    """e_t = mapa[exposure_class]. Falla ante una clase fuera del mapa (no imputa)."""
    desconocidas = set(clases.dropna().unique()) - set(mapa)
    if desconocidas or clases.isna().any():
        raise ValueError(f"clases fuera del mapa o nulas: {sorted(desconocidas)}")
    return clases.map(mapa).astype(float)


def agregar_puntajes_tarea(ann: pd.DataFrame, mapas: dict[str, dict[str, float]]) -> pd.DataFrame:
    """Agrega e_t (principal), e_t_inf y e_t_sup."""
    out = ann.copy()
    out["e_t"] = puntaje_tarea(out["exposure_class"], mapas["principal"])
    out["e_t_inf"] = puntaje_tarea(out["exposure_class"], mapas["inferior"])
    out["e_t_sup"] = puntaje_tarea(out["exposure_class"], mapas["superior"])
    return out


def promedio_ponderado(valores, pesos=None) -> float:
    """sum(w*e)/sum(w); pesos iguales si pesos es None. NaN si no hay datos o sum(w) = 0."""
    v = np.asarray(valores, dtype=float)
    if v.size == 0:
        return float("nan")
    w = np.ones_like(v) if pesos is None else np.asarray(pesos, dtype=float)
    if w.shape != v.shape or (w < 0).any():
        raise ValueError("pesos incompatibles o negativos")
    s = w.sum()
    return float((w * v).sum() / s) if s > 0 else float("nan")


# --------------------------------------------------------------------------- esquemas de salida
class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class OnetRow(_Base):
    """Exposicion por O*NET-SOC, por corrida."""
    run_id: str
    prompt_version: str
    prompt_sha256: str
    model: str
    run_date: dt.date
    onet_version: str
    rubrica_version: str
    onet_soc: str
    n_universo: Optional[int]          # tareas O*NET de la ocupacion (universo), None si no se dio
    n_anotadas: int
    n_core: int
    n_supplemental: int
    n_sin_tipo: int
    cobertura_tareas: Optional[float]  # n_anotadas / n_universo
    E_o: Optional[float]               # principal: core, pesos iguales, mapa principal
    E_o_inferior: Optional[float]
    E_o_superior: Optional[float]
    E_o_todas: Optional[float]         # variante: core + suplementarias + sin tipo
    E_o_pond_im: Optional[float]       # variante PROVISIONAL: core ponderado por IM [NO VERIFICADO en 001]
    E_o_pond_rt: Optional[float]       # variante PROVISIONAL: core ponderado por RT [NO VERIFICADO en 001]
    n_core_con_peso_im: int
    n_core_con_peso_rt: int
    share_E2: Optional[float]          # sobre tareas core
    share_any: Optional[float]         # E1 o E2, sobre tareas core
    motivo_na: Optional[str]
    etiqueta: str


class SincoRow(_Base):
    """Exposicion por grupo unitario SINCO, por corrida."""
    run_id: str
    prompt_version: str
    model: str
    run_date: dt.date
    rubrica_version: str
    sinco_code: str
    E_sinco: Optional[float]           # media uniforme de E_o de las O*NET emparejadas elegibles
    E_sinco_min: Optional[float]       # cota de ambiguedad del crosswalk
    E_sinco_max: Optional[float]
    E_sinco_inferior: Optional[float]
    E_sinco_superior: Optional[float]
    E_sinco_todas: Optional[float]
    share_E2: Optional[float]
    share_any: Optional[float]
    n_onet_mapped: int                 # O*NET emparejadas (sin pares excluidos por match_status)
    n_onet_con_anotacion: int          # de ellas, elegibles (E_o definido y cobertura >= umbral)
    cobertura_onet: Optional[float]    # n_onet_con_anotacion / n_onet_mapped
    umbral_cobertura: float
    crosswalk_type: str
    crosswalk_confidence: str          # derivado de match_status del crosswalk (ok / baja_confianza / sin_coincidencia)
    peso_crosswalk: str
    motivo_na: Optional[str]
    etiqueta: str


_VAR_ONET = ("E_o", "E_o_inferior", "E_o_superior", "share_E2", "share_any")
_VAR_SINCO = ("E_sinco", "E_sinco_min", "E_sinco_max", "E_sinco_inferior", "E_sinco_superior", "share_E2", "share_any")


def _modelo_resumen(nombre: str, clave: str, cols: tuple[str, ...], extras: dict) -> type[BaseModel]:
    campos: dict = {clave: (str, ...), "n_corridas": (int, ...), "n_corridas_con_valor": (int, ...),
                    "run_ids": (str, ...), "prompt_versions": (str, ...), "modelos": (str, ...),
                    "rubrica_version": (str, ...), "estado_agregacion": (str, ...), "etiqueta": (str, ...)}
    for c in cols:
        for suf in ("media", "min", "max"):
            campos[f"{c}_{suf}"] = (Optional[float], ...)
    campos.update(extras)
    return create_model(nombre, __base__=_Base, **campos)


OnetResumen = _modelo_resumen("OnetResumen", "onet_soc", _VAR_ONET, {})
SincoResumen = _modelo_resumen("SincoResumen", "sinco_code", _VAR_SINCO, {
    "n_onet_mapped": (int, ...), "crosswalk_type": (str, ...), "crosswalk_confidence": (str, ...),
    "cobertura_onet_min": (Optional[float], ...)})


def _tipo_arrow(ann) -> pa.DataType:
    args = [a for a in typing.get_args(ann) if a is not type(None)]
    base = args[0] if args else ann
    return {str: pa.string(), int: pa.int64(), float: pa.float64(), bool: pa.bool_(), dt.date: pa.date32()}[base]


def arrow_schema(modelo: type[BaseModel]) -> pa.Schema:
    return pa.schema([(n, _tipo_arrow(f.annotation)) for n, f in modelo.model_fields.items()])


def _registros(df: pd.DataFrame, modelo: type[BaseModel]) -> list[dict]:
    """Valida cada fila contra el modelo pydantic (NaN -> None)."""
    limpio = df.astype(object).where(df.notna(), None)
    return [modelo(**r).model_dump() for r in limpio.to_dict("records")]


def a_tabla(df: pd.DataFrame, modelo: type[BaseModel]) -> pa.Table:
    sch = arrow_schema(modelo)
    recs = _registros(df[list(modelo.model_fields)], modelo)
    return pa.table({n: [r[n] for r in recs] for n in sch.names}, schema=sch)


# --------------------------------------------------------------------------- (3) O*NET por corrida
def agregar_onet(ann_run: pd.DataFrame, mapas: dict, cfg: dict, universo: Optional[pd.DataFrame] = None,
                 pesos: Optional[pd.DataFrame] = None, etiqueta: str = "") -> pd.DataFrame:
    """E_o por O*NET-SOC para UNA corrida (001 4.4). Devuelve una fila por ocupacion.

    universo: columnas onet_soc_code, task_id (todas las tareas O*NET); da n_universo y cobertura, e incluye
    ocupaciones sin ninguna tarea anotada (motivo_na='sin_anotacion'). pesos: salida de cargar_pesos_ratings.
    """
    if ann_run["run_id"].nunique() != 1:
        raise ValueError("agregar_onet recibe exactamente una corrida")
    tipo = cfg["agregacion_onet"]["tipo_principal"]
    a = agregar_puntajes_tarea(ann_run, mapas)
    if pesos is not None:
        a = a.merge(pesos, on=["onet_soc", "task_id"], how="left")
    for c in ("peso_im", "peso_rt"):
        if c not in a:
            a[c] = np.nan
    n_univ = None
    if universo is not None:
        n_univ = universo.groupby("onet_soc_code")["task_id"].nunique()
        fuera = set(a["onet_soc"]) - set(n_univ.index)
        if fuera:
            raise ValueError(f"ocupaciones anotadas fuera del universo: {sorted(fuera)[:5]}")
    meta = {k: a[k].iloc[0] for k in ("run_id", "prompt_version", "prompt_sha256", "model", "run_date", "onet_version")}
    meta["rubrica_version"] = version_rubrica()
    socs = sorted(set(a["onet_soc"]) | (set(n_univ.index) if n_univ is not None else set()))
    grupos = dict(tuple(a.groupby("onet_soc")))
    filas = []
    for soc in socs:
        g = grupos.get(soc, a.iloc[0:0])
        core = g[g["task_type"] == tipo]
        n_u = int(n_univ[soc]) if n_univ is not None and soc in n_univ.index else None
        fila = {**meta, "onet_soc": soc, "n_universo": n_u, "n_anotadas": len(g), "n_core": len(core),
                "n_supplemental": int((g["task_type"] == "supplemental").sum()),
                "n_sin_tipo": int(g["task_type"].isna().sum()),
                "cobertura_tareas": (len(g) / n_u) if n_u else None, "etiqueta": etiqueta}
        if len(g) and fila["n_anotadas"] != g["task_id"].nunique():
            raise ValueError(f"tareas repetidas en {soc}")
        fila["E_o"] = promedio_ponderado(core["e_t"])
        fila["E_o_inferior"] = promedio_ponderado(core["e_t_inf"])
        fila["E_o_superior"] = promedio_ponderado(core["e_t_sup"])
        fila["E_o_todas"] = promedio_ponderado(g["e_t"])
        for suf in ("im", "rt"):
            c = core[core[f"peso_{suf}"].notna()]
            fila[f"n_core_con_peso_{suf}"] = len(c)
            fila[f"E_o_pond_{suf}"] = promedio_ponderado(c["e_t"], c[f"peso_{suf}"])
        fila["share_E2"] = float((core["exposure_class"] == "E2").mean()) if len(core) else float("nan")
        fila["share_any"] = float(core["exposure_class"].isin(["E1", "E2"]).mean()) if len(core) else float("nan")
        fila["motivo_na"] = None if len(core) else ("sin_anotacion" if len(g) == 0 else "sin_tareas_centrales_anotadas")
        filas.append(fila)
    return pd.DataFrame(filas)


def resumen_entre_corridas(df: pd.DataFrame, clave: str, cols: tuple[str, ...], valor_ref: str,
                           pasan: Optional[dict[str, str]] = None) -> pd.DataFrame:
    """PROVISIONAL: media, minimo y maximo por clave entre corridas (ninguna decision fija el metodo).

    valor_ref: columna cuyo no-nulo define n_corridas_con_valor. pasan: {columna: 'first'|'min'} que se conservan.
    """
    filas = []
    for k, g in df.groupby(clave, sort=True):
        f = {clave: k, "n_corridas": g["run_id"].nunique(), "n_corridas_con_valor": int(g[valor_ref].notna().sum()),
             "run_ids": ";".join(sorted(g["run_id"].unique())),
             "prompt_versions": ";".join(sorted(g["prompt_version"].unique())),
             "modelos": ";".join(sorted(g["model"].unique())),
             "rubrica_version": g["rubrica_version"].iloc[0], "etiqueta": g["etiqueta"].iloc[0]}
        for c in cols:
            v = g[c].dropna()
            f[f"{c}_media"] = float(v.mean()) if len(v) else None
            f[f"{c}_min"] = float(v.min()) if len(v) else None
            f[f"{c}_max"] = float(v.max()) if len(v) else None
        for c, how in (pasan or {}).items():
            f[c] = g[c].iloc[0] if how == "first" else (float(g[c].min()) if g[c].notna().any() else None)
        filas.append(f)
    return pd.DataFrame(filas)


# --------------------------------------------------------------------------- (4) SINCO por corrida
def agregar_sinco(onet_run: pd.DataFrame, crosswalk: pd.DataFrame, cfg: dict, etiqueta: str = "") -> pd.DataFrame:
    """E_SINCO para UNA corrida (001 4.5): media uniforme entre las O*NET emparejadas; min y max como cota.

    Una O*NET es elegible si E_o esta definido y cobertura_tareas >= umbral_tareas_onet. Si la fraccion de
    elegibles entre las emparejadas es menor a umbral_onet_sinco, E_SINCO = NA con motivo_na. Los pares con
    match_status excluido (config) no cuentan como emparejados.
    """
    if onet_run["run_id"].nunique() != 1:
        raise ValueError("agregar_sinco recibe exactamente una corrida")
    if onet_run["cobertura_tareas"].isna().all():
        raise ValueError("se requiere el universo de tareas (cobertura_tareas) para evaluar la cobertura")
    req = {"sinco_code", "onet_soc_code", "tipo_relacion"}
    if not req <= set(crosswalk.columns):
        raise EsquemaIncumplido(f"crosswalk sin columnas {sorted(req - set(crosswalk.columns))}")
    if crosswalk.duplicated(["sinco_code", "onet_soc_code"]).any():
        raise EsquemaIncumplido("crosswalk con pares (sinco_code, onet_soc_code) repetidos")
    cw = crosswalk.copy()
    if "match_status" not in cw:
        cw["match_status"] = "ok"
    cu, ct = cfg["cobertura"]["umbral_onet_sinco"], cfg["cobertura"]["umbral_tareas_onet"]
    excl = set(cfg["crosswalk"]["excluir_match_status"])
    o = onet_run.set_index("onet_soc")
    elegible = o["E_o"].notna() & (o["cobertura_tareas"] >= ct)
    meta = {k: onet_run[k].iloc[0] for k in ("run_id", "prompt_version", "model", "run_date", "rubrica_version")}
    peor = {"ok": 0, "baja_confianza": 1, "sin_coincidencia": 2}
    filas = []
    for sinco, g in cw.groupby("sinco_code", sort=True):
        usados = g[~g["match_status"].isin(excl)]
        ids = list(usados["onet_soc_code"])
        el = [s for s in ids if s in elegible.index and bool(elegible[s])]
        n_map, n_el = len(ids), len(el)
        cob = n_el / n_map if n_map else None
        st = max(g["match_status"], key=lambda s: peor.get(s, 1))
        fila = {**meta, "sinco_code": sinco, "n_onet_mapped": n_map, "n_onet_con_anotacion": n_el,
                "cobertura_onet": cob, "umbral_cobertura": cu,
                "crosswalk_type": ";".join(sorted(g["tipo_relacion"].unique())),
                "crosswalk_confidence": st, "peso_crosswalk": cfg["crosswalk"]["peso"], "etiqueta": etiqueta}
        vacio = dict.fromkeys(("E_sinco", "E_sinco_min", "E_sinco_max", "E_sinco_inferior", "E_sinco_superior",
                               "E_sinco_todas", "share_E2", "share_any"), None)
        if n_map == 0:
            filas.append({**fila, **vacio, "motivo_na": "sin_coincidencia"})
        elif cob < cu:
            filas.append({**fila, **vacio, "motivo_na": "cobertura_insuficiente"})
        else:
            s = o.loc[el]
            filas.append({**fila, "E_sinco": promedio_ponderado(s["E_o"]), "E_sinco_min": float(s["E_o"].min()),
                          "E_sinco_max": float(s["E_o"].max()),
                          "E_sinco_inferior": promedio_ponderado(s["E_o_inferior"]),
                          "E_sinco_superior": promedio_ponderado(s["E_o_superior"]),
                          "E_sinco_todas": promedio_ponderado(s["E_o_todas"]),
                          "share_E2": promedio_ponderado(s["share_E2"]), "share_any": promedio_ponderado(s["share_any"]),
                          "motivo_na": None})
    return pd.DataFrame(filas)


# --------------------------------------------------------------------------- piloto
def detectar_piloto(ann: pd.DataFrame, universo: pd.DataFrame, cfg: dict) -> list[str]:
    """Razones por las que las anotaciones son piloto (lista vacia = corrida completa)."""
    p = cfg["piloto"]
    razones = []
    pref = tuple(p["prefijos_run_id"])
    malos = sorted(r for r in ann["run_id"].unique() if r.lower().startswith(pref))
    if malos:
        razones.append(f"run_id de piloto/prueba: {malos}")
    mods = sorted(set(ann["model"]) & set(p["modelos_no_resultado"]))
    if mods:
        razones.append(f"modelo de prueba: {mods}")
    n_occ = universo["onet_soc_code"].nunique()
    cob_occ = ann["onet_soc"].nunique() / n_occ
    if cob_occ < p["umbral_cobertura_ocupaciones"]:
        razones.append(f"{ann['onet_soc'].nunique()} de {n_occ} ocupaciones con tareas anotadas (umbral {p['umbral_cobertura_ocupaciones']})")
    n_t = universo["task_id"].nunique()
    cob_t = ann["task_id"].nunique() / n_t
    if cob_t < p["umbral_cobertura_tareas"]:
        razones.append(f"{ann['task_id'].nunique()} de {n_t} tareas anotadas (umbral {p['umbral_cobertura_tareas']})")
    return razones


# --------------------------------------------------------------------------- (5) salidas
def _sha256(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def registrar_issue(mensaje: str, issues_dir: Path, hoy: Optional[dt.date] = None) -> Path:
    """Regla 5: entregable fuera de esquema -> issue en docs/issues/."""
    hoy = hoy or dt.date.today()
    p = Path(issues_dir) / f"score-{hoy.isoformat()}-esquema-incumplido.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(f"# Issue: entrada de score fuera de esquema ({hoy.isoformat()})\n\n- {mensaje}\n- Accion: score se detuvo; corregir el entregable.\n\n")
    return p


def ejecutar(anot_rutas, crosswalk_path, universo_path, ratings_path, salida_dir, permitir_piloto: bool = False,
             sobrescribir: bool = False, cfg: Optional[dict] = None) -> dict[str, Path]:
    """Calcula y escribe las tablas. Se niega a correr sobre el piloto salvo permitir_piloto."""
    cfg = cfg or cargar_config()
    ann = cargar_anotaciones(anot_rutas)
    universo = pd.read_parquet(universo_path)[["onet_soc_code", "task_id"]]
    razones = detectar_piloto(ann, universo, cfg)
    if razones and not permitir_piloto:
        raise PilotoNoPermitido("; ".join(razones))
    etiqueta = cfg["piloto"]["etiqueta"] if razones else cfg["piloto"]["etiqueta_normal"]
    sufijo = "_PILOTO" if razones else ""
    salida_dir = Path(salida_dir)
    nombres = {k: salida_dir / f"exposicion_{k}{sufijo}.parquet"
               for k in ("ocupacion_onet", "ocupacion_onet_corridas", "sinco", "sinco_corridas")}
    nombres["meta"] = salida_dir / f"exposicion_meta{sufijo}.json"
    if not sobrescribir and any(p.exists() for p in nombres.values()):
        raise FileExistsError("las salidas ya existen; usar --sobrescribir")

    mapas = cargar_mapas(cfg)
    pesos = cargar_pesos_ratings(pd.read_parquet(ratings_path), cfg)
    cw = pd.read_parquet(crosswalk_path)
    onet_tabs, sinco_tabs = [], []
    for _, run in ann.groupby("run_id", sort=True):
        t = agregar_onet(run, mapas, cfg, universo, pesos, etiqueta)
        onet_tabs.append(t)
        sinco_tabs.append(agregar_sinco(t, cw, cfg, etiqueta))
    onet, sinco = pd.concat(onet_tabs, ignore_index=True), pd.concat(sinco_tabs, ignore_index=True)
    estado = f"{cfg['entre_corridas']['estado']}: {cfg['entre_corridas']['metodo']}"
    r_onet = resumen_entre_corridas(onet, "onet_soc", _VAR_ONET, "E_o")
    r_sinco = resumen_entre_corridas(sinco, "sinco_code", _VAR_SINCO, "E_sinco",
                                     {"n_onet_mapped": "first", "crosswalk_type": "first", "crosswalk_confidence": "first"})
    r_sinco["cobertura_onet_min"] = sinco.groupby("sinco_code")["cobertura_onet"].min().reindex(r_sinco["sinco_code"]).to_numpy()
    for r in (r_onet, r_sinco):
        r["estado_agregacion"] = estado
    tablas = {"ocupacion_onet": (onet, OnetRow), "ocupacion_onet_corridas": (r_onet, OnetResumen),
              "sinco": (sinco, SincoRow), "sinco_corridas": (r_sinco, SincoResumen)}
    salida_dir.mkdir(parents=True, exist_ok=True)
    try:
        for k, (df, modelo) in tablas.items():
            pq.write_table(a_tabla(df, modelo), nombres[k])
    except ValidationError as e:
        raise EsquemaIncumplido(f"salida {k} no cumple su esquema: {e}") from e
    meta = {"etiqueta": etiqueta, "es_piloto": bool(razones), "razones_piloto": razones,
            "generado": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "rubrica_version": version_rubrica(), "run_ids": sorted(ann["run_id"].unique()),
            "prompt_versions": sorted(ann["prompt_version"].unique()), "modelos": sorted(ann["model"].unique()),
            "run_dates": sorted(str(d) for d in ann["run_date"].unique()),
            "onet_versions": sorted(ann["onet_version"].unique()),
            "mapas": mapas, "agregacion_entre_corridas": estado,
            "cobertura": cfg["cobertura"], "config_score_sha256": _sha256(CONFIG_PATH),
            "entradas_sha256": {str(Path(p)): _sha256(p) for p in _expandir(anot_rutas)}
            | {"crosswalk": _sha256(crosswalk_path), "universo_tareas": _sha256(universo_path),
               "ratings": _sha256(ratings_path)},
            "filas": {k: len(v[0]) for k, v in tablas.items()}}
    nombres["meta"].write_text(json.dumps(meta, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return nombres


def main(argv=None) -> int:
    cfg = cargar_config()
    r = cfg["rutas"]
    ap = argparse.ArgumentParser(description="Exposicion por O*NET-SOC y SINCO (decision 001). Se niega a correr sobre el piloto.")
    ap.add_argument("--anotaciones", nargs="+", default=[str(ROOT / r["anotaciones_dir"])],
                    help="archivos run_*.parquet o carpetas con ellos")
    ap.add_argument("--crosswalk", default=str(ROOT / r["crosswalk"]))
    ap.add_argument("--universo-tareas", default=str(ROOT / r["universo_tareas"]))
    ap.add_argument("--ratings", default=str(ROOT / r["ratings"]))
    ap.add_argument("--salida-dir", default=str(ROOT / r["salida_dir"]))
    ap.add_argument("--permitir-piloto", action="store_true",
                    help=f"permite correr sobre el piloto; las salidas se rotulan '{cfg['piloto']['etiqueta']}'")
    ap.add_argument("--sobrescribir", action="store_true")
    a = ap.parse_args(argv)
    try:
        out = ejecutar(a.anotaciones, a.crosswalk, a.universo_tareas, a.ratings, a.salida_dir,
                       a.permitir_piloto, a.sobrescribir, cfg)
    except PilotoNoPermitido as e:
        print(f"RECHAZADO: las anotaciones son piloto ({e}). Use --permitir-piloto para una prueba rotulada.", file=sys.stderr)
        return 2
    except (EsquemaIncumplido, ValidationError) as e:
        p = registrar_issue(str(e)[:500], ROOT / r["issues_dir"])
        print(f"DETENIDO: entrada fuera de esquema; issue en {p}", file=sys.stderr)
        return 3
    except FileExistsError as e:
        print(f"RECHAZADO: {e}", file=sys.stderr)
        return 4
    for k, p in out.items():
        print(f"{k}: {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
