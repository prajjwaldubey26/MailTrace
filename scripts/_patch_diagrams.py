"""Patch diagram sizing in build_mailtrace_devwise_style.py"""
from pathlib import Path

p = Path(r"C:\Users\prajj\Documents\proto.SIH\scripts\build_mailtrace_devwise_style.py")
text = p.read_text(encoding="utf-8")
start = text.index("def draw_hub(")
end = text.index("def make_feasibility_diagram(")
mini_start = text.index("def draw_mini_icon(", start)
mini_end = text.index("def draw_item_tree(", mini_start)
mini_block = text[mini_start:mini_end]

new_hub = '''def draw_hub(d, cx, cy, lines, icon="dots"):
    w, h = 340, 180
    rounded_rect(
        d,
        (cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2),
        22,
        fill=(236, 236, 236),
        outline=(110, 110, 110),
        width=4,
    )
    if icon == "dots":
        for ox, oy in [(-24, -48), (8, -48), (-24, -18), (8, -18)]:
            d.ellipse((cx + ox, cy + oy, cx + ox + 20, cy + oy + 20), fill=(70, 70, 70))
    else:
        d.ellipse((cx - 28, cy - 56, cx + 28, cy - 4), outline=(70, 70, 70), width=4)
        d.arc((cx - 42, cy - 46, cx + 42, cy + 14), 20, 160, fill=(70, 70, 70), width=4)
        d.line([(cx - 32, cy - 28), (cx + 32, cy - 28)], fill=(70, 70, 70), width=4)
    y = cy + 14
    for line in lines:
        d.text((cx, y), line, font=font(24, True), fill=(30, 30, 30), anchor="mm")
        y += 28


'''

rest = r'''def draw_item_tree(d, pill_box, items, side="below"):
    x0 = pill_box[0] + 26
    if side == "below":
        y0 = pill_box[3] + 6
        direction = 1
    else:
        y0 = pill_box[1] - 6
        direction = -1
    fnt = font(17)
    line_h = 26
    total = len(items) * line_h + 10
    y_end = y0 + direction * total
    dashed_line(d, (x0, y0), (x0, y_end), fill=(110, 110, 110), width=3, dash=5, gap=4)
    for i, it in enumerate(items):
        yi = y0 + direction * (18 + i * line_h)
        dashed_line(d, (x0, yi), (x0 + 18, yi), fill=(110, 110, 110), width=3, dash=5, gap=4)
        d.text((x0 + 24, yi), it, font=fnt, fill=(55, 55, 55), anchor="lm")


def draw_category_pill(d, cx, cy, title, color, icon_kind):
    fnt = font(20, True)
    tw, th = text_size(d, title, fnt)
    icon_w = 36
    pad_x, pad_y = 16, 14
    w = tw + icon_w + pad_x * 2 + 14
    h = max(th + pad_y * 2, 52)
    box = (cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2)
    rounded_rect(d, box, 14, fill=pastel(color, 185), outline=color, width=4)
    ix = cx - w // 2 + pad_x + 12
    draw_mini_icon(d, icon_kind, ix, cy, color)
    d.text((ix + 18, cy), title, font=fnt, fill=color, anchor="lm")
    return box


def _crop_white(im, pad=18):
    rgb = im.convert("RGB")
    w, h = rgb.size
    px = rgb.load()
    minx, miny, maxx, maxy = w, h, 0, 0
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            if r < 250 or g < 250 or b < 250:
                minx = min(minx, x)
                miny = min(miny, y)
                maxx = max(maxx, x)
                maxy = max(maxy, y)
    if maxx <= minx:
        return im
    return im.crop((max(0, minx - pad), max(0, miny - pad), min(w, maxx + pad), min(h, maxy + pad)))


def make_workflow_diagram(path: Path):
    W, H = 1400, 1180
    im = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)
    cx, cy = 700, 560
    draw_hub(d, cx, cy, ["MailTrace", "Pipeline"], icon="dots")
    branches = [
        ("Ingest", C_BLUE, "ingest", ["Paste / .eml upload", "Show original mail", "SHA-256 custody"], (160, 120), "below", 0.34),
        ("Auth Stamps", C_GREEN, "auth", ["SPF / DKIM / DMARC", "Authentication-Results", "Sender checks", "Stamp fail flags"], (130, 500), "below", 0.16),
        ("Identity", C_CYAN, "identity", ["From vs Reply-To", "Display-name mismatch", "Lookalike domains"], (240, 1000), "above", 0.32),
        ("Scoring", C_RED, "score", ["Risk score 0-100", "Five verdict labels", "Explainable reasons"], (680, 1080), "above", 0.10),
        ("Geo Trace", C_ORANGE, "geo", ["Received hop chain", "Public IPv4 map", "City / country / ISP"], (1180, 960), "above", 0.28),
        ("NLP Cues", C_PURPLE, "nlp", ["Urgency language", "Gift-card / invoice BEC", "Risky URLs", "Impersonation cues"], (1260, 430), "below", 0.22),
        ("Forensics", C_GREY, "forensic", ["Case vault", "PDF report", "IOC / graph view"], (1160, 110), "below", 0.36),
    ]
    for title, color, icon, items, (bx, by), side, bend in branches:
        dashed_curve(d, (cx, cy), (bx, by), bend=bend, fill=(120, 120, 120), width=3, dash=8, gap=5)
        box = draw_category_pill(d, bx, by, title, color, icon)
        draw_item_tree(d, box, items, side=side)
    im = _crop_white(im)
    im.save(path)
    return path


def make_techstack_diagram(path: Path):
    W, H = 1300, 1140
    im = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)
    cx, cy = 650, 580
    draw_hub(d, cx, cy, ["Technologies", "to be Used"], icon="vr")
    branches = [
        ("Frontend", C_GREEN, "frontend", ["HTML / CSS / JS", "Leaflet map"], (150, 130), "below", 0.34),
        ("Backend", C_BLUE, "backend", ["Python 3", "FastAPI", "Uvicorn"], (1140, 150), "below", 0.24),
        ("Analysis", C_PURPLE, "analysis", ["RFC822 parser", "NLP cue engine", "SPF / DKIM / DMARC"], (1180, 620), "below", 0.14),
        ("Geo & Intel", C_CYAN, "geo", ["IP geo table", "Optional IP lookup", "Domain cues"], (1080, 1020), "above", 0.30),
        ("Storage", C_ORANGE, "storage", ["SQLite cases", "ReportLab PDF"], (170, 1000), "above", 0.26),
        ("Runtime", C_RED, "runtime", ["Local laptop", "Cloud (Render)"], (120, 560), "below", 0.12),
    ]
    for title, color, icon, items, (bx, by), side, bend in branches:
        dashed_curve(d, (cx, cy), (bx, by), bend=bend, fill=(120, 120, 120), width=3, dash=8, gap=5)
        box = draw_category_pill(d, bx, by, title, color, icon)
        draw_item_tree(d, box, items, side=side)
    im = _crop_white(im)
    im.save(path)
    return path


'''

p.write_text(text[:start] + new_hub + mini_block + rest + text[end:], encoding="utf-8")
print("patched")
