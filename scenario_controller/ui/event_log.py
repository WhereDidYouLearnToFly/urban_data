from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLabel, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont


_LEVEL_COLORS = {
    0:  "#4caf50",
    1:  "#8bc34a",
    2:  "#cddc39",
    3:  "#ffeb3b",
    4:  "#ffc107",
    5:  "#ff9800",
    6:  "#ff5722",
    7:  "#f44336",
    8:  "#e91e63",
    9:  "#9c27b0",
    10: "#b71c1c",
}


class EventLogWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QHBoxLayout()
        header.addWidget(QLabel("Event Log"))
        header.addStretch()
        btn_clear = QPushButton("Clear")
        btn_clear.setMaximumWidth(60)
        btn_clear.clicked.connect(self.clear)
        header.addWidget(btn_clear)
        layout.addLayout(header)

        self._list = QListWidget()
        self._list.setFont(QFont("Monospace", 9))
        self._list.setAlternatingRowColors(True)
        self._list.setWordWrap(True)
        layout.addWidget(self._list)

    def append_event(self, event: dict, elapsed: float):
        result = event.get("predefined_analysis_result", {})
        level = result.get("level", 0)
        event_type = result.get("event_type", "unknown")
        description = result.get("description", "")
        coords = event.get("coordinates", {})
        src_id = event.get("id", "?")

        m, s = divmod(int(elapsed), 60)
        timestamp = f"{m:02d}:{s:02d}"

        text = f"[{timestamp}] {src_id}  {event_type}  — {description[:80]}"
        if len(description) > 80:
            text += "…"

        item = QListWidgetItem(text)
        color = _LEVEL_COLORS.get(min(level, 10), "#ffffff")
        item.setForeground(QColor(color))
        item.setToolTip(description)

        self._list.addItem(item)
        self._list.scrollToBottom()

    def clear(self):
        self._list.clear()
