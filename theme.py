"""
Design system for the dashboard: colors, fonts, the "editorial" Plotly template, page CSS and shared page pieces.
Every color used by app.py, model_section.py and views/ comes from here.

    apply_page(title)            -> set_page_config + CSS + sidebar navigation (call first on every page)
    section_header(icon, title, help=None, rule=True)
"""
from __future__ import annotations

import html

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# --------------------------------------------------------------------------- #
# UI colors
# --------------------------------------------------------------------------- #
INK = "#1F1A2B"            # text
MUTED = "#6B6478"          # secondary text
RULE = "#ECE6F0"           # dividers, borders
SURFACE = "#FFFFFF"
SURFACE_TINT = "#FAF6FB"   # cards, pills
BRAND = "#63458A"          # badges, active states
BRAND_LIGHT = "#E4B7E5"
ACCENT = "#9A48D0"         # links, highlights

# --------------------------------------------------------------------------- #
# Chart colors
# --------------------------------------------------------------------------- #
GRAPE, ROSE, BLUE, TEAL, LILAC, PINK = "#6A3FA8", "#D9485F", "#3B7DD8", "#1D9A8A", "#9A48D0", "#E07AA8"
PALETTE = [GRAPE, ROSE, BLUE, TEAL, LILAC, PINK]      # categorical order, color-blind checked
OTHER = "#BDB6C8"
AMBER = "#C7851F"          # Germany and health systems strengthening (lilac sat too close to grape)
SPARE_FUNDER_COLORS = [PINK, "#8A6D3B", "#5B8DB8"]   # other funders in a country's top 6 (e.g. Japan in Iraq)
TOP_FUNDERS = 6
GENERIC_SOURCES = {"Other", "Unallocable", "Other OECD DAC countries", "Non OECD DAC countries",
                   "Non OECD non DAC countries"}          # never given their own color; they stay in All Other Sources
DISEASE_COLORS = {"HIV": ROSE, "TB": GRAPE, "Malaria": BLUE, "Immunization": TEAL}

OTHER_SOURCES = "All Other Sources"
FUNDER_COLORS = {"United States": GRAPE, "Gates Foundation": TEAL, "Private Philanthropy": PINK,
                 "United Kingdom": BLUE, "Germany": AMBER, "France": ROSE, OTHER_SOURCES: OTHER}
# source names used by the IHME files and the model, mapped onto the six named funders
FUNDER_ALIASES = {"Private other": "Private Philanthropy", "Corporate donations": "Private Philanthropy",
                  "Other private": "Private Philanthropy"}

MAP_RAMP = ["#F3E6F4", "#E4B7E5", "#C58FD6", "#9A48D0", "#63458A", "#3E2466"]   # light to dark
DEEP = MAP_RAMP[-1]


def funder_group(source: str) -> str:
    """IHME/model source name -> one of the six named funders, or 'All Other Sources'."""
    s = FUNDER_ALIASES.get(source, source)
    return s if s in FUNDER_COLORS else OTHER_SOURCES


def funder_color(source: str) -> str:
    return FUNDER_COLORS[funder_group(source)]


def year_axis(y0: int, y1: int) -> dict:
    """A year x-axis with flat labels. Plotly picks the spacing from the chart's width, so a phone shows every fifth
    year and a desktop every year or every other year; labels never rotate or overlap."""
    return dict(range=[y0 - 0.75, y1 + 0.5], tickangle=0, tickformat="d", title="")


