import serial
import pynmea2
import threading
import time
import cv2
import socket
import struct
from mpu6050.mpu6050 import mpu6050
from collections import deque

SENSOR_PORT = 9000
SENSOR_DELAY = 0.5

# === GLOBAL GPS ===
last_lat, last_lon = None, None
has_fix = False

# === Citire GPS din modul ===
def read_gps():
    global last_lat, last_lon, has_fix

    try:
        gps_serial = serial.Serial("/dev/ttyAMA0", baudrate=9600, timeout=1)
        print("[🛰️] Port GPS deschis.")
    except Exception as e:
        print(f"[❌] Nu s-a putut deschide portul GPS: {e}")
        return

    print("[📡] Aștept coordonate GPS...")

    while True:
        try:
            line = gps_serial.readline().decode("ascii", errors="replace").strip()
            if not line:
                continue

            if line.startswith("$GPGGA"):
                try:
                    msg = pynmea2.parse(line)
                    if isinstance(msg, pynmea2.types.talker.GGA) and msg.gps_qual > 0:
                        last_lat = msg.latitude
                        last_lon = msg.longitude
                        has_fix = True
                        fix_type = f"{'2D' if msg.gps_qual == 1 else '3D'} Fix"
                        print(f"\n[✅] GPS FIX ({fix_type})")
                        print(f"🌍 Lat: {last_lat:.6f}, Lon: {last_lon:.6f}")
                        print(f"🎯 Acuratețe (HDOP): {msg.horizontal_dil}")
                    else:
                        has_fix = False
                except pynmea2.ParseError:
                    continue

            elif line.startswith("$GPRMC") and has_fix:
                try:
                    msg = pynmea2.parse(line)
                    if msg.status == "A":
                        speed_kmh = float(msg.spd_over_grnd) * 1.852
                        print(f"🚗 Viteză: {speed_kmh:.2f} km/h")
                except pynmea2.ParseError:
                    continue

        except Exception as e:
            print(f"[⚠️] Eroare GPS: {e}")
            time.sleep(1)

# === Inițializează senzor MPU6050 ===
sensor = mpu6050(0x68)
print("[📡] Senzor MPU6050 inițializat pentru denivelări...")

Z_BASELINE = 9.81
THRESHOLD_JUMP = 1
THRESHOLD_DEVIATION = 0.5
XY_TOLERANCE = 1.2
WINDOW_SIZE = 10

z_history = deque(maxlen=WINDOW_SIZE)
last_z = None

# === Stream senzor + GPS ===
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
                conn.sendall(data.encode())
                time.sleep(SENSOR_DELAY)

        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            print("[⚠️] Client senzor deconectat. Aștept o nouă conexiune...\n")
            continue
        except Exception as e:
            print(f"[‼️] Eroare senzor: {e}")
            break
        finally:
            try:
                conn.close()
            except:
                pass

    sensor_socket.close()

# === Stream video de la telefon ===
def video_stream():
    cap = None
    VIDEO_SOURCES = [
        'http://192.168.1.139:8080/video',
        'http://192.168.4.10:8080/video'
    ]

    while cap is None or not cap.isOpened():
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

    while True:
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

        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            print("[⚠️] Client video deconectat. Aștept o nouă conexiune...\n")
            continue
        except Exception as e:
            print(f"[‼️] Eroare video: {e}")
            break
        finally:
            try:
                conn.close()
            except:
                pass

    server_socket.close()
    cap.release()

# === Rulează toate thread-urile simultan ===
if __name__ == "__main__":
    threading.Thread(target=read_gps, daemon=True).start()
    threading.Thread(target=video_stream, daemon=True).start()
    threading.Thread(target=sensor_stream, daemon=True).start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[🛑] Server oprit manual.")
