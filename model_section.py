"""
Section 4 of the dashboard: what a funding cut does (money -> fiscal response -> coverage -> lives).

Called from app.py:   render_model_section(iso3, country_name, imf_overrides, names)
All modelling lives in health_model.py and the scenario presets in scenarios.py; this file builds the sidebar
controls and draws the results. what_this_shows / how_to_read / stat are shared with app.py so every section
looks the same.
"""
from __future__ import annotations

import datetime as _dt
import html
import inspect
import io

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import health_model as hm
import scenarios as scn
from scenarios import PRESETS

_ver = tuple(int(x) for x in st.__version__.split(".")[:2] if x.isdigit())
WIDE = {"width": "stretch"} if _ver >= (1, 50) else {"use_container_width": True}
_METRIC_ARGS = set(inspect.signature(st.metric).parameters)

INK, MUTED, GRID = "#2b2b2b", "#6b6b6b", "rgba(0,0,0,0.08)"
LOG_TICKS = [0.01, 0.1, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000]
LOSS, BACKFILL = "#5d6d7e", "#1b6ca8"
SCEN_A, SCEN_B = "#5d6d7e", "#1b6ca8"
TITLE_FONT = dict(size=16)
FIRST_YEAR = 2026                    # year 1 after the cut
MAIN_LINE = {"HIV": "hiv_art", "TB": "tb_ds", "Malaria": "mal_itn", "Immunization": "imm"}
BUCKET_WORD = {"HIV": "HIV", "TB": "TB", "Malaria": "malaria", "Immunization": "immunization"}

GOV_MODES = {"No backfill": "none", "Historical behaviour (estimated)": "historical",
             "Replace a set share": "custom", "As much as fiscal space allows": "max"}
CEILINGS = {"Strong year (75th percentile growth)": "p75", "Best years (90th percentile growth)": "p90"}
ALLOCS = {"Pro-rata to what was cut": "pro_rata", "Lives first (triage)": "lives_first"}


# --------------------------------------------------------------------------- #
# Cached model calls
# --------------------------------------------------------------------------- #
@st.cache_resource(show_spinner=False)
def _inputs():
    return hm.load_inputs()


@st.cache_data(show_spinner=False)
def _default_params() -> pd.DataFrame:
    return hm.load_params()


@st.cache_data(show_spinner=False, max_entries=64)
def _run(iso3, sc_key, fiscal_t, ptab_json, n_draws=400):
    ptab = pd.read_json(io.StringIO(ptab_json), orient="split")
    return hm.run_country(iso3, scn.scenario_from_key(sc_key), hm.Fiscal(*fiscal_t), _inputs(), ptab, n_draws=n_draws)


@st.cache_data(show_spinner=False, max_entries=32)
def _dose(iso3, bucket, fiscal_t, ptab_json):
    ptab = pd.read_json(io.StringIO(ptab_json), orient="split")
    return hm.dose_response(iso3, bucket, hm.Fiscal(*fiscal_t), _inputs(), ptab, grid=np.linspace(0, 1, 11), n_draws=100)


@st.cache_data(show_spinner="Running the model for every country...", max_entries=16)
def _run_all(sc_key, fiscal_t, ptab_json):
    ptab = pd.read_json(io.StringIO(ptab_json), orient="split")
    return hm.run_all(scn.scenario_from_key(sc_key), hm.Fiscal(*fiscal_t), _inputs(), ptab,
                      n_draws=scn.ALL_COUNTRY_DRAWS)


@st.cache_data(show_spinner=False)
def _precomputed(path: str, _mtime: float) -> pd.DataFrame:
    return pd.read_csv(path)


# --------------------------------------------------------------------------- #
# Formatting and shared page elements
# --------------------------------------------------------------------------- #
def money(x: float) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "n/a"
    a, s = abs(x), "-" if x < 0 else ""
    if a >= 1e9:
        return f"{s}${a / 1e9:,.2f}B"
    if a >= 1e6:
        return f"{s}${a / 1e6:,.1f}M"
    if a >= 1e3:
        return f"{s}${a / 1e3:,.0f}K"
    return f"{s}${a:,.0f}"


def num(x: float) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "n/a"
    a = abs(x)
    if a >= 1e6:
        return f"{x / 1e6:,.2f}M"
    if a >= 1e4:
        return f"{x / 1e3:,.0f}K"
    if a >= 1e3:
        return f"{x / 1e3:,.1f}K"
    return f"{x:,.0f}"


def rng(lo, hi) -> str:
    return f"{num(lo)} to {num(hi)}"


def _esc(text: str) -> str:
    """Stop '$' from being read as LaTeX by st.markdown."""
    return text.replace("$", "\\$")


def what_this_shows(text: str):
    """One plain-English line under a section header (same style in every section)."""
    st.markdown(_esc(f"**What this shows:** {text}"))


def how_to_read(text: str, label: str = "How to read this"):
    with st.expander(label):
        st.markdown(_esc(text))


def stat(col, label, value, sub=None, help=None):
    """A bordered metric; `sub` (a range or context) sits under the value in small grey text, without an arrow."""
    kw = {"help": help}
    if "border" in _METRIC_ARGS:
        kw["border"] = True
    if sub and "delta_arrow" in _METRIC_ARGS:
        col.metric(label, value, delta=sub, delta_color="off", delta_arrow="off", **kw)
    else:
        col.metric(label, value, **kw)
        if sub:
            col.caption(_esc(sub))


def _stat_grid(items, ncols):
    for i, it in enumerate(items):
        if i % ncols == 0:
            cols = st.columns(ncols)
        stat(cols[i % ncols], *it)


def _layout(fig, h=380, **kw):
    margin = kw.pop("margin", dict(l=10, r=10, t=50, b=10))
    fig.update_layout(height=h, margin=margin, plot_bgcolor="white", paper_bgcolor="white",
                      font=dict(color=INK, size=13), hoverlabel=dict(bgcolor="white", font_size=13), **kw)
    fig.update_xaxes(gridcolor=GRID, zeroline=False, linecolor="rgba(0,0,0,0.25)", automargin=True)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor="rgba(0,0,0,0.25)", automargin=True)
    return fig


def _title(text):
    return dict(text=text, font=TITLE_FONT, x=0, xanchor="left")


def _resp_label(fiscal_t) -> str:
    mode, theta, _, alloc, ceiling = fiscal_t
    lbl = {"none": "No backfill", "historical": "Historical behaviour", "custom": f"Government replaces {theta:.0%}",
           "max": "As much as fiscal space allows"}[mode]
    if mode != "none":
        lbl += (", lives first" if alloc == "lives_first" else ", pro-rata")
        lbl += (", best-years ceiling" if ceiling == "p90" else "")
    return lbl


