from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from app.models import ApprovalRequest, InvestigationResult
from app.service import IncidentService
from reports.incident_pdf import build_incident_pdf

app = FastAPI(title="Cybersecurity SOC Copilot", version="0.1.0")
service = IncidentService()


@app.get("/health")
def health(): return {"status": "ok", "mode": "defensive-demo"}


@app.get("/alerts")
def alerts(): return service.list_alerts()


@app.post("/investigations/{alert_id}", response_model=InvestigationResult)
def investigate(alert_id: str):
    try: return service.investigate(alert_id)
    except StopIteration as exc: raise HTTPException(404, "Alert not found") from exc


@app.post("/incidents/{incident_id}/approval", response_model=InvestigationResult)
def approve(incident_id: str, request: ApprovalRequest):
    try: return service.approve(incident_id, request)
    except FileNotFoundError as exc: raise HTTPException(404, "Incident not found") from exc


@app.get("/incidents/{incident_id}/report")
def incident_report(incident_id: str):
    try: result = service.get(incident_id)
    except FileNotFoundError as exc: raise HTTPException(404, "Incident not found") from exc
    path = build_incident_pdf(result)
    return FileResponse(path, filename=path.name, media_type="application/pdf")

