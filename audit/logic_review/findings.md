# Logic and evidence review: findings and recommendations

**Branch:** `real-modeling-check`.
**Code reviewed:** commit `a6a4871` (after the cleanup merge); the review files were added on top.
**Rules:** read-only. No model, data or app code was changed.

## Files

| File | Part |
|---|---|
| `findings.md` | 10. This file |
| `URGENT.md` | Critical findings L-01 and L-41 (pushed as found: `12e15a9`, `88bb1b6`) |
| `inputs.csv`, `inputs.md`, `build_inputs.py` | 1. Input review (98 inputs) |
| `assumptions.md`, `sensitivity.py`, `sensitivity.csv`, `tornado.py`, `tornado.png` | 2. Assumptions, evidence and one-at-a-time sensitivity |
| `logic.md` | 3. Logic chain, as plain math with `file:line` |
| `uncertainty_scope.md` | 4. Uncertainty, scope omissions, reproducibility |
| `dashboard.md` | 5. Independent reproduction, labels, consistency, surprising results, claims |
| `benchmarks.md` | 6. External benchmarks |
| `redteam.md`, `redteam_report.md` | 7. Independent red-team review and reconciliation |
| `data_requests.md` | 8. Data requests, with download steps |
| `improvements.md` | 9. Improvements, ranked and sequenced |
| `coverage.md` | 11. Coverage table |
| `reproduction/` (independent `repro.py`, `notes.md`, outputs, cell-by-cell comparison), `range_test.py`, `extra_sensitivity.py`, `build_coverage.py` | Evidence and scripts behind Parts 2, 4, 5 and 11 |

## Status after the "Do now" changes (14 October 2026)

The user approved the "Do now" items; they were implemented on `real-modeling-check`, one commit per item. Findings
and improvements marked ✅ below are done; ◐ partly done. L-01, IMP-02 and anything needing new data were not
started. Before/after numbers: `do_now_before_after.md`.

| Item | Commit | Addresses | What changed |
|---|---|---|---|
| IMP-20 ✅ | `cff29af` | L-36, L-37 | One specification, `docs/SPEC.md`, matching the code. The independent reproduction runs from it alone: 1,860 of 1,860 cells within 0.5% before the model changes, and again after them (`reproduction/notes.md`) |
| IMP-10 ✅ | `581c013` | L-02 | All Countries range = percentile of the summed draws (Full US Exit 1.39-2.70M, was 1.34-2.81M); "range across parameter values" with the parameter-only tooltip everywhere |
| IMP-21 ✅ | `576a8d8` | L-48 (and C7 / L-03, C8 / L-47, C14 / L-08 wording) | Claims C1, C2, C3, C6, C7, C8, C9, C10, C14, C17 reworded; headline rounded to two significant figures |
| L-40 ✅ | `c56214a` | L-40 | Treatment and Prevention shown separately; ART counted as the treatment the lost money would have paid for |
| IMP-14 ✅ (labels) | `752f611` | L-45, L-46, L-28 (label) | "US Bilateral Exit + Multilateral Withdrawals" (77% of the US Global Fund pledge kept); "Total-Aid Cuts (OECD) Applied to Health Aid"; IHME country split described as global ratios |
| L-30 ✅ | `8b89420` | L-30 | "Hypothetical best case (triage)" |
| L-33 ✅ | `f8566e4` | L-33 | Further deaths labelled assumption-driven, with the range across art_reengage 0.25-0.75 (all countries 299K-851K) |
| IMP-05 ✅ | `c6dd075` | L-04, L-20 | LiST effects in full for under-5 deaths, x mal_adult_effect_frac (0.5, assumption) at 5+; mal_cm_eff 0.97 (0.82-0.99), Thwing 2011. Malaria deaths, Full US Exit, -6.4% |
| IMP-18 ✅ | `719ff89` | L-25 | Malaria trend from WHO malaria deaths 2015-2024 (±5% clip labelled an assumption). Malaria deaths -3.2% |
| L-10, L-12, L-13 ✅ | `911fbfe` | L-10, L-12, L-13 | TB trend removed (TB deaths are per patient); detection rate capped at 100%; HIV+ untreated TB CFR = 0.78(1-a) + 0.49a (WHO Table 5). TB deaths +2.7% |
| L-26 ✅ | `ba496d1` | L-26 | asd_share cited to KFF 2025 (47%); value kept at 0.45 |

**Headline after all changes** (all countries, Full US Exit, central): 1,945,605 deaths 2026-2030 (was 1,969,304,
-1.2%); range across parameter values 1.37-2.68M (see `do_now_before_after.md` for every preset and for Kenya, Nigeria,
Mozambique and India). L-01 (Critical) is unchanged and still dominates the uncertainty.

**Checks and test baseline.**
- `audit/checks.py --full` after all changes: 59 checks, 76,501 rows, 0 failures, 6 known warnings (Section 1 vs
  Section 2 DAH).
- The independent reproduction built from `docs/SPEC.md` alone matches 1,900 of 1,900 cells within 0.5%.
- Snapshot `audit/before_do_now.csv` vs `audit/after_do_now.csv`: 251,222 of 3,159,310 values changed, all deaths on
  the malaria lines and on TB treatment, plus the totals, ranges and deaths per US$1M built from them. No money,
  people, coverage or fiscal value changed.
- `tests/baseline_sudden.json` locks results for 5 countries x every preset x 3 responses, with the later mechanisms
  switched off. It was refreshed three times, because the model's malaria and TB death formulas changed on purpose:
  - IMP-05 (`--malaria`, 63 of 99 entries);
  - IMP-18 (`--malaria`, 63);
  - L-13 (new `--tb` mode, 54).
- Each refresh checks that, outside the lives-first response, only that disease's lines, the totals and its path
  moved. The labels-only items changed no baseline value.

**IMP-05 follow-up: under-5 share from the World Malaria Report (14 October 2026).**

**Why.** The caveat below was a concept mismatch: numerator and denominator came from different estimation methods and
years.

**What changed.** The under-5 share is now WHO's own regional share from the World Malaria Report 2025:

| WHO region | Quote and page | Share used |
|---|---|---|
| African | "Just over 75% of all deaths in the region are of children aged under 5 years" (p. 20) | 0.75 (0.70-0.80) |
| Americas | "less than 25%" (p. 24) | 0.20 (0.15-0.25; WHO gives only a bound) |
| Eastern Mediterranean | "36.4% of all deaths" (p. 28) | 0.364 (±5 points) |
| South-East Asia | "Just under a quarter" (pp. 31-32) | 0.25 (±5 points) |
| Western Pacific | "40.0%" (p. 35) | 0.40 (±5 points) |

- The report gives no European Region or global under-5 share, so rule b (global share) is unavailable.
- All 46 countries with malaria deaths use rule a (100% of model malaria deaths). The 4 European Region countries have
  no malaria deaths and no share.
- The old country series is kept behind `mal_u5_use_country_series` (off).

**Effect on malaria deaths, Full US Exit:** 349,644 → 369,425 (+5.7%); all deaths 1,945,605 → 1,965,386 (+1.0%).

| Country | Before | After |
|---|---|---|
| Kenya | 9,714 | 17,822 |
| Ethiopia | 3,651 | 6,304 |
| Nigeria | 73,422 | 63,164 |
| Mozambique | 13,955 | 12,521 |
| India | 202 | 204 |

