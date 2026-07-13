from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from scenario import Scenario, SourceEvent
from publisher import ZmqPublisher


class ScenarioController(QObject):
    event_emitted = pyqtSignal(dict)
    state_changed = pyqtSignal(str)       # "playing" | "paused" | "stopped" | "finished"
    progress_changed = pyqtSignal(float)  # elapsed real-time seconds

    def __init__(self, publisher: ZmqPublisher, parent=None):
        super().__init__(parent)
        self._publisher = publisher
        self._scenario: Scenario | None = None
        self._speed = 1.0
        self._index = 0
        self._elapsed = 0.0
        self._state = "stopped"

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_tick)

    # ── public API ──────────────────────────────────────────────────────────

    def load(self, scenario: Scenario):
        self.stop()
        self._scenario = scenario
        self._index = 0
        self._elapsed = 0.0

    def start(self):
        if not self._scenario or not self._scenario.events:
            return
        if self._state == "playing":
            return
        self._set_state("playing")
        self._schedule_next()

    def pause(self):
        if self._state != "playing":
            return
        self._timer.stop()
        self._set_state("paused")

    def resume(self):
        if self._state != "paused":
            return
        self._set_state("playing")
        self._schedule_next()

    def stop(self):
        self._timer.stop()
        self._index = 0
        self._elapsed = 0.0
        self._set_state("stopped")
        self.progress_changed.emit(0.0)

    def set_speed(self, speed: float):
        self._speed = max(0.1, speed)

    @property
    def state(self) -> str:
        return self._state

    @property
    def scenario(self) -> Scenario | None:
        return self._scenario

    # ── internal ────────────────────────────────────────────────────────────

    def _set_state(self, state: str):
        self._state = state
        self.state_changed.emit(state)

    def _schedule_next(self):
        if not self._scenario or self._index >= len(self._scenario.events):
            if self._scenario and self._scenario.loop:
                self._index = 0
                self._elapsed = 0.0
                self._schedule_next()
            else:
                self._set_state("finished")
            return

        current_offset = self._scenario.events[self._index].offset_seconds
        delay_ms = max(0, int((current_offset - self._elapsed) / self._speed * 1000))
        self._timer.start(delay_ms)

    def _on_tick(self):
        if self._state != "playing" or not self._scenario:
            return

        event = self._scenario.events[self._index]
        self._elapsed = event.offset_seconds
        self.progress_changed.emit(self._elapsed)

        payload = event.to_dict()
        self._publisher.publish(payload)
        self.event_emitted.emit(payload)

        self._index += 1
        self._schedule_next()
