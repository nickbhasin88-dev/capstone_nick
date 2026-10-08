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
        "8th replenishment, Nov 2025). Other donors unchanged."),
    "America First MOUs": (
        "US bilateral aid follows the 2026-2030 MOU schedules your team collected (US funding in that year vs. the "
        "2021-25 pre-cut reference). Countries without a schedule get the average MOU-country cut for that year unless "
        "you override it. US multilateral exits as in 'Full US Exit'."),
    "IHME 2025 preliminary estimates": (
        "Data-driven: applies IHME's own 2025 preliminary DAH estimates relative to 2021-23, separately for every "
        "source x channel x disease cell (IHME has no recipient-level split after 2023, so the global change is applied "
        "to each country's mix)."),
    "OECD-reported 2025 aid cuts": (
        "Each donor's 2025 change in total ODA (OECD preliminary data, Apr 2026) applied to its health aid: US -57%, "
        "Germany -17.4%, France -10.9%, UK -10.8%, Japan -5.6%; others unchanged."),
    "Global Fund & Gavi shortfalls": (
        "Channel shock for all donors: Global Fund -28% (8th replenishment US$11.34B vs US$15.7B for the 7th) and "
        "Gavi -24% (about US$9B raised vs a US$11.9B 2026-30 target)."),
    "Combined retreat": "'Full US Exit' for the US plus the OECD-reported 2025 cuts for all other donors.",
    "Custom": "Set cuts yourself by donor and by channel (cuts combine multiplicatively: 1 - (1-donor cut)(1-channel cut)).",
}
PRECOMPUTED_PRESETS = [p for p in PRESETS if p != "Custom"]

# Fiscal settings the precomputed all-country files use:
# (mode, theta, cap to fiscal space, allocation, ceiling) = No backfill, pro-rata, 75th-percentile ceiling
DEFAULT_FISCAL = ("none", 0.0, True, "pro_rata", "p75")
DEFAULT_MORTALITY_TREND = True     # "Account for Already-Falling Death Rates" on
DEFAULT_MOU_YEAR = 2028
ALL_COUNTRY_DRAWS = 400       # same as the single-country view, so a country's row matches its own page


def mou_cuts(ci: pd.DataFrame, year: int) -> dict:
    out = {}
    for iso, r in ci.iterrows():
        ref = r.get("mou_us_ref")
        if pd.isna(ref) or ref <= 0:
            continue
        y = year
        while y >= 2026 and pd.isna(r.get(f"mou_us_{y}")):
            y -= 1
        if y >= 2026 and pd.notna(r.get(f"mou_us_{y}")):
            out[iso] = float(np.clip(1 - r[f"mou_us_{y}"] / ref, -0.5, 1.0))
    return out


def mou_average_cut_pct(ci: pd.DataFrame, year: int) -> int:
    """Average MOU-country cut in a year, as the whole percent the sidebar slider starts at."""
    return int(round(float(np.mean(list(mou_cuts(ci, year).values()))) * 100))


def default_opts(preset: str, ci: pd.DataFrame) -> dict:
    if preset == "America First MOUs":
        return {"mou_year": DEFAULT_MOU_YEAR, "non_mou_cut": mou_average_cut_pct(ci, DEFAULT_MOU_YEAR) / 100}
    if preset == "Custom":
        return {"custom_direct": {s: (100 if s == "United States" else 0) for s in hm.SOURCE_GROUPS},
                "custom_multi": {s: 0 for s in hm.SOURCE_GROUPS}, "custom_chan": {}}
    return {}


