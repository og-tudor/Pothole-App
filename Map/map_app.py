from flask import Flask, jsonify, render_template, request, redirect, make_response
import sqlite3
import os
import jwt
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
db_route = '../Database/potholes.db'
image_dir = 'static/pothole_images'
# === Citim cheia JWT din fișier ===
with open('./JWT_key', 'r') as f:
    JWT_SECRET = f.read().strip()



# === Middleware pentru autentificare ===
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get('token')
        user_id = verify_token(token)
        if not user_id:
            return redirect("/login")
        return f(user_id, *args, **kwargs)
    return decorated_function

@login_required
def get_location_name(lat, lon):
    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lon, "format": "json"},
            headers={"User-Agent": "your-app-name"}
        )
        data = response.json()
        return data.get("display_name", "")
    except Exception as e:
        print("Eroare geocodare inversă:", e)
        return ""

@app.route('/api/defects')
@login_required
def get_defects(user_id):
    defect_tables = {
        "pothole": "potholes",
        "alligator_crack": "alligator_cracks",
        "block_crack": "block_cracks",
        "longitudinal_crack": "longitudinal_cracks",
        "transverse_crack": "transverse_cracks",
        "repair": "repairs",
        "other_corruption": "other_corruptions"
    }

    conn = sqlite3.connect(db_route)
    cursor = conn.cursor()
    all_defects = []

    for defect_type, table in defect_tables.items():
        cursor.execute(f"SELECT lat, lon, image_path, timestamp FROM {table}")
        rows = cursor.fetchall()
        for row in rows:
            all_defects.append({
                "type": defect_type,
                "lat": row[0],
                "lon": row[1],
                "image": row[2].replace("./static", "/static"),
                "timestamp": row[3]
            })

    conn.close()
    return jsonify(all_defects)



# @app.route('/')
# @login_required
# def map_view(user_id):
#     return render_template('index.html')




# === Pagina de înregistrare ===
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        conn = sqlite3.connect(db_route)
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                        (username, email, password))
            conn.commit()
        except sqlite3.IntegrityError:
            # ✅ trimitem mesajul de eroare către HTML
            return render_template('register.html', error="Utilizator sau email deja existent!")
        finally:
            conn.close()

        return redirect('/login')

    return render_template('register.html')

@app.route('/images')
@login_required
def images_view(user_id):
    return render_template("images.html", title="Imagini")


# === Pagina de login ===
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(db_route)
        cur = conn.cursor()
        cur.execute("SELECT id, password FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password):
            token = generate_token(user[0])
            resp = make_response(redirect('/'))
            resp.set_cookie('token', token, httponly=True, max_age=86400)
            return resp

        # ✅ Trimit flag de eroare în template
        return render_template('login.html', error=True)

    return render_template('login.html')


# === Logout ===
@app.route('/logout')
def logout():
    resp = make_response(redirect('/login'))
    resp.set_cookie('token', '', expires=0)
    return resp

# === JWT helper ===
def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def verify_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload['user_id']
    except:
        return None


@app.route('/api/potholes')
@login_required
def get_potholes(user_id):
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
@login_required
def delete_image(user_id):
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

@app.route('/')
@login_required
def map_view(user_id):
    return render_template("map_view.html", title="Hartă")

@app.route('/statistics')
@login_required
def statistics_view(user_id):
    return render_template("statistics.html", title="Statistici")


@app.route('/api/bumps')
@login_required
def get_bumps(user_id):
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
