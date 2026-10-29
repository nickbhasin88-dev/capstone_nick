"""Independent reproduction of the funding-cut model, built from docs/SPEC.md ONLY (sections 0-7, plus the
§6 "further deaths across the return-to-care assumption" range over art_reengage) and the data files it names.
No other description of the method and none of the model code was consulted. Central run only (every parameter at
`central`). Section references (SPEC §n) point to docs/SPEC.md; places where SPEC.md is silent or ambiguous are
listed in notes.md (a.n).

Usage: python repro.py      (writes independent.csv next to this file)
"""
import math
from pathlib import Path

import numpy as np
import pandas as pd

REPO = str(Path(__file__).resolve().parents[3])
OUT = str(Path(__file__).resolve().parent)

PARAMS = pd.read_csv(f"{REPO}/model_params.csv").set_index("param")
P = PARAMS["central"].astype(float).to_dict()  # SPEC §0: central run
P_LOW = PARAMS["low"].astype(float).to_dict()
P_HIGH = PARAMS["high"].astype(float).to_dict()
CI = pd.read_csv(f"{REPO}/model_data/country_inputs.csv").set_index("iso3")
DAH = pd.read_csv(f"{REPO}/model_data/dah_lines.csv")
UCR = pd.read_csv(f"{REPO}/unit_cost_reference.csv")

YEARS = 5           # t = 0..4 = 2026..2030 (SPEC §0)
POST_YEARS = 5      # k = 0..4 = 2031..2035 (SPEC §1 constants)
T_ALL = YEARS + POST_YEARS
TRENDS = True       # "already-changing death rates" switch: on by default (SPEC §6 "Death-rate switch")

# ---------------------------------------------------------------- SPEC §1 lines, constants
DIRECT_CH = {"Bilateral agency", "NGOs", "Gates direct", "Other"}  # SPEC §2
BUCKETS = {
    # direct lines; linked line (care); unspec / hss lines; §3 treatment lines T_b, prevention lines P_b, testing target
    "HIV": dict(direct=["hiv_art", "hiv_pmtct", "hiv_prev", "hiv_ovc"], care="hiv_care_ct", unspec="hiv_unspec",
                hss="hiv_hss", shares="hiv", treat=["hiv_art"], prev=["hiv_prev", "hiv_pmtct"], test="hiv_care_ct",
                donor="donor_share_hiv"),
    "TB": dict(direct=["tb_ds", "tb_dr"], care=None, unspec="tb_unspec", hss="tb_hss", shares="tb",
               treat=["tb_ds", "tb_dr"], prev=[], test="tb_ds", donor="donor_share_tb"),
    "Malaria": dict(direct=["mal_itn", "mal_irs", "mal_cm"], care=None, unspec="mal_unspec", hss="mal_hss",
                    shares="malaria", treat=["mal_cm"], prev=["mal_itn", "mal_irs"], test="mal_cm",
                    donor="donor_share_malaria"),
    "Immunization": dict(direct=["imm"], care=None, unspec=None, hss=None, shares=None, treat=[], prev=[], test=None,
                         donor="donor_share_imm"),
}
LINE_BUCKET = {l: b for b, c in BUCKETS.items() for l in c["direct"]}
OUT_LINES = ["hiv_art", "hiv_pmtct", "hiv_prev", "tb_ds", "tb_dr", "mal_itn", "mal_irs", "mal_cm", "imm"]
UNIT_LINES = OUT_LINES + ["hiv_ovc"]  # every direct line gets units (SPEC §5)
HIV_LINES = ["hiv_art", "hiv_pmtct", "hiv_prev"]
SHARE_PURPOSES = ["treatment", "prevention", "testing", "rssh", "pm"]

DR_TB_SHARE, DR_TB_COV = 0.04, 0.45  # fallbacks only
ART_HAZARD = [0.013, 0.025, 0.037, 0.049, 0.060, 0.068, 0.072, 0.073, 0.071, 0.067]  # years 1..10 since stopping
ART_HAZARD_LEGACY = [0.012, 0.028, 0.038, 0.045, 0.050]
ART_REENGAGE_LEGACY = 0.5
ART_TRANSMISSION_FALLBACK = 0.118
ART_INFECT_LAG = [0.5, 1, 1, 1, 1]
WEIBULL_SHAPE = 2.25
CPI_U = {2014: 236.736, 2018: 251.107, 2019: 255.657, 2020: 258.811, 2021: 270.970, 2022: 292.655, 2023: 304.702}
LAG = {"hiv_pmtct": [0.6, 1, 1, 1, 1], "tb_ds": [0.7, 1, 1, 1, 1], "tb_dr": [0.7, 1, 1, 1, 1],
       "mal_itn": [0.5, 1, 1, 1, 1], "mal_irs": [0.8, 1, 1, 1, 1], "mal_cm": [1, 1, 1, 1, 1],
       "imm": [0.4, 0.75, 0.95, 1, 1]}  # imm row: legacy vaccine rule only (SPEC §1, §6)
