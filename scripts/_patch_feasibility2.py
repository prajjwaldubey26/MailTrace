"""Large-font dense Feasibility / Challenges / Overcome diagrams."""
from pathlib import Path

p = Path(r"C:\Users\prajj\Documents\proto.SIH\scripts\build_mailtrace_devwise_style.py")
text = p.read_text(encoding="utf-8")
start = text.index("def make_feasibility_diagram(")
end = text.index("def icon_person_book(")

new = '''def make_feasibility_diagram(path: Path):
    """Dense DevWise feasibility map — large type so it stays readable when scaled."""
    W, H = 1280, 420
    im = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)

    cx, cy = 640, 250
    hub_w, hub_h = 360, 170
    hub_box = (cx - hub_w // 2, cy - hub_h // 2, cx + hub_w // 2, cy + hub_h // 2)
    rounded_rect(d, hub_box, 20, fill=(236, 236, 236), outline=(100, 105, 115), width=5)
    d.ellipse((cx - 26, cy - 58, cx - 6, cy - 38), outline=(65, 70, 80), width=3)
    d.ellipse((cx + 6, cy - 58, cx + 26, cy - 38), outline=(65, 70, 80), width=3)
    d.arc((cx - 34, cy - 38, cx - 0, cy - 8), 200, 340, fill=(65, 70, 80), width=3)
    d.arc((cx + 0, cy - 38, cx + 34, cy - 8), 200, 340, fill=(65, 70, 80), width=3)
    d.text((cx, cy + 10), "Feasibility Analysis of", font=font(22), fill=(55, 60, 70), anchor="mm")
    d.text((cx, cy + 44), "MailTrace Platform", font=font(28, True), fill=(25, 30, 40), anchor="mm")

    def big_pill(bx, by, title, color, icon_kind):
        fnt = font(26, True)
        tw, th = text_size(d, title, fnt)
        icon_w, pad_x, pad_y = 44, 20, 16
        w = tw + icon_w + pad_x * 2 + 18
        h = max(th + pad_y * 2, 62)
        box = (bx - w // 2, by - h // 2, bx + w // 2, by + h // 2)
        rounded_rect(d, box, 16, fill=pastel(color, 175), outline=color, width=5)
        ix = bx - w // 2 + pad_x + 14
        draw_mini_icon(d, icon_kind, ix, by, color)
        d.text((ix + 22, by), title, font=fnt, fill=color, anchor="lm")
        return box

    def big_tree(pill_box, items):
        x0 = pill_box[0] + 30
        y0 = pill_box[3] + 8
        fnt = font(22)
        line_h = 34
        total = len(items) * line_h + 8
        dashed_line(d, (x0, y0), (x0, y0 + total), fill=(100, 105, 115), width=3, dash=6, gap=4)
        for i, it in enumerate(items):
            yi = y0 + 20 + i * line_h
            dashed_line(d, (x0, yi), (x0 + 22, yi), fill=(100, 105, 115), width=3, dash=6, gap=4)
            d.text((x0 + 30, yi), it, font=fnt, fill=(40, 45, 55), anchor="lm")

    left_pos, right_pos = (250, 85), (1030, 85)
    left_box = big_pill(left_pos[0], left_pos[1], "Software & Cloud", C_GREEN, "runtime")
    right_box = big_pill(right_pos[0], right_pos[1], "Current Technology", C_BLUE, "backend")

    for pill in (left_box, right_box):
        pts = orthogonal_to_icon(hub_box, pill, obstacles=[], tree_side="below")
        dashed_polyline(d, pts, fill=(100, 105, 115), width=4, dash=9, gap=5)

    big_tree(left_box, ["Laptop demo ready", "No RF hardware", "No classified data"])
    big_tree(right_box, ["Header forensics", "NLP scam cues", "Hop geolocation"])

    im = _crop_white(im, pad=12)
    im.save(path)
    return path


def make_challenges_diagram(path: Path):
    """Compact colorful balance scale — large labels."""
    W, H = 1000, 380
    im = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)

    mx = 500
    d.line([(mx, 70), (mx, 250)], fill=(115, 120, 130), width=7)
    d.line([(180, 130), (820, 130)], fill=(115, 120, 130), width=7)
    d.ellipse((mx - 18, 112, mx + 18, 148), fill=(185, 190, 198), outline=(85, 90, 100), width=3)
    d.polygon(
        [(mx - 48, 250), (mx + 48, 250), (mx + 72, 310), (mx - 72, 310)],
        fill=(200, 205, 210),
        outline=(95, 100, 110),
        width=3,
    )

    lx = 280
    d.ellipse((lx - 78, 122, lx + 78, 178), fill=(255, 228, 210), outline=C_ORANGE, width=6)
    d.line([(lx, 130), (lx, 95)], fill=C_ORANGE, width=4)
    d.ellipse((lx - 22, 42, lx + 22, 86), outline=C_ORANGE, width=5)
    d.ellipse((lx - 8, 56, lx + 8, 72), fill=C_ORANGE)
    d.polygon([(lx, 86), (lx - 16, 118), (lx + 16, 118)], outline=C_ORANGE, width=4)
    d.text((lx, 210), "Empty Geo Maps", font=font(26, True), fill=C_ORANGE, anchor="mm")
    d.text((lx, 242), "(Gmail hides IP)", font=font(20), fill=(75, 80, 90), anchor="mm")
    d.text((lx, 345), "Connectivity of hops", font=font(22, True), fill=(40, 45, 55), anchor="mm")

    rx = 720
    d.ellipse((rx - 78, 122, rx + 78, 178), fill=(236, 222, 250), outline=C_PURPLE, width=6)
    d.line([(rx, 130), (rx, 95)], fill=C_PURPLE, width=4)
    d.rectangle((rx - 26, 78, rx - 12, 118), fill=C_PURPLE)
    d.rectangle((rx - 7, 62, rx + 7, 118), fill=C_PURPLE)
    d.rectangle((rx + 12, 48, rx + 26, 118), fill=C_PURPLE)
    d.text((rx, 210), "Score Noise", font=font(26, True), fill=C_PURPLE, anchor="mm")
    d.text((rx, 242), "(CDN / newsletters)", font=font(20), fill=(75, 80, 90), anchor="mm")
    d.text((rx, 345), "Adoption / trust risks", font=font(22, True), fill=(40, 45, 55), anchor="mm")

    im = _crop_white(im, pad=8)
    im.save(path)
    return path


def make_overcome_diagram(path: Path):
    """Large-type overcoming branch with colorful solution cards."""
    W, H = 900, 700
    im = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)

    sx0, sy0, sx1, sy1 = 30, 250, 280, 450
    rounded_rect(d, (sx0, sy0, sx1, sy1), 20, fill=(236, 236, 236), outline=(95, 100, 110), width=5)
    d.polygon([(100, 295), (100, 380), (165, 338)], fill=C_CYAN)
    d.line([(100, 295), (100, 410)], fill=(65, 70, 80), width=5)
    d.text((195, 335), "Overcoming", font=font(24, True), fill=(30, 35, 45), anchor="mm")
    d.text((195, 372), "Challenges", font=font(24, True), fill=(30, 35, 45), anchor="mm")

    cards = [
        (80, "Caption empty maps\\nas expected (no IPv4)", C_CYAN, "geo"),
        (280, "Demo lab traces +\\nreal Show original", C_GREEN, "ingest"),
        (480, "Explainable rules now;\\nML-ready features later", C_ORANGE, "analysis"),
    ]

    trunk_x = 330
    d.line([(sx1, 350), (trunk_x, 350)], fill=(65, 70, 80), width=6)
    d.line([(trunk_x, 120), (trunk_x, 580)], fill=(65, 70, 80), width=6)

    for y, label, col, ikind in cards:
        mid_y = y + 60
        d.line([(trunk_x, mid_y), (390, mid_y)], fill=(65, 70, 80), width=6)
        d.polygon([(390, mid_y), (374, mid_y - 12), (374, mid_y + 12)], fill=col)
        rounded_rect(d, (398, y + 8, 870, y + 112), 18, fill=pastel(col, 170), outline=col, width=5)
        d.ellipse((418, mid_y - 26, 470, mid_y + 26), fill=(255, 255, 255), outline=col, width=4)
        draw_mini_icon(d, ikind, 444, mid_y, col)
        d.text((640, mid_y), label, font=font(22, True), fill=col, anchor="mm", align="center")

    im = _crop_white(im, pad=10)
    im.save(path)
    return path


'''

