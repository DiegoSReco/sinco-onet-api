"""Pruebas de src/calibrate/b1_dawid_skene.py con datos SINTETICOS de verdad conocida (verificacion del codigo,
no resultados de exposicion)."""
import copy
import datetime as dt
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pytest

from src.annotate import schemas
from src.calibrate import b1_dawid_skene as B

ROOT = Path(__file__).resolve().parents[2]
CLASES = ["E0", "E1", "E2"]
PI = np.array([0.5, 0.3, 0.2])


def cfg_rapida(n_iter=800, descarte=300, thin=2, n_cadenas=3):
    c = copy.deepcopy(B.cargar_config())
    c["muestreo"].update(n_iter=n_iter, descarte=descarte, adelgazamiento=thin, n_cadenas=n_cadenas)
    return c


def theta_verdadera(diag, off_adj=None):
    t = np.full((3, 3), 0.0)
    for c in range(3):
        resto = 1 - diag
        for y in range(3):
            t[c, y] = diag if y == c else resto / 2
    return t


def sintetico(n=1500, thetas=None, seed=1, pi=PI, p_falta=0.0):
    rng = np.random.default_rng(seed)
    thetas = thetas or [theta_verdadera(0.8)] * 4
    z = rng.choice(3, size=n, p=pi)
    filas = []
    for k, T in enumerate(thetas):
        for i in range(n):
            if rng.random() < p_falta:
                continue
            filas.append((f"t{i:05d}", f"run_{k}", CLASES[rng.choice(3, p=T[z[i]])], False))
    return pd.DataFrame(filas, columns=["item", "anotador", "clase", "es_referencia"]), z


# --------------------------------------------------------------------------- recuperacion
def test_recupera_confusion_y_clase_latente():
    thetas = [theta_verdadera(0.85), theta_verdadera(0.75), theta_verdadera(0.8), theta_verdadera(0.7)]
    largo, z = sintetico(n=2000, thetas=thetas, seed=3)
    cfg = cfg_rapida()
    res = B.ajustar(largo, CLASES, cfg)
    t = B.resumir(res, "x", "exposure_class", False)
    d = res["datos"]
    # matrices de confusion posteriores (media) cerca de la verdad
    for k, T in enumerate(thetas):
        sub = t["confusion"][t["confusion"].anotador == f"run_{k}"]
        est = sub.pivot(index="clase_verdadera", columns="clase_observada", values="media").loc[CLASES, CLASES].to_numpy()
        assert np.abs(est - T).max() < 0.05
        # el intervalo cubre la verdad en la mayoria de celdas
        lo = sub.pivot(index="clase_verdadera", columns="clase_observada", values="lo").loc[CLASES, CLASES].to_numpy()
        hi = sub.pivot(index="clase_verdadera", columns="clase_observada", values="hi").loc[CLASES, CLASES].to_numpy()
        assert ((lo <= T) & (T <= hi)).mean() >= 0.7
    # prevalencias
    assert np.abs(t["prevalencias"].set_index("clase").loc[CLASES, "media"].to_numpy() - PI).max() < 0.04
    # clase latente: exactitud de la moda y suma de probabilidades
    it = t["items"].set_index("item").loc[d.items]
    assert (it["clase_modal"].to_numpy() == np.array(CLASES)[z]).mean() > 0.93
    assert np.allclose(it[[f"prob_{c}" for c in CLASES]].sum(axis=1), 1.0)
    assert (it["entropia_bits"] >= 0).all() and (it["entropia_bits"] <= np.log2(3) + 1e-9).all()
    # con 4 anotadores el modelo mejora (o iguala) el voto individual del primer anotador
    primero = largo[largo.anotador == "run_0"].set_index("item")["clase"].loc[d.items]
    assert (it["clase_modal"].to_numpy() == np.array(CLASES)[z]).mean() > (primero.to_numpy() == np.array(CLASES)[z]).mean()


