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

        print(summary_text, flush=True)

        return {
            "print_pdu": None,
            "print": None,
            "log": event_json if event.level >= LOG_LEVEL_THRESHOLD else None,
            "store": event_json if event.tag_ai_action else None,
        }
