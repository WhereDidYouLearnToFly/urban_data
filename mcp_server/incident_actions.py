"""Fake MCP server for the incident-response agent (see SKILL.md and
ui/agent_manager.py). Every tool here just logs to stderr and returns a
canned success string -- this is a pre-award demo/PoC, no real dispatch
systems exist, so calling one of these never does anything real. The
point is that the *tool call itself* is real (opencode + local Ollama
genuinely invoke it), only the underlying action is simulated.

Run standalone for a smoke test:  python3 mcp_server/incident_actions.py
Registered for real use via opencode.json's "mcp" block.
"""
import sys

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("incident-actions")


def _log(name: str, **kwargs):
    args = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())
    print(f"[TOOL CALLED] {name}({args})", file=sys.stderr, flush=True)


@mcp.tool()
def dispatch_unit(location: str, unit_type: str) -> str:
    """Dispatch an emergency response unit (ambulance, fire, police, etc.) to a location."""
    _log("dispatch_unit", location=location, unit_type=unit_type)
    return f"Unit '{unit_type}' dispatched to {location}. ETA 4 minutes."


@mcp.tool()
def issue_alert(zone: str, message: str) -> str:
    """Issue a public alert/warning for a zone."""
    _log("issue_alert", zone=zone, message=message)
    return f"Alert issued for zone '{zone}': {message}"


@mcp.tool()
def lock_zone(zone_id: str, reason: str) -> str:
    """Lock down a zone -- reroute traffic, restrict access."""
    _log("lock_zone", zone_id=zone_id, reason=reason)
    return f"Zone '{zone_id}' locked down. Reason: {reason}"


@mcp.tool()
def request_recon(area: str) -> str:
    """Request additional sensor coverage (e.g. drone recon) over an area."""
    _log("request_recon", area=area)
    return f"Recon requested over '{area}'. Additional sensor coverage inbound."


@mcp.tool()
def escalate_caf(reason: str) -> str:
    """Escalate the incident to CAF (Canadian Armed Forces) liaison for situational awareness."""
    _log("escalate_caf", reason=reason)
    return f"Escalated to CAF liaison. Reason: {reason}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
