import cv2
import socket
import struct
import numpy as np
import torch
import os
import time
import json
import threading
import warnings
import math
import sqlite3

warnings.filterwarnings("ignore", category=FutureWarning)

FLASK_IMAGE_DIR = "../Map/static/pothole_images"
FLASK_DB_PATH = "../Database/potholes.db"

os.makedirs(FLASK_IMAGE_DIR, exist_ok=True)

# 🧬 YOLOv5
model = torch.hub.load('ultralytics/yolov5', 'custom', path='best_windows_exp5_win.pt')
model.conf = 0.85

# 🛰️ Protecție anti-dublură
last_saved = {"timestamp": None, "lat": None, "lon": None}

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # km
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c * 1000  # metri


data = b""
payload_size = struct.calcsize("Q")

last_gps = {"lat": None, "lon": None}
SAVE_DIR = "./test_results"
os.makedirs(SAVE_DIR, exist_ok=True)

# 🛰️ Raspberry Pi stream
def try_connect(ip_list, port, desc="conexiune"):
    for ip in ip_list:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)
            s.connect((ip, port))
            print(f"[🟢] Reușit {desc} la {ip}:{port}")
            return s
        except Exception as e:
            print(f"[⛔] Eșuat {desc} la {ip}:{port} — {e}")
    raise ConnectionError(f"[💥] Nu s-a putut stabili {desc} pe niciun IP.")

# router, AP si cablue ethernet
PI_IPS = ['192.168.1.138', '192.168.4.1', '192.168.5.1'] 

# === Conectare la stream video ===
sock = try_connect(PI_IPS, 8000, "video")

# === Conectare la stream senzor ===
def listen_sensor_data():
    sensor_sock = try_connect(PI_IPS, 9000, "senzor (simulat)")
    try:
        while True:
            data = sensor_sock.recv(1024).decode().strip()
            if data:
                denivelare, lat, lon = map(float, data.split(","))
                last_gps["lat"] = lat
                last_gps["lon"] = lon
                print(f"[🛣️] Denivelare: {denivelare:.2f} | GPS: {lat}, {lon}")
    except Exception as e:
        print(f"[‼️] Eroare senzor pe client: {e}")
    finally:
        sensor_sock.close()


threading.Thread(target=listen_sensor_data, daemon=True).start()

try:
    while True:
        while len(data) < payload_size:
            packet = sock.recv(4 * 1024)
            if not packet:
                raise ConnectionError("Conexiune întreruptă la citire lungime")
            data += packet

        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack("Q", packed_msg_size)[0]

        while len(data) < msg_size:
            packet = sock.recv(4 * 1024)
            if not packet:
                raise ConnectionError("Conexiune întreruptă la citire frame")
            data += packet

        frame_data = data[:msg_size]
        data = data[msg_size:]

        frame = cv2.imdecode(np.frombuffer(frame_data, dtype=np.uint8), cv2.IMREAD_COLOR)
        results = model(frame)
        results.render()

        labels = results.names
        detected = results.pred[0]

        for *box, conf, cls in detected:
            label = labels[int(cls)]
            if "pothole" in label.lower():
                print(f"[🕳️] Gropă detectată! {conf:.2f}")

                if last_gps["lat"] is None or last_gps["lon"] is None:
                    print("[⚠️] Coordonate GPS lipsă — se sare")
                    break

                now = time.time()
                lat, lon = float(last_gps["lat"]), float(last_gps["lon"])
                distance = haversine(lat, lon, last_saved["lat"], last_saved["lon"]) if last_saved["lat"] else float("inf")

                if (last_saved["timestamp"] and now - last_saved["timestamp"] < 2) or (distance < 8):
                    print("[⛔] Dublură detectată — ignorată")
                    break

                timestamp = time.strftime("%Y%m%d-%H%M%S")
                img_name = f"groapa_{timestamp}.jpg"
                flask_img_path = os.path.join(FLASK_IMAGE_DIR, img_name)
                cv2.imwrite(flask_img_path, frame)

                try:
                    conn = sqlite3.connect(FLASK_DB_PATH)
                    cur = conn.cursor()
                    cur.execute("""
                        INSERT INTO potholes (timestamp, lat, lon, image_path)
                        VALUES (?, ?, ?, ?)
                    """, (
                        timestamp, lat, lon, f"./static/pothole_images/{img_name}"
                    ))
                    conn.commit()
                    conn.close()
                    print(f"[✅] Salvat în DB: {img_name} @ ({lat}, {lon})")

                    # actualizează ultima salvare
                    last_saved = {"timestamp": now, "lat": lat, "lon": lon}

                except Exception as db_err:
                    print(f"[❌] Eroare DB: {db_err}")

                break

        annotated = results.ims[0]
        cv2.imshow("YOLOv5 TCP", annotated)

        if cv2.waitKey(1) == 27:
            print("[🚪] ESC apăsat - ieșire")
            break

except Exception as e:
    print(f"[💥] Eroare: {e}")

finally:
    sock.close()
    cv2.destroyAllWindows()
