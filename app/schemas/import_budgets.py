"""Pydantic schemas for POST /api/import/budgets."""

from __future__ import annotations

import math
import re
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator


class LineaPresupuesto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    numero: int = 0
    capitulo: str = ""
    descripcion: str
    cantidad: Optional[float] = None
    unidad: str = "ud"
    precio_unitario: float

    @field_validator("descripcion")
    @classmethod
    def descripcion_length(cls, v: str) -> str:
        if len(v) > 500:
            raise ValueError("descripcion máximo 500 caracteres")
        return v

    @field_validator("unidad")
    @classmethod
    def unidad_length(cls, v: str) -> str:
        if len(v) > 50:
            raise ValueError("unidad máximo 50 caracteres")
        return v

    @field_validator("capitulo")
    @classmethod
    def capitulo_length(cls, v: str) -> str:
        if len(v) > 100:
            raise ValueError("capitulo máximo 100 caracteres")
        return v

    @field_validator("cantidad")
    @classmethod
    def cantidad_bounds(cls, v: Optional[float]) -> Optional[float]:
        if v is None:
            return v
        if math.isnan(v) or math.isinf(v):
            raise ValueError("cantidad debe ser un número finito (no NaN ni Infinity)")
        # Negative/zero quantities are rejected by business logic in import_service
        # but we allow them through validation to provide clear error messages at import time
        if v > 1_000_000:
            raise ValueError("cantidad máximo 1.000.000")
        return v

    @field_validator("precio_unitario")
    @classmethod
    def precio_unitario_finite(cls, v: float) -> float:
        if math.isnan(v) or math.isinf(v):
            raise ValueError("precio_unitario debe ser un número finito (no NaN ni Infinity)")
        if v < 0:
            raise ValueError("precio_unitario no puede ser negativo")
        if v > 1_000_000:
            raise ValueError("precio_unitario máximo 1.000.000")
        return v


class BudgetImportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filename: str = "presupuesto_sin_nombre.json"
    file_hash: str
    building_type: str = "residencial"
    lineas: List[LineaPresupuesto]

    @field_validator("filename")
    @classmethod
    def filename_length(cls, v: str) -> str:
        if len(v) > 500:
            raise ValueError("filename máximo 500 caracteres")
        return v

    @field_validator("building_type")
    @classmethod
    def building_type_length(cls, v: str) -> str:
        if len(v) > 100:
            raise ValueError("building_type máximo 100 caracteres")
        return v

    @field_validator("file_hash")
    @classmethod
    def hash_no_vacio(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^[a-f0-9]{64}$", v):
            raise ValueError("file_hash debe ser SHA256 hex (exactamente 64 caracteres [a-f0-9])")
        return v

    @field_validator("lineas")
    @classmethod
    def lineas_validacion(cls, v: List[LineaPresupuesto]) -> List[LineaPresupuesto]:
        if not v:
            raise ValueError("lineas no puede estar vacío")
        max_lineas = 10_000
        if len(v) > max_lineas:
            raise ValueError(f"Máximo {max_lineas:,} líneas permitidas. Recibidas: {len(v):,}")
        return v


class BudgetImportResponse(BaseModel):
    import_id: str
    items_creados: int
    items_duplicados: int
    muestras_actualizadas: int
    detalles: List[str]
    status: str  # success | partial | error
