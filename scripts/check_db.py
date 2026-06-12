#!/usr/bin/env python3
"""Check database content."""

import sqlite3
from pathlib import Path

db_path = Path("data/master/ratios.db")
seed_path = Path("data/master/ratios.db.seed")

for path, label in [(seed_path, "SEED"), (db_path, "MAIN")]:
    if not path.exists():
        print(f"{label}: no existe")
        continue

    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"\n{label} ({path.stat().st_size} bytes):")
    print(f"  Tablas: {len(tables)}")

    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"    • {table_name}: {count} registros")

    conn.close()
