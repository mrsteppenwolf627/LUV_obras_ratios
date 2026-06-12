"""Pydantic schemas for GET /api/items/with_gamas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ItemMasterWithGama(BaseModel):
    """ItemMaster with computed gama_asignada tier."""

    id: int
    item_key: str
    categoria: Optional[str] = None
    subcategoria: Optional[str] = None
    unidad: Optional[str] = None

    mediana_unitario: Optional[float] = None
    media_unitario: Optional[float] = None
    min_unitario: Optional[float] = None
    max_unitario: Optional[float] = None
    desv_std: Optional[float] = None
    muestras_count: int = Field(default=0)

    gama_asignada: str = Field(
        ..., description="Computed gama tier: MEDIUM|PREMIUM|LUXURY|LUXURY_PLUS|SIN_CLASIFICAR"
    )

    model_config = ConfigDict(from_attributes=True)


class ItemsWithGamasResponse(BaseModel):
    """Response for GET /api/items/with_gamas."""

    items: list[ItemMasterWithGama]
    total_count: int

    model_config = ConfigDict(from_attributes=True)
