from flask import Flask, jsonify, render_template
import sqlite3

app = Flask(__name__)

@app.route('/')
def map_view():
    return render_template('index.html')


db_route = '../Database/potholes.db'
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
            "image": row[2].replace("./static", "/static"),  # ✔️ corectă acum
            "timestamp": row[3]
        }
        for row in rows
    ])



if __name__ == '__main__':
    app.run(debug=True)
