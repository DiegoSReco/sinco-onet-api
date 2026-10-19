"""Pruebas de la muestra de oro (src/match/oro.py) y de la consolidacion (src/match/oro_resultados.py).

Las pruebas de resultados usan datos SINTETICOS construidos aqui; no son revisiones reales.
"""
import re

import numpy as np
import pandas as pd
import pytest

from src.match import oro, oro_resultados as R

PROC = oro.PROC


# ---------------------------------------------------------------- muestreo
def test_asignar_suma_minimo_y_tope():
    tam = {"a": 100, "b": 50, "c": 3, "d": 1}
    f = {"a": 1.0, "b": 1.5, "c": 1.0, "d": 1.0}
    asig = oro.asignar(tam, f, 40, 2)
    assert sum(asig.values()) == 40
    assert all(asig[h] <= tam[h] for h in tam)
    assert asig["d"] == 1 and asig["c"] >= 2
    assert oro.asignar(tam, f, 40, 2) == asig  # determinista


def test_breve():
    assert oro.breve("a b c", 10) == "a b c"
    t = oro.breve("palabra " * 100, 30)
    assert t.endswith("...") and len(t) <= 33


# ---------------------------------------------------------------- salidas reales (si existen)
OUT = [PROC / n for n in ("oro_muestra.parquet", "oro_llave.parquet", "oro_revision/revisor_A.csv", "oro_revision/revisor_B.csv")]
reales = pytest.mark.skipif(not all(p.exists() for p in OUT), reason="muestra de oro aun no generada")


@reales
def test_muestra_tamano_estratos_y_disjuntos():
    m = pd.read_parquet(OUT[0])
    assert (m.muestra == "principal").sum() == 200
    assert 50 <= (m.muestra == "piloto").sum() <= 60
    assert m.sinco_code.is_unique
    assert set(m.division.astype(str)) == set("123456789")
    assert (m.estado_validacion == "sin_validar").all()
    p = m[m.muestra == "principal"]
    assert abs((p.mitad == "calibracion").sum() - (p.mitad == "prueba").sum()) <= p.estrato.nunique()
    # los pesos de diseno suman la poblacion de cada estrato
    s = p.groupby("estrato").agg(w=("peso_diseno", "sum"), N=("N_estrato", "first"))
    assert np.allclose(s.w, s.N)


@reales
def test_reproducible_con_semilla():
    cfg = oro.cargar_config()
    pop = oro.construir_poblacion(cfg, PROC)
    a, b = oro.construir_muestra(cfg, pop), oro.construir_muestra(cfg, pop)
    assert a[["ficha_id", "sinco_code", "mitad"]].equals(b[["ficha_id", "sinco_code", "mitad"]])
    guardada = pd.read_parquet(OUT[0])
    assert list(guardada.sinco_code) == list(a.sinco_code)


@reales
def test_fichas_ciegas_y_codificacion():
    for p in OUT[2:]:
        raw = p.read_bytes()
        assert raw.startswith(b"\xef\xbb\xbf")  # BOM para Excel
        df = R.leer_ficha(p)
        assert list(df.columns) == oro.COLUMNAS_FICHA
        prohibido = re.compile(r"(bge|e5|rango|similitud|margen|prob|frey|osborne|automat|expos|modelo|top-?\d)", re.I)
        assert not [c for c in df.columns if prohibido.search(c)]
        cuerpo = df[["onet_titulo_en", "onet_descripcion_breve", "cand_id"]].astype(str).agg(" ".join, axis=1)
        assert not cuerpo.str.contains(r"(bge-m3|multilingual|frey|osborne)", case=False).any()
        assert (df[["valoracion", "es_mejor", "ninguno_otro", "otro_soc", "confianza", "comentarios"]] == "").all().all()
        assert (df.cand_id == oro.OTRO_ID).sum() == df.ficha_id.nunique()
    a, b = R.leer_ficha(OUT[2]), R.leer_ficha(OUT[3])
    assert list(a.ficha_id.unique()) != list(b.ficha_id.unique())  # orden independiente por revisor


