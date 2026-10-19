"""Pruebas del modo subagente (export/import) con salidas sinteticas."""
import datetime as dt
import json

import pandas as pd
import pytest

from src.annotate import config as C
from src.annotate import prompt as P
from src.annotate import schemas, subagent

CFG = C.cargar()


def piloto_sint(n=6):
    return pd.DataFrame([dict(task_id=str(100 + i), onet_soc="11-1011.00", onet_title="Chief Executives",
                              task_text_en=f"Do thing {i}.", task_type="core" if i % 2 else None) for i in range(n)])


@pytest.fixture
def entorno(tmp_path):
    ind = tmp_path / "in"
    rutas = subagent.export_inputs(CFG, piloto_sint(), dt.date(2026, 10, 19), "2026-10-19", in_dir=ind)
    return tmp_path, ind, rutas


def linea(tid, **kw):
    d = dict(task_id=tid, exposure_class="E1", physical_bottleneck=False, confidence="media", rationale="Cita la tarea.")
    d.update(kw)
    return json.dumps(d)


def importar(tmp, ind, rid, lineas):
    out = tmp / "out"
    out.mkdir(exist_ok=True)
    if lineas is not None:
        (out / f"{rid}.jsonl").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return subagent.import_output(rid, in_dir=ind, out_dir=out, parquet_dir=tmp / "pq", issues_dir=tmp / "iss")


def test_export_tres_corridas_ordenes_distintos_prompt_y_cutoff(entorno):
    tmp, ind, rutas = entorno
    assert [r.stem for r in rutas] == ["piloto-2026-10-19-01", "piloto-2026-10-19-02", "piloto-2026-10-19-03"]
    docs = [json.loads(r.read_text(encoding="utf-8")) for r in rutas]
    ordenes = [tuple(t["task_id"] for t in d["tareas"]) for d in docs]
    assert len(set(ordenes)) == 3 and all(sorted(o) == sorted(ordenes[0]) for o in ordenes)
    d = docs[0]
    assert "2026-10-19" in d["system_prompt"] and "<<" not in d["system_prompt"]
    assert d["prompt_sha256"] == P.cargar().sha256 and d["model"].startswith("claude-sonnet-5-5")
    assert all("<<" not in t["user_prompt"] for t in d["tareas"])
    assert d["formato_salida"]["archivo_salida"].endswith(f"{d['run_id']}.jsonl")


def test_export_exige_fecha_corte_y_no_sobrescribe(entorno, tmp_path):
    tmp, ind, _ = entorno
    with pytest.raises(ValueError):
        subagent.export_inputs(CFG, piloto_sint(), dt.date(2026, 10, 19), "requiere decision", in_dir=tmp_path / "x")
    with pytest.raises(FileExistsError):
        subagent.export_inputs(CFG, piloto_sint(), dt.date(2026, 10, 19), "2026-10-19", in_dir=ind)


def test_import_valido(entorno):
    tmp, ind, rutas = entorno
    rid = rutas[0].stem
    res, path = importar(tmp, ind, rid, [linea(str(100 + i)) for i in range(6)])
    assert not res.failures and len(res.records) == 6
    recs = schemas.read_parquet(path)
    r = recs[0]
    assert r.model.startswith("claude-sonnet-5-5") and r.temperature is None and "no controlable" in r.temperature_note
    assert r.seed is None and r.capability_cutoff == "2026-10-19" and r.annotated_text_lang == "en" and r.task_text_es is None
    assert not (tmp / "iss").exists()


def test_import_invalidas_y_faltantes_no_se_inventan(entorno):
    tmp, ind, rutas = entorno
    rid = rutas[1].stem
    lin = [linea("100"), linea("101", exposure_class="E9"), linea("102", score=0.4), "no json", linea("999"),
           linea("103"), linea("103"), linea("104", physical_bottleneck="si")]
    res, path = importar(tmp, ind, rid, lin)
    assert [r.task_id for r in res.records] == ["100"]
    falladas = {f.task_id: f.stage for f in res.failures}
    assert {"101", "102", "103", "104", "105", "999"} <= set(falladas) and falladas["105"] == "faltante"
    iss = (tmp / "iss" / f"anotacion-{rid}.md").read_text(encoding="utf-8")
    assert "| 105 |" in iss and "| 103 |" in iss
    assert len(schemas.read_parquet(path)) == 1


def test_import_sin_archivo_de_salida(entorno):
    tmp, ind, rutas = entorno
    res, path = importar(tmp, ind, rutas[2].stem, None)
    assert path is None and not res.records
    assert (tmp / "iss" / f"anotacion-{rutas[2].stem}.md").exists()


def test_import_detecta_cambio_de_prompt(entorno):
    tmp, ind, rutas = entorno
    d = json.loads(rutas[0].read_text(encoding="utf-8"))
    d["prompt_sha256"] = "0" * 64
    rutas[0].write_text(json.dumps(d), encoding="utf-8")
    with pytest.raises(ValueError):
        importar(tmp, ind, rutas[0].stem, [linea("100")])
