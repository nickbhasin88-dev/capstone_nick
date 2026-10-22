"""
Build the dashboard segment (round 3, 17 slides) on the team deck's own masters (python-pptx).

    python slides/build_dashboard_segment.py [--team slides/render/team_capstone_deck.pptx] [--out slides/dashboard_segment.pptx]

Style source: the team deck (Capstone Midpoint Check-In.pptx). Its masters, layouts and theme, the "03 Dashboard"
section divider (kept as the title slide), the navy title band of the dashboard section, the slide-number field and
the Yale logo are reused from the team file; every colour below is one the team file uses. Figures: slides/deck_data.json
(slides/deck_data.py), audit/slide_numbers.md and the audit scripts named in each source line. Requires python-pptx.

Layout: one content frame on every content slide. Left and right edges at the title text's left edge (0.37 in, the
logo's left edge; the title's text inset is set to land there), top directly below the title band, bottom 0.3 in above
the logo row (the footer). Source lines sit on one baseline at the bottom of the frame.
"""
from __future__ import annotations

import argparse
import copy
import json
from io import BytesIO
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.chart.data import CategoryChartData, XyChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import (XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION, XL_MARKER_STYLE,
                            XL_TICK_LABEL_POSITION, XL_TICK_MARK)
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.opc.packuri import PackURI
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

HERE = Path(__file__).resolve().parent

# ---- the team deck's own colours (read from Capstone Midpoint Check-In.pptx) ----
NAVY = "1C3073"           # title band; primary series, header bars, numerals, keylines
NAVY_TEXT = "21306F"      # bold body text (slides 8-10)
MID = "3D63B0"            # numerals (slide 10): secondary series
LIGHT = "8FA8E0"          # light blue (12 uses): tertiary series, interval bands
PALE = "DDE7F8"           # light blue fill (slides 24-28): fourth series
BODY = "3A4258"           # body text (slides 8-10)
MUTED = "4A5568"          # captions
DARK = "1B2340"           # bar labels (slide 9)
GRID = "D5DCEA"           # light gray rules (slide 3)
PANEL = "F6F8FC"          # light gray panels (slide 10)
REF = "6B7280"            # gray text (slides 2-3): reference lines
WHITE = "FFFFFF"

# ---- the content frame (EMU) ----
W, H = 12192000, 6858000
FL = 338944                         # left edge = logo left = title text left
FR = W - FL
FW = FR - FL
FT = 1050000                        # directly below the title band (band bottom 954,512 + its 4.5 pt edge)
FOOT = 6257970                      # top of the logo row
FB = FOOT - 274320                  # 0.3 in above the footer
SRC_H = 190000
SRC_Y = FB - SRC_H                  # every source line on this baseline
CB = SRC_Y - 40000                  # content bottom on slides with a source line
TITLE_INSET = FL + 21988            # the title shape starts at x = -21,988


def rgb(h):
    return RGBColor.from_string(h)


# --------------------------------------------------------------------------- deck scaffolding
class Deck:
    def __init__(self, team_path: Path):
        self.prs = Presentation(team_path)
        team = self.prs.slides
        dash = team[11]                                   # slide 12: the dashboard-section look
        self.title_xml = copy.deepcopy([s for s in dash.shapes if s.name == "Title 1"][0]._element)
        bp = self.title_xml.find(".//" + qn("a:bodyPr"))
        bp.set("lIns", str(TITLE_INSET))
        bp.set("rIns", str(TITLE_INSET))
        self.sldnum_xml = copy.deepcopy([s for s in dash.shapes if "Slide Number" in s.name][0]._element)
        self.logos = [(p.image.blob, p.left, p.top, p.width, p.height) for p in dash.shapes if p.shape_type == 13]
        self.lay_content = self.prs.slide_masters[0].slide_layouts.get_by_name("Title and Content")
        sldIdLst = self.prs.slides._sldIdLst
        ids = list(sldIdLst)
        self.title_slide = ids[10]                        # team slide 11, "03 Dashboard", kept unchanged
        for k, sldId in enumerate(ids):
            if k != 10:
                self.prs.part.drop_rel(sldId.rId)
                sldIdLst.remove(sldId)
        self.order = [self.title_slide]

    def content(self, title: str):
        s = self.prs.slides.add_slide(self.lay_content)
        for ph in list(s.placeholders):
            ph._element.getparent().remove(ph._element)
        s.shapes._spTree.append(copy.deepcopy(self.title_xml))
        tshape = [sh for sh in s.shapes if sh.name == "Title 1"][0]
        runs = tshape.text_frame.paragraphs[0].runs
        runs[0].text = title
        for extra in runs[1:]:
            extra._r.getparent().remove(extra._r)
        s.shapes._spTree.append(copy.deepcopy(self.sldnum_xml))
        for blob, l, tp, w, h in self.logos:
            s.shapes.add_picture(BytesIO(blob), l, tp, w, h)
        self.order.append(self.prs.slides._sldIdLst[-1])
        return s

    def save(self, out: Path, notes: list[str]):
        lst = self.prs.slides._sldIdLst
        for el in list(lst):
            lst.remove(el)
        for el in self.order:
            lst.append(el)
        for i, sl in enumerate(self.prs.slides, 1):
            sl.part.partname = PackURI(f"/ppt/slides/tmp{i}.xml")
        for i, sl in enumerate(self.prs.slides, 1):
            sl.part.partname = PackURI(f"/ppt/slides/slide{i}.xml")
            for t in sl._element.iter(qn("a:fld")):
                if t.get("type") == "slidenum":
                    t.find(qn("a:t")).text = str(i)
        for sl, n in zip(self.prs.slides, notes):
            if n:
                sl.notes_slide.notes_text_frame.text = n
        self.prs.save(out)


