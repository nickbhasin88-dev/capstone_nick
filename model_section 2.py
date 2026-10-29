"""
Section 4 of the dashboard: what a funding cut does (money -> fiscal response -> coverage -> lives).

Called from app.py:   render_model_section(iso3, country_name, imf_overrides, names)
All modelling lives in health_model.py and the scenario presets in scenarios.py; this file builds the sidebar
controls and draws the results. chart / stat / title_case are shared with app.py so every section looks the same;
colors and fonts come from theme.py.
"""
from __future__ import annotations

import datetime as _dt
import html
import io
import re

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import health_model as hm
import scenarios as scn
import paths_ui
import theme as th
from scenarios import PRESETS

_ver = tuple(int(x) for x in st.__version__.split(".")[:2] if x.isdigit())
WIDE = {"width": "stretch"} if _ver >= (1, 50) else {"use_container_width": True}

INK, MUTED, GRID = th.INK, th.MUTED, th.RULE
SCATTER_LABELS = 8                   # label the 8 countries with the most deaths per 100,000
LABEL_GAP_LOG = 0.2                  # min vertical gap between stacked scatter labels (log10 units, ~18px)
MAP_FOCUS = dict(center=dict(lon=58, lat=4), projection_scale=2.0)     # Africa and South / Southeast Asia
LOG_TICKS = [0.01, 0.1, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000]
LOSS, BACKFILL = th.ROSE, th.TEAL
SCEN_A, SCEN_B = th.GRAPE, th.BLUE
BUCKET_COLORS = th.DISEASE_COLORS
REPLACED_ALPHA = 0.4                 # "replaced by government" = the disease color at this opacity
FIRST_YEAR = 2026                    # year 1 after the cut
MAIN_LINE = {"HIV": "hiv_art", "TB": "tb_ds", "Malaria": "mal_itn", "Immunization": "imm"}
BUCKET_WORD = {"HIV": "HIV", "TB": "TB", "Malaria": "malaria", "Immunization": "immunization"}

# The estimated historical response (theta) is no replacement, the same as "none", so it isn't offered separately
NO_REPLACEMENT = "No Government Replacement"
GOV_MODES = {NO_REPLACEMENT: "none", "Replace a set share": "custom",
             "As much as fiscal space allows": "max", "Gradual budget increase": "gradual"}
RANGE_LABEL, RANGE_TIP = th.RANGE_LABEL, th.RANGE_TIP
SRC_MODEL = "Model estimates from IHME aid data (2021-23 average), WHO, UNAIDS and World Bank data; see Methods."
SHOW_BRIEF = False                   # the Download Country Brief button (code kept for later)
PRESET_SHORT = {
    "Full US exit": "US bilateral health aid ends and the US withdraws from multilateral agreements (its Global Fund pledge "
                    "falls 23%, so 77% of it is kept). Other US multilateral money is unchanged.",
    "America First MOUs": "US bilateral aid follows this country's signed MOU year by year, 2026-2030; US multilateral "
                          "exits as in US Bilateral Exit + Multilateral Withdrawals. The partner government's co-financing commitments are not "
                          "modelled.",
    "IHME 2025 preliminary estimates": "IHME's preliminary 2025 change for every donor, channel and disease. IHME has "
                                       "no country split for 2025, so this country's mix gets the global ratios.",
    "OECD-reported 2025 aid cuts": "Each donor's 2025 cut in total aid, all sectors (US -57%, Germany -17%, France -11%, "
                                   "UK -11%, Japan -6%), applied to its health aid.",
    "Global Fund & Gavi shortfalls": "All donors' money through Gavi and the Global Fund falls by the share set "
                                     "below, against each fund's 2021-23 disbursements.",
    "Combined retreat": "US Bilateral Exit + Multilateral Withdrawals plus the OECD-reported 2025 total-aid cuts for every other donor.",
    "Custom": "Set the cuts yourself by donor and by channel.",
}
CEILINGS = {"Strong year (75th percentile growth)": "p75", "Best years (90th percentile growth)": "p90"}
# L-30: refilling in order of the model's own deaths per dollar is an optimisation rule, not observed behaviour
LIVES_FIRST = "Hypothetical best case (triage)"
ALLOCS = {"Pro-rata to what was cut": "pro_rata", LIVES_FIRST: "lives_first"}


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
def _run(iso3, sc_key, fiscal_t, ptab_json, trend=True, n_draws=400, cut_path=None, gov_add=None):
    """Cached by (country, scenario, response, parameters, trend, cut path, government-money path), so moving a
    slider back to an earlier value is instant. cut_path / gov_add: tuples of 5 (None = sudden cut, no extra money)."""
    ptab = pd.read_json(io.StringIO(ptab_json), orient="split")
    return hm.run_country(iso3, scn.scenario_from_key(sc_key), hm.Fiscal(*fiscal_t), _inputs(), ptab, n_draws=n_draws,
                          mortality_trend=trend, cut_path=cut_path, gov_add_usd=gov_add)


@st.cache_data(show_spinner=False, max_entries=64)
def _break_even(iso3, sc_key, fiscal_t, cut_path):
    return hm.break_even_share(iso3, scn.scenario_from_key(sc_key), hm.Fiscal(*fiscal_t), _inputs(), cut_path)


def run_ctl(iso3, sk, ctl, **kw):
    """The model run for the current settings, including the funding and budget paths."""
    return _run(iso3, sk, kw.get("fiscal_t", ctl["fiscal_t"]), ctl["ptab_json"], ctl["trend"],
                cut_path=ctl.get("cut_path"), gov_add=kw.get("gov_add", ctl.get("gov_add")))


@st.cache_data(show_spinner=False, max_entries=32)
def _dose(iso3, bucket, fiscal_t, ptab_json, trend=True):
    # 21 points (0-100% in 5% steps); run_country draws its parameters with the same seed at every point, so the band
    # is built from the same random draws all along the curve
    ptab = pd.read_json(io.StringIO(ptab_json), orient="split")
    return hm.dose_response(iso3, bucket, hm.Fiscal(*fiscal_t), _inputs(), ptab, grid=np.linspace(0, 1, 21), n_draws=100,
                            mortality_trend=trend)


@st.cache_data(show_spinner=False, max_entries=32)
def _scenario_path(iso3, sc_key, bucket, fiscal_t, ptab_json, trend=True, cut_path=None, gov_add=None):
    """This scenario's own path for one bucket: every cut scaled from 0% to 100% of its size (21 points, the same
    draws as the even-cut curve), as (share of the bucket's aid lost, extra deaths over 5 years)."""
    ptab = pd.read_json(io.StringIO(ptab_json), orient="split")
    rows = []
    for k in np.linspace(0, 1, 21):
        sc = scn.scenario_from_key(sc_key)
        sc.scale = float(k)
        r = hm.run_country(iso3, sc, hm.Fiscal(*fiscal_t), _inputs(), ptab, n_draws=100, mortality_trend=trend,
                           cut_path=cut_path, gov_add_usd=gov_add)
        bb = r["buckets"].set_index("bucket").loc[bucket]
        rows.append({"k": k, "cut": bb["gross_loss_usd"] / bb["base_usd"] if bb["base_usd"] > 0 else 0.0,
                     "deaths_5y": bb["deaths_5y"]})
    return pd.DataFrame(rows)


@st.cache_data(show_spinner="Running the model for every country...", max_entries=16)
def _run_all(sc_key, fiscal_t, ptab_json, trend=True):
    ptab = pd.read_json(io.StringIO(ptab_json), orient="split")
    return hm.run_all(scn.scenario_from_key(sc_key), hm.Fiscal(*fiscal_t), _inputs(), ptab,
                      n_draws=scn.ALL_COUNTRY_DRAWS, mortality_trend=trend)


@st.cache_data(show_spinner=False)
def _precomputed(preset: str, _mtime: float) -> pd.DataFrame:
    """A precomputed All Countries file with its per-draw totals attached (scenarios.load_precomputed); _mtime only
    invalidates the cache when the file changes."""
    return scn.load_precomputed(hm.MODEL_DIR, preset)


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
    return f"{s}${a:,.2f}" if 0 < a < 10 else f"{s}${a:,.0f}"


def num(x: float) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "n/a"
    if abs(x) < 0.5:                                   # no "-0" from tiny negative rounding
        return "0"
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


# Title Case for labels (not sentences): small words stay lowercase unless first or after a colon; words that already
# contain capitals or digits (acronyms, units, numbers) and a few unit words are left exactly as written.
_SMALL = {"a", "an", "the", "and", "or", "nor", "but", "of", "in", "on", "to", "for", "per", "vs", "vs.", "by", "at",
          "as", "via", "with", "from"}
_KEEP = {"pp", "pts", "yr", "n/a", "e.g.", "i.e."}


def _tc_part(p: str, first: bool) -> str:
    m = re.match(r"^([^A-Za-z]*)([A-Za-z][A-Za-z'’]*)(.*)$", p)
    if not m:
        return p
    pre, core, post = m.groups()
    if re.search(r"\d", pre) or core != core.lower() or core.lower() in _KEEP:
        return p
    if core in _SMALL and not first:
        return p
    return pre + core[0].upper() + core[1:] + post


def title_case(text):
    """'57% of $512.8M for these four buckets' -> '57% of $512.8M for These Four Buckets'. HTML tags pass through."""
    if not isinstance(text, str) or not text:
        return text
    out, first = [], True
    for seg in re.split(r"(<[^>]+>)", text):
        if seg.startswith("<") and seg.endswith(">"):
            out.append(seg)
            continue
        words = []
        for w in re.split(r"(\s+)", seg):
            if not w or w.isspace():
                words.append(w)
                continue
            if w.lower() in _KEEP:
                words.append(w)
            else:
                parts = re.split(r"([-/])", w)
                words.append("".join(x if x in "-/" else _tc_part(x, first and i == 0) for i, x in enumerate(parts)))
            if re.search(r"[A-Za-z0-9]", w):
                first = w.endswith(":")
        out.append("".join(words))
    return "".join(out)


def tc_fig(fig):
    """Title Case a figure's labels: title, legend entries, axis and color-bar titles, annotations."""
    for t in fig.data:
        if getattr(t, "name", None):
            t.name = title_case(t.name)
        cb = getattr(t, "colorbar", None)
        if cb is not None and cb.title is not None and cb.title.text:
            cb.title.text = title_case(cb.title.text)
    if fig.layout.title is not None and fig.layout.title.text:
        fig.layout.title.text = title_case(fig.layout.title.text)
    fig.for_each_xaxis(lambda a: a.update(title_text=title_case(a.title.text)) if a.title.text else None)
    fig.for_each_yaxis(lambda a: a.update(title_text=title_case(a.title.text)) if a.title.text else None)
    for an in fig.layout.annotations or []:
        if an.text:
            an.text = title_case(an.text)
    return fig


def chart(fig, source: str | None = None, note: str | None = None, labels: bool = False, **kw):
    """Draw a figure in the editorial style, with the small 'Note / Source' line underneath. labels=True names each
    series at the right end of a stacked bar chart instead of using a legend."""
    fig = th.style_fig(tc_fig(fig))
    if labels:
        th.direct_labels(fig)
    # theme=None: draw with the "editorial" Plotly template instead of Streamlit's chart theme
    st.plotly_chart(fig, theme=None, config={"displayModeBar": False}, **WIDE, **kw)
    if source or note:
        st.markdown(th.source_html(source, note), unsafe_allow_html=True)


def pill_row(items, cols: int | None = None):
    """A row (or grid, with cols) of equal pills. items: (label, value[, note under the value[, tooltip]])."""
    rows = [(title_case(it[0]), it[1], it[3] if len(it) > 3 else None, title_case(it[2]) if len(it) > 2 else None)
            for it in items]
    st.markdown(th.pills_html(rows, cols=cols, large=True), unsafe_allow_html=True)


def _stat_grid(items, ncols):
    pill_row(items, ncols)


def _layout(fig, h=380, **kw):
    margin = kw.pop("margin", dict(l=10, r=10, t=50, b=10))
    fig.update_layout(height=h, margin=margin, **kw)
    fig.update_xaxes(automargin=True)
    fig.update_yaxes(automargin=True)
    return fig


def _title(text):
    return dict(text=title_case(text), x=0, xanchor="left")


def _resp_label(fiscal_t) -> str:
    mode, theta, _, alloc, ceiling = fiscal_t
    lbl = {"none": NO_REPLACEMENT, "custom": f"Government replaces {theta:.0%}",
           "max": "As much as fiscal space allows", "gradual": "Gradual budget increase"}[mode]
    if mode not in ("none", "gradual"):
        lbl += (", hypothetical best case (triage)" if alloc == "lives_first" else ", pro-rata")
        lbl += (", best-years ceiling" if ceiling == "p90" else "")
    return title_case(lbl)


# --------------------------------------------------------------------------- #
# Sidebar controls
# --------------------------------------------------------------------------- #
# Global Fund & Gavi Shortfalls sliders (audit I-07): reference marks shown under each slider, and the tooltip
SHORTFALL_SLIDERS = {
    "gavi_cut": ("Gavi Funding Cut", scn.GAVI_CUT_DEFAULT,
                 ["~15%: fall vs 2021-23 spending (our estimate)", "24%: gap vs Gavi's US$11.9B target"],
                 "Cut on every donor's money through Gavi, against Gavi's 2021-23 disbursements (the model baseline). "
                 "Gavi 6.0 raised more than US$9B for 2026-2030 (including leftover COVID funds and earlier pledges) "
                 "against a US$11.9B target; the US made no new contribution. That is about US$1.75B a year in 2023 "
                 "US$, about 15% below Gavi's 2021-23 spending excluding COVID (US$2.06B a year in IHME's data; our "
                 "estimate). Sources: Gavi press release (June 2025), Devex, Donor Tracker (2026)."),
    "gf_cut": ("Global Fund Funding Cut", scn.GF_CUT_DEFAULT,
               ["15%: allocation cut in MOU countries (KFF, Jun 2026)", "~20%: pledges vs previous replenishment",
                "~24%: median cut in allocation letters (Aidspan)", "30%: gap vs US$18B target"],
               "Cut on every donor's money through the Global Fund, against its 2021-23 disbursements (the model "
               "baseline). Eighth Replenishment final total US$12.64B (Global Fund Board, Feb 2026) vs a US$18B target "
               "and US$15.7B in the Seventh; 2026-2028 country allocations US$10.78B. KFF (Jun 2026) finds allocations "
               "in MOU countries down 15% vs the original GC7 allocations (range 5% Niger to 53% Guatemala); Aidspan's "
               "median is about -24%. All nominal; real cuts are somewhat deeper."),
}


def _shortfall_sliders(key) -> dict:
    """The two Global Fund & Gavi Shortfalls sliders, each with its reference marks underneath."""
    out = {}
    for k, (label, default, marks, tip) in SHORTFALL_SLIDERS.items():
        out[k] = int(st.slider(f"{label} (%)", 0, 50, default, 1, key=f"{key}_{k}", help=_esc(tip)))
        st.markdown(f"<div style='font-size:11px;line-height:1.35;color:{MUTED};margin:-0.6rem 0 0.5rem'>"
                    + "<br>".join(html.escape(m) for m in marks) + "</div>", unsafe_allow_html=True)
    return out


def _preset_options(preset, ci, iso3, country_name, key):
    opts = scn.default_opts(preset, ci)
    if preset == scn.SHORTFALLS:
        opts.update(_shortfall_sliders(key))
    if preset == "Custom":
        with st.expander("Cuts by Donor and Channel", expanded=True):
            ed = pd.DataFrame({"Donor": hm.SOURCE_GROUPS,
                               "Bilateral & NGO Cut %": [opts["custom_direct"][s] for s in hm.SOURCE_GROUPS],
                               "Via Multilaterals Cut %": [opts["custom_multi"][s] for s in hm.SOURCE_GROUPS]})
            ed = st.data_editor(ed, hide_index=True, key=f"{key}_custom_tbl", disabled=["Donor"],
                                column_config={c: st.column_config.NumberColumn(min_value=-50, max_value=100, step=5)
                                               for c in ("Bilateral & NGO Cut %", "Via Multilaterals Cut %")})
            opts["custom_direct"] = dict(zip(ed["Donor"], ed["Bilateral & NGO Cut %"]))
            opts["custom_multi"] = dict(zip(ed["Donor"], ed["Via Multilaterals Cut %"]))
            opts["custom_chan"] = {ch: st.slider(f"{ch} Channel Cut (%)", 0, 100, 0, 5, key=f"{key}_ch_{ch}",
                                                 help="Hits every donor's money through this channel "
                                                      "(e.g. a replenishment shortfall).")
                                   for ch in ["Global Fund", "Gavi", "WHO", "UNICEF"]}
    return opts


