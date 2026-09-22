from app.models import Recommendation, Severity


def recommend(alert_type: str, severity: Severity) -> list[Recommendation]:
    actions = [Recommendation(action="Collect and preserve relevant logs", rationale="Increase evidentiary confidence before containment.", priority="high")]
    if alert_type == "authentication":
        actions += [
            Recommendation(action="Review account sign-ins and MFA events", rationale="Validate whether access was authorized.", priority="high"),
            Recommendation(action="Reset credentials and revoke sessions", rationale="Contain suspected account compromise after analyst validation.", priority="high"),
        ]
    elif alert_type == "phishing":
        actions += [
            Recommendation(action="Quarantine matching messages", rationale="Limit further user exposure after analyst validates the campaign.", priority="high"),
            Recommendation(action="Block validated malicious indicators", rationale="Prevent repeat access using confirmed indicators only.", priority="medium"),
        ]
    else:
        actions.append(Recommendation(action="Increase endpoint and network monitoring", rationale="Observe for corroborating activity.", priority="medium"))
    if severity in (Severity.high, Severity.critical):
        actions.append(Recommendation(action="Consider host isolation", rationale="Contain potential spread; business impact must be approved.", priority="high"))
    return actions

