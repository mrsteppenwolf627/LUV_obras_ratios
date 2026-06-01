"""CRUD helpers for ItemMasterRatio — category-level ratios per item."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.services.clasificacion_service import calcular_confianza_basada_en_n
from src.db.schema import Categoria, ItemMasterRatio

# Sensible defaults used when the table has no data yet for a category.
_DEFAULT_MEDIANAS: Dict[str, float] = {
    Categoria.MEDIUM.value: 150.0,
    Categoria.PREMIUM.value: 300.0,
    Categoria.LUXURY.value: 500.0,
    Categoria.LUXURY_PLUS.value: 800.0,
}


def get_or_create_ratio(
    session: Session,
    item_master_id: int,
    categoria: str,
) -> ItemMasterRatio:
    """Return existing ratio row or create a new one with default values.

    The new row is added to the session but not committed — the caller decides.
    """
    ratio = (
        session.query(ItemMasterRatio)
        .filter(
            ItemMasterRatio.item_master_id == item_master_id,
            ItemMasterRatio.categoria == categoria,
        )
        .first()
    )

    if ratio is None:
        ratio = ItemMasterRatio(
            item_master_id=item_master_id,
            categoria=categoria,
            ratio_actual=None,
            muestras_count=0,
            confianza=Categoria.MEDIUM.value,  # placeholder; recalculated on first update
        )
        # Set confianza correctly for N=0
        ratio.confianza = calcular_confianza_basada_en_n(0)
        ratio.ultima_actualizacion = datetime.now(timezone.utc)
        session.add(ratio)
        session.flush()

    return ratio


def update_ratio_incremental(
    session: Session,
    item_master_id: int,
    categoria: str,
    nuevo_valor: float,
) -> ItemMasterRatio:
    """Incorporate a new price observation using a running average.

    Formula: new_avg = (old_avg × N + nuevo_valor) / (N + 1)
    """
    ratio = get_or_create_ratio(session, item_master_id, categoria)
    n = ratio.muestras_count

    if ratio.ratio_actual is None:
        ratio.ratio_actual = nuevo_valor
        ratio.mediana = nuevo_valor
        ratio.min_valor = nuevo_valor
        ratio.max_valor = nuevo_valor
    else:
        ratio.ratio_actual = (ratio.ratio_actual * n + nuevo_valor) / (n + 1)
        ratio.mediana = (
            (ratio.mediana * n + nuevo_valor) / (n + 1)
            if ratio.mediana is not None
            else nuevo_valor
        )
        ratio.min_valor = (
            min(ratio.min_valor, nuevo_valor)
            if ratio.min_valor is not None
            else nuevo_valor
        )
        ratio.max_valor = (
            max(ratio.max_valor, nuevo_valor)
            if ratio.max_valor is not None
            else nuevo_valor
        )

    ratio.muestras_count = n + 1
    ratio.confianza = calcular_confianza_basada_en_n(ratio.muestras_count)
    ratio.ultima_actualizacion = datetime.now(timezone.utc)

    return ratio


def get_ratio_by_categoria(
    session: Session,
    item_master_id: int,
    categoria: str,
) -> Optional[ItemMasterRatio]:
    """Return the ratio for a specific item × category, or None."""
    return (
        session.query(ItemMasterRatio)
        .filter(
            ItemMasterRatio.item_master_id == item_master_id,
            ItemMasterRatio.categoria == categoria,
        )
        .first()
    )


def get_ratios_por_item(
    session: Session,
    item_master_id: int,
) -> List[ItemMasterRatio]:
    """Return all category ratios for an item."""
    return (
        session.query(ItemMasterRatio)
        .filter(ItemMasterRatio.item_master_id == item_master_id)
        .order_by(ItemMasterRatio.categoria)
        .all()
    )


def get_median_prices_por_categoria(session: Session) -> Dict[str, float]:
    """Return average mediana per category, falling back to defaults for missing ones.

    Returns:
        {"MEDIUM": 150.0, "PREMIUM": 300.0, "LUXURY": 500.0, "LUXURY_PLUS": 800.0}
    """
    rows = (
        session.query(
            ItemMasterRatio.categoria,
            func.avg(ItemMasterRatio.mediana),
        )
        .filter(ItemMasterRatio.mediana.isnot(None))
        .group_by(ItemMasterRatio.categoria)
        .all()
    )

    result = dict(_DEFAULT_MEDIANAS)
    for cat, avg_median in rows:
        if avg_median is not None and cat in result:
            result[cat] = round(float(avg_median), 2)

    return result
