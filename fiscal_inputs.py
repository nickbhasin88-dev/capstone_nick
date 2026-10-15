"""
Interest payments as a share of government revenue, for the debt-stress factor in fiscal space (audit I-26).

Two sources, per country the more recent one (ties: World Bank):
  - World Bank WDI `GC.XPN.INTP.RV.ZS` (interest payments, % of revenue), already in country_inputs.csv;
  - IMF World Economic Outlook: net interest = (primary net lending/borrowing - net lending/borrowing) / revenue x 100,
    from GGXONLB_NGDP, GGXCNL_NGDP and GGR_NGDP (all % of GDP), latest actual year.
Where neither exists: the median of the dashboard countries in the same World Bank income group, marked estimated.

    python fiscal_inputs.py --download   # fetch WEO from the IMF SDMX API to datasets/, process, patch country_inputs
    python fiscal_inputs.py              # process datasets/ (if present) or reuse macro_data/weo_fiscal/, then patch

The raw download sits in datasets/ (never committed); the processed series is macro_data/weo_fiscal/weo_balances.csv
(committed; a subfolder so it is not read as a country file). who_inputs.apply() calls apply() last, so a full rebuild
(prepare_model.py) gives the same inputs.

Actual vs projection: the WEO API does not carry WEO's "estimates start after" year, so a year counts as actual only if
it is before the country's first GDP estimate year in macro_data/<ISO3>.csv (from the WEO file). This never uses a
projected year; where the fiscal accounts are final for a later year than GDP, it may use an older one.
"""
from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
RAW = HERE / "datasets" / "IMF_WEO_Oct2026_GG_balances_2026-10-13.csv"
OUT_DIR = HERE / "macro_data" / "weo_fiscal"
OUT = OUT_DIR / "weo_balances.csv"
INPUTS_FILE = HERE / "model_data" / "country_inputs.csv"
SOURCE = "IMF World Economic Outlook, October 2026 (api.imf.org SDMX, dataflow IMF.RES:WEO)"
DOWNLOADED = "2026-10-13"
CODES = ["GGXONLB_NGDP", "GGXCNL_NGDP", "GGR_NGDP"]
API = "https://api.imf.org/external/sdmx/3.0/data/dataflow/IMF.RES/WEO/%2B/{keys}.{codes}.A?c%5BTIME_PERIOD%5D=ge:2000"
WB_LABEL = "interest payments (World Bank WDI)"
IMF_LABEL = "net interest (IMF WEO October 2026: primary minus overall balance)"


def download(isos) -> pd.DataFrame:
    url = API.format(keys="+".join(sorted(isos)), codes="+".join(CODES))
    with urllib.request.urlopen(url, timeout=300) as r:
        d = json.load(r)["data"]
    st = d["structures"][0]
    dims = st["dimensions"]["series"]
    times = [v["value"] for v in st["dimensions"]["observation"][0]["values"]]
    rows = []
    for key, s in d["dataSets"][0]["series"].items():
        idx = [int(i) for i in key.split(":")]
        lab = {dims[k]["id"]: dims[k]["values"][i]["id"] for k, i in enumerate(idx)}
        for t, v in s["observations"].items():
            if v and v[0] is not None:
                rows.append({"iso3": lab["COUNTRY"], "indicator": lab["INDICATOR"], "year": int(times[int(t)]),
                             "value": float(v[0])})
    raw = pd.DataFrame(rows).sort_values(["iso3", "indicator", "year"])
    RAW.parent.mkdir(exist_ok=True)
    raw.to_csv(RAW, index=False)
    print(f"  downloaded {len(raw):,} values, {raw.iso3.nunique()} countries -> {RAW.name}")
    return raw


def first_estimate_year(iso3: str) -> float:
    """First year WEO marks GDP as an estimate (macro_data/<ISO3>.csv), or NaN."""
    p = HERE / "macro_data" / f"{iso3}.csv"
    if not p.exists():
        return np.nan
    d = pd.read_csv(p)
    e = d.loc[d["gdp_is_estimate"].astype(str) == "True", "year"]
    return float(e.min()) if len(e) else np.nan


