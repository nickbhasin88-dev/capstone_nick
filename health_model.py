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
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

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
        return np.clip(out, -1.0, 1.0)


def uniform_scenario(bucket: str, cut: float) -> Scenario:
    sc = Scenario(name=f"{bucket} -{cut:.0%}", bucket_only=bucket)
    sc.src_direct = {s: cut for s in SOURCE_GROUPS}
    sc.src_multi = {s: cut for s in SOURCE_GROUPS}
    return sc


@dataclass
class Fiscal:
    mode: str = "none"            # none | historical | custom | max
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
    cm = _v(row, "sh_mlr_tret_zs") / 100
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
    if np.isnan(cm):
        flags.append("malaria treatment coverage not surveyed: default assumed")
    return {"need_cov": e, "hiv_incidence_per_1000": inc_hiv, "flags": flags, "art_cov": art}


def unit_costs(row: pd.Series, P: dict) -> dict:
    g = _v(row, "gdp_pc", 2000.0)
    sc = (max(g, 200.0) / 2000.0) ** P["uc_scale_elast"]
    inc = _v(row, "sh_hiv_incd_tl") / _v(row, "sp_pop_totl") * 1000
    inc = 0.3 if np.isnan(inc) else float(np.clip(inc, 0.05, 10))
    return {
        "hiv_art": P["uc_art_commodity"] + P["uc_art_service_ref"] * sc,
        "hiv_pmtct": P["uc_pmtct"] * np.ones_like(sc),
        "hiv_prev": P["cpia_ref"] * (1.0 / inc) ** 0.5,          # $ per infection averted
        "hiv_ovc": P["uc_ovc"] * np.ones_like(sc),
        "tb_ds": P["uc_tb_commodity"] + P["uc_tb_service_ref"] * sc,
        "tb_dr": P["uc_tb_dr"] * np.ones_like(sc),
        "mal_itn": P["uc_itn"] * np.ones_like(sc),
        "mal_irs": P["uc_irs"] * np.ones_like(sc),
        "mal_cm": P["uc_mal_cm"] * np.ones_like(sc),
        "imm": P["uc_imm"] * np.ones_like(sc),
    }


def per_unit_deaths(row: pd.Series, P: dict, art_cov: float) -> dict:
    """Deaths per unit of service lost, by year 1..5 (arrays n x 5). Malaria handled separately (LiST)."""
    n = len(P["uc_imm"])
    h = _v(row, "tb_hiv_share", 0.0)
    a = 0.0 if np.isnan(art_cov) else art_cov
    cfr_up = P["tb_cfr_untreated_pos"] * (1 - 0.3 * a)     # untreated HIV+ TB: lower when on ART (0.78 -> 0.49)
    cfr_tp = P["tb_cfr_treated_pos"] * (1 - 0.3 * a)
    dcfr = (1 - h) * (P["tb_cfr_untreated_neg"] - P["tb_cfr_treated_neg"]) + h * (cfr_up - cfr_tp)
    u5 = _v(row, "sh_dyn_mort", 50.0)
    imm = P["imm_deaths_per_child_ref"] * float(np.clip(u5 / 50.0, 0.3, 2.5))
    return {
        "hiv_art": np.outer(P["art_hazard_mult"], ART_HAZARD),
        "hiv_pmtct": np.outer(P["pmtct_vt_reduction"] * P["pmtct_infant_mort"], LAG["hiv_pmtct"]),
        "hiv_prev": np.zeros((n, N_YEARS)), "hiv_ovc": np.zeros((n, N_YEARS)),
        "tb_ds": np.outer(dcfr, LAG["tb_ds"]),
        "tb_dr": np.outer(P["tb_dr_dcfr"], LAG["tb_dr"]),
        "imm": np.outer(imm, LAG["imm"]),
    }


def malaria_deaths(row, P, units, need_cov) -> dict:
    """Lives Saved Tool structure: D1 = D0 * prod_i (1 - E_i C_i1) / (1 - E_i C_i0). Returns per-line yearly deaths."""
    D0 = _v(row, "malaria_deaths")
    n = len(P["mal_vc_eff"])
    zero = {k: np.zeros((n, N_YEARS)) for k in ("mal_itn", "mal_irs", "mal_cm")}
    if np.isnan(D0) or D0 <= 0:
        return zero
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
    return {"mal_itn": np.outer(dv_s * sh_itn, LAG["mal_itn"]),
            "mal_irs": np.outer(dv_s * (1 - sh_itn), LAG["mal_irs"]),
            "mal_cm": np.outer(dc_s, LAG["mal_cm"])}


