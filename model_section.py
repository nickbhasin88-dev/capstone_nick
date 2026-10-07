"""
Section 4 of the dashboard: what a funding cut does (money -> fiscal response -> coverage -> lives).

Called from app.py:   render_model_section(iso3, country_name, imf_overrides)
All modelling lives in health_model.py; this file only builds the scenario from the controls and draws the results.
"""
from __future__ import annotations

import io
import json

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import health_model as hm

_ver = tuple(int(x) for x in st.__version__.split(".")[:2] if x.isdigit())
WIDE = {"width": "stretch"} if _ver >= (1, 50) else {"use_container_width": True}

INK, MUTED, GRID = "#2b2b2b", "#6b6b6b", "rgba(0,0,0,0.08)"
LOG_TICKS = [0.01, 0.1, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000]
LOSS, BACKFILL = "#7f8c8d", "#1b6ca8"

# --------------------------------------------------------------------------- #
# Presets (each is documented in the caption shown under the selector)
# --------------------------------------------------------------------------- #
US_MULTI_EXITS = {("United States", "WHO"): 1.0, ("United States", "Gavi"): 1.0, ("United States", "UNFPA"): 1.0,
                  ("United States", "Global Fund"): 0.23}
OECD_2025 = {"United States": 0.57, "Germany": 0.174, "France": 0.109, "United Kingdom": 0.108, "Japan": 0.056}
PRESETS = {
    "Full US exit": (
        "All US government health aid through bilateral agencies and NGOs ends; the US leaves WHO (effective Jan 2026), "
        "stops funding Gavi (announced June 2025) and UNFPA; its Global Fund pledge falls 23% (US$6.0B to US$4.6B, "
        "8th replenishment, Nov 2025). Other donors unchanged."),
    "America First MOUs": (
        "US bilateral aid follows the 2026-2030 MOU schedules your team collected (US funding in that year vs. the "
        "2021-25 pre-cut reference). Countries without a schedule get the average MOU-country cut for that year unless "
        "you override it. US multilateral exits as in 'Full US exit'."),
    "IHME 2025 preliminary estimates": (
        "Data-driven: applies IHME's own 2025 preliminary DAH estimates relative to 2021-23, separately for every "
        "source x channel x disease cell (IHME has no recipient-level split after 2023, so the global change is applied "
        "to each country's mix)."),
    "OECD-reported 2025 aid cuts": (
        "Each donor's 2025 change in total ODA (OECD preliminary data, Apr 2026) applied to its health aid: US -57%, "
        "Germany -17.4%, France -10.9%, UK -10.8%, Japan -5.6%; others unchanged."),
    "Global Fund & Gavi shortfalls": (
        "Channel shock for all donors: Global Fund -28% (8th replenishment US$11.34B vs US$15.7B for the 7th) and "
        "Gavi -24% (about US$9B raised vs a US$11.9B 2026-30 target)."),
    "Combined retreat": "'Full US exit' for the US plus the OECD-reported 2025 cuts for all other donors.",
    "Custom": "Set cuts yourself by donor and by channel (cuts combine multiplicatively: 1 - (1-donor cut)(1-channel cut)).",
}


def mou_cuts(ci: pd.DataFrame, year: int) -> dict:
    out = {}
    for iso, r in ci.iterrows():
        ref = r.get("mou_us_ref")
        if pd.isna(ref) or ref <= 0:
            continue
        y = year
        while y >= 2026 and pd.isna(r.get(f"mou_us_{y}")):
            y -= 1
        if y >= 2026 and pd.notna(r.get(f"mou_us_{y}")):
            out[iso] = float(np.clip(1 - r[f"mou_us_{y}"] / ref, -0.5, 1.0))
    return out


def build_scenario(preset: str, opts: dict, ci: pd.DataFrame) -> hm.Scenario:
    sc = hm.Scenario(name=preset)
    if preset in ("Full US exit", "Combined retreat"):
        sc.src_direct["United States"] = 1.0
        sc.pair.update(US_MULTI_EXITS)
    if preset == "America First MOUs":
        sc.us_direct_by_country = mou_cuts(ci, opts["mou_year"])
        sc.src_direct["United States"] = opts["non_mou_cut"]
        sc.pair.update(US_MULTI_EXITS)
    if preset == "IHME 2025 preliminary estimates":
        sc.ihme_trend = True
    if preset in ("OECD-reported 2025 aid cuts", "Combined retreat"):
        for s, v in OECD_2025.items():
            if preset == "Combined retreat" and s == "United States":
                continue
            sc.src_direct[s] = v
            sc.src_multi[s] = v
    if preset == "Global Fund & Gavi shortfalls":
        sc.chan = {"Global Fund": 0.28, "Gavi": 0.24}
    if preset == "Custom":
        sc.src_direct = {s: v / 100 for s, v in opts["custom_direct"].items()}
        sc.src_multi = {s: v / 100 for s, v in opts["custom_multi"].items()}
        sc.chan = {c: v / 100 for c, v in opts["custom_chan"].items() if v}
    return sc


def _scenario_key(sc: hm.Scenario) -> str:
    d = {k: v for k, v in sc.__dict__.items()}
    d["pair"] = {f"{a}|{b}": v for (a, b), v in sc.pair.items()}
    return json.dumps(d, sort_keys=True, default=str)


def _scenario_from_key(key: str) -> hm.Scenario:
    d = json.loads(key)
    d["pair"] = {tuple(k.split("|")): v for k, v in d["pair"].items()}
    return hm.Scenario(**d)


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
    return hm.run_country(iso3, _scenario_from_key(sc_key), hm.Fiscal(*fiscal_t), _inputs(), ptab, n_draws=n_draws)


