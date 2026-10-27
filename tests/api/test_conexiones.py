"""Pruebas de las conexiones SINCO <-> O*NET: /api/conexiones/{codigo}, /api/conexiones/flujo, /api/onet/occupations/{soc}/sinco
y de que la pagina estatica no lleve cifras fijas ni manejadores inline. Usan copias temporales de las tablas."""
import re
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api import service as S
from src.api.app import create_app

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data" / "processed"
STATIC = ROOT / "src" / "api" / "static"
TABLAS = ["sinco", "sinco_descripcion", "sinco_ocupaciones_ejemplo", "sinco_funciones", "sinco_incluye_excluye", "sinco_referencias",
          "sinco_fe_erratas", "sinco_fuente", "onet_ocupaciones", "tareas_onet_en", "crosswalk", "sinco_probabilidad_fo"]
pytestmark = pytest.mark.skipif(not all((PROC / f"{t}.parquet").exists() for t in TABLAS), reason="faltan tablas procesadas")
_PROHIBIDO_RE = re.compile(r"(score|expos|frey|osborne)", re.I)
_OK = re.compile(r"^(exposicion_agentes|aviso_exposicion|exposicion_(media|rango)_modelos)")   # decision 019; "probabilidad_automatizacion_fo*" tambien se admite


class _Prohibido:
    @staticmethod
    def search(k):
        return None if _OK.match(str(k)) else _PROHIBIDO_RE.search(str(k))


PROHIBIDO = _Prohibido()
ESTADOS = {"mejor_coincidencia", "segunda_opcion", "baja_confianza", "sin_coincidencia"}


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


def _unidad_con_dos(api):
    j = api.get("/api/resumen").json()
    assert j["estado"] == "disponible"
    for c in api.get("/api/download/dataset?formato=json&rango_max=1").json()["filas"]:
        d = api.get(f"/api/conexiones/{c['sinco_code']}").json()
        if len(d["coincidencias"]) == 2 and d["estado_grupo"] == "mejor_coincidencia":
            return d
    raise AssertionError("no hay grupo con dos coincidencias")


def test_conexion_estructura(api):
    d = _unidad_con_dos(api); s = d["sinco"]
    assert len(s["sinco_code"]) == 4 and s["titulo"] and s["division"] == s["sinco_code"][0]
    assert [m["rango"] for m in d["coincidencias"]] == [1, 2]
    assert d["coincidencias"][0]["estado"] == "mejor_coincidencia" and d["coincidencias"][1]["estado"] in ESTADOS
    for m in d["coincidencias"]:
        assert re.fullmatch(r"[0-9]{2}-[0-9]{4}\.[0-9]{2}", m["onet_soc_code"]) and m["soc_grupo"] == m["onet_soc_code"][:2]
        assert m["soc_grupo_nombre"] == S.SOC_GRANDES_GRUPOS[m["soc_grupo"]]
        assert 0 <= m["similitud"] <= 1 and m["onet_titulo"] and m["estado_validacion"] == "sin_validar"
        assert len(m["onet_descripcion_corta"]) <= 245
    assert d["estado_validacion"] == "sin_validar" and "NO validada" in d["explicacion"]
    assert d["probabilidad_automatizacion_fo"]["estado_validacion"] == "sin_validar"
    assert all(h["sinco_code"][:3] == s["subgrupo"] and h["sinco_code"] != s["sinco_code"] for h in d["hermanos"])


def test_conexion_anterior_siguiente_recorren_todos_los_grupos(api):
    arbol = api.get("/api/sinco/tree").json()
    unidades = []
    def rec(ns):
        for n in ns:
            rec(n["ch"]) if n["ch"] else unidades.append(n["c"])
    rec(arbol["raices"])
    d = api.get(f"/api/conexiones/{unidades[0]}").json()
    assert d["anterior"] is None
    vistos = [unidades[0]]
    while d["siguiente"]:
        vistos.append(d["siguiente"]["sinco_code"]); d = api.get(f"/api/conexiones/{vistos[-1]}").json()
    assert d["siguiente"] is None and vistos == unidades


def test_conexion_sin_coincidencia_etiqueta(api):
    r = api.get("/api/resumen").json()
    assert r["kpis"]["sin_coincidencia"] > 0
    filas = api.get("/api/download/dataset?formato=json&rango_max=2").json()["filas"]
    cod = next(f["sinco_code"] for f in filas if f["match_status"] == "sin_coincidencia")
    d = api.get(f"/api/conexiones/{cod}").json()
    assert d["estado_grupo"] == "sin_coincidencia" and all(m["estado"] == "sin_coincidencia" for m in d["coincidencias"])
    assert d["probabilidad_automatizacion_fo"]["valores"]["motivo_na"] == "sin_coincidencia"


def test_conexion_404_y_metodos(api):
    for ruta in ("/api/conexiones/42", "/api/conexiones/1000", "/api/conexiones/abcd", "/api/conexiones/0123", "/api/onet/occupations/99-9999.99/sinco", "/api/onet/occupations/x/sinco"):
        assert api.get(ruta).status_code == 404, ruta
    for ruta in ("/api/conexiones/4213", "/api/conexiones/flujo", "/api/onet/occupations/41-9091.00/sinco"):
        assert api.head(ruta).status_code == 200 and api.head(ruta).content == b""
        for m in ("post", "put", "delete", "patch", "options"):
            r = getattr(api, m)(ruta); assert r.status_code == 405 and r.headers["allow"] == "GET, HEAD", (m, ruta)
        h = api.get(ruta).headers; assert h["cache-control"] == "no-store" and "default-src 'self'" in h["content-security-policy"]


