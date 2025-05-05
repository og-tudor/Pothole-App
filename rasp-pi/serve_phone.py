import serial
import pynmea2
import threading
import time
import cv2
import socket
import struct
import random
from mpu6050.mpu6050 import mpu6050
from collections import deque

SENSOR_PORT = 9000
SENSOR_DELAY = 0.5


# Setări detecție denivelare
Z_BASELINE = 9.81
THRESHOLD_JUMP = 1
THRESHOLD_DEVIATION = 0.5
XY_TOLERANCE = 1.2
WINDOW_SIZE = 10

z_history = deque(maxlen=WINDOW_SIZE)
last_z = None


# === GLOBAL GPS ===
last_lat, last_lon = None, None
has_fix = False

import json

def read_gps():
    global last_lat, last_lon, has_fix

    while True:
        try:
            gps_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            gps_socket.connect(("192.168.4.10", 9005))
            print("[📡] Conectat la GPS-ul telefonului (192.168.4.10:9005)")
        except Exception as e:
            print(f"[❌] Eroare la conectarea la GPS socket: {e}. Reîncerc peste 5 secunde...")
            time.sleep(5)
            continue

        try:
            while True:
                data = gps_socket.recv(1024)
                if not data:
                    print("[⚠️] GPS socket închis de telefon. Reîncerc...")
                    break  # ⇽ iese din buclă și reîncearcă

                lines = data.decode(errors="ignore").splitlines()
                for line in lines:
                    try:
                        gps_data = json.loads(line)

                        if not isinstance(gps_data, dict):
                            continue

                        lat = gps_data.get("latitude")
                        lon = gps_data.get("longitude")
                        used_sat = gps_data.get("gnss_satellites_used_in_fix", 0)

                        if lat and lon and used_sat > 0:
                            last_lat = lat
                            last_lon = lon
                            has_fix = True
                            print(f"\n[✅] GPS FIX din telefon 🛰️")
                            print(f"🌍 Lat: {lat:.6f}, Lon: {lon:.6f}, Sateliți utilizați: {used_sat}")
                        else:
                            has_fix = False
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"[⚠️] Eroare citire GPS socket: {e}. Se va reconecta...")
            time.sleep(3)
        finally:
            try:
                gps_socket.close()
                print("[🔁] Se închide socketul și se încearcă reconectarea la GPS...\n")
            except:
                pass


# Inițializează senzorul
sensor = mpu6050(0x68)
print("[📡] Senzor MPU6050 inițializat pentru denivelări...")



def sensor_stream():
    global last_lat, last_lon, has_fix, last_z

    sensor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sensor_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sensor_socket.bind(('0.0.0.0', SENSOR_PORT))
    sensor_socket.listen(1)
    print("[📡] Server senzor activ, așteaptă clienți...")

    while True:
        try:
            conn, addr = sensor_socket.accept()
            print(f"[✅] Client conectat pentru senzor de la {addr}")

            while True:
                accel = sensor.get_accel_data()
                x, y, z = accel['x'], accel['y'], accel['z']
                z_history.append(z)

                z_avg = sum(z_history) / len(z_history)
                deviation = abs(z - z_avg)
                delta_z = abs(z - last_z) if last_z is not None else 0
                last_z = z

                # Ignoră frânări, curbe
                if abs(x) > XY_TOLERANCE or abs(y) > XY_TOLERANCE:
                    denivelare = 0.0
                else:
                    if deviation > THRESHOLD_DEVIATION and delta_z > THRESHOLD_JUMP:
                        denivelare = round(deviation, 2)
                    else:
                        denivelare = 0.0

                lat = last_lat if has_fix else 0.0
                lon = last_lon if has_fix else 0.0

                data = f"{denivelare},{z:.2f},{lat},{lon}\n"
                try:
                    conn.sendall(data.encode())
                except Exception as e:
                    print(f"[‼️] Eroare la trimiterea datelor senzor: {e}")
                    break  # forțează reconectarea

                time.sleep(SENSOR_DELAY)

        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            print("[⚠️] Client senzor deconectat. Aștept o nouă conexiune...\n")
            continue
        except Exception as e:
            print(f"[‼️] Eroare senzor: {e}")
            continue
        finally:
            try:
                conn.close()
            except:
                pass

    sensor_socket.close()

def video_stream():
    while True:
        # Redeschide sursa video
        cap = None
        while cap is None or not cap.isOpened():
            VIDEO_SOURCES = [
                'http://192.168.1.139:8080/video',
                'http://192.168.4.10:8080/video'
            ]
            for source in VIDEO_SOURCES:
                print(f"[🔎] Încerc să deschid sursa video: {source}")
                cap = cv2.VideoCapture(source)
                time.sleep(1)
                if cap.isOpened():
                    print(f"[🎥] Conectat la sursa video: {source}")
                    break
            if cap is None or not cap.isOpened():
                print("[❌] Nu s-a putut deschide nicio sursă video. Reîncerc peste 5 secunde...")
                time.sleep(5)

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
        server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        server_socket.bind(('0.0.0.0', 8000))
        server_socket.listen(1)
        print("[📷] Server video activ, așteaptă clienți...")

        try:
            conn, addr = server_socket.accept()
            print(f"[✅] Client conectat pentru video de la {addr}")
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("[⚠️] Nu pot citi cadrul video.")
                    break

                frame = cv2.resize(frame, (960, 540))
                _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                data = buffer.tobytes()
                message = struct.pack("Q", len(data)) + data
                conn.sendall(message)

        except Exception as e:
            print(f"[‼️] Eroare video: {e}")
        finally:
            try:
                conn.close()
            except:
                pass
            try:
                server_socket.close()
            except:
                pass
            try:
                cap.release()
            except:
                pass
            print("[🔄] Reset server video. Reîncercare în 3 secunde...")
            time.sleep(3)


# === Rulează totul simultan ===
if __name__ == "__main__":
    threading.Thread(target=read_gps, daemon=True).start()
    threading.Thread(target=video_stream, daemon=True).start()
    threading.Thread(target=sensor_stream, daemon=True).start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[🛑] Server oprit manual.")
