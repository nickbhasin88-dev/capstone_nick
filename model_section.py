"""
Section 4 of the dashboard: what a funding cut does (money -> fiscal response -> coverage -> lives).

Called from app.py:   render_model_section(iso3, country_name, imf_overrides, names)
All modelling lives in health_model.py and the scenario presets in scenarios.py; this file builds the sidebar
controls and draws the results. chart / stat / title_case are shared with app.py so every section looks the same;
colours and fonts come from theme.py.
"""
from __future__ import annotations

import datetime as _dt
import html
import inspect
import io
import re

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import health_model as hm
import scenarios as scn
import theme as th
from scenarios import PRESETS

_ver = tuple(int(x) for x in st.__version__.split(".")[:2] if x.isdigit())
WIDE = {"width": "stretch"} if _ver >= (1, 50) else {"use_container_width": True}
_METRIC_ARGS = set(inspect.signature(st.metric).parameters)

INK, MUTED, GRID = th.INK, th.MUTED, th.RULE
SCATTER_LABELS = 10                  # label the 10 countries with the most deaths per 100,000
MAP_FOCUS = dict(center=dict(lon=62, lat=4), projection_scale=1.85)     # Africa and South / Southeast Asia
LOG_TICKS = [0.01, 0.1, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000]
LOSS, BACKFILL = th.ROSE, th.TEAL
SCEN_A, SCEN_B = th.GRAPE, th.BLUE
BUCKET_COLORS = th.DISEASE_COLORS
REPLACED_ALPHA = 0.4                 # "replaced by government" = the disease colour at this opacity
FIRST_YEAR = 2026                    # year 1 after the cut
MAIN_LINE = {"HIV": "hiv_art", "TB": "tb_ds", "Malaria": "mal_itn", "Immunization": "imm"}
BUCKET_WORD = {"HIV": "HIV", "TB": "TB", "Malaria": "malaria", "Immunization": "immunization"}

# "Historical behaviour" is not offered: the estimated historical response is no backfilling, the same as "none"
GOV_MODES = {"No backfill (historical norm)": "none", "Replace a set share": "custom",
             "As much as fiscal space allows": "max"}
SHOW_BRIEF = False                   # the Download Country Brief button (code kept for later)
PRESET_SHORT = {
    "Full US exit": "All US health aid ends, including WHO, Gavi and UNFPA; the US Global Fund pledge falls 23%.",
    "America First MOUs": "US bilateral aid follows each country's 2026-2030 MOU schedule; US multilateral exits as in "
                          "Full US Exit.",
    "IHME 2025 preliminary estimates": "IHME's preliminary 2025 change for every donor, channel and disease, applied to "
                                       "this country's mix.",
    "OECD-reported 2025 aid cuts": "Each donor's 2025 aid cut (US -57%, Germany -17%, France -11%, UK -11%, Japan -6%) "
                                   "applied to its health aid.",
    "Global Fund & Gavi shortfalls": "All donors: Global Fund -28% and Gavi -24% (replenishment shortfalls).",
    "Combined retreat": "Full US Exit plus the OECD-reported 2025 cuts for every other donor.",
    "Custom": "Set the cuts yourself by donor and by channel.",
}
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
def _run(iso3, sc_key, fiscal_t, ptab_json, trend=True, n_draws=400):
    ptab = pd.read_json(io.StringIO(ptab_json), orient="split")
    return hm.run_country(iso3, scn.scenario_from_key(sc_key), hm.Fiscal(*fiscal_t), _inputs(), ptab, n_draws=n_draws,
                          mortality_trend=trend)


@st.cache_data(show_spinner=False, max_entries=32)
def _dose(iso3, bucket, fiscal_t, ptab_json, trend=True):
    ptab = pd.read_json(io.StringIO(ptab_json), orient="split")
    return hm.dose_response(iso3, bucket, hm.Fiscal(*fiscal_t), _inputs(), ptab, grid=np.linspace(0, 1, 21), n_draws=100,
                            mortality_trend=trend)


@st.cache_data(show_spinner="Running the model for every country...", max_entries=16)
def _run_all(sc_key, fiscal_t, ptab_json, trend=True):
    ptab = pd.read_json(io.StringIO(ptab_json), orient="split")
    return hm.run_all(scn.scenario_from_key(sc_key), hm.Fiscal(*fiscal_t), _inputs(), ptab,
                      n_draws=scn.ALL_COUNTRY_DRAWS, mortality_trend=trend)


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
    return f"{s}${a:,.2f}" if 0 < a < 10 else f"{s}${a:,.0f}"


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
    """Title Case a figure's labels: title, legend entries, axis and colour-bar titles, annotations."""
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


def chart(fig, **kw):
    # theme=None: draw with the "editorial" Plotly template instead of Streamlit's chart theme
    st.plotly_chart(th.style_fig(tc_fig(fig)), theme=None, **WIDE, **kw)


def stat(col, label, value, sub=None, help=None):
    """A bordered metric; `sub` (a range or context) sits under the value in small grey text, without an arrow."""
    kw = {"help": help}
    label, sub = title_case(label), title_case(sub)
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
    fig.update_layout(height=h, margin=margin, **kw)
    fig.update_xaxes(automargin=True)
    fig.update_yaxes(automargin=True)
    return fig


def _title(text):
    return dict(text=title_case(text), x=0, xanchor="left")


def _resp_label(fiscal_t) -> str:
    mode, theta, _, alloc, ceiling = fiscal_t
    lbl = {"none": "No backfill", "historical": "Historical behaviour", "custom": f"Government replaces {theta:.0%}",
           "max": "As much as fiscal space allows"}[mode]
    if mode != "none":
        lbl += (", lives first" if alloc == "lives_first" else ", pro-rata")
        lbl += (", best-years ceiling" if ceiling == "p90" else "")
    return title_case(lbl)


