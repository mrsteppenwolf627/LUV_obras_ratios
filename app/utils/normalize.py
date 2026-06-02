"""Normalization utilities for item keys."""

from __future__ import annotations

import re
import unicodedata


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
