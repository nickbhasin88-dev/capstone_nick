"""
Methods: a full guide to how every number on the dashboard is calculated, where each input comes from, and which
values are assumptions. Key numbers (parameters, regression estimates) are read from the model's own files, so the
guide always matches what the model uses. The cross-checks use the country and scenario chosen on the dashboard.
"""
import io
import json
import textwrap

import pandas as pd
import streamlit as st

import health_model as hm
import model_section as ms
import scenarios as scn
import theme as th
from country_lists import dropdown_countries
from model_section import title_case

I = ms._inputs()
ctx = st.session_state.get("model_ctx", {})
names = dropdown_countries()
iso3 = st.session_state.get("sel_iso3", "KEN")
iso3 = iso3 if iso3 in names else "KEN"
country_name = names[iso3]
preset = st.session_state.get("sel_preset", list(scn.PRESETS)[0])
opts = ctx["opts"] if ctx.get("preset") == preset and ctx.get("opts") else scn.default_opts(preset, I["ci"])
fiscal_t = tuple(ctx.get("fiscal_t", scn.DEFAULT_FISCAL))
ptab_json = ctx.get("ptab_json", ms._default_params().to_json(orient="split"))
trend = ctx.get("trend", scn.DEFAULT_MORTALITY_TREND)
ptab = pd.read_json(io.StringIO(ptab_json), orient="split")

PRM = hm.load_params()                       # the parameter file the model reads (central / low / high / source)
C = PRM["central"].astype(float).to_dict()
UC = hm._uc_ref()                            # study costs in 2023 US$ (inflated from each study's cost year)
REG = json.loads((hm.MODEL_DIR / "regressions.json").read_text())
TH_C, TH_LO, TH_HI = hm.theta_historical(REG)
N_COUNTRIES = len(names)


def md(text: str):
    """Markdown from an indented block; '$' is escaped so it is never read as LaTeX."""
    st.markdown(ms._esc(textwrap.dedent(text).strip()))


def rng_txt(p: str, fmt: str = "{:g}") -> str:
    r = PRM.loc[p]
    return f"{fmt.format(float(r['central']))} ({fmt.format(float(r['low']))} to {fmt.format(float(r['high']))})"


def pct(p: str) -> str:
    return rng_txt(p, "{:.0%}")


st.title("Methods, Data and Limitations")
st.caption("A complete guide to how every number on the dashboard is calculated, where each input comes from, and "
           "which values are assumptions. Numbers quoted here are read from the model's own files.")

tabs = st.tabs(["Overview", "Dashboard Sections", "The Model, Step by Step", "Data Sources",
                "Assumptions & Limitations", "Parameters", "Cross-Checks"])

# =========================================================================== #
# OVERVIEW
# =========================================================================== #
with tabs[0]:
    th.section_header("info", "What the Dashboard Does", rule=False)
    md(f"""
    The dashboard has two halves.

    **Description (Sections 1 to 3).** What is spent on health in each country, who pays for it, and how the
    government's whole budget is raised and spent. These charts show published data with only light processing
    (grouping, unit conversion), described in *Dashboard Sections*.

    **Simulation (Section 4 and the All Countries page).** A four-step model that asks what happens if donors cut
    aid for HIV, TB, malaria and routine immunization:

    1. **Money**: how much aid each service loses (by donor, channel and program area).
    2. **Fiscal response**: how much of it the government replaces, limited by its fiscal space.
    3. **Coverage**: the money not replaced, divided by the cost of serving one person, is the number of people who
       lose a service.
    4. **Lives**: each lost service is turned into extra deaths using published effect sizes and the country's own
       disease burden.

    Every uncertain number is drawn at random many times (Monte Carlo), which gives the ranges shown. The model
    covers {N_COUNTRIES} countries.
    """)
    th.section_header("payments", "Units and Currency")
    md(f"""
    **Every dollar figure is in constant 2023 US dollars**, the unit IHME uses for its aid and health-spending data.
    IHME's constant dollars remove each country's own inflation and convert at 2023 exchange rates, so a country
    whose currency collapsed (for example Nigeria in 2023-24) does not appear to shrink.

    The IMF publishes GDP in *current* dollars, so for the header and Section 3 GDP is converted to the same basis:

    - GDP in 2023 is the IMF World Economic Outlook figure (in 2023, current and constant 2023 dollars are equal).
    - GDP in any other year = GDP in 2023 x (IHME real GDP per person in that year x population that year) /
      (IHME real GDP per person in 2023 x population in 2023). IHME's GDP per person comes from its GDP file (FGH
      2026); population is the IMF's. The conversion is done by `add_constant_dollars.py`.

    Costs taken from studies are brought to 2023 dollars with the US consumer price index (CPI-U) from each study's
    cost year (for example x{hm.CPI_U[2023] / hm.CPI_U[2018]:.3f} from 2018 and x{hm.CPI_U[2023] / hm.CPI_U[2014]:.3f}
    from 2014). IHME's aid data are reported in thousands of dollars and converted to dollars. Amounts are rounded for display
    ($1.2M, $3.4B); calculations use the unrounded values.
    """)
    th.section_header("schedule", "Time Periods")
    md("""
    | What | Years |
    |---|---|
    | Aid by donor and focus area (Section 2) | 2015-2023 (IHME's recipient-level data end in 2023) |
    | Health spending by source (Section 1) | 1995-2023 observed, 2024-2030 IHME projections (paler bars) |
    | Government revenue and spending (Section 3) | latest year with IMF data (user can pick earlier years) |
    | Aid baseline the model cuts | average of 2021, 2022 and 2023 (smooths lumpy bednet campaigns and Gavi tranches) |
    | Model horizon | five years after the cut, 2026-2030 |
    | Fiscal-space growth rates | 2001-2023 |
    | Mortality trends | 2010-2019 (before COVID-19) |
    """)

