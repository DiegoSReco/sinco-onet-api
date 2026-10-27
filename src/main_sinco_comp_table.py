"""Tabla MAIN por grupo unitario SINCO (decision 019): emparejamiento con O*NET, exposicion de los tres modelos, B1 y Frey-Osborne.

Una fila por grupo unitario SINCO (490). Reune, de salidas ya generadas por otros scripts:
  - emparejamiento por embeddings (modelo principal, top-2) con similitud, margen y `peso_softmax` (peso relativo entre los 2
    candidatos, softmax(similitud / tau); NO es una probabilidad calibrada de acierto);
  - exposicion teorica de Haiku, Sonnet y Opus (ruta S, 6 corridas base de `ann-s-v1`): indice ordinal medio y participacion por
    clase de `exposure_class` y `eloundou_class` (EL3 fundida en EL2), cuello de botella fisico, medida entre modelos (018 R1.3)
    y rango entre modelos;
  - B1 ordinal (`unidad = modelo`): indice por grupo con intervalo al 90 %;
  - probabilidad de automatizacion (Frey-Osborne), siempre rotulada y sin validar.
`exp_idx_<modelo>` es la medida principal de 001 (promedio de `exposure_class` con el mapa 0 / 0.5 / 1) aplicada a la ruta S con pesos iguales por
funcion; la regla formal de agregacion de la ruta S (001, E-4) sigue pendiente. `alfa_S`, `beta_S` y `cota_sup_S` son las medidas de comparacion de 001
(EL1; EL1 + 0.5 EL2; EL1 + EL2, con EL3 dentro de EL2). `el_idx_*` es solo un indice auxiliar: asume EL0 < EL1 < EL2 y no es ninguna de las tres.
Rotulo: exposicion teorica sin validar; consistencia entre modelos, no exactitud.
Todas las cifras salen de este script (regla 1).

  python -m src.main_sinco_comp_table [--salida-dir data/processed]
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.annotate import ruta_s as R
from src.annotate.revisar_desacuerdos import CORRIDAS as CORRIDAS_REVISION
from src.match import config as MC
from src.match.pfo import softmax

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
CAL = PROC / "calibracion"
VERSION = "main-0.1"
ROTULO = ("Exposicion teorica por anotacion de modelos (Haiku, Sonnet, Opus), sin validar. Mide consistencia entre modelos, "
          "no exactitud; no es riesgo de perdida de empleo ni una estimacion para Mexico.")
MODELOS = ("haiku", "sonnet", "opus")
CORRIDAS = {  # corridas base de 018 (la variante ann-s-v2 no entra)
    "sonnet": ["ann-s-v1-2026-10-20-01", "ann-s-v1-2026-10-20-02"],
    "haiku": ["ann-s-v1-2026-10-22-haiku-01", "ann-s-v1-2026-10-22-haiku-02"],
    "opus": ["ann-s-v1-2026-10-22-opus-01", "ann-s-v1-2026-10-22-opus-02"],
}
VAL_EXP = {"E0": 0.0, "E1": 0.5, "E2": 1.0}
VAL_EL = {"EL0": 0.0, "EL1": 0.5, "EL2": 1.0}


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def cargar_anotaciones() -> pd.DataFrame:
    """Funciones anotadas de las 6 corridas base, con modelo, corrida, indices por funcion y cuello fisico."""
    dfs = []
    for m, runs in CORRIDAS.items():
        for rid in runs:
            t = pd.read_parquet(R.BASE / "parquet" / f"run_{rid}.parquet",
                                columns=["run_id", "sinco_code", "orden", "exposure_class", "eloundou_class", "physical_bottleneck", "prompt_version"])
            dfs.append(t.assign(modelo=m))
    t = pd.concat(dfs, ignore_index=True)
    t["sinco_code"] = t["sinco_code"].astype(str)
    t["el"] = t["eloundou_class"].replace({"EL3": "EL2"})
    t["exp_v"] = t["exposure_class"].map(VAL_EXP)
    t["el_v"] = t["el"].map(VAL_EL)
    t["pb"] = t["physical_bottleneck"].astype(float)
    if t[["exp_v", "el_v"]].isna().any().any():
        raise ValueError("etiquetas fuera de E0-E2 / EL0-EL3 en las corridas base")
    return t


def exposicion_por_grupo(t: pd.DataFrame) -> pd.DataFrame:
    """Promedio sobre funciones y corridas de cada modelo (media de las medias por corrida)."""
    out = {}
    for m in MODELOS:
        s = t[t["modelo"] == m]
        por_run = s.groupby(["sinco_code", "run_id"])
        med = por_run.agg(exp_idx=("exp_v", "mean"), el_idx=("el_v", "mean"), pb=("pb", "mean")).groupby("sinco_code").mean()
        cols = {f"exp_idx_{m}": med["exp_idx"], f"el_idx_{m}": med["el_idx"], f"pb_{m}": med["pb"]}
        for campo, pref, clases in (("exposure_class", "exp", ("E0", "E1", "E2")), ("el", "el", ("EL0", "EL1", "EL2"))):
            dum = pd.get_dummies(s[campo]).reindex(columns=list(clases), fill_value=0).astype(float)
            dum[["sinco_code", "run_id"]] = s[["sinco_code", "run_id"]].values
            part = dum.groupby(["sinco_code", "run_id"]).mean().groupby("sinco_code").mean()
            for c in clases:
                cols[f"{pref}_{c}_{m}"] = part[c]
            if pref == "el":   # medidas de Eloundou segun 001 (E-3); EL3 ya esta dentro de EL2
                cols[f"alfa_S_{m}"] = part["EL1"]
                cols[f"beta_S_{m}"] = part["EL1"] + 0.5 * part["EL2"]
                cols[f"cota_sup_S_{m}"] = part["EL1"] + part["EL2"]
        out.update(cols)
    return pd.DataFrame(out)


def entre_modelos(g: pd.DataFrame, excluidos: dict[str, list[str]]) -> pd.DataFrame:
    """Media simple con pesos iguales de las medias por modelo no excluidos (018 R1.3) y rango min-max (S6)."""
    r = pd.DataFrame(index=g.index)
    for campo, pref in (("exposure_class", "exp"), ("eloundou_fundida", "el")):
        usados = [m for m in MODELOS if m not in excluidos.get(campo, [])]
        cols = g[[f"{pref}_idx_{m}" for m in usados]]
        r[f"{pref}_idx_media_modelos"] = cols.mean(axis=1) if len(usados) >= 2 else np.nan
        todos = g[[f"{pref}_idx_{m}" for m in MODELOS]]
        r[f"{pref}_idx_min_modelos"] = todos.min(axis=1)
        r[f"{pref}_idx_max_modelos"] = todos.max(axis=1)
        r[f"{pref}_idx_rango_modelos"] = todos.max(axis=1) - todos.min(axis=1)
    usados = [m for m in MODELOS if m not in excluidos.get("eloundou_fundida", [])]
    for med in ("alfa_S", "beta_S", "cota_sup_S"):
        r[f"{med}_media_modelos"] = g[[f"{med}_{m}" for m in usados]].mean(axis=1) if len(usados) >= 2 else np.nan
        todos = g[[f"{med}_{m}" for m in MODELOS]]
        r[f"{med}_rango_modelos"] = todos.max(axis=1) - todos.min(axis=1)
    return r


def acuerdo_funciones(t: pd.DataFrame) -> pd.DataFrame:
    """Por grupo: fraccion de funciones donde los 3 modelos (primera corrida de cada uno) dan la misma clase, y desacuerdo fuerte."""
    primeras = [CORRIDAS_REVISION[m] for m in MODELOS]
    s = t[t["run_id"].isin(primeras)]
    out = {}
    for campo, pref, ext in (("exposure_class", "exp", ("E0", "E2")), ("el", "el", ("EL0", "EL2"))):
        w = s.pivot(index=["sinco_code", "orden"], columns="modelo", values=campo)[list(MODELOS)]
        igual = w.nunique(axis=1) == 1
        fuerte = (w.nunique(axis=1) == 3) | w.apply(lambda f: set(ext) <= set(f), axis=1)
        d = pd.DataFrame({"igual": igual, "fuerte": fuerte}).reset_index().groupby("sinco_code").mean(numeric_only=True)
        out[f"{pref}_frac_coinciden_3_modelos"] = d["igual"]
        out[f"{pref}_frac_desacuerdo_fuerte"] = d["fuerte"]
    return pd.DataFrame(out)


def b1_por_grupo() -> pd.DataFrame:
    out = {}
    for campo, pref in (("exposure_class", "exp"), ("eloundou_class", "el")):
        g = pd.read_parquet(CAL / f"b1_ordinal_{campo}_modelo_grupos.parquet").assign(sinco_code=lambda d: d["grupo"].astype(str)).set_index("sinco_code")
        out[f"b1_{pref}_idx"] = g["indice_medio"]
        out[f"b1_{pref}_idx_lo"] = g["indice_lo"]
        out[f"b1_{pref}_idx_hi"] = g["indice_hi"]
        out[f"b1_{pref}_idx_sin_pooling"] = g["indice_sin_pooling"]
    return pd.DataFrame(out)


def emparejamiento(cfg: dict) -> pd.DataFrame:
    """Top-2 del modelo principal con titulo O*NET, similitud, margen y peso softmax entre los 2 candidatos."""
    principal = cfg["meta"]["modelo_principal"]
    tau = float(cfg["modelos"][principal]["tau"])
    cw = pd.read_parquet(PROC / "crosswalk.parquet")
    cw = cw[cw["modelo"] == principal].copy()
    tit = pd.read_parquet(PROC / "onet_ocupaciones.parquet").set_index("onet_soc_code")["titulo_en"]
    filas = {}
    for code, g in cw.sort_values("rango").groupby("sinco_code"):
        g = g.sort_values("rango")
        sims = g["similitud"].to_numpy(dtype=float)
        w = softmax(sims, tau) if len(sims) >= 2 else np.array([1.0])
        r = {"match_modelo": principal, "match_run_id": g["run_id"].iloc[0], "match_status": g["match_status"].iloc[0],
             "match_baja_confianza": bool(g["baja_confianza"].iloc[0]), "match_margen": float(g["margen"].iloc[0]), "match_tau": tau}
        for i, (_, f) in enumerate(g.head(2).iterrows(), start=1):
            r[f"onet{i}_soc"] = f["onet_soc_code"]
            r[f"onet{i}_titulo"] = tit.get(f["onet_soc_code"])
            r[f"onet{i}_similitud"] = float(f["similitud"])
            r[f"onet{i}_peso_softmax"] = float(w[i - 1])
        filas[code] = r
    em = pd.DataFrame.from_dict(filas, orient="index")
    # concordancia con el otro modelo de embeddings (solo para ver estabilidad del emparejamiento)
    cand = pd.read_parquet(PROC / "match_candidatos.parquet")
    otro = cand[(cand["modelo"] != principal) & (cand["rango"] == 1)].set_index("sinco_code")
    if len(otro):
        em["match_top1_otro_modelo"] = otro["onet_soc_code"].reindex(em.index)
        em["match_top1_coincide_otro_modelo"] = em["match_top1_otro_modelo"] == em["onet1_soc"]
    return em


def frey_osborne(principal: str) -> pd.DataFrame:
    p = pd.read_parquet(PROC / "sinco_probabilidad_fo.parquet")
    p = p[p["modelo"] == principal].set_index("sinco_code")
    return pd.DataFrame({"prob_automatizacion_fo": p["probabilidad_automatizacion_fo"], "prob_fo_cobertura": p["cobertura_fo"],
                         "prob_fo_motivo_na": p["motivo_na"]})


def construir() -> tuple[pd.DataFrame, dict]:
    cfg = MC.cargar()
    s = pd.read_parquet(PROC / "sinco.parquet")
    gu = s[s["nivel"] == "grupo_unitario"].sort_values("orden")
    base = pd.DataFrame({"sinco_code": gu["sinco_code"].astype(str).values, "titulo": gu["titulo"].values,
                         "division": gu["division"].astype(str).values, "subgrupo": gu["sinco_code"].astype(str).str[:3].values}).set_index("sinco_code", drop=False)
    nf = pd.read_parquet(PROC / "sinco_funciones.parquet").assign(sinco_code=lambda d: d["sinco_code"].astype(str)).groupby("sinco_code").size()
    base["n_funciones"] = nf.reindex(base.index).fillna(0).astype(int)

    t = cargar_anotaciones()
    g = exposicion_por_grupo(t)
    acu = json.loads((CAL / "acuerdo_modelos.json").read_text(encoding="utf-8"))
    excl = {c: v["regla_exclusion"]["excluidos"] for c, v in acu["campos"].items()}
    partes = [base, emparejamiento(cfg), frey_osborne(cfg["meta"]["modelo_principal"]), g, entre_modelos(g, excl), acuerdo_funciones(t), b1_por_grupo()]
    main = pd.concat([p.reindex(base.index) if p is not base else p for p in partes], axis=1)
    main["tiene_anotacion"] = main["exp_idx_haiku"].notna()
    main["modelos_excluidos"] = ",".join(sorted({m for v in excl.values() for m in v}))
    main["corridas_base"] = ";".join(r for runs in CORRIDAS.values() for r in runs)
    main["prompt_version"] = ",".join(sorted(t["prompt_version"].unique()))
    main["estado_validacion"] = "sin_validar"
    main["rotulo"] = ROTULO
    main = main.reset_index(drop=True)
    conteos = {rid: {"modelo": m, "exposure_class": g_["exposure_class"].value_counts().to_dict(), "eloundou_class": g_["el"].value_counts().to_dict(), "n": int(len(g_))}
               for (m, rid), g_ in t.groupby(["modelo", "run_id"])}
    ann = main[main["tiene_anotacion"]]
    cols_idx = [f"{p}_idx_{m}" for p in ("exp", "el") for m in MODELOS] + ["exp_idx_media_modelos", "el_idx_media_modelos"]
    por_div = ann.groupby("division")[cols_idx].mean().round(6)
    por_div["n_grupos"] = ann.groupby("division").size()
    meta = {"version": VERSION, "fecha_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "rotulo": ROTULO,
            "conteos_por_corrida": conteos, "medias_por_division": {d: r.dropna().to_dict() for d, r in por_div.iterrows()},
            "n_filas": int(len(main)), "n_con_anotacion": int(main["tiene_anotacion"].sum()), "corridas": CORRIDAS,
            "modelo_embeddings_principal": cfg["meta"]["modelo_principal"], "tau": main["match_tau"].dropna().iloc[0] if main["match_tau"].notna().any() else None,
            "decision": "019", "excluidos_por_regla_R1_3": excl,
            "entradas_sha256": {n: _sha(PROC / n) for n in ("crosswalk.parquet", "match_candidatos.parquet", "sinco.parquet", "sinco_funciones.parquet", "sinco_probabilidad_fo.parquet")}
            | {n: _sha(CAL / n) for n in ("acuerdo_modelos.json", "b1_ordinal_exposure_class_modelo_grupos.parquet", "b1_ordinal_eloundou_class_modelo_grupos.parquet")},
            "columnas": list(main.columns)}
    return main, meta


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m src.main_sinco_comp_table")
    ap.add_argument("--salida-dir", default=str(PROC))
    a = ap.parse_args(argv)
    tabla, meta = construir()
    out = Path(a.salida_dir)
    out.mkdir(parents=True, exist_ok=True)
    tabla.to_parquet(out / "main_sinco_comp_table.parquet", index=False)
    tabla.to_csv(out / "main_sinco_comp_table.csv", index=False, encoding="utf-8-sig")
    (out / "main_sinco_comp_table_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"{meta['n_filas']} grupos unitarios, {meta['n_con_anotacion']} con anotacion, {len(tabla.columns)} columnas -> {out / 'main_sinco_comp_table.parquet'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
