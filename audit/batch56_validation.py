"""
Batch 5+6, item VAL1 (IMP-19): like-for-like comparisons of the model with external benchmarks, with ratios and flags
(ratio above 2 or below 0.5). No model change; nothing is tuned.

    .venv/bin/python audit/batch56_validation.py

Benchmarks (all local files, datasets/MANIFEST.md):
  HIV: ten Brink et al. 2025 (Optima HIV) appendix Table C2, p. 11: cumulative 2025-2030 new infections and HIV-related
       deaths, scenario 5 (PEPFAR discontinued, no mitigation) minus scenario 1 (status quo), for the 15 Optima countries
       the dashboard models; UNAIDS AIDSinfo 2026 estimates, People receiving antiretroviral therapy, all ages, 2025.
  TB:  WHO Global TB Programme, TB_burden_countries (e_mort_num 2024), TB_notifications (c_newinc 2024), TB_budget
       (budget_tot 2025).
  Malaria: WHO World Malaria Report 2025 estimates (GHO MALARIA_EST_DEATHS, 2024; ext_data/gho).
  Vaccines: Toor et al. 2021 Table 3 (deaths averted per 1,000 FVPs), via audit/logic_review/batch56_vaccines.csv.
Writes audit/logic_review/validation_tables.csv (every row) and prints the markdown tables used in validation.md.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
logging.disable(logging.WARNING)
import health_model as hm  # noqa: E402
import scenarios as scn  # noqa: E402

PRESET = "Full US exit"
OUT = ROOT / "audit" / "logic_review" / "validation_tables.csv"
# ten Brink et al. 2025 appendix Table C2 (p. 11), cumulative 2025-2030: (infections S1, infections S5, deaths S1, deaths S5)
OPTIMA_C2 = {"AZE": (1880, 2960, 1190, 1510), "KHM": (8400, 23390, 2570, 5500), "CIV": (50630, 117910, 47190, 92500),
             "DOM": (13270, 36200, 5380, 11040), "SWZ": (14070, 133500, 4030, 19660), "KEN": (162990, 350880, 70790, 146740),
             "KGZ": (1840, 4890, 990, 1610), "MWI": (56210, 476750, 19880, 147540), "MDA": (2490, 3430, 1960, 2520),
             "MNG": (290, 340, 140, 150), "MOZ": (411590, 1359390, 140710, 405710), "ZAF": (671620, 3062640, 251450, 743200),
             "TJK": (1910, 2320, 1250, 1380), "UGA": (246980, 828160, 110270, 310850), "ZWE": (33730, 358000, 20420, 153680)}
TOOR_T3 = {"Measles": 6.5, "HepB": 7.7, "YF": 2.1, "Hib": 2.4, "PCV": 2.3, "Rubella": 0.3, "Rota": 0.8, "MenA": 1.0}


def flag(r):
    return "" if pd.isna(r) else ("FLAG >2" if r > 2 else "FLAG <0.5" if r < 0.5 else "ok")


def md(df, cols, fmt):
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(fmt[c](r[c]) if c in fmt else str(r[c]) for c in cols) + " |")
    return "\n".join(out)


def main():
    I, P = hm.load_inputs(), hm.load_params()
    ci = I["ci"]
    isos = [c for c in ci.index if c in set(I["lines"].iso3)]
    sc = scn.build_scenario(PRESET, scn.default_opts(PRESET, ci), ci)
    A = pd.read_csv(scn.precomputed_path(hm.MODEL_DIR, PRESET)).set_index("iso3")
    runs = {iso: hm.run_country(iso, sc, hm.Fiscal(*scn.DEFAULT_FISCAL), I, P, n_draws=0) for iso in isos}
    L = {iso: r["lines"].set_index("line") for iso, r in runs.items()}
    rows = []

    # ---- HIV vs Optima C2 ----
    hiv = []
    for iso, (i1, i5, d1, d5) in OPTIMA_C2.items():
        if iso not in A.index:
            continue
        m_d, m_i = float(A.loc[iso, "deaths_5y_HIV"]), float(A.loc[iso, "hiv_infections_5y"])
        hiv.append({"iso3": iso, "model_hiv_deaths_2026_30": m_d, "optima_excess_deaths_2025_30": d5 - d1, "ratio_deaths": m_d / (d5 - d1),
                    "model_hiv_infections_2026_30": m_i, "optima_excess_infections_2025_30": i5 - i1, "ratio_infections": m_i / (i5 - i1)})
    hiv = pd.DataFrame(hiv)
    hiv["flag_deaths"], hiv["flag_infections"] = hiv.ratio_deaths.map(flag), hiv.ratio_infections.map(flag)
    tot = {"iso3": "15 countries", "model_hiv_deaths_2026_30": hiv.model_hiv_deaths_2026_30.sum(), "optima_excess_deaths_2025_30": hiv.optima_excess_deaths_2025_30.sum(),
           "model_hiv_infections_2026_30": hiv.model_hiv_infections_2026_30.sum(), "optima_excess_infections_2025_30": hiv.optima_excess_infections_2025_30.sum()}
    tot["ratio_deaths"] = tot["model_hiv_deaths_2026_30"] / tot["optima_excess_deaths_2025_30"]
    tot["ratio_infections"] = tot["model_hiv_infections_2026_30"] / tot["optima_excess_infections_2025_30"]
    tot["flag_deaths"], tot["flag_infections"] = flag(tot["ratio_deaths"]), flag(tot["ratio_infections"])
    hiv = pd.concat([hiv, pd.DataFrame([tot])], ignore_index=True)
    for _, r in hiv.iterrows():
        rows.append({"section": "HIV vs Optima C2", **r.to_dict()})
    n0 = lambda v: f"{v:,.0f}"  # noqa: E731
    r2 = lambda v: f"{v:.2f}"  # noqa: E731
    print("### HIV: model Full US Exit 2026-2030 vs Optima Table C2 (scenario 5 minus status quo, 2025-2030)\n")
    print(md(hiv, ["iso3", "model_hiv_deaths_2026_30", "optima_excess_deaths_2025_30", "ratio_deaths", "flag_deaths", "model_hiv_infections_2026_30", "optima_excess_infections_2025_30", "ratio_infections", "flag_infections"],
             {"model_hiv_deaths_2026_30": n0, "optima_excess_deaths_2025_30": n0, "ratio_deaths": r2, "model_hiv_infections_2026_30": n0, "optima_excess_infections_2025_30": n0, "ratio_infections": r2}))

    # ---- people on ART vs UNAIDS ----
    u = pd.read_csv(ROOT / "datasets" / "UNAIDS_2026" / "UNAIDS_Estimates_2026.csv", low_memory=False,
                    usecols=["Indicator", "Subgroup", "Area ID", "Area Level", "Time Period", "Data value"])
    u = u[(u["Area Level"] == 2) & (u.Indicator == "People receiving antiretroviral therapy") & (u.Subgroup == "All ages")]
    u["Data value"] = pd.to_numeric(u["Data value"], errors="coerce")
    u = u.dropna(subset=["Data value"]).sort_values("Time Period").groupby("Area ID").tail(1).set_index("Area ID")
    art = []
    for iso in isos:
        row = L[iso].loc["hiv_art"]
        covered = row.cov0 * row.need if row.need == row.need and row.cov0 == row.cov0 else np.nan
        if iso in u.index and covered == covered and covered > 0:
            art.append({"iso3": iso, "model_people_on_art_outside_pmtct": covered, "unaids_people_on_art": float(u.loc[iso, "Data value"]),
                        "unaids_year": int(u.loc[iso, "Time Period"]), "ratio": covered / float(u.loc[iso, "Data value"]),
                        "model_people_who_stop_art_per_year": row.units_lost, "stop_share_of_unaids": row.units_lost / float(u.loc[iso, "Data value"])})
    art = pd.DataFrame(art)
    art["flag"] = art.ratio.map(flag)
    for _, r in art.iterrows():
        rows.append({"section": "People on ART vs UNAIDS", **r.to_dict()})
    print("\n### People on ART: model (ART coverage x PLHIV, outside PMTCT) vs UNAIDS 2026 estimates (people receiving ART, all ages)\n")
    print(f"{len(art)} countries; ratio median {art.ratio.median():.2f}, flagged: {art[art.flag.str.startswith('FLAG')].iso3.tolist()}; "
          f"people who stop ART (Full US Exit) as a share of UNAIDS people on ART: median {art.stop_share_of_unaids.median():.2f}, max {art.stop_share_of_unaids.max():.2f} ({art.loc[art.stop_share_of_unaids.idxmax(), 'iso3']})\n")
    print(md(art[art.flag.str.startswith("FLAG") | art.iso3.isin(["KEN", "NGA", "MOZ", "ZAF", "UGA", "IND"])], ["iso3", "model_people_on_art_outside_pmtct", "unaids_people_on_art", "unaids_year", "ratio", "flag", "model_people_who_stop_art_per_year", "stop_share_of_unaids"],
             {"model_people_on_art_outside_pmtct": n0, "unaids_people_on_art": n0, "ratio": r2, "model_people_who_stop_art_per_year": n0, "stop_share_of_unaids": r2}))

    # ---- TB ----
    b = pd.read_csv(ROOT / "datasets" / "WHO_TB" / "TB_burden_countries_2026-10-14.csv")
    b = b[b.year == 2024].set_index("iso3")
    n = pd.read_csv(ROOT / "datasets" / "WHO_TB" / "TB_notifications_2026-10-14.csv", usecols=["iso3", "year", "c_newinc"])
    n = n[n.year == 2024].set_index("iso3")
    bu = pd.read_csv(ROOT / "datasets" / "WHO_TB" / "TB_budget_2026-10-14.csv", usecols=["iso3", "year", "budget_tot"])
    bu = bu[bu.year == 2025].set_index("iso3")
    cpi = hm.CPI_U[2023] / hm.CPI_U[2023]   # WHO budgets are nominal 2025 US$; shown as reported (no CPI for 2025 in the table)
    tb = []
    for iso in isos:
        ds, dr = L[iso].loc["tb_ds"], L[iso].loc["tb_dr"]
        tb_d = float(A.loc[iso, "deaths_5y_TB"]) if iso in A.index else np.nan
        who_d = float(b.e_mort_num.get(iso, np.nan))
        treated = ds.cov0 * ds.need if ds.need == ds.need and ds.cov0 == ds.cov0 else np.nan
        notif = float(n.c_newinc.get(iso, np.nan))
        budget = float(bu.budget_tot.get(iso, np.nan))
        # blended full cost per patient (DS and DR weighted by the model's patients covered)
        dr_cov = dr.cov0 * dr.need if dr.need == dr.need and dr.cov0 == dr.cov0 else 0.0
        blended = (ds.unit_cost * treated + dr.unit_cost * dr_cov) / (treated + dr_cov) if treated and treated > 0 else np.nan
        tb.append({"iso3": iso, "model_tb_excess_deaths_per_year": tb_d / 5, "who_tb_deaths_2024": who_d, "share_of_current_tb_deaths": tb_d / 5 / who_d if who_d else np.nan,
                   "model_tb_patients_treated": treated, "who_notifications_2024": notif, "ratio_treated_vs_notified": treated / notif if notif else np.nan,
                   "model_blended_full_cost_per_patient_2023usd": blended, "who_budget_2025_per_notified_patient": budget / notif if notif and budget == budget else np.nan,
                   "ratio_cost_vs_budget": blended / (budget / notif) if notif and budget == budget and budget > 0 else np.nan})
    tb = pd.DataFrame(tb)
    tb["flag_share"] = np.where(tb.share_of_current_tb_deaths > 1, "FLAG excess > current deaths", np.where(tb.share_of_current_tb_deaths > 0.5, "note > 0.5", "ok"))
    tb["flag_treated"], tb["flag_cost"] = tb.ratio_treated_vs_notified.map(flag), tb.ratio_cost_vs_budget.map(flag)
    for _, r in tb.iterrows():
        rows.append({"section": "TB", **r.to_dict()})
    print("\n### TB\n")
    print(f"excess TB deaths a year as a share of WHO 2024 TB deaths: median {tb.share_of_current_tb_deaths.median():.3f}; above 0.5: {tb[tb.share_of_current_tb_deaths > 0.5].iso3.tolist()}; above 1: {tb[tb.share_of_current_tb_deaths > 1].iso3.tolist()}")
    print(f"patients treated vs notifications: median {tb.ratio_treated_vs_notified.median():.2f}; flagged: {tb[tb.flag_treated.str.startswith('FLAG')].iso3.tolist()}")
    print(f"blended full cost per patient vs WHO 2025 budget per notified patient: median {tb.ratio_cost_vs_budget.median():.2f}; flagged <0.5: {tb[tb.flag_cost == 'FLAG <0.5'].iso3.tolist()}; flagged >2: {tb[tb.flag_cost == 'FLAG >2'].iso3.tolist()}\n")
    sel = tb[tb.iso3.isin(["KEN", "NGA", "MOZ", "ZAF", "UGA", "IND"]) | (tb.share_of_current_tb_deaths > 0.5) | tb.flag_cost.str.startswith("FLAG")]
    print(md(sel, ["iso3", "model_tb_excess_deaths_per_year", "who_tb_deaths_2024", "share_of_current_tb_deaths", "flag_share", "model_tb_patients_treated", "who_notifications_2024", "ratio_treated_vs_notified", "model_blended_full_cost_per_patient_2023usd", "who_budget_2025_per_notified_patient", "ratio_cost_vs_budget", "flag_cost"],
             {"model_tb_excess_deaths_per_year": n0, "who_tb_deaths_2024": n0, "share_of_current_tb_deaths": r2, "model_tb_patients_treated": n0, "who_notifications_2024": n0, "ratio_treated_vs_notified": r2, "model_blended_full_cost_per_patient_2023usd": n0, "who_budget_2025_per_notified_patient": n0, "ratio_cost_vs_budget": r2}))

    # ---- malaria ----
    mal = []
    for iso in isos:
        d0 = float(ci.loc[iso, "malaria_deaths"])
        if not d0 > 0:
            continue
        m = float(A.loc[iso, "deaths_5y_Malaria"]) if iso in A.index else np.nan
        mal.append({"iso3": iso, "model_malaria_excess_deaths_per_year": m / 5, "who_malaria_deaths_2024": d0, "share_of_current_malaria_deaths": m / 5 / d0})
    mal = pd.DataFrame(mal)
    mal["flag"] = np.where(mal.share_of_current_malaria_deaths > 1, "FLAG excess > current deaths", np.where(mal.share_of_current_malaria_deaths > 0.5, "note > 0.5", "ok"))
    for _, r in mal.iterrows():
        rows.append({"section": "Malaria", **r.to_dict()})
    print("\n### Malaria\n")
    print(f"{len(mal)} countries; share median {mal.share_of_current_malaria_deaths.median():.3f}, max {mal.share_of_current_malaria_deaths.max():.2f} ({mal.loc[mal.share_of_current_malaria_deaths.idxmax(), 'iso3']}); above 0.5: {mal[mal.share_of_current_malaria_deaths > 0.5].iso3.tolist()}\n")
    print(md(mal.sort_values("share_of_current_malaria_deaths", ascending=False).head(10), ["iso3", "model_malaria_excess_deaths_per_year", "who_malaria_deaths_2024", "share_of_current_malaria_deaths", "flag"],
             {"model_malaria_excess_deaths_per_year": n0, "who_malaria_deaths_2024": n0, "share_of_current_malaria_deaths": r2}))

    # ---- vaccines vs Toor Table 3 ----
    v = pd.read_csv(ROOT / "audit" / "logic_review" / "batch56_vaccines.csv")
    v = v[v.model_country & v.included & v.gate_pass.notna()].copy()
    v["ratio_vs_toor"] = v.final_dpc * 1000 / v.disease.map(TOOR_T3)
    v["flag"] = v.ratio_vs_toor.map(flag)
    vs = v.groupby("disease").agg(countries=("iso3", "size"), model_per_1000_median=("final_dpc", lambda s: s.median() * 1000),
                                  toor_per_1000=("disease", lambda s: TOOR_T3[s.iloc[0]]), ratio_median=("ratio_vs_toor", "median"),
                                  flagged_above_2=("flag", lambda s: (s == "FLAG >2").sum()), flagged_below_half=("flag", lambda s: (s == "FLAG <0.5").sum())).reset_index()
    for _, r in vs.iterrows():
        rows.append({"section": "Vaccines vs Toor Table 3", **r.to_dict()})
    print("\n### Vaccines: deaths averted per 1,000 fully immunized children vs Toor et al. 2021 Table 3 (per 1,000 FVPs)\n")
    print(md(vs, ["disease", "countries", "model_per_1000_median", "toor_per_1000", "ratio_median", "flagged_above_2", "flagged_below_half"],
             {"model_per_1000_median": r2, "ratio_median": r2}))
    fl = v[v.flag.str.startswith("FLAG")]
    print("\nflagged country-antigen values (after the V1 gate; these are within 0.1-10x but outside 0.5-2x):", fl.groupby("disease").iso3.apply(list).to_dict())

    # ---- UNAIDS year for the transmission rate ----
    yr = ci.loc[isos, "art_transmission_year"].value_counts(dropna=False).sort_index()
    print("\n### UNAIDS year used for each country's HIV transmission rate\n")
    print(yr.to_dict())
    print({y: ci.loc[isos][ci.loc[isos, "art_transmission_year"] == y].index.tolist() for y in yr.index if y != 2025})
    print("regional median (no own rate):", ci.loc[isos][ci.loc[isos, "art_transmission_source"].str.startswith("regional")].index.tolist())

    pd.DataFrame(rows).to_csv(OUT, index=False)


if __name__ == "__main__":
    main()
