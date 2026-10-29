"""TB fixes from the logic review: L-12 (detection rate capped at 100%), L-13 (WHO Table 5 blend for untreated HIV+ TB),
L-10 (no TB death trend: TB deaths are per patient)."""
import logging
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
logging.disable(logging.WARNING)
import health_model as hm  # noqa: E402

I, P = hm.load_inputs(), hm.load_params()
CI = I["ci"]
PC = hm.draw_params(P, 0)


def test_detection_rate_capped_at_100_and_flagged():
    row = CI.loc["KEN"].copy()
    row["sh_tbs_dtec_zs"] = 120.0
    ep = hm.epi(row, PC)
    assert ep["need_cov"]["tb_ds"][1] == 1.0
    assert any("capped at 100%" in f for f in ep["flags"])
    ok = hm.epi(CI.loc["KEN"], PC)
    assert ok["need_cov"]["tb_ds"][1] == pytest.approx(CI.loc["KEN", "sh_tbs_dtec_zs"] / 100)
    assert not any("TB case detection" in f for f in ok["flags"])


def test_untreated_hiv_tb_cfr_is_who_table5_blend():
    row = CI.loc["KEN"]
    a, h = CI.loc["KEN", "sh_hiv_artc_zs"] / 100, CI.loc["KEN", "tb_hiv_share"]
    got = hm.per_unit_levels(row, PC, a)["tb_ds"][0, 0]
    up = 0.78 * (1 - a) + 0.49 * a                         # WHO TB burden methods, Table 5
    tp = PC["tb_cfr_treated_pos"][0] * (1 - 0.3 * a)
    want = (1 - h) * (PC["tb_cfr_untreated_neg"][0] - PC["tb_cfr_treated_neg"][0]) + h * (up - tp)
    assert got == pytest.approx(want)
    assert PC["tb_cfr_untreated_pos"][0] == 0.78 and PC["tb_cfr_untreated_pos_art"][0] == 0.49
    # no one on ART: the off-ART value; everyone on ART for a year or more: the on-ART value
    for cov, cfr in ((0.0, 0.78), (1.0, 0.49)):
        lv = hm.per_unit_levels(row, PC, cov)["tb_ds"][0, 0]
        assert lv == pytest.approx((1 - h) * 0.40 + h * (cfr - PC["tb_cfr_treated_pos"][0] * (1 - 0.3 * cov)))


def test_no_tb_death_trend():
    assert "tb" not in hm.TREND_COLUMNS
    assert "trend_tb_deaths" not in CI.columns
    lv = hm.per_unit_levels(CI.loc["KEN"], PC, 0.9, trend=True)["tb_ds"]
    assert np.allclose(lv, lv[:, :1])                          # the same per-patient effect in every year