@st.cache_data(show_spinner=False, max_entries=32)
def _dose(iso3, bucket, fiscal_t, ptab_json):
    ptab = pd.read_json(io.StringIO(ptab_json), orient="split")
    return hm.dose_response(iso3, bucket, hm.Fiscal(*fiscal_t), _inputs(), ptab, grid=np.linspace(0, 1, 11), n_draws=100)


@st.cache_data(show_spinner="Running the model for every country...", max_entries=16)
def _run_all(sc_key, fiscal_t, ptab_json):
    ptab = pd.read_json(io.StringIO(ptab_json), orient="split")
    return hm.run_all(_scenario_from_key(sc_key), hm.Fiscal(*fiscal_t), _inputs(), ptab, n_draws=60)


# --------------------------------------------------------------------------- #
# Formatting
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


def _caption(text, **kw):
    st.caption(text.replace("$", "\\$"), **kw)


def _md(text, **kw):
    st.markdown(text.replace("$", "\\$"), **kw)


def _metric(col, label, value, sub=None):
    """st.metric with the range/context as a grey caption (no green/red arrow; works on any Streamlit version)."""
    col.metric(label, value)
    if sub:
        col.caption(sub.replace("$", "\\$"))


def rng(lo, hi) -> str:
    return f"{num(lo)} to {num(hi)}"


