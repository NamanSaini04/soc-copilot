from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models import InvestigationResult

ROOT = Path(__file__).resolve().parents[1]


def _footer(canvas, doc):
    canvas.saveState(); canvas.setFont("Helvetica", 8); canvas.setFillColor(colors.HexColor("#64748B"))
    canvas.drawString(20 * mm, 12 * mm, "Cybersecurity SOC Copilot - Defensive use only")
    canvas.drawRightString(190 * mm, 12 * mm, f"Page {doc.page}"); canvas.restoreState()


def build_incident_pdf(result: InvestigationResult, output_dir: Path | None = None) -> Path:
    output_dir = output_dir or ROOT / "reports" / "incidents"
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"SOC_Incident_Report_{result.incident_id}.pdf"
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleWhite", parent=styles["Title"], textColor=colors.white, alignment=TA_CENTER, fontSize=24, leading=29))
    styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=8.5, leading=11))
    doc = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=18*mm, bottomMargin=20*mm)
    story = [Table([[Paragraph("SOC INCIDENT INVESTIGATION REPORT", styles["TitleWhite"])]], colWidths=[170*mm], rowHeights=[35*mm], style=TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#0F2747")),("VALIGN",(0,0),(-1,-1),"MIDDLE")])), Spacer(1,8*mm)]
    meta = [["Incident", result.incident_id], ["Alert", result.alert.alert_id], ["Date/time", result.alert.timestamp.isoformat()], ["Severity", result.severity.value.upper()], ["Risk / confidence", f"{result.risk_score}/100 / {result.confidence:.0%}"], ["Status", result.status], ["Analyst approval", "Approved" if result.analyst_approved else "Not approved"]]
    story += [Table(meta, colWidths=[42*mm,128*mm], style=TableStyle([("BACKGROUND",(0,0),(0,-1),colors.HexColor("#E8EEF6")),("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#94A3B8")),("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),("PADDING",(0,0),(-1,-1),6)])), Spacer(1,6*mm)]
    story += [Paragraph("Executive summary", styles["Heading1"]), Paragraph(f"The SOC Copilot correlated {len(result.evidence)} evidence items for {result.alert.title}. The assessed risk is {result.risk_score}/100 ({result.severity.value}) with {result.confidence:.0%} confidence. Operational actions remain subject to human authorization.", styles["BodyText"])]
    sections = [
        ("Confirmed evidence", [[e.evidence_id, e.source, e.observed_at.isoformat(), e.statement] for e in result.evidence], [24,30,40,76]),
        ("Incident timeline", [[x["timestamp"], x["source"], x["event"]] for x in result.timeline], [42,34,94]),
        ("Indicators of compromise", [[ioc] for ioc in result.iocs] or [["None confirmed"]], [170]),
        ("MITRE ATT&CK mapping", [[m["technique_id"], m["name"], m["basis"]] for m in result.mitre_attack] or [["None", "Insufficient evidence", "No mapping asserted"]], [28,42,100]),
        ("Recommended defensive actions", [[r.priority, r.action, r.rationale, "Yes" if r.requires_approval else "No"] for r in result.recommendations], [22,47,82,19]),
    ]
    for heading, rows, widths in sections:
        story += [Spacer(1,4*mm), Paragraph(heading, styles["Heading2"]), Table([[Paragraph(str(c), styles["Small"]) for c in row] for row in rows], colWidths=[w*mm for w in widths], repeatRows=0, style=TableStyle([("GRID",(0,0),(-1,-1),0.25,colors.HexColor("#CBD5E1")),("VALIGN",(0,0),(-1,-1),"TOP"),("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.white,colors.HexColor("#F8FAFC")]),("PADDING",(0,0),(-1,-1),4)]))]
    story += [Spacer(1, 6*mm), Paragraph("Hypotheses and uncertainty", styles["Heading1"])] + [Paragraph(f"- {h}", styles["BodyText"]) for h in result.hypotheses]
    story += [Paragraph("Affected entities", styles["Heading1"]), Paragraph(f"Systems: {', '.join(result.affected_systems) or 'None confirmed'}<br/>Users: {', '.join(result.affected_users) or 'None confirmed'}", styles["BodyText"]), Paragraph("Knowledge citations", styles["Heading1"])]
    story += [Paragraph(f"[{c.source_id}] {c.title} - {c.section} (retrieval score {c.score:.3f})", styles["BodyText"]) for c in result.citations]
    story += [Paragraph("Agent and tool trace", styles["Heading1"]), Table([[x["timestamp"],x["agent"],x["summary"]] for x in result.agent_trace], colWidths=[55*mm,38*mm,77*mm], style=TableStyle([("GRID",(0,0),(-1,-1),0.25,colors.grey),("FONTSIZE",(0,0),(-1,-1),7),("VALIGN",(0,0),(-1,-1),"TOP")]))]
    story += [Paragraph("Analyst notes", styles["Heading1"]), Paragraph(result.analyst_notes or "No analyst notes recorded.", styles["BodyText"])]
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return path
