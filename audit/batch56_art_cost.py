"""
Batch 5+6, item A1 (L-50 follow-up): ART cost per patient-year with (1) a validity test on the observed-spending measure,
(2) a floor that is a measured full delivery cost, (3) the US$50-600 gate on the final value. Read-only with respect to
the model; batch34_inputs.py --art-full56 writes the result into model_data/country_inputs.csv.

    .venv/bin/python audit/batch56_art_cost.py

Starts from audit/logic_review/batch4b_art_check.csv (Batch 4b item 1: (a) the GHCC-based full cost = site cost x
1 / (1 - asd_share); (b) observed HIV treatment spending per person on ART = total HIV spending x the country's Global
Fund GC7 treatment-and-care module share / UNAIDS people receiving ART, 2023 US$).

Rule 1 (validity of (b)). (b) uses the Global Fund module share as a proxy for the national treatment share, which is
unreliable where the Global Fund funds little of the country's HIV response. (b) is used only where the Global Fund's
share of total HIV spending is at least 10%: Global Fund HIV and TB/HIV disbursements to the country (Global Fund Data
Explorer, datasets/GlobalFund/GF_disbursements_2026-10-14.csv; the mean of the spending year and the two years around
it, because disbursements are lumpy) / total HIV spending in the spending year (ten Brink et al. 2025 appendix Table B2,
p. 8, for the Optima countries; WHO GHED dis11_usd otherwise, as in Batch 4b). Elsewhere, and where (b) is unavailable,
the cost is (a) x the WHO-region median of (b)/(a) computed over the VALID countries only (the median over all valid
countries where the region has fewer than 3).

Rule 2 (floor). The floor is the lowest measured site-level ART delivery cost in unit_cost_reference.csv: Malawi,
US$86.50 per patient-year in 2018 US$ (Rosen et al. 2021, Gates Open Research 5:177, AMBIT synthesis: conventional
facility-based care, ARVs + labs + staff + overhead at site level), inflated to 2023 US$ with the US CPI-U
(health_model.inflate: 304.702 / 251.107) = US$104.96, then x the above-site markup 1 / (1 - asd_share) = 1.818
(asd_share 0.45: KFF 2025, Gaba, Razavi, Kates & Nandakumar, 'Which PEPFAR Investments Drive HIV Outcomes?', PEPFAR
expenditure data 2018-2023, non-service delivery 47% of spending) = US$190.84. Floor and cost are then on the same
basis: a full programme cost per patient-year (site delivery cost plus above-site programme costs). The Batch 4b floor
(TLD + one viral load test, US$57) was a commodity price, not a delivery cost.

Rule 3 (gate). US$50-600 on the FINAL value, after rules 1 and 2.

Range: lo = the final value (uc_art_mult's lower end, 0.68, carries the downside); hi = the higher of (a) and the
candidate (b) or regional value, clipped to [final, 600] (reached at uc_art_mult = 1.38, as in Batch 4b).
Writes audit/logic_review/batch56_art_cost.csv with old (Batch 4b) and new values and the rule applied.
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

CHECK = ROOT / "audit" / "logic_review" / "batch4b_art_check.csv"
GF = ROOT / "datasets" / "GlobalFund" / "GF_disbursements_2026-10-14.csv"
OUT = ROOT / "audit" / "logic_review" / "batch56_art_cost.csv"
GF_MIN_SHARE = 0.10
LO, HI = 50.0, 600.0
GF_NAMES = {"Angola": "AGO", "Azerbaijan": "AZE", "Burundi": "BDI", "Benin": "BEN", "Burkina Faso": "BFA", "Bangladesh": "BGD",
            "Belize": "BLZ", "Bolivia (Plurinational State)": "BOL", "Botswana": "BWA", "Central African Republic": "CAF",
            "Côte d'Ivoire": "CIV", "Cameroon": "CMR", "Congo (Democratic Republic)": "COD", "Djibouti": "DJI",
            "Dominican Republic": "DOM", "Egypt": "EGY", "Ethiopia": "ETH", "Fiji": "FJI", "Ghana": "GHA", "Guinea": "GIN",
            "Gambia": "GMB", "Guatemala": "GTM", "Guyana": "GUY", "Honduras": "HND", "Haiti": "HTI", "Indonesia": "IDN",
            "India": "IND", "Iraq": "IRQ", "Jamaica": "JAM", "Jordan": "JOR", "Kenya": "KEN", "Kyrgyzstan": "KGZ",
            "Cambodia": "KHM", "Lao (Peoples Democratic Republic)": "LAO", "Liberia": "LBR", "Libya": "LBY", "Lesotho": "LSO",
            "Moldova": "MDA", "Madagascar": "MDG", "Mali": "MLI", "Mongolia": "MNG", "Mozambique": "MOZ", "Mauritius": "MUS",
            "Malawi": "MWI", "Namibia": "NAM", "Niger": "NER", "Nigeria": "NGA", "Nicaragua": "NIC", "Nepal": "NPL",
            "Pakistan": "PAK", "Philippines": "PHL", "Papua New Guinea": "PNG", "Rwanda": "RWA", "Senegal": "SEN",
            "Sierra Leone": "SLE", "El Salvador": "SLV", "Somalia": "SOM", "South Sudan": "SSD", "Sao Tome and Principe": "STP",
            "Eswatini": "SWZ", "Togo": "TGO", "Tajikistan": "TJK", "Timor-Leste": "TLS", "Tanzania (United Republic)": "TZA",
            "Uganda": "UGA", "Venezuela (Bolivarian Republic)": "VEN", "Viet Nam": "VNM", "South Africa": "ZAF",
            "Zambia": "ZMB", "Zimbabwe": "ZWE"}


def floor_value(asd_share: float) -> tuple[float, str]:
    ref = pd.read_csv(hm.UC_REF_FILE)
    r = ref[ref.kind == "art_site_cost"].copy()
    r["usd2023"] = [hm.inflate(v, y) for v, y in zip(r.value, r.cost_year)]
    low = r.loc[r.usd2023.idxmin()]
    markup = 1.0 / (1.0 - asd_share)
    return float(low.usd2023 * markup), (f"{low.key} site cost US${low.value:.2f} ({int(low.cost_year)} US$; {low.source}) = "
                                        f"US${low.usd2023:.2f} in 2023 US$ x above-site markup {markup:.3f} = US${low.usd2023 * markup:.2f}")


def main():
    P = hm.draw_params(hm.load_params(), 0)
    asd = float(P["asd_share"][0])
    FLOOR, floor_src = floor_value(asd)
    t = pd.read_csv(CHECK).set_index("iso3")
    gf = pd.read_csv(GF, usecols=["GeographyName1", "GrantComponent1", "DisbursementDate", "DisbursementAmount_ReferenceRate"])
    gf["year"] = pd.to_datetime(gf.DisbursementDate, format="%d-%b-%Y").dt.year
    gf = gf[gf.GrantComponent1.isin(["HIV", "TB/HIV"])]
    gf["iso3"] = gf.GeographyName1.map(GF_NAMES)
    gfy = gf.dropna(subset=["iso3"]).groupby(["iso3", "year"]).DisbursementAmount_ReferenceRate.sum()
    for iso in t.index:
        y = t.loc[iso, "spend_year"]
        if pd.isna(y):
            continue
        vals = [gfy.get((iso, int(y) + k), np.nan) for k in (-1, 0, 1)]
        vals = [v for v in vals if not np.isnan(v)]
        t.loc[iso, "gf_hiv_disb_3yr"] = np.mean(vals) if vals else 0.0
        t.loc[iso, "gf_share_total_hiv"] = t.loc[iso, "gf_hiv_disb_3yr"] / t.loc[iso, "total_hiv_spend_usd"]
    has_b = t.observed_treat_spend_pp_2023.notna()
    t["b_valid"] = has_b & (t.gf_share_total_hiv >= GF_MIN_SHARE)
    ratio = (t.observed_treat_spend_pp_2023 / t.full_cost_now).where(t.b_valid)
    reg_med = ratio.groupby(t.who_region).median()
    reg_n = ratio.groupby(t.who_region).count()
    all_med = float(ratio.median())
    t["old_cost"] = t.final_cost
    for iso in t.index:
        a_ = float(t.loc[iso, "full_cost_now"])
        if t.loc[iso, "b_valid"]:
            cand = float(t.loc[iso, "observed_treat_spend_pp_2023"])
            rule = f"rule 1: observed spending valid (Global Fund share of HIV spending {t.loc[iso, 'gf_share_total_hiv']:.2f} >= 0.10); min(GHCC-based {a_:.0f}, observed {cand:.0f} from {t.loc[iso, 'spend_source']})"
        else:
            reg = t.loc[iso, "who_region"]
            rr, n = reg_med.get(reg, np.nan), int(reg_n.get(reg, 0))
            lab = f"WHO region {reg}, {n} valid countries"
            if pd.isna(rr) or n < 3:
                rr, lab = all_med, f"all {int(t.b_valid.sum())} valid countries"
            why = (f"observed spending invalid (Global Fund share {t.loc[iso, 'gf_share_total_hiv']:.2f} < 0.10)" if has_b[iso]
                   else "no observed spending")
            cand = a_ * float(rr)
            rule = f"rule 1: {why}; GHCC-based {a_:.0f} x median observed/GHCC ratio {float(rr):.2f} ({lab})"
        v = min(a_, cand)
        if v < FLOOR:
            rule += f"; rule 2: floored at the lowest measured full delivery cost {FLOOR:.0f}"
            v = FLOOR
        g = float(np.clip(v, LO, HI))
        if g != v:
            rule += "; rule 3: gate 50-600 applied"
        t.loc[iso, "new_cost"] = g
        t.loc[iso, "new_lo"] = g
        t.loc[iso, "new_hi"] = float(np.clip(max(a_, cand), g, HI))
        t.loc[iso, "new_source"] = rule
        t.loc[iso, "candidate_before_floor"] = min(a_, cand)
    t["floor_usd"] = FLOOR
    t["changed"] = ~np.isclose(t.new_cost, t.old_cost)
    t.to_csv(OUT)
    pd.set_option("display.width", 250)
    print(f"floor: {floor_src}")
    print(f"observed spending available {int(has_b.sum())}, valid {int(t.b_valid.sum())}, invalid: {list(t.index[has_b & ~t.b_valid])}")
    print("regional median (b)/(a), valid countries:", {k: (round(float(v), 2), int(reg_n[k])) for k, v in reg_med.items()}, "all:", round(all_med, 2))
    print(f"floored: {list(t.index[t.new_source.str.contains('rule 2')])}")
    ch = t[t.changed]
    print(f"\n{len(ch)} countries changed:")
    print(ch[["old_cost", "new_cost", "candidate_before_floor", "gf_share_total_hiv", "new_source"]].round(2).to_string())
    print(f"\nnew cost: median {t.new_cost.median():.0f}, min {t.new_cost.min():.0f}, max {t.new_cost.max():.0f}")


if __name__ == "__main__":
    main()
