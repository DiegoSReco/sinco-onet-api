"""Validacion de corrida completa, ruta S (decision 015 sec. 3.9). Solo mide completitud y acuerdo entre corridas;
NO calcula exposicion agregada (E_g) ni ningun puntaje (eso es de src/score). Se niega a declarar aceptada una
corrida incompleta.

Acuerdo: kappa de Cohen ponderado cuadratico por pares de corridas (umbral provisional 0.60, 015 M27) para
`exposure_class` y `eloundou_class` (EL3 fundida en EL2 y, aparte, 4 clases crudas); alfa de Krippendorff ordinal
entre las corridas (solo reporte); acuerdo exacto descriptivo. `physical_bottleneck` y `confidence` se reportan sin umbral.
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import config as C
from . import ruta_s as R
from .schemas import read_parquet_s

ORD = {
    "exposure_class": ["E0", "E1", "E2"],
    "eloundou_fundida": ["EL0", "EL1", "EL2"],
    "eloundou_cruda": ["EL0", "EL1", "EL2", "EL3"],
    "confidence": ["baja", "media", "alta"],
    "physical_bottleneck": [False, True],
}
CON_UMBRAL = ("exposure_class", "eloundou_fundida", "eloundou_cruda")


def kappa_cuadratico(a: list, b: list, clases: list) -> float | None:
    """Kappa ponderado cuadratico (implementacion propia: pesos 1 - (i-j)^2/(k-1)^2). None si no esta definido."""
    k = len(clases)
    idx = {c: i for i, c in enumerate(clases)}
    O = np.zeros((k, k))
    for x, y in zip(a, b):
        O[idx[x], idx[y]] += 1
    n = O.sum()
    if n == 0:
        return None
    E = np.outer(O.sum(1), O.sum(0)) / n
    i, j = np.indices((k, k))
    W = (i - j) ** 2 / (max(k - 1, 1)) ** 2
    den = (W * E).sum()
    if den == 0:
        return None
    return float(1 - (W * O).sum() / den)


def alfa_krippendorff_ordinal(matriz: np.ndarray, clases: list) -> float | None:
    """Alfa de Krippendorff, metrica ordinal. matriz: unidades x corridas con indices de clase (sin faltantes)."""
    k = len(clases)
    n_u, m = matriz.shape
    if m < 2 or n_u == 0:
        return None
    o = np.zeros((k, k))
    for fila in matriz:
        for p, q in itertools.permutations(range(m), 2):
            o[fila[p], fila[q]] += 1.0 / (m - 1)
    nc = o.sum(1)
    n = nc.sum()
    d = np.zeros((k, k))
    for c in range(k):
        for g in range(k):
            lo, hi = min(c, g), max(c, g)
            d[c, g] = (nc[lo:hi + 1].sum() - (nc[c] + nc[g]) / 2) ** 2
    do = (o * d).sum()
    de = (np.outer(nc, nc) * d).sum() / (n - 1) if n > 1 else 0
    if de == 0:
        return None
    return float(1 - do / de)


def _campo(df: pd.DataFrame, campo: str) -> pd.Series:
    if campo == "eloundou_fundida":
        return df["eloundou_class"].replace({"EL3": "EL2"})
    if campo == "eloundou_cruda":
        return df["eloundou_class"]
    return df[campo]


def acuerdo(dfs: dict[str, pd.DataFrame], umbral: float) -> dict:
    """dfs: run_id -> DataFrame indexado por (sinco_code, orden) con el mismo indice en todas."""
    rids = list(dfs)
    out = {}
    for campo, clases in ORD.items():
        series = {r: _campo(dfs[r], campo) for r in rids}
        pares = {}
        for a, b in itertools.combinations(rids, 2):
            kap = kappa_cuadratico(list(series[a]), list(series[b]), clases)
            ex = float((series[a].values == series[b].values).mean())
            pares[f"{a}|{b}"] = {"kappa_cuadratico": kap, "acuerdo_exacto": ex}
        idx = {c: i for i, c in enumerate(clases)}
        mat = np.array([[idx[v] for v in vals] for vals in zip(*[series[r] for r in rids])])
        alfa = alfa_krippendorff_ordinal(mat, clases)
        kaps = [p["kappa_cuadratico"] for p in pares.values()]
        entrada = {"pares": pares, "alfa_krippendorff_ordinal": alfa,
                   "kappa_min": (min(kaps) if kaps and None not in kaps else None)}
        if campo in CON_UMBRAL:
            ok = entrada["kappa_min"] is not None and entrada["kappa_min"] >= umbral
            entrada["umbral_provisional"] = umbral
            entrada["estado"] = "suficiente" if ok else "consistencia insuficiente"
        else:
            entrada["estado"] = "solo reporte"
        out[campo] = entrada
    return out


def validar_corrida_completa(run_ids: list[str], *, n_esperado: int = 3, base: Path = R.BASE, universo: dict | None = None,
                             umbral: float | None = None, escribir: bool = True, cfg: dict | None = None) -> dict:
    """Devuelve un dict con `aceptada` (bool) y `motivos_no_aceptada`. Si hay cualquier incompletitud, NO calcula acuerdo
    ni escribe el informe de aceptacion."""
    cfg = cfg or C.cargar()
    s = R.cfg_s(cfg)
    umbral = s["umbral_kappa"] if umbral is None else umbral
    universo = universo or R.cargar_universo()
    esperado = R.claves_universo(universo)
    grupos_esperados = set(universo["grupos"])
    motivos: list[str] = []
    runs = {}
    if len(run_ids) != n_esperado or len(set(run_ids)) != len(run_ids):
        motivos.append(f"se esperaban {n_esperado} corridas distintas y llegaron {len(run_ids)}")
    dfs = {}
    prompts = set()
    cobertura = {}
    for rid in run_ids:
        try:
            est = R.cargar_estado(rid, base)
        except FileNotFoundError as e:
            motivos.append(f"{rid}: {e}")
            continue
        r = R.resumen_estado(est)
        runs[rid] = r
        if r["fallido"] > 0:
            motivos.append(f"{rid}: {r['fallido']} lote(s) fallido(s) definitivo(s)")
        if r["ok"] != r["n_lotes"]:
            motivos.append(f"{rid}: solo {r['ok']} de {r['n_lotes']} lotes ok")
        P = R._paths(rid, base)["parquet"]
        if not P.exists():
            motivos.append(f"{rid}: no existe el Parquet de la corrida")
            continue
        try:
            recs = read_parquet_s(P)
        except Exception as e:  # esquema invalido
            motivos.append(f"{rid}: Parquet fuera de esquema: {str(e)[:200]}")
            continue
        claves = {(x.sinco_code, x.orden) for x in recs}
        faltan, sobran = esperado - claves, claves - esperado
        cobertura[rid] = {"funciones": len(claves), "funciones_esperadas": len(esperado),
                          "grupos": len({c for c, _ in claves}), "grupos_esperados": len(grupos_esperados)}
        if faltan or sobran:
            motivos.append(f"{rid}: cobertura incompleta o con sobrantes (faltan {len(faltan)}, sobran {len(sobran)})")
        prompts.add(recs[0].prompt_sha256 if recs else None)
        dfs[rid] = pd.DataFrame([x.model_dump() for x in recs]).set_index(["sinco_code", "orden"]).sort_index()
    if len(prompts) > 1:
        motivos.append("las corridas usan distinto prompt_sha256")
    informe = {"aceptada": False, "motivos_no_aceptada": motivos, "corridas": runs, "cobertura": cobertura,
               "alertas": [], "grupos_sin_funciones_NA": len(universo.get("sin_funciones", []))}
    for rid, r in runs.items():
        t = r["tasa_rechazo_primer_intento"]
        if t is not None and t > s["umbral_rechazo_primer_intento"]:
            informe["alertas"].append(f"{rid}: rechazos en primer intento {t:.1%} > {s['umbral_rechazo_primer_intento']:.0%} (alerta, no impide aceptar)")
    if motivos or len(dfs) != len(run_ids):
        return informe          # se niega: no hay acuerdo ni informe de aceptacion sobre una corrida incompleta
    informe["acuerdo"] = acuerdo(dfs, umbral)
    informe["aceptada"] = True
    informe["campos_con_consistencia_insuficiente"] = [c for c, v in informe["acuerdo"].items() if v["estado"] == "consistencia insuficiente"]
    informe["nota"] = ("Aceptacion = completitud y consistencia entre corridas; NO prueba validez de la medida (solo la muestra humana es "
                       "independiente del LLM). Rotulo: exposicion teorica SINCO, sin_validar.")
    if escribir:
        out = Path(base) / ("validacion_" + "_".join(r.rsplit("-", 1)[0] for r in run_ids[:1]) + ".json")
        out.write_text(json.dumps(informe, indent=1, ensure_ascii=False), encoding="utf-8")
        informe["archivo"] = str(out)
    return informe
