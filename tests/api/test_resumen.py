"""Pruebas de GET /api/resumen (KPIs y barras de coincidencias SINCO-O*NET). Usan copias temporales de las tablas."""
import json
import re
import shutil
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.api import service as S
from src.api.app import create_app

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data" / "processed"
TABLAS = ["sinco", "sinco_descripcion", "sinco_ocupaciones_ejemplo", "sinco_funciones", "sinco_incluye_excluye", "sinco_referencias",
          "sinco_fe_erratas", "sinco_fuente", "onet_ocupaciones", "tareas_onet_en", "crosswalk", "sinco_probabilidad_fo",
          "match_candidatos", "match_sinco_resumen"]
pytestmark = pytest.mark.skipif(not all((PROC / f"{t}.parquet").exists() for t in TABLAS), reason="faltan tablas procesadas")
LLAVES_PROB_OK = {"probabilidad_automatizacion_fo"}
R = "/api/resumen"


def _cliente(tmp_path, quitar=()):
    for n in TABLAS:
        if n not in quitar:
            shutil.copy(PROC / f"{n}.parquet", tmp_path / f"{n}.parquet")
    mp = pytest.MonkeyPatch(); mp.setattr(S, "PROC", tmp_path); S.limpiar_cache()
    return mp, TestClient(create_app(allowed_hosts=["testserver"]))


@pytest.fixture()
def api(tmp_path):
    mp, c = _cliente(tmp_path)
    yield c
    mp.undo(); S.limpiar_cache()


def _llaves(o):
    if isinstance(o, dict):
        for k, v in o.items():
            yield k; yield from _llaves(v)
    elif isinstance(o, list):
        for v in o:
            yield from _llaves(v)


def test_estructura_y_coherencia_con_tablas(api):
    r = api.get(R); assert r.status_code == 200
    j = r.json(); k = j["kpis"]
    assert j["estado"] == "disponible" and j["estado_validacion"] == "sin_validar"
    assert "NO validadas" in j["etiqueta_aviso"] and "!= exposicion" in j["etiqueta_aviso"]
    cw = pd.read_parquet(PROC / "crosswalk.parquet"); m = j["modelo"]; cwm = cw[cw["modelo"] == m]
    s = pd.read_parquet(PROC / "sinco.parquet")
    n_gu = int((s["nivel"] == "grupo_unitario").sum())
    assert k["grupos_unitarios"] == n_gu == cwm["sinco_code"].nunique()
    # estados desde el crosswalk (rango 1), no a mano
    est = cwm[cwm["rango"] == 1].set_index("sinco_code")["match_status"].value_counts()
    assert k["con_match_confiable"] == est.get("ok", 0) and k["baja_confianza"] == est.get("baja_confianza", 0)
    assert k["sin_coincidencia"] == est.get("sin_coincidencia", 0)
    assert k["con_match"] + k["sin_coincidencia"] == k["grupos_unitarios"]
    assert k["pct_con_match"] == round(100 * k["con_match"] / n_gu, 1)
    assert sum(e["n"] for e in j["por_estado"]) == n_gu
    # barras por division: suma = total y cada division coincide con el catalogo
    divs = j["por_division"]
    assert [d["division"] for d in divs] == [str(i) for i in range(1, 10)] and all(d["nombre"] for d in divs)
    assert sum(d["total"] for d in divs) == n_gu
    for d in divs:
        assert d["ok"] + d["baja_confianza"] + d["sin_coincidencia"] == d["total"]
        assert d["total"] == int(((s["nivel"] == "grupo_unitario") & (s["sinco_code"].str[0] == d["division"])).sum())
    for e in ("ok", "baja_confianza", "sin_coincidencia"):
        assert sum(d[e] for d in divs) == next(x["n"] for x in j["por_estado"] if x["estado"] == e)
    # O*NET distintas y similitud
    onet = pd.read_parquet(PROC / "onet_ocupaciones.parquet")
    assert k["onet_total"] == len(onet) and 0 < k["onet_distintas_emparejadas"] <= len(onet)
    con = set(est.index) and set(cwm[(cwm["rango"] == 1) & (cwm["match_status"] != "sin_coincidencia")]["sinco_code"])
    assert k["onet_distintas_emparejadas"] == cwm[cwm["sinco_code"].isin(con)]["onet_soc_code"].nunique()
    r1 = cwm[cwm["rango"] == 1]["similitud"]
    assert k["similitud_rango1_media"] == pytest.approx(r1.mean(), abs=1e-4) and k["similitud_rango1_mediana"] == pytest.approx(r1.median(), abs=1e-4)
    assert sum(b["n"] for b in j["histograma_similitud_rango1"]) == n_gu
    assert {x["tipo"]: x["n_pares"] for x in k["tipos_relacion"]} == cwm["tipo_relacion"].value_counts().to_dict()
    assert k["pares_top2"] == len(cwm)


