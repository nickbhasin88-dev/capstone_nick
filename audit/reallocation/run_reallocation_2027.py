"""
MOU reallocation scenarios (audit/reallocation): replace ONE year's US MOU funding for a set of countries with a
teammate's allocations and run the America First MOUs preset with the dashboard defaults (no government response,
sudden path, death-rate trends on, 400 draws, seed 7). Nothing the model reads is edited: the override is in memory
(a copy of country_inputs with mou_us_<year> replaced before scenarios.build_scenario builds the yearly cuts).

    .venv/bin/python audit/reallocation/run_reallocation_2027.py [--year 2027] [--alloc allocations_2027.csv]
                                                               [--draws 400] [--notes notes_2027.md]

Inputs:  <alloc>: iso3, country, then one column per scenario (the first scenario column is the reference, "Baseline");
         nominal US$ of US MOU funding in <year>. Countries not in the file keep their schedule unchanged and are left
         out of every result.
Outputs: results_<year>.csv (levels per scenario and country, totals, and changes vs the reference),
         marginal_<year>.csv (marginal effect of US$1M of <year> MOU money per country and drivers),
         RESULTS_<year>.md (all tables; <notes> appended as the explanation section when present).
Read-only with respect to the model.
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
logging.disable(logging.WARNING)
import health_model as hm  # noqa: E402
import scenarios as scn  # noqa: E402

PRESET = "America First MOUs"
SERVICES = {"ART": ["hiv_art"], "TB treatment": ["tb_ds", "tb_dr"], "Bednets": ["mal_itn"], "Spraying": ["mal_irs"],
            "Malaria treatment": ["mal_cm"], "Vaccines": ["imm"]}
EXTRA = {"PMTCT": ["hiv_pmtct"], "HIV prevention (infections averted)": ["hiv_prev"]}
NEED_LINE = {"ART": "hiv_art", "TB treatment": "tb_ds", "Bednets": "mal_itn", "Spraying": "mal_irs",
             "Malaria treatment": "mal_cm", "Vaccines": "imm", "PMTCT": "hiv_pmtct"}
BUCKETS = hm.BUCKETS
YEARS = scn.YEARS
FISCAL = hm.Fiscal(*scn.DEFAULT_FISCAL)
TREND = scn.DEFAULT_MORTALITY_TREND


def fmt(x, d=0):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "n/a"
    return f"{x:,.{d}f}"


def sfmt(x, d=0):
    """Signed number."""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "n/a"
    return f"{x:+,.{d}f}"


def md_table(cols, rows):
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


BILATERAL_ONLY = True      # set by main(): drop the preset's US multilateral exits (WHO, Gavi, UNFPA, Global Fund 23%)


def build(ci, year, amounts: dict | None):
    """The America First MOUs scenario with mou_us_<year> replaced in memory for the countries in `amounts`. With
    BILATERAL_ONLY the pair cuts the preset adds for US money through WHO, Gavi, UNFPA and the Global Fund are removed,
    so the only cut is the MOU schedule on US direct channels (bilateral agencies, NGOs, Gates direct, Other)."""
    c = ci.copy()
    if amounts:
        for iso, v in amounts.items():
            c.loc[iso, f"mou_us_{year}"] = float(v)
    sc = scn.build_scenario(PRESET, scn.default_opts(PRESET, c), c)
    if BILATERAL_ONLY:
        sc.pair = {}
    return sc


def run(iso, sc, inputs, ptab, draws):
    """(central run, 400-draw run) with the per-year, per-line arrays kept."""
    r0 = hm.run_country(iso, sc, FISCAL, inputs, ptab, n_draws=0, keep_draws=True, mortality_trend=TREND)
    rd = hm.run_country(iso, sc, FISCAL, inputs, ptab, n_draws=draws, keep_draws=True, mortality_trend=TREND)
    return r0, rd


def metrics(iso, sc, r0, rd, year):
    """One flat record of the numbers this analysis reports for one country and scenario."""
    t = YEARS.index(year)
    yt = r0["years"].set_index("year")
    L0 = r0["lines"].set_index("line")
    U0, D0 = r0["draws"]["units"], r0["draws"]["deaths"]
    Ud, Dd = rd["draws"]["units"], rd["draws"]["deaths"]
    m = {"iso3": iso, "mou_cut_year": float(sc.us_direct_path_by_country[iso][t]),
         "aid_lost_year_usd": float(yt.loc[year, "aid_lost_usd"]), "aid_lost_5y_usd": float(yt["aid_lost_usd"].sum()),
         "deaths_year": float(yt.loc[year, "deaths"])}
    for y in YEARS:
        m[f"deaths_{y}"] = float(yt.loc[y, "deaths"])
    people_year = 0.0
    for name, lines in {**SERVICES, **EXTRA}.items():
        u = float(sum(U0[l][0, t] for l in lines))
        m[f"people_{name}_year"] = u
        if name in SERVICES:
            people_year += u
        need = float(L0.loc[NEED_LINE[name], "need"]) if name in NEED_LINE else np.nan
        m[f"need_{name}"] = need
        m[f"cov_drop_{name}_year_pp"] = u / need * 100 if need and not np.isnan(need) else np.nan
        m[f"people_{name}_5y"] = float(sum(U0[l][0, :].sum() for l in lines))
    m["people_services_year"] = people_year
    B0 = r0["buckets"].set_index("bucket")
    Bd = rd["buckets"].set_index("bucket")
    for b in BUCKETS:
        m[f"deaths_5y_{b}"] = float(B0.loc[b, "deaths_5y"])
        m[f"deaths_5y_{b}_lo"], m[f"deaths_5y_{b}_hi"] = float(Bd.loc[b, "deaths_5y_lo"]), float(Bd.loc[b, "deaths_5y_hi"])
    m["deaths_5y"] = float(r0["totals"]["deaths_5y"])
    m["deaths_5y_lo"], m["deaths_5y_hi"] = float(rd["totals"]["deaths_5y_lo"]), float(rd["totals"]["deaths_5y_hi"])
    m["deaths_after_2030"] = float(r0["committed"]["after_2030"])
    m["deaths_after_2030_lo"], m["deaths_after_2030_hi"] = (float(rd["committed"]["after_2030_lo"]),
                                                            float(rd["committed"]["after_2030_hi"]))
    m["hiv_infections_5y"] = float(B0.loc["HIV", "infections_5y"])
    m["hiv_infections_5y_lo"], m["hiv_infections_5y_hi"] = (float(Bd.loc["HIV", "infections_5y_lo"]),
                                                            float(Bd.loc["HIV", "infections_5y_hi"]))
    m["capped_lines"] = ",".join(L0.index[L0["capped"].fillna(False).astype(bool)])
    m["donor_exceeds_cost_lines"] = ",".join(L0.index[L0["donor_exceeds_cost"].fillna(False).astype(bool)])
    # per-draw arrays for paired ranges (same seed in every run)
    arr = {"deaths_5y": np.asarray(rd["draw_totals"]["deaths_5y"], dtype=float),
           "deaths_after_2030": np.asarray(rd["draw_totals"]["after_2030"], dtype=float)}
    for b in BUCKETS:
        arr[f"deaths_5y_{b}"] = sum(Dd[l].sum(axis=1) for l in hm.DIRECT[b])
    arr["people_services_year"] = sum(Ud[l][:, t] for lines in SERVICES.values() for l in lines)
    return m, arr


def pct_range(a):
    return float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2027)
    ap.add_argument("--alloc", default=None, help="allocation CSV (default allocations_<year>.csv next to this script)")
    ap.add_argument("--draws", type=int, default=scn.ALL_COUNTRY_DRAWS)
    ap.add_argument("--notes", default=None, help="markdown appended as the explanation section (default notes_<year>.md)")
    ap.add_argument("--marginal-usd", type=float, default=1e6)
    ap.add_argument("--with-multilateral-exits", action="store_true",
                    help="keep the preset's US exits from WHO, Gavi, UNFPA and 23%% of the Global Fund (default: MOU bilateral schedule only)")
    a = ap.parse_args()
    global BILATERAL_ONLY
    BILATERAL_ONLY = not a.with_multilateral_exits
    year = a.year
    alloc_path = Path(a.alloc) if a.alloc else HERE / f"allocations_{year}.csv"
    notes_path = Path(a.notes) if a.notes else HERE / f"notes_{year}.md"
    alloc = pd.read_csv(alloc_path).set_index("iso3")
    scen_cols = [c for c in alloc.columns if c != "country"]
    ref_col = scen_cols[0]
    isos = list(alloc.index)
    names = alloc["country"].to_dict()

    I, P = hm.load_inputs(), hm.load_params()
    ci = I["ci"]
    lines_all = I["lines"]
    us = lines_all[(lines_all.src_grp == "United States") & lines_all.iso3.isin(isos)]
    us_direct = us[us.chan_grp.isin(hm.DIRECT_CHANNELS)].groupby("iso3").usd.sum().reindex(isos)
    us_all = us.groupby("iso3").usd.sum().reindex(isos)
    md = [f"# {year} MOU reallocation scenarios, {len(isos)} countries (no model changes)", "",
          f"Generated by `audit/reallocation/run_reallocation_2027.py --year {year}` from `{alloc_path.name}`. Preset: "
          f"{PRESET}, dashboard defaults (no government response, sudden path, death-rate trends on, {a.draws} draws, "
          f"seed 7). " + ("**US bilateral aid only:** the preset's US exits from WHO, Gavi, UNFPA and 23% of the Global "
          "Fund are switched off in memory, so the only cut is each country's MOU schedule on US direct channels "
          "(bilateral agencies, NGOs); every other donor and every multilateral channel is unchanged. " if BILATERAL_ONLY
          else "US multilateral exits kept as in the preset. ")
          + f"Only the {year} US MOU amount is replaced, in memory, for the {len(isos)} countries in the file; "
          "every other year and every other country keeps the schedule in `model_data/country_inputs.csv`. Totals "
          f"and comparisons cover these {len(isos)} countries only.", ""]

    # ------------------------------------------------------------------ Step 1: data check
    md += ["## Step 1. Data check", ""]
    on, infl = scn.mou_deflate_settings(P)
    md += [f"- `mou_deflate` is {'on' if on else 'off'} in `model_params.csv` (amounts used nominal, as written)."]
    chk = pd.DataFrame({"country": alloc["country"], "sheet_baseline": alloc[ref_col],
                        "model_mou_us_year": ci.loc[isos, f"mou_us_{year}"], "mou_us_ref": ci.loc[isos, "mou_us_ref"]})
    chk["diff_usd"] = chk["sheet_baseline"] - chk["model_mou_us_year"]
    chk["diff_pct"] = chk["diff_usd"] / chk["model_mou_us_year"] * 100
    bad = chk[chk["diff_pct"].abs() > 0.5]
    md += [f"- {ref_col} column vs the model's `mou_us_{year}`: {len(bad)} of {len(isos)} countries differ by more than "
           f"0.5% (differences of US$1 or less are rounding). Largest absolute difference: US${chk['diff_usd'].abs().max():,.0f}."]
    tot = alloc[scen_cols].sum()
    md += ["- Column totals (US$): " + "; ".join(f"{c} {v:,.2f}" for c, v in tot.items())
           + f". Spread between columns: US${tot.max() - tot.min():,.2f}" + (" (within US$20)." if tot.max() - tot.min() <= 20 else " (NOT within US$20).")]
    md += ["", md_table(["iso3", "Country", f"Sheet {ref_col}", f"Model mou_us_{year}", "Diff US$", "Diff %", "mou_us_ref"],
                        [[i, r.country, fmt(r.sheet_baseline), fmt(r.model_mou_us_year), fmt(r.diff_usd), f"{r.diff_pct:.3f}",
                          fmt(r.mou_us_ref)] for i, r in chk.iterrows()]), ""]

    # ------------------------------------------------------------------ Step 2: headroom
    md += ["## Step 2. Headroom check", "",
           "The preset's cut for a year is clip(1 - amount / `mou_us_ref`, 0, 1) (`scenarios.py` mou_schedule), so an "
           "amount above `mou_us_ref` is a 0% cut and the money above it buys nothing in the model (aid rises count as "
           "no loss, audit I-15). The table compares each ceiling's amount with that reference, and for information "
           "with the model's 2021-23 US baseline from `model_data/dah_lines.csv` (US direct channels, the rows the "
           "cut is applied to; and all US channels). The MOU amounts are nominal US totals from the MOU sheet and the "
           "model applies only the ratio, so only the `mou_us_ref` comparison decides whether money is lost to the clip.", ""]
    rows, flagged = [], []
    for i in isos:
        ref = float(ci.loc[i, "mou_us_ref"])
        r = [i, names[i], fmt(ref), fmt(us_direct[i]), fmt(us_all[i])]
        for c in scen_cols[1:]:
            v = float(alloc.loc[i, c])
            over = v - ref
            r.append(f"{fmt(v)}" + (f" **(+{over:,.0f} above ref)**" if over > 1 else ""))
            if over > 1:
                flagged.append((c, i, over))
        rows.append(r)
    md += [md_table(["iso3", "Country", "mou_us_ref", "US direct 2021-23 (model)", "US all channels 2021-23 (model)"]
                    + [f"{c} {year}" for c in scen_cols[1:]], rows), ""]
    if flagged:
        md += ["Flags (amount above `mou_us_ref`, money that would count as no gain): "
               + "; ".join(f"{c}: {names[i]} US${o:,.0f}" for c, i, o in flagged), f"Total affected: US${sum(o for _, _, o in flagged):,.0f}.", ""]
    else:
        md += ["**No flags:** no ceiling puts any country above its `mou_us_ref` in " + str(year) + ", so no money is lost to the "
               "clip; US$0 affected. (The +US$1 placeholders in the sheet raise a country's cut fraction by at most 1/ref "
               "and are treated as rounding.)", ""]
    above_direct = [(c, i) for c in scen_cols for i in isos if float(alloc.loc[i, c]) > us_direct[i]]
    md += [f"For information: {len([x for x in above_direct if x[0] == ref_col])} of the {len(isos)} {ref_col} amounts "
           "already exceed the model's 2021-23 US direct-channel baseline, because `mou_us_ref` (team sheet, 2021-25 "
           "average, all US funding) is larger than the model's IHME-based US direct rows. The model never applies the "
           "dollar amounts, only cut fractions, so this is not a gain case.", ""]

    # ------------------------------------------------------------------ Step 3: run
    sc_ref = build(ci, year, None)                        # the model's own schedule
    scens = {c: build(ci, year, alloc[c].to_dict()) for c in scen_cols}
    for i in isos:                                         # the reference column must reproduce the model's cuts
        assert np.allclose(sc_ref.us_direct_path_by_country[i], scens[ref_col].us_direct_path_by_country[i], atol=1e-9), i
    res, arrs = {}, {}
    for c in scen_cols:
        res[c], arrs[c] = {}, {}
        for i in isos:
            r0, rd = run(i, scens[c], I, P, a.draws)
            res[c][i], arrs[c][i] = metrics(i, scens[c], r0, rd, year)
            res[c][i]["mou_usd_year"] = float(alloc.loc[i, c])
    pre = pd.read_csv(scn.precomputed_path(hm.MODEL_DIR, PRESET)).set_index("iso3")
    pre_d = float(pre.loc[isos, "deaths_5y"].sum())
    base_d = sum(res[ref_col][i]["deaths_5y"] for i in isos)
    rep = max(abs(res[ref_col][i]["deaths_5y"] - pre.loc[i, "deaths_5y"]) / max(pre.loc[i, "deaths_5y"], 1) for i in isos)
    md += ["## Step 3. Run", "",
           f"- {ref_col} reproduces the model's own MOU schedule for all {len(isos)} countries (cuts identical)."
           + (f" It also reproduces the precomputed All Countries file (`all_countries_America_First_MOUs.csv`): largest "
              f"relative difference in deaths 2026-2030 {rep:.2e}." if not BILATERAL_ONLY else
              f" Deaths 2026-2030 for the {len(isos)} countries are {base_d:,.0f} against {pre_d:,.0f} in the precomputed "
              f"All Countries file, which includes the US multilateral exits that are switched off here."),
           f"- {year} cut fractions by scenario (1 - amount / mou_us_ref):", "",
           md_table(["iso3", "Country"] + scen_cols,
                    [[i, names[i]] + [f"{res[c][i]['mou_cut_year']:.1%}" for c in scen_cols] for i in isos]), ""]

    # ------------------------------------------------------------------ Step 4: outputs
    levels = []
    for c in scen_cols:
        for i in isos:
            levels.append({"scenario": c, "kind": "level", **res[c][i]})
    lev = pd.DataFrame(levels)
    num_cols = [k for k in lev.columns if lev[k].dtype.kind in "fi" and k not in ("mou_cut_year",)]
    sum_cols = [k for k in num_cols if not (k.startswith("cov_drop_") or k.endswith("_lo") or k.endswith("_hi"))]

    def total_row(c):
        d = {"scenario": c, "kind": "total", "iso3": "TOTAL"}
        for k in sum_cols:
            d[k] = float(lev[(lev.scenario == c)][k].sum())
        A = arrs[c]
        for k in ["deaths_5y", "deaths_after_2030"] + [f"deaths_5y_{b}" for b in BUCKETS]:
            lo, hi = pct_range(sum(A[i][k] for i in isos))
            d[f"{k}_lo"], d[f"{k}_hi"] = lo, hi
        for name in {**SERVICES, **EXTRA}:
            need = d[f"need_{name}"]
            d[f"cov_drop_{name}_year_pp"] = d[f"people_{name}_year"] / need * 100 if need else np.nan
        return d

    totals = {c: total_row(c) for c in scen_cols}

    def delta_row(c, i):
        a_, b_ = (res[c][i], res[ref_col][i]) if i != "TOTAL" else (totals[c], totals[ref_col])
        d = {"scenario": f"{c} minus {ref_col}", "kind": "change", "iso3": i}
        for k in num_cols:
            if k in a_ and k in b_ and not (k.endswith("_lo") or k.endswith("_hi")) and not k.startswith("need_"):
                d[k] = a_[k] - b_[k]
        A, B = arrs[c], arrs[ref_col]
        for k in ["deaths_5y", "deaths_after_2030", "people_services_year"] + [f"deaths_5y_{b}" for b in BUCKETS]:
            diff = (sum(A[j][k] for j in isos) - sum(B[j][k] for j in isos)) if i == "TOTAL" else A[i][k] - B[i][k]
            d[f"{k}_lo"], d[f"{k}_hi"] = pct_range(diff)
        return d

    deltas = {c: {i: delta_row(c, i) for i in isos + ["TOTAL"]} for c in scen_cols[1:]}
    out = pd.concat([lev, pd.DataFrame(list(totals.values())),
                     pd.DataFrame([deltas[c][i] for c in scen_cols[1:] for i in isos + ["TOTAL"]])], ignore_index=True)
    out.insert(2, "country", out["iso3"].map(lambda x: names.get(x, "All 15 countries" if x == "TOTAL" else x)))

    md += ["## Step 4. Results", "", f"### 4a. Totals, {len(isos)} countries", "",
           "People losing a service are the model's full-cost equivalents in the year (after the 15% continuity "
           "assumption), summed over ART, TB treatment, bednets, spraying, malaria treatment and vaccines. Deaths are "
           "the central run; ranges are the 2.5th-97.5th percentiles of the draws, and the ranges of changes are "
           "paired (same draws in every scenario).", ""]
    rows = []
    for c in scen_cols:
        T = totals[c]
        rows.append([c, fmt(T["aid_lost_year_usd"] / 1e6, 1), fmt(T["aid_lost_5y_usd"] / 1e6, 1), fmt(T["people_services_year"]),
                     f"{fmt(T['deaths_5y'])} ({fmt(T['deaths_5y_lo'])}-{fmt(T['deaths_5y_hi'])})",
                     fmt(T["deaths_year"]), fmt(T["deaths_after_2030"]), fmt(T["hiv_infections_5y"])])
    md += [md_table(["Scenario", f"Aid lost {year} US$M", "Aid lost 2026-30 US$M", f"People losing services {year}",
                     "Deaths 2026-30 (range)", f"Deaths in {year}", "Further deaths 2031-35", "HIV infections 2026-30"], rows), ""]
    md += [f"### 4b. Change vs {ref_col}, totals", ""]
    rows = []
    for c in scen_cols[1:]:
        D = deltas[c]["TOTAL"]
        rows.append([c, sfmt(D["aid_lost_year_usd"] / 1e6, 2), sfmt(D["aid_lost_5y_usd"] / 1e6, 2),
                     f"{sfmt(D['people_services_year'])} ({sfmt(D['people_services_year_lo'])} to {sfmt(D['people_services_year_hi'])})",
                     f"{sfmt(D['deaths_5y'])} ({sfmt(D['deaths_5y_lo'])} to {sfmt(D['deaths_5y_hi'])})",
                     sfmt(D["deaths_after_2030"]), sfmt(D["hiv_infections_5y"])]
                    + [sfmt(D[f"deaths_5y_{b}"]) for b in BUCKETS])
    md += [md_table(["Scenario", f"Aid lost {year} US$M", "Aid lost 2026-30 US$M", f"People losing services {year} (range)",
                     "Deaths 2026-30 (range)", "Further deaths 2031-35", "HIV infections 2026-30"] + [f"Deaths {b}" for b in BUCKETS], rows), ""]
    for c in scen_cols[1:]:
        D = deltas[c]["TOTAL"]
        d_ = D["deaths_5y"]
        word = "fewer" if d_ < 0 else "more"
        md += [f"- **{c}:** the reallocation is not zero-sum in outcomes: {fmt(abs(d_))} {word} deaths over 2026-2030 "
               f"({sfmt(d_ / max(totals[ref_col]['deaths_5y'], 1) * 100, 2)}% of the {ref_col} total), "
               f"{fmt(abs(D['people_services_year']))} {'fewer' if D['people_services_year'] < 0 else 'more'} people losing a "
               f"service in {year}, and {sfmt(D['aid_lost_year_usd'] / 1e6, 2)} US$M of modelled aid lost in {year} "
               f"(the same nominal total of MOU money buys a different amount of modelled aid because each country's "
               f"cut fraction is applied to its own 2021-23 US direct-channel baseline)."]
    md += [""]
    md += [f"### 4c. People losing each service in {year} and coverage change (totals)", ""]
    rows = []
    for name in list(SERVICES) + list(EXTRA):
        r = [name, fmt(totals[ref_col][f"people_{name}_year"]),
             f"{totals[ref_col][f'cov_drop_{name}_year_pp']:.2f}" if not np.isnan(totals[ref_col][f"cov_drop_{name}_year_pp"]) else "n/a"]
        for c in scen_cols[1:]:
            D = deltas[c]["TOTAL"]
            cv = D.get(f"cov_drop_{name}_year_pp", np.nan)
            r += [sfmt(D[f"people_{name}_year"]), f"{cv:+.3f}" if not np.isnan(cv) else "n/a"]
        rows.append(r)
    md += [md_table(["Service", f"{ref_col} people", f"{ref_col} coverage drop pp"]
                    + [x for c in scen_cols[1:] for x in (f"{c} Δ people", f"{c} Δ pp")], rows), ""]
    md += ["### 4d. Deaths by disease 2026-2030, totals (range), and the part caused by the " + str(year) + " change", ""]
    rows = []
    for b in BUCKETS:
        r = [b, f"{fmt(totals[ref_col][f'deaths_5y_{b}'])} ({fmt(totals[ref_col][f'deaths_5y_{b}_lo'])}-{fmt(totals[ref_col][f'deaths_5y_{b}_hi'])})"]
        for c in scen_cols[1:]:
            D = deltas[c]["TOTAL"]
            r.append(f"{sfmt(D[f'deaths_5y_{b}'])} ({sfmt(D[f'deaths_5y_{b}_lo'])} to {sfmt(D[f'deaths_5y_{b}_hi'])})")
        rows.append(r)
    rows.append(["All"] + [f"{fmt(totals[ref_col]['deaths_5y'])} ({fmt(totals[ref_col]['deaths_5y_lo'])}-{fmt(totals[ref_col]['deaths_5y_hi'])})"]
                + [f"{sfmt(deltas[c]['TOTAL']['deaths_5y'])} ({sfmt(deltas[c]['TOTAL']['deaths_5y_lo'])} to {sfmt(deltas[c]['TOTAL']['deaths_5y_hi'])})" for c in scen_cols[1:]])
    md += [md_table(["Disease", f"{ref_col} deaths 2026-30 (range)"] + [f"{c} Δ (paired range)" for c in scen_cols[1:]], rows), ""]
    md += ["Deaths by calendar year, change vs " + ref_col + " (central): the " + str(year) + " change also moves deaths in later "
           "years (ART cohorts age, TB cases spread 1-2 years later, missed vaccine cohorts die over following years).", ""]
    rows = [[c] + [sfmt(deltas[c]["TOTAL"][f"deaths_{y}"]) for y in YEARS] + [sfmt(deltas[c]["TOTAL"]["deaths_after_2030"])] for c in scen_cols[1:]]
    md += [md_table(["Scenario"] + [str(y) for y in YEARS] + ["2031-35"], rows), ""]

    md += [f"### 4e. By country: {year} money change, change in deaths 2026-30 and in people losing services in {year}", "",
           "Nominal US$ moved is the sheet's change in the country's " + str(year) + " MOU amount; modelled aid is the change "
           "in the model's aid lost in " + str(year) + " (cut fraction x the country's US direct-channel baseline). The "
           "per-US$1M columns divide the change in deaths by the money moved, so they are positive in both directions: "
           "lives saved per US$1M where money arrives, lives lost per US$1M where it leaves.", ""]
    for c in scen_cols[1:]:
        rows = []
        for i in isos:
            D = deltas[c][i]
            moved = D["mou_usd_year"]
            dd = D["deaths_5y"]
            rows.append([i, names[i], sfmt(moved / 1e6, 2), sfmt(-D["aid_lost_year_usd"] / 1e6, 2),
                         f"{sfmt(dd)} ({sfmt(D['deaths_5y_lo'])} to {sfmt(D['deaths_5y_hi'])})", sfmt(D["deaths_after_2030"]),
                         sfmt(D["people_services_year"]), sfmt(D["hiv_infections_5y"]),
                         f"{-dd / (moved / 1e6):+.1f}" if abs(moved) > 1e4 else "n/a",
                         f"{-dd / (-D['aid_lost_year_usd'] / 1e6):+.1f}" if abs(D["aid_lost_year_usd"]) > 1e4 else "n/a"])
        D = deltas[c]["TOTAL"]
        rows.append(["TOTAL", "All 15", "0.00", sfmt(-D["aid_lost_year_usd"] / 1e6, 2),
                     f"{sfmt(D['deaths_5y'])} ({sfmt(D['deaths_5y_lo'])} to {sfmt(D['deaths_5y_hi'])})", sfmt(D["deaths_after_2030"]),
                     sfmt(D["people_services_year"]), sfmt(D["hiv_infections_5y"]), "", ""])
        md += [f"**{c} minus {ref_col}**", "",
               md_table(["iso3", "Country", "MOU US$M moved", "Modelled aid US$M (+ = more aid)", "Δ deaths 2026-30 (range)",
                         "Δ deaths 2031-35", f"Δ people losing services {year}", "Δ HIV infections",
                         "Deaths per US$1M moved (nominal; + = lives the money saves where it arrives, or costs where it leaves)", "per US$1M modelled"], rows), ""]

    # ------------------------------------------------------------------ Step 5: marginal and drivers
    md += ["## Step 5. Efficiency: the marginal effect of US$1M of " + str(year) + " US MOU funding", "",
           f"Method: for each country, the {ref_col} run minus a run with the country's {year} MOU amount lowered by "
           f"US${a.marginal_usd / 1e6:,.0f}M (central parameters, everything else unchanged). 'People kept' are the "
           f"extra full-cost equivalents on each service in {year}; 'deaths averted' are the extra deaths over 2026-2030 "
           "(and 2031-2035) that the US$1M prevents. A +US$1M run checks linearity. The model's own US$1M cards "
           "(`health_model.per_million_card`, audit I-04: a uniform US$1M-a-year cut for five years to one disease across "
           "all donors and channels) are shown afterwards for comparison; they are per disease, per year of money, and "
           "not scaled by the MOU leverage, so they are not the same quantity.", ""]
    marg = []
    for i in isos:
        base_amt = float(alloc.loc[i, ref_col])
        r_base, _ = run(i, scens[ref_col], I, P, 0)
        r_dn, _ = run(i, build(ci, year, {i: base_amt - a.marginal_usd}), I, P, 0)
        r_up, _ = run(i, build(ci, year, {i: base_amt + a.marginal_usd}), I, P, 0)
        t = YEARS.index(year)
        k = 1e6 / a.marginal_usd
        rec = {"iso3": i, "country": names[i], "mou_us_ref": float(ci.loc[i, "mou_us_ref"]),
               "us_direct_base_usd": float(us_direct[i]), "leverage_model_usd_per_mou_usd": float(us_direct[i]) / float(ci.loc[i, "mou_us_ref"]),
               "modelled_aid_per_1M": (r_dn["years"]["aid_lost_usd"].iloc[t] - r_base["years"]["aid_lost_usd"].iloc[t]) * k}
        for name, lines in {**SERVICES, **EXTRA}.items():
            rec[f"kept_{name}_per_1M"] = float(sum(r_dn["draws"]["units"][l][0, t] - r_base["draws"]["units"][l][0, t] for l in lines)) * k
        rec["kept_services_per_1M"] = sum(rec[f"kept_{n}_per_1M"] for n in SERVICES)
        rec["deaths_averted_5y_per_1M"] = (r_dn["totals"]["deaths_5y"] - r_base["totals"]["deaths_5y"]) * k
        rec["deaths_averted_after_2030_per_1M"] = (r_dn["committed"]["after_2030"] - r_base["committed"]["after_2030"]) * k
        rec["deaths_averted_5y_per_1M_plus_side"] = (r_base["totals"]["deaths_5y"] - r_up["totals"]["deaths_5y"]) * k
        rec["infections_averted_5y_per_1M"] = (r_dn["buckets"].set_index("bucket").loc["HIV", "infections_5y"]
                                               - r_base["buckets"].set_index("bucket").loc["HIV", "infections_5y"]) * k
        Bd, Bb = r_dn["buckets"].set_index("bucket"), r_base["buckets"].set_index("bucket")
        for b in BUCKETS:
            rec[f"deaths_averted_{b}_per_1M"] = (Bd.loc[b, "deaths_5y"] - Bb.loc[b, "deaths_5y"]) * k
        # drivers
        Ld, Lb = r_dn["lines"].set_index("line"), r_base["lines"].set_index("line")
        dl = (Ld["gross_loss_usd"] - Lb["gross_loss_usd"]) * hm.N_YEARS * k      # the year's extra loss by line per US$1M
        rec["service_money_per_1M"] = float(dl.sum())      # the part landing on service lines
        for l in hm.ALL_DIRECT:
            rec[f"loss_{l}_per_1M"] = float(dl.get(l, 0.0))
            rec[f"uc_{l}"] = float(Lb.loc[l, "unit_cost"])
            du = (r_dn["draws"]["units"][l][0, t] - r_base["draws"]["units"][l][0, t]) * k
            dd = (r_dn["draws"]["deaths"][l][0, :].sum() - r_base["draws"]["deaths"][l][0, :].sum()) * k
            rec[f"deaths_per_unit_{l}"] = dd / du if du > 1e-9 else np.nan
            rec[f"capped_{l}"] = bool(Lb.loc[l, "capped"])
            rec[f"excess_{l}"] = bool(Lb.loc[l, "donor_exceeds_cost"])
        rec["loss_hiv_care_ct_per_1M"] = float(dl.get("hiv_care_ct", 0.0))
        bmix = us[(us.iso3 == i) & us.chan_grp.isin(hm.DIRECT_CHANNELS)].groupby("bucket").usd.sum()
        for b in BUCKETS:
            rec[f"us_direct_share_{b}"] = float(bmix.get(b, 0.0) / bmix.sum()) if bmix.sum() else np.nan
        row = ci.loc[i]
        rec["art_transmission_rate"] = float(row.get("art_transmission_rate", np.nan))
        rec["u5mr"] = float(row.get("sh_dyn_mort", np.nan))
        rec["imm_deaths_averted_per_child"] = float(row.get("imm_dpc", np.nan))
        rec["malaria_deaths_per_1000_cases"] = float(row.get("malaria_deaths", np.nan)) / float(row.get("malaria_cases", np.nan)) * 1000 if row.get("malaria_cases", 0) else np.nan
        rec["tb_hiv_share"] = float(row.get("tb_hiv_share", np.nan))
        rec["art_coverage"] = float(row.get("sh_hiv_artc_zs", np.nan))
        rec["tb_detection"] = float(row.get("sh_tbs_dtec_zs", np.nan))
        rec["itn_use"] = float(Lb.loc["mal_itn", "cov0"])
        rec["donor_share_hiv"] = float(Lb.loc["hiv_art", "donor_share_ext"])
        rec["donor_share_mal_itn"] = float(Lb.loc["mal_itn", "donor_share_ext"])
        for b in BUCKETS:                                   # the model's own card
            card = hm.per_million_card(i, b, I, P, TREND)
            rec[f"card_{b}_deaths_5y_per_1M_per_year"] = card["deaths_5y"] if card else np.nan
            rec[f"card_{b}_people_per_1M_per_year"] = card["people"] if card else np.nan
        marg.append(rec)
    M = pd.DataFrame(marg).set_index("iso3").sort_values("deaths_averted_5y_per_1M", ascending=False)
    M.insert(0, "rank_deaths_per_1M", range(1, len(M) + 1))
    md += ["### 5a. Ranking by deaths averted per US$1M of " + str(year) + " MOU money (nominal)", ""]
    rows = []
    for i, r in M.iterrows():
        rows.append([int(r.rank_deaths_per_1M), names[i], f"{r.leverage_model_usd_per_mou_usd:.2f}", fmt(r.modelled_aid_per_1M / 1e6, 2),
                     fmt(r.kept_ART_per_1M), fmt(r["kept_TB treatment_per_1M"]), fmt(r.kept_Bednets_per_1M), fmt(r.kept_Spraying_per_1M),
                     fmt(r["kept_Malaria treatment_per_1M"]), fmt(r.kept_Vaccines_per_1M), fmt(r.kept_services_per_1M),
                     f"{r.deaths_averted_5y_per_1M:.1f}", f"{r.deaths_averted_after_2030_per_1M:.1f}",
                     f"{r.deaths_averted_5y_per_1M / r.modelled_aid_per_1M * 1e6:.1f}" if r.modelled_aid_per_1M > 0 else "n/a",
                     f"{r.deaths_averted_5y_per_1M_plus_side:.1f}", f"{r.infections_averted_5y_per_1M:.1f}"])
    md += [md_table(["Rank", "Country", "Leverage (model $ per MOU $)", "Modelled aid per US$1M, US$M", "ART kept", "TB kept",
                     "Bednets kept", "Spraying kept", "Malaria Rx kept", "Vaccines kept", "All six services kept",
                     "Deaths averted 2026-30 per US$1M", "Further 2031-35", "Deaths averted per US$1M modelled aid",
                     "Check: +US$1M side", "HIV infections averted"], rows), ""]
    md += ["### 5b. Drivers", "",
           "Leverage = the country's 2021-23 US direct-channel aid in the model / `mou_us_ref`: how many modelled dollars "
           "one nominal MOU dollar moves. Disease mix = share of the country's US direct-channel aid by disease (the "
           "cut is uniform across the US direct rows, so the money lost follows this mix). Service money per US$1M = the "
           "year's extra loss landing on each service line after the model splits unspecified and systems money "
           "(`health_model.run_country` effective()). Unit costs are the central values the model uses (2023 US$). "
           "Deaths per unit = extra deaths 2026-2030 per extra person losing the service in " + str(year) + ".", ""]
    rows = []
    for i, r in M.iterrows():
        rows.append([names[i], f"{r.leverage_model_usd_per_mou_usd:.2f}"]
                    + [f"{r[f'us_direct_share_{b}']:.0%}" for b in BUCKETS]
                    + [fmt(r[f"loss_{l}_per_1M"] / 1e3) for l in ("hiv_art", "hiv_care_ct", "hiv_prev", "hiv_pmtct", "hiv_ovc", "tb_ds", "mal_itn", "mal_irs", "mal_cm", "imm")])
    md += ["Disease mix of US direct aid and service money per US$1M of MOU money (US$ thousands by line; the rest is "
           "non-service money: programme management, systems, OVC and testing money beyond the kappa share)", "",
           md_table(["Country", "Leverage"] + [f"US mix {b}" for b in BUCKETS]
                    + ["ART", "HIV testing & care", "HIV prevention", "PMTCT", "OVC", "TB DS", "Bednets", "IRS", "Malaria Rx", "Vaccines"], rows), ""]
    rows = []
    for i, r in M.iterrows():
        rows.append([names[i], fmt(r.uc_hiv_art), fmt(r.uc_tb_ds), fmt(r.uc_mal_itn, 2), fmt(r.uc_mal_irs, 2), fmt(r.uc_mal_cm, 2), fmt(r.uc_imm),
                     f"{r.deaths_per_unit_hiv_art:.4f}" if not np.isnan(r.deaths_per_unit_hiv_art) else "n/a",
                     f"{r.deaths_per_unit_tb_ds:.3f}" if not np.isnan(r.deaths_per_unit_tb_ds) else "n/a",
                     f"{r.deaths_per_unit_mal_itn * 1000:.3f}" if not np.isnan(r.deaths_per_unit_mal_itn) else "n/a",
                     f"{r.deaths_per_unit_mal_cm * 1000:.2f}" if not np.isnan(r.deaths_per_unit_mal_cm) else "n/a",
                     f"{r.deaths_per_unit_imm * 1000:.2f}" if not np.isnan(r.deaths_per_unit_imm) else "n/a",
                     f"{r.art_transmission_rate:.3f}", f"{r.art_coverage:.0f}%", f"{r.tb_hiv_share:.0%}" if not np.isnan(r.tb_hiv_share) else "n/a",
                     f"{r.malaria_deaths_per_1000_cases:.2f}" if not np.isnan(r.malaria_deaths_per_1000_cases) else "n/a",
                     f"{r.itn_use:.0%}" if not np.isnan(r.itn_use) else "n/a", f"{r.u5mr:.0f}", f"{r.imm_deaths_averted_per_child * 1000:.1f}"])
    md += ["Unit costs (US$ per person-year, course, net, person sprayed, case treated, child) and health effect per person losing the service", "",
           md_table(["Country", "ART $/py", "TB DS $/course", "Bednet $", "IRS $/person", "Malaria Rx $/case", "Vaccines $/child",
                     "Deaths 2026-30 per ART py lost", "per TB course lost", "per 1,000 bednets lost", "per 1,000 malaria cases untreated",
                     "per 1,000 children unvaccinated", "HIV transmission /unsuppressed py", "ART coverage", "TB-HIV share",
                     "Malaria deaths per 1,000 cases", "Bednet use", "U5MR", "Vaccine deaths averted per 1,000 children"], rows), ""]
    capped = [(names[i], l) for i, r in M.iterrows() for l in hm.ALL_DIRECT if r[f"capped_{l}"]]
    excess = [(names[i], l) for i, r in M.iterrows() for l in hm.ALL_DIRECT if r[f"excess_{l}"]]
    nonlin = [(names[i], r.deaths_averted_5y_per_1M, r.deaths_averted_5y_per_1M_plus_side) for i, r in M.iterrows()
              if abs(r.deaths_averted_5y_per_1M - r.deaths_averted_5y_per_1M_plus_side) > 0.02 * max(abs(r.deaths_averted_5y_per_1M), 1e-9)]
    md += ["Caps and nonlinearity:",
           "- Lines capped at the people covered (" + ref_col + " run): " + ("; ".join(f"{n} {l}" for n, l in capped) if capped else "none") + ".",
           "- Lines where donor money buys more than the donor-funded pool, so units scale with the share of money lost (`donor_exceeds_cost`): "
           + ("; ".join(f"{n} {l}" for n, l in excess) if excess else "none") + ".",
           "- Countries where the -US$1M and +US$1M marginals differ by more than 2% (nonlinear: malaria Lives Saved Tool, ART cohort ageing, TB spread): "
           + ("; ".join(f"{n} ({a_:.2f} vs {b_:.2f})" for n, a_, b_ in nonlin) if nonlin else "none") + ".", ""]
    rows = [[names[i]] + [f"{r[f'card_{b}_deaths_5y_per_1M_per_year']:.1f}" if not np.isnan(r[f"card_{b}_deaths_5y_per_1M_per_year"]) else "n/a" for b in BUCKETS]
            + [fmt(r[f"card_{b}_people_per_1M_per_year"]) for b in BUCKETS] for i, r in M.iterrows()]
    md += ["### 5c. The model's own US$1M cards (audit I-04), for comparison", "",
           "Deaths 2026-2030 from a US$1M-a-year loss for five years to one disease (all donors and channels), and the main "
           "service's people losing it per year (HIV: ART; TB: TB treatment; malaria: bednets; immunization: routine vaccines).", "",
           md_table(["Country"] + [f"{b} deaths per US$1M/yr" for b in BUCKETS] + [f"{b} people per US$1M/yr" for b in BUCKETS], rows), ""]

    # ------------------------------------------------------------------ explanation (notes) and files
    if notes_path.exists():
        md += ["## Step 5 (continued). Explanation", "", notes_path.read_text().strip(), ""]
    out.to_csv(HERE / f"results_{year}.csv", index=False)
    M.to_csv(HERE / f"marginal_{year}.csv")
    (HERE / f"RESULTS_{year}.md").write_text("\n".join(md))
    print(f"wrote results_{year}.csv ({len(out)} rows), marginal_{year}.csv, RESULTS_{year}.md")
    for c in scen_cols[1:]:
        D = deltas[c]["TOTAL"]
        print(f"{c}: deaths 2026-30 {D['deaths_5y']:+,.0f} ({D['deaths_5y_lo']:+,.0f} to {D['deaths_5y_hi']:+,.0f}); "
              f"people losing services {year} {D['people_services_year']:+,.0f}; modelled aid lost {year} {D['aid_lost_year_usd'] / 1e6:+,.2f} US$M")


if __name__ == "__main__":
    main()
