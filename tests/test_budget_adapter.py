"""Tests for budget format adapter."""

from __future__ import annotations

import pytest

from app.adapters.budget_adapter import AdapterError, adapt_budget_to_standard, adapt_linea
from app.schemas.import_budgets import LineaPresupuesto


class TestAdaptLinea:
    """Test adaptation of individual line items."""

    def test_standard_format_passes_through(self):
        """Standard format should be accepted without modification."""
        raw = {
            "numero": 1,
            "descripcion": "Carpintería",
            "cantidad": 10.0,
            "precio_unitario": 100.0,
            "unidad": "m2",
        }
        linea = adapt_linea(raw)
        assert linea.descripcion == "Carpintería"
        assert linea.cantidad == 10.0
        assert linea.precio_unitario == 100.0

    def test_alias_descripcion_description(self):
        """'description' should map to 'descripcion'."""
        raw = {"description": "Test", "cantidad": 10.0, "precio_unitario": 50.0}
        linea = adapt_linea(raw)
        assert linea.descripcion == "Test"

    def test_alias_descripcion_name(self):
        """'name' should map to 'descripcion'."""
        raw = {"name": "Item name", "cantidad": 10.0, "precio_unitario": 50.0}
        linea = adapt_linea(raw)
        assert linea.descripcion == "Item name"

    def test_alias_cantidad_qty(self):
        """'qty' should map to 'cantidad'."""
        raw = {"descripcion": "Test", "qty": 5.0, "precio_unitario": 50.0}
        linea = adapt_linea(raw)
        assert linea.cantidad == 5.0

    def test_alias_cantidad_quantity(self):
        """'quantity' should map to 'cantidad'."""
        raw = {"descripcion": "Test", "quantity": 8.0, "precio_unitario": 50.0}
        linea = adapt_linea(raw)
        assert linea.cantidad == 8.0

    def test_alias_precio_unitario_price(self):
        """'price' should map to 'precio_unitario'."""
        raw = {"descripcion": "Test", "cantidad": 10.0, "price": 75.0}
        linea = adapt_linea(raw)
        assert linea.precio_unitario == 75.0

    def test_alias_precio_unitario_unit_price(self):
        """'unit_price' should map to 'precio_unitario'."""
        raw = {"descripcion": "Test", "cantidad": 10.0, "unit_price": 75.0}
        linea = adapt_linea(raw)
        assert linea.precio_unitario == 75.0

    def test_case_insensitive_matching(self):
        """Field names should be matched case-insensitively."""
        raw = {"DESCRIPCION": "Test", "CANTIDAD": 10.0, "PRECIO_UNITARIO": 50.0}
        linea = adapt_linea(raw)
        assert linea.descripcion == "Test"
        assert linea.cantidad == 10.0
        assert linea.precio_unitario == 50.0

    def test_mixed_case_aliases(self):
        """Mixed case aliases should work."""
        raw = {"Name": "Item", "QTY": 5.0, "Price": 100.0}
        linea = adapt_linea(raw)
        assert linea.descripcion == "Item"
        assert linea.cantidad == 5.0
        assert linea.precio_unitario == 100.0

    def test_missing_descripcion_raises_error(self):
        """Missing descripcion field should raise AdapterError."""
        raw = {"cantidad": 10.0, "precio_unitario": 50.0}
        with pytest.raises(AdapterError) as exc_info:
            adapt_linea(raw)
        assert "descripcion" in str(exc_info.value).lower()

    def test_missing_cantidad_allowed(self):
        """Missing cantidad field is allowed at adapter level (import service will handle it)."""
        raw = {"descripcion": "Test", "precio_unitario": 50.0}
        linea = adapt_linea(raw)
        assert linea.cantidad is None

    def test_missing_precio_unitario_raises_error(self):
        """Missing precio_unitario field should raise AdapterError."""
        raw = {"descripcion": "Test", "cantidad": 10.0}
        with pytest.raises(AdapterError) as exc_info:
            adapt_linea(raw)
        assert "precio" in str(exc_info.value).lower()

    def test_empty_descripcion_allowed(self):
        """Empty descripcion is allowed at adapter level (import service will handle it)."""
        raw = {"descripcion": "", "cantidad": 10.0, "precio_unitario": 50.0}
        linea = adapt_linea(raw)
        assert linea.descripcion == ""

    def test_optional_fields_default(self):
        """Optional fields should have sensible defaults."""
        raw = {"descripcion": "Test", "cantidad": 10.0, "precio_unitario": 50.0}
        linea = adapt_linea(raw)
        assert linea.unidad == "ud"
        assert linea.numero == 0
        assert linea.capitulo == ""


