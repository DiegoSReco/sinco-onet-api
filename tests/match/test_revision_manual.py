"""Pruebas de src/match/revision_manual.py con tablas sinteticas (no tocan data/processed ni cargan modelos)."""
import hashlib
import json
import re
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pytest

from src.match import pfo, retrieve, revision_manual as RM, schemas

ONET = ["11-1011.00", "13-1111.00", "17-2051.00", "29-1141.00", "47-2061.00", "15-1252.00", "11-1011.03", "17-2051.01"]
SINCOS = ["1111", "1112", "1113", "1114", "2111", "2112"]
STATUS = {"1111": "baja_confianza", "1112": "sin_coincidencia", "1113": "ok", "1114": "baja_confianza",
          "2111": "sin_coincidencia", "2112": "baja_confianza"}
FO = {"11-1011": 0.2, "13-1111": 0.6, "17-2051": 0.1, "29-1141": 0.05, "47-2061": 0.8, "47-2062": 0.4}
PUENTE = {"11-1011.00": ["11-1011"], "11-1011.03": ["11-1011"], "13-1111.00": ["13-1111"], "17-2051.00": ["17-2051"],
          "17-2051.01": ["17-2051"], "29-1141.00": ["29-1141"], "47-2061.00": ["47-2061", "47-2062"]}   # 15-1252.00 sin puente
P, A = "bge-m3", "multilingual-e5-large"
TAU = 0.05


def _orden(i, modelo):
    r = ONET[i % 8:] + ONET[:i % 8]
    return r if modelo == P else list(reversed(ONET[(i + 3) % 8:] + ONET[:(i + 3) % 8]))


