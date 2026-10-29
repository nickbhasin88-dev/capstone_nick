"""
Validation & Benchmarks: how the funding-cut model compares with published estimates and with two other ways of
estimating the same cut. Linked from the sidebar; uses the country, scenario and settings chosen on the dashboard.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import theme as th


import health_model as hm
import model_section as ms
import scenarios as scn
from country_lists import dropdown_countries
from model_section import chart, num, rng, title_case

METHOD_COLORS = {"Unit-Cost Model": th.GRAPE, "Poisson Regression": th.BLUE, "Lancet Rate Ratios": th.TEAL}
CATEGORIES = ["HIV", "TB", "Malaria", "Immunization", "Maternal"]
CATEGORY_LABELS = {"Immunization": "Under-5", "Maternal": "Maternal"}

# --------------------------------------------------------------------------- #
# Country and scenario (start from the dashboard's choices)
# --------------------------------------------------------------------------- #
I = ms._inputs()
ctx = st.session_state.get("model_ctx", {})
names = dropdown_countries()
isos = list(names)
st.title("Validation & Benchmarks")
st.caption("How the funding-cut model on the dashboard compares with published studies, and with two other ways of "
           "estimating the same cut.")
# country and scenario are shared with the other pages
pc1, pc2 = st.columns(2)
with pc1:
    iso3 = th.shared_select("Country", isos, "v_country", "sel_iso3", "KEN", format_func=names.get)
with pc2:
    preset, _grp, _note = ms.donor_scenario_select(I["ci"], iso3, names[iso3], "v_preset")
    if _note:
        st.caption(ms._esc(_note))
fiscal_t = tuple(ctx.get("fiscal_t", scn.DEFAULT_FISCAL))
ptab_json = ctx.get("ptab_json", ms._default_params().to_json(orient="split"))
trend = ctx.get("trend", scn.DEFAULT_MORTALITY_TREND)
opts = ctx["opts"] if preset == ctx.get("preset") and "opts" in ctx else scn.default_opts(preset, I["ci"])
country_name = names[iso3]
st.session_state["model_ctx"] = {**ctx, "iso3": iso3, "country_name": country_name, "preset": preset, "opts": opts,
                                 "fiscal_t": fiscal_t, "ptab_json": ptab_json, "trend": trend}
st.caption(ms._esc(scn.preset_description(preset, opts)) + f" Government response ({ms._resp_label(fiscal_t)}), model parameters and the "
           "death-rate setting follow the dashboard.")

# --------------------------------------------------------------------------- #
# A. Published estimates
# --------------------------------------------------------------------------- #
th.section_header("fact_check", "How Our Totals Compare with Published Estimates", rule=False)

rows, all_country = [], {}
for p in scn.PRECOMPUTED_PRESETS:
    path = scn.precomputed_path(hm.MODEL_DIR, p)
    if not path.exists():
        continue
    A = scn.load_precomputed(hm.MODEL_DIR, p)
    all_country[p] = A
    rows.append({"Scenario": title_case(scn.display_name(p)) + (f" ({len(A)} MOU Countries With Funding Data)" if p == ms.MOU else ""),
                 **{b: num(A[f"deaths_5y_{b}"].sum()) for b in hm.BUCKETS},
                 "All Four": num(A["deaths_5y"].sum()),
                 "Range Across Parameter Values": rng(*hm.total_range(A, "deaths_5y"))})
st.subheader(f"Model: Extra Deaths Over 5 Years, All {len(next(iter(all_country.values()), []))} Countries",
             help="America First MOUs covers only the countries with a signed MOU and schedule data.")
st.table(pd.DataFrame(rows).set_index("Scenario"))
st.caption("Read from the precomputed results: No Government Replacement, death rates already falling, default "
           "parameters. Range across parameter values = 2.5th-97.5th percentile of the all-country total over the 400 "
           "draws. " + ms.RANGE_TIP)

us = all_country.get("Full US exit")
if us is not None:
    lifetime, _ = ms.deaths_per_child_immunised(us["iso3"], I, ms._default_params())
    per_year = {b: us[f"deaths_5y_{b}"].sum() / 5 for b in hm.BUCKETS}
    pub = pd.DataFrame([
        {"Source": "Cavalcanti et al. 2025, Lancet",
         "What It Measures": "Deaths averted by USAID programs, 2001-2021, 133 countries",
         "Published": "HIV 25.5M, malaria 8.0M, TB 4.7M, under-5 30.4M (about 1.21M, 0.38M, 0.22M and 1.45M a year)",
         "Closest Model Figure": f"US Bilateral Exit + Multilateral Withdrawals, extra deaths a year: HIV {num(per_year['HIV'])}, malaria "
                                 f"{num(per_year['Malaria'])}, TB {num(per_year['TB'])}, immunization "
                                 f"{num(per_year['Immunization'])}"},
        {"Source": "Cavalcanti et al. 2025, Lancet",
         "What It Measures": "Extra deaths by 2030 if USAID is defunded, all causes and all USAID sectors",
         "Published": "14.1M",
         "Closest Model Figure": f"US Bilateral Exit + Multilateral Withdrawals: {num(us['deaths_5y'].sum())} over 5 years (four diseases)"},
        {"Source": "UNAIDS 2025 (Goals model)",
         "What It Measures": "Extra AIDS deaths if PEPFAR ends, 2025-2029",
         "Published": "More than 4 million",
         "Closest Model Figure": f"US Bilateral Exit + Multilateral Withdrawals, HIV: {num(us['deaths_5y_HIV'].sum())} over 5 years"},
        {"Source": "Optima (Burnet Institute; ten Brink et al. 2025, Lancet HIV)",
         "What It Measures": "Extra HIV deaths from international HIV funding cuts plus PEPFAR ending, 2025-2030",
         "Published": "0.8M to 2.9M",
         "Closest Model Figure": f"US Bilateral Exit + Multilateral Withdrawals, HIV: {num(us['deaths_5y_HIV'].sum())} over 5 years"},
        {"Source": "Gavi",
         "What It Measures": "Future deaths averted per child immunised, since 2000",
         "Published": "About 0.017 (20.6M deaths / 1.2B children)",
         "Closest Model Figure": f"{lifetime:.3f} per fully immunized child over a lifetime (VIMC, Toor et al. 2021, by country and antigen; births-weighted; excludes DTP, polio and BCG)"},
    ])
    st.subheader("Published Estimates", help=(
        "The scopes differ, so the model should come in below most of these figures. The Cavalcanti totals cover all "
        "causes of death and every USAID sector, while the model covers four diseases and only the aid that pays for "
        "HIV, TB, malaria and vaccine services. Cavalcanti, UNAIDS and Optima look at US (or USAID, or PEPFAR) money "
        "only; the 'US Bilateral Exit + Multilateral Withdrawals' scenario is the closest match, but the model also tracks every other donor. The "
        "USAID figures are deaths averted over 21 years of programs, so they are compared per year. Gavi's figure is "
        "lifetime deaths averted per child; the model's is the same quantity at each country's current under-5 "
        "mortality."))
    st.table(pub.set_index("Source"))
    st.caption("The published studies cover more causes, sectors or years than the model, so the model should come in "
               "below most of these figures.")

# --------------------------------------------------------------------------- #
# B. Three methods for the selected country and scenario
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# Model check: donor money above the modelled service cost
# --------------------------------------------------------------------------- #
@st.cache_data(show_spinner=False)
def _excess(ptab_json: str) -> pd.DataFrame:
    import io
    return hm.donor_cost_excess(I, pd.read_json(io.StringIO(ptab_json), orient="split"))


th.section_header("rule", "Lines Where Donor Money Exceeds the Modelled Service Cost")
ex = _excess(ptab_json)
_ln = I["lines"]
n_lines = len(_ln[_ln["line"].isin(hm.ALL_DIRECT)][["iso3", "line"]].drop_duplicates())   # country-lines with aid
st.markdown(th.pills_html([
    ("Country-Service Lines Affected", f"{len(ex):,}", "", f"of {n_lines:,} modelled"),
    ("Countries With At Least One", f"{ex['iso3'].nunique() if len(ex) else 0}", "", f"of {len(names)}"),
    (f"Lines in {country_name}", f"{(ex['iso3'] == iso3).sum() if len(ex) else 0}", "", ""),
], large=True), unsafe_allow_html=True)
if len(ex):
    by_line = ex.groupby("line").size().rename(index=lambda l: hm.LINE_LABELS.get(l, l)).sort_values(ascending=False)
    st.table(pd.DataFrame({"Service": [title_case(i) for i in by_line.index], "Countries": by_line.values})
             .set_index("Service"))
st.caption("In these lines, baseline donor aid ÷ cost per person is more than the donor-funded pool (people currently "
           "covered x the external share of the country's spending on the disease: WHO GHED external share of public "
           "spending for HIV and immunization, WHO TB financing for TB, and for malaria the people the donor money for each "
           "intervention pays for; a regional median where a country has none), so the excess pays for "
           "things other than the service itself (systems, campaigns, newer products). People losing the service are "
           "then that pool x the share of donor money lost, instead of aid lost ÷ cost per person (logic review L-44).")

# --------------------------------------------------------------------------- #
# People on ART that donor money pays for: model vs PEPFAR's reported figure (audit I-09)
# --------------------------------------------------------------------------- #
@st.cache_data(show_spinner=False)
def _on_art(ptab_json: str) -> pd.DataFrame:
    import io
    return hm.donor_funded_on_art(I, pd.read_json(io.StringIO(ptab_json), orient="split"))


th.section_header("medication", "People on ART Paid for by Donors: Model vs PEPFAR")
_art = _on_art(ptab_json)
st.markdown(th.pills_html([
    ("Model: Donor-Funded People on ART", ms.num(_art["donor_funded_on_art"].sum()), "",
     f"all donors, {len(_art)} dashboard countries"),
    ("PEPFAR: People on ART It Supports", ms.num(hm.PEPFAR_ON_ART), "", "PEPFAR's reported figure"),
], large=True), unsafe_allow_html=True)
st.caption(ms._esc(
    "Model = for each country, the smaller of the people on ART (outside PMTCT) and donor HIV treatment money ÷ cost per "
    "patient-year, added up. It counts full-cost equivalents, each treated by the model as a person who stops ART. PEPFAR counts everyone on ART at sites it supports, "
    "including people whose drugs the government or the Global Fund buys, so its figure is larger by design. HIV "
    "testing and care money is not counted here; in the model, " + ms.care_ct_note()[0].lower() + ms.care_ct_note()[1:]))

# --------------------------------------------------------------------------- #
# Malaria inputs: Malaria Atlas Project 2025 vs the values used before (audit I-11)
# --------------------------------------------------------------------------- #
th.section_header("coronavirus", "Malaria Inputs: Malaria Atlas Project 2025 vs Previous Sources")
_ci = I["ci"]
_iso_model = [c for c in _ci.index if c in set(_ln.iso3)]
_mc = _ci.loc[_iso_model]
_d0 = _mc["malaria_deaths"].sum()
_dy = pd.to_numeric(_mc["malaria_deaths_year"], errors="coerce").dropna().astype(int)
st.markdown(th.pills_html([
    ("Baseline Malaria Deaths, Dashboard Countries", f"{_d0:,.0f}", "",
     f"WHO estimates, mostly {_dy.mode()[0]}; {len(_mc[_mc['malaria_deaths'] > 0])} countries with malaria deaths"),
    ("WHO Global Malaria Deaths, 2024", f"{ms.WHO_MALARIA_DEATHS_2024:,}", "", "World Malaria Report 2025"),
    ("Share Covered by the Dashboard", f"{_d0 / ms.WHO_MALARIA_DEATHS_2024:.0%}", "",
     "the dashboard models a subset of countries"),
], large=True), unsafe_allow_html=True)
_cmp = ms.malaria_input_comparison(_mc, names)
st.dataframe(_cmp.set_index("Country"), **ms.WIDE)
st.caption(ms._esc(
    "Treatment now = MAP effective treatment per 100 malaria cases, 2025; before = the latest household survey of "
    "children with fever given antimalarials, used only where incidence was at least 50 per 1,000 at risk. Bednets "
    "now = MAP ITN use, 2025, or a household survey from 2015 on; before = WHO/MAP modelled use or the latest survey "
    "of any year. Cases now = MAP P. falciparum + P. vivax clinical cases, 2025; before = WHO World Malaria Report "
    f"estimates. ⚑ = cases differ by more than 30% ({_cmp['Cases: Change'].str.contains('⚑').sum()} of {len(_cmp)} "
    "countries). Source: Malaria Atlas Project (data.malariaatlas.org), downloaded 13 October 2026; WHO World "
    "Malaria Report 2025."))

# Pakistan: the largest case gap among high-burden countries (decision on the malaria batch)
if "PAK" in _mc.index:
    import malaria_inputs as mi
    _pf, _pv = mi.load("pf_cases").query("iso3 == 'PAK'").set_index("year")["value"], \
        mi.load("pv_cases").query("iso3 == 'PAK'").set_index("year")["value"]
    _who = _mc.loc["PAK", "malaria_cases_prev"]
    st.caption(ms._esc(
        f"Pakistan: MAP puts cases at {ms.num(_mc.loc['PAK', 'malaria_cases'])} in 2025 against WHO's "
        f"{ms.num(_who)} (2024). MAP's P. falciparum estimate for 2024 ({ms.num(_pf.get(2024))}) is close to WHO's "
        f"total; the gap is P. vivax, which MAP puts at {ms.num(_pv.get(2024))} in 2024 and {ms.num(_pv.get(2025))} in "
        "2025, after the surge that followed the 2022 floods. P. vivax rarely kills, so Pakistan's baseline malaria "
        f"deaths (WHO, {_mc.loc['PAK', 'malaria_deaths']:,.0f}) are unchanged; the case number only sets how many "
        "people need treatment."))

th.section_header("event", "Data Years")
st.table(ms.data_years_table(_ci, _iso_model))
st.caption("Year = the most common year across the dashboard countries (range in brackets). Countries by source: "
           "how many countries use each source; the rest use a fallback that is flagged in Methods.")

th.section_header("compare_arrows", f"Three Ways to Estimate the Same Cut: {country_name}")
st.caption(f"{ms.scenario_title(preset, opts)} · {ms._resp_label(fiscal_t)}" + ("" if trend else " · Death Rates Held Constant"))

if iso3 not in I["ci"].index or iso3 not in set(I["lines"].iso3):
    st.info(f"{country_name} has no recorded HIV, TB, malaria or vaccine aid in 2021-2023, so there is nothing to model.")
    st.stop()

sk = scn.scenario_key(scn.build_scenario(preset, opts, I["ci"]))
res = ms._run(iso3, sk, fiscal_t, ptab_json, trend)
B = res["buckets"].set_index("bucket")
est = {"Unit-Cost Model": {b: (B.loc[b, "deaths_5y"], B.loc[b, "deaths_5y_lo"], B.loc[b, "deaths_5y_hi"])
                           for b in hm.BUCKETS}}
pp = hm.poisson_projection(res, I)
est["Poisson Regression"] = {r.bucket: (r.deaths_5y, r.deaths_5y_lo, r.deaths_5y_hi) for r in pp.itertuples()}
lp = hm.lancet_projection(res, I)
est["Lancet Rate Ratios"] = {r.bucket: (r.deaths_5y, np.nan, np.nan) for r in lp.itertuples()}

fig = go.Figure()
for method, vals in est.items():
    cats = [c for c in CATEGORIES if c in vals]
    v = np.array([vals[c][0] for c in cats])
    lo = np.array([vals[c][1] for c in cats])
    hi = np.array([vals[c][2] for c in cats])
    has_range = ~np.isnan(lo)
    fig.add_trace(go.Bar(
        x=[CATEGORY_LABELS.get(c, c) for c in cats], y=v, name=method,
        marker=dict(color=METHOD_COLORS[method]),
        error_y=dict(type="data", symmetric=False, array=np.where(has_range, hi - v, 0),
                     arrayminus=np.where(has_range, v - lo, 0), color=th.MUTED, thickness=1.2,
                     visible=bool(has_range.any())),
        hovertemplate=f"{method}<br>%{{x}}: %{{y:,.0f}} extra deaths over 5 years<extra></extra>"))
fig.add_hline(y=0, line=dict(color=th.MUTED, width=1))
fig.update_layout(barmode="group", bargap=0.25)
ms._layout(fig, h=460, title=ms._title(th.title_sub("Extra Deaths by Method", f"{country_name}, over 5 years")),
           legend=dict(orientation="h", y=-0.12, x=0, yanchor="top"),
           yaxis=dict(title="extra deaths over 5 years"))
chart(fig, source="Unit-cost model (this dashboard); Poisson regressions fitted for this project on 2005-2023 data; "
                  "rate ratios from Cavalcanti et al. 2025, Lancet.")


METHOD_PHRASE = {"Poisson Regression": "the Poisson regression", "Lancet Rate Ratios": "the Lancet rate-ratio estimate"}
METHOD_PLURAL = {"Poisson Regression": "the Poisson regression", "Lancet Rate Ratios": "the Lancet rate ratios"}
BUCKET_PHRASE = {"HIV": "HIV", "TB": "TB", "Malaria": "malaria", "Immunization": "under-5 deaths"}


def _reading() -> str:
    """One line: which alternative estimates land within a factor of two of the unit-cost model, and which don't."""
    agree, differ, wrong = {}, [], []
    for m in ("Poisson Regression", "Lancet Rate Ratios"):
        for b in hm.BUCKETS:
            base = est["Unit-Cost Model"][b][0]
            if b not in est[m] or base <= 0:
                continue
            v, word = est[m][b][0], BUCKET_PHRASE[b]
            if v < 0:
                wrong.append(f"{METHOD_PHRASE[m]} for {word}")
            elif 0.5 <= v / base <= 2:
                agree.setdefault(m, []).append(word)
            else:
                differ.append(f"{METHOD_PHRASE[m]} for {word} is {v / base:.1f}x the model "
                              f"({'higher' if v > base else 'lower'})")
    parts = [f"{METHOD_PLURAL[m]} ({', '.join(w)})" for m, w in agree.items()]
    out = f"In {country_name}, "
    out += (" and ".join(parts) + " land within a factor of two of the unit-cost model") if parts else \
        "no other method lands within a factor of two of the unit-cost model"
    out += ("; " + "; ".join(differ) + ".") if differ else "."
    if wrong:
        w = ", ".join(wrong)
        out += (" " + w[0].upper() + w[1:] + " comes out negative: historically, aid has gone where deaths "
                "were high, so that regression can neither confirm nor rule out the model.")
    return out


