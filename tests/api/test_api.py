"""Pruebas de la API de solo lectura (FastAPI + TestClient; httpx es dependencia de TestClient).

Los tests NO dependen de data/processed/crosswalk.parquet real: usan una copia temporal de las tablas sin ese archivo
y, para el crosswalk, archivos sinteticos en tmp_path.
"""
import hashlib
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
# Decision del usuario 2026-10-19: solo se admite la probabilidad de automatizacion (Frey-Osborne): llaves
# "probabilidad_automatizacion_fo*" y las rutas /api/probabilidad*. Decision 019 (usuario 2026-10-23): ademas se admite la exposicion
# teorica por modelos SOLO bajo las llaves/rutas de abajo (rotulada, sin validar); los scores (E_g) siguen prohibidos.
_PROB_OK = re.compile(r"^(probabilidad_automatizacion_fo|/api/probabilidad|exposicion_agentes|aviso_exposicion|exposicion_(media|rango)_modelos|/api/exposicion|/api/modelos/comparacion|/api/download/main)")
_PROHIBIDO_RE = re.compile(r"(score|expos|prob|frey|osborne)", re.I)


class _Prohibido:
    @staticmethod
    def search(k):
        k = str(k)
        return None if _PROB_OK.match(k) else _PROHIBIDO_RE.search(k)


PROHIBIDO = _Prohibido()
TABLAS = ["sinco", "sinco_descripcion", "sinco_ocupaciones_ejemplo", "sinco_funciones", "sinco_incluye_excluye", "sinco_referencias",
          "sinco_fe_erratas", "sinco_fuente", "onet_ocupaciones", "tareas_onet_en"]


@pytest.fixture(scope="module", autouse=True)
def proc_sin_crosswalk(tmp_path_factory):
    """Copia temporal de las tablas necesarias, sin crosswalk.parquet (el real no interviene en las pruebas)."""
    d = tmp_path_factory.mktemp("proc")
    for n in TABLAS:
        shutil.copy(PROC / f"{n}.parquet", d / f"{n}.parquet")
    mp = pytest.MonkeyPatch()
    mp.setattr(S, "PROC", d)
    S.limpiar_cache()
    yield d
    mp.undo()
    S.limpiar_cache()


@pytest.fixture(scope="module")
def base():
    with TestClient(create_app(allowed_hosts=["testserver"])) as c:
        yield c


def get(base, path):
    r = base.get(path)
    return r.status_code, r.headers, r.content


def gj(base, path):
    r = base.get(path)
    return r.status_code, r.json()


def llaves(o):
    if isinstance(o, dict):
        for k, v in o.items():
            yield k
            yield from llaves(v)
    elif isinstance(o, list):
        for v in o:
            yield from llaves(v)


def test_health_y_meta(base):
    assert gj(base, "/api/health") == (200, {"ok": True})
    st, m = gj(base, "/api/meta")
    assert st == 200
    assert m["sinco"]["niveles"] == {"division": 9, "grupo_principal": 52, "subgrupo": 163, "grupo_unitario": 490}
    h = json.loads((ROOT / "data/raw/manifest.json").read_text(encoding="utf-8"))
    assert m["sinco"]["sha256"] == next(e["sha256"] for e in h if e["id"] == "sinco_2019_pdf")
    assert m["onet"]["version"].startswith("O*NET")
    assert m["tablas"]["tareas_onet_en"] == len(pd.read_parquet(PROC / "tareas_onet_en.parquet"))


def test_arbol_completo_y_coherente(base):
    st, t = gj(base, "/api/sinco/tree")
    assert st == 200 and t["n_nodos"] == 714 and len(t["raices"]) == 9
    s = pd.read_parquet(PROC / "sinco.parquet")
    cods = []

    def rec(nodes, padre):
        for n in nodes:
            cods.append(n["c"])
            assert n["n"] == len(n["c"])
            assert padre is None or n["c"].startswith(padre) and len(n["c"]) == len(padre) + 1
            rec(n["ch"], n["c"])
    rec(t["raices"], None)
    assert sorted(cods) == sorted(s["sinco_code"]) and len(set(cods)) == 714


