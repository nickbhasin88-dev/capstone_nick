"""
Donor-scenario presets for the funding-shock model (no Streamlit, so prepare_model.py can use them too).

    build_scenario(preset, opts, ci) -> health_model.Scenario
    default_opts(preset, ci)         -> the options the sidebar starts with for that preset
"""
from __future__ import annotations

import json
import re

import numpy as np
import pandas as pd

import health_model as hm

US_MULTI_EXITS = {("United States", "WHO"): 1.0, ("United States", "Gavi"): 1.0, ("United States", "UNFPA"): 1.0,
                  ("United States", "Global Fund"): 0.23}
OECD_2025 = {"United States": 0.57, "Germany": 0.174, "France": 0.109, "United Kingdom": 0.108, "Japan": 0.056}
PRESETS = {
    "Full US exit": (
        "All US government health aid through bilateral agencies and NGOs ends; the US leaves WHO (effective Jan 2026), "
        "stops funding Gavi (announced June 2025) and UNFPA; its Global Fund pledge falls 23% (US$6.0B to US$4.6B, "
        "8th replenishment, Nov 2025), so the scenario keeps 77% of the US Global Fund pledge. US money through other "
        "multilaterals (UNICEF, UNAIDS, development banks) is unchanged, and so are other donors."),
    "America First MOUs": (
        "US bilateral aid follows the country's signed America First MOU year by year, 2026-2030: the cut in each year "
        "is 1 - US funding that year ÷ the 2021-25 reference, from the team's MOU sheet, used exactly as written "
        "(a funding increase counts as no cut). Only for the countries that have signed an MOU (KFF tracker) and "
        "have schedule data. US multilateral exits as in 'US Bilateral Exit + Multilateral Withdrawals'. The partner government's co-financing "
        "commitments in the MOU are not modelled (choose a government response to add them)."),
    "IHME 2025 preliminary estimates": (
        "Applies IHME's own 2025 preliminary DAH estimates relative to 2021-23, separately for every source x channel "
        "x disease cell. The country split is not data: IHME has no recipient-level split after 2023, so each "
        "country's mix gets the global ratios."),
    "OECD-reported 2025 aid cuts": (
        "Each donor's 2025 change in total ODA (OECD preliminary data, Apr 2026) applied to its health aid: US -57%, "
        "Germany -17.4%, France -10.9%, UK -10.8%, Japan -5.6%; others unchanged."),
    "Global Fund & Gavi shortfalls": (
        "Channel shock for all donors: every donor's money through Gavi and through the Global Fund falls by the share "
        "you set (default Gavi -15%, Global Fund -20%), against each fund's 2021-23 disbursements (the model "
        "baseline). The Gavi default is our estimate of the fall in spending implied by Gavi 6.0's pledges, not a "
        "published figure, and both defaults apply to this preset only. The sliders' tooltips give the sources."),
    "Combined retreat": "'US Bilateral Exit + Multilateral Withdrawals' for the US plus the OECD-reported 2025 total-aid cuts for all other donors.",
    "Custom": "Set cuts yourself by donor and by channel (cuts combine multiplicatively: 1 - (1-donor cut)(1-channel cut)).",
}
PRECOMPUTED_PRESETS = [p for p in PRESETS if p != "Custom"]

# Global Fund & Gavi Shortfalls (audit I-07): user-set cuts on each fund's 2021-23 disbursements, from every donor
SHORTFALLS = "Global Fund & Gavi shortfalls"
GAVI_CUT_DEFAULT = 15     # % fall vs 2021-23 Gavi spending excluding COVID (our estimate; see Methods)
GF_CUT_DEFAULT = 20       # % fall in Global Fund pledges vs the previous replenishment (US$12.64B vs US$15.7B)

# Fiscal settings the precomputed all-country files use:
# (mode, theta, cap to fiscal space, allocation, ceiling) = No Government Replacement, pro-rata, 75th-percentile ceiling
DEFAULT_FISCAL = ("none", 0.0, True, "pro_rata", "p75")
DEFAULT_MORTALITY_TREND = True     # "Account for Already-Changing Death Rates" on
ALL_COUNTRY_DRAWS = 400       # same as the single-country view, so a country's row matches its own page


# --------------------------------------------------------------------------- #
# America First MOUs: signed status (KFF) and yearly schedules (team MOU sheet)
# --------------------------------------------------------------------------- #
MOU_SIGNED_FILE = hm.MODEL_DIR / "mou_signed.csv"
MOU_GROUP_A, MOU_GROUP_B, MOU_GROUP_C = "A", "B", "C"
NO_MOU_DATA = "MOU signed; no funding data available."


