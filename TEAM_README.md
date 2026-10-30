# Team guide: running the model from a copy of this repo

This guide covers branch `chipmunk`, as of 30 October 2026. It is a short, practical companion to:

- `README.md`: what the dashboard shows and how the data flows;
- `docs/SPEC.md`: every formula;
- `docs/DATA_SOURCES.md`: every citation.

Two warnings before you start:

- **Do not commit `datasets/`.** It is in `.gitignore` and is shared separately (see section 2).
- **Do not run `unaids_inputs.py`, `immunization_inputs.py`, `batch34_inputs.py --art-full56` or
  `batch34_inputs.py --donor56-*` on chipmunk.** They were copied from the tomato branch, and chipmunk deliberately
  does not use their rules (`README.md`, top note; `audit/merge/PLAN.md`). Running them rewrites
  `model_data/country_inputs.csv`.

## 1. Set up

You need Python 3.11 or later. The code is tested on 3.13; the devcontainer uses 3.11.

```
git clone <repo-url> && cd <repo> && git checkout chipmunk
python -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
python -m pip install -r requirements-dev.txt
```

This installs streamlit, pandas, numpy, plotly, statsmodels, openpyxl and pytest.

- `requirements.txt` alone is enough to run the app.
- `requirements-dev.txt` adds pytest, for the tests and checks.

Run every command from the repository root. The scripts find their files relative to it.

## 2. The `datasets/` folder: what you need

Make a folder called `datasets/` at the repository root and copy the shared files into it, keeping the
sub-folder names exactly as below. (On Nick's machine `datasets/` is a link to `../capstone_nick/datasets`. A plain
folder works the same.)

### A. Running the app, a scenario, the tests or the precomputed results: nothing

The dashboard (`app.py`), the model (`health_model.py`, `scenarios.py`), `python -m pytest tests` and
`python prepare_model.py --precompute-only` read only files that are in git:
- `model_data/`, `ext_data/`, `macro_data/`, `spending_data/`, `country_data/`, `revenue_data/`, `cofog_all/`;
- `model_params.csv`, `unit_cost_reference.csv`.

None of them opens `datasets/`.

### B. `audit/checks.py --full` with every comparison: two files (optional)

| Path | Used by | Without it |
|---|---|---|
| `datasets/IHME_DAH_DATABASE_1990_2026_Y2026M09D18.CSV` | `audit/checks.py` (Section 2 totals vs the raw IHME file) | compares with `country_data/` instead, which equals the filtered raw file |
| `datasets/IHME_HEALTH_SPENDING_1995_2023_Y2026M09D21.CSV` | `audit/checks.py` (Section 1, 2023 vs the raw IHME file) | that comparison is skipped and recorded as `..._SKIPPED` (still a pass) |

### C. Rebuilding model inputs from raw data

Only needed if you change an input. Each builder reads only the files listed for it.