# --------------------------------------------------------------------------- #
# Sidebar controls
# --------------------------------------------------------------------------- #
def _preset_options(preset, ci, iso3, country_name, key):
    opts = scn.default_opts(preset, ci)
    if preset == "America First MOUs":
        opts["mou_year"] = st.select_slider("MOU Year", options=[2026, 2027, 2028, 2029, 2030],
                                            value=scn.DEFAULT_MOU_YEAR, key=f"{key}_mouy")
        avg = scn.mou_average_cut_pct(ci, opts["mou_year"])
        opts["non_mou_cut"] = st.slider("US Cut Where There Is No MOU Schedule (%)", 0, 100, avg, 1,
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


def _controls(iso3, country_name, I) -> dict:
    """Control bar at the top of Section 4: scenario | government response | Advanced (popover)."""
    ci = I["ci"]
    ctx = st.session_state.get("model_ctx", {})
    if st.session_state.get("m_preset") not in PRESETS:          # seed once from the other page's choice
        st.session_state["m_preset"] = ctx.get("preset", list(PRESETS)[0])
    if "m_trend" not in st.session_state:
        st.session_state["m_trend"] = ctx.get("trend", scn.DEFAULT_MORTALITY_TREND)
    if st.session_state.get("m_mode") not in GOV_MODES:          # e.g. an option from an older version of the page
        st.session_state["m_mode"] = list(GOV_MODES)[0]
    th_c, th_lo, th_hi = hm.theta_historical(I["reg"])
    with st.container(key="model_controls", border=True):
        c1, c2, c3 = st.columns([1.45, 1.25, 0.8], gap="medium")
        with c1:
            preset = st.selectbox("Donor Scenario", list(PRESETS), key="m_preset", format_func=title_case,
                                  help=_esc(PRESETS[st.session_state["m_preset"]]))      # full description
            st.caption(_esc(PRESET_SHORT.get(preset, PRESETS[preset])))
            opts = _preset_options(preset, ci, iso3, country_name, "m")
        with c2:
            mode = GOV_MODES[st.radio(
                "Government Response", list(GOV_MODES), key="m_mode", format_func=title_case,
                help=_esc(f"How much of the lost aid the government replaces from its own budget. No Backfill is the "
                          f"historical norm: across 97 countries, 2001-2023, governments did not replace falling aid "
                          f"({th_c:+.2f} per $1, 95% CI {th_lo:+.2f} to {th_hi:+.2f})."))]
            theta = 0.0
            if mode == "custom":
                theta = st.slider("Share of Lost Aid Replaced (%)", 0, 100, 25, 5, key="m_theta") / 100
        with c3:
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
                                    help="Lives first refills the services that avert the most deaths per dollar first "
                                         "(usually TB treatment, vaccines, ART) before anything else.")]
            cap = st.checkbox("Cap Replacement at Fiscal Space", value=True, key="m_cap",
                              disabled=(mode in ("none", "max")))
            trend = st.toggle("Account for Already-Falling Death Rates", key="m_trend",
                              help="Baseline malaria deaths and under-5 mortality keep falling at each country's "
                                   "2010-2019 rate during the five years, so the same lost service costs fewer lives in "
                                   "later years. Where a country has no usable trend, -0.9% a year is used (Cavalcanti "
                                   "et al. 2025, Lancet, appendix 10.2). TB and HIV treatment effects are per patient "
                                   "and unchanged.")
            st.divider()
            cmp = None
            if st.toggle("Compare with a Second Scenario", value=False, key="m_compare"):
                options_b = ["Same as Scenario A"] + scn.PRECOMPUTED_PRESETS
                pb = st.selectbox("Donor Scenario (B)", options_b, index=0, key="mb_preset", format_func=title_case)
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
                                          index=list(ALLOCS).index("Lives first (triage)"), key="mb_alloc",
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

    return {"preset": preset, "opts": opts, "fiscal_t": (mode, theta, cap, alloc, ceiling), "mode": mode,
            "ptab": ptab, "ptab_json": ptab.to_json(orient="split"), "cmp": cmp, "trend": trend}


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
INTRO = ("A four-step model for HIV, TB, malaria and immunization: the donor scenario removes aid; the government "
         "can replace part of it, limited by fiscal space; money not replaced ÷ cost per person = people who lose a "
         "service; and each lost service x its effect on mortality = extra deaths. Ranges are 95% intervals from 400 "
         "Monte Carlo draws.")


def render_model_section(iso3: str, country_name: str, imf: dict | None = None, names: dict | None = None):
    names = names or {}
    I = _inputs()
    ci = I["ci"]
    th.section_header("monitor_heart", f"How Aid Cuts Translate into Coverage and Lives in {country_name}",
                      "If donors cut funding, how many people lose services, and how many more die?", help=INTRO)
    ctl = _controls(iso3, country_name, I)
    preset, fiscal_t, ptab_json = ctl["preset"], ctl["fiscal_t"], ctl["ptab_json"]
    sk = scn.scenario_key(scn.build_scenario(preset, ctl["opts"], ci))
    st.session_state["model_ctx"] = {"iso3": iso3, "country_name": country_name, "preset": preset, "opts": ctl["opts"],
                                     "fiscal_t": fiscal_t, "ptab_json": ptab_json, "trend": ctl["trend"]}

    if iso3 not in ci.index or iso3 not in set(I["lines"].iso3):
        st.info(f"{country_name} has no recorded HIV, TB, malaria or vaccine aid in 2021-2023, so there is nothing to "
                "model for this country. The all-country results are below.")
    else:
        _country_results(iso3, country_name, ctl, sk, imf or {})

    _cross_country(sk, ctl, iso3, names)


