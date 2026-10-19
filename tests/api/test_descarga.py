"""Pruebas de descarga del dataset y de /api/probabilidad (FastAPI + TestClient).

Usan COPIAS temporales de las tablas reales (crosswalk top-2 y sinco_probabilidad_fo); el original nunca se escribe.
Los casos "sin tabla de probabilidad" y "con texto malicioso" usan copias modificadas en tmp_path.
"""
import hashlib
import io
import json
import re
import shutil
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
import pytest
from fastapi.testclient import TestClient

from src.api import service as S
from src.api.app import create_app

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data" / "processed"
TABLAS = ["sinco", "sinco_descripcion", "sinco_ocupaciones_ejemplo", "sinco_funciones", "sinco_incluye_excluye", "sinco_referencias",
          "sinco_fe_erratas", "sinco_fuente", "onet_ocupaciones", "tareas_onet_en", "crosswalk", "sinco_probabilidad_fo", "match_candidatos"]
pytestmark = pytest.mark.skipif(not all((PROC / f"{t}.parquet").exists() for t in TABLAS), reason="faltan tablas procesadas")


def _preparar(tmp_path, mp, quitar=(), modificar=None):
    for n in TABLAS:
        if n not in quitar:
            shutil.copy(PROC / f"{n}.parquet", tmp_path / f"{n}.parquet")
    if modificar:
        modificar(tmp_path)
    mp.setattr(S, "PROC", tmp_path)
    S.limpiar_cache()


@pytest.fixture()
def api(tmp_path):
    mp = pytest.MonkeyPatch()
    _preparar(tmp_path, mp)
    with TestClient(create_app(allowed_hosts=["testserver"])) as c:
        yield c
    mp.undo(); S.limpiar_cache()


def _client(tmp_path, quitar=(), modificar=None):
    mp = pytest.MonkeyPatch()
    _preparar(tmp_path, mp, quitar, modificar)
    return mp, TestClient(create_app(allowed_hosts=["testserver"]))


def _csv(r):
    return pd.read_csv(io.StringIO(r.content.decode("utf-8-sig")), dtype={"sinco_code": str})


D = "/api/download/dataset"


def test_completo_980_filas_en_tres_formatos(api):
    n = len(pd.read_parquet(PROC / "crosswalk.parquet"))
    assert n == 980
    rc, rj, rp = api.get(D + "?formato=csv"), api.get(D + "?formato=json"), api.get(D + "?formato=parquet")
    assert rc.status_code == rj.status_code == rp.status_code == 200
    dc = _csv(rc)
    j = rj.json()
    dp = pq.read_table(io.BytesIO(rp.content)).to_pandas()
    assert len(dc) == len(j["filas"]) == len(dp) == n
    assert rc.headers["X-Filas"] == "980" and rc.headers["X-Filas-Truncadas"] == "false"
    # una fila por (SINCO, O*NET), 490 SINCO x rangos 1 y 2
    assert not dc.duplicated(["sinco_code", "onet_soc_code"]).any() and dc["sinco_code"].nunique() == 490
    assert sorted(dc["rango"].unique()) == [1, 2]
    for c in ["sinco_code", "sinco_titulo", "nivel", "division", "rango", "onet_soc_code", "onet_titulo", "similitud", "margen", "modelo",
              "tipo_relacion", "match_status", "baja_confianza", "estado_validacion", "run_id", "probabilidad_automatizacion_fo",
              "probabilidad_automatizacion_fo_media_uniforme", "probabilidad_automatizacion_fo_min", "probabilidad_automatizacion_fo_max",
              "probabilidad_automatizacion_fo_top1", "n_candidatos", "cobertura_peso_fo", "motivo_na", "probabilidad_es_na"]:
        assert c in dc.columns and c in j["filas"][0] and c in dp.columns, c
    assert set(dc["estado_validacion"]) == {"sin_validar"} and set(dc["modelo"]) == {"bge-m3"}
    # la probabilidad agregada por SINCO coincide con la tabla fuente (principal)
    src = pd.read_parquet(PROC / "sinco_probabilidad_fo.parquet")
    src = src[src["es_modelo_principal"]].set_index("sinco_code")["probabilidad_automatizacion_fo"]
    chk = dc.drop_duplicates("sinco_code").set_index("sinco_code")["probabilidad_automatizacion_fo"]
    assert (chk.fillna(-1).round(9) == src.reindex(chk.index).fillna(-1).round(9)).all()
    # procedencia: cabecera, meta JSON y metadatos Parquet
    assert "CC BY 4.0" in rc.headers["X-Atribucion"] and "INEGI" in rc.headers["X-Atribucion"] and "NO validados" in rc.headers["X-Atribucion"]
    assert "Frey y Osborne" in j["meta"]["atribucion"] and j["meta"]["probabilidad_automatizacion_fo"]["estado_validacion"] == "sin_validar"
    assert b"NO validados" in pq.read_schema(io.BytesIO(rp.content)).metadata[b"atribucion"]
    # nombre de archivo fijo
    assert rc.headers["Content-Disposition"] == 'attachment; filename="sinco_onet_completo.csv"'
    assert rp.headers["Content-Disposition"] == 'attachment; filename="sinco_onet_completo.parquet"'


