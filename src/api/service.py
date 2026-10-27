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
    estado_validacion: Literal["sin_validar", "validado", "rechazado", "revision_manual_1_revisor"]
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
    _main.cache_clear()
    _main_meta.cache_clear()
    _comparacion_cache.cache_clear()


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
            "exposicion_agentes": exposicion_estado(),
            "tablas": tablas,
            "atribucion": ATRIBUCION_DESCARGA + " Solo lectura. La exposición por modelos (decisión 019) es teórica y está sin validar."}


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
        "exposicion_agentes": exposicion_detalle(code),
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


# ---------------------------------------------------------------- conexiones SINCO <-> O*NET (vista amigable; solo lectura)
# Grandes grupos (2 digitos) de la clasificacion SOC (Standard Occupational Classification), nombres estandar en ingles.
# Fuente: BLS, "2018 Standard Occupational Classification System" (https://www.bls.gov/soc/2018/major_groups.htm). Los codigos
# O*NET-SOC (NN-NNNN.NN) comienzan con el gran grupo SOC de 2 digitos. Constante fija; no es un dato del proyecto.
SOC_GRANDES_GRUPOS = {
    "11": "Management", "13": "Business and Financial Operations", "15": "Computer and Mathematical",
    "17": "Architecture and Engineering", "19": "Life, Physical, and Social Science", "21": "Community and Social Service",
    "23": "Legal", "25": "Educational Instruction and Library", "27": "Arts, Design, Entertainment, Sports, and Media",
    "29": "Healthcare Practitioners and Technical", "31": "Healthcare Support", "33": "Protective Service",
    "35": "Food Preparation and Serving Related", "37": "Building and Grounds Cleaning and Maintenance",
    "39": "Personal Care and Service", "41": "Sales and Related", "43": "Office and Administrative Support",
    "45": "Farming, Fishing, and Forestry", "47": "Construction and Extraction", "49": "Installation, Maintenance, and Repair",
    "51": "Production", "53": "Transportation and Material Moving", "55": "Military Specific",
}
SOC_FUENTE = "BLS, 2018 Standard Occupational Classification (grandes grupos de 2 digitos); los codigos O*NET-SOC comienzan con ese prefijo."
EXPLICACION_CONEXION = ("Se calculó comparando automáticamente el texto del grupo SINCO (en español) con la descripción en inglés de cada ocupación O*NET mediante un modelo "
                        "de lenguaje multilingüe (sin traducir ninguno de los dos); las dos ocupaciones más parecidas son las coincidencias. Es una propuesta NO validada: la similitud "
                        "no es una probabilidad.")
CLAVES_ESTADO = {"mejor_coincidencia": "mejor coincidencia", "segunda_opcion": "segunda opción", "baja_confianza": "baja confianza",
                 "sin_coincidencia": "sin coincidencia"}


def _corta(txt, n: int = 240) -> str:
    """Primeras frases de un texto, sin pasar de n caracteres (corta en limite de oracion o palabra)."""
    t = " ".join(str(txt or "").split())
    if len(t) <= n:
        return t
    corte = t[:n]
    i = corte.rfind(". ")
    if i >= n * 0.5:
        return corte[:i + 1]
    return corte[:corte.rfind(" ")].rstrip(",;:") + "…"


def _clave_estado(fila: dict) -> str:
    if fila.get("match_status") == "sin_coincidencia":
        return "sin_coincidencia"
    if fila.get("rango") == 1:
        return "baja_confianza" if (fila.get("match_status") == "baja_confianza" or fila.get("baja_confianza")) else "mejor_coincidencia"
    return "segunda_opcion"


def _filas_principal() -> tuple[dict, list[dict]]:
    """(estado del crosswalk, filas del modelo principal)."""
    cw = crosswalk_estado()
    rows = cw.pop("_rows")
    if rows and any(r.get("modelo") for r in rows):
        pr, _ = modelos_info()
        sel = [r for r in rows if r.get("modelo") == pr]
        rows = sel or rows
    return cw, rows


