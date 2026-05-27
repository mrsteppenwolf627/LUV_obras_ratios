"""Statistics calculations for the /api/ratios/stats endpoint."""
from sqlalchemy.orm import Session


def get_stats(session: Session) -> dict:
    from src.db.schema import Budget, LineItem, Ratio
    from sqlalchemy import func

    # Top 10 chapters by sum of total_cost across all budgets
    top_rows = (
        session.query(
            LineItem.chapter_code,
            func.sum(LineItem.total_cost).label("total_amount"),
        )
        .filter(LineItem.total_cost.isnot(None))
        .group_by(LineItem.chapter_code)
        .order_by(func.sum(LineItem.total_cost).desc())
        .limit(10)
        .all()
    )
    top_chapters = [
        {
            "chapter_code": row.chapter_code or "N/A",
            "total_amount": round(float(row.total_amount or 0), 2),
        }
        for row in top_rows
    ]

    # Ratio distribution: bin ratios.median into €/m² ranges
    ratio_medians = [
        float(r.median)
        for r in session.query(Ratio).filter(Ratio.median.isnot(None)).all()
    ]
    bins = [
        ("0-50", 0, 50),
        ("50-100", 50, 100),
        ("100-200", 100, 200),
        ("200-300", 200, 300),
        ("300-500", 300, 500),
        ("500-1000", 500, 1000),
        ("1000+", 1000, float("inf")),
    ]
    ratio_distribution = [
        {"range": label, "count": sum(1 for v in ratio_medians if lo <= v < hi)}
        for label, lo, hi in bins
    ]

    # Temporal evolution: one point per distinct import date
    budgets = session.query(Budget).order_by(Budget.import_date).all()
    evolution = None
    if ratio_medians and budgets:
        global_avg = round(sum(ratio_medians) / len(ratio_medians), 2)
        seen: set = set()
        points = []
        for b in budgets:
            if not b.import_date:
                continue
            date_str = b.import_date.strftime("%Y-%m-%d")
            if date_str not in seen:
                seen.add(date_str)
                points.append({"date": date_str, "avg_ratio": global_avg})
        if points:
            evolution = points

    return {
        "top_chapters": top_chapters,
        "ratio_distribution": ratio_distribution,
        "temporal_evolution": evolution,
    }