# --------------------------------------------------------------------------- #
# Sidebar controls
# --------------------------------------------------------------------------- #
def _preset_options(preset, ci, iso3, country_name, key):
    opts = scn.default_opts(preset, ci)
    if preset == "America First MOUs":
        opts["mou_year"] = st.select_slider("MOU year", options=[2026, 2027, 2028, 2029, 2030],
                                            value=scn.DEFAULT_MOU_YEAR, key=f"{key}_mouy")
        avg = scn.mou_average_cut_pct(ci, opts["mou_year"])
        opts["non_mou_cut"] = st.slider("US cut where there is no MOU schedule (%)", 0, 100, avg, 1,
                                        key=f"{key}_nonmou_{opts['mou_year']}",
                                        help=f"Default = average cut across the MOU countries in {opts['mou_year']} "
                                             f"({avg}%).") / 100
        mc = scn.mou_cuts(ci, opts["mou_year"])
        if iso3 in mc:
            st.caption(_esc(f"{country_name}: the MOU schedule implies a {mc[iso3]:.0%} cut in US bilateral aid in "
                            f"{opts['mou_year']} (US${ci.loc[iso3, 'mou_us_ref'] / 1e6:,.0f}M a year before the cut)."))
        else:
            st.caption(f"{country_name} has no MOU schedule, so the default above applies.")
    if preset == "Custom":
        with st.expander("Cuts by Donor and Channel", expanded=True):
            ed = pd.DataFrame({"Donor": hm.SOURCE_GROUPS,
                               "Bilateral & NGO cut %": [opts["custom_direct"][s] for s in hm.SOURCE_GROUPS],
                               "Via multilaterals cut %": [opts["custom_multi"][s] for s in hm.SOURCE_GROUPS]})
            ed = st.data_editor(ed, hide_index=True, key=f"{key}_custom_tbl", disabled=["Donor"],
                                column_config={c: st.column_config.NumberColumn(min_value=-50, max_value=100, step=5)
                                               for c in ("Bilateral & NGO cut %", "Via multilaterals cut %")})
            opts["custom_direct"] = dict(zip(ed["Donor"], ed["Bilateral & NGO cut %"]))
            opts["custom_multi"] = dict(zip(ed["Donor"], ed["Via multilaterals cut %"]))
            opts["custom_chan"] = {ch: st.slider(f"{ch} channel cut (%)", 0, 100, 0, 5, key=f"{key}_ch_{ch}",
                                                 help="Hits every donor's money through this channel "
                                                      "(e.g. a replenishment shortfall).")
                                   for ch in ["Global Fund", "Gavi", "WHO", "UNICEF"]}
    return opts


def _controls(iso3, country_name, I) -> dict:
    ci = I["ci"]
    with st.sidebar:
        st.divider()
        st.header("Funding-Cut Model")
        preset = st.selectbox("Donor Scenario", list(PRESETS), index=0, key="m_preset")
        st.caption(_esc(PRESETS[preset]))
        opts = _preset_options(preset, ci, iso3, country_name, "m")

        th_c, th_lo, th_hi = hm.theta_historical(I["reg"])
        mode = GOV_MODES[st.radio("Government Response", list(GOV_MODES), index=0, key="m_mode",
                                  help="How much of the lost aid the government replaces from its own budget.")]
        theta = 0.0
        if mode == "custom":
            theta = st.slider("Share of lost aid replaced (%)", 0, 100, 25, 5, key="m_theta") / 100
        if mode == "historical":
            st.caption(_esc(f"Across 97 countries (2001-2023), a $1 fall in aid per person changed government health "
                            f"spending per person by {th_c:+.2f} (95% range {th_lo:+.2f} to {th_hi:+.2f}): no evidence "
                            f"of backfilling, so this option replaces {max(th_c, 0):.0%}."))
        cap = st.checkbox("Cap replacement at fiscal space", value=True, key="m_cap", disabled=(mode in ("none", "max")))
        ceiling = CEILINGS[st.radio("Fiscal-Space Ceiling", list(CEILINGS), key="m_effort", disabled=(mode == "none"),
                                    help="How hard can the health budget be pushed? Capacity = government health "
                                         "spending x (that growth rate minus the country's typical growth) x a "
                                         "debt-stress factor, every year.")]
        alloc = ALLOCS[st.radio("Where Replacement Money Goes", list(ALLOCS), key="m_alloc", disabled=(mode == "none"),
                                help="Lives first refills the services that avert the most deaths per dollar first "
                                     "(usually TB treatment, vaccines, ART) before anything else.")]

        with st.expander("Model Parameters (Editable)"):
            st.caption("Each parameter is drawn from a triangular distribution (low, central, high). "
                       "Edit any cell to see how sensitive the answer is.")
            ptab = st.data_editor(_default_params().reset_index(), hide_index=True, key="m_params",
                                  disabled=["param", "label", "unit", "source"], column_config={"param": None}, **WIDE)
            ptab = ptab.set_index("param")

        st.divider()
        cmp = None
        if st.toggle("Compare with a second scenario", value=False, key="m_compare"):
            st.subheader("Scenario B")
            options_b = ["Same as Scenario A"] + scn.PRECOMPUTED_PRESETS
            pb = st.selectbox("Donor Scenario (B)", options_b, index=0, key="mb_preset")
            if pb == "Same as Scenario A":
                preset_b, opts_b = preset, opts
            else:
                preset_b = pb
                opts_b = _preset_options(preset_b, ci, iso3, country_name, "mb")
            mode_b = GOV_MODES[st.radio("Government Response (B)", list(GOV_MODES),
                                        index=list(GOV_MODES).index("As much as fiscal space allows"), key="mb_mode")]
            theta_b = st.slider("Share of lost aid replaced (B, %)", 0, 100, 25, 5, key="mb_theta") / 100 \
                if mode_b == "custom" else 0.0
            alloc_b = ALLOCS[st.radio("Where Replacement Money Goes (B)", list(ALLOCS),
                                      index=list(ALLOCS).index("Lives first (triage)"), key="mb_alloc",
                                      disabled=(mode_b == "none"))]
            st.caption("Scenario B uses Scenario A's fiscal-space ceiling and model parameters.")
            cmp = {"preset": preset_b, "opts": opts_b, "fiscal_t": (mode_b, theta_b, True, alloc_b, ceiling)}

    return {"preset": preset, "opts": opts, "fiscal_t": (mode, theta, cap, alloc, ceiling), "mode": mode,
            "ptab": ptab, "ptab_json": ptab.to_json(orient="split"), "cmp": cmp}


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
INTRO = (
    "A four-step model for HIV, TB, malaria and immunization.\n\n"
    "1. **Money:** the donor scenario removes aid cell by cell (who pays x which channel x which program).\n"
    "2. **Fiscal response:** the government can replace part of it, limited by its fiscal space.\n"
    "3. **Coverage:** money not replaced ÷ cost per person = people who lose a service.\n"
    "4. **Lives:** people losing a service x that service's effect on mortality in this country.\n\n"
    "Ranges are 95% intervals from 400 Monte Carlo draws over every uncertain parameter. All settings are in the "
    "sidebar.")


def render_model_section(iso3: str, country_name: str, imf: dict | None = None, names: dict | None = None):
    names = names or {}
    I = _inputs()
    ci = I["ci"]
    ctl = _controls(iso3, country_name, I)
    preset, fiscal_t, ptab, ptab_json = ctl["preset"], ctl["fiscal_t"], ctl["ptab"], ctl["ptab_json"]
    sk = scn.scenario_key(scn.build_scenario(preset, ctl["opts"], ci))

    st.header(f"4. What a Funding Cut Does in {country_name}: Money → Coverage → Lives")
    what_this_shows("How much HIV, TB, malaria and vaccine aid would be lost under the scenario chosen in the sidebar, "
                    "how many people would lose services, and how many more people would die.")
    how_to_read(INTRO)

    res = None
    if iso3 not in ci.index or iso3 not in set(I["lines"].iso3):
        st.info(f"{country_name} has no recorded HIV, TB, malaria or vaccine aid in 2021-2023, so there is nothing to "
                "model for this country. The all-country results are below.")
    else:
        res = _country_results(iso3, country_name, ctl, sk, imf or {})

    A = _cross_country(sk, ctl, iso3, names)

    with st.expander("Methods, Data and Limitations"):
        st.markdown(_esc(METHODS))
        st.markdown("**Cross-check: what 20 years of data say.** " + _esc(_crosscheck_summary(res, I, ptab, country_name)))
        _published_estimates(A, I, ptab)


