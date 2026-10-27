"""Pruebas de src/annotate/ruta_s.py y ruta_s_validacion.py con datos SINTETICOS (verifican codigo, no son resultados)."""
import json
import random
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.annotate import ruta_s as R
from src.annotate import ruta_s_validacion as V
from src.annotate import schemas as S

FECHA = "2026-10-20"


def universo_sintetico(n_grupos=27, seed=1):
    rng = random.Random(seed)
    grupos = {}
    for i in range(n_grupos):
        code = f"{1000 + i * 7:04d}"
        nf = 24 if i == 3 else rng.randint(3, 14)
        funcs = [{"orden": o, "texto": f"Funcion {o} del grupo {code}.", "item_fusionado": (code == "1021" and o == 2)}
                 for o in range(1, nf + 1)]
        grupos[code] = {"sinco_code": code, "titulo": f"Grupo {code}", "descripcion": "Descripcion sintetica.",
                        "ocupaciones": ["Ocupacion A", "Ocupacion B"], "funciones": funcs}
    return {"grupos": grupos, "source_sha256": "a" * 64, "sin_funciones": ["9999"]}


@pytest.fixture
def env(tmp_path):
    base = tmp_path / "ruta_s"
    return {"base": base, "issues": tmp_path / "issues", "uni": universo_sintetico()}


def hacer_export(env, n=3):
    return R.export(n_corridas=n, fecha=FECHA, universo=env["uni"], base=env["base"])


def doc_lote(env, rid, bid):
    return json.loads((env["base"] / "inputs" / rid / f"{bid}.json").read_text(encoding="utf-8"))


def respuesta_valida(doc, sesgo=0, rng=None):
    rng = rng or random.Random(0)
    lines = []
    for fid in doc["function_ids"]:
        e = rng.choice(["E0", "E1", "E2"])
        el = {"E0": "EL0", "E1": "EL1", "E2": "EL2"}[e]
        lines.append(json.dumps({"function_id": fid, "exposure_class": e, "eloundou_class": el, "physical_bottleneck": e == "E0",
                                 "confidence": "media", "rationale": "Motivo breve."}))
    return "\n".join(lines)


def escribir(tmp, nombre, texto):
    p = tmp / nombre
    p.write_text(texto, encoding="utf-8")
    return p


# ---------------------------------------------------------------- esquema
def test_modelo_rechaza_fuera_de_esquema_y_continuos():
    base = {"function_id": "1111-01", "exposure_class": "E1", "eloundou_class": "EL3", "physical_bottleneck": False,
            "confidence": "alta", "rationale": "ok"}
    S.ModelOutputS.model_validate(base)
    for malo in [{"exposure_class": "E3"}, {"eloundou_class": "E1"}, {"eloundou_class": "EL4"}, {"physical_bottleneck": "false"},
                 {"confidence": "ALTA"}, {"rationale": ""}, {"score": 0.7}, {"exposure_class": 0.5}]:
        with pytest.raises(ValidationError):
            S.ModelOutputS.model_validate({**base, **malo})


def test_annotation_s_unicidad_y_nulos(tmp_path):
    kw = dict(run_id="r", prompt_version="ann-s-v1", prompt_sha256="a" * 64, model="m", run_date="2026-10-20", batch_id="L001",
              batch_date="2026-10-20", attempt=1, sinco_code="1111", orden=1, function_text_es="x", item_fusionado=False,
              source_sha256="b" * 64, exposure_class="E1", eloundou_class="EL1", physical_bottleneck=False, confidence="alta",
              rationale="r", capability_cutoff="2026-10-20")
    import datetime as dt
    kw["run_date"] = kw["batch_date"] = dt.date(2026, 10, 20)
    a = S.AnnotationS(**kw)
    with pytest.raises(ValidationError):
        S.AnnotationS(**kw, task_id="t1")          # ruta O: nulo en ruta S
    with pytest.raises(ValueError):
        S.validar_unicidad_s([a, a])
    p = tmp_path / "x.parquet"
    S.write_parquet_s([a], p)
    assert S.read_parquet_s(p)[0].sinco_code == "1111"
    with pytest.raises(FileExistsError):
        S.write_parquet_s([a], p)


def test_esquema_ruta_o_intacto():
    assert "eloundou_class" not in S.ARROW_SCHEMA.names and "task_id" in S.ARROW_SCHEMA.names


