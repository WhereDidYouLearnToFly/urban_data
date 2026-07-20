import base64
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

# Source/Event.type -> assets/<dir> convention (see DEV_PLAN.MD Schemas + Step 5)
TYPE_TO_ASSET_DIR = {
    "photo": "photo",
    "video": "video",
    "audio": "audio",
    "fft": "rf",
    "float_sequence": "seismic",
}


@dataclass
class SourceEvent:
    id: str
    type: str
    data: Optional[str]
    coordinates: dict
    predefined_analysis_result: dict
    offset_seconds: float = 0.0
    tag_id: Optional[str] = None
    tag_total: Optional[int] = None
    heading_deg: Optional[float] = None
    speed_kmh: Optional[float] = None
    predicted_track_id: Optional[str] = None
    target_lat: Optional[float] = None
    target_lon: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "data": self.data,
            "coordinates": self.coordinates,
            "predefined_analysis_result": self.predefined_analysis_result,
            "offset_seconds": self.offset_seconds,
            "tag_id": self.tag_id,
            "tag_total": self.tag_total,
            "heading_deg": self.heading_deg,
            "speed_kmh": self.speed_kmh,
            "predicted_track_id": self.predicted_track_id,
            "target_lat": self.target_lat,
            "target_lon": self.target_lon,
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
        folder = Path(path).parent

        events = []
        for entry in d.get("events", []):
            src = entry["source"]
            data = src.get("data")
            if data is None:
                data = self._load_asset_data(folder, src["id"], src["type"])
            events.append(SourceEvent(
                id=src["id"],
                type=src["type"],
                data=data,
                coordinates=src["coordinates"],
                predefined_analysis_result=src["predefined_analysis_result"],
                offset_seconds=entry["offset_seconds"],
                tag_id=src.get("tag_id"),
                tag_total=src.get("tag_total"),
                heading_deg=src.get("heading_deg"),
                speed_kmh=src.get("speed_kmh"),
                predicted_track_id=src.get("predicted_track_id"),
                target_lat=src.get("target_lat"),
                target_lon=src.get("target_lon"),
            ))

        return Scenario(
            id=d["id"],
            name=d["name"],
            description=d.get("description", ""),
            loop=d.get("loop", False),
            speed_hint=float(d.get("speed_hint", "1").rstrip("x") if isinstance(d.get("speed_hint"), str) else d.get("speed_hint", 1)),
            events=events,
        )

    # Real asset extensions only -- excludes tooling artifacts like
    # generation/*.py's ".generated" completion markers or ".gitkeep",
    # which would otherwise be picked up by a naive glob and could shadow
    # (or silently be served as) the actual media for an event.
    ASSET_EXTENSIONS = {".png", ".jpg", ".jpeg", ".mp4", ".wav", ".json"}

    @staticmethod
    def _load_asset_data(folder: Path, event_id: str, type_: str) -> Optional[str]:
        """Look up scenarios/<name>/assets/<modality>/<event_id>.<ext> and
        base64-encode it, per DEV_PLAN.MD's "data is a base64 blob, never a
        path" rule. Returns None if no matching asset is staged yet.
        """
        asset_dir_name = TYPE_TO_ASSET_DIR.get(type_)
        if not asset_dir_name:
            return None
        asset_dir = folder / "assets" / asset_dir_name
        if not asset_dir.is_dir():
            return None
        matches = sorted(
            f for f in asset_dir.glob(f"{event_id}.*")
            if f.suffix.lower() in ScenarioLoader.ASSET_EXTENSIONS
        )
        if not matches:
            return None
        return base64.b64encode(matches[0].read_bytes()).decode("ascii")
