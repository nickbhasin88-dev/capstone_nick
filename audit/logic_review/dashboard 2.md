# Part 5: Dashboard consistency and claims

## 1. Independent reproduction

**How it was done.**
- **Agent:** a separate subagent that had not read `health_model.py`, `scenarios.py`, `model_section.py`, the views,
  the audit recompute scripts or any snapshot.
- **What it worked from:**
  - `logic.md` sections 0-6;
  - `audit/METHOD.md`, consulted only where `logic.md` was incomplete, and recorded each time;
  - the data files (`model_data/`, `model_params.csv`, `unit_cost_reference.csv`).
- **What it built:** its own implementation (`reproduction/repro.py`; notes, outputs and the cell-by-cell comparison are in `reproduction/`).
- **What it computed:**
  - Countries: Kenya, Nigeria, India, Honduras and Mozambique.
  - Cases: (1) Full US Exit, no response, sudden; (2) Full US Exit, custom 25% replacement capped by fiscal space,
    pro rata; (3) OECD 2025, no response; (4) Full US Exit, linear phase-out.
  - Values: every headline total, plus for each of 9 service lines: baseline money, gross and net loss, unit cost,
    need, coverage, people losing per year, coverage drop, deaths 2026-30 and HIV infections.
  - Further deaths 2031-35.
- **Comparison:** against the dashboard's own values (`audit/after_cleanup.csv`, the snapshot of every displayed
  number on the current code).

| | Cells compared | Within 0.5% | Largest difference |
|---|---|---|---|
| Literal reading of `logic.md` | 1,860 | 1,840 | Malaria vector-control deaths exactly +10.0% (all 32 cells); Nigeria total deaths +1.9% to +2.3% |
| Malaria rebound exponent = years elapsed (t-1) | 1,860 | **1,860** | 0.17% (Honduras deaths 2031-35, from the post-2030 vaccine formula when the U5MR clip binds) |

**Result.**
- Every number reproduces within 0.5% once the malaria rebound exponent is read as years elapsed.
- The code uses `(1 + mal_resurgence) ** dur[t]` with `dur` starting at 0 (`health_model.py:865`).
- The 20 cells first flagged on "further deaths" were my own column naming: in the snapshot, `C.deaths` is the
  2026-2035 total. Against `C.after_2030` all 20 match (largest 0.17%).

**What the reproduction found about the documentation.**

| ID | Finding | Severity |
|---|---|---|
| L-36 | `audit/METHOD.md` gives a different ART units formula from the code: "raw = min(covered, eff_base_art / cost) x net / base", which scales the testing-and-care money down by ART's share. The code (`health_model.py:438-450`, `:783-791`) uses net / cost in that branch, as `logic.md` says. Kenya case 1: code 451.7k people a year vs METHOD.md about 328k. The dashboard follows the code, so METHOD.md, the spec the audit recompute claims to implement, is wrong on the largest line. | Presentation (documentation); High confidence |
| L-37 | `logic.md` itself was not enough to reproduce: the agent needed METHOD.md for 12 items (CPI factors, prevention incidence denominator and clip, TB secondary-case CFRs, vaccine timing, post-2030 ART return, Weibull details, defaults). For publication, one complete specification is needed. | Presentation |
| L-39 | Data quirk the reproduction exposed: India's TB money is mostly systems (US$82M) and unspecified (US$36M). Spread by the country's own-money mix, it goes mostly to DR-TB (own money US$16.2M vs DS-TB US$7.2M) at US$14,773 per patient. So India's TB card shows 638 deaths per US$1M vs about 2,000 elsewhere. Spreading by patients, or by the WHO DS/DR split, would put most of it on DS-TB. | Minor; High confidence on the mechanism |
| L-16 (adds to) | DR-TB unit costs fall with poverty but not monotonically: low-income US$1,568, lower-middle US$8,125, upper-middle US$6,800 (single studies). After markup, Mozambique pays US$2,851 per DR-TB patient and the lower-middle countries US$14,773. | Minor |

## 2. Labels, units and time basis

