"""Fill official SIH 2026 idea template with MailTrace content. Layout/branding unchanged."""

from copy import deepcopy
from pathlib import Path

from pptx import Presentation
from pptx.oxml.ns import qn
from pptx.util import Pt

SRC = Path(r"C:\Users\prajj\Downloads\SIH2026-IDEA-Presentation-Format.pptx")
DST = Path(r"C:\Users\prajj\Documents\proto.SIH\MailTrace_SIH26106_official.pptx")
TEAM = "prajjwaldubey"


def set_runs_text(paragraph, text: str) -> None:
    if paragraph.runs:
        paragraph.runs[0].text = text
        for run in paragraph.runs[1:]:
            run.text = ""
    else:
        paragraph.text = text


def clone_paragraph(text_frame, source_para):
    new_p = deepcopy(source_para._p)
    text_frame._txBody.append(new_p)
    return text_frame.paragraphs[-1]


def fill_box(shape, lines: list[str], body_idx: int = 0) -> None:
    """Replace paragraphs; extra lines clone the body paragraph style."""
    tf = shape.text_frame
    paras = list(tf.paragraphs)
    if not paras:
        return
    style = paras[min(body_idx, len(paras) - 1)]
    # first write into existing paras
    for i, line in enumerate(lines):
        if i < len(paras):
            set_runs_text(paras[i], line)
        else:
            np = clone_paragraph(tf, style)
            set_runs_text(np, line)
    # blank leftover existing paras
    for j in range(len(lines), len(list(tf.paragraphs))):
        if j < len(paras):
            set_runs_text(paras[j], "")


def shape_by_name(slide, name: str):
    for sh in slide.shapes:
        if sh.name == name:
            return sh
    return None


def oval_team(slide):
    for sh in slide.shapes:
        if sh.has_text_frame and sh.text_frame.text.strip() == "Your Team Name":
            set_runs_text(sh.text_frame.paragraphs[0], TEAM)