st.markdown("**Reading:** " + _reading())

tbl = pd.DataFrame({
    "Bucket": [CATEGORY_LABELS.get(c, c) for c in CATEGORIES],
    **{m: [(f"{num(vals[c][0])}" + (f" ({rng(vals[c][1], vals[c][2])})" if not np.isnan(vals[c][1]) else ""))
           if c in vals else "Not Covered" for c in CATEGORIES] for m, vals in est.items()},
})
notes = ["Ranges: for the unit-cost model, the range across parameter values (" + ms.RANGE_TIP[0].lower()
         + ms.RANGE_TIP[1:-1] + "); for the Poisson regression, a 95% confidence interval from the coefficient's "
         "standard error. The Lancet ratios are point estimates."]
if len(lp):
    r = lp.iloc[0]
    notes.append(f"US-source health aid in {country_name} falls from US\\${r.us_aid_pc_before:,.2f} to "
                 f"US\\${r.us_aid_pc_after:,.2f} per person in this scenario ({r.us_cut_share:.0%} of US money in the "
                 "modelled programs, net of any government replacement).")
row = I["ci"].loc[iso3]
if not pd.isna(row.get("hiv_deaths_unaids", np.nan)):
    notes.append(f"HIV baseline deaths ({num(row['hiv_deaths_unaids'])} a year) = UNAIDS AIDSinfo 2026 estimates, "
                 f"AIDS-related deaths, all ages, {int(row['hiv_deaths_unaids_year'])}.")
