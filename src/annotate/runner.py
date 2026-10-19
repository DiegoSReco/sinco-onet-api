"""Logica de corridas: una corrida = una pasada independiente sobre todas las tareas; n corridas = n run_id.

Independencia: cada corrida usa su propio run_id, su propia semilla (seed_base + i), su propio proveedor
(fabrica) y un orden de tareas propio; no lee anotaciones de otras corridas ni de otros lotes.
No se calcula ningun puntaje numerico ni agregado.
"""
from __future__ import annotations

import datetime as dt
import json
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from pydantic import ValidationError

from . import config as C
from .prompt import PromptTemplate, cutoff_text
from .providers import LLMProvider, PermanentProviderError, TransientProviderError
from .schemas import Annotation, ModelOutput, read_parquet, write_parquet


@dataclass(frozen=True)
class TaskInput:
    task_id: str
    onet_soc: str
    onet_title: str
    task_text_en: str
    task_type: str | None = None
    task_text_es: str | None = None


@dataclass
class Failure:
    task_id: str
    stage: str          # "api" | "formato"
    attempts: int
    detail: str


@dataclass
class RunResult:
    run_id: str
    records: list[Annotation] = field(default_factory=list)
    failures: list[Failure] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    calls: int = 0
    seconds: float = 0.0


def parse_output(text: str) -> ModelOutput:
    """JSON estricto: el texto completo debe ser un unico objeto JSON valido para ModelOutput."""
    try:
        obj = json.loads(text.strip())
    except json.JSONDecodeError as e:
        raise ValueError(f"no es JSON: {e}") from e
    if not isinstance(obj, dict):
        raise ValueError("el JSON no es un objeto")
    try:
        return ModelOutput.model_validate(obj)
    except ValidationError as e:
        raise ValueError(f"no cumple el esquema: {e.errors(include_url=False, include_input=False)}") from e


def annotate_run(*, run_id: str, tasks: list[TaskInput], provider: LLMProvider, prompt: PromptTemplate,
                 model: str, cfg: dict, run_date: dt.date, temperature: float | None, seed: int | None,
                 sleep: Callable[[float], None] = time.sleep) -> RunResult:
    rt = cfg["reintentos"]
    lang = cfg["texto"]["idioma_anotado"]
    cutoff = cutoff_text(cfg)
    cut_reg = None if C.decision_pendiente(cfg["capacidades"]["fecha_corte"]) else str(cfg["capacidades"]["fecha_corte"])
    res = RunResult(run_id)
    t0 = time.time()
    orden = list(tasks)
    random.Random(seed if seed is not None else 0).shuffle(orden)   # orden propio por corrida
    for t in orden:
        texto = t.task_text_es if lang == "es" else t.task_text_en
        if not texto:
            res.failures.append(Failure(t.task_id, "formato", 0, f"sin texto en idioma '{lang}'"))
            continue
        system, user = prompt.render(capability_cutoff=cutoff, occupation_title=t.onet_title, task_text=texto, lang=lang)
        out, falla = None, None
        for intento_fmt in range(rt["max_reintentos_formato"] + 1):
            resp = None
            for intento_api in range(rt["max_reintentos_api"] + 1):
                res.calls += 1
                try:
                    resp = provider.complete(system, user, temperature=temperature, seed=seed)
                    break
                except TransientProviderError as e:
                    falla = Failure(t.task_id, "api", intento_api + 1, f"transitorio: {e}")
                    if intento_api < rt["max_reintentos_api"]:
                        sleep(min(rt["backoff_base_s"] * 2 ** intento_api, rt["backoff_max_s"]))
                except PermanentProviderError as e:
                    falla = Failure(t.task_id, "api", intento_api + 1, f"permanente: {e}")
                    break
            if resp is None:
                break
            res.input_tokens += resp.input_tokens or 0
            res.output_tokens += resp.output_tokens or 0
            try:
                out = parse_output(resp.text)
                falla = None
                break
            except ValueError as e:
                falla = Failure(t.task_id, "formato", intento_fmt + 1, f"{e} | crudo: {resp.text[:200]!r}")
        if out is None:
            res.failures.append(falla)
            continue
        res.records.append(Annotation(
            run_id=run_id, prompt_version=prompt.version, prompt_sha256=prompt.sha256, model=model,
            run_date=run_date, onet_version=cfg["meta"]["onet_version"], onet_soc=t.onet_soc, task_id=t.task_id,
            task_text_en=t.task_text_en, task_text_es=t.task_text_es,
            translation_version=cfg["texto"]["translation_version"] or None, annotated_text_lang=lang,
            task_type=t.task_type, exposure_class=out.exposure_class, physical_bottleneck=out.physical_bottleneck,
            confidence=out.confidence, rationale=out.rationale, capability_cutoff=cut_reg,
            temperature=temperature, seed=seed))
    res.records.sort(key=lambda r: r.task_id)
    res.seconds = time.time() - t0
    return res


