#!/usr/bin/env python3
"""Strict cross validation for BC3 strict parse output (~C/~D coherence)."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

DEFAULT_INPUT = Path("reports/bc3_strict_parse/bc3_strict_parse_inventory.json")
REPORT_DIR = Path("reports/bc3_strict_validation")
JSON_REPORT = REPORT_DIR / "bc3_strict_validation_report.json"
MD_REPORT = REPORT_DIR / "bc3_strict_validation_report.md"

READINESS_BLOCKED = "VALIDATION_BLOCKED"
READINESS_NON_BLOCKING = "VALIDATION_READY_WITH_NON_BLOCKING_MANUAL_REVIEW"
READINESS_CONTROLLED_EXCLUSIONS = "VALIDATION_READY_WITH_CONTROLLED_EXCLUSIONS"
READINESS_READY = "VALIDATION_READY_FOR_STRICTER_PARSER_DESIGN"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical(code: str) -> str:
    c = str(code or "").strip()
    return c[:-1] if c.endswith("#") else c


def validate_strict(report: dict[str, Any], source_path: str) -> dict[str, Any]:
    blocking_errors: list[dict[str, Any]] = []
    manual_review_items: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    files_out: list[dict[str, Any]] = []

    for key in ("metadata", "files", "global_summary"):
        if key not in report:
            blocking_errors.append(
                {
                    "scope": "global",
                    "severity": "BLOCKED",
                    "code": f"MISSING_{key.upper()}",
                    "detail": f"Missing root key: {key}",
                }
            )

    if blocking_errors:
        return {
            "validation_metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "validator_stage": "phase_4_7_strict_cross_validation",
                "status": "ERROR",
            },
            "source_strict_parse_report": source_path,
            "files": [],
            "blocking_errors": blocking_errors,
            "manual_review_items": [],
            "warnings": [],
            "global_validation_summary": {
                "files_count": 0,
                "files_with_errors": 0,
                "files_with_manual_review": 0,
                "full_corpus_status": "BLOCKED",
                "valid_subset_status": "BLOCKED",
                "eligible_files_count": 0,
                "excluded_files_count": 0,
                "controlled_exclusions": False,
                "can_advance_with_valid_subset": False,
            },
            "validation_readiness": {
                "global": READINESS_BLOCKED,
                "phase_4_next_recommendation": "Fix strict parse contract before proceeding.",
            },
            "phase_4_next_recommendation": "Fix strict parse contract before proceeding.",
        }

    files = report.get("files", [])
    exclusions = report.get("controlled_exclusions", [])
    files_total = len(files)

    structurally_blocked = 0
    files_with_manual = 0
    files_with_errors = 0

    for entry in files:
        sid = entry.get("file_ref", {}).get("sanitized_id", "UNKNOWN")
        parsed = entry.get("parsed", {})
        errors: list[dict[str, str]] = []
        manual: list[dict[str, str]] = []

        header = parsed.get("header")
        concepts = parsed.get("concepts", [])
        relations = parsed.get("relations", [])

        if not header:
            errors.append({"code": "MISSING_V_HEADER", "detail": "Strict parse header missing."})
        if not concepts:
            errors.append({"code": "MISSING_C_CONCEPTS", "detail": "Strict parse concepts missing."})

        concept_set = {_canonical(c.get("code", "")) for c in concepts if c.get("code")}
        orphan_rel = 0
        for rel in relations:
            p = _canonical(rel.get("parent_code", ""))
            c = _canonical(rel.get("child_code", ""))
            if concept_set and ((p and p not in concept_set) or (c and c not in concept_set)):
                orphan_rel += 1

        rel_count = len(relations)
        orphan_ratio = (orphan_rel / rel_count) if rel_count else 0.0
        if orphan_rel > 0 and rel_count > 0:
            if orphan_rel >= 15 and orphan_ratio >= 0.40:
                errors.append(
                    {
                        "code": "ORPHAN_RELATIONS_BLOCKING",
                        "detail": f"{orphan_rel}/{rel_count} orphan relations ratio={orphan_ratio:.2f}",
                    }
                )
            else:
                manual.append(
                    {
                        "code": "RELATION_ORPHAN_CHILD_NON_BLOCKING",
                        "detail": f"{orphan_rel}/{rel_count} orphan relations ratio={orphan_ratio:.2f}",
                    }
                )

        status = "VALID"
        file_readiness = READINESS_READY
        if errors:
            status = "ERROR"
            file_readiness = READINESS_BLOCKED
            files_with_errors += 1
            structurally_blocked += 1
        elif manual:
            status = "MANUAL_REVIEW_REQUIRED"
            file_readiness = READINESS_NON_BLOCKING
            files_with_manual += 1

        files_out.append(
            {
                "sanitized_id": sid,
                "relative_path": entry.get("file_ref", {}).get("relative_path"),
                "status": status,
                "validation_readiness": file_readiness,
                "errors": errors,
                "manual_review_items": manual,
                "unknown_preserved_count": len(entry.get("unknown", [])),
                "unsupported_preserved_count": len(entry.get("unsupported", [])),
            }
        )

        for item in errors:
            blocking_errors.append({"file": sid, **item})
        for item in manual:
            manual_review_items.append({"file": sid, **item})

    excluded_files_count = len(exclusions)
    eligible_files_count = files_total
    controlled_exclusions = excluded_files_count > 0
    can_advance_with_valid_subset = eligible_files_count > 0 and structurally_blocked == 0
    valid_subset_status = "ADVANCE_ALLOWED" if can_advance_with_valid_subset else "BLOCKED"
    full_corpus_status = "BLOCKED" if structurally_blocked > 0 else "NOT_BLOCKED"

    if structurally_blocked > 0:
        readiness = READINESS_BLOCKED
        status = "ERROR"
        recommendation = "Resolve structural blockers before advancing strict flow."
    elif controlled_exclusions:
        readiness = READINESS_CONTROLLED_EXCLUSIONS
        status = "MANUAL_REVIEW_REQUIRED" if files_with_manual > 0 else "VALID"
        recommendation = "Advance with controlled exclusions and tracked manual review."
    elif files_with_manual > 0:
        readiness = READINESS_NON_BLOCKING
        status = "MANUAL_REVIEW_REQUIRED"
        recommendation = "Advance with non-blocking manual review tracked."
    else:
        readiness = READINESS_READY
        status = "VALID"
        recommendation = "Strict cross validation ready for next controlled phase."

    return {
        "validation_metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "validator_stage": "phase_4_7_strict_cross_validation",
            "status": status,
        },
        "source_strict_parse_report": source_path,
        "files": files_out,
        "blocking_errors": blocking_errors,
        "manual_review_items": manual_review_items,
        "warnings": warnings,
        "global_validation_summary": {
            "files_count": files_total,
            "files_with_errors": files_with_errors,
            "files_with_manual_review": files_with_manual,
            "full_corpus_status": full_corpus_status,
            "valid_subset_status": valid_subset_status,
            "eligible_files_count": eligible_files_count,
            "excluded_files_count": excluded_files_count,
            "controlled_exclusions": controlled_exclusions,
            "can_advance_with_valid_subset": can_advance_with_valid_subset,
        },
        "validation_readiness": {
            "global": readiness,
            "files": [{"sanitized_id": f["sanitized_id"], "readiness": f["validation_readiness"]} for f in files_out],
            "phase_4_next_recommendation": recommendation,
        },
        "phase_4_next_recommendation": recommendation,
        "controlled_exclusions": exclusions,
    }


def write_outputs(root: Path, report: dict[str, Any]) -> tuple[Path, Path]:
    json_path = root / JSON_REPORT
    md_path = root / MD_REPORT
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    gs = report.get("global_validation_summary", {})
    vm = report.get("validation_metadata", {})
    lines = [
        "# BC3 Strict Validation Report",
        "",
        "> Local validation output. Real-data reports may be sensitive and must remain outside Git.",
        "",
        f"- Generated at (UTC): {vm.get('generated_at')}",
        f"- Status: {vm.get('status')}",
        f"- Validation readiness: {report.get('validation_readiness', {}).get('global')}",
        f"- Full corpus status: {gs.get('full_corpus_status')}",
        f"- Valid subset status: {gs.get('valid_subset_status')}",
        "",
        "## Blocking Errors",
        "",
    ]
    if report.get("blocking_errors"):
        for item in report["blocking_errors"]:
            lines.append(f"- {item.get('file', 'global')}: {item['code']} ({item['detail']})")
    else:
        lines.append("- none")

    lines.extend(["", "## Manual Review", ""])
    if report.get("manual_review_items"):
        for item in report["manual_review_items"]:
            lines.append(f"- {item.get('file')}: {item['code']} ({item['detail']})")
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
    report = validate_strict(source, str(input_path))
    json_path, md_path = write_outputs(root, report)

    print("BC3 strict validation summary")
    print(f"- Source: {input_path}")
    print(f"- Status: {report['validation_metadata']['status']}")
    print(f"- Readiness: {report['validation_readiness']['global']}")
    print(f"- JSON output: {json_path.relative_to(root).as_posix()}")
    print(f"- Markdown output: {md_path.relative_to(root).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