IMM_W_LEGACY = [0.40, 0.35, 0.20, 0.05]


def cpi_to_2023(year):
    return CPI_U[2023] / CPI_U[int(year)]


def nz(v, default=np.nan):
    """Float value, or `default` when missing."""
    if v is None:
        return default
    try:
        return default if math.isnan(float(v)) else float(v)
    except (TypeError, ValueError):
        return default


def isnan(v):
    return v is None or (isinstance(v, float) and math.isnan(v))


# ---------------------------------------------------------------- SPEC §2 scenario cuts
def make_cut(src_direct, src_multi, pair, chan):
    def cut(s, c):
        x = src_direct.get(s, 0.0) if c in DIRECT_CH else src_multi.get(s, 0.0)
        if (s, c) in pair:
            x = pair[(s, c)]
        y = chan.get(c, 0.0)
        return float(np.clip(1 - (1 - x) * (1 - y), -1, 1))
    return cut


US = "United States"  # the presets table writes "US" (a.2)
US_PAIRS = {(US, "WHO"): 1.0, (US, "Gavi"): 1.0, (US, "UNFPA"): 1.0, (US, "Global Fund"): 0.23}
OECD = {US: 0.57, "Germany": 0.174, "France": 0.109, "United Kingdom": 0.108, "Japan": 0.056}
cut_full_us_exit = make_cut({US: 1.0}, {}, US_PAIRS, {})
cut_oecd = make_cut(OECD, OECD, {}, {})

SUDDEN = [1.0] * YEARS
LINEAR = [(t + 1) / 5 for t in range(YEARS)]  # SPEC §2 funding path table
CASES = {
    1: dict(cut=cut_full_us_exit, path=SUDDEN, gov="none"),
    2: dict(cut=cut_full_us_exit, path=SUDDEN, gov="custom", theta=0.25, cap=True, alloc="pro_rata"),
    3: dict(cut=cut_oecd, path=SUDDEN, gov="none"),
    4: dict(cut=cut_full_us_exit, path=LINEAR, gov="none"),
}


# ---------------------------------------------------------------- SPEC §3 effective money by line
def known_lines(b):
    cfg = BUCKETS[b]
    return cfg["direct"] + ([cfg["care"]] if cfg["care"] else [])


GLOBAL_BASE = DAH.groupby("line").usd.sum().to_dict()  # for the global mix (sum over all countries)


def mix_for(base, lines):
    """Share of each line in `lines`, from the country's baseline; the global mix if the country's sum is 0."""
    tot = sum(base.get(l, 0.0) for l in lines)
    src = base if tot > 0 else GLOBAL_BASE
    tot = sum(src.get(l, 0.0) for l in lines)
    return {l: (src.get(l, 0.0) / tot if tot > 0 else 0.0) for l in lines}


# median of the countries' unspecified-money shares, renormalised (fallback when a country's share is missing)
MEDIAN_SHARES = {}
for _d in ("hiv", "tb", "malaria"):
    _m = CI[[f"unspec_{_d}_{p}" for p in SHARE_PURPOSES]].median()
    MEDIAN_SHARES[_d] = {p: float(_m[f"unspec_{_d}_{p}"] / _m.sum()) for p in SHARE_PURPOSES}


def unspec_shares(r):
    out = {}
    for b, cfg in BUCKETS.items():
        d = cfg["shares"]
        if d is None:
            out[b] = None
            continue
        sh = {p: nz(r[f"unspec_{d}_{p}"]) for p in SHARE_PURPOSES}
        if any(isnan(v) for v in sh.values()):
            sh = dict(MEDIAN_SHARES[d])
        out[b] = sh
    return out


