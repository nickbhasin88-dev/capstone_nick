"""
Adds the two derived columns the dashboard needs to put every dollar figure in constant 2023 US$.

    python add_constant_dollars.py

1. macro_data/<ISO3>.csv  -> gdp_usd_bn_2023: GDP in constant 2023 US$ (billions).
   IHME's "constant 2023 US$" (used by the DAH and health-spending data in Sections 1, 2 and 4) deflates with each
   country's own prices and converts at 2023 exchange rates. To match it, GDP in year y is the IMF WEO 2023 GDP
   (current 2023 US$ = constant 2023 US$ in 2023) moved to year y with IHME's real GDP per person and the WEO
   population:   GDP_2023$(y) = GDP_WEO(2023) x [gdp_pc_IHME(y) x pop(y)] / [gdp_pc_IHME(2023) x pop(2023)]
   Without a WEO 2023 GDP it falls back to gdp_pc_IHME(y) x pop(y).
2. spending_data/<ISO3>.csv -> ghes_per_gdp_mean: IHME government health spending as a share of GDP (1995-2023),
   used for the "the IMF records only part of health spending" note in Section 3.
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent
GDP_FILE = ROOT / "datasets" / "IHME_GDP_1960_2050_FGH_2026_Y2026M06D11.CSV"
SPEND_FILE = ROOT / "datasets" / "IHME_HEALTH_SPENDING_1995_2023_Y2026M09D21.CSV"
ANCHOR_YEAR = 2023


def main():
    gdp = pd.read_csv(GDP_FILE, encoding="utf-8-sig")
    gdp_pc = gdp[gdp["level"] == "Country"].set_index(["iso3", "year"])["gdp_usd_mean"]   # per person, 2023 US$
    n = 0
    for f in sorted((ROOT / "macro_data").glob("*.csv")):
        if f.name.startswith("_"):
            continue
        m = pd.read_csv(f)
        iso = m["iso3"].iloc[0]
        pc = m["year"].map(lambda y: gdp_pc.get((iso, y)))
        real = pc * m["population_m"] / 1e3                           # billions, IHME prices x WEO population
        a = m.loc[m["year"] == ANCHOR_YEAR]
        anchor_weo = a["gdp_usd_bn"].iloc[0] if len(a) else None
        anchor_real = real[m["year"] == ANCHOR_YEAR].iloc[0] if len(a) else None
        if pd.notna(anchor_weo) and pd.notna(anchor_real) and anchor_real > 0:
            m["gdp_usd_bn_2023"] = real * anchor_weo / anchor_real
        else:
            m["gdp_usd_bn_2023"] = real
        m.to_csv(f, index=False)
        n += 1
    print(f"macro_data: gdp_usd_bn_2023 added to {n} files")

    raw = pd.read_csv(SPEND_FILE, usecols=["iso3", "year", "ghes_per_gdp_mean"])
    n = 0
    for f in sorted((ROOT / "spending_data").glob("*.csv")):
        if f.name.startswith("_"):
            continue
        d = pd.read_csv(f)
        d = d.drop(columns=["ghes_per_gdp_mean"], errors="ignore").merge(raw, on=["iso3", "year"], how="left")
        d.to_csv(f, index=False)
        n += 1
    print(f"spending_data: ghes_per_gdp_mean added to {n} files")


if __name__ == "__main__":
    main()
