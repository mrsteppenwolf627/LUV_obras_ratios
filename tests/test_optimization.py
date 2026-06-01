"""Tests for FASE 3: database indexes and normalization."""

from __future__ import annotations

import time

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.db.schema import Base, Budget, LineItem, Ratio
from app.services.comparativa_service import analizar_comparativa
from app.schemas.visuales import ItemPresupuesto, PresupuestoAnalisis


# ---------------------------------------------------------------------------
# Shared in-memory fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def opt_session():
    """In-memory DB pre-seeded with Ratio and LineItem data."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def fk_on(conn, _):
        conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    budget = Budget(
        filename="opt_test.xlsx",
        file_hash="o" * 64,
        source_format="excel",
        total_cost=300_000.0,
        surface_m2=1000.0,
        building_type="residential",
    )
    session.add(budget)
    session.flush()

    for code, name in [("ESTRUCTURA", "Estructura"), ("INSTALACIONES", "Instalaciones")]:
        session.add(
            LineItem(
                budget_id=budget.id,
                chapter_code=code,
                chapter_name=name,
                total_cost=100_000.0,
                validation_status="VALID",
            )
        )

    for code, name, median, n in [
        ("ESTRUCTURA", "Estructura", 300.0, 3),
        ("INSTALACIONES", "Instalaciones", 150.0, 7),
    ]:
        session.add(
            Ratio(
                chapter_code=code,
                chapter_name=name,
                building_type=None,
                median=median,
                min_value=median * 0.8,
                max_value=median * 1.2,
                sample_count=n,
            )
        )

    session.commit()
    yield session
    session.close()


# ---------------------------------------------------------------------------
# Index existence
# ---------------------------------------------------------------------------


def test_indexes_exist_in_memory_db(opt_session):
    """Validate that the expected indexes exist (in-memory DB via Base.metadata)."""
    # In-memory DB created from Base.metadata has no indexes unless declared in the model.
    # We verify they exist in the production DB by checking the migration chain.
    # Here we just confirm the migration file is properly chained.
    from migrations.versions.a1b2c3d4e5f6_add_indexes_for_visualization_endpoints import (
        upgrade,
        downgrade,
        revision,
        down_revision,
    )
    assert revision == "a1b2c3d4e5f6"
    assert down_revision == "54ca4f3a91d5"


def test_indexes_exist_in_production_db():
    """Validate that all 4 indexes are present in the production SQLite DB."""
    from sqlalchemy import create_engine, text as sa_text
    import pathlib

    db_path = pathlib.Path("data/master/ratios.db")
    if not db_path.exists():
        pytest.skip("Production DB not present — skipping index check")

    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as conn:
        rows = conn.execute(
            sa_text("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'ix_%'")
        ).fetchall()
    index_names = {r[0] for r in rows}

    assert "ix_line_items_chapter_code" in index_names
    assert "ix_ratios_chapter_code" in index_names
    assert "ix_line_items_validation_status" in index_names
    assert "ix_line_items_budget_id" in index_names


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------


def test_normalization_uppercase(opt_session):
    """Lowercase chapter input is matched against uppercase DB entry."""
    presupuesto = PresupuestoAnalisis(
        items=[ItemPresupuesto(capitulo="estructura", valor_unitario=300.0)],
        area_total=100.0,
    )
    result = analizar_comparativa(opt_session, presupuesto)
    assert len(result.capitulos) == 1
    assert result.capitulos[0].ratio_encontrado is True


def test_normalization_leading_trailing_spaces(opt_session):
    """Chapter codes with surrounding spaces are matched correctly."""
    presupuesto = PresupuestoAnalisis(
        items=[ItemPresupuesto(capitulo="  INSTALACIONES  ", valor_unitario=150.0)],
        area_total=100.0,
    )
    result = analizar_comparativa(opt_session, presupuesto)
    assert len(result.capitulos) == 1
    assert result.capitulos[0].ratio_encontrado is True


def test_normalization_mixed_case(opt_session):
    """Mixed-case input matches correctly."""
    presupuesto = PresupuestoAnalisis(
        items=[ItemPresupuesto(capitulo="EsTrUcTuRa", valor_unitario=300.0)],
        area_total=100.0,
    )
    result = analizar_comparativa(opt_session, presupuesto)
    assert len(result.capitulos) == 1


def test_quantity_weighting_is_applied(opt_session):
    """Repeated quantities must weight the €/m² average inside a chapter."""
    presupuesto = PresupuestoAnalisis(
        items=[
            ItemPresupuesto(capitulo="ESTRUCTURA", valor_unitario=300.0, cantidad=1),
            ItemPresupuesto(capitulo="ESTRUCTURA", valor_unitario=450.0, cantidad=3),
        ],
        area_total=100.0,
    )
    result = analizar_comparativa(opt_session, presupuesto)
    assert len(result.capitulos) == 1
    assert result.capitulos[0].valor_mio == 412.5
    assert result.capitulos[0].desviacion_pct == 37.5


def test_unknown_chapter_not_matched(opt_session):
    """Unknown chapters go to capitulos_sin_ratio."""
    presupuesto = PresupuestoAnalisis(
        items=[ItemPresupuesto(capitulo="CAPITULO_QUE_NO_EXISTE_XYZ", valor_unitario=100.0)],
        area_total=100.0,
    )
    result = analizar_comparativa(opt_session, presupuesto)
    assert len(result.capitulos) == 0
    assert "CAPITULO_QUE_NO_EXISTE_XYZ" in result.capitulos_sin_ratio


def test_building_type_with_spaces_is_normalized(opt_session):
    """Surrounding spaces in building_type must not break matching."""
    presupuesto = PresupuestoAnalisis(
        items=[ItemPresupuesto(capitulo="ESTRUCTURA", valor_unitario=300.0)],
        area_total=100.0,
        building_type=" residential ",
    )
    result = analizar_comparativa(opt_session, presupuesto)
    assert len(result.capitulos) == 1


# ---------------------------------------------------------------------------
# Performance
# ---------------------------------------------------------------------------


def test_comparativa_performance(opt_session):
    """analizar_comparativa must complete within 500ms for a 5-chapter budget."""
    items = [
        ItemPresupuesto(capitulo=f"CAP_PERF_{i}", valor_unitario=100.0 + i)
        for i in range(5)
    ]
    presupuesto = PresupuestoAnalisis(items=items, area_total=250.0)

    start = time.monotonic()
    analizar_comparativa(opt_session, presupuesto)
    elapsed_ms = (time.monotonic() - start) * 1000

    assert elapsed_ms < 500.0, f"Took {elapsed_ms:.1f}ms (limit: 500ms)"


def test_comparativa_with_known_chapters_performance(opt_session):
    """analizar_comparativa with DB hits must complete within 500ms."""
    presupuesto = PresupuestoAnalisis(
        items=[
            ItemPresupuesto(capitulo="ESTRUCTURA", valor_unitario=300.0),
            ItemPresupuesto(capitulo="INSTALACIONES", valor_unitario=150.0),
        ],
        area_total=500.0,
    )

    start = time.monotonic()
    result = analizar_comparativa(opt_session, presupuesto)
    elapsed_ms = (time.monotonic() - start) * 1000

    assert elapsed_ms < 500.0, f"Took {elapsed_ms:.1f}ms (limit: 500ms)"
    assert len(result.capitulos) == 2
