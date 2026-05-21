from scripts.xlsx_formula_translation import (
    STATUS_PRESERVED_AS_TEXT,
    STATUS_TRANSLATED_FORMULA,
    formula_references_missing_defined_names,
    translate_formula_for_review_view,
)


def test_comparison_formula_translates_to_view_coordinates():
    result = translate_formula_for_review_view(
        sheet_type="COMPARISON_TABLE",
        formula_text="=+H4-F4",
        amount_value="",
        defined_names=set(),
        row_number=5,
        amount_col_letter="C",
        equivalent_col_letter="E",
    )
    assert result.status == STATUS_TRANSLATED_FORMULA
    assert result.output_value == "=E5-C5"
    assert result.is_formula is True


def test_summary_formula_with_missing_defined_name_is_preserved_as_text():
    result = translate_formula_for_review_view(
        sheet_type="BUDGET_SUMMARY",
        formula_text="=PEM*PorGasGen",
        amount_value="",
        defined_names={"TOTAL"},
    )
    assert result.status == STATUS_PRESERVED_AS_TEXT
    assert result.output_value.startswith("formula_preserved_as_text:")
    assert result.is_formula is False


def test_formula_reference_guard_detects_missing_defined_name():
    assert formula_references_missing_defined_names("=PEM*PorGasGen", {"PEM"}) is True
    assert formula_references_missing_defined_names("=SUM(C5:C8)", set()) is False