MOU = "America First MOUs"
MOU_SHAPE = "Follows MOU schedule"   # internal path label: the scenario carries the country's own yearly cuts


def preset_choices(ci, iso3) -> tuple:
    """(options, format_func, group) for the Donor Scenario dropdown: America First MOUs is offered where the country
    has a signed MOU with schedule data (group A), listed but unavailable where it has signed without data (B), and not
    listed otherwise (C)."""
    group = scn.mou_group(ci, iso3)
    opts = [p for p in PRESETS if not (p == MOU and group == scn.MOU_GROUP_C)]

    def fmt(p):
        return title_case(scn.display_name(p)) + (f" ({scn.NO_MOU_DATA})" if p == MOU and group == scn.MOU_GROUP_B
                                                   else "")
    return opts, fmt, group


def mou_fallback(ci, iso3, country_name):
    """If America First MOUs is selected for a country without MOU schedule data, switch to US Bilateral Exit + Multilateral Withdrawals and return the
    one-line notice (None otherwise). Call before the Donor Scenario dropdown is drawn."""
    if st.session_state.get("sel_preset") == MOU and scn.mou_group(ci, iso3) != scn.MOU_GROUP_A:
        prev = st.session_state.get("prev_preset")
        if prev and prev != MOU:                     # just picked for a country that signed without funding data
            st.session_state["sel_preset"] = prev
            return f"America First MOUs: {scn.NO_MOU_DATA}"
        st.session_state["sel_preset"] = "Full US exit"   # switched country while the preset was on
        return f"{country_name}: no MOU funding data; showing US Bilateral Exit + Multilateral Withdrawals."
    return None


def donor_scenario_select(ci, iso3, country_name, widget_key, label="Donor Scenario"):
    """The Donor Scenario dropdown with the MOU rules (shared by the Dashboard and Validation pages). Returns
    (preset, MOU group of the country, notice or None)."""
    note = st.session_state.pop("mou_note", None) or mou_fallback(ci, iso3, country_name)
    opts, fmt, group = preset_choices(ci, iso3)
    preset = th.shared_select(label, opts, widget_key, "sel_preset", opts[0], format_func=fmt,
                              help=_esc(PRESETS[st.session_state.get("sel_preset", opts[0])]))
    if preset == MOU and group == scn.MOU_GROUP_B:                   # listed but unavailable: no model run
        prev = st.session_state.get("prev_preset", "Full US exit")
        st.session_state["sel_preset"] = prev if prev != MOU else "Full US exit"
        st.session_state["mou_note"] = f"America First MOUs: {scn.NO_MOU_DATA}"
        st.rerun()
    st.session_state["prev_preset"] = preset
    return preset, group, note


def backfill_regression_text(reg) -> str:
    """'Across N countries, first-last, governments did not replace falling aid (theta per $1, 95% CI lo to hi).'
    Every value comes from regressions.json (fiscal_replacement)."""
    r = reg["fiscal_replacement"]
    th_c, th_lo, th_hi = hm.theta_historical(reg)
    return (f"Across {r['n_countries']} countries, {r['years'][0]}-{r['years'][1]}, governments did not replace falling "
            f"aid ({th_c:+.2f} per $1, 95% CI {th_lo:+.2f} to {th_hi:+.2f}).")


def _controls(iso3, country_name, I) -> dict:
    """Slim scenario bar under the story headline: scenario | government response | Advanced (popover)."""
    ci = I["ci"]
    ctx = st.session_state.get("model_ctx", {})
    if "m_trend" not in st.session_state:
        st.session_state["m_trend"] = ctx.get("trend", scn.DEFAULT_MORTALITY_TREND)
    if st.session_state.get("m_mode") not in GOV_MODES:          # e.g. an option from an older version of the page
        st.session_state["m_mode"] = list(GOV_MODES)[0]
    with st.container(key="model_controls"):
        st.markdown("<div id='change-scenario' class='ed-kicker' style='margin:0'>Change the Scenario</div>",
                    unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns([1.3, 1.1, 1.3, 0.75], gap="medium")
        with c1:
            preset, group, note = donor_scenario_select(ci, iso3, country_name, "m_preset")
            if note:
                st.caption(_esc(note))
            schedule, sched_end = scn.mou_schedule(ci, iso3) if preset == MOU else (None, None)
            st.caption(_esc(scn.mou_schedule_text(ci, iso3, country_name) if preset == MOU
                            else PRESET_SHORT.get(preset, PRESETS[preset])))
            opts = _preset_options(preset, ci, iso3, country_name, "m")
        with c2:
            if preset == MOU:
                ended = sched_end is not None and sched_end < scn.YEARS[-1]
                tip = (f" title='{html.escape(f'Schedule ends {sched_end}; {sched_end} level held through {scn.YEARS[-1]}.', quote=True)}'"
                       if ended else "")
                st.markdown(f"<div class='ed-kicker' style='margin:0.35rem 0 0'{tip}>"
                            f"{html.escape(f'Follows {country_name}' + chr(39) + 's MOU schedule')}</div>",
                            unsafe_allow_html=True)
                paths_ui.mou_schedule_chart(schedule, sched_end)
                shape = MOU_SHAPE
            else:
                shape = paths_ui.path_selector()
        budget = hm.health_budget(iso3, I)
        room = 0.0
        with c3:
            mode = GOV_MODES[st.selectbox(
                "Government Response", list(GOV_MODES), key="m_mode", format_func=title_case,
                help=_esc("How much of the lost aid the government replaces from its own budget. "
                          + backfill_regression_text(I["reg"])))]
            theta = 0.0
            if mode == "custom":
                theta = st.slider("Share of Lost Aid Replaced (%)", 0, 100, 25, 5, key="m_theta") / 100
            if mode != "gradual":
                st.session_state["gov_panel_on"] = False
            if mode == "gradual":
                if budget["gov_spend_usd"] == budget["gov_spend_usd"]:
                    room = paths_ui.gradual_controls(budget)
                else:
                    st.caption("No data on this government's total spending, so a budget increase can't be modelled.")
                    mode = "none"
        with c4:
            st.markdown("<div style='height:1.75rem'></div>", unsafe_allow_html=True)
            adv = st.popover("Advanced", icon=":material/tune:", width="stretch")
        with adv:
            ceiling = CEILINGS[st.radio("Fiscal-Space Ceiling", list(CEILINGS), key="m_effort",
                                        disabled=(mode == "none"), format_func=title_case,
                                        help="How hard can the health budget be pushed? Capacity = government health "
                                             "spending x (that growth rate minus the country's typical growth) x a "
                                             "debt-stress factor, every year.")]
            alloc = ALLOCS[st.radio("Where Replacement Money Goes", list(ALLOCS), key="m_alloc",
                                    disabled=(mode == "none"), format_func=title_case,
                                    help="Hypothetical best case: an optimisation rule, not how governments are known to "
                                         "behave. It refills the services that avert the most deaths per dollar first "
                                         "(usually TB treatment, vaccines, ART) before anything else.")]
            cap = st.checkbox("Cap Replacement at Fiscal Space", value=True, key="m_cap",
                              disabled=(mode in ("none", "max")))
            trend = st.toggle("Account for Already-Changing Death Rates", key="m_trend",
                              help="Under-5 mortality keeps falling at each country's 2010-2019 rate (-0.9% a year "
                                   "where there is no usable trend; Cavalcanti et al. 2025, Lancet, appendix 10.2). "
                                   "Baseline malaria deaths follow the country's 2015-2024 trend in WHO's estimated "
                                   "malaria deaths, within ±5% a year (the ±5% limit is an assumption). The rebound "
                                   "after bednets and spraying stop is a separate assumption. TB and HIV treatment effects are per patient and "
                                   "unchanged.")
            st.divider()
            cmp = None
            if st.toggle("Compare with a Second Scenario", value=False, key="m_compare"):
                options_b = ["Same as Scenario A"] + [p for p in scn.PRECOMPUTED_PRESETS
                                                      if p != MOU or group == scn.MOU_GROUP_A]
                pb = st.selectbox("Donor Scenario (B)", options_b, index=0, key="mb_preset",
                                  format_func=lambda p: title_case(scn.display_name(p)))
                if pb == "Same as Scenario A":
                    preset_b, opts_b = preset, opts
                else:
                    preset_b = pb
                    opts_b = _preset_options(preset_b, ci, iso3, country_name, "mb")
                mode_b = GOV_MODES[st.radio("Government Response (B)", list(GOV_MODES),
                                            index=list(GOV_MODES).index("As much as fiscal space allows"), key="mb_mode",
                                            format_func=title_case)]
                theta_b = st.slider("Share of Lost Aid Replaced (B, %)", 0, 100, 25, 5, key="mb_theta") / 100 \
                    if mode_b == "custom" else 0.0
                alloc_b = ALLOCS[st.radio("Where Replacement Money Goes (B)", list(ALLOCS),
                                          index=list(ALLOCS).index(LIVES_FIRST), key="mb_alloc",
                                          format_func=title_case, disabled=(mode_b == "none"))]
                st.caption("Scenario B uses Scenario A's fiscal-space ceiling and model parameters.")
                cmp = {"preset": preset_b, "opts": opts_b, "fiscal_t": (mode_b, theta_b, True, alloc_b, ceiling)}
            st.divider()
            st.markdown("**Model Parameters**")
            st.caption("Each parameter is drawn from a triangular distribution (low, central, high). "
                       "Edit any cell to see how sensitive the answer is.")
            ptab = st.data_editor(_default_params().reset_index(), hide_index=True, key="m_params",
                                  disabled=["param", "label", "unit", "status", "source"],
                                  column_config={"param": None, **{c: st.column_config.Column(c.title())
                                                                   for c in ("label", "central", "low", "high", "unit",
                                                                             "status", "source")}}, width=900)
            ptab = ptab.set_index("param")
            problems = hm.validate_params(ptab)
            if problems:                     # keep the previous valid table instead of running (or crashing) on it
                st.caption(_esc("Not applied: " + "; ".join(problems[:3]) + (" ..." if len(problems) > 3 else "")
                                + ". Using the last valid values."))
                prev = st.session_state.get("last_valid_ptab_json")
                ptab = pd.read_json(io.StringIO(prev), orient="split") if prev else _default_params()
            else:
                st.session_state["last_valid_ptab_json"] = ptab.to_json(orient="split")

        # ---- when the funding path or the response is not the default, the box expands: chart + year sliders ----
        expanded = (shape not in (paths_ui.SUDDEN, MOU_SHAPE)) or mode == "gradual"
        cut_path, pts, outcome_slot = None, [0.0] * 5, None
        if expanded:
            st.divider()
            cut, pts = paths_ui.year_panel(iso3, country_name, scn.build_scenario(preset, opts, ci),
                                           hm.Fiscal(mode, theta, cap, alloc, ceiling), I, mode == "gradual", budget,
                                           room, schedule)
            cut_path = tuple(round(c, 4) for c in cut)
            outcome_slot = st.container()
    gov_add = tuple(float(v) for v in hm.gov_add_from_points(pts, budget["gov_spend_usd"])) \
        if mode == "gradual" and any(pts) else None
    if cut_path is not None and all(abs(c - 1) < 1e-9 for c in cut_path):
        cut_path = None                                # identical to the sudden cut: share its cached results
    return {"preset": preset, "opts": opts, "fiscal_t": (mode, theta, cap, alloc, ceiling), "mode": mode,
            "ptab": ptab, "ptab_json": ptab.to_json(orient="split"), "cmp": cmp, "trend": trend,
            "shape": shape, "cut_path": cut_path, "gov_pts": pts, "gov_add": gov_add, "budget": budget,
            "expanded": expanded, "outcome_slot": outcome_slot}


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
INTRO = ("A four-step model for HIV, TB, malaria and immunization: the donor scenario removes aid; the government "
         "can replace part of it, limited by fiscal space; money not replaced ÷ cost per person = people-equivalents of "
         "service lost (the service the lost money would have paid for, not a headcount); and each lost service x its "
         "effect on mortality = extra deaths. Ranges are the range across parameter "
         "values (2.5th-97.5th percentile of 400 Monte Carlo draws). " + RANGE_TIP)


def scenario_bar(iso3: str, country_name: str):
    """Draw the scenario bar and return (settings, scenario key); also shares the settings with the other pages."""
    I = _inputs()
    ctl = _controls(iso3, country_name, I)
    sk = scn.scenario_key(scn.build_scenario(ctl["preset"], ctl["opts"], I["ci"]))
    st.session_state["model_ctx"] = {"iso3": iso3, "country_name": country_name, "preset": ctl["preset"],
                                     "opts": ctl["opts"], "fiscal_t": ctl["fiscal_t"], "ptab_json": ctl["ptab_json"],
                                     "trend": ctl["trend"], "cut_path": ctl["cut_path"], "gov_add": ctl["gov_add"]}
    if ctl["expanded"] and iso3 in I["ci"].index and iso3 in set(I["lines"].iso3):
        res = run_ctl(iso3, sk, ctl)
        base = _run(iso3, sk, scn.DEFAULT_FISCAL, ctl["ptab_json"], ctl["trend"])      # sudden cut, no response
        be = _break_even(iso3, sk, ctl["fiscal_t"], ctl["cut_path"])
        with ctl["outcome_slot"]:
            paths_ui.outcome_panel(country_name, ctl["shape"], response_phrase(ctl), res, base["committed"]["deaths"],
                                   be, ctl["budget"], num, rng, round_words, after_2030_help)
    return ctl, sk


def response_phrase(ctl) -> str:
    """The government response, as a phrase for the outcome sentence."""
    mode, theta = ctl["fiscal_t"][0], ctl["fiscal_t"][1]
    if mode == "gradual":
        p = ctl["gov_pts"]
        steady = all(abs(p[i] - p[0] * (i + 1)) < 0.051 for i in range(5))
        return (f"raising health's budget share by {p[0]:.1f} points a year" if steady and p[0] > 0
                else f"raising health's budget share to +{p[-1]:.1f} points by 2030")
    return {"none": "with no government response", "custom": f"with the government replacing up to {theta:.0%} of "
            "the lost aid", "max": "with the government replacing what its budget allows"}.get(mode, "")


# --------------------------------------------------------------------------- #
# Story lede: a headline, a short summary and three big numbers, written from the model's results
# --------------------------------------------------------------------------- #
SCENARIO_PHRASE = {
    "Full US exit": "If U.S. bilateral health aid ends and the U.S. withdraws from multilateral agreements",
    "America First MOUs": "If U.S. aid follows the new “America First” health agreements",
    "IHME 2025 preliminary estimates": "If aid follows IHME’s 2025 estimates",
    "OECD-reported 2025 aid cuts": "If donors cut health aid as much as their total 2025 aid",
    "Global Fund & Gavi shortfalls": "If the Global Fund and Gavi fall short of their targets",
    "Combined retreat": "If the U.S. exits and other donors cut too",
    "Custom": "Under this scenario",
}


def scenario_title(preset: str, opts: dict | None = None) -> str:
    """The preset's name for captions and kickers, with the chosen cuts for Global Fund & Gavi Shortfalls."""
    return title_case(scn.display_name(preset)) + (f" · {scn.shortfall_label(opts)}" if preset == scn.SHORTFALLS
                                                   else "")


def scenario_phrase(preset: str, opts: dict | None = None) -> str:
    """Opening of the headline, e.g. 'If Gavi funding falls 15% and Global Fund funding 20%'."""
    if preset == scn.SHORTFALLS:
        g, f = scn.shortfall_cuts(opts)
        if g and f:
            return f"If Gavi funding falls {g}% and Global Fund funding {f}%"
        if g or f:
            return f"If {'Gavi' if g else 'Global Fund'} funding falls {g or f}%"
        return "If Gavi and Global Fund funding hold steady"
    return SCENARIO_PHRASE.get(preset, "Under this scenario")


CAUSE_PHRASE = {"HIV": "people losing HIV treatment and prevention", "TB": "untreated tuberculosis",
                "Malaria": "lost malaria nets and treatment", "Immunization": "missed childhood vaccinations"}
# Treatment and Prevention Lost Each Year (L-40): every service line except HIV prevention (its unit is infections
# averted)
CARE_LABELS = {"mal_itn": "bednet users", "mal_irs": "people under indoor spraying", "hiv_art": "people who stop ART*",
               "mal_cm": "malaria patients", "imm": "children unvaccinated",
               "hiv_pmtct": "HIV+ pregnant women", "tb_ds": "TB patients", "tb_dr": "drug-resistant TB patients"}
# L-40: the hero shows treatment and prevention separately; units are what the lost money would have paid for
TREATMENT_LINES = ["hiv_art", "hiv_pmtct", "tb_ds", "tb_dr", "mal_cm"]
PREVENTION_LINES = ["mal_itn", "mal_irs", "imm"]
ART_UNIT_NOTE = ("People who stop ART = the full-cost equivalents of the lost money (lost ART money ÷ full cost per "
                 "patient-year, after government replacement and continuity). The model treats each as a person who "
                 "actually stops treatment: they face the death risk and transmission of someone off ART. It is not "
                 "a count of patients at donor-supported sites, where support may be withdrawn thinly across more "
                 "people.")
TREATMENT_TIP = ("Treatment the lost money would have paid for, each year the cut lasts, under the selected scenario "
                 "and government response: people who stop ART, HIV+ pregnant women (PMTCT), TB patients and malaria "
                 "patients treated. " + ART_UNIT_NOTE)
PREVENTION_TIP = ("Prevention the lost money would have paid for, each year the cut lasts: people sleeping under a "
                  "bednet (person-years of net use), people protected by indoor spraying and children vaccinated.")
CARE_TIP = ("People who lose a service in each year the cut lasts, under the selected scenario and government "
            "response. Bednet users and vaccinated children are prevention; HIV and TB patients are treatment.")


def care_breakdown(L: pd.DataFrame) -> tuple:
    """(total, [(count, label), ...] largest first) of people losing a service each year (central run, after
    government replacement and continuity), the same services as the table's People Losing Service total (all lines
    except HIV prevention, whose unit is infections averted, and orphan support, which has no modelled effect)."""
    u = L["units_lost"].reindex(list(CARE_LABELS)).fillna(0).clip(lower=0)
    parts = sorted(((float(v), CARE_LABELS[k]) for k, v in u.items() if v >= 0.5), reverse=True)
    return float(u.sum()), parts         # the total counts every line, as the table does (I-15); the list skips < 0.5


def care_split(L: pd.DataFrame) -> dict:
    """{'treatment': (total, parts), 'prevention': (total, parts)}: care_breakdown split into treatment (ART, PMTCT, TB,
    malaria treatment) and prevention (bednets, spraying, vaccines), largest parts first (L-40).
    Feeds: the two People Losing ... Each Year numbers at the top of the Dashboard."""
    u = L["units_lost"].reindex(list(CARE_LABELS)).fillna(0).clip(lower=0)
    out = {}
    for k, lines in (("treatment", TREATMENT_LINES), ("prevention", PREVENTION_LINES)):
        parts = sorted(((float(u[l]), CARE_LABELS[l]) for l in lines if u[l] >= 0.5), reverse=True)
        out[k] = (float(u.reindex(lines).sum()), parts)
    return out


def response_kicker(fiscal_t) -> str:
    mode, theta = fiscal_t[0], fiscal_t[1]
    capped = len(fiscal_t) > 2 and fiscal_t[2]
    return {"none": NO_REPLACEMENT,
            "custom": f"Government Replaces {'Up to ' if capped else ''}{theta:.0%}",
            "max": "Government Replaces What Its Budget Allows",
            "gradual": "Gradual Budget Increase"}.get(mode, _resp_label(fiscal_t))
SPELLED = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}


