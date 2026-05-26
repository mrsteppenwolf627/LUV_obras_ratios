"""SQL query helpers for common operations."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from src.db.schema import Budget, LineItem, Ratio


def get_budget_by_hash(session: Session, file_hash: str) -> Optional[Budget]:
    return session.query(Budget).filter_by(file_hash=file_hash).first()


def get_valid_items_for_chapter(
    session: Session, chapter_code: str, building_type: Optional[str] = None
) -> list[LineItem]:
    q = (
        session.query(LineItem)
        .join(Budget)
        .filter(LineItem.chapter_code == chapter_code, LineItem.validation_status == "VALID")
    )
    if building_type is not None:
        q = q.filter(Budget.building_type == building_type)
    return q.all()


def get_all_valid_items(session: Session) -> list[LineItem]:
    return session.query(LineItem).filter_by(validation_status="VALID").all()


def get_ratio(
    session: Session, chapter_code: str, building_type: Optional[str] = None
) -> Optional[Ratio]:
    return (
        session.query(Ratio)
        .filter_by(chapter_code=chapter_code, building_type=building_type)
        .first()
    )


def list_all_budgets(session: Session) -> list[Budget]:
    return session.query(Budget).order_by(Budget.import_date).all()


def list_all_ratios(session: Session) -> list[Ratio]:
    return session.query(Ratio).order_by(Ratio.chapter_code).all()
