"""Full US exit before / after the country-specific ART minimum cost (Goals cross-check follow-up, 2026-10-30).

    python audit/goals_crosscheck/art_floor_before_after.py <before_dir>

<before_dir> holds the files as they were before the change (country_inputs.csv and the all_countries_*.csv files).
Per affected country (dashboard defaults: Full US exit, no government replacement, sudden cut, death-rate trend on, 400
draws): people losing ART, extra deaths 2026-2030 with range, and the four headline cards. Globally: the All Countries
page's cards and the extra deaths with range, from the precomputed files. Writes art_floor_before_after.csv.
"""
from pathlib import Path
import html
import logging
import re
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
logging.disable(logging.WARNING)
import health_model as hm  # noqa: E402
import model_section as ms  # noqa: E402
import scenarios as scn  # noqa: E402
from country_lists import ALLOWED_COUNTRIES  # noqa: E402

OUT = Path(__file__).resolve().parent
PRESET = "Full US exit"
AFFECTED = ["DOM", "IDN", "MUS", "NAM", "NER"]


def country_rows(inputs, label):
    ci = inputs["ci"]
    opts = scn.default_opts(PRESET, ci)
    sc = scn.build_scenario(PRESET, opts, ci)
    ptab = hm.load_params()
    ctl = dict(preset=PRESET, opts=opts, fiscal_t=scn.DEFAULT_FISCAL, ptab_json=ptab.to_json(orient="split"),
               trend=scn.DEFAULT_MORTALITY_TREND, cut_path=None, gov_add=None)
    rows = []
    for iso in AFFECTED:
        res = hm.run_country(iso, sc, hm.Fiscal(*scn.DEFAULT_FISCAL), inputs, ptab, n_draws=scn.ALL_COUNTRY_DRAWS,
                             mortality_trend=scn.DEFAULT_MORTALITY_TREND)
        L, T = res["lines"].set_index("line"), res["totals"]
        cards = re.findall(r"class='l'>([^<]*)<.*?class='v'>([^<]*?)(?: <small>[^<]*</small>)?</span>"
                           r"(?:<span class='n'>([^<]*)</span>)?", ms._hero_cards_html(iso, res, ctl))
        r = {"state": label, "iso3": iso, "art_cost_full": ci.loc[iso, "art_cost_full"],
             "art_people_lost": L.loc["hiv_art", "units_lost"], "art_people_lost_lo": L.loc["hiv_art", "units_lost_lo"],
             "art_people_lost_hi": L.loc["hiv_art", "units_lost_hi"],
             "deaths_5y": T["deaths_5y"], "deaths_5y_lo": T["deaths_5y_lo"], "deaths_5y_hi": T["deaths_5y_hi"]}
        for lbl, v, n in cards:
            r[f"card: {html.unescape(lbl)}"] = html.unescape(v) + (f" | {html.unescape(n)}" if n else "")
        rows.append(r)
    return rows


def global_row(model_dir, label):
    A = scn.load_precomputed(Path(model_dir), PRESET)
    lo, hi = hm.total_range(A)
    A = A[A.iso3.isin(ALLOWED_COUNTRIES) & (A.gross_loss_usd > 0)]
    return {"state": label, "iso3": "ALL", "deaths_5y": A.deaths_5y.sum(), "deaths_5y_lo": lo, "deaths_5y_hi": hi,
            "card: Aid Lost per Year": ms.money(A.gross_loss_usd.sum()),
            "card: Net Aid Lost": ms.money(A.net_loss_usd.sum()),
            "card: People Losing a Service per Year": ms.num(A.people_lost.sum()),
            "card: HIV and TB Treatment Lost per Year": ms.num(A.people_lost_HIV.sum() + A.people_lost_TB.sum()),
            "card: Children Missing Vaccines per Year": ms.num(A.people_lost_Immunization.sum()),
            "people_lost_HIV": A.people_lost_HIV.sum(), "people_lost": A.people_lost.sum(),
            "deaths_5y_HIV": A.deaths_5y_HIV.sum()}


def main(before_dir):
    after = hm.load_inputs()
    before = dict(after, ci=pd.read_csv(Path(before_dir) / "country_inputs.csv").set_index("iso3"))
    rows = country_rows(before, "before") + country_rows(after, "after")
    rows += [global_row(before_dir, "before"), global_row(hm.MODEL_DIR, "after")]
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "art_floor_before_after.csv", index=False)
    pd.set_option("display.width", 250, "display.max_columns", 30, "display.max_colwidth", 60)
    for iso in AFFECTED + ["ALL"]:
        print(df[df.iso3 == iso].dropna(axis=1, how="all").set_index("state").T.to_string(), "\n")


if __name__ == "__main__":
    main(sys.argv[1])
