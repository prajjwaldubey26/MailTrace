"""Retighten flowchart canvas so text stays large on the slide."""
from pathlib import Path

p = Path(r"C:\Users\prajj\Documents\proto.SIH\scripts\build_mailtrace_devwise_style.py")
text = p.read_text(encoding="utf-8")

# Replace make_workflow_diagram and make_techstack_diagram bodies only
start = text.index("def make_workflow_diagram(")
end = text.index("def make_feasibility_diagram(")

new = r'''def make_workflow_diagram(path: Path):
    # Compact canvas + large fonts => readable after slide scale-down
    W, H = 980, 860
    im = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)
    cx, cy = 490, 410
    draw_hub(d, cx, cy, ["MailTrace", "Pipeline"], icon="dots")
    branches = [
        ("Ingest", C_BLUE, "ingest", ["Paste / .eml upload", "Show original mail", "SHA-256 custody"], (140, 95), "below", 0.30),
        ("Auth Stamps", C_GREEN, "auth", ["SPF / DKIM / DMARC", "Authentication-Results", "Sender checks", "Stamp fail flags"], (115, 380), "below", 0.14),
        ("Identity", C_CYAN, "identity", ["From vs Reply-To", "Display-name mismatch", "Lookalike domains"], (175, 730), "above", 0.28),
        ("Scoring", C_RED, "score", ["Risk score 0-100", "Five verdict labels", "Explainable reasons"], (490, 790), "above", 0.08),
        ("Geo Trace", C_ORANGE, "geo", ["Received hop chain", "Public IPv4 map", "City / country / ISP"], (820, 710), "above", 0.26),
        ("NLP Cues", C_PURPLE, "nlp", ["Urgency language", "Gift-card / invoice BEC", "Risky URLs", "Impersonation cues"], (860, 320), "below", 0.20),
        ("Forensics", C_GREY, "forensic", ["Case vault", "PDF report", "IOC / graph view"], (800, 90), "below", 0.32),
    ]
    for title, color, icon, items, (bx, by), side, bend in branches:
        dashed_curve(d, (cx, cy), (bx, by), bend=bend, fill=(115, 115, 115), width=3, dash=8, gap=5)
        box = draw_category_pill(d, bx, by, title, color, icon)
        draw_item_tree(d, box, items, side=side)
    im = _crop_white(im, pad=12)
    im.save(path)
    return path


def make_techstack_diagram(path: Path):
    W, H = 920, 820
    im = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)
    cx, cy = 460, 400
    draw_hub(d, cx, cy, ["Technologies", "to be Used"], icon="vr")
    branches = [
        ("Frontend", C_GREEN, "frontend", ["HTML / CSS / JS", "Leaflet map"], (130, 100), "below", 0.30),
        ("Backend", C_BLUE, "backend", ["Python 3", "FastAPI", "Uvicorn"], (800, 110), "below", 0.22),
        ("Analysis", C_PURPLE, "analysis", ["RFC822 parser", "NLP cue engine", "SPF / DKIM / DMARC"], (830, 430), "below", 0.12),
        ("Geo & Intel", C_CYAN, "geo", ["IP geo table", "Optional IP lookup", "Domain cues"], (760, 730), "above", 0.28),
        ("Storage", C_ORANGE, "storage", ["SQLite cases", "ReportLab PDF"], (140, 720), "above", 0.24),
        ("Runtime", C_RED, "runtime", ["Local laptop", "Cloud (Render)"], (110, 400), "below", 0.10),
    ]
    for title, color, icon, items, (bx, by), side, bend in branches:
        dashed_curve(d, (cx, cy), (bx, by), bend=bend, fill=(115, 115, 115), width=3, dash=8, gap=5)
        box = draw_category_pill(d, bx, by, title, color, icon)
        draw_item_tree(d, box, items, side=side)
    im = _crop_white(im, pad=12)
    im.save(path)
    return path


'''

p.write_text(text[:start] + new + text[end:], encoding="utf-8")

# also enlarge picture placement on slide 3
text2 = p.read_text(encoding="utf-8")
text2 = text2.replace(
    's3.shapes.add_picture(str(wf), Inches(0.4), Inches(1.35), Inches(6.1), Inches(5.2))',
    's3.shapes.add_picture(str(wf), Inches(0.35), Inches(1.25), Inches(6.2), Inches(5.35))',
)
text2 = text2.replace(
    's3.shapes.add_picture(str(ts), Inches(7.05), Inches(1.7), Inches(5.8), Inches(4.8))',
    's3.shapes.add_picture(str(ts), Inches(6.95), Inches(1.65), Inches(6.0), Inches(4.95))',
)
p.write_text(text2, encoding="utf-8")
print("ok")
