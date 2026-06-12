"""Router for GET /api/items/with_gamas (items + computed gama assignment)."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Query

from app import database as _db
from app.schemas.items_extended import ItemMasterWithGama, ItemsWithGamasResponse
from app.utils.gama_utils import determine_gama, find_gama_range
from src.db.schema import ItemMaster

router = APIRouter(prefix="/api", tags=["items"])
logger = logging.getLogger(__name__)


@router.get("/items/with_gamas", response_model=ItemsWithGamasResponse)
def get_items_with_gamas(
    q: Optional[str] = Query(None, min_length=1, max_length=200),
    categoria: Optional[str] = Query(None, min_length=1, max_length=100),
    limit: int = Query(100, ge=1, le=1000),
) -> ItemsWithGamasResponse:
    """
    Get all items with computed gama tier assignment.

    Query Parameters:
    - q: Filter by item_key (substring match, case-insensitive)
    - categoria: Filter by item categoria (exact match, case-insensitive)
    - limit: Max items to return (default 100, max 1000)

    Returns:
    - items: List of ItemMaster with gama_asignada computed on-the-fly
    - total_count: Number of items in result
    """
    session = _db.get_db()
    try:
        # Build query
        query = session.query(ItemMaster)

        if q:
            query = query.filter(ItemMaster.item_key.ilike(f"%{q.lower()}%"))

        if categoria:
            query = query.filter(ItemMaster.categoria == categoria.upper())

        # Order by sample count (confidence) descending
        masters = query.order_by(ItemMaster.muestras_count.desc()).limit(limit).all()

        # Build response with computed gama
        items_with_gama: list[ItemMasterWithGama] = []

        for master in masters:
            # Find gama_range matching item categoria
            gama_row = find_gama_range(session, master.categoria)

            # Determine gama tier based on median price
            gama_asignada = determine_gama(master.mediana_unitario, gama_row)

            # Create response object
            item_with_gama = ItemMasterWithGama(
                id=master.id,
                item_key=master.item_key,
                categoria=master.categoria,
                subcategoria=master.subcategoria,
                unidad=master.unidad,
                mediana_unitario=master.mediana_unitario,
                media_unitario=master.media_unitario,
                min_unitario=master.min_unitario,
                max_unitario=master.max_unitario,
                desv_std=master.desv_std,
                muestras_count=master.muestras_count,
                gama_asignada=gama_asignada,
            )
            items_with_gama.append(item_with_gama)

        return ItemsWithGamasResponse(
            items=items_with_gama,
            total_count=len(items_with_gama),
        )
    finally:
        session.close()
