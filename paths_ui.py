"""
How funding changes over 2026-2030, and a gradual government budget increase: the controls inside the scenario box,
the chart with one red slider (aid cut) and one blue slider (extra health share) per year, and the outcome pills.

    path_selector(ci, iso3)                -> the "How Funding Changes" dropdown (shape name)
    gradual_controls(budget)               -> shape dropdown + points-per-year input (Gradual Budget Increase only)
    year_panel(...)                        -> chart + sliders; returns (cut_path, extra_points)
    outcome_panel(...)                     -> benchmark line, four pills, sentence, caption
Session-state keys start with "m_" so the navigation keeps them when switching pages.
"""
from __future__ import annotations

import html

import numpy as np
import plotly.graph_objects as go
import streamlit as st

import health_model as hm
import scenarios as scn
import theme as th

SUDDEN = scn.PATH_SHAPES[0]
YEARS = scn.YEARS
CUT_KEYS = [f"m_cut_{y}" for y in YEARS]          # 0-100, share of the full cut in force (%)
GOV_KEYS = [f"m_gov_{y}" for y in YEARS]          # extra points of the government budget going to health (cumulative)
DEFAULT_POINTS = 0.5


def _fmt(v: float) -> str:
    a = abs(v)
    return f"${v / 1e9:,.2f}B" if a >= 1e9 else f"${v / 1e6:,.1f}M" if a >= 1e6 else f"${v / 1e3:,.0f}K" if a >= 1e3 \
        else f"${v:,.0f}"


# --------------------------------------------------------------------------- #
# State helpers (callbacks run before the next rerun, so they may set widget values)
# --------------------------------------------------------------------------- #
def _fill_cut(shape: str, mou):
    for k, v in zip(CUT_KEYS, scn.path_shape(shape, mou)):
        st.session_state[k] = int(round(v * 100))
    if shape != "Custom":
        st.session_state["m_path_last"] = shape


def _fill_gov(shape: str, room: float):
    pts = float(st.session_state.get("m_gov_pts", DEFAULT_POINTS))
    for k, v in zip(GOV_KEYS, scn.gov_shape(shape, pts, room)):
        st.session_state[k] = round(v, 1)
    if shape != "Custom":
        st.session_state["m_gov_last"] = shape


def _on_shape(mou):
    shape = st.session_state["m_path_shape"]
    if shape != "Custom":
        _fill_cut(shape, mou)


def _on_cut_slider():
    st.session_state["m_path_shape"] = "Custom"


def _on_gov_shape(room):
    if st.session_state["m_gov_shape"] != "Custom":
        _fill_gov(st.session_state["m_gov_shape"], room)


def _on_gov_slider():
    st.session_state["m_gov_shape"] = "Custom"


def _reset(mou, room):
    last = st.session_state.get("m_path_last", SUDDEN)
    st.session_state["m_path_shape"] = last
    _fill_cut(last, mou)
    if room > 0:                                       # only while a gradual budget increase is on
        g = st.session_state.get("m_gov_last", "Steady")
        st.session_state["m_gov_shape"] = g
        _fill_gov(g, room)


# --------------------------------------------------------------------------- #
# Dropdowns
# --------------------------------------------------------------------------- #
def path_selector(ci, iso3: str) -> str:
    """'How Funding Changes'. MOU Schedule is offered only where the team's sheet has a 2026-2030 schedule."""
    mou = scn.mou_cut_path(ci, iso3)
    options = [s for s in scn.PATH_SHAPES if s != "MOU schedule" or mou is not None]
    if st.session_state.get("m_path_shape") not in options:            # first visit, or MOU shape on a non-MOU country
        st.session_state["m_path_shape"] = SUDDEN
        _fill_cut(SUDDEN, mou)
    if any(k not in st.session_state for k in CUT_KEYS):
        _fill_cut(st.session_state["m_path_shape"] if st.session_state["m_path_shape"] != "Custom" else SUDDEN, mou)
    if st.session_state.get("m_path_iso") != iso3:                    # new country: refill a shape that depends on it
        st.session_state["m_path_iso"] = iso3
        if st.session_state["m_path_shape"] == "MOU schedule":
            _fill_cut("MOU schedule", mou)
    from model_section import title_case
    return st.selectbox("How Funding Changes", options, key="m_path_shape", format_func=title_case,
                        on_change=_on_shape, args=(mou,),
                        help="How the scenario's cut is phased in over 2026-2030. Sudden = the full cut from 2026. "
                             "Phase-outs reach the full cut by 2030; the sliders below set each year.")


