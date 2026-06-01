"""Classification service: category assignment and confidence calculation."""

from __future__ import annotations

from typing import Dict, Optional

from app.utils.keywords_mapping import clasificar_item
from src.db.schema import Categoria, Confianza


def clasificar_item_desde_descripcion(
    descripcion: str,
    precio_unitario: Optional[float] = None,
    ratios_historicos: Optional[Dict[str, float]] = None,
) -> Categoria:
    """Classify item into a LUV gama category.

    Priority:
    1. Keyword match on descripcion.
    2. Price proximity to historical medians (if precio_unitario is provided).
    3. Default: MEDIUM.
    """
    if not descripcion or not descripcion.strip():
        return Categoria.MEDIUM

    match = clasificar_item(descripcion)
    if match is not None:
        return match

    if precio_unitario is not None and ratios_historicos:
        return determinar_categoria_por_precio(precio_unitario, ratios_historicos)

    return Categoria.MEDIUM


def determinar_categoria_por_precio(
    precio_unitario: float,
    ratios_historicos: Dict[str, float],
) -> Categoria:
    """Return the Categoria whose historical median is closest to precio_unitario."""
    valid_cats = {
        cat: price
        for cat, price in ratios_historicos.items()
        if cat in {c.value for c in Categoria}
    }

    if not valid_cats:
        return Categoria.MEDIUM

    closest = min(valid_cats, key=lambda cat: abs(precio_unitario - valid_cats[cat]))
    return Categoria(closest)


def calcular_confianza_basada_en_n(muestras_count: int) -> Confianza:
    """Map a sample count to a Confianza level.

    N < 2   → MUY_DÉBIL
    2–4     → DÉBIL
    5–9     → SÓLIDO
    ≥ 10    → MUY_SÓLIDO
    """
    n = max(int(muestras_count or 0), 0)
    if n >= 10:
        return Confianza.MUY_SOLIDO
    if n >= 5:
        return Confianza.SOLIDO
    if n >= 2:
        return Confianza.DEBIL
    return Confianza.MUY_DEBIL
