"""
Batch 3+4 country inputs (logic review L-43, IMP-03, IMP-11, IMP-04): patch model_data/country_inputs.csv in place
from the evidence tables in audit/logic_review/ (which are built from the raw datasets by audit/batch34_*.py).

    python batch34_inputs.py --shares     # item 2 (L-43): how unspecified money splits by purpose (Global Fund module shares)
    python batch34_inputs.py --art        # item 4 (IMP-03): site-level ART cost per patient-year by country (GHCC, Rosen 2021)
    python batch34_inputs.py --tb         # item 5 (IMP-11): TB course costs (DS, DR) and the MDR/RR share and enrolment
    python batch34_inputs.py --donor      # item 6 (IMP-04): external (donor) share of disease spending, for the cap rule
    python batch34_inputs.py --art-full   # Batch 4b item 2 (L-50): ART cost per patient-year = min(GHCC-based, observed spending), floored and gated
    python batch34_inputs.py --art-full56 # Batch 5+6 item A1: the same with the observed-spending validity test, the Rosen-based floor and the gate on the final value
    python batch34_inputs.py --donor56    # Batch 5+6 items A2-A3: external share of PUBLIC spending for HIV and immunization; intervention-specific donor shares for the malaria lines
    python batch34_inputs.py --vaccines   # Batch 5+6 item V2: deaths averted per fully immunized child (VIMC) and their timing

Columns written (all with a `_source` column saying whether the value is the country's own or a fallback):
  unspec_<disease>_{treatment,prevention,testing,rssh,pm}   shares of unspecified money by purpose (sum to 1)
  art_site_cost, art_site_cost_lo, art_site_cost_hi          2023 US$ per patient-year, site level (before the markup)
  tb_ds_cost, tb_ds_cost_lo, tb_ds_cost_hi                   2023 US$ per drug-susceptible course (provider, before markup)
  tb_dr_cost, tb_dr_cost_lo, tb_dr_cost_hi                   2023 US$ per drug-resistant course
  tb_rr_share, tb_rr_cov                                     RR-TB incidence / all-forms incidence; RR enrolment / RR incidence (WHO 2024)
  donor_share_{hiv,tb,malaria,imm}                           external share of spending on the disease (0-1)
  donor_share_malaria_prev                                   external share of public malaria spending (bednets, spraying; Batch 4b item 3)
  donor_share_hiv, donor_share_imm (Batch 5+6 item A2)       external share of PUBLIC spending on HIV / immunization (replaces the all-source share)
  donor_share_mal_itn, _mal_irs, _mal_cm (Batch 5+6 item A3) intervention-specific donor share = donor money for the line / (people covered x unit cost), capped at 1
  imm_dpc, imm_dpc_lo, imm_dpc_hi, imm_dpc_lag0..lag9, imm_dpc_beyond_window, imm_q5_ratio, imm_antigens (Batch 5+6 item V2)
                                                             deaths averted per fully immunized child (VIMC, 2015-19, x Q5 ratio) and by years since vaccination
Called on its own after the evidence tables change; prepare_model.py (full rebuild) does not rebuild these columns.
"""
from __future__ import annotations

import sys
from pathlib import Path

import warnings

import numpy as np
import pandas as pd

warnings.simplefilter("ignore", pd.errors.PerformanceWarning)   # many new columns on a wide table

ROOT = Path(__file__).resolve().parent
EV = ROOT / "audit" / "logic_review"
CI_PATH = ROOT / "model_data" / "country_inputs.csv"
DISEASES = {"HIV": "hiv", "TB": "tb", "Malaria": "malaria"}
CATS = ["treatment", "prevention", "testing", "rssh", "pm"]


def apply_shares(ci: pd.DataFrame) -> pd.DataFrame:
    t = pd.read_csv(EV / "batch34_gf_shares.csv")
    for d, tag in DISEASES.items():
        x = t[t.disease == d].set_index("iso3").reindex(ci.index)
        for c in CATS:
            ci[f"unspec_{tag}_{c}"] = x[c]
        ci[f"unspec_{tag}_source"] = x["source"]
    return ci


def apply_art(ci: pd.DataFrame) -> pd.DataFrame:
    t = pd.read_csv(EV / "batch34_art_costs.csv").set_index("iso3").reindex(ci.index)
    ci["art_site_cost"], ci["art_site_cost_lo"], ci["art_site_cost_hi"] = t.site_cost, t.site_lo, t.site_hi
    ci["art_site_cost_source"] = t.source
    ci["art_site_cost_year"] = 2023
    return ci


def apply_tb(ci: pd.DataFrame) -> pd.DataFrame:
    t = pd.read_csv(EV / "batch34_tb_costs.csv").set_index("iso3").reindex(ci.index)
    for k in ("DS", "DR"):
        lk = k.lower()
        ci[f"tb_{lk}_cost"], ci[f"tb_{lk}_cost_lo"], ci[f"tb_{lk}_cost_hi"] = t[f"{k}_cost"], t[f"{k}_lo"], t[f"{k}_hi"]
        ci[f"tb_{lk}_cost_source"] = t[f"{k}_source"]
    ci["tb_cost_year"] = 2023
    ci["tb_rr_share"], ci["tb_rr_cov"] = t.rr_share_inc, t.rr_cov
    ci["tb_rr_source"] = np.where(t.rr_share_inc.notna(), "WHO 2024: RR-TB incidence / all-forms incidence; RR patients started on treatment / RR incidence (capped at 1)", "")
    return ci


