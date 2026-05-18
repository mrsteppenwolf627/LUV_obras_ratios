#!/usr/bin/env python3
"""Strict BC3 parser over valid subset based on intermediate eligibility."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Any

DEFAULT_PARSE_INPUT = Path("reports/bc3_preliminary_parse/bc3_preliminary_parse_inventory.json")
DEFAULT_VALIDATION_INPUT = Path("reports/bc3_intermediate_validation/bc3_intermediate_validation_report.json")
REPORT_DIR = Path("reports/bc3_strict_parse")
JSON_REPORT = REPORT_DIR / "bc3_strict_parse_inventory.json"
MD_REPORT = REPORT_DIR / "bc3_strict_parse_inventory_report.md"

ELIGIBLE_STATUSES = {
    "ELIGIBLE_FOR_PRELIMINARY_FLOW",
    "ELIGIBLE_WITH_NON_BLOCKING_MANUAL_REVIEW",
}

REG_TYPE_RE = re.compile(r"^(~[A-Za-z])")


def detect_encoding(raw: bytes) -> dict[str, str]:
    if not raw:
        return {"encoding": "unknown", "confidence": "low", "strategy": "empty_file"}
    try:
        raw.decode("utf-8")
        return {"encoding": "utf-8", "confidence": "high", "strategy": "utf-8"}
    except UnicodeDecodeError:
        pass
    try:
        raw.decode("cp1252")
        return {"encoding": "cp1252", "confidence": "medium", "strategy": "cp1252_fallback"}
    except UnicodeDecodeError:
        return {"encoding": "binary_or_unknown", "confidence": "low", "strategy": "decode_failed"}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_eligibility_index(validation_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for item in validation_report.get("files", []):
        sid = item.get("sanitized_id", "")
        if sid:
            out[sid] = item
    return out


def parse_bc3_file_strict(path: Path, root: Path, sanitized_id: str, relative_path: str) -> dict[str, Any]:
    raw = path.read_bytes()
    decode = detect_encoding(raw)
    result: dict[str, Any] = {
        "file_ref": {
            "sanitized_id": sanitized_id,
            "relative_path": relative_path,
            "extension": path.suffix.lower(),
            "size_bytes": path.stat().st_size,
        },
        "decode": decode,
        "parsed": {"header": None, "concepts": [], "relations": []},
        "unknown": [],
        "unsupported": [],
        "errors": [],
        "warnings": [],
        "manual_review_required": [],
        "traceability": {"lines_processed": 0, "parsed_records_count": 0},
    }

    if decode["encoding"] == "binary_or_unknown":
        result["errors"].append("DECODE_FAILED")
        result["manual_review_required"].append("NOT_DECODABLE_STRICT")
        return result

    lines = raw.decode(decode["encoding"], errors="replace").splitlines()
    result["traceability"]["lines_processed"] = len(lines)

    concept_codes: set[str] = set()
    relation_orphans = 0

    for idx, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or not line.startswith("~"):
            continue
        match = REG_TYPE_RE.match(line)
        if not match:
            result["unknown"].append({"line_number": idx, "raw": line, "reason": "malformed_record_prefix"})
            continue

        record_type = match.group(1).upper()
        payload = line[2:].lstrip("|")
        fields = payload.split("|")

        if record_type == "~V":
            if result["parsed"]["header"] is None:
                result["parsed"]["header"] = {"line_number": idx, "raw": line}
            else:
                result["warnings"].append("MULTIPLE_V_HEADERS")
            result["traceability"]["parsed_records_count"] += 1
            continue

        if record_type == "~C":
            code = (fields[0].split("\\", 1)[0].strip() if fields else "")
            result["parsed"]["concepts"].append({"line_number": idx, "record_type": "~C", "code": code})
            if code:
                concept_codes.add(code[:-1] if code.endswith("#") else code)
            result["traceability"]["parsed_records_count"] += 1
            continue

        if record_type == "~D":
            parent = (fields[0].split("\\", 1)[0].strip() if len(fields) >= 1 else "")
            child = (fields[1].split("\\", 1)[0].strip() if len(fields) >= 2 else "")
            result["parsed"]["relations"].append(
                {
                    "line_number": idx,
                    "record_type": "~D",
                    "parent_code": parent,
                    "child_code": child,
                }
            )
            result["traceability"]["parsed_records_count"] += 1
            continue

        if record_type.startswith("~"):
            result["unsupported"].append({"line_number": idx, "record_type": record_type, "raw": line})
        else:
            result["unknown"].append({"line_number": idx, "raw": line, "reason": "non_standard_record_type"})

    if result["parsed"]["header"] is None:
        result["errors"].append("MISSING_V_HEADER")
    if not result["parsed"]["concepts"]:
        result["errors"].append("MISSING_C_CONCEPTS")
    if not result["parsed"]["relations"]:
        result["errors"].append("MISSING_D_RELATIONS")

    for rel in result["parsed"]["relations"]:
        parent = rel.get("parent_code", "")
        child = rel.get("child_code", "")
        p = parent[:-1] if parent.endswith("#") else parent
        c = child[:-1] if child.endswith("#") else child
        if concept_codes and ((p and p not in concept_codes) or (c and c not in concept_codes)):
            relation_orphans += 1

    rel_count = len(result["parsed"]["relations"])
    if relation_orphans > 0 and rel_count > 0:
        result["manual_review_required"].append(
            f"PARTIAL_ORPHAN_RELATIONS:{relation_orphans}/{rel_count}"
        )

    return result


def parse_strict(parse_report: dict[str, Any], validation_report: dict[str, Any], root: Path) -> dict[str, Any]:
    eligibility = _build_eligibility_index(validation_report)
    strict_files: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []
    eligible_files_count = 0
    excluded_files_count = 0
    structurally_blocked_count = 0

    for entry in parse_report.get("files", []):
        ref = entry.get("file_ref", {})
        sid = ref.get("sanitized_id", "")
        rel = ref.get("relative_path", "")
        if not sid or not rel:
            continue

        eligibility_entry = eligibility.get(sid, {})
        file_status = eligibility_entry.get("file_eligibility_status", "")

        if file_status not in ELIGIBLE_STATUSES:
            excluded_files_count += 1
            exclusions.append(
                {
                    "sanitized_id": sid,
                    "relative_path": rel,
                    "file_eligibility_status": file_status or "UNKNOWN",
                    "file_eligibility_reason": eligibility_entry.get("file_eligibility_reason", "Not eligible in validation report."),
                }
            )
            if file_status == "BLOCKED_STRUCTURAL_ISSUE":
                structurally_blocked_count += 1
            continue

        eligible_files_count += 1
        strict_path = root / rel
        try:
            strict_entry = parse_bc3_file_strict(strict_path, root, sid, rel)
        except Exception as exc:
            strict_entry = {
                "file_ref": {"sanitized_id": sid, "relative_path": rel},
                "parsed": {"header": None, "concepts": [], "relations": []},
                "unknown": [],
                "unsupported": [],
                "errors": [f"READ_OR_PARSE_ERROR:{exc}"],
                "warnings": [],
                "manual_review_required": ["STRICT_PARSE_RUNTIME_FAILURE"],
                "traceability": {"lines_processed": 0, "parsed_records_count": 0},
            }
        strict_files.append(strict_entry)

    has_structural_errors = any(file.get("errors") for file in strict_files) or structurally_blocked_count > 0
    valid_subset_status = "ADVANCE_ALLOWED" if eligible_files_count > 0 and not any(file.get("errors") for file in strict_files) else "BLOCKED"
    full_corpus_status = "BLOCKED" if has_structural_errors else "NOT_BLOCKED"

    return {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "parser_stage": "strict",
            "scope": "valid_subset_only",
            "constraints": [
                "No master import",
                "No ratio calculation",
                "No final amount consolidation",
                "No final category normalization",
            ],
        },
        "source_reports": {
            "preliminary_parse": str(DEFAULT_PARSE_INPUT).replace("\\", "/"),
            "intermediate_validation": str(DEFAULT_VALIDATION_INPUT).replace("\\", "/"),
        },
        "files": strict_files,
        "controlled_exclusions": exclusions,
        "global_summary": {
            "files_total": len(parse_report.get("files", [])),
            "eligible_files_count": eligible_files_count,
            "excluded_files_count": excluded_files_count,
            "structurally_blocked_count": structurally_blocked_count,
            "full_corpus_status": full_corpus_status,
            "valid_subset_status": valid_subset_status,
            "can_advance_with_valid_subset": valid_subset_status == "ADVANCE_ALLOWED",
        },
    }


def write_outputs(root: Path, report: dict[str, Any]) -> tuple[Path, Path]:
    json_path = root / JSON_REPORT
    md_path = root / MD_REPORT
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# BC3 Strict Parse Report",
        "",
        "> Local-only strict parse output. Real-data outputs may be sensitive and must stay outside Git.",
        "",
        f"- Generated at (UTC): {report.get('metadata', {}).get('generated_at')}",
        f"- Full corpus status: {report.get('global_summary', {}).get('full_corpus_status')}",
        f"- Valid subset status: {report.get('global_summary', {}).get('valid_subset_status')}",
        f"- Eligible files: {report.get('global_summary', {}).get('eligible_files_count', 0)}",
        f"- Excluded files: {report.get('global_summary', {}).get('excluded_files_count', 0)}",
        "",
        "## Controlled Exclusions",
        "",
    ]
    exclusions = report.get("controlled_exclusions", [])
    if exclusions:
        for item in exclusions:
            lines.append(
                f"- {item.get('sanitized_id')}: {item.get('file_eligibility_status')} ({item.get('file_eligibility_reason')})"
            )
    else:
        lines.append("- none")

    lines.extend(["", "## Files", ""])
    for item in report.get("files", []):
        ref = item.get("file_ref", {})
        lines.append(f"### {ref.get('sanitized_id')} ({ref.get('relative_path')})")
        lines.append(f"- Errors: {', '.join(item.get('errors', [])) or 'none'}")
        lines.append(f"- Warnings: {', '.join(item.get('warnings', [])) or 'none'}")
        lines.append(f"- Manual review: {', '.join(item.get('manual_review_required', [])) or 'none'}")
        lines.append(f"- Unknown: {len(item.get('unknown', []))}")
        lines.append(f"- Unsupported: {len(item.get('unsupported', []))}")
        lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parse_input = root / DEFAULT_PARSE_INPUT
    validation_input = root / DEFAULT_VALIDATION_INPUT

    if len(sys.argv) > 1:
        parse_input = Path(sys.argv[1]).resolve()
    if len(sys.argv) > 2:
        validation_input = Path(sys.argv[2]).resolve()

    if not parse_input.exists():
        print(f"ERROR: parse input not found: {parse_input}")
        return 1
    if not validation_input.exists():
        print(f"ERROR: validation input not found: {validation_input}")
        return 1

    parse_report = _load_json(parse_input)
    validation_report = _load_json(validation_input)
    strict_report = parse_strict(parse_report, validation_report, root)
    json_path, md_path = write_outputs(root, strict_report)

    print("BC3 strict parser summary")
    print(f"- Parse input: {parse_input}")
    print(f"- Validation input: {validation_input}")
    print(f"- Full corpus status: {strict_report['global_summary']['full_corpus_status']}")
    print(f"- Valid subset status: {strict_report['global_summary']['valid_subset_status']}")
    print(f"- JSON output: {json_path.relative_to(root).as_posix()}")
    print(f"- Markdown output: {md_path.relative_to(root).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
