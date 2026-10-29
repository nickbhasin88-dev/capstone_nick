"""Independent recomputation of the funding-cut model from audit/METHOD.md only.

Run from the repo root:  .venv/bin/python audit/recompute.py
Writes audit/recompute_results.csv (long format).
"""
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "audit" / "recompute_results.csv"

COUNTRIES = ["KEN", "NGA", "HND", "IRQ", "MOZ"]
SCENARIOS = ["Full US exit", "America First MOUs"]
RESPONSES = {"none": 0.0, "custom25": 0.25}

BUCKET_LINES = {
    "HIV": ["hiv_art", "hiv_care_ct", "hiv_pmtct", "hiv_prev", "hiv_ovc", "hiv_unspec", "hiv_hss"],
    "TB": ["tb_ds", "tb_dr", "tb_unspec", "tb_hss"],
    "Malaria": ["mal_itn", "mal_irs", "mal_cm", "mal_unspec", "mal_hss"],
    "Immunization": ["imm"],
}
ALL_LINES = [l for ls in BUCKET_LINES.values() for l in ls]
DIRECT = ["hiv_art", "hiv_pmtct", "hiv_prev", "hiv_ovc", "tb_ds", "tb_dr",
          "mal_itn", "mal_irs", "mal_cm", "imm"]
BUCKET_DIRECT = {b: [l for l in ls if l in DIRECT] for b, ls in BUCKET_LINES.items()}
LINE_BUCKET = {l: b for b, ls in BUCKET_LINES.items() for l in ls}
CARE = "hiv_care_ct"            # METHOD.md (I-09): no units; kappa x its pool counts toward hiv_art
DIRECT_CHANNELS = {"Bilateral agency", "NGOs", "Gates direct", "Other"}

US = "United States"
US_PAIRS = {(US, "WHO"): 1.0, (US, "Gavi"): 1.0, (US, "UNFPA"): 1.0, (US, "Global Fund"): 0.23}

RAMP = {
    "hiv_pmtct": [0.6, 1, 1, 1, 1],
    "tb_ds": [0.7, 1, 1, 1, 1], "tb_dr": [0.7, 1, 1, 1, 1],
    "mal_itn": [0.5, 1, 1, 1, 1], "mal_irs": [0.8, 1, 1, 1, 1], "mal_cm": [1, 1, 1, 1, 1],
}
ART_HAZ_BASE = [0.012, 0.028, 0.038, 0.045, 0.05]
IMM_W = [0.40, 0.35, 0.20, 0.05]
CPI2018 = 304.702 / 251.107
CPI2020 = 304.702 / 258.811

# ---------------------------------------------------------------- data
dah = pd.read_csv(ROOT / "model_data" / "dah_lines.csv")
ci = pd.read_csv(ROOT / "model_data" / "country_inputs.csv").set_index("iso3")
P = pd.read_csv(ROOT / "model_params.csv").set_index("param")["central"].astype(float).to_dict()
ucr = pd.read_csv(ROOT / "unit_cost_reference.csv")