def test_detalle_grupo_unitario(base):
    st, d = gj(base, "/api/sinco/4213")
    assert st == 200
    assert d["nodo"]["titulo"].startswith("Vendedores por tel")
    assert [a["sinco_code"] for a in d["ancestros"]] == ["4", "42", "421"]
    assert d["descripcion"]["texto"] and len(d["funciones"]) == 6 and len(d["ocupaciones_ejemplo"]) == 2
    ex = [x for x in d["incluye_excluye"] if x["tipo"] == "excluye"]
    assert ex and any(r["codigo"] == "3212" and r["existe_en_catalogo"] for x in ex for r in x["referencias"])
    # errata marcada pero no aplicada
    st, e = gj(base, "/api/sinco/5115")
    assert e["fe_de_erratas"] and any(o["afectado_por_errata"] for o in e["ocupaciones_ejemplo"])
    assert any(o["ocupacion"] == "Barista." for o in e["ocupaciones_ejemplo"])


def test_detalle_nivel_superior_y_404(base):
    st, d = gj(base, "/api/sinco/42")
    assert st == 200 and d["funciones"] == [] and len(d["hijos"]) >= 1 and d["descripcion"]["texto"]
    assert gj(base, "/api/sinco/99999")[0] == 404
    assert gj(base, "/api/sinco/0123")[0] == 404
    assert gj(base, "/api/nada")[0] == 404


def test_busqueda_sinco(base):
    st, r = gj(base, "/api/sinco/search?q=barista")
    assert st == 200 and r["total"] >= 1 and any(x["sinco_code"] == "5114" for x in r["resultados"])
    assert gj(base, "/api/sinco/search?q=4213")[1]["resultados"][0]["sinco_code"] == "4213"
    assert gj(base, "/api/sinco/search?q=a")[1]["total"] == 0
    # insensible a acentos
    assert gj(base, "/api/sinco/search?q=telefono")[1]["total"] >= 1


def test_onet(base):
    st, r = gj(base, "/api/onet/occupations?limit=5")
    assert st == 200 and r["total"] == 1016 and len(r["resultados"]) == 5 and set(r["resultados"][0]) == {"onet_soc_code", "titulo_en", "n_tareas"}
    assert gj(base, "/api/onet/occupations?limit=9999")[1]["limit"] == 200
    st, d = gj(base, "/api/onet/occupations/11-1011.00")
    assert st == 200 and d["titulo_en"] == "Chief Executives" and d["n_tareas"] == len(d["tareas"]) == 31
    assert set(d["tareas"][0]) == {"task_id", "tarea_en"}
    assert gj(base, "/api/onet/occupations/99-9999.99")[0] == 404
    assert gj(base, "/api/onet/occupations?q=nurse")[1]["total"] > 0


def test_crosswalk_pendiente_si_no_existe(base):
    assert not (S.PROC / "crosswalk.parquet").exists()  # el fixture aisla el crosswalk real
    st, c = gj(base, "/api/crosswalk")
    assert st == 200 and c["estado"] == "pendiente" and c["mensaje"] == "coincidencias pendientes de crosswalk" and c["filas"] == []
    assert gj(base, "/api/sinco/4213")[1]["coincidencias_onet"]["estado"] == "pendiente"
    assert gj(base, "/api/onet/occupations/11-1011.00")[1]["coincidencias_sinco"]["filas"] == []
    sc = gj(base, "/api/crosswalk/schema")[1]
    assert sc["requeridas"] == ["sinco_code", "onet_soc_code", "tipo_relacion", "fuente", "estado_validacion"]


def _con_crosswalk(monkeypatch, tmp_path, df):
    df.to_parquet(tmp_path / "crosswalk.parquet")
    for n in TABLAS:
        shutil.copy(PROC / f"{n}.parquet", tmp_path / f"{n}.parquet")
    monkeypatch.setattr(S, "PROC", tmp_path)
    S.limpiar_cache()


def test_crosswalk_valido_se_lee_y_filtra_scores(monkeypatch, tmp_path):
    df = pd.DataFrame([{"sinco_code": "1111", "onet_soc_code": "11-1011.00", "tipo_relacion": "1:N", "fuente": "manual",
                        "estado_validacion": "sin_validar", "exposure_score": 0.9, "run_id": "r1"}])
    _con_crosswalk(monkeypatch, tmp_path, df)
    try:
        c = S.crosswalk(sinco_code="1111")
        assert c["estado"] == "disponible" and len(c["filas"]) == 1
        assert "exposure_score" not in c["filas"][0] and c["columnas_ignoradas"] == ["exposure_score"]
        assert "aviso" in c
        assert S.crosswalk(sinco_code="1112")["filas"] == []
    finally:
        monkeypatch.undo(); S.limpiar_cache()


