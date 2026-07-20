import os, sys

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLabel, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

URBAN_DATA_ROOT = os.path.join(os.path.expanduser("~"), "github", "urban_data")
sys.path.insert(0, URBAN_DATA_ROOT)

from common.severity_colors import color_for_level


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
        self._list.setFont(QFont("DejaVu Sans Mono", 9))
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
        item.setForeground(QColor(color_for_level(level)))
        item.setToolTip(description)

        self._list.addItem(item)
        self._list.scrollToBottom()

    def clear(self):
        self._list.clear()
