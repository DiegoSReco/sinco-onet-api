"""Revision manual de los matches SINCO -> O*NET de baja confianza / sin coincidencia.

Uso:
  .venv\\Scripts\\python -m src.match.revision_manual exportar
  .venv\\Scripts\\python -m src.match.revision_manual aplicar RUTA\\revision_manual.csv [--revisor NOMBRE]

exportar: genera data/processed/revision_manual/{revision_manual.csv, onet_catalogo_consulta.csv, LEEME_revision_manual.md,
          exportacion_meta.json}. Solo lee tablas ya generadas (no carga modelos, no descarga nada). NO es la muestra de oro
          ciega: aqui se muestran las similitudes. No incluye probabilidades de Frey-Osborne ni puntajes de exposicion.
aplicar:  valida estrictamente el CSV llenado; si falla escribe un issue en docs/issues/ y sale con codigo 2 SIN modificar
          nada. Si valida, aplica la politica PROVISIONAL (revision_manual_config.toml; ver
          docs/issues/revision-manual-2026-10-19-politica-provisional.md): la decision manual reemplaza los pares automaticos del
          grupo en crosswalk.parquet, se recalcula la probabilidad de automatizacion (Frey-Osborne) solo de esos grupos, se archiva
          la salida previa y se registra la corrida. Todo numero sale de este script / pfo.py (regla 1).
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import os
import shutil
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from . import config as C
from . import pfo, retrieve, schemas

ROOT = C.ROOT
PROC = C.PROC
ISSUES = ROOT / "docs" / "issues"
CONFIG_REV = Path(__file__).with_name("revision_manual_config.toml")
TAG = {"bge-m3": "bge", "multilingual-e5-large": "e5"}
POLITICA = "provisional-2026-10-19"

COLS_REVISOR = ["decision", "onet_manual_1", "onet_manual_2", "peso_1", "peso_2", "confianza_revisor", "comentarios",
                "revisor", "fecha"]
N_CAND_MAX = 10
COLS_CAND = [f"cand{i}" for i in range(1, N_CAND_MAX + 1)]
COLS_INFO = ["sinco_code", "titulo", "nivel", "division", "division_titulo", "estado_match", "estado_match_e5",
             "sim_top1_bge", "margen_bge", "descripcion", "ocupaciones_ejemplo", "funciones", "auto_rango1", "auto_rango2"]
COLUMNAS = COLS_INFO + COLS_CAND + COLS_REVISOR
INSUMOS_EXPORTAR = ["sinco", "sinco_descripcion", "sinco_funciones", "sinco_ocupaciones_ejemplo", "onet_ocupaciones",
                    "match_candidatos", "match_sinco_resumen"]
INSUMOS_APLICAR = ["sinco", "onet_ocupaciones", "match_candidatos", "match_sinco_resumen", "crosswalk",
                   "sinco_probabilidad_fo", "match_corridas", "puente_onet_soc2019_soc2010", "frey_osborne_probabilidades"]
PROBS = ["probabilidad_automatizacion_fo", "probabilidad_automatizacion_fo_media_uniforme", "probabilidad_automatizacion_fo_min",
         "probabilidad_automatizacion_fo_max", "probabilidad_automatizacion_fo_top1",
         "probabilidad_automatizacion_fo_ponderada_sin_filtro"]


# ------------------------------------------------------------------ utilidades
def cargar_config(path: Path = CONFIG_REV) -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


def sha256_archivo(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _una_linea(x) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return ""
    return " ".join(str(x).split())


def _recortar(txt: str, n: int) -> str:
    txt = _una_linea(txt)
    if len(txt) <= n:
        return txt
    return txt[: n - 3].rstrip() + "..."


def _modelos(cfg_match: dict) -> tuple[str, str]:
    principal = cfg_match["meta"]["modelo_principal"]
    alts = [m for m in cfg_match["modelos"] if m != principal]
    return principal, alts[0]


def _na(x) -> bool:
    return x is None or (not isinstance(x, str) and pd.isna(x))


# ------------------------------------------------------------------ exportar
def _fila_cand(code, titulo, info, tag_p, tag_a) -> str:
    def f(tag, d):
        return f"{tag} {d[0]:.3f} (#{d[1]})" if d else f"{tag} fuera del top-10"
    return f"{code} | {titulo} | {f(tag_p, info.get('p'))} | {f(tag_a, info.get('a'))}"


def exportar(proc: Path = PROC, salida: Path | None = None, cfg_rev: dict | None = None, ahora: datetime | None = None) -> dict:
    cfg_rev = cfg_rev or cargar_config()
    cfg_match = C.cargar()
    ex = cfg_rev["exportacion"]
    principal, alterno = _modelos(cfg_match)
    tag_p, tag_a = TAG.get(principal, principal), TAG.get(alterno, alterno)
    salida = Path(salida) if salida else proc / "revision_manual"
    salida.mkdir(parents=True, exist_ok=True)
    ahora = ahora or datetime.now(timezone.utc)
    t = {n: pd.read_parquet(proc / f"{n}.parquet") for n in INSUMOS_EXPORTAR}
    hashes = {n: sha256_archivo(proc / f"{n}.parquet") for n in INSUMOS_EXPORTAR}

    sinco = t["sinco"].set_index("sinco_code")
    div_tit = t["sinco"][t["sinco"]["nivel"] == "division"].set_index("sinco_code")["titulo"]
    onet = t["onet_ocupaciones"].set_index("onet_soc_code")["titulo_en"]
    res = t["match_sinco_resumen"]
    rp = res[res["modelo"] == principal].set_index("sinco_code")
    ra = res[res["modelo"] == alterno].set_index("sinco_code")
    sel = rp[rp["match_status"].isin(ex["estados_incluidos"])].sort_index()
    cand = t["match_candidatos"]
    cp = {k: g for k, g in cand[cand["modelo"] == principal].groupby("sinco_code")}
    ca = {k: g for k, g in cand[cand["modelo"] == alterno].groupby("sinco_code")}
    tops = ex["top_candidatos_por_modelo"]
    desc = t["sinco_descripcion"].set_index("sinco_code")["descripcion"]
    fun = t["sinco_funciones"].sort_values(["sinco_code", "orden"]).groupby("sinco_code")["funcion"].apply(list)
    ocu = t["sinco_ocupaciones_ejemplo"].sort_values(["sinco_code", "orden"]).groupby("sinco_code")["ocupacion"].apply(list)

    filas = []
    for code, r in sel.iterrows():
        gp, ga = cp[code].set_index("onet_soc_code"), ca[code].set_index("onet_soc_code")
        info: dict[str, dict] = {}
        for oc, x in gp.iterrows():
            info.setdefault(oc, {})["p"] = (float(x["similitud"]), int(x["rango"]))
        for oc, x in ga.iterrows():
            info.setdefault(oc, {})["a"] = (float(x["similitud"]), int(x["rango"]))
        elegidos = [oc for oc, d in info.items() if ("p" in d and d["p"][1] <= tops) or ("a" in d and d["a"][1] <= tops)]
        elegidos.sort(key=lambda oc: (min(info[oc].get("p", (0, 99))[1], info[oc].get("a", (0, 99))[1]),
                                      info[oc].get("p", (0, 99))[1], oc))
        elegidos = elegidos[:ex["max_columnas_candidatos"]]
        celdas = [_fila_cand(oc, onet.get(oc, ""), info[oc], tag_p, tag_a) for oc in elegidos]
        celdas += [""] * (N_CAND_MAX - len(celdas))
        auto = gp.sort_values("rango")
        a12 = [f"{oc} | {onet.get(oc, '')}" for oc in auto.index[:2]]
        a12 += [""] * (2 - len(a12))
        filas.append({
            "sinco_code": code, "titulo": _una_linea(sinco.loc[code, "titulo"]), "nivel": sinco.loc[code, "nivel"],
            "division": sinco.loc[code, "division"], "division_titulo": _una_linea(div_tit.get(str(sinco.loc[code, "division"]), "")),
            "estado_match": r["match_status"], "estado_match_e5": ra.loc[code, "match_status"],
            "sim_top1_bge": round(float(r["sim_top1"]), 4), "margen_bge": round(float(r["margen"]), 4),
            "descripcion": _recortar(desc.get(code, ""), ex["max_chars_descripcion"]),
            "ocupaciones_ejemplo": _recortar("; ".join(ocu.get(code, [])), ex["max_chars_ocupaciones"]),
            "funciones": _recortar(" | ".join(_una_linea(x) for x in fun.get(code, [])), ex["max_chars_funciones"]),
            "auto_rango1": a12[0], "auto_rango2": a12[1], **dict(zip(COLS_CAND, celdas)),
            **{c: "" for c in COLS_REVISOR}})
    df = pd.DataFrame(filas, columns=COLUMNAS)
    p_csv = salida / "revision_manual.csv"
    df.to_csv(p_csv, index=False, encoding="utf-8-sig", lineterminator="\r\n")

    cat = t["onet_ocupaciones"].sort_values("onet_soc_code").rename(columns={"onet_soc_code": "codigo_onet"})
    cat["descripcion_en"] = cat["descripcion_en"].map(_una_linea)
    cat[["codigo_onet", "titulo_en", "descripcion_en"]].to_csv(salida / "onet_catalogo_consulta.csv", index=False,
                                                              encoding="utf-8-sig", lineterminator="\r\n")
    por_estado = df["estado_match"].value_counts().to_dict()
    (salida / "LEEME_revision_manual.md").write_text(_leeme(por_estado, len(df), principal, alterno, ex, len(cat)),
                                                     encoding="utf-8")
    meta = {"fecha_utc": ahora.strftime("%Y-%m-%dT%H:%M:%SZ"), "modelo_principal": principal, "modelo_alterno": alterno,
            "n_grupos": int(len(df)), "n_por_estado": {k: int(v) for k, v in por_estado.items()},
            "estados_incluidos": ex["estados_incluidos"], "hashes_tablas_entrada": hashes,
            "hash_revision_manual_csv": sha256_archivo(p_csv), "n_ocupaciones_catalogo": int(len(cat)),
            "columnas": COLUMNAS, "parametros_exportacion": ex, "hash_config_revision": sha256_archivo(CONFIG_REV),
            "politica": POLITICA}
    (salida / "exportacion_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return meta


def _leeme(por_estado: dict, n: int, principal: str, alterno: str, ex: dict, n_onet: int) -> str:
    est = ", ".join(f"{k}: {v}" for k, v in sorted(por_estado.items()))
    return f"""# Revision manual de matches SINCO -> O*NET