def tint(hex_color: str, alpha: float) -> str:
    """The color at this opacity, as rgba()."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def blend(hex_color: str, alpha: float) -> str:
    """The color mixed with white (opaque), as rgb(): looks like tint() on white, but stays the same when drawn over
    another color (treemap children sit on top of their parent box)."""
    h = hex_color.lstrip("#")
    r, g, b = (round(int(h[i:i + 2], 16) * alpha + 255 * (1 - alpha)) for i in (0, 2, 4))
    return f"rgb({r},{g},{b})"


def cycle(n: int) -> list:
    """n categorical colors: the palette, then the palette at 55% for categories 7-12, then grey."""
    seq = PALETTE + [tint(c, 0.55) for c in PALETTE]
    return [seq[i] if i < len(seq) else OTHER for i in range(n)]


# --------------------------------------------------------------------------- #
# Fonts
# --------------------------------------------------------------------------- #
SERIF = "'Source Serif 4', Georgia, 'Times New Roman', serif"
SERIF_ATTR = SERIF.replace("'", "&quot;")       # for style='' attributes
SANS = "'Libre Franklin', 'Helvetica Neue', Arial, sans-serif"
FONTS_URL = ("https://fonts.googleapis.com/css2?family=Libre+Franklin:wght@400;500;600;700"
             "&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&display=swap")
ICONS_URL = "https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,500,0,0"

# --------------------------------------------------------------------------- #
# Plotly template
# --------------------------------------------------------------------------- #
_axis = dict(showgrid=False, zeroline=False, showline=False, ticks="", automargin=True,
             tickfont=dict(family=SANS, size=12, color=MUTED), title=dict(font=dict(family=SANS, size=12, color=MUTED)))
pio.templates["editorial"] = go.layout.Template(
    layout=dict(
        font=dict(family=SANS, size=12, color=INK),
        paper_bgcolor=SURFACE, plot_bgcolor=SURFACE, colorway=PALETTE,
        title=dict(font=dict(family=SANS, size=15, color=INK), x=0, xanchor="left", xref="container",
                   pad=dict(l=10)),
        xaxis=_axis, yaxis={**_axis, "showgrid": True, "gridcolor": RULE, "gridwidth": 1},
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="left", x=0, title_text="", traceorder="normal",
                    font=dict(family=SANS, size=12, color=MUTED)),
        hoverlabel=dict(bgcolor=SURFACE, bordercolor=RULE, font=dict(family=SANS, size=13, color=INK)),
        colorscale=dict(sequential=[[i / (len(MAP_RAMP) - 1), c] for i, c in enumerate(MAP_RAMP)]),
        margin=dict(l=10, r=10, t=50, b=10),
    ),
    data=dict(bar=[go.Bar(marker=dict(line=dict(color=SURFACE, width=2)))]),
)
pio.templates.default = "editorial"


ZERO_LINE = "#A9A1B5"        # darker than the gridlines
LEGEND_GAP_PX = 34           # legend top sits this far below the plot (room for the tick labels)


def source_html(source: str | None = None, note: str | None = None) -> str:
    """The small grey 'Note: ... Source: ...' line NYT puts under every chart."""
    parts = []
    if note:
        parts.append(f"<b>Note:</b> {html.escape(note)}")
    if source:
        parts.append(f"<b>Source:</b> {html.escape(source)}")
    return f"<div class='ed-source'>{' '.join(parts)}</div>".replace("$", "&#36;") if parts else ""


SHORT_NAMES = {"Reproductive & Maternal Health": "Maternal Health", "Newborn & Child Health": "Child Health",
               "Health Systems Strengthening": "Health Systems", "Tuberculosis": "TB", "HIV/AIDS": "HIV",
               "World Bank Lending": "World Bank", "Private Philanthropy": "Philanthropy", "Gates Foundation": "Gates",
               "United States": "US", "United Kingdom": "UK", "All Other Sources": "All Other",
               "Foreign Aid for Health": "Foreign Aid", "Out-of-Pocket": "Out of Pocket"}


def short_name(name: str) -> str:
    base = name.split(" (")[0]
    return SHORT_NAMES.get(base, base)


def title_sub(title: str, sub: str) -> str:
    """A short chart title with a small grey subtitle under it (keeps titles short enough for a phone)."""
    return f"{title}<br><span style='font-size:12px;color:{MUTED}'>{sub}</span>"


def color_key(items) -> str:
    """An inline key for a chart subtitle: names written in their own colors ('HIV  TB  Malaria ...')."""
    return "   ".join(f"<span style='color:{c}'><b>{html.escape(n)}</b></span>" for n, c in items)


def _trace_color(t):
    c = t.marker.color if t.type == "bar" else (t.line.color if t.line else None)
    return c if isinstance(c, str) else None


def direct_labels(fig, min_gap_px: float = 18):
    """NYT-style labels at the right end of a stacked vertical bar chart instead of a legend: each series is named
    just past the last bar, level with its segment and in its color; labels are pushed apart so they never overlap,
    and anything in parentheses is dropped to keep them short."""
    bars = [t for t in fig.data if t.type == "bar" and t.orientation != "h" and t.x is not None and len(t.x)]
    named = [t for t in bars if t.showlegend is not False and t.name]
    if not named:
        return fig
    xs = [x for t in bars for x, y in zip(t.x, t.y) if y is not None and y == y and y != 0]
    if not xs:
        return fig
    categorical = isinstance(xs[0], str) or fig.layout.xaxis.type == "category"
    if categorical:                                    # category axes: positions are 0, 1, 2, ... in data units
        cats = list(dict.fromkeys(x for t in bars for x in t.x))
        x_last = max(xs, key=cats.index)
        x_pos = cats.index(x_last) + 0.5
        if fig.layout.xaxis.range is None:             # keep the labels from widening the axis
            fig.update_xaxes(range=[-0.5, len(cats) - 0.5])
    else:
        x_last = max(xs)
        x_pos = x_last + 0.5
    stack, segs = 0.0, []
    for t in bars:                                     # stack order = trace order
        y = dict(zip(t.x, t.y)).get(x_last)
        y = 0.0 if y is None or y != y else float(y)
        if y <= 0:
            continue
        if t in named:
            segs.append([stack + y / 2, short_name(t.name), _trace_color(t)])
        stack += y
    if not segs:
        return fig
    totals = {}                                         # the axis is scaled to the tallest stack, not the last one
    for t in bars:
        for x, y in zip(t.x, t.y):
            if y is not None and y == y and y > 0:
                totals[x] = totals.get(x, 0.0) + float(y)
    yr = fig.layout.yaxis.range
    top = float(yr[1]) if yr is not None else max(totals.values()) * 1.06
    m = fig.layout.margin
    plot_px = max((fig.layout.height or 450) - (m.t or 50) - (m.b or 10) - 40, 120)
    gap = min_gap_px / plot_px * top
    segs.sort(key=lambda s: s[0])                        # push apart from the bottom up, then down from the top
    for i in range(1, len(segs)):
        segs[i][0] = max(segs[i][0], segs[i - 1][0] + gap)
    if segs[-1][0] > top - gap / 2:
        segs[-1][0] = top - gap / 2
        for i in range(len(segs) - 2, -1, -1):
            segs[i][0] = min(segs[i][0], segs[i + 1][0] - gap)
    for yv, name, col in segs:
        fig.add_annotation(x=x_pos, y=yv, xref="x", yref="y", text=f"<b>{name}</b>", showarrow=False,
                           xanchor="left", xshift=6, font=dict(size=12, color=col or INK, family=SANS))
    room = 16 + 7 * max(len(n) for _, n, _ in segs)   # ~7px per character at 12px bold
    fig.update_layout(showlegend=False, margin=dict(r=max((m.r or 10), room)))
    return fig


def _horizontal(fig) -> bool:
    """True when the categories run down the y axis (horizontal bars, dot plots with labelled rows)."""
    for t in fig.data:
        if t.type == "bar" and t.orientation == "h":
            return True
        if t.type == "scatter" and t.y is not None and len(t.y) and isinstance(t.y[0], str):
            return True
    return False


def style_fig(fig):
    """Apply the editorial look to a finished figure: fonts, title, gridlines on the value axis only (horizontal for
    vertical bars and lines, vertical for horizontal bars), a darker zero line, 2px white gaps between stacked
    segments, and the legend directly under the plot."""
    fig.update_layout(template="editorial", plot_bgcolor=SURFACE, paper_bgcolor=SURFACE,
                      font_family=SANS, hoverlabel=dict(bgcolor=SURFACE, bordercolor=RULE,
                                                        font=dict(family=SANS, size=13, color=INK)))
    if fig.layout.title is not None and fig.layout.title.text:
        # left-aligned to the chart's own edge (not the plot area), so long y labels don't push the title out of view
        fig.update_layout(title=dict(font=dict(family=SANS, size=15, color=INK), x=0, xanchor="left", xref="container",
                                     pad=dict(l=10)))
        if "<br>" in fig.layout.title.text:            # a subtitle: room for two lines above the plot
            fig.update_layout(title=dict(y=0.985, yanchor="top", yref="container"),
                              margin=dict(t=max(fig.layout.margin.t or 0, 74)))
    if not any(getattr(t, "legendrank", None) not in (None, 1000) for t in fig.data):
        fig.update_layout(legend_traceorder="normal")      # charts that set legendrank keep their own order
    for t in fig.data:                 # 2px white gaps between stacked segments, unless a chart sets its own width
        if t.type == "bar" and t.marker.line.width is None:
            t.marker.line.color, t.marker.line.width = SURFACE, 2
    axis_font = dict(tickfont=dict(size=12, color=MUTED), title_font=dict(size=12, color=MUTED))
    fig.update_xaxes(**axis_font, ticklabelstandoff=6)
    fig.update_yaxes(**axis_font)
    if not any(t.type in ("bar", "scatter") for t in fig.data):
        return fig                     # treemaps and maps have no axes
    horiz = _horizontal(fig)
    value_upd, cat_upd = (fig.update_xaxes, fig.update_yaxes) if horiz else (fig.update_yaxes, fig.update_xaxes)
    value_upd(showgrid=True, gridcolor=RULE, gridwidth=1, zeroline=True, zerolinecolor=ZERO_LINE, zerolinewidth=1)
    cat_upd(showgrid=False, zeroline=False)
    # legend directly under the plot: y is a fraction of the plot height, so convert the pixel gap
    if fig.layout.showlegend is not False and fig.layout.legend.orientation in (None, "h") \
            and sum(1 for t in fig.data if t.showlegend is not False and t.name) > 1:
        m = fig.layout.margin
        plot_h = max((fig.layout.height or 450) - (m.t if m.t is not None else 50) - (m.b if m.b is not None else 10)
                     - 40, 120)
        gap = LEGEND_GAP_PX + (18 if fig.layout.xaxis.title.text else 0)
        fig.update_layout(legend=dict(orientation="h", yanchor="top", y=-gap / plot_h, xanchor="left", x=0))
    return fig


# --------------------------------------------------------------------------- #
# Page CSS and shared page pieces
# --------------------------------------------------------------------------- #
CSS = f"""
<style>
@import url('{FONTS_URL}');
@import url('{ICONS_URL}');
html, body, .stApp, .stMarkdown, button, input, select, textarea {{ font-family: {SANS}; }}
.stApp {{ background: {SURFACE}; color: {INK}; }}
.stMainBlockContainer {{ max-width: 1150px; padding-top: 3.5rem; padding-bottom: 6rem; }}
h1, h2, h3, h4 {{ font-family: {SERIF} !important; color: {INK}; letter-spacing: -0.01em; }}
h2 {{ font-weight: 600 !important; }}
h3 {{ font-weight: 600 !important; font-size: 1.35rem !important; }}
/* subsection headers (st.subheader): 48px above (32px + Streamlit's 16px gap) and 20px below (Streamlit pulls a
   markdown block up by 16px, which cancels the gap underneath, so all 20px come from the padding) */
