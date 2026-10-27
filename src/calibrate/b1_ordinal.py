"""B1 ordinal jerarquico con NumPyro (decision 017). PROVISIONAL, SIN VALIDAR.

Modelo ordinal logistico con clase latente continua por item, pooling grupo/division, sesgo por anotador (d_k) y, solo con
referencia humana, efecto de item compartido por las corridas LLM (b_f). Sin humanos mide consistencia entre corridas,
NO exactitud. No calcula la exposicion E_g de 001 (src/score). Cifras: todas salen de este script (regla 1).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from src.calibrate import b1_dawid_skene as b1

VERSION_MODELO = "b1-ordinal-0.1"
ROOT = b1.ROOT


def cargar_ruta_s(rutas, campo: str, cfg: dict, unidad: str = "corrida") -> tuple[pd.DataFrame, dict]:
    """Anotaciones de la ruta S (parquet con sinco_code, orden, run_id, <campo>). item = 'sinco_code|orden'.

    unidad="modelo" (decision 018 sec. 5, nivel A): un anotador por modelo con la moda de sus corridas por item; si las
    corridas discrepan sin moda unica (con 2 corridas, cualquier desacuerdo) el item queda ausente en ese anotador."""
    archivos = []
    for r in rutas:
        p = Path(r)
        archivos += sorted(p.glob("*.parquet")) if p.is_dir() else [p]
    t = pd.concat([pd.read_parquet(p) for p in archivos], ignore_index=True)
    falt = {"run_id", "sinco_code", "orden", campo} - set(t.columns)
    if falt:
        raise b1.EsquemaIncumplido(f"ruta S: faltan columnas {sorted(falt)}")
    t["item"] = t["sinco_code"].astype(str) + "|" + t["orden"].astype(str)
    if t.duplicated(["run_id", "item"]).any():
        raise b1.EsquemaIncumplido("(run_id, item) repetido")
    clase = b1._aplicar_clases(t[campo].astype(str), cfg["campos"][campo], "ruta S")
    largo = pd.DataFrame({"item": t["item"], "anotador": t["run_id"].astype(str), "clase": clase, "es_referencia": False})
    modelos = sorted(t["model"].astype(str).unique()) if "model" in t else []
    info = {"modelos": modelos, "archivos": [str(a) for a in archivos], "unidad": unidad}
    if unidad == "modelo":
        from src.calibrate.acuerdo_modelos import modelo_corto
        largo["anotador"] = t["model"].astype(str).map(modelo_corto).values
        conteo = largo.groupby(["item", "anotador", "clase"]).size().rename("n").reset_index()
        mx = conteo.groupby(["item", "anotador"])["n"].transform("max")
        top = conteo[conteo["n"] == mx]
        unica = top.groupby(["item", "anotador"]).filter(lambda g: len(g) == 1)
        n_antes = len(largo.drop_duplicates(["item", "anotador"]))
        largo = unica[["item", "anotador", "clase"]].assign(es_referencia=False).reset_index(drop=True)
        info["items_anotador_sin_moda"] = int(n_antes - len(largo))
    elif unidad != "corrida":
        raise ValueError("unidad debe ser 'corrida' o 'modelo'")
    return largo, info


def ajustar_ordinal(largo: pd.DataFrame, clases: list[str], cfg: dict, grupo_de=lambda i: i.split("|")[0], div_digitos: int = 1,
                    semilla: Optional[int] = None, n_cadenas: int = 4, n_warmup: int = 1000, n_muestras: int = 1000) -> dict:
    import jax
    import jax.numpy as jnp
    import numpyro
    import numpyro.distributions as dist
    from numpyro.diagnostics import summary
    from numpyro.infer import MCMC, NUTS, init_to_median

    d = b1.Datos(largo, clases)
    C, N, K = d.C, d.n_items, d.n_ann
    if C != 3:
        raise ValueError("el modelo ordinal esta especificado para 3 clases (017)")
    grupos = sorted({grupo_de(i) for i in d.items})
    gix = {g: j for j, g in enumerate(grupos)}
    divs = sorted({g[:div_digitos] for g in grupos})
    dix = {v: j for j, v in enumerate(divs)}
    g_de_item = jnp.asarray([gix[grupo_de(i)] for i in d.items])
    d_de_g = jnp.asarray([dix[g[:div_digitos]] for g in grupos])
    G, D = len(grupos), len(divs)
    item, ann, y = jnp.asarray(d.item), jnp.asarray(d.ann), jnp.asarray(d.y)
    es_ref = jnp.asarray(d.es_ref)
    ref_idx = np.flatnonzero(d.es_ref)
    llm_idx = np.flatnonzero(~d.es_ref)
    con_ref = len(ref_idx) > 0
    if len(llm_idx) < 2 and not con_ref:
        raise ValueError("se necesitan al menos 2 corridas LLM")
    pos_llm = np.full(K, 0)
    pos_llm[llm_idx] = np.arange(len(llm_idx))
    pos_llm = jnp.asarray(pos_llm)
    pos_ref = np.full(K, 0)
    pos_ref[ref_idx] = np.arange(len(ref_idx))
    pos_ref = jnp.asarray(pos_ref)
    nL, nR = len(llm_idx), len(ref_idx)
    n_obs = item.shape[0]

    def logpmf(eta, c_lo, gap):
        """log P(y | eta), ordinal logistico con cortes (c_lo, c_lo + gap); eta, c_lo, gap de forma (n_obs,)."""
        p0 = jax.nn.sigmoid(c_lo - eta)
        p01 = jax.nn.sigmoid(c_lo + gap - eta)
        P = jnp.stack([p0, p01 - p0, 1 - p01], axis=1)
        return jnp.log(jnp.clip(P[jnp.arange(n_obs), y], 1e-12, 1.0))

    def modelo():
        s_d = numpyro.sample("s_d", dist.HalfNormal(1.0))
        s_g = numpyro.sample("s_g", dist.HalfNormal(1.0))
        mu_d = numpyro.sample("mu_d_raw", dist.Normal(0, 1).expand([D])) * s_d
        mu_g = mu_d[d_de_g] + numpyro.sample("mu_g_raw", dist.Normal(0, 1).expand([G])) * s_g
        u = numpyro.deterministic("u", mu_g[g_de_item] + numpyro.sample("e", dist.Normal(0, 1).expand([N])))
        c1 = numpyro.sample("c1", dist.Normal(0, 1.5))
        gap = numpyro.sample("gap", dist.LogNormal(0.5, 0.5))
        raw = numpyro.sample("d_raw", dist.Normal(0, 0.5).expand([nL]))
        dk = raw if con_ref else raw - raw.mean()
        numpyro.deterministic("d_k", dk)
        is_ref = es_ref[ann]
        eta = u[item] + jnp.where(is_ref, 0.0, dk[pos_llm[ann]])
        c_lo = jnp.zeros(n_obs) + c1
        gap_o = jnp.zeros(n_obs) + gap
        if con_ref:
            s_b = numpyro.sample("s_b", dist.HalfNormal(0.5))
            b = numpyro.sample("b_raw", dist.Normal(0, 1).expand([N])) * s_b
            eta = eta + jnp.where(is_ref, 0.0, b[item])
            c1h = numpyro.sample("c1_h", dist.Normal(c1, 0.5).expand([nR]))
            gh = numpyro.sample("gap_h", dist.LogNormal(0.5, 0.5).expand([nR]))
            c_lo = jnp.where(is_ref, c1h[pos_ref[ann]], c_lo)
            gap_o = jnp.where(is_ref, gh[pos_ref[ann]], gap_o)
        numpyro.factor("ll", logpmf(eta, c_lo, gap_o).sum())

    semilla = cfg["muestreo"]["semilla"] if semilla is None else semilla
    mcmc = MCMC(NUTS(modelo, init_strategy=init_to_median), num_warmup=n_warmup, num_samples=n_muestras,
                num_chains=n_cadenas, chain_method="sequential", progress_bar=False)
    mcmc.run(jax.random.PRNGKey(semilla))
    s = mcmc.get_samples(group_by_chain=True)
    claves = [k for k in ("s_d", "s_g", "c1", "gap", "d_k", "s_b", "c1_h", "gap_h") if k in s]
    res = summary({k: s[k] for k in claves})
    filas = []
    for k, v in res.items():
        medias, rhats, esss = np.atleast_1d(v["mean"]), np.atleast_1d(v["r_hat"]), np.atleast_1d(v["n_eff"])
        for j in range(len(medias)):
            nombre = k if np.ndim(v["mean"]) == 0 else f"{k}[{j}]"
            filas.append({"parametro": nombre, "media": float(medias[j]), "rhat": float(rhats[j]), "ess": float(esss[j])})
    diag = pd.DataFrame(filas)
    diag["convergio"] = (diag["rhat"] < cfg["diagnosticos"]["umbral_rhat"]) & (diag["ess"] >= cfg["diagnosticos"]["umbral_ess"])
    u_s = np.asarray(s["u"]).reshape(-1, N)
    c1s = np.asarray(s["c1"]).reshape(-1)
    gs = np.asarray(s["gap"]).reshape(-1)
    z = (u_s > c1s[:, None]).astype(int) + (u_s > (c1s + gs)[:, None]).astype(int)      # (S, N)
    prob = np.stack([(z == c).mean(0) for c in range(C)], axis=1)
    return {"datos": d, "grupos": grupos, "g_de_item": np.asarray(g_de_item), "z": z, "prob_z": prob, "diagnosticos": diag,
            "convergio": bool(diag["convergio"].all()), "con_referencia": con_ref, "semilla": semilla,
            "d_k": np.asarray(s["d_k"]).reshape(-1, nL), "anotadores_llm": [d.anotadores[i] for i in llm_idx],
            "jax": jax.__version__, "numpyro": numpyro.__version__}


def resumir_grupos(res: dict, nivel: float) -> pd.DataFrame:
    z, gi = res["z"], res["g_de_item"]
    C = res["datos"].C
    lo, hi = (1 - nivel) / 2, 1 - (1 - nivel) / 2
    modal = res["prob_z"].argmax(1) / (C - 1)
    filas = []
    for j, g in enumerate(res["grupos"]):
        m = gi == j
        idx = z[:, m].mean(1) / (C - 1)                      # indice ordinal medio del grupo, por sorteo
        filas.append({"grupo": g, "n_funciones": int(m.sum()), "indice_medio": float(idx.mean()),
                      "indice_lo": float(np.quantile(idx, lo)), "indice_hi": float(np.quantile(idx, hi)),
                      "indice_sin_pooling": float(modal[m].mean())})
    return pd.DataFrame(filas)


def ejecutar(anot_rutas, salida_dir, campo: str = "eloundou_class", cfg: Optional[dict] = None, sobrescribir: bool = False,
             unidad: str = "corrida", **kw) -> dict:
    cfg = cfg or b1.cargar_config()
    largo, info = cargar_ruta_s(anot_rutas, campo, cfg, unidad)
    clases = list(cfg["campos"][campo]["clases"])
    res = ajustar_ordinal(largo, clases, cfg, **kw)
    nivel = cfg["salida"]["nivel_intervalo"]
    etiqueta = cfg["salida"]["etiqueta_normal"]
    lectura = cfg["salida"]["medida_con_humana"] if res["con_referencia"] else cfg["salida"]["medida_sin_humana"]
    grupos = resumir_grupos(res, nivel)
    d = res["datos"]
    items = pd.DataFrame({"item": d.items, "grupo": [res["grupos"][j] for j in res["g_de_item"]],
                          **{f"prob_{c}": res["prob_z"][:, i] for i, c in enumerate(clases)}})
    anot = pd.DataFrame({"anotador": res["anotadores_llm"], "d_k_media": res["d_k"].mean(0),
                         "d_k_lo": np.quantile(res["d_k"], (1 - nivel) / 2, axis=0),
                         "d_k_hi": np.quantile(res["d_k"], 1 - (1 - nivel) / 2, axis=0)})
    out = Path(salida_dir)
    out.mkdir(parents=True, exist_ok=True)
    stem = f"b1_ordinal_{campo}" + ("" if unidad == "corrida" else f"_{unidad}")
    rutas = {n: out / f"{stem}_{n}.parquet" for n in ("grupos", "items", "anotadores", "diagnosticos")}
    rutas["meta"] = out / f"{stem}_meta.json"
    if any(p.exists() for p in rutas.values()) and not sobrescribir:
        raise FileExistsError(f"ya existen salidas {stem}_*; use --sobrescribir")
    for n, df in (("grupos", grupos), ("items", items), ("anotadores", anot), ("diagnosticos", res["diagnosticos"])):
        df.to_parquet(rutas[n], index=False)
    advertencia = None if res["con_referencia"] else (
        "SIN muestra humana: consistencia entre corridas, NO exactitud; sin efecto b_f (no identificable).")
    meta = {"etiqueta": etiqueta, "lectura": lectura, "version_modelo": VERSION_MODELO, "decision": "017" if unidad == "corrida" else "017+018", "campo": campo, "unidad": unidad,
            "advertencia": advertencia, "convergio": res["convergio"], "n_items": d.n_items, "n_grupos": len(res["grupos"]),
            "n_anotadores_llm": len(res["anotadores_llm"]), "n_observaciones": d.n_obs, "semilla": res["semilla"],
            "nivel_intervalo": nivel, "entradas": info, "versiones": {"jax": res["jax"], "numpyro": res["numpyro"]},
            "fecha_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "config_sha256": b1._sha256(b1.CONFIG_PATH)}
    rutas["meta"].write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"rutas": rutas, "meta": meta, "grupos": grupos, "anotadores": anot, "diagnosticos": res["diagnosticos"], "resultado": res}


def main(argv=None) -> int:
    cfg = b1.cargar_config()
    ap = argparse.ArgumentParser(description="B1 ordinal jerarquico (017). Ruta S: parquet con sinco_code, orden, run_id, campo.")
    ap.add_argument("--anotaciones", nargs="+", required=True)
    ap.add_argument("--campo", default="eloundou_class", choices=list(cfg["campos"]))
    ap.add_argument("--salida-dir", default=str(ROOT / cfg["salida"]["dir"]))
    ap.add_argument("--n-cadenas", type=int, default=4)
    ap.add_argument("--n-warmup", type=int, default=1000)
    ap.add_argument("--n-muestras", type=int, default=1000)
    ap.add_argument("--sobrescribir", action="store_true")
    ap.add_argument("--unidad", choices=("corrida", "modelo"), default="corrida")
    a = ap.parse_args(argv)
    r = ejecutar(a.anotaciones, a.salida_dir, a.campo, cfg, a.sobrescribir, unidad=a.unidad,
                 n_cadenas=a.n_cadenas, n_warmup=a.n_warmup, n_muestras=a.n_muestras)
    print(json.dumps({k: r["meta"][k] for k in ("etiqueta", "lectura", "convergio", "n_items", "n_grupos", "n_observaciones")},
                     ensure_ascii=False))
    print(r["diagnosticos"].round(3).to_string(index=False))
    print(r["anotadores"].round(3).to_string(index=False))
    print(r["grupos"].head(10).round(3).to_string(index=False))
    return 0 if r["meta"]["convergio"] else 6


if __name__ == "__main__":
    raise SystemExit(main())
