"""Events Feed panel — left column. Scrolling, color-coded list of incoming
Event PDUs, fed by MainWindow's ZMQ subscriber (ui/zmq_client.py).
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

    def add_event(self, level: int, description: str):
        item = QListWidgetItem(description)
        item.setForeground(QColor(color_for_level(level)))
        self.list_widget.insertItem(0, item)
