import sqlite3

# Conectare sau creare fișier SQLite
conn = sqlite3.connect("potholes.db")
cursor = conn.cursor()

# 🕳️ Tabela pentru gropi detectate cu YOLOv5
cursor.execute("""
CREATE TABLE IF NOT EXISTS potholes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    lat REAL,
    lon REAL,
    image_path TEXT
)
""")

# 🔧 Tabela pentru denivelări detectate cu accelerometru
cursor.execute("""
CREATE TABLE IF NOT EXISTS bumps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    lat REAL,
    lon REAL,
    bump_severity REAL
)
""")

conn.commit()
conn.close()
print("[✅] Baza de date a fost creată cu succes!")
