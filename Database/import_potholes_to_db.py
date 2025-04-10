import json
import sqlite3
import os

# Căi către fișiere
json_path = "./images/potholes_deduplicated.json"
db_path = "potholes.db"

# 1. Încarcă datele din JSON
with open(json_path, "r", encoding="utf-8") as f:
    potholes = json.load(f)

# 2. Conectare la baza de date
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 3. Inserează fiecare intrare, adăugând prefixul './images/' la image_path
inserted = 0
for entry in potholes:
    try:
        image_path = os.path.join("./images", entry["image"])

        cursor.execute("""
            INSERT INTO potholes (timestamp, lat, lon, image_path)
            VALUES (?, ?, ?, ?)
        """, (
            entry["timestamp"],
            entry["lat"],
            entry["lon"],
            image_path
        ))
        inserted += 1
    except Exception as e:
        print(f"[⚠️] Eroare la inserare: {e}")

# 4. Finalizare
conn.commit()
conn.close()

print(f"[✅] {inserted} intrări au fost adăugate în baza de date.")
