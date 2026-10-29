"""Tests for America First MOUs (audit I-02, I-03, I-08). Run:  python -m pytest tests"""
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
logging.disable(logging.WARNING)
import health_model as hm  # noqa: E402
import scenarios as scn  # noqa: E402

I, P = hm.load_inputs(), hm.load_params()
CI = I["ci"]
NONE = hm.Fiscal(*scn.DEFAULT_FISCAL)
MOU = "America First MOUs"
GROUP_A = ["BDI", "BWA", "CMR", "ETH", "KEN", "LBR", "LSO", "MDG", "MOZ", "MWI", "NGA", "RWA", "SLE", "SSD", "SWZ", "UGA"]
SIGNED = set(scn.mou_signed()["iso3"])
GROUPS = scn.mou_groups(CI, list(CI.index))
SC = scn.build_scenario(MOU, scn.default_opts(MOU, CI), CI)


def written_schedule(iso):
    """The schedule straight from the team sheet: 1 - US funding / reference, increases = 0, last year held."""
    r, out, last = CI.loc[iso], [], None
    for y in scn.YEARS:
        v = r.get(f"mou_us_{y}")
        if pd.notna(v):
            last = min(max(1 - v / r["mou_us_ref"], 0.0), 1.0)
        out.append(last)
    return out


def test_signed_list_and_groups():
    assert len(SIGNED) == 36
    assert sorted(c for c, g in GROUPS.items() if g == "A") == sorted(GROUP_A)
    assert sum(g == "B" for g in GROUPS.values()) == len(SIGNED & set(CI.index)) - 16
    assert all(GROUPS[c] == "C" for c in CI.index if c not in SIGNED)
    # status comes from the signed list, never from schedule data
    prof = pd.read_csv(hm.MODEL_DIR / "country_profile.csv").set_index("iso3")
    assert set(prof.index[prof.mou_status == "Signed"]) == SIGNED & set(prof.index)
    assert set(prof.mou_status) <= {"Signed", "No MOU"}


@pytest.mark.parametrize("iso", GROUP_A)
def test_applied_us_bilateral_cut_equals_schedule(iso):
    sched = written_schedule(iso)
    assert scn.mou_schedule(CI, iso)[0] == sched
    cells = I["lines"][I["lines"].iso3 == iso]
    cut = SC.cuts_by_year(cells, iso, I["trend_map"])
    us_direct = ((cells["src_grp"] == "United States") & cells["chan_grp"].isin(hm.DIRECT_CHANNELS)).to_numpy()
    assert us_direct.any()
    for t in range(5):                                   # every US bilateral cell, every year: exactly the schedule
        assert np.all(cut[us_direct, t] == sched[t]), (iso, t)
    # US multilateral exits unchanged and constant over the years
    for (src, chan), v in scn.US_MULTI_EXITS.items():
        m = ((cells["src_grp"] == src) & (cells["chan_grp"] == chan)).to_numpy()
        assert np.allclose(cut[m], v, rtol=0, atol=1e-12)             # 1-(1-0.23)(1-0) in floating point
    # and the model applies it: yearly aid lost = the cells' yearly losses, schedule shown as written
    r = hm.run_country(iso, SC, NONE, I, P, n_draws=2)
    assert np.allclose(r["years"]["us_bilateral_cut"], sched, atol=0, rtol=0)
    loss_t = [float(np.clip(pd.Series(cells["usd"].to_numpy() * cut[:, t]).groupby(cells["line"].to_numpy()).sum(),
                            0, None).sum()) for t in range(5)]
    assert np.allclose(r["years"]["aid_lost_usd"], loss_t)


def test_schedule_rules():
    assert scn.mou_schedule(CI, "KEN")[0][0] == 0.0                     # 2026 funding increase -> 0% cut
    e = scn.mou_schedule(CI, "ETH")[0]
    assert e[1] < e[0]                                                   # eases in 2027, followed as written
    for iso in ("BWA", "SSD"):
        s, end = scn.mou_schedule(CI, iso)
        assert end == 2028 and s[3] == s[2] and s[4] == s[2]             # 2028 level held through 2030


def test_easing_schedule_returns_people_to_care():
    r = hm.run_country("ETH", SC, NONE, I, P, n_draws=2, keep_draws=True)
    off = r["draws"]["units"]["hiv_art"][0]
    assert off[1] < off[0]                                               # 2027: fewer people off ART than in 2026


@pytest.mark.parametrize("iso", [c for c in CI.index if GROUPS[c] != "A"][:40])
def test_groups_b_and_c_cannot_run(iso):
    with pytest.raises(ValueError):
        hm.run_country(iso, SC, NONE, I, P, n_draws=2)


def test_all_countries_only_group_a():
    A = hm.run_all(SC, NONE, I, P, n_draws=2)
    assert sorted(A["iso3"]) == sorted(c for c in GROUP_A if c in set(I["lines"].iso3))
    pre = pd.read_csv(scn.precomputed_path(hm.MODEL_DIR, MOU))
    assert sorted(pre["iso3"]) == sorted(A["iso3"])


def test_nothing_rescales_a_schedule():
    # no rescaling helpers or MOU-year settings remain, and the path list has no MOU option
    for name in ("mou_cut_path", "mou_cuts", "mou_average_cut_pct", "DEFAULT_MOU_YEAR"):
        assert not hasattr(scn, name), name
    assert "MOU schedule" not in scn.PATH_SHAPES
    assert scn.default_opts(MOU, CI) == {}
    # every schedule equals the sheet's own levels (not divided by its deepest year)
    for iso in GROUP_A:
        s = scn.mou_schedule(CI, iso)[0]
        assert s == written_schedule(iso)
        assert max(s) < 1.0 or iso in ("RWA",)                           # not normalized so the deepest year = 100%