def main() -> None:
    prs = Presentation(str(SRC))
    s1 = prs.slides[0]
    s2 = prs.slides[1]
    s3 = prs.slides[2]
    s4 = prs.slides[3]
    s5 = prs.slides[4]
    s6 = prs.slides[5]

    # --- Slide 1 title page ---
    tb = shape_by_name(s1, "TextBox 9")
    fill_box(
        tb,
        [
            "",
            "Problem Statement ID – SIH26106",
            "Problem Statement Title – AI-Powered Email Threat Detection, GeoLocation and Forensic Intelligence Platform",
            "Theme – [Fill from SIH portal]",
            "PS Category – Software",
            "Team ID – [Fill from SIH portal]",
            "Team Name (Registered on portal) – prajjwaldubey",
        ],
    )

    # --- Slide 2 ---
    t2 = shape_by_name(s2, "Title 1")
    set_runs_text(t2.text_frame.paragraphs[0], "MailTrace")
    fill_box(
        shape_by_name(s2, "TextBox 8"),
        [
            "Proposed Solution (Describe your Idea/Solution/Prototype)",
            "",
            "Prototype: paste / upload a full original email (.eml or Gmail Show original). Output: threat score, hop map, forensic PDF.",
            "• Detection: SPF, DKIM, DMARC + content cues (urgency, lookalike domains, risky URLs) → score 0–100 and label (legitimate / suspicious / phishing–BEC).",
            "• GeoLocation: public IPv4 addresses from Received: headers → city / country / ISP on a map (mail servers, not a person).",
            "• Forensics: explainable reason list, saved cases, downloadable PDF for SOC / admin review.",
            "How it addresses the problem",
            "• The PS asks for threat detection + geolocation + investigative report in software — this is one laptop pipeline.",
            "• Same tool for genuine and malicious mail; every score point is a logged reason (not a black box).",
            "• User provides the message they received; no mailbox login or interception.",
            "Innovation and uniqueness of the solution",
            "• Explainable scoring suitable for forensics; hop map + PDF in one flow.",
            "• Honest attribution: infrastructure / ISP only. Gmail–Gmail empty map is shown as expected (no public IPv4).",
            "• Heuristic engine now; the same features can host a trained classifier later.",
        ],
        body_idx=3,
    )
    oval_team(s2)

    # --- Slide 3 ---
    fill_box(
        shape_by_name(s3, "TextBox 8"),
        [
            "Technologies to be used",
            "• Python 3, FastAPI, Uvicorn — local web prototype (no hardware / SDR).",
            "• RFC822 parser; rule engine for stamps + scam cues; SQLite case store; ReportLab PDF; Leaflet map.",
            "• Geo: built-in IP table for demo hops + optional ip-api lookup for unknown public IPv4.",
            "Methodology and process for implementation",
            "• Ingest raw email → parse headers/body/URLs → read Authentication-Results (SPF/DKIM/DMARC).",
            "• Apply weighted heuristics → extract public IPv4 from Received: → geolocate → score + reasons.",
            "• UI shows banner, stamps, map, why-list; export forensic PDF. Working prototype already runs on laptop.",
        ],
        body_idx=0,
    )
    oval_team(s3)

    # --- Slide 4 ---
    fill_box(
        shape_by_name(s4, "TextBox 8"),
        [
            "Analysis of the feasibility of the idea",
            "• Software-only PS: no classified data, no Gmail password, no RF hardware. Feasible as a student laptop demo.",
            "• Real Show original mails already run through the same pipeline as lab traces.",
            "Potential challenges and risks",
            "• Gmail hides origin IP / IPv6-only hops → map may be empty.",
            "• No official SIH phishing dataset; CDN/font links can add small score on real newsletters.",
            "• Judges may ask “where is the AI?” if we over-claim a neural network.",
            "Strategies for overcoming these challenges",
            "• Caption empty maps as Gmail–Gmail (expected); still show score and stamps when present.",
            "• Demo two real mails (spam + genuine) plus explainable reason list.",
            "• Position as explainable heuristic intelligence now; ML on the same features as next step. Ethics: pasted mail only, no identity claim.",
        ],
        body_idx=0,
    )
    oval_team(s4)

    # --- Slide 5 ---
    fill_box(
        shape_by_name(s5, "TextBox 8"),
        [
            "Potential impact on the target audience",
            "• College / institute SOC and IT admin: faster triage of fake dean, GST, invoice, and internship-scam mail.",
            "• Students and staff: clear “do not pay / click” vs “looks legitimate” with reasons they can understand.",
            "• CERT-style review of a single suspicious message without reading raw headers by hand.",
            "Benefits of the solution (social, economic, environmental, etc.)",
            "• Social: fewer people falling for BEC / phishing; transparent “servers not a person” geo.",
            "• Economic: less fraud loss and less analyst time per ticket; PDF for internal records.",
            "• Environmental: paperless forensic report instead of printed header dumps.",
        ],
        body_idx=0,
    )
    oval_team(s5)

    # --- Slide 6 ---
    fill_box(
        shape_by_name(s6, "TextBox 8"),
        [
            "Details / Links of the reference and research work",
            "• RFC 7208 SPF — https://datatracker.ietf.org/doc/html/rfc7208",
            "• RFC 6376 DKIM — https://datatracker.ietf.org/doc/html/rfc6376",
            "• RFC 7489 DMARC — https://datatracker.ietf.org/doc/html/rfc7489",
            "• RFC 5321 SMTP (mail is relayed; Received chain is servers) — https://datatracker.ietf.org/doc/html/rfc5321",
            "• CERT-In / MeitY phishing and BEC advisories — https://www.cert-in.org.in/",
            "• APWG Phishing Activity Trends Reports — https://apwg.org/",
            "• Gmail “Show original” (full headers for analysis) — Google Account Help",
        ],
        body_idx=0,
    )
    oval_team(s6)

    prs.save(str(DST))
    print(DST)


if __name__ == "__main__":
    main()