# ---------------------------------------------------------------- prompt
def test_prompt_hash_y_rubricas():
    p = R.cargar_prompt("ann-s-v1")
    assert len(p.sha256) == 64
    assert "Label tasks E0 if direct access to the LLM" in p.system
    assert "Label tasks E2 if having access to the LLM alone" in p.system
    assert "EL3" in p.system and "exposure_class" in p.system
    assert "<<capability_cutoff>>" in p.system and "2026-10-20" in p.system_text("2026-10-20")
    assert "Excluye" not in p.user


# ---------------------------------------------------------------- export
def test_export_determinista_y_tope(env, tmp_path):
    r1 = hacer_export(env)
    env2 = {**env, "base": tmp_path / "otro"}
    hacer_export(env2)
    for rid in r1:
        for p in sorted((env["base"] / "inputs" / rid).glob("L*.json")):
            assert p.read_bytes() == (env2["base"] / "inputs" / rid / p.name).read_bytes()
        for lote in json.loads((env["base"] / rid / "estado.json").read_text())["lotes"].values():
            assert lote["n_funciones"] <= 120 and lote["n_grupos"] <= 10
        assert r1[rid]["funciones"] == sum(len(g["funciones"]) for g in env["uni"]["grupos"].values())
        assert r1[rid]["grupos"] == len(env["uni"]["grupos"])


def test_export_ordenes_distintos_por_corrida_y_cobertura(env):
    hacer_export(env)
    rids = R.run_ids(FECHA, 3, "ann-s-v1")
    ordenes = []
    for rid in rids:
        ids = []
        for p in sorted((env["base"] / "inputs" / rid).glob("L*.json")):
            ids += json.loads(p.read_text(encoding="utf-8"))["function_ids"]
        assert len(ids) == len(set(ids))
        ordenes.append(ids)
    assert len({tuple(o) for o in ordenes}) == 3
    assert ordenes[0] != ordenes[1] and set(ordenes[0]) == set(ordenes[1]) == set(ordenes[2])
    # los lotes difieren entre corridas
    lotes = [tuple(frozenset(json.loads(p.read_text(encoding="utf-8"))["function_ids"]) for p in sorted((env["base"] / "inputs" / rid).glob("L*.json"))) for rid in rids]
    assert lotes[0] != lotes[1]


def test_lote_cierra_por_tope_120():
    uni = {"grupos": {f"{2000 + i:04d}": {"sinco_code": f"{2000 + i:04d}", "titulo": "t", "descripcion": "d", "ocupaciones": [],
                                         "funciones": [{"orden": o, "texto": "f", "item_fusionado": False} for o in range(1, 24)]}
                      for i in range(12)}, "source_sha256": "a" * 64, "sin_funciones": []}
    lotes = R.plan_lotes(uni, 1, 10, 120)
    assert all(sum(len(g["funciones"]) for g in l) <= 120 for l in lotes)
    assert max(len(l) for l in lotes) == 5            # 5 x 23 = 115 (un sexto grupo pasaria de 120)
    lotes10 = R.plan_lotes(uni, 1, 3, 120)
    assert max(len(l) for l in lotes10) == 3          # tambien cierra por 10 (aqui 3) grupos


def test_export_no_sobrescribe_y_mensaje_sin_run_id(env):
    hacer_export(env)
    with pytest.raises(FileExistsError):
        hacer_export(env)
    d = doc_lote(env, R.run_ids(FECHA, 3, "ann-s-v1")[0], "L001")
    assert "ann-s-v1-2026" not in d["mensaje_subagente"] and d["prompt_sha256"] == R.cargar_prompt().sha256
    assert d["capability_cutoff"] == FECHA and d["temperature_controlled"] is False
    assert f"{d['function_ids'][0]}" in d["mensaje_subagente"]


def test_item_fusionado_en_metadatos(env):
    hacer_export(env, 1)
    marcados = []
    rid = R.run_ids(FECHA, 1, "ann-s-v1")[0]
    for p in (env["base"] / "inputs" / rid).glob("L*.json"):
        for g in json.loads(p.read_text(encoding="utf-8"))["grupos"]:
            marcados += [f["function_id"] for f in g["funciones"] if f["item_fusionado"]]
    assert marcados == ["1021-02"]


