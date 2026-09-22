from mcp.server.fastmcp import FastMCP

from app.service import IncidentService

mcp = FastMCP("soc-incidents-controlled")
service = IncidentService()


@mcp.tool()
def retrieve_incident(incident_id: str) -> dict:
    """Retrieve a stored investigation result. Read-only."""
    return service.get(incident_id).model_dump(mode="json")


@mcp.tool()
def create_draft_ticket(incident_id: str, summary: str) -> dict:
    """Create a non-operational draft. Submission remains an analyst action."""
    incident = service.get(incident_id)
    return {"ticket_state": "draft", "incident_id": incident.incident_id, "summary": summary,
            "requires_approval": True, "submitted": False}


if __name__ == "__main__": mcp.run()

