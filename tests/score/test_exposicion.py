"""Pruebas de src/score/exposicion.py con datos SINTETICOS. Los valores esperados estan calculados a mano
en cada prueba (verificacion del codigo, no resultados de exposicion)."""
import datetime as dt
import json

import pandas as pd
import pyarrow.parquet as pq
import pytest

from src.annotate import schemas
from src.score import exposicion as X

CFG = X.cargar_config()
MAPAS = {"principal": {"E0": 0.0, "E1": 0.5, "E2": 1.0},
         "inferior": {"E0": 0.0, "E1": 0.0, "E2": 1.0},
         "superior": {"E0": 0.0, "E1": 1.0, "E2": 1.0}}


def A(run, soc, tid, tipo, clase, model="m-test", fecha=dt.date(2026, 1, 1)):
    return schemas.Annotation(
        run_id=run, prompt_version="pv-test", prompt_sha256="a" * 64, model=model, run_date=fecha,
        onet_version="31.0", onet_soc=soc, task_id=tid, task_text_en="x", annotated_text_lang="en",
        task_type=tipo, exposure_class=clase, physical_bottleneck=False, confidence="alta", rationale="r")


def tareas_run(run, clases_11):
    """Ocupacion 11-1011.00: 4 core (clases_11), 1 supplemental E2, 1 sin tipo E0. 13-1111.00: 2 core E0.
    29-1141.00: 1 core E2 (de 10 del universo)."""
    r = [A(run, "11-1011.00", f"a{i}", "core", c) for i, c in enumerate(clases_11, 1)]
    r += [A(run, "11-1011.00", "a5", "supplemental", "E2"), A(run, "11-1011.00", "a6", None, "E0")]
    r += [A(run, "13-1111.00", "b1", "core", "E0"), A(run, "13-1111.00", "b2", "core", "E0")]
    r += [A(run, "29-1141.00", "c1", "core", "E2")]
    return r


def universo():
    filas = [("11-1011.00", f"a{i}") for i in range(1, 9)] + [("13-1111.00", "b1"), ("13-1111.00", "b2")]
    filas += [("15-1252.00", f"d{i}") for i in range(1, 4)] + [("29-1141.00", f"c{i}") for i in range(1, 11)]
    return pd.DataFrame(filas, columns=["onet_soc_code", "task_id"])


def ratings():
    f = [("11-1011.00", "a1", "IM", 4.0), ("11-1011.00", "a2", "IM", 2.0), ("11-1011.00", "a3", "IM", 2.0),
         ("11-1011.00", "a1", "RT", 100.0), ("11-1011.00", "a2", "RT", 50.0),
         ("11-1011.00", "a1", "FT", 3.0)]
    df = pd.DataFrame(f, columns=["onet_soc_code", "task_id", "scale_id", "data_value"])
    df["recommend_suppress"] = "N"
    return df


def crosswalk():
    f = [("S1", "11-1011.00", "M:N", "ok"), ("S1", "13-1111.00", "M:N", "baja_confianza"),
         ("S2", "11-1011.00", "M:N", "ok"), ("S2", "29-1141.00", "N:1", "ok"),
         ("S3", "15-1252.00", "1:N", "ok"), ("S3", "29-1141.00", "N:1", "ok"),
         ("S4", "11-1011.00", "1:1", "sin_coincidencia")]
    return pd.DataFrame(f, columns=["sinco_code", "onet_soc_code", "tipo_relacion", "match_status"])


def onet_A():
    ann = pd.DataFrame([r.model_dump() for r in tareas_run("run-A", ["E2", "E1", "E0", "E1"])])
    pesos = X.cargar_pesos_ratings(ratings(), CFG)
    return X.agregar_onet(ann, MAPAS, CFG, universo(), pesos, "ETQ").set_index("onet_soc")


# ---------------------------------------------------------------- (2) puntaje por tarea
def test_puntaje_tarea_usa_el_mapa_dado_no_valores_fijos():
    s = pd.Series(["E0", "E1", "E2", "E1"])
    assert X.puntaje_tarea(s, {"E0": 0.0, "E1": 0.25, "E2": 0.9}).tolist() == [0.0, 0.25, 0.9, 0.25]