# --------------------------------------------------------------------------- #
# Core
# --------------------------------------------------------------------------- #
def run_country(iso3: str, scenario: Scenario, fiscal: Fiscal, inputs: dict, ptab: pd.DataFrame,
                n_draws: int = 400, seed: int = 7, keep_draws: bool = False) -> dict:
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

    # ---- 2. fiscal response ----
    fs = fiscal_space(row, fiscal.effort)
    G = float(np.clip(gross, 0, None).sum())
    th_hist = max(0.0, theta_historical(inputs["reg"])[0])
    want = {"none": 0.0, "historical": th_hist * G, "custom": fiscal.theta * G, "max": G}[fiscal.mode]
    R = min(want, fs["capacity"]) if (fiscal.cap_to_space or fiscal.mode == "max") else want
    R = max(R, 0.0)

    ep = epi(row, Pc)
    ucc = unit_costs(row, Pc)
    pudc = per_unit_deaths(row, Pc, ep["art_cov"])

    # deaths per $ (central) for "lives first" ranking; malaria via a small marginal LiST calculation
    def deaths_per_dollar(l):
        if l in pudc:
            return float(pudc[l].sum() / ucc[l][0])
        if l.startswith("mal_"):
            u = {k: np.zeros(1) for k in ("mal_itn", "mal_irs", "mal_cm")}
            u[l] = np.array([1e6 / ucc[l][0]])
            return float(malaria_deaths(row, Pc, u, ep["need_cov"])[l].sum() / 1e6)
        return 0.0

    dpd = {l: deaths_per_dollar(l) for l in ALL_DIRECT}

    def allocate(eff_d, nons):
        """Split the replacement budget R over lines with a loss. Returns (by direct line, by bucket systems)."""
        pos = {l: np.clip(np.asarray(v, dtype=float), 0, None) for l, v in eff_d.items()}
        posn = {b: np.clip(np.asarray(v, dtype=float), 0, None) for b, v in nons.items()}
        tot = sum(pos.values()) + sum(posn.values())
        rep = {l: np.zeros_like(v) for l, v in pos.items()}
        repn = {b: np.zeros_like(v) for b, v in posn.items()}
        if R <= 0:
            return rep, repn
        safe = np.where(tot > 0, tot, 1)
        if fiscal.allocation == "pro_rata":
            rep = {l: R * v / safe for l, v in pos.items()}
            repn = {b: R * v / safe for b, v in posn.items()}
        else:                                  # lives first: most deaths averted per dollar gets refilled first
            left = np.full_like(np.asarray(tot, dtype=float), R)
            for l in sorted(ALL_DIRECT, key=lambda k: -dpd[k]):
                take = np.minimum(left, pos[l])
                rep[l], left = take, left - take
            sn = sum(posn.values())
            repn = {b: np.minimum(v, left * v / np.where(sn > 0, sn, 1)) for b, v in posn.items()}
        return rep, repn

    rep, _ = allocate(eff, nonserv)
    repc, repnc = allocate(effc, nonservc)
    net = {l: eff[l] - rep[l] for l in ALL_DIRECT}
    netc = {l: effc[l] - repc[l] for l in ALL_DIRECT}

    # ---- 3. coverage ----
    uc = unit_costs(row, P)
    units, unitsc, capped = {}, {}, {}
    for l in ALL_DIRECT:
        need, cov = ep["need_cov"].get(l, (np.nan, np.nan))
        if l in ("mal_itn", "mal_irs") and np.isnan(cov):
            cov = Pc["mal_itn_default_use"][0]
        if l == "mal_cm" and np.isnan(cov):
            cov = Pc["mal_cm_default_cov"][0]
        u = np.asarray(net[l]) / uc[l] * (1 - P["continuity"])
        uc0 = np.asarray(netc[l]) / ucc[l] * (1 - Pc["continuity"])
        if l in ep["need_cov"] and not np.isnan(need) and not np.isnan(cov):
            hi, lo = cov * need, -(1 - cov) * need
            capped[l] = bool(uc0[0] > hi) if np.ndim(uc0) else False
            u, uc0 = np.clip(u, lo, hi), np.clip(uc0, lo, hi)
        units[l], unitsc[l] = u, uc0
    # vector control shares one coverage pool
    par, cvc = ep["need_cov"]["mal_itn"]
    if not np.isnan(par):
        cvc = Pc["mal_itn_default_use"][0] if np.isnan(cvc) else cvc
        for U in (units, unitsc):
            tot = U["mal_itn"] + U["mal_irs"]
            scale = np.where(tot > cvc * par, cvc * par / np.where(tot == 0, 1, tot), 1.0)
            U["mal_itn"], U["mal_irs"] = U["mal_itn"] * scale, U["mal_irs"] * scale

    # ---- 4. lives ----
    pud = per_unit_deaths(row, P, ep["art_cov"])
    deaths = {}
    for l in ALL_DIRECT:
        if l in pud:
            deaths[l] = pud[l] * np.asarray(units[l])[:, None]
    deaths.update(malaria_deaths(row, P, units, ep["need_cov"]))
    infections = {
        "hiv_art": np.outer(units["hiv_art"] * P["art_transmission"], ART_INFECT_LAG),
        "hiv_pmtct": np.outer(units["hiv_pmtct"] * P["pmtct_vt_reduction"], np.ones(N_YEARS)),
        "hiv_prev": np.outer(units["hiv_prev"], np.ones(N_YEARS)),
    }
    # central run (all parameters at central values)
    deathsc = {l: pudc[l] * np.asarray(unitsc[l])[:, None] for l in ALL_DIRECT if l in pudc}
    deathsc.update(malaria_deaths(row, Pc, unitsc, ep["need_cov"]))

    # ---- assemble ----
    def q(a, p):
        return float(np.percentile(a, p)) if np.size(a) > 1 else float(np.asarray(a).ravel()[0])

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
        recs.append({
            "bucket": LINE_BUCKET[l], "line": l, "label": LINE_LABELS[l],
            "base_usd": float(np.asarray(effc_base[l]).ravel()[0]),
            "gross_loss_usd": float(np.asarray(effc[l]).ravel()[0]),
            "replaced_usd": float(np.asarray(repc[l]).ravel()[0]),
            "net_loss_usd": float(np.asarray(netc[l]).ravel()[0]),
            "unit_cost": float(ucc[l][0]), "unit_label": UNIT_LABELS[l],
            "need": need, "cov0": cov_used,
            "donor_share_of_coverage": donor_units / (cov_used * need) if (need and cov_used and not np.isnan(need)) else np.nan,
            "units_lost": float(np.asarray(unitsc[l]).ravel()[0]),
            "units_lost_lo": q(units[l], 2.5), "units_lost_hi": q(units[l], 97.5),
            "cov_drop_pp": float(np.asarray(unitsc[l]).ravel()[0]) / need * 100 if (need and not np.isnan(need)) else np.nan,
            "capped": capped.get(l, False),
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
        b_gross = float(gross.reindex(bl).sum()) if bl else 0.0
        b_rep = float(sum(np.asarray(repc[l]).ravel()[0] for l in lb)) + float(np.asarray(repnc.get(b, 0.0)).ravel()[0])
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
    tot5 = sum(deaths[l].sum(axis=1) for l in ALL_DIRECT)
    path_band = pd.DataFrame({"lo": np.percentile(np.cumsum(sum(deaths[l] for l in ALL_DIRECT), axis=1), 2.5, axis=0),
                              "hi": np.percentile(np.cumsum(sum(deaths[l] for l in ALL_DIRECT), axis=1), 97.5, axis=0)},
                             index=path.index)

    out = {"iso3": iso3, "cells": cells, "lines": tab, "buckets": bsum, "path": path, "path_band": path_band,
           "fiscal": {**fs, "gross_loss": G, "replacement": R, "replacement_wanted": want, "theta_hist": th_hist},
           "flags": ep["flags"], "deaths_per_dollar": dpd,
           "totals": {"base": float(base.sum()), "gross": G, "replaced": R, "net": G - R,
                      "gains": float(-np.clip(gross, None, 0).sum()),
                      "deaths_5y": float(sum(deathsc[l].sum() for l in deathsc)),
                      "deaths_5y_lo": q(tot5, 2.5), "deaths_5y_hi": q(tot5, 97.5),
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
def dose_response(iso3, bucket, fiscal, inputs, ptab, grid=None, n_draws=120):
    grid = np.linspace(0, 1, 11) if grid is None else grid
    rows = []
    for g in grid:
        r = run_country(iso3, uniform_scenario(bucket, float(g)), fiscal, inputs, ptab, n_draws=n_draws)
        bb = r["buckets"].set_index("bucket").loc[bucket]
        main_line = {"HIV": "hiv_art", "TB": "tb_ds", "Malaria": "mal_itn", "Immunization": "imm"}[bucket]
        ln = r["lines"].set_index("line").loc[main_line]
        rows.append({"cut": g, "net_loss_usd": bb["net_loss_usd"], "deaths_5y": bb["deaths_5y"],
                     "lo": bb["deaths_5y_lo"], "hi": bb["deaths_5y_hi"], "cov_drop_pp": ln["cov_drop_pp"],
                     "cov0": ln["cov0"]})
    return pd.DataFrame(rows)


def run_all(scenario, fiscal, inputs, ptab, n_draws=80, countries=None):
    countries = countries or [c for c in inputs["ci"].index if c in set(inputs["lines"].iso3)]
    recs = []
    for c in countries:
        r = run_country(c, scenario, fiscal, inputs, ptab, n_draws=n_draws)
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
