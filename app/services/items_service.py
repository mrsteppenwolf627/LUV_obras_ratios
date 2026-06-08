"""Servicio centralizado para deduplicación y normalización de items."""

from __future__ import annotations

import re
import unicodedata
from typing import Optional

from sqlalchemy.orm import Session


def normalize_item_key(descripcion: str) -> str:
    """
    Normaliza descripción de partida a item_key determinístico y único.

    Reglas:
    - Lowercase
    - Elimina acentos/diacríticos (NFKD + filter Mn)
    - Elimina caracteres especiales excepto guiones (-) y guiones bajos (_)
    - Colapsa espacios múltiples a uno
    - Strip inicial/final
    - Máximo 500 caracteres
    - Idempotente: normalize(normalize(x)) == normalize(x)

    "Carpintería Aluminio Doble" → "carpinteria aluminio doble"
    """
    if not descripcion or not isinstance(descripcion, str):
        return ""

    text = descripcion.lower()

    text = "".join(
        c
        for c in unicodedata.normalize("NFKD", text)
        if unicodedata.category(c) != "Mn"
    )

    # Replace disallowed chars with a space so adjacent words don't merge
    text = re.sub(r"[^a-z0-9\s\-_]", " ", text)

    text = re.sub(r"\s+", " ", text)

    text = text.strip()

    return text[:500]


def get_or_create_item_master(
    session: Session,
    item_key: str,
    categoria: Optional[str] = None,
    subcategoria: Optional[str] = None,
    unidad: Optional[str] = None,
) -> "ItemMaster":  # type: ignore[name-defined]  # noqa: F821
    """
    Obtiene o crea un ItemMaster con la clave normalizada.

    Si el item ya existe, retorna el existente.
    Si no existe, crea uno nuevo con los parámetros proporcionados.

    Args:
        session: SQLAlchemy session
        item_key: Clave normalizada (debe ser resultado de normalize_item_key)
        categoria: Categoría del item (ej. "residencial")
        subcategoria: Subcategoría opcional
        unidad: Unidad de medida (default: "ud")

    Returns:
        ItemMaster: El item existente o recién creado
    """
    from src.db.schema import ItemMaster

    master = session.query(ItemMaster).filter(ItemMaster.item_key == item_key).first()
    if master is None:
        master = ItemMaster(
            item_key=item_key,
            categoria=categoria,
            subcategoria=subcategoria,
            unidad=unidad or "ud",
            muestras_count=0,
        )
        session.add(master)
        session.flush()
    return master
