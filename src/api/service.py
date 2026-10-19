"""Capa de servicio de solo lectura: lee los Parquet de data/processed/ y devuelve dicts JSON-serializables.

No escribe nada. No calcula ni expone scores ni exposicion. Unica probabilidad admitida (decision del usuario 2026-10-19):
la probabilidad de automatizacion (Frey-Osborne), rotulada y NO validada, leida de sinco_probabilidad_fo.parquet. Las coincidencias SINCO-O*NET se leen
de data/processed/crosswalk.parquet con un esquema declarado (ver CrosswalkRow); si no existe, estado "pendiente".
"""
from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, ValidationError

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data" / "processed"
RAW = ROOT / "data" / "raw"

MSG_PENDIENTE = "coincidencias pendientes de crosswalk"
# Columnas que jamas se sirven (el proyecto no calcula exposicion en esta etapa).
PROHIBIDAS = re.compile(r"(score|expos|prob|frey|osborne|automat)", re.I)
NIVELES = ["division", "grupo_principal", "subgrupo", "grupo_unitario"]


class CrosswalkRow(BaseModel):
    """Esquema declarado de data/processed/crosswalk.parquet (una fila por par SINCO-O*NET)."""
    model_config = ConfigDict(extra="ignore")
    sinco_code: str = Field(pattern=r"^[1-9][0-9]{0,3}$")
    onet_soc_code: str = Field(pattern=r"^[0-9]{2}-[0-9]{4}\.[0-9]{2}$")
    tipo_relacion: Literal["1:1", "1:N", "N:1", "M:N"]
    fuente: str = Field(min_length=1)
    estado_validacion: Literal["sin_validar", "validado", "rechazado"]
    # opcionales (se muestran si existen)
    isco08_code: Optional[str] = None
    notas: Optional[str] = None
    match_quality: Optional[str] = None
    crosswalk_confidence: Optional[str] = None
    run_id: Optional[str] = None
    # opcionales del emparejamiento por embeddings (005, Metodo A1): similitud coseno, rango, etc. No son probabilidades.
    modelo: Optional[str] = None
    rango: Optional[int] = None
    similitud: Optional[float] = None
    margen: Optional[float] = None
    similitud_alt: Optional[float] = None
    rango_alt: Optional[int] = None
    modelo_alt: Optional[str] = None
    baja_confianza: Optional[bool] = None
    match_status: Optional[str] = None


CROSSWALK_REQUERIDAS = ["sinco_code", "onet_soc_code", "tipo_relacion", "fuente", "estado_validacion"]
CROSSWALK_OPCIONALES = ["isco08_code", "notas", "match_quality", "crosswalk_confidence", "run_id", "modelo", "rango", "similitud",
                        "margen", "similitud_alt", "rango_alt", "modelo_alt", "baja_confianza", "match_status"]


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", str(s).lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def _records(df: pd.DataFrame) -> list[dict]:
    """DataFrame -> lista de dicts con NaN/NA -> None y tipos nativos."""
    return json.loads(df.to_json(orient="records", force_ascii=False))


@lru_cache(maxsize=None)
def _tabla(nombre: str) -> pd.DataFrame:
    return pd.read_parquet(PROC / f"{nombre}.parquet")


def limpiar_cache() -> None:
    _tabla.cache_clear()
    _sinco_idx.cache_clear()


@lru_cache(maxsize=1)
def _sinco_idx() -> pd.DataFrame:
    return _tabla("sinco").set_index("sinco_code", drop=False)


# ---------------------------------------------------------------- crosswalk
def crosswalk_estado() -> dict:
    """Lee y valida crosswalk.parquet. Nunca inventa filas."""
    ruta = PROC / "crosswalk.parquet"
    base = {"archivo": "data/processed/crosswalk.parquet", "columnas_requeridas": CROSSWALK_REQUERIDAS,
            "columnas_opcionales": CROSSWALK_OPCIONALES}
    if not ruta.exists():
        return {**base, "estado": "pendiente", "mensaje": MSG_PENDIENTE, "n_filas": 0, "_rows": []}
    df = pd.read_parquet(ruta)
    ignoradas = [c for c in df.columns if PROHIBIDAS.search(c)]
    faltan = [c for c in CROSSWALK_REQUERIDAS if c not in df.columns]
    if faltan:
        return {**base, "estado": "esquema_invalido", "mensaje": f"faltan columnas: {faltan}", "n_filas": 0, "_rows": []}
    df = df.drop(columns=ignoradas)
    cols = [c for c in CROSSWALK_REQUERIDAS + CROSSWALK_OPCIONALES if c in df.columns]
    rows = _records(df[cols])
    try:
        for r in rows:
            CrosswalkRow(**r)
    except ValidationError as e:
        return {**base, "estado": "esquema_invalido", "mensaje": f"fila invalida: {e.errors()[0]['msg']}", "n_filas": 0, "_rows": []}
    ok_s = set(_tabla("sinco")["sinco_code"]); ok_o = set(_tabla("onet_ocupaciones")["onet_soc_code"])
    if any(r["sinco_code"] not in ok_s or r["onet_soc_code"] not in ok_o for r in rows):
        return {**base, "estado": "esquema_invalido", "mensaje": "hay codigos que no existen en sinco/onet_ocupaciones", "n_filas": 0, "_rows": []}
    out = {**base, "estado": "disponible", "mensaje": "", "n_filas": len(rows), "_rows": rows}
    if ignoradas:
        out["columnas_ignoradas"] = ignoradas
    return out