def build_scenario(preset: str, opts: dict, ci: pd.DataFrame) -> hm.Scenario:
    sc = hm.Scenario(name=preset)
    if preset in ("Full US exit", "Combined retreat"):
        sc.src_direct["United States"] = 1.0
        sc.pair.update(US_MULTI_EXITS)
    if preset == "America First MOUs":
        sc.us_direct_by_country = mou_cuts(ci, opts["mou_year"])
        sc.src_direct["United States"] = opts["non_mou_cut"]
        sc.pair.update(US_MULTI_EXITS)
    if preset == "IHME 2025 preliminary estimates":
        sc.ihme_trend = True
    if preset in ("OECD-reported 2025 aid cuts", "Combined retreat"):
        for s, v in OECD_2025.items():
            if preset == "Combined retreat" and s == "United States":
                continue
            sc.src_direct[s] = v
            sc.src_multi[s] = v
    if preset == "Global Fund & Gavi shortfalls":
        sc.chan = {"Global Fund": 0.28, "Gavi": 0.24}
    if preset == "Custom":
        sc.src_direct = {s: v / 100 for s, v in opts["custom_direct"].items()}
        sc.src_multi = {s: v / 100 for s, v in opts["custom_multi"].items()}
        sc.chan = {c: v / 100 for c, v in opts["custom_chan"].items() if v}
    return sc


def scenario_key(sc: hm.Scenario) -> str:
    d = {k: v for k, v in sc.__dict__.items()}
    d["pair"] = {f"{a}|{b}": v for (a, b), v in sc.pair.items()}
    return json.dumps(d, sort_keys=True, default=str)


def scenario_from_key(key: str) -> hm.Scenario:
    d = json.loads(key)
    d["pair"] = {tuple(k.split("|")): v for k, v in d["pair"].items()}
    return hm.Scenario(**d)


def preset_slug(preset: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", preset).strip("_")


def precomputed_path(model_dir, preset: str):
    return model_dir / f"all_countries_{preset_slug(preset)}.csv"


# --------------------------------------------------------------------------- #
# How funding changes over 2026-2030 (share of the scenario's full cut in force each year) and the shape of a gradual
# government budget increase (extra percentage points of the government budget going to health, cumulative)
# --------------------------------------------------------------------------- #
YEARS = [2026, 2027, 2028, 2029, 2030]
PATH_SHAPES = ["Sudden (default)", "Linear phase-out", "Front-loaded", "Back-loaded", "S-curve", "MOU schedule", "Custom"]
GOV_SHAPES = ["Steady", "Fast start", "Slow start", "Custom"]
S_CURVE_STEEPNESS = 1.5          # logistic slope around the midpoint year (year 3)


def path_shape(name: str, mou_path=None) -> list:
    """Share of the full cut in force in years t = 1..5 (N = 5): linear t/5; front-loaded 1-(1-t/5)^2; back-loaded
    (t/5)^2; S-curve a logistic with midpoint year 3, rescaled so year 5 = 1; MOU schedule from the team's sheet."""
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
    elif name == "MOU schedule" and mou_path is not None:
        v = np.asarray(mou_path, dtype=float)
    else:
        v = np.ones(5)
    return [float(x) for x in np.clip(v, 0, 1)]


def mou_cut_path(ci: pd.DataFrame, iso3: str):
    """The country's 2026-2030 cuts in US bilateral aid from the team's MOU sheet (1 - US funding that year / 2021-25
    reference), as shares of the deepest year's cut; None if the country has no MOU schedule."""
    if iso3 not in ci.index:
        return None
    r = ci.loc[iso3]
    ref = r.get("mou_us_ref")
    if pd.isna(ref) or ref <= 0:
        return None
    cuts, last = [], None
    for y in YEARS:
        v = r.get(f"mou_us_{y}")
        last = last if pd.isna(v) else float(np.clip(1 - v / ref, 0, 1))
        cuts.append(last)
    if all(c is None for c in cuts):
        return None
    cuts = [0.0 if c is None else c for c in cuts]
    top = max(cuts)
    return [c / top for c in cuts] if top > 0 else [0.0] * 5


def gov_shape(name: str, points_per_year: float, ceiling: float) -> list:
    """Extra percentage points of the government budget going to health in years 1..5 (cumulative): Steady p*t;
    Fast start 5p * (1-(1-t/5)^2); Slow start 5p * (t/5)^2; never above the room left to the Abuja ceiling."""
    t = np.arange(1, 6) / 5
    p = max(float(points_per_year), 0.0)
    v = {"Fast start": 5 * p * (1 - (1 - t) ** 2), "Slow start": 5 * p * t ** 2}.get(name, p * np.arange(1, 6))
    return [float(x) for x in np.clip(v, 0, max(ceiling, 0.0))]
