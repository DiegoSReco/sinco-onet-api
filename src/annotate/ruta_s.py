"""Corrida completa de anotacion, ruta S (decision 015 sec. 3): funcion SINCO -> anotacion, con subagentes.

Este modulo NO anota ni calcula puntajes. Prepara lotes, registra el estado, valida e importa las respuestas
de los subagentes (que lanza el orquestador) y nunca inventa una etiqueta.

  python -m src.annotate.ruta_s export --corridas 3 [--fecha YYYY-MM-DD] [--capability-cutoff YYYY-MM-DD]
  python -m src.annotate.ruta_s estado [--run-id R] [--detalle]
  python -m src.annotate.ruta_s mensaje --run-id R --lote L001          # texto exacto para el subagente
  python -m src.annotate.ruta_s iniciar --run-id R --lote L001           # marca en_curso
  python -m src.annotate.ruta_s importar --run-id R [--lote L001] [--respuesta ARCHIVO] [--fecha YYYY-MM-DD]
  python -m src.annotate.ruta_s interrumpir --run-id R --lote L001       # cuota/herramienta: no cuenta como intento
  python -m src.annotate.ruta_s reanudar --run-id R                      # en_curso -> pendiente
  python -m src.annotate.ruta_s ensamblar --run-id R                     # Parquet de la corrida (todos los lotes ok)
  python -m src.annotate.ruta_s validar --run-ids R1 R2 R3               # criterios 015 3.9
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import random
import re
import sys
from pathlib import Path

import pandas as pd

from . import config as C
from .schemas import AnnotationS, ModelOutputS, read_parquet_s, write_parquet_s
from pydantic import ValidationError

PROMPT_DIR = Path(__file__).with_name("prompts")
SYS_MARK, USR_MARK = "<!-- SYSTEM -->", "<!-- USER -->"
BASE = C.ANN_DIR / "ruta_s"
ESTADOS = ("pendiente", "en_curso", "ok", "invalido", "fallido")
FUSION_RE = re.compile(r"\S- [A-ZÁÉÍÓÚÑ]")

OUTPUT_FORMAT = {
    "descripcion": "Responde SOLO con lineas JSON (JSONL): exactamente una linea por function_id entregado, sin texto "
                   "antes ni despues, sin bloques de codigo, sin lineas en blanco.",
    "claves_por_linea": ["function_id", "exposure_class", "eloundou_class", "physical_bottleneck", "confidence", "rationale"],
    "valores": {"exposure_class": ["E0", "E1", "E2"], "eloundou_class": ["EL0", "EL1", "EL2", "EL3"],
                "physical_bottleneck": "true|false (booleano JSON)", "confidence": ["alta", "media", "baja"],
                "rationale": "espanol, maximo 25 palabras, 1-600 caracteres"},
    "prohibido": "claves extra, puntajes numericos, bloques de codigo, texto fuera del JSON",
    "ejemplo_linea": '{"function_id": "0000-00", "exposure_class": "E1", "eloundou_class": "EL1", "physical_bottleneck": false, '
                     '"confidence": "media", "rationale": "Ejemplo de redaccion breve."}',
}


# ----------------------------------------------------------------------------- utilidades
def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    return sha256_bytes(Path(p).read_bytes())


def _write_json(p: Path, obj) -> None:
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1, ensure_ascii=False, sort_keys=False), encoding="utf-8")
    tmp.replace(p)


def _read_json(p: Path):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def function_id(code: str, orden: int) -> str:
    return f"{code}-{int(orden):02d}"


def cfg_s(cfg: dict | None = None) -> dict:
    cfg = cfg or C.cargar()
    if "ruta_s" not in cfg:
        raise ValueError("config.toml: falta la seccion [ruta_s]")
    return cfg["ruta_s"]


# ----------------------------------------------------------------------------- prompt
class PromptS:
    def __init__(self, version: str, system: str, user: str, raw: str):
        self.version, self.system, self.user, self.raw = version, system, user, raw

    @property
    def sha256(self) -> str:
        return sha256_bytes(self.raw.encode("utf-8"))

    def system_text(self, capability_cutoff: str) -> str:
        return self.system.replace("<<capability_cutoff>>", capability_cutoff)

    def grupo_text(self, *, sinco_code, titulo, descripcion, ocupaciones, funciones) -> str:
        return (self.user.replace("<<sinco_code>>", sinco_code).replace("<<titulo>>", titulo)
                .replace("<<descripcion>>", descripcion).replace("<<ocupaciones>>", ocupaciones)
                .replace("<<funciones>>", funciones))


def cargar_prompt(version: str = "ann-s-v1", prompt_dir: Path = PROMPT_DIR) -> PromptS:
    raw = (Path(prompt_dir) / f"{version}.md").read_text(encoding="utf-8")
    if SYS_MARK not in raw or USR_MARK not in raw:
        raise ValueError("prompt sin marcadores SYSTEM/USER")
    _, rest = raw.split(SYS_MARK, 1)
    system, user = rest.split(USR_MARK, 1)
    return PromptS(version, system.strip(), user.strip(), raw)


# ----------------------------------------------------------------------------- universo
def _limpio(s: str) -> str:
    return re.sub(r"\s+", " ", str(s)).strip()


def cargar_universo(proc: Path = C.PROC) -> dict:
    """{'grupos': {code: {...}}, 'source_sha256': str, 'sin_funciones': [codes]} a partir de las tablas procesadas."""
    proc = Path(proc)
    f = pd.read_parquet(proc / "sinco_funciones.parquet")
    d = pd.read_parquet(proc / "sinco_descripcion.parquet")
    s = pd.read_parquet(proc / "sinco.parquet")
    o = pd.read_parquet(proc / "sinco_ocupaciones_ejemplo.parquet")
    src = pd.read_parquet(proc / "sinco_fuente.parquet")
    unit = s[s["nivel"] == "grupo_unitario"].set_index("sinco_code")
    dd = d.set_index("sinco_code")
    grupos = {}
    for code, g in f.groupby("sinco_code"):
        nota = dd.loc[code, "notas_extraccion"]
        marca = isinstance(nota, str) and "vineta perdida" in nota
        funcs = []
        for r in g.sort_values("orden").itertuples():
            t = _limpio(r.funcion)
            funcs.append({"orden": int(r.orden), "texto": t, "item_fusionado": bool(marca and FUSION_RE.search(t))})
        oc = o[(o["sinco_code"] == code) & (~o["afectado_por_errata"])].sort_values("orden")
        grupos[code] = {"sinco_code": code, "titulo": _limpio(unit.loc[code, "titulo"]),
                        "descripcion": _limpio(dd.loc[code, "descripcion"]),
                        "ocupaciones": [_limpio(x) for x in oc["ocupacion"]], "funciones": funcs}
    sin = sorted(set(unit.index) - set(grupos))
    return {"grupos": grupos, "source_sha256": str(src["sha256"].iloc[0]), "sin_funciones": sin}


def claves_universo(universo: dict) -> set[tuple[str, int]]:
    return {(c, f["orden"]) for c, g in universo["grupos"].items() for f in g["funciones"]}


# ----------------------------------------------------------------------------- lotes
def plan_lotes(universo: dict, seed: int, lote_grupos: int = 10, tope_funciones: int = 120) -> list[list[dict]]:
    """Reparto determinista: baraja grupos y funciones con Random(seed) y cierra el lote al llegar a
    `lote_grupos` grupos o cuando el siguiente grupo haria pasar de `tope_funciones` funciones."""
    rng = random.Random(seed)
    codes = sorted(universo["grupos"])
    rng.shuffle(codes)
    lotes: list[list[dict]] = []
    actual: list[dict] = []
    n_f = 0
    for c in codes:
        g = universo["grupos"][c]
        funcs = sorted(g["funciones"], key=lambda x: x["orden"])
        rng.shuffle(funcs)
        if len(funcs) > tope_funciones:
            raise ValueError(f"grupo {c} tiene mas funciones que el tope del lote")
        if actual and (len(actual) >= lote_grupos or n_f + len(funcs) > tope_funciones):
            lotes.append(actual)
            actual, n_f = [], 0
        actual.append({**g, "funciones": funcs})
        n_f += len(funcs)
    if actual:
        lotes.append(actual)
    return lotes


def armar_mensaje(system_prompt: str, grupos_txt: list[str], n_funciones: int) -> str:
    return (system_prompt + "\n\n## BLOQUE F. Funciones a anotar en este lote\n"
            + "\n\n".join(grupos_txt)
            + f"\n\n## Instrucciones finales\nNo uses herramientas ni leas archivos: todo el contenido esta en este mensaje. "
              f"Devuelve exactamente {n_funciones} lineas JSON (una por function_id listado arriba) y nada mas.")


def run_ids(fecha: str, n: int, version: str, alias: str | None = None) -> list[str]:
    """Con alias (decision 018: un modelo distinto) el run_id lleva el modelo: ann-s-v1-FECHA-ALIAS-NN."""
    mid = f"-{alias}" if alias else ""
    return [f"{version}-{fecha}{mid}-{k:02d}" for k in range(1, n + 1)]


def export(*, n_corridas: int, fecha: str, capability_cutoff: str | None = None, universo: dict | None = None,
           base: Path = BASE, cfg: dict | None = None, prompt: PromptS | None = None, seed_base: int | None = None,
           lote_grupos: int | None = None, tope_funciones: int | None = None,
           model: str | None = None, alias: str | None = None) -> dict:
    cfg = cfg or C.cargar()
    s = dict(cfg_s(cfg))
    if model:
        s["model"] = model
    dt.date.fromisoformat(fecha)
    cutoff = capability_cutoff or fecha
    dt.date.fromisoformat(cutoff)
    prompt = prompt or cargar_prompt(s["prompt_version"])
    universo = universo or cargar_universo()
    seed_base = cfg["corridas"]["seed_base"] if seed_base is None else seed_base
    lote_grupos = lote_grupos or s["lote_grupos"]
    tope = tope_funciones or s["tope_funciones"]
    base = Path(base)
    resumen = {}
    for k, rid in enumerate(run_ids(fecha, n_corridas, prompt.version, alias), start=1):
        if (base / "inputs" / rid).exists() or (base / rid).exists():
            raise FileExistsError(f"la corrida {rid} ya fue exportada; no se sobrescribe")
    sys_txt = prompt.system_text(cutoff)
    for k, rid in enumerate(run_ids(fecha, n_corridas, prompt.version, alias), start=1):
        seed = seed_base + k
        lotes = plan_lotes(universo, seed, lote_grupos, tope)
        estado_lotes = {}
        for i, lote in enumerate(lotes, start=1):
            bid = f"L{i:03d}"
            grupos_doc, grupos_txt, fids = [], [], []
            for g in lote:
                lines = [f"[{function_id(g['sinco_code'], f['orden'])}] {f['texto']}" for f in g["funciones"]]
                txt = prompt.grupo_text(sinco_code=g["sinco_code"], titulo=g["titulo"], descripcion=g["descripcion"] or "(sin descripcion)",
                                        ocupaciones="; ".join(g["ocupaciones"]) or "(sin ocupaciones ejemplo)",
                                        funciones="\n".join(lines))
                grupos_txt.append(txt)
                f_ids = [function_id(g["sinco_code"], f["orden"]) for f in g["funciones"]]
                fids += f_ids
                grupos_doc.append({"sinco_code": g["sinco_code"], "titulo": g["titulo"], "user_prompt": txt,
                                   "funciones": [{"function_id": function_id(g["sinco_code"], f["orden"]), "orden": f["orden"],
                                                  "texto": f["texto"], "item_fusionado": f["item_fusionado"]} for f in g["funciones"]]})
            doc = {"run_id": rid, "batch_id": bid, "route": "S", "prompt_version": prompt.version, "prompt_sha256": prompt.sha256,
                   "source_sha256": universo["source_sha256"], "model": s["model"], "run_date": fecha, "capability_cutoff": cutoff,
                   "order_seed": seed, "n_grupos": len(lote), "n_funciones": len(fids), "function_ids": fids,
                   "temperature_requested": None, "temperature_controlled": False, "temperature_note": s["temperature_note"],
                   "system_prompt": sys_txt, "grupos": grupos_doc, "formato_salida": OUTPUT_FORMAT,
                   "mensaje_subagente": armar_mensaje(sys_txt, grupos_txt, len(fids))}
            p = base / "inputs" / rid / f"{bid}.json"
            _write_json(p, doc)
            estado_lotes[bid] = {"estado": "pendiente", "intentos": 0, "n_grupos": len(lote), "n_funciones": len(fids),
                                 "input_sha256": sha256_file(p), "salida_sha256": None, "historial": []}
        meta = {"run_id": rid, "route": "S", "prompt_version": prompt.version, "prompt_sha256": prompt.sha256,
                "source_sha256": universo["source_sha256"], "model": s["model"], "run_date": fecha, "capability_cutoff": cutoff,
                "order_seed": seed, "lote_grupos": lote_grupos, "tope_funciones": tope, "max_reintentos": s["max_reintentos"],
                "n_lotes": len(lotes), "n_grupos": len(universo["grupos"]), "n_funciones": len(claves_universo(universo)),
                "grupos_sin_funciones": universo["sin_funciones"],
                "creado": dt.datetime.now().isoformat(timespec="seconds")}
        _write_json(base / rid / "run_meta.json", meta)
        _write_json(base / rid / "estado.json", {"run_id": rid, "detenida": False, "lotes": estado_lotes})
        resumen[rid] = {"lotes": len(lotes), "grupos": sum(l["n_grupos"] for l in estado_lotes.values()),
                        "funciones": sum(l["n_funciones"] for l in estado_lotes.values()),
                        "max_funciones_lote": max(l["n_funciones"] for l in estado_lotes.values())}
    return resumen


# ----------------------------------------------------------------------------- estado
def _paths(run_id: str, base: Path) -> dict:
    r = Path(base) / run_id
    return {"dir": r, "estado": r / "estado.json", "meta": r / "run_meta.json", "intentos": r / "intentos", "salida": r / "salida",
            "inputs": Path(base) / "inputs" / run_id, "parquet": Path(base) / "parquet" / f"run_{run_id}.parquet"}


def cargar_estado(run_id: str, base: Path = BASE) -> dict:
    p = _paths(run_id, base)["estado"]
    if not p.exists():
        raise FileNotFoundError(f"no existe {p}; ¿se hizo el export?")
    return _read_json(p)


def guardar_estado(est: dict, base: Path = BASE) -> None:
    _write_json(_paths(est["run_id"], base)["estado"], est)


def resumen_estado(est: dict) -> dict:
    c = {e: 0 for e in ESTADOS}
    for l in est["lotes"].values():
        c[l["estado"]] += 1
    primer = [l["historial"][0]["resultado"] for l in est["lotes"].values() if l["historial"]]
    n_primer = len(primer)
    rech = sum(1 for r in primer if r != "ok")
    return {"run_id": est["run_id"], "n_lotes": len(est["lotes"]), **c, "detenida": est.get("detenida", False),
            "intentos_totales": sum(l["intentos"] for l in est["lotes"].values()),
            "primer_intento_evaluados": n_primer, "primer_intento_rechazados": rech,
            "tasa_rechazo_primer_intento": (rech / n_primer) if n_primer else None}


def _issue(run_id: str, texto: str, issues_dir: Path | None = None) -> Path:
    d = Path(issues_dir) if issues_dir else C.ISSUES_DIR
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"anotacion-ruta-s-{run_id}.md"
    if not p.exists():
        p.write_text(f"# Issue: corrida ruta S {run_id}\n\nRegistrado por src/annotate/ruta_s.py (regla 5). No se inventa ninguna anotacion.\n",
                     encoding="utf-8")
    with open(p, "a", encoding="utf-8") as fh:
        fh.write(f"\n- {dt.datetime.now().isoformat(timespec='seconds')}: {texto}\n")
    return p


# ----------------------------------------------------------------------------- validacion de un lote
def validar_respuesta(texto: str, doc: dict) -> tuple[list[ModelOutputS], list[str]]:
    """Validacion estricta de la respuesta de un lote. Devuelve (registros_validos, errores). El lote es valido
    solo si errores == [] (no se acepta un lote a medias)."""
    errores: list[str] = []
    esperados = list(doc["function_ids"])
    vistos: dict[str, ModelOutputS] = {}
    repetidos: set[str] = set()
    lineas = texto.strip().splitlines()
    if not lineas or not texto.strip():
        return [], ["respuesta vacia"]
    for n, ln in enumerate(lineas, start=1):
        if not ln.strip():
            errores.append(f"linea {n}: linea en blanco")
            continue
        try:
            obj = json.loads(ln)
        except ValueError as e:
            errores.append(f"linea {n}: no es JSON ({str(e)[:60]}) | crudo: {ln[:80]!r}")
            continue
        if not isinstance(obj, dict):
            errores.append(f"linea {n}: no es un objeto JSON")
            continue
        try:
            o = ModelOutputS.model_validate(obj)
        except ValidationError as e:
            errores.append(f"linea {n}: fuera de esquema {[ (x['loc'], x['type']) for x in e.errors(include_url=False, include_input=False)]}")
            continue
        if o.function_id not in esperados:
            errores.append(f"linea {n}: function_id {o.function_id} no pertenece al lote")
            continue
        if o.function_id in vistos or o.function_id in repetidos:
            repetidos.add(o.function_id)
            errores.append(f"function_id duplicado: {o.function_id}")
            continue
        vistos[o.function_id] = o
    faltan = [f for f in esperados if f not in vistos and f not in repetidos]
    if faltan:
        errores.append(f"faltan {len(faltan)} function_id: {faltan[:5]}{'...' if len(faltan) > 5 else ''}")
    return [vistos[f] for f in esperados if f in vistos and f not in repetidos], errores


# ----------------------------------------------------------------------------- transiciones de lote
def _lote(est: dict, lote: str) -> dict:
    if lote not in est["lotes"]:
        raise KeyError(f"lote {lote} no existe en {est['run_id']}")
    return est["lotes"][lote]


def iniciar(run_id: str, lote: str, base: Path = BASE) -> int:
    est = cargar_estado(run_id, base)
    if est.get("detenida"):
        raise RuntimeError(f"{run_id} esta detenida por un lote fallido; requiere decision humana")
    l = _lote(est, lote)
    max_int = _max_intentos(run_id, base)
    if l["estado"] == "ok":
        raise RuntimeError(f"{lote} ya esta ok")
    if l["intentos"] >= max_int:
        raise RuntimeError(f"{lote} agoto sus {max_int} intentos")
    l["estado"] = "en_curso"
    guardar_estado(est, base)
    return l["intentos"] + 1


def interrumpir(run_id: str, lote: str, base: Path = BASE) -> None:
    """Cuota o error de herramienta: no cuenta como intento invalido (015 3.7.5)."""
    est = cargar_estado(run_id, base)
    l = _lote(est, lote)
    if l["estado"] != "ok":
        l["estado"] = "pendiente" if l["intentos"] == 0 else "invalido"
        l["nota"] = "interrumpido sin respuesta; no cuenta como intento"
    guardar_estado(est, base)


def reanudar(run_id: str, base: Path = BASE) -> list[str]:
    est = cargar_estado(run_id, base)
    cambiados = []
    for b, l in est["lotes"].items():
        if l["estado"] == "en_curso":
            l["estado"] = "pendiente" if l["intentos"] == 0 else "invalido"
            cambiados.append(b)
    guardar_estado(est, base)
    return cambiados


def _max_intentos(run_id: str, base: Path) -> int:
    return _read_json(_paths(run_id, base)["meta"])["max_reintentos"] + 1


def importar_lote(run_id: str, lote: str, *, respuesta: Path | None = None, base: Path = BASE, fecha: str | None = None,
                  issues_dir: Path | None = None, prompt_dir: Path = PROMPT_DIR) -> dict:
    """Valida la respuesta de un lote y actualiza estado.json. No inventa nada. Devuelve el resultado del intento."""
    base = Path(base)
    fecha = fecha or dt.date.today().isoformat()
    P = _paths(run_id, base)
    est = cargar_estado(run_id, base)
    meta = _read_json(P["meta"])
    l = _lote(est, lote)
    max_int = meta["max_reintentos"] + 1
    if l["estado"] == "ok":
        raise RuntimeError(f"{lote} ya esta ok; no se reimporta")
    if est.get("detenida") or l["estado"] == "fallido":
        raise RuntimeError(f"{run_id}/{lote}: corrida detenida o lote fallido definitivo")
    inp = P["inputs"] / f"{lote}.json"
    if sha256_file(inp) != l["input_sha256"]:
        raise ValueError(f"el archivo de entrada {inp.name} cambio desde el export (hash distinto)")
    doc = _read_json(inp)
    if cargar_prompt(doc["prompt_version"], prompt_dir).sha256 != doc["prompt_sha256"]:
        raise ValueError("el prompt cambio desde el export (hash distinto): es otra prompt_version")
    n = l["intentos"] + 1
    P["intentos"].mkdir(parents=True, exist_ok=True)
    destino = P["intentos"] / f"{lote}_a{n}.txt"
    if respuesta is not None:
        if destino.exists():
            raise FileExistsError(f"{destino} ya existe; las respuestas crudas no se sobrescriben")
        destino.write_bytes(Path(respuesta).read_bytes())
    if not destino.exists():
        l["nota"] = f"sin respuesta {destino.name}; no cuenta como intento"
        if l["estado"] == "en_curso":
            l["estado"] = "pendiente" if l["intentos"] == 0 else "invalido"
        guardar_estado(est, base)
        return {"lote": lote, "resultado": "faltante", "intento": n, "errores": [f"no existe {destino.name}"]}
    if n > max_int:
        raise RuntimeError(f"{lote} agoto sus intentos")
    texto = destino.read_text(encoding="utf-8")
    ok_recs, errores = validar_respuesta(texto, doc)
    palabras_largas = sum(1 for o in ok_recs if len(o.rationale.split()) > cfg_s()["rationale_max_palabras"])
    entrada = {"intento": n, "fecha": fecha, "hora": dt.datetime.now().isoformat(timespec="seconds"), "modelo": doc["model"],
               "resp_sha256": sha256_file(destino), "resultado": "ok" if not errores else "invalido",
               "errores": errores[:20], "n_errores": len(errores), "rationale_gt_max_palabras": palabras_largas}
    l["historial"].append(entrada)
    l["intentos"] = n
    l.pop("nota", None)
    if not errores:
        salida = []
        por_id = {o.function_id: o for o in ok_recs}
        for g in doc["grupos"]:
            for f in g["funciones"]:
                o = por_id[f["function_id"]]
                salida.append({"run_id": run_id, "route": "S", "prompt_version": doc["prompt_version"], "prompt_sha256": doc["prompt_sha256"],
                               "model": doc["model"], "run_date": doc["run_date"], "batch_id": lote, "batch_date": fecha, "attempt": n,
                               "sinco_code": g["sinco_code"], "orden": f["orden"], "function_text_es": f["texto"],
                               "item_fusionado": f["item_fusionado"], "source_sha256": doc["source_sha256"], "annotated_text_lang": "es",
                               "exposure_class": o.exposure_class, "eloundou_class": o.eloundou_class,
                               "physical_bottleneck": o.physical_bottleneck, "confidence": o.confidence, "rationale": o.rationale,
                               "capability_cutoff": doc["capability_cutoff"], "temperature_requested": doc["temperature_requested"],
                               "temperature_controlled": doc["temperature_controlled"], "temperature_note": doc["temperature_note"]})
        sp = P["salida"] / f"{lote}.json"
        _write_json(sp, salida)
        l["estado"] = "ok"
        l["salida_sha256"] = sha256_file(sp)
    elif n >= max_int:
        l["estado"] = "fallido"
        est["detenida"] = True
        ip = _issue(run_id, f"LOTE FALLIDO DEFINITIVO {lote} tras {n} intentos; la corrida se detiene hasta decision humana. "
                            f"Ultimos errores: {errores[:5]}", issues_dir)
        entrada["issue"] = str(ip.name)
    else:
        l["estado"] = "invalido"
        _issue(run_id, f"lote {lote} invalido en el intento {n} de {max_int} (se reintenta con subagente nuevo): {errores[:5]}", issues_dir)
    guardar_estado(est, base)
    return {"lote": lote, "resultado": entrada["resultado"], "intento": n, "estado": l["estado"], "errores": errores}


def importar_corrida(run_id: str, *, base: Path = BASE, fecha: str | None = None, issues_dir: Path | None = None,
                     prompt_dir: Path = PROMPT_DIR) -> dict:
    """Importa todo lote no-ok que tenga un archivo de intento nuevo. Lotes sin respuesta quedan listados como faltantes."""
    est = cargar_estado(run_id, base)
    res, faltantes = [], []
    for b in sorted(est["lotes"]):
        l = est["lotes"][b]
        if l["estado"] in ("ok", "fallido"):
            continue
        nxt = _paths(run_id, base)["intentos"] / f"{b}_a{l['intentos'] + 1}.txt"
        if not nxt.exists():
            faltantes.append(b)
            continue
        res.append(importar_lote(run_id, b, base=base, fecha=fecha, issues_dir=issues_dir, prompt_dir=prompt_dir))
        if cargar_estado(run_id, base).get("detenida"):
            break
    est = cargar_estado(run_id, base)
    if faltantes and not est.get("detenida"):
        _issue(run_id, f"lotes sin respuesta pendiente de importar: {faltantes}", issues_dir)
        est["faltantes"] = faltantes
        guardar_estado(est, base)
    out = {"run_id": run_id, "importados": res, "faltantes": faltantes, "parquet": None}
    if all(l["estado"] == "ok" for l in est["lotes"].values()):
        out["parquet"] = str(ensamblar(run_id, base=base, issues_dir=issues_dir))
    return out


def ensamblar(run_id: str, *, base: Path = BASE, issues_dir: Path | None = None, overwrite: bool = False) -> Path:
    """Une los lotes ok en run_<run_id>.parquet validando contra el esquema. Fila fuera de esquema -> issue y se detiene."""
    P = _paths(run_id, base)
    est = cargar_estado(run_id, base)
    malos = [b for b, l in est["lotes"].items() if l["estado"] != "ok"]
    if malos:
        raise RuntimeError(f"no se ensambla {run_id}: lotes no ok {malos}")
    recs = []
    try:
        for b in sorted(est["lotes"]):
            sp = P["salida"] / f"{b}.json"
            if sha256_file(sp) != est["lotes"][b]["salida_sha256"]:
                raise ValueError(f"salida {sp.name} cambio desde la importacion")
            recs += [AnnotationS(**{**r, "run_date": dt.date.fromisoformat(r["run_date"]),
                                    "batch_date": dt.date.fromisoformat(r["batch_date"])}) for r in _read_json(sp)]
        esperado = sum(l["n_funciones"] for l in est["lotes"].values())
        if len(recs) != esperado:
            raise ValueError(f"registros {len(recs)} != funciones esperadas {esperado}")
        write_parquet_s(recs, P["parquet"], overwrite=overwrite)
        read_parquet_s(P["parquet"])
    except Exception as e:
        _issue(run_id, f"ENSAMBLE FALLIDO (fila fuera de esquema o inconsistencia): {e}", issues_dir)
        raise
    est["ensamblada"] = True
    guardar_estado(est, base)
    return P["parquet"]


# ----------------------------------------------------------------------------- CLI
def _ids(a, base):
    if a.run_id:
        return [a.run_id]
    d = Path(base)
    return sorted(p.name for p in d.iterdir() if p.is_dir() and (p / "estado.json").exists()) if d.exists() else []


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(prog="python -m src.annotate.ruta_s")
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("export")
    e.add_argument("--corridas", type=int, default=None)
    e.add_argument("--fecha", default=None)
    e.add_argument("--capability-cutoff", default=None)
    e.add_argument("--model", default=None, help="texto del campo model (decision 018); por defecto el de config")
    e.add_argument("--alias", default=None, help="alias en el run_id (p. ej. haiku, opus)")
    e.add_argument("--prompt-version", default=None, help="version del prompt (por defecto la de config); p. ej. ann-s-v2 (decision 018 R1.4)")
    for nm in ("estado", "mensaje", "iniciar", "interrumpir", "reanudar", "importar", "ensamblar"):
        x = sub.add_parser(nm)
        x.add_argument("--run-id", required=(nm != "estado"))
        if nm in ("mensaje", "iniciar", "interrumpir"):
            x.add_argument("--lote", required=True)
        if nm == "importar":
            x.add_argument("--lote")
            x.add_argument("--respuesta")
            x.add_argument("--fecha")
        if nm == "estado":
            x.add_argument("--detalle", action="store_true")
    v = sub.add_parser("validar")
    v.add_argument("--run-ids", nargs="+", required=True)
    v.add_argument("--n-esperado", type=int, default=3)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "export":
            s = cfg_s()
            r = export(n_corridas=a.corridas or s["n_corridas"], fecha=a.fecha or dt.date.today().isoformat(),
                       capability_cutoff=a.capability_cutoff, model=a.model, alias=a.alias,
                       prompt=cargar_prompt(a.prompt_version) if a.prompt_version else None)
            print(json.dumps(r, indent=1, ensure_ascii=False))
        elif a.cmd == "estado":
            for rid in _ids(a, BASE):
                est = cargar_estado(rid)
                r = resumen_estado(est)
                print(json.dumps(r, ensure_ascii=False))
                if a.detalle:
                    for b, l in est["lotes"].items():
                        if l["estado"] != "ok":
                            print(f"  {b}: {l['estado']} intentos={l['intentos']}")
        elif a.cmd == "mensaje":
            print(_read_json(_paths(a.run_id, BASE)["inputs"] / f"{a.lote}.json")["mensaje_subagente"])
        elif a.cmd == "iniciar":
            print(f"intento {iniciar(a.run_id, a.lote)}")
        elif a.cmd == "interrumpir":
            interrumpir(a.run_id, a.lote)
        elif a.cmd == "reanudar":
            print(reanudar(a.run_id))
        elif a.cmd == "importar":
            if a.lote:
                r = importar_lote(a.run_id, a.lote, respuesta=Path(a.respuesta) if a.respuesta else None, fecha=a.fecha)
            else:
                r = importar_corrida(a.run_id, fecha=a.fecha)
            print(json.dumps(r, indent=1, ensure_ascii=False))
        elif a.cmd == "ensamblar":
            print(ensamblar(a.run_id))
        elif a.cmd == "validar":
            from . import ruta_s_validacion as V
            r = V.validar_corrida_completa(a.run_ids, n_esperado=a.n_esperado)
            print(json.dumps(r, indent=1, ensure_ascii=False))
            return 0 if r["aceptada"] else 2
    except (RuntimeError, ValueError, FileExistsError, FileNotFoundError, KeyError) as ex:
        print(f"ERROR: {ex}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
