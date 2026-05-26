#!/usr/bin/env python3
"""Create the SQLite database and all tables from scratch."""

import sys
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.db.models import DEFAULT_DB_PATH, init_db


def main() -> None:
    db_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DB_PATH
    print(f"Initialising database at: {db_path}")
    init_db(db_path)
    print("✅ Tables created (or already existed).")


if __name__ == "__main__":
    main()
