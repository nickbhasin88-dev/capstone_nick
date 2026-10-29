"""
Phase 3 of Batch 3+4: reconciliation with Optima for the 15 countries in both the dashboard and ten Brink et al. 2025
(no model change). For each country: the donor share of HIV spending from Optima appendix Table B2 (PEPFAR funding and
total international funding over total expenditure, most recent GAM year), the share of people on ART (outside PMTCT)
who stop ART under US Bilateral Exit + Multilateral Withdrawals before the batch (audit/before_batch34.csv, local) and
after (a central run of the working tree), with the model's ART full cost per patient-year, the external HIV share used
by the cap, and Optima's total HIV spending per person on ART.

    .venv/bin/python audit/logic_review/batch34_reconcile.py [before_snapshot.csv] [output_tag]

Writes audit/logic_review/batch34_reconcile.csv and prints the markdown table.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
logging.disable(logging.WARNING)
import health_model as hm  # noqa: E402
import scenarios as scn  # noqa: E402

# ten Brink et al. 2025, Lancet HIV, appendix Table B2 (p. 8): total expenditure, PEPFAR funding, total international
# funding (US$, GAM year); Côte d'Ivoire's total international is below its PEPFAR figure in the table (PEPFAR from
# COP 2022, flagged there)
B2 = {
    "AZE": (2023, 14_770_145, 0, 2_065_056), "KHM": (2022, 31_565_694, 4_786_621, 20_101_176),
    "CIV": (2022, 180_080_436, 100_845_044, 21_902_421), "DOM": (2022, 72_921_868, 24_650_579, 30_726_584),
    "SWZ": (2019, 102_113_481, 42_866_397, 60_369_904), "KEN": (2022, 764_057_567, 201_786_202, 280_863_737),
    "KGZ": (2023, 12_523_725, 2_116_795, 8_837_142), "MWI": (2022, 259_699_300, 157_037_300, 247_396_300),
    "MDA": (2023, 10_625_628, 0, 4_767_832), "MNG": (2021, 2_474_731, 0, 1_287_518),
    "MOZ": (2019, 557_780_695, 370_271_108, 533_561_519), "ZAF": (2023, 1_863_907_174, 387_997_202, 443_253_308),
    "TJK": (2023, 3_503_630, 0, 0), "UGA": (2020, 538_920_127, 348_501_252, 433_482_483),
    "ZWE": (2023, 310_440_134, 176_939_051, 276_291_719),
}
PRESET = "Full US exit"


def main():
    I, P = hm.load_inputs(), hm.load_params()
    ci = I["ci"]
    before_file = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "audit" / "before_batch34.csv"
    tag = sys.argv[2] if len(sys.argv) > 2 else "batch34"
    before = pd.read_csv(before_file, usecols=["key", "L.hiv_art.units_lost", "L.hiv_art.need",
                                                                        "L.hiv_art.cov0", "L.hiv_art.unit_cost"])
    k = before.key.str.split("|", expand=True)
    before = before[(k[1] == PRESET) & (k[2] == "none") & (k[3] == "Sudden (default)")].copy()
    before["iso3"] = k[0]
    before = before.set_index("iso3")
    sc = scn.build_scenario(PRESET, scn.default_opts(PRESET, ci), ci)
    rows = []
    for iso, (yr, tot, pepfar, intl) in B2.items():
        r = hm.run_country(iso, sc, hm.Fiscal(*scn.DEFAULT_FISCAL), I, P, n_draws=0)
        L = r["lines"].set_index("line").loc["hiv_art"]
        on_art = float(L["need"] * L["cov0"]) - float(ci.loc[iso, "hiv_pos_pregnancies"] * (ci.loc[iso, "sh_hiv_pmtc_zs"] if pd.notna(ci.loc[iso, "sh_hiv_pmtc_zs"]) else ci.loc[iso, "sh_hiv_artc_zs"]) / 100) if pd.notna(ci.loc[iso, "hiv_pos_pregnancies"]) else float(L["need"] * L["cov0"])
        rows.append({
            "iso3": iso, "gam_year": yr, "people_on_art_outside_pmtct": on_art,
            "pepfar_share": pepfar / tot, "intl_share": intl / tot,
            "optima_total_hiv_spend_per_person_on_art": tot / on_art if on_art else np.nan,
            "stop_before": float(before.loc[iso, "L.hiv_art.units_lost"]), "stop_after": float(L["units_lost"]),
            "share_stop_before": float(before.loc[iso, "L.hiv_art.units_lost"]) / on_art if on_art else np.nan,
            "share_stop_after": float(L["units_lost"]) / on_art if on_art else np.nan,
            "art_full_cost_before": float(before.loc[iso, "L.hiv_art.unit_cost"]), "art_full_cost_after": float(L["unit_cost"]),
            "cap_external_share": float(L["donor_share_ext"]) if "donor_share_ext" in L.index else np.nan,
            "art_aid_base_usd": float(L["base_usd"]), "art_aid_lost_usd": float(L["net_loss_usd"]),
            "donor_exceeds_pool": bool(L["donor_exceeds_cost"]),
        })
    t = pd.DataFrame(rows).set_index("iso3")
    t.to_csv(ROOT / "audit" / "logic_review" / f"{tag}_reconcile.csv")
    pd.set_option("display.width", 250)
    print("| Country | GAM year | People on ART (outside PMTCT) | PEPFAR share of HIV spending | All international share | Model share who stop: before | after | ART full cost/yr: before | after | Cap: external HIV share | Optima HIV spending per person on ART | Donor ART aid exceeds the pool |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for iso, r in t.iterrows():
        print(f"| {iso} | {r.gam_year} | {r.people_on_art_outside_pmtct:,.0f} | {r.pepfar_share:.0%} | {r.intl_share:.0%} | "
              f"{r.share_stop_before:.0%} | {r.share_stop_after:.0%} | ${r.art_full_cost_before:,.0f} | ${r.art_full_cost_after:,.0f} | "
              f"{r.cap_external_share:.2f} | ${r.optima_total_hiv_spend_per_person_on_art:,.0f} | {'yes' if r.donor_exceeds_pool else 'no'} |")
    w = t.people_on_art_outside_pmtct
    print(f"\nWeighted (by people on ART) share who stop: before {np.average(t.share_stop_before, weights=w):.1%}, after "
          f"{np.average(t.share_stop_after, weights=w):.1%}; PEPFAR share {np.average(t.pepfar_share, weights=w):.1%}; "
          f"all international {np.average(t.intl_share, weights=w):.1%}")


if __name__ == "__main__":
    main()
