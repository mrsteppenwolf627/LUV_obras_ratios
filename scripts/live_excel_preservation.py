"""Helpers for preserved-budget scaffolding inside live Excel master."""

from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Iterable

INVALID_SHEET_CHARS_RE = re.compile(r"[\[\]\:\*\?\/\\]")
MAX_EXCEL_SHEET_NAME = 31

PRESERVED_BUDGETS_INDEX = "PRESERVED_BUDGETS_INDEX"
PRESERVED_BUDGET_SHEETS = "PRESERVED_BUDGET_SHEETS"
PRESERVED_TO_COST_ITEMS_MAP = "PRESERVED_TO_COST_ITEMS_MAP"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sanitize_sheet_name(name: str, fallback: str = "SHEET") -> str:
    cleaned = INVALID_SHEET_CHARS_RE.sub("_", (name or "").strip())
    cleaned = re.sub(r"\s+", "_", cleaned).strip("_")
    if not cleaned:
        cleaned = fallback
    return cleaned[:MAX_EXCEL_SHEET_NAME]


def make_unique_sheet_name(base: str, existing_names: Iterable[str]) -> str:
    existing = set(existing_names)
    if base not in existing:
        return base
    idx = 1
    while True:
        suffix = f"_{idx:02d}"
        candidate = f"{base[: MAX_EXCEL_SHEET_NAME - len(suffix)]}{suffix}"
        if candidate not in existing:
            return candidate
        idx += 1


def next_preserved_budget_sequence(workbook: object) -> int:
    ws = workbook[PRESERVED_BUDGETS_INDEX]
    max_seq = 0
    for row in range(2, ws.max_row + 1):
        value = ws.cell(row=row, column=5).value
        if value is None:
            continue
        text = str(value).strip()
        if text.isdigit():
            max_seq = max(max_seq, int(text))
    return max_seq + 1


def build_preserved_visible_sheet_name(
    budget_sequence: int,
    sheet_sequence: int,
    source_sheet_name: str,
    existing_names: Iterable[str],
) -> str:
    sanitized_source = sanitize_sheet_name(source_sheet_name, fallback=f"SHEET_{sheet_sequence:03d}")
    base = f"PRES_{budget_sequence:03d}_{sheet_sequence:03d}_{sanitized_source}"
    base = base[:MAX_EXCEL_SHEET_NAME]
    return make_unique_sheet_name(base, existing_names)