def apply_art_full(ci: pd.DataFrame) -> pd.DataFrame:
    t = pd.read_csv(EV / "batch4b_art_check.csv").set_index("iso3").reindex(ci.index)
    ci["art_cost_full"], ci["art_cost_full_lo"], ci["art_cost_full_hi"] = t.final_cost, t.final_lo, t.final_hi
    ci["art_cost_full_source"] = t.final_source
    ci["art_cost_full_year"] = 2023
    return ci


def apply_art_full56(ci: pd.DataFrame) -> pd.DataFrame:
    t = pd.read_csv(EV / "batch56_art_cost.csv").set_index("iso3").reindex(ci.index)
    ci["art_cost_full"], ci["art_cost_full_lo"], ci["art_cost_full_hi"] = t.new_cost, t.new_lo, t.new_hi
    ci["art_cost_full_source"] = t.new_source
    ci["art_cost_full_year"] = 2023
    return ci


def apply_donor56_hiv_imm(ci: pd.DataFrame) -> pd.DataFrame:
    """Batch 5+6 item A2 (L-51): the HIV and immunization pools use the external share of PUBLIC spending."""
    t = pd.read_csv(EV / "batch56_donor_share.csv").set_index("iso3").reindex(ci.index)
    for b, tag in (("HIV", "hiv"), ("Imm", "imm")):
        ci[f"donor_share_{tag}"] = t[f"{b}_pub_share"]
        ci[f"donor_share_{tag}_source"] = t[f"{b}_pub_source"]
        ci[f"donor_share_{tag}_year"] = t[f"{b}_year"]
    return ci


def apply_donor56_malaria(ci: pd.DataFrame) -> pd.DataFrame:
    """Batch 5+6 item A3: intervention-specific donor shares for bednets, spraying and case management."""
    t = pd.read_csv(EV / "batch56_donor_share.csv").set_index("iso3").reindex(ci.index)
    for l in ("mal_itn", "mal_irs", "mal_cm"):
        ci[f"donor_share_{l}"] = t[f"{l}_share"]
        ci[f"donor_share_{l}_source"] = t[f"{l}_share_source"]
    return ci


def apply_vaccines(ci: pd.DataFrame) -> pd.DataFrame:
    """Batch 5+6 item V2: deaths averted per fully immunized child (VIMC) and their timing by years since vaccination."""
    t = pd.read_csv(EV / "batch56_vaccine_country.csv").set_index("iso3").reindex(ci.index)
    cols = ["imm_dpc", "imm_dpc_lo", "imm_dpc_hi", "imm_q5_ratio", "imm_dpc_beyond_window"] + [f"imm_dpc_lag{k}" for k in range(10)]
    for c in cols:
        ci[c] = t[c]
    ci["imm_antigens"], ci["imm_antigens_excluded_zero_coverage"] = t.imm_antigens, t.imm_antigens_excluded_zero_coverage
    ci["imm_dpc_source"], ci["imm_in_vimc"] = t.imm_dpc_source, t.imm_in_vimc
    return ci


def apply_donor(ci: pd.DataFrame) -> pd.DataFrame:
    t = pd.read_csv(EV / "batch34_donor_share.csv").set_index("iso3").reindex(ci.index)
    for b, tag in (("HIV", "hiv"), ("TB", "tb"), ("Malaria", "malaria"), ("Malaria_prev", "malaria_prev"), ("Immunization", "imm")):
        ci[f"donor_share_{tag}"] = t[f"{b}_share"]
        ci[f"donor_share_{tag}_source"] = t[f"{b}_source"]
        ci[f"donor_share_{tag}_year"] = t[f"{b}_year"]
    return ci


def main():
    ci = pd.read_csv(CI_PATH).set_index("iso3")
    done = []
    if "--shares" in sys.argv:
        ci, done = apply_shares(ci), done + ["shares"]
    if "--art" in sys.argv:
        ci, done = apply_art(ci), done + ["art"]
    if "--tb" in sys.argv:
        ci, done = apply_tb(ci), done + ["tb"]
    if "--donor" in sys.argv:
        ci, done = apply_donor(ci), done + ["donor"]
    if "--art-full" in sys.argv:
        ci, done = apply_art_full(ci), done + ["art-full"]
    if "--art-full56" in sys.argv:
        ci, done = apply_art_full56(ci), done + ["art-full56"]
    if "--donor56-hiv-imm" in sys.argv:
        ci, done = apply_donor56_hiv_imm(ci), done + ["donor56-hiv-imm"]
    if "--donor56-malaria" in sys.argv:
        ci, done = apply_donor56_malaria(ci), done + ["donor56-malaria"]
    if "--vaccines" in sys.argv:
        ci, done = apply_vaccines(ci), done + ["vaccines"]
    if not done:
        raise SystemExit(__doc__)
    ci.copy().reset_index().to_csv(CI_PATH, index=False)
    print(f"country_inputs.csv updated: {done}; {len(ci)} countries, {ci.shape[1]} columns")


if __name__ == "__main__":
    main()
