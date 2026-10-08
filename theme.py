"""
Design system for the dashboard: colours, fonts, the "editorial" Plotly template, page CSS and shared page pieces.
Every colour used by app.py, model_section.py and pages/ comes from here.

    apply_page(title)            -> set_page_config + CSS + sidebar navigation (call first on every page)
    section_header(icon, title, question, help=None, rule=True)
"""
from __future__ import annotations

import html

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# --------------------------------------------------------------------------- #
# UI colours
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
# Chart colours
# --------------------------------------------------------------------------- #
GRAPE, ROSE, BLUE, TEAL, LILAC, PINK = "#6A3FA8", "#D9485F", "#3B7DD8", "#1D9A8A", "#9A48D0", "#E07AA8"
PALETTE = [GRAPE, ROSE, BLUE, TEAL, LILAC, PINK]      # categorical order, colour-blind checked
OTHER = "#BDB6C8"

DISEASE_COLORS = {"HIV": ROSE, "TB": GRAPE, "Malaria": BLUE, "Immunization": TEAL}

OTHER_SOURCES = "All Other Sources"
FUNDER_COLORS = {"United States": GRAPE, "Gates Foundation": TEAL, "Private Philanthropy": PINK,
                 "United Kingdom": BLUE, "Germany": LILAC, "France": ROSE, OTHER_SOURCES: OTHER}
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


def tint(hex_color: str, alpha: float) -> str:
    """The colour at this opacity, as rgba()."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def cycle(n: int) -> list:
    """n categorical colours: the palette, then the palette at 55% for categories 7-12, then grey."""
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


def style_fig(fig):
    """Apply the editorial look to a finished figure (anything a trace or layout set explicitly is overridden here)."""
    fig.update_layout(template="editorial", plot_bgcolor=SURFACE, paper_bgcolor=SURFACE,
                      font_family=SANS, hoverlabel=dict(bgcolor=SURFACE, bordercolor=RULE,
                                                        font=dict(family=SANS, size=13, color=INK)))
    if fig.layout.title is not None and fig.layout.title.text:
        # left-aligned to the chart's own edge (not the plot area), so long y labels don't push the title out of view
        fig.update_layout(title=dict(font=dict(family=SANS, size=15, color=INK), x=0, xanchor="left", xref="container",
                                     pad=dict(l=10)))
    fig.update_layout(legend_traceorder="normal")
    fig.update_traces(marker_line_color=SURFACE, marker_line_width=2, selector=dict(type="bar"))
    fig.update_xaxes(showgrid=False, gridcolor=RULE, zeroline=False, tickfont=dict(size=12, color=MUTED),
                     title_font=dict(size=12, color=MUTED))
    fig.update_yaxes(gridcolor=RULE, zeroline=False, tickfont=dict(size=12, color=MUTED),
                     title_font=dict(size=12, color=MUTED))
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
h3 {{ font-weight: 600 !important; font-size: 1.35rem !important; padding-top: 1.2rem !important; }}
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

/* sticky country header (Streamlit wraps the container in a layout div of the same height, so that is what sticks;
   top = height of Streamlit's own toolbar) */
[data-testid="stLayoutWrapper"]:has(> .st-key-hdr), .st-key-hdr {{ position: sticky; top: 3.75rem; z-index: 999; }}
.st-key-hdr {{ background: {SURFACE}; border-bottom: 1px solid {RULE}; padding: 0.6rem 0 0.9rem; }}
.ed-country {{ font-family: {SERIF}; font-size: 44px; font-weight: 600; line-height: 1.05; color: {INK};
               margin: 0 0 0.6rem; letter-spacing: -0.015em; }}
.ed-pills {{ display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 8px; }}
.ed-pill {{ background: {SURFACE_TINT}; border: 1px solid {RULE}; border-radius: 10px; padding: 6px 10px;
            line-height: 1.25; min-width: 0; }}
.ed-pill .l {{ display: block; font-size: 11px; color: {MUTED}; white-space: nowrap; overflow: hidden;
               text-overflow: ellipsis; }}
.ed-pill .v {{ display: block; font-size: 14px; font-weight: 700; color: {INK}; }}
@media (max-width: 720px) {{
  .st-key-hdr {{ padding: 0.4rem 0 0.6rem; }}
  .ed-country {{ font-size: 28px; margin-bottom: 0.4rem; }}
  .ed-pills {{ display: flex; overflow-x: auto; scrollbar-width: none; }}
  .ed-pill {{ flex: 0 0 auto; }}
  .ed-pill .v {{ white-space: nowrap; }}
  .st-key-hdr [data-testid="stWidgetLabel"] {{ display: none; }}
  .st-key-hdr [data-testid="stHorizontalBlock"] {{ gap: 0.4rem; }}
}}

/* section headers */
.ed-sec {{ margin-top: 56px; }}
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

/* the funding-cut model controls */
.st-key-model_controls {{ background: {SURFACE_TINT}; }}
</style>
"""

NAV = [("app.py", "Dashboard", ":material/dashboard:"),
       ("pages/2_Validation.py", "Validation & Benchmarks", ":material/fact_check:"),
       ("pages/3_Methods.py", "Methods", ":material/menu_book:")]


def apply_page(title: str = "Health Financing"):
    """Page config, fonts and CSS, and the sidebar (page navigation only). Call before anything else on a page."""
    st.set_page_config(page_title=title, page_icon=":material/monitor_heart:", layout="wide",
                       initial_sidebar_state="collapsed")
    st.markdown(CSS, unsafe_allow_html=True)
    with st.sidebar:
        for page, label, icon in NAV:
            st.page_link(page, label=label, icon=icon)


def section_header(icon: str, title: str, question: str, help: str | None = None, rule: bool = True):
    """Round BRAND badge with a Material icon, a serif title and one muted question underneath."""
    e = html.escape
    tip = (f"<span class='ed-help material-symbols-rounded' title='{e(help, quote=True)}' "
           f"style=\"font-family:'Material Symbols Rounded'\">info</span>") if help else ""
    st.markdown(
        f"<div class='ed-sec{' rule' if rule else ''}'><div class='ed-sec-row'>"
        f"<div class='ed-badge'><span class='material-symbols-rounded'>{e(icon)}</span></div>"
        f"<div class='ed-sec-title'>{e(title)}{tip}</div></div>"
        f"<div class='ed-sec-q'>{e(question)}</div></div>".replace("$", "&#36;"),
        unsafe_allow_html=True)


def pills_html(items) -> str:
    """items: (label, value, tooltip) -> one row of equal-width profile pills."""
    e = html.escape
    return ("<div class='ed-pills'>" + "".join(
        f"<div class='ed-pill' title='{e(tip, quote=True)}'><span class='l'>{e(lbl)}</span>"
        f"<span class='v'>{e(val)}</span></div>" for lbl, val, tip in items) + "</div>").replace("$", "&#36;")
