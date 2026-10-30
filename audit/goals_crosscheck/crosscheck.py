"""Read-only cross-check of the model's HIV unit costs against UNAIDS Goals / Resource Needs Model sources.

Inputs (not committed, datasets/goals/):
  - "Goals Lite (1) (1).xlsx"  (Malawi Goals Lite: Dashboard, Calculations, GAM, CEA tabs)
  - "Unit costs 11april2025.xlsx" (Stover HIV unit cost database, tab UCdatabase)
Model values come from health_model.unit_costs() with central parameters, so nothing is re-typed.
Writes the CSVs next to this file. Changes no model code, parameter or output.

Run from the repo root:  python audit/goals_crosscheck/crosscheck.py
"""
from pathlib import Path
import sys

import numpy as np
import openpyxl
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import health_model as hm  # noqa: E402

OUT = Path(__file__).resolve().parent
GOALS = ROOT / "datasets/goals/Goals Lite (1) (1).xlsx"
UCDB = ROOT / "datasets/goals/Unit costs 11april2025.xlsx"

# US CPI-U annual averages (BLS CUUR0000SA0): the model's own table (health_model.CPI_U) plus the years it lacks
CPI_U = {**hm.CPI_U, 2016: 240.007, 2017: 245.120, 2024: 313.689}
VISITS = (2, 4)          # ART clinic visits a year: WHO differentiated service delivery, 3- to 6-monthly (assumption)
LO_RATIO, HI_RATIO = 0.5, 2.0


def to2023(value, year):
    """value in `year` US$ -> 2023 US$ (US CPI-U). NaN when the year is unknown."""
    try:
        return value * CPI_U[2023] / CPI_U[int(year)]
    except (KeyError, TypeError, ValueError):
        return np.nan


def model_costs():
    """Central unit costs per country (2023 US$) straight from the model."""
    inputs, ptab = hm.load_inputs(), hm.load_params()
    Pc = hm.draw_params(ptab, 0)
    ci = inputs["ci"]
    rows = []
    for iso, r in ci.iterrows():
        uc = hm.unit_costs(r, Pc)
        inc = r["sh_hiv_incd_tl"] / r["sp_pop_totl"] * 1000
        rows.append({"iso3": iso, "ours_art_full": float(uc["hiv_art"][0]), "ours_art_site": r["art_site_cost"],
                     "ours_art_source": r["art_cost_full_source"], "ours_pmtct": float(uc["hiv_pmtct"][0]),
                     "ours_cpia": float(uc["hiv_prev"][0]), "incidence_per_1000": inc,
                     "on_art": r["plhiv"] * r["sh_hiv_artc_zs"] / 100})
    return pd.DataFrame(rows).set_index("iso3"), float(Pc["cpia_ref"][0])


def ucdb():
    wb = openpyxl.load_workbook(UCDB, data_only=True, read_only=True)
    rows = list(wb["UCdatabase"].iter_rows(values_only=True))
    df = pd.DataFrame([r[:8] for r in rows[1:]], columns=[str(h) for h in rows[0][:8]]).dropna(subset=["ISO", "Item"])
    df["Item"] = df["Item"].str.strip()
    df["cost_2023"] = [to2023(c, y) for c, y in zip(df.Cost, df.Year)]
    return df


def pick(db, iso, item):
    """(cost in 2023 US$, original cost, year, source) for one country x item; the first row if there are several."""
    s = db[(db.ISO == iso) & (db.Item == item)]
    if s.empty:
        return np.nan, np.nan, None, None
    r = s.iloc[0]
    return r.cost_2023, r.Cost, r.Year, r.Source


def flag(ratio_lo, ratio_hi):
    """ratio_lo = ours / their highest, ratio_hi = ours / their lowest: flag if the whole range is outside 0.5-2x."""
    if np.isnan(ratio_lo):
        return "no comparator"
    if ratio_lo > HI_RATIO:
        return "ours > 2x"
    if ratio_hi < LO_RATIO:
        return "ours < 0.5x"
    return "ok"