# =========================================================================== #
# DASHBOARD SECTIONS
# =========================================================================== #
with tabs[1]:
    th.section_header("badge", "Country Header", rule=False)
    md("""
    | Pill | How it is calculated | Source |
    |---|---|---|
    | Region | World Bank region code recorded with the country in the IHME aid database (most common value) | IHME DAH database |
    | Income Group | World Bank income classification; if missing, GDP per person below $1,150 = low, below $4,500 = lower-middle, otherwise upper-middle | World Bank country entities (Gapminder mirror) |
    | US MOU | "MOU Signed" if the team's MOU / co-financing sheet records a status of signed, or (when no status is recorded) has a 2026 US funding schedule; otherwise "No MOU" | Team's MOU / co-financing sheet |
    | GDP | Latest year the IMF reports as actual (not an estimate), in constant 2023 US$ (see *Units and Currency*) | IMF World Economic Outlook, IHME GDP |
    | Population | Same year as GDP | IMF World Economic Outlook |
    """)

    th.section_header("payments", "Section 1: Money Spent on Health")
    md("""
    **Data:** IHME Global Health Spending 1995-2023 and IHME Expected Health Spending 2024-2050.

    Total health spending is split into four sources that add up to the total:

    | Bar | IHME variable | Meaning |
    |---|---|---|
    | Government | `ghes_total` | Government health spending from domestic sources (taxes, social insurance) |
    | Prepaid Private | `ppp_total` | Private insurance and other prepaid schemes |
    | Out-of-Pocket | `oop_total` | Paid by households at the point of care |
    | Foreign Aid for Health (DAH) | `dah_total` | Development assistance for health: money from foreign governments, multilaterals and foundations |

    - **US$ Total** shows the totals; **US$ per Person** uses IHME's per-capita values; **Share of Total** divides each
      source by total health spending.
    - Years after 2023 are IHME's *expected* (projected) spending, drawn paler.
    - **Foreign Aid Share of Total** = DAH ÷ total health spending, for 2023 and for 2030 (expected).
    """)

    th.section_header("public", "Section 2: Who Is Providing the Money")
    md("""
    **Data:** IHME Development Assistance for Health database (1990-2026 release), variable `dah_23` (constant
    2023 US$) by year, **source** (who originally paid), **channel** (who delivered it) and recipient country.

    **Funders.** United States, Gates Foundation, Private Philanthropy (IHME's "private other" plus "corporate
    donations"), United Kingdom, Germany and France always get their own fixed color. Any other funder among the
    country's six largest over 2015-2023 gets one of three spare colors (generic categories such as "Other" and
    "Unallocable" never do). Everything else is grouped as All Other Sources. IHME's "debt repayments" source is
    labelled World Bank Lending (Loan Repayments).

    **NGO / foundation channels (lighter shade).** Money delivered through US NGOs (`NGO`), international NGOs
    (`INTLNGO`), US foundations (`US_FOUND`) and the Gates Foundation directly (`GATES`) is drawn at 45% opacity.
    Bilateral agencies, the Global Fund, Gavi, UN agencies, development banks and the European Commission are drawn
    solid. IHME does not record whether a government knew about a flow; the channel is used as a proxy, and the
    Channel Settings button lets you change which channels count.

    **Pills:** Total in 2023 = all aid that year; Via NGO / Foundation Channels = the lighter-shaded share; Largest
    Funder = the source with the most aid in 2023.

    **Where the Aid Is Spent.** IHME splits aid by health focus area (`hiv`, `tb`, `mal`, `rmh`, `nch`, `oid`,
    `ncd`, `swap_hss`) and, within each, by program area (for example HIV treatment, prevention, care). Six focus
    areas are shown separately; other infectious diseases, non-communicable diseases, "other" and unallocated aid are
    grouped as All Other (the hover shows the breakdown). Inside one focus area the six largest program areas are
    shown and the rest grouped.
    """)

    th.section_header("account_balance", "Section 3: Revenue and Spending")
    md("""
    **Data:** three IMF datasets.

    | Part | Dataset | Variables |
    |---|---|---|
    | Size of each side | IMF World Economic Outlook | general-government revenue, expenditure and net lending/borrowing, % of GDP; gross debt, % of GDP |
    | Revenue mix | IMF World Revenue Longitudinal Data (WoRLD) | revenue by type (income taxes, VAT, excise, trade taxes, grants, social contributions, ...), % of GDP |
    | Spending mix | IMF Government Finance Statistics, COFOG | spending by function (health, education, defence, ...), % of total outlays |

    **How the treemap is built.**

    1. Both sides are sized from the World Economic Outlook, which reports revenue and spending for the same level
       of government (general government). Revenue = `gov_revenue_pct_gdp`; spending = `gov_expenditure_pct_gdp`.
    2. Borrowing (deficit) = spending - revenue, which equals minus the WEO net lending figure. It is drawn on the
       revenue side (dark purple), so both sides are the same size. A surplus is drawn on the spending side.
    3. The revenue and COFOG files supply only the **mix** inside each side: each item's share of its file's total is
       applied to the WEO total. (The two files often cover different levels of government, for example central
       government for revenue and general government for spending, so their own totals are not comparable.)
    4. Interest on public debt is its own box and is not also counted inside General Public Services. If the COFOG
       shares add to more than 100%, the app rescales them to 100% and logs a warning.
    5. Dollar amounts = share of GDP x GDP in constant 2023 US$.
    6. If the WEO has no totals for a year, each side falls back to its own file's total, with a note.

    **Health check.** COFOG often records only part of health spending (for example, it may miss local
    governments). When COFOG health is less than half of IHME's government health spending (`ghes_per_gdp`), a
    caption says so and gives IHME's figure.
    """)

    th.section_header("monitor_heart", "Section 4 Outputs")
    md("""
    | Output | Definition |
    |---|---|
    | Aid at Risk (per Year) | Yearly HIV, TB, malaria and vaccine aid removed by the scenario (gross loss), out of the 2021-2023 average |
    | Replaced by Government | The government's replacement, set by the response chosen, capped by fiscal space |
    | Net Loss to Services | Aid at risk minus what is replaced |
    | Extra Deaths, Year 1 / Over 5 Years | Central estimate (all parameters at their central values); range = 2.5th to 97.5th percentile of the Monte Carlo draws |
    | New HIV Infections, 5 Years | Infections from people off ART, mothers without PMTCT, and lost prevention |
    | Every US$1 Million Lost | People losing the service per $1M = $1M ÷ cost per person x (1 - continuity); coverage drop = that ÷ people in need; extra deaths = deaths per dollar x $1M x (1 - continuity); "aid per death" = $5M (five years of $1M) ÷ those deaths |
    | What Each Service Loses | Per service line: baseline aid, aid lost after replacement, cost per person, people losing the service, coverage before and after, extra deaths (range) |
    | Extra Deaths as More Aid Is Cut | Solid line: every donor cuts this bucket by the same share, 0-100% in 5% steps, same random draws at every step; band = 95% range. Dashed line: this scenario's own cuts scaled from 0% to 100% of their size |
    | Extra Deaths Each Year | Central estimate by year and bucket |
    | Can {{Country}} Fill the Gap? | See *The Model, Step 2*; Aid Lost as % of Government Health Spending = gross loss ÷ government health spending in 2023; as % of revenue = gross loss ÷ (GDP x revenue % of GDP, World Bank WDI) |
    | All Countries | Totals add up country results; deaths per 100,000 = 5-year deaths ÷ population x 100,000; budget exposure = gross loss ÷ government health spending |
    """)

