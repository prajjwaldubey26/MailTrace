"""Wire connectors edge-to-edge (hub side -> pill side)."""
from pathlib import Path

p = Path(r"C:\Users\prajj\Documents\proto.SIH\scripts\build_mailtrace_devwise_style.py")
text = p.read_text(encoding="utf-8")

# 1) draw_hub returns box
old_hub_end = '''    y = cy + 14
    for line in lines:
        d.text((cx, y), line, font=font(24, True), fill=(30, 30, 30), anchor="mm")
        y += 28


def draw_mini_icon'''

new_hub_end = '''    y = cy + 14
    for line in lines:
        d.text((cx, y), line, font=font(24, True), fill=(30, 30, 30), anchor="mm")
        y += 28
    return (cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2)


def rect_border_point(box, tx, ty):
    """Where the ray from box center toward (tx, ty) hits the box edge."""
    left, top, right, bottom = box
    cx = (left + right) / 2
    cy = (top + bottom) / 2
    dx, dy = tx - cx, ty - cy
    if abs(dx) < 1e-6 and abs(dy) < 1e-6:
        return (cx, cy)
    ts = []
    if dx > 0:
        ts.append((right - cx) / dx)
    elif dx < 0:
        ts.append((left - cx) / dx)
    if dy > 0:
        ts.append((bottom - cy) / dy)
    elif dy < 0:
        ts.append((top - cy) / dy)
    t = min(t for t in ts if t > 0)
    return (cx + dx * t, cy + dy * t)


def measure_pill_box(cx, cy, title):
    """Same geometry as draw_category_pill, without drawing."""
    # temporary measure using default font metrics via a 1px image
    from PIL import Image as _Image, ImageDraw as _ImageDraw
    _d = _ImageDraw.Draw(_Image.new("RGB", (8, 8)))
    fnt = font(20, True)
    tw, th = text_size(_d, title, fnt)
    icon_w = 36
    pad_x, pad_y = 16, 14
    w = tw + icon_w + pad_x * 2 + 14
    h = max(th + pad_y * 2, 52)
    return (cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2)


def draw_mini_icon'''

if old_hub_end not in text:
    raise SystemExit("hub end marker not found")
text = text.replace(old_hub_end, new_hub_end, 1)

# 2) replace workflow + techstack connector loops
start = text.index("def make_workflow_diagram(")
end = text.index("def make_feasibility_diagram(")

new = r'''def make_workflow_diagram(path: Path):
    # Compact canvas + large fonts => readable after slide scale-down
    W, H = 980, 860
    im = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)
    cx, cy = 490, 410
    hub_box = draw_hub(d, cx, cy, ["MailTrace", "Pipeline"], icon="dots")
    branches = [
        ("Ingest", C_BLUE, "ingest", ["Paste / .eml upload", "Show original mail", "SHA-256 custody"], (140, 95), "below", 0.30),
        ("Auth Stamps", C_GREEN, "auth", ["SPF / DKIM / DMARC", "Authentication-Results", "Sender checks", "Stamp fail flags"], (115, 380), "below", 0.14),
        ("Identity", C_CYAN, "identity", ["From vs Reply-To", "Display-name mismatch", "Lookalike domains"], (175, 730), "above", 0.28),
        ("Scoring", C_RED, "score", ["Risk score 0-100", "Five verdict labels", "Explainable reasons"], (490, 790), "above", 0.08),
        ("Geo Trace", C_ORANGE, "geo", ["Received hop chain", "Public IPv4 map", "City / country / ISP"], (820, 710), "above", 0.26),
        ("NLP Cues", C_PURPLE, "nlp", ["Urgency language", "Gift-card / invoice BEC", "Risky URLs", "Impersonation cues"], (860, 320), "below", 0.20),
        ("Forensics", C_GREY, "forensic", ["Case vault", "PDF report", "IOC / graph view"], (800, 90), "below", 0.32),
    ]
    # Connectors first: hub EDGE -> pill EDGE (clean, not from mid)
    for title, color, icon, items, (bx, by), side, bend in branches:
        pill = measure_pill_box(bx, by, title)
        p_hub = rect_border_point(hub_box, bx, by)
        p_pill = rect_border_point(pill, cx, cy)
        dashed_curve(d, p_hub, p_pill, bend=bend, fill=(115, 115, 115), width=3, dash=8, gap=5)
    for title, color, icon, items, (bx, by), side, bend in branches:
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
    hub_box = draw_hub(d, cx, cy, ["Technologies", "to be Used"], icon="vr")
    branches = [
        ("Frontend", C_GREEN, "frontend", ["HTML / CSS / JS", "Leaflet map"], (130, 100), "below", 0.30),
        ("Backend", C_BLUE, "backend", ["Python 3", "FastAPI", "Uvicorn"], (800, 110), "below", 0.22),
        ("Analysis", C_PURPLE, "analysis", ["RFC822 parser", "NLP cue engine", "SPF / DKIM / DMARC"], (830, 430), "below", 0.12),
        ("Geo & Intel", C_CYAN, "geo", ["IP geo table", "Optional IP lookup", "Domain cues"], (760, 730), "above", 0.28),
        ("Storage", C_ORANGE, "storage", ["SQLite cases", "ReportLab PDF"], (140, 720), "above", 0.24),
        ("Runtime", C_RED, "runtime", ["Local laptop", "Cloud (Render)"], (110, 400), "below", 0.10),
    ]
    for title, color, icon, items, (bx, by), side, bend in branches:
        pill = measure_pill_box(bx, by, title)
        p_hub = rect_border_point(hub_box, bx, by)
        p_pill = rect_border_point(pill, cx, cy)
        dashed_curve(d, p_hub, p_pill, bend=bend, fill=(115, 115, 115), width=3, dash=8, gap=5)
    for title, color, icon, items, (bx, by), side, bend in branches:
        box = draw_category_pill(d, bx, by, title, color, icon)
        draw_item_tree(d, box, items, side=side)
    im = _crop_white(im, pad=12)
    im.save(path)
    return path


'''

p.write_text(text[:start] + new + text[end:], encoding="utf-8")
print("edge connectors patched")
