"""
Batch 5+6, items A2 (L-51) and A3: donor shares for the cap on the donor-funded pool. Read-only with respect to the
model; batch34_inputs.py --donor56-hiv-imm / --donor56-malaria write the columns into model_data/country_inputs.csv.

    .venv/bin/python audit/batch56_donor_share.py

A2 (L-51, HIV and immunization). The Batch 3+4 cap uses the external share of ALL-SOURCE spending on the disease
(GHED: external / total). Batch 4b found that for malaria the all-source total is dominated by household out-of-pocket
spending on treatment, which is a different service from the donor-funded one, and moved bednets and spraying to the
external share of PUBLIC spending (external / (external + domestic government)). This script reports, for every model
country with GHED data, the composition of HIV (dis11: "HIV/AIDS and other STDs") and immunization (hc62) spending:
external, domestic government, domestic private; the all-source share now used; the public share; and the gap.
Columns HIV_pub_share, Imm_pub_share carry the public share with the same WHO-region-median fallback as Batch 3+4
(audit/batch34_donor_share.py) for countries without GHED data.

A3 (malaria). Intervention-specific shares from audit/batch56_malaria_cap.py (share_specific = donor money for the
line / (people covered x the model's unit cost), capped at 1; regional median where the country has no programme-area
split). Copied here into mal_itn_share, mal_irs_share, mal_cm_share with their source.
Writes audit/logic_review/batch56_donor_share.csv.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
GHED = ROOT / "datasets" / "WHO_GHED" / "GHED_data_2026-10-14.xlsx"
EV = ROOT / "audit" / "logic_review"
OUT = EV / "batch56_donor_share.csv"
FOCUS = ["KEN", "NGA", "MOZ", "ZAF", "UGA", "IND"]


def main():
    lines = pd.read_csv(ROOT / "model_data" / "dah_lines.csv")
    iso_all = sorted(set(lines.iso3))
    ci = pd.read_csv(ROOT / "model_data" / "country_inputs.csv").set_index("iso3")
    d = pd.read_excel(GHED, sheet_name="Data", usecols=["code", "year", "dis11_usd", "dis11_ext_usd", "dis11_gghed_usd",
                                                         "dis11_pvtd_usd", "hc62_usd", "hc62_ext_usd", "hc62_gghed_usd", "hc62_pvtd_usd"])
    d = d[d.code.isin(iso_all)]
    t = pd.DataFrame(index=pd.Index(iso_all, name="iso3"))
    t["who_region"] = ci.who_region.reindex(iso_all)
    for b, tot, ext, gg, pv in (("HIV", "dis11_usd", "dis11_ext_usd", "dis11_gghed_usd", "dis11_pvtd_usd"),
                                ("Imm", "hc62_usd", "hc62_ext_usd", "hc62_gghed_usd", "hc62_pvtd_usd")):
        s = d.dropna(subset=[tot, ext])
        s = s[s[tot] > 0]
        la = s.sort_values("year").groupby("code").tail(1).set_index("code")
        t[f"{b}_year"] = la.year.reindex(iso_all)
        t[f"{b}_total_musd"], t[f"{b}_ext_musd"], t[f"{b}_gov_musd"], t[f"{b}_priv_musd"] = (la[c].reindex(iso_all) for c in (tot, ext, gg, pv))
        t[f"{b}_all_source_share"] = (t[f"{b}_ext_musd"] / t[f"{b}_total_musd"]).clip(0, 1)
        t[f"{b}_pub_share"] = (t[f"{b}_ext_musd"] / (t[f"{b}_ext_musd"] + t[f"{b}_gov_musd"].fillna(0))).clip(0, 1)
        t[f"{b}_private_share"] = t[f"{b}_priv_musd"] / t[f"{b}_total_musd"]
        t[f"{b}_pub_source"] = np.where(t[f"{b}_pub_share"].notna(), "WHO GHED: external / (external + domestic government)", "")
        have = t[t[f"{b}_pub_share"].notna()]
        for iso in t.index[t[f"{b}_pub_share"].isna()]:
            pool = have[have.who_region == t.loc[iso, "who_region"]]
            lab = f"regional median ({t.loc[iso, 'who_region']}, n={len(pool)})"
            if len(pool) < 3:
                pool, lab = have, f"median of model countries (n={len(have)})"
            t.loc[iso, f"{b}_pub_share"], t.loc[iso, f"{b}_pub_source"] = float(pool[f"{b}_pub_share"].median()), lab
    t["HIV_share_now"] = ci.donor_share_hiv.reindex(iso_all)
    t["Imm_share_now"] = ci.donor_share_imm.reindex(iso_all)
    # A3
    m = pd.read_csv(EV / "batch56_malaria_cap.csv")
    for l in ("mal_itn", "mal_irs", "mal_cm"):
        x = m[m.line == l].set_index("iso3")
        t[f"{l}_share"] = x.share_specific.reindex(iso_all)
        t[f"{l}_share_source"] = x.share_source.reindex(iso_all)
        have = t[t[f"{l}_share"].notna()]
        for iso in t.index[t[f"{l}_share"].isna()]:          # countries with no malaria deaths: regional median, unused
            pool = have[have.who_region == t.loc[iso, "who_region"]]
            if len(pool) < 3:
                pool = have
            t.loc[iso, f"{l}_share"] = float(pool[f"{l}_share"].median())
            t.loc[iso, f"{l}_share_source"] = f"no malaria deaths: regional median ({t.loc[iso, 'who_region']})"
    t.to_csv(OUT)
    pd.set_option("display.width", 300); pd.set_option("display.max_columns", 30)
    for b in ("HIV", "Imm"):
        own = t[t[f"{b}_year"].notna()]
        gap = own[f"{b}_pub_share"] - own[f"{b}_all_source_share"]
        print(f"\n{b}: GHED data for {len(own)} of {len(t)} countries (years {int(own[f'{b}_year'].min())}-{int(own[f'{b}_year'].max())}); "
              f"private share median {own[f'{b}_private_share'].median():.2f} (IQR {own[f'{b}_private_share'].quantile(.25):.2f}-{own[f'{b}_private_share'].quantile(.75):.2f}); "
              f"public minus all-source share: median {gap.median():.3f}, > 0.10 in {int((gap > 0.10).sum())} countries: {list(gap.index[gap > 0.10])}")
        cols = [f"{b}_year", f"{b}_total_musd", f"{b}_ext_musd", f"{b}_gov_musd", f"{b}_priv_musd", f"{b}_all_source_share", f"{b}_pub_share", f"{b}_private_share", f"{b}_share_now", f"{b}_pub_source"]
        print(t.loc[FOCUS, cols].round(3).to_string())
    print("\nmalaria shares (A3):", {l: round(float(t[f'{l}_share'].median()), 2) for l in ("mal_itn", "mal_irs", "mal_cm")})


if __name__ == "__main__":
    main()
