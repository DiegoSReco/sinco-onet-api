"""Ayudante del orquestador para la ruta S (decision 018, desviacion operativa): prepara archivos de mensaje por lote.

No anota. Para cada lote pendiente: lo marca en_curso (ruta_s.iniciar), escribe el mensaje del lote en un archivo de texto
unico y dice a que archivo debe escribir su respuesta el subagente (el nombre exacto que espera ruta_s.importar).

  python -m src.annotate.orquesta_s preparar --run-id R [--n 4]      # imprime JSON con lote, mensaje, destino
  python -m src.annotate.orquesta_s importar --run-id R               # importa lo escrito (ruta_s.importar_corrida)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import ruta_s as R

MSG_DIR = R.BASE / "mensajes"


def preparar(run_id: str, n: int = 4, base: Path = R.BASE) -> list[dict]:
    est = R.cargar_estado(run_id, base)
    if est.get("detenida"):
        raise RuntimeError(f"{run_id} esta detenida; requiere decision humana")
    P = R._paths(run_id, base)
    out = []
    if n <= 0:
        return out
    for lote in sorted(est["lotes"]):
        l = est["lotes"][lote]
        if l["estado"] not in ("pendiente", "invalido"):
            continue
        intento = R.iniciar(run_id, lote, base)
        msg = R._read_json(P["inputs"] / f"{lote}.json")["mensaje_subagente"]
        MSG_DIR.mkdir(parents=True, exist_ok=True)
        mp = MSG_DIR / f"{run_id}__{lote}__a{intento}.txt"
        mp.write_text(msg, encoding="utf-8")
        P["intentos"].mkdir(parents=True, exist_ok=True)
        destino = P["intentos"] / f"{lote}_a{intento}.txt"
        out.append({"lote": lote, "intento": intento, "mensaje": str(mp), "destino": str(destino)})
        if len(out) >= n:
            break
    return out


def importar(run_id: str, base: Path = R.BASE) -> dict:
    """Importa solo los lotes en_curso cuyo archivo de respuesta ya existe (no escribe issues por lotes aun sin respuesta)."""
    est = R.cargar_estado(run_id, base)
    P = R._paths(run_id, base)
    res = []
    for lote in sorted(est["lotes"]):
        l = est["lotes"][lote]
        if l["estado"] == "en_curso" and (P["intentos"] / f"{lote}_a{l['intentos'] + 1}.txt").exists():
            x = R.importar_lote(run_id, lote, base=base)
            res.append([lote, x["resultado"], x.get("errores", [])[:2]])
            if R.cargar_estado(run_id, base).get("detenida"):
                break
    est = R.cargar_estado(run_id, base)
    parquet = None
    if all(l["estado"] == "ok" for l in est["lotes"].values()):
        parquet = str(R.ensamblar(run_id, base=base))
    return {"importados": res, "en_curso": [b for b, l in est["lotes"].items() if l["estado"] == "en_curso"],
            "pendientes": sum(1 for l in est["lotes"].values() if l["estado"] in ("pendiente", "invalido")), "parquet": parquet}


def ciclo(run_id: str, max_paralelo: int = 4, base: Path = R.BASE) -> dict:
    """Importa lo escrito y prepara lotes nuevos hasta tener `max_paralelo` en vuelo (decision 015 §3.7: tope 4)."""
    r = importar(run_id, base)
    est = R.cargar_estado(run_id, base)
    nuevos = []
    if not est.get("detenida") and not r["parquet"]:
        nuevos = preparar(run_id, max(0, max_paralelo - len(r["en_curso"])), base)
    r["nuevos"] = nuevos
    return r


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(prog="python -m src.annotate.orquesta_s")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("preparar")
    p.add_argument("--run-id", required=True)
    p.add_argument("--n", type=int, default=4)
    i = sub.add_parser("importar")
    i.add_argument("--run-id", required=True)
    c = sub.add_parser("ciclo")
    c.add_argument("--run-id", required=True)
    c.add_argument("--max", type=int, default=4)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "ciclo":
            print(json.dumps(ciclo(a.run_id, a.max), ensure_ascii=False))
        elif a.cmd == "preparar":
            print(json.dumps(preparar(a.run_id, a.n), ensure_ascii=False))
        else:
            r = importar(a.run_id)
            print(json.dumps(r, ensure_ascii=False))
    except (RuntimeError, ValueError, FileExistsError, FileNotFoundError, KeyError) as ex:
        print(f"ERROR: {ex}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