def num(v):
    """float or None for missing."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) else f


def g(iso, col):
    return num(ci.loc[iso, col]) if col in ci.columns else None


# ---------------------------------------------------------------- MOU direct cut
def mou_x(iso):
    ref = g(iso, "mou_us_ref")
    if ref is None or ref <= 0:
        return None
    for yr in (2028, 2027, 2026):
        v = g(iso, f"mou_us_{yr}")
        if v is not None:
            return float(np.clip(1 - v / ref, -0.5, 1))
    return None


_xs = [mou_x(i) for i in ci.index]
_xs = [x for x in _xs if x is not None]
MOU_DEFAULT = round(100 * float(np.mean(_xs))) / 100


def us_direct_cut(iso, scen):
    if scen == "Full US exit":
        return 1.0
    x = mou_x(iso)
    return MOU_DEFAULT if x is None else x


def row_cut(iso, scen, src, chan, line=None):
    if isinstance(scen, tuple):                      # ("uniform", bucket, cut): the per-US$1M cards (I-04)
        return scen[2] if LINE_BUCKET.get(line) == scen[1] else 0.0
    if src != US:
        x = 0.0
    else:
        x = us_direct_cut(iso, scen) if chan in DIRECT_CHANNELS else 0.0
        if (src, chan) in US_PAIRS:
            x = US_PAIRS[(src, chan)]
    y = 0.0
    return 1 - (1 - x) * (1 - y)


# global mix (share of each direct line in the bucket's direct-line baseline, all countries)
_gl = dah.groupby("line")["usd"].sum()
GLOBAL_MIX = {}
for b, ls in BUCKET_DIRECT.items():
    ls = ls + ([CARE] if b == "HIV" else [])
    tot = sum(_gl.get(l, 0.0) for l in ls)
    for l in ls:
        GLOBAL_MIX[l] = _gl.get(l, 0.0) / tot if tot else 1 / len(ls)


def effective(amounts, base):
    """Fold unspec + kappa*hss into the direct lines using base mix."""
    k = P["hss_kappa"]
    eff, nonserv = {}, {}
    for b, dls in BUCKET_DIRECT.items():
        known = dls + ([CARE] if b == "HIV" else [])
        bsum = sum(base[l] for l in known)
        unspec = amounts.get(f"{b_prefix(b)}_unspec", 0.0) if b != "Immunization" else 0.0
        hss = amounts.get(f"{b_prefix(b)}_hss", 0.0) if b != "Immunization" else 0.0
        mix = {l: (base[l] / bsum if bsum else GLOBAL_MIX[l]) for l in known}
        for l in dls:
            eff[l] = amounts[l] + (unspec + k * hss) * mix[l]
        m_c = 0.0
        if b == "HIV":                       # testing & care: kappa of its pool is service money, the rest is not
            pool = amounts[CARE] + (unspec + hss) * mix[CARE]
            eff[CARE], nonserv[CARE], m_c = k * pool, (1 - k) * pool, mix[CARE]
        if b != "Immunization":
            nonserv[b] = (1 - k) * hss * (1 - m_c)
    return eff, nonserv


def b_prefix(b):
    return {"HIV": "hiv", "TB": "tb", "Malaria": "mal"}[b]


# ---------------------------------------------------------------- unit costs
def unit_costs(iso):
    markup = 1 / (1 - P["asd_share"])
    gdp = g(iso, "gdp_pc") or 1000.0
    sc = (max(gdp, 200) / 1000) ** P["uc_scale_elast"]
    site = ucr[(ucr.kind == "art_site_cost") & (ucr.key == iso)]
    if len(site):
        r = site.iloc[0]
        f = CPI2018 if int(r.cost_year) == 2018 else CPI2020 if int(r.cost_year) == 2020 else 1.0
        art = float(r.value) * f
    else:
        dflt = ucr[ucr.kind == "art_site_default"].set_index("key")["value"].astype(float)
        art = (dflt["arv"] + dflt["non_arv"] * sc) * CPI2018
    c = {"hiv_art": art * P["uc_art_mult"] * markup,
         "hiv_pmtct": P["uc_pmtct"], "hiv_ovc": P["uc_ovc"]}
    inc_n, pop = g(iso, "sh_hiv_incd_tl"), g(iso, "sp_pop_totl")
    inc = 0.3 if (inc_n is None or not pop) else float(np.clip(inc_n / pop * 1000, 0.05, 10))
    c["hiv_prev"] = P["cpia_ref"] * (1 / inc) ** 0.5
    ig = ci.loc[iso, "income_group"]
    ig = ig if ig in ("low_income", "lower_middle_income") else "upper_middle_income"
    tbt = ucr[ucr.key == ig].set_index("kind")["value"].astype(float)
    c["tb_ds"] = tbt["tb_ds_cost"] * P["uc_tb_mult"] * markup
    c["tb_dr"] = tbt["tb_dr_cost"] * P["uc_tb_mult"] * markup
    c["mal_itn"], c["mal_irs"] = P["uc_itn"], P["uc_irs"]
    c["mal_cm"], c["imm"] = P["uc_mal_cm"], P["uc_imm"]
    return c


def pct(v):
    return None if v is None else v / 100


def need_cov(iso):
    plhiv = g(iso, "plhiv")
    art = pct(g(iso, "sh_hiv_artc_zs"))
    pm = pct(g(iso, "sh_hiv_pmtc_zs"))
    tbi = g(iso, "all_forms_of_tb_incidence_estimated")
    par = g(iso, "malaria_pop_at_risk")
    # METHOD.md (I-11): MAP 2025 coverage columns built by malaria_inputs.py; defaults where missing. Spraying without a
    # MAP estimate is None here and set from donor IRS money in the run (people it pays for / people at risk).
    nets = g(iso, "mal_itn_cov")
    if nets is None:
        nets = P["mal_itn_default_use"]
    irs = g(iso, "mal_irs_cov")
    cm = g(iso, "mal_cm_cov")
    if cm is None:
        cm = P["mal_cm_default_cov"]
    return {
        "hiv_art": (plhiv, art),
        "hiv_pmtct": (g(iso, "hiv_pos_pregnancies"), pm if pm is not None else art),
        "tb_ds": (tbi, pct(g(iso, "sh_tbs_dtec_zs"))),
        "tb_dr": (None if tbi is None else 0.04 * tbi, 0.45),
        "mal_itn": (par, nets), "mal_irs": (par, irs),
        "mal_cm": (g(iso, "malaria_cases"), cm),
        "imm": (g(iso, "births"), pct(g(iso, "sh_imm_idpt"))),
        "hiv_prev": (None, None), "hiv_ovc": (None, None),
    }


# ---------------------------------------------------------------- lives helpers
def tb_dcfr_parts(iso):
    h = g(iso, "tb_hiv_share") or 0.0
    a = pct(g(iso, "sh_hiv_artc_zs")) or 0.0
    dcfr = ((1 - h) * (P["tb_cfr_untreated_neg"] - P["tb_cfr_treated_neg"])
            + h * (P["tb_cfr_untreated_pos"] - P["tb_cfr_treated_pos"]) * (1 - 0.3 * a))
    cu = (1 - h) * P["tb_cfr_untreated_neg"] + h * P["tb_cfr_untreated_pos"] * (1 - 0.3 * a)
    ct = (1 - h) * P["tb_cfr_treated_neg"] + h * P["tb_cfr_treated_pos"] * (1 - 0.3 * a)
    return dcfr, cu, ct


def imm_levels(iso, n=8):
    u5 = g(iso, "sh_dyn_mort")
    u5 = 50.0 if u5 is None else u5
    tr = g(iso, "trend_u5mr")
    tr = -0.009 if tr is None else tr
    lv = []
    for t in range(1, 6):
        u = u5 * (1 + tr) ** (t - 1)
        lv.append(P["imm_deaths_per_child_ref"] * P["imm_u5_share"] * float(np.clip(u / 50, 0.3, 2.5)))
    for t in range(6, n + 1):
        lv.append(lv[4] * (1 + tr) ** (t - 5))
    return lv  # index 0 = 2026


def malaria_split(iso, itn, irs, cm, irs0=None):
    """Returns (vector_total, treatment_total, itn_share_of_vector) annual base deaths, or zeros. Vector-control
    coverage = 1 - (1 - ITN use)(1 - IRS coverage); each falls by its own units lost / people at risk."""
    D0 = g(iso, "malaria_deaths")
    if not D0:
        return 0.0, 0.0, 0.5
    nc = need_cov(iso)
    par, n0 = nc["mal_itn"]
    r0 = irs0 if irs0 is not None else (nc["mal_irs"][1] or 0.0)
    cases, cc0 = nc["mal_cm"]
    Ev, Ec = P["mal_vc_eff"], P["mal_cm_eff"]
    n1 = float(np.clip(n0 - itn / par, 0, 1)) if par else n0
    r1 = float(np.clip(r0 - irs / par, 0, 1)) if par else r0
    vc = lambda a, b: 1 - (1 - a) * (1 - b)  # noqa: E731
    cv0, cv1 = vc(n0, r0), vc(n1, r1)
    cc1 = float(np.clip(cc0 - cm / cases, 0, 1)) if cases else cc0
    rv = (1 - Ev * cv1) / (1 - Ev * cv0)
    rc = (1 - Ec * cc1) / (1 - Ec * cc0)
    total = D0 * (rv * rc - 1)
    dv, dc = D0 * (rv - 1), D0 * (rc - 1)
    den = abs(dv) + abs(dc)
    if den == 0:
        return 0.0, 0.0, 0.5
    vec, trt = total * abs(dv) / den, total * abs(dc) / den
    d_itn, d_irs = cv0 - vc(n1, r0), cv0 - vc(n0, r1)
    s = 0.5 if (d_itn + d_irs) <= 0 else d_itn / (d_itn + d_irs)
    return vec, trt, s


def mal_trend(iso):
    tr = g(iso, "trend_malaria_deaths")
    return -0.009 if tr is None else tr


def weib_F(x):
    lam = P["hiv_survival_median"] / math.log(2) ** (1 / 2.25)
    return 1 - math.exp(-((max(x, 0) / lam) ** 2.25))


def hiv_frac(k):
    return weib_F(k + 0.5) - weib_F(k - 0.5)


# ---------------------------------------------------------------- one run
def run(iso, scen, resp_share):
    rows = []
    out = lambda line, metric, value: rows.append((iso, scen, resp, line, metric, value))
    resp = "none" if resp_share == 0 else "custom25"

    d = dah[dah.iso3 == iso].copy()
    d["cut"] = [row_cut(iso, scen, s, c, l) for s, c, l in zip(d.src_grp, d.chan_grp, d.line)]
    d["loss"] = d.usd * d.cut
    base = {l: float(d.loc[d.line == l, "usd"].sum()) for l in ALL_LINES}
    gross = {l: float(d.loc[d.line == l, "loss"].sum()) for l in ALL_LINES}
    G = sum(max(gross[l], 0) for l in ALL_LINES)
    baseline = sum(base.values())

    eff, nonserv = effective(gross, base)
    eff_base, _ = effective(base, base)

    # government response
    ghes = g(iso, "ghes_2023")
    gm = g(iso, "ghes_growth_median") or 0.0
    gp = g(iso, "ghes_growth_p75") or 0.0
    ir = g(iso, "interest_pct_revenue")          # METHOD.md (I-26): never missing
    stress = float(np.clip(1 - (ir - 10) / 40, 0.25, 1))
    cap = 0.0 if ghes is None else ghes * max(0.0, gp - max(gm, 0.0)) * stress
    R = min(resp_share * G, cap, G) if resp_share > 0 else 0.0
    pos = [v for v in eff.values() if v > 0] + [v for v in nonserv.values() if v > 0]
    S = sum(pos)
    repl = {l: (R * eff[l] / S if (eff[l] > 0 and S > 0) else 0.0) for l in DIRECT + [CARE]}
    net = {l: eff[l] - repl[l] for l in DIRECT + [CARE]}

    out("TOTAL", "aid_at_risk", G)
    out("TOTAL", "replaced", R)
    out("TOTAL", "net_loss", G - R)
    out("TOTAL", "baseline_aid", baseline)

    # units
    cost = unit_costs(iso)
    nc = need_cov(iso)
    cont = P["continuity"]
    units = {}
    par0 = nc["mal_irs"][0]
    irs_implied = None
    if par0:                                    # spraying = max(MAP coverage, what donor IRS money pays for)
        implied = min(eff_base["mal_irs"] / cost["mal_irs"] / par0, 1.0)
        if nc["mal_irs"][1] is None or implied > nc["mal_irs"][1]:
            irs_implied = implied
            nc["mal_irs"] = (par0, irs_implied)
    pm_need, pm_cov = nc["hiv_pmtct"]
    pm_covered = pm_need * pm_cov if (pm_need is not None and pm_cov is not None) else 0.0
    for l in DIRECT:
        need, cov = nc[l]
        covered = None if (need is None or cov is None) else cov * need
        if l == "hiv_art" and covered is not None:          # PMTCT women's ART is paid from PMTCT money (I-27)
            covered = max(covered - pm_covered, 0.0)
        n_l, b_l = net[l], eff_base[l]
        if l == "hiv_art":                                   # testing & care money counts toward ART (I-09)
            n_l, b_l = net[l] + net[CARE], eff_base[l] + eff_base[CARE]
        if covered is None:
            raw = n_l / cost[l]
        elif eff_base[l] / cost[l] > covered:                # judged on ART's own money
            raw = min(covered, eff_base[l] / cost[l]) * n_l / b_l
        else:
            raw = n_l / cost[l]
        u = raw * (1 - cont)
        if covered is not None:
            u = float(np.clip(u, -(1 - cov) * need, covered))
        units[l] = u
    # bednets and spraying are each capped at their own people covered (no shared pool since I-11)

    # ---- lives
    deaths = {l: [0.0] * 5 for l in DIRECT}
    after = {"hiv_art": 0.0, "hiv_infections": 0.0, "imm": 0.0, "tb": 0.0}

    # PMTCT
    for t in range(5):
        deaths["hiv_pmtct"][t] = units["hiv_pmtct"] * P["pmtct_vt_reduction"] * P["pmtct_infant_mort"] * RAMP["hiv_pmtct"][t]

    # TB
    dcfr, cfr_u, cfr_t = tb_dcfr_parts(iso)
    tbn, tbc = nc["tb_ds"]
    c_tb = float(np.clip(tbc - units["tb_ds"] / tbn, 0, 1)) if (tbn and tbc is not None) else 0.0
    p_die = c_tb * cfr_t + (1 - c_tb) * cfr_u
    arrivals = [0.0] * 7  # index 0 = 2026 ... 6 = 2032
    for s in range(5):
        deaths["tb_ds"][s] = units["tb_ds"] * dcfr * RAMP["tb_ds"][s]
        deaths["tb_dr"][s] = units["tb_dr"] * P["tb_dr_dcfr"] * RAMP["tb_dr"][s]
        sec = (units["tb_ds"] + units["tb_dr"]) * P["tb_secondary"]
        arrivals[s + 1] += sec / 2
        arrivals[s + 2] += sec / 2
    for t in range(1, 5):
        deaths["tb_ds"][t] += arrivals[t] * p_die
    after["tb"] = (arrivals[5] + arrivals[6]) * p_die

    # Immunization
    lv = imm_levels(iso, n=10)
    U_imm = units["imm"]
    for t in range(10):
        dt = sum(U_imm * IMM_W[t - s] * lv[t] for s in range(5) if 0 <= t - s < 4)
        if t < 5:
            deaths["imm"][t] = dt
        elif t < 10:
            after["imm"] += dt

    # Malaria
    vec, trt, s_itn = malaria_split(iso, units["mal_itn"], units["mal_irs"], units["mal_cm"], irs_implied)
    mtr = mal_trend(iso)
    for t in range(5):
        tf = (1 + mtr) ** t
        rb = (1 + P["mal_resurgence"]) ** t
        deaths["mal_itn"][t] = vec * s_itn * RAMP["mal_itn"][t] * tf * rb
        deaths["mal_irs"][t] = vec * (1 - s_itn) * RAMP["mal_irs"][t] * tf * rb
        deaths["mal_cm"][t] = trt * RAMP["mal_cm"][t] * tf

    # HIV treatment + infections
    U = units["hiv_art"]
    haz = [P["art_hazard_mult"] * h for h in ART_HAZ_BASE]
    plhiv, artc = nc["hiv_art"]
    artc = artc or 0.0
    for t in range(5):
        deaths["hiv_art"][t] = U * haz[t]
    off = [U] * 5 + [U * (1 - P["art_reengage"]) ** (k + 0.5) for k in range(5)]  # 2026..2035
    inf_art = [U * P["art_transmission"] * (0.5 if t == 0 else 1) for t in range(5)] + \
              [off[t] * P["art_transmission"] for t in range(5, 10)]
    inf_prev = [units["hiv_prev"]] * 5 + [0.0] * 5
    c_hiv = [float(np.clip(artc - off[t] / plhiv, 0, 1)) if plhiv else 0.0 for t in range(10)]
    pdie = [c * P["hiv_inf_death_treated"] + (1 - c) * P["hiv_inf_death_untreated"] for c in c_hiv]
    for t in range(10):
        da = sum(inf_art[s] * hiv_frac(t - s) for s in range(t + 1)) * pdie[t]
        dp = sum(inf_prev[s] * hiv_frac(t - s) for s in range(t + 1)) * pdie[t]
        if t < 5:
            deaths["hiv_art"][t] += da
            deaths["hiv_prev"][t] += dp
        else:
            after["hiv_infections"] += da + dp
    after["hiv_art"] = sum(off[t] * haz[4] for t in range(5, 10))

    infections_5y = sum(inf_art[:5]) + sum(inf_prev[:5]) + 5 * units["hiv_pmtct"] * P["pmtct_vt_reduction"]

    # ---- per-line output
    for l in DIRECT:
        need, cov = nc[l]
        out(l, "eff_loss", eff[l])
        out(l, "net_line", net[l])
        out(l, "units_lost", units[l])
        if need is not None and cov is not None:
            out(l, "cov_before", cov)
            out(l, "cov_after", cov - units[l] / need if need else np.nan)
        out(l, "deaths_y1", deaths[l][0])
        out(l, "deaths_5y", sum(deaths[l]))
    out("TOTAL", "deaths_y1", sum(deaths[l][0] for l in DIRECT))
    out("TOTAL", "deaths_5y", sum(sum(deaths[l]) for l in DIRECT))
    for k, v in after.items():
        out(f"after_{k}", "deaths", v)
    out("TOTAL", "after_2030_total", sum(after.values()))
    out("TOTAL", "hiv_infections_5y", infections_5y)

    # ---- cards (METHOD.md section 6, I-04): this same calculation for a US$1M-a-year uniform cut to one disease
    if not isinstance(scen, tuple):
        cards = {"HIV": "hiv_art", "TB": "tb_ds", "Malaria": "mal_itn", "Immunization": "imm"}
        for b, l in cards.items():
            bb = float(d.loc[d.line.map(LINE_BUCKET) == b, "usd"].sum())
            if bb <= 0:
                continue
            cut = min(1.0, 1e6 / bb)
            r = {(ln, m): v for _, _, _, ln, m, v in run(iso, ("uniform", b, cut), 0.0)}
            k = 1e6 / (cut * bb)
            dth = sum(r.get((x, "deaths_5y"), 0.0) for x in DIRECT if LINE_BUCKET[x] == b) * k
            people = r[(l, "units_lost")] * k
            need = nc[l][0]
            out(f"card_{b}", "people", people)
            out(f"card_{b}", "cov_drop_pp", people / need * 100 if need else np.nan)
            out(f"card_{b}", "deaths_5y", dth)
            out(f"card_{b}", "aid_per_death", 5e6 / dth if dth else np.nan)
    return rows


def main():
    rows = []
    for iso in COUNTRIES:
        for scen in SCENARIOS:
            for resp, share in RESPONSES.items():
                rows += run(iso, scen, share)
    df = pd.DataFrame(rows, columns=["iso3", "scenario", "response", "line", "metric", "value"])
    df.to_csv(OUT, index=False)
    print(f"MOU default x = {MOU_DEFAULT}")
    print(f"wrote {len(df)} rows to {OUT}")
    k = df[(df.iso3 == "KEN") & (df.scenario == "Full US exit") & (df.response == "none") & (df.line.isin(["TOTAL"]))]
    print(k.to_string(index=False))


if __name__ == "__main__":
    main()
