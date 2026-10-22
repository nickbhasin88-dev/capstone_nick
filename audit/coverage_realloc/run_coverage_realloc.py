"""
W-2, W-3, W-4 Coverage-preserving reallocation of the 2027 US MOU money, 15 countries (audit/coverage_realloc).
Same engine and conventions as audit/reallocation/run_reallocation_2027.py (America First MOUs preset, US bilateral
MOU schedule only, dashboard defaults, 400 draws, seed 7, central run plus paired 2.5-97.5 ranges; only the 2027
amount changes, in memory). Headline quantities are people on service: ART patient-years, TB courses, bednets,
spraying, malaria treatments, children vaccinated, and ART coverage in percentage points. Deaths are secondary.

    .venv/bin/python audit/coverage_realloc/run_coverage_realloc.py [--draws 400] [--step 1e6]

W-2: holding the 15-country nominal total fixed, the allocation that keeps the most people on service, and the one
     that keeps ART coverage closest to baseline, with no country cut more than 10 / 20 / 30% below its signed 2027
     amount (and no country above its mou_us_ref, where extra money buys nothing); a linear programme on the
     per-country marginals (exact greedy for one budget constraint with box bounds), verified by full runs and a second
     pass with marginals re-measured at the optimum. Compared with the team's Low / Medium / High ceilings.
W-3: the same in modelled dollars (each country's nominal change x its leverage): separates the mou_us_ref artifact
     from the disease-mix effect.
W-4: moves within HIV-heavy countries, within malaria-heavy countries, and across.
Outputs: RESULTS_coverage_realloc.md, marginals.csv, optima.csv, scenarios.csv. Read-only with respect to the model.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "audit" / "reallocation"))
logging.disable(logging.WARNING)
import health_model as hm  # noqa: E402
import run_reallocation_2027 as rr  # noqa: E402

YEAR = 2027
T = rr.YEARS.index(YEAR)
SERV = list(rr.SERVICES)                     # ART, TB treatment, Bednets, Spraying, Malaria treatment, Vaccines
fmt, sfmt, md_table = rr.fmt, rr.sfmt, rr.md_table


def kept(r0):
    """Units lost in YEAR by service (central run), ART coverage drop, deaths, aid lost."""
    U, L, yt = r0["draws"]["units"], r0["lines"].set_index("line"), r0["years"].set_index("year")
    d = {n: float(sum(U[l][0, T] for l in ls)) for n, ls in {**rr.SERVICES, **rr.EXTRA}.items()}
    d["all6"] = sum(d[n] for n in SERV)
    d["art_need"] = float(L.loc["hiv_art", "need"])
    d["ART pp"] = d["ART"] / d["art_need"] * 100
    d["deaths_5y"] = float(r0["totals"]["deaths_5y"])
    d["deaths_after"] = float(r0["committed"]["after_2030"])
    d["infections_5y"] = float(r0["buckets"].set_index("bucket").loc["HIV", "infections_5y"])
    d["aid_lost"] = float(yt.loc[YEAR, "aid_lost_usd"])
    d["capped"] = ",".join(L.index[L["capped"].fillna(False).astype(bool)])
    return d


def draws(rd):
    """Per-draw arrays for paired ranges."""
    Ud = rd["draws"]["units"]
    return {"ART": Ud["hiv_art"][:, T], "all6": sum(Ud[l][:, T] for ls in rr.SERVICES.values() for l in ls),
            "deaths_5y": np.asarray(rd["draw_totals"]["deaths_5y"], dtype=float)}


def rng(a):
    return float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))


class Engine:
    def __init__(self, I, P, isos, n_draws):
        self.I, self.P, self.isos, self.n = I, P, isos, n_draws
        self.ci = I["ci"]
        self.cache = {}

    def one(self, iso, amounts, with_draws=False):
        key = (iso, amounts[iso], with_draws)
        if key not in self.cache:
            sc = rr.build(self.ci, YEAR, {iso: amounts[iso]})
            r0 = hm.run_country(iso, sc, rr.FISCAL, self.I, self.P, n_draws=0, keep_draws=True, mortality_trend=rr.TREND)
            rd = (hm.run_country(iso, sc, rr.FISCAL, self.I, self.P, n_draws=self.n, keep_draws=True, mortality_trend=rr.TREND)
                  if with_draws else None)
            self.cache[key] = (kept(r0), draws(rd) if rd else None)
        return self.cache[key]

    def total(self, amounts, with_draws=True):
        """Totals over the 15 countries (central) and per-draw arrays."""
        ks = {i: self.one(i, amounts, with_draws) for i in self.isos}
        tot = {m: sum(ks[i][0][m] for i in self.isos) for m in SERV + ["all6", "ART", "PMTCT", "deaths_5y", "deaths_after", "infections_5y", "aid_lost", "art_need"]}
        tot["ART pp"] = tot["ART"] / tot["art_need"] * 100
        tot["capped"] = "; ".join(f"{i} {ks[i][0]['capped']}" for i in self.isos if ks[i][0]["capped"])
        arr = {m: sum(ks[i][1][m] for i in self.isos) for m in ("ART", "all6", "deaths_5y")} if with_draws else None
        return tot, arr, ks

    def marginals(self, amounts, step):
        """Per country: units kept per US$1M of YEAR MOU money (minus side), plus side, and caps."""
        rows = []
        k = 1e6 / step
        for i in self.isos:
            b = self.one(i, amounts)[0]
            dn = self.one(i, {**amounts, i: amounts[i] - step})[0]
            up = self.one(i, {**amounts, i: amounts[i] + step})[0]
            r = {"iso3": i, "amount": amounts[i]}
            for m in SERV + ["all6", "ART pp", "deaths_5y", "deaths_after", "infections_5y", "aid_lost"]:
                r[m] = (dn[m] - b[m]) * k
                r[f"{m}_plus"] = (b[m] - up[m]) * k
            r["capped_at_minus"] = dn["capped"]
            rows.append(r)
        return pd.DataFrame(rows).set_index("iso3")


def solve(m: dict, lb: dict, ub: dict, total: float, w: dict) -> dict:
    """max sum m_i x_i  s.t. sum w_i x_i = total, lb_i <= x_i <= ub_i. One budget constraint and box bounds, so the
    exact optimum fills countries in order of m_i / w_i (value per budget dollar) up to their upper bound."""
    x = dict(lb)
    rem = total - sum(w[i] * lb[i] for i in x)
    assert rem >= -1e-6, "lower bounds exceed the budget"
    for i in sorted(x, key=lambda j: -m[j] / w[j]):
        add = min(w[i] * (ub[i] - lb[i]), rem)
        x[i] += add / w[i]
        rem -= add
        if rem <= 1e-6:
            break
    assert rem < 1.0, "upper bounds below the budget"
    return x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=400)
    ap.add_argument("--step", type=float, default=1e6)
    a = ap.parse_args()
    alloc = pd.read_csv(ROOT / "audit" / "reallocation" / "allocations_2027.csv").set_index("iso3")
    isos = list(alloc.index)
    names = alloc["country"].to_dict()
    base = alloc["Baseline"].astype(float).to_dict()
    ceilings = {c: alloc[c].astype(float).to_dict() for c in alloc.columns if c not in ("country", "Baseline")}
    I, P = hm.load_inputs(), hm.load_params()
    ci = I["ci"]
    ref = {i: float(ci.loc[i, "mou_us_ref"]) for i in isos}
    us = I["lines"][(I["lines"].src_grp == "United States") & I["lines"].iso3.isin(isos) & I["lines"].chan_grp.isin(hm.DIRECT_CHANNELS)]
    us_direct = us.groupby("iso3").usd.sum().reindex(isos)
    lev = {i: float(us_direct[i]) / ref[i] for i in isos}
    mix = us.groupby(["iso3", "bucket"]).usd.sum().unstack().fillna(0.0).reindex(isos)
    mix = mix.div(mix.sum(axis=1), axis=0)
    E = Engine(I, P, isos, a.draws)
    TOT = sum(base.values())
    TOT_MODEL = sum(lev[i] * base[i] for i in isos)

    md = [f"# W-2 / W-3 / W-4. Coverage-preserving reallocation of {YEAR} US MOU money, {len(isos)} countries (no model changes)", "",
          "Generated by `audit/coverage_realloc/run_coverage_realloc.py`. Engine and conventions as "
          "`audit/reallocation/run_reallocation_2027.py`: America First MOUs preset, **US bilateral MOU schedule only** (the "
          "preset's US exits from WHO, Gavi, UNFPA and 23% of the Global Fund switched off in memory), dashboard defaults "
          f"(no government response, sudden path, death-rate trends on), {a.draws} draws, seed 7, central run plus paired "
          f"2.5-97.5 ranges. Only the {YEAR} US MOU amount changes, in memory. 'People on service' are the model's full-cost "
          "equivalents in 2027 after the 15% continuity assumption: ART patient-years, TB courses, bednets, people sprayed, "
          "malaria cases treated, children vaccinated. 'ART coverage pp' = ART patient-years lost / people living with HIV x 100. "
          "Deaths 2026-2030 are shown as a secondary column.", ""]

    # ------------------------------------------------------------------ Step 1: baseline and marginals
    b_tot, b_arr, b_ks = E.total(base)
    M0 = E.marginals(base, a.step)
    M0["leverage"] = pd.Series(lev)
    M0["us_mix_HIV"], M0["us_mix_Malaria"] = mix["HIV"], mix["Malaria"]
    M0.to_csv(HERE / "marginals.csv")
    nonlin = [(names[i], m, r[m], r[f"{m}_plus"]) for i, r in M0.iterrows() for m in ("all6", "ART")
              if abs(r[m] - r[f"{m}_plus"]) > 0.02 * max(abs(r[m]), 1e-9)]
    md += ["## Step 1. Baseline (signed 2027 amounts) and the marginal value of US$1M by country", "",
           f"Baseline, 15 countries, {YEAR}: people losing a service {fmt(b_tot['all6'])} ({fmt(rng(b_arr['all6'])[0])}-{fmt(rng(b_arr['all6'])[1])}); "
           f"ART patient-years lost {fmt(b_tot['ART'])} ({fmt(rng(b_arr['ART'])[0])}-{fmt(rng(b_arr['ART'])[1])}), {b_tot['ART pp']:.2f} pp of ART coverage; "
           f"TB courses {fmt(b_tot['TB treatment'])}; bednets {fmt(b_tot['Bednets'])}; children unvaccinated {fmt(b_tot['Vaccines'])}; "
           f"deaths 2026-30 {fmt(b_tot['deaths_5y'])} ({fmt(rng(b_arr['deaths_5y'])[0])}-{fmt(rng(b_arr['deaths_5y'])[1])}); modelled aid lost {YEAR} US${b_tot['aid_lost'] / 1e6:,.1f}M. "
           "These reproduce `audit/reallocation/RESULTS_2027.md` table 4a.", "",
           f"Marginals: the Baseline run minus a run with the country's {YEAR} amount lowered by US${a.step / 1e6:,.0f}M (people kept per US$1M "
           "nominal); the +US$1M side checks linearity. Leverage = modelled US$ per nominal MOU US$ (2021-23 US direct-channel aid / `mou_us_ref`).", "",
           md_table(["Country", "Leverage", "US mix HIV", "US mix malaria", "ART py kept per US$1M", "ART pp per US$1M", "TB courses", "Bednets", "Spraying", "Malaria Rx", "Vaccines", "All six services",
                     "Deaths averted 2026-30 (secondary)", "ART kept per US$1M modelled", "All six per US$1M modelled"],
                    [[names[i], f"{r.leverage:.2f}", f"{r.us_mix_HIV:.0%}", f"{r.us_mix_Malaria:.0%}", fmt(r.ART), f"{r['ART pp']:.4f}", fmt(r["TB treatment"]), fmt(r.Bednets), fmt(r.Spraying),
                      fmt(r["Malaria treatment"]), fmt(r.Vaccines), fmt(r.all6), f"{r.deaths_5y:.1f}", fmt(r.ART / r.leverage), fmt(r.all6 / r.leverage)]
                     for i, r in M0.sort_values("ART", ascending=False).iterrows()]), "",
           "Linearity and caps: " + ("the -US$1M and +US$1M marginals agree within 2% for people on service in every country"
                                     if not nonlin else "countries where the -US$1M and +US$1M marginals differ by more than 2%: "
                                     + "; ".join(f"{n} {m} ({x:,.0f} vs {y:,.0f})" for n, m, x, y in nonlin))
           + "; lines capped at the people covered in the -US$1M runs: " + ("none" if not M0.capped_at_minus.astype(bool).any() else
                                                                            "; ".join(f"{names[i]} {c}" for i, c in M0.capped_at_minus.items() if c)) + ".", ""]

    # ------------------------------------------------------------------ Step 2: W-2 optimisation
    OBJ = {"Most people on service (all six services)": "all6", "ART coverage closest to baseline (fewest ART patient-years lost)": "ART"}
    # (an objective on the sum of each country's pp drop was tried and dropped: it favours small countries and makes the pooled
    # ART coverage drop larger than the signed allocation's, so it does not answer the question)
    optima, scen_rows = [], []
    results = {"Baseline": (base, b_tot, b_arr)}
    for c, amts in ceilings.items():
        results[c] = (amts,) + E.total(amts)[:2]
    md += ["## Step 2. W-2: the allocation that keeps the most people on service, nominal total fixed", "",
           f"Constraint: the 15-country nominal total (US${TOT / 1e6:,.1f}M) is fixed; no country goes below (1 - cap) x its signed "
           "2027 amount; no country goes above its `mou_us_ref` (a 0% cut; money above it buys nothing in the model). With "
           "constant marginals the optimum is bang-bang: the best countries are filled to their reference and the worst cut to "
           "the floor. Pass 2 re-measures the marginals at the pass-1 optimum and solves again; the verified full-run values "
           "are reported.", ""]
    for obj_label, m in OBJ.items():
        for cap in (0.10, 0.20, 0.30):
            lb = {i: base[i] * (1 - cap) for i in isos}
            ub = {i: max(ref[i], base[i]) for i in isos}
            x1 = solve(M0[m].to_dict(), lb, ub, TOT, {i: 1.0 for i in isos})
            t1, a1, _ = E.total(x1)
            M1 = E.marginals(x1, a.step)
            x2 = solve(M1[m].to_dict(), lb, ub, TOT, {i: 1.0 for i in isos})
            t2, a2, _ = E.total(x2)
            pred1 = b_tot[m] - sum(M0.loc[i, m] * (x1[i] - base[i]) / 1e6 for i in isos)
            best, tb, ab = (x2, t2, a2) if t2[m] <= t1[m] else (x1, t1, a1)
            key = f"{obj_label} | cap {cap:.0%}"
            results[key] = (best, tb, ab)
            optima.append({"objective": obj_label, "cap": cap, "metric": m, "predicted_pass1": pred1, "verified_pass1": t1[m], "verified_pass2": t2[m],
                           "changed_in_pass2": sum(abs(x1[i] - x2[i]) > 1 for i in isos), **{f"x_{i}": best[i] for i in isos}})
    O = pd.DataFrame(optima)
    O.to_csv(HERE / "optima.csv", index=False)

    def row(label, amts, tot, arr):
        D = {m: tot[m] - b_tot[m] for m in tot if isinstance(tot[m], float)}
        return [label, sfmt(-(tot["aid_lost"] - b_tot["aid_lost"]) / 1e6, 1),
                f"{sfmt(-D['all6'])} ({sfmt(-rng(arr['all6'] - b_arr['all6'])[1])} to {sfmt(-rng(arr['all6'] - b_arr['all6'])[0])})",
                f"{sfmt(-D['ART'])} ({sfmt(-rng(arr['ART'] - b_arr['ART'])[1])} to {sfmt(-rng(arr['ART'] - b_arr['ART'])[0])})",
                f"{-D['ART pp']:+.3f}", sfmt(-D["TB treatment"]), sfmt(-D["Bednets"]), sfmt(-D["Vaccines"]),
                f"{sfmt(-D['deaths_5y'])} ({sfmt(-rng(arr['deaths_5y'] - b_arr['deaths_5y'])[1])} to {sfmt(-rng(arr['deaths_5y'] - b_arr['deaths_5y'])[0])})",
                sfmt(-D["infections_5y"])]

    cols = ["Scenario", "Modelled aid change 2027 US$M", "People kept on service 2027 (range)", "ART patient-years kept (range)", "ART coverage pp kept",
            "TB courses kept", "Bednets kept", "Children vaccinated kept", "Deaths averted 2026-30 (range)", "HIV infections averted"]
    rows = [row(k, *v) for k, v in results.items() if k != "Baseline"]
    md += ["Change versus Baseline (+ = kept on service / averted; the ceilings are the team's sheet, the optima this script's):", "",
           md_table(cols, rows), ""]
    md += ["Verification of the linear programme (people on service, 15-country totals; lower is better):", "",
           md_table(["Objective", "Cap", "Predicted from marginals (pass 1)", "Verified full run (pass 1)", "Verified (pass 2)", "Countries whose amount changed in pass 2"],
                    [[r.objective, f"{r.cap:.0%}", fmt(r.predicted_pass1, 1 if r.metric == "ART pp" else 0), fmt(r.verified_pass1, 1 if r.metric == "ART pp" else 0),
                      fmt(r.verified_pass2, 1 if r.metric == "ART pp" else 0), int(r.changed_in_pass2)] for r in O.itertuples()]), ""]
    for obj_label in OBJ:
        rows = []
        for i in isos:
            r = [names[i], fmt(base[i] / 1e6, 1), fmt(ref[i] / 1e6, 1)]
            for cap in (0.10, 0.20, 0.30):
                x = results[f"{obj_label} | cap {cap:.0%}"][0][i]
                r.append(f"{x / 1e6:,.1f} ({(x - base[i]) / base[i]:+.0%})")
            rows.append(r)
        md += [f"Allocation for **{obj_label}** (US$M, change vs signed):", "",
               md_table(["Country", "Signed 2027", "mou_us_ref", "Cap 10%", "Cap 20%", "Cap 30%"], rows), ""]

    # ------------------------------------------------------------------ Step 3: W-3 modelled dollars
    md += ["## Step 3. W-3: the same reallocation in modelled dollars", "",
           "The model turns each country's nominal amount into a cut fraction against `mou_us_ref` and applies it to its 2021-23 "
           "US direct-channel aid, so one nominal MOU dollar is worth `leverage` modelled dollars (0.23 Madagascar to 0.90 Botswana). "
           "Here the budget constraint is written in modelled dollars (sum of leverage x amount fixed, "
           f"US${TOT_MODEL / 1e6:,.1f}M): a dollar taken from Kenya must arrive as a modelled dollar elsewhere. (a) The team's ceilings "
           "re-expressed: the countries that lose money keep their nominal cuts; the recipients receive the modelled dollars "
           "released, split in proportion to the sheet's gifts (converted back to nominal with their own leverage). (b) The W-2 "
           "optimisation with the modelled-dollar constraint.", ""]
    rows = []
    for c, amts in ceilings.items():
        d = {i: amts[i] - base[i] for i in isos}
        donors = [i for i in isos if d[i] < 0]
        recips = [i for i in isos if d[i] > 0]
        released = sum(lev[i] * -d[i] for i in donors)
        gifts = sum(d[i] for i in recips)
        x = dict(base)
        over = []
        for i in donors:
            x[i] = amts[i]
        # water-filling: modelled dollars go to recipients in proportion to the sheet's gifts; a recipient that would pass its
        # mou_us_ref stops there (the clip) and the rest is shared among the others in the same proportions
        left, pool = released, {i: d[i] for i in recips}
        for _ in range(20):
            if left <= 1 or not pool:
                break
            tot_g = sum(pool.values())
            nxt = {}
            for i, g in pool.items():
                want = left * g / tot_g / lev[i]
                room = ref[i] - x[i]
                if want > room + 1e-6:
                    over.append(i)
                    x[i] = ref[i]
                    left -= room * lev[i]
                else:
                    nxt[i] = g
            if len(nxt) == len(pool):
                for i, g in pool.items():
                    x[i] += left * g / tot_g / lev[i]
                left = 0.0
            pool = nxt
        over = sorted(set(over))
        tot, arr, _ = E.total(x)
        results[f"{c} in modelled dollars"] = (x, tot, arr)
        nom = results[c][1]
        nom_arr = results[c][2]
        rows.append([c, sfmt((nom["aid_lost"] - b_tot["aid_lost"]) / 1e6, 1), sfmt((tot["aid_lost"] - b_tot["aid_lost"]) / 1e6, 1),
                     sfmt(nom["all6"] - b_tot["all6"]), sfmt(tot["all6"] - b_tot["all6"]), sfmt(nom["ART"] - b_tot["ART"]), sfmt(tot["ART"] - b_tot["ART"]),
                     f"{sfmt(nom['deaths_5y'] - b_tot['deaths_5y'])} ({sfmt(rng(nom_arr['deaths_5y'] - b_arr['deaths_5y'])[0])} to {sfmt(rng(nom_arr['deaths_5y'] - b_arr['deaths_5y'])[1])})",
                     f"{sfmt(tot['deaths_5y'] - b_tot['deaths_5y'])} ({sfmt(rng(arr['deaths_5y'] - b_arr['deaths_5y'])[0])} to {sfmt(rng(arr['deaths_5y'] - b_arr['deaths_5y'])[1])})",
                     f"{1 - (tot['deaths_5y'] - b_tot['deaths_5y']) / (nom['deaths_5y'] - b_tot['deaths_5y']):.0%}" if abs(nom["deaths_5y"] - b_tot["deaths_5y"]) > 1 else "n/a",
                     "; ".join(names[i] for i in over) or "none"])
    md += ["(a) The ceilings, nominal versus modelled-dollar neutral (change vs Baseline; + = more aid lost / more people losing service / more deaths):", "",
           md_table(["Ceiling", "Δ modelled aid lost 2027 US$M, nominal", "Δ, modelled-neutral", "Δ people losing service, nominal", "Δ, modelled-neutral",
                     "Δ ART patient-years lost, nominal", "Δ, modelled-neutral", "Δ deaths 2026-30 (range), nominal", "Δ, modelled-neutral",
                     "Share of the extra deaths that disappears", "Recipients filled to mou_us_ref (rest shared out)"], rows), ""]
    rows = []
    for obj_label, m in OBJ.items():
        for cap in (0.10, 0.20, 0.30):
            lb = {i: base[i] * (1 - cap) for i in isos}
            ub = {i: max(ref[i], base[i]) for i in isos}
            x1 = solve(M0[m].to_dict(), lb, ub, TOT_MODEL, lev)
            t1, a1, _ = E.total(x1)
            M1 = E.marginals(x1, a.step)
            x2 = solve(M1[m].to_dict(), lb, ub, TOT_MODEL, lev)
            t2, a2, _ = E.total(x2)
            best, tb, ab = (x2, t2, a2) if t2[m] <= t1[m] else (x1, t1, a1)
            key = f"{obj_label} | cap {cap:.0%} | modelled-dollar budget"
            results[key] = (best, tb, ab)
            rows.append(row(key, best, tb, ab) + [sfmt(sum(best.values()) / 1e6 - TOT / 1e6, 1)])
    md += ["(b) The W-2 optimisation with the modelled-dollar constraint (change vs Baseline; last column = how much the nominal total moves):", "",
           md_table(cols + ["Nominal total change US$M"], rows), ""]

    # ------------------------------------------------------------------ Step 4: W-4 within vs across disease
    hiv_g = [i for i in isos if mix.loc[i, "HIV"] >= 0.6]
    mal_g = [i for i in isos if mix.loc[i, "Malaria"] >= 0.5]
    md += ["## Step 4. W-4: moves within HIV-heavy countries, within malaria-heavy countries, and across", "",
           f"HIV-heavy = US direct-channel aid at least 60% HIV ({', '.join(names[i] for i in hiv_g)}); malaria-heavy = at least 50% malaria "
           f"({', '.join(names[i] for i in mal_g)}). A move of US$10M nominal from one country to another in {YEAR} (full runs, "
           "paired ranges). Effect per US$1M moved = (recipient's marginal - donor's marginal); the pair table averages the "
           "marginals over all ordered pairs in each class.", ""]
    pairs = []
    for cls, A, B in (("within HIV-heavy", hiv_g, hiv_g), ("within malaria-heavy", mal_g, mal_g), ("across (HIV-heavy to malaria-heavy)", hiv_g, mal_g),
                      ("across (malaria-heavy to HIV-heavy)", mal_g, hiv_g)):
        vals = [(M0.loc[j, "all6"] - M0.loc[i, "all6"], M0.loc[j, "ART"] - M0.loc[i, "ART"], M0.loc[j, "deaths_5y"] - M0.loc[i, "deaths_5y"],
                 M0.loc[j, "aid_lost"] - M0.loc[i, "aid_lost"]) for i in A for j in B if i != j]
        v = np.array(vals)
        best = max(((i, j) for i in A for j in B if i != j), key=lambda p: M0.loc[p[1], "ART"] - M0.loc[p[0], "ART"])
        best6 = max(((i, j) for i in A for j in B if i != j), key=lambda p: M0.loc[p[1], "all6"] - M0.loc[p[0], "all6"])
        gain = v[v[:, 1] > 0] if "within" in cls else v           # within a class every pair has a mirror image, so keep the improving direction
        pairs.append([cls, len(vals), sfmt(np.abs(v[:, 0]).mean()), sfmt(np.abs(v[:, 1]).mean()), f"{v[:, 2].max():+.1f}", sfmt(-v[:, 3].mean() / 1e6, 2),
                      f"{names[best[0]]} to {names[best[1]]}: {M0.loc[best[1], 'ART'] - M0.loc[best[0], 'ART']:+,.0f} ART py, {M0.loc[best[1], 'all6'] - M0.loc[best[0], 'all6']:+,.0f} people",
                      f"{names[best6[0]]} to {names[best6[1]]}: {M0.loc[best6[1], 'all6'] - M0.loc[best6[0], 'all6']:+,.0f} people, {M0.loc[best6[1], 'ART'] - M0.loc[best6[0], 'ART']:+,.0f} ART py"])
    md += [md_table(["Move class", "Ordered pairs", "Mean |Δ people on service| per US$1M moved", "Mean |Δ ART patient-years| per US$1M", "Best Δ deaths averted 2026-30 per US$1M (secondary)",
                     "Mean Δ modelled aid per US$1M moved (US$M; - = money lost in conversion)", "Best pair for ART", "Best pair for people"], pairs), ""]
    moves = []
    for cls, A, B in (("within HIV-heavy", hiv_g, hiv_g), ("within malaria-heavy", mal_g, mal_g), ("across, HIV-heavy to malaria-heavy", hiv_g, mal_g),
                      ("across, malaria-heavy to HIV-heavy", mal_g, hiv_g)):
        i, j = max(((i, j) for i in A for j in B if i != j), key=lambda p: M0.loc[p[1], "all6"] - M0.loc[p[0], "all6"])
        for amt_label, amt_j in (("US$10M nominal", 1e7), ("US$10M modelled (recipient gets 10M x lev_donor / lev_recipient)", 1e7 * lev[i] / lev[j])):
            x = dict(base)
            x[i] -= 1e7
            x[j] = min(base[j] + amt_j, ref[j])
            tot, arr, _ = E.total(x)
            moves.append([f"{cls}: {names[i]} to {names[j]}", amt_label, f"{(x[j] - base[j]) / 1e6:.1f}", sfmt(-(tot["aid_lost"] - b_tot["aid_lost"]) / 1e6, 2)]
                         + row("", x, tot, arr)[2:9])
    md += ["Full runs of the best people-on-service pair in each class (US$10M leaves the donor country in 2027):", "",
           md_table(["Move", "Amount basis", "Recipient receives US$M nominal", "Modelled aid change US$M", "People kept on service 2027 (range)", "ART patient-years kept (range)",
                     "ART coverage pp kept", "TB courses kept", "Bednets kept", "Children vaccinated kept", "Deaths averted 2026-30 (range)"], moves), ""]

    # ------------------------------------------------------------------ files
    for k, (x, tot, arr) in results.items():
        scen_rows.append({"scenario": k, **{f"amt_{i}": x[i] for i in isos}, **{m: v for m, v in tot.items() if isinstance(v, float)},
                          **{f"{m}_lo": rng(arr[m])[0] for m in arr}, **{f"{m}_hi": rng(arr[m])[1] for m in arr}})
    pd.DataFrame(scen_rows).to_csv(HERE / "scenarios.csv", index=False)
    (HERE / "RESULTS_coverage_realloc.md").write_text("\n".join(md))
    print("wrote RESULTS_coverage_realloc.md, marginals.csv, optima.csv, scenarios.csv")
    for k, (x, tot, arr) in results.items():
        print(f"{k}: people {tot['all6'] - b_tot['all6']:+,.0f}; ART {tot['ART'] - b_tot['ART']:+,.0f}; deaths {tot['deaths_5y'] - b_tot['deaths_5y']:+,.0f}; aid {(tot['aid_lost'] - b_tot['aid_lost']) / 1e6:+.1f}")


if __name__ == "__main__":
    main()
