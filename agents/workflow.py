from datetime import UTC, datetime
from pathlib import Path

from agents.investigation_agent import investigate
from agents.response_agent import recommend
from agents.risk_agent import assess
from agents.threat_intel_agent import extract_iocs, lookup, map_attack
from agents.triage_agent import triage
from app.models import Alert, Citation, InvestigationResult
from rag.ingestion import ingest_directory
from rag.retriever import LocalRetriever


class SOCCopilot:
    def __init__(self, knowledge_dir: str | Path):
        self.retriever = LocalRetriever(ingest_directory(knowledge_dir))

    def run(self, alert: Alert, related_events: list[dict]) -> InvestigationResult:
        trace = []
        def record(agent: str, summary: str, inputs: list[str]):
            trace.append({"agent": agent, "timestamp": datetime.now(UTC).isoformat(), "summary": summary, "inputs": inputs})

        t = triage(alert); record("triage_agent", f"{t['severity'].value} / {t['preliminary_score']}", [alert.alert_id])
        inv = investigate(alert, related_events); record("investigation_agent", f"Correlated {len(inv['evidence'])} evidence items", [alert.alert_id])
        iocs = extract_iocs(alert.src_ip or "", alert.indicator or "", alert.description, *[e.statement for e in inv["evidence"]])
        intel = lookup(iocs); record("threat_intel_agent", f"{len(intel)} approved demo-intel matches", iocs)
        query = f"{t['alert_type']} {alert.title} {alert.description}"
        retrieved = self.retriever.search(query); record("rag_agent", f"Retrieved {len(retrieved)} knowledge chunks", [r["source_id"] for r in retrieved])
        risk = assess(alert, t["preliminary_score"], len(inv["evidence"]), len(intel)); record("risk_agent", f"Risk {risk['risk_score']}/100", [e.evidence_id for e in inv["evidence"]])
        actions = recommend(t["alert_type"], risk["severity"]); record("response_agent", f"Proposed {len(actions)} approval-gated actions", [])
        mappings = map_attack(t["alert_type"], " ".join(e.statement for e in inv["evidence"])); record("mitre_mapper", f"Mapped {len(mappings)} provisional techniques", [])
        citations = [Citation(source_id=r["source_id"], title=r["title"], section=r["section"], score=r["score"]) for r in retrieved]
        return InvestigationResult(
            incident_id=f"INC-{alert.alert_id.split('-')[-1]}", alert=alert, severity=risk["severity"], risk_score=risk["risk_score"],
            confidence=risk["confidence"], alert_type=t["alert_type"], evidence=inv["evidence"], hypotheses=inv["hypotheses"],
            timeline=inv["timeline"], affected_users=inv["affected_users"], affected_systems=inv["affected_systems"], iocs=iocs,
            mitre_attack=mappings, knowledge_context=[r["text"] for r in retrieved], citations=citations,
            recommendations=actions, escalation=risk["escalation"], agent_trace=trace)

