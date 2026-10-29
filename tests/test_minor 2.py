"""Tests for audit fixes I-13, I-14, I-15 and I-16. Run:  python -m pytest tests"""
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
logging.disable(logging.WARNING)
import health_model as hm  # noqa: E402
import model_section as ms  # noqa: E402
import scenarios as scn  # noqa: E402

I, P = hm.load_inputs(), hm.load_params()
CI = I["ci"]
NONE = hm.Fiscal(*scn.DEFAULT_FISCAL)
IHME = scn.build_scenario("IHME 2025 preliminary estimates", {}, CI)
COUNTRIES = [c for c in CI.index if c in set(I["lines"].iso3)]


# ---------------- I-16: parameter editor ----------------
def test_low_equals_high_is_a_constant_and_runs():
    for p in ("uc_imm", "continuity", "art_hazard_mult"):
        t = P.copy()
        t.loc[p, ["low", "high"]] = t.loc[p, "central"]
        d = hm.draw_params(t, 50)
        assert d[p].shape == (50,) and np.all(d[p] == t.loc[p, "central"])
        assert hm.validate_params(t) == []
        r = hm.run_country("KEN", scn.build_scenario("Full US exit", {}, CI), NONE, I, t, n_draws=50)
        assert np.isfinite(r["totals"]["deaths_5y"])


def test_low_above_high_is_rejected():
    t = P.copy()
    t.loc["uc_imm", ["low", "high"]] = [120.0, 40.0]
    msg = hm.validate_params(t)
    assert len(msg) == 1 and "uc_imm" in msg[0] and "above high" in msg[0]


def test_central_outside_range_is_rejected():
    t = P.copy()
    t.loc["continuity", "central"] = 0.9                       # range is 0-0.35
    msg = hm.validate_params(t)
    assert len(msg) == 1 and "continuity" in msg[0] and "outside" in msg[0]


def test_other_draws_unchanged_when_one_parameter_is_fixed():
    t = P.copy()
    t.loc["uc_imm", ["low", "high"]] = t.loc["uc_imm", "central"]
    a, b = hm.draw_params(P, 100), hm.draw_params(t, 100)
    # fixing a parameter must not shift the random stream for the parameters after it
    later = list(P.index)[list(P.index).index("uc_imm") + 1:]
    assert all(np.array_equal(a[k], b[k]) for k in later)


# ---------------- I-15: scenarios that raise aid ----------------
def test_pts_formatter_never_shows_double_sign():
    assert ms._pts(6.6) == "−6.6 pts"
    assert ms._pts(-6.6) == "+6.6 pts"
    assert ms._pts(-12.4) == "+12 pts"
    assert "−-" not in ms._pts(-0.4) and "--" not in ms._pts(-0.4)


@pytest.mark.parametrize("iso", COUNTRIES)
def test_no_negative_losses_under_aid_rises(iso):
    r = hm.run_country(iso, IHME, NONE, I, P, n_draws=20)
    L, B, T = r["lines"], r["buckets"], r["totals"]
    assert (L["units_lost"].fillna(0) >= 0).all() and (L["net_loss_usd"] >= -1e-6).all() and (L["deaths_5y"] >= -1e-9).all()
    assert (L["cov_drop_pp"].fillna(0) >= 0).all()
    assert (B["gross_loss_usd"] >= -1e-6).all() and (B["gains_usd"] >= 0).all()
    assert abs(B["gross_loss_usd"].sum() - T["gross"]) <= max(1.0, 1e-9 * T["gross"])
    care, _ = ms.care_breakdown(L.set_index("line"))
    rows = ms._service_rows(L[(L["base_usd"] > 0) | (L["net_loss_usd"] != 0)])
    assert abs(care - rows.loc[rows["line"] != "hiv_prev", "units_lost"].sum()) < 1.0
    assert abs(rows["deaths_5y"].sum() - T["deaths_5y"]) < 1e-6


def test_gain_note_under_the_disease():
    r = hm.run_country("KHM", IHME, NONE, I, P, n_draws=20)
    B = r["buckets"].set_index("bucket")
    assert B.loc["Immunization", "gains_usd"] > 0
    L = r["lines"]
    html = ms._service_table_html(ms._service_rows(L[(L["base_usd"] > 0) | (L["net_loss_usd"] != 0)]), "Cambodia",
                                  r["totals"], {b: float(B.loc[b, "gains_usd"]) for b in hm.BUCKETS})
    assert "Aid to immunization rises by" in html and "gains aren&#x27;t modelled" in html
    assert "−-" not in html and "+-" not in html


# ---------------- I-13: fiscal panel ----------------
@pytest.mark.parametrize("path", [None, (0.2, 0.4, 0.6, 0.8, 1.0)])
@pytest.mark.parametrize("fiscal", [scn.DEFAULT_FISCAL, ("custom", 0.25, True, "pro_rata", "p75")])
def test_fiscal_gap_values_match_headline(path, fiscal):
    r = hm.run_country("KEN", scn.build_scenario("Full US exit", {}, CI), hm.Fiscal(*fiscal), I, P, n_draws=20,
                       cut_path=path)
    avg, y30, show = ms.fiscal_gap_values(r)
    assert abs(avg["left"] - r["totals"]["net"]) < 1e-6
    assert abs(avg["gap"] - (avg["filled"] + avg["left"])) < 1e-6 and abs(y30["gap"] - (y30["filled"] + y30["left"])) < 1e-6
    assert show == (path is not None)


# ---------------- I-14: one health-share definition ----------------
def test_health_share_prefers_world_bank_latest_year():
    for iso in ("KEN", "NGA", "HND"):
        hs = hm.health_share(iso)
        h = hm._share_history()
        h = h[h.iso3 == iso].sort_values("year")
        assert not hs["estimated"] and hs["year"] == int(h["year"].iloc[-1])
        assert hs["share_pct"] == pytest.approx(float(h["share"].iloc[-1]))
        b = hm.health_budget(iso, I)
        assert b["share_pct"] == hs["share_pct"]
        assert b["gov_spend_usd"] == pytest.approx(CI.loc[iso, "ghes_2023"] / (hs["share_pct"] / 100))
        assert hm.fiscal_space(CI.loc[iso])["ghes_pct_gov_spend"] == hs["share_pct"]


def test_health_share_estimated_when_world_bank_missing(monkeypatch):
    h = hm._share_history()
    monkeypatch.setattr(hm._share_history, "cache", h[h.iso3 != "KEN"])
    monkeypatch.setattr(hm.health_share, "cache", {}, raising=False)
    hs = hm.health_share("KEN")
    assert hs["estimated"] and hs["year"] == 2023
    sp = pd.read_csv(hm.HERE / "spending_data" / "KEN.csv").set_index("year")
    mac = pd.read_csv(hm.HERE / "macro_data" / "KEN.csv").set_index("year")
    exp = sp.loc[2023, "ghes_total_mean"] * 1e3 / (mac.loc[2023, "gov_expenditure_pct_gdp"] / 100
                                                   * mac.loc[2023, "gdp_usd_bn_2023"] * 1e9) * 100
    assert hs["share_pct"] == pytest.approx(exp)
