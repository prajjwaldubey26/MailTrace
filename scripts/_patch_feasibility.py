"""Rewrite elegant Feasibility / Challenges / Overcome diagrams + restore lens icons."""
from pathlib import Path

p = Path(r"C:\Users\prajj\Documents\proto.SIH\scripts\build_mailtrace_devwise_style.py")
text = p.read_text(encoding="utf-8")
start = text.index("def make_feasibility_diagram(")
end = text.index("def make_lens_diagram(")

new = '''def make_feasibility_diagram(path: Path):
    """DevWise-style feasibility triad: hub + two category pills + item trees."""
    W, H = 1100, 460
    im = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)

    cx, cy = 550, 200
    hub_w, hub_h = 310, 150
    hub_box = (cx - hub_w // 2, cy - hub_h // 2, cx + hub_w // 2, cy + hub_h // 2)
    rounded_rect(d, hub_box, 18, fill=(236, 236, 236), outline=(110, 110, 110), width=4)
    # people cue
    d.ellipse((cx - 22, cy - 52, cx - 6, cy - 36), outline=(70, 70, 70), width=3)
    d.ellipse((cx + 6, cy - 52, cx + 22, cy - 36), outline=(70, 70, 70), width=3)
    d.arc((cx - 28, cy - 34, cx - 2, cy - 10), 200, 340, fill=(70, 70, 70), width=3)
    d.arc((cx + 2, cy - 34, cx + 28, cy - 10), 200, 340, fill=(70, 70, 70), width=3)
    d.text((cx, cy + 8), "Feasibility Analysis of", font=font(18), fill=(55, 55, 55), anchor="mm")
    d.text((cx, cy + 36), "MailTrace Platform", font=font(22, True), fill=(30, 30, 30), anchor="mm")

    left = ("Software & Cloud", C_GREEN, "runtime",
            ["Laptop demo ready", "No RF hardware", "No classified data"], (200, 95))
    right = ("Current Technology", C_BLUE, "backend",
             ["Header forensics", "NLP scam cues", "Hop geolocation"], (900, 95))

    for title, color, icon, items, (bx, by) in (left, right):
        pill = measure_pill_box(bx, by, title)
        pts = orthogonal_to_icon(hub_box, pill, obstacles=[], tree_side="below")
        dashed_polyline(d, pts, fill=(110, 110, 110), width=3, dash=8, gap=5)
        box = draw_category_pill(d, bx, by, title, color, icon)
        draw_item_tree(d, box, items, side="below")

    im = _crop_white(im, pad=14)
    im.save(path)
    return path


def make_challenges_diagram(path: Path):
    """DevWise balance-scale challenges with colored pans + icons."""
    W, H = 920, 420
    im = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)

    mx, my = 460, 200
    d.line([(mx, 95), (mx, 300)], fill=(120, 125, 135), width=6)
    d.line([(200, 150), (720, 150)], fill=(120, 125, 135), width=6)
    d.ellipse((mx - 16, 134, mx + 16, 166), fill=(190, 195, 200), outline=(90, 95, 105), width=3)
    d.polygon(
        [(mx - 40, 300), (mx + 40, 300), (mx + 62, 350), (mx - 62, 350)],
        fill=(205, 208, 212),
        outline=(100, 105, 110),
        width=3,
    )

    lx = 260
    d.ellipse((lx - 70, 145, lx + 70, 195), fill=(255, 230, 215), outline=C_ORANGE, width=5)
    d.line([(lx, 150), (lx, 118)], fill=C_ORANGE, width=3)
    d.ellipse((lx - 18, 70, lx + 18, 106), outline=C_ORANGE, width=4)
    d.ellipse((lx - 6, 82, lx + 6, 94), fill=C_ORANGE)
    d.polygon([(lx, 106), (lx - 14, 132), (lx + 14, 132)], outline=C_ORANGE, width=3)
    d.text((lx, 230), "Empty Geo Maps", font=font(20, True), fill=C_ORANGE, anchor="mm")
    d.text((lx, 258), "(Gmail hides IP)", font=font(16), fill=(80, 85, 95), anchor="mm")
    d.text((lx, 385), "Connectivity of hops", font=font(18, True), fill=(45, 50, 60), anchor="mm")

    rx = 660
    d.ellipse((rx - 70, 145, rx + 70, 195), fill=(240, 228, 250), outline=C_PURPLE, width=5)
    d.line([(rx, 150), (rx, 118)], fill=C_PURPLE, width=3)
    d.rectangle((rx - 22, 100, rx - 10, 130), fill=C_PURPLE)
    d.rectangle((rx - 6, 88, rx + 6, 130), fill=C_PURPLE)
    d.rectangle((rx + 10, 76, rx + 22, 130), fill=C_PURPLE)
    d.text((rx, 230), "Score Noise", font=font(20, True), fill=C_PURPLE, anchor="mm")
    d.text((rx, 258), "(CDN / newsletters)", font=font(16), fill=(80, 85, 95), anchor="mm")
    d.text((rx, 385), "Adoption / trust risks", font=font(18, True), fill=(45, 50, 60), anchor="mm")

    im = _crop_white(im, pad=10)
    im.save(path)
    return path


def make_overcome_diagram(path: Path):
    """DevWise overcoming branch: source node -> three colored solution cards."""
    W, H = 820, 640
    im = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)

    sx0, sy0, sx1, sy1 = 28, 230, 250, 410
    rounded_rect(d, (sx0, sy0, sx1, sy1), 18, fill=(236, 236, 236), outline=(100, 105, 115), width=4)
    d.polygon([(90, 270), (90, 340), (145, 305)], fill=C_CYAN)
    d.line([(90, 270), (90, 365)], fill=(70, 75, 85), width=4)
    d.text((175, 300), "Overcoming", font=font(20, True), fill=(35, 40, 50), anchor="mm")
    d.text((175, 332), "Challenges", font=font(20, True), fill=(35, 40, 50), anchor="mm")

    cards = [
        (70, "Caption empty maps\\nas expected (no IPv4)", C_CYAN, "geo"),
        (250, "Demo lab traces +\\nreal Show original", C_GREEN, "ingest"),
        (430, "Explainable rules now;\\nML-ready features later", C_ORANGE, "analysis"),
    ]

    trunk_x = 290
    d.line([(sx1, 320), (trunk_x, 320)], fill=(70, 75, 85), width=5)
    d.line([(trunk_x, 110), (trunk_x, 520)], fill=(70, 75, 85), width=5)

    for y, text, col, ikind in cards:
        mid_y = y + 55
        d.line([(trunk_x, mid_y), (350, mid_y)], fill=(70, 75, 85), width=5)
        d.polygon([(350, mid_y), (336, mid_y - 10), (336, mid_y + 10)], fill=col)
        rounded_rect(d, (355, y + 10, 790, y + 100), 16, fill=pastel(col, 175), outline=col, width=4)
        d.ellipse((375, mid_y - 22, 419, mid_y + 22), fill=(255, 255, 255), outline=col, width=3)
        draw_mini_icon(d, ikind, 397, mid_y, col)
        d.text((590, mid_y), text.replace("\\\\n", "\\n"), font=font(18, True), fill=col, anchor="mm", align="center")

    im = _crop_white(im, pad=12)
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


'''

