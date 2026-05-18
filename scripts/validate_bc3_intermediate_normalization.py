#!/usr/bin/env python3
"""Validate BC3 intermediate normalization contract (phase 5.2)."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

DEFAULT_INPUT_INVENTORY = Path("reports/bc3_intermediate_normalization/bc3_intermediate_normalization_inventory.json")
DEFAULT_INPUT_REPORT = Path("reports/bc3_intermediate_normalization/bc3_intermediate_normalization_report.json")
REPORT_DIR = Path("reports/bc3_intermediate_normalization_validation")
JSON_REPORT = REPORT_DIR / "bc3_intermediate_normalization_validation_report.json"
MD_REPORT = REPORT_DIR / "bc3_intermediate_normalization_validation_report.md"

SEVERITY_INFO = "INFO"
SEVERITY_WARNING = "WARNING"
SEVERITY_ERROR = "ERROR"
SEVERITY_MANUAL = "MANUAL_REVIEW_REQUIRED"
SEVERITY_BLOCKED = "BLOCKED"

REQUIRED_ROOT_KEYS = [
    "normalization_metadata",
    "source_reports",
    "corpus_status",
    "files",
    "global_summary",
    "controlled_exclusions",
]

REQUIRED_FILE_KEYS = [
    "file_ref",
    "source_trace",
    "chapters",
    "cost_items",
    "relations",
    "units",
    "descriptions",
    "measurement_signals",
    "economic_signals",
    "validation_flags",
    "manual_review",
    "unknown_or_unsupported",
]

FORBIDDEN_KEYWORDS = [
    "master",
    "ratio",
    "ratios",
    "consolidated_amount",
    "final_category",
    "final_categories",
    "category_mapping",
]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _find_forbidden_paths(node: Any, path: str = "") -> list[str]:
    hits: list[str] = []
    if isinstance(node, dict):
        for k, v in node.items():
            kp = f"{path}.{k}" if path else k
            lower = k.lower()
            if any(token in lower for token in FORBIDDEN_KEYWORDS):
                hits.append(kp)
            hits.extend(_find_forbidden_paths(v, kp))
    elif isinstance(node, list):
        for idx, v in enumerate(node):
            hits.extend(_find_forbidden_paths(v, f"{path}[{idx}]"))
    return hits


def _relation_has_trace(rel: dict[str, Any]) -> bool:
    if not isinstance(rel, dict):
        return False
    if rel.get("line_number") is not None:
        return True
    trace = rel.get("source_trace")
    if isinstance(trace, dict) and trace:
        return True
    return False


def validate_intermediate_normalization(report: dict[str, Any], source_path: str) -> dict[str, Any]:
    blocking_errors: list[dict[str, Any]] = []
    manual_review_items: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    info: list[dict[str, Any]] = []
    files_out: list[dict[str, Any]] = []

    for key in REQUIRED_ROOT_KEYS:
        if key not in report:
            blocking_errors.append(
                {
                    "scope": "global",
                    "severity": SEVERITY_BLOCKED,
                    "code": f"MISSING_{key.upper()}",
                    "detail": f"Missing root key: {key}",
                }
            )

    if blocking_errors:
        return {
            "validation_metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "validator_stage": "phase_5_2_intermediate_normalization_contract",
                "status": SEVERITY_ERROR,
            },
            "source_normalization_report": source_path,
            "corpus_status": {
                "full_corpus_status": "BLOCKED",
                "valid_subset_status": "BLOCKED",
                "can_advance_with_valid_subset": False,
            },
            "files": [],
            "global_validation_summary": {
                "files_count": 0,
                "files_with_errors": 0,
                "files_with_manual_review": 0,
                "contract_status": "BLOCKED",
            },
            "blocking_errors": blocking_errors,
            "manual_review_items": [],
            "warnings": [],
            "info": [],
        }

    files = report.get("files", [])
    controlled_exclusions = report.get("controlled_exclusions", [])
    files_with_errors = 0
    files_with_manual = 0

    for item in files:
        sid = item.get("file_ref", {}).get("sanitized_id", "UNKNOWN")
        relative_path = item.get("file_ref", {}).get("relative_path")
        file_errors: list[dict[str, Any]] = []
        file_manual: list[dict[str, Any]] = []
        file_warnings: list[dict[str, Any]] = []

        for key in REQUIRED_FILE_KEYS:
            if key not in item:
                file_errors.append(
                    {
                        "code": f"MISSING_FILE_FIELD_{key.upper()}",
                        "detail": f"Missing file field: {key}",
                    }
                )

        source_trace = item.get("source_trace")
        if not isinstance(source_trace, dict) or not source_trace:
            file_errors.append({"code": "MISSING_SOURCE_TRACE", "detail": "source_trace missing or empty."})

        if not isinstance(item.get("chapters", None), list):
            file_errors.append({"code": "INVALID_CHAPTERS_TYPE", "detail": "chapters must be a list."})
        if not isinstance(item.get("cost_items", None), list):
            file_errors.append({"code": "INVALID_COST_ITEMS_TYPE", "detail": "cost_items must be a list."})

        for rel in item.get("relations", []):
            if not _relation_has_trace(rel):
                file_errors.append(
                    {
                        "code": "RELATION_TRACEABILITY_MISSING",
                        "detail": "A relation entry is missing source traceability.",
                    }
                )
                break

        for sig in item.get("economic_signals", []):
            if sig.get("consolidated") is True:
                file_errors.append(
                    {
                        "code": "ECONOMIC_SIGNAL_CONSOLIDATED_FORBIDDEN",
                        "detail": "Economic signals must remain non-consolidated in this phase.",
                    }
                )
                break

        for sig in item.get("measurement_signals", []):
            if sig.get("consolidated") is True:
                file_errors.append(
                    {
                        "code": "MEASUREMENT_SIGNAL_CONSOLIDATED_FORBIDDEN",
                        "detail": "Measurement signals must remain non-consolidated in this phase.",
                    }
                )
                break

        manual_review = item.get("manual_review", [])
        if manual_review:
            file_manual.append(
                {
                    "code": "MANUAL_REVIEW_PRESERVED",
                    "detail": f"Manual review entries preserved: {len(manual_review)}",
                }
            )

        unknown_bag = item.get("unknown_or_unsupported", {})
        if isinstance(unknown_bag, dict):
            unknown_count = len(unknown_bag.get("unknown", []))
            unsupported_count = len(unknown_bag.get("unsupported", []))
            if unknown_count or unsupported_count:
                file_warnings.append(
                    {
                        "code": "UNKNOWN_OR_UNSUPPORTED_PRESERVED",
                        "detail": f"unknown={unknown_count}, unsupported={unsupported_count}",
                    }
                )

        file_status = SEVERITY_INFO
        if file_errors:
            files_with_errors += 1
            file_status = SEVERITY_ERROR
        elif file_manual:
            files_with_manual += 1
            file_status = SEVERITY_MANUAL

        files_out.append(
            {
                "sanitized_id": sid,
                "relative_path": relative_path,
                "status": file_status,
                "errors": file_errors,
                "manual_review_items": file_manual,
                "warnings": file_warnings,
            }
        )

        for err in file_errors:
            blocking_errors.append({"file": sid, "severity": SEVERITY_BLOCKED, **err})
        for man in file_manual:
            manual_review_items.append({"file": sid, "severity": SEVERITY_MANUAL, **man})
        for warn in file_warnings:
            warnings.append({"file": sid, "severity": SEVERITY_WARNING, **warn})

    forbidden_paths = _find_forbidden_paths(report)
    if forbidden_paths:
        for path in forbidden_paths:
            blocking_errors.append(
                {
                    "scope": "global",
                    "severity": SEVERITY_BLOCKED,
                    "code": "FORBIDDEN_FIELD_PRESENT",
                    "detail": f"Forbidden field detected: {path}",
                }
            )

    if controlled_exclusions:
        info.append(
            {
                "severity": SEVERITY_INFO,
                "code": "CONTROLLED_EXCLUSIONS_PRESERVED",
                "detail": f"Controlled exclusions preserved: {len(controlled_exclusions)}",
            }
        )

    contract_status = "BLOCKED" if blocking_errors else "VALID"
    validation_status = SEVERITY_ERROR if blocking_errors else (SEVERITY_MANUAL if manual_review_items else SEVERITY_INFO)
    corpus_status = report.get("corpus_status", {})

    return {
        "validation_metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "validator_stage": "phase_5_2_intermediate_normalization_contract",
            "status": validation_status,
        },
        "source_normalization_report": source_path,
        "corpus_status": {
            "full_corpus_status": corpus_status.get("full_corpus_status", "UNKNOWN"),
            "valid_subset_status": corpus_status.get("valid_subset_status", "UNKNOWN"),
            "can_advance_with_valid_subset": corpus_status.get("can_advance_with_valid_subset", False),
        },
        "files": files_out,
        "global_validation_summary": {
            "files_count": len(files),
            "files_with_errors": files_with_errors,
            "files_with_manual_review": files_with_manual,
            "controlled_exclusions_count": len(controlled_exclusions),
            "contract_status": contract_status,
        },
        "blocking_errors": blocking_errors,
        "manual_review_items": manual_review_items,
        "warnings": warnings,
        "info": info,
    }


def write_outputs(root: Path, report: dict[str, Any]) -> tuple[Path, Path]:
    json_path = root / JSON_REPORT
    md_path = root / MD_REPORT
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    gs = report.get("global_validation_summary", {})
    vm = report.get("validation_metadata", {})
    lines = [
        "# BC3 Intermediate Normalization Validation Report",
        "",
        "> Local validation output. Real-data reports may be sensitive and must remain outside Git.",
        "",
        f"- Generated at (UTC): {vm.get('generated_at')}",
        f"- Validation status: {vm.get('status')}",
        f"- Contract status: {gs.get('contract_status')}",
        f"- Files: {gs.get('files_count')}",
        f"- Files with errors: {gs.get('files_with_errors')}",
        f"- Files with manual review: {gs.get('files_with_manual_review')}",
        "",
        "## Blocking Errors",
        "",
    ]

    if report.get("blocking_errors"):
        for item in report["blocking_errors"]:
            who = item.get("file", item.get("scope", "global"))
            lines.append(f"- {who}: {item.get('code')} ({item.get('detail')})")
    else:
        lines.append("- none")

    lines.extend(["", "## Manual Review", ""])
    if report.get("manual_review_items"):
        for item in report["manual_review_items"]:
            lines.append(f"- {item.get('file')}: {item.get('code')} ({item.get('detail')})")
    else:
        lines.append("- none")

    lines.extend(["", "## Warnings", ""])
    if report.get("warnings"):
        for item in report["warnings"]:
            lines.append(f"- {item.get('file', 'global')}: {item.get('code')} ({item.get('detail')})")
    else:
        lines.append("- none")

    lines.extend(["", "## Files", "", "| sanitized_id | status | errors | manual_review |", "|---|---|---:|---:|"])
    for item in report.get("files", []):
        lines.append(
            f"| {item.get('sanitized_id')} | {item.get('status')} | {len(item.get('errors', []))} | {len(item.get('manual_review_items', []))} |"
        )

    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def _resolve_input(root: Path, argv: list[str]) -> Path:
    if len(argv) > 1:
        return Path(argv[1]).resolve()

    inventory = root / DEFAULT_INPUT_INVENTORY
    if inventory.exists():
        return inventory

    report = root / DEFAULT_INPUT_REPORT
    return report


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    input_path = _resolve_input(root, sys.argv)

    if not input_path.exists():
        print(
            "ERROR: normalization input not found. "
            f"Tried: {root / DEFAULT_INPUT_INVENTORY} and {root / DEFAULT_INPUT_REPORT}"
        )
        return 1

    source = _load_json(input_path)
    report = validate_intermediate_normalization(source, str(input_path))
    json_path, md_path = write_outputs(root, report)

    print("BC3 intermediate normalization contract validation summary")
    print(f"- Source: {input_path}")
    print(f"- Validation status: {report['validation_metadata']['status']}")
    print(f"- Contract status: {report['global_validation_summary']['contract_status']}")
    print(f"- JSON output: {json_path.relative_to(root).as_posix()}")
    print(f"- Markdown output: {md_path.relative_to(root).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
