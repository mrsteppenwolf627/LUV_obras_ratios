"""Utilities for gama (material tier) determination and lookup."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from src.db.schema import GamaRange


def determine_gama(unitario_mediana: Optional[float], gama_row: Optional[GamaRange]) -> str:
    """
    Determine the gama tier (MEDIUM, PREMIUM, LUXURY, LUXURY_PLUS) based on unit price.

    Args:
        unitario_mediana: Median unit price (EUR/m²)
        gama_row: GamaRange record with tier boundaries

    Returns:
        'MEDIUM' | 'PREMIUM' | 'LUXURY' | 'LUXURY_PLUS' | 'SIN_CLASIFICAR'
    """
    if unitario_mediana is None or gama_row is None:
        return "SIN_CLASIFICAR"

    price = unitario_mediana

    # Check luxury_plus first (highest tier)
    if gama_row.luxury_plus_min is not None and gama_row.luxury_plus_max is not None:
        if gama_row.luxury_plus_min <= price <= gama_row.luxury_plus_max:
            return "LUXURY_PLUS"

    # Check luxury
    if gama_row.luxury_min is not None and gama_row.luxury_max is not None:
        if gama_row.luxury_min <= price <= gama_row.luxury_max:
            return "LUXURY"

    # Check premium
    if gama_row.premium_min is not None and gama_row.premium_max is not None:
        if gama_row.premium_min <= price <= gama_row.premium_max:
            return "PREMIUM"

    # Check medium
    if gama_row.medium_min is not None and gama_row.medium_max is not None:
        if gama_row.medium_min <= price <= gama_row.medium_max:
            return "MEDIUM"

    return "SIN_CLASIFICAR"


def find_gama_range(
    session: Session, categoria_item: Optional[str]
) -> Optional[GamaRange]:
    """
    Find a GamaRange record matching the given category.

    Args:
        session: SQLAlchemy session
        categoria_item: Item category (e.g., 'ACABADOS', 'CARPINTERIA')

    Returns:
        GamaRange object or None if not found
    """
    if not categoria_item:
        return None

    return (
        session.query(GamaRange)
        .filter(GamaRange.categoria == categoria_item.upper())
        .first()
    )