def mou_signed(path=None) -> pd.DataFrame:
    """Signed America First MOUs (KFF tracker), built by prepare_model.py.
    Feeds: the header MOU status and which countries can run America First MOUs."""
    p = MOU_SIGNED_FILE if path is None else path
    return pd.read_csv(p) if p.exists() else pd.DataFrame(columns=["iso3", "country", "agreement_date"])


MOU_PRICE_BASE_YEAR = 2023      # the 2021-25 reference is centred on 2023; deflation (mou_deflate = 1) is relative to it


def mou_deflate_settings(ptab=None) -> tuple:
    """(deflate on?, US$ inflation a year) from model_params.csv (central values; mou_deflate and mou_us_inflation,
    Batch 7 item 8). Read from the parameter file, not the dashboard's parameter editor: the switch is a
    sensitivity setting, and the default (0, nominal as written) is what the dashboard shows."""
    ptab = hm.load_params() if ptab is None else ptab
    on = "mou_deflate" in ptab.index and float(ptab.loc["mou_deflate", "central"]) >= 0.5
    infl = float(ptab.loc["mou_us_inflation", "central"]) if "mou_us_inflation" in ptab.index else 0.0
    return on, infl


def mou_schedule(ci: pd.DataFrame, iso3: str, deflate=None):
    """(yearly cuts 2026-2030, last year with schedule data) from the team's MOU sheet, or (None, None) without a
    schedule. Cut = 1 - US funding that year / 2021-25 reference, used as written: never rescaled; a funding increase
    is a 0% cut; years after the schedule ends hold its last year's cut. Amounts are nominal US$ as written in the
    MOU; with mou_deflate = 1 in model_params.csv (or deflate=(True, inflation)) each year's amount is first divided
    by (1 + inflation)^(year - 2023) so that it is in 2023 US$ like the reference (Batch 7 item 8, L-35).
    Feeds: the America First MOUs scenario and its schedule chart."""
    if iso3 not in ci.index:
        return None, None
    r = ci.loc[iso3]
    ref = r.get("mou_us_ref")
    if pd.isna(ref) or ref <= 0 or pd.isna(r.get(f"mou_us_{YEARS[0]}")):
        return None, None
    on, infl = mou_deflate_settings() if deflate is None else deflate
    cuts, last, end = [], None, None
    for y in YEARS:
        v = r.get(f"mou_us_{y}")
        if pd.notna(v):
            if on:
                v = v / (1.0 + infl) ** (y - MOU_PRICE_BASE_YEAR)
            last, end = float(np.clip(1 - v / ref, 0.0, 1.0)), y
        cuts.append(last)
    return cuts, end


def mou_group(ci: pd.DataFrame, iso3: str, signed=None) -> str:
    """A = signed MOU with a schedule; B = signed, no schedule; C = no signed MOU.
    Feeds: whether America First MOUs is offered for a country."""
    signed = set(mou_signed()["iso3"]) if signed is None else set(signed)
    if iso3 not in signed:
        return MOU_GROUP_C
    return MOU_GROUP_A if mou_schedule(ci, iso3)[0] is not None else MOU_GROUP_B


def mou_groups(ci: pd.DataFrame, isos, signed=None) -> dict:
    """MOU group (A, B or C, see mou_group) for each country in isos."""
    signed = set(mou_signed()["iso3"]) if signed is None else set(signed)
    return {c: mou_group(ci, c, signed) for c in isos}


def mou_schedule_text(ci: pd.DataFrame, iso3: str, country_name: str) -> str:
    """The caption under the America First MOUs scenario: the country's yearly US bilateral cuts 2026-2030 from its MOU
    (shares), or 'MOU signed; no funding data available.'"""
    cuts, end = mou_schedule(ci, iso3)
    if cuts is None:
        return NO_MOU_DATA
    parts = [f"{c:.0%}" for c in cuts]
    parts[0] += f" ({YEARS[0]})"
    parts[-1] += f" ({YEARS[-1]})"
    on, infl = mou_deflate_settings()
    basis = (f"Cuts compare MOU amounts in 2023 US$ (deflated at {infl:.0%} a year, an assumption; mou_deflate = 1) with the 2021-2025 reference."
             if on else "Cuts compare MOU amounts (nominal US$, as written in the MOU) with the 2021-2025 reference; "
             "inflation over 2026-2030 is not deducted, so the real cut is somewhat deeper (mou_deflate = 1 in the parameter file expresses them in 2023 US$).")
    return (f"US bilateral aid cut: {', '.join(parts)}, per {country_name}'s MOU"
            + (f". Schedule ends {end}; {end} level held through {YEARS[-1]}" if end < YEARS[-1] else "")
            + ". " + basis)


