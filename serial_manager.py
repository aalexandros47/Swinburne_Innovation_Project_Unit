import json, threading, time
from typing import Callable, Optional, List
import serial, serial.tools.list_ports

class SerialManager:
    def __init__(self):
        self.ser: Optional[serial.Serial] = None
        self.rx_thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self.on_message: Optional[Callable[[dict], None]] = None

    @staticmethod
    def list_ports() -> List[str]:
        return [p.device for p in serial.tools.list_ports.comports()]

    def connect(self, port: str, baud: int = 115200):
        self.close()
        self.ser = serial.Serial(port, baud, timeout=0.1)
        self._stop.clear()
        self.rx_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self.rx_thread.start()

    def close(self):
        self._stop.set()
        if self.rx_thread and self.rx_thread.is_alive():
            self.rx_thread.join(timeout=1.0)
        if self.ser:
            try: self.ser.close()
            except Exception: pass
        self.ser = None; self.rx_thread = None

    def _reader_loop(self):
        buf = b""
        while not self._stop.is_set() and self.ser and self.ser.is_open:
            try:
                chunk = self.ser.read(256)
                if chunk:
                    buf += chunk
                    while b"\n" in buf:
                        line, buf = buf.split(b"\n", 1)
                        s = line.strip().decode(errors="ignore")
                        if not s: continue
                        try:
                            msg = json.loads(s)
                            if self.on_message: self.on_message(msg)
                        except json.JSONDecodeError:
                            pass
                else:
                    time.sleep(0.01)
            except Exception:
                time.sleep(0.1)

    def send(self, obj: dict):
        if not self.ser or not self.ser.is_open: return
        self.ser.write((json.dumps(obj)+"\n").encode())