def crosswalk(sinco_code: str | None = None, onet_soc_code: str | None = None) -> dict:
    e = crosswalk_estado()
    rows = [r for r in e.pop("_rows") if (not sinco_code or r["sinco_code"] == sinco_code)
            and (not onet_soc_code or r["onet_soc_code"] == onet_soc_code)]
    if rows:
        tit = _tabla("onet_ocupaciones").set_index("onet_soc_code")["titulo_en"]
        rows = [{**r, "onet_titulo": tit.get(r["onet_soc_code"])} for r in rows]
    e["filas"] = rows
    e["filtro"] = {"sinco_code": sinco_code, "onet_soc_code": onet_soc_code}
    if e["estado"] == "disponible" and any(str(r["fuente"]).lower() not in ("inegi",) for r in rows):
        e["aviso"] = "Coincidencias no oficiales: ver 'fuente' y 'estado_validacion' de cada fila."
    return e


def crosswalk_schema() -> dict:
    return {"estado_actual": crosswalk_estado()["estado"], "requeridas": CROSSWALK_REQUERIDAS,
            "opcionales": CROSSWALK_OPCIONALES, "json_schema": CrosswalkRow.model_json_schema(),
            "nota": "No se admiten columnas de score, exposicion ni probabilidad; si aparecen se ignoran."}


# ---------------------------------------------------------------- meta / health
def health() -> dict:
    return {"ok": True}


def meta() -> dict:
    f = _tabla("sinco_fuente").iloc[0]
    manifest = json.loads((RAW / "manifest.json").read_text(encoding="utf-8")) if (RAW / "manifest.json").exists() else []
    onet = next((m for m in manifest if m.get("id", "").startswith("onet")), {})
    cw = crosswalk_estado()
    pe = probabilidad_estado()
    tablas = {n: int(len(_tabla(n))) for n in ["sinco", "sinco_descripcion", "sinco_ocupaciones_ejemplo", "sinco_funciones",
                                               "sinco_incluye_excluye", "sinco_referencias", "onet_ocupaciones", "tareas_onet_en"]}
    s = _tabla("sinco")
    return {"sinco": {"documento": f["documento"], "url": f["url"], "sha256": f["sha256"], "fecha_descarga": f["fecha_descarga"],
                      "niveles": {n: int((s["nivel"] == n).sum()) for n in NIVELES}},
            "onet": {"version": onet.get("version"), "url": onet.get("url"), "sha256": onet.get("sha256"),
                     "fecha_descarga": onet.get("fecha_descarga")},
            "crosswalk": {"estado": cw["estado"], "mensaje": cw["mensaje"], "n_filas": cw["n_filas"]},
            "probabilidad_automatizacion_fo": {k: pe[k] for k in ("estado", "mensaje", "etiqueta", "estado_validacion", "modelo_principal", "modelos_disponibles", "n_filas")},
            "tablas": tablas,
            "atribucion": ATRIBUCION_DESCARGA + " Solo lectura; sin exposicion."}


# ---------------------------------------------------------------- SINCO
@lru_cache(maxsize=1)
def sinco_tree() -> dict:
    s = _tabla("sinco").sort_values("orden")
    nodes = {r.sinco_code: {"c": r.sinco_code, "t": r.titulo, "n": int(r.nivel_num), "ch": []} for r in s.itertuples()}
    roots = []
    for r in s.itertuples():
        (nodes[r.padre]["ch"] if isinstance(r.padre, str) else roots).append(nodes[r.sinco_code])
    return {"nombre": "SINCO 2019", "niveles": NIVELES, "n_nodos": len(nodes), "raices": roots}