def _country_results(iso3, country_name, ctl, sk, imf):
    preset, fiscal_t, ptab, ptab_json, mode = ctl["preset"], ctl["fiscal_t"], ctl["ptab"], ctl["ptab_json"], ctl["mode"]
    trend = ctl["trend"]
    res = _run(iso3, sk, fiscal_t, ptab_json, trend)
    res0 = _run(iso3, sk, scn.DEFAULT_FISCAL, ptab_json, trend) if mode != "none" else res
    T, B, L = res["totals"], res["buckets"].set_index("bucket"), res["lines"]

    if T.get("gains", 0) > 1e5:
        st.info(_esc(f"Some aid increases in this scenario (+{money(T['gains'])} a year); those gains count as coverage "
                     "and lives gained and partly offset the losses below."))
    if T["gross"] <= 0 and T["base"] > 0:
        st.success(_esc(f"Under '{preset}' {country_name} loses no HIV, TB, malaria or vaccine aid "
                        f"(net change {money(-T['gross'])})."))

    show = L[(L["base_usd"] > 0) | (L["net_loss_usd"] != 0)].copy()
    rows = _service_rows(show)
    cov_fig = _coverage_fig(rows)
    path_fig = _path_fig(res)
    cards = _per_million_cards(res, ptab)
    items = _headline_items(res)

    # ------------------------------ headline ------------------------------ #
    if ctl["cmp"]:
        _comparison(iso3, country_name, ctl, res, items)
    else:
        st.subheader("The Headline")
        st.caption(_esc(f"{title_case(preset)} · {_resp_label(fiscal_t)}"))
        _stat_grid(items, 3)
    if mode != "none" and T["replaced"] > 0:
        saved = res0["totals"]["deaths_5y"] - T["deaths_5y"]
        st.markdown(_esc(f"Government backfill of {money(T['replaced'])} a year averts about **{num(saved)} deaths over "
                         f"5 years** compared with no backfill ({money(T['replaced'] * 5 / max(saved, 1))} per death "
                         "averted)."))
    if SHOW_BRIEF:
        st.download_button(
            "Download Country Brief", icon=":material/download:",
            data=_brief_html(country_name, preset, _resp_label(fiscal_t), items, cards,
                             [cov_fig, path_fig]).encode("utf-8"),
            file_name=f"{country_name.replace(' ', '_')}_funding_cut_brief.html", mime="text/html", key="m_brief",
            help="A one-page HTML summary of this scenario. Open it in a browser and print to PDF.")

    # ------------------------------ per $1M ------------------------------ #
    st.subheader(_esc("Every US$1 Million Lost, by Bucket"),
                 help="Coverage drop per $1M is linear, and so are deaths, except for malaria, where the Lives Saved "
                      "Tool equations make each extra point of lost coverage slightly worse.")
    cols = st.columns(4)
    for col, c in zip(cols, cards):
        col.markdown(_card_html(c), unsafe_allow_html=True)
    st.caption(_esc(f"What US$1M of aid cut every year for five years, and not replaced, does in {country_name}, using "
                    "the main service in each bucket (malaria: bednets)."))

    # ------------------------------ where the money is lost ------------------------------ #
    st.subheader("Where the Money Is Lost")
    cells = res["cells"]
    cl = cells[cells["loss"] > 0]
    if cl.empty:
        st.info("No aid is cut in this scenario.")
    else:
        a, b = st.columns(2)
        with a:
            chart(_loss_by_bucket_fig(B))
        with b:
            chart(_who_cut_fig(cl))
        st.caption(("The lighter part of each bar is what the government replaces. " if T["replaced"] > 0 else "")
                   + "Donors are who originally paid, by the channel the money went through: a US cut to the Global "
                     "Fund is 'US · Global Fund'.")

    # ------------------------------ service table ------------------------------ #
    notes = []
    if show["capped"].any():
        notes.append("Where the aid lost would pay for more people than are covered today, the loss is capped at "
                     "current coverage.")
    notes += [f"{f[0].upper() + f[1:]}." for f in res["flags"]]
    notes.append("HIV prevention turns money into infections averted (no deaths within 5 years). Program money with no "
                 "reported purpose is spread over each bucket's known mix, and "
                 f"{float(ptab.loc['hss_kappa', 'central']):.0%} of lost systems money (labs, staff, monitoring) is "
                 "assumed to cut services. Bednets and spraying protect the same population at risk, so they share one "
                 "row. Deaths ranges are 95% intervals.")
    st.subheader("What Each Service Loses", help=" ".join(notes))
    st.markdown(_service_table_html(rows), unsafe_allow_html=True)
    ovc = show[show["line"] == "hiv_ovc"]
    if len(ovc) and ovc["net_loss_usd"].sum() > 0:
        st.caption(_esc(f"Excludes support for orphans and vulnerable children ({money(ovc['net_loss_usd'].sum())} a "
                        "year lost), which has no modelled effect on deaths."))
    if cov_fig is not None:
        chart(cov_fig)

    # ------------------------------ dose response + path ------------------------------ #
    st.subheader("How the Damage Scales",
                 help="Left: a uniform cut across all donors to one bucket, with the chosen government response; it "
                      "flattens once everyone whose service donors pay for has lost it, and bends where backfill runs "
                      "out of fiscal space. Right: deaths after losing HIV treatment rise from about 1% to 5% a year, "
                      "unvaccinated birth cohorts add up, and nets already hanging protect for about a year.")
    d1, d2 = st.columns(2)
    with d1:
        bsel = st.radio("Bucket", hm.BUCKETS, horizontal=True, key="m_dose_b")
        dr = _dose(iso3, bsel, fiscal_t, ptab_json, trend)
        base_b = B.loc[bsel, "base_usd"]
        cur_cut = B.loc[bsel, "gross_loss_usd"] / base_b if base_b > 0 else 0
        if base_b > 0:
            per10 = float(dr["deaths_5y"].iloc[-1]) / 10
            st.markdown(f"In {country_name}, every 10% of {BUCKET_WORD[bsel]} aid cut adds about **{num(per10)}** "
                        "extra deaths over 5 years.")
        else:
            st.markdown(f"{country_name} receives no {BUCKET_WORD[bsel]} aid in the model, so cutting it changes nothing.")
        chart(_dose_fig(dr, bsel, cur_cut, B.loc[bsel]))
        st.caption("The shaded band is the 95% uncertainty range. It widens as the cut grows because every uncertain "
                   "input (unit costs, mortality effects) applies to more people losing services, so the absolute "
                   "uncertainty grows with the cut.")
    with d2:
        band = res["path_band"]
        st.markdown(_esc(f"Over {FIRST_YEAR}-{FIRST_YEAR + 4} this scenario adds about **{num(T['deaths_5y'])}** "
                         f"extra deaths in {country_name} (range {rng(band['lo'].iloc[-1], band['hi'].iloc[-1])})."))
        # keep the two charts level with each other (the left column has a bucket picker above its chart)
        st.markdown("<div style='height:2.6rem'></div>", unsafe_allow_html=True)
        chart(path_fig)
    st.caption("The 10% figure is the average along the curve; deaths build up over the five years.")

    # ------------------------------ fiscal space ------------------------------ #
    _fiscal_panel(res, country_name, imf)
    return res


