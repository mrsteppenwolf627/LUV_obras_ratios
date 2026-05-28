"""Tests for FASE 1: percentil_25, percentil_75, std_dev on Ratio model."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, event, inspect
from sqlalchemy.orm import sessionmaker

from src.db.schema import Base, Budget, LineItem, Ratio
from src.ratios.calculator import recalculate_all_ratios


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_db(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", echo=False)

    @event.listens_for(engine, "connect")
    def fk_on(conn, _):
        conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session, engine
    session.close()


def _make_budget(session, filename, file_hash, surface_m2, building_type="residential"):
    b = Budget(
        filename=filename,
        file_hash=file_hash,
        source_format="excel",
        total_cost=100_000.0,
        surface_m2=surface_m2,
        building_type=building_type,
    )
    session.add(b)
    session.flush()
    return b


def _make_item(session, budget, chapter_code, total_cost):
    item = LineItem(
        budget_id=budget.id,
        chapter_code=chapter_code,
        chapter_name=chapter_code,
        total_cost=total_cost,
        validation_status="VALID",
    )
    session.add(item)
    session.flush()
    return item


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------


class TestRatioModelColumns:
    def test_model_has_percentil_25(self):
        assert hasattr(Ratio, "percentil_25")

    def test_model_has_percentil_75(self):
        assert hasattr(Ratio, "percentil_75")

    def test_model_has_std_dev(self):
        assert hasattr(Ratio, "std_dev")

    def test_new_columns_in_live_db(self, tmp_db):
        _, engine = tmp_db
        cols = {c["name"] for c in inspect(engine).get_columns("ratios")}
        assert "percentil_25" in cols
        assert "percentil_75" in cols
        assert "std_dev" in cols

    def test_new_columns_nullable(self, tmp_db):
        _, engine = tmp_db
        col_map = {c["name"]: c for c in inspect(engine).get_columns("ratios")}
        assert col_map["percentil_25"]["nullable"] is True
        assert col_map["percentil_75"]["nullable"] is True
        assert col_map["std_dev"]["nullable"] is True


# ---------------------------------------------------------------------------
# recalculate_all_ratios with multiple budgets
# ---------------------------------------------------------------------------


class TestRecalculatePercentiles:
    def test_single_budget_populates_fields(self, tmp_db):
        session, _ = tmp_db
        b = _make_budget(session, "b1.xlsx", "h" * 64, surface_m2=100.0)
        _make_item(session, b, "ESTRUCTURA", total_cost=50_000.0)

        recalculate_all_ratios(session)
        session.flush()

        ratio = session.query(Ratio).filter_by(chapter_code="ESTRUCTURA").first()
        assert ratio is not None
        assert ratio.median == pytest.approx(500.0)  # 50000 / 100
        assert ratio.percentil_25 == pytest.approx(500.0)
        assert ratio.percentil_75 == pytest.approx(500.0)
        assert ratio.std_dev == pytest.approx(0.0)
        assert ratio.sample_count == 1

    def test_two_budgets_compute_correct_statistics(self, tmp_db):
        session, _ = tmp_db
        # Budget 1: 40000 / 100 = 400 €/m²
        b1 = _make_budget(session, "b1.xlsx", "h1" * 32, surface_m2=100.0)
        _make_item(session, b1, "ESTRUCTURA", total_cost=40_000.0)
        # Budget 2: 60000 / 100 = 600 €/m²
        b2 = _make_budget(session, "b2.xlsx", "h2" * 32, surface_m2=100.0)
        _make_item(session, b2, "ESTRUCTURA", total_cost=60_000.0)

        recalculate_all_ratios(session)
        session.flush()

        ratio = session.query(Ratio).filter_by(chapter_code="ESTRUCTURA").first()
        assert ratio.sample_count == 2
        assert ratio.median == pytest.approx(500.0)
        assert ratio.min_value == pytest.approx(400.0)
        assert ratio.max_value == pytest.approx(600.0)
        assert ratio.std_dev is not None
        assert ratio.std_dev > 0
        assert ratio.percentil_25 is not None
        assert ratio.percentil_75 is not None
        assert ratio.percentil_25 <= ratio.median <= ratio.percentil_75

    def test_four_budgets_percentile_ordering(self, tmp_db):
        session, _ = tmp_db
        costs = [200.0, 400.0, 600.0, 800.0]  # €/m² after dividing by 100 m²
        for i, cost_per_m2 in enumerate(costs):
            b = _make_budget(session, f"b{i}.xlsx", f"{'h' + str(i):<64}", surface_m2=100.0)
            _make_item(session, b, "CIMENTACION", total_cost=cost_per_m2 * 100.0)

        recalculate_all_ratios(session)
        session.flush()

        ratio = session.query(Ratio).filter_by(chapter_code="CIMENTACION").first()
        assert ratio.sample_count == 4
        assert ratio.percentil_25 < ratio.median < ratio.percentil_75
        assert ratio.percentil_25 >= ratio.min_value
        assert ratio.percentil_75 <= ratio.max_value

    def test_excluded_items_not_counted(self, tmp_db):
        session, _ = tmp_db
        b = _make_budget(session, "b1.xlsx", "h" * 64, surface_m2=100.0)
        _make_item(session, b, "CUBIERTA", total_cost=30_000.0)
        # Add an EXCLUDED item — should not affect ratio
        item_excl = LineItem(
            budget_id=b.id,
            chapter_code="CUBIERTA",
            chapter_name="CUBIERTA",
            total_cost=999_999.0,
            validation_status="EXCLUDED",
        )
        session.add(item_excl)
        session.flush()

        recalculate_all_ratios(session)
        session.flush()

        ratio = session.query(Ratio).filter_by(chapter_code="CUBIERTA").first()
        assert ratio.median == pytest.approx(300.0)  # Only VALID item counts
        assert ratio.sample_count == 1

    def test_no_surface_m2_skips_ratio_values(self, tmp_db):
        session, _ = tmp_db
        b = _make_budget(session, "b1.xlsx", "h" * 64, surface_m2=None)
        _make_item(session, b, "INSTALACIONES", total_cost=20_000.0)

        recalculate_all_ratios(session)
        session.flush()

        ratio = session.query(Ratio).filter_by(chapter_code="INSTALACIONES").first()
        assert ratio is not None
        assert ratio.median is None
        assert ratio.percentil_25 is None

    def test_idempotent_recalculation(self, tmp_db):
        session, _ = tmp_db
        b = _make_budget(session, "b1.xlsx", "h" * 64, surface_m2=200.0)
        _make_item(session, b, "REVESTIMIENTOS", total_cost=10_000.0)

        recalculate_all_ratios(session)
        session.flush()
        ratio_first = session.query(Ratio).filter_by(chapter_code="REVESTIMIENTOS").first()
        median_first = ratio_first.median

        recalculate_all_ratios(session)
        session.flush()
        ratio_second = session.query(Ratio).filter_by(chapter_code="REVESTIMIENTOS").first()

        assert ratio_second.median == pytest.approx(median_first)
        assert session.query(Ratio).filter_by(chapter_code="REVESTIMIENTOS").count() == 1
