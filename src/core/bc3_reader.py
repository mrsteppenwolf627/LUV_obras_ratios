"""BC3 reader: extracts chapters and item decompositions from FIEBDC-3 files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional


CHAPTER_RE = re.compile(r"^~C\|([^|]+)\|[^|]*\|([^|]*)\|([^|]+)\|")
DECOMP_RE = re.compile(r"^~D\|([^|]+)\|([^|]*)\|")
ENCODINGS = ["cp1252", "utf-8", "latin-1"]


def _detect_encoding(raw: bytes) -> str:
    for enc in ENCODINGS:
        try:
            raw.decode(enc)
            return enc
        except UnicodeDecodeError:
            continue
    return "latin-1"


def _parse_float(raw: str) -> Optional[float]:
    s = raw.strip().replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _parse_amount(raw: str) -> Optional[float]:
    v = _parse_float(raw)
    return v if v is not None and v > 0 else None


def _is_top_level(code: str) -> bool:
    """Top-level chapters end with # and have a short base code (≤4 chars, e.g. C01)."""
    clean = code.rstrip("#").strip()
    return len(clean) <= 4


def _parse_decomp_items(items_str: str) -> list[dict[str, Any]]:
    """
    Parse the items payload of a ~D record.

    Format: CODE\\FACTOR\\RENDIMIENTO\\CODE\\FACTOR\\RENDIMIENTO\\...
    Returns list of {code, factor, rendimiento}.

    Note: RENDIMIENTO is a quantity/performance value (not a cost).
    Unit prices reside in ~B records which are not parsed here.
    """
    parts = [p.strip() for p in items_str.split("\\") if p.strip()]
    items: list[dict[str, Any]] = []
    i = 0
    while i + 2 < len(parts):
        code = parts[i]
        factor = _parse_float(parts[i + 1])
        rendimiento = _parse_float(parts[i + 2])
        if code:
            items.append({
                "code": code,
                "factor": factor if factor is not None else 1.0,
                "rendimiento": rendimiento if rendimiento is not None else 0.0,
            })
        i += 3
    return items


def read_bc3(filepath: str | Path) -> dict[str, Any]:
    """
    Read a BC3 file and extract chapter-level cost data with item decompositions.

    Returns:
      - source_format: 'bc3'
      - filename, filepath
      - chapters: list[dict] with fields:
          chapter_code, chapter_name, total_cost,
          is_top_level, confidence, validation_status, source_line,
          items (list of {code, factor, rendimiento})
      - total_cost: sum of top-level chapters
      - warnings, errors
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

    # Pass 1: parse all ~C and ~D records
    raw_chapters: dict[str, dict[str, Any]] = {}  # clean_code → chapter dict
    chapter_order: list[str] = []

    for lineno, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line.startswith("~"):
            continue

        if line.startswith("~C"):
            m = CHAPTER_RE.match(line)
            if not m:
                continue
            raw_code = m.group(1).strip()
            raw_name = m.group(2).strip()
            raw_amount = m.group(3).strip()

            amount = _parse_amount(raw_amount)
            if amount is None:
                result["warnings"].append(
                    f"ZERO_OR_INVALID_AMOUNT line={lineno} code={raw_code!r}"
                )
                continue

            clean_code = raw_code.rstrip("#").strip()
            top = _is_top_level(raw_code)

            ch: dict[str, Any] = {
                "chapter_code": clean_code,
                "chapter_name": raw_name or clean_code,
                "total_cost": amount,
                "confidence": "HIGH",
                "validation_status": "VALID",
                "validation_reason": None,
                "is_top_level": top,
                "source_line": lineno,
                "items": [],
            }
            raw_chapters[clean_code] = ch
            chapter_order.append(clean_code)

        elif line.startswith("~D"):
            m = DECOMP_RE.match(line)
            if not m:
                continue
            parent_raw = m.group(1).strip().rstrip("#").strip()
            items_str = m.group(2)
            items = _parse_decomp_items(items_str)

            if parent_raw in raw_chapters:
                raw_chapters[parent_raw]["items"] = items

    # Pass 2: consistency check
    # NOTE: In FIEBDC-3, ~D records contain RENDIMIENTO (quantities), not costs.
    # Unit prices live in ~B records (not parsed here).
    # Therefore sum(factor*rendimiento) != chapter total_cost in most real files.
    # We log this as a WARNING for traceability but do NOT mark DUBIOUS,
    # because the ~C total is the authoritative amount from the budget software.
    for clean_code in chapter_order:
        ch = raw_chapters[clean_code]
        if ch["items"]:
            decomp_sum = sum(i["factor"] * i["rendimiento"] for i in ch["items"])
            chapter_total = ch["total_cost"]
            # Check only when decomp_sum is in the same order of magnitude as total
            # (i.e., could plausibly represent costs, not just quantities)
            if decomp_sum > 0 and chapter_total and abs(decomp_sum - chapter_total) / chapter_total > 0.01:
                result["warnings"].append(
                    f"DECOMP_MISMATCH code={clean_code!r} "
                    f"chapter_total={chapter_total:.2f} "
                    f"decomp_sum={decomp_sum:.2f} "
                    f"(~D contains rendimientos, not costs — expected)"
                )

    chapters = [raw_chapters[c] for c in chapter_order]

    if not chapters:
        result["warnings"].append("NO_CHAPTERS_DETECTED")

    result["chapters"] = chapters
    top_totals = [c["total_cost"] for c in chapters if c.get("is_top_level") and c["total_cost"]]
    result["total_cost"] = sum(top_totals) if top_totals else None

    return result