def conexion(code: str) -> dict | None:
    """Todo lo necesario para dibujar la conexion de UN grupo unitario SINCO con sus O*NET emparejados. None si no es grupo unitario."""
    s = _tabla("sinco")
    fila = s[(s["sinco_code"] == code) & (s["nivel"] == "grupo_unitario")]
    if fila.empty:
        return None
    n = fila.iloc[0]
    gu = s[s["nivel"] == "grupo_unitario"].sort_values("orden")["sinco_code"].tolist()
    i = gu.index(code)
    idx = _sinco_idx()
    hermanos = [{"sinco_code": c, "titulo": idx.loc[c, "titulo"]} for c in gu if c[:3] == code[:3] and c != code]
    d = _tabla("sinco_descripcion"); d = d[d["sinco_code"] == code]
    oc = _tabla("sinco_ocupaciones_ejemplo"); oc = oc[oc["sinco_code"] == code].sort_values("orden")
    cw, rows = _filas_principal()
    o = _tabla("onet_ocupaciones").set_index("onet_soc_code")
    mias = sorted([r for r in rows if r["sinco_code"] == code], key=lambda r: (r.get("rango") or 99))
    coinc = []
    for r in mias:
        soc = r["onet_soc_code"]
        est = _clave_estado(r)
        coinc.append({"rango": r.get("rango"), "onet_soc_code": soc, "onet_titulo": o.loc[soc, "titulo_en"],
                      "onet_descripcion_corta": _corta(o.loc[soc, "descripcion_en"]), "soc_grupo": soc[:2],
                      "soc_grupo_nombre": SOC_GRANDES_GRUPOS.get(soc[:2]), "similitud": r.get("similitud"), "margen": r.get("margen"),
                      "baja_confianza": bool(r.get("baja_confianza")), "match_status": r.get("match_status"),
                      "estado": est, "estado_etiqueta": CLAVES_ESTADO[est],
                      "estado_validacion": r.get("estado_validacion"), "modelo": r.get("modelo"), "run_id": r.get("run_id")})
    ant = gu[i - 1] if i > 0 else None
    sig = gu[i + 1] if i + 1 < len(gu) else None
    return {
        "sinco": {"sinco_code": code, "titulo": n["titulo"], "division": code[0], "division_titulo": idx.loc[code[0], "titulo"],
                  "subgrupo": code[:3], "subgrupo_titulo": idx.loc[code[:3], "titulo"] if code[:3] in idx.index else None,
                  "descripcion_corta": _corta(d.iloc[0]["descripcion"]) if len(d) else "",
                  "ocupaciones_ejemplo": oc["ocupacion"].tolist()[:5], "n_ocupaciones_ejemplo": int(len(oc))},
        "anterior": None if ant is None else {"sinco_code": ant, "titulo": idx.loc[ant, "titulo"]},
        "siguiente": None if sig is None else {"sinco_code": sig, "titulo": idx.loc[sig, "titulo"]},
        "hermanos": hermanos,
        "estado": cw["estado"], "mensaje": cw["mensaje"],
        "estado_grupo": (coinc[0]["estado"] if coinc else None),
        "coincidencias": coinc,
        "explicacion": EXPLICACION_CONEXION,
        "estado_validacion": "sin_validar",
        "probabilidad_automatizacion_fo": probabilidad_detalle(code),
        "exposicion_agentes": exposicion_detalle(code),
    }


def onet_sinco(soc: str) -> dict | None:
    """SINCO que apuntan a una ocupacion O*NET (inverso del crosswalk), de mayor a menor similitud."""
    o = _tabla("onet_ocupaciones"); o = o[o["onet_soc_code"] == soc]
    if o.empty:
        return None
    cw, rows = _filas_principal()
    idx = _sinco_idx()
    filas = []
    for r in rows:
        if r["onet_soc_code"] != soc:
            continue
        est = _clave_estado(r)
        m_ = _main()
        e_ = m_.loc[r["sinco_code"]] if m_ is not None and r["sinco_code"] in m_.index else None
        filas.append({"sinco_code": r["sinco_code"], "sinco_titulo": idx.loc[r["sinco_code"], "titulo"], "division": r["sinco_code"][0],
                      "rango": r.get("rango"), "similitud": r.get("similitud"), "baja_confianza": bool(r.get("baja_confianza")),
                      "match_status": r.get("match_status"), "estado": est, "estado_etiqueta": CLAVES_ESTADO[est],
                      "exposicion_media_modelos": None if e_ is None else _num(e_.get("exp_idx_media_modelos")),
                      "exposicion_rango_modelos": None if e_ is None else _num(e_.get("exp_idx_rango_modelos"))})
    filas.sort(key=lambda f: -(f["similitud"] if f["similitud"] is not None else -1))
    return {"onet_soc_code": soc, "titulo_en": o.iloc[0]["titulo_en"], "estado": cw["estado"], "mensaje": cw["mensaje"],
            "total": len(filas), "estado_validacion": "sin_validar", "filas": filas,
            "aviso": "Coincidencias automáticas NO validadas; la similitud no es una probabilidad.",
            "aviso_exposicion": AVISO_EXPO if "AVISO_EXPO" in globals() else None}


