import cv2, threading, time
from typing import Optional, Callable

class VideoManager:
    def __init__(self, cam_index: int = 0):
        self.cam_index = cam_index
        self.cap: Optional[cv2.VideoCapture] = None
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.on_frame: Optional[Callable[[any], None]] = None
        self._writer: Optional[cv2.VideoWriter] = None

    def start(self):
        self.stop()
        self.cap = cv2.VideoCapture(self.cam_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread and self._thread.is_alive(): self._thread.join(timeout=1.0)
        if self._writer: self._writer.release(); self._writer = None
        if self.cap: self.cap.release()
        self.cap = None; self._thread = None

    def _loop(self):
        while not self._stop.is_set() and self.cap and self.cap.isOpened():
            ok, frame = self.cap.read()
            if not ok: time.sleep(0.01); continue
            if self.on_frame: self.on_frame(frame)

    def start_recording(self, path: str, fps: int = 24):
        if not self.cap: return
        w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self._writer = cv2.VideoWriter(path, fourcc, fps, (w, h))

    def write_frame(self, frame):
        if self._writer: self._writer.write(frame)

    def stop_recording(self):
        if self._writer: self._writer.release(); self._writer=None
