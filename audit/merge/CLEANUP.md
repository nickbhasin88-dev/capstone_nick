# Cleanup of the Mac " 2" duplicate files

29 October 2026, branch chipmunk (bc80136). A " 2" file is a macOS copy named like `health_model 2.py`. Each tracked copy
is compared by git blob with the file of the same name without " 2" on (a) chipmunk, (b) origin/tomato (b10df4c),
(c) origin/main (a33fefb). SAFE = identical to at least one of them, so its content exists elsewhere; KEEP = identical
to none.

| | Files |
|---|---|
| Tracked " 2" files | 156 |
| SAFE | 156 |
| KEEP | 0 |
| identical to all three | 119 |
| identical to tomato only (tomato's versions of files chipmunk takes from main or merges) | 31 |

Untracked " 2" files in the worktree (not ignored): none. Ignored: 9 pytest bytecode caches
`tests/__pycache__/test_* 2.cpython-313-pytest-9.1.1.pyc`, generated from the " 2" test files; not source, not
tracked, left in place (pytest no longer creates them once the " 2" tests are gone).

Step 2 removes every SAFE file with `git rm` (git history keeps them). No KEEP files.

| " 2" file | Original | a. chipmunk | b. tomato | c. main | Class |
|---|---|---|---|---|---|
| `.devcontainer/devcontainer 2.json` | `.devcontainer/devcontainer.json` | yes | yes | yes | SAFE |
| `.streamlit/config 2.toml` | `.streamlit/config.toml` | yes | yes | yes | SAFE |
| `add_constant_dollars 2.py` | `add_constant_dollars.py` | yes | yes | yes | SAFE |
| `audit/AUDIT 2.md` | `audit/AUDIT.md` | yes | yes | yes | SAFE |
| `audit/I-01 2.md` | `audit/I-01.md` | yes | yes | yes | SAFE |
| `audit/I-02_I-03_I-08 2.md` | `audit/I-02_I-03_I-08.md` | yes | yes | yes | SAFE |
| `audit/I-05 2.md` | `audit/I-05.md` | yes | yes | yes | SAFE |
| `audit/I-06_I-11_malaria 2.md` | `audit/I-06_I-11_malaria.md` | yes | yes | yes | SAFE |
| `audit/I-07 2.md` | `audit/I-07.md` | yes | yes | yes | SAFE |
| `audit/I-09_I-27_I-04 2.md` | `audit/I-09_I-27_I-04.md` | yes | yes | yes | SAFE |
| `audit/I-10 2.md` | `audit/I-10.md` | yes | yes | yes | SAFE |
| `audit/I-13_I-14_I-15_I-16 2.md` | `audit/I-13_I-14_I-15_I-16.md` | yes | yes | yes | SAFE |
| `audit/I-26_I-17 2.md` | `audit/I-26_I-17.md` | yes | yes | yes | SAFE |
| `audit/METHOD 2.md` | `audit/METHOD.md` | yes | yes | yes | SAFE |
| `audit/after_batch2 2.csv` | `audit/after_batch2.csv` | yes | yes | yes | SAFE |
| `audit/after_do_now 2.csv` | `audit/after_do_now.csv` | yes | yes | yes | SAFE |
| `audit/analysis 2.json` | `audit/analysis.json` | yes | yes | yes | SAFE |
| `audit/archive/README 2.md` | `audit/archive/README.md` | yes | yes | yes | SAFE |
| `audit/archive/analysis 2.py` | `audit/archive/analysis.py` | yes | yes | yes | SAFE |
| `audit/batch2_cohort 2.py` | `audit/batch2_cohort.py` | yes | yes | yes | SAFE |
| `audit/batch2_projection 2.py` | `audit/batch2_projection.py` | yes | yes | yes | SAFE |
| `audit/batch34_art_costs 2.py` | `audit/batch34_art_costs.py` | yes | yes | yes | SAFE |
| `audit/batch34_donor_share 2.py` | `audit/batch34_donor_share.py` | yes | yes | yes | SAFE |
| `audit/batch34_gf_shares 2.py` | `audit/batch34_gf_shares.py` | yes | yes | yes | SAFE |
| `audit/batch34_headline 2.py` | `audit/batch34_headline.py` | yes | yes | yes | SAFE |
| `audit/batch34_tb_costs 2.py` | `audit/batch34_tb_costs.py` | yes | yes | yes | SAFE |
| `audit/batch4b_art_check 2.py` | `audit/batch4b_art_check.py` | yes | yes | yes | SAFE |
| `audit/batch4b_malaria_decomp 2.py` | `audit/batch4b_malaria_decomp.py` | yes | yes | yes | SAFE |
| `audit/before_batch2 2.csv` | `audit/before_batch2.csv` | yes | yes | yes | SAFE |
| `audit/before_batch34 2.csv` | `audit/before_batch34.csv` | yes | yes | yes | SAFE |
| `audit/before_batch4b 2.csv` | `audit/before_batch4b.csv` | yes | yes | yes | SAFE |
| `audit/before_do_now 2.csv` | `audit/before_do_now.csv` | yes | yes | yes | SAFE |
| `audit/checks 2.py` | `audit/checks.py` |  | yes | yes | SAFE |
| `audit/checks_results 2.csv` | `audit/checks_results.csv` |  | yes |  | SAFE |
| `audit/checks_summary 2.csv` | `audit/checks_summary.csv` |  | yes | yes | SAFE |
| `audit/checks_summary 2.md` | `audit/checks_summary.md` |  | yes | yes | SAFE |
| `audit/compare_recompute 2.py` | `audit/compare_recompute.py` | yes | yes | yes | SAFE |
| `audit/cosmetic_fixes 2.md` | `audit/cosmetic_fixes.md` | yes | yes | yes | SAFE |
| `audit/hiv_diff 2.py` | `audit/hiv_diff.py` | yes | yes | yes | SAFE |
| `audit/i07_diff 2.py` | `audit/i07_diff.py` | yes | yes | yes | SAFE |
| `audit/inventory 2.csv` | `audit/inventory.csv` | yes | yes | yes | SAFE |
| `audit/logic_review/batch2_before_after 2.py` | `audit/logic_review/batch2_before_after.py` | yes | yes | yes | SAFE |
| `audit/logic_review/batch34_gf_shares 2.csv` | `audit/logic_review/batch34_gf_shares.csv` | yes | yes | yes | SAFE |
| `audit/logic_review/batch34_reconcile 2.py` | `audit/logic_review/batch34_reconcile.py` | yes | yes | yes | SAFE |
| `audit/logic_review/batch4b_art_check 2.csv` | `audit/logic_review/batch4b_art_check.csv` | yes | yes | yes | SAFE |
| `audit/logic_review/batch4b_before_after 2.md` | `audit/logic_review/batch4b_before_after.md` | yes | yes | yes | SAFE |
| `audit/logic_review/batch4b_reconcile 2.csv` | `audit/logic_review/batch4b_reconcile.csv` | yes | yes | yes | SAFE |
| `audit/logic_review/build_inputs 2.py` | `audit/logic_review/build_inputs.py` | yes | yes | yes | SAFE |
| `audit/logic_review/dashboard 2.md` | `audit/logic_review/dashboard.md` | yes | yes | yes | SAFE |
| `audit/logic_review/do_now_before_after 2.py` | `audit/logic_review/do_now_before_after.py` | yes | yes | yes | SAFE |
| `audit/logic_review/inputs 2.csv` | `audit/logic_review/inputs.csv` | yes | yes | yes | SAFE |
| `audit/logic_review/redteam 2.md` | `audit/logic_review/redteam.md` | yes | yes | yes | SAFE |
| `audit/logic_review/reproduction/compare 2.csv` | `audit/logic_review/reproduction/compare.csv` | yes | yes |  | SAFE |
| `audit/logic_review/sensitivity 2.csv` | `audit/logic_review/sensitivity.csv` | yes | yes | yes | SAFE |
| `audit/logic_review/sensitivity 2.py` | `audit/logic_review/sensitivity.py` | yes | yes | yes | SAFE |
| `audit/minor_diff_counts 2.csv` | `audit/minor_diff_counts.csv` | yes | yes | yes | SAFE |
| `audit/recompute 2.py` | `audit/recompute.py` | yes | yes | yes | SAFE |
| `audit/recompute_notes 2.md` | `audit/recompute_notes.md` | yes | yes | yes | SAFE |
| `audit/snapshot_numbers 2.py` | `audit/snapshot_numbers.py` |  | yes | yes | SAFE |
| `batch34_inputs 2.py` | `batch34_inputs.py` | yes | yes |  | SAFE |
| `budget_section 2.py` | `budget_section.py` | yes | yes | yes | SAFE |
| `country_lists 2.py` | `country_lists.py` | yes | yes | yes | SAFE |
| `docs/file_inventory 2.md` | `docs/file_inventory.md` | yes | yes | yes | SAFE |
| `ext_data/gho/HIV_0000000001 2.csv` | `ext_data/gho/HIV_0000000001.csv` | yes | yes | yes | SAFE |
| `ext_data/gho/HIV_0000000016 2.csv` | `ext_data/gho/HIV_0000000016.csv` | yes | yes | yes | SAFE |
| `ext_data/gho/HIV_0000000020 2.csv` | `ext_data/gho/HIV_0000000020.csv` | yes | yes | yes | SAFE |
| `ext_data/gho/HIV_ARTCOVERAGE 2.csv` | `ext_data/gho/HIV_ARTCOVERAGE.csv` | yes | yes | yes | SAFE |
| `ext_data/gho/MALARIA_EST_CASES 2.csv` | `ext_data/gho/MALARIA_EST_CASES.csv` | yes | yes | yes | SAFE |
| `ext_data/gho/MALARIA_EST_DEATHS 2.csv` | `ext_data/gho/MALARIA_EST_DEATHS.csv` | yes | yes | yes | SAFE |
| `ext_data/gho/MALARIA_EST_INCIDENCE 2.csv` | `ext_data/gho/MALARIA_EST_INCIDENCE.csv` | yes | yes | yes | SAFE |
| `ext_data/gm/ddf--datapoints--ihme_hiv_death--by--country--time 2.csv` | `ext_data/gm/ddf--datapoints--ihme_hiv_death--by--country--time.csv` | yes | yes | yes | SAFE |
| `ext_data/map/incidence_prevalence 2.csv` | `ext_data/map/incidence_prevalence.csv` | yes | yes | yes | SAFE |
| `ext_data/map/irs 2.csv` | `ext_data/map/irs.csv` | yes | yes | yes | SAFE |
| `ext_data/map/itn 2.csv` | `ext_data/map/itn.csv` | yes | yes | yes | SAFE |
| `ext_data/map/pf_cases 2.csv` | `ext_data/map/pf_cases.csv` | yes | yes | yes | SAFE |
| `ext_data/map/pv_cases 2.csv` | `ext_data/map/pv_cases.csv` | yes | yes | yes | SAFE |
| `ext_data/map/treatment 2.csv` | `ext_data/map/treatment.csv` | yes | yes | yes | SAFE |
| `ext_data/sg/ddf--datapoints--all_forms_of_tb_incidence_estimated--by--geo--time 2.csv` | `ext_data/sg/ddf--datapoints--all_forms_of_tb_incidence_estimated--by--geo--time.csv` | yes | yes | yes | SAFE |
| `ext_data/sg/ddf--datapoints--malaria_deaths_in_children_1_59_months_total_deaths--by--geo--time 2.csv` | `ext_data/sg/ddf--datapoints--malaria_deaths_in_children_1_59_months_total_deaths--by--geo--time.csv` | yes | yes | yes | SAFE |
| `ext_data/sg/ddf--datapoints--measles_deaths_in_children_1_59_months_total_deaths--by--geo--time 2.csv` | `ext_data/sg/ddf--datapoints--measles_deaths_in_children_1_59_months_total_deaths--by--geo--time.csv` | yes | yes | yes | SAFE |
| `ext_data/sg/ddf--datapoints--people_living_with_hiv_number_all_ages--by--geo--time 2.csv` | `ext_data/sg/ddf--datapoints--people_living_with_hiv_number_all_ages--by--geo--time.csv` | yes | yes | yes | SAFE |
| `ext_data/sg/ddf--datapoints--pneumonia_deaths_in_children_1_59_months_total_deaths--by--geo--time 2.csv` | `ext_data/sg/ddf--datapoints--pneumonia_deaths_in_children_1_59_months_total_deaths--by--geo--time.csv` | yes | yes | yes | SAFE |
| `ext_data/wdi/gc_dod_totl_gd_zs 2.csv` | `ext_data/wdi/gc_dod_totl_gd_zs.csv` | yes | yes | yes | SAFE |
| `ext_data/wdi/gc_rev_xgrt_gd_zs 2.csv` | `ext_data/wdi/gc_rev_xgrt_gd_zs.csv` | yes | yes | yes | SAFE |
| `ext_data/wdi/gc_xpn_intp_rv_zs 2.csv` | `ext_data/wdi/gc_xpn_intp_rv_zs.csv` | yes | yes | yes | SAFE |
| `ext_data/wdi/gc_xpn_totl_gd_zs 2.csv` | `ext_data/wdi/gc_xpn_totl_gd_zs.csv` | yes | yes | yes | SAFE |
| `ext_data/wdi/sh_dth_mort 2.csv` | `ext_data/wdi/sh_dth_mort.csv` | yes | yes | yes | SAFE |
| `ext_data/wdi/sh_dyn_aids_zs 2.csv` | `ext_data/wdi/sh_dyn_aids_zs.csv` | yes | yes | yes | SAFE |
| `ext_data/wdi/sh_dyn_mort 2.csv` | `ext_data/wdi/sh_dyn_mort.csv` | yes | yes | yes | SAFE |
| `ext_data/wdi/sh_hiv_0014 2.csv` | `ext_data/wdi/sh_hiv_0014.csv` | yes | yes | yes | SAFE |
| `ext_data/wdi/sh_hiv_artc_zs 2.csv` | `ext_data/wdi/sh_hiv_artc_zs.csv` | yes | yes | yes | SAFE |
| `ext_data/wdi/sh_hiv_incd_tl 2.csv` | `ext_data/wdi/sh_hiv_incd_tl.csv` | yes | yes | yes | SAFE |
| `ext_data/wdi/sh_hiv_pmtc_zs 2.csv` | `ext_data/wdi/sh_hiv_pmtc_zs.csv` | yes | yes | yes | SAFE |
| `ext_data/wdi/sh_imm_idpt 2.csv` | `ext_data/wdi/sh_imm_idpt.csv` | yes | yes | yes | SAFE |
| `ext_data/wdi/sh_imm_meas 2.csv` | `ext_data/wdi/sh_imm_meas.csv` | yes | yes | yes | SAFE |
| `ext_data/wdi/sh_mlr_incd_p3 2.csv` | `ext_data/wdi/sh_mlr_incd_p3.csv` | yes | yes | yes | SAFE |
| `ext_data/wdi/sh_mlr_nets_zs 2.csv` | `ext_data/wdi/sh_mlr_nets_zs.csv` | yes | yes | yes | SAFE |
| `ext_data/wdi/sh_mlr_tret_zs 2.csv` | `ext_data/wdi/sh_mlr_tret_zs.csv` | yes | yes | yes | SAFE |
| `ext_data/wdi/sh_mmr_dths 2.csv` | `ext_data/wdi/sh_mmr_dths.csv` | yes | yes | yes | SAFE |
| `ext_data/wdi/sh_tbs_cure_zs 2.csv` | `ext_data/wdi/sh_tbs_cure_zs.csv` | yes | yes | yes | SAFE |
| `ext_data/wdi/sh_tbs_dtec_zs 2.csv` | `ext_data/wdi/sh_tbs_dtec_zs.csv` | yes | yes | yes | SAFE |
| `ext_data/wdi/sh_tbs_incd 2.csv` | `ext_data/wdi/sh_tbs_incd.csv` | yes | yes | yes | SAFE |
| `ext_data/wdi/sh_uhc_sci 2.csv` | `ext_data/wdi/sh_uhc_sci.csv` | yes | yes | yes | SAFE |
| `ext_data/wdi/sh_xpd_ghed_ge_zs 2.csv` | `ext_data/wdi/sh_xpd_ghed_ge_zs.csv` | yes | yes | yes | SAFE |
| `ext_data/wdi/sp_dyn_cbrt_in 2.csv` | `ext_data/wdi/sp_dyn_cbrt_in.csv` | yes | yes | yes | SAFE |
| `ext_data/wdi/sp_dyn_cdrt_in 2.csv` | `ext_data/wdi/sp_dyn_cdrt_in.csv` | yes | yes | yes | SAFE |
| `ext_data/wdi/sp_pop_0014_to 2.csv` | `ext_data/wdi/sp_pop_0014_to.csv` | yes | yes | yes | SAFE |
| `ext_data/wdi/sp_pop_1564_to 2.csv` | `ext_data/wdi/sp_pop_1564_to.csv` | yes | yes | yes | SAFE |
| `ext_data/wdi/sp_pop_totl 2.csv` | `ext_data/wdi/sp_pop_totl.csv` | yes | yes | yes | SAFE |
| `fiscal_inputs 2.py` | `fiscal_inputs.py` |  | yes |  | SAFE |
| `health_model 2.py` | `health_model.py` |  | yes |  | SAFE |
| `hiv_transmission_inputs 2.py` | `hiv_transmission_inputs.py` | yes | yes | yes | SAFE |
| `macro_data/weo_fiscal/weo_balances 2.csv` | `macro_data/weo_fiscal/weo_balances.csv` | yes | yes | yes | SAFE |
| `malaria_inputs 2.py` | `malaria_inputs.py` | yes | yes | yes | SAFE |
| `model_data/all_countries_America_First_MOUs 2.csv` | `model_data/all_countries_America_First_MOUs.csv` |  | yes |  | SAFE |
| `model_data/all_countries_America_First_MOUs_draws 2.csv` | `model_data/all_countries_America_First_MOUs_draws.csv` |  | yes |  | SAFE |
| `model_data/all_countries_Combined_retreat 2.csv` | `model_data/all_countries_Combined_retreat.csv` |  | yes |  | SAFE |
| `model_data/all_countries_Combined_retreat_draws 2.csv` | `model_data/all_countries_Combined_retreat_draws.csv` |  | yes |  | SAFE |
| `model_data/all_countries_Full_US_exit 2.csv` | `model_data/all_countries_Full_US_exit.csv` |  | yes |  | SAFE |
| `model_data/all_countries_Full_US_exit_draws 2.csv` | `model_data/all_countries_Full_US_exit_draws.csv` |  | yes |  | SAFE |
| `model_data/all_countries_Global_Fund_Gavi_shortfalls 2.csv` | `model_data/all_countries_Global_Fund_Gavi_shortfalls.csv` |  | yes |  | SAFE |
| `model_data/all_countries_Global_Fund_Gavi_shortfalls_draws 2.csv` | `model_data/all_countries_Global_Fund_Gavi_shortfalls_draws.csv` |  | yes |  | SAFE |
| `model_data/all_countries_IHME_2025_preliminary_estimates 2.csv` | `model_data/all_countries_IHME_2025_preliminary_estimates.csv` |  | yes |  | SAFE |
| `model_data/all_countries_IHME_2025_preliminary_estimates_draws 2.csv` | `model_data/all_countries_IHME_2025_preliminary_estimates_draws.csv` |  | yes |  | SAFE |
| `model_data/all_countries_OECD_reported_2025_aid_cuts 2.csv` | `model_data/all_countries_OECD_reported_2025_aid_cuts.csv` |  | yes |  | SAFE |
| `model_data/all_countries_OECD_reported_2025_aid_cuts_draws 2.csv` | `model_data/all_countries_OECD_reported_2025_aid_cuts_draws.csv` |  | yes |  | SAFE |
| `model_data/country_profile 2.csv` | `model_data/country_profile.csv` | yes | yes | yes | SAFE |
| `model_data/dah_lines 2.csv` | `model_data/dah_lines.csv` | yes | yes | yes | SAFE |
| `model_data/ihme_trend 2.csv` | `model_data/ihme_trend.csv` | yes | yes | yes | SAFE |
| `model_data/mou_signed 2.csv` | `model_data/mou_signed.csv` | yes | yes | yes | SAFE |
| `model_data/panel 2.csv` | `model_data/panel.csv` | yes | yes | yes | SAFE |
| `model_data/regressions 2.json` | `model_data/regressions.json` | yes | yes | yes | SAFE |
| `model_params 2.csv` | `model_params.csv` |  | yes |  | SAFE |
| `model_section 2.py` | `model_section.py` |  | yes |  | SAFE |
| `paths_ui 2.py` | `paths_ui.py` |  | yes |  | SAFE |
| `prepare_model 2.py` | `prepare_model.py` |  | yes |  | SAFE |
| `requirements-dev 2.txt` | `requirements-dev.txt` | yes | yes | yes | SAFE |
| `scenarios 2.py` | `scenarios.py` |  | yes |  | SAFE |
| `tests/baseline_sudden 2.json` | `tests/baseline_sudden.json` |  | yes |  | SAFE |
| `tests/make_baseline 2.py` | `tests/make_baseline.py` | yes | yes | yes | SAFE |
| `tests/test_budget_section 2.py` | `tests/test_budget_section.py` | yes | yes | yes | SAFE |
| `tests/test_fiscal 2.py` | `tests/test_fiscal.py` |  | yes |  | SAFE |
| `tests/test_hiv 2.py` | `tests/test_hiv.py` |  | yes |  | SAFE |
| `tests/test_i07 2.py` | `tests/test_i07.py` | yes | yes | yes | SAFE |
| `tests/test_malaria 2.py` | `tests/test_malaria.py` |  | yes |  | SAFE |
| `tests/test_minor 2.py` | `tests/test_minor.py` | yes | yes | yes | SAFE |
| `tests/test_mou 2.py` | `tests/test_mou.py` |  | yes |  | SAFE |
| `tests/test_paths 2.py` | `tests/test_paths.py` |  | yes |  | SAFE |
| `tests/test_tb 2.py` | `tests/test_tb.py` | yes | yes | yes | SAFE |
| `theme 2.py` | `theme.py` |  | yes |  | SAFE |
| `unit_cost_reference 2.csv` | `unit_cost_reference.csv` | yes | yes | yes | SAFE |
| `views/1_Dashboard 2.py` | `views/1_Dashboard.py` |  | yes |  | SAFE |
| `views/2_All_Countries 2.py` | `views/2_All_Countries.py` |  | yes |  | SAFE |
| `views/3_Validation 2.py` | `views/3_Validation.py` |  | yes |  | SAFE |
| `views/4_Methods 2.py` | `views/4_Methods.py` |  | yes |  | SAFE |
| `who_inputs 2.py` | `who_inputs.py` | yes | yes | yes | SAFE |

After the cleanup, references in `VERIFICATION.md` and `verify_inventory.py` to tomato's code "kept in the ' 2'
copies" point to files that are now only in git history (commit before this one) and on tomato itself.
