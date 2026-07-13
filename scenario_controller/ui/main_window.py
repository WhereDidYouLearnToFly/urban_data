from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QSplitter
from PyQt5.QtCore import Qt
from ui.controls import ControlsWidget
from ui.event_log import EventLogWidget


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Urban Data — Scenario Controller")
        self.resize(820, 560)
        self._build()

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self.controls = ControlsWidget()
        layout.addWidget(self.controls)

        self.event_log = EventLogWidget()
        layout.addWidget(self.event_log, stretch=1)