def round_words(x: float) -> str:
    """NYT-style rounding for running text: 137,412 -> '137,000'; 8,433 -> '8,400'; 312 -> '310'; 7 -> 'seven'."""
    if x >= 1e6:
        return f"{x / 1e6:,.1f} million"
    if x >= 1e4:
        return f"{round(x, -3):,.0f}"
    if x >= 1e3:
        return f"{round(x, -2):,.0f}"
    if x >= 100:
        return f"{round(x, -1):,.0f}"
    return SPELLED.get(int(round(x)), f"{x:,.0f}")


def approx_words(x: float) -> str:
    """A model estimate for a headline, rounded to two significant figures (logic review L-48: no precise counts):
    126,146 -> '130,000'; 1,969,304 -> '2.0 million'; 8,433 -> '8,400'; 312 -> '310'."""
    if x >= 1e6:
        return f"{x / 1e6:,.1f} million"
    if x >= 100:
        return f"{round(x, -int(np.floor(np.log10(x))) + 1):,.0f}"
    return round_words(x)


def money_words(x: float) -> str:
    """Money for running text, NYT style: '$291 million', '$4.9 million', '$650,000', '$1.2 billion'."""
    a = abs(x)
    if a >= 1e9:
        return f"${x / 1e9:,.1f} billion"
    if a >= 1e7:
        return f"${x / 1e6:,.0f} million"
    if a >= 1e6:
        return f"${x / 1e6:,.1f} million"
    if a >= 1e4:
        return f"${round(x, -4 if a >= 1e5 else -3):,.0f}"
    return f"${x:,.0f}"


def story_lede(iso3: str, country_name: str, ctl: dict, sk: str) -> str:
    """HTML for the top of the Dashboard: kicker, headline, dek and three big numbers."""
    I = _inputs()
    e = html.escape
    path_lbl = "Sudden Cut" if ctl.get("shape", paths_ui.SUDDEN) == paths_ui.SUDDEN else title_case(ctl["shape"])
    kicker = (f"America First MOUs · Follows MOU Schedule · {response_kicker(ctl['fiscal_t'])}" if ctl["preset"] == MOU
              else f"Funding-Cut Scenario · {scenario_title(ctl['preset'], ctl.get('opts'))} · {path_lbl} · {response_kicker(ctl['fiscal_t'])}")
    # the controls sit in the scenario bar just below; the link jumps there (same cached run as Section 4)
    kick_html = (f"<div class='ed-kicker-row'><div class='ed-kicker'>{e(kicker)}</div>"
                 f"<a class='ed-jump' href='#change-scenario' target='_self'>Change Scenario ↓</a></div>")
    if iso3 not in I["ci"].index or iso3 not in set(I["lines"].iso3):
        head = f"{country_name} receives no recorded HIV, TB, malaria or vaccine aid"
        dek = "There is nothing for a donor cut to remove here; the spending and budget charts below still apply."
        return (f"<div class='ed-lede'>{kick_html}<div class='ed-headline'>{e(head)}</div>"
                f"<p class='ed-dek'>{e(dek)}</p></div>")
    res = run_ctl(iso3, sk, ctl)
    T, B, L = res["totals"], res["buckets"].set_index("bucket"), res["lines"].set_index("line")
    phrase = scenario_phrase(ctl["preset"], ctl.get("opts"))
    d5 = T["deaths_5y"]
    if T["gross"] <= 1e4:
        head = f"{phrase}, {country_name} would lose almost no aid for HIV, TB, malaria or vaccines"
        dek = "The services these programs pay for would carry on unchanged."
    elif d5 < 10 and T["replaced"] >= 0.99 * T["gross"]:
        head = f"{phrase}, {country_name} could keep services running if the government fills the gap"
        dek = (f"About {money_words(T['gross'])} a year of aid would be lost on average, and the government's added "
               "money covers it every year, so the model finds almost no extra deaths.")
    elif d5 < 10:
        head = f"{phrase}, {country_name} would lose {money_words(T['gross'])} a year in health aid"
        dek = f"The model finds almost no extra deaths: {country_name} records very few deaths from these diseases."
    else:
        # claims C1 (logic review): a model estimate, rounded, for 2026-2030, and only if nothing replaces the money
        if T["replaced"] > 0 and T["gross"] > 0:
            head = (f"{phrase}, the model estimates about {approx_words(d5)} more deaths in {country_name} in "
                    f"2026-2030, even if the government replaces {T['replaced'] / T['gross']:.0%} of the lost aid")
        else:
            head = (f"{phrase}, with nothing to replace the money, the model estimates about {approx_words(d5)} more "
                    f"deaths in {country_name} in 2026-2030")
        top = B["deaths_5y"].idxmax()
        share = B.loc[top, "deaths_5y"] / d5 if d5 > 0 else 0
        # claim C3: the direction is robust, the exact share is not (logic review L-01), so no percentage
        dek = f"{'Most' if share >= 0.5 else 'The largest share'} would come from {CAUSE_PHRASE[top]}. "
        if T["replaced"] > 0:
            dek += (f"The government could replace {money_words(T['replaced'])} of the {money_words(T['gross'])} "
                    "lost each year; the rest is lost to services.")
        else:
            dek += (f"About {money_words(T['gross'])} a year would be lost. In past aid declines (2001-2023), "
                    "governments on average did not increase their own health spending to compensate.")
    split = care_split(L)

    def brk(parts):
        """'452K HIV treatment* · 466K malaria patients' (top 2, then '+ others')."""
        return (" · ".join(f"{num(v)} {lbl}" for v, lbl in parts[:2]) + (" + others" if len(parts) > 2 else "")) or "none"
    tr, pv = split["treatment"], split["prevention"]
    tr_note = brk(tr[1]) + (" · *full-cost equivalents of the lost money" if any(l == CARE_LABELS["hiv_art"] for _, l in tr[1])
                            else "")
    nums = [
        (money(T["gross"]), "Health Aid Lost Each Year",
         f"{T['gross'] / T['base']:.0%} of aid for these four diseases" if T["base"] else "", False, ""),
        (num(tr[0]) if tr[0] >= 1 else "0", "Treatment Lost Each Year", tr_note, False, TREATMENT_TIP),
        (num(pv[0]) if pv[0] >= 1 else "0", "Prevention Lost Each Year", brk(pv[1]), False, PREVENTION_TIP),
        (num(d5), f"Extra Deaths, {FIRST_YEAR}-{FIRST_YEAR + 4}",
         f"range {rng(T['deaths_5y_lo'], T['deaths_5y_hi'])}"
         + (f" · +{num(res['committed']['after_2030'])} more in 2031-2035 (assumption-driven)"
            if res["committed"]["after_2030"] >= 0.5
            else ""), True, after_2030_help(res["committed"])),
    ]
    big = "".join(f"<div class='ed-bignum' title='{e(tip, quote=True)}'><div class='v{' hl' if hl else ''}'>{e(v)}</div>"
                  f"<div class='l'>{e(lbl)}</div><div class='n'>{e(note)}</div></div>" for v, lbl, note, hl, tip in nums)
    return (f"<div class='ed-lede'>{kick_html}<div class='ed-headline'>{e(head)}</div>"
            f"<p class='ed-dek'>{e(dek)}</p></div><div class='ed-bignums'>{big}</div>").replace("$", "&#36;")


def render_model_section(iso3: str, country_name: str, imf: dict | None, ctl: dict, sk: str):
    I = _inputs()
    ci = I["ci"]
    th.section_header("monitor_heart", f"How Aid Cuts Translate into Coverage and Lives in {country_name}", help=INTRO)
    st.caption(_esc(f"{scenario_title(ctl['preset'], ctl.get('opts'))} · {_resp_label(ctl['fiscal_t'])}. Change the scenario at the top "
                    "of the page."))
    if iso3 not in ci.index or iso3 not in set(I["lines"].iso3):
        st.info(f"{country_name} has no recorded HIV, TB, malaria or vaccine aid in 2021-2023, so there is nothing to "
                "model for this country. See the All Countries page for the other countries.")
    else:
        _country_results(iso3, country_name, ctl, sk, imf or {})


def _country_results(iso3, country_name, ctl, sk, imf):
    preset, fiscal_t, ptab, ptab_json, mode = ctl["preset"], ctl["fiscal_t"], ctl["ptab"], ctl["ptab_json"], ctl["mode"]
    trend = ctl["trend"]
    res = run_ctl(iso3, sk, ctl)
    # the same funding path with no government money, for "replacement averts N deaths"
    res0 = run_ctl(iso3, sk, ctl, fiscal_t=scn.DEFAULT_FISCAL, gov_add=None) if mode != "none" else res
    T, B, L = res["totals"], res["buckets"].set_index("bucket"), res["lines"]

    if T["gross"] <= 0 and T["base"] > 0:
        st.success(_esc(f"Under '{preset}' {country_name} loses no HIV, TB, malaria or vaccine aid"
                        + (f" (aid rises by {money(T['gains'])} a year; gains aren't modelled)." if T.get("gains", 0) >= 0.5
                           else ".")))

    show = L[(L["base_usd"] > 0) | (L["net_loss_usd"] != 0)].copy()
    rows = _service_rows(show)
    cov_fig = _coverage_fig(rows)
    path_fig = _path_fig(res)
    cards = _per_million_cards(iso3, ptab_json, ctl["trend"], country_name)
    items = _headline_items(res, ptab, deaths_basis_text(preset, ctl.get("cut_path"), country_name))

    # ------------------------------ headline ------------------------------ #
    if ctl["cmp"]:
        _comparison(iso3, country_name, ctl, res, items)
    else:
        st.subheader("The Numbers")
        _stat_grid(items, 3)
    if mode != "none" and T["replaced"] > 0:
        saved = res0["totals"]["deaths_5y"] - T["deaths_5y"]
        st.markdown(_esc(f"Government replacement of {money(T['replaced'])} a year averts about **{num(saved)} deaths "
                         f"over 5 years** compared with no government replacement "
                         f"({money(T['replaced'] * 5 / max(saved, 1))} per death "
                         "averted)."))
    if SHOW_BRIEF:
        st.download_button(
            "Download Country Brief", icon=":material/download:",
            data=_brief_html(country_name, preset, _resp_label(fiscal_t), items, cards,
                             [cov_fig, path_fig], ctl.get("opts")).encode("utf-8"),
            file_name=f"{country_name.replace(' ', '_')}_funding_cut_brief.html", mime="text/html", key="m_brief",
            help="A one-page HTML summary of this scenario. Open it in a browser and print to PDF.")

    # ------------------------------ per $1M ------------------------------ #
    st.subheader(_esc(CARDS_TITLE),
                 help="Each card runs the full model for a US$1M-a-year cut to that disease, spread across all its "
                      "services (including HIV testing and care) in proportion to current aid, with no government "
                      "replacement and a sudden cut. People and coverage are for the main service; deaths are for the "
                      "whole disease over 2026-2030, including TB spread, malaria rebound and deaths from new HIV "
                      "infections. The death-rate setting and model parameters follow your choices above.")
    st.markdown(_cards_html(cards), unsafe_allow_html=True)

    # ------------------------------ where the money is lost ------------------------------ #
    st.subheader("Where the Money Is Lost")
    cells = res["cells"]
    cl = cells[cells["loss"] > 0]
    if cl.empty:
        st.info("No aid is cut in this scenario.")
    else:
        n_rows = max(int((B["gross_loss_usd"] > 0).sum()), len(_who_cut_bars(cl)))   # same height for both
        with st.container(border=True, key="money_lost"):
            a, b = st.columns(2, gap="medium")
            with a:
                chart(_loss_by_bucket_fig(B, T["replaced"] > 0, n_rows))
            with b:
                chart(_who_cut_fig(cl, n_rows))
        st.markdown(th.source_html(SRC_MODEL, "Donors are who originally paid; the label after the dot is the "
                                              "channel the money went through."), unsafe_allow_html=True)

    # ------------------------------ service table ------------------------------ #
    notes = []
    if show["capped"].any():
        notes.append("Where the aid lost would pay for more people than are covered today, the loss is capped at "
                     "current coverage. Where donor aid buys more than the donor-funded pool (people covered x the "
                     "external share of the country's spending on the disease), the loss is that pool x the share of "
                     "money lost.")
    notes += [f"{f[0].upper() + f[1:]}." for f in res["flags"]]
    notes.append("HIV prevention turns money into infections averted; deaths from those infections are counted in the "
                 "year they happen (few before 2031). Program money with no "
                 "reported purpose is split by purpose with the country's Global Fund grant mix (treatment, "
                 "prevention, testing, systems, programme management); only the treatment share counts as people on "
                 "treatment; "
                 + systems_note(ptab) + " HIV Testing & Care has no patients of its own: " + care_ct_note()
                 + " Bednets and spraying have their own coverage; together they set vector-control coverage. "
                 "Deaths ranges: " + RANGE_LABEL + ". " + RANGE_TIP)
    st.subheader("What Each Service Loses", help=" ".join(notes))
    st.html(_service_table_html(rows, country_name, T, {b: float(B.loc[b, "gains_usd"]) for b in hm.BUCKETS}))
    ovc = show[show["line"] == "hiv_ovc"]
    st.caption(_esc("Other Aid is money the model does not link to deaths: support for orphans and vulnerable children"
                    + (f" ({money(ovc['net_loss_usd'].sum())} a year lost)" if len(ovc) else "")
                    + f" and the {1 - float(ptab.loc['hss_service_share', 'central']):.0%} of lost systems money (labs, "
                    "staff, monitoring, supply chain) that does not cut services. With it, the totals match Aid at Risk and Net Aid Lost "
                    "Services above. The deaths range is for the total, so it is narrower than adding the rows' ranges."))
    if cov_fig is not None:
        chart(cov_fig, source="Model estimates; coverage today: UNAIDS/WHO 2025 (HIV), WHO 2024 (TB), Malaria Atlas "
                              "Project 2025 (malaria treatment, bednets, spraying; source shown on each bar), WUENIC "
                              "(DTP3).")

    # ------------------------------ dose response + path ------------------------------ #
    st.subheader("How the Damage Scales",
                 help="Left: a uniform cut across all donors to one bucket, with the chosen government response; it "
                      "flattens once everyone whose service donors pay for has lost it, and bends where replacement runs "
                      "out of fiscal space. Right: deaths after losing HIV treatment rise from about 1% to 5% a year, "
                      "unvaccinated birth cohorts add up, and nets already hanging protect for about a year.")
    bsel = st.radio("Bucket (Left Chart Only)", hm.BUCKETS, horizontal=True, key="m_dose_b",
                    help="Picks the bucket for the left chart; the right chart always shows all four buckets.")
    dr = _dose(iso3, bsel, fiscal_t, ptab_json, trend)
    # the dashed "this scenario, scaled" path is not drawn for an MOU schedule, which is never rescaled
    path = None if preset == MOU else _scenario_path(iso3, sk, bsel, fiscal_t, ptab_json, trend, ctl.get("cut_path"),
                                                     ctl.get("gov_add"))
    base_b = B.loc[bsel, "base_usd"]
    cur_cut = B.loc[bsel, "gross_loss_usd"] / base_b if base_b > 0 else 0
    if base_b > 0:
        at10 = float(np.interp(0.10, dr["cut"], dr["deaths_5y"]))
        st.markdown(f"An even 10% cut to {BUCKET_WORD[bsel]} aid adds about **{num(at10)}** extra deaths over 5 years.")
    else:
        st.markdown(f"{country_name} receives no {BUCKET_WORD[bsel]} aid in the model, so cutting it changes nothing.")
    d1, d2 = st.columns(2)
    with d1:
        chart(_dose_fig(dr, bsel, cur_cut, B.loc[bsel], path))
    with d2:
        chart(path_fig, labels=True)
    if preset == MOU:
        st.caption("The scenario-path line isn't shown for MOU schedules, which vary year by year rather than scaling "
                   "one cut.")
    st.markdown(th.source_html(SRC_MODEL, "The solid line cuts every donor and service by the same share. The dashed "
                               "line is this scenario's actual cut, which can run higher or lower because it falls on "
                               "specific services (for example, US money is concentrated in HIV treatment, where each "
                               "dollar saves more lives). The shaded band is the " + RANGE_LABEL + " for the even cut. " + RANGE_TIP),
                unsafe_allow_html=True)

    # ------------------------------ fiscal space ------------------------------ #
    _fiscal_panel(res, country_name, imf, fiscal_t)
    return res