# Fix the escaped newlines in overcome cards — write them as real newlines in source
new = new.replace(
    '(70, "Caption empty maps\\nas expected (no IPv4)", C_CYAN, "geo"),\n'
    '        (250, "Demo lab traces +\\nreal Show original", C_GREEN, "ingest"),\n'
    '        (430, "Explainable rules now;\\nML-ready features later", C_ORANGE, "analysis"),',
    '(70, "Caption empty maps\\nas expected (no IPv4)", C_CYAN, "geo"),\n'
    '        (250, "Demo lab traces +\\nreal Show original", C_GREEN, "ingest"),\n'
    '        (430, "Explainable rules now;\\nML-ready features later", C_ORANGE, "analysis"),',
)
# And simplify the text rendering line
new = new.replace(
    'd.text((590, mid_y), text.replace("\\\\n", "\\n"), font=font(18, True), fill=col, anchor="mm", align="center")',
    'd.text((590, mid_y), text, font=font(18, True), fill=col, anchor="mm", align="center")',
)

text = text[:start] + new + text[end:]

old_s4 = """    t = s4.shapes.add_textbox(Inches(0.42), Inches(1.15), Inches(3.5), Inches(0.32))
    set_run(t.text_frame.paragraphs[0], "Feasibility", size=16, bold=True, color=INK, name="Times New Roman")
    # underline
    u = s4.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.42), Inches(1.45), Inches(1.35), Inches(0.025))
    u.fill.solid(); u.fill.fore_color.rgb = INK; u.line.fill.background()
    s4.shapes.add_picture(str(feas), Inches(0.4), Inches(1.52), Inches(6.3), Inches(2.25))

    t = s4.shapes.add_textbox(Inches(0.42), Inches(4.1), Inches(4.2), Inches(0.32))
    set_run(t.text_frame.paragraphs[0], "Challenges and Risks", size=16, bold=True, color=INK, name="Times New Roman")
    u = s4.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.42), Inches(4.4), Inches(2.55), Inches(0.025))
    u.fill.solid(); u.fill.fore_color.rgb = INK; u.line.fill.background()
    s4.shapes.add_picture(str(chal), Inches(0.55), Inches(4.48), Inches(6.0), Inches(2.2))

    t = s4.shapes.add_textbox(Inches(7.2), Inches(1.15), Inches(4.5), Inches(0.32))
    set_run(t.text_frame.paragraphs[0], "Overcoming Challenges", size=16, bold=True, color=INK, name="Times New Roman")
    u = s4.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(7.2), Inches(1.45), Inches(2.85), Inches(0.025))
    u.fill.solid(); u.fill.fore_color.rgb = INK; u.line.fill.background()
    s4.shapes.add_picture(str(over), Inches(7.15), Inches(1.55), Inches(5.7), Inches(5.1))"""

