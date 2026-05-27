"""Database session factory — wraps src/db/models."""
from src.db.models import get_session, DEFAULT_DB_PATH
from sqlalchemy.orm import Session


def get_db() -> Session:
    return get_session(DEFAULT_DB_PATH)
