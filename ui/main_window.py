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
from ui.agent_manager import AgentManager
from ui.events_feed import EventsFeedPanel
from ui.agents_panel import AgentsPanel
from ui.map_view import MapView
from ui.media_popup import MediaPopup
from ui.system_log import SystemLogPanel
from ui.zmq_client import PduSubscriber

EVENTS_ADDRESS = "tcp://127.0.0.1:5556"
GROUPS_ADDRESS = "tcp://127.0.0.1:5557"

# Experiment flag: when False, AgentManager (opencode serve subprocess +
# QNetworkAccessManager traffic) is never started at all. The Agents panel
# still shows incident summaries from agent_trigger PDUs, just without live
# chat. Was off while isolating the recurring segfault to this subsystem
# (confirmed -- see project memory); AgentManager has since been reworked
# to use one shared opencode session with strictly serial dispatch instead
# of one session per incident fired concurrently, but that hardening was
# never actually tested live. Turning back on now to test it for real.
ENABLE_AGENTS = True


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Urban Data")
        self.resize(1400, 800)
        #self.setWindowFlag(Qt.WindowStaysOnTopHint, True)

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(4, 4, 4, 4)
        root_layout.setSpacing(4)

        self.events_feed = EventsFeedPanel()
        self.agents_panel = AgentsPanel()
        self.map_view = MapView()

        self._events_by_id: dict[str, Event] = {}
        self._open_popups: dict[str, MediaPopup] = {}
        # feed: single click focuses the map, double click opens media.
        # map marker: single click both selects the feed row AND opens
        # media directly if the event has any -- no separate double-click
        # step needed there, and no native Leaflet popup hint either (see
        # map_view.py's addOrUpdateMarker, bindPopup was removed).
        self.events_feed.eventClicked.connect(self.map_view.focus_event)
        self.events_feed.eventDoubleClicked.connect(self._open_media_popup)
        self.map_view.eventClicked.connect(self._on_map_marker_clicked)
        self.map_view.eventDoubleClicked.connect(self._open_media_popup)

        self.agent_manager = None
        if ENABLE_AGENTS:
            self.agent_manager = AgentManager(self)
            self.agent_manager.incident_reply.connect(self._on_agent_reply)
            self.agent_manager.incident_error.connect(
                lambda tag_id, msg: self.system_log.append(f"[WARN] Agent[{tag_id}]: {msg}")
            )
            self.agents_panel.messageSent.connect(self._on_chat_message_sent)

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
        self._events_by_id[event.id] = event
        self.events_feed.add_event(
            event.id, event.level, event.description,
            timestamp=event.timestamp, has_data=bool(event.data),
        )
        self.map_view.add_event(
            event.id, lat, lon, event.level,
            heading_deg=event.heading_deg, speed_kmh=event.speed_kmh,
            track_id=event.predicted_track_id,
            target_lat=event.target_lat, target_lon=event.target_lon,
        )

    def _on_map_marker_clicked(self, event_id: str):
        self.events_feed.select_event(event_id)
        self._open_media_popup(event_id)

    def _open_media_popup(self, event_id: str):
        existing = self._open_popups.get(event_id)
        if existing is not None:
            existing.raise_()
            existing.activateWindow()
            return

        event = self._events_by_id.get(event_id)
        if event is None or not event.data:
            return

        # focus_event() centers the marker in the map widget -- open the
        # popup near that center (offset a bit so it doesn't sit directly on
        # top of the marker) instead of the default cascading spawn spot.
        self.map_view.focus_event(event_id)

        popup = MediaPopup(event, parent=self)
        map_center = self.map_view.mapToGlobal(self.map_view.rect().center())
        popup.move(map_center.x() - popup.width() // 2 + 60, map_center.y() - popup.height() // 2 - 40)

        popup.destroyed.connect(lambda: self._open_popups.pop(event_id, None))
        self._open_popups[event_id] = popup
        popup.show()

    def _on_group_pdu(self, payload: bytes):
        try:
            group = json.loads(payload)
            tag_id = group["tag_id"]
            summary = group["summary"]
            main_event = group.get("main_event", summary)
        except Exception as exc:
            self.system_log.append(f"[ERROR] Failed to decode group PDU: {exc}")
            return
        # main_event (a single event's description) makes a far shorter,
        # more readable panel title than summary (every contributing
        # event's description joined together) -- summary still goes to
        # the agent's own briefing context, where the extra detail helps.
        self.agents_panel.add_incident(tag_id, main_event)
        if self.agent_manager is not None:
            self.agent_manager.create_incident(tag_id, summary, main_event)

    def _on_chat_message_sent(self, tag_id: str, text: str):
        if self.agent_manager is not None:
            self.agent_manager.send_message(tag_id, text)

    def _on_agent_reply(self, tag_id: str, text: str, is_decision: bool):
        self.agents_panel.append_message(tag_id, "agent", text, is_decision=is_decision)
        if is_decision:
            label = self.agents_panel.label_for(tag_id)
            self.system_log.append(f"[{label}] pre-resolved by Agent")

    def keyPressEvent(self, event):
        # showFullScreen() has no window chrome to click back out of --
        # Escape/F11 toggle back to a normal window.
        if event.key() in (Qt.Key_Escape, Qt.Key_F11):
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        self.event_sub.stop()
        self.group_sub.stop()
        if self.agent_manager is not None:
            self.agent_manager.shutdown()
        super().closeEvent(event)
