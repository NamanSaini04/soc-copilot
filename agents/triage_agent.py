from app.models import Alert, Severity

KEYWORDS = {
    "phishing": ("phishing", "credential", "malicious link"),
    "authentication": ("login", "authentication", "password", "mfa"),
    "malware": ("malware", "ransomware", "trojan", "hash"),
    "network": ("network", "beacon", "dns", "connection"),
    "endpoint": ("endpoint", "process", "powershell", "edr"),
}


def triage(alert: Alert) -> dict:
    text = f"{alert.category} {alert.title} {alert.description}".lower()
    alert_type = next((k for k, words in KEYWORDS.items() if any(w in text for w in words)), "other")
    score = min(100, 12 + alert.event_count * 3 + alert.asset_criticality * 8)
    if any(w in text for w in ("admin", "ransomware", "malware", "impossible travel")):
        score += 18
    if alert.indicator:
        score += 7
    score = min(score, 100)
    severity = Severity.critical if score >= 85 else Severity.high if score >= 65 else Severity.medium if score >= 35 else Severity.low
    return {
        "alert_type": alert_type,
        "preliminary_score": score,
        "severity": severity,
        "requires_investigation": score >= 35,
        "reason": "Rule-based baseline using event volume, asset criticality, indicator presence, and high-risk keywords.",
    }

