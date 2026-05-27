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
from src.core.item_extractor import extract_items_from_budget, make_item_key
from src.core.normalizer import normalize
from src.core.presto_reader import parse_presto
from src.db.models import DEFAULT_DB_PATH, get_session
from src.db.queries import get_budget_by_hash
from src.db.schema import Budget, ItemInstance, ItemMaster, SpaceRatio
from src.export.excel_master_generator import generate_master_excel
from src.export.space_ratios_generator import generate_space_ratios_excel
from src.ratios.calculator import recalculate_all_ratios
from src.ratios.item_classifier import classify_item
from src.ratios.item_ratio_calculator import classify_new_item_price, get_item_ratio_history, recalculate_item_master_stats
from src.ratios.space_calculator import calculate_space_ratios

ARCHIVED_DIR = Path("data/archived_budgets")
SPACE_RATIOS_DIR = Path("data/exports/space_ratios")


def detect_format(filepath: Path) -> str:
    ext = filepath.suffix.lower()
    if ext in (".xlsx", ".xlsm"):
        return "excel"
    if ext == ".bc3":
        return "bc3"
    if ext == ".presto":
        return "presto"
    return "unknown"


def read_file(filepath: Path, fmt: str) -> dict:
    if fmt == "excel":
        return read_excel(filepath)
    if fmt == "bc3":
        return read_bc3(filepath)
    if fmt == "presto":
        return parse_presto(filepath)
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
        print(f"❌ Unsupported file type: {filepath.suffix}. Use .xlsx, .bc3 or .Presto")
        sys.exit(1)

    db_path = Path(args.db) if args.db else DEFAULT_DB_PATH

    print(f"📂 Reading {filepath.name} ({fmt.upper()})...")
    raw_data = read_file(filepath, fmt)

    if raw_data.get("errors"):
        print("❌ Reader errors:")
        for e in raw_data["errors"]:
            print(f"   {e}")
        sys.exit(1)

    if raw_data.get("warnings"):
        for w in raw_data["warnings"]:
            print(f"⚠️  {w}")

    print(f"🔑 Computing SHA-256...")
    file_hash = compute_file_hash(filepath)

    # --- Route by format ---
    if fmt == "presto":
        _import_presto(filepath, raw_data, file_hash, db_path, args)
    else:
        _import_chapter_based(filepath, raw_data, file_hash, db_path, args)


def _import_presto(
    filepath: Path, presupuesto: dict, file_hash: str, db_path: Path, args
) -> None:
    """Import a Presto file: creates Budget + SpaceRatio rows + space Excel."""
    n_spaces = len(presupuesto.get("espacios", []))
    total_coste = presupuesto.get("total_coste", 0.0)
    has_breakdown = presupuesto.get("has_space_breakdown", False)

    print(f"\n{'='*60}")
    print(f"  PRESTO IMPORT: {presupuesto['filename']}")
    print(f"{'='*60}")
    print(f"  Budget code    : {presupuesto.get('budget_code', 'N/A')}")
    print(f"  Space breakdown: {'YES' if has_breakdown else 'NO (fallback)'}")
    print(f"  Spaces found   : {n_spaces}")
    print(f"  Total coste    : {total_coste:,.2f} €")
    print()
    for spc in presupuesto.get("espacios", []):
        print(f"  {spc['nombre']:<35} {spc['coste']:>12,.2f} €  [{spc['zona']}]")
    print(f"{'='*60}\n")

    if args.dry_run:
        print("ℹ️  Dry-run: no data written. Use --confirm to import.")
        return

    session = get_session(db_path)
    archived_path: Path | None = None
    generated_excel: Path | None = None

    try:
        existing = get_budget_by_hash(session, file_hash)
        if existing:
            print(f"⚠️  File already imported (Budget ID={existing.id}). Skipping.")
            session.close()
            return

        # Create Budget record
        budget = Budget(
            filename=filepath.name,
            file_hash=file_hash,
            source_format="presto",
            total_cost=total_coste,
            surface_m2=None,
            building_type=None,
        )
        session.add(budget)
        session.flush()
        print(f"📥 Budget staged (ID={budget.id})")

        # Create SpaceRatio records
        ratios = calculate_space_ratios(presupuesto)
        space_rows = []
        for spc in ratios["espacios"]:
            sr = SpaceRatio(
                budget_id=budget.id,
                nombre=spc["nombre"],
                zona=spc["zona"],
                coste=spc["total"]["coste"],
                m2=spc["total"]["m2"],
                ratio_eur_m2=spc["total"]["ratio"],
                coste_prorrateado=spc["total"]["coste_prorrateado"],
            )
            space_rows.append(sr)
        session.add_all(space_rows)
        session.flush()
        print(f"   {len(space_rows)} SpaceRatio rows staged")

        # Generate space ratios Excel
        SPACE_RATIOS_DIR.mkdir(parents=True, exist_ok=True)
        stem = filepath.stem.replace(" ", "_")
        excel_name = f"{stem}_Ratios.xlsx"
        excel_path = SPACE_RATIOS_DIR / excel_name
        print(f"📊 Generating space ratios Excel → {excel_path}")
        generated_excel = Path(generate_space_ratios_excel(ratios, presupuesto, str(excel_path)))
        print(f"   Written: {generated_excel}")

        # Archive original
        print("📁 Archiving original file...")
        archived_path = archive_file(filepath)
        print(f"   Archived to: {archived_path}")

        # Item extraction + classification (HITO 4)
        n_items = _import_items(session, presupuesto, budget.id)
        print(f"   {n_items} item(s) clasificados y registrados")

        session.commit()
        print(f"✅ COMMITTED (Budget ID={budget.id})")
        print(f"✅ Space ratios Excel: {generated_excel}")

    except Exception as exc:
        session.rollback()
        print(f"❌ Import failed — rolling back: {exc}")
        if archived_path and archived_path.exists():
            archived_path.unlink(missing_ok=True)
        if generated_excel and generated_excel.exists():
            generated_excel.unlink(missing_ok=True)
        raise
    finally:
        session.close()