def _country_results(iso3, country_name, ctl, sk, imf):
    preset, fiscal_t, ptab, ptab_json, mode = ctl["preset"], ctl["fiscal_t"], ctl["ptab"], ctl["ptab_json"], ctl["mode"]
    res = _run(iso3, sk, fiscal_t, ptab_json)
    res0 = _run(iso3, sk, scn.DEFAULT_FISCAL, ptab_json) if mode != "none" else res
    T, B, L = res["totals"], res["buckets"].set_index("bucket"), res["lines"]

    if T.get("gains", 0) > 1e5:
        st.info(_esc(f"Some aid increases in this scenario (+{money(T['gains'])} a year); those gains count as coverage "
                     "and lives gained and partly offset the losses below."))
    if T["gross"] <= 0 and T["base"] > 0:
        st.success(_esc(f"Under '{preset}' {country_name} loses no HIV, TB, malaria or vaccine aid "
                        f"(net change {money(-T['gross'])})."))

    show = L[(L["base_usd"] > 0) | (L["net_loss_usd"] != 0)].copy()
    cov_fig = _coverage_fig(show)
    path_fig = _path_fig(res)
    cards = _per_million_cards(res, ptab)
    items = _headline_items(res)

    # ------------------------------ headline ------------------------------ #
    if ctl["cmp"]:
        _comparison(iso3, country_name, ctl, res, items)
    else:
        st.subheader("The Headline")
        st.caption(_esc(f"{preset} · {_resp_label(fiscal_t)}"))
        _stat_grid(items, 3)
    if mode != "none" and T["replaced"] > 0:
        saved = res0["totals"]["deaths_5y"] - T["deaths_5y"]
        st.markdown(_esc(f"Government backfill of {money(T['replaced'])} a year averts about **{num(saved)} deaths over "
                         f"5 years** compared with no backfill ({money(T['replaced'] * 5 / max(saved, 1))} per death "
                         "averted)."))
    st.download_button(
        "Download Country Brief", icon=":material/download:",
        data=_brief_html(country_name, preset, _resp_label(fiscal_t), items, cards, [cov_fig, path_fig]).encode("utf-8"),
        file_name=f"{country_name.replace(' ', '_')}_funding_cut_brief.html", mime="text/html", key="m_brief",
        help="A one-page HTML summary of this scenario. Open it in a browser and print to PDF.")

    # ------------------------------ per $1M ------------------------------ #
    st.subheader(_esc("Every US$1 Million Lost, by Bucket"))
    cols = st.columns(4)
    for col, c in zip(cols, cards):
        col.markdown(_card_html(c), unsafe_allow_html=True)
    how_to_read(f"What one million dollars of aid that is cut every year for five years, and not replaced, does in "
                f"{country_name}, given its costs, current coverage and disease burden. Each card uses the main service "
                "in its bucket (malaria: bednets). The coverage drop per $1M is linear, and so are deaths, except for "
                "malaria, where the Lives Saved Tool equations make each extra point of lost coverage slightly worse.")

    # ------------------------------ where the money is lost ------------------------------ #
    st.subheader("Where the Money Is Lost")
    cells = res["cells"]
    cl = cells[cells["loss"] > 0]
    if cl.empty:
        st.info("No aid is cut in this scenario.")
    else:
        a, b = st.columns(2)
        with a:
            st.plotly_chart(_loss_by_bucket_fig(B), **WIDE)
        with b:
            st.plotly_chart(_who_cut_fig(cl), **WIDE)
        how_to_read("Left: each disease's lost aid, split into the part the government replaces and the part lost to "
                    "services. Right: who originally paid for the money that is cut; hover to see the channels it went "
                    "through (a US cut to the Global Fund counts as United States, via Global Fund).")

    # ------------------------------ chain table ------------------------------ #
    st.subheader("The Chain, Service by Service")
    st.table(_chain_table(show).set_index("Service"))
    notes = []
    if show["capped"].any():
        notes.append("Where the aid lost would pay for more people than are covered today, the loss is capped at "
                     "current coverage.")
    notes += [f"{f[0].upper() + f[1:]}." for f in res["flags"]]
    notes.append("HIV prevention turns money into infections averted (no deaths within 5 years); support for orphans and "
                 "vulnerable children has no modelled effect on deaths. Program money with no reported purpose is "
                 "spread over each bucket's known mix, and "
                 f"{float(ptab.loc['hss_kappa', 'central']):.0%} of lost systems money (labs, staff, monitoring) is "
                 "assumed to cut services. Deaths ranges are 95% intervals.")
    how_to_read(" ".join(notes))
    if cov_fig is not None:
        st.plotly_chart(cov_fig, **WIDE)

    # ------------------------------ dose response + path ------------------------------ #
    st.subheader("How the Damage Scales")
    d1, d2 = st.columns(2)
    with d1:
        bsel = st.radio("Bucket", hm.BUCKETS, horizontal=True, key="m_dose_b")
        dr = _dose(iso3, bsel, fiscal_t, ptab_json)
        base_b = B.loc[bsel, "base_usd"]
        cur_cut = B.loc[bsel, "gross_loss_usd"] / base_b if base_b > 0 else 0
        if base_b > 0:
            per10 = float(dr["deaths_5y"].iloc[-1]) / 10
            st.markdown(f"In {country_name}, every 10% of {BUCKET_WORD[bsel]} aid cut adds about **{num(per10)}** "
                        "extra deaths over 5 years.")
        else:
            st.markdown(f"{country_name} receives no {BUCKET_WORD[bsel]} aid in the model, so cutting it changes nothing.")
        st.plotly_chart(_dose_fig(dr, bsel, cur_cut, B.loc[bsel]), **WIDE)
    with d2:
        band = res["path_band"]
        st.markdown(_esc(f"Over {FIRST_YEAR}-{FIRST_YEAR + 4} this scenario adds about **{num(T['deaths_5y'])}** "
                         f"extra deaths in {country_name} (range {rng(band['lo'].iloc[-1], band['hi'].iloc[-1])})."))
        # keep the two charts level with each other (the left column has a bucket picker above its chart)
        st.markdown("<div style='height:2.6rem'></div>", unsafe_allow_html=True)
        st.plotly_chart(path_fig, **WIDE)
    how_to_read("Left: a uniform cut across all donors to one bucket, with the government response chosen in the "
                "sidebar; the 10% figure is the average along the curve. The curve flattens once everyone whose "
                "service donors pay for has lost it, and bends where government backfill runs out of fiscal space. "
                "Right: deaths after losing HIV treatment rise from about 1% to 5% a year as immunity declines, "
                "unvaccinated birth cohorts add up, and nets already hanging keep protecting for about a year.")

    # ------------------------------ fiscal space ------------------------------ #
    _fiscal_panel(res, country_name, imf)
    return res


