"""
2027 MOU reallocation, dollar for dollar (audit/reallocation). Same allocations as run_reallocation_2027.py, but the
change in each country's 2027 MOU amount is taken at face value as a change in US direct aid (US$1 of MOU = US$1 of
aid), with no cut fraction, no `mou_us_ref` leverage and no clip at a 0% cut. Money above the Original MOU's level is
a gain: it first restores the services the Original MOU cut, then raises coverage above the 2021-23 baseline.

How the dollars become coverage: the model's own conversion per country, from the marginal run in
marginal_<year><tag>.csv (people kept on each service and deaths averted per US$1M of MOU money, divided by the
modelled aid that US$1M moves, so per US$1M of aid). The ±US$1M marginals agree within 2% for 14 of 15 countries, so the
conversion is close to linear; beyond the Original MOU's level it is extrapolated at the same rate (each extra dollar
buys the same mix of services at the same unit costs), with coverage capped at 100% of need. Deaths are the same linear
approximation and are secondary.

    .venv/bin/python audit/reallocation/run_dollar_realloc_2027.py [--alloc allocations_2027_v2.csv] [--tag _v2]

Outputs: RESULTS_dollar_2027<tag>.md, dollar_2027<tag>.csv. Read-only with respect to the model.
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
sys.path.insert(0, str(HERE))
logging.disable(logging.WARNING)
import health_model as hm  # noqa: E402
import run_reallocation_2027 as rr  # noqa: E402

YEAR = 2027
T = rr.YEARS.index(YEAR)
SERV = {"ART": ["hiv_art"], "PMTCT": ["hiv_pmtct"], "TB treatment": ["tb_ds", "tb_dr"], "Bednets": ["mal_itn"],
        "Spraying": ["mal_irs"], "Malaria treatment": ["mal_cm"], "Vaccines": ["imm"]}
SIX = ["ART", "TB treatment", "Bednets", "Spraying", "Malaria treatment", "Vaccines"]
fmt, sfmt, md_table = rr.fmt, rr.sfmt, rr.md_table


def pp(x):
    return "n/a" if x is None or np.isnan(x) else f"{x:+.2f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--alloc", default=str(HERE / "allocations_2027_v2.csv"))
    ap.add_argument("--tag", default="_v2")
    a = ap.parse_args()
    alloc = pd.read_csv(a.alloc).set_index("iso3")
    cols = [c for c in alloc.columns if c != "country"]
    ref, scen = cols[0], cols[1:]
    names = alloc["country"].to_dict()
    isos = list(alloc.index)
    M = pd.read_csv(HERE / f"marginal_{YEAR}{a.tag}.csv").set_index("iso3")

    # Original MOU, central run: units lost in YEAR, need and baseline coverage by service; deaths
    I, P = hm.load_inputs(), hm.load_params()
    rr.BILATERAL_ONLY = True
    sc = rr.build(I["ci"], YEAR, {i: float(alloc.loc[i, ref]) for i in isos})
    base = {}
    for i in isos:
        r0 = hm.run_country(i, sc, rr.FISCAL, I, P, n_draws=0, keep_draws=True, mortality_trend=rr.TREND)
        L, U = r0["lines"].set_index("line"), r0["draws"]["units"]
        b = {"deaths_5y": float(r0["totals"]["deaths_5y"])}
        for s, ls in SERV.items():
            need = float(np.nansum([L.loc[l, "need"] for l in ls]))
            covered = float(np.nansum([L.loc[l, "need"] * L.loc[l, "cov0"] for l in ls]))
            b[f"{s}_need"], b[f"{s}_cov0"] = need, covered / need if need > 0 else np.nan
            b[f"{s}_lost0"] = float(sum(U[l][0, T] for l in ls))
        base[i] = b

    rows = []
    for i in isos:
        aid_per_1M_mou = float(M.loc[i, "modelled_aid_per_1M"])          # US$ of aid moved by US$1M of MOU money
        f = 1e6 / aid_per_1M_mou                                         # -> per US$1M of aid
        for c in scen:
            d_usd = float(alloc.loc[i, c] - alloc.loc[i, ref])
            r = {"scenario": c, "iso3": i, "country": names[i], "orig_usd": float(alloc.loc[i, ref]),
                 "new_usd": float(alloc.loc[i, c]), "d_usd": d_usd}
            for s in SERV:
                per_1M = float(M.loc[i, f"kept_{s}_per_1M"]) * f
                need, cov0, lost0 = base[i][f"{s}_need"], base[i][f"{s}_cov0"], base[i][f"{s}_lost0"]
                kept = d_usd / 1e6 * per_1M
                lost1 = lost0 - kept
                r[f"{s}_capped"] = False
                floor = -(1 - min(cov0, 1.0)) * need if need > 0 else -np.inf   # coverage cannot pass 100% of need
                if kept > 0 and lost1 < floor:
                    lost1, r[f"{s}_capped"] = min(lost0, floor), True
                    kept = lost0 - lost1
                r[f"{s}_kept"] = kept
                r[f"{s}_lost0"], r[f"{s}_lost1"] = lost0, lost1
                r[f"{s}_need"], r[f"{s}_cov0"] = need, cov0
                r[f"{s}_cov_orig"] = (cov0 - lost0 / need) * 100 if need > 0 else np.nan
                r[f"{s}_cov_new"] = (cov0 - lost1 / need) * 100 if need > 0 else np.nan
                r[f"{s}_dpp"] = kept / need * 100 if need > 0 else np.nan
                r[f"{s}_above_base_pp"] = -lost1 / need * 100 if need > 0 and lost1 < 0 else 0.0
            r["six_kept"] = sum(r[f"{s}_kept"] for s in SIX)
            r["deaths_averted_5y"] = d_usd / 1e6 * float(M.loc[i, "deaths_averted_5y_per_1M"]) * f
            r["infections_averted_5y"] = d_usd / 1e6 * float(M.loc[i, "infections_averted_5y_per_1M"]) * f
            rows.append(r)
    R = pd.DataFrame(rows)
    R.to_csv(HERE / f"dollar_{YEAR}{a.tag}.csv", index=False)

    md = [f"# {YEAR} MOU reallocation, dollar for dollar: coverage, 15 countries (no model changes)", "",
          f"Generated by `audit/reallocation/run_dollar_realloc_2027.py` from `{Path(a.alloc).name}`. Each country's change "
          f"in its {YEAR} MOU amount is taken at face value as a change in US direct aid (US$1 of MOU = US$1 of aid): no cut "
          "fraction, no `mou_us_ref` leverage, no 0% floor. Money above the Original MOU amount first restores the services "
          "the Original MOU cut and then raises coverage above the 2021-23 baseline. Dollars become people on each service "
          "through the model's own conversion for each country (people kept and deaths averted per US$1M of aid, from the "
          f"marginal run in `marginal_{YEAR}{a.tag}.csv`), extrapolated at the same rate beyond the Original MOU's level "
          "and capped at 100% of need. Same model run as the main report: America First MOUs, US bilateral schedule only, "
          "dashboard defaults, central parameters.", "",
          "## 1. Money", ""]
    tot = {c: alloc[c].sum() for c in cols}
    md += [md_table(["Scenario", f"{YEAR} MOU total (US$)", "Change vs Original (US$)", "Moved between countries (US$M)"],
                    [[c, fmt(tot[c], 2), sfmt(tot[c] - tot[ref], 2),
                      f"{(alloc[c] - alloc[ref]).clip(lower=0).sum() / 1e6:,.2f}" if c != ref else "0.00"] for c in cols]),
           "", "Aid is therefore unchanged in total in every ceiling: what one country gains another loses, dollar for dollar.", ""]

    md += ["## 2. Totals: change in people on each service in 2027 vs the Original MOU", "",
           "Positive = more people keep (or gain) the service. Coverage change is people / people in need across the 15 "
           "countries, in percentage points.", ""]
    hdr = ["Service", "Original MOU: people losing it in 2027"] + sum([[f"{c} Δ people", f"{c} Δ pp"] for c in scen], [])
    trs = []
    for s in SERV:
        need = sum(base[i][f"{s}_need"] for i in isos)
        line = [s, fmt(sum(base[i][f"{s}_lost0"] for i in isos))]
        for c in scen:
            k = R[R.scenario == c][f"{s}_kept"].sum()
            line += [sfmt(k), pp(k / need * 100 if need else np.nan)]
        trs.append(line)
    line = ["All six services", fmt(sum(base[i][f"{s}_lost0"] for i in isos for s in SIX))]
    for c in scen:
        line += [sfmt(R[R.scenario == c]["six_kept"].sum()), ""]
    trs.append(line)
    md += [md_table(hdr, trs), ""]
    md += [md_table(["Scenario", "Deaths averted 2026-30 (linear approximation)", "HIV infections averted 2026-30"],
                    [[c, sfmt(R[R.scenario == c].deaths_averted_5y.sum()), sfmt(R[R.scenario == c].infections_averted_5y.sum())]
                     for c in scen]), "",
           "Deaths are secondary here: they apply each country's deaths-averted-per-dollar at the Original MOU's level to the "
           "whole change, including money above the baseline.", ""]

    md += ["## 3. By country", ""]
    for c in scen:
        S = R[R.scenario == c].set_index("iso3")
        trs = []
        for i in isos:
            r = S.loc[i]
            if abs(r.d_usd) < 1:
                continue
            trs.append([names[i], f"{r.d_usd / 1e6:+,.2f}", sfmt(r.six_kept), sfmt(r["ART_kept"]),
                        f"{r['ART_cov_orig']:.1f}% → {r['ART_cov_new']:.1f}%" if not np.isnan(r["ART_cov_orig"]) else "n/a",
                        sfmt(r["Bednets_kept"]),
                        f"{r['Bednets_cov_orig']:.1f}% → {r['Bednets_cov_new']:.1f}%" if not np.isnan(r["Bednets_cov_orig"]) else "n/a",
                        sfmt(r["TB treatment_kept"]), sfmt(r.deaths_averted_5y)])
        md += [f"**{c}** (countries whose amount changes)", "",
               md_table(["Country", "Δ US$M", "Δ people on the six services", "Δ ART patients",
                         "ART coverage 2027: Original → new", "Δ bednet users", "Bednet use 2027: Original → new",
                         "Δ TB courses", "Deaths averted 2026-30 (approx.)"], trs), ""]

    md += ["## 4. Coverage above the 2021-23 baseline", "",
           "Countries whose new amount more than restores what the Original MOU cut: coverage in 2027 ends above its "
           "2021-23 level (percentage points above baseline, by service).", ""]
    trs = []
    for c in scen:
        S = R[R.scenario == c]
        for _, r in S.iterrows():
            above = {s: r[f"{s}_above_base_pp"] for s in SERV if r[f"{s}_above_base_pp"] > 0.005}
            if above:
                trs.append([c, r.country, f"{r.d_usd / 1e6:+,.2f}"] +
                           [f"{r[f'{s}_cov0'] * 100:.1f}% → {r[f'{s}_cov_new']:.1f}%" if s in above else "" for s in SERV])
    md += [md_table(["Scenario", "Country", "Δ US$M"] + [f"{s} (baseline → new)" for s in SERV], trs) if trs else "None.", ""]
    capped = [f"{r.scenario} {r.country} {s}" for _, r in R.iterrows() for s in SERV if r[f"{s}_capped"]]
    md += [f"Services where the gain is limited by 100% of need: {', '.join(capped) or 'none'}.", ""]

    md += ["## 5. Conversion used (per US$1M of aid, Original MOU level)", "",
           md_table(["Country", "ART", "PMTCT", "TB courses", "Bednets", "Spraying", "Malaria Rx", "Vaccines",
                     "Deaths averted 2026-30"],
                    [[names[i]] + [fmt(float(M.loc[i, f"kept_{s}_per_1M"]) * 1e6 / float(M.loc[i, "modelled_aid_per_1M"]))
                                   for s in SERV]
                     + [f"{float(M.loc[i, 'deaths_averted_5y_per_1M']) * 1e6 / float(M.loc[i, 'modelled_aid_per_1M']):.1f}"]
                     for i in isos]), "",
           "Not every aid dollar reaches one of these services: part goes to HIV testing and care, programme management, "
           "systems and other lines the model counts as money lost but not as people (shares in the main report, table 5b).", ""]
    (HERE / f"RESULTS_dollar_{YEAR}{a.tag}.md").write_text("\n".join(md) + "\n")
    print("\n".join(md[:60]))


if __name__ == "__main__":
    main()
