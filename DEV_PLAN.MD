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
| 2 — Fake AI Analyzer | ⬜ Todo | GNU Radio custom Python block |
| 3 — Fake AI Processor | ⬜ Todo | GNU Radio custom Python block |
| 4 — UI Application | ⬜ Todo | `ui/` |
| 5 — Media Assets | ⬜ Todo | `assets/` |
| 6 — Live Agents + MCP | ⬜ Todo | `mcp_server/`, `SKILL.md` |

---

## Phase 1 — Demo Skeleton

### Step 1: Scenario JSON ✅
All demo scenarios as structured JSON files. Coordinates and descriptions generated. No media required at this stage.

**Output:** `scenarios/` — one subfolder per scenario, each with `scenario.json` and placeholder `assets/{photo,video,audio,rf,seismic}/` folders.

| Scenario | Events | Duration | Loop |
|---|---|---|---|
| `01_all_ok` | 8 | 2m 20s | yes |
| `02_small_events` | 16 | 10m | no |
| `03_flood` | 22 | 13m | no |
| `04a_drone_attack` | 22 | 10m | no |
| `04b_ground_invasion` | 42 | 24m (×10 = 2m 24s) | no |

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

### Step 2: Fake AI Analyzer
GNU Radio custom Python block. Subscribes to Scenario Controller ZMQ output. Converts each incoming `predefined_analysis_result` field into a full Event (see Event Schema).

- Input: Source PDU from ZMQ SUB Message Source
- Output: Event PDU with all Event Schema fields populated
- Adds `timestamp` (wall clock at receive time)
- Passes `tag_id` and `tag_ai_action` through unchanged

**Output:** GNU Radio OOT block or embedded GRC Python block

---

### Step 3: Fake AI Event Processor
GNU Radio custom Python block. Receives Event PDUs from Step 2. Simulates cross-event correlation.

- Accumulates events by `tag_id` group
- When all parts of a group arrive, sets `tag_ai_action` on the group's events
- Emits `prediction` and `suggestion` events for `main_event` detections
- For `main_event`: emits an agent-trigger message (stub for Step 6)

**Output:** GNU Radio OOT block or embedded GRC Python block

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
All ZMQ messages use multipart: `[topic_bytes, json_payload_bytes]`
- **Topic:** `b"urban_data"`
- **Payload:** JSON string

In GNU Radio: use `ZMQ SUB Message Source` / `ZMQ PUB Message Sink` blocks (not stream variants).

### Source Schema
Produced by the Scenario Controller. Input to the GNU Radio flowgraph.

```json
{
  "id": "string",
  "type": "fft | photo | video | audio | float_sequence",
  "data": "path/to/asset or null",
  "coordinates": { "lat": 0.0, "lon": 0.0 },
  "offset_seconds": 0.0,
  "predefined_analysis_result": {
    "event_type": "string",
    "level": 0,
    "description": "string",
    "confidence": 0.0,
    "tag_id": "1/3",
    "tag_ai_action": "main_event | prediction | suggestion"
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
| 1 | Everything OK | 8 (loops) | Baseline "nothing happening" across Toronto, Ottawa, Vancouver |
| 2 | Small events | 16 | Traffic violation, car crash, ambulance, street fight, gas smell |
| 3 | Flood | 22 | Don + Humber flood, water rescue, citizen radio reports |
| 4a | Drone attack | 22 | Shahed swarm: RF → acoustic → visual → impacts in Toronto + Ottawa |
| 4b | Ground invasion | 42 | Two-column invasion Ontario + BC, 6 phases, seismic → border → urban combat |

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
