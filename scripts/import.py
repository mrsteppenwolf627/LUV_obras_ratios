#!/usr/bin/env python3
"""
Import a budget file (Excel or BC3) into the LUV Obras Ratios master.

Usage:
    python scripts/import.py <file> [--dry-run] [--confirm]
                             [--surface <m2>] [--type <building_type>]
                             [--db <path>]

Examples:
    python scripts/import.py data/samples/proyecto_001/22_10_SCE_Datos.xlsx --dry-run
    python scripts/import.py data/samples/proyecto_001/22_10_SCE_Datos.xlsx --confirm --surface 450
"""

import argparse
import io
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.auditor import compute_file_hash, generate_import_log, save_log
from src.core.bc3_reader import read_bc3
from src.core.excel_reader import read_excel
from src.core.normalizer import normalize
from src.db.models import DEFAULT_DB_PATH, get_session
from src.db.queries import get_budget_by_hash
from src.export.excel_master_generator import generate_master_excel
from src.ratios.calculator import recalculate_all_ratios

ARCHIVED_DIR = Path("data/archived_budgets")


def detect_format(filepath: Path) -> str:
    ext = filepath.suffix.lower()
    if ext in (".xlsx", ".xlsm"):
        return "excel"
    if ext == ".bc3":
        return "bc3"
    return "unknown"


def read_file(filepath: Path, fmt: str) -> dict:
    if fmt == "excel":
        return read_excel(filepath)
    if fmt == "bc3":
        return read_bc3(filepath)
    return {"source_format": fmt, "filename": filepath.name, "errors": [f"UNSUPPORTED_FORMAT: {fmt}"], "chapters": [], "warnings": []}


def _print_preview(raw_data: dict, budget, items: list, logs: list) -> None:
    print(f"\n{'='*60}")
    print(f"  PREVIEW: {budget.filename}")
    print(f"{'='*60}")
    print(f"  Format     : {raw_data['source_format'].upper()}")
    print(f"  Hash       : {budget.file_hash[:16]}...")
    print(f"  Total cost : {budget.total_cost:,.2f} €" if budget.total_cost else "  Total cost : N/A")
    print(f"  Surface    : {budget.surface_m2} m²" if budget.surface_m2 else "  Surface    : not provided")
    print(f"  Chapters   : {len(items)} ({sum(1 for i in items if i.validation_status == 'VALID')} valid, {sum(1 for i in items if i.validation_status == 'DUBIOUS')} dubious)")
    print()
    for item in items:
        status_icon = "✅" if item.validation_status == "VALID" else "⚠️ "
        cost_str = f"{item.total_cost:>12,.2f} €" if item.total_cost else "           N/A"
        print(f"  {status_icon}  {item.chapter_code:<30} {cost_str}")
    if raw_data.get("errors"):
        print("\n  ERRORS:")
        for e in raw_data["errors"]:
            print(f"    ✗ {e}")
    if raw_data.get("warnings"):
        print("\n  WARNINGS:")
        for w in raw_data["warnings"]:
            print(f"    ⚠  {w}")
    print(f"{'='*60}\n")


def archive_file(filepath: Path) -> Path:
    """Copy the source file to archived_budgets/."""
    ARCHIVED_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = ARCHIVED_DIR / f"{ts}_{filepath.name}"
    shutil.copy2(filepath, dest)
    return dest


def main() -> None:
    parser = argparse.ArgumentParser(description="Import budget into LUV master")
    parser.add_argument("filepath", help="Path to .xlsx or .bc3 file")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--confirm", action="store_true", help="Actually import")
    parser.add_argument("--surface", type=float, default=None, help="Building surface in m²")
    parser.add_argument("--type", dest="building_type", default=None, help="Building type label")
    parser.add_argument("--db", default=None, help="Path to SQLite DB file")
    args = parser.parse_args()

    if not args.dry_run and not args.confirm:
        print("❌ Specify --dry-run or --confirm.")
        sys.exit(1)

    filepath = Path(args.filepath)
    if not filepath.exists():
        print(f"❌ File not found: {filepath}")
        sys.exit(1)

    fmt = detect_format(filepath)
    if fmt == "unknown":
        print(f"❌ Unsupported file type: {filepath.suffix}")
        sys.exit(1)

    db_path = Path(args.db) if args.db else DEFAULT_DB_PATH

    print(f"📂 Reading {filepath.name} ({fmt.upper()})...")
    raw_data = read_file(filepath, fmt)

    if raw_data.get("errors"):
        print("❌ Reader errors:")
        for e in raw_data["errors"]:
            print(f"   {e}")
        sys.exit(1)

    print(f"🔑 Computing SHA-256...")
    file_hash = compute_file_hash(filepath)

    budget, items, logs = normalize(
        raw_data,
        surface_m2=args.surface,
        building_type=args.building_type,
        file_hash=file_hash,
    )

    _print_preview(raw_data, budget, items, logs)

    log = generate_import_log(budget, items, filepath, dry_run=args.dry_run)

    if args.dry_run:
        log_path = save_log(log)
        print(f"📝 Dry-run log saved: {log_path}")
        print("ℹ️  No data written (--dry-run). Use --confirm to import.")
        return

    # -- CONFIRM path --
    session = get_session(db_path)
    try:
        existing = get_budget_by_hash(session, file_hash)
        if existing:
            print(f"⚠️  File already imported (Budget ID={existing.id}). Skipping.")
            session.close()
            return

        session.add(budget)
        session.add_all(items)
        session.add_all(logs)
        session.commit()
        print(f"✅ Budget saved (ID={budget.id})")

        print("📊 Recalculating ratios...")
        n = recalculate_all_ratios(session)
        session.commit()
        print(f"   {n} ratio(s) updated.")

        print("📊 Generating master Excel...")
        out_path = generate_master_excel(session)
        print(f"✅ Master updated: {out_path}")

        print("📁 Archiving original file...")
        archived = archive_file(filepath)
        print(f"   Archived to: {archived}")

        log["db_budget_id"] = budget.id
        log_path = save_log(log)
        print(f"📝 Import log saved: {log_path}")

    except Exception as exc:
        session.rollback()
        print(f"❌ Import failed: {exc}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