def _layout(fig, h=380, **kw):
    margin = kw.pop("margin", dict(l=10, r=10, t=40, b=10))
    fig.update_layout(height=h, margin=margin, plot_bgcolor="white", paper_bgcolor="white",
                      font=dict(color=INK, size=13), hoverlabel=dict(bgcolor="white", font_size=13), **kw)
    fig.update_xaxes(gridcolor=GRID, zeroline=False, linecolor="rgba(0,0,0,0.25)")
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor="rgba(0,0,0,0.25)")
    return fig


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def render_model_section(iso3: str, country_name: str, imf: dict | None = None):
    st.header(f"4. What a funding cut does in {country_name}: money → coverage → lives")
    _caption("A four-step model for HIV, TB, malaria and immunization. **Money:** the donor scenario removes aid cell by "
               "cell (who pays x which channel x which program). **Fiscal response:** the government can backfill part of "
               "it, limited by its fiscal space. **Coverage:** money not replaced ÷ unit cost = people who lose a service. "
               "**Lives:** people losing a service x that service's effect on mortality in this country's epidemiology. "
               "Ranges are 95% intervals from 400 Monte Carlo draws over every uncertain parameter.")
    I = _inputs()
    ci = I["ci"]
    if iso3 not in ci.index or iso3 not in set(I["lines"].iso3):
        st.info(f"{country_name} has no recorded HIV, TB, malaria or vaccine aid in 2021-2023, so there is nothing to model.")
        return

    # ------------------------------ controls ------------------------------ #
    c1, c2 = st.columns([1.1, 1])
    opts = {}
    with c1:
        _md("**Donor scenario**")
        preset = st.selectbox("Scenario", list(PRESETS), index=0, key="m_preset", label_visibility="collapsed")
        _caption(PRESETS[preset])
        if preset == "America First MOUs":
            a, b = st.columns(2)
            opts["mou_year"] = a.select_slider("MOU year", options=[2026, 2027, 2028, 2029, 2030], value=2028, key="m_mouy")
            avg = float(np.mean(list(mou_cuts(ci, opts["mou_year"]).values())))
            opts["non_mou_cut"] = b.slider("US cut where no MOU schedule (%)", 0, 100, int(round(avg * 100)), 1,
                                           key=f"m_nonmou_{opts['mou_year']}",
                                           help=f"Default = average cut across the 16 MOU countries in {opts['mou_year']} "
                                                f"({avg:.0%}).") / 100
            mc = mou_cuts(ci, opts["mou_year"])
            if iso3 in mc:
                _caption(f"{country_name}: MOU schedule implies a **{mc[iso3]:.0%}** cut in US bilateral aid in "
                           f"{opts['mou_year']} (US${ci.loc[iso3, 'mou_us_ref'] / 1e6:,.0f}M/yr pre-cut reference).")
            else:
                _caption(f"{country_name} has no MOU schedule in the team sheet, so the default above applies.")
        if preset == "Custom":
            with st.expander("Cuts by donor and channel", expanded=True):
                ed = pd.DataFrame({"Donor": hm.SOURCE_GROUPS,
                                   "Bilateral & NGO cut %": [100 if s == "United States" else 0 for s in hm.SOURCE_GROUPS],
                                   "Via multilaterals cut %": [0] * len(hm.SOURCE_GROUPS)})
                ed = st.data_editor(ed, hide_index=True, key="m_custom_tbl", disabled=["Donor"],
                                    column_config={c: st.column_config.NumberColumn(min_value=-50, max_value=100, step=5)
                                                   for c in ("Bilateral & NGO cut %", "Via multilaterals cut %")})
                opts["custom_direct"] = dict(zip(ed["Donor"], ed["Bilateral & NGO cut %"]))
                opts["custom_multi"] = dict(zip(ed["Donor"], ed["Via multilaterals cut %"]))
                _caption("Channel shocks hit every donor's money through that channel (e.g. a replenishment shortfall).")
                cc = st.columns(4)
                opts["custom_chan"] = {ch: cc[i].slider(f"{ch} %", 0, 100, 0, 5, key=f"m_ch_{ch}")
                                       for i, ch in enumerate(["Global Fund", "Gavi", "WHO", "UNICEF"])}
    with c2:
        _md("**Government response**")
        th_c, th_lo, th_hi = hm.theta_historical(I["reg"])
        mode_lbl = {"No backfill": "none", "Historical behaviour (estimated)": "historical",
                    "Replace a set share": "custom", "As much as fiscal space allows": "max"}
        mode = mode_lbl[st.radio("How much of the lost aid does the government replace?", list(mode_lbl), index=0,
                                 key="m_mode")]
        theta = 0.0
        if mode == "custom":
            theta = st.slider("Share of lost aid replaced (%)", 0, 100, 25, 5, key="m_theta") / 100
        cap = st.checkbox("Cap replacement at fiscal space", value=True, key="m_cap", disabled=(mode in ("none", "max")))
        effort = st.radio("Fiscal-space ceiling", ["Strong year (75th pct. GHES growth)", "Best years (90th pct.)"],
                          horizontal=True, key="m_effort", disabled=(mode == "none"),
                          help="How hard can the health budget be pushed? Capacity = GHES x (that growth rate minus the "
                               "country's typical growth) x a debt-stress factor, every year.")
        alloc = st.radio("Where does replacement money go?", ["Pro-rata to what was cut", "Lives first (triage)"],
                         horizontal=True, key="m_alloc",
                         help="Lives first refills the services that avert the most deaths per dollar first "
                              "(usually TB treatment, vaccines, ART) before anything else.")
        if mode == "historical":
            _caption(f"Estimated from 97 countries, 2001-2023: when aid per person fell by $1, government health spending "
                       f"per person changed by **{th_c:+.2f}** (95% CI {th_lo:+.2f} to {th_hi:+.2f}) within two years. "
                       f"That is no evidence of backfilling, so this option replaces {max(th_c, 0):.0%}.")
    fiscal_t = (mode, theta, cap, "pro_rata" if alloc.startswith("Pro") else "lives_first",
                "p90" if effort.startswith("Best") else "p75")

    with st.expander("Model parameters: unit costs and effect sizes (editable)"):
        _caption("Each parameter is drawn from a triangular distribution (low, central, high). Edit any cell to see "
                   "how sensitive the answer is. Sources and rationale in the last column.")
        ptab0 = _default_params().reset_index()
        ptab = st.data_editor(ptab0, hide_index=True, key="m_params", disabled=["param", "label", "unit", "source"],
                              column_config={"param": None}, **WIDE)
        ptab = ptab.set_index("param")
    ptab_json = ptab.to_json(orient="split")

    sc = build_scenario(preset, opts, ci)
    sk = _scenario_key(sc)
    res = _run(iso3, sk, fiscal_t, ptab_json)
    res0 = _run(iso3, sk, ("none", 0.0, True, "pro_rata", "p75"), ptab_json) if mode != "none" else res
    T, F, B, L = res["totals"], res["fiscal"], res["buckets"].set_index("bucket"), res["lines"]

    if T.get("gains", 0) > 1e5:
        _caption(f"Some aid cells *increase* in this scenario (+{money(T['gains'])}/yr); those gains are counted as "
                 "coverage and lives gained and partly offset the losses below.")
    if T["gross"] <= 0 and T["base"] > 0:
        st.success((f"Under '{preset}' {country_name} loses no HIV, TB, malaria or vaccine aid "
                    f"(net change {money(-T['gross'])}).").replace("$", "\\$"))

    # ------------------------------ headline ------------------------------ #
    st.subheader("The headline")
    k = st.columns(6)
    _metric(k[0], "Aid at risk (per year)", money(T["gross"]),
            f"{T['gross'] / T['base']:.0%} of {money(T['base'])} for these four buckets" if T["base"] else None)
    _metric(k[1], "Replaced by government", money(T["replaced"]),
            f"{T['replaced'] / T['gross']:.0%} of the loss" if T["gross"] > 0 else None)
    _metric(k[2], "Net loss to services", money(T["net"]), "per year")
    _metric(k[3], "Extra deaths, year 1", num(T["deaths_y1"]),
            "95% UI " + rng(res["buckets"]["deaths_y1_lo"].sum(), res["buckets"]["deaths_y1_hi"].sum()))
    _metric(k[4], "Extra deaths over 5 years", num(T["deaths_5y"]), "95% UI " + rng(T["deaths_5y_lo"], T["deaths_5y_hi"]))
    _metric(k[5], "New HIV infections, 5 years", num(B.loc["HIV", "infections_5y"]),
            "95% UI " + rng(B.loc["HIV", "infections_5y_lo"], B.loc["HIV", "infections_5y_hi"]))
    if mode != "none" and T["replaced"] > 0:
        saved = res0["totals"]["deaths_5y"] - T["deaths_5y"]
        if fiscal_t[3] == "lives_first":
            _caption("Lives-first triage protects treatment and vaccines first; HIV prevention and OVC programs are refilled "
                     "last, so new HIV infections can stay high even when deaths fall.")
        _caption(f"Government backfill of {money(T['replaced'])}/yr averts about **{num(saved)} deaths over 5 years** "
                   f"compared with no backfill ({money(T['replaced'] * 5 / max(saved, 1))} per death averted).")
    _caption("UI = 95% uncertainty interval. Deaths assume the cut is sustained for five years; "
               "year 1 is lower because mortality after losing treatment, bednets or vaccines builds up over time.")

    # ------------------------------ per $1M ------------------------------ #
    st.subheader("Every US$1 million lost, by bucket")
    _caption("The core conversion: what one million dollars of aid that is cut and not replaced does to coverage and to "
               f"lives in {country_name}, given its unit costs, current coverage and disease burden.")
    cols = st.columns(4)
    main_line = {"HIV": "hiv_art", "TB": "tb_ds", "Malaria": "mal_itn", "Immunization": "imm"}
    Ls = L.set_index("line")
    for i, b in enumerate(hm.BUCKETS):
        ln = Ls.loc[main_line[b]]
        uc = ln["unit_cost"]
        need = ln["need"]
        per_m_units = 1e6 / uc * (1 - float(ptab.loc["continuity", "central"]))
        dpp = per_m_units / need * 100 if need and not np.isnan(need) else np.nan
        d_per = res["deaths_per_dollar"][main_line[b]] * 1e6 * (1 - float(ptab.loc["continuity", "central"]))
        with cols[i]:
            st.markdown(f"<div style='border-left:4px solid {hm.BUCKET_COLORS[b]};padding:2px 0 2px 12px'>"
                        f"<div style='font-weight:700;font-size:16px'>{b}</div>"
                        f"<div style='color:{MUTED};font-size:12px'>{hm.LINE_LABELS[main_line[b]]}</div>"
                        f"<div style='font-size:14px;margin-top:6px'><b>{num(per_m_units)}</b> {ln['unit_label']} lose the service</div>"
                        f"<div style='font-size:14px'><b>{dpp:,.2f} pp</b> coverage drop</div>"
                        f"<div style='font-size:14px'><b>{d_per:,.0f}</b> extra deaths over 5 yrs</div>"
                        f"<div style='color:{MUTED};font-size:12px;margin-top:4px'>unit cost {money(uc)} · "
                        f"{money(5e6 / d_per) if d_per > 0 else 'n/a'} of aid per death</div></div>".replace("$", "&#36;"),
                        unsafe_allow_html=True)
    _caption("Per US$1M cut every year for five years from the main service line in each bucket (malaria: bednets). "
               "'pp' = percentage points of the population in need. Coverage drop per $1M is linear; deaths are too, except "
               "for malaria, where the Lives Saved Tool equations make each extra point of lost coverage slightly worse.")

    # ------------------------------ money flow ------------------------------ #
    st.subheader("Where the money is lost: donor → channel → disease")
    cells = res["cells"]
    cl = cells[cells["loss"] > 0]
    if cl.empty:
        st.info("No aid is cut in this scenario.")
    else:
        _sankey(cl, B, T)

    # ------------------------------ chain table ------------------------------ #
    st.subheader("The chain, service by service")
    show = L[(L["base_usd"] > 0) | (L["net_loss_usd"] != 0)].copy()
    tbl = pd.DataFrame({
        "Bucket": show["bucket"], "Service": show["label"],
        "Aid now (yr)": show["base_usd"].map(money),
        "Lost, net of backfill": show["net_loss_usd"].map(money),
        "Unit cost": [f"{money(r.unit_cost)} per {hm.UNIT_SINGULAR[r.line]}" for r in show.itertuples()],
        "Donors fund (% of current coverage)": show["donor_share_of_coverage"].map(lambda v: "n/a" if pd.isna(v) else f"{min(v, 9.99):.0%}" + ("+" if v > 1 else "")),
        "People losing service": show["units_lost"].map(num),
        "Coverage before → after": [
            "n/a" if pd.isna(r.need) or pd.isna(r.cov0) else f"{r.cov0:.0%} → {max(r.cov0 - r.cov_drop_pp / 100, 0):.0%}"
            for r in show.itertuples()],
        "Deaths, yr 1": show["deaths_y1"].map(num),
        "Deaths, 5 yrs (95% UI)": [f"{num(r.deaths_5y)} ({rng(r.deaths_5y_lo, r.deaths_5y_hi)})" for r in show.itertuples()],
        "HIV infections, 5 yrs": show["infections_5y"].map(lambda v: num(v) if v > 0 else ""),
    })
    st.dataframe(tbl, hide_index=True, **WIDE)
    notes = []
    if show["capped"].any():
        notes.append("Where the aid lost would pay for more people than are currently covered, the loss is capped at current "
                     "coverage (flagged 100%+ in the donor-share column).")
    notes += [f"{f[0].upper() + f[1:]}." for f in res["flags"]]
    notes.append("HIV prevention converts money to infections averted (no deaths within 5 years); OVC support has no "
                 "modelled mortality effect. 'Unreported' program money is spread over each bucket's known mix, and "
                 f"{float(ptab.loc['hss_kappa', 'central']):.0%} of lost systems money (labs, staff, M&E) is assumed to cut services.")
    _caption(" ".join(notes))

    _coverage_dumbbell(show)

    # ------------------------------ dose response + path ------------------------------ #
    st.subheader("How the damage scales")
    d1, d2 = st.columns(2)
    with d1:
        bsel = st.radio("Bucket", hm.BUCKETS, horizontal=True, key="m_dose_b")
        dr = _dose(iso3, bsel, fiscal_t, ptab_json)
        cur_cut = B.loc[bsel, "gross_loss_usd"] / B.loc[bsel, "base_usd"] if B.loc[bsel, "base_usd"] > 0 else 0
        _dose_chart(dr, bsel, cur_cut, B.loc[bsel], res, ptab, iso3)
    with d2:
        _path_chart(res)

    # ------------------------------ fiscal space ------------------------------ #
    _fiscal_panel(res, country_name, imf or {})

    # ------------------------------ statistical cross-check ------------------------------ #
    st.subheader("Cross-check: what 20 years of data say")
    xc = hm.statistical_crosscheck(res, I, ptab)
    if not xc.empty:
        out = pd.DataFrame({
            "Service": [f"{r.bucket}: {hm.LINE_LABELS[r.line]}" for r in xc.itertuples()],
            "Coverage drop: unit-cost model": xc["mech_cov_drop_pp"].map(lambda v: f"{v:,.1f} pp"),
            "Coverage drop: panel regression (95% CI)": [f"{r.cov_drop_pp:,.1f} pp ({r.cov_drop_pp_lo:,.1f} to {r.cov_drop_pp_hi:,.1f})" for r in xc.itertuples()],
            "Deaths 5 yrs: unit-cost model": xc["mech_deaths_5y"].map(num),
            "Deaths 5 yrs: panel regression": [f"{num(r.deaths_5y)} ({rng(max(r.deaths_5y_lo, 0), r.deaths_5y_hi)})" for r in xc.itertuples()],
            "Regression": [f"β = {r.beta:.2f} (SE {r.se:.2f}), {r.n_obs:,} obs, {r.n_countries} countries" for r in xc.itertuples()],
        })
        st.dataframe(out, hide_index=True, **WIDE)
        _caption("The panel regressions relate coverage (ART coverage, TB treatment coverage, DTP3) to log aid per person in "
                   "need within each country over 2005-2023, with country and year fixed effects and controls for government "
                   "health spending and GDP. They are a *lower bound* on a sudden cut: historically aid moved gradually, other "
                   "funders filled gaps, and year effects absorb the global scale-up. The unit-cost model describes an abrupt "
                   "cut with nothing else adjusting. The truth for 2025-2030 most likely lies between the two.")

    # ------------------------------ cross-country ------------------------------ #
    _cross_country(sk, fiscal_t, ptab_json, iso3, preset)

    with st.expander("Methods, data and limitations"):
        _md(METHODS)


