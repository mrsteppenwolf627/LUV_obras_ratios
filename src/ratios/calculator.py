"""Ratio calculator: median €/m² per chapter from validated data."""

from __future__ import annotations

import statistics
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from src.db.schema import Budget, LineItem, Ratio
from src.db.queries import get_ratio, list_all_budgets


def calculate_cost_per_m2(
    session: Session,
    chapter_code: str,
    building_type: Optional[str] = None,
) -> Optional[float]:
    """Return the median €/m² for a chapter, or None if no valid data."""
    values = _collect_cost_per_m2_values(session, chapter_code, building_type)
    if not values:
        return None
    return statistics.median(values)


def _collect_cost_per_m2_values(
    session: Session, chapter_code: str, building_type: Optional[str]
) -> list[float]:
    """Gather per-budget €/m² values for a chapter."""
    q = (
        session.query(LineItem, Budget)
        .join(Budget)
        .filter(
            LineItem.chapter_code == chapter_code,
            LineItem.validation_status == "VALID",
            Budget.surface_m2 > 0,
        )
    )
    if building_type is not None:
        q = q.filter(Budget.building_type == building_type)

    values: list[float] = []
    for item, budget in q.all():
        if item.total_cost and budget.surface_m2:
            values.append(item.total_cost / budget.surface_m2)
    return values


def calculate_median_ratio(
    session: Session,
    chapter_code: str,
    building_type: Optional[str] = None,
) -> Optional[float]:
    """Alias for calculate_cost_per_m2 — returns median €/m²."""
    return calculate_cost_per_m2(session, chapter_code, building_type)


def recalculate_all_ratios(session: Session) -> int:
    """
    Recompute Ratio rows for every distinct chapter_code x building_type
    combination found among VALID line items.  Returns the number of ratios updated.
    """
    # Collect all distinct (chapter_code, building_type) pairs
    rows = (
        session.query(LineItem.chapter_code, Budget.building_type)
        .join(Budget)
        .filter(LineItem.validation_status == "VALID")
        .distinct()
        .all()
    )

    updated = 0
    for chapter_code, building_type in rows:
        values = _collect_cost_per_m2_values(session, chapter_code, building_type)

        # Get existing ratio or create new
        ratio = get_ratio(session, chapter_code, building_type)
        if ratio is None:
            # Resolve chapter_name from any item
            item = (
                session.query(LineItem)
                .filter_by(chapter_code=chapter_code, validation_status="VALID")
                .first()
            )
            ratio = Ratio(
                chapter_code=chapter_code,
                chapter_name=item.chapter_name if item else chapter_code,
                building_type=building_type,
            )
            session.add(ratio)

        if values:
            ratio.median = statistics.median(values)
            ratio.min_value = min(values)
            ratio.max_value = max(values)
            ratio.cost_per_m2 = ratio.median
            ratio.sample_count = len(values)
        else:
            # No surface data — count samples without ratio
            count = (
                session.query(LineItem)
                .join(Budget)
                .filter(
                    LineItem.chapter_code == chapter_code,
                    LineItem.validation_status == "VALID",
                    *(
                        [Budget.building_type == building_type]
                        if building_type is not None
                        else []
                    ),
                )
                .count()
            )
            ratio.sample_count = count

        ratio.last_updated = datetime.now(timezone.utc)
        updated += 1

    session.flush()
    return updated
