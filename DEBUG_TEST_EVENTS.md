# Debug test events (05_invasion)

`05_invasion` has all five media types, so it's a good single scenario for
testing each renderer in isolation. All event IDs below were verified to
resolve real data via `ScenarioLoader._load_asset_data` directly (bypassing
the running app), so if any of these still show nothing in the UI, the bug
is in the app/rendering layer, not missing/misgenerated data.

| Type | Event ID | Description |
|---|---|---|
| photo | src_001 | All systems nominal. Toronto baseline. No anomalies detected |
| photo | src_007 | Ottawa security camera: delta-wing silhouettes at ~150m alt |
| video | src_008 | Ottawa traffic camera: Shahed formation overflying Rideau Canal |
| video | src_1044 | Trudeau Airport camera: transport helicopters discharging troops |
| audio | src_009 | Explosion — Shahed-136 warhead detonation near Union Station |
| audio | src_101 | Maritime patrol acoustic buoy: heavy vessel engine signature |
| fft (RF) | src_002 | RF anomaly over Atlantic — Shahed-136 signature at 900MHz |
| fft (RF) | src_003 | RF cluster Maine/NB border — multiple contacts in formation |
| float_sequence (seismic) | src_018 | Seismic Windsor: 3.8Hz rhythmic vibration from southwest |
| float_sequence (seismic) | src_1085 | Seismic sensor Fredericton area: rhythmic vibration signature |

To test: restart both the Scenario Controller and the UI process (fresh
process, not just reselecting the scenario), load `05_invasion`, then click
each event above one at a time and confirm the popup opens and renders/plays
correctly. Any failure now shows up in the System Log panel with the actual
error (see `ui/main_window.py:_open_media_popup`'s try/except), so check
there first if something doesn't work.
