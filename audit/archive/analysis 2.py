"""
Analyses for the dashboard audit (Steps 2, 5 and 6 evidence). Run from the repo root:

    .venv/bin/python audit/analysis.py

Writes:
  audit/fallbacks.csv        how many countries hit each default, fallback, clip or cap
  audit/outliers.csv         every country's outlier metrics (Full US exit, no backfill); top/bottom 10 in AUDIT.md
  audit/sensitivity.csv      5-year deaths and 2031-2035 deaths, all countries, each parameter at low / high
  audit/analysis.json        the other numbers quoted in AUDIT.md (cards vs model, ranges, MOU path, benchmarks ...)
The model and app code are only imported and called, never changed.
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
logging.disable(logging.WARNING)

import health_model as hm  # noqa: E402
import scenarios as scn  # noqa: E402

OUT = ROOT / "audit"            # its outputs live in audit/ (referenced by AUDIT.md)
I, P = hm.load_inputs(), hm.load_params()
CI, LINES = I["ci"], I["lines"]
PC = hm.draw_params(P, 0)
COUNTRIES = [c for c in CI.index if c in set(LINES.iso3)]
NONE = hm.Fiscal(*scn.DEFAULT_FISCAL)
FUS = scn.build_scenario("Full US exit", {}, CI)
A: dict = {}


def run(iso, sc=FUS, fiscal=NONE, ptab=P, n=400, **kw):
    return hm.run_country(iso, sc, fiscal, I, ptab, n_draws=n, **kw)


# --------------------------------------------------------------------------- #
# 1. Fallbacks, defaults, clips and caps (70 modelled countries)
# --------------------------------------------------------------------------- #
def fallbacks():
    c = CI.loc[COUNTRIES]
    out = []

    def add(what, n, note=""):
        out.append({"item": what, "countries": int(n), "of": len(COUNTRIES), "note": note})

    for col in ("plhiv", "sh_hiv_artc_zs", "sh_hiv_pmtc_zs", "hiv_pos_pregnancies", "malaria_deaths", "malaria_cases",
                "malaria_pop_at_risk", "sh_mlr_nets_zs"):
        src = c.get(f"{col}_source")
        if src is not None:
            n_fb = (~src.astype(str).str.startswith(("UNAIDS", "WHO"))).sum()
            add(f"{col}: not from WHO/UNAIDS (fallback)", n_fb, "; ".join(sorted(set(c.index[~src.astype(str).str.startswith(('UNAIDS', 'WHO'))]))))
    mal = c["malaria_deaths"].fillna(0) > 0
    add("malaria countries (WHO deaths > 0)", mal.sum())
    add("bednet use missing -> default 50% (malaria countries)", (mal & c["sh_mlr_nets_zs"].isna()).sum())
    lowinc = c["sh_mlr_incd_p3"].isna() | (c["sh_mlr_incd_p3"] < hm.MAL_CM_MIN_INCIDENCE)
    add("malaria treatment coverage -> default 40% (malaria countries; incidence < 50/1000 or survey missing)",
        (mal & (lowinc | c["sh_mlr_tret_zs"].isna())).sum())
    if "sh_mlr_tret_zs_year" in c:
        yrs = c.loc[mal & ~lowinc & c["sh_mlr_tret_zs"].notna(), "sh_mlr_tret_zs_year"]
        add("malaria treatment survey used: year <= 2015", (yrs <= 2015).sum(), f"median survey year {yrs.median():.0f}")
    if "sh_mlr_nets_zs_year" in c:
        y = c.loc[mal & c["sh_mlr_nets_zs"].notna() & ~c["sh_mlr_nets_zs_source"].astype(str).str.startswith("WHO"),
                  "sh_mlr_nets_zs_year"]
        add("bednet use from an old under-5 survey (not WHO modelled)", len(y), f"survey years {y.min():.0f}-{y.max():.0f}" if len(y) else "")
    add("PMTCT coverage missing -> ART coverage used", c["sh_hiv_pmtc_zs"].isna().sum())
    add("TB-HIV share missing -> 0", c["tb_hiv_share"].isna().sum())
    add("ART coverage missing", c["sh_hiv_artc_zs"].isna().sum())
    add("under-5 mortality missing -> 50", c["sh_dyn_mort"].isna().sum())
    add("GDP per person missing -> $1,000", c["gdp_pc"].isna().sum())
    add("income group missing -> GDP rule", c["income_group"].isna().sum() if "income_group" in c else len(c))
    add("government health spending 2023 missing -> fiscal capacity 0", c["ghes_2023"].isna().sum())
    add("GHES growth p75 <= median -> fiscal capacity 0",
        ((c["ghes_growth_p75"].fillna(0) - c["ghes_growth_median"].fillna(0).clip(lower=0)) <= 0).sum())
    add("interest/revenue missing -> debt-stress factor 1", c["gc_xpn_intp_rv_zs"].isna().sum())
    add("debt-stress factor < 1", (c["gc_xpn_intp_rv_zs"] > 10).sum())
    add("debt-stress factor at floor 0.25", (c["gc_xpn_intp_rv_zs"] >= 40).sum())
    u5 = c["sh_dyn_mort"].fillna(50) / 50
    add("vaccine death scale clipped at 0.3 (U5MR < 15)", (u5 < 0.3).sum())
    add("vaccine death scale clipped at 2.5 (U5MR > 125)", (u5 > 2.5).sum())
    inc = c["sh_hiv_incd_tl"] / c["sp_pop_totl"] * 1000
    add("HIV incidence clipped to [0.05, 10]/1000 (prevention cost)", ((inc < 0.05) | (inc > 10)).sum())
    add("HIV incidence missing -> 0.3/1000", inc.isna().sum())
    ref = pd.read_csv(ROOT / "unit_cost_reference.csv")
    spec = set(ref.loc[ref.kind == "art_site_cost", "key"])
    add("ART cost from a country study (else default)", len(spec & set(COUNTRIES)), ", ".join(sorted(spec & set(COUNTRIES))))
    # trend fills (fewer than 5 years of data in 2010-2019)
    for col in ("trend_u5mr", "trend_malaria_deaths"):
        v = c[col]
        add(f"{col}: at the -8%/+2% clip", ((v <= -0.08 + 1e-9) | (v >= 0.02 - 1e-9)).sum())
        add(f"{col}: equal to the median fill (likely no usable series)", (v == v.median()).sum(), f"median {v.median():.4f}")
    # model-level caps on Full US exit
    capped, excess, pool, zero_after = {}, {}, 0, {}
    for iso in COUNTRIES:
        L = run(iso, n=2)["lines"]
        for r in L.itertuples():
            if r.capped:
                capped[r.line] = capped.get(r.line, 0) + 1
            if r.donor_exceeds_cost:
                excess[r.line] = excess.get(r.line, 0) + 1
            if r.need == r.need and r.need > 0 and r.cov0 == r.cov0 and r.cov0 > 0 and \
                    r.cov0 - r.cov_drop_pp / 100 <= 1e-9 and r.units_lost > 0:
                zero_after[r.line] = zero_after.get(r.line, 0) + 1
    add("Full US exit: lines capped at people covered", sum(capped.values()), json.dumps(capped))
    add("Full US exit / any: donor aid exceeds cost x covered (proportional scaling)", sum(excess.values()), json.dumps(excess))
    add("Full US exit: coverage driven to 0%", sum(zero_after.values()), json.dumps(zero_after))
    tr = pd.read_csv(ROOT / "model_data" / "ihme_trend.csv")
    add("IHME 2025 cells: ratio clipped at 1.5", int((tr.ratio >= 1.5 - 1e-9).sum()), f"of {len(tr)} cells")
    add("IHME 2025 cells: ratio 0 (funding ends)", int((tr.ratio <= 1e-9).sum()), f"of {len(tr)} cells")
    add("IHME 2025 cells: baseline < $20M, uses donor x bucket ratio", int((tr.base_usd < 20e6).sum()), f"of {len(tr)} cells")
    mc = scn.mou_cuts(CI, scn.DEFAULT_MOU_YEAR)
    add("America First MOUs: countries with a schedule (others get the average cut)", len(mc),
        f"average 2028 cut {scn.mou_average_cut_pct(CI, scn.DEFAULT_MOU_YEAR)}%")
    pd.DataFrame(out).to_csv(OUT / "fallbacks.csv", index=False)


# --------------------------------------------------------------------------- #
# 2. Outliers (Full US exit, no backfill)
# --------------------------------------------------------------------------- #
def outliers():
    recs = []
    for iso in COUNTRIES:
        r = run(iso)
        T, L = r["totals"], r["lines"].set_index("line")
        row = CI.loc[iso]
        on_art = row["plhiv"] * row["sh_hiv_artc_zs"] / 100 if pd.notna(row["sh_hiv_artc_zs"]) else np.nan
        d = {"iso3": iso, "pop": row["sp_pop_totl"], "aid_lost": T["gross"], "deaths_5y": T["deaths_5y"],
             "deaths_per_100k": T["deaths_5y"] / row["sp_pop_totl"] * 1e5,
             "aid_lost_per_death_5y": T["gross"] * 5 / T["deaths_5y"] if T["deaths_5y"] > 0.5 else np.nan,
             "people_losing_art": L.loc["hiv_art", "units_lost"], "people_on_art": on_art,
             "art_loss_pct_of_on_art": L.loc["hiv_art", "units_lost"] / on_art * 100 if on_art and on_art > 0 else np.nan,
             "plhiv_source": row.get("plhiv_source", ""), "income_group": row.get("income_group", "")}
        for ln in hm.ALL_DIRECT:
            d[f"drop_pp_{ln}"] = L.loc[ln, "cov_drop_pp"]
            d[f"capped_{ln}"] = bool(L.loc[ln, "capped"])
            d[f"excess_{ln}"] = bool(L.loc[ln, "donor_exceeds_cost"])
            d[f"cov0_{ln}"] = L.loc[ln, "cov0"]
        for b in hm.BUCKETS:
            d[f"deaths_{b}"] = r["buckets"].set_index("bucket").loc[b, "deaths_5y"]
        d["us_share_of_modelled_aid"] = T["gross"] / T["base"] if T["base"] else np.nan
        recs.append(d)
    df = pd.DataFrame(recs)
    df.to_csv(OUT / "outliers.csv", index=False)
    return df


# --------------------------------------------------------------------------- #
# 3. Sensitivity: every parameter at its low and high value (central run, all countries)
# --------------------------------------------------------------------------- #
def total(ptab, sc=FUS, **kw):
    d5 = after = 0.0
    for iso in COUNTRIES:
        r = hm.run_country(iso, sc, NONE, I, ptab, n_draws=2, **kw)
        d5 += r["totals"]["deaths_5y"]
        after += r["committed"]["after_2030"]
    return d5, after


def sensitivity():
    base5, base_a = total(P)
    rows = [{"param": "(central)", "status": "", "value": "", "deaths_5y": base5, "after_2030": base_a}]
    for p in P.index:
        for side in ("low", "high"):
            t = P.copy()
            v = float(P.loc[p, side])
            t.loc[p, "central"] = v          # the central run uses only this; low/high stay (fixing all three crashes uc_imm)
            d5, a = total(t)
            rows.append({"param": p, "status": P.loc[p, "status"], "side": side, "value": v,
                         "central_value": float(P.loc[p, "central"]), "deaths_5y": d5, "after_2030": a,
                         "pct_change_5y": (d5 / base5 - 1) * 100, "pct_change_after": (a / base_a - 1) * 100})
    # hard-coded assumptions in health_model.py (module constants), changed temporarily for this run only
    consts = [("DR_TB_SHARE", 0.02, 0.06), ("DR_TB_COV", 0.30, 0.60), ("MAL_CM_MIN_INCIDENCE", 25, 100),
              ("HIV_WEIBULL_SHAPE", 2.0, 2.5), ("FALLBACK_MORTALITY_TREND", -0.02, 0.0)]
    for name, lo, hi in consts:
        orig = getattr(hm, name)
        for side, v in (("low", lo), ("high", hi)):
            setattr(hm, name, v)
            d5, a = total(P)
            rows.append({"param": f"code:{name}", "status": "assumption (hard-coded)", "side": side, "value": v,
                         "central_value": orig, "deaths_5y": d5, "after_2030": a,
                         "pct_change_5y": (d5 / base5 - 1) * 100, "pct_change_after": (a / base_a - 1) * 100})
        setattr(hm, name, orig)
    # mortality trend switch
    d5, a = total(P, mortality_trend=False)
    rows.append({"param": "setting:mortality_trend off", "status": "assumption (default on)", "side": "off",
                 "deaths_5y": d5, "after_2030": a, "pct_change_5y": (d5 / base5 - 1) * 100,
                 "pct_change_after": (a / base_a - 1) * 100})
    pd.DataFrame(rows).to_csv(OUT / "sensitivity.csv", index=False)
    A["sensitivity_base"] = {"deaths_5y": base5, "after_2030": base_a}


# --------------------------------------------------------------------------- #
# 4. Other numbers for the report
# --------------------------------------------------------------------------- #
def cards_vs_model():
    """Per-US$1M cards vs what the full model gives for a small even cut to that bucket (deaths per $1M a year)."""
    import model_section as ms
    out = []
    for iso in ("KEN", "NGA", "MOZ", "HND", "IRQ", "UGA", "ZAF", "COD"):
        r = run(iso)
        cards = {c["bucket"]: c for c in ms._per_million_cards(r, P, iso)}
        for b in hm.BUCKETS:
            r0 = hm.run_country(iso, hm.uniform_scenario(b, 0.10), NONE, I, P, n_draws=2)
            bb = r0["buckets"].set_index("bucket").loc[b]
            model = bb["deaths_5y"] / (bb["net_loss_usd"] / 1e6) if bb["net_loss_usd"] > 1e3 else np.nan
            card = float(cards[b]["deaths"].replace(",", ""))
            out.append({"iso3": iso, "bucket": b, "card_deaths_per_1M": card,
                        "model_deaths_per_1M_bucket_10pct_cut": model,
                        "ratio_card_to_model": card / model if model and model == model and model > 0 else np.nan,
                        "card_people_per_1M": float(cards[b]["people_n"].replace(",", ""))})
    A["cards_vs_model"] = out


def infections_median_vs_central():
    out = []
    for iso in ("KEN", "NGA", "MOZ", "ZAF", "UGA"):
        r = run(iso, keep_draws=True)
        rc = run(iso, n=0) if False else None
        med = r["buckets"].set_index("bucket").loc["HIV", "infections_5y"]
        # central run: n_draws=0 makes every draw the central value
        c = hm.run_country(iso, FUS, NONE, I, P, n_draws=0)["buckets"].set_index("bucket").loc["HIV", "infections_5y"]
        out.append({"iso3": iso, "shown_median": med, "central": c, "pct_diff": (med / c - 1) * 100 if c else np.nan})
    A["infections_median_vs_central"] = out


def central_vs_median_deaths():
    out = []
    for iso in ("KEN", "NGA", "MOZ", "ZAF", "UGA", "COD", "HND"):
        r = run(iso)
        T = r["totals"]
        med = float(np.median(sum(v.sum(axis=1) for v in run(iso, keep_draws=True)["draws"]["deaths"].values())))
        out.append({"iso3": iso, "central": T["deaths_5y"], "median": med, "lo": T["deaths_5y_lo"], "hi": T["deaths_5y_hi"]})
    A["central_vs_median_deaths"] = out


def joint_vs_summed_range():
    """All Countries says summing country percentiles is wider than a joint interval. Check it."""
    tot = np.zeros(400)
    lo = hi = 0.0
    for iso in COUNTRIES:
        r = run(iso, keep_draws=True)
        d = sum(v.sum(axis=1) for v in r["draws"]["deaths"].values())
        tot += d
        lo += np.percentile(d, 2.5)
        hi += np.percentile(d, 97.5)
    A["all_country_range"] = {"summed_percentiles": [lo, hi], "joint_percentiles": [float(np.percentile(tot, 2.5)),
                                                                                    float(np.percentile(tot, 97.5))]}


def mou_path():
    """The 'MOU schedule' path applied to the America First MOUs preset (2028 default) vs the schedule itself."""
    out = []
    for iso in scn.mou_cuts(CI, 2028):
        path = scn.mou_cut_path(CI, iso)
        if path is None:
            continue
        sched = []
        r = CI.loc[iso]
        last = None
        for y in scn.YEARS:
            v = r.get(f"mou_us_{y}")
            last = last if pd.isna(v) else float(np.clip(1 - v / r["mou_us_ref"], 0, 1))
            sched.append(0.0 if last is None else last)
        o28 = scn.default_opts("America First MOUs", CI)
        dash = hm.run_country(iso, scn.build_scenario("America First MOUs", o28, CI), NONE, I, P, n_draws=2, cut_path=path)
        # faithful: the preset at the deepest year, with the same relative path -> US direct cut in year t = schedule
        deep = scn.YEARS[int(np.argmax(sched))]
        od = {**o28, "mou_year": deep}
        faith = hm.run_country(iso, scn.build_scenario("America First MOUs", od, CI), NONE, I, P, n_draws=2, cut_path=path)
        c28 = scn.mou_cuts(CI, 2028)[iso]
        out.append({"iso3": iso, "schedule_cuts": [round(x, 3) for x in sched],
                    "dashboard_us_cut_by_year": [round(c28 * p, 3) for p in path],
                    "dashboard_committed": dash["committed"]["deaths"], "schedule_committed": faith["committed"]["deaths"],
                    "dashboard_deaths_5y": dash["totals"]["deaths_5y"], "schedule_deaths_5y": faith["totals"]["deaths_5y"]})
    A["mou_path"] = out
    # the preset itself (sudden): one year's cut held for five years vs the schedule's 2026-2030 average
    pre = []
    for iso, c in scn.mou_cuts(CI, 2028).items():
        r = CI.loc[iso]
        cuts = [1 - r[f"mou_us_{y}"] / r["mou_us_ref"] for y in scn.YEARS if pd.notna(r.get(f"mou_us_{y}"))]
        pre.append({"iso3": iso, "cut_2028_used": round(c, 3), "schedule_mean_2026_30": round(float(np.mean(cuts)), 3),
                    "schedule_2030": round(cuts[-1], 3)})
    A["mou_preset"] = pre


def benchmarks():
    pre = {p: pd.read_csv(scn.precomputed_path(hm.MODEL_DIR, p)) for p in scn.PRECOMPUTED_PRESETS}
    us = pre["Full US exit"]
    art = 0.0
    for iso in COUNTRIES:
        art += run(iso, n=2)["lines"].set_index("line").loc["hiv_art", "units_lost"]
    A["benchmarks"] = {
        "full_us_exit_deaths_5y": float(us.deaths_5y.sum()), "full_us_exit_hiv_5y": float(us.deaths_5y_HIV.sum()),
        "full_us_exit_tb_5y": float(us.deaths_5y_TB.sum()), "full_us_exit_malaria_5y": float(us.deaths_5y_Malaria.sum()),
        "full_us_exit_imm_5y": float(us.deaths_5y_Immunization.sum()),
        "full_us_exit_hiv_infections_5y": float(us.hiv_infections_5y.sum()),
        "full_us_exit_people_losing_art": art, "full_us_exit_after_2030": float(us.deaths_after_2030.sum()),
        "plhiv_on_art_70_countries": float((CI.loc[COUNTRIES, "plhiv"] * CI.loc[COUNTRIES, "sh_hiv_artc_zs"] / 100).sum()),
    }


def regression_claims():
    r = I["reg"]["fiscal_replacement"]
    A["fiscal_regression"] = {"n_countries": r["n_countries"], "years": r["years"], "theta": hm.theta_historical(I["reg"])}


def main():
    if not hasattr(scn, "mou_cuts"):
        sys.exit("Archived: this script belongs to commit 4cbb7ff (see audit/archive/README.md). Run it there.")
    fallbacks()
    print("fallbacks done")
    df = outliers()
    print("outliers done")
    cards_vs_model()
    infections_median_vs_central()
    central_vs_median_deaths()
    joint_vs_summed_range()
    mou_path()
    benchmarks()
    regression_claims()
    print("analyses done")
    sensitivity()
    print("sensitivity done")
    (OUT / "analysis.json").write_text(json.dumps(A, indent=1, default=float))


if __name__ == "__main__":
    main()
