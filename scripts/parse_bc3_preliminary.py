#!/usr/bin/env python3
"""Preliminary BC3 parser that outputs an intermediate structure only."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Any

SAMPLES_DIR = Path("data/samples")
REPORT_DIR = Path("reports/bc3_preliminary_parse")
JSON_REPORT = REPORT_DIR / "bc3_preliminary_parse_inventory.json"
MD_REPORT = REPORT_DIR / "bc3_preliminary_parse_inventory_report.md"

SUPPORTED_TYPES = {"~V", "~C", "~D", "~K", "~M", "~T"}
REG_TYPE_RE = re.compile(r"^(~[A-Za-z])")
FIEBDC_RE = re.compile(r"(?i)fiebdc[^|\\]*")
NUMERIC_RE = re.compile(r"^-?\d+(?:[.,]\d+)?$")
AMOUNT_LIKE_RE = re.compile(r"^-?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})$")
UNIT_RE = re.compile(r"^(m2|m3|ml|m|ud|u|kg|l|h)$", re.IGNORECASE)
ABSOLUTE_PATH_HINT_RE = re.compile(r"(?i)([a-z]:\\\\|/home/|/users/|\\\\\\\\)")


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


def _sanitize_text(value: str, limit: int = 80) -> str:
    compact = value.replace("\t", " ").strip()
    compact = ABSOLUTE_PATH_HINT_RE.sub("[PATH]", compact)
    return compact[:limit]


def _candidate_code(token: str) -> str:
    return token.split("\\", 1)[0].strip()


def _classify_concept(code: str) -> str:
    if code.endswith("#"):
        return "chapter_candidate"
    if re.match(r"^[A-Za-z]{2,4}\d{1,3}$", code):
        return "chapter_candidate"
    if re.match(r"^[A-Za-z]{0,3}\d+[A-Za-z0-9]+$", code):
        return "item_candidate"
    return "other_candidate"


def parse_bc3_file(path: Path, root: Path) -> dict[str, Any]:
    rel = path.relative_to(root).as_posix()
    try:
        raw = path.read_bytes()
    except Exception as exc:
        return {
            "file_ref": {
                "sanitized_id": "",
                "relative_path": rel,
                "extension": path.suffix.lower(),
                "size_bytes": path.stat().st_size if path.exists() else 0,
            },
            "decode": {"encoding": "unknown", "confidence": "low", "strategy": "read_failed"},
            "header": {"has_v": False, "v_line_number": None, "fiebdc_version_candidate": None},
            "records": {
                "total_records": 0,
                "record_type_counts": {},
                "supported_record_types": [],
                "unknown_record_types": [],
            },
            "concepts": [],
            "relations": {"links": [], "incomplete_relations": []},
            "units": [],
            "economic_signals": {"numeric_tokens_count": 0, "amount_like_tokens_count": 0},
            "raw_records": [],
            "unsupported_records": [],
            "risk_flags": ["READ_FAILED"],
            "errors": [f"Could not read file: {exc}"],
            "warnings": [],
            "manual_review_required": ["READ_FAILURE_REQUIRES_REVIEW"],
        }

    decode = detect_encoding(raw)
    if decode["encoding"] == "binary_or_unknown":
        return {
            "file_ref": {
                "sanitized_id": "",
                "relative_path": rel,
                "extension": path.suffix.lower(),
                "size_bytes": path.stat().st_size,
            },
            "decode": decode,
            "header": {"has_v": False, "v_line_number": None, "fiebdc_version_candidate": None},
            "records": {
                "total_records": 0,
                "record_type_counts": {},
                "supported_record_types": [],
                "unknown_record_types": [],
            },
            "concepts": [],
            "relations": {"links": [], "incomplete_relations": []},
            "units": [],
            "economic_signals": {"numeric_tokens_count": 0, "amount_like_tokens_count": 0},
            "raw_records": [],
            "unsupported_records": [],
            "risk_flags": ["DECODE_FAILED"],
            "errors": ["Could not decode file using utf-8 or cp1252."],
            "warnings": [],
            "manual_review_required": ["DECODE_BLOCKER"],
        }

    text = raw.decode(decode["encoding"], errors="replace")
    lines = text.splitlines()
    record_counts: Counter[str] = Counter()
    concepts: list[dict[str, Any]] = []
    links: list[dict[str, Any]] = []
    incomplete_relations: list[dict[str, Any]] = []
    raw_records: list[dict[str, Any]] = []
    unsupported_records: list[dict[str, Any]] = []
    units: set[str] = set()
    numeric_tokens = 0
    amount_tokens = 0
    header_line_number: int | None = None
    fiebdc_version: str | None = None
    warnings: list[str] = []
    errors: list[str] = []
    manual_review_required: list[str] = []

    for idx, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or not line.startswith("~"):
            continue
        match = REG_TYPE_RE.match(line)
        if not match:
            continue
        record_type = match.group(1).upper()
        payload = line[2:].lstrip("|")
        fields = payload.split("|")
        record_counts[record_type] += 1

        if len(raw_records) < 25:
            raw_records.append(
                {
                    "line_number": idx,
                    "record_type": record_type,
                    "raw_sample": _sanitize_text(line),
                }
            )

        if record_type == "~V" and header_line_number is None:
            header_line_number = idx
            m = FIEBDC_RE.search(line)
            if m:
                fiebdc_version = m.group(0)

        if record_type == "~C":
            code = _candidate_code(fields[0]) if fields else ""
            concepts.append(
                {
                    "line_number": idx,
                    "record_type": record_type,
                    "code": code,
                    "classification": _classify_concept(code) if code else "missing_code",
                }
            )

        if record_type == "~D":
            parent = _candidate_code(fields[0]) if len(fields) >= 1 else ""
            child = _candidate_code(fields[1]) if len(fields) >= 2 else ""
            if parent and child:
                links.append(
                    {
                        "line_number": idx,
                        "record_type": record_type,
                        "parent_code": parent,
                        "child_code": child,
                    }
                )
            else:
                incomplete_relations.append(
                    {
                        "line_number": idx,
                        "record_type": record_type,
                        "parent_code": parent,
                        "child_code": child,
                        "reason": "missing_parent_or_child",
                    }
                )

        if record_type not in SUPPORTED_TYPES:
            if len(unsupported_records) < 50:
                unsupported_records.append(
                    {
                        "line_number": idx,
                        "record_type": record_type,
                        "raw_sample": _sanitize_text(line),
                    }
                )

        for field_idx, field in enumerate(fields):
            for token in re.split(r"[\\;,\s]+", field):
                candidate = token.strip()
                if not candidate:
                    continue
                if UNIT_RE.match(candidate):
                    units.add(candidate.lower())
                if NUMERIC_RE.match(candidate):
                    numeric_tokens += 1
                if AMOUNT_LIKE_RE.match(candidate):
                    amount_tokens += 1

    if decode["confidence"] == "medium":
        warnings.append("ENCODING_MEDIUM_CONFIDENCE")
        manual_review_required.append("ENCODING_REVIEW_RECOMMENDED")
    if header_line_number is None:
        errors.append("Missing ~V header.")
        manual_review_required.append("MISSING_V_HEADER")
    if incomplete_relations:
        warnings.append("INCOMPLETE_D_RELATIONS")
        manual_review_required.append("INCOMPLETE_RELATIONS_REVIEW")
    unknown_types = sorted(rt for rt in record_counts if rt not in SUPPORTED_TYPES)
    if unknown_types:
        warnings.append("UNKNOWN_RECORD_TYPES_PRESENT")
        manual_review_required.append("UNKNOWN_RECORD_TYPES_REVIEW")
    if amount_tokens > 0 and amount_tokens < numeric_tokens:
        warnings.append("AMBIGUOUS_ECONOMIC_TOKENS")
        manual_review_required.append("AMBIGUOUS_ECONOMIC_SIGNALS_REVIEW")
    if len(units) > 3:
        warnings.append("MULTIPLE_UNITS_DETECTED")
        manual_review_required.append("MULTIPLE_UNITS_REVIEW")

    risk_flags: list[str] = []
    if errors:
        risk_flags.append("PARSER_PRELIMINARY_ERROR")
    if manual_review_required:
        risk_flags.append("MANUAL_REVIEW_REQUIRED")
    if warnings and not errors:
        risk_flags.append("WARNINGS_PRESENT")
    if not risk_flags:
        risk_flags.append("PRELIMINARY_PARSE_OK")

    supported_present = sorted(rt for rt in record_counts if rt in SUPPORTED_TYPES)

    return {
        "file_ref": {
            "sanitized_id": "",
            "relative_path": rel,
            "extension": path.suffix.lower(),
            "size_bytes": path.stat().st_size,
        },
        "decode": decode,
        "header": {
            "has_v": header_line_number is not None,
            "v_line_number": header_line_number,
            "fiebdc_version_candidate": fiebdc_version,
        },
        "records": {
            "total_records": sum(record_counts.values()),
            "record_type_counts": dict(sorted(record_counts.items())),
            "supported_record_types": supported_present,
            "unknown_record_types": unknown_types,
        },
        "concepts": concepts,
        "relations": {
            "links": links,
            "incomplete_relations": incomplete_relations,
        },
        "units": sorted(units),
        "economic_signals": {
            "numeric_tokens_count": numeric_tokens,
            "amount_like_tokens_count": amount_tokens,
            "contains_amount_like_tokens": amount_tokens > 0,
            "ambiguous_economic_tokens": amount_tokens > 0 and amount_tokens < numeric_tokens,
        },
        "raw_records": raw_records,
        "unsupported_records": unsupported_records,
        "risk_flags": sorted(set(risk_flags)),
        "errors": sorted(set(errors)),
        "warnings": sorted(set(warnings)),
        "manual_review_required": sorted(set(manual_review_required)),
    }


def parse_bc3_samples(root: Path) -> dict[str, Any]:
    samples_path = root / SAMPLES_DIR
    generated_at = datetime.now(timezone.utc).isoformat()
    if not samples_path.exists():
        return {
            "metadata": {
                "generated_at": generated_at,
                "parser_stage": "preliminary",
                "scope": "intermediate_structure_only",
                "sensitivity_policy": "Real outputs are local-only and must stay outside Git.",
            },
            "files": [],
            "global_summary": {
                "samples_dir": str(SAMPLES_DIR).replace("\\", "/"),
                "exists": False,
                "bc3_files_count": 0,
                "message": "Samples directory does not exist.",
            },
        }

    bc3_files = sorted([p for p in samples_path.rglob("*") if p.is_file() and p.suffix.lower() == ".bc3"])
    files: list[dict[str, Any]] = []
    for idx, file_path in enumerate(bc3_files, start=1):
        parsed = parse_bc3_file(file_path, root)
        parsed["file_ref"]["sanitized_id"] = f"BC3_{idx:02d}"
        files.append(parsed)

    decode_failed = sum(1 for item in files if "DECODE_FAILED" in item.get("risk_flags", []))
    files_with_errors = sum(1 for item in files if item.get("errors"))
    files_with_manual_review = sum(1 for item in files if item.get("manual_review_required"))
    unknown_types = sorted({t for item in files for t in item["records"]["unknown_record_types"]})

    summary = {
        "samples_dir": str(SAMPLES_DIR).replace("\\", "/"),
        "exists": True,
        "bc3_files_count": len(files),
        "files_with_errors": files_with_errors,
        "files_with_manual_review": files_with_manual_review,
        "decode_failed_files": decode_failed,
        "unknown_record_types": unknown_types,
        "message": "OK" if files else "No BC3 files found in data/samples.",
        "constraints": [
            "No master import",
            "No ratio calculation",
            "No final normalization",
            "No final amount consolidation",
        ],
    }
    return {
        "metadata": {
            "generated_at": generated_at,
            "parser_stage": "preliminary",
            "scope": "intermediate_structure_only",
            "sensitivity_policy": "Real outputs are local-only and must stay outside Git.",
        },
        "files": files,
        "global_summary": summary,
    }


def write_outputs(root: Path, report: dict[str, Any]) -> tuple[Path, Path]:
    json_path = root / JSON_REPORT
    md_path = root / MD_REPORT
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    lines: list[str] = []
    meta = report.get("metadata", {})
    gs = report.get("global_summary", {})
    lines.append("# BC3 Preliminary Parse Report")
    lines.append("")
    lines.append("> Local parser output. Real-data reports may contain sensitive metadata and must remain outside Git.")
    lines.append("")
    lines.append(f"- Generated at (UTC): {meta.get('generated_at')}")
    lines.append(f"- Parser stage: {meta.get('parser_stage')}")
    lines.append(f"- Scope: {meta.get('scope')}")
    lines.append(f"- BC3 files count: {gs.get('bc3_files_count', 0)}")
    lines.append(f"- Files with errors: {gs.get('files_with_errors', 0)}")
    lines.append(f"- Files with manual review: {gs.get('files_with_manual_review', 0)}")
    lines.append("")
    lines.append("## Files")
    lines.append("")
    for entry in report.get("files", []):
        ref = entry["file_ref"]
        lines.append(f"### {ref.get('sanitized_id')} ({ref.get('extension')}, {ref.get('size_bytes')} bytes)")
        lines.append(f"- Relative path: {ref.get('relative_path')}")
        lines.append(
            f"- Decode: {entry['decode']['encoding']} ({entry['decode']['confidence']}, {entry['decode']['strategy']})"
        )
        lines.append(
            f"- Header: has_v={entry['header']['has_v']}, fiebdc={entry['header']['fiebdc_version_candidate']}"
        )
        lines.append(
            f"- Records: total={entry['records']['total_records']}, supported={','.join(entry['records']['supported_record_types']) or 'none'}, unknown={','.join(entry['records']['unknown_record_types']) or 'none'}"
        )
        lines.append(
            f"- Relations: links={len(entry['relations']['links'])}, incomplete={len(entry['relations']['incomplete_relations'])}"
        )
        lines.append(
            f"- Economic signals: numeric={entry['economic_signals']['numeric_tokens_count']}, amount_like={entry['economic_signals']['amount_like_tokens_count']}"
        )
        lines.append(f"- Risk flags: {', '.join(entry.get('risk_flags', [])) or 'none'}")
        lines.append(f"- Errors: {', '.join(entry.get('errors', [])) or 'none'}")
        lines.append(f"- Warnings: {', '.join(entry.get('warnings', [])) or 'none'}")
        lines.append(
            f"- Manual review required: {', '.join(entry.get('manual_review_required', [])) or 'none'}"
        )
        lines.append("")
    if not report.get("files"):
        lines.append("No BC3 files found.")
        lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def print_summary(report: dict[str, Any], root: Path, json_path: Path, md_path: Path) -> None:
    gs = report.get("global_summary", {})
    print("BC3 preliminary parser summary")
    print(f"- Samples dir: {gs.get('samples_dir')}")
    print(f"- Exists: {gs.get('exists')}")
    print(f"- BC3 files: {gs.get('bc3_files_count')}")
    print(f"- Files with errors: {gs.get('files_with_errors', 0)}")
    print(f"- Files with manual review: {gs.get('files_with_manual_review', 0)}")
    print(f"- JSON output: {json_path.relative_to(root).as_posix()}")
    print(f"- Markdown output: {md_path.relative_to(root).as_posix()}")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    report = parse_bc3_samples(root)
    json_path, md_path = write_outputs(root, report)
    print_summary(report, root, json_path, md_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
