"""Pruebas de src/annotate/ (sin red, sin LLM real)."""
import datetime as dt
import json

import pandas as pd
import pytest
from pydantic import ValidationError

from src.annotate import config as C
from src.annotate import pilot, prompt as P, providers, runner, schemas
from src.annotate.runner import TaskInput

CFG = C.cargar()


def tarea(i, tipo="core"):
    return TaskInput(task_id=str(i), onet_soc="11-1011.00", onet_title="Chief Executives",
                     task_text_en=f"Prepare report number {i}.", task_type=tipo)


def reg(**kw):
    base = dict(run_id="r1", prompt_version="ann-v1", prompt_sha256="a" * 64, model="m", run_date=dt.date(2026, 10, 19),
                onet_version="31.0", onet_soc="11-1011.00", task_id="1", task_text_en="x", annotated_text_lang="en",
                exposure_class="E1", physical_bottleneck=False, confidence="alta", rationale="Cita la tarea.")
    base.update(kw)
    return schemas.Annotation(**base)


def correr(tasks, provider, run_id="t-01", **kw):
    return runner.annotate_run(run_id=run_id, tasks=tasks, provider=provider, prompt=P.cargar(), model="dry", cfg=CFG,
                               run_date=dt.date(2026, 10, 19), temperature=0.0, seed=1, sleep=lambda s: None, **kw)


# ---- esquema
def test_esquema_valido_y_estricto():
    assert reg().exposure_class == "E1"
    for malo in (dict(exposure_class="E3"), dict(exposure_class=0.5), dict(confidence="muy alta"),
                 dict(physical_bottleneck="si"), dict(task_type="otro"), dict(onet_soc="11-1011"),
                 dict(rationale="  "), dict(score=0.37), dict(annotated_text_lang="es"), dict(run_id="a b")):
        with pytest.raises(ValidationError):
            reg(**malo)


def test_sin_puntaje_continuo_en_esquema():
    assert not any("score" in n or "puntaje" in n for n in schemas.Annotation.model_fields)
    assert set(schemas.ModelOutput.model_fields) == {"exposure_class", "physical_bottleneck", "confidence", "rationale"}


def test_unicidad_run_task():
    with pytest.raises(ValueError):
        schemas.validar_unicidad([reg(), reg()])
    schemas.validar_unicidad([reg(), reg(task_id="2"), reg(run_id="r2")])


def test_parquet_roundtrip_y_no_sobrescribe(tmp_path):
    p = tmp_path / "run_r1.parquet"
    schemas.write_parquet([reg(), reg(task_id="2", task_type="core", temperature=0.5, seed=3)], p)
    assert [r.task_id for r in schemas.read_parquet(p)] == ["1", "2"]
    with pytest.raises(FileExistsError):
        schemas.write_parquet([reg()], p)


def test_config_mapa_no_aplicado_y_decisiones_pendientes():
    assert CFG["mapa_numerico"]["principal"] == {"E0": 0.0, "E1": 0.5, "E2": 1.0}
    assert C.decision_pendiente(CFG["capacidades"]["fecha_corte"])
    assert C.decision_pendiente(CFG["modelo"]["nombre"])
    src = "".join(open(f"src/annotate/{m}.py", encoding="utf-8").read() for m in ("runner", "schemas", "pilot", "run"))
    assert "mapa_numerico" not in src


# ---- prompt
def test_prompt_sin_umbral_y_con_cutoff():
    p = P.cargar()
    raw = p.raw.lower()
    assert "<<capability_cutoff>>" in p.system
    for prohibido in ("50 %", "50%", "mitad del tiempo", "eloundou"):
        assert prohibido not in raw
    s, u = p.render(capability_cutoff="X", occupation_title="T", task_text="Do it.", lang="en")
    assert "<<" not in s + u and "Do it." in u
    assert "requiere decisión" in P.cutoff_text(CFG)


def test_guardar_doc_inmutable(tmp_path):
    p = P.cargar()
    out = P.guardar_doc(p, CFG, tmp_path)
    assert p.sha256 in out.read_text(encoding="utf-8")
    P.guardar_doc(p, CFG, tmp_path)
    out.write_text("otro", encoding="utf-8")
    with pytest.raises(RuntimeError):
        P.guardar_doc(p, CFG, tmp_path)


# ---- parseo
@pytest.mark.parametrize("txt", ["no json", "[]", '{"exposure_class":"E1"}', '```json\n{}\n```',
                                 '{"exposure_class":"E1","physical_bottleneck":"false","confidence":"alta","rationale":"x"}',
                                 '{"exposure_class":"E1","physical_bottleneck":false,"confidence":"alta","rationale":"x","score":1}'])
def test_parse_rechaza(txt):
    with pytest.raises(ValueError):
        runner.parse_output(txt)


def test_parse_acepta():
    o = runner.parse_output('{"exposure_class":"E2","physical_bottleneck":true,"confidence":"baja","rationale":"ok"}')
    assert o.exposure_class == "E2" and o.physical_bottleneck is True


# ---- corrida
def test_corrida_dryrun_una_por_tarea():
    tasks = [tarea(i) for i in range(30)]
    res = correr(tasks, providers.DryRunProvider())
    assert len(res.records) == 30 and not res.failures
    assert {r.task_id for r in res.records} == {t.task_id for t in tasks}
    assert all(r.capability_cutoff is None and r.annotated_text_lang == "en" for r in res.records)


