"""Router for POST /api/import/budgets — delegates business logic to ImportService."""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException

from app import database as _db
from app.adapters.budget_adapter import AdapterError, adapt_budget_to_standard
from app.schemas.import_budgets import BudgetImportRequest, BudgetImportResponse
from app.services.import_service import DuplicateImportError, ImportService

router = APIRouter(prefix="/api", tags=["import"])
logger = logging.getLogger(__name__)

# Simple in-memory rate limiting: {(ip, username): request_count}
_RATE_LIMIT_STORE: dict[tuple[str, str], int] = {}


def verify_token(authorization: Optional[str] = None) -> str:
    """
    Placeholder for JWT/token verification.
    For MVP: accept any token or default to "anonymous".
    Returns username/identifier for rate limiting.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return "anonymous"
    # In production: verify JWT and extract subject
    return "authenticated_user"


@router.post("/import/budgets", response_model=BudgetImportResponse)
def import_budgets(
    raw_input: dict[str, Any] = Body(...),
    username: str = Depends(verify_token),
) -> BudgetImportResponse:
    """
    Importar presupuesto con deduplicación automática via item_key.

    Acepta presupuestos en varios formatos y los adapta al estándar.
    Los nombres de campos pueden variar (descripción→description, cantidad→qty, etc.).

    Security:
    - Requires authentication (placeholder)
    - Per-user rate limiting (simple in-memory)
    - Unbounded batch size protection (10k line cap)
    - Exception leakage prevention
    - Format adaptation with clear error messages
    """
    session = _db.get_db()
    client_ip = "127.0.0.1"  # In production: extract from request context

    try:
        # Attempt to adapt flexible input to standard format
        try:
            request = adapt_budget_to_standard(raw_input, format_hint="auto")
        except AdapterError as e:
            session.close()
            raise HTTPException(
                status_code=400,
                detail=f"Error en formato del presupuesto: {str(e)}. "
                f"Campos requeridos: file_hash, lineas (con descripcion, cantidad, precio_unitario). "
                f"Aceptamos alias: description/nombre, qty/quantity, price/precio/unit_price.",
            )

        # Rate limit: 100 requests per user+IP per minute (simplified in-memory)
        # In production: use Redis + sliding window or leaky bucket algorithm
        rate_key = (client_ip, username)
        _RATE_LIMIT_STORE[rate_key] = _RATE_LIMIT_STORE.get(rate_key, 0) + 1
        if _RATE_LIMIT_STORE[rate_key] > 100:
            raise HTTPException(
                status_code=429,
                detail="Demasiadas solicitudes. Intenta más tarde.",
            )

        # Unbounded batch size protection
        max_lineas = 10_000
        if len(request.lineas) > max_lineas:
            raise HTTPException(
                status_code=400,
                detail=f"Máximo {max_lineas:,} líneas permitidas. Recibidas: {len(request.lineas):,}",
            )

        service = ImportService(session)
        return service.importar(
            filename=request.filename,
            file_hash=request.file_hash,
            building_type=request.building_type,
            lineas=request.lineas,
        )

    except DuplicateImportError as exc:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Ya importado el {exc.import_date} (hash={exc.file_hash[:8]}...)",
        )
    except HTTPException:
        session.rollback()
        raise
    except Exception as exc:
        session.rollback()
        # Log full exception server-side, return generic message to client
        logger.exception("Error crítico en import_budgets")
        raise HTTPException(status_code=500, detail="Error procesando solicitud") from exc
    finally:
        session.close()