def _import_chapter_based(
    filepath: Path, raw_data: dict, file_hash: str, db_path: Path, args
) -> None:
    """Import Excel / BC3 file using chapter-level flow (original Hito 1+2 logic)."""
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

    session = get_session(db_path)
    archived_path: Path | None = None
    generated_excel: Path | None = None

    try:
        existing = get_budget_by_hash(session, file_hash)
        if existing:
            print(f"⚠️  File already imported (Budget ID={existing.id}). Skipping.")
            session.close()
            return

        session.add(budget)
        session.add_all(items)
        session.add_all(logs)
        session.flush()
        print(f"📥 Budget staged (ID={budget.id}, transaction pending)")

        print("📊 Recalculating ratios...")
        n = recalculate_all_ratios(session)
        session.flush()
        print(f"   {n} ratio(s) staged (transaction pending)")

        print("📊 Generating master Excel...")
        out_path = generate_master_excel(session)
        generated_excel = Path(out_path)
        print(f"   Master written: {out_path}")

        print("📁 Archiving original file...")
        archived_path = archive_file(filepath)
        print(f"   Archived to: {archived_path}")

        # Item extraction + classification (HITO 4)
        n_items = _import_items(session, raw_data, budget.id)
        print(f"   {n_items} item(s) clasificados y registrados")

        log["db_budget_id"] = budget.id
        log_path = save_log(log)
        print(f"📝 Import log saved: {log_path}")

        session.commit()
        print(f"✅ TRANSACTION COMMITTED (Budget ID={budget.id})")
        print(f"✅ Master updated: {out_path}")

    except Exception as exc:
        session.rollback()
        print(f"❌ Import failed — rolling back: {exc}")
        if archived_path and archived_path.exists():
            archived_path.unlink(missing_ok=True)
        if generated_excel and generated_excel.exists():
            pass
        raise
    finally:
        session.close()


def _import_items(session, budget_data: dict, budget_id: int) -> int:
    """Extract, classify, and persist items from a parsed budget. Returns item count."""
    raw_items = extract_items_from_budget(budget_data, budget_id=budget_id)
    if not raw_items:
        return 0

    count = 0
    for raw in raw_items:
        key = make_item_key(raw["descripcion"], raw["unidad"])
        if not key.strip("|"):
            continue

        classification = classify_item(raw)

        # Get or create ItemMaster
        master = session.query(ItemMaster).filter(ItemMaster.item_key == key).first()
        if master is None:
            master = ItemMaster(
                item_key=key,
                categoria=classification["categoria"],
                subcategoria=classification["subcategoria"],
                unidad=raw["unidad"],
                muestras_count=0,
            )
            session.add(master)
            session.flush()

        # Price comparison vs history
        historic = get_item_ratio_history(session, master.id)
        price_class = classify_new_item_price(raw, historic)

        instance = ItemInstance(
            budget_id=budget_id,
            item_master_id=master.id,
            codigo=raw["codigo"],
            descripcion=raw["descripcion"],
            categoria_original=raw["categoria_original"],
            unidad=raw["unidad"],
            cantidad=raw["cantidad"],
            precio_unitario=raw["precio_unitario"],
            precio_total=raw["precio_total"],
            categoria_detectada=classification["categoria"],
            confianza_clasificacion=classification["confianza"],
            desviacion_vs_historico=price_class.get("desviacion_porcentaje"),
            clasificacion_precio=price_class["clasificacion"],
            validation_status=raw["validation_status"],
        )
        session.add(instance)
        session.flush()

        # Update ItemMaster stats
        recalculate_item_master_stats(session, master.id)
        count += 1

    return count


if __name__ == "__main__":
    main()
