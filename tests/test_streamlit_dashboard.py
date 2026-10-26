"""Headless Streamlit smoke test: exercise the actual dashboard script."""
from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_public_demo_dashboard_can_investigate_fixture_alert():
    app_path = Path(__file__).resolve().parents[1] / "dashboard" / "streamlit_app.py"
    at = AppTest.from_file(str(app_path), default_timeout=30).run()
    assert not at.exception, "The initial Streamlit dashboard must render"
    assert len(at.tabs) == 3
    assert any("Run investigation" == button.label for button in at.button)

    investigate_button = next(button for button in at.button if button.label == "Run investigation")
    investigate_button.click().run()
    assert not at.exception, "The dashboard investigation must render"
    assert at.session_state["active_incident"] == "INC-001"
    result = at.session_state["soc_demo_service"].get("INC-001")
    assert result.evidence and result.recommendations
    assert not result.analyst_approved
