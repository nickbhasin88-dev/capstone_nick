"""Tests for audit fix I-07: user-set Gavi and Global Fund cuts in the shortfalls preset. Run:  python -m pytest tests"""
import logging
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
logging.disable(logging.WARNING)
import health_model as hm  # noqa: E402
import model_section as ms  # noqa: E402
import scenarios as scn  # noqa: E402

I, P = hm.load_inputs(), hm.load_params()
CI = I["ci"]
NONE = hm.Fiscal(*scn.DEFAULT_FISCAL)
SF = scn.SHORTFALLS


def test_defaults_are_gavi_15_global_fund_20():
    assert scn.default_opts(SF, CI) == {"gavi_cut": 15, "gf_cut": 20}
    for opts in ({}, None, scn.default_opts(SF, CI)):
        sc = scn.build_scenario(SF, opts, CI)
        assert sc.chan == {"Gavi": 0.15, "Global Fund": 0.20}
        # a channel cut for every source donor only: no donor-level or US multilateral cut on top
        assert not sc.src_direct and not sc.src_multi and not sc.pair


@pytest.mark.parametrize("iso", ["KEN", "NGA", "MOZ", "HND"])
@pytest.mark.parametrize("gavi, gf", [(15, 20), (0, 50), (37, 0), (0, 0)])
def test_aid_lost_is_the_cut_times_each_funds_baseline(iso, gavi, gf):
    """Sudden cut, no response: aid lost = Gavi cut x Gavi-channel baseline + Global Fund cut x its baseline, all
    source donors (US included once), and nothing from any other channel."""
    L = I["lines"][I["lines"].iso3 == iso]
    exp = gavi / 100 * L.loc[L.chan_grp == "Gavi", "usd"].sum() + gf / 100 * L.loc[L.chan_grp == "Global Fund", "usd"].sum()
    r = hm.run_country(iso, scn.build_scenario(SF, {"gavi_cut": gavi, "gf_cut": gf}, CI), NONE, I, P, n_draws=0)
    assert r["totals"]["gross"] == pytest.approx(exp, rel=1e-9, abs=1e-3)
    if gavi == 0 and gf == 0:
        assert r["totals"]["deaths_5y"] == 0


def test_us_gavi_money_is_cut_once():
    L = I["lines"][I["lines"].iso3 == "KEN"]
    us_gavi = L.loc[(L.chan_grp == "Gavi") & (L.src_grp == "United States"), "usd"].sum()
    assert us_gavi > 0
    sc = scn.build_scenario(SF, {"gavi_cut": 15, "gf_cut": 0}, CI)
    cells = L[L.chan_grp == "Gavi"][["src_grp", "chan_grp", "bucket"]]
    assert set(sc.cuts(cells, "KEN", I["trend_map"]).round(12)) == {0.15}


def test_labels_reflect_the_chosen_values():
    opts = {"gavi_cut": 15, "gf_cut": 20}
    assert scn.shortfall_label(opts) == "Gavi −15% · Global Fund −20%"
    assert scn.shortfall_label(None) == "Gavi −15% · Global Fund −20%"
    assert ms.scenario_title(SF, {"gavi_cut": 24, "gf_cut": 30}).endswith("Gavi −24% · Global Fund −30%")
    assert ms.scenario_phrase(SF, opts) == "If Gavi funding falls 15% and Global Fund funding 20%"
    assert ms.scenario_phrase(SF, {"gavi_cut": 0, "gf_cut": 20}) == "If Global Fund funding falls 20%"
    assert ms.scenario_phrase(SF, {"gavi_cut": 10, "gf_cut": 0}) == "If Gavi funding falls 10%"
    assert "Selected: Gavi −15% · Global Fund −20%." in scn.preset_description(SF, opts)
    # other presets are unchanged
    assert ms.scenario_title("Full US exit", opts) == ms.title_case("US Bilateral Exit + Multilateral Withdrawals")
    assert ms.scenario_phrase("Full US exit") == ms.SCENARIO_PHRASE["Full US exit"]


def test_sliders_cover_0_to_50_with_defaults_in_range():
    for k, (label, default, marks, tip) in ms.SHORTFALL_SLIDERS.items():
        assert 0 <= default <= 50 and marks and ("Sources:" in tip or "KFF" in tip)
    assert ms.SHORTFALL_SLIDERS["gavi_cut"][1] == 15 and ms.SHORTFALL_SLIDERS["gf_cut"][1] == 20


def test_precomputed_file_uses_the_defaults():
    """The All Countries file for this preset was built with the default cuts (Kenya's row matches a live run)."""
    import pandas as pd
    A = pd.read_csv(scn.precomputed_path(hm.MODEL_DIR, SF)).set_index("iso3")
    r = hm.run_country("KEN", scn.build_scenario(SF, scn.default_opts(SF, CI), CI), NONE, I, P,
                       n_draws=scn.ALL_COUNTRY_DRAWS, mortality_trend=scn.DEFAULT_MORTALITY_TREND)
    assert A.loc["KEN", "gross_loss_usd"] == pytest.approx(r["totals"]["gross"], rel=1e-9)
    assert A.loc["KEN", "deaths_5y"] == pytest.approx(r["totals"]["deaths_5y"], rel=1e-9)
