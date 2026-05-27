"""Queries for archived budgets."""
from datetime import timezone
from typing import List

from sqlalchemy.orm import Session


def get_archived_budgets(session: Session) -> List[dict]:
    from src.db.schema import Budget, LineItem

    budgets = session.query(Budget).order_by(Budget.import_date.desc()).all()
    result = []
    for b in budgets:
        chapter_count = (
            session.query(LineItem).filter(LineItem.budget_id == b.id).count()
        )

        import_date_str = ""
        if b.import_date:
            dt = b.import_date
            import_date_str = (
                dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                if dt.tzinfo
                else dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            )

        result.append(
            {
                "budget_id": b.id,
                "filename": b.filename or "",
                "import_date": import_date_str,
                "total_amount": float(b.total_cost or 0.0),
                "chapter_count": chapter_count,
                "file_hash": b.file_hash or "",
            }
        )

    return result