def check_a(ours, db):
    names = db.drop_duplicates("ISO").set_index("ISO")["Country"]
    art, pm = [], []
    for iso, o in ours.iterrows():
        arv, arv0, arv_y, _ = pick(db, iso, "Adult ARVs")
        vl, *_ = pick(db, iso, "Viral load test")
        cd4, *_ = pick(db, iso, "CD4 test")
        cre, *_ = pick(db, iso, "Creatinine test")
        visit, *_ = pick(db, iso, "Routine visit cost")
        sd, *_ = pick(db, iso, "ART service delivery")
        visit0 = 0.0 if np.isnan(visit) else visit
        lo = arv + vl + VISITS[0] * visit0                          # ARVs + 1 VL + 2 visits
        hi = arv + vl + cd4 + cre + VISITS[1] * visit0              # + CD4 + creatinine + 4 visits
        sd_total = arv + sd if not np.isnan(sd) else np.nan         # ARVs + the database's ART service delivery
        art.append({"iso3": iso, "country": names.get(iso), "ours_art_full_2023": o.ours_art_full,
                    "ours_art_site_2023": o.ours_art_site, "ours_source": o.ours_art_source,
                    "ucdb_adult_arvs_2023": arv, "ucdb_viral_load_2023": vl, "ucdb_cd4_2023": cd4,
                    "ucdb_creatinine_2023": cre, "ucdb_visit_2023": visit, "visit_missing": np.isnan(visit),
                    "theirs_bundle_lo_2023": lo, "theirs_bundle_hi_2023": hi,
                    "theirs_arv_plus_service_delivery_2023": sd_total,
                    "ratio_full_vs_hi": o.ours_art_full / hi, "ratio_full_vs_lo": o.ours_art_full / lo,
                    "ratio_site_vs_hi": o.ours_art_site / hi, "ratio_site_vs_lo": o.ours_art_site / lo,
                    "ratio_full_vs_service_delivery": o.ours_art_full / sd_total,
                    "flag_full": flag(o.ours_art_full / hi, o.ours_art_full / lo),
                    "flag_site": flag(o.ours_art_site / hi, o.ours_art_site / lo),
                    "concept": "ours = full programme cost per patient-year (site x 1/(1-0.45), capped at observed "
                               "treatment spend); theirs = commodities + labs + CHOICE visit cost per patient-year, "
                               "no above-site costs: partial match"})
        # PMTCT: the database's PMTCT row where present, and a per-woman-year bundle built from its components
        p, p0, py, psrc = pick(db, iso, "PMTCT")
        hs, *_ = pick(db, iso, "HIV/syphlis for pregnant women")
        eid, *_ = pick(db, iso, "Early infant diagnosis")
        bundle = hs + eid + arv + vl + VISITS[1] * visit0
        pm.append({"iso3": iso, "country": names.get(iso), "ours_pmtct_2023": o.ours_pmtct,
                   "ucdb_pmtct_raw": p0, "ucdb_pmtct_year": py, "ucdb_pmtct_2023": p, "ucdb_pmtct_source": psrc,
                   "ratio_vs_ucdb_pmtct": o.ours_pmtct / p,
                   "flag_vs_ucdb_pmtct": flag(o.ours_pmtct / p, o.ours_pmtct / p),
                   "theirs_bundle_2023": bundle, "ratio_vs_bundle": o.ours_pmtct / bundle,
                   "flag_vs_bundle": flag(o.ours_pmtct / bundle, o.ours_pmtct / bundle),
                   "concept_ucdb_pmtct": "unit not stated in the database (per woman? per programme client?): "
                                         "concept uncertain",
                   "concept_bundle": "both per HIV+ pregnant woman per year incl. her ART; bundle = HIV/syphilis test "
                                     "+ EID + 1 year adult ARVs + 1 VL + 4 visits, no above-site costs: partial match"})
    return pd.DataFrame(art), pd.DataFrame(pm)


def goals_lite():
    wb = openpyxl.load_workbook(GOALS, data_only=True)
    return wb["GAM"], wb["Dashboard"], wb["Calculations"], wb["CEA"]


def check_b(ours, gam, dash):
    v = lambda c: float(gam[c].value or 0)                       # noqa: E731
    adults, kids = float(dash["C3"].value), float(dash["C4"].value)
    arv_adult, arv_ped = v("W8"), v("W12")                       # 1.2.1 adult ART (all ARVs), 1.2.2 paediatric ARVs
    treat = v("W2") - v("W3")                                    # 1 Treatment, care & support minus 1.1 testing
    total = v("W159")                                            # TOTAL GRAND
    deflator = CPI_U[2023] / CPI_U[2024]
    on_art_model = ours.loc["MWI", "on_art"]
    rows = []
    for denom_label, denom in (("Goals Lite on ART (920,000 adults + 27,000 children)", adults + kids),
                               ("model: UNAIDS PLHIV x ART coverage", on_art_model)):
        rows += [
            {"measure": "ARV drugs per person on ART (lower bound)", "denominator": denom_label,
             "numerator_2024_usd": arv_adult + arv_ped, "people_on_art": denom,
             "per_person_2024": (arv_adult + arv_ped) / denom},
            {"measure": "Treatment, care & support (excl. testing) per person on ART", "denominator": denom_label,
             "numerator_2024_usd": treat, "people_on_art": denom, "per_person_2024": treat / denom},
            {"measure": "Total HIV spending per person on ART (upper bound)", "denominator": denom_label,
             "numerator_2024_usd": total, "people_on_art": denom, "per_person_2024": total / denom},
        ]
    df = pd.DataFrame(rows)
    df["per_person_2023"] = df.per_person_2024 * deflator
    df["ours_art_full_2023"] = ours.loc["MWI", "ours_art_full"]
    df["ratio_ours_to_bound"] = df.ours_art_full_2023 / df.per_person_2023
    df["goals_lite_adult_art_unit_cost_2024"] = float(dash["D3"].value)
    return df


