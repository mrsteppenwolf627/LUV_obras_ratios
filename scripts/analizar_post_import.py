#!/usr/bin/env python
# Script de auditoria post-importacion (FASE 2)
# Analiza resultados en BD SQLite

import sqlite3
import os
from datetime import datetime
from pathlib import Path

DB_PATH = "data/master/ratios.db"
LOGS_DIR = "logs"

# Setup logging
os.makedirs(LOGS_DIR, exist_ok=True)
timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
audit_log = Path(LOGS_DIR) / f"auditoria_{timestamp}.log"

def log_msg(msg, level="INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    with open(audit_log, "a") as f:
        f.write(line + "\n")

log_msg("=" * 50)
log_msg("INICIANDO AUDITORIA POST-IMPORTACION")
log_msg(f"BD: {DB_PATH}")
log_msg("=" * 50)

# Check database
if not os.path.exists(DB_PATH):
    log_msg(f"Base de datos no encontrada: {DB_PATH}", "ERROR")
    log_msg("Probablemente no se han importado datos aun", "WARNING")
    exit(1)

# Connect
try:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    log_msg("Conexion a BD establecida")
except Exception as e:
    log_msg(f"Error conectando a BD: {e}", "ERROR")
    exit(1)

# Query: Total items
try:
    cursor.execute("SELECT COUNT(*) as total FROM item_master")
    total_items = cursor.fetchone()["total"]
    log_msg(f"Total items en BD: {total_items}")
except Exception as e:
    log_msg(f"Error consultando BD: {e}", "ERROR")
    log_msg("Verificar si las tablas existen", "WARNING")
    conn.close()
    exit(1)

if total_items == 0:
    log_msg("No se encontraron items en la BD", "WARNING")
    log_msg("Ejecuta la importacion primero", "INFO")
    conn.close()
    exit(0)

# Query: Distribution by confidence (based on muestras_count)
log_msg("Consultando distribucion por confianza...")

cursor.execute("SELECT COUNT(*) as cnt FROM item_master WHERE muestras_count >= 10")
items_muy_solido = cursor.fetchone()["cnt"]

cursor.execute("SELECT COUNT(*) as cnt FROM item_master WHERE muestras_count BETWEEN 5 AND 9")
items_solido = cursor.fetchone()["cnt"]

cursor.execute("SELECT COUNT(*) as cnt FROM item_master WHERE muestras_count BETWEEN 2 AND 4")
items_debil = cursor.fetchone()["cnt"]

cursor.execute("SELECT COUNT(*) as cnt FROM item_master WHERE muestras_count = 1")
items_muy_debil = cursor.fetchone()["cnt"]

conf_dist = {
    "MUY_SOLIDO (N>=10)": items_muy_solido,
    "SOLIDO (N 5-9)": items_solido,
    "DEBIL (N 2-4)": items_debil,
    "MUY_DEBIL (N=1)": items_muy_debil
}

# Query: Top items by muestras_count
log_msg("Consultando items principales...")
cursor.execute("""
SELECT
  item_key,
  categoria,
  muestras_count,
  mediana_unitario,
  media_unitario,
  desv_std
FROM item_master
ORDER BY muestras_count DESC
LIMIT 15
""")

top_items = cursor.fetchall()

conn.close()

# Report
log_msg("")
log_msg("")
log_msg("=" * 50)
log_msg("REPORTE AUDITORIA POST-IMPORTACION")
log_msg("=" * 50)
log_msg("")

log_msg(f"FECHA: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
log_msg("")

log_msg("RESUMEN GENERAL")
log_msg("=" * 50)
log_msg(f"Total items (ItemMaster): {total_items}")
log_msg("")

log_msg("DISTRIBUCION POR CONFIANZA")
log_msg("=" * 50)

for estado, cant in conf_dist.items():
    pct = round((cant / total_items) * 100, 1) if total_items > 0 else 0
    log_msg(f"{estado} : {cant} items ({pct}%)")

log_msg("")

items_confiables = items_muy_solido + items_solido
pct_confiables = round((items_confiables / total_items) * 100, 1) if total_items > 0 else 0

log_msg("")

log_msg("TOP ITEMS POR CONVERGENCIA (N muestras)")
log_msg("=" * 50)

if len(top_items) > 0:
    for i, row in enumerate(top_items, 1):
        item = (row["item_key"][:40] if row["item_key"] else "unknown").ljust(40)
        cat = row["categoria"] or "unknown"
        n = row["muestras_count"] or 0
        media = row["media_unitario"] or 0.0
        desv = row["desv_std"] or 0.0
        log_msg(f"{i:2d}. {item} N={n:3d} media={media:10.2f} desv={desv:8.2f}")
else:
    log_msg("No hay items con datos", "WARNING")

log_msg("")
log_msg(f"LOGS: {audit_log}")
log_msg("=" * 50)

log_msg("Auditoria completada")
