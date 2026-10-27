"""Acuerdo entre modelos en la ruta S (decision 018 sec. 4 y R1.3). Rotulo: CONSISTENCIA ENTRE MODELOS, NO EXACTITUD.

Calcula S1 (kappa ponderado cuadratico por par), S2 (alfa de Krippendorff ordinal), S4 (correlacion por grupo del indice
ordinal medio), S5 (tabla cruzada de rubricas por modelo), S6 (rango entre modelos) y S8 (control negativo physical_bottleneck),
y evalua la regla de exclusion preespecificada de 018 R1.3 (kappa medio < 0.40 frente a AMBOS modelos restantes).
NO calcula E_g de 001 ni alfa_S/beta_S/cota_sup_S (eso es de src/score); el "indice ordinal medio" es clase/(C-1) promediada,
solo para comparar. No cita cifras en el articulo (regla 6). Umbrales 0.60 y 0.40 PROVISIONALES (018).

  python -m src.calibrate.acuerdo_modelos --run-ids R1 R2 ... [--salida-dir DIR]
"""
from __future__ import annotations

import argparse
import datetime as dt
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.annotate import ruta_s as R
from src.annotate.ruta_s_validacion import ORD, alfa_krippendorff_ordinal, kappa_cuadratico, _campo

ROOT = Path(__file__).resolve().parents[2]
CAMPOS = ("exposure_class", "eloundou_fundida", "eloundou_cruda")
UMBRAL_USO, UMBRAL_EXCLUSION = 0.60, 0.40


def modelo_corto(s: str) -> str:
    s = s.lower()
    for m in ("haiku", "sonnet", "opus"):
        if m in s:
            return m
    raise ValueError(f"modelo no reconocido: {s}")


def cargar(run_ids: list[str]) -> pd.DataFrame:
    dfs = []
    for r in run_ids:
        t = pd.read_parquet(R.BASE / "parquet" / f"run_{r}.parquet")
        t["modelo"] = modelo_corto(str(t["model"].iloc[0]))
        t["item"] = t["sinco_code"].astype(str) + "|" + t["orden"].astype(str)
        dfs.append(t)
    return pd.concat(dfs, ignore_index=True)


def _matriz(t: pd.DataFrame, campo: str, por: str) -> pd.DataFrame:
    """items x (corridas | modelos con moda). Moda por modelo: NaN si las corridas discrepan (empate con 2 corridas)."""
    t = t.assign(v=_campo(t, campo))
    ancho = t.pivot(index="item", columns="run_id", values="v")
    if por == "corrida":
        return ancho
    cols = {}
    for m in sorted(t["modelo"].unique()):
        rs = sorted(t.loc[t["modelo"] == m, "run_id"].unique())
        sub = ancho[rs]
        cols[m] = sub.iloc[:, 0].where(sub.nunique(axis=1) == 1)
    return pd.DataFrame(cols)


def _kappa_par(a: pd.Series, b: pd.Series, clases: list) -> float | None:
    ok = a.notna() & b.notna()
    return kappa_cuadratico(list(a[ok]), list(b[ok]), clases) if ok.any() else None


def _alfa(mat: pd.DataFrame, clases: list) -> tuple[float | None, int]:
    m = mat.dropna()
    idx = {c: i for i, c in enumerate(clases)}
    if m.empty:
        return None, 0
    return alfa_krippendorff_ordinal(np.array([[idx[v] for v in fila] for fila in m.values]), clases), len(m)


def acuerdo_campo(t: pd.DataFrame, campo: str) -> dict:
    clases = ORD[campo]
    corr = _matriz(t, campo, "corrida")
    moda = _matriz(t, campo, "modelo")
    modelos = sorted(t["modelo"].unique())
    runs = {m: sorted(t.loc[t["modelo"] == m, "run_id"].unique()) for m in modelos}
    intra = {m: _kappa_par(corr[runs[m][0]], corr[runs[m][1]], clases) for m in modelos if len(runs[m]) >= 2}
    entre = {}
    for a, b in itertools.combinations(modelos, 2):
        ks = [_kappa_par(corr[x], corr[y], clases) for x in runs[a] for y in runs[b]]
        entre[f"{a}|{b}"] = {"kappa_medio_pares_de_corridas": (float(np.mean(ks)) if None not in ks else None),
                              "kappa_sobre_moda": _kappa_par(moda[a], moda[b], clases),
                              "n_items_moda_comun": int((moda[a].notna() & moda[b].notna()).sum())}
    # Regla de exclusion (018 R1.3): modelo excluido si su kappa medio es < 0.40 frente a AMBOS restantes.
    excluidos, marcados = [], []
    for m in modelos:
        k = [entre[f"{min(m, o)}|{max(m, o)}"]["kappa_medio_pares_de_corridas"] for o in modelos if o != m]
        bajos = [x is not None and x < UMBRAL_EXCLUSION for x in k]
        if all(bajos) and len(k) == 2:
            excluidos.append(m)
        elif any(bajos):
            marcados.append(m)
    a_corr, n_c = _alfa(corr, clases)
    a_mod, n_m = _alfa(moda, clases)
    return {"intra_modelo_kappa": intra, "entre_modelos": entre,
            "alfa_krippendorff_ordinal": {"corridas": a_corr, "n_items_corridas": n_c, "modas_por_modelo": a_mod, "n_items_modas": n_m},
            "acuerdo_exacto_corridas": {m: float((corr[runs[m][0]] == corr[runs[m][1]]).mean()) for m in modelos if len(runs[m]) >= 2},
            "items_con_moda_por_modelo": {m: float(moda[m].notna().mean()) for m in modelos},
            "regla_exclusion": {"excluidos": excluidos, "marcados_bajo_frente_a_uno": marcados, "umbral": UMBRAL_EXCLUSION},
            "estado_uso_principal": {"umbral_kappa_min": UMBRAL_USO,
                                     "suficiente": all(v["kappa_medio_pares_de_corridas"] is not None and v["kappa_medio_pares_de_corridas"] >= UMBRAL_USO
                                                       for v in entre.values())}}