def effective(X, base, shares):
    """X: line -> money (baseline or a year's G). Returns (E for direct lines and hiv_care_ct, nonservice dict).

    nonservice has a key "care" (nonservice[care]) and one key per bucket (nonservice[b])."""
    k = P["hss_kappa"]
    sigma = P["hss_service_share"]
    E, ns = {}, {}
    for b, cfg in BUCKETS.items():
        K = known_lines(b)
        mix = mix_for(base, K)
        U = X.get(cfg["unspec"], 0.0) if cfg["unspec"] else 0.0
        S = X.get(cfg["hss"], 0.0) if cfg["hss"] else 0.0
        sh = shares[b]
        add = {l: 0.0 for l in K}
        Sp = S + (U * sh["rssh"] if sh else 0.0)                  # S' = S + U x s_rssh
        for l in K:
            add[l] += sigma * Sp * mix[l]                         # systems money converted (sigma, central 0)
        if sh:
            mixT = mix_for(base, cfg["treat"])
            for l in cfg["treat"]:
                add[l] += U * sh["treatment"] * mixT[l]
            if cfg["prev"]:
                mixP = mix_for(base, cfg["prev"])
                for l in cfg["prev"]:
                    add[l] += U * sh["prevention"] * mixP[l]
            if cfg["care"]:
                add[cfg["care"]] += U * sh["testing"]              # HIV: add[care] += U x s_test
            else:
                add[cfg["test"]] += k * U * sh["testing"]          # TB, malaria: kappa x U x s_test to the target
        for l in cfg["direct"]:
            E[l] = X.get(l, 0.0) + add[l]
        if cfg["care"]:
            c = cfg["care"]
            pool = X.get(c, 0.0) + add[c]
            E[c] = k * pool
            ns["care"] = (1 - k) * pool
        nsb = (1 - sigma) * Sp
        if sh:
            nsb += U * sh["pm"]
            if not cfg["prev"]:
                nsb += U * sh["prevention"]
            if not cfg["care"]:
                nsb += (1 - k) * U * sh["testing"]
        ns[b] = nsb
    return E, ns


# ---------------------------------------------------------------- SPEC §5 unit costs
def ucr_value(kind, key):
    v = UCR[(UCR.kind == kind) & (UCR.key == key)]
    return (float(v.value.iloc[0]), v.cost_year.iloc[0]) if len(v) else (np.nan, np.nan)


def unit_costs(r, iso):
    markup = 1 / (1 - P["asd_share"])
    gdp = nz(r["gdp_pc"], 1000.0)
    sc = (max(gdp, 200) / 1000) ** P["uc_scale_elast"]
    m = P["uc_art_mult"]
    acf = nz(r["art_cost_full"])
    if not isnan(acf):
        if m <= 1:
            art = acf * m
        else:
            hi = float(np.clip(nz(r["art_cost_full_hi"], acf), acf, 600))
            art = acf * (1 + (m - 1) * (hi / acf - 1) / 0.38)
    else:  # a.8
        site = nz(r["art_site_cost"])
        if isnan(site):
            v, yr = ucr_value("art_site_cost", iso)
            if not isnan(v):
                site = v * cpi_to_2023(yr)
            else:
                site = (ucr_value("art_site_default", "arv")[0] + ucr_value("art_site_default", "non_arv")[0] * sc) \
                    * cpi_to_2023(2018)
        art = site * m * markup
    uc = {"hiv_art": art, "hiv_pmtct": P["uc_pmtct"], "hiv_ovc": P["uc_ovc"]}
    pop = nz(r["sp_pop_totl"])
    ninf = nz(r["sh_hiv_incd_tl"])
    inc = ninf / pop * 1000 if (not isnan(pop) and pop > 0 and not isnan(ninf)) else np.nan
    inc = 0.3 if isnan(inc) else float(np.clip(inc, 0.05, 10))
    uc["hiv_prev"] = P["cpia_ref"] * (1 / inc) ** 0.5
    ig = r["income_group"]
    if not isinstance(ig, str):  # missing group: guessed from GDP per person (a.9)
        ig = "low_income" if gdp < 1150 else ("lower_middle_income" if gdp < 4500 else "upper_middle_income")
    if ig not in ("low_income", "lower_middle_income"):
        ig = "upper_middle_income"
    for l, col in (("tb_ds", "tb_ds_cost"), ("tb_dr", "tb_dr_cost")):
        v = nz(r[col])
        if isnan(v):
            v = ucr_value(col, ig)[0]
        uc[l] = v * P["uc_tb_mult"] * markup
    uc.update(mal_itn=P["uc_itn"], mal_irs=P["uc_irs"], mal_cm=P["uc_mal_cm"], imm=P["uc_imm"])
    return uc, inc


