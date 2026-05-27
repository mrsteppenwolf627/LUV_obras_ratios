"""Queries for ratios and master metadata."""
from datetime import timezone
from typing import List, Tuple

from sqlalchemy.orm import Session


def get_master_data(session: Session) -> Tuple[dict, List[dict]]:
    from src.db.schema import Budget, Ratio

    total_budgets = session.query(Budget).count()
    total_ratios = session.query(Ratio).count()

    last_budget = session.query(Budget).order_by(Budget.import_date.desc()).first()
    last_import = None
    if last_budget and last_budget.import_date:
        dt = last_budget.import_date
        last_import = (
            dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            if dt.tzinfo
            else dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        )

    metadata = {
        "total_budgets": total_budgets,
        "total_ratios": total_ratios,
        "last_import": last_import,
    }

    ratios = session.query(Ratio).order_by(Ratio.chapter_code).all()
    ratio_list = [
        {
            "chapter_code": r.chapter_code or "",
            "chapter_description": r.chapter_name or "",
            "building_type": r.building_type or "",
            "median_ratio": float(r.median) if r.median is not None else 0.0,
            "min_ratio": float(r.min_value) if r.min_value is not None else 0.0,
            "max_ratio": float(r.max_value) if r.max_value is not None else 0.0,
            "count_budgets": r.sample_count or 0,
            "validation_status": "VALID" if r.median is not None else "DUBIOUS",
        }
        for r in ratios
    ]

    return metadata, ratio_list
