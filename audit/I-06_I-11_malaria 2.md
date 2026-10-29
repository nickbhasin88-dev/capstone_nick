# Malaria batch: I-06 and I-11 Fixed; I-27 and I-17 partly fixed (malaria)

## Data

- **Malaria Atlas Project (MAP)**, national unit data, data.malariaatlas.org, downloaded 2026-10-13. The raw files are
  in `datasets/` (never committed).
  - `malaria_inputs.py` saves the series the model uses to `ext_data/map/` (committed), each row tagged with source
    and download date.
  - Files: `treatment` (Effective Treatment per 100 cases), `itn` (Access, Use, Use Rate), `irs` (Coverage, in 100
    households), `pf_cases` and `pv_cases` (Clinical Cases), `incidence_prevalence`. All cover 2000-2025; ITN covers
    40 countries, the rest 106.
  - MAP's 2025 values repeat 2024 for treatment and ITN.
  - The IRS file models Africa only: 62 countries (the Americas, Asia, the Middle East) are 0 in every year, which is
    read as "no estimate", not "no spraying".
- **WHO World Malaria Report 2025** (`datasets/WHO_World_Malaria_Report_2025.pdf`, ISBN 978-92-4-011782-2): 610,000
  malaria deaths in 2024, 12,000 more than in 2023; case incidence up 8.5% from 2015 to 2024; Ethiopia among the largest
  increases.
- `malaria_inputs.apply()` runs last inside `who_inputs.apply()`, so a full `prepare_model.py` rebuild gives the same
  inputs. Checked: applying it to the old `country_inputs.csv`, or again to the new one, reproduces the committed file
  exactly.

## I-11: malaria coverage baselines

Countries per source: 70 dashboard countries, of which 46 have malaria deaths.

| Input | MAP 2025 | Fallback | Default |
|---|---|---|---|
| A. Treatment coverage (`mal_cm_cov`) = MAP effective treatment / 100 | 61 (all 46 malaria countries) | survey rule: 0 | 9: EGY, FJI, JAM, JOR, LBY, LSO, MDA, MNG, MUS (no malaria deaths) |
| B. Cases needing treatment = MAP Pf + Pv clinical cases | 61 (all 46) | WHO estimate 2, derived 7 (no malaria deaths) | - |
| C. Bednet use (`mal_itn_cov`) = MAP ITN "Use" | 31 | survey from 2015 on: 8 (GUY, HTI, IND, LAO, PAK, PNG, STP, TLS) | 31; among malaria countries 9: BGD, BOL, BWA, IDN, NAM, NPL, PHL, VEN, ZAF |
| D. Spraying coverage (`mal_irs_cov`) = MAP household IRS coverage | 36 (35 malaria countries) | no MAP estimate: coverage = people donor IRS money pays for / people at risk (34; 11 malaria countries) | - |

**A. Treatment coverage.**
- `sh_mlr_tret_zs` is no longer used where MAP has a value. The old "incidence >= 50 per 1,000" survey rule now applies
  only to non-MAP countries, and none of them has a usable survey.
- `mal_cm_eff` is unchanged. MAP measures who receives an effective drug; `mal_cm_eff` measures how much that reduces
  deaths. These are separate steps, as in the Lives Saved Tool.

**D. Spraying coverage.**
- Combined vector control in the Lives Saved Tool formula: C_v = 1 - (1 - ITN use)(1 - IRS coverage). Each falls by
  its own people losing the service / population at risk.
- The vector-control deaths are split between nets and spraying by how much each one's fall lowers C_v.
- The old shared pool (spraying reused bednet coverage) is removed; each line is capped at its own coverage x
  population at risk.

**Denominators and unit costs.**
- **Bednets:** people at risk (WHO: cases / incidence per 1,000 at risk) x ITN use = people sleeping under a net, at
  US$2.2 per person-year of net use. Consistent.