def process(raw: pd.DataFrame) -> pd.DataFrame:
    """Wide by country-year: the three balances, net interest % of revenue, and whether the year counts as actual."""
    w = raw.pivot_table(index=["iso3", "year"], columns="indicator", values="value").reset_index()
    w["net_interest_pct_revenue"] = (w["GGXONLB_NGDP"] - w["GGXCNL_NGDP"]) / w["GGR_NGDP"] * 100
    fe = {c: first_estimate_year(c) for c in w["iso3"].unique()}
    w["first_estimate_year"] = w["iso3"].map(fe)
    w["actual"] = w["year"] < w["first_estimate_year"]
    w = w.assign(source=SOURCE, downloaded=DOWNLOADED)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    w.to_csv(OUT, index=False)
    print(f"  {OUT.relative_to(HERE)}: {w.iso3.nunique()} countries, {int(w.year.min())}-{int(w.year.max())}")
    return w


def imf_latest(index) -> pd.DataFrame:
    w = pd.read_csv(OUT)
    a = w[w["actual"] & w["net_interest_pct_revenue"].notna() & (w["GGR_NGDP"] > 0)]
    last = a.sort_values("year").groupby("iso3").tail(1).set_index("iso3")
    return last[["net_interest_pct_revenue", "year"]].reindex(index)


def apply(ci: pd.DataFrame) -> pd.DataFrame:
    """interest_pct_revenue (+ _year, _source, _estimated, flag_interest_alt_def) for every country. Primary definition
    (Batch 7 item 7, logic review L-34): IMF WEO net interest as a share of revenue, the definition with the wider
    coverage (every dashboard country). Where the IMF value is missing, the World Bank WDI interest-payments value is
    kept and flag_interest_alt_def = True marks the different definition (gross interest paid, central government);
    otherwise the income-group median of the dashboard countries, marked estimated. Before Batch 7 the rule was the
    more recent of the two sources (ties: World Bank), which mixed the definitions silently in 17 countries."""
    ci = ci.copy()
    idx = ci.index
    wb, wy = ci["gc_xpn_intp_rv_zs"], pd.to_numeric(ci.get("gc_xpn_intp_rv_zs_year"), errors="coerce")
    im = imf_latest(idx) if OUT.exists() else pd.DataFrame(index=idx, columns=["net_interest_pct_revenue", "year"])
    iv, iy = pd.to_numeric(im["net_interest_pct_revenue"]), pd.to_numeric(im["year"])
    use_imf = iv.notna()
    use_wb = wb.notna() & ~use_imf
    ci["flag_interest_alt_def"] = use_wb
    ci["interest_pct_revenue"] = np.where(use_imf, iv, np.where(use_wb, wb, np.nan))
    ci["interest_pct_revenue_year"] = np.where(use_imf, iy, np.where(use_wb, wy, np.nan))
    ci["interest_pct_revenue_source"] = np.where(use_imf, IMF_LABEL, np.where(use_wb, WB_LABEL, ""))
    ci["interest_imf"], ci["interest_imf_year"] = iv, iy                       # both kept for the comparison
    ci["interest_estimated"] = False
    have = ci["interest_pct_revenue"].notna()
    groups = ci.get("income_group", pd.Series("", index=idx)).fillna("")
    dash = ci.get("in_dashboard", pd.Series(True, index=idx)).fillna(True).astype(bool)
    med = ci[have & dash].groupby(groups[have & dash])["interest_pct_revenue"].median()
    overall = ci.loc[have & dash, "interest_pct_revenue"].median()
    for c in idx[~have]:
        g = groups[c]
        ci.loc[c, "interest_pct_revenue"] = med.get(g, overall)
        ci.loc[c, "interest_pct_revenue_source"] = (f"median of {g.replace('_', ' ')} countries" if g in med
                                                     else "median of dashboard countries")
        ci.loc[c, "interest_estimated"] = True
    return ci


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--download", action="store_true")
    a = p.parse_args()
    ci = pd.read_csv(INPUTS_FILE).set_index("iso3")
    if a.download:
        process(download(ci.index))
    elif RAW.exists():
        process(pd.read_csv(RAW))
    new = apply(ci)
    s = new["interest_pct_revenue_source"].str.split(" \\(").str[0].value_counts().to_dict()
    print("  sources:", s, "| estimated:", int(new["interest_estimated"].sum()), "| flag_interest_alt_def:", int(new["flag_interest_alt_def"].sum()))
    new.reset_index().to_csv(INPUTS_FILE, index=False)
    print("updated", INPUTS_FILE)


if __name__ == "__main__":
    main()
