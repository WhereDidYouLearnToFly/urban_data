from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt


def apply_dark(app: QApplication):
    app.setStyle("Fusion")
    p = QPalette()
    p.setColor(QPalette.Window,          QColor(30, 30, 30))
    p.setColor(QPalette.WindowText,      QColor(220, 220, 220))
    p.setColor(QPalette.Base,            QColor(22, 22, 22))
    p.setColor(QPalette.AlternateBase,   QColor(38, 38, 38))
    p.setColor(QPalette.ToolTipBase,     QColor(50, 50, 50))
    p.setColor(QPalette.ToolTipText,     QColor(220, 220, 220))
    p.setColor(QPalette.Text,            QColor(220, 220, 220))
    p.setColor(QPalette.Button,          QColor(50, 50, 50))
    p.setColor(QPalette.ButtonText,      QColor(220, 220, 220))
    p.setColor(QPalette.BrightText,      Qt.red)
    p.setColor(QPalette.Highlight,       QColor(0, 120, 215))
    p.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    p.setColor(QPalette.Link,            QColor(100, 180, 255))
    p.setColor(QPalette.Disabled, QPalette.Text,       QColor(100, 100, 100))
    p.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(100, 100, 100))
    p.setColor(QPalette.Disabled, QPalette.WindowText, QColor(100, 100, 100))
    app.setPalette(p)