# =========================================================================== #
# THE MODEL
# =========================================================================== #
with tabs[2]:
    th.section_header("account_tree", "Step 1: Money (What Aid Is Lost)", rule=False)
    md("""
    **Baseline.** For each country, the IHME aid database is summed by **source group x channel group x service
    line** and averaged over 2021-2023. Each such combination is a *cell*.
    """)
    st.latex(r"\text{baseline}_{c} = \tfrac{1}{3}\sum_{y=2021}^{2023} \text{DAH}_{c,y}\times 1000 \quad"
             r"\text{(IHME reports thousands of constant 2023 US\$)}")
    md("""
    **Service lines** come from IHME program-area columns:

    | Service line | Bucket | IHME program-area columns |
    |---|---|---|
    | HIV treatment | HIV | `hiv_treat`, `hiv_care`, `hiv_ct` (testing) |
    | Prevention of mother-to-child transmission | HIV | `hiv_pmtct` |
    | HIV prevention | HIV | `hiv_prev` |
    | Orphans & vulnerable children | HIV | `hiv_ovc` |
    | HIV unspecified | HIV | `hiv_other`, `hiv_amr` |
    | HIV systems support | HIV | `hiv_hss_other`, `hiv_hss_hrh`, `hiv_hss_me` |
    | TB case finding & treatment | TB | `tb_treat`, `tb_diag` |
    | Drug-resistant TB | TB | `tb_amr` |
    | TB unspecified / systems | TB | `tb_other` / `tb_hss_*` |
    | Bednets & other vector control | Malaria | `mal_con_nets`, `mal_con_oth` |
    | Indoor residual spraying | Malaria | `mal_con_irs` |
    | Malaria testing & treatment | Malaria | `mal_diag`, `mal_treat`, `mal_comm_con` |
    | Malaria unspecified / systems | Malaria | `mal_other`, `mal_amr` / `mal_hss_*` |
    | Routine immunization | Immunization | `nch_cnv` (vaccines, newborn & child health) |

    **Source groups** (who paid): United States, United Kingdom, Germany, France, Japan, Canada, Netherlands,
    Nordics (Sweden, Norway, Denmark, Finland), Gates Foundation, Other private (private other, corporate donations),
    Development-bank lending (IHME "debt repayments"), Non-DAC governments (China and other non-DAC), Other /
    unallocable, and Other DAC governments (all remaining donor governments).

    **Channel groups** (who delivered it): Bilateral agency (all `BIL_*`), NGOs (`NGO`, `INTLNGO`, `US_FOUND`),
    Gates direct, Global Fund, Gavi, WHO (incl. PAHO), UNICEF, UNFPA, UNAIDS, Unitaid, Development banks (World
    Bank IDA/IBRD, AfDB, AsDB, IDB), EU institutions, CEPI, Other. Bilateral, NGO, Gates-direct and Other are
    *direct* channels; the rest are *multilateral*.

    **The cut in each cell.** A scenario sets a cut for the source on direct channels, a cut for the source's money
    through multilaterals, optional cuts for a specific source-channel pair, and optional cuts for a channel that hit
    every donor (a replenishment shortfall). They combine multiplicatively:
    """)
    st.latex(r"\text{cut}_c = 1-(1-\text{donor cut})\,(1-\text{channel cut}),\qquad \text{loss}_c = \text{baseline}_c \times \text{cut}_c")
    md(f"""
    **Money with no reported purpose.** Aid tagged "unspecified" is spread over the bucket's known service lines in
    proportion to the country's own mix (or the global mix if it has none). Of systems money (labs, staff,
    monitoring), a share κ = {pct('hss_kappa')} is assumed to cut services; the rest is lost without a modelled
    service effect.
    """)
    st.latex(r"\text{effective loss}_{\ell} = \text{direct loss}_{\ell} + (\text{unspecified} + \kappa \times \text{systems}) \times \text{mix}_{\ell}")
    md("""
    **Donor scenarios (presets).**

    | Scenario | What is cut | Source of the numbers |
    |---|---|---|
    | Full US Exit | US direct aid -100%; US contributions through WHO, Gavi and UNFPA -100%; US Global Fund pledge -23% (US$6.0B to US$4.6B) | US announcements (WHO exit effective Jan 2026; Gavi June 2025); Global Fund 8th replenishment, Nov 2025 |
    | America First MOUs | US direct aid follows each country's 2026-2030 MOU schedule (US funding that year ÷ 2021-25 reference); countries without a schedule get the average MOU-country cut; US multilateral exits as above | Team's MOU / co-financing sheet |
    | IHME 2025 Preliminary Estimates | Each source x channel x disease cell changes by IHME's 2025 preliminary total ÷ its 2021-23 average (global ratio applied to the country's mix; cells under US$20M a year use the source x disease ratio; clipped to 0-1.5) | IHME DAH database, 2025 preliminary estimates |
    | OECD-Reported 2025 Aid Cuts | Each donor's 2025 change in total aid applied to its health aid: US -57%, Germany -17.4%, France -10.9%, UK -10.8%, Japan -5.6% | OECD preliminary 2025 ODA data, April 2026 |
    | Global Fund & Gavi Shortfalls | Every donor's money through the Global Fund -28% (US$11.34B vs US$15.7B) and Gavi -24% (about US$9B vs US$11.9B target) | Replenishment outcomes |
    | Combined Retreat | Full US Exit plus the OECD cuts for every other donor | As above |
    | Custom | Set by the user | |
    """)

    th.section_header("account_balance", "Step 2: Fiscal Response (What the Government Replaces)")
    md("""
    The gross loss G is the sum of all positive cell losses. The government wants to replace:

    - **No Backfill (Historical Norm):** nothing.
    - **Replace a Set Share:** a share θ chosen by the user, θ x G.
    - **As Much as Fiscal Space Allows:** all of G.

    Replacement is then capped by **fiscal space**, the extra money the health budget could find in a year:
    """)
    st.latex(r"R=\min(\text{wanted},\ \text{capacity}),\qquad \text{capacity} = \text{GHES}_{2023}\times\max\!\big(0,\ g_{\text{strong}}-\max(g_{\text{typical}},0)\big)\times s")
    md("""
    - **GHES₂₀₂₃**: government health spending in 2023 (IHME, constant 2023 US$).
    - **g_typical**: the median real annual growth of government health spending in that country, 2001-2023 (IHME).
    - **g_strong**: the 75th percentile of that growth (a strong year), or the 90th (the best years), chosen under
      Advanced.
    - **s, the debt-stress factor**: 1 when interest takes 10% of revenue or less, falling linearly to 0.25 at 40%
      or more. Interest as % of revenue is World Bank WDI `GC.XPN.INTP.RV.ZS`, latest year.
    """)
    st.latex(r"s=\operatorname{clip}\!\Big(1-\frac{\text{interest \% of revenue}-10}{40},\ 0.25,\ 1\Big)")
    md(f"""
    **Why no backfill is the historical norm.** A two-way fixed-effects regression across {REG['fiscal_replacement']['n_countries']}
    countries ({REG['fiscal_replacement']['years'][0]}-{REG['fiscal_replacement']['years'][1]},
    {REG['fiscal_replacement']['n_obs']:,} country-years) relates the yearly change in government health spending
    per person to falls (this year and last) and rises in aid per person, controlling for GDP growth. The implied
    replacement rate is θ = -(b_fall + b_fall,lag) = {TH_C:+.2f} per $1 (95% CI {TH_LO:+.2f} to {TH_HI:+.2f}):
    governments did not, on average, replace falling aid.

    **Where replacement money goes.** *Pro-rata*: in proportion to each service's loss. *Lives first*: service lines
    are refilled in order of deaths averted per dollar (usually TB treatment, vaccines and HIV treatment first).
    """)

    th.section_header("groups", "Step 3: Coverage (Who Loses a Service)")
    md("""
    Donor money pays for a number of people: its baseline aid divided by the cost per person, but never more than the
    people currently covered. People losing the service are that number times the share of donor money lost:
    """)
    st.latex(r"\text{donor-funded}_{\ell}=\min\!\Big(\text{people covered}_{\ell},\ \frac{\text{aid now}_{\ell}}{\text{cost per person}_{\ell}}\Big)")
    st.latex(r"\text{people losing service}_{\ell}=\text{donor-funded}_{\ell}\times\frac{\text{aid lost}_{\ell}}{\text{aid now}_{\ell}}\times(1-\text{continuity})")
    md("""
    When donor aid buys less than full coverage (most lines), this is simply aid lost ÷ cost per person. When donor aid
    is more than the full cost of everyone covered (for example HIV treatment in Honduras, where donor treatment aid is
    about twice what ART for all patients would cost), the excess is paying for things other than the service itself,
    so the loss is scaled by the share of money lost instead of running past the people covered. The Validation page
    counts the lines where this happens.
    """)
    md(f"""
    - **Continuity** = {pct('continuity')}: the share of people who keep their service anyway (absorbed by government
      facilities or cheaper delivery). *Assumption.*
    - The result is **capped** at the people currently covered (coverage x people in need), so a cut can never remove
      more people than are on a service. Bednets and spraying share one cap (the population at risk).
    - **Coverage drop** (percentage points) = people losing the service ÷ people in need x 100.

    **Cost per person** (what donors spend per person served):

    | Service | Formula | Central value / source |
    |---|---|---|
    | HIV treatment | site cost x multiplier ÷ (1 - above-service share) | Site cost per patient-year (Rosen et al. 2021, 2018-2020 US$, inflated to 2023 US$ with US CPI-U): Malawi ${UC[('art_site_cost', 'MWI')]:.2f}, Zambia ${UC[('art_site_cost', 'ZMB')]:.2f}, Lesotho ${UC[('art_site_cost', 'LSO')]:.2f}, Uganda ${UC[('art_site_cost', 'UGA')]:.2f}, Zimbabwe ${UC[('art_site_cost', 'ZWE')]:.2f}; elsewhere ${UC[('art_site_default', 'arv')]:.2f} (ARVs + labs) + ${UC[('art_site_default', 'non_arv')]:.2f} x (GDP per person ÷ $1,000)^{C['uc_scale_elast']:g} (staff). Above-service share {pct('asd_share')} (PEPFAR expenditure analysis) |
    | PMTCT | per HIV+ pregnant woman | ${C['uc_pmtct']:,.0f} (*assumption*), incremental to the mother's ART |
    | HIV prevention | $ per infection averted = ${C['cpia_ref']:,.0f} x (1 ÷ incidence per 1,000)^0.5 | *Assumption*; incidence clipped to 0.05-10 per 1,000 |
    | Orphans & vulnerable children | per child-year | ${C['uc_ovc']:,.0f} (*assumption*); no mortality effect |
    | TB treatment | income-group cost x multiplier ÷ (1 - above-service share) | Laurence, Griffiths & Vassall 2015: low income $332, lower-middle $351, upper-middle $1,081 (2014 US$ x 1.287) |
    | Drug-resistant TB | as above | $1,568 / $8,125 / $6,800 by income group (same study) |
    | Bednets | per person-year of net use | ${C['uc_itn']:.2f} (GiveWell: $4-6 per net, 1.8 people per net, ~2 years, ~63% used) |
    | Indoor spraying | per person-year protected | ${C['uc_irs']:.2f} (PMI Mali 2012-14, $6.08-7.40 in 2014 US$ x 1.287) |
    | Malaria testing & treatment | per confirmed case treated | ${C['uc_mal_cm']:.2f} (*assumption*: ACT + tests + delivery) |
    | Routine immunization | per child immunized | ${C['uc_imm']:.0f} (Gavi disbursements ÷ children reached, 2021 and 2024) |

    **People in need and current coverage:**

    | Service | People in need | Current coverage |
    |---|---|---|
    | HIV treatment | People living with HIV = HIV prevalence 15-49 x population 15-64 x calibration + children 0-14 with HIV (calibration = UNAIDS PLHIV ÷ that product in 2011, clipped 0.6-1.6) | ART coverage, WDI `SH.HIV.ARTC.ZS` |
    | PMTCT | HIV+ pregnancies = births x prevalence x 1.15 (women's prevalence ~15% above all adults) | PMTCT coverage, WDI `SH.HIV.PMTC.ZS` (ART coverage if missing) |
    | TB treatment | TB incidence, all forms (WHO via Gapminder) | TB treatment coverage, WDI `SH.TBS.DTEC.ZS` |
    | Drug-resistant TB | 4% of TB incidence | 45% (*assumption*) |
    | Bednets / spraying | Population at risk = population x 95% in sub-Saharan Africa, 35% elsewhere | Children sleeping under nets, WDI `SH.MLR.NETS.ZS`; {C['mal_itn_default_use']:.0%} if not surveyed |
    | Malaria testing & treatment | Malaria cases = incidence per 1,000 at risk (WDI `SH.MLR.INCD.P3`) x population at risk | Children with fever receiving antimalarials, WDI `SH.MLR.TRET.ZS`, used only where malaria incidence is at least {hm.MAL_CM_MIN_INCIDENCE} cases per 1,000 at risk; otherwise {C['mal_cm_default_cov']:.0%} (where malaria is rare, most fevers are not malaria, so the survey is near zero for that reason and does not measure coverage of malaria cases) |
    | Routine immunization | Births = crude birth rate x population (WDI) | DTP3 coverage, WDI `SH.IMM.IDPT` |

    Where nobody is counted as in need (for example malaria treatment in Iraq), coverage cannot be calculated and the
    dashboard shows "Not Modelled".
    """)

    th.section_header("favorite", "Step 4: Lives (Extra Deaths)")
    md("Deaths = people losing a service x deaths per person who loses it, year by year over five years.")
    md(f"""
    **HIV treatment.** Excess deaths per person-year off ART rise as immunity declines: 1.2%, 2.8%, 3.8%, 4.5% and
    5.0% in years 1-5, times an uncertain multiplier {rng_txt('art_hazard_mult')}. Calibrated so five-year deaths
    from losing PEPFAR-supported ART sit between the Optima and UNAIDS estimates. People off ART also transmit HIV:
    {rng_txt('art_transmission')} new infections per person-year (half in year 1).
    """)
    st.latex(r"\text{deaths}_{y}=\text{people off ART}\times h_y\times m,\qquad h=(0.012,\,0.028,\,0.038,\,0.045,\,0.050)")
    md(f"""
    **Mother-to-child transmission.** Deaths per mother losing PMTCT = transmission averted
    {rng_txt('pmtct_vt_reduction')} (WHO: 15-45% without, under 5% with) x death by age 2 if infected
    {rng_txt('pmtct_infant_mort')} (Newell et al. 2004).

    **TB.** Deaths per patient untreated = case fatality untreated - case fatality treated, weighted by the share of
    TB patients with HIV (h, WHO TB/HIV incidence ÷ TB incidence) and lowered for those on ART (a = ART coverage):
    """)
    st.latex(r"\Delta\text{CFR}=(1-h)\,(0.43-0.03)+h\,(0.62-0.06)\,(1-0.3a)")
    md(f"""
    with untreated / treated case fatality {rng_txt('tb_cfr_untreated_neg')} / {rng_txt('tb_cfr_treated_neg')}
    (HIV-negative) and {rng_txt('tb_cfr_untreated_pos')} / {rng_txt('tb_cfr_treated_pos')} (HIV-positive), from WHO's
    TB burden estimation methods. Drug-resistant TB: {rng_txt('tb_dr_dcfr')} deaths averted per patient treated
    (*assumption*).

    **Malaria** uses the Lives Saved Tool form. Coverage after the cut feeds a multiplicative death reduction:
    """)
    st.latex(r"D_1=D_0\times\frac{1-E_v C_{v,1}}{1-E_v C_{v,0}}\times\frac{1-E_c C_{c,1}}{1-E_c C_{c,0}}")
    md(f"""
    - D₀ = all-age malaria deaths = WHO/MCEE child (1-59 months) malaria deaths ÷ 0.76 in sub-Saharan Africa (WHO:
      under-5s are ~76% of malaria deaths there) or ÷ 0.40 elsewhere.
    - E_v = {rng_txt('mal_vc_eff')}, the reduction in deaths at full vector-control coverage (Eisele et al. 2010);
      E_c = {rng_txt('mal_cm_eff')} for case management (Thwing et al. 2011).
    - C₀ = current coverage; C₁ = C₀ - people losing the service ÷ people in need.
    - Because the formula is multiplicative, each extra point of coverage lost costs slightly more lives.

    **Routine immunization.** Future deaths averted per child immunized at under-5 mortality of 50 per 1,000 =
    {rng_txt('imm_deaths_per_child_ref')} (Gavi: 20.6M deaths averted ÷ 1.2B children; 1.7M ÷ 72M in 2024), times the
    share that would occur before age 5, {rng_txt('imm_u5_share')} (Li et al. 2021: hepatitis B and HPV deaths come in
    adulthood), scaled by the country's under-5 mortality:
    """)
    st.latex(r"\text{deaths per child}=0.020\times0.65\times\operatorname{clip}\!\Big(\frac{\text{U5MR}}{50},\,0.3,\,2.5\Big)")
    md("""
    **Timing.** Deaths build up over the five years. The share of the full yearly effect reached in years 1-5:

    | Service | Year 1 | Year 2 | Year 3 | Year 4 | Year 5 |
    |---|---|---|---|---|---|
    | PMTCT | 60% | 100% | 100% | 100% | 100% |
    | TB (both) | 70% | 100% | 100% | 100% | 100% |
    | Bednets (nets keep protecting ~1 year) | 50% | 100% | 100% | 100% | 100% |
    | Indoor spraying | 80% | 100% | 100% | 100% | 100% |
    | Malaria treatment | 100% | 100% | 100% | 100% | 100% |
    | Vaccines (unvaccinated cohorts add up) | 40% | 75% | 95% | 100% | 100% |

    **Already-falling death rates** (on by default). Baseline malaria deaths and under-5 mortality were falling
    before any cut, so in year y they are multiplied by (1 + trend)^(y-1). Each country's trend is its average annual
    change over 2010-2019 from a log-linear fit (at least 5 years of data), clipped to -8% to +2% a year; countries
    without data get the median; if still missing, -0.9% a year (Cavalcanti et al. 2025, Lancet, appendix 10.2). TB
    and HIV effects are per patient and unchanged.

    **HIV prevention** turns money into infections averted only (no deaths within five years). **Orphans and
    vulnerable children** support has no modelled effect on deaths.
    """)

    th.section_header("casino", "Uncertainty")
    md("""
    Every parameter in the *Parameters* tab is drawn from a triangular distribution (low, central, high), 400 times
    per country with a fixed random seed (7), so results are reproducible and every chart uses the same draws.
    Headline numbers are the **central** run (every parameter at its central value); ranges are the 2.5th and 97.5th
    percentiles of the 400 draws. All-country ranges add the country percentiles, which makes them wider than a jointly
    simulated interval. Parameters can be edited under Advanced to test sensitivity.
    """)

