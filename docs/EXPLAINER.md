# The Funding-Cut Model, Explained In Plain Language

This guide explains, step by step, how the dashboard turns a cut in health aid into estimates of people losing
services, extra deaths and new HIV infections. It is written for readers with a global health background and no
modelling experience. Every number comes from the current model (branch `tomato`, commit `4dcd7ae` or later) and its
data files; nothing is recalled from memory. The precise specification that the code follows is `docs/SPEC.md`; the
record of every change is `audit/logic_review/MODEL_CHANGELOG.md`; the evidence behind each value is in
`model_params.csv` and the `audit/logic_review/*_evidence.md` files.

A note on terms: the first time a technical term appears it is defined in brackets. All terms are also in the Glossary
(Section 8). Dashboard labels are written exactly as they appear on the dashboard, in Title Case.

> **Code And Specification Agreement.** An independent reproduction built from `docs/SPEC.md` alone (no model code
> read) matched the dashboard's own numbers in 1,980 of 1,980 cells to within 0.5%, with a largest difference of
> 0.0000% (five countries, four cases; `audit/logic_review/reproduction/`). No disagreement between the code and the
> specification was found while writing this guide. Where the specification was silent (six places, such as what
> happens when an input is missing) it was clarified to say what the code does.

---

## 1. One-Page Overview

**The question.** If donor funding for HIV, tuberculosis (TB), malaria and routine childhood immunization is cut in a
low- or middle-income country, how many people lose a service, how many extra deaths follow over 2026 to 2030, how many
extra HIV infections, and how much could the government offset?

**The chain, one sentence per step.**

1. **Aid Money.** Start from each country's donor health aid in 2021 to 2023 (the Institute for Health Metrics and
   Evaluation, IHME, Development Assistance for Health database), averaged and expressed in constant 2023 US dollars,
   broken down by who paid, which channel delivered it, and which service it funded.
2. **Scenario Cut.** A Donor Scenario (for example US Bilateral Exit + Multilateral Withdrawals) removes a share of
   each donor-channel-service cell; a cut path says how fast the cut arrives.
3. **Government Response.** The government may replace none, a set share, or as much as its fiscal space allows of
   the lost money, limited by how much its health budget could realistically grow.
4. **Services Lost.** The net money lost on each service is divided by the cost per person served to give the number
   of people who lose that service, never more than the people whose service donor money actually pays for.
5. **Coverage Change.** People losing a service divided by the people who need it gives the fall in coverage, in
   percentage points.
6. **Deaths And Infections.** Each person losing a service carries a published risk of death (or, for HIV, of
   infecting others): the excess death risk after stopping antiretroviral therapy (ART), TB case fatality without
   treatment, the Lives Saved Tool equations for malaria, and the Vaccine Impact Modelling Consortium (VIMC)
   deaths-averted-per-child estimates for vaccines.
7. **Uncertainty.** Every uncertain parameter is drawn 400 times from its range; the dashboard shows the central
   estimate and the 2.5th to 97.5th percentile of the draws.

**Headline result.** Under US Bilateral Exit + Multilateral Withdrawals (internal name `Full US exit`), with No
Government Replacement, a Sudden (default) cut and Account for Already-Changing Death Rates on, the 70 dashboard
countries lose US$3.96 billion of aid a year (38% of US$10.34 billion) and the model estimates:

| Output (dashboard label) | Central | Range Across Parameter Values |
|---|---|---|
| Extra Deaths Over 5 Years (2026 to 2030) | 1,927,405 | 1,462,315 to 2,597,871 |
| of which HIV | 998,535 | 693,955 to 1,646,133 |
| of which TB | 463,973 | 288,314 to 611,489 |
| of which Malaria | 276,952 | 141,485 to 314,157 |
| of which Immunization | 187,945 | 137,884 to 347,943 |
| New HIV Infections, 5 Years | 3,966,261 | 2,495,176 to 5,789,244 (sum of country percentiles, see Section 2h) |
| People who stop ART, per year (full-cost equivalents) | 4,861,100 | 3,400,339 to 6,494,427 (sum of country percentiles) |
| Further Deaths, 2031-2035 (Assumption-Driven) | 990,588 | 560,282 to 1,761,411 |

The per-disease ranges are computed the same way as the total's range (percentiles of the all-country total in each
of the 400 draws); the dashboard itself displays the range only for the all-disease total.

**What is included.** Four disease areas (HIV, TB, malaria, routine immunization); 70 countries that receive 71.5% of
the country-coded aid for these four areas; deaths from 2026 to 2030, with deaths set in motion by those cuts and
falling in 2031 to 2035 shown separately; new HIV infections to 2030 (with onward transmission for one further
generation); five government response options; parameter uncertainty.

**What is not included.** Other health areas (maternal and child health beyond vaccines, nutrition, health systems
as such); deaths from vaccines against diphtheria, tetanus, pertussis, polio and TB (BCG) and from HPV vaccination
(no usable evidence per child, so vaccine deaths are a floor); the effect of aid gains (a service whose aid rises
counts as no loss); uncertainty in the data and in the model's structure (the displayed ranges are parameter-only);
cuts that were already in force in 2025 (the baseline is 2021 to 2023); countries outside the 70 (for example
Myanmar, Sudan, Afghanistan, Chad, Yemen and Ukraine).

---

## 2. Step-By-Step

### 2a. Aid Baseline

**In plain words.** The model starts from what donors actually spent on each country's HIV, TB, malaria and
immunization programmes, who spent it, how it was delivered and what it bought.

**Data.** IHME's Development Assistance for Health (DAH) database, 1990 to 2026 edition (file
`IHME_DAH_DATABASE_1990_2026_Y2026M09D18.CSV`). DAH is IHME's estimate of all financial and in-kind resources
transferred from donors to low- and middle-income countries for health. Each row is a year, a source (the donor
country or organisation that paid), a channel (the agency that delivered the money) and a recipient country, with the
money split across "programme areas" (what it funded, such as HIV treatment or malaria bednets). Amounts are in
thousands of constant 2023 US dollars; the model multiplies by 1,000.

**Years averaged.** 2021, 2022 and 2023, the three latest years with recipient-country detail (IHME has no
country split after 2023). The baseline is the simple average of the three years. In symbols: baseline(c) = (1/3)
x sum over y = 2021..2023 of DAH(c, y) x 1,000.

**The double-counting rule (`elim_ch`).** IHME records some transfers twice: once when a bilateral agency gives money
to a multilateral, and again when the multilateral spends it. IHME flags one copy with `elim_ch = 1`; the model drops
those rows before adding anything up, as IHME's own user guide instructs (pages 3 to 4). This matters: without the
filter, money would be counted twice (audit item I-01).

