"""
Batch 5+6, item A3: diagnosis of the malaria cap (IMP-04) by intervention, and the intervention-specific donor share.
Read-only with respect to the model; batch34_inputs.py --donor56 writes the shares into model_data/country_inputs.csv.

    .venv/bin/python audit/batch56_malaria_cap.py [--after]

Step 1 (diagnosis, every malaria country; the five largest by WHO 2024 malaria deaths are printed): for bednets,
spraying and case management under Full US Exit (central, no response, sudden): lost donor money for the intervention
(net loss, US$ a year, after the Batch 3+4 split of unspecified money); people covered implied by that money before
any cap (lost money / the model's unit cost); current coverage (MAP measure, population base, year); the share now
used in the cap (external share of public malaria spending for bednets and spraying, all-source share for case
management; GHED); deaths 2026-30 before and after the cap. "Before the cap" is a run with every donor share set to
1 (the pre-IMP-04 rule: the pool is everyone covered); "after" is the current rule.

Step 2 (intervention-specific donor share): share_l = (donor money for intervention l, baseline, after the split of
unspecified money by purpose) / (people covered x the model's unit cost for l), capped at 1. Donor money for l =
E_base[l] (`health_model.run_country`, central). People covered = MAP coverage x population base (bednets: ITN use x
population at risk; spraying: the coverage the model uses x population at risk; case management: effective treatment
x MAP clinical cases). Unit costs: uc_itn 2.2 per person-year of net use, uc_irs 8.5 per person-year protected,
uc_mal_cm 14 per case treated (model_params.csv). Where the country's IHME malaria money has no programme-area split
at all (every known malaria line is 0 in dah_lines.csv: none of the 70 countries), the WHO-region median share would
apply. New pool = people covered x share_l.
Writes audit/logic_review/batch56_malaria_cap.csv.
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
import scenarios as scn  # noqa: E402

OUT = ROOT / "audit" / "logic_review" / "batch56_malaria_cap.csv"
LINES = ["mal_itn", "mal_irs", "mal_cm"]
PRESET = "Full US exit"
MAP_MEASURE = {"mal_itn": "MAP ITN use (share of people sleeping under a net) x population at risk",
               "mal_irs": "MAP IRS coverage (households sprayed) or donor-implied coverage x population at risk",
               "mal_cm": "MAP effective treatment per 100 cases x MAP clinical cases"}


def run(I, P, iso, sc, donor_one=False):
    I2 = I
    if donor_one:
        ci = I["ci"].copy()
        for c in ("donor_share_malaria", "donor_share_malaria_prev", "donor_share_mal_itn", "donor_share_mal_irs", "donor_share_mal_cm"):
            if c in ci.columns:
                ci[c] = 1.0
        I2 = dict(I, ci=ci)
    return hm.run_country(iso, sc, hm.Fiscal(*scn.DEFAULT_FISCAL), I2, P, n_draws=0)["lines"].set_index("line")


def main():
    I, P = hm.load_inputs(), hm.load_params()
    ci = I["ci"]
    sc = scn.build_scenario(PRESET, scn.default_opts(PRESET, ci), ci)
    lines = I["lines"]
    raw = lines[lines.line.isin(LINES)].groupby(["iso3", "line"]).usd.sum().unstack().reindex(columns=LINES).fillna(0)
    rows = []
    for iso in sorted(set(lines.iso3)):
        if not (ci.loc[iso, "malaria_deaths"] > 0):
            continue
        L_now, L_nocap = run(I, P, iso, sc), run(I, P, iso, sc, donor_one=True)
        for l in LINES:
            a, b = L_now.loc[l], L_nocap.loc[l]
            covered = a.cov0 * a.need if a.need == a.need and a.cov0 == a.cov0 else np.nan
            money_buys = a.base_usd / a.unit_cost
            rows.append({
                "iso3": iso, "line": l, "malaria_deaths_2024": ci.loc[iso, "malaria_deaths"],
                "donor_money_base_usd": a.base_usd, "lost_money_usd": a.net_loss_usd,
                "people_implied_by_lost_money": a.net_loss_usd / a.unit_cost, "unit_cost": a.unit_cost,
                "coverage": a.cov0, "coverage_source": a.cov_source, "population_base": a.need, "people_covered": covered,
                "coverage_measure": MAP_MEASURE[l], "share_used_now": a.donor_share_ext,
                "pool_now": covered * a.donor_share_ext if covered == covered else np.nan,
                "cap_binds_now": bool(a.donor_exceeds_cost),
                "units_lost_before_cap": b.units_lost, "units_lost_now": a.units_lost,
                "deaths_before_cap": b.deaths_5y, "deaths_now": a.deaths_5y,
                "money_buys_people": money_buys,
                "share_specific": float(min(1.0, money_buys / covered)) if covered and covered == covered and covered > 0 else np.nan,
                "raw_line_money_usd": float(raw.loc[iso, l]) if iso in raw.index else 0.0,
                "raw_malaria_lines_total_usd": float(raw.loc[iso].sum()) if iso in raw.index else 0.0,
                "who_region": ci.loc[iso, "who_region"],
            })
    t = pd.DataFrame(rows)
    # fallback: countries with no programme-area split (all known malaria lines 0) get the regional median of share_specific
    t["share_source"] = "donor money for the line / (people covered x unit cost), capped at 1"
    med = t.groupby(["who_region", "line"]).share_specific.median()
    for i, r in t.iterrows():
        if r.raw_malaria_lines_total_usd <= 0 or not (r.share_specific == r.share_specific):
            v = med.get((r.who_region, r.line), np.nan)
            v = float(t[t.line == r.line].share_specific.median()) if pd.isna(v) else float(v)
            t.loc[i, "share_specific"], t.loc[i, "share_source"] = v, f"regional median ({r.who_region})" if not pd.isna(med.get((r.who_region, r.line), np.nan)) else "median of all malaria countries"
    t.to_csv(OUT, index=False)
    pd.set_option("display.width", 300); pd.set_option("display.max_columns", 40)
    top5 = t.drop_duplicates("iso3").nlargest(5, "malaria_deaths_2024").iso3.tolist()
    cols = ["iso3", "line", "lost_money_usd", "people_implied_by_lost_money", "coverage", "coverage_source", "population_base", "people_covered", "share_used_now", "pool_now", "cap_binds_now", "deaths_before_cap", "deaths_now", "money_buys_people", "share_specific"]
    print("five largest malaria countries (WHO 2024 deaths):", top5)
    print(t[t.iso3.isin(top5)][cols].round(3).to_string())
    print("\ncap binds now:", t.groupby("line").cap_binds_now.sum().to_dict())
    print("share_specific == 1 (donor money exceeds the cost of current coverage):", t[t.share_specific >= 1 - 1e-9].groupby("line").size().to_dict())
    print("share_specific median by line:", t.groupby("line").share_specific.median().round(2).to_dict())
    print("deaths now by line (all countries):", t.groupby("line").deaths_now.sum().round(0).to_dict(), "total", round(t.deaths_now.sum()))
    print("deaths before cap by line:", t.groupby("line").deaths_before_cap.sum().round(0).to_dict(), "total", round(t.deaths_before_cap.sum()))


if __name__ == "__main__":
    main()
