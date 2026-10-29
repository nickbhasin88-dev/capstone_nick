"""Tests for the 'Announced donor cuts' preset (announcement_model/). Run:  python -m pytest tests"""
import logging

import pytest
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
logging.disable(logging.WARNING)
import health_model as hm  # noqa: E402
import scenarios as scn  # noqa: E402

I, P = hm.load_inputs(), hm.load_params()
CI, AMAP = I["ci"], I["announce_map"]
NONE = hm.Fiscal(*scn.DEFAULT_FISCAL)
ANN = scn.ANNOUNCED
SC = scn.build_scenario(ANN, scn.default_opts(ANN, CI), CI)
CSV = pd.read_csv(hm.MODEL_DIR / hm.ANNOUNCE_FILE)


def test_file_covers_every_country_and_cuts_are_bounded():
    assert set(I["lines"].iso3) - set(CSV.iso3) <= {"GUY"}     # no 2023 IHME baseline: pooled path
    gy = I["lines"][I["lines"].iso3 == "GUY"]
    assert (SC.cuts_by_year(gy, "GUY", I["trend_map"], AMAP)[:, 2] * gy.usd.to_numpy()).sum() > 0
    cuts = CSV[[f"cut_{y}" for y in scn.YEARS]].to_numpy()
    known = CSV[[f"known_cut_{y}" for y in scn.YEARS]].to_numpy()
    assert np.all((cuts >= -1) & (cuts <= 1)) and np.all((known >= -1) & (known <= 1))


def test_preset_registered():
    assert ANN in scn.PRESETS and ANN in scn.PRECOMPUTED_PRESETS
    assert scn.UI_PRESETS == [ANN, "Custom"]
    assert SC.announcement and not scn.build_scenario("Full US exit", scn.default_opts("Full US exit", CI), CI).announcement


def test_cells_take_their_own_yearly_path():
    cells = I["lines"][I["lines"].iso3 == "ZMB"]
    cuts = SC.cuts_by_year(cells, "ZMB", I["trend_map"], AMAP)
    row = CSV[(CSV.iso3 == "ZMB") & (CSV.src_grp == "United States") & (CSV.chan_grp == "Bilateral agency")].iloc[0]
    want = [row[f"cut_{y}"] for y in scn.YEARS]
    us_bil = ((cells.src_grp == "United States") & (cells.chan_grp == "Bilateral agency")).to_numpy()
    assert us_bil.any()
    assert np.allclose(cuts[us_bil], want)
    assert (np.diff(want) > -1e-3).all() and want[-1] > want[0] + 0.2   # the similar countries' path deepens


def test_without_the_file_nothing_is_cut():
    cells = I["lines"][I["lines"].iso3 == "ZMB"]
    assert np.all(SC.cuts_by_year(cells, "ZMB", I["trend_map"], {}) == 0)


def test_run_country_and_precomputed_file():
    r = hm.run_country("ZMB", SC, NONE, I, P, n_draws=100)
    lost = r["years"]["aid_lost_usd"].to_numpy()
    assert np.all(lost > 0) and np.all(np.diff(lost) > 0)
    assert r["totals"]["deaths_5y"] > 0
    pre = pd.read_csv(scn.precomputed_path(hm.MODEL_DIR, ANN))
    assert len(pre) == I["lines"].iso3.nunique()


def test_inputs_cached_before_the_file_existed_still_cut():
    """A running app keeps load_inputs() cached across a code update, so its inputs can lack announce_map."""
    stale = {k: v for k, v in I.items() if k != "announce_map"}
    r = hm.run_country("ZMB", SC, NONE, stale, P, n_draws=50)
    assert r["years"]["aid_lost_usd"].gt(0).all()


def test_global_fund_cut_is_the_allocation_not_stacked_on_donor_cuts():
    """Every donor's Global Fund money in a country gets the same cut (the country's allocation ratio): the Global
    Fund cuts because donors cut, so a donor's own cut is never applied on top. 2026-2027 are the published
    allocations; from 2028 the GC7 -> GC8 change continues at the same yearly rate (predicted)."""
    gf = CSV[(CSV.iso3 == "ZMB") & (CSV.chan_grp == "Global Fund")]
    assert len(gf) > 3
    cut = gf[[f"cut_{y}" for y in scn.YEARS]].to_numpy()
    known = gf[[f"known_cut_{y}" for y in scn.YEARS]].to_numpy()
    assert np.allclose(cut.std(0), 0, atol=1e-3)
    assert np.allclose(cut[:, :2], known[:, :2]) and np.allclose(known[:, 2:], 0)
    kept27 = 1 - cut[0, 1]
    assert np.allclose(1 - cut[0, 2:], kept27 * kept27 ** (np.arange(1, 4) / 3), atol=1e-3)


