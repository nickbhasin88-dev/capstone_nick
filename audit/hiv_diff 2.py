"""
Diff audit/before_hiv.csv against audit/after_hiv.csv (made by snapshot_numbers.py) for the HIV batch (I-09, I-27
PMTCT part, I-04). Run from the repo root:

    .venv/bin/python audit/hiv_diff.py

Attributes every changed value: HIV lines, bucket and path (I-09, I-27), the per-US$1M cards (I-04), and the totals,
year and All Countries values that include HIV deaths may change; TB, malaria and immunization lines and buckets, aid
amounts and fiscal values may not. Prints the report tables and exits 1 if anything else moved.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
A = pd.read_csv(ROOT / "audit" / "before_hiv.csv", index_col="key", low_memory=False)
B = pd.read_csv(ROOT / "audit" / "after_hiv.csv", index_col="key", low_memory=False)
assert list(A.index) == list(B.index)
new_cols = [c for c in B.columns if c not in A.columns]
cols = [c for c in A.columns if c in B.columns]
COUNTRIES = {"KEN": "Kenya", "NGA": "Nigeria", "MOZ": "Mozambique", "UGA": "Uganda", "ZAF": "South Africa",
             "ZMB": "Zambia", "MWI": "Malawi", "HND": "Honduras"}
num = lambda x: pd.to_numeric(x, errors="coerce")  # noqa: E731


def allowed(col: str) -> str | None:
    if col.startswith(("L.hiv_", "B.HIV.", "path.HIV.")):
        return "HIV line, bucket or path (I-09, I-27)"
    if col.startswith("card."):
        return "per-US$1M card (I-04)"
    if col in ("T.deaths_5y", "T.deaths_5y_lo", "T.deaths_5y_hi", "T.deaths_y1") or col.startswith("C.") or \
            (col.startswith("Y.") and col.endswith(".deaths")):
        return "total deaths (include HIV)"
    if col.startswith("sum.") and ("HIV" in col or "deaths" in col or "infections" in col):
        return "All Countries sum"
    if col == "break_even":
        return "break-even (deaths-based)"
    return None


a, b = A[cols], B[cols]
same = (a == b) | (a.isna() & b.isna())
fa, fb = a.apply(num), b.apply(num)
tiny = ((fa - fb).abs() < 1e-6) | ((fa - fb).abs() <= 1e-9 * fa.abs())
changed = ~same & ~tiny.fillna(False)
rows, bad = [], []
for c in a.columns[changed.any().to_numpy()]:
    why = allowed(c)
    rows.append((why or "UNEXPLAINED", c, int(changed[c].sum())))
    if why is None:
        bad.append((c, int(changed[c].sum()), list(a.index[changed[c].to_numpy()][:4])))
d = pd.DataFrame(rows, columns=["reason", "column", "values"])
print(f"{a.size:,} values compared; {int(changed.values.sum()):,} changed (beyond rounding); "
      f"{len(new_cols)} new columns (the HIV Testing & Care line: {', '.join(c.split('.')[-1] for c in new_cols[:6])}...)")
print(d.groupby("reason")["values"].sum().to_string())
if bad:
    print("\nUNEXPLAINED:")
    for x in bad[:30]:
        print(" ", x)


def k(iso):
    return f"{iso}|Full US exit|none|Sudden (default)"


def ba(col, iso, fmt="{:,.0f}"):
    x, y = (A.loc[k(iso), col] if col in A.columns else np.nan), B.loc[k(iso), col]
    f = lambda v: "n/a" if pd.isna(num(v)) else fmt.format(num(v))  # noqa: E731
    return f"{f(x)} -> {f(y)}"


print("\nFull US exit, no government response, sudden cut:")
rep = []
for iso, name in COUNTRIES.items():
    rep.append({"Country": name,
                "ART aid": ba("L.hiv_art.base_usd", iso, "${:,.0f}"),
                "Testing & care aid": ba("L.hiv_care_ct.base_usd", iso, "${:,.0f}"),
                "PMTCT aid": ba("L.hiv_pmtct.base_usd", iso, "${:,.0f}"),
                "Prevention aid": ba("L.hiv_prev.base_usd", iso, "${:,.0f}"),
                "People losing ART": ba("L.hiv_art.units_lost", iso),
                "PMTCT women losing": ba("L.hiv_pmtct.units_lost", iso),
                "HIV deaths 2026-30": ba("B.HIV.deaths_5y", iso),
                "New HIV infections": ba("B.HIV.infections_5y", iso)})
pd.set_option("display.width", 300)
print(pd.DataFrame(rep).set_index("Country").T.to_string())

print("\nPer-US$1M cards (people losing main service / coverage drop pp / extra deaths 5y):")
cr = []
for iso, name in COUNTRIES.items():
    r = {"Country": name}
    for bk in ("HIV", "TB", "Malaria", "Immunization"):
        r[bk] = (f"{A.loc[k(iso), f'card.{bk}.people']}/{A.loc[k(iso), f'card.{bk}.cov']}/{A.loc[k(iso), f'card.{bk}.deaths']}"
                 f" -> {B.loc[k(iso), f'card.{bk}.people']}/{B.loc[k(iso), f'card.{bk}.cov']}/{B.loc[k(iso), f'card.{bk}.deaths']}")
    cr.append(r)
print(pd.DataFrame(cr).set_index("Country").to_string())

print("\nAll Countries, deaths 2026-2030 by disease (default settings):")
pre = []
for key in [x for x in A.index if x.startswith("ALL|")]:
    r = {"Preset": key.split("|")[1]}
    for bk in ("HIV", "TB", "Malaria", "Immunization"):
        r[bk] = f"{num(A.loc[key, f'sum.deaths_5y_{bk}']):,.0f} -> {num(B.loc[key, f'sum.deaths_5y_{bk}']):,.0f}"
    r["All"] = f"{num(A.loc[key, 'sum.deaths_5y']):,.0f} -> {num(B.loc[key, 'sum.deaths_5y']):,.0f}"
    r["New HIV infections"] = (f"{num(A.loc[key, 'sum.hiv_infections_5y']):,.0f} -> "
                               f"{num(B.loc[key, 'sum.hiv_infections_5y']):,.0f}")
    pre.append(r)
print(pd.DataFrame(pre).set_index("Preset").to_string())
sys.exit(1 if bad else 0)