# --------------------------------------------------------------------------- #
# Headline, comparison, cards
# --------------------------------------------------------------------------- #
AFTER_2030_PARTS = {"hiv_art": "people still off HIV treatment", "hiv_infections": "new HIV infections",
                    "imm": "children who missed vaccines", "tb": "TB spread by untreated patients"}


def after_2030_help(C) -> str:
    """Tooltip: what the deaths in 2031-2035 set in motion by the 2026-2030 losses are made of (central estimates)."""
    parts = C.get("after_parts", {})
    bits = [f"{AFTER_2030_PARTS[k]} {num(v)}" for k, v in sorted(parts.items(), key=lambda kv: -kv[1])
            if k in AFTER_2030_PARTS and v >= 0.5]
    return (REENGAGE_TIP + " Deaths in 2031-2035 caused by the 2026-2030 losses, with funding back from 2031 (people "
            "off HIV treatment return gradually)"
            + (": " + "; ".join(bits) if bits else "") + ". Range: " + RANGE_LABEL + ". " + RANGE_TIP)


REENGAGE_TIP = ("Assumption-driven: most of these deaths depend on how fast people who stopped HIV treatment return "
                "once funding is back in 2031 (art_reengage, an assumption with no published source; central 50% a "
                "year).")


def reengage_range_text(C) -> str:
    """'20K to 67K if 75% to 25% of people off HIV treatment return each year after 2030': deaths in 2031-2035 across
    the art_reengage range, everything else central (L-33). Empty if the run has no such range."""
    if "after_2030_reengage" not in C:
        return ""
    mn, mx = C["after_2030_reengage"]
    lo_v, hi_v = C["reengage_values"]
    return f"{rng(mn, mx)} if {hi_v:.0%} to {lo_v:.0%} of people off HIV treatment return each year after 2030"


HSS_LINES = list(hm.HSS.values())


def net_aid_note(res, ptab) -> tuple:
    """(sub-line, tooltip) for Net Aid Lost. The sub-line shows the health-systems money inside it (yearly HSS aid lost,
    after replacement in proportion) and is hidden when that is 0; the share counted as lost services and its range
    come from hss_service_share in the parameters (model_params.csv unless edited in the app)."""
    k, lo, hi = (float(ptab.loc["hss_service_share", c]) for c in ("central", "low", "high"))
    cells, T = res["cells"], res["totals"]
    hss = float(np.clip(cells.loc[cells["line"].isin(HSS_LINES), "loss"].sum(), 0, None)) if len(cells) else 0.0
    hss_net = hss * (T["net"] / T["gross"]) if T["gross"] > 0 else 0.0
    sub = (f"incl. {money(hss_net)} health-systems money, {k:.0%} counted as lost services (assumption)"
           if hss_net >= 0.5 else "per year")
    tip = ("Aid lost minus what the government replaces, per year. Health-systems money (labs, staff, data systems, "
           "supply chain) is above-site money that the cost per patient already includes, so it is not converted "
           f"into patients again: {k:.0%} of it is counted as lost services"
           + (f"; the uncertainty runs vary this from {lo:.0%} to {hi:.0%}" if hi > lo else
              " (a structural assumption held constant in the uncertainty runs)") + " (logic review L-05).")
    return sub, tip


def systems_note(ptab) -> str:
    """How systems money enters the model (logic review L-05, Batch 3+4); value from hss_service_share."""
    k = float(ptab.loc["hss_service_share", "central"])
    return (f"{k:.0%} of lost systems money (labs, staff, monitoring, supply chain) is counted as lost services: it is "
            "above-site money that the cost per patient already includes (assumption, logic review L-05).")


def deaths_basis_text(preset: str, cut_path, country_name: str = "") -> str:
    """What the 5-year deaths assume about the funding path (I-19)."""
    if preset == MOU:
        return f"Follows {country_name}'s MOU schedule, 2026-2030."
    if cut_path is not None:
        return "Follows the chosen phase-out path, 2026-2030."
    return "Assumes the cut is sustained for five years."


def _headline_items(res, ptab=None, basis: str = "Assumes the cut is sustained for five years.") -> list:
    ptab = _default_params() if ptab is None else ptab
    T, B = res["totals"], res["buckets"].set_index("bucket")
    items = [
        ("Aid at Risk (per Year)", money(T["gross"]),
         f"{T['gross'] / T['base']:.0%} of {money(T['base'])} for these four buckets" if T["base"] else None,
         "Yearly HIV, TB, malaria and vaccine aid removed by the scenario, out of the 2021-2023 average."),
        ("Replaced by Government", money(T["replaced"]),
         f"{T['replaced'] / T['gross']:.0%} of the loss" if T["gross"] > 0 else None,
         "Set by the government response in the sidebar, limited by fiscal space."),
        ("Net Aid Lost", money(T["net"]), *net_aid_note(res, ptab)),
        ("Further Deaths, 2031-2035 (Assumption-Driven)", num(res["committed"]["after_2030"]),
         "range " + rng(res["committed"]["after_2030_lo"], res["committed"]["after_2030_hi"]) + " · "
         + reengage_range_text(res["committed"]),
         after_2030_help(res["committed"])),
        ("Extra Deaths Over 5 Years", num(T["deaths_5y"]), "range " + rng(T["deaths_5y_lo"], T["deaths_5y_hi"]),
         f"{basis} Range: {RANGE_LABEL}. {RANGE_TIP}"),
        ("New HIV Infections, 5 Years", num(B.loc["HIV", "infections_5y"]),
         "range " + rng(B.loc["HIV", "infections_5y_lo"], B.loc["HIV", "infections_5y_hi"]),
         "The hypothetical best case (triage) refills treatment and vaccines first and HIV prevention last, so new infections can stay "
         "high even when deaths fall. Range: " + RANGE_LABEL + ". " + RANGE_TIP),
    ]
    return [(title_case(lbl), val, title_case(sub), hlp) for lbl, val, sub, hlp in items]


def _comparison(iso3, country_name, ctl, res_a, items_a):
    c = ctl["cmp"]
    ci = _inputs()["ci"]
    sk_b = scn.scenario_key(scn.build_scenario(c["preset"], c["opts"], ci))
    # an MOU schedule is never rescaled by Scenario A's funding path
    res_b = _run(iso3, sk_b, c["fiscal_t"], ctl["ptab_json"], ctl["trend"],
                 cut_path=None if c["preset"] == MOU else ctl.get("cut_path"))
    st.subheader("Scenario A vs Scenario B")
    a, b = st.columns(2, gap="large")
    for col, tag, preset, opts, fiscal_t, items in ((a, "A", ctl["preset"], ctl.get("opts"), ctl["fiscal_t"], items_a),
                                                    (b, "B", c["preset"], c["opts"], c["fiscal_t"],
                                                     _headline_items(res_b, ctl["ptab"], deaths_basis_text(
                                                         c["preset"], None if c["preset"] == MOU else ctl.get("cut_path"),
                                                         country_name)))):
        with col:
            st.markdown(_esc(f"**Scenario {tag}:** {scenario_title(preset, opts)} · {_resp_label(fiscal_t)}"))
            _stat_grid(items, 2)
    da, db = res_a["totals"]["deaths_5y"], res_b["totals"]["deaths_5y"]
    diff = da - db
    st.markdown(f"Scenario B {'averts' if diff >= 0 else 'adds'} about **{num(abs(diff))}** extra deaths over 5 years "
                f"in {country_name} compared with Scenario A.")
    BA, BB = res_a["buckets"].set_index("bucket"), res_b["buckets"].set_index("bucket")
    fig = go.Figure()
    for tag, Bx, col in (("Scenario A", BA, SCEN_A), ("Scenario B", BB, SCEN_B)):
        fig.add_trace(go.Bar(x=hm.BUCKETS, y=[Bx.loc[k, "deaths_5y"] for k in hm.BUCKETS], name=tag,
                             marker=dict(color=col), text=[num(Bx.loc[k, "deaths_5y"]) for k in hm.BUCKETS], textposition="outside",
                             cliponaxis=False, hovertemplate=f"{tag}<br>%{{x}}: %{{y:,.0f}} extra deaths<extra></extra>"))
    fig.update_layout(barmode="group", bargap=0.3)
    _layout(fig, h=340, title=_title(th.title_sub("Extra Deaths by Disease", "Scenario A vs. B, over 5 years")),
            legend=dict(orientation="h", y=-0.12, x=0, yanchor="top"),
            yaxis=dict(title="extra deaths, 5 years", rangemode="tozero"))
    chart(fig, source=SRC_MODEL)


CARD_FOOT_TIP = ("Total aid lost over 5 years ($5M) divided by extra deaths over the same 5 years; this equals $1M "
                 "divided by the average extra deaths per year.")
CARDS_TITLE = "What Every US$1 Million Cut Does, by Disease"
CARD_MAIN = {"HIV": "HIV treatment (ART)", "TB": "TB treatment", "Malaria": "bednets", "Immunization": "routine vaccines"}
NO_DEATHS_REASON = {"Malaria": " (very low transmission)"}


@st.cache_data(show_spinner=False, max_entries=64)
def _card_runs(iso3: str, ptab_json: str, trend: bool) -> dict:
    """Full-model US$1M-a-year cut per disease (audit I-04), cached by country, parameters and death-rate setting."""
    ptab = pd.read_json(io.StringIO(ptab_json), orient="split")
    return {b: hm.per_million_card(iso3, b, _inputs(), ptab, trend) for b in hm.BUCKETS}


def _per_million_cards(iso3: str, ptab_json: str, trend: bool, country_name: str = "") -> list:
    """The four cards: people losing and coverage drop for the disease's main service, extra deaths for the whole
    disease, from a US$1M-a-year loss spread over all the disease's services in proportion to current aid."""
    runs = _card_runs(iso3, ptab_json, trend)
    out = []
    for b in hm.BUCKETS:
        word = BUCKET_WORD[b]
        c = runs[b]
        base = {"bucket": b, "color": BUCKET_COLORS[b], "service": b, "foot_tip": ""}
        if c is None:                                   # no aid for this disease in the country
            out.append({**base, "unit": "", "people": "", "people_n": None, "cov_n": None, "coverage": "n/a",
                        "deaths": "", "no_deaths": f"No {word} aid in {country_name}", "foot": ""})
            continue
        d = c["deaths_5y"]
        no_deaths = not (d >= 0.5)
        spread = f"Spread across all {word} services in proportion to current aid"
        if c["scaled"]:
            spread += f" ({money(c['aid_usd'])} a year in total; results scaled to $1M)"
        out.append({**base, "unit": f"main service: {CARD_MAIN[b]} ({c['unit_label']})",
                    "people": f"{num(c['people'])} {c['unit_label']} lose the service",
                    "people_n": f"{c['people']:,.0f}",
                    "cov_n": None if not np.isfinite(c["cov_drop_pp"]) else f"{c['cov_drop_pp']:,.1f}",
                    "coverage": "n/a" if not np.isfinite(c["cov_drop_pp"]) else f"{c['cov_drop_pp']:,.1f} Percentage Points",
                    "deaths": f"{d:,.0f}",
                    "no_deaths": (f"No {word} deaths modelled in {country_name}{NO_DEATHS_REASON.get(b, '')}"
                                  if no_deaths else ""),
                    "foot": spread + ("" if no_deaths else f" · Model estimate: about {money(5e6 / d)} of aid lost per life lost "
                                                         "(based on US$1M a year for 5 years)"),
                    "foot_tip": "" if no_deaths else CARD_FOOT_TIP})
    return out


def _card_html(c) -> str:
    """One card: bucket, service on one line, unit as a grey second line, then three big numbers."""
    e = html.escape
    if c.get("people_n") is None:                      # no aid for this disease in the country
        return (f"<div class='ed-card' style='border-top-color:{c['color']}'><div class='t'>{e(c['bucket'])}</div>"
                f"<div class='none'>{e(c['no_deaths'])}</div></div>").replace("$", "&#36;")
    big = (f"<div class='big'>{e(c['people_n'])}</div><div class='lbl'>People Losing the Main Service</div>")
    big += (f"<div class='big'>{e(c['cov_n'])}</div><div class='lbl'>Coverage Drop (Percentage Points)</div>"
            if c["cov_n"] is not None else "")
    big += (f"<div class='none'>{e(c['no_deaths'])}</div>" if c["no_deaths"] else
            f"<div class='big'>{e(c['deaths'])}</div><div class='lbl'>Extra Deaths Over 5 Years</div>")
    return (f"<div class='ed-card' style='border-top-color:{c['color']}'>"
            f"<div class='t'>{e(c['bucket'])}</div>"
            f"<div class='s'>{e(c['unit'])}</div>{big}"
            f"<div class='foot' title='{e(c.get('foot_tip', ''), quote=True)}'>{e(c['foot'])}</div></div>"
            ).replace("$", "&#36;")


