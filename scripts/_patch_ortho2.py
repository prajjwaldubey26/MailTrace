"""Force icon-side straight joins + better obstacle dodge."""
from pathlib import Path

p = Path(r"C:\Users\prajj\Documents\proto.SIH\scripts\build_mailtrace_devwise_style.py")
text = p.read_text(encoding="utf-8")

start = text.index("def orthogonal_to_icon(")
# replace through dashed_polyline function end
end = text.index("def draw_mini_icon(")

new = r'''def orthogonal_to_icon(hub_box, pill_box, obstacles=None, tree_side="below"):
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


'''

# Keep draw_mini_icon intact
p.write_text(text[:start] + new + text[end:], encoding="utf-8")

# Update call sites to pass tree_side
text = p.read_text(encoding="utf-8")
text = text.replace(
    "pts = orthogonal_to_icon(hub_box, pill, obstacles=others)",
    "pts = orthogonal_to_icon(hub_box, pill, obstacles=others, tree_side=side)",
)
p.write_text(text, encoding="utf-8")
print("icon-side orthogonal routing updated")
