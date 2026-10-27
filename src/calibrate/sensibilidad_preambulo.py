"""Sensibilidad al preambulo (decision 018 R1.4, S5): Sonnet ann-s-v1 contra ann-s-v2. Rotulo: CONSISTENCIA, NO EXACTITUD.

Compara el kappa ponderado cuadratico entre corridas v1 y v2 de Sonnet con el kappa entre las dos corridas v1 y entre las dos v2
(ruido entre corridas). `exposure_class` no depende del parrafo cambiado: su cambio estima el ruido residual. No entra a la
medida de registro (018 R1.3). Cifras solo de este script (regla 1).

  python -m src.calibrate.sensibilidad_preambulo --v1 R1 R2 --v2 R3 R4
"""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.annotate import ruta_s as R
from src.annotate.ruta_s_validacion import ORD, _campo, kappa_cuadratico

ROOT = Path(__file__).resolve().parents[2]


def _serie(run_id: str, campo: str) -> pd.Series:
    t = pd.read_parquet(R.BASE / "parquet" / f"run_{run_id}.parquet")
    t["item"] = t["sinco_code"].astype(str) + "|" + t["orden"].astype(str)
    return _campo(t, campo).set_axis(t["item"]).sort_index()


def _kappa(a: str, b: str, campo: str) -> float | None:
    sa, sb = _serie(a, campo), _serie(b, campo)
    return kappa_cuadratico(list(sa), list(sb.loc[sa.index]), ORD[campo])


def comparar(v1: list[str], v2: list[str]) -> dict:
    out = {"rotulo": "consistencia entre versiones de prompt, no exactitud", "v1": v1, "v2": v2, "campos": {}}
    for campo in ("exposure_class", "eloundou_fundida", "eloundou_cruda"):
        intra_v1 = [_kappa(a, b, campo) for a, b in itertools.combinations(v1, 2)]
        intra_v2 = [_kappa(a, b, campo) for a, b in itertools.combinations(v2, 2)]
        cruz = [_kappa(a, b, campo) for a in v1 for b in v2]
        cambio = {}
        if campo != "exposure_class":
            s1 = pd.concat([_serie(r, campo) for r in v1], axis=1)
            s2 = pd.concat([_serie(r, campo) for r in v2], axis=1)
            idx = {c: i for i, c in enumerate(ORD[campo])}
            m1 = s1.apply(lambda c: c.map(idx)).mean(axis=1)
            m2 = s2.apply(lambda c: c.map(idx)).mean(axis=1)
            cambio = {"media_indice_v1": float(m1.mean() / (len(idx) - 1)), "media_indice_v2": float(m2.mean() / (len(idx) - 1)),
                      "dif_media_v2_menos_v1": float((m2 - m1).mean() / (len(idx) - 1))}
        out["campos"][campo] = {"kappa_intra_v1": intra_v1, "kappa_intra_v2": intra_v2, "kappa_cruzado_v1_v2_medio": float(np.mean(cruz)),
                                "kappa_cruzado_v1_v2": cruz, **cambio}
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m src.calibrate.sensibilidad_preambulo")
    ap.add_argument("--v1", nargs="+", required=True)
    ap.add_argument("--v2", nargs="+", required=True)
    ap.add_argument("--salida", default=str(ROOT / "data" / "processed" / "calibracion" / "sensibilidad_preambulo.json"))
    a = ap.parse_args(argv)
    r = comparar(a.v1, a.v2)
    Path(a.salida).write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    for c, v in r["campos"].items():
        print(c, "intra v1", [round(x, 3) for x in v["kappa_intra_v1"]], "intra v2", [round(x, 3) for x in v["kappa_intra_v2"]],
              "cruzado", round(v["kappa_cruzado_v1_v2_medio"], 3), {k: round(x, 3) for k, x in v.items() if k.startswith(("media", "dif"))})
    print("->", a.salida)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