# ---------------------------------------------------------------- importacion
def test_importacion_valida(env, tmp_path):
    hacer_export(env, 1)
    rid = R.run_ids(FECHA, 1, "ann-s-v1")[0]
    d = doc_lote(env, rid, "L001")
    assert R.iniciar(rid, "L001", env["base"]) == 1
    resp = escribir(tmp_path, "r.txt", respuesta_valida(d))
    r = R.importar_lote(rid, "L001", respuesta=resp, base=env["base"], fecha=FECHA, issues_dir=env["issues"])
    assert r["resultado"] == "ok"
    est = R.cargar_estado(rid, env["base"])
    assert est["lotes"]["L001"]["estado"] == "ok" and est["lotes"]["L001"]["intentos"] == 1
    sal = json.loads((env["base"] / rid / "salida" / "L001.json").read_text(encoding="utf-8"))
    assert len(sal) == d["n_funciones"] and sal[0]["model"] == "claude-sonnet-5-5 (subagente Claude Code)"
    assert sal[0]["temperature_controlled"] is False and sal[0]["temperature_requested"] is None
    with pytest.raises(RuntimeError):
        R.importar_lote(rid, "L001", respuesta=resp, base=env["base"], fecha=FECHA)


@pytest.mark.parametrize("caso", ["faltante", "duplicado", "sobrante", "fuera_esquema", "no_json", "continuo", "bloque_codigo", "vacio"])
def test_importacion_invalida(env, tmp_path, caso):
    hacer_export(env, 1)
    rid = R.run_ids(FECHA, 1, "ann-s-v1")[0]
    d = doc_lote(env, rid, "L001")
    lines = respuesta_valida(d).splitlines()
    if caso == "faltante":
        lines = lines[:-1]
    elif caso == "duplicado":
        lines.append(lines[0])
    elif caso == "sobrante":
        lines.append(lines[0].replace(d["function_ids"][0], "0000-01"))
    elif caso == "fuera_esquema":
        lines[0] = lines[0].replace('"E', '"X', 1)
    elif caso == "no_json":
        lines[0] = "texto libre"
    elif caso == "continuo":
        o = json.loads(lines[0]); o["score"] = 0.5; lines[0] = json.dumps(o)
    elif caso == "bloque_codigo":
        lines = ["```json"] + lines + ["```"]
    elif caso == "vacio":
        lines = []
    r = R.importar_lote(rid, "L001", respuesta=escribir(tmp_path, "r.txt", "\n".join(lines)), base=env["base"], fecha=FECHA,
                        issues_dir=env["issues"])
    assert r["resultado"] == "invalido" and r["errores"]
    est = R.cargar_estado(rid, env["base"])["lotes"]["L001"]
    assert est["estado"] == "invalido" and est["intentos"] == 1
    assert not (env["base"] / rid / "salida" / "L001.json").exists()      # no se acepta a medias
    assert (env["issues"] / f"anotacion-ruta-s-{rid}.md").exists()


def test_reintentos_hasta_fallido_y_corrida_detenida(env, tmp_path):
    hacer_export(env, 1)
    rid = R.run_ids(FECHA, 1, "ann-s-v1")[0]
    for i in range(3):
        r = R.importar_lote(rid, "L001", respuesta=escribir(tmp_path, f"r{i}.txt", "basura"), base=env["base"], fecha=FECHA,
                            issues_dir=env["issues"])
    est = R.cargar_estado(rid, env["base"])
    assert est["lotes"]["L001"]["estado"] == "fallido" and est["lotes"]["L001"]["intentos"] == 3 and est["detenida"]
    assert len(list((env["base"] / rid / "intentos").glob("L001_a*.txt"))) == 3     # respuestas crudas conservadas
    assert "FALLIDO DEFINITIVO" in (env["issues"] / f"anotacion-ruta-s-{rid}.md").read_text(encoding="utf-8")
    with pytest.raises(RuntimeError):
        R.iniciar(rid, "L002", env["base"])
    with pytest.raises(RuntimeError):
        R.importar_lote(rid, "L002", respuesta=escribir(tmp_path, "z.txt", "x"), base=env["base"])


