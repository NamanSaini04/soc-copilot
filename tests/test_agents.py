import json
from pathlib import Path

from agents.triage_agent import triage
from agents.workflow import SOCCopilot
from app.models import Alert

ROOT = Path(__file__).resolve().parents[1]


def alert(alert_id="ALT-001"):
    rows = json.loads((ROOT / "data" / "alerts.json").read_text())
    return Alert.model_validate(next(x for x in rows if x["alert_id"] == alert_id))


def test_triage_is_deterministic():
    assert triage(alert()) == triage(alert())


def test_workflow_separates_evidence_and_hypotheses():
    result = SOCCopilot(ROOT / "knowledge_base").run(alert(), [])
    assert result.evidence and result.hypotheses
    assert all(item.provenance for item in result.evidence)


def test_every_action_requires_approval():
    result = SOCCopilot(ROOT / "knowledge_base").run(alert(), [])
    assert all(item.requires_approval for item in result.recommendations)

