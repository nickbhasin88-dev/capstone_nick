"""
W-6 The government response needed (audit/gov_response): for each MOU country, the share of the lost US bilateral aid
the government would have to replace (cents per aid dollar) to hold ART, TB treatment and routine vaccination at
their baseline coverage, using the model's own fiscal machinery (health_model.Fiscal: 'custom' mode with a set share
theta; 'lives_first' allocation refills services in the model's deaths-per-dollar order, so the three services are
protected first; 'pro_rata' spreads replacement over every line, so holding them flat needs the whole loss). The cost
is compared with government health spending (GHES 2023), revenue, the model's fiscal-space capacity, the historical
19 cents (and the zero found for low-income countries in W-1) and the country's usual GHES growth. America First MOUs
preset, US bilateral MOU schedule only, dashboard defaults otherwise, central runs (the needed share is a money
calculation; deaths shown with 400-draw ranges).

    .venv/bin/python audit/gov_response/run_gov_response.py [--draws 400]

Outputs: RESULTS_gov_response.md, gov_response.csv. Read-only with respect to the model.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "audit" / "reallocation"))
logging.disable(logging.WARNING)
import health_model as hm  # noqa: E402
import scenarios as scn  # noqa: E402
import run_reallocation_2027 as rr  # noqa: E402

fmt, sfmt, md_table = rr.fmt, rr.sfmt, rr.md_table
PROTECT = ["hiv_art", "tb_ds", "tb_dr", "imm"]
THETA_HIST = 0.19


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=400)
    a = ap.parse_args()
    alloc = pd.read_csv(ROOT / "audit" / "reallocation" / "allocations_2027.csv").set_index("iso3")
    isos, names = list(alloc.index), alloc["country"].to_dict()
    I, P = hm.load_inputs(), hm.load_params()
    ci = I["ci"]
    sc = scn.build_scenario(rr.PRESET, {}, ci)
    sc.pair = {}
    sc_full = scn.build_scenario(rr.PRESET, {}, ci)
    th_c, th_lo, th_hi = hm.theta_historical(I["reg"])

    def run(i, fiscal, draws=0):
        return hm.run_country(i, sc, fiscal, I, P, n_draws=draws, keep_draws=True, mortality_trend=rr.TREND)

    def protected_units(r):
        U = r["draws"]["units"]
        return float(max(sum(U[l][0, t] for l in PROTECT) for t in range(5)))

    rows = []
    for i in isos:
        none = hm.Fiscal(*scn.DEFAULT_FISCAL)
        r0 = run(i, none)
        rd = run(i, none, a.draws)
        rf = hm.run_country(i, sc_full, none, I, P, n_draws=0, mortality_trend=rr.TREND)
        yt = r0["years"].set_index("year")
        G = yt["aid_lost_usd"].to_numpy()
        G_full = rf["years"].set_index("year")["aid_lost_usd"].to_numpy()
        fs = r0["fiscal"]
        hb = hm.health_budget(i, I)
        row = ci.loc[i]
        base_prot = protected_units(r0)
        # bisection on theta, lives-first, uncapped: smallest share that leaves no one off the three services in any year
        lo, hi = 0.0, 1.0
        for _ in range(22):
            mid = (lo + hi) / 2
            r = run(i, hm.Fiscal("custom", mid, False, "lives_first", "p75"))
            if protected_units(r) <= max(1.0, 1e-4 * base_prot):
                hi = mid
            else:
                lo = mid
        theta = hi
        r_star = run(i, hm.Fiscal("custom", theta, False, "lives_first", "p75"))
        rd_star = run(i, hm.Fiscal("custom", theta, False, "lives_first", "p75"), a.draws)
        L = r_star["lines"].set_index("line")
        refilled = [l for l in L.index if L.loc[l, "replaced_usd"] > 1 and L.loc[l, "gross_loss_usd"] > 1]
        # with the fiscal-space cap (the dashboard's 'Replace a set share' always caps): what is reached
        r_cap = run(i, hm.Fiscal("custom", theta, True, "lives_first", "p75"))
        r_max = run(i, hm.Fiscal("max", 0.0, True, "lives_first", "p75"))
        r_hist = run(i, hm.Fiscal("custom", THETA_HIST, True, "lives_first", "p75"))
        ghes = float(row["ghes_2023"])
        rev = fs["revenue"]
        gov = hb["gov_spend_usd"]
        g_med = float(row["ghes_growth_median"])
        peak_t = int(np.argmax(G))
        need_usd_peak = theta * G[peak_t]
        need_usd_mean = theta * G.mean()
        d = {"iso3": i, "country": names[i], "aid_lost_peak_usd": G[peak_t], "peak_year": 2026 + peak_t, "aid_lost_mean_usd": G.mean(),
             "aid_lost_peak_with_exits_usd": G_full.max(),
             "theta_lives_first": theta, "refilled_lines": ",".join(refilled),
             "need_usd_peak": need_usd_peak, "need_usd_mean": need_usd_mean,
             "ghes_2023": ghes, "need_pct_ghes_peak": need_usd_peak / ghes * 100, "need_pct_ghes_mean": need_usd_mean / ghes * 100,
             "revenue_usd": rev, "need_pct_revenue_peak": need_usd_peak / rev * 100 if rev == rev else np.nan,
             "gov_spend_usd": gov, "need_pp_of_gov_budget": need_usd_peak / gov * 100 if gov == gov else np.nan,
             "health_share_pct": hb["share_pct"], "capacity_usd": fs["capacity"], "need_pct_capacity_peak": need_usd_peak / fs["capacity"] * 100 if fs["capacity"] else np.nan,
             "ghes_growth_median": g_med, "years_of_usual_growth": np.log1p(need_usd_peak / ghes) / np.log1p(g_med) if g_med > 0 else np.nan,
             "gdp_growth_weo": float(row.get("gdp_growth_weo_2026_30", np.nan)),
             "prot_units_none": base_prot, "prot_units_capped_theta": protected_units(r_cap), "prot_units_max": protected_units(r_max), "prot_units_hist19": protected_units(r_hist),
             "theta_hist_cents": THETA_HIST,
             "deaths_5y_none": float(r0["totals"]["deaths_5y"]), "deaths_5y_none_lo": float(rd["totals"]["deaths_5y_lo"]), "deaths_5y_none_hi": float(rd["totals"]["deaths_5y_hi"]),
             "deaths_5y_theta": float(r_star["totals"]["deaths_5y"]), "deaths_5y_theta_lo": float(rd_star["totals"]["deaths_5y_lo"]), "deaths_5y_theta_hi": float(rd_star["totals"]["deaths_5y_hi"]),
             "deaths_5y_max": float(r_max["totals"]["deaths_5y"]), "replaced_max_mean_usd": float(r_max["totals"]["replaced"]),
             "art_py_none": float(max(r0["draws"]["units"]["hiv_art"][0])), "tb_none": float(max(sum(r0["draws"]["units"][l][0] for l in ("tb_ds", "tb_dr")))),
             "imm_none": float(max(r0["draws"]["units"]["imm"][0])), "interest_pct_revenue": fs["interest_pct_revenue"], "stress_factor": fs["stress_factor"]}
        rows.append(d)
    R = pd.DataFrame(rows).set_index("iso3")
    R.to_csv(HERE / "gov_response.csv")
    tot_G = R.aid_lost_peak_usd.sum()
    tot_need = R.need_usd_peak.sum()
    md = ["# W-6. The government response needed to hold ART, TB treatment and vaccination flat (no model changes)", "",
          "Generated by `audit/gov_response/run_gov_response.py`. America First MOUs preset, US bilateral MOU schedule only (US "
          "multilateral exits off; the peak-year loss with them on is shown for reference), dashboard defaults otherwise, "
          f"{a.draws} draws for the death ranges. For each country the smallest replacement share theta (the dashboard's "
          "'Replace a set share', `health_model.Fiscal` mode custom) that leaves nobody off ART, TB treatment (DS and DR) or "
          "routine vaccination in any year 2026-2030, with the 'lives first' allocation (services refilled in the model's "
          "deaths-per-dollar order, so these three come first) and no fiscal-space cap; found by bisection (22 steps). "
          "Under the dashboard's default pro-rata allocation the whole loss has to be replaced (theta = 1) to hold any one "
          "service flat, because replacement is spread over every line in proportion to its loss. The cost is theta x the "
          "peak year's aid lost (usually 2030, when the MOU cuts are deepest).", ""]
    md += ["## Step 1. The replacement share and what it costs", "",
           md_table(["Country", "Peak-year US bilateral aid lost (US$M, year)", "with multilateral exits", "theta needed (cents per aid US$1, lives first)",
                     "Lines refilled at theta", "Cost in peak year US$M", "% of GHES 2023", "% of revenue", "pp of total government budget (health share now)",
                     "% of the model's fiscal-space capacity", "Years of usual GHES growth it equals"],
                    [[r.country, f"{r.aid_lost_peak_usd / 1e6:,.1f} ({int(r.peak_year)})", f"{r.aid_lost_peak_with_exits_usd / 1e6:,.1f}", f"{r.theta_lives_first:.2f}",
                      r.refilled_lines, f"{r.need_usd_peak / 1e6:,.1f}", f"{r.need_pct_ghes_peak:.1f}%",
                      f"{r.need_pct_revenue_peak:.2f}%" if r.need_pct_revenue_peak == r.need_pct_revenue_peak else "n/a (no revenue data)",
                      f"{r.need_pp_of_gov_budget:.2f} pp ({r.health_share_pct:.1f}%)" if r.need_pp_of_gov_budget == r.need_pp_of_gov_budget else "n/a",
                      f"{r.need_pct_capacity_peak:.0f}%" if r.need_pct_capacity_peak == r.need_pct_capacity_peak else "n/a",
                      (f"{r.years_of_usual_growth:.1f}" if r.years_of_usual_growth < 50 else ">50") + f" (median real growth {r.ghes_growth_median:.1%}/yr)" if r.years_of_usual_growth == r.years_of_usual_growth else "n/a (median growth <= 0)"]
                     for r in R.sort_values("need_pct_ghes_peak", ascending=False).itertuples()]), "",
           f"Totals, 15 countries, peak year: aid lost US${tot_G / 1e6:,.0f}M; replacement needed US${tot_need / 1e6:,.0f}M "
           f"({tot_need / tot_G:.0%} of the loss); {tot_need / R.ghes_2023.sum() * 100:.1f}% of their combined GHES 2023 "
           f"(US${R.ghes_2023.sum() / 1e9:,.1f}B).", ""]
    md += ["## Step 2. Against the historical response and the model's fiscal space", "",
           f"Historical benchmark (`regressions.json`, W-1): theta {th_c:+.2f} (95% CI {th_lo:+.2f} to {th_hi:+.2f}) pooled; about 0 "
           "in low-income and aid-dependent countries. The table shows what the three protected services look like with no "
           "response, with the historical 19 cents (if it were replacement rather than co-movement), with theta capped by the "
           "model's fiscal-space capacity (the dashboard always caps a set share), and with 'as much as fiscal space allows'.", "",
           md_table(["Country", "People off the three services, no response (peak year)", "with 19 cents replacement", "with theta needed, capped by fiscal space", "as much as fiscal space allows",
                     "Fiscal-space capacity US$M/yr", "Interest % of revenue (stress factor)", "Deaths 2026-30 no response (range)", "Deaths 2026-30 at theta (range)"],
                    [[r.country, fmt(r.prot_units_none), fmt(r.prot_units_hist19), fmt(r.prot_units_capped_theta), fmt(r.prot_units_max), f"{r.capacity_usd / 1e6:,.1f}",
                      f"{r.interest_pct_revenue:.0f}% ({r.stress_factor:.2f})", f"{fmt(r.deaths_5y_none)} ({fmt(r.deaths_5y_none_lo)}-{fmt(r.deaths_5y_none_hi)})",
                      f"{fmt(r.deaths_5y_theta)} ({fmt(r.deaths_5y_theta_lo)}-{fmt(r.deaths_5y_theta_hi)})"] for r in R.itertuples()]), ""]
    md += ["## Step 3. Reading", "",
           f"- theta needed ranges from {R.theta_lives_first.min():.2f} ({R.theta_lives_first.idxmin()}) to {R.theta_lives_first.max():.2f} "
           f"({R.theta_lives_first.idxmax()}): the share of each country's lost US money that sits on treatment and vaccine lines "
           "(plus the lines the model ranks above them). The rest of the loss is prevention, testing, OVC, programme management and "
           "systems money, which this exercise lets go.",
           f"- As a share of GHES the peak-year cost runs from {R.need_pct_ghes_peak.min():.1f}% ({R.need_pct_ghes_peak.idxmin()}) to "
           f"{R.need_pct_ghes_peak.max():.1f}% ({R.need_pct_ghes_peak.idxmax()}); countries above 10% would need more than a decade "
           "of their usual real GHES growth to absorb it, and more than the model's fiscal-space capacity in "
           f"{int((R.need_pct_capacity_peak > 100).sum())} of 15 countries.",
           "- Caveats: GHES 2023 and revenue are IHME / World Bank levels in current US$; revenue is missing for Liberia, Nigeria "
           "and Sierra Leone; fiscal-space capacity is the model's labelled assumption (a strong year's extra GHES growth x a "
           "debt-stress factor); the 'lives first' allocation is a best case the dashboard labels as hypothetical; the MOU "
           "co-financing commitments are not modelled; costs are in the model's 2023 US$ while MOU amounts are nominal.", ""]
    (HERE / "RESULTS_gov_response.md").write_text("\n".join(md))
    print("wrote RESULTS_gov_response.md, gov_response.csv")
    print(R[["theta_lives_first", "need_pct_ghes_peak", "need_pct_capacity_peak", "years_of_usual_growth"]].round(2).to_string())


if __name__ == "__main__":
    main()