# --------------------------------------------------------------------------- #
# Charts
# --------------------------------------------------------------------------- #
def _sankey(cl: pd.DataFrame, B: pd.DataFrame, T: dict):
    tot = cl["loss"].sum()
    cl = cl.copy()
    small_src = cl.groupby("src_grp")["loss"].sum() < 0.01 * tot
    cl.loc[cl["src_grp"].isin(small_src[small_src].index), "src_grp"] = "Other donors"
    src = cl.groupby("src_grp")["loss"].sum().sort_values(ascending=False).index.tolist()
    ch = cl.groupby("chan_grp")["loss"].sum().sort_values(ascending=False).index.tolist()
    bk = [b for b in hm.BUCKETS if b in set(cl["bucket"])]
    fates = ["Replaced by government", "Lost to services"]
    nodes = [f"{s}" for s in src] + [f"via {c}" for c in ch] + bk + fates
    idx = {n: i for i, n in enumerate(nodes)}
    S, Tg, V, C = [], [], [], []
    for (s, c), v in cl.groupby(["src_grp", "chan_grp"])["loss"].sum().items():
        S.append(idx[s]); Tg.append(idx[f"via {c}"]); V.append(v); C.append("rgba(120,120,120,0.25)")
    for (c, b), v in cl.groupby(["chan_grp", "bucket"])["loss"].sum().items():
        S.append(idx[f"via {c}"]); Tg.append(idx[b]); V.append(v)
        h = hm.BUCKET_COLORS[b].lstrip("#")
        C.append(f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},0.35)")
    for b in bk:
        g, rep = B.loc[b, "gross_loss_usd"], B.loc[b, "replaced_usd"]
        if rep > 0:
            S.append(idx[b]); Tg.append(idx[fates[0]]); V.append(rep); C.append("rgba(27,108,168,0.35)")
        if g - rep > 0:
            S.append(idx[b]); Tg.append(idx[fates[1]]); V.append(g - rep); C.append("rgba(90,90,90,0.30)")
    ncol = (["#5d6d7e"] * len(src) + ["#aab2bd"] * len(ch) + [hm.BUCKET_COLORS[b] for b in bk] + [BACKFILL, "#4d4d4d"])
    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(label=[f"{n}  {money(v)}" for n, v in zip(nodes, _node_values(nodes, S, Tg, V))], pad=14, thickness=14,
                  color=ncol, line=dict(color="white", width=1),
                  hovertemplate="%{label}<extra></extra>"),
        link=dict(source=S, target=Tg, value=V, color=C, customdata=[money(v) for v in V],
                  hovertemplate="%{source.label} → %{target.label}<br>%{customdata} per year<extra></extra>")))
    _layout(fig, h=460, title=dict(text=f"Annual aid lost: {money(T['gross'])}", font=dict(size=15)))
    st.plotly_chart(fig, **WIDE)
    _caption("Left: who originally paid. Middle: the channel that delivered it (a US cut to the Global Fund shows up as "
               "'United States → via Global Fund'). Right: the disease bucket, and how much of the loss the government replaces.")