[data-testid="stHeading"]:has(h3) {{ padding-top: 32px; }}
[data-testid="stHeading"] h3 {{ padding-top: 0 !important; padding-bottom: 20px !important; margin: 0 !important; }}
a {{ color: {ACCENT}; }}
[data-testid="stCaptionContainer"], .stCaption {{ color: {MUTED} !important; }}
hr {{ border-color: {RULE} !important; }}

/* metrics: quiet grey label, big serif number */
[data-testid="stMetric"] {{ background: {SURFACE}; border-color: {RULE} !important; border-radius: 10px; }}
[data-testid="stMetricLabel"] p {{ color: {MUTED}; font-size: 0.82rem; }}
[data-testid="stMetricValue"] {{ font-family: {SERIF}; font-weight: 600; color: {INK}; }}
[data-testid="stMetricDelta"] {{ color: {MUTED} !important; }}
[data-testid="stExpander"] details {{ border-color: {RULE}; border-radius: 10px; }}
[data-testid="stTable"] table, [data-testid="stTable"] th, [data-testid="stTable"] td {{ border-color: {RULE} !important; }}
[data-testid="stTable"] th {{ color: {MUTED}; font-weight: 600; }}

/* Streamlit's own top bar (with the page links) is opaque, so nothing shows through above the sticky header */
[data-testid="stHeader"] {{ background: {SURFACE}; }}

