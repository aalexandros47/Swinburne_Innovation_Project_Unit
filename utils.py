import os, json, zipfile
from datetime import datetime
import cv2
from PyQt6.QtGui import QImage, QPixmap

def now_stamp(): return datetime.now().strftime("%Y%m%d_%H%M%S")
def ensure_dir(path): os.makedirs(path, exist_ok=True)
def save_metadata_json(path: str, data: dict):
    with open(path, "w", encoding="utf-8") as f: json.dump(data, f, indent=2)
def zip_folder(folder_path: str, zip_path: str):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(folder_path):
            for fn in files:
                full = os.path.join(root, fn); rel = os.path.relpath(full, folder_path); z.write(full, rel)
def bgr_to_qpixmap(frame_bgr) -> QPixmap:
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    qimg = QImage(rgb.data, w, h, ch*w, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(qimg)
