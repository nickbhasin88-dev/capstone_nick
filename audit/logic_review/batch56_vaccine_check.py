"""
Batch 5+6 item V3: vaccine deaths 2026-2030 and the vaccine part of the further deaths 2031-2035, for every precomputed
preset (all countries) and for the six focus countries, from a model run per country in the current working tree.
Run it once in a worktree at the commit before V2 (before) and once in the working tree (after), then compare:

    .venv/bin/python audit/logic_review/batch56_vaccine_check.py <out.csv>
"""
import logging
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
logging.disable(logging.WARNING)
import health_model as hm  # noqa: E402
import scenarios as scn  # noqa: E402

FOCUS = ["KEN", "NGA", "MOZ", "ZAF", "UGA", "IND"]


def main(out):
    I, P = hm.load_inputs(), hm.load_params()
    rows = []
    for preset in scn.PRECOMPUTED_PRESETS:
        sc = scn.build_scenario(preset, scn.default_opts(preset, I["ci"]), I["ci"])
        countries = [c for c in I["ci"].index if c in set(I["lines"].iso3)]
        if sc.mou_only:
            countries = [c for c in countries if c in sc.us_direct_path_by_country]
        for iso in countries:
            r = hm.run_country(iso, sc, hm.Fiscal(*scn.DEFAULT_FISCAL), I, P, n_draws=0)
            B = r["buckets"].set_index("bucket")
            rows.append({"preset": preset, "iso3": iso, "imm_deaths_5y": float(B.loc["Immunization", "deaths_5y"]),
                         "imm_after_2030": float(r["committed"]["after_parts"]["imm"]),
                         "deaths_5y": r["totals"]["deaths_5y"], "after_2030": r["committed"]["after_2030"]})
    t = pd.DataFrame(rows)
    t.to_csv(out, index=False)
    s = t.groupby("preset")[["imm_deaths_5y", "imm_after_2030", "deaths_5y", "after_2030"]].sum()
    print(s.round(0).to_string())
    print(t[t.iso3.isin(FOCUS) & (t.preset == "Full US exit")].set_index("iso3")[["imm_deaths_5y", "imm_after_2030"]].round(0).to_string())


if __name__ == "__main__":
    main(sys.argv[1])
