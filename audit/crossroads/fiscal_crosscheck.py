"""
Part 2 of the World Bank GRPH 2025 cross-check: compare the model's fiscal inputs with the report's Appendix 4 data
for every overlapping country. Compare only; nothing here feeds the model.

    python audit/crossroads/fiscal_crosscheck.py

Currency: the report is in constant 2024 US$; the model in constant 2023 US$. The model's inflate() (health_model.py
line 426) moves study costs between years with the US CPI-U annual average (BLS series CUUR0000SA0; CPI_U dict, line
422, 2023 = 304.702). The same logic moves 2024 US$ to 2023 US$ by 304.702 / 313.689; the 2024 annual average
(313.689) is not in the code's table and is taken from BLS (CUUR0000SA0, annual average 2024). This is a US-price
deflator; the report built its own constant-2024 series with GDP deflators and exchange rates (p. 22 note 1), so
the conversion is approximate (about -2.9%).
"""
from pathlib import Path
import sys
import numpy as np
import pandas as pd

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT))
import health_model as hm       # noqa: E402

CPI_2023, CPI_2024 = 304.702, 313.689
D = CPI_2023 / CPI_2024          # 2024 US$ -> 2023 US$

wb = pd.read_csv(HERE / "wb_grph_appendix4.csv")
w24 = wb[wb.year == 2024].set_index("iso3")
w30 = wb[wb.year == 2030].set_index("iso3")
inputs = hm.load_inputs()
ci = inputs["ci"]
A = pd.read_csv(hm.MODEL_DIR / "all_countries_Full_US_exit.csv").set_index("iso3")
isos = [c for c in w24.index if c in ci.index]

rows = []
for c in isos:
    r, a = ci.loc[c], (A.loc[c] if c in A.index else None)
    pop = float(r["sp_pop_totl"])
    fs = hm.fiscal_space(r, "p75")
    fs90 = hm.fiscal_space(r, "p90")
    m = pd.read_csv(ROOT / "macro_data" / f"{c}.csv").set_index("year")
    rev24, exp24 = (float(m.loc[2024, "gov_revenue_pct_gdp"]), float(m.loc[2024, "gov_expenditure_pct_gdp"])) if 2024 in m.index else (np.nan, np.nan)
    phe24, phe30 = float(w24.loc[c, "phe_pc"]), float(w30.loc[c, "phe_pc"])
    g_wb = phe30 / phe24 - 1 if phe24 > 0 else np.nan            # = post-interest GGE per capita growth (report p. 66)
    cls = "contraction" if g_wb < 0 else "stagnation" if g_wb <= 0.10 else "expansion"
    rows.append({
        "iso3": c, "country": w24.loc[c, "country"], "wb_income_group": w24.loc[c, "income_group"], "model_income_group": r.get("income_group"),
        # (a) current government health spending per capita
        "model_ghes_pc_2023": float(r["ghes_2023"]) / pop,                      # IHME GHES 2023 / WDI population
        "wb_phe_pc_2024_in_2023usd": phe24 * D,
        "ratio_a_model_over_wb": (float(r["ghes_2023"]) / pop) / (phe24 * D) if phe24 > 0 else np.nan,
        "wb_phe_minus_ihme_ghes_pc": phe24 * D - float(r["ghes_2023"]) / pop,   # rough proxy for on-budget DAH + definitions
        "model_dah_pc_2023_ihme": float(r["dah_2023"]) / pop,                   # IHME DAH, all purposes, 2023
        "wb_offbudget_dah_pc_2024_in_2023usd": float(w24.loc[c, "offbudget_dah_pc"]) * D,
        "ratio_dah_ihme_over_wb_offbudget": (float(r["dah_2023"]) / pop) / (float(w24.loc[c, "offbudget_dah_pc"]) * D) if w24.loc[c, "offbudget_dah_pc"] > 0 else np.nan,
        # (b) fiscal outlook
        "wb_phe_growth_2024_30": g_wb, "wb_class": cls,
        "wb_phe_annual_growth": (1 + g_wb) ** (1 / 6) - 1 if g_wb == g_wb else np.nan,
        "wb_dphe_pc_2024_30_in_2023usd": (phe30 - phe24) * D,
        "model_capacity_pc_p75": fs["capacity"] / pop, "model_capacity_pc_p90": fs90["capacity"] / pop,
        "model_capacity_pct_ghes_p75": fs["capacity"] / fs["ghes"] if fs["ghes"] else np.nan,
        "model_surge_rate_p75": fs["surge_rate"], "model_ghes_growth_median": fs["ghes_growth_median"],
        "model_stress_factor": fs["stress_factor"],
        "ratio_b_capacity_over_wb_dphe": (fs["capacity"] / pop) / ((phe30 - phe24) * D) if phe30 > phe24 else np.nan,
        "ihme_expected_ghes_growth_2023_30_unused": float(r["ghes_2030_expected"]) / float(r["ghes_2023"]) - 1 if r["ghes_2023"] > 0 else np.nan,
        "model_full_us_exit_loss_pc": (float(a["gross_loss_usd"]) / pop) if a is not None else np.nan,
        "model_loss_over_capacity": (float(a["gross_loss_usd"]) / fs["capacity"]) if a is not None and fs["capacity"] > 0 else np.nan,
        # (c) interest
        "model_interest_pct_revenue": fs["interest_pct_revenue"], "model_interest_year": fs["interest_year"],
        "weo_rev_pct_gdp_2024": rev24, "weo_exp_pct_gdp_2024": exp24,
        "model_interest_pct_gge_approx": fs["interest_pct_revenue"] * rev24 / exp24 if exp24 else np.nan,
    })
