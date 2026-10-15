# Health Financing Dashboard

A Streamlit dashboard on who pays for health in 71 low- and middle-income countries, and what happens to health
coverage and lives if donors cut HIV, TB, malaria and immunization aid. All dollar figures are constant 2023 US$
(except amounts quoted from MOUs, which are nominal).

For one country it shows:
- health spending by source (Section 1);
- who provides the aid and what it pays for (Section 2);
- the government budget (Section 3);
- a funding-cut model (Section 4): pick a donor scenario, a government response and a funding path, and the model
  estimates the aid lost, the people losing each service, the coverage drop and the extra deaths in 2026-2030 (and
  2031-2035), with 95% ranges.

Other pages run every country at once (All Countries), compare the model with published estimates (Validation &
Benchmarks), and document every calculation (Methods).

## How data flows from raw files to the screen

```
 datasets/  (raw downloads, NOT in git)
   IHME DAH, health spending, GDP | MAP | KFF tracker | team MOU sheet | IMF WEO
        |
        v
 preparation scripts (run by hand)
   malaria_inputs.py   fiscal_inputs.py   prepare_model.py (calls who_inputs.py)   add_constant_dollars.py
        |
        v
 processed inputs (in git)
   ext_data/   macro_data/   model_data/   spending_data/   country_data/   revenue_data/   cofog_all/
   model_params.csv   unit_cost_reference.csv
        |
        v
 model (no Streamlit)
   health_model.py   scenarios.py   budget_section.py
        |
        v
 display (Streamlit)
   app.py -> views/1_Dashboard.py, 2_All_Countries.py, 3_Validation.py, 4_Methods.py
            (model_section.py, paths_ui.py, theme.py, country_lists.py)
```

`docs/file_inventory.md` lists every file, whether the app or only the offline scripts use it, and the evidence.

## Run the app

```
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Then open http://localhost:8501. Every file the app reads is in the repository, so `datasets/` is not needed to run
it. `app.py` only sets up navigation; the pages live in `views/` (a folder called `pages/` would make Streamlit bypass
that navigation).

To deploy on Streamlit Community Cloud: create an app from this repository and branch with main file `app.py`
(Python 3.11 or later).

## Run the tests and audit checks

```
python -m pip install -r requirements-dev.txt
python -m pytest tests                      # unit and regression tests (about 20 seconds)
python audit/checks.py --quick              # 9 countries, fewer draws (about 2 minutes)
python audit/checks.py --full               # every country, preset, response and funding path (10-25 minutes)
python audit/recompute.py && python audit/compare_recompute.py   # independent recalculation vs the dashboard
python audit/snapshot_numbers.py audit/<name>.csv                # every displayed number, for before/after diffs
```

`audit/AUDIT.md` is the audit report and issue log. Each fixed issue has its own note in `audit/`.

## Rebuild everything from `datasets/`

Put the raw files in `datasets/` (see below), then run, in this order:

```
# 1. Malaria Atlas Project series -> ext_data/map/
python malaria_inputs.py

# 2. IMF WEO fiscal balances (downloaded from the IMF API) -> macro_data/weo_fiscal/
python fiscal_inputs.py --download

# 2b. Sections 1-3 per-country files -> country_data/ and spending_data/ (macro_data/, revenue_data/, cofog_all/
#     cannot be rebuilt from the files on disk; see build_sections.py's docstring)
python build_sections.py --country-data --spending-data   # or --verify to compare with the committed files

# 3. Model inputs, regressions and precomputed results -> model_data/
#    (add --download to refresh ext_data/ from the World Bank / Gapminder mirrors and WHO GHO first)
python prepare_model.py \
    --dah datasets/IHME_DAH_DATABASE_1990_2026_Y2026M09D18.CSV \
    --spend datasets/IHME_HEALTH_SPENDING_1995_2023_Y2026M09D21.CSV \
    --expected datasets/IHME_EXPECTED_HEALTH_SPENDING_2024_2050_Y2026M09D23.CSV \
    --gdp datasets/IHME_GDP_1960_2050_FGH_2026_Y2026M06D11.CSV \
    --mou datasets/co-financing_MOU.xlsx