def test_prior_fuerte_vs_debil_con_pocos_datos():
    # verdad con diagonal 0.55; prior fuerte dice ~0.91; con n pequeno el fuerte debe jalar mas hacia el prior
    thetas = [theta_verdadera(0.55)] * 3
    largo, _ = sintetico(n=40, thetas=thetas, seed=5)
    cfg = cfg_rapida()
    diag_media = {}
    for nivel in ("debil", "fuerte"):
        res = B.ajustar(largo, CLASES, cfg, prior=nivel)
        c = B.resumir(res, "x", "exposure_class", False)["confusion"]
        diag_media[nivel] = c[c.clase_verdadera == c.clase_observada]["media"].mean()
    prior_media = 20 / 22
    assert abs(diag_media["fuerte"] - prior_media) < abs(diag_media["debil"] - prior_media)
    assert diag_media["fuerte"] > diag_media["debil"]


def test_convergencia_y_diagnosticos():
    largo, _ = sintetico(n=800, seed=7)
    cfg = cfg_rapida(n_iter=1500, descarte=500, n_cadenas=4)
    res = B.ajustar(largo, CLASES, cfg)
    g = res["diagnosticos"]
    assert (g.rhat < cfg["diagnosticos"]["umbral_rhat"]).all()
    assert res["convergio"]
    assert g.ess.min() > 50
    assert "loglik_marginal" in set(g.parametro)
    # la traza de loglik tiene n_cadenas x n_iter filas y no hay NaN
    tr = B.resumir(res, "x", "exposure_class", False)["traza_loglik"]
    assert len(tr) == 4 * 1500 and tr["loglik_marginal"].notna().all()


def test_rhat_y_ess_funciones():
    rng = np.random.default_rng(0)
    iid = rng.normal(size=(4, 1000))
    assert abs(B.rhat_dividido(iid) - 1) < 0.02
    assert B.ess_aprox(iid) > 0.6 * iid.size
    ar = np.zeros((4, 1000))
    e = rng.normal(size=(4, 1000))
    for t in range(1, 1000):
        ar[:, t] = 0.95 * ar[:, t - 1] + e[:, t]
    assert B.ess_aprox(ar) < 0.2 * ar.size
    distintas = iid + np.array([[0], [5], [10], [15]])
    assert B.rhat_dividido(distintas) > 1.5


def test_determinismo_con_semilla():
    largo, _ = sintetico(n=200, seed=9)
    cfg = cfg_rapida(n_iter=300, descarte=100, n_cadenas=2)
    a = B.resumir(B.ajustar(largo, CLASES, cfg, semilla=11), "x", "exposure_class", False)
    b = B.resumir(B.ajustar(largo, CLASES, cfg, semilla=11), "x", "exposure_class", False)
    c = B.resumir(B.ajustar(largo, CLASES, cfg, semilla=12), "x", "exposure_class", False)
    pd.testing.assert_frame_equal(a["items"], b["items"])
    pd.testing.assert_frame_equal(a["confusion"], b["confusion"])
    assert not np.allclose(a["confusion"]["media"], c["confusion"]["media"])


def test_items_con_anotaciones_faltantes():
    largo, z = sintetico(n=600, seed=13, p_falta=0.5)
    # un item con una sola anotacion y otro sin ninguna (el sin anotaciones no aparece en el largo)
    cfg = cfg_rapida(n_iter=400, descarte=150, n_cadenas=2)
    res = B.ajustar(largo, CLASES, cfg)
    t = B.resumir(res, "x", "exposure_class", False)
    it = t["items"]
    assert it[[f"prob_{c}" for c in CLASES]].notna().all().all()
    assert np.allclose(it[[f"prob_{c}" for c in CLASES]].sum(axis=1), 1.0)
    assert it.n_anotaciones.min() >= 1 and it.n_anotaciones.max() <= 4
    # un item con 1 anotacion tiene mas entropia media que uno con 4
    assert it[it.n_anotaciones == 1].entropia_bits.mean() > it[it.n_anotaciones == 4].entropia_bits.mean()
    # los items sin ninguna anotacion no entran: n_items = items con >=1 observacion
    assert res["datos"].n_items == largo["item"].nunique()