@pytest.mark.parametrize("cambio,msg", [({"tipo_relacion": "2:2"}, "fila invalida"), ({"sinco_code": "9998"}, "no existen"),
                                        ({"estado_validacion": "quiza"}, "fila invalida"), ({"fuente": ""}, "fila invalida")])
def test_crosswalk_invalido(monkeypatch, tmp_path, cambio, msg):
    fila = {"sinco_code": "1111", "onet_soc_code": "11-1011.00", "tipo_relacion": "1:1", "fuente": "manual", "estado_validacion": "validado"}
    fila.update(cambio)
    _con_crosswalk(monkeypatch, tmp_path, pd.DataFrame([fila]))
    try:
        c = S.crosswalk()
        assert c["estado"] == "esquema_invalido" and msg in c["mensaje"] and c["filas"] == []
    finally:
        monkeypatch.undo(); S.limpiar_cache()


def test_crosswalk_faltan_columnas(monkeypatch, tmp_path):
    _con_crosswalk(monkeypatch, tmp_path, pd.DataFrame([{"sinco_code": "1111", "onet_soc_code": "11-1011.00"}]))
    try:
        assert S.crosswalk()["estado"] == "esquema_invalido"
    finally:
        monkeypatch.undo(); S.limpiar_cache()


def test_solo_lectura_metodos(base):
    for m in ("post", "put", "delete", "patch", "options"):
        for ruta in ("/api/crosswalk", "/api/nada", "/", "/docs"):
            r = getattr(base, m)(ruta) if m != "options" else base.options(ruta)
            assert r.status_code == 405 and "GET" in r.headers["Allow"], (m, ruta)
    assert base.head("/api/health").status_code == 200 and base.head("/api/health").content == b""


def test_sin_scores_ni_exposicion_en_respuestas(base):
    rutas = ["/api/meta", "/api/sinco/tree", "/api/sinco/4213", "/api/sinco/42", "/api/sinco/search?q=venta",
             "/api/onet/occupations?limit=200", "/api/onet/occupations/11-1011.00", "/api/crosswalk", "/api/crosswalk/schema",
             "/api/probabilidad", "/api/probabilidad/4213"]
    for r in rutas:
        _, d = gj(base, r)
        malas = [k for k in llaves(d) if PROHIBIDO.search(str(k))]
        # el JSON schema del crosswalk menciona la prohibicion solo en texto, no como llave de datos
        assert not malas, (r, malas)


def test_estaticos_y_traversal(base):
    st, h, b = get(base, "/")
    assert st == 200 and b"SINCO 2019" in b and "text/html" in h["Content-Type"]
    assert get(base, "/app.js")[0] == 200 and get(base, "/style.css")[0] == 200
    assert get(base, "/..%2f..%2fdata/raw/manifest.json")[0] == 404
    assert get(base, "/%2e%2e/%2e%2e/data/raw/manifest.json")[0] == 404
    assert get(base, "/..%5c..%5cdata/raw/manifest.json")[0] == 404
    assert get(base, "/%2e%2e%2fservice.py")[0] == 404
    assert get(base, "/../service.py")[0] == 404
    assert get(base, "/service.py")[0] == 404 and get(base, "/app.py")[0] == 404
    assert get(base, "/static/../app.js")[0] in (200, 404)
    assert get(base, "/index.html%00.png")[0] == 404


def test_no_escribe_en_data(base):
    def huella():
        return {str(p): hashlib.md5(p.read_bytes()).hexdigest() for p in (ROOT / "data").rglob("*") if p.is_file()}
    a = huella()
    for r in ["/api/meta", "/api/sinco/4213", "/api/onet/occupations/11-1011.00", "/api/crosswalk"]:
        get(base, r)
    assert huella() == a


