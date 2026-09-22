from app.models import Alert, Severity


def assess(alert: Alert, triage_score: int, evidence_count: int, intel_hits: int) -> dict:
    score = min(100, round(0.55 * triage_score + 7 * evidence_count + 10 * intel_hits + 4 * alert.asset_criticality))
    confidence = min(0.95, 0.45 + 0.07 * evidence_count + 0.08 * intel_hits)
    level = Severity.critical if score >= 85 else Severity.high if score >= 65 else Severity.medium if score >= 35 else Severity.low
    escalation = "Escalate to incident response" if score >= 65 else "SOC analyst review" if score >= 35 else "Monitor and close if validated benign"
    return {"risk_score": score, "severity": level, "confidence": round(confidence, 2), "escalation": escalation}