def indice_por_grupo(t: pd.DataFrame, campo: str) -> pd.DataFrame:
    """Indice ordinal medio (clase/(C-1)) por grupo y modelo: media sobre funciones y corridas del modelo. NO es E_g."""
    clases = ORD[campo]
    v = _campo(t, campo).map({c: i for i, c in enumerate(clases)}) / (len(clases) - 1)
    return t.assign(idx=v).groupby(["sinco_code", "modelo"])["idx"].mean().unstack("modelo")


def correlaciones(g: pd.DataFrame) -> dict:
    out = {}
    for a, b in itertools.combinations(g.columns, 2):
        out[f"{a}|{b}"] = {"pearson": float(g[a].corr(g[b])), "spearman": float(g[a].corr(g[b], method="spearman"))}
    return out


def control_negativo(t: pd.DataFrame) -> dict:
    """S8: indice ordinal medio de exposure_class con y sin physical_bottleneck, por modelo."""
    v = t["exposure_class"].map({"E0": 0, "E1": 0.5, "E2": 1.0})
    d = t.assign(idx=v, pb=t["physical_bottleneck"].astype(bool)).groupby(["modelo", "pb"])["idx"].agg(["mean", "size"])
    return {m: {("con_cuello_fisico" if pb else "sin_cuello_fisico"): {"indice_medio": float(r["mean"]), "n": int(r["size"])}
                for (mm, pb), r in d.iterrows() if mm == m} for m in sorted(t["modelo"].unique())}


def cruzada(t: pd.DataFrame) -> dict:
    return {m: pd.crosstab(s["exposure_class"], s["eloundou_class"]).to_dict() for m, s in t.groupby("modelo")}


def ejecutar(run_ids: list[str], salida_dir: Path) -> dict:
    t = cargar(run_ids)
    res = {"rotulo": "consistencia entre modelos, no exactitud", "version": "acuerdo-modelos-0.1",
           "fecha": dt.datetime.now().isoformat(timespec="seconds"), "run_ids": run_ids,
           "prompt_versions": sorted(t["prompt_version"].unique().tolist()),
           "campos": {c: acuerdo_campo(t, c) for c in CAMPOS}, "grupos": {}}
    salida_dir.mkdir(parents=True, exist_ok=True)
    for campo in ("exposure_class", "eloundou_fundida"):
        g = indice_por_grupo(t, campo)
        g["min_modelos"], g["max_modelos"] = g.min(axis=1), g.max(axis=1)
        g["rango"] = g["max_modelos"] - g["min_modelos"]
        g.to_csv(salida_dir / f"indice_por_grupo_{campo}.csv", encoding="utf-8")
        modelos = [c for c in g.columns if c in ("haiku", "sonnet", "opus")]
        res["grupos"][campo] = {"n_grupos": int(len(g)), "correlaciones": correlaciones(g[modelos]),
                                "rango_medio_entre_modelos": float(g["rango"].mean()), "rango_max": float(g["rango"].max())}
    res["control_negativo_S8"] = control_negativo(t)
    res["tabla_cruzada_S5"] = {m: {str(k): v for k, v in d.items()} for m, d in cruzada(t).items()}
    (salida_dir / "acuerdo_modelos.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m src.calibrate.acuerdo_modelos")
    ap.add_argument("--run-ids", nargs="+", required=True)
    ap.add_argument("--salida-dir", default=str(ROOT / "data" / "processed" / "calibracion"))
    a = ap.parse_args(argv)
    r = ejecutar(a.run_ids, Path(a.salida_dir))
    for c, v in r["campos"].items():
        print(c, "| excluidos:", v["regla_exclusion"]["excluidos"], "| marcados:", v["regla_exclusion"]["marcados_bajo_frente_a_uno"],
              "| uso principal:", v["estado_uso_principal"]["suficiente"])
    print("->", Path(a.salida_dir) / "acuerdo_modelos.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
