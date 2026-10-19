"""Capa de servicio de solo lectura: lee los Parquet de data/processed/ y devuelve dicts JSON-serializables.

No escribe nada. No calcula ni expone scores, exposicion ni probabilidades. Las coincidencias SINCO-O*NET se leen
de data/processed/crosswalk.parquet con un esquema declarado (ver CrosswalkRow); si no existe, estado "pendiente".
"""
from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

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
    tablas = {n: int(len(_tabla(n))) for n in ["sinco", "sinco_descripcion", "sinco_ocupaciones_ejemplo", "sinco_funciones",
                                               "sinco_incluye_excluye", "sinco_referencias", "onet_ocupaciones", "tareas_onet_en"]}
    s = _tabla("sinco")
    return {"sinco": {"documento": f["documento"], "url": f["url"], "sha256": f["sha256"], "fecha_descarga": f["fecha_descarga"],
                      "niveles": {n: int((s["nivel"] == n).sum()) for n in NIVELES}},
            "onet": {"version": onet.get("version"), "url": onet.get("url"), "sha256": onet.get("sha256"),
                     "fecha_descarga": onet.get("fecha_descarga")},
            "crosswalk": {"estado": cw["estado"], "mensaje": cw["mensaje"], "n_filas": cw["n_filas"]},
            "tablas": tablas,
            "atribucion": "SINCO 2019: INEGI. O*NET: USDOL/ETA, licencia CC BY 4.0. Solo lectura; sin scores ni exposicion."}


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
