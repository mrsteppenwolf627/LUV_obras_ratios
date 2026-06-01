"""FastAPI application — LUV Obras Ratios backend."""
import sys
from pathlib import Path

# Make src.* importable when running from the project root
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import shutil
import tempfile
from datetime import datetime, timezone

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .database import get_db
from .crud.ratios import get_master_data
from .crud.budgets import get_archived_budgets
from .crud.items import get_item_history, get_items_by_category, search_items
from .utils.stats import get_stats
from .utils.excel_export import generate_or_get_excel
from .routers.visuales import router as visuales_router, invalidar_cache_chapters
from .routers.items_analisis import router as items_analisis_router

app = FastAPI(title="LUV Obras Ratios API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://agentic-developer-platform-adp.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(visuales_router)
app.include_router(items_analisis_router)


@app.get("/api/master")
def api_master():
    session = get_db()
    try:
        metadata, ratios = get_master_data(session)
        return {"metadata": metadata, "ratios": ratios}
    finally:
        session.close()


@app.get("/api/archived")
def api_archived():
    session = get_db()
    try:
        return {"archived": get_archived_budgets(session)}
    finally:
        session.close()


@app.get("/api/ratios/stats")
def api_stats():
    session = get_db()
    try:
        return get_stats(session)
    finally:
        session.close()


@app.post("/api/import")
async def api_import(file: UploadFile = File(...)):
    from src.core.auditor import compute_file_hash
    from src.core.bc3_reader import read_bc3
    from src.core.excel_reader import read_excel
    from src.core.normalizer import normalize
    from src.db.queries import get_budget_by_hash
    from src.export.excel_master_generator import generate_master_excel
    from src.ratios.calculator import recalculate_all_ratios

    filename = file.filename or "unknown"
    ext = Path(filename).suffix.lower()

    if ext not in (".xlsx", ".xlsm", ".bc3", ".presto"):
        return {
            "success": False,
            "message": f"Formato no soportado: {ext}. Use .xlsx, .xlsm, .bc3 o .Presto",
        }

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = Path(tmp.name)

    session = get_db()
    try:
        from src.core.auditor import compute_file_hash
        from src.db.queries import get_budget_by_hash

        file_hash = compute_file_hash(tmp_path)

        existing = get_budget_by_hash(session, file_hash)
        if existing:
            return {
                "success": False,
                "message": f"Este archivo ya fue importado (Budget ID={existing.id})",
            }

        if ext == ".presto":
            return await _import_presto_api(
                session, tmp_path, filename, file_hash, _ROOT
            )

        from src.core.bc3_reader import read_bc3
        from src.core.excel_reader import read_excel
        from src.core.normalizer import normalize
        from src.export.excel_master_generator import generate_master_excel
        from src.ratios.calculator import recalculate_all_ratios

        fmt = "excel" if ext in (".xlsx", ".xlsm") else "bc3"
        raw_data = read_excel(tmp_path) if fmt == "excel" else read_bc3(tmp_path)

        if raw_data.get("errors"):
            return {
                "success": False,
                "message": "Error al leer: " + "; ".join(raw_data["errors"]),
            }

        budget, items, logs = normalize(
            raw_data, surface_m2=None, building_type=None, file_hash=file_hash
        )
        budget.filename = filename

        session.add(budget)
        session.add_all(items)
        session.add_all(logs)
        session.flush()

        ratios_created = recalculate_all_ratios(session)
        session.flush()
        invalidar_cache_chapters()

        generate_master_excel(session)

        archived_dir = _ROOT / "data" / "archived_budgets"
        archived_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        shutil.copy2(tmp_path, archived_dir / f"{ts}_{filename}")

        session.commit()

        return {
            "success": True,
            "message": "Archivo importado correctamente",
            "budget_id": budget.id,
            "filename": filename,
            "file_hash": file_hash,
            "chapter_count": len(items),
            "total_amount": float(budget.total_cost or 0.0),
            "ratios_created": ratios_created,
        }

    except Exception as exc:
        session.rollback()
        return {"success": False, "message": f"Error al importar: {exc}"}

    finally:
        session.close()
        tmp_path.unlink(missing_ok=True)


async def _import_presto_api(session, tmp_path: Path, filename: str, file_hash: str, root: Path) -> dict:
    """Handle Presto import inside the API endpoint."""
    from src.core.presto_reader import parse_presto
    from src.db.schema import Budget, SpaceRatio
    from src.export.space_ratios_generator import generate_space_ratios_excel
    from src.ratios.space_calculator import calculate_space_ratios

    presupuesto = parse_presto(tmp_path)
    presupuesto["filename"] = filename

    if presupuesto.get("errors"):
        return {"success": False, "message": "Error al leer Presto: " + "; ".join(presupuesto["errors"])}

    budget = Budget(
        filename=filename,
        file_hash=file_hash,
        source_format="presto",
        total_cost=presupuesto.get("total_coste", 0.0),
        surface_m2=None,
        building_type=None,
    )
    session.add(budget)
    session.flush()

    ratios = calculate_space_ratios(presupuesto)
    space_rows = [
        SpaceRatio(
            budget_id=budget.id,
            nombre=spc["nombre"],
            zona=spc["zona"],
            coste=spc["total"]["coste"],
            m2=spc["total"]["m2"],
            ratio_eur_m2=spc["total"]["ratio"],
            coste_prorrateado=spc["total"]["coste_prorrateado"],
        )
        for spc in ratios["espacios"]
    ]
    session.add_all(space_rows)
    session.flush()

    exports_dir = root / "data" / "exports" / "space_ratios"
    exports_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(filename).stem.replace(" ", "_")
    excel_path = exports_dir / f"{stem}_Ratios.xlsx"
    generate_space_ratios_excel(ratios, presupuesto, str(excel_path))

    archived_dir = root / "data" / "archived_budgets"
    archived_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    shutil.copy2(tmp_path, archived_dir / f"{ts}_{filename}")

    session.commit()

    return {
        "success": True,
        "message": "Presto importado correctamente",
        "budget_id": budget.id,
        "filename": filename,
        "file_hash": file_hash,
        "space_count": len(space_rows),
        "total_amount": float(presupuesto.get("total_coste", 0.0)),
        "has_space_breakdown": presupuesto.get("has_space_breakdown", False),
        "excel_path": str(excel_path),
        "warnings": presupuesto.get("warnings", []),
    }


@app.get("/api/items/search")
def api_items_search(q: str = "", categoria: str = "", limit: int = 100):
    session = get_db()
    try:
        items = search_items(
            session,
            q=q or None,
            categoria=categoria or None,
            limit=min(limit, 500),
        )
        return {"items": items, "count": len(items)}
    finally:
        session.close()


@app.get("/api/items/by-category")
def api_items_by_category(categoria: str):
    if not categoria:
        return {"error": "El parámetro 'categoria' es obligatorio"}
    session = get_db()
    try:
        items = get_items_by_category(session, categoria)
        return {"categoria": categoria.upper(), "items": items, "count": len(items)}
    finally:
        session.close()


@app.get("/api/items/{item_key:path}/history")
def api_item_history(item_key: str):
    session = get_db()
    try:
        result = get_item_history(session, item_key)
        if result is None:
            raise HTTPException(status_code=404, detail=f"Ítem '{item_key}' no encontrado")
        return result
    finally:
        session.close()


@app.get("/api/export/master.xlsx")
def api_export_master():
    session = get_db()
    try:
        excel_path = generate_or_get_excel(session)
    finally:
        session.close()

    if not excel_path.exists():
        raise HTTPException(status_code=404, detail="Master Excel no disponible")

    return FileResponse(
        path=str(excel_path),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="master_ratios.xlsx",
    )
