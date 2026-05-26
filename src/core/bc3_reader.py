"""BC3 reader: extracts top-level chapters and amounts from FIEBDC-3 files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional


# Only top-level chapters (code ends with #): e.g. ~C|C01#||NAME|AMOUNT|DATE|0|
# Sub-chapters have codes like ~C|C0501#| — we include those too, but flag them
CHAPTER_RE = re.compile(r"^~C\|([^|]+)\|[^|]*\|([^|]*)\|([^|]+)\|")
ENCODINGS = ["cp1252", "utf-8", "latin-1"]


def _detect_encoding(raw: bytes) -> str:
    for enc in ENCODINGS:
        try:
            raw.decode(enc)
            return enc
        except UnicodeDecodeError:
            continue
    return "latin-1"


def _parse_amount(raw: str) -> Optional[float]:
    s = raw.strip().replace(",", ".")
    try:
        v = float(s)
        return v if v > 0 else None
    except ValueError:
        return None


def _is_top_level(code: str) -> bool:
    """Top-level chapters have a simple code ending in #, e.g. C01#."""
    clean = code.rstrip("#").strip()
    # Top-level: alphanumeric code with no more than 3 chars (C01, C02, etc.)
    # Sub-level: C0501, C1001, etc.
    return len(clean) <= 4


def read_bc3(filepath: str | Path) -> dict[str, Any]:
    """
    Read a BC3 file and extract chapter-level cost data.

    Returns the same shape as excel_reader.read_excel:
      - source_format: 'bc3'
      - filename: str
      - chapters: list[dict]  (chapter_code, chapter_name, total_cost, confidence, is_top_level)
      - total_cost: float | None  (sum of top-level chapters)
      - warnings: list[str]
      - errors: list[str]
    """
    path = Path(filepath)
    result: dict[str, Any] = {
        "source_format": "bc3",
        "filename": path.name,
        "filepath": str(path),
        "sheets_processed": [],
        "chapters": [],
        "total_cost": None,
        "warnings": [],
        "errors": [],
    }

    if path.suffix.lower() != ".bc3":
        result["errors"].append(f"UNSUPPORTED_EXTENSION: {path.suffix}")
        return result

    try:
        raw = path.read_bytes()
    except Exception as exc:
        result["errors"].append(f"READ_FAILED: {exc}")
        return result

    enc = _detect_encoding(raw)
    try:
        text = raw.decode(enc, errors="replace")
    except Exception as exc:
        result["errors"].append(f"DECODE_FAILED enc={enc}: {exc}")
        return result

    chapters: list[dict[str, Any]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line.startswith("~C"):
            continue
        m = CHAPTER_RE.match(line)
        if not m:
            continue

        raw_code = m.group(1).strip()
        raw_name = m.group(2).strip()
        raw_amount = m.group(3).strip()

        amount = _parse_amount(raw_amount)
        if amount is None:
            result["warnings"].append(f"ZERO_OR_INVALID_AMOUNT line={lineno} code={raw_code!r}")
            continue

        clean_code = raw_code.rstrip("#").strip()
        top = _is_top_level(raw_code)

        chapters.append(
            {
                "chapter_code": clean_code,
                "chapter_name": raw_name or clean_code,
                "total_cost": amount,
                "confidence": "HIGH",
                "is_top_level": top,
                "source_line": lineno,
            }
        )

    if not chapters:
        result["warnings"].append("NO_CHAPTERS_DETECTED")

    result["chapters"] = chapters
    # Total = sum of top-level chapters only
    top_totals = [c["total_cost"] for c in chapters if c.get("is_top_level") and c["total_cost"]]
    result["total_cost"] = sum(top_totals) if top_totals else None

    return result
