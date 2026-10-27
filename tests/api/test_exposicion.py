"""Exposicion del metodo de agentes en la API (decision 019): rotulada, sin validar, sin E_g, con estados vacios explicitos."""
import io
import json
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
          "sinco_fe_erratas", "sinco_fuente", "onet_ocupaciones", "tareas_onet_en", "crosswalk", "sinco_probabilidad_fo"]
CAL = ["acuerdo_modelos.json", "sensibilidad_preambulo.json", "b1_ordinal_eloundou_class_modelo_anotadores.parquet",
       "b1_ordinal_eloundou_class_modelo_diagnosticos.parquet", "b1_ordinal_eloundou_class_modelo_meta.json",
       "b1_ordinal_exposure_class_modelo_anotadores.parquet", "b1_ordinal_exposure_class_modelo_diagnosticos.parquet",
       "b1_ordinal_exposure_class_modelo_meta.json"]
pytestmark = pytest.mark.skipif(not (PROC / "main_sinco_comp_table.parquet").exists(), reason="tabla MAIN no generada (python -m src.main_sinco_comp_table)")


def _cliente(tmp_path, con_main=True):
    for n in TABLAS:
        shutil.copy(PROC / f"{n}.parquet", tmp_path / f"{n}.parquet")
    (tmp_path / "calibracion").mkdir()
    if con_main:
        for n in ("main_sinco_comp_table.parquet", "main_sinco_comp_table_meta.json"):
            shutil.copy(PROC / n, tmp_path / n)
        for n in CAL:
            if (PROC / "calibracion" / n).exists():
                shutil.copy(PROC / "calibracion" / n, tmp_path / "calibracion" / n)
    mp = pytest.MonkeyPatch(); mp.setattr(S, "PROC", tmp_path); mp.setattr(S, "CAL", tmp_path / "calibracion"); S.limpiar_cache()
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


def test_detalle_rotulado_con_tres_modelos_y_sin_eg(api):
    d = api.get("/api/exposicion/4213").json()
    assert d["estado"] == "disponible" and d["estado_validacion"] == "sin_validar" and "sin validar" in d["etiqueta"]
    assert "consistencia entre modelos, no exactitud" in d["aviso"] and d["decision"] == "019"
    v = d["valores"]
    assert set(v["modelos"]) == {"haiku", "sonnet", "opus"} and v["n_funciones"] > 0
    for m in v["modelos"].values():
        assert 0 <= m["exposure_idx"] <= 1 and 0 <= m["eloundou_idx"] <= 1
        assert abs(sum(m["exposure_clases"].values()) - 1) < 1e-9
    e = v["entre_modelos"]
    assert e["exposure_idx_min"] <= e["exposure_idx_media"] <= e["exposure_idx_max"] and e["exposure_idx_rango"] >= 0
    assert 0 <= v["b1"]["exposure"]["lo"] <= v["b1"]["exposure"]["idx"] <= v["b1"]["exposure"]["hi"] <= 1
    c = v["emparejamiento"]["candidatos"]
    assert [x["rango"] for x in c] == [1, 2] and abs(sum(x["peso_softmax"] for x in c) - 1) < 1e-9
    assert "NO es una probabilidad calibrada" in v["emparejamiento"]["aviso_peso"]
    assert v["probabilidad_fo"]["estado_validacion"] == "sin_validar"
    malas = [k for k in _llaves(d) if str(k).lower() in ("e_g", "score", "scores", "alfa_s", "beta_s", "cota_sup_s")]
    assert not malas


def test_sin_fila_y_sin_anotacion(api):
    assert api.get("/api/exposicion/42").json()["estado"] == "sin_fila"
    assert api.get("/api/exposicion/99999").status_code == 404 or api.get("/api/exposicion/99999").json().get("estado") == "sin_fila"
    m = pd.read_parquet(PROC / "main_sinco_comp_table.parquet")
    sin = m.loc[~m["tiene_anotacion"], "sinco_code"].iloc[0]
    d = api.get(f"/api/exposicion/{sin}").json()
    assert d["estado"] == "sin_anotacion" and "sin imputar" in d["mensaje"]
    assert all(x["exposure_idx"] is None for x in d["valores"]["modelos"].values())