# =========================================================================== #
# DATA SOURCES
# =========================================================================== #
with tabs[3]:
    th.section_header("database", "Datasets", rule=False)
    md("""
    | Dataset | Provider and version | Variables used | Used in |
    |---|---|---|---|
    | Development Assistance for Health | IHME, 1990-2026 (Sept 2026 release) | Aid (`dah_23`) by source, channel, recipient, focus and program area; 2025 preliminary totals | Section 2; model baseline (2021-23) and IHME 2025 scenario |
    | Global Health Spending | IHME, 1995-2023 | Government, prepaid private, out-of-pocket and aid spending: totals, per person, % of GDP | Section 1; government health spending and its growth (fiscal space) |
    | Expected Health Spending | IHME, 2024-2050 | Same variables, projected | Section 1 (2024-2030) |
    | GDP | IHME Financing Global Health, 1960-2050 (2026) | GDP per person, constant 2023 US$ | Constant-dollar GDP; ART staff-cost scaling; regression controls |
    | World Economic Outlook | IMF | GDP, population, general-government revenue, expenditure, net lending and gross debt (% of GDP) | Header; Section 3 totals |
    | World Revenue Longitudinal Data | IMF | Revenue by type, % of GDP | Section 3 revenue mix |
    | Government Finance Statistics (COFOG) | IMF | Spending by function, % of outlays | Section 3 spending mix |
    | World Development Indicators | World Bank, via Gapminder's open-numbers mirror | See the table below | Model inputs |
    | Systema Globalis | Gapminder (WHO estimates) | People living with HIV; TB incidence and deaths (HIV-negative and HIV-positive); child (1-59 months) malaria, measles and pneumonia deaths (WHO/MCEE) | Model inputs |
    | HIV share of deaths | Gapminder fasttrack (IHME GBD) | HIV deaths as % of all deaths | Validation page (Lancet rate ratios) |
    | Country classifications | World Bank (Gapminder mirror) | Income group | Header; TB costs |
    | MOU / co-financing sheet | Capstone team | US reference funding 2021-25 and 2026-2030 schedules; MOU status | America First MOUs scenario; header |
    | Gavi financial data | Gavi, FY2021-25 | Disbursements | Cost per child immunized |
    """)
    th.section_header("table_chart", "World Development Indicators Used")
    md("""
    Each value is the most recent year available from 2010 (2005 for malaria survey indicators) to 2024.

    | Code | Meaning | Used for |
    |---|---|---|
    | `SH.DYN.AIDS.ZS` | HIV prevalence, ages 15-49 (%) | People living with HIV; HIV+ pregnancies |
    | `SH.HIV.ARTC.ZS` | ART coverage (% of people living with HIV) | HIV treatment coverage |
    | `SH.HIV.INCD.TL` | New HIV infections | HIV incidence (prevention cost) |
    | `SH.HIV.0014` | Children 0-14 living with HIV | People living with HIV |
    | `SH.HIV.PMTC.ZS` | PMTCT coverage (%) | PMTCT coverage |
    | `SH.TBS.DTEC.ZS` | TB treatment coverage (%) | TB coverage |
    | `SH.MLR.INCD.P3` | Malaria incidence per 1,000 at risk | Malaria cases |
    | `SH.MLR.NETS.ZS` | Children under 5 sleeping under nets (%) | Vector-control coverage |
    | `SH.MLR.TRET.ZS` | Children with fever receiving antimalarials (%) | Malaria treatment coverage |
    | `SH.IMM.IDPT` | DTP3 immunization (%) | Immunization coverage |
    | `SH.DYN.MORT` | Under-5 mortality per 1,000 | Vaccine effect scaling; trend |
    | `SH.DTH.MORT` | Under-5 deaths | Poisson regression (Validation) |
    | `SP.DYN.CBRT.IN` | Crude birth rate | Births |
    | `SP.POP.TOTL`, `SP.POP.1564.TO` | Population, total and 15-64 | People in need; per-person rates |
    | `GC.REV.XGRT.GD.ZS` | Revenue excluding grants (% of GDP) | Aid lost as % of revenue |
    | `GC.DOD.TOTL.GD.ZS` | Central government debt (% of GDP) | Fiscal panel |
    | `GC.XPN.INTP.RV.ZS` | Interest payments (% of revenue) | Debt-stress factor |
    | `SH.XPD.GHED.GE.ZS` | Government health spending (% of government spending) | Health share pill (Abuja target 15%) |
    | `SP.DYN.CDRT.IN`, `SH.MMR.DTHS` | Crude death rate; maternal deaths | Validation page |
    """)
    th.section_header("menu_book", "Published Studies Behind the Parameters")
    md("""
    - Rosen S et al. 2021, *Gates Open Research* 5:177 (cost of HIV treatment delivery, five countries).
    - Results for Development, PEPFAR expenditure analysis (above-service-delivery spending, 45%).
    - Laurence YV, Griffiths UK, Vassall A 2015, *PharmacoEconomics* (TB treatment costs by income group).
    - GiveWell insecticide-treated net cost-effectiveness analysis; PMI Africa IRS project costs (*Malaria Journal* 2018).
    - Gavi progress reports (deaths averted per child; disbursements per child).
    - Li X et al. 2021, *Lancet* (VIMC: lifetime vs under-5 vaccine deaths averted).
    - Newell ML et al. 2004, *Lancet* (mortality of HIV-infected infants).
    - WHO Global TB Report technical appendix, Glaziou et al. (TB case fatality, Tables 4-5).
    - Eisele TP, Larsen DA, Steketee RW 2010 and Thwing J et al. 2011 (Lives Saved Tool malaria effects).
    - UNAIDS 2025 funding-cuts brief; ten Brink D et al. 2025, *Lancet HIV* (Optima) (ART hazard calibration).
    - Cavalcanti DM et al. 2025, *Lancet* (USAID impact; mortality trend; Poisson method; rate ratios).
    """)