# --------------------------------------------------------------------------- #
# Headline, comparison, cards
# --------------------------------------------------------------------------- #
def _headline_items(res) -> list:
    T, B = res["totals"], res["buckets"].set_index("bucket")
    return [
        ("Aid at Risk (per Year)", money(T["gross"]),
         f"{T['gross'] / T['base']:.0%} of {money(T['base'])}" if T["base"] else None,
         "Yearly HIV, TB, malaria and vaccine aid removed by the scenario, out of the 2021-2023 average."),
        ("Replaced by Government", money(T["replaced"]),
         f"{T['replaced'] / T['gross']:.0%} of the loss" if T["gross"] > 0 else None,
         "Set by the government response in the sidebar, limited by fiscal space."),
        ("Net Loss to Services", money(T["net"]), "per year", "Aid lost minus what the government replaces."),
        ("Extra Deaths, Year 1", num(T["deaths_y1"]),
         "range " + rng(res["buckets"]["deaths_y1_lo"].sum(), res["buckets"]["deaths_y1_hi"].sum()),
         "Year 1 is lower than later years because deaths after losing treatment, bednets or vaccines build up over "
         "time. Range = 95% interval."),
        ("Extra Deaths Over 5 Years", num(T["deaths_5y"]), "range " + rng(T["deaths_5y_lo"], T["deaths_5y_hi"]),
         "Assumes the cut is sustained for five years. Range = 95% interval."),
        ("New HIV Infections, 5 Years", num(B.loc["HIV", "infections_5y"]),
         "range " + rng(B.loc["HIV", "infections_5y_lo"], B.loc["HIV", "infections_5y_hi"]),
         "Lives-first triage refills treatment and vaccines first and HIV prevention last, so new infections can stay "
         "high even when deaths fall. Range = 95% interval."),
    ]


def _comparison(iso3, country_name, ctl, res_a, items_a):
    c = ctl["cmp"]
    ci = _inputs()["ci"]
    sk_b = scn.scenario_key(scn.build_scenario(c["preset"], c["opts"], ci))
    res_b = _run(iso3, sk_b, c["fiscal_t"], ctl["ptab_json"])
    st.subheader("Scenario A vs Scenario B")
    a, b = st.columns(2, gap="large")
    for col, tag, preset, fiscal_t, items in ((a, "A", ctl["preset"], ctl["fiscal_t"], items_a),
                                              (b, "B", c["preset"], c["fiscal_t"], _headline_items(res_b))):
        with col:
            st.markdown(_esc(f"**Scenario {tag}:** {preset} · {_resp_label(fiscal_t)}"))
            _stat_grid(items, 2)
    da, db = res_a["totals"]["deaths_5y"], res_b["totals"]["deaths_5y"]
    diff = da - db
    st.markdown(f"Scenario B {'averts' if diff >= 0 else 'adds'} about **{num(abs(diff))}** extra deaths over 5 years "
                f"in {country_name} compared with Scenario A.")
    BA, BB = res_a["buckets"].set_index("bucket"), res_b["buckets"].set_index("bucket")
    fig = go.Figure()
    for tag, Bx, col in (("Scenario A", BA, SCEN_A), ("Scenario B", BB, SCEN_B)):
        fig.add_trace(go.Bar(x=hm.BUCKETS, y=[Bx.loc[k, "deaths_5y"] for k in hm.BUCKETS], name=tag,
                             marker=dict(color=col, line=dict(color="white", width=1.5)),
                             text=[num(Bx.loc[k, "deaths_5y"]) for k in hm.BUCKETS], textposition="outside",
                             cliponaxis=False, hovertemplate=f"{tag}<br>%{{x}}: %{{y:,.0f}} extra deaths<extra></extra>"))
    fig.update_layout(barmode="group", bargap=0.3)
    _layout(fig, h=340, title=_title("Extra Deaths Over 5 Years by Disease: Scenario A vs B"),
            legend=dict(orientation="h", y=1.02, x=1, xanchor="right", yanchor="bottom"),
            yaxis=dict(title="extra deaths, 5 years", rangemode="tozero"))
    st.plotly_chart(fig, **WIDE)


def _per_million_cards(res, ptab) -> list:
    Ls = res["lines"].set_index("line")
    cont = float(ptab.loc["continuity", "central"])
    out = []
    for b in hm.BUCKETS:
        line = MAIN_LINE[b]
        ln = Ls.loc[line]
        uc, need = ln["unit_cost"], ln["need"]
        per_m_units = 1e6 / uc * (1 - cont)
        dpp = per_m_units / need * 100 if need and not np.isnan(need) else np.nan
        d_per = res["deaths_per_dollar"][line] * 1e6 * (1 - cont)
        out.append({"bucket": b, "color": hm.BUCKET_COLORS[b], "service": hm.LINE_LABELS[line],
                    "people": f"{num(per_m_units)} {ln['unit_label']} lose the service",
                    "coverage": "n/a" if np.isnan(dpp) else f"{dpp:,.2f} percentage points",
                    "deaths": f"{d_per:,.0f}",
                    "foot": f"Cost {money(uc)} per {hm.UNIT_SINGULAR[line]} · "
                            f"{money(5e6 / d_per) if d_per > 0 else 'n/a'} of aid per death"})
    return out


def _card_html(c) -> str:
    return (f"<div style='border:1px solid rgba(128,128,128,0.25);border-top:4px solid {c['color']};border-radius:8px;"
            f"padding:12px 14px;height:100%'>"
            f"<div style='font-weight:700;font-size:1.05rem'>{c['bucket']}</div>"
            f"<div style='font-size:0.85rem;opacity:0.7;margin-bottom:8px'>{html.escape(c['service'])}</div>"
            f"<div style='font-size:0.95rem;line-height:1.6'>{html.escape(c['people'])}<br>"
            f"<b>{c['coverage']}</b> coverage drop<br><b>{c['deaths']}</b> extra deaths over 5 years</div>"
            f"<div style='font-size:0.85rem;opacity:0.7;margin-top:8px'>{html.escape(c['foot'])}</div>"
            f"</div>").replace("$", "&#36;")


# --------------------------------------------------------------------------- #
# Charts and tables
# --------------------------------------------------------------------------- #
def _loss_by_bucket_fig(B: pd.DataFrame):
    bk = [b for b in hm.BUCKETS if B.loc[b, "gross_loss_usd"] > 0][::-1]
    rep = [max(B.loc[b, "replaced_usd"], 0.0) for b in bk]
    lost = [max(B.loc[b, "gross_loss_usd"] - B.loc[b, "replaced_usd"], 0.0) for b in bk]
    fig = go.Figure()
    for name, vals, col in (("Replaced by government", rep, BACKFILL), ("Lost to services", lost, LOSS)):
        fig.add_trace(go.Bar(y=bk, x=vals, name=name, orientation="h",
                             marker=dict(color=col, line=dict(color="white", width=1.5)),
                             customdata=[money(v) for v in vals],
                             hovertemplate=f"%{{y}} · {name}: %{{customdata}} a year<extra></extra>"))
    tot = [r + l for r, l in zip(rep, lost)]
    fig.add_trace(go.Scatter(y=bk, x=tot, mode="text", text=[money(t) for t in tot], textposition="middle right",
                             textfont=dict(color=INK), showlegend=False, hoverinfo="skip"))
    fig.update_layout(barmode="stack", bargap=0.35)
    _layout(fig, h=360, title=_title("Aid Lost per Year, by Disease"),
            legend=dict(orientation="h", y=-0.12, x=0), margin=dict(l=10, r=70, t=50, b=10),
            xaxis=dict(showticklabels=False, range=[0, max(tot) * 1.25]))
    return fig


def _who_cut_fig(cl: pd.DataFrame):
    by_src = cl.groupby("src_grp")["loss"].sum().sort_values()
    by_ch = cl.groupby(["src_grp", "chan_grp"])["loss"].sum()
    hover = []
    for s in by_src.index:
        ch = by_ch.loc[s].sort_values(ascending=False)
        hover.append("<br>".join(f"via {c}: {money(v)}" for c, v in ch.items()))
    fig = go.Figure(go.Bar(y=by_src.index, x=by_src.values, orientation="h",
                           marker=dict(color="#5d6d7e", line=dict(color="white", width=1.5)),
                           text=[money(v) for v in by_src.values], textposition="outside", cliponaxis=False,
                           textfont=dict(color=INK), customdata=hover,
                           hovertemplate="<b>%{y}</b>: %{text} a year<br>%{customdata}<extra></extra>"))
    fig.update_layout(bargap=float(np.clip(1 - 34 * len(by_src) / 280, 0.25, 0.85)))
    _layout(fig, h=max(360, 80 + 34 * len(by_src)), title=_title("Who Cut the Money"),
            margin=dict(l=10, r=70, t=50, b=10), xaxis=dict(showticklabels=False, range=[0, by_src.max() * 1.25]))
    return fig


