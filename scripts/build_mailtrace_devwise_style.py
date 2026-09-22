"""Generate MailTrace SIH PPT matching DevWise visual design system."""

from __future__ import annotations

import math
from copy import deepcopy
from pathlib import Path

from lxml import etree
from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_SHAPE_TYPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

ROOT = Path(r"C:\Users\prajj\Documents\proto.SIH")
SRC = Path(r"C:\Users\prajj\Downloads\SIH2026-IDEA-Presentation-Format (2).pptx")
DST = ROOT / "MailTrace_SIH26106_DevWiseStyle.pptx"
ASSETS = ROOT / "scripts" / "mailtrace_assets"
ASSETS.mkdir(parents=True, exist_ok=True)

TEAM = "prajjwaldubey"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"

# DevWise palette
FOOTER_BLUE = RGBColor(0x2A, 0x7A, 0xB8)
BORDER_BLUE = RGBColor(0x6D, 0xB0, 0xD8)
OVAL_PURPLE = RGBColor(0x8B, 0x7B, 0xB8)
INK = RGBColor(0x1A, 0x1A, 0x1A)
HEAD_BLUE = RGBColor(0x1E, 0x5A, 0x8C)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
MUTED = RGBColor(0x55, 0x55, 0x55)

# Pastel category colors (RGB tuples for PIL)
C_BLUE = (70, 130, 200)
C_GREEN = (60, 160, 100)
C_CYAN = (50, 170, 180)
C_RED = (210, 100, 110)
C_ORANGE = (210, 140, 70)
C_PURPLE = (140, 100, 180)
C_GREY = (140, 140, 150)


def font(size: int, bold: bool = False):
    candidates = [
        r"C:\Windows\Fonts\calibrib.ttf" if bold else r"C:\Windows\Fonts\calibri.ttf",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\timesbd.ttf" if bold else r"C:\Windows\Fonts\times.ttf",
    ]
    for c in candidates:
        if Path(c).exists():
            return ImageFont.truetype(c, size)
    return ImageFont.load_default()


def rounded_rect(draw, xy, radius, fill=None, outline=None, width=2):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def dashed_line(draw, p0, p1, fill=(180, 180, 180), width=2, dash=7, gap=5):
    x0, y0 = p0
    x1, y1 = p1
    length = math.hypot(x1 - x0, y1 - y0) or 1
    dx, dy = (x1 - x0) / length, (y1 - y0) / length
    t = 0.0
    draw_on = True
    while t < length:
        seg = dash if draw_on else gap
        t2 = min(length, t + seg)
        if draw_on:
            draw.line(
                (x0 + dx * t, y0 + dy * t, x0 + dx * t2, y0 + dy * t2),
                fill=fill,
                width=width,
            )
        t = t2
        draw_on = not draw_on


