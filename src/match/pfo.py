"""Enlace de probabilidades de Frey-Osborne y agregacion a SINCO (005 5.6, 5.7).

O*NET-SOC 2019 -> (puente) -> SOC 2010 (6 digitos) -> probabilidad de automatizacion (Frey-Osborne).
Reglas provisionales (ver issues en docs/issues/): el conjunto S de candidatos pesa por softmax(sim/tau)
(principal) o uniforme; un O*NET con varios SOC 2010 reparte su peso por igual entre ellos; el mismo SOC alcanzado
por varios O*NET se colapsa sumando pesos; los SOC sin probabilidad F-O (o sin puente) se omiten y se reporta la
fraccion de peso cubierta. Nada se imputa.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

ETIQUETA = "probabilidad de automatizacion (Frey-Osborne)"


def softmax(sims, tau: float) -> np.ndarray:
    z = np.asarray(sims, dtype=np.float64) / tau
    z = z - z.max()
    e = np.exp(z)
    return e / e.sum()


def mapa_puente(puente: pd.DataFrame) -> dict[str, list[str]]:
    """onet_soc_2019_code -> lista ordenada de SOC 2010 distintos."""
    g = puente.dropna(subset=["onet_soc_2019_code", "soc_2010"]).groupby("onet_soc_2019_code")["soc_2010"]
    return {k: sorted(set(v)) for k, v in g}


def _combinar(pesos_j: np.ndarray, socs_j: list[list[str]], fo: dict[str, float]) -> dict:
    """Pesos por SOC (colapsado) y media con renormalizacion sobre los SOC que tienen probabilidad."""
    peso_soc: dict[str, float] = {}
    for w, socs in zip(pesos_j, socs_j):
        for s in socs:
            peso_soc[s] = peso_soc.get(s, 0.0) + w / len(socs)
    con = {s: w for s, w in peso_soc.items() if s in fo}
    tot_con = sum(con.values())
    media = sum(w * fo[s] for s, w in con.items()) / tot_con if tot_con > 0 else np.nan
    total = float(np.sum(pesos_j))
    return {"media": media, "cobertura_peso": tot_con / total if total > 0 else 0.0,
            "socs": sorted(peso_soc), "socs_con_fo": sorted(con)}


def agregar_sinco(sims, onet_codes: list[str], tau: float, puente: dict[str, list[str]],
                  fo: dict[str, float], pesos=None) -> dict:
    """sims/onet_codes: conjunto S ordenado por rango (el primero es top-1). Agregaciones de 005 5.7.

    pesos (opcional): pesos explicitos por candidato (revision manual); se normalizan a suma 1 y reemplazan al softmax
    de la agregacion principal (p_ponderada). Sin pesos el comportamiento es el de siempre.
    """
    sims = np.asarray(sims, dtype=np.float64)
    socs_j = [puente.get(c, []) for c in onet_codes]
    sin_puente = [c for c, s in zip(onet_codes, socs_j) if not s]
    if pesos is None:
        w_princ = softmax(sims, tau)
    else:
        w_princ = np.asarray(pesos, dtype=np.float64)
        w_princ = w_princ / w_princ.sum()
    w_soft = _combinar(w_princ, socs_j, fo)
    w_uni = _combinar(np.full(len(sims), 1.0 / len(sims)), socs_j, fo)
    top1_socs = [s for s in socs_j[0] if s in fo]
    p_vals = [fo[s] for s in w_uni["socs_con_fo"]]
    return {
        "p_ponderada": w_soft["media"], "p_media": w_uni["media"],
        "p_min": min(p_vals) if p_vals else np.nan, "p_max": max(p_vals) if p_vals else np.nan,
        "p_top1": float(np.mean([fo[s] for s in top1_socs])) if top1_socs else np.nan,
        "n_candidatos": len(sims), "n_soc2010": len(w_uni["socs"]), "n_soc2010_con_fo": len(w_uni["socs_con_fo"]),
        "cobertura_peso_fo": w_soft["cobertura_peso"],
        "bandera_multi_soc2010": any(len(s) > 1 for s in socs_j),
        "bandera_sin_puente": bool(sin_puente), "onet_sin_puente": ",".join(sin_puente),
        "bandera_soc_sin_fo": len(w_uni["socs"]) > len(w_uni["socs_con_fo"]),
        "cobertura_fo": ("ninguna" if not w_uni["socs_con_fo"] else
                         "completa" if (w_soft["cobertura_peso"] > 1 - 1e-9) else "parcial"),
        "top1_socs": ",".join(socs_j[0]),
    }
