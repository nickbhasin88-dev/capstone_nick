"""
Diff audit/before_i07.csv against audit/after_i07.csv (made by snapshot_numbers.py) for the I-07 fix: only rows of the
Global Fund & Gavi Shortfalls preset (Gavi 24% -> 15%, Global Fund 28% -> 20%) may change. Run from the repo root:

    .venv/bin/python audit/i07_diff.py

Prints the changed values by preset and column group, and the totals for the preset; exits 1 if anything outside the
preset changed.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
A = pd.read_csv(ROOT / "audit" / "before_i07.csv", index_col="key", low_memory=False)
B = pd.read_csv(ROOT / "audit" / "after_i07.csv", index_col="key", low_memory=False)
assert list(A.index) == list(B.index), "row keys differ"
assert list(A.columns) == list(B.columns), "columns differ"
SF = "Global Fund & Gavi shortfalls"

same = (A == B) | (A.isna() & B.isna())
changed = ~same
preset = pd.Series([k.split("|")[1] for k in A.index], index=A.index)
n_changed = changed.sum(axis=1)
by_preset = n_changed.groupby(preset).agg(["sum", lambda s: int((s > 0).sum()), "size"])
by_preset.columns = ["values_changed", "rows_changed", "rows"]
print(f"{A.size:,} values compared; {int(changed.values.sum()):,} changed")
print(by_preset.to_string())
outside = n_changed[(preset != SF) & (n_changed > 0)]
if len(outside):
    print("\nCHANGES OUTSIDE THE PRESET:")
    for k in outside.index[:20]:
        cols = A.columns[changed.loc[k].to_numpy()]
        print(k, list(cols[:10]))
    sys.exit(1)

# the preset's headline numbers before and after (sudden cut, no response) for a few countries, and the All Countries sums
num = lambda x: pd.to_numeric(x, errors="coerce")  # noqa: E731
keys = [k for k in A.index if k.split("|")[1] == SF and not k.startswith("ALL|")]
show = [c for c in ("T.gross", "T.net", "T.deaths_5y", "C.after_2030") if c in A.columns]
rows = []
for iso in ("KEN", "NGA", "MOZ", "HND", "ETH", "COD"):
    for k in keys:
        p = k.split("|")
        if len(p) == 4 and p[0] == iso and p[2] == "none" and p[3].startswith("Sudden"):
            rows.append({"key": k, **{f"{c} before": num(A.loc[k, c]) for c in show},
                         **{f"{c} after": num(B.loc[k, c]) for c in show}})
if rows:
    print("\n" + pd.DataFrame(rows).set_index("key").round(0).T.to_string())
allk = [k for k in A.index if k.startswith("ALL|") and SF in k]
for k in allk:
    cols = [c for c in A.columns if changed.loc[k, c]]
    print(f"\n{k}:")
    for c in cols[:20]:
        print(f"  {c}: {num(A.loc[k, c]):,.0f} -> {num(B.loc[k, c]):,.0f}")
rel = (num(B.loc[keys, "T.deaths_5y"]) / num(A.loc[keys, "T.deaths_5y"]).replace(0, np.nan)).dropna()
print(f"\nDeaths 2026-2030 after/before across {len(rel)} preset rows: median {rel.median():.3f}, "
      f"range {rel.min():.3f}-{rel.max():.3f}")
