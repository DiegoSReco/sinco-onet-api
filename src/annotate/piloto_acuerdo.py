"""Acuerdo descriptivo entre las 3 corridas del piloto (exploratorio, decision 008).

No calcula exposicion ni usa el mapa E0/E1/E2 -> 0/0.5/1: solo distribuciones de clase y acuerdo
entre corridas sobre las mismas tareas. Salida: data/processed/annotations/pilot/acuerdo.json.
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import cohen_kappa_score

RAIZ = Path(__file__).resolve().parents[2]
DIR = RAIZ / "data" / "processed" / "annotations" / "pilot"
ORDEN = ["E0", "E1", "E2"]


def main() -> None:
    corridas = {p.stem.removeprefix("run_"): pd.read_parquet(p) for p in sorted(DIR.glob("run_*.parquet"))}
    ids = list(corridas)
    base = corridas[ids[0]][["task_id"]]
    cls = pd.DataFrame({r: d.set_index("task_id")["exposure_class"] for r, d in corridas.items()})
    cls = cls.loc[base["task_id"]]
    fis = pd.DataFrame({r: d.set_index("task_id")["physical_bottleneck"] for r, d in corridas.items()}).loc[cls.index]

    out: dict = {"corridas": ids, "n_tareas": int(len(cls)), "nota": "exploratorio; NO es exposicion"}
    out["distribucion_clase"] = {r: cls[r].value_counts().reindex(ORDEN, fill_value=0).to_dict() for r in ids}
    out["distribucion_physical_bottleneck"] = {r: int(fis[r].sum()) for r in ids}
    pares = {}
    for a, b in itertools.combinations(ids, 2):
        pares[f"{a}|{b}"] = {
            "acuerdo_exacto": float((cls[a] == cls[b]).mean()),
            "kappa_nominal": float(cohen_kappa_score(cls[a], cls[b], labels=ORDEN)),
            "kappa_ponderado_lineal": float(cohen_kappa_score(cls[a], cls[b], labels=ORDEN, weights="linear")),
            "acuerdo_physical_bottleneck": float((fis[a] == fis[b]).mean()),
        }
    out["pares"] = pares
    n_iguales = (cls.nunique(axis=1) == 1)
    out["tareas_con_acuerdo_unanime"] = int(n_iguales.sum())
    out["tareas_con_tres_clases_distintas"] = int((cls.nunique(axis=1) == 3).sum())
    # Independencia: justificaciones textualmente identicas entre corridas (senal de copia)
    rat = pd.DataFrame({r: d.set_index("task_id")["rationale"] for r, d in corridas.items()}).loc[cls.index]
    out["rationale_identico_entre_corridas"] = int((rat.nunique(axis=1) < len(ids)).sum())
    (DIR / "acuerdo.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
