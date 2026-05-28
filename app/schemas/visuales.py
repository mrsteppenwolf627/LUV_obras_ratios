"""Pydantic schemas for visualization endpoints (FASE 2)."""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class CapituloRatioResponse(BaseModel):
    capitulo: str
    descripcion: Optional[str]
    minimo: Optional[float]
    percentil_25: Optional[float] = None
    mediana: Optional[float]
    percentil_75: Optional[float] = None
    maximo: Optional[float]
    desviacion_std: Optional[float] = None
    cantidad_datos: int
    estado_confiabilidad: Literal["muy_solido", "solido", "debil", "muy_debil"]
    building_type: Optional[str] = None


class ItemPresupuesto(BaseModel):
    capitulo: str = Field(..., description="Código de capítulo")
    valor_unitario: float = Field(..., gt=0, description="Precio unitario (€/m2)")
    cantidad: int = Field(default=1, ge=1, description="Cantidad")
    unidad: str = Field(default="m2", description="Unidad")


class PresupuestoAnalisis(BaseModel):
    items: List[ItemPresupuesto] = Field(..., min_length=1)
    area_total: float = Field(..., gt=0, description="Área total en m2")
    building_type: Optional[str] = None


class ComparativaCapitulo(BaseModel):
    capitulo: str
    descripcion: Optional[str]
    valor_mio: float = Field(..., description="Valor usuario (€/m2)")
    valor_ratio: float = Field(..., description="Mediana histórica (€/m2)")
    desviacion_pct: float = Field(..., description="Desviación en %")
    impacto_monetario: float = Field(..., description="Impacto total en €")
    estado_confiabilidad: Literal["muy_solido", "solido", "debil", "muy_debil"]
    ratio_encontrado: bool = True


class ResumenComparativa(BaseModel):
    total_presupuesto: float
    total_ratio: float
    diferencia_pct: float
    diferencia_monetaria: float
    area_total: float
    confiabilidad_global: Literal["muy_solido", "solido", "debil", "muy_debil"]


class ComparativaResponse(BaseModel):
    capitulos: List[ComparativaCapitulo]
    capitulos_sin_ratio: List[str] = Field(default_factory=list)
    resumen: ResumenComparativa