# --------------------------------------------------------------------------- building blocks
def text(slide, x, y, w, h, paras, size=16, color=BODY, bold=False, font="Arial", align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, spacing=None, line=None):
    """paras: list of str, or list of [(text, style dict), ...] runs per paragraph. Insets 0.05 in or less."""
    tb = slide.shapes.add_textbox(int(x), int(y), int(w), int(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Emu(45720)
    tf.margin_top = tf.margin_bottom = Emu(18288)
    for i, p in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = align
        if spacing:
            para.space_after = Pt(spacing)
        if line:
            para.line_spacing = line
        for rt, st in (p if isinstance(p, list) else [(p, {})]):
            r = para.add_run()
            r.text = rt
            f = r.font
            f.name = st.get("font", font)
            f.size = Pt(st.get("size", size))
            f.bold = st.get("bold", bold)
            f.color.rgb = rgb(st.get("color", color))
    return tb


def rect(slide, x, y, w, h, fill):
    sh = slide.shapes.add_shape(1, int(x), int(y), int(w), int(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = rgb(fill)
    sh.line.fill.background()
    sh.shadow.inherit = False
    tf = sh.text_frame
    tf.margin_left = tf.margin_right = Emu(45720)
    tf.margin_top = tf.margin_bottom = Emu(18288)
    return sh


def bar_label(shape, s, size=20, color=WHITE, align=PP_ALIGN.LEFT, font="Arial", bold=True):
    tf = shape.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = s
    r.font.name, r.font.size, r.font.bold = font, Pt(size), bold
    r.font.color.rgb = rgb(color)


def line(slide, x1, y1, x2, y2, color=GRID, width=1.0):
    ln = slide.shapes.add_connector(1, int(x1), int(y1), int(x2), int(y2))
    ln.line.color.rgb = rgb(color)
    ln.line.width = Pt(width)
    return ln


def source(slide, s):
    """One-line footnote in the team deck's source style (Arial Nova 11, slides 24-26), same baseline on every slide."""
    return text(slide, FL, SRC_Y, FW, SRC_H, [s], size=11, color="000000", font="Arial Nova", anchor=MSO_ANCHOR.BOTTOM)


LINE_H = 262000                      # one 16 pt line with 3 pt spacing


def strip(slide, lines):
    """The fixed body strip at the bottom of the frame, above the source line: one to three 16 pt lines."""
    assert 1 <= len(lines) <= 3
    h = LINE_H * len(lines) + 40000
    top = CB - h
    text(slide, FL, top, FW, h, lines, size=16, color=BODY, spacing=3, anchor=MSO_ANCHOR.BOTTOM)
    return top


# --------------------------------------------------------------------------- charts: one style everywhere
def _sub(parent, tag, **attrs):
    return etree.SubElement(parent, qn(tag), **{k: str(v) for k, v in attrs.items()})


def _manual(layout_parent_el, x, y, w=None, h=None, target=None):
    lay = layout_parent_el.find(qn("c:layout"))
    if lay is None:
        lay = etree.Element(qn("c:layout"))
        tx = layout_parent_el.find(qn("c:tx"))
        if tx is not None:
            tx.addnext(lay)
        else:
            layout_parent_el.insert(0, lay)
    for ch in list(lay):
        lay.remove(ch)
    ml = _sub(lay, "c:manualLayout")
    if target:
        _sub(ml, "c:layoutTarget", val=target)
    _sub(ml, "c:xMode", val="edge")
    _sub(ml, "c:yMode", val="edge")
    _sub(ml, "c:x", val=x)
    _sub(ml, "c:y", val=y)
    if w is not None:
        _sub(ml, "c:w", val=w)
        _sub(ml, "c:h", val=h)


def _no_fill_spPr(parent_el, before_tags=()):
    sp = parent_el.find(qn("c:spPr"))
    if sp is not None:
        parent_el.remove(sp)
    sp = etree.Element(qn("c:spPr"))
    _sub(sp, "a:noFill")
    ln = _sub(sp, "a:ln")
    _sub(ln, "a:noFill")
    anchor = None
    for t in before_tags:
        anchor = parent_el.find(qn(t))
        if anchor is not None:
            break
    if anchor is not None:
        anchor.addprevious(sp)
    else:
        parent_el.append(sp)


def chart(slide, kind, cd, title, y0, y1, plot, legend=True):
    """Full-frame-width chart: bold 16 pt title top-left, no border, no plot fill, legend at the bottom in one row.
    plot = (x, y, w, h) of the inner plot area as fractions of the chart."""
    gf = slide.shapes.add_chart(kind, FL, int(y0), FW, int(y1 - y0), cd)
    ch = gf.chart
    ch.font.name = "Arial"
    ch.font.size = Pt(13)
    ch.font.color.rgb = rgb(DARK)
    ch.has_title = True
    tf = ch.chart_title.text_frame
    tf.text = title
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    for r in p.runs:
        r.font.size, r.font.bold, r.font.name = Pt(16), True, "Arial"
        r.font.color.rgb = rgb(NAVY_TEXT)
    t_el = ch._chartSpace.chart.find(qn("c:title"))
    _manual(t_el, 0.0, 0.0)
    ov = t_el.find(qn("c:overlay"))
    if ov is None:
        ov = etree.Element(qn("c:overlay"))
        t_el.find(qn("c:layout")).addnext(ov)
    ov.set("val", "0")
    ch.has_legend = legend
    if legend:
        ch.legend.position = XL_LEGEND_POSITION.BOTTOM
        ch.legend.include_in_layout = False
        ch.legend.font.size = Pt(13)
        ch.legend.font.name = "Arial"
        ch.legend.font.color.rgb = rgb(DARK)
    pa = ch._chartSpace.chart.plotArea
    _manual(pa, *plot, target="inner")
    _no_fill_spPr(pa, before_tags=("c:extLst",))
    cs = ch._chartSpace
    _no_fill_spPr(cs, before_tags=("c:txPr", "c:externalData", "c:extLst"))
    rc = cs.find(qn("c:roundedCorners"))
    if rc is None:
        rc = etree.Element(qn("c:roundedCorners"))
        cs.find(qn("c:chart")).addprevious(rc)
    rc.set("val", "0")
    return ch


def axis(ax, title=None, size=13, num_fmt=None, grid=False, title_size=13, color=DARK, line_color=GRID):
    """Tick marks off; gridlines (horizontal only, set by the caller) thin light gray; axis titles 13-14 pt."""
    ax.major_tick_mark = XL_TICK_MARK.NONE
    ax.minor_tick_mark = XL_TICK_MARK.NONE
    ax.has_minor_gridlines = False
    ax.has_major_gridlines = grid
    if grid:
        ax.major_gridlines.format.line.color.rgb = rgb(GRID)
        ax.major_gridlines.format.line.width = Pt(0.75)
    ax.tick_labels.font.size = Pt(size)
    ax.tick_labels.font.name = "Arial"
    ax.tick_labels.font.color.rgb = rgb(color)
    ax.format.line.color.rgb = rgb(line_color)
    if num_fmt:
        ax.tick_labels.number_format = num_fmt
        ax.tick_labels.number_format_is_linked = False
    if title:
        ax.has_title = True
        tf = ax.axis_title.text_frame
        tf.text = title
        for r in tf.paragraphs[0].runs:
            r.font.size, r.font.bold, r.font.name = Pt(title_size), False, "Arial"
            r.font.color.rgb = rgb(MUTED)


def color_series(ch, colors):
    for s, c in zip(ch.plots[0].series, colors):
        s.format.fill.solid()
        s.format.fill.fore_color.rgb = rgb(c)
        s.format.line.fill.background()


def labels(series, fmt=None, size=12, color=DARK, pos=XL_LABEL_POSITION.OUTSIDE_END):
    series.data_labels.show_value = True
    dl = series.data_labels
    dl.font.size, dl.font.bold, dl.font.name = Pt(size), True, "Arial"
    dl.font.color.rgb = rgb(color)
    dl.position = pos
    if fmt:
        dl.number_format, dl.number_format_is_linked = fmt, False


def point_label(series, i, t, size=12, color=DARK, pos=XL_LABEL_POSITION.RIGHT):
    dl = series.points[i].data_label
    tf = dl.text_frame
    tf.text = t
    for r in tf.paragraphs[0].runs:
        r.font.size, r.font.bold, r.font.name = Pt(size), True, "Arial"
        r.font.color.rgb = rgb(color)
    dl.position = pos


def hide_point_label(series, i):
    dLbls = series._element.get_or_add_dLbls()
    d = dLbls._insert_dLbl_in_sequence(i) if hasattr(dLbls, "_insert_dLbl_in_sequence") else None
    if d is None:
        d = etree.Element(qn("c:dLbl"))
        _sub(d, "c:idx", val=i)
        dLbls.insert(0, d)
    for ch in list(d):
        if ch.tag != qn("c:idx"):
            d.remove(ch)
    _sub(d, "c:delete", val=1)


def table(slide, x, y, w, rows, widths, header_h, row_h):
    """Navy header with white text; alternating light gray rows; first column bold 16 pt; cell text 15 pt."""
    nr, nc = len(rows), len(rows[0])
    gf = slide.shapes.add_table(nr, nc, int(x), int(y), int(w), int(header_h + row_h * (nr - 1)))
    tbl = gf.table
    tot = sum(widths)
    for j, wd in enumerate(widths):
        tbl.columns[j].width = Emu(int(w * wd / tot))
    tblPr = tbl._tbl.tblPr
    for a in ("bandRow", "firstRow"):
        tblPr.set(a, "0")
    sid = tblPr.find(qn("a:tableStyleId"))
    if sid is None:
        sid = etree.SubElement(tblPr, qn("a:tableStyleId"))
    sid.text = "{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}"
    for i in range(nr):
        tbl.rows[i].height = Emu(int(header_h if i == 0 else row_h))
        for j in range(nc):
            c = tbl.cell(i, j)
            c.margin_left = c.margin_right = Emu(45720)
            c.margin_top = c.margin_bottom = Emu(18288)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = c.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT
            r = p.add_run()
            r.text = str(rows[i][j])
            r.font.name = "Arial"
            c.fill.solid()
            if i == 0:
                r.font.size, r.font.bold = Pt(16), True
                r.font.color.rgb = rgb(WHITE)
                c.fill.fore_color.rgb = rgb(NAVY)
            else:
                r.font.size = Pt(16 if j == 0 else 14)
                r.font.bold = j == 0
                r.font.color.rgb = rgb(NAVY_TEXT if j == 0 else BODY)
                c.fill.fore_color.rgb = rgb(PANEL if i % 2 == 1 else WHITE)
            tcPr = c._tc.get_or_add_tcPr()
            fill = tcPr.find(qn("a:solidFill"))
            for tag in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
                ln = etree.Element(qn(tag), w="9525")
                sf = etree.SubElement(ln, qn("a:solidFill"))
                etree.SubElement(sf, qn("a:srgbClr"), val=GRID)
                fill.addprevious(ln)
    return gf


NUM_BLUE = "3D63B0"       # numerals (team Agenda and Objectives slides)
HEAD_FONT = "Franklin Gothic Medium"


def numbered_rows(s, items, label_size=26, text_size=20):
    """The team deck's Agenda / Objectives pattern: numbered rows with hairlines between them, spread over the frame.
    No fills, no bars."""
    n = len(items)
    rh = (FB - FT) // n
    for k, (lab, txt) in enumerate(items):
        y = FT + k * rh
        line(s, FL, y, FR, y, color=GRID, width=1.0)
        text(s, FL, y, 900000, rh, [f"{k + 1:02d}"], size=label_size, color=NUM_BLUE, font=HEAD_FONT,
             anchor=MSO_ANCHOR.MIDDLE)
        text(s, FL + 900000, y, 2300000, rh, [lab], size=label_size, color=NAVY_TEXT, font=HEAD_FONT,
             anchor=MSO_ANCHOR.MIDDLE)
        text(s, FL + 3300000, y, FW - 3300000, rh, [txt], size=text_size, color=BODY, anchor=MSO_ANCHOR.MIDDLE,
             line=1.1)
    line(s, FL, FB, FR, FB, color=GRID, width=1.0)


def summary(d, letter, name, problem, approach, finding):
    """Section summary: the same three numbered rows at the same coordinates on all five."""
    s = d.content(f"Section {letter}: {name}")
    numbered_rows(s, [("Problem", problem), ("Approach", approach), ("Finding", finding)])
    return s


# --------------------------------------------------------------------------- the deck
def build(team: Path, out: Path):
    D = json.loads((HERE / "deck_data.json").read_text())
    d = Deck(team)
    notes = [""]

    # 2. Question and purpose: the same numbered-row pattern as the section summaries
    s = d.content("The dashboard turns aid cuts into people losing services")
    numbered_rows(s, [("Question", "When donor health aid is cut in 2026-2030, how many people a year lose HIV, TB, malaria "
                          "and routine immunization services in each of 70 countries, and how much of the lost aid "
                          "can each government replace?"),
             ("Purpose", "For WHO and ministries of health: run any Donor Scenario country by country, see which "
                         "services and channels lose most, and test each Government Response option against the "
                         "country's fiscal space.")], text_size=22)
    notes.append("The dashboard answers one question for any country and any cut, and is built for comparing "
                 "scenarios rather than producing a single forecast.")

    # 3. What the dashboard can do: one full-frame table
    s = d.content("Any donor, channel, cut pace and replacement, for 71 countries")
    rows = [
        ["You set", "Options, as labelled in the dashboard"],
        ["Who cuts", "Custom: the United States or any of 13 other donor groups, or every donor’s money through the "
                     "Global Fund, Gavi, WHO or UNICEF"],
        ["How the cut flows", "Per donor: Bilateral & NGO Cut % and Via Multilaterals Cut %; cuts combine as "
                              "1 − (1 − donor cut)(1 − channel cut)"],
        ["How fast", "How Funding Changes, 2026-2030: Sudden (Default), Linear Phase-Out, Front-Loaded, Back-Loaded, "
                     "S-Curve, Custom"],
        ["What fills the gap", "Government Response: No Government Replacement (default), Replace a Set Share, "
                               "As Much as Fiscal Space Allows or Gradual Budget Increase"],
        ["Presets", "Donor Scenario: US Bilateral Exit + Multilateral Withdrawals; America First MOUs; IHME 2025 "
                    "Preliminary Estimates; Total-Aid Cuts (OECD) Applied to Health Aid; Global Fund & Gavi "
                    "Shortfalls; Combined Retreat"],
        ["Uncertainty", "Range Across Parameter Values: 2.5th to 97.5th percentile of 400 parameter draws, beside "
                        "every central estimate"]]
    hh = 460000
    table(s, FL, FT, FW, rows, [2.2, 10.4], hh, (CB - FT - hh) // (len(rows) - 1))
    source(s, "Source: dashboard code (scenarios.py, model_section.py, paths_ui.py), October 2026; 71 countries listed, "
              "70 with recorded aid (Panama has none).")
    notes.append("Option names are the dashboard's own labels, spelled as displayed. The Custom scenario sets a "
                 "bilateral and a multilateral cut for each of 14 donor groups and a channel cut for the Global Fund, "
                 "Gavi, WHO and UNICEF.")

    # 4. Section A summary
    summary(d, "A", "How the dashboard is built",
            "A cut is announced in US dollars; how many people then lose a service, and how much coverage falls, is not.",
            "IHME aid by donor, channel and service, joined to cost per person served, people in need and government "
            "budgets for 70 countries, in five linked steps.",
            "Any Donor Scenario runs from US$ lost to people losing each service and coverage points lost, with a "
            "2.5th to 97.5th percentile range from 400 draws.")
    notes.append("")

    # 5. Five linked steps: a pipeline across the frame, the main input dataset under each step
    s = d.content("Five linked steps turn a donor’s cut into lost services and coverage")
    steps = [("Aid Money", "By donor, channel, service", "IHME DAH 1990-2026, 2021-23 average"),
             ("Scenario Cut", "Share cut, 2026-2030 path", "KFF MOU tracker; OECD ODA 2025; IHME 2025"),
             ("Government Response", "Four replacement options", "IHME Health Spending; WB WDI; IMF WEO"),
             ("Services Lost", "Net loss ÷ cost per person", "GHCC unit costs (ART, TB), 2023 US$"),
             ("Coverage Change", "Lost ÷ people in need", "UNAIDS, WHO, MAP, WUENIC, 2024-25")]
    cw = FW // 5
    dia = 1000000
    block_h = dia + 2500000
    cy = FT + (CB - FT - block_h) // 2 + dia // 2
    line(s, FL + cw // 2, cy, FL + 4 * cw + cw // 2, cy, color=GRID, width=2.0)
    for i, (name, desc, data) in enumerate(steps):
        cx = FL + i * cw + cw // 2
        c = s.shapes.add_shape(9, cx - dia // 2, cy - dia // 2, dia, dia)
        c.fill.solid()
        c.fill.fore_color.rgb = rgb(NUM_BLUE if i < 4 else NAVY)
        c.line.fill.background()
        c.shadow.inherit = False
        bar_label(c, str(i + 1), size=36, align=PP_ALIGN.CENTER)
        y = cy + dia // 2 + 120000
        text(s, cx - cw // 2 + 91440, y, cw - 182880, 620000, [name], size=18, color=NAVY_TEXT, bold=True,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.BOTTOM)
        text(s, cx - cw // 2 + 91440, y + 660000, cw - 182880, 600000, [desc], size=15, color=BODY,
             align=PP_ALIGN.CENTER)
        line(s, cx - 500000, y + 1340000, cx + 500000, y + 1340000, color=GRID, width=1.0)
        text(s, cx - cw // 2 + 91440, y + 1420000, cw - 182880, 560000, [data], size=13, color=MUTED,
             align=PP_ALIGN.CENTER)
    source(s, "Sources: IHME DAH; KFF; OECD; IHME Health Spending; WB WDI; IMF WEO; GHCC; UNAIDS; WHO GTB; MAP; WUENIC "
              "(see References); health_model.py.")
    notes.append("The step names are the model's own (docs/EXPLAINER.md, section 1), in the order the code applies "
                 "them: the government response is netted off the lost aid before it is divided by the cost per person.")

    # 6. Section B summary
    sh = D["us_share"]
    n_major = sum(1 for r in sh if r["us_share"] > 0.5)
    us_b_, tot_b = D["us_aid_musd"] / 1000, D["total_aid_musd"] / 1000
    summary(d, "B", "Where the money comes from",
            "How exposed a country is to a cut depends on who pays for its services and through which channel.",
            "IHME DAH aid for HIV, TB, malaria and immunization, 2021-23 average, split by donor, channel and "
            "IHME programme area for 70 countries.",
            f"The US pays US${us_b_:.1f}B of US${tot_b:.1f}B a year ({us_b_ / tot_b:.0%}), and over 50% in "
            f"{n_major} of the 20 largest recipients.")
    notes.append("")

    # 7. US share, top 20
    s = d.content(f"The US pays over half the aid in {n_major} of the 20 largest recipients")
    short = {"Democratic Republic of the Congo": "DR Congo", "Cote d'Ivoire": "Côte d’Ivoire"}
    rows = list(reversed(sh))
    cd = CategoryChartData()
    cd.categories = [short.get(r["country"], r["country"]) for r in rows]
    cd.add_series("United States (all channels)", [r["us_share"] for r in rows])
    cd.add_series("All other donors", [1 - r["us_share"] for r in rows])
    top = strip(s, [f"Across all 70 countries the US pays {us_b_ / tot_b:.0%}: US${us_b_:.1f}B of US${tot_b:.1f}B a "
                    "year, 2021-23 average, constant 2023 US$."])
    ch = chart(s, XL_CHART_TYPE.BAR_STACKED_100, cd,
               "US share of 2021-23 aid for HIV, TB, malaria and immunization, 20 largest recipients of the 70",
               FT, top - 40000, (0.135, 0.085, 0.85, 0.70))
    ch.plots[0].gap_width = 30
    etree.SubElement(ch.category_axis._element, qn("c:tickLblSkip"), val="1")
    color_series(ch, [NAVY, LIGHT])
    labels(ch.plots[0].series[0], fmt="0%", color=WHITE, pos=XL_LABEL_POSITION.INSIDE_END)
    axis(ch.value_axis, "Share of the country’s aid for these four areas, %, 2021-23 average", num_fmt="0%")
    axis(ch.category_axis, "Recipient (largest total aid at top)", size=12)
    source(s, "Source: IHME DAH 1990-2026, 2021-23 average, constant 2023 US$; model_data/dah_lines.csv (prepare_model.py).")
    notes.append("Total aid for the four areas is the ranking variable. The US share includes US money through every "
                 "channel, including its contributions to the Global Fund and Gavi.")

    # 8. Channel x purpose
    cp = D["channel_purpose"]
    ptot = D["purpose_total"]
    tot = sum(ptot.values())
    chans = ["Global Fund", "Bilateral agencies", "NGOs", "Gavi", "Other channels"]
    purposes = [("Direct services", "Direct services"), ("Testing and care", "HIV testing and care"),
                ("Systems support", "Systems support"), ("Purpose not stated", "Purpose not stated")]
    s = d.content(f"{ptot['Direct services'] / tot:.0%} of aid pays directly for services; a fifth has no stated purpose")
    cd = CategoryChartData()
    cd.categories = chans
    for key, lab in purposes:
        cd.add_series(lab, [cp[c].get(key, 0.0) for c in chans])
    top = strip(s, ["Direct services: ART, PMTCT, HIV prevention, OVC, TB care, bednets, spraying, malaria care, "
                    "vaccines.",
                    f"Of US${tot / 1000:.1f}B a year: systems support {ptot['Systems support'] / tot:.0%}, purpose not "
                    f"stated {ptot['Purpose not stated'] / tot:.0%}, HIV testing and care {ptot['Testing and care'] / tot:.0%}."])
    ch = chart(s, XL_CHART_TYPE.COLUMN_STACKED, cd,
               "Aid by channel and IHME programme area, 70 countries, 2021-23 average",
               FT, top - 40000, (0.075, 0.095, 0.915, 0.65))
    ch.plots[0].gap_width = 55
    ch.plots[0].overlap = 100
    cols = [NAVY, MID, LIGHT, PALE]
    color_series(ch, cols)
    for k, ser in enumerate(ch.plots[0].series):
        labels(ser, fmt="#,##0", color=WHITE if k < 2 else DARK, pos=XL_LABEL_POSITION.CENTER)
        for i, c in enumerate(chans):
            if cp[c].get(purposes[k][0], 0.0) < 150:
                hide_point_label(ser, i)
    axis(ch.value_axis, "Aid, US$ millions a year", grid=True, num_fmt="#,##0")
    axis(ch.category_axis, "Channel (IHME channel group)")
    source(s, "Source: IHME DAH 1990-2026, 2021-23 average, constant 2023 US$; HIV, TB, malaria and immunization areas grouped "
              "as in prepare_model.LINES.")
    notes.append("This chart shows IHME's own coding. The model later splits the 'purpose not stated' money using "
                 "Global Fund grant module shares; that allocation is not shown here.")

    # 9. Section C summary
    ca = D["channels_all"]
    cn = D["channels_n"]
    ab = D["art_bound"]
    full_all = ab["full_exit_all"]["art_off_per_year"] / 1e6
    summary(d, "C", "What a cut removes",
            "The same US$1M cut removes different services depending on the channel it flows through and the country.",
            "Services Lost = net aid lost on each service ÷ cost per person served, capped at the people donor money "
            "pays for; the same for any donor and any channel.",
            "On signed MOU schedules, ART coverage falls below 90% in two countries in 2026. US Bilateral Exit + "
            f"Multilateral Withdrawals, the upper bound, stops ART for {full_all:.2f}M people a year.")
    notes.append("")

    # 10. Channels
    us_b, gf_art = ca["US bilateral (direct channels)"]["ART"], ca["Global Fund (all donors)"]["ART"]
    s = d.content(f"Per US$1M, US bilateral cuts remove {us_b / gf_art:.1f}× the ART of Global Fund cuts")
    order = [("US bilateral (direct channels)", "US Bilateral & NGO", True),
             ("US money through the Global Fund", "US via Global Fund", True),
             ("Global Fund (all donors)", "Global Fund, all donors", False), ("WHO (all donors)", "WHO, all donors", False),
             ("UNICEF (all donors)", "UNICEF, all donors", False), ("Gavi (all donors)", "Gavi, all donors", False)]
    cd = CategoryChartData()
    cd.categories = [f"{lab} ({cn[k]})" for k, lab, _ in order]
    cd.add_series("US money", [ca[k]["ART"] if us else None for k, _, us in order])
    cd.add_series("All donors’ money through the channel", [None if us else ca[k]["ART"] for k, _, us in order])
    top = strip(s, ["Each channel cut alone, by the share losing US$10M a year per country (half its baseline if below "
                    "US$20M).",
                    "Sudden (Default) path, no replacement; full-cost equivalents after 15% continuity (assumption).",
                    "Gavi money buys vaccines only, so a Gavi cut removes no ART."])
    ch = chart(s, XL_CHART_TYPE.COLUMN_CLUSTERED, cd,
               "ART patient-years lost a year per US$1M of aid lost a year, by channel cut, 2026-30",
               FT, top - 40000, (0.075, 0.105, 0.915, 0.57))
    ch.plots[0].gap_width = 45
    ch.plots[0].overlap = 100
    color_series(ch, [NAVY, MID])
    for ser in ch.plots[0].series:
        labels(ser, fmt="#,##0")
    axis(ch.value_axis, "ART patient-years per US$1M", grid=True, num_fmt="#,##0")
    axis(ch.category_axis, "Channel cut (countries the channel funds, of 70)")
    source(s, "Source: model output, audit/channels/run_channels.py (health_model.run_country, central run); IHME DAH "
              "1990-2026, 2021-23 average.")
    notes.append("Pooled over the countries each channel funds: sum of people lost divided by sum of money lost. TB "
                 "and vaccine counts per dollar are not shown because their unit costs are flagged as uncertain.")

    # 11. MOU ART coverage
    ma = D["mou_art"]
    keep = [i for i in ("SWZ", "LSO", "KEN", "BWA") if i in ma]
    s = d.content("Under the MOUs, ART coverage falls below 90% in two countries in 2026")
    years = ["2025", "2026", "2027", "2028", "2029", "2030"]
    cd = CategoryChartData()
    cd.categories = years
    for i in keep:
        cd.add_series(ma[i]["country"], [ma[i]["today"]] + [ma[i][y] for y in years[1:]])
    cd.add_series("90% threshold", [0.90] * len(years))
    top = strip(s, ["Eswatini and Lesotho fall below 90% in 2026 and Kenya in 2028; Botswana stays at 94% or above.",
                    "US bilateral cuts on each signed MOU schedule only (no US multilateral exits); no replacement; 15% "
                    "continuity (assumption).",
                    "Rwanda (94% in 2025) is not shown: its result rests on an estimated count of donor-funded patients."])
    ch = chart(s, XL_CHART_TYPE.LINE_MARKERS, cd,
               "ART coverage on signed MOU schedules, 4 of 5 MOU countries above 90% in 2025",
               FT, top - 40000, (0.075, 0.115, 0.80, 0.58))
    cols = [NAVY, MID, LIGHT, "2F52A6"]
    marks = [XL_MARKER_STYLE.CIRCLE, XL_MARKER_STYLE.SQUARE, XL_MARKER_STYLE.TRIANGLE, XL_MARKER_STYLE.DIAMOND]
    for k, ser in enumerate(ch.plots[0].series):
        ser.smooth = False
        ser.format.line.width = Pt(2.5)
        if k < len(keep):
            ser.format.line.color.rgb = rgb(cols[k])
            ser.marker.style = marks[k]
            ser.marker.size = 8
            ser.marker.format.fill.solid()
            ser.marker.format.fill.fore_color.rgb = rgb(cols[k])
            ser.marker.format.line.color.rgb = rgb(cols[k])
            point_label(ser, len(years) - 1, f"{ma[keep[k]]['country']} {ma[keep[k]]['2030']:.0%}",
                        color=cols[k] if k != 2 else MID)
        else:
            ser.format.line.color.rgb = rgb(REF)
            ser.format.line.width = Pt(1.5)
            ser.format.line.dash_style = MSO_LINE_DASH_STYLE.DASH
            ser.marker.style = XL_MARKER_STYLE.NONE
    ch.value_axis.minimum_scale, ch.value_axis.maximum_scale, ch.value_axis.major_unit = 0.6, 1.0, 0.1
    axis(ch.value_axis, "% of people with HIV on ART", grid=True, num_fmt="0%")
    axis(ch.category_axis, "Year (2025: UNAIDS estimate; 2026-2030: model)")
    source(s, "Source: UNAIDS AIDSinfo 2026 (2025 coverage); KFF MOU tracker and team MOU sheet; model output, "
              "audit/concentration/run_concentration.py.")
    notes.append("Rwanda is also above 90% today but is left out: its result depends on the estimated number of "
                 "donor-funded patients, which the deck treats as not well supported.")

    # 12. Upper bound
    s = d.content(f"Upper bound: {full_all:.2f}M people a year stop ART under a full US exit")
    cd = CategoryChartData()
    cd.categories = ["16 MOU countries", "All 70 countries"]
    cd.add_series("America First MOUs", [ab["mou_16"]["art_off_per_year"] / 1e6, None])
    cd.add_series("US Bilateral Exit + Multilateral Withdrawals (upper bound)",
                  [ab["full_exit_16"]["art_off_per_year"] / 1e6, full_all])
    top = strip(s, ["Full exit: US Bilateral & NGO aid −100% from 2026; US money via WHO, Gavi, UNFPA −100%; US Global "
                    "Fund pledge −23%.",
                    "America First MOUs: US bilateral cuts on each signed MOU schedule plus the same US multilateral "
                    "exits. No replacement.",
                    f"Aid lost a year: US${ab['mou_16']['aid_lost_per_year_musd'] / 1000:.2f}B (MOUs, 16 countries); "
                    f"US${ab['full_exit_16']['aid_lost_per_year_musd'] / 1000:.2f}B (full exit, 16); "
                    f"US${ab['full_exit_all']['aid_lost_per_year_musd'] / 1000:.2f}B (full exit, 70)."])
    ch = chart(s, XL_CHART_TYPE.COLUMN_CLUSTERED, cd,
               "People who stop ART a year (full-cost equivalents), 2026-30 average, by Donor Scenario",
               FT, top - 40000, (0.075, 0.105, 0.915, 0.6))
    ch.plots[0].gap_width = 70
    ch.plots[0].overlap = -8
    color_series(ch, [MID, NAVY])
    for ser in ch.plots[0].series:
        labels(ser, fmt='0.00"M"')
    axis(ch.value_axis, "People who stop ART a year, millions", grid=True, num_fmt="0.0")
    axis(ch.category_axis, "Countries covered by the scenario")
    source(s, "Source: model output (health_model.run_country, central run), presets America First MOUs and US Bilateral "
              "Exit + Multilateral Withdrawals; IHME DAH 2021-23.")
    notes.append("The MOU preset applies only to the 16 countries with a signed MOU and a schedule, so it has no "
                 "all-country bar. Both presets include the US exits from WHO, Gavi and UNFPA and a 23% cut to its "
                 "Global Fund pledge.")

    # 13. Section D summary
    hist = {r["group"]: r for r in D["history"]}
    lic = hist["Income: low income"]
    allc = hist["All countries"]
    summary(d, "D", "What governments can replace",
            "How much lost aid a government replaces decides how many people lose a service.",
            f"A two-way fixed-effects regression on IHME data, {allc['n_countries']} countries, 2002-23; in the "
            "dashboard, Government Response sets the replacement for any Donor Scenario.",
            "When aid fell, low-income governments neither replaced it nor cut their own health spending "
            + f"({lic['theta']:+.2f} per US$1 lost, {lic['n_countries']} countries).".replace("-", "−"))
    notes.append("")

    # 14. History: dot plot with interval bands
    s = d.content("When aid fell, low-income governments kept health spending unchanged")
    groups = [("All countries", "All countries"), ("Income: upper middle income", "Upper-middle income"),
              ("Income: lower middle income", "Lower-middle income"), ("Income: low income", "Low income"),
              ("Aid dependence (DAH/THE 2015-23): high (top third)", "Most aid-dependent third"),
              ("The 15 MOU countries", "MOU countries in the panel")]
    rows = [(lab, hist[k]) for k, lab in groups]
    n = len(rows)
    xd = XyChartData()
    s1 = xd.add_series("Estimate, with its 95% confidence interval as the band")
    s2 = xd.add_series("label")
    for i, (_, r) in enumerate(rows):
        s1.add_data_point(r["theta"], n - i)
        s2.add_data_point(r["hi"], n - i)
    px, py, pw, ph = 0.25, 0.12, 0.70, 0.72
    y1 = CB - 40000
    ch = chart(s, XL_CHART_TYPE.XY_SCATTER, xd,
               "Change in government health spending per US$1 of aid lost, by country group, 2002-23",
               FT, y1, (px, py, pw, ph), legend=False)
    sr, sl = ch.plots[0].series
    sr.marker.style = XL_MARKER_STYLE.CIRCLE
    sr.marker.size = 11
    sr.marker.format.fill.solid()
    sr.marker.format.fill.fore_color.rgb = rgb(NAVY)
    sr.marker.format.line.color.rgb = rgb(NAVY)
    sr.format.line.fill.background()
    sl.marker.style = XL_MARKER_STYLE.NONE
    sl.format.line.fill.background()
    eb = etree.Element(qn("c:errBars"))
    _sub(eb, "c:errDir", val="x")
    _sub(eb, "c:errBarType", val="both")
    _sub(eb, "c:errValType", val="cust")
    _sub(eb, "c:noEndCap", val="1")
    for tag, vals in (("c:plus", [r["hi"] - r["theta"] for _, r in rows]),
                      ("c:minus", [r["theta"] - r["lo"] for _, r in rows])):
        el = _sub(eb, tag)
        nl = _sub(el, "c:numLit")
        _sub(nl, "c:formatCode").text = "General"
        _sub(nl, "c:ptCount", val=n)
        for k, val in enumerate(vals):
            pt = _sub(nl, "c:pt", idx=k)
            _sub(pt, "c:v").text = f"{val:.4f}"
    sp = _sub(eb, "c:spPr")
    ln = _sub(sp, "a:ln", w=203200, cap="flat")
    _sub(_sub(ln, "a:solidFill"), "a:srgbClr", val=LIGHT)
    sr._element.find(qn("c:xVal")).addprevious(eb)
    for i, (_, r) in enumerate(rows):
        hot = i == 0 or i >= 3
        point_label(sl, i, f"{r['theta']:+.2f}".replace("-", "−"), size=14, color=NAVY_TEXT if hot else MUTED)
    xa, ya = ch.category_axis, ch.value_axis
    axis(xa, "Change in government health spending per person per US$1 of aid lost (constant 2023 US$)", num_fmt='+0.0;"−"0.0;0', title_size=14)
    xa.minimum_scale, xa.maximum_scale, xa.major_unit = -1.2, 0.6, 0.2
    axis(ya, grid=True, line_color=NAVY)
    ya.minimum_scale, ya.maximum_scale, ya.major_unit = 0.5, n + 0.5, 1.0
    ya.tick_label_position = XL_TICK_LABEL_POSITION.NONE
    ya.format.line.width = Pt(2.25)
    ch_h = y1 - FT
    plot_top, step = FT + py * ch_h, ph * ch_h / n
    hdr_y = plot_top - 330000
    text(s, FL, hdr_y, px * FW - 91440, 300000, ["Country group (countries)"], size=13, color=MUTED, bold=True)
    text(s, FL + px * FW, hdr_y, pw * FW, 300000, ["Dot: estimate.  Bar: 95% confidence interval."], size=13,
         color=MUTED, align=PP_ALIGN.RIGHT)
    for i, (lab, r) in enumerate(rows):
        yc = plot_top + (i + 0.5) * step
        hot = i == 0 or i >= 3
        col = NAVY_TEXT if hot else MUTED
        text(s, FL, yc - 170000, px * FW - 91440, 340000, [f"{lab} ({r['n_countries']})"], size=14, color=col,
             bold=hot, anchor=MSO_ANCHOR.MIDDLE)
    source(s, "Source: IHME Health Spending 1995-2023 (GHES per person); IHME DAH 1990-2026; prepare_model.twoway_fe; "
              "audit/fiscal_history/run_fiscal_history.py.")
    notes.append("The pooled estimate across 97 countries is −0.19, but its interval includes zero. In the 26 "
                 "low-income countries the estimate is +0.01 with a tight interval: spending neither fell nor rose "
                 "when aid fell. 15 of the 16 MOU countries are in the IHME panel. Dot = estimate; band = 95% "
                 "confidence interval (clustered by country). Country and year fixed effects; regressors: aid falls "
                 "this year and last, and GDP growth. Below 0: spending fell with aid; above 0: lost aid replaced.")

    # 15. Section E summary
    summary(d, "E", "Insights",
            "To guide WHO, a result has to hold across countries and donors, not rest on one country.",
            "All six presets and six single-channel cuts run for all 70 countries; results resting on flagged inputs "
            "(TB costs, vaccine unit costs, estimated donor-funded patients) dropped.",
            "Five results kept: US funding share, Global Fund & Gavi Shortfalls, ART per US$1M by channel, MOU ART "
            "coverage, past government response.")
    notes.append("")

    # 16. Insights: five equal full-width rows
    gfg = 1022   # US$M a year, Global Fund & Gavi Shortfalls preset (audit/slide_numbers.md, table b)
    s = d.content("Five results hold across countries, donors and channels")
    ins = [f"The US pays {us_b_ / tot_b:.0%} (US${us_b_:.1f}B of US${tot_b:.1f}B a year) of HIV, TB, malaria and "
           f"immunization aid in 70 countries, and over 50% in {n_major} of the 20 largest recipients.",
           f"Global Fund & Gavi Shortfalls (every donor: Global Fund −20%, Gavi −15%) removes US${gfg / 1000:.2f}B "
           "of aid a year across 70 countries.",
           f"Per US$1M lost, a US Bilateral & NGO cut removes {us_b:,.0f} ART patient-years a year and a Global Fund "
           f"cut {gf_art:,.0f} ({cn['US bilateral (direct channels)']} and {cn['Global Fund (all donors)']} countries funded).",
           "On signed MOU schedules (US bilateral cuts only), ART coverage falls below 90% in Eswatini and Lesotho in "
           "2026 and Kenya in 2028.",
           f"When aid fell in 2002-23, government health spending in {lic['n_countries']} low-income countries did "
           f"not move: {lic['theta']:+.2f} per US$1 lost ({lic['lo']:+.2f} to {lic['hi']:+.2f}).".replace("-0", "−0")]
    rh = (CB - FT) // 5
    for i, t in enumerate(ins):
        y = FT + i * rh
        if i:
            line(s, FL, y, FR, y, color=GRID, width=1.0)
        text(s, FL, y, 640000, rh, [str(i + 1)], size=28, color=NAVY, bold=True, align=PP_ALIGN.CENTER,
             anchor=MSO_ANCHOR.MIDDLE)
        text(s, FL + 731520, y, FW - 731520, rh, [t], size=18, color=BODY, anchor=MSO_ANCHOR.MIDDLE)
    source(s, "Sources: IHME DAH 1990-2026, 2021-23; model output by preset (audit/slide_numbers.md table b, audit/channels, "
              "audit/concentration, audit/fiscal_history).")
    notes.append("Insight 2 comes from a multilateral, all-donor scenario: the Global Fund & Gavi Shortfalls preset at "
                 "its defaults. The Gavi −15% default is the team's estimate.")

    # 17. References: two columns filling the frame
    s = d.content("References")
    refs = [
        ("IHME DAH", "Institute for Health Metrics and Evaluation. Development Assistance for Health Database 1990-2026."),
        ("IHME Health Spending", "Institute for Health Metrics and Evaluation. Health spending 1995-2023 (government "
                                 "health spending, GHES)."),
        ("UNAIDS", "Joint United Nations Programme on HIV/AIDS. AIDSinfo estimates, 2026 release (data for 2025)."),
        ("WHO GTB", "World Health Organization. Global Tuberculosis Report data, 2024."),
        ("MAP", "Malaria Atlas Project. National estimates of net use, spraying and treatment, 2025."),
        ("WUENIC", "WHO/UNICEF Estimates of National Immunization Coverage, 2025 revision."),
        ("WHO GHED", "World Health Organization. Global Health Expenditure Database, December 2025 update."),
        ("GHCC", "Global Health Cost Consortium. Unit Cost Study Repository (HIV ART, TB), 2015-2021 studies."),
        ("IMF WEO", "International Monetary Fund. World Economic Outlook, October 2026."),
        ("WB WDI", "World Bank. World Development Indicators, latest year available."),
        ("OECD ODA 2025", "OECD. Preliminary official development assistance data for 2025, April 2026."),
        ("KFF MOU tracker", "KFF. America First Global Health MOU tracker, 2026; project team MOU schedule sheet."),
        ("Model", "Capstone dashboard model (health_model.py, scenarios.py, prepare_model.py) and audit scripts, "
                  "October 2026.")]
    per = 7
    colw = (FW - 274320) // 2
    slot = (FB - FT) // per
    for k, (ab_, txt) in enumerate(refs):
        c, r = divmod(k, per)
        x, y = FL + c * (colw + 274320), FT + r * slot
        if r:
            line(s, x, y, x + colw, y, color=GRID, width=0.75)
        text(s, x, y, colw, slot, [[(ab_ + ". ", {"bold": True, "color": NAVY_TEXT, "font": "Arial"}), (txt, {})]], size=12,
             color="000000", font="Arial Nova", anchor=MSO_ANCHOR.MIDDLE)
    notes.append("")

    d.save(out, notes)
    print("wrote", out, "with", len(d.prs.slides), "slides")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--team", default=str(HERE / "render" / "team_capstone_deck.pptx"))
    ap.add_argument("--out", default=str(HERE / "dashboard_segment.pptx"))
    a = ap.parse_args()
    build(Path(a.team), Path(a.out))