def sinco_detail(code: str) -> dict | None:
    idx = _sinco_idx()
    if code not in idx.index:
        return None
    n = idx.loc[code]
    anc, p = [], n["padre"]
    while isinstance(p, str):
        a = idx.loc[p]
        anc.insert(0, {"sinco_code": p, "titulo": a["titulo"], "nivel": a["nivel"]})
        p = a["padre"]
    hijos = idx[idx["padre"] == code].sort_values("orden")
    d = _tabla("sinco_descripcion"); d = d[d["sinco_code"] == code]
    oc = _tabla("sinco_ocupaciones_ejemplo"); oc = oc[oc["sinco_code"] == code].sort_values("orden")
    fu = _tabla("sinco_funciones"); fu = fu[fu["sinco_code"] == code].sort_values("orden")
    ie = _tabla("sinco_incluye_excluye"); ie = ie[ie["sinco_code"] == code].sort_values(["tipo", "orden"])
    rf = _tabla("sinco_referencias"); rf = rf[rf["sinco_code"] == code]
    refs = {}
    for r in rf.itertuples():
        refs.setdefault((r.tipo, int(r.orden)), []).append(
            {"codigo": r.codigo_referido, "titulo": idx.loc[r.codigo_referido, "titulo"] if r.codigo_referido in idx.index else None,
             "existe_en_catalogo": bool(r.codigo_valido)})
    items_ie = [{"tipo": r.tipo, "orden": int(r.orden), "texto": r.texto, "pagina_pdf": int(r.pdf_page),
                 "afectado_por_errata": bool(r.afectado_por_errata), "referencias": refs.get((r.tipo, int(r.orden)), [])}
                for r in ie.itertuples()]
    er = _tabla("sinco_fe_erratas"); er = er[er["sinco_code"] == code]
    de = d.iloc[0] if len(d) else None
    return {
        "nodo": {"sinco_code": code, "titulo": n["titulo"], "nivel": n["nivel"], "padre": n["padre"] if isinstance(n["padre"], str) else None,
                 "pagina_pdf_estructura": int(n["pdf_page_estructura"])},
        "ancestros": anc,
        "hijos": [{"sinco_code": r.sinco_code, "titulo": r.titulo, "nivel": r.nivel} for r in hijos.itertuples()],
        "descripcion": None if de is None else {"texto": de["descripcion"], "pagina_pdf_inicio": int(de["pdf_page_ini"]),
                                                "pagina_pdf_fin": int(de["pdf_page_fin"]),
                                                "pagina_impresa_inicio": None if pd.isna(de["pagina_impresa_ini"]) else int(de["pagina_impresa_ini"]),
                                                "notas_extraccion": None if pd.isna(de["notas_extraccion"]) else de["notas_extraccion"]},
        "ocupaciones_ejemplo": [{"orden": int(r.orden), "ocupacion": r.ocupacion, "afectado_por_errata": bool(r.afectado_por_errata)} for r in oc.itertuples()],
        "funciones": [{"orden": int(r.orden), "funcion": r.funcion} for r in fu.itertuples()],
        "incluye_excluye": items_ie,
        "fe_de_erratas": _records(er[["pagina_impresa", "seccion", "nota", "texto_dice", "texto_debe_decir", "fecha"]]),
        "coincidencias_onet": crosswalk(sinco_code=code),
        "probabilidad_automatizacion_fo": probabilidad_detalle(code),
    }


def sinco_search(q: str, limit: int = 30) -> dict:
    qn = _norm(q.strip())
    if len(qn) < 2:
        return {"q": q, "total": 0, "resultados": []}
    s = _tabla("sinco")
    res, vistos = [], set()
    for r in s.itertuples():
        if r.sinco_code.startswith(qn) or qn in _norm(r.titulo):
            res.append({"sinco_code": r.sinco_code, "titulo": r.titulo, "nivel": r.nivel, "motivo": "codigo/titulo"}); vistos.add(r.sinco_code)
    oc = _tabla("sinco_ocupaciones_ejemplo")
    ocn = oc["ocupacion"].map(_norm)
    for r in oc[ocn.str.contains(re.escape(qn))].itertuples():
        if r.sinco_code not in vistos:
            res.append({"sinco_code": r.sinco_code, "titulo": _sinco_idx().loc[r.sinco_code, "titulo"], "nivel": "grupo_unitario",
                        "motivo": f"ocupacion ejemplo: {r.ocupacion}"}); vistos.add(r.sinco_code)
    return {"q": q, "total": len(res), "resultados": res[:limit]}


