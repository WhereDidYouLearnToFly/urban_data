import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class SourceEvent:
    id: str
    type: str
    data: Optional[str]
    coordinates: dict
    predefined_analysis_result: dict
    offset_seconds: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "data": self.data,
            "coordinates": self.coordinates,
            "predefined_analysis_result": self.predefined_analysis_result,
            "offset_seconds": self.offset_seconds,
        }


@dataclass
class Scenario:
    id: str
    name: str
    description: str
    loop: bool
    speed_hint: float
    events: list[SourceEvent] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        if not self.events:
            return 0.0
        return self.events[-1].offset_seconds


class ScenarioLoader:
    def __init__(self, scenarios_dir: str):
        self.scenarios_dir = Path(scenarios_dir)

    def list_scenarios(self) -> list[dict]:
        result = []
        for folder in sorted(self.scenarios_dir.iterdir()):
            json_path = folder / "scenario.json"
            if json_path.exists():
                with open(json_path) as f:
                    d = json.load(f)
                result.append({"id": d["id"], "name": d["name"], "path": str(json_path)})
        return result

    def load(self, path: str) -> Scenario:
        with open(path) as f:
            d = json.load(f)

        events = []
        for entry in d.get("events", []):
            src = entry["source"]
            events.append(SourceEvent(
                id=src["id"],
                type=src["type"],
                data=src.get("data"),
                coordinates=src["coordinates"],
                predefined_analysis_result=src["predefined_analysis_result"],
                offset_seconds=entry["offset_seconds"],
            ))

        return Scenario(
            id=d["id"],
            name=d["name"],
            description=d.get("description", ""),
            loop=d.get("loop", False),
            speed_hint=float(d.get("speed_hint", "1").rstrip("x") if isinstance(d.get("speed_hint"), str) else d.get("speed_hint", 1)),
            events=events,
        )
