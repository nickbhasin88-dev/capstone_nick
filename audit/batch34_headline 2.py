"""
Batch 3+4 progress numbers: the all-country headline (US Bilateral Exit + Multilateral Withdrawals, central run, no
government response, sudden cut, trends on) by disease, and the people who stop ART (full-cost equivalents, per year
mean over 2026-2030, summed over countries), from the precomputed All Countries file plus one central run per
country for the ART count. Read-only.

    .venv/bin/python audit/batch34_headline.py [label]
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
logging.disable(logging.WARNING)
import health_model as hm  # noqa: E402
import scenarios as scn  # noqa: E402

PRESET = "Full US exit"
FOCUS = ["KEN", "NGA", "MOZ", "ZAF", "UGA", "IND"]


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "now"
    I, P = hm.load_inputs(), hm.load_params()
    A = pd.read_csv(scn.precomputed_path(hm.MODEL_DIR, PRESET)).set_index("iso3")
    sc = scn.build_scenario(PRESET, scn.default_opts(PRESET, I["ci"]), I["ci"])
    art, art_c = 0.0, {}
    for iso in A.index:
        L = hm.run_country(iso, sc, hm.Fiscal(*scn.DEFAULT_FISCAL), I, P, n_draws=0)["lines"].set_index("line")
        art_c[iso] = float(L.loc["hiv_art", "units_lost"])
        art += art_c[iso]
    print(f"[{label}] all-disease deaths 2026-30: {A.deaths_5y.sum():,.0f} | HIV {A.deaths_5y_HIV.sum():,.0f} | "
          f"TB {A.deaths_5y_TB.sum():,.0f} | malaria {A.deaths_5y_Malaria.sum():,.0f} | vaccines {A.deaths_5y_Immunization.sum():,.0f} | "
          f"further 2031-35 {A.deaths_after_2030.sum():,.0f} | HIV infections {A.hiv_infections_5y.sum():,.0f} | "
          f"people who stop ART (per year) {art:,.0f}")
    print("  focus: " + "; ".join(f"{c} deaths {A.loc[c, 'deaths_5y']:,.0f}, ART {art_c[c]:,.0f}" for c in FOCUS if c in A.index))


if __name__ == "__main__":
    main()
