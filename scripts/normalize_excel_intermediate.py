#!/usr/bin/env python3
"""Normalize the Excel full-reader output into an intermediate structure."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Any

DEFAULT_READER_INPUT = Path("reports/excel_full_reader/excel_full_reader_inventory.json")
DEFAULT_VALIDATION_INPUT = Path("reports/excel_full_reader_validation/excel_full_reader_validation_report.json")
REPORT_DIR = Path("reports/excel_intermediate_normalization")
JSON_REPORT = REPORT_DIR / "excel_intermediate_normalization_report.json"
MD_REPORT = REPORT_DIR / "excel_intermediate_normalization_report.md"

UNIT_TOKEN_RE = re.compile(r"\b(M2|M3|ML|UD|KG|L|CM|MM)\b", re.IGNORECASE)
NUMERIC_TOKEN_RE = re.compile(r"\b\d+(?:[.,]\d+)?\b")
MAX_SAMPLE_ROWS = 5
MAX_TRACEABILITY_ENTRIES = 200


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _truncate(text: str, max_len: int = 180) -> str:
    value = (text or "").strip()
    if len(value) <= max_len:
        return value
    return value[: max_len - 3] + "..."


def _validation_index(validation_report: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    if not validation_report:
        return out
    for item in validation_report.get("sheet_validation", []):
        sheet_ref = item.get("sheet_ref")
        if sheet_ref:
            out[sheet_ref] = item
    return out


def _extract_candidate_rows(sheet: dict[str, Any]) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    cell_samples = sheet.get("cell_samples_sanitized", {})
    for item in cell_samples.get("first_non_empty_rows", [])[:MAX_SAMPLE_ROWS]:
        samples.append(
            {
                "row": item.get("row"),
                "kind": "first_non_empty_row",
                "cells": item.get("cells", [])[:10],
            }
        )
    for item in cell_samples.get("dense_rows", [])[:MAX_SAMPLE_ROWS]:
        samples.append(
            {
                "row": item.get("row"),
                "kind": "dense_row",
                "non_empty_cells": item.get("non_empty_cells"),
                "cells": item.get("cells", [])[:10],
            }
        )
    return samples


def _extract_traceability(sheet: dict[str, Any]) -> list[dict[str, Any]]:
    traceability = []
    for item in sheet.get("traceability_map", [])[:MAX_TRACEABILITY_ENTRIES]:
        traceability.append(
            {
                "row": item.get("row"),
                "column": item.get("column"),
                "coordinate": item.get("coordinate"),
                "data_type": item.get("data_type"),
                "value_type": item.get("value_type"),
                "sanitized_value": item.get("sanitized_value"),
                "formula": item.get("formula"),
                "flags": item.get("flags", []),
            }
        )
    return traceability


def _signals_from_sheet(sheet: dict[str, Any], field: str) -> list[dict[str, Any]]:
    cols = sheet.get("budget_signals", {}).get("candidate_columns", {}).get(field, [])
    return [{"column": col, "source": "candidate_columns"} for col in cols]


def _derived_units(sheet: dict[str, Any]) -> list[str]:
    units: set[str] = set()
    for col in sheet.get("budget_signals", {}).get("candidate_columns", {}).get("unidad", []):
        if col:
            units.add(col)
    for entry in sheet.get("traceability_map", []):
        value = str(entry.get("sanitized_value") or "")
        for token in UNIT_TOKEN_RE.findall(value):
            units.add(token.upper())
    return sorted(units)


def _derived_numeric_signals(sheet: dict[str, Any]) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    for entry in sheet.get("traceability_map", []):
        value = str(entry.get("sanitized_value") or "")
        numbers = NUMERIC_TOKEN_RE.findall(value)
        if numbers:
            signals.append(
                {
                    "coordinate": entry.get("coordinate"),
                    "row": entry.get("row"),
                    "column": entry.get("column"),
                    "numeric_tokens": numbers[:5],
                    "formula": entry.get("formula"),
                }
            )
    return signals


def _normalize_sheet(sheet: dict[str, Any], validation_entry: dict[str, Any] | None) -> dict[str, Any]:
    warnings = list(sheet.get("warnings", []))
    manual_review = list(sheet.get("manual_review", []))
    if validation_entry:
        warnings.extend(
            f"{item.get('code')}:{item.get('detail')}" for item in validation_entry.get("warnings", [])
        )
        manual_review.extend(
            f"{item.get('code')}:{item.get('detail')}" for item in validation_entry.get("manual_review", [])
        )

    candidate_tables = list(sheet.get("candidate_table_blocks", []))
    if not candidate_tables and sheet.get("is_likely_tabular"):
        candidate_tables.append(
            {
                "block_type": "heuristic_table_block",
                "confidence": "low",
                "source": "normalized_from_reader",
                "range": sheet.get("used_range"),
            }
        )

    candidate_rows = _extract_candidate_rows(sheet)
    candidate_columns = sheet.get("candidate_columns", {})
    traceability = _extract_traceability(sheet)
    source_trace = {
        "workbook_ref": sheet.get("workbook_ref"),
        "sheet_ref": sheet.get("sheet_ref"),
        "sheet_type": sheet.get("sheet_type"),
        "sheet_name_sanitized": sheet.get("sheet_name_sanitized"),
        "used_range": sheet.get("used_range"),
        "dimensions": sheet.get("dimensions"),
        "visibility": sheet.get("visibility"),
        "traceability_count": len(sheet.get("traceability_map", [])),
        "cell_traceability": traceability,
    }

    candidate_chapters = []
    for col in candidate_columns.get("capitulo", []):
        candidate_chapters.append({"column": col, "source": "candidate_columns"})
    for col in candidate_columns.get("partida", []):
        candidate_chapters.append({"column": col, "source": "candidate_columns"})

    candidate_cost_items = []
    for col in candidate_columns.get("partida", []) + candidate_columns.get("codigo", []) + candidate_columns.get("descripcion", []):
        candidate_cost_items.append({"column": col, "source": "candidate_columns"})

    formula_signals = []
    for item in sheet.get("formulas_summary", {}).get("sample_cells", []):
        formula_signals.append({"coordinate": item, "source": "formulas_summary"})
    for entry in traceability:
        if entry.get("formula"):
            formula_signals.append(
                {
                    "coordinate": entry.get("coordinate"),
                    "row": entry.get("row"),
                    "column": entry.get("column"),
                    "formula": entry.get("formula"),
                }
            )

    unknown_or_unstructured_blocks = list(sheet.get("visual_blocks", []))
    unknown_or_unstructured_blocks.extend(sheet.get("unknown_or_unsupported", []))

    return {
        "sheet_ref": sheet.get("sheet_ref"),
        "sheet_name_sanitized": sheet.get("sheet_name_sanitized"),
        "sheet_type": sheet.get("sheet_type"),
        "source_trace": source_trace,
        "candidate_tables": candidate_tables,
        "candidate_rows": candidate_rows,
        "candidate_columns": candidate_columns,
        "candidate_chapters": candidate_chapters,
        "candidate_cost_items": candidate_cost_items,
        "unit_signals": _signals_from_sheet(sheet, "unidad") + [{"unit": unit, "source": "traceability"} for unit in _derived_units(sheet)],
        "quantity_signals": _signals_from_sheet(sheet, "cantidad") + _derived_numeric_signals(sheet),
        "price_signals": _signals_from_sheet(sheet, "precio"),
        "amount_signals": _signals_from_sheet(sheet, "importe"),
        "formula_signals": formula_signals,
        "manual_review": manual_review,
        "warnings": warnings,
        "unknown_or_unstructured_blocks": unknown_or_unstructured_blocks,
    }


def normalize_excel_intermediate(
    reader_report: dict[str, Any], validation_report: dict[str, Any] | None
) -> dict[str, Any]:
    validation_idx = _validation_index(validation_report)

    workbooks: list[dict[str, Any]] = []
    normalized_sheet_count = 0
    tabular_sheet_count = 0
    non_tabular_sheet_count = 0
    manual_review_items = 0
    warning_items = 0

    for workbook in reader_report.get("workbook_summaries", []):
        workbook_ref = workbook.get("workbook_ref")
        workbook_sheets = [sheet for sheet in reader_report.get("sheets", []) if sheet.get("workbook_ref") == workbook_ref]
        normalized_sheets = []
        workbook_manual_review = list(workbook.get("manual_review", []))
        workbook_warnings = list(workbook.get("warnings", []))

        for sheet in workbook_sheets:
            normalized = _normalize_sheet(sheet, validation_idx.get(sheet.get("sheet_ref")))
            normalized_sheets.append(normalized)
            normalized_sheet_count += 1
            warning_items += len(normalized["warnings"])
            manual_review_items += len(normalized["manual_review"])
            if sheet.get("is_likely_tabular"):
                tabular_sheet_count += 1
            else:
                non_tabular_sheet_count += 1

        workbooks.append(
            {
                "workbook_ref": workbook_ref,
                "relative_path_sanitized": workbook.get("relative_path_sanitized"),
                "extension": workbook.get("extension"),
                "readable": workbook.get("readable"),
                "sheet_count": workbook.get("sheet_count"),
                "worksheet_count": workbook.get("worksheet_count"),
                "chartsheet_count": workbook.get("chartsheet_count"),
                "source_trace": {
                    "reader_workbook_summary": workbook,
                    "sheet_count_normalized": len(normalized_sheets),
                },
                "sheets": normalized_sheets,
                "warnings": workbook_warnings,
                "manual_review": workbook_manual_review,
            }
        )

    reader_summary = reader_report.get("global_summary", {})
    controlled_exclusions = list(reader_report.get("controlled_exclusions", []))
    blocking = bool(reader_summary.get("workbooks_unreadable", 0))
    can_advance = normalized_sheet_count > 0 and not blocking

    corpus_status = {
        "full_corpus_status": "BLOCKED" if blocking else "NOT_BLOCKED",
        "valid_subset_status": "ADVANCE_ALLOWED" if can_advance else "BLOCKED",
        "can_advance_with_valid_subset": can_advance,
    }

    return {
        "normalization_metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "normalization_stage": "phase_7_2_excel_intermediate",
            "constraints": [
                "No master import",
                "No ratio calculation",
                "No final amount consolidation",
                "No final category normalization",
                "No category mapping feed",
            ],
        },
        "source_reports": {
            "excel_full_reader": str(DEFAULT_READER_INPUT).replace("\\", "/"),
            "excel_full_reader_validation": str(DEFAULT_VALIDATION_INPUT).replace("\\", "/"),
        },
        "corpus_status": corpus_status,
        "workbooks": workbooks,
        "global_summary": {
            "workbooks_total": len(reader_report.get("workbook_summaries", [])),
            "normalized_workbooks_count": len(workbooks),
            "normalized_sheets_count": normalized_sheet_count,
            "tabular_sheets_count": tabular_sheet_count,
            "non_tabular_sheets_count": non_tabular_sheet_count,
            "controlled_exclusions_count": len(controlled_exclusions),
            "manual_review_items_count": manual_review_items,
            "warnings_count": warning_items,
        },
        "controlled_exclusions": controlled_exclusions,
    }


def write_outputs(root: Path, report: dict[str, Any]) -> tuple[Path, Path]:
    json_path = root / JSON_REPORT
    md_path = root / MD_REPORT
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Excel Intermediate Normalization Report",
        "",
        "> Local normalization output. Real-data artifacts may be sensitive and must remain outside Git.",
        "",
        f"- Generated at (UTC): {report.get('normalization_metadata', {}).get('generated_at')}",
        f"- Full corpus status: {report.get('corpus_status', {}).get('full_corpus_status')}",
        f"- Valid subset status: {report.get('corpus_status', {}).get('valid_subset_status')}",
        f"- Normalized workbooks: {report.get('global_summary', {}).get('normalized_workbooks_count', 0)}",
        f"- Normalized sheets: {report.get('global_summary', {}).get('normalized_sheets_count', 0)}",
        "",
        "## Workbooks",
        "",
    ]
    for workbook in report.get("workbooks", []):
        lines.append(f"### {workbook.get('workbook_ref')}")
        lines.append(f"- Path: {workbook.get('relative_path_sanitized')}")
        lines.append(f"- Readable: {workbook.get('readable')}")
        lines.append(f"- Sheets: {len(workbook.get('sheets', []))}")
        lines.append(f"- Warnings: {', '.join(workbook.get('warnings', [])) or 'none'}")
        lines.append(f"- Manual review: {', '.join(workbook.get('manual_review', [])) or 'none'}")
        lines.append("")
        for sheet in workbook.get("sheets", []):
            lines.append(f"#### {sheet.get('sheet_ref')}")
            lines.append(f"- Candidate tables: {len(sheet.get('candidate_tables', []))}")
            lines.append(f"- Candidate rows: {len(sheet.get('candidate_rows', []))}")
            lines.append(f"- Candidate cost items: {len(sheet.get('candidate_cost_items', []))}")
            lines.append(f"- Traceability entries: {sheet.get('source_trace', {}).get('traceability_count', 0)}")
            lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    reader_input = root / DEFAULT_READER_INPUT
    validation_input = root / DEFAULT_VALIDATION_INPUT

    if len(sys.argv) > 1:
        reader_input = Path(sys.argv[1]).resolve()
    if len(sys.argv) > 2:
        validation_input = Path(sys.argv[2]).resolve()

    if not reader_input.exists():
        print(f"ERROR: Excel reader input not found: {reader_input}")
        return 1

    reader_report = _load_json(reader_input)
    validation_report = _load_json(validation_input) if validation_input.exists() else None
    normalized = normalize_excel_intermediate(reader_report, validation_report)
    json_path, md_path = write_outputs(root, normalized)

    print("Excel intermediate normalization summary")
    print(f"- Reader input: {reader_input}")
    print(f"- Validation input: {validation_input if validation_input.exists() else 'not found (skipped)'}")
    print(f"- Full corpus status: {normalized['corpus_status']['full_corpus_status']}")
    print(f"- Valid subset status: {normalized['corpus_status']['valid_subset_status']}")
    print(f"- JSON output: {json_path.relative_to(root).as_posix()}")
    print(f"- Markdown output: {md_path.relative_to(root).as_posix()}")
    return 0


def _sanitize_source_path(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except Exception:
        return path.name


if __name__ == "__main__":
    sys.exit(main())
