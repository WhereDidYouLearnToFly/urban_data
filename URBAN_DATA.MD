# Urban Data — Ambient Sensing Demo Design

## 1. Event Types

1. Photo of a flying drone in the sky
2. Video of a large drone flying in the sky
3. Photo of a tank on the highway
4. Video of a tank column moving across a street
5. Photo of heavy traffic
6. Photo/video/sound of an ambulance
7. Photo/video/sound of a firefighter
8. Empty road
9. Empty streets
10. Small traffic violation
11. Explosion
12. Car crash
13. Running person
14. Street fight
15. Mob march
16. "Nothing happening" — baseline/negative event. Needed so the model has a class for "everything is normal" instead of only ever firing on anomalies.
17. Citizen report (ham radio voice, ham radio text, phone app, etc.)

**Open question:** what other event types should be added? Revisit once the demo scenarios (Section 8) are finalized.

## 2. System Pipeline

```
SOURCE 0..N ──▶ Source Standardizer ──▶ AI Source Analyzer (Multimodal) ──▶ Event 00..NN ──▶ AI Event Processor ──▶ UI Representation
```

**Source Standardizer**
Converts each raw feed (camera, mic, seismograph, RF receiver, ...) into the standardized source format (Section 3).

**AI Source Analyzer (multimodal)** — per-source detection:
1. Detect what's in a video/photo
2. Detect what's in an audio clip
3. Detect seismic activity
4. Detect RF patterns associated with drones
5. Detect drones from video (may overlap with #1)
6. Distinguish citizen reports from sensor feeds
7. Detect traffic violations (possibly a separate subsystem — open question)

Each detection emits an **Event** (Section 4).

**AI Event Processor** — a trained model that correlates events across sources and locations to:
- Predict likely outcomes
- Suggest actions
- Make higher-level calls when corroborating events line up (e.g., drone-sound event + explosion event, in the same place and time window, implies a drone strike)

**UI Representation**
1. Every event is plotted on the map as a colored dot (color = event type/severity)
2. An event feed shows a text representation of each event
3. Clicking a photo/video/audio/RF event on the map or feed highlights it and opens a popup with the attached data
4. RF events are rendered as a waterfall plot
5. Open question: what goes in the "middle" — the AI's reasoning process? Suggested actions? A dialogue with an agent? (See Section 7, AI Agent.)

## 3. Standardized Source Structure

Sources arrive from many different systems, so the pipeline needs one standard format plus a script/plugin per source type that converts it into this format:

- `.type` — `fft` | `photo` | `video` | `audio` | `float_sequence`
- `.data` — binary blob
- `.coordinates`

This is also the mechanism that answers the brief's "scalable architecture" outcome: adding a new sensor type only means writing one new plugin that converts it into this standard format — the AI Event Processor and UI never need to change.

## 4. Event Structure

Produced by the AI Source Analyzer, and itself standardized so both the AI Event Processor and the UI can consume it:

- `.level` — severity, 0–10
- `.description` — what was detected
- `.type` — `fft` | `photo` | `video` | `audio` | `float_sequence`
- `.data` — binary blob
- `.coordinates`
- `.confidence` — model confidence for this detection (0–1)
- `.contributing_sources` — IDs of the source(s) this event was derived/fused from

`.confidence` and `.contributing_sources` exist so operators can see *which sensors* backed a call and *how sure* the system is — required for the "explainable and actionable outputs" outcome in the brief.

## 5. Privacy / Anonymization

Civilian-derived feeds (traffic cameras especially) must not expose identifiable people or plates. Faces/plates are blurred **during fake-data preparation**, i.e. run as a real (not simulated) preprocessing pass over the demo's source assets before they ever enter the Source Streamer. This gives the demo one genuinely working module — real anonymization — instead of everything being scripted, and directly addresses the brief's compliance requirement rather than leaving it as a narrative-only claim.

## 6. Target Deployment Hardware

Real system (post-demo) targets NVIDIA Jetson Orin Nano, or Jetson Xavier/Orin NX if more headroom is needed — answers the brief's "rapid deployability / edge-deployable" outcome with a concrete, low-cost, field-portable box rather than a cloud dependency.

## 7. Demo Scope

No training happens before the proposal is submitted — training is what the funding ask is for, and it happens after award. The **UI Representation** module is built for real for the demo; every **AI Source Analyzer** and **AI Event Processor** module is simulated for the demo, no exceptions:

| Module | Demo status | Post-award |
|---|---|---|
| RF (drone detection) | Simulated for the demo, like the rest — but backed by an existing, already-built GNU Radio air-traffic RF scanner, cited in the proposal as proof of team capability | Adapt existing scanner to drone-signature detection |
| Video (OpenCV, extreme situations) | Simulated | To train |
| Audio | Simulated | To train |
| Seismic | Simulated | To train |
| AI Event Processor (fusion/decision maker) | Simulated | To train |

Two applications make up the demo:

**App 1 — Source Streamer**
Drives the source stream for a chosen scenario, imitating a real-life feed. Its output is a source event plus a `[predefined analysis result]` field — a stand-in for what the real AI Source Analyzer would have produced.

**App 2 — the actual demo**
Consumes the Source Streamer's output and fakes the "AI Source Analyzer" step by turning the predefined result into a "real-looking event" plus metadata that imitates the AI Event Processor's output. That real-looking event is what the UI (Section 2) actually renders — on the map, in the feed, and in the detail popup.

To imitate the AI Event Processor's cross-event correlation, each event carries:
- `.tag_id` — e.g. `1/3`, `2/3`, `3/3`, grouping related events together
- `.tag_ai_action` — set once all parts of a group have arrived; one of `main_event` / `prediction` / `suggestion`

**AI Agent.** For a "main event" — something actually detected (drone, tank, flood, earthquake, etc.), not every event — an AI agent is created from the AI Event Processor's result. Each such agent supports a conversation with the operator. This part could be real: a local LLM via Ollama (e.g. Gemma) plus a custom skill exposing dummy/simulated commands, so the conversation itself is live even though the underlying detection is scripted.

## 8. Demo Scenarios

1. Everything is OK
2. Occasional small events
3. Flood (blocked roads, ambulances, etc.)
4. Full-scale invasion:
   - a. Iranian/Russian drone attack (Shaheds) from the sea, US territory, and the North Pole (video, photo, sound)
   - b. Tanks with troops moving from the south into British Columbia and Ontario (triggers seismic activity, video, sound, etc.)

## 9. Available Demo Data Sources

Real datasets already downloaded, for use as Source Streamer assets:

| Path | Modality | Notes |
|---|---|---|
| `~/data/urban_data/video_ontario511` | Video | Live Ontario 511 traffic cams — `cameras.json` (300+ cameras) + fetch script + sample snapshots |
| `~/data/urban_data/audio_urbansound8k` | Audio | 10-class urban sound events (siren, gunshot, engine idling, etc.) |
| `~/data/urban_data/vibration_pnw` | Seismic/vibration | Real Pacific NW Seismic Network waveforms + metadata |
| `~/data/ai_sensor/audio_drone` | Audio | Al-Emadi drone-audio dataset — binary (drone/no-drone) + multiclass, pre-labeled |
| `~/data/ai_sensor/rf_dronerf` | RF | DroneRF signatures per drone/flight mode (still `.rar`, needs extraction) |
| `~/data/ai_sensor/visual_antiuav_sample` | Video | Anti-UAV benchmark clips, day + IR |

None of the above cover tanks, floods, or mob/crowd marches — needed for demo scenarios 3 and 4b (Section 8). These will be synthesized with ComfyUI, using real Ontario 511 camera stills (`video_ontario511`, table above) as the image-to-video base/control frame, so the generated tank column / floodwater / crowd is composited into a specific real camera's actual scene rather than a generic backdrop.

## 10. Presentation & Documentation

To be specified once the demo is built, based on actual results and screenshots.