def test_referencia_humana_separa_sesgo_comun():
    # Sesgo comun del LLM: verdad E1 se "ve" como E2 con prob 0.4 y todas las corridas copian esa vista (95 %).
    rng = np.random.default_rng(21)
    n = 1500
    z = rng.choice(3, size=n, p=PI)
    vista = z.copy()
    vista[(z == 1) & (rng.random(n) < 0.4)] = 2
    filas = []
    for k in range(3):
        for i in range(n):
            y = vista[i] if rng.random() < 0.95 else rng.choice(3)
            filas.append((f"t{i:05d}", f"run_{k}", CLASES[y], False))
    llm = pd.DataFrame(filas, columns=["item", "anotador", "clase", "es_referencia"])
    idx = rng.choice(n, size=500, replace=False)
    humano = pd.DataFrame({"item": [f"t{i:05d}" for i in idx], "anotador": "humano",
                           "clase": [CLASES[z[i] if rng.random() < 0.95 else rng.choice(3)] for i in idx],
                           "es_referencia": True})
    cfg = cfg_rapida(n_iter=1200, descarte=400, n_cadenas=3)

    def e12(largo):
        res = B.ajustar(largo, CLASES, cfg)
        c = B.resumir(res, "x", "exposure_class", "humano" in set(largo.anotador))["confusion"]
        return c[(c.anotador == "run_0") & (c.clase_verdadera == "E1") & (c.clase_observada == "E2")]["media"].iloc[0], res

    sin, _ = e12(llm)
    todo = pd.concat([llm, humano], ignore_index=True)
    con_corrida, _ = e12(todo)
    assert sin < 0.15                 # sin humano el sesgo comun es invisible (consistencia, no exactitud)
    # LIMITE documentado: con las corridas como anotadores independientes, la referencia NO basta (el sesgo comun
    # viola la independencia condicional); por eso existe la unidad 'modelo'.
    assert con_corrida < 0.2
    colapsado = B.colapsar_por_grupo(todo, {f"run_{k}": "llm" for k in range(3)})
    assert set(colapsado.anotador) == {"llm", "humano"}
    res = B.ajustar(colapsado, CLASES, cfg)
    c = B.resumir(res, "x", "exposure_class", True)["confusion"]
    con = c[(c.anotador == "llm") & (c.clase_verdadera == "E1") & (c.clase_observada == "E2")]["media"].iloc[0]
    assert abs(con - 0.4) < 0.12      # con humano y una vista por modelo se recupera el sesgo comun
    # medidas y etiquetas
    m_sin = B.resumir(B.ajustar(llm, CLASES, cfg), "x", "exposure_class", False)
    assert set(m_sin["medidas"].tipo_medida) == {"consistencia_entre_corridas_NO_exactitud"}
    assert "acuerdo_con_clase_latente" in set(m_sin["medidas"].medida) and "exactitud" not in set(m_sin["medidas"].medida)
    m_con = B.resumir(res, "x", "exposure_class", True)
    assert set(m_con["medidas"].tipo_medida) == {"exactitud_estimada_con_referencia_humana"}
    assert "exactitud" in set(m_con["medidas"].medida)
    assert m_con["medidas"][m_con["medidas"].anotador == "humano"].es_referencia_humana.all()


# --------------------------------------------------------------------------- entradas reales (esquema Annotation)
def _A(run, tid, clase, model="m-test", soc="11-1011.00"):
    return schemas.Annotation(
        run_id=run, prompt_version="pv", prompt_sha256="a" * 64, model=model, run_date=dt.date(2026, 1, 1),
        onet_version="31.0", onet_soc=soc, task_id=tid, task_text_en="x", annotated_text_lang="en",
        task_type="core", exposure_class=clase, physical_bottleneck=False, confidence="alta", rationale="r")


def escribir_corridas(tmp_path, runs, n=150, seed=2, prefijo="run_corrida"):
    rng = np.random.default_rng(seed)
    z = rng.choice(3, size=n, p=PI)
    soc = [f"11-{1000 + i % 30:04d}.00" for i in range(n)]
    universo = pd.DataFrame({"onet_soc_code": soc, "task_id": [f"t{i}" for i in range(n)]})
    up = tmp_path / "universo.parquet"; universo.to_parquet(up)
    T = theta_verdadera(0.8)
    for r in runs:
        recs = [_A(r, f"t{i}", CLASES[rng.choice(3, p=T[z[i]])], soc=soc[i]) for i in range(n)]
        schemas.write_parquet(recs, tmp_path / f"run_{r}.parquet")
    return up, z