def gradual_controls(budget: dict) -> float:
    """Shape and pace of a gradual government budget increase. Returns the room left to the Abuja ceiling."""
    from model_section import title_case
    room = float(budget["room_pct"]) if budget["room_pct"] == budget["room_pct"] else 0.0
    if st.session_state.get("m_gov_shape") not in scn.GOV_SHAPES:
        st.session_state["m_gov_shape"] = "Steady"
    if "m_gov_pts" not in st.session_state:
        st.session_state["m_gov_pts"] = DEFAULT_POINTS
    # (re)fill the year values when the panel is switched on, unless the user had set them by hand (Custom)
    if any(k not in st.session_state for k in GOV_KEYS) or not st.session_state.get("gov_panel_on"):
        if st.session_state["m_gov_shape"] != "Custom" or any(k not in st.session_state for k in GOV_KEYS):
            _fill_gov(st.session_state["m_gov_shape"] if st.session_state["m_gov_shape"] != "Custom" else "Steady",
                      room)
    st.session_state["gov_panel_on"] = True
    a, b = st.columns(2)
    a.selectbox("Budget Increase Shape", scn.GOV_SHAPES, key="m_gov_shape", format_func=title_case,
                on_change=_on_gov_shape, args=(room,))
    b.number_input("Points per Year", min_value=0.0, max_value=max(round(room / 5, 1), 0.1), step=0.1, format="%.1f",
                   key="m_gov_pts", on_change=_on_gov_shape, args=(room,),
                   help="Extra percentage points of the government budget going to health, added each year "
                        "(cumulative). Sets the default year values below.")
    return room


# --------------------------------------------------------------------------- #
# Chart + sliders
# --------------------------------------------------------------------------- #
def year_panel(iso3, country_name, scenario, fiscal, I, gradual: bool, budget: dict, room: float, mou):
    """One chart (2026-2030) with a row of per-year sliders under it. Returns (cut_path 0-1, extra points)."""
    chart_slot = st.container()
    cols = st.columns(5, gap="small")
    for y, c, ck, gk in zip(YEARS, cols, CUT_KEYS, GOV_KEYS):
        with c:
            st.markdown(f"<div class='ed-year'>{y}</div>", unsafe_allow_html=True)
            with st.container(key=f"cutsl_{y}"):
                st.slider("Aid Cut", 0, 100, step=5, key=ck, format="%d%%", on_change=_on_cut_slider)
            if gradual:
                with st.container(key=f"govsl_{y}"):
                    if room > 0:
                        st.session_state[gk] = min(float(st.session_state.get(gk, 0.0)), room)
                        st.slider("Extra Health Share", 0.0, float(room), step=0.1, key=gk, format="+%.1f pts",
                                  on_change=_on_gov_slider)
                    else:
                        st.caption("Already at the 15% target")
    cut = [st.session_state[k] / 100 for k in CUT_KEYS]
    pts = [float(st.session_state.get(k, 0.0)) if gradual and room > 0 else 0.0 for k in GOV_KEYS]
    falls = [YEARS[i] for i in range(1, 5) if cut[i] < cut[i - 1] - 1e-9]
    r1, r2 = st.columns([4, 1])
    if falls:
        r1.caption(f"Note: the cut falls in {', '.join(map(str, falls))}. That is read as aid returning, and people "
                   "return to care.")
    r2.button("Reset to Shape", type="tertiary", key="path_reset_btn", on_click=_reset, args=(mou, room),
              icon=":material/restart_alt:")

    gov_usd = hm.gov_add_from_points(pts, budget["gov_spend_usd"])
    G_t, R_t = hm._money_by_year(iso3, scenario, fiscal, I, cut)
    with chart_slot:
        _chart(cut, pts, G_t, R_t, gov_usd, gradual)
    return cut, pts


def _chart(cut, pts, G_t, R_t, gov_usd, gradual):
    gap = G_t - np.minimum(R_t + gov_usd, G_t)
    fig = go.Figure()
    for i, y in enumerate(YEARS):                    # shading: unfilled gap (red) or government keeps up (blue)
        unfilled = gap[i] > 1e-6 and G_t[i] > 0
        fig.add_vrect(x0=y - 0.5, x1=y + 0.5, layer="below", line_width=0,
                      fillcolor=th.tint(th.ROSE if unfilled else th.BLUE, 0.08 if unfilled else 0.07))
    first_red = next((y for i, y in enumerate(YEARS) if gap[i] > 1e-6 and G_t[i] > 0), None)
    first_blue = next((y for i, y in enumerate(YEARS) if not (gap[i] > 1e-6 and G_t[i] > 0)), None)
    for y, txt, col in ((first_red, "Unfilled Gap", th.ROSE), (first_blue, "Gap Filled", th.BLUE)):
        if y is not None:                          # short, at the bottom-left of the first block of each kind
            fig.add_annotation(x=y - 0.45, y=0.0, yref="paper", xanchor="left", yanchor="bottom", yshift=3,
                               showarrow=False, text=f"<b>{txt}</b>", font=dict(size=11, color=col))
    cd = np.c_[[_fmt(v) for v in G_t], [_fmt(v) for v in R_t + gov_usd]]
    fig.add_trace(go.Scatter(x=YEARS, y=[c * 100 for c in cut], mode="lines+markers", name="Aid Cut in Force",
                             line=dict(color=th.ROSE, width=3), marker=dict(size=9), customdata=cd,
                             hovertemplate="%{x}: %{y:.0f}% of the cut in force<br>aid lost %{customdata[0]}<br>"
                                           "government money %{customdata[1]}<extra></extra>"))
    if gradual:
        fig.add_trace(go.Scatter(x=YEARS, y=pts, mode="lines+markers", name="Extra Health Share", yaxis="y2",
                                 line=dict(color=th.BLUE, width=3), marker=dict(size=9), customdata=cd,
                                 hovertemplate="%{x}: +%{y:.1f} points of the budget<br>government money "
                                               "%{customdata[1]}<br>aid lost %{customdata[0]}<extra></extra>"))
    top2 = max(max(pts) * 1.25, 1.0)
    fig.update_layout(height=260, margin=dict(l=0, r=0, t=26, b=6), showlegend=False, hovermode="closest",
                      xaxis=dict(range=[2025.5, 2030.5], tickvals=YEARS, showticklabels=False, showgrid=False),
                      yaxis=dict(range=[0, 108], ticksuffix="%", ticklabelposition="inside", showgrid=True,
                                 tickvals=[20, 40, 60, 80, 100], ticktext=["20%", "40%", "60%", "80%", "100%"],
                                 gridcolor=th.RULE, tickfont=dict(color=th.ROSE, size=11)),
                      yaxis2=dict(overlaying="y", side="right", range=[0, top2], ticklabelposition="inside",
                                  showgrid=False, ticksuffix=" pts", tickformat=".1f", nticks=5,
                                  tickfont=dict(color=th.BLUE, size=11),
                                  visible=gradual))
    from model_section import chart
    chart(fig)


