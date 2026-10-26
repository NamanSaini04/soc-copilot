"""Public-facing synthetic SOC demo: no external side effects, per-session state."""
from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.models import ApprovalRequest
from app.service import IncidentService
from reports.incident_pdf import build_incident_pdf

st.set_page_config(
    page_title="Cybersecurity SOC Copilot | Defensive Demo",
    page_icon="🛡️",
    layout="wide",
)

# Do NOT cache this service globally. Every visitor gets their own in-memory
# investigation records and approval history; no data is persisted on the host.
if "soc_demo_service" not in st.session_state:
    st.session_state["soc_demo_service"] = IncidentService(persist=False)
service = st.session_state["soc_demo_service"]

st.title("🛡️ Cybersecurity SOC Copilot")
st.caption("Interactive defensive demo · 3 synthetic security alerts · No real-world systems or live threat intelligence")
st.info(
    "This is a portfolio laboratory, not an operational SOC. "
    "All alerts and intelligence are synthetic. Analyst approvals only update the demo record; "
    "they never reset passwords, isolate hosts, block indicators, or contact external services."
)

queue_tab, investigation_tab, scope_tab = st.tabs(
    ["📋 Alert queue", "🔍 Investigation workspace", "📐 Methodology and limitations"]
)

alerts = service.list_alerts()
frame = pd.DataFrame([alert.model_dump(mode="json") for alert in alerts])
with queue_tab:
    c1, c2, c3 = st.columns(3)
    c1.metric("Sample alerts", len(frame))
    c2.metric("Affected users", frame["user"].nunique())
    c3.metric("Critical assets (score 5)", int((frame["asset_criticality"] == 5).sum()))
    left, right = st.columns(2)
    left.plotly_chart(
        px.bar(frame.groupby("category", as_index=False).size(), x="category", y="size", title="Alerts by category"),
        width="stretch",
    )
    right.plotly_chart(
        px.histogram(frame, x="asset_criticality", title="Asset criticality"),
        width="stretch",
    )
    st.dataframe(frame[["alert_id", "timestamp", "category", "title", "source", "asset_criticality"]], width="stretch", hide_index=True)

with investigation_tab:
    st.markdown("### Choose an alert to investigate")
    selected = st.selectbox(
        "Available synthetic alerts",
        [alert.alert_id for alert in alerts],
        format_func=lambda alert_id: next(
            f"{a.alert_id} — {a.title}" for a in alerts if a.alert_id == alert_id
        ),
    )
    if st.button("Run investigation", type="primary"):
        st.session_state["active_incident"] = service.investigate(selected).incident_id

    incident_id = st.session_state.get("active_incident")
    result = service.get(incident_id) if incident_id else None

    if not result:
        st.info("Select an alert and choose **Run investigation** to view its evidence, recommendations and reports.")

    if result:
        st.subheader(f"{result.incident_id}: {result.alert.title}")
        a, b, c, d = st.columns(4)
        a.metric("Severity", result.severity.value.upper())
        b.metric("Risk", f"{result.risk_score}/100")
        c.metric("Confidence", f"{result.confidence:.0%}")
        d.metric("Review status", "Approved" if result.analyst_approved else ("Rejected" if result.review_history else "Pending"))
        st.caption(f"Status: {result.status} · {result.escalation}")

        st.markdown("#### Evidence and timeline")
        st.dataframe(
            pd.DataFrame([e.model_dump(mode="json") for e in result.evidence]),
            width="stretch",
            hide_index=True,
        )
        with st.expander("Incident timeline and observed indicators"):
            st.dataframe(pd.DataFrame(result.timeline), width="stretch", hide_index=True)
            st.write("Indicators extracted from provided fixtures:", ", ".join(result.iocs) or "None")

        st.markdown("#### Hypotheses — not confirmed facts")
        for hypothesis in result.hypotheses:
            st.warning(hypothesis)

        knowledge_col, mapping_col = st.columns(2)
        with knowledge_col:
            st.markdown("#### Playbook citations")
            if result.citations:
                st.dataframe(pd.DataFrame([c.model_dump() for c in result.citations]), width="stretch", hide_index=True)
            else:
                st.caption("No retrieved knowledge chunk met the minimum relevance score.")
        with mapping_col:
            st.markdown("#### Provisional MITRE ATT&CK mapping")
            if result.mitre_attack:
                st.dataframe(pd.DataFrame(result.mitre_attack), width="stretch", hide_index=True)
            else:
                st.caption("Insufficient evidence for an ATT&CK mapping.")

        st.markdown("#### Proposed defensive recommendations (never executed)")
        st.dataframe(
            pd.DataFrame([r.model_dump() for r in result.recommendations]),
            width="stretch", hide_index=True,
        )

        with st.form("analyst_review"):
            analyst = st.text_input("Reviewer name", max_chars=80)
            notes = st.text_area("Review notes", max_chars=2000, help="Demo only; do not enter personal or confidential data.")
            decision = st.radio("Decision", ["Approve recommendations for review", "Reject recommendations"], horizontal=True)
            submitted = st.form_submit_button("Record review decision", type="primary")
        if submitted:
            try:
                request = ApprovalRequest(analyst=analyst, notes=notes, approved=decision.startswith("Approve"))
            except ValueError:
                st.error("Please enter a reviewer name of at least 2 characters.")
            else:
                service.approve(result.incident_id, request)
                st.success("Decision recorded in this browser session only. No external security action was performed.")
                st.rerun()

        if result.review_history:
            st.markdown("#### Review audit history (session-only)")
            st.dataframe(
                pd.DataFrame([event.model_dump(mode="json") for event in result.review_history]),
                width="stretch", hide_index=True,
            )

        with st.expander("Auditable agent trace"):
            st.dataframe(pd.DataFrame(result.agent_trace), width="stretch", hide_index=True)

        st.markdown("#### Download reproducible incident evidence")
        with TemporaryDirectory(prefix="soc-demo-") as temp_dir:
            pdf_path = build_incident_pdf(result, output_dir=Path(temp_dir))
            pdf_bytes = pdf_path.read_bytes()
        col_a, col_b = st.columns(2)
        col_a.download_button("📄 Download incident PDF", pdf_bytes, file_name=f"{result.incident_id}-report.pdf", mime="application/pdf")
        col_b.download_button("🧾 Download incident JSON", result.model_dump_json(indent=2), file_name=f"{result.incident_id}.json", mime="application/json")

with scope_tab:
    st.markdown("### What this project demonstrates")
    st.markdown(
        "1. **Triage:** transparent rule-based severity baseline, not a learned threat-classifier.\n"
        "2. **Investigation:** correlate supplied synthetic events and keep evidence separate from hypotheses.\n"
        "3. **Knowledge retrieval:** local TF-IDF playbook search with chunk IDs and citation scores.\n"
        "4. **Risk and ATT&CK:** deterministic risk calculation and explicitly provisional technique mapping.\n"
        "5. **Human review:** record proposed actions as approved or rejected; no operational execution.\n"
        "6. **Reporting:** export the incident as PDF and structured JSON."
    )
    st.warning(
        "Evaluation currently has only three labelled synthetic fixtures; that is a functional smoke test, "
        "not a reliable detection accuracy claim. There is no real SIEM integration, authentication system, "
        "organization-level multi-user store, or live response execution."
    )
    st.markdown("[Read the full repository and implementation](https://github.com/NamanSaini04/soc-copilot)")