def dashed_curve(draw, p0, p1, bend=0.22, fill=(150, 150, 150), width=2, dash=6, gap=5):
    """Quadratic bezier dotted connector (not a plain straight line)."""
    x0, y0 = p0
    x1, y1 = p1
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    # perpendicular offset for uneven organic curves
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy) or 1
    px, py = -dy / length, dx / length
    # alternate bend direction by endpoint quadrant-ish
    sign = 1 if ((x0 + y0) // 40) % 2 == 0 else -1
    cx = mx + px * length * bend * sign
    cy = my + py * length * bend * sign

    steps = max(24, int(length / 8))
    pts = []
    for i in range(steps + 1):
        t = i / steps
        u = 1 - t
        x = u * u * x0 + 2 * u * t * cx + t * t * x1
        y = u * u * y0 + 2 * u * t * cy + t * t * y1
        pts.append((x, y))

    draw_on = True
    acc = 0.0
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        seg_len = math.hypot(b[0] - a[0], b[1] - a[1])
        acc += seg_len
        if draw_on:
            draw.line((a[0], a[1], b[0], b[1]), fill=fill, width=width)
        if acc >= (dash if draw_on else gap):
            acc = 0.0
            draw_on = not draw_on


def text_size(draw, text, fnt):
    b = draw.textbbox((0, 0), text, font=fnt)
    return b[2] - b[0], b[3] - b[1]


def wrap_text(draw, text, fnt, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if text_size(draw, trial, fnt)[0] <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [text]


# -------------------- diagram generators --------------------

def make_mailtrace_logo(path: Path):
    """Circular project emblem (DevWise-style center logo)."""
    s = 512
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # outer rings
    d.ellipse((20, 20, s - 20, s - 20), fill=(20, 70, 110, 255))
    d.ellipse((55, 55, s - 55, s - 55), fill=(245, 248, 252, 255))
    # envelope
    d.rounded_rectangle((140, 200, 372, 340), radius=18, outline=(30, 120, 170), width=8)
    d.line([(140, 210), (256, 290), (372, 210)], fill=(30, 120, 170), width=7)
    # path/trace arc
    d.arc((100, 120, 412, 400), start=200, end=340, fill=(40, 180, 150), width=8)
    d.ellipse((350, 145, 380, 175), fill=(220, 80, 90))
    # label ring text
    f = font(36, True)
    d.text((s // 2, 430), "MAILTRACE", font=f, fill=(20, 70, 110), anchor="mm")
    im.save(path)
    return path


def pastel(color, amount=160):
    return tuple(min(255, c + amount) for c in color)


def draw_hub(d, cx, cy, lines, icon="dots"):
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


def orthogonal_to_icon(hub_box, pill_box, obstacles=None, tree_side="below"):
    """
    Orthogonal dashed path:
    - leaves hub from a SIDE (straight stub out)
    - only joins pill on ICON side (left edge), with a final STRAIGHT horizontal
    - elbows only (no curves), prefers paths that miss other boxes/text
    """
    obstacles = list(obstacles or [])
    left, top, right, bottom = pill_box
    icon = (left, (top + bottom) / 2.0)
    # always approach icon from the left with a straight horizontal
    approach = (icon[0] - 40, icon[1])

    # estimated text-tree obstacle under/over pill so lines don't cross labels
    tree_h = 110
    if tree_side == "below":
        tree_box = (left, bottom, right + 160, bottom + tree_h)
    else:
        tree_box = (left, top - tree_h, right + 160, top)
    obstacles = obstacles + [tree_box]

    # pick hub exit on the side facing the approach point (cleaner)
    exit_pt, stub = hub_exit_and_stub(hub_box, approach, stub=36)
    sx, sy = stub
    ax, ay = approach

    # Channel lanes around hub to keep lines in white space
    hl, ht, hr, hb = hub_box
    lane_left = hl - 55
    lane_right = hr + 55
    lane_top = ht - 55
    lane_bot = hb + 55

    candidates = []
    # direct elbows
    candidates.append([exit_pt, stub, (sx, ay), approach, icon])
    candidates.append([exit_pt, stub, (ax, sy), approach, icon])
    # around hub using outer lanes
    candidates.append([exit_pt, stub, (sx, lane_top), (ax, lane_top), approach, icon])
    candidates.append([exit_pt, stub, (sx, lane_bot), (ax, lane_bot), approach, icon])
    candidates.append([exit_pt, stub, (lane_left, sy), (lane_left, ay), approach, icon])
    candidates.append([exit_pt, stub, (lane_right, sy), (lane_right, ay), approach, icon])
    # go out then around
    candidates.append([exit_pt, stub, (lane_left, sy), (lane_left, lane_top), (ax, lane_top), approach, icon])
    candidates.append([exit_pt, stub, (lane_right, sy), (lane_right, lane_top), (ax, lane_top), approach, icon])
    candidates.append([exit_pt, stub, (lane_left, sy), (lane_left, lane_bot), (ax, lane_bot), approach, icon])
    candidates.append([exit_pt, stub, (lane_right, sy), (lane_right, lane_bot), (ax, lane_bot), approach, icon])

    hub_obs = [(hl + 2, ht + 2, hr - 2, hb - 2)]
    obs = hub_obs + obstacles

    best = None
    for pts in candidates:
        clean = [pts[0]]
        for q in pts[1:]:
            if abs(q[0] - clean[-1][0]) > 0.8 or abs(q[1] - clean[-1][1]) > 0.8:
                clean.append(q)
        # must end with horizontal into icon
        if abs(clean[-1][1] - clean[-2][1]) > 0.8:
            continue
        if clean[-1][0] <= clean[-2][0]:
            continue
        hits = 0
        # ignore final short approach into icon for collision
        for i in range(len(clean) - 2):
            for ob in obs:
                if _seg_hits_box(clean[i], clean[i + 1], ob, pad=6):
                    hits += 1
        length = sum(
            abs(clean[i + 1][0] - clean[i][0]) + abs(clean[i + 1][1] - clean[i][1])
            for i in range(len(clean) - 1)
        )
        score = (hits, length, len(clean))
        if best is None or score < best[0]:
            best = (score, clean)
    return best[1] if best else [exit_pt, stub, approach, icon]


def dashed_polyline(draw, points, fill=(110, 110, 110), width=3, dash=8, gap=5):
    for i in range(len(points) - 1):
        a, b = points[i], points[i + 1]
        # enforce axis-aligned segments only
        if abs(a[0] - b[0]) > 0.8 and abs(a[1] - b[1]) > 0.8:
            mid = (b[0], a[1])
            dashed_line(draw, a, mid, fill=fill, width=width, dash=dash, gap=gap)
            dashed_line(draw, mid, b, fill=fill, width=width, dash=dash, gap=gap)
        else:
            dashed_line(draw, a, b, fill=fill, width=width, dash=dash, gap=gap)


def draw_mini_icon(d, kind, x, y, col):
    """Small line icons inside category pills (DevWise style)."""
    if kind == "ingest":
        d.rounded_rectangle((x - 8, y - 6, x + 8, y + 6), radius=2, outline=col, width=2)
        d.line([(x - 5, y - 2), (x + 5, y - 2)], fill=col, width=1)
        d.line([(x - 5, y + 2), (x + 3, y + 2)], fill=col, width=1)
    elif kind == "auth":
        d.ellipse((x - 7, y - 8, x + 7, y + 6), outline=col, width=2)
        d.rectangle((x - 3, y + 2, x + 3, y + 9), outline=col, width=2)
    elif kind == "identity":
        d.ellipse((x - 5, y - 9, x + 5, y - 1), outline=col, width=2)
        d.arc((x - 9, y - 1, x + 9, y + 10), 200, 340, fill=col, width=2)
    elif kind == "nlp":
        d.ellipse((x - 8, y - 7, x + 8, y + 7), outline=col, width=2)
        d.line([(x - 3, y - 2), (x + 3, y - 2)], fill=col, width=1)
        d.line([(x - 2, y + 2), (x + 2, y + 2)], fill=col, width=1)
    elif kind == "geo":
        d.ellipse((x - 8, y - 8, x + 8, y + 8), outline=col, width=2)
        d.ellipse((x - 3, y - 3, x + 3, y + 3), outline=col, width=2)
        d.line([(x, y - 8), (x, y + 8)], fill=col, width=1)
        d.line([(x - 8, y), (x + 8, y)], fill=col, width=1)
    elif kind == "score":
        d.rectangle((x - 8, y + 2, x - 4, y + 8), fill=col)
        d.rectangle((x - 2, y - 2, x + 2, y + 8), fill=col)
        d.rectangle((x + 4, y - 6, x + 8, y + 8), fill=col)
    elif kind == "forensic":
        d.rounded_rectangle((x - 8, y - 8, x + 8, y + 8), radius=2, outline=col, width=2)
        d.line([(x - 4, y - 2), (x + 4, y - 2)], fill=col, width=1)
        d.line([(x - 4, y + 2), (x + 2, y + 2)], fill=col, width=1)
    elif kind == "frontend":
        d.rounded_rectangle((x - 9, y - 7, x + 9, y + 5), radius=2, outline=col, width=2)
        d.rectangle((x - 5, y + 5, x + 5, y + 8), outline=col, width=1)
    elif kind == "backend":
        d.polygon([(x - 8, y), (x, y - 8), (x + 8, y), (x, y + 8)], outline=col, width=2)
    elif kind == "analysis":
        # brain / chip cue
        d.ellipse((x - 8, y - 7, x + 8, y + 7), outline=col, width=2)
        d.line([(x - 4, y - 2), (x + 4, y - 2)], fill=col, width=1)
        d.line([(x - 3, y + 2), (x + 3, y + 2)], fill=col, width=1)
        d.line([(x, y - 7), (x, y - 11)], fill=col, width=2)
    elif kind == "storage":
        d.ellipse((x - 8, y - 8, x + 8, y - 2), outline=col, width=2)
        d.line([(x - 8, y - 5), (x - 8, y + 6)], fill=col, width=2)
        d.line([(x + 8, y - 5), (x + 8, y + 6)], fill=col, width=2)
        d.arc((x - 8, y + 2, x + 8, y + 10), 0, 180, fill=col, width=2)
    elif kind == "runtime":
        d.rounded_rectangle((x - 8, y - 6, x + 8, y + 4), radius=2, outline=col, width=2)
        d.ellipse((x - 10, y + 4, x + 10, y + 10), outline=col, width=2)
    else:
        d.ellipse((x - 6, y - 6, x + 6, y + 6), outline=col, width=2)


def draw_item_tree(d, pill_box, items, side="below"):
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



def _pad_to_aspect(im, aspect, fill=(255, 255, 255)):
    """Pad image with white so width/height == aspect (prevents PPT squash)."""
    w, h = im.size
    cur = w / max(h, 1)
    if abs(cur - aspect) < 0.02:
        return im
    if cur > aspect:
        # too wide -> add vertical pad
        new_h = int(round(w / aspect))
        out = Image.new("RGB", (w, new_h), fill)
        out.paste(im, (0, (new_h - h) // 2))
        return out
    new_w = int(round(h * aspect))
    out = Image.new("RGB", (new_w, h), fill)
    out.paste(im, ((new_w - w) // 2, 0))
    return out


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
        pts = orthogonal_to_icon(hub_box, pill, obstacles=others, tree_side=side)
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
        pts = orthogonal_to_icon(hub_box, pill, obstacles=others, tree_side=side)
        dashed_polyline(d, pts, fill=(110, 110, 110), width=3, dash=8, gap=5)
    for title, pill, (bx, by), side, color, icon, items in pills:
        box = draw_category_pill(d, bx, by, title, color, icon)
        draw_item_tree(d, box, items, side=side)
    im = _crop_white(im, pad=12)
    im.save(path)
    return path


def make_feasibility_diagram(path: Path):
    """Compact feasibility map matched to panel aspect (~2.8:1)."""
    # Target panel ~6.35x2.25 in -> keep content filling this ratio
    W, H = 980, 350
    im = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)

    cx, cy = 490, 195
    hub = (cx - 155, cy - 78, cx + 155, cy + 78)
    rounded_rect(d, hub, 18, fill=(236, 236, 236), outline=(95, 100, 110), width=4)
    d.ellipse((cx - 24, cy - 58, cx - 6, cy - 40), outline=(60, 65, 75), width=3)
    d.ellipse((cx + 6, cy - 58, cx + 24, cy - 40), outline=(60, 65, 75), width=3)
    d.arc((cx - 32, cy - 40, cx - 2, cy - 10), 200, 340, fill=(60, 65, 75), width=3)
    d.arc((cx + 2, cy - 40, cx + 32, cy - 10), 200, 340, fill=(60, 65, 75), width=3)
    d.text((cx, cy + 6), "Feasibility Analysis of", font=font(22), fill=(55, 60, 70), anchor="mm")
    d.text((cx, cy + 38), "MailTrace Platform", font=font(28, True), fill=(25, 30, 40), anchor="mm")

    def side_pill(bx, by, title, color, icon_kind):
        fnt = font(26, True)
        tw, th = text_size(d, title, fnt)
        pad_x, pad_y, icon_w = 16, 12, 40
        w = tw + icon_w + pad_x * 2 + 14
        h = max(th + pad_y * 2, 58)
        box = (bx - w // 2, by - h // 2, bx + w // 2, by + h // 2)
        rounded_rect(d, box, 14, fill=pastel(color, 170), outline=color, width=4)
        ix = bx - w // 2 + pad_x + 12
        draw_mini_icon(d, icon_kind, ix, by, color)
        d.text((ix + 20, by), title, font=fnt, fill=color, anchor="lm")
        return box

    def side_tree(pill_box, items):
        x0 = pill_box[0] + 28
        y0 = pill_box[3] + 6
        fnt = font(24)
        line_h = 34
        dashed_line(d, (x0, y0), (x0, y0 + len(items) * line_h + 6), fill=(95, 100, 110), width=3, dash=6, gap=4)
        for i, it in enumerate(items):
            yi = y0 + 20 + i * line_h
            dashed_line(d, (x0, yi), (x0 + 18, yi), fill=(95, 100, 110), width=3, dash=6, gap=4)
            d.text((x0 + 24, yi), it, font=fnt, fill=(35, 40, 50), anchor="lm")

    left = side_pill(175, 70, "Software & Cloud", C_GREEN, "runtime")
    right = side_pill(805, 70, "Current Technology", C_BLUE, "backend")

    # connectors hub mid-side -> pill mid-side (icon side for right/left)
    ly = (left[1] + left[3]) / 2
    ry = (right[1] + right[3]) / 2
    dashed_polyline(d, [(hub[0], cy), (hub[0] - 28, cy), (hub[0] - 28, ly), (left[2], ly)],
                    fill=(100, 105, 115), width=3, dash=8, gap=5)
    dashed_polyline(d, [(hub[2], cy), (hub[2] + 28, cy), (hub[2] + 28, ry), (right[0], ry)],
                    fill=(100, 105, 115), width=3, dash=8, gap=5)

    side_tree(left, ["Laptop demo ready", "No RF hardware", "No classified data"])
    side_tree(right, ["Header forensics", "NLP scam cues", "Hop geolocation"])

    # pad to panel aspect so PPT stretch does not crush type
    im = _crop_white(im, pad=8)
    im = _pad_to_aspect(im, 6.35 / 2.25)
    im.save(path)
    return path


def make_challenges_diagram(path: Path):
    """Balance-scale challenges — compact, large labels."""
    W, H = 900, 340
    im = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)

    mx = 450
    d.line([(mx, 40), (mx, 210)], fill=(110, 115, 125), width=7)
    d.line([(140, 100), (760, 100)], fill=(110, 115, 125), width=7)
    d.ellipse((mx - 18, 82, mx + 18, 118), fill=(180, 185, 192), outline=(80, 85, 95), width=3)
    d.polygon([(mx - 48, 210), (mx + 48, 210), (mx + 70, 270), (mx - 70, 270)],
              fill=(198, 202, 208), outline=(90, 95, 105), width=3)

    lx = 250
    d.ellipse((lx - 78, 88, lx + 78, 148), fill=(255, 225, 205), outline=C_ORANGE, width=5)
    d.line([(lx, 96), (lx, 60)], fill=C_ORANGE, width=4)
    d.ellipse((lx - 22, 18, lx + 22, 62), outline=C_ORANGE, width=4)
    d.ellipse((lx - 8, 32, lx + 8, 48), fill=C_ORANGE)
    d.polygon([(lx, 62), (lx - 14, 92), (lx + 14, 92)], outline=C_ORANGE, width=3)
    d.text((lx, 172), "Empty Geo Maps", font=font(28, True), fill=C_ORANGE, anchor="mm")
    d.text((lx, 204), "(Gmail hides IP)", font=font(20), fill=(70, 75, 85), anchor="mm")
    d.text((lx, 310), "Connectivity of hops", font=font(24, True), fill=(35, 40, 50), anchor="mm")

    rx = 650
    d.ellipse((rx - 78, 88, rx + 78, 148), fill=(234, 220, 248), outline=C_PURPLE, width=5)
    d.line([(rx, 96), (rx, 60)], fill=C_PURPLE, width=4)
    d.rectangle((rx - 26, 55, rx - 12, 100), fill=C_PURPLE)
    d.rectangle((rx - 7, 42, rx + 7, 100), fill=C_PURPLE)
    d.rectangle((rx + 12, 28, rx + 26, 100), fill=C_PURPLE)
    d.text((rx, 172), "Score Noise", font=font(28, True), fill=C_PURPLE, anchor="mm")
    d.text((rx, 204), "(CDN / newsletters)", font=font(20), fill=(70, 75, 85), anchor="mm")
    d.text((rx, 310), "Adoption / trust risks", font=font(24, True), fill=(35, 40, 50), anchor="mm")

    im = _crop_white(im, pad=6)
    im = _pad_to_aspect(im, 6.2 / 2.2)
    im.save(path)
    return path


def make_overcome_diagram(path: Path):
    """Overcoming branch — large teal cards like DevWise."""
    W, H = 860, 680
    im = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)

    sx0, sy0, sx1, sy1 = 28, 250, 270, 450
    rounded_rect(d, (sx0, sy0, sx1, sy1), 20, fill=(236, 236, 236), outline=(90, 95, 105), width=4)
    d.polygon([(95, 295), (95, 385), (155, 340)], fill=C_CYAN)
    d.line([(95, 295), (95, 415)], fill=(60, 65, 75), width=4)
    d.text((185, 335), "Overcoming", font=font(24, True), fill=(30, 35, 45), anchor="mm")
    d.text((185, 370), "Challenges", font=font(24, True), fill=(30, 35, 45), anchor="mm")

    cards = [
        (85, "Caption empty maps\nas expected (no IPv4)", C_CYAN, "geo"),
        (280, "Demo lab traces +\nreal Show original", C_GREEN, "ingest"),
        (475, "Explainable rules now;\nML-ready features later", C_ORANGE, "analysis"),
    ]

    trunk_x = 315
    d.line([(sx1, 350), (trunk_x, 350)], fill=(60, 65, 75), width=6)
    d.line([(trunk_x, 125), (trunk_x, 575)], fill=(60, 65, 75), width=6)

    for y, label, col, ikind in cards:
        mid_y = y + 60
        d.line([(trunk_x, mid_y), (370, mid_y)], fill=(60, 65, 75), width=6)
        d.polygon([(370, mid_y), (354, mid_y - 12), (354, mid_y + 12)], fill=col)
        # DevWise-like: light blue cards with colored text
        rounded_rect(d, (380, y + 8, 830, y + 112), 18, fill=(230, 242, 250), outline=C_BLUE, width=4)
        d.ellipse((400, mid_y - 26, 452, mid_y + 26), fill=(255, 255, 255), outline=col, width=3)
        draw_mini_icon(d, ikind, 426, mid_y, col)
        d.text((620, mid_y), label, font=font(26, True), fill=C_CYAN, anchor="mm", align="center")

    im = _crop_white(im, pad=8)
    im = _pad_to_aspect(im, 5.8 / 5.15)
    im.save(path)
    return path


def icon_person_book(d, x, y, col):
    d.ellipse((x - 5, y - 16, x + 5, y - 6), outline=col, width=2)
    d.arc((x - 12, y - 4, x + 12, y + 16), 200, 340, fill=col, width=2)
    d.line([(x - 10, y + 4), (x + 10, y + 4)], fill=col, width=2)


def icon_teacher(d, x, y, col):
    d.ellipse((x - 5, y - 16, x + 5, y - 6), outline=col, width=2)
    d.rectangle((x - 14, y - 2, x + 14, y + 12), outline=col, width=2)
    d.line([(x - 8, y + 4), (x + 8, y + 4)], fill=col, width=1)


def icon_people(d, x, y, col):
    d.ellipse((x - 10, y - 14, x - 2, y - 6), outline=col, width=2)
    d.ellipse((x + 2, y - 14, x + 10, y - 6), outline=col, width=2)
    d.arc((x - 14, y - 2, x, y + 14), 200, 340, fill=col, width=2)
    d.arc((x, y - 2, x + 14, y + 14), 200, 340, fill=col, width=2)


def icon_social(d, x, y, col):
    d.ellipse((x - 14, y - 6, x - 2, y + 6), outline=col, width=2)
    d.ellipse((x + 2, y - 6, x + 14, y + 6), outline=col, width=2)
    d.line([(x - 2, y), (x + 2, y)], fill=col, width=2)


def icon_economic(d, x, y, col):
    d.ellipse((x - 8, y - 2, x + 8, y + 14), outline=col, width=2)
    d.line([(x, y - 10), (x, y)], fill=col, width=2)
    d.line([(x - 6, y + 16), (x + 6, y + 16)], fill=col, width=2)


def icon_leaf(d, x, y, col):
    d.ellipse((x - 10, y - 12, x + 10, y + 10), outline=col, width=2)
    d.line([(x, y + 10), (x, y - 8)], fill=col, width=2)


def icon_shield(d, x, y, col):
    d.polygon(
        [(x, y - 16), (x + 12, y - 8), (x + 10, y + 8), (x, y + 16), (x - 10, y + 8), (x - 12, y - 8)],
        outline=col,
        width=2,
    )


def make_lens_diagram(path: Path, title: str, inputs: list[tuple], output: str, colors):
    """DevWise-style convergence lens diagram on black with line icons."""
    W, H = 900, 480
    im = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((W // 2, 28), title, font=font(18), fill=(160, 160, 160), anchor="mm")

    lx, ly = 500, 250
    d.ellipse((lx - 40, ly - 130, lx + 40, ly + 130), outline=(210, 210, 210), width=2)
    d.ellipse((lx - 22, ly - 130, lx + 55, ly + 130), outline=(170, 170, 170), width=1)

    ys = [120, 250, 380]
    icon_fns = {
        "book": icon_person_book,
        "teacher": icon_teacher,
        "people": icon_people,
        "social": icon_social,
        "econ": icon_economic,
        "leaf": icon_leaf,
        "shield": icon_shield,
    }
    for item, y, col in zip(inputs, ys, colors):
        label, _, ikey = item[0], item[1], item[2]
        icon_fns.get(ikey, icon_shield)(d, 320, y, col)
        d.text((295, y), label, font=font(14), fill=(185, 185, 185), anchor="rm")
        d.line([(338, y), (lx - 35, y)], fill=col, width=2)
        d.line([(lx + 42, y), (640, 250)], fill=col, width=2)

    icon_shield(d, 660, 250, (190, 190, 190))
    d.text((685, 250), output, font=font(14), fill=(185, 185, 185), anchor="lm")
    im.save(path)
    return path


# -------------------- ppt helpers --------------------

def set_run(paragraph, text, size=12, bold=False, color=INK, name="Calibri"):
    if paragraph.runs:
        paragraph.runs[0].text = text
        for r in paragraph.runs[1:]:
            r.text = ""
        run = paragraph.runs[0]
    else:
        run = paragraph.add_run()
        run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = name
    return run


def clear_shape_text(shape):
    if shape.has_text_frame:
        for p in shape.text_frame.paragraphs:
            set_run(p, "", size=10)


def hide_shape(shape):
    """Move off-canvas."""
    shape.left = Inches(20)
    shape.top = Inches(20)


def add_border_box(slide, left, top, width, height):
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    sh.fill.solid()
    sh.fill.fore_color.rgb = WHITE
    sh.line.color.rgb = BORDER_BLUE
    sh.line.width = Pt(1.5)
    # soften corners
    try:
        sh.adjustments[0] = 0.05
    except Exception:
        pass
    return sh


def add_textbox(slide, left, top, width, height, lines, size=12, bold_first=False, head_size=None):
    """DevWise-matched sizes: body ~12pt, section heads ~15pt, bold labels ~12pt."""
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    hsz = head_size if head_size is not None else size + 3
    for i, item in enumerate(lines):
        if isinstance(item, tuple):
            kind, text = item
        else:
            kind, text = "b", item
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.level = 0
        if kind == "h":
            set_run(p, text, size=hsz, bold=True, color=INK, name="Times New Roman")
            p.space_after = Pt(6)
            p.space_before = Pt(2)
        elif kind == "bh":
            set_run(p, text, size=size, bold=True, color=INK, name="Times New Roman")
            p.space_after = Pt(2)
        else:
            set_run(p, text, size=size, bold=False, color=INK, name="Calibri")
            p.space_after = Pt(5)
    return box


def oval_team(slide):
    for sh in slide.shapes:
        if not sh.has_text_frame:
            continue
        txt = sh.text_frame.text.strip()
        if txt in ("Your Team Name", TEAM, "DevWise") or "Team Name" in txt:
            set_run(sh.text_frame.paragraphs[0], TEAM, size=9, bold=True, color=INK)


def set_title(slide, text):
    for sh in slide.shapes:
        if sh.has_text_frame and sh.name.startswith("Title"):
            set_run(sh.text_frame.paragraphs[0], text, size=28, bold=True, color=INK, name="Georgia")
            return sh


def delete_slide(prs, index):
    rId = prs.slides._sldIdLst[index].get(qn("r:id"))
    prs.part.drop_rel(rId)
    prs.slides._sldIdLst.remove(prs.slides._sldIdLst[index])


def fill_title_page(slide):
    for sh in slide.shapes:
        if sh.name == "TextBox 9":
            lines = [
                "",
                "Problem Statement ID – SIH26106",
                "Problem Statement Title – AI-Powered Email Threat Detection, GeoLocation and Forensic Intelligence Platform",
                "Theme – Blockchain & Cybersecurity",
                "PS Category – Software",
                "Team ID – [Fill from SIH portal]",
                "Team Name (Registered on portal) – prajjwaldubey",
            ]
            tf = sh.text_frame
            paras = list(tf.paragraphs)
            for i, line in enumerate(lines):
                if i < len(paras):
                    p = paras[i]
                else:
                    p = tf.add_paragraph()
                set_run(p, line, size=15 if i == 2 else 16, bold=True, color=INK)
            return


def clear_body_placeholder(slide):
    for sh in slide.shapes:
        if sh.name == "TextBox 8":
            hide_shape(sh)


def build():
    # assets
    # Real MailTrace favicon (hi-res) — not the old generated envelope logo
    fav = ASSETS / "mailtrace_favicon.png"
    if not fav.exists():
        # fallback regenerate via make_favicon algorithm
        make_mailtrace_logo(ASSETS / "mailtrace_logo.png")
        logo = ASSETS / "mailtrace_logo.png"
    else:
        logo = fav
    wf = make_workflow_diagram(ASSETS / "workflow.png")
    ts = make_techstack_diagram(ASSETS / "techstack.png")
    feas = make_feasibility_diagram(ASSETS / "feasibility.png")
    chal = make_challenges_diagram(ASSETS / "challenges.png")
    over = make_overcome_diagram(ASSETS / "overcome.png")
    lens1 = make_lens_diagram(
        ASSETS / "lens_impact.png",
        "Campus Email Defence",
        [
            ("Faster triage for SOC / IT", C_BLUE, "teacher"),
            ("Clear do-not-pay guidance", C_GREEN, "book"),
            ("CERT-style single-mail review", (120, 190, 80), "people"),
        ],
        "Safer institute email response",
        [C_BLUE, C_GREEN, (120, 190, 80)],
    )
    lens2 = make_lens_diagram(
        ASSETS / "lens_benefits.png",
        "Solution Benefits",
        [
            ("Social", C_BLUE, "social"),
            ("Economic", C_GREEN, "econ"),
            ("Environmental", (140, 200, 90), "leaf"),
        ],
        "Positive Impact",
        [C_BLUE, C_GREEN, (140, 200, 90)],
    )

    prs = Presentation(str(SRC))
    s1, s2, s3, s4, s5, s6 = (prs.slides[i] for i in range(6))

    # --- 1 title ---
    fill_title_page(s1)

    # --- 2 idea (3 boxes) ---
    clear_body_placeholder(s2)
    set_title(s2, "")  # title replaced by logo+name
    # hide original title text by clearing
    for sh in s2.shapes:
        if sh.name.startswith("Title"):
            clear_shape_text(sh)
            hide_shape(sh)
    oval_team(s2)

    # favicon + MailTrace title (DevWise center-brand style)
    s2.shapes.add_picture(str(logo), Inches(5.55), Inches(0.12), Inches(0.85), Inches(0.85))
    tbox = s2.shapes.add_textbox(Inches(6.5), Inches(0.22), Inches(4.2), Inches(0.7))
    set_run(tbox.text_frame.paragraphs[0], "MailTrace", size=32, bold=True, color=INK, name="Times New Roman")

    # left tall box
    add_border_box(s2, Inches(0.35), Inches(1.15), Inches(6.2), Inches(5.55))
    add_textbox(
        s2,
        Inches(0.5),
        Inches(1.25),
        Inches(5.9),
        Inches(5.3),
        [
            ("h", "Proposed Solution:"),
            ("b", "• Develop a comprehensive web platform that analyses original emails (paste or .eml upload), focusing on improving institutional email security through technology."),
            ("b", "• Features include SPF/DKIM/DMARC checks, scam-language cues, lookalike domain spotting, hop-path geolocation, explainable risk score, and a downloadable forensic PDF."),
            ("h", "Detection, Trace & Forensics:"),
            ("bh", "• Threat Scoring:"),
            ("b", "  Integration of authentication stamps with content cues; identifies trends and labels legitimate / suspicious / impersonated / phishing / fraud."),
            ("bh", "• Path Mapping:"),
            ("b", "  Rebuilds the Received-header chain and plots public IPs with city, country, and ISP."),
            ("bh", "• Case Vault:"),
            ("b", "  Digital case store with file fingerprint, minimising rework and promoting shared review across SOC/admin teams."),
        ],
        size=12,
        head_size=15,
    )

    # top right
    add_border_box(s2, Inches(6.75), Inches(1.15), Inches(6.2), Inches(2.55))
    add_textbox(
        s2,
        Inches(6.9),
        Inches(1.25),
        Inches(5.9),
        Inches(2.35),
        [
            ("h", "How it Addresses the Problem:"),
            ("bh", "• Detection Engine:"),
            ("b", "  Spots phishing, BEC, and spoofed mail using headers + body patterns, helping institutes catch fraud before users click."),
            ("bh", "• GeoLocation Module:"),
            ("b", "  Shows where mail servers sat along the path — useful for investigation without naming a person’s home address."),
            ("bh", "• Forensic Report:"),
            ("b", "  Ready PDF with score, reasons, stamps, and map for tickets and incident response."),
        ],
        size=12,
        head_size=15,
    )

    # bottom right
    add_border_box(s2, Inches(6.75), Inches(3.85), Inches(6.2), Inches(2.85))
    add_textbox(
        s2,
        Inches(6.9),
        Inches(3.95),
        Inches(5.9),
        Inches(2.65),
        [
            ("h", "Innovation and Uniqueness:"),
            ("b", "• End-to-end flow: detection + map + PDF in one laptop tool."),
            ("b", "• Explainable score — every point has a written reason."),
            ("b", "• Honest geo: mail servers / ISP only, not personal identity."),
            ("b", "• Works on real Gmail “Show original” and .eml files."),
            ("b", "• Graph of domains, IPs, and clues for campaign-style review."),
            ("b", "• No mailbox login; user pastes the mail they already received."),
            ("b", "• Chain-of-custody fingerprint for investigative integrity."),
        ],
        size=12,
        head_size=15,
    )

    # --- 3 technical ---
    clear_body_placeholder(s3)
    set_title(s3, "TECHNICAL APPROACH")
    oval_team(s3)
    add_border_box(s3, Inches(0.25), Inches(1.15), Inches(6.4), Inches(5.55))
    add_border_box(s3, Inches(6.85), Inches(1.15), Inches(6.2), Inches(5.55))
    # tech-stack heading
    h = s3.shapes.add_textbox(Inches(8.6), Inches(1.25), Inches(2.8), Inches(0.35))
    p = h.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    set_run(p, "Tech-Stack", size=16, bold=True, color=INK, name="Georgia")
    # underline via thin shape
    line = s3.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(9.15), Inches(1.55), Inches(1.6), Inches(0.03))
    line.fill.solid()
    line.fill.fore_color.rgb = INK
    line.line.fill.background()

    s3.shapes.add_picture(str(wf), Inches(0.35), Inches(1.25), Inches(6.2), Inches(5.35))
    s3.shapes.add_picture(str(ts), Inches(6.95), Inches(1.65), Inches(6.0), Inches(4.95))

    # --- 4 feasibility ---
    clear_body_placeholder(s4)
    set_title(s4, "FEASIBILITY AND VIABILITY")
    oval_team(s4)
    add_border_box(s4, Inches(0.28), Inches(1.05), Inches(6.55), Inches(2.9))
    add_border_box(s4, Inches(0.28), Inches(4.1), Inches(6.55), Inches(2.7))
    add_border_box(s4, Inches(7.0), Inches(1.05), Inches(6.0), Inches(5.75))

    # section titles centered like DevWise
    t = s4.shapes.add_textbox(Inches(0.35), Inches(1.08), Inches(6.4), Inches(0.32))
    t.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    set_run(t.text_frame.paragraphs[0], "Feasibility", size=16, bold=True, color=INK, name="Times New Roman")
    u = s4.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(2.95), Inches(1.38), Inches(1.2), Inches(0.025))
    u.fill.solid(); u.fill.fore_color.rgb = INK; u.line.fill.background()
    s4.shapes.add_picture(str(feas), Inches(0.38), Inches(1.45), Inches(6.35), Inches(2.4))

    t = s4.shapes.add_textbox(Inches(0.35), Inches(4.12), Inches(6.4), Inches(0.32))
    t.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    set_run(t.text_frame.paragraphs[0], "Challenges and Risks", size=16, bold=True, color=INK, name="Times New Roman")
    u = s4.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(2.45), Inches(4.42), Inches(2.2), Inches(0.025))
    u.fill.solid(); u.fill.fore_color.rgb = INK; u.line.fill.background()
    s4.shapes.add_picture(str(chal), Inches(0.45), Inches(4.5), Inches(6.2), Inches(2.2))

    t = s4.shapes.add_textbox(Inches(7.05), Inches(1.08), Inches(5.9), Inches(0.32))
    t.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    set_run(t.text_frame.paragraphs[0], "Overcoming Challenges", size=16, bold=True, color=INK, name="Times New Roman")
    u = s4.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(8.45), Inches(1.38), Inches(3.1), Inches(0.025))
    u.fill.solid(); u.fill.fore_color.rgb = INK; u.line.fill.background()
    s4.shapes.add_picture(str(over), Inches(7.1), Inches(1.45), Inches(5.8), Inches(5.25))

    # --- 5 impact ---
    clear_body_placeholder(s5)
    set_title(s5, "IMPACT AND BENEFITS")
    oval_team(s5)
    add_border_box(s5, Inches(0.3), Inches(1.15), Inches(6.35), Inches(5.55))
    add_border_box(s5, Inches(6.85), Inches(1.15), Inches(6.15), Inches(5.55))

    add_textbox(
        s5,
        Inches(0.45),
        Inches(1.25),
        Inches(6.05),
        Inches(2.2),
        [
            ("h", "Potential Impact on the Target Audience:"),
            ("b", "• Improved threat awareness and faster triage of fake dean, GST, invoice, and internship-scam mail for college / institute SOC and IT admin."),
            ("b", "• Empowerment of students and staff with a clear “do not pay / click” vs “looks legitimate” view."),
            ("b", "• Enhanced readiness for CERT-style review of a single suspicious message without reading raw headers by hand."),
        ],
        size=12,
    )
    s5.shapes.add_picture(str(lens1), Inches(0.55), Inches(3.55), Inches(5.9), Inches(2.9))

    add_textbox(
        s5,
        Inches(7.0),
        Inches(1.25),
        Inches(5.85),
        Inches(2.0),
        [
            ("h", "Benefits of the Solution:"),
            ("b", "• Social: Bridges the gap between spam filters and real investigation; promotes safer campus email use."),
            ("b", "• Economic: Cuts fraud loss and analyst time per ticket; PDF supports internal records."),
            ("b", "• Environmental: Reduces paper usage with digital forensic reports."),
        ],
        size=12,
    )
    s5.shapes.add_picture(str(lens2), Inches(7.05), Inches(3.55), Inches(5.75), Inches(2.9))

    # --- 6 research ---
    clear_body_placeholder(s6)
    set_title(s6, "RESEARCH AND REFERENCES")
    oval_team(s6)
    # vertical divider
    div = s6.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(6.65), Inches(1.3), Inches(0.02), Inches(5.3))
    div.fill.solid()
    div.fill.fore_color.rgb = BORDER_BLUE
    div.line.fill.background()

    add_textbox(
        s6,
        Inches(0.45),
        Inches(1.35),
        Inches(5.9),
        Inches(5.2),
        [
            ("h", "Email Authentication Standards"),
            ("bh", "• RFC 7208 — SPF"),
            ("b", "  How receivers check if a host may send for a domain."),
            ("b", "  https://datatracker.ietf.org/doc/html/rfc7208"),
            ("bh", "• RFC 6376 — DKIM"),
            ("b", "  Cryptographic signature so body/headers can be verified."),
            ("b", "  https://datatracker.ietf.org/doc/html/rfc6376"),
            ("bh", "• RFC 7489 — DMARC"),
            ("b", "  Policy aligning SPF/DKIM with the visible From domain."),
            ("b", "  https://datatracker.ietf.org/doc/html/rfc7489"),
        ],
        size=12,
    )
    add_textbox(
        s6,
        Inches(6.9),
        Inches(1.35),
        Inches(5.9),
        Inches(5.2),
        [
            ("h", "Threat Landscape and Practice"),
            ("bh", "• CERT-In / MeitY advisories"),
            ("b", "  Guidance on phishing and business email compromise in India."),
            ("b", "  https://www.cert-in.org.in/"),
            ("bh", "• APWG Phishing Activity Trends"),
            ("b", "  Shows volume of credential and payment fraud mail."),
            ("b", "  https://apwg.org/"),
            ("bh", "• RFC 5321 — SMTP"),
            ("b", "  Mail is relayed; Received chain is servers, not a person’s house."),
            ("b", "  https://datatracker.ietf.org/doc/html/rfc5321"),
        ],
        size=12,
    )

    if len(prs.slides) >= 7:
        delete_slide(prs, 6)

    prs.save(str(DST))
    print("saved", DST)


if __name__ == "__main__":
    build()
