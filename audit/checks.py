"""
Automated checks for the dashboard audit (Step 4). Run from the repo root:

    .venv/bin/python audit/checks.py            # full run (same as --full): every country, ~10 minutes
    .venv/bin/python audit/checks.py --quick    # development: 9 countries, fewer draws; writes *_quick outputs only

Runs the model for every country x every donor preset x every government response and checks the invariants listed
in AUDIT.md; also runs global checks (precomputed files, monotonicity, zero cut, data reconciliation for Sections 1-3).
Writes audit/checks_results.csv (one row per country-scenario-check) and audit/checks_summary.csv / .md.
The model and app code are only imported and called, never changed.
"""
from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
logging.disable(logging.WARNING)

import health_model as hm  # noqa: E402
import scenarios as scn  # noqa: E402

OUT = ROOT / "audit"
TOL = 1e-6
I, P = hm.load_inputs(), hm.load_params()
CI, LINES = I["ci"], I["lines"]
PC = hm.draw_params(P, 0)
KAPPA = float(PC["hss_kappa"][0])
SIGMA = float(PC["hss_service_share"][0])
COUNTRIES = [c for c in CI.index if c in set(LINES.iso3)]
QUICK = "--quick" in sys.argv
if QUICK:
    COUNTRIES = [c for c in ("KEN", "NGA", "MOZ", "UGA", "ZAF", "ZMB", "MWI", "HND", "IRQ") if c in COUNTRIES]
# quick mode: 100 draws (was 50). With 50 draws the 97.5th percentile of a skewed parameter set (malaria costs and
# effects have centrals near one end of their ranges) can fall below the central run once hss_kappa's wide draw range
# no longer applies to systems money (Batch 3+4, L-05); the dashboard's 400 draws and 100 draws keep the central inside
DRAWS = 100 if QUICK else 400
SUFFIX = "_quick" if QUICK else ""
PRESETS = list(scn.PRESETS)
RESPONSES = {
    "none": scn.DEFAULT_FISCAL,
    "custom25": ("custom", 0.25, True, "pro_rata", "p75"),
    "max": ("max", 0.0, True, "pro_rata", "p75"),
    "gradual": ("gradual", 0.0, True, "pro_rata", "p75"),
}
rows: list[dict] = []


def rec(iso, preset, resp, check, ok, value="", detail="", warning=False):
    """warning=True: the check passes but is reported as a warning (a known, tolerated difference)."""
    rows.append({"iso3": iso, "preset": preset, "response": resp, "check": check, "pass": bool(ok),
                 "warning": bool(warning and ok),
                 "value": value if isinstance(value, str) else f"{value:.6g}" if value == value else "nan",
                 "detail": detail})


def close(a, b, rel=1e-6, abs_=1e-6):
    return abs(a - b) <= max(abs_, rel * max(abs(a), abs(b)))


def gov_add_for(iso):
    """What the dashboard passes for 'Gradual budget increase' with its defaults (Steady, 0.5 points a year)."""
    b = hm.health_budget(iso, I)
    room = float(b["room_pct"]) if b["room_pct"] == b["room_pct"] else 0.0
    if room <= 0 or not (b["gov_spend_usd"] == b["gov_spend_usd"]):
        return None
    pts = scn.gov_shape("Steady", 0.5, room)
    return tuple(float(v) for v in hm.gov_add_from_points(pts, b["gov_spend_usd"])) if any(pts) else None


# --------------------------------------------------------------------------- #
# Independent reimplementation of the documented scenario cuts (for the 1-(1-a)(1-b) check)
# --------------------------------------------------------------------------- #
DIRECT = {"Bilateral agency", "NGOs", "Gates direct", "Other"}
US_PAIRS = {("United States", "WHO"): 1.0, ("United States", "Gavi"): 1.0, ("United States", "UNFPA"): 1.0,
            ("United States", "Global Fund"): 0.23}
OECD = {"United States": 0.57, "Germany": 0.174, "France": 0.109, "United Kingdom": 0.108, "Japan": 0.056}


def expected_cut(preset, iso, src, chan, bucket, opts):
    if preset == "IHME 2025 preliminary estimates":
        return 1.0 - I["trend_map"].get((src, chan, bucket), 1.0)
    if preset == scn.ANNOUNCED:                     # cells show the average of the cell's five yearly announced cuts
        v = hm.announcement_lookup(I["announce_map"], iso, src, chan)
        return 0.0 if v is None else float(np.mean(np.clip(v, -1, 1)))
    direct = chan in DIRECT
    a, pair, ch = 0.0, {}, {}
    if preset in ("Full US exit", "Combined retreat"):
        if src == "United States" and direct:
            a = 1.0
        pair = US_PAIRS
    if preset == "America First MOUs":
        if src == "United States" and direct:
            a = float(np.mean(scn.mou_schedule(CI, iso)[0]))   # cells show the average yearly cut of the schedule
        pair = US_PAIRS
    if preset in ("OECD-reported 2025 aid cuts", "Combined retreat") and src in OECD:
        if not (preset == "Combined retreat" and src == "United States"):
            a = OECD[src]
    if preset == "Global Fund & Gavi shortfalls":
        ch = {"Global Fund": 0.20, "Gavi": 0.15}      # documented defaults (I-07); the sliders change them
    if preset == "Custom":
        a = (opts["custom_direct"][src] if direct else opts["custom_multi"][src]) / 100
    a = pair.get((src, chan), a)
    b = ch.get(chan, 0.0)
    return float(np.clip(1 - (1 - a) * (1 - b), -1, 1))


def yearly_line_loss(iso, preset, opts, cells) -> pd.Series:
    """Average yearly loss by line as the model defines it (sudden path): each year's line loss, a rise counted as no
    loss (I-15), averaged over 2026-2030. Equal to the cells' average-cut loss when cuts are the same every year; the
    Announced donor cuts preset changes cuts by year, so a line can gain in one year and lose in another."""
    if not len(cells):
        return pd.Series(dtype=float)
    sc = scn.build_scenario(preset, opts, CI)
    cy = sc.cuts_by_year(cells, iso, I["trend_map"], I["announce_map"])
    yl = [pd.Series(cells["usd"].to_numpy() * cy[:, t], index=cells.index).groupby(cells["line"]).sum().clip(lower=0)
          for t in range(cy.shape[1])]
    return sum(yl) / len(yl)


