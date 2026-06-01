"""Keyword-based item classification for LUV Studio gama categories."""

from __future__ import annotations

from typing import List, Optional, Tuple

from src.db.schema import Categoria

# Rules checked in priority order — first match wins.
# Each entry: (list_of_substrings, Categoria)
_KEYWORD_RULES: List[Tuple[List[str], Categoria]] = [
    (
        [
            "motorizado", "motorizada", "domótica", "domotica", "domótico", "domotico",
            "mármol", "marmol", "travertino", "piedra natural", "madera tropical",
            "bulthaup", "siematic", "poggenpohl",
        ],
        Categoria.LUXURY_PLUS,
    ),
    (
        [
            "madera maciza", "maciza", "gran formato",
            "porcelánico", "porcelanico",
            "lacado brillo", "revestimiento pétreo", "revestimiento petreo",
            "cocina diseño", "cocina diseno",
        ],
        Categoria.LUXURY,
    ),
    (
        [
            "doble acristalamiento", "aluminio lacado", "aluminio rpt",
            "parquet", "roble", "tarima flotante",
            "carpintería aluminio", "carpinteria aluminio",
            "acabado premium",
        ],
        Categoria.PREMIUM,
    ),
    (
        [
            "básico", "basico", "económico", "economico", "económica", "economica",
            "funcional", "estándar", "estandar", "standard",
            "pintura plástica", "pintura plastica",
            "azulejo", "baldosa cerámica", "baldosa ceramica",
            "pvc",
        ],
        Categoria.MEDIUM,
    ),
]


def clasificar_item(descripcion: str) -> Optional[Categoria]:
    """Return Categoria if a keyword matches, else None.

    Matching is case-insensitive substring search. Highest-priority tier wins.
    """
    if not descripcion or not descripcion.strip():
        return None

    desc_lower = descripcion.lower()
    for keywords, categoria in _KEYWORD_RULES:
        if any(kw in desc_lower for kw in keywords):
            return categoria

    return None
