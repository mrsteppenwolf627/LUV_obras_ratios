"""Queries for archived budgets and BudgetImport CRUD."""
from datetime import timezone
from typing import List, Optional

from sqlalchemy.orm import Session


def create_budget_import(
    session: Session,
    filename: str,
    file_hash: str,
    building_type: Optional[str],
) -> "BudgetImport":  # type: ignore[name-defined]  # noqa: F821
    from src.db.schema import BudgetImport

    record = BudgetImport(
        filename=filename,
        file_hash=file_hash,
        building_type=building_type,
        status="success",
    )
    session.add(record)
    session.flush()
    return record


def get_budget_import_by_hash(session: Session, file_hash: str) -> Optional["BudgetImport"]:  # type: ignore[name-defined]  # noqa: F821
    from src.db.schema import BudgetImport

    return session.query(BudgetImport).filter(BudgetImport.file_hash == file_hash).first()


def update_budget_import_status(
    session: Session,
    import_record: "BudgetImport",  # type: ignore[name-defined]  # noqa: F821
    status: str,
    items_count: int,
    error_message: Optional[str] = None,
) -> None:
    import_record.status = status
    import_record.items_count = items_count
    if error_message:
        import_record.error_message = error_message


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
