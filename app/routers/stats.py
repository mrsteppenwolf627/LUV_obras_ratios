"""Router for statistics endpoints (rango, distribuciones, etc)."""

from typing import Optional
from fastapi import APIRouter, HTTPException
from sqlalchemy import func
from pydantic import BaseModel

from app import database as _db
from src.db.schema import ItemInstance, ItemMaster

router = APIRouter(prefix="/api", tags=["stats"])


class RangoResponse(BaseModel):
    chapter: str
    items_count: int
    muestras_total: int
    min_unitario: float
    max_unitario: float
    p25_unitario: float
    median_unitario: float
    p75_unitario: float
    avg_unitario: float


@router.get("/ratios/rango", response_model=RangoResponse)
def get_ratios_rango(chapter: Optional[str] = None):
    """
    Devuelve estadísticas de precios unitarios para una categoría/capítulo.

    Parámetros:
    - chapter: Nombre de categoría (ESTRUCTURA, FONTANERIA, etc)

    Retorna:
    - min, max, p25, mediana, p75, promedio de precio_unitario
    - count de items y total de muestras
    """
    if not chapter:
        raise HTTPException(status_code=400, detail="Parámetro 'chapter' requerido")

    session = _db.get_db()
    try:
        chapter_upper = chapter.upper()

        # Obtener todos los ItemInstance de esta categoría
        instances = (
            session.query(ItemInstance)
            .join(ItemMaster, ItemInstance.item_master_id == ItemMaster.id)
            .filter(ItemMaster.categoria == chapter_upper)
            .all()
        )

        if not instances:
            raise HTTPException(status_code=404, detail=f"Sin datos para capítulo: {chapter}")

        # Extraer precios unitarios
        precios = sorted([inst.precio_unitario for inst in instances if inst.precio_unitario])

        if not precios:
            raise HTTPException(status_code=404, detail=f"Sin precios válidos para: {chapter}")

        # Calcular estadísticas
        n = len(precios)
        min_p = min(precios)
        max_p = max(precios)
        avg_p = sum(precios) / n

        # Percentiles
        def percentil(data, p):
            """Calcula percentil con interpolación lineal."""
            if len(data) == 1:
                return data[0]
            h = (len(data) - 1) * p / 100.0
            h_int = int(h)
            h_frac = h - h_int
            if h_int + 1 >= len(data):
                return data[-1]
            return data[h_int] * (1 - h_frac) + data[h_int + 1] * h_frac

        p25 = percentil(precios, 25)
        p50 = percentil(precios, 50)  # mediana
        p75 = percentil(precios, 75)

        # Contar items únicos y total de muestras
        items_count = len(set(inst.item_master_id for inst in instances))
        muestras_total = len(instances)

        return RangoResponse(
            chapter=chapter_upper,
            items_count=items_count,
            muestras_total=muestras_total,
            min_unitario=round(min_p, 2),
            max_unitario=round(max_p, 2),
            p25_unitario=round(p25, 2),
            median_unitario=round(p50, 2),
            p75_unitario=round(p75, 2),
            avg_unitario=round(avg_p, 2),
        )

    finally:
        session.close()
