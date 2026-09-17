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
    story.append(Paragraph(f"<b>Classification:</b> {case.get('label')} &nbsp; <b>Score:</b> {case.get('score')}/100", styles["Heading2"]))
    story.append(Paragraph(f"<b>Subject:</b> {case.get('subject') or '(none)'}", styles["Normal"]))
    story.append(Paragraph(f"<b>From:</b> {case.get('from_addr')}", styles["Normal"]))
    story.append(Paragraph(f"<b>Analyzed:</b> {case.get('analyzed_at')}", styles["Normal"]))
    story.append(Spacer(1, 8))
    auth = case.get("auth") or {}
    story.append(Paragraph(f"SPF={auth.get('spf')} &nbsp; DKIM={auth.get('dkim')} &nbsp; DMARC={auth.get('dmarc')}", styles["Normal"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Scoring reasons", styles["Heading2"]))
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
