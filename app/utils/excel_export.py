"""Excel master export — generates or overwrites data/master/master_latest.xlsx."""
from pathlib import Path

from sqlalchemy.orm import Session

_EXCEL_PATH = Path("data/master/master_latest.xlsx")


def generate_or_get_excel(session: Session) -> Path:
    from src.export.excel_master_generator import generate_master_excel

    generate_master_excel(session, _EXCEL_PATH)
    return _EXCEL_PATH
