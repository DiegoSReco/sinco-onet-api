"""Modo 'subagente' (sin API, sin red): las anotaciones las hacen subagentes de Claude Code.

  export: escribe data/processed/annotations/pilot_inputs/<run_id>.json (prompt completo + tareas en orden propio
          + formato exacto de salida).
  import: lee data/processed/annotations/pilot_outputs/<run_id>.jsonl, valida estrictamente y escribe
          data/processed/annotations/pilot/run_<run_id>.parquet. No hay reintento: tareas faltantes o invalidas
          se registran como no anotadas en docs/issues/anotacion-<run_id>.md; nunca se inventan.

Este modulo no escribe anotaciones ni calcula puntajes.
  python -m src.annotate.subagent export --date 2026-10-19 [--capability-cutoff 2026-10-19]
  python -m src.annotate.subagent import --run-id <run_id>
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import random
import sys
from pathlib import Path

from . import config as C
from . import pilot, prompt as P
from .runner import Failure, RunResult, guardar_corrida, parse_output
from .schemas import Annotation

IN_DIR = C.ANN_DIR / "pilot_inputs"
OUT_DIR = C.ANN_DIR / "pilot_outputs"
PARQUET_DIR = C.ANN_DIR / "pilot"
OUTPUT_KEYS = ["exposure_class", "physical_bottleneck", "confidence", "rationale"]

OUTPUT_FORMAT = {
    "archivo_salida": "data/processed/annotations/pilot_outputs/<run_id>.jsonl",
    "descripcion": "UNA linea JSON por tarea, exactamente una linea por task_id de 'tareas' (sin lineas en blanco ni comentarios).",
    "claves_por_linea": ["task_id"] + OUTPUT_KEYS,
    "nota_task_id": "task_id solo identifica la tarea (copiado de la entrada); las otras 4 claves son el ModelOutput del prompt.",
    "valores": {"exposure_class": ["E0", "E1", "E2"], "physical_bottleneck": "true|false (booleano JSON)",
                "confidence": ["alta", "media", "baja"], "rationale": "1-2 frases en espanol, 1-600 caracteres"},
    "prohibido": "claves extra, puntajes numericos, bloques de codigo, texto fuera del JSON",
    "ejemplo_linea": '{"task_id": "0000", "exposure_class": "E1", "physical_bottleneck": false, "confidence": "media", "rationale": "Ejemplo de redaccion breve que cita un elemento de la tarea."}',
}


def cutoff_valido(v) -> str:
    if C.decision_pendiente(v):
        raise ValueError("fecha de corte 'requiere decision': pasa --capability-cutoff explicito")
    dt.date.fromisoformat(str(v))
    return str(v)


def run_ids(cfg: dict, n: int | None = None) -> list[str]:
    s = cfg["subagente"]
    return [f"{s['run_id_base']}-{i:02d}" for i in range(1, (n or s["n_corridas"]) + 1)]


def export_inputs(cfg: dict, tareas_df, run_date: dt.date, capability_cutoff: str, in_dir: Path = IN_DIR,
                  n_runs: int | None = None) -> list[Path]:
    cutoff = cutoff_valido(capability_cutoff)
    prompt = P.cargar(cfg["meta"]["prompt_version"])
    s = cfg["subagente"]
    lang = s["texto"]
    if lang != "en":
        raise ValueError("el modo subagente anota ingles (decision del usuario)")
    base = tareas_df.sort_values("task_id").to_dict("records")
    in_dir = Path(in_dir)
    in_dir.mkdir(parents=True, exist_ok=True)
    rutas = []
    for i, rid in enumerate(run_ids(cfg, n_runs), start=1):
        order_seed = cfg["corridas"]["seed_base"] + i
        orden = list(base)
        random.Random(order_seed).shuffle(orden)
        system, user_t = prompt.render(capability_cutoff=cutoff, occupation_title="<<occupation_title>>",
                                       task_text="<<task_text>>", lang=lang)
        tareas = []
        for t in orden:
            _, user = prompt.render(capability_cutoff=cutoff, occupation_title=t["onet_title"],
                                    task_text=t["task_text_en"], lang=lang)
            tt = t["task_type"] if isinstance(t["task_type"], str) else None
            tareas.append({"task_id": str(t["task_id"]), "onet_soc": t["onet_soc"], "onet_title": t["onet_title"],
                           "task_text_en": t["task_text_en"], "task_type": tt, "user_prompt": user})
        doc = {"run_id": rid, "prompt_version": prompt.version, "prompt_sha256": prompt.sha256, "model": s["model"],
               "run_date": run_date.isoformat(), "capability_cutoff": cutoff, "annotated_text_lang": lang,
               "onet_version": cfg["meta"]["onet_version"], "order_seed": order_seed,
               "temperature_note": s["temperature_note"], "n_tareas": len(tareas),
               "instrucciones": "Anota cada tarea de forma independiente con system_prompt + user_prompt de la tarea. "
                                "No leas otras corridas ni archivos de salida existentes. Escribe el archivo de salida indicado.",
               "system_prompt": system, "formato_salida": OUTPUT_FORMAT | {"archivo_salida": f"data/processed/annotations/pilot_outputs/{rid}.jsonl"},
               "tareas": tareas}
        p = in_dir / f"{rid}.json"
        if p.exists():
            raise FileExistsError(f"{p} ya existe; no se sobrescribe")
        p.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
        rutas.append(p)
    return rutas


def import_output(run_id: str, in_dir: Path = IN_DIR, out_dir: Path = OUT_DIR, parquet_dir: Path = PARQUET_DIR,
                  issues_dir: Path | None = None) -> tuple[RunResult, Path | None]:
    doc = json.loads((Path(in_dir) / f"{run_id}.json").read_text(encoding="utf-8"))
    if doc["run_id"] != run_id:
        raise ValueError("run_id del archivo de entrada no coincide")
    if doc["prompt_sha256"] != P.cargar(doc["prompt_version"]).sha256:
        raise ValueError("el prompt cambio desde el export (hash distinto): es otra prompt_version")
    tareas = {t["task_id"]: t for t in doc["tareas"]}
    res = RunResult(run_id)
    jsonl = Path(out_dir) / f"{run_id}.jsonl"
    lineas = jsonl.read_text(encoding="utf-8").splitlines() if jsonl.exists() else []
    if not jsonl.exists():
        res.failures.append(Failure("*", "faltante", 0, f"no existe {jsonl.name}"))
    parsed: dict[str, object] = {}
    malas: dict[str, Failure] = {}
    for n, ln in enumerate(lineas, start=1):
        if not ln.strip():
            continue
        try:
            obj = json.loads(ln)
            if not isinstance(obj, dict) or not isinstance(obj.get("task_id"), str):
                raise ValueError("falta task_id (str)")
            tid = obj.pop("task_id")
        except ValueError as e:
            res.failures.append(Failure(f"linea{n}", "formato", 1, f"{e} | crudo: {ln[:120]!r}"))
            continue
        if tid not in tareas:
            res.failures.append(Failure(tid, "formato", 1, "task_id no pertenece a la entrada"))
            continue
        if tid in parsed or tid in malas:
            parsed.pop(tid, None)
            malas[tid] = Failure(tid, "formato", 1, "task_id duplicado en la salida (ambas lineas descartadas)")
            continue
        try:
            parsed[tid] = parse_output(json.dumps(obj))
        except ValueError as e:
            malas[tid] = Failure(tid, "formato", 1, str(e)[:300])
    res.failures += list(malas.values())
    for tid, t in tareas.items():
        if tid not in parsed:
            if tid not in malas and jsonl.exists():
                res.failures.append(Failure(tid, "faltante", 0, "sin linea en la salida"))
            continue
        o = parsed[tid]
        res.records.append(Annotation(
            run_id=run_id, prompt_version=doc["prompt_version"], prompt_sha256=doc["prompt_sha256"], model=doc["model"],
            run_date=dt.date.fromisoformat(doc["run_date"]), onet_version=doc["onet_version"], onet_soc=t["onet_soc"],
            task_id=tid, task_text_en=t["task_text_en"], task_text_es=None, translation_version=None,
            annotated_text_lang=doc["annotated_text_lang"], task_type=t["task_type"], exposure_class=o.exposure_class,
            physical_bottleneck=o.physical_bottleneck, confidence=o.confidence, rationale=o.rationale,
            capability_cutoff=doc["capability_cutoff"], temperature=None, temperature_note=doc["temperature_note"], seed=None))
    res.records.sort(key=lambda r: r.task_id)
    if not res.records:
        from .runner import escribir_issue
        escribir_issue(run_id, res, len(tareas), "Sin ninguna anotacion valida; no se escribe Parquet.", issues_dir)
        return res, None
    return res, guardar_corrida(res, len(tareas), parquet_dir, issues_dir)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("export")
    e.add_argument("--date", default=None)
    e.add_argument("--capability-cutoff", default=None, help="default: la fecha de la corrida (decision del usuario)")
    e.add_argument("--n-runs", type=int, default=None)
    i = sub.add_parser("import")
    i.add_argument("--run-id", required=True)
    a = ap.parse_args(argv)
    cfg = C.cargar()
    if a.cmd == "export":
        d = dt.date.fromisoformat(a.date) if a.date else dt.date.today()
        try:
            rutas = export_inputs(cfg, pilot.cargar_piloto(), d, a.capability_cutoff or d.isoformat(), n_runs=a.n_runs)
        except (ValueError, FileExistsError) as ex:
            print(f"ERROR: {ex}", file=sys.stderr)
            return 2
        P.guardar_doc(P.cargar(cfg["meta"]["prompt_version"]), cfg)
        for r in rutas:
            print(r)
        return 0
    res, path = import_output(a.run_id)
    print(f"{res.run_id}: anotadas={len(res.records)} no_anotadas={len(res.failures)} -> {path}")
    return 0 if not res.failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