def _chain_table(show: pd.DataFrame) -> pd.DataFrame:
    def cov_change(r):
        if pd.isna(r.need) or pd.isna(r.cov0):
            return "n/a"
        after = max(r.cov0 - r.cov_drop_pp / 100, 0)
        d = (after - r.cov0) * 100
        return f"{r.cov0:.0%} → {after:.0%} ({d:+.0f} pts)" if abs(d) >= 1 else f"{r.cov0:.0%} → {after:.0%} ({d:+.1f} pts)"

    return pd.DataFrame({
        "Service": show["label"].values,
        "Aid Today (per yr)": show["base_usd"].map(money).values,
        "Aid Lost After Backfill": show["net_loss_usd"].map(money).values,
        "Cost per Person": [f"{money(r.unit_cost)} per {hm.UNIT_SINGULAR[r.line]}" for r in show.itertuples()],
        "People Losing Service": show["units_lost"].map(num).values,
        "Coverage Change": [cov_change(r) for r in show.itertuples()],
        "Deaths, Year 1": show["deaths_y1"].map(num).values,
        "Deaths, 5 Years (range)": [f"{num(r.deaths_5y)} ({rng(r.deaths_5y_lo, r.deaths_5y_hi)})"
                                    for r in show.itertuples()],
    })


def _coverage_fig(show: pd.DataFrame):
    d = show[show["need"].notna() & show["cov0"].notna() & (show["line"] != "mal_irs")].copy()
    if d.empty:
        return None
    d["after"] = (d["cov0"] - d["cov_drop_pp"] / 100).clip(0, 1)
    d = d.iloc[::-1]
    fig = go.Figure()
    for r in d.itertuples():
        col = hm.BUCKET_COLORS[r.bucket]
        fig.add_trace(go.Scatter(x=[r.after * 100, r.cov0 * 100], y=[r.label, r.label], mode="lines",
                                 line=dict(color=col, width=2), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=d["cov0"] * 100, y=d["label"], mode="markers", name="Coverage now",
                             marker=dict(size=11, color="white", line=dict(color=[hm.BUCKET_COLORS[b] for b in d["bucket"]], width=2)),
                             hovertemplate="%{y}<br>now: %{x:.0f}%<extra></extra>"))
    fig.add_trace(go.Scatter(x=d["after"] * 100, y=d["label"], mode="markers+text", name="After the cut",
                             marker=dict(size=11, color=[hm.BUCKET_COLORS[b] for b in d["bucket"]], line=dict(color="white", width=2)),
                             text=[f"-{v:.1f} pts" if v >= 0.05 else "" for v in d["cov_drop_pp"]],
                             # labels left of the dot, except near 0% where they would run off the chart (then above it)
                             textposition=["middle left" if a >= 0.15 else "top center" for a in d["after"]],
                             textfont=dict(color=MUTED, size=12),
                             hovertemplate="%{y}<br>after: %{x:.0f}%<extra></extra>"))
    _layout(fig, h=90 + 42 * len(d), title=_title("Coverage Before and After the Cut (% of People in Need)"),
            legend=dict(orientation="h", y=-0.15, x=0), xaxis=dict(range=[-8, 102], ticksuffix="%"))
    return fig


def _dose_fig(dr: pd.DataFrame, bucket: str, cur_cut: float, bb: pd.Series):
    col = hm.BUCKET_COLORS[bucket]
    h = col.lstrip("#")
    fill = f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},0.15)"
    x = dr["cut"] * 100
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(x) + list(x[::-1]), y=list(dr["hi"]) + list(dr["lo"][::-1]), fill="toself",
                             fillcolor=fill, line=dict(width=0), hoverinfo="skip", name="95% range"))
    fig.add_trace(go.Scatter(x=x, y=dr["deaths_5y"], mode="lines", line=dict(color=col, width=2), name="Extra deaths, 5 yrs",
                             customdata=np.c_[dr["net_loss_usd"].map(money), dr["cov_drop_pp"].fillna(0)],
                             hovertemplate="%{x:.0f}% of aid cut (%{customdata[0]} a year)<br>coverage "
                                           "-%{customdata[1]:.1f} percentage points<br>%{y:,.0f} extra deaths over "
                                           "5 years<extra></extra>"))
    if cur_cut > 0:
        fig.add_trace(go.Scatter(x=[cur_cut * 100], y=[bb["deaths_5y"]], mode="markers", name="This scenario",
                                 marker=dict(size=13, color=col, line=dict(color="white", width=2)),
                                 hovertemplate="this scenario: %{x:.0f}% cut, %{y:,.0f} deaths<extra></extra>"))
        fig.add_annotation(x=cur_cut * 100, y=bb["deaths_5y"], text=f"This scenario: {cur_cut:.0%} cut,<br>"
                                                                    f"{num(bb['deaths_5y'])} deaths",
                           showarrow=True, arrowhead=0, arrowcolor=MUTED, ax=-60 if cur_cut > 0.5 else 60, ay=-40,
                           font=dict(color=INK, size=12), bgcolor="rgba(255,255,255,0.85)", align="left")
    _layout(fig, h=400, title=_title("Extra Deaths as More Aid Is Cut"), showlegend=False,
            xaxis=dict(title="Share of this bucket's aid cut", ticksuffix="%"),
            yaxis=dict(title="extra deaths over 5 years", rangemode="tozero"))
    return fig


def _path_fig(res: dict):
    p = res["path"]
    years = [str(FIRST_YEAR + i - 1) for i in p.index]
    fig = go.Figure()
    for b in hm.BUCKETS:
        fig.add_trace(go.Bar(x=years, y=p[b], name=b, marker=dict(color=hm.BUCKET_COLORS[b],
                             line=dict(color="white", width=2)),
                             hovertemplate=f"{b}<br>%{{x}}: %{{y:,.0f}} extra deaths<extra></extra>"))
    fig.update_layout(barmode="stack", bargap=0.35)
    _layout(fig, h=400, title=_title(f"Extra Deaths Each Year, {FIRST_YEAR}-{FIRST_YEAR + 4}"),
            legend=dict(orientation="h", y=-0.12, x=0), yaxis=dict(title="extra deaths in that year"),
            xaxis=dict(type="category"))
    return fig


