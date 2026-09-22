from datetime import datetime

from app.models import Alert, Evidence


def investigate(alert: Alert, related_events: list[dict]) -> dict:
    evidence = [
        Evidence(
            evidence_id=f"EV-{alert.alert_id}-001",
            source=alert.source,
            observed_at=alert.timestamp,
            statement=alert.description,
            confidence=0.95,
            provenance=f"uploaded_alert:{alert.alert_id}",
        )
    ]
    timeline = [{"timestamp": alert.timestamp.isoformat(), "event": alert.title, "source": alert.source}]
    users = {alert.user} if alert.user else set()
    systems = {alert.device} if alert.device else set()
    for index, event in enumerate(related_events, 2):
        observed = datetime.fromisoformat(event["timestamp"])
        evidence.append(Evidence(
            evidence_id=f"EV-{alert.alert_id}-{index:03d}", source=event["source"], observed_at=observed,
            statement=event["message"], confidence=float(event.get("confidence", 0.9)),
            provenance=f"synthetic_log:{event.get('event_id', index)}"))
        timeline.append({"timestamp": observed.isoformat(), "event": event["message"], "source": event["source"]})
        if event.get("user"): users.add(event["user"])
        if event.get("device"): systems.add(event["device"])
    timeline.sort(key=lambda row: row["timestamp"])
    hypotheses = []
    if alert.category == "authentication":
        hypotheses.append("The account may be compromised; confirmation requires identity-provider and endpoint evidence.")
    elif alert.category == "phishing":
        hypotheses.append("The message may be an initial-access attempt; delivery and click telemetry must be verified.")
    else:
        hypotheses.append("Observed activity may be malicious or benign; additional correlated telemetry is required.")
    return {"evidence": evidence, "timeline": timeline, "affected_users": sorted(users),
            "affected_systems": sorted(systems), "hypotheses": hypotheses}