| Displayed item | Math | Label | OK? |
|---|---|---|---|
| Aid at Risk / Health Aid Lost Each Year | mean over 2026-30 of gross loss, US$/yr | "(per Year)", "Each Year" | yes |
| Net Aid Lost | mean (L_t - budget_t), US$/yr | "per year" (sub-line) | yes |
| People Losing Care Each Year (hero) | sum over lines of mean_t units, excluding prevention and OVC | "Each Year". Tooltip: "People who lose a service in each year the cut lasts" | yes. For ART the same people mostly recur each year (the table says so since the labels fix) |
| People Losing Service, per Year (table) and the 5-year total line | mean_t and sum_t units | both labelled | yes |
| Units for ART, malaria and vaccines | patient-years; person-years of net use; children | unit labels in the table | **L-01:** "people on HIV treatment losing care" are full-cost equivalents, not people. The label implies headcount (L-40, Presentation) |
| Coverage after / drop | coverage - mean units / need, percentage points | "pp" | yes |
| Extra Deaths, 2026-2030 | sum over 5 years | "Extra Deaths, 2026-2030", "Over 5 Years" | yes |
| Further Deaths 2031-2035 | deaths in 2031-35 from losses in 2026-30 | labelled | yes |
| New HIV Infections, 5 Years | sum over 2026-30 | yes | yes |
| Per-US$1M cards | US$1M a year for 5 years; deaths over 5 years; "aid lost per life lost" = US$5M / deaths | foot tooltip explains | yes |
| Ranges | 2.5th-97.5th percentile of parameter draws | "Range = 95% interval" | **L-02:** the name overclaims (`uncertainty_scope.md`) |
| All Countries totals | sum of country central values; range = sum of country percentiles | `ALL_RANGE_TIP` says this "overstates the width" | Disclosed. The better fix is the percentile of summed draws (IMP-10) |
| Money units | constant 2023 US$; MOU amounts nominal | README and Methods; MOU caption "nominal US$" | **L-35:** nominal MOU schedules compared with a nominal 2021-25 reference ignore 2026-30 inflation. A flat nominal schedule is a real cut of about 2-3% a year that the model counts as 0 |

## 3. Do related numbers agree everywhere?

`audit/checks.py --quick` (run during this review; result at the end of this file) tests that:
- the headline totals equal the sum of the service table;
- the All Countries row for a country equals its own page (same 400 draws, seed 7);
- money is conserved across lines, nothing is negative, units are at most covered and deaths at most people affected;
- the Validation inputs match the model.

The independent reproduction confirms the headline-to-line arithmetic for 5 countries x 4 cases.