@reales
def test_llave_cubre_fichas_y_distractores():
    k = pd.read_parquet(OUT[1])
    a = R.leer_ficha(OUT[2])
    n_cand = (a.cand_id != oro.OTRO_ID).sum()
    assert n_cand == len(k)
    assert k.groupby("ficha_id").es_distractor.sum().eq(2).all()
    real = k[~k.es_distractor]
    assert real[["rango_bge_m3", "rango_e5"]].min(axis=1).le(5).all()
    for t in ("bge_m3", "e5"):  # cada ficha contiene el top-1 de ambos modelos
        assert real.groupby("ficha_id")[f"rango_{t}"].min().eq(1).all()


# ---------------------------------------------------------------- resultados con datos sinteticos
def llave_sintetica(n=12):
    filas = []
    for i in range(n):
        f = f"M{i + 1:03d}"
        # 3 candidatos bge (rangos 1-3), 3 e5 (el top-1 de e5 coincide con bge en fichas pares), 2 distractores
        socs = [f"11-{i:02d}{j}0.00" for j in range(1, 6)]
        reg = [
            (socs[0], 1, 1), (socs[1], 2, 3), (socs[2], 3, np.nan),
            (socs[3], np.nan, 2), (socs[4], np.nan, 1 if i % 2 else 3),
        ]
        if i % 2 == 0:
            reg[0] = (socs[0], 1, 1)
            reg[4] = (socs[4], np.nan, 3)
        else:
            reg[0] = (socs[0], 1, 2)
        for s, rb, re_ in reg:
            filas.append(dict(ficha_id=f, muestra="principal", sinco_code=str(1000 + i), onet_soc_code=s, es_distractor=False,
                              rango_bge_m3=rb, rango_e5=re_, peso_diseno=2.0, mitad="calibracion" if i < n // 2 else "prueba"))
        for j in range(2):
            filas.append(dict(ficha_id=f, muestra="principal", sinco_code=str(1000 + i), onet_soc_code=f"53-{i:02d}{j}0.00",
                              es_distractor=True, rango_bge_m3=np.nan, rango_e5=np.nan, peso_diseno=2.0,
                              mitad="calibracion" if i < n // 2 else "prueba"))
    k = pd.DataFrame(filas)
    for rev, off in (("A", 0), ("B", 3)):
        k[f"cand_id_{rev}"] = k.groupby("ficha_id").cumcount().map(lambda j: f"c{((j + off) % 7) + 1:02d}")
    return k


def llenar(llave, rev, regla, otro=None):
    """Construye una ficha 'llena' sintetica. regla(ficha, soc, es_distractor) -> valoracion."""
    filas = []
    for f, g in llave.groupby("ficha_id"):
        vals = {r.onet_soc_code: regla(f, r.onet_soc_code, r.es_distractor) for r in g.itertuples()}
        orden = [r for r in g.itertuples()]
        mejor = next((r.onet_soc_code for r in orden if vals[r.onet_soc_code] == "exacto"), None) or \
            next((r.onet_soc_code for r in orden if vals[r.onet_soc_code] == "parcial"), None)
        for r in orden:
            filas.append({**dict.fromkeys(oro.COLUMNAS_FICHA, ""), "ficha_id": f, "sinco_code": r.sinco_code,
                          "cand_id": getattr(r, f"cand_id_{rev}"), "onet_soc_code": r.onet_soc_code,
                          "valoracion": vals[r.onet_soc_code].capitalize(),
                          "es_mejor": "Sí" if r.onet_soc_code == mejor else ""})
        o = {**dict.fromkeys(oro.COLUMNAS_FICHA, ""), "ficha_id": f, "sinco_code": g.sinco_code.iloc[0], "cand_id": oro.OTRO_ID,
             "confianza": "Media"}
        if mejor is None:
            o["ninguno_otro"] = "si"
            o["otro_soc"] = "99-9999.00"
        filas.append(o)
    return pd.DataFrame(filas, columns=oro.COLUMNAS_FICHA)


def regla_a(f, soc, dist):
    if dist:
        return "incorrecto"
    return "exacto" if soc.endswith("10.00") else ("parcial" if soc.endswith("20.00") else "incorrecto")


def test_validacion_y_acuerdo_perfecto():
    k = llave_sintetica()
    A, B = llenar(k, "A", regla_a), llenar(k, "B", regla_a)
    da, db = R.validar_ficha(A, k, "A"), R.validar_ficha(B, k, "B")
    cons = R.consolidar(da, db, k)
    kp = R.kappas(cons)
    assert kp["kappa_nominal"] == pytest.approx(1.0)
    assert kp["kappa_ponderado_lineal"] == pytest.approx(1.0)
    assert R.acuerdo_mejor(da, db)["acuerdo_mejor_soc"] == 1.0


def test_kappa_calculado_a_mano():
    # 10 pares: A y B coinciden en 8; tabla binaria (aceptable): A=1 en 5, B=1 en 4, ambos 1 en 4, ambos 0 en 5.
    # po = 0.9 ; pe = 0.5*0.4 + 0.5*0.6 = 0.5 ; kappa = (0.9-0.5)/(0.5) = 0.8
    a = [1] * 5 + [0] * 5
    b = [1] * 4 + [0] + [0] * 5
    assert R._kappa(a, b) == pytest.approx(0.8)


def test_kappa_con_desacuerdos_en_fichas():
    k = llave_sintetica()
    A = llenar(k, "A", regla_a)

    def regla_b(f, soc, dist):  # B degrada los 'exacto' de fichas pares a 'parcial'
        v = regla_a(f, soc, dist)
        return "parcial" if (v == "exacto" and int(f[1:]) % 2 == 0) else v
    B = llenar(k, "B", regla_b)
    da, db = R.validar_ficha(A, k, "A"), R.validar_ficha(B, k, "B")
    cons = R.consolidar(da, db, k)
    kp = R.kappas(cons)
    assert kp["kappa_nominal"] < 1.0
    assert kp["kappa_binario_aceptable"] == pytest.approx(1.0)  # parcial y exacto son ambos aceptables
    assert kp["kappa_ponderado_lineal"] > kp["kappa_nominal"]
    # la tabla 3x3 coincide con sklearn aplicado a mano
    from sklearn.metrics import cohen_kappa_score
    assert kp["kappa_nominal"] == pytest.approx(cohen_kappa_score(cons.val_A, cons.val_B))


def test_metricas_por_modelo():
    k = llave_sintetica()
    A, B = llenar(k, "A", regla_a), llenar(k, "B", regla_a)
    cons = R.consolidar(R.validar_ficha(A, k, "A"), R.validar_ficha(B, k, "B"), k)
    # el unico exacto ('...10.00' = socs[0]?) : socs son f"11-{i:02d}{j}0.00", j=1..5 -> '10.00' solo si j=1 => socs[0]
    # socs[0] es rango 1 de bge y rango 1 (pares) o 2 (impares) de e5; socs[1] ('20.00') es parcial, rango 2 bge
    m = R.metricas_modelo(cons, "acept_estricto", "bge_m3", (1, 3, 5))
    assert m["precision@1"] == 1.0 and m["MRR"] == 1.0
    assert m["precision@3"] == pytest.approx(2 / 3)       # socs[0] y socs[1] aceptables entre top-3 de bge
    assert m["recall@3"] == pytest.approx(1.0)
    e = R.metricas_modelo(cons, "acept_estricto", "e5", (1, 3, 5))
    assert e["precision@1"] == pytest.approx(0.5)         # en fichas impares el top-1 de e5 es socs[4] (incorrecto)
    assert e["MRR"] == pytest.approx(0.5 * 1.0 + 0.5 * 0.5)
    assert e["n_fichas"] == 12


def test_ninguno_otro_cuenta_como_fallo():
    k = llave_sintetica()
    A = llenar(k, "A", lambda f, s, d: "incorrecto")
    B = llenar(k, "B", lambda f, s, d: "incorrecto")
    da, db = R.validar_ficha(A, k, "A"), R.validar_ficha(B, k, "B")
    cons = R.consolidar(da, db, k)
    assert R.metricas_modelo(cons, "acept_estricto", "bge_m3", (1,))["precision@1"] == 0.0
    assert R.acuerdo_mejor(da, db)["fichas_ninguno_otro_A"] == 1.0


def test_calcular_completo_con_bootstrap_pequeno():
    k = llave_sintetica()
    A, B = llenar(k, "A", regla_a), llenar(k, "B", regla_a)
    da, db = R.validar_ficha(A, k, "A"), R.validar_ficha(B, k, "B")
    cfg = oro.cargar_config()
    cfg["resultados"]["bootstrap_B"] = 20
    res = R.calcular(R.consolidar(da, db, k), None, cfg, da, db)
    assert res["acuerdo_revisores"]["kappa_nominal"] == pytest.approx(1.0)
    assert res["acuerdo_revisores"]["cumple_umbral_provisional"] is True
    assert res["distractores"]["aceptados_A"] == 0.0
    assert "estricto" in str(res["metricas_por_modelo"].keys()) or "acept_estricto" in res["metricas_por_modelo"]


def test_esquema_rechaza_errores():
    k = llave_sintetica(3)
    A = llenar(k, "A", regla_a)
    # valoracion invalida
    mal = A.copy()
    mal.loc[0, "valoracion"] = "quizas"
    with pytest.raises(R.FichaError, match="valoracion invalida"):
        R.validar_ficha(mal, k, "A")
    # dos mejores
    mal = A.copy()
    idx = mal[(mal.ficha_id == "M001") & (mal.cand_id != oro.OTRO_ID)].index[:2]
    mal.loc[idx, "es_mejor"] = "si"
    with pytest.raises(R.FichaError, match="exactamente una"):
        R.validar_ficha(mal, k, "A")
    # codigo O*NET alterado
    mal = A.copy()
    mal.loc[0, "onet_soc_code"] = "00-0000.00"
    with pytest.raises(R.FichaError):
        R.validar_ficha(mal, k, "A")
    # columna faltante
    with pytest.raises(R.FichaError, match="faltan columnas"):
        R.validar_ficha(A.drop(columns=["confianza"]), k, "A")
    # ficha ausente
    with pytest.raises(R.FichaError, match="ausentes"):
        R.validar_ficha(A[A.ficha_id != "M002"], k, "A")
    # sin confianza
    mal = A.copy()
    mal.loc[mal.cand_id == oro.OTRO_ID, "confianza"] = ""
    with pytest.raises(R.FichaError, match="confianza"):
        R.validar_ficha(mal, k, "A")


def test_lectura_csv_excel_punto_y_coma_y_cp1252(tmp_path):
    k = llave_sintetica(2)
    A = llenar(k, "A", regla_a)
    A.loc[0, "comentarios"] = "decisión con acento, y coma"
    p1 = tmp_path / "a.csv"
    A.to_csv(p1, index=False, encoding="utf-8-sig", sep=";")
    p2 = tmp_path / "b.csv"
    A.to_csv(p2, index=False, encoding="cp1252", sep=",")
    for p in (p1, p2):
        d = R.leer_ficha(p)
        assert d.loc[0, "comentarios"] == "decisión con acento, y coma"
        R.validar_ficha(d, k, "A")


def test_main_extremo_a_extremo_sintetico(tmp_path):
    k = llave_sintetica(6)
    llave_p = tmp_path / "llave.parquet"
    k.to_parquet(llave_p)
    oro.escribir_csv(llenar(k, "A", regla_a), tmp_path / "A.csv")
    oro.escribir_csv(llenar(k, "B", regla_a), tmp_path / "B.csv")
    cfg = oro.cargar_config()
    cfg["resultados"]["bootstrap_B"] = 10
    res = R.main(tmp_path / "A.csv", tmp_path / "B.csv", "principal", llave_p, tmp_path / "no_existe.parquet",
                 tmp_path / "res.json", cfg)
    assert (tmp_path / "res.json").exists()
    assert res["acuerdo_revisores"]["kappa_nominal"] == pytest.approx(1.0)
