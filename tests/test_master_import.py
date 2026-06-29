"""Contract tests for FASE MASTER — import entry gate (T2).

These tests define the invariant that holds from T1 onwards:
  - Every new BudgetImport starts as PENDING_REVIEW.
  - A PENDING_REVIEW import NEVER feeds item_master_ratios.
  - The technical `status` field and the functional `approval_status` are
    fully independent.

Both tests pass without any T3 code because:
  1. T1 added the approval_status column with default="PENDING_REVIEW".
  2. ImportService has never touched item_master_ratios (that only happens
     in /api/items/analisis, which is frozen for the canonic flow).

These tests are permanent regression guards: they must keep passing through
T3, T4, T6 and beyond — if any future change causes a PENDING_REVIEW import
to populate item_master_ratios, these tests will catch it.
"""
from __future__ import annotations

import hashlib

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.db.schema import Base, BudgetImport, ItemMasterRatio


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


def _do_import(session, seed: str, desc: str, lineas=None) -> BudgetImport:
    """Run ImportService and return the resulting BudgetImport record."""
    from app.services.import_service import ImportService

    svc = ImportService(session)
    svc.importar(
        filename=f"{seed}.xlsx",
        file_hash=_sha256(seed),
        building_type="residencial",
        lineas=lineas or [_linea(desc)],
    )
    return session.query(BudgetImport).filter_by(file_hash=_sha256(seed)).first()


# ---------------------------------------------------------------------------
# Test 1 — default approval_status = PENDING_REVIEW
# ---------------------------------------------------------------------------

class TestDefaultApprovalStatus:
    def test_new_import_defaults_to_pending_review(self, session):
        """BudgetImport creado por ImportService debe quedar en PENDING_REVIEW.

        Este es el portón de entrada del flujo FASE MASTER: ninguna importación
        puede alimentar ratios hasta que un humano la apruebe explícitamente.
        """
        record = _do_import(session, "mi_t2_import1", "Alicatado baño test master")

        assert record is not None
        assert record.approval_status == "PENDING_REVIEW", (
            "El approval_status inicial siempre debe ser PENDING_REVIEW. "
            "Las importaciones no aprobadas no deben alterar ratios definitivos."
        )

    def test_technical_status_and_approval_status_are_independent(self, session):
        """status (técnico) y approval_status (funcional) son campos independientes.

        Una ingesta completamente exitosa (status=success) sigue en PENDING_REVIEW
        hasta aprobación explícita. El estado de ingesta no implica aprobación.
        """
        record = _do_import(session, "mi_t2_import1b", "Pintura plástica lisa independencia")

        assert record.status == "success"          # ingesta OK
        assert record.approval_status == "PENDING_REVIEW"  # aprobación pendiente

    def test_partial_import_also_defaults_to_pending_review(self, session):
        """Incluso una importación parcial (status=partial) empieza en PENDING_REVIEW."""
        record = _do_import(
            session,
            "mi_t2_import1c",
            "Partida parcial test",
            lineas=[
                _linea("Solado exterior válido", num=1),
                _linea("Sin cantidad inválida", cantidad=0.0, num=2),
            ],
        )

        assert record.status == "partial"
        assert record.approval_status == "PENDING_REVIEW"

    def test_review_fields_start_as_null(self, session):
        """reviewed_by, reviewed_at y review_notes son NULL en importación nueva."""
        record = _do_import(session, "mi_t2_import1d", "Estructura hormigón test nulos")

        assert record.reviewed_by is None
        assert record.reviewed_at is None
        assert record.review_notes is None


# ---------------------------------------------------------------------------
# Test 2 — PENDING_REVIEW no alimenta item_master_ratios
# ---------------------------------------------------------------------------

class TestPendingReviewDoesNotFeedRatios:
    def test_pending_review_import_does_not_update_final_ratios(self, session):
        """Una importación PENDING_REVIEW no debe generar filas en item_master_ratios.

        ADR-004: no se actualizan ratios sin validación.
        ImportService crea ItemMaster e ItemInstance pero nunca toca
        item_master_ratios — eso solo ocurrirá en approve_import() (T3).
        """
        record = _do_import(
            session,
            "mi_t2_import2a",
            "Solado porcelánico 60x60 test no ratios",
        )

        assert record.approval_status == "PENDING_REVIEW"

        ratios_count = session.query(ItemMasterRatio).count()
        assert ratios_count == 0, (
            f"item_master_ratios debe estar vacía tras PENDING_REVIEW, "
            f"pero tiene {ratios_count} fila(s). "
            "Solo approve_import() debe actualizar ratios."
        )

    def test_multiple_pending_imports_still_no_ratios(self, session):
        """Varios imports consecutivos sin aprobar nunca generan item_master_ratios."""
        for i in range(3):
            _do_import(
                session,
                f"mi_t2_import2b_{i}",
                f"Partida multi pendiente número {i}",
            )

        ratios_count = session.query(ItemMasterRatio).count()
        assert ratios_count == 0, (
            "Múltiples imports PENDING_REVIEW acumulados no deben generar "
            f"item_master_ratios (hay {ratios_count} filas)."
        )

    def test_item_master_created_but_ratios_empty(self, session):
        """ImportService crea ItemMaster (catálogo) pero NO item_master_ratios.

        El catálogo crece con cada importación; los ratios calculados solo
        aparecen tras aprobación explícita.
        """
        from src.db.schema import ItemMaster

        _do_import(
            session,
            "mi_t2_import2c",
            "Carpintería aluminio lacado test catálogo",
        )

        masters_count = session.query(ItemMaster).count()
        ratios_count = session.query(ItemMasterRatio).count()

        assert masters_count >= 1, "El ItemMaster debe existir tras importar"
        assert ratios_count == 0, (
            "item_master_ratios debe seguir vacía — los ratios solo se calculan "
            "tras aprobación (T3)."
        )
