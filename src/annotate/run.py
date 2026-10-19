"""CLI: python -m src.annotate.run --run-id R --sample pilot --provider dry-run --model NAME --n-runs N

Solo el proveedor 'dry-run' existe. La muestra 'full' NO esta habilitada (requiere aprobacion tras el piloto).
Las corridas dry-run se escriben en data/processed/annotations/dryrun/ y nunca son resultados.
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

from . import config as C
from . import pilot, prompt as P, providers
from .runner import TaskInput, run_many


def tareas_desde_df(df) -> list[TaskInput]:
    return [TaskInput(task_id=str(r.task_id), onet_soc=r.onet_soc, onet_title=r.onet_title, task_text_en=r.task_text_en,
                      task_type=r.task_type if isinstance(r.task_type, str) else None,
                      task_text_es=r.task_text_es if isinstance(r.task_text_es, str) else None)
            for r in df.itertuples()]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True, help="id base; las corridas son {id}-01, {id}-02, ...")
    ap.add_argument("--sample", choices=["pilot", "full"], default="pilot")
    ap.add_argument("--provider", default="dry-run")
    ap.add_argument("--model", required=True)
    ap.add_argument("--n-runs", type=int, default=None)
    ap.add_argument("--temperature", type=float, default=None)
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--date", default=None, help="YYYY-MM-DD (default: hoy)")
    a = ap.parse_args(argv)

    cfg = C.cargar()
    if a.sample == "full":
        print("ERROR: la corrida completa no esta habilitada; requiere reporte del piloto y aprobacion.", file=sys.stderr)
        return 2
    if a.provider != "dry-run":
        if C.decision_pendiente(cfg["capacidades"]["fecha_corte"]):
            print("ERROR: fecha de corte de capacidades 'requiere decision' (001 P3); no se corre un proveedor real.", file=sys.stderr)
            return 2
        provider_factory = lambda: providers.crear(a.provider)  # noqa: E731  (lanza NotImplementedError)
    else:
        provider_factory = providers.DryRunProvider
    prompt = P.cargar(cfg["meta"]["prompt_version"])
    P.guardar_doc(prompt, cfg)
    out_dir = Path(a.out_dir) if a.out_dir else (C.ANN_DIR / "dryrun" if a.provider == "dry-run" else C.ANN_DIR)
    tasks = tareas_desde_df(pilot.cargar_piloto())
    run_date = dt.date.fromisoformat(a.date) if a.date else dt.date.today()
    n = a.n_runs or cfg["corridas"]["n_corridas"]
    for res, path in run_many(base_run_id=a.run_id, n_runs=n, tasks=tasks, provider_factory=provider_factory, prompt=prompt,
                              model=a.model, cfg=cfg, run_date=run_date, temperature=a.temperature, out_dir=out_dir):
        print(f"{res.run_id}: anotadas={len(res.records)} omitidas={len(res.failures)} llamadas={res.calls} "
              f"tokens_in~{res.input_tokens} tokens_out~{res.output_tokens} s={res.seconds:.2f} -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
