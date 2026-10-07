"""
Build the inputs for the funding-shock model (Section 4 of app.py).

    python prepare_model.py --dah  <IHME_DAH_DATABASE_1990_2026_*.CSV>
                            --spend <IHME_HEALTH_SPENDING_1995_2023_*.CSV>
                            --expected <IHME_EXPECTED_HEALTH_SPENDING_2024_2050_*.CSV>
                            --gdp  <IHME_GDP_1960_2050_*.CSV>
                            --mou  <co-financing_MOU.xlsx>
                            [--download]      # refresh ext_data/ from the Gapminder WDI mirror on GitHub

Writes ./model_data/:
    dah_lines.csv        baseline aid (avg 2021-2023, constant 2023 US$) by country x source group x channel x service line
    ihme_trend.csv       IHME's own 2025 (preliminary) / 2021-23 ratio by source group x channel x disease bucket
    country_inputs.csv   epidemiology, coverage, fiscal-space and MOU data, one row per country
    panel.csv            country-year panel used for the regressions
    regressions.json     fixed-effects estimates (fiscal replacement + coverage dose-response)

Everything is in constant 2023 US$ unless noted. IHME DAH values are in thousands of US$.
"""
import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
OUT = HERE / "model_data"
EXT = HERE / "ext_data"

BASE_YEARS = (2021, 2023)          # baseline = average of these years (smooths lumpy net campaigns / Gavi tranches)

# --------------------------------------------------------------------------- #
# Country list (same as the dashboard dropdown)
# --------------------------------------------------------------------------- #
ISO3 = ["AFG", "ALB", "AGO", "ARM", "AZE", "BGD", "BLR", "BLZ", "BEN", "BOL", "BWA", "BRA", "BFA", "BDI", "KHM", "CMR",
        "CAF", "CHN", "COL", "CRI", "CIV", "COD", "DJI", "DOM", "ECU", "EGY", "SLV", "SWZ", "ETH", "FJI", "GMB", "GEO",
        "GHA", "GTM", "GIN", "GUY", "HTI", "HND", "IND", "IDN", "IRQ", "JAM", "JOR", "KAZ", "KEN", "KSV", "KGZ", "LAO",
        "LSO", "LBR", "LBY", "MDG", "MWI", "MLI", "MUS", "MEX", "MDA", "MNG", "MAR", "MOZ", "MMR", "NAM", "NPL", "NIC",
        "NER", "NGA", "PAK", "PAN", "PNG", "PRY", "PER", "PHL", "ROU", "RUS", "RWA", "STP", "SEN", "SLE", "SOM", "ZAF",
        "SSD", "SDN", "TJK", "TZA", "THA", "TLS", "TGO", "TTO", "TKM", "UGA", "UKR", "UZB", "VEN", "VNM", "PSE", "YEM",
        "ZMB", "ZWE"]
SSA = {"AGO", "BEN", "BWA", "BFA", "BDI", "CMR", "CAF", "CIV", "COD", "DJI", "SWZ", "ETH", "GMB", "GHA", "GIN", "KEN",
       "LSO", "LBR", "MDG", "MWI", "MLI", "MUS", "MOZ", "NAM", "NER", "NGA", "RWA", "STP", "SEN", "SLE", "SOM", "ZAF",
       "SSD", "SDN", "TZA", "TGO", "UGA", "ZMB", "ZWE"}

# --------------------------------------------------------------------------- #
# How IHME columns map onto the model
# --------------------------------------------------------------------------- #
SOURCE_GROUPS = {
    "United_States": "United States", "United_Kingdom": "United Kingdom", "Germany": "Germany", "France": "France",
    "Japan": "Japan", "Canada": "Canada", "Netherlands": "Netherlands",
    "Sweden": "Nordics", "Norway": "Nordics", "Denmark": "Nordics", "Finland": "Nordics",
    "Gates Foundation": "Gates Foundation",
    "Private_other": "Other private", "Corporate_donations": "Other private",
    "Debt_repayments": "Development-bank lending",
    "China": "Non-DAC governments", "Non_OECD_DAC_countries": "Non-DAC governments",
    "Non_OECD_non_DAC_countries": "Non-DAC governments",
    "Other": "Other / unallocable", "Unallocable": "Other / unallocable",
}  # everything else (Australia, Belgium, Italy, Spain, Switzerland, Korea, ...) -> "Other DAC governments"


