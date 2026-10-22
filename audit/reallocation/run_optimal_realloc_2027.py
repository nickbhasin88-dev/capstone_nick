"""
Best reallocation of the 2027 US MOU money for deaths, dollar for dollar, solved with the model itself
(audit/reallocation). US$1 of MOU moved = US$1 of US direct aid in the country, spent the way the country's US direct
aid is spent, with the model's own costs, coverage, caps and health effects (America First MOUs, US bilateral schedule
only, dashboard defaults).

Bounds (what the model can represent, plus a policy limit):
  - total unchanged: what one country gains another loses, dollar for dollar;
  - a country receiving money can at most get back its 2021-23 US direct aid (a 0% cut in 2027); the model has no
    coverage above its baseline, so money beyond that point is not allowed rather than extrapolated;
  - a country giving money can at most give the US direct aid it still has in 2027 under the Original MOU;
  - each country's change is within +/- B% of its signed 2027 amount (B = 10, 20, 30);
  - optionally, the total moved is limited to the team's Higher Ceiling (US$133.6M).

Method: each country's deaths 2026-2030 are computed with the model on a US$1M grid of aid changes inside its bounds
(central parameters). The allocation is then improved US$1M at a time: any move of US$1M from one country to another
(either direction) that lowers total deaths is made, best move first, until no move helps (a local optimum on the
model's own curves, which are not straight lines).
The result is re-run with 400 draws (seed 7) for ranges, people losing services and HIV results.

    .venv/bin/python audit/reallocation/run_optimal_realloc_2027.py [--tag _v2]

Outputs: allocations_2027_opt.csv, optimal_curves_2027.csv, RESULTS_optimal_2027.md. Read-only with respect to the model.
"""
from __future__ import annotations

import argparse
import heapq
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
logging.disable(logging.WARNING)
import health_model as hm  # noqa: E402
import run_reallocation_2027 as rr  # noqa: E402

