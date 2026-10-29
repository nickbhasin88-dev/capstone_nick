"""
Batch 3+4, item D (IMP-03): site-level ART cost per patient-year by country from the GHCC Unit Cost Study Repository
(datasets/GHCC_UCSR/GHCC_UCSR_HIV_ART.xlsx, 2020 US$ per datasets/MANIFEST.md) pooled with the Rosen et al. 2021 site
costs already in unit_cost_reference.csv. Read-only with respect to the model.

    .venv/bin/python audit/batch34_art_costs.py

Eligible GHCC records: output unit per person (patient) per year; provider perspective; above-service costs not
included ("No Costs Included" or not stated); a numeric mean unit cost. Records that include some above-service costs
are left out because the model adds its own above-site markup (1 / (1 - asd_share)). Recency: the record's price year
("Reported Currency Year"; the reference year where it is not stated) must be 2015 or later, so that the ARV prices
in the cost are those of the dolutegravir era rather than the 2010-2014 regimens (a concept-match rule set before the
values were seen; the all-years variant is kept in the output as site_cost_allyears for comparison).
Financial vs economic: 98 of 99 GHCC ART records are economic costs. Financial costs are the central concept (donor
money buys financial costs), so every economic value is scaled by the financial / economic ratio measured where both
exist in Value TB (datasets/ValueTB, same facilities, both variants): a labelled adjustment, not an ART measurement.
Central = the country's median across eligible records (2023 US$); range = the 25th-75th percentile of the records
(or +/-25% with fewer than 3 records). Countries with no eligible study: the median of the model countries with a study
in their WHO region (at least 3), else in their World Bank income group, else overall.
Gate (batch34 rules): every country site cost between US$50 and US$600 per patient-year; countries outside use the
fallback and are listed.
Writes audit/logic_review/batch34_art_costs.csv.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import health_model as hm  # noqa: E402

GHCC = ROOT / "datasets" / "GHCC_UCSR" / "GHCC_UCSR_HIV_ART.xlsx"
VALUETB = ROOT / "datasets" / "ValueTB" / "ValueTB_pooled_patient.dta"
OUT = ROOT / "audit" / "logic_review" / "batch34_art_costs.csv"
GHCC_COST_YEAR = 2020            # datasets/MANIFEST.md: "GHCC UCSR costs are in 2020 USD"
COUNTRY = {"Côte d'Ivoire": "CIV", "Eswatini": "SWZ", "Ghana": "GHA", "India": "IND", "Indonesia": "IDN",
           "Kenya": "KEN", "Malawi": "MWI", "Nigeria": "NGA", "South Africa": "ZAF",
           "Tanzania, United Republic of": "TZA", "Uganda": "UGA", "Zambia": "ZMB"}
PER_YEAR = {"Per Person Treated Per Year", "Per Patient Year", "Per Person Served Per Year",
            "Per Person Seen In Year On ART"}
LO, HI = 50.0, 600.0
RECENT_FROM = 2015


def fin_econ_ratio() -> tuple[float, int]:
    """Financial / economic cost ratio from Value TB: per facility x intervention, bottom-up, where both exist."""
    d = pd.read_stata(VALUETB, convert_categoricals=False)
    d = d[(d.met_TDvBU == "BU") & (d.tcost_USD > 0)]
    key = ["fc_country", "fc_code", "int_detail", "int_phase", "int_phase2"]
    f = d[d.met_FINvECON == "FIN"].groupby(key).tcost_USD.first()
    e = d[d.met_FINvECON == "ECON"].groupby(key).tcost_USD.first()
    j = pd.concat([f.rename("fin"), e.rename("econ")], axis=1).dropna()
    r = j.fin / j.econ
    return float(r.median()), int(len(r))


def main():
    ratio, n_ratio = fin_econ_ratio()
    g = pd.read_excel(GHCC)
    g["uc"] = pd.to_numeric(g["Mean Unit Cost"], errors="coerce")
    ok = (g["Output unit"].isin(PER_YEAR) & (g["Perspective"] == "Provider") & g.uc.notna()
          & ~g["Above Service Costs Included"].astype(str).str.startswith("Some"))
    g = g[ok].copy()
    g["iso3"] = g["Country"].map(COUNTRY)
    g["price_year"] = pd.to_numeric(g["Reported Currency Year"], errors="coerce").fillna(g["Reference Year"])
    g_all = g.copy()
    g = g[g.price_year >= RECENT_FROM].copy()
    g["usd2023"] = hm.inflate(g.uc, GHCC_COST_YEAR)
    g["fin2023"] = np.where(g["Economic / Financial"].str.lower().str.startswith("financial"), g.usd2023, g.usd2023 * ratio)
    recs = g[["iso3", "fin2023", "Reference Year", "All Authors", "Title", "Economic / Financial"]].rename(
        columns={"fin2023": "usd", "Reference Year": "year", "All Authors": "authors", "Title": "title",
                 "Economic / Financial": "kind"})
    recs["source"] = "GHCC UCSR"
    # Rosen et al. 2021 site costs already in the model (site level, ARVs + labs + staff; financial costs)
    ref = pd.read_csv(ROOT / "unit_cost_reference.csv")
    ro = ref[ref.kind == "art_site_cost"]
    rosen = pd.DataFrame({"iso3": ro.key, "usd": [hm.inflate(v, y) for v, y in zip(ro.value, ro.cost_year)],
                          "year": ro.cost_year, "authors": "Rosen et al. 2021", "title": ro.source,
                          "kind": "Financial (site)", "source": "unit_cost_reference.csv"})
    recs = pd.concat([recs, rosen], ignore_index=True)
    g_all["usd2023"] = hm.inflate(g_all.uc, GHCC_COST_YEAR)
    g_all["fin2023"] = np.where(g_all["Economic / Financial"].str.lower().str.startswith("financial"), g_all.usd2023, g_all.usd2023 * ratio)
    recs_all = pd.concat([g_all[["iso3", "fin2023"]].rename(columns={"fin2023": "usd"}), rosen[["iso3", "usd"]]], ignore_index=True)

    ci = pd.read_csv(ROOT / "model_data" / "country_inputs.csv").set_index("iso3")
    lines = pd.read_csv(ROOT / "model_data" / "dah_lines.csv")
    iso_all = sorted(set(lines.iso3))
    own = recs.groupby("iso3").usd.agg(["median", "count", lambda s: s.quantile(.25), lambda s: s.quantile(.75)])
    own.columns = ["median", "n", "q25", "q75"]
    own_all = recs_all.groupby("iso3").usd.agg(["median", "count"])
    rows = []
    for iso in iso_all:
        reg, ig = ci.loc[iso, "who_region"], ci.loc[iso, "income_group"] if iso in ci.index else (None, None)
        r = {"iso3": iso, "who_region": reg, "income_group": ig, "n_records": 0, "own_median": np.nan,
             "gate_fail": False}
        if iso in own.index:
            r.update({"n_records": int(own.loc[iso, "n"]), "own_median": float(own.loc[iso, "median"]),
                      "own_q25": float(own.loc[iso, "q25"]), "own_q75": float(own.loc[iso, "q75"])})
            r["gate_fail"] = not (LO <= r["own_median"] <= HI)
        rows.append(r)
    t = pd.DataFrame(rows).set_index("iso3")
    usable = t[(t.n_records > 0) & ~t.gate_fail]
    for iso in t.index:
        if iso in usable.index:
            t.loc[iso, ["site_cost", "site_lo", "site_hi"]] = [usable.loc[iso, "own_median"], usable.loc[iso, "own_q25"],
                                                              usable.loc[iso, "own_q75"]]
            if t.loc[iso, "n_records"] < 3:
                t.loc[iso, ["site_lo", "site_hi"]] = [0.75 * usable.loc[iso, "own_median"], 1.25 * usable.loc[iso, "own_median"]]
            t.loc[iso, "source"] = f"own studies (n={int(t.loc[iso, 'n_records'])})"
            continue
        pool = usable[usable.who_region == t.loc[iso, "who_region"]]
        label = f"median of {len(pool)} model countries with studies in WHO region {t.loc[iso, 'who_region']}"
        if len(pool) < 3:
            pool = usable[usable.income_group == t.loc[iso, "income_group"]]
            label = f"median of {len(pool)} model countries with studies in income group {t.loc[iso, 'income_group']}"
        if len(pool) < 3:
            pool = usable
            label = f"median of all {len(pool)} model countries with studies"
        t.loc[iso, ["site_cost", "site_lo", "site_hi"]] = [pool.own_median.median(), pool.own_median.quantile(.25),
                                                          pool.own_median.quantile(.75)]
        t.loc[iso, "source"] = label + (" (own median outside the US$50-600 gate)" if t.loc[iso, "gate_fail"] else "")
    # the model's current site cost (2023 US$, before markup) for comparison
    P = hm.draw_params(hm.load_params(), 0)
    t["current_site_cost"] = [float(hm.unit_costs(ci.loc[iso], P)["hiv_art"][0] * (1 - P["asd_share"][0])) for iso in t.index]
    t["cost_year"] = 2023
    # all-years variant (no recency rule): own median where any eligible record exists, else the AFR / income / overall
    # median of those, for comparison only
    oa = own_all[own_all["median"].between(LO, HI)]
    for iso in t.index:
        if iso in oa.index:
            t.loc[iso, "site_cost_allyears"] = float(oa.loc[iso, "median"])
            t.loc[iso, "n_records_allyears"] = int(oa.loc[iso, "count"])
        else:
            pool = oa[oa.index.isin(t.index[t.who_region == t.loc[iso, "who_region"]])]
            if len(pool) < 3:
                pool = oa[oa.index.isin(t.index[t.income_group == t.loc[iso, "income_group"]])]
            if len(pool) < 3:
                pool = oa
            t.loc[iso, "site_cost_allyears"] = float(pool["median"].median())
            t.loc[iso, "n_records_allyears"] = 0
    t.reset_index().to_csv(OUT, index=False)

    pd.set_option("display.width", 250)
    print(f"financial / economic ratio (Value TB, bottom-up, {n_ratio} facility-interventions): {ratio:.3f}")
    print(f"eligible GHCC records: {len(g)} (price year >= {RECENT_FROM}; {len(g_all)} with any year) in {g.iso3.nunique()} countries; "
          f"with Rosen: {recs.iso3.nunique()} countries")
    print(recs.groupby("iso3").usd.agg(["count", "median", "min", "max"]).round(0).to_string())
    print(f"\nmodel countries with their own value: {int((t.source.str.startswith('own')).sum())} of {len(t)}; "
          f"gate failures: {list(t.index[t.gate_fail])}")
    print(t.source.value_counts().to_string())
    print(t[["site_cost", "site_cost_allyears", "current_site_cost"]].describe().round(0).to_string())
    print(t.loc[["KEN", "NGA", "MOZ", "ZAF", "UGA", "IND", "IDN", "MWI", "ZMB", "ZWE"], ["site_cost", "site_lo", "site_hi", "site_cost_allyears", "current_site_cost", "source"]].round(0).to_string())


if __name__ == "__main__":
    main()