# ---------------------------------------------------------------- O*NET
def onet_list(q: str = "", limit: int = 50, offset: int = 0) -> dict:
    limit = max(1, min(int(limit), 200)); offset = max(0, int(offset))
    o = _tabla("onet_ocupaciones")
    if q.strip():
        qn = _norm(q.strip())
        m = (o["onet_soc_code"].str.contains(re.escape(q.strip())) | o["titulo_en"].map(_norm).str.contains(re.escape(qn))
             | o["descripcion_en"].map(_norm).str.contains(re.escape(qn)))
        o = o[m]
    n_tasks = _tabla("tareas_onet_en").groupby("onet_soc_code").size()
    page = o.iloc[offset:offset + limit][["onet_soc_code", "titulo_en"]].copy()
    page["n_tareas"] = page["onet_soc_code"].map(n_tasks).fillna(0).astype(int)
    return {"q": q, "total": int(len(o)), "limit": limit, "offset": offset, "resultados": _records(page)}


def onet_detail(soc: str) -> dict | None:
    o = _tabla("onet_ocupaciones"); o = o[o["onet_soc_code"] == soc]
    if o.empty:
        return None
    t = _tabla("tareas_onet_en"); t = t[t["onet_soc_code"] == soc]
    r = o.iloc[0]
    return {"onet_soc_code": soc, "titulo_en": r["titulo_en"], "descripcion_en": r["descripcion_en"],
            "n_tareas": int(len(t)), "tareas": _records(t[["task_id", "tarea_en"]]),
            "coincidencias_sinco": crosswalk(onet_soc_code=soc)}


# ---------------------------------------------------------------- probabilidad de automatizacion (Frey-Osborne)
# Decision del usuario 2026-10-19 ("usa probabilidades en el repo"; ver docs/decisions/009): SOLO se admite esta
# probabilidad, rotulada y marcada NO validada. La exposicion sigue prohibida en endpoints e interfaz.
ETIQUETA_PROB = "probabilidad de automatizacion (Frey-Osborne)"
MSG_PROB_NA = "probabilidad no disponible"
PROB_QUE_ES = ("Probabilidad de automatizacion de Frey y Osborne (2013/2017) para ocupaciones SOC 2010, trasladada a SINCO 2019 mediante "
               "el emparejamiento automatico SINCO-O*NET (media ponderada por similitud sobre los 2 candidatos).")
PROB_QUE_NO_ES = ("No es exposicion a IA, ni riesgo de perdida de empleo, ni una estimacion para Mexico. Depende de un emparejamiento "
                  "automatico NO validado y de parametros provisionales sin calibrar.")
AVISO_PROB = "NO validada: " + PROB_QUE_NO_ES
ATRIBUCION_DESCARGA = ("Fuentes: O*NET (USDOL/ETA, CC BY 4.0); SINCO 2019 (INEGI); Frey y Osborne (2013/2017). "
                       "Resultados de emparejamiento automatico NO validados.")
PROB_COLS = ["probabilidad_automatizacion_fo", "probabilidad_automatizacion_fo_media_uniforme", "probabilidad_automatizacion_fo_min",
             "probabilidad_automatizacion_fo_max", "probabilidad_automatizacion_fo_top1"]
PROB_EXTRA = ["n_candidatos", "cobertura_peso_fo", "cobertura_fo", "motivo_na", "bandera_multi_soc2010", "bandera_soc_sin_fo",
              "n_soc2010", "n_soc2010_con_fo"]
PROB_REQUERIDAS = ["modelo", "es_modelo_principal", "sinco_code", "titulo", "estado_validacion", "run_id"] + PROB_COLS
PROB_PUBLICAS = ["sinco_code", "titulo", "modelo", "run_id", "estado_validacion"] + PROB_COLS + PROB_EXTRA
TOPE_FILAS_DESCARGA = 50_000


class Indisponible(Exception):
    """Dato requerido ausente (crosswalk pendiente o tabla de probabilidad inexistente)."""


def _prob_raw() -> tuple[str, str, pd.DataFrame | None]:
    ruta = PROC / "sinco_probabilidad_fo.parquet"
    if not ruta.exists():
        return "no_disponible", MSG_PROB_NA, None
    df = _tabla("sinco_probabilidad_fo")
    faltan = [c for c in PROB_REQUERIDAS if c not in df.columns]
    if faltan:
        return "esquema_invalido", f"faltan columnas: {faltan}", None
    return "disponible", "", df


def modelos_info() -> tuple[str | None, list[str]]:
    """(modelo principal, modelos disponibles). El principal lo declara la tabla de probabilidad o, sin ella, el crosswalk."""
    est, _, p = _prob_raw()
    if p is not None and len(p):
        disp = sorted(p["modelo"].unique())
        pr = p.loc[p["es_modelo_principal"].astype(bool), "modelo"]
        return (pr.iloc[0] if len(pr) else disp[0]), disp
    cw = crosswalk_estado()
    ms = sorted({r.get("modelo") for r in cw["_rows"] if r.get("modelo")})
    return (ms[0] if ms else None), ms