def test_puntaje_tarea_rechaza_clase_desconocida():
    with pytest.raises(ValueError):
        X.puntaje_tarea(pd.Series(["E0", "E3"]), MAPAS["principal"])


def test_mapas_vienen_de_la_configuracion_de_annotate():
    from src.annotate import config as acfg
    m = X.cargar_mapas(CFG)
    sec = acfg.cargar()["mapa_numerico"]
    assert m["principal"] == sec["principal"] and m["inferior"] == sec["limite_inferior"]
    assert m["superior"] == sec["limite_superior"]


def test_promedio_ponderado():
    assert X.promedio_ponderado([1, 0], [3, 1]) == pytest.approx(0.75)   # (3*1 + 1*0)/4
    assert X.promedio_ponderado([1, 0]) == pytest.approx(0.5)
    assert pd.isna(X.promedio_ponderado([])) and pd.isna(X.promedio_ponderado([1], [0]))
    with pytest.raises(ValueError):
        X.promedio_ponderado([1], [-1])


# ---------------------------------------------------------------- (1) carga
def test_cargar_anotaciones_varias_corridas_y_directorio(tmp_path):
    schemas.write_parquet(tareas_run("run-A", ["E2", "E1", "E0", "E1"]), tmp_path / "run_run-A.parquet")
    schemas.write_parquet(tareas_run("run-B", ["E2", "E2", "E2", "E0"]), tmp_path / "run_run-B.parquet")
    df = X.cargar_anotaciones(tmp_path)
    assert len(df) == 2 * 9 and set(df["run_id"]) == {"run-A", "run-B"}
    assert len(X.cargar_anotaciones([tmp_path / "run_run-A.parquet"])) == 9


def test_cargar_rechaza_duplicados_entre_archivos(tmp_path):
    schemas.write_parquet(tareas_run("run-A", ["E2"] * 4), tmp_path / "run_1.parquet")
    schemas.write_parquet(tareas_run("run-A", ["E2"] * 4), tmp_path / "run_2.parquet")
    with pytest.raises(X.EsquemaIncumplido):
        X.cargar_anotaciones(tmp_path)


def test_cargar_rechaza_esquema_invalido(tmp_path):
    pq.write_table(pq.read_table(_escribir(tmp_path)).drop(["rationale"]), tmp_path / "run_malo.parquet")
    with pytest.raises(X.EsquemaIncumplido):
        X.cargar_anotaciones([tmp_path / "run_malo.parquet"])


def _escribir(tmp_path):
    p = tmp_path / "ok.parquet"
    schemas.write_parquet(tareas_run("run-A", ["E2"] * 4), p)
    return p


def test_cargar_rechaza_metadatos_inconsistentes_en_un_run(tmp_path):
    r = tareas_run("run-A", ["E2"] * 4)
    r[0] = A("run-A", "11-1011.00", "a1", "core", "E2", model="otro")
    schemas.write_parquet(r, tmp_path / "run_x.parquet")
    with pytest.raises(X.EsquemaIncumplido):
        X.cargar_anotaciones([tmp_path / "run_x.parquet"])


# ---------------------------------------------------------------- (3) O*NET por corrida
def test_E_o_principal_y_variantes_a_mano():
    o = onet_A().loc["11-1011.00"]
    # core: E2,E1,E0,E1 -> 1, .5, 0, .5 -> 2/4
    assert o["E_o"] == pytest.approx(0.5)
    assert o["E_o_inferior"] == pytest.approx(0.25)      # 1,0,0,0
    assert o["E_o_superior"] == pytest.approx(0.75)      # 1,1,0,1
    assert o["E_o_todas"] == pytest.approx(3.0 / 6)      # 1+.5+0+.5 + supp E2 (1) + sin tipo E0 (0) = 3 sobre 6
    assert o["share_E2"] == pytest.approx(0.25) and o["share_any"] == pytest.approx(0.75)
    assert (o["n_anotadas"], o["n_core"], o["n_supplemental"], o["n_sin_tipo"], o["n_universo"]) == (6, 4, 1, 1, 8)
    assert o["cobertura_tareas"] == pytest.approx(6 / 8)