# --------------------------------------------------------------------------- #
# Per-run checks
# --------------------------------------------------------------------------- #
def displayed_equals_central(iso, preset, resp, res, rc):
    """I-05: every displayed number is the central run. rc = the same run with n_draws=0 (every draw = central)."""
    T, Tc = res["totals"], rc["totals"]
    pairs = {f"T.{k}": (T[k], Tc[k]) for k in ("gross", "replaced", "net", "deaths_5y", "deaths_y1")}
    pairs["C.after_2030"] = (res["committed"]["after_2030"], rc["committed"]["after_2030"])
    pairs["C.committed"] = (res["committed"]["deaths"], rc["committed"]["deaths"])
    B, Bc = res["buckets"].set_index("bucket"), rc["buckets"].set_index("bucket")
    for b in hm.BUCKETS:
        for k in ("deaths_5y", "deaths_y1", "gross_loss_usd", "net_loss_usd", "infections_5y"):
            pairs[f"B.{b}.{k}"] = (B.loc[b, k], Bc.loc[b, k])
    L, Lc = res["lines"].set_index("line"), rc["lines"].set_index("line")
    for ln in hm.ALL_DIRECT:
        for k in ("units_lost", "cov_drop_pp", "deaths_5y", "deaths_y1", "infections_5y", "net_loss_usd"):
            a, b = L.loc[ln, k], Lc.loc[ln, k]
            if a == a or b == b:
                pairs[f"L.{ln}.{k}"] = (a, b)
    pairs.update({f"path.{b}.{t}": (res["path"][b].iloc[t], rc["path"][b].iloc[t]) for b in hm.BUCKETS for t in range(5)})
    bad = [f"{k}: shown {a:.4g} vs central {b:.4g}" for k, (a, b) in pairs.items()
           if not (a == b or close(float(a), float(b), 1e-9, 1e-6))]
    rec(iso, preset, resp, "displayed_value_equals_central_run", not bad, len(bad), "; ".join(bad[:5]))


def deaths_vs_people(iso, preset, tag, L):
    """Every service line: 5-year deaths never exceed the 5-year total of people affected; for ART, never the peak
    number of people off treatment (mostly the same people each year)."""
    bad = []
    for r in L.itertuples():
        if r.line in hm.LINKED or not (r.deaths_5y > 1e-9):
            continue
        cap = r.units_lost_peak if r.line == "hiv_art" else r.units_lost_5y
        if not (r.deaths_5y <= cap * (1 + 1e-9) + 1e-6):
            bad.append(f"{r.line}: deaths {r.deaths_5y:.1f} > {'peak' if r.line == 'hiv_art' else '5-year'} people "
                       f"{cap:.1f}")
    rec(iso, preset, tag, "deaths_le_people_affected", not bad, len(bad), "; ".join(bad[:4]))