# 4. Constant-2023-US$ GDP and government health spending as % of GDP -> macro_data/, spending_data/
python add_constant_dollars.py
```

- Steps 1 and 2 also patch `model_data/country_inputs.csv`. Step 3 rebuilds it and applies them again, through
  `who_inputs.apply()`.
- After editing `model_params.csv`, refresh only the All Countries results with
  `python prepare_model.py --precompute-only`.
- The per-country files for Sections 1-3 (`country_data/`, `spending_data/`, `macro_data/`, `revenue_data/`,
  `cofog_all/`) were built by earlier scripts that are not in this repository. They are kept as processed inputs.

## Where each kind of data lives

| Folder or file | What | Built by |
|---|---|---|
| `datasets/` | Raw downloads (untracked) | you (see below) |
| `model_data/` | Model inputs (`country_inputs.csv`, `dah_lines.csv`, `ihme_trend.csv`, `panel.csv`, `regressions.json`, `mou_signed.csv`, `country_profile.csv`) and the precomputed All Countries results (`all_countries_<preset>.csv`) | `prepare_model.py` |
| `ext_data/` | World Bank WDI, WHO GHO, Gapminder series (`wdi/`, `gho/`, `sg/`, `gm/`), Malaria Atlas Project series (`map/`), unused reference series (`reference/`) | `prepare_model.py --download`, `who_inputs.py --download`, `malaria_inputs.py` |
| `macro_data/` | IMF WEO by country (GDP, population, revenue, spending, debt); `weo_fiscal/` = WEO fiscal balances for interest costs | earlier scripts; `add_constant_dollars.py`; `fiscal_inputs.py` |
| `spending_data/` | IHME health spending by source, per country (Section 1) | earlier scripts; `add_constant_dollars.py` |
| `country_data/` | IHME DAH by donor and focus area, per country (Section 2) | earlier scripts |
| `revenue_data/`, `cofog_all/` | IMF revenue by type and COFOG spending by function, per country (Section 3) | earlier scripts |
| `model_params.csv` | Every model parameter: central, low, high, sourced or assumption, citation | edited by hand |
| `unit_cost_reference.csv` | Country ART and income-group TB unit costs from studies | edited by hand |

## Untracked raw files and where to get them

`datasets/` is in `.gitignore`. Nothing in it is needed to run the app; it is needed only to rebuild.

| File in `datasets/` | Source |
|---|---|
| `IHME_DAH_DATABASE_1990_2026_Y2026M09D18.CSV` (plus its codebook, info sheet and user guide) | IHME, Financing Global Health: Development Assistance for Health Database 1990-2026 (GHDx, ghdx.healthdata.org) |
| `IHME_HEALTH_SPENDING_1995_2023_Y2026M09D21.CSV` | IHME, Global Health Spending 1995-2023 (GHDx) |
| `IHME_EXPECTED_HEALTH_SPENDING_2024_2050_Y2026M09D23.CSV` | IHME, Expected Health Spending 2024-2050 (GHDx) |
| `IHME_GDP_1960_2050_FGH_2026_Y2026M06D11.CSV` | IHME, GDP estimates 1960-2050, FGH 2026 (GHDx) |
| `MAP_national_*_2026-10-13.csv` (treatment, ITN, IRS, Pf cases, Pv cases, incidence/prevalence) | Malaria Atlas Project, national unit data, data.malariaatlas.org (downloaded 2026-10-13) |
| `WHO_World_Malaria_Report_2025.pdf` | WHO, World Malaria Report 2025 (who.int); cited on the Methods and Validation pages |
| `KFF_MOU_Tracker_2026-10-08.xlsx` | KFF, Tracker: America First MOU Bilateral Global Health Agreements (kff.org), table as of 8 October 2026 |
| `co-financing_MOU.xlsx` | The capstone team's MOU / co-financing sheet (US funding schedules 2026-2030); ask the team |
| `IMF_WEO_Oct2026_GG_balances_2026-10-13.csv` | IMF World Economic Outlook, October 2026, via api.imf.org; written by `fiscal_inputs.py --download` |
| `dataset_..._IMF.FAD_WORLD_3.0.1.csv` | IMF World Revenue Longitudinal Data (data.imf.org); source of `revenue_data/` |
| `world_bank_health_expenditure_as_percent_of_GDP.csv` | World Bank WDI (data.worldbank.org) |
| `Gavi-Country-Financial-Data-FY2021-25_*.xlsx` | Gavi country financial data (gavi.org); background for the immunization cost |

## The model in one paragraph

- **Money.** Baseline aid is IHME's 2021-23 average by donor x channel x program area. A scenario cuts each cell.
- **Government response.** Optionally the government replaces part of the loss, capped by fiscal space.
- **People affected.** The money lost becomes people losing each service: net loss ÷ cost per person, capped at
  the people covered.
- **Deaths.** Those people become extra deaths through service-specific effects: ART interruption, PMTCT, TB case
  fatality, the Lives Saved Tool for malaria, and deaths averted per child vaccinated.
- **Uncertainty.** Every parameter is drawn 400 times from a triangular distribution.

The Methods page has every formula, source and assumption. `docs/SPEC.md` is the compact specification: it matches
the code, and `audit/logic_review/reproduction/repro.py` reimplements it independently (`audit/recompute.py` is the
earlier independent recalculation, built from the specification's previous version).
