"""Events Feed panel — left column. Scrolling, color-coded list of incoming
Event PDUs, fed by MainWindow's ZMQ subscriber (ui/zmq_client.py), newest
appended at the bottom with auto-scroll (not prepended at the top -- see
add_event). Rows for events carrying media/data are marked with a media
icon. Single-clicking a row focuses the map on that event (eventClicked);
double-clicking opens it in the shared PopupGroup (eventDoubleClicked) — see
ui/main_window.py.
"""
from datetime import datetime

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem
from PyQt5.QtGui import QColor

from common.severity_colors import color_for_level


def _format_timestamp(timestamp: str) -> str:
    try:
        return datetime.fromisoformat(timestamp).strftime("%H:%M:%S")
    except (TypeError, ValueError):
        return "--:--:--"


class EventsFeedPanel(QWidget):
    eventClicked = pyqtSignal(str)
    eventDoubleClicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(QLabel("<b>Events Feed</b>"))

        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.list_widget)

    def add_event(self, event_id: str, level: int, description: str, timestamp: str = None, has_data: bool = False):
        # plain Unicode glyph, not an emoji -- Qt5 doesn't render color/bitmap
        # emoji fonts reliably (tofu boxes), but a normal vector glyph like
        # this renders fine and picks up the item's severity foreground color.
        marker = "■ " if has_data else ""
        time_prefix = f"[{_format_timestamp(timestamp)}] " if timestamp else ""
        item = QListWidgetItem(f"{time_prefix}{marker}{description}")
        item.setForeground(QColor(color_for_level(level)))
        item.setData(Qt.UserRole, event_id)
        # append + auto-scroll, not insertItem(0, ...) -- inserting at the
        # front shifts every existing row down each time, which gets more
        # expensive exactly when a lot of events land close together (e.g.
        # a drone-swarm burst). Appending is O(1) regardless of list size.
        self.list_widget.addItem(item)
        self.list_widget.scrollToBottom()

    def select_event(self, event_id: str):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.UserRole) == event_id:
                self.list_widget.setCurrentItem(item)
                self.list_widget.scrollToItem(item)
                return

    def _on_item_clicked(self, item: QListWidgetItem):
        event_id = item.data(Qt.UserRole)
        if event_id:
            self.eventClicked.emit(event_id)

    def _on_item_double_clicked(self, item: QListWidgetItem):
        event_id = item.data(Qt.UserRole)
        if event_id:
            self.eventDoubleClicked.emit(event_id)
