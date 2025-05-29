import cv2
import socket
import struct
import numpy as np
import os
import time
import json
import threading
import warnings
import math
import sqlite3
from ultralytics import YOLO  # 🔄 import nou pentru YOLOv8/11

BUMP_THRESHOLD = 0.45
POTHOLE_THRESHOLD = 0.2

warnings.filterwarnings("ignore", category=FutureWarning)

FLASK_IMAGE_DIR = "../Map/static/pothole_images"
FLASK_DB_PATH = "../Database/potholes.db"

os.makedirs(FLASK_IMAGE_DIR, exist_ok=True)
SAVE_DIR = "./test_results"
os.makedirs(SAVE_DIR, exist_ok=True)

# 🧬 YOLOv8/v11
model = YOLO("best.pt")  # 🔄 folosește YOLOv8 sau v11
model.conf = POTHOLE_THRESHOLD

model.model.names = {
    0: "pothole",
    1: "alligator_crack",
    2: "block_crack",
    3: "longitudinal_crack",
    4: "other_corruption",
    5: "repair",
    6: "transverse_crack"
}

class_thresholds = {
    0: 0.13,   # pothole
    1: 0.3,   # alligator crack
    3: 0.6,   # longitudinal crack
    6: 0.4    # transverse crack
}
disabled_classes = {2, 4, 5}  # Excludem 'other corruption' și 'repair'


print("Clase în model:")
for i, name in enumerate(model.names):
    print(f"{i}: {name}")


last_saved = {}

last_gps = {"lat": None, "lon": None}

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c * 1000

payload_size = struct.calcsize("Q")
data = b""

PI_IPS = ['192.168.1.138', '192.168.4.1', '192.168.5.1']

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

def listen_sensor_data():
    global last_gps
    last_valid = {"lat": None, "lon": None}
    fallback_coords = {"lat": 44.444, "lon": 26.000}
    last_bump_time = 0

    while True:
        try:
            sensor_sock = try_connect(PI_IPS, 9000, "senzor (real)")

            while True:
                raw = sensor_sock.recv(1024).decode().strip()
                if not raw:
                    continue

                try:
                    denivelare, acc_z, lat, lon = map(float, raw.split(","))
                    print(f"[🛣️] Denivelare: {denivelare:.2f} | Z: {acc_z:.2f} | GPS: {lat}, {lon}")
                    if lat != 0.0 and lon != 0.0:
                        last_valid["lat"] = lat
                        last_valid["lon"] = lon

                    last_gps["lat"] = last_valid["lat"] or fallback_coords["lat"]
                    last_gps["lon"] = last_valid["lon"] or fallback_coords["lon"]

                    now = time.time()
                    if denivelare >= BUMP_THRESHOLD and (now - last_bump_time > 0.5):
                        last_bump_time = now
                        timestamp = time.strftime("%Y%m%d-%H%M%S")
                        conn = sqlite3.connect(FLASK_DB_PATH)
                        cur = conn.cursor()
                        cur.execute("""
                            INSERT INTO bumps (timestamp, lat, lon, bump_severity)
                            VALUES (?, ?, ?, ?)
                        """, (
                            timestamp,
                            last_gps["lat"],
                            last_gps["lon"],
                            denivelare
                        ))
                        conn.commit()
                        conn.close()
                        print(f"[📥] Denivelare salvată în DB @ ({last_gps['lat']}, {last_gps['lon']})")

                except ValueError:
                    print(f"[⚠️] Date senzor invalide: {raw}")
                    continue

        except Exception as e:
            print(f"[‼️] Eroare flux senzor: {e}. Reîncerc în 3 secunde...")
            time.sleep(3)
            continue
        finally:
            try:
                sensor_sock.close()
            except:
                pass