| Pair checked | Result |
|---|---|
| Story lede numbers vs Section 4 headline cards | Same run (`run_ctl` cached; `model_section.py:672`) |
| Hero "People Losing Care" vs table total | Same function (`care_breakdown`, `model_section.py:604-610`) |
| Country page vs All Countries row | `checks.py` (precomputed files rebuilt byte-identically, `uncertainty_scope.md`) |
| Validation "This Model" vs All Countries | Same precomputed file (`views/3_Validation.py:70`) |
| Per-US$1M cards vs Section 4 | Different runs by design (US$1M spread over a disease's lines) |

## 4. Results a viewer would find surprising, and why

Full US Exit, no response. Snapshot values.

1. **TB deaths per US$1M are 5-6x HIV's** (Kenya TB 1,945 vs HIV 344; Mozambique 2,125 vs 375).
   - **TB:** US$1M buys 1,332 patients at US$638 (after the 45% markup). About 40% of them die untreated (0.43
     untreated vs 0.03 treated), plus 0.4 secondary cases each. That is about **US$2,600 per death**.
   - **HIV:** US$1M buys about 3,600 patient-years at US$277. Each person off ART dies at 17.3% over 5 years. That is
     about US$5.6-7.9k per death.
   - The TB figure is plausible: TB treatment is among the most cost-effective interventions, with published costs
     of a few hundred US$ per DALY averted (see `benchmarks.md`).
   - The HIV figure is low per dollar because of L-01. With Brinkhof's 40% risk, HIV deaths per US$1M would be about
     2.3x the current figure.
2. **Kenya's ART coverage falls 30 points and Honduras's 39 points, but Kenya's vaccine coverage falls only 1.6
   points.**
   - ART is the largest donor line, and US$277 per patient-year is cheap relative to donor money.
   - Vaccines: donor money for vaccines ÷ US$87 is small next to births (Kenya: 24,728 children vs about 1.5M births).
     Most routine immunization is government-financed or Gavi co-financed.
3. **Bednet "people losing service" are in the millions** (Nigeria 13.1M person-years), **yet malaria coverage drops
   only 5.6 points.** Nets are cheap (US$2.2 per person-year) and the population at risk is about 230M.
4. **India loses DR-TB patients at 11% of the rate of DS-TB but at 23x the unit cost** (L-39).
5. **The vaccine card shows 9,770 children per US$1M in every country.**
   - This is US$1M x (1 - 0.15) / 87: one global vaccine cost.
   - Only deaths vary, through U5MR. A viewer may expect cost to vary by country.
   - Gavi country financial data would allow that (DR-09).
6. **Lives-first replacement can raise new HIV infections** while deaths fall. It refills treatment first and
   prevention last. Disclosed in the infections tooltip (`model_section.py:916`).
7. **Honduras: malaria card shows 106,022 people losing service, but 0 deaths.** WHO reports 0 malaria deaths.
   Labelled "No malaria deaths modelled ... (very low transmission)". Explained.
8. **A gradual phase-out can produce more 2031-35 deaths than a sudden cut in some countries.** More people are
   still in early high-hazard years at the end of 2030. The cohort logic in `art_cohorts` (`health_model.py:485-525`)
   explains this.
9. **Nigeria malaria: 40,564 bednet deaths vs 24,649 treatment deaths.** Nigeria's ITN use is 28% and treatment
   coverage 56%. Vector control is about 64% of Nigeria's malaria money.

None of these is unexplained by the logic, so none becomes a finding, except where the logic itself is questioned
(L-01, L-39).

## 5. Claims audit

Every sentence that states or implies a result, from `model_section.py`, `views/*.py` and the Methods page.

| # | Where | Text | Supported at that strength? | Suggested wording |
|---|---|---|---|---|
| C1 | Story headline (`model_section.py:680`) | "{Scenario}, {country} could see about N more deaths by 2030" | Partly. "Could" is right. But N is a central run whose main driver (ART) is calibrated inconsistently (L-01), and "by 2030" omits "if the cut is sustained and nothing replaces it". | "If {scenario} is sustained and not replaced, the model estimates about N more deaths in {country} in 2026-2030 (range a-b across parameter values)." |
| C2 | Story dek (`:691`) | "historically governments have not replaced falling aid" | Supported, with a qualifier. The regression gives theta = -0.19 (95% CI -0.45 to +0.07; `prepare_model.py:526`): no evidence of replacement on average, 2001-2023. But past falls were smaller and gradual, and the MOUs commit governments to co-financing (L-08). | "In past aid declines (2001-2023), governments on average did not increase their own health spending to compensate." |
| C3 | Story dek (`:687`) | "Most would come from people losing HIV treatment and prevention (x%)" | Depends on L-01: the HIV share of deaths moves from about 51% to 54-78% under consistent readings. The direction ("most from HIV" in southern and eastern Africa) is robust; the share is not. | Keep, without the percentage, or show it with the range. |
| C4 | Headline cards, Methods, Validation (`:529`, `:913`, `:917`, `:867`, Validation `:290`, `:307`) | "Ranges are 95% intervals" / "Range = 95% interval" | **Overclaims** (L-02). The ranges cover parameter uncertainty only. | "Range across parameter values (2.5th-97.5th percentile of 400 draws); excludes data and structural uncertainty." |
| C5 | Hero (`:600`) | "People Losing Care Each Year" | **Overclaims for ART.** These are full-cost equivalents (L-01, L-40). | "People-equivalents of care lost each year (lost money ÷ cost per person)", or a tooltip saying so. |
| C6 | Per-US$1M foot | "About $X of aid lost per life lost" | Supported as model arithmetic. Readers may compare it with cost-effectiveness benchmarks; it is consistent for TB and malaria, low-death for HIV (L-01). | Keep; add "model estimate". |
| C7 | All Countries pills | "Aid Lost per Year, 70 of 71 Countries"; "Totals add up each country's central estimate" | Supported and correctly scoped. | Keep; add "These 71 countries receive about 72% of country-allocated HIV, TB, malaria and vaccine aid" (L-03). |
| C8 | Validation (`:1862`, Methods) | "its totals should come in below the Cavalcanti figure and within or below the ten Brink range for comparable scenarios" | Supported for Cavalcanti. For ten Brink, the model's 1.01M HIV deaths are inside 0.77-2.93M, but only because L-01's two inconsistencies partly cancel. | Keep; add a note on the ART calibration once L-01 is resolved. |
| C9 | Methods cross-check (`:1806`) | "They are a lower bound for a sudden cut, because aid historically moved gradually and other funders filled gaps, so the truth for 2026-2030 most likely lies between the two approaches" | **Overclaims.** "Most likely lies between" is a judgment without evidence. Regression coefficients on gradual historical changes are not a bound. | "They describe how coverage moved with aid in the past, when changes were gradual and other funders often filled gaps, so they likely understate the effect of a sudden cut." |
| C10 | `model_params.csv` art_hazard_mult source | "sits between Optima ... and UNAIDS" | **Wrong.** The model gives 1.01M HIV deaths, at the bottom of Optima's range (L-01). | Rewrite once L-01 is resolved. |
| C11 | OECD preset description (`scenarios.py:35`) | "Each donor's 2025 change in total ODA ... applied to its health aid" | Transparent and accurate. The concept is weak (L-28). | Add: "health aid fell faster for the UK and France (IHME: -39%, -33%)". |
| C12 | Full US Exit description (`scenarios.py:23`) | "stops funding Gavi (announced June 2025) and UNFPA; its Global Fund pledge falls 23% (US$6.0B to US$4.6B ...)" | Verified (pledge figures: Global Fund, EATG). | Keep. Optional: "the US paid US$3.12B of its US$6B 7th-cycle pledge". |
| C13 | Global Fund & Gavi preset | "default Gavi -15%" | Labelled "our estimate" on Methods. Unverified as a disbursement forecast (L-09). | Keep the label on the dashboard too. |
| C14 | MOU preset | "used exactly as written (a funding increase counts as no cut)" | Accurate. Omits partner co-financing commitments (L-08) and inflation (L-35). | Add: "MOU co-financing commitments by the partner government are not modelled." |
| C15 | Net Aid Lost sub-line | "{k}% counted as lost services (assumption)" | Accurate and labelled. | Keep. |
| C16 | Validation Reading (`views/3_Validation.py:278`) | "historically, aid has gone where deaths were high, so that regression can neither confirm nor rule out the model" | Supported (reverse causality is the standard explanation). | Keep. |
| C17 | INTRO | "money not replaced ÷ cost per person = people who lose a service" | Accurate description of the math. Implies a person-level meaning (L-01). | "... = people-equivalents of service lost". |
| C18 | Infections tooltip | "Lives-first triage refills treatment and vaccines first" | Accurate. "Triage" implies a real policy; it is a hypothetical rule (L-30). | "Lives first (hypothetical best case)". |

**Count:** 18 claims reviewed.
- Supported as written: 8 (C6, C7, C11, C12, C15, C16, and C2 and C8 with a qualifier).
- Need a qualifier: 5 (C1, C3, C13, C14, C18).
- Overclaim or wrong: 5 (C4, C5, C9, C10, C17).

## `audit/checks.py --quick` result (run 14 October 2026, this review)

**55 checks, 14,688 rows: 0 failed, 6 warnings.** All 6 warnings are `section1_dah_equals_section2_dah_same_year`:
Section 1's DAH (health spending database) differs from Section 2's DAH (DAH database) by 2-4.4% in 6 of 630
country-years. These are two IHME products with different revision timing; not a model issue.

Relevant passes include:
- `dashboard_country_equals_all_countries_row` 28/28;
- `cut_formula_matches_documented_scenario` 236/236;
- `unspec_and_kappa_conserve_money` 236/236;
- `section1_2023_matches_raw_IHME_file` 71/71;
- `zero_cut_gives_zero` 118/118.