def shortfall_cuts(opts: dict) -> tuple:
    """(Gavi cut %, Global Fund cut %) for the Global Fund & Gavi Shortfalls preset; the defaults when not set.
    Feeds: build_scenario and the scenario labels."""
    opts = opts or {}
    return int(opts.get("gavi_cut", GAVI_CUT_DEFAULT)), int(opts.get("gf_cut", GF_CUT_DEFAULT))


def shortfall_label(opts: dict) -> str:
    """'Gavi −15% · Global Fund −20%'.
    Feeds: the kicker, captions and the scenario description."""
    g, f = shortfall_cuts(opts)
    return f"Gavi −{g}% · Global Fund −{f}%"


def preset_description(preset: str, opts: dict | None = None) -> str:
    """The preset's description, with the chosen Gavi and Global Fund cuts for the shortfalls preset.
    Feeds: the Donor Scenario tooltip and the Validation caption."""
    if preset == SHORTFALLS:
        return PRESETS[preset] + f" Selected: {shortfall_label(opts)}."
    return PRESETS[preset]


def default_opts(preset: str, ci: pd.DataFrame) -> dict:
    """The options a preset starts with: Gavi 15% / Global Fund 20% for the shortfalls preset, US 100% for Custom, none
    otherwise."""
    if preset == SHORTFALLS:
        return {"gavi_cut": GAVI_CUT_DEFAULT, "gf_cut": GF_CUT_DEFAULT}
    if preset == "Custom":
        return {"custom_direct": {s: (100 if s == "United States" else 0) for s in hm.SOURCE_GROUPS},
                "custom_multi": {s: 0 for s in hm.SOURCE_GROUPS}, "custom_chan": {}}
    return {}


def build_scenario(preset: str, opts: dict, ci: pd.DataFrame) -> hm.Scenario:
    """Turn a donor preset and its options into a health_model.Scenario: which donors' bilateral and multilateral money
    is cut, by how much (shares 0-1), pair and channel cuts, MOU schedules, or IHME's 2025 ratios. Feeds every model
    run for the chosen preset."""
    sc = hm.Scenario(name=preset)
    if preset in ("Full US exit", "Combined retreat"):
        sc.src_direct["United States"] = 1.0
        sc.pair.update(US_MULTI_EXITS)
    if preset == "America First MOUs":
        # group A only: each country's own yearly schedule; the model refuses any other country (mou_only)
        signed = set(mou_signed()["iso3"])
        sc.us_direct_path_by_country = {c: mou_schedule(ci, c)[0] for c in ci.index
                                        if c in signed and mou_schedule(ci, c)[0] is not None}
        sc.mou_only = True
        sc.pair.update(US_MULTI_EXITS)
    if preset == "IHME 2025 preliminary estimates":
        sc.ihme_trend = True
    if preset in ("OECD-reported 2025 aid cuts", "Combined retreat"):
        for s, v in OECD_2025.items():
            if preset == "Combined retreat" and s == "United States":
                continue
            sc.src_direct[s] = v
            sc.src_multi[s] = v
    if preset == SHORTFALLS:
        # a channel cut for all source donors; this preset has no US multilateral exit, so nothing is counted twice
        g, f = shortfall_cuts(opts)
        sc.chan = {"Global Fund": f / 100, "Gavi": g / 100}
    if preset == "Custom":
        sc.src_direct = {s: v / 100 for s, v in opts["custom_direct"].items()}
        sc.src_multi = {s: v / 100 for s, v in opts["custom_multi"].items()}
        sc.chan = {c: v / 100 for c, v in opts["custom_chan"].items() if v}
    return sc


def scenario_key(sc: hm.Scenario) -> str:
    """The scenario as a JSON string, used as the cache key for model runs."""
    d = {k: v for k, v in sc.__dict__.items()}
    d["pair"] = {f"{a}|{b}": v for (a, b), v in sc.pair.items()}
    d["us_direct_path_by_country"] = {k: [float(x) for x in v] for k, v in sc.us_direct_path_by_country.items()}
    return json.dumps(d, sort_keys=True, default=str)


