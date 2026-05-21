from openpyxl import Workbook

from scripts.xlsx_sheet_semantic_classifier import (
    SHEET_AUXILIARY,
    SHEET_BUDGET_CLASSIC,
    SHEET_BUDGET_SUMMARY,
    SHEET_COMPARISON_TABLE,
    SHEET_FORMULA_CALCULATION,
    SHEET_METADATA,
    SHEET_SPACE_BREAKDOWN,
    SHEET_UNKNOWN,
    classify_worksheet_semantics,
)


def _ws(headers: list[str], rows: list[list[object]] | None = None, title: str = "Sheet") -> object:
    wb = Workbook()
    ws = wb.active
    ws.title = title
    ws.append(headers)
    for row in rows or []:
        ws.append(row)
    return ws


def test_classifier_detects_budget_classic():
    ws = _ws(["Codigo", "Descripcion", "Ud", "Cantidad", "Precio unitario", "Importe"], [["1.1", "Partida", "m2", 2, 5, 10]])
    result = classify_worksheet_semantics(ws)
    assert result.sheet_type == SHEET_BUDGET_CLASSIC


def test_classifier_detects_budget_summary():
    ws = _ws(["Codigo", "Descripcion", "Formula", "Importe"], [["LUV_AP", "EQUIPAMIENTO", "=D2/PEM", 37297.09]])
    result = classify_worksheet_semantics(ws)
    assert result.sheet_type == SHEET_BUDGET_SUMMARY


def test_classifier_detects_space_breakdown():
    ws = _ws(["Código", "Info", "Resumen", "Pres"], [["COCINA", "", "COCINA", 1000]], title="Espacios")
    result = classify_worksheet_semantics(ws)
    assert result.sheet_type == SHEET_SPACE_BREAKDOWN


def test_classifier_detects_comparison_table():
    ws = _ws(
        ["Cap.", "Nombre del capítulo", "Importe (€)", "Nombre equivalente", "Importe equivalente", "Diferencia"],
        [[2, "Demoliciones", 687.5, "DEMOLICIONES", 550, "=E2-C2"]],
    )
    result = classify_worksheet_semantics(ws)
    assert result.sheet_type == SHEET_COMPARISON_TABLE


def test_classifier_detects_formula_sheet():
    ws = _ws(["Campo A", "Campo B"], [["=PEM*PorHonPry", "=A2*0.2"], ["=A3*0.3", "=B3*2"]])
    result = classify_worksheet_semantics(ws)
    assert result.sheet_type == SHEET_FORMULA_CALCULATION


def test_classifier_returns_unknown_or_aux_when_insufficient_evidence():
    ws = _ws(["x", "y"], [[None, None], ["foo", "bar"]])
    result = classify_worksheet_semantics(ws)
    assert result.sheet_type in {SHEET_UNKNOWN, SHEET_AUXILIARY, SHEET_METADATA}
