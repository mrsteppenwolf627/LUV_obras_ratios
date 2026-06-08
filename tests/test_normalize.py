"""Unit tests for app.services.items_service.normalize_item_key."""

import pytest
from app.services.items_service import normalize_item_key


def test_normalize_lowercase():
    assert normalize_item_key("CARPINTERÍA") == "carpinteria"


def test_normalize_multiple_spaces():
    assert normalize_item_key("Espacio   múltiple") == "espacio multiple"


def test_normalize_accents():
    assert normalize_item_key("Pintura Café Gris") == "pintura cafe gris"


def test_normalize_idempotent():
    x = "CARPINTERÍA  ALUMINIO"
    once = normalize_item_key(x)
    twice = normalize_item_key(once)
    assert once == twice


def test_normalize_special_chars():
    # Special chars replaced with spaces; adjacent digits stay separate
    result = normalize_item_key("Piso@Cerámico#2.5€")
    # @ → space, # → space, . → space, € → space → "piso ceramico 2 5"
    assert result == "piso ceramico 2 5"
    assert "@" not in result
    assert "#" not in result
    assert "€" not in result


def test_normalize_max_length():
    long_str = "a" * 600
    assert len(normalize_item_key(long_str)) == 500


def test_normalize_edge_cases():
    assert normalize_item_key("") == ""
    assert normalize_item_key("   ") == ""
    assert normalize_item_key(None) == ""  # type: ignore[arg-type]


def test_normalize_keeps_hyphens():
    assert normalize_item_key("Doble Acristalamiento - Premium") == "doble acristalamiento - premium"


def test_normalize_keeps_underscores():
    assert normalize_item_key("item_con_guion_bajo") == "item_con_guion_bajo"


def test_normalize_full_example():
    result = normalize_item_key("CARPINTERÍA  ALUMINIO (DOBLE)")
    assert result == "carpinteria aluminio doble"


def test_normalize_strips_whitespace():
    assert normalize_item_key("   Espacios   múltiples   ") == "espacios multiples"
