"""B1 NumPyro (decision 016): reproduce el Gibbs en datos sinteticos. Se omite si NumPyro no esta instalado."""
import numpy as np
import pandas as pd
import pytest

pytest.importorskip("numpyro")
from src.calibrate import b1_dawid_skene as b1
from src.calibrate import b1_numpyro as bn


def _largo(seed=3, N=150, K=3):
    rng = np.random.default_rng(seed)
    pi = np.array([.5, .3, .2]); th = np.array([[.8, .15, .05], [.15, .7, .15], [.05, .2, .75]])
    z = rng.choice(3, N, p=pi)
    filas = [{"item": f"t{i}", "anotador": f"r{k}", "clase": ["E0", "E1", "E2"][rng.choice(3, p=th[z[i]])], "es_referencia": False}
             for i in range(N) for k in range(K)]
    return pd.DataFrame(filas), pi


def test_numpyro_converge_y_coincide_con_gibbs():
    cfg = b1.cargar_config(); largo, pi = _largo()
    r = bn.comparar_con_gibbs(largo, ["E0", "E1", "E2"], cfg, n_warmup=300, n_muestras=300, n_cadenas=2)
    assert r["numpyro_convergio"] and r["gibbs_convergio"]
    assert r["dif_max_pi"] < 0.03 and r["dif_max_diag_theta"] < 0.05
    assert r["acuerdo_clase_modal"] > 0.97
