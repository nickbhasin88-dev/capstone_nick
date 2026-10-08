"""
Funding shock -> fiscal response -> coverage -> lives.

A country-level model for HIV, TB, malaria and immunization:

  1. MONEY     baseline aid (IHME DAH, avg 2021-23) by source x channel x service line; a donor scenario sets the
               fraction cut in every cell; unreported program areas are spread over the bucket's known mix and a
               share (kappa) of lost systems money (labs, HR, M&E) is assumed to translate into lost services.
  2. FISCAL    the government can backfill part of the loss; the replacement rate is a policy choice (default from
               the panel regression) capped by fiscal space = GHES x (best-year minus typical GHES growth) x debt-stress.
  3. COVERAGE  net money lost / unit cost = people who lose a service; divided by the population in need it gives
               the coverage drop (percentage points), never more than the people currently covered.
  4. LIVES     people losing a service x the mortality effect of that service, using country epidemiology:
               ART interruption hazards, WHO TB case-fatality ratios, Lives Saved Tool equations for malaria,
               Gavi/VIMC deaths averted per child immunised (scaled to under-5 mortality).

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
FULL_LINE_BUCKET = {**LINE_BUCKET, **{v: k for k, v in UNSPEC.items()}, **{v: k for k, v in HSS.items()}}
LINE_LABELS = {
    "hiv_art": "HIV treatment (ART, testing, care)", "hiv_pmtct": "Prevention of mother-to-child transmission",
    "hiv_prev": "HIV prevention (PrEP, VMMC, condoms, key populations)", "hiv_ovc": "Orphans & vulnerable children",
    "tb_ds": "TB case finding & treatment", "tb_dr": "Drug-resistant TB",
    "mal_itn": "Bednets & other vector control", "mal_irs": "Indoor residual spraying",
    "mal_cm": "Malaria testing & treatment", "imm": "Routine immunization (vaccines + delivery)",
}
UNIT_LABELS = {"hiv_art": "people on ART", "hiv_pmtct": "HIV+ pregnant women", "hiv_prev": "infections averted",
               "hiv_ovc": "children supported", "tb_ds": "TB patients treated", "tb_dr": "DR-TB patients treated",
               "mal_itn": "people sleeping under nets", "mal_irs": "people protected by spraying",
               "mal_cm": "malaria cases treated", "imm": "children immunized"}
UNIT_SINGULAR = {"hiv_art": "patient-year", "hiv_pmtct": "woman", "hiv_prev": "infection averted",
                 "hiv_ovc": "child-year", "tb_ds": "patient", "tb_dr": "patient", "mal_itn": "person-year",
                 "mal_irs": "person-year", "mal_cm": "case", "imm": "child"}
COVERAGE_LABELS = {"hiv_art": "ART coverage (% of PLHIV)", "hiv_pmtct": "PMTCT coverage",
                   "tb_ds": "TB treatment coverage", "tb_dr": "DR-TB treatment coverage (assumed 45%)",
                   "mal_itn": "Bednet use (vector-control coverage)", "mal_irs": "Vector-control coverage",
                   "mal_cm": "Malaria treatment coverage", "imm": "DTP3 coverage"}

SOURCE_GROUPS = ["United States", "United Kingdom", "Germany", "France", "Japan", "Canada", "Netherlands", "Nordics",
                 "Other DAC governments", "Gates Foundation", "Other private", "Development-bank lending",
                 "Non-DAC governments", "Other / unallocable"]
DIRECT_CHANNELS = {"Bilateral agency", "NGOs", "Gates direct", "Other"}
MULTI_CHANNELS = ["Global Fund", "Gavi", "WHO", "UNICEF", "UNFPA", "UNAIDS", "Unitaid", "Development banks",
                  "EU institutions", "CEPI"]

N_YEARS = 5
# how quickly the full annual effect appears after a sustained cut (year 1..5)
LAG = {
    "hiv_art": None,                                   # explicit hazard ramp below
    "hiv_pmtct": np.array([0.6, 1, 1, 1, 1]),
    "tb_ds": np.array([0.7, 1, 1, 1, 1]), "tb_dr": np.array([0.7, 1, 1, 1, 1]),
    "mal_itn": np.array([0.5, 1, 1, 1, 1]), "mal_irs": np.array([0.8, 1, 1, 1, 1]), "mal_cm": np.ones(5),
    "imm": np.array([0.4, 0.75, 0.95, 1, 1]),
}
ART_HAZARD = np.array([0.012, 0.028, 0.038, 0.045, 0.05])  # excess deaths per person-year off ART, by year since loss
ART_INFECT_LAG = np.array([0.5, 1, 1, 1, 1])
DR_TB_SHARE, DR_TB_COV = 0.04, 0.45
MAL_CM_MIN_INCIDENCE = 50       # malaria cases per 1,000 at risk needed to read fever treatment as case coverage
_EXCESS_LOGGED: set = set()     # (iso3, line) pairs already logged as "donor money exceeds the service cost"


# --------------------------------------------------------------------------- #
# Inputs
# --------------------------------------------------------------------------- #
def load_inputs(model_dir: Path = MODEL_DIR) -> dict:
    lines = pd.read_csv(model_dir / "dah_lines.csv")
    ci = pd.read_csv(model_dir / "country_inputs.csv").set_index("iso3")
    trend = pd.read_csv(model_dir / "ihme_trend.csv")
    reg = json.loads((model_dir / "regressions.json").read_text())
    # global mix of each bucket's known (direct) lines -> fallback for allocating unreported program areas
    gm = lines[lines.line.isin(ALL_DIRECT)].groupby(["bucket", "line"])["usd"].sum()
    gmix = {b: (gm[b] / gm[b].sum()).reindex(DIRECT[b]).fillna(0).to_dict() for b in BUCKETS}
    return {"lines": lines, "ci": ci, "trend": trend, "reg": reg, "global_mix": gmix,
            "trend_map": trend.set_index(["src_grp", "chan_grp", "bucket"])["ratio"].to_dict()}


def load_params(path: Path = PARAMS_FILE) -> pd.DataFrame:
    return pd.read_csv(path).set_index("param")


def draw_params(ptab: pd.DataFrame, n: int, seed: int = 7) -> dict:
    """n == 0 -> central values only (arrays of length 1)."""
    rng = np.random.default_rng(seed)
    out = {}
    for p, r in ptab.iterrows():
        c, lo, hi = float(r["central"]), float(r["low"]), float(r["high"])
        if n == 0 or hi <= lo:
            out[p] = np.array([c])
        else:
            lo, hi = min(lo, c), max(hi, c)
            out[p] = rng.triangular(lo, c, hi, size=n) if hi > lo else np.full(n, c)
    return out


def theta_historical(reg: dict) -> tuple:
    """Replacement rate implied by the fiscal regression: -(b_fall + b_fall_lag) with a 95% CI (independence approx)."""
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
    us_direct_by_country: dict = field(default_factory=dict)   # iso3 -> cut on US direct channels (MOU schedule)
    ihme_trend: bool = False
    bucket_only: str | None = None                      # restrict the shock to one bucket (dose-response curves)
    scale: float = 1.0                                  # multiplies every cut (the scenario's own path, 0 -> 1)

    def cuts(self, cells: pd.DataFrame, iso3: str, trend_map: dict) -> np.ndarray:
        out = np.zeros(len(cells))
        for i, (s, c, b) in enumerate(zip(cells["src_grp"], cells["chan_grp"], cells["bucket"])):
            if self.bucket_only and b != self.bucket_only:
                continue
            if self.ihme_trend:
                out[i] = 1.0 - trend_map.get((s, c, b), 1.0)
                continue
            direct = c in DIRECT_CHANNELS
            x = self.src_direct.get(s, 0.0) if direct else self.src_multi.get(s, 0.0)
            if direct and s == "United States" and iso3 in self.us_direct_by_country:
                x = self.us_direct_by_country[iso3]
            x = self.pair.get((s, c), x)
            y = self.chan.get(c, 0.0)
            out[i] = 1.0 - (1.0 - x) * (1.0 - y)
        return np.clip(out, -1.0, 1.0) * self.scale


def uniform_scenario(bucket: str, cut: float) -> Scenario:
    sc = Scenario(name=f"{bucket} -{cut:.0%}", bucket_only=bucket)
    sc.src_direct = {s: cut for s in SOURCE_GROUPS}
    sc.src_multi = {s: cut for s in SOURCE_GROUPS}
    return sc


@dataclass
class Fiscal:
    mode: str = "none"            # none | historical | custom | max | gradual (money comes via gov_add_usd)
    theta: float = 0.0            # replacement share for "custom"
    cap_to_space: bool = True
    allocation: str = "pro_rata"  # pro_rata | lives_first
    effort: str = "p75"           # p75 (strong year) | p90 (best years): sets the fiscal-space ceiling


# --------------------------------------------------------------------------- #
# Country helpers
# --------------------------------------------------------------------------- #
def _v(row, k, default=np.nan):
    x = row.get(k, default)
    return default if x is None or (isinstance(x, float) and np.isnan(x)) else float(x)


def fiscal_space(row: pd.Series, effort: str = "p75") -> dict:
    """Backfill capacity per year = GHES x (strong-year growth - typical growth) x debt-stress factor.
    effort 'p75' = a strong year (75th percentile of real GHES growth, 2001-23); 'p90' = the best years (90th)."""
    ghes = _v(row, "ghes_2023")
    med, p90 = _v(row, "ghes_growth_median", 0.0), _v(row, "ghes_growth_p90", 0.0)
    p75 = _v(row, "ghes_growth_p75", 0.0)
    top = p90 if effort == "p90" else p75
    surge = max(0.0, top - max(med, 0.0))
    intr = _v(row, "gc_xpn_intp_rv_zs")
    stress = 1.0 if np.isnan(intr) else float(np.clip(1 - (intr - 10) / 40, 0.25, 1.0))
    pop, gdp_pc = _v(row, "sp_pop_totl"), _v(row, "gdp_pc")
    rev_pct = _v(row, "gc_rev_xgrt_gd_zs")
    gdp = pop * gdp_pc if not (np.isnan(pop) or np.isnan(gdp_pc)) else np.nan
    return {"ghes": ghes, "ghes_growth_median": med, "ghes_growth_p90": p90, "ghes_growth_p75": p75,
            "ghes_growth_top": top, "effort": effort, "surge_rate": surge,
            "interest_pct_revenue": intr, "stress_factor": stress,
            "capacity": (ghes * surge * stress) if not np.isnan(ghes) else 0.0,
            "gdp": gdp, "revenue": gdp * rev_pct / 100 if not np.isnan(rev_pct) else np.nan, "revenue_pct_gdp": rev_pct,
            "debt_pct_gdp": _v(row, "gc_dod_totl_gd_zs"), "ghes_pct_gov_spend": _v(row, "sh_xpd_ghed_ge_zs"),
            "ghes_pct_gdp": _v(row, "ghes_pct_gdp_2023"), "ghes_pc": _v(row, "ghes_pc_2023")}


def epi(row: pd.Series, P: dict) -> dict:
    """Population in need and baseline coverage for each direct line."""
    pop = _v(row, "sp_pop_totl")
    inc_hiv = _v(row, "sh_hiv_incd_tl") / pop * 1000 if pop else np.nan
    itn = _v(row, "sh_mlr_nets_zs") / 100
    # "% of under-5 fevers given antimalarials" measures coverage of malaria cases only where most fevers are malaria;
    # where malaria is rare it is near zero for that reason, so the default coverage is used instead
    cm = _v(row, "sh_mlr_tret_zs") / 100
    mal_inc = _v(row, "sh_mlr_incd_p3")
    cm_low_malaria = not np.isnan(cm) and not (mal_inc >= MAL_CM_MIN_INCIDENCE)
    if cm_low_malaria:
        cm = np.nan
    art = _v(row, "sh_hiv_artc_zs") / 100
    pm = _v(row, "sh_hiv_pmtc_zs") / 100
    e = {
        "hiv_art": (_v(row, "plhiv"), art),
        "hiv_pmtct": (_v(row, "hiv_pos_pregnancies"), pm if not np.isnan(pm) else art),
        "tb_ds": (_v(row, "all_forms_of_tb_incidence_estimated"), _v(row, "sh_tbs_dtec_zs") / 100),
        "tb_dr": (_v(row, "all_forms_of_tb_incidence_estimated") * DR_TB_SHARE, DR_TB_COV),
        "mal_itn": (_v(row, "malaria_pop_at_risk"), itn),
        "mal_irs": (_v(row, "malaria_pop_at_risk"), itn),
        "mal_cm": (_v(row, "malaria_cases"), cm),
        "imm": (_v(row, "births"), _v(row, "sh_imm_idpt") / 100),
    }
    flags = []
    if np.isnan(itn):
        flags.append("bednet use not surveyed: default assumed")
    if cm_low_malaria:
        flags.append("malaria is rare here, so the fever-treatment survey does not measure malaria treatment: "
                     "default coverage assumed")
    elif np.isnan(cm):
        flags.append("malaria treatment coverage not surveyed: default assumed")
    return {"need_cov": e, "hiv_incidence_per_1000": inc_hiv, "flags": flags, "art_cov": art}


UC_REF_FILE = HERE / "unit_cost_reference.csv"


# US CPI-U annual averages (BLS series CUUR0000SA0), to bring study costs to 2023 US$ (2014 -> 2023 = 1.287, the
# factor already applied to the TB rows of unit_cost_reference.csv)
CPI_U = {2014: 236.736, 2018: 251.107, 2019: 255.657, 2020: 258.811, 2021: 270.970, 2022: 292.655, 2023: 304.702}
PRICE_YEAR = 2023


def inflate(value: float, cost_year: int) -> float:
    """A study cost in cost_year US$ -> 2023 US$ (US CPI-U)."""
    return value * CPI_U[PRICE_YEAR] / CPI_U[int(cost_year)]


def _uc_ref() -> dict:
    """Sourced unit-cost reference values (country ART studies, income-group TB costs), in 2023 US$: each value is
    inflated from its cost_year (ART site costs are 2018-2020 US$; TB rows are already 2023 US$)."""
    if not hasattr(_uc_ref, "cache"):
        r = pd.read_csv(UC_REF_FILE)
        _uc_ref.cache = {(k, key): inflate(float(v), y)
                         for k, key, v, y in zip(r["kind"], r["key"], r["value"], r["cost_year"])}
    return _uc_ref.cache


def income_group(row: pd.Series) -> str:
    g = row.get("income_group") if hasattr(row, "get") else None
    if isinstance(g, str) and g:
        return g
    gdp = _v(row, "gdp_pc", 2000.0)                    # fallback: rough GDP-per-capita thresholds
    return "low_income" if gdp < 1150 else "lower_middle_income" if gdp < 4500 else "upper_middle_income"


def unit_costs(row: pd.Series, P: dict) -> dict:
    """Donor cost per unit of service. Site/provider costs from studies are grossed up for above-service spending."""
    ref = _uc_ref()
    iso = row.name if isinstance(row.name, str) else ""
    markup = 1.0 / (1.0 - P["asd_share"])                # site cost -> full donor program cost
    g = _v(row, "gdp_pc", 1000.0)
    sc = (max(g, 200.0) / 1000.0) ** P["uc_scale_elast"]
    art_site = ref.get(("art_site_cost", iso))
    if art_site is None:
        art_site = ref[("art_site_default", "arv")] + ref[("art_site_default", "non_arv")] * sc
    ig = income_group(row)
    ig_key = ig if ig in ("low_income", "lower_middle_income", "upper_middle_income") else "upper_middle_income"
    tb_ds = ref[("tb_ds_cost", ig_key)]
    tb_dr = ref[("tb_dr_cost", ig_key)]
    inc = _v(row, "sh_hiv_incd_tl") / _v(row, "sp_pop_totl") * 1000
    inc = 0.3 if np.isnan(inc) else float(np.clip(inc, 0.05, 10))
    one = np.ones_like(P["uc_imm"])
    return {
        "hiv_art": art_site * P["uc_art_mult"] * markup,
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


FALLBACK_MORTALITY_TREND = -0.009    # %/yr decline in baseline mortality (Cavalcanti et al. 2025, Lancet, appendix 10.2)
TREND_COLUMNS = {"u5": "trend_u5mr", "malaria": "trend_malaria_deaths", "tb": "trend_tb_deaths"}


def mortality_trend_factors(row: pd.Series, kind: str, use: bool = True) -> np.ndarray:
    """(1 + annual trend)^(year - 1) for years 1..5: baseline deaths keep falling (or rising) as they did in 2010-2019.
    kind: 'u5' (under-5 mortality rate) or 'malaria' (child malaria deaths). Ones when switched off."""
    if not use:
        return np.ones(N_YEARS)
    t = _v(row, TREND_COLUMNS[kind])
    t = FALLBACK_MORTALITY_TREND if np.isnan(t) else t
    return (1.0 + t) ** np.arange(N_YEARS)


def _units_lost(net, base, unit_cost, covered):
    """Units of service lost (before continuity): donor-funded units x share of donor money lost."""
    net, base, unit_cost = np.asarray(net, dtype=float), np.asarray(base, dtype=float), np.asarray(unit_cost, dtype=float)
    plain = net / unit_cost
    if np.isnan(covered):
        return plain
    funded = np.minimum(covered, base / unit_cost)
    share = np.divide(net, base, out=np.zeros_like(net * base), where=np.abs(base) > 0)
    return np.where(base / unit_cost > covered, funded * share, plain)


def per_unit_levels(row: pd.Series, P: dict, art_cov: float, trend: bool = True) -> dict:
    """Deaths per unit of service lost once the full effect has built up, by CALENDAR year 1..5 (arrays n x 5),
    for the lines handled year by year (PMTCT, TB, vaccines). The ramp-up (LAG) is applied separately, by how long the
    cut has been in force. trend: vaccine deaths scale with the country's falling under-5 mortality."""
    n = len(P["uc_imm"])
    h = _v(row, "tb_hiv_share", 0.0)
    a = 0.0 if np.isnan(art_cov) else art_cov
    cfr_up = P["tb_cfr_untreated_pos"] * (1 - 0.3 * a)     # untreated HIV+ TB: lower when on ART (0.78 -> 0.49)
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


