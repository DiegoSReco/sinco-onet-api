"""Medidor de avance de la anotacion ruta S (decisiones 015 y 018). Solo lee; no anota ni calcula exposicion.

  python -m src.annotate.progreso                 # tabla en la terminal
  python -m src.annotate.progreso --watch 10      # se refresca cada 10 s y reescribe progreso.html
  python -m src.annotate.progreso --html          # escribe una vez data/processed/annotations/ruta_s/progreso.html

Muestra, por corrida: modelo, lotes ok/en curso/pendientes/invalidos/fallidos, funciones anotadas y una barra.
Abajo, "como se llena la tabla": funciones anotadas por modelo y distribucion acumulada de exposure_class y eloundou_class
(conteos de lo ya importado; son avance, no resultados).
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import sys
import time
from collections import Counter
from pathlib import Path

from . import config as C

BASE = C.ANN_DIR / "ruta_s"
HTML = BASE / "progreso.html"
ESTADOS = ("ok", "en_curso", "pendiente", "invalido", "fallido")


def _json(p: Path):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def leer(base: Path = BASE) -> list[dict]:
    """Una fila por corrida con conteos de lotes, funciones y distribuciones de lo ya importado."""
    filas = []
    for d in sorted(p for p in Path(base).iterdir() if p.is_dir() and (p / "estado.json").exists()):
        est, meta = _json(d / "estado.json"), _json(d / "run_meta.json")
        c = Counter(l["estado"] for l in est["lotes"].values())
        f_ok = sum(l["n_funciones"] for l in est["lotes"].values() if l["estado"] == "ok")
        ex, el = Counter(), Counter()
        for sp in sorted((d / "salida").glob("*.json")) if (d / "salida").exists() else []:
            for r in _json(sp):
                ex[r["exposure_class"]] += 1
                el[r["eloundou_class"]] += 1
        filas.append({"run_id": d.name, "modelo": meta["model"], "n_lotes": len(est["lotes"]), "lotes": {e: c.get(e, 0) for e in ESTADOS},
                      "funciones_ok": f_ok, "funciones": meta["n_funciones"], "detenida": est.get("detenida", False),
                      "ensamblada": bool(est.get("ensamblada")), "exposure_class": dict(ex), "eloundou_class": dict(el),
                      "intentos": sum(l["intentos"] for l in est["lotes"].values())})
    return filas


def _barra(x: int, n: int, ancho: int = 24) -> str:
    lleno = int(round(ancho * x / n)) if n else 0
    return "█" * lleno + "░" * (ancho - lleno)


def texto(filas: list[dict]) -> str:
    out = [f"Avance de anotacion ruta S - {dt.datetime.now():%Y-%m-%d %H:%M:%S}", ""]
    out.append(f"{'corrida':36} {'lotes ok':>9} {'func.':>11}  avance")
    for f in filas:
        marca = " DETENIDA" if f["detenida"] else (" ensamblada" if f["ensamblada"] else "")
        extra = "".join(f" {k}={v}" for k, v in f["lotes"].items() if k != "ok" and v)
        out.append(f"{f['run_id']:36} {f['lotes']['ok']:>4}/{f['n_lotes']:<4} {f['funciones_ok']:>5}/{f['funciones']:<5} "
                   f"{_barra(f['funciones_ok'], f['funciones'])}{marca}{extra}")
    out += ["", "Como se llena la tabla (lo ya importado, por corrida):"]
    out.append(f"{'corrida':36} {'E0':>6} {'E1':>6} {'E2':>6} | {'EL0':>6} {'EL1':>6} {'EL2':>6} {'EL3':>6}")
    for f in filas:
        e, l = f["exposure_class"], f["eloundou_class"]
        out.append(f"{f['run_id']:36} " + " ".join(f"{e.get(k, 0):>6}" for k in ("E0", "E1", "E2")) + " | "
                   + " ".join(f"{l.get(k, 0):>6}" for k in ("EL0", "EL1", "EL2", "EL3")))
    tot = sum(f["funciones_ok"] for f in filas)
    tope = sum(f["funciones"] for f in filas)
    out += ["", f"Total: {tot}/{tope} anotaciones ({100 * tot / tope:.1f} %)" if tope else "Sin corridas exportadas."]
    return "\n".join(out)


def html_doc(filas: list[dict]) -> str:
    def fila(f):
        pct = 100 * f["funciones_ok"] / f["funciones"] if f["funciones"] else 0
        e, l = f["exposure_class"], f["eloundou_class"]
        est = "detenida" if f["detenida"] else ("ensamblada" if f["ensamblada"] else "")
        return (f"<tr><td>{html.escape(f['run_id'])}<br><small>{html.escape(f['modelo'])}</small></td>"
                f"<td>{f['lotes']['ok']}/{f['n_lotes']}<br><small>en curso {f['lotes']['en_curso']} · pend. {f['lotes']['pendiente']} · "
                f"inv. {f['lotes']['invalido']} · fall. {f['lotes']['fallido']}</small></td>"
                f"<td><div class='b'><i style='width:{pct:.1f}%'></i></div>{f['funciones_ok']}/{f['funciones']} ({pct:.1f} %) {est}</td>"
                + "".join(f"<td>{e.get(k, 0)}</td>" for k in ("E0", "E1", "E2"))
                + "".join(f"<td>{l.get(k, 0)}</td>" for k in ("EL0", "EL1", "EL2", "EL3")) + "</tr>")
    tot = sum(f["funciones_ok"] for f in filas)
    tope = sum(f["funciones"] for f in filas)
    return ("<!doctype html><meta charset='utf-8'><meta http-equiv='refresh' content='10'><title>Avance ruta S</title>"
            "<style>body{font:14px system-ui;margin:24px;background:#fff;color:#111}table{border-collapse:collapse}"
            "td,th{border:1px solid #ccc;padding:4px 8px;text-align:right}td:first-child,td:nth-child(2),td:nth-child(3){text-align:left}"
            ".b{width:220px;height:10px;background:#e5e5e5}.b i{display:block;height:10px;background:#2563eb}"
            "@media(prefers-color-scheme:dark){body{background:#111;color:#eee}td,th{border-color:#444}.b{background:#333}}</style>"
            f"<h2>Avance de anotacion, ruta S</h2><p>Actualizado {dt.datetime.now():%Y-%m-%d %H:%M:%S} (la pagina se recarga cada 10 s). "
            f"Total {tot}/{tope} anotaciones. Conteos = avance, no resultados.</p>"
            "<table><tr><th>Corrida / modelo</th><th>Lotes</th><th>Funciones</th><th>E0</th><th>E1</th><th>E2</th>"
            "<th>EL0</th><th>EL1</th><th>EL2</th><th>EL3</th></tr>" + "".join(fila(f) for f in filas) + "</table>")


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(prog="python -m src.annotate.progreso")
    ap.add_argument("--watch", type=int, default=0, help="segundos entre refrescos (0 = una vez)")
    ap.add_argument("--html", action="store_true", help="escribe progreso.html")
    a = ap.parse_args(argv)
    while True:
        filas = leer()
        if a.html or a.watch:
            HTML.write_text(html_doc(filas), encoding="utf-8")
        print(texto(filas), flush=True)
        if not a.watch:
            return 0
        time.sleep(a.watch)
        print("\n" + "-" * 60)


if __name__ == "__main__":
    raise SystemExit(main())
