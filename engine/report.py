from __future__ import annotations

from io import BytesIO
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def build_pdf(case: dict) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm)
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph("SIH26106 Forensic Email Intelligence Report", styles["Title"]))
    story.append(Paragraph("AICTE Cyber Security Cell — prototype (simulation / lab samples)", styles["Normal"]))
    story.append(Spacer(1, 8))
    tclass = case.get("threat_class") or case.get("label")
    story.append(
        Paragraph(
            f"<b>Threat class:</b> {tclass} &nbsp; <b>Score:</b> {case.get('score')}/100",
            styles["Heading2"],
        )
    )
    story.append(Paragraph(f"<b>Subject:</b> {case.get('subject') or '(none)'}", styles["Normal"]))
    story.append(Paragraph(f"<b>From:</b> {case.get('from_addr')}", styles["Normal"]))
    story.append(Paragraph(f"<b>Analyzed:</b> {case.get('analyzed_at')}", styles["Normal"]))
    story.append(Spacer(1, 8))
    auth = case.get("auth") or {}
    story.append(Paragraph(f"SPF={auth.get('spf')} &nbsp; DKIM={auth.get('dkim')} &nbsp; DMARC={auth.get('dmarc')}", styles["Normal"]))
    story.append(Spacer(1, 8))
    cust = case.get("custody") or {}
    if cust:
        story.append(Paragraph("Chain of custody (prototype)", styles["Heading2"]))
        story.append(Paragraph(f"{cust.get('algorithm')}: {cust.get('sha256')}", styles["Normal"]))
        story.append(Paragraph(f"Bytes: {cust.get('byte_length')} &nbsp; Hashed: {cust.get('hashed_at')}", styles["Normal"]))
        story.append(Paragraph(cust.get("note") or "", styles["Italic"]))
        story.append(Spacer(1, 8))
    di = case.get("domain_intel") or {}
    if di:
        story.append(Paragraph("Domain intelligence (public DNS)", styles["Heading2"]))
        story.append(Paragraph(f"From domain: {di.get('domain')}", styles["Normal"]))
        story.append(Paragraph("MX: " + (", ".join(di.get("mx_records") or []) or "(none)"), styles["Normal"]))
        story.append(Paragraph("A: " + (", ".join(di.get("a_records") or []) or "(none)"), styles["Normal"]))
        for n in di.get("notes") or []:
            story.append(Paragraph(n, styles["Normal"]))
        story.append(Spacer(1, 8))
    hi = case.get("header_intel") or {}
    anoms = hi.get("anomalies") or []
    if anoms:
        story.append(Paragraph("Header anomalies", styles["Heading2"]))
        for a in anoms:
            story.append(Paragraph(a.get("detail") or a.get("code") or "", styles["Normal"]))
        story.append(Spacer(1, 8))
    story.append(Paragraph("Explainability (weighted features, not SHAP/neural net)", styles["Heading2"]))
    exp = case.get("explain") or {}
    story.append(Paragraph(exp.get("note") or "", styles["Italic"]))
    if exp.get("hitl_review"):
        story.append(Paragraph("HITL: " + (exp.get("hitl_reason") or "Needs human review"), styles["Normal"]))
    story.append(Paragraph("Intents: " + ", ".join(exp.get("intents") or []) or "none", styles["Normal"]))
    story.append(Spacer(1, 8))
    for r in case.get("reasons") or []:
        story.append(Paragraph(f"+{r['points']} [{r['code']}] {r['detail']}", styles["Normal"]))
    story.append(Spacer(1, 8))
    attr = case.get("attribution") or {}
    story.append(Paragraph("Attribution (infrastructure only)", styles["Heading2"]))
    story.append(Paragraph(attr.get("summary", ""), styles["Normal"]))
    story.append(Paragraph(f"Origin IP: {attr.get('origin_ip') or 'n/a'}", styles["Normal"]))
    story.append(Paragraph(f"Pattern: {attr.get('likely_pattern')} (confidence {attr.get('confidence')})", styles["Normal"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Received path (public IPs)", styles["Heading2"]))
    for p in case.get("geo_hops") or []:
        story.append(
            Paragraph(
                f"{p.get('ip')} — {p.get('city')} {p.get('country')} — {p.get('isp')} [{p.get('role')} / {p.get('threat_tag')}]",
                styles["Normal"],
            )
        )
    story.append(Spacer(1, 12))
    story.append(
        Paragraph(
            "This report is a decision-support artefact for institutional SOC / admin review. "
            "It does not identify a natural person and is not a court-ready attribution without ISP legal process.",
            styles["Italic"],
        )
    )
    doc.build(story)
    return buf.getvalue()


def write_pdf(case: dict, path: Path) -> None:
    path.write_bytes(build_pdf(case))