def test_inverso_onet_coherente_con_el_directo(api):
    d = _unidad_con_dos(api); m = d["coincidencias"][0]
    inv = api.get(f"/api/onet/occupations/{m['onet_soc_code']}/sinco").json()
    assert inv["estado"] == "disponible" and inv["total"] == len(inv["filas"]) >= 1 and inv["estado_validacion"] == "sin_validar"
    fila = next(f for f in inv["filas"] if f["sinco_code"] == d["sinco"]["sinco_code"])
    assert fila["rango"] == 1 and fila["similitud"] == m["similitud"] and fila["sinco_titulo"] == d["sinco"]["titulo"]
    sims = [f["similitud"] for f in inv["filas"]]; assert sims == sorted(sims, reverse=True)
    assert "NO validadas" in inv["aviso"]


def test_inverso_onet_vacio_es_un_estado_valido(api):
    usados = {f["onet_soc_code"] for f in api.get("/api/download/dataset?formato=json").json()["filas"]}
    libre = next(o["onet_soc_code"] for o in api.get("/api/onet/occupations?limit=200").json()["resultados"] if o["onet_soc_code"] not in usados)
    inv = api.get(f"/api/onet/occupations/{libre}/sinco").json()
    assert inv["estado"] == "disponible" and inv["total"] == 0 and inv["filas"] == []


def test_flujo_suma_los_grupos_unitarios(api):
    f = api.get("/api/conexiones/flujo").json(); k = api.get("/api/resumen").json()["kpis"]
    assert f["estado"] == "disponible" and len(f["divisiones"]) == 9 and "bls.gov" in f["soc_fuente"] or "BLS" in f["soc_fuente"]
    assert sum(e["n"] for e in f["enlaces"]) == f["total_grupos"] == k["grupos_unitarios"]
    assert sum(g["n"] for g in f["grupos_soc"]) == f["total_grupos"]
    for e in f["enlaces"]:
        assert e["n"] == e["ok"] + e["baja_confianza"] + e["sin_coincidencia"] and e["soc_grupo"] in S.SOC_GRANDES_GRUPOS
    assert set(S.SOC_GRANDES_GRUPOS) == {f"{i}" for i in (11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33, 35, 37, 39, 41, 43, 45, 47, 49, 51, 53, 55)}


def test_sin_llaves_de_exposicion(api):
    for ruta in ("/api/conexiones/4213", "/api/conexiones/1329", "/api/conexiones/flujo", "/api/onet/occupations/41-9091.00/sinco"):
        malas = [k for k in _llaves(api.get(ruta).json()) if PROHIBIDO.search(str(k))]
        assert not malas, (ruta, malas)
        otras = [k for k in _llaves(api.get(ruta).json()) if "prob" in str(k).lower() and not str(k).startswith("probabilidad_automatizacion_fo")]
        assert not otras, (ruta, otras)


def test_estado_vacio_sin_crosswalk(tmp_path):
    mp, c = _cliente(tmp_path, quitar=("crosswalk",))
    try:
        d = c.get("/api/conexiones/4213").json()
        assert d["estado"] == "pendiente" and d["coincidencias"] == [] and d["estado_grupo"] is None and d["sinco"]["titulo"]
        f = c.get("/api/conexiones/flujo").json()
        assert f["estado"] == "pendiente" and f["enlaces"] == [] and f["grupos_soc"] == [] and len(f["divisiones"]) == 9
        i = c.get("/api/onet/occupations/41-9091.00/sinco").json()
        assert i["estado"] == "pendiente" and i["filas"] == [] and i["total"] == 0
    finally:
        mp.undo(); S.limpiar_cache()


def test_pagina_sin_cifras_fijas_ni_inline(api):
    html = api.get("/").text; js = api.get("/app.js").text; css = api.get("/style.css").text
    for nombre, txt in (("html", html), ("js", js)):
        assert not re.search(r"\b(490|980|1016|1,016|714|465|407)\b", txt), nombre
    for id_ in ("tab-conexiones", "v-conexiones", "q-con", "con-lienzo", "flujo", "guia", "copiar", "q-global"):
        assert f'id="{id_}"' in html, id_
    assert not re.search(r"\son[a-z]+\s*=", html) and "<script>" not in html and "javascript:" not in html
    assert not re.search(r"\.onclick\s*=|eval\(|new Function|document\.write", js)
    assert "https://" not in html.replace("https://www.", "") and "http://www.w3.org/2000/svg" in js and not re.search(r"https?://(?!www\.w3\.org)", js + css)
    for frase in ("Cómo leer esto", "baja confianza", "sin coincidencia", "no es exposición", "NO validada"):
        assert frase.lower() in (html + js).lower(), frase
    assert "/api/conexiones/" in js and "/sinco`" in js and "location.hash" in js and "Ver como tabla" in js
    h = api.get("/")
    assert "script-src 'self'" in h.headers["content-security-policy"] and "unsafe-inline" not in h.headers["content-security-policy"].split("script-src")[1].split(";")[0]


def test_archivos_estaticos_coinciden_con_disco(api):
    assert api.get("/app.js").content == (STATIC / "app.js").read_bytes()