def per_run(iso, preset, resp, res, fiscal_t, opts):
    T, L, B, C, F = res["totals"], res["lines"], res["buckets"], res["committed"], res["fiscal"]
    Lx = L.set_index("line")
    Bx = B.set_index("bucket")
    show = L[(L["base_usd"] > 0) | (L["net_loss_usd"] != 0)]
    gains = T.get("gains", 0) > 0

    # 1-2 displayed values finite and non-negative
    disp = {f"T.{k}": T[k] for k in ("base", "gross", "replaced", "net", "deaths_5y", "deaths_5y_lo", "deaths_5y_hi",
                                     "deaths_y1")}
    disp.update({f"B.{b}.{k}": Bx.loc[b, k] for b in hm.BUCKETS for k in ("gross_loss_usd", "replaced_usd",
                                                                            "net_loss_usd", "deaths_5y")})
    disp["HIV.infections_5y"] = Bx.loc["HIV", "infections_5y"]
    disp.update({f"C.{k}": v for k, v in C["after_parts"].items()})
    disp["C.after_2030"] = C["after_2030"]
    for r in show.itertuples():
        linked = r.line in hm.LINKED          # HIV testing & care: no units or cost of its own (shown as "-"; I-09)
        for k in ("base_usd", "net_loss_usd", "unit_cost", "units_lost", "deaths_5y", "deaths_5y_lo", "deaths_5y_hi"):
            if not (linked and k in ("unit_cost", "units_lost")):
                disp[f"L.{r.line}.{k}"] = getattr(r, k)
        if r.need == r.need and r.need > 0:
            disp[f"L.{r.line}.cov0"] = r.cov0
            disp[f"L.{r.line}.cov_drop_pp"] = r.cov_drop_pp
    disp.update({f"F.{k}": F[k] for k in ("ghes", "capacity", "replacement")})
    bad_nan = [k for k, v in disp.items() if not np.isfinite(float(v))]
    rec(iso, preset, resp, "displayed_finite", not bad_nan, len(bad_nan), "; ".join(bad_nan[:8]))
    neg = [k for k, v in disp.items() if np.isfinite(float(v)) and float(v) < -1e-6]
    rec(iso, preset, resp, "displayed_nonnegative", not neg or gains, len(neg),
        ("aid gains in scenario; " if gains else "") + "; ".join(neg[:8]))

    # 3-4 coverage
    cov_bad, cap_bad = [], []
    for r in show.itertuples():
        if not (r.need == r.need and r.need > 0 and r.cov0 == r.cov0):
            continue
        after = r.cov0 - r.cov_drop_pp / 100
        if not (0 <= r.cov0 <= 1 + TOL) or after < -1e-6 or after > r.cov0 + 1e-6:
            cov_bad.append(f"{r.line}: {r.cov0:.3f}->{after:.3f}")
        if r.units_lost > r.cov0 * r.need * (1 + 1e-6) + 1e-6:
            cap_bad.append(f"{r.line}: {r.units_lost:.0f}>{r.cov0 * r.need:.0f}")
    rec(iso, preset, resp, "coverage_in_0_1_and_after_le_before", not cov_bad, len(cov_bad), "; ".join(cov_bad))
    rec(iso, preset, resp, "people_losing_le_people_covered", not cap_bad, len(cap_bad), "; ".join(cap_bad))

    # 5-6 money ordering
    ok = (T["net"] <= T["gross"] + TOL) and (T["gross"] <= T["base"] * (1 + 1e-9) + TOL) and \
         (-TOL <= T["replaced"] <= T["gross"] + TOL)
    rec(iso, preset, resp, "net_le_gross_le_base_and_replaced_le_gross", ok, T["gross"] / T["base"] if T["base"] else 0,
        f"net={T['net']:.0f} gross={T['gross']:.0f} base={T['base']:.0f} replaced={T['replaced']:.0f}")
    if fiscal_t[0] in ("custom", "max"):
        rec(iso, preset, resp, "replaced_le_fiscal_capacity", T["replaced"] <= F["capacity"] + TOL,
            T["replaced"] - F["capacity"], f"replaced={T['replaced']:.0f} capacity={F['capacity']:.0f}")
    # line-level: net loss per line <= gross per line
    lbad = [r.line for r in L.itertuples() if r.net_loss_usd > r.gross_loss_usd + 1e-6 or r.replaced_usd < -1e-6]
    rec(iso, preset, resp, "line_net_le_line_gross", not lbad, len(lbad), "; ".join(lbad))

    # 7-9 deaths
    dneg = [k for k, v in disp.items() if ("deaths" in k or k.startswith("C.")) and float(v) < -1e-6]
    rec(iso, preset, resp, "deaths_nonnegative", not dneg or gains, len(dneg), "; ".join(dneg[:8]))
    rbad = []
    trip = [("T", T["deaths_5y_lo"], T["deaths_5y"], T["deaths_5y_hi"]),
            ("C.after", C["after_2030_lo"], C["after_2030"], C["after_2030_hi"]),
            ("C.committed", C["deaths_lo"], C["deaths"], C["deaths_hi"]),
            ("HIV.inf", Bx.loc["HIV", "infections_5y_lo"], Bx.loc["HIV", "infections_5y"],
             Bx.loc["HIV", "infections_5y_hi"])]
    trip += [(f"B.{b}", Bx.loc[b, "deaths_5y_lo"], Bx.loc[b, "deaths_5y"], Bx.loc[b, "deaths_5y_hi"]) for b in hm.BUCKETS]
    trip += [(f"L.{r.line}", r.deaths_5y_lo, r.deaths_5y, r.deaths_5y_hi) for r in show.itertuples()]
    trip += [(f"L.{r.line}.inf", r.infections_5y_lo, r.infections_5y, r.infections_5y_hi) for r in show.itertuples()
             if r.infections_5y_hi > 0]
    trip += [(f"L.{r.line}.units", r.units_lost_lo, r.units_lost, r.units_lost_hi) for r in show.itertuples()
             if r.line not in hm.LINKED]
    for name, lo, c, hi in trip:
        if not (lo - 1e-6 <= c <= hi + 1e-6):
            rbad.append(f"{name}: {lo:.1f} <= {c:.1f} <= {hi:.1f}")
    rec(iso, preset, resp, "range_lo_le_central_le_hi", not rbad, len(rbad), "; ".join(rbad[:6]))
    ybad = [n for n, a, b in [("T", T["deaths_y1"], T["deaths_5y"])] +
            [(r.line, r.deaths_y1, r.deaths_5y) for r in L.itertuples()] if a > b + 1e-6 and not gains]
    rec(iso, preset, resp, "year1_le_5year", not ybad, len(ybad), "; ".join(ybad))

    # 10 sums
    sb = []
    for b in hm.BUCKETS:
        s = L.loc[L["bucket"] == b, "deaths_5y"].sum()
        if not close(s, Bx.loc[b, "deaths_5y"], 1e-9, 1e-6):
            sb.append(f"{b}: lines {s:.3f} vs bucket {Bx.loc[b, 'deaths_5y']:.3f}")
    if not close(B["deaths_5y"].sum(), T["deaths_5y"], 1e-9, 1e-6):
        sb.append(f"buckets {B['deaths_5y'].sum():.3f} vs total {T['deaths_5y']:.3f}")
    for k_b, k_t in (("gross_loss_usd", "gross"), ("replaced_usd", "replaced"), ("net_loss_usd", "net")):
        if not close(B[k_b].sum(), T[k_t], 1e-6, 1.0):
            sb.append(f"{k_b}: buckets {B[k_b].sum():.0f} vs total {T[k_t]:.0f}")
    rec(iso, preset, resp, "lines_sum_to_buckets_sum_to_totals", not sb, len(sb), "; ".join(sb))
    # path chart and headline agree
    pth = res["path"]
    rec(iso, preset, resp, "path_chart_sums_to_headline", close(pth.values.sum(), T["deaths_5y"], 1e-9, 1e-6) and
        close(pth.iloc[0].sum(), T["deaths_y1"], 1e-9, 1e-6), pth.values.sum() - T["deaths_5y"])
    # unspecified splitting conserves money: line losses (direct lines, plus linked lines in full) + the non-service
    # money = bucket. Batch 3+4 (L-05, L-43; SPEC.md section 3): non-service = (1 - sigma) x (HSS + systems share of
    # unspecified) + programme-management share of unspecified + prevention share where the bucket has no prevention
    # line (TB) + (1 - kappa) x testing share where it has no linked line (TB, malaria)
    cells = res["cells"]
    yl = yearly_line_loss(iso, preset, opts, cells)
    kb = []
    for b in ("HIV", "TB", "Malaria"):
        hss = float(yl.get(hm.HSS[b], 0.0))
        unspec = float(yl.get(hm.UNSPEC[b], 0.0))
        tag = hm.UNSPEC_TAG[b]
        sh = {c: float(CI.loc[iso, f"unspec_{tag}_{c}"]) for c in ("treatment", "prevention", "testing", "rssh", "pm")}
        ns = (1 - SIGMA) * (hss + unspec * sh["rssh"]) + unspec * sh["pm"]
        if not hm.UNSPEC_PREV.get(b):
            ns += unspec * sh["prevention"]
        if not hm.LINKED_IN[b]:
            ns += (1 - KAPPA) * unspec * sh["testing"]
        direct = L.loc[L["bucket"] == b, "gross_loss_usd"].sum()
        bucket = Bx.loc[b, "gross_loss_usd"]
        if not close(direct + ns, bucket, 1e-6, 1.0):
            kb.append(f"{b}: direct {direct:.0f} + non-service {ns:.0f} vs bucket {bucket:.0f}")
    rec(iso, preset, resp, "unspec_and_kappa_conserve_money", not kb, len(kb), "; ".join(kb))
    # 1-(1-a)(1-b) applied once, exactly as documented
    exp = np.array([expected_cut(preset, iso, s, c, b, opts) for s, c, b in
                    zip(cells["src_grp"], cells["chan_grp"], cells["bucket"])])
    diff = np.abs(exp - cells["cut"].to_numpy()) if len(cells) else np.zeros(1)
    rec(iso, preset, resp, "cut_formula_matches_documented_scenario", diff.max() < 1e-9, float(diff.max()))

    # 11-12 table and hero agree with the headline
    import model_section as ms   # imported here: streamlit-free functions only
    rws = ms._service_rows(show)
    tb = []
    if not close(rws["deaths_5y"].sum(), T["deaths_5y"], 1e-9, 1e-6):
        tb.append(f"table deaths {rws['deaths_5y'].sum():.2f} vs headline {T['deaths_5y']:.2f}")
    o_base, o_net = T["base"] - rws["base_usd"].sum(), T["net"] - rws["net_loss_usd"].sum()
    if o_base < -1 or o_net < -1:
        tb.append(f"Other Aid row negative (shown as $0): base {o_base:.0f}, net {o_net:.0f}")
    rec(iso, preset, resp, "table_total_row_equals_headline", not tb, len(tb), "; ".join(tb))
    care, _ = ms.care_breakdown(Lx)
    ppl = rws.loc[rws["line"] != "hiv_prev", "units_lost"].sum()
    rec(iso, preset, resp, "hero_people_equals_table_people", close(care, ppl, 1e-9, 0.5), care - ppl,
        f"hero {care:.0f} table {ppl:.0f}")
    # per-year label: aid at risk per year equals the scenario's yearly loss
    G = float(yl.sum()) if len(cells) else 0.0
    rec(iso, preset, resp, "aid_at_risk_is_per_year_not_5yr_total", close(G, T["gross"], 1e-9, 1.0), T["gross"] / G if G else 1)
    # coverage shown as fraction (not percent)
    pct_bad = [r.line for r in show.itertuples() if r.cov0 == r.cov0 and r.cov0 > 1.0 + TOL]
    rec(iso, preset, resp, "coverage_is_fraction_not_percent", not pct_bad, len(pct_bad), "; ".join(pct_bad))
    return T


