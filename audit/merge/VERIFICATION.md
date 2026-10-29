# Merge verification: chipmunk (Step 3)

29 October 2026. chipmunk = main a33fefb + tomato's deaths logic, built in Step 2 as listed in `PLAN.md` with your
decisions 1-7. main, tomato, nyt and real-modeling-check were not touched. Nothing was deleted.

| Check | Result |
|---|---|
| a. Nothing lost | **0 Missing.** 2,518 of 2,627 inventory items Present on chipmunk's live code. The other 109 are tomato items your decisions keep off (R3, R5-R11, D2-D7); 84 of them are still on chipmunk as tomato's own code in main's byte-identical " 2" copies, 25 are input columns kept on tomato only |
| b. Main unchanged | **Yes**, except vaccine deaths (R4): 0 of 8,078,940 snapshot values differ outside deaths. One effect beyond the snapshot: see *Triage allocation* below |
| c. Accuracy | **Pass**: no negative deaths; zero deaths with no cut; coverage never below 0; people losing a service never above people covered; table deaths = total; years 2026-2030, constant 2023 US$ |
| d. Full US Exit vs tomato | 1,777,774 vs 1,928,289; the whole gap of 150,515 is explained by R1, R2, R3, R5, R6, R7 (zero residual) |
| e. Tests | 408 passed, 0 failed (" 2" files skipped) |
| f. `audit/checks.py --full` | 87,799 of 88,091 pass; **292 fail, all pre-existing on main** (Announced donor cuts in 3 money checks that predate the preset; section 6) |
| g. Dashboard pages | Dashboard, All Countries, Methods (and the Validation file) load with no exception or error |

## 1. Commits (on top of a33fefb and the two Step 0-1 commits)

| Commit | Piece |
|---|---|
| 3323958 | 2.1 tomato-only files (157), unchanged |
| 933a1f6 | 2.2 files changed only on tomato (Validation page, 8 audit records, README, SPEC, batch34_inputs); header note in README/SPEC |
| 85edd2e | 2.3 C7 tooling fix (card check reads the model value; snapshot_numbers `.get`); IHME spending comparison skipped when the file is absent |
| 9a6997a | 2.4a R4 inputs: 19 VIMC columns appended to `country_inputs.csv`; 2 parameters appended to `model_params.csv` |
| e8c5d25 | 2.4b R4 model: tomato's V2 vaccine code in `health_model.py` |
| 07c76ea | 2.4c R4 test: tomato's vaccine-timing test; V2 per-child helper; baseline vaccine entries refreshed |
| 8542b5d | 2.4d R4 All Countries deaths columns regenerated (all other columns byte-identical to main) |
| ce5689b | 2.5 service table with deaths, under Service Coverage, Year by Year |
| 005bfbc | 2.6 Methods Step 4: Lives |
| e6a1dce | 2.7 merge tests a-d; conftest skip of " 2" files; one main test narrowed (section 5) |
| 6b03602 | caption: preset name title-cased |
| 6ec03eb | Validation page: main's text where tomato's described rules chipmunk does not use |
| (this commit) | VERIFICATION.md, `verify_inventory.py`, `verification_items.csv`, `fue_chain.py`, `fue_chain.csv`, chipmunk headline snapshot |

Notes against the plan: PLAN.md said 26 vaccine columns; tomato's V2 added 19 (`imm_dpc`, `_lo`, `_hi`, `imm_q5_ratio`,
`imm_dpc_beyond_window`, `imm_dpc_lag0-9`, `imm_antigens`, `imm_antigens_excluded_zero_coverage`, `imm_dpc_source`,
`imm_in_vimc`), all of them taken. The two V2 parameter labels `imm_deaths_per_child_ref` and `imm_u5_share` now say
"Legacy ... (used only when imm_legacy_u5mr_scaling = 1)", as on tomato (values unchanged). main's "vaccines + delivery"
line detail is kept (R10); the table's help tooltip says DTP, polio and BCG are excluded from vaccine deaths.

## 2. Nothing lost (INVENTORY.md, every item)

`audit/merge/verify_inventory.py` marks each item; the per-item list with locations is
`audit/merge/verification_items.csv` (2,627 rows: section, item, side, status, location, note).

