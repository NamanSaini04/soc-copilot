import ipaddress
import re

DEMO_INTEL = {
    "203.0.113.77": {"reputation": "synthetic-malicious", "confidence": 0.90, "source": "Demo CTI fixture"},
    "198.51.100.42": {"reputation": "synthetic-suspicious", "confidence": 0.70, "source": "Demo CTI fixture"},
    "invoice-review.example": {"reputation": "synthetic-malicious", "confidence": 0.85, "source": "Demo CTI fixture"},
}


def extract_iocs(*texts: str) -> list[str]:
    joined = " ".join(t for t in texts if t)
    candidates = set(re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", joined))
    candidates.update(re.findall(r"\b(?:[a-z0-9-]+\.)+(?:example|com|net|org)\b", joined.lower()))
    valid = []
    for item in candidates:
        try:
            if item[0].isdigit(): ipaddress.ip_address(item)
            valid.append(item)
        except ValueError:
            continue
    return sorted(valid)


def lookup(iocs: list[str]) -> list[dict]:
    return [{"indicator": ioc, **DEMO_INTEL[ioc]} for ioc in iocs if ioc in DEMO_INTEL]


def map_attack(alert_type: str, evidence_text: str) -> list[dict[str, str]]:
    text = evidence_text.lower()
    mappings = []
    if alert_type == "authentication" or "login" in text:
        mappings.append({"technique_id": "T1078", "name": "Valid Accounts", "basis": "Authentication activity observed; mapping is provisional."})
    if "powershell" in text:
        mappings.append({"technique_id": "T1059.001", "name": "PowerShell", "basis": "PowerShell execution explicitly observed."})
    if alert_type == "phishing":
        mappings.append({"technique_id": "T1566", "name": "Phishing", "basis": "Alert categorized as phishing; subtype requires more evidence."})
    return mappings

