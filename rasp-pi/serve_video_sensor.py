import cv2
import socket
import struct
import time
import os
import subprocess
import threading
import random

# === CONFIG ===
VIDEO_PORT = 8000
SENSOR_PORT = 9000
VIDEO_SOURCES = [
    'http://192.168.1.139:8080/video',  # ← IP inițial
    'http://192.168.4.10:8080/video'    # ← IP alternativ
]

FPS = 100  # milisecunde între cadre
SENSOR_DELAY = 0.5  # secunde între date senzor

# === Eliberează port video dacă e blocat ===
def elibereaza_port(port=VIDEO_PORT):
    try:
        subprocess.run(f"fuser -k {port}/tcp", shell=True, stderr=subprocess.DEVNULL)
        print(f"[⚙️] Portul {port} a fost eliberat.")
    except Exception:
        pass

elibereaza_port()

# === Thread: Trimite flux video pe portul 8000 ===
def video_stream():
    cap = None
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
    server_socket.bind(('0.0.0.0', VIDEO_PORT))
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

# === Thread: Trimite date senzor + GPS pe portul 9000 ===
# === Thread: Trimite date senzor + GPS pe portul 9000 ===
def sensor_stream():
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
                acc_z = round(random.uniform(9.5, 10.5), 2)
                threshold = 0.3
                deviation = round(abs(acc_z - 9.81), 2)
                denivelare = deviation if deviation > threshold else 0.0

                # Coordonate aleatoare în zona dată
                lat = round(random.uniform(44.393, 44.484), 6)
                lon = round(random.uniform(26.031, 26.168), 6)

                data = f"{denivelare},{lat},{lon}\n"
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


# === Rulează ambele streamuri simultan ===
if __name__ == "__main__":
    threading.Thread(target=video_stream, daemon=True).start()
    threading.Thread(target=sensor_stream, daemon=True).start()

    # Ține scriptul deschis
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[🛑] Server oprit manual.")
