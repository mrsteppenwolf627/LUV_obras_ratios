"""Vercel Python Serverless entry point for LUV Obras Ratios API.

All /api/* requests are rewritten to this file via vercel.json.
FastAPI receives the full original path (e.g. /api/ratios/chapters),
which matches the routers that mount under prefix="/api".

Endpoints excluded from serverless (require local filesystem):
  POST /api/import        — file upload + temp files + Excel generation
  GET  /api/export/...    — large Excel file streaming
  GET  /api/master        — reads local SQLite + Excel
"""

import sys
from pathlib import Path

# Make app.* and src.* importable when Vercel runs this file directly.
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Triggers python-dotenv load for local testing; no-op on Vercel
# (env vars come from the Vercel dashboard there).
import app.config  # noqa: F401

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.visuales import router as visuales_router
from app.routers.items_analisis import router as items_analisis_router
from app.routers.import_budgets import router as import_budgets_router
from app.routers.stats import router as stats_router
from app.routers.items_extended import router as items_extended_router

app = FastAPI(title="LUV Obras Ratios API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(visuales_router)
app.include_router(items_analisis_router)
app.include_router(import_budgets_router)
app.include_router(stats_router)
app.include_router(items_extended_router)


@app.get("/api/health")
def health():
    return {"status": "ok", "runtime": "vercel-serverless"}
