# QUESTIONS.md — Implementation Questions

Review questions for the GNU Radio Python blocks:

---

## ai_analyzer.py (Fake AI Analyzer — Step 2)

### Current Design
- Receives `Source` JSON blob from Scenario Controller ZMQ socket
- Extracts `predefined_analysis_result` field
- Converts to full `Event` with timestamp
- Returns Event JSON blob

### Questions
1. Will this be a **GNU Radio embedded Python block** (function: `message_port()`)?
2. **Input/Output format**: GNU Radio blocks exchange bytes, but the flow will use ZMQ PUB/SUB between steps — so output goes to another ZMQ socket, not GR ports? Or will GR message ports connect everything?

---

## ai_processor.py (Fake AI Event Processor — Step 3)

### Current Design
- Loads scenario JSON to get `_groups` dict
- Buffers events by `tag_id`
- When `tag_total` reached, fires `main_event`/`prediction`/`suggestion`
- Returns `{"events": [...], "agent_triggers": [...]}`

### Critical Question
**Lines 15-16**: `ProcessorLogic.__init__` loads `scenario_path`.

But **Problem**: How does the ZMQ message carry the scenario path or groups dict?

### Options
- **Option A**: Message carries scenario_id, processor knows where to load from
- **Option B**: First message includes groups dict as metadata, processor stores in memory
- **Option C**: Processor is a singleton with groups loaded once (no scenario_path needed)

Which option do you prefer?

### Also
- Lines 56-61: Agent triggers are JSON blobs. Are these sent on a **separate ZMQ topic** or same topic?

---

## ZMQ Message Format

### Current
- Topic: `b"urban_data"` (from constants.py)
- Part 1: `urban_data_events` (for processor output)
- Part 2: JSON payload

### Question
**Multipart format**: Should each ZMQ message be `[topic, groups, event]`?

Or just `[topic, event]` (single topic, groups passed via metadata)?

---

## Debug Logging

### Question
You mentioned "message debug until it is done."

- Should we add print logging to both Analyzer and Processor?
- Level flags (DEBUG/INFO/WARN)?
- Log paths (console vs file)?

---

## Constants

### Currently Defined
- `SCENARIO_CONTROLLER_ADDRESS = "tcp://127.0.0.1:5555"`
- `SCENARIO_CONTROLLER_TOPIC = b"urban_data"`
- `PROCESSOR_OUTPUT_ADDRESS = "tcp://127.0.0.1:5556"`
- `PROCESSOR_OUTPUT_TOPIC = b"urban_data_events"`

### Questions
1. Should Analyzer output go to same address (`5556`) or separate?
2. Should agent triggers go to different topic or same?
3. Do we need a **UI listener** address too (for Step 4)?

---

## Next Steps

Please clarify:
1. Scenario loading strategy (Option A/B/C)?
2. ZMQ messaging format (single/multipart)?
3. Debug logging preferences?
4. Address allocation (5556 vs others)?

Once answered, I'll update QUESTIONS.md with your choices.

---

## Answers

Wired up in `grc/urban_data.grc` — see that file for the actual block config.

### ai_analyzer.py
1. **Yes**, embedded Python block (`epy_block` in GRC): a `gr.basic_block` subclass using `message_port_register_in/out` + `set_msg_handler`. Not a plain function.
2. **GR message ports connect everything inside the flowgraph.** ZMQ only exists at the two *boundaries* of the flowgraph: (a) the ZMQ SUB source, which connects to the Scenario Controller's external PUB socket, and (b) a stub ZMQ PUB sink after the Processor, standing in for the not-yet-built Step 4 UI. Between Analyzer → Processor there is no ZMQ hop at all — pure in-process GR message passing. This matches "no ZMQ hop between processor and UI" in `DEV_PLAN.MD`'s Architecture Overview, extended one step earlier to Analyzer→Processor too.

### ai_processor.py
**None of A/B/C** — the groups dict doesn't travel over the wire at all. `scenario_path` is a **GRC block parameter** on the Processor block (see `grc/urban_data.grc`, currently defaults to `scenarios/01_all_ok/scenario.json`), loaded once at flowgraph start. Whoever runs the demo just has to point the Scenario Controller and this block parameter at the *same* scenario before hitting Execute — no runtime handshake needed. Switching scenarios means restarting the flowgraph with a different `scenario_path`, which is fine for a demo. (Closest in spirit to Option C, but via a static block param instead of a hardcoded singleton, so it's still configurable per scenario without editing code.)

**Agent triggers**: separate message port (`agent_trigger`), kept distinct from `events`. It's currently unconnected in the `.grc` (stub for Step 6) — when it does get a ZMQ sink, give it its own topic (e.g. `b"urban_data_agent_trigger"`), not reused `urban_data_events`, so a future agent-listener can subscribe without filtering.

### ZMQ Message Format
**`[topic, event]`** — two parts, matching `scenario_controller/publisher.py` exactly. Groups never go over ZMQ (see above), so there's no third part.

### Debug Logging
Skip custom logging infra for now. The `.grc` already has a `Message Debug` block wired to the Processor's `events` output for console visibility. Don't add print/DEBUG-INFO-WARN plumbing to `common/ai_analyzer.py`/`ai_processor.py` — that's speculative infra we don't need pre-demo; GNU Radio surfaces Python tracebacks from embedded blocks directly in the console anyway. Revisit only if actually debugging something specific.

### Constants / Address Allocation
1. Analyzer doesn't touch ZMQ at all (see above) — only the Processor's `events` port goes out over ZMQ, on `5556`.
2. Agent triggers: different topic, not yet allocated an address (Step 6 concern, currently just a dangling message port).
3. No separate UI listener address needed — Step 4's UI runs in the *same process* as the flowgraph (GRC-generated PyQt5 app with the flowgraph embedded) and consumes events via a direct GR message-port connection. The current `5556` ZMQ sink is an explicit temporary stand-in for that, removed once Step 4's Qt widgets exist.
