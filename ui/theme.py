"""Re-exports the dark palette from scenario_controller's UI, so both apps
(Scenario Controller and this one) look visually consistent.
"""
import os, sys

URBAN_DATA_ROOT = os.path.join(os.path.expanduser("~"), "github", "urban_data")
sys.path.insert(0, URBAN_DATA_ROOT)

from scenario_controller.ui.theme import apply_dark

__all__ = ["apply_dark"]
