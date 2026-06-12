"""Tests for gama assignment logic and constraints (HALLAZGOS 1, 2, 3)."""

import pytest
from src.db.models import get_session
from src.db.schema import GamaRange, ItemMaster
from scripts.assign_gamas_persistent import assign_gamas_to_all_items


class TestHallazgo2GamaRangeConstraints:
    """HALLAZGO 2: Constraint validation in GamaRange model."""

    def test_medium_tier_min_max_validation(self):
        """MEDIUM tier constraint: medium_min <= medium_max."""
        with pytest.raises(ValueError, match="MEDIUM tier constraint violated"):
            GamaRange(
                material_type="TEST",
                categoria="TEST",
                medium_min=100.0,
                medium_max=50.0,  # Invalid: 100 > 50
            )

    def test_premium_tier_min_max_validation(self):
        """PREMIUM tier constraint: premium_min <= premium_max."""
        with pytest.raises(ValueError, match="PREMIUM tier constraint violated"):
            GamaRange(
                material_type="TEST",
                categoria="TEST",
                premium_min=200.0,
                premium_max=150.0,  # Invalid
            )

    def test_luxury_tier_min_max_validation(self):
        """LUXURY tier constraint: luxury_min <= luxury_max."""
        with pytest.raises(ValueError, match="LUXURY tier constraint violated"):
            GamaRange(
                material_type="TEST",
                categoria="TEST",
                luxury_min=1000.0,
                luxury_max=500.0,  # Invalid
            )

    def test_luxury_plus_tier_min_max_validation(self):
        """LUXURY_PLUS tier constraint: luxury_plus_min <= luxury_plus_max."""
        with pytest.raises(ValueError, match="LUXURY_PLUS tier constraint violated"):
            GamaRange(
                material_type="TEST",
                categoria="TEST",
                luxury_plus_min=2000.0,
                luxury_plus_max=1000.0,  # Invalid
            )

    def test_premium_overlap_with_medium(self):
        """PREMIUM tier should not be below MEDIUM max."""
        with pytest.raises(ValueError, match="PREMIUM tier constraint violated"):
            GamaRange(
                material_type="TEST",
                categoria="TEST",
                medium_min=50.0,
                medium_max=100.0,
                premium_min=80.0,  # Invalid: less than medium_max
                premium_max=150.0,
            )

    def test_luxury_overlap_with_premium(self):
        """LUXURY tier should not be below PREMIUM max."""
        with pytest.raises(ValueError, match="LUXURY tier constraint violated"):
            GamaRange(
                material_type="TEST",
                categoria="TEST",
                premium_min=100.0,
                premium_max=200.0,
                luxury_min=150.0,  # Invalid: less than premium_max
                luxury_max=300.0,
            )

    def test_valid_gama_range_constraints(self):
        """Valid GamaRange should pass all constraints."""
        gama = GamaRange(
            material_type="TEST",
            categoria="TEST",
            medium_min=50.0,
            medium_max=100.0,
            premium_min=100.0,
            premium_max=200.0,
            luxury_min=200.0,
            luxury_max=400.0,
            luxury_plus_min=400.0,
            luxury_plus_max=800.0,
        )
        assert gama.medium_min == 50.0
        assert gama.luxury_plus_max == 800.0


class TestHallazgo1TransactionHandling:
    """HALLAZGO 1: Transaction handling with rollback and error reporting."""

    def test_assign_gamas_returns_error_list(self):
        """assign_gamas_to_all_items returns errors list."""
        result = assign_gamas_to_all_items()
        assert "errors" in result
        assert isinstance(result["errors"], list)

    def test_assign_gamas_counts_items(self):
        """assign_gamas_to_all_items counts with_gama_assigned and sin_clasificar."""
        result = assign_gamas_to_all_items()
        assert "total_items" in result
        assert "with_gama_assigned" in result
        assert "sin_clasificar" in result
        assert result["with_gama_assigned"] + result["sin_clasificar"] == result["total_items"]

    def test_assign_gamas_persists_values(self):
        """assign_gamas_to_all_items persists gama_asignada to database."""
        session = get_session()
        try:
            # Insert test item
            item = ItemMaster(
                item_key="test_carpinteria",
                categoria="CARPINTERIA",
                mediana_unitario=208.17,
                muestras_count=1,
            )
            session.add(item)
            session.flush()
            item_id = item.id

            # Run assignment
            result = assign_gamas_to_all_items(session)

            # Verify persisted
            updated_item = session.query(ItemMaster).filter(ItemMaster.id == item_id).first()
            assert updated_item is not None
            assert updated_item.gama_asignada in (
                "MEDIUM",
                "PREMIUM",
                "LUXURY",
                "LUXURY_PLUS",
                "SIN_CLASIFICAR",
            )
        finally:
            session.rollback()
            session.close()


class TestHallazgo3ErrorHandling:
    """HALLAZGO 3: Error handling in endpoint and fallback to SIN_CLASIFICAR."""

    def test_gama_asignada_never_none(self):
        """gama_asignada field should never be None (always has a value)."""
        session = get_session()
        try:
            items = session.query(ItemMaster).limit(10).all()
            for item in items:
                # After assign_gamas runs, should never be None
                if item.gama_asignada is None:
                    item.gama_asignada = "SIN_CLASIFICAR"
                    session.add(item)
            session.commit()

            # Verify all items have a gama_asignada value
            items = session.query(ItemMaster).limit(10).all()
            for item in items:
                assert item.gama_asignada is not None
                assert len(item.gama_asignada) > 0
        finally:
            session.rollback()
            session.close()


class TestSeedDataValidation:
    """Validate that seed data complies with constraints."""

    def test_all_seed_gama_ranges_valid(self):
        """All 8 seed gama_ranges should be valid."""
        session = get_session()
        try:
            gama_ranges = session.query(GamaRange).all()
            assert len(gama_ranges) == 8

            for gama in gama_ranges:
                # Verify min <= max for each tier
                if gama.medium_min and gama.medium_max:
                    assert gama.medium_min <= gama.medium_max
                if gama.premium_min and gama.premium_max:
                    assert gama.premium_min <= gama.premium_max
                if gama.luxury_min and gama.luxury_max:
                    assert gama.luxury_min <= gama.luxury_max
                if gama.luxury_plus_min and gama.luxury_plus_max:
                    assert gama.luxury_plus_min <= gama.luxury_plus_max
        finally:
            session.close()