def _cards_html(cards) -> str:
    """All four cards in one grid row, so they share one height."""
    return "<div class='ed-cards'>" + "".join(_card_html(c) for c in cards) + "</div>"


# --------------------------------------------------------------------------- #
# Charts and tables
# --------------------------------------------------------------------------- #
BAR_PX, ROW_PX, MIN_BAR_FRAC = 18, 32, 2 / 380       # bar thickness, row pitch, and 2px of a ~380px-wide plot


def _loss_layout(n_rows: int):
    """Shared height and bar gap for the two 'Where the Money Is Lost' charts, so their baselines line up."""
    h = max(240, 90 + ROW_PX * n_rows)
    gap = float(np.clip(1 - BAR_PX / max((h - 90) / max(n_rows, 1), BAR_PX), 0.15, 0.85))
    return h, gap


def _visible(vals, xmax):
    """Tiny values drawn at least 2px wide (labels and hover keep the real number)."""
    return [max(v, xmax * MIN_BAR_FRAC) if v > 0 else 0 for v in vals]


def _loss_by_bucket_fig(B: pd.DataFrame, any_replaced: bool = False, n_rows: int | None = None):
    """Aid lost per disease in the disease color; the part the government replaces in the same color at 40%."""
    bk = [b for b in hm.BUCKETS if B.loc[b, "gross_loss_usd"] > 0][::-1]
    rep = [max(B.loc[b, "replaced_usd"], 0.0) for b in bk]
    lost = [max(B.loc[b, "gross_loss_usd"] - B.loc[b, "replaced_usd"], 0.0) for b in bk]
    tot = [r + l for r, l in zip(rep, lost)]
    xmax = max(tot) * 1.3
    h, gap = _loss_layout(n_rows or len(bk))
    fig = go.Figure()
    for name, vals, alpha in (("Lost to services", lost, 1.0), ("Replaced by government", rep, REPLACED_ALPHA)):
        fig.add_trace(go.Bar(y=bk, x=_visible(vals, xmax) if alpha == 1.0 else vals, name=name, orientation="h",
                             marker=dict(color=[th.tint(BUCKET_COLORS[b], alpha) for b in bk]),
                             customdata=[money(v) for v in vals], showlegend=False,
                             hovertemplate=f"%{{y}} · {name}: %{{customdata}} a year<extra></extra>"))
    fig.add_trace(go.Scatter(y=bk, x=[max(t, xmax * MIN_BAR_FRAC) for t in tot], mode="text",
                             text=["  " + money(t) for t in tot], textposition="middle right",
                             textfont=dict(color=INK), showlegend=False, hoverinfo="skip", cliponaxis=False))
    fig.update_layout(barmode="stack", bargap=gap)
    _layout(fig, h=h, title=_title(th.title_sub("Aid Lost per Year", "Lighter = replaced by government")
                                   if any_replaced else "Aid Lost per Year"),
            margin=dict(l=10, r=20, t=50, b=10), xaxis=dict(range=[0, xmax]))
    return fig


SRC_SHORT = {"United States": "US", "United Kingdom": "UK", "Gates Foundation": "Gates"}
CHAN_SHORT = {"Bilateral agency": "Bilateral", "Gates direct": "Direct", "Development banks": "Dev. Banks"}
MAX_WHO_CUT_BARS = 12


def _who_cut_bars(cl: pd.DataFrame) -> pd.Series:
    d = cl.groupby(["src_grp", "chan_grp"])["loss"].sum().sort_values(ascending=False)
    d = d[d > 0]
    if len(d) > MAX_WHO_CUT_BARS:                   # keep the chart readable: the rest as one grey bar
        d = pd.concat([d.iloc[:MAX_WHO_CUT_BARS - 1],
                       pd.Series([d.iloc[MAX_WHO_CUT_BARS - 1:].sum()], index=[("All other", "")])])
    return d


def _who_cut_fig(cl: pd.DataFrame, n_rows: int | None = None):
    """One bar per donor x channel ('US · Bilateral'), in the funder's color, largest at the top."""
    d = _who_cut_bars(cl)
    labels = [f"{SRC_SHORT.get(s, s)} · {CHAN_SHORT.get(c, c)}" if c else s for s, c in d.index]
    colors = [th.funder_color(s) if c else th.OTHER for s, c in d.index]
    labels, vals, colors = labels[::-1], list(d.values[::-1]), colors[::-1]
    xmax = float(d.max()) * 1.3
    h, gap = _loss_layout(n_rows or len(d))
    fig = go.Figure(go.Bar(y=labels, x=_visible(vals, xmax), orientation="h", marker=dict(color=colors),
                           text=[money(v) for v in vals], textposition="outside", cliponaxis=False,
                           textfont=dict(color=INK), hovertemplate="<b>%{y}</b>: %{text} a year<extra></extra>"))
    fig.update_layout(bargap=gap)
    _layout(fig, h=h, title=_title("Who Cut the Money"), margin=dict(l=10, r=20, t=50, b=10),
            xaxis=dict(range=[0, xmax]))
    return fig




LINE_SHORT = {"hiv_art": ("HIV Treatment", "antiretroviral therapy (ART)"),
              "hiv_care_ct": ("HIV Testing & Care", "counselling, testing, care & support"),
              "hiv_pmtct": ("Mother-to-Child Transmission", "prevention (PMTCT)"),
              "hiv_prev": ("HIV Prevention", "PrEP, VMMC, condoms, key populations"),
              "hiv_ovc": ("Orphans & Vulnerable Children", "support"),
              "tb_ds": ("TB Treatment", "case finding & treatment"),
              "tb_dr": ("Drug-Resistant TB", "second-line treatment"),
              "mal_itn": ("Bednets", "insecticide-treated nets & other vector control"),
              "mal_irs": ("Indoor Spraying", "indoor residual spraying"),
              "mal_cm": ("Malaria Treatment", "testing & treatment"),
              "imm": ("Routine Immunization", "vaccines + delivery; deaths exclude DTP, polio and BCG (no per-child evidence), a conservative floor")}


LINE_ORDER = ["hiv_art", "hiv_care_ct", "hiv_pmtct", "hiv_prev", "hiv_ovc", "tb_ds", "tb_dr", "mal_itn", "mal_irs",
              "mal_cm", "imm"]
COST_UNIT = {"hiv_pmtct": "per woman per year, including her ART"}


def care_ct_note() -> str:
    """How HIV testing and care money enters the model (audit I-09); values from hss_kappa in model_params.csv."""
    k = _default_params().loc["hss_kappa"]
    return (f"{float(k['central']):.0%} of lost testing and care money is counted as lost ART care (assumption; range "
            f"{float(k['low']):.0%}-{float(k['high']):.0%}).")


def care_ct_tip() -> str:
    return ("HIV testing, counselling, care and support have no patients of their own in the model. Cutting them means "
            "fewer people diagnosed and kept in care, so fewer on ART: " + care_ct_note()
            + " Those people and deaths are counted in the HIV Treatment row.")


def _service_rows(show: pd.DataFrame) -> pd.DataFrame:
    """Lines as shown to readers: support for orphans and vulnerable children dropped (it has no modelled effect on
    deaths). Bednets and indoor spraying are separate rows, each with its own coverage (MAP ITN use and MAP household
    IRS coverage). Adds the short name, the cost text, the coverage source and whether coverage can be shown (it can't
    when nobody is in need, e.g. malaria treatment in Iraq: the drop would be 0 / 0)."""
    d = show[show["line"] != "hiv_ovc"].copy()
    d["cost_big"] = [("–" if r.line in hm.LINKED else money(r.unit_cost)) for r in d.itertuples()]
    d["cost_unit"] = [("" if r.line in hm.LINKED else COST_UNIT.get(r.line, f"per {hm.UNIT_SINGULAR[r.line]}"))
                      for r in d.itertuples()]
    if "cov_source" not in d:
        d["cov_source"] = ""
    d["cov_source"] = d["cov_source"].fillna("")
    d["name"] = d["line"].map(lambda l: LINE_SHORT.get(l, (l, ""))[0])
    d["detail"] = d["line"].map(lambda l: LINE_SHORT.get(l, ("", ""))[1])
    d["cov_ok"] = (d["need"] > 0) & d["cov0"].notna() & np.isfinite(d["cov_drop_pp"].astype(float))
    d["after"] = np.where(d["cov_ok"], (d["cov0"] - d["cov_drop_pp"].fillna(0) / 100).clip(0, 1), np.nan)
    d["drop"] = np.where(d["cov_ok"], (d["cov0"] - d["after"]) * 100, np.nan)
    order = {b: i for i, b in enumerate(hm.BUCKETS)}
    lo = {l: i for i, l in enumerate(LINE_ORDER)}
    return (d.assign(_o=d["bucket"].map(order), _l=d["line"].map(lambda l: lo.get(l, 99)))
            .sort_values(["_o", "_l"], kind="stable").drop(columns=["_o", "_l"]))


def _pts(v: float) -> str:
    """Coverage change as text, from a drop in points (positive = coverage falls): '−6.6 pts', '−12 pts'; a negative
    drop is a rise, '+6.6 pts' (never '−-'). One decimal below 10 points, whole points above."""
    sign = "−" if v > 0 else "+" if v < 0 else ""
    a = abs(v)
    return f"{sign}{a:.1f} pts" if a < 10 else f"{sign}{a:.0f} pts"


def gains_note(bucket: str, gain: float) -> str:
    """I-15: one note per disease whose aid rises."""
    return f"Aid to {BUCKET_WORD[bucket]} rises by {money(gain)} in this scenario; gains aren't modelled."


DISEASE_WORD = {"HIV": "HIV", "TB": "TB", "Malaria": "malaria", "Immunization": "vaccine-preventable"}


def cov_pair(c0: float, c1: float) -> str:
    """'66% → 65%', or one decimal when coverage is below 1% ('0.2% → 0.0%')."""
    f = "{:.1%}" if min(c0, c1) < 0.01 else "{:.0%}"
    return f"{f.format(c0)} → {f.format(c1)}"


def _service_table_html(rows: pd.DataFrame, country_name: str = "", T: dict | None = None,
                        gains: dict | None = None) -> str:
    """'What Each Service Loses': NYT-style HTML table, grouped by disease, with a Total row. With the run's totals T,
    an Other Aid row (orphan support and systems money not modelled as services) makes the money columns add up to
    the headline figures, and the Total deaths range is the run's own range across parameter values."""
    e = html.escape
    grey = lambda t: f"<span class='sub'>{t}</span>"
    nm = f"<span class='nm'>{e('Not Modelled')}</span>"
    head = [("Service", ""), ("Donor Aid Now", "per year"), ("Aid Lost", "per year, after government replacement"),
            ("Cost per Person", ""), ("People Losing Service, per Year", ""), ("Coverage", ""),
            ("Extra Deaths, 5 Years Total", "")]
    th_html = "".join(f"<th>{e(h)}" + (f"<br>{grey(e(s))}" if s else "") + "</th>" for h, s in head)
    body, prev = [], None
    for r in rows.itertuples():
        col = BUCKET_COLORS[r.bucket]
        if prev is not None and r.bucket != prev:
            body += _gain_rows(prev, gains)
            body.append("<tr class='gap'><td colspan='7'></td></tr>")
        prev = r.bucket
        service = (f"<td class='svc' style='border-left:3px solid {col}'><span class='dot' style='background:{col}'>"
                   f"</span><b>{e(r.name)}</b><br>{grey(e(r.detail))}</td>")
        dash = f"<span class='nm' title='{e(care_ct_tip(), quote=True)}'>–</span>"
        if r.line in hm.LINKED:                        # HIV testing & care: works through ART (I-09)
            cells = [money(r.base_usd), money(r.net_loss_usd), "<span class='big'>–</span>", dash, dash,
                     f"<span class='nm' title='{e(care_ct_tip(), quote=True)}'>In HIV<br>Treatment</span>"]
            body.append("<tr>" + service + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
            continue
        if r.cov_ok:
            src = f"<br>{grey(e('(' + r.cov_source + ')'))}" if r.cov_source else ""
            cov = f"{cov_pair(r.cov0, r.after)}{src}<br><span class='drop'>{_pts(r.drop)}</span>"
        elif r.line == "hiv_prev":
            cov = "<span class='nm'>No Single<br>Target Group</span>"
        else:
            cov = nm
        if r.line == "hiv_prev" and not (r.deaths_5y >= 0.5):   # infections averted, few deaths before 2031
            tip = ("Prevention averts new HIV infections; their deaths mostly fall after 2030 (see Further Deaths, "
                   "2031-2035) and in the New HIV Infections card.")
            deaths = f"<span class='nm' title='{e(tip, quote=True)}'>See New<br>Infections</span>"
        elif not (r.deaths_5y_hi > 0) and r.net_loss_usd > 0:
            tip = (f"{country_name} records almost no {DISEASE_WORD[r.bucket]} deaths, so cutting this aid adds "
                   "almost none.")
            deaths = f"<b title='{e(tip, quote=True)}'>~0</b>"
        else:
            deaths = f"<b>{num(r.deaths_5y)}</b><br>{grey(rng(r.deaths_5y_lo, r.deaths_5y_hi))}"
        people = num(r.units_lost) if r.units_lost > 0 or r.cov_ok else nm
        if r.units_lost > 0:                    # 5-year total under the yearly number (ART: mostly the same people)
            five = getattr(r, "units_lost_5y", np.nan)
            people += "<br>" + grey(f"<span title='{e(ART_UNIT_NOTE, quote=True)}'>people who stop ART: full-cost "
                                    "equivalents of the lost money; mostly the same people each year</span>"
                                    if r.line == "hiv_art" else
                                    f"{num(five)} over 5 years" if five == five else "")
        cells = [money(r.base_usd), money(r.net_loss_usd),
                 f"<span class='big'>{e(r.cost_big)}</span><br>"
                 f"{grey(e(r.cost_unit).replace('per infection averted', 'per infection<br>averted'))}", people, cov, deaths]
        body.append("<tr>" + service + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
    if prev is not None:
        body += _gain_rows(prev, gains)
    # Other Aid: money with no modelled effect on deaths, so the money columns add up to the headline figures
    base_tot, net_tot = rows["base_usd"].sum(), rows["net_loss_usd"].sum()
    d_lo, d_hi = rows["deaths_5y_lo"].sum(), rows["deaths_5y_hi"].sum()
    if T is not None:
        o_base, o_net = T["base"] - base_tot, T["net"] - net_tot
        if max(o_base, o_net) >= 0.005 * max(T["base"], 1.0):
            body.append("<tr class='gap'><td colspan='7'></td></tr>")
            body.append("<tr><td class='svc' style='border-left:3px solid #cfcad6'><b>Other Aid</b><br>"
                        f"{grey('orphan support; systems money not cutting services')}</td>"
                        + "".join(f"<td>{c}</td>" for c in (money(max(o_base, 0)), money(max(o_net, 0)), "", nm, "",
                                                            nm)) + "</tr>")
        base_tot, net_tot, d_lo, d_hi = T["base"], T["net"], T["deaths_5y_lo"], T["deaths_5y_hi"]
    # total row (people exclude HIV prevention, whose unit is infections averted)
    ppl = rows.loc[rows["line"] != "hiv_prev", "units_lost"].sum()
    total = ["<td class='svc'><b>Total</b></td>", f"<td><b>{money(base_tot)}</b></td>",
             f"<td><b>{money(net_tot)}</b></td>", "<td></td>", f"<td><b>{num(ppl)}</b></td>",
             "<td></td>", f"<td><b>{num(rows['deaths_5y'].sum())}</b><br>{grey(rng(d_lo, d_hi))}</td>"]
    body.append("<tr class='tot'>" + "".join(total) + "</tr>")
    return ("<div class='ed-nyt-wrap'><table class='ed-nyt'><colgroup><col style='width:26%'>"
            + "<col style='width:12.3%'>" * 6 + "</colgroup><thead><tr>" + th_html + "</tr></thead><tbody>"
            + "".join(body) + "</tbody></table></div>").replace("$", "&#36;")


def _gain_rows(bucket, gains) -> list:
    """The 'aid rises' note under a disease's rows in the service table (I-15)."""
    g = (gains or {}).get(bucket, 0.0)
    if g < 0.5:
        return []
    return [f"<tr><td colspan='7' class='svc' style='border-left:3px solid {BUCKET_COLORS[bucket]}'>"
            f"<span class='sub'>{html.escape(gains_note(bucket, g))}</span></td></tr>"]


def _coverage_fig(rows: pd.DataFrame):
    """How much coverage each service loses: one bar per service (percentage points), largest first."""
    d = rows[rows["cov_ok"] & (rows["drop"] > 0)].copy()
    if d.empty:
        return None
    d = d.sort_values("drop")                      # plotly draws the first row at the bottom
    # the row label carries the coverage before -> after, so the bar end only needs the drop (fits on a phone)
    labels = [f"<b>{n}</b><br><span style='color:{MUTED}'>{cov_pair(c0, a)}{f' ({src})' if src else ''}</span>"
              for n, c0, a, src in zip(d["name"], d["cov0"], d["after"], d["cov_source"])]
    text = [f"  {_pts(v)}" for v in d["drop"]]
    xmax = float(d["drop"].max())
    fig = go.Figure(go.Bar(y=labels, x=_visible(list(d["drop"]), xmax * 1.35), orientation="h",
                           marker=dict(color=[BUCKET_COLORS[b] for b in d["bucket"]]), text=text,
                           textposition="outside", cliponaxis=False, textfont=dict(color=INK, size=13),
                           customdata=d["drop"], hovertemplate="%{y}: −%{customdata:.1f} percentage points"
                                                               "<extra></extra>"))
    h = max(260, 100 + 46 * len(d))                # two-line row labels need a little more height per row
    fig.update_layout(bargap=0.45)
    _layout(fig, h=h, title=_title(th.title_sub("Coverage Lost, by Service", "Percentage points; coverage before → after")),
            margin=dict(l=10, r=20, t=50, b=10), xaxis=dict(range=[0, xmax * 1.35]))
    return fig


def _dose_fig(dr: pd.DataFrame, bucket: str, cur_cut: float, bb: pd.Series, path: pd.DataFrame | None = None):
    """Even cut across all donors (solid, with its band across parameter values) and this scenario's own path (dashed, ending at the dot)."""
    col = BUCKET_COLORS[bucket]
    x = dr["cut"] * 100
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(x) + list(x[::-1]), y=list(dr["hi"]) + list(dr["lo"][::-1]), fill="toself",
                             fillcolor=th.tint(col, 0.15), line=dict(width=0), hoverinfo="skip",
                             name="Range Across Parameter Values", legendrank=3))
    fig.add_trace(go.Scatter(x=x, y=dr["deaths_5y"], mode="lines", line=dict(color=col, width=2),
                             name="Even Cut Across All Donors", legendrank=1,
                             customdata=np.c_[dr["net_loss_usd"].map(money), dr["cov_drop_pp"].fillna(0)],
                             hovertemplate="even cut: %{x:.0f}% of aid (%{customdata[0]} a year)<br>coverage "
                                           "-%{customdata[1]:.1f} percentage points<br>%{y:,.0f} extra deaths over "
                                           "5 years<extra></extra>"))
    ymax = float(dr["hi"].max()) * 1.3
    if cur_cut > 0:
        if path is not None and len(path):
            fig.add_trace(go.Scatter(x=path["cut"] * 100, y=path["deaths_5y"], mode="lines", name="This Scenario", legendrank=2,
                                     line=dict(color=INK, width=2, dash="dash"),
                                     hovertemplate="this scenario, scaled: %{x:.0f}% of aid lost<br>%{y:,.0f} extra "
                                                   "deaths over 5 years<extra></extra>"))
            ymax = max(ymax, float(path["deaths_5y"].max()) * 1.3)
        fig.add_trace(go.Scatter(x=[cur_cut * 100], y=[bb["deaths_5y"]], mode="markers", showlegend=False,
                                 marker=dict(size=12, color=INK, line=dict(color=th.SURFACE, width=2)),
                                 hovertemplate="this scenario: %{x:.0f}% cut, %{y:,.0f} deaths<extra></extra>"))
        left = cur_cut >= 0.3           # above-left of the dot; above-right for small cuts so it stays on the chart
        fig.add_annotation(x=cur_cut * 100, y=bb["deaths_5y"], ax=-28 if left else 28, ay=-44,
                           xanchor="right" if left else "left", yanchor="bottom",
                           text=f"This scenario:<br>{cur_cut:.0%} cut, {num(bb['deaths_5y'])} deaths",
                           showarrow=True, arrowhead=0, arrowwidth=1, arrowcolor=MUTED, standoff=7,
                           font=dict(color=INK, size=12), bgcolor=th.tint(th.SURFACE, 0.9))
    # direct labels instead of a legend: name the even-cut line at its end and the band inside it
    y_end, hi85, mid85 = float(dr["deaths_5y"].iloc[-1]), float(np.interp(85, x, dr["hi"])), \
        float(np.interp(85, x, (dr["hi"] + dr["deaths_5y"]) / 2))
    if y_end > 0:
        fig.add_annotation(x=100, y=y_end, text="<b>Even cut,<br>all donors</b>", showarrow=False, xanchor="right",
                           yanchor="top", yshift=-6, font=dict(size=12, color=col), align="right")
        fig.add_annotation(x=85, y=mid85 + (hi85 - mid85) * 0.35, text="Range across<br>parameter values", showarrow=False,
                           font=dict(size=11, color=MUTED))
    _layout(fig, h=420, title=_title("Extra Deaths as More Aid Is Cut"), showlegend=False,
            # x starts a little left of 0 so the "0%" tick does not sit on top of the y-axis "0"
            xaxis=dict(title="Share of this bucket's aid lost", ticksuffix="%", range=[-4, 102]),
            yaxis=dict(title="extra deaths over 5 years", range=[0, ymax if ymax > 0 else 1]))
    return fig


