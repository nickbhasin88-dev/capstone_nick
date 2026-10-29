"""
2027 MOU reallocation, dollar for dollar, HIV money only (audit/reallocation). Same allocations and method as
run_dollar_realloc_2027.py (US$1 of MOU = US$1 of aid, no cut fraction, no leverage, no 0% floor; money above the
Original MOU's level raises coverage above the 2021-23 baseline, capped at 100% of need), but every dollar moved is
treated as HIV money: it buys only the HIV services the country's US HIV aid buys (ART, PMTCT, HIV prevention, testing
and care, OVC), in the same proportions, at the same unit costs.

Conversion per US$1M of HIV aid = the model's marginal per US$1M of MOU money (marginal_<year><tag>.csv) / the aid that
US$1M moves / the HIV share of the country's US direct aid. This holds because the model's cut is uniform across the
country's US direct rows, so the HIV part of a marginal dollar is the HIV share. HIV deaths and infections are the same
linear approximation (central parameters, no ranges).

    .venv/bin/python audit/reallocation/run_dollar_hiv_2027.py [--alloc allocations_2027_v2.csv] [--tag _v2]

Outputs: RESULTS_dollar_hiv_2027<tag>.md, dollar_hiv_2027<tag>.csv. Read-only with respect to the model.
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
SERV = {"ART": "hiv_art", "PMTCT": "hiv_pmtct"}
MONEY = {"ART": "hiv_art", "Testing & care": "hiv_care_ct", "Prevention": "hiv_prev", "PMTCT": "hiv_pmtct", "OVC": "hiv_ovc"}
fmt, sfmt, md_table = rr.fmt, rr.sfmt, rr.md_table


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

    # per US$1M of HIV aid
    k = 1e6 / M["modelled_aid_per_1M"] / M["us_direct_share_HIV"]
    conv = pd.DataFrame({"ART": M["kept_ART_per_1M"] * k, "PMTCT": M["kept_PMTCT_per_1M"] * k,
                         "infections": M["infections_averted_5y_per_1M"] * k, "hiv_deaths": M["deaths_averted_HIV_per_1M"] * k,
                         "hiv_deaths_after_2030": np.nan, "art_cost": M["uc_hiv_art"], "hiv_share": M["us_direct_share_HIV"]})
    for lab, l in MONEY.items():
        conv[f"money_{lab}"] = M[f"loss_{l}_per_1M"] / M["modelled_aid_per_1M"] / M["us_direct_share_HIV"]   # share of the HIV dollar

    # Original MOU, central run: ART and PMTCT need, baseline coverage, units lost in YEAR; HIV deaths and infections
    I, P = hm.load_inputs(), hm.load_params()
    rr.BILATERAL_ONLY = True
    sc = rr.build(I["ci"], YEAR, {i: float(alloc.loc[i, ref]) for i in isos})
    base = {}
    for i in isos:
        r0 = hm.run_country(i, sc, rr.FISCAL, I, P, n_draws=0, keep_draws=True, mortality_trend=rr.TREND)
        L, U, B = r0["lines"].set_index("line"), r0["draws"]["units"], r0["buckets"].set_index("bucket")
        b = {"hiv_deaths_5y": float(B.loc["HIV", "deaths_5y"]), "infections_5y": float(B.loc["HIV", "infections_5y"])}
        for s, l in SERV.items():
            b[f"{s}_need"], b[f"{s}_cov0"], b[f"{s}_lost0"] = float(L.loc[l, "need"]), float(L.loc[l, "cov0"]), float(U[l][0, T])
        base[i] = b

    rows = []
    for i in isos:
        for c in scen:
            d = float(alloc.loc[i, c] - alloc.loc[i, ref])
            r = {"scenario": c, "iso3": i, "country": names[i], "d_usd": d}
            for s in SERV:
                need, cov0, lost0 = base[i][f"{s}_need"], base[i][f"{s}_cov0"], base[i][f"{s}_lost0"]
                kept = d / 1e6 * float(conv.loc[i, s])
                lost1 = lost0 - kept
                floor = -(1 - min(cov0, 1.0)) * need if need > 0 else -np.inf
                r[f"{s}_capped"] = bool(kept > 0 and lost1 < floor)
                if r[f"{s}_capped"]:
                    lost1 = min(lost0, floor)
                    kept = lost0 - lost1
                r[f"{s}_kept"] = kept
                r[f"{s}_cov_base"] = cov0 * 100
                r[f"{s}_cov_orig"] = (cov0 - lost0 / need) * 100 if need > 0 else np.nan
                r[f"{s}_cov_new"] = (cov0 - lost1 / need) * 100 if need > 0 else np.nan
                r[f"{s}_need"] = need
            r["infections_averted"] = d / 1e6 * float(conv.loc[i, "infections"])
            r["hiv_deaths_averted"] = d / 1e6 * float(conv.loc[i, "hiv_deaths"])
            rows.append(r)
    R = pd.DataFrame(rows)
    R.to_csv(HERE / f"dollar_hiv_{YEAR}{a.tag}.csv", index=False)

    tot0 = {"hiv_deaths": sum(b["hiv_deaths_5y"] for b in base.values()), "inf": sum(b["infections_5y"] for b in base.values()),
            "art_need": sum(base[i]["ART_need"] for i in isos), "pmtct_need": sum(base[i]["PMTCT_need"] for i in isos)}
    md = [f"# {YEAR} MOU reallocation, dollar for dollar, HIV money only: 15 countries (no model changes)", "",
          f"Generated by `audit/reallocation/run_dollar_hiv_2027.py` from `{Path(a.alloc).name}`. Every dollar moved between "
          "countries is treated as HIV money: US$1 of MOU = US$1 of HIV aid, spent the way the country's US HIV aid is spent "
          "(ART, PMTCT, HIV prevention, testing and care, OVC) at the model's unit costs. No cut fraction, no `mou_us_ref` "
          "leverage, no 0% floor: money above the Original MOU amount restores what the Original MOU cut and then raises "
          "coverage above the 2021-23 baseline, capped at 100% of need. The 2027 total is the same in every ceiling "
          f"(US${alloc[ref].sum():,.0f}; the ceilings differ from it by at most US$0.01). Conversions come from the model's "
          f"marginal run (`marginal_{YEAR}{a.tag}.csv`) divided by the HIV share of each country's US direct aid; HIV deaths "
          "and infections are a linear approximation at central parameters.", "",
          "## 1. Totals, 15 countries: change vs the Original MOU", "",
          "Positive = better than the Original MOU (more people on the service, more infections or deaths averted).", ""]
    trs = []
    for c in scen:
        S = R[R.scenario == c]
        trs.append([c, f"{S.d_usd.clip(lower=0).sum() / 1e6:,.1f}", sfmt(S.ART_kept.sum()),
                    f"{S.ART_kept.sum() / tot0['art_need'] * 100:+.2f}", sfmt(S.PMTCT_kept.sum()),
                    f"{S.PMTCT_kept.sum() / tot0['pmtct_need'] * 100:+.2f}", sfmt(S.infections_averted.sum()),
                    sfmt(S.hiv_deaths_averted.sum())])
    md += [md_table(["Scenario", "HIV money moved (US$M)", "ART patients 2027", "ART coverage pp", "PMTCT mothers 2027",
                     "PMTCT coverage pp", "HIV infections averted 2026-30", "HIV deaths averted 2026-30"], trs), "",
           f"For scale, under the Original MOU the 15 countries have {fmt(tot0['hiv_deaths'])} HIV deaths and "
           f"{fmt(tot0['inf'])} new HIV infections over 2026-2030, and {fmt(sum(base[i]['ART_lost0'] for i in isos))} people "
           f"losing ART in {YEAR}.", ""]

    md += ["## 2. By country", ""]
    for c in scen:
        S = R[(R.scenario == c) & (R.d_usd.abs() >= 1)]
        md += [f"**{c}**", "",
               md_table(["Country", "Δ HIV US$M", "Δ ART patients", "ART coverage 2027: baseline / Original → new",
                         "Δ PMTCT mothers", "PMTCT coverage: Original → new", "HIV infections averted", "HIV deaths averted"],
                        [[r.country, f"{r.d_usd / 1e6:+,.2f}", sfmt(r.ART_kept),
                          f"{r.ART_cov_base:.1f}% / {r.ART_cov_orig:.1f}% → {r.ART_cov_new:.1f}%", sfmt(r.PMTCT_kept),
                          f"{r.PMTCT_cov_orig:.1f}% → {r.PMTCT_cov_new:.1f}%" + (" (capped)" if r.PMTCT_capped else ""),
                          sfmt(r.infections_averted), sfmt(r.hiv_deaths_averted)] for _, r in S.iterrows()]), ""]
    above = R[R.ART_cov_new > R.ART_cov_base + 0.005]
    md += ["Countries whose ART coverage in 2027 ends above its 2021-23 baseline: " +
           (", ".join(f"{r.country} ({r.scenario}: {r.ART_cov_base:.1f}% → {r.ART_cov_new:.1f}%)" for _, r in above.iterrows())
            or "none") + ".", ""]
    caps = [f"{r.scenario} {r.country} {s}" for _, r in R.iterrows() for s in SERV if r[f"{s}_capped"]]
    md += [f"Services where the gain is limited by 100% of need: {', '.join(caps) or 'none'}.", ""]

    md += ["## 3. What US$1M of HIV aid buys in each country (Original MOU level)", "",
           "ART and PMTCT: people on the service in 2027. Infections and deaths: averted over 2026-2030. Money split: share "
           "of the HIV dollar landing on each line in the model (the rest of each line is programme management and systems "
           "money the model spreads across lines).", "",
           md_table(["Country", "ART patients", "ART cost US$/patient-year", "PMTCT mothers", "HIV infections averted",
                     "HIV deaths averted"] + [f"{lab} share" for lab in MONEY] + ["HIV share of US direct aid", "Role in the ceilings"],
                    [[names[i], fmt(conv.loc[i, "ART"]), fmt(conv.loc[i, "art_cost"]), fmt(conv.loc[i, "PMTCT"]),
                      fmt(conv.loc[i, "infections"]), f"{conv.loc[i, 'hiv_deaths']:.1f}"]
                     + [f"{conv.loc[i, f'money_{lab}']:.0%}" for lab in MONEY] + [f"{conv.loc[i, 'hiv_share']:.0%}",
                        ("gives" if (alloc.loc[i, scen] < alloc.loc[i, ref] - 1).any() else
                         "receives" if (alloc.loc[i, scen] > alloc.loc[i, ref] + 1).any() else "unchanged")]
                     for i in sorted(isos, key=lambda x: -conv.loc[x, "ART"])]), "",
           "Madagascar's US aid is 3% HIV, so its HIV conversion rests on very little money and is not meaningful; it is "
           "unchanged in every ceiling.", ""]
    (HERE / f"RESULTS_dollar_hiv_{YEAR}{a.tag}.md").write_text("\n".join(md) + "\n")
    print("\n".join(md[:30]))


if __name__ == "__main__":
    main()
