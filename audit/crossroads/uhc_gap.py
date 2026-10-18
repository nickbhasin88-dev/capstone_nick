"""
Part 5 of the World Bank GRPH 2025 cross-check: an illustrative UHC financing gap indicator (design study only).

gap share = 1 - (government health spending + donor health spending) per capita / WHO Progress minimum benchmark
Model side (2023 US$): IHME GHES 2023 per capita + IHME DAH 2023 (all purposes) per capita; after Full US exit the
model's gross aid lost per capita is subtracted (no replacement), or the net loss after 'As much as fiscal space
allows' (central run). Benchmark: the report's per-country WHO Progress value (Appendix 4, 2024 US$) x 304.702/313.689.
Report side (2024 US$): PHE + off-budget DAH vs the same benchmark, 2024 and 2030 (projected).
Also written: the report's own 'WHO government gap' check (= benchmark - PHE - off-budget DAH).

    python audit/crossroads/uhc_gap.py
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

D = 304.702 / 313.689
FOCUS = ["KEN", "NGA", "MOZ", "ZAF", "UGA", "IND",                       # Part 4 focus countries
         "COD", "LBR", "VNM", "BFA", "LAO", "CIV", "MWI", "AGO", "SEN", "ETH", "NER", "BGD"]   # named in the report, pp. 34-35
wb = pd.read_csv(HERE / "wb_grph_appendix4.csv")
chk = wb.assign(calc=wb.who_benchmark_pc - wb.phe_pc - wb.offbudget_dah_pc)
print("report gap identity: max |WHO government gap - (benchmark - PHE - off-budget DAH)| =",
      round(float((chk.who_gov_gap_pc - chk.calc).abs().max()), 2), "(rounding)")
w24 = wb[wb.year == 2024].set_index("iso3")
w30 = wb[wb.year == 2030].set_index("iso3")
inputs, ptab = hm.load_inputs(), hm.load_params()
ci = inputs["ci"]
sc = scn.build_scenario("Full US exit", {}, ci)
rows = []
for c in FOCUS:
    r = ci.loc[c]
    pop = float(r["sp_pop_totl"])
    G = float(r["ghes_2023"]) / pop
    Dah = float(r["dah_2023"]) / pop
    none = hm.run_country(c, sc, hm.Fiscal(), inputs, ptab, n_draws=0)["totals"]
    mx = hm.run_country(c, sc, hm.Fiscal(mode="max"), inputs, ptab, n_draws=0)["totals"]
    B = float(w24.loc[c, "who_benchmark_pc"]) * D if c in w24.index else np.nan
    rec = {"iso3": c, "country": hm.load_inputs()["ci"].index.get_loc(c) and str(r.get("income_group")),
           "benchmark_pc_2023usd": B, "model_ghes_pc_2023": G, "model_dah_pc_2023_ihme": Dah,
           "model_modelled_aid_pc": none["base"] / pop, "model_loss_pc_full_us_exit": none["gross"] / pop,
           "model_net_loss_pc_fiscal_space": mx["net"] / pop,
           "before_spend_pc": G + Dah, "after_norepl_spend_pc": G + Dah - none["gross"] / pop,
           "after_fiscal_space_spend_pc": G + Dah - mx["net"] / pop}
    for k in ("before", "after_norepl", "after_fiscal_space"):
        rec[f"{k}_gap_share"] = 1 - rec[f"{k}_spend_pc"] / B if B == B else np.nan
    if c in w24.index:
        rec.update({"wb_phe_pc_2024": float(w24.loc[c, "phe_pc"]), "wb_offdah_pc_2024": float(w24.loc[c, "offbudget_dah_pc"]),
                    "wb_benchmark_pc_2024": float(w24.loc[c, "who_benchmark_pc"]),
                    "wb_gap_share_2024": 1 - (w24.loc[c, "phe_pc"] + w24.loc[c, "offbudget_dah_pc"]) / w24.loc[c, "who_benchmark_pc"],
                    "wb_gap_share_2030": 1 - (w30.loc[c, "phe_pc"] + w30.loc[c, "offbudget_dah_pc"]) / w30.loc[c, "who_benchmark_pc"]})
    rows.append(rec)
T = pd.DataFrame(rows).set_index("iso3").drop(columns="country")
T.to_csv(HERE / "part5_uhc_gap.csv")
pd.set_option("display.width", 250)
print(T[["benchmark_pc_2023usd", "model_ghes_pc_2023", "model_dah_pc_2023_ihme", "model_loss_pc_full_us_exit", "model_net_loss_pc_fiscal_space",
         "before_gap_share", "after_norepl_gap_share", "after_fiscal_space_gap_share", "wb_gap_share_2024", "wb_gap_share_2030"]].round(2).to_string())
