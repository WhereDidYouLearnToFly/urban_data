"""Canonical event-severity (`.level`, 0-10) -> color mapping. Shared by the
Scenario Controller's event log, the Step 4 UI's events feed, and the map
view, so the same severity renders the same color everywhere. Plain hex
strings — no Qt dependency, per common/'s framework-agnostic convention.
"""

LEVEL_COLORS = {
    0:  "#4caf50",
    1:  "#8bc34a",
    2:  "#cddc39",
    3:  "#ffeb3b",
    4:  "#ffc107",
    5:  "#ff9800",
    6:  "#ff5722",
    7:  "#f44336",
    8:  "#e91e63",
    9:  "#9c27b0",
    10: "#b71c1c",
}


def color_for_level(level: int) -> str:
    return LEVEL_COLORS[max(0, min(int(level), 10))]
