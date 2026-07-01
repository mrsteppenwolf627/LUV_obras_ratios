"""Excel master export for the official approved-only workbook."""
import os
from pathlib import Path

from sqlalchemy.orm import Session

OFFICIAL_MASTER_FILENAME = "LUV_RATIOS_MASTER.xlsx"
_LOCAL_EXCEL_PATH = Path("data/master") / OFFICIAL_MASTER_FILENAME
_SERVERLESS_EXCEL_PATH = Path("/tmp") / OFFICIAL_MASTER_FILENAME


def is_serverless_vercel_runtime() -> bool:
    return bool(os.getenv("VERCEL")) or bool(os.getenv("VERCEL_ENV"))


def resolve_official_master_export_path() -> Path:
    if is_serverless_vercel_runtime():
        return _SERVERLESS_EXCEL_PATH
    return _LOCAL_EXCEL_PATH


def generate_or_get_excel(session: Session) -> Path:
    from src.export.excel_master_generator import generate_master_excel_approved

    export_path = resolve_official_master_export_path()
    generate_master_excel_approved(session, export_path)
    return export_path
