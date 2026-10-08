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
    # 21 points (0-100% in 5% steps); run_country draws its parameters with the same seed at every point, so the band
    # is built from the same random draws all along the curve
    ptab = pd.read_json(io.StringIO(ptab_json), orient="split")
    return hm.dose_response(iso3, bucket, hm.Fiscal(*fiscal_t), _inputs(), ptab, grid=np.linspace(0, 1, 21), n_draws=100,
                            mortality_trend=trend)


@st.cache_data(show_spinner=False, max_entries=32)
def _scenario_path(iso3, sc_key, bucket, fiscal_t, ptab_json, trend=True):
    """This scenario's own path for one bucket: every cut scaled from 0% to 100% of its size (21 points, the same
    draws as the even-cut curve), as (share of the bucket's aid lost, extra deaths over 5 years)."""
    ptab = pd.read_json(io.StringIO(ptab_json), orient="split")
    rows = []
    for k in np.linspace(0, 1, 21):
        sc = scn.scenario_from_key(sc_key)
        sc.scale = float(k)
        r = hm.run_country(iso3, sc, hm.Fiscal(*fiscal_t), _inputs(), ptab, n_draws=100, mortality_trend=trend)
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


def chart(fig, **kw):
    # theme=None: draw with the "editorial" Plotly template instead of Streamlit's chart theme
    st.plotly_chart(th.style_fig(tc_fig(fig)), theme=None, config={"displayModeBar": False}, **WIDE, **kw)


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
    if "m_trend" not in st.session_state:
        st.session_state["m_trend"] = ctx.get("trend", scn.DEFAULT_MORTALITY_TREND)
    if st.session_state.get("m_mode") not in GOV_MODES:          # e.g. an option from an older version of the page
        st.session_state["m_mode"] = list(GOV_MODES)[0]
    th_c, th_lo, th_hi = hm.theta_historical(I["reg"])
    with st.container(key="model_controls", border=True):
        c1, c2, c3 = st.columns([1.45, 1.25, 0.8], gap="medium")
        with c1:
            preset = th.shared_select("Donor Scenario", list(PRESETS), "m_preset", "sel_preset", list(PRESETS)[0],
                                      format_func=title_case,
                                      help=_esc(PRESETS[st.session_state.get("sel_preset", list(PRESETS)[0])]))
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
    I = _inputs()
    ci = I["ci"]
    th.section_header("monitor_heart", f"How Aid Cuts Translate into Coverage and Lives in {country_name}", help=INTRO)
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
    cards = _per_million_cards(res, ptab, country_name)
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
    st.html(_service_table_html(rows, country_name))
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
    bsel = st.radio("Bucket (Left Chart Only)", hm.BUCKETS, horizontal=True, key="m_dose_b",
                    help="Picks the bucket for the left chart; the right chart always shows all four buckets.")
    dr = _dose(iso3, bsel, fiscal_t, ptab_json, trend)
    path = _scenario_path(iso3, sk, bsel, fiscal_t, ptab_json, trend)
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
        chart(path_fig)
    st.caption("The solid line cuts every donor and service by the same share. The dashed line is this scenario's "
               "actual cut, which can run higher or lower because it falls on specific services (for example, US "
               "money is concentrated in HIV treatment, where each dollar saves more lives). The shaded band is the "
               "95% uncertainty range for the even cut.")

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


CARD_SERVICE = {"HIV": "HIV Treatment", "TB": "TB Treatment", "Malaria": "Bednets & Spraying",
                "Immunization": "Routine Immunization"}
NO_DEATHS_REASON = {"Malaria": " (very low transmission)"}


def _per_million_cards(res, ptab, country_name: str = "") -> list:
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
        no_deaths = not (d_per > 0)                     # e.g. malaria in Iraq: nothing to model
        out.append({"bucket": b, "color": BUCKET_COLORS[b], "service": CARD_SERVICE[b],
                    "people": f"{num(per_m_units)} {ln['unit_label']} lose the service",       # a sentence (brief)
                    "people_n": f"{per_m_units:,.0f}", "unit": ln["unit_label"],
                    "cov_n": None if np.isnan(dpp) else f"{dpp:,.1f}",
                    "coverage": "n/a" if np.isnan(dpp) else f"{dpp:,.1f} Percentage Points",
                    "deaths": f"{d_per:,.0f}",
                    "no_deaths": (f"No {BUCKET_WORD[b]} deaths modelled in {country_name}{NO_DEATHS_REASON.get(b, '')}"
                                  if no_deaths else ""),
                    "foot": title_case(f"Cost {money(uc)} per {hm.UNIT_SINGULAR[line]}"
                                       + ("" if no_deaths else f" · {money(5e6 / d_per)} of aid per death"))})
    return out