def probabilidad_estado() -> dict:
    est, msg, p = _prob_raw()
    pr, disp = modelos_info()
    return {"estado": est, "mensaje": msg, "etiqueta": ETIQUETA_PROB, "estado_validacion": "sin_validar", "aviso": AVISO_PROB,
            "que_es": PROB_QUE_ES, "que_no_es": PROB_QUE_NO_ES, "modelo_principal": pr, "modelos_disponibles": disp,
            "n_filas": 0 if p is None else int(len(p))}


def _prob_modelo(modelo: str | None) -> tuple[str, str, pd.DataFrame | None]:
    est, msg, p = _prob_raw()
    if p is None:
        return est, msg, None
    pr, disp = modelos_info()
    modelo = modelo or pr
    if modelo not in disp:
        raise ValueError(f"modelo desconocido: {modelo!r}; disponibles: {disp}")
    return est, msg, p[p["modelo"] == modelo]


def _codigos_filtrados(sinco_prefix=None, division=None, nivel=None, q=None) -> set[str] | None:
    """Codigos SINCO que cumplen los filtros (None = sin filtro). q: misma busqueda sin acentos que /api/sinco/search."""
    if nivel is not None and nivel not in NIVELES:
        raise ValueError(f"nivel invalido: {nivel!r}; use uno de {NIVELES}")
    if sinco_prefix is not None and not re.fullmatch(r"[1-9][0-9]{0,3}", sinco_prefix):
        raise ValueError("sinco_prefix debe ser un codigo o prefijo SINCO de 1 a 4 digitos")
    if division is not None and not 1 <= int(division) <= 9:
        raise ValueError("division debe ser 1 a 9")
    if q is not None and len(q) > 100:
        raise ValueError("q admite hasta 100 caracteres")
    if all(v is None or v == "" for v in (sinco_prefix, division, nivel, q)):
        return None
    s = _tabla("sinco")
    m = pd.Series(True, index=s.index)
    if sinco_prefix:
        m &= s["sinco_code"].str.startswith(sinco_prefix)
    if division is not None:
        m &= s["sinco_code"].str[0] == str(int(division))
    if nivel:
        m &= s["nivel"] == nivel
    cods = set(s.loc[m, "sinco_code"])
    if q and q.strip():
        cods &= {x["sinco_code"] for x in sinco_search(q, 100_000)["resultados"]}
    return cods


def _prob_publica(df: pd.DataFrame) -> list[dict]:
    cols = [c for c in PROB_PUBLICAS if c in df.columns]
    rows = _records(df[cols])
    for r in rows:
        r["etiqueta"] = ETIQUETA_PROB
    return rows


def probabilidad_lista(q=None, sinco_prefix=None, division=None, nivel=None, modelo=None, solo_con_probabilidad=False,
                       limit: int = 50, offset: int = 0) -> dict:
    limit = max(1, min(int(limit), 200)); offset = max(0, int(offset))
    e = probabilidad_estado()
    est, _, p = _prob_modelo(modelo)
    e.update({"modelo": modelo or e["modelo_principal"], "total": 0, "limit": limit, "offset": offset, "resultados": []})
    if p is None:
        return e
    cods = _codigos_filtrados(sinco_prefix, division, nivel, q)
    if cods is not None:
        p = p[p["sinco_code"].isin(cods)]
    if solo_con_probabilidad:
        p = p[p["probabilidad_automatizacion_fo"].notna()]
    p = p.sort_values("sinco_code")
    e["total"] = int(len(p)); e["resultados"] = _prob_publica(p.iloc[offset:offset + limit])
    return e


def probabilidad_detalle(code: str, modelo: str | None = None) -> dict:
    """Probabilidad de un SINCO. Siempre rotulada y marcada NO validada."""
    est, msg, p = _prob_modelo(modelo)
    base = {"etiqueta": ETIQUETA_PROB, "estado_validacion": "sin_validar", "aviso": AVISO_PROB, "que_es": PROB_QUE_ES,
            "que_no_es": PROB_QUE_NO_ES}
    if p is None:
        return {**base, "estado": est, "mensaje": msg, "valores": None}
    f = p[p["sinco_code"] == code]
    if f.empty:
        return {**base, "estado": "sin_fila", "mensaje": "este nivel SINCO no tiene probabilidad asignada (solo grupos unitarios)", "valores": None}
    return {**base, "estado": "disponible", "mensaje": "", "valores": _prob_publica(f)[0]}


# ---------------------------------------------------------------- dataset descargable
COLS_BASE = ["sinco_code", "sinco_titulo", "nivel", "division", "rango", "onet_soc_code", "onet_titulo", "similitud", "margen", "modelo",
             "tipo_relacion", "match_status", "baja_confianza", "estado_validacion", "fuente", "run_id"]
