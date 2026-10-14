"""
Funding shock -> fiscal response -> coverage -> lives.

A country-level model for HIV, TB, malaria and immunization:

  1. MONEY     baseline aid (IHME DAH, avg 2021-23) by source x channel x service line; a donor scenario sets the
               fraction cut in every cell; unreported program areas are split by purpose with the country's Global
               Fund module shares (treatment, prevention, testing, systems, programme management; L-43); systems
               money (labs, HR, M&E) is above-site money already priced into the marked-up unit costs, so it is lost
               without a modelled service effect (hss_service_share, default 0; logic review L-05).
  2. FISCAL    the government can backfill part of the loss; the replacement rate is a policy choice (default from
               the panel regression) capped by fiscal space = GHES x (best-year minus typical GHES growth) x debt-stress.
  3. COVERAGE  net money lost / unit cost = people who lose a service; divided by the population in need it gives
               the coverage drop (percentage points), never more than the people currently covered.
  4. LIVES     people losing a service x the mortality effect of that service, using country epidemiology:
               ART interruption hazards, WHO TB case-fatality ratios, Lives Saved Tool equations for malaria,
               VIMC deaths averted per fully immunized child by country and years since vaccination (Batch 5+6).

Every uncertain parameter is drawn from a triangular(low, central, high) distribution; results report the median
and the 2.5-97.5 percentile range of the Monte Carlo draws.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from malaria_inputs import MAL_CM_MIN_INCIDENCE  # noqa: F401  (cited on the Methods page)

log = logging.getLogger("health_model")
HERE = Path(__file__).parent
MODEL_DIR = HERE / "model_data"
PARAMS_FILE = HERE / "model_params.csv"

BUCKETS = ["HIV", "TB", "Malaria", "Immunization"]
BUCKET_COLORS = {"HIV": "#c0392b", "TB": "#8e5ea2", "Malaria": "#e67e22", "Immunization": "#2e86c1"}
DIRECT = {"HIV": ["hiv_art", "hiv_pmtct", "hiv_prev", "hiv_ovc"], "TB": ["tb_ds", "tb_dr"],
          "Malaria": ["mal_itn", "mal_irs", "mal_cm"], "Immunization": ["imm"]}
UNSPEC = {"HIV": "hiv_unspec", "TB": "tb_unspec", "Malaria": "mal_unspec"}
HSS = {"HIV": "hiv_hss", "TB": "tb_hss", "Malaria": "mal_hss"}
ALL_DIRECT = [l for b in BUCKETS for l in DIRECT[b]]
LINE_BUCKET = {l: b for b in BUCKETS for l in DIRECT[b]}
# money lines with no units of their own (audit I-09): hss_kappa of their lost money counts as lost service on the
# target line; the rest is non-service money
LINKED = {"hiv_care_ct": "hiv_art"}
LINKED_IN = {b: [l for l, t in LINKED.items() if LINE_BUCKET[t] == b] for b in BUCKETS}
MONEY_LINES = ALL_DIRECT + list(LINKED)
FULL_LINE_BUCKET = {**LINE_BUCKET, **{v: k for k, v in UNSPEC.items()}, **{v: k for k, v in HSS.items()},
                    **{l: LINE_BUCKET[t] for l, t in LINKED.items()}}
LINE_LABELS = {
    "hiv_art": "HIV treatment (ART)", "hiv_care_ct": "HIV testing & care", "hiv_pmtct": "Prevention of mother-to-child transmission",
    "hiv_prev": "HIV prevention (PrEP, VMMC, condoms, key populations)", "hiv_ovc": "Orphans & vulnerable children",
    "tb_ds": "TB case finding & treatment", "tb_dr": "Drug-resistant TB",
    "mal_itn": "Bednets & other vector control", "mal_irs": "Indoor residual spraying",
    "mal_cm": "Malaria testing & treatment", "imm": "Routine immunization (vaccines + delivery)",
}
UNIT_LABELS = {"hiv_art": "people who stop ART (full-cost equivalents)", "hiv_pmtct": "HIV+ pregnant women", "hiv_prev": "infections averted",
               "hiv_ovc": "children supported", "tb_ds": "TB patients treated", "tb_dr": "DR-TB patients treated",
               "mal_itn": "people sleeping under nets", "mal_irs": "people protected by spraying",
               "mal_cm": "malaria cases treated", "imm": "children immunized"}
UNIT_SINGULAR = {"hiv_art": "patient-year of ART", "hiv_pmtct": "woman", "hiv_prev": "infection averted",
                 "hiv_ovc": "child-year", "tb_ds": "patient", "tb_dr": "patient", "mal_itn": "person-year",
                 "mal_irs": "person-year", "mal_cm": "case", "imm": "child"}

SOURCE_GROUPS = ["United States", "United Kingdom", "Germany", "France", "Japan", "Canada", "Netherlands", "Nordics",
                 "Other DAC governments", "Gates Foundation", "Other private", "Development-bank lending",
                 "Non-DAC governments", "Other / unallocable"]
DIRECT_CHANNELS = {"Bilateral agency", "NGOs", "Gates direct", "Other"}

N_YEARS = 5
# how quickly the full annual effect appears after a sustained cut (year 1..5)
LAG = {
    "hiv_art": None,                                   # explicit hazard ramp below
    "hiv_pmtct": np.array([0.6, 1, 1, 1, 1]),
    "tb_ds": np.array([0.7, 1, 1, 1, 1]), "tb_dr": np.array([0.7, 1, 1, 1, 1]),
    "mal_itn": np.array([0.5, 1, 1, 1, 1]), "mal_irs": np.array([0.8, 1, 1, 1, 1]), "mal_cm": np.ones(5),
    "imm": np.array([0.4, 0.75, 0.95, 1, 1]),
}
# L-01 (Batch 2): excess deaths per person-year after stopping ART, by years since stopping (1..10), from a CD4-stage
# cohort calculation (audit/batch2_cohort.py: untreated CD4 progression and death rates from Optima HIV, ten Brink et
# al. 2025 appendix Tables A1-A2; starting CD4 of people on ART from ZIMPHIA 2020 Table 10.1), minus deaths had they
# stayed on suppressive ART. Years 1-5 are 2026-2030; years 6-10 apply after 2030 to people still off care. Scaled by
# art_hazard_mult. The model treats every full-cost equivalent as a person who actually stops ART.
ART_HAZARD = np.array([0.013, 0.025, 0.037, 0.049, 0.060, 0.068, 0.072, 0.073, 0.071, 0.067])
# the values before Batch 2, used only when hiv_legacy_art_params = 1 (sensitivity check): a 5-year ramp whose year-5
# value applied after 2030, one transmission rate for every country and a 50% a year return to care after 2030
ART_HAZARD_LEGACY = np.array([0.012, 0.028, 0.038, 0.045, 0.05])
ART_REENGAGE_LEGACY = 0.5
ART_TRANSMISSION_FALLBACK = 0.118   # UNAIDS 2025 median rate across the dashboard countries, if a country has none
ART_INFECT_LAG = np.array([0.5, 1, 1, 1, 1])
POST_YEARS = 5                  # deaths set in motion are counted in 2031-2035, with funding back from 2031
HIV_WEIBULL_SHAPE = 2.25        # survival after HIV infection without ART (Todd et al. 2007; UNAIDS Spectrum)
ART_MULT_UP = 0.38              # uc_art_mult high (1.38) minus 1: maps the draw's upper half onto art_cost_full_hi (Batch 4b)
# Batch 5+6 (V2, L-42 / L-18): deaths averted per fully immunized child by years since vaccination (country_inputs.csv
# imm_dpc_lag0..lag9, from VIMC estimates; audit/batch56_vaccines.py). imm_dpc_mult's low (0.56) and high (1.64) map
# the draw onto the country's VIMC lo / hi values (imm_dpc_lo, imm_dpc_hi), the same way uc_art_mult does for ART
IMM_LAGS = 10
IMM_MULT_LO, IMM_MULT_HI = 0.56, 1.64
DR_TB_SHARE, DR_TB_COV = 0.04, 0.45     # fallbacks only: countries use WHO's RR-TB share and enrolment (IMP-11)
# how unspecified money (IHME program area not reported) is split by purpose (Batch 3+4, L-43): the country's Global
# Fund module shares in country_inputs.csv (unspec_<disease>_<purpose>; batch34_inputs.py). Treatment and prevention
# shares go to those lines by the country's mix; the testing share is treated like HIV testing-and-care money (kappa
# of it counts toward the treatment line); the systems share joins HSS money; programme management is non-service
UNSPEC_TAG = {"HIV": "hiv", "TB": "tb", "Malaria": "malaria"}
# external (donor) share of the country's spending on each disease: country_inputs.csv donor_share_<tag> (IMP-04). HIV
# and immunization use the external share of PUBLIC spending (Batch 5+6 item A2). The malaria lines use an
# intervention-specific share (Batch 5+6 item A3): donor money for the intervention / (people covered x the model's
# unit cost), capped at 1, so the pool is the people the donor money for that intervention pays for (the cap is applied
# per intervention, so the share must be that intervention's; the external share of all public malaria spending, kept
# in donor_share_malaria_prev, is dominated by domestic case-management salaries and understated donor-funded nets)
DONOR_SHARE_TAG = {"HIV": "hiv", "TB": "tb", "Malaria": "malaria", "Immunization": "imm"}
DONOR_SHARE_LINE = {"mal_itn": "mal_itn", "mal_irs": "mal_irs", "mal_cm": "mal_cm"}
UNSPEC_TREAT = {"HIV": ["hiv_art"], "TB": ["tb_ds", "tb_dr"], "Malaria": ["mal_cm"]}
UNSPEC_PREV = {"HIV": ["hiv_prev", "hiv_pmtct"], "TB": [], "Malaria": ["mal_itn", "mal_irs"]}
UNSPEC_TEST_TARGET = {"HIV": "hiv_art", "TB": "tb_ds", "Malaria": "mal_cm"}
_EXCESS_LOGGED: set = set()     # (iso3, line) pairs already logged as "donor money exceeds the service cost"


# --------------------------------------------------------------------------- #
# Inputs
# --------------------------------------------------------------------------- #
def load_inputs(model_dir: Path = MODEL_DIR) -> dict:
    """Read the model inputs from model_data/: dah_lines.csv (baseline aid, US$ a year, by country x donor group x
    channel x service line), country_inputs.csv (one row per country: people in need, coverage, deaths, fiscal data),
    ihme_trend.csv (IHME's 2025 / 2021-23 aid ratios) and regressions.json. Returns a dict with those tables, the
    global mix of each disease's service lines (fallback for spreading unspecified money) and the IHME trend as a
    lookup. Feeds every model run."""
    lines = pd.read_csv(model_dir / "dah_lines.csv")
    ci = pd.read_csv(model_dir / "country_inputs.csv").set_index("iso3")
    trend = pd.read_csv(model_dir / "ihme_trend.csv")
    reg = json.loads((model_dir / "regressions.json").read_text())
    # global mix of each bucket's known (direct) lines -> fallback for allocating unreported program areas
    gm = lines[lines.line.isin(MONEY_LINES)].groupby(["bucket", "line"])["usd"].sum()
    gmix = {b: (gm[b] / gm[b].sum()).reindex(DIRECT[b] + LINKED_IN[b]).fillna(0).to_dict() for b in BUCKETS}
    # fallback split of unspecified money by purpose (L-43): the median of the countries' shares, renormalised
    ush = {}
    for b, tag in UNSPEC_TAG.items():
        cols = {c: f"unspec_{tag}_{c}" for c in ("treatment", "prevention", "testing", "rssh", "pm")}
        if all(c in ci.columns for c in cols.values()):
            med = {c: float(ci[col].median()) for c, col in cols.items()}
        else:
            med = {"treatment": 1.0, "prevention": 0.0, "testing": 0.0, "rssh": 0.0, "pm": 0.0}
        tot = sum(med.values()) or 1.0
        ush[b] = {c: v / tot for c, v in med.items()}
    return {"lines": lines, "ci": ci, "trend": trend, "reg": reg, "global_mix": gmix, "unspec_shares": ush,
            "trend_map": trend.set_index(["src_grp", "chan_grp", "bucket"])["ratio"].to_dict()}


def load_params(path: Path = PARAMS_FILE) -> pd.DataFrame:
    """Read model_params.csv: one row per parameter with central, low and high values (units in its 'unit' column),
    status (sourced / assumption) and source. Feeds every model run, the Methods parameter table and the parameter
    editor."""
    return pd.read_csv(path).set_index("param")


def validate_params(ptab: pd.DataFrame) -> list:
    """Problems that make a parameter table unusable (shown inline in the app, which then keeps the previous valid
    table): low above high, or central outside [low, high]. Empty list = valid.
    Feeds: the inline message in the parameter editor."""
    out = []
    for p, r in ptab.iterrows():
        try:
            c, lo, hi = float(r["central"]), float(r["low"]), float(r["high"])
        except (TypeError, ValueError):
            out.append(f"{p}: low, central and high must be numbers")
            continue
        if not all(np.isfinite([c, lo, hi])):
            out.append(f"{p}: low, central and high must be numbers")
        elif lo > hi:
            out.append(f"{p}: low ({lo:g}) is above high ({hi:g})")
        elif not lo <= c <= hi:
            out.append(f"{p}: central ({c:g}) is outside low-high ({lo:g} to {hi:g})")
    return out


def draw_params(ptab: pd.DataFrame, n: int, seed: int = 7) -> dict:
    """n == 0 -> central values only (arrays of length 1). A parameter with low == high (or low == central == high) is
    a constant: n copies of its central value, with no triangular draw (I-16).
    Feeds: every model run (the central run and the 95% ranges)."""
    rng = np.random.default_rng(seed)
    out = {}
    for p, r in ptab.iterrows():
        c, lo, hi = float(r["central"]), float(r["low"]), float(r["high"])
        if n == 0:
            out[p] = np.array([c])
        elif hi <= lo:
            rng.triangular(0.0, 0.5, 1.0, size=n)          # skip its draws so the other parameters' draws don't shift
            out[p] = np.full(n, c)
        else:
            lo, hi = min(lo, c), max(hi, c)
            out[p] = rng.triangular(lo, c, hi, size=n) if hi > lo else np.full(n, c)
    return out


def theta_historical(reg: dict) -> tuple:
    """Replacement rate implied by the fiscal regression: -(b_fall + b_fall_lag) with a 95% CI (independence approx).
    Feeds: the Government Response help text and the Methods page (replacement per US$1 lost)."""
    r = reg["fiscal_replacement"]
    b = r["coef"]["d_dah_pc_fall"] + r["coef"]["d_dah_pc_fall_l1"]
    se = float(np.hypot(r["se"]["d_dah_pc_fall"], r["se"]["d_dah_pc_fall_l1"]))
    return -b, -b - 1.96 * se, -b + 1.96 * se


# --------------------------------------------------------------------------- #
# Scenario
# --------------------------------------------------------------------------- #
@dataclass
class Scenario:
    name: str = "Custom"
    src_direct: dict = field(default_factory=dict)      # source group -> cut on bilateral/NGO/direct channels
    src_multi: dict = field(default_factory=dict)       # source group -> cut on its contributions via multilaterals
    pair: dict = field(default_factory=dict)            # (source group, channel group) -> cut (overrides the above)
    chan: dict = field(default_factory=dict)            # channel group -> cut for ALL sources (replenishment shortfall)
    # iso3 -> 5 cuts (2026-2030) on US direct channels, used as written (America First MOU schedules)
    us_direct_path_by_country: dict = field(default_factory=dict)
    mou_only: bool = False                              # only countries in us_direct_path_by_country can be run
    ihme_trend: bool = False
    bucket_only: str | None = None                      # restrict the shock to one bucket (dose-response curves)
    scale: float = 1.0                                  # multiplies every cut (the scenario's own path, 0 -> 1)

    def cuts(self, cells: pd.DataFrame, iso3: str, trend_map: dict) -> np.ndarray:
        """The scenario's cut (share 0-1) on each aid cell (donor group x channel x disease) of one country. IHME trend:
        1 - IHME's 2025 / 2021-23 ratio. Otherwise the donor cut (bilateral or via multilaterals), overridden by a
        donor x channel pair cut, combined with a channel cut for all donors as 1 - (1 - donor cut)(1 - channel cut);
        then x scale. Feeds Aid at Risk and everything after it."""
        out = np.zeros(len(cells))
        for i, (s, c, b) in enumerate(zip(cells["src_grp"], cells["chan_grp"], cells["bucket"])):
            if self.bucket_only and b != self.bucket_only:
                continue
            if self.ihme_trend:
                out[i] = 1.0 - trend_map.get((s, c, b), 1.0)
                continue
            direct = c in DIRECT_CHANNELS
            x = self.src_direct.get(s, 0.0) if direct else self.src_multi.get(s, 0.0)
            x = self.pair.get((s, c), x)
            y = self.chan.get(c, 0.0)
            out[i] = 1.0 - (1.0 - x) * (1.0 - y)
        return np.clip(out, -1.0, 1.0) * self.scale

    def cuts_by_year(self, cells: pd.DataFrame, iso3: str, trend_map: dict) -> np.ndarray:
        """Cut on every cell in each year 2026-2030 (cells x 5). The same as cuts() in every year, except US direct
        channels in a country with a yearly schedule (us_direct_path_by_country), which follow that schedule."""
        base = self.cuts(cells, iso3, trend_map)
        out = np.repeat(base[:, None], N_YEARS, axis=1)
        path = self.us_direct_path_by_country.get(iso3)
        if path is None or not len(cells):
            return out
        for i, (s, c, b) in enumerate(zip(cells["src_grp"], cells["chan_grp"], cells["bucket"])):
            if s != "United States" or c not in DIRECT_CHANNELS or (self.bucket_only and b != self.bucket_only):
                continue
            y = self.chan.get(c, 0.0)
            for t in range(N_YEARS):
                x = self.pair.get((s, c), float(path[t]))
                out[i, t] = float(np.clip(1.0 - (1.0 - x) * (1.0 - y), -1.0, 1.0)) * self.scale
        return out


def uniform_scenario(bucket: str, cut: float) -> Scenario:
    """A scenario that cuts one disease by the same share for every donor and channel. bucket: 'HIV', 'TB', 'Malaria' or
    'Immunization'; cut: share 0-1. Used by the per-US$1M cards and the 'Extra deaths as more aid is cut' chart."""
    sc = Scenario(name=f"{bucket} -{cut:.0%}", bucket_only=bucket)
    sc.src_direct = {s: cut for s in SOURCE_GROUPS}
    sc.src_multi = {s: cut for s in SOURCE_GROUPS}
    return sc


def per_million_card(iso3: str, bucket: str, inputs: dict, ptab: pd.DataFrame, mortality_trend: bool = True):
    """What a US$1M-a-year loss does to one disease (audit I-04): the full model with the loss spread over all of the
    disease's aid lines in proportion to current aid (a uniform cut, every donor and channel), no government
    replacement, sudden path, every mechanism included (caps, TB spread, malaria rebound, HIV infection deaths).
    Returns None when the country has no aid for the disease. Where the disease's aid is under US$1M a year, the whole
    of it is cut and the results are scaled up to US$1M (flag 'scaled').
    Feeds: the four 'What Every US$1 Million Cut Does' cards."""
    L = inputs["lines"]
    base = float(L.loc[(L.iso3 == iso3) & (L.bucket == bucket), "usd"].sum())
    if base <= 0:
        return None
    cut = min(1.0, 1e6 / base)
    r = run_country(iso3, uniform_scenario(bucket, cut), Fiscal(), inputs, ptab, n_draws=0,
                    mortality_trend=mortality_trend)
    lost = float(r["buckets"].set_index("bucket").loc[bucket, "gross_loss_usd"])
    k = 1e6 / lost if lost > 0 else np.nan
    main = {"HIV": "hiv_art", "TB": "tb_ds", "Malaria": "mal_itn", "Immunization": "imm"}[bucket]
    ln = r["lines"].set_index("line").loc[main]
    return {"bucket": bucket, "main_line": main, "aid_usd": base, "cut": cut, "aid_lost_usd": lost, "scaled": base < 1e6,
            "people": float(ln["units_lost"]) * k, "cov_drop_pp": float(ln["cov_drop_pp"]) * k,
            "deaths_5y": float(r["buckets"].set_index("bucket").loc[bucket, "deaths_5y"]) * k,
            "unit_label": ln["unit_label"], "unit_cost": float(ln["unit_cost"])}


@dataclass
class Fiscal:
    mode: str = "none"            # none | custom | max | gradual (money comes via gov_add_usd)
    theta: float = 0.0            # replacement share for "custom"
    cap_to_space: bool = True
    allocation: str = "pro_rata"  # pro_rata | lives_first
    effort: str = "p75"           # p75 (strong year) | p90 (best years): sets the fiscal-space ceiling


# --------------------------------------------------------------------------- #
# Country helpers
# --------------------------------------------------------------------------- #
def _v(row, k, default=np.nan):
    """A value from a country row as a float, or `default` when it is missing or NaN."""
    x = row.get(k, default)
    return default if x is None or (isinstance(x, float) and np.isnan(x)) else float(x)


def fiscal_space(row: pd.Series, effort: str = "p75") -> dict:
    """Backfill capacity per year = GHES x (strong-year growth - typical growth) x debt-stress factor.
    effort 'p75' = a strong year (75th percentile of real GHES growth, 2001-23); 'p90' = the best years (90th).
    Inputs: a country row (GHES 2023 in US$, growth rates as shares, interest as % of revenue). Feeds: Backfill
    Capacity (fiscal space) in the fiscal panel, and the cap on 'Replace a Set Share' and 'As Much as Fiscal Space
    Allows'."""
    ghes = _v(row, "ghes_2023")
    hs = health_share(row.name if isinstance(row.name, str) else "")      # health share of government spending
    med, p90 = _v(row, "ghes_growth_median", 0.0), _v(row, "ghes_growth_p90", 0.0)
    p75 = _v(row, "ghes_growth_p75", 0.0)
    top = p90 if effort == "p90" else p75
    # surge = how much faster than usual GHES can grow in a strong year (a share of GHES a year, never negative)
    surge = max(0.0, top - max(med, 0.0))
    # interest % of revenue (fiscal_inputs.py, audit I-26): the more recent of World Bank and IMF WEO, else the
    # income-group median (estimated); never a silent default of 1
    intr = _v(row, "interest_pct_revenue")
    if np.isnan(intr):
        raise ValueError(f"{row.name}: no interest-to-revenue value (run fiscal_inputs.py)")
    # debt stress: 1 when interest takes <= 10% of revenue, falling linearly to 0.25 at >= 40%
    stress = float(np.clip(1 - (intr - 10) / 40, 0.25, 1.0))
    pop, gdp_pc = _v(row, "sp_pop_totl"), _v(row, "gdp_pc")
    rev_pct = _v(row, "gc_rev_xgrt_gd_zs")
    gdp = pop * gdp_pc if not (np.isnan(pop) or np.isnan(gdp_pc)) else np.nan     # US$ (for revenue in US$)
    return {"ghes": ghes, "ghes_growth_median": med, "ghes_growth_p90": p90, "ghes_growth_p75": p75,
            "ghes_growth_top": top, "effort": effort, "surge_rate": surge,
            "interest_pct_revenue": intr, "stress_factor": stress,
            "interest_year": _v(row, "interest_pct_revenue_year"),
            "interest_source": str(row.get("interest_pct_revenue_source", "")),
            "interest_estimated": bool(row.get("interest_estimated", False)),
            "capacity": (ghes * surge * stress) if not np.isnan(ghes) else 0.0,
            "gdp": gdp, "revenue": gdp * rev_pct / 100 if not np.isnan(rev_pct) else np.nan, "revenue_pct_gdp": rev_pct,
            "debt_pct_gdp": _v(row, "gc_dod_totl_gd_zs"), "ghes_pct_gov_spend": hs["share_pct"],
            "ghes_pct_gov_spend_year": hs["year"], "ghes_pct_gov_spend_estimated": hs["estimated"],
            "ghes_pct_gdp": _v(row, "ghes_pct_gdp_2023"), "ghes_pc": _v(row, "ghes_pc_2023")}


def epi(row: pd.Series, P: dict) -> dict:
    """Population in need and baseline coverage for each direct line.
    Returns need_cov: line -> (people in need, coverage 0-1 or NaN for the default), flags, ART coverage and source
    tags for malaria coverage. Feeds: people losing a service, coverage before -> after, deaths."""
    pop = _v(row, "sp_pop_totl")
    inc_hiv = _v(row, "sh_hiv_incd_tl") / pop * 1000 if pop else np.nan
    # malaria coverage (malaria_inputs.py, audit I-11): MAP 2025 where MAP has a value; otherwise a survey (treatment:
    # only where malaria is common; bednets: only from 2015 on) or NaN = the default. Spraying without a MAP estimate is
    # NaN here and set in run_country to the coverage donor IRS money pays for.
    itn, irs, cm = _v(row, "mal_itn_cov"), _v(row, "mal_irs_cov"), _v(row, "mal_cm_cov")
    art = _v(row, "sh_hiv_artc_zs") / 100
    pm = _v(row, "sh_hiv_pmtc_zs") / 100
    e = {
        "hiv_art": (_v(row, "plhiv"), art),
        "hiv_pmtct": (_v(row, "hiv_pos_pregnancies"), pm if not np.isnan(pm) else art),
        # notified / estimated incidence can exceed 100% by definition (WDI); capped at 100% and flagged (L-12)
        "tb_ds": (_v(row, "all_forms_of_tb_incidence_estimated"), min(_v(row, "sh_tbs_dtec_zs") / 100, 1.0)),
        # Batch 3+4 (IMP-11): the country's RR-TB share of incidence and RR treatment enrolment (WHO 2024,
        # tb_rr_share, tb_rr_cov in country_inputs.csv); the global constants where a country has none
        "tb_dr": (_v(row, "all_forms_of_tb_incidence_estimated") * _v(row, "tb_rr_share", DR_TB_SHARE),
                  _v(row, "tb_rr_cov", DR_TB_COV)),
        "mal_itn": (_v(row, "malaria_pop_at_risk"), itn),
        "mal_irs": (_v(row, "malaria_pop_at_risk"), irs),
        "mal_cm": (_v(row, "malaria_cases"), cm),
        "imm": (_v(row, "births"), _v(row, "sh_imm_idpt") / 100),
    }
    flags = []
    if _v(row, "sh_tbs_dtec_zs") > 100:
        flags.append(f"TB case detection rate is {_v(row, 'sh_tbs_dtec_zs'):.0f}% (notifications above WHO's incidence "
                     "estimate); capped at 100%")
    if np.isnan(itn):
        flags.append("bednet use: no MAP estimate or survey since 2015, default assumed")
    if np.isnan(cm):
        flags.append("malaria treatment coverage: no MAP estimate or usable survey, default assumed")
    return {"need_cov": e, "hiv_incidence_per_1000": inc_hiv, "flags": flags, "art_cov": art,
            "cov_source": {l: coverage_source(row, l) for l in ("mal_itn", "mal_irs", "mal_cm")}}


def coverage_source(row: pd.Series, line: str) -> str:
    """Short source tag for a malaria line's baseline coverage, e.g. 'MAP 2025', 'survey 2018', 'assumed'.
    Feeds: the source tag next to each malaria coverage value in the service table."""
    col = {"mal_itn": "mal_itn_cov", "mal_irs": "mal_irs_cov", "mal_cm": "mal_cm_cov"}[line]
    src, yr = row.get(f"{col}_source"), row.get(f"{col}_year")
    yr = f" {int(yr)}" if isinstance(yr, (int, float, np.integer, np.floating)) and not np.isnan(yr) else ""
    if isinstance(src, str) and src.startswith("MAP"):
        return src
    if src == "survey":
        return f"survey{yr}"
    return "implied by donor spending" if line == "mal_irs" else "assumed"


UC_REF_FILE = HERE / "unit_cost_reference.csv"


# US CPI-U annual averages (BLS series CUUR0000SA0), to bring study costs to 2023 US$ (2014 -> 2023 = 1.287, the
# factor already applied to the TB rows of unit_cost_reference.csv)
CPI_U = {2014: 236.736, 2018: 251.107, 2019: 255.657, 2020: 258.811, 2021: 270.970, 2022: 292.655, 2023: 304.702}
PRICE_YEAR = 2023


def inflate(value: float, cost_year: int) -> float:
    """A study cost in cost_year US$ -> 2023 US$ (US CPI-U).
    Feeds: unit costs taken from studies (ART site costs, malaria treatment, IRS)."""
    return value * CPI_U[PRICE_YEAR] / CPI_U[int(cost_year)]


def _uc_ref() -> dict:
    """Sourced unit-cost reference values (country ART studies, income-group TB costs), in 2023 US$: each value is
    inflated from its cost_year (ART site costs are 2018-2020 US$; TB rows are already 2023 US$).
    Feeds: unit_costs."""
    if not hasattr(_uc_ref, "cache"):
        r = pd.read_csv(UC_REF_FILE)
        _uc_ref.cache = {(k, key): inflate(float(v), y)
                         for k, key, v, y in zip(r["kind"], r["key"], r["value"], r["cost_year"])}
    return _uc_ref.cache


def income_group(row: pd.Series) -> str:
    """World Bank income group of a country row ('low_income', 'lower_middle_income', 'upper_middle_income'); without
    one, a rough guess from GDP per person (US$). Used for TB unit costs and the country header."""
    g = row.get("income_group") if hasattr(row, "get") else None
    if isinstance(g, str) and g:
        return g
    gdp = _v(row, "gdp_pc", 2000.0)                    # fallback: rough GDP-per-capita thresholds
    return "low_income" if gdp < 1150 else "lower_middle_income" if gdp < 4500 else "upper_middle_income"


def unit_costs(row: pd.Series, P: dict) -> dict:
    """Donor cost per unit of service. Site/provider costs from studies are grossed up for above-service spending.
    Returns line -> US$ per unit (2023 US$, arrays over draws). Feeds: Cost per Person and people losing a service."""
    ref = _uc_ref()
    iso = row.name if isinstance(row.name, str) else ""
    markup = 1.0 / (1.0 - P["asd_share"])                # site cost -> full donor program cost
    g = _v(row, "gdp_pc", 1000.0)
    # staff and delivery costs scale with income: (GDP per person / US$1,000)^elasticity, GDP floored at US$200
    sc = (max(g, 200.0) / 1000.0) ** P["uc_scale_elast"]
    # Batch 3+4 (IMP-03): the country's site cost per patient-year from country_inputs.csv (GHCC Unit Cost Study
    # Repository pooled with Rosen et al. 2021; 2023 US$; a regional or income-group median where the country has no
    # eligible study; batch34_inputs.py --art). The older rule (Rosen site costs for five countries, elsewhere ARVs +
    # income-scaled non-ARV costs) is the fallback only if the column is missing
    art_site = _v(row, "art_site_cost")
    if np.isnan(art_site):
        art_site = ref.get(("art_site_cost", iso))
    if art_site is None:                                  # no country study: ARVs + income-scaled non-ARV costs
        art_site = ref[("art_site_default", "arv")] + ref[("art_site_default", "non_arv")] * sc
    ig = income_group(row)
    ig_key = ig if ig in ("low_income", "lower_middle_income", "upper_middle_income") else "upper_middle_income"
    # Batch 3+4 (IMP-11): the country's provider cost per treatment course from country_inputs.csv (Value TB and GHCC
    # studies; income-group median pooled with Laurence et al. 2015 where the country has no study; 2023 US$;
    # batch34_inputs.py --tb). The income-group rows of unit_cost_reference.csv are the fallback if the column is missing
    tb_ds, tb_dr = _v(row, "tb_ds_cost"), _v(row, "tb_dr_cost")
    if np.isnan(tb_ds):
        tb_ds = ref[("tb_ds_cost", ig_key)]
    if np.isnan(tb_dr):
        tb_dr = ref[("tb_dr_cost", ig_key)]
    # HIV incidence per 1,000 people (0.3 if missing, clipped to 0.05-10): prevention costs more per infection averted
    # where infections are rare
    inc = _v(row, "sh_hiv_incd_tl") / _v(row, "sp_pop_totl") * 1000
    inc = 0.3 if np.isnan(inc) else float(np.clip(inc, 0.05, 10))
    one = np.ones_like(P["uc_imm"])
    # Batch 4b (L-50): the ART cost per patient-year the model uses is the lower of the GHCC-based full cost (site cost
    # x markup) and the observed HIV treatment spending per person on ART (Optima Table B2 or WHO GHED x the Global
    # Fund treatment share / UNAIDS people on ART), floored at first-line drugs plus a viral load test and gated to
    # US$50-600 (country_inputs.csv art_cost_full; audit/batch4b_art_check.py). Draws: uc_art_mult below 1 scales the
    # value down (study spread); above 1 it moves toward art_cost_full_hi (the higher of the two measures, within the
    # gate), reaching it at the parameter's high value
    art_full = _v(row, "art_cost_full")
    if np.isnan(art_full):
        hiv_art = art_site * P["uc_art_mult"] * markup
    else:
        hi_ = _v(row, "art_cost_full_hi", art_full)
        m = np.asarray(P["uc_art_mult"], dtype=float)
        hiv_art = np.where(m > 1.0, art_full * (1.0 + (m - 1.0) * (hi_ / art_full - 1.0) / ART_MULT_UP), art_full * m)
    return {
        "hiv_art": hiv_art,
        "hiv_pmtct": P["uc_pmtct"] * one,
        "hiv_prev": P["cpia_ref"] * (1.0 / inc) ** 0.5,          # $ per infection averted
        "hiv_ovc": P["uc_ovc"] * one,
        "tb_ds": tb_ds * P["uc_tb_mult"] * markup,
        "tb_dr": tb_dr * P["uc_tb_mult"] * markup,
        "mal_itn": P["uc_itn"] * one,                         # GiveWell / PMI costs are already full program costs
        "mal_irs": P["uc_irs"] * one,
        "mal_cm": P["uc_mal_cm"] * one,
        "imm": P["uc_imm"] * one,                             # Gavi spend per child is already a full program cost
    }


AID_BASE_YEARS = (2021, 2023)    # aid baseline = average of these years (prepare_model.py uses the same constant)
GHES_YEAR = 2023                 # government health spending year (column ghes_2023)
FALLBACK_MORTALITY_TREND = -0.009    # %/yr decline in baseline mortality (Cavalcanti et al. 2025, Lancet, appendix 10.2)
# Baseline death-rate trends apply where deaths are modelled as a share of a baseline level (malaria deaths, under-5
# mortality for vaccines). TB and HIV deaths are per patient (case fatality of an untreated vs a treated patient; the
# ART hazard), which a national death trend does not change, so their counterfactual is flat (logic review L-10).
TREND_COLUMNS = {"u5": "trend_u5mr", "malaria": "trend_malaria_deaths"}


def mortality_trend_factors(row: pd.Series, kind: str, use: bool = True) -> np.ndarray:
    """(1 + annual trend)^(year - 1) for years 1..5: baseline deaths keep falling (or rising) on the country's trend
    (under-5 mortality: 2010-2019; malaria: WHO estimated malaria deaths 2015-2024, malaria_inputs.py).
    kind: 'u5' (under-5 mortality rate) or 'malaria' (all-age malaria deaths). Ones when switched off.
    Feeds: deaths from vaccines and malaria in each year 2026-2030."""
    if not use:
        return np.ones(N_YEARS)
    t = _v(row, TREND_COLUMNS[kind])
    t = FALLBACK_MORTALITY_TREND if np.isnan(t) else t
    return (1.0 + t) ** np.arange(N_YEARS)


def _units_lost(net, base, unit_cost, covered, cap_base=None, donor_share=1.0):
    """Units of service lost (before continuity): donor-funded units x share of donor money lost. cap_base: the money
    that pays for the service itself, used to test whether donor money buys more than the donor-funded pool (for ART,
    the treatment money only, not the testing and care money that also counts toward it; audit I-09). donor_share:
    the external share of the country's spending on the disease (country_inputs.csv donor_share_*; Batch 3+4, IMP-04 /
    L-44): the donor-funded pool is at most covered x donor_share, so a line where donor money would buy more than that
    pool loses pool x share of money lost rather than treating every covered person as donor-funded.
    Feeds: People Losing Service (units, people or patient-years a year)."""
    net, base, unit_cost = np.asarray(net, dtype=float), np.asarray(base, dtype=float), np.asarray(unit_cost, dtype=float)
    cap_base = base if cap_base is None else np.asarray(cap_base, dtype=float)
    plain = net / unit_cost
    if np.isnan(covered):
        return plain
    pool = covered * donor_share
    funded = np.minimum(pool, cap_base / unit_cost)
    share = np.divide(net, base, out=np.zeros_like(net * base), where=np.abs(base) > 0)
    return np.where(cap_base / unit_cost > pool, funded * share, plain)


def per_unit_levels(row: pd.Series, P: dict, art_cov: float, trend: bool = True) -> dict:
    """Deaths per unit of service lost once the full effect has built up, by CALENDAR year 1..5 (arrays n x 5),
    for the lines handled year by year (PMTCT, TB, vaccines). The ramp-up (LAG) is applied separately, by how long the
    cut has been in force. trend: vaccine deaths scale with the country's falling under-5 mortality.
    Feeds: deaths for PMTCT, TB and vaccines."""
    n = len(P["uc_imm"])
    h = _v(row, "tb_hiv_share", 0.0)
    a = 0.0 if np.isnan(art_cov) else art_cov
    # untreated HIV+ TB: WHO Table 5 off ART (0.78) and on ART for a year or more (0.49), blended by ART coverage (L-13)
    cfr_up = P["tb_cfr_untreated_pos"] * (1 - a) + P["tb_cfr_untreated_pos_art"] * a
    cfr_tp = P["tb_cfr_treated_pos"] * (1 - 0.3 * a)
    dcfr = (1 - h) * (P["tb_cfr_untreated_neg"] - P["tb_cfr_treated_neg"]) + h * (cfr_up - cfr_tp)
    u5 = _v(row, "sh_dyn_mort", 50.0) * mortality_trend_factors(row, "u5", trend)       # per year 1..5
    ones = np.ones(N_YEARS)
    return {
        "hiv_pmtct": np.outer(P["pmtct_vt_reduction"] * P["pmtct_infant_mort"], ones),
        "hiv_prev": np.zeros((n, N_YEARS)), "hiv_ovc": np.zeros((n, N_YEARS)),
        "tb_ds": np.outer(dcfr, ones),
        "tb_dr": np.outer(P["tb_dr_dcfr"], ones),
        "imm": np.outer(P["imm_deaths_per_child_ref"] * P["imm_u5_share"], np.clip(u5 / 50.0, 0.3, 2.5)),
    }


def imm_legacy(row: pd.Series, P: dict) -> bool:
    """True when the vaccine pathway uses the pre-Batch-5+6 rule (imm_deaths_per_child_ref x imm_u5_share x
    clip(U5MR / 50, 0.3, 2.5), cohort weights 0.40 / 0.35 / 0.20 / 0.05): the sensitivity switch
    imm_legacy_u5mr_scaling = 1, or a country row without the VIMC columns."""
    if float(np.ravel(P.get("imm_legacy_u5mr_scaling", np.zeros(1)))[0]) >= 0.5:
        return True
    return np.isnan(_v(row, "imm_dpc")) or np.isnan(_v(row, "imm_dpc_lag0"))


def imm_per_child(row: pd.Series, P: dict) -> np.ndarray:
    """Deaths averted per fully immunized child by years since vaccination, k = 0..9 (arrays n x 10; Batch 5+6 V2):
    country_inputs.csv imm_dpc_lag0..lag9 (VIMC deaths averted per vaccinated child, 2015-2019, summed over the routine
    antigens the country uses, x the WPP Q5 2026-30 / 2015-19 ratio, spread by the fitted timing per pathogen;
    audit/batch56_vaccines.py), scaled by the draw of imm_dpc_mult: below 1 toward the country's VIMC low value
    (imm_dpc_lo / imm_dpc at the parameter's low, 0.56), above 1 toward its high value (at 1.64).
    Feeds: vaccine deaths 2026-2030 and 2031-2035, the lives-first ranking, the Validation per-child comparison."""
    lag = np.array([_v(row, f"imm_dpc_lag{k}", 0.0) for k in range(IMM_LAGS)])
    tot = _v(row, "imm_dpc", float(lag.sum()))
    lo_r = _v(row, "imm_dpc_lo", tot) / tot if tot > 0 else 1.0
    hi_r = _v(row, "imm_dpc_hi", tot) / tot if tot > 0 else 1.0
    m = np.asarray(P["imm_dpc_mult"], dtype=float)
    scale = np.where(m < 1.0, 1.0 - (1.0 - m) / (1.0 - IMM_MULT_LO) * (1.0 - lo_r),
                     1.0 + (m - 1.0) / (IMM_MULT_HI - 1.0) * (hi_r - 1.0))
    return np.outer(scale, lag)


def per_unit_deaths(row: pd.Series, P: dict, art_cov: float, trend: bool = True) -> dict:
    """Deaths per unit of service lost, by year 1..5 of a cut in force since year 1 (arrays n x 5). Malaria is
    handled separately (LiST). = per_unit_levels x LAG, plus the ART hazard ramp; vaccines (unless legacy) = the
    cumulative sum of the per-child deaths by years since vaccination (a child missed in year 1 of a sudden cut adds
    its lag-k deaths in year k + 1).
    Feeds: the 'lives first' ranking and per-line deaths."""
    lv = per_unit_levels(row, P, art_cov, trend)
    out = {l: v * (LAG[l] if LAG.get(l) is not None else 1.0) for l, v in lv.items()}
    out["hiv_art"] = hiv_art_params(row, P)[0][:, :N_YEARS]
    if not imm_legacy(row, P):
        out["imm"] = np.cumsum(imm_per_child(row, P)[:, :N_YEARS], axis=1)
    return out


def hiv_art_params(row, P: dict) -> tuple:
    """The ART cohort inputs for one country and one set of draws: (hazard n x 10 by years since stopping ART,
    transmission per person-year n, return-to-care share per year n, mean years newly infected people stay
    unsuppressed n or None). Transmission = art_transmission_mult x the country's UNAIDS rate of new infections per
    person with unsuppressed viral load (`art_transmission_rate` in country_inputs.csv; ART_TRANSMISSION_FALLBACK if
    missing). With hiv_legacy_art_params = 1: the pre-Batch-2 values (ART_HAZARD_LEGACY, art_transmission,
    ART_REENGAGE_LEGACY, no second generation).
    Feeds: HIV treatment deaths and infections (art_cohorts) and the lives-first ranking (per_unit_deaths)."""
    n = len(P["art_hazard_mult"])
    if float(np.ravel(P["hiv_legacy_art_params"])[0]) >= 0.5:
        return (np.outer(P["art_hazard_mult"], ART_HAZARD_LEGACY), P["art_transmission"] * np.ones(n),
                np.full(n, ART_REENGAGE_LEGACY), None)
    rate = _v(row, "art_transmission_rate", ART_TRANSMISSION_FALLBACK)
    return (np.outer(P["art_hazard_mult"], ART_HAZARD), P["art_transmission_mult"] * rate,
            P["art_reengage"] * np.ones(n), P["hiv_new_inf_unsup_years"] * np.ones(n))


def art_cohorts(stock: np.ndarray, hazard_by_age: np.ndarray, transmission: np.ndarray, reengage: np.ndarray,
                unsup_years=None):
    """People who stop ART tracked as cohorts. stock: (n x 5) people off ART in each year. A rise in the stock is a
    new cohort with years-since-stopping = 1; a fall returns the most recent cohorts to care first. Each cohort's
    excess death risk follows hazard_by_age (n x H, by its own years since stopping; the last value after that), and
    it transmits HIV at `transmission` per person-year (half in its first year). Negative stock (aid gains) uses the
    hazard of the calendar year, as before.
    After 2030 funding is back: people still off care return at `reengage` a year (mid-year average), and those who
    have not yet returned keep their risk. unsup_years (n, or None = off): the people infected by the cohorts are
    themselves unsuppressed for a mean of that many years (exponential) and transmit at the same rate, one further
    generation (second-generation infections, Batch 2). Returns (deaths n x 5, infections n x 5, deaths n x POST,
    infections n x POST, people still off care n x POST) for 2026-2030 and 2031-2035.
    Feeds: HIV treatment deaths and new infections from people off ART, 2026-2035."""
    n, H = stock.shape[0], hazard_by_age.shape[1]
    pos, neg = np.clip(stock, 0, None), np.clip(stock, None, 0)
    deaths, infections = np.zeros((n, N_YEARS)), np.zeros((n, N_YEARS))
    cohorts = []                                       # [size (n,), age]
    prev = np.zeros(n)
    for t in range(N_YEARS):
        delta = pos[:, t] - prev
        drop = np.clip(-delta, 0, None)
        for c in reversed(cohorts):                    # the most recent cohorts return to care first
            take = np.minimum(c[0], drop)
            c[0] = c[0] - take
            drop = drop - take
        cohorts.append([np.clip(delta, 0, None), 1])
        for size, age in cohorts:
            a = min(age, H) - 1
            deaths[:, t] += size * hazard_by_age[:, a]
            infections[:, t] += size * transmission * ART_INFECT_LAG[min(a, N_YEARS - 1)]
        for c in cohorts:
            c[1] += 1
        prev = pos[:, t]
        deaths[:, t] += neg[:, t] * hazard_by_age[:, t]          # gains: same as the sudden-cut formula
        infections[:, t] += neg[:, t] * transmission * ART_INFECT_LAG[t]
    post_d, post_i, off = np.zeros((n, POST_YEARS)), np.zeros((n, POST_YEARS)), np.zeros((n, POST_YEARS))
    for size, age in cohorts:                          # still off care at the end of 2030
        for k in range(POST_YEARS):
            stay = size * (1 - reengage) ** (k + 0.5)
            a = min(age + k, H) - 1
            post_d[:, k] += stay * hazard_by_age[:, a]
            post_i[:, k] += stay * transmission * ART_INFECT_LAG[min(a, N_YEARS - 1)]
            off[:, k] += stay
    if unsup_years is not None:
        # second generation: an infection in mid-year s contributes w[k] unsuppressed person-years in year s + k, with
        # exponential time to suppression of mean unsup_years; each transmits at the same rate (no third generation)
        T = N_YEARS + POST_YEARS
        D = np.asarray(unsup_years, dtype=float)[:, None]
        edges = np.arange(T + 1) - 0.5
        cum = D * (1 - np.exp(-np.clip(edges, 0, None) / D))           # integral of exp(-u/D) from 0 to each edge
        w = cum[:, 1:] - cum[:, :-1]                                      # n x T
        first = np.hstack([infections, post_i])
        second = np.zeros_like(first)
        for s_ in range(T):
            for t in range(s_, T):
                second[:, t] += first[:, s_] * w[:, t - s_] * transmission
        infections = infections + second[:, :N_YEARS]
        post_i = post_i + second[:, N_YEARS:]
    return deaths, infections, post_d, post_i, off


def hiv_death_timing(median: np.ndarray, n_years: int) -> np.ndarray:
    """Share of the eventual HIV deaths among people infected (mid-year) in year 0 that happen in years 0..n_years-1
    after infection, without treatment: Weibull survival with shape HIV_WEIBULL_SHAPE and the given median (years).
    Returns n x n_years.
    Feeds: deaths from new HIV infections (2026-2030 and 2031-2035)."""
    lam = np.asarray(median, dtype=float)[:, None] / np.log(2) ** (1 / HIV_WEIBULL_SHAPE)
    k = np.arange(n_years)[None, :]
    F = lambda t: 1 - np.exp(-(np.maximum(t, 0) / lam) ** HIV_WEIBULL_SHAPE)
    return F(k + 0.5) - F(k - 0.5)


# under-5 share of malaria deaths where the country's child series is missing: WHO World Malaria Report regional shares
# (the same values prepare_model.py uses to derive missing all-age deaths). Used only by the sensitivity switch.
MALARIA_U5_SHARE_FALLBACK = {True: 0.76, False: 0.40}


def malaria_u5_share_country_series(row) -> float:
    """The previous rule, kept as a sensitivity check (mal_u5_use_country_series = 1): WHO/MCEE child malaria deaths
    (`malaria_deaths_in_children_1_59_months_total_deaths`, 2021) / WHO all-age malaria deaths (2024), clipped to 0-1;
    0.76 (sub-Saharan Africa) / 0.40 where either is missing. It divides two estimation methods and years, which gives
    implausible values (Nigeria 0.98, Kenya 0.19, Ethiopia 0.11), so it is off by default."""
    d0, child = _v(row, "malaria_deaths"), _v(row, "malaria_deaths_in_children_1_59_months_total_deaths")
    if np.isnan(d0) or d0 <= 0 or np.isnan(child):
        ssa = row.get("is_ssa", False)
        return MALARIA_U5_SHARE_FALLBACK[isinstance(ssa, (bool, np.bool_)) and bool(ssa)]
    return float(np.clip(child / d0, 0.0, 1.0))


def malaria_u5_share(row, P) -> np.ndarray:
    """Share of the country's malaria deaths that are in children under 5 (arrays over draws): the World Malaria Report
    2025 share for the country's WHO region (`malaria_u5_share_param` in country_inputs.csv names the parameter,
    mal_u5_share_<region>; rule a). Countries with no WMR figure (European Region: no malaria deaths, no global figure
    in the report) get 0, which has no effect because their malaria deaths are 0. mal_u5_use_country_series = 1
    switches to the old country series (sensitivity check).
    Feeds: malaria deaths (the Lives Saved Tool effects are child effect sizes)."""
    n = len(P["mal_vc_eff"])
    if float(np.ravel(P["mal_u5_use_country_series"])[0]) >= 0.5:
        return np.full(n, malaria_u5_share_country_series(row))
    par = row.get("malaria_u5_share_param")
    if isinstance(par, str) and par in P:
        return np.asarray(P[par], dtype=float) * np.ones(n)
    return np.zeros(n)


def malaria_levels(row, P, units, need_cov) -> dict:
    """Lives Saved Tool structure: D1 = D0 * prod_i (1 - E_i C_i1) / (1 - E_i C_i0), for one year's units lost.
    Vector control is one intervention whose coverage combines bednets and spraying: C_vc = 1 - (1 - ITN use) x
    (1 - IRS coverage), each reduced by its own people losing the service / people at risk. Treatment coverage is the
    share of malaria cases that get an effective drug (MAP); mal_cm_eff is how much that reduces deaths (separate steps,
    as in the Lives Saved Tool). The effects are child effect sizes: D0 is split into under-5 deaths (full effects) and
    deaths at 5 and over (effects x mal_adult_effect_frac), each with the formula above, and the two are added.
    Returns the yearly extra deaths per line (arrays n) at baseline D0, before ramp-up and the mortality trend.
    Feeds: malaria deaths by line (bednets, spraying, treatment)."""
    D0 = _v(row, "malaria_deaths")
    n = len(P["mal_vc_eff"])
    if np.isnan(D0) or D0 <= 0:
        return {k: np.zeros(n) for k in ("mal_itn", "mal_irs", "mal_cm")}
    par, itn0 = need_cov["mal_itn"]
    _, irs0 = need_cov["mal_irs"]
    cases, ccm0 = need_cov["mal_cm"]
    itn0 = P["mal_itn_default_use"] if np.isnan(itn0) else np.full(n, itn0)
    irs0 = np.zeros(n) if np.isnan(irs0) else np.full(n, irs0)
    ccm0 = P["mal_cm_default_cov"] if np.isnan(ccm0) else np.full(n, ccm0)
    # L-04 / L-20: the Lives Saved Tool effects are for children 1-59 months. They apply in full to under-5 deaths; for
    # deaths at age 5 and over they are scaled by mal_adult_effect_frac (no published adult effect size)
    Ev, Ec = P["mal_vc_eff"], P["mal_cm_eff"]
    fa = P["mal_adult_effect_frac"]
    s_u5 = malaria_u5_share(row, P)
    ok_par = bool(par) and not np.isnan(par)
    itn1 = np.clip(itn0 - (units["mal_itn"] / par if ok_par else 0), 0, 1)
    irs1 = np.clip(irs0 - (units["mal_irs"] / par if ok_par else 0), 0, 1)
    ccm1 = np.clip(ccm0 - (units["mal_cm"] / cases if cases and not np.isnan(cases) else 0), 0, 1)

    def vc(i, r):
        """Combined vector-control coverage: 1 - (1 - bednet use)(1 - spraying coverage), all shares 0-1."""
        return 1 - (1 - i) * (1 - r)
    cvc0, cvc1 = vc(itn0, irs0), vc(itn1, irs1)
    total = np.zeros(n)
    dv, dc = np.zeros(n), np.zeros(n)
    for d_grp, ev, ec in ((D0 * s_u5, Ev, Ec), (D0 * (1 - s_u5), Ev * fa, Ec * fa)):
        rv = (1 - ev * cvc1) / (1 - ev * cvc0)
        rc = (1 - ec * ccm1) / (1 - ec * ccm0)
        total = total + d_grp * (rv * rc - 1)
        dv, dc = dv + d_grp * (rv - 1), dc + d_grp * (rc - 1)
    denom = np.where(np.abs(dv) + np.abs(dc) > 0, np.abs(dv) + np.abs(dc), 1)
    dv_s, dc_s = total * np.abs(dv) / denom, total * np.abs(dc) / denom
    # vector-control deaths split by each line's own fall in combined coverage (the other line held at baseline)
    d_itn, d_irs = cvc0 - vc(itn1, irs0), cvc0 - vc(itn0, irs1)
    tot = d_itn + d_irs
    sh_itn = np.where(tot > 0, d_itn / np.where(tot > 0, tot, 1), 0.5)
    return {"mal_itn": dv_s * sh_itn, "mal_irs": dv_s * (1 - sh_itn), "mal_cm": dc_s}


def malaria_deaths(row, P, units, need_cov, trend: bool = True) -> dict:
    """Per-line yearly malaria deaths (n x 5) for a cut in force since year 1: levels x LAG x mortality trend.
    trend: baseline malaria deaths D0 follow the country's 2015-2024 WHO malaria death trend in years 1..5.
    Feeds: malaria deaths in the service table and headline."""
    lv = malaria_levels(row, P, units, need_cov)
    f = mortality_trend_factors(row, "malaria", trend)          # D0 x (1 + trend)^(year - 1)
    return {l: np.outer(v, LAG[l] * f) for l, v in lv.items()}


# --------------------------------------------------------------------------- #
# Core
# --------------------------------------------------------------------------- #
def _path(x, default) -> np.ndarray:
    """A funding path or government-money path as an array of 5 values (2026-2030); `default` repeated when None. Raises
    an error for any other length."""
    v = np.full(N_YEARS, float(default)) if x is None else np.asarray(x, dtype=float).ravel()
    if v.size != N_YEARS:
        raise ValueError(f"a year path needs {N_YEARS} values (2026-2030), got {v.size}")
    return v


def run_country(iso3: str, scenario: Scenario, fiscal: Fiscal, inputs: dict, ptab: pd.DataFrame,
                n_draws: int = 400, seed: int = 7, keep_draws: bool = False, mortality_trend: bool = True,
                cut_path=None, gov_add_usd=None) -> dict:
    """The full model for one country. cut_path: share of the scenario's full cut in force in each year 2026-2030
    (default all 1 = a sudden cut). gov_add_usd: extra government health money in each year (default 0), on top of
    the government response in `fiscal`. With the defaults the results are the same as the original sudden-cut model.
    Feeds: every Section 4 number for the selected country (headline, The Numbers, service table, charts, fiscal
    panel) and each row of the All Countries page."""
    cut_path = np.clip(_path(cut_path, 1.0), 0.0, 1.0)
    gov_add = np.clip(_path(gov_add_usd, 0.0), 0.0, None)
    ci, lines = inputs["ci"], inputs["lines"]
    if scenario.mou_only and iso3 not in scenario.us_direct_path_by_country:
        raise ValueError(f"{iso3}: no MOU funding schedule, so the America First MOUs scenario can't be run")
    row = ci.loc[iso3] if iso3 in ci.index else pd.Series(dtype=float)
    cells = lines[lines.iso3 == iso3].copy()
    # cut on each cell in each year: the scenario's own yearly cuts (MOU schedules) x the funding path
    cut_y = scenario.cuts_by_year(cells, iso3, inputs["trend_map"]) if len(cells) else np.zeros((0, N_YEARS))
    cut_m = cut_y * cut_path[None, :]
    usd = cells["usd"].to_numpy()
    gross_t = [pd.Series(usd * cut_m[:, t], index=cells.index).groupby(cells["line"]).sum() for t in range(N_YEARS)]
    gross_full_t = [pd.Series(usd * cut_y[:, t], index=cells.index).groupby(cells["line"]).sum()
                    for t in range(N_YEARS)]
    # a service line whose aid rises counts as no loss: gains aren't modelled (I-15); the rise is kept for the notes
    gains_t = [(-g).clip(lower=0) for g in gross_t]
    gross_t = [g.clip(lower=0) for g in gross_t]
    gross_full_t = [g.clip(lower=0) for g in gross_full_t]
    cells["cut"] = cut_m.mean(axis=1) if len(cells) else []          # average yearly cut (shown in charts)
    cells["loss"] = cells["usd"] * cells["cut"]

    base = cells.groupby("line")["usd"].sum()
    gross = (sum(gross_t) / N_YEARS) if len(cells) else pd.Series(dtype=float)   # average yearly loss by line, >= 0
    gains = (sum(gains_t) / N_YEARS) if len(cells) else pd.Series(dtype=float)   # average yearly rise by line
    P = draw_params(ptab, n_draws, seed)
    Pc = draw_params(ptab, 0)
    n = len(P["uc_imm"])

    # ---- 1. money: effective loss by direct line (per draw because kappa is uncertain) ----
    def unspec_shares(b):
        """The country's split of unspecified money by purpose (L-43): treatment, prevention, testing, systems,
        programme management; from country_inputs.csv (Global Fund module shares, or a regional median), else the
        global median of the model countries."""
        tag = UNSPEC_TAG[b]
        cols = [f"unspec_{tag}_{c}" for c in ("treatment", "prevention", "testing", "rssh", "pm")]
        v = np.array([_v(row, c) for c in cols])
        if np.isnan(v).any() or v.sum() <= 0:
            v = np.array([inputs["unspec_shares"][b][c] for c in ("treatment", "prevention", "testing", "rssh", "pm")])
        return v / v.sum()

    def sub_mix(lines_, mix):
        m = pd.Series({l: mix.get(l, 0.0) for l in lines_})
        if m.sum() <= 0:
            m = pd.Series({l: inputs["global_mix"][LINE_BUCKET[l]].get(l, 0.0) for l in lines_})
        return m / m.sum() if m.sum() > 0 else m

    def effective(series, kappa, sigma):
        """Money by line after splitting unspecified money by purpose (L-43) and treating systems money as above-site
        money (L-05). Unspecified money U: U x treatment share to the treatment lines by the country's mix, U x
        prevention share to the prevention lines by mix (TB has none: non-service), U x testing share to the
        testing-and-care pool (HIV: the linked line; TB and malaria: kappa of it counts toward the treatment line, the
        rest is non-service), U x systems share joins HSS money, U x programme-management share is non-service.
        Systems money (HSS plus that share) is above-site money that the marked-up unit costs already price into every
        patient, so only sigma = hss_service_share of it (default 0) is spread as service money by the full mix; the
        rest is nonservice[bucket]. Linked lines (HIV testing and care) keep kappa x their pool as service money (it
        counts toward the target line's units) and put the rest in nonservice[line]."""
        eff, nonservice = {}, {}
        for b in BUCKETS:
            known = DIRECT[b] + LINKED_IN[b]
            d = series.reindex(known).fillna(0.0)
            bmix = base.reindex(known).fillna(0.0)
            mix = (bmix / bmix.sum()) if bmix.sum() > 0 else pd.Series(inputs["global_mix"][b])
            u = series.get(UNSPEC.get(b, ""), 0.0)
            s = series.get(HSS.get(b, ""), 0.0)
            if b in UNSPEC_TAG:
                sh_t, sh_p, sh_x, sh_r, sh_m = unspec_shares(b)
            else:
                sh_t, sh_p, sh_x, sh_r, sh_m = 1.0, 0.0, 0.0, 0.0, 0.0
            s_all = s + u * sh_r                                  # systems money incl. the systems share of unspecified
            add = {l: sigma * s_all * mix.get(l, 0.0) for l in known}
            tm = sub_mix(UNSPEC_TREAT.get(b, DIRECT[b]), mix)
            for l, w in tm.items():
                add[l] += u * sh_t * w
            ns_extra = u * sh_m
            if UNSPEC_PREV.get(b):
                pm_ = sub_mix(UNSPEC_PREV[b], mix)
                for l, w in pm_.items():
                    add[l] += u * sh_p * w
            else:
                ns_extra += u * sh_p
            if LINKED_IN[b]:
                add[LINKED_IN[b][0]] += u * sh_x                   # into the testing-and-care pool (kappa applies below)
            elif b in UNSPEC_TEST_TARGET:
                add[UNSPEC_TEST_TARGET[b]] += kappa * u * sh_x
                ns_extra = ns_extra + (1 - kappa) * u * sh_x
            for l in DIRECT[b]:
                eff[l] = d[l] + add[l]
            for l in LINKED_IN[b]:
                pool = d[l] + add[l]                                # its own money + its share of unspecified money
                eff[l], nonservice[l] = kappa * pool, (1 - kappa) * pool
            nonservice[b] = (1 - sigma) * s_all + ns_extra
        return eff, nonservice

    eff_base, _ = effective(base, P["hss_kappa"], P["hss_service_share"])
    effc_base, nsc_base = effective(base, Pc["hss_kappa"], Pc["hss_service_share"])

    # ---- 2. fiscal response, year by year ----
    # aid lost in year t = full scenario loss x cut_path(t); the government response in `fiscal` applies to that year's
    # loss (capped by fiscal space), then any extra money (gov_add) is added. Net gap = loss - both, floored at 0.
    fs = fiscal_space(row, fiscal.effort)
    # full-cut yearly loss (the scenario's own deepest year), reported for the fiscal panel and break-even
    G = float(max(np.clip(g, 0, None).sum() for g in gross_full_t)) if len(cells) else 0.0

    def response(g):
        """The government's replacement in one year for an aid loss g (US$): none / gradual 0, a set share theta x g, or
        all of g; capped at fiscal capacity when the cap is on (always for 'as much as fiscal space allows'). Returns
        (replacement, amount wanted), US$."""
        want = {"none": 0.0, "gradual": 0.0, "custom": fiscal.theta * g, "max": g}[fiscal.mode]
        r = min(want, fs["capacity"]) if (fiscal.cap_to_space or fiscal.mode == "max") else want
        return max(r, 0.0), want

    G_t = np.array([float(np.clip(g, 0, None).sum()) for g in gross_t]) if len(cells) else np.zeros(N_YEARS)
    R_t = np.array([response(g)[0] for g in G_t])                    # the existing government response, per year
    budget_t = np.minimum(R_t + gov_add, G_t)                        # total replacement, never more than is lost
    R, want = response(G)                                            # full-cut values, reported for the fiscal panel

    ep = epi(row, Pc)
    ucc = unit_costs(row, Pc)
    # spraying coverage = the larger of MAP's estimate and the coverage donor IRS money pays for (people it buys /
    # people at risk), so losing that money removes the spraying it bought even where MAP shows little or none (MAP
    # models IRS for Africa only; elsewhere the implied coverage is used on its own)
    par, irs = ep["need_cov"]["mal_irs"]
    if par and not np.isnan(par):
        bought = float(np.asarray(effc_base["mal_irs"]).ravel()[0]) / float(ucc["mal_irs"][0])
        implied = float(np.clip(bought / par, 0, 1))
        if np.isnan(irs) or implied > irs:
            ep["need_cov"]["mal_irs"] = (par, implied)
            if not np.isnan(irs):
                ep["cov_source"]["mal_irs"] = f"implied by donor spending; {ep['cov_source']['mal_irs']}: {irs:.0%}"
    pudc = per_unit_deaths(row, Pc, ep["art_cov"], mortality_trend)

    # deaths per $ (central) for "lives first" ranking; malaria via a small marginal LiST calculation
    def deaths_per_dollar(l):
        """Deaths over 5 years per US$ lost on one service line (central parameters), used to rank lines for the 'lives
        first' allocation. Malaria uses a small Lives Saved Tool calculation for US$1M."""
        if l in pudc:
            return float(pudc[l].sum() / ucc[l][0])
        if l.startswith("mal_"):
            u = {k: np.zeros(1) for k in ("mal_itn", "mal_irs", "mal_cm")}
            u[l] = np.array([1e6 / ucc[l][0]])
            return float(malaria_deaths(row, Pc, u, ep["need_cov"], mortality_trend)[l].sum() / 1e6)
        return 0.0

    dpd = {l: deaths_per_dollar(l) for l in ALL_DIRECT}
    dpd.update({l: dpd[t] for l, t in LINKED.items()})           # linked money works through its target line

    def allocate(eff_d, nons, budget):
        """Split a replacement budget over lines with a loss. Returns (by direct line, by bucket systems)."""
        pos = {l: np.clip(np.asarray(v, dtype=float), 0, None) for l, v in eff_d.items()}
        posn = {b: np.clip(np.asarray(v, dtype=float), 0, None) for b, v in nons.items()}
        tot = sum(pos.values()) + sum(posn.values())
        rep = {l: np.zeros_like(v) for l, v in pos.items()}
        repn = {b: np.zeros_like(v) for b, v in posn.items()}
        if budget <= 0:
            return rep, repn
        safe = np.where(tot > 0, tot, 1)
        if fiscal.allocation == "pro_rata":
            rep = {l: budget * v / safe for l, v in pos.items()}
            repn = {b: budget * v / safe for b, v in posn.items()}
        else:                                  # lives first: most deaths averted per dollar gets refilled first
            left = np.full_like(np.asarray(tot, dtype=float), budget)
            for l in sorted(MONEY_LINES, key=lambda k: -dpd[k]):
                take = np.minimum(left, pos[l])
                rep[l], left = take, left - take
            sn = sum(posn.values())
            repn = {b: np.minimum(v, left * v / np.where(sn > 0, sn, 1)) for b, v in posn.items()}
        return rep, repn

    # per year: effective loss scaled by the path, replacement allocated, net loss by line
    years = range(N_YEARS)
    effc_t, repc_t, repnc_t, net_t, netc_t, nsc_t_all = [], [], [], [], [], []
    for t in years:
        e_t, ns_t = effective(gross_t[t], P["hss_kappa"], P["hss_service_share"])
        ec_t, nsc_t = effective(gross_t[t], Pc["hss_kappa"], Pc["hss_service_share"])
        r, _ = allocate(e_t, ns_t, budget_t[t])
        rc, rnc = allocate(ec_t, nsc_t, budget_t[t])
        effc_t.append(ec_t)
        repc_t.append(rc)
        repnc_t.append(rnc)
        nsc_t_all.append(nsc_t)
        net_t.append({l: e_t[l] - r[l] for l in MONEY_LINES})
        netc_t.append({l: ec_t[l] - rc[l] for l in MONEY_LINES})

    # ---- 3. coverage: people losing each service in each year ----
    uc = unit_costs(row, P)
    units = {l: np.zeros((n, N_YEARS)) for l in ALL_DIRECT}           # per draw x year
    unitsc = {l: np.zeros((1, N_YEARS)) for l in ALL_DIRECT}          # central x year
    capped, excess, funded, donor_share = {}, {}, {}, {}
    pm_need, pm_cov = ep["need_cov"]["hiv_pmtct"]
    pmtct_covered = pm_need * pm_cov if not (np.isnan(pm_need) or np.isnan(pm_cov)) else 0.0
    for l in ALL_DIRECT:
        need, cov = ep["need_cov"].get(l, (np.nan, np.nan))
        if l == "mal_itn" and np.isnan(cov):
            cov = Pc["mal_itn_default_use"][0]
        if l == "mal_cm" and np.isnan(cov):
            cov = Pc["mal_cm_default_cov"][0]
        # people losing the service = people donor money pays for x share of that money lost. Donor money pays for
        # min(people covered, aid / cost per person): when aid exceeds the full cost of everyone covered, the excess
        # pays for things other than the service itself, so the loss scales proportionally instead of running past
        # the people covered. When aid buys less than full coverage this equals net loss / cost per person.
        covered = cov * need if (l in ep["need_cov"] and not np.isnan(need) and not np.isnan(cov)) else np.nan
        # pregnant women on PMTCT (Option B+) are on ART, but their ART is in the PMTCT cost and paid from PMTCT money
        # (audit I-27), so they are not part of the people the ART line's money can pay for or lose
        if l == "hiv_art" and not np.isnan(covered):
            covered = max(covered - pmtct_covered, 0.0)
        # the donor-funded pool is at most the external share of the country's spending on the disease x the people
        # covered (Batch 3+4, IMP-04 / L-44; GHED and WHO TB financing; 1 if the country has no value)
        dsh = _v(row, f"donor_share_{DONOR_SHARE_LINE.get(l, DONOR_SHARE_TAG[LINE_BUCKET[l]])}", 1.0)
        if np.isnan(dsh) and l in DONOR_SHARE_LINE:
            dsh = _v(row, f"donor_share_{DONOR_SHARE_TAG[LINE_BUCKET[l]]}", 1.0)
        dsh = 1.0 if np.isnan(dsh) else float(np.clip(dsh, 0.0, 1.0))
        donor_share[l] = dsh
        b0 = float(np.asarray(effc_base[l]).ravel()[0])
        funded[l] = b0 / float(ucc[l][0]) if np.isnan(covered) else min(covered * dsh, b0 / float(ucc[l][0]))
        excess[l] = bool(not np.isnan(covered) and b0 / float(ucc[l][0]) > covered * dsh * (1 + 1e-9))   # tolerance: ties
        if excess[l] and (iso3, l) not in _EXCESS_LOGGED:
            _EXCESS_LOGGED.add((iso3, l))
            log.warning("%s %s: donor aid ($%.0f) buys %.0f units at $%.0f each, more than the donor-funded pool of %.0f "
                        "(%.0f people covered x external share %.2f); units lost scaled proportionally", iso3, l, b0,
                        b0 / float(ucc[l][0]), float(ucc[l][0]), covered * dsh, covered, dsh)
        capped[l] = False
        # linked money (HIV testing and care -> ART) adds to this line's money lost and its base, but whether donor
        # money buys more than everyone covered is judged on the line's own money only (audit I-09)
        links = [k for k, t in LINKED.items() if t == l]
        for t in years:
            n_t = net_t[t][l] + sum(net_t[t][k] for k in links)
            nc_t = netc_t[t][l] + sum(netc_t[t][k] for k in links)
            b_all = eff_base[l] + sum(eff_base[k] for k in links)
            bc_all = effc_base[l] + sum(effc_base[k] for k in links)
            u = _units_lost(n_t, b_all, uc[l], covered, cap_base=eff_base[l], donor_share=donor_share[l]) * (1 - P["continuity"])
            uc0 = _units_lost(nc_t, bc_all, ucc[l], covered, cap_base=effc_base[l], donor_share=donor_share[l]) * (1 - Pc["continuity"])
            if l in ep["need_cov"] and not np.isnan(need) and not np.isnan(cov):
                hi = covered if l == "hiv_art" else cov * need
                capped[l] = capped[l] or bool(np.ravel(uc0)[0] > hi)
                u, uc0 = np.minimum(u, hi), np.minimum(uc0, hi)
            # never negative: aid rises count as no loss (I-15), so this only removes floating-point noise when the
            # government replaces a line in full
            units[l][:, t], unitsc[l][:, t] = np.maximum(u, 0.0), np.maximum(uc0, 0.0)
    # bednets and spraying each have their own coverage now (MAP ITN use, MAP IRS coverage), so each line is capped at
    # its own people covered above; their combined effect is computed in malaria_levels

    # ---- 4. lives ----
    # ramp-up (LAG) is indexed by how long the cut has been in force, not by calendar year
    # the cut "starts" in the first year anything is cut (a funding path, or a schedule that begins later)
    started = np.flatnonzero(np.abs(cut_m).sum(axis=0) > 0) if len(cells) else np.flatnonzero(cut_path > 0)
    dur = np.array([t - started[0] if started.size and t >= started[0] else 0 for t in years])
    mal_f = mortality_trend_factors(row, "malaria", mortality_trend)

    tb_need, tb_cov = ep["need_cov"]["tb_ds"]
    art_need, art_cov0 = ep["need_cov"]["hiv_art"]
    u5_trend = _v(row, TREND_COLUMNS["u5"])
    u5_trend = (FALLBACK_MORTALITY_TREND if np.isnan(u5_trend) else u5_trend) if mortality_trend else 0.0
    IMM_COHORT = np.diff(np.r_[0.0, LAG["imm"]])       # a missed birth cohort's deaths by years since: .40 .35 .20 .05 0
    TB_ARRIVAL = (0.5, 0.5)                            # secondary TB cases appear 1 and 2 years after the untreated year

    def lives(Px, U):
        """Deaths (n x 5), infections (n x 5) and deaths in 2031-2035 set in motion by the 2026-2030 losses (dict of n
        arrays) for one set of draws, with funding back from 2031. Parts: people still off ART (hiv_art), new HIV
        infections (hiv_infections), missed birth cohorts (imm) and TB spread from untreated cases (tb)."""
        nx = len(Px["uc_imm"])
        lv = per_unit_levels(row, Px, ep["art_cov"], mortality_trend)
        d, inf, after = {}, {}, {}
        for l in ("hiv_pmtct", "hiv_prev", "hiv_ovc", "tb_ds", "tb_dr"):
            lag = LAG.get(l)
            ramp = np.array([lag[k] for k in dur]) if lag is not None else np.ones(N_YEARS)
            d[l] = U[l] * lv[l] * ramp                                      # year t depends only on year t's loss
        # vaccines: each year's missed birth cohort dies over the following years. Batch 5+6 (V2): by the VIMC
        # deaths averted per fully immunized child by years since vaccination (imm_per_child, lags 0-9; the 2026-2030
        # mortality level is already in the value, so no calendar trend applies); deaths falling in 2031-2035 count as
        # further deaths, those beyond 2035 (lags past the window) are not counted. Legacy rule (sensitivity switch):
        # IMM_COHORT weights x the under-5-mortality level of the year they happen (trend continues after 2030)
        d["imm"] = np.zeros((nx, N_YEARS))
        after["imm"] = np.zeros(nx)
        if imm_legacy(row, Px):
            for s_ in years:
                for k in range(N_YEARS):
                    t = s_ + k
                    if t < N_YEARS:
                        d["imm"][:, t] += U["imm"][:, s_] * IMM_COHORT[k] * lv["imm"][:, t]
                    else:                                                   # after 2030, mortality keeps its trend
                        after["imm"] += U["imm"][:, s_] * IMM_COHORT[k] * lv["imm"][:, -1] * (1 + u5_trend) ** (t - 4)
        else:
            w_imm = imm_per_child(row, Px)
            for s_ in years:
                for k in range(IMM_LAGS):
                    t = s_ + k
                    if t < N_YEARS:
                        d["imm"][:, t] += U["imm"][:, s_] * w_imm[:, k]
                    elif t < N_YEARS + POST_YEARS:
                        after["imm"] += U["imm"][:, s_] * w_imm[:, k]
        # TB spread: untreated person-years cause secondary cases 1-2 years later, treated at that year's reduced
        # coverage; cases arriving after 2030 are set in motion by the cut
        h = _v(row, "tb_hiv_share", 0.0)
        a_ = 0.0 if np.isnan(ep["art_cov"]) else ep["art_cov"]
        cfr_u = (1 - h) * Px["tb_cfr_untreated_neg"] + h * (Px["tb_cfr_untreated_pos"] * (1 - a_)
                                                            + Px["tb_cfr_untreated_pos_art"] * a_)
        cfr_t = (1 - h) * Px["tb_cfr_treated_neg"] + h * Px["tb_cfr_treated_pos"] * (1 - 0.3 * a_)
        ok_tb = not (np.isnan(tb_need) or np.isnan(tb_cov) or tb_need <= 0)
        cov_t = [np.clip(tb_cov - U["tb_ds"][:, t] / tb_need, 0, 1) if ok_tb else np.full(nx, 0.0) for t in years]
        after["tb"] = np.zeros(nx)
        # secondary deaths belong to the line whose lost patients generated them (tb_ds or tb_dr), so each line's
        # deaths stay within its own people affected (Batch 3+4: with systems money no longer converted, a line can
        # have no lost patients while the other TB line has some)
        for src in ("tb_ds", "tb_dr"):
            for s_ in years:
                sec = U[src][:, s_] * Px["tb_secondary"]
                for k, share in enumerate(TB_ARRIVAL, start=1):
                    t = s_ + k
                    c = cov_t[min(t, N_YEARS - 1)]
                    dd = sec * share * (c * cfr_t + (1 - c) * cfr_u)
                    if t < N_YEARS:
                        d[src][:, t] += dd
                    else:
                        after["tb"] += dd
        # HIV treatment cohorts (2026-2030, and those still off care in 2031-2035)
        hz, trans, reengage, unsup = hiv_art_params(row, Px)
        d["hiv_art"], inf["hiv_art"], post_d, post_i, off_post = art_cohorts(U["hiv_art"], hz, trans, reengage, unsup)
        after["hiv_art"] = post_d.sum(axis=1)
        # malaria: Lives Saved Tool each year; lost vector control rebounds while the loss lasts
        mal = {k: np.zeros((nx, N_YEARS)) for k in ("mal_itn", "mal_irs", "mal_cm")}
        for t in years:
            m = malaria_levels(row, Px, {k: U[k][:, t] for k in mal}, ep["need_cov"])
            for k in mal:
                rebound = (1 + Px["mal_resurgence"]) ** dur[t] if k != "mal_cm" else 1.0
                mal[k][:, t] = m[k] * LAG[k][dur[t]] * mal_f[t] * rebound
        d.update(mal)
        inf["hiv_pmtct"] = U["hiv_pmtct"] * Px["pmtct_vt_reduction"][:, None]
        inf["hiv_prev"] = U["hiv_prev"].copy()
        # new adult HIV infections (from people off ART, and lost prevention) die on the untreated survival curve,
        # scaled by the chance of dying of HIV with / without treatment at that year's ART coverage. Deaths up to 2030
        # go to the line that caused the infection; 2031-2035 deaths are set in motion. (Infant infections from PMTCT
        # are already counted under PMTCT.)
        H = N_YEARS + POST_YEARS
        ok_art = not (np.isnan(art_need) or np.isnan(art_cov0) or art_need <= 0)
        off_all = np.hstack([U["hiv_art"], off_post])                     # people off ART, 2026-2035
        cov_all = np.clip(art_cov0 - off_all / art_need, 0, 1) if ok_art else np.zeros((nx, H))
        risk = (cov_all * Px["hiv_inf_death_treated"][:, None]
                + (1 - cov_all) * Px["hiv_inf_death_untreated"][:, None])
        timing = hiv_death_timing(Px["hiv_survival_median"], H)

        def infection_deaths(new_inf):                                    # n x H infections -> n x H deaths
            """Deaths from new HIV infections: each year's infections (draws x years) spread over the following years by
            the Weibull survival curve (hiv_death_timing) and scaled by each year's death risk at that year's ART
            coverage. Returns draws x years of deaths."""
            out = np.zeros((nx, H))
            for s_ in range(H):
                for t in range(s_, H):
                    out[:, t] += new_inf[:, s_] * timing[:, t - s_] * risk[:, t]
            return out

        da = infection_deaths(np.hstack([inf["hiv_art"], post_i]))
        dp = infection_deaths(np.hstack([inf["hiv_prev"], np.zeros((nx, POST_YEARS))]))
        d["hiv_art"] = d["hiv_art"] + da[:, :N_YEARS]
        d["hiv_prev"] = d["hiv_prev"] + dp[:, :N_YEARS]
        after["hiv_infections"] = da[:, N_YEARS:].sum(axis=1) + dp[:, N_YEARS:].sum(axis=1)
        return d, inf, after

    deaths, infections, after_parts = lives(P, units)
    deathsc, infectionsc, afterc_parts = lives(Pc, unitsc)
    # L-33: deaths in 2031-2035 depend mostly on the assumed return-to-care rate after 2030. Central run with
    # art_reengage at its low and high values (everything else central): more re-engagement, fewer deaths.
    reengage_after = []
    for v in (float(ptab.loc["art_reengage", "high"]), float(ptab.loc["art_reengage", "low"])):
        Pv = {k: (np.full_like(x, v) if k == "art_reengage" else x) for k, x in Pc.items()}
        reengage_after.append(float(sum(np.ravel(a)[0] for a in lives(Pv, unitsc)[2].values())))
    after = sum(after_parts.values())
    afterc = {k: float(np.ravel(v)[0]) for k, v in afterc_parts.items()}
    deathsc = {l: v for l, v in deathsc.items() if l in pudc or l.startswith("mal_")}

    # ---- assemble (money and people are averages over the 5 years: equal to the yearly values for a sudden cut) ----
    def q(a, p):
        """The p-th percentile of the draws (or the single value when there is one draw)."""
        return float(np.percentile(a, p)) if np.size(a) > 1 else float(np.asarray(a).ravel()[0])

    def mean_c(seq, l):
        """The central run's value of line l, averaged over the 5 years (US$ or people)."""
        return float(np.mean([np.asarray(x[l]).ravel()[0] for x in seq]))

    recs = []
    for l in ALL_DIRECT:
        need, cov = ep["need_cov"].get(l, (np.nan, np.nan))
        d5 = deaths[l].sum(axis=1)
        d1 = deaths[l][:, 0]
        inf5 = infections[l].sum(axis=1) if l in infections else np.zeros(n)
        cov_used = cov
        if l == "mal_itn" and np.isnan(cov):
            cov_used = Pc["mal_itn_default_use"][0]
        if l == "mal_cm" and np.isnan(cov):
            cov_used = Pc["mal_cm_default_cov"][0]
        donor_units = float(np.asarray(effc_base[l]).ravel()[0]) / float(ucc[l][0])
        u_mean, uc_mean = units[l].mean(axis=1), float(unitsc[l].mean())
        recs.append({
            "bucket": LINE_BUCKET[l], "line": l, "label": LINE_LABELS[l],
            "base_usd": float(np.asarray(effc_base[l]).ravel()[0]),
            "gross_loss_usd": mean_c(effc_t, l), "replaced_usd": mean_c(repc_t, l), "net_loss_usd": mean_c(netc_t, l),
            "unit_cost": float(ucc[l][0]), "unit_label": UNIT_LABELS[l],
            "need": need, "cov0": cov_used, "cov_source": ep["cov_source"].get(l, ""),
            "donor_share_of_coverage": donor_units / (cov_used * need) if (need and cov_used and not np.isnan(need)) else np.nan,
            "units_lost": uc_mean, "units_lost_lo": q(u_mean, 2.5), "units_lost_hi": q(u_mean, 97.5),
            # people affected over 2026-2030 = the yearly values added up (follows the funding path), and the peak
            # year (for ART, mostly the same people stay off treatment, so the peak is the number of people)
            "units_lost_5y": float(unitsc[l].sum()), "units_lost_peak": float(unitsc[l].max()),
            "cov_drop_pp": uc_mean / need * 100 if (need and not np.isnan(need)) else np.nan,
            "capped": capped.get(l, False),
            "donor_exceeds_cost": excess.get(l, False),
            "donor_share_ext": donor_share.get(l, np.nan),       # external share of spending on the disease (cap, IMP-04)
            "donor_funded_units": funded.get(l, np.nan),        # people donor money pays for now (central)
            "deaths_y1": float(deathsc[l][0, 0]) if l in deathsc else 0.0,
            "deaths_y1_lo": q(d1, 2.5), "deaths_y1_hi": q(d1, 97.5),
            "deaths_5y": float(deathsc[l].sum()) if l in deathsc else 0.0,
            "deaths_5y_lo": q(d5, 2.5), "deaths_5y_hi": q(d5, 97.5),
            # central run, like deaths; the range is the 2.5th-97.5th percentile of the draws
            "infections_5y": float(np.asarray(infectionsc[l]).sum()) if l in infectionsc else 0.0,
            "infections_5y_lo": q(inf5, 2.5), "infections_5y_hi": q(inf5, 97.5),
        })
    # linked money lines (HIV testing and care): their full money, no units of their own; kappa of their lost money is
    # already inside the target line's people losing the service and deaths
    for l, tgt in LINKED.items():
        full = lambda e, ns: float(np.asarray(e[l]).ravel()[0]) + float(np.asarray(ns.get(l, 0.0)).ravel()[0])  # noqa: E731
        g_full = float(np.mean([full(effc_t[t], nsc_t_all[t]) for t in years]))
        r_full = float(np.mean([full(repc_t[t], repnc_t[t]) for t in years]))
        recs.append({"bucket": LINE_BUCKET[tgt], "line": l, "label": LINE_LABELS[l], "linked_to": tgt,
                     "base_usd": full(effc_base, nsc_base), "gross_loss_usd": g_full, "replaced_usd": r_full,
                     "net_loss_usd": g_full - r_full, "unit_cost": np.nan, "unit_label": "", "need": np.nan,
                     "cov0": np.nan, "cov_source": "", "donor_share_of_coverage": np.nan, "units_lost": np.nan,
                     "units_lost_lo": np.nan, "units_lost_hi": np.nan, "units_lost_5y": np.nan,
                     "units_lost_peak": np.nan, "cov_drop_pp": np.nan, "capped": False,
                     "donor_exceeds_cost": False, "donor_share_ext": np.nan, "donor_funded_units": np.nan, "deaths_y1": 0.0, "deaths_y1_lo": 0.0, "deaths_y1_hi": 0.0,
                     "deaths_5y": 0.0, "deaths_5y_lo": 0.0, "deaths_5y_hi": 0.0, "infections_5y": 0.0,
                     "infections_5y_lo": 0.0, "infections_5y_hi": 0.0})
    tab = pd.DataFrame(recs)

    # bucket summary incl. money that has no modelled outcome (OVC, systems share)
    bsum = []
    for b in BUCKETS:
        lb = [l for l in DIRECT[b]]
        d5 = sum(deaths[l].sum(axis=1) for l in lb)
        d1 = sum(deaths[l][:, 0] for l in lb)
        inf5 = sum(infections[l].sum(axis=1) for l in lb if l in infections) if b == "HIV" else np.zeros(n)
        bl = [l for l in base.index if FULL_LINE_BUCKET.get(l) == b]
        b_base = float(base.reindex(bl).sum()) if bl else 0.0
        b_gross = float(gross.reindex(bl).sum()) if bl else 0.0           # average yearly loss
        b_rep = float(np.mean([sum(np.asarray(repc_t[t][l]).ravel()[0] for l in lb + LINKED_IN[b])
                               + sum(float(np.asarray(repnc_t[t].get(k, 0.0)).ravel()[0]) for k in [b] + LINKED_IN[b])
                               for t in years]))
        b_net = b_gross - b_rep
        b_gain = float(gains.reindex(bl).sum()) if bl else 0.0
        dc5 = float(sum(deathsc[l].sum() for l in lb if l in deathsc))
        bsum.append({"bucket": b, "base_usd": b_base, "gross_loss_usd": b_gross, "replaced_usd": b_rep, "gains_usd": b_gain,
                     "net_loss_usd": b_net, "deaths_y1": float(sum(deathsc[l][0, 0] for l in lb if l in deathsc)),
                     "deaths_5y": dc5, "deaths_5y_lo": q(d5, 2.5), "deaths_5y_hi": q(d5, 97.5),
                     "deaths_y1_lo": q(d1, 2.5), "deaths_y1_hi": q(d1, 97.5),
                     "infections_5y": float(sum(np.asarray(infectionsc[l]).sum() for l in lb if l in infectionsc))
                     if b == "HIV" else 0.0,
                     "infections_5y_lo": q(inf5, 2.5), "infections_5y_hi": q(inf5, 97.5),
                     "deaths_per_musd": dc5 / 5 / (b_net / 1e6) if b_net > 1e4 else np.nan})
    bsum = pd.DataFrame(bsum)

    path = pd.DataFrame({b: sum(deathsc[l][0] for l in DIRECT[b] if l in deathsc) for b in BUCKETS},
                        index=pd.Index(range(1, N_YEARS + 1), name="year_after_cut"))
    all_d = sum(deaths[l] for l in ALL_DIRECT)
    tot5 = all_d.sum(axis=1)
    path_band = pd.DataFrame({"lo": np.percentile(np.cumsum(all_d, axis=1), 2.5, axis=0),
                              "hi": np.percentile(np.cumsum(all_d, axis=1), 97.5, axis=0)}, index=path.index)
    d5c = float(sum(deathsc[l].sum() for l in deathsc))
    committed = tot5 + after                           # deaths set in motion by the 2026-2030 losses
    us_path = scenario.us_direct_path_by_country.get(iso3)
    year_tab = pd.DataFrame({"year": [2026 + t for t in years], "cut_share": cut_path,
                             "us_bilateral_cut": (np.asarray(us_path, dtype=float) * cut_path * scenario.scale
                                                  if us_path is not None else np.full(N_YEARS, np.nan)),
                             "aid_lost_usd": G_t,
                             "response_usd": R_t, "gov_add_usd": gov_add, "replaced_usd": budget_t,
                             "gap_usd": G_t - budget_t,
                             "deaths": [float(sum(deathsc[l][0, t] for l in deathsc)) for t in years]})

    out = {"iso3": iso3, "cells": cells, "lines": tab, "buckets": bsum, "path": path, "path_band": path_band,
           "years": year_tab,
           "fiscal": {**fs, "gross_loss": G, "replacement": float(R_t.mean()), "replacement_wanted": want},
           "flags": ep["flags"], "deaths_per_dollar": dpd,
           "committed": {"deaths": d5c + sum(afterc.values()), "deaths_lo": q(committed, 2.5),
                         "deaths_hi": q(committed, 97.5), "after_2030": sum(afterc.values()),
                         "after_2030_lo": q(after, 2.5), "after_2030_hi": q(after, 97.5),
                         "after_parts": afterc,
                         # (at art_reengage high, at art_reengage low): the range across the return-to-care assumption
                         "after_2030_reengage": tuple(reengage_after),
                         "reengage_values": (float(ptab.loc["art_reengage", "low"]),
                                             float(ptab.loc["art_reengage", "high"]))},
           "totals": {"base": float(base.sum()), "gross": float(G_t.mean()), "replaced": float(budget_t.mean()),
                      "net": float((G_t - budget_t).mean()), "gross_full": G,
                      "gains": float(gains.sum()) if len(cells) else 0.0,
                      "deaths_5y": d5c, "deaths_5y_lo": q(tot5, 2.5), "deaths_5y_hi": q(tot5, 97.5),
                      "deaths_y1": float(sum(deathsc[l][0, 0] for l in deathsc))}}
    # per-draw totals (n,), so the All Countries range can be taken from the sum over countries (logic review IMP-10)
    out["draw_totals"] = {"deaths_5y": tot5, "after_2030": np.asarray(after, dtype=float) * np.ones(n)}
    if keep_draws:
        out["draws"] = {"deaths": deaths, "units": units}
    return out


# --------------------------------------------------------------------------- #
# Statistical cross-check (panel fixed-effects dose-response)
# --------------------------------------------------------------------------- #
STAT_SPECS = {   # bucket -> (regression key, regressor, need column, line whose per-unit deaths apply)
    "HIV": ("hiv_art", "x_hiv", "plhiv", "hiv_art", "sh_hiv_artc_zs"),
    "TB": ("tb_treatment", "x_tb", "all_forms_of_tb_incidence_estimated", "tb_ds", "sh_tbs_dtec_zs"),
    "Immunization": ("dtp3", "x_imm", "births", "imm", "sh_imm_idpt"),
}


def statistical_crosscheck(res: dict, inputs: dict, ptab: pd.DataFrame) -> pd.DataFrame:
    """Validation page, 'Poisson regression' method: the coverage drop implied by the panel regressions (coverage on
    log(1 + aid per person in need)) for the run's net aid loss, turned into deaths with the model's own deaths per
    person. res: a run_country result. Returns one row per disease (HIV, TB, immunization): coverage drop (percentage
    points) and deaths over 5 years with a 95% range."""
    ci = inputs["ci"]
    row = ci.loc[res["iso3"]]
    Pc = draw_params(ptab, 0)
    ep = epi(row, Pc)
    pud = per_unit_deaths(row, Pc, ep["art_cov"])
    out = []
    for b, (rk, xk, needk, line, covk) in STAT_SPECS.items():
        r = inputs["reg"][rk]
        beta, se = r["coef"][xk], r["se"][xk]
        bb = res["buckets"].set_index("bucket").loc[b]
        need = _v(row, needk)
        cov0 = _v(row, covk)
        if np.isnan(need) or need <= 0 or bb["base_usd"] <= 0:
            continue
        x0 = np.log1p(bb["base_usd"] / need)
        x1 = np.log1p(max(bb["base_usd"] - bb["net_loss_usd"], 0) / need)
        rec = {"bucket": b, "beta": beta, "se": se, "n_obs": r["n_obs"], "n_countries": r["n_countries"]}
        for tag, bt in (("", beta), ("_lo", beta - 1.96 * se), ("_hi", beta + 1.96 * se)):
            dpp = bt * (x1 - x0)                                    # percentage points (negative = drop)
            units = -dpp / 100 * need
            if not np.isnan(cov0):
                units = min(units, cov0 / 100 * need)
            rec[f"cov_drop_pp{tag}"] = -dpp
            rec[f"deaths_5y{tag}"] = units * float(pud[line].sum())
        mech = res["lines"].set_index("line").loc[line]
        rec["line"] = line
        rec["mech_cov_drop_pp"] = mech["cov_drop_pp"]
        rec["mech_deaths_5y"] = mech["deaths_5y"]
        out.append(rec)
    return pd.DataFrame(out)


# --------------------------------------------------------------------------- #
# Batch helpers
# --------------------------------------------------------------------------- #
def dose_response(iso3, bucket, fiscal, inputs, ptab, grid=None, n_draws=120, mortality_trend=True):
    """The 'Extra deaths as more aid is cut' chart: run the model for one disease cut by 0%, 10%, ... 100% (all donors).
    Returns one row per cut: net aid lost (US$ a year), deaths over 5 years with range, and the main service's
    coverage drop (percentage points)."""
    grid = np.linspace(0, 1, 11) if grid is None else grid
    rows = []
    for g in grid:
        r = run_country(iso3, uniform_scenario(bucket, float(g)), fiscal, inputs, ptab, n_draws=n_draws,
                        mortality_trend=mortality_trend)
        bb = r["buckets"].set_index("bucket").loc[bucket]
        main_line = {"HIV": "hiv_art", "TB": "tb_ds", "Malaria": "mal_itn", "Immunization": "imm"}[bucket]
        ln = r["lines"].set_index("line").loc[main_line]
        rows.append({"cut": g, "net_loss_usd": bb["net_loss_usd"], "deaths_5y": bb["deaths_5y"],
                     "lo": bb["deaths_5y_lo"], "hi": bb["deaths_5y_hi"], "cov_drop_pp": ln["cov_drop_pp"],
                     "cov0": ln["cov0"]})
    return pd.DataFrame(rows)


PEPFAR_ON_ART = 20.6e6           # people on ART that PEPFAR reports supporting (Validation comparison)


def donor_funded_on_art(inputs, ptab) -> pd.DataFrame:
    """People on ART that donor treatment money pays for now, per country (central): min(people on ART outside PMTCT,
    ART money / cost per patient-year).
    Feeds: the Validation page comparison with PEPFAR."""
    rows = []
    for c in [c for c in inputs["ci"].index if c in set(inputs["lines"].iso3)]:
        L = run_country(c, Scenario(), Fiscal(), inputs, ptab, n_draws=0)["lines"].set_index("line")
        rows.append({"iso3": c, "donor_funded_on_art": float(L.loc["hiv_art", "donor_funded_units"])})
    return pd.DataFrame(rows)


def donor_cost_excess(inputs, ptab) -> pd.DataFrame:
    """Country-lines where baseline donor aid / cost per person exceeds the donor-funded pool (people covered x the
    external share of spending on the disease; IMP-04): the excess pays for things other than the service, and units
    lost are scaled proportionally there.
    Feeds: the Validation page count of lines where donor money exceeds the service cost."""
    rows = []
    for c in [c for c in inputs["ci"].index if c in set(inputs["lines"].iso3)]:
        L = run_country(c, Scenario(), Fiscal(), inputs, ptab, n_draws=0)["lines"]
        for r in L[L["donor_exceeds_cost"]].itertuples():
            rows.append({"iso3": c, "line": r.line, "aid_usd": r.base_usd, "unit_cost": r.unit_cost,
                         "units_aid_buys": r.base_usd / r.unit_cost, "people_covered": r.cov0 * r.need,
                         "donor_share_ext": r.donor_share_ext, "donor_funded_pool": r.cov0 * r.need * r.donor_share_ext})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Government health budget: today's share, room to the Abuja target, history, break-even
# --------------------------------------------------------------------------- #
ABUJA_CEILING = 15.0             # % of government spending on health (Abuja Declaration target)
HEALTH_SHARE_FILE = HERE / "ext_data" / "wdi" / "sh_xpd_ghed_ge_zs.csv"


def _share_history() -> pd.DataFrame:
    """World Bank WDI SH.XPD.GHED.GE.ZS (health's share of government spending, %), every country-year, read once and
    cached. Feeds health_share and the 'fastest historical rise' benchmark."""
    if not hasattr(_share_history, "cache"):
        d = pd.read_csv(HEALTH_SHARE_FILE)
        d.columns = ["iso3", "year", "share"]
        d["iso3"] = d["iso3"].str.upper()
        _share_history.cache = d.dropna()
    return _share_history.cache


def _series(path: Path, value) -> pd.Series:
    """year -> value from one of the per-country files (empty when the file is missing).
    Feeds: health_share's estimated fallback."""
    if not path.exists():
        return pd.Series(dtype=float)
    d = pd.read_csv(path)
    return pd.Series(value(d).to_numpy(dtype=float), index=d["year"].to_numpy()).dropna()


def health_share(iso3: str) -> dict:
    """Health's share of government spending (%), one definition for the whole dashboard (audit I-14):
      1. World Bank WDI SH.XPD.GHED.GE.ZS (WHO Global Health Expenditure Database), latest available year;
      2. if missing: IHME government health spending / IMF WEO general-government expenditure, same year (estimated);
      3. otherwise NaN ('n/a').
    Returns share_pct, year, estimated (bool) and source.
    Feeds: the Health Share pill, the path panel caption, the room to 15%, and the points-to-dollars conversion."""
    cache = health_share.__dict__.setdefault("cache", {})
    if iso3 in cache:
        return cache[iso3]
    h = _share_history()
    h = h[h.iso3 == iso3].sort_values("year")
    if len(h):
        out = {"share_pct": float(h["share"].iloc[-1]), "year": int(h["year"].iloc[-1]), "estimated": False,
               "source": "World Bank WDI SH.XPD.GHED.GE.ZS (WHO GHED)"}
    else:
        # observed years only: IHME rows not flagged as projected, IMF years not flagged as estimates
        ghes = _series(HERE / "spending_data" / f"{iso3}.csv",
                       lambda d: (d["ghes_total_mean"] * 1e3).where(d.get("projected", 0) == 0))
        gov = _series(HERE / "macro_data" / f"{iso3}.csv",
                      lambda d: (d["gov_expenditure_pct_gdp"] / 100 * d["gdp_usd_bn_2023"] * 1e9)
                      .where(~d.get("gdp_is_estimate", pd.Series(False, index=d.index)).astype(bool)))
        both = sorted(set(ghes.index) & set(gov[gov > 0].index))
        if both:
            y = both[-1]
            out = {"share_pct": float(ghes[y] / gov[y] * 100), "year": int(y), "estimated": True,
                   "source": "IHME government health spending / IMF WEO general-government expenditure"}
        else:
            out = {"share_pct": np.nan, "year": None, "estimated": False, "source": None}
    cache[iso3] = out
    return out


def health_budget(iso3: str, inputs: dict) -> dict:
    """Health's share of government spending today (health_share: World Bank, else IHME / IMF), total government
    spending implied by it (government health spending 2023 / share, US$), the room to the Abuja 15% ceiling, and the
    fastest sustained rise in the country's history (90th percentile of its yearly changes in the World Bank share,
    percentage points). Every 'points of the budget' to dollars conversion uses gov_spend_usd from here.
    Feeds: the Gradual Budget Increase sliders, break-even and the path panel."""
    row = inputs["ci"].loc[iso3] if iso3 in inputs["ci"].index else pd.Series(dtype=float)
    ghes = _v(row, "ghes_2023")
    hs = health_share(iso3)
    share = hs["share_pct"]
    gov = ghes / (share / 100) if share == share and share > 0 and not np.isnan(ghes) else np.nan
    h = _share_history()
    h = h[(h.iso3 == iso3) & h.year.between(2000, 2023)].sort_values("year")
    ch = h["share"].diff()[h["year"].diff() == 1].dropna()
    p90 = float(ch.quantile(0.9)) if len(ch) >= 5 else np.nan
    room = max(ABUJA_CEILING - share, 0.0) if not np.isnan(share) else np.nan
    return {"share_pct": share, "share_year": hs["year"], "share_estimated": hs["estimated"],
            "gov_spend_usd": gov, "ceiling_pct": ABUJA_CEILING, "room_pct": room,
            "p90_rise_pp": p90, "ghes_usd": ghes, "gov_source": hs["source"]}


def _money_by_year(iso3, scenario, fiscal, inputs, cut_path):
    """Aid lost and the existing government response in each year 2026-2030 (US$), without running the full model.
    Feeds: break_even_share."""
    ci, lines = inputs["ci"], inputs["lines"]
    row = ci.loc[iso3] if iso3 in ci.index else pd.Series(dtype=float)
    cells = lines[lines.iso3 == iso3].copy()
    path = np.clip(_path(cut_path, 1.0), 0, 1)
    if len(cells):
        cut_m = scenario.cuts_by_year(cells, iso3, inputs["trend_map"]) * path[None, :]
        usd = cells["usd"].to_numpy()
        G_t = np.array([float(np.clip(pd.Series(usd * cut_m[:, t], index=cells.index).groupby(cells["line"]).sum(),
                                      0, None).sum()) for t in range(N_YEARS)])
    else:
        G_t = np.zeros(N_YEARS)
    fs = fiscal_space(row, fiscal.effort)
    R_t = []
    for g in G_t:
        want = {"none": 0.0, "gradual": 0.0, "custom": fiscal.theta * g, "max": g}[fiscal.mode]
        R_t.append(max(min(want, fs["capacity"]) if (fiscal.cap_to_space or fiscal.mode == "max") else want, 0.0))
    return G_t, np.array(R_t)


def gov_add_from_points(points, gov_spend_usd: float) -> np.ndarray:
    """Extra government health money (US$) from extra percentage points of the government budget, year by year.
    Feeds: Gradual Budget Increase money (US$ a year)."""
    return np.clip(_path(points, 0.0), 0, None) / 100 * (gov_spend_usd if gov_spend_usd == gov_spend_usd else 0.0)


def break_even_share(iso3, scenario, fiscal, inputs, cut_path=None, tol: float = 1e-4):
    """Smallest constant yearly increase s in health's share of government spending (percentage points per year,
    cumulative: s in 2026, 2s in 2027, ...) that keeps the net gap <= 0 in every year of the cut path, on top of the
    government response in `fiscal`; capped so the share never passes the Abuja 15% target. Found by bisection.
    Returns 0.0 if there is no gap, None if it can't be reached by 15% (or the budget data are missing).
    Feeds: the break-even line in the funding-path panel."""
    hb = health_budget(iso3, inputs)
    G_t, R_t = _money_by_year(iso3, scenario, fiscal, inputs, cut_path)
    gap = G_t - R_t
    if (gap <= 1e-6).all():
        return 0.0
    if np.isnan(hb["gov_spend_usd"]) or np.isnan(hb["room_pct"]) or hb["room_pct"] <= 0:
        return None
    steps = np.arange(1, N_YEARS + 1)

    def keeps_up(s):
        """True if raising health's budget share by s points a year (cumulative) gives at least the aid gap in every
        year."""
        return bool((gov_add_from_points(s * steps, hb["gov_spend_usd"]) >= gap - 1e-6).all())

    hi = hb["room_pct"] / N_YEARS                    # fastest steady rise that still ends at or below 15%
    if not keeps_up(hi):
        return None
    lo = 0.0
    while hi - lo > tol:
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if keeps_up(mid) else (mid, hi)
    return hi


def run_all(scenario, fiscal, inputs, ptab, n_draws=80, countries=None, mortality_trend=True):
    """Run the model for every dashboard country (or `countries`) and return one row per country: aid (US$ a year),
    deaths 2026-2030 with range, deaths 2031-2035, deaths and net loss by disease, new HIV infections, fiscal
    capacity. Feeds the All Countries page and the precomputed model_data/all_countries_<preset>.csv files."""
    countries = countries or [c for c in inputs["ci"].index if c in set(inputs["lines"].iso3)]
    if scenario.mou_only:                              # America First MOUs: only countries with an MOU schedule
        countries = [c for c in countries if c in scenario.us_direct_path_by_country]
    recs = []
    d5_tot, after_tot = 0.0, 0.0
    for c in countries:
        r = run_country(c, scenario, fiscal, inputs, ptab, n_draws=n_draws, mortality_trend=mortality_trend)
        d5_tot = d5_tot + r["draw_totals"]["deaths_5y"]
        after_tot = after_tot + r["draw_totals"]["after_2030"]
        row = inputs["ci"].loc[c]
        t = r["totals"]
        rec = {"iso3": c, "pop": _v(row, "sp_pop_totl"), "base_usd": t["base"], "gross_loss_usd": t["gross"],
               "replaced_usd": t["replaced"], "net_loss_usd": t["net"], "deaths_y1": t["deaths_y1"],
               "deaths_5y": t["deaths_5y"], "deaths_5y_lo": t["deaths_5y_lo"], "deaths_5y_hi": t["deaths_5y_hi"],
               "loss_pct_ghes": t["gross"] / r["fiscal"]["ghes"] if r["fiscal"]["ghes"] else np.nan,
               "capacity_usd": r["fiscal"]["capacity"], "deaths_after_2030": r["committed"]["after_2030"],
               "deaths_after_2030_lo": r["committed"]["after_2030_lo"],
               "deaths_after_2030_hi": r["committed"]["after_2030_hi"],
               "deaths_after_2030_reengage_min": r["committed"]["after_2030_reengage"][0],
               "deaths_after_2030_reengage_max": r["committed"]["after_2030_reengage"][1]}
        for _, bb in r["buckets"].iterrows():
            rec[f"deaths_5y_{bb['bucket']}"] = bb["deaths_5y"]
            rec[f"net_loss_{bb['bucket']}"] = bb["net_loss_usd"]
        rec["hiv_infections_5y"] = float(r["buckets"].set_index("bucket").loc["HIV", "infections_5y"])
        recs.append(rec)
    out = pd.DataFrame(recs)
    # draw-by-draw totals over all countries: the All Countries range is their 2.5th-97.5th percentile (IMP-10)
    # stored as tuples: pandas compares attrs when it combines frames, and arrays or frames can't be compared that way
    ones = np.ones(max(n_draws, 1))
    out.attrs["draw_totals"] = {"deaths_5y": tuple(float(x) for x in np.ravel(d5_tot) * ones),
                                "deaths_after_2030": tuple(float(x) for x in np.ravel(after_tot) * ones)}
    return out


def total_range(results: pd.DataFrame, col: str = "deaths_5y") -> tuple:
    """(2.5th, 97.5th) percentile over the draws of the total of `col` over all countries in `results` (a run_all table
    or a precomputed file loaded with scenarios.load_precomputed). The draws are the same in every country, so the
    total of each draw is a draw of the total. Countries with no aid loss add 0 in every draw, so a table filtered to
    countries with a loss has the same range. Returns (nan, nan) when the draw totals are not available.
    Feeds: the range of every All Countries total and of the Validation comparison rows."""
    d = results.attrs.get("draw_totals")
    if d is None or col not in d or len(d[col]) < 2:
        return np.nan, np.nan
    v = np.asarray(d[col], dtype=float)
    return float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))