def _h(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


@pytest.fixture()
def proc(tmp_path):
    d = tmp_path / "processed"
    d.mkdir()
    sinco = pd.DataFrame(
        [{"sinco_code": "1", "nivel": "division", "titulo": "Directores", "division": "1"},
         {"sinco_code": "2", "nivel": "division", "titulo": "Profesionistas", "division": "2"}] +
        [{"sinco_code": c, "nivel": "grupo_unitario", "titulo": f"Grupo {c}", "division": c[0]} for c in SINCOS])
    sinco.to_parquet(d / "sinco.parquet", index=False)
    pd.DataFrame({"sinco_code": SINCOS, "descripcion": [f"Descripcion del grupo {c}.\nSegunda linea." for c in SINCOS]}
                 ).to_parquet(d / "sinco_descripcion.parquet", index=False)
    pd.DataFrame([{"sinco_code": c, "orden": k, "funcion": f"Funcion {k} de {c}  con   espacios"} for c in SINCOS for k in (1, 2)]
                 ).to_parquet(d / "sinco_funciones.parquet", index=False)
    pd.DataFrame([{"sinco_code": c, "orden": 1, "ocupacion": f"Ocupacion de {c}."} for c in SINCOS]
                 ).to_parquet(d / "sinco_ocupaciones_ejemplo.parquet", index=False)
    pd.DataFrame({"onet_soc_code": ONET, "titulo_en": [f"Title {c}" for c in ONET],
                  "descripcion_en": [f"Desc\n{c}" for c in ONET]}).to_parquet(d / "onet_ocupaciones.parquet", index=False)
    pd.DataFrame({"soc_2010": list(FO), "probabilidad_automatizacion_fo": list(FO.values())}
                 ).to_parquet(d / "frey_osborne_probabilidades.parquet", index=False)
    pd.DataFrame([{"onet_soc_2019_code": o, "soc_2010": s} for o, ss in PUENTE.items() for s in ss]
                 ).to_parquet(d / "puente_onet_soc2019_soc2010.parquet", index=False)
    pd.DataFrame({"sinco_code": ["1111", "2111"]}).to_parquet(d / "oro_muestra.parquet", index=False)

    cand, res = [], []
    for i, c in enumerate(SINCOS):
        for m in (P, A):
            orden = _orden(i, m)
            sims = [0.9 - 0.04 * r - (0.01 * i if m == P else 0) for r in range(8)]
            for r, (oc, s) in enumerate(zip(orden, sims), start=1):
                cand.append({"run_id": "match-A1-x", "modelo": m, "sinco_code": c, "onet_soc_code": oc, "rango": r, "similitud": s,
                             "dif_con_top1": sims[0] - s, "en_conjunto": r <= 2, "margen_sinco": sims[0] - sims[1]})
            st = STATUS[c] if m == P else "ok"
            res.append({"run_id": "match-A1-x", "modelo": m, "sinco_code": c, "sim_top1": sims[0], "sim_top2": sims[1],
                        "margen": sims[0] - sims[1], "n_conjunto": 2, "bandera_sim_top1_baja": st != "ok",
                        "bandera_margen_bajo": False, "baja_confianza": st != "ok", "match_status": st, "n_tokens_texto": 10,
                        "texto_truncado": False, "campos_truncados": "", "residual_sin_funciones": False,
                        "residual_por_titulo": False, "estado_validacion": "sin_validar"})
    cand, res = pd.DataFrame(cand), pd.DataFrame(res)
    cand.to_parquet(d / "match_candidatos.parquet", index=False)
    res.to_parquet(d / "match_sinco_resumen.parquet", index=False)

    s = cand[(cand.modelo == P) & cand.en_conjunto]
    st = res[res.modelo == P].set_index("sinco_code")
    sa = cand[cand.modelo == A].set_index(["sinco_code", "onet_soc_code"])
    cw = s[["sinco_code", "onet_soc_code", "rango", "similitud"]].copy()
    cw["margen"] = cw["sinco_code"].map(st["margen"])
    cw["match_status"] = cw["sinco_code"].map(st["match_status"])
    cw["baja_confianza"] = cw["sinco_code"].map(st["baja_confianza"])
    cw["tipo_relacion"] = retrieve.tipo_relacion(cw)
    cw["fuente"], cw["estado_validacion"], cw["run_id"], cw["modelo"] = "semiautomatico_embeddings_A1_bge-m3", "sin_validar", "match-A1-x", P
    cw["similitud_alt"] = [sa.loc[(a, b), "similitud"] for a, b in zip(cw.sinco_code, cw.onet_soc_code)]
    cw["rango_alt"] = [int(sa.loc[(a, b), "rango"]) for a, b in zip(cw.sinco_code, cw.onet_soc_code)]
    cw["modelo_alt"] = A
    cw["notas"] = "auto"
    cw = cw.sort_values(["sinco_code", "rango"]).reset_index(drop=True)
    pq.write_table(schemas.validar_crosswalk(cw, set(SINCOS), set(ONET)), d / "crosswalk.parquet")

    puente = {k: sorted(v) for k, v in PUENTE.items()}
    filas = []
    for m in (P, A):
        for c in SINCOS:
            g = cand[(cand.modelo == m) & (cand.sinco_code == c) & cand.en_conjunto].sort_values("rango")
            ag = pfo.agregar_sinco(g["similitud"].to_numpy(), g["onet_soc_code"].tolist(), TAU, puente, FO)
            sin = STATUS[c] == "sin_coincidencia" and m == P
            row = {"run_id": "match-A1-x", "modelo": m, "es_modelo_principal": m == P, "titulo": f"Grupo {c}", "sinco_code": c,
                   "top1_onet_soc_code": g["onet_soc_code"].iloc[0],
                   "probabilidad_automatizacion_fo_ponderada_sin_filtro": ag["p_ponderada"]}
            for col, k in [("probabilidad_automatizacion_fo", "p_ponderada"), ("probabilidad_automatizacion_fo_media_uniforme", "p_media"),
                           ("probabilidad_automatizacion_fo_min", "p_min"), ("probabilidad_automatizacion_fo_max", "p_max"),
                           ("probabilidad_automatizacion_fo_top1", "p_top1")]:
                row[col] = None if sin or pd.isna(ag[k]) else ag[k]
            row["motivo_na"] = "sin_coincidencia" if sin else (None if not pd.isna(ag["p_ponderada"]) else "sin_probabilidad_fo")
            for k in ("n_candidatos", "n_soc2010", "n_soc2010_con_fo", "cobertura_peso_fo", "cobertura_fo", "bandera_multi_soc2010",
                      "bandera_sin_puente", "onet_sin_puente", "bandera_soc_sin_fo", "top1_socs"):
                row[k] = ag[k]
            rr = res[(res.modelo == m) & (res.sinco_code == c)].iloc[0]
            row.update(match_status=rr.match_status, baja_confianza=bool(rr.baja_confianza), sim_top1=rr.sim_top1, margen=rr.margen,
                       residual_sin_funciones=False, residual_por_titulo=False, estado_validacion="sin_validar",
                       etiqueta=pfo.ETIQUETA)
            filas.append(row)
    pf = pd.DataFrame(filas)
    pf["n_sinco_mismo_top1_soc"] = pf.groupby(["modelo", "top1_socs"])["sinco_code"].transform("count")
    schemas.validar_pfo(pf, set(SINCOS))
    pf.to_parquet(d / "sinco_probabilidad_fo.parquet", index=False)

    base = {"hf_id": "x/y", "revision_modelo": "a" * 40, "fecha": "2026-10-19T00:00:00Z", "metodo": "A1", "text_template_version": "t",
            "seed": 1, "normalizacion": "L2", "max_length": 8, "n_truncados_sinco": 0, "n_truncados_onet": 0, "dispositivo": "cpu",
            "dtype": "f32", "hash_matriz_sinco": "b" * 64, "hash_matriz_onet": "b" * 64, "hash_matriz_similitud": "b" * 64,
            "hash_config": "c" * 64, "parametros": "{}", "estado_parametros": "p", "estado_validacion": "sin_validar",
            "hashes_insumos": "{}", "versiones_librerias": "{}", "segundos_embedding": 1.0, "vectores_desde_cache": False,
            "n_sinco": 6, "n_onet": 8}
    pd.DataFrame([{"run_id": "match-A1-x", "modelo": m, **base} for m in (P, A)]).to_parquet(d / "match_corridas.parquet", index=False)
    return d


def _exportar(proc):
    out = proc / "revision_manual"
    meta = RM.exportar(proc, out)
    return out, meta


def _llenar(csv_in: Path, csv_out: Path, cambios: dict) -> Path:
    df = RM.leer_csv(csv_in)
    for code, campos in cambios.items():
        for k, v in campos.items():
            df.loc[df["sinco_code"] == code, k] = v
    df.to_csv(csv_out, index=False, encoding="utf-8-sig")
    return csv_out


def _aplicar(proc, csv, tmp_path, fecha="2026-10-20", **kw):
    return RM.aplicar(csv, proc, issues=tmp_path / "issues", revision_dir=proc / "revision_manual", fecha=fecha, **kw)


def _estado(proc):
    return {n: _h(proc / f"{n}.parquet") for n in ("crosswalk", "sinco_probabilidad_fo", "match_corridas", "oro_muestra")}


DECISIONES = {
    "1111": {"decision": "ACEPTAR_RANGO1", "revisor": "Ana", "confianza_revisor": "alta"},
    "1112": {"decision": "ACEPTAR_RANGO2", "revisor": "Ana"},
    "1114": {"decision": "ACEPTAR_AMBOS", "revisor": "Ana"},
    "2111": {"decision": "OTRO", "onet_manual_1": "29-1141.00", "onet_manual_2": "13-1111.00", "peso_1": "3", "peso_2": "1", "revisor": "Ana"},
    "2112": {"decision": "NINGUNO", "revisor": "Ana", "comentarios": "sin equivalente"},
}


# ------------------------------------------------------------------ exportar
def test_exportar_columnas_y_conteo(proc):
    out, meta = _exportar(proc)
    assert meta["n_grupos"] == 5 and meta["n_por_estado"] == {"baja_confianza": 3, "sin_coincidencia": 2}
    assert open(out / "revision_manual.csv", "rb").read(3) == b"\xef\xbb\xbf"
    df = pd.read_csv(out / "revision_manual.csv", encoding="utf-8-sig", dtype=str, keep_default_na=False)
    assert list(df.columns) == RM.COLUMNAS and set(df["sinco_code"]) == set(SINCOS) - {"1113"}
    assert (df[RM.COLS_REVISOR] == "").all().all()
    assert not [c for c in df.columns if re.search(r"prob|expos|frey|osborne", c, re.I)]
    r = df[df.sinco_code == "1111"].iloc[0]
    assert r["auto_rango1"] == "11-1011.00 | Title 11-1011.00" and r["auto_rango2"] == "13-1111.00 | Title 13-1111.00"
    cands = [r[c] for c in RM.COLS_CAND if r[c]]
    codes = [c.split(" | ")[0] for c in cands]
    assert len(codes) == len(set(codes)) and cands[0].startswith("11-1011.00 | Title 11-1011.00 | bge 0.900 (#1) | e5 ")
    assert all(len(c.split(" | ")) == 4 for c in cands)
    assert "\n" not in r["descripcion"] and "  " not in r["funciones"] and " | " in r["funciones"]
    cat = pd.read_csv(out / "onet_catalogo_consulta.csv", encoding="utf-8-sig")
    assert list(cat.columns) == ["codigo_onet", "titulo_en", "descripcion_en"] and len(cat) == 8
    txt = (out / "LEEME_revision_manual.md").read_text(encoding="utf-8")
    assert "NO es la muestra de oro" in txt and "No hace falta consultar probabilidades" in txt
    m = json.loads((out / "exportacion_meta.json").read_text(encoding="utf-8"))
    assert m["hashes_tablas_entrada"]["match_candidatos"] == _h(proc / "match_candidatos.parquet") and m["n_grupos"] == 5


def test_exportar_recorta_textos(proc):
    cfg = RM.cargar_config()
    cfg["exportacion"] = {**cfg["exportacion"], "max_chars_funciones": 30}
    out = proc / "r2"
    RM.exportar(proc, out, cfg_rev=cfg)
    df = pd.read_csv(out / "revision_manual.csv", encoding="utf-8-sig", dtype=str, keep_default_na=False)
    assert df["funciones"].str.len().max() <= 30 and df["funciones"].str.endswith("...").all()


# ------------------------------------------------------------------ aplicar: cada decision
def test_aplicar_cada_decision(proc, tmp_path):
    out, _ = _exportar(proc)
    old_cw, old_pf = pd.read_parquet(proc / "crosswalk.parquet"), pd.read_parquet(proc / "sinco_probabilidad_fo.parquet")
    csv = _llenar(out / "revision_manual.csv", tmp_path / "lleno.csv", DECISIONES)
    assert _aplicar(proc, csv, tmp_path) == 0
    cw, pf = pd.read_parquet(proc / "crosswalk.parquet"), pd.read_parquet(proc / "sinco_probabilidad_fo.parquet")
    par = lambda c: cw[cw.sinco_code == c].sort_values("onet_soc_code")["onet_soc_code"].tolist()
    assert par("1111") == ["11-1011.00"] and par("1112") == ["17-2051.00"]
    assert par("1114") == ["29-1141.00", "47-2061.00"] and par("2111") == ["13-1111.00", "29-1141.00"] and par("2112") == []
    man = cw[cw.sinco_code.isin(DECISIONES)]
    assert (man.fuente == "manual").all() and (man.estado_validacion == "revision_manual_1_revisor").all()
    assert man.run_id.str.match(r"^manual-2026-10-20-[0-9a-f]{8}$").all() and man.run_id.nunique() == 1
    # conserva rango/similitud automaticos; NA fuera del top-2
    f = cw[(cw.sinco_code == "1112")].iloc[0]
    assert f.rango == 2 and f.rango_alt >= 1 and not pd.isna(f.similitud)
    o = cw[(cw.sinco_code == "2111") & (cw.onet_soc_code == "13-1111.00")].iloc[0]
    assert pd.isna(o.rango) or o.rango in (1, 2)
    # no revisados: identicos (1113); y el otro modelo no cambia
    a = cw[cw.sinco_code == "1113"].drop(columns=["tipo_relacion"]).reset_index(drop=True)
    b = old_cw[old_cw.sinco_code == "1113"].drop(columns=["tipo_relacion"]).reset_index(drop=True)
    pd.testing.assert_frame_equal(a, b, check_dtype=False)
    e5 = lambda d: d[d.modelo == A].reset_index(drop=True)
    pd.testing.assert_frame_equal(e5(pf), e5(old_pf))
    pm = pf[pf.modelo == P].set_index("sinco_code")
    col = "probabilidad_automatizacion_fo"
    assert pm.loc["1111", col] == pytest.approx(0.2)                      # solo rango 1: 11-1011
    assert pm.loc["1112", col] == pytest.approx(0.1)                      # sin_coincidencia revisado => ya no es NA
    assert pm.loc["1114", col] == pytest.approx(0.5 * 0.05 + 0.5 * (0.5 * 0.8 + 0.5 * 0.4))   # uniforme, 47-2061 reparte 50/50
    assert pm.loc["2111", col] == pytest.approx(0.75 * 0.05 + 0.25 * 0.6)  # pesos 3:1 del revisor, orden dado
    assert pm.loc["2112", "motivo_na"] == "sin_equivalente_onet_revision_manual" and pd.isna(pm.loc["2112", col])
    assert pm.loc["2112", "n_candidatos"] == 0 and pm.loc["2112", "cobertura_fo"] == "ninguna"
    assert (pm.loc[list(DECISIONES), "estado_validacion"] == "revision_manual_1_revisor").all()
    assert pm.loc["1113", "estado_validacion"] == "sin_validar"
    assert pm.loc["1113", col] == old_pf[(old_pf.modelo == P) & (old_pf.sinco_code == "1113")][col].iloc[0]
    assert pm.loc["2111", "top1_onet_soc_code"] == "29-1141.00"


def test_aplicar_ambos_con_pesos_y_sin_peso(proc, tmp_path):
    out, _ = _exportar(proc)
    csv = _llenar(out / "revision_manual.csv", tmp_path / "l.csv",
                  {"1114": {"decision": "ACEPTAR_AMBOS", "peso_1": "3", "peso_2": "1", "revisor": "Ana"}})
    assert _aplicar(proc, csv, tmp_path) == 0
    pm = pd.read_parquet(proc / "sinco_probabilidad_fo.parquet").query("modelo == @P").set_index("sinco_code")
    assert pm.loc["1114", "probabilidad_automatizacion_fo"] == pytest.approx(0.75 * 0.05 + 0.25 * 0.6)
    assert pm.loc["1114", "probabilidad_automatizacion_fo_media_uniforme"] == pytest.approx(0.325)
    cam = pd.read_parquet(proc / "revision_manual_cambios.parquet")
    assert bool(cam.iloc[0]["pesos_dados_por_revisor"]) and cam.iloc[0]["pesos_usados"] == "0.7500;0.2500"


# ------------------------------------------------------------------ validaciones: rechazo sin modificar nada
MALOS = [
    ("decision invalida", {"1111": {"decision": "SI", "revisor": "a"}}, "decision"),
    ("codigo manual inexistente", {"1111": {"decision": "OTRO", "onet_manual_1": "99-9999.00", "revisor": "a"}}, "onet_manual_1"),
    ("codigo sin .00 con sugerencia", {"1111": {"decision": "OTRO", "onet_manual_1": "13-1111", "revisor": "a"}}, "13-1111.00"),
    ("OTRO sin codigo", {"1111": {"decision": "OTRO", "revisor": "a"}}, "OTRO exige"),
    ("ACEPTAR con codigos", {"1111": {"decision": "ACEPTAR_AMBOS", "onet_manual_1": "13-1111.00", "revisor": "a"}}, "no admite"),
    ("NINGUNO con codigos", {"1111": {"decision": "NINGUNO", "onet_manual_2": "13-1111.00", "revisor": "a"}}, "no admite"),
    ("peso no numerico", {"1114": {"decision": "ACEPTAR_AMBOS", "peso_1": "x", "peso_2": "1", "revisor": "a"}}, "no es un numero"),
    ("peso cero", {"1114": {"decision": "ACEPTAR_AMBOS", "peso_1": "0", "peso_2": "1", "revisor": "a"}}, "> 0"),
    ("un solo peso", {"1114": {"decision": "ACEPTAR_AMBOS", "peso_1": "1", "revisor": "a"}}, "ambos pesos"),
    ("peso con un solo par", {"1111": {"decision": "ACEPTAR_RANGO1", "peso_1": "1", "revisor": "a"}}, "dos pares"),
    ("codigos repetidos", {"1111": {"decision": "OTRO", "onet_manual_1": "13-1111.00", "onet_manual_2": "13-1111.00", "revisor": "a"}}, "iguales"),
    ("confianza invalida", {"1111": {"decision": "ACEPTAR_RANGO1", "confianza_revisor": "muy", "revisor": "a"}}, "confianza_revisor"),
    ("sin revisor", {"1111": {"decision": "ACEPTAR_RANGO1"}}, "revisor"),
    ("datos sin decision", {"1111": {"onet_manual_1": "13-1111.00"}}, "decision vacia"),
]


@pytest.mark.parametrize("nombre,cambios,esperado", MALOS, ids=[m[0] for m in MALOS])
def test_validacion_rechaza_sin_modificar(proc, tmp_path, nombre, cambios, esperado):
    out, _ = _exportar(proc)
    # una fila valida junto a la mala: tampoco debe aplicarse (todo o nada)
    cambios = {**cambios, "1112": {"decision": "ACEPTAR_RANGO1", "revisor": "a"}}
    csv = _llenar(out / "revision_manual.csv", tmp_path / "malo.csv", cambios)
    antes = _estado(proc)
    n_arch = sorted(p.name for p in proc.iterdir())
    assert _aplicar(proc, csv, tmp_path) == 2
    assert _estado(proc) == antes and sorted(p.name for p in proc.iterdir()) == n_arch
    issue = (tmp_path / "issues" / "revision-manual-2026-10-20-validacion-fallida.md").read_text(encoding="utf-8")
    assert esperado in issue and "| fila_csv | sinco_code |" in issue
    assert not (proc / "revision_manual" / "previo_2026-10-20").exists()


def test_validacion_estructural(proc, tmp_path):
    out, _ = _exportar(proc)
    df = RM.leer_csv(out / "revision_manual.csv")
    antes = _estado(proc)
    # columna renombrada
    df.rename(columns={"decision": "decisión"}).to_csv(tmp_path / "a.csv", index=False, encoding="utf-8-sig")
    assert _aplicar(proc, tmp_path / "a.csv", tmp_path) == 2
    # sinco_code inexistente, duplicado y de un nivel no unitario
    d2 = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    d2.loc[1, "sinco_code"] = "9998"
    d2.loc[2, "sinco_code"] = "1"
    d2.to_csv(tmp_path / "b.csv", index=False, encoding="utf-8-sig")
    assert _aplicar(proc, tmp_path / "b.csv", tmp_path) == 2
    msg = (tmp_path / "issues" / "revision-manual-2026-10-20-validacion-fallida.md").read_text(encoding="utf-8")
    assert "no existe como grupo unitario" in msg and "duplicado" in msg
    assert _estado(proc) == antes


def test_duda_se_ignora_y_se_lista(proc, tmp_path, capsys):
    out, _ = _exportar(proc)
    antes = _estado(proc)
    csv = _llenar(out / "revision_manual.csv", tmp_path / "d.csv", {"1111": {"decision": "DUDA", "comentarios": "no se"}})
    assert _aplicar(proc, csv, tmp_path) == 0
    o = capsys.readouterr().out
    assert "DUDA (ignoradas): 1" in o and "DUDA 1111: no se" in o and _estado(proc) == antes
    csv = _llenar(out / "revision_manual.csv", tmp_path / "d2.csv",
                  {"1111": {"decision": "DUDA", "comentarios": "no se"}, "1112": {"decision": "ACEPTAR_RANGO1", "revisor": "Ana"}})
    assert _aplicar(proc, csv, tmp_path) == 0
    cw = pd.read_parquet(proc / "crosswalk.parquet")
    assert (cw[cw.sinco_code == "1111"].fuente != "manual").all() and (cw[cw.sinco_code == "1112"].fuente == "manual").all()
    res = json.loads(next((proc / "revision_manual").glob("aplicacion_*.json")).read_text(encoding="utf-8"))
    assert res["n_duda"] == 1 and res["duda"][0]["sinco_code"] == "1111"


# ------------------------------------------------------------------ auditoria
def test_auditoria_archivo_previo_cambios_y_corridas(proc, tmp_path):
    out, _ = _exportar(proc)
    prev_cw, prev_pf, prev_co, prev_oro = (proc / f"{n}.parquet" for n in ("crosswalk", "sinco_probabilidad_fo", "match_corridas", "oro_muestra"))
    h = {n: _h(p) for n, p in zip(("cw", "pf", "co", "oro"), (prev_cw, prev_pf, prev_co, prev_oro))}
    csv = _llenar(out / "revision_manual.csv", tmp_path / "l.csv", DECISIONES)
    assert _aplicar(proc, csv, tmp_path) == 0
    previo = proc / "revision_manual" / "previo_2026-10-20"
    assert _h(previo / "crosswalk.parquet") == h["cw"] and _h(previo / "sinco_probabilidad_fo.parquet") == h["pf"]
    assert _h(previo / "match_corridas.parquet") == h["co"]
    assert _h(proc / "oro_muestra.parquet") == h["oro"]                       # la muestra de oro no se toca
    assert not (proc / "oro_llave.parquet").exists()
    cam = pd.read_parquet(proc / "revision_manual_cambios.parquet")
    assert len(cam) == 5 and set(cam.sinco_code) == set(DECISIONES)
    for c in ("sinco_code", "decision", "pares_antes", "pares_despues", "probabilidad_antes", "probabilidad_despues", "revisor",
              "fecha_revision", "en_muestra_oro", "run_id"):
        assert c in cam.columns
    c = cam.set_index("sinco_code")
    assert bool(c.loc["1111", "en_muestra_oro"]) and bool(c.loc["2111", "en_muestra_oro"]) and not c.loc["1112", "en_muestra_oro"]
    assert c.loc["1112", "pares_antes"] == "13-1111.00; 17-2051.00" and c.loc["1112", "pares_despues"] == "17-2051.00"
    assert pd.isna(c.loc["1112", "probabilidad_antes"]) and c.loc["1112", "probabilidad_despues"] == pytest.approx(0.1)
    assert c.loc["1112", "motivo_na_antes"] == "sin_coincidencia"
    assert c.loc["2112", "motivo_na_despues"] == "sin_equivalente_onet_revision_manual"
    co = pd.read_parquet(proc / "match_corridas.parquet")
    assert len(co) == 3 and (co.run_id == c.run_id.iloc[0]).sum() == 1 and co.run_id.iloc[:2].eq("match-A1-x").all()
    assert co.iloc[-1].metodo == "revision_manual" and json.loads(co.iloc[-1].parametros)["n_aplicados"] == 5
    assert (proc / "revision_manual" / "aplicadas" / f"{c.run_id.iloc[0]}_revision_manual.csv").exists()


# ------------------------------------------------------------------ esquema final y API
def test_esquema_final_y_api(proc, tmp_path, monkeypatch):
    out, _ = _exportar(proc)
    csv = _llenar(out / "revision_manual.csv", tmp_path / "l.csv", DECISIONES)
    assert _aplicar(proc, csv, tmp_path) == 0
    assert pq.read_table(proc / "crosswalk.parquet").schema.equals(schemas.CROSSWALK_ARROW)
    cw, pf = pd.read_parquet(proc / "crosswalk.parquet"), pd.read_parquet(proc / "sinco_probabilidad_fo.parquet")
    onet = pd.read_parquet(proc / "onet_ocupaciones.parquet")
    schemas.validar_crosswalk(cw, set(SINCOS), set(onet.onet_soc_code))
    schemas.validar_pfo(pf, set(SINCOS))
    schemas.validar_corridas(pd.read_parquet(proc / "match_corridas.parquet"))
    assert not cw.duplicated(["sinco_code", "onet_soc_code"]).any()
    # tipo_relacion consistente con el grafo final
    assert (cw["tipo_relacion"] == retrieve.tipo_relacion(cw)).all()
    # la API acepta el crosswalk con filas manuales (fuente/estado nuevos no rompen el esquema ni los filtros)
    from src.api import service as S
    monkeypatch.setattr(S, "PROC", proc)
    S.limpiar_cache()
    try:
        e = S.crosswalk_estado()
        assert e["estado"] == "disponible", e["mensaje"]
        r = S.crosswalk(sinco_code="2111")
        assert {f["fuente"] for f in r["filas"]} == {"manual"} and {f["estado_validacion"] for f in r["filas"]} == {"revision_manual_1_revisor"}
        assert S.crosswalk(sinco_code="2112")["filas"] == []
    finally:
        S.limpiar_cache()


# ------------------------------------------------------------------ idempotencia
def test_idempotencia(proc, tmp_path):
    out, _ = _exportar(proc)
    csv = _llenar(out / "revision_manual.csv", tmp_path / "l.csv", DECISIONES)
    assert _aplicar(proc, csv, tmp_path) == 0
    despues = _estado(proc)
    cam1 = pd.read_parquet(proc / "revision_manual_cambios.parquet")
    previos = sorted(p.name for p in (proc / "revision_manual").glob("previo_*"))
    assert _aplicar(proc, csv, tmp_path) == 0                                  # mismo dia
    assert _aplicar(proc, csv, tmp_path, fecha="2026-10-21") == 0              # otro dia, mismo archivo
    assert _estado(proc) == despues
    pd.testing.assert_frame_equal(pd.read_parquet(proc / "revision_manual_cambios.parquet"), cam1)
    assert sorted(p.name for p in (proc / "revision_manual").glob("previo_*")) == previos
    cw = pd.read_parquet(proc / "crosswalk.parquet")
    assert not cw.duplicated(["sinco_code", "onet_soc_code"]).any()
    assert len(cw[cw.sinco_code == "1113"]) == 2


def test_segunda_revision_reemplaza_la_primera(proc, tmp_path):
    out, _ = _exportar(proc)
    c1 = _llenar(out / "revision_manual.csv", tmp_path / "1.csv", {"1111": {"decision": "ACEPTAR_RANGO1", "revisor": "Ana"}})
    assert _aplicar(proc, c1, tmp_path) == 0
    c2 = _llenar(out / "revision_manual.csv", tmp_path / "2.csv", {"1111": {"decision": "ACEPTAR_RANGO2", "revisor": "Ana"}})
    assert _aplicar(proc, c2, tmp_path, fecha="2026-10-21") == 0
    cw = pd.read_parquet(proc / "crosswalk.parquet")
    assert cw[cw.sinco_code == "1111"]["onet_soc_code"].tolist() == ["13-1111.00"]       # rango 2 automatico, no el par manual previo
    cam = pd.read_parquet(proc / "revision_manual_cambios.parquet")
    assert len(cam) == 2 and cam.iloc[1].pares_antes == "11-1011.00" and cam.iloc[1].pares_despues == "13-1111.00"
    assert (proc / "revision_manual" / "previo_2026-10-21").exists()
