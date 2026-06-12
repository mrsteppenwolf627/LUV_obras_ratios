"""Router for GET /api/items/with_gamas (items + computed gama assignment)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError

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
    - items: List of ItemMaster with gama_asignada (always present, never null)
    - total_count: Number of items in result

    Raises:
    - 500 Internal Server Error: Database error or unexpected processing error
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
        failed_items: list[tuple[int, str, str]] = []

        for master in masters:
            try:
                # Find gama_range matching item categoria
                gama_row = find_gama_range(session, master.categoria)

                # Determine gama tier based on median price
                gama_asignada = determine_gama(master.mediana_unitario, gama_row)

                # Ensure gama_asignada is never None/empty
                if not gama_asignada:
                    gama_asignada = "SIN_CLASIFICAR"

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

            except Exception as item_error:
                error_msg = f"{type(item_error).__name__}: {str(item_error)}"
                logger.warning(
                    f"Failed to process item {master.id} ({master.item_key}): {error_msg}",
                    exc_info=True,
                )
                failed_items.append((master.id, master.item_key, error_msg))
                # Fall back to SIN_CLASIFICAR for this item
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
                    gama_asignada="SIN_CLASIFICAR",
                )
                items_with_gama.append(item_with_gama)

        if failed_items:
            logger.warning(
                f"Processed {len(masters)} items with {len(failed_items)} fallbacks to SIN_CLASIFICAR"
            )

        return ItemsWithGamasResponse(
            items=items_with_gama,
            total_count=len(items_with_gama),
        )

    except SQLAlchemyError as db_error:
        error_msg = f"Database error: {str(db_error)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "database_error",
                "message": "Failed to query items from database",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    except Exception as global_error:
        error_msg = f"{type(global_error).__name__}: {str(global_error)}"
        logger.error(f"Unexpected error in get_items_with_gamas: {error_msg}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_server_error",
                "message": "An unexpected error occurred while processing items",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    finally:
        session.close()
