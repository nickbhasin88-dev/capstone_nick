"""
HIV inputs from the UNAIDS AIDSinfo 2026 estimates file (logic review IMP-24, L-11; Batch 7 items 4-5).

    python unaids_inputs.py        # patch model_data/country_inputs.csv in place (needs datasets/UNAIDS_2026/)

Reads `datasets/UNAIDS_2026/UNAIDS_Estimates_2026.csv` (Area Level 2 = countries, unrounded `Data value`, latest
year with a value, 2025 in the 2026 round) and writes, each with `<column>_year` and `<column>_source`:
    plhiv                 People living with HIV, all ages
    sh_hiv_artc_zs        Coverage of people living with HIV receiving ART, all ages (%)
    sh_hiv_pmtc_zs        Coverage of pregnant women who receive ARV for preventing MTCT (%)
    hiv_pos_pregnancies   Pregnant women needing ARV for preventing MTCT
    sh_hiv_incd_tl        New HIV infections, all ages
    hiv_deaths_unaids     AIDS-related deaths, all ages (new column; Validation page, Lancet rate-ratio method)
Where UNAIDS has no value the previous value and source are kept (WHO GHO or the derived fallback). The same UNAIDS
estimates reach the model through the WHO Global Health Observatory (`who_inputs.py`); this file is the primary
source and GHO the fallback. Called by prepare_model.py after who_inputs.apply(); runnable on its own.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
UNAIDS_FILE = HERE / "datasets" / "UNAIDS_2026" / "UNAIDS_Estimates_2026.csv"
INPUTS_FILE = HERE / "model_data" / "country_inputs.csv"
SOURCE = "UNAIDS AIDSinfo 2026 estimates (datasets/UNAIDS_2026)"
WANT = {  # column -> (indicator, subgroup)
    "plhiv": ("People living with HIV", "All ages estimate"),
    "sh_hiv_artc_zs": ("Coverage of people living with HIV receiving ART", "All ages estimate"),
    "sh_hiv_pmtc_zs": ("Coverage of pregnant women who receive ARV for preventing MTCT", "estimate"),
    "hiv_pos_pregnancies": ("Pregnant women needing ARV for preventing MTCT", "estimate"),
    "sh_hiv_incd_tl": ("New HIV Infections", "All ages estimate"),
    "hiv_deaths_unaids": ("AIDS-related deaths", "All ages estimate"),
}


def unaids_latest(path: Path = UNAIDS_FILE) -> pd.DataFrame:
    """One row per ISO3 with each WANT column and its year (latest year with a value)."""
    u = pd.read_csv(path, low_memory=False, usecols=["Indicator", "Subgroup", "Area ID", "Area Level", "Time Period", "Data value"])
    u = u[u["Area Level"] == 2].copy()
    u["Data value"] = pd.to_numeric(u["Data value"], errors="coerce")
    u = u.dropna(subset=["Data value"])
    out = {}
    for col, (ind, sub) in WANT.items():
        d = u[(u.Indicator == ind) & (u.Subgroup == sub)].sort_values("Time Period").groupby("Area ID").tail(1).set_index("Area ID")
        out[col], out[f"{col}_year"] = d["Data value"], d["Time Period"]
    return pd.DataFrame(out)


def apply(ci: pd.DataFrame) -> pd.DataFrame:
    ci = ci.copy()
    t = unaids_latest().reindex(ci.index)
    for col in WANT:
        have = t[col].notna()
        prev_src = ci[f"{col}_source"] if f"{col}_source" in ci else pd.Series("", index=ci.index)
        ci[f"{col}_source"] = np.where(have, SOURCE, prev_src)
        ci[col] = t[col].where(have, ci[col] if col in ci else np.nan)
        ci[f"{col}_year"] = t[f"{col}_year"].where(have, ci.get(f"{col}_year"))
    return ci


def main():
    ci = pd.read_csv(INPUTS_FILE).set_index("iso3")
    new = apply(ci)
    for col in WANT:
        n = int((new[f"{col}_source"] == SOURCE).sum())
        if col in ci:
            r = (new[col] / ci[col]).replace([np.inf, -np.inf], np.nan)
            print(f"  {col}: UNAIDS for {n} of {len(ci)}; new / old median {r.median():.3f}, outside 0.9-1.1 in {int(((r > 1.1) | (r < 0.9)).sum())}")
        else:
            print(f"  {col}: UNAIDS for {n} of {len(ci)} (new column)")
    new.reset_index().to_csv(INPUTS_FILE, index=False)
    print("updated", INPUTS_FILE)


if __name__ == "__main__":
    main()
