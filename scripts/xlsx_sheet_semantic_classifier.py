"""Semantic sheet classification for adaptive professional XLSX review views."""

from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata
from typing import Any


SHEET_BUDGET_CLASSIC = "BUDGET_CLASSIC"
SHEET_BUDGET_SUMMARY = "BUDGET_SUMMARY"
SHEET_SPACE_BREAKDOWN = "SPACE_BREAKDOWN"
SHEET_COMPARISON_TABLE = "COMPARISON_TABLE"
SHEET_FORMULA_CALCULATION = "FORMULA_CALCULATION_SHEET"
SHEET_AUXILIARY = "AUXILIARY_SHEET"
SHEET_METADATA = "METADATA_SHEET"
SHEET_UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class SheetSemanticClassification:
    sheet_name: str
    sheet_type: str
    confidence: str
    reasons: tuple[str, ...]
    warnings: tuple[str, ...]
    header_row: int
    detected_columns: dict[str, int]


def _norm(value: object) -> str:
    text = "" if value is None else str(value).strip().lower()
    text = "".join(ch for ch in unicodedata.normalize("NFD", text) if unicodedata.category(ch) != "Mn")
    text = text.replace("\n", " ").replace("\r", " ")
    text = re.sub(r"[^\w\s€()./-]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _header_field(normalized_header: str) -> str:
    if not normalized_header:
        return ""
    if normalized_header in {"cap", "cap.", "capitulo", "capitulo codigo", "codigo capitulo"}:
        return "cap"
    if "nombre del capitulo" in normalized_header or "capitulo nombre" in normalized_header:
        return "chapter_name"
    if "nombre equivalente" in normalized_header:
        return "equivalent_name"
    if "importe equivalente" in normalized_header or "presupuesto equivalente" in normalized_header:
        return "equivalent_amount"
    if "diferencia" in normalized_header:
        return "difference"
    if normalized_header.startswith("codigo") or normalized_header in {"cod", "ref", "referencia", "partida"}:
        return "code"
    if any(token in normalized_header for token in ("descripcion", "concepto", "detalle", "resumen", "nombre")):
        return "description"
    if normalized_header in {"ud", "uds", "unidad", "unidades", "unit"}:
        return "unit"
    if any(token in normalized_header for token in ("cantidad", "medicion", "medicion", "qty", "quantity")):
        return "quantity"
    if any(token in normalized_header for token in ("precio unitario", "precio ud", "p unitario", "unit price", "precio")):
        return "unit_price"
    if normalized_header in {"pres", "pres(*)", "presupuesto"}:
        return "amount"
    if any(token in normalized_header for token in ("importe", "presupuesto", "coste", "total", "amount")):
        return "amount"
    if normalized_header.startswith("info"):
        return "info"
    if "formula" in normalized_header or "ratio" in normalized_header:
        return "formula"
    return ""


def _detect_header_row_and_columns(ws: object, max_scan_rows: int = 35) -> tuple[int, dict[str, int], int]:
    max_row = min(getattr(ws, "max_row", 1), max_scan_rows)
    max_col = min(getattr(ws, "max_column", 1), 40)
    best_row = 1
    best_columns: dict[str, int] = {}
    best_score = -1
    for row_idx in range(1, max_row + 1):
        row_columns: dict[str, int] = {}
        score = 0
        for col_idx in range(1, max_col + 1):
            header = _norm(ws.cell(row=row_idx, column=col_idx).value)
            field = _header_field(header)
            if not field:
                continue
            if field not in row_columns:
                row_columns[field] = col_idx
            score += 2
        if {"description", "amount"} <= set(row_columns):
            score += 4
        if {"cap", "chapter_name", "amount"} <= set(row_columns):
            score += 5
        if {"equivalent_name", "equivalent_amount", "difference"} <= set(row_columns):
            score += 6
        if score > best_score:
            best_row = row_idx
            best_columns = row_columns
            best_score = score
    return best_row, best_columns, max(best_score, 0)


def _formula_density(ws: object, sample_rows: int = 120, sample_cols: int = 16) -> float:
    max_row = min(getattr(ws, "max_row", 1), sample_rows)
    max_col = min(getattr(ws, "max_column", 1), sample_cols)
    formula_cells = 0
    nonempty = 0
    for row_idx in range(1, max_row + 1):
        for col_idx in range(1, max_col + 1):
            value = ws.cell(row=row_idx, column=col_idx).value
            if value in ("", None):
                continue
            nonempty += 1
            if isinstance(value, str) and value.strip().startswith("="):
                formula_cells += 1
    if nonempty == 0:
        return 0.0
    return formula_cells / nonempty


def _looks_numeric(value: object) -> bool:
    text = _norm(value).replace(" ", "")
    if not text:
        return False
    if re.fullmatch(r"-?\d+(?:[.,]\d+)?", text):
        return True
    return False


def _looks_code(value: object) -> bool:
    text = _norm(value)
    if not text:
        return False
    if re.fullmatch(r"[a-z0-9_.-]{1,40}", text) and re.search(r"[a-z]", text):
        return True
    if re.fullmatch(r"\d+(?:[.-]\d+)*", text):
        return True
    return False


def _structural_profile(ws: object, scan_rows: int = 45) -> dict[str, int]:
    max_row = min(getattr(ws, "max_row", 1), scan_rows)
    hits_summary = 0
    hits_space = 0
    hits_comparison = 0
    for row_idx in range(1, max_row + 1):
        c1 = ws.cell(row=row_idx, column=1).value
        c2 = ws.cell(row=row_idx, column=2).value
        c3 = ws.cell(row=row_idx, column=3).value
        c4 = ws.cell(row=row_idx, column=4).value
        c5 = ws.cell(row=row_idx, column=5).value
        c6 = ws.cell(row=row_idx, column=6).value
        c7 = ws.cell(row=row_idx, column=7).value
        c8 = ws.cell(row=row_idx, column=8).value
        if _looks_code(c1) and re.search(r"[a-z]", _norm(c2)) and _looks_numeric(c4):
            hits_summary += 1
        if re.search(r"[a-z]", _norm(c1)) and re.search(r"[a-z]", _norm(c3)) and _looks_numeric(c4):
            hits_space += 1
        if _looks_code(c4) and re.search(r"[a-z]", _norm(c5)) and _looks_numeric(c6) and re.search(r"[a-z]", _norm(c7)) and _looks_numeric(c8):
            hits_comparison += 1
    return {
        "summary": hits_summary,
        "space": hits_space,
        "comparison": hits_comparison,
    }


def _infer_comparison_columns_from_rows(ws: object) -> dict[str, int]:
    max_row = min(getattr(ws, "max_row", 1), 60)
    max_col = min(getattr(ws, "max_column", 1), 30)
    for row_idx in range(1, max_row + 1):
        for start in range(1, max_col - 4):
            c1 = ws.cell(row=row_idx, column=start).value
            c2 = ws.cell(row=row_idx, column=start + 1).value
            c3 = ws.cell(row=row_idx, column=start + 2).value
            c4 = ws.cell(row=row_idx, column=start + 3).value
            c5 = ws.cell(row=row_idx, column=start + 4).value
            c6 = ws.cell(row=row_idx, column=start + 5).value
            if not (_looks_code(c1) and re.search(r"[a-z]", _norm(c2)) and _looks_numeric(c3)):
                continue
            if not (re.search(r"[a-z]", _norm(c4)) and _looks_numeric(c5)):
                continue
            c6_raw = "" if c6 is None else str(c6).strip()
            if not c6_raw.startswith("=") and not _looks_numeric(c6):
                continue
            return {
                "cap": start,
                "chapter_name": start + 1,
                "amount": start + 2,
                "equivalent_name": start + 3,
                "equivalent_amount": start + 4,
                "difference": start + 5,
            }
    return {}


def _infer_summary_columns_from_rows(ws: object) -> dict[str, int]:
    max_row = min(getattr(ws, "max_row", 1), 60)
    for row_idx in range(1, max_row + 1):
        c1 = ws.cell(row=row_idx, column=1).value
        c2 = ws.cell(row=row_idx, column=2).value
        c3 = ws.cell(row=row_idx, column=3).value
        c4 = ws.cell(row=row_idx, column=4).value
        if _looks_code(c1) and re.search(r"[a-z]", _norm(c2)) and _looks_numeric(c4):
            mapping = {"code": 1, "description": 2, "amount": 4}
            if isinstance(c3, str) and c3.strip().startswith("="):
                mapping["formula"] = 3
            return mapping
    return {}


def _infer_space_columns_from_rows(ws: object) -> dict[str, int]:
    max_row = min(getattr(ws, "max_row", 1), 60)
    for row_idx in range(1, max_row + 1):
        c1 = ws.cell(row=row_idx, column=1).value
        c3 = ws.cell(row=row_idx, column=3).value
        c4 = ws.cell(row=row_idx, column=4).value
        if re.search(r"[a-z]", _norm(c1)) and re.search(r"[a-z]", _norm(c3)) and _looks_numeric(c4):
            return {"code": 1, "info": 2, "description": 3, "amount": 4}
    return {}


def classify_worksheet_semantics(ws: object) -> SheetSemanticClassification:
    header_row, detected, score = _detect_header_row_and_columns(ws)
    reasons: list[str] = []
    warnings: list[str] = []
    sheet_type = SHEET_UNKNOWN
    confidence = "LOW"
    name_hint = _norm(getattr(ws, "title", ""))
    formula_density = _formula_density(ws)
    structural = _structural_profile(ws)

    if {"cap", "chapter_name", "amount", "equivalent_name", "equivalent_amount", "difference"} <= set(detected):
        sheet_type = SHEET_COMPARISON_TABLE
        confidence = "HIGH"
        reasons.append("comparison_columns_detected")
    elif structural["comparison"] >= 3:
        detected = {**_infer_comparison_columns_from_rows(ws), **detected}
        sheet_type = SHEET_COMPARISON_TABLE
        confidence = "MEDIUM"
        reasons.append("comparison_structural_pattern_detected")
    elif (
        {"code", "description", "amount"} <= set(detected)
        and any(field in detected for field in ("unit", "quantity", "unit_price"))
    ):
        sheet_type = SHEET_BUDGET_CLASSIC
        confidence = "HIGH"
        reasons.append("classic_budget_columns_detected")
    elif {"code", "info", "description"} <= set(detected) and "amount" in detected:
        sheet_type = SHEET_SPACE_BREAKDOWN
        confidence = "HIGH"
        reasons.append("space_breakdown_columns_detected")
    elif "espacio" in name_hint and {"code", "description"} <= set(detected):
        sheet_type = SHEET_SPACE_BREAKDOWN
        confidence = "MEDIUM"
        reasons.append("space_sheet_name_hint")
    elif {"code", "description", "amount"} <= set(detected):
        if "formula" in detected or formula_density >= 0.15:
            sheet_type = SHEET_BUDGET_SUMMARY
            confidence = "HIGH"
            reasons.append("summary_budget_columns_detected")
        else:
            sheet_type = SHEET_BUDGET_SUMMARY
            confidence = "MEDIUM"
            reasons.append("summary_budget_columns_inferred")
            warnings.append("economic_header_low_confidence")
    elif structural["summary"] >= 3:
        detected = {**_infer_summary_columns_from_rows(ws), **detected}
        sheet_type = SHEET_BUDGET_SUMMARY
        confidence = "MEDIUM"
        reasons.append("summary_structural_pattern_detected")
        warnings.append("economic_header_low_confidence")
    elif structural["space"] >= 3 and formula_density < 0.2:
        detected = {**_infer_space_columns_from_rows(ws), **detected}
        sheet_type = SHEET_SPACE_BREAKDOWN
        confidence = "LOW"
        reasons.append("space_structural_pattern_detected")
    elif formula_density >= 0.35:
        sheet_type = SHEET_FORMULA_CALCULATION
        confidence = "MEDIUM"
        reasons.append("formula_density_high")
    elif score <= 2 and getattr(ws, "max_row", 0) <= 10:
        sheet_type = SHEET_METADATA
        confidence = "LOW"
        reasons.append("metadata_shape_detected")
    elif score >= 3:
        sheet_type = SHEET_AUXILIARY
        confidence = "LOW"
        reasons.append("tabular_auxiliary_shape_detected")
    else:
        sheet_type = SHEET_UNKNOWN
        confidence = "LOW"
        reasons.append("insufficient_semantic_evidence")
        warnings.append("MANUAL_REVIEW_REQUIRED")

    if sheet_type in {SHEET_UNKNOWN, SHEET_AUXILIARY, SHEET_METADATA}:
        warnings.append("MANUAL_REVIEW_REQUIRED")

    return SheetSemanticClassification(
        sheet_name=str(getattr(ws, "title", "")),
        sheet_type=sheet_type,
        confidence=confidence,
        reasons=tuple(dict.fromkeys(reasons)),
        warnings=tuple(dict.fromkeys(warnings)),
        header_row=header_row,
        detected_columns=detected,
    )
