"""
Batch 3+4, item E (IMP-11): provider cost per TB treatment course by country, drug-susceptible (DS) and drug-resistant
(DR) separately, from the Value TB patient-level dataset (datasets/ValueTB, 2018 US$) and the other GHCC Unit Cost
Study Repository TB studies (datasets/GHCC_UCSR/GHCC_UCSR_TB.xlsx, 2020 US$), with each country's MDR/RR-TB share and
treatment enrolment from WHO (datasets/WHO_TB) and a cross-check against WHO national TB programme budgets per patient.
Read-only with respect to the model.

    .venv/bin/python audit/batch34_tb_costs.py

Value TB (codebook: unit cost per intervention = quantity of each service per patient episode x unit cost of the
service, plus drugs; tcost_USD is that total): one course = intensive phase + continuation phase (+ the inpatient
intensive phase where costed) at the same facility, for the same regimen and population.
  DS: 1st-line treatment, new and relapse, adult pulmonary TB.
  DR: 2nd-line treatment, MDR-TB, short regimen (the long regimen is the high end).
Central = financial, bottom-up; range = the four variants (financial / economic x bottom-up / top-down) across
facilities (median of each variant; the 25th-75th percentile of facilities for the central variant is also kept).
Other GHCC studies: per person treated, provider perspective, full course only (phase-only records left out).
Fallback for countries without a study: the median over the model countries with a value in the same World Bank
income group, pooled with the Laurence, Griffiths & Vassall 2015 income-group mean already in unit_cost_reference.csv
(one record each), so the fallback never rests on a single country.
Gate (batch34 rules): DS course between US$100 and US$3,000 and DR between US$1,000 and US$30,000 (2023 US$); the WHO
budget-per-patient cross-check within a factor of 3 of the blended full cost in at least half of the countries with
WHO data.
Writes audit/logic_review/batch34_tb_costs.csv.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import health_model as hm  # noqa: E402

VALUETB = ROOT / "datasets" / "ValueTB" / "ValueTB_pooled_patient.dta"
GHCC = ROOT / "datasets" / "GHCC_UCSR" / "GHCC_UCSR_TB.xlsx"
WHO_TB = ROOT / "datasets" / "WHO_TB"
OUT = ROOT / "audit" / "logic_review" / "batch34_tb_costs.csv"
VTB_ISO = {"Ethiopia": "ETH", "Georgia": "GEO", "India": "IND", "Kenya": "KEN", "Philippines": "PHL"}
GHCC_ISO = {"South Africa": "ZAF", "South Africa\xa0": "ZAF", "Nigeria": "NGA", "Nigeria\xa0": "NGA", "Brazil": "BRA",
            "Brazil\xa0": "BRA", "China": "CHN"}
DS_GATE, DR_GATE = (100.0, 3000.0), (1000.0, 30000.0)


def valuetb_courses() -> pd.DataFrame:
    d = pd.read_stata(VALUETB, convert_categoricals=False)
    d = d[d.int_class == "TB TREATMENT"].copy()
    d["iso3"] = d.fc_country.map(VTB_ISO)
    d["variant"] = d.met_FINvECON + "_" + d.met_TDvBU
    ds = d[(d.int_type == "1st Line TB Treatment") & (d.int_regimen == "New and relapse") & (d.int_pop1 == "Adult")
           & (d.int_pop3 == "PTB")]
    dr = d[(d.int_type == "2nd Line TB treatment") & (d.int_pop2 == "MDR-TB")]
    out = []
    for name, sub, by in (("DS", ds, []), ("DR", dr, ["int_regimen"])):
        key = ["iso3", "fc_code", "variant"] + by
        # one course per facility x variant (x regimen for DR): sum of the phase rows, each phase counted once
        phases = sub.groupby(key + ["int_phase"]).tcost_USD.first().reset_index()
        course = phases.groupby(key).agg(usd2018=("tcost_USD", "sum"), n_phases=("int_phase", "nunique")).reset_index()
        course = course[course.n_phases >= 2]
        course["kind"] = name
        if not by:
            course["int_regimen"] = ""
        out.append(course)
    c = pd.concat(out, ignore_index=True)
    c["usd"] = hm.inflate(c.usd2018, 2018)
    return c


def main():
    c = valuetb_courses()
    # per country: central = FIN_BU median across facilities; the other variants as the range
    rows = []
    for (iso, kind, reg), g in c.groupby(["iso3", "kind", "int_regimen"]):
        v = g.groupby("variant").usd.median()
        fb = g[g.variant == "FIN_BU"].usd
        rows.append({"iso3": iso, "kind": kind, "regimen": reg, "central": float(v.get("FIN_BU", np.nan)),
                     "variants_lo": float(v.min()), "variants_hi": float(v.max()), "fac_q25": float(fb.quantile(.25)),
                     "fac_q75": float(fb.quantile(.75)), "n_facilities": int(fb.size),
                     "source": "Value TB (Sweeney et al.), 2018 US$ x CPI-U to 2023"})
    vt = pd.DataFrame(rows)
    # other GHCC studies (full course, per person treated, provider perspective)
    g = pd.read_excel(GHCC)
    g = g[g["Reference Year"] != 2021].copy()                      # the 2021 rows are the Value TB entries
    g["uc"] = pd.to_numeric(g["Mean Unit Cost"], errors="coerce")
    g = g[g["Output unit"].isin(["Per Person Treated"]) & (g.Perspective == "Provider") & g.uc.notna()]
    g["iso3"] = g.Country.map(GHCC_ISO)
    trait = g["Sub-Studies Unique Trait(s)"].astype(str)
    full = ~trait.str.contains("phase", case=False)
    g = g[full & g.iso3.notna()].copy()
    g["kind"] = np.where(g["Target group (clinical)"].astype(str).str.contains("Multi-drug|resistant", case=False)
                         | (g["TB Drug Resistance"].astype(str).str.contains("Mdr")), "DR", "DS")
    g["usd"] = hm.inflate(g.uc, 2020)
    g["cite"] = g["All Authors"].astype(str) + " (" + g["Reference Year"].astype(str) + "): " + g["Title"].astype(str)
    oth = g.groupby(["iso3", "kind"]).agg(central=("usd", "median"), variants_lo=("usd", "min"), variants_hi=("usd", "max"),
                                          n_facilities=("usd", "size"), source=("cite", lambda s: "; ".join(sorted(set(s))[:3]) + " (GHCC UCSR, 2020 US$ x CPI-U to 2023)")).reset_index()
    oth["regimen"] = ""
    oth["fac_q25"], oth["fac_q75"] = oth.variants_lo, oth.variants_hi
    studies = pd.concat([vt, oth], ignore_index=True)

    ci = pd.read_csv(ROOT / "model_data" / "country_inputs.csv").set_index("iso3")
    lines = pd.read_csv(ROOT / "model_data" / "dah_lines.csv")
    iso_all = sorted(set(lines.iso3))
    ref = pd.read_csv(ROOT / "unit_cost_reference.csv")
    laurence = {(k.replace("tb_", "").replace("_cost", "").upper(), ig): float(v)
                for k, ig, v in zip(ref.kind, ref.key, ref.value) if k in ("tb_ds_cost", "tb_dr_cost")}

    def own(iso, kind):
        s = studies[(studies.iso3 == iso) & (studies.kind == kind)]
        if kind == "DR" and (s.regimen == "Short").any():
            s = s[s.regimen == "Short"]
        return s

    t = pd.DataFrame(index=iso_all)
    for kind, gate in (("DS", DS_GATE), ("DR", DR_GATE)):
        t[f"{kind}_own"] = [own(i, kind).central.median() if len(own(i, kind)) else np.nan for i in iso_all]
        t[f"{kind}_gate_fail"] = t[f"{kind}_own"].notna() & ~t[f"{kind}_own"].between(*gate)
        valid = t[t[f"{kind}_own"].notna() & ~t[f"{kind}_gate_fail"]]
        for iso in iso_all:
            ig = ci.loc[iso, "income_group"] if iso in ci.index else None
            ig = ig if ig in ("low_income", "lower_middle_income", "upper_middle_income") else "upper_middle_income"
            if iso in valid.index:
                s = own(iso, kind)
                t.loc[iso, f"{kind}_cost"] = s.central.median()
                lo_ = min(s.variants_lo.min(), s.fac_q25.min())
                hi_ = max(s.variants_hi.max(), s.fac_q75.max())
                if kind == "DR":
                    longr = studies[(studies.iso3 == iso) & (studies.kind == "DR") & (studies.regimen == "Long")]
                    if len(longr):
                        hi_ = max(hi_, longr.central.max())
                t.loc[iso, f"{kind}_lo"], t.loc[iso, f"{kind}_hi"] = lo_, hi_
                t.loc[iso, f"{kind}_source"] = "; ".join(s.source.unique())
            else:
                pool = list(valid.loc[[i for i in valid.index if ci.loc[i, "income_group"] == ig], f"{kind}_own"])
                pool.append(laurence[(kind, ig)])
                t.loc[iso, f"{kind}_cost"] = float(np.median(pool))
                t.loc[iso, f"{kind}_lo"], t.loc[iso, f"{kind}_hi"] = float(np.min(pool)), float(np.max(pool))
                t.loc[iso, f"{kind}_source"] = (f"median of {len(pool) - 1} model countries with studies in income group {ig} "
                                                f"pooled with the Laurence et al. 2015 {ig} mean (2023 US$)"
                                                + (" (own value outside the gate)" if t.loc[iso, f"{kind}_gate_fail"] else ""))
    # WHO MDR/RR-TB share of incidence and treatment enrolment (2024)
    m = pd.read_csv(WHO_TB / "MDR_RR_TB_burden_estimates_2026-10-14.csv")
    b = pd.read_csv(WHO_TB / "TB_burden_countries_2026-10-14.csv")
    n = pd.read_csv(WHO_TB / "TB_notifications_2026-10-14.csv",
                    usecols=["iso3", "year", "c_newinc", "conf_rrmdr_tx", "unconf_rrmdr_tx", "conf_rr_nfqr_tx",
                             "unconf_rr_nfqr_tx", "conf_rr_fqr_tx"])
    m, b, n = (x[x.year == 2024].set_index("iso3") for x in (m, b, n))
    n["rr_tx"] = n[["conf_rrmdr_tx", "unconf_rrmdr_tx", "conf_rr_nfqr_tx", "unconf_rr_nfqr_tx", "conf_rr_fqr_tx"]].sum(axis=1, min_count=1)
    t["rr_share_inc"] = m.e_inc_rr_num.reindex(iso_all) / b.e_inc_num.reindex(iso_all)
    t["rr_cov"] = (n.rr_tx.reindex(iso_all) / m.e_inc_rr_num.reindex(iso_all)).clip(upper=1.0)
    t["rr_share_notified"] = (n.rr_tx.reindex(iso_all) / n.c_newinc.reindex(iso_all)).clip(upper=1.0)
    # WHO budget per patient cross-check (nominal US$, 2025 budget; 2024 expenditure per notification as a second view)
    bud = pd.read_csv(WHO_TB / "TB_budget_2026-10-14.csv")
    bud = bud[(bud.year == 2025) & (bud.budget_tot > 0)].set_index("iso3")
    pats = bud.tx_dstb.fillna(0) + bud.tx_mdr.fillna(0)
    t["who_budget_per_patient_2025"] = (bud.budget_tot / pats.where(pats > 0)).reindex(iso_all)
    ex = pd.read_csv(WHO_TB / "TB_expenditure_utilisation_2026-10-14.csv")
    ex = ex[(ex.year == 2024) & (ex.exp_tot > 0)].set_index("iso3")
    t["who_exp_per_notified_2024"] = (ex.exp_tot.reindex(iso_all) / n.c_newinc.reindex(iso_all))
    P = hm.draw_params(hm.load_params(), 0)
    markup = 1.0 / (1.0 - float(P["asd_share"][0]))
    r = t.rr_share_notified.fillna(t.rr_share_inc).fillna(0.04)
    t["blended_full_cost"] = ((1 - r) * t.DS_cost + r * t.DR_cost) * markup
    t["ratio_budget_to_model"] = t.who_budget_per_patient_2025 / t.blended_full_cost
    t["within_factor_3"] = t.ratio_budget_to_model.between(1 / 3, 3)
    t["current_DS_cost"] = [float(hm.unit_costs(ci.loc[i], P)["tb_ds"][0] / markup) for i in iso_all]
    t["current_DR_cost"] = [float(hm.unit_costs(ci.loc[i], P)["tb_dr"][0] / markup) for i in iso_all]
    t.index.name = "iso3"
    t.reset_index().to_csv(OUT, index=False)

    pd.set_option("display.width", 250)
    print("Value TB and GHCC course costs (2023 US$):")
    print(studies[["iso3", "kind", "regimen", "central", "variants_lo", "variants_hi", "n_facilities"]].round(0).to_string())
    for kind in ("DS", "DR"):
        print(f"\n{kind}: own value for {int(t[f'{kind}_own'].notna().sum())} countries; gate failures: "
              f"{list(t.index[t[f'{kind}_gate_fail']])}; fallback for {int(t[f'{kind}_source'].str.startswith('median').sum())}")
        print(t[f"{kind}_cost"].describe().round(0).to_string())
    print(f"\nMDR/RR share of incidence: median {t.rr_share_inc.median():.3f}, min {t.rr_share_inc.min():.3f}, max {t.rr_share_inc.max():.3f}, "
          f"n {t.rr_share_inc.notna().sum()}; enrolment / RR incidence: median {t.rr_cov.median():.2f}, n {t.rr_cov.notna().sum()}")
    w = t.dropna(subset=["ratio_budget_to_model"])
    print(f"WHO 2025 budget per expected patient vs blended full cost: n {len(w)}, within factor 3: {int(w.within_factor_3.sum())} "
          f"({w.within_factor_3.mean():.0%}); median ratio {w.ratio_budget_to_model.median():.2f}")
    print(t.loc[["KEN", "NGA", "MOZ", "ZAF", "UGA", "IND", "ETH", "PHL", "TJK", "KHM"],
                ["DS_cost", "DR_cost", "current_DS_cost", "current_DR_cost", "rr_share_inc", "rr_cov", "who_budget_per_patient_2025",
                 "blended_full_cost", "ratio_budget_to_model"]].round(2).to_string())


if __name__ == "__main__":
    main()
