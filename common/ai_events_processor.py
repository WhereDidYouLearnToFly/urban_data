"""Fake AI Event Processor — Step 3 of DEV_PLAN.MD.

Simulates cross-event correlation: buffers events sharing a `tag_id`, and
once every event of a group has arrived (`tag_total` reached), synthesizes
the group's main_event / prediction / suggestion events from the scenario's
`groups` block (see Group Schema in DEV_PLAN.MD).
"""
import json

from common.schemas import Event


class ProcessorLogic:
    def __init__(self, scenario_path: str):
        with open(scenario_path) as f:
            self._groups = json.load(f).get("groups", {})
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

        group = self._groups.get(event.tag_id, {})
        contributing = [sid for e in buf for sid in e.contributing_sources]
        max_level = max(e.level for e in buf)

        for action in ("main_event", "prediction", "suggestion"):
            text = group.get(action)
            if not text:
                continue
            derived = Event(
                id=f"{event.tag_id}_{action}",
                level=max_level,
                description=text,
                type=buf[-1].type,
                data=None,
                coordinates=buf[-1].coordinates,
                timestamp=buf[-1].timestamp,
                confidence=1.0,
                contributing_sources=contributing,
                tag_id=event.tag_id,
                tag_ai_action=action,
            )
            out_events.append(derived.to_json())
            if action == "main_event":
                triggers.append(json.dumps({
                    "tag_id": event.tag_id,
                    "summary": group.get("summary"),
                    "main_event": text,
                }).encode())

        del self._buffers[event.tag_id]
        return {"events": out_events, "agent_triggers": triggers}