elif not pd.isna(row.get("hiv_deaths_est", np.nan)):
    notes.append(f"HIV baseline deaths ({num(row['hiv_deaths_est'])} a year) = IHME's HIV share of all deaths in "
                 f"{int(row['hiv_death_share_year'])} (Gapminder) x the current crude death rate x population; "
                 f"{int(row['hiv_death_share_year'])} is the latest year in that series (UNAIDS has no estimate for "
                 "this country).")
notes.append("The Poisson regression applies the change in child malaria deaths proportionally to all-age malaria "
             "deaths, and its under-5 estimate covers all child health and vaccine aid, so it is compared with the "
             "immunization bucket.")
st.subheader("Estimates by Method", help=" ".join(notes))
st.table(tbl.set_index("Bucket"))
st.caption("Ranges: unit-cost model = range across parameter values (parameter uncertainty only; data and model "
           "structure not included); Poisson regression = 95% confidence interval; the Lancet ratios are point "
           "estimates.")

# --------------------------------------------------------------------------- #
# C. How each method works
# --------------------------------------------------------------------------- #
th.section_header("functions", "How Each Method Works")
c1, c2, c3 = st.columns(3, gap="large")
with c1:
    st.subheader("Unit-Cost Model")
    st.markdown("Follows the money: aid lost, minus what the government replaces, divided by the cost of serving one "
                "person, gives the people who lose HIV treatment, TB care, bednets or vaccines; each lost service is "
                "then turned into deaths using published effect sizes and the country's own disease burden.  \n"
                "**Main limitation:** it uses average costs and assumes nothing else adjusts, so it describes an abrupt "
                "cut; real cuts hit marginal services first and other funders sometimes step in.")
