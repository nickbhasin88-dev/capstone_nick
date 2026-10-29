"""
Independent re-run of the dashboard's fiscal-response regression (regressions.json "fiscal_replacement"; slide 18),
from the raw files on disk rather than model_data/panel.csv, with a second regression implementation.

Checks:
  1. Panel: rebuild the first differences from the raw IHME files (health spending 1995-2023, GDP 1960-2050) and
     compare them with model_data/panel.csv, cell by cell; check that no country has a gap in its years (a gap would
     make a first difference span two years).
  2. Regression: statsmodels OLS with country and year dummies and country-clustered SEs (not prepare_model.twoway_fe),
     compared with regressions.json.
  3. theta = -(b_fall + b_fall_l1) with its 95% CI from the full covariance matrix (the earlier audit used an
     independence approximation that ignores the covariance of the two coefficients).
  4. The rise coefficient: what happens when aid rises.
  5. Rounding: IHME's per-person columns are whole dollars; re-run with per-person values from the unrounded totals /
     UN WPP 2024 population (both GHES and DAH on the same population, so the comparison is internally consistent).
  6. The slide 18 groups (income groups, the most aid-dependent third, the 15 MOU countries), definitions as in
     run_fiscal_history.py.

    .venv/bin/python audit/fiscal_history/rerun_regression_check.py  -> RESULTS_rerun_check.md, rerun_check.csv
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT))
logging.disable(logging.WARNING)
import prepare_model as pm  # noqa: E402  (country list ISO3 only; the regression is re-implemented here)

SPEND = ROOT / "datasets" / "IHME_HEALTH_SPENDING_1995_2023_Y2026M09D21.CSV"
GDP = ROOT / "datasets" / "IHME_GDP_1960_2050_FGH_2026_Y2026M06D11.CSV"
WPP = ROOT / "datasets" / "WPP2024" / "WPP2024_Demographic_Indicators_Medium.csv"
PANEL = ROOT / "model_data" / "panel.csv"
REG = ROOT / "model_data" / "regressions.json"
MOU15 = ["BWA", "BDI", "CMR", "SWZ", "ETH", "KEN", "LSO", "LBR", "MDG", "MWI", "MOZ", "NGA", "RWA", "SLE", "UGA"]
XS = ["d_dah_pc_fall", "d_dah_pc_fall_l1", "d_dah_pc_rise", "d_gdp_pc"]
SLIDE = {"All countries": (-0.19, 97), "Upper-middle income": (-0.41, 32), "Lower-middle income": (-0.15, 37),
         "Low income": (0.01, 26), "Most aid-dependent third": (-0.05, 32), "MOU countries in the panel": (-0.09, 15)}


def build(ghes_pc: pd.Series, dah_pc: pd.Series, base: pd.DataFrame) -> pd.DataFrame:
    p = base.copy()
    p["ghes_pc"], p["dah_pc"] = ghes_pc.values, dah_pc.values
    p = p.sort_values(["iso3", "year"]).reset_index(drop=True)
    g = p.groupby("iso3")
    p["d_ghes_pc"] = g["ghes_pc"].diff()
    d = g["dah_pc"].diff()
    p["d_dah_pc_fall"] = d.clip(upper=0)
    p["d_dah_pc_rise"] = d.clip(lower=0)
    p["d_dah_pc_fall_l1"] = p.groupby("iso3")["d_dah_pc_fall"].shift(1)
    p["d_gdp_pc"] = g["gdp_pc"].diff()
    return p


def fit(df: pd.DataFrame) -> dict:
    d = df[["iso3", "year", "d_ghes_pc"] + XS].replace([np.inf, -np.inf], np.nan).dropna()
    m = smf.ols("d_ghes_pc ~ " + " + ".join(XS) + " + C(iso3) + C(year)", data=d).fit(
        cov_type="cluster", cov_kwds={"groups": pd.factorize(d["iso3"])[0]})
    V = m.cov_params()
    a, b = "d_dah_pc_fall", "d_dah_pc_fall_l1"
    th = -(m.params[a] + m.params[b])
    se_full = float(np.sqrt(V.loc[a, a] + V.loc[b, b] + 2 * V.loc[a, b]))
    se_ind = float(np.hypot(m.bse[a], m.bse[b]))
    r = m.params["d_dah_pc_rise"]
    return {"n_obs": int(m.nobs), "n_countries": int(d.iso3.nunique()), "years": f"{d.year.min()}-{d.year.max()}",
            "b_fall": m.params[a], "se_fall": m.bse[a], "b_fall_l1": m.params[b], "se_fall_l1": m.bse[b],
            "b_rise": r, "se_rise": m.bse["d_dah_pc_rise"], "b_gdp": m.params["d_gdp_pc"],
            "theta": th, "theta_lo": th - 1.96 * se_full, "theta_hi": th + 1.96 * se_full,
            "theta_lo_indep": th - 1.96 * se_ind, "theta_hi_indep": th + 1.96 * se_ind,
            "rise_lo": r - 1.96 * m.bse["d_dah_pc_rise"], "rise_hi": r + 1.96 * m.bse["d_dah_pc_rise"],
            "cov_fall_fall_l1": float(V.loc[a, b])}


def main():
    sp = pd.read_csv(SPEND, encoding="utf-8-sig")
    sp = sp[(sp.level == "Country") & sp.iso3.isin(pm.ISO3) & sp.year.between(2000, 2023)]
    gdp = pd.read_csv(GDP, encoding="utf-8-sig")
    gdp = gdp[gdp.level == "Country"][["iso3", "year", "gdp_usd_mean"]].rename(columns={"gdp_usd_mean": "gdp_pc"})
    base = sp[["iso3", "year", "ghes_total_mean", "dah_total_mean", "the_per_cap_mean"]].merge(gdp, on=["iso3", "year"],
                                                                                              how="left")
    base = base.sort_values(["iso3", "year"]).reset_index(drop=True)
    sp = sp.set_index(["iso3", "year"]).loc[list(zip(base.iso3, base.year))]
    out = ["# Fiscal-response regression (slide 18): independent re-run from the raw data (no model changes)", "",
           "Generated by `audit/fiscal_history/rerun_regression_check.py`. Raw inputs: "
           f"`{SPEND.name}`, `{GDP.name}`, `{WPP.name}`. Regression: statsmodels OLS with country and year dummies and "
           "country-clustered standard errors (a different implementation from `prepare_model.twoway_fe`).", ""]

    # 1. panel rebuild and gaps
    gaps = base.groupby("iso3").year.apply(lambda s: int((s.diff().dropna() != 1).sum()))
    p = build(sp["ghes_per_cap_mean"], sp["dah_per_cap_mean"], base)
    mp = pd.read_csv(PANEL)
    cmp = p.merge(mp[["iso3", "year"] + ["d_ghes_pc"] + XS], on=["iso3", "year"], suffixes=("", "_model"))
    diffs = {c: float(np.nanmax(np.abs(cmp[c] - cmp[f"{c}_model"]))) for c in ["d_ghes_pc"] + XS}
    nan_mismatch = {c: int((cmp[c].isna() != cmp[f"{c}_model"].isna()).sum()) for c in ["d_ghes_pc"] + XS}
    out += ["## 1. Panel rebuilt from the raw files", "",
            f"- Countries in the build list with spending data: {base.iso3.nunique()} (of {len(pm.ISO3)}); "
            f"country-years 2000-2023: {len(base)}.",
            f"- Countries with a gap in their years: {int((gaps > 0).sum())}" +
            (f" ({', '.join(gaps[gaps > 0].index)})" if (gaps > 0).any() else "") + ".",
            f"- Largest absolute difference from model_data/panel.csv, by variable: " +
            ", ".join(f"{k} {v:.2g}" for k, v in diffs.items()) + f"; missing-value mismatches: {sum(nan_mismatch.values())}.",
            ""]

    # 2-4. pooled regression
    reg = json.load(open(REG))["fiscal_replacement"]
    f0 = fit(p[p.year >= 2001])
    out += ["## 2. Pooled regression: re-run vs the dashboard", "",
            "| | Dashboard (regressions.json) | Re-run (statsmodels, raw data) |", "|---|---|---|"]
    for k, lab in [("d_dah_pc_fall", "b fall (this year)"), ("d_dah_pc_fall_l1", "b fall (last year)"),
                   ("d_dah_pc_rise", "b rise"), ("d_gdp_pc", "b GDP per person")]:
        key = {"d_dah_pc_fall": "b_fall", "d_dah_pc_fall_l1": "b_fall_l1", "d_dah_pc_rise": "b_rise", "d_gdp_pc": "b_gdp"}[k]
        se = {"b_fall": f0["se_fall"], "b_fall_l1": f0["se_fall_l1"], "b_rise": f0["se_rise"]}.get(key)
        out.append(f"| {lab} | {reg['coef'][k]:+.4f} (SE {reg['se'][k]:.4f}) | {f0[key]:+.4f}" +
                   (f" (SE {se:.4f})" if se is not None else "") + " |")
    out += [f"| Country-years / countries / years | {reg['n_obs']} / {reg['n_countries']} / {reg['years'][0]}-{reg['years'][1]} "
            f"| {f0['n_obs']} / {f0['n_countries']} / {f0['years']} |", "",
            "## 3. theta (government health spending change per US$1 of aid lost, over that year and the next)", "",
            f"- theta = {f0['theta']:+.3f}.",
            f"- 95% CI with the full covariance matrix: {f0['theta_lo']:+.2f} to {f0['theta_hi']:+.2f}.",
            f"- 95% CI as on slide 18 (covariance ignored): {f0['theta_lo_indep']:+.2f} to {f0['theta_hi_indep']:+.2f} "
            f"(covariance of the two fall coefficients: {f0['cov_fall_fall_l1']:+.4f}).", "",
            "## 4. When aid rises", "",
            f"- Change in government health spending per US$1 of aid gained (same year): {f0['b_rise']:+.3f} "
            f"(95% CI {f0['rise_lo']:+.2f} to {f0['rise_hi']:+.2f}). The model has no lag term for rises.", ""]

    # 5. unrounded per person
    w = pd.read_csv(WPP, usecols=["ISO3_code", "Time", "TPopulation1July"], low_memory=False).dropna(subset=["ISO3_code"])
    w["ISO3_code"] = w.ISO3_code.replace({"XKX": "KSV"})
    pop = w.set_index(["ISO3_code", "Time"])["TPopulation1July"] * 1e3
    popv = pop.reindex(list(zip(base.iso3, base.year))).values
    pu = build(pd.Series(base.ghes_total_mean.values * 1e3 / popv), pd.Series(base.dah_total_mean.values * 1e3 / popv), base)
    f1 = fit(pu[pu.year >= 2001])
    out += ["## 5. Rounding check: per-person values from unrounded totals / UN WPP 2024 population", "",
            f"- theta {f1['theta']:+.3f} (95% CI {f1['theta_lo']:+.2f} to {f1['theta_hi']:+.2f}); rise {f1['b_rise']:+.3f} "
            f"({f1['rise_lo']:+.2f} to {f1['rise_hi']:+.2f}); {f1['n_obs']} country-years, {f1['n_countries']} countries.",
            "- IHME uses its own (GBD) population, so per-person levels differ slightly from the IHME columns; the check is "
            "only whether whole-dollar rounding changes the estimate.", ""]

    # 6. slide groups
    wb = pd.read_csv(ROOT / "ext_data" / "wb_country_entities.csv", usecols=["iso3166_1_alpha3", "income_groups"]).dropna()
    inc = wb.set_index("iso3166_1_alpha3")["income_groups"].to_dict()
    inc["KSV"] = inc.get("XKX", np.nan)
    rows = []
    for lab, panel in [("IHME per-person columns (as the dashboard)", p), ("Unrounded totals / WPP population", pu)]:
        q = panel[panel.year >= 2001].copy()
        dep = base[base.year.between(2015, 2023)].assign(r=lambda x: sp.loc[list(zip(x.iso3, x.year)), "dah_per_cap_mean"].values
                                                         / x.the_per_cap_mean).groupby("iso3").r.mean()
        dep_t = pd.qcut(dep, 3, labels=["low", "middle", "high"])
        groups = {"All countries": q, "Upper-middle income": q[q.iso3.map(inc) == "upper_middle_income"],
                  "Lower-middle income": q[q.iso3.map(inc) == "lower_middle_income"],
                  "Low income": q[q.iso3.map(inc) == "low_income"],
                  "Most aid-dependent third": q[q.iso3.map(dep_t) == "high"],
                  "MOU countries in the panel": q[q.iso3.isin(MOU15)]}
        for g, d in groups.items():
            r = fit(d)
            rows.append({"data": lab, "group": g, "slide_theta": SLIDE[g][0], "slide_countries": SLIDE[g][1], **r})
    t = pd.DataFrame(rows)
    t.to_csv(HERE / "rerun_check.csv", index=False)
    out += ["## 6. Slide 18 groups", "",
            "| Group | Slide | Re-run theta | 95% CI (full covariance) | 95% CI (as slide) | Countries (slide / re-run) | "
            "Rise: change per US$1 gained | Unrounded theta | Unrounded 95% CI |", "|---|---|---|---|---|---|---|---|---|"]
    a, b = t[t.data.str.startswith("IHME")].set_index("group"), t[t.data.str.startswith("Unrounded")].set_index("group")
    for g in SLIDE:
        r, u = a.loc[g], b.loc[g]
        out.append(f"| {g} | {r.slide_theta:+.2f} | {r.theta:+.2f} | {r.theta_lo:+.2f} to {r.theta_hi:+.2f} | "
                   f"{r.theta_lo_indep:+.2f} to {r.theta_hi_indep:+.2f} | {int(r.slide_countries)} / {int(r.n_countries)} | "
                   f"{r.b_rise:+.2f} ({r.rise_lo:+.2f} to {r.rise_hi:+.2f}) | {u.theta:+.2f} | {u.theta_lo:+.2f} to {u.theta_hi:+.2f} |")
    out += ["", "Income groups: World Bank classification in `ext_data/wb_country_entities.csv` (one current "
            "classification applied to all years). Aid dependence: mean DAH / total health spending per person 2015-2023, "
            "terciles. Sign: theta < 0 means government health spending fell with the aid; theta > 0 would be replacement."]
    (HERE / "RESULTS_rerun_check.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