def test_variante_ponderada_por_importancia_y_relevancia():
    o = onet_A().loc["11-1011.00"]
    # IM: a1=4 (e=1), a2=2 (e=.5), a3=2 (e=0); a4 sin peso se excluye -> (4+1+0)/8
    assert o["E_o_pond_im"] == pytest.approx(5 / 8) and o["n_core_con_peso_im"] == 3
    # RT: a1=100 (e=1), a2=50 (e=.5) -> (100+25)/150
    assert o["E_o_pond_rt"] == pytest.approx(125 / 150) and o["n_core_con_peso_rt"] == 2


def test_ocupaciones_sin_core_o_sin_anotacion_son_NA_con_causa():
    o = onet_A()
    assert o.loc["15-1252.00", "motivo_na"] == "sin_anotacion" and pd.isna(o.loc["15-1252.00", "E_o"])
    assert o.loc["15-1252.00", "n_anotadas"] == 0 and o.loc["15-1252.00", "cobertura_tareas"] == 0
    assert o.loc["13-1111.00", "E_o"] == 0 and o.loc["13-1111.00", "share_any"] == 0
    assert o.loc["29-1141.00", "cobertura_tareas"] == pytest.approx(0.1)
    assert (o["etiqueta"] == "ETQ").all()


def test_agregar_onet_exige_una_corrida_y_universo_consistente():
    ann = pd.DataFrame([r.model_dump() for r in tareas_run("run-A", ["E2"] * 4) + tareas_run("run-B", ["E2"] * 4)])
    with pytest.raises(ValueError):
        X.agregar_onet(ann, MAPAS, CFG)
    una = ann[ann["run_id"] == "run-A"]
    with pytest.raises(ValueError):
        X.agregar_onet(una, MAPAS, CFG, universo().query("onet_soc_code != '13-1111.00'"))


def test_agregar_onet_sin_universo_deja_cobertura_nula():
    ann = pd.DataFrame([r.model_dump() for r in tareas_run("run-A", ["E2", "E1", "E0", "E1"])])
    o = X.agregar_onet(ann, MAPAS, CFG)
    assert o["cobertura_tareas"].isna().all() and o["E_o"].notna().any()


# ---------------------------------------------------------------- (4) SINCO
def sinco_A(cfg=CFG):
    return X.agregar_sinco(onet_A().reset_index(), crosswalk(), cfg, "ETQ").set_index("sinco_code")


def test_sinco_media_uniforme_min_max_a_mano():
    s = sinco_A().loc["S1"]
    # 11-1011: E_o .5 ; 13-1111: E_o 0 -> media .25, min 0, max .5
    assert (s["E_sinco"], s["E_sinco_min"], s["E_sinco_max"]) == pytest.approx((0.25, 0.0, 0.5))
    assert s["E_sinco_inferior"] == pytest.approx(0.125) and s["E_sinco_superior"] == pytest.approx(0.375)
    assert s["E_sinco_todas"] == pytest.approx((0.5 + 0.0) / 2)   # E_o_todas: .5 y 0
    assert (s["n_onet_mapped"], s["n_onet_con_anotacion"], s["cobertura_onet"]) == (2, 2, 1.0)
    assert s["crosswalk_type"] == "M:N" and s["crosswalk_confidence"] == "baja_confianza"
    assert s["peso_crosswalk"] == "uniforme" and pd.isna(s["motivo_na"])