def test_reanudacion_tras_fallo(env, tmp_path):
    hacer_export(env, 1)
    rid = R.run_ids(FECHA, 1, "ann-s-v1")[0]
    d1, d2 = doc_lote(env, rid, "L001"), doc_lote(env, rid, "L002")
    R.importar_lote(rid, "L001", respuesta=escribir(tmp_path, "a.txt", respuesta_valida(d1)), base=env["base"], fecha=FECHA, issues_dir=env["issues"])
    R.iniciar(rid, "L002", env["base"])                         # queda en_curso (interrupcion)
    R.interrumpir(rid, "L002", env["base"])
    est = R.cargar_estado(rid, env["base"])["lotes"]
    assert est["L002"]["estado"] == "pendiente" and est["L002"]["intentos"] == 0     # no cuenta como intento
    R.iniciar(rid, "L003", env["base"])
    assert R.reanudar(rid, env["base"]) == ["L003"]
    # primer intento de L002 invalido, segundo valido
    R.importar_lote(rid, "L002", respuesta=escribir(tmp_path, "b.txt", "x"), base=env["base"], fecha=FECHA, issues_dir=env["issues"])
    R.importar_lote(rid, "L002", respuesta=escribir(tmp_path, "c.txt", respuesta_valida(d2)), base=env["base"], fecha=FECHA, issues_dir=env["issues"])
    est = R.cargar_estado(rid, env["base"])["lotes"]
    assert est["L001"]["intentos"] == 1 and est["L002"]["intentos"] == 2 and est["L002"]["estado"] == "ok"
    assert est["L002"]["historial"][0]["resultado"] == "invalido"


def test_faltantes_en_importar_corrida(env, tmp_path):
    hacer_export(env, 1)
    rid = R.run_ids(FECHA, 1, "ann-s-v1")[0]
    out = R.importar_corrida(rid, base=env["base"], fecha=FECHA, issues_dir=env["issues"])
    assert len(out["faltantes"]) == len(R.cargar_estado(rid, env["base"])["lotes"]) and out["parquet"] is None
    assert "sin respuesta" in (env["issues"] / f"anotacion-ruta-s-{rid}.md").read_text(encoding="utf-8")


def test_estado_resumen(env, tmp_path):
    hacer_export(env, 1)
    rid = R.run_ids(FECHA, 1, "ann-s-v1")[0]
    R.importar_lote(rid, "L001", respuesta=escribir(tmp_path, "a.txt", "x"), base=env["base"], fecha=FECHA, issues_dir=env["issues"])
    R.importar_lote(rid, "L001", respuesta=escribir(tmp_path, "b.txt", respuesta_valida(doc_lote(env, rid, "L001"))), base=env["base"],
                    fecha=FECHA, issues_dir=env["issues"])
    R.iniciar(rid, "L002", env["base"])
    r = R.resumen_estado(R.cargar_estado(rid, env["base"]))
    assert r["ok"] == 1 and r["en_curso"] == 1 and r["pendiente"] == r["n_lotes"] - 2
    assert r["intentos_totales"] == 2 and r["primer_intento_rechazados"] == 1 and r["tasa_rechazo_primer_intento"] == 1.0


def test_prompt_modificado_bloquea_importacion(env, tmp_path):
    hacer_export(env, 1)
    rid = R.run_ids(FECHA, 1, "ann-s-v1")[0]
    pd_ = tmp_path / "prompts"
    pd_.mkdir()
    (pd_ / "ann-s-v1.md").write_text(R.cargar_prompt().raw + "\nextra", encoding="utf-8")
    with pytest.raises(ValueError):
        R.importar_lote(rid, "L001", respuesta=escribir(tmp_path, "a.txt", "x"), base=env["base"], prompt_dir=pd_)


# ---------------------------------------------------------------- validacion de corrida completa
def completar(env, tmp_path, runs, variante):
    for k, rid in enumerate(runs):
        est = R.cargar_estado(rid, env["base"])
        for b in est["lotes"]:
            d = doc_lote(env, rid, b)
            lines = []
            for fid in d["function_ids"]:
                e = random.Random(fid).choice(["E0", "E1", "E2"])
                if variante == "ruido" and random.Random(f"{k}-{fid}-a").random() < 0.9:
                    e = random.Random(f"{k}-{fid}-b").choice(["E0", "E1", "E2"])
                el = {"E0": "EL0", "E1": "EL1", "E2": "EL2"}[e]
                lines.append(json.dumps({"function_id": fid, "exposure_class": e, "eloundou_class": el, "physical_bottleneck": e == "E0",
                                         "confidence": "media", "rationale": "Motivo."}))
            R.importar_lote(rid, b, respuesta=escribir(tmp_path, f"{rid}_{b}.txt", "\n".join(lines)), base=env["base"], fecha=FECHA,
                            issues_dir=env["issues"])
        assert R.ensamblar(rid, base=env["base"], issues_dir=env["issues"]).exists()


