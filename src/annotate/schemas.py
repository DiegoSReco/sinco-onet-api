"""Esquemas del registro de anotacion (decision 001 sec. 7; rubrica v1).

El anotador solo emite clases (E0/E1/E2); no hay puntaje continuo. El mapa numerico
E0/E1/E2 -> 0/0.5/1 vive en config.toml y NO se aplica aqui.
"""
from __future__ import annotations

import datetime as dt
from typing import Literal, Optional

import pyarrow as pa
import pyarrow.parquet as pq
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from typing_extensions import Annotated

ExposureClass = Literal["E0", "E1", "E2"]
Confidence = Literal["alta", "media", "baja"]
TaskType = Literal["core", "supplemental"]
Texto = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
RunId = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_.-]+$", min_length=1, max_length=80)]
OnetSoc = Annotated[str, StringConstraints(pattern=r"^\d{2}-\d{4}\.\d{2}$")]
RATIONALE_MAX = 600


class ModelOutput(BaseModel):
    """Lo unico que debe devolver el modelo (JSON estricto). Sin campos extra, sin puntajes."""
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    exposure_class: ExposureClass
    physical_bottleneck: bool
    confidence: Confidence
    rationale: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=RATIONALE_MAX)]


class Annotation(BaseModel):
    """Un registro por (run_id, task_id)."""
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    run_id: RunId
    prompt_version: Texto
    prompt_sha256: Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
    model: Texto
    run_date: dt.date
    onet_version: Texto
    onet_soc: OnetSoc
    task_id: Texto
    task_text_en: Texto
    task_text_es: Optional[Texto] = None          # nulo mientras no exista traduccion
    translation_version: Optional[Texto] = None
    annotated_text_lang: Literal["en", "es"]       # que texto vio el modelo
    task_type: Optional[TaskType] = None           # nulo = O*NET no lo informa (ver issue)
    exposure_class: ExposureClass
    physical_bottleneck: bool
    confidence: Confidence
    rationale: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=RATIONALE_MAX)]
    capability_cutoff: Optional[Texto] = None      # 001 P3: requiere decision
    temperature: Optional[float] = Field(default=None, ge=0, le=2)   # nulo si no es controlable
    temperature_note: Optional[Texto] = None                          # p. ej. 'solicitada 1.0, no controlable...'
    seed: Optional[int] = None

    @model_validator(mode="after")
    def _coherencia(self):
        if self.annotated_text_lang == "es" and not self.task_text_es:
            raise ValueError("annotated_text_lang='es' exige task_text_es")
        return self


def validar_unicidad(records: list[Annotation]) -> None:
    vistos = set()
    for r in records:
        k = (r.run_id, r.task_id)
        if k in vistos:
            raise ValueError(f"registro duplicado para (run_id, task_id) = {k}")
        vistos.add(k)


ARROW_SCHEMA = pa.schema([
    ("run_id", pa.string()), ("prompt_version", pa.string()), ("prompt_sha256", pa.string()),
    ("model", pa.string()), ("run_date", pa.date32()), ("onet_version", pa.string()),
    ("onet_soc", pa.string()), ("task_id", pa.string()), ("task_text_en", pa.string()),
    ("task_text_es", pa.string()), ("translation_version", pa.string()),
    ("annotated_text_lang", pa.string()), ("task_type", pa.string()),
    ("exposure_class", pa.string()), ("physical_bottleneck", pa.bool_()),
    ("confidence", pa.string()), ("rationale", pa.string()),
    ("capability_cutoff", pa.string()), ("temperature", pa.float64()), ("temperature_note", pa.string()),
    ("seed", pa.int64()),
])


def write_parquet(records: list[Annotation], path, overwrite: bool = False) -> None:
    from pathlib import Path
    path = Path(path)
    validar_unicidad(records)
    if path.exists() and not overwrite:
        raise FileExistsError(f"{path} ya existe; una corrida no se sobrescribe")
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = {n: [getattr(r, n) for r in records] for n in ARROW_SCHEMA.names}
    pq.write_table(pa.table(cols, schema=ARROW_SCHEMA), path)


def read_parquet(path) -> list[Annotation]:
    """Lee y revalida cada fila contra Annotation (falla si el archivo no cumple el esquema)."""
    t = pq.read_table(path)
    if t.schema.names != ARROW_SCHEMA.names:
        raise ValueError(f"columnas distintas del esquema: {t.schema.names}")
    recs = [Annotation(**row) for row in t.to_pylist()]
    validar_unicidad(recs)
    return recs
