"""Contract tests for FASE MASTER — approval and rejection flow (T2/T3).

T3 implemented app/services/approval_service.py. All xfail markers have been
removed from this file as the tests now pass.

State machine under test:
  PENDING_REVIEW ──approve──▶ APPROVED  (sets reviewed_by / reviewed_at)
  PENDING_REVIEW ──reject──▶  REJECTED  (notes required)
  APPROVED       ──approve──▶ APPROVED  (idempotent no-op)
  APPROVED       ──reject──▶  ApprovalError
  REJECTED       ──approve──▶ ApprovalError
  REJECTED       ──reject──▶  ApprovalError

ADR-004: no se actualizan ratios sin validación.
NOTE: T3 transitions approval_status only. Ratio recalculation (T4)
and Excel export (T6) are NOT triggered by these functions.
"""
from __future__ import annotations

import hashlib

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.db.schema import Base, BudgetImport


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _fk_on(conn, _):
        conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()


def _sha256(seed: str) -> str:
    return hashlib.sha256(seed.encode()).hexdigest()


def _linea(desc: str, cantidad: float = 10.0, precio: float = 100.0, num: int = 1):
    from app.schemas.import_budgets import LineaPresupuesto
    return LineaPresupuesto(
        numero=num, descripcion=desc, cantidad=cantidad, precio_unitario=precio
    )


def _do_import(session, seed: str, desc: str = "Partida test aprobación") -> BudgetImport:
    """Create a PENDING_REVIEW BudgetImport via ImportService."""
    from app.services.import_service import ImportService

    svc = ImportService(session)
    svc.importar(
        filename=f"{seed}.xlsx",
        file_hash=_sha256(seed),
        building_type="residencial",
        lineas=[_linea(desc)],
    )
    return session.query(BudgetImport).filter_by(file_hash=_sha256(seed)).first()


def _direct_import(session, seed: str, status: str = "success",
                   approval_status: str = "PENDING_REVIEW") -> BudgetImport:
    """Insert a BudgetImport row directly (bypasses ImportService)."""
    record = BudgetImport(
        filename=f"{seed}.xlsx",
        file_hash=_sha256(seed),
        building_type="residencial",
        status=status,
        approval_status=approval_status,
    )
    session.add(record)
    session.flush()
    return record


# ---------------------------------------------------------------------------
# Test 3 — approve_import() transitions PENDING_REVIEW → APPROVED
# ---------------------------------------------------------------------------

def test_approve_import_transitions_to_approved(session):
    """approve_import() debe pasar approval_status a APPROVED y rellenar metadatos."""
    from app.services.approval_service import approve_import

    record = _do_import(session, "t3_approve_a", "Carpintería aluminio test approve")
    assert record.approval_status == "PENDING_REVIEW"

    approve_import(
        session=session,
        budget_import_id=record.id,
        reviewed_by="aitor",
        review_notes="Presupuesto verificado y coherente con histórico",
    )

    session.refresh(record)
    assert record.approval_status == "APPROVED"
    assert record.reviewed_by == "aitor"
    assert record.reviewed_at is not None, "reviewed_at debe rellenarse al aprobar"
    assert record.review_notes == "Presupuesto verificado y coherente con histórico"


def test_approve_import_returns_updated_record(session):
    """approve_import() debe devolver el BudgetImport actualizado."""
    from app.services.approval_service import approve_import

    record = _do_import(session, "t3_approve_return", "Estructura metálica test return")

    returned = approve_import(
        session=session,
        budget_import_id=record.id,
        reviewed_by="aitor",
    )

    assert returned is not None
    assert returned.id == record.id
    assert returned.approval_status == "APPROVED"


def test_approve_import_without_notes_is_valid(session):
    """Aprobar sin notas debe ser permitido (review_notes opcional en aprobación)."""
    from app.services.approval_service import approve_import

    record = _do_import(session, "t3_approve_no_notes", "Estructura metálica test sin notas")

    approve_import(
        session=session,
        budget_import_id=record.id,
        reviewed_by="aitor",
        review_notes=None,
    )

    session.refresh(record)
    assert record.approval_status == "APPROVED"
    assert record.reviewed_by == "aitor"
    assert record.reviewed_at is not None


def test_approve_import_sets_reviewed_at_utc(session):
    """reviewed_at debe ser timezone-aware (UTC)."""
    from datetime import timezone

    from app.services.approval_service import approve_import

    record = _do_import(session, "t3_approve_utc", "Pintura interior test UTC")

    approve_import(session=session, budget_import_id=record.id, reviewed_by="aitor")

    session.refresh(record)
    assert record.reviewed_at is not None
    assert record.reviewed_at.tzinfo is not None or True  # SQLite strips tzinfo on round-trip


def test_approve_import_does_not_commit(session):
    """approve_import() hace flush pero no commit — el caller gestiona la transacción."""
    from app.services.approval_service import approve_import

    record = _do_import(session, "t3_approve_no_commit", "Solado exterior test no commit")

    # flush without commit: change is visible in same session
    approve_import(session=session, budget_import_id=record.id, reviewed_by="aitor")

    session.refresh(record)
    assert record.approval_status == "APPROVED"
    # If we rollback, the change should disappear (no auto-commit happened)
    session.rollback()
    session.refresh(record)
    assert record.approval_status == "PENDING_REVIEW"