def _fiscal_panel(res: dict, country_name: str, imf: dict):
    F = res["fiscal"]
    st.subheader(f"Can {country_name} Fill the Gap? Fiscal Space")
    rev = F["revenue"]
    if (pd.isna(rev) or not rev) and imf.get("revenue_pct_gdp") and F["gdp"]:
        rev = imf["revenue_pct_gdp"] / 100 * F["gdp"]
    debt = F["debt_pct_gdp"] if not pd.isna(F["debt_pct_gdp"]) else imf.get("debt_pct_gdp", np.nan)
    G = F["gross_loss"]
    _stat_grid([
        ("Government Health Spending, 2023", money(F["ghes"]),
         f"${F['ghes_pc']:,.0f} per person · {F['ghes_pct_gdp']:.1f}% of GDP" if not pd.isna(F["ghes_pc"]) else None, None),
        ("Aid Loss as % of Government Health Spending", f"{G / F['ghes']:.0%}" if F["ghes"] else "n/a", None, None),
        ("Aid Loss as % of Government Revenue", f"{G / rev:.1%}" if rev and not pd.isna(rev) else "n/a", None, None),
        ("Interest as % of Revenue", f"{F['interest_pct_revenue']:.0f}%" if not pd.isna(F["interest_pct_revenue"]) else "n/a",
         f"gross debt {debt:.0f}% of GDP" if not pd.isna(debt) else None, None),
        ("Health Share of Government Spending",
         f"{F['ghes_pct_gov_spend']:.1f}%" if not pd.isna(F["ghes_pct_gov_spend"]) else "n/a", "Abuja target: 15%", None),
    ], 3)
    typical = F["ghes"] * max(F["ghes_growth_median"], 0)
    bars = [("Aid lost (gross, per year)", G, "#4d4d4d"),
            ("Backfill capacity (fiscal space)", F["capacity"], BACKFILL),
            ("Backfill applied in this run", F["replacement"], "#5dade2"),
            ("One year of typical growth in<br>government health spending", typical, "#aab2bd")]
    fig = go.Figure(go.Bar(y=[b[0] for b in bars][::-1], x=[b[1] for b in bars][::-1], orientation="h",
                           marker=dict(color=[b[2] for b in bars][::-1], line=dict(color="white", width=2)),
                           text=[money(b[1]) for b in bars][::-1], textposition="outside", cliponaxis=False,
                           textfont=dict(color=INK), hovertemplate="%{y}: %{text}<extra></extra>"))
    _layout(fig, h=280, title=_title("The Gap vs. What the Budget Can Absorb (US$ per Year)"),
            xaxis=dict(showticklabels=False), margin=dict(l=10, r=80, t=50, b=10))
    a, b = st.columns([1.3, 1])
    with a:
        st.plotly_chart(fig, **WIDE)
    with b:
        yrs = G / typical if typical > 0 else np.inf
        st.markdown(_esc(
            f"- **Backfill capacity** = government health spending x ({'best-year' if F['effort'] == 'p90' else 'strong-year'} "
            f"growth {F['ghes_growth_top']:.0%} minus typical growth {max(F['ghes_growth_median'], 0):.0%}) x debt-stress "
            f"factor {F['stress_factor']:.2f} = **{money(F['capacity'])} a year**.\n"
            f"- Filling the whole gap would take **{'more than 10' if yrs > 10 else f'{yrs:,.1f}'} years** of the "
            f"country's typical growth in government health spending, all of it diverted to these four programs.\n"
            f"- The debt-stress factor shrinks capacity when interest eats more than 10% of revenue "
            f"(to a floor of 0.25 at 40% or more)."))
    how_to_read("Growth rates are real (constant 2023 US$) from IHME, 2001-2023. Interest, revenue and debt are World "
                "Bank WDI, latest year (IMF data from this dashboard fill gaps where available).")


# --------------------------------------------------------------------------- #
# Across all countries
# --------------------------------------------------------------------------- #
def _all_country_results(sk, ctl) -> pd.DataFrame:
    """Precomputed file when the settings are the defaults it was built with; otherwise run live."""
    preset, ptab = ctl["preset"], ctl["ptab"]
    path = scn.precomputed_path(hm.MODEL_DIR, preset)
    if preset in scn.PRECOMPUTED_PRESETS and path.exists() and ctl["fiscal_t"] == scn.DEFAULT_FISCAL:
        ci = _inputs()["ci"]
        default_sk = scn.scenario_key(scn.build_scenario(preset, scn.default_opts(preset, ci), ci))
        p0 = _default_params()
        same_params = ptab[["central", "low", "high"]].astype(float).reindex(p0.index).equals(
            p0[["central", "low", "high"]].astype(float))
        if sk == default_sk and same_params:
            return _precomputed(str(path), path.stat().st_mtime)
    return _run_all(sk, ctl["fiscal_t"], ctl["ptab_json"])


def _cross_country(sk, ctl, iso3, names) -> pd.DataFrame:
    st.subheader("Across All Countries: Who Is Most Exposed?")
    A = _all_country_results(sk, ctl).copy()
    A["name"] = A["iso3"].map(lambda c: names.get(c, c))
    A = A[A["gross_loss_usd"] > 0].copy()
    if A.empty:
        st.info("No country loses aid in this scenario.")
        return A
    st.caption(_esc(f"{ctl['preset']} · {_resp_label(ctl['fiscal_t'])}"))
    tot = A[["gross_loss_usd", "net_loss_usd", "deaths_y1", "deaths_5y", "deaths_5y_lo", "deaths_5y_hi", "hiv_infections_5y"]].sum()
    _stat_grid([
        (f"Aid Lost, {len(A)} Countries", money(tot["gross_loss_usd"]) + " a year",
         f"net of backfill {money(tot['net_loss_usd'])}", None),
        ("Extra Deaths, Year 1", num(tot["deaths_y1"]), None, None),
        ("Extra Deaths Over 5 Years", num(tot["deaths_5y"]), "range " + rng(tot["deaths_5y_lo"], tot["deaths_5y_hi"]),
         "Totals add up country results; the range adds country 2.5th and 97.5th percentiles, so it is wider than a "
         "jointly simulated interval."),
        ("New HIV Infections, 5 Years", num(tot["hiv_infections_5y"]), None, None),
    ], 4)
    A["deaths_per_100k"] = A["deaths_5y"] / A["pop"] * 1e5
    A["loss_pct_ghes_pct"] = A["loss_pct_ghes"] * 100

    st.plotly_chart(_world_map(A, iso3), **WIDE)

    c1, c2 = st.columns([1.15, 1])
    with c1:
        d = A[(A["loss_pct_ghes_pct"] > 0) & (A["deaths_per_100k"] > 0)]
        fig = go.Figure()
        other = d[d["iso3"] != iso3]
        sz = np.sqrt(d["net_loss_usd"].clip(lower=1)) / np.sqrt(d["net_loss_usd"].max()) * 40 + 6
        fig.add_trace(go.Scatter(x=other["loss_pct_ghes_pct"], y=other["deaths_per_100k"], mode="markers+text",
                                 text=[c if (r.deaths_per_100k > d["deaths_per_100k"].quantile(0.8) or
                                             r.loss_pct_ghes_pct > d["loss_pct_ghes_pct"].quantile(0.85)) else ""
                                       for c, r in zip(other["iso3"], other.itertuples())],
                                 textposition="top center", textfont=dict(size=11, color=MUTED),
                                 marker=dict(size=sz[d["iso3"] != iso3], color="rgba(93,109,126,0.45)",
                                             line=dict(color="white", width=1.5)),
                                 customdata=np.c_[other["name"], other["net_loss_usd"].map(money), other["deaths_5y"].map(num)],
                                 hovertemplate="<b>%{customdata[0]}</b><br>aid loss = %{x:.0f}% of government health "
                                               "spending<br>%{y:,.0f} deaths per 100,000 over 5 years "
                                               "(%{customdata[2]})<br>net loss %{customdata[1]} a year<extra></extra>",
                                 name="Countries"))
        me = d[d["iso3"] == iso3]
        if len(me):
            fig.add_trace(go.Scatter(x=me["loss_pct_ghes_pct"], y=me["deaths_per_100k"], mode="markers+text", text=[iso3],
                                     textposition="top center", textfont=dict(size=13, color=INK),
                                     marker=dict(size=sz[d["iso3"] == iso3], color="#c0392b", line=dict(color="white", width=2)),
                                     hoverinfo="skip", name="Selected country"))
        fig.add_vline(x=d["loss_pct_ghes_pct"].median(), line=dict(color=GRID, width=1, dash="dot"))
        fig.add_hline(y=d["deaths_per_100k"].median(), line=dict(color=GRID, width=1, dash="dot"))
        _layout(fig, h=480, title=_title("Budget Exposure vs. Deaths per Person"), showlegend=False,
                xaxis=dict(type="log", title="aid lost as % of government health spending (log)", ticksuffix="%",
                           tickvals=LOG_TICKS, ticktext=[f"{v:g}" for v in LOG_TICKS]),
                yaxis=dict(type="log", title="extra deaths per 100,000 people over 5 years (log)",
                           tickvals=LOG_TICKS, ticktext=[f"{v:g}" for v in LOG_TICKS]))
        st.plotly_chart(fig, **WIDE)
    with c2:
        top = A.sort_values("deaths_5y", ascending=False).head(15).iloc[::-1]
        fig = go.Figure()
        for b in hm.BUCKETS:
            fig.add_trace(go.Bar(y=top["name"], x=top[f"deaths_5y_{b}"], name=b, orientation="h",
                                 marker=dict(color=hm.BUCKET_COLORS[b], line=dict(color="white", width=1.5)),
                                 hovertemplate=f"%{{y}} · {b}: %{{x:,.0f}}<extra></extra>"))
        fig.update_layout(barmode="stack")
        _layout(fig, h=480, title=_title("15 Countries with the Most Extra Deaths (5 Years)"),
                legend=dict(orientation="h", y=-0.1, x=0))
        st.plotly_chart(fig, **WIDE)
    how_to_read("Map: darker countries lose more lives per person (the colour scale stops at the 95th percentile so a "
                "few extreme countries don't wash out the rest; hover for exact numbers). Scatter: bubble size = net aid "
                "lost per year; countries in the top right lose a lot relative to their own health budget *and* lose "
                "many lives per person, so they are the hardest to backfill with the highest stakes. Dotted lines are "
                "medians.")
    out = A.drop(columns=["name"]).sort_values("deaths_5y", ascending=False)
    st.download_button("Download All-Country Results (CSV)", out.to_csv(index=False).encode(),
                       file_name=f"model_results_{scn.preset_slug(ctl['preset'])}.csv", mime="text/csv")
    return A