def per_unit_deaths(row: pd.Series, P: dict, art_cov: float, trend: bool = True) -> dict:
    """Deaths per unit of service lost, by year 1..5 of a cut in force since year 1 (arrays n x 5). Malaria is
    handled separately (LiST). = per_unit_levels x LAG, plus the ART hazard ramp."""
    lv = per_unit_levels(row, P, art_cov, trend)
    out = {l: v * (LAG[l] if LAG.get(l) is not None else 1.0) for l, v in lv.items()}
    out["hiv_art"] = np.outer(P["art_hazard_mult"], ART_HAZARD)
    return out


def art_cohorts(stock: np.ndarray, hazard_by_age: np.ndarray, transmission: np.ndarray):
    """People off ART tracked as cohorts. stock: (n x 5) people off ART in each year. A rise in the stock is a new
    cohort with years-since-loss = 1; a fall returns the most recent cohorts to care first. Each cohort's excess death
    risk follows hazard_by_age (n x 5, by its own years since losing care), and it transmits HIV at `transmission` per
    person-year (half in its first year). Negative stock (aid gains) uses the hazard of the calendar year, as before.
    Returns (deaths n x 5, infections n x 5, committed deaths after 2030 n): the cohorts still off care at the end of
    2030 followed to the end of their own 5 years, with no new cuts after 2030."""
    n = stock.shape[0]
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
            a = min(age, N_YEARS) - 1
            deaths[:, t] += size * hazard_by_age[:, a]
            infections[:, t] += size * transmission * ART_INFECT_LAG[a]
        for c in cohorts:
            c[1] += 1
        prev = pos[:, t]
        deaths[:, t] += neg[:, t] * hazard_by_age[:, t]          # gains: same as the sudden-cut formula
        infections[:, t] += neg[:, t] * transmission * ART_INFECT_LAG[t]
    after = np.zeros(n)
    for size, age in cohorts:                          # still off care at the end of 2030
        for a in range(age, N_YEARS + 1):
            after += size * hazard_by_age[:, a - 1]
    return deaths, infections, after