COLS_PROB = PROB_COLS + ["n_candidatos", "cobertura_peso_fo", "cobertura_fo", "motivo_na", "probabilidad_es_na",
                         "probabilidad_estado_validacion"]


def dataset(sinco_prefix=None, division=None, nivel=None, q=None, rango_max: int = 2, solo_con_probabilidad: bool = False,
            modelo: str | None = None) -> tuple[pd.DataFrame, dict]:
    """Una fila por (grupo SINCO, O*NET emparejado) + probabilidad agregada por SINCO si existe la tabla. Devuelve (df, meta)."""
    if rango_max not in (1, 2):
        raise ValueError("rango_max debe ser 1 o 2")
    cw = crosswalk_estado()
    if cw["estado"] != "disponible":
        raise Indisponible(cw["mensaje"] or f"crosswalk {cw['estado']}")
    cwdf = pd.DataFrame(cw["_rows"])
    pr, disp = modelos_info()
    modelo = modelo or pr
    if modelo not in disp:
        raise ValueError(f"modelo desconocido: {modelo!r}; disponibles: {disp}")
    est, _, p = _prob_modelo(modelo)
    cw_modelos = set(cwdf["modelo"].dropna()) if "modelo" in cwdf else set()
    if modelo in cw_modelos:
        base = cwdf[cwdf["modelo"] == modelo].copy()
    else:   # modelo no principal: top-k del mismo run desde match_candidatos
        if not (PROC / "match_candidatos.parquet").exists():
            raise Indisponible(f"no hay coincidencias para el modelo {modelo}")
        mc = _tabla("match_candidatos")
        k = int(cwdf["rango"].max()) if "rango" in cwdf and cwdf["rango"].notna().any() else 2
        base = mc[(mc["modelo"] == modelo) & (mc["run_id"].isin(cwdf["run_id"].dropna().unique())) & (mc["rango"] <= k)].copy()
        base = base.rename(columns={"margen_sinco": "margen"})
        base["fuente"] = f"semiautomatico_embeddings_A1_{modelo}"; base["estado_validacion"] = "sin_validar"
        if p is not None:
            base = base.merge(p[["sinco_code", "match_status", "baja_confianza"]], on="sinco_code", how="left")
    if "rango" not in base:
        base["rango"] = pd.NA
    base = base[base["rango"].isna() | (base["rango"] <= rango_max)]
    cods = _codigos_filtrados(sinco_prefix, division, nivel, q)
    if cods is not None:
        base = base[base["sinco_code"].isin(cods)]
    s = _tabla("sinco").set_index("sinco_code"); o = _tabla("onet_ocupaciones").set_index("onet_soc_code")
    base["sinco_titulo"] = base["sinco_code"].map(s["titulo"]); base["nivel"] = base["sinco_code"].map(s["nivel"])
    base["division"] = base["sinco_code"].str[0].astype(int)
    base["onet_titulo"] = base["onet_soc_code"].map(o["titulo_en"])
    base["modelo"] = modelo
    for c in COLS_BASE:
        if c not in base:
            base[c] = None
    prob_ok = p is not None
    cols = list(COLS_BASE)
    if prob_ok:
        pp = p.set_index("sinco_code")
        for c in PROB_COLS + ["n_candidatos", "cobertura_peso_fo", "cobertura_fo", "motivo_na"]:
            base[c] = base["sinco_code"].map(pp[c]) if c in pp else None
        base["probabilidad_es_na"] = base["probabilidad_automatizacion_fo"].isna()
        base["probabilidad_estado_validacion"] = base["sinco_code"].map(pp["estado_validacion"])
        cols += COLS_PROB
        if solo_con_probabilidad:
            base = base[base["probabilidad_automatizacion_fo"].notna()]
    elif solo_con_probabilidad:
        raise Indisponible(MSG_PROB_NA)
    base = base.sort_values(["sinco_code", "rango"], kind="stable")
    truncado = len(base) > TOPE_FILAS_DESCARGA
    out = base[cols].head(TOPE_FILAS_DESCARGA).reset_index(drop=True)
    runs = sorted(out["run_id"].dropna().unique().tolist())
    onet = meta()["onet"]
    info = {
        "filtros": {"sinco_prefix": sinco_prefix, "division": division, "nivel": nivel, "q": q, "rango_max": rango_max,
                    "solo_con_probabilidad": solo_con_probabilidad, "modelo": modelo},
        "completo": cods is None and rango_max == 2 and not solo_con_probabilidad and modelo == pr,
        "n_filas": int(len(out)), "truncado": truncado, "tope_filas": TOPE_FILAS_DESCARGA, "run_id": runs, "modelo": modelo,
        "probabilidad_automatizacion_fo": ({"estado": "disponible", "etiqueta": ETIQUETA_PROB, "estado_validacion": "sin_validar", "aviso": AVISO_PROB}
                         if prob_ok else {"estado": "no_disponible", "mensaje": MSG_PROB_NA}),
        "atribucion": ATRIBUCION_DESCARGA, "onet_version": onet.get("version"),
        "estado_coincidencias": "automaticas, NO validadas (Metodo A1, embeddings; la similitud no es una probabilidad)",
        "columnas": cols,
    }
    return out, info


