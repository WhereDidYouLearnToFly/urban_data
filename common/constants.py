"""Shared constants for the urban_data demo pipeline.

Keeps the Scenario Controller and the GNU Radio flowgraph in sync without
hardcoding the same address/topic strings in two places.
"""

# Scenario Controller -> GNU Radio flowgraph (see scenario_controller/publisher.py)
SCENARIO_CONTROLLER_ADDRESS = "tcp://127.0.0.1:5555"
SCENARIO_CONTROLLER_TOPIC = b"urban_data"

# Fake AI Processor -> external viewers (stub sink until Step 4 UI exists)
PROCESSOR_OUTPUT_ADDRESS = "tcp://127.0.0.1:5556"
PROCESSOR_OUTPUT_TOPIC = b"urban_data_events"
