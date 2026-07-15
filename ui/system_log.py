"""System Log strip — bottom, full width. Genuine runtime/system messages
(block errors, dropped connections, exceptions) — not event content, see
DEV_PLAN.MD Step 4.

Preview-only: seeded with placeholder log lines.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPlainTextEdit


class SystemLogPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(QLabel("<b>System Log</b>"))

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(500)
        layout.addWidget(self.log_view)

        self._add_placeholder_lines()

    def append(self, message: str):
        self.log_view.appendPlainText(message)

    def _add_placeholder_lines(self):
        for line in [
            "[INFO] Flowgraph started",
            "[INFO] ZMQ SUB connected — tcp://127.0.0.1:5555",
            "[WARN] scenario_controller heartbeat delayed (320ms)",
        ]:
            self.append(line)
