"""Carga y hash de la configuracion versionada (src/match/config.toml). Los parametros viven aqui, no en el codigo."""
from __future__ import annotations

import hashlib
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data" / "processed"
CONFIG_PATH = Path(__file__).with_name("config.toml")


def cargar(path: Path | str = CONFIG_PATH) -> dict:
    with open(path, "rb") as f:
        cfg = tomllib.load(f)
    validar(cfg)
    return cfg


def validar(cfg: dict) -> None:
    for sec in ("meta", "recuperacion", "texto", "modelos", "puente_fo"):
        if sec not in cfg:
            raise ValueError(f"config: falta la seccion [{sec}]")
    if cfg["meta"]["estado_validacion"] != "sin_validar":
        raise ValueError("config: estado_validacion debe ser 'sin_validar' (005 R.4.4)")
    if cfg["meta"]["modelo_principal"] not in cfg["modelos"]:
        raise ValueError("config: modelo_principal no esta en [modelos]")
    for nombre, m in cfg["modelos"].items():
        for k in ("hf_id", "revision", "max_length", "delta", "tau"):
            if k not in m:
                raise ValueError(f"config: modelo {nombre} sin '{k}'")
        if len(m["revision"]) != 40:
            raise ValueError(f"config: modelo {nombre} sin revision (commit) fijada")


def hash_config(path: Path | str = CONFIG_PATH) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
