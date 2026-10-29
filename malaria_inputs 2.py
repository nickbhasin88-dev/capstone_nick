"""
Malaria coverage, cases and the baseline malaria death trend from the Malaria Atlas Project (MAP), audit I-06 / I-11.

Source: Malaria Atlas Project, national unit data (data.malariaatlas.org), downloaded 2026-10-13. The raw downloads
sit in datasets/ (never committed); process() saves the subset the model uses to ext_data/map/, which is committed.

    python malaria_inputs.py              # rebuild ext_data/map/ from datasets/ and patch model_data/country_inputs.csv
    python malaria_inputs.py --apply-only # patch country_inputs.csv from ext_data/map/ only

who_inputs.apply() calls apply() last, so a full rebuild (prepare_model.py) gives the same inputs. Columns written, each
with <column>_year and <column>_source:
    mal_cm_cov    malaria treatment coverage = MAP "Effective Treatment" per 100 malaria cases (0-1)
    mal_itn_cov   bednet coverage = MAP ITN "Use" (people sleeping under a net, 0-1)
    mal_irs_cov   spraying coverage = MAP IRS "Coverage" (households sprayed, 0-1)
    malaria_cases MAP P. falciparum + P. vivax clinical cases (MAP countries; others keep the WHO estimate)
    who_region, malaria_u5_share_rule, malaria_u5_share_param  WHO region (ext_data/who_regions.csv) and which World
                          Malaria Report 2025 under-5 share applies (the value is in model_params.csv)
    trend_malaria_deaths  annual trend of WHO estimated malaria deaths (GHO MALARIA_EST_DEATHS, ext_data/gho/),
                          2015 to the latest year, clipped to +/-5% a year (the clip is an assumption)
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
RAW_DIR = HERE / "datasets"
MAP_DIR = HERE / "ext_data" / "map"
INPUTS_FILE = HERE / "model_data" / "country_inputs.csv"
DOWNLOAD_DATE = "2026-10-13"
SOURCE = "Malaria Atlas Project (data.malariaatlas.org)"
MAP_YEAR = 2025                         # latest year in the MAP files (ITN and treatment repeat 2024 there)
RAW = {                                 # processed name -> (raw file, metrics kept)
    "treatment": ("MAP_national_treatment_2026-10-13.csv", ["Effective Treatment"]),
    "itn": ("MAP_national_ITN_2026-10-13.csv", ["Access", "Use", "Use Rate"]),
    "irs": ("MAP_national_IRS_2026-10-13.csv", ["Coverage"]),
    "pf_cases": ("MAP_national_Pf_cases_2026-10-13.csv", ["Clinical Cases"]),
    "pv_cases": ("MAP_national_Pv_cases_2026-10-13.csv", ["Clinical Cases"]),
    "incidence_prevalence": ("MAP_national_incidence_prevalence_2026-10-13.csv",
                             ["Incidence Rate", "Infection Prevalence"]),
}
TREND_START = 2015                      # malaria death trend: WHO deaths from 2015 to the latest year in the file
TREND_CLIP = (-0.05, 0.05)              # assumption (no source): keeps a short noisy series from extrapolating far
WHO_DEATHS_FILE = HERE / "ext_data" / "gho" / "MALARIA_EST_DEATHS.csv"   # written by who_inputs.py --download
WHO_REGIONS_FILE = HERE / "ext_data" / "who_regions.csv"   # WHO region of each country (WHO TB data, g_whoregion)
# WHO regions for which the World Malaria Report 2025 states the share of malaria deaths in children under 5
# (model_params.csv mal_u5_share_<region>); there is no European Region or global figure in the report
WMR_U5_REGIONS = {"AFR": "mal_u5_share_afr", "AMR": "mal_u5_share_amr", "EMR": "mal_u5_share_emr",
                  "SEA": "mal_u5_share_sea", "WPR": "mal_u5_share_wpr"}
ITN_SURVEY_MIN_YEAR = 2015              # outside MAP's ITN countries, a household survey counts only from 2015
MAL_CM_MIN_INCIDENCE = 50               # non-MAP countries: fever-treatment surveys count only where malaria is common


def process():
    """datasets/MAP_*.csv -> ext_data/map/<name>.csv (iso3, year, metric, units, value, source, downloaded)."""
    MAP_DIR.mkdir(parents=True, exist_ok=True)
    for name, (raw, metrics) in RAW.items():
        d = pd.read_csv(RAW_DIR / raw, encoding="utf-8-sig")
        d = d[d["Metric"].isin(metrics)].rename(columns={"ISO3": "iso3", "Year": "year", "Metric": "metric",
                                                         "Units": "units", "Value": "value"})
        d = d[["iso3", "year", "metric", "units", "value"]].assign(source=SOURCE, downloaded=DOWNLOAD_DATE)
        d.sort_values(["metric", "iso3", "year"]).to_csv(MAP_DIR / f"{name}.csv", index=False)
        print(f"  {name}: {d.iso3.nunique()} countries, {int(d.year.min())}-{int(d.year.max())}, metrics {metrics}")


def load(name: str, metric: str | None = None) -> pd.DataFrame:
    d = pd.read_csv(MAP_DIR / f"{name}.csv")
    return d if metric is None else d[d["metric"] == metric]


def at_year(d: pd.DataFrame, year: int = MAP_YEAR) -> pd.Series:
    return d[d["year"] == year].set_index("iso3")["value"]


def irs_modelled(d: pd.DataFrame) -> set:
    """MAP models spraying for Africa only; elsewhere every year is 0, which means 'no estimate', not 'no spraying'."""
    return set(d.loc[d["value"] > 0, "iso3"])


def death_trend(index) -> tuple[pd.Series, pd.Series, tuple]:
    """Annual % change of WHO estimated malaria deaths (World Malaria Report, GHO MALARIA_EST_DEATHS), log-linear fit
    from TREND_START to the latest year in the file (at least 5 positive years), clipped to TREND_CLIP (logic review
    L-25: the deaths themselves, not the P. falciparum case trend used before). Returns (trend, unclipped fit, years);
    countries without a usable WHO series get 0."""
    d = pd.read_csv(WHO_DEATHS_FILE)
    years = (TREND_START, int(d["year"].max()))
    d = d[d.year.between(*years) & (d.value > 0)]
    fit = pd.Series({iso: float(np.expm1(np.polyfit(g["year"], np.log(g["value"]), 1)[0]))
                     for iso, g in d.groupby("iso3") if len(g) >= 5}, dtype=float).reindex(index)
    return fit.clip(*TREND_CLIP).fillna(0.0), fit, years


def _wdi_latest(code: str) -> pd.DataFrame:
    d = pd.read_csv(HERE / "ext_data" / "wdi" / f"{code}.csv").rename(columns={"geo": "iso3", "time": "year", code: "value"})
    d["iso3"] = d["iso3"].str.upper()
    return d.dropna(subset=["value"]).sort_values("year").groupby("iso3").tail(1).set_index("iso3")


def apply(ci: pd.DataFrame) -> pd.DataFrame:
    ci = ci.copy()
    idx = ci.index
    tag = f"MAP {MAP_YEAR}"

    # A. treatment coverage: MAP effective treatment; else the old survey rule (fever treatment, only where malaria is
    #    common); else the default (NaN here)
    tr = at_year(load("treatment", "Effective Treatment")).reindex(idx) / 100
    have = tr.notna()
    surv = ci["sh_mlr_tret_zs"] / 100 if "sh_mlr_tret_zs" in ci else pd.Series(np.nan, index=idx)
    surv = surv.where(ci.get("sh_mlr_incd_p3", pd.Series(np.nan, index=idx)) >= MAL_CM_MIN_INCIDENCE)
    ci["mal_cm_cov"] = tr.where(have, surv)
    ci["mal_cm_cov_year"] = np.where(have, MAP_YEAR, np.where(surv.notna(), ci.get("sh_mlr_tret_zs_year"), np.nan))
    ci["mal_cm_cov_source"] = np.where(have, tag, np.where(surv.notna(), "survey", "default"))

    # B. cases needing treatment: MAP Pf + Pv clinical cases
    pf, pv = at_year(load("pf_cases")).reindex(idx), at_year(load("pv_cases")).reindex(idx)
    cases = pf.fillna(0) + pv.fillna(0)
    have = pf.notna() | pv.notna()
    # the WHO / derived value, kept for the Validation page (on a rerun, the value saved the first time)
    src0 = ci.get("malaria_cases_source", pd.Series("", index=idx)).fillna("").astype(str)
    again = src0.str.startswith("MAP") & ("malaria_cases_prev" in ci)
    ci["malaria_cases_prev"] = ci["malaria_cases"].where(~again, ci.get("malaria_cases_prev"))
    ci["malaria_cases_prev_source"] = src0.where(~again, ci.get("malaria_cases_prev_source"))
    ci["malaria_cases"] = cases.where(have, ci["malaria_cases"])
    ci["malaria_cases_year"] = np.where(have, MAP_YEAR, ci.get("malaria_cases_year"))
    ci["malaria_cases_source"] = np.where(have, f"{tag}: P. falciparum + P. vivax clinical cases",
                                          ci.get("malaria_cases_source"))

    # C. bednets: MAP ITN use; else the newest household survey if from 2015 on; else the default (NaN here)
    itn = at_year(load("itn", "Use")).reindex(idx) / 100
    have = itn.notna()
    w = _wdi_latest("sh_mlr_nets_zs").reindex(idx)
    recent = w["value"].notna() & (w["year"] >= ITN_SURVEY_MIN_YEAR)
    ci["mal_itn_cov"] = itn.where(have, (w["value"] / 100).where(recent))
    ci["mal_itn_cov_year"] = np.where(have, MAP_YEAR, w["year"].where(recent))
    ci["mal_itn_cov_source"] = np.where(have, tag, np.where(recent, "survey", "default"))

    # D. spraying: MAP household IRS coverage where MAP models it (Africa); elsewhere no estimate (NaN here; the model
    #    then uses the coverage donor IRS money pays for)
    irs = load("irs", "Coverage")
    v = at_year(irs).reindex(idx) / 100
    have = v.notna() & idx.isin(list(irs_modelled(irs)))
    ci["mal_irs_cov"] = v.where(have)
    ci["mal_irs_cov_year"] = np.where(have, MAP_YEAR, np.nan)
    ci["mal_irs_cov_source"] = np.where(have, tag, "no MAP estimate")

    # L-25: baseline malaria death trend = trend of WHO estimated malaria deaths, 2015 to the latest year
    t, fit, yrs = death_trend(idx)
    ci["trend_malaria_deaths"] = t
    ci["trend_malaria_deaths_fit"] = fit
    ci["trend_malaria_deaths_source"] = np.where(fit.notna(), f"WHO estimated malaria deaths, {yrs[0]}-{yrs[1]}",
                                                 "no WHO death series: 0")
    # under-5 share of malaria deaths (logic review IMP-05 follow-up): the World Malaria Report 2025 share for the
    # country's WHO region. Rule a = WMR regional figure; no WMR figure (European Region: no malaria deaths, and the
    # report gives no global share) = none
    reg = pd.read_csv(WHO_REGIONS_FILE).set_index("iso3")["who_region"].reindex(idx)
    ci["who_region"] = reg
    ci["malaria_u5_share_rule"] = np.where(reg.isin(list(WMR_U5_REGIONS)), "a: WMR 2025 regional share",
                                           "none: no WMR regional or global figure (no malaria deaths)")
    ci["malaria_u5_share_param"] = reg.map(WMR_U5_REGIONS)
    return ci


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--apply-only", action="store_true", help="skip rebuilding ext_data/map/ from datasets/")
    a = p.parse_args()
    if not a.apply_only:
        process()
    ci = pd.read_csv(INPUTS_FILE).set_index("iso3")
    new = apply(ci)
    for c in ("mal_cm_cov", "mal_itn_cov", "mal_irs_cov", "malaria_cases"):
        print(f"  {c:14s}", new[f"{c}_source"].fillna("n/a").str.split(":").str[0].value_counts().to_dict())
    print("  trend clipped:", int((new["trend_malaria_deaths_fit"].abs() > TREND_CLIP[1]).sum()))
    new.reset_index().to_csv(INPUTS_FILE, index=False)
    print("updated", INPUTS_FILE)


if __name__ == "__main__":
    main()
