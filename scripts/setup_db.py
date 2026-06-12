#!/usr/bin/env python3
"""
Setup script to initialize the database with seed data.

This script:
1. Checks if the main database exists
2. If not, restores from the seed file (data/master/ratios.db.seed)
3. If seed doesn't exist, creates an empty database from schema
4. Initializes all tables ensuring reproducibility across environments
"""

import sys
import shutil
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.db.models import DEFAULT_DB_PATH, init_db


SEED_PATH = Path("data/master/ratios.db.seed")


def setup_database() -> None:
    """Initialize database: restore from seed or create fresh."""

    # Ensure data directory exists
    DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    if DEFAULT_DB_PATH.exists():
        print(f"✅ Database already exists at: {DEFAULT_DB_PATH}")
        return

    print(f"📦 Setting up database at: {DEFAULT_DB_PATH}")

    # Try to restore from seed file
    if SEED_PATH.exists():
        try:
            print(f"🔄 Restoring from seed: {SEED_PATH}")
            shutil.copy2(SEED_PATH, DEFAULT_DB_PATH)
            print(f"✅ Database restored from seed ({SEED_PATH.stat().st_size} bytes)")
            return
        except Exception as e:
            print(f"⚠️  Failed to restore from seed: {e}")
            print("   Creating fresh database instead...")
    else:
        print(f"ℹ️  Seed file not found: {SEED_PATH}")
        print("   Creating fresh database from schema...")

    # Create empty database from schema
    init_db(DEFAULT_DB_PATH)
    print(f"✅ Fresh database created at: {DEFAULT_DB_PATH}")


if __name__ == "__main__":
    try:
        setup_database()
        print("\n✅ Setup complete. You can now run the application.")
    except Exception as e:
        print(f"\n❌ Setup failed: {e}", file=sys.stderr)
        sys.exit(1)
