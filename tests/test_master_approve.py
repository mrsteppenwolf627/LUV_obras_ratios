"""Contract tests for FASE MASTER — approval and rejection flow (T2/T3).

All tests in this file are marked xfail(strict=True) because they depend on
app/services/approval_service.py which will be created in T3.

xfail(strict=True) semantics:
  - While T3 is pending: ImportError from the missing module causes the test
    to FAIL → pytest records it as XFAIL (expected failure) → CI stays green.
  - Once T3 is implemented and a test PASSES: pytest records it as XPASS
    (unexpected pass) → CI fails → that is the signal to remove the xfail
    marker from that specific test.

Do NOT remove a marker until the corresponding test passes reliably.
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


# ---------------------------------------------------------------------------
# Test 3 — approve_import() transitions to APPROVED
# ---------------------------------------------------------------------------

@pytest.mark.xfail(
    strict=True,
    reason="app.services.approval_service not implemented yet (T3 pending)",
)
def test_approve_import_transitions_to_approved(session):
    """approve_import() debe pasar approval_status a APPROVED y rellenar metadatos.

    Contrato esperado de approve_import():
      - approval_status  → "APPROVED"
      - reviewed_by      → valor proporcionado
      - reviewed_at      → timestamp UTC (no nulo)
      - review_notes     → valor proporcionado (puede ser None si no es obligatorio)
    """
    from app.services.approval_service import approve_import  # ImportError → xfail

    record = _do_import(session, "mi_t2_approve3a", "Carpintería aluminio test approve")
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


@pytest.mark.xfail(
    strict=True,
    reason="app.services.approval_service not implemented yet (T3 pending)",
)
def test_approve_import_without_notes_is_valid(session):
    """Aprobar sin notas debe ser permitido (review_notes opcional en aprobación)."""
    from app.services.approval_service import approve_import  # ImportError → xfail

    record = _do_import(session, "mi_t2_approve3b", "Estructura metálica test sin notas")

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


@pytest.mark.xfail(
    strict=True,
    reason="app.services.approval_service not implemented yet (T3 pending)",
)
def test_approve_import_is_idempotent(session):
    """Aprobar un import ya APPROVED no debe duplicar muestras ni lanzar error."""
    from app.services.approval_service import approve_import  # ImportError → xfail
    from src.db.schema import ItemMasterRatio

    record = _do_import(session, "mi_t2_approve3c", "Fontanería cobre test idempotente")

    approve_import(session=session, budget_import_id=record.id, reviewed_by="aitor")
    ratios_after_first = session.query(ItemMasterRatio).count()

    approve_import(session=session, budget_import_id=record.id, reviewed_by="aitor")
    ratios_after_second = session.query(ItemMasterRatio).count()

    assert ratios_after_first == ratios_after_second, (
        "Aprobar dos veces no debe duplicar filas en item_master_ratios."
    )


# ---------------------------------------------------------------------------
# Test 4 — reject_import() transitions to REJECTED
# ---------------------------------------------------------------------------

@pytest.mark.xfail(
    strict=True,
    reason="app.services.approval_service not implemented yet (T3 pending)",
)
def test_reject_import_transitions_to_rejected(session):
    """reject_import() debe pasar approval_status a REJECTED con metadatos completos.

    Contrato esperado de reject_import():
      - approval_status  → "REJECTED"
      - reviewed_by      → valor proporcionado
      - reviewed_at      → timestamp UTC (no nulo)
      - review_notes     → obligatorio al rechazar (motivo del rechazo)
    """
    from app.services.approval_service import reject_import  # ImportError → xfail

    record = _do_import(session, "mi_t2_reject4a", "Fontanería cobre test reject")
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


@pytest.mark.xfail(
    strict=True,
    reason="app.services.approval_service not implemented yet (T3 pending)",
)
def test_reject_import_requires_review_notes(session):
    """Rechazar sin motivo debe levantar ValueError: el motivo es obligatorio al rechazar."""
    from app.services.approval_service import reject_import  # ImportError → xfail

    record = _do_import(session, "mi_t2_reject4b", "Electricidad test rechazo sin notas")

    with pytest.raises((ValueError, TypeError), match="review_notes|motivo|reason|notes"):
        reject_import(
            session=session,
            budget_import_id=record.id,
            reviewed_by="aitor",
            review_notes=None,
        )


@pytest.mark.xfail(
    strict=True,
    reason="app.services.approval_service not implemented yet (T3 pending)",
)
def test_rejected_import_does_not_update_ratios(session):
    """Un import REJECTED no debe generar ni actualizar item_master_ratios.

    ADR-004 y ADR-007: exclusión sin borrado, pero los rechazados nunca
    alimentan ratios definitivos.
    """
    from app.services.approval_service import reject_import  # ImportError → xfail
    from src.db.schema import ItemMasterRatio

    record = _do_import(session, "mi_t2_reject4c", "Pintura exterior test rechazo ratios")

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
# Test 7 — error técnico impide aprobación
# ---------------------------------------------------------------------------

@pytest.mark.xfail(
    strict=True,
    reason="app.services.approval_service not implemented yet (T3 pending)",
)
def test_failed_technical_import_cannot_be_approved(session):
    """Si status técnico es 'error', approve_import() debe rechazar la operación.

    ADR-004: no se actualizan ratios sin validación. Un import técnicamente
    fallido no puede considerarse válido para alimentar el master aunque alguien
    intente aprobarlo manualmente.

    La excepción esperada es ApprovalError (o equivalente) con mensaje que
    identifique el estado de error como causa del bloqueo.
    """
    from app.services.approval_service import ApprovalError, approve_import  # ImportError → xfail

    # Crear BudgetImport directamente con status técnico = error
    record = BudgetImport(
        filename="import_fallido.xlsx",
        file_hash=_sha256("mi_t2_test7_error_status"),
        building_type="residencial",
        status="error",
        approval_status="PENDING_REVIEW",
    )
    session.add(record)
    session.flush()

    with pytest.raises(ApprovalError):
        approve_import(
            session=session,
            budget_import_id=record.id,
            reviewed_by="aitor",
            review_notes=None,
        )


@pytest.mark.xfail(
    strict=True,
    reason="app.services.approval_service not implemented yet (T3 pending)",
)
def test_nonexistent_import_raises_on_approve(session):
    """Intentar aprobar un ID inexistente debe levantar una excepción clara."""
    from app.services.approval_service import ApprovalError, approve_import  # ImportError → xfail

    with pytest.raises((ApprovalError, ValueError, LookupError)):
        approve_import(
            session=session,
            budget_import_id=999_999,
            reviewed_by="aitor",
            review_notes=None,
        )
