import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parents[2] / "output" / "forensics.db"

connection = sqlite3.connect(db_path)

tables = connection.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
    AND name NOT LIKE 'sqlite_%'
    ORDER BY name
""").fetchall()

print("Tables:")
for table in tables:
    print("-", table[0])

connection.execute("PRAGMA foreign_keys = ON")
print("\nForeign keys enabled:", connection.execute("PRAGMA foreign_keys").fetchone()[0])

connection.close()