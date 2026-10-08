"""Save sudden-cut results so tests can check that the current model, with the default path and the later mechanisms
switched off, reproduces them. baseline_sudden.json was made by running this file at commit 5eb6111 (before TB spread,
malaria rebound, vaccine cohorts and HIV infection deaths) with the current model_data/country_inputs.csv.
Run from the repo root:  python tests/make_baseline.py"""
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
logging.disable(logging.WARNING)
import health_model as hm  # noqa: E402
import scenarios as scn  # noqa: E402

COUNTRIES = ["KEN", "NGA", "MOZ", "HND", "IRQ"]
FISCALS = {"none": scn.DEFAULT_FISCAL, "custom25": ("custom", 0.25, True, "pro_rata", "p75"),
           "max_lives": ("max", 0.0, True, "lives_first", "p75")}
N_DRAWS = 100


def snapshot(res):
    L = res["lines"].set_index("line")
    cols = ["units_lost", "units_lost_lo", "units_lost_hi", "deaths_y1", "deaths_5y", "deaths_5y_lo", "deaths_5y_hi",
            "infections_5y", "net_loss_usd", "replaced_usd", "cov_drop_pp"]
    return {"lines": {l: {c: float(L.loc[l, c]) if L.loc[l, c] == L.loc[l, c] else None for c in cols} for l in L.index},
            "totals": {k: float(v) for k, v in res["totals"].items()},
            "path": {b: [float(x) for x in res["path"][b]] for b in hm.BUCKETS}}


def main():
    I, P = hm.load_inputs(), hm.load_params()
    out = {}
    for iso in COUNTRIES:
        for preset in scn.PRESETS:
            sc = scn.build_scenario(preset, scn.default_opts(preset, I["ci"]), I["ci"])
            for fk, ft in FISCALS.items():
                out[f"{iso}|{preset}|{fk}"] = snapshot(hm.run_country(iso, sc, hm.Fiscal(*ft), I, P, n_draws=N_DRAWS))
    p = Path(__file__).parent / "baseline_sudden.json"
    p.write_text(json.dumps(out))
    print(f"saved {len(out)} runs to {p}")


if __name__ == "__main__":
    main()