# --------------------------------------------------------------------------- #
# Headline, comparison, cards
# --------------------------------------------------------------------------- #
def _headline_items(res) -> list:
    T, B = res["totals"], res["buckets"].set_index("bucket")
    items = [
        ("Aid at Risk (per Year)", money(T["gross"]),
         f"{T['gross'] / T['base']:.0%} of {money(T['base'])} for these four buckets" if T["base"] else None,
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
    return [(title_case(lbl), val, title_case(sub), hlp) for lbl, val, sub, hlp in items]


def _comparison(iso3, country_name, ctl, res_a, items_a):
    c = ctl["cmp"]
    ci = _inputs()["ci"]
    sk_b = scn.scenario_key(scn.build_scenario(c["preset"], c["opts"], ci))
    res_b = _run(iso3, sk_b, c["fiscal_t"], ctl["ptab_json"], ctl["trend"])
    st.subheader("Scenario A vs Scenario B")
    a, b = st.columns(2, gap="large")
    for col, tag, preset, fiscal_t, items in ((a, "A", ctl["preset"], ctl["fiscal_t"], items_a),
                                              (b, "B", c["preset"], c["fiscal_t"], _headline_items(res_b))):
        with col:
            st.markdown(_esc(f"**Scenario {tag}:** {title_case(preset)} · {_resp_label(fiscal_t)}"))
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
    _layout(fig, h=340, title=_title("Extra Deaths Over 5 Years by Disease: Scenario A vs B"),
            legend=dict(orientation="h", y=-0.12, x=0, yanchor="top"),
            yaxis=dict(title="extra deaths, 5 years", rangemode="tozero"))
    chart(fig)


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
        out.append({"bucket": b, "color": BUCKET_COLORS[b], "service": title_case(hm.LINE_LABELS[line]),
                    "people": f"{num(per_m_units)} {ln['unit_label']} lose the service",       # a sentence (brief)
                    "people_n": num(per_m_units), "unit": ln["unit_label"],
                    "cov_n": "n/a" if np.isnan(dpp) else f"{dpp:,.2f}",
                    "coverage": "n/a" if np.isnan(dpp) else f"{dpp:,.2f} Percentage Points",
                    "deaths": f"{d_per:,.0f}",
                    "foot": title_case(f"Cost {money(uc)} per {hm.UNIT_SINGULAR[line]} · "
                                       f"{money(5e6 / d_per) if d_per > 0 else 'n/a'} of aid per death")})
    return out


def _card_html(c) -> str:
    """Three big numbers per bucket, with small labels; cost per person and aid per death underneath."""
    e = html.escape
    return (f"<div class='ed-card' style='border-top-color:{c['color']}'>"
            f"<div class='t'>{e(c['bucket'])}</div><div class='s'>{e(c['service'])}</div>"
            f"<div class='big'>{e(c['people_n'])}</div><div class='lbl'>People Losing the Service "
            f"({e(c['unit'])})</div>"
            f"<div class='big'>{e(c['cov_n'])}</div><div class='lbl'>Coverage Drop (Percentage Points)</div>"
            f"<div class='big'>{e(c['deaths'])}</div><div class='lbl'>Extra Deaths Over 5 Years</div>"
            f"<div class='foot'>{e(c['foot'])}</div></div>").replace("$", "&#36;")


# --------------------------------------------------------------------------- #
# Charts and tables
# --------------------------------------------------------------------------- #
def _loss_by_bucket_fig(B: pd.DataFrame):
    """Aid lost per disease in the disease colour; the part the government replaces in the same colour at 40%."""
    bk = [b for b in hm.BUCKETS if B.loc[b, "gross_loss_usd"] > 0][::-1]
    rep = [max(B.loc[b, "replaced_usd"], 0.0) for b in bk]
    lost = [max(B.loc[b, "gross_loss_usd"] - B.loc[b, "replaced_usd"], 0.0) for b in bk]
    fig = go.Figure()
    for name, vals, alpha in (("Lost to services", lost, 1.0), ("Replaced by government", rep, REPLACED_ALPHA)):
        fig.add_trace(go.Bar(y=bk, x=vals, name=name, orientation="h",
                             marker=dict(color=[th.tint(BUCKET_COLORS[b], alpha) for b in bk]),
                             customdata=[money(v) for v in vals], showlegend=False,
                             hovertemplate=f"%{{y}} · {name}: %{{customdata}} a year<extra></extra>"))
    tot = [r + l for r, l in zip(rep, lost)]
    fig.add_trace(go.Scatter(y=bk, x=tot, mode="text", text=[money(t) for t in tot], textposition="middle right",
                             textfont=dict(color=INK), showlegend=False, hoverinfo="skip"))
    fig.update_layout(barmode="stack", bargap=0.35)
    _layout(fig, h=360, title=_title("Aid Lost per Year, by Disease"), margin=dict(l=10, r=70, t=50, b=10),
            xaxis=dict(showticklabels=False, showgrid=False, range=[0, max(tot) * 1.25]),
            yaxis=dict(showgrid=False))
    return fig


SRC_SHORT = {"United States": "US", "United Kingdom": "UK", "Gates Foundation": "Gates"}
CHAN_SHORT = {"Bilateral agency": "Bilateral", "Gates direct": "Direct", "Development banks": "Dev. Banks"}
MAX_WHO_CUT_BARS = 12


def _who_cut_fig(cl: pd.DataFrame):
    """One bar per donor x channel ('US · Bilateral'), in the funder's colour, largest at the top."""
    d = cl.groupby(["src_grp", "chan_grp"])["loss"].sum().sort_values(ascending=False)
    d = d[d > 0]
    if len(d) > MAX_WHO_CUT_BARS:                   # keep the chart readable: the rest as one grey bar
        d = pd.concat([d.iloc[:MAX_WHO_CUT_BARS - 1],
                       pd.Series([d.iloc[MAX_WHO_CUT_BARS - 1:].sum()], index=[("All other", "")])])
    labels = [f"{SRC_SHORT.get(s, s)} · {CHAN_SHORT.get(c, c)}" if c else s for s, c in d.index]
    colors = [th.funder_color(s) if c else th.OTHER for s, c in d.index]
    labels, vals, colors = labels[::-1], d.values[::-1], colors[::-1]
    fig = go.Figure(go.Bar(y=labels, x=vals, orientation="h", marker=dict(color=colors),
                           text=[money(v) for v in vals], textposition="outside", cliponaxis=False,
                           textfont=dict(color=INK), hovertemplate="<b>%{y}</b>: %{text} a year<extra></extra>"))
    fig.update_layout(bargap=float(np.clip(1 - 34 * len(d) / 280, 0.25, 0.7)))
    _layout(fig, h=max(360, 80 + 34 * len(d)), title=_title("Who Cut the Money"),
            margin=dict(l=10, r=80, t=50, b=10), xaxis=dict(showticklabels=False, showgrid=False,
                                                            range=[0, float(d.max()) * 1.3]),
            yaxis=dict(showgrid=False))
    return fig


SUM_COLS = ["base_usd", "gross_loss_usd", "replaced_usd", "net_loss_usd", "units_lost", "cov_drop_pp", "deaths_y1",
            "deaths_5y", "deaths_5y_lo", "deaths_5y_hi"]


def _service_rows(show: pd.DataFrame) -> pd.DataFrame:
    """Lines as shown to readers: bednets and indoor spraying merged (same population at risk, so their coverage drops
    add up; ranges are added, which slightly widens them), and support for orphans and vulnerable children dropped
    (it has no modelled effect on deaths)."""
    d = show[show["line"] != "hiv_ovc"].copy()
    d["cost_txt"] = [f"{money(r.unit_cost)} per {hm.UNIT_SINGULAR[r.line]}" for r in d.itertuples()]
    if {"mal_itn", "mal_irs"} <= set(d["line"]):
        itn, irs = d[d["line"] == "mal_itn"].iloc[0], d[d["line"] == "mal_irs"].iloc[0]
        row = itn.copy()
        for c in SUM_COLS:
            row[c] = np.nansum([itn[c], irs[c]])
        row["label"] = "Bednets & spraying"
        row["capped"] = bool(itn["capped"] or irs["capped"])
        row["cost_txt"] = f"{money(itn['unit_cost'])} (nets), {money(irs['unit_cost'])} (spraying) per person-year"
        d = d[~d["line"].isin(["mal_itn", "mal_irs"])]
        d = pd.concat([d, row.to_frame().T]).sort_index()
        for c in SUM_COLS + ["need", "cov0", "unit_cost"]:
            d[c] = pd.to_numeric(d[c])
    return d


def _service_table_html(rows: pd.DataFrame) -> str:
    """'What Each Service Loses' as an HTML table: money right-aligned, the coverage drop in rose."""
    e = html.escape

    def cov_change(r):
        if pd.isna(r.need) or pd.isna(r.cov0):
            return "n/a"
        after = max(r.cov0 - r.cov_drop_pp / 100, 0)
        dpts = (after - r.cov0) * 100
        pts = f"{dpts:+.0f}" if abs(dpts) >= 1 else f"{dpts:+.1f}"
        return f"{r.cov0:.0%} → {after:.0%} <span class='drop'>({pts.replace('-', '−')} pts)</span>"

    head = [("Service", ""), ("Aid Today (per Yr)", "num"), ("Aid Lost After Backfill", "num"), ("Cost per Person", ""),
            ("People Losing Service", "num"), ("Coverage Change", "cov"), ("Deaths, 5 Years (Range)", "num")]
    body = []
    for r in rows.itertuples():
        cells = [(e(title_case(r.label)), ""), (money(r.base_usd), "num"), (money(r.net_loss_usd), "num"),
                 (e(title_case(r.cost_txt)), ""), (num(r.units_lost), "num"), (cov_change(r), "cov"),
                 (f"{num(r.deaths_5y)}<br><span style='color:{th.MUTED};font-size:12px'>"
                  f"{rng(r.deaths_5y_lo, r.deaths_5y_hi)}</span>", "num")]
        body.append("<tr>" + "".join(f"<td class='{c}'>{v}</td>" for v, c in cells) + "</tr>")
    return ("<div class='ed-table-wrap'><table class='ed-table'><thead><tr>"
            + "".join(f"<th class='{c}'>{h}</th>" for h, c in head) + "</tr></thead><tbody>"
            + "".join(body) + "</tbody></table></div>").replace("$", "&#36;")


def _coverage_fig(rows: pd.DataFrame):
    """Coverage now (hollow) and after the cut (filled), one row per service, largest drop at the top."""
    d = rows[rows["need"].notna() & rows["cov0"].notna()].copy()
    if d.empty:
        return None
    d["after"] = (d["cov0"] - d["cov_drop_pp"] / 100).clip(0, 1)
    d["drop"] = (d["cov0"] - d["after"]) * 100
    d = d.sort_values("drop")                      # plotly draws the first row at the bottom
    d["label"] = d["label"].map(title_case)
    cols = [BUCKET_COLORS[b] for b in d["bucket"]]
    fig = go.Figure()
    for r, col in zip(d.itertuples(), cols):
        fig.add_trace(go.Scatter(x=[r.after * 100, r.cov0 * 100], y=[r.label, r.label], mode="lines",
                                 line=dict(color=col, width=4), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=d["cov0"] * 100, y=d["label"], mode="markers", name="Coverage now",
                             marker=dict(size=16, color=th.SURFACE, line=dict(color=cols, width=3)),
                             hovertemplate="%{y}<br>now: %{x:.0f}%<extra></extra>"))
    fig.add_trace(go.Scatter(x=d["after"] * 100, y=d["label"], mode="markers", name="After the cut",
                             marker=dict(size=16, color=cols, line=dict(color=th.SURFACE, width=2)),
                             hovertemplate="%{y}<br>after: %{x:.0f}%<extra></extra>"))
    for r in d.itertuples():                       # the drop, at the low end of each line
        if r.drop < 0.05:
            continue
        txt = f"−{r.drop:.0f} pts" if r.drop >= 1 else f"−{r.drop:.1f} pts"
        left = r.after >= 0.16
        fig.add_annotation(x=r.after * 100, y=r.label, text=f"<b>{txt}</b>", showarrow=False,
                           xanchor="right" if left else "left", xshift=-14 if left else 14,
                           yshift=0 if left else 18, font=dict(color=th.ROSE, size=15))
    _layout(fig, h=110 + 56 * len(d), title=_title("Coverage Before and After the Cut (% of People in Need)"),
            legend=dict(orientation="h", y=-0.08, x=0, yanchor="top"),
            xaxis=dict(range=[-4, 104], ticksuffix="%", showgrid=True, gridcolor=th.RULE),
            yaxis=dict(showgrid=False))
    return fig


def _dose_fig(dr: pd.DataFrame, bucket: str, cur_cut: float, bb: pd.Series):
    col = BUCKET_COLORS[bucket]
    fill = th.tint(col, 0.15)
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
                                 marker=dict(size=13, color=col, line=dict(color=th.SURFACE, width=2)),
                                 hovertemplate="this scenario: %{x:.0f}% cut, %{y:,.0f} deaths<extra></extra>"))
        fig.add_annotation(x=cur_cut * 100, y=bb["deaths_5y"], text=f"This scenario: {cur_cut:.0%} cut,<br>"
                                                                    f"{num(bb['deaths_5y'])} deaths",
                           showarrow=True, arrowhead=0, arrowcolor=MUTED, ax=-60 if cur_cut > 0.5 else 60, ay=-40,
                           font=dict(color=INK, size=12), bgcolor=th.tint(th.SURFACE, 0.85), align="left")
    _layout(fig, h=400, title=_title("Extra Deaths as More Aid Is Cut"), showlegend=False,
            xaxis=dict(title="Share of this bucket's aid cut", ticksuffix="%"),
            yaxis=dict(title="extra deaths over 5 years", rangemode="tozero"))
    return fig