def _path_fig(res: dict):
    p = res["path"]
    years = [str(FIRST_YEAR + i - 1) for i in p.index]
    fig = go.Figure()
    for b in hm.BUCKETS:
        fig.add_trace(go.Bar(x=years, y=p[b], name=b, marker=dict(color=BUCKET_COLORS[b]),
                             hovertemplate=f"{b}<br>%{{x}}: %{{y:,.0f}} extra deaths<extra></extra>"))
    fig.update_layout(barmode="stack", bargap=0.35)
    _layout(fig, h=400, title=_title(th.title_sub("Extra Deaths Each Year", f"All four diseases, {FIRST_YEAR}-{FIRST_YEAR + 4}")),
            legend=dict(orientation="h", y=-0.12, x=0), yaxis=dict(title="extra deaths in that year"),
            xaxis=dict(type="category"))
    return fig


def pct_smart(frac: float) -> str:
    """A share as text that never shows 0% for a non-zero value: <0.1%, one decimal below 1%, else whole numbers."""
    if frac is None or pd.isna(frac) or not np.isfinite(frac):
        return "n/a"
    v = frac * 100
    if v <= 0:
        return "0%"
    if v < 0.1:
        return "<0.1%"
    return f"{v:.1f}%" if v < 1 else f"{v:,.0f}%"


def fiscal_gap_values(res) -> tuple:
    """I-13: (average per year 2026-2030, 2030, show the 2030 line) for the three gap numbers, from the same run as the
    headline: gap before the government steps in = aid lost (gross); filled = the chosen response plus any gradual
    budget money; left = the difference (= the headline's net aid lost)."""
    T, Y = res["totals"], res["years"].set_index("year")
    avg = {"gap": float(T["gross"]), "filled": float(T["replaced"]), "left": float(T["net"])}
    y30 = {"gap": float(Y.loc[2030, "aid_lost_usd"]), "filled": float(Y.loc[2030, "replaced_usd"]),
           "left": float(Y.loc[2030, "gap_usd"])}
    show = any(abs(avg[k] - y30[k]) > max(0.5, 1e-6 * abs(avg[k])) for k in avg)
    return avg, y30, show


def _response_phrase_short(fiscal_t) -> str:
    mode, theta = fiscal_t[0], fiscal_t[1]
    return {"none": NO_REPLACEMENT, "custom": f"a {theta:.0%} replacement",
            "max": "replacement up to fiscal space", "gradual": "a gradual budget increase"}.get(mode, "this response")


def _fiscal_sentence(res, F: dict, country_name: str, fiscal_t) -> str:
    avg, _, _ = fiscal_gap_values(res)
    if avg["gap"] <= 0:
        return "No aid is lost in this scenario, so there is no gap to fill."
    out = (f"{country_name} loses about {money_words(avg['gap'])}/yr in aid; under {_response_phrase_short(fiscal_t)} "
           f"the government fills {money_words(avg['filled'])}, leaving {money_words(avg['left'])}/yr unfilled.")
    cap = F["capacity"]
    year = "its best years" if F["effort"] == "p90" else "a strong year"
    out += (f" In {year} the health budget could add about {money_words(cap)}/yr for these programs (fiscal space)."
            if cap and cap > 0 else f" The health budget does not grow faster than usual even in {year}, so there is "
                                    "no fiscal space to fill the gap.")
    return out


def health_share_pill(F) -> tuple:
    """(label, value, tooltip, note) for health's share of government spending (one definition: health_share)."""
    v, y, est = F.get("ghes_pct_gov_spend"), F.get("ghes_pct_gov_spend_year"), F.get("ghes_pct_gov_spend_estimated")
    if v is None or pd.isna(v):
        return ("Health Share of Government Spending", "n/a", "No World Bank figure and no IHME / IMF data to estimate it.",
                "Abuja Target: 15%")
    if est:
        return (f"Health Share of Government Spending, {y} (estimated)", f"{v:.1f}%",
                "World Bank figure not available; estimated from IHME and IMF data.", "Abuja Target: 15%")
    return (f"Health Share of Government Spending, {y}", f"{v:.1f}%",
            "Government health spending ÷ all government spending (World Bank WDI, WHO Global Health Expenditure "
            "Database).", "Abuja Target: 15%")


def interest_text(F: dict) -> str:
    """'Interest: 38% of revenue (IMF WEO, 2024)', or '(estimated: median of low income countries)' (audit I-26)."""
    if F.get("interest_estimated"):
        return f"Interest: {F['interest_pct_revenue']:.0f}% of revenue (estimated: {F['interest_source']})"
    src = "IMF WEO Oct 2026" if str(F.get("interest_source", "")).startswith("net interest") else "World Bank WDI"
    y = F.get("interest_year")
    return f"Interest: {F['interest_pct_revenue']:.0f}% of revenue ({src}{f', {int(y)}' if y == y and y else ''})"


