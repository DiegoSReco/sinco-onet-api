"""Determinismo: dos corridas con la misma semilla dan el mismo hash de vectores. Requiere pesos en cache (HF_HOME)."""
import os
from pathlib import Path

import pytest

os.environ.setdefault("HF_HOME", str(Path.home() / "hf_cache"))
from src.match import config as C  # noqa: E402

CACHE = Path(os.environ["HF_HOME"]) / "hub" / "models--intfloat--multilingual-e5-large"
pytestmark = pytest.mark.skipif(not CACHE.exists(), reason="pesos no descargados")

TEXTOS = ["query: Directores generales en empresas", "query: Chief Executives. Determine and formulate policies.",
          "query: Panaderos y reposteros", "query: Bakers. Mix and bake ingredients to produce breads and pastries."]


def _hash(nombre):
    from src.match import embed
    cfg = C.cargar()
    m = cfg["modelos"][nombre]
    embed.fijar_semilla(cfg["meta"]["seed"])
    modelo = embed.cargar_modelo(m["hf_id"], m["revision"], m["max_length"], local_only=True)
    return embed.hash_matriz(embed.codificar(modelo, TEXTOS))


def test_mismo_hash_en_dos_corridas():
    assert _hash("multilingual-e5-large") == _hash("multilingual-e5-large")
