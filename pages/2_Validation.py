"""
Validation & Benchmarks: how the funding-cut model compares with published estimates and with two other ways of
estimating the same cut. Linked from the sidebar; uses the country, scenario and settings chosen on the dashboard.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import health_model as hm
import model_section as ms
import scenarios as scn
from country_lists import dropdown_countries
from model_section import chart, how_to_read, num, rng, stat, title_case, what_this_shows
from scenarios import PRESETS

st.set_page_config(page_title="Validation & Benchmarks", page_icon="📊", layout="wide")

METHOD_COLORS = {"Unit-Cost Model": "#5d6d7e", "Poisson Regression": "#1b6ca8", "Lancet Rate Ratios": "#c0392b"}
CATEGORIES = ["HIV", "TB", "Malaria", "Immunization", "Maternal"]
CATEGORY_LABELS = {"Immunization": "Immunization / Under-5", "Maternal": "Maternal"}

# --------------------------------------------------------------------------- #
# Sidebar: country and scenario (start from the dashboard's choices)
# --------------------------------------------------------------------------- #
I = ms._inputs()
ctx = st.session_state.get("model_ctx", {})
names = dropdown_countries()
isos = list(names)
with st.sidebar:
    st.page_link("app.py", label="Dashboard", icon=":material/dashboard:")
    st.page_link("pages/2_Validation.py", label="Validation & Benchmarks", icon=":material/fact_check:")
    st.divider()
    # seed once from the dashboard's choices (stable keys, so later picks always register)
    if st.session_state.get("v_country") not in isos:
        st.session_state["v_country"] = ctx["iso3"] if ctx.get("iso3") in isos else "KEN"
    if st.session_state.get("v_preset") not in PRESETS:
        st.session_state["v_preset"] = ctx.get("preset", list(PRESETS)[0])
    iso3 = st.selectbox("Country", isos, format_func=names.get, key="v_country")
    preset = st.selectbox("Donor Scenario", list(PRESETS), format_func=title_case, key="v_preset")
    st.caption(PRESETS[preset].replace("$", "\\$"))
fiscal_t = tuple(ctx.get("fiscal_t", scn.DEFAULT_FISCAL))
ptab_json = ctx.get("ptab_json", ms._default_params().to_json(orient="split"))
trend = ctx.get("trend", scn.DEFAULT_MORTALITY_TREND)
opts = ctx["opts"] if preset == ctx.get("preset") and "opts" in ctx else scn.default_opts(preset, I["ci"])
country_name = names[iso3]
st.session_state["model_ctx"] = {**ctx, "iso3": iso3, "country_name": country_name, "preset": preset, "opts": opts,
                                 "fiscal_t": fiscal_t, "ptab_json": ptab_json, "trend": trend}
with st.sidebar:
    st.caption(f"Government response ({ms._resp_label(fiscal_t)}), model parameters and the death-rate setting follow "
               "the dashboard.")

st.title("Validation & Benchmarks")
st.caption("How the funding-cut model on the dashboard compares with published studies, and with two other ways of "
           "estimating the same cut.")

# --------------------------------------------------------------------------- #
# A. Published estimates
# --------------------------------------------------------------------------- #
st.header("A. How Our Totals Compare with Published Estimates")
what_this_shows("The model's all-country totals for each scenario, next to the best-known published estimates of what "
                "aid cuts and aid programs do to deaths.")

rows, all_country = [], {}
for p in scn.PRECOMPUTED_PRESETS:
    path = scn.precomputed_path(hm.MODEL_DIR, p)
    if not path.exists():
        continue
    A = pd.read_csv(path)
    all_country[p] = A
    rows.append({"Scenario": title_case(p), **{b: num(A[f"deaths_5y_{b}"].sum()) for b in hm.BUCKETS},
                 "All Four": num(A["deaths_5y"].sum()),
                 "Range": rng(A["deaths_5y_lo"].sum(), A["deaths_5y_hi"].sum())})
st.subheader("Model: Extra Deaths Over 5 Years, All 95 Countries")
st.table(pd.DataFrame(rows).set_index("Scenario"))
st.caption("Read from the precomputed results: no government backfill, death rates already falling, default "
           "parameters. Ranges add country 2.5th and 97.5th percentiles.")

us = all_country.get("Full US exit")
if us is not None:
    lifetime, _ = ms.deaths_per_child_immunised(us["iso3"], I, ms._default_params())
    per_year = {b: us[f"deaths_5y_{b}"].sum() / 5 for b in hm.BUCKETS}
    pub = pd.DataFrame([
        {"Source": "Cavalcanti et al. 2025, Lancet",
         "What It Measures": "Deaths averted by USAID programs, 2001-2021, 133 countries",
         "Published": "HIV 25.5M, malaria 8.0M, TB 4.7M, under-5 30.4M (about 1.21M, 0.38M, 0.22M and 1.45M a year)",
         "Closest Model Figure": f"Full US Exit, extra deaths a year: HIV {num(per_year['HIV'])}, malaria "
                                 f"{num(per_year['Malaria'])}, TB {num(per_year['TB'])}, immunization "
                                 f"{num(per_year['Immunization'])}"},
        {"Source": "Cavalcanti et al. 2025, Lancet",
         "What It Measures": "Extra deaths by 2030 if USAID is defunded, all causes and all USAID sectors",
         "Published": "14.1M",
         "Closest Model Figure": f"Full US Exit: {num(us['deaths_5y'].sum())} over 5 years (four diseases)"},
        {"Source": "UNAIDS 2025 (Goals model)",
         "What It Measures": "Extra AIDS deaths if PEPFAR ends, 2025-2029",
         "Published": "4.2M",
         "Closest Model Figure": f"Full US Exit, HIV: {num(us['deaths_5y_HIV'].sum())} over 5 years"},
        {"Source": "Optima (Burnet Institute; ten Brink et al. 2025, Lancet HIV)",
         "What It Measures": "Extra HIV deaths from international HIV funding cuts plus PEPFAR ending, 2025-2030",
         "Published": "0.8M to 2.9M",
         "Closest Model Figure": f"Full US Exit, HIV: {num(us['deaths_5y_HIV'].sum())} over 5 years"},
        {"Source": "Gavi",
         "What It Measures": "Future deaths averted per child immunised, since 2000",
         "Published": "About 0.017 (20.6M deaths / 1.2B children)",
         "Closest Model Figure": f"{lifetime:.3f} per child (births-weighted, today's mortality)"},
    ])
    st.subheader("Published Estimates")
    st.table(pub.set_index("Source"))
    how_to_read(
        "The scopes differ, so the model should come in below most of these figures. The Cavalcanti totals cover all "
        "causes of death and every USAID sector, while the model covers four diseases and only the aid that pays for "
        "HIV, TB, malaria and vaccine services. Cavalcanti, UNAIDS and Optima look at US (or USAID, or PEPFAR) money "
        "only; the 'Full US Exit' scenario is the closest match, but the model also tracks every other donor. The "
        "USAID figures are deaths averted over 21 years of programs, so they are compared per year. Gavi's figure is "
        "lifetime deaths averted per child; the model's is the same quantity at each country's current under-5 "
        "mortality.")

# --------------------------------------------------------------------------- #
# B. Three methods for the selected country and scenario
# --------------------------------------------------------------------------- #
st.divider()
st.header(f"B. Three Ways to Estimate the Same Cut: {country_name}")
what_this_shows("Extra deaths over five years from the same aid cut, estimated three different ways, so you can see "
                "whether the model's answer is in the right range.")
st.caption(f"{title_case(preset)} · {ms._resp_label(fiscal_t)}" + ("" if trend else " · Death Rates Held Constant"))

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
        marker=dict(color=METHOD_COLORS[method], line=dict(color="white", width=1.5)),
        error_y=dict(type="data", symmetric=False, array=np.where(has_range, hi - v, 0),
                     arrayminus=np.where(has_range, v - lo, 0), color="rgba(0,0,0,0.45)", thickness=1.2,
                     visible=bool(has_range.any())),
        hovertemplate=f"{method}<br>%{{x}}: %{{y:,.0f}} extra deaths over 5 years<extra></extra>"))
fig.add_hline(y=0, line=dict(color="rgba(0,0,0,0.35)", width=1))
fig.update_layout(barmode="group", bargap=0.25)
ms._layout(fig, h=460, title=ms._title(f"Extra Deaths Over 5 Years by Method, {country_name}"),
           legend=dict(orientation="h", y=1.02, x=1, xanchor="right", yanchor="bottom"),
           yaxis=dict(title="extra deaths over 5 years"))
chart(fig)


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
st.table(tbl.set_index("Bucket"))
notes = ["Ranges: 95% intervals (unit-cost model: parameter uncertainty; Poisson regression: the coefficient's standard "
         "error). The Lancet ratios are point estimates."]
if len(lp):
    r = lp.iloc[0]
    notes.append(f"US-source health aid in {country_name} falls from US\\${r.us_aid_pc_before:,.2f} to "
                 f"US\\${r.us_aid_pc_after:,.2f} per person in this scenario ({r.us_cut_share:.0%} of US money in the "
                 "modelled programs, net of any government backfill).")
row = I["ci"].loc[iso3]
if not pd.isna(row.get("hiv_deaths_est", np.nan)):
    notes.append(f"HIV baseline deaths ({num(row['hiv_deaths_est'])} a year) = IHME's HIV share of all deaths in "
                 f"{int(row['hiv_death_share_year'])} (Gapminder) x the current crude death rate x population; "
                 f"{int(row['hiv_death_share_year'])} is the latest year in that series.")
notes.append("The Poisson regression applies the change in child malaria deaths proportionally to all-age malaria "
             "deaths, and its under-5 estimate covers all child health and vaccine aid, so it is compared with the "
             "immunization bucket.")
how_to_read(" ".join(notes))

# --------------------------------------------------------------------------- #
# C. How each method works
# --------------------------------------------------------------------------- #
st.divider()
st.header("C. How Each Method Works")
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