def conexiones_flujo() -> dict:
    """Flujo division SINCO -> gran grupo SOC (2 digitos del O*NET de rango 1); ancho = numero de grupos unitarios SINCO."""
    cw, rows = _filas_principal()
    s = _tabla("sinco")
    divs = [{"division": r.sinco_code, "nombre": r.titulo} for r in s[s["nivel"] == "division"].sort_values("sinco_code").itertuples()]
    base = {"estado": cw["estado"], "mensaje": cw["mensaje"], "estado_validacion": "sin_validar", "soc_fuente": SOC_FUENTE,
            "divisiones": divs, "grupos_soc": [], "enlaces": [], "total_grupos": 0}
    if cw["estado"] != "disponible":
        return base
    r1: dict[str, dict] = {}
    for r in rows:
        if r.get("rango") == 1 and r["sinco_code"] not in r1:
            r1[r["sinco_code"]] = r
    cuenta: dict[tuple[str, str], dict] = {}
    for code, r in r1.items():
        k = (code[0], r["onet_soc_code"][:2])
        e = cuenta.setdefault(k, {"division": k[0], "soc_grupo": k[1], "n": 0, "ok": 0, "baja_confianza": 0, "sin_coincidencia": 0})
        e["n"] += 1
        st = r.get("match_status")
        e[st if st in ("ok", "baja_confianza", "sin_coincidencia") else "ok"] += 1
    tot_soc: dict[str, int] = {}
    for (_, g), e in cuenta.items():
        tot_soc[g] = tot_soc.get(g, 0) + e["n"]
    base["grupos_soc"] = [{"soc_grupo": g, "nombre": SOC_GRANDES_GRUPOS.get(g, g), "n": n} for g, n in sorted(tot_soc.items())]
    base["enlaces"] = sorted(cuenta.values(), key=lambda e: (e["division"], e["soc_grupo"]))
    base["total_grupos"] = len(r1)
    return base


# ---------------------------------------------------------------- exposicion del metodo de agentes (decision 019)
CAL = PROC / "calibracion"
ETIQUETA_EXPO = "exposición teórica por anotación de modelos (Haiku, Sonnet, Opus), sin validar"
AVISO_EXPO = ("Sin validar. Mide consistencia entre modelos, no exactitud. Los tres modelos son de la misma familia: el sesgo común no es "
              "identificable. No es riesgo de pérdida de empleo ni una estimación para México.")
EXPO_QUE_ES = ("Cada función de un grupo SINCO fue etiquetada por Haiku, Sonnet y Opus (2 corridas cada uno) con dos rúbricas: exposure_class (E0 a E2) y "
               "eloundou_class (EL0 a EL3, con EL3 fundida en EL2). El índice es el promedio de la clase (0, 0.5, 1) sobre las funciones del grupo y las corridas del modelo.")
EXPO_QUE_NO_ES = ("El índice de exposure_class es la medida principal de 001 con pesos iguales por función (la agregación formal de la ruta S sigue pendiente); alfa/beta/cota son las medidas de Eloundou. No es una medición contra humanos, no es riesgo de perder el empleo ni una "
                  "estimación para México. Los tres modelos comparten familia.")
AVISO_PESO = ("peso_softmax es un peso relativo entre los 2 candidatos, softmax(similitud / tau) con tau provisional sin calibrar. "
              "NO es una probabilidad calibrada de que el emparejamiento sea correcto.")
MODELOS_EXPO = ("haiku", "sonnet", "opus")
NOMBRE_MODELO = {"haiku": "Haiku", "sonnet": "Sonnet", "opus": "Opus"}
ORDENES_EXPO = {"codigo": ("sinco_code", True), "exposicion_desc": ("exp_idx_media_modelos", False), "exposicion_asc": ("exp_idx_media_modelos", True),
                "desacuerdo_desc": ("exp_idx_rango_modelos", False)}


@lru_cache(maxsize=1)
def _main() -> pd.DataFrame | None:
    ruta = PROC / "main_sinco_comp_table.parquet"
    if not ruta.exists():
        return None
    df = pd.read_parquet(ruta)
    df["sinco_code"] = df["sinco_code"].astype(str)
    return df.set_index("sinco_code", drop=False).rename_axis(None)


