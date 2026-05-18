#!/usr/bin/env python3
"""Validate the contract emitted by the full Excel reader."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

DEFAULT_INPUT = Path("reports/excel_full_reader/excel_full_reader_inventory.json")
REPORT_DIR = Path("reports/excel_full_reader_validation")
JSON_REPORT = REPORT_DIR / "excel_full_reader_validation_report.json"
MD_REPORT = REPORT_DIR / "excel_full_reader_validation_report.md"

REQUIRED_ROOT_KEYS = [
    "reader_metadata",
    "source_files",
    "workbook_summaries",
    "sheets",
    "global_summary",
    "risks",
    "warnings",
    "manual_review",
    "controlled_exclusions",
]

REQUIRED_WORKBOOK_KEYS = [
    "workbook_ref",
    "relative_path_sanitized",
    "extension",
    "sheet_count",
    "worksheet_count",
    "chartsheet_count",
    "readable",
    "errors",
    "warnings",
    "manual_review",
    "risks",
]

REQUIRED_SHEET_KEYS = [
    "sheet_ref",
    "workbook_ref",
    "sheet_name_sanitized",
    "sheet_type",
    "used_range",
    "dimensions",
    "visibility",
    "merged_cells_summary",
    "formulas_summary",
    "comments_summary",
    "styles_summary",
    "density_profile",
    "candidate_header_rows",
    "candidate_columns",
    "candidate_table_blocks",
    "visual_blocks",
    "budget_signals",
    "traceability_map",
    "cell_samples_sanitized",
    "warnings",
    "manual_review",
]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _missing_codes(prefix: str, keys: list[str], payload: dict[str, Any]) -> list[dict[str, Any]]:
    missing: list[dict[str, Any]] = []
    for key in keys:
        if key not in payload:
            missing.append(
                {
                    "scope": prefix,
                    "severity": "ERROR",
                    "code": f"MISSING_{key.upper()}",
                    "detail": f"Missing required key: {key}",
                }
            )
    return missing


def _sheet_status(sheet: dict[str, Any]) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    manual_review: list[dict[str, Any]] = []

    errors.extend(_missing_codes(f"sheet:{sheet.get('sheet_ref', 'UNKNOWN')}", REQUIRED_SHEET_KEYS, sheet))

    if not isinstance(sheet.get("candidate_header_rows", []), list):
        errors.append(
            {
                "scope": sheet.get("sheet_ref", "UNKNOWN"),
                "severity": "ERROR",
                "code": "INVALID_CANDIDATE_HEADER_ROWS_TYPE",
                "detail": "candidate_header_rows must be a list.",
            }
        )
    if not isinstance(sheet.get("candidate_columns", {}), dict):
        errors.append(
            {
                "scope": sheet.get("sheet_ref", "UNKNOWN"),
                "severity": "ERROR",
                "code": "INVALID_CANDIDATE_COLUMNS_TYPE",
                "detail": "candidate_columns must be a dict.",
            }
        )
    if not isinstance(sheet.get("traceability_map", []), list):
        errors.append(
            {
                "scope": sheet.get("sheet_ref", "UNKNOWN"),
                "severity": "ERROR",
                "code": "INVALID_TRACEABILITY_MAP_TYPE",
                "detail": "traceability_map must be a list.",
            }
        )

    sheet_type = str(sheet.get("sheet_type") or "").upper()
    if sheet_type == "WORKSHEET":
        if not sheet.get("traceability_map"):
            errors.append(
                {
                    "scope": sheet.get("sheet_ref", "UNKNOWN"),
                    "severity": "ERROR",
                    "code": "TRACEABILITY_MAP_EMPTY",
                    "detail": "Worksheet must preserve cell-level traceability.",
                }
            )
        if not sheet.get("candidate_header_rows") and not sheet.get("is_empty_sheet"):
            manual_review.append(
                {
                    "scope": sheet.get("sheet_ref", "UNKNOWN"),
                    "severity": "MANUAL_REVIEW_REQUIRED",
                    "code": "NO_CLEAR_HEADERS",
                    "detail": "Worksheet has no clear header rows.",
                }
            )
        if not sheet.get("is_likely_tabular"):
            warnings.append(
                {
                    "scope": sheet.get("sheet_ref", "UNKNOWN"),
                    "severity": "WARNING",
                    "code": "NON_TABULAR_WORKSHEET",
                    "detail": "Worksheet appears visually or structurally non-tabular.",
                }
            )
            manual_review.append(
                {
                    "scope": sheet.get("sheet_ref", "UNKNOWN"),
                    "severity": "MANUAL_REVIEW_REQUIRED",
                    "code": "NON_TABULAR_WORKSHEET",
                    "detail": "Worksheet requires manual interpretation.",
                }
            )
    elif sheet_type == "CHARTSHEET":
        manual_review.append(
            {
                "scope": sheet.get("sheet_ref", "UNKNOWN"),
                "severity": "MANUAL_REVIEW_REQUIRED",
                "code": "CHARTSHEET_CONTEXT",
                "detail": "Chartsheet preserved as non-tabular context.",
            }
        )
    else:
        warnings.append(
            {
                "scope": sheet.get("sheet_ref", "UNKNOWN"),
                "severity": "WARNING",
                "code": "UNKNOWN_SHEET_TYPE",
                "detail": f"Unexpected sheet_type={sheet_type!r}.",
            }
        )
        manual_review.append(
            {
                "scope": sheet.get("sheet_ref", "UNKNOWN"),
                "severity": "MANUAL_REVIEW_REQUIRED",
                "code": "UNKNOWN_SHEET_TYPE",
                "detail": f"Unexpected sheet type {sheet_type!r}.",
            }
        )

    status = "VALID"
    if errors:
        status = "ERROR"
    elif manual_review or warnings:
        status = "MANUAL_REVIEW_REQUIRED"

    return status, errors, warnings, manual_review


def validate_excel_full_reader(report: dict[str, Any], source_path: str) -> dict[str, Any]:
    blocking_errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    manual_review_items: list[dict[str, Any]] = []
    info: list[dict[str, Any]] = []
    workbook_validation: list[dict[str, Any]] = []
    sheet_validation: list[dict[str, Any]] = []

    blocking_errors.extend(_missing_codes("root", REQUIRED_ROOT_KEYS, report))
    if blocking_errors:
        return {
            "validation_metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "validator_stage": "phase_7_2_excel_full_reader_contract",
                "status": "ERROR",
            },
            "source_excel_full_reader_report": source_path,
            "workbook_validation": [],
            "sheet_validation": [],
            "blocking_errors": blocking_errors,
            "warnings": [],
            "manual_review_items": [],
            "info": [],
            "global_validation_summary": {
                "workbooks_count": 0,
                "sheets_count": 0,
                "worksheet_count": 0,
                "chartsheet_count": 0,
                "controlled_exclusions_count": 0,
                "blocking_error_count": len(blocking_errors),
                "warning_count": 0,
                "manual_review_count": 0,
                "eligible_workbooks_count": 0,
                "can_advance_to_excel_intermediate_normalization": False,
                "full_corpus_status": "BLOCKED",
                "valid_subset_status": "BLOCKED",
            },
            "validation_readiness": {
                "global": "VALIDATION_BLOCKED",
                "phase_7_2_next_recommendation": "Fix the Excel reader contract before normalizing.",
            },
            "phase_7_2_next_recommendation": "Fix the Excel reader contract before normalizing.",
            "controlled_exclusions": report.get("controlled_exclusions", []),
        }

    workbook_summaries = report.get("workbook_summaries", [])
    sheets = report.get("sheets", [])

    workbook_map: dict[str, dict[str, Any]] = {}
    for workbook in workbook_summaries:
        workbook_errors = _missing_codes(
            f"workbook:{workbook.get('workbook_ref', 'UNKNOWN')}", REQUIRED_WORKBOOK_KEYS, workbook
        )
        workbook_status = "VALID"
        workbook_warnings: list[dict[str, Any]] = []
        workbook_manual: list[dict[str, Any]] = []
        if workbook_errors:
            workbook_status = "ERROR"
        if int(workbook.get("sheet_count", 0) or 0) == 0:
            workbook_manual.append(
                {
                    "scope": workbook.get("workbook_ref", "UNKNOWN"),
                    "severity": "MANUAL_REVIEW_REQUIRED",
                    "code": "EMPTY_WORKBOOK",
                    "detail": "Workbook contains no sheets.",
                }
            )
            workbook_status = "MANUAL_REVIEW_REQUIRED" if workbook_status == "VALID" else workbook_status
        workbook_map[workbook.get("workbook_ref", "")] = {
            "workbook_ref": workbook.get("workbook_ref"),
            "relative_path_sanitized": workbook.get("relative_path_sanitized"),
            "readable": workbook.get("readable"),
            "status": workbook_status,
            "errors": workbook_errors,
            "warnings": workbook_warnings,
            "manual_review": workbook_manual,
        }
        workbook_validation.append(workbook_map[workbook.get("workbook_ref", "")])
        blocking_errors.extend(workbook_errors)
        manual_review_items.extend(workbook_manual)
        warnings.extend(workbook_warnings)

    for sheet in sheets:
        sheet_status, sheet_errors, sheet_warnings, sheet_manual = _sheet_status(sheet)
        sheet_validation.append(
            {
                "sheet_ref": sheet.get("sheet_ref"),
                "workbook_ref": sheet.get("workbook_ref"),
                "sheet_name_sanitized": sheet.get("sheet_name_sanitized"),
                "sheet_type": sheet.get("sheet_type"),
                "status": sheet_status,
                "errors": sheet_errors,
                "warnings": sheet_warnings,
                "manual_review": sheet_manual,
            }
        )
        blocking_errors.extend(sheet_errors)
        warnings.extend(sheet_warnings)
        manual_review_items.extend(sheet_manual)

    global_summary = report.get("global_summary", {})
    workbooks_count = len(workbook_summaries)
    sheets_count = len(sheets)
    worksheet_count = sum(1 for sheet in sheets if str(sheet.get("sheet_type")).upper() == "WORKSHEET")
    chartsheet_count = sum(1 for sheet in sheets if str(sheet.get("sheet_type")).upper() == "CHARTSHEET")
    eligible_workbooks_count = sum(1 for item in workbook_summaries if bool(item.get("readable")))
    controlled_exclusions_count = len(report.get("controlled_exclusions", []))
    blocking_error_count = len(blocking_errors)
    warning_count = len(warnings)
    manual_review_count = len(manual_review_items)
    can_advance = blocking_error_count == 0 and sheets_count > 0

    if blocking_error_count > 0:
        readiness = "VALIDATION_BLOCKED"
        status = "ERROR"
        recommendation = "Fix the Excel reader contract before normalizing."
        full_corpus_status = "BLOCKED"
        valid_subset_status = "BLOCKED"
    elif manual_review_count > 0 or warning_count > 0:
        readiness = "VALIDATION_READY_WITH_NON_BLOCKING_MANUAL_REVIEW"
        status = "MANUAL_REVIEW_REQUIRED"
        recommendation = "Advance with non-blocking manual review tracked."
        full_corpus_status = "NOT_BLOCKED"
        valid_subset_status = "ADVANCE_ALLOWED" if can_advance else "BLOCKED"
    elif controlled_exclusions_count > 0:
        readiness = "VALIDATION_READY_WITH_CONTROLLED_EXCLUSIONS"
        status = "VALID"
        recommendation = "Advance with controlled exclusions tracked."
        full_corpus_status = "NOT_BLOCKED"
        valid_subset_status = "ADVANCE_ALLOWED" if can_advance else "BLOCKED"
    else:
        readiness = "VALIDATION_READY_FOR_INTERMEDIATE_NORMALIZATION"
        status = "VALID"
        recommendation = "Excel reader contract ready for intermediate normalization."
        full_corpus_status = "NOT_BLOCKED"
        valid_subset_status = "ADVANCE_ALLOWED" if can_advance else "BLOCKED"

    info.append(
        {
            "scope": "global",
            "severity": "INFO",
            "code": "CONTROLLED_EXCLUSIONS_PRESERVED",
            "detail": f"Controlled exclusions count: {controlled_exclusions_count}",
        }
    )
    info.append(
        {
            "scope": "global",
            "severity": "INFO",
            "code": "TRACEABILITY_PRESERVED",
            "detail": f"Total traced cell entries: {global_summary.get('traced_cells_total', 0)}",
        }
    )

    return {
        "validation_metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "validator_stage": "phase_7_2_excel_full_reader_contract",
            "status": status,
            "source_report_path": source_path,
        },
        "source_excel_full_reader_report": source_path,
        "workbook_validation": workbook_validation,
        "sheet_validation": sheet_validation,
        "blocking_errors": blocking_errors,
        "warnings": warnings,
        "manual_review_items": manual_review_items,
        "info": info,
        "global_validation_summary": {
            "workbooks_count": workbooks_count,
            "sheets_count": sheets_count,
            "worksheet_count": worksheet_count,
            "chartsheet_count": chartsheet_count,
            "controlled_exclusions_count": controlled_exclusions_count,
            "blocking_error_count": blocking_error_count,
            "warning_count": warning_count,
            "manual_review_count": manual_review_count,
            "eligible_workbooks_count": eligible_workbooks_count,
            "can_advance_to_excel_intermediate_normalization": can_advance,
            "full_corpus_status": full_corpus_status,
            "valid_subset_status": valid_subset_status,
        },
        "validation_readiness": {
            "global": readiness,
            "phase_7_2_next_recommendation": recommendation,
        },
        "phase_7_2_next_recommendation": recommendation,
        "controlled_exclusions": report.get("controlled_exclusions", []),
    }


def write_outputs(root: Path, report: dict[str, Any]) -> tuple[Path, Path]:
    json_path = root / JSON_REPORT
    md_path = root / MD_REPORT
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    gs = report.get("global_validation_summary", {})
    vm = report.get("validation_metadata", {})
    lines = [
        "# Excel Full Reader Validation Report",
        "",
        "> Local validation output. Real-data artifacts may be sensitive and must remain outside Git.",
        "",
        f"- Generated at (UTC): {vm.get('generated_at')}",
        f"- Status: {vm.get('status')}",
        f"- Readiness: {report.get('validation_readiness', {}).get('global')}",
        f"- Full corpus status: {gs.get('full_corpus_status')}",
        f"- Valid subset status: {gs.get('valid_subset_status')}",
        "",
        "## Blocking Errors",
        "",
    ]
    if report.get("blocking_errors"):
        for item in report["blocking_errors"]:
            lines.append(f"- {item.get('scope')}: {item.get('code')} ({item.get('detail')})")
    else:
        lines.append("- none")

    lines.extend(["", "## Manual Review", ""])
    if report.get("manual_review_items"):
        for item in report["manual_review_items"]:
            lines.append(f"- {item.get('scope')}: {item.get('code')} ({item.get('detail')})")
    else:
        lines.append("- none")

    lines.extend(["", "## Warnings", ""])
    if report.get("warnings"):
        for item in report["warnings"]:
            lines.append(f"- {item.get('scope')}: {item.get('code')} ({item.get('detail')})")
    else:
        lines.append("- none")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    input_path = root / DEFAULT_INPUT
    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1]).resolve()
    if not input_path.exists():
        print(f"ERROR: input JSON not found: {input_path}")
        return 1

    source = _load_json(input_path)
    source_path = _sanitize_source_path(root, input_path)
    report = validate_excel_full_reader(source, source_path)
    json_path, md_path = write_outputs(root, report)

    print("Excel full reader validation summary")
    print(f"- Source: {input_path}")
    print(f"- Status: {report['validation_metadata']['status']}")
    print(f"- Readiness: {report['validation_readiness']['global']}")
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
