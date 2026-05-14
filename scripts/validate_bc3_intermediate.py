#!/usr/bin/env python3
"""Validate BC3 preliminary intermediate JSON structure."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

DEFAULT_INPUT = Path("reports/bc3_preliminary_parse/bc3_preliminary_parse_inventory.json")
REPORT_DIR = Path("reports/bc3_intermediate_validation")
JSON_REPORT = REPORT_DIR / "bc3_intermediate_validation_report.json"
MD_REPORT = REPORT_DIR / "bc3_intermediate_validation_report.md"

REQUIRED_ROOT_KEYS = ["metadata", "files", "global_summary"]
REQUIRED_FILE_KEYS = [
    "file_ref",
    "decode",
    "header",
    "records",
    "concepts",
    "relations",
    "units",
    "risk_flags",
    "errors",
    "warnings",
    "manual_review_required",
]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _entry_id(entry: dict[str, Any], idx: int) -> str:
    ref = entry.get("file_ref", {})
    return ref.get("sanitized_id") or f"FILE_{idx:02d}"


def validate_intermediate(report: dict[str, Any], source_path: str, unknown_threshold: int = 2) -> dict[str, Any]:
    validation_files: list[dict[str, Any]] = []
    blocking_errors: list[dict[str, Any]] = []
    manual_review_items: list[dict[str, Any]] = []
    warnings_items: list[dict[str, Any]] = []
    info_items: list[dict[str, Any]] = []

    missing_root = [k for k in REQUIRED_ROOT_KEYS if k not in report]
    if missing_root:
        blocking_errors.append(
            {
                "severity": "BLOCKED",
                "scope": "global",
                "code": "MISSING_ROOT_KEYS",
                "detail": ",".join(missing_root),
            }
        )
        return {
            "validation_metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "validator_stage": "phase_4_2_preliminary",
                "unknown_record_threshold": unknown_threshold,
                "status": "BLOCKED",
            },
            "source_parse_report": source_path,
            "files": [],
            "global_validation_summary": {
                "status": "BLOCKED",
                "files_count": 0,
                "files_with_errors": 0,
                "files_with_manual_review": 0,
                "files_with_warnings": 0,
            },
            "blocking_errors": blocking_errors,
            "manual_review_items": [],
            "warnings": [],
            "info": [],
        }

    files = report.get("files", [])
    if not isinstance(files, list):
        blocking_errors.append(
            {
                "severity": "BLOCKED",
                "scope": "global",
                "code": "FILES_NOT_A_LIST",
                "detail": "Root key 'files' must be a list.",
            }
        )
        files = []

    for idx, entry in enumerate(files, start=1):
        sid = _entry_id(entry, idx)
        file_errors: list[dict[str, str]] = []
        file_warnings: list[dict[str, str]] = []
        file_manual: list[dict[str, str]] = []
        file_info: list[dict[str, str]] = []

        missing_keys = [k for k in REQUIRED_FILE_KEYS if k not in entry]
        if missing_keys:
            file_errors.append(
                {
                    "severity": "ERROR",
                    "code": "MISSING_FILE_KEYS",
                    "detail": ",".join(missing_keys),
                }
            )

        header = entry.get("header", {})
        if not header.get("has_v"):
            file_errors.append(
                {
                    "severity": "ERROR",
                    "code": "MISSING_V_HEADER",
                    "detail": "~V header not detected.",
                }
            )

        concepts = entry.get("concepts", [])
        if not concepts:
            file_warnings.append(
                {
                    "severity": "WARNING",
                    "code": "MISSING_C_CONCEPTS",
                    "detail": "No ~C concepts parsed.",
                }
            )
            file_manual.append(
                {
                    "severity": "MANUAL_REVIEW_REQUIRED",
                    "code": "CONCEPTS_ABSENT_REVIEW",
                    "detail": "Review if source BC3 has concepts not parsed.",
                }
            )

        concept_codes = {
            str(c.get("code", "")).strip()
            for c in concepts
            if isinstance(c, dict) and str(c.get("code", "")).strip()
        }
        relations = entry.get("relations", {}).get("links", [])
        for rel in relations:
            parent = str(rel.get("parent_code", "")).strip()
            child = str(rel.get("child_code", "")).strip()
            if parent and concept_codes and parent not in concept_codes:
                file_warnings.append(
                    {
                        "severity": "WARNING",
                        "code": "RELATION_PARENT_NOT_IN_CONCEPTS",
                        "detail": parent,
                    }
                )
                file_manual.append(
                    {
                        "severity": "MANUAL_REVIEW_REQUIRED",
                        "code": "RELATION_ORPHAN_PARENT",
                        "detail": parent,
                    }
                )
            if child and concept_codes and child not in concept_codes:
                file_warnings.append(
                    {
                        "severity": "WARNING",
                        "code": "RELATION_CHILD_NOT_IN_CONCEPTS",
                        "detail": child,
                    }
                )
                file_manual.append(
                    {
                        "severity": "MANUAL_REVIEW_REQUIRED",
                        "code": "RELATION_ORPHAN_CHILD",
                        "detail": child,
                    }
                )

        unknowns = entry.get("records", {}).get("unknown_record_types", [])
        if isinstance(unknowns, list) and unknowns:
            if len(unknowns) > unknown_threshold:
                file_manual.append(
                    {
                        "severity": "MANUAL_REVIEW_REQUIRED",
                        "code": "UNKNOWN_RECORDS_OVER_THRESHOLD",
                        "detail": f"{len(unknowns)}>{unknown_threshold}",
                    }
                )
            else:
                file_warnings.append(
                    {
                        "severity": "WARNING",
                        "code": "UNKNOWN_RECORDS_UNDER_THRESHOLD",
                        "detail": f"{len(unknowns)}<={unknown_threshold}",
                    }
                )

        manual_reasons = entry.get("manual_review_required", [])
        if file_manual and (not isinstance(manual_reasons, list) or len(manual_reasons) == 0):
            file_manual.append(
                {
                    "severity": "MANUAL_REVIEW_REQUIRED",
                    "code": "MISSING_MANUAL_REASONS",
                    "detail": "manual_review_required is empty while manual flags exist.",
                }
            )

        if not file_errors and not file_warnings and not file_manual:
            file_info.append(
                {
                    "severity": "INFO",
                    "code": "STRUCTURE_VALID",
                    "detail": "Preliminary structure is coherent.",
                }
            )

        status = "VALID"
        if file_errors:
            status = "ERROR"
        elif file_manual:
            status = "MANUAL_REVIEW_REQUIRED"
        elif file_warnings:
            status = "WARNING"

        validation_files.append(
            {
                "sanitized_id": sid,
                "relative_path": entry.get("file_ref", {}).get("relative_path"),
                "status": status,
                "errors": file_errors,
                "warnings": file_warnings,
                "manual_review_items": file_manual,
                "info": file_info,
            }
        )
        blocking_errors.extend({"file": sid, **item} for item in file_errors)
        manual_review_items.extend({"file": sid, **item} for item in file_manual)
        warnings_items.extend({"file": sid, **item} for item in file_warnings)
        info_items.extend({"file": sid, **item} for item in file_info)

    global_status = "VALID"
    if any(item.get("severity") == "BLOCKED" for item in blocking_errors):
        global_status = "BLOCKED"
    elif blocking_errors:
        global_status = "ERROR"
    elif manual_review_items:
        global_status = "MANUAL_REVIEW_REQUIRED"
    elif warnings_items:
        global_status = "WARNING"

    return {
        "validation_metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "validator_stage": "phase_4_2_preliminary",
            "unknown_record_threshold": unknown_threshold,
            "status": global_status,
        },
        "source_parse_report": source_path,
        "files": validation_files,
        "global_validation_summary": {
            "status": global_status,
            "files_count": len(validation_files),
            "files_with_errors": sum(1 for f in validation_files if f["errors"]),
            "files_with_manual_review": sum(1 for f in validation_files if f["manual_review_items"]),
            "files_with_warnings": sum(1 for f in validation_files if f["warnings"]),
        },
        "blocking_errors": blocking_errors,
        "manual_review_items": manual_review_items,
        "warnings": warnings_items,
        "info": info_items,
    }


def write_outputs(root: Path, report: dict[str, Any]) -> tuple[Path, Path]:
    json_path = root / JSON_REPORT
    md_path = root / MD_REPORT
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    lines: list[str] = []
    vm = report.get("validation_metadata", {})
    gs = report.get("global_validation_summary", {})
    lines.append("# BC3 Intermediate Validation Report")
    lines.append("")
    lines.append("> Local validation output. Real-data reports may be sensitive and must remain outside Git.")
    lines.append("")
    lines.append(f"- Generated at (UTC): {vm.get('generated_at')}")
    lines.append(f"- Status: {vm.get('status')}")
    lines.append(f"- Source parse report: {report.get('source_parse_report')}")
    lines.append(f"- Files count: {gs.get('files_count', 0)}")
    lines.append(f"- Files with errors: {gs.get('files_with_errors', 0)}")
    lines.append(f"- Files with manual review: {gs.get('files_with_manual_review', 0)}")
    lines.append(f"- Files with warnings: {gs.get('files_with_warnings', 0)}")
    lines.append("")
    lines.append("## Blocking Errors")
    lines.append("")
    if report.get("blocking_errors"):
        for item in report["blocking_errors"]:
            lines.append(f"- {item.get('file', 'global')}: {item['code']} ({item['detail']})")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Manual Review")
    lines.append("")
    if report.get("manual_review_items"):
        for item in report["manual_review_items"]:
            lines.append(f"- {item.get('file', 'global')}: {item['code']} ({item['detail']})")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Warnings")
    lines.append("")
    if report.get("warnings"):
        for item in report["warnings"]:
            lines.append(f"- {item.get('file', 'global')}: {item['code']} ({item['detail']})")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Files")
    lines.append("")
    for file_report in report.get("files", []):
        lines.append(f"### {file_report['sanitized_id']} - {file_report['status']}")
        lines.append(f"- Path: {file_report.get('relative_path')}")
        lines.append(f"- Errors: {len(file_report['errors'])}")
        lines.append(f"- Manual review items: {len(file_report['manual_review_items'])}")
        lines.append(f"- Warnings: {len(file_report['warnings'])}")
        lines.append("")
    if not report.get("files"):
        lines.append("No files to validate.")
        lines.append("")
    lines.append("## Recommendation")
    lines.append("")
    status = vm.get("status")
    if status in {"BLOCKED", "ERROR"}:
        lines.append("- Do not proceed to next phase until structural issues are fixed.")
    elif status == "MANUAL_REVIEW_REQUIRED":
        lines.append("- Proceed only after targeted manual review of flagged files.")
    elif status == "WARNING":
        lines.append("- Proceed with caution and keep warnings tracked.")
    else:
        lines.append("- Validation baseline is acceptable for next controlled phase.")

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
    report = validate_intermediate(source, str(input_path))
    json_path, md_path = write_outputs(root, report)
    print("BC3 intermediate validation summary")
    print(f"- Source: {input_path}")
    print(f"- Status: {report['validation_metadata']['status']}")
    print(f"- JSON output: {json_path.relative_to(root).as_posix()}")
    print(f"- Markdown output: {md_path.relative_to(root).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