def _node_values(nodes, S, T, V):
    inflow, outflow = np.zeros(len(nodes)), np.zeros(len(nodes))
    for s, t, v in zip(S, T, V):
        outflow[s] += v
        inflow[t] += v
    return np.maximum(inflow, outflow)


def _coverage_dumbbell(show: pd.DataFrame):
    d = show[show["need"].notna() & show["cov0"].notna() & (show["line"] != "mal_irs")].copy()
    if d.empty:
        return
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
                             text=[f"-{v:.1f} pp" if v >= 0.05 else "" for v in d["cov_drop_pp"]], textposition="middle left",
                             textfont=dict(color=MUTED, size=12),
                             hovertemplate="%{y}<br>after: %{x:.0f}%<extra></extra>"))
    _layout(fig, h=60 + 42 * len(d), title=dict(text="Coverage now (open) and after the cut (filled), % of people in need",
                                                 font=dict(size=15)),
            legend=dict(orientation="h", y=-0.15, x=0), xaxis=dict(range=[-8, 102], ticksuffix="%"))
    st.plotly_chart(fig, **WIDE)


def _dose_chart(dr: pd.DataFrame, bucket: str, cur_cut: float, bb: pd.Series, res: dict, ptab: pd.DataFrame, iso3: str):
    col = hm.BUCKET_COLORS[bucket]
    h = col.lstrip("#")
    fill = f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},0.15)"
    x = dr["cut"] * 100
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(x) + list(x[::-1]), y=list(dr["hi"]) + list(dr["lo"][::-1]), fill="toself",
                             fillcolor=fill, line=dict(width=0), hoverinfo="skip", name="95% interval"))
    fig.add_trace(go.Scatter(x=x, y=dr["deaths_5y"], mode="lines", line=dict(color=col, width=2), name="Extra deaths, 5 yrs",
                             customdata=np.c_[dr["net_loss_usd"].map(money), dr["cov_drop_pp"].fillna(0)],
                             hovertemplate="%{x:.0f}% of aid cut (%{customdata[0]}/yr)<br>coverage -%{customdata[1]:.1f} pp"
                                           "<br>%{y:,.0f} extra deaths over 5 yrs<extra></extra>"))
    if cur_cut > 0:
        fig.add_trace(go.Scatter(x=[cur_cut * 100], y=[bb["deaths_5y"]], mode="markers+text", name="This scenario",
                                 marker=dict(size=11, color=col, line=dict(color="white", width=2)),
                                 text=["this scenario"], textposition="top left", textfont=dict(color=MUTED),
                                 hovertemplate="this scenario: %{x:.0f}% cut, %{y:,.0f} deaths<extra></extra>"))
    _layout(fig, h=360, title=dict(text=f"{bucket}: extra deaths over 5 years vs. share of aid cut", font=dict(size=15)),
            showlegend=False, xaxis=dict(title="% of this bucket's aid cut (all donors)", ticksuffix="%"),
            yaxis=dict(title="extra deaths, 5 years", rangemode="tozero"))
    st.plotly_chart(fig, **WIDE)
    _caption("Uniform cut across all donors, using the government response chosen above. The curve flattens once "
               "everyone whose service donors pay for has lost it, and kinks where government backfill runs out of fiscal space.")


