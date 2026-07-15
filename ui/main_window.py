"""Main window — assembles the 3-column layout (Events Feed / Agents / Map)
over a full-width System Log strip, per hg.jpg. Preview-only: no backend
wiring yet, no GNU Radio, no ZMQ.
"""
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QSplitter
from PyQt5.QtCore import Qt

from ui.events_feed import EventsFeedPanel
from ui.agents_panel import AgentsPanel
from ui.map_view import MapView
from ui.system_log import SystemLogPanel


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Urban Data — UI Preview")
        self.resize(1400, 800)

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(4, 4, 4, 4)
        root_layout.setSpacing(4)

        self.events_feed = EventsFeedPanel()
        self.agents_panel = AgentsPanel()
        self.map_view = MapView()

        top_splitter = QSplitter(Qt.Horizontal)
        top_splitter.addWidget(self.events_feed)
        top_splitter.addWidget(self.agents_panel)
        top_splitter.addWidget(self.map_view)
        top_splitter.setSizes([300, 400, 500])

        self.system_log = SystemLogPanel()

        main_splitter = QSplitter(Qt.Vertical)
        main_splitter.addWidget(top_splitter)
        main_splitter.addWidget(self.system_log)
        main_splitter.setSizes([600, 200])

        root_layout.addWidget(main_splitter)
