from mcp.server.fastmcp import FastMCP

from agents.threat_intel_agent import lookup

mcp = FastMCP("soc-threat-intel-approved")


@mcp.tool()
def lookup_indicator(indicator: str) -> dict:
    """Look up one indicator only in the approved synthetic fixture."""
    matches = lookup([indicator])
    return matches[0] if matches else {"indicator": indicator, "status": "no_approved_source_match", "confidence": 0.0}


if __name__ == "__main__": mcp.run()

