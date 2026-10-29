"""
Merge snapshot (chipmunk = main's dashboard + tomato's deaths logic): every model output, per branch, with fixed seeds.

    .venv/bin/python audit/merge/snapshot_merge.py <out.csv>            # run from the root of the branch to snapshot
    .venv/bin/python audit/merge/snapshot_merge.py --diff <a.csv> <b.csv> [--cols <regex>]

Runs on main, tomato and chipmunk alike (features are detected, not assumed). One row per country x donor preset x
government response x funding path (as audit/snapshot_numbers.py: every PRESET incl. Custom at its defaults, every
non-custom path, four responses; America First MOUs: its own schedule only), seed 7, 400 draws. Columns:
  - every value audit/snapshot_numbers.py flattens (totals, buckets, lines, years, fiscal, cards), and
  - every numeric column of the line and bucket tables (L.<line>.<col>, B.<bucket>.<col>), which picks up main's
    per-year columns (net_loss_<year>, units_lost_<year>, cov_drop_pp_<year>).
Extra rows:
  - ALL|<preset>: column sums of each precomputed All Countries file (model_data/all_countries_<preset>.csv);
  - PROJ|<iso3>: main's Announced donor cuts projection (announcement_totals, known_loss_by_year, announced_path,
    phase_out_by_donor, policy_money, tax_effort) where the branch has it;
  - FILE|<path>: sha1 of the projection and OECD input/output files (announcement_cuts.csv, announcement_areas.csv,
    announcement_model/oda_history.csv, model_data/*.csv precomputed files).
A headline file <out>_headline.csv (sudden path, no government response: totals per country x preset) is also written.
"""
from __future__ import annotations

import hashlib
import importlib.util
import logging
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))
logging.disable(logging.WARNING)

import health_model as hm  # noqa: E402
import model_section as ms  # noqa: E402
import scenarios as scn  # noqa: E402

spec = importlib.util.spec_from_file_location("snapshot_numbers", ROOT / "audit" / "snapshot_numbers.py")
sn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sn)

SEED, DRAWS = 7, 400

# main's US$1M cards no longer carry a "deaths" field (commit 5c7241a), which audit/snapshot_numbers.py.flatten reads;
# give it None there so one snapshot script runs on every branch (flatten itself is left unchanged)
_cards = ms._per_million_cards
ms._per_million_cards = lambda *a, **k: [{"deaths": None, **c} for c in _cards(*a, **k)]


def numeric_tables(res) -> dict:
    d = {}
    for name, key, idx in (("L", "lines", "line"), ("B", "buckets", "bucket")):
        t = res[key]
        for r in t.to_dict("records"):
            for k, v in r.items():
                if k != idx and isinstance(v, (int, float, np.integer, np.floating, bool, np.bool_)):
                    d[f"{name}.{r[idx]}.{k}"] = float(v)
    for k, v in res["totals"].items():
        if isinstance(v, (int, float, np.integer, np.floating)):
            d[f"T.{k}"] = float(v)
    return d


def projection_rows(I) -> list:
    rows = []
    countries = [c for c in I["ci"].index if c in set(I["lines"].iso3)]
    tot = hm.announcement_totals() if hasattr(hm, "announcement_totals") else {}
    for iso in countries:
        d = {"key": f"PROJ|{iso}"}
        if iso in tot:
            d["A.base"] = tot[iso]["base"]
            for k in ("lost", "known", "mou_pred"):
                for t, v in enumerate(tot[iso][k]):
                    d[f"A.{k}.{2026 + t}"] = v
        if hasattr(hm, "known_loss_by_year"):
            for t, v in enumerate(hm.known_loss_by_year(iso, I)):
                d[f"K.{2026 + t}"] = v
        if hasattr(ms, "announced_path"):
            ap = ms.announced_path(iso)
            if ap:
                for k, v in ap.items():
                    if np.ndim(v) == 1:
                        for t, x in enumerate(v):
                            d[f"AP.{k}.{2026 + t}"] = float(x)
                    elif isinstance(v, (int, float, np.floating, bool)):
                        d[f"AP.{k}"] = float(v)
        if hasattr(ms, "phase_out_by_donor"):
            po = ms.phase_out_by_donor(iso)
            for idx, r in po.iterrows():
                for c, v in r.items():
                    if isinstance(v, (int, float, np.integer, np.floating)):
                        d[f"PO.{idx}.{c}"] = float(v)
        if hasattr(hm, "policy_money"):
            for ab, tx in ((True, False), (False, True), (True, True)):
                p = hm.policy_money(iso, I, ab, tx)
                for t, v in enumerate(p["by_year"]):
                    d[f"PM.{int(ab)}{int(tx)}.{2026 + t}"] = float(v)
        if hasattr(hm, "tax_effort"):
            te = hm.tax_effort(iso)
            d["TE.tax_pct"], d["TE.gdp_usd"] = te["tax_pct"], te["gdp_usd"]
        rows.append(d)
    return rows


