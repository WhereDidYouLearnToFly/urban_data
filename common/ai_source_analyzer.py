"""Fake AI Analyzer — Step 2 of DEV_PLAN.MD.

Stands in for the real multimodal AI Source Analyzer: turns a Source PDU
into a full Event PDU. Pass the incoming PDU's raw blob straight to
`analyze` — it handles parsing and re-serialization.
"""
import itertools
from datetime import datetime, timezone

from common.schemas import Event, Source


class AnalyzerLogic:
    def __init__(self):
        self._counter = itertools.count(1)

    def analyze(self, source_json: bytes) -> bytes | None:
        source = Source.from_json(source_json)
        result = source.predefined_analysis_result
        if result["event_type"] == "nothing_happening":
            # a baseline "all clear" reading, not an incident -- nothing to
            # report to the operator, so no Event is produced at all.
            return None
        event = Event(
            id=f"evt_{next(self._counter):04d}",
            level=result["level"],
            description=result["description"],
            type=source.type,
            data=source.data,
            coordinates=source.coordinates,
            timestamp=datetime.now(timezone.utc).isoformat(),
            confidence=result["confidence"],
            contributing_sources=[source.id],
            tag_id=source.tag_id,
            tag_total=source.tag_total,
            tag_ai_action=None,
            heading_deg=source.heading_deg,
            speed_kmh=source.speed_kmh,
            predicted_track_id=source.predicted_track_id,
            target_lat=source.target_lat,
            target_lon=source.target_lon,
        )
        return event.to_json()