def _card_html(c) -> str:
    """One card: bucket, service on one line, unit as a grey second line, then three big numbers."""
    e = html.escape
    big = (f"<div class='big'>{e(c['people_n'])}</div><div class='lbl'>People Losing the Service</div>")
    big += (f"<div class='big'>{e(c['cov_n'])}</div><div class='lbl'>Coverage Drop (Percentage Points)</div>"
            if c["cov_n"] is not None else "")
    big += (f"<div class='none'>{e(c['no_deaths'])}</div>" if c["no_deaths"] else
            f"<div class='big'>{e(c['deaths'])}</div><div class='lbl'>Extra Deaths Over 5 Years</div>")
    return (f"<div class='ed-card' style='border-top-color:{c['color']}'>"
            f"<div class='t'>{e(c['bucket'])}</div><div class='s1'>{e(c['service'])}</div>"
            f"<div class='s'>{e(c['unit'])}</div>{big}"
            f"<div class='foot'>{e(c['foot'])}</div></div>").replace("$", "&#36;")


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
    _layout(fig, h=h, title=_title("Aid Lost per Year, by Disease"
                                   + (" (Lighter = Replaced by Government)" if any_replaced else "")),
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


SUM_COLS = ["base_usd", "gross_loss_usd", "replaced_usd", "net_loss_usd", "units_lost", "cov_drop_pp", "deaths_y1",
            "deaths_5y", "deaths_5y_lo", "deaths_5y_hi"]


LINE_SHORT = {"hiv_art": ("HIV Treatment", "ART, testing, care"),
              "hiv_pmtct": ("Mother-to-Child Transmission", "prevention (PMTCT)"),
              "hiv_prev": ("HIV Prevention", "PrEP, VMMC, condoms, key populations"),
              "hiv_ovc": ("Orphans & Vulnerable Children", "support"),
              "tb_ds": ("TB Treatment", "case finding & treatment"),
              "tb_dr": ("Drug-Resistant TB", "second-line treatment"),
              "mal_vec": ("Bednets & Spraying", "nets and indoor residual spraying"),
              "mal_itn": ("Bednets", "bednets & other vector control"),
              "mal_irs": ("Indoor Spraying", "indoor residual spraying"),
              "mal_cm": ("Malaria Treatment", "testing & treatment"),
              "imm": ("Routine Immunization", "vaccines + delivery")}


def _service_rows(show: pd.DataFrame) -> pd.DataFrame:
    """Lines as shown to readers: bednets and indoor spraying merged (same population at risk, so their coverage drops
    add up; ranges are added, which slightly widens them), and support for orphans and vulnerable children dropped
    (it has no modelled effect on deaths). Adds the short name, the cost text and whether coverage can be shown
    (it can't when nobody is in need, e.g. malaria treatment in Iraq: the drop would be 0 / 0)."""
    d = show[show["line"] != "hiv_ovc"].copy()
    d["cost_big"] = d["unit_cost"].map(money)
    d["cost_unit"] = [f"per {hm.UNIT_SINGULAR[r.line]}" for r in d.itertuples()]
    if {"mal_itn", "mal_irs"} <= set(d["line"]):
        itn, irs = d[d["line"] == "mal_itn"].iloc[0], d[d["line"] == "mal_irs"].iloc[0]
        row = itn.copy()
        for c in SUM_COLS:
            row[c] = np.nansum([itn[c], irs[c]])
        row["line"], row["label"] = "mal_vec", "Bednets & spraying"
        row["capped"] = bool(itn["capped"] or irs["capped"])
        row["cost_big"] = f"{money(itn['unit_cost'])} / {money(irs['unit_cost'])}"
        row["cost_unit"] = "per person-year"
        d = d[~d["line"].isin(["mal_itn", "mal_irs"])]
        d = pd.concat([d, row.to_frame().T]).sort_index()
        for c in SUM_COLS + ["need", "cov0", "unit_cost"]:
            d[c] = pd.to_numeric(d[c])
    d["name"] = d["line"].map(lambda l: LINE_SHORT.get(l, (l, ""))[0])
    d["detail"] = d["line"].map(lambda l: LINE_SHORT.get(l, ("", ""))[1])
    d["cov_ok"] = (d["need"] > 0) & d["cov0"].notna() & np.isfinite(d["cov_drop_pp"].astype(float))
    d["after"] = np.where(d["cov_ok"], (d["cov0"] - d["cov_drop_pp"].fillna(0) / 100).clip(0, 1), np.nan)
    d["drop"] = np.where(d["cov_ok"], (d["cov0"] - d["after"]) * 100, np.nan)
    order = {b: i for i, b in enumerate(hm.BUCKETS)}
    return d.assign(_o=d["bucket"].map(order)).sort_values("_o", kind="stable").drop(columns="_o")


def _pts(v: float) -> str:
    """Coverage drop as text: one decimal below 10 points, whole points above."""
    return f"−{v:.1f} pts" if v < 10 else f"−{v:.0f} pts"


DISEASE_WORD = {"HIV": "HIV", "TB": "TB", "Malaria": "malaria", "Immunization": "vaccine-preventable"}


def cov_pair(c0: float, c1: float) -> str:
    """'66% → 65%', or one decimal when coverage is below 1% ('0.2% → 0.0%')."""
    f = "{:.1%}" if min(c0, c1) < 0.01 else "{:.0%}"
    return f"{f.format(c0)} → {f.format(c1)}"


def _service_table_html(rows: pd.DataFrame, country_name: str = "") -> str:
    """'What Each Service Loses': NYT-style HTML table, grouped by disease, with a Total row."""
    e = html.escape
    grey = lambda t: f"<span class='sub'>{t}</span>"
    nm = f"<span class='nm'>{e('Not Modelled')}</span>"
    head = [("Service", ""), ("Donor Aid Now", "per year"), ("Aid Lost", "per year, after government replacement"),
            ("Cost per Person", ""), ("People Losing Service", ""), ("Coverage", ""), ("Extra Deaths", "5 years")]
    th_html = "".join(f"<th>{e(h)}" + (f"<br>{grey(e(s))}" if s else "") + "</th>" for h, s in head)
    body, prev = [], None
    for r in rows.itertuples():
        col = BUCKET_COLORS[r.bucket]
        if prev is not None and r.bucket != prev:
            body.append("<tr class='gap'><td colspan='7'></td></tr>")
        prev = r.bucket
        service = (f"<td class='svc' style='border-left:3px solid {col}'><span class='dot' style='background:{col}'>"
                   f"</span><b>{e(r.name)}</b><br>{grey(e(r.detail))}</td>")
        if r.cov_ok:
            cov = f"{cov_pair(r.cov0, r.after)}<br><span class='drop'>{_pts(r.drop)}</span>"
        elif r.line == "hiv_prev":
            cov = "<span class='nm'>No Single<br>Target Group</span>"
        else:
            cov = nm
        if r.line == "hiv_prev":             # the only line with no death pathway inside the 5 years
            tip = ("Prevention averts new HIV infections; their deaths mostly fall after the 5-year window, so "
                   "they're counted in the New HIV Infections card.")
            deaths = f"<span class='nm' title='{e(tip, quote=True)}'>See New<br>Infections</span>"
        elif not (r.deaths_5y_hi > 0) and r.net_loss_usd > 0:
            tip = (f"{country_name} records almost no {DISEASE_WORD[r.bucket]} deaths, so cutting this aid adds "
                   "almost none.")
            deaths = f"<b title='{e(tip, quote=True)}'>~0</b>"
        else:
            deaths = f"<b>{num(r.deaths_5y)}</b><br>{grey(rng(r.deaths_5y_lo, r.deaths_5y_hi))}"
        people = num(r.units_lost) if r.units_lost > 0 or r.cov_ok else nm
        cells = [money(r.base_usd), money(r.net_loss_usd),
                 f"<span class='big'>{e(r.cost_big)}</span><br>"
                 f"{grey(e(r.cost_unit).replace('per infection averted', 'per infection<br>averted'))}", people, cov, deaths]
        body.append("<tr>" + service + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
    # total row (people exclude HIV prevention, whose unit is infections averted)
    ppl = rows.loc[rows["line"] != "hiv_prev", "units_lost"].sum()
    total = ["<td class='svc'><b>Total</b></td>", f"<td><b>{money(rows['base_usd'].sum())}</b></td>",
             f"<td><b>{money(rows['net_loss_usd'].sum())}</b></td>", "<td></td>", f"<td><b>{num(ppl)}</b></td>",
             "<td></td>", f"<td><b>{num(rows['deaths_5y'].sum())}</b><br>"
                          f"{grey(rng(rows['deaths_5y_lo'].sum(), rows['deaths_5y_hi'].sum()))}</td>"]
    body.append("<tr class='tot'>" + "".join(total) + "</tr>")
    return ("<div class='ed-nyt-wrap'><table class='ed-nyt'><colgroup><col style='width:26%'>"
            + "<col style='width:12.3%'>" * 6 + "</colgroup><thead><tr>" + th_html + "</tr></thead><tbody>"
            + "".join(body) + "</tbody></table></div>").replace("$", "&#36;")


def _coverage_fig(rows: pd.DataFrame):
    """How much coverage each service loses: one bar per service (percentage points), largest first."""
    d = rows[rows["cov_ok"] & (rows["drop"] > 0)].copy()
    if d.empty:
        return None
    d = d.sort_values("drop")                      # plotly draws the first row at the bottom
    labels = [f"<b>{n}</b>" for n in d["name"]]
    text = [f"  {_pts(v)} ({cov_pair(c0, a)})" for v, c0, a in zip(d["drop"], d["cov0"], d["after"])]
    xmax = float(d["drop"].max())
    fig = go.Figure(go.Bar(y=labels, x=_visible(list(d["drop"]), xmax * 2.0), orientation="h",
                           marker=dict(color=[BUCKET_COLORS[b] for b in d["bucket"]]), text=text,
                           textposition="outside", cliponaxis=False, textfont=dict(color=INK, size=13),
                           customdata=d["drop"], hovertemplate="%{y}: −%{customdata:.1f} percentage points"
                                                               "<extra></extra>"))
    h, gap = _loss_layout(len(d))
    fig.update_layout(bargap=gap)
    _layout(fig, h=h, title=_title("How Much Coverage Each Service Loses (Percentage Points)"),
            margin=dict(l=10, r=20, t=50, b=10), xaxis=dict(range=[0, xmax * 2.0], nticks=5))
    return fig


def _dose_fig(dr: pd.DataFrame, bucket: str, cur_cut: float, bb: pd.Series, path: pd.DataFrame | None = None):
    """Even cut across all donors (solid, with its 95% band) and this scenario's own path (dashed, ending at the dot)."""
    col = BUCKET_COLORS[bucket]
    x = dr["cut"] * 100
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(x) + list(x[::-1]), y=list(dr["hi"]) + list(dr["lo"][::-1]), fill="toself",
                             fillcolor=th.tint(col, 0.15), line=dict(width=0), hoverinfo="skip",
                             name="95% Uncertainty Range", legendrank=3))
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
                           text=f"This Scenario: {cur_cut:.0%} Cut, {num(bb['deaths_5y'])} Deaths",
                           showarrow=True, arrowhead=0, arrowwidth=1, arrowcolor=MUTED, standoff=7,
                           font=dict(color=INK, size=12), bgcolor=th.tint(th.SURFACE, 0.9))
    _layout(fig, h=420, title=_title("Extra Deaths as More Aid Is Cut"),
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
    _layout(fig, h=400, title=_title(f"Extra Deaths Each Year, All Buckets, {FIRST_YEAR}-{FIRST_YEAR + 4}"),
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


ABSORB_SHARE = 0.10        # a gap under 10% of a strong year's backfill capacity counts as easily absorbed
TINY_GAP_SHARE = 0.05      # under 5% of the largest bar, the gap chart can't be read: show pills instead


def _fiscal_sentence(F: dict, country_name: str) -> str:
    """One sentence from the data: how big the gap is against the health budget, and what a strong year would cover."""
    G, ghes, cap = F["gross_loss"], F["ghes"], F["capacity"]
    if not G or G <= 0:
        return "No aid is lost in this scenario, so there is no gap to fill."
    share = pct_smart(G / ghes) if ghes else "n/a"
    if cap and cap > 0 and G < ABSORB_SHARE * cap:
        return (f"{country_name}'s health budget could absorb this gap: it equals {share} of government health "
                f"spending, and a strong budget year alone would cover it {cap / G:,.0f} times over.")
    out = f"Replacing the lost aid would take a {share} increase in government health spending. " if ghes else ""
    pts = (F["ghes_growth_top"] - max(F["ghes_growth_median"], 0)) * 100
    year = "its best years" if F["effort"] == "p90" else "a strong year"
    if pd.isna(pts) or pts <= 0 or not cap or cap <= 0:
        return out + f"{country_name}'s health budget does not grow faster than usual even in {year}, so it has no room " \
                     "to fill the gap."
    pts_txt = f"{pts:.0f}" if pts >= 1 else f"{pts:.1f}"
    out += f"In {year} {country_name}'s health budget grows about {pts_txt}% faster than in a typical year, which "
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
        ("Aid Lost as % of Government Health Spending", pct_smart(G / F["ghes"]) if F["ghes"] else "n/a",
         "Gross aid lost per year ÷ government health spending, 2023", ""),
        ("Aid Lost as % of Government Revenue", pct_smart(G / rev) if rev and not pd.isna(rev) else "n/a",
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
            ("Replaced in this scenario", F["replacement"], th.tint(BACKFILL, 0.55)),
            ("One year of typical growth in<br>government health spending", typical, th.OTHER))]
    biggest = max(b[1] for b in bars)
    if biggest > 0 and G < TINY_GAP_SHARE * biggest:       # bars can't be compared: show the four values instead
        st.markdown(th.pills_html([(lbl.replace("<br>", " "), money(v), "") for lbl, v, _ in bars]),
                    unsafe_allow_html=True)
        return
    fig = go.Figure(go.Bar(y=[b[0] for b in bars][::-1], x=[b[1] for b in bars][::-1], orientation="h",
                           marker=dict(color=[b[2] for b in bars][::-1]),
                           text=[money(b[1]) for b in bars][::-1], textposition="outside", cliponaxis=False,
                           textfont=dict(color=INK), hovertemplate="%{y}: %{text}<extra></extra>"))
    _layout(fig, h=300, title=_title("The Gap vs. What the Budget Can Absorb (US$ per Year)"),
            xaxis=dict(range=[0, biggest * 1.25]), margin=dict(l=10, r=80, t=50, b=10))
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


def cross_country(sk, ctl, iso3, names) -> pd.DataFrame:
    """The All Countries page: totals, map, exposure scatter and the 15 hardest-hit countries."""
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

    c1, c2 = st.columns([1.15, 1])
    with c1:
        d = A[(A["loss_pct_ghes_pct"] > 0) & (A["deaths_per_100k"] > 0)]
        fig = go.Figure()
        other = d[d["iso3"] != iso3]
        sz = np.sqrt(d["net_loss_usd"].clip(lower=1)) / np.sqrt(d["net_loss_usd"].max()) * 40 + 6
        top = d.nlargest(SCATTER_LABELS, "deaths_per_100k")                   # label only these
        fig.add_trace(go.Scatter(x=other["loss_pct_ghes_pct"], y=other["deaths_per_100k"], mode="markers",
                                 marker=dict(size=sz[d["iso3"] != iso3], color=th.GRAPE, opacity=0.5,
                                             line=dict(color=th.SURFACE, width=1)),
                                 customdata=np.c_[other["name"], other["net_loss_usd"].map(money), other["deaths_5y"].map(num)],
                                 hovertemplate="<b>%{customdata[0]}</b><br>aid loss = %{x:.0f}% of government health "
                                               "spending<br>%{y:,.0f} deaths per 100,000 over 5 years "
                                               "(%{customdata[2]})<br>net loss %{customdata[1]} a year<extra></extra>",
                                 name="Countries"))
        me = d[d["iso3"] == iso3]
        if len(me):
            fig.add_trace(go.Scatter(x=me["loss_pct_ghes_pct"], y=me["deaths_per_100k"], mode="markers+text",
                                     text=["" if iso3 in set(top["iso3"]) else iso3],
                                     textposition="top center", textfont=dict(size=13, color=INK),
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
                               ax=lx, ay=ly, axref="x", ayref="y", text=r.iso3, showarrow=True, arrowhead=0,
                               arrowwidth=1, arrowcolor=MUTED, standoff=4, xanchor="left",
                               font=dict(size=11, color=INK, family=th.SANS))
        y_lo = float(np.log10(d["deaths_per_100k"].min())) - 0.15
        _layout(fig, h=480, title=_title("Budget Exposure vs. Deaths per Person"), showlegend=False,
                xaxis=dict(type="log", title="aid lost as % of government health spending (log)", ticksuffix="%",
                           tickvals=LOG_TICKS, ticktext=[f"{v:g}" for v in LOG_TICKS],
                           range=[float(np.log10(d["loss_pct_ghes_pct"].min())) - 0.15, lx + 0.45]),
                yaxis=dict(type="log", title="extra deaths per 100,000 people over 5 years (log)",
                           tickvals=LOG_TICKS, ticktext=[f"{v:g}" for v in LOG_TICKS],
                           range=[min(y_lo, (prev or y_lo) - 0.1), float(np.log10(d["deaths_per_100k"].max())) + 0.2]))
        chart(fig)
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
        _layout(fig, h=480, title=_title("15 Countries with the Most Extra Deaths (5 Years)"),
                xaxis=dict(range=[0, float(tot15.max()) * 1.22]), margin=dict(l=10, r=20, t=50, b=10))
        chart(fig)
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
                      thickness=10, len=0.45, x=0.5, xanchor="center", y=0, yanchor="top", ypad=0,
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
    _layout(fig, h=470, title=_title("Extra Deaths per 100,000 People Over 5 Years"), margin=dict(l=0, r=0, t=40, b=50))
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