# --------------------------------------------------------------------------- #
# Alternative estimates of the same cut (Validation & Benchmarks page)
# --------------------------------------------------------------------------- #
# Our own Poisson fixed-effects regressions (prepare_model.py, Cavalcanti et al. 2025 appendix 4.1 method):
# bucket -> (regression key, baseline-deaths column, aid-before column or None, denominator column)
POISSON_SPECS = {
    "TB": ("poisson_tb", "tb_deaths_total", None, "sp_pop_totl"),
    "Malaria": ("poisson_malaria", "malaria_deaths", None, "sp_pop_totl"),
    "Immunization": ("poisson_u5", "sh_dth_mort", "dah_nch_base", "births"),
}


def poisson_projection(res: dict, inputs: dict) -> pd.DataFrame:
    """deaths_after = deaths_now x exp(beta x (x_after - x_before)), x = log(1 + aid per person), using the net cut
    (after government backfill). Extra deaths over 5 years = 5 x the yearly change; range from beta +/- 1.96 SE.
    TB and malaria use the bucket's own aid; under-5 deaths use all vaccine + child health aid per birth, cut by the
    net immunization loss. Malaria is estimated on child deaths and applied proportionally to all-age deaths.
    Feeds: the Validation page 'Poisson regression' estimates."""
    row = inputs["ci"].loc[res["iso3"]]
    B = res["buckets"].set_index("bucket")
    out = []
    for b, (key, death_col, before_col, denom_col) in POISSON_SPECS.items():
        r = inputs["reg"].get(key)
        deaths, denom = _v(row, death_col), _v(row, denom_col)
        if r is None or np.isnan(deaths) or np.isnan(denom) or denom <= 0:
            continue
        before = _v(row, before_col) if before_col else B.loc[b, "base_usd"]
        if np.isnan(before):
            continue
        after = max(before - B.loc[b, "net_loss_usd"], 0.0)
        dx = np.log1p(after / denom) - np.log1p(before / denom)
        beta, se = r["coef"][r["x"][0]], r["se"][r["x"][0]]
        est = {tag: 5 * deaths * (np.exp(bt * dx) - 1) for tag, bt in (("", beta), ("_a", beta - 1.96 * se), ("_b", beta + 1.96 * se))}
        out.append({"bucket": b, "deaths_5y": est[""], "deaths_5y_lo": min(est["_a"], est["_b"]),
                    "deaths_5y_hi": max(est["_a"], est["_b"]), "beta": beta, "se": se, "baseline_deaths": deaths,
                    "aid_pc_before": before / denom, "aid_pc_after": after / denom})
    return pd.DataFrame(out)


