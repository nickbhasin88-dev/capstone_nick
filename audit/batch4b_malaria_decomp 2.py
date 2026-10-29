"""
Batch 4b, item 3: decomposition of the malaria change across the Batch 3+4 item commits, by intervention line, for all
countries and for the five largest malaria countries (US Bilateral Exit + Multilateral Withdrawals, central run, no
response, sudden cut, trends on). Each commit is checked out in a temporary git worktree and run with that commit's
own code and inputs. Read-only with respect to the model.

    .venv/bin/python audit/batch4b_malaria_decomp.py

Writes audit/logic_review/batch4b_malaria_decomp.csv (one row per commit x country x line: net money lost, units lost
per year, deaths 2026-30, donor-exceeds-pool flag).
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
COMMITS = [("before", "cd42746"), ("item1", "4f9f0c0"), ("item2", "2a792f7"), ("item4", "810df94"), ("item5", "e6fa30f"),
           ("item6", "f7fbb88"), ("item7", "f424606"), ("final", "c1b0846")]
RUNNER = r'''
import logging, sys, os, json; logging.disable(logging.WARNING)
sys.path.insert(0, os.getcwd())
import health_model as hm, scenarios as scn
I, P = hm.load_inputs(), hm.load_params()
sc = scn.build_scenario("Full US exit", scn.default_opts("Full US exit", I["ci"]), I["ci"])
out = []
for iso in sorted(set(I["lines"].iso3)):
    r = hm.run_country(iso, sc, hm.Fiscal(*scn.DEFAULT_FISCAL), I, P, n_draws=0)
    L = r["lines"].set_index("line")
    for l in ("mal_itn", "mal_irs", "mal_cm"):
        out.append({"iso3": iso, "line": l, "net_loss_usd": float(L.loc[l, "net_loss_usd"]), "units_lost": float(L.loc[l, "units_lost"]),
                    "deaths_5y": float(L.loc[l, "deaths_5y"]), "unit_cost": float(L.loc[l, "unit_cost"]),
                    "donor_exceeds": bool(L.loc[l, "donor_exceeds_cost"]), "cov0": float(L.loc[l, "cov0"]) if L.loc[l, "cov0"] == L.loc[l, "cov0"] else None})
    B = r["buckets"].set_index("bucket")
    out.append({"iso3": iso, "line": "Malaria_total", "net_loss_usd": float(B.loc["Malaria", "net_loss_usd"]), "units_lost": None,
                "deaths_5y": float(B.loc["Malaria", "deaths_5y"]), "unit_cost": None, "donor_exceeds": None, "cov0": None})
print(json.dumps(out))
'''


def main():
    frames = []
    with tempfile.TemporaryDirectory() as td:
        for label, sha in COMMITS:
            wt = Path(td) / label
            subprocess.run(["git", "worktree", "add", "-q", str(wt), sha], cwd=ROOT, check=True)
            try:
                res = subprocess.run([PY, "-c", RUNNER], cwd=wt, capture_output=True, text=True, check=True).stdout
                f = pd.DataFrame(json.loads(res))
                f.insert(0, "commit", label)
                frames.append(f)
            finally:
                subprocess.run(["git", "worktree", "remove", "--force", str(wt)], cwd=ROOT, check=True)
    t = pd.concat(frames, ignore_index=True)
    t.to_csv(ROOT / "audit" / "logic_review" / "batch4b_malaria_decomp.csv", index=False)
    pd.set_option("display.width", 250)
    tot = t[t.line == "Malaria_total"].groupby("commit", sort=False).deaths_5y.sum()
    print("all-country malaria deaths 2026-30 by commit:")
    print(tot.round(0).to_string())
    byline = t[t.line != "Malaria_total"].groupby(["commit", "line"], sort=False).agg(deaths=("deaths_5y", "sum"), units=("units_lost", "sum"), money=("net_loss_usd", "sum")).unstack("line")
    print(byline.round(0).to_string())
    big = t[(t.commit == "before") & (t.line == "Malaria_total")].nlargest(5, "deaths_5y").iso3.tolist()
    print("five largest malaria countries (before):", big)
    for iso in big:
        x = t[(t.iso3 == iso) & (t.line != "Malaria_total")].pivot_table(index="commit", columns="line", values=["deaths_5y", "units_lost"], sort=False)
        print(f"\n{iso}\n{x.round(0).to_string()}")
        print(t[(t.iso3 == iso) & (t.commit == 'final') & (t.line != 'Malaria_total')][["line", "donor_exceeds", "cov0", "unit_cost"]].to_string(index=False))


if __name__ == "__main__":
    main()