**Sources (donor groups).** United States; United Kingdom; Germany; France; Japan; Canada; Netherlands; Nordics
(Sweden, Norway, Denmark, Finland); Gates Foundation; Other Private (private other, corporate donations);
Development-Bank Lending (IHME's debt repayments); Non-DAC Governments (China and others); Other / Unallocable; Other
DAC Governments (all remaining donor governments).

**Channels.** Bilateral Agency (every IHME `BIL_*` code), NGOs (NGO, international NGO, US foundations), Gates Direct,
Global Fund, Gavi, WHO (including PAHO), UNICEF, UNFPA, UNAIDS, Unitaid, Development Banks, EU Institutions, CEPI,
Other. Bilateral Agency, NGOs, Gates Direct and Other are "direct" channels; the rest are "multilateral". The
distinction matters for scenarios: a donor's bilateral cut hits its direct channels, while its contributions through
a multilateral are cut only if the scenario says so.

**Programme areas to model lines.** IHME's programme-area columns are grouped into the model's service lines:

| Service line (dashboard label) | IHME programme areas |
|---|---|
| HIV Treatment (ART) | `hiv_treat` |
| HIV Testing & Care | `hiv_care` (care and support), `hiv_ct` (counselling and testing) |
| Prevention Of Mother-To-Child Transmission | `hiv_pmtct` |
| HIV Prevention (PrEP, VMMC, Condoms, Key Populations) | `hiv_prev` |
| Orphans & Vulnerable Children | `hiv_ovc` |
| HIV unspecified | `hiv_other`, `hiv_amr` |
| HIV systems support | `hiv_hss_other`, `hiv_hss_hrh`, `hiv_hss_me` |
| TB Case Finding & Treatment | `tb_treat`, `tb_diag` |
| Drug-Resistant TB | `tb_amr` |
| TB unspecified / systems | `tb_other` / `tb_hss_*` |
| Bednets & Other Vector Control | `mal_con_nets`, `mal_con_oth` |
| Indoor Residual Spraying | `mal_con_irs` |
| Malaria Testing & Treatment | `mal_diag`, `mal_treat`, `mal_comm_con` |
| Malaria unspecified / systems | `mal_other`, `mal_amr` / `mal_hss_*` |
| Routine Immunization (Vaccines + Delivery) | `nch_cnv` |

**Result.** 40,005 country x donor x channel x line cells in `model_data/dah_lines.csv` for 70 countries (Panama is in
the country list but has no recorded aid for these four areas): US$10.34 billion a year, of which HIV US$5,273
million, malaria US$1,900 million, immunization US$1,650 million, TB US$1,522 million. By donor: United States
US$5,204 million (50%), United Kingdom 889, Gates Foundation 651, Germany 610, France 570. By channel: Global Fund
US$4,274 million, Bilateral Agency 2,684, NGOs 1,478, Gavi 1,118.

**Files.** `model_data/dah_lines.csv`; built by `prepare_model.py`.

### 2b. Scenarios And Cut Paths

**In plain words.** A Donor Scenario says which donors cut how much of their money, through which channels. The cut
on each cell combines a donor cut (bilateral or multilateral) with any channel-wide cut so that nothing is counted
twice: a 50% donor cut on top of a 20% channel cut removes 60%, not 70%.

**Formula in words.** Cut on a cell = 1 minus (1 minus the donor's cut) times (1 minus the channel's cut). In symbols:
cut = 1 - (1 - x)(1 - y), where x is the donor cut for that channel type and y the channel cut; a donor-channel pair
cut, where given, replaces x. Money lost in a cell = baseline x cut. A service line whose aid would rise counts as
no loss (gains are not modelled).

**The presets** (Donor Scenario selector):

| Donor Scenario | What it assumes | Source |
|---|---|---|
| US Bilateral Exit + Multilateral Withdrawals | US money through Bilateral Agency, NGOs, Gates Direct and Other channels: -100%; US contributions through WHO, Gavi and UNFPA: -100%; US Global Fund pledge: -23% (US$6.0 billion to US$4.6 billion, so 77% is kept); US money through UNICEF, UNAIDS and development banks and all other donors unchanged | US announcements: WHO exit effective January 2026, Gavi funding stopped June 2025; Global Fund Eighth Replenishment, November 2025 |
| America First MOUs | For the 16 countries with a signed Memorandum of Understanding and a funding schedule: US direct aid follows the country's own schedule year by year (cut in year t = 1 - US funding that year / the 2021-2025 reference), used exactly as written; a funding increase is a 0% cut; a schedule that ends in 2028 holds its 2028 cut; US multilateral exits as above; co-financing commitments are not modelled; amounts are nominal US$ as written (a `mou_deflate` switch in the parameter file expresses them in 2023 US$ at an assumed 2% a year, raising the preset's deaths by 14%) | KFF America First MOU tracker (signed status); the team's MOU and co-financing sheet (schedules) |
| IHME 2025 Preliminary Estimates | Each donor x channel x disease cell changes by IHME's 2025 preliminary total divided by its 2021-23 average (a global ratio applied to the country's own mix; cells under US$20 million a year use the donor x disease ratio; clipped to 0 to 1.5) | IHME DAH database, 2025 preliminary estimates |
| Total-Aid Cuts (OECD) Applied to Health Aid | Each donor's 2025 change in total official development assistance applied to its health aid, bilateral and multilateral alike: United States -57%, Germany -17.4%, France -10.9%, United Kingdom -10.8%, Japan -5.6% | OECD preliminary 2025 ODA data, April 2026 (total aid, not health-specific; labelled as such) |
| Global Fund & Gavi Shortfalls | Every donor's money through Gavi falls by the Gavi Funding Cut (%) slider (default 15%) and through the Global Fund by the Global Fund Funding Cut (%) slider (default 20%), against each fund's 2021-23 disbursements; no US multilateral exit is added | Gavi 6.0 pledges vs 2021-23 spending (our estimate); Global Fund Eighth Replenishment US$12.64 billion vs US$15.7 billion in the Seventh (about -20%); KFF and Aidspan allocation data are the slider marks |
| Combined Retreat | US Bilateral Exit + Multilateral Withdrawals plus the OECD total-aid cuts for Germany, France, the United Kingdom and Japan | As above |
| Custom | Cuts set by the user by donor (direct and multilateral) and by channel | |

**Cut paths** (How Funding Changes). The share of the scenario's full cut in force in each year 2026 to 2030, with
u = year / 5: Sudden (default) 100% every year; Linear phase-out 20, 40, 60, 80, 100%; Front-loaded 1 - (1 - u)^2 =
36, 64, 84, 96, 100%; Back-loaded u^2 = 4, 16, 36, 64, 100%; S-curve (a logistic curve with slope 1.5 around year 3,
rescaled so that year 5 is 100%) = 18, 32, 56, 83, 100%; Custom (set year by year). The MOU schedules are used as
written and are never multiplied by a path.

**Files.** `scenarios.py` (presets and paths), `model_data/ihme_trend.csv` (IHME 2025 ratios), `model_data/
mou_signed.csv` and the `mou_us_*` columns of `country_inputs.csv` (MOU schedules).

### 2c. Government Response

**In plain words.** The government can put its own money into the gap. The dashboard offers four options
(Government Response selector) and limits each by fiscal space: the extra money a health budget could realistically
find in a year.

**Options.**
- **No Government Replacement** (default): nothing is replaced.
- **Replace a Set Share**: the government replaces a share of the lost aid set with the Share of Lost Aid Replaced (%)
  slider (default 25%), capped at fiscal space when Cap Replacement at Fiscal Space is ticked (default on).
- **As Much as Fiscal Space Allows**: all of the loss, capped at fiscal space.
- **Gradual Budget Increase**: the government raises health's share of its total budget by a number of percentage
  points a year (Points per Year; Steady, Fast start, Slow start or Custom shapes), never past the Abuja target of
  15%; extra money = points / 100 x total government spending, where total government spending = government health
  spending 2023 / health's share of government spending (World Bank WDI, latest year), held at its 2023 level in
  constant 2023 dollars. A `budget_growth` setting (default 0) can let that budget grow at the country's projected
  nominal GDP growth (WEO, median 7.5% a year); at the full rate the all-country gradual-increase result falls by
  22% (Batch 7).

**Why No Government Replacement is the default.** A two-way fixed-effects regression across 97 countries and 2,134
country-years (2002 to 2023) relates the yearly change in government health spending per person to falls in aid per
person this year and last year, controlling for GDP growth. The implied replacement rate is minus the sum of the two
fall coefficients: -(0.073 + 0.116) = -0.19 per US$1, with a 95% confidence interval of about -0.45 to +0.07. On
average, governments did not replace falling aid.

**Fiscal space, in words.** Government health spending in 2023 times how much faster than usual it could grow in a
strong year, times a debt-stress factor. In symbols: capacity = GHES_2023 x max(0, g_strong - max(g_typical, 0)) x s,
where g_typical is the country's median real growth in government health spending 2001 to 2023 (IHME), g_strong its
75th percentile (Strong year; or the 90th percentile under Best years in Advanced), and the debt-stress factor s =
clip(1 - (interest as % of revenue - 10) / 40, 0.25, 1): 1 when interest takes 10% of revenue or less, falling to
0.25 at 40% or more. Interest as a share of revenue is IMF World Economic Outlook (October 2026) net interest, with the World Bank
series as a flagged fallback (not needed by any country).

**Where the replacement goes.** Pro-rata to what was cut (default): in proportion to each service's loss. Hypothetical
best case (triage): services are refilled in order of the model's own deaths averted per dollar (usually TB
treatment, vaccines and ART first). This is an optimisation rule, not observed behaviour, and is labelled as such.

**Formula.** Budget in year t: B_t = min(replacement_t + extra government money_t, loss_t). Net loss by service =
effective loss - its share of B_t.

**Files.** `country_inputs.csv` (`ghes_2023`, growth percentiles, `interest_pct_revenue`), `model_data/
regressions.json` (the regression), `ext_data/wdi/sh_xpd_ghed_ge_zs.csv` (health share of government spending).

### 2d. Money To People

**In plain words.** Each service has a cost per person served. Lost money divided by that cost gives the people who
lose the service. Three refinements keep this honest: money that funds systems or management does not buy patients;
money with no stated purpose is split by what the country's grants actually fund; and donors cannot be credited with
more people than their money pays for.

**Unit costs (cost per person served, constant 2023 US dollars, Cost per Person column of the service table):**