/* sticky country header (Streamlit wraps the container in a layout div of the same height, so that is what sticks;
   top = height of Streamlit's own top bar) */
[data-testid="stLayoutWrapper"]:has(> .st-key-hdr), .st-key-hdr {{ position: sticky; top: 3.75rem; z-index: 999; }}
[data-testid="stLayoutWrapper"]:has(> .st-key-hdr) {{ margin-bottom: 24px; }}
.st-key-hdr {{ background: {SURFACE}; border-bottom: 1px solid {RULE}; box-shadow: 0 2px 8px rgba(31,26,43,0.06);
               padding: 0.5rem 20px 20px !important; }}      /* side padding keeps text off the edges */
/* a short white fade under the border, so content sliding under the header never butts up against it */
.st-key-hdr::after {{ content: ""; position: absolute; left: 0; right: 0; top: calc(100% + 1px); height: 14px;
                      background: linear-gradient({SURFACE}, rgba(255,255,255,0)); pointer-events: none; }}
.ed-country {{ font-family: {SERIF}; font-size: 36px; font-weight: 600; line-height: 1.05; color: {INK};
               margin: 0 0 0.5rem; letter-spacing: -0.015em; }}

.ed-units {{ font-family: {SANS}; font-size: 12px; font-weight: 400; color: {MUTED}; margin-left: 14px;
             letter-spacing: 0; vertical-align: middle; }}
