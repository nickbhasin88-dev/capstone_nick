"""
One-at-a-time sensitivity for the logic review (Part 2). Read-only: the model code is imported and called, never
changed; constants are swapped in memory only for the duration of one run.

    .venv/bin/python audit/logic_review/sensitivity.py

All-country deaths 2026-2030 (and 2031-2035), Full US Exit, No Government Replacement, death-rate trend on, central
run (n_draws = 0), with one input at its low and its high value. Writes sensitivity.csv; tornado.py draws the chart.
"""
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
logging.disable(logging.WARNING)
import health_model as hm  # noqa: E402
import scenarios as scn  # noqa: E402

I0, P0 = hm.load_inputs(), hm.load_params()
SC = scn.build_scenario("Full US exit", {}, I0["ci"])
ISOS = sorted(set(I0["lines"].iso3))
NONE = hm.Fiscal(*scn.DEFAULT_FISCAL)


def total(I=I0, P=P0):
    d5 = after = 0.0
    for c in ISOS:
        r = hm.run_country(c, SC, NONE, I, P, n_draws=0)
        d5 += r["totals"]["deaths_5y"]
        after += r["committed"]["after_2030"]
    return d5, after


def with_param(name, value):
    P = P0.copy()
    P.loc[name, ["central", "low", "high"]] = value
    return total(P=P)


def with_const(attr, value, key=None):
    old = getattr(hm, attr)
    try:
        if key is None:
            setattr(hm, attr, value)
        else:
            new = dict(old)
            new[key] = value
            setattr(hm, attr, new)
        return total()
    finally:
        setattr(hm, attr, old)


def with_ci(col, values):
    ci = I0["ci"].copy()
    ci[col] = values
    return total(I=dict(I0, ci=ci))


rows = []
base = total()
print(f"base: deaths 2026-30 {base[0]:,.0f}, 2031-35 {base[1]:,.0f}")

for p, r in P0.iterrows():
    lo, hi = with_param(p, r["low"]), with_param(p, r["high"])
    rows.append({"input": p, "kind": "parameter", "status": r["status"], "central": r["central"], "low": r["low"],
                 "high": r["high"], "d5_low": lo[0], "d5_high": hi[0], "after_low": lo[1], "after_high": hi[1]})
    print(p, f"{lo[0]:,.0f} / {hi[0]:,.0f}", flush=True)

ci = I0["ci"]
extra = [
    # (name, kind, central text, low text, high text, low run, high run)
    ("DR_TB_SHARE (MDR/RR share of TB incidence)", "constant", 0.04, 0.03, 0.06,
     lambda: with_const("DR_TB_SHARE", 0.03), lambda: with_const("DR_TB_SHARE", 0.06)),
    ("DR_TB_COV (DR-TB treatment coverage)", "constant", 0.45, 0.30, 0.60,
     lambda: with_const("DR_TB_COV", 0.30), lambda: with_const("DR_TB_COV", 0.60)),
    ("LAG tb year 1", "constant", 0.7, 0.5, 1.0,
     lambda: with_const("LAG", np.array([0.5, 1, 1, 1, 1]), "tb_ds"),
     lambda: with_const("LAG", np.array([1.0, 1, 1, 1, 1]), "tb_ds")),
    ("LAG bednets year 1", "constant", 0.5, 0.3, 0.8,
     lambda: with_const("LAG", np.array([0.3, 1, 1, 1, 1]), "mal_itn"),
     lambda: with_const("LAG", np.array([0.8, 1, 1, 1, 1]), "mal_itn")),
    ("ART_HAZARD shape (front-loaded vs flat 3.46%)", "constant", "ramp", "flat", "front-loaded",
     lambda: with_const("ART_HAZARD", np.full(5, 0.0346)),
     lambda: with_const("ART_HAZARD", np.array([0.05, 0.045, 0.038, 0.028, 0.012]))),
    ("Malaria death trend (MAP Pf, clip +/-5%)", "data choice", "as is", "0 (flat)", "unclipped fit",
     lambda: with_ci("trend_malaria_deaths", 0.0),
     lambda: with_ci("trend_malaria_deaths", ci["trend_malaria_deaths_fit"].fillna(0.0))),
    ("Under-5 mortality trend (2010-19)", "data choice", "as is", "0 (flat)", "x1.5",
     lambda: with_ci("trend_u5mr", 0.0), lambda: with_ci("trend_u5mr", ci["trend_u5mr"] * 1.5)),
    ("Malaria cases (MAP vs WHO)", "data choice", "MAP Pf+Pv", "WHO estimate", "WHO estimate",
     lambda: with_ci("malaria_cases", ci["malaria_cases_prev"].fillna(ci["malaria_cases"])), None),
]
for name, kind, c, lo_t, hi_t, f_lo, f_hi in extra:
    lo = f_lo()
    hi = f_hi() if f_hi else lo
    rows.append({"input": name, "kind": kind, "status": "hard-coded" if kind == "constant" else "data",
                 "central": c, "low": lo_t, "high": hi_t, "d5_low": lo[0], "d5_high": hi[0],
                 "after_low": lo[1], "after_high": hi[1]})
    print(name, f"{lo[0]:,.0f} / {hi[0]:,.0f}", flush=True)

d = pd.DataFrame(rows)
d["pct_low"] = d["d5_low"] / base[0] - 1
d["pct_high"] = d["d5_high"] / base[0] - 1
d["swing"] = (d["d5_high"] - d["d5_low"]).abs()
d["base_d5"], d["base_after"] = base
d.sort_values("swing", ascending=False).to_csv(Path(__file__).parent / "sensitivity.csv", index=False)
print("saved sensitivity.csv")
