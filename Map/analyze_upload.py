# analyze_upload.py
import os
import time
import cv2
import numpy as np
import sqlite3
from ultralytics import YOLO
from math import radians, sin, cos, sqrt, atan2

MODEL = YOLO("../Processing_Data/best_5_labels.pt")
MODEL.model.names = {
    0: "pothole",
    1: "alligator_crack",
    2: "longitudinal_crack",
    3: "transverse_crack",
    4: "manhole"
}

CLASS_THRESHOLDS = {
    0: 0.6,
    1: 0.55,
    2: 0.6,
    3: 0.35,
    4: 0.6
}
DISABLED_CLASSES = {}

IMAGE_DIR = "static/pothole_images"
DB_PATH = "../Database/potholes.db"
CLASS_TABLE = {
    "pothole": "potholes",
    "alligator_crack": "alligator_cracks",
    "longitudinal_crack": "longitudinal_cracks",
    "transverse_crack": "transverse_cracks",
    "manhole": "manholes"
}
os.makedirs(IMAGE_DIR, exist_ok=True)

def analyze_and_save(image_np, lat, lon, problem_type, description, address):
    if image_np is None or image_np.size == 0:
        print("[EROARE] Imaginea nu a putut fi procesată.")
        return []
    results = MODEL(image_np, verbose=False)[0]
    detections = results.boxes

    saved = []
    labels_detected = set()

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    new_filename = f"annotated_{timestamp}.jpg"
    final_path = os.path.join(IMAGE_DIR, new_filename)
    yolo_img_path = f"./static/pothole_images/{new_filename}"
    annotated_saved = False

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for box in detections:
        conf = float(box.conf[0])
        cls = int(box.cls[0])
        label = MODEL.names.get(cls, f"cls_{cls}").lower().replace(" ", "_")

        if cls in DISABLED_CLASSES:
            continue

        threshold = CLASS_THRESHOLDS.get(cls, 0.2)
        if conf < threshold:
            continue

        # Dacă este doar manhole, nu considerăm o detecție validă
        if label == "manhole":
            continue

        table = CLASS_TABLE.get(label)
        if not table or label in labels_detected:
            continue

        # Salvează imaginea o singură dată
        if not annotated_saved:
            annotated = results.plot()
            cv2.imwrite(final_path, annotated)
            annotated_saved = True

        cur.execute(f"""
            INSERT INTO {table} (timestamp, lat, lon, image_path, conf)
            VALUES (?, ?, ?, ?, ?)
        """, (timestamp, lat, lon, yolo_img_path, conf))

        saved.append({"label": label, "confidence": conf, "path": final_path})
        labels_detected.add(label)


    # Salvează imaginea originală dacă nu s-a detectat nimic
    if not saved:
        cv2.imwrite(final_path, image_np)  # fără adnotări

    # Salvează raportul o singură dată, cu mențiune dacă nu sunt detecții
    cur.execute("""
        INSERT INTO reports (timestamp, problem_type, image_path, description, lat, lon, address)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        timestamp,
        problem_type,
        yolo_img_path,
        description + (" (Nicio detecție găsită)" if not saved else ""),
        lat,
        lon,
        address
    ))

    conn.commit()
    conn.close()

    return saved