new_s4 = """    # section titles centered like DevWise
    t = s4.shapes.add_textbox(Inches(0.35), Inches(1.12), Inches(6.4), Inches(0.36))
    t.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    set_run(t.text_frame.paragraphs[0], "Feasibility", size=18, bold=True, color=INK, name="Times New Roman")
    u = s4.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(2.85), Inches(1.46), Inches(1.4), Inches(0.03))
    u.fill.solid(); u.fill.fore_color.rgb = INK; u.line.fill.background()
    s4.shapes.add_picture(str(feas), Inches(0.38), Inches(1.55), Inches(6.35), Inches(2.25))

    t = s4.shapes.add_textbox(Inches(0.35), Inches(4.08), Inches(6.4), Inches(0.36))
    t.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    set_run(t.text_frame.paragraphs[0], "Challenges and Risks", size=18, bold=True, color=INK, name="Times New Roman")
    u = s4.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(2.35), Inches(4.42), Inches(2.4), Inches(0.03))
    u.fill.solid(); u.fill.fore_color.rgb = INK; u.line.fill.background()
    s4.shapes.add_picture(str(chal), Inches(0.45), Inches(4.5), Inches(6.2), Inches(2.2))

    t = s4.shapes.add_textbox(Inches(7.05), Inches(1.12), Inches(5.9), Inches(0.36))
    t.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    set_run(t.text_frame.paragraphs[0], "Overcoming Challenges", size=18, bold=True, color=INK, name="Times New Roman")
    u = s4.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(8.35), Inches(1.46), Inches(3.3), Inches(0.03))
    u.fill.solid(); u.fill.fore_color.rgb = INK; u.line.fill.background()
    s4.shapes.add_picture(str(over), Inches(7.1), Inches(1.55), Inches(5.8), Inches(5.15))"""

if old_s4 not in text:
    print("WARN: slide4 layout block not found exactly")
else:
    text = text.replace(old_s4, new_s4)
    print("slide4 layout updated")

p.write_text(text, encoding="utf-8")
print("feasibility diagrams + icons restored")