def scenario_from_key(key: str) -> hm.Scenario:
    """The scenario back from scenario_key's JSON string."""
    d = json.loads(key)
    d["pair"] = {tuple(k.split("|")): v for k, v in d["pair"].items()}
    return hm.Scenario(**d)


# Names shown for presets whose internal key (used in file names, cache keys and tests) differs from the label
# (logic review IMP-14 / L-45, L-28)
PRESET_DISPLAY = {"Full US exit": "US Bilateral Exit + Multilateral Withdrawals", "OECD-reported 2025 aid cuts": "Total-Aid Cuts (OECD) Applied to Health Aid"}


def display_name(preset: str) -> str:
    """The name shown for a preset (its key unless PRESET_DISPLAY renames it)."""
    return PRESET_DISPLAY.get(preset, preset)


def preset_slug(preset: str) -> str:
    """The preset name with non-alphanumerics replaced by '_', for file names."""
    return re.sub(r"[^A-Za-z0-9]+", "_", preset).strip("_")


def precomputed_path(model_dir, preset: str):
    """model_data/all_countries_<preset>.csv for a preset (the All Countries page's file)."""
    return model_dir / f"all_countries_{preset_slug(preset)}.csv"


def precomputed_draws_path(model_dir, preset: str):
    """model_data/all_countries_<preset>_draws.csv: the total over all countries in each of the 400 draws (deaths
    2026-2030 and 2031-2035), from which the All Countries range is taken (logic review IMP-10)."""
    return model_dir / f"all_countries_{preset_slug(preset)}_draws.csv"


def load_precomputed(model_dir, preset: str) -> pd.DataFrame:
    """A precomputed All Countries file, with its draw totals attached as attrs['draw_totals'] (see
    health_model.total_range). Feeds the All Countries page, the Validation page and the audit snapshot."""
    A = pd.read_csv(precomputed_path(model_dir, preset))
    dp = precomputed_draws_path(model_dir, preset)
    if dp.exists():
        d = pd.read_csv(dp)
        A.attrs["draw_totals"] = {c: tuple(float(x) for x in d[c]) for c in d.columns if c != "draw"}
    return A


# --------------------------------------------------------------------------- #
# How funding changes over 2026-2030 (share of the scenario's full cut in force each year) and the shape of a gradual
# government budget increase (extra percentage points of the government budget going to health, cumulative)
# --------------------------------------------------------------------------- #
YEARS = [2026, 2027, 2028, 2029, 2030]
PATH_SHAPES = ["Sudden (default)", "Linear phase-out", "Front-loaded", "Back-loaded", "S-curve", "Custom"]
GOV_SHAPES = ["Steady", "Fast start", "Slow start", "Custom"]
S_CURVE_STEEPNESS = 1.5          # logistic slope around the midpoint year (year 3)


def path_shape(name: str) -> list:
    """Share of the full cut in force in years t = 1..5 (N = 5): linear t/5; front-loaded 1-(1-t/5)^2; back-loaded
    (t/5)^2; S-curve a logistic with midpoint year 3, rescaled so year 5 = 1.
    Feeds: the funding-path choice (share of the cut in force each year)."""
    t = np.arange(1, 6) / 5
    if name == "Linear phase-out":
        v = t
    elif name == "Front-loaded":
        v = 1 - (1 - t) ** 2
    elif name == "Back-loaded":
        v = t ** 2
    elif name == "S-curve":
        s = 1 / (1 + np.exp(-S_CURVE_STEEPNESS * (np.arange(1, 6) - 3)))
        v = s / s[-1]
    else:
        v = np.ones(5)
    return [float(x) for x in np.clip(v, 0, 1)]


def gov_shape(name: str, points_per_year: float, ceiling: float) -> list:
    """Extra percentage points of the government budget going to health in years 1..5 (cumulative): Steady p*t;
    Fast start 5p * (1-(1-t/5)^2); Slow start 5p * (t/5)^2; never above the room left to the Abuja ceiling.
    Feeds: the Gradual Budget Increase shapes."""
    t = np.arange(1, 6) / 5
    p = max(float(points_per_year), 0.0)
    v = {"Fast start": 5 * p * (1 - (1 - t) ** 2), "Slow start": 5 * p * t ** 2}.get(name, p * np.arange(1, 6))
    return [float(x) for x in np.clip(v, 0, max(ceiling, 0.0))]
