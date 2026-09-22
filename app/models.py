from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Alert(BaseModel):
    alert_id: str
    timestamp: datetime
    source: str
    category: str
    title: str
    user: str | None = None
    device: str | None = None
    src_ip: str | None = None
    indicator: str | None = None
    event_count: int = 1
    asset_criticality: int = Field(3, ge=1, le=5)
    description: str


class Evidence(BaseModel):
    evidence_id: str
    source: str
    observed_at: datetime
    statement: str
    confidence: float = Field(ge=0, le=1)
    provenance: str


class Citation(BaseModel):
    source_id: str
    title: str
    section: str
    score: float


class Recommendation(BaseModel):
    action: str
    rationale: str
    priority: Literal["low", "medium", "high"]
    requires_approval: bool = True


class InvestigationResult(BaseModel):
    incident_id: str
    alert: Alert
    severity: Severity
    risk_score: int = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    status: str = "awaiting_analyst_review"
    alert_type: str
    evidence: list[Evidence]
    hypotheses: list[str]
    timeline: list[dict[str, Any]]
    affected_users: list[str]
    affected_systems: list[str]
    iocs: list[str]
    mitre_attack: list[dict[str, str]]
    knowledge_context: list[str]
    citations: list[Citation]
    recommendations: list[Recommendation]
    escalation: str
    agent_trace: list[dict[str, Any]]
    analyst_approved: bool = False
    analyst_notes: str = ""


class ApprovalRequest(BaseModel):
    analyst: str
    approved: bool
    notes: str = ""