def _fiscal_panel(res: dict, country_name: str, imf: dict, fiscal_t=scn.DEFAULT_FISCAL):
    F = res["fiscal"]
    stress = (f" {interest_text(F)}, so the debt-stress factor is {F['stress_factor']:.2f} (1 at 10% of revenue or "
              "less, falling to 0.25 at 40%).")
    st.subheader(f"Can {country_name} Fill the Gap?",
                 help=_esc("All three numbers come from the same run as the headline, as averages per year over "
                           "2026-2030 (2030 shown underneath when it differs). Backfill capacity (fiscal space) = "
                           "government health spending x (strong-year growth minus typical growth) x a debt-stress "
                           "factor." + stress + " Growth rates are real (constant 2023 US$) from IHME, 2001-2023; "
                           "interest is the more recent of World Bank WDI interest payments and IMF WEO net "
                           "interest (primary minus overall balance), or the income-group median where neither "
                           "exists."))
    avg, y30, show30 = fiscal_gap_values(res)
    rev = F["revenue"]
    if (pd.isna(rev) or not rev) and imf.get("revenue_pct_gdp") and F["gdp"]:
        rev = imf["revenue_pct_gdp"] / 100 * F["gdp"]
    G = avg["gap"]
    st.markdown(th.pills_html([
        ("Government Health Spending (2023)", money(F["ghes"]),
         "IHME, constant 2023 US$",
         f"${F['ghes_pc']:,.0f} per person · {F['ghes_pct_gdp']:.1f}% of GDP" if not pd.isna(F["ghes_pc"]) else ""),
        ("Aid Lost as % of Government Health Spending", pct_smart(G / F["ghes"]) if F["ghes"] else "n/a",
         "Aid lost per year (gross, average 2026-2030) ÷ government health spending, 2023", ""),
        ("Aid Lost as % of Government Revenue", pct_smart(G / rev) if rev and not pd.isna(rev) else "n/a",
         "Aid lost per year (gross, average 2026-2030) ÷ total government revenue", ""),
        health_share_pill(F),
    ], large=True), unsafe_allow_html=True)
    none_selected = avg["filled"] <= 0.5 and fiscal_t[0] == "none"
    sub = lambda k: (f"2030: {money(y30[k])}" if show30 else "")
    st.markdown(th.pills_html([
        ("Gap Before Government Steps In", money(avg["gap"]),
         "Aid lost per year (gross), average 2026-2030.", sub("gap")),
        ("Filled by the Government", "0" if none_selected else money(avg["filled"]),
         "Replacement under the chosen response plus any gradual budget increase, average per year 2026-2030.",
         "No Government Replacement selected" if none_selected else sub("filled")),
        ("Gap Left After Government Response", money(avg["left"]),
         "Gap before the government steps in minus what it fills, average per year 2026-2030 (= Net Aid Lost).",
         sub("left")),
    ], large=True), unsafe_allow_html=True)
    st.markdown(_esc(_fiscal_sentence(res, F, country_name, fiscal_t)))
    if G <= 0:
        return
    views = [("Average per Year, 2026-2030", avg)] + ([("2030", y30)] if show30 else [])
    cap = float(F["capacity"] or 0.0)
    gmax = max(v["gap"] for _, v in views)
    on_scale = 0 < cap <= 4 * gmax                            # a capacity far beyond the gap would squash the bars
    xmax = max(gmax, cap if on_scale else 0.0) * 1.22
    fig = go.Figure()
    names = [n for n, _ in views][::-1]
    vals = [v for _, v in views][::-1]
    fig.add_trace(go.Bar(y=names, x=[v["gap"] for v in vals], orientation="h", width=0.62, name="Gap",
                         marker=dict(color=th.tint(LOSS, 0.18)), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Bar(y=names, x=[v["filled"] for v in vals], base=[0] * len(vals), orientation="h", width=0.42,
                         name="Filled by the government", marker=dict(color=th.BLUE),
                         text=[money(v["filled"]) if v["filled"] > 0.02 * xmax else "" for v in vals],
                         textposition="inside", insidetextanchor="middle", textfont=dict(color="white"),
                         customdata=[money(v["filled"]) for v in vals],
                         hovertemplate="%{y}: filled by the government %{customdata}<extra></extra>"))
    fig.add_trace(go.Bar(y=names, x=[v["left"] for v in vals], base=[v["filled"] for v in vals], orientation="h",
                         width=0.42, name="Gap left", marker=dict(color=LOSS),
                         text=[money(v["left"]) if v["left"] > 0.02 * xmax else "" for v in vals],
                         textposition="inside", insidetextanchor="middle", textfont=dict(color="white"),
                         customdata=[money(v["left"]) for v in vals],
                         hovertemplate="%{y}: gap left %{customdata}<extra></extra>"))
    fig.add_trace(go.Scatter(y=names, x=[v["gap"] for v in vals], mode="text", showlegend=False, hoverinfo="skip",
                             text=["  " + money(v["gap"]) + " gap" for v in vals], textposition="middle right",
                             textfont=dict(color=INK), cliponaxis=False))
    if on_scale:
        fig.add_vline(x=cap, line=dict(color=INK, width=1.5, dash="dash"))
        fig.add_annotation(x=cap, y=1.0, yref="paper", text=f"Backfill Capacity (Fiscal Space): {money(cap)}",
                           showarrow=False, xanchor="left", yanchor="top", xshift=5, font=dict(size=11, color=INK),
                           bgcolor=th.tint(th.SURFACE, 0.85))
    fig.update_layout(barmode="overlay", bargap=0.35, legend=dict(orientation="h", y=-0.18, x=0))
    _layout(fig, h=190 + 70 * len(views),
            title=_title(th.title_sub("The Gap and the Government Response", "US$ per year")),
            xaxis=dict(range=[0, xmax], nticks=4), yaxis=dict(type="category"), margin=dict(l=10, r=90, t=70, b=10))
    note = (None if on_scale or cap <= 0 else
            f"Backfill capacity (fiscal space), {money(cap)} a year, is off the scale of this chart.")
    chart(fig, source="Model estimates; IHME government health spending and its real growth, 2001-2023; "
                      f"{interest_text(F)}.", note=note)


# --------------------------------------------------------------------------- #
# Data years (audit I-17) and the malaria input checks (I-11), shared by the Methods and Validation pages
# --------------------------------------------------------------------------- #
WHO_MALARIA_DEATHS_2024 = 610_000      # WHO World Malaria Report 2025: estimated malaria deaths worldwide in 2024
DATA_YEARS = [   # (input, column holding each country's year or None, fixed years, source, column holding the source)
    ("Aid baseline (what a scenario cuts)", None, "2021-2023 average", "IHME DAH database", None),
    ("Government health spending", None, "2023", "IHME health spending database", None),
    ("Health share of government spending", "sh_xpd_ghed_ge_zs_year", None, "World Bank WDI (WHO GHED)", None),
    ("People living with HIV", "plhiv_year", None, "UNAIDS / WHO", "plhiv_source"),
    ("ART coverage", "sh_hiv_artc_zs_year", None, "UNAIDS / WHO", "sh_hiv_artc_zs_source"),
    ("PMTCT coverage", "sh_hiv_pmtc_zs_year", None, "UNAIDS / WHO", "sh_hiv_pmtc_zs_source"),
    ("TB incidence", "all_forms_of_tb_incidence_estimated_year", None, "WHO Global TB Report (via Gapminder)", None),
    ("TB treatment coverage", "sh_tbs_dtec_zs_year", None, "WHO (World Bank WDI)", None),
    ("Malaria deaths (baseline)", "malaria_deaths_year", None, "WHO World Malaria Report", "malaria_deaths_source"),
    ("Malaria population at risk", "malaria_pop_at_risk_year", None, "WHO World Malaria Report",
     "malaria_pop_at_risk_source"),
    ("Malaria cases needing treatment", "malaria_cases_year", None, "MAP P. falciparum + P. vivax clinical cases",
     "malaria_cases_source"),
    ("Malaria treatment coverage", "mal_cm_cov_year", None, "MAP effective treatment (per 100 cases)",
     "mal_cm_cov_source"),
    ("Bednet use", "mal_itn_cov_year", None, "MAP ITN use", "mal_itn_cov_source"),
    ("Indoor spraying coverage", "mal_irs_cov_year", None, "MAP household IRS coverage", "mal_irs_cov_source"),
    ("Malaria death trend", None, "2015-2024", "WHO estimated malaria deaths (fitted trend, ±5% a year: an assumption)",
     None),
    ("DTP3 coverage", "sh_imm_idpt_year", None, "WHO / UNICEF (World Bank WDI)", None),
    ("Under-5 mortality", "sh_dyn_mort_year", None, "UN IGME (World Bank WDI)", None),
    ("Under-5 mortality trend", None, "2010-2019", "UN IGME (World Bank WDI)", None),
    ("Population and births", "sp_pop_totl_year", None, "World Bank WDI", None),
    ("Interest as % of revenue (debt stress)", "interest_pct_revenue_year", None,
     "more recent of World Bank WDI and IMF WEO (Oct 2026)", "interest_pct_revenue_source"),
]


def _source_kind(s) -> str:
    s = str(s) if isinstance(s, str) else ""
    for key, kind in (("net interest", "IMF WEO"), ("median of", "estimated"), ("MAP", "MAP"), ("WHO", "WHO"), ("UNAIDS", "UNAIDS"), ("survey", "survey"),
                      ("World Bank", "World Bank"), ("default", "default"), ("no MAP", "no estimate"),
                      ("derived", "derived"), ("assumption", "assumed")):
        if s.startswith(key) or (key == "World Bank" and "World Bank" in s):
            return kind
    return "other" if s else "n/a"


COVERAGE_YEAR_COLS = ["sh_hiv_artc_zs_year", "sh_hiv_pmtc_zs_year", "sh_tbs_dtec_zs_year", "sh_imm_idpt_year",
                      "mal_cm_cov_year", "mal_itn_cov_year", "mal_irs_cov_year"]


def _yr_range(a: int, b: int) -> str:
    return str(a) if a == b else f"{a}-{str(b)[2:] if str(a)[:2] == str(b)[:2] else b}"


def inputs_years_line(ci: pd.DataFrame, isos) -> str:
    """One line for under the country header (audit I-17), with every year read from the inputs: 'Inputs: aid
    2021-23 average; coverage 2024-25 (malaria: MAP 2025); government health spending 2023; applied to 2026-2030
    without projection.'"""
    d = ci.loc[[c for c in isos if c in ci.index]]
    modes = [int(pd.to_numeric(d[c], errors="coerce").dropna().mode()[0]) for c in COVERAGE_YEAR_COLS
             if c in d and pd.to_numeric(d[c], errors="coerce").notna().any()]
    mal = pd.to_numeric(d.get("mal_cm_cov_year"), errors="coerce").dropna()
    a0, a1 = hm.AID_BASE_YEARS
    return (f"Inputs: aid {_yr_range(a0, a1)} average; coverage {_yr_range(min(modes), max(modes))}"
            + (f" (malaria: MAP {int(mal.mode()[0])})" if len(mal) else "")
            + f"; government health spending {hm.GHES_YEAR}; applied to {scn.YEARS[0]}-{scn.YEARS[-1]} without "
              "projection.")


def data_years_table(ci: pd.DataFrame, isos) -> pd.DataFrame:
    """One row per model input: years used (most common, with the range) and how many countries use each source."""
    d = ci.loc[[c for c in isos if c in ci.index]]
    rows = []
    for name, ycol, fixed, src, scol in DATA_YEARS:
        if fixed:
            years = fixed
        else:
            y = pd.to_numeric(d.get(ycol, pd.Series(dtype=float)), errors="coerce").dropna().astype(int)
            years = ("n/a" if y.empty else str(y.mode()[0]) if y.min() == y.max()
                     else f"{y.mode()[0]} (range {y.min()}-{y.max()})")
        if scol and scol in d:
            k = d[scol].map(_source_kind).value_counts()
            used = " · ".join(f"{n} {v}" for n, v in k.items())
        else:
            used = f"all {len(d)}"
        rows.append({"Input": name, "Year": years, "Source": src, "Countries by source": used})
    return pd.DataFrame(rows).set_index("Input")


def malaria_input_comparison(ci: pd.DataFrame, names: dict) -> pd.DataFrame:
    """Malaria countries (baseline deaths > 0): MAP 2025 vs the values the model used before (I-11)."""
    d = ci[(ci["malaria_deaths"] > 0)].copy()
    pct = lambda v: "n/a" if pd.isna(v) else f"{v:.0%}"  # noqa: E731
    yr = lambda v: "" if pd.isna(v) else f" ({int(v)})"  # noqa: E731
    P = _default_params()["central"]
    dcm, ditn = float(P["mal_cm_default_cov"]), float(P["mal_itn_default_use"])
    old_cases, new_cases = d["malaria_cases_prev"], d["malaria_cases"]
    change = (new_cases / old_cases - 1).where(old_cases > 0)
    # what the model used before: the fever-treatment survey only where incidence >= 50 per 1,000, else the default;
    # bednets: the WHO/MAP modelled series or the latest survey (any year), else the default
    tret_ok = d["sh_mlr_tret_zs"].notna() & (d["sh_mlr_incd_p3"] >= hm.MAL_CM_MIN_INCIDENCE)
    out = pd.DataFrame({
        "Country": [names.get(c, c) for c in d.index],
        "Treatment: Before": [pct(v / 100) + yr(y) if ok else f"{dcm:.0%} (default)" for v, y, ok in
                              zip(d["sh_mlr_tret_zs"], d["sh_mlr_tret_zs_year"], tret_ok)],
        "Treatment: Now": [pct(dcm if pd.isna(v) else v) + f" ({hm.coverage_source(r, 'mal_cm')})"
                           for v, (_, r) in zip(d["mal_cm_cov"], d.iterrows())],
        "Bednets: Before": [f"{ditn:.0%} (default)" if pd.isna(v) else pct(v / 100) + yr(y) for v, y in
                            zip(d["sh_mlr_nets_zs"], d["sh_mlr_nets_zs_year"])],
        "Bednets: Now": [pct(ditn if pd.isna(v) else v) + f" ({hm.coverage_source(r, 'mal_itn')})"
                         for v, (_, r) in zip(d["mal_itn_cov"], d.iterrows())],
        "Cases: Before": [num(v) for v in old_cases],
        "Cases: MAP 2025": [num(v) for v in new_cases],
        "Cases: Change": ["n/a" if pd.isna(v) else f"{v:+.0%}" + (" ⚑" if abs(v) > 0.30 else "") for v in change],
    }, index=d.index)
    return out.sort_values("Country")


# --------------------------------------------------------------------------- #
# Across all countries
# --------------------------------------------------------------------------- #
def _all_country_results(sk, ctl) -> pd.DataFrame:
    """Precomputed file when the settings are the defaults it was built with; otherwise run live. Global Fund & Gavi
    Shortfalls always uses its default cuts here (the sliders apply to the country view)."""
    preset, ptab = ctl["preset"], ctl["ptab"]
    if preset == scn.SHORTFALLS:
        ci = _inputs()["ci"]
        sk = scn.scenario_key(scn.build_scenario(preset, scn.default_opts(preset, ci), ci))
    path = scn.precomputed_path(hm.MODEL_DIR, preset)
    if (preset in scn.PRECOMPUTED_PRESETS and path.exists() and ctl["fiscal_t"] == scn.DEFAULT_FISCAL
            and ctl["trend"] == scn.DEFAULT_MORTALITY_TREND):
        ci = _inputs()["ci"]
        default_sk = scn.scenario_key(scn.build_scenario(preset, scn.default_opts(preset, ci), ci))
        p0 = _default_params()
        same_params = ptab[["central", "low", "high"]].astype(float).reindex(p0.index).equals(
            p0[["central", "low", "high"]].astype(float))
        if sk == default_sk and same_params:
            return _precomputed(preset, path.stat().st_mtime)
    return _run_all(sk, ctl["fiscal_t"], ctl["ptab_json"], ctl["trend"])


# claim C7 / L-03: what share of the aid the dashboard's countries cover (IHME DAH 2021-23, elim_ch == 0; logic review)
SCOPE_NOTE = ("The 71 dashboard countries receive about 72% of the HIV, TB, malaria and vaccine aid that IHME assigns "
              "to a country (2021-23); aid coded to global or unallocated programs (about 18% more) is not included.")
ALL_RANGE_TIP = ("Totals add up each country's central estimate. The range is the " + RANGE_LABEL + ": the "
                 "2.5th-97.5th percentile of the all-country total over the 400 draws (the same draws in every "
                 "country). " + RANGE_TIP)


def cross_country(sk, ctl, iso3, names) -> pd.DataFrame:
    """The All Countries page: totals, map, exposure scatter and the 15 hardest-hit countries."""
    A = _all_country_results(sk, ctl).copy()
    A["name"] = A["iso3"].map(lambda c: names.get(c, c))
    A = A[A["gross_loss_usd"] > 0].copy()
    if A.empty:
        st.info("No country loses aid in this scenario.")
        return A
    is_mou = ctl["preset"] == MOU
    shortfalls = ctl["preset"] == scn.SHORTFALLS
    st.caption(_esc(f"{scenario_title(ctl['preset'], None if shortfalls else ctl.get('opts'))} · "
                    f"{_resp_label(ctl['fiscal_t'])}" + ("" if ctl["trend"] else " · Death Rates Held Constant")))
    if shortfalls and scn.shortfall_cuts(ctl.get("opts")) != scn.shortfall_cuts(None):
        st.caption(_esc(f"This page uses the default cuts ({scn.shortfall_label(None)}). Your setting "
                        f"({scn.shortfall_label(ctl.get('opts'))}) applies to the country Dashboard only."))
    if is_mou:
        st.subheader(f"MOU Countries With Funding Data ({len(A)})",
                     help="America First MOUs is modelled only where the country has signed an MOU (KFF tracker) and "
                          "the team's sheet has its 2026-2030 US funding schedule. On the map, countries that signed "
                          "without funding data are light grey; countries without an MOU are lighter grey.")
    after_cols = [c for c in ("deaths_after_2030", "deaths_after_2030_reengage_min", "deaths_after_2030_reengage_max")
                  if c in A]
    tot = A[["gross_loss_usd", "net_loss_usd", "deaths_y1", "deaths_5y", "hiv_infections_5y"] + after_cols].sum()
    # ranges from the per-draw totals over all countries (IMP-10), not the sum of country percentiles
    tot["deaths_5y_lo"], tot["deaths_5y_hi"] = hm.total_range(A, "deaths_5y")
    if "deaths_after_2030" in after_cols:
        tot["deaths_after_2030_lo"], tot["deaths_after_2030_hi"] = hm.total_range(A, "deaths_after_2030")
    st.markdown(th.pills_html([
        (f"Aid Lost per Year, MOU Countries With Funding Data ({len(A)})" if is_mou
         else f"Aid Lost per Year, {len(A)} of {len(names)} Countries", money(tot["gross_loss_usd"]),
         "HIV, TB, malaria and vaccine aid removed by the scenario. " + SCOPE_NOTE,
         f"Net Aid Lost {money(tot['net_loss_usd'])}"),
        ("Further Deaths, 2031-2035 (Assumption-Driven)", num(tot["deaths_after_2030"]),
         REENGAGE_TIP + " Deaths in 2031-2035 caused by the 2026-2030 losses, with funding back from 2031: people "
         "still off HIV treatment, new HIV infections, children who missed vaccines and TB spread by untreated "
         "patients. " + ALL_RANGE_TIP,
         "Range " + rng(tot["deaths_after_2030_lo"], tot["deaths_after_2030_hi"])
         + (f"; {rng(tot['deaths_after_2030_reengage_min'], tot['deaths_after_2030_reengage_max'])} across "
            f"return-to-care {float(ctl['ptab'].loc['art_reengage', 'low']):.0%}-"
            f"{float(ctl['ptab'].loc['art_reengage', 'high']):.0%} a year"
            if "deaths_after_2030_reengage_min" in tot else ""))
        if "deaths_after_2030" in tot else
        ("Extra Deaths, Year 1", num(tot["deaths_y1"]), "Deaths build up over the five years", ""),
        ("Extra Deaths Over 5 Years", num(tot["deaths_5y"]), ALL_RANGE_TIP,
         "Range " + rng(tot["deaths_5y_lo"], tot["deaths_5y_hi"])),
        ("New HIV Infections, 5 Years", num(tot["hiv_infections_5y"]),
         "From lost HIV prevention and treatment. Totals add up each country's central estimate.", ""),
    ], large=True), unsafe_allow_html=True)
    A["deaths_per_100k"] = A["deaths_5y"] / A["pop"] * 1e5
    A["loss_pct_ghes_pct"] = A["loss_pct_ghes"] * 100

    _, tcol = st.columns([5, 1])
    world = tcol.toggle("World", value=False, key="m_map_world", help="Show the whole world instead of Africa and Asia")
    groups = scn.mou_groups(_inputs()["ci"], list(names)) if is_mou else None
    chart(_world_map(A, iso3, world, groups, names), source=SRC_MODEL)

    c1, c2 = st.columns([1.15, 1])
    with c1:
        d = A[(A["loss_pct_ghes_pct"] > 0) & (A["deaths_per_100k"] > 0)]
        fig = go.Figure()
        other = d[d["iso3"] != iso3]
        sz = np.sqrt(d["net_loss_usd"].clip(lower=1)) / np.sqrt(d["net_loss_usd"].max()) * 40 + 6
        top = d.nlargest(SCATTER_LABELS, "deaths_per_100k")                   # label only these
        fig.add_trace(go.Scatter(x=other["loss_pct_ghes_pct"], y=other["deaths_per_100k"], mode="markers",
                                 marker=dict(size=sz[d["iso3"] != iso3], color=th.OTHER, opacity=0.6,
                                             line=dict(color=th.SURFACE, width=1)),
                                 customdata=np.c_[other["name"], other["net_loss_usd"].map(money), other["deaths_5y"].map(num)],
                                 hovertemplate="<b>%{customdata[0]}</b><br>aid loss = %{x:.0f}% of government health "
                                               "spending<br>%{y:,.0f} deaths per 100,000 over 5 years "
                                               "(%{customdata[2]})<br>net aid lost %{customdata[1]} a year<extra></extra>",
                                 name="Countries"))
        me = d[d["iso3"] == iso3]
        if len(me):
            fig.add_trace(go.Scatter(x=me["loss_pct_ghes_pct"], y=me["deaths_per_100k"], mode="markers+text",
                                     text=["" if iso3 in set(top["iso3"]) else f"<b>{iso3}</b>"],
                                     textposition="top center", textfont=dict(size=13, color=th.BRAND),
                                     marker=dict(size=sz[d["iso3"] == iso3], color=th.BRAND, line=dict(color=th.SURFACE, width=2)),
                                     hoverinfo="skip", name="Selected country"))
        fig.add_vline(x=d["loss_pct_ghes_pct"].median(), line=dict(color=GRID, width=1, dash="dot"))
        fig.add_hline(y=d["deaths_per_100k"].median(), line=dict(color=GRID, width=1, dash="dot"))
        # labels stacked in a column right of the points, at least LABEL_GAP_LOG apart, each with a leader line
        # (annotations on log axes take log10 positions)
        lx = float(np.log10(d["loss_pct_ghes_pct"].max())) + 0.3
        prev = None
        for r in top.sort_values("deaths_per_100k", ascending=False).itertuples():
            ly = float(np.log10(r.deaths_per_100k))
            ly = ly if prev is None else min(ly, prev - LABEL_GAP_LOG)
            prev = ly
            fig.add_annotation(x=float(np.log10(r.loss_pct_ghes_pct)), y=float(np.log10(r.deaths_per_100k)),
                               ax=lx, ay=ly, axref="x", ayref="y",
                               text=f"<b>{r.iso3}</b>" if r.iso3 == iso3 else r.iso3, showarrow=True, arrowhead=0,
                               arrowwidth=1, arrowcolor=MUTED, standoff=4, xanchor="left",
                               font=dict(size=11, color=th.BRAND if r.iso3 == iso3 else INK, family=th.SANS))
        y_lo = float(np.log10(d["deaths_per_100k"].min())) - 0.15
        _layout(fig, h=480, title=_title(th.title_sub("Budget Exposure vs. Deaths", "Each circle is a country")), showlegend=False,
                xaxis=dict(type="log", title="aid lost, % of govt. health spending (log)", ticksuffix="%",
                           tickvals=LOG_TICKS, ticktext=[f"{v:g}" for v in LOG_TICKS],
                           range=[float(np.log10(d["loss_pct_ghes_pct"].min())) - 0.15, lx + 0.45]),
                yaxis=dict(type="log", title="extra deaths per 100,000, 5 years (log)",
                           tickvals=LOG_TICKS, ticktext=[f"{v:g}" for v in LOG_TICKS],
                           range=[min(y_lo, (prev or y_lo) - 0.1), float(np.log10(d["deaths_per_100k"].max())) + 0.2]))
        chart(fig, source=SRC_MODEL, note=f"Each circle is a country, sized by aid lost per year; "
                                          f"{names.get(iso3, iso3)} is highlighted. Dotted lines are medians.")
    with c2:
        top = A.sort_values("deaths_5y", ascending=False).head(15).iloc[::-1]
        fig = go.Figure()
        for b in hm.BUCKETS:
            fig.add_trace(go.Bar(y=top["name"], x=top[f"deaths_5y_{b}"], name=b, orientation="h",
                                                  marker=dict(color=BUCKET_COLORS[b]),
                                 hovertemplate=f"%{{y}} · {b}: %{{x:,.0f}}<extra></extra>"))
        tot15 = top[[f"deaths_5y_{b}" for b in hm.BUCKETS]].sum(axis=1)
        fig.add_trace(go.Scatter(y=top["name"], x=tot15, mode="text", text=["  " + num(v) for v in tot15],
                                 textposition="middle right", textfont=dict(color=INK, size=12), showlegend=False,
                                 hoverinfo="skip", cliponaxis=False))
        fig.update_layout(barmode="stack")
        key = th.color_key([(b, BUCKET_COLORS[b]) for b in hm.BUCKETS])
        sel = names.get(iso3, iso3)
        _layout(fig, h=500, showlegend=False,
                title=dict(text=f"Most Extra Deaths, 5 Years<br><span style='font-size:12px'>{key}</span>",
                           x=0, xanchor="left"),
                yaxis=dict(tickvals=list(top["name"]),
                           ticktext=[f"<b><span style='color:{th.BRAND}'>{n}</span></b>" if n == sel else n
                                     for n in top["name"]]),
                xaxis=dict(range=[0, float(tot15.max()) * 1.22]), margin=dict(l=10, r=20, t=70, b=10))
        rank = int((A["deaths_5y"] > A.loc[A["iso3"] == iso3, "deaths_5y"].max()).sum()) + 1 \
            if (A["iso3"] == iso3).any() else None
        chart(fig, source=SRC_MODEL,
              note=None if rank is None or rank <= 15 else f"{sel} ranks {rank} of {len(A)}.")
    return A


def _world_map(A: pd.DataFrame, iso3: str, world: bool = False, groups: dict | None = None, names: dict | None = None):
    """Deaths per 100,000 by country. With MOU groups (America First MOUs), countries outside the modelled group are
    drawn in grey: signed without funding data (light) and no MOU (lighter)."""
    zmax = float(A["deaths_per_100k"].quantile(0.95))
    pct = A["loss_pct_ghes_pct"].map(lambda v: "n/a" if pd.isna(v) else f"{v:,.0f}%")
    fig = go.Figure(go.Choropleth(
        locations=A["iso3"], z=A["deaths_per_100k"], locationmode="ISO-3", zmin=0, zmax=zmax,
        colorscale=[[i / (len(th.MAP_RAMP) - 1), c] for i, c in enumerate(th.MAP_RAMP)],
        marker_line_color=th.SURFACE, marker_line_width=0.5,
        colorbar=dict(orientation="h", title=dict(text="Extra Deaths per 100,000 (5 Years)", side="top",
                                                  font=dict(size=12, color=MUTED)),
                      thickness=10, len=0.45, x=0.5, xanchor="center", y=0, yanchor="top", ypad=0,
                      tickfont=dict(size=11, color=MUTED), outlinewidth=0),
        customdata=np.c_[A["name"], A["gross_loss_usd"].map(money), A["deaths_5y"].map(num), pct,
                         A["hiv_infections_5y"].map(num) if "hiv_infections_5y" in A else ["n/a"] * len(A)],
        hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[2]} extra deaths over 5 years "
                      "(%{z:,.0f} per 100,000)<br>%{customdata[4]} new HIV infections over 5 years<br>"
                      "aid lost: %{customdata[1]} a year<br>"
                      "= %{customdata[3]} of government health spending<extra></extra>"))
    if groups:
        for g, col, txt in ((scn.MOU_GROUP_B, th.blend(th.MUTED, 0.45), "MOU signed; no funding data"),
                            (scn.MOU_GROUP_C, th.blend(th.MUTED, 0.2), "No MOU")):
            locs = [c for c, v in groups.items() if v == g and c not in set(A["iso3"])]
            if locs:
                fig.add_trace(go.Choropleth(locations=locs, z=[1] * len(locs), locationmode="ISO-3", showscale=False,
                                            colorscale=[[0, col], [1, col]], marker_line_color=th.SURFACE,
                                            marker_line_width=0.5, customdata=[(names or {}).get(c, c) for c in locs],
                                            hovertemplate=f"<b>%{{customdata}}</b><br>{txt}<extra></extra>"))
    sel = A[A["iso3"] == iso3]
    if len(sel):
        fig.add_trace(go.Choropleth(locations=sel["iso3"], z=[1], locationmode="ISO-3", showscale=False,
                                    colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
                                    marker_line_color=INK, marker_line_width=2, hoverinfo="skip"))
    fig.update_geos(projection_type="natural earth", showframe=False, showcoastlines=False, showcountries=True,
                    countrycolor=th.SURFACE, countrywidth=0.5, showland=True, landcolor=th.RULE,
                    bgcolor=th.SURFACE, **(dict(lataxis_range=[-45, 75]) if world else MAP_FOCUS))
    _layout(fig, h=470, title=_title(th.title_sub("Extra Deaths per 100,000 People", "Over 5 years")), margin=dict(l=0, r=0, t=40, b=50))
    return fig