def malaria_levels(row, P, units, need_cov) -> dict:
    """Lives Saved Tool structure: D1 = D0 * prod_i (1 - E_i C_i1) / (1 - E_i C_i0), for one year's units lost.
    Returns the yearly extra deaths per line (arrays n) at baseline D0, before ramp-up and the mortality trend."""
    D0 = _v(row, "malaria_deaths")
    n = len(P["mal_vc_eff"])
    if np.isnan(D0) or D0 <= 0:
        return {k: np.zeros(n) for k in ("mal_itn", "mal_irs", "mal_cm")}
    par, cvc0 = need_cov["mal_itn"]
    cases, ccm0 = need_cov["mal_cm"]
    cvc0 = P["mal_itn_default_use"] if np.isnan(cvc0) else np.full(n, cvc0)
    ccm0 = P["mal_cm_default_cov"] if np.isnan(ccm0) else np.full(n, ccm0)
    Ev, Ec = P["mal_vc_eff"], P["mal_cm_eff"]
    u_vc = units["mal_itn"] + units["mal_irs"]
    cvc1 = np.clip(cvc0 - (u_vc / par if par and not np.isnan(par) else 0), 0, 1)
    ccm1 = np.clip(ccm0 - (units["mal_cm"] / cases if cases and not np.isnan(cases) else 0), 0, 1)
    rv = (1 - Ev * cvc1) / (1 - Ev * cvc0)
    rc = (1 - Ec * ccm1) / (1 - Ec * ccm0)
    total = D0 * (rv * rc - 1)
    dv, dc = D0 * (rv - 1), D0 * (rc - 1)
    denom = np.where(np.abs(dv) + np.abs(dc) > 0, np.abs(dv) + np.abs(dc), 1)
    dv_s, dc_s = total * np.abs(dv) / denom, total * np.abs(dc) / denom
    sh_itn = np.where(np.abs(u_vc) > 0, units["mal_itn"] / np.where(u_vc == 0, 1, u_vc), 0.5)
    return {"mal_itn": dv_s * sh_itn, "mal_irs": dv_s * (1 - sh_itn), "mal_cm": dc_s}


