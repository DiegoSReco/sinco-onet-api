"""Lectura, validacion y consolidacion de las fichas de revision de la muestra de oro (005 8.1-8.2).

Uso:
  .venv\\Scripts\\python -m src.match.oro_resultados --a revisor_A_lleno.csv --b revisor_B_lleno.csv [--muestra principal]

Calcula: kappa de Cohen (nominal y ponderado lineal) entre revisores sobre {exacto, parcial, incorrecto},
kappa binario (aceptable = exacto o parcial), acuerdo en el "mejor" candidato, y por modelo precision@k, MRR,
recall@k y precision@1 ponderada por el diseno, con intervalos de Wilson / bootstrap por ficha.
No calcula exposicion ni usa probabilidades de Frey-Osborne. Las cifras son de revision humana y siguen
rotuladas con parametros provisionales (umbral de kappa sin decidir).
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

from src.match.oro import COLUMNAS_FICHA, OTRO_ID, PROC, TAG, cargar_config

VALORACIONES = ["incorrecto", "parcial", "exacto"]  # orden ordinal
CONFIANZAS = ["alta", "media", "baja"]
SI = {"si", "s", "x", "1", "true", "yes"}


class FichaError(ValueError):
    """La ficha no cumple el esquema (regla 5 de CLAUDE.md: no se calcula nada con fichas invalidas)."""

    def __init__(self, errores: list[str]):
        self.errores = errores
        super().__init__(f"{len(errores)} error(es) de esquema:\n- " + "\n- ".join(errores[:50]))


def _norm(x) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return ""
    s = unicodedata.normalize("NFKD", str(x)).encode("ascii", "ignore").decode().strip().lower()
    return s


# ---------------------------------------------------------------- lectura
def leer_ficha(path: Path) -> pd.DataFrame:
    """Lee un CSV de Excel: UTF-8 con BOM (o cp1252), delimitador coma, punto y coma o tabulador."""
    raw = Path(path).read_bytes()
    for enc in ("utf-8-sig", "cp1252"):
        try:
            texto = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    primera = texto.split("\n", 1)[0]
    delim = max([",", ";", "\t"], key=primera.count)
    df = pd.read_csv(io.StringIO(texto), sep=delim, dtype=str, keep_default_na=False, quoting=csv.QUOTE_MINIMAL)
    df.columns = [c.strip() for c in df.columns]
    return df


def validar_ficha(df: pd.DataFrame, llave: pd.DataFrame, rev: str, fichas: set[str] | None = None,
                  completa: bool = True) -> pd.DataFrame:
    """Valida el esquema y devuelve una tabla normalizada por (ficha_id, cand_id). Levanta FichaError."""
    err: list[str] = []
    faltan = [c for c in COLUMNAS_FICHA if c not in df.columns]
    if faltan:
        raise FichaError([f"faltan columnas: {faltan}"])
    d = df[COLUMNAS_FICHA].copy()
    for c in COLUMNAS_FICHA:
        d[c] = d[c].astype(str).str.strip()
    d["valoracion_n"] = d["valoracion"].map(_norm)
    d["confianza_n"] = d["confianza"].map(_norm)
    d["mejor"] = d["es_mejor"].map(lambda v: _norm(v) in SI)
    d["ninguno"] = d["ninguno_otro"].map(lambda v: _norm(v) in SI)
    for c in ("es_mejor", "ninguno_otro"):
        raros = d[(d[c] != "") & ~d[c].map(lambda v: _norm(v) in SI)]
        for _, r in raros.iterrows():
            err.append(f"{r.ficha_id}/{r.cand_id}: valor no valido en {c}: '{r[c]}' (use 'si' o deje vacio)")
    if d.duplicated(["ficha_id", "cand_id"]).any():
        err.append("filas duplicadas (ficha_id, cand_id)")
    esperado = llave[["ficha_id", "onet_soc_code", f"cand_id_{rev}"]].rename(columns={f"cand_id_{rev}": "cand_id"})
    esperado = esperado.dropna(subset=["cand_id"])
    fid_esp = set(llave["ficha_id"]) if fichas is None else set(fichas)
    presentes = set(d["ficha_id"])
    ajenas = presentes - set(llave["ficha_id"])
    if ajenas:
        err.append(f"fichas que no estan en la llave: {sorted(ajenas)[:10]}")
    if completa and (fid_esp - presentes):
        err.append(f"fichas ausentes: {len(fid_esp - presentes)} (p. ej. {sorted(fid_esp - presentes)[:5]})")
    usar = fid_esp & presentes
    esperado = esperado[esperado.ficha_id.isin(usar)]
    cand = d[(d.cand_id != OTRO_ID) & d.ficha_id.isin(usar)]
    m = cand.merge(esperado, on=["ficha_id", "cand_id"], how="outer", suffixes=("", "_esp"), indicator=True)
    for _, r in m[m._merge != "both"].head(20).iterrows():
        err.append(f"{r.ficha_id}/{r.cand_id}: candidato {'sobrante' if r._merge == 'left_only' else 'ausente'}")
    for _, r in m[(m._merge == "both") & (m.onet_soc_code != m.onet_soc_code_esp)].iterrows():
        err.append(f"{r.ficha_id}/{r.cand_id}: codigo O*NET modificado ({r.onet_soc_code} != {r.onet_soc_code_esp})")
    for fid in sorted(usar):
        g = d[d.ficha_id == fid]
        c = g[g.cand_id != OTRO_ID]
        o = g[g.cand_id == OTRO_ID]
        if len(o) != 1:
            err.append(f"{fid}: debe tener exactamente una fila {OTRO_ID}")
            continue
        o = o.iloc[0]
        malas = c[~c.valoracion_n.isin(VALORACIONES)]
        for _, r in malas.iterrows():
            err.append(f"{fid}/{r.cand_id}: valoracion invalida o vacia ('{r.valoracion}'); use exacto, parcial o incorrecto")
        if o.valoracion_n:
            err.append(f"{fid}: la fila {OTRO_ID} no lleva valoracion")
        n_mejor = int(c["mejor"].sum())
        if n_mejor + int(o["ninguno"]) != 1:
            err.append(f"{fid}: marque exactamente una de: un candidato como mejor (es_mejor=si) o ninguno_otro=si en la fila {OTRO_ID}")
        if n_mejor == 1 and c[c.mejor].iloc[0].valoracion_n == "incorrecto":
            err.append(f"{fid}: el mejor candidato no puede ser 'incorrecto'")
        if o["ninguno"] and (c.valoracion_n == "exacto").any():
            err.append(f"{fid}: ninguno_otro=si pero hay candidatos 'exacto'")
        if o.confianza_n not in CONFIANZAS:
            err.append(f"{fid}: confianza en la fila {OTRO_ID} debe ser alta, media o baja")
    if err:
        raise FichaError(err)
    return d[d.ficha_id.isin(usar)].reset_index(drop=True)


# ---------------------------------------------------------------- consolidacion
def consolidar(da: pd.DataFrame, db: pd.DataFrame, llave: pd.DataFrame) -> pd.DataFrame:
    """Una fila por candidato (de la llave) con las valoraciones de A y B ya validadas."""
    def lado(d, rev):
        c = d[d.cand_id != OTRO_ID][["ficha_id", "onet_soc_code", "valoracion_n", "mejor"]]
        return c.rename(columns={"valoracion_n": f"val_{rev}", "mejor": f"mejor_{rev}"})
    k = llave.merge(lado(da, "A"), on=["ficha_id", "onet_soc_code"]).merge(lado(db, "B"), on=["ficha_id", "onet_soc_code"])
    for rev in "AB":
        k[f"acept_{rev}"] = k[f"val_{rev}"].isin(["exacto", "parcial"])
    k["acept_estricto"] = k.acept_A & k.acept_B
    k["acept_laxo"] = k.acept_A | k.acept_B
    return k


def _wilson(x: float, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = x / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (float(c - h), float(c + h))


def _kappa(a, b, weights=None, labels=None) -> float:
    a, b = list(a), list(b)
    if len(set(a) | set(b)) < 2:
        return float("nan")  # sin variabilidad: kappa indefinido
    return float(cohen_kappa_score(a, b, weights=weights, labels=labels))


def kappas(cons: pd.DataFrame) -> dict:
    """Kappa de Cohen entre revisores, solo sobre candidatos reales (no distractores se incluyen: son parte de la tarea)."""
    ord_a = cons.val_A.map(VALORACIONES.index)
    ord_b = cons.val_B.map(VALORACIONES.index)
    return {
        "n_pares": int(len(cons)),
        "kappa_nominal": _kappa(cons.val_A, cons.val_B),
        "kappa_ponderado_lineal": _kappa(ord_a, ord_b, weights="linear", labels=[0, 1, 2]),
        "kappa_binario_aceptable": _kappa(cons.acept_A, cons.acept_B),
        "acuerdo_observado_3cat": float((cons.val_A == cons.val_B).mean()),
        "acuerdo_observado_binario": float((cons.acept_A == cons.acept_B).mean()),
    }


def acuerdo_mejor(da: pd.DataFrame, db: pd.DataFrame) -> dict:
    def mejor(d):
        out = {}
        for fid, g in d.groupby("ficha_id"):
            m = g[(g.cand_id != OTRO_ID) & g.mejor]
            out[fid] = m.iloc[0].onet_soc_code if len(m) else OTRO_ID
        return pd.Series(out)
    a, b = mejor(da), mejor(db)
    b = b.reindex(a.index)
    gg = lambda s: s.map(lambda x: x[:2] if x != OTRO_ID else OTRO_ID)
    return {"n_fichas": int(len(a)), "acuerdo_mejor_soc": float((a == b).mean()),
            "kappa_mejor_soc": _kappa(a, b), "acuerdo_mejor_gran_grupo_soc2": float((gg(a) == gg(b)).mean()),
            "kappa_mejor_gran_grupo_soc2": _kappa(gg(a), gg(b)),
            "fichas_ninguno_otro_A": float((a == OTRO_ID).mean()), "fichas_ninguno_otro_B": float((b == OTRO_ID).mean())}


def bootstrap_kappas(cons: pd.DataFrame, B: int, seed: int) -> dict:
    """Intervalo percentil 95 % remuestreando fichas (los pares de una ficha no son independientes)."""
    rng = np.random.default_rng(np.random.SeedSequence([seed, 7]))
    grupos = {f: g for f, g in cons.groupby("ficha_id")}
    ids = np.array(sorted(grupos))
    res = {"kappa_nominal": [], "kappa_ponderado_lineal": []}
    for _ in range(B):
        s = rng.choice(ids, size=len(ids), replace=True)
        c = pd.concat([grupos[f] for f in s])
        k = kappas(c)
        for n in res:
            res[n].append(k[n])
    out = {}
    for n, v in res.items():
        v = np.array(v, dtype=float)
        v = v[~np.isnan(v)]
        out[n] = [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] if len(v) else [float("nan")] * 2
    return out


def metricas_modelo(cons: pd.DataFrame, acept: str, tag: str, ks=(1, 3, 5)) -> dict:
    """precision@k, MRR, recall@k de un modelo, tomando `acept` como verdad. Solo ve lo mostrado a los revisores
    (pool top-5 por modelo): el recall esta sesgado por pooling (005 8.1, riesgo 8)."""
    rk, w = f"rango_{tag}", "peso_diseno"
    d = cons[(~cons.es_distractor) & cons[rk].notna()]
    fichas = sorted(d.ficha_id.unique())
    p1, mrr, wts = [], [], []
    prec = {k: [] for k in ks}
    rec = {k: [] for k in ks}
    for f in fichas:
        g = d[d.ficha_id == f].sort_values(rk)
        a = g[acept].to_numpy()
        p1.append(float(a[0]) if g[rk].iloc[0] == 1 else 0.0)
        pos = np.flatnonzero(a)
        mrr.append(1.0 / g[rk].iloc[pos[0]] if len(pos) else 0.0)
        wts.append(float(g[w].iloc[0]))
        total_acept = int(cons[(cons.ficha_id == f) & (~cons.es_distractor)][acept].sum())
        for k in ks:
            t = g[g[rk] <= k]
            prec[k].append(float(t[acept].sum()) / k)
            if total_acept:
                rec[k].append(float(t[acept].sum()) / total_acept)
    n = len(fichas)
    w_ = np.array(wts)
    out = {"n_fichas": n, "precision@1": float(np.mean(p1)) if n else float("nan"),
           "precision@1_wilson95": _wilson(sum(p1), n),
           "precision@1_ponderada_diseno": float(np.average(p1, weights=w_)) if n else float("nan"),
           "MRR": float(np.mean(mrr)) if n else float("nan"),
           "MRR_ponderado_diseno": float(np.average(mrr, weights=w_)) if n else float("nan"),
           "n_fichas_con_aceptable": int(len(rec[ks[0]]))}
    for k in ks:
        out[f"precision@{k}"] = float(np.mean(prec[k])) if n else float("nan")
        out[f"recall@{k}"] = float(np.mean(rec[k])) if rec[k] else float("nan")
    return out


def calcular(cons: pd.DataFrame, muestra: pd.DataFrame | None, cfg: dict, da: pd.DataFrame, db: pd.DataFrame,
             con_bootstrap: bool = True) -> dict:
    ks = tuple(cfg["resultados"]["k_precision"])
    cons = cons.copy()
    cons = cons.merge(muestra[["ficha_id", "division", "tipo_caso", "tercil_margen"]], on="ficha_id", how="left") \
        if muestra is not None else cons
    out: dict = {"estado": "revision humana; parametros provisionales (umbral_kappa sin decidir)",
                 "n_fichas": int(cons.ficha_id.nunique())}
    kp = kappas(cons)
    kp["umbral_kappa_provisional"] = cfg["resultados"]["umbral_kappa"]
    kp["cumple_umbral_provisional"] = bool(kp["kappa_nominal"] >= kp["umbral_kappa_provisional"]) if not np.isnan(kp["kappa_nominal"]) else None
    if con_bootstrap:
        kp["bootstrap_IC95"] = bootstrap_kappas(cons, cfg["resultados"]["bootstrap_B"], cfg["meta"]["seed"])
    out["acuerdo_revisores"] = kp
    out["acuerdo_mejor"] = acuerdo_mejor(da, db)
    real = cons[~cons.es_distractor]
    out["distractores"] = {"n": int(cons.es_distractor.sum()),
                           "aceptados_A": float(cons[cons.es_distractor].acept_A.mean()) if cons.es_distractor.any() else None,
                           "aceptados_B": float(cons[cons.es_distractor].acept_B.mean()) if cons.es_distractor.any() else None}
    out["aceptables_por_ficha_estricto"] = {"media": float(real.groupby("ficha_id").acept_estricto.sum().mean()),
                                            "fichas_sin_aceptable": int((real.groupby("ficha_id").acept_estricto.sum() == 0).sum())}
    esc = ["acept_A", "acept_B", "acept_estricto", "acept_laxo"]
    out["metricas_por_modelo"] = {e: {m: metricas_modelo(cons, e, t, ks) for m, t in TAG.items()} for e in esc}
    por = {}
    for col in ("mitad", "division", "tipo_caso", "tercil_margen"):
        if col in cons.columns and cons[col].notna().any():
            por[col] = {str(v): {m: metricas_modelo(g, "acept_estricto", t, ks) for m, t in TAG.items()}
                        for v, g in cons.groupby(col)}
    out["metricas_estricto_por_estrato"] = por
    a = cons.drop_duplicates("ficha_id")
    return out


def main(a: Path, b: Path, muestra_sel: str | None = "principal", llave_path: Path = PROC / "oro_llave.parquet",
         muestra_path: Path = PROC / "oro_muestra.parquet", salida: Path | None = PROC / "oro_resultados.json",
         config=None) -> dict:
    cfg = cargar_config() if config is None else config
    llave = pd.read_parquet(llave_path)
    muestra = pd.read_parquet(muestra_path) if Path(muestra_path).exists() else None
    if muestra_sel:
        llave = llave[llave.muestra == muestra_sel]
        if muestra is not None:
            muestra = muestra[muestra.muestra == muestra_sel]
    # el CSV trae piloto y principal juntos: se valida solo la muestra elegida (las demas filas se ignoran)
    sel = set(llave["ficha_id"])
    fa, fb = leer_ficha(a), leer_ficha(b)
    da = validar_ficha(fa[fa["ficha_id"].isin(sel)], llave, "A")
    db = validar_ficha(fb[fb["ficha_id"].isin(sel)], llave, "B")
    cons = consolidar(da, db, llave)
    res = calcular(cons, muestra, cfg, da, db)
    res["muestra"] = muestra_sel
    if salida:
        Path(salida).write_text(json.dumps(res, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", type=Path, required=True)
    ap.add_argument("--b", type=Path, required=True)
    ap.add_argument("--muestra", default="principal", choices=["principal", "piloto"])
    ap.add_argument("--salida", type=Path, default=PROC / "oro_resultados.json")
    x = ap.parse_args()
    print(json.dumps(main(x.a, x.b, x.muestra, salida=x.salida), indent=2, ensure_ascii=False, default=str))
