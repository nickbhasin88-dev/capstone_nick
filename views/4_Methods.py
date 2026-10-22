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
preset = st.session_state.get("sel_preset", scn.UI_PRESETS[0])
preset = preset if preset in scn.UI_PRESETS else scn.UI_PRESETS[0]
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


def _u5_share_table() -> pd.DataFrame:
    """Under-5 share of malaria deaths by WHO region (World Malaria Report 2025, model_params.csv) with the rule and the
    modelled countries that use it (country_inputs.csv: who_region, malaria_u5_share_rule)."""
    ci = I["ci"]
    ci = ci[ci.index.isin(set(I["lines"].iso3))]
    names = dropdown_countries()
    rows = []
    for reg, label in (("AFR", "African"), ("AMR", "Americas"), ("EMR", "Eastern Mediterranean"),
                       ("SEA", "South-East Asia"), ("WPR", "Western Pacific"), ("EUR", "European")):
        c = ci[ci["who_region"] == reg]
        if not len(c):
            continue
        par = f"mal_u5_share_{reg.lower()}"
        with_d = c[c["malaria_deaths"].fillna(0) > 0]
        rows.append({"WHO Region": label,
                     "Under-5 Share": (f"{PRM.loc[par, 'central']:.1%} ({PRM.loc[par, 'low']:.1%}-{PRM.loc[par, 'high']:.1%})"
                                       if par in PRM.index else "none"),
                     "Rule": c["malaria_u5_share_rule"].iloc[0].split(":")[0],
                     "Source": (PRM.loc[par, "source"].split(":")[0] if par in PRM.index
                                else "No WMR regional or global figure (no malaria deaths)"),
                     "Countries With Malaria Deaths": ", ".join(sorted(names.get(i, i) for i in with_d.index)) or "none"})
    return pd.DataFrame(rows).set_index("WHO Region")


def pct(p: str) -> str:
    return rng_txt(p, "{:.0%}")


st.title("Methods, Data and Limitations")
st.caption("A complete guide to how every number on the dashboard is calculated, where each input comes from, and "
           "which values are assumptions. Numbers quoted here are read from the model's own files.")

