"""
Batch 3+4, item B (L-43): how donor money for each disease splits between treatment, prevention, testing, systems
(RSSH) and programme management, by country, from Global Fund grant budgets (GC7 2023-2025, fallback GC6 2020-2022),
cross-checked against Global Fund expenditures and WHO TB programme budget lines. Read-only with respect to the model.

    .venv/bin/python audit/batch34_gf_shares.py

Writes audit/logic_review/batch34_gf_shares.csv (one row per model country x disease: the five shares, the source
cycle, the expenditure cross-check shares and, for TB, the WHO budget-line shares) and prints a summary.

Module mapping (Global Fund modular framework names as they appear in the data):
  HIV:     treatment = "Treatment, care and support"; testing = "Differentiated HIV Testing Services";
           prevention = every "Prevention ..." / "Comprehensive prevention ..." module, "PMTCT" and "Elimination of
           vertical transmission ..."; "Reducing human rights-related barriers ..." -> programme management/other.
  TB:      treatment (= the model's TB line, which is IHME diagnosis + treatment money) = "TB diagnosis, treatment and
           care", "TB care and prevention", "MDR-TB", "Drug-resistant (DR)-TB diagnosis, treatment and care";
           testing/case finding = "Key and vulnerable populations (KVP) - TB/DR-TB", "Collaboration with other
           providers and sectors", "TB/HIV"; prevention = "TB/DR-TB Prevention"; human rights -> programme management.
  Malaria: treatment = "Case management"; prevention = "Vector control", "Specific prevention interventions (SPI)".
  RSSH:    every "RSSH..." module.  Programme management: "Program management". "Payment for results" rows (results-based
           disbursements that are not tagged by purpose: India, Rwanda, Dominican Republic) are left out of the
           shares; negative budget adjustments are clipped at 0.
Multi-component (programme management, payment for results) and RSSH modules are not disease-specific: within each
grant they are allocated to the grant's diseases in proportion to the grant's disease-module budgets; standalone RSSH
grants are allocated across the country's diseases in proportion to the country's disease-module budgets.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
GF = ROOT / "datasets" / "GlobalFund"
WHO_TB = ROOT / "datasets" / "WHO_TB"
OUT = ROOT / "audit" / "logic_review" / "batch34_gf_shares.csv"

NAMES = {'Angola': 'AGO', 'Azerbaijan': 'AZE', 'Bangladesh': 'BGD', 'Belize': 'BLZ', 'Benin': 'BEN',
         'Bolivia (Plurinational State)': 'BOL', 'Botswana': 'BWA', 'Burkina Faso': 'BFA', 'Burundi': 'BDI',
         'Cambodia': 'KHM', 'Cameroon': 'CMR', 'Central African Republic': 'CAF', "Côte d'Ivoire": 'CIV',
         'Congo (Democratic Republic)': 'COD', 'Djibouti': 'DJI', 'Dominican Republic': 'DOM', 'Egypt': 'EGY',
         'El Salvador': 'SLV', 'Eswatini': 'SWZ', 'Ethiopia': 'ETH', 'Gambia': 'GMB', 'Ghana': 'GHA',
         'Guatemala': 'GTM', 'Guinea': 'GIN', 'Guyana': 'GUY', 'Haiti': 'HTI', 'Honduras': 'HND', 'India': 'IND',
         'Indonesia': 'IDN', 'Jamaica': 'JAM', 'Kenya': 'KEN', 'Kyrgyzstan': 'KGZ',
         'Lao (Peoples Democratic Republic)': 'LAO', 'Lesotho': 'LSO', 'Liberia': 'LBR', 'Madagascar': 'MDG',
         'Malawi': 'MWI', 'Mali': 'MLI', 'Mauritius': 'MUS', 'Moldova': 'MDA', 'Mongolia': 'MNG',
         'Mozambique': 'MOZ', 'Namibia': 'NAM', 'Nepal': 'NPL', 'Nicaragua': 'NIC', 'Niger': 'NER',
         'Nigeria': 'NGA', 'Pakistan': 'PAK', 'Panama': 'PAN', 'Papua New Guinea': 'PNG', 'Philippines': 'PHL',
         'Rwanda': 'RWA', 'Sao Tome and Principe': 'STP', 'Senegal': 'SEN', 'Sierra Leone': 'SLE', 'Somalia': 'SOM',
         'South Africa': 'ZAF', 'South Sudan': 'SSD', 'Tajikistan': 'TJK', 'Tanzania (United Republic)': 'TZA',
         'Timor-Leste': 'TLS', 'Togo': 'TGO', 'Uganda': 'UGA', 'Venezuela (Bolivarian Republic)': 'VEN',
         'Viet Nam': 'VNM', 'Zambia': 'ZMB', 'Zimbabwe': 'ZWE'}
DISEASE = {"HIV/AIDS": "HIV", "Tuberculosis": "TB", "Malaria": "Malaria"}
CATS = ["treatment", "prevention", "testing", "rssh", "pm"]


def category(component: str, module: str) -> str:
    m = module or ""
    if component == "RSSH" or m.startswith("RSSH"):
        return "rssh"
    if m == "Program management" or component == "Multi-Component":
        return "pm"
    if component == "HIV/AIDS":
        if m == "Treatment, care and support":
            return "treatment"
        if m == "Differentiated HIV Testing Services":
            return "testing"
        if "human rights" in m:
            return "pm"
        return "prevention"            # every prevention package, PMTCT, vertical transmission
    if component == "Tuberculosis":
        if m in ("TB diagnosis, treatment and care", "TB care and prevention", "MDR-TB",
                 "Drug-resistant (DR)-TB diagnosis, treatment and care"):
            return "treatment"
        if m in ("Key and vulnerable populations (KVP) - TB/DR-TB", "Collaboration with other providers and sectors",
                 "TB/HIV"):
            return "testing"
        if m == "TB/DR-TB Prevention":
            return "prevention"
        return "pm"                    # human rights and gender barriers
    if component == "Malaria":
        return "treatment" if m == "Case management" else "prevention"
    return "pm"


def allocate(df: pd.DataFrame, grant_col: str, module_component: str, module: str, amount: str) -> pd.DataFrame:
    """Rows -> (iso3, disease, category, amount) with non-disease modules spread over the grant's diseases."""
    df = df.copy()
    df["cat"] = [category(c, m) for c, m in zip(df[module_component], df[module])]
    df["disease"] = df[module_component].map(DISEASE)
    out = []
    for (iso, grant), g in df.groupby(["iso3", grant_col]):
        dis = g[g.disease.notna()].groupby("disease")[amount].sum()
        dis = dis[dis > 0]
        nondis = g[g.disease.isna()]
        if len(dis):
            w = dis / dis.sum()
        else:
            w = None
        for r in g[g.disease.notna()].itertuples():
            out.append((iso, r.disease, r.cat, getattr(r, amount)))
        for r in nondis.itertuples():
            if w is not None:
                for d, wd in w.items():
                    out.append((iso, d, r.cat, getattr(r, amount) * wd))
            else:
                out.append((iso, "UNALLOCATED", r.cat, getattr(r, amount)))
    o = pd.DataFrame(out, columns=["iso3", "disease", "cat", "amt"])
    # standalone RSSH / multicomponent grants with no disease module: spread over the country's diseases
    un = o[o.disease == "UNALLOCATED"]
    o = o[o.disease != "UNALLOCATED"]
    if len(un):
        cw = o.groupby(["iso3", "disease"]).amt.sum()
        rows = []
        for r in un.itertuples():
            w = cw.loc[r.iso3] if r.iso3 in cw.index.get_level_values(0) else None
            if w is None or w.sum() <= 0:
                continue
            for d, wd in (w / w.sum()).items():
                rows.append((r.iso3, d, r.cat, r.amt * wd))
        o = pd.concat([o, pd.DataFrame(rows, columns=o.columns)], ignore_index=True)
    return o