# =========================================================================== #
# ASSUMPTIONS AND LIMITATIONS
# =========================================================================== #
with tabs[4]:
    th.section_header("rule", "Values That Are Assumptions", rule=False)
    a = PRM[PRM["status"] == "assumption"].reset_index()
    md("These parameters have no single published source; they are reasoned assumptions with wide ranges:")
    st.table(a[["label", "central", "low", "high", "unit", "source"]].rename(columns=lambda c: title_case(c))
             .set_index("Label"))
    md("""
    Fixed structural assumptions (not in the parameter table):

    - Drug-resistant TB is 4% of TB incidence, with 45% treatment coverage.
    - Malaria population at risk is 95% of the population in sub-Saharan Africa and 35% elsewhere; under-5s are 76%
      of malaria deaths in sub-Saharan Africa and 40% elsewhere.
    - HIV prevalence among pregnant women is 15% above the all-adult rate.
    - A cut is sustained for all five years, and no other funder steps in except the government response chosen.
    - The 2021-2023 average is the "before" level for every country.
    """)
    th.section_header("report", "Limitations")
    md("""
    - **Average, not marginal, costs.** Cuts usually hit the most expensive or least essential services first, and
      some cut services are cheaper than average. The model uses average costs per person.
    - **Donor money and service cost do not always line up.** In many country-service lines donor aid is more than
      the modelled cost of serving everyone covered (see the Validation page); the excess is assumed to pay for
      things other than the service, which may understate or overstate what a cut does to those lines.
    - **No second-round effects.** Drug resistance, outbreaks (for example measles), health-worker layoffs and supply
      chain breakdowns are not modelled.
    - **No re-allocation by other donors** beyond the government response.
    - **Post-2023 aid is not observed by recipient.** IHME's 2024-2025 estimates have no country split, so the model's
      baseline is 2021-2023.
    - **Survey data can be old.** Malaria coverage comes from household surveys; where none exist, defaults are used
      and flagged.
    - **Program-area tags are partial** (most TB aid is untagged), so unspecified money is spread over the known mix.
    - **The regressions are associations, not causes.** Aid goes where deaths are high, which can hide or reverse a
      protective effect (see the Validation page).
    - **Treat results as scenario estimates, not forecasts.**
    """)

