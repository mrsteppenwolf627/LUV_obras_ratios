#!/usr/bin/env python3
"""Local, one-shot importer: push an already-validated budget JSON into the
database pointed to by DATABASE_URL, reusing the validated ImportService.

NO HTTP, NO Vercel. Opens a single DB session from DATABASE_URL (env/.env),
runs the import inside one transaction (ImportService commits once at the end
on success; any error rolls back). Never prints DATABASE_URL or secrets.

Safety:
- Refuses to run unless DATABASE_URL points at the Supabase Transaction
  Pooler (host *.pooler.supabase.com), unless --allow-direct is passed.
- Re-runs the same pre-checks as the endpoint (line count, hash, price/qty
  > 0, BudgetImportRequest schema).
- Honors the file_hash dedup guard: if budget_imports already has the hash,
  ImportService raises DuplicateImportError -> we stop, no reinsert.

Usage:
  python scripts/import_local_to_supabase.py \
      --json data/temp_import_xlsx_only/260318_PEC.import.json \
      [--expect-lines 206] [--expect-hash <sha256>] [--allow-direct]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _counts(session):
    from src.db.schema import Budget, ItemMaster, ItemInstance
    out = {
        "budgets": session.query(Budget).count(),
        "item_master": session.query(ItemMaster).count(),
        "item_instances": session.query(ItemInstance).count(),
    }
    try:
        from src.db.schema import BudgetImport
        out["budget_imports"] = session.query(BudgetImport).count()
    except Exception:
        out["budget_imports"] = None
    return out


def main() -> int:
    import os

    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path,
                    default=Path("data/temp_import_xlsx_only/260318_PEC.import.json"))
    ap.add_argument("--expect-lines", type=int, default=206)
    ap.add_argument("--expect-hash", type=str,
                    default="106b511082fddbe8d280213bd36dcd3aa8c79cb097f146835150d482132a5510")
    ap.add_argument("--allow-direct", action="store_true",
                    help="Permit a non-pooler (direct) DATABASE_URL.")
    args = ap.parse_args()

    # Load .env exactly like the app, without printing anything sensitive.
    try:
        import app.config  # noqa: F401
    except Exception:
        pass

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("ABORT: DATABASE_URL no está definida en el entorno/.env.")
        return 2

    host = (urlparse(db_url).hostname or "")
    is_pooler = host.endswith("pooler.supabase.com")
    if not is_pooler and not args.allow_direct:
        print("ABORT: DATABASE_URL no apunta al Transaction Pooler "
              "(*.pooler.supabase.com). Usa el pooler o pasa --allow-direct "
              "explícitamente. (No se imprime la URL.)")
        return 3

    # Pre-checks on the JSON payload (no DB yet).
    if not args.json.exists():
        print(f"ABORT: no existe el JSON {args.json}")
        return 2
    data = json.loads(args.json.read_text(encoding="utf-8"))
    lineas = data.get("lineas", [])
    if len(lineas) != args.expect_lines:
        print(f"ABORT: el JSON tiene {len(lineas)} líneas, se esperaban {args.expect_lines}.")
        return 4
    if data.get("file_hash") != args.expect_hash:
        print("ABORT: file_hash del JSON no coincide con el esperado.")
        return 4
    bad_price = [l.get("numero") for l in lineas
                 if not (isinstance(l.get("precio_unitario"), (int, float)) and l["precio_unitario"] > 0)]
    bad_qty = [l.get("numero") for l in lineas
               if not (isinstance(l.get("cantidad"), (int, float)) and l["cantidad"] > 0)]
    if bad_price or bad_qty:
        print(f"ABORT: precios<=0={len(bad_price)} cantidades<=0={len(bad_qty)} (no se importa).")
        return 4

    from app.schemas.import_budgets import BudgetImportRequest
    try:
        req = BudgetImportRequest(**data)
    except Exception as e:
        print("ABORT: el payload no pasa BudgetImportRequest:", repr(e))
        return 4

    print(f"Pre-checks OK: {len(req.lineas)} líneas, hash válido, pooler={is_pooler} "
          f"(allow_direct={args.allow_direct}).")

    # Open session and import inside one transaction.
    from app.database import get_db
    from app.services.import_service import ImportService, DuplicateImportError

    session = get_db()
    try:
        before = _counts(session)
        t0 = time.time()
        try:
            resp = ImportService(session).importar(
                filename=req.filename,
                file_hash=req.file_hash,
                building_type=req.building_type,
                lineas=req.lineas,
            )
        except DuplicateImportError as dup:
            session.rollback()
            print("DUPLICADO: budget_imports ya contiene este file_hash "
                  f"(importado {dup.import_date}). No se fuerza reinserción.")
            return 5
        except Exception:
            session.rollback()
            print("ERROR durante la importación -> ROLLBACK. No se escribió nada.")
            raise
        elapsed = time.time() - t0
        after = _counts(session)

        print("=== IMPORTACIÓN COMPLETADA (commit aplicado por ImportService) ===")
        print("file_hash importado :", req.file_hash)
        print("status              :", resp.status)
        print("items_creados       :", resp.items_creados)
        print("items_duplicados    :", resp.items_duplicados)
        print("muestras_actualizadas:", resp.muestras_actualizadas)
        print("duración (s)        :", round(elapsed, 2))
        print("--- conteos antes -> después ---")
        for k in ("budgets", "budget_imports", "item_master", "item_instances"):
            print(f"  {k:16} {before.get(k)} -> {after.get(k)}")
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