| Section | Items | Present | Off by decision | Missing |
|---|---|---|---|---|
| Files (main 737, tomato 721; union) | 894 | 894 | 0 | 0 |
| UI items, main | 313 | 313 | 0 | 0 |
| UI items, tomato | 284 | 208 | 76 | 0 |
| Functions, classes, constants | 587 | 583 | 4 | 0 |
| Parameters | 51 | 48 | 3 | 0 |
| Model input files | 27 | 27 | 0 | 0 |
| Input columns | 262 | 237 | 25 | 0 |
| Tests | 156 | 155 | 1 | 0 |
| Checks | 53 | 53 | 0 | 0 |
| **Total** | **2,627** | **2,518** | **109** | **0** |

How "Present" is decided: files exist on chipmunk; UI rows have every referenced main/tomato source line found
unchanged in chipmunk's file (difflib line map; the CSV gives chipmunk's file:line); functions, parameters, columns,
tests and checks are looked up on chipmunk.

**main items: all 313 UI items and every main function, parameter, column, test and check are Present.** main files
whose content changed, all intended: `health_model.py` (V2 added), `model_section.py` (deaths column, table call,
V2 helper), `views/4_Methods.py` (Step 4 added; one Dashboard Sections row extended), `views/3_Validation.py` (one
Gavi line), `model_data/country_inputs.csv` (19 columns appended), `model_params.csv` (2 rows appended, 2 labels),
the 14 All Countries files (deaths columns only), `tests/test_paths.py`, `tests/baseline_sudden.json`,
`tests/conftest.py`, `tests/test_announcement.py`, `audit/checks.py`, `audit/snapshot_numbers.py`, README, SPEC.
Six main UI rows contain lines the merge changed (the service table function, the Gavi cross-check label, one Methods
table row, three Validation-page lines that now show the VIMC figure); all six are still present.

**tomato items off by your decisions (109).** None is deaths logic you asked to keep, the service table, a check, or
a test of an adopted rule:

| Why | Items |
|---|---|
| main's version kept (conflict defaults to main): main restyled or removed the element | 38 UI |
| Off by decision 2 (D2 lede/pills, D3 card deaths, D4 dose charts, D5 A vs B deaths, D6 All Countries deaths, D7 Cross-Checks tab) | 36 UI |
| R11 default-off switches (L-35 MOU deflation, item 10 budget growth, item 14 malaria flags) | 4 functions, 3 parameters, 6 columns |
| R7 projected births | 6 columns |
| R3 malaria intervention cap | 6 columns |
| R9 UNAIDS HIV deaths (Validation baseline) | 3 columns |
| R5 / R6 / R8 source and flag columns | 4 columns |
| R10 "unverified review figures" (L-32) | 2 UI |
| R8 interest test (`test_imf_net_interest_is_primary...`) | 1 test, kept byte-identical in `tests/test_fiscal 2.py` (not collected, decision 4) |

tomato's own versions of `health_model.py`, `model_section.py`, `scenarios.py`, `fiscal_inputs.py`,
`prepare_model.py`, `paths_ui.py`, `views/*.py`, `model_params.csv`, `tests/test_fiscal.py`, `tests/test_hiv.py` and
`tests/baseline_sudden.json` are on chipmunk byte for byte as main's " 2" copies. tomato's full `country_inputs.csv`
is not (only on tomato and tag backup-tomato-2026-10-29).

## 3. Main unchanged

`snapshot_merge.py` on chipmunk (seed 7, 400 draws; every preset incl. Custom, country, path and response: 9,868 runs,
plus All Countries sums, 70 projection rows, file hashes) against `snapshot_main.csv`: 9,974 rows x 810 columns,
8,078,940 values; 243,323 differ, **all of them deaths**:

- columns that differ: deaths of the vaccine line and bucket (`L.imm.deaths_*`, `B.Immunization.deaths_*`,
  `deaths_per_musd`), the totals that include them (`T.deaths_*`, `Y.<year>.deaths`, `C.deaths*`, `C.after_2030*`,
  `C.part.imm`), the Immunization deaths path, the deaths sums and ranges of the 7 All Countries files and those 14
  files' hashes;
