# Urban Data — Development Plan

## Goal
Build a demonstrable grant-proposal demo in the shortest time possible. All AI modules are simulated/scripted. Architecture must be clean and modular so real logic can replace each module post-funding.

---

## Architecture Overview

```
┌─────────────────────┐        ┌────────────────────────────────────────────────────────────────┐
│  Scenario Controller│        │  GRC Application (PyQt5)                                       │
│  (PyQt5 + ZMQ PUB)  │──ZMQ──▶│  ZMQ SUB ▶ Fake Analyzer ▶ Fake Processor                     │
│  scenario_controller│        │                                   │ message port                │
└─────────────────────┘        │                                   ▼                            │
                               │                         Custom Qt Widgets                      │
                               │                         (map, event feed, popups)              │
                               └────────────────────────────────────────────────────────────────┘
```

**Demo mode:** Scenario Controller feeds the flowgraph via ZMQ.
**Production mode:** Real hardware sources replace the Scenario Controller. The GRC application stays identical.

The UI is a wrapper around the GNU Radio processor — a GRC-generated PyQt5 app with custom Qt widgets (map, feed, detail popups) added alongside the flowgraph blocks. No ZMQ hop between processor and UI; they run in the same process and communicate via GNU Radio message ports.

The GRC flowgraph diagram is also a presentation asset — it visually proves the modular architecture to reviewers.

### GNU Radio data models
GNU Radio supports two parallel data flow models. Both are used in this project:

| Model | Used for | GNU Radio mechanism |
|---|---|---|
| **Stream** | RF/FFT, audio PCM, seismic float sequences | Sample stream → DSP blocks |
| **Message / PDU** | Images, video frames, JSON, custom structs | `(metadata_dict, data_blob)` PMT pairs |

All inter-process data (Scenario Controller → GR, GR → UI) travels as **PDU messages over ZMQ** using `ZMQ PUB/SUB Message` blocks. The blob field carries the payload (JPEG bytes, JSON string, numpy array, etc.).

---

## Status

| Step | Status | Output |
|---|---|---|
| 1 — Scenario JSON | ✅ Done | `scenarios/` — 5 scenarios, 110 total events |
| 1.1 — Scenario Controller | ✅ Done | `scenario_controller/` — PyQt5 UI + ZMQ PUB |
| 2 — Fake AI Analyzer | 🔶 Logic done, GRC wiring pending | `common/ai_analyzer.py` |
| 3 — Fake AI Processor | 🔶 Logic done, GRC wiring pending | `common/ai_processor.py` |
| 4 — UI Application | ⬜ Todo | `ui/` |
| 5 — Media Assets | ⬜ Todo | `assets/` |
| 6 — Live Agents + MCP | ⬜ Todo | `mcp_server/`, `SKILL.md` |

---

## Phase 1 — Demo Skeleton

### Step 1: Scenario JSON ✅
All demo scenarios as structured JSON files. Coordinates and descriptions generated. No media required at this stage.

**Output:** `scenarios/` — one subfolder per scenario, each with `scenario.json` and placeholder `assets/{photo,video,audio,rf,seismic}/` folders.

| Scenario        | Events | Duration | Loop |
|-----------------|--------|----------|------|
|`01_all_ok`      | 8      | 2m 20s   | yes  |
|`02_small_events`| 15     | 9m 20s   | no   |
|`03_flood`       | 20     | 11m 40s  | no   |
|`04_mob_protests`| 17     | 6m 20s   | no   |
|`05_invasion`    | 45     | 21m 20s  | no   |

---

### Step 1.1: Scenario Controller ✅
PyQt5 desktop app. Reads scenario JSON and replays events over a ZMQ PUB socket at configurable speed.

**Files:** `scenario_controller/`
- `main.py` — entry point, wires everything
- `scenario.py` — `SourceEvent`, `Scenario`, `ScenarioLoader`
- `controller.py` — `ScenarioController` (QObject + QTimer, play/pause/stop/speed)
- `publisher.py` — `ZmqPublisher` (ZMQ PUB, topic `urban_data`)
- `ui/controls.py` — scenario picker, transport controls, speed slider, ZMQ address field
- `ui/event_log.py` — color-coded live event log (color = severity 0–10)
- `ui/main_window.py` — main window shell

**Run:** `cd scenario_controller && python3 main.py`
**Default ZMQ address:** `tcp://127.0.0.1:5555`

---

### GNU Radio Flowgraph Skeleton
`grc/urban_data.grc` (wired directly in gnuradio-companion):

