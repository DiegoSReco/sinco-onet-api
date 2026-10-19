"""Carga, renderizado y registro (docs/prompts/{prompt_version}.md) del prompt versionado."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from . import config as C

PROMPT_DIR = Path(__file__).with_name("prompts")
SYS_MARK, USR_MARK = "<!-- SYSTEM -->", "<!-- USER -->"


@dataclass(frozen=True)
class PromptTemplate:
    version: str
    system: str
    user: str
    raw: str

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.raw.encode("utf-8")).hexdigest()

    def render(self, *, capability_cutoff: str, occupation_title: str, task_text: str, lang: str) -> tuple[str, str]:
        s = self.system.replace("<<capability_cutoff>>", capability_cutoff)
        u = (self.user.replace("<<occupation_title>>", occupation_title)
             .replace("<<task_text>>", task_text).replace("<<lang>>", lang))
        return s, u


def cargar(version: str = "ann-v1") -> PromptTemplate:
    path = PROMPT_DIR / f"{version.removeprefix('ann-')}.md"
    raw = path.read_text(encoding="utf-8")
    if SYS_MARK not in raw or USR_MARK not in raw:
        raise ValueError("prompt sin marcadores SYSTEM/USER")
    _, rest = raw.split(SYS_MARK, 1)
    system, user = rest.split(USR_MARK, 1)
    return PromptTemplate(version, system.strip(), user.strip(), raw)


def cutoff_text(cfg: dict) -> str:
    v = cfg["capacidades"]["fecha_corte"]
    return "no definida (requiere decisión; solo corridas de prueba)" if C.decision_pendiente(v) else str(v)


def guardar_doc(p: PromptTemplate, cfg: dict, doc_dir: Path | None = None) -> Path:
    """Escribe docs/prompts/{version}.md con el prompt completo. Una version no se reescribe con otro contenido."""
    doc_dir = Path(doc_dir) if doc_dir else C.PROMPTS_DOC_DIR
    doc_dir.mkdir(parents=True, exist_ok=True)
    out = doc_dir / f"{p.version}.md"
    cuerpo = (f"# Prompt {p.version}\n\n- sha256 de src/annotate/prompts/{p.version.removeprefix('ann-')}.md: `{p.sha256}`\n"
              f"- Rubrica: docs/rubric.md (version 1). Parametro `capability_cutoff`: {cutoff_text(cfg)}\n"
              f"- Marcadores `<<...>>` se sustituyen por corrida. No se declara umbral de tiempo (001 3.3 [NO VERIFICADO]).\n\n"
              f"~~~text\n{p.raw}\n~~~\n")
    if out.exists() and f"`{p.sha256}`" not in out.read_text(encoding="utf-8"):
        raise RuntimeError(f"{out} existe con otro contenido: un cambio de prompt exige nueva prompt_version")
    if not out.exists():
        out.write_text(cuerpo, encoding="utf-8")
    return out