YEAR = 2027
T = rr.YEARS.index(YEAR)
STEP = 1e6
BOUNDS = [0.10, 0.20, 0.30]
fmt, sfmt, md_table = rr.fmt, rr.sfmt, rr.md_table
SIX = ["ART", "TB treatment", "Bednets", "Spraying", "Malaria treatment", "Vaccines"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="_v2")
    ap.add_argument("--draws", type=int, default=400)
    a = ap.parse_args()
    team = pd.read_csv(HERE / f"allocations_{YEAR}{a.tag}.csv").set_index("iso3")
    cols = [c for c in team.columns if c != "country"]
    ref_col = cols[0]
    orig = team[ref_col].astype(float)
    names = team["country"].to_dict()
    isos = list(orig.index)
    I, P = hm.load_inputs(), hm.load_params()
    rr.BILATERAL_ONLY = True
    ci = I["ci"]
    lines = I["lines"]
    B = (lines[(lines.src_grp == "United States") & lines.iso3.isin(isos) & lines.chan_grp.isin(hm.DIRECT_CHANNELS)]
         .groupby("iso3").usd.sum().reindex(isos))
    ref = ci.loc[isos, "mou_us_ref"].astype(float)
    cut0 = (1 - orig / ref).clip(0, 1)
    lost0 = cut0 * B                                         # US direct aid lost in YEAR under the Original MOU

    def amount(i, x):
        """MOU amount whose cut makes the model's US direct aid in YEAR change by +x dollars (face value)."""
        return float(ref[i] * (1 - (cut0[i] - x / B[i])))

    def deaths(i, x, draws=0):
        sc = rr.build(ci, YEAR, {**orig.to_dict(), i: amount(i, x)})
        return hm.run_country(i, sc, rr.FISCAL, I, P, n_draws=draws, mortality_trend=rr.TREND)

    # deaths curves on the grid, inside the model bounds (widest policy bound)
    bmax = max(BOUNDS)
    curves, rows = {}, []
    for i in isos:
        up = min(lost0[i], bmax * orig[i])                     # up to a 0% cut
        dn = min(B[i] - lost0[i], bmax * orig[i])              # down to all remaining US direct aid
        xs = np.unique(np.concatenate([-np.arange(0, dn + 1e-6, STEP), np.arange(0, up + 1e-6, STEP)]))
        d = {x: float(deaths(i, x)["totals"]["deaths_5y"]) for x in xs}
        curves[i] = d
        rows += [{"iso3": i, "country": names[i], "x_usd": x, "deaths_5y": v} for x, v in d.items()]
    pd.DataFrame(rows).to_csv(HERE / f"optimal_curves_{YEAR}.csv", index=False)

    def solve(bound, cap=np.inf):
        """Greedy from zero, then pairwise improvement: move US$1M from any country to any other (either direction)
        whenever it lowers total deaths, within the bounds, until no move helps. Positions are whole US$M."""
        K = {i: {int(round(x / STEP)): v for x, v in curves[i].items()} for i in isos}
        up = {i: int(np.floor(min(lost0[i], bound * orig[i]) / STEP + 1e-9)) for i in isos}
        dn = {i: int(np.floor(min(B[i] - lost0[i], bound * orig[i]) / STEP + 1e-9)) for i in isos}
        pos = {i: 0 for i in isos}
        capk = np.inf if np.isinf(cap) else int(np.floor(cap / STEP + 1e-9))

        def ok(i, k):
            return -dn[i] <= k <= up[i] and k in K[i]

        def moved(p):
            return sum(max(v, 0) for v in p.values())

        while True:
            best = (0.0, None, None)
            for g in isos:
                if not ok(g, pos[g] - 1):
                    continue
                cost = K[g][pos[g] - 1] - K[g][pos[g]]                     # deaths added by giving US$1M
                for r in isos:
                    if r == g or not ok(r, pos[r] + 1):
                        continue
                    d = cost + K[r][pos[r] + 1] - K[r][pos[r]]               # net change in deaths
                    if d < best[0] - 1e-9:
                        q = dict(pos)
                        q[g] -= 1
                        q[r] += 1
                        if moved(q) <= capk:
                            best = (d, g, r)
            if best[1] is None:
                break
            pos[best[1]] -= 1
            pos[best[2]] += 1
        return pd.Series({i: pos[i] * STEP for i in isos})

    teamv = (team["Higher Ceiling"] - orig).clip(lower=0).sum()
    scen = {f"Best within +/-{b:.0%}": solve(b) for b in BOUNDS}
    scen["Best, US$133.6M moved (as Higher Ceiling), +/-30%"] = solve(0.30, teamv)
    alloc = pd.DataFrame({"country": team["country"], ref_col: orig})
    for k, x in scen.items():
        alloc[k] = (orig + x).round(2)
    alloc.to_csv(HERE / f"allocations_{YEAR}_opt.csv")

    # full runs with draws: Original vs each optimum (paired draws)
    def full(xmap):
        sc = rr.build(ci, YEAR, {**orig.to_dict(), **{i: amount(i, xmap.get(i, 0.0)) for i in isos}})
        out = {"deaths": 0.0, "draws": 0.0, "after": 0.0, "hiv_inf": 0.0, "hiv_deaths": 0.0, "aid_lost": 0.0}
        units = {s: 0.0 for s in list(rr.SERVICES) + list(rr.EXTRA)}
        per = {}
        for i in isos:
            r0 = hm.run_country(i, sc, rr.FISCAL, I, P, n_draws=0, keep_draws=True, mortality_trend=rr.TREND)
            rd = hm.run_country(i, sc, rr.FISCAL, I, P, n_draws=a.draws, mortality_trend=rr.TREND)
            Bk = r0["buckets"].set_index("bucket")
            out["deaths"] += float(r0["totals"]["deaths_5y"])
            out["draws"] = out["draws"] + np.asarray(rd["draw_totals"]["deaths_5y"], float)
            out["after"] += float(r0["committed"]["after_2030"])
            out["hiv_inf"] += float(Bk.loc["HIV", "infections_5y"])
            out["hiv_deaths"] += float(Bk.loc["HIV", "deaths_5y"])
            out["aid_lost"] += float(r0["years"].set_index("year").loc[YEAR, "aid_lost_usd"])
            L = r0["lines"].set_index("line")
            pi = {"deaths": float(r0["totals"]["deaths_5y"]), "art_need": float(L.loc["hiv_art", "need"]),
                  "art_cov0": float(L.loc["hiv_art", "cov0"])}
            for s, ls in {**rr.SERVICES, **rr.EXTRA}.items():
                u = float(sum(r0["draws"]["units"][l][0, T] for l in ls))
                units[s] += u
                pi[s] = u
            per[i] = pi
        out["units"] = units
        out["per"] = per
        return out

    base = full({})
    res = {k: full(x.to_dict()) for k, x in scen.items()}

    md = [f"# Best reallocation of the {YEAR} US MOU money for deaths, 15 countries (no model changes)", "",
          "Generated by `audit/reallocation/run_optimal_realloc_2027.py`. Dollar for dollar: US$1 of MOU moved = US$1 of US "
          "direct aid in the country, spent the way that country's US direct aid is spent, run through the model itself "
          "(America First MOUs, US bilateral schedule only, dashboard defaults; deaths ranges from 400 paired draws).", "",
          "**Bounds.** Total unchanged; a receiving country can at most get back its 2021-23 US direct aid (0% cut in 2027: "
          "the model has no coverage above baseline, so it is not extrapolated); a giving country can at most give the US "
          "aid it still has; each country within +/-10%, 20% or 30% of its signed 2027 amount; one version also limits the "
          f"total moved to the team's Higher Ceiling (US${teamv / 1e6:,.1f}M).", "",
          "**Method.** Each country's deaths 2026-2030 were computed with the model on a US$1M grid of aid changes. Starting from "
          "the Original MOU, US$1M was moved at a time between whichever two countries lowered total deaths the most, in "
          "either direction, until no move helped. The model's curves are not straight lines (restoring ART money brings "
          "back people cut in 2026; deeper cuts cost fewer deaths per dollar), so this is the best allocation found, not a "
          "proven global optimum. Amounts are in whole US$M.", "",
          "## 1. Results vs the Original MOU", "",
          "Positive = better than the Original MOU.", ""]
    trs = []
    for k, r in res.items():
        dd = base["draws"] - r["draws"]
        trs.append([k, f"{scen[k].clip(lower=0).sum() / 1e6:,.1f}", sfmt(base["deaths"] - r["deaths"]),
                    f"{sfmt(np.percentile(dd, 2.5))} to {sfmt(np.percentile(dd, 97.5))}",
                    sfmt(base["after"] - r["after"]), sfmt(base["hiv_deaths"] - r["hiv_deaths"]),
                    sfmt(base["hiv_inf"] - r["hiv_inf"]),
                    sfmt(sum(base["units"][s] - r["units"][s] for s in SIX)), sfmt(base["units"]["ART"] - r["units"]["ART"]),
                    f"{(base['aid_lost'] - r['aid_lost']) / 1e6:+,.2f}"])
    md += [md_table(["Scenario", "Moved US$M", "Deaths averted 2026-30", "Range (paired)", "Deaths averted 2031-35",
                     "HIV deaths averted", "HIV infections averted", "People keeping a service 2027 (six services)",
                     "ART patients 2027", "Check: aid change US$M (should be 0)"], trs), "",
           f"Original MOU: {fmt(base['deaths'])} deaths 2026-2030, {fmt(sum(base['units'][s] for s in SIX))} people losing a "
           f"service in {YEAR}, {fmt(base['units']['ART'])} losing ART.", ""]

    md += ["## 2. The allocations (2027 MOU amounts, US$M; change vs Original in brackets)", ""]
    trs = []
    for i in isos:
        trs.append([names[i], f"{orig[i] / 1e6:,.1f}"] + [f"{(orig[i] + scen[k][i]) / 1e6:,.1f} ({scen[k][i] / 1e6:+,.1f})"
                                                          if abs(scen[k][i]) > 1 else f"{orig[i] / 1e6:,.1f}" for k in scen]
                   + [f"{lost0[i] / 1e6:,.1f}", f"{(curves[i][0.0] - curves[i][min(curves[i], key=lambda v: abs(v - 1e6))]):.0f}"])
    md += [md_table(["Country", ref_col] + list(scen) + ["Room to 0% cut US$M", "Deaths averted by first +US$1M"], trs), ""]

    md += ["## 3. Coverage by country in the widest version (+/-30%)", ""]
    k30 = f"Best within +/-{0.30:.0%}"
    trs = []
    for i in isos:
        x = scen[k30][i]
        if abs(x) < 1:
            continue
        b, r = base["per"][i], res[k30]["per"][i]
        cov = lambda u: (b["art_cov0"] - u / b["art_need"]) * 100
        trs.append([names[i], f"{x / 1e6:+,.1f}", sfmt(b["deaths"] - r["deaths"]), sfmt(b["ART"] - r["ART"]),
                    f"{b['art_cov0'] * 100:.1f}% / {cov(b['ART']):.1f}% → {cov(r['ART']):.1f}%",
                    sfmt(sum(b[s] - r[s] for s in SIX)), sfmt(b["Bednets"] - r["Bednets"])])
    md += [md_table(["Country", "Δ US$M", "Deaths averted 2026-30", "Δ ART patients", "ART coverage: baseline / Original → new",
                     "Δ people on six services", "Δ bednet users"], trs), ""]
    (HERE / f"RESULTS_optimal_{YEAR}.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
