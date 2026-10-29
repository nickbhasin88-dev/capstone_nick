"""Merge checks (audit/merge/PLAN.md, Step 3 a-d): tomato's deaths logic on main's model, for every country and preset.

a. deaths are never negative, and are zero when no aid is cut (a zero funding path) and on every line with no loss;
b. coverage after the cut is never below zero, and people losing a service never exceed the people covered, in the
   2026-2030 average and in every year;
c. the service table's deaths add up to the run total (rows shown + the lines it leaves out, which carry none);
d. units and years: model years 2026-2030, money as yearly averages of the per-year values, deaths as the five-year sum.
"""
import logging

import numpy as np
import pytest

import health_model as hm
import model_section as ms
import scenarios as scn

logging.disable(logging.WARNING)
I, P = hm.load_inputs(), hm.load_params()
CI = I["ci"]
COUNTRIES = [c for c in CI.index if c in set(I["lines"].iso3)]
RESPONSES = {"none": scn.DEFAULT_FISCAL, "custom25": ("custom", 0.25, True, "pro_rata", "p75"),
             "max_lives": ("max", 0.0, True, "lives_first", "p75")}
N_DRAWS = 50
TOL = 1e-6


def runs(preset, fk, **kw):
    sc = scn.build_scenario(preset, scn.default_opts(preset, CI), CI)
    for iso in COUNTRIES:
        if sc.mou_only and iso not in sc.us_direct_path_by_country:
            continue
        yield iso, hm.run_country(iso, sc, hm.Fiscal(*RESPONSES[fk]), I, P, n_draws=N_DRAWS, seed=7, **kw)


@pytest.mark.parametrize("fk", list(RESPONSES))
@pytest.mark.parametrize("preset", scn.PRESETS)
def test_deaths_coverage_and_table(preset, fk):
    for iso, r in runs(preset, fk):
        L, T = r["lines"], r["totals"]
        # a: never negative (central, range, first year, per year)
        for c in ("deaths_y1", "deaths_5y", "deaths_5y_lo", "deaths_5y_hi"):
            assert (L[c].fillna(0) >= -TOL).all(), (iso, preset, fk, c, L.loc[L[c] < -TOL, ["line", c]])
            assert T[c] >= -TOL, (iso, preset, fk, c, T[c])
        assert (r["years"]["deaths"] >= -TOL).all(), (iso, preset, fk)
        assert r["committed"]["deaths"] >= -TOL, (iso, preset, fk)
        # a: a line that loses nothing (and has no lost people) adds no deaths
        none = L[(L["net_loss_usd"].abs() < 0.5) & (L["units_lost"].fillna(0) <= TOL)]
        assert (none["deaths_5y"].fillna(0).abs() <= 1e-6).all(), (iso, preset, fk, none[["line", "deaths_5y"]])
        # b: coverage never below 0; people losing a service never above people covered (average and every year)
        cov = L[L["cov0"].notna() & (L["need"] > 0)]
        covered = cov["need"] * cov["cov0"]
        for c in ["units_lost"] + [f"units_lost_{y}" for y in range(hm.YEAR0, hm.YEAR0 + hm.N_YEARS)]:
            assert (cov[c].fillna(0) <= covered * (1 + 1e-9) + 1e-6).all(), (iso, preset, fk, c)
        for c in ["cov_drop_pp"] + [f"cov_drop_pp_{y}" for y in range(hm.YEAR0, hm.YEAR0 + hm.N_YEARS)]:
            assert (cov["cov0"] - cov[c].fillna(0) / 100 >= -1e-9).all(), (iso, preset, fk, c)
        # c: the table's rows plus the lines it leaves out add up to the run total; left-out lines carry no deaths
        show = L[(L["base_usd"] > 0) | (L["net_loss_usd"] != 0)]
        rows = ms._service_rows(show)
        left_out = L[~L["line"].isin(rows["line"])]
        assert abs(left_out["deaths_5y"].fillna(0).sum()) <= 1e-6, (iso, preset, fk, left_out["line"].tolist())
        assert abs(rows["deaths_5y"].sum() - T["deaths_5y"]) <= 1e-6 * max(1.0, T["deaths_5y"]), (iso, preset, fk)
        # d: years 2026-2030; deaths = sum of the yearly deaths; money = average of the yearly values
        Y = r["years"]
        assert Y["year"].tolist() == list(range(2026, 2031))
        assert abs(Y["deaths"].sum() - T["deaths_5y"]) <= 1e-6 * max(1.0, T["deaths_5y"]), (iso, preset, fk)
        assert abs(Y["gap_usd"].mean() - T["net"]) <= 1e-6 * max(1.0, T["net"]), (iso, preset, fk)
        yearly = L[[f"net_loss_{y}" for y in range(2026, 2031)]].mean(axis=1)
        assert np.allclose(yearly, L["net_loss_usd"], rtol=1e-9, atol=1e-3), (iso, preset, fk)


@pytest.mark.parametrize("preset", scn.PRESETS)
def test_zero_cut_zero_deaths(preset):
    for iso, r in runs(preset, "none", cut_path=[0] * 5):
        assert abs(r["totals"]["deaths_5y"]) < 1e-9 and abs(r["committed"]["deaths"]) < 1e-9, (iso, preset)
        assert (r["lines"]["deaths_5y"].fillna(0).abs() < 1e-9).all(), (iso, preset)


def test_table_labels_years_and_units():
    iso = "KEN"
    sc = scn.build_scenario("Full US exit", scn.default_opts("Full US exit", CI), CI)
    r = hm.run_country(iso, sc, hm.Fiscal(*scn.DEFAULT_FISCAL), I, P, n_draws=N_DRAWS, seed=7)
    L = r["lines"]
    rows = ms._service_rows(L[(L["base_usd"] > 0) | (L["net_loss_usd"] != 0)])
    h = ms._service_table_html(rows, "Kenya", r["totals"], {b: 0.0 for b in hm.BUCKETS})
    assert "Extra Deaths, 2026-2030 Total" in h and "People Losing Service, per Year" in h
    assert ms.num(rows["deaths_5y"].sum()) in h                 # the Total row shows the sum of the rows
    assert hm.YEAR0 == 2026 and hm.N_YEARS == 5