with c2:
    st.subheader("Poisson Regression")
    st.markdown("Our own version of the Lancet method: across up to 97 countries and 2005-2023, it asks how deaths "
                "moved within each country when its aid per person moved, controlling for income, government health "
                "spending and global trends (country and year fixed effects, population offset).  \n"
                "**Main limitation:** it measures associations, not causes. Aid tends to go where deaths are high, which "
                "can hide, or even reverse, the protective effect.")
with c3:
    st.subheader("Lancet Rate Ratios")
    st.markdown("Applies the published Cavalcanti et al. (2025) rate ratios, which link USAID health funding per "
                "person to lower HIV, malaria and maternal death rates, to the drop in this country's US-source health "
                "aid.  \n"
                "**Main limitation:** the ratios were estimated for USAID funding across 133 countries in 2001-2021 "
                "and are applied here to one country, using IHME's US-source aid as the funding measure, with HIV "
                "deaths from a 2019 share.")

reg = I["reg"]
specs = [("poisson_tb", "TB Deaths", "TB aid per person"),
         ("poisson_u5", "Under-5 Deaths", "Vaccine + child health aid per birth"),
         ("poisson_malaria", "Child Malaria Deaths (Africa)", "Malaria aid per person")]
st.subheader("Our Poisson Regressions")
st.table(pd.DataFrame([{
    "Outcome": lbl, "Aid Measure (Log 1 + US$)": title_case(aid),
    "Coefficient": f"{reg[k]['coef'][reg[k]['x'][0]]:+.3f}", "Standard Error": f"{reg[k]['se'][reg[k]['x'][0]]:.3f}",
    "Countries": reg[k]["n_countries"], "Observations": f"{reg[k]['n_obs']:,}",
    "Years": f"{reg[k]['years'][0]}-{reg[k]['years'][1]}"} for k, lbl, aid in specs if k in reg]).set_index("Outcome"))
st.caption("A negative coefficient means more aid has gone with fewer deaths. Controls: log GDP per capita and log "
           "government health spending per capita; country and year fixed effects; standard errors clustered by country.")
