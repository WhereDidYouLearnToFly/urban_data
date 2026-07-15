"""Events Feed panel — left column. Scrolling, color-coded list of incoming
Event PDUs.

Preview-only for now: populated with placeholder rows, not wired to any
message port.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem
from PyQt5.QtGui import QColor

from common.severity_colors import color_for_level


class EventsFeedPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(QLabel("<b>Events Feed</b>"))

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        self._add_placeholder_rows()

    def add_event(self, level: int, description: str):
        item = QListWidgetItem(description)
        item.setForeground(QColor(color_for_level(level)))
        self.list_widget.insertItem(0, item)

    def _add_placeholder_rows(self):
        for level, text in [
            (1, "Traffic normal — Hwy 401 westbound"),
            (5, "Ambulance dispatched — Ottawa downtown"),
            (8, "Flood warning — Don River rising"),
            (1, "Nothing to report — Vancouver harbour"),
        ]:
            self.add_event(level, text)