def shares(o: pd.DataFrame) -> pd.DataFrame:
    t = o.groupby(["iso3", "disease", "cat"]).amt.sum().unstack("cat").reindex(columns=CATS).fillna(0.0)
    t = t[t.sum(axis=1) > 0]
    return t.div(t.sum(axis=1), axis=0)


def main():
    lines = pd.read_csv(ROOT / "model_data" / "dah_lines.csv")
    ci = pd.read_csv(ROOT / "model_data" / "country_inputs.csv").set_index("iso3")
    model_iso = sorted(set(lines.iso3))
    b = pd.read_csv(GF / "GF_budgets_2026-10-14.csv",
                    usecols=["GeographyName1", "Grant1", "GrantComponent1", "GrantCycle1", "ModuleComponent1", "Module1",
                             "BudgetAmount_ReferenceRate"])
    b = b[b.GeographyName1.isin(NAMES)].copy()
    b["iso3"] = b.GeographyName1.map(NAMES)
    b["ModuleComponent1"] = b["ModuleComponent1"].fillna("")
    b["Module1"] = b["Module1"].fillna("")
    b = b[b.Module1 != "Payment for results"]
    b["BudgetAmount_ReferenceRate"] = b["BudgetAmount_ReferenceRate"].clip(lower=0)
    cycles = {}
    for cyc in ("2023-2025", "2020-2022"):
        o = allocate(b[b.GrantCycle1 == cyc], "Grant1", "ModuleComponent1", "Module1", "BudgetAmount_ReferenceRate")
        cycles[cyc] = shares(o)
        cycles[cyc + "_usd"] = o.groupby(["iso3", "disease"]).amt.sum()
    # expenditure cross-check: latest reported annual expenditure by module, GC6 and GC7 (cumulative rows exist only
    # for GC5)
    e = pd.read_csv(GF / "GF_expenditures_modules_2026-10-14.csv",
                    usecols=["GeographyName1", "Grant1", "GrantCycle1", "ModuleComponent", "Module", "IsLatestReported",
                             "IsCumulative", "ExpenditureAmount_ReferenceRate"])
    e = e[e.GeographyName1.isin(NAMES) & (e.IsLatestReported == True) & (e.IsCumulative == False)].copy()  # noqa: E712
    e["iso3"] = e.GeographyName1.map(NAMES)
    e["ModuleComponent"] = e["ModuleComponent"].fillna("")
    e["Module"] = e["Module"].fillna("")
    e = e[~e.ModuleComponent.isin(["Ungrouped Components", ""]) & (e.Module != "Payment for results")]
    e = e[e.GrantCycle1.isin(["2020-2022", "2023-2025"])]
    e["ExpenditureAmount_ReferenceRate"] = e["ExpenditureAmount_ReferenceRate"].clip(lower=0)
    exp_sh = shares(allocate(e, "Grant1", "ModuleComponent", "Module", "ExpenditureAmount_ReferenceRate"))

    # WHO TB budget lines (2025 budget; 2024 if missing): treatment = first- and second-line drugs, DS and DR programme
    # costs, patient support; testing/other = lab, TB/HIV; prevention = TPT; systems/management = staff, operational
    # research, other
    tb = pd.read_csv(WHO_TB / "TB_budget_2026-10-14.csv")
    tb = tb[tb.iso3.isin(model_iso)]
    tb = tb[tb.budget_tot > 0].sort_values("year").groupby("iso3").tail(1).set_index("iso3")
    who = pd.DataFrame({
        "who_treatment": tb[["budget_fld", "budget_prog", "budget_sld", "budget_mdrmgt", "budget_patsup"]].sum(axis=1, min_count=1),
        "who_testing": tb[["budget_lab", "budget_tbhiv"]].sum(axis=1, min_count=1),
        "who_prevention": tb["budget_tpt"].fillna(0),
        "who_staff_other": tb[["budget_staff", "budget_orsrvy", "budget_oth"]].sum(axis=1, min_count=1),
        "who_year": tb["year"]})
    tot = who[["who_treatment", "who_testing", "who_prevention", "who_staff_other"]].sum(axis=1)
    for c in ("who_treatment", "who_testing", "who_prevention", "who_staff_other"):
        who[c] = who[c] / tot

    rows = []
    for iso in model_iso:
        for d in ("HIV", "TB", "Malaria"):
            base = lines[(lines.iso3 == iso) & (lines.bucket == d)].usd.sum()
            rec = {"iso3": iso, "disease": d, "who_region": ci.loc[iso, "who_region"] if iso in ci.index else "",
                   "ihme_base_usd": base, "ihme_unspec_usd": lines[(lines.iso3 == iso) & (lines.line == {"HIV": "hiv_unspec", "TB": "tb_unspec", "Malaria": "mal_unspec"}[d])].usd.sum()}
            src = ""
            for cyc in ("2023-2025", "2020-2022"):
                sh = cycles[cyc]
                if (iso, d) in sh.index and cycles[cyc + "_usd"].get((iso, d), 0) >= 1e6:
                    for c in CATS:
                        rec[c] = float(sh.loc[(iso, d), c])
                    rec["gf_budget_usd"] = float(cycles[cyc + "_usd"].loc[(iso, d)])
                    src = f"GF budgets {cyc}"
                    break
            rec["source"] = src
            if (iso, d) in exp_sh.index:
                for c in CATS:
                    rec["exp_" + c] = float(exp_sh.loc[(iso, d), c])
            if d == "TB" and iso in who.index:
                rec.update(who.loc[iso].to_dict())
            rows.append(rec)
    t = pd.DataFrame(rows)
    # regional median fallback (WHO region of the model countries with Global Fund data; overall median if none)
    have = t[t.source != ""]
    for i, r in t[t.source == ""].iterrows():
        pool = have[(have.disease == r.disease) & (have.who_region == r.who_region)]
        label = f"regional median ({r.who_region})"
        if len(pool) < 3:
            pool = have[have.disease == r.disease]
            label = "median of model countries"
        med = pool[CATS].median()
        med = med / med.sum()
        for c in CATS:
            t.loc[i, c] = float(med[c])
        t.loc[i, "source"] = label
    t.to_csv(OUT, index=False)

    pd.set_option("display.width", 250)
    print(f"model countries: {len(model_iso)}; country-disease lines: {len(t)}")
    print(t.source.value_counts().to_string())
    print("\nmedian shares by disease (Global Fund budgets):")
    print(have.groupby("disease")[CATS].median().round(3).to_string())
    print("\nmedian shares by disease (Global Fund expenditures, cross-check):")
    print(t.groupby("disease")[["exp_" + c for c in CATS]].median().round(3).to_string())
    print("\nTB: WHO budget-line shares (median):")
    print(t[t.disease == "TB"][["who_treatment", "who_testing", "who_prevention", "who_staff_other"]].median().round(3).to_string())
    bad = t[(t.treatment < 0.05) | (t.treatment > 0.95)]
    print(f"\ntreatment share outside 0.05-0.95: {len(bad)}")
    print(bad[["iso3", "disease", "treatment", "source"]].to_string())
    s = t[CATS].sum(axis=1)
    print(f"shares sum to 1: max |sum-1| = {float((s - 1).abs().max()):.2e}")
    d = (t.treatment - t.exp_treatment).abs()
    print(f"budget vs expenditure treatment share: median |diff| {d.median():.3f}, 90th pct {d.quantile(.9):.3f}, n {d.notna().sum()}")
    tbx = t[t.disease == "TB"].dropna(subset=["who_treatment"])
    print(f"TB: GF treatment share vs WHO budget-line treatment share: median {tbx.treatment.median():.3f} vs {tbx.who_treatment.median():.3f}; "
          f"correlation {tbx.treatment.corr(tbx.who_treatment):.2f} (n {len(tbx)})")
    print("\nfocus countries:")
    print(t[t.iso3.isin(["KEN", "NGA", "MOZ", "ZAF", "UGA", "IND", "TJK", "KHM"])][["iso3", "disease"] + CATS + ["exp_treatment", "who_treatment", "source"]].round(3).to_string())


if __name__ == "__main__":
    main()