_FORMULA = ("=", "+", "-", "@", "\t", "\r")


def csv_seguro(df: pd.DataFrame) -> pd.DataFrame:
    """Anti-inyeccion de formulas (CSV/Excel): toda celda de TEXTO cuyo primer caracter visible sea = + - @ (o tab/CR) se
    prefija con una comilla simple. Las columnas numericas y booleanas no se tocan."""
    def f(v):
        return "'" + v if isinstance(v, str) and v.lstrip(" ")[:1] in _FORMULA else v
    out = df.copy()
    for c in out.columns:
        if out[c].dtype == object or str(out[c].dtype) in ("str", "string"):
            out[c] = out[c].map(f)
    return out


# ---------------------------------------------------------------- resumen (KPIs y barras de coincidencias SINCO-O*NET)
ESTADOS_MATCH = ["ok", "baja_confianza", "sin_coincidencia"]
ETIQUETA_ESTADO = {"ok": "Con coincidencia", "baja_confianza": "Coincidencia de baja confianza", "sin_coincidencia": "Sin coincidencia"}
AVISO_RESUMEN = ("Coincidencias automaticas (Metodo A1, top-2) NO validadas; probabilidad de automatizacion (Frey-Osborne) != exposicion a IA.")
BIN_SIM = 0.05


def _pares_modelo(modelo: str | None) -> tuple[str, pd.DataFrame, pd.Series]:
    """(modelo, pares top-2 [sinco_code, onet_soc_code, rango, similitud, tipo_relacion?], estado por grupo unitario)."""
    cw = crosswalk_estado()
    if cw["estado"] != "disponible":
        raise Indisponible(cw["mensaje"] or f"crosswalk {cw['estado']}")
    cwdf = pd.DataFrame(cw["_rows"])
    pr, disp = modelos_info()
    modelo = modelo or pr
    if modelo not in disp:
        raise ValueError(f"modelo desconocido: {modelo!r}; disponibles: {disp}")
    if "modelo" in cwdf and modelo in set(cwdf["modelo"].dropna()):
        par = cwdf[cwdf["modelo"] == modelo].copy()
        est = par[par["rango"] == 1].drop_duplicates("sinco_code").set_index("sinco_code")["match_status"]
    else:   # modelo alterno: pares de match_candidatos (mismo run) y estado de match_sinco_resumen
        if not (PROC / "match_candidatos.parquet").exists() or not (PROC / "match_sinco_resumen.parquet").exists():
            raise Indisponible(f"no hay coincidencias para el modelo {modelo}")
        mc = _tabla("match_candidatos")
        par = mc[(mc["modelo"] == modelo) & (mc["run_id"].isin(cwdf["run_id"].dropna().unique())) & (mc["rango"] <= 2)].copy()
        rs = _tabla("match_sinco_resumen")
        est = rs[rs["modelo"] == modelo].drop_duplicates("sinco_code").set_index("sinco_code")["match_status"]
    return modelo, par, est