def test_total_health_aid_uses_the_2019_2023_average():
    """The money headline covers all health aid against the 2019-2023 average, COVID-19 money included."""
    tot = hm.announcement_totals()
    assert 1.2e9 < tot["KEN"]["base"] < 1.4e9                  # Kenya: 1.30, 1.40, 1.47, 1.30, 0.94 $B
    for iso in ("KEN", "ZMB"):
        t = tot[iso]
        assert np.all(t["lost"] > 0) and np.all(t["known"] <= t["lost"] + 1)
    assert tot["KEN"]["lost"][-1] > tot["KEN"]["lost"][0]       # the MOU cliff in 2030


def test_donor_cut_is_uniform_across_its_predicted_channels():
    de = CSV[(CSV.iso3 == "ZMB") & (CSV.src_grp == "Germany") & ~CSV.chan_grp.isin(["Global Fund", "Gavi"])]
    assert len(de) > 1 and np.allclose(de["cut_2028"], de["cut_2028"].iloc[0], atol=1e-3)


def test_known_loss_is_part_of_total_loss():
    for iso in ("ZMB", "KEN", "GUY"):
        cells = I["lines"][I["lines"].iso3 == iso]
        total = np.clip((cells.usd.to_numpy()[:, None] * SC.cuts_by_year(cells, iso, I["trend_map"], AMAP)).sum(0), 0, None)
        known = hm.known_loss_by_year(iso, I)
        assert np.all(known <= total + 1)
    assert hm.known_loss_by_year("KEN", I).sum() > 0            # MOU + Global Fund


def test_dashboard_is_coverage_only():
    """No deaths in the headline numbers; the lede names each country's biggest risks. The service table's only deaths
    are its last column (merge decision 2-3, chipmunk: 'Extra Deaths, 2026-2030 Total')."""
    import model_section as ms
    r = hm.run_country("KEN", SC, NONE, I, P, n_draws=0)
    labels = " ".join(lbl for lbl, *_ in ms._headline_items(r, P))
    assert "Death" not in labels and "People Losing a Service" in labels
    table = ms._service_table_html(ms._service_rows(r["lines"]), "Kenya", r["totals"])
    assert table.count("Deaths") == 1 and "Extra Deaths, 2026-2030 Total" in table
    for iso in ("KEN", "ZMB"):
        risks = ms.risk_lines(iso, hm.run_country(iso, SC, NONE, I, P, n_draws=0))
        assert risks[0].startswith("Biggest risk:") and any(t.startswith("Hardest-hit service:") for t in risks)
    assert "US government bilateral aid" in ms.risk_lines("KEN", r)[0]     # the MOU is Kenya's largest 2030 loss


def test_all_countries_people_columns():
    out = hm.run_all(SC, NONE, I, P, n_draws=0, countries=["KEN", "ZMB"])
    assert (out["people_lost"] > 0).all()
    assert np.allclose(out["people_lost"], out[[f"people_lost_{b}" for b in hm.BUCKETS]].sum(axis=1))


def test_abuja_and_tax_options():
    """Abuja: (15% - health share) x government spending; tax: new revenue up to 15% of GDP, spent at the health share
    (15% when combined with Abuja); nothing where a country is already past the target; phased in by 2030."""
    hb, te = hm.health_budget("KEN", I), hm.tax_effort("KEN")
    a = hm.policy_money("KEN", I, True, False)
    assert a["abuja_usd"] == pytest.approx((0.15 - hb["share_pct"] / 100) * hb["gov_spend_usd"])
    t = hm.policy_money("KEN", I, False, True)
    assert t["tax_usd"] == pytest.approx((15 - te["tax_pct"]) / 100 * te["gdp_usd"] * hb["share_pct"] / 100)
    both = hm.policy_money("KEN", I, True, True)
    assert both["tax_usd"] == pytest.approx(t["tax_usd"] * 15 / hb["share_pct"])
    assert np.allclose(both["by_year"], both["full_usd"] * np.array([0.2, 0.4, 0.6, 0.8, 1.0]))
    assert hm.policy_money("ZAF", I, True, True)["full_usd"] == 0           # past both targets
    r0 = hm.run_country("KEN", SC, NONE, I, P, n_draws=0)
    r1 = hm.run_country("KEN", SC, NONE, I, P, n_draws=0, gov_add_usd=tuple(a["by_year"]))
    assert r1["totals"]["replaced"] > 0 and r1["totals"]["net"] < r0["totals"]["net"]


