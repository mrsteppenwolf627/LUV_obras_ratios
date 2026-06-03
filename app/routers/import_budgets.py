"""Router for POST /api/import/budgets — delegates business logic to ImportService."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app import database as _db
from app.schemas.import_budgets import BudgetImportRequest, BudgetImportResponse
from app.services.import_service import DuplicateImportError, ImportService

router = APIRouter(prefix="/api", tags=["import"])
logger = logging.getLogger(__name__)


@router.post("/import/budgets", response_model=BudgetImportResponse)
def import_budgets(request: BudgetImportRequest) -> BudgetImportResponse:
    """Importar presupuesto con deduplicación automática via item_key."""
    session = _db.get_db()
    try:
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
        logger.exception("Error crítico en import_budgets: %s", exc)
        raise HTTPException(status_code=500, detail=f"Error al importar: {exc}") from exc
    finally:
        session.close()