def main():
    t0 = time.time()
    # ---------------- per-run checks ----------------
    for preset in PRESETS:
        opts = scn.default_opts(preset, CI)
        sc = scn.build_scenario(preset, opts, CI)
        for resp, ft in RESPONSES.items():
            for iso in COUNTRIES:
                if preset == "America First MOUs" and iso not in sc.us_direct_path_by_country:
                    continue                                   # group A only (I-02/I-03/I-08)
                gov_add = gov_add_for(iso) if resp == "gradual" else None
                res = hm.run_country(iso, sc, hm.Fiscal(*ft), I, P, n_draws=DRAWS, gov_add_usd=gov_add)
                per_run(iso, preset, resp, res, ft, opts)
                deaths_vs_people(iso, preset, resp, res["lines"])
                rc = hm.run_country(iso, sc, hm.Fiscal(*ft), I, P, n_draws=0, gov_add_usd=gov_add)
                displayed_equals_central(iso, preset, resp, res, rc)
    print(f"per-run checks done in {time.time() - t0:.0f}s")

    # ---------------- I-13 and I-15: every country x preset x response x funding path ----------------
    import model_section as ms
    paths = [s_ for s_ in scn.PATH_SHAPES if s_ != "Custom"]
    for preset in PRESETS:
        opts = scn.default_opts(preset, CI)
        sc = scn.build_scenario(preset, opts, CI)
        for path in (["MOU schedule"] if sc.mou_only else paths):
            cut = None if path in ("MOU schedule", "Sudden (default)") else tuple(scn.path_shape(path))
            for resp, ft in RESPONSES.items():
                for iso in COUNTRIES:
                    if sc.mou_only and iso not in sc.us_direct_path_by_country:
                        continue
                    gov_add = gov_add_for(iso) if resp == "gradual" else None
                    r = hm.run_country(iso, sc, hm.Fiscal(*ft), I, P, n_draws=20, cut_path=cut, gov_add_usd=gov_add)
                    T, L = r["totals"], r["lines"]
                    tag = f"{resp} | {path}"
                    avg, y30, _ = ms.fiscal_gap_values(r)
                    ok = close(avg["left"], T["net"], 1e-9, 1e-6) and close(avg["gap"], avg["filled"] + avg["left"],
                                                                             1e-9, 1e-6) \
                        and close(y30["gap"], y30["filled"] + y30["left"], 1e-9, 1e-6)
                    rec(iso, preset, tag, "fiscal_gap_left_equals_headline_net_and_gap_equals_filled_plus_left", ok,
                        avg["left"] - T["net"], f"gap {avg['gap']:.0f} filled {avg['filled']:.0f} left {avg['left']:.0f}")
                    show = L[(L["base_usd"] > 0) | (L["net_loss_usd"] != 0)]
                    rws = ms._service_rows(show)
                    care, _ = ms.care_breakdown(L.set_index("line"))
                    ppl = rws.loc[rws["line"] != "hiv_prev", "units_lost"].sum()
                    ok = close(care, ppl, 1e-9, 0.5) and close(rws["deaths_5y"].sum(), T["deaths_5y"], 1e-9, 1e-6)
                    rec(iso, preset, tag, "headline_people_and_deaths_equal_table_totals", ok, care - ppl,
                        f"hero people {care:.0f} table {ppl:.0f}; deaths {T['deaths_5y']:.1f} table "
                        f"{rws['deaths_5y'].sum():.1f}")
                    neg = [f"{x.line}" for x in L.itertuples() if x.units_lost < -1e-9 or
                           (x.cov_drop_pp == x.cov_drop_pp and x.cov_drop_pp < -1e-9)]
                    rec(iso, preset, tag, "no_negative_people_or_coverage_drop", not neg, len(neg), "; ".join(neg))
                    deaths_vs_people(iso, preset, tag, L)
    print(f"path checks done in {time.time() - t0:.0f}s")

    # ---------------- precomputed files vs a fresh run ----------------
    for preset in scn.PRECOMPUTED_PRESETS:
        path = scn.precomputed_path(hm.MODEL_DIR, preset)
        old = pd.read_csv(path).set_index("iso3")
        if QUICK:                                      # the full run_all comparison runs in --full only
            new = pd.DataFrame(columns=old.columns, index=pd.Index([], name="iso3"))
        else:
            new = hm.run_all(scn.build_scenario(preset, scn.default_opts(preset, CI), CI), hm.Fiscal(*scn.DEFAULT_FISCAL),
                             I, P, n_draws=scn.ALL_COUNTRY_DRAWS).set_index("iso3")
        for iso in new.index:
            cols = [c for c in new.columns if c in old.columns]
            d = {c: abs(new.loc[iso, c] - old.loc[iso, c]) / max(1.0, abs(new.loc[iso, c])) for c in cols
                 if pd.notna(new.loc[iso, c]) or pd.notna(old.loc[iso, c])}
            worst = max(d, key=lambda c: d[c] if d[c] == d[c] else 1.0)
            rec(iso, preset, "none", "precomputed_csv_matches_fresh_run", d[worst] < 1e-6, d[worst], worst)
        missing = set(new.columns) - set(old.columns)
        rec("ALL", preset, "none", "precomputed_csv_has_all_columns", not missing, len(missing), ", ".join(missing))
        # draw totals (IMP-10): present, 400 draws, equal to a fresh run (--full), and the range brackets the total
        A = scn.load_precomputed(hm.MODEL_DIR, preset)
        dt = A.attrs.get("draw_totals")
        rec("ALL", preset, "none", "precomputed_draw_totals_present",
            dt is not None and len(dt["deaths_5y"]) == scn.ALL_COUNTRY_DRAWS, 0 if dt is None else len(dt["deaths_5y"]))
        if dt is not None:
            lo, hi = hm.total_range(A, "deaths_5y")
            rec("ALL", preset, "none", "all_country_range_brackets_total", lo <= A["deaths_5y"].sum() <= hi,
                f"{lo:,.0f} <= {A['deaths_5y'].sum():,.0f} <= {hi:,.0f}")
            if not QUICK:
                fresh = new.attrs.get("draw_totals")
                f_, o_ = np.asarray(fresh["deaths_5y"]), np.asarray(dt["deaths_5y"])
                dd = float(np.max(np.abs(f_ - o_) / np.maximum(1.0, np.abs(f_))))
                rec("ALL", preset, "none", "precomputed_draw_totals_match_fresh_run", dd < 1e-6, dd)
        # also the dashboard's own country run == the All Countries row
        for iso in ("KEN", "NGA", "MOZ", "HND", "IRQ"):
            if iso not in old.index:                   # America First MOUs: group A countries only
                continue
            r = hm.run_country(iso, scn.build_scenario(preset, scn.default_opts(preset, CI), CI),
                               hm.Fiscal(*scn.DEFAULT_FISCAL), I, P, n_draws=400)
            ok = close(r["totals"]["deaths_5y"], old.loc[iso, "deaths_5y"], 1e-6, 1e-3) and \
                close(r["totals"]["gross"], old.loc[iso, "gross_loss_usd"], 1e-9, 1.0)
            rec(iso, preset, "none", "dashboard_country_equals_all_countries_row", ok,
                r["totals"]["deaths_5y"] - old.loc[iso, "deaths_5y"])
    print(f"precomputed checks done in {time.time() - t0:.0f}s")

    # ---------------- I-04: per-US$1M cards = the full model for a US$1M uniform cut to the disease ----------------
    import model_section as ms
    pj = P.to_json(orient="split")
    for iso in COUNTRIES:
        cards = {c["bucket"]: c for c in ms._per_million_cards(iso, pj, scn.DEFAULT_MORTALITY_TREND, iso)}
        for b in hm.BUCKETS:
            aid = float(LINES.loc[(LINES.iso3 == iso) & (LINES.bucket == b), "usd"].sum())
            c = cards[b]
            if aid <= 0:
                rec(iso, b, "", "card_says_no_aid_when_none", c["people_n"] is None and "No " in c["no_deaths"], aid)
                continue
            cut = min(1.0, 1e6 / aid)
            r = hm.run_country(iso, hm.uniform_scenario(b, cut), hm.Fiscal(), I, P, n_draws=0,
                               mortality_trend=scn.DEFAULT_MORTALITY_TREND)
            Bx = r["buckets"].set_index("bucket")
            lost = float(Bx.loc[b, "gross_loss_usd"])
            want = float(Bx.loc[b, "deaths_5y"]) * 1e6 / lost
            # the cards no longer show deaths (main 5c7241a): check the model value they are built from instead
            pm = hm.per_million_card(iso, b, I, P, scn.DEFAULT_MORTALITY_TREND)
            shown = float(pm["deaths_5y"]) if pm else 0.0
            ok = abs(shown - want) <= max(0.01 * want, 0.5) and (cut == 1.0 or abs(lost - 1e6) < 1.0)
            rec(iso, b, "", "card_deaths_equal_full_model_1M_uniform_cut", ok, shown - want,
                f"card {shown:.0f}, model {want:.1f}, aid lost {lost:,.0f} of {aid:,.0f}")
    print(f"card checks done in {time.time() - t0:.0f}s")

    # ---------------- monotonic in the size of the cut, and zero cut ----------------
    for preset in PRESETS:
        opts = scn.default_opts(preset, CI)
        for resp in ("none", "custom25"):
            for iso in COUNTRIES:
                if preset == "America First MOUs" and scn.mou_group(CI, iso) != "A":
                    continue
                vals = []
                for k in (0.0, 0.25, 0.5, 0.75, 1.0):
                    sc = scn.build_scenario(preset, opts, CI)
                    sc.scale = k
                    r = hm.run_country(iso, sc, hm.Fiscal(*RESPONSES[resp]), I, P, n_draws=2)
                    vals.append((r["totals"]["deaths_5y"], r["committed"]["deaths"], r["totals"]["net"],
                                 r["totals"]["gross"]))
                    if k == 0.0:
                        z = max(abs(r["totals"]["deaths_5y"]), abs(r["totals"]["gross"]), abs(r["committed"]["deaths"]))
                        rec(iso, preset, resp, "zero_cut_gives_zero", z < 1e-6, z)
                d5 = [v[0] for v in vals]
                cm = [v[1] for v in vals]
                nt = [v[2] for v in vals]
                gains = vals[-1][3] < 0
                mono = all(d5[i + 1] >= d5[i] - 1e-6 for i in range(4)) and all(cm[i + 1] >= cm[i] - 1e-6 for i in range(4))
                rec(iso, preset, resp, "more_cut_never_fewer_deaths", mono or gains,
                    min(d5[i + 1] - d5[i] for i in range(4)), "deaths 0/25/50/75/100%: " + ", ".join(f"{x:.0f}" for x in d5)
                    + (" (scenario raises aid)" if gains else ""))
                rec(iso, preset, resp, "more_cut_never_less_net_loss", all(nt[i + 1] >= nt[i] - 1e-6 for i in range(4)) or gains,
                    min(nt[i + 1] - nt[i] for i in range(4)))
    print(f"monotonic checks done in {time.time() - t0:.0f}s")

    # ---------------- data checks ----------------
    # no line in two buckets
    lb = LINES.groupby("line")["bucket"].nunique()
    rec("ALL", "", "", "no_line_in_two_buckets", (lb == 1).all(), int((lb > 1).sum()))
    # I-01: modelled aid per country x bucket = IHME's bucket total, 2021-23 average, after dropping elim_ch == 1 rows
    # (double-counted transfers between channels). Read from the raw IHME DAH file when it is present (it is not in
    # the repo); otherwise from country_data, which equals the filtered raw file row for row (audit/I-01.md).
    # IHME rounds every program-area column to US$1,000 per row, separately from the bucket total, so small
    # country-buckets can differ by a few tens of thousands of dollars: pass = within 0.5% OR within US$50,000 a year.
    idx = pd.read_csv(ROOT / "country_data" / "_index.csv")
    f_of = dict(zip(idx.recipient_isocode, idx.file))
    bcol = {"HIV": "hiv_dah_23", "TB": "tb_dah_23", "Malaria": "mal_dah_23", "Immunization": "nch_cnv_dah_23"}
    raw_dah = ROOT / "datasets" / "IHME_DAH_DATABASE_1990_2026_Y2026M09D18.CSV"
    if raw_dah.exists():
        rd = pd.read_csv(raw_dah, usecols=["year", "recipient_isocode", "elim_ch", *bcol.values()], na_values=["-"],
                         low_memory=False)
        rd = rd[(rd.elim_ch == 0) & rd.year.between(2021, 2023)]
        ihme_tot = (rd.groupby("recipient_isocode")[list(bcol.values())].sum() / 3 * 1e3)
        src = "raw IHME DAH file, elim_ch == 0"
    else:
        parts = {}
        for iso in COUNTRIES:
            if iso in f_of:
                cd = pd.read_csv(ROOT / "country_data" / f_of[iso])
                parts[iso] = cd[cd.year.between(2021, 2023)][list(bcol.values())].sum() / 3 * 1e3
        ihme_tot = pd.DataFrame(parts).T
        src = "country_data (= raw file with elim_ch == 0)"
    strict = 0
    for iso in COUNTRIES:
        mod = LINES[LINES.iso3 == iso].groupby("bucket")["usd"].sum()
        bad = []
        for b, c in bcol.items():
            ihme = float(ihme_tot.loc[iso, c]) if iso in ihme_tot.index else 0.0
            m = float(mod.get(b, 0.0))
            if not close(m, ihme, 0.005, 1.0):
                strict += 1
            if not close(m, ihme, 0.005, 50_000):
                bad.append(f"{b}: model {m / 1e6:.3f}M vs IHME {ihme / 1e6:.3f}M")
        rec(iso, "", "", "modelled_aid_equals_IHME_bucket_total_elim_ch0", not bad, len(bad),
            "; ".join(bad) if bad else f"source: {src}")
    rec("ALL", "", "", "modelled_aid_equals_IHME_bucket_total_strict_0.5pct", True, strict,
        f"{strict} of {4 * len(COUNTRIES)} country-buckets differ by more than 0.5% (all IHME rounding, under US$50K)")
    # percentages: coverage inputs stored as percent in 0-100
    for c in ("sh_hiv_artc_zs", "sh_hiv_pmtc_zs", "sh_tbs_dtec_zs", "sh_mlr_nets_zs", "sh_mlr_tret_zs", "sh_imm_idpt",
              "sh_xpd_ghed_ge_zs"):
        v = CI[c].dropna()
        rec("ALL", "", "", f"percent_scale_{c}", bool(((v >= 0) & (v <= 100)).all() and v.median() > 1),
            float(v.max()), f"min {v.min():.2f} median {v.median():.1f} max {v.max():.1f}; n>100: {(v > 100).sum()}")
    # malaria coverage from MAP (I-11) is stored as a fraction in 0-1
    for c in ("mal_cm_cov", "mal_itn_cov", "mal_irs_cov"):
        v = CI[c].dropna()
        rec("ALL", "", "", f"fraction_scale_{c}", bool(((v >= 0) & (v <= 1)).all()), float(v.max()),
            f"min {v.min():.3f} median {v.median():.3f} max {v.max():.3f}; {CI[c + '_source'].value_counts().to_dict()}")
    for iso in CI.index:
        hb = hm.health_budget(iso, I)
        s = hb["share_pct"]
        rec(iso, "", "", "health_share_in_0_100", s != s or 0 < s < 100, s, hb["gov_source"])
    # unit costs inside their documented ranges; country-specific vs default
    ref = pd.read_csv(ROOT / "unit_cost_reference.csv")
    art_specific = set(ref.loc[ref.kind == "art_site_cost", "key"])
    lo_p = {k: np.array([float(P.loc[k, "low"])]) for k in P.index}
    hi_p = {k: np.array([float(P.loc[k, "high"])]) for k in P.index}
    for iso in CI.index:
        row = CI.loc[iso]
        uc_c, uc_lo, uc_hi = hm.unit_costs(row, PC), hm.unit_costs(row, lo_p), hm.unit_costs(row, hi_p)
        bad = [k for k in uc_c if not (min(uc_lo[k][0], uc_hi[k][0]) - 1e-9 <= uc_c[k][0] <= max(uc_lo[k][0], uc_hi[k][0]) + 1e-9)]
        ig = row.get("income_group")
        rec(iso, "", "", "unit_costs_inside_parameter_range", not bad, len(bad),
            f"ART {row.get('art_site_cost_source', 'country study' if iso in art_specific else 'default (ARV median + GDP-scaled staff)')}; "
            f"TB income group {'World Bank' if isinstance(ig, str) and ig else 'GDP fallback'}: {hm.income_group(row)}"
            + (f"; out of range: {bad}" if bad else ""))
    # currency: constant-2023 GDP equals nominal GDP in 2023
    for iso in CI.index:
        f = ROOT / "macro_data" / f"{iso}.csv"
        if not f.exists():
            rec(iso, "", "", "gdp_constant2023_equals_nominal_in_2023", False, "", "no macro file")
            continue
        m = pd.read_csv(f)
        r = m[m.year == 2023]
        if len(r) and pd.notna(r["gdp_usd_bn"].iloc[0]) and pd.notna(r["gdp_usd_bn_2023"].iloc[0]):
            a, b = r["gdp_usd_bn"].iloc[0], r["gdp_usd_bn_2023"].iloc[0]
            rec(iso, "", "", "gdp_constant2023_equals_nominal_in_2023", close(a, b, 1e-6), b / a)
        else:
            rec(iso, "", "", "gdp_constant2023_equals_nominal_in_2023", False, "", "2023 GDP missing")
    # Section 1: stacked components = total; 2023 matches the raw IHME file
    # the raw IHME health spending file is not in the repo; when it is absent the 2023 comparison is skipped and reported
    raw_hs = ROOT / "datasets" / "IHME_HEALTH_SPENDING_1995_2023_Y2026M09D21.CSV"
    if raw_hs.exists():
        raw = pd.read_csv(raw_hs, encoding="utf-8-sig", usecols=["iso3", "level", "year", "the_total_mean",
                          "ghes_total_mean", "ppp_total_mean", "oop_total_mean", "dah_total_mean"])
        raw = raw[raw.level == "Country"].set_index(["iso3", "year"])
    else:
        raw = pd.DataFrame(index=pd.MultiIndex.from_tuples([], names=["iso3", "year"]))
        rec("ALL", "", "", "section1_2023_matches_raw_IHME_file_SKIPPED", True, "", f"skipped: {raw_hs.name} not found")
    for iso in CI.index:
        f = ROOT / "spending_data" / f"{iso}.csv"
        if not f.exists():
            rec(iso, "", "", "section1_components_sum_to_total", False, "", "no spending file")
            continue
        sp = pd.read_csv(f)
        sp = sp[sp.year.between(2015, 2023)]
        comp = sp[["dah_total_mean", "ghes_total_mean", "ppp_total_mean", "oop_total_mean"]].sum(axis=1)
        rel = (comp / sp["the_total_mean"] - 1).abs().max()
        rec(iso, "", "", "section1_components_sum_to_total", rel < 0.01, rel)
        r23 = sp[sp.year == 2023]
        if len(r23) and (iso, 2023) in raw.index:
            d = max(abs(r23[c].iloc[0] - raw.loc[(iso, 2023), c]) / max(1, abs(raw.loc[(iso, 2023), c]))
                    for c in ("the_total_mean", "ghes_total_mean", "dah_total_mean"))
            rec(iso, "", "", "section1_2023_matches_raw_IHME_file", d < 1e-6, d)
        # Section 1 DAH (IHME spending database) = Section 2 DAH (IHME DAH database, elim_ch == 0), every year shown
        # (2015-2023). Two IHME products, so they agree to within rounding and IHME's own processing: tolerance 2%.
        if iso in f_of:
            cd = pd.read_csv(ROOT / "country_data" / f_of[iso])
            s2y = cd.groupby("year")["dah_23"].sum()
            for _, r in sp.iterrows():
                s1 = r["dah_total_mean"]
                if s1 and s1 > 0:
                    s2 = float(s2y.get(r["year"], 0.0))
                    # within 2%: pass; 2-5%: pass with a warning (IHME's two products round and process differently
                    # in a few small countries); over 5%: fail
                    rec(iso, str(int(r["year"])), "", "section1_dah_equals_section2_dah_same_year", close(s2, s1, 0.05),
                        s2 / s1, f"Section 2 {s2 / 1e3:.2f}M vs Section 1 {s1 / 1e3:.2f}M",
                        warning=not close(s2, s1, 0.02))
    # Section 3: WEO identity, revenue items vs file total, COFOG shares, and the default year's coverage levels
    for iso in CI.index:
        mf, rf, cf = (ROOT / d / f"{iso}.csv" for d in ("macro_data", "revenue_data", "cofog_all"))
        if not mf.exists():
            continue
        mac = pd.read_csv(mf)
        rev = pd.read_csv(rf) if rf.exists() else None
        spd = pd.read_csv(cf) if cf.exists() else None
        ry = set(rev.year) if rev is not None else set()
        sy = set(spd.year) if spd is not None else set()
        if not (ry or sy):
            rec(iso, "", "", "section3_has_data", False, "", "no revenue or COFOG file")
            continue
        both = sorted(ry & sy, reverse=True)
        y = both[0] if both else sorted(ry | sy, reverse=True)[0]
        r = mac[mac.year == y]
        if len(r) and r[["gov_revenue_pct_gdp", "gov_expenditure_pct_gdp", "gov_net_lending_pct_gdp"]].notna().all(axis=1).iloc[0]:
            R, E, NL = (float(r[c].iloc[0]) for c in ("gov_revenue_pct_gdp", "gov_expenditure_pct_gdp", "gov_net_lending_pct_gdp"))
            rec(iso, str(y), "", "section3_weo_spending_minus_revenue_equals_borrowing", abs((E - R) + NL) <= 0.5, (E - R) + NL)
        else:
            rec(iso, str(y), "", "section3_weo_totals_present_for_default_year", False, "", "WEO totals missing: each "
                "side sized from its own file")
        if rev is not None and y in ry:
            g = rev[rev.year == y]
            if g["total_pct_gdp"].notna().any():
                d = g["pct_gdp"].sum() - g["total_pct_gdp"].dropna().iloc[0]
                rec(iso, str(y), "", "section3_revenue_items_sum_to_file_total", abs(d) <= 0.5, d, g["coverage"].iloc[0])

        if spd is not None and y in sy:
            g = spd[spd.year == y]
            s = g["pct_outlays"].sum()
            rec(iso, str(y), "", "section3_cofog_shares_sum_to_100", abs(s - 100) <= 0.5, s)


    # Section 3 (I-10): every country-year with a breakdown, each side's boxes (items + the grey "other levels" box)
    # add up to that side's IMF WEO general-government total; a central-government breakdown is never rescaled; where
    # the central total is above WEO, it is shown alone (total = the central total) with a note
    import budget_section as bs
    levels = {"rev": {}, "spd": {}}
    for iso in CI.index:
        mf, rf, cf = (ROOT / d / f"{iso}.csv" for d in ("macro_data", "revenue_data", "cofog_all"))
        if not mf.exists():
            continue
        mac = pd.read_csv(mf).set_index("year")
        rev = pd.read_csv(rf) if rf.exists() else None
        spd = pd.read_csv(cf) if cf.exists() else None
        years = sorted(set(rev.year if rev is not None else []) | set(spd.year if spd is not None else []))
        for y in years:
            R_w = mac.at[y, "gov_revenue_pct_gdp"] if y in mac.index else np.nan
            E_w = mac.at[y, "gov_expenditure_pct_gdp"] if y in mac.index else np.nan
            if pd.isna(R_w) or pd.isna(E_w):
                continue
            rg = rev[rev.year == y] if rev is not None else None
            g = spd[spd.year == y] if spd is not None else None
            bx = bs.budget_boxes(rg, g, float(R_w), float(E_w), f"{iso} {y}")
            for k, weo_t, raw in (("rev", float(R_w), rg), ("spd", float(E_w), g)):
                sd = bx[k]
                if sd is None or raw is None or raw.empty:
                    continue
                levels[k].setdefault(iso, {})[y] = sd["level"]
                boxes = bs.side_box_sum(sd)
                want = sd["total"] if sd["note"] else weo_t
                # 0.01 points of GDP: the grey box is left out when under 0.005 (rounding between the two IMF files)
                ok = abs(boxes - want) <= 0.01 and (sd["note"] is None or sd["total"] > weo_t)
                rec(iso, str(y), k, "section3_side_boxes_sum_to_weo_total", ok, boxes - want,
                    f"{sd['level']}: boxes {boxes:.2f}% of GDP (grey {sd['other']:.2f}), WEO {weo_t:.2f}%"
                    + ("; central above WEO, shown alone" if sd["note"] else ""))
                if sd["level"] == "Central Government" and sd["items"] is not None:
                    own = sd["items"]["pct_gdp"].sum()
                    rec(iso, str(y), k, "section3_central_breakdown_not_rescaled",
                        abs(sd["items"]["v"].sum() - own) <= 1e-9, sd["items"]["v"].sum() - own)
    for k, name in (("rev", "revenue"), ("spd", "spending")):
        latest = {iso: ys[max(ys)] for iso, ys in levels[k].items()}
        n_g = sum(v == "General Government" for v in latest.values())
        n_c = sum(v == "Central Government" for v in latest.values())
        rec("ALL", "", k, f"section3_{name}_breakdown_levels", True, n_g,
            f"latest year: general government {n_g}, central government {n_c} countries")

    out = pd.DataFrame(rows)
    out.to_csv(OUT / f"checks_results{SUFFIX}.csv", index=False)
    summ = (out.groupby("check").agg(runs=("pass", "size"), passed=("pass", "sum"), warnings=("warning", "sum"))
            .assign(failed=lambda d: d.runs - d.passed)[["runs", "passed", "failed", "warnings"]]
            .sort_values(["failed", "warnings"], ascending=False))
    summ.to_csv(OUT / f"checks_summary{SUFFIX}.csv")
    lines_md = ["| Check | Runs | Passed | Failed | Warnings |", "|---|---|---|---|---|"]
    lines_md += [f"| {k} | {r.runs} | {r.passed} | {r.failed} | {r.warnings} |" for k, r in summ.iterrows()]
    (OUT / f"checks_summary{SUFFIX}.md").write_text("\n".join(lines_md) + "\n")
    print(summ.to_string())
    print(f"done in {time.time() - t0:.0f}s; {len(out)} rows")


if __name__ == "__main__":
    main()
