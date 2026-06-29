"""Approval service for FASE MASTER — human-gated import workflow.

State machine for BudgetImport.approval_status:

  PENDING_REVIEW ──approve──▶ APPROVED
  PENDING_REVIEW ──reject──▶ REJECTED
  APPROVED       ──approve──▶ APPROVED  (idempotent, no-op)
  APPROVED       ──reject──▶ ApprovalError
  REJECTED       ──approve──▶ ApprovalError
  REJECTED       ──reject──▶ ApprovalError

ADR-004: no se actualizan ratios sin validación.
NOTE: T3 — this service only manages approval_status transitions.
Ratio recalculation (T4) and Excel export (T6) are NOT triggered here.
The caller (router T4) is responsible for committing the transaction.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from src.db.schema import BudgetImport


class ApprovalError(Exception):
    """Raised when an approval or rejection operation is not permitted.

    Covers: record not found, wrong technical status, invalid state transition.
    """


def approve_import(
    session: Session,
    budget_import_id: int,
    reviewed_by: str,
    review_notes: Optional[str] = None,
) -> BudgetImport:
    """Transition a BudgetImport to APPROVED.

    Rules:
    - Record must exist → ApprovalError otherwise.
    - Technical status must not be "error" → ApprovalError otherwise (ADR-004).
    - If already APPROVED: no-op, return existing record (idempotent).
    - If REJECTED: transition not allowed → ApprovalError.
    - If PENDING_REVIEW: transition to APPROVED, fill review metadata.

    Does session.flush() but NOT session.commit().
    The caller owns the transaction.
    """
    record = session.query(BudgetImport).filter_by(id=budget_import_id).first()
    if record is None:
        raise ApprovalError(
            f"BudgetImport con id={budget_import_id} no encontrado."
        )

    if record.status == "error":
        raise ApprovalError(
            f"No se puede aprobar la importación id={budget_import_id}: "
            f"el estado técnico es 'error'. "
            "Solo importaciones con status success o partial pueden aprobarse."
        )

    if record.approval_status == "APPROVED":
        # Idempotent: already approved, return as-is without modifying anything.
        return record

    if record.approval_status == "REJECTED":
        raise ApprovalError(
            f"No se puede aprobar la importación id={budget_import_id}: "
            f"ya fue rechazada. Crea una nueva importación si procede."
        )

    # PENDING_REVIEW → APPROVED
    record.approval_status = "APPROVED"
    record.reviewed_by = reviewed_by
    record.reviewed_at = datetime.now(timezone.utc)
    record.review_notes = review_notes

    session.flush()
    return record


def reject_import(
    session: Session,
    budget_import_id: int,
    reviewed_by: str,
    review_notes: Optional[str] = None,
) -> BudgetImport:
    """Transition a BudgetImport to REJECTED.

    Rules:
    - Record must exist → ApprovalError otherwise.
    - review_notes is required when rejecting → ValueError otherwise.
    - Only PENDING_REVIEW can be rejected → ApprovalError for any other state.

    Does session.flush() but NOT session.commit().
    The caller owns the transaction.
    """
    if not review_notes or not review_notes.strip():
        raise ValueError(
            "review_notes es obligatorio al rechazar una importación. "
            "Proporciona el motivo del rechazo."
        )

    record = session.query(BudgetImport).filter_by(id=budget_import_id).first()
    if record is None:
        raise ApprovalError(
            f"BudgetImport con id={budget_import_id} no encontrado."
        )

    if record.approval_status != "PENDING_REVIEW":
        raise ApprovalError(
            f"No se puede rechazar la importación id={budget_import_id}: "
            f"el estado actual es '{record.approval_status}'. "
            "Solo importaciones en PENDING_REVIEW pueden rechazarse."
        )

    # PENDING_REVIEW → REJECTED
    record.approval_status = "REJECTED"
    record.reviewed_by = reviewed_by
    record.reviewed_at = datetime.now(timezone.utc)
    record.review_notes = review_notes

    session.flush()
    return record
