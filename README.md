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
bypass that navigation). `theme.py` holds every color, font and chart style. The model is `health_model.py`; the
donor scenarios are in `scenarios.py`; Section 4 is drawn by `model_section.py`.

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
      --expected datasets/IHME_EXPECTED_HEALTH_SPENDING_2024_2050_Y2026M09D23.CSV \
      --gdp datasets/IHME_GDP_1960_2050_FGH_2026_Y2026M06D11.CSV --mou datasets/co-financing_MOU.xlsx
  ```

  (`--precompute-only` re-runs only the all-country results.) The IHME DAH file is too large for GitHub and is kept
  outside the repository.
- Constant-dollar GDP and IHME government health spending as a share of GDP:
  `python add_constant_dollars.py`
- `country_data/`, `spending_data/`, `macro_data/`, `revenue_data/` and `cofog_all/` were built by earlier
  scripts that are not in this repository.