# --------------------------------------------------------------------------- #
# Outcomes
# --------------------------------------------------------------------------- #
PATH_PHRASE = {"Sudden (default)": "With a sudden cut", "Linear phase-out": "Phasing the cut in evenly over 5 years",
               "Front-loaded": "Front-loading the cut", "Back-loaded": "Back-loading the cut",
               "S-curve": "Phasing the cut in along an S-curve", "MOU schedule": "Following the MOU schedule",
               "Custom": "With this path"}


def outcome_panel(country_name, shape, response_phrase, res, base_committed, break_even, budget, num, rng,
                  round_words):
    """Benchmark line, four pills, one sentence and the caption."""
    share, p90 = budget["share_pct"], budget["p90_rise_pp"]
    if share == share:
        st.caption(f"{country_name} today: health is {share:.1f}% of government spending; fastest sustained rise in "
                   f"its history: {p90:.1f} points a year (90th percentile of its 2001-2023 yearly changes)."
                   if p90 == p90 else f"{country_name} today: health is {share:.1f}% of government spending.")
    T, C = res["totals"], res["committed"]
    avoided = base_committed - C["deaths"]
    be = ("Not reachable by 15%" if break_even is None else "None needed" if break_even <= 1e-9
          else f"+{break_even:.1f} points a year")
    st.markdown(th.pills_html([
        ("Extra Deaths 2026-2030", num(max(T["deaths_5y"], 0.0)) if T["deaths_5y"] > -0.5 else num(T["deaths_5y"]),
         "Central estimate; range = 95% interval",
         f"Range {rng(T['deaths_5y_lo'], T['deaths_5y_hi'])}"),
        ("Further Deaths Already Set in Motion After 2030", num(max(C["after_2030"], 0.0)),
         "People still off HIV treatment at the end of 2030, followed to the end of their own 5 years with no new cuts",
         ""),
        ("Deaths Avoided vs Sudden Cut With No Response", num(max(avoided, 0)) if avoided >= -0.5 else f"−{num(-avoided)}",
         "Committed basis: deaths in 2026-2030 plus those set in motion by then", f"of {num(base_committed)}"),
        ("Break-Even Budget Increase", be, "Smallest steady yearly rise in health's share of government spending that "
                                           "keeps pace with the lost aid every year (up to the 15% Abuja target)", ""),
    ], large=True), unsafe_allow_html=True)
    yrs = res["years"]
    keeps = [g <= 1e-6 for g in yrs["gap_usd"]]
    if all(keeps):
        pace = "keeps pace every year"
    elif not any(keeps):
        pace = "never fully keeps pace"
    else:
        first = next((YEARS[i] for i in range(5) if all(keeps[i:])), None)
        pace = f"keeps pace from {first}" if first else "keeps pace only in some years"
    lead = PATH_PHRASE.get(shape, "With this path") + (f" and {response_phrase}" if response_phrase else "")
    sent = (f"{lead}, {country_name} {pace} and "
            + (f"avoids about {round_words(avoided)} of the {round_words(base_committed)} deaths a sudden cut would "
               f"cause." if avoided > 0.5 else "avoids none of the deaths a sudden cut would cause."))
    if break_even is None:
        sent += " Keeping pace every year is not possible without passing the 15% Abuja target."
    elif break_even > 1e-9:
        sent += f" Keeping pace every year needs at least +{break_even:.1f} points a year."
    st.markdown(html.escape(sent).replace("$", "\\$"))
    st.caption("Assumes people return to care when funding returns and that new government money is spent as "
               "efficiently as donor money. Deaths avoided count deaths set in motion before 2030, so delaying a cut "
               "isn't counted as preventing it.")
