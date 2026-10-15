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


def apply(ci: pd.DataFrame) -> pd.DataFrame:
    ci = ci.copy()
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
    new.reset_index().to_csv(INPUTS_FILE, index=False)
    print("updated", INPUTS_FILE)


if __name__ == "__main__":
    main()
