"""
Step 3: compare the independent recalculation (audit/recompute_results.csv, written from audit/METHOD.md without the
model code) with the dashboard's own functions. Run from the repo root:

    .venv/bin/python audit/compare_recompute.py

Writes audit/recompute_compare.csv (every value side by side) and prints the differences over 0.5%.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
logging.disable(logging.WARNING)

import health_model as hm  # noqa: E402
import model_section as ms  # noqa: E402
import scenarios as scn  # noqa: E402

I, P = hm.load_inputs(), hm.load_params()
RESP = {"none": scn.DEFAULT_FISCAL, "custom25": ("custom", 0.25, True, "pro_rata", "p75")}


def dashboard_values(iso, scen, resp):
    sc = scn.build_scenario(scen, scn.default_opts(scen, I["ci"]), I["ci"])
    r = hm.run_country(iso, sc, hm.Fiscal(*RESP[resp]), I, P, n_draws=400)
    rc = hm.run_country(iso, sc, hm.Fiscal(*RESP[resp]), I, P, n_draws=0)       # every draw = central
    T, L, C = r["totals"], r["lines"].set_index("line"), r["committed"]
    out = {("TOTAL", "aid_at_risk"): T["gross"], ("TOTAL", "replaced"): T["replaced"], ("TOTAL", "net_loss"): T["net"],
           ("TOTAL", "baseline_aid"): T["base"], ("TOTAL", "deaths_y1"): T["deaths_y1"],
           ("TOTAL", "deaths_5y"): T["deaths_5y"], ("TOTAL", "after_2030_total"): C["after_2030"],
           # the dashboard showed the median of the draws for infections until I-05; it now shows the central run
           ("TOTAL", "hiv_infections_5y"): rc["buckets"].set_index("bucket").loc["HIV", "infections_5y"],
           ("TOTAL", "hiv_infections_5y_SHOWN"): r["buckets"].set_index("bucket").loc["HIV", "infections_5y"]}
    for k, v in C["after_parts"].items():
        out[(f"after_{k}", "deaths")] = v
    for ln in hm.ALL_DIRECT:
        x = L.loc[ln]
        out[(ln, "eff_loss")] = x["gross_loss_usd"]
        out[(ln, "net_line")] = x["net_loss_usd"]
        out[(ln, "units_lost")] = x["units_lost"]
        out[(ln, "deaths_y1")] = x["deaths_y1"]
        out[(ln, "deaths_5y")] = x["deaths_5y"]
        if x["need"] == x["need"] and x["need"] > 0 and x["cov0"] == x["cov0"]:
            out[(ln, "cov_before")] = x["cov0"]
            out[(ln, "cov_after")] = max(x["cov0"] - x["cov_drop_pp"] / 100, 0)
    for c in ms._per_million_cards(iso, P.to_json(orient="split"), True, iso):
        b = c["bucket"]
        if c["people_n"] is None:                       # no aid for this disease
            continue
        people = float(c["people_n"].replace(",", ""))
        deaths = float(c["deaths"].replace(",", ""))
        out[(f"card_{b}", "people")] = people
        out[(f"card_{b}", "cov_drop_pp")] = float(c["cov_n"].replace(",", "")) if c["cov_n"] else np.nan
        out[(f"card_{b}", "deaths_5y")] = deaths
        out[(f"card_{b}", "aid_per_death")] = 5e6 / deaths if deaths > 0 else np.nan
    return out


def main():
    rc = pd.read_csv(ROOT / "audit" / "recompute_results.csv")
    rows = []
    for (iso, scen, resp), g in rc.groupby(["iso3", "scenario", "response"]):
        if scen == "America First MOUs":
            # redefined after the independent recalculation (I-02/I-03/I-08: yearly schedules, group A only), so the
            # recomputation's version of it no longer describes the model; tests/test_mou.py checks the new preset
            continue
        dv = dashboard_values(iso, scen, resp)
        indep = {(r.line, r.metric): r.value for r in g.itertuples()}
        for key in sorted(set(dv) | set(indep)):
            a, b = indep.get(key, np.nan), dv.get(key, np.nan)
            diff = (a - b) / abs(b) * 100 if b == b and abs(b) > 1e-9 else (0.0 if a == a and abs(a) < 1e-6 else np.nan)
            rows.append({"iso3": iso, "scenario": scen, "response": resp, "line": key[0], "metric": key[1],
                         "independent": a, "dashboard": b, "pct_diff": diff})
    df = pd.DataFrame(rows)
    # the card values are displayed rounded to whole numbers / one decimal; compare at that precision
    disp_round = df["line"].str.startswith("card_") & df["metric"].isin(["people", "deaths_5y", "cov_drop_pp"])
    df["material"] = (df["pct_diff"].abs() > 0.5) & ~(disp_round & ((df["independent"] - df["dashboard"]).abs() <= 0.5))
    df.loc[df["metric"].str.contains("SHOWN"), "material"] = False
    df.to_csv(ROOT / "audit" / "recompute_compare.csv", index=False)
    both = df.dropna(subset=["independent", "dashboard"])
    print(f"{len(both)} values compared; {int(df['material'].sum())} differ by more than 0.5%")
    print(df[df["material"]].to_string(max_rows=80))
    shown = df[df["metric"].str.contains("SHOWN")].merge(
        df[(df["line"] == "TOTAL") & (df["metric"] == "hiv_infections_5y")],
        on=["iso3", "scenario", "response"], suffixes=("_shown", "_central"))
    print("\nNew HIV infections: shown on the dashboard vs central run (equal since the I-05 fix)")
    print(shown[["iso3", "scenario", "response", "dashboard_shown", "dashboard_central"]].assign(
        pct=lambda d: (d.dashboard_shown / d.dashboard_central - 1) * 100).round(1).to_string())


if __name__ == "__main__":
    main()
