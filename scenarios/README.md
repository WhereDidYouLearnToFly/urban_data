# Scenarios

Each subfolder is one demo scenario consumed by the Scenario Controller (see DEV_PLAN.MD Step 1.1).

## Structure

```
<scenario_id>/
  scenario.json   — ordered event list with timing and predefined analysis results
  assets/
    photo/        — still images (.jpg, .png)
    video/        — video clips (.mp4)
    audio/        — audio clips (.wav, .mp3)
    rf/           — RF/FFT data (.npy, .csv)
    seismic/      — seismic waveforms (.npy, .csv)
```

Asset folders are empty placeholders until Phase 2 (real + ComfyUI-generated media).

## Scenarios

| Folder | Name | Loop |
|---|---|---|
| `01_all_ok/` | Everything OK | yes |
| `02_small_events/` | Occasional Small Events | no |
| `03_flood/` | Flood | no |
| `04a_drone_attack/` | Drone Attack — Shahed Swarm | no |
| `04b_ground_invasion/` | Ground Invasion — Tank Column | no |

## scenario.json Format

```json
{
  "id": "string",
  "name": "string",
  "description": "string",
  "loop": true,
  "events": [
    {
      "offset_seconds": 0,
      "source": {
        "id": "string",
        "type": "fft | photo | video | audio | float_sequence",
        "data": "path/to/asset or null",
        "coordinates": { "lat": 0.0, "lon": 0.0 },
        "predefined_analysis_result": {
          "event_type": "string",
          "level": 0,
          "description": "string",
          "confidence": 0.0,
          "tag_id": "1/3",
          "tag_ai_action": "main_event | prediction | suggestion"
        }
      }
    }
  ]
}
```

`offset_seconds` is relative to scenario start. The Scenario Controller emits each source event at the correct wall-clock time. When `loop: true`, the sequence repeats from the beginning after the last event.

`data` is `null` until a real asset exists at `assets/<type>/<filename>`.
