"""Pydantic schemas for POST /api/items/analisis."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ItemParaAnalisis(BaseModel):
    descripcion: str = Field(..., min_length=3, max_length=500)
    precio_unitario: float = Field(..., gt=0)
    cantidad: float = Field(default=1.0, gt=0)
    unidad: str = Field(default="m2")

    @field_validator("descripcion", "unidad")
    @classmethod
    def validate_no_empty(cls, v: str) -> str:
        normalized = v.strip()
        if not normalized:
            raise ValueError("no puede estar vacío")
        return normalized


class PresupuestoParaAnalisis(BaseModel):
    items: List[ItemParaAnalisis] = Field(..., min_length=1)
    area_total: Optional[float] = Field(default=None, gt=0)
    building_type: Optional[str] = Field(default=None)

    model_config = ConfigDict(str_strip_whitespace=True)


class ItemAnalisisResultado(BaseModel):
    descripcion: str
    categoria: str
    precio_usuario: float
    ratio_historico: Optional[float] = None
    desviacion_pct: Optional[float] = None
    confianza: str
    impacto_monetario: Optional[float] = None
    ratio_encontrado: bool = True

    model_config = ConfigDict(extra="forbid")


class ResumenPorCategoria(BaseModel):
    categoria: str
    cantidad_items: int
    precio_total_usuario: float
    ratio_total_historico: float
    desviacion_pct_promedio: float
    confianza_global: str
    items_sin_ratio: int

    model_config = ConfigDict(extra="forbid")


class AnalisisItemsResponse(BaseModel):
    items: List[ItemAnalisisResultado]
    resumenes_por_categoria: Dict[str, ResumenPorCategoria]
    resumen_general: Dict[str, Any]
    ratios_updated: bool = False
    mode: str = "read_only"

    model_config = ConfigDict(extra="forbid")