def _path_fig(res: dict):
    p = res["path"]
    years = [str(FIRST_YEAR + i - 1) for i in p.index]
    fig = go.Figure()
    for b in hm.BUCKETS:
        fig.add_trace(go.Bar(x=years, y=p[b], name=b, marker=dict(color=BUCKET_COLORS[b]),
                             hovertemplate=f"{b}<br>%{{x}}: %{{y:,.0f}} extra deaths<extra></extra>"))
    fig.update_layout(barmode="stack", bargap=0.35)
    _layout(fig, h=400, title=_title(f"Extra Deaths Each Year, {FIRST_YEAR}-{FIRST_YEAR + 4}"),
            legend=dict(orientation="h", y=-0.12, x=0), yaxis=dict(title="extra deaths in that year"),
            xaxis=dict(type="category"))
    return fig


def _fiscal_sentence(F: dict, country_name: str) -> str:
    """One sentence from the data: how big the gap is against the health budget, and what a strong year would cover."""
    G, ghes, cap = F["gross_loss"], F["ghes"], F["capacity"]
    if not G or G <= 0:
        return "No aid is lost in this scenario, so there is no gap to fill."
    out = f"Replacing the lost aid would take a {G / ghes:.0%} increase in government health spending. " if ghes else ""
    pts = (F["ghes_growth_top"] - max(F["ghes_growth_median"], 0)) * 100
    year = "its best years" if F["effort"] == "p90" else "a strong year"
    if pd.isna(pts) or pts <= 0 or not cap or cap <= 0:
        return out + f"{country_name}'s health budget does not grow faster than usual even in {year}, so it has no room " \
                     "to fill the gap."
    pts_txt = f"{pts:.0f}" if pts >= 1 else f"{pts:.1f}"
    out += (f"In {year} {country_name}'s health budget grows about {pts_txt} point{'s' if pts_txt != '1' else ''} "
            "faster than usual, which ")
    out += f"would cover the whole {money(G)} gap." if cap >= G else f"would cover {money(cap)} of the {money(G)} gap."
    return out


