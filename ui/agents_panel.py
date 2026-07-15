"""Agents panel — middle column. Per-incident agent reasoning/chat view
(Step 6).

Preview-only: shows a placeholder empty state. Not wired to agent_manager
or the agent_trigger port yet.
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

        self._add_placeholder_incident()

    def add_incident(self, tag_id: str, summary: str):
        item = QListWidgetItem(f"[{tag_id}] {summary}")
        self.incident_list.addItem(item)

    def _add_placeholder_incident(self):
        self.add_incident("—", "No active incidents — waiting for agent_trigger")