def source_group(s: str) -> str:
    return SOURCE_GROUPS.get(s, "Other DAC governments")


def channel_group(c: str) -> str:
    if c.startswith("BIL_"):
        return "Bilateral agency"
    return {"NGO": "NGOs", "INTLNGO": "NGOs", "US_FOUND": "NGOs", "GATES": "Gates direct", "GFATM": "Global Fund",
            "GAVI": "Gavi", "WHO": "WHO", "PAHO": "WHO", "UNICEF": "UNICEF", "UNFPA": "UNFPA", "UNAIDS": "UNAIDS",
            "UNITAID": "Unitaid", "WB_IDA": "Development banks", "WB_IBRD": "Development banks", "WB": "Development banks",
            "AfDB": "Development banks", "AsDB": "Development banks", "IDB": "Development banks",
            "EC": "EU institutions", "EEA": "EU institutions", "CEPI": "CEPI"}.get(c, "Other")


# service line -> (bucket, IHME program-area columns)
LINES = {
    "hiv_art":   ("HIV", ["hiv_treat", "hiv_care", "hiv_ct"]),
    "hiv_pmtct": ("HIV", ["hiv_pmtct"]),
    "hiv_prev":  ("HIV", ["hiv_prev"]),
    "hiv_ovc":   ("HIV", ["hiv_ovc"]),
    "hiv_unspec": ("HIV", ["hiv_other", "hiv_amr"]),          # program area not reported -> allocated by the known mix
    "hiv_hss":   ("HIV", ["hiv_hss_other", "hiv_hss_hrh", "hiv_hss_me"]),   # systems support (labs, HR, M&E)
    "tb_ds":     ("TB", ["tb_treat", "tb_diag"]),
    "tb_dr":     ("TB", ["tb_amr"]),
    "tb_unspec": ("TB", ["tb_other"]),
    "tb_hss":    ("TB", ["tb_hss_other", "tb_hss_hrh", "tb_hss_me"]),
    "mal_itn":   ("Malaria", ["mal_con_nets", "mal_con_oth"]),
    "mal_irs":   ("Malaria", ["mal_con_irs"]),
    "mal_cm":    ("Malaria", ["mal_diag", "mal_treat", "mal_comm_con"]),
    "mal_unspec": ("Malaria", ["mal_other", "mal_amr"]),
    "mal_hss":   ("Malaria", ["mal_hss_other", "mal_hss_hrh", "mal_hss_me"]),
    "imm":       ("Immunization", ["nch_cnv"]),
}
BUCKET_TOTAL_COL = {"HIV": "hiv_dah_23", "TB": "tb_dah_23", "Malaria": "mal_dah_23", "Immunization": "nch_cnv_dah_23"}


# --------------------------------------------------------------------------- #
# External series (WDI / WHO / UNAIDS / UN IGME via Gapminder's GitHub mirrors)
# --------------------------------------------------------------------------- #
WDI = ["sh_dyn_aids_zs", "sh_hiv_artc_zs", "sh_hiv_incd_tl", "sh_hiv_0014", "sh_hiv_pmtc_zs", "sh_tbs_incd",
       "sh_tbs_dtec_zs", "sh_tbs_cure_zs", "sh_mlr_incd_p3", "sh_mlr_nets_zs", "sh_mlr_tret_zs", "sh_imm_idpt",
       "sh_imm_meas", "sh_dyn_mort", "sh_dth_mort", "sp_dyn_cbrt_in", "sp_pop_totl", "sp_pop_1564_to", "sp_pop_0014_to",
       "gc_rev_xgrt_gd_zs", "gc_dod_totl_gd_zs", "gc_xpn_intp_rv_zs", "gc_xpn_totl_gd_zs", "sh_xpd_ghed_ge_zs",
       "sh_uhc_sci"]