| Path in `datasets/` | Read by | Builds |
|---|---|---|
| `IHME_DAH_DATABASE_1990_2026_Y2026M09D18.CSV` | `prepare_model.py --dah`, `build_sections.py` | `model_data/dah_lines.csv`, `ihme_trend.csv`, `country_data/` |
| `IHME_HEALTH_SPENDING_1995_2023_Y2026M09D21.CSV` | `prepare_model.py --spend`, `build_sections.py`, `add_constant_dollars.py` | `country_inputs.csv` (spending columns), `spending_data/` |
| `KFF_MOU_Tracker_2026-10-08.xlsx` | `prepare_model.py` (default `--kff`) | `model_data/mou_signed.csv` |
| `UNAIDS_2026/UNAIDS_Estimates_2026.csv` | `hiv_transmission_inputs.py` (called by `prepare_model.py`), `audit/batch4b_art_check.py` | `art_transmission_rate*`; people on ART for `art_cost_full` |
| `MAP_national_treatment_2026-10-13.csv`, `MAP_national_ITN_2026-10-13.csv`, `MAP_national_IRS_2026-10-13.csv`, `MAP_national_Pf_cases_2026-10-13.csv`, `MAP_national_Pv_cases_2026-10-13.csv`, `MAP_national_incidence_prevalence_2026-10-13.csv` | `malaria_inputs.py` | `ext_data/map/`, malaria columns of `country_inputs.csv` |
| `IMF_WEO_Oct2026_GG_balances_2026-10-13.csv` | `fiscal_inputs.py` (written by `--download`) | `macro_data/weo_fiscal/`, `interest_pct_revenue` |
| `GHCC_UCSR/GHCC_UCSR_HIV_ART.xlsx` | `audit/batch34_art_costs.py`, `audit/batch4b_art_check.py` | `art_site_cost*`, `art_cost_full*` |
| `GHCC_UCSR/GHCC_UCSR_TB.xlsx` | `audit/batch34_tb_costs.py` | `tb_ds_cost*`, `tb_dr_cost*` |
| `ValueTB/ValueTB_pooled_patient.dta` | `audit/batch34_art_costs.py`, `audit/batch34_tb_costs.py` | TB course costs |
| `WHO_GHED/GHED_data_2026-10-14.xlsx` | `audit/batch34_donor_share.py`, `audit/batch4b_art_check.py` | `donor_share_*`; observed HIV spending for `art_cost_full` |
| `WHO_TB/TB_budget_2026-10-14.csv`, `WHO_TB/TB_expenditure_utilisation_2026-10-14.csv`, `WHO_TB/MDR_RR_TB_burden_estimates_2026-10-14.csv`, `WHO_TB/TB_burden_countries_2026-10-14.csv`, `WHO_TB/TB_notifications_2026-10-14.csv` | `audit/batch34_donor_share.py`, `audit/batch34_tb_costs.py`, `audit/batch34_gf_shares.py` | `donor_share_tb`, `tb_rr_share`, `tb_rr_cov` |
| `GlobalFund/GF_budgets_2026-10-14.csv`, `GlobalFund/GF_expenditures_modules_2026-10-14.csv` | `audit/batch34_gf_shares.py` | `unspec_<disease>_*` (how unspecified money splits by purpose) |
| `Goals/Unit costs 11april2025.xlsx` | `audit/batch4b_art_check.py` | the ART minimum cost (Stover database ARVs + viral load) |
| `Toor2021/VIMC_deaths_by_year_of_vac.csv`, `Toor2021/VIMC_deaths_by_cross_section.csv`, `Toor2021/VIMC_deaths_by_cohort.csv` | `audit/batch56_vaccines.py` | `imm_dpc*` (deaths averted per vaccinated child) |
| `WUENIC_2025.xlsx` | `audit/batch56_vaccines.py` | `imm_dpc*` (coverage weights) |
| `WPP2024/WPP2024_Demographic_Indicators_Medium.csv` | `audit/batch56_vaccines.py` | `imm_q5_ratio` |

The `audit/batch*.py` scripts write tables to `audit/logic_review/`. Then `batch34_inputs.py` copies them into
`country_inputs.csv`. On chipmunk the flags used are `--shares --art --tb --donor --art-full --vaccines`. The
Batch 7 `--flags` columns are not part of chipmunk's inputs.

**Missing from the shared folder.** A full `prepare_model.py` rebuild (all four `--dah --spend --expected --gdp`
arguments) cannot be reproduced from it, because three files are not there:
- `IHME_EXPECTED_HEALTH_SPENDING_2024_2050_Y2026M09D23.CSV`;
- `IHME_GDP_1960_2050_FGH_2026_Y2026M06D11.CSV`;
- the team's `co-financing_MOU.xlsx`. Without it, the America First MOUs schedules are lost.

The announcement workbook `aid_cut_projections_announcements.xlsx` is also missing. It is the argument to
`announcement_model/project_cuts.py`, which rebuilds `model_data/announcement_cuts.csv` (the Announced donor cuts
preset). Ask the team for it before changing that preset.

Use the targeted builders above and `prepare_model.py --precompute-only` instead.

**Reference only, not read by any model step:**
- `Allel2022/` (one audit script);
- `Goals/Goals Lite (1) (1).xlsx` (the Goals cross-check);
- `GlobalFund/GF_allocations_*.csv`, `GlobalFund/GF_disbursements_*.csv`;
- `WHO_TB/TB_outcomes_*.csv`, `WHO_TB/TB_data_dictionary_*.csv`;
- `WPP2024/WPP2024_PopulationByAge5GroupSex_Medium.csv`;
- the PDFs and IHME codebook files.

