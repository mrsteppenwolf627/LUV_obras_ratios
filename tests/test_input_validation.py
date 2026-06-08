"""Tests for input validation: NaN, Infinity, string bounds, extra fields."""

from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from app.schemas.import_budgets import BudgetImportRequest, LineaPresupuesto


class TestLineaPresupuestoValidation:
    """Test LineaPresupuesto input validation."""

    def test_precio_unitario_finite_accepts_positive(self):
        """Valid positive price should be accepted."""
        linea = LineaPresupuesto(
            descripcion="Test",
            cantidad=10.0,
            precio_unitario=100.5,
        )
        assert linea.precio_unitario == 100.5

    def test_precio_unitario_rejects_nan(self):
        """NaN price should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            LineaPresupuesto(
                descripcion="Test",
                cantidad=10.0,
                precio_unitario=float("nan"),
            )
        assert "finito" in str(exc_info.value).lower() or "nan" in str(exc_info.value).lower()

    def test_precio_unitario_rejects_infinity(self):
        """Infinite price should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            LineaPresupuesto(
                descripcion="Test",
                cantidad=10.0,
                precio_unitario=float("inf"),
            )
        assert "finito" in str(exc_info.value).lower() or "infinity" in str(exc_info.value).lower()

    def test_precio_unitario_rejects_negative_infinity(self):
        """Negative infinite price should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            LineaPresupuesto(
                descripcion="Test",
                cantidad=10.0,
                precio_unitario=float("-inf"),
            )
        assert "finito" in str(exc_info.value).lower()

    def test_precio_unitario_rejects_above_max(self):
        """Price above 1M should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            LineaPresupuesto(
                descripcion="Test",
                cantidad=10.0,
                precio_unitario=1_000_001.0,
            )
        assert "máximo" in str(exc_info.value).lower()

    def test_cantidad_finite_accepts_positive(self):
        """Valid positive quantity should be accepted."""
        linea = LineaPresupuesto(
            descripcion="Test",
            cantidad=100.5,
            precio_unitario=50.0,
        )
        assert linea.cantidad == 100.5

    def test_cantidad_accepts_none(self):
        """None quantity should be accepted (for backward compat)."""
        linea = LineaPresupuesto(
            descripcion="Test",
            cantidad=None,
            precio_unitario=50.0,
        )
        assert linea.cantidad is None

    def test_cantidad_rejects_nan(self):
        """NaN quantity should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            LineaPresupuesto(
                descripcion="Test",
                cantidad=float("nan"),
                precio_unitario=50.0,
            )
        assert "finito" in str(exc_info.value).lower()

    def test_cantidad_rejects_infinity(self):
        """Infinite quantity should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            LineaPresupuesto(
                descripcion="Test",
                cantidad=float("inf"),
                precio_unitario=50.0,
            )
        assert "finito" in str(exc_info.value).lower()

    def test_cantidad_rejects_above_max(self):
        """Quantity above 1M should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            LineaPresupuesto(
                descripcion="Test",
                cantidad=1_000_001.0,
                precio_unitario=50.0,
            )
        assert "máximo" in str(exc_info.value).lower()

    def test_descripcion_max_length(self):
        """Descripcion > 500 chars should be rejected."""
        long_desc = "x" * 501
        with pytest.raises(ValidationError) as exc_info:
            LineaPresupuesto(
                descripcion=long_desc,
                cantidad=10.0,
                precio_unitario=50.0,
            )
        assert "500" in str(exc_info.value)

    def test_unidad_max_length(self):
        """Unidad > 50 chars should be rejected."""
        long_unidad = "x" * 51
        with pytest.raises(ValidationError) as exc_info:
            LineaPresupuesto(
                descripcion="Test",
                cantidad=10.0,
                precio_unitario=50.0,
                unidad=long_unidad,
            )
        assert "50" in str(exc_info.value)

    def test_extra_fields_forbid(self):
        """Extra fields should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            LineaPresupuesto(
                descripcion="Test",
                cantidad=10.0,
                precio_unitario=50.0,
                extra_field="should fail",
            )
        assert "extra" in str(exc_info.value).lower()


class TestBudgetImportRequestValidation:
    """Test BudgetImportRequest input validation."""

    def test_extra_fields_forbid(self):
        """Extra fields in request should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            BudgetImportRequest(
                filename="test.xlsx",
                file_hash="a" * 64,
                building_type="residencial",
                lineas=[
                    LineaPresupuesto(
                        descripcion="Test",
                        cantidad=10.0,
                        precio_unitario=50.0,
                    )
                ],
                extra_field="should fail",
            )
        assert "extra" in str(exc_info.value).lower()

    def test_filename_max_length(self):
        """Filename > 500 chars should be rejected."""
        long_filename = "x" * 501
        with pytest.raises(ValidationError) as exc_info:
            BudgetImportRequest(
                filename=long_filename,
                file_hash="a" * 64,
                building_type="residencial",
                lineas=[
                    LineaPresupuesto(
                        descripcion="Test",
                        cantidad=10.0,
                        precio_unitario=50.0,
                    )
                ],
            )
        assert "500" in str(exc_info.value)

    def test_building_type_max_length(self):
        """Building_type > 100 chars should be rejected."""
        long_building = "x" * 101
        with pytest.raises(ValidationError) as exc_info:
            BudgetImportRequest(
                filename="test.xlsx",
                file_hash="a" * 64,
                building_type=long_building,
                lineas=[
                    LineaPresupuesto(
                        descripcion="Test",
                        cantidad=10.0,
                        precio_unitario=50.0,
                    )
                ],
            )
        assert "100" in str(exc_info.value)

    def test_valid_request_accepted(self):
        """Valid request should be accepted."""
        request = BudgetImportRequest(
            filename="test.xlsx",
            file_hash="a" * 64,
            building_type="residencial",
            lineas=[
                LineaPresupuesto(
                    descripcion="Test item",
                    cantidad=10.0,
                    precio_unitario=50.0,
                )
            ],
        )
        assert request.filename == "test.xlsx"
        assert len(request.lineas) == 1