# ---------------------------------------------------------------- SPEC §5 need and coverage
def epi(r, Eb, uc):
    art = nz(r["sh_hiv_artc_zs"]) / 100
    pm = nz(r["sh_hiv_pmtc_zs"]) / 100
    if isnan(pm):
        pm = art
    tbinc = nz(r["all_forms_of_tb_incidence_estimated"])
    rr_share = nz(r["tb_rr_share"], DR_TB_SHARE)
    rr_cov = nz(r["tb_rr_cov"], DR_TB_COV)
    par = nz(r["malaria_pop_at_risk"])
    itn = nz(r["mal_itn_cov"])
    if isnan(itn):
        itn = P["mal_itn_default_use"]
    irs_map = nz(r["mal_irs_cov"])
    if isnan(par) or par <= 0:
        irs = irs_map  # PAR missing or 0: implied not computed; mal_irs_cov (NaN if missing)
    else:
        implied = float(np.clip((Eb["mal_irs"] / uc["mal_irs"]) / par, 0, 1))
        irs = implied if (isnan(irs_map) or implied > irs_map) else irs_map
    cm = nz(r["mal_cm_cov"])
    if isnan(cm):
        cm = P["mal_cm_default_cov"]
    need = {"hiv_art": nz(r["plhiv"]), "hiv_pmtct": nz(r["hiv_pos_pregnancies"]), "tb_ds": tbinc,
            "tb_dr": rr_share * tbinc, "mal_itn": par, "mal_irs": par, "mal_cm": nz(r["malaria_cases"]),
            "imm": nz(r["births"]), "hiv_prev": np.nan, "hiv_ovc": np.nan}
    tbdet = nz(r["sh_tbs_dtec_zs"])
    if not isnan(tbdet):
        tbdet = min(tbdet, 100.0)  # TB detection % capped at 100 (SPEC §1)
    cov = {"hiv_art": art, "hiv_pmtct": pm, "tb_ds": tbdet / 100, "tb_dr": rr_cov,
           "mal_itn": itn, "mal_irs": irs, "mal_cm": cm, "imm": nz(r["sh_imm_idpt"]) / 100,
           "hiv_prev": np.nan, "hiv_ovc": np.nan}
    covered = {l: cov[l] * need[l] for l in need}
    if isnan(art) or isnan(need["hiv_art"]):
        covered["hiv_art"] = np.nan
    else:
        pm_women = pm * need["hiv_pmtct"]
        covered["hiv_art"] = max(art * need["hiv_art"] - (0.0 if isnan(pm_women) else pm_women), 0.0)  # a.10
    return need, cov, covered


def donor_shares(r, Eb, uc, covered):
    """d by direct line (SPEC §5 donor-funded pool), clipped to 0-1; 1 if missing."""
    d = {}
    for l in UNIT_LINES:
        b = LINE_BUCKET[l]
        if b == "Malaria":
            v = nz(r[f"donor_share_{l}"])
            if isnan(v):
                v = nz(r["donor_share_malaria_prev"]) if l in ("mal_itn", "mal_irs") else nz(r["donor_share_malaria"])
        else:
            v = nz(r[BUCKETS[b]["donor"]])
        d[l] = 1.0 if isnan(v) else float(np.clip(v, 0, 1))
    return d


# ---------------------------------------------------------------- SPEC §6 curves
def weib_F(x):
    lam = P["hiv_survival_median"] / math.log(2) ** (1 / WEIBULL_SHAPE)
    return 1 - math.exp(-((max(x, 0) / lam) ** WEIBULL_SHAPE))


