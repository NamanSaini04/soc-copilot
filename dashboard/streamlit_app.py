import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.models import ApprovalRequest
from app.service import IncidentService
from reports.incident_pdf import build_incident_pdf

st.set_page_config(page_title="SOC Copilot", page_icon="🛡️", layout="wide")
service = IncidentService()
st.title("Cybersecurity SOC Copilot")
st.caption("Defensive portfolio environment - synthetic data - analyst approval required")

alerts = service.list_alerts()
frame = pd.DataFrame([a.model_dump(mode="json") for a in alerts])
c1, c2, c3 = st.columns(3)
c1.metric("Total alerts", len(frame)); c2.metric("Affected users", frame.user.nunique()); c3.metric("Critical assets", int((frame.asset_criticality == 5).sum()))
left, right = st.columns(2)
left.plotly_chart(px.bar(frame.groupby("category", as_index=False).size(), x="category", y="size", title="Alerts by category"), use_container_width=True)
right.plotly_chart(px.histogram(frame, x="asset_criticality", title="Asset criticality distribution"), use_container_width=True)

selected = st.selectbox("Select alert", [a.alert_id for a in alerts])
if st.button("Run investigation", type="primary"):
    st.session_state["result"] = service.investigate(selected)

result = st.session_state.get("result")
if result:
    st.subheader(f"{result.incident_id}: {result.alert.title}")
    a, b, c = st.columns(3); a.metric("Severity", result.severity.value.upper()); b.metric("Risk", f"{result.risk_score}/100"); c.metric("Confidence", f"{result.confidence:.0%}")
    st.markdown("#### Confirmed evidence")
    st.dataframe(pd.DataFrame([e.model_dump(mode="json") for e in result.evidence]), use_container_width=True)
    st.markdown("#### Hypotheses (not confirmed)"); st.warning("\n".join(f"- {h}" for h in result.hypotheses))
    st.markdown("#### Knowledge citations"); st.dataframe(pd.DataFrame([x.model_dump() for x in result.citations]), use_container_width=True)
    st.markdown("#### Proposed defensive actions"); st.dataframe(pd.DataFrame([x.model_dump() for x in result.recommendations]), use_container_width=True)
    analyst = st.text_input("Analyst name")
    notes = st.text_area("Analyst notes")
    ca, cb = st.columns(2)
    if ca.button("Approve recommendations", disabled=not analyst):
        st.session_state["result"] = service.approve(result.incident_id, ApprovalRequest(analyst=analyst, approved=True, notes=notes)); st.rerun()
    if cb.button("Reject recommendations", disabled=not analyst):
        st.session_state["result"] = service.approve(result.incident_id, ApprovalRequest(analyst=analyst, approved=False, notes=notes)); st.rerun()
    pdf = build_incident_pdf(st.session_state["result"])
    st.download_button("Download incident PDF", pdf.read_bytes(), file_name=pdf.name, mime="application/pdf")