**New caveat from IMP-05 (resolved by the follow-up above).** The under-5 share of malaria deaths comes from the WHO/MCEE child series (2021) ÷ WHO
all-age deaths (2024). It varies widely and in places disagrees with WHO's regional figure (75% under 5 in the African
Region): Nigeria 0.98, Mozambique 0.90, Kenya 0.19, Ethiopia 0.11. So country malaria results moved in different
directions: Kenya -40%, India -30%, Nigeria +10%, Mozambique +8%. A WHO country series of under-5 malaria deaths would
settle it (data request).

## Batch 2: ART death risk and HIV transmission (14 October 2026)

Option A (user decision): "people losing ART" stays the count of people who stop ART (full-cost equivalents of the
lost money, all donors, all countries); the death risk, re-engagement and transmission now describe people who have
actually stopped ART. Evidence and sources: `batch2_evidence.md`; scripts `audit/batch2_cohort.py`,
`audit/batch2_projection.py`.

| Item | Status | What changed |
|---|---|---|
| L-01 ✅ | done | `ART_HAZARD` = excess deaths by years since stopping ART, 1-10, from a CD4-stage cohort calculation (Optima Tables A1-A2; ZIMPHIA 2020 starting CD4): 1.3, 2.5, 3.7, 4.9, 6.0% then 6.8-7.3%; 5-year 18.4% (was 17.3%); `art_hazard_mult` 1 (0.65-1.7); years 6-10 replace the flat year-5 value after 2030. The parameter text no longer claims a calibration to PEPFAR totals |
| L-41 ◐ | partly done | `art_transmission` 0.04 replaced by the country's UNAIDS 2025 rate of new infections per person with unsuppressed viral load (`country_inputs.csv` `art_transmission_rate`, median 0.12; WHO-region median for 14 countries) x `art_transmission_mult` 1 (0.71-1.38); one further generation of infections (`hiv_new_inf_unsup_years` 4, 2.5-5.5, assumption). Infections 1.55M to 4.3M (UNAIDS 6M). The remaining gap to Optima is L-49, not transmission |
| L-33 follow-up | done | `art_reengage` 0.5 (assumption) to 0.35 (0.17-0.68), sourced indirectly (Kranzer 2010, Kaplan 2017, Mody 2026) |
| Labels | done | "people who stop ART (full-cost equivalents)" with a tooltip in the service table, the hero, the cards and the Methods page |
| Sensitivity switch | done | `hiv_legacy_art_params` = 1 restores the old hazard, transmission, re-engagement and no second generation (central results identical to `before_batch2.csv`; ranges differ through the new `art_hazard_mult` range) |

**Open item L-49 (Major, High confidence, from the Batch 2 benchmark): the Optima overlap gap is driven by the
count of people who stop ART, not by death risk or transmission.** Model 0.57M vs Optima scenario 5 1.37M HIV deaths;
1.87M vs 5.08M infections (15 overlapping countries, `batch2_optima_compare.csv`). Example: Mozambique 23% of people
on ART stop in the model vs PEPFAR 66% of HIV spending (Optima appendix Table B2, p. 8). To be addressed in Batches
3-4 (money conversion, unit costs, continuity, cap rule). Per country (model: Full US Exit, people who stop ART /
people on ART outside PMTCT, `before_batch2.csv`; Optima Table B2: PEPFAR funding / total expenditure and total
international funding / total expenditure, most recent GAM year):

| Country | People who stop ART (model) | People on ART | Model share who stop | PEPFAR share of HIV spending | All international share |
|---|---|---|---|---|---|
| Azerbaijan | 310 | 9,720 | 3% | 0% | 14% |
| Cambodia | 4,337 | 72,200 | 6% | 15% | 64% |
| Côte d'Ivoire | 103,156 | 183,443 | 56% | 56% | 12% (Table B2's "total international" is below its PEPFAR figure; PEPFAR is from COP 2022) |
| Dominican Republic | 24,451 | 57,200 | 43% | 34% | 42% |
| Eswatini | 70,040 | 199,500 | 35% | 42% | 59% |
| Kenya | 451,685 | 1,365,000 | 33% | 26% | 37% |
| Kyrgyzstan | 2,222 | 7,700 | 29% | 17% | 71% |
| Malawi | 396,616 | 890,000 | 45% | 60% | 95% |
| Moldova | 383 | 9,180 | 4% | 0% | 45% |
| Mongolia | 20 | 294 | 7% | 0% | 52% |
| Mozambique | 488,713 | 2,100,000 | 23% | 66% | 96% |
| South Africa | 677,587 | 6,156,000 | 11% | 21% | 24% |
| Tajikistan | 4,417 | 12,160 | 36% | 0% | 0% |
| Uganda | 355,770 | 1,275,000 | 28% | 65% | 80% |
| Zimbabwe | 163,293 | 1,235,000 | 13% | 57% | 89% |

The model's share is below PEPFAR's funding share in the four countries that carry most of Optima's deaths
(Mozambique, Uganda, Malawi, Zimbabwe), and above it where the US funds little (Tajikistan, Kyrgyzstan, Dominican
Republic): the full-cost denominator, the non-service share, continuity and the cap rule all act here. Optima's
scenario 5 also drops initiations to zero and counts six years (2025-2030).

**Headline after Batch 2** (all countries, Full US Exit, central, sudden cut, no response): 2,055,422 deaths
2026-2030 (was 1,965,386, +4.6%); HIV deaths 1,096,151 (was 1,006,114, +8.9%); HIV infections 4,334,929 (was
1,552,704, x2.8); further deaths 2031-2035 1,092,054 (was 495,218, x2.2: slower return to care and a death risk that
keeps rising to year 8 instead of staying at 5%). TB, malaria and vaccine deaths unchanged. Every preset and the
five focus countries: `batch2_before_after.md`.

**Checks after Batch 2.** `audit/checks.py --full`: 59 checks, 76,501 rows, 0 failures, 6 known warnings (Section 1 vs
Section 2 DAH). 357 tests pass; `tests/baseline_sudden.json` refreshed with `--hiv` (84 of 99 entries; no non-HIV
line moved, including under lives first). Snapshot `audit/before_batch2.csv` vs `audit/after_batch2.csv` (local):
287,674 of 3,227,070 values changed, all on the HIV treatment line, the HIV bucket, the HIV path, the totals and
ranges built from them, further deaths and the HIV US$1M card; no money, people, coverage, fiscal, TB, malaria or
vaccine value changed. Commits: evidence `c625037`, implementation `49767e9`.

## Batch 3+4: money-to-people conversion, unit costs, cap rule, TB costs, continuity (14 October 2026)

Evidence, decisions and gates: `batch34_evidence.md`; scripts `audit/batch34_*.py`. Before snapshot:
`audit/before_batch34.csv` (local). Headline = all countries, US Bilateral Exit + Multilateral Withdrawals, central
run, no response, sudden cut, 2026-2030 deaths; ART = people who stop ART (full-cost equivalents, per year), summed
over countries. Before the batch: 2,055,422 deaths; 5,303,707 people who stop ART.