- **Spraying:**
  - MAP counts households sprayed; the model applies that share to people at risk, at US$8.5 per person protected.
    This assumes household and population coverage are about equal.
  - In 24 country-lines (all African), donor IRS money exceeds cost x people sprayed: MAP shows little or no
    spraying in 2025, e.g. Nigeria 0% since 2018, Benin 0% since 2022, Burkina Faso 0% since 2021.
  - There the existing rule applies: the loss scales with the share of donor money lost, capped at the people
    covered. So Nigeria's spraying deaths go to 0.
- **Treatment:** MAP Pf + Pv cases x effective-treatment share = cases treated, at US$14 per case (I-27).

**E. Display.** Every malaria coverage value shows its source and year, e.g. "58% → 30% (MAP 2025)", "18% (survey
2017)", "50% (assumed)", "(implied by donor spending)".
- Where it appears: the service table and the coverage chart. A test checks that Kenya's table shows "(MAP 2025)" three
  times.
- Bednets and spraying are now separate rows, since their coverages differ.
- The malaria per-US$1M card, which prices bednets only, is titled "Bednets". Its full rework is I-04.

## I-06: baseline malaria death trend

- Trend = annual change in MAP *P. falciparum* clinical cases, 2015-2025 (log-linear fit, at least 5 positive years),
  clipped to ±5% a year, applied to baseline malaria deaths in 2026-2030. 0 where MAP has no Pf data.
- *P. falciparum* causes nearly all malaria deaths, and no MAP mortality series exists.
- Under-5 mortality keeps its 2010-2019 trend.
- **Clipped: 19 of 46 malaria countries** (10 at +5%: AGO, BOL, DJI, ETH, HTI, IDN, MDG, PAK, STP, ZMB; 9 at -5%:
  BGD, BWA, IND, LBR, NAM, NPL, VEN, ZAF, ZWE). The old trend (WHO deaths 2010-2019, -8% to +2%) had 13 at -8% and 12
  at +2%.
- Examples:
  - Ethiopia -8.0% → +5.0% (fit +10.7%);
  - Pakistan -8.0% → +5.0% (fit +29%);
  - Nigeria -0.4% → +2.3%;
  - Kenya +1.1% → +1.0%;
  - Uganda -5.8% → +1.6%.
- Methods cites MAP and the World Malaria Report 2025 (the 8.5% incidence rise, 610,000 deaths, Ethiopia).

## I-27 (malaria part): treatment cost

- `uc_mal_cm` = US$14 (5-34), status "sourced" (was US$8, 5-15, assumption).
- Source: White et al. 2011, *Malaria Journal* 10:337: median financial cost per uncomplicated case treated $5.84
  (2.36-23.65) + diagnosis $4.32 (0.34-9.34), 2009 US$, x1.42 (CPI-U) = $14.4. ACT and RDT prices have fallen since.
- **Range note:** the 5-34 range is as specified. Summing the study's ranges gives $3.8-$46.8 after inflation, so the
  range is narrower than the study's extremes.
- **Malaria-treatment lines where donor money > cost x cases covered: 51 → 33.**
  - Bednets: 16 → 14.
  - Spraying: 1 → 24, because spraying is now capped by MAP's own spraying coverage (see D).
  - All lines: 200 → 203.
  - A tie tolerance was added to this flag: where spraying coverage is defined as what donor money buys, equal
    values had been flagged by floating-point noise. The flag feeds only the Validation count, not any model number.
  - PMTCT (50) is left for the HIV batch.

## I-17 (malaria part): data years

- New "Data Years" table on the Methods page and on the Validation page (`model_section.data_years_table`). It
  computes each input's year from `country_inputs.csv` (most common year, range and countries per source), so it
  cannot drift from the data.
- Malaria coverage (treatment, bednets, spraying) and cases are listed as MAP 2025. The malaria trend is listed as MAP
  Pf cases 2015-2025.
- The Methods "Time Periods" table is updated to match.

## Validation page

