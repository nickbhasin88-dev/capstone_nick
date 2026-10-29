"""
Before/after table for the logic-review "Do now" changes: all-country deaths by disease for every precomputed preset,
and the same for Kenya, Nigeria, Mozambique and India, from model_data/all_countries_<preset>.csv at commit 2cfcb14
(before) and in the working tree (after). Central run, no government response, sudden cut, trends on.

    .venv/bin/python audit/logic_review/do_now_before_after.py > audit/logic_review/do_now_before_after.md
"""
import io
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import scenarios as scn  # noqa: E402

BEFORE = "2cfcb14"
COLS = ["deaths_5y_HIV", "deaths_5y_TB", "deaths_5y_Malaria", "deaths_5y_Immunization", "deaths_5y", "deaths_after_2030"]
NAMES = ["HIV", "TB", "Malaria", "Immunization", "All, 2026-30", "Further, 2031-35"]
COUNTRIES = {"KEN": "Kenya", "NGA": "Nigeria", "MOZ": "Mozambique", "IND": "India"}


def load(preset, rev=None):
    path = scn.precomputed_path(ROOT / "model_data", preset)
    if rev is None:
        return pd.read_csv(path).set_index("iso3")
    txt = subprocess.run(["git", "show", f"{rev}:model_data/{path.name}"], capture_output=True, text=True,
                         cwd=ROOT, check=True).stdout
    return pd.read_csv(io.StringIO(txt)).set_index("iso3")


def cell(b, a):
    return f"{b:,.0f} → {a:,.0f} ({(a / b - 1) * 100:+.1f}%)" if b else f"{b:,.0f} → {a:,.0f}"


def table(rows):
    out = ["| Preset | " + " | ".join(NAMES) + " |", "|---|" + "---|" * len(NAMES)]
    out += [f"| {name} | " + " | ".join(cell(b, a) for b, a in vals) + " |" for name, vals in rows]
    return "\n".join(out)


print("## All countries, deaths by disease (before → after)\n")
rows = []
for p in scn.PRECOMPUTED_PRESETS:
    b, a = load(p, BEFORE), load(p)
    rows.append((scn.display_name(p), [(b[c].sum(), a[c].sum()) for c in COLS]))
print(table(rows))
for iso, name in COUNTRIES.items():
    print(f"\n## {name} (before → after)\n")
    rows = []
    for p in scn.PRECOMPUTED_PRESETS:
        b, a = load(p, BEFORE), load(p)
        if iso in b.index:
            rows.append((scn.display_name(p), [(b.loc[iso, c], a.loc[iso, c]) for c in COLS]))
    print(table(rows))