SG = ["people_living_with_hiv_number_all_ages", "all_forms_of_tb_incidence_estimated",
      "all_forms_of_tb_number_of_deaths_estimated", "tb_hivplus_number_of_deaths_estimated",
      "tb_hivplus_incidence_estimated", "malaria_deaths_in_children_1_59_months_total_deaths",
      "measles_deaths_in_children_1_59_months_total_deaths", "pneumonia_deaths_in_children_1_59_months_total_deaths"]
WDI_URL = "https://raw.githubusercontent.com/open-numbers/ddf--open_numbers--world_development_indicators/master/datapoints/ddf--datapoints--{}--by--geo--time.csv"
SG_URL = "https://raw.githubusercontent.com/open-numbers/ddf--gapminder--systema_globalis/master/countries-etc-datapoints/ddf--datapoints--{}--by--geo--time.csv"


def download_ext():
    import urllib.request
    (EXT / "wdi").mkdir(parents=True, exist_ok=True)
    (EXT / "sg").mkdir(parents=True, exist_ok=True)
    for i in WDI:
        urllib.request.urlretrieve(WDI_URL.format(i), EXT / "wdi" / f"{i}.csv")
    for i in SG:
        urllib.request.urlretrieve(SG_URL.format(i), EXT / "sg" / f"ddf--datapoints--{i}--by--geo--time.csv")


def read_ext(name: str) -> pd.DataFrame:
    p = EXT / "wdi" / f"{name}.csv"
    if not p.exists():
        p = EXT / "sg" / f"ddf--datapoints--{name}--by--geo--time.csv"
    d = pd.read_csv(p)
    d.columns = ["iso3", "year", "value"]
    d["iso3"] = d["iso3"].str.upper()
    d["year"] = d["year"].astype(int)
    return d.dropna()


def latest(name: str, max_year: int = 2024, min_year: int = 2010) -> pd.DataFrame:
    """Most recent value per country in [min_year, max_year] -> columns name, name_year."""
    d = read_ext(name)
    d = d[(d.year <= max_year) & (d.year >= min_year)].sort_values("year").groupby("iso3").tail(1)
    return d.set_index("iso3").rename(columns={"value": name, "year": f"{name}_year"})


# --------------------------------------------------------------------------- #
# Fixed-effects regression (two-way within transformation, country-clustered SEs) - no statsmodels needed
# --------------------------------------------------------------------------- #
def twoway_fe(df: pd.DataFrame, y: str, xs: list, unit="iso3", time="year") -> dict:
    d = df[[unit, time, y] + xs].replace([np.inf, -np.inf], np.nan).dropna().copy()
    cols = [y] + xs
    # iterative demeaning (handles unbalanced panels)
    z = d[cols].astype(float).copy()
    for _ in range(50):
        prev = z.copy()
        z = z - z.groupby(d[unit]).transform("mean")
        z = z - z.groupby(d[time]).transform("mean")
        if np.abs(z - prev).to_numpy().max() < 1e-10:
            break
    Y = z[y].to_numpy()
    X = z[xs].to_numpy()
    XtX_inv = np.linalg.pinv(X.T @ X)
    b = XtX_inv @ X.T @ Y
    e = Y - X @ b
    # cluster-robust (country) variance
    meat = np.zeros((len(xs), len(xs)))
    for _, idx in d.groupby(unit).indices.items():
        s = X[idx].T @ e[idx]
        meat += np.outer(s, s)
    G, N, K = d[unit].nunique(), len(d), len(xs) + d[unit].nunique() + d[time].nunique() - 1
    adj = G / (G - 1) * (N - 1) / max(N - K, 1)
    V = adj * XtX_inv @ meat @ XtX_inv
    se = np.sqrt(np.diag(V))
    r2_within = 1 - (e @ e) / (Y @ Y) if (Y @ Y) > 0 else np.nan
    return {"y": y, "x": xs, "coef": dict(zip(xs, b.round(6))), "se": dict(zip(xs, se.round(6))),
            "n_obs": int(N), "n_countries": int(G), "years": [int(d[time].min()), int(d[time].max())],
            "r2_within": float(round(r2_within, 4))}


