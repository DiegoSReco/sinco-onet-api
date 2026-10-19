"""Muestra de oro del emparejamiento A1 (005 8.1): muestreo estratificado, fichas ciegas y llave.

Uso:  .venv\\Scripts\\python -m src.match.oro [--salida DIR]
No carga modelos: usa las tablas ya generadas (match_candidatos, match_sinco_resumen).
No calcula exposicion ni usa probabilidades de Frey-Osborne (ni en fichas ni en la muestra).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tomllib
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data" / "processed"
CONFIG_ORO = Path(__file__).with_name("oro_config.toml")

COLUMNAS_FICHA = [
    "ficha_id", "sinco_code", "sinco_titulo", "sinco_descripcion", "sinco_funciones", "sinco_ocupaciones_ejemplo",
    "cand_id", "onet_soc_code", "onet_titulo_en", "onet_descripcion_breve",
    "valoracion", "es_mejor", "ninguno_otro", "otro_soc", "confianza", "comentarios",
]
OTRO_ID = "OTRO"
TAG = {"bge-m3": "bge_m3", "multilingual-e5-large": "e5"}


def cargar_config(path: Path = CONFIG_ORO) -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ---------------------------------------------------------------- muestreo
def asignar(tamanos: dict, factores: dict, n: int, minimo: int) -> dict:
    """Asignacion proporcional a N_h * f_h con minimo por estrato y tope N_h (determinista)."""
    n = min(n, sum(tamanos.values()))
    asig = {h: min(minimo, N) for h, N in tamanos.items()}
    while sum(asig.values()) > n:
        h = max(asig, key=lambda x: (asig[x], x))
        asig[h] -= 1
    total = sum(tamanos[h] * factores[h] for h in tamanos)
    ideal = {h: n * tamanos[h] * factores[h] / total for h in tamanos}
    while sum(asig.values()) < n:
        cand = [h for h in tamanos if asig[h] < tamanos[h]]
        h = max(cand, key=lambda x: (ideal[x] - asig[x], str(x)))
        asig[h] += 1
    return asig


def muestrear(pob: pd.DataFrame, n: int, minimo: int, cfg_m: dict, rng) -> pd.DataFrame:
    """MAS dentro de cada estrato (division x tipo de caso); devuelve filas con N_h, n_h y peso de diseno."""
    fac = {"acuerdo": 1.0, "discrepancia": cfg_m["factor_discrepancia"], "sin_coincidencia": cfg_m["factor_sin_coincidencia"]}
    tam = pob.groupby("estrato").size().to_dict()
    f = {h: fac[h.split("|")[1]] for h in tam}
    asig = asignar(tam, f, n, minimo)
    partes = []
    for h in sorted(tam):
        g = pob[pob["estrato"] == h].sort_values("sinco_code")
        idx = rng.choice(len(g), size=asig[h], replace=False)
        s = g.iloc[sorted(idx)].copy()
        s["N_estrato"], s["n_estrato"] = tam[h], asig[h]
        s["peso_diseno"] = tam[h] / asig[h]
        partes.append(s)
    return pd.concat(partes, ignore_index=True)


def construir_poblacion(cfg: dict, proc: Path) -> pd.DataFrame:
    sinco = pd.read_parquet(proc / "sinco.parquet")
    gu = sinco[sinco["nivel"] == "grupo_unitario"][["sinco_code", "titulo", "division"]].copy()
    res = pd.read_parquet(proc / "match_sinco_resumen.parquet")
    cand = pd.read_parquet(proc / "match_candidatos.parquet")
    modelos = cfg["meta"]["modelos"]
    mp = cfg["meta"]["modelo_principal"]
    pop = gu.set_index("sinco_code")
    for m in modelos:
        t = cand[(cand.modelo == m) & (cand.rango == 1)].set_index("sinco_code")["onet_soc_code"]
        pop[f"top1_{TAG[m]}"] = t
        r = res[res.modelo == m].set_index("sinco_code")
        pop[f"match_status_{TAG[m]}"] = r["match_status"]
        pop[f"baja_confianza_{TAG[m]}"] = r["baja_confianza"]
        pop[f"margen_{TAG[m]}"] = r["margen"]
    rp = res[res.modelo == mp].set_index("sinco_code")
    pop["residual_sin_funciones"] = rp["residual_sin_funciones"]
    pop["residual_por_titulo"] = rp["residual_por_titulo"]
    a, b = TAG[modelos[0]], TAG[modelos[1]]
    pop["top1_coincide"] = pop[f"top1_{a}"] == pop[f"top1_{b}"]
    pop["tipo_caso"] = np.where(pop[f"match_status_{TAG[mp]}"] == "sin_coincidencia", "sin_coincidencia",
                                np.where(pop["top1_coincide"], "acuerdo", "discrepancia"))
    pop["tercil_margen"] = pd.qcut(pop[f"margen_{TAG[mp]}"].astype(float), 3, labels=["bajo", "medio", "alto"]).astype(str)
    nf = pd.read_parquet(proc / "sinco_funciones.parquet").groupby("sinco_code").size()
    ne = pd.read_parquet(proc / "sinco_ocupaciones_ejemplo.parquet").groupby("sinco_code").size()
    pop["n_funciones"] = nf.reindex(pop.index).fillna(0).astype(int)
    pop["n_ocupaciones_ejemplo"] = ne.reindex(pop.index).fillna(0).astype(int)
    pop["tiene_funciones"] = pop["n_funciones"] > 0
    pop["tiene_ocupaciones_ejemplo"] = pop["n_ocupaciones_ejemplo"] > 0
    pop["estrato"] = pop["division"].astype(str) + "|" + pop["tipo_caso"]
    return pop.reset_index()


def construir_muestra(cfg: dict, pop: pd.DataFrame) -> pd.DataFrame:
    seed = cfg["meta"]["seed"]
    cm = cfg["muestra"]
    principal = muestrear(pop, cm["n_principal"], cm["minimo_por_estrato_principal"], cm,
                          np.random.default_rng(np.random.SeedSequence([seed, 1])))
    principal["muestra"] = "principal"
    resto = pop[~pop["sinco_code"].isin(principal["sinco_code"])]
    piloto = muestrear(resto, cm["n_piloto"], cm["minimo_por_estrato_piloto"], cm,
                       np.random.default_rng(np.random.SeedSequence([seed, 2])))
    piloto["muestra"] = "piloto"
    m = pd.concat([principal, piloto], ignore_index=True)
    rng = np.random.default_rng(np.random.SeedSequence([seed, 3]))
    m["mitad"] = ""
    for h in sorted(m.loc[m.muestra == "principal", "estrato"].unique()):
        g = m[(m.muestra == "principal") & (m.estrato == h)].sort_values("sinco_code")
        ids = rng.permutation(g.index.to_numpy())
        ncal = int(round(len(ids) * cm["fraccion_calibracion"]))
        m.loc[ids[:ncal], "mitad"] = "calibracion"
        m.loc[ids[ncal:], "mitad"] = "prueba"
    m.loc[m.muestra == "piloto", "mitad"] = "piloto"
    m = m.sort_values(["muestra", "sinco_code"]).reset_index(drop=True)
    pref = np.where(m["muestra"] == "piloto", "P", "M")
    m.insert(0, "ficha_id", [f"{p}{i + 1:03d}" for p, i in zip(pref, m.groupby("muestra").cumcount())])
    return m


# ---------------------------------------------------------------- candidatos y llave
def breve(txt: str, n: int) -> str:
    txt = " ".join(str(txt or "").split())
    if len(txt) <= n:
        return txt
    return txt[:n].rsplit(" ", 1)[0].rstrip(".,;:") + "..."


def construir_llave(cfg: dict, muestra: pd.DataFrame, proc: Path) -> pd.DataFrame:
    cand = pd.read_parquet(proc / "match_candidatos.parquet")
    onet = pd.read_parquet(proc / "onet_ocupaciones.parquet")
    res = pd.read_parquet(proc / "match_sinco_resumen.parquet")
    modelos = cfg["meta"]["modelos"]
    kpm = cfg["revision"]["candidatos_por_modelo"]
    nd = cfg["revision"]["n_distractores"]
    seed = cfg["meta"]["seed"]
    todos = sorted(onet["onet_soc_code"])
    filas = []
    for _, fr in muestra.iterrows():
        sc = fr["sinco_code"]
        c = cand[cand.sinco_code == sc]
        por_modelo = {m: c[c.modelo == m].set_index("onet_soc_code") for m in modelos}
        union = sorted({s for m in modelos for s in por_modelo[m].index[por_modelo[m]["rango"] <= kpm]})
        for soc in union:
            r = {"ficha_id": fr["ficha_id"], "muestra": fr["muestra"], "sinco_code": sc, "onet_soc_code": soc,
                 "es_distractor": False}
            presentes = []
            for m in modelos:
                cm, t = por_modelo[m], TAG[m]
                if soc in cm.index:
                    r[f"rango_{t}"] = int(cm.loc[soc, "rango"])
                    r[f"similitud_{t}"] = float(cm.loc[soc, "similitud"])
                    r[f"en_conjunto_{t}"] = bool(cm.loc[soc, "en_conjunto"])
                    if cm.loc[soc, "rango"] <= kpm:
                        presentes.append(m)
                else:
                    r[f"rango_{t}"] = np.nan
                    r[f"similitud_{t}"] = np.nan
                    r[f"en_conjunto_{t}"] = False
                rr = res[(res.modelo == m) & (res.sinco_code == sc)].iloc[0]
                r[f"margen_{t}"] = float(rr["margen"])
                r[f"match_status_{t}"] = rr["match_status"]
                r[f"baja_confianza_{t}"] = bool(rr["baja_confianza"])
            r["modelos_que_lo_proponen"] = "+".join(presentes)
            filas.append(r)
        excl = set(c["onet_soc_code"])
        rng = np.random.default_rng(np.random.SeedSequence([seed, 4, int(sc)]))
        pool = [x for x in todos if x not in excl]
        for soc in rng.choice(pool, size=nd, replace=False):
            filas.append({"ficha_id": fr["ficha_id"], "muestra": fr["muestra"], "sinco_code": sc, "onet_soc_code": str(soc),
                          "es_distractor": True, "modelos_que_lo_proponen": "distractor"})
    k = pd.DataFrame(filas)
    k = k.merge(onet.rename(columns={"titulo_en": "onet_titulo_en", "descripcion_en": "onet_descripcion_en"}),
                on="onet_soc_code", how="left")
    return k.sort_values(["ficha_id", "onet_soc_code"]).reset_index(drop=True)


def _lista(x) -> str:
    return "\n".join("- " + " ".join(str(t).split()).rstrip(".") for t in x)


def textos_sinco(proc: Path) -> pd.DataFrame:
    d = pd.read_parquet(proc / "sinco_descripcion.parquet").set_index("sinco_code")
    s = pd.read_parquet(proc / "sinco.parquet").set_index("sinco_code")
    fu = pd.read_parquet(proc / "sinco_funciones.parquet").sort_values(["sinco_code", "orden"])
    oc = pd.read_parquet(proc / "sinco_ocupaciones_ejemplo.parquet").sort_values(["sinco_code", "orden"])
    out = pd.DataFrame(index=s.index)
    out["sinco_titulo"] = s["titulo"]
    out["sinco_descripcion"] = d["descripcion"].reindex(out.index).fillna("")
    out["sinco_funciones"] = fu.groupby("sinco_code")["funcion"].apply(_lista).reindex(out.index).fillna("")
    out["sinco_ocupaciones_ejemplo"] = oc.groupby("sinco_code")["ocupacion"].apply(_lista).reindex(out.index).fillna("")
    return out


def construir_fichas(cfg: dict, muestra: pd.DataFrame, llave: pd.DataFrame, proc: Path) -> dict:
    tx = textos_sinco(proc)
    nmax = cfg["revision"]["max_chars_descripcion_onet"]
    seed = cfg["meta"]["seed"]
    por_ficha = {fid: g for fid, g in llave.groupby("ficha_id")}
    fichas = {}
    for ri, rev in enumerate(cfg["revision"]["revisores"]):
        rng = np.random.default_rng(np.random.SeedSequence([seed, 5, ri]))
        filas = []
        for fid in rng.permutation(muestra["ficha_id"].to_numpy()):
            g = por_ficha[fid]
            sc = g["sinco_code"].iloc[0]
            g = g.iloc[rng.permutation(len(g))]
            for j, (_, r) in enumerate(g.iterrows(), 1):
                fila = dict.fromkeys(COLUMNAS_FICHA, "")
                fila.update(ficha_id=fid, sinco_code=sc, sinco_titulo=tx.loc[sc, "sinco_titulo"], cand_id=f"c{j:02d}",
                            onet_soc_code=r["onet_soc_code"], onet_titulo_en=r["onet_titulo_en"],
                            onet_descripcion_breve=breve(r["onet_descripcion_en"], nmax))
                if j == 1:  # texto SINCO una sola vez por ficha (no ordenar la hoja)
                    fila.update({c: tx.loc[sc, c] for c in ("sinco_descripcion", "sinco_funciones", "sinco_ocupaciones_ejemplo")})
                filas.append(fila)
            fila = dict.fromkeys(COLUMNAS_FICHA, "")
            fila.update(ficha_id=fid, sinco_code=sc, sinco_titulo=tx.loc[sc, "sinco_titulo"], cand_id=OTRO_ID,
                        onet_titulo_en="(Ninguno de los anteriores / otro SOC)")
            filas.append(fila)
        fichas[rev] = pd.DataFrame(filas, columns=COLUMNAS_FICHA)
    return fichas


def escribir_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig", lineterminator="\r\n")


def llave_con_ids(llave: pd.DataFrame, fichas: dict) -> pd.DataFrame:
    """Agrega a la llave el cand_id y la posicion mostrados a cada revisor."""
    for rev, df in fichas.items():
        d = df[df.cand_id != OTRO_ID][["ficha_id", "onet_soc_code", "cand_id"]].copy()
        d["pos"] = d["cand_id"].str[1:].astype(int)
        d = d.rename(columns={"cand_id": f"cand_id_{rev}", "pos": f"posicion_{rev}"})
        llave = llave.merge(d, on=["ficha_id", "onet_soc_code"], how="left")
    return llave


def main(salida: Path = PROC, config: Path = CONFIG_ORO) -> dict:
    cfg = cargar_config(config)
    pop = construir_poblacion(cfg, PROC)
    muestra = construir_muestra(cfg, pop)
    llave = construir_llave(cfg, muestra, PROC)
    fichas = construir_fichas(cfg, muestra, llave, PROC)
    cand_path = PROC / "match_candidatos.parquet"
    run_ids = pd.read_parquet(cand_path)["run_id"].unique().tolist()
    run_id = f"oro-{datetime.now(timezone.utc):%Y%m%dT%H%M%S}-{sha256(config)[:8]}"
    muestra["oro_run_id"] = run_id
    muestra["match_run_id"] = ";".join(run_ids)
    muestra["estado_validacion"] = "sin_validar"
    llave = llave_con_ids(llave, fichas)
    llave = llave.merge(muestra[["ficha_id", "mitad", "peso_diseno"]], on="ficha_id")
    llave["oro_run_id"] = run_id
    llave = llave.drop(columns=["onet_descripcion_en"])
    salida.mkdir(parents=True, exist_ok=True)
    muestra.to_parquet(salida / "oro_muestra.parquet", index=False)
    llave.to_parquet(salida / "oro_llave.parquet", index=False)
    for rev, df in fichas.items():
        escribir_csv(df, salida / "oro_revision" / f"revisor_{rev}.csv")
    manifiesto = {
        "oro_run_id": run_id, "fecha_utc": datetime.now(timezone.utc).isoformat(), "seed": cfg["meta"]["seed"],
        "hash_config_oro": sha256(config), "match_run_ids": run_ids, "hash_match_candidatos": sha256(cand_path),
        "n_principal": int((muestra.muestra == "principal").sum()), "n_piloto": int((muestra.muestra == "piloto").sum()),
        "n_candidatos_llave": int(len(llave)), "estado_parametros": cfg["meta"]["estado_parametros"],
        "estado_validacion": "sin_validar",
    }
    (salida / "oro_manifiesto.json").write_text(json.dumps(manifiesto, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifiesto


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", type=Path, default=PROC)
    a = ap.parse_args()
    print(json.dumps(main(a.salida), indent=2, ensure_ascii=False))
