"""
One slide combining "Five linked steps" and "Users can test any donor, speed and government response":
the five-step pipeline across the top; under steps 2-3, what the user sets; under steps 1, 4 and 5, the data.

    python slides/build_steps_controls_slide.py   -> slides/steps_and_controls_slide.pptx
"""
from pathlib import Path

from pptx.enum.text import MSO_ANCHOR, PP_ALIGN

from build_dashboard_segment import (BODY, CB, FL, FT, FW, GRID, MUTED, NAVY, NAVY_TEXT, Deck, bar_label, line,
                                     rect, source, text)

HERE = Path(__file__).resolve().parent
NUM_BLUE, PALE = "3D63B0", "DDE7F8"

d = Deck(HERE / "render" / "team_capstone_deck.pptx")
d.prs.part.drop_rel(d.title_slide.rId)              # this file holds the one slide only
d.order.remove(d.title_slide)
s = d.content("Five steps from a donor’s cut to lost coverage, and what users set")

steps = [("Aid Money", "By donor, channel, service"),
         ("Scenario Cut", "Who cuts, how, how fast"),
         ("Gov. Response", "What replaces lost aid"),
         ("Services Lost", "Net loss ÷ cost per person"),
         ("Coverage Change", "Lost ÷ people in need")]
data = {0: "IHME DAH 1990-2026, 2021-23 average",
        3: "Cost studies per service: GHCC, Value TB, Rosen 2021, White 2011, GiveWell, PMI, Lydon 2014, MSF (2023 US$)",
        4: "UNAIDS, WHO, MAP, WUENIC, UN WPP 2024 births"}
cw = FW // 5
dia = 760000
cy = FT + 140000 + dia // 2
line(s, FL + cw // 2, cy, FL + 4 * cw + cw // 2, cy, color=GRID, width=2.0)
for i, (name, desc) in enumerate(steps):
    cx = FL + i * cw + cw // 2
    c = s.shapes.add_shape(9, cx - dia // 2, cy - dia // 2, dia, dia)
    c.fill.solid()
    c.fill.fore_color.rgb = __import__("build_dashboard_segment").rgb(NUM_BLUE if i < 4 else NAVY)
    c.line.fill.background()
    c.shadow.inherit = False
    bar_label(c, str(i + 1), size=30, align=PP_ALIGN.CENTER)
    y = cy + dia // 2 + 100000
    text(s, cx - cw // 2, y, cw, 380000, [name], size=18, color=NAVY_TEXT, bold=True, align=PP_ALIGN.CENTER)
    text(s, cx - cw // 2, y + 370000, cw, 320000, [desc], size=14, color=BODY, align=PP_ALIGN.CENTER)

# lower band: data under steps 1, 4, 5; the user's settings under steps 2-3
band_y = cy + dia // 2 + 900000
band_h = CB - band_y - 120000
for i, src in data.items():
    cx = FL + i * cw + cw // 2
    line(s, cx - 450000, band_y, cx + 450000, band_y, color=GRID, width=1.0)
    text(s, cx - cw // 2 + 91440, band_y + 80000, cw - 182880, 300000, ["Data"], size=13, color=MUTED, bold=True,
         align=PP_ALIGN.CENTER)
    text(s, cx - cw // 2 + 91440, band_y + 360000, cw - 182880, 1100000, [src], size=13, color=MUTED,
         align=PP_ALIGN.CENTER)

px, pw = FL + cw + 91440, 2 * cw - 182880
rect(s, px, band_y, pw, band_h, PALE)
text(s, px + 91440, band_y + 60000, pw - 182880, 340000, ["You set"], size=16, color=NAVY_TEXT, bold=True)
controls = [("Who cuts", "A preset scenario, or Custom: the US, 13 other donor groups, or all donors via "
                         "Global Fund, Gavi, WHO or UNICEF"),
            ("How the cut flows", "Direct and multilateral aid, cut separately per donor"),
            ("How fast", "Sudden, Linear, Front-Loaded, Back-Loaded, S\u2011Curve or Custom"),
            ("What fills the gap", "No Government Replacement, Replace a Set Share, As Much as Fiscal Space "
                                   "Allows or Gradual Budget Increase"),
            ("Data", "KFF MOU Tracker, OECD, IHME 2025 (cuts); IMF WEO, IHME, World Bank WDI (response)")]
text(s, px + 91440, band_y + 370000, pw - 182880, band_h - 400000,
     [[(lab + ": ", {"bold": True, "color": NAVY_TEXT}), (opt, {})] for lab, opt in controls],
     size=12, color=BODY, spacing=4)
# brackets tie the settings box to steps 2 and 3
for i in (1, 2):
    cx = FL + i * cw + cw // 2
    line(s, cx, cy + dia // 2 + 720000, cx, band_y, color=NUM_BLUE, width=1.25)

source(s, "Sources: dashboard code (scenarios.py, model_section.py, model_params.csv); data and studies as listed (see References).")
out = HERE / "steps_and_controls_slide.pptx"
d.save(out, ["Five steps from aid money to coverage change. The user chooses the scenario (steps 2) and the government "
             "response (step 3); the other steps run on the data shown under them."])
print("wrote", out)
