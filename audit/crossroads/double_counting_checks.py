"""
Part 4 of the World Bank GRPH 2025 cross-check: numeric evidence for the double-counting and consistency audit.
Runs the model (central parameters, Full US exit) for all dashboard countries and the six focus countries and writes
audit/crossroads/part4_*.csv. Read-only: nothing here changes model code, inputs or outputs.

    python audit/crossroads/double_counting_checks.py
"""
from pathlib import Path
import sys
import numpy as np
import pandas as pd

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT))
import health_model as hm       # noqa: E402
import scenarios as scn         # noqa: E402

FOCUS = ["KEN", "NGA", "MOZ", "ZAF", "UGA", "IND"]
inputs, ptab = hm.load_inputs(), hm.load_params()
ci = inputs["ci"]
sc = scn.build_scenario("Full US exit", {}, ci)
countries = [c for c in ci.index if c in set(inputs["lines"].iso3)]

# ---- check 6 / 2: every country, central run, no replacement: units vs pools, money conservation ----
rows, bucket_rows = [], []
for c in countries:
    r = hm.run_country(c, sc, hm.Fiscal(), inputs, ptab, n_draws=0)
    L = r["lines"].set_index("line")
    for l in hm.ALL_DIRECT:
        x = L.loc[l]
        covered = x["cov0"] * x["need"] if pd.notna(x["cov0"]) and pd.notna(x["need"]) else np.nan
        rows.append({"iso3": c, "line": l, "base_usd": x["base_usd"], "gross_loss_usd": x["gross_loss_usd"],
                     "units_lost": x["units_lost"], "donor_funded_units": x["donor_funded_units"],
                     "people_covered": covered, "donor_share_ext": x["donor_share_ext"],
                     "pool": covered * x["donor_share_ext"] if pd.notna(covered) else np.nan,
                     "capped": x["capped"], "donor_exceeds_cost": x["donor_exceeds_cost"],
                     "deaths_5y": x["deaths_5y"]})
    B = r["buckets"].set_index("bucket")
    for b in hm.BUCKETS:
        direct = [l for l in hm.DIRECT[b]] + hm.LINKED_IN[b]
        bucket_rows.append({"iso3": c, "bucket": b, "bucket_gross": B.loc[b, "gross_loss_usd"],
                            "lines_gross": float(L.loc[direct, "gross_loss_usd"].sum()),
                            "nonservice_gross": B.loc[b, "gross_loss_usd"] - float(L.loc[direct, "gross_loss_usd"].sum()),
                            "bucket_base": B.loc[b, "base_usd"], "lines_base": float(L.loc[direct, "base_usd"].sum())})
U = pd.DataFrame(rows)
U["units_over_pool"] = U["units_lost"] > U["pool"] * (1 + 1e-9)
U["units_over_covered"] = U["units_lost"] > U["people_covered"] * (1 + 1e-9)
U.to_csv(HERE / "part4_units_vs_pools.csv", index=False)
BB = pd.DataFrame(bucket_rows)
BB.to_csv(HERE / "part4_bucket_money.csv", index=False)
print("lines where units lost exceed people covered:", int(U["units_over_covered"].sum()))
print("lines where units lost exceed the donor-funded pool (covered x external share):", int(U["units_over_pool"].sum()))
print(U[U["units_over_pool"]].groupby("line").size().to_dict())
print("ART: units lost > donor-funded units (own treatment money / cost):",
      int((U[(U.line == "hiv_art")]["units_lost"] > U[(U.line == "hiv_art")]["donor_funded_units"] * (1 + 1e-9)).sum()), "countries")
print("nonservice share of gross loss by bucket (all countries):",
      (BB.groupby("bucket")["nonservice_gross"].sum() / BB.groupby("bucket")["bucket_gross"].sum()).round(3).to_dict())
print("any negative nonservice:", bool((BB["nonservice_gross"] < -1e-6).any()))

