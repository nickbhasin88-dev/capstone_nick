"""Tests for audit fixes I-09 (HIV testing & care), I-27 PMTCT part and I-04 (per-US$1M cards).
Run:  python -m pytest tests"""
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
import prepare_model as pm  # noqa: E402
import scenarios as scn  # noqa: E402

I, P = hm.load_inputs(), hm.load_params()
CI, LINES = I["ci"], I["lines"]
NONE = hm.Fiscal(*scn.DEFAULT_FISCAL)
KAPPA = float(P.loc["hss_kappa", "central"])
EXIT = scn.build_scenario("Full US exit", {}, CI)


# ---------------- I-09 ----------------
def test_line_mapping():
    assert pm.LINES["hiv_art"] == ("HIV", ["hiv_treat"])
    assert pm.LINES["hiv_care_ct"] == ("HIV", ["hiv_care", "hiv_ct"])
    cols = [c for b, cs in pm.LINES.values() for c in cs if b == "HIV"]
    assert len(cols) == len(set(cols))                       # each IHME program area in one line only


def test_care_line_has_money_but_no_units():
    r = hm.run_country("KEN", EXIT, NONE, I, P, n_draws=0)
    L = r["lines"].set_index("line")
    c = L.loc["hiv_care_ct"]
    assert c["base_usd"] > 0 and c["net_loss_usd"] > 0
    assert np.isnan(c["units_lost"]) and np.isnan(c["cov0"]) and c["deaths_5y"] == 0


def test_kappa_of_care_loss_counts_toward_art():
    """Cutting only the testing & care line: ART loses kappa x the loss / cost x (1 - continuity) people."""
    sc = hm.Scenario(name="care only")
    sc.src_direct = {s: 1.0 for s in hm.SOURCE_GROUPS}
    sc.src_multi = {s: 1.0 for s in hm.SOURCE_GROUPS}
    sc.bucket_only = "HIV"
    # zero every HIV line except testing & care by giving the run a lines table with only that line cut
    lines = LINES.copy()
    keep = (lines.iso3 != "KEN") | (lines.line == "hiv_care_ct") | (lines.bucket != "HIV")
    I2 = dict(I, lines=lines[keep])
    r = hm.run_country("KEN", sc, NONE, I2, P, n_draws=0)
    L = r["lines"].set_index("line")
    care_loss = L.loc["hiv_care_ct", "gross_loss_usd"]
    cont = float(P.loc["continuity", "central"])
    want = KAPPA * care_loss / L.loc["hiv_art", "unit_cost"] * (1 - cont)
    assert L.loc["hiv_art", "units_lost"] == pytest.approx(min(want, L.loc["hiv_art", "cov0"] * L.loc["hiv_art", "need"]))
    assert L.loc["hiv_art", "units_lost"] > 0


def test_service_table_care_row():
    r = hm.run_country("KEN", EXIT, NONE, I, P, n_draws=0)
    L = r["lines"]
    rows = ms._service_rows(L[(L["base_usd"] > 0) | (L["net_loss_usd"] != 0)])
    assert list(rows["line"])[:2] == ["hiv_art", "hiv_care_ct"]
    html = ms._service_table_html(rows, "Kenya", r["totals"])
    assert "HIV Testing &amp; Care" in html and "counted as lost ART care" in html
    assert f"{KAPPA:.0%} of lost testing and care money is counted as lost ART care" in ms.care_ct_note()


# ---------------- I-27 PMTCT ----------------
def test_pmtct_cost():
    r = P.loc["uc_pmtct"]
    assert (r["central"], r["low"], r["high"], r["status"]) == (250, 150, 450, "unverified")   # Batch 7 item 16 (L-32): relabelled, value and range unchanged
    assert "Option B+" in r["label"] and "Health Policy and Planning" in r["source"] and r["source"].startswith("UNVERIFIED")
    assert ms.COST_UNIT["hiv_pmtct"] == "per woman per year, including her ART"


def test_pmtct_women_outside_art_pool():
    """People losing ART never exceed people on ART minus women covered by PMTCT."""
    for iso in ("KEN", "NGA", "SSD", "HTI", "MOZ"):
        L = hm.run_country(iso, EXIT, NONE, I, P, n_draws=0)["lines"].set_index("line")
        pm_cov = L.loc["hiv_pmtct", "cov0"] * L.loc["hiv_pmtct", "need"]
        assert L.loc["hiv_art", "units_lost"] <= L.loc["hiv_art", "cov0"] * L.loc["hiv_art", "need"] - pm_cov + 1e-6
        assert L.loc["hiv_art", "donor_funded_units"] <= L.loc["hiv_art", "cov0"] * L.loc["hiv_art", "need"] - pm_cov + 1e-6


# ---------------- I-04 cards ----------------
@pytest.mark.parametrize("iso", ["KEN", "NGA", "HND", "ZAF", "IRQ"])
def test_card_is_full_model_for_1m_uniform_cut(iso):
    pj = P.to_json(orient="split")
    cards = {c["bucket"]: c for c in ms._per_million_cards(iso, pj, True, iso)}
    for b in hm.BUCKETS:
        aid = LINES.loc[(LINES.iso3 == iso) & (LINES.bucket == b), "usd"].sum()
        cut = min(1.0, 1e6 / aid)
        r = hm.run_country(iso, hm.uniform_scenario(b, cut), hm.Fiscal(), I, P, n_draws=0)
        B = r["buckets"].set_index("bucket")
        k = 1e6 / B.loc[b, "gross_loss_usd"]
        want = B.loc[b, "deaths_5y"] * k
        got = float(cards[b]["deaths"].replace(",", "")) if cards[b]["deaths"] else 0.0
        assert got == pytest.approx(want, abs=0.5, rel=0.01)
        main = ms.MAIN_LINE[b]
        ln = r["lines"].set_index("line").loc[main]
        assert float(cards[b]["people_n"].replace(",", "")) == pytest.approx(ln["units_lost"] * k, abs=0.5)
        assert "Spread across all" in cards[b]["foot"]


def test_card_without_aid_says_so(monkeypatch):
    lines = LINES[~((LINES.iso3 == "HND") & (LINES.bucket == "Malaria"))]
    monkeypatch.setattr(ms, "_inputs", lambda: dict(I, lines=lines))
    ms._card_runs.clear()
    c = {c["bucket"]: c for c in ms._per_million_cards("HND", P.to_json(orient="split"), True, "Honduras")}
    ms._card_runs.clear()
    assert c["Malaria"]["no_deaths"] == "No malaria aid in Honduras" and c["Malaria"]["people_n"] is None
    assert "No malaria aid in Honduras" in ms._card_html(c["Malaria"])
    assert ms.CARDS_TITLE == "What Every US$1 Million Cut Does, by Disease"
