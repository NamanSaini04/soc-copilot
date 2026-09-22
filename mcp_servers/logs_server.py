import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

ROOT = Path(__file__).resolve().parents[1]
mcp = FastMCP("soc-logs-readonly")


@mcp.tool()
def search_activity(alert_id: str, limit: int = 100) -> list[dict]:
    """Return synthetic events linked to an exact alert ID. Read-only."""
    safe_limit = max(1, min(limit, 500))
    events = json.loads((ROOT / "data" / "events.json").read_text())
    return [e for e in events if e["alert_id"] == alert_id][:safe_limit]


if __name__ == "__main__": mcp.run()