# Cavalcanti et al. 2025 (Lancet), appendix Web Table 19: rate ratios for USAID health funding per capita vs ~$0
LANCET_FUNDING = np.array([0.71, 1.37, 5.76])
LANCET_RR = {"HIV": np.array([0.83, 0.81, 0.50]), "Malaria": np.array([0.94, 0.78, 0.58]),
             "Maternal": np.array([0.91, 0.83, 0.67])}
LANCET_BASELINE = {"HIV": "hiv_deaths_est", "Malaria": "malaria_deaths", "Maternal": "sh_mmr_dths"}


def lancet_log_rr(bucket: str, funding_pc: float) -> float:
    """Log rate ratio at a given US health aid per capita: interpolated in log funding between the published points,
    linear in funding from 0 up to the first point, and held flat above the last one.
    Feeds: lancet_projection."""
    lr = np.log(LANCET_RR[bucket])
    if funding_pc <= 0:
        return 0.0
    if funding_pc < LANCET_FUNDING[0]:
        return float(lr[0] * funding_pc / LANCET_FUNDING[0])
    return float(np.interp(np.log(funding_pc), np.log(LANCET_FUNDING), lr))


def lancet_projection(res: dict, inputs: dict) -> pd.DataFrame:
    """Apply the published rate ratios to the country's US-source health aid per capita before and after the cut.
    The US cut is the share of US money lost in the modelled cells, net of government backfill in proportion.
    Feeds: the Validation page 'Lancet rate ratios' estimates."""
    row = inputs["ci"].loc[res["iso3"]]
    pop, us_base = _v(row, "sp_pop_totl"), _v(row, "us_health_aid_base")
    cells, T = res["cells"], res["totals"]
    us = cells[cells["src_grp"] == "United States"]
    us_cut = float(np.clip(us["loss"].sum() / us["usd"].sum(), 0, 1)) if us["usd"].sum() > 0 else 0.0
    us_cut *= (T["net"] / T["gross"]) if T["gross"] > 0 else 0.0
    if np.isnan(pop) or pop <= 0 or np.isnan(us_base):
        return pd.DataFrame()
    f0 = us_base / pop
    f1 = f0 * (1 - us_cut)
    out = []
    for b, col in LANCET_BASELINE.items():
        deaths = _v(row, col)
        if np.isnan(deaths):
            continue
        ratio = np.exp(lancet_log_rr(b, f1) - lancet_log_rr(b, f0))
        out.append({"bucket": b, "deaths_5y": 5 * deaths * (ratio - 1), "baseline_deaths": deaths,
                    "us_aid_pc_before": f0, "us_aid_pc_after": f1, "us_cut_share": us_cut})
    return pd.DataFrame(out)