- **New section: "Malaria Inputs: Malaria Atlas Project 2025 vs Previous Sources".**
  - The table shows, per malaria country, what the model used before and now for treatment and bednets (with source
    and year), and cases before (WHO) vs MAP 2025.
  - **20 of 46 countries** have cases that differ by more than 30% (flagged): BGD, BOL, BWA, DJI, ETH, GUY, HTI, IDN,
    MDG, MLI, NAM, NPL, PAK, PHL, PNG, RWA, SEN, VEN, ZAF, ZWE.
  - The largest relative differences are in low-burden countries (South Africa 735 → 12K, Bangladesh 16K → 107K).
  - Among high-burden countries:
    - Pakistan 3.15M → 14.41M;
    - Madagascar 8.17M → 4.06M;
    - Ethiopia 12.4M → 16.7M;
    - Mali 8.5M → 5.9M;
    - Rwanda 1.10M → 0.56M.
- **Baseline malaria deaths:** the 70 dashboard countries' baseline malaria deaths (WHO, mostly 2024) add up to
  **572,719, 94% of WHO's 610,000** global deaths in 2024. The dashboard is a subset of countries; the high-burden
  African countries are nearly all included.

## Before / after

`audit/snapshot_numbers.py` saved every displayed number before and after (8,470 runs, 355 values each, plus the All
Countries files). `audit/malaria_diff.py` attributes every change.

- **3,006,850 values compared; 209,571 changed beyond rounding; none unexplained.** Every change is in a malaria line,
  bucket, path or card (164,583), a total that includes malaria deaths (44,958), or an All Countries sum (30).
- HIV, TB and immunization lines, aid amounts, fiscal values and break-even did not change. The snapshot's responses
  are all pro-rata, so the allocation of government money does not depend on malaria.

**Countries** (Full US Exit, no government response, sudden cut; coverage before → after; extra deaths 2026-2030):

| Country | Treatment coverage | Treatment deaths | Bednet use | Bednet deaths | Spraying coverage | Spraying deaths | Malaria deaths | All deaths | Malaria card: deaths per US$1M a year over 5 years |
|---|---|---|---|---|---|---|---|---|---|
| Nigeria | 44% → 56% | 34,908 → 24,645 | 41% → 28% | 42,053 → 40,692 | 41% → 0% | 1,822 → 0 | 78,783 → 65,337 | 247,759 → 234,313 | 976 → 945 |
| DR Congo | 29% → 42% | 16,089 → 14,051 | 61% → 46% | 31,946 → 30,201 | 61% → 0% | 193 → 1 | 48,228 → 44,253 | 129,983 → 126,008 | 885 → 836 |
| Uganda | 62% → 72% | 9,791 → 8,316 | 69% → 68% | 6,625 → 7,296 | 69% → 9% | 1,167 → 454 | 17,583 → 16,066 | 143,006 → 141,489 | 441 → 477 |
| Mozambique | 33% → 53% | 5,802 → 6,933 | 51% → 43% | 6,551 → 5,374 | 51% → 10% | 954 → 588 | 13,308 → 12,895 | 207,339 → 206,926 | 644 → 619 |
| Burkina Faso | 51% → 60% | 9,331 → 6,855 | 53% → 50% | 8,221 → 9,639 | 53% → 0% | 479 → 0 | 18,031 → 16,494 | 24,302 → 22,765 | 778 → 912 |
| Tanzania | 36% → 66% | 14,718 → 19,240 | 57% → 62% | 11,562 → 12,536 | 57% → 1% | 998 → 142 | 27,278 → 31,918 | 178,572 → 183,212 | 548 → 589 |
| Kenya | 20% → 58% | 2,858 → 11,791 | 54% → 44% | 4,693 → 4,360 | 54% → 3% | 224 → 121 | 7,775 → 16,271 | 138,960 → 147,455 | 288 → 262 |
| Ethiopia | 8% → 29% | 1,629 → 4,242 | 19% → 9% | 3,442 → 2,167 | 19% → 3% | 356 → 419 | 5,427 → 6,829 | 71,326 → 72,728 | 223 → 274 |
| Malawi | 29% → 60% | 2,690 → 3,356 | 32% → 59% | 2,392 → 4,780 | 32% → 1% | 272 → 60 | 5,353 → 8,196 | 92,623 → 95,466 | 356 → 529 |
| Niger | 19% → 53% | 7,583 → 7,236 | 82% → 89% | 23,386 → 25,359 | 82% → 0% | 932 → 0 | 31,900 → 32,596 | 39,312 → 40,007 | 2,381 → 2,583 |
| Honduras | 40% → 36% | 0 → 0 | 50% → 50% | 0 → 0 | 50% → 0% | 0 → 0 | 0 → 0 | 1,825 → 1,825 | 0 → 0 |

