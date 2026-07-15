"""Standalone preview entry point for the Step 4 UI layout.

Launches just the Qt shell with placeholder content — no GNU Radio
flowgraph, no ZMQ, nothing wired yet. Run from the urban_data root:

    python3 -m ui.main
"""
import os, sys

URBAN_DATA_ROOT = os.path.join(os.path.expanduser("~"), "github", "urban_data")
sys.path.insert(0, URBAN_DATA_ROOT)

from PyQt5.QtWidgets import QApplication

from ui.theme import apply_dark
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    apply_dark(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
