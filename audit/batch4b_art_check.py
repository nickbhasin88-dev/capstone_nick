"""
Batch 4b, item 1 (L-50): the ART cost each country uses now, and the observed HIV treatment spending per person on ART.
Read-only with respect to the model.

    .venv/bin/python audit/batch4b_art_check.py

Observed treatment spending per person on ART = total HIV spending x treatment-and-care share / people receiving ART:
  total HIV spending: ten Brink et al. 2025 appendix Table B2 (p. 8) for its countries that are modelled (15; most
      recent GAM year, nominal US$); otherwise WHO GHED `dis11_usd` (HIV/AIDS and other STDs, million current US$,
      latest year with a value; datasets/WHO_GHED);
  treatment-and-care share: the country's Global Fund GC7 module share ("Treatment, care and support";
      `unspec_hiv_treatment` in country_inputs.csv, Batch 3+4 item 2; a WHO-region median where the country has no grant);
  people receiving ART: UNAIDS AIDSinfo 2026 estimates, "People receiving antiretroviral therapy", All ages, unrounded
      `Data value`, same year as the spending (datasets/UNAIDS_2026).
Nominal US$ of the spending year are put in 2023 US$ with the US CPI-U annual averages (BLS: 2015 237.017, 2016 240.007,
2017 245.120, then health_model.CPI_U). The model's full cost = site cost x 1 / (1 - asd_share) x uc_art_mult.
Item 2 rule (columns final_cost, final_lo, final_hi, final_source): ART cost per patient-year = the lower of (a) the
GHCC-based full cost and (b) the observed treatment spending per person on ART; where (b) is unavailable, (a) x the
median (b)/(a) ratio of the model countries in the same WHO region (the overall median if the region has none);
floor = the higher of (i) the country's ARV drugs plus one viral load test a year (Goals cross-check, 2026-10-30:
Stover HIV unit cost database, datasets/Goals/"Unit costs 11april2025.xlsx", tab UCdatabase, items "Adult ARVs" and
"Viral load test", in the US$ of each row's Year put in 2023 US$ with CPI-U; Stover et al. 2026, PLOS Glob Public
Health 6(10):e0007360; github.com/JGStover/HIV-Unit-Costs; for South Africa the ARV part is the national tender price,
which is lower, see ZAF_TLD) and (ii) the global first-line price used before (TLD "under US$45 per person, per year",
Global Fund news release 30 August 2023; viral load "global access price from Roche of US$9.40 per test", CHAI, Case
Study: Viral Load Access, 2015; 9.40 in 2015 US$ x CPI-U to 2023 = 12.08; 57.08 in 2023 US$), kept so that no
country's cost falls (it binds only for South Africa); gate US$50-600 on the final value.
Range: lo = the final value, hi = the higher of (a) and (b) capped at 600 (the draws also run below the central through
uc_art_mult's lower end, 0.68, from the spread of the cost studies).
Writes audit/logic_review/batch4b_art_check.csv.
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

CPI = {2015: 237.017, 2016: 240.007, 2017: 245.120, **hm.CPI_U, 2024: 313.689, 2025: 321.943}   # BLS CPI-U (FRED CPIAUCNS)
UCDB = ROOT / "datasets" / "Goals" / "Unit costs 11april2025.xlsx"
# South Africa: NDoH contract HP13-2025ARV (1 December 2025 - 30 November 2028), Contract Circular Version 2 (Addendum
# 5, 4 May 2026, health.gov.za/wp-content/uploads/2026/05/HP13-2025ARV_Add-5-Replacement-Contract-Circular_4-May-2026.pdf),
# items 13 and 23, dolutegravir 50 mg / lamivudine 300 mg / tenofovir 300 mg tablet (TLD): every award as
# (tablets per pack, price in rand per pack, packs awarded). "All prices are inclusive of 15 % VAT" and "on a delivered
# basis" (circular, 1.3-1.4). Rand -> US$ at the 2025 average (17.8782 ZAR per US$, Federal Reserve H.10, FRED AEXSFUS)
ZAF_TLD = [(84, 156.00, 4_901_521), (90, 160.00, 4_778_740), (84, 160.68, 4_756_123), (84, 168.99, 4_668_884),
           (84, 170.49, 4_623_649), (90, 175.00, 4_307_005), (84, 175.95, 4_274_695),
           (28, 56.86, 13_822_564), (28, 55.90, 16_470_472), (28, 56.22, 16_166_813), (30, 56.77, 16_081_788),
           (28, 62.40, 15_923_885), (30, 63.10, 14_867_152), (28, 63.25, 14_089_784), (30, 64.04, 14_041_199)]
ZAF_VAT, ZAF_ZAR_PER_USD, ZAF_PRICE_YEAR = 0.15, 17.8782, 2025
B2 = {"AZE": (2023, 14_770_145), "KHM": (2022, 31_565_694), "CIV": (2022, 180_080_436), "DOM": (2022, 72_921_868),
      "SWZ": (2019, 102_113_481), "KEN": (2022, 764_057_567), "KGZ": (2023, 12_523_725), "MWI": (2022, 259_699_300),
      "MDA": (2023, 10_625_628), "MNG": (2021, 2_474_731), "MOZ": (2019, 557_780_695), "ZAF": (2023, 1_863_907_174),
      "TJK": (2023, 3_503_630), "UGA": (2020, 538_920_127), "ZWE": (2023, 310_440_134)}
OUT = ROOT / "audit" / "logic_review" / "batch4b_art_check.csv"


def inflate(v, y):
    return v * CPI[2023] / CPI[int(y)]


def zaf_tld_per_year() -> float:
    """South Africa's TLD price per patient-year, 2023 US$: volume-weighted price per tablet over every HP13-2025ARV
    award, x 365, without VAT (the database prices carry no tax), in US$ at the 2025 rate, then CPI-U to 2023."""
    rand_per_tab = sum(p * q for _, p, q in ZAF_TLD) / sum(n * q for n, _, q in ZAF_TLD)
    return inflate(rand_per_tab * 365 / (1 + ZAF_VAT) / ZAF_ZAR_PER_USD, ZAF_PRICE_YEAR)


def art_minimum(isos) -> pd.DataFrame:
    """Each country's ARV drugs + one viral load test per patient-year, 2023 US$ (the floor), with its source. ARVs and
    viral load from the Stover database (one row per country and item), each row in the US$ of its Year; South Africa's
    ARVs from its national tender where that is lower."""
    import openpyxl
    wb = openpyxl.load_workbook(UCDB, data_only=True, read_only=True)
    rows = list(wb["UCdatabase"].iter_rows(values_only=True))
    db = pd.DataFrame([r[:8] for r in rows[1:]], columns=[str(h) for h in rows[0][:8]]).dropna(subset=["ISO", "Item"])
    db = db[db.Item.str.strip().isin(["Adult ARVs", "Viral load test"])].drop_duplicates(["ISO", "Item"])
    db["usd_2023"] = [inflate(float(c), y) for c, y in zip(db.Cost, db.Year)]
    v = db.pivot(index="ISO", columns="Item", values="usd_2023")
    out = []
    for iso in isos:
        arv, vl = float(v.loc[iso, "Adult ARVs"]), float(v.loc[iso, "Viral load test"])
        r = {"iso3": iso, "ucdb_arv_2023": arv, "ucdb_vl_2023": vl, "national_arv_2023": np.nan}
        src = "Stover database ARVs + viral load"
        if iso == "ZAF":
            r["national_arv_2023"] = zaf_tld_per_year()
            if r["national_arv_2023"] < arv:
                arv, src = r["national_arv_2023"], "NDoH tender HP13-2025ARV TLD + Stover database viral load"
        r["min_cost_2023"], r["min_source"] = arv + vl, src
        out.append(r)
    return pd.DataFrame(out).set_index("iso3")


def main():
    I, P = hm.load_inputs(), hm.load_params()
    ci = I["ci"]
    iso_all = sorted(set(I["lines"].iso3))
    Pc = hm.draw_params(P, 0)
    markup = 1.0 / (1.0 - float(Pc["asd_share"][0]))
    # (a) the cost now used
    a = pd.read_csv(ROOT / "audit" / "logic_review" / "batch34_art_costs.csv").set_index("iso3")
    g = pd.read_excel(ROOT / "datasets" / "GHCC_UCSR" / "GHCC_UCSR_HIV_ART.xlsx")
    g["price_year"] = pd.to_numeric(g["Reported Currency Year"], errors="coerce").fillna(g["Reference Year"])
    ok = (g["Output unit"].isin(["Per Person Treated Per Year", "Per Patient Year", "Per Person Served Per Year",
                                 "Per Person Seen In Year On ART"]) & (g["Perspective"] == "Provider")
          & pd.to_numeric(g["Mean Unit Cost"], errors="coerce").notna()
          & ~g["Above Service Costs Included"].astype(str).str.startswith("Some") & (g.price_year >= 2015))
    g = g[ok]
    cmap = {"Côte d'Ivoire": "CIV", "Eswatini": "SWZ", "Ghana": "GHA", "India": "IND", "Indonesia": "IDN", "Kenya": "KEN",
            "Malawi": "MWI", "Nigeria": "NGA", "South Africa": "ZAF", "Tanzania, United Republic of": "TZA",
            "Uganda": "UGA", "Zambia": "ZMB"}
    g["iso3"] = g.Country.map(cmap)
    rec = g.groupby("iso3").agg(ghcc_records=("uc" if "uc" in g else "Mean Unit Cost", "size"),
                                price_years=("price_year", lambda s: "/".join(sorted({str(int(x)) for x in s}))),
                                kinds=("Economic / Financial", lambda s: "/".join(sorted(set(s)))),
                                settings=("Ownership", lambda s: "/".join(sorted({str(x) for x in s}))))
    # (b) observed treatment spending per person on ART
    u = pd.read_csv(ROOT / "datasets" / "UNAIDS_2026" / "UNAIDS_Estimates_2026.csv", low_memory=False,
                    usecols=["Indicator", "Subgroup", "Area ID", "Area Level", "Time Period", "Data value"])
    u = u[(u["Area Level"] == 2) & (u.Indicator == "People receiving antiretroviral therapy") & (u.Subgroup == "All ages")]
    u["Data value"] = pd.to_numeric(u["Data value"], errors="coerce")
    art = u.dropna(subset=["Data value"]).set_index(["Area ID", "Time Period"])["Data value"]
    gh = pd.read_excel(ROOT / "datasets" / "WHO_GHED" / "GHED_data_2026-10-14.xlsx", sheet_name="Data",
                       usecols=["code", "year", "dis11_usd"]).dropna(subset=["dis11_usd"])
    gh = gh[(gh.dis11_usd > 0)].sort_values("year").groupby("code").tail(1).set_index("code")
    rows = []
    for iso in iso_all:
        row = ci.loc[iso]
        site = float(row["art_site_cost"])
        full = site * markup
        r = {"iso3": iso, "site_cost_2023": site, "full_cost_now": full, "source": row["art_site_cost_source"],
             "own_study": str(row["art_site_cost_source"]).startswith("own"),
             "gate_site_50_600": 50 <= site <= 600, "gate_full_50_600": 50 <= full <= 600,
             "ghcc_records": int(rec.ghcc_records.get(iso, 0)), "price_years": rec.price_years.get(iso, ""),
             "cost_kind": ("economic x 0.981 (GHCC) and financial (Rosen 2021)" if iso in rec.index else
                           "financial (Rosen 2021)" if iso in ("LSO", "ZMB", "ZWE", "MWI", "UGA") and str(row["art_site_cost_source"]).startswith("own") else "fallback"),
             "setting": rec.settings.get(iso, "")}
        if iso in B2:
            yr, tot = B2[iso]
            r.update({"spend_source": f"Optima Table B2 ({yr})", "spend_year": yr, "total_hiv_spend_usd": tot})
        elif iso in gh.index:
            yr = int(gh.loc[iso, "year"])
            r.update({"spend_source": f"WHO GHED dis11_usd ({yr})", "spend_year": yr, "total_hiv_spend_usd": float(gh.loc[iso, "dis11_usd"]) * 1e6})
        else:
            r.update({"spend_source": "", "spend_year": np.nan, "total_hiv_spend_usd": np.nan})
        r["treatment_share"] = float(row["unspec_hiv_treatment"])
        r["treatment_share_source"] = row["unspec_hiv_source"]
        if r["spend_source"]:
            yr = int(r["spend_year"])
            n_art = art.get((iso, yr), np.nan)
            r["people_on_art_unaids"] = n_art
            if n_art and not np.isnan(n_art) and n_art > 0:
                r["observed_treat_spend_pp_nominal"] = r["total_hiv_spend_usd"] * r["treatment_share"] / n_art
                r["observed_treat_spend_pp_2023"] = inflate(r["observed_treat_spend_pp_nominal"], yr)
                r["total_spend_pp_2023"] = inflate(r["total_hiv_spend_usd"] / n_art, yr)
        r["ratio_ghcc_to_observed"] = r["full_cost_now"] / r["observed_treat_spend_pp_2023"] if r.get("observed_treat_spend_pp_2023") else np.nan
        rows.append(r)
    t = pd.DataFrame(rows).set_index("iso3")
    t["who_region"] = ci.who_region.reindex(t.index)
    # ---- item 2 rule ----
    FLOOR = 45.0 + inflate(9.40, 2015)
    mins = art_minimum(t.index)
    t = t.join(mins)
    ratio_ba = (t.observed_treat_spend_pp_2023 / t.full_cost_now)
    reg_med = ratio_ba.groupby(t.who_region).median()
    all_med = float(ratio_ba.median())
    for iso in t.index:
        a_ = float(t.loc[iso, "full_cost_now"])
        b_ = t.loc[iso, "observed_treat_spend_pp_2023"]
        if pd.notna(b_):
            cand, src = float(b_), f"min(GHCC-based {a_:.0f}, observed {float(b_):.0f} from {t.loc[iso, 'spend_source']})"
        else:
            rr = reg_med.get(t.loc[iso, "who_region"], np.nan)
            lab = f"WHO region {t.loc[iso, 'who_region']}"
            if pd.isna(rr):
                rr, lab = all_med, "all model countries"
            cand, src = a_ * float(rr), f"no observed spending: GHCC-based {a_:.0f} x median observed/GHCC ratio {float(rr):.2f} ({lab})"
        v = min(a_, cand)
        note = ""
        cmin = float(t.loc[iso, "min_cost_2023"])
        if v < max(FLOOR, cmin):
            if cmin > FLOOR:
                note = f"; floored at the country's ARVs + viral load {cmin:.0f} ({t.loc[iso, 'min_source']})"
            else:
                note = f"; floored at drugs + viral load {FLOOR:.0f}"
            v = max(FLOOR, cmin)
        v = float(np.clip(v, 50.0, 600.0))
        if v == 600.0 or v == 50.0:
            note += "; gate 50-600 applied"
        t.loc[iso, "final_cost"] = v
        t.loc[iso, "final_lo"] = v
        t.loc[iso, "final_hi"] = float(np.clip(max(a_, cand), v, 600.0))
        t.loc[iso, "final_source"] = src + note
    t["floor_usd"] = FLOOR
    print(f"\nitem 2: floor {FLOOR:.2f}; final cost median {t.final_cost.median():.0f} (min {t.final_cost.min():.0f}, max {t.final_cost.max():.0f}); "
          f"floored: {list(t.index[t.final_source.str.contains('floored')])}; from observed: {int(t.final_source.str.startswith('min(').sum())}; "
          f"GHCC lower than observed: {int(((t.final_cost == t.full_cost_now) & t.final_source.str.startswith('min(')).sum())}")
    t.to_csv(OUT)
    pd.set_option("display.width", 250)
    print(f"countries: {len(t)}; own study {int(t.own_study.sum())}; site gate fails {int((~t.gate_site_50_600).sum())}; "
          f"full-cost gate fails {int((~t.gate_full_50_600).sum())}: {list(t.index[~t.gate_full_50_600])}")
    have = t.dropna(subset=["observed_treat_spend_pp_2023"])
    print(f"observed spending per person on ART available for {len(have)} countries (Optima {int(have.spend_source.str.startswith('Optima').sum())}, GHED {int(have.spend_source.str.startswith('WHO').sum())})")
    print(f"ratio GHCC full cost / observed: median {have.ratio_ghcc_to_observed.median():.2f}, IQR {have.ratio_ghcc_to_observed.quantile(.25):.2f}-{have.ratio_ghcc_to_observed.quantile(.75):.2f}; "
          f"above 1 in {int((have.ratio_ghcc_to_observed > 1).sum())} of {len(have)}")
    print(have.groupby("who_region").ratio_ghcc_to_observed.median().round(2).to_dict())
    print(t.loc[[i for i in B2 if i in t.index], ["full_cost_now", "total_spend_pp_2023", "treatment_share", "observed_treat_spend_pp_2023", "ratio_ghcc_to_observed", "people_on_art_unaids"]].round(2).to_string())


if __name__ == "__main__":
    main()
