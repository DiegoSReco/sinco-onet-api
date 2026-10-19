"""Pruebas sobre las salidas reales en data/processed/ (se omiten si aun no existen)."""
import json
import re
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
import pytest

from src.match import schemas

PROC = Path(__file__).resolve().parents[2] / "data" / "processed"
CW, PF, CO, CAND = (PROC / n for n in ("crosswalk.parquet", "sinco_probabilidad_fo.parquet", "match_corridas.parquet",
                                       "match_candidatos.parquet"))
pytestmark = pytest.mark.skipif(not (CW.exists() and PF.exists() and CO.exists()), reason="salidas aun no generadas")


@pytest.fixture(scope="module")
def sinco():
    return pd.read_parquet(PROC / "sinco.parquet")


def test_esquema_pyarrow_crosswalk():
    assert pq.read_table(CW).schema.equals(schemas.CROSSWALK_ARROW)


def test_crosswalk_integridad_y_sin_scores(sinco):
    df = pd.read_parquet(CW)
    onet = pd.read_parquet(PROC / "onet_ocupaciones.parquet")
    schemas.validar_crosswalk(df, set(sinco["sinco_code"]), set(onet["onet_soc_code"]))
    assert not [c for c in df.columns if schemas.PROHIBIDAS_CROSSWALK.search(c)]
    assert (df["estado_validacion"] == "sin_validar").all()
    gu = set(sinco[sinco.nivel == "grupo_unitario"]["sinco_code"])
    assert set(df["sinco_code"]) == gu
    assert (df.groupby("sinco_code")["rango"].min() == 1).all()


def test_api_acepta_el_crosswalk():
    from src.api import service as S
    S.limpiar_cache()
    e = S.crosswalk_estado()
    assert e["estado"] == "disponible", e["mensaje"]
    assert e["n_filas"] == len(pd.read_parquet(CW))
    assert "columnas_ignoradas" not in e


def test_tabla_pfo_esquema_e_integridad(sinco):
    df = pd.read_parquet(PF)
    schemas.validar_pfo(df, set(sinco["sinco_code"]))
    assert "probabilidad_automatizacion_fo" in df.columns
    assert not [c for c in df.columns if re.search(r"expos|riesgo", c, re.I)]
    assert (df["estado_validacion"] == "sin_validar").all()
    assert (df["etiqueta"] == "probabilidad de automatizacion (Frey-Osborne)").all()
    d = df.dropna(subset=["probabilidad_automatizacion_fo"])
    assert d["probabilidad_automatizacion_fo"].between(0, 1).all()
    assert df.loc[df["probabilidad_automatizacion_fo"].isna(), "motivo_na"].notna().all()
    assert (d["probabilidad_automatizacion_fo_min"] <= d["probabilidad_automatizacion_fo"] + 1e-9).all()
    assert (d["probabilidad_automatizacion_fo"] <= d["probabilidad_automatizacion_fo_max"] + 1e-9).all()
    fo = pd.read_parquet(PROC / "frey_osborne_probabilidades.parquet")["probabilidad_automatizacion_fo"]
    assert d["probabilidad_automatizacion_fo_min"].isin(set(fo)).all()


def test_corridas_registro_completo():
    df = pd.read_parquet(CO)
    schemas.validar_corridas(df)
    assert (df["fecha"].str.len() > 0).all() and (df["revision_modelo"].str.len() == 40).all()
    json.loads(df["hashes_insumos"].iloc[0])


def test_candidatos_conservan_top_k():
    c = pd.read_parquet(CAND)
    assert c.groupby(["modelo", "sinco_code"]).size().eq(10).all()
    assert c["similitud"].between(-1.0001, 1.0001).all()
