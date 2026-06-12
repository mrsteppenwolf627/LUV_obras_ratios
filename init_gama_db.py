#!/usr/bin/env python3

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "master" / "ratios.db"


def init_db():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # 1. Crear tabla gama_ranges
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gama_ranges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            material_type TEXT NOT NULL,
            categoria TEXT NOT NULL,
            medium_min REAL NOT NULL,
            medium_max REAL NOT NULL,
            premium_min REAL NOT NULL,
            premium_max REAL NOT NULL,
            luxury_min REAL NOT NULL,
            luxury_max REAL NOT NULL,
            luxury_plus_min REAL NOT NULL,
            luxury_plus_max REAL NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(material_type, categoria)
        )
    """)

    # 2. Insertar seed data
    gama_data = [
        ('PORCELANA', 'SUELOS', 15, 25, 25, 40, 40, 60, 60, 100),
        ('PIEDRA', 'SUELOS', 30, 50, 50, 80, 80, 150, 150, 300),
        ('PINTURA', 'PAREDES', 5, 10, 10, 20, 20, 40, 40, 80),
        ('METAL', 'ACCESORIOS', 50, 100, 100, 180, 180, 300, 300, 500),
        ('VIDRIO', 'CARPINTERIA', 40, 80, 80, 150, 150, 250, 250, 400),
        ('MADERA', 'SUELOS', 10, 25, 25, 60, 60, 150, 150, 300),
        ('TEXTIL', 'SUELOS', 8, 15, 15, 35, 35, 80, 80, 200),
        ('ENCIMERA', 'COCINA', 20, 40, 40, 80, 80, 150, 150, 300),
    ]

    for material, categoria, m_min, m_max, p_min, p_max, l_min, l_max, lp_min, lp_max in gama_data:
        cursor.execute("""
            INSERT OR IGNORE INTO gama_ranges
            (material_type, categoria, medium_min, medium_max, premium_min, premium_max,
             luxury_min, luxury_max, luxury_plus_min, luxury_plus_max)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (material, categoria, m_min, m_max, p_min, p_max, l_min, l_max, lp_min, lp_max))

    # 3. Añadir columna gama_asignada si no existe
    try:
        cursor.execute("ALTER TABLE item_master ADD COLUMN gama_asignada TEXT DEFAULT 'SIN_CLASIFICAR'")
    except sqlite3.OperationalError:
        pass  # Ya existe

    # 4. Asignar gama a cada item
    cursor.execute("SELECT id, categoria, mediana_unitario FROM item_master")
    items = cursor.fetchall()

    for item_id, item_cat, unitario in items:
        if unitario is None:
            gama = 'SIN_CLASIFICAR'
        else:
            cursor.execute(
                "SELECT medium_min, premium_min, luxury_min, luxury_plus_min FROM gama_ranges WHERE categoria = ? LIMIT 1",
                (item_cat,)
            )
            row = cursor.fetchone()
            if row:
                m_min, p_min, l_min, lp_min = row
                if unitario < p_min:
                    gama = 'MEDIUM'
                elif unitario < l_min:
                    gama = 'PREMIUM'
                elif unitario < lp_min:
                    gama = 'LUXURY'
                else:
                    gama = 'LUXURY_PLUS'
            else:
                gama = 'SIN_CLASIFICAR'
        cursor.execute("UPDATE item_master SET gama_asignada = ? WHERE id = ?", (gama, item_id))

    conn.commit()
    conn.close()
    print(f"[OK] BD inicializada - {len(items)} items asignados")


if __name__ == "__main__":
    init_db()
