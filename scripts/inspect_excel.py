#!/usr/bin/env python3
"""Diagnose Excel sample files without importing data into master."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Any

from openpyxl import load_workbook  # type: ignore

SAMPLES_DIR = Path("data/samples")
REPORT_DIR = Path("reports/excel_diagnostics")
JSON_REPORT = REPORT_DIR / "excel_diagnostics_inventory.json"
MD_REPORT = REPORT_DIR / "excel_diagnostics_inventory_report.md"

SUPPORTED_EXTENSIONS = {".xlsx", ".xlsm"}
LEGACY_OR_UNSUPPORTED_EXTENSIONS = {".xls", ".xlsb"}
ALL_EXCEL_EXTENSIONS = SUPPORTED_EXTENSIONS | LEGACY_OR_UNSUPPORTED_EXTENSIONS

COLUMN_PATTERNS = {
    "codigo": [r"\bcod(igo)?\b", r"\bref(erencia)?\b", r"\bpartida\b"],
    "descripcion": [r"\bdesc(ripcion)?\b", r"\bconcepto\b", r"\btexto\b"],
    "unidad": [r"\bunidad\b", r"\bud\b", r"\bu\.?\b"],
    "cantidad": [r"\bcantidad\b", r"\bmedicion\b", r"\bqty\b"],
    "precio": [r"\bprecio\b", r"\bp\.?\s*unit\b", r"\bunitario\b"],
    "importe": [r"\bimporte\b", r"\btotal\b", r"\bcoste\b", r"\bpresupuesto\b"],
}


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _detect_sheet_type(sheet: Any) -> str:
    cls = sheet.__class__.__name__.lower()
    if "chartsheet" in cls:
        return "CHARTSHEET"
    if hasattr(sheet, "iter_rows"):
        return "WORKSHEET"
    return "UNKNOWN"


def _scan_header_and_columns(rows: list[list[str]]) -> tuple[list[str], dict[str, list[str]]]:
    candidate_headers: list[str] = []
    candidate_columns: dict[str, list[str]] = {k: [] for k in COLUMN_PATTERNS}

    if not rows:
        return candidate_headers, candidate_columns

    max_rows = min(25, len(rows))
    for ridx in range(max_rows):
        row = rows[ridx]
        non_empty = [cell for cell in row if cell]
        if len(non_empty) < 2:
            continue

        hit_count = 0
        for cell in non_empty:
            cell_l = cell.lower()
            for patterns in COLUMN_PATTERNS.values():
                if any(re.search(p, cell_l) for p in patterns):
                    hit_count += 1
                    break

        if hit_count >= 2:
            candidate_headers = non_empty
            for col_name in non_empty:
                col_l = col_name.lower()
                for field, patterns in COLUMN_PATTERNS.items():
                    if any(re.search(p, col_l) for p in patterns):
                        if col_name not in candidate_columns[field]:
                            candidate_columns[field].append(col_name)
            break

    return candidate_headers, candidate_columns


def inspect_excel_file(path: Path, relative_path: str) -> dict[str, Any]:
    ext = path.suffix.lower()
    file_ref = {
        "relative_path": relative_path,
        "extension": ext,
        "size_bytes": path.stat().st_size,
        "supported_extension": ext in SUPPORTED_EXTENSIONS,
    }

    if ext in LEGACY_OR_UNSUPPORTED_EXTENSIONS:
        return {
            "file_ref": file_ref,
            "workbook_status": "UNSUPPORTED_LEGACY_EXCEL",
            "sheets": [],
            "summary": {
                "worksheets_count": 0,
                "chartsheets_count": 0,
                "empty_sheets_count": 0,
                "non_tabular_sheets_count": 0,
                "possible_tables_count": 0,
            },
            "risks": ["LEGACY_OR_UNSUPPORTED_EXTENSION"],
            "manual_review": ["CONVERT_TO_SUPPORTED_EXCEL_FORMAT"],
        }

    try:
        wb = load_workbook(path, read_only=False, data_only=False)
    except Exception as exc:
        return {
            "file_ref": file_ref,
            "workbook_status": "WORKBOOK_OPEN_ERROR",
            "sheets": [],
            "summary": {
                "worksheets_count": 0,
                "chartsheets_count": 0,
                "empty_sheets_count": 0,
                "non_tabular_sheets_count": 0,
                "possible_tables_count": 0,
            },
            "risks": ["WORKBOOK_OPEN_ERROR"],
            "manual_review": [f"OPEN_ERROR:{exc}"],
        }

    sheets_out: list[dict[str, Any]] = []
    risks: list[str] = []
    manual_review: list[str] = []

    worksheets_count = 0
    chartsheets_count = 0
    empty_sheets_count = 0
    non_tabular_sheets_count = 0
    possible_tables_count = 0

    for sheet in wb.worksheets + wb.chartsheets:  # type: ignore[attr-defined]
        sheet_type = _detect_sheet_type(sheet)
        sheet_name = sheet.title
        out: dict[str, Any] = {
            "sheet_name": sheet_name,
            "sheet_type": sheet_type,
        }

        if sheet_type != "WORKSHEET":
            if sheet_type == "CHARTSHEET":
                chartsheets_count += 1
                manual_review.append(f"CHARTSHEET_PRESENT:{sheet_name}")
            else:
                manual_review.append(f"UNKNOWN_SHEET_TYPE:{sheet_name}")
            out.update(
                {
                    "dimensions": {"max_row": None, "max_column": None},
                    "non_empty_rows": 0,
                    "non_empty_columns": 0,
                    "possible_tables": [],
                    "candidate_headers": [],
                    "candidate_columns": {k: [] for k in COLUMN_PATTERNS},
                    "merged_cells_count": 0,
                    "formula_cells_count": 0,
                    "numeric_format_samples": [],
                    "is_empty_sheet": True,
                    "is_likely_tabular": False,
                }
            )
            sheets_out.append(out)
            continue

        worksheets_count += 1
        max_row = getattr(sheet, "max_row", 0) or 0
        max_column = getattr(sheet, "max_column", 0) or 0

        rows_text: list[list[str]] = []
        non_empty_rows = 0
        non_empty_cols_set: set[int] = set()
        formula_cells_count = 0
        numeric_formats: set[str] = set()

        for row in sheet.iter_rows(min_row=1, max_row=max_row, max_col=max_column):
            row_values: list[str] = []
            has_data = False
            for idx, cell in enumerate(row, start=1):
                txt = _as_text(cell.value)
                row_values.append(txt)
                if txt:
                    has_data = True
                    non_empty_cols_set.add(idx)
                if isinstance(cell.value, str) and cell.value.startswith("="):
                    formula_cells_count += 1
                fmt = _as_text(cell.number_format)
                if fmt and fmt not in {"General", "@"} and len(numeric_formats) < 20:
                    numeric_formats.add(fmt)
            if has_data:
                non_empty_rows += 1
            rows_text.append(row_values)

        candidate_headers, candidate_columns = _scan_header_and_columns(rows_text)
        possible_tables = sorted(list(getattr(sheet, "tables", {}).keys()))
        merged_cells_count = len(getattr(sheet, "merged_cells", {}).ranges)

        if non_empty_rows == 0:
            empty_sheets_count += 1
            risks.append("EMPTY_WORKSHEET_PRESENT")
            manual_review.append(f"EMPTY_WORKSHEET:{sheet_name}")

        is_likely_tabular = non_empty_rows > 1 and len(non_empty_cols_set) > 1
        if not is_likely_tabular:
            non_tabular_sheets_count += 1
            manual_review.append(f"NON_TABULAR_WORKSHEET:{sheet_name}")

        if not candidate_headers:
            manual_review.append(f"NO_CLEAR_HEADERS:{sheet_name}")

        if formula_cells_count > 0:
            risks.append("FORMULAS_PRESENT")

        if merged_cells_count > 0:
            risks.append("MERGED_CELLS_PRESENT")

        possible_tables_count += len(possible_tables)

        out.update(
            {
                "dimensions": {"max_row": max_row, "max_column": max_column},
                "non_empty_rows": non_empty_rows,
                "non_empty_columns": len(non_empty_cols_set),
                "possible_tables": possible_tables,
                "candidate_headers": candidate_headers,
                "candidate_columns": candidate_columns,
                "merged_cells_count": merged_cells_count,
                "formula_cells_count": formula_cells_count,
                "numeric_format_samples": sorted(numeric_formats),
                "is_empty_sheet": non_empty_rows == 0,
                "is_likely_tabular": is_likely_tabular,
            }
        )
        sheets_out.append(out)

    wb.close()

    if chartsheets_count > 0:
        risks.append("CHARTSHEETS_PRESENT")

    return {
        "file_ref": file_ref,
        "workbook_status": "EXCEL_DIAGNOSED",
        "sheets": sheets_out,
        "summary": {
            "worksheets_count": worksheets_count,
            "chartsheets_count": chartsheets_count,
            "empty_sheets_count": empty_sheets_count,
            "non_tabular_sheets_count": non_tabular_sheets_count,
            "possible_tables_count": possible_tables_count,
        },
        "risks": sorted(set(risks)),
        "manual_review": sorted(set(manual_review)),
    }


def inspect_excel_samples(root: Path) -> dict[str, Any]:
    samples_path = root / SAMPLES_DIR
    generated_at = datetime.now(timezone.utc).isoformat()

    if not samples_path.exists():
        return {
            "generated_at": generated_at,
            "samples_dir": str(SAMPLES_DIR).replace("\\", "/"),
            "exists": False,
            "files_total": 0,
            "excel_files_detected": 0,
            "files": [],
            "global_summary": {},
        }

    all_files = sorted([p for p in samples_path.rglob("*") if p.is_file()])
    excel_files = [p for p in all_files if p.suffix.lower() in ALL_EXCEL_EXTENSIONS]

    out_files: list[dict[str, Any]] = []
    worksheets_total = 0
    chartsheets_total = 0

    for path in excel_files:
        rel = str(path.relative_to(root)).replace("\\", "/")
        diagnosed = inspect_excel_file(path, rel)
        out_files.append(diagnosed)
        summary = diagnosed.get("summary", {})
        worksheets_total += int(summary.get("worksheets_count", 0) or 0)
        chartsheets_total += int(summary.get("chartsheets_count", 0) or 0)

    return {
        "generated_at": generated_at,
        "samples_dir": str(SAMPLES_DIR).replace("\\", "/"),
        "exists": True,
        "files_total": len(all_files),
        "excel_files_detected": len(excel_files),
        "files": out_files,
        "global_summary": {
            "worksheets_total": worksheets_total,
            "chartsheets_total": chartsheets_total,
            "excel_files_with_manual_review": sum(1 for f in out_files if f.get("manual_review")),
            "excel_files_with_risks": sum(1 for f in out_files if f.get("risks")),
        },
    }


def write_reports(root: Path, payload: dict[str, Any]) -> tuple[Path, Path]:
    json_path = root / JSON_REPORT
    md_path = root / MD_REPORT
    json_path.parent.mkdir(parents=True, exist_ok=True)

    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Excel Diagnostics Inventory",
        "",
        "> Local report. Real-data output may be sensitive and must remain outside Git.",
        "",
        f"- Generated at (UTC): {payload.get('generated_at')}",
        f"- Samples dir: {payload.get('samples_dir')}",
        f"- Files total: {payload.get('files_total', 0)}",
        f"- Excel files detected: {payload.get('excel_files_detected', 0)}",
        "",
        "## Global summary",
        "",
        f"- Worksheets total: {payload.get('global_summary', {}).get('worksheets_total', 0)}",
        f"- Chartsheets total: {payload.get('global_summary', {}).get('chartsheets_total', 0)}",
        f"- Excel files with risks: {payload.get('global_summary', {}).get('excel_files_with_risks', 0)}",
        f"- Excel files with manual review: {payload.get('global_summary', {}).get('excel_files_with_manual_review', 0)}",
        "",
        "## Files",
        "",
    ]

    for entry in payload.get("files", []):
        ref = entry.get("file_ref", {})
        lines.append(f"### {ref.get('relative_path')}")
        lines.append(f"- Workbook status: {entry.get('workbook_status')}")
        lines.append(f"- Worksheets: {entry.get('summary', {}).get('worksheets_count', 0)}")
        lines.append(f"- Chartsheets: {entry.get('summary', {}).get('chartsheets_count', 0)}")
        lines.append(f"- Risks: {', '.join(entry.get('risks', [])) or 'none'}")
        lines.append(f"- Manual review: {', '.join(entry.get('manual_review', [])) or 'none'}")
        lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    payload = inspect_excel_samples(root)
    json_path, md_path = write_reports(root, payload)

    print("Excel diagnostics summary")
    print(f"- Samples dir: {payload.get('samples_dir')}")
    print(f"- Files total: {payload.get('files_total', 0)}")
    print(f"- Excel files detected: {payload.get('excel_files_detected', 0)}")
    print(f"- Worksheets total: {payload.get('global_summary', {}).get('worksheets_total', 0)}")
    print(f"- Chartsheets total: {payload.get('global_summary', {}).get('chartsheets_total', 0)}")
    print(f"- JSON report: {json_path.relative_to(root).as_posix()}")
    print(f"- Markdown report: {md_path.relative_to(root).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
