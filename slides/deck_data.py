"""
Figures for the dashboard deck (round 2), computed from the model's own data and functions; read-only.

    .venv/bin/python slides/deck_data.py        -> slides/deck_data.json

- us_share: US share of 2021-23 aid for HIV, TB, malaria and vaccines, top 20 of the 70 countries by total aid
  (model_data/dah_lines.csv, built from IHME DAH 1990-2026 by prepare_model.py).
- channel_purpose: the same aid for all 70 countries by channel group and by IHME programme-area type (no model
  allocation: unspecified aid is shown as "purpose not stated").
- art_bound: people off ART per year (2026-30 average, full-cost equivalents) under America First MOUs and under
  US Bilateral Exit + Multilateral Withdrawals for the 16 MOU countries, and Full US exit for all countries
  (health_model.run_country, dashboard defaults, central run).
- mou_art: ART coverage 2026-30 under the MOU schedule (audit/concentration/thresholds.csv, US bilateral only).
- history: subsample regressions (audit/fiscal_history/subsample_theta.csv).
- channels: people per US$1M by channel, all countries (audit/channels/channels.csv).
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
logging.disable(logging.WARNING)
import health_model as hm  # noqa: E402
import scenarios as scn  # noqa: E402

out = {}
I, P = hm.load_inputs(), hm.load_params()
ci, L = I["ci"], I["lines"]
from country_lists import ALLOWED_COUNTRIES  # noqa: E402
names = dict(ALLOWED_COUNTRIES) if isinstance(ALLOWED_COUNTRIES, dict) else {}
if not names:
    names = pd.read_csv(ROOT / "ext_data" / "who_regions.csv").set_index("iso3")["country"].to_dict()

# US share, top 20 by total aid
tot = L.groupby("iso3").usd.sum()
us = L[L.src_grp == "United States"].groupby("iso3").usd.sum().reindex(tot.index).fillna(0)
top = tot.sort_values(ascending=False).head(20)
out["us_share"] = [{"iso3": i, "country": names.get(i, i), "total_musd": tot[i] / 1e6, "us_musd": us[i] / 1e6,
                    "us_share": us[i] / tot[i]} for i in top.index]
out["n_countries_with_aid"] = int(tot.size)
out["total_aid_musd"] = float(tot.sum() / 1e6)
out["us_aid_musd"] = float(us.sum() / 1e6)

# channel x purpose, all countries (IHME programme areas as grouped in prepare_model.LINES)
direct = set(hm.ALL_DIRECT)
def purpose(line):
    if line in direct:
        return "Direct services"
    if line == "hiv_care_ct":
        return "Testing and care"
    if line.endswith("_hss"):
        return "Systems support"
    return "Purpose not stated"
L2 = L.assign(purpose=L.line.map(purpose))
chan_map = {"Global Fund": "Global Fund", "Bilateral agency": "Bilateral agencies", "NGOs": "NGOs", "Gavi": "Gavi"}
L2["chan"] = L2.chan_grp.map(lambda c: chan_map.get(c, "Other channels"))
cp = L2.groupby(["chan", "purpose"]).usd.sum().unstack().fillna(0) / 1e6
out["channel_purpose"] = {c: cp.loc[c].to_dict() for c in cp.index}
out["purpose_total"] = (L2.groupby("purpose").usd.sum() / 1e6).to_dict()

# ART bound: MOU vs full exit (same 16 countries) and full exit, all countries
F = hm.Fiscal(*scn.DEFAULT_FISCAL)
sc_mou = scn.build_scenario("America First MOUs", {}, ci)
mou16 = sorted(sc_mou.us_direct_path_by_country)
sc_full = scn.build_scenario("Full US exit", {}, ci)
def art(sc, isos):
    a = aid = 0.0
    for i in isos:
        r = hm.run_country(i, sc, F, I, P, n_draws=0)
        a += float(r["lines"].set_index("line").loc["hiv_art", "units_lost"])
        aid += float(r["totals"]["gross"])
    return a, aid
out["art_bound"] = {}
for key, sc, isos in (("mou_16", sc_mou, mou16), ("full_exit_16", sc_full, mou16),
                      ("full_exit_all", sc_full, sorted(tot.index))):
    a, aid = art(sc, isos)
    out["art_bound"][key] = {"art_off_per_year": a, "aid_lost_per_year_musd": aid / 1e6, "n": len(isos)}
out["mou16"] = mou16

# MOU ART coverage, from the W-9 threshold scan
t = pd.read_csv(ROOT / "audit" / "concentration" / "thresholds.csv").set_index("iso3")
out["mou_art"] = {i: {"country": t.loc[i, "country"], "today": float(t.loc[i, "art_cov0"]),
                      **{str(y): float(t.loc[i, f"art_cov_{y}"]) for y in range(2026, 2031)}}
                  for i in t.index if t.loc[i, "art_cov0"] >= 0.90}
# which of them rest on the donor-funded pool cap (donor money buys more than the pool)
excess = {}
sc_b = scn.build_scenario("America First MOUs", {}, ci)
sc_b.pair = {}
for i in out["mou_art"]:
    r = hm.run_country(i, sc_b, F, I, P, n_draws=0)
    excess[i] = bool(r["lines"].set_index("line").loc["hiv_art", "donor_exceeds_cost"])
out["mou_art_pool_capped"] = excess

# history subsamples and channels
out["history"] = pd.read_csv(ROOT / "audit" / "fiscal_history" / "subsample_theta.csv").to_dict("records")
ch = pd.read_csv(ROOT / "audit" / "channels" / "channels.csv")
ch = ch[ch["size"] == "full"]
g = ch.groupby("channel")[["aid_lost_per_year", "ART", "Bednets", "TB treatment", "Vaccines"]].sum()
for m in ("ART", "Bednets", "TB treatment", "Vaccines"):
    g[m] = g[m] / (g["aid_lost_per_year"] / 1e6)
out["channels_all"] = g.drop(columns="aid_lost_per_year").to_dict("index")
out["channels_n"] = ch.groupby("channel").iso3.nunique().to_dict()

(Path(__file__).parent / "deck_data.json").write_text(json.dumps(out, indent=1, default=float))
print(json.dumps({k: out[k] for k in ("art_bound", "mou_art_pool_capped", "purpose_total", "n_countries_with_aid",
                                      "total_aid_musd", "us_aid_musd")}, indent=1, default=float))
print(pd.DataFrame(out["us_share"])[["country", "total_musd", "us_share"]].round(2).to_string())
print(cp.round(0).to_string())
print(pd.DataFrame(out["channels_all"]).T.round(0).to_string())
