"""Extract individual items from parsed budgets (Presto, BC3, Excel).

Input: output of parse_presto(), read_bc3(), or read_excel()
Output: list of normalized item dicts ready for classification and DB insertion.
"""

from __future__ import annotations

import re
from typing import Optional


def extract_items_from_budget(
    budget_data: dict,
    budget_id: Optional[int] = None,
) -> list[dict]:
    """
    Extract individual items from a parsed budget.

    Handles three formats:
    - presto: espacios[].partidas[]
    - bc3 / excel: chapters[]

    Returns list of normalized item dicts:
    {
        "codigo": str,
        "descripcion": str,
        "categoria_original": str,
        "cantidad": float | None,
        "unidad": str,
        "precio_unitario": float | None,
        "precio_total": float | None,
        "presupuesto_id": int | None,
        "validation_status": "VALID" | "DUBIOUS",
        "dubious_reasons": list[str],
    }
    """
    fmt = budget_data.get("source_format", "")

    if fmt == "presto" or "espacios" in budget_data:
        return _extract_from_presto(budget_data, budget_id)
    if fmt in ("bc3", "excel") or "chapters" in budget_data:
        return _extract_from_chapters(budget_data, budget_id)
    return []


def make_item_key(descripcion: str, unidad: str) -> str:
    """Stable dedup key: normalized description + unit."""
    norm = re.sub(r"[^a-z0-9 ]", "", (descripcion or "").lower().strip())
    norm = re.sub(r"\s+", " ", norm).strip()
    unit = (unidad or "").lower().strip()
    return f"{norm}|{unit}"


# ---------------------------------------------------------------------------
# Format-specific extractors
# ---------------------------------------------------------------------------

def _extract_from_presto(budget_data: dict, budget_id: Optional[int]) -> list[dict]:
    items = []
    for espacio in budget_data.get("espacios", []):
        cat_original = espacio.get("nombre", "")
        for partida in espacio.get("partidas", []):
            items.append(
                _normalize_item(
                    codigo=partida.get("codigo", ""),
                    descripcion=partida.get("descripcion", ""),
                    categoria_original=cat_original,
                    cantidad=partida.get("cantidad"),
                    unidad=partida.get("unidad", ""),
                    precio_unitario=partida.get("unitario"),
                    precio_total=partida.get("coste"),
                    presupuesto_id=budget_id,
                )
            )
    return items


def _extract_from_chapters(budget_data: dict, budget_id: Optional[int]) -> list[dict]:
    items = []
    for ch in budget_data.get("chapters", []):
        items.append(
            _normalize_item(
                codigo=ch.get("chapter_code", ""),
                descripcion=ch.get("chapter_name") or ch.get("description", ""),
                categoria_original=ch.get("chapter_code", ""),
                cantidad=ch.get("quantity"),
                unidad=ch.get("unit", ""),
                precio_unitario=ch.get("unit_cost"),
                precio_total=ch.get("total_cost"),
                presupuesto_id=budget_id,
            )
        )
    return items


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

def _normalize_item(
    codigo: str,
    descripcion: str,
    categoria_original: str,
    cantidad,
    unidad: str,
    precio_unitario,
    precio_total,
    presupuesto_id: Optional[int],
) -> dict:
    dubious_reasons: list[str] = []

    # Coerce cantidad
    try:
        cantidad = float(cantidad) if cantidad is not None else None
    except (TypeError, ValueError):
        cantidad = None
        dubious_reasons.append("cantidad no numérica")

    # Coerce precio_total
    try:
        precio_total = float(precio_total) if precio_total is not None else None
    except (TypeError, ValueError):
        precio_total = None
        dubious_reasons.append("precio_total no numérico")

    # Coerce precio_unitario; derive from total/cantidad if missing
    try:
        precio_unitario = float(precio_unitario) if precio_unitario is not None else None
    except (TypeError, ValueError):
        precio_unitario = None

    if precio_unitario is None and precio_total is not None and cantidad and cantidad > 0:
        precio_unitario = round(precio_total / cantidad, 6)

    # Validation flags
    if precio_total is None or precio_total == 0:
        dubious_reasons.append("precio_total ausente o cero")
    if not str(descripcion).strip():
        dubious_reasons.append("descripción vacía")
    if precio_unitario is not None and precio_unitario < 0:
        dubious_reasons.append("precio_unitario negativo")

    return {
        "codigo": str(codigo) if codigo else "",
        "descripcion": str(descripcion).strip() if descripcion else "",
        "categoria_original": str(categoria_original) if categoria_original else "",
        "cantidad": cantidad,
        "unidad": str(unidad).strip() if unidad else "",
        "precio_unitario": precio_unitario,
        "precio_total": precio_total,
        "presupuesto_id": presupuesto_id,
        "validation_status": "DUBIOUS" if dubious_reasons else "VALID",
        "dubious_reasons": dubious_reasons,
    }
