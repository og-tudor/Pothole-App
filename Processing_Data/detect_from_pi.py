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

BUMP_THRESHOLD = 0.45
POTHOLE_THRESHOLD = 0.7

warnings.filterwarnings("ignore", category=FutureWarning)

FLASK_IMAGE_DIR = "../Map/static/pothole_images"
FLASK_DB_PATH = "../Database/potholes.db"

os.makedirs(FLASK_IMAGE_DIR, exist_ok=True)
SAVE_DIR = "./test_results"
os.makedirs(SAVE_DIR, exist_ok=True)

# 🧬 YOLOv5
model = torch.hub.load('ultralytics/yolov5', 'custom', path='best_windows_exp5_win.pt')
model.conf = POTHOLE_THRESHOLD

last_saved = {"timestamp": None, "lat": None, "lon": None}
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

                    # actualizare sau fallback
                    if last_valid["lat"] is not None and last_valid["lon"] is not None:
                        last_gps["lat"] = last_valid["lat"]
                        last_gps["lon"] = last_valid["lon"]
                    else:
                        last_gps["lat"] = fallback_coords["lat"]
                        last_gps["lon"] = fallback_coords["lon"]


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

                results = model(frame)
                labels = results.names
                detected = results.pred[0]

                for *box, conf, cls in detected:
                    if conf < POTHOLE_THRESHOLD:
                        continue

                    label = labels[int(cls)]
                    if "pothole" in label.lower():
                        print(f"[🕳️] Gropă detectată! {conf:.2f}")

                        if last_gps["lat"] is None or last_gps["lon"] is None:
                            last_gps["lat"] = 44.453944
                            last_gps["lon"] = 26.028722
                            print("[ℹ️] Coordonate GPS lipsă — folosit fallback")

                        lat, lon = float(last_gps["lat"]), float(last_gps["lon"])
                        now = time.time()
                        distance = haversine(lat, lon, last_saved["lat"], last_saved["lon"]) if last_saved["lat"] else float("inf")

                        if (last_saved["timestamp"] and now - last_saved["timestamp"] < 1) or (distance < 3):
                            print("[⛔] Dublură detectată — ignorată")
                            break

                        timestamp = time.strftime("%Y%m%d-%H%M%S")
                        img_name = f"groapa_{timestamp}.jpg"
                        flask_img_path = os.path.join(FLASK_IMAGE_DIR, img_name)
                        raw_img_path = os.path.join(SAVE_DIR, f"raw_{img_name}")

                        cv2.imwrite(raw_img_path, frame.copy())
                        results.render()
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
                            last_saved.update({"timestamp": now, "lat": lat, "lon": lon})

                        except Exception as db_err:
                            print(f"[❌] Eroare DB: {db_err}")
                        break

                annotated = results.ims[0]
                if os.name == 'nt' or os.environ.get('DISPLAY'):
                    cv2.imshow("YOLOv5 TCP", annotated)
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