def _fiscal_panel(res: dict, country_name: str, imf: dict):
    F = res["fiscal"]
    stress = (f" High interest costs shrink it: interest takes {F['interest_pct_revenue']:.0f}% of revenue, so the "
              f"debt-stress factor is {F['stress_factor']:.2f} (1 at 10% or less, falling to 0.25 at 40%)."
              if not pd.isna(F["interest_pct_revenue"]) else "")
    st.subheader(f"Can {country_name} Fill the Gap?",
                 help=_esc("Backfill capacity = government health spending x (strong-year growth minus typical growth) "
                           "x a debt-stress factor." + stress + " Growth rates are real (constant 2023 US$) from IHME, "
                           "2001-2023; interest and revenue are World Bank WDI, latest year (IMF data fill gaps)."))
    rev = F["revenue"]
    if (pd.isna(rev) or not rev) and imf.get("revenue_pct_gdp") and F["gdp"]:
        rev = imf["revenue_pct_gdp"] / 100 * F["gdp"]
    G = F["gross_loss"]
    st.markdown(th.pills_html([
        ("Government Health Spending (2023)", money(F["ghes"]),
         "IHME, constant 2023 US$",
         f"${F['ghes_pc']:,.0f} per person · {F['ghes_pct_gdp']:.1f}% of GDP" if not pd.isna(F["ghes_pc"]) else ""),
        ("Aid Lost as % of Government Health Spending", f"{G / F['ghes']:.0%}" if F["ghes"] else "n/a",
         "Gross aid lost per year ÷ government health spending, 2023", ""),
        ("Aid Lost as % of Government Revenue", f"{G / rev:.1%}" if rev and not pd.isna(rev) else "n/a",
         "Gross aid lost per year ÷ total government revenue", ""),
        ("Health Share of Government Spending",
         f"{F['ghes_pct_gov_spend']:.1f}%" if not pd.isna(F["ghes_pct_gov_spend"]) else "n/a",
         "Government health spending ÷ all government spending", "Abuja Target: 15%"),
    ], large=True), unsafe_allow_html=True)
    st.markdown(_esc(_fiscal_sentence(F, country_name)))
    typical = F["ghes"] * max(F["ghes_growth_median"], 0)
    bars = [(title_case(lbl), v, c) for lbl, v, c in (
            ("Aid lost (gross, per year)", G, LOSS),
            ("Backfill capacity (fiscal space)", F["capacity"], BACKFILL),
            ("Backfill applied in this run", F["replacement"], th.tint(BACKFILL, 0.55)),
            ("One year of typical growth in<br>government health spending", typical, th.OTHER))]
    fig = go.Figure(go.Bar(y=[b[0] for b in bars][::-1], x=[b[1] for b in bars][::-1], orientation="h",
                           marker=dict(color=[b[2] for b in bars][::-1]),
                           text=[money(b[1]) for b in bars][::-1], textposition="outside", cliponaxis=False,
                           textfont=dict(color=INK), hovertemplate="%{y}: %{text}<extra></extra>"))
    _layout(fig, h=300, title=_title("The Gap vs. What the Budget Can Absorb (US$ per Year)"),
            xaxis=dict(showticklabels=False, showgrid=False), yaxis=dict(showgrid=False),
            margin=dict(l=10, r=80, t=50, b=10))
    chart(fig)


# --------------------------------------------------------------------------- #
# Across all countries
# --------------------------------------------------------------------------- #
def _all_country_results(sk, ctl) -> pd.DataFrame:
    """Precomputed file when the settings are the defaults it was built with; otherwise run live."""
    preset, ptab = ctl["preset"], ctl["ptab"]
    path = scn.precomputed_path(hm.MODEL_DIR, preset)
    if (preset in scn.PRECOMPUTED_PRESETS and path.exists() and ctl["fiscal_t"] == scn.DEFAULT_FISCAL
            and ctl["trend"] == scn.DEFAULT_MORTALITY_TREND):
        ci = _inputs()["ci"]
        default_sk = scn.scenario_key(scn.build_scenario(preset, scn.default_opts(preset, ci), ci))
        p0 = _default_params()
        same_params = ptab[["central", "low", "high"]].astype(float).reindex(p0.index).equals(
            p0[["central", "low", "high"]].astype(float))
        if sk == default_sk and same_params:
            return _precomputed(str(path), path.stat().st_mtime)
    return _run_all(sk, ctl["fiscal_t"], ctl["ptab_json"], ctl["trend"])


