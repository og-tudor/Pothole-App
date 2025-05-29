# analyze_upload.py
import os
import time
import cv2
import numpy as np
import sqlite3
from ultralytics import YOLO
from math import radians, sin, cos, sqrt, atan2

MODEL = YOLO("../Processing_Data/best.pt")
MODEL.model.names = {
    0: "pothole",
    1: "alligator_crack",
    2: "block_crack",
    3: "longitudinal_crack",
    4: "other_corruption",
    5: "repair",
    6: "transverse_crack"
}

CLASS_THRESHOLDS = {
    0: 0.13,
    1: 0.3,
    3: 0.6,
    6: 0.4
}
DISABLED_CLASSES = {2, 4, 5}

IMAGE_DIR = "static/pothole_images"
DB_PATH = "../Database/potholes.db"
CLASS_TABLE = {
    "pothole": "potholes",
    "alligator_crack": "alligator_cracks",
    "block_crack": "block_cracks",
    "longitudinal_crack": "longitudinal_cracks",
    "transverse_crack": "transverse_cracks",
    "repair": "repairs",
    "other_corruption": "other_corruptions"
}
os.makedirs(IMAGE_DIR, exist_ok=True)

def analyze_and_save(image_path, lat, lon):
    image = cv2.imread(image_path)
    results = MODEL(image, verbose=False)[0]
    detections = results.boxes

    saved = []
    labels_detected = set()

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    new_filename = f"annotated_{timestamp}.jpg"
    final_path = os.path.join(IMAGE_DIR, new_filename)
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

        table = CLASS_TABLE.get(label)
        if not table or label in labels_detected:
            continue

        # Salvează imaginea o singură dată
        if not annotated_saved:
            annotated = results.plot()
            cv2.imwrite(final_path, annotated)
            annotated_saved = True

        cur.execute(f"""
            INSERT INTO {table} (timestamp, lat, lon, image_path)
            VALUES (?, ?, ?, ?)
        """, (timestamp, lat, lon, f"./static/pothole_images/{new_filename}"))

        saved.append({"label": label, "confidence": conf, "path": final_path})
        labels_detected.add(label)

    conn.commit()
    conn.close()

    return saved