def file_rows() -> list:
    files = sorted(set(ROOT.glob("model_data/all_countries_*.csv")) | {ROOT / "model_data/announcement_cuts.csv",
                   ROOT / "model_data/announcement_areas.csv", ROOT / "announcement_model/oda_history.csv"})
    return [{"key": f"FILE|{p.relative_to(ROOT)}", "sha1": hashlib.sha1(p.read_bytes()).hexdigest()}
            for p in files if p.exists()]


def snapshot(out_path):
    I, P = hm.load_inputs(), hm.load_params()
    ci = I["ci"]
    rows, head = [], []
    countries = [c for c in ci.index if c in set(I["lines"].iso3)]
    for preset in scn.PRESETS:
        sc = scn.build_scenario(preset, scn.default_opts(preset, ci), ci)
        for iso in countries:
            if sc.mou_only and iso not in sc.us_direct_path_by_country:
                continue
            paths = ["MOU schedule"] if sc.mou_only else sn.PATHS
            for path in paths:
                cut = None if path in ("MOU schedule", "Sudden (default)") else tuple(scn.path_shape(path))
                for resp, ft in sn.RESPONSES.items():
                    gov = sn.gov_add_for(iso, I) if resp == "gradual" else None
                    res = hm.run_country(iso, sc, hm.Fiscal(*ft), I, P, n_draws=DRAWS, seed=SEED, cut_path=cut,
                                         gov_add_usd=gov)
                    d = {"key": f"{iso}|{preset}|{resp}|{path}"}
                    d.update(sn.flatten(res, P, iso, I, cut, sc, ft))
                    d.update(numeric_tables(res))
                    d["break_even"] = hm.break_even_share(iso, sc, hm.Fiscal(*ft), I, cut)
                    rows.append(d)
                    if resp == "none" and path in ("Sudden (default)", "MOU schedule"):
                        T = res["totals"]
                        head.append({"iso3": iso, "preset": preset, **{k: T.get(k, np.nan) for k in (
                            "base", "gross", "replaced", "net", "deaths_y1", "deaths_5y", "deaths_5y_lo",
                            "deaths_5y_hi")}, "after_2030": res["committed"]["after_2030"],
                            "people_lost": float(res["lines"].loc[~res["lines"]["line"].isin(["hiv_prev", "hiv_ovc"]),
                                                                  "units_lost"].clip(lower=0).sum())})
        print(f"  {preset}: {len(rows)} rows so far", flush=True)
    for preset in scn.PRECOMPUTED_PRESETS:
        A = scn.load_precomputed(hm.MODEL_DIR, preset)
        d = {"key": f"ALL|{preset}"}
        d.update({f"sum.{c}": A[c].sum() for c in A.columns if c != "iso3" and pd.api.types.is_numeric_dtype(A[c])})
        for c in ("deaths_5y", "deaths_after_2030"):
            if c in A:
                d[f"range.{c}_lo"], d[f"range.{c}_hi"] = hm.total_range(A, c)
        d["n_countries"] = len(A)
        rows.append(d)
    rows += projection_rows(I) + file_rows()
    df = pd.DataFrame(rows).set_index("key")
    df.to_csv(out_path, float_format="%.12g")
    pd.DataFrame(head).to_csv(str(out_path).replace(".csv", "_headline.csv"), index=False, float_format="%.6g")
    print(f"saved {df.shape[0]} rows x {df.shape[1]} values to {out_path}")


def diff(a, b, cols=None):
    A = pd.read_csv(a, index_col="key", low_memory=False)
    B = pd.read_csv(b, index_col="key", low_memory=False)
    if cols:
        A = A[[c for c in A.columns if re.search(cols, c)]]
        B = B[[c for c in B.columns if re.search(cols, c)]]
    only_a, only_b = sorted(set(A.index) - set(B.index)), sorted(set(B.index) - set(A.index))
    ca, cb = sorted(set(A.columns) - set(B.columns)), sorted(set(B.columns) - set(A.columns))
    r, c = A.index.intersection(B.index), A.columns.intersection(B.columns)
    x, y = A.loc[r, c], B.loc[r, c]
    same = (x == y) | (x.isna() & y.isna())
    n_bad = int((~same).values.sum())
    print(f"{len(r)} rows x {len(c)} columns compared ({x.size:,} values); {n_bad} differ; rows only in a: "
          f"{len(only_a)}, only in b: {len(only_b)}; columns only in a: {len(ca)}, only in b: {len(cb)}")
    if n_bad:
        bad = (~same).stack()
        for (k, cc) in bad[bad].index[:20]:
            print(f"  {k} {cc}: a {x.loc[k, cc]} b {y.loc[k, cc]}")
    for lab, v in (("rows only in a", only_a), ("rows only in b", only_b), ("cols only in a", ca),
                   ("cols only in b", cb)):
        if v:
            print(f"  {lab}: {v[:8]}{' ...' if len(v) > 8 else ''}")
    return n_bad == 0 and not only_a and not ca


if __name__ == "__main__":
    if sys.argv[1] == "--diff":
        rx = sys.argv[sys.argv.index("--cols") + 1] if "--cols" in sys.argv else None
        sys.exit(0 if diff(sys.argv[2], sys.argv[3], rx) else 1)
    snapshot(sys.argv[1])