@lru_cache(maxsize=1)
def _main_meta() -> dict:
    ruta = PROC / "main_sinco_comp_table_meta.json"
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}


def _num(x):
    return None if x is None or pd.isna(x) else float(x)


def _txt(x):
    return None if x is None or pd.isna(x) else x


def _base_expo() -> dict:
    return {"etiqueta": ETIQUETA_EXPO, "aviso": AVISO_EXPO, "que_es": EXPO_QUE_ES, "que_no_es": EXPO_QUE_NO_ES,
            "estado_validacion": "sin_validar", "decision": "019"}


def exposicion_estado() -> dict:
    m = _main()
    base = {k: v for k, v in _base_expo().items() if k in ("etiqueta", "aviso", "estado_validacion", "decision")}
    if m is None:
        return {**base, "estado": "no_disponible", "mensaje": "exposición no disponible", "n_filas": 0}
    meta = _main_meta()
    return {**base, "estado": "disponible", "mensaje": "", "n_filas": int(len(m)), "n_con_anotacion": int(m["tiene_anotacion"].sum()),
            "corridas": meta.get("corridas"), "fecha_utc": meta.get("fecha_utc")}


def _expo_fila(r: pd.Series) -> dict:
    modelos = {}
    for k in MODELOS_EXPO:
        modelos[k] = {"modelo": NOMBRE_MODELO[k], "exposure_idx": _num(r.get(f"exp_idx_{k}")),
                      "exposure_clases": {c: _num(r.get(f"exp_{c}_{k}")) for c in ("E0", "E1", "E2")},
                      "eloundou_idx": _num(r.get(f"el_idx_{k}")),
                      "eloundou_clases": {c: _num(r.get(f"el_{c}_{k}")) for c in ("EL0", "EL1", "EL2")},
                      "cuello_fisico_frac": _num(r.get(f"pb_{k}"))}
    cand = []
    for i in (1, 2):
        if pd.notna(r.get(f"onet{i}_soc")):
            cand.append({"rango": i, "onet_soc_code": r[f"onet{i}_soc"], "onet_titulo": _txt(r.get(f"onet{i}_titulo")),
                         "similitud": _num(r.get(f"onet{i}_similitud")), "peso_softmax": _num(r.get(f"onet{i}_peso_softmax"))})
    coincide = r.get("match_top1_coincide_otro_modelo")
    return {
        "sinco_code": r["sinco_code"], "titulo": r["titulo"], "division": r["division"], "n_funciones": int(r["n_funciones"]),
        "modelos": modelos,
        "entre_modelos": {"exposure_idx_media": _num(r.get("exp_idx_media_modelos")), "exposure_idx_min": _num(r.get("exp_idx_min_modelos")),
                          "exposure_idx_max": _num(r.get("exp_idx_max_modelos")), "exposure_idx_rango": _num(r.get("exp_idx_rango_modelos")),
                          "eloundou_idx_media": _num(r.get("el_idx_media_modelos")), "eloundou_idx_min": _num(r.get("el_idx_min_modelos")),
                          "eloundou_idx_max": _num(r.get("el_idx_max_modelos")), "eloundou_idx_rango": _num(r.get("el_idx_rango_modelos")),
                          "modelos_excluidos": [x for x in str(r.get("modelos_excluidos") or "").split(",") if x],
                          "regla": "media simple con pesos iguales de los modelos no excluidos (018 R1.3); se reportan también los tres por modelo y el rango"},
        "acuerdo_funciones": {"exposure_frac_coinciden_3_modelos": _num(r.get("exp_frac_coinciden_3_modelos")),
                              "exposure_frac_desacuerdo_fuerte": _num(r.get("exp_frac_desacuerdo_fuerte")),
                              "eloundou_frac_coinciden_3_modelos": _num(r.get("el_frac_coinciden_3_modelos")),
                              "eloundou_frac_desacuerdo_fuerte": _num(r.get("el_frac_desacuerdo_fuerte")),
                              "nota": "primera corrida de cada modelo; función por función"},
        "b1": {"exposure": {"idx": _num(r.get("b1_exp_idx")), "lo": _num(r.get("b1_exp_idx_lo")), "hi": _num(r.get("b1_exp_idx_hi")),
                            "sin_pooling": _num(r.get("b1_exp_idx_sin_pooling"))},
               "eloundou": {"idx": _num(r.get("b1_el_idx")), "lo": _num(r.get("b1_el_idx_lo")), "hi": _num(r.get("b1_el_idx_hi")),
                            "sin_pooling": _num(r.get("b1_el_idx_sin_pooling"))},
               "nota": "B1 ordinal, unidad = modelo, intervalo al 90 %. Consistencia entre modelos, no exactitud. Escala distinta de la media simple."},
        "emparejamiento": {"modelo": _txt(r.get("match_modelo")), "tau": _num(r.get("match_tau")), "match_status": _txt(r.get("match_status")),
                           "baja_confianza": None if pd.isna(r.get("match_baja_confianza")) else bool(r.get("match_baja_confianza")),
                           "margen": _num(r.get("match_margen")), "top1_coincide_otro_modelo": None if pd.isna(coincide) else bool(coincide),
                           "candidatos": cand, "aviso_peso": AVISO_PESO},
        "probabilidad_fo": {"etiqueta": ETIQUETA_PROB, "valor": _num(r.get("prob_automatizacion_fo")), "cobertura": _txt(r.get("prob_fo_cobertura")),
                            "motivo_na": _txt(r.get("prob_fo_motivo_na")), "estado_validacion": "sin_validar"},
    }


