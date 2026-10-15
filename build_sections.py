"""
Rebuild the Sections 1-3 per-country files from the raw datasets on disk (logic review L-38 / IMP-12; Batch 7 item 15).

    python build_sections.py --country-data   # country_data/<Country>.csv + _index.csv from the IHME DAH database
    python build_sections.py --spending-data  # spending_data/<ISO3>.csv + _index.csv from IHME health spending 1995-2023
                                              # and expected spending 2024-2050
    python build_sections.py --verify         # rebuild both into a temporary folder and compare with the committed files

Not rebuildable from what is on disk (left as they are): macro_data/<ISO3>.csv (needs the full IMF WEO series: GDP,
revenue, expenditure, debt, population; only the general-government balances are in datasets/), revenue_data/
(needs the IMF WoRLD mapping of revenue codes to the file's label, group and coverage columns and the general-
government totals; the WoRLD download in datasets/ is central-government by series code without that mapping) and
cofog_all/ (COFOG spending by function is not on disk).
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
DAH = HERE / "datasets" / "IHME_DAH_DATABASE_1990_2026_Y2026M09D18.CSV"
SPEND = HERE / "datasets" / "IHME_HEALTH_SPENDING_1995_2023_Y2026M09D21.CSV"
EXPECTED = HERE / "datasets" / "IHME_EXPECTED_HEALTH_SPENDING_2024_2050_Y2026M09D23.CSV"
SPEND_COLS = ["the_total_mean", "the_per_cap_mean", "ghes_total_mean", "ppp_total_mean", "oop_total_mean", "dah_total_mean",
              "ghes_per_cap_mean", "ppp_per_cap_mean", "oop_per_cap_mean", "dah_per_cap_mean", "ghes_per_gdp_mean"]


def country_iso_map():
    idx = pd.read_csv(HERE / "country_data" / "_index.csv")
    return dict(zip(idx.recipient_isocode, idx.recipient_country)), dict(zip(idx.recipient_isocode, idx.file))


def build_country_data(out: Path):
    """One file per country with every IHME DAH row for that recipient after dropping elim_ch == 1 (double-counted
    transfers), all programme-area columns kept; `_index.csv` lists the files."""
    names, files = country_iso_map()
    template = pd.read_csv(HERE / "country_data" / files[next(iter(files))], nrows=1).columns.tolist()
    raw = pd.read_csv(DAH, na_values=["-"], low_memory=False)
    raw = raw[(raw.elim_ch == 0) & raw.recipient_isocode.isin(files)]
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for iso, f in files.items():
        d = raw[raw.recipient_isocode == iso][[c for c in template if c in raw.columns]].copy()
        num = [c for c in d.columns if c.endswith("_dah_23")]
        d[num] = d[num].fillna(0.0)                 # IHME writes '-' for an empty programme area; the files hold 0
        d.to_csv(out / f, index=False)
        rows.append({"recipient_country": names[iso], "recipient_isocode": iso, "file": f})
    pd.DataFrame(rows).to_csv(out / "_index.csv", index=False)
    return len(rows)


def build_spending_data(out: Path):
    """One file per country: IHME health spending 1995-2023 (projected = 0) followed by expected spending 2024-2050
    (projected = 1), the eleven columns the dashboard reads."""
    idx = pd.read_csv(HERE / "spending_data" / "_index.csv")
    h = pd.read_csv(SPEND, encoding="utf-8-sig", low_memory=False)
    e = pd.read_csv(EXPECTED, encoding="utf-8-sig", low_memory=False)
    h, e = h[h.level == "Country"], e[e.level == "Country"]
    out.mkdir(parents=True, exist_ok=True)
    for iso, name in zip(idx.iso3, idx.location_name):
        a = h[h.iso3 == iso].assign(projected=0)
        b = e[e.iso3 == iso].assign(projected=1)
        d = pd.concat([a, b], ignore_index=True)
        for c in SPEND_COLS:
            if c not in d.columns:
                d[c] = np.nan
        d.loc[d.projected == 1, "ghes_per_gdp_mean"] = np.nan   # the files carry the GDP share for observed years only
        d = d[["iso3", "year", "projected"] + SPEND_COLS].assign(location_name=name)
        d = d[["iso3", "location_name", "year", "projected"] + SPEND_COLS].sort_values("year")
        d.to_csv(out / f"{iso}.csv", index=False)
    idx.to_csv(out / "_index.csv", index=False)
    return len(idx)


def compare(new_dir: Path, old_dir: Path, key_cols) -> dict:
    """Largest relative difference per file between a rebuilt folder and the committed one (numeric columns)."""
    worst = {}
    for f in sorted(old_dir.glob("*.csv")):
        if f.name == "_index.csv":
            continue
        o, n = pd.read_csv(f), pd.read_csv(new_dir / f.name)
        o, n = o.sort_values(key_cols).reset_index(drop=True), n.sort_values(key_cols).reset_index(drop=True)
        if len(o) != len(n):
            worst[f.name] = float("inf")
            continue
        num = [c for c in o.columns if c in n.columns and pd.api.types.is_numeric_dtype(o[c])]
        diff = 0.0
        for c in num:
            a, b = o[c].to_numpy(dtype=float), n[c].to_numpy(dtype=float)
            both = ~(np.isnan(a) & np.isnan(b))
            if (np.isnan(a) != np.isnan(b)).any():
                diff = max(diff, float("inf"))
                continue
            scale = np.maximum(np.abs(a[both]), 1.0)
            diff = max(diff, float(np.max(np.abs(a[both] - b[both]) / scale)) if both.any() else 0.0)
        worst[f.name] = diff
    return worst


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--country-data", action="store_true")
    p.add_argument("--spending-data", action="store_true")
    p.add_argument("--verify", action="store_true")
    a = p.parse_args()
    if a.verify:
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            n = build_country_data(tmp / "country_data")
            w = compare(tmp / "country_data", HERE / "country_data", ["year", "source", "channel"])
            print(f"country_data: {n} files rebuilt; within 0.5%: {sum(v <= 0.005 for v in w.values())} of {len(w)}; worst {max(w.values()):.4%}")
            n = build_spending_data(tmp / "spending_data")
            w = compare(tmp / "spending_data", HERE / "spending_data", ["year"])
            bad = {k: v for k, v in w.items() if v > 0.005}
            print(f"spending_data: {n} files rebuilt; within 0.5%: {sum(v <= 0.005 for v in w.values())} of {len(w)}; worst {max(w.values()):.4%}; outside: {bad}")
        return
    if a.country_data:
        print("country_data:", build_country_data(HERE / "country_data"), "files")
    if a.spending_data:
        print("spending_data:", build_spending_data(HERE / "spending_data"), "files")


if __name__ == "__main__":
    main()
