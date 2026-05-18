#!/usr/bin/env python3
"""Initial BC3 intermediate normalizer from strict parse/validation outputs."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Any

DEFAULT_STRICT_PARSE_INPUT = Path("reports/bc3_strict_parse/bc3_strict_parse_inventory.json")
DEFAULT_STRICT_VALIDATION_INPUT = Path("reports/bc3_strict_validation/bc3_strict_validation_report.json")
REPORT_DIR = Path("reports/bc3_intermediate_normalization")
JSON_REPORT = REPORT_DIR / "bc3_intermediate_normalization_report.json"
MD_REPORT = REPORT_DIR / "bc3_intermediate_normalization_report.md"

NUMERIC_TOKEN_RE = re.compile(r"\b\d+(?:[.,]\d+)?\b")
ECONOMIC_TOKEN_RE = re.compile(r"(?:EUR|€|PRES|IMPORTE|COSTE|PRECIO)", re.IGNORECASE)
MEASUREMENT_TOKEN_RE = re.compile(r"(?:M2|M3|ML|UD|KG|L|CM|MM)", re.IGNORECASE)
MAX_DESCRIPTION_LEN = 400


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _truncate(text: str, max_len: int = MAX_DESCRIPTION_LEN) -> str:
    value = (text or "").strip()
    if len(value) <= max_len:
        return value
    return value[: max_len - 3] + "..."


def _extract_signals(text: str) -> dict[str, list[str]]:
    numbers = NUMERIC_TOKEN_RE.findall(text or "")
    econ = ECONOMIC_TOKEN_RE.findall(text or "")
    meas = MEASUREMENT_TOKEN_RE.findall(text or "")
    return {
        "numeric_tokens": numbers,
        "economic_tokens": sorted({token.upper() for token in econ}),
        "measurement_tokens": sorted({token.upper() for token in meas}),
    }


def _classify_concept(code: str) -> str:
    return "chapter" if str(code or "").endswith("#") else "cost_item"


def _validation_index(validation_report: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    if not validation_report:
        return out
    for item in validation_report.get("files", []):
        sid = item.get("sanitized_id", "")
        if sid:
            out[sid] = item
    return out


def _normalize_file(
    strict_file: dict[str, Any], validation_entry: dict[str, Any] | None
) -> dict[str, Any]:
    ref = strict_file.get("file_ref", {})
    parsed = strict_file.get("parsed", {})
    concepts = parsed.get("concepts", [])
    relations = parsed.get("relations", [])
    unknown = strict_file.get("unknown", [])
    unsupported = strict_file.get("unsupported", [])

    chapters: list[dict[str, Any]] = []
    cost_items: list[dict[str, Any]] = []
    units_set: set[str] = set()
    descriptions: list[dict[str, Any]] = []
    measurement_signals: list[dict[str, Any]] = []
    economic_signals: list[dict[str, Any]] = []

    for concept in concepts:
        code = concept.get("code", "")
        raw = concept.get("raw", "") or code
        line_number = concept.get("line_number")
        cls = _classify_concept(code)
        desc = _truncate(str(raw))
        sig = _extract_signals(raw)

        if cls == "chapter":
            chapters.append({"code": code, "line_number": line_number, "candidate": True})
        else:
            cost_items.append({"code": code, "line_number": line_number, "candidate": True})

        descriptions.append({"code": code, "text": desc, "truncated": len(str(raw)) > len(desc)})
        measurement_signals.append(
            {
                "code": code,
                "line_number": line_number,
                "tokens": sig["measurement_tokens"],
                "numeric_tokens": sig["numeric_tokens"],
                "consolidated": False,
            }
        )
        economic_signals.append(
            {
                "code": code,
                "line_number": line_number,
                "tokens": sig["economic_tokens"],
                "numeric_tokens": sig["numeric_tokens"],
                "consolidated": False,
            }
        )
        for token in sig["measurement_tokens"]:
            units_set.add(token)

    normalized_relations = [
        {
            "parent_code": rel.get("parent_code"),
            "child_code": rel.get("child_code"),
            "line_number": rel.get("line_number"),
            "record_type": rel.get("record_type"),
        }
        for rel in relations
    ]

    validation_flags = {
        "strict_parse_errors": strict_file.get("errors", []),
        "strict_parse_warnings": strict_file.get("warnings", []),
        "strict_validation_errors": (validation_entry or {}).get("errors", []),
    }
    manual_review = list(strict_file.get("manual_review_required", []))
    if validation_entry:
        for item in validation_entry.get("manual_review_items", []):
            code = item.get("code")
            detail = item.get("detail")
            manual_review.append(f"{code}:{detail}" if detail else str(code))

    return {
        "file_ref": {
            "sanitized_id": ref.get("sanitized_id"),
            "relative_path": ref.get("relative_path"),
            "extension": ref.get("extension"),
            "size_bytes": ref.get("size_bytes"),
        },
        "source_trace": {
            "header_line": (parsed.get("header") or {}).get("line_number"),
            "strict_traceability": strict_file.get("traceability", {}),
            "source_stage": "strict_parse",
        },
        "chapters": chapters,
        "cost_items": cost_items,
        "relations": normalized_relations,
        "units": sorted(units_set),
        "descriptions": descriptions,
        "measurement_signals": measurement_signals,
        "economic_signals": economic_signals,
        "validation_flags": validation_flags,
        "manual_review": manual_review,
        "unknown_or_unsupported": {
            "unknown": unknown,
            "unsupported": unsupported,
        },
    }


def normalize_intermediate(
    strict_parse_report: dict[str, Any], strict_validation_report: dict[str, Any] | None
) -> dict[str, Any]:
    validation_idx = _validation_index(strict_validation_report)

    files: list[dict[str, Any]] = []
    for strict_file in strict_parse_report.get("files", []):
        sid = strict_file.get("file_ref", {}).get("sanitized_id", "")
        files.append(_normalize_file(strict_file, validation_idx.get(sid)))

    parse_summary = strict_parse_report.get("global_summary", {})
    validation_summary = (strict_validation_report or {}).get("global_validation_summary", {})
    corpus_status = {
        "full_corpus_status": validation_summary.get(
            "full_corpus_status", parse_summary.get("full_corpus_status", "UNKNOWN")
        ),
        "valid_subset_status": validation_summary.get(
            "valid_subset_status", parse_summary.get("valid_subset_status", "UNKNOWN")
        ),
        "can_advance_with_valid_subset": validation_summary.get(
            "can_advance_with_valid_subset",
            parse_summary.get("can_advance_with_valid_subset", False),
        ),
    }

    return {
        "normalization_metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "normalization_stage": "phase_5_1_initial_intermediate",
            "constraints": [
                "No master import",
                "No ratio calculation",
                "No final amount consolidation",
                "No final category normalization",
                "No category mapping feed",
            ],
        },
        "source_reports": {
            "strict_parse": str(DEFAULT_STRICT_PARSE_INPUT).replace("\\", "/"),
            "strict_validation": str(DEFAULT_STRICT_VALIDATION_INPUT).replace("\\", "/"),
        },
        "corpus_status": corpus_status,
        "files": files,
        "global_summary": {
            "files_total": len(strict_parse_report.get("files", [])),
            "normalized_files_count": len(files),
            "eligible_files_count": parse_summary.get("eligible_files_count", len(files)),
            "excluded_files_count": parse_summary.get("excluded_files_count", 0),
        },
        "controlled_exclusions": strict_parse_report.get("controlled_exclusions", []),
    }


def write_outputs(root: Path, report: dict[str, Any]) -> tuple[Path, Path]:
    json_path = root / JSON_REPORT
    md_path = root / MD_REPORT
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# BC3 Intermediate Normalization Report",
        "",
        "> Local normalization output. Real-data artifacts may be sensitive and must remain outside Git.",
        "",
        f"- Generated at (UTC): {report.get('normalization_metadata', {}).get('generated_at')}",
        f"- Full corpus status: {report.get('corpus_status', {}).get('full_corpus_status')}",
        f"- Valid subset status: {report.get('corpus_status', {}).get('valid_subset_status')}",
        f"- Normalized files: {report.get('global_summary', {}).get('normalized_files_count', 0)}",
        f"- Controlled exclusions: {len(report.get('controlled_exclusions', []))}",
        "",
        "## Files",
        "",
    ]
    for item in report.get("files", []):
        ref = item.get("file_ref", {})
        lines.append(f"### {ref.get('sanitized_id')} ({ref.get('relative_path')})")
        lines.append(f"- Chapters: {len(item.get('chapters', []))}")
        lines.append(f"- Cost items: {len(item.get('cost_items', []))}")
        lines.append(f"- Relations: {len(item.get('relations', []))}")
        lines.append(f"- Units observed: {', '.join(item.get('units', [])) or 'none'}")
        lines.append(f"- Manual review entries: {len(item.get('manual_review', []))}")
        lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    strict_parse_input = root / DEFAULT_STRICT_PARSE_INPUT
    strict_validation_input = root / DEFAULT_STRICT_VALIDATION_INPUT

    if len(sys.argv) > 1:
        strict_parse_input = Path(sys.argv[1]).resolve()
    if len(sys.argv) > 2:
        strict_validation_input = Path(sys.argv[2]).resolve()

    if not strict_parse_input.exists():
        print(f"ERROR: strict parse input not found: {strict_parse_input}")
        return 1

    strict_parse_report = _load_json(strict_parse_input)
    strict_validation_report: dict[str, Any] | None = None
    if strict_validation_input.exists():
        strict_validation_report = _load_json(strict_validation_input)

    normalized = normalize_intermediate(strict_parse_report, strict_validation_report)
    json_path, md_path = write_outputs(root, normalized)

    print("BC3 intermediate normalization summary")
    print(f"- Strict parse input: {strict_parse_input}")
    print(f"- Strict validation input: {strict_validation_input if strict_validation_input.exists() else 'not found (skipped)'}")
    print(f"- Full corpus status: {normalized['corpus_status']['full_corpus_status']}")
    print(f"- Valid subset status: {normalized['corpus_status']['valid_subset_status']}")
    print(f"- JSON output: {json_path.relative_to(root).as_posix()}")
    print(f"- Markdown output: {md_path.relative_to(root).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