- **0 differences** in the 497 coverage, people, money, fiscal and projection columns; **0** in the 1,400 OECD-preset
  rows outside deaths; **0** in the 70 Announced-projection rows; announcement_cuts.csv, announcement_areas.csv and
  oda_history.csv hashes equal; HIV, TB and malaria deaths unchanged everywhere.

All Countries files: a fresh precompute differs from main's committed files by last-bit float rounding (at most
4e-16 relative) in money and people columns, so only the deaths columns that moved were written; every other column
is byte-identical to main.

Vaccine deaths, all countries, 2026-2030: Full US Exit 102,735 -> 184,908; Announced Donor Cuts (main's default)
282,717 -> 512,195, so its total goes 1,523,919 -> 1,753,398 (+15%). HIV, TB and malaria deaths and every people and
money column are unchanged.

**Triage allocation (beyond the snapshot, which covers the pro-rata allocation only).** Under "Where Replacement Money
Goes: Hypothetical best case (triage)" (Advanced menu; also the default for Scenario B in the comparison) the
government's money refills the services with the most deaths averted per dollar first. R4 changes vaccine deaths per
dollar, so the triage order and therefore coverage change: Announced Donor Cuts, fiscal-space response, 53 of 770
coverage values in 19 countries (largest 17.7 points); with a 25% response 95 values in 36 countries; Custom 18 and
41. Under pro-rata (the default) nothing changes. This follows directly from R4 and is consistent (the same deaths drive
the ranking and the table); keeping main's triage order would mean ranking with deaths the table no longer shows.
`tests/baseline_sudden.json`: 13 lives-first entries moved for this reason (HIV, malaria, TB lines); the other 60
refreshed entries moved only in vaccine deaths.

## 4. Accuracy (on main's model)

Over all 9,868 snapshot runs (every preset, country, path and response) and in `tests/test_merge_deaths.py` (every
preset x country x no response / 25% / triage):

| Check | Result |
|---|---|
| Deaths never negative (111 deaths columns: lines, buckets, totals, years, 2031-2035) | min 0.0 |
| Zero with no cut: 3,242 runs with no net loss; zero funding path for every preset and country | max 1.6e-11 |
| A line with no loss and no people lost has no deaths | pass |
| Coverage after the cut never below 0 (average and each year 2026-2030; 457,680 checks) | min 0.0 |
| People losing a service never above people covered (average and each year) | max excess 0.0 |
| Table: rows' deaths = run total; lines left out of the table (orphan support) carry 0 deaths | max relative gap 7.5e-12 |
| Years: model years 2026-2030 (`YEAR0` 2026, `N_YEARS` 5); deaths_5y = sum of the yearly deaths; money and people = yearly averages of the per-year columns | pass (gap 6.3e-12) |
| Units: constant 2023 US$ (same inputs and baseline as main; no conversion added); deaths labelled "Extra Deaths, 2026-2030 Total", people "per Year" | pass |
| No double counting: deaths come from the same net loss as coverage; Aid Lost in the table is the four diseases only, stated in the caption (the fiscal panel counts all health aid under Announced Donor Cuts) | pass |

## 5. Full US Exit: chipmunk vs main and tomato

Extra deaths 2026-2030, all 70 countries, central (All Countries files):

| | main | chipmunk | tomato |
|---|---|---|---|
| Total | 1,695,601 | 1,777,774 | 1,928,289 |
| HIV | 938,069 | 938,069 | 998,517 |
| TB | 463,973 | 463,973 | 463,966 |
| Malaria | 190,824 | 190,824 | 276,952 |
| Vaccines | 102,735 | 184,908 | 188,853 |

chipmunk - main = +82,173, all vaccines (R4, VIMC). tomato - chipmunk = +150,515, attributed by adding tomato's items
to chipmunk one at a time (`audit/merge/fue_chain.py`, results `fue_chain.csv`; the last step equals tomato's own
file exactly):

| Step (cumulative) | Total | Change | Where |
|---|---|---|---|
| chipmunk | 1,777,774 | | |
| + R1 ART cost per patient-year (A1) | 1,748,929 | -28,845 | HIV |
| + R2 donor-funded pools, public-spending share (A2) | 1,841,277 | +92,348 | HIV +89,312, vaccines +3,037 |
| + R5 WUENIC DTP3/MCV1 (L-17) | 1,841,743 | +466 | vaccines |
| + R6 UNAIDS HIV inputs (IMP-24) | 1,841,719 | -24 | HIV -18, TB -7 |
| + R7 projected births (L-24) | 1,842,161 | +442 | vaccines |
| + R3 malaria intervention cap (A3) | 1,928,289 | +86,128 | malaria |
| tomato | 1,928,289 | residual 0 | |

R8-R11 change nothing here (no government response; labels; default-off switches). PLAN.md's one-at-a-time effects
differ for R2 (+50,592 HIV alone vs +89,312 after R1: the lower ART cost and the larger donor pool compound) and R5
(-1,714 under main's old vaccine rule vs +466 under VIMC).

## 6. Tests and checks

- `pytest tests` (" 2" files not collected, decision 4): **408 passed, 0 failed**. New: `tests/test_merge_deaths.py`
  (33). Changed: `test_paths.py::test_late_vaccine_cut_committed` is tomato's VIMC version (R4); main's
  `test_announcement.py::test_dashboard_is_coverage_only` now expects exactly one deaths column in the service table
  ("Extra Deaths, 2026-2030 Total", decisions 2-3); its headline and lede assertions are unchanged.
- `audit/checks.py --full` (IHME health spending comparison skipped: the file is not in `datasets/`):
  88,091 runs in 942 s: **87,799 passed, 292 failed, 6 warnings**; `section1_2023_matches_raw_IHME_file_SKIPPED`
  recorded. Every deaths, coverage, table and precomputed check passes (e.g. `deaths_nonnegative` 2,028,
  `zero_cut_gives_zero` 1,014, `table_total_row_equals_headline` 2,028, `card_deaths_equal_full_model_1M_uniform_cut`
  280, `precomputed_csv_matches_fresh_run` 437, `coverage_in_0_1_and_after_le_before` 2,028). **All 292 failures are
  main's "Announced donor cuts" preset, in three money checks written before that preset existed**:
  `cut_formula_matches_documented_scenario` 280 (`expected_cut` has no branch for the preset, so it expects a zero cut),
  `aid_at_risk_is_per_year_not_5yr_total` 8 (DJI, GUY) and `unspec_and_kappa_conserve_money` 4 (DJI malaria): both
  compare one year's cell loss with the 2026-2030 average, which differ when the cut changes by year. They are
  pre-existing on main: the checked money values are identical to main (section 3), and the same cut-formula (70 of
  70 countries) and aid-at-risk (DJI, GUY) failures reproduce on main's own code. They never showed because checks.py
  stopped at the card check (C7) on main. The 6 warnings are the known Section 1 vs Section 2 DAH gaps of 2-5%.
  Fixing the three checks means teaching checks.py the Announced preset, which is outside decision 7 (not done).

## 7. Dashboard

Run headlessly with Streamlit's AppTest (`app.py` navigation): Dashboard (Announced Donor Cuts, Kenya; and Custom),
All Countries, Methods, plus `views/3_Validation.py` on its own: **0 exceptions, 0 errors on every page**. Dashboard
section order: Where the Aid Is Spent, Where the Money Is Lost, Service Coverage, Year by Year, **What Each Service
Loses** (table with "Extra Deaths, 2026-2030 Total" and the four-diseases caption), Can {country} Fill the Gap?.
Methods shows "Step 4: Lives (Extra Deaths)".

## 8. Other notes

- `datasets/` holds `IHME_HEALTH_SPENDING_1995_2023_Y2026M09D21 2.CSV` (a macOS duplicate name). Per decision 5 it
  was not used; renaming it to the expected name would let the skipped comparison run.
- The broken ref `refs/heads/main 2` was left alone (decision 6).
- Snapshots: `snapshot_chipmunk.csv` is gitignored (~60 MB); `snapshot_chipmunk_headline.csv` is committed.
