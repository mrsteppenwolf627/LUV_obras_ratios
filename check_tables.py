import sqlite3

conn = sqlite3.connect('backend/data.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cursor.fetchall()

print("Tablas en BD:")
for table in tables:
    print(f"  - {table[0]}")

conn.close()