def test_validacion_tres_corridas_sinteticas(env, tmp_path):
    hacer_export(env)
    runs = R.run_ids(FECHA, 3, "ann-s-v1")
    completar(env, tmp_path, runs, "igual")
    rep = V.validar_corrida_completa(runs, base=env["base"], universo=env["uni"], escribir=False)
    assert rep["aceptada"] and rep["acuerdo"]["exposure_class"]["estado"] == "suficiente"
    assert rep["acuerdo"]["exposure_class"]["alfa_krippendorff_ordinal"] == pytest.approx(1.0)
    assert rep["acuerdo"]["eloundou_cruda"]["kappa_min"] == pytest.approx(1.0)
    assert rep["cobertura"][runs[0]]["funciones"] == rep["cobertura"][runs[0]]["funciones_esperadas"]


def test_validacion_consistencia_insuficiente(env, tmp_path):
    hacer_export(env)
    runs = R.run_ids(FECHA, 3, "ann-s-v1")
    completar(env, tmp_path, runs, "ruido")
    rep = V.validar_corrida_completa(runs, base=env["base"], universo=env["uni"], escribir=False)
    assert rep["aceptada"] and "exposure_class" in rep["campos_con_consistencia_insuficiente"]


def test_validacion_rechaza_corrida_incompleta(env, tmp_path):
    hacer_export(env)
    runs = R.run_ids(FECHA, 3, "ann-s-v1")
    completar(env, tmp_path, runs[:2], "igual")                  # la tercera sin anotar
    rep = V.validar_corrida_completa(runs, base=env["base"], universo=env["uni"], escribir=False)
    assert rep["aceptada"] is False and "acuerdo" not in rep
    assert any("lotes ok" in m for m in rep["motivos_no_aceptada"])
    assert V.validar_corrida_completa(runs[:2], base=env["base"], universo=env["uni"], escribir=False)["aceptada"] is False  # 2 != 3


def test_validacion_rechaza_cobertura_incompleta(env, tmp_path):
    hacer_export(env)
    runs = R.run_ids(FECHA, 3, "ann-s-v1")
    completar(env, tmp_path, runs, "igual")
    uni2 = json.loads(json.dumps(env["uni"]))
    uni2["grupos"]["8888"] = {"sinco_code": "8888", "titulo": "t", "descripcion": "d", "ocupaciones": [],
                              "funciones": [{"orden": 1, "texto": "f", "item_fusionado": False}]}
    rep = V.validar_corrida_completa(runs, base=env["base"], universo=uni2, escribir=False)
    assert not rep["aceptada"] and any("cobertura" in m for m in rep["motivos_no_aceptada"])


def test_validacion_rechaza_lote_fallido(env, tmp_path):
    hacer_export(env)
    runs = R.run_ids(FECHA, 3, "ann-s-v1")
    completar(env, tmp_path, runs[:2], "igual")
    for i in range(3):
        R.importar_lote(runs[2], "L001", respuesta=escribir(tmp_path, f"f{i}.txt", "x"), base=env["base"], fecha=FECHA, issues_dir=env["issues"])
    rep = V.validar_corrida_completa(runs, base=env["base"], universo=env["uni"], escribir=False)
    assert not rep["aceptada"] and any("fallido" in m for m in rep["motivos_no_aceptada"])


def test_kappa_y_alfa_valores_conocidos():
    a = ["E0", "E1", "E2", "E2"]
    assert V.kappa_cuadratico(a, a, ["E0", "E1", "E2"]) == pytest.approx(1.0)
    assert V.kappa_cuadratico(["E0", "E0"], ["E0", "E0"], ["E0", "E1", "E2"]) is None
    from sklearn.metrics import cohen_kappa_score
    x = ["E0", "E1", "E2", "E1", "E0", "E2", "E2", "E1"]
    y = ["E0", "E2", "E2", "E1", "E1", "E2", "E1", "E1"]
    assert V.kappa_cuadratico(x, y, ["E0", "E1", "E2"]) == pytest.approx(cohen_kappa_score(x, y, weights="quadratic", labels=["E0", "E1", "E2"]))


def test_ausencia_de_exposicion_agregada(env, tmp_path):
    hacer_export(env, 3)
    runs = R.run_ids(FECHA, 3, "ann-s-v1")
    completar(env, tmp_path, runs, "igual")
    rep = V.validar_corrida_completa(runs, base=env["base"], universo=env["uni"], escribir=False)
    txt = json.dumps(rep)
    for prohibido in ("E_g", "alfa_S", "beta_S", "cota_sup_S", "share_E2", "share_any", "exposicion_media"):
        assert prohibido not in txt
    cols = S.read_parquet_s(env["base"] / "parquet" / f"run_{runs[0]}.parquet")[0].model_dump().keys()
    assert not any(c.startswith(("E_", "score", "puntaje")) for c in cols)