# ---------------------------------------------------------------- FastAPI / endurecimiento
def test_openapi_y_docs(base):
    st, o = gj(base, "/openapi.json")
    assert st == 200 and set(o["paths"]) == {"/api/health", "/api/meta", "/api/sinco/tree", "/api/sinco/search", "/api/sinco/{codigo}",
                                            "/api/onet/occupations", "/api/onet/occupations/{soc}", "/api/crosswalk", "/api/crosswalk/schema",
                                            "/api/probabilidad", "/api/probabilidad/{codigo}", "/api/download/conteo", "/api/download/dataset", "/api/resumen",
                                                "/api/conexiones/flujo", "/api/conexiones/{codigo}", "/api/onet/occupations/{soc}/sinco",
                                                "/api/exposicion", "/api/exposicion/{codigo}", "/api/modelos/comparacion", "/api/download/main"}
    assert all(set(v) == {"get"} for v in o["paths"].values())  # sin escritura en el contrato
    assert not [k for k in llaves(o["paths"]) if PROHIBIDO.search(str(k))]
    assert get(base, "/docs")[0] == 200


def test_cabeceras_y_cors_por_defecto(base):
    r = base.get("/api/health", headers={"Origin": "http://evil.example"})
    assert r.headers["X-Content-Type-Options"] == "nosniff" and r.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'self'" in r.headers["Content-Security-Policy"] and r.headers["Cache-Control"] == "no-store"
    assert "access-control-allow-origin" not in r.headers


def test_cors_configurable():
    with TestClient(create_app(cors_origins=["http://ok.example"], allowed_hosts=["testserver"])) as c:
        assert c.get("/api/health", headers={"Origin": "http://ok.example"}).headers["access-control-allow-origin"] == "http://ok.example"
        assert "access-control-allow-origin" not in c.get("/api/health", headers={"Origin": "http://evil.example"}).headers
        pre = c.options("/api/health", headers={"Origin": "http://ok.example", "Access-Control-Request-Method": "POST"})
        assert pre.status_code == 400  # POST no permitido en preflight


def test_host_no_permitido():
    with TestClient(create_app(allowed_hosts=["127.0.0.1"])) as c:  # testserver no esta permitido
        assert c.get("/api/health").status_code == 400
        assert c.get("/api/health", headers={"Host": "127.0.0.1:8001"}).status_code == 200


def test_limites_de_busqueda_y_paginacion(base):
    assert base.get("/api/sinco/search?q=" + "a" * 101).status_code == 422
    assert base.get("/api/onet/occupations?q=" + "a" * 101).status_code == 422
    assert base.get("/api/onet/occupations?offset=-1").status_code == 422
    assert base.get("/api/onet/occupations?offset=100001").status_code == 422
    assert gj(base, "/api/onet/occupations?limit=0")[1]["limit"] == 1
    assert len(gj(base, "/api/sinco/search?q=venta&limit=100000")[1]["resultados"]) <= 100
    assert len(gj(base, "/api/sinco/search?q=venta&limit=2")[1]["resultados"]) == 2


def test_prohibido_sigue_prohibiendo_exposicion():
    for k in ("exposure_score", "exposicion_ia", "score", "probabilidad_perdida_empleo", "frey_osborne_p", "probabilidad"):
        assert PROHIBIDO.search(k), k
    for k in ("probabilidad_automatizacion_fo", "probabilidad_automatizacion_fo_min", "/api/probabilidad/{codigo}"):
        assert not PROHIBIDO.search(k), k


def test_crosswalk_a1_se_sirve_con_similitud_sin_scores(monkeypatch, tmp_path, base):
    fila = {"sinco_code": "1111", "onet_soc_code": "11-1011.00", "tipo_relacion": "M:N", "fuente": "semiautomatico_embeddings_A1_bge-m3",
            "estado_validacion": "sin_validar", "run_id": "match-A1-x", "modelo": "bge-m3", "rango": 1, "similitud": 0.68, "margen": 0.03,
            "baja_confianza": False, "match_status": "ok"}
    _con_crosswalk(monkeypatch, tmp_path, pd.DataFrame([fila]))
    try:
        st, c = gj(base, "/api/crosswalk?sinco_code=1111")
        f = c["filas"][0]
        assert st == 200 and c["estado"] == "disponible" and f["similitud"] == 0.68 and f["rango"] == 1 and f["estado_validacion"] == "sin_validar"
        assert not [k for k in llaves(c) if PROHIBIDO.search(str(k))]
        assert gj(base, "/api/onet/occupations/11-1011.00")[1]["coincidencias_sinco"]["n_filas"] == 1
    finally:
        monkeypatch.undo(); S.limpiar_cache()