# =========================================================================== #
# PARAMETERS
# =========================================================================== #
with tabs[5]:
    th.section_header("tune", "Every Model Parameter", rule=False)
    md("Each is drawn from a triangular distribution (low, central, high). Status says whether the value comes from a "
       "published source or is an assumption. Edit them under Advanced on the Dashboard to test sensitivity.")
    params = PRM.reset_index()
    st.table(params.rename(columns={c: title_case(c.replace("_", " ")) for c in params.columns}).set_index("Param"))
    th.section_header("functions", "Regression Estimates")
    rows = []
    for k, v in REG.items():
        if k.startswith("_"):
            continue
        x = v["x"][0]
        rows.append({"Regression": k.replace("_", " ").title(), "Outcome": v["y"], "Main Regressor": x,
                     "Coefficient": f"{v['coef'][x]:+.3f}", "Standard Error": f"{v['se'][x]:.3f}",
                     "Countries": v["n_countries"], "Observations": f"{v['n_obs']:,}",
                     "Years": f"{v['years'][0]}-{v['years'][1]}"})
    st.table(pd.DataFrame(rows).set_index("Regression"))
    md("Coverage and fiscal regressions: two-way (country and year) fixed effects, standard errors clustered by "
       "country. Poisson regressions: country and year fixed effects, log population (or births) offset, controls for "
       "log GDP per person and log government health spending per person (method of Cavalcanti et al. 2025).")

# =========================================================================== #
# CROSS-CHECKS
# =========================================================================== #
with tabs[6]:
    th.section_header("fact_check", "Cross-Checks for the Current Selection", rule=False)
    st.caption(f"{country_name} · {title_case(preset)} · {ms._resp_label(fiscal_t)}"
               + ("" if trend else " · Death Rates Held Constant"))
    sk = scn.scenario_key(scn.build_scenario(preset, opts, I["ci"]))
    res = ms._run(iso3, sk, fiscal_t, ptab_json, trend) if (iso3 in I["ci"].index and iso3 in set(I["lines"].iso3)) \
        else None
    st.subheader("What 20 Years of Data Say")
    st.markdown(ms._esc(ms._crosscheck_summary(res, I, ptab, country_name)))
    ctl = {"preset": preset, "ptab": ptab, "ptab_json": ptab_json, "fiscal_t": fiscal_t, "trend": trend}
    A = ms._all_country_results(sk, ctl)
    ms._published_estimates(A[A["gross_loss_usd"] > 0], I, ptab)
