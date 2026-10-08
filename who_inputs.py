"""
Current WHO / UNAIDS estimates for the model's HIV and malaria inputs, from the WHO Global Health Observatory (GHO).

Replaces values that prepare_model.py otherwise derives indirectly from the Gapminder mirror (people living with HIV
rebuilt from 2011, all-age malaria deaths = child deaths / a regional share, population at risk from a fixed share).
Each replaced column gets <column>_year and <column>_source; where WHO has no value the derived value is kept and
the source says so.

    python who_inputs.py              # patch model_data/country_inputs.csv from the cached ext_data/gho/ files
    python who_inputs.py --download   # refresh ext_data/gho/ from the GHO API first

prepare_model.py calls apply() too, so a full rebuild gives the same inputs.
"""
from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
GHO_DIR = HERE / "ext_data" / "gho"
GHO_URL = "https://ghoapi.azureedge.net/api/{}"
INPUTS_FILE = HERE / "model_data" / "country_inputs.csv"

GHO = {
    "HIV_0000000001": "people living with HIV (all ages), UNAIDS/WHO estimate",
    "HIV_ARTCOVERAGE": "ART coverage among people living with HIV (%), UNAIDS/WHO estimate",
    # named "Estimated number of pregnant women living with HIV" in the GHO catalogue, but the values are PMTCT
    # coverage in % with an uncertainty range (e.g. Kenya 2025: "91 [83 - 100]"), so it is read as coverage
    "HIV_0000000020": "PMTCT coverage: pregnant women living with HIV receiving ARVs (%), UNAIDS/WHO estimate",
    "HIV_0000000016": "pregnant women living with HIV who received ARVs for PMTCT (number)",
    "MALARIA_EST_DEATHS": "estimated malaria deaths, all ages (World Malaria Report)",
    "MALARIA_EST_CASES": "estimated malaria cases (World Malaria Report)",
    "MALARIA_EST_INCIDENCE": "estimated malaria incidence per 1,000 population at risk (World Malaria Report)",
    "MALARIA_ITN_USE": "population in malaria-endemic areas who slept under an ITN the previous night (%), modelled",
}
TREND_YEARS, TREND_CLIP = (2010, 2019), (-0.08, 0.02)    # same window and clip as prepare_model.py


def download():
    GHO_DIR.mkdir(parents=True, exist_ok=True)
    for code in GHO:
        with urllib.request.urlopen(GHO_URL.format(code), timeout=120) as r:
            v = json.load(r)["value"]
        d = pd.DataFrame(v)
        d = d[(d["SpatialDimType"] == "COUNTRY") & d["NumericValue"].notna()]
        d = d.rename(columns={"SpatialDim": "iso3", "TimeDim": "year", "NumericValue": "value", "Low": "low",
                              "High": "high"})[["iso3", "year", "value", "low", "high"]]
        d.sort_values(["iso3", "year"]).to_csv(GHO_DIR / f"{code}.csv", index=False)
        print(f"  {code}: {d.iso3.nunique()} countries, latest year {int(d.year.max())}")


def series(code: str) -> pd.DataFrame:
    return pd.read_csv(GHO_DIR / f"{code}.csv")


def latest(code: str, index) -> tuple[pd.Series, pd.Series]:
    d = series(code).sort_values("year").groupby("iso3").tail(1).set_index("iso3")
    return d["value"].reindex(index), d["year"].reindex(index)


def annual_trend(d: pd.DataFrame, index) -> pd.Series:
    """Average annual % change over TREND_YEARS from a log-linear fit (at least 5 positive years), clipped; countries
    without usable data get the median (as prepare_model.annual_trend)."""
    d = d[d.year.between(*TREND_YEARS) & (d.value > 0)]
    out = {iso: float(np.expm1(np.polyfit(g["year"], np.log(g["value"]), 1)[0]))
           for iso, g in d.groupby("iso3") if len(g) >= 5}
    t = pd.Series(out, dtype=float).reindex(index).clip(*TREND_CLIP)
    return t.fillna(t.median())


