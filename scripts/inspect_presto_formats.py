#!/usr/bin/env python3
"""Inspect Presto/PZH-like files without destructive parsing."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import string
import sys
import zipfile
from typing import Any

SAMPLES_DIR = Path("data/samples")
REPORT_DIR = Path("reports/presto_diagnostics")
JSON_REPORT = REPORT_DIR / "presto_diagnostics_inventory.json"
MD_REPORT = REPORT_DIR / "presto_diagnostics_inventory_report.md"

PRESTO_EXTENSIONS = {".presto", ".pzh", ".prestobackup", ".prestorecord"}
PRESTO_NAME_HINTS = ("presto", "pzh")


def _sanitize_path(path: str) -> str:
    return path.replace("\\", "/").strip()


def _loadable_text_ratio(sample: bytes) -> float:
    if not sample:
        return 0.0
    printable = set(bytes(string.printable, "ascii"))
    count = sum(1 for b in sample if b in printable)
    return count / len(sample)


def _magic_kind(raw: bytes) -> str:
    if not raw:
        return "empty"
    if raw.startswith(b"PK\x03\x04"):
        return "zip"
    if raw.startswith(b"SQLite format 3\x00"):
        return "sqlite"
    ratio = _loadable_text_ratio(raw[:4096])
    if ratio >= 0.82:
        return "text"
    return "binary"


def _sample_text(raw: bytes, limit: int = 16) -> list[str]:
    try:
        text = raw.decode("utf-8")
        encoding = "utf-8"
    except UnicodeDecodeError:
        try:
            text = raw.decode("cp1252")
            encoding = "cp1252"
        except UnicodeDecodeError:
            return []
    lines = []
    for line in text.splitlines()[:limit]:
        stripped = line.strip()
        if stripped:
            lines.append(stripped[:200])
    if lines:
        lines.insert(0, f"[encoding={encoding}]")
    return lines


def _inspect_zip(path: Path) -> dict[str, Any]:
    names: list[str] = []
    try:
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()[:20]
        return {
            "support_classification": "READABLE_WITH_STANDARD_LIBRARY",
            "parser_or_reader_used": "zipfile",
            "internal_names_sample": names,
            "notes": "Zip container readable with standard library.",
        }
    except Exception as exc:
        return {
            "support_classification": "NEEDS_EXTERNAL_TOOL",
            "parser_or_reader_used": "zipfile_failed",
            "internal_names_sample": names,
            "notes": f"Zip container not readable with standard library: {exc}",
        }


def _inspect_sqlite(path: Path) -> dict[str, Any]:
    tables: list[str] = []
    try:
        conn = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
        try:
            cur = conn.execute("SELECT name FROM sqlite_master ORDER BY name")
            tables = [row[0] for row in cur.fetchall()[:20]]
        finally:
            conn.close()
        return {
            "support_classification": "READABLE_WITH_STANDARD_LIBRARY",
            "parser_or_reader_used": "sqlite3",
            "internal_names_sample": tables,
            "notes": "SQLite container readable with standard library.",
        }
    except Exception as exc:
        return {
            "support_classification": "NEEDS_EXTERNAL_TOOL",
            "parser_or_reader_used": "sqlite3_failed",
            "internal_names_sample": tables,
            "notes": f"SQLite container not readable with standard library: {exc}",
        }


def _inspect_text(path: Path, raw: bytes) -> dict[str, Any]:
    sample_lines = _sample_text(raw)
    return {
        "support_classification": "DIRECTLY_READABLE",
        "parser_or_reader_used": "text_decoder",
        "internal_names_sample": sample_lines,
        "notes": "Plain text-like content readable without vendor tooling.",
    }


def _inspect_binary(path: Path, raw: bytes, ext: str) -> dict[str, Any]:
    name = path.name.lower()
    if ext in PRESTO_EXTENSIONS or any(hint in name for hint in PRESTO_NAME_HINTS):
        return {
            "support_classification": "NEEDS_VENDOR_EXPORT",
            "parser_or_reader_used": "none",
            "internal_names_sample": [],
            "notes": "Binary/proprietary-like content. Vendor export or specialized tool may be required.",
        }
    return {
        "support_classification": "UNSUPPORTED_OR_UNKNOWN",
        "parser_or_reader_used": "none",
        "internal_names_sample": [],
        "notes": "Not recognized as a Presto/PZH-like target.",
    }


def _is_presto_like(path: Path) -> bool:
    ext = path.suffix.lower()
    name = path.name.lower()
    return ext in PRESTO_EXTENSIONS or any(hint in name for hint in PRESTO_NAME_HINTS)


def inspect_presto_formats(root: Path) -> dict[str, Any]:
    samples_path = root / SAMPLES_DIR
    generated_at = datetime.now(timezone.utc).isoformat()

    if not samples_path.exists():
        return {
            "diagnostics_metadata": {
                "generated_at": generated_at,
                "diagnostic_stage": "phase_7_2_presto_pzh_research",
            },
            "source_files": [],
            "files": [],
            "global_summary": {
                "files_scanned_total": 0,
                "presto_like_files_total": 0,
                "directly_readable_total": 0,
                "readable_with_standard_library_total": 0,
                "needs_external_tool_total": 0,
                "needs_vendor_export_total": 0,
                "unsupported_or_unknown_total": 0,
                "controlled_exclusions_total": 0,
            },
            "warnings": [],
            "manual_review": [],
            "controlled_exclusions": [],
        }

    all_files = sorted([p for p in samples_path.rglob("*") if p.is_file()])
    source_files: list[dict[str, Any]] = []
    presto_files: list[dict[str, Any]] = []
    controlled_exclusions: list[dict[str, Any]] = []
    warnings: list[str] = []
    manual_review: list[str] = []
    counts = {
        "directly_readable_total": 0,
        "readable_with_standard_library_total": 0,
        "needs_external_tool_total": 0,
        "needs_vendor_export_total": 0,
        "unsupported_or_unknown_total": 0,
    }

    for path in all_files:
        rel = _sanitize_path(str(path.relative_to(root)))
        ext = path.suffix.lower()
        is_presto = _is_presto_like(path)
        source_files.append(
            {
                "relative_path_sanitized": rel,
                "extension": ext,
                "size_bytes": path.stat().st_size,
                "is_presto_like": is_presto,
            }
        )

        if not is_presto:
            controlled_exclusions.append(
                {
                    "relative_path_sanitized": rel,
                    "reason": "NOT_PRESTO_FORMAT",
                }
            )
            continue

        raw = path.read_bytes()
        magic = _magic_kind(raw)
        sample = {
            "relative_path_sanitized": rel,
            "extension": ext,
            "size_bytes": path.stat().st_size,
            "magic_kind": magic,
            "magic_bytes_hex": raw[:16].hex(),
            "header_sample": _sample_text(raw, limit=6),
            "support_classification": "UNSUPPORTED_OR_UNKNOWN",
            "parser_or_reader_used": "none",
            "internal_names_sample": [],
            "notes": "",
        }

        if magic == "zip":
            sample.update(_inspect_zip(path))
        elif magic == "sqlite":
            sample.update(_inspect_sqlite(path))
        elif magic == "text":
            sample.update(_inspect_text(path, raw))
        else:
            sample.update(_inspect_binary(path, raw, ext))

        if sample["support_classification"] == "DIRECTLY_READABLE":
            counts["directly_readable_total"] += 1
        elif sample["support_classification"] == "READABLE_WITH_STANDARD_LIBRARY":
            counts["readable_with_standard_library_total"] += 1
        elif sample["support_classification"] == "NEEDS_EXTERNAL_TOOL":
            counts["needs_external_tool_total"] += 1
        elif sample["support_classification"] == "NEEDS_VENDOR_EXPORT":
            counts["needs_vendor_export_total"] += 1
        else:
            counts["unsupported_or_unknown_total"] += 1

        if sample["support_classification"] in {"NEEDS_EXTERNAL_TOOL", "NEEDS_VENDOR_EXPORT"}:
            manual_review.append(f"{rel}:{sample['support_classification']}")
            warnings.append(f"{rel}:{sample['support_classification']}")

        presto_files.append(sample)

    return {
        "diagnostics_metadata": {
            "generated_at": generated_at,
            "diagnostic_stage": "phase_7_2_presto_pzh_research",
        },
        "source_files": source_files,
        "files": presto_files,
        "global_summary": {
            "files_scanned_total": len(all_files),
            "presto_like_files_total": len(presto_files),
            **counts,
            "controlled_exclusions_total": len(controlled_exclusions),
        },
        "warnings": warnings,
        "manual_review": manual_review,
        "controlled_exclusions": controlled_exclusions,
    }


def write_reports(root: Path, payload: dict[str, Any]) -> tuple[Path, Path]:
    json_path = root / JSON_REPORT
    md_path = root / MD_REPORT
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Presto Diagnostics Report",
        "",
        "> Local diagnostic output. Real-data artifacts may be sensitive and must remain outside Git.",
        "",
        f"- Generated at (UTC): {payload.get('diagnostics_metadata', {}).get('generated_at')}",
        f"- Files scanned: {payload.get('global_summary', {}).get('files_scanned_total', 0)}",
        f"- Presto-like files: {payload.get('global_summary', {}).get('presto_like_files_total', 0)}",
        "",
        "## Presto-like files",
        "",
    ]
    for item in payload.get("files", []):
        lines.append(f"### {item.get('relative_path_sanitized')}")
        lines.append(f"- Support classification: {item.get('support_classification')}")
        lines.append(f"- Reader used: {item.get('parser_or_reader_used')}")
        lines.append(f"- Magic kind: {item.get('magic_kind')}")
        lines.append(f"- Notes: {item.get('notes')}")
        lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    payload = inspect_presto_formats(root)
    json_path, md_path = write_reports(root, payload)

    print("Presto/PZH diagnostics summary")
    print(f"- Files scanned: {payload['global_summary']['files_scanned_total']}")
    print(f"- Presto-like files: {payload['global_summary']['presto_like_files_total']}")
    print(f"- JSON report: {json_path.relative_to(root).as_posix()}")
    print(f"- Markdown report: {md_path.relative_to(root).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
