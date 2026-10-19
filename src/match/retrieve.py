"""Recuperacion SINCO -> O*NET-SOC: coseno, top-k, conjunto S, margen y banderas (005 5.4).

Todo numpy, sin indices vectoriales (fuerza bruta 490 x 1016).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def similitud(q: np.ndarray, d: np.ndarray) -> np.ndarray:
    """Coseno (vectores ya L2-normalizados). Matriz n_sinco x n_onet, float32."""
    return q.astype(np.float32) @ d.astype(np.float32).T


def topk(sim: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
    """Indices y similitudes del top-k por fila. Empates: orden estable por indice (codigos ordenados)."""
    orden = np.argsort(-sim, axis=1, kind="stable")[:, :k]
    return orden, np.take_along_axis(sim, orden, axis=1)


def umbrales(sim_top1: np.ndarray, margen: np.ndarray, q_baja: float, q_margen: float, q_sin: float) -> dict:
    """Umbrales relativos a la distribucion propia del modelo (provisional, sin calibrar)."""
    return {"sim_top1_baja": float(np.quantile(sim_top1, q_baja)),
            "margen_bajo": float(np.quantile(margen, q_margen)),
            "sim_top1_sin_coincidencia": float(np.quantile(sim_top1, q_sin))}


def candidatos(sim: np.ndarray, sinco_codes: list[str], onet_codes: list[str], k: int, delta: float,
               rango_max: int, q_baja: float, q_margen: float, q_sin: float):
    """Devuelve (top-k largo, resumen por SINCO, umbrales)."""
    idx, s = topk(sim, k)
    margen = s[:, 0] - s[:, 1]
    umb = umbrales(s[:, 0], margen, q_baja, q_margen, q_sin)
    filas = []
    for i, code in enumerate(sinco_codes):
        for r in range(idx.shape[1]):
            filas.append((code, onet_codes[idx[i, r]], r + 1, float(s[i, r]), float(s[i, 0] - s[i, r]),
                          bool(r + 1 <= rango_max and s[i, r] >= s[i, 0] - delta)))
    top = pd.DataFrame(filas, columns=["sinco_code", "onet_soc_code", "rango", "similitud", "dif_con_top1",
                                       "en_conjunto"])
    top["margen_sinco"] = np.repeat(margen, idx.shape[1])
    res = pd.DataFrame({"sinco_code": sinco_codes, "sim_top1": s[:, 0], "sim_top2": s[:, 1], "margen": margen,
                        "n_conjunto": top.groupby("sinco_code", sort=False)["en_conjunto"].sum().to_numpy()})
    res["bandera_sim_top1_baja"] = res["sim_top1"] < umb["sim_top1_baja"]
    res["bandera_margen_bajo"] = res["margen"] < umb["margen_bajo"]
    res["baja_confianza"] = res["bandera_sim_top1_baja"] | res["bandera_margen_bajo"]
    sin = res["sim_top1"] < umb["sim_top1_sin_coincidencia"]
    res["match_status"] = np.where(sin, "sin_coincidencia", np.where(res["baja_confianza"], "baja_confianza", "ok"))
    return top, res, umb


def tipo_relacion(pares: pd.DataFrame) -> pd.Series:
    """1:1, 1:N, N:1, M:N sobre el grafo de pares (sinco, onet) del conjunto S (003)."""
    n_o = pares.groupby("sinco_code")["onet_soc_code"].transform("nunique")
    n_s = pares.groupby("onet_soc_code")["sinco_code"].transform("nunique")
    return pd.Series(np.select([(n_o == 1) & (n_s == 1), (n_o > 1) & (n_s == 1), (n_o == 1) & (n_s > 1)],
                               ["1:1", "1:N", "N:1"], default="M:N"), index=pares.index)
