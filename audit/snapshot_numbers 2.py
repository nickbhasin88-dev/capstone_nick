"""
Snapshot every number the dashboard displays, to check that a wording-only change moves none of them.

    .venv/bin/python audit/snapshot_numbers.py audit/before_cosmetic.csv
    .venv/bin/python audit/snapshot_numbers.py audit/after_cosmetic.csv
    .venv/bin/python audit/snapshot_numbers.py --diff audit/before_cosmetic.csv audit/after_cosmetic.csv

One row per country x donor preset x government response x funding path (America First MOUs: group A countries,
its own schedule only), with every displayed value as a column: totals, buckets, service lines (people, coverage,
deaths and ranges, infections), deaths by year, 2031-2035 parts, fiscal panel values, break-even, and the four
per-US$1M cards. Plus one row per precomputed All Countries file (column sums) and the Validation table inputs.
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
import model_section as ms  # noqa: E402
import scenarios as scn  # noqa: E402

RESPONSES = {"none": scn.DEFAULT_FISCAL, "custom25": ("custom", 0.25, True, "pro_rata", "p75"),
             "max": ("max", 0.0, True, "pro_rata", "p75"), "gradual": ("gradual", 0.0, True, "pro_rata", "p75")}
PATHS = [s for s in scn.PATH_SHAPES if s != "Custom"]


def gov_add_for(iso, I):
    b = hm.health_budget(iso, I)
    room = float(b["room_pct"]) if b["room_pct"] == b["room_pct"] else 0.0
    if room <= 0 or not (b["gov_spend_usd"] == b["gov_spend_usd"]):
        return None
    pts = scn.gov_shape("Steady", 0.5, room)
    return tuple(float(v) for v in hm.gov_add_from_points(pts, b["gov_spend_usd"])) if any(pts) else None


def flatten(res, P, iso, I, cut_path, sc, ft):
    d = {}
    for k, v in res["totals"].items():
        d[f"T.{k}"] = v
    for k in ("deaths", "deaths_lo", "deaths_hi", "after_2030", "after_2030_lo", "after_2030_hi"):
        d[f"C.{k}"] = res["committed"][k]
    for k, v in res["committed"]["after_parts"].items():
        d[f"C.part.{k}"] = v
    # L-33: 2031-2035 deaths at art_reengage high and low (shown under Further Deaths)
    d["C.after_2030_reengage_min"], d["C.after_2030_reengage_max"] = res["committed"]["after_2030_reengage"]
    for r in res["buckets"].itertuples():
        for k in ("base_usd", "gross_loss_usd", "replaced_usd", "net_loss_usd", "deaths_y1", "deaths_5y", "deaths_5y_lo",
                  "deaths_5y_hi", "infections_5y", "infections_5y_lo", "infections_5y_hi", "deaths_per_musd"):
            d[f"B.{r.bucket}.{k}"] = getattr(r, k)
    for r in res["lines"].itertuples():
        for k in ("base_usd", "gross_loss_usd", "replaced_usd", "net_loss_usd", "unit_cost", "need", "cov0", "units_lost",
                  "units_lost_lo", "units_lost_hi", "cov_drop_pp", "deaths_y1", "deaths_5y", "deaths_5y_lo",
                  "deaths_5y_hi", "infections_5y", "infections_5y_lo", "infections_5y_hi"):
            d[f"L.{r.line}.{k}"] = getattr(r, k)
    for b in hm.BUCKETS:
        for t, v in enumerate(res["path"][b]):
            d[f"path.{b}.{t}"] = v
    for r in res["years"].itertuples():
        for k in ("aid_lost_usd", "response_usd", "gov_add_usd", "replaced_usd", "gap_usd", "deaths"):
            d[f"Y.{r.year}.{k}"] = getattr(r, k)
    F = res["fiscal"]
    for k in ("ghes", "capacity", "replacement", "gross_loss", "ghes_pc", "ghes_pct_gdp", "ghes_pct_gov_spend",
              "revenue", "interest_pct_revenue", "stress_factor", "ghes_growth_top", "ghes_growth_median"):
        d[f"F.{k}"] = F[k]
    hb = hm.health_budget(iso, I)
    for k in ("share_pct", "gov_spend_usd", "room_pct", "p90_rise_pp"):
        d[f"HB.{k}"] = hb[k]
    for c in ms._per_million_cards(iso, P.to_json(orient="split"), True, iso):
        d[f"card.{c['bucket']}.people"] = c["people_n"]
        d[f"card.{c['bucket']}.cov"] = c["cov_n"]
        d[f"card.{c['bucket']}.deaths"] = c["deaths"]
        # the footer's dollar amounts (unit cost, aid per death); "US$1M ... 5 years" in the I-24 wording is fixed text
        d[f"card.{c['bucket']}.foot_numbers"] = " ".join(__import__("re").findall(r"(?<!US)\$([\d.,]+[KMB]?)", c["foot"]))
    return d


def snapshot(out_path):
    I, P = hm.load_inputs(), hm.load_params()
    ci = I["ci"]
    rows = []
    countries = [c for c in ci.index if c in set(I["lines"].iso3)]
    for preset in scn.PRESETS:
        sc = scn.build_scenario(preset, scn.default_opts(preset, ci), ci)
        for iso in countries:
            if sc.mou_only and iso not in sc.us_direct_path_by_country:
                continue
            paths = ["MOU schedule"] if sc.mou_only else PATHS
            for path in paths:
                cut = None if path in ("MOU schedule", "Sudden (default)") else tuple(scn.path_shape(path))
                for resp, ft in RESPONSES.items():
                    gov = gov_add_for(iso, I) if resp == "gradual" else None
                    res = hm.run_country(iso, sc, hm.Fiscal(*ft), I, P, n_draws=400, cut_path=cut, gov_add_usd=gov)
                    d = {"key": f"{iso}|{preset}|{resp}|{path}"}
                    d.update(flatten(res, P, iso, I, cut, sc, ft))
                    d["break_even"] = hm.break_even_share(iso, sc, hm.Fiscal(*ft), I, cut)
                    rows.append(d)
        print(f"  {preset}: {len(rows)} rows so far", flush=True)
    for preset in scn.PRECOMPUTED_PRESETS:
        A = scn.load_precomputed(hm.MODEL_DIR, preset)
        d = {"key": f"ALL|{preset}"}
        d.update({f"sum.{c}": A[c].sum() for c in A.columns if c != "iso3"})
        # the displayed All Countries ranges: percentiles of the all-country total over the draws (IMP-10)
        for c in ("deaths_5y", "deaths_after_2030"):
            d[f"range.{c}_lo"], d[f"range.{c}_hi"] = hm.total_range(A, c)
        d["n_countries"] = len(A)
        rows.append(d)
    df = pd.DataFrame(rows).set_index("key")
    df.to_csv(out_path, float_format="%.12g")
    print(f"saved {df.shape[0]} rows x {df.shape[1]} values to {out_path}")


def diff(a, b):
    A = pd.read_csv(a, index_col="key", low_memory=False)
    B = pd.read_csv(b, index_col="key", low_memory=False)
    out = []
    if set(A.index) != set(B.index):
        out.append(f"rows differ: only before {sorted(set(A.index) - set(B.index))[:5]}, "
                   f"only after {sorted(set(B.index) - set(A.index))[:5]}")
    if set(A.columns) != set(B.columns):
        out.append(f"columns differ: only before {sorted(set(A.columns) - set(B.columns))[:5]}, "
                   f"only after {sorted(set(B.columns) - set(A.columns))[:5]}")
    common_r = A.index.intersection(B.index)
    common_c = A.columns.intersection(B.columns)
    a, b = A.loc[common_r, common_c], B.loc[common_r, common_c]
    same = (a == b) | (a.isna() & b.isna())
    n_bad = int((~same).values.sum())
    print(f"{len(common_r)} rows x {len(common_c)} columns compared ({a.size:,} values); {n_bad} differ")
    if n_bad:
        bad = (~same).stack()
        for (k, c) in bad[bad].index[:20]:
            print(f"  {k} {c}: before {a.loc[k, c]} after {b.loc[k, c]}")
    for o in out:
        print(o)
    return n_bad == 0 and not out


if __name__ == "__main__":
    if sys.argv[1] == "--diff":
        sys.exit(0 if diff(sys.argv[2], sys.argv[3]) else 1)
    snapshot(sys.argv[1])
