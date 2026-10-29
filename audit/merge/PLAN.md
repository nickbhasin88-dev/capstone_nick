# Merge plan: main + tomato -> chipmunk (Step 1, plan only)

29 October 2026. main = a33fefb, tomato = 733b99f (local), shared base = 178733c. Nothing below is built yet.

## 0. What the branches actually differ in

- main merged tomato up to **Batch 4b** (14 Oct). main's deaths model is therefore tomato's Batch 2, 3+4 and 4b model.
  Evidence: main's central Full US exit headline is 1,695,601 deaths, exactly tomato's own logged "after Batch 4b"
  figure (`audit/logic_review/MODEL_CHANGELOG.md`); TB people losing service and coverage match exactly in all 2,116
  shared no-response rows.
- main then **hid** the deaths (commit 5c7241a, "Dashboard shows coverage only"): the model still computes deaths on
  every run, but no navigated page shows them, Methods Step 4 and the Cross-Checks tab were removed, and the
  Validation page left the navigation. main also removed the service table from the page (aea3e72, one chart per
  service); `_service_table_html` is still defined but never called.
- tomato added **Batch 5+6 and Batch 7** after the base: ART cost validity and floor (A1), public-spending donor
  shares (A2), the malaria intervention cap (A3), VIMC vaccine deaths (V2), direct WUENIC and UNAIDS inputs (L-17,
  IMP-24), projected births (L-24), the interest definition (L-34), several default-off switches, labels, docs, the
  validation work and the WHO findings audits. tomato never changed `views/1_Dashboard.py`; its service table with
  deaths is the shared-base table.

So the items you named in Rule One fall into two groups:

| Item you named | Status |
|---|---|
| TB costs (Batch 3+4 IMP-11) | **Same on both**: no conflict |
| Malaria under-5 share | **Same on both** |
| HIV death risk and transmission (Batch 2) | **Same on both** |
| Double-counting fixes (Batch 3+4 L-05 systems money, I-09 linked lines, I-15 gains) | **Same on both** |
| ART costs, Batch 4b (L-50) | Same on both; the **Batch 5+6 A1** follow-up differs (row R1 below) |
| Malaria intervention cap | **Differs** (R3) |
| Vaccines | **Differs** (R4) |

## 1. Rule One: tomato changes that main's version overrides (each needs your decision)