How to read the table:
- "Spraying coverage before" was bednet use (the old shared pool).
- Treatment deaths rise where MAP coverage is much higher than the old survey. Higher coverage means more people
  receive treatment that a cut can remove; Kenya 20% → 58% is the largest such case.
- Treatment deaths fall where the cost per case rose (US$8 → 14) and coverage changed less (Nigeria).
- Spraying deaths fall where MAP shows little spraying.

**All Countries** (default settings: no government response, death-rate trend on):

| Preset | Malaria deaths before | after | change | All deaths before | after |
|---|---|---|---|---|---|
| Full US Exit | 386,885 | 383,794 | -0.8% | 2,147,238 | 2,144,148 |
| America First MOUs | 83,285 | 84,980 | +2.0% | 382,750 | 384,445 |
| IHME 2025 Preliminary Estimates | 278,186 | 271,894 | -2.3% | 1,602,835 | 1,596,544 |
| OECD-Reported 2025 Aid Cuts | 388,530 | 382,425 | -1.6% | 1,901,993 | 1,895,888 |
| Global Fund & Gavi Shortfalls | 159,869 | 156,198 | -2.3% | 704,181 | 700,510 |
| Combined Retreat | 428,169 | 424,092 | -1.0% | 2,338,402 | 2,334,325 |

The totals move little because country changes offset each other: Kenya, Tanzania, Malawi and Ethiopia go up;
Nigeria, DR Congo and Burkina Faso go down.

**Per-US$1M malaria card** (bednets): deaths per US$1M a year over 5 years, in the table above. It rises where bednet
use and the malaria trend are now higher (Malawi 356 → 529, Burkina Faso 778 → 912). It falls where both are lower
or spraying now adds to vector-control coverage (Kenya 288 → 262, DR Congo 885 → 836).

## Tests, checks, recompute

- **Tests: 331 / 331 pass.**
  - `tests/test_malaria.py` is new (13 tests): MAP values and sources for A-D, the IRS fallback, the combined
    vector-control formula, per-line caps, the trend fit and clip (19 clipped), the US$14 cost, sources shown in the
    table, Data Years, and that `apply` gives the same result when run twice.
- **Test baseline rebuilt** (`python tests/make_baseline.py --malaria`): 84 of 99 entries refreshed.
  - Why: the baseline locks each preset's sudden-cut results against the original model (5eb6111, later mechanisms
    off). Malaria inputs, coverage definitions, the treatment cost and the trend all changed on purpose, so every
    entry with malaria results moved.
  - The refresh checks that outside the lives-first response only malaria lines, the totals and the malaria path
    changed. HIV, TB and immunization lines still match the original model exactly.
  - In 4 lives-first entries (NGA and MOZ IHME 2025, MOZ shortfalls, MOZ MOUs), non-malaria lines also moved. Lives
    first refills lines in order of deaths averted per dollar, and malaria's ranking changed.
  - The other 15 entries are unchanged.
- **`audit/recompute.py`** (independent recalculation from `audit/METHOD.md`, both updated for the new malaria method):
  932 values compared, 0 differ by more than 0.5% from the dashboard.
