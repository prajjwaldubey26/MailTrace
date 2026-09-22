"""Replace curved connectors with orthogonal icon-side joins."""
from pathlib import Path

p = Path(r"C:\Users\prajj\Documents\proto.SIH\scripts\build_mailtrace_devwise_style.py")
text = p.read_text(encoding="utf-8")

# Insert orthogonal helpers after measure_pill_box, before draw_mini_icon
marker = "def draw_mini_icon(d, kind, x, y, col):"
helpers = r'''
def icon_side_point(pill_box):
    """Connection target: left-middle of pill (icon lives at the start)."""
    left, top, right, bottom = pill_box
    return (left, (top + bottom) / 2)


def hub_exit_and_stub(hub_box, toward, stub=30):
    """Straight exit from hub SIDE (not center), then short outward stub."""
    exit_pt = rect_border_point(hub_box, toward[0], toward[1])
    left, top, right, bottom = hub_box
    ex, ey = exit_pt
    if abs(ex - left) <= 1.5:
        stub_pt = (ex - stub, ey)
    elif abs(ex - right) <= 1.5:
        stub_pt = (ex + stub, ey)
    elif abs(ey - top) <= 1.5:
        stub_pt = (ex, ey - stub)
    else:
        stub_pt = (ex, ey + stub)
    return exit_pt, stub_pt


def _seg_hits_box(a, b, box, pad=10):
    """Axis-aligned segment vs inflated box."""
    x0, y0 = a
    x1, y1 = b
    l, t, r, btm = box
    l, t, r, btm = l - pad, t - pad, r + pad, btm + pad
    if abs(y0 - y1) < 0.5:  # horizontal
        y = y0
        if y < t or y > btm:
            return False
        lo, hi = sorted((x0, x1))
        return not (hi < l or lo > r)
    if abs(x0 - x1) < 0.5:  # vertical
        x = x0
        if x < l or x > r:
            return False
        lo, hi = sorted((y0, y1))
        return not (hi < t or lo > btm)
    return False


def _path_hits(points, obstacles):
    for i in range(len(points) - 1):
        for ob in obstacles:
            if _seg_hits_box(points[i], points[i + 1], ob):
                return True
    return False


def orthogonal_to_icon(hub_box, pill_box, obstacles=None):
    """
    Multi-bend orthogonal path:
    hub side (straight stub) -> elbows -> straight into icon side.
    Never curved. Final segment is always horizontal into the icon.
    """
    obstacles = list(obstacles or [])
    # do not treat own pill as obstacle for final approach
    icon = icon_side_point(pill_box)
    approach = (icon[0] - 34, icon[1])  # straight horizontal into icon
    pcx = (pill_box[0] + pill_box[2]) / 2
    pcy = (pill_box[1] + pill_box[3]) / 2
    exit_pt, stub = hub_exit_and_stub(hub_box, (pcx, pcy), stub=32)

    sx, sy = stub
    ax, ay = approach

    candidates = [
        # 2-bend classic
        [exit_pt, stub, (sx, ay), approach, icon],
        [exit_pt, stub, (ax, sy), approach, icon],
        # 3-bend via mid channels (more room to dodge)
        [exit_pt, stub, (sx, (sy + ay) / 2), (ax, (sy + ay) / 2), approach, icon],
        [exit_pt, stub, ((sx + ax) / 2, sy), ((sx + ax) / 2, ay), approach, icon],
    ]

    # Prefer paths that miss hub + other obstacles
    hub_obs = [
        (
            hub_box[0] + 4,
            hub_box[1] + 4,
            hub_box[2] - 4,
            hub_box[3] - 4,
        )
    ]
    obs = hub_obs + obstacles
    best = None
    for pts in candidates:
        # collapse near-duplicates
        clean = [pts[0]]
        for q in pts[1:]:
            if abs(q[0] - clean[-1][0]) > 1 or abs(q[1] - clean[-1][1]) > 1:
                clean.append(q)
        # score: collisions then length
        hits = 1 if _path_hits(clean[1:-1], obs) else 0  # allow stubs near boxes lightly
        # stricter: full path except final into icon
        hits = 0
        for i in range(len(clean) - 2):
            for ob in obs:
                if _seg_hits_box(clean[i], clean[i + 1], ob, pad=8):
                    hits += 1
        length = 0.0
        for i in range(len(clean) - 1):
            length += abs(clean[i + 1][0] - clean[i][0]) + abs(clean[i + 1][1] - clean[i][1])
        score = (hits, length)
        if best is None or score < best[0]:
            best = (score, clean)
    return best[1]


def dashed_polyline(draw, points, fill=(115, 115, 115), width=3, dash=8, gap=5):
    for i in range(len(points) - 1):
        dashed_line(draw, points[i], points[i + 1], fill=fill, width=width, dash=dash, gap=gap)


'''