def test_filtros_dan_subconjuntos_coherentes(api):
    full = _csv(api.get(D))
    d4 = _csv(api.get(D + "?division=4"))
    assert 0 < len(d4) < len(full) and set(d4["division"]) == {4} and d4["sinco_code"].str.startswith("4").all()
    assert len(d4) == (full["division"] == 4).sum()
    pre = _csv(api.get(D + "?sinco_prefix=42"))
    assert len(pre) and pre["sinco_code"].str.startswith("42").all()
    r1 = _csv(api.get(D + "?rango_max=1"))
    assert len(r1) == 490 and set(r1["rango"]) == {1}
    # q insensible a acentos: "telefono" encuentra "telef..." (4213 Vendedores por telefono)
    q = api.get(D + "?q=telefono")
    assert "4213" in set(_csv(q)["sinco_code"]) and q.headers["Content-Disposition"].endswith('_filtrado.csv"')
    assert len(_csv(api.get(D + "?nivel=grupo_unitario"))) == 980 and len(_csv(api.get(D + "?nivel=division"))) == 0
    sp = _csv(api.get(D + "?solo_con_probabilidad=true"))
    assert sp["probabilidad_automatizacion_fo"].notna().all() and 0 < len(sp) < len(full)
    assert api.get("/api/download/conteo?division=4").json()["n_filas"] == len(d4)
    assert api.get("/api/download/conteo").json()["completo"] is True


def test_modelo_alterno_desde_match_candidatos(api):
    alt = _csv(api.get(D + "?modelo=multilingual-e5-large"))
    assert len(alt) == 980 and set(alt["modelo"]) == {"multilingual-e5-large"}
    assert alt["probabilidad_automatizacion_fo"].notna().any()


def test_filtros_invalidos(api):
    for u in ("?formato=xls", "?nivel=x", "?division=0", "?division=10", "?sinco_prefix=0123", "?sinco_prefix=12345", "?sinco_prefix=ab",
              "?q=" + "a" * 101, "?rango_max=3", "?rango_max=0", "?modelo=no_existe", "?solo_con_probabilidad=quizas"):
        r = api.get(D + u)
        assert r.status_code == 422 and "error" in r.json(), u
    assert api.get("/api/probabilidad?offset=-1").status_code == 422
    assert api.get("/api/probabilidad?modelo=zz").status_code == 422
    assert api.get("/api/probabilidad/99999").status_code == 404


def test_inyeccion_de_formulas_csv(tmp_path):
    def mod(d):
        c = pd.read_parquet(d / "crosswalk.parquet")
        c.loc[0, "notas"] = "=cmd|' /C calc'!A0"
        c.loc[0, "fuente"] = "@SUM(1+1)"
        c.loc[1, "fuente"] = "+1+1"
        c.loc[2, "fuente"] = "-2+3"
        c.to_parquet(d / "crosswalk.parquet")
        o = pd.read_parquet(d / "onet_ocupaciones.parquet")
        o.loc[o["onet_soc_code"] == c.loc[0, "onet_soc_code"], "titulo_en"] = "=HYPERLINK(\"http://x\")"
        o.to_parquet(d / "onet_ocupaciones.parquet")
    mp, cl = _client(tmp_path, modificar=mod)
    try:
        with cl as c:
            r = c.get(D + "?formato=csv&sinco_prefix=111")
            df = _csv(r)
            fuentes = list(df["fuente"][:3])
            assert fuentes == ["'@SUM(1+1)", "'+1+1", "'-2+3"]
            assert df["onet_titulo"][0].startswith("'=HYPERLINK")
            # ninguna celda de texto empieza con caracter de formula
            for col in df.select_dtypes(include=["object", "str"]):
                assert not df[col].dropna().astype(str).str.match(r"^[=+\-@\t\r]").any(), col
            # los numeros (p. ej. negativos) no se alteran; JSON/Parquet conservan el valor original
            assert pd.api.types.is_numeric_dtype(df["similitud"])
            assert c.get(D + "?formato=json&sinco_prefix=111").json()["filas"][0]["fuente"] == "@SUM(1+1)"
    finally:
        mp.undo(); S.limpiar_cache()


