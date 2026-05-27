"""Re-export ORM models and provide DB session factory."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from src.db.schema import Base, Budget, LineItem, Ratio, SpaceRatio, ValidationLog

__all__ = ["Budget", "LineItem", "Ratio", "SpaceRatio", "ValidationLog", "Base", "get_session", "init_db"]

DEFAULT_DB_PATH = Path("data/master/ratios.db")


def _get_engine(db_path: Path = DEFAULT_DB_PATH):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    # Enable foreign key enforcement for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(conn, _):
        conn.execute("PRAGMA foreign_keys=ON")
    return engine


def init_db(db_path: Path = DEFAULT_DB_PATH) -> None:
    """Create all tables if they don't exist."""
    engine = _get_engine(db_path)
    Base.metadata.create_all(engine)


def get_session(db_path: Path = DEFAULT_DB_PATH) -> Session:
    """Return a new SQLAlchemy session."""
    engine = _get_engine(db_path)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()
