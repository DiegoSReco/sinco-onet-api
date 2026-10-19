"""Carga y validacion de src/annotate/config.toml. Los parametros viven en la configuracion, no en el codigo."""
from __future__ import annotations

import hashlib
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data" / "processed"
ANN_DIR = PROC / "annotations"
ISSUES_DIR = ROOT / "docs" / "issues"
PROMPTS_DOC_DIR = ROOT / "docs" / "prompts"
CONFIG_PATH = Path(__file__).with_name("config.toml")
REQUIERE_DECISION = "requiere decision"


def cargar(path: Path | str = CONFIG_PATH) -> dict:
    with open(path, "rb") as f:
        cfg = tomllib.load(f)
    validar(cfg)
    return cfg


def validar(cfg: dict) -> None:
    for sec in ("meta", "modelo", "capacidades", "texto", "mapa_numerico", "piloto", "corridas", "reintentos"):
        if sec not in cfg:
            raise ValueError(f"config: falta la seccion [{sec}]")
    for nombre, m in cfg["mapa_numerico"].items():
        if set(m) != {"E0", "E1", "E2"}:
            raise ValueError(f"config: mapa {nombre} debe tener E0, E1, E2")
        if not (m["E0"] <= m["E1"] <= m["E2"]) or min(m.values()) < 0 or max(m.values()) > 1:
            raise ValueError(f"config: mapa {nombre} debe ser monotono en [0, 1]")
    p = cfg["piloto"]
    if p["n_core"] + p["n_supplemental"] + p["n_sin_tipo"] != p["n_total"]:
        raise ValueError("config: la asignacion del piloto no suma n_total")
    if cfg["texto"]["idioma_anotado"] not in ("en", "es"):
        raise ValueError("config: idioma_anotado debe ser 'en' o 'es'")


def decision_pendiente(valor) -> bool:
    return valor in (None, "", REQUIERE_DECISION)


def hash_config(path: Path | str = CONFIG_PATH) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
