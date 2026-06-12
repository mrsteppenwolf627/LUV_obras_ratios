#!/usr/bin/env python3
"""Create the SQLite database and all tables from scratch."""

import sys
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.db.models import DEFAULT_DB_PATH, init_db, get_session
from scripts.seed_gama_ranges import seed_gama_ranges


def main() -> None:
    db_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DB_PATH
    print(f"Initialising database at: {db_path}")
    init_db(db_path)
    print("[OK] Tables created (or already existed).")

    # Seed gama_ranges data
    print("Seeding gama_ranges...")
    session = get_session(db_path)
    inserted = seed_gama_ranges(session)
    print(f"[OK] {inserted} gama_ranges records inserted/verified.")
    session.close()


if __name__ == "__main__":
    main()
