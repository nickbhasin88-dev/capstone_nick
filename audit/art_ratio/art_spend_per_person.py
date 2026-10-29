"""
HIV care-and-treatment spending per person on ART, all sources, 15 MOU countries: how much money it takes to keep one
person on treatment for a year.

    $ per person on ART (2023 US$) = IHME HIV/AIDS spending on care and treatment, all sources (year y)
                                     / UNAIDS people receiving ART, all ages (year y), inflated 2019 -> 2023 (US CPI-U)

- Numerator: IHME Global HIV/AIDS Spending 2000-2017 (care_total_mean, lower, upper; thousands of 2019 US$; government,
  prepaid private, out-of-pocket and development assistance together), from the VIHspending sheet of Allel et al.
  2022 S1 Data (PLOS Global Public Health 2(8):e0000463). The same IHME release is on GHDx
  (ghdx.healthdata.org/record/global-hivaids-spending-2000-2017; login needed).
- Denominator: UNAIDS AIDSinfo 2026 estimates, PEOPLE_RECEIVING_ART, all ages, unrounded, same year.
- Year: 2017, the last year of the IHME series. Also reported: the 2015-2017 mean, as a check on one-year noise.
- Range: IHME's lower and upper care-and-treatment estimates over the same denominator.

    .venv/bin/python audit/art_ratio/art_spend_per_person.py  -> audit/art_ratio/art_spend_per_person.csv
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
logging.disable(logging.WARNING)
import health_model as hm  # noqa: E402

IHME = ROOT / "datasets" / "Allel2022" / "Allel2022_S1_Data_DEA_databook.xlsx"
UNAIDS = ROOT / "datasets" / "UNAIDS_2026" / "UNAIDS_Estimates_2026.csv"
OUT = Path(__file__).resolve().parent / "art_spend_per_person.csv"

COUNTRIES = {"BWA": "Botswana", "BDI": "Burundi", "CMR": "Cameroon", "SWZ": "Eswatini", "ETH": "Ethiopia", "KEN": "Kenya",
             "LSO": "Lesotho", "LBR": "Liberia", "MDG": "Madagascar", "MWI": "Malawi", "MOZ": "Mozambique",
             "NGA": "Nigeria", "RWA": "Rwanda", "SLE": "Sierra Leone", "UGA": "Uganda"}
YEAR, CHECK_YEARS = 2017, (2015, 2016, 2017)
IHME_PRICE_YEAR = 2019
OUTLIER = 1.5       # flagged when more than 1.5x or less than 1/1.5 of the 15-country median


def people_on_art() -> pd.Series:
    u = pd.read_csv(UNAIDS, usecols=["Indicator_GId", "Subgroup_Val_GId", "Area", "Area Level", "Time Period", "Data value"])
    u = u[(u.Indicator_GId == "PEOPLE_RECEIVING_ART") & (u["Area Level"] == 2) & (u.Subgroup_Val_GId == "ALL_AGES")]
    u["iso3"] = u.Area.map({v: k for k, v in COUNTRIES.items()})
    missing = set(COUNTRIES.values()) - set(u.Area)
    if missing:
        raise SystemExit(f"UNAIDS area names not matched: {sorted(missing)}")
    return u.dropna(subset=["iso3"]).set_index(["iso3", "Time Period"])["Data value"].astype(float)


def main():
    v = pd.read_excel(IHME, sheet_name="VIHspending")
    v = v[(v.level == "Country") & v.iso3.isin(COUNTRIES)].set_index(["iso3", "year"])
    art = people_on_art()
    k = 1e3 * hm.inflate(1.0, IHME_PRICE_YEAR)            # thousands of 2019 US$ -> 2023 US$
    rows = []
    for iso, name in COUNTRIES.items():
        n = art[(iso, YEAR)]
        r = v.loc[(iso, YEAR)]
        chk = [v.loc[(iso, y), "care_total_mean"] * k / art[(iso, y)] for y in CHECK_YEARS]
        rows.append({"iso3": iso, "country": name, "year": YEAR,
                     "care_treat_spend_k2019usd": r.care_total_mean, "people_on_art": n,
                     "usd_per_person_on_art": r.care_total_mean * k / n,
                     "usd_per_person_on_art_lo": r.care_total_lower * k / n,
                     "usd_per_person_on_art_hi": r.care_total_upper * k / n,
                     "usd_per_person_on_art_2015_17_mean": float(np.mean(chk)),
                     "care_share_of_hiv_spending": r.care_per_the_mean,
                     "donor_share_of_hiv_spending": r.dah_per_the_mean})
    t = pd.DataFrame(rows)
    med = t.usd_per_person_on_art.median()
    x = t.usd_per_person_on_art
    t["outlier"] = np.where(x > OUTLIER * med, "high", np.where(x < med / OUTLIER, "low", ""))
    t.loc[t.people_on_art < 25_000, "outlier"] = (t.outlier + "; small programme (<25,000 on ART)").str.lstrip("; ")
    t = t.sort_values("usd_per_person_on_art")
    t.to_csv(OUT, index=False)
    pd.set_option("display.width", 250)
    print(t.drop(columns=["care_treat_spend_k2019usd"]).round(2).to_string(index=False))
    print(f"median {med:.0f} (2023 US$); wrote {OUT}")


if __name__ == "__main__":
    main()