def _cross_country(sk, ctl, iso3, names) -> pd.DataFrame:
    th.section_header("travel_explore", "Across All Countries: Who Is Most Exposed?",
                      "Which countries lose the most, relative to their own budgets and populations?")
    A = _all_country_results(sk, ctl).copy()
    A["name"] = A["iso3"].map(lambda c: names.get(c, c))
    A = A[A["gross_loss_usd"] > 0].copy()
    if A.empty:
        st.info("No country loses aid in this scenario.")
        return A
    st.caption(_esc(f"{title_case(ctl['preset'])} · {_resp_label(ctl['fiscal_t'])}"
                    + ("" if ctl["trend"] else " · Death Rates Held Constant")))
    tot = A[["gross_loss_usd", "net_loss_usd", "deaths_y1", "deaths_5y", "deaths_5y_lo", "deaths_5y_hi", "hiv_infections_5y"]].sum()
    st.markdown(th.pills_html([
        (f"Aid Lost per Year, {len(A)} Countries", money(tot["gross_loss_usd"]),
         "HIV, TB, malaria and vaccine aid removed by the scenario", f"Net of Backfill {money(tot['net_loss_usd'])}"),
        ("Extra Deaths, Year 1", num(tot["deaths_y1"]), "Deaths build up over the five years", ""),
        ("Extra Deaths Over 5 Years", num(tot["deaths_5y"]),
         "Totals add up country results; the range adds country 2.5th and 97.5th percentiles, so it is wider than a "
         "jointly simulated interval.", "Range " + rng(tot["deaths_5y_lo"], tot["deaths_5y_hi"])),
        ("New HIV Infections, 5 Years", num(tot["hiv_infections_5y"]), "From lost HIV prevention and treatment", ""),
    ], large=True), unsafe_allow_html=True)
    A["deaths_per_100k"] = A["deaths_5y"] / A["pop"] * 1e5
    A["loss_pct_ghes_pct"] = A["loss_pct_ghes"] * 100

    _, tcol = st.columns([5, 1])
    world = tcol.toggle("World", value=False, key="m_map_world", help="Show the whole world instead of Africa and Asia")
    chart(_world_map(A, iso3, world))
    st.caption("The map's colour scale stops at the 95th percentile so a few extreme countries don't wash out the rest.")

    c1, c2 = st.columns([1.15, 1])
    with c1:
        d = A[(A["loss_pct_ghes_pct"] > 0) & (A["deaths_per_100k"] > 0)]
        fig = go.Figure()
        other = d[d["iso3"] != iso3]
        sz = np.sqrt(d["net_loss_usd"].clip(lower=1)) / np.sqrt(d["net_loss_usd"].max()) * 40 + 6
        top10 = set(d.nlargest(SCATTER_LABELS, "deaths_per_100k")["iso3"])      # label only these
        fig.add_trace(go.Scatter(x=other["loss_pct_ghes_pct"], y=other["deaths_per_100k"], mode="markers+text",
                                 text=[c if c in top10 else "" for c in other["iso3"]],
                                 textposition="top center", textfont=dict(size=11, color=INK),
                                 marker=dict(size=sz[d["iso3"] != iso3], color=th.GRAPE, opacity=0.5,
                                             line=dict(color=th.SURFACE, width=1)),
                                 customdata=np.c_[other["name"], other["net_loss_usd"].map(money), other["deaths_5y"].map(num)],
                                 hovertemplate="<b>%{customdata[0]}</b><br>aid loss = %{x:.0f}% of government health "
                                               "spending<br>%{y:,.0f} deaths per 100,000 over 5 years "
                                               "(%{customdata[2]})<br>net loss %{customdata[1]} a year<extra></extra>",
                                 name="Countries"))
        me = d[d["iso3"] == iso3]
        if len(me):
            fig.add_trace(go.Scatter(x=me["loss_pct_ghes_pct"], y=me["deaths_per_100k"], mode="markers+text", text=[iso3],
                                     textposition="top center", textfont=dict(size=13, color=INK),
                                     marker=dict(size=sz[d["iso3"] == iso3], color=th.BRAND, line=dict(color=th.SURFACE, width=2)),
                                     hoverinfo="skip", name="Selected country"))
        fig.add_vline(x=d["loss_pct_ghes_pct"].median(), line=dict(color=GRID, width=1, dash="dot"))
        fig.add_hline(y=d["deaths_per_100k"].median(), line=dict(color=GRID, width=1, dash="dot"))
        _layout(fig, h=480, title=_title("Budget Exposure vs. Deaths per Person"), showlegend=False,
                xaxis=dict(type="log", title="aid lost as % of government health spending (log)", ticksuffix="%",
                           tickvals=LOG_TICKS, ticktext=[f"{v:g}" for v in LOG_TICKS]),
                yaxis=dict(type="log", title="extra deaths per 100,000 people over 5 years (log)",
                           tickvals=LOG_TICKS, ticktext=[f"{v:g}" for v in LOG_TICKS]))
        chart(fig)
    with c2:
        top = A.sort_values("deaths_5y", ascending=False).head(15).iloc[::-1]
        fig = go.Figure()
        for b in hm.BUCKETS:
            fig.add_trace(go.Bar(y=top["name"], x=top[f"deaths_5y_{b}"], name=b, orientation="h",
                                                  marker=dict(color=BUCKET_COLORS[b]),
                                 hovertemplate=f"%{{y}} · {b}: %{{x:,.0f}}<extra></extra>"))
        fig.update_layout(barmode="stack")
        _layout(fig, h=480, title=_title("15 Countries with the Most Extra Deaths (5 Years)"),
                legend=dict(orientation="h", y=-0.1, x=0))
        chart(fig)
    st.caption("Bubble size is net aid lost per year and dotted lines are medians: countries in the top right lose the "
               "most relative to their own health budgets and populations.")
    return A


