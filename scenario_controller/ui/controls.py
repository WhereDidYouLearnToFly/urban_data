from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QLabel, QLineEdit, QComboBox, QSlider, QGroupBox,
)
from PyQt5.QtCore import Qt, pyqtSignal


class ControlsWidget(QWidget):
    play_clicked = pyqtSignal()
    pause_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    scenario_changed = pyqtSignal(str)   # emits scenario json path
    speed_changed = pyqtSignal(float)
    zmq_address_changed = pyqtSignal(str)

    _SPEEDS = [0.5, 1.0, 2.0, 5.0, 10.0, 20.0]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        # ── scenario + zmq ──────────────────────────────────────────────────
        top = QGroupBox("Source")
        top_layout = QHBoxLayout(top)

        top_layout.addWidget(QLabel("Scenario:"))
        self._scenario_combo = QComboBox()
        self._scenario_combo.setMinimumWidth(220)
        self._scenario_combo.currentIndexChanged.connect(self._on_scenario_changed)
        top_layout.addWidget(self._scenario_combo)

        top_layout.addSpacing(20)
        top_layout.addWidget(QLabel("ZMQ:"))
        self._zmq_input = QLineEdit("tcp://127.0.0.1:5555")
        self._zmq_input.setMaximumWidth(180)
        self._zmq_input.editingFinished.connect(
            lambda: self.zmq_address_changed.emit(self._zmq_input.text().strip())
        )
        top_layout.addWidget(self._zmq_input)
        top_layout.addStretch()

        root.addWidget(top)

        # ── transport controls ───────────────────────────────────────────────
        bottom = QGroupBox("Playback")
        bottom_layout = QHBoxLayout(bottom)

        self._btn_play = QPushButton("▶  Play")
        self._btn_play.setMinimumWidth(90)
        self._btn_play.clicked.connect(self.play_clicked)

        self._btn_pause = QPushButton("⏸  Pause")
        self._btn_pause.setMinimumWidth(90)
        self._btn_pause.setEnabled(False)
        self._btn_pause.clicked.connect(self.pause_clicked)

        self._btn_stop = QPushButton("⏹  Stop")
        self._btn_stop.setMinimumWidth(90)
        self._btn_stop.setEnabled(False)
        self._btn_stop.clicked.connect(self.stop_clicked)

        bottom_layout.addWidget(self._btn_play)
        bottom_layout.addWidget(self._btn_pause)
        bottom_layout.addWidget(self._btn_stop)
        bottom_layout.addSpacing(20)

        bottom_layout.addWidget(QLabel("Speed:"))
        self._speed_slider = QSlider(Qt.Horizontal)
        self._speed_slider.setMinimum(0)
        self._speed_slider.setMaximum(len(self._SPEEDS) - 1)
        self._speed_slider.setValue(1)
        self._speed_slider.setMaximumWidth(140)
        self._speed_slider.setTickPosition(QSlider.TicksBelow)
        self._speed_slider.setTickInterval(1)
        self._speed_slider.valueChanged.connect(self._on_speed_changed)

        self._speed_label = QLabel("1×")
        self._speed_label.setMinimumWidth(32)

        bottom_layout.addWidget(self._speed_slider)
        bottom_layout.addWidget(self._speed_label)
        bottom_layout.addStretch()

        # status label (set from outside via set_state/set_progress)
        self._status_text = "● IDLE"
        self._status_label = QLabel(self._status_text)
        self._status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        bottom_layout.addWidget(self._status_label)

        root.addWidget(bottom)

    # ── public ──────────────────────────────────────────────────────────────

    def populate_scenarios(self, scenarios: list[dict]):
        self._scenario_combo.blockSignals(True)
        self._scenario_combo.clear()
        for s in scenarios:
            self._scenario_combo.addItem(s["name"], userData=s["path"])
        self._scenario_combo.blockSignals(False)
        if scenarios:
            self._on_scenario_changed(0)

    def set_state(self, state: str):
        playing = state == "playing"
        paused = state == "paused"
        idle = state in ("stopped", "finished")

        self._btn_play.setEnabled(not playing)
        self._btn_pause.setEnabled(playing)
        self._btn_stop.setEnabled(not idle)

        icons = {
            "playing": "▶ PLAYING",
            "paused":  "⏸ PAUSED",
            "stopped": "● IDLE",
            "finished": "✓ DONE",
        }
        self._status_text = icons.get(state, state.upper())
        self._status_label.setText(self._status_text)

    def set_progress(self, elapsed: float, duration: float):
        def fmt(s):
            m, sec = divmod(int(s), 60)
            return f"{m:02d}:{sec:02d}"
        self._status_label.setText(f"{self._status_text}  {fmt(elapsed)} / {fmt(duration)}")

    # ── internal ────────────────────────────────────────────────────────────

    def _on_scenario_changed(self, index: int):
        path = self._scenario_combo.itemData(index)
        if path:
            self.scenario_changed.emit(path)

    def _on_speed_changed(self, index: int):
        speed = self._SPEEDS[index]
        self._speed_label.setText(f"{speed:g}×")
        self.speed_changed.emit(speed)