def exposicion_detalle(code: str) -> dict:
    """Exposición por modelos de UN grupo unitario SINCO, con su emparejamiento y B1. Siempre rotulada y sin validar."""
    base = _base_expo()
    m = _main()
    if m is None:
        return {**base, "estado": "no_disponible", "mensaje": "exposición no disponible", "valores": None}
    if code not in m.index:
        return {**base, "estado": "sin_fila", "mensaje": "este nivel SINCO no tiene exposición asignada (solo grupos unitarios)", "valores": None}
    r = m.loc[code]
    v = _expo_fila(r)
    if not bool(r["tiene_anotacion"]):
        return {**base, "estado": "sin_anotacion", "mensaje": "el catálogo no trae funciones para este grupo: sin exposición, sin imputar", "valores": v}
    return {**base, "estado": "disponible", "mensaje": "", "valores": v}


def _expo_compacta(r: pd.Series) -> dict:
    return {"sinco_code": r["sinco_code"], "titulo": r["titulo"], "division": r["division"], "n_funciones": int(r["n_funciones"]),
            "tiene_anotacion": bool(r["tiene_anotacion"]),
            "exposure_idx": {k: _num(r.get(f"exp_idx_{k}")) for k in MODELOS_EXPO},
            "eloundou_idx": {k: _num(r.get(f"el_idx_{k}")) for k in MODELOS_EXPO},
            "exposure_idx_media_modelos": _num(r.get("exp_idx_media_modelos")), "eloundou_idx_media_modelos": _num(r.get("el_idx_media_modelos")),
            "exposure_idx_rango_modelos": _num(r.get("exp_idx_rango_modelos")),
            "onet1_soc_code": _txt(r.get("onet1_soc")), "onet1_titulo": _txt(r.get("onet1_titulo")),
            "onet1_similitud": _num(r.get("onet1_similitud")), "onet1_peso_softmax": _num(r.get("onet1_peso_softmax")),
            "match_status": _txt(r.get("match_status"))}


def exposicion_lista(q=None, sinco_prefix=None, division=None, orden: str = "codigo", solo_con_anotacion: bool = False,
                     limit: int = 50, offset: int = 0) -> dict:
    limit = max(1, min(int(limit), 200)); offset = max(0, int(offset))
    if orden not in ORDENES_EXPO:
        raise ValueError(f"orden invalido: {orden!r}; use uno de {sorted(ORDENES_EXPO)}")
    e = {**_base_expo(), "estado": exposicion_estado()["estado"], "orden": orden, "total": 0, "limit": limit, "offset": offset, "resultados": []}
    m = _main()
    if m is None:
        e["mensaje"] = "exposición no disponible"
        return e
    cods = _codigos_filtrados(sinco_prefix, division, None, q)
    if cods is not None:
        m = m[m["sinco_code"].isin(cods)]
    if solo_con_anotacion:
        m = m[m["tiene_anotacion"]]
    col, asc = ORDENES_EXPO[orden]
    m = m.sort_values([col, "sinco_code"], ascending=[asc, True], na_position="last")
    e["total"] = int(len(m))
    e["resultados"] = [_expo_compacta(r) for _, r in m.iloc[offset:offset + limit].iterrows()]
    return e


