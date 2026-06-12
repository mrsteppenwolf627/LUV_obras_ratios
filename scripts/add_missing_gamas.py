"""Add missing gama_ranges entries and reassign SIN_CLASIFICAR items."""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "master" / "ratios.db"

MISSING_GAMAS = [
    # (material_type, categoria, m_min, m_max, p_min, p_max, l_min, l_max, lp_min, lp_max)
    ("ELECTRICIDAD", "INSTALACIONES", 30, 50,  50, 100, 100, 200, 200, 400),
    ("ACCESORIOS",   "INSTALACIONES", 20, 40,  40,  80,  80, 150, 150, 300),
]


def _find_gama_row(cursor, item_categoria: str):
    """
    Look up gama_ranges for a given item categoria.
    Strategy: try material_type match first, then categoria match.
    This handles both PINTURA (material_type='PINTURA') and
    CARPINTERIA (categoria='CARPINTERIA') cases.
    """
    cursor.execute(
        "SELECT medium_min, premium_min, luxury_min, luxury_plus_min "
        "FROM gama_ranges WHERE material_type = ? LIMIT 1",
        (item_categoria,),
    )
    row = cursor.fetchone()
    if row:
        return row

    cursor.execute(
        "SELECT medium_min, premium_min, luxury_min, luxury_plus_min "
        "FROM gama_ranges WHERE categoria = ? LIMIT 1",
        (item_categoria,),
    )
    return cursor.fetchone()


def _classify(precio: float, m_min, p_min, l_min, lp_min) -> str:
    if precio < p_min:
        return "MEDIUM"
    if precio < l_min:
        return "PREMIUM"
    if precio < lp_min:
        return "LUXURY"
    return "LUXURY_PLUS"


def agregar_gamas_faltantes() -> dict:
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    try:
        # 1. Insertar materiales nuevos (idempotente)
        insertados = 0
        for row in MISSING_GAMAS:
            cursor.execute(
                "INSERT OR IGNORE INTO gama_ranges "
                "(material_type, categoria, medium_min, medium_max, "
                " premium_min, premium_max, luxury_min, luxury_max, "
                " luxury_plus_min, luxury_plus_max, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
                row,
            )
            if cursor.rowcount:
                insertados += 1
                print(f"  [+] Insertado: material_type={row[0]}, categoria={row[1]}")

        # 2. Reasignar items SIN_CLASIFICAR
        cursor.execute(
            "SELECT id, categoria, mediana_unitario "
            "FROM item_master WHERE gama_asignada = 'SIN_CLASIFICAR'"
        )
        pendientes = cursor.fetchall()

        reasignados = 0
        sin_rango = 0
        detalle = []

        for item_id, item_cat, mediana in pendientes:
            if mediana is None:
                detalle.append((item_id, item_cat, None, "SIN_CLASIFICAR", "sin mediana"))
                continue

            gama_row = _find_gama_row(cursor, item_cat)
            if gama_row:
                m_min, p_min, l_min, lp_min = gama_row
                nueva_gama = _classify(mediana, m_min, p_min, l_min, lp_min)
                cursor.execute(
                    "UPDATE item_master SET gama_asignada = ? WHERE id = ?",
                    (nueva_gama, item_id),
                )
                reasignados += 1
                detalle.append((item_id, item_cat, mediana, nueva_gama, "ok"))
            else:
                sin_rango += 1
                detalle.append((item_id, item_cat, mediana, "SIN_CLASIFICAR", "sin rango"))

        conn.commit()
        return {
            "insertados": insertados,
            "reasignados": reasignados,
            "sin_rango": sin_rango,
            "detalle": detalle,
        }

    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    print(f"BD: {DB_PATH}")
    print()

    result = agregar_gamas_faltantes()

    print()
    print(f"Materiales insertados:  {result['insertados']}")
    print(f"Items reasignados:      {result['reasignados']}")
    print(f"Items sin rango:        {result['sin_rango']}")
    print()
    print("Detalle items procesados:")
    for item_id, cat, mediana, gama, estado in result["detalle"]:
        med_str = f"{mediana:.2f}" if mediana else "None"
        print(f"  [{item_id}] {cat:15s} mediana={med_str:8s} -> {gama}  ({estado})")

    # Distribución final
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    print()
    print("Distribucion final gama_asignada:")
    c.execute("SELECT gama_asignada, COUNT(*) FROM item_master GROUP BY gama_asignada ORDER BY COUNT(*) DESC")
    for gama, count in c.fetchall():
        print(f"  {gama}: {count}")
    conn.close()
