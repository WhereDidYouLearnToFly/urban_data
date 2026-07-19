"""UI entry point -- wraps the GRC-generated flowgraph directly: starts
grc/urban_data.py's top_block in this process, then runs the Qt UI against
its live ZMQ PUB sinks (zmq_sink_0 on 5556, zmq_sink on 5557) via
ui/zmq_client.py.

The Scenario Controller (main.py) is still a separate process -- it feeds
the flowgraph over ZMQ on 5555, same as when the flowgraph runs standalone.
Run from the urban_data root:

    python3 -m ui.main
"""
import os, sys

URBAN_DATA_ROOT = os.path.join(os.path.expanduser("~"), "github", "urban_data")
GRC_DIR = os.path.join(URBAN_DATA_ROOT, "grc")
sys.path.insert(0, URBAN_DATA_ROOT)
# grc/urban_data.py imports its embedded blocks (urban_data_epy_block_N) as
# bare top-level modules, the same way GNU Radio Companion runs it -- needs
# its own directory on sys.path, not just the repo root.
sys.path.insert(0, GRC_DIR)

from PyQt5.QtWidgets import QApplication

from ui.theme import apply_dark
from ui.main_window import MainWindow

from urban_data import urban_data as FlowgraphTopBlock


def main():
    flowgraph = FlowgraphTopBlock()
    flowgraph.start()

    app = QApplication(sys.argv)
    apply_dark(app)
    window = MainWindow()
    window.showFullScreen()

    exit_code = app.exec_()

    flowgraph.stop()
    flowgraph.wait()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