# --------------------------------------------------------------------------- #
# Methods: cross-check summary and published estimates
# --------------------------------------------------------------------------- #
def _crosscheck_summary(res, I, ptab, country_name) -> str:
    regs = [I["reg"][k] for k in ("hiv_art", "tb_treatment", "dtp3")]
    s1 = (f"Panel regressions across up to {max(r['n_countries'] for r in regs)} countries (2005-2023, with country and "
          "year fixed effects) relate HIV treatment coverage, TB treatment coverage and DTP3 vaccine coverage to aid per "
          "person in need.")
    s3 = ("They describe how coverage moved with aid in the past, when changes were gradual and other funders often "
          "filled gaps, so they likely understate the effect of a sudden cut.")
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


def deaths_per_child_immunised(isos, I, ptab) -> tuple:
    """The model's deaths averted per fully immunized child, births-weighted across countries: (over a lifetime,
    within ten years of vaccination). Batch 5+6: the VIMC-based country values (imm_dpc, imm_dpc_lag0-9); under the
    legacy switch, the old rule (lifetime = under-5 value / imm_u5_share)."""
    Pc = hm.draw_params(ptab, 0)
    life, window, births = [], [], []
    for c in isos:
        row = I["ci"].loc[c]
        b = row.get("births", np.nan)
        if pd.isna(b) or b <= 0:
            continue
        if hm.imm_legacy(row, Pc):
            u5 = float(hm.per_unit_deaths(row, Pc, np.nan, trend=False)["imm"][0, -1])
            life.append(u5 / float(Pc["imm_u5_share"][0]))
            window.append(u5)
        else:
            w = hm.imm_per_child(row, Pc)[0]
            life.append(float(row["imm_dpc"]))
            window.append(float(w.sum()))
        births.append(float(b))
    if not births:
        return np.nan, np.nan
    return float(np.average(life, weights=births)), float(np.average(window, weights=births))


def _published_estimates(A: pd.DataFrame, I, ptab):
    st.markdown("#### Does This Match Published Estimates?")
    if A is None or A.empty:
        st.info("The current scenario cuts no aid, so there is nothing to compare.")
        return
    lifetime, model_per_child = deaths_per_child_immunised(A["iso3"], I, ptab)
    n = len(A)
    tbl = pd.DataFrame([
        {"Study": "Cavalcanti et al., Lancet 2025",
         "What It Covers": "USAID defunding; all causes and all programs; 133 countries; 2025-2030",
         "Published": "More than 14M additional deaths by 2030",
         "This Model (Current Scenario)": f"{num(A['deaths_5y'].sum())} extra deaths over 5 years "
                                          f"({RANGE_LABEL} {rng(*hm.total_range(A, 'deaths_5y'))}), {n} countries"},
        {"Study": "ten Brink et al., Lancet HIV 2025",
         "What It Covers": "HIV only; 24% cut by the top 5 donors plus PEPFAR ending; all low- and middle-income "
                           "countries; 2025-2030",
         "Published": "0.77M to 2.93M additional HIV deaths",
         "This Model (Current Scenario)": f"{num(A['deaths_5y_HIV'].sum())} extra HIV deaths over 5 years, {n} countries"},
        {"Study": "Gavi (2000-2024)",
         "What It Covers": "Future deaths averted per child immunised",
         "Published": "About 0.017 (20.6M deaths averted / 1.2B children)",
         "This Model (Current Scenario)": f"{lifetime:.3f} per child over a lifetime (VIMC, Toor et al. 2021, by country and antigen), of which {model_per_child:.3f} within ten years of vaccination (births-weighted across countries; excludes DTP, polio and BCG)"},
    ])
    st.table(tbl.set_index("Study"))
    st.markdown("The published studies cover more causes, programs, countries or years than this model, which counts "
                "only HIV, TB, malaria and vaccine aid in the countries on this dashboard, so its totals should come "
                "in below the Cavalcanti figure and within or below the ten Brink range for comparable scenarios. "
                "The HIV comparison depends on how lost ART money is turned into people who stop treatment (each "
                "unit is a full-cost equivalent of the lost money, treated as a person who stops ART; the death risk "
                "and transmission per person are from the evidence in Batch 2 of the logic review), so agreement "
                "with ten Brink et al. should not be read as validation.")


# --------------------------------------------------------------------------- #
# Country brief (self-contained HTML; prints cleanly to PDF from the browser)
# --------------------------------------------------------------------------- #
def _brief_html(country_name, preset, resp_label, items, cards, figs, opts=None) -> str:
    e = html.escape
    stats = "".join(f"<div class='stat'><div class='lbl'>{e(lbl)}</div><div class='val'>{e(val)}</div>"
                    f"<div class='sub'>{e(sub or '')}</div></div>" for lbl, val, sub, _ in items)
    card_html = "".join(f"<div class='card' style='border-top-color:{c['color']}'><div class='cb'>{e(c['bucket'])}</div>"
                        f"<div class='sub'>{e(c['service'])}</div><div class='cl'>{e(c['people'])}<br>"
                        f"<b>{e(c['coverage'])}</b> Coverage Drop<br><b>{e(c['deaths'])}</b> Extra Deaths Over 5 Years"
                        f"</div><div class='sub'>{e(c['foot'])}</div></div>" for c in cards)
    charts, first = [], True
    for f in figs:
        if f is None:
            continue
        g = th.style_fig(tc_fig(go.Figure(f)))
        g.update_layout(width=700, autosize=False)
        charts.append("<div class='chart'>" + g.to_html(full_html=False, include_plotlyjs="cdn" if first else False,
                                                        config={"displayModeBar": False, "responsive": False}) + "</div>")
        first = False
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(country_name)}: Funding-Cut Brief</title>
<link rel="stylesheet" href="{th.FONTS_URL}">
<style>
  @page {{ size: auto; margin: 14mm; }}
  body {{ font-family: {th.SANS}; color: {th.INK}; background: {th.SURFACE};
         max-width: 720px; margin: 24px auto; padding: 0 16px; line-height: 1.45; }}
  h1, h2, .val, .cb {{ font-family: {th.SERIF}; }}
  h1 {{ font-size: 30px; font-weight: 600; margin: 0 0 4px; }}
  h2 {{ font-size: 20px; font-weight: 600; margin: 28px 0 10px; padding-top: 14px; border-top: 1px solid {th.RULE}; }}
  .meta {{ color: {th.MUTED}; font-size: 14px; }}
  .grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }}
  .cards {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }}
  .stat, .card {{ border: 1px solid {th.RULE}; border-radius: 10px; padding: 10px 12px; break-inside: avoid; }}
  .card {{ background: {th.SURFACE_TINT}; }}
  .card {{ border-top: 4px solid; }}
  .lbl {{ font-size: 13px; color: {th.MUTED}; }}
  .val {{ font-size: 24px; font-weight: 600; }}
  .sub {{ font-size: 12px; color: {th.MUTED}; }}
  .cb {{ font-weight: 600; font-size: 17px; }}
  .cl {{ font-size: 14px; margin: 6px 0; }}
  .chart {{ break-inside: avoid; margin: 8px 0 0; }}
  .foot {{ color: {th.MUTED}; font-size: 12px; margin-top: 24px; border-top: 1px solid {th.RULE}; padding-top: 8px; }}
  @media print {{ body {{ margin: 0 auto; }} h2 {{ break-after: avoid; }} }}
</style></head><body>
<h1>{e(country_name)}: What a Funding Cut Does</h1>
<div class="meta"><b>Donor Scenario:</b> {e(scenario_title(preset, opts))}<br><b>Government Response:</b> {e(resp_label)}</div>
<p class="meta">{e(scn.preset_description(preset, opts))}</p>
<h2>The Headline</h2><div class="grid">{stats}</div>
<h2>What Every US$1 Million Cut Does, by Disease</h2><div class="cards">{card_html}</div>
<h2>Coverage and Deaths</h2>{''.join(charts)}
<div class="foot">Generated {_dt.date.today():%d %B %Y} from the Health Financing dashboard. Sources: IHME Development
Assistance for Health and health spending; World Bank WDI; WHO and UNAIDS series via Gapminder. Ranges are the range across
parameter values (400 Monte Carlo draws); they exclude uncertainty in the data and in the model's structure, which is
larger. Scenario estimates, not forecasts.</div>
</body></html>"""