| Item | Status | Commit | Headline after | People who stop ART after | What changed |
|---|---|---|---|---|---|
| 1. L-05 overhead | ✅ done | `4f9f0c0` | 1,798,648 (-12.5%) | 4,938,369 (-6.9%) | Systems money is no longer converted into service units: `hss_service_share` = 0 (range 0-0.25, assumption) replaces kappa for HSS money; `hss_kappa` keeps its I-09 role for testing-and-care money only. Fully loaded unit costs (site x 1/(1 - asd_share)) stay. TB fell most (-26%: 17% of its effective treatment money was kappa x HSS), malaria -15%, HIV -7%, vaccines unchanged. The money-conservation check in `audit/checks.py` now tests the new formula (SPEC.md section 3). The quick harness's draw count went from 50 to 100 (`batch34_evidence.md` A) |
| 2. L-43 unspecified money | ✅ done | `2a792f7` | 1,676,482 (-6.8% vs item 1; -18.4% vs before) | 4,871,552 (-1.4%; -8.1%) | Unspecified money is split by purpose with the country's Global Fund GC7 module shares (`country_inputs.csv` `unspec_*`, `batch34_inputs.py --shares`): treatment share to treatment lines, prevention to prevention lines, testing to testing-and-care (kappa), systems to systems money, programme management to non-service. TB -20% (treatment share 49% instead of the 77% the mix rule gave), malaria -12%, HIV -1%. 38 of 210 lines use a WHO-region median |
| 3. IMP-02 | ◐ partly done / (c) BLOCKED | `85440df` | 1,676,482 (no change) | 4,871,552 (no change) | (a) and (b) are items 2 and 1. (c) testing-and-care money as a flow of lost initiations: BLOCKED. UNAIDS has "People initiating ART" but no source gives a cost per new initiation, and the flow formulation accumulates people who never start (1.27M a year across the 70 countries, so about three times today's person-years off ART by 2030) rather than lowering the count; implementing it would move HIV deaths by a structural amount set by two unsourced inputs. The kappa proxy (I-09) stays, labelled as a proxy in SPEC.md and on the Methods page (`batch34_evidence.md` C) |
| 4. IMP-03 ART unit costs | ✅ done | `810df94` | 1,402,337 (-16.4% vs item 3; -31.8% vs before) | 3,450,945 (-29.2%; -34.9%) | Site cost per patient-year by country (`art_site_cost`, 2023 US$) from GHCC UCSR records (per person-year, provider, no above-service costs, price year 2015+, economic x 0.981) pooled with Rosen 2021: own value for 7 countries, South Africa outside the gate, 63 use the WHO-region or income-group median (AFR $220 vs the old default's $156 median). `uc_art_mult` range 0.68-1.38 from the country ranges. HIV deaths -27%. Baseline: 83 entries refreshed; 11 lives-first entries also moved vaccine, bednet and spraying lines through the refill order (KEN, MOZ) |
| 5. IMP-11 TB treatment costs | ✅ done | `e6fa30f` | 1,655,265 (+18.0% vs item 4; -19.5% vs before) | 3,450,945 (no change) | Provider cost per course by country (`tb_ds_cost`, `tb_dr_cost`, 2023 US$): Value TB facility costing (financial, bottom-up; Ethiopia, India, Kenya, Philippines) and GHCC studies (South Africa); income-group medians pooled with Laurence 2015 elsewhere (DS $275 / $135 / $678, DR $1,568 / $2,818 / $8,028 by income group vs the old $332 / $351 / $1,081 and $1,568 / $8,125 / $6,800). WHO's country RR-TB share of incidence and enrolment replace the global 4% and 45%. `uc_tb_mult` range 0.78-1.60. **TB deaths +91%** (277,104 to 530,032: lower course costs mean more patients per lost dollar; South Africa and India TB more than double), so this item is flagged in the report although the all-disease headline moves +18%. WHO budget-per-patient cross-check within a factor of 3 in 35 of 60 countries. Baseline: 81 entries refreshed; 7 Kenya lives-first entries also moved other lines |
| 6. IMP-04 / L-44 cap rule | ✅ done | `f7fbb88` | 1,379,963 (-16.6% vs item 5; -32.9% vs before) | 3,184,530 (-7.7%; -40.0%) | The donor-funded pool is people covered x the external share of the country's spending on the disease (`donor_share_*`: GHED for HIV, malaria and immunization; WHO TB financing for TB; WHO-region median where missing) instead of everyone covered; units lost = pool x share of money lost where donor money would buy more than the pool. Malaria -48% (external share median 0.25), vaccines -12%, TB -12%, HIV -8%. Labelled: a spending share is not exactly the share of patients donors fund |
| 7. IMP-16 / L-14 continuity | ◐ partly done (value kept) | (this commit) | 1,379,963 (no change) | 3,184,530 (no change) | Evidence from the 2025 cuts was found (KFF: PEPFAR ART "remained relatively stable" at 20.3M vs 20.4M; Cust & Chabata 2026: at four defunded NGOs "treatment by 22% to 32%" lower; WHO: TB treatment "the least affected") but none directly measures the share of patients who keep the same service after its donor funding is withdrawn in an LMIC (service volumes at defunded NGOs under a waiver; programme-wide stocks under partial cuts; a disruption survey), so under the rule set on 14 October 2026 `continuity` stays 0.15 as a labelled assumption; range narrowed from 0-0.35 to 0-0.30; 0.30 recorded as a sensitivity value (`batch34_evidence.md` G). Per-country TB continuity could not be built (no private-sector notification variable in the 2026 WHO file). Only ranges moved (86 baseline entries) |

**First full check.** `audit/checks.py --full` after item 7: 36 failures (`deaths_le_people_affected`, TB treatment
line, El Salvador and Nicaragua under Custom), traced to item 1 and fixed by attributing secondary TB deaths to the
line whose lost patients generated them (totals unchanged; `batch34_evidence.md`, "First full check").

**Final full check** (after the fix and Phase 3, commit `225e532`): `audit/checks.py --full`, 59 checks, 76,501
rows, **0 failures, 6 known warnings** (Section 1 vs Section 2 DAH); 357 tests pass.

**Combined effect of the batch** (all countries, Full US Exit, central): 2,055,422 to 1,379,963 deaths 2026-2030
(-32.9%); HIV 1,096,151 to 669,366 (-39%), TB 472,436 to 463,973 (-2%; -41% after items 1-2, +91% in item 5, -12%
in item 6), malaria 369,425 to 143,889 (-61%), vaccines 117,411 to 102,735 (-12%); further deaths 2031-2035 1,092,054
to 661,961; HIV infections 4,334,929 to 2,802,503; people who stop ART 5,303,707 to 3,184,530 (-40%). No single item
moved the headline by more than 50% and the combined change (-33%) is inside the -50% / +150% band, so no item is
RED; item 5's TB line (+91%) is flagged. Every preset and six countries: `batch34_before_after.md`.

**Phase 3 reconciliation with Optima** (15 overlapping countries, `batch34_evidence.md` Phase 3,
`batch34_reconcile.csv`): the model's share of people on ART who stop under Full US Exit fell from 21% to 13%
(weighted), against PEPFAR's 39% share of HIV spending and 53% for all international funding (Optima Table B2). The
gap is driven by the full-cost conversion (a lost dollar removes 1 / full cost per patient-year people, and the full
cost, US$400-675, is above total HIV spending per person on ART in Kenya, Uganda, Mozambique, Zimbabwe and South
Africa), by the money that now buys no people (systems, programme management, the non-treatment shares of
unspecified money, half of testing and care), by continuity and the cap, and by the 23% Global Fund cut. Not tuned.

**L-50 (Major; ✅ done in Batch 4b, 14 October 2026; floor and validity rules revised in Batch 5+6 item A1).** The ART
full cost per patient-year (site cost x 1 / (1 - asd_share)) exceeded the country's total HIV spending per person on
ART in 5 of the 15 Optima countries; the item D gate had been applied to the site-level value, so Kenya (644) and
Uganda (675) passed it. Batch 4b: the cost used is now the lower of the GHCC-based full cost and observed treatment
spending per person on ART (Optima Table B2 or GHED x the Global Fund treatment share / UNAIDS people on ART; the
regional median ratio where unavailable). Batch 5+6 (A1): observed spending counts only where the Global Fund funds
at least 10% of total HIV spending (the module share is a proxy for the national treatment share; invalid in South
Africa, Nigeria, Namibia, the Dominican Republic, Botswana, Guyana, the Philippines and São Tomé and Príncipe, which
take the regional median ratio over the valid countries); the floor is the lowest measured site-level delivery cost
(Malawi, Rosen et al. 2021, US$86.50 in 2018 US$ = US$105 in 2023 US$) x the same 1.818 above-site markup =
US$190.84, so floor and cost are on one basis (the US$57 TLD-plus-viral-load floor was a commodity price); the
US$50-600 gate is on the final value. Median US$216 (Kenya 308, Uganda 314, Mozambique 227, Nigeria and South Africa
208; 13 countries at the floor). PEPFAR Expenditure Analysis per patient (DR-01) would still settle the level.
`batch4b_evidence.md` items 1-2; `batch56_evidence.md` A1.

## Batch 4b: ART unit cost consistency, malaria and TB explanations (14 October 2026)

Evidence: `batch4b_evidence.md`; scripts `audit/batch4b_art_check.py`, `audit/batch4b_malaria_decomp.py`; before
snapshot `audit/before_batch4b.csv` (local). Headline = all countries, Full US Exit, central, 2026-30 deaths.

| Item | Status | Commit | Headline after | What changed |
|---|---|---|---|---|
| 1 Diagnose the ART cost | ✅ done | `6b652b1` | 1,379,963 (no change) | The item D gate had been applied to the site-level value, so Kenya (644 full) and Uganda (675) passed; observed treatment spending per person on ART (Optima Table B2 or GHED x Global Fund treatment share / UNAIDS people on ART) is available for 43 countries; the GHCC-based full cost is 1.85 times it at the median and above it in 35 of 43 |
| 2 Fix the ART cost (L-50) | ✅ done | `d30ecab` | 1,648,665 (+19.5%) | Cost per patient-year = the lower of the GHCC-based full cost and observed treatment spending per person on ART (regional median ratio where unavailable), floored at drugs plus viral load (US$57; Global Fund 30 August 2023; CHAI 2015) and gated to US$50-600: median US$274. HIV deaths 669,366 -> 938,069; people who stop ART 3.18M -> 4.56M. HIV baseline only rebuilt (83 entries; 13 lives-first entries moved other lines) |
| 3 Explain malaria -61% | ✅ done, one fix | `7342148` | 1,695,601 (+2.8%) | Item 6's cap drove it (-48% of the item-2 level), items 1-2 the rest; systems and management shares match the Global Fund malaria mix by construction. Concept mismatch found and fixed: the all-source malaria spending share (household treatment spending 35% at the median, 87% in Nigeria) gave donor-funded nets a pool of 3% of people covered in Nigeria; bednets and spraying now use the external share of public malaria spending (median 0.56). Malaria deaths 143,889 -> 190,824. Malaria baseline only rebuilt (84 entries) |
| 4 Explain TB | ✅ done | (docs) | no change | The +91% in Batch 3+4 item 5 is the lower course costs (old costs restored: 265,626 vs 463,973); the country RR shares and enrolment are worth -2,000 deaths |

**Checks after Batch 4b.** `audit/checks.py --full`: 59 checks, 76,501 rows, 0 failures, 6 known warnings; 357 tests
pass; `--quick` 0 failures after each item.

**L-51 (Minor, Medium confidence; ✅ done in Batch 5+6 item A2).** The donor-funded pool for HIV and immunization used
the external share of all-source spending; GHED's HIV total is "HIV/AIDS and other STDs" with a private share of 67%
in Nigeria, 49% in Guinea and 44% in Senegal (10 of 40 countries with data have a public-minus-all-source gap above 10
points), and private immunization spending is 37% in Nigeria (5 of 48 countries above 10 points). Batch 5+6: both
lines use the external share of public spending, as bednets and spraying do since Batch 4b. `batch56_evidence.md` A2.

**Updated reconciliation (15 Optima countries):** the model's share of people on ART who stop under Full US Exit is
21% (weighted) after Batch 4b (13% after Batch 3+4, 21% before it), against PEPFAR's 39% share of HIV spending and
53% for all international funding; `batch4b_evidence.md`.

## Batch 5+6: ART cost floor, input shares, malaria cap concept, vaccines, validation, SPEC reproduction (14 October 2026)

Evidence: `batch56_evidence.md`; scripts `audit/batch56_*.py`; before snapshot `audit/before_batch56.csv` (local).
Headline = all countries, Full US Exit, central, 2026-30 deaths. Before the batch: 1,695,601.

| Item | Status | Commit | Headline after | What changed |
|---|---|---|---|---|
| A1 ART cost floor and observed-spending validity (L-50) | ✅ done | `a0c2082` | 1,666,755 (-1.7%) | Observed spending per person on ART counts only where the Global Fund funds at least 10% of HIV spending (35 of 43 countries); elsewhere the regional median ratio over the valid countries. Floor = lowest measured site delivery cost (Malawi, Rosen 2021) x the 1.818 above-site markup = US$190.84 (was US$57, a commodity price); gate on the final value. 43 countries change (median US$274 -> 216); HIV deaths 938,069 -> 909,223; people who stop ART 4.56M -> 4.42M. HIV baseline only rebuilt (42 entries) |
| A2 L-51 input-share check (HIV, immunization) | ✅ done (fix applied) | `b30f4b8` | 1,757,745 (+5.5%) | The HIV and immunization pools use the external share of public spending (GHED), as bednets and spraying do: the private part of GHED's "HIV/AIDS and other STDs" and immunization totals is household spending on STI care and private-sector vaccination, not the donor-funded service. Nigeria HIV share 0.18 -> 0.55 (people who stop ART 184,289 -> 562,261 a year), immunization 0.40 -> 0.63; 10 HIV and 5 immunization countries move by more than 10 points. HIV deaths 909,223 -> 998,535; vaccines 102,735 -> 104,413. HIV and immunization baselines rebuilt (67 entries; PMTCT shares the HIV pool share) |
| A3 Malaria cap concept (IMP-04 follow-up) | ✅ done (fix applied) | `7f07d6b` | 1,843,873 (+4.9%) | The cap is applied per intervention, so the share is the intervention's: people the donor money for bednets / spraying / treatment pays for ÷ people covered, capped at 1 (`donor_share_mal_*`), instead of the external share of all public malaria spending (nets, spraying) or of all-source spending (treatment). Nigeria bednets: donor money pays for 63% of net users, the old share gave 22%. Malaria deaths 190,824 -> 276,952 (bednets 104,023 -> 148,831; treatment 84,075 -> 123,822; spraying 2,726 -> 4,299); Nigeria 16,559 -> 50,470. No country's annual excess exceeds its current malaria deaths (max Zambia 0.28). Net unit cost confirmed per person-year of use. Malaria baseline only rebuilt (84 entries) |
| V1 Vaccine evidence (L-42, L-18) | ✅ done (analysis only) | `fced791` | no change | VIMC deaths averted per vaccinated child by country and antigen (Toor 2021 supplementary data / WUENIC x WPP surviving infants, 2015-19; minimum year for measles, MenA, YF; x Q5 2026-30 / 2015-19), timing by years since vaccination (NNLS fit; under-5 share by pathogen), Toor Table 3 gate (38 of 620 outliers to regional medians); HPV and JE excluded; DTP, polio and BCG excluded for lack of a citable per-child value (dashboard note). `audit/batch56_vaccines.py` |
| V2 Implement vaccines | ✅ done | `7464034` | 1,927,405 (+4.5%) | Deaths per fully immunized child = the VIMC-based country value (median 0.025 lifetime; Kenya 0.021, Nigeria 0.059, India 0.012) by years since vaccination, replacing 0.020 x 0.65 x clip(U5MR / 50) with fixed cohort weights (kept as `imm_legacy_u5mr_scaling`); `imm_dpc_mult` 1 (0.56-1.64) from the VIMC credible intervals; uc_imm unchanged. Vaccine deaths 104,413 -> 187,945 (+80%); vaccine further deaths 21,424 -> 15,243. Immunization baseline rebuilt (73 entries; 13 lives-first entries moved other lines) |
| V3 Vaccine check and first --full | ✅ done | `c53a969` | 1,927,405 | Before/after for every preset and the six focus countries (`batch56_before_after.md`, `batch56_evidence.md` V3); first `--full`: 59 checks, 76,501 rows, 0 failures, 6 known warnings; 352 tests pass, 5 fail (test_late_vaccine_cut_committed asserts the pre-batch cohort weights; not edited, see `batch56_evidence.md` V3) |
| VAL1 Validation (IMP-19, L-47) | ✅ done (no model change) | `a4cd2c2` | no change | `validation.md`: HIV vs Optima Table C2 (15 countries; deaths 0.39, infections 0.36 of Optima's PEPFAR-discontinued excess; Kenya 1.04, South Africa 0.18, Tajikistan 3.65 flagged with explanations), people on ART vs UNAIDS (median 1.00), TB excess as a share of WHO deaths (median 9%, Mozambique 79%), TB cost vs programme budget per patient (median 0.47; 33 flagged), malaria excess as a share of WMR deaths (median 6%, max Zambia 28%), vaccines vs Toor Table 3 by antigen, context studies with scopes, UNAIDS year per country. Validation section on the Methods page |
| VAL2 Independent SPEC reproduction | ✅ done | `a9853ab` | no change | A separate agent rebuilt the four cases for five countries from `docs/SPEC.md` and the data files only: 1,980 of 1,980 cells within 0.5% (largest difference 0.0000%); 23 ambiguities listed, six SPEC clarifications, no model bug (`batch56_evidence.md` VAL2) |
| DOC Changelog | ✅ done | `041d7f4` | no change | `MODEL_CHANGELOG.md`: every parameter, input and rule changed across Batches 1, malaria under-5, 2, 3+4, 4b and 5+6 with old and new values, sources and commits; open items and known limitations |

**Checks after Batch 5+6.** `audit/checks.py --full` twice (after V3 and at the end): 59 checks, 76,501 rows, 0 failures, 6 known warnings each time; `--quick` 0 failures after every model item. Tests: 352 passed and 5 failed by design at the end of the batch (`test_late_vaccine_cut_committed` asserted the pre-batch vaccine cohort weights; not edited then). Test test_late_vaccine_cut_committed updated from the superseded 60% assumption to the VIMC-based timing rule (approved). 357 tests now pass. Combined effect (Full US Exit, all countries, central): deaths 2026-30 1,695,601 -> 1,927,405 (+13.7%); HIV 938,069 -> 998,535; TB unchanged 463,973; malaria 190,824 -> 276,952; vaccines 102,735 -> 187,945; further deaths 2031-35 933,796 -> 990,588; HIV infections 3.79M -> 3.97M; people who stop ART 4.56M -> 4.86M a year. No item moved the headline by more than 5.5%, so none is RED.

## Summary

| Area | Result |
|---|---|
| Inputs reviewed | **98**.<br>- Concept match: exact 23, close 20, **mismatch 4**, not applicable 51 (parameters and constants; judged in Part 2).<br>- Status: sourced 49, derived 10, assumption 15, hard-coded constant 24.<br>- Currency: 33 data inputs current. 2 one release behind (DTP3, HIV incidence). 6 dated studies or series (ART, TB and DR-TB costs, vaccine delivery cost, GBD-2019 HIV death share, 2021-23 aid base years). |
| Country selection | 71 countries receive **71.5%** of country-coded HIV, TB, malaria and vaccine aid. 18% is coded "Global". Myanmar, Ukraine, Afghanistan, Sudan, Chad and Yemen are missing. No documented selection rule. |
| Assumptions by class | **(a)** supported 15; **(b)** evidence suggests a different value 9; **(c)** genuine assumption 22; **(d)** data exists 7 |
| Sensitivity | 42 inputs varied one at a time; 20 largest in `tornado.png`. Top 4: `art_hazard_mult` -18.6% / +23.3%; `continuity` +18.0% / -23.8%; `asd_share` +17.8% / -12.2%; `hss_kappa` -10.1% / +16.2%. |
| Dashboard numbers reproduced | **1,860 of 1,860 cells within 0.5%**: independent implementation, 5 countries x 4 cases, largest difference 0.17%. `audit/checks.py --quick`: 55 checks, 0 failures. |
| Claims reviewed | **18**: 8 supported, 5 need a qualifier, 5 overclaim or wrong |
| Benchmarks compared | **12** (Cavalcanti; Optima; UNAIDS; Clark; Mandal; MAP/PMI; Gavi; WHO HIV, TB and malaria burden; Thembisa; CEPAC). 2 gaps not fully explained: HIV infections (L-41), vaccine deaths per dollar (L-42). |
| Red-team points | **20**: 9 already found, 6 partly found (extended), 5 new (L-43, L-44, L-45, L-46, L-47). All resolved; 3 disagreements recorded (`redteam.md`). |
| Reproducibility | All of `model_data/`, including the 6 precomputed All Countries files, rebuilt **byte-identical** from `datasets/` in a clean environment. `country_inputs.csv` is numerically identical (float printing differs). Sections 1-3 per-country files **cannot be rebuilt** (scripts not in the repository). |
| Improvements proposed | **24**: Do now 7; Do before presenting 11; Nice to have 6 |
| Findings | **48**: Critical 2; Major 12; Minor 23; Presentation 11 |

## All findings

**Severity:**
- **Critical:** changes a headline number by more than 10%, or uses the wrong concept for a major input.
- **Major:** 3-10%, or the wrong concept for a minor input.
- **Minor:** under 3%.
- **Presentation:** labels, explanation or claims only.

**Confidence:** High = verified against a primary source or code; Medium = secondary or indirect; Low = judgment.

**Effects:** on all-country deaths 2026-2030, Full US Exit, no government response (base 1,969,304), unless stated.

| ID | Severity | Conf. | Finding and evidence | Effect (tested where possible) | Proposed fix | Needs your data? |
|---|---|---|---|---|---|---|
| L-01 ✅ done (Batch 2, Option A: see the status section) | **Critical** | High (concept), Medium (size) | ART death hazard calibrated as 17% x 20.6M PEPFAR-supported patients (`model_params.csv` art_hazard_mult), applied to 5.30M full-cost equivalents (`health_model.py:438-450`, `:856-858`). HIV deaths 1.01M, about a third of Optima's PEPFAR-ending scenario (2.93M) and a quarter of UNAIDS (>4M). See `URGENT.md`. | Consistent readings: +7% to +115% (Brinkhof 20-60% risk; tested: 2.11M / 3.17M / 4.23M); reading B about +130% | IMP-01: pick one reading, calibrate, show both | No (A); DR-01 (B) |
| L-41 ◐ partly done (Batch 2: per-country transmission and a second generation; infections 4.3M vs UNAIDS 6M, Optima overlap gap open: L-49) | **Critical** | High (gap), Medium (cause) | HIV infections 1.55M vs Optima 4.43-10.75M and UNAIDS 6M. `art_transmission` was calibrated per supported patient, like L-01. | Reading B: about 3.7M off-ART infections (+140% or more) | IMP-01 | No |
| L-43 ✅ done with stated gap (Batch 3+4 item 2; Batch 7 item 1: 34 of 210 lines on WHO-region medians, capped lines listed in `batch7_evidence.md`) | Major | High (mechanism), Low (size) | Unspecified money is spread to services only. TB: US$700M of US$1,522M (46%) becomes patients; effective TB service money is 3.7x the tagged amount. Tajikistan extra TB deaths are 108% of current TB deaths a year. | Est. -5% to -8% (not run) | IMP-02 | No |
| L-44 ✅ done (Batch 3+4 item 6: donor-funded pool capped at the external share of disease spending) | Major | High (mechanism), Medium (size) | Proportional-cap rule (`_units_lost`, `health_model.py:438-450`) treats all covered people as donor-funded when donor money ÷ cost > covered. 160 of 695 lines (Validation page). | Est. -3% to -5% (red team; not run) | IMP-04 | DR-04 |
| L-05 | Major | Medium | `hss_kappa` (assumption, no evidence found) converts systems and testing & care money into patients at a cost already marked up by 1/(1-asd): above-site costs counted twice. | Swing -10.1% / +16.2%; kappa = 0 gives -20% (red team) | IMP-02 | No |
| L-14 ◐ partly done (Batch 3+4 item 7: evidence reviewed, value kept at 0.15 by rule; 0.30 is a sensitivity value) | Major | Medium | `continuity` 0.15 is one global value with no source. PEPFAR FY25 ART counts were "stable" after the 2025 cuts (KFF). Large private TB sectors (India: 33% of notifications). | Swing +18.0% / -23.8% | IMP-16 | DR-02, DR-07 |
| L-04 ✅ done (c6dd075) | Major | High | Malaria effect sizes (Eisele 2010; Thwing 2011) are for children 1-59 months but are applied to all-age deaths. | **-4.9%** (tested: 1,872,379) | IMP-05 | No |
| L-20 ✅ done (c6dd075) | Major | High | `mal_cm_eff` 0.82 is the severe-malaria effect, applied to effective treatment of all cases. LiST uses 99% for uncomplicated malaria with ACT (Thwing 2011). | +4.1% at 0.99 | IMP-05 | No |
| L-06 | Major | High | Aid baseline 2021-23, but US health aid fell 67% in 2025 (IHME FGH 2025). Coverage is 2024-25, a mix of years. Cuts that began in 2025 start the hazard clock in 2026. IHME has no recipient detail after 2023 (checked). | Aid at Risk overstated for US scenarios (tens of %); deaths relative to 2021-23 service levels | IMP-06 | DR-03 |
| L-08 ◐ partly done (576a8d8 (the MOU preset now says co-financing is not modelled; not implemented)) | Major (MOU preset) | High | The MOU preset ignores partner co-financing commitments, which are the defining feature of the MOUs (KFF tracker). | MOU preset deaths (360K) overstated wherever co-financing is delivered | IMP-08 | DR-12 |
| L-28 ◐ partly done (752f611 (label only: renamed and described as total-aid cuts; the cuts themselves are unchanged)) | Major (OECD preset) | High | OECD total-ODA changes are applied to health aid. IHME health-specific changes differ (UK -39% vs -10.8%; France -33% vs -10.9%). Labelled in the app. | OECD preset: country and donor mix wrong; total direction unknown | IMP-14; use IHME donor x disease ratios | No |
| L-18 ◐ partly done (Batch 5+6 V2: deaths per child are now the sum over the antigens the country uses, from VIMC; the unit is still a full-schedule child at US$87) | Major | Medium | Vaccine units are full-schedule children at US$87, but Gavi money buys specific newer vaccines. Losing it rarely means losing DTP3 entirely. | Unknown; see L-42 | IMP-15 | DR-05, DR-09 |
| L-42 ✅ done (Batch 5+6 V1-V2: VIMC deaths averted per vaccinated child by country and antigen; vaccine deaths +80%; DTP, polio and BCG still excluded, stated as a floor) | Major (under) | Medium | Vaccine deaths per dollar are 3-10x below Gavi's own claim (more than a million deaths if the US withdraws about US$1.58B). Part is scope (under-5 vs lifetime). | Vaccines are 6% of deaths; could rise severalfold | IMP-15 | DR-09 |
| L-33 ✅ done (f8566e4) | Major (2031-35 number) | High | "Further deaths 2031-35" depend mostly on `art_reengage` 0.5, an assumption. Most deaths from new HIV infections fall after 2035. | 2031-35: 298,801 (0.75) to 850,819 (0.25) vs 494,715 | Label as assumption-driven; show the range | No |
| L-02 ✅ done (581c013) | Presentation | High | Ranges are parameter-only but labelled "95% interval" (at least 10 places). The all-country range sums country percentiles: 1.34-2.81M vs the correct 1.39-2.70M. | Range 11% too wide; real uncertainty far larger (L-01) | IMP-09, IMP-10 | No |
| L-03 ◐ partly done (576a8d8 (scope stated in the All Countries tooltip; no countries added)) | Presentation | High | Country scope: 71.5% of country-coded disease aid. Large recipients missing; no documented selection rule. | Totals understate "all LMICs" | State the scope; IMP-23 | No |
| L-07 | Minor | High | 8 countries use an under-5 bednet survey for the whole population. 31 use a 50% default, though older surveys show 4-31% (Indonesia, Namibia, Botswana). | about 0 on deaths; credibility | Use the latest survey with decay, or 0 | No |
| L-09 | Minor | Medium | Gavi -15% default is "our estimate"; Gavi 6.0 has only US$6B in new pledges (Donor Tracker). | Preset only | Keep the label; IMP-13 | No |
| L-10 ✅ done (911fbfe) | Minor | High | `trend_tb_deaths` is defined (`health_model.py:423`) but never applied. TB and HIV counterfactuals are flat while malaria and vaccines trend. | small | Apply it or remove it, and document | No |
| L-11 | Minor | High | `hiv_deaths_est` (Validation, Lancet comparison) uses the GBD-2019 HIV share via Gapminder. Honduras comes out at 85 a year. | Validation page only | Use UNAIDS 2025 deaths | DR-06 |
| L-12 ✅ done (911fbfe) | Minor | High | TB detection rate can exceed 100% by definition (WDI). None does now; there is no guard. | 0 now | Clip at 1 and flag | No |
| L-13 ✅ done (911fbfe) | Minor | High | HIV+ TB untreated CFR = 0.62(1-0.3a) approximates WHO Table 5 (0.78 off ART; 0.49 at 1 year or more on ART). | under +1% | 0.78(1-a) + 0.49a | No |
| L-15 | Minor | High | TB: the whole 10-year case fatality is put in the year of loss (WHO: untreated duration about 3 years). Secondary cases all arrive 1-2 years later. | 2026-30 TB deaths overstated by a few %; moved to 2031-35 | IMP-11 | No |
| L-16 ✅ done (Batch 3+4 item 5: Value TB short-regimen and GHCC DR costs; WHO country RR-TB shares and enrolment) | Minor | High | DR-TB costs from single 2014 studies, pre-BPaLM (GDF US$284 per course), not monotone by income. Global 4% share and 45% coverage, though Central Asia's share is far higher. | about ±0.2% | IMP-03, IMP-11 | DR-02, DR-08 |
| L-17 ✅ done (Batch 7 item 3: `immunization_inputs.py` reads WUENIC 2025 directly) | Minor | High | DTP3 2024 via the WDI mirror; WUENIC 2025 was released July 2026. | small | Download WUENIC directly | DR-05 |
| L-19 ✅ done (Batch 5+6 V2: replaced by the WPP Q5 2026-30 / 2015-19 ratio on VIMC country values; the old scaling is the legacy switch) | Minor | Medium | Vaccine deaths scaled by clip(U5MR/50, 0.3, 2.5): our assumption. | Swing in `imm_*` about ±1% | VIMC by country | DR-09 |
| L-21 | Minor | High | MAP IRS is "the proportion of household sprayed", used as the share of people. | under 0.5% | Note it, or convert | No |
| L-22 | Minor | Medium | The IRS max() rule credits money-implied spraying where MAP shows none (Nigeria 0% since 2018). | under 0.1% (Nigeria spraying deaths 1,276) | Use MAP where it exists | No |
| L-23 | Minor | High | MAP vs WHO malaria cases differ by more than 30% in 20 of 46 countries (Pakistan 14.4M vs 3.15M). | -0.5% with WHO cases | Document; show both | No |
| L-24 | Minor | High | Need (births, PLHIV, incidence) held at the latest year, 2026-2030. | +2% to +5% where caps bind | IMP-17 | DR-10 |
| L-25 ✅ done (719ff89) | Minor | Medium | Malaria death trend = Pf case trend clipped ±5% (clip unsourced). It compounds with resurgence in high-trend countries. | -0.8% / +0.1% | IMP-18 | No (on disk) |
| L-27 (open: IMP-02c BLOCKED, Batch 3+4) | Minor | Low | Testing & care money (US$760M/yr) is counted as lost ART at kappa; it funds a flow of new initiations, not a stock. A flow formulation needs a cost per initiation (none found) and raises the count rather than lowering it (`batch34_evidence.md` C). | inside L-05 | IMP-02 | No |
| L-29 | Minor | Medium | Fiscal capacity is one strong year's growth held flat for 5 years, not cumulative. Stress thresholds unsourced. | 0 on default headlines | Cumulative capacity; cite IMF DSF | No |
| L-31 | Minor | Medium | WEO vintage of `macro_data` is untagged. WDI revenue and debt are central government only, missing for 18 and 41 countries. | display only | Tag the vintage | No |
| L-32 | Minor | Low | `uc_pmtct` 250: the cited review's figures could not be verified. | ±1.5% | Verify or replace | No |
| L-34 | Minor | High | Interest burden mixes IMF net general-government interest (53 countries) and WDI gross central-government interest (17). | fiscal panel only | Document; prefer one | No |
| L-35 | Minor | High | MOU amounts are nominal against a nominal reference, so inflation over 2026-30 is uncounted. Schedules ending 2028 are held flat; increases are counted as 0. | MOU preset understated by about 2-3% a year in real terms | Deflate | No |
| L-38 | Minor | High | Sections 1-3 per-country files can't be rebuilt (scripts not in the repository). | reproducibility | IMP-12 | No |
| L-39 | Minor | High | India's TB systems and unspecified money goes mostly to DR-TB (by own-money mix) at US$14,773 per patient. India's TB card: 638 deaths per US$1M vs about 2,000 elsewhere. | India only | Spread by patients or by the WHO DS/DR split | No |
| L-26 ✅ done (ba496d1) | Presentation | Medium | `asd_share` 45% cited to "PEPFAR 2014", not found. KFF 2025 reports 47%. | none | Fix the citation | No |
| L-30 ✅ done (8b89420) | Presentation | High | "Lives first (triage)" is an optimisation rule, not observed behaviour. | none | Label "hypothetical best case" | No |
| L-36 ✅ done (cff29af) | Presentation | High | `audit/METHOD.md` gives a different ART-units formula from the code. Kenya: 451.7k (code) vs about 328k (METHOD.md). | documentation | IMP-20 | No |
| L-37 ✅ done (cff29af) | Presentation | High | `logic.md` was not enough to reproduce on its own: the independent reproducer needed 12 items from METHOD.md. | documentation | IMP-20 | No |
| L-40 ✅ done (c56214a) | Presentation | High | "People Losing Care Each Year" sums full-cost-equivalent ART patients, bednet person-years and malaria episodes as people (Kenya: 4.90M of 6.10M are bednet users). | none | Relabel, or split treatment vs prevention | No |
| L-45 ✅ done (752f611) | Presentation | High | "Full US Exit" keeps 77% of the US Global Fund pledge and ignores signed MOUs. | none | IMP-14 | No |
| L-46 ✅ done (752f611) | Presentation | High | The IHME 2025 preset is called "Data-driven", but the country split is a uniform global ratio. | none | IMP-14 | No |
| L-47 ✅ done (Batch 5+6 VAL1: like-for-like comparisons with a stated 0.5-2x band, TB and malaria benchmarks, Gavi row labelled as a VIMC-based comparison, flags explained; `validation.md`) | Presentation | Medium | The Validation page is framed to pass ("should come in below"). The Optima row shows 0.77-2.93M as comparable, though 2.93M is the PEPFAR-ending scenario. The Gavi row is circular. No TB or malaria benchmark. | none | IMP-19 | No |
| L-48 ✅ done (576a8d8) | Presentation | High | Headline and Methods claims overstate certainty (claims C1, C4, C5, C9, C17 in `dashboard.md`). | none | IMP-21 | No |

## The 10 most important findings, ranked

1. ✅ **L-01 (Critical; done, Batch 2).** The ART death risk is calibrated per supported patient but applied per full-cost
   equivalent. HIV deaths are about a third of the comparable Optima scenario. Every consistent reading raises the
   headline: +7% to +130%.
2. ◐ **L-41 (Critical; partly done, Batch 2).** HIV infections are 3-7x below published estimates, for the same reason.
3. **L-43 (Major).** Unspecified disease money (46% of TB aid) is counted entirely as patients' treatment. TB is
   likely overstated, with impossible country results (Tajikistan 108% of current TB deaths).
4. **L-05 (Major).** Above-site costs are counted twice: markup plus kappa conversion of systems money. This is the
   fourth-largest sensitivity and has no evidence behind it.
5. **L-14 (Major).** Continuity is the second-largest sensitivity, a single unsourced value. The 2025 PEPFAR data
   suggest it is higher in the short run.
6. **L-44 (Major).** The cap rule treats all covered people as donor-funded in 160 lines.
7. **L-06 (Major).** The 2021-23 baseline vs cuts that happened in 2025: "Aid at Risk" includes money already gone,
   and the hazard clock starts a year late.
8. ✅ **L-02 (Presentation, high visibility; done 581c013).** "95% interval" describes parameter noise only. The real uncertainty is
   several-fold larger.
9. ✅ **L-04 + L-20 (Major; done c6dd075).** Malaria effect sizes: the wrong age group (-4.9%) and the wrong treatment effect (+4.1%).
10. **L-42 / L-18 (Major).** The vaccine pathway uses full-schedule costs and effects. It is likely conservative by a
    large factor relative to Gavi and VIMC.

## The 10 most valuable improvements, ranked (details in `improvements.md`)

1. **IMP-01.** Resolve the ART and infection concept; show readings A and B (Do now).
2. **IMP-02.** Spread unspecified money over services and systems; one treatment of above-site costs (Do before
   presenting).
3. ✅ **IMP-10 + IMP-21** (done 581c013, 576a8d8). Honest range labels, all-country range from summed draws, claims wording (Do now).
4. **IMP-04.** Cap the donor-funded share with GHED or PEPFAR data (Do before presenting).
5. ✅ **IMP-05** (done c6dd075). Malaria effects on under-5 deaths; LiST treatment effect (Do now).
6. **IMP-19.** Like-for-like Validation with acceptance bands; add TB, malaria and South Africa benchmarks (Do before
   presenting).
7. **IMP-06.** 2025 aid baseline option from ForeignAssistance.gov, Global Fund and Gavi data (Do before presenting).
8. **IMP-16.** Country-specific continuity (TB private sector; PEPFAR TX_ML) (Do before presenting).
9. **IMP-03.** Country unit costs (GHCC; Sweeney 2024; PEPFAR Expenditure Analysis; BPaLM) (Do before presenting).
10. **IMP-08.** MOU co-financing as the MOU preset's default response, in real terms (Do before presenting).

## What we can and can't claim

### Supported by the model and the evidence, with suggested wording

- **Direction and order of magnitude.** "Under a sustained end of US health aid with no replacement, the model
  estimates on the order of 2 million extra deaths from HIV, TB, malaria and vaccine-preventable disease in these 71
  countries over 2026-2030."
  - Supported: the central run is 1.97M. Every correction found moves the total in a band of roughly 1.5M to 4.5M (the downward corrections L-04, L-05, L-43 and L-44 together about -25%; L-01 up to +130%),
    and published models for HIV alone reach 2.9-4M.
  - State it as "on the order of", not a precise number.
- **Cross-country pattern.** "The largest losses fall in countries where donors pay for most HIV and TB treatment:
  Mozambique, Nigeria, Tanzania, South Africa, Kenya, Uganda and the DRC."
  - Robust to every alternative tested: L-01 raises these countries most.
- **HIV is the largest single source.** "Most of the extra deaths come from people losing HIV treatment."
  - Robust: L-01 raises HIV's share from 51% to 54-78%. L-43 lowers TB.
  - Don't quote a precise percentage.
- **TB and malaria per dollar.** "Per dollar, TB treatment and malaria programs avert the most deaths."
  - Consistent with the cost-effectiveness literature.
  - Hedge for TB (L-43, L-44). India is an exception for a data reason (L-39).
- **Past replacement.** "In past aid declines (2001-2023), governments on average did not raise their own health
  spending to compensate."
  - Supported by the regression: θ = -0.19, 95% CI -0.45 to +0.07.
- **Fiscal room.** "Few governments could fill the gap from fiscal space alone: the model's estimate of yearly room
  is small next to the loss (Kenya: about US$21M against US$278M)."
  - Supported as a model statement; capacity rule L-29.
- **Benchmarks.** "The totals sit below all-cause estimates (Cavalcanti et al.), because the model counts four
  disease areas in 71 countries."

### Not supported, or not at the stated strength

- **A precise death count, or a "95% interval".** Ranges are parameter-only (L-02). Structural choices (L-01, L-05,
  L-43) move results far more.
  - Instead: "about 2 million (range across parameter values 1.4-2.7 million; structural choices could put it
    between about 1.5 and 4.5 million)."
- **"N people will lose HIV treatment."** Units are full-cost equivalents, not headcounts (L-01, L-40).
  - Instead: "the lost money would have paid for treatment for about N people".
- **HIV infections.** "1.6 million new HIV infections" is 3-7x below published models (L-41). Don't present it until
  L-01 is resolved.
- **TB deaths per country.** Not reliable for Tajikistan, Cambodia, Mozambique and India until L-43, L-44 and L-39 are
  fixed.
- **Vaccine deaths.** Likely understated (L-42). Present them as a conservative lower estimate.
- **"Between Optima and UNAIDS."** False as calibrated (L-01). Validation agreement with Optima is partly a
  coincidence of offsetting errors (L-47).
- **OECD preset as "OECD-reported health cuts".** It applies total-ODA cuts (L-28).
- **MOU preset as "the effect of the MOUs".** It omits the co-financing that defines them (L-08).
- **"Further deaths 2031-2035" as committed deaths.** It mostly reflects an assumed re-engagement rate (L-33), and it
  excludes most deaths from new infections after 2035.
- **Totals for "low- and middle-income countries".** The model covers 71.5% of country-coded aid and none of the
  "Global" share (L-03).

## Known omissions and their direction of bias

From `uncertainty_scope.md` Part 4b.

| Omission | Bias in extra deaths | Rough size |
|---|---|---|
| Other health aid (maternal and child health beyond vaccines, nutrition, family planning, NTDs, WASH) | Under | Cavalcanti covers all causes: about 7x the model, mostly scope |
| Countries not on the dashboard, and "Global" aid | Under | 28.5% of country-coded disease aid; maybe +10-25% |
| Supply-chain, data-system and surveillance collapse beyond kappa | Under | unquantified |
| Deaths after 2035 (new HIV infections; lost epidemic control) | Under | most deaths from 1.55M+ infections fall after 2035 |
| Other donors or governments stepping in (beyond the response options) | Over | 2025 PEPFAR ART counts were stable (KFF) |
| Behavioral responses (private care) beyond 15% continuity | Over | continuity swing ±20% |
| Population and epidemic growth in need | Under | +2-5% |
| Price falls (BPaLM, cheaper nets, lenacapavir) | Over or under | small |
| Drug resistance after interruptions | Under, long term | unquantified |
