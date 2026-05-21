"""Safe formula translation policies for adaptive professional review views."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


STATUS_TRANSLATED_FORMULA = "TRANSLATED_FORMULA"
STATUS_PRESERVED_FORMULA = "PRESERVED_FORMULA"
STATUS_PRESERVED_AS_TEXT = "PRESERVED_AS_TEXT"
STATUS_VALUE_ONLY = "VALUE_ONLY"
STATUS_MOVED_TO_TRACE = "MOVED_TO_TRACE"
STATUS_UNSUPPORTED_FORMULA = "UNSUPPORTED_FORMULA"

_CELL_REF_RE = re.compile(r"^\$?[A-Z]{1,3}\$?\d+$")
_RANGE_REF_RE = re.compile(r"^\$?[A-Z]{1,3}\$?\d+:\$?[A-Z]{1,3}\$?\d+$")
_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_\.]*")
_KNOWN_FUNCTIONS = {
    "SUM",
    "AVERAGE",
    "MIN",
    "MAX",
    "ABS",
    "ROUND",
    "IF",
    "AND",
    "OR",
    "NOT",
    "VLOOKUP",
    "XLOOKUP",
    "INDEX",
    "MATCH",
    "COUNT",
    "COUNTA",
    "SUMIF",
    "SUMIFS",
    "IFERROR",
    "LEFT",
    "RIGHT",
    "MID",
    "CONCAT",
    "CONCATENATE",
    "TEXT",
    "VALUE",
    "INT",
}


@dataclass(frozen=True)
class FormulaTranslationResult:
    status: str
    output_value: str
    trace_note: str
    is_formula: bool


def extract_defined_names(workbook: Any) -> set[str]:
    names: set[str] = set()
    defined = getattr(workbook, "defined_names", None)
    if defined is None:
        return names
    # openpyxl compatibility: defined_names.definedName list or mapping-like API
    if hasattr(defined, "definedName"):
        for item in getattr(defined, "definedName", []):
            name = str(getattr(item, "name", "")).strip()
            if name:
                names.add(name.upper())
        return names
    values = []
    try:
        values = list(defined.values())
    except Exception:
        values = []
    for item in values:
        name = str(getattr(item, "name", "")).strip()
        if name:
            names.add(name.upper())
    return names


def _formula_tokens(formula: str) -> set[str]:
    return {token.upper() for token in _TOKEN_RE.findall(formula)}


def _is_cell_or_range_token(token: str) -> bool:
    return bool(_CELL_REF_RE.fullmatch(token) or _RANGE_REF_RE.fullmatch(token))


def _has_missing_defined_names(formula: str, defined_names: set[str]) -> bool:
    body = formula.lstrip("=")
    for token in _formula_tokens(body):
        if token in _KNOWN_FUNCTIONS:
            continue
        if _is_cell_or_range_token(token):
            continue
        if token in {"TRUE", "FALSE"}:
            continue
        # Cross-sheet refs are not translated as active formulas in review views.
        if "!" in token:
            return True
        if token not in defined_names:
            return True
    return False


def formula_references_missing_defined_names(formula: str, defined_names: set[str]) -> bool:
    text = (formula or "").strip()
    if not text.startswith("="):
        return False
    return _has_missing_defined_names(text, defined_names)


def _as_text_formula(formula: str) -> str:
    clean = formula.strip()
    return f"formula_preserved_as_text: {clean}"


def translate_formula_for_review_view(
    sheet_type: str,
    formula_text: str,
    amount_value: str,
    defined_names: set[str],
    row_number: int | None = None,
    amount_col_letter: str = "C",
    equivalent_col_letter: str = "E",
) -> FormulaTranslationResult:
    formula = (formula_text or "").strip()
    if not formula:
        return FormulaTranslationResult(
            status=STATUS_VALUE_ONLY,
            output_value=amount_value,
            trace_note="VALUE_ONLY",
            is_formula=False,
        )

    # COMPARISON_TABLE: never reuse inherited formulas with old coordinates.
    if sheet_type == "COMPARISON_TABLE":
        if row_number is None:
            if amount_value:
                return FormulaTranslationResult(
                    status=STATUS_VALUE_ONLY,
                    output_value=amount_value,
                    trace_note="COMPARISON_FORMULA_TRANSLATION_ROW_MISSING|VALUE_ONLY",
                    is_formula=False,
                )
            return FormulaTranslationResult(
                status=STATUS_UNSUPPORTED_FORMULA,
                output_value=_as_text_formula(formula),
                trace_note="COMPARISON_FORMULA_TRANSLATION_ROW_MISSING|FORMULA_PRESERVED_AS_TEXT",
                is_formula=False,
            )
        translated = f"={equivalent_col_letter}{row_number}-{amount_col_letter}{row_number}"
        return FormulaTranslationResult(
            status=STATUS_TRANSLATED_FORMULA,
            output_value=translated,
            trace_note=f"COMPARISON_FORMULA_TRANSLATED:{translated}",
            is_formula=True,
        )

    # For summary/classic/space views we only keep active formulas if they are safe.
    if not formula.startswith("="):
        return FormulaTranslationResult(
            status=STATUS_PRESERVED_AS_TEXT,
            output_value=formula,
            trace_note="FORMULA_NOT_ACTIVE_TEXT",
            is_formula=False,
        )

    if _has_missing_defined_names(formula, defined_names):
        return FormulaTranslationResult(
            status=STATUS_PRESERVED_AS_TEXT,
            output_value=_as_text_formula(formula),
            trace_note="MISSING_DEFINED_NAME|FORMULA_PRESERVED_AS_TEXT",
            is_formula=False,
        )

    # Guardrail: avoid carrying formulas that reference foreign worksheets.
    if "!" in formula:
        return FormulaTranslationResult(
            status=STATUS_MOVED_TO_TRACE,
            output_value=_as_text_formula(formula),
            trace_note="CROSS_SHEET_FORMULA_NOT_TRANSLATED|FORMULA_PRESERVED_AS_TEXT",
            is_formula=False,
        )

    return FormulaTranslationResult(
        status=STATUS_PRESERVED_FORMULA,
        output_value=formula,
        trace_note="FORMULA_PRESERVED_ACTIVE",
        is_formula=True,
    )