@lru_cache(maxsize=1)
def _comparacion_cache() -> dict | None:
    ruta = CAL / "acuerdo_modelos.json"
    if not ruta.exists():
        return None
    ac = json.loads(ruta.read_text(encoding="utf-8"))
    campos = {}
    for campo, v in ac["campos"].items():   # kappa_sobre_moda no se expone: queda inflado por la selección de ítems (018 R2.2)
        campos[campo] = {"kappa_intra_modelo": v["intra_modelo_kappa"],
                         "kappa_entre_modelos": {k: x["kappa_medio_pares_de_corridas"] for k, x in v["entre_modelos"].items()},
                         "alfa_krippendorff_ordinal_corridas": v["alfa_krippendorff_ordinal"]["corridas"],
                         "acuerdo_exacto_corridas": v["acuerdo_exacto_corridas"], "regla_exclusion": v["regla_exclusion"],
                         "umbral_uso_principal": v["estado_uso_principal"]["umbral_kappa_min"], "cumple_umbral_uso_principal": v["estado_uso_principal"]["suficiente"]}
    b1 = {}
    for campo in ("eloundou_class", "exposure_class"):
        pa = CAL / f"b1_ordinal_{campo}_modelo_anotadores.parquet"
        if pa.exists():
            d = pd.read_parquet(CAL / f"b1_ordinal_{campo}_modelo_diagnosticos.parquet")
            meta_b1 = json.loads((CAL / f"b1_ordinal_{campo}_modelo_meta.json").read_text(encoding="utf-8"))
            b1[campo] = {"anotadores": _records(pd.read_parquet(pa)), "convergio": bool(meta_b1["convergio"]), "max_rhat": float(d["rhat"].max()),
                         "min_ess": float(d["ess"].min()), "n_items": meta_b1["n_items"], "n_grupos": meta_b1["n_grupos"], "etiqueta": meta_b1["etiqueta"],
                         "lectura": meta_b1.get("lectura"), "umbrales": {"rhat_max": 1.05, "ess_min": 100}}
    sens = CAL / "sensibilidad_preambulo.json"
    meta = _main_meta()
    return {"corridas_base": meta.get("corridas"), "campos": campos, "correlaciones_por_grupo": ac.get("grupos"),
            "control_negativo_cuello_fisico": ac.get("control_negativo_S8"), "b1_ordinal_por_modelo": b1,
            "sensibilidad_preambulo": json.loads(sens.read_text(encoding="utf-8")) if sens.exists() else None,
            "conteos_por_corrida": meta.get("conteos_por_corrida"), "medias_por_division": meta.get("medias_por_division"),
            "modelos_excluidos_por_regla": meta.get("excluidos_por_regla_R1_3"),
            "umbrales_provisionales": {"uso_principal": 0.60, "exclusion": 0.40},
            "limites": ["Los tres modelos son de la misma familia: el sesgo común no es identificable.",
                        "Sin muestra humana independiente no hay exactitud, solo consistencia.",
                        "Con 2 corridas por modelo, la moda por modelo deja ausente el ítem en que las corridas discrepan (018 R2.2)."]}


def modelos_comparacion() -> dict:
    """Comparación entre modelos, sesgo de B1 y sensibilidad al preámbulo (todo de scripts en src/)."""
    base = {"etiqueta": ETIQUETA_EXPO, "aviso": AVISO_EXPO, "estado_validacion": "sin_validar", "decision": "019"}
    c = _comparacion_cache()
    if c is None:
        return {**base, "estado": "no_disponible", "mensaje": "comparación no disponible"}
    return {**base, "estado": "disponible", "mensaje": "", **c}


def main_dataset(sinco_prefix=None, division=None, q=None, solo_con_anotacion: bool = False) -> tuple[pd.DataFrame, dict]:
    """Tabla MAIN completa o filtrada para descarga. Sin tabla -> Indisponible."""
    m = _main()
    if m is None:
        raise Indisponible("tabla MAIN no disponible")
    cods = _codigos_filtrados(sinco_prefix, division, None, q)
    if cods is not None:
        m = m[m["sinco_code"].isin(cods)]
    if solo_con_anotacion:
        m = m[m["tiene_anotacion"]]
    df = m.reset_index(drop=True)
    return df, {"n_filas": int(len(df)), "completo": cods is None and not solo_con_anotacion, "etiqueta": ETIQUETA_EXPO, "aviso": AVISO_EXPO,
                "estado_validacion": "sin_validar", "decision": "019"}