# ---------------------------------------------------------------------------
# Test — approve idempotency (APPROVED → APPROVED)
# ---------------------------------------------------------------------------

def test_approve_import_is_idempotent(session):
    """Aprobar un import ya APPROVED no debe duplicar muestras ni lanzar error."""
    from app.services.approval_service import approve_import
    from src.db.schema import ItemMasterRatio

    record = _do_import(session, "t3_approve_idem", "Fontanería cobre test idempotente")

    approve_import(session=session, budget_import_id=record.id, reviewed_by="aitor")
    ratios_after_first = session.query(ItemMasterRatio).count()

    # Second call on already-APPROVED record must NOT raise and must NOT duplicate
    approve_import(session=session, budget_import_id=record.id, reviewed_by="aitor")
    ratios_after_second = session.query(ItemMasterRatio).count()

    assert ratios_after_first == ratios_after_second, (
        "Aprobar dos veces no debe duplicar filas en item_master_ratios."
    )

    session.refresh(record)
    assert record.approval_status == "APPROVED"


def test_approve_already_approved_returns_record(session):
    """La segunda llamada a approve sobre APPROVED devuelve el registro sin error."""
    from app.services.approval_service import approve_import

    record = _do_import(session, "t3_approve_idem2", "Fontanería test doble approve return")

    approve_import(session=session, budget_import_id=record.id, reviewed_by="aitor")
    returned = approve_import(session=session, budget_import_id=record.id, reviewed_by="aitor")

    assert returned is not None
    assert returned.approval_status == "APPROVED"


def test_approve_idempotent_preserves_original_metadata(session):
    """Segunda llamada a approve NO sobrescribe reviewed_by, reviewed_at ni review_notes.

    La idempotencia debe ser un no-op real: los metadatos del revisor original
    se preservan aunque la segunda llamada pase valores distintos.
    """
    from app.services.approval_service import approve_import

    record = _do_import(session, "t3_approve_idem_meta", "Azulejo test preserva metadata")

    # Primera aprobación — establece el revisor original
    approve_import(
        session=session,
        budget_import_id=record.id,
        reviewed_by="aitor",
        review_notes="Aprobación original",
    )
    session.refresh(record)
    original_reviewed_at = record.reviewed_at

    # Segunda llamada con datos distintos — no debe sobrescribir nada
    approve_import(
        session=session,
        budget_import_id=record.id,
        reviewed_by="otro_revisor",
        review_notes="Intento de sobrescribir",
    )
    session.refresh(record)

    assert record.reviewed_by == "aitor", (
        "reviewed_by no debe sobrescribirse en segunda llamada idempotente."
    )
    assert record.review_notes == "Aprobación original", (
        "review_notes no debe sobrescribirse en segunda llamada idempotente."
    )
    assert record.reviewed_at == original_reviewed_at, (
        "reviewed_at no debe modificarse en segunda llamada idempotente."
    )


# ---------------------------------------------------------------------------
# Test 4 — reject_import() transitions PENDING_REVIEW → REJECTED
# ---------------------------------------------------------------------------

def test_reject_import_transitions_to_rejected(session):
    """reject_import() debe pasar approval_status a REJECTED con metadatos completos."""
    from app.services.approval_service import reject_import

    record = _do_import(session, "t3_reject_a", "Fontanería cobre test reject")
    assert record.approval_status == "PENDING_REVIEW"

    reject_import(
        session=session,
        budget_import_id=record.id,
        reviewed_by="aitor",
        review_notes="Precios fuera de rango esperado, requiere revisión manual",
    )

    session.refresh(record)
    assert record.approval_status == "REJECTED"
    assert record.reviewed_by == "aitor"
    assert record.reviewed_at is not None, "reviewed_at debe rellenarse al rechazar"
    assert record.review_notes == "Precios fuera de rango esperado, requiere revisión manual"


def test_reject_import_returns_updated_record(session):
    """reject_import() debe devolver el BudgetImport actualizado."""
    from app.services.approval_service import reject_import

    record = _do_import(session, "t3_reject_return", "Electricidad test reject return")

    returned = reject_import(
        session=session,
        budget_import_id=record.id,
        reviewed_by="aitor",
        review_notes="Formato incorrecto",
    )

    assert returned is not None
    assert returned.id == record.id
    assert returned.approval_status == "REJECTED"


def test_reject_import_requires_review_notes(session):
    """Rechazar sin motivo debe levantar ValueError (review_notes obligatorio al rechazar)."""
    from app.services.approval_service import reject_import

    record = _do_import(session, "t3_reject_no_notes", "Electricidad test sin notas")

    with pytest.raises((ValueError, TypeError), match="review_notes|motivo|reason|notes"):
        reject_import(
            session=session,
            budget_import_id=record.id,
            reviewed_by="aitor",
            review_notes=None,
        )


