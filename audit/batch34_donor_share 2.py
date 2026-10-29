"""
Batch 3+4, item F (IMP-04 / L-44): the external (donor) share of each country's spending on HIV, TB, malaria and
immunization, for the cap on the donor-funded pool of covered people. Read-only with respect to the model.

    .venv/bin/python audit/batch34_donor_share.py

Sources (latest year with data per country):
  HIV, malaria: WHO Global Health Expenditure Database (datasets/WHO_GHED/GHED_data_2026-10-14.xlsx, sheet Data):
      external funding on the disease / total spending on the disease
      = EXT (external health expenditure, million NCU) x dis11_ext_ext (or dis13_ext_ext, % of EXT) / 100 / dis11 (dis13)
  TB: WHO Global TB Programme financing (datasets/WHO_TB/TB_expenditure_utilisation_2026-10-14.csv, funding received
      2024: (rcvd_tot_gf + rcvd_tot_usaid + rcvd_tot_grnt) / rcvd_tot_sources); if missing, the 2025 budget file's
      expected funding (cf_tot_gf + cf_tot_usaid + cf_tot_grnt) / cf_tot_sources. GHED dis12 as a comparison column.
  Immunization: GHED hc62_ext / hc62 (external funding on immunization programmes / spending on immunization).
  Malaria prevention lines (bednets, spraying; Batch 4b item 3): the external share of PUBLIC malaria spending,
      dis13_ext_usd / (dis13_ext_usd + dis13_gghed_usd), because campaign nets and spraying are financed by donors and
      governments while GHED's all-source malaria total is dominated by household spending on treatment (private share
      median 35%, Nigeria 87%), which made the pool for donor-funded nets 3% of people covered in Nigeria.
Countries without a value: the median of the model countries with data in the same WHO region (at least 3), else the
overall median. Concept note: a spending share is not the share of covered people whose service is donor-funded;
it is the closest external measure (red-team point 9) and is applied with that label.
Writes audit/logic_review/batch34_donor_share.csv.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
GHED = ROOT / "datasets" / "WHO_GHED" / "GHED_data_2026-10-14.xlsx"
WHO_TB = ROOT / "datasets" / "WHO_TB"
OUT = ROOT / "audit" / "logic_review" / "batch34_donor_share.csv"


def latest(df, code_col="code"):
    return df.sort_values("year").groupby(code_col).tail(1).set_index(code_col)


def main():
    lines = pd.read_csv(ROOT / "model_data" / "dah_lines.csv")
    iso_all = sorted(set(lines.iso3))
    ci = pd.read_csv(ROOT / "model_data" / "country_inputs.csv").set_index("iso3")
    d = pd.read_excel(GHED, sheet_name="Data",
                      usecols=["code", "year", "ext", "dis11", "dis12", "dis13", "dis11_ext_ext", "dis12_ext_ext",
                               "dis13_ext_ext", "hc62", "hc62_ext", "dis13_ext_usd", "dis13_gghed_usd", "dis13_pvtd_usd",
                               "dis13_usd"])
    d = d[d.code.isin(iso_all)]
    t = pd.DataFrame(index=iso_all)
    t["who_region"] = ci.who_region.reindex(iso_all)
    for b, dis in (("HIV", "dis11"), ("Malaria", "dis13"), ("TB_ghed", "dis12")):
        s = d.dropna(subset=["ext", dis, dis + "_ext_ext"])
        s = s[s[dis] > 0].copy()
        s["sh"] = (s.ext * s[dis + "_ext_ext"] / 100 / s[dis]).clip(0, 1)
        la = latest(s)
        t[f"{b}_share"], t[f"{b}_year"] = la.sh.reindex(iso_all), la.year.reindex(iso_all)
    s = d.dropna(subset=["dis13_ext_usd"]).copy()
    s["pub"] = s.dis13_ext_usd + s.dis13_gghed_usd.fillna(0)
    s = s[s.pub > 0]
    s["sh"] = (s.dis13_ext_usd / s.pub).clip(0, 1)
    s["priv"] = (s.dis13_pvtd_usd / s.dis13_usd).where(s.dis13_usd > 0)
    la = latest(s)
    t["Malaria_prev_share"], t["Malaria_prev_year"] = la.sh.reindex(iso_all), la.year.reindex(iso_all)
    t["Malaria_private_share"] = la.priv.reindex(iso_all)
    s = d.dropna(subset=["hc62", "hc62_ext"])
    s = s[s.hc62 > 0].copy()
    s["sh"] = (s.hc62_ext / s.hc62).clip(0, 1)
    la = latest(s)
    t["Immunization_share"], t["Immunization_year"] = la.sh.reindex(iso_all), la.year.reindex(iso_all)
    ex = pd.read_csv(WHO_TB / "TB_expenditure_utilisation_2026-10-14.csv")
    ex = ex[ex.iso3.isin(iso_all) & (ex.rcvd_tot_sources > 0)].copy()
    ex["sh"] = (ex[["rcvd_tot_gf", "rcvd_tot_usaid", "rcvd_tot_grnt"]].sum(axis=1, min_count=1) / ex.rcvd_tot_sources).clip(0, 1)
    la = latest(ex.dropna(subset=["sh"]), "iso3")
    t["TB_share"], t["TB_year"], t["TB_source"] = la.sh.reindex(iso_all), la.year.reindex(iso_all), "WHO TB funding received"
    bud = pd.read_csv(WHO_TB / "TB_budget_2026-10-14.csv")
    bud = bud[bud.iso3.isin(iso_all) & (bud.cf_tot_sources > 0)].copy()
    bud["sh"] = (bud[["cf_tot_gf", "cf_tot_usaid", "cf_tot_grnt"]].sum(axis=1, min_count=1) / bud.cf_tot_sources).clip(0, 1)
    lb = latest(bud.dropna(subset=["sh"]), "iso3")
    miss = t.TB_share.isna() & lb.sh.reindex(iso_all).notna()
    t.loc[miss, "TB_share"], t.loc[miss, "TB_year"], t.loc[miss, "TB_source"] = lb.sh.reindex(iso_all)[miss], lb.year.reindex(iso_all)[miss], "WHO TB expected funding (budget file)"
    t.loc[t.TB_share.isna(), "TB_source"] = ""
    for b in ("HIV", "Malaria", "Malaria_prev", "Immunization"):
        t[f"{b}_source"] = np.where(t[f"{b}_share"].notna(), "WHO GHED", "")
    # fallbacks
    for b in ("HIV", "TB", "Malaria", "Malaria_prev", "Immunization"):
        have = t[t[f"{b}_share"].notna()]
        for iso in t.index[t[f"{b}_share"].isna()]:
            pool = have[have.who_region == t.loc[iso, "who_region"]]
            label = f"regional median ({t.loc[iso, 'who_region']}, n={len(pool)})"
            if len(pool) < 3:
                pool, label = have, f"median of model countries (n={len(have)})"
            t.loc[iso, f"{b}_share"] = float(pool[f"{b}_share"].median())
            t.loc[iso, f"{b}_source"] = label
    t.index.name = "iso3"
    t.reset_index().to_csv(OUT, index=False)
    pd.set_option("display.width", 250)
    for b in ("HIV", "TB", "Malaria", "Malaria_prev", "Immunization"):
        own = t[f"{b}_source"].str.startswith("WHO")
        print(f"{b}: own value {int(own.sum())} of {len(t)} (years {int(t[f'{b}_year'].min())}-{int(t[f'{b}_year'].max())}); "
              f"median {t.loc[own, f'{b}_share'].median():.2f}, IQR {t.loc[own, f'{b}_share'].quantile(.25):.2f}-{t.loc[own, f'{b}_share'].quantile(.75):.2f}")
    x = t.dropna(subset=["TB_ghed_share"])
    print(f"TB: WHO financing vs GHED dis12 external share, n {len(x)}, correlation {x.TB_share.corr(x.TB_ghed_share):.2f}, "
          f"median diff {(x.TB_share - x.TB_ghed_share).median():+.2f}")
    print(t.loc[["KEN", "NGA", "MOZ", "ZAF", "UGA", "IND", "TJK", "HND", "ZWE", "KHM"],
                ["HIV_share", "HIV_source", "TB_share", "TB_source", "Malaria_share", "Immunization_share"]].round(2).to_string())


if __name__ == "__main__":
    main()