# ---- check 6: the HIV testing-and-care line's contribution to ART units and deaths (kappa 0 vs default) ----
pt0 = ptab.copy()
pt0.loc["hss_kappa", ["central", "low", "high"]] = 0.0
k = []
for c in FOCUS + ["ALL"]:
    cs = countries if c == "ALL" else [c]
    a = sum(hm.run_country(x, sc, hm.Fiscal(), inputs, ptab, n_draws=0)["lines"].set_index("line").loc["hiv_art", ["units_lost", "deaths_5y"]] for x in cs)
    b = sum(hm.run_country(x, sc, hm.Fiscal(), inputs, pt0, n_draws=0)["lines"].set_index("line").loc["hiv_art", ["units_lost", "deaths_5y"]] for x in cs)
    k.append({"iso3": c, "art_units_default": a["units_lost"], "art_units_kappa0": b["units_lost"],
              "art_deaths_default": a["deaths_5y"], "art_deaths_kappa0": b["deaths_5y"]})
K = pd.DataFrame(k)
K["units_from_care_money"] = K["art_units_default"] - K["art_units_kappa0"]
K["deaths_from_care_money"] = K["art_deaths_default"] - K["art_deaths_kappa0"]
K.to_csv(HERE / "part4_care_line_contribution.csv", index=False)
print(K.round(0).to_string())

# ---- check 2: replacement never exceeds the loss, the capacity (when capped) or any line's loss ----
rep = []
for c in FOCUS:
    for name, f, add in [("max", hm.Fiscal(mode="max"), None),
                         ("custom100_capped", hm.Fiscal(mode="custom", theta=1.0, cap_to_space=True), None),
                         ("custom100_uncapped", hm.Fiscal(mode="custom", theta=1.0, cap_to_space=False), None),
                         ("gradual_1pt", hm.Fiscal(mode="gradual"), None),
                         ("max_lives_first", hm.Fiscal(mode="max", allocation="lives_first"), None)]:
        if name == "gradual_1pt":
            hb = hm.health_budget(c, inputs)
            add = hm.gov_add_from_points([1, 2, 3, 4, 5], hb["gov_spend_usd"])
        r = hm.run_country(c, sc, f, inputs, ptab, n_draws=0, gov_add_usd=add)
        T, F, L = r["totals"], r["fiscal"], r["lines"]
        rep.append({"iso3": c, "option": name, "gross": T["gross"], "replaced": T["replaced"], "capacity": F["capacity"],
                    "replaced_le_gross": T["replaced"] <= T["gross"] + 1e-6,
                    "replaced_le_capacity": T["replaced"] <= F["capacity"] + 1e-6,
                    "any_line_replaced_gt_lost": bool((L["replaced_usd"] > L["gross_loss_usd"] + 1e-6).any()),
                    "deaths_5y": T["deaths_5y"]})
R = pd.DataFrame(rep)
R.to_csv(HERE / "part4_replacement_bounds.csv", index=False)
print(R.to_string())

# ---- check 6: unspecified-money shares sum to 1 ----
for tag in ("hiv", "tb", "malaria"):
    cols = [f"unspec_{tag}_{c}" for c in ("treatment", "prevention", "testing", "rssh", "pm")]
    s = ci[cols].sum(axis=1)
    print(f"unspec_{tag}: shares sum to 1 in {int((s.sub(1).abs() < 1e-6).sum())} of {len(ci)} rows; min {s.min():.4f} max {s.max():.4f}; NaN rows {int(ci[cols].isna().any(axis=1).sum())}")

# ---- check 6: TB-HIV overlap order of magnitude (people who lose both ART and TB treatment) ----
ov = []
for c in FOCUS:
    r = hm.run_country(c, sc, hm.Fiscal(), inputs, ptab, n_draws=0)
    L = r["lines"].set_index("line")
    row = ci.loc[c]
    plhiv = float(row["plhiv"])
    art_off = L.loc["hiv_art", "units_lost"]
    tb_deaths = L.loc[["tb_ds", "tb_dr"], "deaths_5y"].sum()
    h = float(row.get("tb_hiv_share", 0.0))
    ov.append({"iso3": c, "art_people_off": art_off, "plhiv": plhiv, "share_plhiv_off": art_off / plhiv if plhiv else np.nan,
               "tb_deaths_5y": tb_deaths, "tb_hiv_share": h,
               "overlap_upper_bound_deaths": tb_deaths * h * (art_off / plhiv if plhiv else 0)})
O = pd.DataFrame(ov)
O.to_csv(HERE / "part4_tb_hiv_overlap.csv", index=False)
print(O.round(3).to_string())
print("done")