def test_ejecutar_escribe_parquet_con_esquema_y_metadatos(tmp_path):
    up, _ = escribir_corridas(tmp_path, ["full-01", "full-02", "full-03"])
    cfg = cfg_rapida(n_iter=400, descarte=150, n_cadenas=2)
    out = tmp_path / "salida"
    r = B.ejecutar(tmp_path, out, "exposure_class", cfg=cfg, universo_path=up)
    assert r["meta"]["etiqueta"] == "PROVISIONAL, SIN VALIDAR" and not r["meta"]["es_piloto"]
    assert r["meta"]["modo"] == "sin_referencia_humana"
    assert "NO EXACTITUD" in r["resumen"] and "no son independientes" in r["resumen"]
    esq = {**B.ESQUEMAS_BASE, "items": B.esquema_items(CLASES)}
    for n, schema in esq.items():
        t = pq.read_table(r["rutas"][n])
        assert t.schema.names == schema.names and [f.type for f in t.schema] == [f.type for f in schema]
        meta = json.loads(t.schema.metadata[b"b1_meta"])
        assert meta["run_ids_entrada"] == ["full-01", "full-02", "full-03"] and meta["semilla"] == cfg["muestreo"]["semilla"]
    m = json.loads(r["rutas"]["meta"].read_text(encoding="utf-8"))
    for k in ("entradas_sha256", "config_sha256", "versiones", "fecha_utc", "corridas", "muestreo", "lectura"):
        assert k in m
    assert all(len(h) == 64 for h in m["entradas_sha256"].values())
    assert {c["run_id"] for c in m["corridas"]} == {"full-01", "full-02", "full-03"}
    # no sobrescribe sin permiso
    with pytest.raises(FileExistsError):
        B.ejecutar(tmp_path, out, "exposure_class", cfg=cfg, universo_path=up)


def test_colapso_por_modelo_empates_ausentes():
    f = pd.DataFrame([("a", "r1", "E0", False), ("a", "r2", "E0", False), ("a", "r3", "E1", False),
                      ("b", "r1", "E0", False), ("b", "r2", "E1", False),
                      ("a", "h", "E1", True)], columns=["item", "anotador", "clase", "es_referencia"])
    o = B.colapsar_por_grupo(f, {"r1": "m", "r2": "m", "r3": "m"})
    m = o[o.anotador == "m"].set_index("item")["clase"]
    assert m.to_dict() == {"a": "E0"}          # 'b' empata -> ausente
    assert (o.anotador == "h").sum() == 1


def test_ejecutar_con_referencia(tmp_path):
    up, z = escribir_corridas(tmp_path / "x" if (tmp_path / "x").mkdir() is None else tmp_path, ["full-01", "full-02", "full-03"])
    ref = pd.DataFrame({"task_id": [f"t{i}" for i in range(0, 150, 3)], "clase_humana": [CLASES[z[i]] for i in range(0, 150, 3)],
                        "revisor": "A"})
    refp = tmp_path / "ref.csv"; ref.to_csv(refp, index=False)
    cfg = cfg_rapida(n_iter=400, descarte=150, n_cadenas=2)
    r = B.ejecutar(tmp_path / "x", tmp_path / "o", "exposure_class", refp, dict(col_revisor="revisor"), cfg=cfg, universo_path=up)
    assert r["meta"]["modo"] == "con_referencia_humana"
    assert "humano:A" in r["meta"]["anotadores"]
    assert r["tablas"]["items"].tiene_referencia_humana.sum() == 50
    assert "SIN referencia humana" not in r["resumen"]


