"""
Batch 2, Step 1C-D: concept-matched transmission rates from UNAIDS 2025 and a projection of the Full US Exit scenario
under the proposed values (no model code is changed: the model is imported and its constants and parameter table are
overridden for the run).

    .venv/bin/python audit/batch2_projection.py

Variants (all central run, no government response, sudden cut, all countries):
  0 current            : the model as committed
  1 hazard+reengage    : ART_HAZARD -> cohort-calculation values (audit/batch2_cohort.py), art_reengage 0.5 -> 0.35
  2 + transmission     : art_transmission 0.04 -> the country's UNAIDS 2025 new infections / people with
                         unsuppressed viral load (regional median where missing), first generation only
  3 + second generation: people newly infected by those who stopped ART are themselves unsuppressed (mean D years
                         to suppression) and transmit at the same rate (one further generation)
Writes audit/logic_review/batch2_projection.csv (by country and variant) and batch2_transmission.csv (the rates).
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

OUT = ROOT / "audit" / "logic_review"
UNAIDS = ROOT / "datasets" / "UNAIDS_2026" / "UNAIDS_Estimates_2026.csv"

NEW_HAZARD = np.array([0.013, 0.025, 0.037, 0.049, 0.060])   # excess deaths per person-year, years 1-5 off ART
NEW_REENGAGE = (0.35, 0.17, 0.68)                             # central, low, high
D_UNSUPPRESSED = 4.0                                          # mean years a newly infected person stays unsuppressed
FOCUS = ["KEN", "NGA", "MOZ", "ZAF", "UGA"]

# Optima (ten Brink et al. 2025, appendix Table C2): cumulative 2025-2030, scenario 1 (status quo), 4 (PEPFAR
# discontinued + mitigation), 5 (PEPFAR discontinued, no mitigation): (inf1, inf4, inf5, d1, d4, d5)
OPTIMA_C2 = {
    "AZE": (1880, 2960, 2960, 1190, 1510, 1510), "KHM": (8400, 18260, 23390, 2570, 3510, 5500),
    "CIV": (50630, 65300, 117910, 47190, 56100, 92500), "DOM": (13270, 27920, 36200, 5380, 7150, 11040),
    "SWZ": (14070, 43890, 133500, 4030, 6520, 19660), "KEN": (162990, 199460, 350880, 70790, 78640, 146740),
    "KGZ": (1840, 4000, 4890, 990, 1220, 1610), "MWI": (56210, 143420, 476750, 19880, 35290, 147540),
    "MDA": (2490, 3430, 3430, 1960, 2520, 2520), "MNG": (290, 340, 340, 140, 150, 150),
    "MOZ": (411590, 614180, 1359390, 140710, 183070, 405710),
    "ZAF": (671620, 2372810, 3062640, 251450, 534400, 743200), "TJK": (1910, 2320, 2320, 1250, 1380, 1380),
    "UGA": (246980, 339330, 828160, 110270, 133090, 310850), "ZWE": (33730, 101700, 358000, 20420, 37230, 153680),
}


def transmission_rates(ci: pd.DataFrame) -> pd.DataFrame:
    """UNAIDS 2025: new HIV infections (all ages) / (people living with HIV - people with suppressed viral load),
    unrounded Data value, Area Level 2. Fallback: median of the model's countries in the same WHO region, else the
    overall median."""
    df = pd.read_csv(UNAIDS, low_memory=False)
    c = df[(df["Area Level"] == 2) & (df["Time Period"] == 2025)]

    def get(ind, sub):
        s = c[(c.Indicator == ind) & (c.Subgroup == sub)].set_index("Area ID")["Data value"]
        return pd.to_numeric(s, errors="coerce")

    t = pd.DataFrame({"inf": get("New HIV Infections", "All ages estimate"),
                      "inf_lo": get("New HIV Infections", "All ages lower estimate"),
                      "inf_hi": get("New HIV Infections", "All ages upper estimate"),
                      "plhiv": get("People living with HIV", "All ages estimate"),
                      "sup": get("People living with HIV who have suppressed viral loads", "All ages")})
    t = t.reindex(ci.index)
    t["unsup"] = t.plhiv - t.sup
    t["ratio"] = t.inf / t.unsup
    t["ratio_lo"], t["ratio_hi"] = t.inf_lo / t.unsup, t.inf_hi / t.unsup
    t["who_region"] = ci["who_region"]
    overall = t.ratio.median()
    reg = t.groupby("who_region").ratio.median()
    t["source"] = np.where(t.ratio.notna(), "country", "fallback")
    t["rate"] = t.ratio
    for iso in t.index[t.ratio.isna()]:
        r = reg.get(t.loc[iso, "who_region"], np.nan)
        t.loc[iso, "rate"] = overall if np.isnan(r) else r
    t["rate_lo"] = np.where(t.ratio.notna(), t.ratio_lo, t.rate * (t.ratio_lo / t.ratio).median())
    t["rate_hi"] = np.where(t.ratio.notna(), t.ratio_hi, t.rate * (t.ratio_hi / t.ratio).median())
    return t


def second_generation_weights(H: int, D: float) -> np.ndarray:
    """w[k] = expected unsuppressed person-years in year s + k from one infection in mid-year s, with exponential
    time to suppression of mean D years."""
    w = np.zeros(H)
    f = lambda u: D * (1 - np.exp(-u / D))          # integral of exp(-u/D) from 0 to u
    w[0] = f(0.5)
    for k in range(1, H):
        w[k] = f(k + 0.5) - f(k - 0.5)
    return w


def patched_art_cohorts(orig, D):
    """Wrap health_model.art_cohorts: add the infections caused by the people the ART-stoppers infected (one further
    generation), within 2026-2035."""
    H = hm.N_YEARS + hm.POST_YEARS
    w = second_generation_weights(H, D)

    def inner(stock, hazard_by_age, transmission, reengage):
        d, inf, post_d, post_i, off = orig(stock, hazard_by_age, transmission, reengage)
        first = np.hstack([inf, post_i])                 # n x 10 first-generation infections
        second = np.zeros_like(first)
        for s in range(H):
            for t in range(s, H):
                second[:, t] += first[:, s] * w[t - s] * transmission
        return d, inf + second[:, :hm.N_YEARS], post_d, post_i + second[:, hm.N_YEARS:], off
    return inner


def main():
    I, P = hm.load_inputs(), hm.load_params()
    ci = I["ci"]
    countries = [c for c in ci.index if c in set(I["lines"].iso3)]
    rates = transmission_rates(ci)
    rates.to_csv(OUT / "batch2_transmission.csv")
    print("Transmission rates (new infections per person with unsuppressed viral load per year), model countries:")
    print(rates.ratio.describe().round(3).to_string())
    print("regional medians:", rates.groupby("who_region").ratio.median().round(3).to_dict())
    print("fallback countries:", rates.index[rates.source == "fallback"].tolist())

    sc = scn.build_scenario("Full US exit", scn.default_opts("Full US exit", ci), ci)
    fiscal = hm.Fiscal(*scn.DEFAULT_FISCAL)
    orig_hazard, orig_cohorts = hm.ART_HAZARD.copy(), hm.art_cohorts
    rows = []
    variants = ["0 current", "1 hazard+reengage", "2 + transmission", "3 + second generation"]
    for v in variants:
        hm.ART_HAZARD = orig_hazard if v.startswith("0") else NEW_HAZARD
        hm.art_cohorts = patched_art_cohorts(orig_cohorts, D_UNSUPPRESSED) if v.startswith("3") else orig_cohorts
        for iso in countries:
            pt = P.copy()
            if not v.startswith("0"):
                pt.loc["art_reengage", ["central", "low", "high"]] = NEW_REENGAGE
            if v.startswith(("2", "3")):
                r = rates.loc[iso]
                pt.loc["art_transmission", ["central", "low", "high"]] = (r.rate, r.rate_lo, r.rate_hi)
            res = hm.run_country(iso, sc, fiscal, I, pt, n_draws=0)
            B = res["buckets"].set_index("bucket")
            L = res["lines"].set_index("line")
            rows.append({"variant": v, "iso3": iso,
                         "deaths_5y": res["totals"]["deaths_5y"],
                         "hiv_deaths_5y": B.loc["HIV", "deaths_5y"],
                         "art_deaths_5y": L.loc["hiv_art", "deaths_5y"],
                         "hiv_infections_5y": B.loc["HIV", "infections_5y"],
                         "art_infections_5y": L.loc["hiv_art", "infections_5y"],
                         "people_stop_art": L.loc["hiv_art", "units_lost"],
                         "after_2030": res["committed"]["after_2030"],
                         "after_2030_hiv_art": res["committed"]["after_parts"].get("hiv_art", 0.0),
                         "after_2030_hiv_inf": res["committed"]["after_parts"].get("hiv_infections", 0.0)})
    hm.ART_HAZARD, hm.art_cohorts = orig_hazard, orig_cohorts
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "batch2_projection.csv", index=False)
    pd.set_option("display.width", 250)
    cols = ["deaths_5y", "hiv_deaths_5y", "art_deaths_5y", "hiv_infections_5y", "art_infections_5y", "after_2030",
            "after_2030_hiv_art", "after_2030_hiv_inf"]
    print("\nAll countries, Full US Exit, central:")
    print(df.groupby("variant")[cols].sum().round(0).to_string())
    for iso in FOCUS:
        print(f"\n{iso}:")
        print(df[df.iso3 == iso].set_index("variant")[cols[:5]].round(0).to_string())
    # Optima comparison (overlapping countries, scenario 5 - scenario 1 and 4 - 1)
    ov = [c for c in OPTIMA_C2 if c in countries]
    print("\nOptima Table C2 overlap (2025-2030, PEPFAR discontinued) vs model (2026-2030, Full US Exit):")
    rec = []
    for iso in ov:
        i1, i4, i5, d1, d4, d5 = OPTIMA_C2[iso]
        m0 = df[(df.variant == variants[0]) & (df.iso3 == iso)].iloc[0]
        m3 = df[(df.variant == variants[3]) & (df.iso3 == iso)].iloc[0]
        rec.append({"iso3": iso, "optima_deaths_s4": d4 - d1, "optima_deaths_s5": d5 - d1,
                    "model_hiv_deaths_now": m0.hiv_deaths_5y, "model_hiv_deaths_proposed": m3.hiv_deaths_5y,
                    "optima_inf_s4": i4 - i1, "optima_inf_s5": i5 - i1,
                    "model_inf_now": m0.hiv_infections_5y, "model_inf_proposed": m3.hiv_infections_5y})
    o = pd.DataFrame(rec).set_index("iso3")
    o.loc["TOTAL"] = o.sum()
    print(o.round(0).to_string())
    o.to_csv(OUT / "batch2_optima_compare.csv")


if __name__ == "__main__":
    main()
