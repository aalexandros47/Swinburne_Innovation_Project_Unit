import os, time
from PyQt6.QtWidgets import (QWidget, QLabel, QPushButton, QComboBox, QHBoxLayout, QVBoxLayout,
                             QSlider, QFileDialog, QGroupBox, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap
from serial_manager import SerialManager
from video_manager import VideoManager
from utils import bgr_to_qpixmap, now_stamp, save_metadata_json, zip_folder

class MainUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("P.R.O.B.E PC — Companion")
        self.resize(1200, 720)

        self.serial = SerialManager()
        self.serial.on_message = self._on_serial_message
        self.video = VideoManager(cam_index=0)

        self.current_frame = None
        self.case_dir = None
        self.recording = False

        # top bar
        self.port_combo = QComboBox()
        self.refresh_btn = QPushButton("Refresh Ports")
        self.connect_btn = QPushButton("Connect")
        self.status_lbl = QLabel("Status: Disconnected"); self.status_lbl.setStyleSheet("color:#aaa")
        top = QHBoxLayout()
        top.addWidget(QLabel("Port:")); top.addWidget(self.port_combo,1)
        top.addWidget(self.refresh_btn); top.addWidget(self.connect_btn); top.addWidget(self.status_lbl)

        # video
        self.video_lbl = QLabel("Video Preview"); self.video_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_lbl.setStyleSheet("background:#000; border:1px solid #333;"); self.video_lbl.setMinimumHeight(420)

        # ----- axis controls (NEW) -----
        self.axis_combo = QComboBox(); self.axis_combo.addItems(["SWAB","OSC","ROT","PITCH"])
        self.dir_combo  = QComboBox();  self.dir_combo.addItems(["Dir 0","Dir 1"])
        self.speed_slider = QSlider(Qt.Orientation.Horizontal); self.speed_slider.setRange(200, 5000); self.speed_slider.setValue(800)
        self.count_slider = QSlider(Qt.Orientation.Horizontal); self.count_slider.setRange(1, 2000); self.count_slider.setValue(200)
        self.axis_on_btn = QPushButton("Axis ON")
        self.axis_off_btn = QPushButton("Axis OFF")
        self.jog_btn = QPushButton("Start JOG")
        self.stop_axis_btn = QPushButton("STOP Axis")
        self.step_btn = QPushButton("STEP Count")

        # capture bar
        self.capture_btn = QPushButton("Capture Still")
        self.record_btn  = QPushButton("Start Recording")
        self.open_case_btn = QPushButton("Choose Case Folder…")
        self.export_btn = QPushButton("Export Case (.zip)")

        cap = QHBoxLayout()
        cap.addWidget(self.axis_combo)
        cap.addWidget(self.dir_combo)
        cap.addWidget(QLabel("Speed (µs)")); cap.addWidget(self.speed_slider)
        cap.addWidget(QLabel("Count")); cap.addWidget(self.count_slider)
        cap.addWidget(self.axis_on_btn); cap.addWidget(self.axis_off_btn)
        cap.addWidget(self.jog_btn); cap.addWidget(self.stop_axis_btn); cap.addWidget(self.step_btn)
        cap.addStretch(1)
        cap.addWidget(self.capture_btn); cap.addWidget(self.record_btn)
        cap.addWidget(self.open_case_btn); cap.addWidget(self.export_btn)

        # right control box (generic controls kept for later expansion)
        ctrl_box = QGroupBox("Session")
        start_btn = QPushButton("Start Session (All ON)")
        stop_btn  = QPushButton("Stop Session (All OFF)")
        v = QVBoxLayout(); v.addWidget(start_btn); v.addWidget(stop_btn); ctrl_box.setLayout(v)

        # layout
        left = QVBoxLayout()
        left.addLayout(top); left.addWidget(self.video_lbl); left.addLayout(cap)
        root = QHBoxLayout(self); root.addLayout(left,3); root.addWidget(ctrl_box,1)

        # signals
        self.refresh_btn.clicked.connect(self._refresh_ports)
        self.connect_btn.clicked.connect(self._connect_toggle)
        start_btn.clicked.connect(lambda: self._send({"CMD":"HELLO?"}) or self._send({"CMD":"ON","AXIS":"SWAB","VAL":1}) or
                                             self._send({"CMD":"ON","AXIS":"OSC","VAL":1}) or
                                             self._send({"CMD":"ON","AXIS":"ROT","VAL":1}))
        stop_btn.clicked.connect(lambda: self._send({"CMD":"ALL_OFF"}))

        self.axis_on_btn.clicked.connect(lambda: self._axis_onoff(True))
        self.axis_off_btn.clicked.connect(lambda: self._axis_onoff(False))
        self.jog_btn.clicked.connect(self._axis_jog)
        self.stop_axis_btn.clicked.connect(self._axis_stop)
        self.step_btn.clicked.connect(self._axis_step)

        self.capture_btn.clicked.connect(self._capture_still)
        self.record_btn.clicked.connect(self._toggle_record)
        self.open_case_btn.clicked.connect(self._choose_case)
        self.export_btn.clicked.connect(self._export_case)

        # video
        self.video.on_frame = self._on_frame
        self.video.start()
        self.timer = QTimer(self); self.timer.timeout.connect(self._ui_tick); self.timer.start(1000//30)

        self._refresh_ports()

    # -------- serial ----------
    def _refresh_ports(self):
        self.port_combo.clear(); self.port_combo.addItems(self.serial.list_ports())

    def _connect_toggle(self):
        if self.connect_btn.text()=="Connect":
            port = self.port_combo.currentText()
            if not port: QMessageBox.warning(self,"Port","No COM port selected."); return
            try:
                self.serial.connect(port)
                self.connect_btn.setText("Disconnect")
                self.status_lbl.setText(f"Status: Connected to {port}")
                self.status_lbl.setStyleSheet("color:#4caf50")
            except Exception as e:
                QMessageBox.critical(self,"Connect error",str(e))
        else:
            self.serial.close()
            self.connect_btn.setText("Connect")
            self.status_lbl.setText("Status: Disconnected")
            self.status_lbl.setStyleSheet("color:#aaa")

    def _on_serial_message(self, msg: dict):
        # later: parse {"type":"STATUS", ...} and show badges
        pass

    def _send(self, obj: dict): self.serial.send(obj)

    # -------- axis helpers ----------
    def _axis_name(self) -> str: return self.axis_combo.currentText()

    def _axis_onoff(self, on: bool):
        self._send({"CMD":"ON","AXIS": self._axis_name(), "VAL": 1 if on else 0})

    def _axis_jog(self):
        axis = self._axis_name()
        dirv = 1 if self.dir_combo.currentIndex()==1 else 0
        spd = int(self.speed_slider.value())
        self._send({"CMD":"JOG","AXIS":axis,"DIR":dirv,"SPEED":spd})

    def _axis_stop(self):
        self._send({"CMD":"STOP","AXIS": self._axis_name()})

    def _axis_step(self):
        axis = self._axis_name()
        dirv = 1 if self.dir_combo.currentIndex()==1 else 0
        spd = int(self.speed_slider.value())
        cnt = int(self.count_slider.value())
        self._send({"CMD":"STEP","AXIS":axis,"DIR":dirv,"SPEED":spd,"COUNT":cnt})

    # -------- video/capture ----------
    def _on_frame(self, frame_bgr): self.current_frame = frame_bgr

    def _ui_tick(self):
        if self.current_frame is None: return
        pm: QPixmap = bgr_to_qpixmap(self.current_frame)
        self.video_lbl.setPixmap(pm.scaled(self.video_lbl.width(), self.video_lbl.height(),
                                           Qt.AspectRatioMode.KeepAspectRatio,
                                           Qt.TransformationMode.SmoothTransformation))
        if self.recording: self.video.write_frame(self.current_frame)

    def _ensure_case(self):
        if not self.case_dir:
            self.case_dir = os.path.join(os.getcwd(), "case_"+now_stamp())
            os.makedirs(self.case_dir, exist_ok=True)

    def _capture_still(self):
        if self.current_frame is None:
            QMessageBox.information(self,"Capture","No frame yet."); return
        self._ensure_case()
        path = os.path.join(self.case_dir, f"still_{now_stamp()}.png")
        import cv2; cv2.imwrite(path, self.current_frame)
        save_metadata_json(path.replace(".png",".json"), {"type":"photo","timestamp":now_stamp(),"notes":""})
        QMessageBox.information(self,"Capture",f"Saved: {path}")

    def _toggle_record(self):
        if not self.recording:
            self._ensure_case()
            path = os.path.join(self.case_dir, f"clip_{now_stamp()}.mp4")
            self.video.start_recording(path, fps=24)
            self.recording = True; self.record_btn.setText("Stop Recording")
        else:
            self.video.stop_recording()
            self.recording = False; self.record_btn.setText("Start Recording")
            QMessageBox.information(self,"Recording","Clip saved to case folder.")

    def _choose_case(self):
        d = QFileDialog.getExistingDirectory(self,"Choose / Create Case Folder")
        if d: self.case_dir = d

    def _export_case(self):
        if not self.case_dir:
            QMessageBox.information(self,"Export","No case folder yet."); return
        zip_path,_ = QFileDialog.getSaveFileName(self,"Export Case as ZIP",f"{self.case_dir}.zip","Zip Files (*.zip)")
        if zip_path:
            zip_folder(self.case_dir, zip_path)
            QMessageBox.information(self,"Export",f"Exported: {zip_path}")
