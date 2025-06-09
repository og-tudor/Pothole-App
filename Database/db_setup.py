import sqlite3

conn = sqlite3.connect("potholes.db")
cursor = conn.cursor()

# Users
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

# Bumps - Accelerometre
cursor.execute("""
CREATE TABLE IF NOT EXISTS bumps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    lat REAL,
    lon REAL,
    bump_severity REAL,
    conf REAL,
    run_id INTEGER
)
""")

# Potholes
cursor.execute("""
CREATE TABLE IF NOT EXISTS potholes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    lat REAL,
    lon REAL,
    image_path TEXT,
    conf REAL,
    run_id INTEGER
)
""")

# Alligator cracks
cursor.execute("""
CREATE TABLE IF NOT EXISTS alligator_cracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    lat REAL,
    lon REAL,
    image_path TEXT,
    conf REAL,
    run_id INTEGER
)
""")

# Longitudinal cracks
cursor.execute("""
CREATE TABLE IF NOT EXISTS longitudinal_cracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    lat REAL,
    lon REAL,
    image_path TEXT,
    conf REAL,
    run_id INTEGER
)
""")

# Transverse cracks
cursor.execute("""
CREATE TABLE IF NOT EXISTS transverse_cracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    lat REAL,
    lon REAL,
    image_path TEXT,
    conf REAL,
    run_id INTEGER
)
""")

# Manholes
cursor.execute("""
CREATE TABLE IF NOT EXISTS manholes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    lat REAL,
    lon REAL,
    image_path TEXT,
    conf REAL,
    run_id INTEGER
)
""")

# Reports
cursor.execute("""
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    problem_type TEXT NOT NULL,
    image_path TEXT NOT NULL,
    description TEXT,
    lat REAL,
    lon REAL,
    address TEXT
)
""")

conn.commit()
conn.close()
print("Tabelele au fost create cu succes!")
