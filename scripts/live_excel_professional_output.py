"""Professional human-review budget sheets for PREVIEW_ONLY workbooks."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
import re
from typing import Any
from uuid import uuid4

from openpyxl.styles import Alignment, Font, PatternFill

try:
    from scripts.xlsx_budget_detection import (
        ROW_AMBIGUOUS,
        ROW_CHAPTER,
        ROW_COST_ITEM,
        ROW_NON_BUDGET,
        ROW_SUBCHAPTER,
        ROW_SUBTOTAL,
        ROW_TOTAL,
        BudgetRowExtraction,
    )
except ModuleNotFoundError:
    from xlsx_budget_detection import (  # type: ignore
        ROW_AMBIGUOUS,
        ROW_CHAPTER,
        ROW_COST_ITEM,
        ROW_NON_BUDGET,
        ROW_SUBCHAPTER,
        ROW_SUBTOTAL,
        ROW_TOTAL,
        BudgetRowExtraction,
    )


REVIEW_HEADERS = ["Codigo", "Descripcion", "Ud", "Cantidad", "Precio unitario", "Importe"]
TRACE_HEADERS = [
    "review_row_id",
    "review_sheet_name",
    "review_row_number",
    "row_class",
    "mapping_status",
    "validation_status",
    "source_file_id",
    "import_batch_id",
    "budget_version_id",
    "source_sheet_name",
    "source_row_number",
    "preserved_row_id",
    "cost_item_id",
    "trace_notes",
]


def _next_sequence(workbook: Any, prefix: str) -> int:
    pattern = re.compile(rf"^{re.escape(prefix)}_(\d{{3}})$")
    max_seq = 0
    for name in workbook.sheetnames:
        match = pattern.match(name)
        if match:
            max_seq = max(max_seq, int(match.group(1)))
    return max_seq + 1


def _to_decimal(value: str) -> Decimal | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return Decimal(text)
    except (InvalidOperation, ValueError):
        return None


def _safe_review_text(value: str) -> str:
    text = "" if value is None else str(value).strip()
    if text.startswith("="):
        return f"'{text}"
    return text


def _sum_formula(rows: list[int]) -> str:
    if not rows:
        return ""
    if len(rows) == 1:
        return f"=F{rows[0]}"
    return "=SUM(" + ",".join(f"F{idx}" for idx in rows) + ")"


def _build_preserved_trace_index(workbook: Any, import_batch_id: str) -> dict[tuple[str, str], dict[str, str]]:
    if "PRESERVED_TO_COST_ITEMS_MAP" not in workbook.sheetnames:
        return {}
    ws = workbook["PRESERVED_TO_COST_ITEMS_MAP"]
    headers = [str(ws.cell(row=1, column=idx).value or "").strip() for idx in range(1, ws.max_column + 1)]
    idx = {name: pos + 1 for pos, name in enumerate(headers)}
    required = {"source_sheet_name", "source_row_number", "preserved_row_id", "cost_item_id", "mapping_status", "notes", "import_batch_id"}
    if not required.issubset(idx.keys()):
        return {}
    trace: dict[tuple[str, str], dict[str, str]] = {}
    for row_idx in range(2, ws.max_row + 1):
        row_import_batch_id = str(ws.cell(row=row_idx, column=idx["import_batch_id"]).value or "").strip()
        if row_import_batch_id != import_batch_id:
            continue
        key = (
            str(ws.cell(row=row_idx, column=idx["source_sheet_name"]).value or "").strip(),
            str(ws.cell(row=row_idx, column=idx["source_row_number"]).value or "").strip(),
        )
        if not key[0] or not key[1]:
            continue
        trace[key] = {
            "preserved_row_id": str(ws.cell(row=row_idx, column=idx["preserved_row_id"]).value or "").strip(),
            "cost_item_id": str(ws.cell(row=row_idx, column=idx["cost_item_id"]).value or "").strip(),
            "mapping_status": str(ws.cell(row=row_idx, column=idx["mapping_status"]).value or "").strip(),
            "map_notes": str(ws.cell(row=row_idx, column=idx["notes"]).value or "").strip(),
        }
    return trace


def _apply_visual_style(review_ws: Any) -> None:
    header_fill = PatternFill(fill_type="solid", fgColor="D9E1F2")
    chapter_fill = PatternFill(fill_type="solid", fgColor="E2F0D9")
    subtotal_fill = PatternFill(fill_type="solid", fgColor="FCE4D6")
    total_fill = PatternFill(fill_type="solid", fgColor="D9D9D9")
    ambiguous_fill = PatternFill(fill_type="solid", fgColor="FFF2CC")
    bold = Font(bold=True)

    review_ws.merge_cells("A1:F1")
    review_ws["A1"].font = Font(bold=True, size=14)
    review_ws["A1"].alignment = Alignment(horizontal="left", vertical="center")
    review_ws["A2"].alignment = Alignment(horizontal="left", vertical="center")
    review_ws.row_dimensions[1].height = 22
    review_ws.row_dimensions[2].height = 18

    for col, width in {"A": 14, "B": 64, "C": 8, "D": 12, "E": 16, "F": 16, "G": 2}.items():
        review_ws.column_dimensions[col].width = width
    review_ws.column_dimensions["G"].hidden = True

    for col_idx in range(1, 7):
        cell = review_ws.cell(row=4, column=col_idx)
        cell.font = bold
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
    review_ws.row_dimensions[4].height = 20
    review_ws.freeze_panes = "A5"
    review_ws.auto_filter.ref = "A4:F4"

    for row_idx in range(5, review_ws.max_row + 1):
        code = str(review_ws.cell(row=row_idx, column=1).value or "").strip()
        description = str(review_ws.cell(row=row_idx, column=2).value or "").strip().upper()
        marker = str(review_ws.cell(row=row_idx, column=7).value or "")

        row_fill = None
        row_bold = False
        if marker.startswith("CHAPTER_") or marker.startswith("SUBCHAPTER_"):
            row_fill = chapter_fill
            row_bold = True
        elif marker.startswith("SUBTOTAL_"):
            row_fill = subtotal_fill
            row_bold = True
        elif marker.startswith("TOTAL_") or description.startswith("TOTAL GENERAL"):
            row_fill = total_fill
            row_bold = True
        elif marker.startswith("AMBIGUOUS_"):
            row_fill = ambiguous_fill

        for col_idx in range(1, 7):
            cell = review_ws.cell(row=row_idx, column=col_idx)
            if col_idx == 2:
                cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
            elif col_idx == 3:
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="right", vertical="center")
            if col_idx in {4, 5} and cell.value not in ("", None):
                cell.number_format = "#,##0.00"
            if col_idx == 6 and cell.value not in ("", None):
                cell.number_format = '#,##0.00 "EUR"'
            if row_fill is not None:
                cell.fill = row_fill
            if row_bold:
                cell.font = Font(bold=True)
        if code and len(code) <= 6 and marker.startswith("CHAPTER_"):
            review_ws.row_dimensions[row_idx].height = 20


def append_professional_budget_review(
    workbook: Any,
    extractions: list[BudgetRowExtraction],
    source_file_id: str,
    import_batch_id: str,
    budget_version_id: str,
    mode_label: str = "PREVIEW_ONLY",
) -> dict[str, str]:
    seq = _next_sequence(workbook, "BUDGET_REVIEW")
    review_sheet_name = f"BUDGET_REVIEW_{seq:03d}"
    trace_sheet_name = f"BUDGET_REVIEW_TRACE_{seq:03d}"
    review_ws = workbook.create_sheet(title=review_sheet_name, index=0)
    trace_ws = workbook.create_sheet(title=trace_sheet_name, index=1)

    review_ws["A1"] = "Presupuesto de obra - Revision profesional"
    review_ws["A2"] = f"ID sanitizado: {source_file_id} | Modo: {mode_label}"
    review_ws["A3"] = "Vista humana prioritaria. Trazabilidad tecnica en hoja BUDGET_REVIEW_TRACE_*."

    for col_idx, header in enumerate(REVIEW_HEADERS, start=1):
        review_ws.cell(row=4, column=col_idx, value=header)
    review_ws.cell(row=4, column=7, value="_review_row_id")

    trace_ws.append(TRACE_HEADERS)

    preserved_trace = _build_preserved_trace_index(workbook, import_batch_id=import_batch_id)
    current_row = 5
    current_chapter = ""
    chapter_item_rows: list[int] = []
    all_item_rows: list[int] = []
    subtotal_rows: list[int] = []
    has_input_total = False

    def append_trace(
        review_row_id: str,
        review_row_number: int,
        extraction: BudgetRowExtraction | None,
        row_class: str,
        mapping_status: str,
        notes: str,
    ) -> None:
        source_sheet_name = extraction.source_sheet_name if extraction else ""
        source_row_number = str(extraction.source_row_number) if extraction else ""
        trace_key = (source_sheet_name, source_row_number)
        from_map = preserved_trace.get(trace_key, {})
        validation_status = extraction.validation_status if extraction else "PENDING"
        trace_ws.append(
            [
                review_row_id,
                review_sheet_name,
                str(review_row_number),
                row_class,
                mapping_status or from_map.get("mapping_status", ""),
                validation_status,
                source_file_id,
                import_batch_id,
                budget_version_id,
                source_sheet_name,
                source_row_number,
                from_map.get("preserved_row_id", ""),
                from_map.get("cost_item_id", ""),
                "|".join(part for part in [notes, from_map.get("map_notes", "")] if part),
            ]
        )

    def append_subtotal_row(label: str) -> None:
        nonlocal current_row
        if not chapter_item_rows:
            return
        review_row_id = f"brv_{uuid4().hex[:10]}"
        review_ws.cell(row=current_row, column=2, value=f"Subtotal {label}".strip())
        review_ws.cell(row=current_row, column=6, value=_sum_formula(chapter_item_rows))
        review_ws.cell(row=current_row, column=7, value=f"SUBTOTAL_{review_row_id}")
        append_trace(
            review_row_id=review_row_id,
            review_row_number=current_row,
            extraction=None,
            row_class=ROW_SUBTOTAL,
            mapping_status="NOT_COST_ITEM",
            notes="GENERATED_SUBTOTAL",
        )
        subtotal_rows.append(current_row)
        current_row += 1

    for extraction in extractions:
        row_class = extraction.row_class
        if row_class == ROW_NON_BUDGET:
            continue

        if row_class in {ROW_CHAPTER, ROW_SUBCHAPTER}:
            append_subtotal_row(current_chapter)
            chapter_item_rows = []
            current_chapter = extraction.chapter_name or extraction.item_description

        review_row_id = f"brv_{uuid4().hex[:10]}"
        code = extraction.item_code or extraction.chapter_code
        description = _safe_review_text(extraction.item_description or extraction.chapter_name)
        unit = extraction.unit
        quantity_value = _to_decimal(extraction.quantity)
        unit_price_value = _to_decimal(extraction.unit_price)
        amount_value = _to_decimal(extraction.amount)

        review_ws.cell(row=current_row, column=1, value=code)
        review_ws.cell(row=current_row, column=2, value=description)
        review_ws.cell(row=current_row, column=3, value=unit)
        review_ws.cell(row=current_row, column=4, value=float(quantity_value) if quantity_value is not None else None)
        review_ws.cell(row=current_row, column=5, value=float(unit_price_value) if unit_price_value is not None else None)

        if row_class == ROW_COST_ITEM and quantity_value is not None and unit_price_value is not None:
            review_ws.cell(row=current_row, column=6, value=f"=D{current_row}*E{current_row}")
        elif amount_value is not None:
            review_ws.cell(row=current_row, column=6, value=float(amount_value))

        if row_class == ROW_SUBTOTAL:
            if chapter_item_rows:
                review_ws.cell(row=current_row, column=2, value=description or f"Subtotal {current_chapter}".strip())
                review_ws.cell(row=current_row, column=6, value=_sum_formula(chapter_item_rows))
                chapter_item_rows = []
            elif amount_value is not None:
                review_ws.cell(row=current_row, column=6, value=float(amount_value))
            subtotal_rows.append(current_row)
        elif row_class == ROW_TOTAL:
            has_input_total = True
            review_ws.cell(row=current_row, column=2, value=description or "TOTAL GENERAL")
            total_from_rows = subtotal_rows if subtotal_rows else all_item_rows
            if total_from_rows:
                review_ws.cell(row=current_row, column=6, value=_sum_formula(total_from_rows))
            elif amount_value is not None:
                review_ws.cell(row=current_row, column=6, value=float(amount_value))
        elif row_class == ROW_COST_ITEM:
            all_item_rows.append(current_row)
            chapter_item_rows.append(current_row)
        elif row_class == ROW_AMBIGUOUS:
            review_ws.cell(row=current_row, column=2, value=f"[REVISION] {description}".strip())

        marker = f"{row_class}_{review_row_id}"
        review_ws.cell(row=current_row, column=7, value=marker)
        append_trace(
            review_row_id=review_row_id,
            review_row_number=current_row,
            extraction=extraction,
            row_class=row_class,
            mapping_status=extraction.mapping_status,
            notes=extraction.notes,
        )
        current_row += 1

    append_subtotal_row(current_chapter)

    if not has_input_total:
        review_row_id = f"brv_{uuid4().hex[:10]}"
        review_ws.cell(row=current_row, column=2, value="TOTAL GENERAL")
        total_from_rows = subtotal_rows if subtotal_rows else all_item_rows
        if total_from_rows:
            review_ws.cell(row=current_row, column=6, value=_sum_formula(total_from_rows))
        review_ws.cell(row=current_row, column=7, value=f"TOTAL_{review_row_id}")
        append_trace(
            review_row_id=review_row_id,
            review_row_number=current_row,
            extraction=None,
            row_class=ROW_TOTAL,
            mapping_status="NOT_COST_ITEM",
            notes="GENERATED_TOTAL",
        )
        current_row += 1

    _apply_visual_style(review_ws)

    return {
        "review_sheet_name": review_sheet_name,
        "trace_sheet_name": trace_sheet_name,
        "review_row_count": str(max(current_row - 5, 0)),
        "trace_row_count": str(max(trace_ws.max_row - 1, 0)),
    }