def test_sinco_cobertura_parcial_en_el_umbral_y_NA_bajo_el_umbral():
    s = sinco_A().loc["S2"]   # 29-1141 (cobertura .1 < umbral tareas) no es elegible: 1 de 2 = .5 >= .5
    assert s["E_sinco"] == pytest.approx(0.5) and s["cobertura_onet"] == pytest.approx(0.5)
    assert s["crosswalk_type"] == "M:N;N:1"
    cfg2 = json.loads(json.dumps(CFG))
    cfg2["cobertura"]["umbral_onet_sinco"] = 0.75
    s2 = sinco_A(cfg2).loc["S2"]
    assert pd.isna(s2["E_sinco"]) and s2["motivo_na"] == "cobertura_insuficiente" and s2["n_onet_con_anotacion"] == 1


def test_sinco_NA_sin_cobertura_y_sin_coincidencia():
    t = sinco_A()
    assert pd.isna(t.loc["S3", "E_sinco"]) and t.loc["S3", "motivo_na"] == "cobertura_insuficiente"
    assert t.loc["S3", "n_onet_con_anotacion"] == 0
    assert pd.isna(t.loc["S4", "E_sinco"]) and t.loc["S4", "motivo_na"] == "sin_coincidencia"
    assert t.loc["S4", "n_onet_mapped"] == 0


def test_sinco_exige_universo_y_columnas_del_crosswalk():
    o = onet_A().reset_index()
    with pytest.raises(X.EsquemaIncumplido):
        X.agregar_sinco(o, crosswalk().drop(columns=["tipo_relacion"]), CFG)
    with pytest.raises(X.EsquemaIncumplido):
        X.agregar_sinco(o, pd.concat([crosswalk(), crosswalk().iloc[:1]]), CFG)
    with pytest.raises(ValueError):
        X.agregar_sinco(o.assign(cobertura_tareas=float("nan")), crosswalk(), CFG)


def test_crosswalk_real_tiene_las_columnas_requeridas():
    p = X.ROOT / CFG["rutas"]["crosswalk"]
    if not p.exists():
        pytest.skip("sin crosswalk")
    assert {"sinco_code", "onet_soc_code", "tipo_relacion", "match_status"} <= set(pq.read_schema(p).names)


# ---------------------------------------------------------------- entre corridas (PROVISIONAL)
def test_resumen_entre_corridas_media_min_max_a_mano():
    anns = []
    for run, cl in (("run-A", ["E2", "E1", "E0", "E1"]), ("run-B", ["E2", "E2", "E2", "E0"])):
        a = pd.DataFrame([r.model_dump() for r in tareas_run(run, cl)])
        anns.append(X.agregar_onet(a, MAPAS, CFG, universo(), None, "ETQ"))
    r = X.resumen_entre_corridas(pd.concat(anns), "onet_soc", X._VAR_ONET, "E_o").set_index("onet_soc")
    f = r.loc["11-1011.00"]
    # A: .5 ; B: (1+1+1+0)/4 = .75 -> media .625
    assert (f["E_o_media"], f["E_o_min"], f["E_o_max"]) == pytest.approx((0.625, 0.5, 0.75))
    assert f["n_corridas"] == 2 and f["run_ids"] == "run-A;run-B"
    assert r.loc["15-1252.00", "n_corridas_con_valor"] == 0 and pd.isna(r.loc["15-1252.00", "E_o_media"])


# ---------------------------------------------------------------- (5) salidas y piloto
def _entradas(tmp_path, completa):
    """completa=True: el universo es solo lo anotado (cobertura total); False: universo grande (piloto)."""
    run = "full-01" if completa else "run-A"
    recs = tareas_run(run, ["E2", "E1", "E0", "E1"])
    ad = tmp_path / "ann"
    schemas.write_parquet(recs, ad / f"run_{run}.parquet")
    u = pd.DataFrame([(r.onet_soc, r.task_id) for r in recs], columns=["onet_soc_code", "task_id"]) if completa else universo()
    u.to_parquet(tmp_path / "u.parquet")
    crosswalk().to_parquet(tmp_path / "cw.parquet")
    ratings().to_parquet(tmp_path / "r.parquet")
    return ad, tmp_path / "cw.parquet", tmp_path / "u.parquet", tmp_path / "r.parquet"


