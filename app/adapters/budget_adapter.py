"""Adapter for converting various budget formats to standard BudgetImportRequest."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.schemas.import_budgets import BudgetImportRequest, LineaPresupuesto

logger = logging.getLogger(__name__)

# Field mapping patterns for flexible input
FIELD_ALIASES = {
    # descripcion variations
    "descripcion": ["descripcion", "description", "nombre", "name", "item", "partida", "concepto"],
    # cantidad variations
    "cantidad": ["cantidad", "quantity", "qty", "amount", "count"],
    # precio_unitario variations
    "precio_unitario": [
        "precio_unitario",
        "price_unit",
        "unit_price",
        "precio",
        "price",
        "unit_cost",
        "valor_unitario",
    ],
    # unidad variations
    "unidad": ["unidad", "unit", "u", "uom"],
    # capitulo variations
    "capitulo": ["capitulo", "chapter", "section", "codigo", "code", "category"],
    # numero variations
    "numero": ["numero", "number", "num", "line", "linea"],
}


class AdapterError(Exception):
    """Exception raised when adaptation fails."""

    pass


def _find_field(raw_dict: Dict[str, Any], aliases: List[str]) -> Optional[str]:
    """
    Find a field in dictionary by checking multiple aliases (case-insensitive).

    Args:
        raw_dict: Dictionary to search in
        aliases: List of possible field names

    Returns:
        The actual field name in the dictionary, or None if not found
    """
    # Lowercase keys for case-insensitive matching
    lower_dict = {k.lower(): k for k in raw_dict.keys()}

    for alias in aliases:
        alias_lower = alias.lower()
        if alias_lower in lower_dict:
            return lower_dict[alias_lower]

    return None


def _extract_value(raw_dict: Dict[str, Any], aliases: List[str], default: Any = None) -> Any:
    """Extract a value from dictionary by trying multiple field aliases."""
    field_name = _find_field(raw_dict, aliases)
    if field_name is not None:
        return raw_dict[field_name]
    return default


def adapt_linea(raw_linea: Dict[str, Any]) -> LineaPresupuesto:
    """
    Adapt a single line item from flexible format to standard LineaPresupuesto.

    Args:
        raw_linea: Dictionary with possibly non-standard field names

    Returns:
        LineaPresupuesto with standardized field names

    Raises:
        AdapterError: If critical fields are missing
    """
    # Extract required fields
    descripcion = _extract_value(raw_linea, FIELD_ALIASES["descripcion"])
    if descripcion is None:
        raise AdapterError("Campo requerido 'descripcion' (o alias: description, nombre, name) no encontrado")
    # Note: Empty descripcion is allowed here; import_service will omit empty descriptions during processing

    cantidad = _extract_value(raw_linea, FIELD_ALIASES["cantidad"])
    # Note: cantidad can be None; import_service will omit lines with invalid quantities

    precio_unitario = _extract_value(raw_linea, FIELD_ALIASES["precio_unitario"])
    if precio_unitario is None:
        raise AdapterError(
            "Campo requerido 'precio_unitario' (o alias: price_unit, unit_price, precio, price) no encontrado"
        )

    # Extract optional fields with sensible defaults
    unidad = _extract_value(raw_linea, FIELD_ALIASES["unidad"], default="ud")
    numero = _extract_value(raw_linea, FIELD_ALIASES["numero"], default=0)
    capitulo = _extract_value(raw_linea, FIELD_ALIASES["capitulo"], default="")

    try:
        return LineaPresupuesto(
            numero=int(numero) if numero is not None else 0,
            capitulo=str(capitulo) if capitulo else "",
            descripcion=str(descripcion).strip(),
            cantidad=float(cantidad) if cantidad is not None else None,
            unidad=str(unidad) if unidad else "ud",
            precio_unitario=float(precio_unitario),
        )
    except (ValueError, TypeError) as e:
        raise AdapterError(f"Error al convertir valores numéricos: {e}") from e


def adapt_budget_to_standard(
    raw_input: Dict[str, Any] | List[Dict[str, Any]],
    format_hint: str = "auto",
) -> BudgetImportRequest:
    """
    Adapt budget input in flexible format to standard BudgetImportRequest.

    Supports various field naming conventions and structures. Attempts to detect
    and map non-standard field names to standard ones.

    Args:
        raw_input: Budget data in flexible format. Can be:
            - Dict with 'lineas' key containing list of line items
            - Dict without 'lineas' (treated as single line item)
            - Direct list of line items
        format_hint: Hint for format detection ("auto", "json", "csv", etc.)

    Returns:
        BudgetImportRequest with standardized structure

    Raises:
        AdapterError: If critical fields are missing or cannot be mapped

    Examples:
        >>> # Standard format (no adaptation needed)
        >>> data = {
        ...     "filename": "presupuesto.xlsx",
        ...     "file_hash": "a" * 64,
        ...     "building_type": "residencial",
        ...     "lineas": [{"descripcion": "Item", "cantidad": 10, "precio_unitario": 100}]
        ... }
        >>> req = adapt_budget_to_standard(data)

        >>> # Non-standard field names (adapted)
        >>> data = {
        ...     "filename": "presupuesto.xlsx",
        ...     "file_hash": "a" * 64,
        ...     "building_type": "residencial",
        ...     "lineas": [{"name": "Item", "qty": 10, "price": 100}]
        ... }
        >>> req = adapt_budget_to_standard(data)
    """
    if isinstance(raw_input, list):
        # If input is a list of lines directly, wrap it
        raw_input = {"lineas": raw_input}

    if not isinstance(raw_input, dict):
        raise AdapterError(
            f"Presupuesto debe ser un diccionario o lista, recibido: {type(raw_input).__name__}"
        )

    # Extract top-level fields (these are usually standard)
    filename = raw_input.get("filename", "presupuesto_sin_nombre.json")
    file_hash = raw_input.get("file_hash")
    building_type = raw_input.get("building_type", "residencial")

    if not file_hash:
        raise AdapterError("Campo requerido 'file_hash' no encontrado")

    # Extract lines
    lineas_raw = raw_input.get("lineas")

    if lineas_raw is None:
        # Try to detect if the whole dict is a single line item
        # (if it has descripcion/cantidad/precio_unitario-like fields)
        try:
            single_linea = adapt_linea(raw_input)
            lineas_raw = [single_linea]
        except AdapterError:
            raise AdapterError(
                "Campo requerido 'lineas' no encontrado y estructura no es una línea válida"
            )
    elif not isinstance(lineas_raw, list):
        raise AdapterError(f"'lineas' debe ser una lista, recibido: {type(lineas_raw).__name__}")

    if not lineas_raw:
        raise AdapterError("'lineas' no puede estar vacío")

    # Adapt each line item
    adapted_lineas: List[LineaPresupuesto] = []
    for i, raw_linea in enumerate(lineas_raw):
        if not isinstance(raw_linea, dict):
            raise AdapterError(f"Línea {i} no es un diccionario: {type(raw_linea).__name__}")

        try:
            adapted_linea = adapt_linea(raw_linea)
            adapted_lineas.append(adapted_linea)
        except AdapterError as e:
            raise AdapterError(f"Error en línea {i}: {e}") from e

    # Create standard request
    try:
        return BudgetImportRequest(
            filename=filename,
            file_hash=file_hash,
            building_type=building_type,
            lineas=adapted_lineas,
        )
    except Exception as e:
        raise AdapterError(f"Error al crear BudgetImportRequest: {e}") from e
