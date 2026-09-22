import json
from pathlib import Path

from agents.workflow import SOCCopilot
from app.models import Alert, ApprovalRequest, InvestigationResult

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RESULTS = ROOT / "reports" / "incidents" / "json"


class IncidentService:
    def __init__(self):
        RESULTS.mkdir(parents=True, exist_ok=True)
        self.alerts = [Alert.model_validate(x) for x in json.loads((DATA / "alerts.json").read_text())]
        self.events = json.loads((DATA / "events.json").read_text())
        self.copilot = SOCCopilot(ROOT / "knowledge_base")

    def list_alerts(self) -> list[Alert]:
        return self.alerts

    def investigate(self, alert_id: str) -> InvestigationResult:
        alert = next(a for a in self.alerts if a.alert_id == alert_id)
        events = [e for e in self.events if e["alert_id"] == alert_id]
        result = self.copilot.run(alert, events)
        self.save(result)
        return result

    def get(self, incident_id: str) -> InvestigationResult:
        return InvestigationResult.model_validate_json((RESULTS / f"{incident_id}.json").read_text())

    def approve(self, incident_id: str, request: ApprovalRequest) -> InvestigationResult:
        result = self.get(incident_id)
        result.analyst_approved = request.approved
        result.analyst_notes = f"{request.analyst}: {request.notes}".strip()
        result.status = "approved_for_defensive_action" if request.approved else "analyst_rejected_actions"
        self.save(result)
        return result

    @staticmethod
    def save(result: InvestigationResult) -> None:
        (RESULTS / f"{result.incident_id}.json").write_text(result.model_dump_json(indent=2), encoding="utf-8")

