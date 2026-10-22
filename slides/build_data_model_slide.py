"""
One slide: what data the dashboard joins, and the model outline (a simpler version of the team's slide 13).

    python slides/build_data_model_slide.py   -> slides/data_and_model_slide.pptx

Uses the team masters and the helpers in build_dashboard_segment.py. The four headline counts are the team slide's own.
"""
from pathlib import Path

from pptx.enum.text import MSO_ANCHOR, PP_ALIGN

import build_dashboard_segment as B
from build_dashboard_segment import (BODY, CB, FB, FL, FR, FT, FW, GRID, MUTED, NAVY, NAVY_TEXT, Deck, _sub, line,
                                     rect, bar_label, text)

HERE = Path(__file__).resolve().parent
NUM_BLUE, HEAD = "3D63B0", "Franklin Gothic Medium"

d = Deck(HERE / "render" / "team_capstone_deck.pptx")
d.prs.part.drop_rel(d.title_slide.rId)              # this file holds the one slide only
d.order.remove(d.title_slide)
s = d.content("The dashboard links aid, budgets and health data to show coverage at risk")

# 1. four headline counts
stats = [("26", "datasets"), ("16", "organizations"), ("32", "published studies"), ("70", "countries")]
sw = FW // 4
for i, (n, lab) in enumerate(stats):
    x = FL + i * sw
    text(s, x, FT + 60000, sw, 560000, [[(n + " ", {"size": 34, "color": NUM_BLUE, "font": HEAD}),
                                         (lab, {"size": 18, "color": NAVY_TEXT})]], anchor=MSO_ANCHOR.BOTTOM)
y0 = FT + 760000
line(s, FL, y0, FR, y0, color=GRID, width=1.0)

# 2. left: the data, three plain rows
gut = 457200
lw = (FW - gut) * 52 // 100
rx = FL + lw + gut
rw = FR - rx
top = y0 + 200000
text(s, FL, top, lw, 380000, ["The data"], size=20, color=NAVY_TEXT, font=HEAD)
data = [("Money", "Aid by donor and channel; government budgets",
         "IHME DAH and Health Spending, IMF WEO, World Bank, KFF MOUs"),
        ("Need and coverage", "People who need each service, and who gets it",
         "UNAIDS, WHO, Malaria Atlas Project, WUENIC, UN population"),
        ("Costs and effects", "Cost per person served; what losing care does",
         "GHCC unit costs, Global Fund budgets, Optima HIV, LiST, VIMC")]
rh = (CB - top - 460000) // 3
for k, (h, what, src) in enumerate(data):
    y = top + 460000 + k * rh
    line(s, FL, y, FL, y + rh - 120000, color=NUM_BLUE, width=3.0)
    text(s, FL + 140000, y, lw - 140000, rh - 120000,
         [[(h, {"bold": True, "color": NAVY_TEXT, "size": 18})], [(what, {"size": 16})],
          [(src, {"size": 13, "color": MUTED})]], spacing=3, anchor=MSO_ANCHOR.MIDDLE)

# 3. right: the model, three steps top to bottom, fiscal space feeding the middle step
text(s, rx, top, rw, 380000, ["The model"], size=20, color=NAVY_TEXT, font=HEAD)
steps = ["Expected aid retreat", "Coverage lost by service", "Coverage gap that remains"]
bw, bh = rw * 62 // 100, 560000
area = CB - top - 460000
gap = (area - 3 * bh) // 2
ys = [top + 460000 + k * (bh + gap) for k in range(3)]
for k, (t, y) in enumerate(zip(steps, ys)):
    bar_label(rect(s, rx, y, bw, bh, NAVY), t, size=17, align=PP_ALIGN.CENTER)
    if k < 2:
        a = line(s, rx + bw // 2, y + bh, rx + bw // 2, ys[k + 1], color=NAVY, width=1.5)
        _sub(a.line._get_or_add_ln(), "a:tailEnd", type="triangle")
# the question sits beside the arrow into "Coverage lost by service"
qx, qw = rx + bw + 182880, rw - bw - 182880
qy = ys[1] + bh // 2 - 450000
q = rect(s, qx, qy, qw, 900000, "DDE7F8")
bar_label(q, "Can fiscal space fill the gap?", size=15, color=NAVY_TEXT, align=PP_ALIGN.CENTER)
a = line(s, qx, ys[1] + bh // 2, rx + bw, ys[1] + bh // 2, color="A85A32", width=1.5)
_sub(a.line._get_or_add_ln(), "a:tailEnd", type="triangle")

out = HERE / "data_and_model_slide.pptx"
d.save(out, ["Left: the three kinds of data the dashboard joins for 70 countries. Right: the model in three steps; "
                 "the government's fiscal space is netted off the lost aid before coverage loss is counted."])
print("wrote", out)
