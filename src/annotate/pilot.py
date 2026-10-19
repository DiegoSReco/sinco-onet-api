"""Seleccion reproducible del piloto (semilla en config.toml) y tabla de entrada de tareas.

Fuentes: data/processed/tareas_onet_en.parquet, tareas_onet_ratings.parquet, onet_ocupaciones.parquet.
task_type NO esta en las tablas procesadas; se lee (solo lectura) de Task Statements.txt dentro de
data/raw/onet_db_31_0_text.zip, verificando el sha256 contra data/raw/manifest.json.
"""
from __future__ import annotations

import hashlib
import io
import json
import random
import zipfile
from pathlib import Path

import pandas as pd

from . import config as C

RAW_ZIP = C.ROOT / "data" / "raw" / "onet_db_31_0_text.zip"
MANIFEST = C.ROOT / "data" / "raw" / "manifest.json"
PILOT_PATH = C.ANN_DIR / "piloto_tareas.parquet"


def cargar_task_types(zip_path: Path = RAW_ZIP, verificar_hash: bool = True) -> pd.DataFrame:
    if verificar_hash:
        esperado = next(m["sha256"] for m in json.loads(MANIFEST.read_text(encoding="utf-8")) if m["id"] == "onet_31_0_text")
        if hashlib.sha256(Path(zip_path).read_bytes()).hexdigest() != esperado:
            raise ValueError("el zip de O*NET no coincide con el hash del manifest")
    with zipfile.ZipFile(zip_path) as z:
        s = pd.read_csv(io.BytesIO(z.read("db_31_0_text/Task Statements.txt")), sep="\t", dtype=str)
    s = s.rename(columns={"O*NET-SOC Code": "onet_soc_code", "Task ID": "task_id", "Task Type": "task_type_raw"})
    s["task_type"] = s["task_type_raw"].map({"Core": "core", "Supplemental": "supplemental"})
    return s[["task_id", "onet_soc_code", "task_type"]]


def construir_tabla_tareas(proc: Path = C.PROC, task_types: pd.DataFrame | None = None) -> pd.DataFrame:
    t = pd.read_parquet(proc / "tareas_onet_en.parquet")
    occ = pd.read_parquet(proc / "onet_ocupaciones.parquet")[["onet_soc_code", "titulo_en"]]
    r = pd.read_parquet(proc / "tareas_onet_ratings.parquet")
    k = ["task_id", "onet_soc_code"]
    imp = r[r.scale_id == "IM"][k + ["data_value"]].rename(columns={"data_value": "importance_im"})
    rel = r[r.scale_id == "RT"][k + ["data_value"]].rename(columns={"data_value": "relevance_rt"})
    d = t.merge(occ, on="onet_soc_code", how="left").merge(imp, on=k, how="left").merge(rel, on=k, how="left")
    if task_types is None:
        task_types = cargar_task_types()
    d = d.merge(task_types, on=k, how="left")
    d = d.rename(columns={"onet_soc_code": "onet_soc", "tarea_en": "task_text_en", "titulo_en": "onet_title"})
    d["task_text_es"] = None
    d["major_group"] = d["onet_soc"].str[:2]
    if d["onet_title"].isna().any():
        raise ValueError("tareas con onet_soc sin titulo en onet_ocupaciones")
    d["task_id"] = d["task_id"].astype(str)
    return d.sort_values(["onet_soc", "task_id"]).reset_index(drop=True)


def _elegir(sub: pd.DataFrame, n: int, rng: random.Random) -> list[int]:
    """Una tarea por ocupacion; reparte en ronda entre grupos mayores SOC (orden barajado con la semilla)."""
    por_grupo: dict[str, list[str]] = {}
    for soc in sorted(sub.onet_soc.unique()):
        por_grupo.setdefault(soc[:2], []).append(soc)
    grupos = sorted(por_grupo)
    rng.shuffle(grupos)
    for g in grupos:
        rng.shuffle(por_grupo[g])
    elegidos: list[int] = []
    while len(elegidos) < n and any(por_grupo.values()):
        for g in grupos:
            if len(elegidos) >= n:
                break
            if por_grupo[g]:
                soc = por_grupo[g].pop()
                elegidos.append(rng.choice(sorted(sub.index[sub.onet_soc == soc])))
    if len(elegidos) < n:
        raise ValueError("no hay suficientes ocupaciones en el estrato")
    return elegidos


def seleccionar_piloto(tabla: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    p = cfg["piloto"]
    rng = random.Random(p["seed"])
    partes = []
    for tipo, n in (("core", p["n_core"]), ("supplemental", p["n_supplemental"]), (None, p["n_sin_tipo"])):
        sub = tabla[tabla.task_type.isna()] if tipo is None else tabla[tabla.task_type == tipo]
        s = tabla.loc[_elegir(sub, n, rng)].copy()
        s["stratum"] = tipo or "sin_tipo"
        partes.append(s)
    out = pd.concat(partes).sort_values(["stratum", "onet_soc", "task_id"]).reset_index(drop=True)
    if out.task_id.duplicated().any() or len(out) != p["n_total"]:
        raise ValueError("piloto invalido")
    return out


def guardar_piloto(piloto: pd.DataFrame, cfg: dict, path: Path = PILOT_PATH) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    piloto.to_parquet(path, index=False)
    meta = {"seed": cfg["piloto"]["seed"], "n_total": len(piloto),
            "asignacion": {k: cfg["piloto"][k] for k in ("n_core", "n_supplemental", "n_sin_tipo")},
            "composicion_por_estrato": piloto.stratum.value_counts().to_dict(),
            "n_ocupaciones": int(piloto.onet_soc.nunique()), "n_grupos_mayores": int(piloto.major_group.nunique()),
            "onet_version": cfg["meta"]["onet_version"], "config_sha256": C.hash_config(),
            "fuente_task_type": "data/raw/onet_db_31_0_text.zip :: Task Statements.txt (solo lectura)"}
    path.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")


def cargar_piloto(path: Path = PILOT_PATH) -> pd.DataFrame:
    return pd.read_parquet(path)


def main() -> None:
    cfg = C.cargar()
    piloto = seleccionar_piloto(construir_tabla_tareas(), cfg)
    guardar_piloto(piloto, cfg)
    print(piloto.stratum.value_counts().to_string())
    print("ocupaciones:", piloto.onet_soc.nunique(), "grupos mayores:", piloto.major_group.nunique())


if __name__ == "__main__":
    main()
