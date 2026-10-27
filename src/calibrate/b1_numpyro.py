"""B1 con NumPyro (decision 016): mismo modelo Dawid-Skene que b1_dawid_skene.py, muestreado con NUTS.

Reutiliza cargadores, Datos y priors de b1_dawid_skene (hiperparametros de config.toml, PROVISIONAL). Sirve para
comparar con el Gibbs propio (linea base `b1-0.1`) antes de pasar al modelo ordinal jerarquico. Lo que mide y sus
limites son los mismos: sin referencia humana, solo consistencia entre corridas, NO exactitud.

Identificabilidad: Dawid-Skene tiene intercambio de etiquetas; con inicializacion aleatoria las cadenas no convergen
(016, Enmienda 1). Se usa init_to_median y priors con diagonal > fuera de la diagonal.
Dependencias: requirements-calibrate.txt (importacion perezosa: el resto de src/calibrate no la necesita).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.calibrate import b1_dawid_skene as b1

VERSION_MODELO = "b1-numpyro-0.1"


def ajustar_numpyro(largo: pd.DataFrame, clases: list[str], cfg: dict, prior: str | None = None, semilla: int | None = None,
                    n_cadenas: int = 4, n_warmup: int = 1000, n_muestras: int = 1000) -> dict:
    import jax
    import jax.numpy as jnp
    import numpyro
    import numpyro.distributions as dist
    from numpyro.diagnostics import summary
    from numpyro.infer import MCMC, NUTS, init_to_median

    d = b1.Datos(largo, clases)
    prior_theta = jnp.asarray(b1.construir_prior(d, cfg, prior))
    alpha_pi = float(cfg["prior"]["prevalencia"]["alpha"])
    item, ann, y = jnp.asarray(d.item), jnp.asarray(d.ann), jnp.asarray(d.y)
    N, K, C = d.n_items, d.n_ann, d.C

    def log_post_z(pi, theta):
        contrib = jnp.log(theta)[ann, :, y]                       # (n_obs, C): log P(y_obs | z=c)
        return jnp.log(pi)[None, :] + jax.ops.segment_sum(contrib, item, num_segments=N)

    def modelo():
        pi = numpyro.sample("pi", dist.Dirichlet(jnp.full(C, alpha_pi)))
        theta = numpyro.sample("theta", dist.Dirichlet(prior_theta))
        numpyro.factor("ll", jax.scipy.special.logsumexp(log_post_z(pi, theta), axis=1).sum())

    semilla = cfg["muestreo"]["semilla"] if semilla is None else semilla
    mcmc = MCMC(NUTS(modelo, init_strategy=init_to_median), num_warmup=n_warmup, num_samples=n_muestras,
                num_chains=n_cadenas, chain_method="sequential", progress_bar=False)
    mcmc.run(jax.random.PRNGKey(semilla))
    s = mcmc.get_samples(group_by_chain=True)                      # (cadenas, muestras, ...)
    resumen = summary(s)
    rhat = max(float(np.max(v["r_hat"])) for v in resumen.values())
    ess = min(float(np.min(v["n_eff"])) for v in resumen.values())
    pi_s = np.asarray(s["pi"]).reshape(-1, C); th_s = np.asarray(s["theta"]).reshape(-1, K, C, C)
    pz = np.asarray(jax.vmap(lambda p, t: jax.nn.softmax(log_post_z(p, t), axis=1))(jnp.asarray(pi_s), jnp.asarray(th_s))).mean(0)
    return {"datos": d, "pi": pi_s, "theta": th_s, "prob_z": pz, "rhat_max": rhat, "ess_min": ess,
            "convergio": bool(rhat < cfg["diagnosticos"]["umbral_rhat"] and ess >= cfg["diagnosticos"]["umbral_ess"]),
            "jax": jax.__version__, "numpyro": numpyro.__version__, "version_modelo": VERSION_MODELO}


def comparar_con_gibbs(largo, clases, cfg, **kw) -> dict:
    """Ajusta con ambos muestreadores y devuelve las diferencias en prevalencias, diagonales de confusion y clase modal."""
    g = b1.ajustar(largo, clases, cfg, prior=kw.get("prior"))
    n = ajustar_numpyro(largo, clases, cfg, **kw)
    pi_g = np.concatenate([c["pi"] for c in g["cadenas"]]).mean(0)
    th_g = np.concatenate([c["theta"] for c in g["cadenas"]]).mean(0)
    pz_g = sum(c["zcount"] for c in g["cadenas"]); pz_g = pz_g / pz_g.sum(1, keepdims=True)
    diag = lambda t: np.stack([np.diag(t[k]) for k in range(t.shape[0])])
    return {"pi_gibbs": pi_g.round(4).tolist(), "pi_numpyro": n["pi"].mean(0).round(4).tolist(),
            "dif_max_pi": float(np.abs(pi_g - n["pi"].mean(0)).max()),
            "dif_max_diag_theta": float(np.abs(diag(th_g) - diag(n["theta"].mean(0))).max()),
            "dif_max_theta": float(np.abs(th_g - n["theta"].mean(0)).max()),
            "acuerdo_clase_modal": float((pz_g.argmax(1) == n["prob_z"].argmax(1)).mean()),
            "gibbs_convergio": g["convergio"], "numpyro_convergio": n["convergio"],
            "numpyro_rhat_max": n["rhat_max"], "numpyro_ess_min": n["ess_min"],
            "n_items": n["datos"].n_items, "anotadores": n["datos"].anotadores}


def main(argv=None) -> int:
    cfg = b1.cargar_config()
    ap = argparse.ArgumentParser(description="Compara B1 NumPyro vs Gibbs (016). Solo imprime; no escribe en data/.")
    ap.add_argument("--anotaciones", nargs="+", required=True)
    ap.add_argument("--campo", default="exposure_class", choices=list(cfg["campos"]))
    ap.add_argument("--prior", choices=["debil", "fuerte"], default=None)
    a = ap.parse_args(argv)
    largo, _ = b1.cargar_anotaciones_llm(a.anotaciones, a.campo, cfg)
    print(json.dumps(comparar_con_gibbs(largo, list(cfg["campos"][a.campo]["clases"]), cfg, prior=a.prior), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
