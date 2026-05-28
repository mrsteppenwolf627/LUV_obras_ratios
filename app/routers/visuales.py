"""Router for visualization endpoints (FASE 2)."""

from __future__ import annotations

import time
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from app import database as _db
from app.schemas.visuales import CapituloRatioResponse, ComparativaResponse, PresupuestoAnalisis
from app.services.comparativa_service import analizar_comparativa, obtener_capitulos_ratios

router = APIRouter(prefix="/api", tags=["visuales"])

# In-memory cache for GET /api/ratios/chapters (invalidated on each import)
_chapters_cache: dict = {"data": None, "timestamp": 0.0, "ttl": 3600.0}


def invalidar_cache_chapters() -> None:
    """Invalidate the chapters cache. Call this after recalculate_all_ratios."""
    _chapters_cache["data"] = None
    _chapters_cache["timestamp"] = 0.0


@router.get("/ratios/chapters", response_model=List[CapituloRatioResponse])
def get_ratios_chapters(building_type: Optional[str] = None):
    """
    List all chapters with consolidated statistics.

    Returns min / p25 / median / p75 / max / std_dev and confiabilidad badge.
    Response is cached for 1 hour and invalidated on every budget import.
    """
    now = time.time()
    cache_key = building_type or "__all__"

    if (
        _chapters_cache["data"] is not None
        and cache_key in _chapters_cache["data"]
        and (now - _chapters_cache["timestamp"]) < _chapters_cache["ttl"]
    ):
        return _chapters_cache["data"][cache_key]

    session = _db.get_db()
    try:
        resultado = obtener_capitulos_ratios(session, building_type)
    finally:
        session.close()

    if _chapters_cache["data"] is None:
        _chapters_cache["data"] = {}
    _chapters_cache["data"][cache_key] = resultado
    _chapters_cache["timestamp"] = now
    return resultado


@router.post("/analyze/comparativa", response_model=ComparativaResponse)
def analyze_comparativa(presupuesto: PresupuestoAnalisis):
    """
    Compare user budget against historical chapter ratios.

    Each item's `valor_unitario` is in €/m². The endpoint returns
    per-chapter deviation and a monetary impact estimate.
    """
    # area_total > 0 is already enforced by the Pydantic schema (gt=0),
    # but we add an explicit 400 for clarity in API docs.
    if presupuesto.area_total <= 0:
        raise HTTPException(status_code=400, detail="area_total debe ser > 0")

    session = _db.get_db()
    try:
        return analizar_comparativa(session, presupuesto)
    finally:
        session.close()