@media (max-width: 720px) {{ .ed-units {{ display: block; margin: 2px 0 0; }} }}

/* pills: ONE component for every pill row. Equal width and equal height in a row (grid, rows stretch); label at the
   top, value at the bottom; long labels wrap, nothing is cut off */
.ed-pills {{ display: grid; gap: 8px; grid-auto-rows: 1fr; align-items: stretch; margin-bottom: 0 !important; }}
/* Streamlit pulls the last block of a markdown element up by 1rem; cancel that so pills never overflow their row */
[data-testid="stMarkdownContainer"]:has(.ed-pills) {{ margin-bottom: 0 !important; }}
[data-testid="stMarkdownContainer"] > div:has(> .ed-pills), [data-testid="stMarkdownContainer"] .ed-pills:last-child
    {{ margin-bottom: 0 !important; }}
.ed-pill {{ background: {SURFACE_TINT}; border: 1px solid {RULE}; border-radius: 10px; padding: 8px 12px;
            display: flex; flex-direction: column; justify-content: space-between; min-width: 0; line-height: 1.25; }}
.ed-pill .l {{ display: block; font-size: 11px; color: {MUTED}; overflow-wrap: anywhere; }}
.ed-pill .v {{ display: block; font-size: 14px; font-weight: 700; color: {INK}; margin-top: 4px; }}
.ed-pill .n {{ display: block; font-size: 11.5px; color: {MUTED}; margin-top: 2px; }}
.st-key-hdr .ed-pill {{ min-height: 64px; }}
.ed-pills.lg {{ gap: 12px; margin: 0.4rem 0 1rem !important; }}
.ed-pills.lg .ed-pill {{ padding: 12px 16px; min-height: 96px; }}
.ed-pills.lg .l {{ font-size: 12.5px; }}
.ed-pills.lg .v {{ font-family: {SERIF}; font-size: 28px; font-weight: 600; line-height: 1.15; margin-top: 8px; }}
@media (max-width: 720px) {{
  .st-key-hdr {{ padding: 0.3rem 14px 14px !important; }}
  .ed-country {{ font-size: 26px; margin-bottom: 0.35rem; }}
  .st-key-hdr .ed-pills {{ display: flex; overflow-x: auto; scrollbar-width: none; align-items: stretch; }}
  .st-key-hdr .ed-pill {{ flex: 0 0 128px; min-height: 58px; }}
  .st-key-hdr [data-testid="stWidgetLabel"] {{ display: none; }}
  .st-key-hdr [data-testid="stHorizontalBlock"] {{ gap: 0.4rem; }}
  .ed-pills.lg {{ grid-template-columns: repeat(2, minmax(0, 1fr)) !important; }}
  .ed-pills.lg .v {{ font-size: 23px; }}
}}