def _world_map(A: pd.DataFrame, iso3: str, world: bool = False):
    zmax = float(A["deaths_per_100k"].quantile(0.95))
    pct = A["loss_pct_ghes_pct"].map(lambda v: "n/a" if pd.isna(v) else f"{v:,.0f}%")
    fig = go.Figure(go.Choropleth(
        locations=A["iso3"], z=A["deaths_per_100k"], locationmode="ISO-3", zmin=0, zmax=zmax,
        colorscale=[[i / (len(th.MAP_RAMP) - 1), c] for i, c in enumerate(th.MAP_RAMP)],
        marker_line_color=th.SURFACE, marker_line_width=0.5,
        colorbar=dict(orientation="h", title=dict(text="Extra Deaths per 100,000 (5 Years)", side="top",
                                                  font=dict(size=12, color=MUTED)),
                      thickness=10, len=0.45, x=0.5, xanchor="center", y=-0.02, yanchor="top",
                      tickfont=dict(size=11, color=MUTED), outlinewidth=0),
        customdata=np.c_[A["name"], A["gross_loss_usd"].map(money), A["deaths_5y"].map(num), pct],
        hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[2]} extra deaths over 5 years "
                      "(%{z:,.0f} per 100,000)<br>aid lost: %{customdata[1]} a year<br>"
                      "= %{customdata[3]} of government health spending<extra></extra>"))
    sel = A[A["iso3"] == iso3]
    if len(sel):
        fig.add_trace(go.Choropleth(locations=sel["iso3"], z=[1], locationmode="ISO-3", showscale=False,
                                    colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
                                    marker_line_color=INK, marker_line_width=2, hoverinfo="skip"))
    fig.update_geos(projection_type="natural earth", showframe=False, showcoastlines=False, showcountries=True,
                    countrycolor=th.SURFACE, countrywidth=0.5, showland=True, landcolor=th.RULE,
                    bgcolor=th.SURFACE, **(dict(lataxis_range=[-45, 75]) if world else MAP_FOCUS))
    _layout(fig, h=520, title=_title("Extra Deaths per 100,000 People Over 5 Years"), margin=dict(l=0, r=0, t=50, b=60))
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


def deaths_per_child_immunised(isos, I, ptab) -> tuple:
    """The model's future deaths averted per child immunised, births-weighted across countries, at today's mortality:
    (over a lifetime, before age 5)."""
    Pc = hm.draw_params(ptab, 0)
    per_child, births = [], []
    for c in isos:
        row = I["ci"].loc[c]
        b = row.get("births", np.nan)
        if pd.isna(b) or b <= 0:
            continue
        per_child.append(float(hm.per_unit_deaths(row, Pc, np.nan, trend=False)["imm"][0, -1]))
        births.append(float(b))
    u5 = float(np.average(per_child, weights=births)) if births else np.nan
    return u5 / float(Pc["imm_u5_share"][0]), u5


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
                                          f"(range {rng(A['deaths_5y_lo'].sum(), A['deaths_5y_hi'].sum())}), {n} countries"},
        {"Study": "ten Brink et al., Lancet HIV 2025",
         "What It Covers": "HIV only; 24% cut by the top 5 donors plus PEPFAR ending; all low- and middle-income "
                           "countries; 2025-2030",
         "Published": "0.77M to 2.93M additional HIV deaths",
         "This Model (Current Scenario)": f"{num(A['deaths_5y_HIV'].sum())} extra HIV deaths over 5 years, {n} countries"},
        {"Study": "Gavi (2000-2024)",
         "What It Covers": "Future deaths averted per child immunised",
         "Published": "About 0.017 (20.6M deaths averted / 1.2B children)",
         "This Model (Current Scenario)": f"{lifetime:.3f} per child over a lifetime, of which {model_per_child:.3f} before age 5 (births-weighted across countries)"},
    ])
    st.table(tbl.set_index("Study"))
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
<div class="meta"><b>Donor Scenario:</b> {e(title_case(preset))}<br><b>Government Response:</b> {e(resp_label)}</div>
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
covered. Costs per person come from published studies (see `unit_cost_reference.csv`): HIV treatment site costs from
Rosen et al. 2021 for Malawi, Zambia, Lesotho, Uganda and Zimbabwe (median drug cost + GDP-scaled staff cost elsewhere);
TB cost per patient by World Bank income group (Laurence et al. 2015); both grossed up for the 45% of donor spending that
sits above service delivery (PEPFAR expenditure analysis). Bednets (GiveWell), spraying (PMI) and vaccines (Gavi spend per
child) are already full program costs. Coverage drop (percentage points) = people losing service ÷ population in need: people living with HIV (prevalence x population 15-64, calibrated to UNAIDS 2011
counts, + children), HIV+ pregnancies, TB incidence, population at malaria risk, malaria cases, births.

**4. Lives.**
- *HIV treatment:* excess deaths among people off treatment rise 1.2%, 2.8%, 3.8%, 4.5%, 5% in years 1-5 (x an uncertain
  multiplier); they also transmit HIV (0.04 infections per person-year). Calibrated to sit between the Optima and UNAIDS
  estimates for losing PEPFAR.
- *Mother-to-child transmission:* infections averted per mother (0.25; WHO: 15-45% transmission without prevention vs
  under 5% with it) x death by age 2 if infected (0.45; Newell et al. 2004).
- *TB:* deaths per patient untreated = case-fatality untreated minus treated (WHO: 0.43 vs 0.03 HIV-negative; higher for
  HIV-positive, weighted by the country's TB/HIV share and HIV treatment coverage).
- *Malaria:* Lives Saved Tool form, D₁ = D₀ x Π (1 - E·C₁)/(1 - E·C₀) with E = 0.55 for vector control (Eisele et al. 2010) and 0.82 for case
  management, D₀ = malaria deaths (WHO/MCEE child malaria deaths ÷ under-5 share: 0.76 in Africa, 0.40 elsewhere).
- *Vaccines:* future deaths averted per child immunised (Gavi: 0.017-0.024) x the 65% that occur before age 5 (Li et al.
  2021: hepatitis B and HPV deaths come in adulthood) x country under-5 mortality ÷ 50.
- Year-by-year lags: deaths build up over 5 years (see the yearly deaths chart).
- *Already-falling death rates* (sidebar switch, on by default): malaria deaths and under-5 mortality were falling
  before any cut, so baseline malaria deaths (D₀) and the under-5 mortality scaling for vaccines are multiplied by
  (1 + trend)^(year - 1) in years 1-5. Each country's trend is its average annual change over 2010-2019 (log-linear fit,
  before COVID), clipped to -8% to +2% a year, with the median across countries where data are missing; if a trend is
  still unavailable, -0.9% a year is used (Cavalcanti et al. 2025, Lancet, appendix section 10.2). TB and HIV treatment
  effects are per patient, so they are unchanged.

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
