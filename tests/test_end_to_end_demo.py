"""End-to-end demo acceptance tests: no real security actions are executed."""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.models import ApprovalRequest
from app.service import IncidentService
from reports.incident_pdf import build_incident_pdf


def test_investigate_review_reopen_export_in_an_isolated_session(tmp_path: Path):
    service = IncidentService(persist=False, results_dir=tmp_path)
    assert len(service.list_alerts()) == 3
    investigation = service.investigate("ALT-001")
    assert investigation.incident_id == "INC-001"
    assert investigation.evidence
    assert investigation.citations
    assert investigation.recommendations
    assert all(item.requires_approval for item in investigation.recommendations)
    assert not list(tmp_path.glob("*")), "In-memory demo must not write shared incident files"

    approved = service.approve(
        investigation.incident_id,
        ApprovalRequest(analyst="Demo Reviewer", notes="Evidence reviewed; no actions executed", approved=True),
    )
    assert approved.analyst_approved is True
    assert approved.status == "recommendations_reviewed_approved"
    assert len(approved.review_history) == 1
    assert approved.review_history[0].analyst == "Demo Reviewer"

    # Re-running a reviewed alert must not silently erase its decision.
    reopened = service.investigate("ALT-001")
    assert reopened.review_history == approved.review_history

    rejected = service.approve(
        approved.incident_id,
        ApprovalRequest(analyst="Second Reviewer", notes="Need additional telemetry", approved=False),
    )
    assert rejected.analyst_approved is False
    assert rejected.status == "recommendations_rejected"
    assert [row.approved for row in rejected.review_history] == [True, False]

    pdf = build_incident_pdf(rejected, output_dir=tmp_path)
    assert pdf.is_file() and pdf.read_bytes().startswith(b"%PDF")
    assert rejected.model_dump_json(indent=2).startswith("{")
    assert len(service.list_incidents()) == 1


def test_sessions_are_isolated():
    a = IncidentService(persist=False)
    b = IncidentService(persist=False)
    result = a.investigate("ALT-002")
    a.approve(result.incident_id, ApprovalRequest(analyst="Reviewer A", approved=True))
    with pytest.raises(FileNotFoundError):
        b.get(result.incident_id)
    result_b = b.investigate("ALT-002")
    assert not result_b.analyst_approved
    assert result_b.review_history == []


def test_persistent_mode_can_reopen_review_after_restart(tmp_path: Path):
    first = IncidentService(persist=True, results_dir=tmp_path)
    result = first.investigate("ALT-003")
    first.approve(result.incident_id, ApprovalRequest(analyst="Reviewer B", approved=True))
    second = IncidentService(persist=True, results_dir=tmp_path)
    reopened = second.get(result.incident_id)
    assert reopened.review_history[0].analyst == "Reviewer B"
    assert reopened.analyst_approved is True
    assert second.investigate("ALT-003").analyst_approved is True


@pytest.mark.parametrize("incident_id", ["../secrets", "INC-../../secrets", "/tmp/report", "INC-1/other", "INC-"])
def test_invalid_incident_ids_never_read_paths(tmp_path: Path, incident_id: str):
    service = IncidentService(persist=True, results_dir=tmp_path)
    with pytest.raises(ValueError, match="Invalid incident identifier"):
        service.get(incident_id)


def test_blank_reviewer_is_rejected():
    with pytest.raises(ValidationError):
        ApprovalRequest(analyst=" ", approved=True)


def test_api_denies_unauthorized_access_and_never_executes_actions(monkeypatch):
    from app import api

    monkeypatch.setattr(api, "service", IncidentService(persist=False))
    monkeypatch.delenv("SOC_API_TOKEN", raising=False)
    client = TestClient(api.app)
    assert client.get("/health").status_code == 200
    assert client.get("/alerts").status_code == 503
    assert client.post("/investigations/ALT-001").status_code == 503

    monkeypatch.setenv("SOC_API_TOKEN", "a-local-test-token-not-for-deployment")
    assert client.get("/alerts").status_code == 401
    headers = {"X-SOC-Demo-Token": "a-local-test-token-not-for-deployment"}
    assert len(client.get("/alerts", headers=headers).json()) == 3
    assert client.post("/investigations/DOES-NOT-EXIST", headers=headers).status_code == 404
    investigation = client.post("/investigations/ALT-001", headers=headers)
    assert investigation.status_code == 200
    incident_id = investigation.json()["incident_id"]
    assert client.get(f"/incidents/{incident_id}", headers=headers).status_code == 200
    assert client.get("/incidents/../secrets", headers=headers).status_code in (400, 404)

    approved = client.post(
        f"/incidents/{incident_id}/approval",
        headers=headers,
        json={"analyst": "Demo Reviewer", "approved": True, "notes": "For review only"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "recommendations_reviewed_approved"
    assert approved.json()["review_history"]
    assert len(client.get("/incidents", headers=headers).json()) == 1
    assert client.get(f"/incidents/{incident_id}/report", headers=headers).content.startswith(b"%PDF")