```
[ZMQ PDU Source]  →  [Fake AI Analyzer]  →  [Fake AI Processor]  →  [ZMQ PUB Message Sink] (+ [Message Debug])
 tcp://127.0.0.1:5555                                                  tcp://127.0.0.1:5556
 topic "urban_data"                                                     topic "urban_data_events"
```

The ZMQ PUB sink is a stub standing in for Step 4 — lets the eventual UI (or a throwaway subscriber) be tested against real Event PDUs before the direct message-port wiring exists. Step 4 replaces it with a GNU Radio message-port connection straight into the Qt widgets (no ZMQ hop between processor and UI, per Architecture Overview above). Message Debug stays attached alongside for console visibility during development.

**Shared logic:** `common/` — plain Python, no GNU Radio dependency, unit-testable outside GRC:
- `common/schemas.py` — `Source`/`Event` dataclasses (canonical field list, mirrors Schemas section below)
- `common/constants.py` — ZMQ addresses/topics, shared with `scenario_controller`
- `common/ai_analyzer.py` — Step 2 logic
- `common/ai_processor.py` — Step 3 logic

**Import convention:** each embedded Python block bootstraps `sys.path` relative to its own `__file__` (one directory up, since `grc/` sits next to `common/` at repo root) before importing from `common` — no packaging/install step needed:
```python
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))
from common.ai_analyzer import AnalyzerLogic
```

---

### Step 2: Fake AI Analyzer
GNU Radio embedded Python block (`gr.basic_block`). GR message ports connect to Processor (pure in-process, no ZMQ). Converts incoming `predefined_analysis_result` field into a full Event (see Event Schema).

**Input/Output:** GR message ports (In/Out)
- **Input:** Source PDU blob from ZMQ Source
- **Output:** Event PDU blob (timestamp added, `tag_id` passed through, `tag_ai_action` = null)

**Logic:** `common/ai_analyzer.py` — `AnalyzerLogic.analyze(source_json: bytes) -> bytes`

**GRC wiring:** Embedded Python block wraps `AnalyzerLogic`

**Output:** `grc/urban_data.grc` embedded Python block ("Fake AI Analyzer")

---

### Step 3: Fake AI Event Processor
GNU Radio custom Python block. Receives Event PDUs from Step 2. Simulates cross-event correlation.

- Accumulates events by `tag_id` group
- When `tag_total` events for a `tag_id` have arrived, synthesizes `main_event`/`prediction`/`suggestion` events from the scenario's `groups` block
- For `main_event`: emits a separate agent-trigger message on its own port (stub for Step 6)

**Logic:** `common/ai_processor.py` — `ProcessorLogic(scenario_path).handle(event_json: bytes) -> dict`, returns `{"events": [...], "agent_triggers": [...]}`. Loads `groups` from the active scenario's JSON at init via `scenario_path` block parameter.

**GRC wiring:** embedded Python block with two message outputs — `events` (to ZMQ PUB) and `agent_trigger` (stub for Step 6). `scenario_path` exposed as a GRC block parameter.

**Agent triggers:** Separate message port (`agent_trigger`), kept distinct from `events` — currently unconnected in `.grc` (stub for Step 6, no ZMQ sink exists yet). When it does get one, give it its own topic (not `urban_data_events`) so a future agent-listener can subscribe without filtering — exact topic string not decided yet / not in `common/constants.py`.

**Output:** `grc/urban_data.grc` embedded Python block ("Fake AI Processor")

---

### Step 4: UI Application
GRC-generated PyQt5 application. The GNU Radio flowgraph runs inside it. Custom Qt widgets are added to the same window and receive processed events via GNU Radio message ports — no ZMQ between processor and UI.

- **Map view:** custom QWidget drawing event dots over a static Canada map tile (color = event type / severity). Click a dot to open detail popup.
- **Event feed:** QListWidget — scrolling color-coded event log
- **Detail popup:** QDialog showing event metadata + attached media (QLabel for photo, QMediaPlayer for video/audio, QPainter widget for RF waterfall)
- **Dark theme:** shared `ui/theme.py` palette

**Output:** `grc/urban_data.grc` + `grc/urban_data.py` (generated), custom widget files alongside

---

## Phase 2 — Real Media

### Step 5: Media Assets
Attach real and generated media to scenario events.

- Copy applicable datasets from `~/data/` into `scenarios/<id>/assets/`
- Generate missing visuals with ComfyUI (tanks, mobs, explosions, floods) using Ontario 511 stills as control frames
- Run anonymization pass on civilian footage (blur faces and plates)
- Update scenario JSON `data` fields to reference asset file paths

**Output:** populated `scenarios/<id>/assets/` folders; updated `scenario.json` files

---

## Phase 3 — Live Agents & Polish