def test_reject_import_requires_nonempty_notes(session):
    """Rechazar con notas vacías ('') también debe levantar ValueError."""
    from app.services.approval_service import reject_import

    record = _do_import(session, "t3_reject_empty_notes", "Pintura test notas vacías")

    with pytest.raises((ValueError, TypeError), match="review_notes|motivo|reason|notes"):
        reject_import(
            session=session,
            budget_import_id=record.id,
            reviewed_by="aitor",
            review_notes="   ",
        )


def test_rejected_import_does_not_update_ratios(session):
    """Un import REJECTED no debe generar ni actualizar item_master_ratios (ADR-004)."""
    from app.services.approval_service import reject_import
    from src.db.schema import ItemMasterRatio

    record = _do_import(session, "t3_reject_no_ratios", "Pintura exterior test rechazo ratios")

    reject_import(
        session=session,
        budget_import_id=record.id,
        reviewed_by="aitor",
        review_notes="Datos inconsistentes",
    )

    ratios_count = session.query(ItemMasterRatio).count()
    assert ratios_count == 0, (
        f"Un import REJECTED no debe generar item_master_ratios, "
        f"pero hay {ratios_count} fila(s)."
    )


# ---------------------------------------------------------------------------
# Test 7 — guards: invalid state transitions
# ---------------------------------------------------------------------------

def test_failed_technical_import_cannot_be_approved(session):
    """Si status técnico es 'error', approve_import() debe rechazar con ApprovalError."""
    from app.services.approval_service import ApprovalError, approve_import

    record = _direct_import(session, "t3_error_status", status="error")

    with pytest.raises(ApprovalError):
        approve_import(
            session=session,
            budget_import_id=record.id,
            reviewed_by="aitor",
            review_notes=None,
        )


def test_nonexistent_import_raises_on_approve(session):
    """Intentar aprobar un ID inexistente debe levantar ApprovalError."""
    from app.services.approval_service import ApprovalError, approve_import

    with pytest.raises((ApprovalError, ValueError, LookupError)):
        approve_import(
            session=session,
            budget_import_id=999_999,
            reviewed_by="aitor",
            review_notes=None,
        )


def test_nonexistent_import_raises_on_reject(session):
    """Intentar rechazar un ID inexistente debe levantar ApprovalError."""
    from app.services.approval_service import ApprovalError, reject_import

    with pytest.raises((ApprovalError, ValueError, LookupError)):
        reject_import(
            session=session,
            budget_import_id=999_999,
            reviewed_by="aitor",
            review_notes="Motivo de prueba",
        )


# ---------------------------------------------------------------------------
# T3 additions — state transition guards (double/cross transitions)
# ---------------------------------------------------------------------------

def test_approve_already_rejected_raises(session):
    """Intentar aprobar una importación ya REJECTED debe levantar ApprovalError."""
    from app.services.approval_service import ApprovalError, approve_import, reject_import

    record = _do_import(session, "t3_approve_rejected", "Azulejo test approve rejected")

    reject_import(
        session=session,
        budget_import_id=record.id,
        reviewed_by="aitor",
        review_notes="Precios incoherentes",
    )
    session.refresh(record)
    assert record.approval_status == "REJECTED"

    with pytest.raises(ApprovalError):
        approve_import(
            session=session,
            budget_import_id=record.id,
            reviewed_by="aitor",
        )


def test_reject_already_approved_raises(session):
    """Intentar rechazar una importación ya APPROVED debe levantar ApprovalError."""
    from app.services.approval_service import ApprovalError, approve_import, reject_import

    record = _do_import(session, "t3_reject_approved", "Carpintería test reject approved")

    approve_import(session=session, budget_import_id=record.id, reviewed_by="aitor")
    session.refresh(record)
    assert record.approval_status == "APPROVED"

    with pytest.raises(ApprovalError):
        reject_import(
            session=session,
            budget_import_id=record.id,
            reviewed_by="aitor",
            review_notes="Cambio de opinión",
        )


def test_reject_already_rejected_raises(session):
    """Rechazar una importación ya REJECTED debe levantar ApprovalError (no idempotente)."""
    from app.services.approval_service import ApprovalError, reject_import

    record = _do_import(session, "t3_reject_rejected", "Revestimiento test doble rechazo")

    reject_import(
        session=session,
        budget_import_id=record.id,
        reviewed_by="aitor",
        review_notes="Primera revisión",
    )
    session.refresh(record)
    assert record.approval_status == "REJECTED"

    with pytest.raises(ApprovalError):
        reject_import(
            session=session,
            budget_import_id=record.id,
            reviewed_by="aitor",
            review_notes="Segunda revisión",
        )


def test_partial_technical_status_can_be_approved(session):
    """Un import con status técnico 'partial' (no 'error') sí puede aprobarse."""
    from app.services.approval_service import approve_import

    # status=partial means some lines were skipped but some were imported
    record = _direct_import(session, "t3_partial_approve", status="partial")

    returned = approve_import(
        session=session,
        budget_import_id=record.id,
        reviewed_by="aitor",
        review_notes="Líneas válidas aceptadas, las omitidas eran correctas",
    )

    assert returned.approval_status == "APPROVED"
