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

## Scenarios

| Folder | Name | Loop |
|---|---|---|
| `02_small_events/` | Occasional Small Events | no |
| `03_flood/` | Flood | no |
| `04_mob_protests/` | Mob Protests | no |
| `05_invasion/` | Full Scale Invasion | no |
| `06_nuclear_war/` | Nuclear War | no |

### Debug scenarios

`05a`–`05e` split `05_invasion`'s 228 events out by media type, one renderer
per scenario, for isolating popup/rendering bugs without waiting through the
full 21-minute combined run. Each reuses `05_invasion`'s asset files via a
symlinked `assets/<type>/` directory (no data duplicated) and re-spaces its
events 4 seconds apart starting at `offset_seconds: 0`.

| Folder | Name | Type | Events |
|---|---|---|---|
| `05a_invasion_photo/` | Invasion — Photo Debug | `photo` | 59 |
| `05b_invasion_video/` | Invasion — Video Debug | `video` | 23 |
| `05c_invasion_audio/` | Invasion — Audio Debug | `audio` | 105 |
| `05d_invasion_rf/` | Invasion — RF/FFT Debug | `fft` | 31 |
| `05e_invasion_seismic/` | Invasion — Seismic Debug | `float_sequence` | 10 |

To use: restart the Scenario Controller and UI (fresh process), load one of
these, and click through the event feed. Popup failures now show up in the
System Log with the actual exception (see `ui/main_window.py`'s
`_open_media_popup`), so check there first.

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
