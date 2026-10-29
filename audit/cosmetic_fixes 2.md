# I-12, I-18, I-19, I-20, I-21, I-22, I-24: wording fixes. Fixed

These are wording-only changes; no displayed number changed (verified below).

## Changes by file

### `model_section.py`

- **I-12, headline card:** "Net Loss to Services" is now "Net Aid Lost".
  - Sub-line: "incl. {money} health-systems money, {kappa:.0%} counted as lost services (assumption)". It is hidden when
    that amount is 0. The amount is the yearly health-systems aid lost, net of replacement in proportion.
  - Tooltip: "Health-systems money (labs, staff, data systems) supports services indirectly. We assume {kappa:.0%}… vary
    this from {low:.0%} to {high:.0%}."
  - kappa, low and high are read from `hss_kappa` in the parameter table (model_params.csv, or edited values in the
    app).
  - New function: `net_aid_note`.
- **I-12, other mentions:**
  - the Other Aid caption: "…match Aid at Risk and Net Aid Lost";
  - the All Countries pill note: "Net of Backfill" becomes "Net Aid Lost";
  - the scatter hover: "net loss" becomes "net aid lost".
- **I-18 and I-20, Government Response tooltip:** the new `backfill_regression_text` gives "Across {n} countries,
  {first}-{last}, governments did not replace falling aid ({theta} per $1, 95% CI {lo} to {hi})." Every value is read
  from `regressions.json`, so it now shows 97 countries, **2002-2023** (the hard-coded "2001-2023" is gone).
- **I-20, one name for the no-replacement option:** "No Government Replacement" everywhere.
  - The dropdown option (was "No backfill (historical norm)") and the `_resp_label` used in captions and the comparison
    view (was "No backfill"; the unused "Historical behaviour" label too).
  - The summary kicker already used it.
  - Backfill sentence: "Government backfill of … compared with no backfill" becomes "Government replacement of …
    compared with no government replacement".
  - Help texts: "Backfill capacity" becomes "Replacement capacity" (fiscal panel help and bar tooltip), and "where
    backfill runs out" becomes "where replacement runs out".
- **I-19, deaths tooltip:** the Extra Deaths Over 5 Years tooltip comes from `deaths_basis_text`:
  - Sudden: "Assumes the cut is sustained for five years."
  - Phased paths: "Follows the chosen phase-out path, 2026-2030."
  - America First MOUs: "Follows {Country}'s MOU schedule, 2026-2030."
  - The comparison view applies the same rule to Scenario B.
- **I-24, card footer:** "Cost {cost} per {unit} · About {money} of aid lost per life lost (based on US$1M a year for
  5 years)".
  - Tooltip: "Total aid lost over 5 years ($5M) divided by extra deaths over the same 5 years; this equals $1M divided by
    the average extra deaths per year."

### `scenarios.py`

- **I-21:** the MOU schedule caption adds "Cuts compare MOU amounts (nominal US$, as written in the MOU) with the
  2021-2025 reference."
- **I-20:** a comment now says "No Government Replacement".

### `views/1_Dashboard.py`

- **I-21:** the header reads "All dollar figures in constant 2023 US$ (except MOU amounts)".

### `views/3_Validation.py`

- **I-22:** the UNAIDS published figure "4.2M" becomes "More than 4 million".
- **I-20:**
  - caption: "no government backfill" becomes "No Government Replacement";
  - note: "net of any government backfill" becomes "net of any government replacement".

### `views/4_Methods.py`

- **I-20:** "No Backfill (Historical Norm)" becomes "No Government Replacement"; "Why no backfill is the historical
  norm" becomes "Why No Government Replacement is the default". The regression years were already read from
  `regressions.json`.
- **I-12:** the outputs table now says "Net Aid Lost", including the health-systems / kappa note.
- **I-24:** the per-US$1M definition uses the new footer wording and the $1M ÷ average-yearly-deaths equivalence.
- **I-21:**
  - "Every dollar figure is in constant 2023 US dollars (except MOU amounts)…", plus the line "MOU cut percentages
    compare each year's MOU amount with the 2021-2025 reference in the same nominal dollars; the rest of the dashboard
    uses constant 2023 US$."
  - The MOU sheet row says "(nominal US$, as written in the MOU)".

### `theme.py`

- **I-12, I-20:** the docstring example "Net of Backfill" becomes "Net Aid Lost".

### `model_params.csv`

- **I-22:** the `art_hazard_mult` source note appends "(approximate; UNAIDS reports 'more than 4 million')" after
  "UNAIDS Goals (4.2M deaths)". The parameter value is unchanged.

## Old wording check

A final grep of app.py, model_section.py, paths_ui.py, theme.py, scenarios.py and views/ for "No Backfill", "Historical
Norm", "no backfill", "Historical Behaviour", "Net Loss to Services", "Net of Backfill", "4.2M", "of aid per death" and
"97 countries, 2001" finds no displayed text. The remaining matches are internal names, not shown on screen:
- the `BACKFILL` color constant;
- the `backfill_regression_text` function name.

There is no `pages/` folder (pages live in `views/`). "2001-2023" still appears where it names other data windows (IHME
GHES growth, the health-share history), not the backfill regression.

## Verification

- **Every displayed number is identical.** `audit/snapshot_numbers.py` saved every displayed number before and after:
  - 8,470 runs (70 countries x 7 presets x 4 responses x 5 funding paths; America First MOUs for its 16 countries on
    their own schedule);
  - plus the six All Countries files;
  - 355 values each: totals, buckets, lines and ranges, yearly deaths, 2031-2035 parts, fiscal panel, health budget,
    break-even, and the four per-US$1M cards.
  - Diff: 3,006,850 values compared, **0 differ**.
  - The two snapshot files (`audit/before_cosmetic.csv`, `audit/after_cosmetic.csv`, 29 MB each) are gitignored;
    re-create them with the script.
- **Tests:** 215 of 215 pass.
- **`audit/checks.py`:** the results file is byte-identical to the previous commit's. The only failing checks are the
  pre-existing ones for open issues I-15 (aid-gain display, IHME 2025 preset), I-10 (Section 3 government level), and
  the 6 small Section 1 / Section 2 aid gaps. Wording changes cannot affect them, and nothing new fails.
