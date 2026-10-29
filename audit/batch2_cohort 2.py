"""
Batch 2, Step 1A: death risk after stopping ART, from a CD4-stage cohort calculation (not part of the model).

    .venv/bin/python audit/batch2_cohort.py

People who stop ART start in the CD4 distribution of people on ART (ZIMPHIA 2020, Table 10.1: median 528 cells/uL,
Q1 366, Q3 706 among adults aware of their status and on ART; men 411 (282, 558), women 603 (437, 768)), then progress
at untreated rates and die at untreated stage-specific rates (Optima HIV, ten Brink et al. 2025 appendix, Table A1
"Disease progression (average years to move)" and Table A2 "Death rate (% HIV-related mortality per year)").
The counterfactual (had they stayed on ART) uses the relative death rate on suppressive ART (Table A2: 23%,
15-30%) applied to the same starting distribution, which is treated as stable while on ART.

Output: the annual death probability (all HIV deaths, and excess over staying on ART) in years 1-10 after stopping,
for the central Optima values and their ranges, for three starting distributions. Written to
audit/logic_review/batch2_cohort.csv and printed.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent / "logic_review" / "batch2_cohort.csv"

STAGES = [">500", "350-500", "200-350", "50-200", "<50"]

# Optima Table A1, disease progression, average years to move (central, low, high).
# Rows: >500 -> 350-500, 350-500 -> 200-350, 200-350 -> 50-200, 50-200 -> <50.
PROG_YEARS = {"central": [0.95, 3.00, 3.74, 1.50],
              "low": [0.62, 2.83, 3.48, 1.13],       # faster progression (fewer years)
              "high": [1.16, 3.16, 4.00, 2.25]}      # slower progression
# Optima Table A2, death rate, % HIV-related mortality per year, untreated, by stage.
DEATH = {"central": [0.0036, 0.0058, 0.0088, 0.059, 0.32],
         "low": [0.0029, 0.0048, 0.0075, 0.054, 0.296],
         "high": [0.0044, 0.0071, 0.0101, 0.079, 0.432]}
# Optima Table A2, relative death rate on ART achieving viral suppression.
REL_ON_ART = {"central": 0.23, "low": 0.15, "high": 0.30}

# Starting CD4 distribution of people on ART (shares of the five stages), from ZIMPHIA 2020 Table 10.1 quartiles,
# interpolated within quartiles (see batch2_evidence.md, Step 1A). The split of <200 into 50-200 and <50 is an
# assumption (4:1), as the survey only reports <200 as one band.
START = {
    "total (median 528; Q1 366, Q3 706)": [0.53, 0.22, 0.20, 0.04, 0.01],
    "men (median 411; Q1 282, Q3 558)": [0.32, 0.28, 0.30, 0.08, 0.02],
    "women (median 603; Q1 437, Q3 768)": [0.64, 0.20, 0.13, 0.025, 0.005],
}

DT = 1 / 120     # time step: 1/10 month
YEARS = 10       # years after stopping ART reported (the model uses 1-5 in 2026-2030 and the later values after 2030)


def run(start, prog, death, rel, years=5):
    """Deterministic compartment model: 5 CD4 stages + dead. Returns annual death probabilities (per person alive at
    the start of the cohort, i.e. deaths in year k / initial cohort) off ART and on ART, years 1..years."""
    rates = [1 / y for y in prog]
    s = np.array(start, dtype=float)
    s = s / s.sum()
    on = s.copy()
    off_deaths, on_deaths = [], []
    n_steps = int(round(1 / DT))
    for k in range(years):
        d_off = d_on = 0.0
        for _ in range(n_steps):
            # off ART: progress and die
            dead = s * np.array(death) * DT
            move = np.zeros(5)
            for i in range(4):
                move[i] = s[i] * rates[i] * DT
            new = s - dead - move
            new[1:] += move[:4]
            s = new
            d_off += dead.sum()
            # on ART: same stage distribution, death at the suppressed relative rate (no progression)
            dead_on = on * np.array(death) * rel * DT
            on = on - dead_on
            d_on += dead_on.sum()
        off_deaths.append(d_off)
        on_deaths.append(d_on)
    return np.array(off_deaths), np.array(on_deaths), s


def main():
    rows = []
    current = np.array([0.012, 0.028, 0.038, 0.045, 0.05])
    for name, start in START.items():
        for case, (prog, death, rel) in {
            "central": (PROG_YEARS["central"], DEATH["central"], REL_ON_ART["central"]),
            "low (slow progression, low death rates, low ART benefit)":
                (PROG_YEARS["high"], DEATH["low"], REL_ON_ART["high"]),
            "high (fast progression, high death rates, high ART benefit)":
                (PROG_YEARS["low"], DEATH["high"], REL_ON_ART["low"]),
        }.items():
            off, on, end = run(start, prog, death, rel, years=YEARS)
            excess = off - on
            rows.append({"start": name, "case": case,
                         **{f"off_y{k + 1}": off[k] for k in range(YEARS)},
                         **{f"on_y{k + 1}": on[k] for k in range(YEARS)},
                         **{f"excess_y{k + 1}": excess[k] for k in range(YEARS)},
                         "off_5y": off[:5].sum(), "excess_5y": excess[:5].sum(), "excess_10y": excess.sum(),
                         "end_share_<200": end[3] + end[4], "end_share_<50": end[4]})
    df = pd.DataFrame(rows)
    OUT.parent.mkdir(exist_ok=True)
    df.to_csv(OUT, index=False)
    pd.set_option("display.width", 250)
    print("Excess death probability after stopping ART (share of the starting cohort dying in each year, minus deaths\n"
          "had they stayed on suppressive ART)")
    for r in df.itertuples():
        ex = [getattr(r, f"excess_y{k}") for k in range(1, YEARS + 1)]
        print(f"{r.start:38s} | {r.case:62s} | excess y1-10: " + " ".join(f"{v:.3f}" for v in ex)
              + f" (5y {r.excess_5y:.3f}, 10y {r.excess_10y:.3f}; all deaths off ART 5y {r.off_5y:.3f})")
    print(f"{'current ART_HAZARD':38s} | {'':62s} | excess: " + " ".join(f"{v:.3f}" for v in current)
          + f" (5y {current.sum():.3f})")


if __name__ == "__main__":
    main()
