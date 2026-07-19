"""Source and Event schema definitions shared by the Scenario Controller and
the GNU Radio flowgraph. Keep in sync with the "Schemas" section of
DEV_PLAN.MD — that document is the canonical field list.
"""
import json
from dataclasses import asdict, dataclass
from typing import Optional


@dataclass
class Source:
    id: str
    type: str
    coordinates: dict
    predefined_analysis_result: dict
    data: Optional[str] = None
    offset_seconds: float = 0.0
    tag_id: Optional[str] = None
    tag_total: Optional[int] = None
    # Optional authored movement hint for a moving threat (drone, mob, tank
    # column, ...) -- static per-event metadata, not a live tracking feed.
    # Consumed by the map view to draw a directional arrow + trail instead
    # of a plain dot. None means "static, render as a dot" as before.
    heading_deg: Optional[float] = None
    speed_kmh: Optional[float] = None
    # Ties repeat sightings of the *same physical tracked object* together
    # for the map's predicted-path re-anchoring, independent of tag_id (which
    # groups events into an incident for the agent system -- a different
    # concern, e.g. three simultaneous-but-distinct RF contacts can share one
    # tag_id/incident while each needing its own separate predicted path).
    # None means "no cross-event continuity" -- path is keyed by this
    # event's own id instead.
    predicted_track_id: Optional[str] = None
    # Where the moving object is actually headed, if known -- the map draws
    # the predicted path from this event's own coordinates to this point
    # (real distance), instead of guessing a fixed-length line from
    # heading_deg alone. heading_deg (and the arrow icon) are then derived
    # from these two points rather than authored separately, which is also
    # what keeps them from drifting out of sync with each other. None means
    # "no known destination" -- falls back to the short heading-only line.
    target_lat: Optional[float] = None
    target_lon: Optional[float] = None

    @classmethod
    def from_json(cls, blob: bytes) -> "Source":
        return cls(**json.loads(blob))


@dataclass
class Event:
    id: str
    level: int
    description: str
    type: str
    coordinates: dict
    timestamp: str
    confidence: float
    contributing_sources: list
    data: Optional[str] = None
    tag_id: Optional[str] = None
    tag_total: Optional[int] = None
    tag_ai_action: Optional[str] = None
    heading_deg: Optional[float] = None
    speed_kmh: Optional[float] = None
    predicted_track_id: Optional[str] = None
    # Where the moving object is actually headed, if known -- the map draws
    # the predicted path from this event's own coordinates to this point
    # (real distance), instead of guessing a fixed-length line from
    # heading_deg alone. heading_deg (and the arrow icon) are then derived
    # from these two points rather than authored separately, which is also
    # what keeps them from drifting out of sync with each other. None means
    # "no known destination" -- falls back to the short heading-only line.
    target_lat: Optional[float] = None
    target_lon: Optional[float] = None

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> bytes:
        return json.dumps(self.to_dict()).encode()

    @classmethod
    def from_dict(cls, d: dict) -> "Event":
        return cls(**d)

    @classmethod
    def from_json(cls, blob: bytes) -> "Event":
        return cls.from_dict(json.loads(blob))
