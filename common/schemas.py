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
