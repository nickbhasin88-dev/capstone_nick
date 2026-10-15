"""
Batch 7, item 14: per-country flags for the malaria-input caveats L-07, L-21, L-22 and L-23, so affected countries can
be filtered. Read-only with respect to the model; batch34_inputs.py --flags writes the columns into country_inputs.csv.

    .venv/bin/python audit/batch7_flags.py

  flag_itn_default   L-07: bednet use is the 50% default (no MAP estimate and no household survey since 2015)
  flag_irs_household L-21: spraying coverage is MAP's share of households sprayed, applied to people at risk
  flag_irs_implied   L-22: spraying coverage is implied by donor spending (MAP shows none, or less than the money buys)
  flag_map_who_gap   L-23: MAP clinical cases differ from the WHO estimate kept in malaria_cases_prev by more than 30%
Writes audit/logic_review/batch7_flags.csv (one row per modelled country).
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

OUT = ROOT / "audit" / "logic_review" / "batch7_flags.csv"


def main():
    I = hm.load_inputs()
    ci = I["ci"]
    isos = sorted(set(I["lines"].iso3))
    rows = []
    for iso in isos:
        r = ci.loc[iso]
        L = hm.run_country(iso, hm.Scenario(), hm.Fiscal(), I, hm.load_params(), n_draws=0)["lines"].set_index("line")
        irs_src = str(L.loc["mal_irs", "cov_source"])
        prev, now = r.get("malaria_cases_prev"), r.get("malaria_cases")
        gap = (abs(now / prev - 1) > 0.30) if (pd.notna(prev) and pd.notna(now) and prev > 0) else False
        rows.append({"iso3": iso,
                     "flag_itn_default": str(r.get("mal_itn_cov_source")) == "default",
                     "flag_irs_household": str(r.get("mal_irs_cov_source", "")).startswith("MAP"),
                     "flag_irs_implied": irs_src.startswith("implied"),
                     "flag_map_who_gap": bool(gap),
                     "map_cases": now, "who_cases_prev": prev, "malaria_deaths": r.get("malaria_deaths")})
    t = pd.DataFrame(rows).set_index("iso3")
    t.to_csv(OUT)
    for c in ("flag_itn_default", "flag_irs_household", "flag_irs_implied", "flag_map_who_gap"):
        print(f"{c}: {int(t[c].sum())} countries: {', '.join(t.index[t[c]])}")


if __name__ == "__main__":
    main()
