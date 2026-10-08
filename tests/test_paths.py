"""Tests for year-varying cut and government-money paths (health_model.run_country). Run:  python -m pytest tests"""
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
logging.disable(logging.WARNING)
import health_model as hm  # noqa: E402
import scenarios as scn  # noqa: E402
from make_baseline import COUNTRIES, FISCALS, N_DRAWS, snapshot  # noqa: E402

I, P = hm.load_inputs(), hm.load_params()
BASE = json.loads((Path(__file__).parent / "baseline_sudden.json").read_text())
NONE = hm.Fiscal(*scn.DEFAULT_FISCAL)


def run(iso, preset="Full US exit", fiscal=NONE, **kw):
    sc = scn.build_scenario(preset, scn.default_opts(preset, I["ci"]), I["ci"])
    return hm.run_country(iso, sc, fiscal, I, P, n_draws=N_DRAWS, **kw)


def close(a, b):
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= 1e-6 * max(1.0, abs(a), abs(b))


# (a) default paths reproduce the original sudden-cut results, for 5 countries, every preset and 3 responses
@pytest.mark.parametrize("key", sorted(BASE))
def test_default_path_reproduces_original(key):
    iso, preset, fk = key.split("|")
    sc = scn.build_scenario(preset, scn.default_opts(preset, I["ci"]), I["ci"])
    for kw in ({}, {"cut_path": [1] * 5, "gov_add_usd": [0] * 5}):        # implicit and explicit defaults
        got = snapshot(hm.run_country(iso, sc, hm.Fiscal(*FISCALS[fk]), I, P, n_draws=N_DRAWS, **kw))
        exp = BASE[key]
        for l, cols in exp["lines"].items():
            for c, v in cols.items():
                assert close(got["lines"][l][c], v), (key, l, c, got["lines"][l][c], v)
        for k, v in exp["totals"].items():
            assert close(got["totals"][k], v), (key, k, got["totals"][k], v)
        for b, v in exp["path"].items():
            assert all(close(x, y) for x, y in zip(got["path"][b], v)), (key, b)


# (b) a zero cut path gives zero deaths
@pytest.mark.parametrize("iso", COUNTRIES)
def test_zero_path_zero_deaths(iso):
    r = run(iso, cut_path=[0] * 5)
    assert abs(r["totals"]["deaths_5y"]) < 1e-9 and abs(r["committed"]["deaths"]) < 1e-9


# (c) same final cut, slower path -> fewer committed deaths
@pytest.mark.parametrize("iso", COUNTRIES)
def test_slower_path_fewer_committed_deaths(iso):
    sudden = run(iso)["committed"]["deaths"]
    linear = run(iso, cut_path=[0.2, 0.4, 0.6, 0.8, 1.0])["committed"]["deaths"]
    back = run(iso, cut_path=[0.04, 0.16, 0.36, 0.64, 1.0])["committed"]["deaths"]
    assert linear <= sudden + 1e-6 and back <= linear + 1e-6
    if sudden > 10:                       # strictly fewer wherever the cut causes deaths
        assert linear < sudden


# (d) extra government money >= aid lost every year -> zero deaths
@pytest.mark.parametrize("iso", COUNTRIES)
def test_full_government_money_zero_deaths(iso):
    G = run(iso)["totals"]["gross_full"]
    r = run(iso, gov_add_usd=[G * 1.01] * 5)
    assert abs(r["totals"]["deaths_5y"]) < 1e-6 and abs(r["committed"]["deaths"]) < 1e-6


# (e) a cut that starts in 2030: few 2026-2030 deaths, but HIV-treatment committed deaths match a 2026 cut of the same size
@pytest.mark.parametrize("iso", COUNTRIES)
def test_late_cut_committed(iso):
    early, late = run(iso), run(iso, cut_path=[0, 0, 0, 0, 1])
    assert late["totals"]["deaths_5y"] < 0.5 * early["totals"]["deaths_5y"] + 1e-9
    # people off ART: the 2030 cohort is followed for its own 5 years, so it commits the same deaths as the 2026 cohort
    hiv_early = early["lines"].set_index("line").loc["hiv_art", "deaths_5y"] + 0.0
    hiv_late = late["committed"]["after_2030"] + late["lines"].set_index("line").loc["hiv_art", "deaths_5y"]
    assert abs(hiv_late - hiv_early) <= 1e-6 * max(1.0, hiv_early)
    # returning to care averts deaths: a cut in force 2026-2027 only, then restored, commits fewer HIV deaths
    temp = run(iso, cut_path=[1, 1, 0, 0, 0])
    hiv_temp = temp["committed"]["after_2030"] + temp["lines"].set_index("line").loc["hiv_art", "deaths_5y"]
    assert hiv_temp <= hiv_early + 1e-6


# (f) TB, malaria and immunization deaths in a year depend only on that year's net gap
@pytest.mark.parametrize("iso", COUNTRIES)
def test_year_by_year_services_ignore_later_years(iso):
    a = hm.run_country(iso, scn.build_scenario("Full US exit", {}, I["ci"]), NONE, I, P, n_draws=20, keep_draws=True,
                       cut_path=[0.3, 0.5, 0.7, 0.9, 1.0])
    b = hm.run_country(iso, scn.build_scenario("Full US exit", {}, I["ci"]), NONE, I, P, n_draws=20, keep_draws=True,
                       cut_path=[0.3, 0.5, 0.7, 0.2, 0.0])
    for l in ("tb_ds", "tb_dr", "mal_itn", "mal_irs", "mal_cm", "imm", "hiv_pmtct"):
        assert np.allclose(a["draws"]["deaths"][l][:, :3], b["draws"]["deaths"][l][:, :3]), l
        assert np.allclose(a["draws"]["units"][l][:, :3], b["draws"]["units"][l][:, :3]), l


# break-even: the returned rise keeps up in every year, and a slightly smaller one doesn't
@pytest.mark.parametrize("iso", COUNTRIES)
@pytest.mark.parametrize("path", [[1] * 5, [0.2, 0.4, 0.6, 0.8, 1.0]])
def test_break_even_share(iso, path):
    sc = scn.build_scenario("Full US exit", {}, I["ci"])
    s = hm.break_even_share(iso, sc, NONE, I, path)
    hb = hm.health_budget(iso, I)
    steps = np.arange(1, 6)
    if s is None:                         # even the fastest rise that stays under 15% falls short in some year
        fastest = hm.gov_add_from_points(hb["room_pct"] / 5 * steps, hb["gov_spend_usd"])
        assert (fastest < run(iso, cut_path=path)["years"]["gap_usd"].values - 1e-6).any()
        return
    r = run(iso, cut_path=path, gov_add_usd=hm.gov_add_from_points(s * steps, hb["gov_spend_usd"]))
    assert r["years"]["gap_usd"].max() <= 1e-3 * max(1.0, r["totals"]["gross_full"]) and r["totals"]["deaths_5y"] < 1e-6
    if s > 0.01:
        r2 = run(iso, cut_path=path, gov_add_usd=hm.gov_add_from_points(0.95 * s * steps, hb["gov_spend_usd"]))
        assert r2["years"]["gap_usd"].max() > 0
