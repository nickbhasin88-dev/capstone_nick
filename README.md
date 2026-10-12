# Health Financing Dashboard

Who pays for health in 71 low- and middle-income countries, and what happens to coverage and lives if donors cut
HIV, TB, malaria and immunization aid. All dollar figures are constant 2023 US$.

## Run it locally

```
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Then open http://localhost:8501.

## Pages

| Page | File | What it shows |
|---|---|---|
| Dashboard | `views/1_Dashboard.py` | One country: health spending, donors, government budget, and the funding-cut model |
| All Countries | `views/2_All_Countries.py` | Every country under one donor scenario: totals, map, exposure scatter |
| Validation & Benchmarks | `views/3_Validation.py` | The model against published estimates and two statistical methods |
| Methods | `views/4_Methods.py` | How every number is calculated, data sources, assumptions |

`app.py` only sets up the navigation; the pages live in `views/` (a folder called `pages/` would make Streamlit
bypass that navigation). `theme.py` holds every color, font and chart style.

## Files

| File or folder | What it is |
|---|---|
| `health_model.py` | The funding-cut model (no Streamlit): money -> government response -> coverage -> deaths. Import it in a notebook to run anything in batch. |
| `model_params.csv` | Every unit cost and effect size, with low / central / high values, `sourced` or `assumption`, and the citation. |
| `unit_cost_reference.csv` | Sourced unit costs: ART site costs (Rosen et al. 2021) and TB cost per patient by income group (Laurence et al. 2015). |
| `scenarios.py` | Donor-scenario presets and funding-path shapes, shared by the app and `prepare_model.py`. |
| `model_section.py`, `paths_ui.py` | Section 4 of the dashboard and the funding-path controls. |
| `country_lists.py` | The 71 countries the dashboard covers. |
| `model_data/` | Prebuilt model inputs (`dah_lines.csv`, `country_inputs.csv`, `ihme_trend.csv`, `panel.csv`, `regressions.json`, `country_profile.csv`) and the all-country results at default settings (`all_countries_<scenario>.csv`). |
| `ext_data/` | WHO, UNAIDS, World Bank and UN IGME series used to build the inputs: `gho/` from the WHO Global Health Observatory (`who_inputs.py`), `wdi/`, `sg/` and `gm/` from Gapminder's mirrors. |
| `country_data/`, `spending_data/`, `macro_data/`, `revenue_data/`, `cofog_all/` | Per-country data behind Sections 1-3 (IHME aid and spending, IMF macro, revenue and spending by function). |
| `datasets/` | Raw source files: IHME health spending and GDP, IMF revenue (WoRLD), Gavi financial data and the team's MOU sheet. |
| `tests/` | `python -m pytest tests`: checks the funding paths and each model mechanism. |

## Deploy to Streamlit Community Cloud

1. Push this branch to GitHub.
2. At https://share.streamlit.io choose **Create app**, pick this repository and branch, and set the main file to
   `app.py`. Python 3.11 or later.
3. Every data file the app reads is in the repository (`country_data/`, `spending_data/`, `macro_data/`,
   `revenue_data/`, `cofog_all/`, `model_data/`), so nothing else needs uploading.

## Rebuild the data

- Model inputs and the precomputed all-country results:

  ```
  python prepare_model.py --dah <IHME_DAH_DATABASE_1990_2026_*.CSV> \
      --spend datasets/IHME_HEALTH_SPENDING_1995_2023_Y2026M09D21.CSV \
      --gdp datasets/IHME_GDP_1960_2050_FGH_2026_Y2026M06D11.CSV --mou datasets/co-financing_MOU.xlsx
  ```

  (`--precompute-only` re-runs only the all-country results.) The IHME DAH file is too large for GitHub and is kept
  outside the repository.
- Current WHO / UNAIDS HIV and malaria inputs (also applied by the full rebuild):
  `python who_inputs.py --download`
- Constant-dollar GDP and IHME government health spending as a share of GDP:
  `python add_constant_dollars.py`
- `country_data/`, `spending_data/`, `macro_data/`, `revenue_data/` and `cofog_all/` were built by earlier
  scripts that are not in this repository.