def _path_chart(res: dict):
    p = res["path"]
    fig = go.Figure()
    for b in hm.BUCKETS:
        fig.add_trace(go.Bar(x=[f"Year {i}" for i in p.index], y=p[b], name=b, marker=dict(color=hm.BUCKET_COLORS[b],
                             line=dict(color="white", width=2)),
                             hovertemplate=f"{b}<br>%{{x}}: %{{y:,.0f}} extra deaths<extra></extra>"))
    cum = p.sum(axis=1).cumsum()
    fig.update_layout(barmode="stack", bargap=0.35)
    _layout(fig, h=420, title=dict(text=f"Extra deaths per year after the cut (cumulative after 5 years: {num(cum.iloc[-1])})",
                                   font=dict(size=15)),
            legend=dict(orientation="h", y=-0.12, x=0), yaxis=dict(title="extra deaths in that year"))
    st.plotly_chart(fig, **WIDE)
    _caption("ART interruption mortality rises from ~1% to ~5% a year as immunity declines; unvaccinated birth cohorts "
               "accumulate; nets already hanging keep protecting for about a year.")


def _fiscal_panel(res: dict, country_name: str, imf: dict):
    F = res["fiscal"]
    st.subheader(f"Can {country_name} fill the gap? Fiscal space")
    rev = F["revenue"]
    if (pd.isna(rev) or not rev) and imf.get("revenue_pct_gdp") and F["gdp"]:
        rev = imf["revenue_pct_gdp"] / 100 * F["gdp"]
    debt = F["debt_pct_gdp"] if not pd.isna(F["debt_pct_gdp"]) else imf.get("debt_pct_gdp", np.nan)
    G = F["gross_loss"]
    k = st.columns(5)
    _metric(k[0], "Gov. health spending (GHES), 2023", money(F["ghes"]),
            f"${F['ghes_pc']:,.0f} per person · {F['ghes_pct_gdp']:.1f}% of GDP" if not pd.isna(F["ghes_pc"]) else None)
    _metric(k[1], "Aid loss as % of GHES", f"{G / F['ghes']:.0%}" if F["ghes"] else "n/a")
    _metric(k[2], "Aid loss as % of gov. revenue", f"{G / rev:.1%}" if rev and not pd.isna(rev) else "n/a")
    _metric(k[3], "Interest as % of revenue",
            f"{F['interest_pct_revenue']:.0f}%" if not pd.isna(F["interest_pct_revenue"]) else "n/a",
            f"gross debt {debt:.0f}% of GDP" if not pd.isna(debt) else None)
    _metric(k[4], "Health share of gov. spending",
            f"{F['ghes_pct_gov_spend']:.1f}%" if not pd.isna(F["ghes_pct_gov_spend"]) else "n/a", "Abuja target: 15%")
    typical = F["ghes"] * max(F["ghes_growth_median"], 0)
    bars = [("Aid lost (gross, per year)", G, "#4d4d4d"),
            ("Backfill capacity (fiscal space)", F["capacity"], BACKFILL),
            ("Backfill applied in this run", F["replacement"], "#5dade2"),
            ("One year of typical GHES growth", typical, "#aab2bd")]
    fig = go.Figure(go.Bar(y=[b[0] for b in bars][::-1], x=[b[1] for b in bars][::-1], orientation="h",
                           marker=dict(color=[b[2] for b in bars][::-1], line=dict(color="white", width=2)),
                           text=[money(b[1]) for b in bars][::-1], textposition="outside", cliponaxis=False,
                           textfont=dict(color=INK), hovertemplate="%{y}: %{text}<extra></extra>"))
    _layout(fig, h=250, title=dict(text="The gap vs. what the budget can absorb (US$ per year)", font=dict(size=15)),
            xaxis=dict(showticklabels=False), margin=dict(l=10, r=80, t=40, b=10))
    a, b = st.columns([1.3, 1])
    with a:
        st.plotly_chart(fig, **WIDE)
    with b:
        yrs = G / typical if typical > 0 else np.inf
        _md(
            f"- **Backfill capacity** = GHES x ({'best-year' if F['effort'] == 'p90' else 'strong-year'} growth "
            f"{F['ghes_growth_top']:.0%} minus typical growth "
            f"{max(F['ghes_growth_median'], 0):.0%}) x debt-stress factor {F['stress_factor']:.2f} = **{money(F['capacity'])}/yr**.\n"
            f"- Filling the whole gap would take **{'more than 10' if yrs > 10 else f'{yrs:,.1f}'} years** of the "
            f"country's typical GHES growth, all of it diverted to these four programs.\n"
            f"- The debt-stress factor shrinks capacity when interest eats more than 10% of revenue "
            f"(to a floor of 0.25 at 40%+).")
        _caption("Growth rates are real (constant 2023 US$) from IHME, 2001-2023. Interest, revenue and debt are World Bank "
                   "WDI, latest year (IMF data from this dashboard fill gaps where available).")


