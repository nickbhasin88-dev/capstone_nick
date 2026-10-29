"""
HIV transmission rate per person with unsuppressed viral load, by country (logic review L-41, Batch 2).

    python hiv_transmission_inputs.py        # patch model_data/country_inputs.csv in place (needs the UNAIDS file)

Rate = new HIV infections (all ages) / (people living with HIV - people living with HIV who have suppressed viral
loads), both for the latest year with all three values (2025 in the 2026 estimates), from UNAIDS AIDSinfo
(`datasets/UNAIDS_2026/UNAIDS_Estimates_2026.csv`, unrounded `Data value`, Area Level 2 = countries). A person who
stops ART becomes a person with unsuppressed viral load, so this is the concept-matched transmission rate for the
model's ART cohorts (replaces the single value art_transmission = 0.04, kept as the legacy value).
Low / high = the UNAIDS lower / upper infection estimates over the same denominator.
Countries without the suppression indicator get the median of the dashboard countries in their WHO region (the
overall median if the region has none), flagged `art_transmission_source = regional median (<region>)`.
Called by prepare_model.py (full rebuild) and runnable on its own to patch an existing country_inputs.csv.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
UNAIDS_FILE = ROOT / "datasets" / "UNAIDS_2026" / "UNAIDS_Estimates_2026.csv"
MODEL_DIR = ROOT / "model_data"
COLS = ["art_transmission_rate", "art_transmission_rate_lo", "art_transmission_rate_hi", "art_transmission_year",
        "art_transmission_source"]


def unaids_rates(path: Path = UNAIDS_FILE) -> pd.DataFrame:
    """One row per ISO3 with the country's rate, bounds and year (latest year with all three indicators)."""
    df = pd.read_csv(path, low_memory=False, usecols=["Indicator", "Subgroup", "Area ID", "Area Level",
                                                      "Time Period", "Data value"])
    c = df[df["Area Level"] == 2].copy()
    c["Data value"] = pd.to_numeric(c["Data value"], errors="coerce")
    want = {("New HIV Infections", "All ages estimate"): "inf",
            ("New HIV Infections", "All ages lower estimate"): "inf_lo",
            ("New HIV Infections", "All ages upper estimate"): "inf_hi",
            ("People living with HIV", "All ages estimate"): "plhiv",
            ("People living with HIV who have suppressed viral loads", "All ages"): "sup"}
    parts = []
    for (ind, sub), name in want.items():
        s = c[(c.Indicator == ind) & (c.Subgroup == sub)][["Area ID", "Time Period", "Data value"]]
        parts.append(s.rename(columns={"Area ID": "iso3", "Time Period": "year", "Data value": name}))
    t = parts[0]
    for p in parts[1:]:
        t = t.merge(p, on=["iso3", "year"], how="outer")
    t = t.dropna(subset=["inf", "plhiv", "sup"])
    t = t[t.plhiv > t.sup]
    t = t.sort_values("year").groupby("iso3").tail(1).set_index("iso3")
    t["unsup"] = t.plhiv - t.sup
    t["rate"] = t.inf / t.unsup
    t["rate_lo"], t["rate_hi"] = t.inf_lo / t.unsup, t.inf_hi / t.unsup
    return t[["year", "inf", "plhiv", "sup", "unsup", "rate", "rate_lo", "rate_hi"]]


def apply(ci: pd.DataFrame, path: Path = UNAIDS_FILE) -> pd.DataFrame:
    """Add the art_transmission_* columns to a country table indexed by iso3 (needs `who_region`)."""
    t = unaids_rates(path).reindex(ci.index)
    ci = ci.copy()
    ci["art_transmission_rate"], ci["art_transmission_rate_lo"], ci["art_transmission_rate_hi"] = t.rate, t.rate_lo, t.rate_hi
    ci["art_transmission_year"] = t.year
    ci["art_transmission_source"] = np.where(t.rate.notna(), "UNAIDS 2026 estimates: new infections / (PLHIV - suppressed)", "")
    have = ci.art_transmission_rate.notna()
    overall = float(ci.loc[have, "art_transmission_rate"].median())
    lo_f = float((ci.loc[have, "art_transmission_rate_lo"] / ci.loc[have, "art_transmission_rate"]).median())
    hi_f = float((ci.loc[have, "art_transmission_rate_hi"] / ci.loc[have, "art_transmission_rate"]).median())
    reg = ci.loc[have].groupby("who_region")["art_transmission_rate"].median() if "who_region" in ci else pd.Series(dtype=float)
    for iso in ci.index[~have]:
        region = ci.loc[iso, "who_region"] if "who_region" in ci else None
        r = reg.get(region, np.nan) if region is not None else np.nan
        if np.isnan(r):
            r, label = overall, "median of dashboard countries"
        else:
            label = f"regional median ({region})"
        ci.loc[iso, "art_transmission_rate"] = r
        ci.loc[iso, "art_transmission_rate_lo"], ci.loc[iso, "art_transmission_rate_hi"] = r * lo_f, r * hi_f
        ci.loc[iso, "art_transmission_year"] = float(t.year.max())
        ci.loc[iso, "art_transmission_source"] = label
    return ci


def main():
    if not UNAIDS_FILE.exists():
        raise SystemExit(f"missing {UNAIDS_FILE}")
    p = MODEL_DIR / "country_inputs.csv"
    ci = pd.read_csv(p).set_index("iso3")
    new = apply(ci)
    n_c = (new.art_transmission_source.str.startswith("UNAIDS")).sum()
    print(f"art_transmission_rate: UNAIDS value for {n_c} of {len(new)} countries, fallback for {len(new) - n_c}; "
          f"median {new.art_transmission_rate.median():.3f}")
    new.reset_index().to_csv(p, index=False)


if __name__ == "__main__":
    main()
