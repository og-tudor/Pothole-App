import sqlite3

# Conectare la fișierul SQLite existent
conn = sqlite3.connect("potholes.db")
cursor = conn.cursor()

# 🧑‍💼 Tabela pentru utilizatori
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

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

# 🐊 Alligator cracks
cursor.execute("""
CREATE TABLE IF NOT EXISTS alligator_cracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    lat REAL,
    lon REAL,
    image_path TEXT
)
""")

# 🧱 Block cracks
cursor.execute("""
CREATE TABLE IF NOT EXISTS block_cracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    lat REAL,
    lon REAL,
    image_path TEXT
)
""")

# ➖ Longitudinal cracks
cursor.execute("""
CREATE TABLE IF NOT EXISTS longitudinal_cracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    lat REAL,
    lon REAL,
    image_path TEXT
)
""")

# 🔁 Transverse cracks
cursor.execute("""
CREATE TABLE IF NOT EXISTS transverse_cracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    lat REAL,
    lon REAL,
    image_path TEXT
)
""")

# 🔧 Repairs
cursor.execute("""
CREATE TABLE IF NOT EXISTS repairs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    lat REAL,
    lon REAL,
    image_path TEXT
)
""")

# ❓ Other corruptions
cursor.execute("""
CREATE TABLE IF NOT EXISTS other_corruptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    lat REAL,
    lon REAL,
    image_path TEXT
)
""")

conn.commit()
conn.close()
print("[✅] Tabelele au fost create cu succes în baza de date existentă!")