def resumen(modelo: str | None = None) -> dict:
    """KPIs y datos de barras de cuantos grupos unitarios SINCO hacen match con O*NET. Todo se calcula aqui, de las tablas."""
    base = {"etiqueta_aviso": AVISO_RESUMEN, "estado_validacion": "sin_validar"}
    cw = crosswalk_estado()
    if cw["estado"] != "disponible":
        return {**base, "estado": cw["estado"], "mensaje": cw["mensaje"] or MSG_PENDIENTE, "modelo": None, "modelos_disponibles": []}
    modelo, par, est = _pares_modelo(modelo)
    pr, disp = modelos_info()
    s = _tabla("sinco")
    gu = s[s["nivel"] == "grupo_unitario"][["sinco_code", "titulo"]]
    n_gu = int(len(gu))
    est = gu["sinco_code"].map(est).fillna("sin_dato")
    est.index = gu["sinco_code"]
    estados = ESTADOS_MATCH + (["sin_dato"] if (est == "sin_dato").any() else [])
    cuenta = {e: int((est == e).sum()) for e in estados}
    pct = lambda n, d: round(100.0 * n / d, 1) if d else None
    con_match = cuenta["ok"] + cuenta["baja_confianza"]

    # divisiones
    divs = s[s["nivel"] == "division"].sort_values("sinco_code")
    div_de = gu["sinco_code"].str[0]
    por_div = []
    for d in divs.itertuples():
        e = est[(div_de == d.sinco_code).values]
        fila = {"division": d.sinco_code, "nombre": d.titulo, "total": int(len(e))}
        fila.update({k: int((e == k).sum()) for k in estados})
        por_div.append(fila)

    # O*NET distintas (pares de grupos con coincidencia) y similitud del rango 1
    n_onet = int(len(_tabla("onet_ocupaciones")))
    con = set(est[est.isin(["ok", "baja_confianza"])].index)
    distintas = int(par.loc[par["sinco_code"].isin(con), "onet_soc_code"].nunique())
    r1 = par[par["rango"] == 1].drop_duplicates("sinco_code")["similitud"].dropna().astype(float)
    hist = []
    if len(r1):
        lo = np.floor(r1.min() / BIN_SIM) * BIN_SIM
        hi = np.ceil(r1.max() / BIN_SIM) * BIN_SIM
        bordes = np.round(np.arange(lo, hi + BIN_SIM / 2, BIN_SIM), 4)
        cnt, _ = np.histogram(r1, bins=bordes)
        hist = [{"desde": float(bordes[i]), "hasta": float(bordes[i + 1]), "n": int(cnt[i])} for i in range(len(cnt))]
    tipos = par["tipo_relacion"].value_counts() if "tipo_relacion" in par else pd.Series(dtype=int)

    # probabilidad de automatizacion (Frey-Osborne): solo conteos de disponibilidad, rotulada y NO validada
    pe, pmsg, p = _prob_raw()
    prob = {"etiqueta": ETIQUETA_PROB, "estado_validacion": "sin_validar"}
    if p is None:
        prob.update(estado="no_disponible", mensaje=MSG_PROB_NA)
    else:
        pm = p[p["modelo"] == modelo].drop_duplicates("sinco_code")
        na = pm["probabilidad_automatizacion_fo"].isna()
        causas = pm.loc[na, "motivo_na"].fillna("sin_motivo").value_counts()
        prob.update(estado="disponible", mensaje="", n_grupos=int(len(pm)), n_con_valor=int((~na).sum()), n_na=int(na.sum()),
                    pct_con_valor=pct(int((~na).sum()), int(len(pm))), causas_na=[{"causa": k, "n": int(v)} for k, v in causas.items()])

    return {
        **base, "estado": "disponible", "mensaje": "", "modelo": modelo, "modelo_principal": pr, "modelos_disponibles": disp,
        "run_id": sorted(par["run_id"].dropna().unique().tolist()) if "run_id" in par else [],
        "kpis": {
            "grupos_unitarios": n_gu,
            "con_match": con_match, "pct_con_match": pct(con_match, n_gu),
            "con_match_confiable": cuenta["ok"], "pct_con_match_confiable": pct(cuenta["ok"], n_gu),
            "baja_confianza": cuenta["baja_confianza"], "pct_baja_confianza": pct(cuenta["baja_confianza"], n_gu),
            "sin_coincidencia": cuenta["sin_coincidencia"], "pct_sin_coincidencia": pct(cuenta["sin_coincidencia"], n_gu),
            "onet_total": n_onet, "onet_distintas_emparejadas": distintas, "pct_onet_emparejadas": pct(distintas, n_onet),
            "similitud_rango1_media": None if r1.empty else round(float(r1.mean()), 4),
            "similitud_rango1_mediana": None if r1.empty else round(float(r1.median()), 4),
            "pares_top2": int(len(par)),
            "tipos_relacion": [{"tipo": k, "n_pares": int(v)} for k, v in tipos.items()],
        },
        "por_estado": [{"estado": e, "etiqueta": ETIQUETA_ESTADO.get(e, "Sin dato"), "n": cuenta[e], "pct": pct(cuenta[e], n_gu)} for e in estados],
        "por_division": por_div,
        "histograma_similitud_rango1": hist,
        "probabilidad_automatizacion_fo": prob,
        "notas": ["Un grupo 'con coincidencia' tiene match_status ok o baja_confianza; 'sin coincidencia' = el modelo no supero los umbrales provisionales.",
                  "Ocupaciones O*NET distintas: sobre los top-2 de los grupos con coincidencia. Similitud = coseno del rango 1 (no es una probabilidad).",
                  "Umbrales provisionales sin calibrar. " + AVISO_RESUMEN],
    }
