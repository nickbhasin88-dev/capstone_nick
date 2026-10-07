# Funding-shock model: money -> coverage -> lives

Section 4 of the dashboard. For any country it answers: *if this much aid is lost in this health bucket, how much
coverage falls and how many more people die?* Buckets: HIV, TB, malaria, immunization.

## Files

| File | What it is |
|---|---|
| `app.py` | Your dashboard, unchanged except: section 3 is wrapped in a function (so a country with no IMF data no longer stops the page) and section 4 is added at the end. |
| `model_section.py` | Section 4 UI: scenario controls, charts, tables. |
| `health_model.py` | The model itself (no Streamlit). Import it in a notebook to run anything in batch. |
| `model_params.csv` | Every unit cost and effect size, with low/central/high and a source note. Edit here, or live in the app. |
| `prepare_model.py` | Rebuilds `model_data/` from the raw IHME files + the MOU sheet (+ `ext_data/`). |
| `model_data/` | Prebuilt inputs: `dah_lines.csv`, `country_inputs.csv`, `ihme_trend.csv`, `panel.csv`, `regressions.json`. |
| `ext_data/` | WDI / WHO / UNAIDS / UN IGME series pulled from Gapminder's GitHub mirrors (so the build is reproducible offline). |

## Run

Put these next to your existing `country_data/`, `spending_data/`, etc., then:

```
pip install streamlit plotly pandas numpy openpyxl
streamlit run app.py
```

To rebuild inputs (e.g. after updating the MOU sheet):

```
python prepare_model.py --dah IHME_DAH_DATABASE_1990_2026_Y2026M09D18.CSV \
  --spend IHME_HEALTH_SPENDING_1995_2023_Y2026M09D21.CSV \
  --expected IHME_EXPECTED_HEALTH_SPENDING_2024_2050_Y2026M09D23.CSV \
  --gdp IHME_GDP_1960_2050_FGH_2026_Y2026M06D11.CSV \
  --mou co-financing_MOU.xlsx            # add --download to refresh ext_data/ from GitHub
```

## The chain

1. **Money.** Baseline = 2021-23 average IHME DAH by *source x channel x program area*. A scenario sets a cut per
   cell, so a US cut to the Global Fund hits Kenya's malaria nets in proportion to the US share of what the Global
   Fund spends there. Untagged program money is spread over the bucket's known mix; a share kappa of lost systems money
   (labs, HR, M&E) becomes lost services.
2. **Fiscal response.** Government replacement = min(theta x loss, capacity). Capacity = GHES x (75th or 90th percentile
   minus median real GHES growth, 2001-23) x debt-stress factor (interest/revenue). The historical theta is estimated
   from a 97-country fixed-effects panel: about -0.19 (95% CI -0.45 to +0.07), i.e. no evidence that governments
   backfilled past aid declines. Replacement can be allocated pro-rata or "lives first".
3. **Coverage.** People losing a service = net loss / unit cost x (1 - continuity), capped at the number now covered.
   Coverage drop = that / population in need (PLHIV, HIV+ pregnancies, TB incidence, population at malaria risk,
   malaria cases, births).
4. **Lives.** ART interruption hazards (1.2% rising to 5%/yr) + onward HIV transmission; PMTCT infant infections and
   deaths; WHO TB case-fatality ratios (untreated vs treated, by HIV status); Lives Saved Tool equations for malaria;
   Gavi/VIMC deaths averted per child immunised scaled by under-5 mortality.
5. **Uncertainty.** 400 Monte Carlo draws from triangular(low, central, high) for every parameter.
6. **Cross-check.** Two-way fixed-effects regressions of ART coverage, TB treatment coverage and DTP3 on aid per person
   in need (2005-23). These give a lower bound; the unit-cost model gives the abrupt-cut case.

## Scenario presets

Full US exit; America First MOUs (team's 2026-30 schedules, year selectable); IHME 2025 preliminary estimates
(data-driven); OECD-reported 2025 ODA cuts; Global Fund & Gavi shortfalls; Combined retreat; Custom.

## Things to improve with more time / data

- Replace default unit costs with country-specific costing (PEPFAR expenditure analysis, Global Fund budgets, cMYPs).
- Malaria: WHO World Malaria Report country deaths/cases and population at risk would replace the approximations
  (child deaths / 0.76; at-risk share 0.95 in SSA).
- Add MOU co-financing commitments as a separate "committed domestic replacement" input.
- Add MNCH/nutrition if the team re-expands scope.
