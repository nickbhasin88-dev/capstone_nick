"""
Immunization coverage inputs from the WHO/UNICEF Estimates of National Immunization Coverage (WUENIC), 2025 revision
(logic review L-17, IMP-24; Batch 7 items 3-4).

    python immunization_inputs.py        # patch model_data/country_inputs.csv in place (needs datasets/WUENIC_2025.xlsx)

Replaces the World Bank WDI mirror values of DTP3 (`sh_imm_idpt`) and MCV1 (`sh_imm_meas`) with WUENIC's own
estimates (latest year per country, coverage in % of surviving infants), with `<column>_year` and `<column>_source`.
Where WUENIC has no value for a country the previous value and source are kept. Called by prepare_model.py (full
rebuild) after who_inputs.apply(), and runnable on its own.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
WUENIC_FILE = HERE / "datasets" / "WUENIC_2025.xlsx"
INPUTS_FILE = HERE / "model_data" / "country_inputs.csv"
SOURCE = "WHO/UNICEF WUENIC 2025 revision (datasets/WUENIC_2025.xlsx)"
ANTIGENS = {"sh_imm_idpt": "dtp3", "sh_imm_meas": "mcv1"}


def wuenic_latest(path: Path = WUENIC_FILE) -> pd.DataFrame:
    """One row per ISO3: latest-year coverage and year for each antigen in ANTIGENS."""
    w = pd.read_excel(path, "country", usecols=["iso3c", "vaccine", "year", "coverage"]).dropna(subset=["coverage"])
    out = {}
    for col, ant in ANTIGENS.items():
        d = w[w.vaccine == ant].sort_values("year").groupby("iso3c").tail(1).set_index("iso3c")
        out[col], out[f"{col}_year"] = d["coverage"], d["year"]
    return pd.DataFrame(out)


def wuenic_series(antigen: str, path: Path = WUENIC_FILE) -> pd.DataFrame:
    """Full country-year series for one antigen (iso3, year, value), for the regression panel."""
    w = pd.read_excel(path, "country", usecols=["iso3c", "vaccine", "year", "coverage"]).dropna(subset=["coverage"])
    d = w[w.vaccine == antigen].rename(columns={"iso3c": "iso3", "coverage": "value"})[["iso3", "year", "value"]]
    d["year"] = d["year"].astype(int)
    return d.sort_values(["iso3", "year"]).reset_index(drop=True)


WPP_FILE = HERE / "datasets" / "WPP2024" / "WPP2024_Demographic_Indicators_Medium.csv"
BIRTH_YEARS = range(2026, 2031)
WPP_SOURCE = "UN WPP 2024 medium variant, Births (thousands x 1,000)"


def apply_births(ci: pd.DataFrame) -> pd.DataFrame:
    """births_2026 .. births_2030 (people) from the WPP 2024 medium-variant projections (logic review L-24, Batch 7
    item 12): the immunization line's people in need year by year. Countries without a WPP value keep NaN and the
    model falls back to the latest-year `births`."""
    ci = ci.copy()
    wp = pd.read_csv(WPP_FILE, usecols=["ISO3_code", "Time", "Births"], low_memory=False).dropna(subset=["ISO3_code"])
    b = wp[wp.Time.isin(list(BIRTH_YEARS))].pivot(index="ISO3_code", columns="Time", values="Births").reindex(ci.index) * 1000
    for y in BIRTH_YEARS:
        ci[f"births_{y}"] = b[y]
    ci["births_proj_source"] = np.where(b.notna().all(axis=1), WPP_SOURCE, "")
    return ci


def apply(ci: pd.DataFrame) -> pd.DataFrame:
    ci = apply_births(ci)
    t = wuenic_latest().reindex(ci.index)
    for col in ANTIGENS:
        have = t[col].notna()
        ci[f"{col}_source"] = np.where(have, SOURCE, ci.get(f"{col}_source", pd.Series("World Bank WDI mirror", index=ci.index)))
        ci[col] = t[col].where(have, ci[col])
        ci[f"{col}_year"] = t[f"{col}_year"].where(have, ci.get(f"{col}_year"))
    return ci


def main():
    ci = pd.read_csv(INPUTS_FILE).set_index("iso3")
    new = apply(ci)
    for col in ANTIGENS:
        d = (new[col] - ci[col]).abs()
        print(f"  {col}: WUENIC for {int((new[f'{col}_source'] == SOURCE).sum())} of {len(ci)}; year {new[f'{col}_year'].value_counts().to_dict()}; "
              f"changed by > 2 points in {int((d > 2).sum())} countries")
    print(f"  births 2026-2030 from WPP for {int((new['births_proj_source'] != '').sum())} of {len(ci)}; "
          f"2026 / latest-year births median {(new['births_2026'] / new['births']).median():.3f}")
    new.reset_index().to_csv(INPUTS_FILE, index=False)
    print("updated", INPUTS_FILE)


if __name__ == "__main__":
    main()