/* "what each service loses" table */
.ed-table {{ width: 100%; border-collapse: collapse; font-size: 14px; margin: 0.3rem 0 0.4rem; }}
.ed-table th {{ color: {MUTED}; font-weight: 600; font-size: 12.5px; text-align: left; padding: 8px 10px;
                border-bottom: 1px solid {RULE}; vertical-align: bottom; }}
.ed-table td {{ padding: 9px 10px; border-bottom: 1px solid {RULE}; vertical-align: top; color: {INK}; }}
.ed-table .num {{ text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }}
.ed-table .cov {{ white-space: nowrap; }}
.ed-table .drop {{ color: {ROSE}; font-weight: 700; }}
.ed-table-wrap {{ overflow-x: auto; }}

/* "what each service loses": NYT-style table */
.ed-nyt-wrap {{ overflow-x: auto; margin: 0.2rem 0 0.4rem; }}
.ed-nyt {{ width: 100%; min-width: 980px; border-collapse: collapse; table-layout: fixed; font-size: 14px; color: {INK};
           font-family: {SANS}; }}
.ed-nyt th {{ font-size: 12px; font-weight: 600; color: {MUTED}; text-align: center; vertical-align: bottom;
              padding: 0 8px 10px; border-bottom: 1px solid {RULE}; line-height: 1.3; }}
.ed-nyt th:first-child {{ text-align: left; padding-left: 14px; }}
.ed-nyt td {{ text-align: center; white-space: nowrap; padding: 14px 8px; border-bottom: 1px solid {RULE};
              vertical-align: middle; line-height: 1.35; font-variant-numeric: tabular-nums; }}
.ed-nyt td.svc {{ text-align: left; white-space: normal; padding-left: 12px; }}
.ed-nyt tbody tr:not(.gap):not(.tot):hover td {{ background: {SURFACE_TINT}; }}
.ed-nyt .sub {{ font-size: 12px; color: {MUTED}; font-weight: 400; }}
.ed-nyt .big {{ font-size: 16px; font-weight: 600; }}
.ed-nyt .nm {{ color: {MUTED}; font-size: 13px; }}
.ed-nyt .dot {{ display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 7px;
                vertical-align: 1px; }}
.ed-nyt .drop {{ display: inline-block; margin-top: 3px; padding: 1px 8px; border-radius: 999px; font-size: 12px;
                 font-weight: 700; color: {ROSE}; background: rgba(217,72,95,0.10); }}
.ed-nyt tr.gap td {{ padding: 0; height: 8px; border-bottom: none; }}
.ed-nyt tr.tot td {{ border-top: 2px solid {INK}; border-bottom: none; }}

/* service cards (every US$1M lost) */
.ed-card {{ background: {SURFACE_TINT}; border: 1px solid {RULE}; border-top: 4px solid; border-radius: 10px;
            padding: 14px 16px; height: 100%; }}
.ed-card .t {{ font-family: {SERIF}; font-weight: 600; font-size: 1.25rem; color: {INK}; }}
.ed-cards {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; align-items: stretch; }}
.ed-card {{ display: flex; flex-direction: column; }}
.ed-card .s1 {{ font-size: 0.92rem; font-weight: 600; color: {INK}; white-space: nowrap; overflow-wrap: normal; }}
.ed-card .s {{ font-size: 0.8rem; color: {MUTED}; margin-bottom: 6px; }}
.ed-card .none {{ font-size: 0.85rem; color: {MUTED}; margin-top: 14px; line-height: 1.35; }}
.ed-card .foot {{ margin-top: auto !important; }}
@media (max-width: 720px) {{ .ed-cards {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} }}
.ed-card .big {{ font-family: {SERIF}; font-size: 30px; font-weight: 600; line-height: 1.1; color: {INK}; margin-top: 10px; }}
.ed-card .lbl {{ font-size: 12px; color: {MUTED}; }}
.ed-card .foot {{ font-size: 12px; color: {MUTED}; margin-top: 12px; padding-top: 8px; border-top: 1px solid {RULE}; }}