def check_c(ours, cpia_ref, calc, cea):
    mwi = ours.loc["MWI", "ours_cpia"]
    rows = []
    for r in range(3, 25):
        name, val = cea[f"E{r}"].value, cea[f"G{r}"].value
        if name and val is not None:
            rows.append({"source": "CEA tab (Goals/RNM, 2024 -> 2030 scale-up)", "intervention": name.strip(),
                         "infections_averted": cea[f"F{r}"].value, "cost_per_infection_averted": float(val)})
    for r in range(27, 36):
        rows.append({"source": "Calculations tab (Goals Lite, coverage halved, 2026-2030)",
                     "intervention": calc[f"A{r}"].value, "infections_averted": None,
                     "cost_per_infection_averted": float(calc[f"B{r}"].value)})
    df = pd.DataFrame(rows)
    df["ours_mwi"] = mwi
    df["ours_below_theirs"] = mwi < df.cost_per_infection_averted
    # infection-weighted average of the CEA tab (total cost / total infections averted), prevention only and all
    cea_rows = df[df.source.str.startswith("CEA")]
    prev = cea_rows[~cea_rows.intervention.str.startswith("ART")]
    wavg = lambda d: (d.cost_per_infection_averted * d.infections_averted).sum() / d.infections_averted.sum()  # noqa
    meta = {"cpia_ref": cpia_ref, "mwi_incidence_per_1000": ours.loc["MWI", "incidence_per_1000"], "ours_mwi": mwi,
            "cea_weighted_prevention": wavg(prev), "cea_weighted_all": wavg(cea_rows),
            "cea_n_above_ours": int((cea_rows.cost_per_infection_averted > mwi).sum()), "cea_n": len(cea_rows)}
    # Calculations tab, pooled over the prevention programmes it halves (row 11 = money saved 2025-30, row 10 = extra
    # infections): condoms (AO, E), key populations (AQ, G), SBCC (AS, I), VMMC (AT, J). PrEP (AR, H) is a scale-up
    # there, not a cut, so it is left out
    pairs = [("AO", "E"), ("AQ", "G"), ("AS", "I"), ("AT", "J")]
    saved = [float(calc[f"{c}11"].value) for c, _ in pairs]
    extra = [float(calc[f"{i}10"].value) for _, i in pairs]
    meta["calc_pooled_prevention_cut"] = sum(saved) / sum(extra)
    meta["calc_pooled_prevention_cut_excl_condoms"] = sum(saved[1:]) / sum(extra[1:])
    pd.DataFrame([meta]).to_csv(OUT / "check_c_summary.csv", index=False)
    return df, meta


def main():
    for f in (GOALS, UCDB):
        if not f.exists():
            sys.exit(f"missing input: {f}")
    ours, cpia_ref = model_costs()
    db = ucdb()
    art, pm = check_a(ours, db)
    art.to_csv(OUT / "check_a_art.csv", index=False)
    pm.to_csv(OUT / "check_a_pmtct.csv", index=False)
    gam, dash, calc, cea = goals_lite()
    b = check_b(ours, gam, dash)
    b.to_csv(OUT / "check_b_malawi_bounds.csv", index=False)
    c, meta = check_c(ours, cpia_ref, calc, cea)
    c.to_csv(OUT / "check_c_cost_per_infection.csv", index=False)
    ours[["ours_cpia", "incidence_per_1000"]].to_csv(OUT / "ours_cpia_by_country.csv")

    pd.set_option("display.width", 220)
    print("A ART flags (full):", art.flag_full.value_counts().to_dict())
    print("A ART flags (site):", art.flag_site.value_counts().to_dict())
    print(art[["iso3", "ours_art_full_2023", "ours_art_site_2023", "theirs_bundle_lo_2023", "theirs_bundle_hi_2023",
               "ratio_full_vs_hi", "flag_full", "flag_site"]].round(2).to_string(index=False))
    print(art.dropna(subset=["theirs_arv_plus_service_delivery_2023"])[
        ["iso3", "ours_art_full_2023", "theirs_arv_plus_service_delivery_2023", "ratio_full_vs_service_delivery"]])
    print(pm.dropna(subset=["ucdb_pmtct_2023"])[["iso3", "ucdb_pmtct_raw", "ucdb_pmtct_year", "ucdb_pmtct_2023",
                                                  "ratio_vs_ucdb_pmtct", "flag_vs_ucdb_pmtct"]].round(2))
    print("PMTCT bundle flags:", pm.flag_vs_bundle.value_counts().to_dict(),
          "bundle range", pm.theirs_bundle_2023.min().round(1), pm.theirs_bundle_2023.median().round(1),
          pm.theirs_bundle_2023.max().round(1))
    print(b.round(2).to_string(index=False))
    print(meta)
    print(c.round(0).to_string(index=False))
    print("ours cpia across countries:", ours.ours_cpia.describe().round(0).to_dict())


if __name__ == "__main__":
    main()
