"""Ayuda de revision humana de la ruta S (decision 018): lista las funciones donde los tres modelos discrepan mas.

No calcula exposicion ni puntajes; solo muestra etiquetas ya anotadas lado a lado para que una persona las lea. Cifras (conteos)
salen de este script (regla 1). Rotulo: consistencia entre modelos, no exactitud.

  python -m src.annotate.revisar_desacuerdos [--campo eloundou_class|exposure_class] [--n 20] [--csv ruta.csv]
"""
from __future__ import annotations

import argparse
import sys

import pandas as pd

from . import ruta_s as R

# Primera corrida de cada modelo; cambiar aqui para revisar otra corrida.
CORRIDAS = {"sonnet": "ann-s-v1-2026-10-20-01", "haiku": "ann-s-v1-2026-10-22-haiku-01", "opus": "ann-s-v1-2026-10-22-opus-01"}


def tabla(campo: str = "eloundou_class") -> pd.DataFrame:
    t = {m: pd.read_parquet(R.BASE / "parquet" / f"run_{r}.parquet").set_index(["sinco_code", "orden"]) for m, r in CORRIDAS.items()}
    d = pd.DataFrame({m: x[campo].replace({"EL3": "EL2"}) for m, x in t.items()})
    d["funcion"] = t["sonnet"]["function_text_es"].str.slice(0, 110)
    d["razon_haiku"] = t["haiku"]["rationale"].str.slice(0, 110)
    d["razon_sonnet"] = t["sonnet"]["rationale"].str.slice(0, 110)
    d["razon_opus"] = t["opus"]["rationale"].str.slice(0, 110)
    return d


def fuertes(d: pd.DataFrame) -> pd.DataFrame:
    """Desacuerdo fuerte: los tres modelos dan tres clases distintas, o los extremos (EL0 y EL2 / E0 y E2) se enfrentan."""
    m = d[["sonnet", "haiku", "opus"]]
    ext = m.apply(lambda f: {"EL0", "EL2"} <= set(f) or {"E0", "E2"} <= set(f), axis=1)
    return d[(m.nunique(axis=1) == 3) | ext]


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(prog="python -m src.annotate.revisar_desacuerdos")
    ap.add_argument("--campo", default="eloundou_class", choices=("eloundou_class", "exposure_class"))
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--csv", default=None, help="guarda todos los desacuerdos fuertes en este CSV")
    a = ap.parse_args(argv)
    d = tabla(a.campo)
    f = fuertes(d)
    print(f"{len(d)} funciones; {len(f)} con desacuerdo fuerte ({a.campo}, EL3 fundida en EL2)")
    if a.csv:
        f.to_csv(a.csv, encoding="utf-8-sig")
        print("->", a.csv)
    with pd.option_context("display.max_colwidth", 110, "display.width", 250):
        print(f.head(a.n).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