/* section headers */
.ed-sec {{ margin-top: 56px; margin-bottom: 32px; }}      /* 32px under the title (the element gap is cancelled) */
.ed-sec.rule {{ border-top: 1px solid {RULE}; padding-top: 40px; }}
.ed-sec-row {{ display: flex; align-items: center; gap: 14px; }}
.ed-badge {{ flex: 0 0 36px; width: 36px; height: 36px; border-radius: 50%; background: {BRAND}; color: {SURFACE};
             display: flex; align-items: center; justify-content: center; }}
.ed-badge .material-symbols-rounded {{ font-family: 'Material Symbols Rounded'; font-size: 20px; line-height: 1;
             font-weight: normal; font-style: normal; letter-spacing: normal; text-transform: none; white-space: nowrap;
             -webkit-font-feature-settings: 'liga'; font-feature-settings: 'liga'; -webkit-font-smoothing: antialiased; }}
.ed-sec-title {{ font-family: {SERIF}; font-size: 30px; font-weight: 600; line-height: 1.15; color: {INK};
                 margin: 0; letter-spacing: -0.01em; }}
.ed-sec-q {{ color: {MUTED}; font-size: 16px; margin: 6px 0 4px 50px; }}
.ed-help {{ color: {MUTED}; font-size: 15px; cursor: help; margin-left: 6px; vertical-align: middle; }}
@media (max-width: 720px) {{
  .ed-sec-title {{ font-size: 23px; }}
  .ed-sec-q {{ margin-left: 0; }}
}}

/* the funding-cut model control bar */
.st-key-model_controls {{ background: {SURFACE_TINT}; border-color: {RULE} !important; border-radius: 12px; }}
/* ---- dropdowns: white with a visible border (and a purple border on hover / focus), so they read as controls on
   both the white page and the tinted scenario bar ---- */
[data-testid="stSelectbox"] .react-aria-ComboBox > div, [data-baseweb="select"] > div {{
    background-color: {SURFACE} !important; border: 1px solid #B8AEC6 !important; border-radius: 8px !important;
    box-shadow: 0 1px 2px rgba(31,26,43,0.06); }}
[data-testid="stSelectbox"] .react-aria-ComboBox > div:hover, [data-baseweb="select"] > div:hover {{
    border-color: {BRAND} !important; }}
[data-testid="stSelectbox"] .react-aria-ComboBox > div:focus-within, [data-baseweb="select"] > div:focus-within {{
    border-color: {BRAND} !important; box-shadow: 0 0 0 2px {BRAND_LIGHT} !important; }}
[data-testid="stSelectbox"] .react-aria-ComboBox button svg, [data-baseweb="select"] svg {{ color: {BRAND} !important; }}
.st-key-model_controls {{ background: {SURFACE_TINT}; border-radius: 12px; padding: 12px 16px 6px !important; }}

/* ---- no app chrome: the page should read like a website ---- */
[data-testid="stAppDeployButton"], [data-testid="stMainMenu"], #MainMenu, [data-testid="stDecoration"],
[data-testid="stStatusWidget"], [data-testid="stToolbarActions"], footer {{ display: none !important; }}

/* ---- running text uses the full width of the page, like the charts ---- */
[data-testid="stMarkdownContainer"] > p {{ font-size: 16.5px; line-height: 1.6; }}

/* ---- story lede (top of the Dashboard) ---- */
.ed-lede {{ margin: 8px 0 6px; }}
.ed-kicker {{ font-family: {SANS}; font-size: 12px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;
              color: {ACCENT}; margin-bottom: 10px; }}
.ed-headline {{ font-family: {SERIF}; font-size: 42px; line-height: 1.12; font-weight: 600; color: {INK};
                letter-spacing: -0.015em; margin: 0 0 14px; }}
.ed-dek {{ font-family: {SANS}; font-size: 19px; line-height: 1.5; color: #4A4458; margin: 0 0 26px; }}
.ed-bignums {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); border-top: 1px solid {INK};
               border-bottom: 1px solid {RULE}; margin: 0 0 18px; }}