def test_probabilidad_y_llaves_permitidas(api):
    j = api.get(R).json(); p = j["probabilidad_automatizacion_fo"]
    pf = pd.read_parquet(PROC / "sinco_probabilidad_fo.parquet"); pf = pf[pf["modelo"] == j["modelo"]]
    assert p["estado"] == "disponible" and p["estado_validacion"] == "sin_validar" and "Frey-Osborne" in p["etiqueta"]
    assert p["n_con_valor"] == int(pf["probabilidad_automatizacion_fo"].notna().sum()) and p["n_con_valor"] + p["n_na"] == p["n_grupos"] == 490
    assert {c["causa"]: c["n"] for c in p["causas_na"]} == pf["motivo_na"].value_counts().to_dict()
    # ningun campo de exposicion/score; unica llave de probabilidad: la permitida
    for k in set(_llaves(j)):
        assert not re.search(r"expos|score", k, re.I), k
        if re.search(r"prob|automat|frey|osborne", k, re.I):
            assert k in LLAVES_PROB_OK, k
    assert not re.search(r"exposicion a ia|\"score", json.dumps(j).replace("!= exposicion a IA", ""), re.I)


def test_modelo_alterno_y_desconocido(api):
    j = api.get(R, params={"modelo": "multilingual-e5-large"}).json()
    assert j["modelo"] == "multilingual-e5-large" and sum(d["total"] for d in j["por_division"]) == 490
    rs = pd.read_parquet(PROC / "match_sinco_resumen.parquet"); rs = rs[rs["modelo"] == "multilingual-e5-large"]
    assert j["kpis"]["sin_coincidencia"] == int((rs["match_status"] == "sin_coincidencia").sum())
    assert api.get(R, params={"modelo": "no-existe"}).status_code == 422


def test_estado_vacio_sin_crosswalk(tmp_path):
    mp, c = _cliente(tmp_path, quitar=("crosswalk",))
    try:
        r = c.get(R); j = r.json()
        assert r.status_code == 200 and j["estado"] == "pendiente" and "pendientes" in j["mensaje"]
        assert "kpis" not in j and "por_division" not in j
    finally:
        mp.undo(); S.limpiar_cache()


def test_sin_tabla_de_probabilidad(tmp_path):
    mp, c = _cliente(tmp_path, quitar=("sinco_probabilidad_fo",))
    try:
        j = c.get(R).json()
        assert j["estado"] == "disponible" and j["kpis"]["grupos_unitarios"] == 490
        assert j["probabilidad_automatizacion_fo"]["estado"] == "no_disponible" and j["probabilidad_automatizacion_fo"]["mensaje"] == "probabilidad no disponible"
        assert "n_con_valor" not in j["probabilidad_automatizacion_fo"]
    finally:
        mp.undo(); S.limpiar_cache()


def test_head_y_metodos(api):
    h = api.head(R); assert h.status_code == 200 and h.content == b""
    for m in ("post", "put", "delete", "patch", "options"):
        r = getattr(api, m)(R); assert r.status_code == 405 and r.headers["allow"] == "GET, HEAD"
    r = api.get(R); assert "default-src 'self'" in r.headers["content-security-policy"] and r.headers["cache-control"] == "no-store"


def test_pagina_principal_tiene_resumen_sin_cifras_fijas(api):
    html = api.get("/").text; js = api.get("/app.js").text
    assert 'id="v-resumen"' in html and 'id="tab-resumen"' in html and 'id="v-sinco"' in html
    assert "/api/resumen" in js and "490" not in html and "1016" not in js and "1,016" not in js
    assert "NO validadas" in js and "≠ exposición a IA" in js
