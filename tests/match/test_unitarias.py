"""Pruebas unitarias de src/match/ con datos sinteticos (no requieren modelos ni red)."""
import numpy as np
import pandas as pd
import pytest

from src.match import config as C
from src.match import pfo, retrieve, schemas, texts


class TokFalso:
    """Tokenizador de palabras: 1 token = 1 palabra."""
    def encode(self, t, add_special_tokens=False):
        return t.split()

    def decode(self, ids):
        return " ".join(ids)


def test_config_valida_y_marca_provisional():
    cfg = C.cargar()
    assert cfg["meta"]["estado_validacion"] == "sin_validar"
    assert "provisional" in cfg["meta"]["estado_parametros"]
    for m in cfg["modelos"].values():
        assert len(m["revision"]) == 40
    assert len(C.hash_config()) == 64


def test_config_rechaza_revision_no_fijada():
    cfg = C.cargar()
    cfg["modelos"]["bge-m3"]["revision"] = "main"
    with pytest.raises(ValueError):
        C.validar(cfg)


def test_truncamiento_por_prioridad_y_registro():
    campos = {"titulo": "uno dos", "ocupaciones": "a b c", "descripcion": "d1 d2 d3 d4 d5", "funciones": "f1 f2 f3 f4"}
    txt, info = texts.construir_texto(campos, TokFalso(), max_length=2 + 1 + 3 + 4 + 5, prefijo="query:")
    assert txt.startswith("query:")
    assert info["truncado"] is True
    assert "funciones" in info["campos_truncados"]
    assert "titulo" not in info["campos_truncados"]
    assert "uno dos" in txt


def test_sin_truncamiento_si_cabe():
    _, info = texts.construir_texto({"titulo": "x", "descripcion": "y"}, TokFalso(), 100, "")
    assert info["truncado"] is False


def test_topk_margen_y_empates_estables():
    sim = np.array([[0.5, 0.9, 0.9, 0.1]], dtype=np.float32)
    idx, s = retrieve.topk(sim, 3)
    assert idx[0].tolist() == [1, 2, 0]  # empate 1/2 resuelto por indice
    assert np.allclose(s[0], [0.9, 0.9, 0.5])


def test_candidatos_top2_banderas_y_estado():
    rng = np.random.default_rng(0)
    sim = rng.random((50, 30)).astype(np.float32)
    top, res, umb = retrieve.candidatos(sim, [str(1000 + i) for i in range(50)], [f"11-{1000+j}.00" for j in range(30)],
                                        k=10, k_top=2, q_baja=0.1, q_margen=0.1, q_sin=0.05)
    assert len(top) == 500
    assert top.groupby("sinco_code")["rango"].apply(lambda r: r.tolist() == list(range(1, 11))).all()
    assert top[top.rango <= 2]["en_conjunto"].all() and not top[top.rango > 2]["en_conjunto"].any()
    assert (top.groupby("sinco_code")["en_conjunto"].sum() == 2).all()
    assert set(res["match_status"]) <= {"ok", "baja_confianza", "sin_coincidencia"}
    assert (res["n_conjunto"] == 2).all()
    assert (res["sim_top1"] >= res["sim_top2"]).all()
    assert umb["sim_top1_sin_coincidencia"] <= umb["sim_top1_baja"]


def test_agregacion_top2_ponderada_entre_los_dos():
    from src.match import pfo
    puente = {"11-1011.00": ["11-1011"], "11-1021.00": ["11-1021"]}
    fo = {"11-1011": 0.2, "11-1021": 0.8}
    r = pfo.agregar_sinco([0.70, 0.60], ["11-1011.00", "11-1021.00"], 0.05, puente, fo)
    w = pfo.softmax([0.70, 0.60], 0.05)
    assert r["n_candidatos"] == 2
    assert abs(r["p_ponderada"] - (w[0] * 0.2 + w[1] * 0.8)) < 1e-12
    assert abs(r["p_media"] - 0.5) < 1e-12 and r["p_min"] == 0.2 and r["p_max"] == 0.8 and r["p_top1"] == 0.2
    assert abs(r["cobertura_peso_fo"] - 1) < 1e-12


def test_config_k_top_2():
    from src.match import config as C
    assert C.cargar()["recuperacion"]["k_top"] == 2


