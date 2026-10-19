"""Embeddings locales (sentence-transformers) con revision (commit) fijada. Sin APIs."""
from __future__ import annotations

import hashlib
import platform
import random

import numpy as np


def fijar_semilla(seed: int) -> None:
    import torch
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def cargar_modelo(hf_id: str, revision: str, max_length: int, local_only: bool = False):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(hf_id, revision=revision, device="cpu", local_files_only=local_only,
                                model_kwargs={"torch_dtype": "float32"})
    model.max_seq_length = max_length
    return model


def codificar(model, textos: list[str], batch_size: int = 16) -> np.ndarray:
    """Vectores L2-normalizados, float32, en el orden de entrada."""
    v = model.encode(textos, batch_size=batch_size, convert_to_numpy=True, normalize_embeddings=True,
                     show_progress_bar=False)
    return np.ascontiguousarray(v, dtype=np.float32)


def hash_matriz(m: np.ndarray) -> str:
    m = np.ascontiguousarray(m, dtype=np.float32)
    h = hashlib.sha256()
    h.update(str(m.shape).encode())
    h.update(m.tobytes())
    return h.hexdigest()


def versiones() -> dict:
    import importlib.metadata as md
    out = {"python": platform.python_version(), "plataforma": platform.platform()}
    for p in ("torch", "transformers", "sentence-transformers", "scikit-learn", "scipy", "numpy", "pandas", "pyarrow",
              "pydantic", "huggingface-hub"):
        try:
            out[p] = md.version(p)
        except md.PackageNotFoundError:
            out[p] = "NA"
    return out
