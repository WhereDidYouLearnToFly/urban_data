"""Debug Controller — event tap for live inspection of the Event stream.

Sits alongside the real ai_events_processor, reading the same Event PDUs from
ai_source_analyzer. Prints a human-readable one-line summary to stdout
directly (message_debug's PDU hex dump isn't readable), and still splits
each event across the log/store Message Debug ports by content:
- print_pdu: unused, always None (superseded by the direct print below)
- print:     unused, always None (superseded by the direct print below)
- log:       raw PDU, only when level >= LOG_LEVEL_THRESHOLD
- store:     raw PDU, only when tag_ai_action is set (main_event/prediction/suggestion)
"""
from common.schemas import Event

LOG_LEVEL_THRESHOLD = 5


class DebugControllerLogic:
    def handle(self, event_json: bytes) -> dict:
        event = Event.from_json(event_json)
        summary_text = "[{}] L{} {} (conf={:.2f})".format(
            event.tag_id or "-", event.level, event.description, event.confidence
        )

        # no flush=True: forcing a synchronous write per event turns a burst
        # of near-simultaneous events (e.g. a drone swarm) into that many
        # blocking syscalls in a row on this thread -- and since this runs
        # on a GNU Radio embedded-block thread sharing the same GIL as the
        # Qt main thread, a stall here can freeze the whole UI, not just
        # this print. Let normal buffering (line-buffered on a TTY, block-
        # buffered otherwise) batch it instead.
        print(summary_text)

        return {
            "print_pdu": None,
            "print": None,
            "log": event_json if event.level >= LOG_LEVEL_THRESHOLD else None,
            "store": event_json if event.tag_ai_action else None,
        }