.ed-bignum {{ padding: 14px 18px 16px 0; }}
.ed-bignum + .ed-bignum {{ border-left: 1px solid {RULE}; padding-left: 18px; }}
.ed-bignum .v {{ font-family: {SERIF}; font-size: 40px; font-weight: 600; line-height: 1.05; color: {INK}; }}
.ed-bignum .v.hl {{ color: {ROSE}; }}
.ed-bignum .l {{ font-size: 13px; font-weight: 600; color: {INK}; margin-top: 6px; }}
.ed-bignum .n {{ font-size: 12.5px; color: {MUTED}; margin-top: 2px; }}
@media (max-width: 720px) {{
  .ed-headline {{ font-size: 28px; }}
  .ed-dek {{ font-size: 16.5px; }}
  .ed-bignums {{ grid-template-columns: 1fr; }}
  .ed-bignum + .ed-bignum {{ border-left: none; border-top: 1px solid {RULE}; padding-left: 0; }}
  .ed-bignum .v {{ font-size: 32px; }}
}}

/* ---- "Source:" line under every chart ---- */
.ed-source {{ font-family: {SANS}; font-size: 12px; color: {MUTED}; margin: -10px 0 6px;
              line-height: 1.45; }}
.ed-source b {{ font-weight: 600; color: #4A4458; }}
</style>
"""

PAGES = [("views/1_Dashboard.py", "Dashboard", ":material/dashboard:"),
         ("views/2_All_Countries.py", "All Countries", ":material/travel_explore:"),
         ("views/3_Validation.py", "Validation & Benchmarks", ":material/fact_check:"),
         ("views/4_Methods.py", "Methods", ":material/menu_book:")]


def setup():
    """Page config, fonts and CSS. Called once per run by app.py, before the selected page runs."""
    st.set_page_config(page_title="Health Financing", page_icon=":material/monitor_heart:", layout="wide",
                       initial_sidebar_state="collapsed")
    st.markdown(CSS, unsafe_allow_html=True)


def shared_select(label, options, widget_key, shared_key, default, **kw):
    """A selectbox whose choice is shared by every page: the widget is set from st.session_state[shared_key] on each
    run, and changing it writes back to shared_key, so switching pages keeps the choice."""
    cur = st.session_state.get(shared_key, default)
    st.session_state[widget_key] = cur if cur in options else default
    def _sync():
        st.session_state[shared_key] = st.session_state[widget_key]
    val = st.selectbox(label, options, key=widget_key, on_change=_sync, **kw)
    st.session_state[shared_key] = val
    return val


def section_header(icon: str, title: str, help: str | None = None, rule: bool = True):
    """Round BRAND badge with a Material icon and a serif title (an info icon carries `help` as a tooltip)."""
    e = html.escape
    tip = (f"<span class='ed-help material-symbols-rounded' title='{e(help, quote=True)}' "
           f"style=\"font-family:'Material Symbols Rounded'\">info</span>") if help else ""
    st.markdown(
        f"<div class='ed-sec{' rule' if rule else ''}'><div class='ed-sec-row'>"
        f"<div class='ed-badge'><span class='material-symbols-rounded'>{e(icon)}</span></div>"
        f"<div class='ed-sec-title'>{e(title)}{tip}</div></div></div>".replace("$", "&#36;"),
        unsafe_allow_html=True)


def pills_html(items, cols: int | None = None, large: bool = False) -> str:
    """The one pill component. items: (label, value, tooltip[, small note under the value]). Every pill in a row has
    the same width and height. A note that only repeats the value (e.g. 'Net of Backfill $4.26B' when nothing is
    replaced) is dropped. large=True: big serif values, for stats inside the page."""
    e = html.escape
    cells = []
    for it in items:
        lbl, val, tip = it[:3]
        note = it[3] if len(it) > 3 and it[3] else ""
        if note and str(val) and str(val) in note:
            note = ""
        cells.append(f"<div class='ed-pill' title='{e(tip or '', quote=True)}'><span class='l'>{e(lbl)}</span>"
                     f"<span><span class='v'>{e(str(val))}</span>"
                     + (f"<span class='n'>{e(note)}</span>" if note else "") + "</span></div>")
    n = cols or len(items)
    return (f"<div class='ed-pills{' lg' if large else ''}' style='grid-template-columns:repeat({n}, minmax(0, 1fr))'>"
            + "".join(cells) + "</div>").replace("$", "&#36;")
