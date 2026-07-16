"""Fake AI Event Processor — Step 3 of DEV_PLAN.MD.

Simulates cross-event correlation: buffers Event PDUs sharing a `tag_id`,
and once every event of a group has arrived (`tag_total` reached),
synthesizes a main_event from the buffered events themselves and fires an
agent_trigger for it. No scenario knowledge — this block only ever sees
data received over ZMQ.
"""
import json

from common.schemas import Event


class ProcessorLogic:
    def __init__(self):
        self._buffers = {}  # tag_id -> list[Event]

    def handle(self, event_json: bytes) -> dict:
        """Returns {"events": [bytes, ...], "agent_triggers": [bytes, ...]}."""
        event = Event.from_json(event_json)

        if not event.tag_id:
            return {"events": [event.to_json()], "agent_triggers": []}

        buf = self._buffers.setdefault(event.tag_id, [])
        buf.append(event)
        out_events = [event.to_json()]
        triggers = []

        if event.tag_total is None or len(buf) < event.tag_total:
            return {"events": out_events, "agent_triggers": triggers}

        contributing = [sid for e in buf for sid in e.contributing_sources]
        max_level = max(e.level for e in buf)
        top_event = max(buf, key=lambda e: e.level)
        summary = "; ".join(e.description for e in buf)

        main_event = Event(
            id=f"{event.tag_id}_main_event",
            level=max_level,
            description=top_event.description,
            type=buf[-1].type,
            data=None,
            coordinates=buf[-1].coordinates,
            timestamp=buf[-1].timestamp,
            confidence=1.0,
            contributing_sources=contributing,
            tag_id=event.tag_id,
            tag_ai_action="main_event",
        )
        out_events.append(main_event.to_json())
        triggers.append(json.dumps({
            "tag_id": event.tag_id,
            "summary": summary,
            "main_event": top_event.description,
        }).encode())

        del self._buffers[event.tag_id]
        return {"events": out_events, "agent_triggers": triggers}
