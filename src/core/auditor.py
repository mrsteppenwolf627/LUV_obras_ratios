"""Auditor: SHA-256 hashing and JSON import logs."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOGS_DIR = Path("logs/imports")


def compute_file_hash(filepath: str | Path) -> str:
    """Return the SHA-256 hex digest of a file."""
    path = Path(filepath)
    sha = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()


def generate_import_log(
    budget: Any,
    items: list[Any],
    filepath: str | Path,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Build a JSON-serialisable import audit record."""
    from src.db.schema import LineItem  # local import to avoid circularity

    valid = sum(1 for i in items if i.validation_status == "VALID")
    dubious = sum(1 for i in items if i.validation_status == "DUBIOUS")

    return {
        "schema_version": "1.0",
        "event": "DRY_RUN" if dry_run else "IMPORT",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "filepath": str(filepath),
        "filename": budget.filename,
        "file_hash": budget.file_hash,
        "source_format": budget.source_format,
        "surface_m2": budget.surface_m2,
        "building_type": budget.building_type,
        "total_cost": budget.total_cost,
        "chapters": {
            "total": len(items),
            "valid": valid,
            "dubious": dubious,
        },
        "chapters_detail": [
            {
                "chapter_code": i.chapter_code,
                "chapter_name": i.chapter_name,
                "total_cost": i.total_cost,
                "validation_status": i.validation_status,
            }
            for i in items
        ],
    }


def save_log(log: dict[str, Any], logs_dir: str | Path = LOGS_DIR) -> Path:
    """Write the log dict as a JSON file; returns the file path."""
    out_dir = Path(logs_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stem = Path(log.get("filename", "unknown")).stem
    event = log.get("event", "IMPORT").lower()
    out_path = out_dir / f"{ts}_{event}_{stem}.json"

    out_path.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
    return out_path