def run(iso, case, art_reengage=None):
    """art_reengage: override for the further-deaths range (SPEC §6 Totals, L-33); None = central."""
    legacy_art = P["hiv_legacy_art_params"] == 1
    cfg = CASES[case]
    r = CI.loc[iso]
    rows = DAH[DAH.iso3 == iso].copy()
    rows["cut"] = [cfg["cut"](s, c) for s, c in zip(rows.src_grp, rows.chan_grp)]
    base = rows.groupby("line").usd.sum().to_dict()
    shares = unspec_shares(r)
    Eb, _ = effective(base, base, shares)
    path = cfg["path"]

    # SPEC §2 gross loss by line and year (gains set to 0)
    G = []
    for t in range(YEARS):
        g = (rows.usd * rows.cut * path[t]).groupby(rows.line).sum().to_dict()
        G.append({l: max(v, 0.0) for l, v in g.items()})
    L = np.array([sum(g.values()) for g in G])

    # SPEC §6 duration: first year with any non-zero cut in force on any row
    nonzero = [t for t in range(YEARS) if (rows.cut * path[t] != 0).any()]
    first = nonzero[0] if nonzero else 0  # a.12
    dur = [t - first if t >= first else 0 for t in range(YEARS)]

    # SPEC §4 government response
    g_med = nz(r["ghes_growth_median"], 0.0)
    g_top = nz(r["ghes_growth_p75"], 0.0)
    surge = max(0.0, g_top - max(g_med, 0.0))
    stress = float(np.clip(1 - (float(r["interest_pct_revenue"]) - 10) / 40, 0.25, 1))
    ghes = nz(r["ghes_2023"])
    capacity = 0.0 if isnan(ghes) else ghes * surge * stress
    E, N, budget, ns_list, repl_list = [], [], [], [], []
    for t in range(YEARS):
        e, ns = effective(G[t], base, shares)
        if cfg["gov"] == "custom":
            want = cfg["theta"] * L[t]
            R = min(want, capacity) if cfg.get("cap") else want
        elif cfg["gov"] == "max":
            R = min(L[t], capacity)
        else:  # none / gradual (gradual adds gov_add_t, not used in these cases)
            R = 0.0
        gov_add = 0.0
        B = min(R + gov_add, L[t])
        # pro rata over positive money-line losses and positive nonservice amounts (each a separate amount)
        amounts = {**{("E", l): v for l, v in e.items()}, **{("ns", k): v for k, v in ns.items()}}
        denom = sum(v for v in amounts.values() if v > 0)
        repl = {key: (B * v / denom if (v > 0 and denom > 0) else 0.0) for key, v in amounts.items()}
        E.append(e); ns_list.append(ns); budget.append(B); repl_list.append(repl)
        N.append({l: e[l] - repl[("E", l)] for l in e})
    budget = np.array(budget)

    # SPEC §5 units lost
    uc, inc = unit_costs(r, iso)
    need, cov, covered = epi(r, Eb, uc)
    dshare = donor_shares(r, Eb, uc, covered)
    cont = P["continuity"]
    units = {l: np.zeros(YEARS) for l in UNIT_LINES}
    for t in range(YEARS):
        for l in UNIT_LINES:
            if l == "hiv_art":
                n = N[t]["hiv_art"] + N[t]["hiv_care_ct"]
                b = Eb["hiv_art"] + Eb["hiv_care_ct"]
                tb = Eb["hiv_art"]
            else:
                n, b, tb = N[t][l], Eb[l], Eb[l]
            c = covered[l]
            if isnan(c):
                raw = n / uc[l]
            else:
                pool = c * dshare[l]
                if tb / uc[l] > pool:
                    raw = pool * n / b if b > 0 else 0.0
                else:
                    raw = n / uc[l]
            u = raw * (1 - cont)
            if not isnan(need[l]) and not isnan(cov[l]):
                cap = covered["hiv_art"] if l == "hiv_art" else cov[l] * need[l]
                u = min(u, cap)
            units[l][t] = max(u, 0.0)

    # ---------------- SPEC §6 deaths; 10-year arrays (index 0..4 = 2026-30, 5..9 = 2031-35)
    D = {l: np.zeros(T_ALL) for l in OUT_LINES}
    INF = {l: np.zeros(T_ALL) for l in HIV_LINES}
    art_pct = nz(r["sh_hiv_artc_zs"])
    a = 0.0 if isnan(art_pct) else art_pct / 100
    tr_u5 = nz(r["trend_u5mr"], -0.009) if TRENDS else 0.0
    tr_mal = nz(r["trend_malaria_deaths"], -0.009) if TRENDS else 0.0
    f_u5 = [(1 + tr_u5) ** t for t in range(YEARS)]
    f_mal = [(1 + tr_mal) ** t for t in range(YEARS)]

    # PMTCT
    lvl_pmtct = P["pmtct_vt_reduction"] * P["pmtct_infant_mort"]
    for t in range(YEARS):
        D["hiv_pmtct"][t] = units["hiv_pmtct"][t] * lvl_pmtct * LAG["hiv_pmtct"][dur[t]]
    INF["hiv_pmtct"][:YEARS] = units["hiv_pmtct"] * P["pmtct_vt_reduction"]

    # TB treatment
    h = nz(r["tb_hiv_share"], 0.0)
    cfr_u_pos = P["tb_cfr_untreated_pos"] * (1 - a) + P["tb_cfr_untreated_pos_art"] * a
    dcfr = (1 - h) * (P["tb_cfr_untreated_neg"] - P["tb_cfr_treated_neg"]) + \
        h * (cfr_u_pos - P["tb_cfr_treated_pos"] * (1 - 0.3 * a))
    for t in range(YEARS):
        D["tb_ds"][t] = units["tb_ds"][t] * dcfr * LAG["tb_ds"][dur[t]]
        D["tb_dr"][t] = units["tb_dr"][t] * P["tb_dr_dcfr"] * LAG["tb_dr"][dur[t]]
    # TB spread: secondary cases from each line's lost patients, arriving in s+1 and s+2, die at the arrival year's
    # coverage; arrivals 2031-2032 count in further deaths (part "tb")
    cfr_u = (1 - h) * P["tb_cfr_untreated_neg"] + h * cfr_u_pos
    cfr_t = (1 - h) * P["tb_cfr_treated_neg"] + h * P["tb_cfr_treated_pos"] * (1 - 0.3 * a)
    if isnan(need["tb_ds"]) or isnan(cov["tb_ds"]) or need["tb_ds"] <= 0:
        ctb = np.zeros(YEARS)
    else:
        ctb = np.clip(cov["tb_ds"] - units["tb_ds"] / need["tb_ds"], 0, 1)
    for s in range(YEARS):
        for l in ("tb_ds", "tb_dr"):
            sec = units[l][s] * P["tb_secondary"]
            for lag in (1, 2):
                t = s + lag
                c = ctb[min(t, YEARS - 1)]  # c at the arrival year; c_4 after 2030 (a.13)
                D[l][t] += 0.5 * sec * (c * cfr_t + (1 - c) * cfr_u)

    # Vaccines (SPEC §6, Batch 5+6 V2): per-child deaths by years since vaccination
    dpc0 = nz(r["imm_dpc"])
    if P["imm_legacy_u5mr_scaling"] != 1 and not isnan(dpc0):
        dpc = [nz(r[f"imm_dpc_lag{k}"], 0.0) for k in range(10)]
        m = P["imm_dpc_mult"]
        lo, hi = nz(r["imm_dpc_lo"]) / dpc0, nz(r["imm_dpc_hi"]) / dpc0
        factor = 1 - (1 - m) * (1 - lo) / (1 - 0.56) if m < 1 else 1 + (m - 1) * (hi - 1) / (1.64 - 1)
        for s in range(YEARS):
            for k in range(10):
                t = s + k
                if t < T_ALL:  # lags after 2035 are not counted
                    D["imm"][t] += units["imm"][s] * dpc[k] * factor
    else:  # legacy rule
        u5 = nz(r["sh_dyn_mort"], 50.0)
        level = [P["imm_deaths_per_child_ref"] * P["imm_u5_share"] * float(np.clip(u5 * f_u5[t] / 50, 0.3, 2.5))
                 for t in range(YEARS)]
        for s in range(YEARS):
            for k, w in enumerate(IMM_W_LEGACY):
                t = s + k
                lv = level[t] if t < YEARS else level[YEARS - 1] * (1 + tr_u5) ** (t - (YEARS - 1))
                D["imm"][t] += units["imm"][s] * w * lv

    # Malaria (LiST form)
    D0 = nz(r["malaria_deaths"])
    s_u5 = np.nan
    if not isnan(D0) and D0 > 0:
        if P["mal_u5_use_country_series"] == 1:  # sensitivity switch: the old country-series rule
            child = nz(r["malaria_deaths_in_children_1_59_months_total_deaths"])
            if isnan(child):
                s_u5 = 0.76 if str(r["is_ssa"]).strip().lower() == "true" else 0.40
            else:
                s_u5 = float(np.clip(child / D0, 0, 1))
        else:  # WMR 2025 regional share named in malaria_u5_share_param; none -> 0 (a.14)
            pname = r["malaria_u5_share_param"]
            s_u5 = P[pname] if (isinstance(pname, str) and pname in P) else 0.0
        fa = P["mal_adult_effect_frac"]
        groups = [(D0 * s_u5, P["mal_vc_eff"], P["mal_cm_eff"]),
                  (D0 * (1 - s_u5), P["mal_vc_eff"] * fa, P["mal_cm_eff"] * fa)]
        par, cases = need["mal_itn"], need["mal_cm"]
        n0 = cov["mal_itn"]
        r0 = 0.0 if isnan(cov["mal_irs"]) else cov["mal_irs"]
        m0 = cov["mal_cm"]
        par_ok = not isnan(par) and par > 0
        cases_ok = not isnan(cases) and cases > 0
        vc = lambda i, rr: 1 - (1 - i) * (1 - rr)
        cv0 = vc(n0, r0)
        for t in range(YEARS):
            n1 = float(np.clip(n0 - (units["mal_itn"][t] / par if par_ok else 0.0), 0, 1))
            r1 = float(np.clip(r0 - (units["mal_irs"][t] / par if par_ok else 0.0), 0, 1))
            m1 = float(np.clip(m0 - (units["mal_cm"][t] / cases if cases_ok else 0.0), 0, 1))
            cv1 = vc(n1, r1)
            total = dv = dc = 0.0
            for Dg, Ev, Ec in groups:
                rv = (1 - Ev * cv1) / (1 - Ev * cv0)
                rc = (1 - Ec * m1) / (1 - Ec * m0)
                total += Dg * (rv * rc - 1)
                dv += Dg * (rv - 1)
                dc += Dg * (rc - 1)
            dv, dc = abs(dv), abs(dc)
            den = dv + dc if (dv + dc) != 0 else 1.0
            vpart, cpart = total * dv / den, total * dc / den
            fi, fr = cv0 - vc(n1, r0), cv0 - vc(n0, r1)
            wi = 0.5 if (fi == 0 and fr == 0) else fi / (fi + fr)
            res = (1 + P["mal_resurgence"]) ** dur[t]
            D["mal_itn"][t] = vpart * wi * LAG["mal_itn"][dur[t]] * f_mal[t] * res
            D["mal_irs"][t] = vpart * (1 - wi) * LAG["mal_irs"][dur[t]] * f_mal[t] * res
            D["mal_cm"][t] = cpart * f_mal[t]

    # HIV treatment cohorts (SPEC §6, Batch 2): each cohort = [size, age]
    if legacy_art:
        hz = [P["art_hazard_mult"] * x for x in ART_HAZARD_LEGACY]
        H = 5
        r_tr = P["art_transmission"]
        reengage = ART_REENGAGE_LEGACY if art_reengage is None else art_reengage
    else:
        hz = [P["art_hazard_mult"] * x for x in ART_HAZARD]
        H = 10
        r_tr = P["art_transmission_mult"] * nz(r["art_transmission_rate"], ART_TRANSMISSION_FALLBACK)
        reengage = P["art_reengage"] if art_reengage is None else art_reengage
    cohorts = []
    prev = 0.0
    first_gen = np.zeros(T_ALL)
    for t in range(YEARS):
        stock = units["hiv_art"][t]
        delta = max(stock, 0.0) - max(prev, 0.0)
        if delta > 0:
            cohorts.append([delta, 1])
        elif delta < 0:
            drop = -delta
            for c in reversed(cohorts):  # most recent cohorts leave first
                take = min(c[0], drop); c[0] -= take; drop -= take
                if drop <= 0:
                    break
        prev = stock
        dth = inf = 0.0
        for sz, age in cohorts:
            dth += sz * hz[min(age, H) - 1]
            inf += sz * r_tr * ART_INFECT_LAG[min(age, 5) - 1]
        if stock < 0:  # negative stock (gains only) -- cannot occur here as units >= 0
            dth += stock * hz[min(t + 1, H) - 1]
            inf += stock * r_tr * ART_INFECT_LAG[min(t, 4)]
        D["hiv_art"][t] = dth
        first_gen[t] = inf
        for c in cohorts:
            c[1] += 1  # age_at_end_2030 is the age after the 2030 increment (a.11)
    off = np.zeros(T_ALL)
    off[:YEARS] = units["hiv_art"]
    for k in range(POST_YEARS):
        t = YEARS + k
        frac = (1 - reengage) ** (k + 0.5)
        dth = inf = still = 0.0
        for sz, age_end in cohorts:
            people = sz * frac
            aa = min(age_end + k, H)
            dth += people * hz[aa - 1]
            inf += people * r_tr * ART_INFECT_LAG[min(aa, 5) - 1]
            still += people
        D["hiv_art"][t] = dth
        first_gen[t] = inf
        off[t] = still
    INF["hiv_art"][:] = first_gen
    # Second generation (unless legacy): each first-generation infection is unsuppressed for an exponential time
    # with mean D and transmits at r; no third generation
    if not legacy_art:
        Dm = P["hiv_new_inf_unsup_years"]
        Fexp = lambda x: Dm * (1 - math.exp(-max(x, 0) / Dm))
        w = [Fexp(k + 0.5) - Fexp(k - 0.5) for k in range(T_ALL)]
        for t in range(T_ALL):
            INF["hiv_art"][t] += sum(first_gen[s] * w[t - s] * r_tr for s in range(t + 1))
    INF["hiv_prev"][:YEARS] = units["hiv_prev"]

    # Deaths from new infections (off-ART and prevention; PMTCT infant infections not run through the curve)
    plhiv = need["hiv_art"]
    if isnan(plhiv) or isnan(art_pct) or plhiv <= 0:
        cart = np.zeros(T_ALL)
    else:
        cart = np.clip(art_pct / 100 - off / plhiv, 0, 1)
    inf_deaths = {src: np.zeros(T_ALL) for src in ("hiv_art", "hiv_prev")}
    for src in ("hiv_art", "hiv_prev"):
        for t in range(T_ALL):
            risk = cart[t] * P["hiv_inf_death_treated"] + (1 - cart[t]) * P["hiv_inf_death_untreated"]
            tot = 0.0
            for s in range(t + 1):
                tot += INF[src][s] * (weib_F(t - s + 0.5) - weib_F(t - s - 0.5))
            inf_deaths[src][t] = tot * risk
            D[src][t] += inf_deaths[src][t]

    # ---------------- output
    out = {"key": f"{iso}|{case}", "T.base": sum(base.values()), "T.gross": L.mean(), "T.replaced": budget.mean(),
           "T.net": (L - budget).mean()}
    out["T.deaths_5y"] = sum(D[l][:YEARS].sum() for l in OUT_LINES)  # hiv_ovc has no deaths
    # further deaths 2031-2035 = parts hiv_art (cohorts), hiv_infections (off-ART and prevention), imm, tb
    parts = {"hiv_art": D["hiv_art"][YEARS:].sum() - inf_deaths["hiv_art"][YEARS:].sum(),
             "hiv_infections": inf_deaths["hiv_art"][YEARS:].sum() + inf_deaths["hiv_prev"][YEARS:].sum(),
             "imm": D["imm"][YEARS:].sum(), "tb": D["tb_ds"][YEARS:].sum() + D["tb_dr"][YEARS:].sum()}
    out["C.after_2030"] = sum(parts.values())
    for l in OUT_LINES:
        p = f"L.{l}."
        out[p + "base_usd"] = Eb[l]
        out[p + "gross_loss_usd"] = np.mean([E[t][l] for t in range(YEARS)])
        out[p + "net_loss_usd"] = np.mean([N[t][l] for t in range(YEARS)])
        out[p + "unit_cost"] = uc[l]
        out[p + "need"] = need[l]
        out[p + "cov0"] = cov[l]
        out[p + "units_lost"] = units[l].mean()
        out[p + "cov_drop_pp"] = units[l].mean() / need[l] * 100 if (not isnan(need[l]) and need[l] > 0) else np.nan
        out[p + "deaths_5y"] = D[l][:YEARS].sum()
        out[p + "infections_5y"] = INF[l][:YEARS].sum() if l in HIV_LINES else np.nan
    for b, c in BUCKETS.items():  # SPEC §7: bucket deaths = sum over its direct lines
        out[f"B.{b}.deaths_5y"] = sum(D[l][:YEARS].sum() for l in c["direct"] if l in D)
    diag = dict(capacity=capacity, first=first, care_eb=Eb["hiv_care_ct"],
                care_gross=np.mean([E[t]["hiv_care_ct"] for t in range(YEARS)]),
                inc_per_1000=inc, art_covered=covered["hiv_art"], art_cost=uc["hiv_art"],
                conservation=max(abs(sum(E[t].values()) + sum(ns_list[t].values()) - L[t]) for t in range(YEARS)),
                after_2030_parts={k: round(v, 1) for k, v in parts.items()},
                inf_after2030=INF["hiv_art"][YEARS:].sum(), mal_u5_share=s_u5, irs_cov=cov["mal_irs"])
    return out, diag


if __name__ == "__main__":
    res, diags = [], {}
    for iso in ["KEN", "NGA", "IND", "HND", "MOZ"]:
        for case in CASES:
            o, d = run(iso, case)
            # SPEC §6 Totals (L-33): further deaths with art_reengage at its high value (fewest deaths) and
            # its low value (most deaths), every other parameter central
            o["C.after_2030_reengage_min"] = run(iso, case, art_reengage=P_HIGH["art_reengage"])[0]["C.after_2030"]
            o["C.after_2030_reengage_max"] = run(iso, case, art_reengage=P_LOW["art_reengage"])[0]["C.after_2030"]
            res.append(o); diags[o["key"]] = d
    df = pd.DataFrame(res)
    df.to_csv(f"{OUT}/independent.csv", index=False)
    pd.set_option("display.width", 250)
    print(df[["key", "T.base", "T.gross", "T.replaced", "T.net", "T.deaths_5y", "C.after_2030",
              "C.after_2030_reengage_min", "C.after_2030_reengage_max"]].round(0).to_string())
    for k, d in diags.items():
        print(k, {kk: (round(v, 3) if isinstance(v, float) else v) for kk, v in d.items()})
