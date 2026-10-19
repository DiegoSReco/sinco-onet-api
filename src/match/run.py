"""Metodo A1: SINCO 2019 (es) -> O*NET-SOC (en) con embeddings multilingues y probabilidad F-O agregada.

Uso:  .venv\\Scripts\\python -m src.match.run [--salida DIR] [--solo-modelo NOMBRE] [--local]
Variables: HF_HOME (cache de pesos fuera de git; por defecto ~/hf_cache).
Todo resultado queda marcado estado_validacion = sin_validar. No calcula exposicion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("HF_HOME", str(Path.home() / "hf_cache"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pyarrow.parquet as pq  # noqa: E402

from . import config as C  # noqa: E402
from . import embed, pfo, retrieve, schemas, texts  # noqa: E402

TABLAS = ["sinco", "sinco_descripcion", "sinco_funciones", "sinco_ocupaciones_ejemplo", "sinco_incluye_excluye",
          "onet_ocupaciones", "tareas_onet_en", "frey_osborne_probabilidades", "puente_onet_soc2019_soc2010"]
RESIDUAL_TITULO = r"no especificad|^otros\b|^otras\b|n\.c\.p"


def sha256_archivo(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def leer_insumos(proc: Path) -> tuple[dict, dict]:
    t = {n: pd.read_parquet(proc / f"{n}.parquet") for n in TABLAS}
    h = {n: sha256_archivo(proc / f"{n}.parquet") for n in TABLAS}
    return t, h


def _huella(nombre: str, m: dict, seed: int, textos_s: list, textos_o: list) -> str:
    h = hashlib.sha256()
    for x in (nombre, m["hf_id"], m["revision"], str(m["max_length"]), str(seed), *textos_s, "||", *textos_o):
        h.update(x.encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()


def correr_modelo(nombre: str, cfg: dict, t: dict, local: bool, vec_dir: Path, reusar: bool) -> dict:
    m = cfg["modelos"][nombre]
    seed = cfg["meta"]["seed"]
    embed.fijar_semilla(seed)
    model = embed.cargar_modelo(m["hf_id"], m["revision"], m["max_length"], local_only=local)
    tok = model.tokenizer
    d_s = texts.documentos_sinco(t, tok, m["max_length"], m["prefijo_consulta"], cfg["texto"]["max_ocupaciones_ejemplo"],
                                 cfg["texto"]["prioridad_truncamiento"])
    d_o = texts.documentos_onet(t["onet_ocupaciones"], tok, m["max_length"], m["prefijo_documento"])
    huella = _huella(nombre, m, seed, d_s["texto"].tolist(), d_o["texto"].tolist())
    meta_p = vec_dir / f"{nombre}_meta.json"
    desde_cache = False
    if reusar and meta_p.exists() and json.loads(meta_p.read_text())["huella"] == huella             and (vec_dir / f"{nombre}_sinco.npy").exists() and (vec_dir / f"{nombre}_onet.npy").exists():
        q, d = np.load(vec_dir / f"{nombre}_sinco.npy"), np.load(vec_dir / f"{nombre}_onet.npy")
        seg = json.loads(meta_p.read_text())["segundos"]
        desde_cache = True
    else:
        t0 = time.time()
        q = embed.codificar(model, d_s["texto"].tolist())
        d = embed.codificar(model, d_o["texto"].tolist())
        seg = time.time() - t0
        np.save(vec_dir / f"{nombre}_sinco.npy", q)
        np.save(vec_dir / f"{nombre}_onet.npy", d)
        meta_p.write_text(json.dumps({"huella": huella, "segundos": seg}))
    sim = retrieve.similitud(q, d)
    return {"nombre": nombre, "m": m, "q": q, "d": d, "sim": sim, "docs_s": d_s, "docs_o": d_o, "seg": seg, "desde_cache": desde_cache,
            "dispositivo": str(model.device), "dtype": str(next(model.parameters()).dtype)}


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", default=str(C.PROC))
    ap.add_argument("--solo-modelo", default=None)
    ap.add_argument("--reusar-vectores", action="store_true",
                    help="reutiliza vectores de match_vectores/ si la huella (modelo, revision, textos, semilla) coincide")
    ap.add_argument("--local", action="store_true", help="no consultar la red (solo cache local)")
    a = ap.parse_args(argv)
    out = Path(a.salida)
    out.mkdir(parents=True, exist_ok=True)
    vec_dir = out / "match_vectores"
    vec_dir.mkdir(exist_ok=True)

    cfg = C.cargar()
    hcfg = C.hash_config()
    t, h_in = leer_insumos(C.PROC)
    fecha = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    run_id = f"match-A1-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}-{hcfg[:8]}"
    modelos = [a.solo_modelo] if a.solo_modelo else list(cfg["modelos"])
    principal = cfg["meta"]["modelo_principal"]
    rec = cfg["recuperacion"]

    sinco_s = t["sinco"].set_index("sinco_code")["titulo"]
    onet_codes_all = sorted(t["onet_ocupaciones"]["onet_soc_code"])
    puente = pfo.mapa_puente(t["puente_onet_soc2019_soc2010"])
    fo = dict(zip(t["frey_osborne_probabilidades"]["soc_2010"],
                  t["frey_osborne_probabilidades"]["probabilidad_automatizacion_fo"]))

    res_modelos, top_all, resumen_all, pfo_all, corridas = {}, [], [], [], []
    for nombre in modelos:
        r = correr_modelo(nombre, cfg, t, a.local, vec_dir, a.reusar_vectores)
        m = r["m"]
        sinco_codes = r["docs_s"]["sinco_code"].tolist()
        onet_codes = r["docs_o"]["onet_soc_code"].tolist()
        assert onet_codes == onet_codes_all
        top, res, umb = retrieve.candidatos(r["sim"], sinco_codes, onet_codes, rec["k"], m["delta"],
                                            rec["rango_max_conjunto"], rec["cuantil_baja_sim_top1"],
                                            rec["cuantil_bajo_margen"], rec["cuantil_sin_coincidencia"])
        r.update(top=top, res=res, umb=umb)
        res_modelos[nombre] = r
        top.insert(0, "modelo", nombre)
        top.insert(0, "run_id", run_id)
        top_all.append(top)

        # resumen por SINCO (+ flags de texto y residuales)
        ds = r["docs_s"].set_index("sinco_code")
        res = res.copy()
        res.insert(0, "modelo", nombre)
        res.insert(0, "run_id", run_id)
        res["n_tokens_texto"] = res["sinco_code"].map(ds["n_tokens"])
        res["texto_truncado"] = res["sinco_code"].map(ds["truncado"])
        res["campos_truncados"] = res["sinco_code"].map(ds["campos_truncados"])
        res["residual_sin_funciones"] = ~res["sinco_code"].map(ds["tiene_funciones"])
        tit = res["sinco_code"].map(sinco_s)
        res["residual_por_titulo"] = tit.str.contains(RESIDUAL_TITULO, case=False, regex=True)
        res["estado_validacion"] = "sin_validar"
        resumen_all.append(res)

        # probabilidad F-O (conjunto S por SINCO)
        s_set = top[top["en_conjunto"]]
        filas = []
        for code, g in s_set.groupby("sinco_code", sort=True):
            g = g.sort_values("rango")
            ag = pfo.agregar_sinco(g["similitud"].to_numpy(), g["onet_soc_code"].tolist(), m["tau"], puente, fo)
            filas.append({"sinco_code": code, "top1_onet_soc_code": g["onet_soc_code"].iloc[0], **ag})
        pf = pd.DataFrame(filas).merge(res[["sinco_code", "match_status", "baja_confianza", "sim_top1", "margen",
                                            "residual_sin_funciones", "residual_por_titulo"]], on="sinco_code")
        sin = pf["match_status"].eq("sin_coincidencia")
        P = pfo.ETIQUETA
        pf["probabilidad_automatizacion_fo_ponderada_sin_filtro"] = pf["p_ponderada"]
        for col, src in [("probabilidad_automatizacion_fo", "p_ponderada"),
                         ("probabilidad_automatizacion_fo_media_uniforme", "p_media"),
                         ("probabilidad_automatizacion_fo_min", "p_min"),
                         ("probabilidad_automatizacion_fo_max", "p_max"),
                         ("probabilidad_automatizacion_fo_top1", "p_top1")]:
            pf[col] = pf[src].where(~sin)
        pf["motivo_na"] = np.where(sin, "sin_coincidencia", np.where(pf["p_ponderada"].isna(), "sin_probabilidad_fo", None))
        pf["n_sinco_mismo_top1_soc"] = pf.groupby("top1_socs")["sinco_code"].transform("count")
        pf.insert(0, "titulo", pf["sinco_code"].map(sinco_s))
        pf.insert(0, "es_modelo_principal", nombre == principal)
        pf.insert(0, "modelo", nombre)
        pf.insert(0, "run_id", run_id)
        pf["estado_validacion"] = "sin_validar"
        pf["etiqueta"] = P
        pfo_all.append(pf)

        corridas.append({
            "run_id": run_id, "modelo": nombre, "hf_id": m["hf_id"], "revision_modelo": m["revision"], "fecha": fecha,
            "metodo": cfg["meta"]["metodo"], "text_template_version": cfg["meta"]["text_template_version"],
            "seed": cfg["meta"]["seed"], "normalizacion": "L2", "max_length": m["max_length"],
            "n_truncados_sinco": int(r["docs_s"]["truncado"].sum()), "n_truncados_onet": int(r["docs_o"]["truncado"].sum()),
            "dispositivo": r["dispositivo"], "dtype": r["dtype"],
            "hash_matriz_sinco": embed.hash_matriz(r["q"]), "hash_matriz_onet": embed.hash_matriz(r["d"]),
            "hash_matriz_similitud": embed.hash_matriz(r["sim"]), "hash_config": hcfg,
            "parametros": json.dumps({"k": rec["k"], "delta": m["delta"], "tau": m["tau"],
                                      "rango_max_conjunto": rec["rango_max_conjunto"], "umbrales_calculados": umb,
                                      "cuantiles": {k: v for k, v in rec.items() if k.startswith("cuantil")}},
                                     sort_keys=True),
            "estado_parametros": cfg["meta"]["estado_parametros"], "estado_validacion": "sin_validar",
            "hashes_insumos": json.dumps(h_in, sort_keys=True), "versiones_librerias": json.dumps(embed.versiones(), sort_keys=True),
            "segundos_embedding": round(r["seg"], 1), "vectores_desde_cache": r["desde_cache"], "n_sinco": len(sinco_codes), "n_onet": len(onet_codes),
        })
        print(f"[{nombre}] listo: {r['seg']:.0f} s de embedding", flush=True)

    top_df = pd.concat(top_all, ignore_index=True)
    resumen_df = pd.concat(resumen_all, ignore_index=True)
    pfo_df = pd.concat(pfo_all, ignore_index=True)
    # columnas de trabajo internas fuera de la tabla final
    pfo_df = pfo_df.drop(columns=["p_ponderada", "p_media", "p_min", "p_max", "p_top1"])
    corr_df = pd.DataFrame(corridas)

    # crosswalk.parquet: modelo principal, conjunto S, sin columnas de score/probabilidad
    sinco_codes_set, onet_codes_set = set(t["sinco"]["sinco_code"]), set(t["onet_ocupaciones"]["onet_soc_code"])
    cw = None
    if principal in res_modelos:
        rp = res_modelos[principal]
        s = rp["top"][rp["top"]["en_conjunto"]].copy()
        st = rp["res"].set_index("sinco_code")
        cw = s[["sinco_code", "onet_soc_code", "rango", "similitud"]].copy()
        cw["margen"] = cw["sinco_code"].map(st["margen"])
        cw["match_status"] = cw["sinco_code"].map(st["match_status"])
        cw["baja_confianza"] = cw["sinco_code"].map(st["baja_confianza"])
        cw["tipo_relacion"] = retrieve.tipo_relacion(cw)
        cw["fuente"] = f"{cfg['meta']['fuente_crosswalk']}_{principal}"
        cw["estado_validacion"] = "sin_validar"
        cw["run_id"] = run_id
        cw["modelo"] = principal
        alts = [n for n in res_modelos if n != principal]
        cw["similitud_alt"], cw["rango_alt"], cw["modelo_alt"] = np.nan, pd.NA, None
        if alts:
            ra = res_modelos[alts[0]]
            si = {c: i for i, c in enumerate(res_modelos[principal]["docs_s"]["sinco_code"])}
            oi = {c: i for i, c in enumerate(onet_codes_all)}
            simA = ra["sim"]
            vals = [simA[si[a_], oi[b_]] for a_, b_ in zip(cw["sinco_code"], cw["onet_soc_code"])]
            cw["similitud_alt"] = vals
            cw["rango_alt"] = [int((simA[si[a_]] > simA[si[a_], oi[b_]]).sum() + 1) for a_, b_ in zip(cw["sinco_code"], cw["onet_soc_code"])]
            cw["modelo_alt"] = alts[0]
        cw["notas"] = ("A1 " + principal + "; rango=" + cw["rango"].astype(str) + "; similitud=" + cw["similitud"].round(4).astype(str)
                       + "; margen=" + cw["margen"].round(4).astype(str) + "; estado=" + cw["match_status"]
                       + "; sin_validar; parametros provisionales sin calibrar; no es correspondencia oficial")
        cw = cw.sort_values(["sinco_code", "rango"]).reset_index(drop=True)

    # validacion de esquema ANTES de escribir (regla 5)
    schemas.validar_pfo(pfo_df, sinco_codes_set)
    schemas.validar_corridas(corr_df)
    tabla_cw = schemas.validar_crosswalk(cw, sinco_codes_set, onet_codes_set) if cw is not None else None

    if tabla_cw is not None:
        pq.write_table(tabla_cw, out / "crosswalk.parquet")
    top_df.to_parquet(out / "match_candidatos.parquet", index=False)
    resumen_df.to_parquet(out / "match_sinco_resumen.parquet", index=False)
    pfo_df.to_parquet(out / "sinco_probabilidad_fo.parquet", index=False)
    corr_df.to_parquet(out / "match_corridas.parquet", index=False)

    # cobertura (cifras que usara el reporte; todo sale de este script)
    fo_en_puente = {s for ss in puente.values() for s in ss}
    cob = {"run_id": run_id, "fecha": fecha,
           "fo_codigos_total": len(fo), "fo_codigos_fuera_del_puente": sorted(set(fo) - fo_en_puente),
           "puente_o_net_2019_con_varios_soc2010": sorted(k for k, v in puente.items() if len(v) > 1),
           "onet_sin_puente": sorted(set(onet_codes_all) - set(puente)),
           "por_modelo": {}}
    for nombre in res_modelos:
        p = pfo_df[pfo_df["modelo"] == nombre]
        cob["por_modelo"][nombre] = {
            "n_sinco": int(len(p)),
            "con_p_fo_principal": int(p["probabilidad_automatizacion_fo"].notna().sum()),
            "na_total": int(p["probabilidad_automatizacion_fo"].isna().sum()),
            "motivo_na": p["motivo_na"].fillna("").value_counts().to_dict(),
            "match_status": p["match_status"].value_counts().to_dict(),
            "cobertura_fo": p["cobertura_fo"].value_counts().to_dict(),
            "baja_confianza": int(p["baja_confianza"].sum()),
            "bandera_multi_soc2010": int(p["bandera_multi_soc2010"].sum()),
            "bandera_sin_puente": int(p["bandera_sin_puente"].sum()),
            "bandera_soc_sin_fo": int(p["bandera_soc_sin_fo"].sum()),
            "residual_sin_funciones": int(p["residual_sin_funciones"].sum()),
            "residual_por_titulo": int(p["residual_por_titulo"].sum()),
            "umbrales": res_modelos[nombre]["umb"],
            "sim_top1_cuantiles": {str(q): float(np.quantile(res_modelos[nombre]["res"]["sim_top1"], q)) for q in (0, .1, .25, .5, .75, .9, 1)},
            "margen_cuantiles": {str(q): float(np.quantile(res_modelos[nombre]["res"]["margen"], q)) for q in (0, .1, .25, .5, .75, .9, 1)},
            "n_conjunto_distribucion": res_modelos[nombre]["res"]["n_conjunto"].value_counts().sort_index().to_dict(),
        }
    if len(res_modelos) == 2:
        a_, b_ = list(res_modelos)
        ta = res_modelos[a_]["top"].query("rango==1").set_index("sinco_code")["onet_soc_code"]
        tb = res_modelos[b_]["top"].query("rango==1").set_index("sinco_code")["onet_soc_code"]
        cob["acuerdo_top1_entre_modelos"] = float((ta == tb.reindex(ta.index)).mean())
        cob["acuerdo_top1_grupo_soc_2dig"] = float((ta.str[:2] == tb.reindex(ta.index).str[:2]).mean())
        pa_ = pfo_df[pfo_df.modelo == a_].set_index("sinco_code")["probabilidad_automatizacion_fo"]
        pb_ = pfo_df[pfo_df.modelo == b_].set_index("sinco_code")["probabilidad_automatizacion_fo"]
        j = pd.concat([pa_, pb_], axis=1, keys=["a", "b"]).dropna()
        cob["spearman_p_fo_entre_modelos"] = float(j["a"].corr(j["b"], method="spearman"))
        cob["n_par_p_fo_entre_modelos"] = int(len(j))
    (out / "match_cobertura.json").write_text(json.dumps(cob, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(json.dumps(cob, indent=2, ensure_ascii=False, default=str)[:6000])
    return cob


if __name__ == "__main__":
    main()
