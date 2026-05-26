"""SQLAlchemy ORM models for the LUV Obras Ratios system."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, relationship


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Budget(Base):
    """One imported budget file."""

    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    file_hash = Column(String(64), unique=True, nullable=False)
    import_date = Column(DateTime, default=_utcnow, nullable=False)
    surface_m2 = Column(Float, nullable=True)
    building_type = Column(String(100), nullable=True)
    source_format = Column(String(20), nullable=False)  # 'excel' | 'bc3'
    total_cost = Column(Float, nullable=True)
    raw_data_json = Column(Text, nullable=True)

    items = relationship("LineItem", back_populates="budget", cascade="all, delete-orphan")
    validation_logs = relationship(
        "ValidationLog",
        primaryjoin="ValidationLog.budget_id == Budget.id",
        back_populates="budget",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Budget id={self.id} filename={self.filename!r} hash={self.file_hash[:8]}>"


class LineItem(Base):
    """A single chapter/line extracted from a budget."""

    __tablename__ = "line_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    budget_id = Column(Integer, ForeignKey("budgets.id"), nullable=False)
    chapter_code = Column(String(100), nullable=True)
    chapter_name = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    quantity = Column(Float, nullable=True)
    unit = Column(String(30), nullable=True)
    unit_cost = Column(Float, nullable=True)
    total_cost = Column(Float, nullable=True)
    # VALID | DUBIOUS | EXCLUDED
    validation_status = Column(String(20), nullable=False, default="VALID")

    budget = relationship("Budget", back_populates="items")
    validation_logs = relationship(
        "ValidationLog",
        primaryjoin="ValidationLog.line_item_id == LineItem.id",
        back_populates="line_item",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<LineItem id={self.id} chapter={self.chapter_code!r} total={self.total_cost}>"


class Ratio(Base):
    """Aggregated ratio per chapter, optionally per building type."""

    __tablename__ = "ratios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chapter_code = Column(String(100), nullable=False)
    chapter_name = Column(String(500), nullable=True)
    building_type = Column(String(100), nullable=True)
    cost_per_m2 = Column(Float, nullable=True)
    median = Column(Float, nullable=True)
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    sample_count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        UniqueConstraint("chapter_code", "building_type", name="uq_ratio_chapter_type"),
    )

    def __repr__(self) -> str:
        return f"<Ratio chapter={self.chapter_code!r} median={self.median} n={self.sample_count}>"


class ValidationLog(Base):
    """One validation event tied to a budget or a specific line item."""

    __tablename__ = "validation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    line_item_id = Column(Integer, ForeignKey("line_items.id"), nullable=True)
    budget_id = Column(Integer, ForeignKey("budgets.id"), nullable=True)
    rule_name = Column(String(100), nullable=False)
    # PASS | FAIL | WARNING
    status = Column(String(20), nullable=False)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    line_item = relationship(
        "LineItem",
        primaryjoin="ValidationLog.line_item_id == LineItem.id",
        back_populates="validation_logs",
    )
    budget = relationship(
        "Budget",
        primaryjoin="ValidationLog.budget_id == Budget.id",
        back_populates="validation_logs",
    )

    def __repr__(self) -> str:
        return f"<ValidationLog rule={self.rule_name!r} status={self.status!r}>"
