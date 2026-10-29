"""
Part 3 of the World Bank GRPH 2025 cross-check: the implied percentage fall in the model's baseline donor health aid
under each preset (from the precomputed All Countries files), for all 70 countries with aid and for the countries the
report covers, plus a "World Bank Table A2.3"-style scenario (US bilateral -60%, Germany -10%, France -25%, UK -40%,
multilaterals and other donors 0%) evaluated on the model's aid cells. Money only, plus central deaths for the
A2.3-style scenario. Read-only.

    python audit/crossroads/scenario_crosscheck.py
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

wb = pd.read_csv(HERE / "wb_grph_appendix4.csv")
overlap = sorted(set(wb.iso3))
inputs, ptab = hm.load_inputs(), hm.load_params()
rows = []
for preset in scn.PRECOMPUTED_PRESETS:
    A = scn.load_precomputed(hm.MODEL_DIR, preset)
    sub = A[A.iso3.isin(overlap)]
    rows.append({"preset": preset, "display": scn.display_name(preset), "countries": len(A),
                 "base_usd_bn": A.base_usd.sum() / 1e9, "gross_loss_usd_bn": A.gross_loss_usd.sum() / 1e9,
                 "implied_fall_all": A.gross_loss_usd.sum() / A.base_usd.sum(),
                 "countries_overlap": len(sub),
                 "implied_fall_overlap": sub.gross_loss_usd.sum() / sub.base_usd.sum(),
                 "deaths_5y": A.deaths_5y.sum()})
# World Bank Table A2.3 assumptions on the model's cells (bilateral only, i.e. direct channels; 0% via multilaterals)
sc = hm.Scenario(name="WB GRPH 2025 (Table A2.3)")
sc.src_direct = {"United States": 0.60, "Germany": 0.10, "France": 0.25, "United Kingdom": 0.40}
res = hm.run_all(sc, hm.Fiscal(), inputs, ptab, n_draws=0)
sub = res[res.iso3.isin(overlap)]
rows.append({"preset": "WB_A2.3_style", "display": "World Bank GRPH 2025 (Table A2.3 assumptions)", "countries": len(res),
             "base_usd_bn": res.base_usd.sum() / 1e9, "gross_loss_usd_bn": res.gross_loss_usd.sum() / 1e9,
             "implied_fall_all": res.gross_loss_usd.sum() / res.base_usd.sum(), "countries_overlap": len(sub),
             "implied_fall_overlap": sub.gross_loss_usd.sum() / sub.base_usd.sum(), "deaths_5y": res.deaths_5y.sum()})
res.to_csv(HERE / "part3_wb_a23_style_all_countries.csv", index=False)
out = pd.DataFrame(rows)
out.to_csv(HERE / "part3_preset_implied_falls.csv", index=False)
print(out.round(3).to_string())
# how the fall splits by channel type in the model's baseline (for the off-budget comparison)
L = inputs["lines"]
direct = L.chan_grp.isin(hm.DIRECT_CHANNELS)
print("baseline via direct channels (bilateral/NGO/Gates direct/other):", round(L[direct].usd.sum() / L.usd.sum(), 3))
print("US share of baseline:", round(L[L.src_grp == "United States"].usd.sum() / L.usd.sum(), 3),
      "| US direct share of baseline:", round(L[(L.src_grp == "United States") & direct].usd.sum() / L.usd.sum(), 3))
