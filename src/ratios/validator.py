"""Validation helpers for ratio data quality."""

from __future__ import annotations

from typing import Any


def is_outlier(value: float, median: float, threshold: float = 3.0) -> bool:
    """Return True if value deviates more than threshold * median from the median."""
    if median == 0:
        return False
    return abs(value - median) / median > threshold


def validate_ratio_inputs(items: list[Any]) -> list[str]:
    """Check a list of LineItem-like objects; return list of warning strings."""
    warnings: list[str] = []
    if not items:
        warnings.append("NO_VALID_ITEMS")
        return warnings
    for item in items:
        if item.total_cost is None:
            warnings.append(f"MISSING_COST chapter={item.chapter_code!r}")
        elif item.total_cost <= 0:
            warnings.append(f"NON_POSITIVE_COST chapter={item.chapter_code!r} value={item.total_cost}")
    return warnings