def test_tipo_relacion():
    p = pd.DataFrame({"sinco_code": ["1111", "1111", "2222", "3333", "4444"],
                      "onet_soc_code": ["a", "b", "c", "c", "d"]})
    assert retrieve.tipo_relacion(p).tolist() == ["1:N", "1:N", "N:1", "N:1", "1:1"]
    p2 = pd.DataFrame({"sinco_code": ["1", "1", "2"], "onet_soc_code": ["a", "b", "a"]})
    assert "M:N" in retrieve.tipo_relacion(p2).tolist()


def test_softmax_suma_uno_y_orden():
    w = pfo.softmax([0.9, 0.8, 0.7], 0.05)
    assert w.sum() == pytest.approx(1) and w[0] > w[1] > w[2]


PUENTE = {"A": ["11-0001"], "B": ["11-0002", "11-0003"], "C": ["11-0004"], "D": []}
FO = {"11-0001": 0.2, "11-0002": 0.6, "11-0003": 0.8}   # 11-0004 sin F-O


def test_agregacion_pfo_reglas():
    r = pfo.agregar_sinco([0.9, 0.9], ["A", "B"], 0.05, PUENTE, FO)
    assert r["p_ponderada"] == pytest.approx(0.5 * 0.2 + 0.25 * 0.6 + 0.25 * 0.8)
    assert r["p_media"] == pytest.approx(r["p_ponderada"])
    assert r["p_min"] == 0.2 and r["p_max"] == 0.8
    assert r["p_top1"] == pytest.approx(0.2)
    assert r["bandera_multi_soc2010"] is True and r["cobertura_fo"] == "completa"
    assert r["n_soc2010"] == 3


def test_agregacion_cobertura_parcial_y_na_sin_imputar():
    r = pfo.agregar_sinco([0.9, 0.9, 0.9], ["A", "C", "D"], 0.05, PUENTE, FO)
    assert r["cobertura_fo"] == "parcial" and r["bandera_soc_sin_fo"] and r["bandera_sin_puente"]
    assert r["p_ponderada"] == pytest.approx(0.2)           # solo A tiene p; no se imputa nada
    assert r["cobertura_peso_fo"] == pytest.approx(1 / 3)
    n = pfo.agregar_sinco([0.9], ["C"], 0.05, PUENTE, FO)
    assert n["cobertura_fo"] == "ninguna" and np.isnan(n["p_ponderada"]) and np.isnan(n["p_top1"])


def test_colapso_mismo_soc():
    puente = {"X": ["11-0001"], "Y": ["11-0001"]}
    r = pfo.agregar_sinco([0.9, 0.5], ["X", "Y"], 0.05, puente, {"11-0001": 0.3})
    assert r["n_soc2010"] == 1 and r["p_ponderada"] == pytest.approx(0.3)


def test_mapa_puente_distintos():
    df = pd.DataFrame({"onet_soc_2019_code": ["A", "A", "B"], "soc_2010": ["11-0001", "11-0001", "11-0002"]})
    assert pfo.mapa_puente(df) == {"A": ["11-0001"], "B": ["11-0002"]}


def _cw_ok():
    return pd.DataFrame([{"sinco_code": "1111", "onet_soc_code": "11-1011.00", "tipo_relacion": "1:1", "fuente": "x",
                          "estado_validacion": "sin_validar", "notas": None, "run_id": "r", "modelo": "m", "rango": 1,
                          "similitud": 0.5, "margen": 0.1, "similitud_alt": None, "rango_alt": None, "modelo_alt": None,
                          "baja_confianza": False, "match_status": "ok"}])


def test_crosswalk_valido_y_rechazos():
    df = _cw_ok()
    schemas.validar_crosswalk(df, {"1111"}, {"11-1011.00"})
    with pytest.raises(schemas.SchemaError):   # columna de probabilidad
        schemas.validar_crosswalk(df.assign(probabilidad_automatizacion_fo=0.1), {"1111"}, {"11-1011.00"})
    with pytest.raises(schemas.SchemaError):   # codigo inexistente
        schemas.validar_crosswalk(df, {"2222"}, {"11-1011.00"})
    with pytest.raises(schemas.SchemaError):   # estado distinto de sin_validar
        schemas.validar_crosswalk(df.assign(estado_validacion="validado"), {"1111"}, {"11-1011.00"})
    with pytest.raises(schemas.SchemaError):   # duplicado
        schemas.validar_crosswalk(pd.concat([df, df]), {"1111"}, {"11-1011.00"})
