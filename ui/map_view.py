"""Map view — right column. Event dots over a Canada map, Arctic called out
separately at the top (per hg.jpg).

Preview-only: draws a placeholder outline, no real map tile or geo
projection yet, so the layout can be reviewed before that asset exists.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtCore import Qt, QRectF


class MapView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(QLabel("<b>Map</b>"))
        layout.addStretch()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        margin = 20
        arctic_rect = QRectF(margin, margin + 24, self.width() - 2 * margin, 28)
        canada_rect = QRectF(margin, arctic_rect.bottom() + 8,
                              self.width() - 2 * margin,
                              self.height() - arctic_rect.bottom() - margin - 8)

        painter.setPen(QPen(QColor(140, 180, 210), 2))
        painter.setBrush(QColor(35, 50, 65))
        painter.drawRoundedRect(arctic_rect, 10, 10)
        painter.setPen(QColor(200, 225, 245))
        painter.drawText(arctic_rect, Qt.AlignCenter, "ARCTIC")

        painter.setPen(QPen(QColor(120, 160, 200), 2))
        painter.setBrush(QColor(40, 55, 70))
        painter.drawRoundedRect(canada_rect, 12, 12)
        painter.setPen(QColor(220, 220, 220))
        painter.drawText(canada_rect, Qt.AlignCenter, "CANADA\n(placeholder outline)")

        super().paintEvent(event)
