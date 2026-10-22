"""
W-7 Channel comparison (audit/channels): dollar for dollar, does a cut through the Global Fund, Gavi or US bilateral
channels cost more coverage? Each channel is cut on its own (a health_model.Scenario with one donor cut, one channel
cut or one donor x channel pair) by a fraction chosen so that the modelled aid lost is the same (US$10M a year, or
half the channel's baseline where that is smaller), sudden path, 5 years, no government response, death-rate trends
on. Results are per US$1M of aid lost per year, so channels are compared at equal money. Also: the America First MOUs
preset's US multilateral exits (WHO, Gavi, UNFPA 100%, Global Fund 23%) against a US bilateral cut of the same size
in each country. Central runs (money and people are linear in the cut except where lines are capped; a half-size
cut checks linearity); deaths with 400-draw ranges for the pooled rows.

    .venv/bin/python audit/channels/run_channels.py [--draws 400]

Outputs: RESULTS_channels.md, channels.csv. Read-only with respect to the model.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "audit" / "reallocation"))
logging.disable(logging.WARNING)
import health_model as hm  # noqa: E402
import scenarios as scn  # noqa: E402
import run_reallocation_2027 as rr  # noqa: E402

fmt, sfmt, md_table = rr.fmt, rr.sfmt, rr.md_table
SERV = rr.SERVICES
TARGET = 1e7


def channel_scenarios(f):
    return {"US bilateral (direct channels)": hm.Scenario(name="us_bilateral", src_direct={"United States": f}),
            "US money through the Global Fund": hm.Scenario(name="us_gf", pair={("United States", "Global Fund"): f}),
            "Global Fund (all donors)": hm.Scenario(name="gf", chan={"Global Fund": f}),
            "Gavi (all donors)": hm.Scenario(name="gavi", chan={"Gavi": f}),
            "WHO (all donors)": hm.Scenario(name="who", chan={"WHO": f}),
            "UNICEF (all donors)": hm.Scenario(name="unicef", chan={"UNICEF": f})}


def channel_base(lines, iso, name):
    L = lines[lines.iso3 == iso]
    if name.startswith("US bilateral"):
        return float(L[(L.src_grp == "United States") & L.chan_grp.isin(hm.DIRECT_CHANNELS)].usd.sum())
    if name.startswith("US money through the Global Fund"):
        return float(L[(L.src_grp == "United States") & (L.chan_grp == "Global Fund")].usd.sum())
    chan = {"Global Fund (all donors)": "Global Fund", "Gavi (all donors)": "Gavi", "WHO (all donors)": "WHO", "UNICEF (all donors)": "UNICEF"}[name]
    return float(L[L.chan_grp == chan].usd.sum())


def measure(r, draws=None):
    U, L, yt = r["draws"]["units"], r["lines"].set_index("line"), r["years"].set_index("year")
    aid = float(yt["aid_lost_usd"].mean())
    d = {"aid_lost_per_year": aid}
    for n, ls in {**SERV, **rr.EXTRA}.items():
        d[n] = float(sum(U[l][0, :].mean() for l in ls))
    d["all6"] = sum(d[n] for n in SERV)
    d["deaths_5y"] = float(r["totals"]["deaths_5y"])
    d["service_money"] = float(L.loc[hm.ALL_DIRECT, "gross_loss_usd"].sum())
    d["capped"] = ",".join(L.index[L["capped"].fillna(False).astype(bool)])
    B = r["buckets"].set_index("bucket")
    for b in hm.BUCKETS:
        d[f"mix_{b}"] = float(B.loc[b, "gross_loss_usd"]) / aid if aid else np.nan
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=400)
    a = ap.parse_args()
    alloc = pd.read_csv(ROOT / "audit" / "reallocation" / "allocations_2027.csv").set_index("iso3")
    mou15, names = list(alloc.index), alloc["country"].to_dict()
    I, P = hm.load_inputs(), hm.load_params()
    ci, lines = I["ci"], I["lines"]
    allc = [i for i in ci.index if len(lines[lines.iso3 == i])]
    F = hm.Fiscal(*scn.DEFAULT_FISCAL)
    rows = []
    for i in allc:
        for name in channel_scenarios(1.0):
            base = channel_base(lines, i, name)
            if base < 1e5:
                continue
            f = min(1.0, TARGET / base) if base > 2 * TARGET else 0.5
            for lab, ff in (("full", f), ("half", f / 2)):
                sc = channel_scenarios(ff)[name]
                r = hm.run_country(i, sc, F, I, P, n_draws=0, keep_draws=True, mortality_trend=rr.TREND)
                m = measure(r)
                rows.append({"iso3": i, "channel": name, "size": lab, "cut_fraction": ff, "channel_base_usd": base, **m})
    R = pd.DataFrame(rows)
    R.to_csv(HERE / "channels.csv", index=False)
    full = R[R["size"] == "full"].set_index(["iso3", "channel"])
    half = R[R["size"] == "half"].set_index(["iso3", "channel"])
    per = full.copy()
    for m in list(SERV) + ["all6", "PMTCT", "deaths_5y", "service_money"]:
        per[m] = full[m] / (full["aid_lost_per_year"] / 1e6)
    per_h = half.copy()
    for m in list(SERV) + ["all6", "deaths_5y"]:
        per_h[m] = half[m] / (half["aid_lost_per_year"] / 1e6)
    nonlin = [(i, c, per.loc[(i, c), "all6"], per_h.loc[(i, c), "all6"]) for (i, c) in per.index
              if abs(per.loc[(i, c), "all6"] - per_h.loc[(i, c), "all6"]) > 0.02 * max(abs(per.loc[(i, c), "all6"]), 1e-9)]

    def pooled(isos, label):
        out = []
        for c in channel_scenarios(1.0):
            sub = full[full.index.get_level_values("iso3").isin(isos) & (full.index.get_level_values("channel") == c)]
            if not len(sub):
                continue
            aid = sub["aid_lost_per_year"].sum() / 1e6
            out.append([c, len(sub), fmt(aid, 1)] + [fmt(sub[m].sum() / aid) for m in ["ART", "TB treatment", "Bednets", "Spraying", "Malaria treatment", "Vaccines", "all6"]]
                       + [f"{sub['deaths_5y'].sum() / aid:.0f}", f"{sub['service_money'].sum() / sub['aid_lost_per_year'].sum():.0%}"]
                       + [f"{(sub[f'mix_{b}'] * sub['aid_lost_per_year']).sum() / sub['aid_lost_per_year'].sum():.0%}" for b in hm.BUCKETS])
        return [f"**{label}** (people on service kept per US$1M of aid per year; pooled = sum of people / sum of money):", "",
                md_table(["Channel", "Countries", "Aid lost US$M/yr (sum of the test cuts)", "ART patient-years", "TB courses", "Bednets", "People sprayed", "Malaria cases treated",
                          "Children vaccinated", "All six services", "Deaths 2026-30 per US$1M/yr (secondary)", "Share of money on service lines"] + [f"Mix {b}" for b in hm.BUCKETS], out), ""]

    md = ["# W-7. Channel comparison: what US$1M buys through each channel (no model changes)", "",
          "Generated by `audit/channels/run_channels.py`. Each channel is cut alone (`health_model.Scenario`: a donor cut on US direct "
          "channels, a donor x channel pair cut, or a channel cut for every donor) by the fraction that loses US$10M a year "
          "(half the channel's 2021-23 baseline where the baseline is below US$20M), sudden path, five years, no government "
          "response, death-rate trends on, central runs. People on service are the yearly full-cost equivalents after the 15% "
          "continuity assumption, per US$1M of aid lost per year, so channels are compared at equal money. The disease mix is "
          "the share of the lost money by disease (what the channel funds in that country); the share on service lines is the "
          "part of the money the model turns into services (the rest is prevention without units, OVC, testing beyond the "
          "kappa share, programme management and systems).", ""]
    md += ["## Step 1. Pooled results", ""] + pooled(mou15, "15 MOU countries") + pooled(allc, f"All {len(allc)} dashboard countries")
    md += ["Linearity: " + ("the full and half-size cuts give the same people per US$1M within 2% everywhere" if not nonlin else
                            f"{len(nonlin)} country x channel cases differ by more than 2% between the full and half-size cuts (caps or ART cohort rule): "
                            + "; ".join(f"{i} {c} ({x:,.0f} vs {y:,.0f})" for i, c, x, y in nonlin[:12]) + (" ..." if len(nonlin) > 12 else "")) + ".",
           "Capped lines (full cuts): " + ("; ".join(f"{i} {c}: {v}" for (i, c), v in full["capped"].items() if v) or "none") + ".", ""]
    md += ["## Step 2. By country, 15 MOU countries (people on service kept per US$1M of aid per year)", ""]
    for c in channel_scenarios(1.0):
        sub = per[per.index.get_level_values("channel") == c]
        sub = sub[sub.index.get_level_values("iso3").isin(mou15)]
        if not len(sub):
            continue
        md += [f"**{c}**", "",
               md_table(["Country", "Channel baseline US$M/yr", "Test cut", "ART patient-years", "TB courses", "Bednets", "Children vaccinated", "All six services", "Deaths 2026-30 (secondary)", "Share on service lines", "Mix HIV / TB / malaria / imm"],
                        [[names[i], fmt(r.channel_base_usd / 1e6, 1), f"{r.cut_fraction:.0%}", fmt(r.ART), fmt(r["TB treatment"]), fmt(r.Bednets), fmt(r.Vaccines), fmt(r.all6), f"{r.deaths_5y:.0f}",
                          f"{r.service_money / 1e6:.0%}", " / ".join(f"{r[f'mix_{b}']:.0%}" for b in hm.BUCKETS)] for (i, _), r in sub.iterrows()]), ""]
    # the preset's multilateral exits vs an equivalent bilateral cut
    md += ["## Step 3. The preset's US multilateral exits against a US bilateral cut of the same size", "",
           "The America First MOUs preset also removes US money through WHO, Gavi and UNFPA (100%) and 23% of US money through "
           "the Global Fund. For each country that package is run alone (no MOU schedule), then a US bilateral (direct-channel) cut "
           "that loses the same modelled money per year.", ""]
    rows2, tot = [], {"exits": {}, "bil": {}}
    for i in mou15:
        sc = hm.Scenario(name="exits", pair=dict(scn.US_MULTI_EXITS))
        r = hm.run_country(i, sc, F, I, P, n_draws=a.draws, keep_draws=True, mortality_trend=rr.TREND)
        me = measure(r)
        usb = channel_base(lines, i, "US bilateral (direct channels)")
        f = me["aid_lost_per_year"] / usb if usb else np.nan
        if f > 1:
            f = 1.0
        rb = hm.run_country(i, hm.Scenario(name="bil", src_direct={"United States": f}), F, I, P, n_draws=a.draws, keep_draws=True, mortality_trend=rr.TREND)
        mb = measure(rb)
        for k, m in (("exits", me), ("bil", mb)):
            for x in ["aid_lost_per_year", "ART", "TB treatment", "Bednets", "Vaccines", "all6", "deaths_5y"]:
                tot[k][x] = tot[k].get(x, 0.0) + m[x]
        rows2.append([names[i], fmt(me["aid_lost_per_year"] / 1e6, 1), f"{f:.1%}", fmt(me["ART"]), fmt(mb["ART"]), fmt(me["TB treatment"]), fmt(mb["TB treatment"]),
                      fmt(me["Bednets"]), fmt(mb["Bednets"]), fmt(me["Vaccines"]), fmt(mb["Vaccines"]), fmt(me["all6"]), fmt(mb["all6"]),
                      f"{fmt(me['deaths_5y'])} ({fmt(r['totals']['deaths_5y_lo'])}-{fmt(r['totals']['deaths_5y_hi'])})",
                      f"{fmt(mb['deaths_5y'])} ({fmt(rb['totals']['deaths_5y_lo'])}-{fmt(rb['totals']['deaths_5y_hi'])})"])
    e, b = tot["exits"], tot["bil"]
    rows2.append(["TOTAL", fmt(e["aid_lost_per_year"] / 1e6, 1), "", fmt(e["ART"]), fmt(b["ART"]), fmt(e["TB treatment"]), fmt(b["TB treatment"]), fmt(e["Bednets"]), fmt(b["Bednets"]),
                  fmt(e["Vaccines"]), fmt(b["Vaccines"]), fmt(e["all6"]), fmt(b["all6"]), fmt(e["deaths_5y"]), fmt(b["deaths_5y"])])
    md += [md_table(["Country", "Aid lost US$M/yr (exits)", "Equivalent bilateral cut", "ART py lost: exits", "bilateral", "TB courses: exits", "bilateral", "Bednets: exits", "bilateral",
                     "Children unvaccinated: exits", "bilateral", "All six: exits", "bilateral", "Deaths 2026-30: exits (range)", "bilateral (range)"], rows2), ""]
    md += ["## Step 4. Reading and caveats", "",
           "- The channel's disease and line mix in each country decides what a dollar buys: Gavi money is vaccines (and systems "
           "money the model treats as above-site), Global Fund money is a mix with more malaria and TB and more unspecified and "
           "systems money, US bilateral money is mostly HIV treatment and care. 'People' therefore favours malaria-heavy channels "
           "(a bednet costs US$2.20), ART patient-years favour US bilateral money, and TB courses the Global Fund.",
           "- Cuts to multilateral channels are modelled as a uniform share of every donor's money through that channel in the "
           "country's 2021-23 mix; how the Global Fund or Gavi would actually reallocate a shortfall across countries and "
           "programmes is not modelled (the dashboard's 'Global Fund & Gavi shortfalls' preset carries the same limitation).",
           "- Where a line is capped at the people covered or donor money exceeds the donor-funded pool, people per dollar fall "
           "with the size of the cut; the half-size check above lists those cases.", ""]
    (HERE / "RESULTS_channels.md").write_text("\n".join(md))
    print("wrote RESULTS_channels.md, channels.csv; nonlinear cases", len(nonlin))


if __name__ == "__main__":
    main()
