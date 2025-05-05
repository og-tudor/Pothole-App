import socket
import time
import random

# Socket pentru date senzor + GPS
sensor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sensor_socket.bind(('0.0.0.0', 9000))
sensor_socket.listen(1)
print("[📡] Aștept client pentru senzor+GPS...")

conn, addr = sensor_socket.accept()
print(f"[✅] Client conectat de la {addr}")

# Coordonate de start și sfârșit
start_lat, start_lon = 44.427602, 26.034011
end_lat, end_lon = 44.428710, 26.054566
steps = 20  # numărul de pași/interpolări între cele 2 puncte

# Generăm punctele intermediare
latitudes = [start_lat + i * (end_lat - start_lat) / steps for i in range(steps + 1)]
longitudes = [start_lon + i * (end_lon - start_lon) / steps for i in range(steps + 1)]

# Pentru ciclu dus-întors
index = 0
direction = 1  # 1 = dus, -1 = întors

try:
    while True:
        # Simulare Z-axis (accelerometru)
        acc_z = round(random.uniform(9.5, 10.5), 2)  # uneori trece de prag

        # Calculează "denivelare" dacă acc_z deviază de la normal (9.81)
        threshold = 0.3
        deviation = round(abs(acc_z - 9.81), 2)
        denivelare = deviation if deviation > threshold else 0.0

        # Ia coordonata GPS actuală
        lat = round(latitudes[index], 6)
        lon = round(longitudes[index], 6)

        # Trimite un singur string: denivelare,lat,lon
        data = f"{denivelare},{lat},{lon}\n"
        conn.sendall(data.encode())

        # Update index pentru GPS
        index += direction
        if index >= len(latitudes):
            index = len(latitudes) - 2
            direction = -1
        elif index < 0:
            index = 1
            direction = 1

        time.sleep(0.5)

except Exception as e:
    print(f"[‼️] Eroare senzor: {e}")
finally:
    conn.close()
    sensor_socket.close()
