#!/usr/bin/env python3
"""Diagnostic BC3 inspection without parsing/importing data."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Any

SAMPLES_DIR = Path("data/samples")
REPORT_DIR = Path("reports/bc3_diagnostics")
JSON_REPORT = REPORT_DIR / "bc3_diagnostic_inventory.json"
MD_REPORT = REPORT_DIR / "bc3_diagnostic_inventory_report.md"

FIEBDC_RE = re.compile(r"(?i)fiebdc[^|\\]*")
REG_TYPE_RE = re.compile(r"^(~[A-Za-z])")
NUMERIC_RE = re.compile(r"^-?\d+(?:[.,]\d+)?$")
AMOUNT_LIKE_RE = re.compile(r"^-?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})$")
UNIT_RE = re.compile(r"^(m2|m3|ml|m|ud|u|kg|l|h)$", re.IGNORECASE)


def detect_encoding(raw: bytes) -> dict[str, Any]:
    if not raw:
        return {
            "encoding": "unknown",
            "confidence": "low",
            "strategy": "empty_file",
        }

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


def _candidate_code(token: str) -> str:
    return token.split("\\", 1)[0].strip()


def inspect_bc3_file(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
    except Exception as exc:
        return {
            "status": "BC3_READ_FAILED",
            "encoding": "unknown",
            "encoding_confidence": "low",
            "record_types_present": [],
            "record_type_counts": {},
            "fiebdc_header_line": None,
            "fiebdc_version_candidate": None,
            "chapter_code_candidates": [],
            "hierarchy_relations_candidates": [],
            "units_detected": [],
            "amount_indicators": {"numeric_tokens_count": 0, "amount_like_tokens_count": 0},
            "notes": f"Could not read file: {exc}",
        }

    enc = detect_encoding(raw)
    if enc["encoding"] == "binary_or_unknown":
        return {
            "status": "BC3_DECODE_UNCERTAIN",
            "encoding": enc["encoding"],
            "encoding_confidence": enc["confidence"],
            "record_types_present": [],
            "record_type_counts": {},
            "fiebdc_header_line": None,
            "fiebdc_version_candidate": None,
            "chapter_code_candidates": [],
            "hierarchy_relations_candidates": [],
            "units_detected": [],
            "amount_indicators": {"numeric_tokens_count": 0, "amount_like_tokens_count": 0},
            "notes": "Could not decode file with supported encodings.",
        }

    text = raw.decode(enc["encoding"], errors="replace")
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    record_type_counts: Counter[str] = Counter()
    chapter_codes: set[str] = set()
    relations: set[tuple[str, str]] = set()
    units: set[str] = set()
    numeric_tokens_count = 0
    amount_like_tokens_count = 0
    fiebdc_header_line: str | None = None
    fiebdc_version_candidate: str | None = None

    for line in lines:
        if line.startswith("~") is False:
            continue

        m_type = REG_TYPE_RE.match(line)
        if not m_type:
            continue
        record_type = m_type.group(1).upper()
        record_type_counts[record_type] += 1

        if record_type == "~V" and fiebdc_header_line is None:
            fiebdc_header_line = line[:200]
            m_fiebdc = FIEBDC_RE.search(line)
            if m_fiebdc:
                fiebdc_version_candidate = m_fiebdc.group(0)

        payload = line[2:].lstrip("|")
        fields = payload.split("|")

        if record_type == "~C" and fields:
            code = _candidate_code(fields[0])
            if code:
                chapter_codes.add(code)

        if record_type == "~D" and len(fields) >= 2:
            parent = _candidate_code(fields[0])
            child = _candidate_code(fields[1])
            if parent and child:
                relations.add((parent, child))

        for field in fields:
            for token in re.split(r"[\\;,\s]+", field):
                candidate = token.strip()
                if not candidate:
                    continue
                if UNIT_RE.match(candidate):
                    units.add(candidate.lower())
                if NUMERIC_RE.match(candidate):
                    numeric_tokens_count += 1
                if AMOUNT_LIKE_RE.match(candidate):
                    amount_like_tokens_count += 1

    return {
        "status": "BC3_DIAGNOSTIC_OK",
        "encoding": enc["encoding"],
        "encoding_confidence": enc["confidence"],
        "record_types_present": sorted(record_type_counts.keys()),
        "record_type_counts": dict(sorted(record_type_counts.items())),
        "fiebdc_header_line": fiebdc_header_line,
        "fiebdc_version_candidate": fiebdc_version_candidate,
        "chapter_code_candidates": sorted(chapter_codes),
        "hierarchy_relations_candidates": [
            {"parent": parent, "child": child} for parent, child in sorted(relations)
        ],
        "units_detected": sorted(units),
        "amount_indicators": {
            "numeric_tokens_count": numeric_tokens_count,
            "amount_like_tokens_count": amount_like_tokens_count,
        },
        "notes": "Diagnostic-only extraction. No parser, no totals, no master update.",
    }


def inspect_bc3_samples(root: Path) -> dict[str, Any]:
    samples_path = root / SAMPLES_DIR
    generated_at = datetime.now(timezone.utc).isoformat()

    if not samples_path.exists():
        return {
            "generated_at": generated_at,
            "samples_dir": str(SAMPLES_DIR).replace("\\", "/"),
            "exists": False,
            "bc3_files_count": 0,
            "message": "Samples directory does not exist.",
            "files": [],
        }

    bc3_files = sorted([p for p in samples_path.rglob("*") if p.is_file() and p.suffix.lower() == ".bc3"])
    entries: list[dict[str, Any]] = []
    for file_path in bc3_files:
        rel = file_path.relative_to(root)
        inspection = inspect_bc3_file(file_path)
        entries.append(
            {
                "relative_path": str(rel).replace("\\", "/"),
                "filename": file_path.name,
                "extension": file_path.suffix.lower(),
                "size_bytes": file_path.stat().st_size,
                "inspection": inspection,
            }
        )

    return {
        "generated_at": generated_at,
        "samples_dir": str(SAMPLES_DIR).replace("\\", "/"),
        "exists": True,
        "bc3_files_count": len(entries),
        "message": "OK" if entries else "No BC3 files found in data/samples.",
        "files": entries,
    }


def write_reports(root: Path, report: dict[str, Any]) -> tuple[Path, Path]:
    json_path = root / JSON_REPORT
    md_path = root / MD_REPORT
    json_path.parent.mkdir(parents=True, exist_ok=True)

    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    lines: list[str] = []
    lines.append("# BC3 Diagnostic Report")
    lines.append("")
    lines.append("> Local diagnostic report. May contain sensitive metadata from real samples.")
    lines.append("")
    lines.append(f"- Generated at (UTC): {report['generated_at']}")
    lines.append(f"- Samples directory: {report['samples_dir']}")
    lines.append(f"- Exists: {report['exists']}")
    lines.append(f"- BC3 files count: {report['bc3_files_count']}")
    lines.append(f"- Message: {report['message']}")
    lines.append("")
    lines.append("## Files")
    lines.append("")

    if report.get("files"):
        for entry in report["files"]:
            insp = entry["inspection"]
            lines.append(f"### {entry['relative_path']}")
            lines.append(f"- Status: {insp['status']}")
            lines.append(f"- Encoding: {insp['encoding']} ({insp['encoding_confidence']})")
            lines.append(f"- FIEBDC candidate: {insp.get('fiebdc_version_candidate')}")
            lines.append(f"- Record types present: {', '.join(insp.get('record_types_present', [])) or 'none'}")
            lines.append(
                f"- Chapter candidates: {len(insp.get('chapter_code_candidates', []))} | Relations: {len(insp.get('hierarchy_relations_candidates', []))}"
            )
            lines.append(
                f"- Amount indicators: numeric={insp['amount_indicators']['numeric_tokens_count']}, amount_like={insp['amount_indicators']['amount_like_tokens_count']}"
            )
            lines.append("")
    else:
        lines.append("No BC3 files found.")
        lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def print_summary(report: dict[str, Any], json_path: Path, md_path: Path, root: Path) -> None:
    print("BC3 diagnostic summary")
    print(f"- Samples dir: {report['samples_dir']}")
    print(f"- Exists: {report['exists']}")
    print(f"- BC3 files: {report['bc3_files_count']}")
    print(f"- JSON report: {json_path.relative_to(root).as_posix()}")
    print(f"- Markdown report: {md_path.relative_to(root).as_posix()}")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    report = inspect_bc3_samples(root)
    json_path, md_path = write_reports(root, report)
    print_summary(report, json_path, md_path, root)
    if report["exists"] and report["bc3_files_count"] == 0:
        print("INFO: No BC3 files found in data/samples.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