def _cross_country(sk, fiscal_t, ptab_json, iso3, preset):
    st.subheader("Across all countries: who is most exposed?")
    if not st.toggle("Run this scenario for every country (about 5-10 seconds)", value=False, key="m_all"):
        _caption("Switch on to compare countries under the same scenario and government response.")
        return
    A = _run_all(sk, fiscal_t, ptab_json)
    ci = _inputs()["ci"]
    A["name"] = A["iso3"]
    A = A[A["gross_loss_usd"] > 0].copy()
    if A.empty:
        st.info("No country loses aid in this scenario.")
        return
    tot = A[["gross_loss_usd", "net_loss_usd", "deaths_y1", "deaths_5y", "deaths_5y_lo", "deaths_5y_hi", "hiv_infections_5y"]].sum()
    k = st.columns(4)
    _metric(k[0], f"Aid lost, {len(A)} countries", money(tot["gross_loss_usd"]) + "/yr",
            f"net of backfill {money(tot['net_loss_usd'])}/yr")
    _metric(k[1], "Extra deaths, year 1", num(tot["deaths_y1"]))
    _metric(k[2], "Extra deaths over 5 years", num(tot["deaths_5y"]), "range " + rng(tot["deaths_5y_lo"], tot["deaths_5y_hi"]))
    _metric(k[3], "New HIV infections, 5 years", num(tot["hiv_infections_5y"]))
    _caption("Totals add country medians; the range adds country 2.5th and 97.5th percentiles, so it is wider than a "
               "jointly simulated interval.")
    A["deaths_per_100k"] = A["deaths_5y"] / A["pop"] * 1e5
    A["loss_pct_ghes_pct"] = A["loss_pct_ghes"] * 100
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
                                 customdata=np.c_[other["iso3"], other["net_loss_usd"].map(money), other["deaths_5y"].map(num)],
                                 hovertemplate="<b>%{customdata[0]}</b><br>aid loss = %{x:.0f}% of GHES<br>%{y:,.0f} deaths per "
                                               "100k over 5 yrs (%{customdata[2]})<br>net loss %{customdata[1]}/yr<extra></extra>",
                                 name="Countries"))
        me = d[d["iso3"] == iso3]
        if len(me):
            fig.add_trace(go.Scatter(x=me["loss_pct_ghes_pct"], y=me["deaths_per_100k"], mode="markers+text", text=[iso3],
                                     textposition="top center", textfont=dict(size=13, color=INK),
                                     marker=dict(size=sz[d["iso3"] == iso3], color="#c0392b", line=dict(color="white", width=2)),
                                     hoverinfo="skip", name="Selected country"))
        fig.add_vline(x=d["loss_pct_ghes_pct"].median(), line=dict(color=GRID, width=1, dash="dot"))
        fig.add_hline(y=d["deaths_per_100k"].median(), line=dict(color=GRID, width=1, dash="dot"))
        _layout(fig, h=480, title=dict(text="Fiscal exposure vs. health exposure", font=dict(size=15)), showlegend=False,
                xaxis=dict(type="log", title="aid lost as % of government health spending (log)", ticksuffix="%",
                           tickvals=LOG_TICKS, ticktext=[f"{v:g}" for v in LOG_TICKS]),
                yaxis=dict(type="log", title="extra deaths per 100,000 people over 5 yrs (log)",
                           tickvals=LOG_TICKS, ticktext=[f"{v:g}" for v in LOG_TICKS]))
        st.plotly_chart(fig, **WIDE)
        _caption("Bubble size = net aid lost per year. Top-right countries both lose a lot relative to their own budget and "
                   "lose many lives per capita: hardest to backfill, highest stakes. Dotted lines are medians.")
    with c2:
        top = A.sort_values("deaths_5y", ascending=False).head(15).iloc[::-1]
        fig = go.Figure()
        for b in hm.BUCKETS:
            fig.add_trace(go.Bar(y=top["iso3"], x=top[f"deaths_5y_{b}"], name=b, orientation="h",
                                 marker=dict(color=hm.BUCKET_COLORS[b], line=dict(color="white", width=1.5)),
                                 hovertemplate=f"%{{y}} · {b}: %{{x:,.0f}}<extra></extra>"))
        fig.update_layout(barmode="stack")
        _layout(fig, h=480, title=dict(text="15 countries with the most extra deaths (5 yrs)", font=dict(size=15)),
                legend=dict(orientation="h", y=-0.1, x=0))
        st.plotly_chart(fig, **WIDE)
    out = A.drop(columns=["name"]).sort_values("deaths_5y", ascending=False)
    st.download_button("Download all-country results (CSV)", out.to_csv(index=False).encode(),
                       file_name=f"model_results_{preset.replace(' ', '_')}.csv", mime="text/csv")