def _world_map(A: pd.DataFrame, iso3: str):
    zmax = float(A["deaths_per_100k"].quantile(0.95))
    pct = A["loss_pct_ghes_pct"].map(lambda v: "n/a" if pd.isna(v) else f"{v:,.0f}%")
    fig = go.Figure(go.Choropleth(
        locations=A["iso3"], z=A["deaths_per_100k"], locationmode="ISO-3", zmin=0, zmax=zmax,
        colorscale=[[0, "#fbe9e7"], [0.5, "#e57368"], [1, "#922b21"]],
        marker_line_color="white", marker_line_width=0.6,
        colorbar=dict(title=dict(text="deaths per<br>100,000", font=dict(size=12)), thickness=12, len=0.7),
        customdata=np.c_[A["name"], A["gross_loss_usd"].map(money), A["deaths_5y"].map(num), pct],
        hovertemplate="<b>%{customdata[0]}</b><br>%{z:,.0f} extra deaths per 100,000 over 5 years<br>"
                      "extra deaths: %{customdata[2]}<br>aid lost: %{customdata[1]} a year<br>"
                      "= %{customdata[3]} of government health spending<extra></extra>"))
    sel = A[A["iso3"] == iso3]
    if len(sel):
        fig.add_trace(go.Choropleth(locations=sel["iso3"], z=[1], locationmode="ISO-3", showscale=False,
                                    colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
                                    marker_line_color=INK, marker_line_width=2, hoverinfo="skip"))
    fig.update_geos(projection_type="natural earth", showframe=False, showcoastlines=False, showcountries=True,
                    countrycolor="white", showland=True, landcolor="#eceff1", lataxis_range=[-45, 75])
    _layout(fig, h=460, title=_title("Extra Deaths per 100,000 People Over 5 Years"), margin=dict(l=0, r=0, t=50, b=0))
    return fig


# --------------------------------------------------------------------------- #
# Methods: cross-check summary and published estimates
# --------------------------------------------------------------------------- #
def _crosscheck_summary(res, I, ptab, country_name) -> str:
    regs = [I["reg"][k] for k in ("hiv_art", "tb_treatment", "dtp3")]
    s1 = (f"Panel regressions across up to {max(r['n_countries'] for r in regs)} countries (2005-2023, with country and "
          "year fixed effects) relate HIV treatment coverage, TB treatment coverage and DTP3 vaccine coverage to aid per "
          "person in need.")
    s3 = ("They are a lower bound for a sudden cut, because aid historically moved gradually and other funders filled "
          "gaps, so the truth for 2026-2030 most likely lies between the two approaches.")
    if res is None:
        return f"{s1} {s3}"
    xc = hm.statistical_crosscheck(res, I, ptab)
    if xc.empty:
        s2 = f"{country_name} has too little data on these three services for a comparison."
    else:
        s2 = (f"For {country_name} under this scenario they imply about {num(xc['deaths_5y'].clip(lower=0).sum())} extra "
              f"deaths over 5 years from these three services, against {num(xc['mech_deaths_5y'].sum())} from the "
              "unit-cost model.")
    return f"{s1} {s2} {s3}"


def _published_estimates(A: pd.DataFrame, I, ptab):
    st.markdown("#### Does This Match Published Estimates?")
    if A is None or A.empty:
        st.info("The current scenario cuts no aid, so there is nothing to compare.")
        return
    # model's future deaths averted per child immunised, births-weighted across the modelled countries
    Pc = hm.draw_params(ptab, 0)
    ci = I["ci"]
    per_child, births = [], []
    for c in A["iso3"]:
        row = ci.loc[c]
        b = row.get("births", np.nan)
        if pd.isna(b) or b <= 0:
            continue
        per_child.append(float(hm.per_unit_deaths(row, Pc, np.nan)["imm"][0, -1]))
        births.append(float(b))
    model_per_child = float(np.average(per_child, weights=births)) if births else np.nan
    n = len(A)
    tbl = pd.DataFrame([
        {"Study": "Cavalcanti et al., Lancet 2025",
         "What it covers": "USAID defunding; all causes and all programs; 133 countries; 2025-2030",
         "Published": "More than 14M additional deaths by 2030",
         "This model (current scenario)": f"{num(A['deaths_5y'].sum())} extra deaths over 5 years "
                                          f"(range {rng(A['deaths_5y_lo'].sum(), A['deaths_5y_hi'].sum())}), {n} countries"},
        {"Study": "ten Brink et al., Lancet HIV 2025",
         "What it covers": "HIV only; 24% cut by the top 5 donors plus PEPFAR ending; all low- and middle-income "
                           "countries; 2025-2030",
         "Published": "0.77M to 2.93M additional HIV deaths",
         "This model (current scenario)": f"{num(A['deaths_5y_HIV'].sum())} extra HIV deaths over 5 years, {n} countries"},
        {"Study": "Gavi (2000-2024)",
         "What it covers": "Future deaths averted per child immunised",
         "Published": "About 0.017 (20.6M deaths averted / 1.2B children)",
         "This model (current scenario)": f"{model_per_child:.3f} per child (births-weighted across countries)"},
    ])
    st.dataframe(tbl, hide_index=True, **WIDE)
    st.markdown("The published studies cover more causes, programs, countries or years than this model, which counts "
                "only HIV, TB, malaria and vaccine aid in the countries on this dashboard, so its totals should come "
                "in below the Cavalcanti figure and within or below the ten Brink range for comparable scenarios.")