`datasets/MANIFEST.md` gives each file's source, URL, download date and units.

## 3. Run a scenario

### In the dashboard

```
python -m streamlit run app.py               # then open http://localhost:8501
```

The dashboard offers two scenarios: "Announced donor cuts" and "Custom". A government response and a funding path
are set on the page. Nothing is written to disk.

### From Python (any preset, one country)

```python
import logging; logging.disable(logging.WARNING)   # the model logs a line whenever a donor-funded pool caps a service
import health_model as hm, scenarios as scn

inputs, ptab = hm.load_inputs(), hm.load_params()       # model_data/ and model_params.csv
preset = "Full US exit"                                 # any key of scenarios.PRESETS
sc = scn.build_scenario(preset, scn.default_opts(preset, inputs["ci"]), inputs["ci"])
res = hm.run_country("KEN", sc, hm.Fiscal(*scn.DEFAULT_FISCAL), inputs, ptab, n_draws=400)
print(res["totals"]["deaths_5y"], res["totals"]["deaths_5y_lo"], res["totals"]["deaths_5y_hi"])
print(res["lines"][["line", "net_loss_usd", "units_lost", "deaths_5y"]])
```

The presets are:
- Full US exit
- America First MOUs
- IHME 2025 preliminary estimates
- OECD-reported 2025 aid cuts
- Global Fund & Gavi shortfalls
- Combined retreat
- Announced donor cuts
- Custom

For a government response, use `hm.Fiscal(mode, theta, cap_to_space, allocation, effort)`. Here `mode` is
`none | custom | max | gradual`. The default is `("none", 0.0, True, "pro_rata", "p75")`, which means no
replacement.

`res` is a dict with these keys:
- `totals` (aid lost, deaths 2026-2030 with `_lo` and `_hi`);
- `lines` (one row per service line);
- `buckets` (HIV, TB, malaria, immunization);
- `path` and `years` (year by year);
- `fiscal` (the government response);
- `committed` (deaths set in motion for 2031-2035);
- `cells` (the aid cells cut).

Nothing is saved unless you save it.

### All countries, every preset (the All Countries page)

```
python prepare_model.py --precompute-only    # about 30 seconds
```

This writes `model_data/all_countries_<preset>.csv` (one row per country) and `model_data/all_countries_<preset>_draws.csv`
(the all-country total in each of the 400 draws, for the ranges). It uses the default settings: no government
replacement, sudden cut, death-rate trend on, 400 draws, seed 7.

Rerun it after any change to `model_params.csv` or `model_data/country_inputs.csv`, or the All Countries page
will show stale numbers.

### Every number at once (for before/after comparisons)

```
python audit/merge/snapshot_merge.py <out.csv>            # about 10 minutes; also writes <out>_headline.csv
python audit/merge/snapshot_merge.py --diff audit/merge/snapshot_chipmunk.csv <out.csv>
```

## 4. Where each input lives

### Model parameters: `model_params.csv`

The file has one row per parameter, with columns `param,label,central,low,high,unit,status,source`.
- The `source` column holds the full citation.
- `docs/DATA_SOURCES.md` lists them by source.
- The Methods page shows the same table.

Each draw takes a triangular value between `low` and `high`, peaking at `central`.

