"""
Before/after table for Batch 5+6: all-country deaths by disease, HIV infections and further deaths for every
precomputed preset, and the same for Kenya, Nigeria, Mozambique, South Africa, Uganda and India, from
model_data/all_countries_<preset>.csv at a BEFORE commit and in the working tree (after). Central run, no government
response, sudden cut, trends on. With --vaccines, also the vaccine deaths and the vaccine part of the further deaths
(item V3; the vaccine part needs a model run per country at both states, so it is read from the per-country audit
snapshots when given).

    .venv/bin/python audit/logic_review/batch56_before_after.py [before_commit] > audit/logic_review/batch56_before_after.md
"""
import io
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import scenarios as scn  # noqa: E402

BEFORE = sys.argv[1] if len(sys.argv) > 1 else "178733c"
COLS = ["deaths_5y_HIV", "deaths_5y_TB", "deaths_5y_Malaria", "deaths_5y_Immunization", "deaths_5y", "deaths_after_2030",
        "hiv_infections_5y"]
NAMES = ["HIV deaths", "TB", "Malaria", "Vaccines", "All deaths, 2026-30", "Further deaths, 2031-35", "HIV infections"]
COUNTRIES = {"KEN": "Kenya", "NGA": "Nigeria", "MOZ": "Mozambique", "ZAF": "South Africa", "UGA": "Uganda", "IND": "India"}


def load(preset, rev=None):
    path = scn.precomputed_path(ROOT / "model_data", preset)
    if rev is None:
        return pd.read_csv(path).set_index("iso3")
    txt = subprocess.run(["git", "show", f"{rev}:model_data/{path.name}"], capture_output=True, text=True,
                         cwd=ROOT, check=True).stdout
    return pd.read_csv(io.StringIO(txt)).set_index("iso3")


def cell(b, a):
    return f"{b:,.0f} → {a:,.0f} ({(a / b - 1) * 100:+.1f}%)" if b else f"{b:,.0f} → {a:,.0f}"


def table(rows, first="Preset"):
    out = ["| " + first + " | " + " | ".join(NAMES) + " |", "|---|" + "---|" * len(NAMES)]
    out += [f"| {name} | " + " | ".join(cell(b, a) for b, a in vals) + " |" for name, vals in rows]
    return "\n".join(out)


def main():
    print("# Batch 5+6: before/after (central run, no government response, sudden cut, trends on)\n")
    print(f"Before = `model_data/all_countries_<preset>.csv` at commit `{BEFORE}`; after = the working tree.\n")
    print("## All countries, by preset\n")
    rows = []
    for preset in scn.PRECOMPUTED_PRESETS:
        b, a = load(preset, BEFORE), load(preset)
        rows.append((preset, [(b[c].sum(), a[c].sum()) for c in COLS]))
    print(table(rows))
    for iso, name in COUNTRIES.items():
        print(f"\n## {name}\n")
        rows = []
        for preset in scn.PRECOMPUTED_PRESETS:
            b, a = load(preset, BEFORE), load(preset)
            if iso not in b.index or iso not in a.index:
                continue
            rows.append((preset, [(b.loc[iso, c], a.loc[iso, c]) for c in COLS]))
        print(table(rows))


if __name__ == "__main__":
    main()