def test_sin_tabla_de_probabilidad(tmp_path):
    mp, cl = _client(tmp_path, quitar=("sinco_probabilidad_fo",))
    try:
        with cl as c:
            e = c.get("/api/probabilidad").json()
            assert e["estado"] == "no_disponible" and e["mensaje"] == "probabilidad no disponible" and e["resultados"] == []
            assert e["estado_validacion"] == "sin_validar" and "Frey-Osborne" in e["etiqueta"]
            d = c.get("/api/sinco/4213").json()["probabilidad_automatizacion_fo"]
            assert d["estado"] == "no_disponible" and d["valores"] is None
            assert c.get("/api/meta").json()["probabilidad_automatizacion_fo"]["estado"] == "no_disponible"
            r = c.get(D + "?formato=csv")
            df = _csv(r)
            assert r.status_code == 200 and len(df) == 980 and not [x for x in df.columns if "probabilidad" in x]
            assert r.headers["X-Probabilidad"] == "no_disponible"
            j = c.get(D + "?formato=json").json()
            assert j["meta"]["probabilidad_automatizacion_fo"] == {"estado": "no_disponible", "mensaje": "probabilidad no disponible"}
            assert c.get(D + "?solo_con_probabilidad=true").status_code == 409
            assert c.get("/api/download/conteo").json()["probabilidad_automatizacion_fo"]["estado"] == "no_disponible"
    finally:
        mp.undo(); S.limpiar_cache()


def test_sin_crosswalk_responde_409(tmp_path):
    mp, cl = _client(tmp_path, quitar=("crosswalk",))
    try:
        with cl as c:
            r = c.get(D)
            assert r.status_code == 409 and "pendientes" in r.json()["error"]
    finally:
        mp.undo(); S.limpiar_cache()


def test_probabilidad_endpoints_y_detalle(api):
    lst = api.get("/api/probabilidad?limit=5").json()
    assert lst["estado"] == "disponible" and lst["total"] == 490 and len(lst["resultados"]) == 5 and lst["modelo"] == "bge-m3"
    assert lst["estado_validacion"] == "sin_validar" and lst["etiqueta"] == "probabilidad de automatizacion (Frey-Osborne)"
    assert "NO es" in lst["que_no_es"] or "No es" in lst["que_no_es"]
    pag2 = api.get("/api/probabilidad?limit=5&offset=5").json()["resultados"]
    assert pag2[0]["sinco_code"] != lst["resultados"][0]["sinco_code"]
    assert api.get("/api/probabilidad?limit=99999").json()["limit"] == 200
    d = api.get("/api/probabilidad/1111").json()
    assert d["estado"] == "disponible" and d["valores"]["estado_validacion"] == "sin_validar" and d["valores"]["etiqueta"].startswith("probabilidad")
    assert api.get("/api/probabilidad/42").json()["estado"] == "sin_fila"
    det = api.get("/api/sinco/1111").json()
    assert det["probabilidad_automatizacion_fo"]["valores"]["probabilidad_automatizacion_fo"] == d["valores"]["probabilidad_automatizacion_fo"]
    assert [f["rango"] for f in det["coincidencias_onet"]["filas"]] == [1, 2] and det["coincidencias_onet"]["filas"][0]["onet_titulo"]


def test_sin_exposicion_en_respuestas_de_descarga(api):
    j = api.get(D + "?formato=json&division=1").json()
    ok = re.compile(r"^probabilidad_(automatizacion_fo|es_na|estado_validacion)")
    malas = [k for k in set(j["filas"][0]) | set(j["meta"]) if re.search(r"(score|expos|prob|frey|osborne)", k, re.I) and not ok.match(k)]
    assert not malas, malas
    assert not [k for k in set(j["filas"][0]) if re.search(r"(score|expos)", k, re.I)]


def test_head_y_metodos(api):
    h = api.head(D)
    assert h.status_code == 200 and h.content == b"" and "attachment" in h.headers["Content-Disposition"]
    for m in ("post", "put", "delete", "patch"):
        for ruta in (D, "/api/probabilidad", "/api/download/conteo"):
            r = getattr(api, m)(ruta)
            assert r.status_code == 405 and "GET" in r.headers["Allow"], (m, ruta)
    assert api.options(D).status_code == 405
    r = api.get(D)
    assert r.headers["X-Content-Type-Options"] == "nosniff" and r.headers["Cache-Control"] == "no-store"


def test_descarga_no_escribe_en_data(api):
    def huella():
        return {str(p): hashlib.md5(p.read_bytes()).hexdigest() for p in (ROOT / "data").rglob("*") if p.is_file()}
    a = huella()
    for f in ("csv", "json", "parquet"):
        api.get(f"{D}?formato={f}")
    api.get("/api/probabilidad"); api.get("/api/download/conteo?division=4")
    assert huella() == a