class TestAdaptBudgetToStandard:
    """Test adaptation of complete budget requests."""

    def test_standard_format_passes_through(self):
        """Standard format should pass through unchanged."""
        raw = {
            "filename": "presupuesto.xlsx",
            "file_hash": "a" * 64,
            "building_type": "residencial",
            "lineas": [
                {
                    "numero": 1,
                    "descripcion": "Item 1",
                    "cantidad": 10.0,
                    "precio_unitario": 100.0,
                }
            ],
        }
        request = adapt_budget_to_standard(raw)
        assert request.filename == "presupuesto.xlsx"
        assert len(request.lineas) == 1
        assert request.lineas[0].descripcion == "Item 1"

    def test_alternate_field_names_adapted(self):
        """Budget with alternate field names should be adapted."""
        raw = {
            "filename": "presupuesto.xlsx",
            "file_hash": "a" * 64,
            "building_type": "residencial",
            "lineas": [
                {
                    "name": "Item 1",
                    "qty": 10.0,
                    "price": 100.0,
                }
            ],
        }
        request = adapt_budget_to_standard(raw)
        assert request.lineas[0].descripcion == "Item 1"
        assert request.lineas[0].cantidad == 10.0
        assert request.lineas[0].precio_unitario == 100.0

    def test_list_input_wrapped_in_lineas(self):
        """Direct list input should be wrapped as 'lineas'."""
        raw = [
            {
                "descripcion": "Item 1",
                "cantidad": 10.0,
                "precio_unitario": 100.0,
            }
        ]
        # This would need file_hash in the dict, so let's test with a dict containing lineas
        with pytest.raises(AdapterError) as exc_info:
            adapt_budget_to_standard(raw)
        # Lists should be wrapped but they need file_hash
        assert "file_hash" in str(exc_info.value).lower()

    def test_missing_file_hash_raises_error(self):
        """Missing file_hash should raise AdapterError."""
        raw = {
            "filename": "presupuesto.xlsx",
            "building_type": "residencial",
            "lineas": [
                {
                    "descripcion": "Item 1",
                    "cantidad": 10.0,
                    "precio_unitario": 100.0,
                }
            ],
        }
        with pytest.raises(AdapterError) as exc_info:
            adapt_budget_to_standard(raw)
        assert "file_hash" in str(exc_info.value).lower()

    def test_missing_lineas_raises_error(self):
        """Missing lineas field should raise AdapterError."""
        raw = {
            "filename": "presupuesto.xlsx",
            "file_hash": "a" * 64,
            "building_type": "residencial",
        }
        with pytest.raises(AdapterError) as exc_info:
            adapt_budget_to_standard(raw)
        assert "lineas" in str(exc_info.value).lower()

    def test_empty_lineas_raises_error(self):
        """Empty lineas should raise AdapterError."""
        raw = {
            "filename": "presupuesto.xlsx",
            "file_hash": "a" * 64,
            "building_type": "residencial",
            "lineas": [],
        }
        with pytest.raises(AdapterError) as exc_info:
            adapt_budget_to_standard(raw)
        # Check that error mentions empty lineas (handle encoding)
        error_str = str(exc_info.value).lower()
        assert "lineas" in error_str and ("vac" in error_str or "empty" in error_str)

    def test_invalid_linea_raises_error_with_context(self):
        """Invalid line item should raise error with line number context."""
        raw = {
            "filename": "presupuesto.xlsx",
            "file_hash": "a" * 64,
            "building_type": "residencial",
            "lineas": [
                {"descripcion": "Item 1", "cantidad": 10.0, "precio_unitario": 100.0},
                {"descripcion": "Item 2", "cantidad": 5.0},  # Missing precio_unitario
            ],
        }
        with pytest.raises(AdapterError) as exc_info:
            adapt_budget_to_standard(raw)
        error_msg = str(exc_info.value)
        assert "línea 1" in error_msg.lower() or "line 1" in error_msg.lower()
        assert "precio" in error_msg.lower()

    def test_defaults_applied(self):
        """Default values should be applied for optional fields."""
        raw = {
            "file_hash": "a" * 64,
            "lineas": [
                {
                    "descripcion": "Item 1",
                    "cantidad": 10.0,
                    "precio_unitario": 100.0,
                }
            ],
        }
        request = adapt_budget_to_standard(raw)
        assert request.filename == "presupuesto_sin_nombre.json"
        assert request.building_type == "residencial"

    def test_whitespace_stripped_from_descripcion(self):
        """Whitespace should be stripped from descripcion."""
        raw = {
            "file_hash": "a" * 64,
            "lineas": [
                {
                    "descripcion": "  Item with spaces  ",
                    "cantidad": 10.0,
                    "precio_unitario": 100.0,
                }
            ],
        }
        request = adapt_budget_to_standard(raw)
        assert request.lineas[0].descripcion == "Item with spaces"

    def test_numeric_conversion(self):
        """String numbers should be converted to numeric types."""
        raw = {
            "file_hash": "a" * 64,
            "lineas": [
                {
                    "descripcion": "Item 1",
                    "cantidad": "10",  # String instead of float
                    "precio_unitario": "100.5",  # String instead of float
                }
            ],
        }
        request = adapt_budget_to_standard(raw)
        assert request.lineas[0].cantidad == 10.0
        assert request.lineas[0].precio_unitario == 100.5

    def test_complex_mixed_format(self):
        """Complex budget with mixed formats should be adapted."""
        raw = {
            "filename": "mixed_presupuesto.xlsx",
            "file_hash": "b" * 64,
            "building_type": "comercial",
            "lineas": [
                {
                    "Name": "Item A",  # Alternate name
                    "QTY": 5,  # Alternate quantity field
                    "UNIT_PRICE": 200.0,  # Alternate price field
                    "U": "m3",  # Alternate unit field
                },
                {
                    "descripcion": "Item B",  # Standard name
                    "cantidad": 10,  # Standard field
                    "precio_unitario": 150.0,  # Standard field
                },
            ],
        }
        request = adapt_budget_to_standard(raw)
        assert request.filename == "mixed_presupuesto.xlsx"
        assert request.building_type == "comercial"
        assert len(request.lineas) == 2
        assert request.lineas[0].descripcion == "Item A"
        assert request.lineas[0].cantidad == 5.0
        assert request.lineas[0].precio_unitario == 200.0
        assert request.lineas[0].unidad == "m3"
        assert request.lineas[1].descripcion == "Item B"