# --------------------------------------------------------------------------- #
# Country brief (self-contained HTML; prints cleanly to PDF from the browser)
# --------------------------------------------------------------------------- #
def _brief_html(country_name, preset, resp_label, items, cards, figs) -> str:
    e = html.escape
    stats = "".join(f"<div class='stat'><div class='lbl'>{e(lbl)}</div><div class='val'>{e(val)}</div>"
                    f"<div class='sub'>{e(sub or '')}</div></div>" for lbl, val, sub, _ in items)
    card_html = "".join(f"<div class='card' style='border-top-color:{c['color']}'><div class='cb'>{e(c['bucket'])}</div>"
                        f"<div class='sub'>{e(c['service'])}</div><div class='cl'>{e(c['people'])}<br>"
                        f"<b>{e(c['coverage'])}</b> coverage drop<br><b>{e(c['deaths'])}</b> extra deaths over 5 years"
                        f"</div><div class='sub'>{e(c['foot'])}</div></div>" for c in cards)
    charts, first = [], True
    for f in figs:
        if f is None:
            continue
        g = go.Figure(f)
        g.update_layout(width=700, autosize=False)
        charts.append("<div class='chart'>" + g.to_html(full_html=False, include_plotlyjs="cdn" if first else False,
                                                        config={"displayModeBar": False, "responsive": False}) + "</div>")
        first = False
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(country_name)}: Funding-Cut Brief</title>
<style>
  @page {{ size: auto; margin: 14mm; }}
  body {{ font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; color: #2b2b2b; background: #fff;
         max-width: 720px; margin: 24px auto; padding: 0 16px; line-height: 1.45; }}
  h1 {{ font-size: 26px; margin: 0 0 4px; }}
  h2 {{ font-size: 18px; margin: 28px 0 10px; }}
  .meta {{ color: #6b6b6b; font-size: 14px; }}
  .grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }}
  .cards {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }}
  .stat, .card {{ border: 1px solid #ddd; border-radius: 8px; padding: 10px 12px; break-inside: avoid; }}
  .card {{ border-top: 4px solid; }}
  .lbl {{ font-size: 13px; color: #6b6b6b; }}
  .val {{ font-size: 22px; font-weight: 700; }}
  .sub {{ font-size: 12px; color: #6b6b6b; }}
  .cb {{ font-weight: 700; font-size: 16px; }}
  .cl {{ font-size: 14px; margin: 6px 0; }}
  .chart {{ break-inside: avoid; margin: 8px 0 0; }}
  .foot {{ color: #6b6b6b; font-size: 12px; margin-top: 24px; border-top: 1px solid #ddd; padding-top: 8px; }}
  @media print {{ body {{ margin: 0 auto; }} h2 {{ break-after: avoid; }} }}
</style></head><body>
<h1>{e(country_name)}: What a Funding Cut Does</h1>
<div class="meta"><b>Donor scenario:</b> {e(preset)}<br><b>Government response:</b> {e(resp_label)}</div>
<p class="meta">{e(PRESETS[preset])}</p>
<h2>The Headline</h2><div class="grid">{stats}</div>
<h2>Every US$1 Million Lost, by Bucket</h2><div class="cards">{card_html}</div>
<h2>Coverage and Deaths</h2>{''.join(charts)}
<div class="foot">Generated {_dt.date.today():%d %B %Y} from the Health Financing dashboard. Sources: IHME Development
Assistance for Health and health spending; World Bank WDI; WHO and UNAIDS series via Gapminder. Ranges are 95% intervals
from 400 Monte Carlo draws. Scenario estimates, not forecasts.</div>
</body></html>"""


METHODS = r"""
**1. Money.** Baseline aid is the 2021-2023 average from the IHME Development Assistance for Health database (constant 2023 US$),
kept at the level of *source x channel x program area* for each recipient. Program areas are grouped into service lines:
HIV treatment (treatment + care + testing), prevention of mother-to-child transmission, prevention, orphans and vulnerable
children; TB case finding & treatment, drug-resistant TB; malaria bednets/other vector control, indoor spraying, case
management; vaccines. Aid with no program area reported is spread over the bucket's known mix (the country's own, or the
global mix if it has none). Systems money (labs, staff, monitoring) is lost in full, but only a share κ (default 50%) is
assumed to translate into lost services. A scenario sets a cut for every cell; donor and channel cuts combine as
1 - (1 - donor cut)(1 - channel cut).

**2. Fiscal response.** Replacement R = min(θ x gross loss, capacity), where capacity = government health spending x
(75th-percentile, or 90th for the "best years" ceiling, minus median real growth in government health spending, 2001-2023)
x debt-stress factor (1 at interest ≤ 10% of revenue, falling linearly to 0.25 at 40%). The *historical* θ comes from a
two-way fixed-effects regression of the change in government health spending per person on falls (and lagged falls) in aid
per person across 97 countries; the estimate is slightly negative and not significant, i.e. no historical backfilling.
Replacement money is allocated pro-rata or "lives first" (lines with the most deaths averted per dollar first).

**3. Coverage.** People losing a service = net loss ÷ cost per person x (1 - continuity), capped at the number currently
covered. Costs = commodity cost + delivery cost x (GDP per capita / $2,000)^0.4. Coverage drop (percentage points) = people
losing service ÷ population in need: people living with HIV (prevalence x population 15-64, calibrated to UNAIDS 2011
counts, + children), HIV+ pregnancies, TB incidence, population at malaria risk, malaria cases, births.

**4. Lives.**
- *HIV treatment:* excess deaths among people off treatment rise 1.2%, 2.8%, 3.8%, 4.5%, 5% in years 1-5 (x an uncertain
  multiplier); they also transmit HIV (0.04 infections per person-year).
- *Mother-to-child transmission:* infections averted per mother (0.22) x death by age 2 if infected (0.45).
- *TB:* deaths per patient untreated = case-fatality untreated minus treated (WHO: 0.43 vs 0.03 HIV-negative; higher for
  HIV-positive, weighted by the country's TB/HIV share and HIV treatment coverage).
- *Malaria:* Lives Saved Tool form, D₁ = D₀ x Π (1 - E·C₁)/(1 - E·C₀) with E = 0.45 for vector control and 0.60 for case
  management, D₀ = malaria deaths (WHO/MCEE child malaria deaths ÷ under-5 share: 0.76 in Africa, 0.40 elsewhere).
- *Vaccines:* future deaths averted per child immunised (Gavi: 0.017-0.024) x country under-5 mortality ÷ 50.
- Year-by-year lags: deaths build up over 5 years (see the yearly deaths chart).

**Uncertainty.** All parameters in the table are drawn from triangular(low, central, high); 400 draws per country. Headline
numbers are the central-parameter run; ranges are the 2.5th and 97.5th percentiles.

**Data.** IHME DAH 1990-2025 (Sept 2026 release), IHME health spending 1995-2023 and expected spending 2024-2050, IHME GDP;
World Bank WDI (UNAIDS, WHO, WUENIC, UN IGME series) and Gapminder's mirrors of WHO TB estimates and WHO/MCEE child
cause-of-death estimates; the team's MOU / co-financing sheet.

**Limitations.** Costs are averages, but cuts hit marginal services first; some cut services are cheaper or dearer. Coverage
indicators for malaria come from household surveys and can be old. Program-area tags in IHME are partial (most TB aid is
untagged). The model does not capture second-round effects (drug resistance, outbreaks such as measles, health-worker
layoffs) or re-allocation by other donors, and post-2023 aid is not observed at the recipient level. Treat outputs as
scenario estimates, not forecasts.
"""
