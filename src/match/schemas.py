"""Esquemas (pyarrow + pydantic) de las salidas de src/match/ y verificaciones de integridad.

Regla 5 de CLAUDE.md: si una salida no cumple su esquema, se levanta SchemaError y no se escribe.
"""
from __future__ import annotations

import re
from typing import Literal, Optional

import pandas as pd
import pyarrow as pa
from pydantic import BaseModel, ConfigDict, Field

# Misma lista negra que la API (src/api/service.py): el crosswalk NO lleva scores/exposicion/probabilidad.
PROHIBIDAS_CROSSWALK = re.compile(r"(score|expos|prob|frey|osborne|automat)", re.I)
# Ninguna tabla de este modulo puede llamar "exposicion" a nada.
PROHIBIDAS_TODAS = re.compile(r"(expos|riesgo)", re.I)


class SchemaError(ValueError):
    pass


class CrosswalkFila(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sinco_code: str = Field(pattern=r"^[1-9][0-9]{0,3}$")
    onet_soc_code: str = Field(pattern=r"^[0-9]{2}-[0-9]{4}\.[0-9]{2}$")
    tipo_relacion: Literal["1:1", "1:N", "N:1", "M:N"]
    fuente: str = Field(min_length=1)
    estado_validacion: Literal["sin_validar", "revision_manual_1_revisor"]
    notas: Optional[str] = None
    run_id: str
    modelo: str
    rango: Optional[int] = Field(default=None, ge=1)   # NA solo en pares manuales fuera del top-2 automatico
    similitud: Optional[float] = None                  # NA solo en pares manuales fuera de los candidatos guardados
    margen: float
    similitud_alt: Optional[float] = None
    rango_alt: Optional[int] = None
    modelo_alt: Optional[str] = None
    baja_confianza: bool
    match_status: Literal["ok", "baja_confianza", "sin_coincidencia"]


CROSSWALK_ARROW = pa.schema([
    ("sinco_code", pa.string()), ("onet_soc_code", pa.string()), ("tipo_relacion", pa.string()),
    ("fuente", pa.string()), ("estado_validacion", pa.string()), ("notas", pa.string()), ("run_id", pa.string()),
    ("modelo", pa.string()), ("rango", pa.int32()), ("similitud", pa.float64()), ("margen", pa.float64()),
    ("similitud_alt", pa.float64()), ("rango_alt", pa.int32()), ("modelo_alt", pa.string()),
    ("baja_confianza", pa.bool_()), ("match_status", pa.string()),
])

PFO_COL = "probabilidad_automatizacion_fo"


class PFoFila(BaseModel):
    model_config = ConfigDict(extra="forbid")
    run_id: str
    modelo: str
    es_modelo_principal: bool
    sinco_code: str = Field(pattern=r"^[1-9][0-9]{3}$")
    titulo: str
    probabilidad_automatizacion_fo: Optional[float] = Field(default=None, ge=0, le=1)
    probabilidad_automatizacion_fo_media_uniforme: Optional[float] = Field(default=None, ge=0, le=1)
    probabilidad_automatizacion_fo_min: Optional[float] = Field(default=None, ge=0, le=1)
    probabilidad_automatizacion_fo_max: Optional[float] = Field(default=None, ge=0, le=1)
    probabilidad_automatizacion_fo_top1: Optional[float] = Field(default=None, ge=0, le=1)
    probabilidad_automatizacion_fo_ponderada_sin_filtro: Optional[float] = Field(default=None, ge=0, le=1)
    motivo_na: Optional[Literal["sin_coincidencia", "sin_probabilidad_fo", "sin_equivalente_onet_revision_manual"]] = None
    n_candidatos: int = Field(ge=0)   # 0 solo si la revision manual declara que no hay equivalente en O*NET
    n_soc2010: int = Field(ge=0)
    n_soc2010_con_fo: int = Field(ge=0)
    cobertura_peso_fo: float = Field(ge=0, le=1.0000001)
    cobertura_fo: Literal["completa", "parcial", "ninguna"]
    match_status: Literal["ok", "baja_confianza", "sin_coincidencia"]
    baja_confianza: bool
    sim_top1: float
    margen: float
    top1_onet_soc_code: str
    top1_socs: str
    n_sinco_mismo_top1_soc: int = Field(ge=1)
    bandera_multi_soc2010: bool
    bandera_sin_puente: bool
    onet_sin_puente: str
    bandera_soc_sin_fo: bool
    residual_sin_funciones: bool
    residual_por_titulo: bool
    estado_validacion: Literal["sin_validar", "revision_manual_1_revisor"]
    etiqueta: str


class CorridaFila(BaseModel):
    model_config = ConfigDict(extra="forbid")
    run_id: str
    modelo: str
    hf_id: str
    revision_modelo: str = Field(min_length=40, max_length=40)
    fecha: str
    metodo: str
    text_template_version: str
    seed: int
    normalizacion: str
    max_length: int
    n_truncados_sinco: int
    n_truncados_onet: int
    dispositivo: str
    dtype: str
    hash_matriz_sinco: str = Field(min_length=64, max_length=64)
    hash_matriz_onet: str = Field(min_length=64, max_length=64)
    hash_matriz_similitud: str = Field(min_length=64, max_length=64)
    hash_config: str = Field(min_length=64, max_length=64)
    parametros: str
    estado_parametros: str
    estado_validacion: Literal["sin_validar"]
    hashes_insumos: str
    versiones_librerias: str
    segundos_embedding: float
    vectores_desde_cache: bool
    n_sinco: int
    n_onet: int


def _a_tabla(df: pd.DataFrame, schema: pa.Schema) -> pa.Table:
    try:
        return pa.Table.from_pandas(df[[f.name for f in schema]], schema=schema, preserve_index=False)
    except Exception as e:  # pragma: no cover - mensaje informativo
        raise SchemaError(f"no cumple el esquema pyarrow: {e}") from e


def _filas(df: pd.DataFrame) -> list[dict]:
    out = []
    for r in df.to_dict("records"):
        d = {}
        for k, v in r.items():
            if v is None or (not isinstance(v, str) and pd.isna(v)):
                d[k] = None
            else:
                d[k] = v.item() if hasattr(v, "item") else v
        out.append(d)
    return out


def _validar_modelo(df: pd.DataFrame, modelo) -> None:
    for i, r in enumerate(_filas(df)):
        try:
            modelo(**r)
        except Exception as e:
            raise SchemaError(f"fila {i} no cumple {modelo.__name__}: {e}") from e


def validar_crosswalk(df: pd.DataFrame, sinco_codes: set[str], onet_codes: set[str]) -> pa.Table:
    malas = [c for c in df.columns if PROHIBIDAS_CROSSWALK.search(c)]
    if malas:
        raise SchemaError(f"crosswalk con columnas de score/exposicion/probabilidad: {malas}")
    _validar_modelo(df, CrosswalkFila)
    if not set(df["sinco_code"]) <= sinco_codes:
        raise SchemaError("crosswalk: sinco_code fuera de sinco.parquet")
    if not set(df["onet_soc_code"]) <= onet_codes:
        raise SchemaError("crosswalk: onet_soc_code fuera de onet_ocupaciones.parquet")
    if df.duplicated(["sinco_code", "onet_soc_code"]).any():
        raise SchemaError("crosswalk: pares duplicados")
    return _a_tabla(df, CROSSWALK_ARROW)


def validar_pfo(df: pd.DataFrame, sinco_codes: set[str]) -> None:
    malas = [c for c in df.columns if PROHIBIDAS_TODAS.search(c)]
    if malas:
        raise SchemaError(f"columnas con 'exposicion'/'riesgo': {malas}")
    _validar_modelo(df, PFoFila)
    if not set(df["sinco_code"]) <= sinco_codes:
        raise SchemaError("sinco_probabilidad_fo: sinco_code fuera de sinco.parquet")
    if df.duplicated(["modelo", "sinco_code"]).any():
        raise SchemaError("sinco_probabilidad_fo: duplicados (modelo, sinco_code)")


def validar_corridas(df: pd.DataFrame) -> None:
    _validar_modelo(df, CorridaFila)
