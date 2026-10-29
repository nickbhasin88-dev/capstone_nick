# Audit of every number the dashboard displays

Branch `real-modeling-check`, commit `4cbb7ff` (8 October 2026). Audit run 12 October 2026. No model or app code was
changed. Everything in this folder can be re-run from the repo root:

| File | What it is |
|---|---|
| `inventory.csv` (`make_inventory.py`) | Step 1: 113 displayed numbers (or families of numbers drawn by one piece of code), with the function that draws them, the function that computes them, units, time basis and currency |
| `METHOD.md` | The method written out in plain language from the code; the only description given to the independent recalculation |
| `recompute.py`, `recompute_results.csv`, `recompute_notes.md` | Step 3: independent recalculation, written by a separate agent that never opened the model code |
| `compare_recompute.py`, `recompute_compare.csv` | Step 3: the independent values next to the dashboard's own functions |
| `checks.py`, `checks_results.csv`, `checks_summary.csv/.md` | Step 4: 38,505 automated checks, every country x every preset x every government response |
| `archive/analysis.py` (runs at commit 4cbb7ff; see `archive/README.md`), `fallbacks.csv`, `outliers.csv`, `sensitivity.csv`, `analysis.json` | Steps 2, 5 and 6 evidence: fallback counts, outlier metrics, parameter sensitivity, card and path tests, benchmarks |

---

## 1. Summary

**Verdict.** The arithmetic is right, but some inputs and a few scenario and display choices are not. The code does
exactly what its method says:
- An independent recalculation from a plain-language description, by an agent that never saw the model code,
  reproduced all 1,864 compared values to within 0.5%. Every one matched to rounding.
- The automated checks found no impossible values: no NaN, no negative deaths, no coverage outside 0-100%, no
  replacement above fiscal capacity.
- Deaths never fall as the cut grows, and a zero cut gives zero.
- The precomputed All Countries files match a fresh run.

The problems are upstream of the arithmetic and in a few labels:
- the aid baseline itself;
- how the MOU scenario is applied over time;
- an outdated malaria trend;
- one scenario premise (Gavi);
- the per-US$1M cards;
- several labels that claim more than the math does.

**Issues by severity:** Critical 4, Major 7, Minor 7, Cosmetic 7 (25 in total, full log in section 5). **Fixed: I-01** (see `I-01.md`); **I-02, I-03, I-08** (see `I-02_I-03_I-08.md`); **I-05** (see `I-05.md`); **I-13, I-14, I-15, I-16** (commit 11dae37; see `I-13_I-14_I-15_I-16.md`); **I-12, I-18, I-19, I-20, I-21, I-22, I-24** (wording, commit ea998aa; see `cosmetic_fixes.md`).

**The five that matter most**

