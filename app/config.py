"""Application configuration — reads DATABASE_URL from environment."""
import os
from pathlib import Path

# Load .env if present (local dev)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except ImportError:
    pass

DATABASE_URL: str | None = os.getenv("DATABASE_URL")