| Service | Cost (central, range) | How it is built and why it measures the right thing |
|---|---|---|
| HIV Treatment (ART) | by country; median US$216 (191 to 400); Kenya 308, Nigeria 208, Mozambique 227, South Africa 208, Uganda 314, India 216 | The lower of (a) the site-level cost per patient-year from the Global Health Cost Consortium repository pooled with Rosen et al. 2021 (Gates Open Research 5:177), times 1 / (1 - 0.45) for above-site programme costs (management, monitoring, supply chain: 47% of PEPFAR spending, KFF 2025), and (b) observed HIV treatment spending per person on ART (total HIV spending from ten Brink et al. 2025 appendix Table B2 or WHO GHED, times the country's Global Fund treatment module share, divided by UNAIDS people on ART), used only where the Global Fund funds at least 10% of HIV spending (35 countries), otherwise the regional median ratio of (b) to (a). Floor US$190.84 = the lowest measured site delivery cost (Malawi, US$86.50 in 2018 US dollars, Rosen 2021) inflated and marked up; gate US$50 to 600. The model needs what a dollar of lost treatment money pays for per patient, so a cost above what a country spends per person on ART cannot be right (logic review L-50) |
| Prevention Of Mother-To-Child Transmission | US$250 (150 to 450) per woman per year, including her ART | Health Policy and Planning 2016;31(8):1133 review of Option B+ costs (US$114 to 470 across five studies; median about 250 in 2023 dollars) |
| HIV Prevention | US$5,000 (2,500 to 12,000) per infection averted at an incidence of 1 per 1,000, scaled by (1 / incidence)^0.5 | Labelled assumption: prevention costs more per infection averted where infections are rare; affects infections only |
| Orphans & Vulnerable Children | US$100 (60 to 160) per child-year | Labelled assumption; no deaths modelled |
| TB Case Finding & Treatment | by country, provider cost per course x 1 / (1 - 0.45): Kenya 150, India 105, Ethiopia 218, Philippines 120 (Value TB facility costs, 2018 dollars); South Africa 274 (Vassall 2017); others 275 / 135 / 678 by income group (pooled with Laurence, Griffiths & Vassall 2015) | Facility-level financial cost of a full course (intensive plus continuation phase), the money that buys one treated patient |
| Drug-Resistant TB | Kenya 2,818, Philippines 1,580 (Value TB short regimen); South Africa 9,256; others 1,568 / 2,818 / 8,028 by income group | As above, second-line regimens |
| Bednets & Other Vector Control | US$2.20 (1.40 to 3.50) per person-year of net use | US$5 per net delivered / (1.8 people per net x 2 years) / 63% of nets in use (GiveWell); a cost per person actually sleeping under a net, matching the coverage measure (MAP net use) and the effect size (children sleeping under a net); a 3-year net life gives US$1.47, inside the range |
| Indoor Residual Spraying | US$8.50 (6 to 10) per person protected per year | PMI Africa IRS project, Mali 2012-14, US$6.08 to 7.40 (2014 dollars) inflated |
| Malaria Testing & Treatment | US$14 (4 to 47) per case treated | White et al. 2011, Malaria Journal 10:337: US$5.84 treatment + US$4.32 diagnosis (2009 dollars) inflated |
| Routine Immunization | US$87 (38 to 104) per fully immunized child | Lydon et al. 2014 delivery cost per infant US$45.6 + MSF The Right Shot 2015 vaccine prices US$41.3 (low end), both in 2023 dollars; high = MSF high price; low = Brenzel 2015 |

Study costs are brought to 2023 US dollars with the US consumer price index (CPI-U).

**Overhead counted once.** HIV and TB treatment costs are site costs times 1.818 (1 / (1 - 0.45)), so every patient
already carries the above-site programme cost. Systems money (laboratories, human resources, monitoring, supply
chain; IHME's `*_hss_*` areas) is that above-site money. Converting it into patients a second time would count it
twice, so it is lost "without a modelled service effect" (parameter `hss_service_share` = 0; logic review L-05). HIV
Testing & Care money funds diagnosis and retention, not drugs; it has no patients of its own, and half of its loss
(parameter `hss_kappa` = 0.5, range 0.25 to 0.9, a labelled assumption) is counted as lost ART at the ART cost.

**Unspecified money.** IHME's "other" programme areas (16% of HIV aid, 46% of TB, 27% of malaria) have no stated
purpose. The model splits them by the country's Global Fund grant budgets by module (Grant Cycle 7): the treatment
share goes to treatment lines, the prevention share to prevention lines, the testing share is treated like Testing &
Care, the systems share joins systems money and the programme-management share is lost without a service effect.
Median shares: HIV treatment 35%, prevention 23%, testing 6%, systems 11%, management 22%; TB 49 / 1 / 21 / 10 / 17%;
malaria 22 / 48 / 0 / 14 / 15%. Countries without a Global Fund grant use their WHO-region median.

**Effective loss formula.** For a service line l: effective loss = its own lost money + unspecified lost money x the
share for its purpose x the line's share of its purpose group (+ systems money x 0). Money is conserved: service
losses plus non-service losses equal the total lost.

**The cap rule (donor-funded pool).** Donor money pays for a number of people: its baseline aid divided by the cost
per person, but never more than the people whose service donors actually fund. In symbols: donor-funded people =
min(people covered x donor share, aid / cost). People losing the service = donor-funded people x the share of donor
money lost, times (1 - continuity). The donor share is the external share of public spending on the disease (WHO
Global Health Expenditure Database: external / (external + domestic government); household spending on STI care or
private vaccination is not the donor-funded service) for HIV and immunization; WHO TB financing data for TB; and for
each malaria intervention, the people its own donor money pays for as a share of people covered (the cap is applied
per intervention, so the share must be that intervention's). In most lines donor money buys fewer people than the
pool and the rule is simply lost money / cost.

**Continuity.** 15% (range 0 to 30%) of the people who lose donor funding keep their service anyway (absorbed by
government facilities or cheaper delivery). Labelled assumption: the 2025 evidence (KFF: PEPFAR ART counts "remained
relatively stable"; Cust & Chabata 2026: treatment "22% to 32%" lower at defunded NGOs; WHO: TB treatment "the least
affected") all describes partial withdrawals with commodities still flowing, so no study measures the quantity.

**Full-cost equivalents.** People who stop ART = lost ART money / full cost per patient-year. Each such unit is
treated as a person who actually stops treatment. We do not use PEPFAR's 20.6 million people at supported sites,
because that count includes people whose drugs the government or the Global Fund buys; applying death risks to it
would credit the lost money with people it does not pay for. The Validation page compares the model's donor-funded
people on ART with PEPFAR's figure.

**Files.** `country_inputs.csv` (`art_cost_full`, `tb_ds_cost`, `tb_dr_cost`, `unspec_*`, `donor_share_*`),
`model_params.csv`, `unit_cost_reference.csv`; built by `batch34_inputs.py` from the `audit/batch*_*.py` scripts.

### 2e. Coverage Change

**In plain words.** The people who lose a service, divided by everyone who needs it, is the drop in coverage.

**Need and coverage by service** (People in Need and Coverage Before columns): ART: people living with HIV and ART
coverage (UNAIDS AIDSinfo 2026 estimates for 2025, read directly from the UNAIDS file since Batch 7); PMTCT:
HIV-positive pregnancies (women needing ARV) and PMTCT coverage (same file); TB: WHO TB incidence and the case
detection rate (capped at 100%); drug-resistant TB: WHO's rifampicin-resistant share of incidence and enrolment;
bednets and spraying: population at risk (WHO) and Malaria Atlas Project (MAP) 2025 net use and household spraying
coverage; malaria treatment: MAP clinical cases and effective treatment per 100 cases; immunization: projected births for each year 2026 to 2030 (UN WPP 2024, since Batch 7) and DTP3
coverage (WHO/UNICEF WUENIC 2025, since Batch 7). People losing a service can never exceed the people covered.

**Formula.** Coverage drop (percentage points) = people losing the service / people in need x 100; Coverage After =
Coverage Before - the drop.

### 2f. Deaths And Infections

#### HIV

**People who stop ART.** As above: lost ART money (plus half of lost Testing & Care money) / cost per patient-year,
times (1 - continuity), never more than people on ART outside PMTCT.

**Death risk by years since stopping.** Excess deaths per person-year off ART rise as immunity falls: 1.3%, 2.5%,
3.7%, 4.9% and 6.0% in years 1 to 5, then 6.8%, 7.2%, 7.3%, 7.1%, 6.7% in years 6 to 10 (18.4% over five years).
These come from a CD4 cohort calculation (`audit/batch2_cohort.py`): people start in the CD4 distribution of people
on ART (ZIMPHIA 2020, Table 10.1: median 528 cells per microlitre), move through CD4 stages at untreated rates and die
at untreated stage-specific rates (Optima HIV, ten Brink et al. 2025 appendix Tables A1 and A2), minus the deaths they
would have had on suppressive ART. Multiplier `art_hazard_mult` 1 (0.65 to 1.70: women with Optima's low rates to men
with its high rates). People who stop are tracked as cohorts: a rise in the number off ART starts a new cohort, a fall
returns the most recent cohorts to care first.

**Re-engagement.** After 2030, with funding assumed back, people still off ART return to care at 35% a year (range
17% to 68%: Kranzer 2010; Kaplan 2017; Mody 2026, all indirect evidence from people who disengaged while services ran);
until they return they keep their excess risk.

**Transmission.** Each person off ART transmits HIV at the country's UNAIDS 2025 rate of new infections per person
with unsuppressed viral load (new infections / (people living with HIV - people with suppressed viral load); median
0.12 a year, Kenya 0.070; half in the first year off treatment), times `art_transmission_mult` 1 (0.71 to 1.38, the
UNAIDS bounds). The people infected are unsuppressed for about 4 years on average (2.5 to 5.5, labelled assumption
from the 2.6-year median time to diagnosis, Giguere et al. 2021) and transmit at the same rate: one further
generation is counted, no more.

**Deaths from new infections.** Adults infected die on the untreated survival curve (Weibull, median 10.5 years,
Todd et al. 2007), scaled by that year's chance of eventually dying of HIV: 85% untreated (70 to 95) or 10% treated
(5 to 20, assumption), weighted by ART coverage. Deaths to 2030 go to the line that caused the infection; deaths in
2031 to 2035 go to Further Deaths.

**PMTCT.** Deaths per mother losing PMTCT = transmission averted 25% (10 to 40; WHO) x infant death by age 2 if
infected 45% (35 to 52.5; Newell et al. 2004).

#### TB

**Course costs.** As in 2d; the number of patients untreated = lost money / (course cost x 1.818).

**Drug-susceptible vs drug-resistant.** Two lines. Drug-susceptible: deaths per patient untreated = case fatality
untreated 43% (28 to 53) minus treated 3% (0 to 7) for HIV-negative patients (WHO TB burden estimation methods,
Table 4), and for HIV-positive patients 78% off ART or 49% on ART (Table 5) weighted by ART coverage, minus 6%
treated; weighted by the share of TB patients with HIV. Drug-resistant: 45% deaths averted per patient treated
(30 to 60, labelled assumption). TB spread: each untreated patient causes 0.4 (0.2 to 0.8) further cases (Styblo 1991;
Vynnycky & Fine 1997), arriving one and two years later and treated at that year's reduced coverage. The ramp-up: 70%
of the full effect in the first year.

#### Malaria

**Coverage.** MAP 2025 net use (people sleeping under a net), household spraying coverage (the larger of MAP's value
and what donor spraying money pays for), and effective treatment per 100 cases, each over its population base.

**Lives Saved Tool effect sizes.** Deaths after the cut = baseline deaths x (1 - E_v x C_v1) / (1 - E_v x C_v0) x
(1 - E_c x C_c1) / (1 - E_c x C_c0), where vector control coverage C_v = 1 - (1 - net use)(1 - spraying), E_v = 55%
(40 to 61; Eisele et al. 2010) and E_c = 97% (82 to 99; Thwing et al. 2011, ACT for uncomplicated malaria).

**Under-5 share by WHO region.** The effects are for children aged 1 to 59 months. The World Malaria Report 2025
gives the under-5 share of malaria deaths by region: African Region 75% (p. 20), Americas 20% (below 25%, p. 24),
Eastern Mediterranean 36.4% (p. 28), South-East Asia 25% (pp. 31-32), Western Pacific 40% (p. 35); ranges of plus or
minus 5 points are an assumption around the WHO figure.

**Effect at 5 and over.** The child effects times `mal_adult_effect_frac` 0.5 (0 to 1), a labelled assumption: no
published adult effect size was found.

**Trend and rebound.** Baseline deaths follow the country's 2015 to 2024 trend in WHO's estimated malaria deaths
(clipped to plus or minus 5% a year, an assumption); deaths from lost nets and spraying grow by 10% a year (0 to 25%,
assumption; direction from Cohen et al. 2012's 75 resurgence events) while the loss lasts.

**The intervention-specific cap.** The donor share for bednets, spraying and treatment is the people each
intervention's own donor money pays for (baseline money / unit cost) as a share of the people covered, capped at
100% (medians: nets 53%, spraying 100%, treatment 39%). An earlier rule used the external share of all public malaria
spending, which is dominated by domestic case-management salaries and gave Nigeria's donor-funded nets a pool of 22%
of net users although donor money pays for 63%.

#### Vaccines

**Deaths averted per vaccinated child.** From the VIMC estimates published with Toor et al. 2021 (eLife 10:e67635):
deaths averted attributed to each vaccination year, by disease and country. For each routine infant antigen the
country uses (hepatitis B, Hib, pneumococcal, rotavirus, measles, rubella, yellow fever, meningitis A where in the
schedule; WHO/UNICEF coverage above zero in 2025), deaths averted per vaccinated child = VIMC deaths averted /
vaccinated children, averaged over the vaccination years 2015 to 2019, the years VIMC based on reported coverage. For
measles, meningitis A and yellow fever the lowest of the five years is used, because the VIMC files do not separate
campaigns from routine doses (campaigns inflate the mean by about 10% for measles and yellow fever and 3.9 times for
meningitis A).

**Denominators.** Vaccinated children = WHO/UNICEF coverage x UN World Population Prospects 2024 surviving infants
(the WHO/UNICEF denominator for every antigen used here; the hepatitis B birth dose uses live births but the same child
is counted once).

**Mortality-trend adjustment.** The sum over antigens is multiplied by the country's World Population Prospects
under-5 mortality (Q5) in 2026 to 2030 divided by 2015 to 2019 (Kenya 0.84, Nigeria 0.81, India 0.62), a labelled
adjustment so the values reflect current child mortality. No further trend applies to vaccines.

**Timing.** Each missed cohort's deaths are spread by years since vaccination using the VIMC timing per pathogen
(fitted by non-negative least squares to the VIMC calendar-year and birth-cohort series): measles 77% in the
vaccination year and 23% the year after; rotavirus 64 / 36%; Hib and PCV 57 to 59% then 23 to 24%, 7 to 9%, 4 to 8%,
3 to 6%; rubella 100% in year 0; hepatitis B 42 / 21 / 16 / 13 / 9% of its under-5 deaths. The under-5 share of each
pathogen's lifetime deaths is the country's own (100% for Hib, PCV, rotavirus, rubella; 94% measles; 15% meningitis
A; 8% yellow fever; 1.5% hepatitis B). Deaths in years 5 to 9 are counted where identified (measles 1%, hepatitis B
0.4%); the rest (adult hepatitis B, meningitis A and yellow fever at age 5 and over) is outside the model's window.

**Gate.** Each country-antigen value must lie within 0.1 to 10 times Toor et al. 2021 Table 3 (deaths averted per
1,000 fully vaccinated persons: measles 6.5, hepatitis B 7.7, Hib 2.4, PCV 2.3, yellow fever 2.1, meningitis A 1.0,
rotavirus 0.8, rubella 0.3); 38 of 620 values fell outside and take the WHO-region median, as do the four dashboard
countries VIMC does not cover (Botswana, Dominican Republic, Libya, Mauritius). Result: median 0.025 deaths averted
per fully immunized child over a lifetime (Kenya 0.021, Nigeria 0.059, India 0.012). Range: the VIMC 95% credible
intervals through `imm_dpc_mult` 1 (0.56 to 1.64).

**What is excluded and why vaccine deaths are a floor.** DTP (pertussis, tetanus, diphtheria), polio and BCG are not
in the VIMC estimates and no citable deaths-averted-per-child value by country or region was found (Shattock et al.
2024, Lancet, report totals by pathogen and region only). HPV is an adolescent vaccine outside the infant schedule and
the cost per child; Japanese encephalitis has no WHO/UNICEF antigen. A child who misses the full schedule also misses
those vaccines, so the counted deaths understate the true number: a conservative floor, stated on the dashboard.

### 2g. Deaths After 2030 (Committed Deaths)

**In plain words.** A cut that starts late in the period shows few deaths before 2030 only because its deaths come
later. To avoid flattering late cuts, the model follows the deaths set in motion by the 2026 to 2030 losses for five
more years, to the end of 2035, assuming funding is back from 2031. They are reported separately as Further Deaths,
2031-2035 (Assumption-Driven), not in the headline, because they depend mostly on the assumed return-to-care rate.

**Four parts.** People still off ART (returning at 35% a year, keeping their risk by years since stopping);
deaths in 2031 to 2035 of adults infected with HIV in 2026 to 2035 by people off ART or because prevention was lost;
missed vaccine cohorts' deaths falling in 2031 to 2035; secondary TB cases arriving in 2031 and 2032. Under US
Bilateral Exit + Multilateral Withdrawals: 990,588 further deaths (560,282 to 1,761,411), of which people off ART
694,084, new HIV infections 261,764, TB spread 19,498, missed vaccines 15,243. The dashboard also shows the range
across the return-to-care assumption alone (`art_reengage` at 0.68 and 0.17).

### 2h. Uncertainty

**In plain words.** Every uncertain number in `model_params.csv` has a low, central and high value. The model is run
400 times with each parameter drawn from a triangular distribution between its low and high values (peaked at the
central), the same draws in every country (random seed 7). The dashboard shows the central run as the point value and
the 2.5th to 97.5th percentile of the 400 draws as the range.

**Which parameters vary.** All 48 rows of `model_params.csv` except the constants (`hss_service_share`,
`hiv_legacy_art_params`, `mal_u5_use_country_series`, `imm_legacy_u5mr_scaling`, whose low equals their high). The
inputs in `country_inputs.csv` (aid, coverage, people in need, unit costs by country) are not varied; the country cost
columns move through multipliers (`uc_art_mult`, `uc_tb_mult`, `imm_dpc_mult`) that map onto each country's own low and
high values.

**What the range means.** The dashboard calls it Range Across Parameter Values: the spread of results across the
parameter draws. **What it does not mean.** It is not a confidence interval. Uncertainty in the data (aid amounts,
people in need, coverage, baseline deaths) and in the model's structure (for example whether lost money means people
stopping treatment entirely) is larger and is not included. For All Countries totals the range is the percentile of
the all-country total in each draw (not the sum of country percentiles, which would overstate the width); the
dashboard shows that range for the all-disease total and for further deaths. The all-country HIV infections and
people-who-stop-ART figures are shown as central values only; the sums of country percentiles in Section 1 are an
upper bound on their widths.

### 2i. How The Model Is Checked

- **Automated checks** (`audit/checks.py`): 59 invariants over every country, Donor Scenario and Government Response
  (76,501 checks in the full run): displayed values equal the central run; coverage stays between 0 and 1; people
  losing a service never exceed people covered; deaths never exceed people affected; money is conserved through the
  splits; more cut never means fewer deaths; a zero cut gives zero; precomputed All Countries files match fresh runs;
  the cut formula matches the documented scenarios; modelled aid equals IHME's totals. Last run: 0 failures, 6 known
  warnings (small differences between two IHME products in Section 1).
- **Tests** (`tests/`): 357 tests, including regression baselines locked for 99 country-scenario-response
  combinations and checks that the funding-path and cohort mechanisms reproduce the sudden-cut results exactly. All
  pass.
- **Independent reproduction** from the specification alone: 1,980 of 1,980 cells within 0.5%.
- **Validation** (`audit/logic_review/validation.md`; Methods page, Validation Against External Benchmarks), with a
  stated band of 0.5 to 2 times the benchmark: HIV deaths are 0.39 and infections 0.36 of Optima HIV's
  PEPFAR-discontinued excess over 15 overlapping countries (Kenya 1.04, Eswatini 1.17, Dominican Republic 1.09 agree;
  South Africa 0.18 and the small programmes are below; Tajikistan 3.65 above, because Optima records no international
  HIV funding there); people on ART match UNAIDS (median ratio 1.00); excess TB deaths are a median 9% of WHO's 2024
  TB deaths (Mozambique 79%); the model's TB cost is 0.47 of the national programme budget per notified patient
  (budgets fund whole programmes); excess malaria deaths are a median 6% of World Malaria Report deaths (maximum
  Zambia 28%); vaccine deaths per 1,000 children are 0.65 to 2.3 times Toor's per-dose figures by antigen.

---

## 3. Worked Example: Kenya Under US Bilateral Exit + Multilateral Withdrawals

Dashboard defaults: Donor Scenario US Bilateral Exit + Multilateral Withdrawals; How Funding Changes: Sudden
(default); Government Response: No Government Replacement; Account for Already-Changing Death Rates: on; default
parameters. Kenya has signed an America First MOU with a funding schedule (group A: cuts of 0%, 4%, 16%, 20%, 60% in
2026 to 2030), shown under the Donor Scenario selector; it is not used by this scenario.

**Step 1, Aid Baseline.** Kenya's HIV, TB, malaria and immunization aid averaged US$483.6 million a year in 2021 to
2023 (Section 4 header and The Numbers: Aid at Risk (per Year) sub-line "57% of US$484M"). By donor: United States
US$323.8 million (67%), United Kingdom 25.7, Gates Foundation 24.7, Other Private 21.4, Germany 18.9, France 18.0.
By disease: HIV US$340.3 million, malaria 81.4, TB 34.4, immunization 27.5. By channel: Bilateral Agency 207.3, Global
Fund 152.1, NGOs 85.5, Gavi 16.4, Gates Direct 12.3. By line: HIV treatment 106.4, HIV testing and care 73.5, HIV
systems 55.8, HIV unspecified 46.2, HIV prevention 43.1, bednets 21.3, malaria unspecified 20.8, malaria systems 17.8,
malaria treatment 16.4, TB systems 15.1, TB unspecified 9.3, TB treatment 9.1, immunization 27.5.

**Step 2, Scenario Cut.** US money through Bilateral Agency (US$202.5 million) and NGOs (60.0) is cut in full; 23% of
the US money through the Global Fund (13.2); US money through Gavi (1.9), WHO (0.15) and UNFPA (0.03). Aid at Risk
(per Year): **US$277.7 million**, 57% of the baseline (The Numbers; Where the Money Is Lost chart, Aid Lost per Year).

**Step 3, Government Response.** None (default). For reference, the Can Kenya Fill the Gap? panel shows fiscal space
of US$21.1 million a year: government health spending US$2,138 million x surge 1.97 points (75th percentile growth
10.2% minus median 8.2%) x debt-stress 0.50 (interest 30.0% of revenue, IMF WEO 2024); health is 8.65% of
government spending (2023); the break-even rise is 1.12 points of the budget a year.

**Step 4, Money To People** (What Each Service Loses table). After splitting unspecified money (Kenya's Global Fund
HIV shares: treatment 50%, prevention 29%, testing 9%, systems 1%, management 10%) and dropping systems money, the
yearly net loss by service and the people it buys:

| Service | Net Aid Lost per year | Cost per Person | People Losing Service, per Year | Pool rule |
|---|---|---|---|---|
| HIV Treatment (ART) | US$103.1 million (+ half of US$67.6 million Testing & Care) | US$308 | 377,732 people who stop ART | donor share 0.73 x 1,326,509 on ART outside PMTCT = 968,000; donor money buys 420,000; not binding |
| Prevention Of Mother-To-Child Transmission | US$5.0 million | US$250 | 14,803 women | donor money exceeds the pool (0.73 x 38,491); pool x share lost |
| HIV Prevention | US$27.3 million | US$8,399 per infection averted | 2,768 infections averted lost | none |
| Orphans & Vulnerable Children | US$6.6 million | US$100 | 56,392 children | none; no deaths |
| TB Case Finding & Treatment | US$2.9 million | US$273 | 9,178 patients | not binding |
| Drug-Resistant TB | US$0.24 million | US$5,124 | 40 patients | not binding |
| Bednets & Other Vector Control | US$10.8 million | US$2.20 | 4,185,036 person-years of net use | share 0.58; not binding |
| Indoor Residual Spraying | US$1.8 million | US$8.50 | 177,828 people | not binding |
| Malaria Testing & Treatment | US$5.2 million | US$14 | 313,590 cases | not binding |
| Routine Immunization | US$2.5 million | US$87 | 24,728 children | share 0.90; not binding |

Each figure is already reduced by continuity (15%). The Numbers hero shows Treatment Lost Each Year 715,343 (ART
377,732, PMTCT 14,803, TB 9,218, malaria treatment 313,590) and Prevention Lost Each Year 4,387,592 (bednets, spraying,
vaccines).

**Step 5, Coverage Change** (Coverage Before to After in the table): ART 91.0% minus 25.2 points (people who stop ART
/ 1.5 million people living with HIV); PMTCT 91.0% minus 35.0 points; TB detection 81% minus 7.8 points;
drug-resistant TB 47% minus 4.1 points; net use 43.7% minus 7.4 points; spraying 2.7% minus 0.3 points; malaria
treatment 57.9% minus 8.2 points; DTP3 91% minus 1.6 points.

**Step 6, Deaths And Infections** (Extra Deaths Over 5 Years and the table's Extra Deaths column):

| Disease | Extra Deaths Over 5 Years | Range | How |
|---|---|---|---|
| HIV | 78,776 | 48,701 to 138,351 | ART 70,927 (377,732 people x hazards 1.3 to 6.0% a year, plus deaths from the infections they cause); PMTCT 7,661 (14,803 x 0.25 x 0.45 x 5 years with a 60% first-year ramp); prevention 189 |
| TB | 19,872 | 11,814 to 26,848 | 9,178 patients a year x case fatality difference (HIV share of TB patients 21%, ART 91%) plus 0.4 secondary cases each |
| Malaria | 12,580 | 5,304 to 13,351 | bednets 3,194, spraying 83, treatment 9,303 from 11,656 baseline deaths, under-5 share 75% |
| Immunization | 1,630 | 1,147 to 3,822 | 24,728 children a year x 0.0209 deaths per child over a lifetime, of which 0.0143 within ten years and 73% of that in the year missed |
| All four | **112,858** | **75,243 to 170,040** | year 1: 10,945; years 1 to 5: 10,945, 18,059, 23,112, 28,030, 32,711 (Extra Deaths Each Year chart) |

New HIV Infections, 5 Years: **164,310** (95,817 to 242,030): 131,969 from people off ART (including their onward
transmission), 13,838 from lost prevention, 18,504 infant infections from lost PMTCT.

**Step 7, Further Deaths, 2031-2035 (Assumption-Driven):** 63,606 (29,700 to 126,782): people still off ART 53,934,
their and prevention's new infections 8,750, TB spread 799, missed vaccines 123; 29,498 to 98,003 across the
return-to-care assumption.

**Per US$1 million** (What Every US$1 Million Cut Does, by Disease cards): HIV 290 extra deaths over five years for a
US$1 million-a-year cut (about US$17,000 of aid per life lost); TB 2,560 (US$2,000); malaria 581 (US$9,000);
immunization 644 (US$8,000).

**Where Kenya appears.** Dashboard page: Section 4, How Aid Cuts Translate into Coverage and Lives in Kenya (The
Numbers; the US$1 million cards; Where the Money Is Lost; What Each Service Loses; How the Damage Scales; Can Kenya
Fill the Gap?). All Countries page: Kenya's row (deaths 112,858, 200 per 100,000 people). Validation page: the three
methods compared for Kenya.

---

## 4. Data Sources Table

| Dataset | Producer | Year used | Contents | Units | Step |
|---|---|---|---|---|---|
| Development Assistance for Health database, 1990-2026 | IHME | 2021-2023 average; 2025 preliminary for the IHME preset | Aid by source, channel, recipient and programme area | thousands of constant 2023 US$ (x 1,000) | 2a, 2b |
| Health spending 1995-2023; expected spending 2024-2050 | IHME | 2023 | Government health spending, growth history | constant 2023 US$ | 2c |
| World Economic Outlook, October 2026 | IMF | latest actual year | Revenue, expenditure, balances (interest as share of revenue) | % of GDP | 2c |
| World Development Indicators | World Bank | latest year | Health share of government spending; TB detection; HIV incidence; population; births | % and counts | 2c, 2e |
| Global Health Observatory | WHO / UNAIDS | 2025 (HIV); 2024 (malaria) | People living with HIV, ART and PMTCT coverage; malaria deaths, cases, incidence | counts, % | 2e, 2f |
| Global TB Report data | WHO | 2024 | TB incidence, deaths, notifications, RR-TB share and enrolment, financing | counts, US$ | 2e, 2f, 2d (TB donor share), 2i |
| Malaria Atlas Project national estimates | MAP | 2025 | Net access and use, IRS coverage, effective treatment, clinical cases | % and counts | 2e, 2f |
| World Malaria Report 2025 | WHO | 2024 | Under-5 share of malaria deaths by region; funding | % | 2f |
| Global Health Expenditure Database (December 2025 update) | WHO | latest year, 2016-2023 | Spending on HIV/STDs, malaria and immunization by source (external, government, private) | million current US$ | 2d (donor shares, ART observed spending) |
| Global Fund Data Explorer (allocations, budgets by module, disbursements) | The Global Fund | Grant Cycle 7 (2023-2025); disbursements by year | Module shares; HIV disbursements | nominal US$ | 2d |
| Unit Cost Study Repository (HIV ART, TB) | Global Health Cost Consortium | 2015-2021 studies | Site-level cost per patient-year and per course | 2020 US$ | 2d |
| Value TB patient-level costs | Sweeney et al. | 2018 | Facility cost per TB course, five countries | 2018 US$ | 2d |
| Rosen et al. 2021 (AMBIT synthesis) | Gates Open Research 5:177 | 2018-2020 | ART site costs, five countries | 2018-2020 US$ | 2d |
| Optima HIV appendix (ten Brink et al. 2025) | Lancet HIV | most recent GAM year | Total HIV spending by source (Table B2); progression and death rates (Tables A1-A2); scenario outcomes (Table C2) | US$, rates, counts | 2d, 2f, 2i |
| UNAIDS AIDSinfo 2026 estimates | UNAIDS | 2025 | PLHIV, ART and PMTCT coverage, women needing ARV, new infections, AIDS deaths, suppressed viral load, people on ART | counts | 2d, 2e, 2f, 2i |
| VIMC estimates (Toor et al. 2021) | Vaccine Impact Modelling Consortium | vaccination years 2015-2019; calendar years 2000-2019 | Deaths averted by year of vaccination, calendar year and birth cohort, 10 pathogens, 112 countries | counts | 2f |
| WUENIC 2025 revision | WHO / UNICEF | 2015-2019, 2025 | Coverage by antigen; DTP3 and MCV1 model inputs | % | 2e, 2f |
| World Population Prospects 2024 | UN DESA | 2015-2030 | Surviving infants, births (projected 2026-2030 for the immunization need), under-5 mortality, population | thousands (x 1,000); per 1,000 | 2e, 2f |
| KFF America First MOU tracker; team MOU sheet | KFF; project team | 2026 | Signed MOUs; yearly US funding schedules | nominal US$ | 2b |
| OECD preliminary ODA 2025 | OECD | April 2026 | Change in total aid by donor | % | 2b |

---

## 5. Evidence Vs Assumption Table

| Parameter | Central (range), unit | Evidence or Labelled Assumption | Source or reason |
|---|---|---|---|
| `asd_share` above-site programme share | 0.45 (0.30-0.55) | Evidence | KFF 2025 (Gaba, Razavi, Kates & Nandakumar): non-service delivery 47% of PEPFAR spending 2018-23 |
| `uc_art_mult` ART cost multiplier (country costs in `art_cost_full`) | 1 (0.68-1.38) | Evidence | GHCC repository; Rosen 2021; ten Brink 2025 Table B2; GHED; UNAIDS; floor Rosen Malawi; range from the spread of cost studies |
| `uc_scale_elast` income elasticity of staff costs | 0.4 (0.25-0.6) | Labelled Assumption | fallback only when no country study exists |
| `uc_pmtct` | 250 (150-450) US$ per woman-year | Evidence | Health Policy and Planning 2016;31(8):1133 review |
| `cpia_ref` cost per HIV infection averted | 5,000 (2,500-12,000) US$ | Labelled Assumption | no single cost per infection averted across prevention mixes; affects infections only |
| `uc_ovc` | 100 (60-160) US$ per child-year | Labelled Assumption | no mortality effect modelled |
| `uc_tb_mult` TB cost multiplier (country costs in `tb_ds_cost`, `tb_dr_cost`) | 1 (0.78-1.60) | Evidence | Value TB; GHCC (Vassall 2017, Cox 2015); Laurence, Griffiths & Vassall 2015 |
| `uc_itn` | 2.2 (1.4-3.5) US$ per person-year of net use | Evidence | GiveWell ITN analysis (US$4-6 per net, 1.8 people, about 2 years, 63% used) |
| `uc_irs` | 8.5 (6-10) US$ per person-year | Evidence | PMI Africa IRS project, Mali 2012-14 |
| `uc_mal_cm` | 14 (4-47) US$ per case | Evidence | White et al. 2011, Malaria Journal 10:337 |
| `uc_imm` | 87 (38-104) US$ per child | Evidence | Lydon et al. 2014; MSF The Right Shot 2015; Brenzel 2015 |
| `art_hazard_mult` (hazards 1.3-6.0%, 6.8-7.3%) | 1 (0.65-1.7) | Evidence | CD4 cohort calculation from Optima Tables A1-A2 and ZIMPHIA 2020 Table 10.1 |
| `art_transmission` (legacy only) | 0.04 (0.02-0.08) | Superseded | used only when `hiv_legacy_art_params` = 1 |
| `art_transmission_mult` (country UNAIDS rates) | 1 (0.71-1.38) | Evidence | UNAIDS AIDSinfo 2026 estimates |
| `hiv_new_inf_unsup_years` | 4 (2.5-5.5) years | Labelled Assumption | from the 2.6-year median time to diagnosis (Giguere 2021) plus linkage; no direct measure of onward transmission duration |
| `pmtct_vt_reduction` | 0.25 (0.10-0.40) | Evidence | WHO: 15-45% transmission without, under 5% with intervention |
| `pmtct_infant_mort` | 0.45 (0.35-0.525) | Evidence | Newell et al. 2004, Lancet |
| `tb_cfr_untreated_neg`, `tb_cfr_treated_neg` | 0.43 (0.28-0.53); 0.03 (0-0.07) | Evidence | WHO TB burden estimation methods, Table 4 |
| `tb_cfr_untreated_pos`, `tb_cfr_untreated_pos_art`, `tb_cfr_treated_pos` | 0.78 (0.65-0.94); 0.49 (0.31-0.70); 0.06 (0.03-0.09) | Evidence | WHO TB burden methods, Table 5, p. 28 |
| `tb_dr_dcfr` | 0.45 (0.30-0.60) | Labelled Assumption | about 60% untreated vs 15% treated fatality; no single source |
| `tb_secondary` | 0.4 (0.2-0.8) cases per untreated patient-year | Evidence (derived) | Styblo 1991 (10 infections a year); WHO (60% smear-positive); Vynnycky & Fine 1997 (5-10% progress) |
| `mal_vc_eff` | 0.55 (0.40-0.61) | Evidence | Eisele, Larsen & Steketee 2010 (Lives Saved Tool) |
| `mal_cm_eff` | 0.97 (0.82-0.99) | Evidence | Thwing, Eisele & Steketee 2011 |
| `mal_itn_default_use`, `mal_cm_default_cov` | 0.50 (0.40-0.60); 0.40 (0.30-0.50) | Labelled Assumption | used only where no MAP or survey value exists (no malaria country needs the treatment default) |
| `mal_adult_effect_frac` | 0.5 (0-1) | Labelled Assumption | no published adult effect size |
| `mal_u5_share_afr`, `_amr`, `_emr`, `_sea`, `_wpr` | 0.75, 0.20, 0.364, 0.25, 0.40 (plus or minus 0.05) | Evidence (central); Assumption (range) | World Malaria Report 2025 regional statements |
| `mal_resurgence` | 0.10 (0-0.25) a year | Labelled Assumption | direction from Cohen et al. 2012; speed varies widely |
| `imm_deaths_per_child_ref`, `imm_u5_share` (legacy only) | 0.020; 0.65 | Superseded | used only when `imm_legacy_u5mr_scaling` = 1 |
| `imm_dpc_mult` (country values in `imm_dpc*`) | 1 (0.56-1.64) | Evidence | VIMC estimates (Toor et al. 2021); WUENIC 2025; WPP 2024; Toor Table 3 gate |
| `hss_kappa` share of testing-and-care money counted as lost ART | 0.5 (0.25-0.9) | Labelled Assumption | the money funds diagnosis and retention, a flow, not a stock of patients; no cost per initiation exists |
| `hss_service_share` systems money converted to services | 0 (constant) | Labelled Assumption (structural) | above-site money is already in the unit-cost markup; 0.5 is a sensitivity case |
| `continuity` | 0.15 (0-0.30) | Labelled Assumption | no study measures the share of patients who keep a service after its donor funding is withdrawn |
| `hiv_inf_death_untreated`, `hiv_survival_median` | 0.85 (0.70-0.95); 10.5 (8.6-12.5) years | Evidence | Todd et al. 2007 (ALPHA network), CASCADE |
| `hiv_inf_death_treated` | 0.10 (0.05-0.20) | Labelled Assumption | near-normal life expectancy on ART, allowing for late diagnosis |
| `art_reengage` | 0.35 (0.17-0.68) a year | Evidence (indirect) | Kranzer 2010; Kaplan 2017; Mody 2026 (disengagement while services ran, not a programme restart) |
| Fiscal-space debt-stress thresholds | 10% of revenue (5-15); 40-point span (30-50); floor 0.25 (0.15-0.50) | Labelled Assumption | no study measures where interest costs stop a health budget growing (L-29); constants, not drawn |
| Cut paths (Linear, Front-loaded, Back-loaded, S-curve shapes) | | Scenario definitions | user choices, not estimates |
| Ramp-up (LAG) shares: PMTCT 60%, TB 70%, bednets 50%, spraying 80% in year 1 | | Labelled Assumption | how fast the full effect appears |

---

## 6. Known Limitations And Next Steps

Direction: the way the headline would most likely move if the item were resolved (Higher, Lower, Unclear).

- Continuity 15% is an assumption with no direct measurement; the sensitivity value is 30%. Direction: Lower if
  continuity is higher (L-14 / IMP-16).
- Testing-and-care money counted as lost ART at 50% is a stock proxy for a flow of diagnoses; the flow version is
  blocked for lack of a cost per initiation. Direction: Unclear (L-27 / IMP-02c).
- Systems money buys no service in the model; the earlier rule (50%) is a sensitivity case. Direction: Higher if
  systems money does cut services (L-05).
- HIV deaths are 0.39 and infections 0.36 of Optima's PEPFAR-discontinued excess; the gap is in the money-to-people
  conversion (full-cost equivalents, continuity, the 23% Global Fund cut), not transmission. Direction: Higher
  (L-41 / L-49).
- The ART cost level (median US$216, 13 countries at the US$191 floor) would be settled by PEPFAR Expenditure
  Analysis cost per patient. Direction: Unclear (L-50 / DR-01).
- The vaccine unit is a full-schedule child at US$87 while donor money buys specific antigens; no cost per antigen.
  Direction: Unclear (L-18 / IMP-15).
- Vaccine deaths exclude DTP, polio and BCG for lack of a per-child value. Direction: Higher (L-42).
- Lifetime vaccine deaths after 2035 (adult hepatitis B, meningitis A and yellow fever at age 5 and over) are not
  counted. Direction: Higher for committed deaths.
- Malaria treatment uses the same intervention-specific donor share rule as nets; the alternative (GHED all-source
  share) would give 84,075 instead of 123,822 treatment deaths. Direction: Lower under the alternative (A3).
- The aid baseline is 2021 to 2023; cuts already in force in 2025 are not netted out and coverage is 2024 to 2025.
  Direction: Lower for US scenarios' Aid at Risk (L-06 / IMP-06).
- MOU co-financing commitments are not modelled. Direction: Lower for the MOU preset (L-08 / IMP-08).
- The OECD preset applies total-aid cuts to health aid. Direction: Unclear (L-28 / IMP-14).
- 70 countries receive 71.5% of country-coded aid; Myanmar, Sudan, Afghanistan, Chad, Yemen and Ukraine are missing.
  Direction: Higher for the all-country total (L-03 / IMP-23).
- Bednet use defaults to 50% where no MAP or recent survey exists; IRS household share is applied to people; IRS is
  implied from donor spending where MAP shows none; MAP and WHO case counts differ (Pakistan). Direction: Unclear
  (L-07, L-21, L-22, L-23).
- People living with HIV and TB and malaria incidence are held at the latest year through 2030 (no projection on
  disk); births now follow WPP projections (Batch 7). Direction: Higher where need grows (L-24 / IMP-17, partly done).
- The Lancet rate-ratio method on the Validation page still uses a GBD-2019 HIV death share. Direction: Validation
  page only (L-11).
- TB case fatality is placed in the year of loss and secondary cases arrive within two years, both labelled timing
  assumptions (Batch 7). Direction: 2026 to 2030 TB deaths somewhat high, 2031 to 2035 somewhat low (L-15).
- Fiscal capacity is one strong year's growth held flat (a cumulative version is a known alternative, not
  implemented); the debt-stress thresholds are labelled assumptions with ranges. Direction: Government Response
  options only (L-29, labelling half closed in Batch 7).
- The PMTCT cost review figures could not be verified. Direction: Unclear (L-32).
- Sections 1 to 3 per-country files cannot be rebuilt from scripts in the repository. Direction: none (L-38).
- India's TB systems and unspecified money follows its own line mix toward drug-resistant TB. Direction: Lower for
  India (L-39).
- The Gavi -15% default is an estimate. Direction: Global Fund & Gavi Shortfalls preset only (L-09).
- TB deaths rose 91% in Batch 3+4 when course costs fell to facility-level values; the model's cost is 0.47 of
  national programme budgets per notified patient at the median. Direction: Lower if budget-level costs were used.

---

**Closed in Batch 7 (15 October 2026).** L-43, the split of unspecified aid, is done with a stated gap: 34 of the 210
country-disease lines use a WHO-region median because the country has no Global Fund grant for that disease, and the
lines where donor money would buy more than the donor-funded pool are listed in `audit/logic_review/batch7_evidence.md`.
The headline chain in the changelog was re-run at each batch's own commit and corrected (before Batch 1: 1,969,304;
Batch 2 raised HIV deaths by 9%). L-17: DTP3 coverage now comes from WUENIC 2025 directly (30 countries moved by
more than 2 points; vaccine deaths +0.2%). IMP-24: the HIV inputs (people living with HIV, ART and PMTCT coverage,
HIV-positive pregnancies, new infections) are read from the UNAIDS 2026 file directly, with WHO GHO as the fallback;
the only HIV series still taken from the World Bank mirror is adult prevalence, used in a fallback and in the
Validation-page regressions. L-11: the Lancet rate-ratio comparison on the Validation page now starts from UNAIDS
2025 AIDS-related deaths instead of a GBD-2019 share of all deaths (Kenya's baseline 70,569 to 19,434 a year). L-31: the interest series is labelled with its IMF WEO release (October
2026); the other macro series carry no recorded vintage and are labelled as such. L-34: interest as a share of revenue
now has one primary definition, IMF WEO net interest, available for every country; the World Bank gross-interest
series is a flagged fallback that no country currently needs. L-35: MOU amounts stay nominal by default and are
labelled so on the dashboard; a `mou_deflate` switch (2% a year US$ inflation, labelled assumption, range 1-4%)
expresses them in 2023 US$, which raises the America First MOUs preset from 364,586 to 416,307 deaths. Gradual
Budget Increase: a `budget_growth` setting (default 0, the 2023 budget held flat) lets the budget grow with WEO
nominal GDP; at the full rate the preset falls from 534,944 to 419,439 deaths and Kenya's break-even from 1.12 to
1.06 points a year. L-09: the Gavi -15% default is labelled as our estimate, applying to its preset only (value
unchanged). L-24 (births): the immunization need follows WPP 2024 projected births for each year 2026 to 2030
(vaccine deaths +0.2%); people living with HIV and TB and malaria incidence stay at the latest year because no
projection is on disk. L-15: the TB timing rules are labelled as assumptions on the Methods page.

---

## 7. Likely Questions And Answers

**Why are there more deaths than people losing coverage in some places?** There are not. Every service's five-year
deaths are checked against the people affected (for ART, the peak number off treatment, since mostly the same people
stay off); the automated checks fail if deaths exceed people. What can look like it: TB spread adds secondary cases
to the untreated patients' deaths, and HIV adds deaths among people newly infected by those off ART, so a line's
deaths can exceed its own patients' deaths while staying below its people affected.

**Why is your HIV estimate lower than Optima's?** Optima's scenario removes all PEPFAR support for six years with zero
new ART initiations and includes a 24% cut by the five largest donors; the model cuts US direct aid and 23% of its
Global Fund pledge for five years, keeps 15% continuity and converts lost money at the full cost per patient-year. Over
the 15 overlapping countries the model gives 0.39 of Optima's excess deaths and 0.36 of its infections; Kenya,
Eswatini and the Dominican Republic agree within the band.

**Why not use PEPFAR's 20.6 million people at supported sites?** That count includes everyone at a PEPFAR-supported
site, including people whose drugs the government or the Global Fund buys. Applying a death risk to it would credit
the lost money with people it does not pay for. The model counts the people the lost money actually funds.

**What are full-cost equivalents, in one sentence?** Lost ART money divided by the full cost of treating one person
for a year, each unit treated as a person who stops ART.

**Why do deaths continue after 2030?** People still off ART, adults infected in 2026 to 2035, children who missed
vaccines late in the period and secondary TB cases all die after the cut ends; the model follows them to 2035 so that
a late cut is not flattered, and reports them separately because they depend on the assumed return-to-care rate.

**Why are vaccine deaths a floor?** They count only hepatitis B, Hib, pneumococcal, rotavirus, measles, rubella,
yellow fever and meningitis A; diphtheria, tetanus, pertussis, polio and BCG have no citable deaths-averted-per-child
value and are left out, and deaths after 2035 are not counted.

**Why do TB deaths depend so much on cost per course?** People untreated = lost money / cost per course, and each
untreated patient carries a 40-point difference in case fatality; halving the cost doubles the patients and the
deaths. With the older income-group costs TB deaths would be 265,626 instead of 463,973.

**How do you know your malaria numbers are right?** Nobody can know that; we check them. Excess malaria deaths are a
median 6% of the World Malaria Report's current deaths (at most 28%, Zambia); coverage, cases and deaths come from MAP
and WHO; the effect sizes are the Lives Saved Tool's; and the intervention-specific cap means donors are credited only
with the people their money buys.

**What does the range mean? Is it a confidence interval?** It is the 2.5th to 97.5th percentile of 400 runs with the
parameters drawn from their ranges. It is not a confidence interval: uncertainty in the data and in the model's
structure is larger and not included.

**What happens if governments replace some of the money?** Under US Bilateral Exit + Multilateral Withdrawals, all
countries: No Government Replacement 1,927,405 deaths; Replace a Set Share at 25% (pro-rata) 1,577,269 (18% fewer);
the same with the hypothetical best case (triage) 970,184 (50% fewer); As Much as Fiscal Space Allows 1,199,160 (38%
fewer); Gradual Budget Increase (Steady, 0.5 points a year) 535,501 (72% fewer).

**Why use 2021-2023 aid instead of 2025?** IHME has no recipient-country detail after 2023; 2021 to 2023 is the latest
three-year window with the breakdown the model needs. The IHME 2025 Preliminary Estimates preset applies IHME's 2025
global ratios to it.

**How did you avoid double counting money?** IHME's `elim_ch = 1` rows (transfers recorded twice) are dropped before
summing; donor and channel cuts combine multiplicatively; systems money is not converted into patients because the
unit costs already include above-site costs; the splits of unspecified money are checked to conserve the total.

**Which numbers are assumptions rather than evidence?** Continuity (15%), the share of testing-and-care money counted
as lost ART (50%), the cost per HIV infection averted, the OVC cost, the drug-resistant TB deaths averted per patient,
the effect of malaria interventions at age 5 and over (50%), the malaria rebound (10% a year), the default net use
where no survey exists, the time newly infected people stay unsuppressed (4 years), the chance of dying of HIV when
treated (10%), the fiscal-space thresholds and the ramp-up shares. Section 5 lists all of them.

**How was the model checked?** 59 automated invariants over 76,501 checks (0 failures), 357 tests, an independent
reproduction from the written specification (1,980 of 1,980 cells within 0.5%) and validation against Optima,
UNAIDS, WHO TB and malaria data and VIMC with a stated acceptance band.

**What would change your headline the most?** The ART death hazard multiplier, continuity, the above-site share and
the share of testing-and-care money counted as lost ART (the four largest one-at-a-time swings in the logic review's
sensitivity analysis, each moving the headline by 10 to 24%), and structurally the full-cost conversion itself:
Optima's coverage-drop approach gives 2.6 times the model's HIV deaths over the overlapping countries.

**Does the headline include deaths after 2030?** No. Extra Deaths Over 5 Years counts 2026 to 2030 only; Further
Deaths, 2031-2035 (Assumption-Driven) is shown separately.

**Why does the IHME 2025 preset give so few vaccine deaths?** IHME's 2025 preliminary data show Gavi-channel money
little changed, so that preset cuts almost no immunization aid (22,489 vaccine deaths against 187,945 under the US
exit).

---

## 8. Glossary

- **Above-Site Costs**: programme costs beyond the clinic (management, monitoring, supply chain); 45% of spending.
- **Aid At Risk (per Year)**: the yearly aid the scenario removes, before any government replacement.
- **ART**: antiretroviral therapy, the drugs that suppress HIV.
- **Baseline Aid**: the 2021 to 2023 average of donor health aid for the four disease areas.
- **Cap Rule / Donor-Funded Pool**: the people whose service donor money actually pays for; losses cannot exceed it.
- **CD4 Count**: a measure of immune strength; it falls without ART and drives the death risk.
- **Channel**: the organisation that delivers aid (bilateral agency, Global Fund, Gavi, NGO).
- **Committed Deaths / Further Deaths, 2031-2035**: deaths set in motion by the 2026 to 2030 cuts that fall after 2030.
- **Continuity**: the share of people who keep a service after its donor funding ends.
- **Coverage**: the share of people in need who receive a service.
- **Cut Path**: how fast the scenario's cut arrives over 2026 to 2030.
- **DAH**: Development Assistance for Health, IHME's measure of donor health aid.
- **Direct Channel**: bilateral agencies, NGOs and foundations, as opposed to multilateral funds.
- **Donor Share**: the share of a service's users whose service donors fund, measured from spending data.
- **Effective Loss**: a service line's lost money after unspecified money is split and systems money removed.
- **Elim_ch**: IHME's flag for a transfer recorded twice; those rows are dropped.
- **Fiscal Space**: the extra money a government health budget could find in a year.
- **Full-Cost Equivalents**: lost ART money divided by the full cost per patient-year.
- **Hazard**: the excess death rate per person-year.
- **IHME**: Institute for Health Metrics and Evaluation, University of Washington.
- **Lives Saved Tool (LiST)**: the Johns Hopkins model whose malaria effect sizes are used.
- **MAP**: Malaria Atlas Project, the source of malaria coverage and case estimates.
- **Monte Carlo Draws**: repeated model runs with parameters sampled from their ranges (400 here).
- **MOU**: Memorandum of Understanding between the US and a partner government on future US funding.
- **Multilateral Channel**: pooled funds and UN agencies (Global Fund, Gavi, WHO, UNICEF).
- **Net Aid Lost**: Aid At Risk minus what the government replaces.
- **Percentile Range**: the 2.5th to 97.5th percentile of the draws, shown as Range Across Parameter Values.
- **PMTCT**: prevention of mother-to-child transmission of HIV.
- **Programme Area**: IHME's category for what aid funded (for example HIV treatment).
- **Q5 / U5MR**: the probability of dying before age 5 (under-5 mortality), per 1,000 live births.
- **Rifampicin-Resistant (RR) TB**: TB needing second-line drugs; the model's drug-resistant line.
- **Sudden (default)**: the full cut in force from 2026.
- **Triangular Distribution**: a probability distribution peaked at the central value with straight sides to the low and high.
- **Unit Cost / Cost per Person**: what donors spend per person served.
- **Unspecified Money**: aid whose programme area IHME could not identify; split by Global Fund module shares.
- **VIMC**: Vaccine Impact Modelling Consortium, whose deaths-averted estimates drive the vaccine pathway.
- **WUENIC**: WHO/UNICEF Estimates of National Immunization Coverage.
