import sys
from pathlib import Path

from PyQt5.QtWidgets import QApplication, QMessageBox

from ui.theme import apply_dark
from scenario import ScenarioLoader
from publisher import ZmqPublisher
from controller import ScenarioController
from ui.main_window import MainWindow

SCENARIOS_DIR = Path(__file__).parent.parent / "scenarios"
DEFAULT_ZMQ = "tcp://127.0.0.1:5555"


def main():
    app = QApplication(sys.argv)
    apply_dark(app)

    publisher = ZmqPublisher()
    publisher.connect(DEFAULT_ZMQ)

    loader = ScenarioLoader(str(SCENARIOS_DIR))
    controller = ScenarioController(publisher)

    window = MainWindow()
    controls = window.controls
    log = window.event_log

    # ── populate scenarios ───────────────────────────────────────────────────
    scenarios = loader.list_scenarios()
    controls.populate_scenarios(scenarios)
    _paths = {s["name"]: s["path"] for s in scenarios}

    # ── wire signals ─────────────────────────────────────────────────────────
    def on_scenario_changed(path: str):
        controller.stop()
        log.clear()
        try:
            scenario = loader.load(path)
            controller.load(scenario)
            controls.set_state("stopped")
        except Exception as e:
            QMessageBox.warning(window, "Load error", str(e))

    def on_play():
        if controller.state == "paused":
            controller.resume()
        else:
            controller.start()

    def on_event(event: dict):
        log.append_event(event, controller._elapsed)

    def on_progress(elapsed: float):
        duration = controller.scenario.duration_seconds if controller.scenario else 0
        controls.set_progress(elapsed, duration)

    controls.scenario_changed.connect(on_scenario_changed)
    controls.play_clicked.connect(on_play)
    controls.pause_clicked.connect(controller.pause)
    controls.stop_clicked.connect(controller.stop)
    controls.speed_changed.connect(controller.set_speed)
    controls.zmq_address_changed.connect(lambda addr: (publisher.disconnect(), publisher.connect(addr)))

    controller.event_emitted.connect(on_event)
    controller.state_changed.connect(controls.set_state)
    controller.progress_changed.connect(on_progress)

    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
