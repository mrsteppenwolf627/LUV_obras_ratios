"""Pydantic schemas for POST /api/import/budgets."""

from __future__ import annotations

import re
from typing import List, Optional

from pydantic import BaseModel, field_validator


class LineaPresupuesto(BaseModel):
    numero: int = 0
    capitulo: str = ""
    descripcion: str
    cantidad: Optional[float] = None
    unidad: str = "ud"
    precio_unitario: float


class BudgetImportRequest(BaseModel):
    filename: str = "presupuesto_sin_nombre.json"
    file_hash: str
    building_type: str = "residencial"
    lineas: List[LineaPresupuesto]

    @field_validator("file_hash")
    @classmethod
    def hash_no_vacio(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^[a-f0-9]{64}$", v):
            raise ValueError("file_hash debe ser SHA256 hex (exactamente 64 caracteres [a-f0-9])")
        return v

    @field_validator("lineas")
    @classmethod
    def lineas_no_vacias(cls, v: List[LineaPresupuesto]) -> List[LineaPresupuesto]:
        if not v:
            raise ValueError("lineas no puede estar vacío")
        return v


class BudgetImportResponse(BaseModel):
    import_id: str
    items_creados: int
    items_duplicados: int
    muestras_actualizadas: int
    detalles: List[str]
    status: str  # success | partial | error