# Convert \\n in the cards list into real newline escapes in the written source
new = new.replace(
    '"Caption empty maps\\nas expected (no IPv4)"',
    '"Caption empty maps\\nas expected (no IPv4)"',
)
# The above is no-op because Write already has single backslash-n in the file as \\n
# Force correct content:
new = new.replace(
    '(80, "Caption empty maps\\nas expected (no IPv4)", C_CYAN, "geo"),\n'
    '        (280, "Demo lab traces +\\nreal Show original", C_GREEN, "ingest"),\n'
    '        (480, "Explainable rules now;\\nML-ready features later", C_ORANGE, "analysis"),',
    '(80, "Caption empty maps\\nas expected (no IPv4)", C_CYAN, "geo"),\n'
    '        (280, "Demo lab traces +\\nreal Show original", C_GREEN, "ingest"),\n'
    '        (480, "Explainable rules now;\\nML-ready features later", C_ORANGE, "analysis"),',
)

text = text[:start] + new + text[end:]
p.write_text(text, encoding="utf-8")

# Post-fix overcome newlines to be real \n escapes in source
src = p.read_text(encoding="utf-8")
src = src.replace(
    '(80, "Caption empty maps\\nas expected (no IPv4)", C_CYAN, "geo"),',
    '(80, "Caption empty maps\\nas expected (no IPv4)", C_CYAN, "geo"),',
)
# Explicit byte-level fix
old_cards = (
    '(80, "Caption empty maps\\nas expected (no IPv4)", C_CYAN, "geo"),\n'
    '        (280, "Demo lab traces +\\nreal Show original", C_GREEN, "ingest"),\n'
    '        (480, "Explainable rules now;\\nML-ready features later", C_ORANGE, "analysis"),'
)
# What is actually in the file after write?
idx = src.index("Caption empty maps")
print("RAW:", repr(src[idx : idx + 70]))

# If we see double backslash, fix to single
if "maps\\\\n" in src or "maps\\nas" in repr(src[idx:idx+40]):
    pass

# Force rewrite of the three string literals using chr(10) via python rewrite of that section
import re
def fix_nl(m):
    s = m.group(0)
    return s.replace("\\\\n", "\\n")

# Safer: replace known bad double-escaped forms
src2 = src
# When file has literal backslash-n (one backslash), we're good.
# When file has two backslashes before n, fix.
src2 = src2.replace("maps\\\\nas", "maps\\nas")
src2 = src2.replace("+\\\\nreal", "+\\nreal")
src2 = src2.replace(";\\\\nML", ";\\nML")
p.write_text(src2, encoding="utf-8")
idx = p.read_text(encoding="utf-8").index("Caption empty maps")
print("AFTER:", repr(p.read_text(encoding="utf-8")[idx : idx + 70]))
print("done")