def test_cli_se_niega_sobre_piloto(tmp_path, capsys):
    ad, cw, u, r = _entradas(tmp_path, completa=False)
    out = tmp_path / "out"
    rc = X.main(["--anotaciones", str(ad), "--crosswalk", str(cw), "--universo-tareas", str(u), "--ratings", str(r),
                 "--salida-dir", str(out)])
    assert rc == 2 and not out.exists()
    assert "piloto" in capsys.readouterr().err.lower()
    with pytest.raises(X.PilotoNoPermitido):
        X.ejecutar(ad, cw, u, r, out)


def test_permitir_piloto_rotula_salidas_y_las_marca_en_archivo(tmp_path):
    ad, cw, u, r = _entradas(tmp_path, completa=False)
    out = tmp_path / "out"
    rutas = X.ejecutar(ad, cw, u, r, out, permitir_piloto=True)
    assert all(p.name.endswith("_PILOTO.parquet") or p.name.endswith("_PILOTO.json") for p in rutas.values())
    for k in ("ocupacion_onet", "sinco", "ocupacion_onet_corridas", "sinco_corridas"):
        t = pq.read_table(rutas[k]).to_pandas()
        assert (t["etiqueta"] == "PILOTO, NO RESULTADO").all()
    meta = json.loads(rutas["meta"].read_text(encoding="utf-8"))
    assert meta["es_piloto"] and meta["run_ids"] == ["run-A"] and meta["prompt_versions"] == ["pv-test"]
    assert meta["rubrica_version"] == "1" and meta["modelos"] == ["m-test"]
    with pytest.raises(FileExistsError):
        X.ejecutar(ad, cw, u, r, out, permitir_piloto=True)
    X.ejecutar(ad, cw, u, r, out, permitir_piloto=True, sobrescribir=True)


def test_corrida_completa_sintetica_escribe_sin_sufijo_y_con_trazabilidad(tmp_path):
    ad, cw, u, r = _entradas(tmp_path, completa=True)
    assert X.main(["--anotaciones", str(ad), "--crosswalk", str(cw), "--universo-tareas", str(u), "--ratings", str(r),
                   "--salida-dir", str(tmp_path / "o")]) == 0
    t = pq.read_table(tmp_path / "o" / "exposicion_ocupacion_onet.parquet").to_pandas().set_index("onet_soc")
    assert t.loc["11-1011.00", "E_o"] == pytest.approx(0.5)
    assert t.loc["11-1011.00", "run_id"] == "full-01" and t.loc["11-1011.00", "prompt_version"] == "pv-test"
    assert t.loc["11-1011.00", "model"] == "m-test" and t.loc["11-1011.00", "rubrica_version"] == "1"
    assert (t["etiqueta"] == "PROVISIONAL, SIN VALIDAR").all()
    s = pq.read_table(tmp_path / "o" / "exposicion_sinco.parquet").to_pandas().set_index("sinco_code")
    assert s.loc["S1", "E_sinco"] == pytest.approx(0.25)
    assert pq.read_schema(tmp_path / "o" / "exposicion_sinco.parquet").field("run_date").type == "date32[day]"


def test_entrada_fuera_de_esquema_escribe_issue_y_se_detiene(tmp_path, monkeypatch):
    ad, cw, u, r = _entradas(tmp_path, completa=True)
    malo = tmp_path / "malo"
    malo.mkdir()
    pq.write_table(pq.read_table(next(ad.glob("run_*.parquet"))).drop(["rationale"]), malo / "run_x.parquet")
    monkeypatch.setitem(X.cargar_config.__globals__, "ROOT", tmp_path)
    rc = X.main(["--anotaciones", str(malo), "--crosswalk", str(cw), "--universo-tareas", str(u), "--ratings", str(r),
                 "--salida-dir", str(tmp_path / "o2")])
    assert rc == 3 and list((tmp_path / "docs" / "issues").glob("score-*-esquema-incumplido.md"))
    assert not (tmp_path / "o2").exists()
