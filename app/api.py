"""Local-only API for a defensive SOC demonstration.

Set SOC_API_TOKEN explicitly; never place it in source or expose this API
on the public internet without real identity, authorization and rate limits.
"""
import hmac
import os

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse

from app.models import ApprovalRequest, InvestigationResult
from app.service import IncidentService
from reports.incident_pdf import build_incident_pdf

app = FastAPI(title="Cybersecurity SOC Copilot", version="0.2.0")
service = IncidentService()


def require_demo_token(x_soc_demo_token: str | None = Header(default=None)) -> None:
    expected = os.getenv("SOC_API_TOKEN", "")
    if not expected:
        raise HTTPException(status_code=503, detail="API unavailable: SOC_API_TOKEN must be configured")
    if not x_soc_demo_token or not hmac.compare_digest(x_soc_demo_token, expected):
        raise HTTPException(status_code=401, detail="Invalid demo API token")


@app.get("/health")
def health():
    return {"status": "ok", "mode": "defensive-demo", "api_auth_configured": bool(os.getenv("SOC_API_TOKEN"))}


@app.get("/alerts", dependencies=[Depends(require_demo_token)])
def alerts():
    return service.list_alerts()


@app.get("/incidents", response_model=list[InvestigationResult], dependencies=[Depends(require_demo_token)])
def incidents():
    return service.list_incidents()


@app.get("/incidents/{incident_id}", response_model=InvestigationResult, dependencies=[Depends(require_demo_token)])
def read_incident(incident_id: str):
    try:
        return service.get(incident_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Incident not found") from exc


@app.post("/investigations/{alert_id}", response_model=InvestigationResult, dependencies=[Depends(require_demo_token)])
def investigate(alert_id: str):
    try:
        return service.investigate(alert_id)
    except StopIteration as exc:
        raise HTTPException(status_code=404, detail="Alert not found") from exc


@app.post("/incidents/{incident_id}/approval", response_model=InvestigationResult, dependencies=[Depends(require_demo_token)])
def approve(incident_id: str, request: ApprovalRequest):
    try:
        return service.approve(incident_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Incident not found") from exc


@app.get("/incidents/{incident_id}/report", dependencies=[Depends(require_demo_token)])
def incident_report(incident_id: str):
    try:
        result = service.get(incident_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Incident not found") from exc
    path = build_incident_pdf(result)
    return FileResponse(path, filename=path.name, media_type="application/pdf")