| Line | Parameter | Central (low-high) | Unit | Status | Source (short) |
|---|---|---|---|---|---|
| 2 | `asd_share` | 0.45 (0.30-0.55) | proportion | sourced | KFF 2025 (Gaba et al.), PEPFAR non-service-delivery share |
| 3 | `uc_art_mult` | 1 (0.68-1.38) | multiplier | sourced | Batch 4b (L-50); the country ART cost itself is `art_cost_full` in `country_inputs.csv` |
| 4 | `uc_scale_elast` | 0.4 (0.25-0.6) | elasticity | assumption | salaries rise with income |
| 5 | `uc_pmtct` | 250 (150-450) | US$ per woman per year | sourced | Health Policy and Planning 2016 review of Option B+ CEAs |
| 6 | `cpia_ref` | 5000 (2500-12000) | US$ per infection averted | assumption | scaled by (1/incidence)^0.5 |
| 7 | `uc_ovc` | 100 (60-160) | US$ per child-year | assumption | |
| 8 | `uc_tb_mult` | 1 (0.78-1.60) | multiplier | sourced | Batch 3+4 (IMP-11); country costs `tb_ds_cost`, `tb_dr_cost` |
| 9 | `uc_itn` | 2.2 (1.4-3.5) | US$ per person-year | sourced | GiveWell ITN analysis |
| 10 | `uc_irs` | 8.5 (6-10) | US$ per person-year | sourced | PMI Africa IRS project |
| 11 | `uc_mal_cm` | 14 (4-47) | US$ per case | sourced | White et al. |
| 12 | `uc_imm` | 87 (38-104) | US$ per child | sourced | Lydon et al.; MSF; Brenzel |
| 13 | `art_hazard_mult` | 1 (0.65-1.7) | multiplier | sourced | Batch 2 (L-01) |
| 14 | `art_transmission` | 0.04 (0.02-0.08) | infections per person-year | legacy | sensitivity only |
| 15 | `pmtct_vt_reduction` | 0.25 (0.10-0.40) | probability | sourced | WHO AFRO |
| 16 | `pmtct_infant_mort` | 0.45 (0.35-0.525) | probability | sourced | Newell et al. |
| 17-20 | `tb_cfr_untreated_neg`, `tb_cfr_treated_neg`, `tb_cfr_untreated_pos`, `tb_cfr_treated_pos` | 0.43, 0.03, 0.78, 0.06 | probability | sourced | WHO TB burden methods (Glaziou et al.), Tables 4-5 |
| 21 | `tb_dr_dcfr` | 0.45 (0.30-0.60) | probability | assumption | |
| 22 | `mal_vc_eff` | 0.55 (0.40-0.61) | proportion | sourced | Eisele et al. 2010 (LiST) |
| 23 | `mal_cm_eff` | 0.97 (0.82-0.99) | proportion | sourced | Thwing et al. 2011 (LiST) |
| 24 | `mal_itn_default_use` | 0.50 (0.40-0.60) | proportion | assumption | |
| 25 | `mal_cm_default_cov` | 0.40 (0.30-0.50) | proportion | assumption | |
| 26 | `imm_deaths_per_child_ref` | 0.020 (0.017-0.024) | deaths per child | sourced | Gavi (legacy rule, off) |
| 27 | `imm_u5_share` | 0.65 (0.50-0.75) | proportion | sourced | Li et al. (legacy rule, off) |
| 28 | `hss_kappa` | 0.5 (0.25-0.9) | proportion | assumption | audit I-09 |
| 29 | `continuity` | 0.15 (0.0-0.30) | proportion | assumption | |
| 30 | `tb_secondary` | 0.4 (0.2-0.8) | cases per person-year | sourced | derived |
| 31 | `mal_resurgence` | 0.10 (0.0-0.25) | growth per year | assumption | direction from Cohen et al. |
| 32 | `hiv_inf_death_untreated` | 0.85 (0.70-0.95) | probability | sourced | Todd et al. |
| 33 | `hiv_inf_death_treated` | 0.10 (0.05-0.20) | probability | assumption | |
| 34 | `hiv_survival_median` | 10.5 (8.6-12.5) | years | sourced | Todd et al. |
| 35 | `art_reengage` | 0.35 (0.17-0.68) | proportion per year | sourced | Batch 2 |
| 36 | `mal_adult_effect_frac` | 0.5 (0-1) | proportion | assumption | |
| 37 | `tb_cfr_untreated_pos_art` | 0.49 (0.31-0.70) | probability | sourced | WHO TB burden methods, Table 5 |
| 38-42 | `mal_u5_share_afr`, `_amr`, `_emr`, `_sea`, `_wpr` | 0.75, 0.20, 0.364, 0.25, 0.40 | proportion | sourced | WHO World Malaria Report 2025 |
| 43 | `mal_u5_use_country_series` | 0 (switch) | switch | assumption | sensitivity only |
| 44 | `art_transmission_mult` | 1 (0.71-1.38) | multiplier | sourced | Batch 2 (L-41) |
| 45 | `hiv_new_inf_unsup_years` | 4 (2.5-5.5) | years | assumption | Batch 2 |
| 46 | `hiv_legacy_art_params` | 0 (switch) | switch | constant | off |
| 47 | `hss_service_share` | 0 (0-0) | proportion | assumption | L-05 |
| 48 | `imm_dpc_mult` | 1 (0.56-1.64) | multiplier | sourced | Batch 5+6 V2; country values `imm_dpc*` |
| 49 | `imm_legacy_u5mr_scaling` | 0 (switch) | switch | constant | off |

