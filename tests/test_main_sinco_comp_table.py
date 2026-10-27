"""Tabla MAIN (decision 019): una fila por grupo unitario, rangos validos, pesos que suman 1 y coherencia con el script de acuerdo."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src import main_sinco_comp_table as M

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(not (M.R.BASE / "parquet" / f"run_{M.CORRIDAS['opus'][1]}.parquet").exists() or not (M.CAL / "acuerdo_modelos.json").exists(),
                                reason="faltan las corridas de la ruta S o los resultados de calibracion")


@pytest.fixture(scope="module")
def construido():
    return M.construir()


def test_una_fila_por_grupo_unitario_y_columnas_clave(construido):
    t, meta = construido
    s = pd.read_parquet(M.PROC / "sinco.parquet")
    assert t["sinco_code"].is_unique and set(t["sinco_code"]) == set(s.loc[s["nivel"] == "grupo_unitario", "sinco_code"].astype(str))
    for c in ("onet1_soc", "onet1_similitud", "onet1_peso_softmax", "onet2_soc", "exp_idx_haiku", "exp_idx_sonnet", "exp_idx_opus", "el_idx_media_modelos",
              "b1_exp_idx", "prob_automatizacion_fo", "estado_validacion", "rotulo"):
        assert c in t.columns
    assert (t["estado_validacion"] == "sin_validar").all() and meta["n_filas"] == len(t) == meta["n_con_anotacion"] + int((~t["tiene_anotacion"]).sum())


def test_rangos_pesos_y_sin_imputar(construido):
    t, _ = construido
    idx = [c for c in t.columns if "_idx_" in c and not c.endswith("sin_pooling") or c.endswith("sin_pooling")]
    for c in idx:
        v = t[c].dropna()
        assert ((v >= -1e-9) & (v <= 1 + 1e-9)).all(), c
    ok = t["onet1_peso_softmax"].notna()
    assert np.allclose((t.loc[ok, "onet1_peso_softmax"] + t.loc[ok, "onet2_peso_softmax"]).to_numpy(), 1.0)
    assert (t["onet1_similitud"] >= t["onet2_similitud"]).all()
    sin = t[~t["tiene_anotacion"]]
    assert len(sin) > 0 and sin[[c for c in t.columns if c.startswith(("exp_idx_haiku", "el_idx_opus", "b1_exp_idx"))]].isna().all().all()
    for p in ("exp", "el"):
        con = t[t["tiene_anotacion"]]
        assert (con[f"{p}_idx_min_modelos"] <= con[f"{p}_idx_media_modelos"] + 1e-9).all() and (con[f"{p}_idx_media_modelos"] <= con[f"{p}_idx_max_modelos"] + 1e-9).all()
        for m in M.MODELOS:
            cols = [f"{p}_{c}_{m}" for c in (("E0", "E1", "E2") if p == "exp" else ("EL0", "EL1", "EL2"))]
            assert np.allclose(con[cols].sum(axis=1).to_numpy(), 1.0)


def test_coincide_con_el_indice_de_acuerdo_modelos(construido):
    t, _ = construido
    csv = M.CAL / "indice_por_grupo_exposure_class.csv"
    if not csv.exists():
        pytest.skip("falta indice_por_grupo_exposure_class.csv")
    c = pd.read_csv(csv, dtype={"sinco_code": str}).set_index("sinco_code")
    x = t.set_index("sinco_code")
    for m in M.MODELOS:
        assert np.allclose(x.loc[c.index, f"exp_idx_{m}"].to_numpy(), c[m].to_numpy(), atol=1e-9)


def test_excluye_la_variante_v2(construido):
    t, meta = construido
    assert "ann-s-v2" not in t["corridas_base"].iloc[0] and t["prompt_version"].iloc[0] == "ann-s-v1"
    assert sum(len(v) for v in meta["corridas"].values()) == 6
