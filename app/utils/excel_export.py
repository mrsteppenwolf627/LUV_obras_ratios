"""Excel master export for the official approved-only workbook."""
from pathlib import Path

from sqlalchemy.orm import Session

_EXCEL_PATH = Path("data/master/LUV_RATIOS_MASTER.xlsx")


def generate_or_get_excel(session: Session) -> Path:
    from src.export.excel_master_generator import generate_master_excel_approved

    generate_master_excel_approved(session, _EXCEL_PATH)
    return _EXCEL_PATH