Archivo generado por `python -m src.match.revision_manual exportar`. Contiene **{n} grupos unitarios SINCO 2019**
cuyo match automatico ({principal}) quedo en `baja_confianza` o `sin_coincidencia` ({est}).

**Esto NO es la muestra de oro ciega.** Aqui si se muestran las similitudes de los dos modelos y los pares automaticos; sirve
para corregir el crosswalk, no para medir la calidad del metodo. **No hace falta consultar probabilidades de automatizacion**:
no se incluyen en el archivo (tampoco puntajes de exposicion).

## Como llenarlo
Abra `revision_manual.csv` en Excel (UTF-8; si los acentos se ven mal use Datos > Desde texto/CSV con codificacion UTF-8).
Para cada fila lea el titulo, la descripcion, las ocupaciones ejemplo y las funciones, compare con los candidatos O*NET y
llene SOLO las columnas de la derecha. Una fila sin `decision` se considera no revisada y se ignora. Guarde como **CSV UTF-8**
con los mismos nombres de columna y devuelva el archivo: se valida y se aplica con
`python -m src.match.revision_manual aplicar archivo.csv`. Para buscar codigos use `onet_catalogo_consulta.csv`
({n_onet} ocupaciones: codigo, titulo EN, descripcion EN).

## Columnas informativas (no editar)
`sinco_code`, `titulo`, `nivel`, `division`, `division_titulo`, `estado_match` ({principal}), `estado_match_e5` ({alterno}),
`sim_top1_bge` y `margen_bge` (coseno del mejor candidato y su ventaja sobre el segundo; no son probabilidades),
`descripcion` (maximo {ex['max_chars_descripcion']} caracteres), `ocupaciones_ejemplo` (maximo {ex['max_chars_ocupaciones']};
separadas por `;`), `funciones` (maximo {ex['max_chars_funciones']}; separadas por ` | `; un recorte termina en `...`),
`auto_rango1` / `auto_rango2` (los 2 pares automaticos del crosswalk actual: codigo | titulo EN).
`cand1`..`cand10`: union sin duplicados de los top-5 de {principal} y de {alterno}, ordenados por su mejor rango, cada uno como
`codigo | titulo EN | bge similitud (#rango) | e5 similitud (#rango)`; "fuera del top-10" si ese modelo no lo guardo.

