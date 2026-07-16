"""Agents panel — middle column. Per-incident agent reasoning/chat view
(Step 6).

Populated today from the agent_trigger group summaries MainWindow receives
over ZMQ (ui/zmq_client.py) — {tag_id, summary, main_event} per
common/ai_events_processor.py. Not yet wired to a live agent_manager or
per-incident chat; that's the rest of Step 6.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem


class AgentsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(QLabel("<b>Agents</b>"))

        self.incident_list = QListWidget()
        layout.addWidget(self.incident_list)

    def add_incident(self, tag_id: str, summary: str):
        item = QListWidgetItem(f"[{tag_id}] {summary}")
        self.incident_list.addItem(item)
