"""Pydantic schemas for visualization endpoints (FASE 2)."""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CapituloRatioResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

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


class ItemRatioResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_master_id: int
    item_key: str
    categoria: str
    muestras_total: int
    min_unitario: float
    p25_unitario: float
    median_unitario: float
    p75_unitario: float
    max_unitario: float
    avg_unitario: float


class ItemPresupuesto(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    capitulo: str = Field(..., description="Codigo de capitulo")
    valor_unitario: float = Field(..., gt=0, description="Precio unitario (EUR/m2)")
    cantidad: int = Field(default=1, ge=1, description="Cantidad")
    unidad: str = Field(default="m2", description="Unidad")

    @field_validator("capitulo", "unidad")
    @classmethod
    def validate_non_empty_string(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("no puede estar vacio")
        return normalized


class PresupuestoAnalisis(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    items: List[ItemPresupuesto] = Field(..., min_length=1)
    area_total: float = Field(..., gt=0, description="Area total en m2")
    building_type: Optional[str] = None

    @field_validator("building_type")
    @classmethod
    def normalize_building_type(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class ComparativaCapitulo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capitulo: str
    descripcion: Optional[str]
    valor_mio: float = Field(..., description="Valor usuario (EUR/m2)")
    valor_ratio: float = Field(..., description="Mediana historica (EUR/m2)")
    desviacion_pct: float = Field(..., description="Desviacion en %")
    impacto_monetario: float = Field(..., description="Impacto total en EUR")
    estado_confiabilidad: Literal["muy_solido", "solido", "debil", "muy_debil"]
    ratio_encontrado: bool = True


class ResumenComparativa(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_presupuesto: float
    total_ratio: float
    diferencia_pct: float
    diferencia_monetaria: float
    area_total: float
    confiabilidad_global: Literal["muy_solido", "solido", "debil", "muy_debil"]


class ComparativaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capitulos: List[ComparativaCapitulo]
    capitulos_sin_ratio: List[str] = Field(default_factory=list)
    resumen: ResumenComparativa