METHODS = r"""
**1. Money.** Baseline aid is the 2021-2023 average from the IHME Development Assistance for Health database (constant 2023 US$),
kept at the level of *source x channel x program area* for each recipient. Program areas are grouped into service lines:
HIV treatment (treatment + care + testing), PMTCT, prevention, OVC; TB case finding & treatment, drug-resistant TB; malaria
bednets/other vector control, indoor spraying, case management; vaccines. Aid with no program area reported is spread over the
bucket's known mix (the country's own, or the global mix if it has none). Systems money (HSS: labs, staff, M&E) is lost in
full, but only a share κ (default 50%) is assumed to translate into lost services. A scenario sets a cut for every cell; donor
and channel cuts combine as 1 - (1 - donor cut)(1 - channel cut).

**2. Fiscal response.** Replacement R = min(θ x gross loss, capacity), where capacity = GHES x (75th-percentile, or 90th for the
"best years" ceiling, minus median real GHES growth, 2001-2023) x debt-stress factor (1 at interest ≤ 10% of revenue, falling linearly to 0.25 at 40%). The *historical*
θ comes from a two-way fixed-effects regression of the change in GHES per capita on falls (and lagged falls) in DAH per capita
across 97 countries; the estimate is slightly negative and not significant, i.e. no historical backfilling. Replacement money
is allocated pro-rata or "lives first" (lines with the most deaths averted per dollar first).

**3. Coverage.** People losing a service = net loss ÷ unit cost x (1 - continuity), capped at the number currently covered.
Unit costs = commodity cost + delivery cost x (GDP per capita / $2,000)^0.4. Coverage drop = people losing service ÷ population
in need: PLHIV (prevalence x population 15-64, calibrated to UNAIDS 2011 counts, + children), HIV+ pregnancies, TB incidence,
population at malaria risk, malaria cases, births.

**4. Lives.**
- *ART:* excess deaths among people off ART rise 1.2%, 2.8%, 3.8%, 4.5%, 5% in years 1-5 (x an uncertain multiplier); they
  also transmit HIV (0.04 infections per person-year).
- *PMTCT:* infections averted per mother (0.22) x death by age 2 if infected (0.45).
- *TB:* deaths per patient untreated = case-fatality untreated minus treated (WHO: 0.43 vs 0.03 HIV-negative; higher for HIV-positive,
  weighted by the country's TB/HIV share and ART coverage).
- *Malaria:* Lives Saved Tool form, D₁ = D₀ x Π (1 - E·C₁)/(1 - E·C₀) with E = 0.45 for vector control and 0.60 for case
  management, D₀ = malaria deaths (WHO/MCEE child malaria deaths ÷ under-5 share: 0.76 in Africa, 0.40 elsewhere).
- *Vaccines:* future deaths averted per child immunised (Gavi: 0.017-0.024) x country under-5 mortality ÷ 50.
- Year-by-year lags: deaths build up over 5 years (see the path chart).

**Uncertainty.** All parameters in the table are drawn from triangular(low, central, high); 400 draws per country. Headline numbers are
the central-parameter run; ranges are the 2.5th and 97.5th percentiles.

**Cross-check.** Two-way fixed-effects regressions of ART coverage, TB treatment coverage and DTP3 on log(1 + aid per person in need)
(2-year moving average), log GHES per capita and log GDP per capita, 2005-2023, SEs clustered by country.

**Data.** IHME DAH 1990-2025 (Sept 2026 release), IHME health spending 1995-2023 and expected spending 2024-2050, IHME GDP; World Bank WDI
(UNAIDS, WHO, WUENIC, UN IGME series) and Gapminder's mirrors of WHO TB estimates and WHO/MCEE child cause-of-death estimates; the team's MOU /
co-financing sheet.

**Limitations.** Unit costs are averages, but cuts hit marginal services first; some cut services are cheaper or dearer. Coverage
indicators for malaria come from household surveys and can be old. Program-area tags in IHME are partial (most TB aid is untagged).
The model does not capture second-round effects (drug resistance, outbreaks such as measles, health-worker layoffs) or
re-allocation by other donors, and post-2023 aid is not observed at the recipient level. Treat outputs as scenario estimates,
not forecasts.
"""
