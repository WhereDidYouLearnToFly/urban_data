import time

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

        # Wall-clock reference for computing a continuously-updating elapsed
        # time between discrete event ticks (see _current_elapsed) -- reset
        # whenever playback starts/resumes/loops or the speed changes, so the
        # displayed clock counts smoothly instead of only jumping forward
        # whenever the next scheduled event happens to fire.
        self._play_started_at = None
        self._elapsed_at_play_start = 0.0

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_tick)

        self._clock_timer = QTimer(self)
        self._clock_timer.setInterval(100)
        self._clock_timer.timeout.connect(self._on_clock_tick)

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
        self._rebase_clock()
        self._clock_timer.start()
        self._schedule_next()

    def pause(self):
        if self._state != "playing":
            return
        self._timer.stop()
        self._clock_timer.stop()
        self._elapsed = self._current_elapsed()
        self._set_state("paused")

    def resume(self):
        if self._state != "paused":
            return
        self._set_state("playing")
        self._rebase_clock()
        self._clock_timer.start()
        self._schedule_next()

    def stop(self):
        self._timer.stop()
        self._clock_timer.stop()
        self._index = 0
        self._elapsed = 0.0
        self._set_state("stopped")
        self.progress_changed.emit(0.0)

    def set_speed(self, speed: float):
        self._speed = max(0.1, speed)
        if self._state == "playing":
            # Rebase so the new rate applies immediately -- both to the
            # displayed clock and to the pending event timer -- instead of
            # only taking effect once whichever event was already scheduled
            # happens to fire.
            self._elapsed = self._current_elapsed()
            self._rebase_clock()
            self._schedule_next()

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

    def _rebase_clock(self):
        self._play_started_at = time.monotonic()
        self._elapsed_at_play_start = self._elapsed

    def _current_elapsed(self) -> float:
        if self._play_started_at is None:
            return self._elapsed
        return self._elapsed_at_play_start + (time.monotonic() - self._play_started_at) * self._speed

    def _on_clock_tick(self):
        if self._state != "playing" or not self._scenario:
            return
        self.progress_changed.emit(self._current_elapsed())

    def _schedule_next(self):
        if not self._scenario or self._index >= len(self._scenario.events):
            if self._scenario and self._scenario.loop:
                self._index = 0
                self._elapsed = 0.0
                self._rebase_clock()
                self._schedule_next()
            else:
                self._clock_timer.stop()
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
        self._rebase_clock()
        self.progress_changed.emit(self._elapsed)

        payload = event.to_dict()
        self._publisher.publish(payload)
        self.event_emitted.emit(payload)

        self._index += 1
        self._schedule_next()