- **`audit/checks.py`**: 62,044 rows.
  - All pass, including the new `fraction_scale_mal_*_cov` checks.
  - The exceptions are the pre-existing open items: I-10 (Section 3 government level) and the 6 small Section 1 /
    Section 2 aid gaps.
- **App:** every page checked headless (Streamlit AppTest), with no exceptions, including from a clean clone without
  `datasets/`.

## Follow-up (decisions on the malaria batch)

1. **Spraying where MAP shows 0% or little.**
   - Coverage = max(MAP IRS coverage, coverage that donor spraying money buys = donor IRS spending / `uc_irs` /
     people at risk).
   - Where the money-based figure is larger, the source reads "implied by donor spending; MAP 2025: 0%".
   - Full US Exit, no government response, sudden cut, deaths 2026-2030:

     | Country | Spraying coverage | Spraying deaths | Malaria deaths | All deaths |
     |---|---|---|---|---|
     | Nigeria | 0% (MAP) → 1.04% | 0 → 1,276 | 65,337 → 66,489 | 234,313 → 235,466 |
     | Benin | 0% (MAP) → 1.85% | 0 → 94 | 6,196 → 6,258 | 9,709 → 9,771 |
     | Burkina Faso | 0% (MAP) → 3.11% | 0 → 284 | 16,494 → 16,663 | 22,765 → 22,935 |

   - Bednet deaths dip slightly in these countries (Nigeria 40,692 → 40,564), because spraying now adds to
     combined vector-control coverage.
   - Other countries with donor IRS money above MAP's coverage also move:
     - Tanzania: spraying 1% → 3%, deaths 142 → 423;
     - Malawi: 1% → 4%, 60 → 171;
     - Niger: 0% → 2%, 0 → 116;
     - DR Congo: 1 → 98.
2. **Spraying outside MAP's coverage:** unchanged (the money-based figure alone).
3. **`uc_mal_cm`:** central 14, low 4, high 47.
   - Note: "Low and high add the low and high ends of White et al.'s separate treatment and diagnosis ranges, inflated
     x1.42; deliberately wide."
   - Central results are unchanged; only the ranges move.
4. **Display:** as before.
5. **Pakistan:** a note under the Validation page's MAP-vs-WHO comparison.
   - Cases: MAP 14.4M (2025) vs WHO 3.15M (2024).
   - MAP's *P. falciparum* estimate for 2024, 3.2M, is close to WHO's total; the gap is *P. vivax* (MAP: 8.6M in 2024,
     10.1M in 2025), after the surge that followed the 2022 floods.
   - Baseline deaths are unchanged (WHO, 3,037). Pakistan's model results are unchanged: spraying 0.02%, 54 malaria
     deaths.

**All Countries malaria deaths** (default settings):

| Preset | Before | After |
|---|---|---|
| Full US Exit | 383,794 | 385,713 (+0.5%) |
| America First MOUs | 84,980 | 85,543 (+0.7%) |
| IHME 2025 | 271,894 | 273,636 (+0.6%) |
| OECD 2025 | 382,425 | 384,775 (+0.6%) |
| Global Fund & Gavi Shortfalls | 156,198 | 157,227 (+0.7%) |
| Combined Retreat | 424,092 | 426,369 (+0.5%) |

**Diff, tests and checks:**
- **Snapshot diff:** 3,006,850 values compared; 102,546 changed. All are in malaria lines, buckets, paths and cards,
  totals that include malaria deaths, or All Countries sums; none is unexplained.
- **Tests:** 331 / 331 pass. Test baseline: 53 of 99 entries refreshed (`--malaria`); outside lives first, only
  malaria changed. In lives first, NGA IHME 2025 also moved non-malaria lines.
- **Recompute:** 0 of 932 values differ by more than 0.5%.
- **`audit/checks.py`:** only the pre-existing I-10 and Section 1 / 2 items fail.