def test_services_by_year():
    """Each service has its own money lost, people and coverage drop for every year 2026-2030; their averages are the
    5-year figures, and the year view of the service table adds up to that year's net loss."""
    r = hm.run_country("KEN", SC, NONE, I, P, n_draws=0)
    L = r["lines"]
    yrs = [hm.YEAR0 + t for t in range(hm.N_YEARS)]
    d = L[L["line"].isin(hm.ALL_DIRECT)]
    np.testing.assert_allclose(d[[f"units_lost_{y}" for y in yrs]].mean(axis=1), d["units_lost"], rtol=1e-6)
    ok = d["cov_drop_pp"].notna()
    np.testing.assert_allclose(d.loc[ok, [f"cov_drop_pp_{y}" for y in yrs]].mean(axis=1), d.loc[ok, "cov_drop_pp"],
                               rtol=1e-6)
    np.testing.assert_allclose(L[[f"net_loss_{y}" for y in yrs]].mean(axis=1), L["net_loss_usd"], rtol=1e-6, atol=1)
    art = d.set_index("line").loc["hiv_art"]
    assert art["cov_drop_pp_2030"] > art["cov_drop_pp"] > art["cov_drop_pp_2026"] > 0
    import model_section as ms
    rows = ms._service_rows(L[(L["base_usd"] > 0) | (L["net_loss_usd"] != 0)])
    assert ms._model_years(rows) == yrs
    ry, Ty = ms._year_rows(rows, r, r["totals"], 2030)
    assert Ty["net"] == pytest.approx(float(r["years"].set_index("year").loc[2030, "gap_usd"]))
    assert ry.set_index("line").loc["hiv_art", "drop"] == pytest.approx(art["cov_drop_pp_2030"])
    assert ms._coverage_path_fig(rows) is not None


def test_treatment_gets_its_share_of_each_disease(monkeypatch):
    """TREAT_SHARE of each disease's aid (all of its lines) pays for treatment; the rest cuts no service, and other
    services keep no money of their own (the optional TREAT_SHARE rule, off by default)."""
    monkeypatch.setattr(hm, "TREAT_SHARE", 0.8)
    r = hm.run_country("KEN", SC, NONE, I, P, n_draws=0)
    L, cells = r["lines"].set_index("line"), I["lines"][I["lines"].iso3 == "KEN"]
    for b, treat in hm.UNSPEC_TREAT.items():
        total = cells.loc[cells["bucket"] == b, "usd"].sum()
        assert L.loc[treat, "base_usd"].sum() == pytest.approx(hm.TREAT_SHARE * total, rel=1e-6)
    for l in ("hiv_pmtct", "hiv_prev", "mal_itn", "mal_irs", "hiv_care_ct"):
        assert L.loc[l, "base_usd"] == 0 and L.loc[l, "net_loss_usd"] == 0
    assert L.loc["imm", "base_usd"] == pytest.approx(cells.loc[cells["line"] == "imm", "usd"].sum())
    assert L.loc["hiv_art", "cov_drop_pp_2030"] > 15


def test_phase_out_by_funder():
    """The per-funder phase-out covers all of the country's health aid: the US, Global Fund and Gavi lines, each OECD
    donor and everyone else add up to the total base and loss."""
    import model_section as ms
    d = ms.phase_out_by_donor("KEN")
    a = hm.announcement_sources("KEN")
    assert {"United States", "Global Fund", "Gavi"} <= set(d.index)
    assert d["base"].sum() == pytest.approx(a["base"].sum())
    assert (d["base"] * d["cut_2030"]).sum() == pytest.approx(a["lost_2030"].sum())
    assert d.loc["Gavi", "cut_2026"] > 0 and d.loc["United States", "cut_2030"] > d.loc["United States", "cut_2026"]
    assert ms._spread([5.0, 5.5, 20.0], 2.0) == [5.0, 7.0, 20.0]


def test_fiscal_panel_uses_all_health_aid_lost():
    """Can the Country Fill the Gap? uses the Announced donor cuts headline money (all health aid lost each year), and
    the government fills it by the chosen response, capped at fiscal space."""
    import model_section as ms
    r = hm.run_country("KEN", SC, NONE, I, P, n_draws=0)
    lost = hm.announcement_totals()["KEN"]["lost"]
    avg, y30, _ = ms.fiscal_gap_values(ms.with_all_aid(r, lost, scn.DEFAULT_FISCAL))
    assert y30["gap"] == pytest.approx(lost[-1]) and avg["filled"] == 0 and y30["left"] == pytest.approx(lost[-1])
    fmax = ("max", 0.0, True, "pro_rata", "p50")
    rm = hm.run_country("KEN", SC, hm.Fiscal(*fmax), I, P, n_draws=0)
    avg_m, y30_m, _ = ms.fiscal_gap_values(ms.with_all_aid(rm, lost, fmax))
    assert y30_m["filled"] == pytest.approx(min(lost[-1], rm["fiscal"]["capacity"]))