if marker not in text:
    raise SystemExit("marker not found")
# avoid double-insert
if "def orthogonal_to_icon(" not in text:
    text = text.replace(marker, helpers + marker, 1)

# Replace make_workflow and make_techstack connector sections
start = text.index("def make_workflow_diagram(")
end = text.index("def make_feasibility_diagram(")

new = r'''def make_workflow_diagram(path: Path):
    W, H = 980, 860
    im = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)
    cx, cy = 490, 410
    hub_box = draw_hub(d, cx, cy, ["MailTrace", "Pipeline"], icon="dots")
    branches = [
        ("Ingest", C_BLUE, "ingest", ["Paste / .eml upload", "Show original mail", "SHA-256 custody"], (140, 95), "below"),
        ("Auth Stamps", C_GREEN, "auth", ["SPF / DKIM / DMARC", "Authentication-Results", "Sender checks", "Stamp fail flags"], (115, 380), "below"),
        ("Identity", C_CYAN, "identity", ["From vs Reply-To", "Display-name mismatch", "Lookalike domains"], (175, 730), "above"),
        ("Scoring", C_RED, "score", ["Risk score 0-100", "Five verdict labels", "Explainable reasons"], (490, 790), "above"),
        ("Geo Trace", C_ORANGE, "geo", ["Received hop chain", "Public IPv4 map", "City / country / ISP"], (820, 710), "above"),
        ("NLP Cues", C_PURPLE, "nlp", ["Urgency language", "Gift-card / invoice BEC", "Risky URLs", "Impersonation cues"], (860, 320), "below"),
        ("Forensics", C_GREY, "forensic", ["Case vault", "PDF report", "IOC / graph view"], (800, 90), "below"),
    ]
    pills = [(title, measure_pill_box(bx, by, title), (bx, by), side, color, icon, items)
             for title, color, icon, items, (bx, by), side in branches]
    # obstacles = all other pills (avoid crossing boxes)
    for i, (title, pill, pos, side, color, icon, items) in enumerate(pills):
        others = [pills[j][1] for j in range(len(pills)) if j != i]
        pts = orthogonal_to_icon(hub_box, pill, obstacles=others)
        dashed_polyline(d, pts, fill=(110, 110, 110), width=3, dash=8, gap=5)
    for title, pill, (bx, by), side, color, icon, items in pills:
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
        ("Frontend", C_GREEN, "frontend", ["HTML / CSS / JS", "Leaflet map"], (130, 100), "below"),
        ("Backend", C_BLUE, "backend", ["Python 3", "FastAPI", "Uvicorn"], (800, 110), "below"),
        ("Analysis", C_PURPLE, "analysis", ["RFC822 parser", "NLP cue engine", "SPF / DKIM / DMARC"], (830, 430), "below"),
        ("Geo & Intel", C_CYAN, "geo", ["IP geo table", "Optional IP lookup", "Domain cues"], (760, 730), "above"),
        ("Storage", C_ORANGE, "storage", ["SQLite cases", "ReportLab PDF"], (140, 720), "above"),
        ("Runtime", C_RED, "runtime", ["Local laptop", "Cloud (Render)"], (110, 400), "below"),
    ]
    pills = [(title, measure_pill_box(bx, by, title), (bx, by), side, color, icon, items)
             for title, color, icon, items, (bx, by), side in branches]
    for i, (title, pill, pos, side, color, icon, items) in enumerate(pills):
        others = [pills[j][1] for j in range(len(pills)) if j != i]
        pts = orthogonal_to_icon(hub_box, pill, obstacles=others)
        dashed_polyline(d, pts, fill=(110, 110, 110), width=3, dash=8, gap=5)
    for title, pill, (bx, by), side, color, icon, items in pills:
        box = draw_category_pill(d, bx, by, title, color, icon)
        draw_item_tree(d, box, items, side=side)
    im = _crop_white(im, pad=12)
    im.save(path)
    return path


'''

p.write_text(text[:start] + new + text[end:], encoding="utf-8")
print("orthogonal icon connectors ready")
