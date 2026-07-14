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

    def analyze(self, source_json: bytes) -> bytes:
        source = Source.from_json(source_json)
        result = source.predefined_analysis_result
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
        )
        return event.to_json()
