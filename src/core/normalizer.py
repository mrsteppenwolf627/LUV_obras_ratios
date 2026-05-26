"""Normalizer: converts reader output into ORM objects ready for DB insertion."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

from src.db.schema import Budget, LineItem, ValidationLog


def normalize(
    raw_data: dict[str, Any],
    surface_m2: Optional[float] = None,
    building_type: Optional[str] = None,
    file_hash: str = "",
) -> tuple[Budget, list[LineItem], list[ValidationLog]]:
    """
    Convert reader output into Budget + LineItem + ValidationLog objects.

    Does NOT commit to DB — caller is responsible for session.add() + commit().

    Returns (budget, items, logs).
    """
    filename = raw_data.get("filename", "unknown")
    source_format = raw_data.get("source_format", "unknown")
    chapters = raw_data.get("chapters", [])
    reader_errors = raw_data.get("errors", [])
    reader_warnings = raw_data.get("warnings", [])

    budget = Budget(
        filename=filename,
        file_hash=file_hash,
        import_date=datetime.now(timezone.utc),
        surface_m2=surface_m2,
        building_type=building_type,
        source_format=source_format,
        total_cost=raw_data.get("total_cost"),
        raw_data_json=json.dumps(
            {
                "sheets_processed": raw_data.get("sheets_processed", []),
                "reader_errors": reader_errors,
                "reader_warnings": reader_warnings,
                "chapter_count": len(chapters),
            },
            ensure_ascii=False,
        ),
    )

    items: list[LineItem] = []
    logs: list[ValidationLog] = []

    for ch in chapters:
        status = _validate_chapter(ch, logs, budget)
        item = LineItem(
            budget=budget,
            chapter_code=ch.get("chapter_code") or "",
            chapter_name=ch.get("chapter_name") or "",
            description=ch.get("chapter_name") or "",
            quantity=None,
            unit=None,
            unit_cost=None,
            total_cost=ch.get("total_cost"),
            validation_status=status,
        )
        items.append(item)

    # Log reader-level errors as budget-level validation events
    for err in reader_errors:
        logs.append(
            ValidationLog(
                budget=budget,
                rule_name="READER_ERROR",
                status="FAIL",
                message=err,
            )
        )
    for warn in reader_warnings:
        logs.append(
            ValidationLog(
                budget=budget,
                rule_name="READER_WARNING",
                status="WARNING",
                message=warn,
            )
        )

    return budget, items, logs


def _validate_chapter(
    ch: dict[str, Any], logs: list[ValidationLog], budget: Budget
) -> str:
    """Return VALID | DUBIOUS and append any validation events to logs.

    Reader-assigned validation_status is always respected — DUBIOUS from the
    reader is never upgraded to VALID here.
    """
    total = ch.get("total_cost")
    code = ch.get("chapter_code", "")

    # 1. Respect any validation_status the reader already assigned
    reader_status = ch.get("validation_status")
    reader_reason = ch.get("validation_reason")
    if reader_status == "DUBIOUS":
        logs.append(
            ValidationLog(
                budget=budget,
                rule_name="READER_DUBIOUS",
                status="FAIL",
                message=f"chapter_code={code!r}: {reader_reason or 'marcado dudoso por el lector'}",
            )
        )
        return "DUBIOUS"

    # 2. Own structural checks
    if total is None:
        logs.append(
            ValidationLog(
                budget=budget,
                rule_name="MISSING_AMOUNT",
                status="FAIL",
                message=f"chapter_code={code!r} has no amount",
            )
        )
        return "DUBIOUS"

    if total <= 0:
        logs.append(
            ValidationLog(
                budget=budget,
                rule_name="NEGATIVE_OR_ZERO_AMOUNT",
                status="FAIL",
                message=f"chapter_code={code!r} amount={total}",
            )
        )
        return "DUBIOUS"

    # 3. Legacy confidence check (for callers that still pass the old field)
    if ch.get("confidence") == "LOW":
        logs.append(
            ValidationLog(
                budget=budget,
                rule_name="LOW_CONFIDENCE",
                status="WARNING",
                message=f"chapter_code={code!r} low detection confidence",
            )
        )
        return "DUBIOUS"

    return "VALID"