## Columnas del revisor
| Columna | Contenido |
|---|---|
| `decision` | `ACEPTAR_RANGO1` (queda solo `auto_rango1`), `ACEPTAR_RANGO2` (solo `auto_rango2`), `ACEPTAR_AMBOS` (los dos automaticos), `OTRO` (usted da los codigos), `NINGUNO` (ningun O*NET equivale al grupo), `DUDA` (no resuelto; se ignora y se lista) |
| `onet_manual_1`, `onet_manual_2` | codigos O*NET-SOC completos (ej. `17-2151.00`). Obligatorio `onet_manual_1` si `decision = OTRO`; `onet_manual_2` opcional. Deben quedar vacios en las demas decisiones |
| `peso_1`, `peso_2` | opcionales, numeros > 0, solo con dos pares (`ACEPTAR_AMBOS` u `OTRO` con dos codigos): importancia relativa de cada par (se normalizan). Si no los da, pesan igual. Dé ambos o ninguno |
| `confianza_revisor` | `alta`, `media` o `baja` (opcional) |
| `comentarios` | texto libre (opcional) |
| `revisor`, `fecha` | quien revisa y cuando (texto). `revisor` es obligatorio en las filas que se aplican (o se pasa `--revisor`) |

## Que pasa al aplicar (politica PROVISIONAL)
La decision REEMPLAZA los pares automaticos de ese grupo en `crosswalk.parquet` (fuente `manual`, estado
`revision_manual_1_revisor`: un solo revisor, sin segunda lectura). La probabilidad de automatizacion se recalcula solo para los
grupos revisados (pesos del revisor o iguales); las demas filas no cambian. La salida previa se archiva en
`revision_manual/previo_<fecha>/` y los cambios quedan en `data/processed/revision_manual_cambios.parquet`. Si el archivo no
cumple las reglas no se modifica nada y se escribe un issue con las filas a corregir.
"""


# ------------------------------------------------------------------ lectura y validacion
def leer_csv(path: Path) -> pd.DataFrame:
    raw = Path(path).read_bytes()
    try:
        txt = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        txt = raw.decode("cp1252")
    primera = txt.splitlines()[0] if txt else ""
    sep = ";" if primera.count(";") > primera.count(",") else ","
    return pd.read_csv(io.StringIO(txt), sep=sep, dtype=str, keep_default_na=False)


def _peso(x: str):
    x = x.strip().replace(",", ".")
    if x == "":
        return None
    v = float(x)   # ValueError -> lo reporta el llamador
    if not math.isfinite(v):
        raise ValueError("no finito")
    return v


def validar(df: pd.DataFrame, t: dict, cfg_rev: dict, revisor_def: str = "") -> tuple[list[dict], dict]:
    """Devuelve (errores, plan). No modifica nada."""
    ap = cfg_rev["aplicacion"]
    perm, conf_perm = set(ap["decisiones"]), set(ap["confianzas"])
    err: list[dict] = []

    def e(fila, code, campo, msg):
        err.append({"fila_csv": fila, "sinco_code": code, "campo": campo, "problema": msg})

    faltan = [c for c in COLUMNAS if c not in df.columns]
    if faltan:
        e("-", "-", "columnas", f"faltan columnas (no deben renombrarse ni borrarse): {faltan}")
        return err, {}
    df = df.copy()
    for c in df.columns:
        df[c] = df[c].astype(str).str.strip()
    unit = set(t["sinco"].loc[t["sinco"]["nivel"] == "grupo_unitario", "sinco_code"])
    onet = set(t["onet_ocupaciones"]["onet_soc_code"])
    dup = set(df["sinco_code"][df["sinco_code"].duplicated(keep=False)])
    plan = {"aplicar": [], "duda": [], "pendientes": [], "n_filas": int(len(df))}
    for i, r in df.iterrows():
        fila, code = i + 2, r["sinco_code"]
        if code not in unit:
            e(fila, code, "sinco_code", "no existe como grupo unitario en sinco.parquet")
            continue
        if code in dup:
            e(fila, code, "sinco_code", "sinco_code duplicado en el archivo")
            continue
        dec = r["decision"].upper()
        c1, c2 = r["onet_manual_1"], r["onet_manual_2"]
        extras = [c for c in ("onet_manual_1", "onet_manual_2", "peso_1", "peso_2") if r[c] != ""]
        if dec == "":
            if extras:
                e(fila, code, "decision", f"decision vacia pero hay datos en {extras}; llene la decision o limpie los campos")
            else:
                plan["pendientes"].append(code)
            continue
        if dec not in perm:
            e(fila, code, "decision", f"valor '{r['decision']}' no permitido; use uno de {sorted(perm)}")
            continue
        n_ant = len(err)
        if r["confianza_revisor"] and r["confianza_revisor"].lower() not in conf_perm:
            e(fila, code, "confianza_revisor", f"'{r['confianza_revisor']}' no permitido; use {sorted(conf_perm)}")
        if dec == "DUDA":
            if len(err) == n_ant:
                plan["duda"].append({"sinco_code": code, "comentarios": r["comentarios"]})
            continue
        for c, v in (("onet_manual_1", c1), ("onet_manual_2", c2)):
            if v and v not in onet:
                hint = f" (quiso decir {v}.00?)" if f"{v}.00" in onet else ""
                e(fila, code, c, f"codigo '{v}' no existe en onet_ocupaciones{hint}")
        if dec in ("ACEPTAR_RANGO1", "ACEPTAR_RANGO2", "ACEPTAR_AMBOS", "NINGUNO") and (c1 or c2):
            e(fila, code, "onet_manual_1/2", f"{dec} no admite codigos manuales; deje vacios o use OTRO")
        if dec == "OTRO":
            if not c1:
                e(fila, code, "onet_manual_1", "OTRO exige al menos onet_manual_1")
            if c1 and c1 == c2:
                e(fila, code, "onet_manual_2", "onet_manual_1 y onet_manual_2 son iguales")
        npar = {"ACEPTAR_RANGO1": 1, "ACEPTAR_RANGO2": 1, "NINGUNO": 0, "ACEPTAR_AMBOS": 2,
                "OTRO": (2 if c2 else 1)}[dec]
        pesos = []
        for c in ("peso_1", "peso_2"):
            try:
                v = _peso(r[c])
            except ValueError:
                e(fila, code, c, f"'{r[c]}' no es un numero")
                v = None
            if v is not None and v <= 0:
                e(fila, code, c, "el peso debe ser > 0")
            pesos.append(v)
        if npar < 2 and any(p is not None for p in pesos):
            e(fila, code, "peso_1/peso_2", "los pesos solo aplican cuando hay dos pares")
        if npar == 2 and ((pesos[0] is None) != (pesos[1] is None)):
            e(fila, code, "peso_1/peso_2", "con dos pares de ambos pesos o ninguno")
        revisor = r["revisor"] or revisor_def
        if not revisor:
            e(fila, code, "revisor", "falta el revisor (columna 'revisor' o --revisor)")
        if len(err) == n_ant:
            plan["aplicar"].append({
                "sinco_code": code, "decision": dec, "onet_manual": [c for c in (c1, c2) if c],
                "pesos": [pesos[0], pesos[1]] if npar == 2 and pesos[0] is not None else [],
                "revisor": revisor, "fecha_revision": r["fecha"], "confianza_revisor": r["confianza_revisor"].lower(),
                "comentarios": r["comentarios"]})
    return err, plan


def _escribir_issue(issues: Path, nombre: str, titulo: str, cuerpo: str) -> Path:
    issues.mkdir(parents=True, exist_ok=True)
    p = issues / nombre
    p.write_text(f"# {titulo}\n\n{cuerpo}\n", encoding="utf-8")
    return p


def _issue_validacion(issues: Path, fecha: str, csv: Path, err: list[dict]) -> Path:
    filas = "\n".join(f"| {x['fila_csv']} | {x['sinco_code']} | {x['campo']} | {x['problema']} |" for x in err)
    cuerpo = (f"Origen: `src/match/revision_manual.py aplicar` sobre `{csv}`. Estado: **detenido; no se modifico ningun dato** (regla 5).\n\n"
              f"Corrija estas {len(err)} filas/campos del CSV y vuelva a ejecutar `aplicar`. `fila_csv` cuenta el encabezado como fila 1.\n\n"
              "| fila_csv | sinco_code | campo | problema |\n|---|---|---|---|\n" + filas)
    return _escribir_issue(issues, f"revision-manual-{fecha}-validacion-fallida.md", "Revision manual: el archivo no cumple las reglas", cuerpo)


# ------------------------------------------------------------------ aplicar
def _norm_records(df: pd.DataFrame, excluir: list[str]) -> list:
    d = df.drop(columns=[c for c in excluir if c in df.columns]).astype(object)
    d = d.where(d.notna(), None)

    def n(v):
        if v is None or v is pd.NA:
            return None
        if isinstance(v, (float, np.floating)):
            return round(float(v), 9)
        if isinstance(v, (np.integer, np.bool_)):
            return v.item()
        return v
    recs = [tuple((k, n(v)) for k, v in sorted(r.items())) for r in d.to_dict("records")]
    return sorted(recs, key=str)


def aplicar(csv: Path, proc: Path = PROC, issues: Path | None = None, revision_dir: Path | None = None,
            fecha: str | None = None, revisor_def: str = "", cfg_rev: dict | None = None, ahora: datetime | None = None) -> int:
    """Codigo de salida: 0 ok / sin cambios, 2 validacion fallida, 3 insumos o esquema de salida invalidos."""
    csv = Path(csv)
    proc = Path(proc)
    cfg_rev = cfg_rev or cargar_config()
    ahora = ahora or datetime.now(timezone.utc)
    fecha = fecha or ahora.strftime("%Y-%m-%d")
    issues = Path(issues) if issues else ISSUES
    revision_dir = Path(revision_dir) if revision_dir else proc / "revision_manual"
    faltan = [n for n in INSUMOS_APLICAR if not (proc / f"{n}.parquet").exists()]
    if faltan:
        _escribir_issue(issues, f"revision-manual-{fecha}-insumos-faltantes.md", "Revision manual: faltan tablas de entrada",
                        f"No existen en `{proc}`: {faltan}. No se modifico nada.")
        print(f"ERROR: faltan tablas {faltan}", file=sys.stderr)
        return 3
    t = {n: pd.read_parquet(proc / f"{n}.parquet") for n in INSUMOS_APLICAR}
    df = leer_csv(csv)
    err, plan = validar(df, t, cfg_rev, revisor_def)
    if err:
        p = _issue_validacion(issues, fecha, csv, err)
        print(f"VALIDACION FALLIDA: {len(err)} problema(s). No se modifico nada. Issue: {p}", file=sys.stderr)
        for x in err[:20]:
            print(f"  fila {x['fila_csv']} sinco {x['sinco_code']} [{x['campo']}]: {x['problema']}", file=sys.stderr)
        return 2
    cfg_match = C.cargar()
    principal, alterno = _modelos(cfg_match)
    ap_meta = cfg_rev["meta"]
    csv_hash = sha256_archivo(csv)
    run_id = f"manual-{fecha}-{csv_hash[:8]}"
    duda, ap = plan["duda"], plan["aplicar"]
    print(f"Filas: {plan['n_filas']}; a aplicar: {len(ap)}; DUDA (ignoradas): {len(duda)}; sin revisar: {len(plan['pendientes'])}")
    for d in duda:
        print(f"  DUDA {d['sinco_code']}: {d['comentarios']}")
    if not ap:
        print("Nada que aplicar.")
        return 0

    cw_old, pf_old = t["crosswalk"], t["sinco_probabilidad_fo"]
    cand = t["match_candidatos"]
    cp = cand[cand["modelo"] == principal].set_index(["sinco_code", "onet_soc_code"])
    ca = cand[cand["modelo"] == alterno].set_index(["sinco_code", "onet_soc_code"])
    rp = t["match_sinco_resumen"]
    rp = rp[rp["modelo"] == principal].set_index("sinco_code")
    rank12 = {(c, int(r)): oc for c, r, oc in cand[(cand["modelo"] == principal) & (cand["rango"] <= 2)]
              [["sinco_code", "rango", "onet_soc_code"]].itertuples(index=False)}
    puente = pfo.mapa_puente(t["puente_onet_soc2019_soc2010"])
    fo = dict(zip(t["frey_osborne_probabilidades"]["soc_2010"], t["frey_osborne_probabilidades"]["probabilidad_automatizacion_fo"]))
    titulos = t["sinco"].set_index("sinco_code")["titulo"]
    pf_p = pf_old[pf_old["modelo"] == principal].set_index("sinco_code")
    oro_p = proc / "oro_muestra.parquet"
    oro_codes = set(pd.read_parquet(oro_p, columns=["sinco_code"])["sinco_code"]) if oro_p.exists() else set()
    est_man = ap_meta["estado_validacion_manual"]
    tau = cfg_match["modelos"][principal]["tau"]

    nuevas, pf_nuevas, cambios, revisados = [], {}, [], set()
    for a in ap:
        code, dec = a["sinco_code"], a["decision"]
        revisados.add(code)
        r1, r2 = rank12.get((code, 1)), rank12.get((code, 2))
        pares = {"ACEPTAR_RANGO1": [r1], "ACEPTAR_RANGO2": [r2], "ACEPTAR_AMBOS": [r1, r2],
                 "OTRO": a["onet_manual"], "NINGUNO": []}[dec]
        pesos = a["pesos"] if (a["pesos"] and len(a["pesos"]) == len(pares)) else None
        w = list(pesos) if pesos else ([1.0] * len(pares))
        w = [x / sum(w) for x in w] if w else []
        for pos, oc in enumerate(pares):
            ip, ia = (code, oc) in cp.index, (code, oc) in ca.index
            rango_p = int(cp.loc[(code, oc), "rango"]) if ip else None
            nuevas.append({
                "sinco_code": code, "onet_soc_code": oc, "fuente": ap_meta["fuente_manual"], "estado_validacion": est_man,
                "run_id": run_id, "modelo": principal,
                "rango": rango_p if (rango_p is not None and rango_p <= 2) else None,
                "similitud": float(cp.loc[(code, oc), "similitud"]) if ip else None,
                "margen": float(rp.loc[code, "margen"]), "baja_confianza": bool(rp.loc[code, "baja_confianza"]),
                "match_status": rp.loc[code, "match_status"],
                "similitud_alt": float(ca.loc[(code, oc), "similitud"]) if ia else None,
                "rango_alt": int(ca.loc[(code, oc), "rango"]) if ia else None,
                "modelo_alt": alterno if ia else None, "_orden": pos,
                "notas": (f"revision manual (1 revisor, sin segunda lectura); decision={dec}; revisor={a['revisor']}; "
                          f"rango_auto_{principal}={'fuera_del_top10' if rango_p is None else rango_p}; peso={w[pos]:.3f}; "
                          f"reemplaza los pares automaticos del grupo; politica {POLITICA}; no es correspondencia oficial")})
        # probabilidad (solo filas del modelo principal)
        fila = pf_p.loc[code].copy()
        antes, motivo_antes = fila["probabilidad_automatizacion_fo"], fila["motivo_na"]
        if pares:
            ag = pfo.agregar_sinco(np.ones(len(pares)), pares, tau, puente, fo, pesos=w)
            vals = dict(zip(PROBS, [ag["p_ponderada"], ag["p_media"], ag["p_min"], ag["p_max"], ag["p_top1"], ag["p_ponderada"]]))
            for k, v in vals.items():
                fila[k] = None if pd.isna(v) else float(v)
            fila["motivo_na"] = None if not pd.isna(ag["p_ponderada"]) else "sin_probabilidad_fo"
            for k in ("n_candidatos", "n_soc2010", "n_soc2010_con_fo", "cobertura_peso_fo", "bandera_multi_soc2010", "bandera_sin_puente",
                      "onet_sin_puente", "bandera_soc_sin_fo", "cobertura_fo", "top1_socs"):
                fila[k] = ag[k]
            fila["top1_onet_soc_code"] = pares[0]
        else:
            for k in PROBS:
                fila[k] = None
            fila["motivo_na"] = ap_meta["motivo_na_ninguno"]
            for k, v in {"n_candidatos": 0, "n_soc2010": 0, "n_soc2010_con_fo": 0, "cobertura_peso_fo": 0.0,
                         "bandera_multi_soc2010": False, "bandera_sin_puente": False, "onet_sin_puente": "",
                         "bandera_soc_sin_fo": False, "cobertura_fo": "ninguna", "top1_socs": "", "top1_onet_soc_code": ""}.items():
                fila[k] = v
        fila["run_id"], fila["estado_validacion"] = run_id, est_man
        pf_nuevas[code] = fila
        despues = fila["probabilidad_automatizacion_fo"]
        antes_pares = cw_old.loc[cw_old["sinco_code"] == code].sort_values("rango")["onet_soc_code"].tolist()
        cambios.append({
            "run_id": run_id, "fecha_aplicacion": ahora.strftime("%Y-%m-%dT%H:%M:%SZ"), "sinco_code": code,
            "titulo": titulos.get(code, ""), "modelo": principal, "decision": dec,
            "pares_antes": "; ".join(antes_pares), "pares_despues": "; ".join(pares),
            "cambio_pares": antes_pares != list(pares),
            "probabilidad_antes": None if pd.isna(antes) else float(antes),
            "probabilidad_despues": None if pd.isna(despues) else float(despues),
            "motivo_na_antes": None if _na(motivo_antes) else motivo_antes,
            "motivo_na_despues": None if _na(fila["motivo_na"]) else fila["motivo_na"],
            "pesos_usados": ";".join(f"{x:.4f}" for x in w), "pesos_dados_por_revisor": pesos is not None,
            "revisor": a["revisor"], "fecha_revision": a["fecha_revision"], "confianza_revisor": a["confianza_revisor"],
            "comentarios": a["comentarios"], "en_muestra_oro": code in oro_codes, "politica": POLITICA})

    # crosswalk nuevo: los grupos revisados se reemplazan; el resto se conserva
    resto = cw_old[~cw_old["sinco_code"].isin(revisados)].copy()
    resto["_k"] = resto["rango"].astype(float)
    cw_new = pd.DataFrame(nuevas)
    if len(cw_new):
        cw_new["_k"] = cw_new["rango"].astype(float).fillna(10 + cw_new["_orden"])
        cw_new = cw_new.drop(columns=["_orden"])
    cw_all = pd.concat([resto, cw_new], ignore_index=True) if len(cw_new) else resto
    cw_all["tipo_relacion"] = retrieve.tipo_relacion(cw_all)
    cw_all = cw_all.sort_values(["sinco_code", "_k"], kind="stable").drop(columns=["_k"]).reset_index(drop=True)
    cw_all = cw_all[list(cw_old.columns)]
    cw_all["rango"] = cw_all["rango"].astype("Int32")
    cw_all["rango_alt"] = cw_all["rango_alt"].astype("Int32")

    # probabilidad nueva (solo los grupos revisados del modelo principal); n_sinco_mismo_top1_soc se recalcula en ese modelo
    pf_all = pf_old.copy()
    for code, fila in pf_nuevas.items():
        idx = pf_all.index[(pf_all["modelo"] == principal) & (pf_all["sinco_code"] == code)][0]
        for k, v in fila.items():
            pf_all.at[idx, k] = v
    m = pf_all["modelo"] == principal
    cnt = pf_all.loc[m].groupby("top1_socs")["sinco_code"].transform("count")
    pf_all.loc[m, "n_sinco_mismo_top1_soc"] = cnt.where(pf_all.loc[m, "top1_socs"] != "", 1).astype(pf_old["n_sinco_mismo_top1_soc"].dtype)

    # esquemas ANTES de escribir (regla 5)
    try:
        tabla_cw = schemas.validar_crosswalk(cw_all, set(t["sinco"]["sinco_code"]), set(t["onet_ocupaciones"]["onet_soc_code"]))
        schemas.validar_pfo(pf_all, set(t["sinco"]["sinco_code"]))
    except schemas.SchemaError as ex:
        p = _escribir_issue(issues, f"revision-manual-{fecha}-esquema-salida.md", "Revision manual: la salida no cumple el esquema",
                            f"{ex}\n\nNo se modifico ningun dato (regla 5).")
        print(f"ERROR de esquema: {ex}. Issue: {p}", file=sys.stderr)
        return 3

    # idempotencia: si nada cambia (salvo run_id) no se escribe ni se archiva
    if (_norm_records(cw_all, ["run_id"]) == _norm_records(cw_old, ["run_id"])
            and _norm_records(pf_all, ["run_id"]) == _norm_records(pf_old, ["run_id"])):
        print("Sin cambios: el archivo ya esta aplicado (idempotente). No se escribio nada.")
        return 0

    # corrida (se conservan las anteriores)
    hashes_in = {n_: sha256_archivo(proc / f"{n_}.parquet") for n_ in INSUMOS_APLICAR}
    corr_new = pd.DataFrame([{
        "run_id": run_id, "modelo": principal, "hf_id": "revision_manual", "revision_modelo": "0" * 40,
        "fecha": ahora.strftime("%Y-%m-%dT%H:%M:%SZ"), "metodo": "revision_manual", "text_template_version": "n/a", "seed": 0,
        "normalizacion": "n/a", "max_length": 0, "n_truncados_sinco": 0, "n_truncados_onet": 0, "dispositivo": "n/a", "dtype": "n/a",
        "hash_matriz_sinco": "0" * 64, "hash_matriz_onet": "0" * 64, "hash_matriz_similitud": "0" * 64,
        "hash_config": sha256_archivo(CONFIG_REV),
        "parametros": json.dumps({"politica": POLITICA, "csv_sha256": csv_hash, "csv_nombre": csv.name, "n_aplicados": len(ap),
                                  "n_duda": len(duda),
                                  "decisiones": pd.Series([a["decision"] for a in ap]).value_counts().to_dict(),
                                  "pesos_sin_dar": "uniformes", "config": cfg_rev}, sort_keys=True, default=str),
        "estado_parametros": ap_meta["estado_parametros"], "estado_validacion": "sin_validar",
        "hashes_insumos": json.dumps(hashes_in, sort_keys=True), "versiones_librerias": json.dumps(
            {"pandas": pd.__version__, "pyarrow": pa.__version__, "numpy": np.__version__}, sort_keys=True),
        "segundos_embedding": 0.0, "vectores_desde_cache": False, "n_sinco": len(ap), "n_onet": int(len(t["onet_ocupaciones"]))}])
    corr_all = pd.concat([t["match_corridas"], corr_new[list(t["match_corridas"].columns)]], ignore_index=True)
    try:
        schemas.validar_corridas(corr_all)
    except schemas.SchemaError as ex:
        p = _escribir_issue(issues, f"revision-manual-{fecha}-esquema-corridas.md", "Revision manual: corrida no cumple el esquema", str(ex))
        print(f"ERROR de esquema: {ex}. Issue: {p}", file=sys.stderr)
        return 3

    cam_new = pd.DataFrame(cambios)
    p_cam = proc / "revision_manual_cambios.parquet"
    cam_all = pd.concat([pd.read_parquet(p_cam), cam_new], ignore_index=True) if p_cam.exists() else cam_new

    # auditoria: archivo previo (nunca se sobrescribe uno existente)
    revision_dir.mkdir(parents=True, exist_ok=True)
    previo = revision_dir / f"previo_{fecha}"
    n = 1
    while previo.exists():
        n += 1
        previo = revision_dir / f"previo_{fecha}_{n}"
    previo.mkdir()
    for nom in ("crosswalk", "sinco_probabilidad_fo", "match_corridas", "revision_manual_cambios"):
        src = proc / f"{nom}.parquet"
        if src.exists():
            shutil.copy2(src, previo / src.name)
    (revision_dir / "aplicadas").mkdir(exist_ok=True)
    shutil.copy2(csv, revision_dir / "aplicadas" / f"{run_id}_revision_manual.csv")

    # escritura via temporales y reemplazo
    tmp = {nom: proc / f"{nom}.parquet.tmp" for nom in ("crosswalk", "sinco_probabilidad_fo", "match_corridas", "revision_manual_cambios")}
    pq.write_table(tabla_cw, tmp["crosswalk"])
    pf_all.to_parquet(tmp["sinco_probabilidad_fo"], index=False)
    corr_all.to_parquet(tmp["match_corridas"], index=False)
    cam_all.to_parquet(tmp["revision_manual_cambios"], index=False)
    for nom, tp in tmp.items():
        os.replace(tp, proc / f"{nom}.parquet")

    key = ["sinco_code", "onet_soc_code"]
    a_ = cw_all[~cw_all["sinco_code"].isin(revisados)][key + ["tipo_relacion"]]
    b_ = cw_old[~cw_old["sinco_code"].isin(revisados)][key + ["tipo_relacion"]]
    n_tipo = int((a_.merge(b_, on=key, suffixes=("_n", "_a"))
                  .eval("tipo_relacion_n != tipo_relacion_a")).sum())
    resumen = {"run_id": run_id, "fecha": fecha, "csv": csv.name, "csv_sha256": csv_hash, "n_aplicados": len(ap),
               "decisiones": pd.Series([a["decision"] for a in ap]).value_counts().to_dict(), "n_duda": len(duda),
               "duda": duda, "n_sin_revisar": len(plan["pendientes"]), "previo": previo.name,
               "n_en_muestra_oro": int(cam_new["en_muestra_oro"].sum()),
               "n_filas_no_revisadas_con_tipo_relacion_recalculado": n_tipo}
    (revision_dir / f"aplicacion_{run_id}.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(resumen, indent=2, ensure_ascii=False))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    e_ = sub.add_parser("exportar")
    e_.add_argument("--proc", default=str(PROC))
    e_.add_argument("--salida", default=None)
    a_ = sub.add_parser("aplicar")
    a_.add_argument("csv")
    a_.add_argument("--proc", default=str(PROC))
    a_.add_argument("--revisor", default="")
    a_.add_argument("--fecha", default=None)
    a = ap.parse_args(argv)
    if a.cmd == "exportar":
        meta = exportar(Path(a.proc), Path(a.salida) if a.salida else None)
        print(json.dumps({k: meta[k] for k in ("fecha_utc", "n_grupos", "n_por_estado", "n_ocupaciones_catalogo")}, ensure_ascii=False))
        return 0
    return aplicar(Path(a.csv), Path(a.proc), revisor_def=a.revisor, fecha=a.fecha)


if __name__ == "__main__":
    sys.exit(main())