def test_rechaza_piloto_y_permite_con_etiqueta(tmp_path):
    up, _ = escribir_corridas(tmp_path, ["piloto-2026-01-01", "piloto-2026-01-02"])
    cfg = cfg_rapida(n_iter=300, descarte=100, n_cadenas=2)
    with pytest.raises(B.PilotoNoPermitido):
        B.ejecutar(tmp_path, tmp_path / "o", cfg=cfg, universo_path=up)
    assert B.main(["--anotaciones", str(tmp_path), "--salida-dir", str(tmp_path / "o2"), "--universo-tareas", str(up)]) == 2
    assert not (tmp_path / "o2").exists()
    r = B.ejecutar(tmp_path, tmp_path / "o", cfg=cfg, universo_path=up, permitir_piloto=True)
    assert r["meta"]["etiqueta"] == "PILOTO, NO RESULTADO" and r["meta"]["es_piloto"]
    assert all("_PILOTO_" in p.name for p in r["rutas"].values())
    assert (r["tablas"]["items"].etiqueta == "PILOTO, NO RESULTADO").all()
    assert "PILOTO, NO RESULTADO" in r["resumen"]


def test_rechaza_piloto_por_cobertura(tmp_path):
    up, _ = escribir_corridas(tmp_path, ["full-01", "full-02"], n=100)
    u = pd.read_parquet(up)
    extra = pd.DataFrame({"onet_soc_code": [f"99-{i:04d}.00" for i in range(100)], "task_id": [f"u{i}" for i in range(100)]})
    pd.concat([u, extra]).to_parquet(up)       # las anotaciones cubren ~50 % del universo
    with pytest.raises(B.PilotoNoPermitido):
        B.ejecutar(tmp_path, tmp_path / "o", cfg=cfg_rapida(300, 100, 2, 2), universo_path=up)


def test_campo_eloundou_class_con_fusion_el3(tmp_path):
    rng = np.random.default_rng(4)
    n = 120
    z = rng.choice(3, size=n, p=PI)
    cl = np.array(["EL0", "EL1", "EL2"])
    for r in ("full-01", "full-02", "full-03"):
        y = np.where(rng.random(n) < 0.85, z, rng.choice(3, size=n))
        lab = cl[y].astype(object); lab[(y == 2) & (rng.random(n) < 0.3)] = "EL3"
        pd.DataFrame({"run_id": r, "task_id": [f"f{i}" for i in range(n)], "eloundou_class": lab}).to_parquet(tmp_path / f"run_{r}.parquet")
    cfg = cfg_rapida(n_iter=300, descarte=100, n_cadenas=2)
    out = B.ejecutar(tmp_path, tmp_path / "o", "eloundou_class", cfg=cfg)
    assert list(out["resultado"]["datos"].clases) == ["EL0", "EL1", "EL2"]
    assert set(out["tablas"]["items"].clase_modal) <= {"EL0", "EL1", "EL2"}
    assert "b1_eloundou_class" in out["rutas"]["items"].name


def test_clase_fuera_de_esquema(tmp_path):
    pd.DataFrame({"run_id": "r", "task_id": ["a", "b"], "eloundou_class": ["EL1", "EL9"]}).to_parquet(tmp_path / "run_r.parquet")
    with pytest.raises(B.EsquemaIncumplido):
        B.ejecutar(tmp_path, tmp_path / "o", "eloundou_class", cfg=cfg_rapida())
    with pytest.raises(B.EsquemaIncumplido):
        B.cargar_referencia(_csv(tmp_path, {"task_id": ["a"], "clase_humana": ["E7"]}), "exposure_class", B.cargar_config())
    p = B.registrar_issue("prueba", tmp_path / "issues", dt.date(2026, 1, 2))
    assert p.name == "calibracion-2026-01-02-esquema-incumplido.md" and "prueba" in p.read_text(encoding="utf-8")


def _csv(tmp_path, d):
    p = tmp_path / "r.csv"; pd.DataFrame(d).to_csv(p, index=False); return p


# --------------------------------------------------------------------------- alcance del modulo
def test_modulo_sin_empleo_ni_probabilidades_de_automatizacion():
    prohibidos = ("enoe", "frey", "osborne")
    carpeta = ROOT / "src" / "calibrate"
    archivos = list(carpeta.glob("*.py")) + list(carpeta.glob("*.toml"))
    assert len(archivos) >= 3
    for f in archivos:
        txt = f.read_text(encoding="utf-8").lower()
        for w in prohibidos:
            assert w not in txt, f"{f.name} menciona {w}"


def test_config_valida():
    c = B.cargar_config()
    assert c["muestreo"]["n_cadenas"] >= 2
    assert c["prior"]["debil"]["diag"] < c["prior"]["fuerte"]["diag"]