def _put(ci, col, value, year, source, fallback_source):
    """Use the WHO value where there is one, keep the existing (derived) value elsewhere."""
    have = value.notna()
    if col not in ci:
        ci[col] = np.nan
    old_year = ci[f"{col}_year"] if f"{col}_year" in ci else pd.Series(np.nan, index=ci.index)
    ci[col] = value.where(have, ci[col])
    ci[f"{col}_year"] = year.where(have, old_year)
    ci[f"{col}_source"] = np.where(have, source, fallback_source)


def apply(ci: pd.DataFrame) -> pd.DataFrame:
    ci = ci.copy()
    idx = ci.index
    # --- HIV (UNAIDS estimates as published by WHO) ---
    v, y = latest("HIV_0000000001", idx)
    _put(ci, "plhiv", v, y, "UNAIDS/WHO estimate",
         "derived: adult prevalence x population 15-64 (2011 calibration) + children (no UNAIDS estimate published)")
    v, y = latest("HIV_ARTCOVERAGE", idx)
    _put(ci, "sh_hiv_artc_zs", v, y, "UNAIDS/WHO estimate", "World Bank WDI (UNAIDS)")
    cov, ycov = latest("HIV_0000000020", idx)
    _put(ci, "sh_hiv_pmtc_zs", cov, ycov, "UNAIDS/WHO estimate", "World Bank WDI (UNAIDS)")
    n, _ = latest("HIV_0000000016", idx)
    # pregnant women living with HIV = women receiving ARVs / coverage; where coverage is reported as 100% (top-coded)
    # this is a lower bound, so the larger of it and the births-based estimate is kept
    preg = n / (cov / 100)
    preg = preg.where((cov > 0) & (cov < 100), np.fmax(preg, ci["hiv_pos_pregnancies"]))
    _put(ci, "hiv_pos_pregnancies", preg.where(n.notna() & cov.notna()), ycov,
         "UNAIDS/WHO: women receiving ARVs / PMTCT coverage",
         "derived: births x adult prevalence x 1.15 (no UNAIDS estimate published)")
    # --- malaria (World Malaria Report estimates) ---
    deaths, yd = latest("MALARIA_EST_DEATHS", idx)
    _put(ci, "malaria_deaths", deaths, yd, "WHO World Malaria Report estimate",
         "derived: child malaria deaths (WHO/MCEE) / regional under-5 share (no WHO estimate published)")
    cases, yc = latest("MALARIA_EST_CASES", idx)
    inc, _ = latest("MALARIA_EST_INCIDENCE", idx)
    _put(ci, "malaria_cases", cases, yc, "WHO World Malaria Report estimate",
         "derived: incidence x population at risk (no WHO estimate published)")
    par = (cases / inc * 1000).where(inc > 0)
    _put(ci, "malaria_pop_at_risk", par.clip(upper=ci["sp_pop_totl"]), yc,
         "WHO: estimated cases / incidence per 1,000 at risk",
         "assumption: 95% (sub-Saharan Africa) or 35% of the population (no WHO estimate published)")
    itn, yi = latest("MALARIA_ITN_USE", idx)
    _put(ci, "sh_mlr_nets_zs", itn, yi, "WHO/Malaria Atlas Project modelled ITN use, whole population",
         "latest household survey: children under 5 sleeping under an ITN (World Bank WDI)")
    tr = series("MALARIA_EST_DEATHS")
    ci["trend_malaria_deaths"] = annual_trend(tr[tr.iso3.isin(idx)], idx)
    return ci


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--download", action="store_true", help="refresh ext_data/gho/ from the WHO GHO API first")
    args = p.parse_args()
    if args.download or not GHO_DIR.exists():
        download()
    ci = pd.read_csv(INPUTS_FILE).set_index("iso3")
    new = apply(ci)
    for c in ("plhiv", "sh_hiv_artc_zs", "hiv_pos_pregnancies", "malaria_deaths", "malaria_cases",
              "malaria_pop_at_risk", "sh_mlr_nets_zs"):
        src = new[f"{c}_source"]
        who = src.str.startswith(("UNAIDS", "WHO")).sum()
        print(f"  {c:22s} WHO/UNAIDS for {who} of {len(new)} countries; "
              f"total {ci[c].sum():,.0f} -> {new[c].sum():,.0f}")
    new.reset_index().to_csv(INPUTS_FILE, index=False)
    print("updated", INPUTS_FILE)


if __name__ == "__main__":
    main()
