"""Debug Controller — event tap for live inspection of the Event stream.

Sits alongside the real ai_events_processor, reading the same Event PDUs from
ai_source_analyzer, and splits each one across the four Message Debug ports by
content:
- print_pdu: raw PDU, always
- print:     human-readable one-line summary, always
- log:       raw PDU, only when level >= LOG_LEVEL_THRESHOLD
- store:     raw PDU, only when tag_ai_action is set (main_event/prediction/suggestion)
"""
from common.schemas import Event

LOG_LEVEL_THRESHOLD = 5


class DebugControllerLogic:
    def handle(self, event_json: bytes) -> dict:
        event = Event.from_json(event_json)
        summary = "[{}] L{} {} (conf={:.2f})".format(
            event.tag_id or "-", event.level, event.description, event.confidence
        ).encode()

        return {
            "print_pdu": event_json,
            "print": summary,
            "log": event_json if event.level >= LOG_LEVEL_THRESHOLD else None,
            "store": event_json if event.tag_ai_action else None,
        }