T = pd.DataFrame(rows).set_index("iso3")
T.to_csv(HERE / "part2_fiscal_comparison.csv")

pd.set_option("display.width", 250)
print(f"deflator 2024->2023 US$ = {D:.4f}; {len(T)} overlapping countries\n")
print("(a) government health spending per capita: model IHME GHES 2023 vs WB PHE 2024 (2023 US$)")
print(T["ratio_a_model_over_wb"].describe().round(2).to_string())
fa = T[(T.ratio_a_model_over_wb > 1.5) | (T.ratio_a_model_over_wb < 0.67)]
print("flagged (a):", len(fa))
print(fa[["country", "model_ghes_pc_2023", "wb_phe_pc_2024_in_2023usd", "ratio_a_model_over_wb", "wb_phe_minus_ihme_ghes_pc"]].round(1).sort_values("ratio_a_model_over_wb").to_string())
print("\nIHME DAH (all purposes) vs WB off-budget DAH per capita, ratio:", T["ratio_dah_ihme_over_wb_offbudget"].describe().round(2).to_dict())
print("\n(b) WB class counts:", T.wb_class.value_counts().to_dict())
print("model capacity (p75) as % of GHES:", (T.model_capacity_pct_ghes_p75 * 100).describe().round(1).to_dict())
print("WB PHE growth 2024-30 (%):", (T.wb_phe_growth_2024_30 * 100).describe().round(1).to_dict())
print("ratio (b) capacity per year / WB 2024-30 PHE increase per capita:", T.ratio_b_capacity_over_wb_dphe.describe().round(2).to_dict())
fb = T[(T.ratio_b_capacity_over_wb_dphe > 1.5) | (T.ratio_b_capacity_over_wb_dphe < 0.67) | (T.wb_class == "contraction")]
print("flagged (b):", len(fb))
print(fb[["country", "wb_class", "wb_phe_growth_2024_30", "wb_dphe_pc_2024_30_in_2023usd", "model_capacity_pc_p75", "model_surge_rate_p75", "model_stress_factor", "ratio_b_capacity_over_wb_dphe", "model_loss_over_capacity"]].round(2).sort_values("ratio_b_capacity_over_wb_dphe").to_string())
print("\n(c) interest: model % of revenue -> approx % of GGE (x WEO 2024 revenue/expenditure)")
box2 = {"MWI": 22.3, "SOM": 0.7, "PAK": 39.9}
for c, v in box2.items():
    if c in T.index:
        print(f"  {c}: model {T.loc[c,'model_interest_pct_revenue']:.1f}% of revenue ({int(T.loc[c,'model_interest_year'])}) -> ~{T.loc[c,'model_interest_pct_gge_approx']:.1f}% of GGE vs Box 2 {v}% of GGE (2024); ratio {T.loc[c,'model_interest_pct_gge_approx']/v:.2f}")
for g, med in (("low_income", 7.5), ("lower_middle_income", 7.3)):
    s = T[T.wb_income_group == g]["model_interest_pct_gge_approx"]
    print(f"  {g}: model median ~{s.median():.1f}% of GGE (n={s.notna().sum()}) vs Box 2 median {med}%")
print("\nfocus countries:")
print(T.loc[[c for c in ["KEN", "NGA", "MOZ", "UGA", "IND", "MWI", "ETH", "COD"] if c in T.index],
            ["model_ghes_pc_2023", "wb_phe_pc_2024_in_2023usd", "ratio_a_model_over_wb", "wb_class", "wb_phe_growth_2024_30", "wb_dphe_pc_2024_30_in_2023usd", "model_capacity_pc_p75", "ratio_b_capacity_over_wb_dphe", "model_interest_pct_revenue", "model_interest_pct_gge_approx"]].round(2).to_string())