### Step 6: UI Finalization + Real Agents + MCP Server
- Wire Ollama LLM (e.g. Gemma) to `main_event` triggers so operators can converse with a per-incident AI agent
- Build `SKILL.md` and MCP server exposing simulated reaction commands (dispatch unit, issue alert, lock zone, etc.)
- Polish UI

**Output:** `mcp_server/`, updated `ui/`, `SKILL.md`

---

## Schemas

### ZMQ Message Format
All ZMQ messages use multipart: `[topic_bytes, json_payload_bytes]`. Two separate hops, each with its own address/topic (see `common/constants.py`):
- **Scenario Controller → flowgraph:** `tcp://127.0.0.1:5555`, topic `b"urban_data"`, payload = Source Schema
- **Processor → stub sink (Step 4 stand-in):** `tcp://127.0.0.1:5556`, topic `b"urban_data_events"`, payload = Event Schema

In GNU Radio: use `ZMQ SUB Message Source` / `ZMQ PUB Message Sink` blocks (not stream variants).

### Group Schema
Defined at the scenario level. The AI Processor fires the group result when all events sharing a `tag_id` have arrived (event count == `tag_total`).

```json
"groups": {
  "<tag_id>": {
    "summary": "what this group of events collectively means",
    "main_event": "confirmed incident description, or null",
    "prediction": "what is likely to happen next, or null",
    "suggestion": "recommended action, or null"
  }
}
```

### Source Schema
Produced by the Scenario Controller. Input to the GNU Radio flowgraph.

```json
{
  "id": "string",
  "type": "fft | photo | video | audio | float_sequence",
  "data": "path/to/asset or null",
  "coordinates": { "lat": 0.0, "lon": 0.0 },
  "offset_seconds": 0.0,
  "tag_id": "string or omitted if standalone",
  "tag_total": 3,
  "predefined_analysis_result": {
    "event_type": "string",
    "level": 0,
    "description": "string",
    "confidence": 0.0
  }
}
```

### Event Schema
Produced by the Fake AI Analyzer block. Input to the Fake AI Processor block and the UI.

```json
{
  "id": "string",
  "level": 0,
  "description": "string",
  "type": "fft | photo | video | audio | float_sequence",
  "data": "path/to/asset or null",
  "coordinates": { "lat": 0.0, "lon": 0.0 },
  "timestamp": "ISO 8601",
  "confidence": 0.0,
  "contributing_sources": ["source_id"],
  "tag_id": "1/3",
  "tag_ai_action": "main_event | prediction | suggestion"
}
```

---

## Demo Scenarios

| # | Name | Events | Key content |
|---|---|---|---|
| 01 | Everything OK | 8 (loops) | Baseline "nothing happening" across Toronto, Ottawa, Vancouver |
| 02 | Small events | 15 | Traffic violation, car crash, ambulance, street fight, gas smell |
| 03 | Flood | 20 | Don + Humber flood, water rescue, citizen radio reports |
| 04 | Coordinated Civil Unrest | 17 | Simultaneous riots Toronto + Ottawa + Vancouver, coordinated pattern detected |
| 05 | Full Scale Invasion | 45 | Shahed drones → Ka-52 helicopters + airborne desant → two armored columns → urban combat |

---

## Available Data

| Path | Modality | Notes |
|---|---|---|
| `~/data/urban_data/video_ontario511` | Video | 300+ Ontario 511 traffic cams, `cameras.json` + fetch script |
| `~/data/urban_data/audio_urbansound8k` | Audio | 10-class urban sounds (siren, gunshot, engine idle, etc.) |
| `~/data/urban_data/vibration_pnw` | Seismic | Pacific NW Seismic Network waveforms + metadata |
| `~/data/ai_sensor/audio_drone` | Audio | Drone audio — binary (drone/no-drone) + multiclass, labeled |
| `~/data/ai_sensor/rf_dronerf` | RF | DroneRF signatures per drone/flight mode (`.rar`, needs extraction) |
| `~/data/ai_sensor/visual_antiuav_sample` | Video | Anti-UAV benchmark clips, day + IR |

Tanks, floods, mobs not in real data — generate with ComfyUI (Step 5).

---

## Event Types Reference

1. Photo — drone in sky
2. Video — large drone in sky
3. Photo — tank on highway
4. Video — tank column on street
5. Photo — heavy traffic
6. Photo/video/audio — ambulance
7. Photo/video/audio — firefighter
8. Empty road
9. Empty streets
10. Small traffic violation
11. Explosion
12. Car crash
13. Running person
14. Street fight
15. Mob march
16. Nothing happening (baseline / negative class)
17. Citizen report (ham radio voice/text, phone app)