1. **I-01 (Fixed; cause: IHME's elim_ch double-counting flag was not applied): The model's aid baseline was about 7% larger than IHME's own totals.**
   - It is more than 5% larger in 50 of the 70 countries: Somalia 1.87x, South Sudan 1.30x, Angola 1.19x.
   - Immunization is the worst bucket at +15%.
   - Aid at risk, people losing services and deaths all scale with it. Kenya is about +6%, Nigeria +7%.
2. **I-02 (Fixed): The "MOU Schedule" funding path badly understated the MOU schedules.**
   - Each year's cut is rescaled so that the deepest year equals the 2028 cut.
   - For Kenya that gives 7.6K deaths over 5 years instead of 21.8K (2.9x fewer).
   - 14 of the 16 MOU countries are affected.
3. **I-03 (Fixed): The "America First MOUs" preset held one year's cut (2028) for all five years.**
   - It is described as following "the 2026-2030 MOU schedules", which it does not.
   - Ethiopia gets an 8% cut although its schedule averages 24% and reaches 49% in 2030.
4. **I-05 (Fixed): "New HIV Infections" showed a different statistic from every other number.**
   - It is the median of the 400 draws, while every death figure is the central run.
   - The two differ by up to 10% (Nigeria +10%, Kenya +8%).
5. **I-06 and I-07: two scenario premises are out of date or not supported by their source.**
   - I-06: the malaria death trend is fitted to 2010-2019, but malaria deaths have been flat or rising since 2015.
     Applying it understates malaria deaths by 12-17% in Ethiopia, Burkina Faso and Uganda.
   - I-07: the "Gavi -24%" cut is the 2026-2030 pledges against Gavi's target. The pledges (over US$9B) are
     actually above the previous cycle's US$8.8B.

---

## 2. Method trace: from raw data to the screen

### 2.1 Data sources

| Publisher | File in repo | Year(s) used | Units | Feeds |
|---|---|---|---|---|
| IHME, Development Assistance for Health 1990-2026 | raw file **not in repo** (gitignored) -> `model_data/dah_lines.csv`, `ihme_trend.csv`; `country_data/<Country>.csv` (built by a script not in the repo) | model baseline: average of 2021-2023; IHME 2025 preliminary for one preset; Section 2: 2015-2023 | thousands of constant 2023 US$ (x 1,000 in the model) | Model money (Section 4), Section 2 charts |
| IHME, Global Health Spending 1995-2023 | `datasets/IHME_HEALTH_SPENDING_...CSV` -> `spending_data/`, `country_inputs.csv` (ghes_2023, growth) | 2015-2023 (charts); 2023 (GHES); 2001-2023 growth | thousands of constant 2023 US$ | Section 1; fiscal capacity; fiscal panel |
| IHME, GDP (FGH 2026) | `datasets/IHME_GDP_...CSV` | 2024 GDP per person; history for constant-dollar GDP | constant 2023 US$ | ART staff-cost scaling; revenue denominator; header GDP years other than 2023 |
| IMF World Economic Outlook | `macro_data/` | header: latest actual (2024); Section 3: selected year (default latest with both mixes); government spending 2023 for the budget path | % of GDP; GDP US$ bn (nominal and constant 2023) | Header, Section 3 totals, gradual budget increase |
| IMF World Revenue Longitudinal Data | `revenue_data/` | selected year | % of GDP | Section 3 revenue mix |
| IMF Government Finance Statistics (COFOG) | `cofog_all/` | selected year | % of outlays | Section 3 spending mix |
| WHO Global Health Observatory (UNAIDS 2025 round; World Malaria Report) | `ext_data/gho/` via `who_inputs.py` | PLHIV, ART, PMTCT 2025; malaria deaths, cases, incidence 2024; ITN use 2024 | counts; % | Need and coverage (HIV, malaria), malaria baseline deaths and trend |
| World Bank WDI (Gapminder mirror) | `ext_data/wdi/` | mostly 2024; malaria surveys 2005+ (treatment median 2017); fiscal 2015-2024 | % ; counts | TB coverage, DTP3, U5MR, births, population, HIV incidence, interest/revenue, health share, fallbacks |
| Gapminder Systema Globalis (WHO, MCEE) | `ext_data/sg/` | TB incidence and deaths 2024; child deaths 2021 | counts | TB need, TB-HIV share; Validation regressions |
| Team MOU / co-financing sheet | `datasets/co-financing_MOU.xlsx` -> `country_inputs.csv` mou_* | US reference 2021-25; schedules 2026-2030 | **nominal** US$ per year | America First MOUs preset, MOU path, header status |
| Published studies | `model_params.csv`, `unit_cost_reference.csv` | various, inflated to 2023 with US CPI-U | per unit | Unit costs and effect sizes |

**Year mismatches.**
- Aid is the 2021-2023 average. It is applied to coverage measured in 2024-2025 and to people in need in 2024-2025.
  It is set against government health spending for 2023 and GDP for 2024. All of this is assumed to hold in
  2026-2030, with no projection between 2024 and 2026.
- This matters most where aid has already fallen since 2023: the model then removes aid that may already be gone.
  The IHME 2025 preset partly addresses this.
- Malaria treatment coverage comes from household surveys, median year 2017 (2006-2021), because WHO has no modelled
  series. Nine non-African countries use under-5 bednet surveys from 2007-2021 (`fallbacks.csv`).

**Currency.**
- Model money is in constant 2023 US$ throughout.
- Unit costs are inflated to 2023 with US CPI-U.
- Section 3 dollars = WEO share of GDP x GDP in constant 2023 US$. A ratio times real GDP is consistent, and the check
  that constant and nominal GDP are equal in 2023 passed for all 71 countries.
- The one nominal number on screen is the MOU caption's "US$X million a year before the cut", from the team sheet
  (I-21).

**Level of government.**
- WEO totals are general government.
- The revenue mix is central government for 45 of 71 countries; COFOG is central or budgetary government for 30 of
  46 (I-10).
- IHME government health spending covers all levels.

### 2.2 Stage 1: money (what aid is lost)

1. **IHME DAH to `dah_lines.csv`** (`prepare_model.py:253-274`).
   - For each recipient x source x channel x year, sum the program-area columns that map to each service line
     (`prepare_model.py:92-109`).
   - Average 2021-2023, then multiply by 1,000 to get US$.
   - Sources are grouped into 14 donor groups and channels into 15 channel groups.
   - **Finding:** the per-country bucket sums are larger than IHME's own bucket totals in `country_data` for the same
     years (I-01). `country_data` itself agrees with IHME's spending database to within 1.2% for 2023.
2. **Cut per row** (`health_model.py:142-157`): cut = 1 - (1 - donor cut)(1 - channel cut).
   - A (donor, channel) pair overrides the donor cut. It is applied once, then multiplied by the path scale.
   - Check `cut_formula_matches_documented_scenario`: an independent implementation of every preset matched every row,
     1,960 of 1,960 runs.
3. **Scenario percentages against their sources**

   | Preset | Values | Verdict |
   |---|---|---|
   | Full US exit | US direct 100%; US via WHO, Gavi, UNFPA 100%; US via Global Fund 23% | 23% = 1 - 4.6/6.0 (US pledge, 8th vs 7th replenishment): verified (Aidspan). Gavi stop (June 2025) and WHO exit verified. Other US multilateral channels (UNICEF, UNAIDS, development banks) are untouched: a choice, not documented as such |
   | OECD-reported 2025 cuts | US 57%, DE 17.4%, FR 10.9%, UK 10.8%, JP 5.6% | Verified against OECD preliminary 2025 data (US -56.9%; others -17%, -11%, -11%, -6%). Applying total-ODA cuts to health is an assumption |
   | Global Fund & Gavi shortfalls | GF -28%, Gavi -24% | GF: 1 - 11.34/15.7 = 27.8%, verified. **Gavi: over US$9B pledged against an US$11.9B target, but US$8.8B was raised for 2021-25, so this is a shortfall against target, not a cut (I-07)** |
   | America First MOUs | US direct cut = 1 - US 2028 / 2021-25 reference (team sheet), clipped to [-0.5, 1]; others 36% (rounded average) | Arithmetic matches the sheet. The **2028 value is held for all five years (I-03)** |
   | IHME 2025 preliminary | 1 - IHME 2025 / 2021-23, by source x channel x bucket | 467 of 572 cells (baseline under US$20M) use the donor x bucket ratio; 39 cells clipped at 1.5x |
   | Combined retreat | Full US exit + OECD cuts for other donors | Composition verified |

4. **Effective loss of each service** (`health_model.py:459-476`).
   - Money with no reported purpose ("unspecified") is spread over the bucket's direct lines by their baseline mix.
   - kappa = 50% (*assumption*) of systems money (labs, staff, monitoring) counts as lost services; the other 50% is
     "non-service".
   - Check `unspec_and_kappa_conserve_money`: direct lines + (1 - kappa) x systems = bucket gross, 1,960 of 1,960.
     Nothing is double counted.
5. **Aid at risk** = sum over all 16 lines of max(loss, 0) (`health_model.py:482`).
   - Per year, by construction: check `aid_at_risk_is_per_year_not_5yr_total`, 1,960 of 1,960.
   - With a phased path, the hero and The Numbers show the 2026-2030 average.

### 2.3 Stage 2: government response

- **Capacity per year** = GHES 2023 x max(0, p75 growth - max(median growth, 0)) x debt-stress, where debt-stress =
  clip(1 - (interest % of revenue - 10)/40, 0.25, 1) (`health_model.py:184-203`).
  - Growth is the real year-on-year change in IHME GHES, 2001-2023 (`prepare_model.py:326-332`).
  - Interest/revenue is missing for 18 countries; they silently get a stress factor of 1. 30 countries are below 1;
    none are at the 0.25 floor. All 70 have GHES and positive capacity.
- **Responses**:
  - No backfill = 0.
  - Replace a set share = min(theta x loss, capacity).
  - As much as fiscal space allows = min(loss, capacity).
  - Gradual = extra percentage points x IMF 2023 government spending.
  - Replacement is never above the loss. Check `replaced_le_fiscal_capacity`: 980 of 980.
- **Allocation**: pro-rata over positive service losses and non-service systems money. Lives-first refills services in
  order of deaths per dollar (`health_model.py:512-532`).
- **"No backfill is the historical norm."**
  - The two-way fixed-effects estimate is -0.19 per $1 (95% CI -0.45 to +0.07), 97 countries.
  - The years are **2002-2023** (the UI says 2001-2023, I-18). The claim is consistent with the estimate.

### 2.4 Stage 3: coverage (who loses a service)

- **People losing a service** = net loss / cost, times (1 - continuity 15%, *assumption*).
  - Where donor money buys more than the people covered: covered x net loss / effective baseline.
  - The result is clipped to [-(1 - coverage) x need, coverage x need] (`health_model.py:318-326, 555-588`).
  - Proportional scaling applies to 204 country-lines under Full US exit (PMTCT 52, malaria treatment 51, ART 29,
    TB 24 + 24, bednets 16, vaccines 7, spraying 1). No line hits the cap, and no coverage is driven to 0%.
- **Need and coverage**: METHOD.md section 3. The fallbacks below are counted over the 70 modelled countries
  (`fallbacks.csv`):

  | Input | Fallback | Countries |
  |---|---|---|
  | PLHIV, ART coverage | derived / WDI where UNAIDS has none | 5 (CIV, GTM, IRQ, JOR, NIC) |
  | PMTCT coverage, HIV+ pregnancies | WDI / births x prevalence x 1.15 | 10 |
  | Malaria deaths and cases | derived (only non-malaria countries) | 7 |
  | Population at risk | 95% / 35% of population | 16 (all with no or very little malaria) |
  | Bednet use | old under-5 survey / default 50% | 9 / 6 |
  | Malaria treatment coverage | default 40% (incidence < 50 per 1,000 or no survey) | 17 of 46 malaria countries |
  | ART unit cost | country study (Rosen et al.) vs default | 5 study, 65 default |
  | TB unit cost | income group (World Bank list, none missing) | 70 |
  | HIV incidence (prevention cost) | clipped to 0.05-10 per 1,000 / missing -> 0.3 | 11 / 5 |
  | Vaccine death scale | U5MR/50 clipped at 0.3 | 7 |

- **Unit costs** are inside their parameter ranges for all 71 countries (`unit_costs_inside_parameter_range`).
  - The ART line (`hiv_art`) is funded by IHME's treatment + care + counselling-and-testing columns. Care and testing
    are 32% of that money overall (median 41% by country: Kenya 41%, Nigeria 38%).
  - All of it is turned into ART patient-years at the ART cost (I-09).
- **Missing values**:
  - A missing coverage value removes the cap and the scaling for that line (it falls back to net loss / cost).
  - A missing need value makes coverage "Not Modelled".
  - Missing malaria deaths give 0 malaria deaths; missing TB-HIV share gives 0 (no country affected); missing
    interest gives stress 1.
  - In display code, `care_breakdown` fills missing units with 0. `fillna(0)` in `prepare_model.py` (aid columns,
    child health aid, US aid) treats a missing IHME cell as zero aid, which is IHME's own convention.

### 2.5 Stage 4: lives

Formulas are in METHOD.md section 4. Parameters (central, with their status in `model_params.csv`):
- *sourced*: ART hazard (calibrated), TB case fatality (WHO), Lives Saved Tool effect sizes, vaccine deaths per child
  (Gavi), PMTCT (WHO AFRO, Newell), TB spread (derived from Styblo and Vynnycky & Fine), HIV survival (Todd 2007).
- *assumption*: continuity, kappa, DR-TB effect, malaria rebound, treated-HIV death risk, re-engagement, PMTCT /
  malaria / OVC / prevention costs, default coverages.

Every value used in code is read from the CSV; nothing is duplicated in code except the hard-coded structural constants
listed in section 6. The cited sources were spot-checked for the scenario figures. The effect sizes (Eisele 2010
55% (49-61%), Thwing 2011, WHO TB tables) match the values quoted in the CSV.

**Mortality trend** (on by default):
- Under-5 mortality and malaria deaths are multiplied by (1 + 2010-2019 trend)^(year - 1), with the trend clipped to
  -8% / +2%.
- For malaria this uses WHO's estimated deaths. **13 of the 46 malaria countries sit at the -8% clip**, while WHO's
  2015-2024 series is flat or rising in many of them (I-06).

**Deaths in 2031-2035**: METHOD.md section 5. The four parts sum to the pill. The independent recalculation matched
each part.

**Uncertainty**:
- Each parameter is drawn from a triangular(low, central, high) distribution, 400 draws, seed 7.
- Ranges are the 2.5th and 97.5th percentiles of the draws. The headline is the central run, which falls inside the
  range for every displayed number (check `range_lo_le_central_le_hi`, 1,960 of 1,960).
- All countries use the same seed, so draw i is the same parameter vector everywhere. That makes country results
  strongly comonotonic.
- The All Countries caption says that summing country percentiles gives a wider range than a joint interval. That is
  true but small: summed 1.60M-3.16M against joint 1.66M-3.05M.
- **Exception: New HIV Infections shows the median of the draws, not the central run (I-05).**

### 2.6 Per-US$1M cards, dose-response and scenario path

- **Cards** (`model_section.py:804-826`). For the main service of each bucket:
  - people = 1,000,000 / cost x (1 - continuity);
  - deaths = deaths per unit over 5 years for a sudden cut x people.
  - They ignore proportional scaling and the coverage cap, and leave out TB spread, malaria rebound and HIV infection
    deaths. They are titled "by bucket" but price only the main service.
  - Compared with the full model's deaths per US$1M of bucket aid lost (10% even cut): HIV cards are 1.19-2.83x
    higher (Honduras 2.83x, Iraq 1.64x, DR Congo 1.60x, South Africa 1.51x), and TB 1.12-1.43x. Malaria is
    0.75-1.31x and immunization 1.00x (`analysis.json`: cards_vs_model) (I-04).
- **Dose-response** (`health_model.py:847-859`): a uniform cut of one bucket, 21 points from 0 to 100%, 100 draws.
  The curve is the central run; the band is the 2.5-97.5 percentile of the draws.
- **This scenario's path** (`model_section.py:107-120`): the scenario scaled from 0 to 1.
- **Extra Deaths Each Year**: the central run by year. It sums to the headline (check `path_chart_sums_to_headline`,
  1,960 of 1,960).

### 2.7 Fiscal-space panel

- **GHES (2023)**, per person and % of GDP: all IHME, constant 2023 US$.
- **Aid lost as % of GHES**: the full-cut loss / GHES 2023. Under a phased path this differs from the hero's average
  (I-13).
- **Aid lost as % of revenue**: loss / (population x IHME GDP per person 2024 x WDI revenue % of GDP, latest; IMF if
  missing).
- **Health share of government spending**: WDI SH.XPD.GHED.GE.ZS (2023). The budget-path panel on the same page uses
  the IMF-based share (I-14).
- **The bars**: aid lost, capacity, replacement (existing response only, so 0 under a gradual budget increase), and
  typical growth = GHES x max(median growth, 0).

### 2.8 Descriptive sections 1-3

- **Section 1**:
  - Stacked IHME spending: aid + government + prepaid private + out-of-pocket equals total to within 1% for all 71
    countries in 2015-2023.
  - The 2023 values equal the raw IHME file for all 71 countries.
  - The pills are 2023 total and aid share.
- **Section 2**:
  - IHME DAH by funder and channel; light shading = NGO, international NGO, US foundation and Gates channels.
  - The 2023 total agrees with Section 1's 2023 aid for all 69 countries with both: ratio 0.988-1.000, median 0.999.
  - The "Where the Aid Is Spent" stacks use the same file.
- **Section 3**:
  - Box sizes come from WEO revenue and expenditure (% of GDP) x constant-2023 GDP; mixes come from WoRLD and COFOG,
    rescaled to the WEO totals.
  - WEO spending - revenue = -net lending to within 0.5 points for all 71 countries; revenue items sum to the file
    total for 71 of 71; COFOG shares sum to 100 for 46 of 46.
  - Level mismatch: I-10.

---

## 3. Results

### 3.1 Independent hand recalculation (Step 3)

**Setup.** A separate agent was given only `METHOD.md`, the data files, `model_params.csv` and
`unit_cost_reference.csv`. It was told not to open any `.py` file. It wrote `recompute.py` and computed every requested
value for Kenya, Nigeria, Honduras, Iraq and Mozambique, under Full US Exit and America First MOUs, with No Backfill
and Replace 25%.

**Result.** **All 1,864 compared values agree with the dashboard's functions to within 0.5%; there are 0 material
differences** (`recompute_compare.csv`). The values cover:
- aid at risk, replaced and net loss;
- every line's effective and net loss, people losing the service, coverage before and after, year-1 and 5-year deaths;
- total deaths, the 2031-2035 parts and new HIV infections (central run);
- all four per-US$1M cards.

Example, Kenya, Full US Exit, No Backfill:

| Value | Independent | Dashboard |
|---|---|---|
| Aid at risk | $290.78M | $290.78M |
| Deaths 2026-2030 | 144,871 | 144,871 |
| Deaths 2031-2035 | 47,858 | 47,858 |
| New HIV infections, central run | 144,123 | 144,123 (the dashboard **shows 155,312**, the median of the draws: I-05) |

The agent's notes (`recompute_notes.md`) list 13 places where the description needed interpreting. Every reading it
chose matched the code. It also flagged things that look odd in the method itself:
- Malaria treatment coverage defaults to 40% even when a survey exists, if incidence is below 50 per 1,000 (Honduras:
  0.2% surveyed). This is intended: where malaria is rare, fever surveys don't measure malaria treatment.
- PMTCT infections have no first-year ramp-up while PMTCT deaths do.
- The orphan-support line takes a share of spread and replacement money but has no outcome.
- Iraq has an MOU reference but no schedule, so it gets the 36% default.

### 3.2 Automated checks (Step 4)

38,505 checks were run on 70 countries x 7 presets x 4 responses, plus the global and data checks. Full table:
`checks_summary.md`; rows: `checks_results.csv`.

| Result | Checks |
|---|---|
| **All pass** | no NaN/inf among displayed values; non-negative values (outside aid-gain cases); deaths >= 0; coverage stored as a fraction; people losing <= people covered; net <= gross <= baseline; replaced <= gross; replaced <= capacity; low <= central <= high; year 1 <= 5 years; path chart = headline; table Total = headline; kappa and spreading conserve money; cut formula = documented scenario; more cut never gives fewer deaths or less net loss (0/25/50/75/100%, 980 runs); zero cut gives zero (980); precomputed CSVs = fresh run (420 country-presets, max difference < 1e-6); dashboard country = All Countries row; no line in two buckets; unit costs in range; percent scales; constant = nominal GDP in 2023; Section 1 sums and raw-file match; Section 2 = Section 1 aid; WEO identity; revenue and COFOG totals |
| **Fail: line baselines = IHME bucket totals** | 70 of 70 differ by more than 0.5% in at least one bucket; 50 differ by more than 5% in total (I-01) |
| **Fail: lines sum to buckets / hero people = table people / coverage after <= before** | 20, 18 and 16 runs, all in the IHME 2025 preset where some aid **rises**. Aid at risk takes max(0, loss) line by line while the bucket chart nets gains; the hero clips negative "people losing" while the table nets them; coverage shows a rise with a double minus sign ("−-6.6 pts") (I-15). One Gambia run is a 0.6-person rounding difference |
| **Fail: Section 3 mix is general government** | the revenue mix is central government for 45 of 71 countries; COFOG for 30 of 46 (I-10) |

---

## 4. Outlier and plausibility review (Step 5) and labels (Step 6)

### 4.1 Rankings (Full US exit, no backfill; `outliers.csv`)

**Extra deaths per 100,000 over 5 years**

| Rank | Top 10 | Bottom 10 |
|---|---|---|
| 1 | Eswatini 1,395 | Iraq 0.4 |
| 2 | Lesotho 1,074 | Egypt 0.6 |
| 3 | Namibia 704 | Libya 0.8 |
| 4 | Zambia 649 | Jordan 1.2 |
| 5 | Mozambique 622 | India 1.6 |
| 6 | Botswana 479 | Mauritius 2.5 |
| 7 | Malawi 446 | Azerbaijan 2.8 |
| 8 | Liberia 325 | Venezuela 2.9 |
| 9 | Uganda 302 | Fiji 3.4 |
| 10 | Tanzania 272 | Bolivia 5.7 |

- **Top, real:** the highest HIV prevalence in the world and PEPFAR-funded treatment; HIV is 57-98% of deaths in the
  top seven (Mozambique 57%, Zambia 78%, Malawi 87%, the rest 92-98%). Liberia is malaria-driven, and its bednet and ART lines use proportional scaling.
- **Bottom, real:** little US health aid and low burden. India's per-capita figure is tiny because of its population;
  its 23,700 deaths are mostly TB.

**Aid lost per death** (5 years of aid / 5-year deaths)
- **Highest:** Jordan $46.6K, São Tomé $37.1K, Jamaica $33.1K, Kyrgyzstan $27.2K, Venezuela $24.1K, Belize $20.9K,
  Haiti $20.8K, Guatemala $20.3K, Mauritius $20.2K, Honduras $20.2K.
  - Real: middle-income countries with higher costs and low mortality per lost service.
  - Haiti and Jamaica: almost all deaths are HIV, and both use proportional scaling of ART.
- **Lowest:** Niger $3.1K, Central African Republic $5.1K, Philippines $5.2K, Sierra Leone $5.3K, DR Congo $5.7K,
  Guinea $5.9K, Nigeria $6.4K, Bangladesh $6.6K, Liberia $6.6K, Mozambique $7.1K.
  - Real: high malaria mortality (Niger: WHO 35K malaria deaths a year).
  - Philippines and Bangladesh: TB, with cheap treatment (US$638 per patient) and a ~40% case-fatality difference.
  - These are within published cost-effectiveness ranges for malaria and TB.

**People losing ART as % of people on ART**
- **Highest:** Jamaica 67%, Haiti 66%, Côte d'Ivoire 58%, Dominican Republic 56%, Honduras 51%, Lesotho 50%,
  Malawi 50%, Namibia 50%, Guatemala 49%, Zambia 46%.
  - Partly real: US money pays for a large share of ART in the Caribbean and Central America.
  - Partly artifact:
    - Côte d'Ivoire and Guatemala use derived PLHIV (no UNAIDS estimate);
    - Jamaica, Haiti, Côte d'Ivoire, Honduras and Guatemala are in the proportional-scaling group;
    - care and testing money is counted as ART (I-09).
- **Lowest:** Mauritius 1.6%, Iraq 1.6%, India 2.0%, Libya 2.1%, Venezuela 3.2%, Fiji 4.1%, Azerbaijan 4.2%,
  Moldova 5.1%, Egypt 6.1%, Central African Republic 6.3%. Real: little US HIV treatment money.

**Largest coverage drops by service**
- HIV treatment: Haiti 56 points, Lesotho 48, Namibia 47, Côte d'Ivoire 45, Malawi 44.
- PMTCT: Lesotho 61, Namibia 54, Kenya 47, Tanzania 46, Uganda 42.
  - Plausible for PEPFAR-funded programs.
  - PMTCT costs US$150 per woman (*assumption*), and 52 PMTCT lines use proportional scaling. This suggests the cost
    is too low (I-27).
- TB: Tajikistan 26, Mozambique 26.
- Bednets: Liberia 29, Sierra Leone 22.
- Malaria treatment: Liberia 21; Zimbabwe, Senegal, Cambodia and Zambia 11-15. These four use the 40% default coverage,
  an artifact of the default.
- Vaccines: São Tomé 12. All others are under 9 points, as expected, since governments and Gavi co-finance.

### 4.2 Benchmarks (as cited in the app)

| Benchmark | Published | Model (Full US exit, 70 countries) | Gap explained by scope? |
|---|---|---|---|
| PEPFAR-supported people on ART | 20.6M (FY2024) | 6.40M lose ART (of 24.7M on ART in these countries) | Yes, mostly. PEPFAR "supports" sites where governments and the Global Fund buy drugs; the model counts only what the lost US money pays for, after 15% continuity and proportional scaling |
| UNAIDS: AIDS deaths if US funding is not replaced, to 2029 | "more than 4 million" deaths, "6 million" infections (UNAIDS, July 2025; the app quotes 4.2M) | 1.24M HIV deaths 2026-2030; 1.93M new infections (sum of medians) | Partly. UNAIDS assumes the loss of all PEPFAR-supported services including prevention and commodities; the model's ART hazard is calibrated to the middle of Optima and Goals; infections are at the low end (transmission rate at the bottom of the published range) |
| Optima (ten Brink et al. 2025) | 0.77-2.93M HIV deaths 2025-2030 | 1.24M | Inside the range |
| Cavalcanti et al. 2025 (Lancet) | 14.1M all-cause deaths by 2030, all USAID sectors | 2.28M | Yes: four diseases only, no nutrition, maternal or WASH, and other causes |
| PMI (Lancet 2025) | 107K malaria deaths averted in 2025 by PMI | 81K a year | Consistent (Global Fund share, rebound and trend choices) |
| Gavi deaths per child | 0.017 | 0.019 | Consistent |

### 4.3 Labels against the math (Step 6)

The labels whose claims the math doesn't support:

| Where | Label says | Math does | Issue |
|---|---|---|---|
| The Numbers, New HIV Infections | (same style as the deaths pills) | median of 400 draws | I-05 |
| Preset description and caption, America First MOUs | "follows the 2026-2030 MOU schedules" | one year (2028) held for five years | I-03 |
| How Funding Changes: MOU Schedule | follows the MOU schedule | the schedule rescaled to the 2028 cut | I-02 |
| Header, US MOU | "MOU Signed" | status inferred from a 2026 value existing; the sheet column is "MOU schedule, or current estimate if no MOU" | I-08 |
| Every US$1 Million Lost, **by Bucket** | per bucket | main service only; no scaling; three mechanisms left out | I-04 |
| Net Loss to **Services** | lost to services | includes non-service systems money (Kenya: $30.4M of $290.8M) | I-12 |
| Fiscal panel, Health Share of Government Spending | one share | WDI, while the path panel's share is IMF-based | I-14 |
| Extra Deaths Over 5 Years tooltip | "Assumes the cut is sustained for five years" | wrong under a phased path | I-19 |
| Government Response help, fiscal tooltips | "2001-2023" | regression years 2002-2023 | I-18 |
| Coverage chip with aid gains | "−-6.6 pts" | double sign | I-15 |
| MOU caption | "US$XM a year before the cut" | nominal team-sheet dollars under an "all constant 2023 US$" header | I-21 |
| Card foot | "$X of aid per death" | assumes $1M lost every year for 5 years (unstated) | I-24 |
| Kicker, dropdown, captions | "No Government Replacement", "No Backfill (Historical Norm)", "No Backfill" | one setting | I-20 |

Labels checked and found correct:
- per-year and 5-year labels on every pill (check `aid_at_risk_is_per_year_not_5yr_total`);
- years in "2026-2030" and "2031-2035";
- "constant 2023 US$" on Sections 1-3;
- the All Countries range caption;
- "Not Modelled" (shown only where need or coverage is missing, or for orphan support);
- "~0" (only where the 97.5th percentile is 0);
- no misleading "0%" (no country has an aid share between 0 and 0.5% in 2023).

---

## 5. Issue log

Effect is on the headline numbers (Extra Deaths 2026-2030, Aid at Risk) unless stated.

| ID | Severity | What's wrong | Where | Countries / scenarios | Evidence | Proposed fix | Estimated effect |
|---|---|---|---|---|---|---|---|
| I-01 | Critical, **Fixed** | Model aid baseline (`dah_lines.csv`) was larger than IHME's bucket totals for the same years. **Cause: IHME's elim_ch double-counting flag was not applied.** | `prepare_model.py:255-263` (filter now applied right after reading the raw file) | 50 of 70 above +5%; all presets | Was: HIV +7.0%, TB +3.2%, malaria +5.8%, immunization +15.3%; Somalia 1.87x. Now: bucket totals within 0.1% of IHME; every country x bucket within 0.5% or US$50K (IHME rounding). Details: `I-01.md` | Done: filter added; model_data, all precomputed results and the test baseline regenerated and committed; two checks added | Full US exit deaths 2026-2030: 2.28M to 2.15M (-5.7%); Kenya -4.1%, Nigeria -6.7%, Ethiopia -9.2%, Somalia -32.7%. IHME 2025 preset +17% (US bilateral HIV now falls 39% in 2025 instead of rising 12.5%) |
| I-02 | Critical, **Fixed** | "MOU Schedule" path rescales each year's cut so the deepest year = the 2028 cut | `scenarios.py:mou_cut_path` + `model_section.py:415-418` (scenario built at `mou_year` 2028) | 14 of 16 MOU countries (BWA, SSD unaffected); America First MOUs + MOU Schedule path | `analysis.json` mou_path: Kenya 7,621 vs 21,832 deaths 5y; Nigeria 38.8K vs 65.9K; Ethiopia 7.7K vs 17.9K | When the path is MOU Schedule, build the scenario at the deepest-cut year (or pass yearly cuts directly) so year t's US cut = the schedule's year t | Deaths x1.0-2.9 for the 14 countries under that path |
| I-03 | Critical, **Fixed** | America First MOUs holds the 2028 cut for all of 2026-2030 but is described as following the 2026-2030 schedules | `scenarios.py:20-34, 56-78`; `model_section.py:49-51, 288-300` | 16 MOU countries; 54 others get the 36% average | `analysis.json` mou_preset: Ethiopia 8.3% used vs 23.6% average (48.9% in 2030); Kenya 16.1% vs 19.7% (60.3%); Burundi 47% vs 52% | Default this preset to the MOU Schedule path (after fixing I-02), or relabel it "the cut in <year>, held for five years" | Ethiopia x about 2.8, Kenya x about 1.2 if the schedule average is used |
| I-05 | Critical, **Fixed** (see `I-05.md`) | New HIV Infections (pill, All Countries sum) is the median of the draws; every other headline is the central run | `health_model.py:707, 729`; shown at `model_section.py:762`, `:1259` | All countries, all scenarios | `compare_recompute.py`: shown/central = Nigeria 1.10, Kenya 1.08, Honduras 1.07, Mozambique 1.00 | Report the central run (as for deaths), keep the percentile range | -10% to +1% on the infections pill |
| I-04 | Major, **Fixed** (commit 270e3fc; see `I-09_I-27_I-04.md`) | Per-US$1M cards price only the main service, ignore proportional scaling and caps, and leave out TB spread, malaria rebound and HIV infection deaths; titled "by Bucket" | `model_section.py:804-826`, `health_model.py:501-510` | All countries; worst where ART uses proportional scaling (29 countries) | `analysis.json` cards_vs_model: HIV 1.19-2.83x the model, TB 1.12-1.43x, malaria 0.75-1.31x | Compute the cards by running the model for a US$1M loss on the bucket's actual mix (or on the main line through the same scaling), and title them accordingly | Cards fall by up to 65% (Honduras HIV) |
| I-06 | Major, **Fixed** (commit 1b41c15; see `I-06_I-11_malaria.md`) | Malaria deaths trend uses 2010-2019; WHO deaths are flat or rising since 2015 in many countries; 13 of 46 malaria countries sit at the -8% clip | `prepare_model.py:368-370`, `who_inputs.py:apply` (trend), `health_model.py:308-315` | Malaria countries | Ethiopia: trend -8%, deaths 5.7K (2019) to 22.4K (2024); malaria deaths with trend off: Ethiopia +20%, Burkina Faso +19%, Uganda +13%, Mozambique +7% | Fit 2015-2024 (or hold flat) for malaria; keep 2010-2019 only for under-5 mortality, where declines continue | Malaria bucket +7% to +20% in affected countries; total about +0.9% |
| I-07 | Major, **Fixed** (commit f836fa1; see `I-07.md`) | "Gavi -24%" is the shortfall against Gavi's 2026-30 target, not a fall from the previous cycle (US$8.8B for 2021-25, now over US$9B pledged) | `scenarios.py:28-30, 77-78`, `model_section.py:56` | Global Fund & Gavi shortfalls preset | Gavi and press sources (section 2.2) | Drop the Gavi channel cut or base it on actual disbursement changes; relabel as "shortfall vs target" | Immunization deaths in that preset (169K) largely unsupported; the preset's total 1.01M would drop about 16% |
| I-08 | Major, **Fixed** | Header "MOU Signed" is inferred from a 2026 US value existing; the sheet's column is "MOU schedule, or current estimate if no MOU" | `prepare_model.py:418-421` | 16 countries labelled Signed | `datasets/co-financing_MOU.xlsx` row 3, cols 7-11; no mou_status column | Add an explicit status column to the team sheet and stop inferring it | Label only |
| I-09 | Major, **Fixed** (commit 270e3fc; see `I-09_I-27_I-04.md`) | ART line includes HIV care and counselling-and-testing money, all converted into ART patient-years at the ART cost | `prepare_model.py:93` (hiv_treat + hiv_care + hiv_ct) | All HIV countries | Care + testing = 32% of the line's money (country median 41%; Kenya 41%, Nigeria 38%) | Model testing and care separately (testing -> fewer new ART starts; care -> no direct ART effect), or disclose and test the sensitivity | If testing and care money has no immediate effect on people on ART, people losing ART (and HIV treatment deaths) fall by up to that share, about 30-40%, where ART isn't proportionally scaled (Kenya, Nigeria); HIV treatment is about half of all deaths |
| I-10 | Major, **Fixed** (commit 9b440ec; see `I-10.md`) | Section 3 mixes central-government revenue and COFOG compositions with general-government WEO totals | `views/1_Dashboard.py:686-741` | Revenue: 45 of 71; COFOG: 30 of 46 | `checks_results.csv` section3_*_is_general_government | Use general-government COFOG and WoRLD where available; otherwise show the central-government total as its own box, not rescaled | Box sizes, including Health, misstated for those countries |
| I-11 | Major, **Fixed** (commit 1b41c15; see `I-06_I-11_malaria.md`) | The Methods page and app say malaria treatment coverage is the "latest survey", but surveys are old (median 2017, 2006-2021), and 17 of 46 malaria countries use the 40% default | `who_inputs.py`, `health_model.py:206-238` | 46 malaria countries | `fallbacks.csv` | Show the survey year next to coverage; consider WHO's reported treatment courses as a cross-check | Malaria treatment deaths (about 1/3 of malaria) for those countries |
| I-13 | Minor, **Fixed** (commit 11dae37; see `I-13_I-14_I-15_I-16.md`) | Fiscal panel uses the full-cut loss and the existing response only, while the hero and The Numbers use the 2026-2030 average and include gradual budget money | `model_section.py:1164-1212`, `health_model.py:748` | Phased paths, gradual responses | Inventory | Use the same yearly averages (or label "full cut") | Display only |
| I-14 | Minor, **Fixed** (commit 11dae37; see `I-13_I-14_I-15_I-16.md`) | Two different "health share of government spending" figures on the same page (WDI vs IMF) | `health_model.py:202` vs `:908-929` | All; e.g. Honduras 9.4% vs 9.0% | — | Use `health_budget()` in the fiscal pill too | Display only |
| I-15 | Minor, **Fixed** (commit 11dae37; see `I-13_I-14_I-15_I-16.md`) | Aid-gain scenarios: coverage chip shows "−-x pts"; hero people (negatives clipped) ≠ table (netted); bucket bars net gains while Aid at Risk ignores them | `model_section.py:970, 495`; `health_model.py:482` vs `:720` | IHME 2025 preset: 10 countries before the I-01 fix, **25 after** (the corrected 2025 ratios show more aid rising, 183 of 572 cells, mostly immunization); plus 7 runs elsewhere where the hero and table differ by under one person (the hero drops lines under 0.5 people) | `checks_results.csv` | Handle gains explicitly (label as gains; one rule for netting) | Cambodia hero 139.9K vs table 116.4K people |
| I-16 | Minor, **Fixed** (commit 11dae37; see `I-13_I-14_I-15_I-16.md`) | Fixing `uc_imm` (low = central = high) in the parameter editor crashes the run | `health_model.py:111-112, 457` | Any user edit of that row | Reproduced: ValueError on broadcast | Draw fixed parameters as arrays of length n | Crash |
| I-17 | Minor, **Fixed** (malaria: `I-06_I-11_malaria.md`; header line, Methods and Data Years: commit 450889b, `I-26_I-17.md`) | Base-year mismatch: aid 2021-23, coverage 2024-25, GHES 2023, GDP 2024, all applied to 2026-2030 without projection | Throughout | All | Section 2.1 | State it in the header; consider the IHME 2025 levels as a baseline option | Unknown; largest where aid already fell after 2023 |
| I-26 | Minor, **Fixed** (commit 450889b; see `I-26_I-17.md`) | Interest/revenue missing -> debt-stress factor silently 1 (18 countries); the interest year can be as old as 2015 | `health_model.py:192-193` | 18 countries | `fallbacks.csv` | Flag it in the panel; use the IMF interest series | Fiscal capacity overstated for any of them under stress |
| I-27 | Minor, **Fixed** (malaria: `I-06_I-11_malaria.md`; PMTCT: commit 270e3fc, `I-09_I-27_I-04.md`) | Donor money exceeds cost x people covered in 204 country-lines (PMTCT 52, malaria treatment 51): unit costs (PMTCT $150, malaria treatment $8, both assumptions) are probably too low | `model_params.csv`; Validation page | 67 countries | `fallbacks.csv`; Validation page | Recalibrate PMTCT (cost per HIV+ woman incl. testing all pregnant women) and malaria case management | Small on deaths (sensitivity ±1.5% and ±2.9%), because proportional scaling already caps the lines |
| I-12 | Cosmetic, **Fixed** (commit ea998aa; see `cosmetic_fixes.md`) | "Net Loss to Services" includes non-service systems money | `model_section.py:756` | All | Kenya: $30.4M of $290.8M | Rename "Net Aid Lost" or subtract the non-service part | Label |
| I-18 | Cosmetic, **Fixed** (commit ea998aa; see `cosmetic_fixes.md`) | "2001-2023" for a regression run on 2002-2023 | `model_section.py:345, 1172` | All | `regressions.json` | Read the years from the file | Label |
| I-19 | Cosmetic, **Fixed** (commit ea998aa; see `cosmetic_fixes.md`) | "Assumes the cut is sustained for five years" shown under phased paths | `model_section.py:761` | Phased paths | — | Make it conditional | Label |
| I-20 | Cosmetic, **Fixed** (commit ea998aa; see `cosmetic_fixes.md`) | Three names for the no-response setting | `model_section.py:44, 274, 503` | All | — | One name | Label |
| I-21 | Cosmetic, **Fixed** (commit ea998aa; see `cosmetic_fixes.md`) | MOU caption in nominal US$ under a constant-2023 header | `model_section.py:297-298` | MOU countries | Sheet header: "US$ per year" (KFF / Foreign Assistance) | Say "nominal" | Label |
| I-22 | Cosmetic, **Fixed** (commit ea998aa; see `cosmetic_fixes.md`) | Validation cites "UNAIDS 2025 (Goals model) 4.2M"; UNAIDS's July 2025 statement says "more than 4 million" deaths and 6 million infections by 2029 | `views/3_Validation.py:86-89` | — | Press coverage of the UNAIDS report | Cite the document and figure exactly | Label |
| I-24 | Cosmetic, **Fixed** (commit ea998aa; see `cosmetic_fixes.md`) | Card foot "$X of aid per death" assumes $1M a year for 5 years without saying so | `model_section.py:825` | All | — | "per death over 5 years of a $1M-a-year cut" | Label |

(IDs I-23 and I-25 were checked and dropped. I-23: no country shows a misleading "0%" aid share. I-25: the All Countries
range caption is correct.)

---

## 6. Assumptions the results depend on

All-country 5-year deaths, Full US exit, no backfill, central run = **2,276,992**; deaths in 2031-2035 = **591,489**.
Each value below is set to its low or high, with everything else central (`sensitivity.csv`). The first block is the
parameters marked *assumption* in `model_params.csv`; the second is assumptions hard-coded in `health_model.py`. For
comparison, the most influential *sourced* parameter is art_hazard_mult: -19% / +24%.

| Assumption | Value (low-high) | 5-year deaths at low / high | 2031-2035 deaths at low / high |
|---|---|---|---|
| continuity (people who keep services anyway) | 0.15 (0-0.35) | +18.0% / -23.8% | +18.5% / -24.2% |
| hss_kappa (systems money that cuts services) | 0.5 (0.25-0.9) | -5.7% / +8.8% | -3.4% / +5.4% |
| mal_resurgence (malaria rebound per year) | 0.10 (0-0.25) | -2.0% / +3.8% | 0 / 0 |
| uc_mal_cm (malaria treatment cost) | $8 ($5-15) | +2.3% / -2.9% | 0 / 0 |
| uc_scale_elast (ART staff cost vs GDP) | 0.4 (0.25-0.6) | +1.0% / -1.4% | +1.8% / -2.6% |
| uc_pmtct (PMTCT cost) | $150 ($100-250) | +0.8% / -1.6% | 0 / 0 |
| cpia_ref (prevention cost per infection averted) | $5,000 ($2,500-12,000) | +0.3% / -0.2% | +4.7% / -2.7% |
| tb_dr_dcfr (DR-TB deaths averted per patient) | 0.45 (0.3-0.6) | -0.2% / +0.2% | 0 / 0 |
| hiv_inf_death_treated | 0.10 (0.05-0.20) | -0.1% / +0.1% | -2.7% / +5.4% |
| mal_cm_default_cov | 0.40 (0.30-0.50) | -0.0% / +0.1% | 0 / 0 |
| mal_itn_default_use | 0.50 (0.40-0.60) | 0.0% / 0.0% | 0 / 0 |
| art_reengage (return to ART after 2030) | 0.5 (0.25-0.75) | 0 / 0 | **+73.2% / -40.2%** |
| uc_ovc | $100 | no effect on deaths | no effect |
| *Hard-coded:* HIV survival Weibull shape | 2.25 (2.0-2.5) | +0.3% / -0.2% | +1.0% / -1.0% |
| *Hard-coded:* malaria-treatment survey threshold | 50/1,000 (25-100) | -0.1% / +0.3% | 0 / 0 |
| *Hard-coded:* DR-TB share of TB | 4% (2-6%) | -0.2% / +0.1% | 0 / 0 |
| *Hard-coded:* DR-TB coverage | 45% (30-60%) | -0.1% / +0.1% | 0 / 0 |
| *Hard-coded:* fallback mortality trend | -0.9%/yr (-2% to 0) | 0 (no country uses it) | 0 |
| *Setting:* mortality trend on (default) | on / off | off: +0.9% (malaria +7% to +20% in Ethiopia, Burkina Faso, Uganda, Mozambique) | off: +0.6% |

Other structural assumptions not varied here:
- ramp-up shares by year;
- the ART hazard shape (1.2-5.0%) and the transmission ramp;
- vaccine cohort weights (40/35/20/5%);
- TB secondary-case timing (half in year +1, half in +2) and the 0.3 ART factor on HIV+ TB case fatality;
- the debt-stress formula (10% / 40%) and the p75 effort level;
- the 36% non-MOU cut;
- applying OECD total-ODA cuts to health;
- the IHME 2025 ratio clip (0-1.5) and the US$20M fallback threshold;
- holding 2021-23 aid and 2024-25 coverage fixed into 2026-2030.

**Biggest uncertainties:**
- *Five-year deaths:* continuity (an assumption) moves the total by about -24% to +18%. art_hazard_mult (sourced
  calibration) moves it by about -19% to +24%.
- *2031-2035 figure:* dominated by the re-engagement assumption (-40% to +73%).