# --------------------------------------------------------------------------- #
def main(a):
    OUT.mkdir(exist_ok=True)
    if a.download:
        download_ext()

    # ---------------- DAH ---------------- #
    print("reading DAH ...")
    need = ["year", "source", "channel", "recipient_isocode", "dah_23"] + list(BUCKET_TOTAL_COL.values())
    need += sorted({f"{c}_dah_23" for _, cs in LINES.values() for c in cs})
    dah = pd.read_csv(a.dah, usecols=lambda c: c in need, na_values=["-"], low_memory=False)
    num = [c for c in dah.columns if c.endswith("_dah_23")]
    dah[num] = dah[num].fillna(0.0)
    dah["src_grp"] = dah["source"].map(source_group)
    dah["chan_grp"] = dah["channel"].map(channel_group)

    # (1) baseline by country x source group x channel group x line, US$ (not thousands)
    base = dah[dah.year.between(*BASE_YEARS) & dah.recipient_isocode.isin(ISO3)]
    rows = []
    for line, (bucket, cols) in LINES.items():
        g = base.groupby(["recipient_isocode", "src_grp", "chan_grp", "year"])[[f"{c}_dah_23" for c in cols]].sum().sum(axis=1)
        g = g.groupby(level=[0, 1, 2]).sum() / (BASE_YEARS[1] - BASE_YEARS[0] + 1) * 1e3
        g = g[g.abs() > 0].rename("usd").reset_index()
        g["line"], g["bucket"] = line, bucket
        rows.append(g)
    lines = pd.concat(rows).rename(columns={"recipient_isocode": "iso3"})
    lines.to_csv(OUT / "dah_lines.csv", index=False)
    # total DAH (all purposes) per country, for "share of aid that the model covers"
    tot = base.groupby("recipient_isocode")["dah_23"].sum() / (BASE_YEARS[1] - BASE_YEARS[0] + 1) * 1e3
    print(f"  dah_lines: {len(lines):,} rows, {lines.iso3.nunique()} countries, ${lines.usd.sum() / 1e9:.1f}B/yr modelled")

    # (2) IHME's own 2025 preliminary estimate relative to the 2021-23 baseline (global totals; no recipient in 2024-25)
    glob = dah[dah.year.between(*BASE_YEARS)].groupby(["src_grp", "chan_grp"])[list(BUCKET_TOTAL_COL.values())].sum() / 3
    g25 = dah[dah.year == 2025].groupby(["src_grp", "chan_grp"])[list(BUCKET_TOTAL_COL.values())].sum()
    tr = []
    for b, col in BUCKET_TOTAL_COL.items():
        t = pd.DataFrame({"base": glob[col], "y2025": g25[col]}).fillna(0.0)
        t["bucket"] = b
        tr.append(t.reset_index())
    tr = pd.concat(tr)
    # fall back to source-group x bucket when the cell is tiny (< $20M/yr baseline)
    sb = tr.groupby(["src_grp", "bucket"])[["base", "y2025"]].sum()
    sb["ratio_sb"] = sb["y2025"] / sb["base"]
    tr = tr.merge(sb["ratio_sb"].reset_index(), on=["src_grp", "bucket"], how="left")
    tr["ratio"] = np.where(tr["base"] >= 20_000, tr["y2025"] / tr["base"].where(tr["base"] > 0), tr["ratio_sb"])
    tr["ratio"] = tr["ratio"].fillna(1.0).clip(0, 1.5)
    tr["base_usd"], tr["y2025_usd"] = tr["base"] * 1e3, tr["y2025"] * 1e3
    tr[["src_grp", "chan_grp", "bucket", "base_usd", "y2025_usd", "ratio"]].to_csv(OUT / "ihme_trend.csv", index=False)

    # ---------------- spending, GDP ---------------- #
    sp = pd.read_csv(a.spend, encoding="utf-8-sig")
    sp = sp[sp.level == "Country"]
    ex = pd.read_csv(a.expected, encoding="utf-8-sig")
    ex = ex[ex.level == "Country"]
    gdp = pd.read_csv(a.gdp, encoding="utf-8-sig")
    gdp = gdp[gdp.level == "Country"][["iso3", "year", "gdp_usd_mean"]].rename(columns={"gdp_usd_mean": "gdp_pc"})

    # ---------------- country inputs ---------------- #
    ci = pd.DataFrame(index=pd.Index(ISO3, name="iso3"))
    s23 = sp[sp.year == 2023].set_index("iso3")
    for k in ["the", "ghes", "ppp", "oop", "dah"]:
        ci[f"{k}_2023"] = s23[f"{k}_total_mean"] * 1e3
    ci["ghes_pc_2023"] = s23["ghes_per_cap_mean"]
    ci["ghes_pct_gdp_2023"] = s23["ghes_per_gdp_mean"] * 100
    ci["dah_share_the_2023"] = s23["dah_per_the_mean"]
    e30 = ex[ex.year == 2030].set_index("iso3")
    e26 = ex[ex.year == 2026].set_index("iso3")
    ci["ghes_2026_expected"] = e26["ghes_total_mean"] * 1e3
    ci["dah_2026_expected"] = e26["dah_total_mean"] * 1e3
    ci["ghes_2030_expected"] = e30["ghes_total_mean"] * 1e3
    ci["gdp_pc"] = gdp[gdp.year == 2024].set_index("iso3")["gdp_pc"]
    ci["dah_all_purposes_base"] = tot

    # historical real GHES growth (fiscal "surge" capacity)
    gh = sp[sp.iso3.isin(ISO3)].sort_values(["iso3", "year"])[["iso3", "year", "ghes_total_mean"]].copy()
    gh["g"] = gh.groupby("iso3")["ghes_total_mean"].pct_change()
    gh = gh[gh.year >= 2001]
    ci["ghes_growth_median"] = gh.groupby("iso3")["g"].median()
    ci["ghes_growth_p75"] = gh.groupby("iso3")["g"].quantile(0.75)
    ci["ghes_growth_p90"] = gh.groupby("iso3")["g"].quantile(0.9)

    for n in WDI:
        ci = ci.join(latest(n, min_year=2005 if n.startswith("sh_mlr") else 2010))
    for n in SG:
        ci = ci.join(latest(n, min_year=2000))

    # PLHIV (all ages) = prevalence 15-49 x population 15-64 x calibration + children 0-14.
    # Calibration ratio from 2011, the last year with a direct PLHIV series (median ~1.0, clipped 0.6-1.6).
    pv, p1564, kids = read_ext("sh_dyn_aids_zs"), read_ext("sp_pop_1564_to"), read_ext("sh_hiv_0014")
    pl = read_ext("people_living_with_hiv_number_all_ages")
    cal = (pl[pl.year == 2011].set_index("iso3")["value"]
           - kids[kids.year == 2011].set_index("iso3")["value"].reindex(pl[pl.year == 2011].iso3).fillna(0).values) / (
        pv[pv.year == 2011].set_index("iso3")["value"] / 100 * p1564[p1564.year == 2011].set_index("iso3")["value"])
    ci["plhiv_calibration"] = cal.reindex(ci.index).clip(0.6, 1.6).fillna(1.0)
    ci["plhiv"] = (ci["sh_dyn_aids_zs"] / 100 * ci["sp_pop_1564_to"] * ci["plhiv_calibration"]
                   + ci["sh_hiv_0014"].fillna(0))
    ci["births"] = ci["sp_dyn_cbrt_in"] / 1000 * ci["sp_pop_totl"]
    ci["hiv_pos_pregnancies"] = ci["births"] * ci["sh_dyn_aids_zs"] / 100 * 1.15     # female prevalence ~15% above all-adult
    ci["tb_hiv_share"] = (ci["tb_hivplus_incidence_estimated"] / ci["all_forms_of_tb_incidence_estimated"]).clip(0, 0.8)
    ci["tb_deaths_total"] = ci["all_forms_of_tb_number_of_deaths_estimated"].fillna(0) + ci["tb_hivplus_number_of_deaths_estimated"].fillna(0)
    # malaria: all-age deaths from child (1-59m) deaths; WHO: under-5s ~76% of malaria deaths in the African Region
    ci["is_ssa"] = ci.index.isin(SSA)
    u5_share = np.where(ci["is_ssa"], 0.76, 0.40)
    ci["malaria_deaths"] = ci["malaria_deaths_in_children_1_59_months_total_deaths"] / u5_share
    ci["malaria_at_risk_share"] = np.where(ci["is_ssa"], 0.95, 0.35)
    ci["malaria_pop_at_risk"] = ci["sp_pop_totl"] * ci["malaria_at_risk_share"]
    ci["malaria_cases"] = ci["sh_mlr_incd_p3"] / 1000 * ci["malaria_pop_at_risk"]
    ci["vpd_child_deaths"] = (ci["measles_deaths_in_children_1_59_months_total_deaths"].fillna(0)
                              + ci["pneumonia_deaths_in_children_1_59_months_total_deaths"].fillna(0))

    # ---------------- MOU / co-financing sheet (team-collected) ---------------- #
    if a.mou and Path(a.mou).exists():
        m = pd.read_excel(a.mou, header=None)
        names = ["country", "iso3", "us_ref", "gf_ref", "gavi_ref", "wb_ref", "oth_ref", "us_2026", "us_2027", "us_2028",
                 "us_2029", "us_2030", "gf_gc8_hiv", "gf_gc8_tb", "gf_gc8_mal", "gf_gc8_rssh", "gavi_2026_30",
                 "wb_2026_30"]
        m = m.iloc[5:, :len(names)]
        m.columns = names
        m = m[m.iso3.isin(ISO3)].set_index("iso3").drop(columns="country")
        m = m.apply(pd.to_numeric, errors="coerce")
        ci = ci.join(m.add_prefix("mou_"))
    ci.reset_index().to_csv(OUT / "country_inputs.csv", index=False)
    print(f"  country_inputs: {ci.shape}")

    # ---------------- panel + regressions ---------------- #
    print("regressions ...")
    yrs = range(2000, 2024)
    rec = dah[dah.recipient_isocode.isin(ISO3) & dah.year.between(1999, 2023)]
    byb = rec.groupby(["recipient_isocode", "year"])[list(BUCKET_TOTAL_COL.values())].sum() * 1e3
    byb.index.names = ["iso3", "year"]
    pan = byb.rename(columns={v: f"dah_{k.lower()}" for k, v in BUCKET_TOTAL_COL.items()}).reset_index()
    spp = sp[sp.iso3.isin(ISO3)][["iso3", "year", "ghes_per_cap_mean", "dah_per_cap_mean", "the_per_cap_mean"]]
    pan = pan.merge(spp, on=["iso3", "year"], how="outer").merge(gdp, on=["iso3", "year"], how="left")
    for n in ["sp_pop_totl", "sp_pop_1564_to", "sh_dyn_aids_zs", "sh_hiv_0014", "sh_hiv_artc_zs", "sh_tbs_dtec_zs",
              "sh_imm_idpt", "sp_dyn_cbrt_in", "sh_mlr_incd_p3", "sh_dyn_mort", "all_forms_of_tb_incidence_estimated"]:
        pan = pan.merge(read_ext(n).rename(columns={"value": n}), on=["iso3", "year"], how="left")
    pan = pan[pan.year.isin(yrs)].sort_values(["iso3", "year"]).reset_index(drop=True)
    pan["plhiv"] = (pan["sh_dyn_aids_zs"] / 100 * pan["sp_pop_1564_to"] * pan["iso3"].map(ci["plhiv_calibration"])
                    + pan["sh_hiv_0014"].fillna(0))
    pan["births"] = pan["sp_dyn_cbrt_in"] / 1000 * pan["sp_pop_totl"]
    g = pan.groupby("iso3")
    for b in ["hiv", "tb", "malaria", "immunization"]:      # 2-year moving average smooths lumpy disbursements
        pan[f"dah_{b}_ma"] = g[f"dah_{b}"].transform(lambda s: s.rolling(2, min_periods=1).mean())
    pan["x_hiv"] = np.log1p(pan["dah_hiv_ma"] / pan["plhiv"])                       # $ per PLHIV
    pan["x_tb"] = np.log1p(pan["dah_tb_ma"] / pan["all_forms_of_tb_incidence_estimated"])   # $ per incident case
    pan["x_imm"] = np.log1p(pan["dah_immunization_ma"] / pan["births"])             # $ per birth
    pan["x_mal"] = np.log1p(pan["dah_malaria_ma"] / pan["sp_pop_totl"])             # $ per person
    pan["ln_ghes_pc"] = np.log(pan["ghes_per_cap_mean"])
    pan["ln_gdp_pc"] = np.log(pan["gdp_pc"])
    pan["ln_mal_inc"] = np.log(pan["sh_mlr_incd_p3"].where(pan["sh_mlr_incd_p3"] > 0))
    # fiscal response: first differences in $ per capita
    pan["d_ghes_pc"] = g["ghes_per_cap_mean"].diff()
    pan["d_dah_pc"] = g["dah_per_cap_mean"].diff()
    pan["d_dah_pc_fall"] = pan["d_dah_pc"].clip(upper=0)
    pan["d_dah_pc_rise"] = pan["d_dah_pc"].clip(lower=0)
    pan["d_dah_pc_fall_l1"] = pan.groupby("iso3")["d_dah_pc_fall"].shift(1)
    pan["d_gdp_pc"] = g["gdp_pc"].diff()
    pan.to_csv(OUT / "panel.csv", index=False)

    reg = {}
    # (a) does government health spending rise when aid falls? (asymmetric, contemporaneous + 1 lag)
    reg["fiscal_replacement"] = twoway_fe(pan[pan.year >= 2001], "d_ghes_pc",
                                          ["d_dah_pc_fall", "d_dah_pc_fall_l1", "d_dah_pc_rise", "d_gdp_pc"])
    # (b) coverage dose-response (within-country), aid per person in need, controlling for GHES and GDP
    reg["hiv_art"] = twoway_fe(pan[pan.year >= 2005], "sh_hiv_artc_zs", ["x_hiv", "ln_ghes_pc", "ln_gdp_pc"])
    reg["tb_treatment"] = twoway_fe(pan[pan.year >= 2005], "sh_tbs_dtec_zs", ["x_tb", "ln_ghes_pc", "ln_gdp_pc"])
    reg["dtp3"] = twoway_fe(pan[pan.year >= 2005], "sh_imm_idpt", ["x_imm", "ln_ghes_pc", "ln_gdp_pc"])
    reg["malaria_incidence"] = twoway_fe(pan[(pan.year >= 2005) & pan.iso3.isin(SSA)], "ln_mal_inc",
                                         ["x_mal", "ln_ghes_pc", "ln_gdp_pc"])
    reg["_notes"] = {
        "fiscal_replacement": "d(GHES per capita) on falls/rises in DAH per capita; theta = -(b_fall + b_fall_l1)",
        "coverage": "coverage (percentage points) on log(1 + aid per person in need), 2-yr moving average of aid; "
                    "country and year fixed effects; SEs clustered by country. Within-country associations, not causal.",
        "baseline_years": list(BASE_YEARS),
    }
    (OUT / "regressions.json").write_text(json.dumps(reg, indent=2, default=float))
    for k, v in reg.items():
        if k.startswith("_"):
            continue
        print(f"  {k:20s} n={v['n_obs']:5d} G={v['n_countries']:3d}  " +
              "  ".join(f"{x}={v['coef'][x]:+.3f} ({v['se'][x]:.3f})" for x in v["x"]))
    print("done ->", OUT)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dah", required=True)
    p.add_argument("--spend", required=True)
    p.add_argument("--expected", required=True)
    p.add_argument("--gdp", required=True)
    p.add_argument("--mou", default=None)
    p.add_argument("--download", action="store_true")
    main(p.parse_args())
