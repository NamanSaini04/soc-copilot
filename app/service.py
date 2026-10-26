"""Evidence-preserving incident service for local APIs and isolated demo sessions."""
from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from agents.workflow import SOCCopilot
from app.models import Alert, ApprovalRequest, InvestigationResult, ReviewEvent

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RESULTS = ROOT / "reports" / "incidents" / "json"
INCIDENT_ID = re.compile(r"^INC-[A-Za-z0-9]{1,30}$")


class IncidentService:
    """Local persistence by default; in-memory only for per-browser demo sessions.

    This is NOT a multi-user production store or an authorization boundary.
    """

    def __init__(
        self,
        *,
        persist: bool = True,
        data_dir: Path | None = None,
        results_dir: Path | None = None,
    ):
        self.persist = persist
        self.data_dir = Path(data_dir) if data_dir is not None else DATA
        self.results_dir = Path(results_dir) if results_dir is not None else RESULTS
        if persist:
            self.results_dir.mkdir(parents=True, exist_ok=True)
        self.alerts = [
            Alert.model_validate(row)
            for row in json.loads((self.data_dir / "alerts.json").read_text(encoding="utf-8"))
        ]
        self.events = json.loads((self.data_dir / "events.json").read_text(encoding="utf-8"))
        self._records: dict[str, InvestigationResult] = {}
        self.copilot = SOCCopilot(ROOT / "knowledge_base")

    @staticmethod
    def _safe_id(incident_id: str) -> str:
        if not INCIDENT_ID.fullmatch(incident_id):
            raise ValueError("Invalid incident identifier")
        return incident_id

    def list_alerts(self) -> list[Alert]:
        return [alert.model_copy(deep=True) for alert in self.alerts]

    def list_incidents(self) -> list[InvestigationResult]:
        identifiers = set(self._records)
        if self.persist:
            identifiers.update(
                path.stem for path in self.results_dir.glob("INC-*.json")
                if INCIDENT_ID.fullmatch(path.stem)
            )
        return [self.get(identifier) for identifier in sorted(identifiers)]

    def investigate(self, alert_id: str) -> InvestigationResult:
        alert = next(a for a in self.alerts if a.alert_id == alert_id)
        incident_id = f"INC-{alert.alert_id.split('-')[-1]}"
        # Repeat investigation is idempotent for an already reviewed incident:
        # reopening it must not silently erase an analyst's decision.
        try:
            existing = self.get(incident_id)
            if existing.review_history:
                return existing
        except FileNotFoundError:
            pass
        events = [event for event in self.events if event["alert_id"] == alert_id]
        result = self.copilot.run(alert, events)
        self.save(result)
        return result.model_copy(deep=True)

    def get(self, incident_id: str) -> InvestigationResult:
        self._safe_id(incident_id)
        if incident_id in self._records:
            return self._records[incident_id].model_copy(deep=True)
        if self.persist:
            path = self.results_dir / f"{incident_id}.json"
            if path.is_file():
                result = InvestigationResult.model_validate_json(path.read_text(encoding="utf-8"))
                self._records[incident_id] = result.model_copy(deep=True)
                return result
        raise FileNotFoundError(f"Unknown incident: {incident_id}")

    def approve(self, incident_id: str, request: ApprovalRequest) -> InvestigationResult:
        result = self.get(incident_id)
        result.review_history.append(
            ReviewEvent(
                reviewed_at=datetime.now(UTC),
                analyst=request.analyst,
                approved=request.approved,
                notes=request.notes,
            )
        )
        result.analyst_approved = request.approved
        result.analyst_notes = f"{request.analyst}: {request.notes}".strip()
        # An analyst approves a *recommendation*, never an operational action.
        result.status = "recommendations_reviewed_approved" if request.approved else "recommendations_rejected"
        self.save(result)
        return result.model_copy(deep=True)

    def save(self, result: InvestigationResult) -> None:
        self._safe_id(result.incident_id)
        self._records[result.incident_id] = result.model_copy(deep=True)
        if not self.persist:
            return
        # Atomic replacement prevents half-written JSON on process interruption.
        tmp_name: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self.results_dir,
                prefix=".incident-", suffix=".tmp", delete=False,
            ) as handle:
                tmp_name = handle.name
                handle.write(result.model_dump_json(indent=2))
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, self.results_dir / f"{result.incident_id}.json")
        finally:
            if tmp_name and Path(tmp_name).exists():
                Path(tmp_name).unlink()
