"""Agents panel — middle column. One consolidated window (bordered
"small window" look), not one box per incident: a static incident list
pinned at the top (updates as agent_trigger group summaries arrive via
MainWindow._on_group_pdu), a single dialogue transcript below it that
grows/auto-scrolls as the conversation goes, and one larger, clearly
clickable input at the bottom -- matching the reality that there's a
single shared agent underneath (ui/agent_manager.py), not a separate one
per incident.

A new incident sits in the top list until the agent's first ("decision")
reply for it comes back -- that reply renders in italics in the dialogue
and the incident is removed from the pending list, so the list only ever
shows incidents the agent hasn't weighed in on yet.
"""
import html

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTextEdit, QFrame, QListWidget, QListWidgetItem,
)

_AGENT_ACCENT = "#ffd11a"
_OPERATOR_ACCENT = "#5a86b8"


class AgentsPanel(QWidget):
    messageSent = pyqtSignal(str, str)  # tag_id (of the latest incident), text

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        header = QLabel("<b>Agents</b>")
        header.setStyleSheet("font-size: 16px;")
        layout.addWidget(header)

        # single bordered "window" holding everything below
        window = QFrame()
        window.setFrameShape(QFrame.StyledPanel)
        window.setStyleSheet(
            "QFrame { border: 1px solid #2a4d6e; border-radius: 4px; background: #16283d; }"
        )
        window_layout = QVBoxLayout(window)
        window_layout.setContentsMargins(6, 6, 6, 6)
        window_layout.setSpacing(6)

        # top: static incident list, doesn't scroll away as the dialogue
        # grows. No fixed height cap -- it gets a share of whatever space is
        # available (grows with the window, e.g. maximized/fullscreen) and
        # scrolls natively (QListWidget default) once it has more rows than
        # fit in that space, so it isn't stuck showing only ~4 at a time.
        self.incident_list = QListWidget()
        self.incident_list.setStyleSheet(
            "QListWidget { font-size: 18px; } QListWidget::item { padding: 4px 0; }"
        )
        window_layout.addWidget(self.incident_list, stretch=1)

        # bottom: single dialogue transcript, grows and auto-scrolls with the conversation
        self.transcript_view = QTextEdit()
        self.transcript_view.setReadOnly(True)
        self.transcript_view.setStyleSheet("QTextEdit { font-size: 18px; }")
        window_layout.addWidget(self.transcript_view, stretch=2)

        input_row = QHBoxLayout()
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("Message the agent...")
        self.input_line.setMinimumHeight(48)
        self.input_line.setStyleSheet("QLineEdit { font-size: 20px; padding: 6px 10px; }")
        self.input_line.returnPressed.connect(self._on_send)
        send_btn = QPushButton("Send")
        send_btn.setMinimumHeight(48)
        send_btn.setMinimumWidth(90)
        send_btn.setStyleSheet("QPushButton { font-size: 18px; }")
        send_btn.clicked.connect(self._on_send)
        input_row.addWidget(self.input_line, stretch=1)
        input_row.addWidget(send_btn)
        window_layout.addLayout(input_row)

        layout.addWidget(window, stretch=1)

        self._latest_tag_id: str | None = None
        # tag_id (the internal correlation key routing/agent_manager.py
        # actually use) -> "INC-N" display label. Operators shouldn't see
        # raw scenario keys like "naval_launch_atlantic" -- assigned once,
        # in creation order, and kept even after an incident leaves the
        # pending list so follow-up chat still shows the same number.
        self._incident_numbers: dict[str, int] = {}
        self._next_incident_number = 1

    def label_for(self, tag_id: str) -> str:
        if tag_id not in self._incident_numbers:
            self._incident_numbers[tag_id] = self._next_incident_number
            self._next_incident_number += 1
        return f"INC-{self._incident_numbers[tag_id]}"

    def add_incident(self, tag_id: str, summary: str):
        item = QListWidgetItem(f"● {self.label_for(tag_id)} — {summary}")
        item.setForeground(QColor(_AGENT_ACCENT))
        item.setData(Qt.UserRole, tag_id)
        self.incident_list.addItem(item)
        self.incident_list.scrollToBottom()
        self._latest_tag_id = tag_id

    def remove_incident(self, tag_id: str):
        for i in range(self.incident_list.count()):
            item = self.incident_list.item(i)
            if item.data(Qt.UserRole) == tag_id:
                self.incident_list.takeItem(i)
                return

    def append_message(self, tag_id: str, role: str, text: str, is_decision: bool = False):
        color = _OPERATOR_ACCENT if role == "operator" else _AGENT_ACCENT
        label = "Operator" if role == "operator" else "Agent"
        prefix = f"<b>[{self.label_for(tag_id)}]</b> " if tag_id else ""
        # transcript_view.append() renders its argument as HTML (the <b>
        # tags above make Qt treat the whole string as rich text), and HTML
        # collapses literal newlines to a single space -- so the agent's
        # "one action per line" report was arriving intact but rendering as
        # one run-on line. Escape the model's raw text, then turn its
        # newlines into <br> so line breaks actually survive.
        # Only the section labels get bolded -- almost every line in a
        # typical report is either an "I did this:" action or a "-"
        # suggestion, so bolding line *content* ends up bolding nearly the
        # whole message and nothing stands out. Labels-only keeps it
        # scannable (like a form) without everything shouting.
        lines = [html.escape(line) for line in text.split("\n")]
        styled_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("I did this:"):
                idx = line.index("I did this:") + len("I did this:")
                head, rest = line[:idx], line[idx:]
                styled_lines.append(f'<b>{head}</b>{rest}')
            elif stripped == "I suggest you do this:":
                styled_lines.append(f'<b>{line}</b>')
            else:
                styled_lines.append(line)
        escaped = "<br>".join(styled_lines)
        body = f"<i>{escaped}</i>" if is_decision else escaped
        # break to a new line right after the "Agent: [INC-N]" header (plus
        # a blank line for breathing room), so the first "I did this:" line
        # starts fresh instead of running on the same line as the header.
        # A dashed rule after each message separates one incident's report
        # from the next in the transcript.
        self.transcript_view.append(
            f'<b style="color:{color}">{label}:</b> {prefix}<br><br>{body}<br><br>'
            f'-----------------------------<br>'
        )
        scrollbar = self.transcript_view.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        if is_decision and tag_id:
            self.remove_incident(tag_id)

    def _on_send(self):
        text = self.input_line.text().strip()
        if not text:
            return
        self.input_line.clear()
        tag_id = self._latest_tag_id or ""
        self.append_message(tag_id, "operator", text)
        self.messageSent.emit(tag_id, text)
