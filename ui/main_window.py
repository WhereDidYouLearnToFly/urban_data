"""Main window — assembles the 3-column layout (Events Feed / Agents / Map)
over a full-width System Log strip, per hg.jpg. Live: subscribes to the
flowgraph's ZMQ PUB sinks (grc/urban_data.grc: zmq_sink_0 on 5556 for
Events, zmq_sink on 5557 for agent_trigger group summaries) and feeds every
panel from that, no placeholder data.
"""
import json

from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QSplitter
from PyQt5.QtCore import Qt

from common.schemas import Event
from ui.events_feed import EventsFeedPanel
from ui.agents_panel import AgentsPanel
from ui.map_view import MapView
from ui.system_log import SystemLogPanel
from ui.zmq_client import PduSubscriber

EVENTS_ADDRESS = "tcp://127.0.0.1:5556"
GROUPS_ADDRESS = "tcp://127.0.0.1:5557"


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Urban Data")
        self.resize(1400, 800)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)

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

        self._start_subscribers()

    def _start_subscribers(self):
        self.event_sub = PduSubscriber(EVENTS_ADDRESS)
        self.event_sub.messageReceived.connect(self._on_event_pdu)
        self.event_sub.messageError.connect(
            lambda msg: self.system_log.append(f"[WARN] Malformed event PDU dropped: {msg}")
        )
        self.event_sub.disconnected.connect(
            lambda msg: self.system_log.append(f"[WARN] Event stream disconnected: {msg}")
        )

        self.group_sub = PduSubscriber(GROUPS_ADDRESS)
        self.group_sub.messageReceived.connect(self._on_group_pdu)
        self.group_sub.messageError.connect(
            lambda msg: self.system_log.append(f"[WARN] Malformed group PDU dropped: {msg}")
        )
        self.group_sub.disconnected.connect(
            lambda msg: self.system_log.append(f"[WARN] Group stream disconnected: {msg}")
        )

        self.event_sub.start()
        self.system_log.append(f"[INFO] Subscribed to event stream — {EVENTS_ADDRESS}")
        self.group_sub.start()
        self.system_log.append(f"[INFO] Subscribed to group stream — {GROUPS_ADDRESS}")

    def _on_event_pdu(self, payload: bytes):
        try:
            event = Event.from_json(payload)
            lat = event.coordinates["lat"]
            lon = event.coordinates["lon"]
        except Exception as exc:
            self.system_log.append(f"[ERROR] Failed to decode event PDU: {exc}")
            return
        self.events_feed.add_event(event.level, event.description)
        self.map_view.add_event(event.id, lat, lon, event.level, event.description)

    def _on_group_pdu(self, payload: bytes):
        try:
            group = json.loads(payload)
            tag_id = group["tag_id"]
            summary = group["summary"]
        except Exception as exc:
            self.system_log.append(f"[ERROR] Failed to decode group PDU: {exc}")
            return
        self.agents_panel.add_incident(tag_id, summary)

    def closeEvent(self, event):
        self.event_sub.stop()
        self.group_sub.stop()
        super().closeEvent(event)
