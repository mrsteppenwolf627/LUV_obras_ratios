#!/usr/bin/env python3
"""Build a common inventory across BC3, Excel, and Presto/PZH files."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

SAMPLES_DIR = Path("data/samples")
REPORT_DIR = Path("reports/multiformat_inventory")
JSON_REPORT = REPORT_DIR / "multiformat_inventory.json"
MD_REPORT = REPORT_DIR / "multiformat_inventory_report.md"

EXCEL_REPORT = Path("reports/excel_full_reader/excel_full_reader_inventory.json")
EXCEL_VALIDATION_REPORT = Path("reports/excel_full_reader_validation/excel_full_reader_validation_report.json")
PRESTO_REPORT = Path("reports/presto_diagnostics/presto_diagnostics_inventory.json")
BC3_PARSE_REPORT = Path("reports/bc3_strict_parse/bc3_strict_parse_inventory.json")
BC3_VALIDATION_REPORT = Path("reports/bc3_strict_validation/bc3_strict_validation_report.json")

EXCEL_EXTENSIONS = {".xlsx", ".xlsm", ".xls", ".xlsb"}
PRESTO_EXTENSIONS = {".presto", ".pzh", ".prestobackup", ".prestorecord"}
BC3_EXTENSIONS = {".bc3"}


def _sanitize_path(path: str) -> str:
    return path.replace("\\", "/").strip()


def _load_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _format_type_for_path(path: Path) -> str:
    ext = path.suffix.lower()
    name = path.name.lower()
    if ext in BC3_EXTENSIONS:
        return "BC3"
    if ext in EXCEL_EXTENSIONS:
        return "EXCEL"
    if ext in PRESTO_EXTENSIONS or "presto" in name or "pzh" in name:
        return "PRESTO"
    if ext == ".pdf":
        return "PDF"
    return "OTHER"


def _excel_indexes(reader_report: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    idx: dict[str, dict[str, Any]] = {}
    if not reader_report:
        return idx
    for item in reader_report.get("workbook_summaries", []):
        rel = item.get("relative_path_sanitized")
        if rel:
            idx[rel] = item
    return idx


def _bc3_indexes(parse_report: dict[str, Any] | None, validation_report: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    idx: dict[str, dict[str, Any]] = {}
    if parse_report:
        for item in parse_report.get("files", []):
            rel = item.get("file_ref", {}).get("relative_path")
            if rel:
                idx[rel] = {
                    "parse": item,
                    "validation": None,
                    "controlled_exclusion": False,
                }
        for item in parse_report.get("controlled_exclusions", []):
            rel = item.get("relative_path")
            if rel:
                idx.setdefault(rel, {"parse": None, "validation": None, "controlled_exclusion": True})
                idx[rel]["controlled_exclusion"] = True
                idx[rel]["controlled_exclusion_reason"] = item.get("file_eligibility_reason")
                idx[rel]["file_eligibility_status"] = item.get("file_eligibility_status")
    if validation_report:
        for item in validation_report.get("files", []):
            rel = item.get("relative_path")
            if rel:
                idx.setdefault(rel, {"parse": None, "validation": None, "controlled_exclusion": False})
                idx[rel]["validation"] = item
    return idx


def _presto_index(presto_report: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    idx: dict[str, dict[str, Any]] = {}
    if not presto_report:
        return idx
    for item in presto_report.get("files", []):
        rel = item.get("relative_path_sanitized")
        if rel:
            idx[rel] = item
    return idx


def _bc3_sanitized_id(info: dict[str, Any] | None) -> str | None:
    if not info:
        return None
    parse = info.get("parse") or {}
    validation = info.get("validation") or {}
    return (
        (parse.get("file_ref") or {}).get("sanitized_id")
        or validation.get("sanitized_id")
        or info.get("sanitized_id")
    )


def _derive_excel_status(entry: dict[str, Any] | None) -> tuple[str, str, bool, list[str], list[str], str]:
    if not entry:
        return (
            "NOT_INSPECTED",
            "NOT_ELIGIBLE_OR_NOT_INSPECTED",
            True,
            ["EXCEL_REPORT_MISSING"],
            [],
            "Run read_excel_full and validate_excel_full_reader.",
        )
    readable = bool(entry.get("readable"))
    warnings = list(entry.get("warnings", []))
    manual = list(entry.get("manual_review", []))
    if not readable:
        return (
            "NOT_READABLE",
            "BLOCKED_STRUCTURAL_ISSUE" if entry.get("errors") else "NOT_ELIGIBLE_AUXILIARY_OR_CORRUPT",
            True,
            warnings,
            manual,
            "Inspect the workbook contract or exclude the file.",
        )
    if warnings or manual:
        return (
            "READABLE_WITH_MANUAL_REVIEW",
            "ELIGIBLE_WITH_NON_BLOCKING_MANUAL_REVIEW",
            False,
            warnings,
            manual,
            "Run intermediate normalization with manual review tracked.",
        )
    return (
        "READABLE",
        "ELIGIBLE_FOR_READING",
        False,
        warnings,
        manual,
        "Run Excel intermediate normalization.",
    )


def _derive_bc3_status(entry: dict[str, Any] | None) -> tuple[str, str, bool, list[str], list[str], str]:
    if not entry:
        return (
            "NOT_INSPECTED",
            "NOT_INSPECTED",
            True,
            ["BC3_REPORT_MISSING"],
            [],
            "Run parse_bc3_strict and validate_bc3_strict.",
        )
    if entry.get("file_eligibility_status"):
        eligible_status = entry.get("file_eligibility_status")
        controlled = eligible_status != "ELIGIBLE_FOR_PRELIMINARY_FLOW" and eligible_status != "ELIGIBLE_WITH_NON_BLOCKING_MANUAL_REVIEW"
        readable_status = "EXCLUDED" if controlled else "READABLE"
        warnings = list(entry.get("warnings", []))
        manual = list(entry.get("manual_review_required", []))
        next_action = "Keep excluded as technical reference." if controlled else "Run strict normalization."
        return readable_status, eligible_status, controlled, warnings, manual, next_action

    validation = entry.get("validation")
    parse = entry.get("parse")
    warnings: list[str] = []
    manual: list[str] = []
    if validation:
        warnings.extend(item.get("code", "") for item in validation.get("warnings", []))
        manual.extend(item.get("code", "") for item in validation.get("manual_review_items", []))
        validation_readiness = validation.get("validation_readiness", {})
        if isinstance(validation_readiness, dict):
            readiness = validation_readiness.get("global", "UNKNOWN")
        else:
            readiness = str(validation_readiness or "UNKNOWN")
        status = validation.get("validation_metadata", {}).get("status", "UNKNOWN")
        if readiness == "VALIDATION_BLOCKED":
            return (
                "BLOCKED",
                "BLOCKED_STRUCTURAL_ISSUE",
                True,
                warnings,
                manual,
                "Inspect structural blockers before proceeding.",
            )
        if readiness == "VALIDATION_READY_WITH_NON_BLOCKING_MANUAL_REVIEW":
            return (
                "READABLE_WITH_MANUAL_REVIEW",
                "ELIGIBLE_WITH_NON_BLOCKING_MANUAL_REVIEW",
                False,
                warnings,
                manual,
                "Advance with manual review tracked.",
            )
        if readiness == "VALIDATION_READY_WITH_CONTROLLED_EXCLUSIONS":
            return (
                "READABLE_WITH_CONTROLLED_EXCLUSIONS",
                "ELIGIBLE_FOR_READING",
                False,
                warnings,
                manual,
                "Advance with controlled exclusions tracked.",
            )
        return (
            "READABLE",
            "ELIGIBLE_FOR_READING",
            False,
            warnings,
            manual,
            "Run intermediate normalization if needed.",
        )
    if parse:
        warnings.extend(parse.get("warnings", []))
        manual.extend(parse.get("manual_review_required", []))
        if parse.get("errors"):
            return (
                "BLOCKED",
                "BLOCKED_STRUCTURAL_ISSUE",
                True,
                warnings,
                manual,
                "Inspect parse errors before proceeding.",
            )
        return (
            "READABLE",
            "ELIGIBLE_FOR_READING",
            False,
            warnings,
            manual,
            "Run validation and normalization.",
        )
    return (
        "NOT_INSPECTED",
        "NOT_INSPECTED",
        True,
        warnings,
        manual,
        "Run strict parse and validation.",
    )


def _derive_presto_status(entry: dict[str, Any] | None) -> tuple[str, str, bool, list[str], list[str], str]:
    if not entry:
        return (
            "NOT_INSPECTED",
            "UNSUPPORTED_OR_UNKNOWN",
            True,
            ["PRESTO_REPORT_MISSING"],
            [],
            "Run inspect_presto_formats.",
        )
    support = entry.get("support_classification", "UNSUPPORTED_OR_UNKNOWN")
    warnings: list[str] = []
    manual: list[str] = []
    controlled = support in {"NEEDS_EXTERNAL_TOOL", "NEEDS_VENDOR_EXPORT", "UNSUPPORTED_OR_UNKNOWN"}
    if support == "DIRECTLY_READABLE":
        return (
            "READABLE",
            "ELIGIBLE_FOR_READING",
            False,
            warnings,
            manual,
            "Proceed to common inventory or downstream normalization.",
        )
    if support == "READABLE_WITH_STANDARD_LIBRARY":
        return (
            "READABLE_WITH_STANDARD_LIBRARY",
            "ELIGIBLE_WITH_NON_BLOCKING_MANUAL_REVIEW",
            False,
            warnings,
            manual,
            "Inspect with standard library and decide on export path.",
        )
    if support == "NEEDS_EXTERNAL_TOOL":
        warnings.append("PRESTO_NEEDS_EXTERNAL_TOOL")
        manual.append("PRESTO_NEEDS_EXTERNAL_TOOL")
        return (
            "NOT_DIRECTLY_READABLE",
            "NEEDS_EXTERNAL_TOOL",
            controlled,
            warnings,
            manual,
            "Use external tooling or vendor export.",
        )
    if support == "NEEDS_VENDOR_EXPORT":
        warnings.append("PRESTO_NEEDS_VENDOR_EXPORT")
        manual.append("PRESTO_NEEDS_VENDOR_EXPORT")
        return (
            "NOT_DIRECTLY_READABLE",
            "NEEDS_VENDOR_EXPORT",
            controlled,
            warnings,
            manual,
            "Require vendor export before further processing.",
        )
    warnings.append("PRESTO_UNKNOWN_SUPPORT")
    manual.append("PRESTO_UNKNOWN_SUPPORT")
    return (
        "NOT_INSPECTED",
        "UNSUPPORTED_OR_UNKNOWN",
        controlled,
        warnings,
        manual,
        "Keep as technical reference until support is clarified.",
    )


def build_multiformat_inventory(root: Path) -> dict[str, Any]:
    samples_path = root / SAMPLES_DIR
    generated_at = datetime.now(timezone.utc).isoformat()

    excel_report = _load_json_if_exists(root / EXCEL_REPORT)
    excel_validation = _load_json_if_exists(root / EXCEL_VALIDATION_REPORT)
    presto_report = _load_json_if_exists(root / PRESTO_REPORT)
    bc3_parse = _load_json_if_exists(root / BC3_PARSE_REPORT)
    bc3_validation = _load_json_if_exists(root / BC3_VALIDATION_REPORT)

    excel_idx = _excel_indexes(excel_report)
    bc3_idx = _bc3_indexes(bc3_parse, bc3_validation)
    presto_idx = _presto_index(presto_report)

    all_files = sorted([p for p in samples_path.rglob("*") if p.is_file()]) if samples_path.exists() else []
    entries: list[dict[str, Any]] = []
    controlled_exclusions: list[dict[str, Any]] = []
    warnings: set[str] = set()
    manual_review: set[str] = set()
    format_counts: dict[str, int] = {}
    readable_counts: dict[str, int] = {}
    eligibility_counts: dict[str, int] = {}

    for path in all_files:
        rel = _sanitize_path(str(path.relative_to(root)))
        fmt = _format_type_for_path(path)
        format_counts[fmt] = format_counts.get(fmt, 0) + 1

        if fmt == "EXCEL":
            if path.suffix.lower() in {".xls", ".xlsb"}:
                readable_status = "NOT_READABLE_LEGACY_EXCEL"
                eligibility_status = "NOT_ELIGIBLE_AUXILIARY_OR_CORRUPT"
                controlled = True
                item_warnings = ["LEGACY_EXCEL_NOT_SUPPORTED"]
                item_manual = ["LEGACY_EXCEL_NOT_SUPPORTED"]
                next_action = "Keep as reference only or convert to supported Excel."
                parser_or_reader_used = "none"
                output_report_path = None
            else:
                readable_status, eligibility_status, controlled, item_warnings, item_manual, next_action = _derive_excel_status(
                    excel_idx.get(rel)
                )
                parser_or_reader_used = "read_excel_full" if excel_idx.get(rel) else "none"
                output_report_path = EXCEL_REPORT if excel_idx.get(rel) else None
        elif fmt == "BC3":
            info = bc3_idx.get(rel)
            readable_status, eligibility_status, controlled, item_warnings, item_manual, next_action = _derive_bc3_status(
                info
            )
            parser_or_reader_used = "parse_bc3_strict" if info else "none"
            output_report_path = BC3_PARSE_REPORT if info else None
        elif fmt == "PRESTO":
            readable_status, eligibility_status, controlled, item_warnings, item_manual, next_action = _derive_presto_status(
                presto_idx.get(rel)
            )
            parser_or_reader_used = "inspect_presto_formats" if presto_idx.get(rel) else "none"
            output_report_path = PRESTO_REPORT if presto_idx.get(rel) else None
        else:
            readable_status = "IGNORED"
            eligibility_status = "NOT_IN_SCOPE"
            controlled = True
            item_warnings = ["FORMAT_OUT_OF_SCOPE"]
            item_manual = ["FORMAT_OUT_OF_SCOPE"]
            next_action = "Keep as reference only."
            parser_or_reader_used = "none"
            output_report_path = None

        warnings.update(item_warnings)
        manual_review.update(item_manual)
        readable_counts[readable_status] = readable_counts.get(readable_status, 0) + 1
        eligibility_counts[eligibility_status] = eligibility_counts.get(eligibility_status, 0) + 1
        if controlled:
            controlled_exclusions.append(
                {
                    "file_ref": {"relative_path_sanitized": rel},
                    "format_type": fmt,
                    "reason": eligibility_status,
                }
            )

        entries.append(
            {
                "file_ref": {
                    "relative_path_sanitized": rel,
                    "sanitized_id": _bc3_sanitized_id(bc3_idx.get(rel)) if fmt == "BC3" else None,
                },
                "format_type": fmt,
                "readable_status": readable_status,
                "parser_or_reader_used": parser_or_reader_used,
                "eligibility_status": eligibility_status,
                "controlled_exclusion": controlled,
                "output_report_path_sanitized": _sanitize_path(str(output_report_path)) if output_report_path else None,
                "warnings": item_warnings,
                "manual_review": item_manual,
                "next_action": next_action,
            }
        )

    return {
        "inventory_metadata": {
            "generated_at": generated_at,
            "inventory_stage": "phase_7_2_multiformat_common",
        },
        "source_reports": {
            "excel_full_reader": _sanitize_path(str(EXCEL_REPORT)),
            "excel_full_reader_validation": _sanitize_path(str(EXCEL_VALIDATION_REPORT)),
            "presto_diagnostics": _sanitize_path(str(PRESTO_REPORT)),
            "bc3_strict_parse": _sanitize_path(str(BC3_PARSE_REPORT)),
            "bc3_strict_validation": _sanitize_path(str(BC3_VALIDATION_REPORT)),
        },
        "files": entries,
        "global_summary": {
            "files_total": len(all_files),
            "format_counts": format_counts,
            "readable_counts": readable_counts,
            "eligibility_counts": eligibility_counts,
            "controlled_exclusions_count": len(controlled_exclusions),
            "manual_review_count": len(manual_review),
            "warning_count": len(warnings),
            "bc3_inventory_available": bc3_parse is not None,
            "excel_inventory_available": excel_report is not None,
            "presto_inventory_available": presto_report is not None,
        },
        "warnings": sorted(warnings),
        "manual_review": sorted(manual_review),
        "controlled_exclusions": controlled_exclusions,
    }


def write_reports(root: Path, payload: dict[str, Any]) -> tuple[Path, Path]:
    json_path = root / JSON_REPORT
    md_path = root / MD_REPORT
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    gs = payload.get("global_summary", {})
    lines = [
        "# Multiformat Inventory Report",
        "",
        "> Local multi-format inventory. Real-data artifacts may be sensitive and must remain outside Git.",
        "",
        f"- Generated at (UTC): {payload.get('inventory_metadata', {}).get('generated_at')}",
        f"- Files total: {gs.get('files_total', 0)}",
        f"- Controlled exclusions: {gs.get('controlled_exclusions_count', 0)}",
        "",
        "## By format",
        "",
    ]
    for fmt, count in sorted(gs.get("format_counts", {}).items()):
        lines.append(f"- {fmt}: {count}")
    lines.extend(["", "## Files", ""])
    for item in payload.get("files", [])[:50]:
        lines.append(f"### {item.get('file_ref', {}).get('relative_path_sanitized')}")
        lines.append(f"- Format: {item.get('format_type')}")
        lines.append(f"- Readable status: {item.get('readable_status')}")
        lines.append(f"- Eligibility status: {item.get('eligibility_status')}")
        lines.append(f"- Parser/reader used: {item.get('parser_or_reader_used')}")
        lines.append(f"- Controlled exclusion: {item.get('controlled_exclusion')}")
        lines.append(f"- Next action: {item.get('next_action')}")
        lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    payload = build_multiformat_inventory(root)
    json_path, md_path = write_reports(root, payload)

    print("Multiformat inventory summary")
    print(f"- Files total: {payload['global_summary']['files_total']}")
    print(f"- JSON output: {json_path.relative_to(root).as_posix()}")
    print(f"- Markdown output: {md_path.relative_to(root).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
