"""Headless tests for the real three-case Streamlit investigation demo."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parents[1] / "dashboard" / "streamlit_app.py"


@pytest.mark.parametrize("alert_id", ["ALT-001", "ALT-002", "ALT-003"])
def test_all_synthetic_alerts_investigate_and_export(alert_id, tmp_path):
    """Every bundled scenario should show findings and support PDF/JSON export."""
    from reports.incident_pdf import build_incident_pdf

    at = AppTest.from_file(str(APP_PATH), default_timeout=30).run()
    assert not at.exception, "Dashboard must open before an investigation"
    assert len(at.tabs) == 3
    assert "Run investigation" in [b.label for b in at.button]

    at.selectbox[0].select(alert_id).run()
    assert not at.exception
    next(b for b in at.button if b.label == "Run investigation").click().run()
    assert not at.exception, f"Dashboard failed to show investigation for {alert_id}"

    result = at.session_state["soc_demo_service"].get(
        at.session_state["active_incident"]
    )
    assert result.alert.alert_id == alert_id
    assert result.evidence
    assert result.timeline
    assert result.agent_trace
    assert result.recommendations
    assert all(action.requires_approval for action in result.recommendations)
    assert not result.analyst_approved

    # AppTest does not execute browser download buttons; exercise their exact
    # underlying PDF/JSON generation functions and validate readable output.
    pdf_path = build_incident_pdf(result, output_dir=tmp_path)
    assert pdf_path.read_bytes().startswith(b"%PDF-")
    from pypdf import PdfReader

    pdf_text = "\n".join(page.extract_text() or "" for page in PdfReader(pdf_path).pages)
    assert result.incident_id in pdf_text
    assert "SOC INCIDENT INVESTIGATION REPORT" in " ".join(pdf_text.split())

    exported = result.model_validate_json(result.model_dump_json(indent=2))
    assert exported.alert.alert_id == alert_id
    assert exported.evidence == result.evidence


@pytest.mark.parametrize("decision,expected", [
    ("Approve recommendations for review", True),
    ("Reject recommendations", False),
])
def test_analyst_can_record_either_review_decision(decision, expected):
    at = AppTest.from_file(str(APP_PATH), default_timeout=30).run()
    next(b for b in at.button if b.label == "Run investigation").click().run()
    assert not at.exception
    assert "Record review decision" in [b.label for b in at.button]
    at.text_input[0].set_value("Portfolio Reviewer")
    at.radio[0].set_value(decision)
    next(b for b in at.button if b.label == "Record review decision").click().run()
    assert not at.exception
    record = at.session_state["soc_demo_service"].get("INC-001")
    assert record.analyst_approved is expected
    assert len(record.review_history) == 1
    assert record.review_history[0].analyst == "Portfolio Reviewer"


def test_sessions_isolate_investigations():
    first = AppTest.from_file(str(APP_PATH), default_timeout=30).run()
    second = AppTest.from_file(str(APP_PATH), default_timeout=30).run()
    next(b for b in first.button if b.label == "Run investigation").click().run()
    assert not first.exception
    assert not second.exception
    assert first.session_state["active_incident"] == "INC-001"
    assert "active_incident" not in second.session_state
