from openpyxl import Workbook

from scripts.xlsx_budget_detection import (
    ROW_AMBIGUOUS,
    ROW_CHAPTER,
    ROW_COST_ITEM,
    ROW_EMPTY,
    ROW_HEADER,
    ROW_SUBTOTAL,
    ROW_TOTAL,
    classify_budget_row,
    detect_header_row_and_mapping,
    parse_budget_number,
)


def _workbook_with_header(headers: list[str]) -> Workbook:
    wb = Workbook()
    ws = wb.active
    ws.title = "Synthetic"
    ws.append(["intro"])
    ws.append(headers)
    ws.append(["1.1", "Texto sintetico", "Linea sintetica", "m2", 2, 10, 20])
    return wb


def test_detects_economic_header_variants():
    cases = [
        ("Importe", "amount"),
        ("Importe Total", "amount"),
        ("Total", "amount"),
        ("Precio unitario", "unit_price"),
        ("P. Unitario", "unit_price"),
        ("Medición", "quantity"),
        ("Cantidad", "quantity"),
        ("Ud.", "unit"),
        ("Descripción", "item_description"),
        ("Concepto", "item_description"),
    ]
    for label, field in cases:
        wb = _workbook_with_header(["Codigo", "Concepto", label])
        try:
            ws = wb.active
            detection = detect_header_row_and_mapping(ws)
            assert detection.header_row == 2
            assert field in detection.mapping
        finally:
            wb.close()


def test_detects_headers_with_accents_newlines_and_uppercase():
    wb = _workbook_with_header(["CÓDIGO", "DESCRIPCIÓN\nPARTIDA", "PRECIO\nUNITARIO", "IMPORTE TOTAL"])
    try:
        detection = detect_header_row_and_mapping(wb.active)
        assert detection.mapping["item_code"] == 1
        assert detection.mapping["item_description"] == 2
        assert detection.mapping["unit_price"] == 3
        assert detection.mapping["amount"] == 4
    finally:
        wb.close()


def test_parse_budget_number_common_formats():
    assert parse_budget_number("687.5", "amount").normalized == "687.5"
    assert parse_budget_number("687,50", "amount").normalized == "687.5"
    assert parse_budget_number("1.234,56", "amount").normalized == "1234.56"
    assert parse_budget_number("1 234,56", "amount").normalized == "1234.56"
    assert parse_budget_number("1,234.56", "amount").normalized == "1234.56"
    assert parse_budget_number("€ 1.234,56", "amount").normalized == "1234.56"
    assert parse_budget_number("1.234,56 €", "amount").normalized == "1234.56"
    assert parse_budget_number("(1.234,56)", "amount").normalized == "-1234.56"


def test_parse_budget_number_rejects_codes_and_years_without_context():
    assert not parse_budget_number("1.2.03", "item_code").is_valid
    assert not parse_budget_number("2024").is_valid
    assert parse_budget_number("2024", "amount").normalized == "2024"


def test_classifies_rows_without_promoting_headers_totals_or_empty_rows():
    mapping = {"item_description": 2, "unit": 3, "quantity": 4, "unit_price": 5, "amount": 6}
    assert classify_budget_row(["Codigo", "Descripcion", "Ud", "Cantidad", "Precio", "Importe"], mapping, 1, 1) == ROW_HEADER
    assert classify_budget_row([None, "", None], mapping, 2, 1) == ROW_EMPTY
    assert classify_budget_row(["", "Subtotal capitulo", "", "", "", "100"], mapping, 3, 1) == ROW_SUBTOTAL
    assert classify_budget_row(["", "Total presupuesto", "", "", "", "100"], mapping, 4, 1) == ROW_TOTAL
    assert classify_budget_row(["", "Capitulo preliminares", "", "", "", ""], mapping, 5, 1) == ROW_CHAPTER
    assert classify_budget_row(["", "Partida valida", "ud", "2", "10", "20"], mapping, 6, 1) == ROW_COST_ITEM
    assert classify_budget_row(["", "", "", "", "", "20"], mapping, 7, 1) in {ROW_AMBIGUOUS, "NON_BUDGET_ROW"}
