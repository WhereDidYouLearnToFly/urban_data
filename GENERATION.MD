# Media Generation Plan

Every scenario event should have real, clickable media behind it (photo/video/
audio/RF/seismic) generated from that event's own `description` text, instead
of placeholder stock assets. This file is the working plan/notes for that
pass -- manifests live in `generation/`, nothing has been generated yet.

## Current state (as of writing)

Photo and video are already "covered" for scenarios `02_small_events`
through `05_invasion`, but with **placeholders** (real 511 highway-camera
photos, trimmed anti-UAV dataset video clips) -- not content generated from
each event's actual description. The goal is to replace those with real
generations. RF and seismic for those same four scenarios are already real
recorded data (DroneRF captures, PNSN waveforms) -- no work needed there.

`06_nuclear_war` has zero staged assets of any kind (it was authored as pure
JSON, "just for fun," not demo material) -- fft, float_sequence, and audio
are all missing.

## Manifests (`generation/`)

- `manifest.json` -- 114 entries, photo + video, every event across
  `02`-`05`. Each entry: `scenario`, `event_id`, `type`, `description`,
  `coordinates`, `current_asset` (the placeholder it replaces), `target_path`.
- `manifest_audio.json` -- 99 entries, every event with no real staged audio
  (60 in `05_invasion`'s ham-radio/citizen-report events, a handful in
  `02`-`04`, all 32 audio events in `06_nuclear_war`).
- `manifest_rf_seismic.json` -- 192 entries, all of `06_nuclear_war`'s fft
  (164) and float_sequence (28) events.

Regenerate any of these by re-running the extraction (walk each
`scenario.json`, filter by `type` + missing/placeholder asset) if scenario
content changes before generation actually happens.

## Photo / video -- ComfyUI

- Models: **flux1-krea-dev** (photo), **ltx-2-19b** (video). Both already
  present under `~/ComfyUI/models/`. ComfyUI itself is installed but not
  currently running -- needs to be started (`/system_stats` on :8188 to
  confirm it's up) before the generation script can hit its API.
- Driven by `manifest.json`, submitting via ComfyUI's `/prompt` API and
  polling `/history` for each job, saving the result to that entry's
  `target_path` (which already matches the convention
  `ScenarioLoader._load_asset_data` expects -- nothing downstream needs to
  change once the file lands there).
- **Open item: prompt rewriting.** The `description` field is sensor-report
  text (e.g. "Downtown Toronto — civilian resistance on King St West. Small
  arms fire from buildings. Helicopters firing rockets at buildings"), not a
  well-formed image/video prompt. Feeding it to Flux/LTX verbatim will
  produce *something* but probably not great results. Plan is to add a
  rewrite step (raw description -> actual generation prompt) rather than
  pipe descriptions straight into the model -- not yet designed.
- Rough time budget: photos ~30-60s each (~1-2 hrs for all 114), video is
  the expensive part -- LTX-2-19b generating 23 clips could be 1-2+ hrs
  depending on clip length/steps. Scripted (submit -> poll -> save -> next)
  so it can run mostly unattended once started.

## Audio -- TTS via ComfyUI

- Decision: install a TTS custom node in ComfyUI (VibeVoice or similar) so
  audio generation stays on the same pipeline/API as photo/video, rather
  than a separate standalone TTS tool.
- **Open item: VibeVoice isn't actually installed yet.** There's an empty
  `~/ComfyUI/models/vibevoice/` folder (past intent, never finished) but no
  corresponding custom node in `~/ComfyUI/custom_nodes/`. This needs a real
  install (clone the node, pull weights, verify it loads) before any audio
  generation can run -- untested, budget extra time for this specifically.
- Driven by `manifest_audio.json`: TTS reads each event's `description`
  aloud, then run the output through a bandpass/static filter pass (ffmpeg)
  for radio-chatter grit -- these are all framed as ham-radio/citizen
  reports, not clean broadcast audio.
- Rough time budget: fast once the node is working, ~20-30 min for all 99.

## RF / seismic -- numpy synthesis, no ComfyUI

- Only needed for `06_nuclear_war` (192 events). This is **not** a
  generative-model task -- same approach as the real RF/seismic data
  already staged for the other scenarios (RF computed via numpy FFT from
  real DroneRF captures, seismic pulled from real PNSN waveforms), just
  synthesized instead of sourced, since there's no real "nuclear detonation
  seismic signature" dataset to pull from.
- Driven by `manifest_rf_seismic.json`. Cheap (seconds, no GPU) -- could be
  done independently of the ComfyUI session entirely, any time.

## Risks / open items going into the generation session

1. Prompt-rewrite step for photo/video isn't designed yet (see above).
2. VibeVoice install is unproven -- real setup risk, not just a config flag.
3. ComfyUI needs to be started before anything can run.
4. `06_nuclear_war` currently has no photo/video events at all -- out of
   scope unless that's added later.