### Country inputs: `model_data/country_inputs.csv`

The file has one row per country (71) and about 236 columns.
- Most values have a `<column>_source` column saying where the number came from: the country's own value, or a regional or income-group fallback.
- Each `<column>_year` gives the data year.
- `docs/SPEC.md` section 1 lists every column and the script that builds it.

| What | Columns | Built by |
|---|---|---|
| Population, deaths, coverage, GDP, government health spending | `sp_*`, `sh_*`, `ghes_*`, `gdp_pc`, ... | `prepare_model.py` (World Bank WDI, WHO GHO, IHME) and `who_inputs.py` |
| HIV transmission | `art_transmission_rate*` | `hiv_transmission_inputs.py` (UNAIDS 2026) |
| ART cost per patient-year | `art_site_cost*`, `art_cost_full*` | `audit/batch34_art_costs.py`, `audit/batch4b_art_check.py` → `batch34_inputs.py --art --art-full` |
| TB course costs, RR-TB | `tb_ds_cost*`, `tb_dr_cost*`, `tb_rr_*` | `audit/batch34_tb_costs.py` → `batch34_inputs.py --tb` |
| Donor share of spending | `donor_share_*` | `audit/batch34_donor_share.py` → `batch34_inputs.py --donor` |
| Unspecified money by purpose | `unspec_*` | `audit/batch34_gf_shares.py` → `batch34_inputs.py --shares` |
| Vaccine deaths averted per child | `imm_dpc*`, `imm_q5_ratio` | `audit/batch56_vaccines.py` → `batch34_inputs.py --vaccines` |
| Malaria coverage and cases | `mal_*`, `malaria_*` | `malaria_inputs.py` (MAP) |
| Interest on debt | `interest_pct_revenue*` | `fiscal_inputs.py` (IMF WEO) |

### Other inputs

| File | What | Built by |
|---|---|---|
| `model_data/dah_lines.csv` | baseline aid, 2021-23 average, by country × donor × channel × service line | `prepare_model.py` (IHME DAH) |
| `model_data/ihme_trend.csv` | IHME's 2025 / 2021-23 aid ratios | `prepare_model.py` |
| `model_data/announcement_cuts.csv`, `announcement_areas.csv` | the "Announced donor cuts" yearly cuts | `announcement_model/project_cuts.py` |
| `model_data/mou_signed.csv` | signed America First MOUs | `prepare_model.py` (KFF tracker) |
| `model_data/regressions.json` | Poisson / fixed-effects regressions (Validation page) | `prepare_model.py` |
| `unit_cost_reference.csv` | fallback ART and TB unit costs from studies | edited by hand |
| `scenarios.py` | preset definitions (`PRESETS`, `build_scenario`), defaults (`DEFAULT_FISCAL`, `ALL_COUNTRY_DRAWS = 400`) | code |

## 5. Tests and checks

```
python -m pytest tests                  # 408 tests, 2-4 minutes
python audit/checks.py --quick          # 9 countries, fewer draws, about 2 minutes
python audit/checks.py --full           # every country × preset × response × path: 88,161 checks, about 17 minutes
```

**What a pass looks like.**
- pytest: `408 passed`.
- `checks.py --full`: every row passes, with 6 known warnings (`section1_dah_equals_section2_dah_same_year`).

**Outputs.** `checks.py` rewrites `audit/checks_results.csv` and `audit/checks_summary.csv`. Those files are in git, so
`git diff` shows what moved.

**After changing an input.** To confirm that no model output changed, compare a fresh snapshot with
`audit/merge/snapshot_chipmunk.csv` (section 3). Expect 12 rows to exist only in the old snapshot: file hashes of
" 2" duplicate files that commit 20938a5 deleted.