def test_reintentos_y_backoff_acotado():
    esperas = []
    prov = providers.DryRunProvider(fail_rate=1.0, invalid_rate=0.0)
    res = runner.annotate_run(run_id="t-01", tasks=[tarea(1)], provider=prov, prompt=P.cargar(), model="d", cfg=CFG,
                              run_date=dt.date(2026, 10, 19), temperature=0, seed=1, sleep=esperas.append)
    assert len(res.records) == 1                       # el segundo intento ya no falla
    assert esperas == [CFG["reintentos"]["backoff_base_s"]]


def test_fallo_api_permanente_no_inventa():
    class Caido(providers.LLMProvider):
        def complete(self, *a, **k):
            raise providers.TransientProviderError("caido")
    esperas = []
    res = runner.annotate_run(run_id="t-01", tasks=[tarea(1)], provider=Caido(), prompt=P.cargar(), model="d", cfg=CFG,
                              run_date=dt.date(2026, 10, 19), temperature=0, seed=1, sleep=esperas.append)
    assert not res.records and res.failures[0].stage == "api"
    assert len(esperas) == CFG["reintentos"]["max_reintentos_api"] and max(esperas) <= CFG["reintentos"]["backoff_max_s"]


def test_formato_invalido_reintenta_y_luego_registra(tmp_path):
    prov = providers.DryRunProvider(always_invalid_marker="MALA")
    tasks = [tarea(1), TaskInput("2", "11-1011.00", "T", "MALA tarea")]
    res = correr(tasks, prov)
    assert [r.task_id for r in res.records] == ["1"]
    assert res.failures[0].task_id == "2" and res.failures[0].stage == "formato"
    assert res.failures[0].attempts == CFG["reintentos"]["max_reintentos_formato"] + 1
    out = runner.guardar_corrida(res, 2, tmp_path, issues_dir=tmp_path)
    assert out.exists() and (tmp_path / "anotacion-t-01.md").exists()
    assert "| 2 |" in (tmp_path / "anotacion-t-01.md").read_text(encoding="utf-8")


def test_formato_invalido_transitorio_se_recupera():
    res = correr([tarea(i) for i in range(20)], providers.DryRunProvider(invalid_rate=1.0))
    assert len(res.records) == 20 and not res.failures


def test_sin_issue_si_todo_ok(tmp_path):
    res = correr([tarea(1)], providers.DryRunProvider())
    runner.guardar_corrida(res, 1, tmp_path, issues_dir=tmp_path)
    assert not list(tmp_path.glob("anotacion-*.md"))


def test_multiples_corridas_independientes(tmp_path):
    tasks = [tarea(i) for i in range(30)]
    sal = runner.run_many(base_run_id="b", n_runs=3, tasks=tasks, provider_factory=providers.DryRunProvider,
                          prompt=P.cargar(), model="dry", cfg=CFG, run_date=dt.date(2026, 10, 19), temperature=0.0,
                          out_dir=tmp_path, issues_dir=tmp_path)
    assert [r.run_id for r, _ in sal] == ["b-01", "b-02", "b-03"]
    dfs = [pd.read_parquet(p) for _, p in sal]
    assert all(len(d) == 30 and d.task_id.is_unique for d in dfs)
    assert len({tuple(d.seed) for d in dfs}) == 3
    assert not dfs[0].exposure_class.equals(dfs[1].exposure_class)      # semillas distintas -> salidas distintas
    # no hay lectura de otras corridas: re-ejecutar una corrida reproduce lo mismo
    r2 = correr(tasks, providers.DryRunProvider(), run_id="b-01")
    assert r2.records[0].task_id == "0"


def test_proveedor_real_no_existe():
    with pytest.raises(NotImplementedError):
        providers.crear("openai")


def test_cli_rechaza_full_y_proveedor_real(capsys):
    from src.annotate import run
    assert run.main(["--run-id", "x", "--sample", "full", "--model", "m"]) == 2
    assert run.main(["--run-id", "x", "--provider", "anthropic", "--model", "m"]) == 2


# ---- piloto
def tabla_sintetica():
    filas = []
    for g in range(11, 40):
        for o in range(6):
            soc = f"{g}-{1000 + o}.00"
            for k in range(4):
                tp = "core" if k < 3 else ("supplemental" if o % 2 else None)
                filas.append(dict(task_id=f"{g}{o}{k}", onet_soc=soc, onet_title="t", task_text_en="x", task_type=tp,
                                  task_text_es=None, major_group=str(g)))
    return pd.DataFrame(filas)


def test_piloto_reproducible_y_estratificado():
    t = tabla_sintetica()
    a, b = pilot.seleccionar_piloto(t, CFG), pilot.seleccionar_piloto(t, CFG)
    pd.testing.assert_frame_equal(a, b)
    assert len(a) == CFG["piloto"]["n_total"] and a.task_id.is_unique
    assert a.stratum.value_counts().to_dict() == {"core": 28, "supplemental": 10, "sin_tipo": 2}
    assert a.groupby("stratum").onet_soc.apply(lambda s: s.is_unique).all()
    cfg2 = json.loads(json.dumps(CFG)); cfg2["piloto"]["seed"] = 1
    assert not pilot.seleccionar_piloto(t, cfg2).task_id.equals(a.task_id)