def receive_video():
    global data
    class_to_table = {
        "pothole": "potholes",
        "alligator_crack": "alligator_cracks",
        "block_crack": "block_cracks",
        "longitudinal_crack": "longitudinal_cracks",
        "transverse_crack": "transverse_cracks",
        "repair": "repairs",
        "other_corruption": "other_corruptions"
    }

    while True:
        try:
            sock = try_connect(PI_IPS, 8000, "video")
            data = b""
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
                if frame is None:
                    print("[❌] Frame corupt — skip")
                    continue

                results = model(frame, verbose=False)[0]
                # print(f"[🔍] Detectări YOLOv8: {len(results.boxes)}")


                found_valid = False
                for i, box in enumerate(results.boxes):
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    label = model.names.get(cls, f"cls_{cls}").lower().replace(" ", "_")
                    print(f"[📦] box[{i}] → cls: {cls} ({label}), conf: {conf:.2f}")
                    
                    if cls in disabled_classes:
                        continue
                    # Verificare threshold per clasa
                    threshold = class_thresholds.get(cls, POTHOLE_THRESHOLD)
                    if conf < threshold:
                        # print(f"[⬇️] Confidență sub prag pentru {label}: {conf:.2f} < {threshold:.2f}")
                        continue
                    # if conf < POTHOLE_THRESHOLD:
                    #     continue

                    if label not in class_to_table:
                        print(f"[ℹ️] Etichetă necunoscută: {label}")
                        continue

                    print(f"[📌] Detectat: {label} @ {conf:.2f}")

                    if last_gps["lat"] is None or last_gps["lon"] is None:
                        last_gps["lat"] = 44.453944
                        last_gps["lon"] = 26.028722
                        print("[ℹ️] GPS lipsă — fallback")

                    lat, lon = float(last_gps["lat"]), float(last_gps["lon"])
                    now = time.time()
                    last_info = last_saved.get(label, {"timestamp": None, "lat": None, "lon": None})
                    recent = last_info["timestamp"] and now - last_info["timestamp"] < 1
                    too_close = (
                        last_info["lat"] is not None
                        and haversine(lat, lon, last_info["lat"], last_info["lon"]) < 3
                    )

                    if recent or too_close:
                        reason = []
                        if recent:
                            reason.append("timp")
                        if too_close:
                            reason.append("distanță")
                        print(f"[⛔] Dublură {label} — ignorat ({' și '.join(reason)})")
                        continue

                    timestamp = time.strftime("%Y%m%d-%H%M%S")
                    img_name = f"{label}_{timestamp}.jpg"
                    flask_img_path = os.path.join(FLASK_IMAGE_DIR, img_name)
                    raw_img_path = os.path.join(SAVE_DIR, f"raw_{img_name}")

                    cv2.imwrite(raw_img_path, frame.copy())
                    annotated = results.plot()
                    cv2.imwrite(flask_img_path, annotated)

                    try:
                        conn = sqlite3.connect(FLASK_DB_PATH)
                        cur = conn.cursor()
                        cur.execute(f"""
                            INSERT INTO {class_to_table[label]} (timestamp, lat, lon, image_path)
                            VALUES (?, ?, ?, ?)
                        """, (
                            timestamp, lat, lon, f"./static/pothole_images/{img_name}"
                        ))
                        conn.commit()
                        conn.close()
                        print(f"[✅] {label} salvat în DB @ ({lat}, {lon})")

                        last_saved[label] = {"timestamp": now, "lat": lat, "lon": lon}
                        found_valid = True
                    except Exception as db_err:
                        print(f"[❌] Eroare DB: {db_err}")


                if not found_valid:
                    annotated = results.plot()
                if os.name == 'nt' or os.environ.get('DISPLAY'):
                    cv2.imshow("YOLOv8 TCP", annotated)
                    if cv2.waitKey(1) == 27:
                        print("[🚪] ESC apăsat - ieșire")
                        return

        except Exception as e:
            print(f"[🔁] Eroare flux video: {e}. Reîncerc în 3 secunde...")
            time.sleep(3)
        finally:
            try:
                sock.close()
            except:
                pass
            cv2.destroyAllWindows()


# === Start threads ===
threading.Thread(target=listen_sensor_data, daemon=True).start()
receive_video()
