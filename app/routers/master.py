"""Router for FASE MASTER approval flow — /api/master/*.

NOTE (T4): This router is NOT yet registered in app/main.py or api/index.py.
Registration happens in T5. The router is fully functional and tested
independently via a test-local FastAPI app.

Endpoints:
  GET  /api/master/status                        — flow health/phase info
  GET  /api/master/imports                       — list imports (filterable)
  GET  /api/master/imports/pending               — shortcut: PENDING_REVIEW only
  GET  /api/master/imports/{import_id}           — single import detail
  POST /api/master/imports/{import_id}/approve   — approve (PENDING → APPROVED)
  POST /api/master/imports/{import_id}/reject    — reject  (PENDING → REJECTED)

No ratio recalculation. No Excel export. No side effects beyond approval_status.
The service (approval_service.py) does flush(); this router does commit/rollback.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict

from app import database as _db
from app.services.approval_service import ApprovalError, approve_import, reject_import
from src.db.schema import BudgetImport

router = APIRouter(prefix="/api/master", tags=["master"])
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic schemas (inline — no separate schema file needed for T4)
# ---------------------------------------------------------------------------

class BudgetImportOut(BaseModel):
    """Serialisation of a BudgetImport row for API responses."""

    id: int
    filename: str
    file_hash: str
    status: str
    approval_status: str
    building_type: Optional[str] = None
    import_date: Optional[datetime] = None
    items_count: Optional[int] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ApproveBody(BaseModel):
    reviewed_by: str
    notes: Optional[str] = None


class RejectBody(BaseModel):
    reviewed_by: str
    notes: str


# ---------------------------------------------------------------------------
# GET /api/master/status
# ---------------------------------------------------------------------------

@router.get("/status")
def master_status():
    """Return FASE MASTER flow metadata — useful for health checks and UI banners."""
    return {
        "phase": "FASE_MASTER",
        "approval_flow_enabled": True,
        "message": (
            "Flujo de aprobación activo. Las importaciones quedan en PENDING_REVIEW "
            "hasta aprobación explícita. Solo los presupuestos APPROVED alimentan ratios "
            "y el exportador LUV_RATIOS_MASTER.xlsx."
        ),
    }


# ---------------------------------------------------------------------------
# GET /api/master/imports
# ---------------------------------------------------------------------------

@router.get("/imports", response_model=List[BudgetImportOut])
def list_imports(
    approval_status: Optional[str] = None,
    technical_status: Optional[str] = None,
    limit: int = 100,
):
    """List BudgetImport records with optional filters.

    Query params:
      approval_status  — PENDING_REVIEW | APPROVED | REJECTED
      technical_status — success | partial | error
      limit            — max records returned (default 100, max 500)
    """
    limit = min(limit, 500)
    session = _db.get_db()
    try:
        q = session.query(BudgetImport)
        if approval_status:
            q = q.filter(BudgetImport.approval_status == approval_status.upper())
        if technical_status:
            q = q.filter(BudgetImport.status == technical_status.lower())
        records = q.order_by(BudgetImport.import_date.desc()).limit(limit).all()
        return [BudgetImportOut.model_validate(r) for r in records]
    finally:
        session.close()


# ---------------------------------------------------------------------------
# GET /api/master/imports/pending
# NOTE: must be defined BEFORE /{import_id} to avoid path collision
# ---------------------------------------------------------------------------

@router.get("/imports/pending", response_model=List[BudgetImportOut])
def list_pending_imports(limit: int = 100):
    """Shortcut: list only PENDING_REVIEW imports, newest first."""
    limit = min(limit, 500)
    session = _db.get_db()
    try:
        records = (
            session.query(BudgetImport)
            .filter(BudgetImport.approval_status == "PENDING_REVIEW")
            .order_by(BudgetImport.import_date.desc())
            .limit(limit)
            .all()
        )
        return [BudgetImportOut.model_validate(r) for r in records]
    finally:
        session.close()


# ---------------------------------------------------------------------------
# GET /api/master/imports/{import_id}
# ---------------------------------------------------------------------------

@router.get("/imports/{import_id}", response_model=BudgetImportOut)
def get_import(import_id: int):
    """Return detail for a single BudgetImport. 404 if not found."""
    session = _db.get_db()
    try:
        record = session.query(BudgetImport).filter_by(id=import_id).first()
        if record is None:
            raise HTTPException(status_code=404, detail=f"Import {import_id} no encontrado")
        return BudgetImportOut.model_validate(record)
    finally:
        session.close()


# ---------------------------------------------------------------------------
# POST /api/master/imports/{import_id}/approve
# ---------------------------------------------------------------------------

@router.post("/imports/{import_id}/approve", response_model=BudgetImportOut)
def approve_import_endpoint(import_id: int, body: ApproveBody):
    """Transition a PENDING_REVIEW import to APPROVED.

    Body: { "reviewed_by": "...", "notes": "..." }

    Returns the updated BudgetImport.
    400 if transition is not allowed (wrong state, status=error, not found).

    NOTE (T4): does NOT recalculate ratios. That happens in a future task.
    """
    session = _db.get_db()
    try:
        record = approve_import(
            session=session,
            budget_import_id=import_id,
            reviewed_by=body.reviewed_by,
            review_notes=body.notes,
        )
        session.commit()
        return BudgetImportOut.model_validate(record)
    except ApprovalError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        session.rollback()
        logger.exception("Error inesperado en approve_import_endpoint id=%d", import_id)
        raise HTTPException(status_code=500, detail="Error interno al aprobar la importación")
    finally:
        session.close()


# ---------------------------------------------------------------------------
# POST /api/master/imports/{import_id}/reject
# ---------------------------------------------------------------------------

@router.post("/imports/{import_id}/reject", response_model=BudgetImportOut)
def reject_import_endpoint(import_id: int, body: RejectBody):
    """Transition a PENDING_REVIEW import to REJECTED.

    Body: { "reviewed_by": "...", "notes": "..." }  (notes required)

    Returns the updated BudgetImport.
    400 if transition is not allowed or notes are missing.
    """
    session = _db.get_db()
    try:
        record = reject_import(
            session=session,
            budget_import_id=import_id,
            reviewed_by=body.reviewed_by,
            review_notes=body.notes,
        )
        session.commit()
        return BudgetImportOut.model_validate(record)
    except (ApprovalError, ValueError) as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        session.rollback()
        logger.exception("Error inesperado en reject_import_endpoint id=%d", import_id)
        raise HTTPException(status_code=500, detail="Error interno al rechazar la importación")
    finally:
        session.close()
