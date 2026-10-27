"""Exporta a un JSON los datos que usa la pagina interactiva de revision (no calcula exposicion ni puntajes).

Reune, de salidas ya generadas por otros scripts: kappa entre modelos (acuerdo_modelos.json), conteos de clases por corrida,
sesgo por modelo y diagnosticos de B1 ordinal, y las funciones donde los tres modelos no coinciden (con texto y razones).
Rotulo: consistencia entre modelos, no exactitud. Cifras solo de scripts (regla 1); no se citan en el articulo (regla 6).

  python -m src.calibrate.exportar_explorador [--salida data/processed/calibracion/explorador_datos.json]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from src.annotate import ruta_s as R
from src.annotate.revisar_desacuerdos import CORRIDAS, fuertes, tabla

ROOT = Path(__file__).resolve().parents[2]
CAL = ROOT / "data" / "processed" / "calibracion"
CORRIDAS_CONTEO = {
    "Sonnet v1-01": "ann-s-v1-2026-10-20-01", "Sonnet v1-02": "ann-s-v1-2026-10-20-02",
    "Haiku v1-01": "ann-s-v1-2026-10-22-haiku-01", "Haiku v1-02": "ann-s-v1-2026-10-22-haiku-02",
    "Opus v1-01": "ann-s-v1-2026-10-22-opus-01", "Opus v1-02": "ann-s-v1-2026-10-22-opus-02",
    "Sonnet v2-01": "ann-s-v2-2026-10-22-sonnet-01", "Sonnet v2-02": "ann-s-v2-2026-10-22-sonnet-02",
}
MAX_FILAS = 700


def conteos() -> dict:
    out = {}
    for nombre, rid in CORRIDAS_CONTEO.items():
        t = pd.read_parquet(R.BASE / "parquet" / f"run_{rid}.parquet")
        out[nombre] = {"exposure_class": t["exposure_class"].value_counts().to_dict(),
                       "eloundou_class": t["eloundou_class"].replace({"EL3": "EL2"}).value_counts().to_dict(),
                       "n": int(len(t))}
    return out


def b1() -> dict:
    out = {}
    for campo in ("eloundou_class", "exposure_class"):
        a = pd.read_parquet(CAL / f"b1_ordinal_{campo}_modelo_anotadores.parquet")
        d = pd.read_parquet(CAL / f"b1_ordinal_{campo}_modelo_diagnosticos.parquet")
        meta = json.loads((CAL / f"b1_ordinal_{campo}_modelo_meta.json").read_text(encoding="utf-8"))
        out[campo] = {"anotadores": a.to_dict("records"), "max_rhat": float(d["rhat"].max()), "min_ess": float(d["ess"].min()),
                      "convergio": bool(meta["convergio"]), "n_items": meta["n_items"], "n_grupos": meta["n_grupos"],
                      "etiqueta": meta["etiqueta"]}
    return out


def desacuerdos() -> dict:
    out = {}
    for campo in ("eloundou_class", "exposure_class"):
        d = tabla(campo)
        m = d[["sonnet", "haiku", "opus"]]
        con = d[m.nunique(axis=1) > 1].copy()
        con["fuerte"] = con.index.isin(fuertes(d).index)
        con = con.sort_values("fuerte", ascending=False, kind="stable")
        total = int(len(con))
        con = con.head(MAX_FILAS)
        out[campo] = {"total_con_desacuerdo": total, "total_fuertes": int(fuertes(d).shape[0]), "n_funciones": int(len(d)),
                      "filas": [[int(i[0]), int(i[1]), r.sonnet, r.haiku, r.opus, bool(r.fuerte), r.funcion, r.razon_sonnet, r.razon_haiku, r.razon_opus]
                                for i, r in con.iterrows()]}
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m src.calibrate.exportar_explorador")
    ap.add_argument("--salida", default=str(CAL / "explorador_datos.json"))
    a = ap.parse_args(argv)
    ac = json.loads((CAL / "acuerdo_modelos.json").read_text(encoding="utf-8"))
    datos = {"rotulo": "consistencia entre modelos, no exactitud", "corridas_para_desacuerdos": CORRIDAS,
             "umbrales_provisionales": {"uso_principal": 0.60, "exclusion": 0.40},
             "acuerdo": ac["campos"], "conteos": conteos(), "b1": b1(), "desacuerdos": desacuerdos()}
    Path(a.salida).write_text(json.dumps(datos, ensure_ascii=False, separators=(",", ":"), default=str), encoding="utf-8")
    print("->", a.salida, round(Path(a.salida).stat().st_size / 1024), "KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
