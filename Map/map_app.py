from flask import Flask, jsonify, render_template, request
import sqlite3
import os

app = Flask(__name__)
db_route = '../Database/potholes.db'
image_dir = 'static/pothole_images'

@app.route('/')
def map_view():
    return render_template('index.html')

@app.route('/api/potholes')
def get_potholes():
    conn = sqlite3.connect(db_route)
    cursor = conn.cursor()
    cursor.execute("SELECT lat, lon, image_path, timestamp FROM potholes")
    rows = cursor.fetchall()
    conn.close()
    return jsonify([
        {
            "lat": row[0],
            "lon": row[1],
            "image": row[2].replace("./static", "/static"),
            "timestamp": row[3]
        }
        for row in rows
    ])

@app.route('/api/delete_image', methods=['POST'])
def delete_image():
    data = request.json
    image_path = data.get("image_path")
    if not image_path:
        return jsonify({"error": "Lipsă cale imagine"}), 400

    # Creează calea absolută spre fișier
    full_image_path = os.path.abspath(os.path.join('static', image_path.replace("/static/", "")))

    # Șterge fișierul imagine
    try:
        if os.path.exists(full_image_path):
            os.remove(full_image_path)
    except Exception as e:
        print(f"Eroare la ștergerea imaginii: {e}")

    # Șterge din baza de date
    conn = sqlite3.connect(db_route)
    cur = conn.cursor()
    cur.execute("DELETE FROM potholes WHERE image_path = ?", (image_path.replace("/static", "./static"),))
    conn.commit()
    conn.close()

    return jsonify({"status": "deleted"})

@app.route('/api/bumps')
def get_bumps():
    conn = sqlite3.connect(db_route)
    cursor = conn.cursor()
    cursor.execute("SELECT lat, lon, bump_severity FROM bumps")
    rows = cursor.fetchall()
    conn.close()

    return jsonify([
        {
            "lat": row[0],
            "lon": row[1],
            "intensity": row[2]  # păstrăm "intensity" în JSON pentru JS
        }
        for row in rows
    ])



if __name__ == '__main__':
    app.run(debug=True)