def malaria_deaths(row, P, units, need_cov, trend: bool = True) -> dict:
    """Per-line yearly malaria deaths (n x 5) for a cut in force since year 1: levels x LAG x mortality trend.
    trend: baseline malaria deaths D0 follow the country's 2010-2019 trend in years 1..5."""
    lv = malaria_levels(row, P, units, need_cov)
    f = mortality_trend_factors(row, "malaria", trend)          # D0 x (1 + trend)^(year - 1)
    return {l: np.outer(v, LAG[l] * f) for l, v in lv.items()}


# --------------------------------------------------------------------------- #
# Core
# --------------------------------------------------------------------------- #
def _path(x, default) -> np.ndarray:
    v = np.full(N_YEARS, float(default)) if x is None else np.asarray(x, dtype=float).ravel()
    if v.size != N_YEARS:
        raise ValueError(f"a year path needs {N_YEARS} values (2026-2030), got {v.size}")
    return v


def run_country(iso3: str, scenario: Scenario, fiscal: Fiscal, inputs: dict, ptab: pd.DataFrame,
                n_draws: int = 400, seed: int = 7, keep_draws: bool = False, mortality_trend: bool = True,
                cut_path=None, gov_add_usd=None) -> dict:
    """The full model for one country. cut_path: share of the scenario's full cut in force in each year 2026-2030
    (default all 1 = a sudden cut). gov_add_usd: extra government health money in each year (default 0), on top of
    the government response in `fiscal`. With the defaults the results are the same as the original sudden-cut model."""
    cut_path = np.clip(_path(cut_path, 1.0), 0.0, 1.0)
    gov_add = np.clip(_path(gov_add_usd, 0.0), 0.0, None)
    ci, lines = inputs["ci"], inputs["lines"]
    row = ci.loc[iso3] if iso3 in ci.index else pd.Series(dtype=float)
    cells = lines[lines.iso3 == iso3].copy()
    cells["cut"] = scenario.cuts(cells, iso3, inputs["trend_map"]) if len(cells) else []
    cells["loss"] = cells["usd"] * cells["cut"]

    base = cells.groupby("line")["usd"].sum()
    gross = cells.groupby("line")["loss"].sum()
    P = draw_params(ptab, n_draws, seed)
    Pc = draw_params(ptab, 0)
    n = len(P["uc_imm"])

    # ---- 1. money: effective loss by direct line (per draw because kappa is uncertain) ----
    def effective(series, kappa):
        eff, nonservice = {}, {}
        for b in BUCKETS:
            d = series.reindex(DIRECT[b]).fillna(0.0)
            bmix = base.reindex(DIRECT[b]).fillna(0.0)
            mix = (bmix / bmix.sum()) if bmix.sum() > 0 else pd.Series(inputs["global_mix"][b])
            u = series.get(UNSPEC.get(b, ""), 0.0)
            s = series.get(HSS.get(b, ""), 0.0)
            for l in DIRECT[b]:
                eff[l] = d[l] + (u + kappa * s) * mix.get(l, 0.0)
            nonservice[b] = (1 - kappa) * s
        return eff, nonservice

    eff, nonserv = effective(gross, P["hss_kappa"])
    eff_base, _ = effective(base, P["hss_kappa"])
    effc, nonservc = effective(gross, Pc["hss_kappa"])
    effc_base, _ = effective(base, Pc["hss_kappa"])

    # ---- 2. fiscal response, year by year ----
    # aid lost in year t = full scenario loss x cut_path(t); the government response in `fiscal` applies to that year's
    # loss (capped by fiscal space), then any extra money (gov_add) is added. Net gap = loss - both, floored at 0.
    fs = fiscal_space(row, fiscal.effort)
    G = float(np.clip(gross, 0, None).sum())
    th_hist = max(0.0, theta_historical(inputs["reg"])[0])

    def response(g):
        want = {"none": 0.0, "gradual": 0.0, "historical": th_hist * g, "custom": fiscal.theta * g,
                "max": g}[fiscal.mode]
        r = min(want, fs["capacity"]) if (fiscal.cap_to_space or fiscal.mode == "max") else want
        return max(r, 0.0), want

    G_t = G * cut_path
    R_t = np.array([response(g)[0] for g in G_t])                    # the existing government response, per year
    budget_t = np.minimum(R_t + gov_add, G_t)                        # total replacement, never more than is lost
    R, want = response(G)                                            # full-cut values, reported for the fiscal panel

    ep = epi(row, Pc)
    ucc = unit_costs(row, Pc)
    pudc = per_unit_deaths(row, Pc, ep["art_cov"], mortality_trend)

    # deaths per $ (central) for "lives first" ranking; malaria via a small marginal LiST calculation
    def deaths_per_dollar(l):
        if l in pudc:
            return float(pudc[l].sum() / ucc[l][0])
        if l.startswith("mal_"):
            u = {k: np.zeros(1) for k in ("mal_itn", "mal_irs", "mal_cm")}
            u[l] = np.array([1e6 / ucc[l][0]])
            return float(malaria_deaths(row, Pc, u, ep["need_cov"], mortality_trend)[l].sum() / 1e6)
        return 0.0

    dpd = {l: deaths_per_dollar(l) for l in ALL_DIRECT}

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
            for l in sorted(ALL_DIRECT, key=lambda k: -dpd[k]):
                take = np.minimum(left, pos[l])
                rep[l], left = take, left - take
            sn = sum(posn.values())
            repn = {b: np.minimum(v, left * v / np.where(sn > 0, sn, 1)) for b, v in posn.items()}
        return rep, repn

    # per year: effective loss scaled by the path, replacement allocated, net loss by line
    years = range(N_YEARS)
    effc_t, repc_t, repnc_t, net_t, netc_t = [], [], [], [], []
    for t in years:
        e_t = {l: v * cut_path[t] for l, v in eff.items()}
        ns_t = {b: v * cut_path[t] for b, v in nonserv.items()}
        ec_t = {l: v * cut_path[t] for l, v in effc.items()}
        nsc_t = {b: v * cut_path[t] for b, v in nonservc.items()}
        r, _ = allocate(e_t, ns_t, budget_t[t])
        rc, rnc = allocate(ec_t, nsc_t, budget_t[t])
        effc_t.append(ec_t)
        repc_t.append(rc)
        repnc_t.append(rnc)
        net_t.append({l: e_t[l] - r[l] for l in ALL_DIRECT})
        netc_t.append({l: ec_t[l] - rc[l] for l in ALL_DIRECT})

    # ---- 3. coverage: people losing each service in each year ----
    uc = unit_costs(row, P)
    units = {l: np.zeros((n, N_YEARS)) for l in ALL_DIRECT}           # per draw x year
    unitsc = {l: np.zeros((1, N_YEARS)) for l in ALL_DIRECT}          # central x year
    capped, excess = {}, {}
    for l in ALL_DIRECT:
        need, cov = ep["need_cov"].get(l, (np.nan, np.nan))
        if l in ("mal_itn", "mal_irs") and np.isnan(cov):
            cov = Pc["mal_itn_default_use"][0]
        if l == "mal_cm" and np.isnan(cov):
            cov = Pc["mal_cm_default_cov"][0]
        # people losing the service = people donor money pays for x share of that money lost. Donor money pays for
        # min(people covered, aid / cost per person): when aid exceeds the full cost of everyone covered, the excess
        # pays for things other than the service itself, so the loss scales proportionally instead of running past
        # the people covered. When aid buys less than full coverage this equals net loss / cost per person.
        covered = cov * need if (l in ep["need_cov"] and not np.isnan(need) and not np.isnan(cov)) else np.nan
        b0 = float(np.asarray(effc_base[l]).ravel()[0])
        excess[l] = bool(not np.isnan(covered) and b0 / float(ucc[l][0]) > covered)
        if excess[l] and (iso3, l) not in _EXCESS_LOGGED:
            _EXCESS_LOGGED.add((iso3, l))
            log.warning("%s %s: donor aid ($%.0f) buys %.0f units at $%.0f each, more than the %.0f people covered; "
                        "units lost scaled proportionally", iso3, l, b0, b0 / float(ucc[l][0]), float(ucc[l][0]), covered)
        capped[l] = False
        for t in years:
            u = _units_lost(net_t[t][l], eff_base[l], uc[l], covered) * (1 - P["continuity"])
            uc0 = _units_lost(netc_t[t][l], effc_base[l], ucc[l], covered) * (1 - Pc["continuity"])
            if l in ep["need_cov"] and not np.isnan(need) and not np.isnan(cov):
                hi, lo = cov * need, -(1 - cov) * need
                capped[l] = capped[l] or bool(np.ravel(uc0)[0] > hi)
                u, uc0 = np.clip(u, lo, hi), np.clip(uc0, lo, hi)
            units[l][:, t], unitsc[l][:, t] = u, uc0
    # vector control shares one coverage pool
    par, cvc = ep["need_cov"]["mal_itn"]
    if not np.isnan(par):
        cvc = Pc["mal_itn_default_use"][0] if np.isnan(cvc) else cvc
        for U in (units, unitsc):
            tot = U["mal_itn"] + U["mal_irs"]
            scale = np.where(tot > cvc * par, cvc * par / np.where(tot == 0, 1, tot), 1.0)
            U["mal_itn"], U["mal_irs"] = U["mal_itn"] * scale, U["mal_irs"] * scale

    # ---- 4. lives ----
    # ramp-up (LAG) is indexed by how long the cut has been in force, not by calendar year
    started = np.flatnonzero(cut_path > 0)
    dur = np.array([t - started[0] if started.size and t >= started[0] else 0 for t in years])
    mal_f = mortality_trend_factors(row, "malaria", mortality_trend)

    def lives(Px, U):
        """Deaths (n x 5), infections (n x 5) and committed deaths after 2030 (n) for one set of draws."""
        nx = len(Px["uc_imm"])
        lv = per_unit_levels(row, Px, ep["art_cov"], mortality_trend)
        d, inf = {}, {}
        for l in ("hiv_pmtct", "hiv_prev", "hiv_ovc", "tb_ds", "tb_dr", "imm"):
            lag = LAG.get(l)
            ramp = np.array([lag[k] for k in dur]) if lag is not None else np.ones(N_YEARS)
            d[l] = U[l] * lv[l] * ramp                                      # year t depends only on year t's loss
        hz = np.outer(Px["art_hazard_mult"], ART_HAZARD)
        d["hiv_art"], inf["hiv_art"], after = art_cohorts(U["hiv_art"], hz, Px["art_transmission"])
        mal = {k: np.zeros((nx, N_YEARS)) for k in ("mal_itn", "mal_irs", "mal_cm")}
        for t in years:
            m = malaria_levels(row, Px, {k: U[k][:, t] for k in mal}, ep["need_cov"])
            for k in mal:
                mal[k][:, t] = m[k] * LAG[k][dur[t]] * mal_f[t]
        d.update(mal)
        inf["hiv_pmtct"] = U["hiv_pmtct"] * Px["pmtct_vt_reduction"][:, None]
        inf["hiv_prev"] = U["hiv_prev"].copy()
        return d, inf, after

    deaths, infections, after = lives(P, units)
    deathsc, _, afterc = lives(Pc, unitsc)
    deathsc = {l: v for l, v in deathsc.items() if l in pudc or l.startswith("mal_")}

    # ---- assemble (money and people are averages over the 5 years: equal to the yearly values for a sudden cut) ----
    def q(a, p):
        return float(np.percentile(a, p)) if np.size(a) > 1 else float(np.asarray(a).ravel()[0])

    def mean_c(seq, l):
        return float(np.mean([np.asarray(x[l]).ravel()[0] for x in seq]))

    recs = []
    for l in ALL_DIRECT:
        need, cov = ep["need_cov"].get(l, (np.nan, np.nan))
        d5 = deaths[l].sum(axis=1)
        d1 = deaths[l][:, 0]
        inf5 = infections[l].sum(axis=1) if l in infections else np.zeros(n)
        cov_used = cov
        if l in ("mal_itn", "mal_irs") and np.isnan(cov):
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
            "need": need, "cov0": cov_used,
            "donor_share_of_coverage": donor_units / (cov_used * need) if (need and cov_used and not np.isnan(need)) else np.nan,
            "units_lost": uc_mean, "units_lost_lo": q(u_mean, 2.5), "units_lost_hi": q(u_mean, 97.5),
            "cov_drop_pp": uc_mean / need * 100 if (need and not np.isnan(need)) else np.nan,
            "capped": capped.get(l, False),
            "donor_exceeds_cost": excess.get(l, False),
            "deaths_y1": float(deathsc[l][0, 0]) if l in deathsc else 0.0,
            "deaths_y1_lo": q(d1, 2.5), "deaths_y1_hi": q(d1, 97.5),
            "deaths_5y": float(deathsc[l].sum()) if l in deathsc else 0.0,
            "deaths_5y_med": q(d5, 50), "deaths_5y_lo": q(d5, 2.5), "deaths_5y_hi": q(d5, 97.5),
            "infections_5y": q(inf5, 50), "infections_5y_lo": q(inf5, 2.5), "infections_5y_hi": q(inf5, 97.5),
        })
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
        b_gross = float(gross.reindex(bl).sum()) * float(cut_path.mean()) if bl else 0.0
        b_rep = float(np.mean([sum(np.asarray(repc_t[t][l]).ravel()[0] for l in lb)
                               + float(np.asarray(repnc_t[t].get(b, 0.0)).ravel()[0]) for t in years]))
        b_net = b_gross - b_rep
        dc5 = float(sum(deathsc[l].sum() for l in lb if l in deathsc))
        bsum.append({"bucket": b, "base_usd": b_base, "gross_loss_usd": b_gross, "replaced_usd": b_rep,
                     "net_loss_usd": b_net, "deaths_y1": float(sum(deathsc[l][0, 0] for l in lb if l in deathsc)),
                     "deaths_5y": dc5, "deaths_5y_lo": q(d5, 2.5), "deaths_5y_hi": q(d5, 97.5),
                     "deaths_y1_lo": q(d1, 2.5), "deaths_y1_hi": q(d1, 97.5),
                     "infections_5y": q(inf5, 50), "infections_5y_lo": q(inf5, 2.5), "infections_5y_hi": q(inf5, 97.5),
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
    year_tab = pd.DataFrame({"year": [2026 + t for t in years], "cut_share": cut_path, "aid_lost_usd": G_t,
                             "response_usd": R_t, "gov_add_usd": gov_add, "replaced_usd": budget_t,
                             "gap_usd": G_t - budget_t,
                             "deaths": [float(sum(deathsc[l][0, t] for l in deathsc)) for t in years]})

    out = {"iso3": iso3, "cells": cells, "lines": tab, "buckets": bsum, "path": path, "path_band": path_band,
           "years": year_tab,
           "fiscal": {**fs, "gross_loss": G, "replacement": float(R_t.mean()), "replacement_wanted": want,
                      "theta_hist": th_hist},
           "flags": ep["flags"], "deaths_per_dollar": dpd,
           "committed": {"deaths": d5c + float(np.ravel(afterc)[0]), "deaths_lo": q(committed, 2.5),
                         "deaths_hi": q(committed, 97.5), "after_2030": float(np.ravel(afterc)[0]),
                         "after_2030_lo": q(after, 2.5), "after_2030_hi": q(after, 97.5)},
           "totals": {"base": float(base.sum()), "gross": float(G_t.mean()), "replaced": float(budget_t.mean()),
                      "net": float((G_t - budget_t).mean()), "gross_full": G,
                      "gains": float(-np.clip(gross, None, 0).sum()),
                      "deaths_5y": d5c, "deaths_5y_lo": q(tot5, 2.5), "deaths_5y_hi": q(tot5, 97.5),
                      "deaths_y1": float(sum(deathsc[l][0, 0] for l in deathsc))}}
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


def donor_cost_excess(inputs, ptab) -> pd.DataFrame:
    """Country-lines where baseline donor aid / cost per person exceeds the people currently covered (the excess
    pays for things other than the service; units lost are scaled proportionally there)."""
    rows = []
    for c in [c for c in inputs["ci"].index if c in set(inputs["lines"].iso3)]:
        L = run_country(c, Scenario(), Fiscal(), inputs, ptab, n_draws=0)["lines"]
        for r in L[L["donor_exceeds_cost"]].itertuples():
            rows.append({"iso3": c, "line": r.line, "aid_usd": r.base_usd, "unit_cost": r.unit_cost,
                         "units_aid_buys": r.base_usd / r.unit_cost, "people_covered": r.cov0 * r.need})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Government health budget: today's share, room to the Abuja target, history, break-even
# --------------------------------------------------------------------------- #
ABUJA_CEILING = 15.0             # % of government spending on health (Abuja Declaration target)
HEALTH_SHARE_FILE = HERE / "ext_data" / "wdi" / "sh_xpd_ghed_ge_zs.csv"


def _share_history() -> pd.DataFrame:
    if not hasattr(_share_history, "cache"):
        d = pd.read_csv(HEALTH_SHARE_FILE)
        d.columns = ["iso3", "year", "share"]
        d["iso3"] = d["iso3"].str.upper()
        _share_history.cache = d.dropna()
    return _share_history.cache


def health_budget(iso3: str, inputs: dict) -> dict:
    """Health's share of government spending today (%), total government spending (US$, = government health spending
    2023 / that share), the room to the Abuja 15% ceiling, and the fastest sustained rise in the country's history
    (90th percentile of its 2001-2023 yearly changes in the share, percentage points)."""
    row = inputs["ci"].loc[iso3] if iso3 in inputs["ci"].index else pd.Series(dtype=float)
    share, ghes = _v(row, "sh_xpd_ghed_ge_zs"), _v(row, "ghes_2023")
    gov = ghes / (share / 100) if share and share > 0 and not np.isnan(ghes) else np.nan
    h = _share_history()
    h = h[(h.iso3 == iso3) & h.year.between(2000, 2023)].sort_values("year")
    ch = h["share"].diff()[h["year"].diff() == 1].dropna()
    p90 = float(ch.quantile(0.9)) if len(ch) >= 5 else np.nan
    room = max(ABUJA_CEILING - share, 0.0) if not np.isnan(share) else np.nan
    return {"share_pct": share, "gov_spend_usd": gov, "ceiling_pct": ABUJA_CEILING, "room_pct": room,
            "p90_rise_pp": p90, "ghes_usd": ghes}


def _money_by_year(iso3, scenario, fiscal, inputs, cut_path):
    """Aid lost and the existing government response in each year 2026-2030 (US$), without running the full model."""
    ci, lines = inputs["ci"], inputs["lines"]
    row = ci.loc[iso3] if iso3 in ci.index else pd.Series(dtype=float)
    cells = lines[lines.iso3 == iso3].copy()
    loss = (cells["usd"] * scenario.cuts(cells, iso3, inputs["trend_map"])) if len(cells) else pd.Series(dtype=float)
    G = float(np.clip(loss.groupby(cells["line"]).sum(), 0, None).sum()) if len(cells) else 0.0
    fs = fiscal_space(row, fiscal.effort)
    th = max(0.0, theta_historical(inputs["reg"])[0])
    G_t = G * np.clip(_path(cut_path, 1.0), 0, 1)
    R_t = []
    for g in G_t:
        want = {"none": 0.0, "gradual": 0.0, "historical": th * g, "custom": fiscal.theta * g,
                "max": g}[fiscal.mode]
        R_t.append(max(min(want, fs["capacity"]) if (fiscal.cap_to_space or fiscal.mode == "max") else want, 0.0))
    return G_t, np.array(R_t)


def gov_add_from_points(points, gov_spend_usd: float) -> np.ndarray:
    """Extra government health money (US$) from extra percentage points of the government budget, year by year."""
    return np.clip(_path(points, 0.0), 0, None) / 100 * (gov_spend_usd if gov_spend_usd == gov_spend_usd else 0.0)


def break_even_share(iso3, scenario, fiscal, inputs, cut_path=None, tol: float = 1e-4):
    """Smallest constant yearly increase s in health's share of government spending (percentage points per year,
    cumulative: s in 2026, 2s in 2027, ...) that keeps the net gap <= 0 in every year of the cut path, on top of the
    government response in `fiscal`; capped so the share never passes the Abuja 15% target. Found by bisection.
    Returns 0.0 if there is no gap, None if it can't be reached by 15% (or the budget data are missing)."""
    hb = health_budget(iso3, inputs)
    G_t, R_t = _money_by_year(iso3, scenario, fiscal, inputs, cut_path)
    gap = G_t - R_t
    if (gap <= 1e-6).all():
        return 0.0
    if np.isnan(hb["gov_spend_usd"]) or np.isnan(hb["room_pct"]) or hb["room_pct"] <= 0:
        return None
    steps = np.arange(1, N_YEARS + 1)

    def keeps_up(s):
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
    countries = countries or [c for c in inputs["ci"].index if c in set(inputs["lines"].iso3)]
    recs = []
    for c in countries:
        r = run_country(c, scenario, fiscal, inputs, ptab, n_draws=n_draws, mortality_trend=mortality_trend)
        row = inputs["ci"].loc[c]
        t = r["totals"]
        rec = {"iso3": c, "pop": _v(row, "sp_pop_totl"), "base_usd": t["base"], "gross_loss_usd": t["gross"],
               "replaced_usd": t["replaced"], "net_loss_usd": t["net"], "deaths_y1": t["deaths_y1"],
               "deaths_5y": t["deaths_5y"], "deaths_5y_lo": t["deaths_5y_lo"], "deaths_5y_hi": t["deaths_5y_hi"],
               "loss_pct_ghes": t["gross"] / r["fiscal"]["ghes"] if r["fiscal"]["ghes"] else np.nan,
               "capacity_usd": r["fiscal"]["capacity"]}
        for _, bb in r["buckets"].iterrows():
            rec[f"deaths_5y_{bb['bucket']}"] = bb["deaths_5y"]
            rec[f"net_loss_{bb['bucket']}"] = bb["net_loss_usd"]
        rec["hiv_infections_5y"] = float(r["buckets"].set_index("bucket").loc["HIV", "infections_5y"])
        recs.append(rec)
    return pd.DataFrame(recs)


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
    net immunization loss. Malaria is estimated on child deaths and applied proportionally to all-age deaths."""
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
    linear in funding from 0 up to the first point, and held flat above the last one."""
    lr = np.log(LANCET_RR[bucket])
    if funding_pc <= 0:
        return 0.0
    if funding_pc < LANCET_FUNDING[0]:
        return float(lr[0] * funding_pc / LANCET_FUNDING[0])
    return float(np.interp(np.log(funding_pc), np.log(LANCET_FUNDING), lr))


def lancet_projection(res: dict, inputs: dict) -> pd.DataFrame:
    """Apply the published rate ratios to the country's US-source health aid per capita before and after the cut.
    The US cut is the share of US money lost in the modelled cells, net of government backfill in proportion."""
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
