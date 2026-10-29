"""
Before/after table for Batch 2 (ART death risk, re-engagement and HIV transmission; L-01, L-41): all-country HIV
deaths, HIV infections, all-disease deaths and further deaths for every precomputed preset, and the same for Kenya,
Nigeria, Mozambique, South Africa and Uganda, from model_data/all_countries_<preset>.csv at commit c625037 (before)
and in the working tree (after). Central run, no government response, sudden cut, trends on.

    .venv/bin/python audit/logic_review/batch2_before_after.py > audit/logic_review/batch2_before_after.md
"""
import io
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import scenarios as scn  # noqa: E402

BEFORE = "c625037"
COLS = ["deaths_5y_HIV", "hiv_infections_5y", "deaths_5y_TB", "deaths_5y_Malaria", "deaths_5y_Immunization",
        "deaths_5y", "deaths_after_2030"]
NAMES = ["HIV deaths", "HIV infections", "TB", "Malaria", "Immunization", "All deaths, 2026-30", "Further deaths, 2031-35"]
COUNTRIES = {"KEN": "Kenya", "NGA": "Nigeria", "MOZ": "Mozambique", "ZAF": "South Africa", "UGA": "Uganda"}


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
    print("# Batch 2: before/after (central run, no government response, sudden cut, trends on)\n")
    print(f"Before = `model_data/all_countries_<preset>.csv` at commit `{BEFORE}`; after = the working tree. "
          "Non-HIV columns are shown to confirm that only HIV results moved.\n")
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
    # which columns changed at all, over every preset and country
    changed = set()
    for preset in scn.PRECOMPUTED_PRESETS:
        b, a = load(preset, BEFORE), load(preset)
        common = [c for c in a.columns if c in b.columns]
        idx = b.index.intersection(a.index)
        for c in common:
            x, y = b.loc[idx, c], a.loc[idx, c]
            if pd.api.types.is_numeric_dtype(x) and ((x - y).abs() > 1e-6 * (x.abs() + 1)).any():
                changed.add(c)
    print("\n## Columns that changed in any preset or country\n")
    print(", ".join(sorted(changed)))


if __name__ == "__main__":
    main()
