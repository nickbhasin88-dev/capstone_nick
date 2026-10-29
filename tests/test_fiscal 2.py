"""Tests for audit fixes I-26 (interest data for the debt-stress factor) and I-17 (data years).
Run:  python -m pytest tests"""
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
logging.disable(logging.WARNING)
import fiscal_inputs as fi  # noqa: E402
import health_model as hm  # noqa: E402
import model_section as ms  # noqa: E402
import prepare_model as pm  # noqa: E402

I = hm.load_inputs()
CI = I["ci"]
ISOS = sorted(set(I["lines"].iso3))


def test_every_country_has_interest_and_stress_is_never_a_silent_1():
    assert CI["interest_pct_revenue"].notna().all()
    for iso in ISOS:
        F = hm.fiscal_space(CI.loc[iso])
        want = float(np.clip(1 - (CI.loc[iso, "interest_pct_revenue"] - 10) / 40, 0.25, 1))
        assert F["stress_factor"] == pytest.approx(want)
    row = CI.loc["KEN"].copy()
    row["interest_pct_revenue"] = np.nan
    with pytest.raises(ValueError):
        hm.fiscal_space(row)


def test_imf_net_interest_formula_and_actual_years():
    w = pd.read_csv(fi.OUT)
    k = w[(w.iso3 == "KEN") & (w.year == 2024)].iloc[0]
    assert k["net_interest_pct_revenue"] == pytest.approx((k["GGXONLB_NGDP"] - k["GGXCNL_NGDP"]) / k["GGR_NGDP"] * 100)
    assert (w.loc[w["actual"], "year"] < w.loc[w["actual"], "first_estimate_year"]).all()
    assert set(w["source"]) == {fi.SOURCE}


def test_imf_net_interest_is_primary_and_the_world_bank_fallback_is_flagged():
    """Batch 7 item 7 (L-34): the IMF WEO net-interest definition is used wherever it exists (every dashboard
    country); the World Bank gross-interest value is used only where the IMF value is missing, and then
    flag_interest_alt_def marks the different definition. Replaces the pre-Batch-7 'more recent source wins' test."""
    for iso, r in CI.iterrows():
        if pd.notna(r["interest_imf"]):
            assert r["interest_pct_revenue_source"] == fi.IMF_LABEL, iso
            assert r["interest_pct_revenue"] == pytest.approx(r["interest_imf"]), iso
            assert not bool(r["flag_interest_alt_def"]), iso
    assert CI.loc["PAK", "interest_pct_revenue_source"] == fi.IMF_LABEL        # previously missing
    # a country whose IMF value is missing keeps the World Bank value, flagged
    ci = CI.copy()
    real_latest = fi.imf_latest
    fi.imf_latest = lambda idx: real_latest(idx).assign(
        net_interest_pct_revenue=lambda d: d["net_interest_pct_revenue"].where(d.index != "KEN"))
    try:
        out = fi.apply(ci)
    finally:
        fi.imf_latest = real_latest
    assert out.loc["KEN", "interest_pct_revenue_source"] == fi.WB_LABEL
    assert out.loc["KEN", "interest_pct_revenue"] == pytest.approx(CI.loc["KEN", "gc_xpn_intp_rv_zs"])
    assert bool(out.loc["KEN", "flag_interest_alt_def"]) and not bool(out.loc["UGA", "flag_interest_alt_def"])


def test_income_group_median_when_both_missing():
    ci = CI.copy()
    ci.loc["KEN", ["gc_xpn_intp_rv_zs", "gc_xpn_intp_rv_zs_year"]] = np.nan
    real_latest = fi.imf_latest
    fi.imf_latest = lambda idx: real_latest(idx).assign(
        net_interest_pct_revenue=lambda d: d["net_interest_pct_revenue"].where(d.index != "KEN"))
    try:
        out = fi.apply(ci)
    finally:
        fi.imf_latest = real_latest
    g = ci.loc["KEN", "income_group"]
    peers = out[(out.income_group == g) & ~out.interest_estimated & (out.index != "KEN")]["interest_pct_revenue"]
    assert out.loc["KEN", "interest_estimated"] and out.loc["KEN", "interest_pct_revenue"] == pytest.approx(peers.median())
    assert "median of" in out.loc["KEN", "interest_pct_revenue_source"]
    F = hm.fiscal_space(out.loc["KEN"])
    assert ms.interest_text(F).startswith("Interest: ") and "estimated" in ms.interest_text(F)


def test_interest_text_shows_source_and_year():
    F = hm.fiscal_space(CI.loc["PAK"])
    assert ms.interest_text(F) == f"Interest: {F['interest_pct_revenue']:.0f}% of revenue (IMF WEO Oct 2026, 2024)"   # Batch 7 item 6: the label carries the WEO release


def test_inputs_years_line():
    assert ms.inputs_years_line(CI, ISOS) == ("Inputs: aid 2021-23 average; coverage 2024-25 (malaria: MAP 2025); "
                                               "government health spending 2023; applied to 2026-2030 without "
                                               "projection.")
    assert hm.AID_BASE_YEARS == pm.BASE_YEARS
