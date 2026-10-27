"""B1 ordinal (decision 017): recupera el orden de sesgos de anotador y de grupos en datos sinteticos."""
import numpy as np
import pandas as pd
import pytest

pytest.importorskip("numpyro")
from src.calibrate import b1_dawid_skene as b1
from src.calibrate import b1_ordinal as bo


def _sintetico(seed=5, G=12, F=25, K=3, sesgos=(-0.6, 0.0, 0.6)):
    rng = np.random.default_rng(seed)
    mu = np.linspace(-1.5, 1.5, G)
    filas = []
    for g in range(G):
        for f in range(F):
            u = mu[g] + rng.normal()
            for k in range(K):
                eta = u + sesgos[k]
                p0 = 1 / (1 + np.exp(-(-0.8 - eta)))
                p01 = 1 / (1 + np.exp(-(0.8 - eta)))
                y = rng.choice(3, p=[p0, p01 - p0, 1 - p01])
                filas.append({"item": f"{1000 + g}|{f}", "anotador": f"r{k}", "clase": ["EL0", "EL1", "EL2"][y],
                              "es_referencia": False})
    return pd.DataFrame(filas)


def test_ordinal_recupera_sesgo_y_orden_de_grupos():
    cfg = b1.cargar_config()
    res = bo.ajustar_ordinal(_sintetico(), ["EL0", "EL1", "EL2"], cfg, n_cadenas=2, n_warmup=300, n_muestras=300)
    assert res["convergio"], res["diagnosticos"]
    dk = res["d_k"].mean(0)
    assert dk[0] < dk[1] < dk[2] and abs(dk.sum()) < 1e-6
    g = bo.resumir_grupos(res, 0.9)
    assert np.corrcoef(np.arange(len(g)), g["indice_medio"])[0, 1] > 0.9


def test_unidad_modelo_usa_moda_y_deja_ausente_sin_moda(tmp_path):
    cfg = b1.cargar_config()
    filas = []
    # item 1: haiku coincide (EL0, EL0); item 2: haiku discrepa (EL0, EL2) -> sin moda; sonnet siempre EL1
    for it, h in ((1, ("EL0", "EL0")), (2, ("EL0", "EL2"))):
        for k, (run, mod, cl) in enumerate([("h1", "haiku", h[0]), ("h2", "haiku", h[1]), ("s1", "sonnet", "EL1"), ("s2", "sonnet", "EL1")]):
            filas.append({"run_id": run, "sinco_code": "1111", "orden": it, "model": f"{mod} (x)", "eloundou_class": cl})
    p = tmp_path / "a.parquet"
    pd.DataFrame(filas).to_parquet(p)
    largo, info = bo.cargar_ruta_s([p], "eloundou_class", cfg, unidad="modelo")
    assert set(largo["anotador"]) == {"haiku", "sonnet"}
    assert info["items_anotador_sin_moda"] == 1
    assert len(largo[largo["anotador"] == "haiku"]) == 1 and len(largo[largo["anotador"] == "sonnet"]) == 2