tabs = st.tabs(["Overview", "Dashboard Sections", "The Model, Step by Step", "Data Sources",
                "Assumptions & Limitations", "Parameters"])

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

    **Simulation (Section 4 and the All Countries page).** A three-step model that asks what happens if donors cut
    aid for HIV, TB, malaria and routine immunization:

    1. **Money**: how much aid each service loses (by donor, channel and program area).
    2. **Fiscal response**: how much of it the government replaces, limited by its fiscal space.
    3. **Coverage**: the money not replaced, divided by the cost of serving one person, is the number of people who
       lose a service, shown as a drop in coverage.

    Every uncertain number is drawn at random many times (Monte Carlo), which gives the ranges shown. The model
    covers {N_COUNTRIES} countries.
    """)
    th.section_header("payments", "Units and Currency")
    md(f"""
    **Every dollar figure is in constant 2023 US dollars (except MOU amounts)**, the unit IHME uses for its aid and
    health-spending data. MOU cut percentages compare each year's MOU amount with the 2021-2025 reference in the same
    nominal dollars; the rest of the dashboard uses constant 2023 US$. MOU amounts are nominal US$, as written in the
    MOU, and future years are not converted.
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
    | Health spending by source (Section 1) | 2015-2023, observed years only |
    | Government revenue and spending (Section 3) | latest year with IMF data (user can pick earlier years) |
    | Aid baseline the model cuts | average of 2021, 2022 and 2023 (smooths lumpy bednet campaigns and Gavi tranches) |
    | Model horizon | five years after the cut, 2026-2030 |
    | Fiscal-space growth rates | 2001-2023 |
    | Mortality trends | under-5 mortality 2010-2019 (before COVID-19); malaria: WHO estimated malaria deaths 2015-2024 |
    | Malaria coverage and cases | Malaria Atlas Project 2025 (treatment, bednets, spraying, cases) |
    """)
    th.section_header("event", "Data Years")
    md("""
    The model applies each input's latest year to 2026-2030 without projecting it forward. The years differ by
    input: aid is the 2021-2023 average (IHME's last recipient-level years), while coverage is from 2024-2025.
    """)
    st.table(ms.data_years_table(I["ci"], sorted(set(I["lines"].iso3))))

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
    | US MOU | "MOU Signed" if the country is in KFF's tracker of signed America First MOU bilateral global health agreements (36 countries, data as of 8 October 2026); otherwise "No MOU". Never inferred from whether schedule data exist | KFF Tracker: America First MOU Bilateral Global Health Agreements (as of 2026-10-08) |
    | GDP | Latest year the IMF reports as actual (not an estimate), in constant 2023 US$ (see *Units and Currency*) | IMF World Economic Outlook, IHME GDP |
    | Population | Same year as GDP | IMF World Economic Outlook |
    """)

    th.section_header("payments", "Section 1: Money Spent on Health")
    md("""
    **Data:** IHME Global Health Spending 1995-2023 (the chart shows 2015-2023).

    Total health spending is split into four sources that add up to the total:

    | Bar | IHME variable | Meaning |
    |---|---|---|
    | Government | `ghes_total` | Government health spending from domestic sources (taxes, social insurance) |
    | Prepaid Private | `ppp_total` | Private insurance and other prepaid schemes |
    | Out-of-Pocket | `oop_total` | Paid by households at the point of care |
    | Foreign Aid for Health (DAH) | `dah_total` | Development assistance for health: money from foreign governments, multilaterals and foundations |

    - **US$ Total** shows the totals; **US$ per Person** uses IHME's per-capita values; **Share of Total** divides each
      source by total health spending.
    - Foreign aid sits at the bottom of each bar so its share is easy to compare across years.
    - IHME's projections for 2024 onward are not shown: they assume aid keeps flowing, which the cuts modelled in
      Section 4 make unlikely.
    - **Foreign Aid Share of Total** = DAH ÷ total health spending in 2023.
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
    3. Each side's breakdown depends on the level of government the IMF file covers that year (the side's label
       says which):
       - **General government** (same level as the WEO): the breakdown is used and scaled to the WEO total, which only
         reconciles the small differences between the two IMF sources.
       - **Central government**: the breakdown is shown at its own size and is never stretched to the
         general-government total. One grey box, "Other Levels of Government (no breakdown)", holds the rest of the
         WEO total (states, provinces, local governments, social security funds).
       - If the central total is larger than the WEO total, the central breakdown is shown alone, with a short note.
       If the two sides come from different levels of government, a caption says so. The pills always show the WEO
       general-government revenue, spending and borrowing. `audit/checks.py` checks that each side's boxes add up to
       its WEO total, grey box included.
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
    | Treatment Lost Each Year; Prevention Lost Each Year (top of the Dashboard) | Treatment = HIV treatment, PMTCT, TB treatment and malaria treatment; prevention = bednet use, indoor spraying and childhood vaccination. Each counts the service the lost money would have paid for in a year (money lost ÷ cost per person). For HIV treatment this is patient-years of ART the lost money would have paid for, not a headcount of people who stop treatment |
    | Replaced by Government | The government's replacement, set by the response chosen, capped by fiscal space |
    | Net Aid Lost | Aid at risk minus what is replaced. It includes health-systems money (labs, staff, data systems, supply chain), which is above-site money already priced into the cost per patient, so it is not converted into lost services (`hss_service_share` = 0, a structural assumption held constant in the uncertainty runs; logic review L-05) |
    | People Losing a Service (per Year) | People-equivalents losing a service each year, all four diseases: money lost ÷ cost per person, capped at the people donors fund. HIV prevention (counted in infections averted) and orphan support are left out |
    | Biggest risks (top of the Dashboard, Announced donor cuts) | The donor x channel flow with the largest loss in 2030 and whether it is published or predicted; the year the loss jumps most and the flow behind the jump; the service whose coverage falls the most |
    | What Every US$1 Million Cut Does, by Disease | Each card runs the full model for a US$1M-a-year loss to one disease, spread across all its service lines (including HIV testing and care, unspecified and systems money) in proportion to current aid: no government replacement, sudden cut. People losing the service and the coverage drop are for the main service (HIV: ART; TB: TB treatment; malaria: bednets; immunization: routine vaccines). Where a disease's aid is under US$1M a year, all of it is cut and the results are scaled to US$1M |
    | What Each Service Loses | Per service line: baseline aid, aid lost after replacement, cost per person, people losing the service per year (average over 2026-2030), with the 5-year total of people affected underneath (the yearly numbers added up, following the funding path; for HIV treatment, mostly the same people stay off ART each year, so no total is added), and coverage before and after |
    | Can {{Country}} Fill the Gap? | The chart, from the same run as the headline, shows averages per year over 2026-2030 (and 2030 when it differs): the gap before the government steps in = aid lost (gross); filled by the government = the chosen response plus any gradual budget increase; gap left = the difference (= Net Aid Lost). The dashed line is backfill capacity (fiscal space), see *The Model, Step 2*. Aid Lost as % of Government Health Spending = average yearly gross loss ÷ government health spending in 2023; as % of revenue = that loss ÷ (GDP x revenue % of GDP, World Bank WDI). Health share of government spending: see *Gradual budget increase* |
    | All Countries | Totals add up country results; people losing a service per 100,000 = people-equivalents losing a service per year ÷ population x 100,000; budget exposure = gross loss ÷ government health spending |
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
    | HIV treatment (ART) | HIV | `hiv_treat` |
    | HIV testing & care | HIV | `hiv_care` (care and support), `hiv_ct` (counselling and testing); no patients of its own: a share κ of its lost money counts as lost ART care (below) |
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
    **Money with no reported purpose.** Aid tagged "unspecified" (IHME's `*_other` program areas: 16% of HIV aid,
    46% of TB aid and 27% of malaria aid in the model countries) is split by purpose using the country's Global Fund
    grant budgets by module (Grant Cycle 7, 2023-2025; `datasets/GlobalFund`; `audit/batch34_gf_shares.py`): the
    treatment share goes to the treatment lines (ART; TB treatment and DR-TB; malaria testing and treatment) in
    proportion to the country's mix, the prevention share to the prevention lines (HIV prevention and PMTCT;
    bednets and spraying), the testing share to testing and care (HIV: that line; TB and malaria: treated the same
    way, κ of it counting toward treatment), the systems share joins systems money and the programme-management
    share is lost without a modelled service effect. Only the treatment share becomes people on treatment. Median
    shares across the model countries: HIV treatment 35%, prevention 23%, testing 6%, systems 11%, management 22%;
    TB 49 / 1 / 21 / 10 / 17%; malaria 22 / 48 / 0 / 14 / 15%. Countries without a Global Fund grant for a disease
    (38 of 210 country-disease lines) use the median of the model countries in their WHO region. Before this change
    the money was spread over the known service lines by mix, which sent 45% (HIV), 77% (TB) and 40% (malaria) of it
    to treatment (logic review L-43).

    **Systems money** (labs, staff, monitoring, supply chain: IHME's `*_hss_*` program areas) is above-site money.
    The cost per patient for HIV and TB treatment is a site cost divided by (1 - above-service share), which already
    prices that money into every patient, so converting it into patients a second time counted it twice (logic
    review L-05). A share σ = {pct('hss_service_share')} of lost systems money is counted as lost services (a
    structural assumption held constant in the uncertainty runs; the earlier rule converted 50% and can be run as a
    sensitivity case through the parameter editor); the rest is lost without a modelled service effect.

    **HIV testing and care.** IHME's "HIV - Care and Support" and "HIV - Counseling and Testing" money is its own line,
    HIV Testing & Care, not ART. It pays for diagnosis and keeping people in care rather than for drugs, so it has no
    patients of its own; cutting it means fewer people diagnosed and retained, so fewer on ART. {ms.care_ct_note()}
    This is a proxy: the money funds a flow of diagnoses and retention, not a stock of patients, and a
    flow-of-initiations treatment is not implemented (no evidence on the cost per new initiation; logic review L-27,
    IMP-02, `audit/logic_review/batch34_evidence.md`). That part adds to the money lost on HIV treatment (so it adds people
    losing ART); the rest is lost without a modelled effect. Whether ART donor money buys more than everyone covered is
    judged on treatment money only. Across the dashboard countries this line is a median of 41% of the former HIV
    treatment money (13% in South Africa to 60% in Guyana).
    """)
    st.latex(r"\text{effective loss}_{\ell} = \text{direct loss}_{\ell} + \text{unspecified} \times s_{p(\ell)} \times \text{mix}_{\ell \mid p(\ell)} + \sigma \times \text{systems} \times \text{mix}_{\ell},\qquad \sigma = 0")
    md("where s_p is the share of unspecified money for the purpose p of line ℓ (treatment or prevention) and "
       "mix_{ℓ|p} is the line's share of the country's baseline aid among the lines of that purpose.")
    md("""
    **Donor scenarios (presets).**

    | Scenario | What is cut | Source of the numbers |
    |---|---|---|
    | US Bilateral Exit + Multilateral Withdrawals | US direct aid -100%; US contributions through WHO, Gavi and UNFPA -100%; US Global Fund pledge -23% (US$6.0B to US$4.6B), so 77% of the pledge is kept; other US multilateral money unchanged | US announcements (WHO exit effective Jan 2026; Gavi June 2025); Global Fund 8th replenishment, Nov 2025 |
    | America First MOUs | Only for countries with a signed MOU (KFF) **and** 2026-2030 US funding values in the team's sheet, plus Zambia's from its MOU table (17 countries). US direct aid follows the country's own schedule year by year: cut in year t = 1 - US funding in t ÷ 2021-25 reference, used exactly as written (never rescaled); a funding increase counts as a 0% cut; a schedule that eases later is followed as written (people return to care); where the schedule ends in 2028 (Botswana, South Sudan) the 2028 cut is held through 2030. US multilateral exits as above. Countries that signed without funding data list the scenario as unavailable; countries without an MOU don't offer it | KFF tracker (status); team's MOU / co-financing sheet (schedules) |
    | IHME 2025 Preliminary Estimates | Each source x channel x disease cell changes by IHME's 2025 preliminary total ÷ its 2021-23 average (global ratio applied to the country's mix; cells under US$20M a year use the source x disease ratio; clipped to 0-1.5) | IHME DAH database, 2025 preliminary estimates. Where a service line's aid rises, it counts as no loss (gains aren't modelled); the table notes the rise under that disease |
    | Total-Aid Cuts (OECD) Applied to Health Aid | Each donor's 2025 change in total aid (all sectors, not health-specific) applied to its health aid: US -57%, Germany -17.4%, France -10.9%, UK -10.8%, Japan -5.6% | OECD preliminary 2025 ODA data, April 2026 |
    | Global Fund & Gavi Shortfalls | Every donor's money through Gavi and through the Global Fund falls by a share the user sets (0-50%; default Gavi -15%, Global Fund -20%), against each fund's 2021-23 disbursements (the model baseline). No US multilateral exit is added, so nothing is counted twice. Gavi: Gavi 6.0 raised more than US$9B for 2026-2030 (including leftover COVID funds and earlier pledges) vs a US$11.9B target, about US$1.75B a year in 2023 US$; that is about 15% below Gavi's 2021-23 spending excluding COVID (US$2.06B a year in IHME's data; our estimate). The 24% gap to the target is a shortfall against plans, not a fall in spending. Global Fund: Eighth Replenishment US$12.64B vs US$15.7B in the Seventh (about -20%) and a US$18B target (-30%); KFF finds MOU-country allocations down 15% vs the original GC7 allocations, and Aidspan's median allocation-letter cut is about -24%. All nominal; real cuts are somewhat deeper. The All Countries page uses the defaults | Gavi press release (June 2025), Devex, Donor Tracker (2026); Global Fund Board (Feb 2026); KFF (June 2026); Aidspan; IHME DAH database |
    | Combined Retreat | US Bilateral Exit + Multilateral Withdrawals plus the OECD total-aid cuts for every other donor | As above |
    | Custom | Set by the user | |
    """)

    th.section_header("account_balance", "Step 2: Fiscal Response (What the Government Replaces)")
    md("""
    The gross loss G is the sum of all positive cell losses. The government wants to replace:

    - **No Government Replacement:** nothing.
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
      or more. Interest as % of revenue is the more recent of two sources (ties: World Bank): World Bank WDI
      interest payments (`GC.XPN.INTP.RV.ZS`), and IMF World Economic Outlook (October 2026) net interest = (primary
      balance - overall balance) ÷ revenue (`GGXONLB_NGDP`, `GGXCNL_NGDP`, `GGR_NGDP`), latest actual year. WEO's
      data API does not flag projections, so a year counts as actual only if it is before the country's first GDP
      estimate year. Net interest is interest paid minus interest received, so it can be a little below interest
      paid. Where neither source has a value, the median of the dashboard countries in the same income group is used
      and marked "estimated". The source and year are shown in the fiscal panel.
    """)
    st.latex(r"s=\operatorname{clip}\!\Big(1-\frac{\text{interest \% of revenue}-10}{40},\ 0.25,\ 1\Big)")
    md(f"""
    **Why No Government Replacement is the default.** A two-way fixed-effects regression across {REG['fiscal_replacement']['n_countries']}
    countries ({REG['fiscal_replacement']['years'][0]}-{REG['fiscal_replacement']['years'][1]},
    {REG['fiscal_replacement']['n_obs']:,} country-years) relates the yearly change in government health spending
    per person to falls (this year and last) and rises in aid per person, controlling for GDP growth. The implied
    replacement rate is θ = -(b_fall + b_fall,lag) = {TH_C:+.2f} per $1 (95% CI {TH_LO:+.2f} to {TH_HI:+.2f}):
    governments did not, on average, replace falling aid.

    **Where replacement money goes.** *Pro-rata*: in proportion to each service's loss. *Hypothetical best case
    (triage)*: service lines are refilled in order of the model's own priority ranking (usually TB treatment,
    vaccines and HIV treatment first). This is an optimisation rule showing the most a given budget could save, not a
    description of how governments are known to allocate money.
    """)

    th.section_header("groups", "Step 3: Coverage (Who Loses a Service)")
    md("""
    Donor money pays for a number of people: its baseline aid divided by the cost per person, but never more than the
    donor-funded pool, which is the people currently covered times the external (donor) share of the country's
    spending on that disease (`donor_share_*` in `country_inputs.csv`: WHO Global Health Expenditure Database
    external funding on HIV, malaria and immunization as a share of spending on each, latest year; WHO TB financing
    data for TB, funding received from the Global Fund, USAID and other grants ÷ all funding received, 2024; a
    WHO-region median where a country has no value: HIV 40 of 70 countries have their own value, TB 69, malaria 38,
    immunization 48). Bednets and spraying use the external share of *public* malaria spending (external ÷ (external
    + domestic government), GHED): campaign nets and spraying are financed by donors and governments, while the
    all-source malaria total is dominated by household spending on treatment (87% of malaria spending in Nigeria),
    which had left donor-funded nets a pool of 3% of the people covered there (Batch 4b). People losing the service
    are that number times the share of donor money lost:
    """)
    st.latex(r"\text{donor-funded}_{\ell}=\min\!\Big(\text{people covered}_{\ell}\times\text{external share}_{d(\ell)},\ \frac{\text{aid now}_{\ell}}{\text{cost per person}_{\ell}}\Big)")
    st.latex(r"\text{people losing service}_{\ell}=\text{donor-funded}_{\ell}\times\frac{\text{aid lost}_{\ell}}{\text{aid now}_{\ell}}\times(1-\text{continuity})")
    md("""
    When donor aid buys less than the donor-funded pool (most lines), this is simply aid lost ÷ cost per person. When
    donor aid is more than the full cost of that pool (for example HIV treatment in Honduras, where donor treatment
    aid is about twice what ART for all patients would cost), the excess is paying for things other than the service
    itself, so the loss is the pool times the share of money lost instead of running past the people donors fund.
    Before Batch 3+4 the pool was everyone covered, which treated every patient as donor-funded in 160 country-lines
    (logic review L-44). A spending share is not exactly the share of patients whose service donors pay for (donors
    often buy commodities for everyone while governments pay staff); it is the closest external measure and is
    labelled as such.
    """)
    md(f"""
    - **Continuity** = {pct('continuity')} (range {PRM.loc['continuity', 'low']:.0%}-{PRM.loc['continuity', 'high']:.0%}):
      the share of people who keep their service anyway (absorbed by government facilities, other donors or cheaper
      delivery). *Assumption.* The 2025 US cuts give only indirect evidence, all under partial withdrawals with
      commodities still flowing: people on PEPFAR-supported ART "remained relatively stable" at 20.3M in FY2025 Q4
      vs 20.4M a year earlier (KFF, April 2026); at four defunded key-population NGOs in Uganda and Zimbabwe
      treatment fell "by 22% to 32%" (Cust & Chabata 2026, *Lancet Global Health*); TB treatment was "the least
      affected" service in WHO's 17-country survey (Global TB Report 2025). None measures the share of patients who
      keep the same service after its funding is withdrawn, so the value stays an assumption; 0.30 is a sensitivity
      value (`audit/logic_review/batch34_evidence.md`, G).
    - The result is **capped** at the people currently covered (coverage x people in need), so a cut can never remove
      more people than are on a service. Bednets and spraying share one cap (the population at risk).
    - **Coverage drop** (percentage points) = people losing the service ÷ people in need x 100.

    **Cost per person** (what donors spend per person served):

    | Service | Formula | Central value / source |
    |---|---|---|
    | HIV treatment | the lower of (a) GHCC-based full cost and (b) observed treatment spending per person on ART; floored and gated; x multiplier | (a) site cost per patient-year by country (`art_site_cost`: GHCC Unit Cost Study Repository records pooled with Rosen et al. 2021; own value for 7 countries, the WHO-region or income-group median elsewhere) ÷ (1 - above-service share {pct('asd_share')}), which gives $400 in most countries and up to $675. (b) total HIV spending (ten Brink et al. 2025 appendix Table B2 for the 15 Optima countries; WHO GHED elsewhere) x the country's Global Fund treatment-and-care module share ÷ UNAIDS people receiving ART, same year, in 2023 US$ (43 countries; elsewhere (a) x the regional median of (b)/(a), 0.50 in Africa). The lower is used because the model needs what a dollar of lost treatment money pays for per patient, and (a) exceeded total HIV spending per person on ART in Kenya and Uganda (logic review L-50, Batch 4b). Floor $57 = TLD "under US$45 per person, per year" (Global Fund, 30 August 2023) + one viral load test at the "global access price from Roche of US$9.40 per test" (CHAI 2015; 2023 US$); gate $50-600. Median $274 (Kenya $308, Uganda $314, Mozambique $227, Malawi $199, Zimbabwe $129; South Africa and the Dominican Republic at the floor because the Global Fund share understates their treatment share). Uncertainty: {PRM.loc['uc_art_mult', 'low']:.2f} x the value up to the higher of (a) and (b) within the gate |
    | PMTCT | per woman per year, including her ART | ${C['uc_pmtct']:,.0f} (range ${PRM.loc['uc_pmtct', 'low']:.0f}-${PRM.loc['uc_pmtct', 'high']:.0f}) per HIV+ pregnant woman under Option B+: her ART, testing, infant prophylaxis and infant diagnosis. *Health Policy and Planning* 2016;31(8):1133 review of Option B+ cost-effectiveness analyses (annual cost per woman: Gopalappa $114, Ishikawa $170, Ciaranello $179, Fasawe $194, Kuznik $470), median about $250 in 2023 US$ (CPI-U); ARV prices have since fallen, so this is conservative |
    | HIV prevention | $ per infection averted = ${C['cpia_ref']:,.0f} x (1 ÷ incidence per 1,000)^0.5 | *Assumption*; incidence clipped to 0.05-10 per 1,000 |
    | Orphans & vulnerable children | per child-year | ${C['uc_ovc']:,.0f} (*assumption*); no mortality effect |
    | TB treatment | country cost per course x multiplier ÷ (1 - above-service share) | Provider cost per drug-susceptible course (`tb_ds_cost` in `country_inputs.csv`, 2023 US$): Value TB facility costing (Sweeney et al., 2018 US$; intensive + continuation phase, financial bottom-up): Ethiopia $218, India $105, Kenya $150, Philippines $120; South Africa $274 (Vassall et al. 2017, GHCC). Other countries: the median of those in their income group pooled with Laurence, Griffiths & Vassall 2015 ($275 low income, $135 lower-middle, $678 upper-middle). Range: {PRM.loc['uc_tb_mult', 'low']:.2f}-{PRM.loc['uc_tb_mult', 'high']:.2f} x |
    | Drug-resistant TB | as above | Per MDR-TB course (`tb_dr_cost`): Value TB short regimen Kenya $2,818, Philippines $1,580; South Africa $9,256 (Vassall 2017; Cox 2015); others $1,568 / $2,818 / $8,028 by income group (same pooling). DR-TB need = WHO's RR-TB share of incidence (`tb_rr_share`, median 2.1%, up to 34%) and coverage = RR patients started on treatment ÷ RR incidence (`tb_rr_cov`, median 35%), replacing the global 4% and 45% |
    | Bednets | per person-year of net use | ${C['uc_itn']:.2f} (GiveWell: $4-6 per net, 1.8 people per net, ~2 years, ~63% used) |
    | Indoor spraying | per person-year protected | ${C['uc_irs']:.2f} (PMI Mali 2012-14, $6.08-7.40 in 2014 US$ x 1.287) |
    | Malaria testing & treatment | per case treated (diagnosis + treatment) | ${C['uc_mal_cm']:.0f} (range ${PRM.loc['uc_mal_cm', 'low']:.0f}-${PRM.loc['uc_mal_cm', 'high']:.0f}): White et al. 2011, *Malaria Journal* 10:337, median financial cost per uncomplicated case treated $5.84 + diagnosis $4.32 (2009 US$) x 1.42 (US CPI-U to 2023). ACT and RDT prices have fallen since, so current costs may be lower |
    | Routine immunization | full cost per child immunized (vaccines + delivery) | ${C['uc_imm']:.0f}: delivery $45.6 per infant (Lydon et al. 2014, 2016-20) + vaccines $41.3 (MSF The Right Shot 2015, low end), both in 2023 US$; range $38 (Brenzel 2015, Gavi-country plans) to $104 (MSF high end). Check: donor vaccine aid per immunized child has a median of $40, below the full cost, as expected when governments co-finance |

    **People in need and current coverage.** HIV and malaria figures are the current WHO / UNAIDS estimates from
    the WHO Global Health Observatory (people living with HIV, ART and PMTCT coverage: UNAIDS 2025 round; malaria
    deaths and population at risk: World Malaria Report, 2024). Malaria coverage (treatment, bednets, spraying) and
    cases are Malaria Atlas Project 2025 values (data.malariaatlas.org, downloaded 13 October 2026; built by
    `malaria_inputs.py`). Where WHO publishes no estimate for a country
    the older derived value is kept and flagged in `country_inputs.csv` (column `<input>_source`); this applies to
    people living with HIV in Côte d'Ivoire, Guatemala, Iraq, Jordan and Nicaragua. The download and patch are done by
    `who_inputs.py`.

    | Service | People in need | Current coverage |
    |---|---|---|
    | HIV treatment | People living with HIV, all ages, 2025 (UNAIDS/WHO, GHO `HIV_0000000001`) | ART coverage, 2025 (UNAIDS/WHO, GHO `HIV_ARTCOVERAGE`) |
    | PMTCT | Pregnant women living with HIV, 2025 = women receiving ARVs (GHO `HIV_0000000016`) ÷ PMTCT coverage (GHO `HIV_0000000020`, which the GHO catalogue names "number of pregnant women living with HIV" but which holds coverage in %); where coverage is top-coded at 100%, the larger of that and births x prevalence x 1.15 | PMTCT coverage, 2025 (UNAIDS/WHO) |
    | TB treatment | TB incidence, all forms, 2024 (WHO Global TB Report, via Gapminder) | TB treatment coverage, 2024, WDI `SH.TBS.DTEC.ZS` (WHO) |
    | Drug-resistant TB | WHO's RR-TB share of incidence, 2024 (`tb_rr_share`; median 2.1%; 4% where WHO has none) | RR-TB patients started on treatment ÷ RR-TB incidence, 2024 (`tb_rr_cov`; median 35%; 45% where WHO has none) |
    | Bednets | Population at risk, 2024 = WHO estimated cases ÷ incidence per 1,000 at risk (GHO `MALARIA_EST_CASES`, `MALARIA_EST_INCIDENCE`) | ITN use (share of people sleeping under a net), 2025, Malaria Atlas Project (31 African countries); elsewhere a household survey of children under 5 sleeping under a net (WDI `SH.MLR.NETS.ZS`) only if from 2015 or later; otherwise {C['mal_itn_default_use']:.0%} (*assumption*) |
    | Indoor spraying | Population at risk (as above) | Household IRS coverage, 2025, Malaria Atlas Project (modelled for Africa only; 0 in every year elsewhere, read as no estimate). Coverage used = the larger of MAP's estimate and the people donor IRS money pays for ÷ population at risk (the second alone where MAP has no estimate), so a cut removes the spraying it bought even where MAP shows little or none. MAP counts households sprayed; the model applies that share to people at risk, at a cost per person protected |
    | Malaria testing & treatment | Malaria cases needing treatment, 2025 = Malaria Atlas Project *P. falciparum* + *P. vivax* clinical cases (61 countries); elsewhere the WHO estimate (GHO `MALARIA_EST_CASES`) | Effective treatment per 100 malaria cases, 2025, Malaria Atlas Project: the share of cases that receive an effective antimalarial. Where MAP has no value: the latest fever-treatment survey (WDI `SH.MLR.TRET.ZS`) where malaria incidence is at least {hm.MAL_CM_MIN_INCIDENCE} per 1,000 at risk, else {C['mal_cm_default_cov']:.0%} (*assumption*); none of the dashboard's malaria countries needs this |
    | Routine immunization | Births = crude birth rate x population (WDI) | DTP3 coverage, WDI `SH.IMM.IDPT` |

    Where nobody is counted as in need (for example malaria treatment in Iraq), coverage cannot be calculated and the
    dashboard shows "Not Modelled".
    """)

    th.section_header("timeline", "Funding Paths Over 2026-2030")
    md("""
    By default a scenario's cut starts in full in 2026 and lasts five years (a **sudden cut**). Under **How Funding
    Changes** the cut can instead be phased in, and under **Government Response** the government can add money
    gradually. Each year t = 1..5 (2026-2030) then has its own values:

    - **Share of the scenario's cut in force**, c(t) between 0 and 1. Aid lost in year t = full scenario loss x c(t).
    - **Extra government health money**, A(t), in US$.
    """)
    st.latex(r"\text{net gap}(t)=\max\big(0,\ \text{aid lost}\times c(t)-\text{government response}(t)-A(t)\big)")
    md(f"""
    The net gap is allocated to services exactly as for a sudden cut, and the people losing each service in year t
    follow from that year's gap (same costs per person and the same cap on what donor money pays for).

    **Shapes** of c(t) over N = 5 years:

    | Shape | c(t), t = 1..5 | 2026-2030 |
    |---|---|---|
    | Sudden (default) | 1 | {", ".join(f"{v:.0%}" for v in scn.path_shape("Sudden (default)"))} |
    | Linear phase-out | t / 5 | {", ".join(f"{v:.0%}" for v in scn.path_shape("Linear phase-out"))} |
    | Front-loaded | 1 - (1 - t/5)² | {", ".join(f"{v:.0%}" for v in scn.path_shape("Front-loaded"))} |
    | Back-loaded | (t/5)² | {", ".join(f"{v:.0%}" for v in scn.path_shape("Back-loaded"))} |
    | S-curve | logistic with midpoint year 3 (slope {scn.S_CURVE_STEEPNESS}), rescaled so year 5 = 1 | {", ".join(f"{v:.0%}" for v in scn.path_shape("S-curve"))} |
    | Custom | set year by year with the sliders | |

    **Gradual budget increase.** The government raises health's share of its total spending by a number of
    percentage points each year (cumulative): Steady p·t; Fast start 5p·(1 - (1 - t/5)²); Slow start 5p·(t/5)², never
    past the Abuja target of 15%. Extra money A(t) = points(t) ÷ 100 x total government spending, where total
    government spending = government health spending (IHME, 2023) ÷ health's share of government spending.

    **Health's share of government spending** has one definition everywhere on the dashboard (the fiscal panel, the
    budget-increase sliders, the break-even rise and every points-to-dollars conversion): (1) the World Bank's
    `SH.XPD.GHED.GE.ZS` (WHO Global Health Expenditure Database), latest available year, shown as "Health Share of
    Government Spending, {{year}}"; (2) where the World Bank has no figure, IHME government health spending ÷ IMF World
    Economic Outlook general-government expenditure for the same year, shown with "(estimated)"; (3) "n/a" if
    neither exists. No other government response applies with the budget-increase option.

    **Break-even budget increase.** The smallest constant yearly rise s in health's share of government spending
    (cumulative: s points in 2026, 2s in 2027, ...) that keeps the net gap at or below zero in every year of the chosen
    funding path, on top of the chosen government response. Found by bisection between 0 and the rise that reaches
    15% in 2030; "not reachable by 15%" if even that falls short in some year.

    **Assumptions.** New government money is spent as efficiently as donor money. The benchmark under the sliders is the country's fastest sustained rise in health's share of
    government spending: the 90th percentile of its 2001-2023 yearly changes (WDI).
    """)

    th.section_header("casino", "Uncertainty")
    md("""
    Every parameter in the *Parameters* tab is drawn from a triangular distribution (low, central, high), 400 times
    per country with a fixed random seed (7), so results are reproducible and every chart uses the same draws.
    Headline numbers are the **central** run (every parameter at its central value); ranges are the 2.5th and 97.5th
    percentiles of the 400 draws, called the **range across parameter values**. All-country ranges are the 2.5th and
    97.5th percentiles of the all-country total in each draw (the draws are the same in every country).
    These ranges reflect uncertainty in model parameters only. Uncertainty in the data (aid amounts, people in need,
    coverage) and in the model's structure (for example, whether lost money means people stopping
    treatment entirely) is larger and not included, so the ranges are not confidence intervals. Parameters can be
    edited under Advanced to test sensitivity.
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
    | Expected Health Spending | IHME, 2024-2050 | Same variables, projected | Not used: loaded into the model's input file, but no calculation or chart uses it |
    | GDP | IHME Financing Global Health, 1960-2050 (2026) | GDP per person, constant 2023 US$ | Constant-dollar GDP; ART staff-cost scaling; regression controls |
    | World Economic Outlook | IMF | GDP, population, general-government revenue, expenditure, net lending and gross debt (% of GDP) | Header; Section 3 totals; total government spending for the gradual budget increase |
    | World Revenue Longitudinal Data | IMF | Revenue by type, % of GDP | Section 3 revenue mix |
    | Government Finance Statistics (COFOG) | IMF | Spending by function, % of outlays | Section 3 spending mix |
    | World Development Indicators | World Bank, via Gapminder's open-numbers mirror | See the table below | Model inputs |
    | Global Health Observatory | WHO (UNAIDS 2025 round for HIV; World Malaria Report for 2024 malaria) | People living with HIV; ART and PMTCT coverage; women receiving ARVs for PMTCT; malaria deaths, cases and incidence per 1,000 at risk; modelled ITN use | Model inputs (people in need, coverage, malaria deaths and trend) |
    | Systema Globalis | Gapminder (WHO estimates) | TB incidence and deaths (HIV-negative and HIV-positive); child (1-59 months) malaria, measles and pneumonia deaths (WHO/MCEE) | TB inputs; Validation page regressions |
    | Country classifications | World Bank (Gapminder mirror) | Income group | Header; TB costs |
    | MOU / co-financing sheet | Capstone team | US reference funding 2021-25 and 2026-2030 schedules (nominal US$, as written in the MOU) | America First MOUs scenario |
    | KFF Tracker: America First MOU Bilateral Global Health Agreements | KFF, data as of 8 October 2026 | Countries with a signed MOU (36), agreement date, US funding | Header MOU status; which countries can run America First MOUs |
    | Gavi financial data | Gavi, FY2021-25 | Disbursements | Cost per child immunized |
    | World Economic Outlook, October 2026 (fiscal balances) | IMF, api.imf.org SDMX (dataflow IMF.RES:WEO), downloaded 13 October 2026 | Primary net lending/borrowing, net lending/borrowing and revenue, % of GDP (`GGXONLB_NGDP`, `GGXCNL_NGDP`, `GGR_NGDP`) | Net interest % of revenue for the debt-stress factor, where more recent than the World Bank figure |
    | Malaria Atlas Project national unit data | MAP (data.malariaatlas.org), downloaded 13 October 2026 | Effective treatment per 100 cases; ITN use; household IRS coverage; *P. falciparum* and *P. vivax* clinical cases (2000-2025) | Malaria coverage and cases (2025); malaria death trend (*P. falciparum* cases 2015-2025) |
    | World Malaria Report 2025 | WHO | 610,000 malaria deaths in 2024; case incidence trend 2015-2024 | Validation page; malaria trend rationale |

    Section 1 uses IHME's health spending database and Section 2 its DAH database; aid totals agree within 2% for 624 of
    630 country-years, with small differences in a few small countries.
    """)
    th.section_header("table_chart", "World Development Indicators Used")
    md("""
    Each value is the most recent year available from 2010 (2005 for malaria survey indicators) to 2024.

    | Code | Meaning | Used for |
    |---|---|---|
    | `SH.DYN.AIDS.ZS` | HIV prevalence, ages 15-49 (%) | Fallbacks for people living with HIV and HIV+ pregnancies where UNAIDS publishes no estimate; regressions |
    | `SH.HIV.ARTC.ZS` | ART coverage (% of people living with HIV) | Fallback where the GHO has no 2025 value |
    | `SH.HIV.INCD.TL` | New HIV infections | HIV incidence (prevention cost) |
    | `SH.HIV.0014` | Children 0-14 living with HIV | Fallback for people living with HIV |
    | `SH.HIV.PMTC.ZS` | PMTCT coverage (%) | Fallback for PMTCT coverage |
    | `SH.TBS.DTEC.ZS` | TB treatment coverage (%) | TB coverage |
    | `SH.MLR.INCD.P3` | Malaria incidence per 1,000 at risk | Whether fever-treatment surveys measure malaria treatment; fallback for malaria cases |
    | `SH.MLR.NETS.ZS` | Children under 5 sleeping under nets (%) | Bednet use where MAP has no estimate, only if surveyed in 2015 or later |
    | `SH.MLR.TRET.ZS` | Children with fever receiving antimalarials (%) | Malaria treatment coverage only where MAP has no estimate |
    | `SH.IMM.IDPT` | DTP3 immunization (%) | Immunization coverage |
    | `SH.DYN.MORT` | Under-5 mortality per 1,000 | Vaccine effect scaling; trend |
    | `SP.DYN.CBRT.IN` | Crude birth rate | Births |
    | `SP.POP.TOTL`, `SP.POP.1564.TO` | Population, total and 15-64 | People in need; per-person rates |
    | `GC.REV.XGRT.GD.ZS` | Revenue excluding grants (% of GDP) | Aid lost as % of revenue |
    | `GC.DOD.TOTL.GD.ZS` | Central government debt (% of GDP) | Fiscal panel |
    | `GC.XPN.INTP.RV.ZS` | Interest payments (% of revenue) | Debt-stress factor (or IMF WEO net interest, whichever is more recent) |
    | `SH.XPD.GHED.GE.ZS` | Government health spending (% of government spending) | Health's share of government spending (first choice, latest year); fastest historical rise in that share (benchmark under the sliders) |
    """)
    th.section_header("menu_book", "Published Studies Behind the Parameters")
    md("""
    - Rosen S et al. 2021, *Gates Open Research* 5:177 (cost of HIV treatment delivery, five countries).
    - KFF 2025, *Which PEPFAR Investments Drive HIV Outcomes?* (Gaba, Razavi, Kates & Nandakumar): non-service
      delivery was 47% of PEPFAR spending in 22 countries, 2018-2023 (basis of the above-service share, 0.45).
    - Laurence YV, Griffiths UK, Vassall A 2015, *PharmacoEconomics* (TB treatment costs by income group).
    - GiveWell insecticide-treated net cost-effectiveness analysis; PMI Africa IRS project costs (*Malaria Journal* 2018).
    - Gavi progress reports (future deaths averted per child immunized).
    - Lydon P, Gandhi G, Vandelaer J, Okwo-Bele JM 2014, *Bulletin of the WHO* 92:382-384 (health-system cost of
      delivering routine vaccination per infant, 2011-2020).
    - Brenzel L 2015, *Vaccine* (costs and financing of routine immunization from Gavi countries' multi-year plans).
    - Médecins Sans Frontières 2015, *The Right Shot*, 2nd edition (price to fully vaccinate a child).
    - Li X et al. 2021, *Lancet* (VIMC: lifetime vs under-5 vaccine deaths averted).
    - Newell ML et al. 2004, *Lancet* (mortality of HIV-infected infants).
    - WHO Global TB Report technical appendix, Glaziou et al. (TB case fatality, Tables 4-5).
    - Styblo K 1991, *Epidemiology of tuberculosis* (infections caused per untreated smear-positive case).
    - Vynnycky E, Fine PEM 1997, *Epidemiology and Infection* (risk of disease after TB infection).
    - Cohen JM et al. 2012, *Malaria Journal* 11:122 (malaria resurgence after control programs weaken).
    - Todd J et al. 2007, *AIDS* 21 suppl 6 (survival after HIV infection without treatment in Africa).
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

    - Drug-resistant TB uses WHO's country RR-TB share of incidence and enrolment (2024); the RR share of notified
      patients weights the drug-susceptible and drug-resistant course costs in the WHO budget cross-check only.
    - Malaria population at risk is 95% of the population in sub-Saharan Africa and 35% elsewhere where WHO publishes
      no estimate; under-5s are 76% of malaria deaths in sub-Saharan Africa and 40% elsewhere.
    - HIV prevalence among pregnant women is 15% above the all-adult rate.
    - A cut is sustained for all five years, and no other funder steps in except the government response chosen.
    - The 2021-2023 average is the "before" level for every country.
    """)
    th.section_header("report", "Limitations")
    md("""
    - **Average, not marginal, costs.** Cuts usually hit the most expensive or least essential services first, and
      some cut services are cheaper than average. The model uses average costs per person.
    - **Donor money and service cost do not always line up.** In many country-service lines donor aid is more than
      the modelled cost of serving everyone covered; the excess is assumed to pay for
      things other than the service, which may understate or overstate what a cut does to those lines.
    - **No second-round effects.** Drug resistance, outbreaks (for example measles), health-worker layoffs and supply
      chain breakdowns are not modelled.
    - **No re-allocation by other donors** beyond the government response.
    - **Post-2023 aid is not observed by recipient.** IHME's 2024-2025 estimates have no country split, so the model's
      baseline is 2021-2023. A 2025 baseline (IHME's preliminary 2025 aid levels) would reflect aid already lost
      after 2023; this is planned as a future option. The IHME 2025 scenario shows the effect of those losses.
    - **Inputs come from different years** and are applied to 2026-2030 without projection (see *Data Years*): aid is
      the 2021-2023 average, coverage is 2024-2025, government health spending is 2023.
    - **Malaria coverage is modelled.** Treatment, bednet and spraying coverage are Malaria Atlas Project 2025
      estimates (MAP's 2025 values repeat 2024 for treatment and bednets). Outside MAP's bednet countries, surveys
      from 2015 on or a default are used and flagged with the source and year next to each value.
    - **Program-area tags are partial** (most TB aid is untagged), so unspecified money is split by purpose with the
      country's Global Fund grant mix, an assumption that unclassified donor money looks like the Global Fund's.
    - **The regressions are associations, not causes.** Aid goes where deaths are high, which can hide or reverse a
      protective effect.
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