Effects are central runs over all 70 modelled countries (sudden cut, no government response), measured by swapping
the one tomato item into main's model (`scratchpad effects.py`; V2 and L-24 measured on tomato's code with its own
switch / fallback, since main lacks that code). FUE = Full US exit, ADC = Announced donor cuts (main's dashboard default).
"Coverage values changed" = country x service coverage drops (of 770) that would move on main's coverage graphs.

| # | Item | main's version (default under Rule One) | tomato's version | Effect of taking tomato's | Touches main's coverage graphs? |
|---|---|---|---|---|---|
| R1 | A1 ART cost per patient-year | observed spending used wherever available; floor US$57 (TLD + one viral load test) | observed spending only where the Global Fund pays >= 10% of HIV spending; floor US$191 (Rosen 2021 site cost x above-site markup); 43 countries change, median 274 -> 216 | deaths FUE 1,695,601 -> 1,666,755 (-1.7%; HIV 938,069 -> 909,223); ADC 1,523,919 -> 1,501,272 (-1.5%); people losing a service -0.2% | **Yes**, 25 values |
| R2 | A2 HIV and immunization donor-funded pools | external share of all-source spending | external share of public spending (Nigeria HIV 0.18 -> 0.55) | FUE +3.1% (HIV +50,592, vaccines +1,678); ADC +1.6%; people +0.4% | **Yes**, 93 |
| R3 | A3 malaria intervention cap | bednets and spraying capped by the public-malaria donor share; treatment by the all-source share | each intervention's own donor share (donor money / people covered x unit cost) | malaria deaths FUE 190,824 -> 276,952 (+45%), all deaths +5.1%; ADC +4.9%; **people losing a service +41% (FUE) / +36% (ADC)**, mostly bednets | **Yes**, 130 |
| R4 | V2 vaccine deaths | Gavi 0.020 per child x under-5 share 0.65 x U5MR/50, cohort weights 0.40/0.35/0.20/0.05 | VIMC deaths averted per fully immunized child by country, antigen and years since vaccination (Toor 2021); `imm_dpc_mult` 0.56-1.64; old rule kept as switch `imm_legacy_u5mr_scaling` | vaccine deaths FUE 104,963 -> 188,853 (+80%); all deaths +4.5% | **No** (deaths only) |
| R5 | L-17 DTP3 and MCV1 coverage | World Bank WDI mirror, 2024 | WUENIC 2025 read directly (30 countries differ by > 2 points) | FUE -0.1% (vaccines -1,714); ADC -0.3% | **Yes**, 46 (immunization "coverage today") |
| R6 | IMP-24 HIV inputs | WHO GHO / WDI | UNAIDS 2026 file (PLHIV, ART and PMTCT coverage, pregnancies, incidence) | FUE -0.0% (HIV -421, TB -7); ADC -0.1% | **Yes**, 133 (HIV "coverage today") |
| R7 | L-24 immunization need | latest-year births held to 2030 | WPP 2024 projected births 2026-2030 | vaccine deaths +441 (+0.2%) | **Yes**, 41 |
| R8 | L-34 interest definition (+ L-31 label "IMF WEO Oct 2026") | more recent of IMF and World Bank | IMF WEO net interest for every country; 17 countries change (Ethiopia 12.6 -> 7.8%) | none without a government response; with 25% response FUE 1,396,340 -> 1,395,942; max response 1,059,897 -> 1,057,684; changes the fiscal panel's "Interest: x% of revenue" in 17 countries | Only with a government response; **changes main's fiscal panel** |
| R9 | L-11 Lancet comparison baseline | GBD-2019 HIV share | UNAIDS 2025 AIDS deaths (Kenya 221,301 -> 60,943 over 5 years) | Validation page only (not in main's navigation) | No |
| R10 | Wording and labels | "leaves WHO, Gavi and UNFPA"; Gavi -15% description; `uc_pmtct` status "sourced"; `uc_art_mult` source text; vaccine row detail "vaccines + delivery" | "withdraws from multilateral agreements"; "our estimate, this preset only"; `uc_pmtct` "unverified" (L-32); Batch 5+6 source text; "deaths exclude DTP, polio and BCG..." | no numbers | Labels only |
| R11 | Default-off additions | none | `mou_deflate` + `mou_us_inflation` (L-35), `budget_growth` + `gdp_growth_weo_2026_30` (item 10), named debt-stress constants (L-29, same values), malaria input flags (item 14) | **zero at defaults** (verified by tomato's own logs) | No |

Default (Rule One) = main's version for every row. My recommendation, for you to accept or change:

- **R4 (V2 vaccines): take tomato's.** It is deaths logic main doesn't have in its current form; it moves no main
  output (coverage, money, OECD, projection all unchanged), and the old rule was the item the logic review flagged
  (L-42, L-18). Cost: 26 input columns appended, 2 parameter rows appended at the end (no draw shifts), tomato's
  vaccine timing test, and the deaths columns in the 14 All Countries files regenerated.
- **R1, R2, R3, R5, R6, R7, R8: keep main's** (Rule One), because each changes main's coverage graphs or fiscal panel,
  which Goal 1 and the Step 3 "match snapshot_main exactly" check require to stay as they are. R3 is the biggest open
  question on the model's accuracy (+41% people losing a service); worth a separate decision later, not in this merge.
- **R9, R10: keep main's.** **R11: keep main's** (bringing them in changes nothing at defaults, but they are not
  deaths logic; they stay on tomato and in the inventory).

## 2. Tomato deaths displays that main removed (other than the service table)

You asked for the service table only. These tomato displays stay off chipmunk unless you say otherwise. The code for
most still exists on main, uncalled. Full list: INVENTORY.md section 3 (A1-A28).

| | Display | Default |
|---|---|---|
| D1 | Methods "Step 4: Lives (Extra Deaths)", 180 lines | **Recommend adding** after Step 3: the table shows deaths, so Methods must say how they are made (only the deaths step; main's other Methods text unchanged) |
| D2 | Lede headline and "Extra Deaths, 2026-2030" big number; The Numbers pills; outcome-panel deaths pills | Off (main's lede and pills) |
| D3 | US$1M cards' deaths line | Off (main's test asserts the cards carry no deaths) |
| D4 | "How the Damage Scales": dose chart, "Extra Deaths Each Year" chart | Off |
| D5 | Scenario A vs B deaths chart; "replacement averts N deaths" line | Off (main shows people kept instead) |
| D6 | All Countries deaths pills, map, scatter, top 15 | Off (main shows people losing a service) |
| D7 | Validation & Benchmarks page in navigation; Methods Cross-Checks tab | Off; tomato's `views/3_Validation.py` content kept in the repo (it is not in main's navigation now either) |

## 3. Rule Three: what tomato's deaths logic assumes that main's model does differently, and the fix

| # | Mismatch | Fix |
|---|---|---|
| C1 | tomato's table has 7 columns; main's `_service_table_html` was cut to 6 (and gained `_other_aid_sub`, new column widths and colspans) | port only the deaths column, Total-row deaths and range, and the hiv_prev / "~0" / "In HIV Treatment" cells into main's current function; everything else stays main's |
| C2 | Years: main has per-year columns (`net_loss_<year>`, `units_lost_<year>`, `cov_drop_pp_<year>`) and an unused year helper; the model has no per-year deaths by line | table shows money and people as 2026-2030 yearly averages (as main's rows) and deaths as the 2026-2030 total, labelled so; no year picker (main shows none) |
| C3 | Money definition under Announced donor cuts: main's fiscal panel uses **all health aid** lost (`with_all_aid`, display only); the deaths and the table use the four diseases' net loss after replacement (as main's coverage graphs) | keep the model's definition (deaths and coverage from the same net loss; no double counting); one caption line says the table covers HIV, TB, malaria and vaccines, so its Aid Lost total is below the fiscal panel's all-health-aid figure |
| C4 | Units: both constant 2023 US$, model years 2026-2030 (`YEAR0` 2026, `N_YEARS` 5), cut fractions applied to the 2021-23 baseline | none needed; Step 3 check d confirms |
| C5 | Totals: Total-row deaths = sum of shown rows; orphan support (excluded row) and linked lines carry 0 deaths | none; pre-check on main's code: sum of rows = run total in 507 of 507 runs (every preset x country) |
| C6 | Only if R4 taken: V2 reads `imm_dpc*` columns and `imm_dpc_mult` that main lacks | append tomato's 26 vaccine columns to main's `country_inputs.csv` (no existing column touched; Zambia's MOU amounts stay main's); append the 2 parameters at the end of `model_params.csv`; regenerate the deaths columns of `model_data/all_countries_*` and prove every other column byte-equal to main |
| C7 | main's `audit/checks.py` and `audit/snapshot_numbers.py` crash: they read `card["deaths"]`, which main's cards no longer have (pre-existing on main since 5c7241a) | compare the card check against `hm.per_million_card(...)["deaths"]` (the model value) instead of the card text; `.get` in snapshot_numbers. Tooling only |
| C8 | main's " 2" test copies (a33fefb) are tomato's tests: 15 fail on main today (5 vaccine-timing, 5 card-deaths, 2 interest label, 2 MOU, 1 PMTCT label) | your choice: (a) leave them and report the 15 as pre-existing; (b) `collect_ignore_glob = ["* 2.py"]` in `tests/conftest.py` (files kept). Recommend (b): the originals of all 27 tomato-version copies are kept as tomato's real test files where adopted |

## 4. Every file: take main, take tomato, or merge by hand

| Group | Files | Action | Why |
|---|---|---|---|
| main only | 173 (announcement model, Announced precomputed files, `model_sourced_update/`, `tests/conftest.py`, `tests/test_announcement.py`, 156 " 2" copies) | main | main only |
| tomato only | 157 (150 audit files incl. WHO findings and reallocation, 2 docs figures, `docs/EXPLAINER.md`, `DATA_SOURCES.md`, `build_sections.py`, `immunization_inputs.py`, `unaids_inputs.py`, slides) | tomato, unchanged | additive; nothing lost. `immunization_inputs` / `unaids_inputs` are NOT wired into `prepare_model.py` (that would apply R5/R6 on the next rebuild) |
| identical | 521 | either | |
| changed on main only | `app.py`, `theme.py`, `paths_ui.py`, `views/1_Dashboard.py` (table placed via model_section, not here), `views/2_All_Countries.py`, `tests/test_malaria.py`, `tests/test_mou.py` | main | main wins |
| changed on tomato only | `views/3_Validation.py`, the 8 audit files (`checks_results.csv`, `logic_review/{assumptions,findings,improvements}.md`, `reproduction/*`) | tomato | deaths validation and audit records (Rule Two) |
| | `README.md`, `docs/SPEC.md`, `batch34_inputs.py` | tomato + one header note in README/SPEC naming where chipmunk uses main's rule | docs and an input builder; no effect on outputs |
| | `fiscal_inputs.py`, `tests/test_fiscal.py`, `tests/baseline_sudden.json`, `model_params.csv` | **main** (R8; baseline must match the rules kept); `model_params.csv` + 2 rows only if R4 | Rule One |
| changed on both | `health_model.py` | by hand: main's file, plus the V2 vaccine code if R4 | |
| | `model_section.py` | by hand: main's file, plus the deaths column (C1) and the table call and caption in `_country_results`; plus V2 helpers in `deaths_per_child_immunised` if R4 | |
| | `views/4_Methods.py` | by hand: main's, plus Step 4 if D1 | |
| | `scenarios.py`, `prepare_model.py` | main | R10, R11, R5/R6 not taken |
| | `tests/test_hiv.py` | main | R10 (PMTCT label) not taken |
| | `tests/test_paths.py` | by hand: main's `ihme_split` fixture; tomato's VIMC vaccine-timing test if R4, else main's | |
| | `model_data/country_inputs.csv` | main (+ C6 columns if R4) | |
| | 12 `model_data/all_countries_*` files | main (deaths columns regenerated if R4; all other columns verified identical) | |

New files (additive): `audit/merge/{INVENTORY,PLAN,VERIFICATION}.md`, `snapshot_merge.py`, a test file
`tests/test_merge_deaths.py` for checks a-c.

**Removed, renamed or hidden: none.** No file is deleted; every main page, section, chart, control, preset, label and
text stays. (D2-D7 are tomato displays that main already removed; they are not added back unless you say so.)

## 5. Where the table and the coverage graphs sit (Dashboard, unchanged order otherwise)

```
How Aid Cuts Translate into Coverage in {country}          (main's section, unchanged)
  Where the Money Is Lost        [money by disease] [who cut it]          (main)
  Service Coverage, Year by Year  small multiples, one chart per service   (main)
                                  coverage drop overview + source line      (main)
  What Each Service Loses   (?)   NEW: tomato's table                       <- added here
    Service | Donor Aid Now | Aid Lost | Cost per Person |
    People Losing Service, per Year | Coverage | Extra Deaths, 2026-2030 Total
    ... one row per service, Other Aid, Total (deaths range = the run's own range)
    caption: Other Aid; four diseases only (C3)
  Can {country} Fill the Gap?     fiscal panel                              (main)
```

Column label: tomato's is "Extra Deaths, 5 Years Total". If you want the words "lives saved", the same number can be
labelled "Lives Saved by This Aid, 2026-2030" (the deaths the lost aid had been preventing). Default: tomato's label.

## 6. Build (Step 2, after APPROVE): one commit per piece

1. Tomato-only files (audit, docs, slides, input builders), unchanged.
2. Tomato-only-changed files taken from tomato (Validation page, audit records, README/SPEC/batch34_inputs).
3. Tooling fix C7 (checks.py card check, snapshot_numbers).
4. If R4: vaccine inputs and parameters (C6), then the V2 model code, then tomato's vaccine test, then regenerated
   All Countries deaths columns.
5. Service table with deaths (C1-C3) in `model_section.py`.
6. Methods Step 4 if D1.
7. Tests for a-c; conftest choice C8.
8. VERIFICATION.md.

## 7. Verify (Step 3)

- Nothing lost: every row of INVENTORY.md (files, 313 main UI items, 284 tomato UI items, functions, parameters,
  inputs, columns, tests, checks) marked Present (with location) or Missing / not-adopted-by-decision.
- Main unchanged: `snapshot_merge.py` on chipmunk vs `snapshot_main.csv`: every value equal, except the deaths-derived
  columns if R4 (those are listed and reconciled to the R4 effect). OECD preset, Announced projection (PROJ rows and
  file hashes), coverage and per-year columns must match exactly.
- a: deaths never negative; zero when no aid is cut (Custom at defaults, and every row with net loss 0).
  b: coverage never below 0; people losing a service never above people covered. c: table rows add up to the Total
  in every country x preset. d: units and years (constant 2023 US$, 2026-2030) checked on the table and run totals.
  e: Full US exit (in both models) chipmunk vs tomato, total and by disease, every difference attributed to R1-R8.
- Tests: chipmunk suite, plus tomato's own suite and main's own suite run against chipmunk, with every failure
  attributed to a decision above. `audit/checks.py --full`: **blocked** (next section).
- Open the dashboard (Dashboard, All Countries, Methods, plus the Validation file) and confirm every page loads.

## 8. Blockers and questions found in Step 0

1. **`audit/checks.py` cannot finish on any branch**: it reads `datasets/IHME_HEALTH_SPENDING_1995_2023_Y2026M09D21.CSV`,
   which is not in `datasets/` or anywhere on this Mac (only the 2024-2050 expected-spending file is in Downloads). On
   tomato the quick run stops there. On main it stops earlier (C7). Please put the file back in `datasets/`, or approve
   running checks with that one comparison skipped and reported.
2. `--full` time: the script says ~10 min; my notes from Batch 5+6 say over an hour. OK to run it once at the end?
3. main moved during Step 0 (your a33fefb): it adds the 156 " 2" files and changes the "Cap Replacement at Fiscal Space"
   default to off. chipmunk was re-based on it before any snapshot; both backup tags exist.
4. The fetch from origin fails on a broken local ref `refs/heads/main 2` (a macOS duplicate in `.git/refs/heads/`). I
   worked around it and did not touch it. Delete it yourself when convenient.