def escribir_issue(run_id: str, res: RunResult | None, n_tareas: int, motivo_extra: str | None = None,
                   issues_dir: Path | None = None) -> Path | None:
    """docs/issues/anotacion-{run_id}.md si hay tareas no anotadas o el entregable no cumple el esquema."""
    if res is not None and not res.failures and not motivo_extra:
        return None
    issues_dir = Path(issues_dir) if issues_dir else C.ISSUES_DIR
    issues_dir.mkdir(parents=True, exist_ok=True)
    p = issues_dir / f"anotacion-{run_id}.md"
    L = [f"# Issue de anotacion: corrida {run_id}", "", f"- Tareas de entrada: {n_tareas}"]
    if res is not None:
        L += [f"- Tareas anotadas: {len(res.records)}", f"- Tareas no anotadas: {len(res.failures)}"]
    if motivo_extra:
        L += ["", "## Entregable fuera de esquema", motivo_extra]
    if res is not None and res.failures:
        L += ["", "## Tareas no anotadas (no se inventan puntajes)", "", "| task_id | etapa | intentos | detalle |", "|---|---|---|---|"]
        L += [f"| {f.task_id} | {f.stage} | {f.attempts} | {f.detail.replace('|', '/')[:300]} |" for f in res.failures]
    p.write_text("\n".join(L) + "\n", encoding="utf-8")
    return p


def guardar_corrida(res: RunResult, n_tareas: int, out_dir: Path, issues_dir: Path | None = None) -> Path:
    """Escribe el Parquet, lo relee contra el esquema y, si algo falla o faltan tareas, deja issue."""
    out = Path(out_dir) / f"run_{res.run_id}.parquet"
    try:
        write_parquet(res.records, out)
        read_parquet(out)
    except Exception as e:  # entregable fuera de esquema: issue y detener (regla 5)
        escribir_issue(res.run_id, res, n_tareas, motivo_extra=f"{type(e).__name__}: {e}", issues_dir=issues_dir)
        raise
    escribir_issue(res.run_id, res, n_tareas, issues_dir=issues_dir)
    return out


def run_many(*, base_run_id: str, n_runs: int, tasks: list[TaskInput], provider_factory: Callable[[], LLMProvider],
             prompt: PromptTemplate, model: str, cfg: dict, run_date: dt.date, temperature: float | None,
             out_dir: Path, seed_base: int | None = None, issues_dir: Path | None = None,
             sleep: Callable[[float], None] = time.sleep) -> list[tuple[RunResult, Path]]:
    seed_base = cfg["corridas"]["seed_base"] if seed_base is None else seed_base
    salidas = []
    for i in range(1, n_runs + 1):
        rid = f"{base_run_id}-{i:02d}"
        res = annotate_run(run_id=rid, tasks=tasks, provider=provider_factory(), prompt=prompt, model=model, cfg=cfg,
                           run_date=run_date, temperature=temperature, seed=seed_base + i, sleep=sleep)
        salidas.append((res, guardar_corrida(res, len(tasks), out_dir, issues_dir)))
    return salidas
