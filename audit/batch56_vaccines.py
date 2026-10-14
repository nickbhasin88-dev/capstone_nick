"""
Batch 5+6, item V1 (L-42, L-18): deaths averted per vaccinated child by country and antigen from the Vaccine Impact
Modelling Consortium estimates (Toor et al. 2021, eLife 10:e67635; datasets/Toor2021), WUENIC 2025 coverage and WPP
2024 denominators; the timing of those deaths by years since vaccination; gates. Read-only with respect to the model;
batch34_inputs.py --vaccines writes the country values into model_data/country_inputs.csv (item V2).

    .venv/bin/python audit/batch56_vaccines.py

1. Scope: routine infant vaccines in the cost per fully immunized child. HPV is excluded (adolescent vaccine, girls
   9-14; not part of the infant schedule or of uc_imm). VIMC disease -> WUENIC antigen (coverage denominator per
   WUENIC: surviving infants for every antigen used here; the HepB birth dose, hepbb, uses live births and is reported
   but not used as a denominator because the same child is counted by hepb3):
   HepB -> hepb3; Hib -> hib3; PCV -> pcvc (PCV final dose); Rota -> rotac (rotavirus last dose); Measles -> mcv1
   (MCV2 is a second dose to the same children); Rubella -> rcv1; YF -> yfv; MenA -> menga. JE has no WUENIC antigen
   in the 2025 file and cannot be mapped: excluded and listed.
2. Denominator: vaccinated children in year y = WUENIC coverage(y) x WPP 2024 LBsurvivingAge1(y) (thousands x 1000).
3. Deaths averted per vaccinated child = VIMC year_of_vac deaths averted(y) / vaccinated(y), mean over 2015-2019 (the
   vaccination years VIMC based on reported WUENIC coverage: Toor et al. 2021, Methods, "past RI coverage (1980-2018)
   was obtained from WUENIC"; 2019-2030 are forecasts). Range: the deaths_av_lo / deaths_av_hi columns (95% CrI).
4. Mortality trend adjustment (labelled): value x [mean WPP Q5 2026-2030 / mean WPP Q5 2015-2019] of the country.
5. Routine vs campaign: the VIMC files do not separate routine from campaign vaccination (one row per disease-year;
   Toor et al. attribute both RI and NRI to the year of vaccination). For measles, MenA and YF the per-child value is
   therefore the MINIMUM over 2015-2019 (a year without a campaign is closest to the routine-only value); the mean /
   minimum ratio is reported as the campaign inflation. Conservative, labelled.
6. DTP (pertussis, tetanus, diphtheria), polio and BCG are not in VIMC; no citable per-vaccinated-child value by
   country or region was found (Shattock et al. 2024, Lancet, report global and regional deaths averted by pathogen
   over 1974-2024 without per-child values), so they are excluded and the dashboard says so.
7. Timing: the distribution of deaths averted by years since vaccination is estimated per pathogen by non-negative
   least squares, pooling all VIMC countries and calendar years 2000-2019: under-5 deaths averted in calendar year y
   (cross_section file, age_group under5) = sum over k = 0..4 of (under-5 lifetime deaths averted of the birth cohort
   y - k, cohort file) x v_k. The under-5 share of a pathogen's lifetime deaths averted is country-specific (cohort
   file, under5 / all, cohorts 2015-2019). Years 5-9 since vaccination: the same fit on all-age deaths with lags
   0-11 where it explains the data (R2 >= 0.9: measles, HepB); where it does not (MenA, YF) the deaths at ages 5 and
   over are counted as lifetime deaths beyond the model's window (labelled assumption, conservative).
GATE: each country-antigen value (adjusted, per 1,000 vaccinated) must be within 0.1x-10x of the Toor 2021 Table 3
deaths averted per 1,000 FVPs for that disease; outliers take the WHO-region median of the passing countries and are
listed. Countries not in VIMC (Botswana, Dominican Republic, Libya, Mauritius) take the regional median per antigen.
Writes audit/logic_review/batch56_vaccines.csv (country x antigen), batch56_vaccine_timing.csv (pathogen x lag) and
batch56_vaccine_country.csv (one row per model country, consumed by batch34_inputs.py --vaccines).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import nnls

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
DS = ROOT / "datasets"
EV = ROOT / "audit" / "logic_review"
YEARS = list(range(2015, 2020))
FUTURE = list(range(2026, 2031))
ANTIGEN = {"HepB": "hepb3", "Hib": "hib3", "PCV": "pcvc", "Rota": "rotac", "Measles": "mcv1", "Rubella": "rcv1",
           "YF": "yfv", "MenA": "menga"}
UNMAPPED = {"JE": "no WUENIC antigen (JE vaccine is not in the WUENIC 2025 file)",
            "HPV": "adolescent vaccine (girls 9-14), not part of the infant schedule or of uc_imm"}
CAMPAIGN_HEAVY = {"Measles", "MenA", "YF"}
# Toor et al. 2021, eLife 10:e67635, Table 3 (p. 9): deaths averted per 1,000 fully vaccinated persons, vaccination
# activities 2000-2030, with 95% credible intervals
TOOR_T3 = {"Measles": (6.5, 5.9, 8.2), "HepB": (7.7, 4.7, 12.0), "HPV": (12.0, 11.0, 13.0), "YF": (2.1, 1.1, 4.6),
           "Hib": (2.4, 1.1, 4.5), "PCV": (2.3, 1.1, 3.7), "Rubella": (0.3, 0.1, 0.5), "Rota": (0.8, 0.5, 1.0),
           "MenA": (1.0, 0.8, 1.4), "JE": (0.4, 0.0, 0.8)}
GATE = (0.1, 10.0)
LAGS = 10


def load_vimc():
    yov = pd.read_csv(DS / "Toor2021" / "VIMC_deaths_by_year_of_vac.csv")
    cs = pd.read_csv(DS / "Toor2021" / "VIMC_deaths_by_cross_section.csv")
    co = pd.read_csv(DS / "Toor2021" / "VIMC_deaths_by_cohort.csv")
    return (d[d.disease != "All Diseases"] for d in (yov, cs, co))


def load_wuenic():
    w = pd.read_excel(DS / "WUENIC_2025.xlsx", "country")
    w["who"] = w["who"].str.upper().replace({"SEAR": "SEA"})
    return w


def load_wpp():
    wp = pd.read_csv(DS / "WPP2024" / "WPP2024_Demographic_Indicators_Medium.csv",
                     usecols=["ISO3_code", "Time", "Births", "LBsurvivingAge1", "Q5"], low_memory=False)
    wp = wp.dropna(subset=["ISO3_code"]).rename(columns={"ISO3_code": "iso3", "Time": "year"})
    wp["Births"] *= 1000           # WPP counts are in thousands (datasets/MANIFEST.md)
    wp["LBsurvivingAge1"] *= 1000
    return wp.set_index(["iso3", "year"])


def timing(cs, co) -> pd.DataFrame:
    """Non-negative least squares deconvolution of calendar-year deaths averted into years since vaccination."""
    rows = []

    def fit(dis, age, K):
        c = co[(co.disease == dis) & (co.age_group == age)].pivot(index="country", columns="year", values="deaths_averted")
        x = cs[(cs.disease == dis) & (cs.age_group == age)].pivot(index="country", columns="year", values="deaths_averted")
        A, b = [], []
        for iso in x.index:
            if iso not in c.index:
                continue
            for y in range(2000, 2020):
                if y in x.columns:
                    A.append([c.loc[iso].get(y - k, 0.0) for k in range(K)])
                    b.append(x.loc[iso, y])
        A, b = np.nan_to_num(np.array(A)), np.nan_to_num(np.array(b))
        w, _ = nnls(A, b)
        r2 = 1 - ((b - A @ w) ** 2).sum() / ((b - b.mean()) ** 2).sum()
        return w, float(r2), len(b)

    for dis in ANTIGEN:
        v, r2u, n = fit(dis, "under5", 5)
        v = v / v.sum() if v.sum() > 0 else v                 # shares of the under-5 deaths by age 0..4
        w_all, r2a, _ = fit(dis, "all", 12)
        if dis in ("Hib", "PCV", "Rota", "Rubella"):
            later, method_later = np.zeros(5), "0 by definition: every death averted is under 5 (cohort file, under5 = all)"
        elif r2a >= 0.9:
            later, method_later = w_all[5:10], f"NNLS on all-age deaths, lags 0-11, R2 {r2a:.3f}"
        else:
            later, method_later = np.zeros(5), (f"assumption: deaths at age 5+ counted as lifetime deaths beyond the window "
                                                 f"(all-age NNLS fit R2 {r2a:.2f}, not usable)")
        for k in range(5):
            rows.append({"disease": dis, "lag": k, "weight_within_u5": float(v[k]), "method": f"NNLS under-5, lags 0-4, R2 {r2u:.3f}, {n} country-years"})
        for k in range(5, 10):
            rows.append({"disease": dis, "lag": k, "weight_of_lifetime": float(later[k - 5]), "method": method_later})
    return pd.DataFrame(rows)


def main():
    yov, cs, co = load_vimc()
    w = load_wuenic()
    wp = load_wpp()
    ci = pd.read_csv(ROOT / "model_data" / "country_inputs.csv").set_index("iso3")
    model_iso = sorted(set(pd.read_csv(ROOT / "model_data" / "dah_lines.csv").iso3))
    region = pd.read_csv(ROOT / "ext_data" / "who_regions.csv").set_index("iso3")["who_region"]
    region = region.combine_first(w.drop_duplicates("iso3c").set_index("iso3c")["who"])
    cov = w.pivot_table(index=["iso3c", "vaccine"], columns="year", values="coverage")
    latest_year = int(w.year.max())
    yv = yov.set_index(["country", "disease", "year"])
    # under-5 share of lifetime deaths averted, country x disease (cohorts 2015-2019)
    ch = co[co.year.isin(YEARS)].groupby(["country", "disease", "age_group"]).deaths_averted.sum().unstack()
    u5s = (ch["under5"] / ch["all"]).clip(0, 1)
    u5s_pooled = (co[co.year.isin(YEARS)].groupby(["disease", "age_group"]).deaths_averted.sum().unstack().pipe(lambda d: d["under5"] / d["all"])).clip(0, 1)
    # Q5 ratio
    q5 = wp["Q5"].unstack()
    q5r = (q5[FUTURE].mean(axis=1) / q5[YEARS].mean(axis=1)).rename("q5_ratio")

    rows = []
    vimc_iso = sorted(set(yov.country))
    for iso in vimc_iso:
        for dis, ant in ANTIGEN.items():
            if (iso, dis) not in yv.index.droplevel(2).unique():
                continue
            vals = []
            for y in YEARS:
                if (iso, dis, y) not in yv.index or (iso, ant) not in cov.index:
                    continue
                c = cov.loc[(iso, ant)].get(y, np.nan)
                si = wp["LBsurvivingAge1"].get((iso, y), np.nan)
                if pd.isna(c) or pd.isna(si) or c <= 0:
                    continue
                vac = c / 100 * si
                r = yv.loc[(iso, dis, y)]
                vals.append({"year": y, "coverage": c, "vaccinated": vac, "da": max(r.deaths_averted, 0.0),
                             "da_lo": max(r.deaths_av_lo, 0.0), "da_hi": max(r.deaths_av_hi, 0.0)})
            if not vals:
                continue
            v = pd.DataFrame(vals)
            v["dpc"], v["dpc_lo"], v["dpc_hi"] = v.da / v.vaccinated, v.da_lo / v.vaccinated, v.da_hi / v.vaccinated
            mean = v.dpc.mean()
            imin = v.dpc.idxmin()
            use_min = dis in CAMPAIGN_HEAVY
            dpc = float(v.dpc[imin]) if use_min else float(mean)
            lo = float(v.dpc_lo[imin]) if use_min else float(v.dpc_lo.mean())
            hi = float(v.dpc_hi[imin]) if use_min else float(v.dpc_hi.mean())
            rows.append({"iso3": iso, "disease": dis, "antigen": ant, "years_used": len(v),
                         "coverage_2015_19_mean": v.coverage.mean(), "coverage_latest": cov.loc[(iso, ant)].get(latest_year, np.nan) if (iso, ant) in cov.index else np.nan,
                         "vaccinated_mean": v.vaccinated.mean(), "deaths_averted_mean": v.da.mean(),
                         "dpc_mean": mean, "dpc_min_year": float(v.dpc[imin]), "min_year": int(v.year[imin]),
                         "campaign_inflation_mean_over_min": mean / v.dpc[imin] if v.dpc[imin] > 0 else np.nan,
                         "dpc_used_unadjusted": dpc, "rule": "minimum year 2015-19 (campaign-heavy antigen)" if use_min else "mean 2015-19",
                         "q5_ratio": q5r.get(iso, np.nan), "dpc_lo_unadjusted": lo, "dpc_hi_unadjusted": hi,
                         "u5_share": u5s.get((iso, dis), np.nan), "u5_share_source": "country cohort file" if (iso, dis) in u5s.index and pd.notna(u5s.get((iso, dis))) else "pooled",
                         "who_region": region.get(iso, np.nan)})
    t = pd.DataFrame(rows)
    t["u5_share"] = t.u5_share.fillna(t.disease.map(u5s_pooled))
    t["q5_ratio"] = t.q5_ratio.fillna(1.0)
    for c in ("dpc", "dpc_lo", "dpc_hi"):
        t[f"{c}_adj"] = t[f"{c}_used_unadjusted" if c == "dpc" else f"{c}_unadjusted"] * t.q5_ratio
    t["toor_per_1000"] = t.disease.map(lambda d: TOOR_T3[d][0])
    t["gate_ratio"] = t.dpc_adj * 1000 / t.toor_per_1000
    t["gate_pass"] = t.gate_ratio.between(GATE[0], GATE[1])
    passing = t[t.gate_pass]
    reg_med = passing.groupby(["who_region", "disease"])[["dpc_adj", "dpc_lo_adj", "dpc_hi_adj", "u5_share"]].median()
    all_med = passing.groupby("disease")[["dpc_adj", "dpc_lo_adj", "dpc_hi_adj", "u5_share"]].median()

    def fallback(reg, dis):
        if (reg, dis) in reg_med.index and passing[(passing.who_region == reg) & (passing.disease == dis)].shape[0] >= 3:
            return reg_med.loc[(reg, dis)], f"WHO region {reg} median of passing countries"
        return all_med.loc[dis], "median of all passing countries"

    t["final_dpc"], t["final_lo"], t["final_hi"], t["final_source"] = t.dpc_adj, t.dpc_lo_adj, t.dpc_hi_adj, "own VIMC value"
    for i, r in t[~t.gate_pass].iterrows():
        f, lab = fallback(r.who_region, r.disease)
        t.loc[i, ["final_dpc", "final_lo", "final_hi"]] = [f.dpc_adj, f.dpc_lo_adj, f.dpc_hi_adj]
        t.loc[i, "final_source"] = f"outside the 0.1-10x Toor Table 3 gate (ratio {r.gate_ratio:.2f}): {lab}"
    # non-VIMC model countries: regional median per antigen
    extra = []
    for iso in [c for c in model_iso if c not in vimc_iso]:
        reg = region.get(iso, ci.who_region.get(iso))
        for dis, ant in ANTIGEN.items():
            if (iso, ant) not in cov.index:
                continue
            f, lab = fallback(reg, dis)
            extra.append({"iso3": iso, "disease": dis, "antigen": ant, "coverage_latest": cov.loc[(iso, ant)].get(latest_year, np.nan),
                          "final_dpc": f.dpc_adj, "final_lo": f.dpc_lo_adj, "final_hi": f.dpc_hi_adj, "u5_share": f.u5_share,
                          "final_source": f"not in VIMC: {lab}", "who_region": reg, "gate_pass": np.nan, "q5_ratio": q5r.get(iso, np.nan)})
    t = pd.concat([t, pd.DataFrame(extra)], ignore_index=True)
    t["included"] = t.coverage_latest.fillna(0) > 0
    t["model_country"] = t.iso3.isin(model_iso)
    t.to_csv(EV / "batch56_vaccines.csv", index=False)

    tm = timing(cs, co)
    tm.to_csv(EV / "batch56_vaccine_timing.csv", index=False)
    v_u5 = tm.dropna(subset=["weight_within_u5"]).pivot(index="disease", columns="lag", values="weight_within_u5")
    v_later = tm.dropna(subset=["weight_of_lifetime"]).pivot(index="disease", columns="lag", values="weight_of_lifetime")

    # per model country
    out = []
    unm = yov[yov.disease.isin(UNMAPPED) & yov.country.isin(model_iso) & yov.year.isin(YEARS)].groupby("disease").country.unique()
    for iso in model_iso:
        x = t[(t.iso3 == iso) & t.included]
        rec = {"iso3": iso, "imm_dpc": x.final_dpc.sum(), "imm_dpc_lo": x.final_lo.sum(), "imm_dpc_hi": x.final_hi.sum(),
               "imm_antigens": "/".join(sorted(x.antigen)), "imm_antigens_excluded_zero_coverage": "/".join(sorted(t[(t.iso3 == iso) & ~t.included].antigen)),
               "imm_q5_ratio": float(t[t.iso3 == iso].q5_ratio.dropna().iloc[0]) if t[t.iso3 == iso].q5_ratio.notna().any() else np.nan,
               "imm_dpc_source": "; ".join(f"{r.disease}: {r.final_source}" for r in x.itertuples()),
               "imm_in_vimc": iso in vimc_iso}
        lag = np.zeros(LAGS)
        for r in x.itertuples():
            lag[:5] += r.final_dpc * r.u5_share * v_u5.loc[r.disease].to_numpy()
            lag[5:] += r.final_dpc * v_later.loc[r.disease].to_numpy()
        for k in range(LAGS):
            rec[f"imm_dpc_lag{k}"] = lag[k]
        rec["imm_dpc_beyond_window"] = rec["imm_dpc"] - lag.sum()
        out.append(rec)
    o = pd.DataFrame(out).set_index("iso3")
    o.to_csv(EV / "batch56_vaccine_country.csv")

    pd.set_option("display.width", 300); pd.set_option("display.max_columns", 30); pd.set_option("display.max_rows", 200)
    print("unmapped VIMC diseases:", UNMAPPED, "model countries with VIMC estimates for them:", {k: list(v) for k, v in unm.items()})
    print(f"\ncountry-antigen values: {len(t)}; gate failures: {int((t.gate_pass == False).sum())}")  # noqa: E712
    print(t[t.gate_pass == False][["iso3", "disease", "dpc_adj", "toor_per_1000", "gate_ratio", "final_dpc", "final_source"]].round(5).to_string())  # noqa: E712
    print("\ncampaign inflation (mean / minimum year, median across countries):", t.groupby("disease").campaign_inflation_mean_over_min.median().round(2).to_dict())
    print("per 1,000 vaccinated, median across VIMC countries (adjusted):", (t[t.model_country].groupby("disease").final_dpc.median() * 1000).round(2).to_dict())
    print("Toor Table 3 per 1,000 FVP:", {k: v[0] for k, v in TOOR_T3.items() if k in ANTIGEN})
    print("\ntiming (under-5 weights by years since vaccination):"); print(v_u5.round(3).to_string())
    print("years 5-9 (share of lifetime):"); print(v_later.round(4).to_string())
    print("\nmodel countries:"); print(o.loc[["KEN", "NGA", "MOZ", "ZAF", "UGA", "IND"], ["imm_dpc", "imm_dpc_lo", "imm_dpc_hi", "imm_q5_ratio", "imm_antigens", "imm_dpc_beyond_window"]].round(5).to_string())
    print(f"imm_dpc: median {o.imm_dpc.median():.4f}, min {o.imm_dpc.min():.4f}, max {o.imm_dpc.max():.4f}; lo/central median {(o.imm_dpc_lo / o.imm_dpc).median():.2f}, hi/central median {(o.imm_dpc_hi / o.imm_dpc).median():.2f}")
    print("old method (0.020 x 0.65 x clip(U5MR/50)) for comparison:", {c: round(0.02 * 0.65 * float(np.clip(ci.loc[c, 'sh_dyn_mort'] / 50, 0.3, 2.5)), 4) for c in ["KEN", "NGA", "MOZ", "ZAF", "UGA", "IND"]})


if __name__ == "__main__":
    main()