def test_detalle_sinco_y_conexion_incluyen_la_llave(api):
    assert api.get("/api/sinco/4213").json()["exposicion_agentes"]["estado"] == "disponible"
    assert api.get("/api/conexiones/4213").json()["exposicion_agentes"]["estado"] == "disponible"
    assert api.get("/api/meta").json()["exposicion_agentes"]["n_con_anotacion"] > 0
    f = api.get("/api/onet/occupations/41-9091.00/sinco").json()["filas"]
    assert f and all("exposicion_media_modelos" in x for x in f)


def test_lista_paginada_orden_y_filtros(api):
    d = api.get("/api/exposicion?limit=500&orden=exposicion_desc&solo_con_anotacion=true").json()
    assert d["limit"] == 200 and d["total"] > 0 and len(d["resultados"]) == 200
    v = [r["exposure_idx_media_modelos"] for r in d["resultados"]]
    assert v == sorted(v, reverse=True)
    r = api.get("/api/exposicion?division=4&limit=5").json()
    assert r["total"] > 0 and all(x["division"] == "4" for x in r["resultados"])
    assert api.get("/api/exposicion?q=cocinero").json()["total"] > 0
    assert api.get("/api/exposicion?orden=xx").status_code == 422
    assert api.get("/api/exposicion?sinco_prefix=0").status_code == 422
    assert api.get("/api/exposicion?offset=-1").status_code == 422


def test_comparacion_no_expone_kappa_sobre_moda(api):
    d = api.get("/api/modelos/comparacion").json()
    assert d["estado"] == "disponible" and "sin validar" in d["etiqueta"]
    assert set(d["campos"]) == {"exposure_class", "eloundou_fundida", "eloundou_cruda"}
    for c in d["campos"].values():
        assert set(c["kappa_entre_modelos"]) == {"haiku|opus", "haiku|sonnet", "opus|sonnet"}
    assert "kappa_sobre_moda" not in json.dumps(d)
    b = d["b1_ordinal_por_modelo"]["eloundou_class"]
    assert b["convergio"] and b["max_rhat"] <= 1.05 and b["min_ess"] >= 100 and len(b["anotadores"]) == 3
    assert d["limites"] and d["umbrales_provisionales"] == {"uso_principal": 0.60, "exclusion": 0.40}


def test_descarga_main_formatos_y_filtros(api):
    r = api.get("/api/download/main?formato=csv&division=4")
    assert r.status_code == 200 and "attachment" in r.headers["Content-Disposition"] and r.headers["X-Estado-Validacion"] == "sin_validar"
    t = pd.read_csv(io.BytesIO(r.content), dtype={"sinco_code": str})
    assert len(t) == int(r.headers["X-Filas"]) and t["sinco_code"].str[0].eq("4").all() and "rotulo" in t.columns
    full = api.get("/api/download/main?formato=json").json()
    assert full["meta"]["completo"] and full["meta"]["n_filas"] == 490 == len(full["filas"])
    p = api.get("/api/download/main?formato=parquet")
    assert len(pd.read_parquet(io.BytesIO(p.content))) == 490
    assert api.get("/api/download/main?formato=xlsx").status_code == 422


def test_solo_lectura(api):
    for ruta in ("/api/exposicion", "/api/exposicion/4213", "/api/modelos/comparacion", "/api/download/main"):
        assert api.post(ruta).status_code == 405


def test_estado_vacio_sin_tabla_main(tmp_path):
    mp, c = _cliente(tmp_path, con_main=False)
    try:
        assert c.get("/api/exposicion/4213").json()["estado"] == "no_disponible"
        assert c.get("/api/exposicion").json()["estado"] == "no_disponible" and c.get("/api/exposicion").json()["resultados"] == []
        assert c.get("/api/modelos/comparacion").json()["estado"] == "no_disponible"
        assert c.get("/api/download/main").status_code == 409
        assert c.get("/api/meta").json()["exposicion_agentes"]["estado"] == "no_disponible"
        assert c.get("/api/sinco/4213").status_code == 200
    finally:
        mp.undo(); S.limpiar_cache()
