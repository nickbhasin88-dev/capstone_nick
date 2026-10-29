# Merge inventory: main + tomato -> chipmunk (Step 0)

Built 29 October 2026 before any code change. Everything on each branch, so Step 3 can mark each item Present or Missing on chipmunk.

| | Commit | Backup tag |
|---|---|---|
| main | a33fefb ("edit v1", 29 Oct 2026; was 23c4f46 when this work started) | backup-main-2026-10-29 (23c4f46), backup-main-2026-10-29-b (a33fefb) |
| tomato | 733b99f (local; origin/tomato is b10df4c, one commit behind: 733b99f adds WHO findings scripts and slides, no model change) | backup-tomato-2026-10-29 (733b99f) |
| shared base | 178733c (main merged tomato up to Batch 4b on 14 Oct 2026) | |

## Counts

| Item | main | tomato |
|---|---|---|
| Files | 737 | 721 |
| UI items (pages, sections, charts, tables, cards, controls, presets, text) | 313 | 284 |
| Model and UI functions | 544 | 506 |
| Parameters | 46 | 51 |
| Model input files | 27 | 20 |
| Input columns | 218 | 262 |
| Tests | 155 | 69 |
| Checks | 53 | 53 |

UI items by kind: main caption/text block 75, heading 55, card/metric 37, section 35, table 26, control 24, chart 22, tooltip-bearing control 20, preset 9, tab 6, expander 3, download 1; tomato caption/text block 66, card/metric 49, section 39, heading 37, table 32, control 21, chart 17, tooltip-bearing control 16, preset 4, expander 1, download 1, tab 1.

## 1. Files

Categories compare origin/main (a33fefb) with tomato (733b99f); "changed on X only" means the other branch still has the shared-base (178733c) version.

| Category | Files |
|---|---|
| different: changed on both | 20 |
| different: changed on main only | 7 |
| different: changed on tomato only | 16 |
| identical | 521 |
| main only | 173 |
| tomato only | 157 |

Note: 156 of the 173 main-only files are the " 2" copies committed in a33fefb ("edit v1"); each is byte-identical to the tomato (27) or shared-base (129) version of the file without " 2".


### different: changed on both (20)

- `health_model.py`
- `model_data/all_countries_America_First_MOUs.csv`
- `model_data/all_countries_America_First_MOUs_draws.csv`
- `model_data/all_countries_Combined_retreat.csv`
- `model_data/all_countries_Combined_retreat_draws.csv`
- `model_data/all_countries_Full_US_exit.csv`
- `model_data/all_countries_Full_US_exit_draws.csv`
- `model_data/all_countries_Global_Fund_Gavi_shortfalls.csv`
- `model_data/all_countries_Global_Fund_Gavi_shortfalls_draws.csv`
- `model_data/all_countries_IHME_2025_preliminary_estimates.csv`
- `model_data/all_countries_IHME_2025_preliminary_estimates_draws.csv`
- `model_data/all_countries_OECD_reported_2025_aid_cuts.csv`
- `model_data/all_countries_OECD_reported_2025_aid_cuts_draws.csv`
- `model_data/country_inputs.csv`
- `model_section.py`
- `prepare_model.py`
- `scenarios.py`
- `tests/test_hiv.py`
- `tests/test_paths.py`
- `views/4_Methods.py`

### different: changed on main only (7)

- `app.py`
- `paths_ui.py`
- `tests/test_malaria.py`
- `tests/test_mou.py`
- `theme.py`
- `views/1_Dashboard.py`
- `views/2_All_Countries.py`

### different: changed on tomato only (16)

- `README.md`
- `audit/checks_results.csv`
- `audit/logic_review/assumptions.md`
- `audit/logic_review/findings.md`
- `audit/logic_review/improvements.md`
- `audit/logic_review/reproduction/compare.csv`
- `audit/logic_review/reproduction/independent.csv`
- `audit/logic_review/reproduction/notes.md`
- `audit/logic_review/reproduction/repro.py`
- `batch34_inputs.py`
- `docs/SPEC.md`
- `fiscal_inputs.py`
- `model_params.csv`
- `tests/baseline_sudden.json`
- `tests/test_fiscal.py`
- `views/3_Validation.py`

### identical (521)

`.devcontainer/devcontainer.json`, `.gitattributes`, `.gitignore`, `.streamlit/config.toml`, `add_constant_dollars.py`, `audit/AUDIT.md`, `audit/I-01.md`, `audit/I-02_I-03_I-08.md`, `audit/I-05.md`, `audit/I-06_I-11_malaria.md`, `audit/I-07.md`, `audit/I-09_I-27_I-04.md`, `audit/I-10.md`, `audit/I-13_I-14_I-15_I-16.md`, `audit/I-26_I-17.md`, `audit/METHOD.md`, `audit/after_batch2.csv`, `audit/after_do_now.csv`, `audit/analysis.json`, `audit/archive/README.md`, `audit/archive/analysis.py`, `audit/batch2_cohort.py`, `audit/batch2_projection.py`, `audit/batch34_art_costs.py`, `audit/batch34_donor_share.py`, `audit/batch34_gf_shares.py`, `audit/batch34_headline.py`, `audit/batch34_tb_costs.py`, `audit/batch4b_art_check.py`, `audit/batch4b_malaria_decomp.py`, `audit/before_batch2.csv`, `audit/before_batch34.csv`, `audit/before_batch4b.csv`, `audit/before_do_now.csv`, `audit/checks.py`, `audit/checks_summary.csv`, `audit/checks_summary.md`, `audit/compare_recompute.py`, `audit/cosmetic_fixes.md`, `audit/fallbacks.csv`, `audit/fiscal_diff.py`, `audit/hiv_diff.py`, `audit/i01_before_after.py`, `audit/i07_diff.py`, `audit/inventory.csv`, `audit/logic_review/URGENT.md`, `audit/logic_review/batch2_before_after.md`, `audit/logic_review/batch2_before_after.py`, `audit/logic_review/batch2_cohort.csv`, `audit/logic_review/batch2_evidence.md`, `audit/logic_review/batch2_optima_compare.csv`, `audit/logic_review/batch2_projection.csv`, `audit/logic_review/batch2_transmission.csv`, `audit/logic_review/batch34_art_costs.csv`, `audit/logic_review/batch34_before_after.md`, `audit/logic_review/batch34_before_after.py`, `audit/logic_review/batch34_donor_share.csv`, `audit/logic_review/batch34_evidence.md`, `audit/logic_review/batch34_gf_shares.csv`, `audit/logic_review/batch34_reconcile.csv`, `audit/logic_review/batch34_reconcile.py`, `audit/logic_review/batch34_tb_costs.csv`, `audit/logic_review/batch4b_art_check.csv`, `audit/logic_review/batch4b_before_after.md`, `audit/logic_review/batch4b_evidence.md`, `audit/logic_review/batch4b_malaria_decomp.csv`, `audit/logic_review/batch4b_reconcile.csv`, `audit/logic_review/benchmarks.md`, `audit/logic_review/build_coverage.py`, `audit/logic_review/build_inputs.py`, `audit/logic_review/coverage.md`, `audit/logic_review/dashboard.md`, `audit/logic_review/data_requests.md`, `audit/logic_review/do_now_before_after.md`, `audit/logic_review/do_now_before_after.py`, `audit/logic_review/extra_sensitivity.py`, `audit/logic_review/inputs.csv`, `audit/logic_review/inputs.md`, `audit/logic_review/logic.md`, `audit/logic_review/range_test.py`, `audit/logic_review/redteam.md`, `audit/logic_review/redteam_report.md`, `audit/logic_review/reproduction/compare.py`, `audit/logic_review/sensitivity.csv`, `audit/logic_review/sensitivity.py`, `audit/logic_review/tornado.png`, `audit/logic_review/tornado.py`, `audit/logic_review/uncertainty_scope.md`, `audit/make_inventory.py`, `audit/malaria_diff.py`, `audit/minor_diff.py`, `audit/minor_diff_counts.csv`, `audit/outliers.csv`, `audit/recompute.py`, `audit/recompute_compare.csv`, `audit/recompute_notes.md`, `audit/recompute_results.csv`, `audit/sensitivity.csv`, `audit/snapshot_numbers.py`, `budget_section.py`, `cofog_all/AGO.csv`, `cofog_all/AZE.csv`, `cofog_all/BDI.csv`, `cofog_all/BFA.csv`, `cofog_all/BGD.csv`, `cofog_all/BOL.csv`, `cofog_all/BWA.csv`, `cofog_all/CAF.csv`, `cofog_all/CMR.csv`, `cofog_all/DOM.csv`, `cofog_all/EGY.csv`, `cofog_all/ETH.csv`, `cofog_all/FJI.csv`, `cofog_all/GIN.csv`, `cofog_all/GTM.csv`, `cofog_all/HND.csv`, `cofog_all/IDN.csv`, `cofog_all/IND.csv`, `cofog_all/JAM.csv`, `cofog_all/JOR.csv`, `cofog_all/KEN.csv`, `cofog_all/KGZ.csv`, `cofog_all/LBR.csv`, `cofog_all/MDA.csv`, `cofog_all/MDG.csv`, `cofog_all/MNG.csv`, `cofog_all/MOZ.csv`, `cofog_all/MUS.csv`, `cofog_all/NAM.csv`, `cofog_all/NGA.csv`, `cofog_all/NIC.csv`, `cofog_all/NPL.csv`, `cofog_all/PAK.csv`, `cofog_all/PAN.csv`, `cofog_all/PHL.csv`, `cofog_all/PNG.csv`, `cofog_all/SLV.csv`, `cofog_all/SOM.csv`, `cofog_all/STP.csv`, `cofog_all/TGO.csv`, `cofog_all/TJK.csv`, `cofog_all/TLS.csv`, `cofog_all/TZA.csv`, `cofog_all/UGA.csv`, `cofog_all/ZAF.csv`, `cofog_all/ZMB.csv`, `country_data/Angola.csv`, `country_data/Azerbaijan.csv`, `country_data/Bangladesh.csv`, `country_data/Belize.csv`, `country_data/Benin.csv`, `country_data/Bolivia.csv`, `country_data/Botswana.csv`, `country_data/Burkina_Faso.csv`, `country_data/Burundi.csv`, `country_data/Cambodia.csv`, `country_data/Cameroon.csv`, `country_data/Central_African_Republic.csv`, `country_data/Cote_d_Ivoire.csv`, `country_data/Democratic_Republic_of_the_Congo.csv`, `country_data/Djibouti.csv`, `country_data/Dominican_Republic.csv`, `country_data/Egypt.csv`, `country_data/El_Salvador.csv`, `country_data/Ethiopia.csv`, `country_data/Fiji.csv`, `country_data/Ghana.csv`, `country_data/Guatemala.csv`, `country_data/Guinea.csv`, `country_data/Guyana.csv`, `country_data/Haiti.csv`, `country_data/Honduras.csv`, `country_data/India.csv`, `country_data/Indonesia.csv`, `country_data/Iraq.csv`, `country_data/Jamaica.csv`, `country_data/Jordan.csv`, `country_data/Kenya.csv`, `country_data/Kyrgyzstan.csv`, `country_data/Laos.csv`, `country_data/Lesotho.csv`, `country_data/Liberia.csv`, `country_data/Libya.csv`, `country_data/Madagascar.csv`, `country_data/Malawi.csv`, `country_data/Mali.csv`, `country_data/Mauritius.csv`, `country_data/Moldova.csv`, `country_data/Mongolia.csv`, `country_data/Mozambique.csv`, `country_data/Namibia.csv`, `country_data/Nepal.csv`, `country_data/Nicaragua.csv`, `country_data/Niger.csv`, `country_data/Nigeria.csv`, `country_data/Pakistan.csv`, `country_data/Panama.csv`, `country_data/Papua_New_Guinea.csv`, `country_data/Philippines.csv`, `country_data/Rwanda.csv`, `country_data/Sao_Tome_and_Principe.csv`, `country_data/Senegal.csv`, `country_data/Sierra_Leone.csv`, `country_data/Somalia.csv`, `country_data/South_Africa.csv`, `country_data/South_Sudan.csv`, `country_data/Swaziland.csv`, `country_data/Tajikistan.csv`, `country_data/Tanzania.csv`, `country_data/The_Gambia.csv`, `country_data/Timor_Leste.csv`, `country_data/Togo.csv`, `country_data/Uganda.csv`, `country_data/Venezuela.csv`, `country_data/Vietnam.csv`, `country_data/Zambia.csv`, `country_data/Zimbabwe.csv`, `country_data/_index.csv`, `country_lists.py`, `docs/file_inventory.md`, `ext_data/gho/HIV_0000000001.csv`, `ext_data/gho/HIV_0000000016.csv`, `ext_data/gho/HIV_0000000020.csv`, `ext_data/gho/HIV_ARTCOVERAGE.csv`, `ext_data/gho/MALARIA_EST_CASES.csv`, `ext_data/gho/MALARIA_EST_DEATHS.csv`, `ext_data/gho/MALARIA_EST_INCIDENCE.csv`, `ext_data/gho/MALARIA_ITN_USE.csv`, `ext_data/gm/ddf--datapoints--ihme_hiv_death--by--country--time.csv`, `ext_data/map/incidence_prevalence.csv`, `ext_data/map/irs.csv`, `ext_data/map/itn.csv`, `ext_data/map/pf_cases.csv`, `ext_data/map/pv_cases.csv`, `ext_data/map/treatment.csv`, `ext_data/reference/README.md`, `ext_data/reference/sg/ddf--datapoints--all_forms_of_tb_treatment_coverage_percent--by--geo--time.csv`, `ext_data/reference/sg/ddf--datapoints--annual_hiv_deaths_number_all_ages--by--geo--time.csv`, `ext_data/reference/sg/ddf--datapoints--hiv_deaths_in_children_1_59_months_total_deaths--by--geo--time.csv`, `ext_data/reference/sg/ddf--datapoints--malaria_number_of_cases_reported--by--geo--time.csv`, `ext_data/reference/sg/ddf--datapoints--malaria_number_of_deaths_reported--by--geo--time.csv`, `ext_data/reference/sg/ddf--datapoints--meningitis_deaths_in_children_1_59_months_total_deaths--by--geo--time.csv`, `ext_data/reference/sg/ddf--datapoints--newly_hiv_infected_number_all_ages--by--geo--time.csv`, `ext_data/reference/sg/ddf--datapoints--number_of_child_deaths--by--geo--time.csv`, `ext_data/reference/sg/ddf--datapoints--pertussis_deaths_in_children_1_59_months_total_deaths--by--geo--time.csv`, `ext_data/reference/wdi/ny_gdp_pcap_cd.csv`, `ext_data/reference/wdi/sh_dth_comm_zs.csv`, `ext_data/reference/wdi/sh_dth_imrt.csv`, `ext_data/reference/wdi/sh_dyn_nmrt.csv`, `ext_data/reference/wdi/sh_imm_hepb.csv`, `ext_data/reference/wdi/sh_uhc_sci_id.csv`, `ext_data/reference/wdi/sh_xpd_ghed_gd_zs.csv`, `ext_data/sg/ddf--datapoints--all_forms_of_tb_incidence_estimated--by--geo--time.csv`, `ext_data/sg/ddf--datapoints--all_forms_of_tb_number_of_deaths_estimated--by--geo--time.csv`, `ext_data/sg/ddf--datapoints--malaria_deaths_in_children_1_59_months_total_deaths--by--geo--time.csv`, `ext_data/sg/ddf--datapoints--measles_deaths_in_children_1_59_months_total_deaths--by--geo--time.csv`, `ext_data/sg/ddf--datapoints--people_living_with_hiv_number_all_ages--by--geo--time.csv`, `ext_data/sg/ddf--datapoints--pneumonia_deaths_in_children_1_59_months_total_deaths--by--geo--time.csv`, `ext_data/sg/ddf--datapoints--tb_hivplus_incidence_estimated--by--geo--time.csv`, `ext_data/sg/ddf--datapoints--tb_hivplus_number_of_deaths_estimated--by--geo--time.csv`, `ext_data/wb_country_entities.csv`, `ext_data/wdi/gc_dod_totl_gd_zs.csv`, `ext_data/wdi/gc_rev_xgrt_gd_zs.csv`, `ext_data/wdi/gc_xpn_intp_rv_zs.csv`, `ext_data/wdi/gc_xpn_totl_gd_zs.csv`, `ext_data/wdi/sh_dth_mort.csv`, `ext_data/wdi/sh_dyn_aids_zs.csv`, `ext_data/wdi/sh_dyn_mort.csv`, `ext_data/wdi/sh_hiv_0014.csv`, `ext_data/wdi/sh_hiv_artc_zs.csv`, `ext_data/wdi/sh_hiv_incd_tl.csv`, `ext_data/wdi/sh_hiv_pmtc_zs.csv`, `ext_data/wdi/sh_imm_idpt.csv`, `ext_data/wdi/sh_imm_meas.csv`, `ext_data/wdi/sh_mlr_incd_p3.csv`, `ext_data/wdi/sh_mlr_nets_zs.csv`, `ext_data/wdi/sh_mlr_tret_zs.csv`, `ext_data/wdi/sh_mmr_dths.csv`, `ext_data/wdi/sh_tbs_cure_zs.csv`, `ext_data/wdi/sh_tbs_dtec_zs.csv`, `ext_data/wdi/sh_tbs_incd.csv`, `ext_data/wdi/sh_uhc_sci.csv`, `ext_data/wdi/sh_xpd_ghed_ge_zs.csv`, `ext_data/wdi/sp_dyn_cbrt_in.csv`, `ext_data/wdi/sp_dyn_cdrt_in.csv`, `ext_data/wdi/sp_pop_0014_to.csv`, `ext_data/wdi/sp_pop_1564_to.csv`, `ext_data/wdi/sp_pop_totl.csv`, `ext_data/who_regions.csv`, `hiv_transmission_inputs.py`, `macro_data/AGO.csv`, `macro_data/AZE.csv`, `macro_data/BDI.csv`, `macro_data/BEN.csv`, `macro_data/BFA.csv`, `macro_data/BGD.csv`, `macro_data/BLZ.csv`, `macro_data/BOL.csv`, `macro_data/BWA.csv`, `macro_data/CAF.csv`, `macro_data/CIV.csv`, `macro_data/CMR.csv`, `macro_data/COD.csv`, `macro_data/DJI.csv`, `macro_data/DOM.csv`, `macro_data/EGY.csv`, `macro_data/ETH.csv`, `macro_data/FJI.csv`, `macro_data/GHA.csv`, `macro_data/GIN.csv`, `macro_data/GMB.csv`, `macro_data/GTM.csv`, `macro_data/GUY.csv`, `macro_data/HND.csv`, `macro_data/HTI.csv`, `macro_data/IDN.csv`, `macro_data/IND.csv`, `macro_data/IRQ.csv`, `macro_data/JAM.csv`, `macro_data/JOR.csv`, `macro_data/KEN.csv`, `macro_data/KGZ.csv`, `macro_data/KHM.csv`, `macro_data/LAO.csv`, `macro_data/LBR.csv`, `macro_data/LBY.csv`, `macro_data/LSO.csv`, `macro_data/MDA.csv`, `macro_data/MDG.csv`, `macro_data/MLI.csv`, `macro_data/MNG.csv`, `macro_data/MOZ.csv`, `macro_data/MUS.csv`, `macro_data/MWI.csv`, `macro_data/NAM.csv`, `macro_data/NER.csv`, `macro_data/NGA.csv`, `macro_data/NIC.csv`, `macro_data/NPL.csv`, `macro_data/PAK.csv`, `macro_data/PAN.csv`, `macro_data/PHL.csv`, `macro_data/PNG.csv`, `macro_data/RWA.csv`, `macro_data/SEN.csv`, `macro_data/SLE.csv`, `macro_data/SLV.csv`, `macro_data/SOM.csv`, `macro_data/SSD.csv`, `macro_data/STP.csv`, `macro_data/SWZ.csv`, `macro_data/TGO.csv`, `macro_data/TJK.csv`, `macro_data/TLS.csv`, `macro_data/TZA.csv`, `macro_data/UGA.csv`, `macro_data/VEN.csv`, `macro_data/VNM.csv`, `macro_data/ZAF.csv`, `macro_data/ZMB.csv`, `macro_data/ZWE.csv`, `macro_data/weo_fiscal/weo_balances.csv`, `malaria_inputs.py`, `model_data/country_profile.csv`, `model_data/dah_lines.csv`, `model_data/ihme_trend.csv`, `model_data/mou_signed.csv`, `model_data/panel.csv`, `model_data/regressions.json`, `requirements-dev.txt`, `requirements.txt`, `revenue_data/AGO.csv`, `revenue_data/AZE.csv`, `revenue_data/BDI.csv`, `revenue_data/BEN.csv`, `revenue_data/BFA.csv`, `revenue_data/BGD.csv`, `revenue_data/BLZ.csv`, `revenue_data/BOL.csv`, `revenue_data/BWA.csv`, `revenue_data/CAF.csv`, `revenue_data/CIV.csv`, `revenue_data/CMR.csv`, `revenue_data/COD.csv`, `revenue_data/DJI.csv`, `revenue_data/DOM.csv`, `revenue_data/EGY.csv`, `revenue_data/ETH.csv`, `revenue_data/FJI.csv`, `revenue_data/GHA.csv`, `revenue_data/GIN.csv`, `revenue_data/GMB.csv`, `revenue_data/GTM.csv`, `revenue_data/GUY.csv`, `revenue_data/HND.csv`, `revenue_data/HTI.csv`, `revenue_data/IDN.csv`, `revenue_data/IND.csv`, `revenue_data/IRQ.csv`, `revenue_data/JAM.csv`, `revenue_data/JOR.csv`, `revenue_data/KEN.csv`, `revenue_data/KGZ.csv`, `revenue_data/KHM.csv`, `revenue_data/LAO.csv`, `revenue_data/LBR.csv`, `revenue_data/LBY.csv`, `revenue_data/LSO.csv`, `revenue_data/MDA.csv`, `revenue_data/MDG.csv`, `revenue_data/MLI.csv`, `revenue_data/MNG.csv`, `revenue_data/MOZ.csv`, `revenue_data/MUS.csv`, `revenue_data/MWI.csv`, `revenue_data/NAM.csv`, `revenue_data/NER.csv`, `revenue_data/NGA.csv`, `revenue_data/NIC.csv`, `revenue_data/NPL.csv`, `revenue_data/PAK.csv`, `revenue_data/PAN.csv`, `revenue_data/PHL.csv`, `revenue_data/PNG.csv`, `revenue_data/RWA.csv`, `revenue_data/SEN.csv`, `revenue_data/SLE.csv`, `revenue_data/SLV.csv`, `revenue_data/SOM.csv`, `revenue_data/SSD.csv`, `revenue_data/STP.csv`, `revenue_data/SWZ.csv`, `revenue_data/TGO.csv`, `revenue_data/TJK.csv`, `revenue_data/TLS.csv`, `revenue_data/TZA.csv`, `revenue_data/UGA.csv`, `revenue_data/VEN.csv`, `revenue_data/VNM.csv`, `revenue_data/ZAF.csv`, `revenue_data/ZMB.csv`, `revenue_data/ZWE.csv`, `spending_data/AGO.csv`, `spending_data/AZE.csv`, `spending_data/BDI.csv`, `spending_data/BEN.csv`, `spending_data/BFA.csv`, `spending_data/BGD.csv`, `spending_data/BLZ.csv`, `spending_data/BOL.csv`, `spending_data/BWA.csv`, `spending_data/CAF.csv`, `spending_data/CIV.csv`, `spending_data/CMR.csv`, `spending_data/COD.csv`, `spending_data/DJI.csv`, `spending_data/DOM.csv`, `spending_data/EGY.csv`, `spending_data/ETH.csv`, `spending_data/FJI.csv`, `spending_data/GHA.csv`, `spending_data/GIN.csv`, `spending_data/GMB.csv`, `spending_data/GTM.csv`, `spending_data/GUY.csv`, `spending_data/HND.csv`, `spending_data/HTI.csv`, `spending_data/IDN.csv`, `spending_data/IND.csv`, `spending_data/IRQ.csv`, `spending_data/JAM.csv`, `spending_data/JOR.csv`, `spending_data/KEN.csv`, `spending_data/KGZ.csv`, `spending_data/KHM.csv`, `spending_data/LAO.csv`, `spending_data/LBR.csv`, `spending_data/LBY.csv`, `spending_data/LSO.csv`, `spending_data/MDA.csv`, `spending_data/MDG.csv`, `spending_data/MLI.csv`, `spending_data/MNG.csv`, `spending_data/MOZ.csv`, `spending_data/MUS.csv`, `spending_data/MWI.csv`, `spending_data/NAM.csv`, `spending_data/NER.csv`, `spending_data/NGA.csv`, `spending_data/NIC.csv`, `spending_data/NPL.csv`, `spending_data/PAK.csv`, `spending_data/PAN.csv`, `spending_data/PHL.csv`, `spending_data/PNG.csv`, `spending_data/RWA.csv`, `spending_data/SEN.csv`, `spending_data/SLE.csv`, `spending_data/SLV.csv`, `spending_data/SOM.csv`, `spending_data/SSD.csv`, `spending_data/STP.csv`, `spending_data/SWZ.csv`, `spending_data/TGO.csv`, `spending_data/TJK.csv`, `spending_data/TLS.csv`, `spending_data/TZA.csv`, `spending_data/UGA.csv`, `spending_data/VEN.csv`, `spending_data/VNM.csv`, `spending_data/ZAF.csv`, `spending_data/ZMB.csv`, `spending_data/ZWE.csv`, `spending_data/_index.csv`, `tests/make_baseline.py`, `tests/test_budget_section.py`, `tests/test_i07.py`, `tests/test_minor.py`, `tests/test_tb.py`, `unit_cost_reference.csv`, `who_inputs.py`

### main only (173)

- `.devcontainer/devcontainer 2.json`
- `.streamlit/config 2.toml`
- `add_constant_dollars 2.py`
- `announcement_model/.gitignore`
- `announcement_model/oda_history.csv`
- `announcement_model/project_cuts.py`
- `audit/AUDIT 2.md`
- `audit/I-01 2.md`
- `audit/I-02_I-03_I-08 2.md`
- `audit/I-05 2.md`
- `audit/I-06_I-11_malaria 2.md`
- `audit/I-07 2.md`
- `audit/I-09_I-27_I-04 2.md`
- `audit/I-10 2.md`
- `audit/I-13_I-14_I-15_I-16 2.md`
- `audit/I-26_I-17 2.md`
- `audit/METHOD 2.md`
- `audit/after_batch2 2.csv`
- `audit/after_do_now 2.csv`
- `audit/analysis 2.json`
- `audit/archive/README 2.md`
- `audit/archive/analysis 2.py`
- `audit/batch2_cohort 2.py`
- `audit/batch2_projection 2.py`
- `audit/batch34_art_costs 2.py`
- `audit/batch34_donor_share 2.py`
- `audit/batch34_gf_shares 2.py`
- `audit/batch34_headline 2.py`
- `audit/batch34_tb_costs 2.py`
- `audit/batch4b_art_check 2.py`
- `audit/batch4b_malaria_decomp 2.py`
- `audit/before_batch2 2.csv`
- `audit/before_batch34 2.csv`
- `audit/before_batch4b 2.csv`
- `audit/before_do_now 2.csv`
- `audit/checks 2.py`
- `audit/checks_results 2.csv`
- `audit/checks_summary 2.csv`
- `audit/checks_summary 2.md`
- `audit/compare_recompute 2.py`
- `audit/cosmetic_fixes 2.md`
- `audit/hiv_diff 2.py`
- `audit/i07_diff 2.py`
- `audit/inventory 2.csv`
- `audit/logic_review/batch2_before_after 2.py`
- `audit/logic_review/batch34_gf_shares 2.csv`
- `audit/logic_review/batch34_reconcile 2.py`
- `audit/logic_review/batch4b_art_check 2.csv`
- `audit/logic_review/batch4b_before_after 2.md`
- `audit/logic_review/batch4b_reconcile 2.csv`
- `audit/logic_review/build_inputs 2.py`
- `audit/logic_review/dashboard 2.md`
- `audit/logic_review/do_now_before_after 2.py`
- `audit/logic_review/inputs 2.csv`
- `audit/logic_review/redteam 2.md`
- `audit/logic_review/reproduction/compare 2.csv`
- `audit/logic_review/sensitivity 2.csv`
- `audit/logic_review/sensitivity 2.py`
- `audit/minor_diff_counts 2.csv`
- `audit/recompute 2.py`
- `audit/recompute_notes 2.md`
- `audit/snapshot_numbers 2.py`
- `batch34_inputs 2.py`
- `budget_section 2.py`
- `country_lists 2.py`
- `docs/file_inventory 2.md`
- `ext_data/gho/HIV_0000000001 2.csv`
- `ext_data/gho/HIV_0000000016 2.csv`
- `ext_data/gho/HIV_0000000020 2.csv`
- `ext_data/gho/HIV_ARTCOVERAGE 2.csv`
- `ext_data/gho/MALARIA_EST_CASES 2.csv`
- `ext_data/gho/MALARIA_EST_DEATHS 2.csv`
- `ext_data/gho/MALARIA_EST_INCIDENCE 2.csv`
- `ext_data/gm/ddf--datapoints--ihme_hiv_death--by--country--time 2.csv`
- `ext_data/map/incidence_prevalence 2.csv`
- `ext_data/map/irs 2.csv`
- `ext_data/map/itn 2.csv`
- `ext_data/map/pf_cases 2.csv`
- `ext_data/map/pv_cases 2.csv`
- `ext_data/map/treatment 2.csv`
- `ext_data/sg/ddf--datapoints--all_forms_of_tb_incidence_estimated--by--geo--time 2.csv`
- `ext_data/sg/ddf--datapoints--malaria_deaths_in_children_1_59_months_total_deaths--by--geo--time 2.csv`
- `ext_data/sg/ddf--datapoints--measles_deaths_in_children_1_59_months_total_deaths--by--geo--time 2.csv`
- `ext_data/sg/ddf--datapoints--people_living_with_hiv_number_all_ages--by--geo--time 2.csv`
- `ext_data/sg/ddf--datapoints--pneumonia_deaths_in_children_1_59_months_total_deaths--by--geo--time 2.csv`
- `ext_data/wdi/gc_dod_totl_gd_zs 2.csv`
- `ext_data/wdi/gc_rev_xgrt_gd_zs 2.csv`
- `ext_data/wdi/gc_xpn_intp_rv_zs 2.csv`
- `ext_data/wdi/gc_xpn_totl_gd_zs 2.csv`
- `ext_data/wdi/sh_dth_mort 2.csv`
- `ext_data/wdi/sh_dyn_aids_zs 2.csv`
- `ext_data/wdi/sh_dyn_mort 2.csv`
- `ext_data/wdi/sh_hiv_0014 2.csv`
- `ext_data/wdi/sh_hiv_artc_zs 2.csv`
- `ext_data/wdi/sh_hiv_incd_tl 2.csv`
- `ext_data/wdi/sh_hiv_pmtc_zs 2.csv`
- `ext_data/wdi/sh_imm_idpt 2.csv`
- `ext_data/wdi/sh_imm_meas 2.csv`
- `ext_data/wdi/sh_mlr_incd_p3 2.csv`
- `ext_data/wdi/sh_mlr_nets_zs 2.csv`
- `ext_data/wdi/sh_mlr_tret_zs 2.csv`
- `ext_data/wdi/sh_mmr_dths 2.csv`
- `ext_data/wdi/sh_tbs_cure_zs 2.csv`
- `ext_data/wdi/sh_tbs_dtec_zs 2.csv`
- `ext_data/wdi/sh_tbs_incd 2.csv`
- `ext_data/wdi/sh_uhc_sci 2.csv`
- `ext_data/wdi/sh_xpd_ghed_ge_zs 2.csv`
- `ext_data/wdi/sp_dyn_cbrt_in 2.csv`
- `ext_data/wdi/sp_dyn_cdrt_in 2.csv`
- `ext_data/wdi/sp_pop_0014_to 2.csv`
- `ext_data/wdi/sp_pop_1564_to 2.csv`
- `ext_data/wdi/sp_pop_totl 2.csv`
- `fiscal_inputs 2.py`
- `health_model 2.py`
- `hiv_transmission_inputs 2.py`
- `macro_data/weo_fiscal/weo_balances 2.csv`
- `malaria_inputs 2.py`
- `model_data/all_countries_America_First_MOUs 2.csv`
- `model_data/all_countries_America_First_MOUs_draws 2.csv`
- `model_data/all_countries_Announced_donor_cuts.csv`
- `model_data/all_countries_Announced_donor_cuts_draws.csv`
- `model_data/all_countries_Combined_retreat 2.csv`
- `model_data/all_countries_Combined_retreat_draws 2.csv`
- `model_data/all_countries_Full_US_exit 2.csv`
- `model_data/all_countries_Full_US_exit_draws 2.csv`
- `model_data/all_countries_Global_Fund_Gavi_shortfalls 2.csv`
- `model_data/all_countries_Global_Fund_Gavi_shortfalls_draws 2.csv`
- `model_data/all_countries_IHME_2025_preliminary_estimates 2.csv`
- `model_data/all_countries_IHME_2025_preliminary_estimates_draws 2.csv`
- `model_data/all_countries_OECD_reported_2025_aid_cuts 2.csv`
- `model_data/all_countries_OECD_reported_2025_aid_cuts_draws 2.csv`
- `model_data/announcement_areas.csv`
- `model_data/announcement_cuts.csv`
- `model_data/country_profile 2.csv`
- `model_data/dah_lines 2.csv`
- `model_data/ihme_trend 2.csv`
- `model_data/mou_signed 2.csv`
- `model_data/panel 2.csv`
- `model_data/regressions 2.json`
- `model_params 2.csv`
- `model_section 2.py`
- `model_sourced_update/README_MODEL.md`
- `model_sourced_update/ext_data/wb_country_entities.csv`
- `model_sourced_update/health_model.py`
- `model_sourced_update/model_data/country_inputs.csv`
- `model_sourced_update/model_params.csv`
- `model_sourced_update/model_section.py`
- `model_sourced_update/prepare_model.py`
- `model_sourced_update/unit_cost_reference.csv`
- `paths_ui 2.py`
- `prepare_model 2.py`
- `requirements-dev 2.txt`
- `scenarios 2.py`
- `tests/baseline_sudden 2.json`
- `tests/conftest.py`
- `tests/make_baseline 2.py`
- `tests/test_announcement.py`
- `tests/test_budget_section 2.py`
- `tests/test_fiscal 2.py`
- `tests/test_hiv 2.py`
- `tests/test_i07 2.py`
- `tests/test_malaria 2.py`
- `tests/test_minor 2.py`
- `tests/test_mou 2.py`
- `tests/test_paths 2.py`
- `tests/test_tb 2.py`
- `theme 2.py`
- `unit_cost_reference 2.csv`
- `views/1_Dashboard 2.py`
- `views/2_All_Countries 2.py`
- `views/3_Validation 2.py`
- `views/4_Methods 2.py`
- `who_inputs 2.py`

### tomato only (157)

- `audit/FINDINGS_WHO.md`
- `audit/after_batch56.csv`
- `audit/art_ratio/art_spend_per_person.csv`
- `audit/art_ratio/art_spend_per_person.py`
- `audit/batch56_art_cost.py`
- `audit/batch56_donor_share.py`
- `audit/batch56_malaria_cap.py`
- `audit/batch56_vaccines.py`
- `audit/batch56_validation.py`
- `audit/batch7_flags.py`
- `audit/before_batch56.csv`
- `audit/channels/RESULTS_channels.md`
- `audit/channels/channels.csv`
- `audit/channels/run_channels.py`
- `audit/concentration/RESULTS_concentration.md`
- `audit/concentration/loss_by_line.csv`
- `audit/concentration/run_concentration.py`
- `audit/concentration/thresholds.csv`
- `audit/coverage_realloc/RESULTS_coverage_realloc.md`
- `audit/coverage_realloc/marginals.csv`
- `audit/coverage_realloc/optima.csv`
- `audit/coverage_realloc/run_coverage_realloc.py`
- `audit/coverage_realloc/scenarios.csv`
- `audit/crossroads/CROSSROADS_REVIEW.md`
- `audit/crossroads/double_counting_checks.py`
- `audit/crossroads/extract_appendix4.py`
- `audit/crossroads/fiscal_crosscheck.py`
- `audit/crossroads/part2_fiscal_comparison.csv`
- `audit/crossroads/part3_preset_implied_falls.csv`
- `audit/crossroads/part3_wb_a23_style_all_countries.csv`
- `audit/crossroads/part4_bucket_money.csv`
- `audit/crossroads/part4_care_line_contribution.csv`
- `audit/crossroads/part4_replacement_bounds.csv`
- `audit/crossroads/part4_tb_hiv_overlap.csv`
- `audit/crossroads/part4_units_vs_pools.csv`
- `audit/crossroads/part5_uhc_gap.csv`
- `audit/crossroads/scenario_crosscheck.py`
- `audit/crossroads/uhc_gap.py`
- `audit/crossroads/wb_grph_appendix4.csv`
- `audit/fiscal_history/RESULTS_fiscal_history.md`
- `audit/fiscal_history/RESULTS_rerun_check.md`
- `audit/fiscal_history/episodes.csv`
- `audit/fiscal_history/jackknife_theta.csv`
- `audit/fiscal_history/rerun_check.csv`
- `audit/fiscal_history/rerun_regression_check.py`
- `audit/fiscal_history/run_fiscal_history.py`
- `audit/fiscal_history/subsample_theta.csv`
- `audit/gov_response/RESULTS_gov_response.md`
- `audit/gov_response/gov_response.csv`
- `audit/gov_response/run_gov_response.py`
- `audit/health_share/build_health_share_xlsx.py`
- `audit/health_share/health_share_gov_spending.xlsx`
- `audit/logic_review/MODEL_CHANGELOG.md`
- `audit/logic_review/batch56_art_cost.csv`
- `audit/logic_review/batch56_before_after.md`
- `audit/logic_review/batch56_before_after.py`
- `audit/logic_review/batch56_donor_share.csv`
- `audit/logic_review/batch56_evidence.md`
- `audit/logic_review/batch56_malaria_cap.csv`
- `audit/logic_review/batch56_vaccine_check.py`
- `audit/logic_review/batch56_vaccine_country.csv`
- `audit/logic_review/batch56_vaccine_timing.csv`
- `audit/logic_review/batch56_vaccines.csv`
- `audit/logic_review/batch7_evidence.md`
- `audit/logic_review/batch7_flags.csv`
- `audit/logic_review/validation.md`
- `audit/logic_review/validation_tables.csv`
- `audit/other_donors/RESULTS_other_donors.md`
- `audit/other_donors/other_donors.csv`
- `audit/other_donors/run_other_donors.py`
- `audit/reallocation/RESULTS_2027.md`
- `audit/reallocation/RESULTS_2027_opt.md`
- `audit/reallocation/RESULTS_2027_opt.pdf`
- `audit/reallocation/RESULTS_2027_v2.md`
- `audit/reallocation/RESULTS_2027_v2.pdf`
- `audit/reallocation/RESULTS_dollar_2027_v2.md`
- `audit/reallocation/RESULTS_dollar_2027_v2.pdf`
- `audit/reallocation/RESULTS_dollar_hiv_2027_v2.md`
- `audit/reallocation/RESULTS_dollar_hiv_2027_v2.pdf`
- `audit/reallocation/RESULTS_optimal_2027.md`
- `audit/reallocation/RESULTS_optimal_2027.pdf`
- `audit/reallocation/allocations_2027.csv`
- `audit/reallocation/allocations_2027_opt.csv`
- `audit/reallocation/allocations_2027_opt_mou.csv`
- `audit/reallocation/allocations_2027_v2.csv`
- `audit/reallocation/dollar_2027_v2.csv`
- `audit/reallocation/dollar_hiv_2027_v2.csv`
- `audit/reallocation/marginal_2027.csv`
- `audit/reallocation/marginal_2027_opt.csv`
- `audit/reallocation/marginal_2027_v2.csv`
- `audit/reallocation/notes_2027.md`
- `audit/reallocation/notes_2027_opt.md`
- `audit/reallocation/notes_2027_v2.md`
- `audit/reallocation/optimal_2027.csv`
- `audit/reallocation/optimal_curves_2027.csv`
- `audit/reallocation/results_2027.csv`
- `audit/reallocation/results_2027_opt.csv`
- `audit/reallocation/results_2027_v2.csv`
- `audit/reallocation/run_dollar_hiv_2027.py`
- `audit/reallocation/run_dollar_realloc_2027.py`
- `audit/reallocation/run_optimal_realloc_2027.py`
- `audit/reallocation/run_reallocation_2027.py`
- `audit/slide_numbers.md`
- `audit/timing/RESULTS_timing.md`
- `audit/timing/run_timing.py`
- `audit/timing/timing.csv`
- `build_sections.py`
- `docs/DATA_SOURCES.md`
- `docs/EXPLAINER.md`
- `docs/figures/fiscal_replacement.png`
- `docs/figures/fiscal_replacement.svg`
- `immunization_inputs.py`
- `slides/backfill_slide.pptx`
- `slides/build_backfill_slide.py`
- `slides/build_dashboard_segment.py`
- `slides/build_data_model_slide.py`
- `slides/build_donor_change_chart.py`
- `slides/build_donor_change_chart_mpl.py`
- `slides/build_live_demo_slide.py`
- `slides/build_steps_controls_slide.py`
- `slides/dashboard_segment.pptx`
- `slides/data_and_model_slide.pptx`
- `slides/deck_data.json`
- `slides/deck_data.py`
- `slides/donor_change_chart.pptx`
- `slides/live_demo_slide.pptx`
- `slides/render/backfill_slide.pdf`
- `slides/render/dashboard_segment.pdf`
- `slides/render/data_and_model_slide.pdf`
- `slides/render/donor_change_chart.pdf`
- `slides/render/donor_change_chart.png`
- `slides/render/donor_change_chart_cm.pdf`
- `slides/render/donor_change_chart_cm.png`
- `slides/render/live_demo_slide.pdf`
- `slides/render/png/live_demo_slide.png`
- `slides/render/png/p01.png`
- `slides/render/png/p02.png`
- `slides/render/png/p03.png`
- `slides/render/png/p04.png`
- `slides/render/png/p05.png`
- `slides/render/png/p06.png`
- `slides/render/png/p07.png`
- `slides/render/png/p08.png`
- `slides/render/png/p09.png`
- `slides/render/png/p10.png`
- `slides/render/png/p11.png`
- `slides/render/png/p12.png`
- `slides/render/png/p13.png`
- `slides/render/png/p14.png`
- `slides/render/png/p15.png`
- `slides/render/png/p16.png`
- `slides/render/png/p17.png`
- `slides/render/steps_and_controls_slide.pdf`
- `slides/render/team.pdf`
- `slides/render/team_capstone_deck.pptx`
- `slides/steps_and_controls_slide.pptx`
- `unaids_inputs.py`

## 2. Dashboard UI, branch main


Read-only inventory built from source. Conventions:

- **Name as shown** is the on-screen form. Where the code passes text through `model_section.title_case` (directly, via `pill_row`, via `format_func=title_case`, or via `chart()` -> `tc_fig`, which title-cases every Plotly title, subtitle, trace name, axis title, colour-bar title and annotation), the title-cased form is given. Widget labels, `st.subheader`, `th.section_header` and `th.pills_html` labels are NOT title-cased; they are given exactly as written. `{country}` / `{yr}` etc. are runtime values.
- **file:line** = the line of the Streamlit call (or the function `def` for whole components). `ms` = model_section.py, `pu` = paths_ui.py, `th` = theme.py, `D` = views/1_Dashboard.py, `AC` = views/2_All_Countries.py, `V` = views/3_Validation.py, `M` = views/4_Methods.py, `scn` = scenarios.py.
- **Kind** values: section (th.section_header badge headings) · heading (st.title / st.subheader / kicker / bold markdown heading) · chart · table · card/metric (pills, big numbers, header facts) · control · tooltip-bearing control (widget with `help=`) · preset · caption/text block · download · expander (incl. st.popover) · tab.
- Default scenario state on `main`: Donor Scenario offers only **Announced Donor Cuts** (default) and **Custom** (`scn.UI_PRESETS`, scenarios.py:59). Everything tied to America First MOUs or Global Fund & Gavi Shortfalls in the scenario bar is therefore unreachable from the UI.

### 1. App shell (app.py, theme.py)

| ID | Page | Kind | Name as shown | Rendering function | file:line | Shown? |
|---|---|---|---|---|---|---|
| MAIN-UI-001 | App shell | section | Browser tab title "Health Financing" (icon monitor_heart, wide layout, sidebar collapsed) | th.setup | th:514-518 (called app.py:11) | always |
| MAIN-UI-002 | App shell | control | Top navigation bar: "Dashboard" · "All Countries" · "Methods" (st.navigation, position="top") | app.py module | app.py:20-22; page list th.PAGES th:509-511 | always |
| MAIN-UI-003 | App shell | section | Page "Validation & Benchmarks" (views/3_Validation.py) | — | th:509-511 omit it; app.py:5 docstring says "kept but not in the navigation" | not shown: not in th.PAGES, so st.navigation never registers it |
| MAIN-UI-004 | App shell | caption/text block | Session persistence of widget keys with prefixes m_, mb_, c1_, c2_, c3b_, c4_year_ (except m_params, m_custom_tbl, mb_custom_tbl). Note: bud_share_*/bud_tax_* (budget sliders) are NOT in the list | app.py module | app.py:15-19 | always (not visible) |

### 2. Dashboard (views/1_Dashboard.py, default page)

Order follows the page top to bottom.

| ID | Page | Kind | Name as shown | Rendering function | file:line | Shown? |
|---|---|---|---|---|---|---|
| MAIN-UI-005 | Dashboard | caption/text block | st.error "No `country_data/` folder found. Run `python prepare_data.py <path to the IHME DAH CSV>` first." (+ st.stop) | page module | D:246-247 | conditional: country_data/ missing |
| MAIN-UI-006 | Dashboard | caption/text block | st.warning "These data folders are missing (or empty) next to this script, so part of the page won't show: ..." | page module | D:259 | conditional: any of spending_data/, cofog_all/, macro_data/, revenue_data/ missing |
| MAIN-UI-007 | Dashboard | section | Sticky country header (container key "hdr", 3 columns) | page module | D:268-269 | always |
| MAIN-UI-008 | Dashboard | heading | Country name (class ed-country) | page module | D:304 | always |
| MAIN-UI-009 | Dashboard | card/metric | Header fact "Region" | page module | D:298, 301-305 | conditional: profile has region |
| MAIN-UI-010 | Dashboard | card/metric | Header fact "Income" (Low Income / Lower-Middle Income / Upper-Middle Income / High Income) | page module | D:298, 145-146 | conditional: profile has income_group |
| MAIN-UI-011 | Dashboard | card/metric | Header fact "GDP, {yr}" | page module | D:299 | conditional: macro data has gdp_usd_bn |
| MAIN-UI-012 | Dashboard | card/metric | Header fact "Population, {yr}" | page module | D:300 | conditional: macro data has population_m (note: Methods "Country Header" table also lists "US MOU", which is NOT rendered here) |
| MAIN-UI-013 | Dashboard | chart | Header locator map (Choropleth of the selected country, no title, static) key "hdr_map" | page module | D:307-315 | always |
| MAIN-UI-014 | Dashboard | control | "Country" selectbox, key `country_sel` (shared via `sel_iso3`); options = 71 ALLOWED_COUNTRIES iso3 shown as names; default Kenya | th.shared_select | D:272-274 -> th:528 | always |
| MAIN-UI-015 | Dashboard | heading | Story lede headline (class ed-headline). Announced: "If donors cut aid as announced, {country} would lose {$} of {health aid / HIV, TB, malaria and vaccine aid} in 2026, rising to {$} by 2030" (or "...would lose almost no ..."). Custom: "{scenario phrase}, {country} would lose {$} a year of HIV, TB, malaria and vaccine aid, and about {N} people a year would lose a service" (or "...would lose almost no aid..."). No aid: "{country} receives no recorded HIV, TB, malaria or vaccine aid" | ms.story_lede / ms._money_lede | D:318-321; ms:907-952, ms:999-1021 | always (text varies) |
| MAIN-UI-016 | Dashboard | caption/text block | Story lede dek (class ed-dek): Custom: "The government could replace ..." or "In past aid declines (2001-2023), governments on average did not increase their own health spending to compensate."; Announced: "{A bigger health budget / higher tax revenue} would add {$} a year for health by 2030, ..." (only when budget sliders add money); "None of the announced cuts falls on this aid here."; no-aid dek | ms.story_lede / ms._money_lede | ms:915, 925, 930-934, 1007, 1017-1019 | conditional (Announced dek empty unless budget sliders moved) |
| MAIN-UI-017 | Dashboard | card/metric | Big number "Health Aid Lost Each Year" (note "{x}% of aid for these four diseases") | ms.story_lede | ms:944-945, 949-952 | conditional: preset = Custom and country modelled (Announced uses _money_lede, no big numbers) |
| MAIN-UI-018 | Dashboard | card/metric | Big number "Treatment Lost Each Year" (tooltip TREATMENT_TIP ms:830; note top-2 parts e.g. "452K people who stop ART* · ..." + "*full-cost equivalents of the lost money") | ms.story_lede | ms:946 | conditional: preset = Custom and country modelled |
| MAIN-UI-019 | Dashboard | card/metric | Big number "Prevention Lost Each Year" (tooltip PREVENTION_TIP ms:833) | ms.story_lede | ms:947 | conditional: preset = Custom and country modelled |
| MAIN-UI-020 | Dashboard | heading | Kicker "Aid lost each year in {country}" | ms.known_vs_predicted_chart | ms:387 | conditional: preset = Announced Donor Cuts, country in model lines, announced loss > 0 |
| MAIN-UI-021 | Dashboard | chart | Known vs predicted aid lost 2026-2030 (stacked bars, no title). Traces "Known (Published Cuts)", "Predicted MOU Cut (No MOU)" (only if > 0), "Predicted (Modelled Estimate)"; y-axis "Aid Lost" ($...M); totals as text | ms.known_vs_predicted_chart | ms:382-405; called D:322-323 | conditional: same as kicker above |
| MAIN-UI-022 | Dashboard | heading | Kicker "Change the Scenario" (anchor id change-scenario), container key "model_controls" | ms._controls | ms:537-539 | always |
| MAIN-UI-023 | Dashboard | tooltip-bearing control | "Donor Scenario" selectbox, key `m_preset` (shared via `sel_preset`); options "Announced Donor Cuts", "Custom"; help = full scn.PRESETS text of the current preset | ms.donor_scenario_select -> th.shared_select | ms:543 -> ms:508 -> th:528 | always |
| MAIN-UI-024 | Dashboard | caption/text block | MOU fallback notice ("America First MOUs: MOU signed; no funding data available." / "{country}: no MOU funding data; showing US Bilateral Exit + Multilateral Withdrawals.") | ms._controls | ms:544-545 (from ms:490-500, 506) | not shown in practice: only set when America First MOUs is selected, which is not offered |
| MAIN-UI-025 | Dashboard | tooltip-bearing control | "How Funding Changes" selectbox, key `m_path_shape`; options Sudden (Default), Linear Phase-Out, Front-Loaded, Back-Loaded, S-Curve, Custom; help "How the scenario's cut is phased in over 2026-2030. ..." | pu.path_selector | pu:95 (called ms:550) | conditional: preset not in (America First MOUs, Announced) -> only when Custom |
| MAIN-UI-026 | Dashboard | caption/text block | MOU schedule caption (scn.mou_schedule_text) | ms._controls | ms:553 | not shown: America First MOUs not offered |
| MAIN-UI-027 | Dashboard | tooltip-bearing control | "Gavi Funding Cut (%)" slider 0-50, key `m_gavi_cut`, help SHORTFALL_SLIDERS tip, plus grey reference marks "~15%: fall vs 2021-23 spending (our estimate)" / "24%: gap vs Gavi's US$11.9B target" | ms._shortfall_sliders | ms:324-326 (data ms:301-317) | not shown: Global Fund & Gavi Shortfalls not in UI_PRESETS |
| MAIN-UI-028 | Dashboard | tooltip-bearing control | "Global Fund Funding Cut (%)" slider 0-50, key `m_gf_cut`, plus marks "15%: allocation cut in MOU countries (KFF, Jun 2026)", "~20%: pledges vs previous replenishment", "~24%: median cut in allocation letters (Aidspan)", "30%: gap vs US$18B target" | ms._shortfall_sliders | ms:324-326 | not shown: Shortfalls not in UI_PRESETS |
| MAIN-UI-029 | Dashboard | expander | "Cuts by Donor and Channel" (expanded=True) | ms._preset_options | ms:335 | conditional: preset = Custom |
| MAIN-UI-030 | Dashboard | control | Data editor key `m_custom_tbl`; columns "Donor" (disabled) · "Bilateral & NGO Cut %" · "Via Multilaterals Cut %" (NumberColumn -50..100 step 5); 14 rows = hm.SOURCE_GROUPS (United States, United Kingdom, Germany, France, Japan, Canada, Netherlands, Nordics, Other DAC governments, Gates Foundation, Other private, Development-bank lending, Non-DAC governments, Other / unallocable) | ms._preset_options | ms:336-343 | conditional: preset = Custom |
| MAIN-UI-031 | Dashboard | tooltip-bearing control | "Global Fund Channel Cut (%)" slider 0-100 step 5, key `m_ch_Global Fund`, help "Hits every donor's money through this channel (e.g. a replenishment shortfall)." | ms._preset_options | ms:344-347 | conditional: preset = Custom |
| MAIN-UI-032 | Dashboard | tooltip-bearing control | "Gavi Channel Cut (%)" slider, key `m_ch_Gavi` | ms._preset_options | ms:344-347 | conditional: preset = Custom |
| MAIN-UI-033 | Dashboard | tooltip-bearing control | "WHO Channel Cut (%)" slider, key `m_ch_WHO` | ms._preset_options | ms:344-347 | conditional: preset = Custom |
| MAIN-UI-034 | Dashboard | tooltip-bearing control | "UNICEF Channel Cut (%)" slider, key `m_ch_UNICEF` | ms._preset_options | ms:344-347 | conditional: preset = Custom |
| MAIN-UI-035 | Dashboard | tooltip-bearing control | "Government Response" selectbox, key `m_mode`; options "No Government Replacement", "Replace a Set Share", "Gradual Budget Increase" ("As Much as Fiscal Space Allows" excluded here); help "How much of the lost aid the government replaces from its own budget. Across N countries, ... governments did not replace falling aid (...)" | ms._controls | ms:565-569 | always |
| MAIN-UI-036 | Dashboard | control | "Share of Lost Aid Replaced (%)" slider 0-100 default 25 step 5, key `m_theta` | ms._controls | ms:572 | conditional: Government Response = Replace a Set Share |
| MAIN-UI-037 | Dashboard | control | "Budget Increase Shape" selectbox, key `m_gov_shape`; options Steady, Fast Start, Slow Start, Custom | pu.gradual_controls | pu:134-135 (called ms:577) | conditional: Gradual Budget Increase and government spending known |
| MAIN-UI-038 | Dashboard | tooltip-bearing control | "Points per Year" number_input, key `m_gov_pts`, help "Extra percentage points of the government budget going to health, added each year (cumulative). ..." | pu.gradual_controls | pu:136-139 | conditional: as above |
| MAIN-UI-039 | Dashboard | caption/text block | "No data on this government's total spending, so a budget increase can't be modelled." | ms._controls | ms:579 | conditional: Gradual and no government spending data |
| MAIN-UI-040 | Dashboard | tooltip-bearing control | "Fiscal-Space Ceiling" radio, key `m_effort`; options "Strong Year (75th Percentile Growth)", "Best Years (90th Percentile Growth)"; disabled when No Government Replacement; help "How hard can the health budget be pushed? ..." | ms._controls | ms:582-586 | always |
| MAIN-UI-041 | Dashboard | control | "Cap Replacement at Fiscal Space" checkbox (default OFF since a33fefb "edit v1"; on at 23c4f46), key `m_cap`; disabled for none/max | ms._controls | ms:587-588 | always |
| MAIN-UI-042 | Dashboard | tooltip-bearing control | "Health Budget Reaches the Abuja Target" checkbox, key `m_abuja` | ms._controls | ms:591-594 | not shown: SHOW_GOV_OPTIONS = False (ms:352) |
| MAIN-UI-043 | Dashboard | tooltip-bearing control | "Tax Collection Rises to 15% of GDP" checkbox, key `m_tax` | ms._controls | ms:595-600 | not shown: SHOW_GOV_OPTIONS = False |
| MAIN-UI-044 | Dashboard | caption/text block | policy_caption "By 2030: Abuja target: +$... a year; tax at 15% of GDP ...(phased in from 2026)." | ms._controls / ms.policy_caption | ms:607-608; ms:737-749 | not shown: SHOW_GOV_OPTIONS = False |
| MAIN-UI-045 | Dashboard | expander | Popover "Advanced" (icon tune) | ms._controls | ms:611 | always |
| MAIN-UI-046 | Dashboard | tooltip-bearing control | "Where Replacement Money Goes" radio, key `m_alloc`; options "Pro-Rata to What Was Cut", "Hypothetical Best Case (Triage)"; disabled when none; help "Hypothetical best case: an optimisation rule, ..." | ms._controls | ms:613-617 | always (inside Advanced) |
| MAIN-UI-047 | Dashboard | control | "Compare with a Second Scenario" toggle (default off), key `m_compare` | ms._controls | ms:621 | always (inside Advanced) |
| MAIN-UI-048 | Dashboard | control | "Donor Scenario (B)" selectbox, key `mb_preset`; options "Same as Scenario A", "Announced Donor Cuts" | ms._controls | ms:622-625 | conditional: compare toggle on |
| MAIN-UI-049 | Dashboard | control | "Government Response (B)" radio, key `mb_mode`; options No Government Replacement, Replace a Set Share, As Much as Fiscal Space Allows (default), Gradual Budget Increase | ms._controls | ms:631-633 | conditional: compare toggle on |
| MAIN-UI-050 | Dashboard | control | "Share of Lost Aid Replaced (B, %)" slider, key `mb_theta` | ms._controls | ms:634-635 | conditional: compare on and B response = Replace a Set Share |
| MAIN-UI-051 | Dashboard | control | "Where Replacement Money Goes (B)" radio, key `mb_alloc`; default Hypothetical Best Case (Triage) | ms._controls | ms:636-638 | conditional: compare toggle on |
| MAIN-UI-052 | Dashboard | caption/text block | "Scenario B uses Scenario A's fiscal-space ceiling and model parameters." | ms._controls | ms:639 | conditional: compare toggle on |
| MAIN-UI-053 | Dashboard | control | Scenario B custom cuts (data editor key `mb_custom_tbl`, sliders `mb_ch_*`, expander "Cuts by Donor and Channel") | ms._preset_options(…, "mb") | ms:630 | not shown: Donor Scenario (B) never offers Custom (Custom not in PRECOMPUTED_PRESETS) |
| MAIN-UI-054 | Dashboard | heading | "**Model Parameters**" | ms._controls | ms:642 | always (inside Advanced) |
| MAIN-UI-055 | Dashboard | caption/text block | "Each parameter is drawn from a triangular distribution (low, central, high). Edit any cell to see how sensitive the answer is." | ms._controls | ms:643-644 | always (inside Advanced) |
| MAIN-UI-056 | Dashboard | control | Parameter data editor, key `m_params`; visible columns "Label" · "Central" · "Low" · "High" · "Unit" · "Status" · "Source" (param hidden; Label/Unit/Status/Source disabled), width 900, one row per model_params.csv parameter (46 rows) | ms._controls | ms:645-649 | always (inside Advanced) |
| MAIN-UI-057 | Dashboard | caption/text block | "Not applied: {problems}. Using the last valid values." | ms._controls | ms:652-654 | conditional: edited parameters invalid |
| MAIN-UI-058 | Dashboard | heading | Kicker "{country}'s MOU schedule" + small schedule chart + caption "Schedule ends {yr}; the {yr} level is held through 2030." | ms._controls / pu.mou_schedule_chart | ms:660-666 | not shown: America First MOUs not offered |
| MAIN-UI-059 | Dashboard | heading | Kicker "Announced phase-out in {country}, by funder" | ms.phase_out_by_donor_chart | ms:447-448 | conditional: preset = Announced and phase_out_by_donor non-empty |
| MAIN-UI-060 | Dashboard | chart | Announced phase-out by funder (lines, no title). One line per funder, direct labels: United States, Global Fund, Gavi, United Kingdom, Germany, France, Japan, Canada, Netherlands, Nordics, Other DAC Governments, Foundations, Banks and Others; x "Year", y "Share of 2019-2023 Aid Cut" | ms.phase_out_by_donor_chart | ms:442-474 (called ms:671) | conditional: as kicker above |
| MAIN-UI-061 | Dashboard | chart | Small red line "share of aid cut" per year (no title, 120 px) | pu.mou_schedule_chart | pu:101-116 (called ms:669) | conditional: preset = Announced and phase_out_by_donor empty (cut model lacks the country) |
| MAIN-UI-062 | Dashboard | caption/text block | Year labels "2026" ... "2030" above the per-year sliders (class ed-year) | pu.year_panel | pu:154 | conditional: panel expanded = (Custom and How Funding Changes != Sudden) or Government Response = Gradual Budget Increase |
| MAIN-UI-063 | Dashboard | chart | Funding-path chart (no title): trace "Aid Cut in Force" (or "Aid Cut (Announced)" / "US Bilateral Aid Cut (MOU)" when a schedule is fixed), trace "Extra Health Share" (gradual only, right axis); background shading with annotations "Unfilled Gap" / "Gap Filled" | pu._chart | pu:189-224 (via pu:183-185) | conditional: panel expanded |
| MAIN-UI-064 | Dashboard | control | "Aid Cut" sliders ×5 (0-100 step 5, format %d%%), keys `m_cut_2026` … `m_cut_2030` | pu.year_panel | pu:157 | conditional: panel expanded and no fixed schedule (i.e. Custom) |
| MAIN-UI-065 | Dashboard | control | "Extra Health Share" sliders ×5 (0-room, format +%.1f pts), keys `m_gov_2026` … `m_gov_2030` | pu.year_panel | pu:162-163 | conditional: expanded, Gradual Budget Increase, room to Abuja > 0 |
| MAIN-UI-066 | Dashboard | caption/text block | "Already at the 15% target" | pu.year_panel | pu:165 | conditional: Gradual and room <= 0 |
| MAIN-UI-067 | Dashboard | caption/text block | "Note: the cut falls in {years}. That is read as aid returning, and people return to care." | pu.year_panel | pu:172-173 | conditional: Custom path with a falling year |
| MAIN-UI-068 | Dashboard | control | "Reset to Shape" button (tertiary, icon restart_alt), key `path_reset_btn` | pu.year_panel | pu:174-175 | conditional: panel expanded and no fixed schedule |
| MAIN-UI-069 | Dashboard | caption/text block | "{country}: health is X% of government spending ({year}); fastest sustained rise in its history: Y points a year (90th percentile of its 2001-2023 yearly changes)." | pu.outcome_panel | pu:240-244 | conditional: panel expanded, country modelled, health share known |
| MAIN-UI-070 | Dashboard | card/metric | Pill "Net Aid Lost per Year" (tooltip "Average 2026-2030, after government replacement") | pu.outcome_panel | pu:251 | conditional: panel expanded and country modelled (ms:760-766) |
| MAIN-UI-071 | Dashboard | card/metric | Pill "People Losing a Service per Year" (tooltip "People-equivalents: the services the lost money would have paid for") | pu.outcome_panel | pu:252-253 | conditional: as above |
| MAIN-UI-072 | Dashboard | card/metric | Pill "People Kept in Services vs Sudden Cut With No Response" (note "of {N}") | pu.outcome_panel | pu:254-255 | conditional: as above |
| MAIN-UI-073 | Dashboard | card/metric | Pill "Break-Even Budget Increase" ("Not reachable by 15%" / "None needed" / "+x points a year") | pu.outcome_panel | pu:256-257 | conditional: as above |
| MAIN-UI-074 | Dashboard | caption/text block | Outcome sentence "{path phrase} and {response}, {country} {keeps pace ...} and keeps about N more people a year in services than a sudden cut would. ..." | pu.outcome_panel | pu:268-276 | conditional: as above |
| MAIN-UI-075 | Dashboard | caption/text block | "Assumes new government money is spent as efficiently as donor money." | pu.outcome_panel | pu:277 | conditional: as above |
| MAIN-UI-076 | Dashboard | section | "Revenue and Spending in {country}" (badge account_balance, no rule) | th.section_header | D:526 | always |
| MAIN-UI-077 | Dashboard | caption/text block | st.info "The IMF files have no government revenue or spending-by-function data for {country}." | _budget_section | D:337 | conditional: no IMF revenue and spending years |
| MAIN-UI-078 | Dashboard | control | "Year" selectbox, key `c4_year_{iso3}`; options = IMF years (newest first), default newest year with both sides | _budget_section | D:344 | conditional: IMF data exist |
| MAIN-UI-079 | Dashboard | tooltip-bearing control | "Health Share of Government Spending (%)" slider 0-30 step 0.5, key `bud_share_{iso3}`, help "Today: x%. Abuja target: 15%." | ms.budget_sliders | ms:727-728 (called D:346) | conditional: country has health-share and tax data |
| MAIN-UI-080 | Dashboard | tooltip-bearing control | "Tax Revenue (% of GDP)" slider 0-40 step 0.5, key `bud_tax_{iso3}`, help "Today: x% (year). IMF benchmark: 15%." | ms.budget_sliders | ms:730-731 | conditional: as above |
| MAIN-UI-081 | Dashboard | caption/text block | st.info "No IMF revenue or spending data for {country} in {yr}." | _budget_section | D:372 | conditional |
| MAIN-UI-082 | Dashboard | chart | Treemap "Government Revenue and Spending, {yr}". Boxes (title-cased): Government Budget; Money In: Revenue ({level}) [+ Borrowing] or "Revenue (No Breakdown Available for {yr})"; revenue items; Other Levels of Government (No Breakdown); Added Tax Revenue; Borrowing (Spending Beyond Revenue); Money Out: Spending ({level}) [+ Surplus]; Health; Added Health Spending; COFOG functions; Surplus (Revenue Not Spent). Source line | _budget_section -> ms.chart | D:467-476 | conditional: IMF data for the year |
| MAIN-UI-083 | Dashboard | card/metric | Pill "Revenue, {yr}" (note "x% of GDP", tooltip basis) | _budget_section -> ms.pill_row | D:493, 503 | conditional: revenue total known |
| MAIN-UI-084 | Dashboard | card/metric | Pill "Spending, {yr}" | _budget_section | D:495, 503 | conditional: spending total known |
| MAIN-UI-085 | Dashboard | card/metric | Pill "Deficit (Borrowing)" or "Surplus" | _budget_section | D:496-499, 503 | conditional: both sides present |
| MAIN-UI-086 | Dashboard | card/metric | Pill "Gross Government Debt, {yr}" | _budget_section | D:500-503 | conditional: WEO debt known |
| MAIN-UI-087 | Dashboard | card/metric | Pill "Added for Health by 2030" (note "{x}% of the aid lost in 2030" under Announced) | _budget_section | D:504-511 | conditional: budget sliders moved above today's level |
| MAIN-UI-088 | Dashboard | caption/text block | Side notes (budget_section: "Central-government figures exceed the IMF WEO general-government total this year, ..." / "Revenue and spending come from different levels of government in this year's data.") | _budget_section | D:513-515 | conditional |
| MAIN-UI-089 | Dashboard | caption/text block | "The IMF World Economic Outlook has no general-government totals for this year, so each side is sized from its own IMF file, ..." | _budget_section | D:516-518 | conditional: no WEO totals |
| MAIN-UI-090 | Dashboard | section | "Money Spent on Health in {country}, Over Time" (badge payments) with info-icon tooltip "DAH = development assistance for health: ..." | th.section_header | D:532-534 | always |
| MAIN-UI-091 | Dashboard | caption/text block | st.info "{country} isn't in the IHME health-spending dataset (it covers 204 countries and territories), ..." | page module | D:537 | conditional |
| MAIN-UI-092 | Dashboard | control | "Show As" radio (label collapsed, horizontal), key `c2_view`; options "US$ Total", "US$ per Person", "Share of Total (%)" | page module | D:541-543 | conditional: country has spending file |
| MAIN-UI-093 | Dashboard | chart | "Health Spending by Source" / sub "2015-2023; Constant 2023 US$". Series (direct labels): Foreign Aid for Health (DAH), Government, Prepaid Private, Out-of-Pocket; y "US$ {Millions/Billions} (Constant 2023)" / "US$ per Person (Constant 2023)" / "% Of Total Health Spending". Source "IHME Global Health Spending 1995-2023; constant 2023 US$." | page module -> ms.chart | D:567-587 | conditional: spending file |
| MAIN-UI-094 | Dashboard | card/metric | Pill "Total Spending, 2023" | ms.pill_row | D:590-591 | conditional: spending file |
| MAIN-UI-095 | Dashboard | card/metric | Pill "Foreign Aid Share of Total, 2023" | ms.pill_row | D:592-593 | conditional: spending file |
| MAIN-UI-096 | Dashboard | section | "Who Is Providing the Money in {country}?" (badge public) | th.section_header | D:600 | always |
| MAIN-UI-097 | Dashboard | caption/text block | st.info "{country} is not a recipient in the IHME DAH database (typically a high-income country), ..." | page module | D:603 | conditional |
| MAIN-UI-098 | Dashboard | control | "Health Category" selectbox, key `c1_hfa`; 11 options (see §7) | page module | D:609 | conditional: DAH file |
| MAIN-UI-099 | Dashboard | control | "Program Area" selectbox, key `c1_pa_{hfa}`; "All Program Areas" + the focus area's program areas | page module | D:616-618 | conditional: Health Category != All Focus Areas and it has program areas |
| MAIN-UI-100 | Dashboard | expander | Popover "Channel Settings" (icon tune) | page module | D:621 | conditional: DAH file |
| MAIN-UI-101 | Dashboard | tooltip-bearing control | Multiselect "Channels Drawn as NGO / Foundation (Lighter Shade)", key `c1_ngo`; 22 options (see §7), default US NGOs (NGO), International NGOs (INTLNGO), US Foundations (US_FOUND), Gates Foundation (Direct) (GATES); help "IHME doesn't record whether a government knew about a flow. ..." | page module | D:622-628 | conditional: DAH file (inside popover) |
| MAIN-UI-102 | Dashboard | card/metric | Pill "Total in {yr}" | ms.pill_row | D:668 | conditional: aid > 0 in last year |
| MAIN-UI-103 | Dashboard | card/metric | Pill "Via NGO / Foundation Channels, {yr}" | ms.pill_row | D:669 | conditional: aid > 0 |
| MAIN-UI-104 | Dashboard | card/metric | Pill "Largest Funder, {yr}" | ms.pill_row | D:670 | conditional: aid > 0 |
| MAIN-UI-105 | Dashboard | caption/text block | st.info "No funding recorded for this selection." | page module | D:672 | conditional |
| MAIN-UI-106 | Dashboard | chart | "Health Aid by Funder" / sub = title-cased focus area (e.g. "All Focus Areas", "HIV/AIDS: Treatment"). Series: United States, Gates Foundation, Private Philanthropy, United Kingdom, Germany, France, up to 3 spare top-6 funders, All Other Sources (solid = government channel, lighter = NGO/foundation); annotation "{funder}: x%<br>of {yr} aid"; note "Lighter shades are aid delivered through NGOs and foundations, ..."; source IHME DAH | page module -> ms.chart | D:676-713 | conditional: DAH file |
| MAIN-UI-107 | Dashboard | heading | st.subheader "Where the Aid Is Spent" | page module | D:719 | always |
| MAIN-UI-108 | Dashboard | caption/text block | st.info "{country} is not a recipient in the IHME DAH database, so there is no category breakdown to show." | page module | D:732 | conditional |
| MAIN-UI-109 | Dashboard | control | "Show As" radio (label collapsed, horizontal), key `c3b_view`; options "US$ Total", "Share of Total (%)" | page module | D:737-739 | conditional: DAH file |
| MAIN-UI-110 | Dashboard | control | "Break Down" selectbox, key `c3b_brk`; 9 options (see §7) | page module | D:741-742 | conditional: DAH file |
| MAIN-UI-111 | Dashboard | caption/text block | st.info "No funding recorded for this selection." | page module | D:768 | conditional |
| MAIN-UI-112 | Dashboard | chart | "Health Aid by What It Pays For" / sub "All Focus Areas" or "Inside {focus area}". Series (All): HIV/AIDS, Tuberculosis, Malaria, Newborn & Child Health (Incl. Vaccines), Reproductive & Maternal Health, Health Systems Strengthening, All Other; (inside one area): 6 largest program areas + "Smaller Categories"; y "% Of Health Aid" or "US$ {unit} (Constant 2023)" | page module -> ms.chart | D:773-797 | conditional: DAH file |
| MAIN-UI-113 | Dashboard | section | "How Aid Cuts Translate into Coverage in {country}" (badge monitor_heart) with info tooltip INTRO "A three-step model for HIV, TB, malaria and immunization: ..." | ms.render_model_section | ms:1027 (called D:814) | always |
| MAIN-UI-114 | Dashboard | caption/text block | st.info "{country} has no recorded HIV, TB, malaria or vaccine aid in 2021-2023, so there is nothing to model for this country. See the All Countries page for the other countries." | ms.render_model_section | ms:1029-1030 | conditional: country not modelled |
| MAIN-UI-115 | Dashboard | caption/text block | st.success "Under '{preset}' {country} loses no HIV, TB, malaria or vaccine aid[ (aid rises by $X a year; gains aren't modelled).]" | ms._country_results | ms:1044-1047 | conditional: gross loss 0 |
| MAIN-UI-116 | Dashboard | heading | st.subheader "Scenario A vs Scenario B" | ms._comparison | ms:1190 | conditional: compare toggle on |
| MAIN-UI-117 | Dashboard | caption/text block | "**Scenario A:** {scenario} · {response}" and "**Scenario B:** ..." | ms._comparison | ms:1196 | conditional: compare on |
| MAIN-UI-118 | Dashboard | card/metric | Pill "Aid at Risk (per Year)" ×2 (A and B) (note "x% of $Y for These Four Buckets"; tooltip) | ms._headline_items -> ms._stat_grid | ms:1169-1171, 1197 | conditional: compare on |
| MAIN-UI-119 | Dashboard | card/metric | Pill "Replaced by Government" ×2 | ms._headline_items | ms:1172-1174, 1197 | conditional: compare on |
| MAIN-UI-120 | Dashboard | card/metric | Pill "Net Aid Lost" ×2 (note from net_aid_note: "Per Year" or "Incl. $X Health-Systems Money, …") | ms._headline_items | ms:1175, 1197 | conditional: compare on |
| MAIN-UI-121 | Dashboard | card/metric | Pill "People Losing a Service (per Year)" ×2 (note "All Four Diseases") | ms._headline_items | ms:1176-1178, 1197 | conditional: compare on |
| MAIN-UI-122 | Dashboard | caption/text block | "Scenario B keeps services for about **N** more/fewer people a year in {country} than Scenario A." | ms._comparison | ms:1199-1200 | conditional: compare on |
| MAIN-UI-123 | Dashboard | chart | "Net Aid Lost by Disease" / sub "Scenario A vs. B, per Year"; traces "Scenario A", "Scenario B"; x HIV, TB, Malaria, Immunization; y "US$ Million a Year" | ms._comparison | ms:1202-1212 | conditional: compare on |
| MAIN-UI-124 | Dashboard | caption/text block | "Government replacement of $X a year keeps services for about **N people a year** compared with no government replacement." | ms._country_results | ms:1055-1058 | conditional: a response is on and replaced > 0 |
| MAIN-UI-125 | Dashboard | heading | st.subheader "Where the Money Is Lost" | ms._country_results | ms:1061 | conditional: country modelled |
| MAIN-UI-126 | Dashboard | caption/text block | st.info "No aid is cut in this scenario." | ms._country_results | ms:1065 | conditional |
| MAIN-UI-127 | Dashboard | chart | "Aid Lost per Year" (sub "Lighter = Replaced by Government" when anything replaced); bars per disease, traces "Lost to Services" / "Replaced by Government" (legend hidden), totals as text; bordered container key "money_lost" | ms._loss_by_bucket_fig | ms:1293-1314 (called ms:1071) | conditional: some aid cut |
| MAIN-UI-128 | Dashboard | chart | "Who Cut the Money"; one bar per donor · channel (e.g. "US · Bilateral"), max 12 bars incl. "All other" | ms._who_cut_fig | ms:1331-1345 (called ms:1073) | conditional: some aid cut |
| MAIN-UI-129 | Dashboard | heading | st.subheader "Service Coverage, Year by Year" | ms._country_results | ms:1076 | conditional: country modelled |
| MAIN-UI-130 | Dashboard | chart | Small multiples, one chart per service, 3 per row, worst drop first. Title = service name (HIV Treatment, Mother-to-Child Transmission, TB Treatment, Drug-Resistant TB, Bednets, Indoor Spraying, Malaria Treatment, Routine Immunization), sub "{$cost} Per {unit}" (e.g. "$308 per Patient-Year of ART"); x "Now", 2026…2030; y "Coverage" (%); end annotation "−x pts" | ms._service_grid -> ms._service_fig | ms:1625-1635, ms:1604-1622 (called ms:1077) | conditional: country modelled; one chart per service with a coverage figure |
| MAIN-UI-131 | Dashboard | caption/text block | st.info "No service has a coverage figure in this scenario." | ms._service_grid | ms:1629 | conditional |
| MAIN-UI-132 | Dashboard | table | Coverage-drop overview (st.html): caption line "Coverage today → {last year}, largest drop first"; columns (no header row): Service (colour dot + name) · "{today}% → {2030}%" · "−x pts" · status "Needs help" (>=10 pts) / "Watch" (5-10) / "Holding"; or "No service loses coverage in this scenario." | ms._drop_overview_html | ms:1584-1601 (called ms:1078) | conditional: country modelled |
| MAIN-UI-133 | Dashboard | caption/text block | Source line "Model estimates; coverage today: UNAIDS/WHO 2025 (HIV), WHO 2024 (TB), Malaria Atlas Project 2025 (malaria), WUENIC (DTP3)." | ms._country_results | ms:1079-1080 | conditional: country modelled |
| MAIN-UI-134 | Dashboard | heading | st.subheader "Can {country} Fill the Gap?" with help tooltip ("All three numbers come from the same run as the headline, ... debt-stress factor ...") | ms._fiscal_panel | ms:1813-1820 | conditional: country modelled |
| MAIN-UI-135 | Dashboard | card/metric | Pill "Government Health Spending (2023)" (tooltip "IHME, constant 2023 US$", note "x% of GDP") | ms._fiscal_panel | ms:1827-1829 | conditional: country modelled |
| MAIN-UI-136 | Dashboard | card/metric | Pill "Aid Lost as % of Government Health Spending" | ms._fiscal_panel | ms:1830-1831 | conditional: country modelled |
| MAIN-UI-137 | Dashboard | card/metric | Pill "Aid Lost as % of Government Revenue" | ms._fiscal_panel | ms:1832-1833 | conditional: country modelled |
| MAIN-UI-138 | Dashboard | card/metric | Pill "Health Share of Government Spending, {yr}" / "…, {yr} (estimated)" / "Health Share of Government Spending" (n/a); note "Abuja Target: 15%" | ms.health_share_pill | ms:1786-1797, 1834 | conditional: country modelled |
| MAIN-UI-139 | Dashboard | chart | "The Gap and the Government Response" / sub "US$ per Year"; rows "2026-30 Average" (+ "2030" when different); traces "Gap", "Filled by the Government", "Gap Left"; "{$} gap" labels; dashed line + annotation "Fiscal Space: {$}"; note "Backfill capacity (fiscal space), $X a year, is off the scale of this chart." when off scale; source "IHME Government health spending, 2001-2023" | ms._fiscal_panel | ms:1837-1876 | conditional: average gap > 0 |

### 3. All Countries (views/2_All_Countries.py)

| ID | Page | Kind | Name as shown | Rendering function | file:line | Shown? |
|---|---|---|---|---|---|---|
| MAIN-UI-140 | All Countries | heading | st.title "All Countries" | page module | AC:21 | always |
| MAIN-UI-141 | All Countries | tooltip-bearing control | "Donor Scenario" selectbox, key `ac_preset` (shared `sel_preset`); options "Announced Donor Cuts", "Custom"; help = scn.PRESETS text | th.shared_select | AC:24-26 -> th:528 | always |
| MAIN-UI-142 | All Countries | caption/text block | st.info "No country loses aid in this scenario." | ms.cross_country | ms:2031 | conditional |
| MAIN-UI-143 | All Countries | caption/text block | Caption "{Scenario} · {response label}" (e.g. "Announced Donor Cuts · No Government Replacement") | ms.cross_country | ms:2035-2036 | conditional: some country loses aid |
| MAIN-UI-144 | All Countries | caption/text block | "This page uses the default cuts (...). Your setting (...) applies to the country Dashboard only." | ms.cross_country | ms:2037-2039 | not shown: Shortfalls not offered |
| MAIN-UI-145 | All Countries | heading | st.subheader "MOU Countries With Funding Data ({n})" with help | ms.cross_country | ms:2040-2044 | not shown: America First MOUs not offered |
| MAIN-UI-146 | All Countries | card/metric | Pill "Aid Lost per Year, {n} of {N} Countries" (MOU variant: "Aid Lost per Year, MOU Countries With Funding Data ({n})"); tooltip incl. SCOPE_NOTE; note "Net Aid Lost {$}" | ms.cross_country | ms:2050-2054 | conditional: some country loses aid |
| MAIN-UI-147 | All Countries | card/metric | Pill "People Losing a Service per Year" | ms.cross_country | ms:2055-2058 | conditional: as above |
| MAIN-UI-148 | All Countries | card/metric | Pill "HIV and TB Treatment Lost per Year" | ms.cross_country | ms:2059-2060 | conditional: as above |
| MAIN-UI-149 | All Countries | card/metric | Pill "Children Missing Vaccines per Year" | ms.cross_country | ms:2061-2062 | conditional: as above |
| MAIN-UI-150 | All Countries | tooltip-bearing control | "World" toggle (default off), key `m_map_world`, help "Show the whole world instead of Africa and Asia" | ms.cross_country | ms:2067-2068 | conditional: some country loses aid |
| MAIN-UI-151 | All Countries | chart | Choropleth "People Losing a Service per 100,000" / sub "Each Year"; colour bar "People Losing a Service per 100,000 (per Year)"; selected country outlined; MOU grey layers "MOU signed; no funding data" / "No MOU" only for MOU preset | ms._world_map | ms:2149-2184 (called ms:2070) | conditional: some country loses aid |
| MAIN-UI-152 | All Countries | chart | Scatter "Budget Exposure vs. Services Lost" / sub "Each Circle Is a Country"; x "Aid Lost, % of Govt. Health Spending (Log)", y "People Losing a Service per 100,000 (Log)"; 8 labelled ISO3 codes; note "Each circle is a country, sized by aid lost per year; {country} is highlighted. Dotted lines are medians." | ms.cross_country | ms:2073-2120 | conditional: some country loses aid |
| MAIN-UI-153 | All Countries | chart | Stacked bars "Most People Losing a Service, per Year" + colour key HIV · TB · Malaria · Immunization; top 15 countries, totals as text; note "{country} ranks {r} of {n}." if outside top 15 | ms.cross_country | ms:2121-2145 | conditional: some country loses aid |

### 4. Methods (views/4_Methods.py)

All headings below. Level: H1 = st.title; T = tab; H2 = th.section_header (badge heading); H3 = bold run-in paragraph lead inside md() (bullet-list bold leads are not listed as headings). Tables include markdown tables written inside md().

| ID | Page | Kind | Name as shown | Rendering function | file:line | Shown? |
|---|---|---|---|---|---|---|
| MAIN-UI-154 | Methods | heading | H1 "Methods, Data and Limitations" | page module | M:80 | always |
| MAIN-UI-155 | Methods | caption/text block | "A complete guide to how every number on the dashboard is calculated, ..." | page module | M:81-82 | always |
| MAIN-UI-156 | Methods | tab | Tab "Overview" | st.tabs | M:84 | always |
| MAIN-UI-157 | Methods | tab | Tab "Dashboard Sections" | st.tabs | M:84 | always |
| MAIN-UI-158 | Methods | tab | Tab "The Model, Step by Step" | st.tabs | M:84 | always |
| MAIN-UI-159 | Methods | tab | Tab "Data Sources" | st.tabs | M:85 | always |
| MAIN-UI-160 | Methods | tab | Tab "Assumptions & Limitations" | st.tabs | M:85 | always |
| MAIN-UI-161 | Methods | tab | Tab "Parameters" | st.tabs | M:85 | always |
| MAIN-UI-162 | Methods | section | H2 "What the Dashboard Does" (Overview) | th.section_header | M:91 | always (tab Overview) |
| MAIN-UI-163 | Methods | heading | H3 "Description (Sections 1 to 3)." | md | M:95 | always (tab Overview) |
| MAIN-UI-164 | Methods | heading | H3 "Simulation (Section 4 and the All Countries page)." | md | M:99 | always (tab Overview) |
| MAIN-UI-165 | Methods | section | H2 "Units and Currency" | th.section_header | M:110 | always (tab Overview) |
| MAIN-UI-166 | Methods | heading | H3 "Every dollar figure is in constant 2023 US dollars (except MOU amounts)" | md | M:112 | always (tab Overview) |
| MAIN-UI-167 | Methods | section | H2 "Time Periods" | th.section_header | M:131 | always (tab Overview) |
| MAIN-UI-168 | Methods | table | Markdown table: What · Years (8 rows) | md | M:133-142 | always (tab Overview) |
| MAIN-UI-169 | Methods | section | H2 "Data Years" | th.section_header | M:144 | always (tab Overview) |
| MAIN-UI-170 | Methods | table | st.table data_years_table: index "Input"; columns Year · Source · Countries by source (20 rows, ms.DATA_YEARS ms:1883-1909) | ms.data_years_table | M:149 (fn ms:1945-1962) | always (tab Overview) |
| MAIN-UI-171 | Methods | section | H2 "Country Header" | th.section_header | M:155 | always (tab Dashboard Sections) |
| MAIN-UI-172 | Methods | table | Markdown table: Pill · How it is calculated · Source (rows Region, Income Group, US MOU, GDP, Population) | md | M:157-163 | always |
| MAIN-UI-173 | Methods | section | H2 "Section 1: Money Spent on Health" | th.section_header | M:166 | always |
| MAIN-UI-174 | Methods | heading | H3 "Data:" | md | M:168 | always |
| MAIN-UI-175 | Methods | table | Markdown table: Bar · IHME variable · Meaning (Government, Prepaid Private, Out-of-Pocket, Foreign Aid for Health (DAH)) | md | M:172-177 | always |
| MAIN-UI-176 | Methods | section | H2 "Section 2: Who Is Providing the Money" | th.section_header | M:187 | always |
| MAIN-UI-177 | Methods | heading | H3 "Data:" | md | M:189 | always |
| MAIN-UI-178 | Methods | heading | H3 "Funders." | md | M:192 | always |
| MAIN-UI-179 | Methods | heading | H3 "NGO / foundation channels (lighter shade)." | md | M:198 | always |
| MAIN-UI-180 | Methods | heading | H3 "Pills:" | md | M:204 | always |
| MAIN-UI-181 | Methods | heading | H3 "Where the Aid Is Spent." | md | M:207 | always |
| MAIN-UI-182 | Methods | section | H2 "Section 3: Revenue and Spending" | th.section_header | M:214 | always |
| MAIN-UI-183 | Methods | heading | H3 "Data:" | md | M:216 | always |
| MAIN-UI-184 | Methods | table | Markdown table: Part · Dataset · Variables (Size of each side, Revenue mix, Spending mix) | md | M:218-222 | always |
| MAIN-UI-185 | Methods | heading | H3 "How the treemap is built." | md | M:224 | always |
| MAIN-UI-186 | Methods | heading | H3 "Health check." | md | M:246 | always |
| MAIN-UI-187 | Methods | section | H2 "Section 4 Outputs" | th.section_header | M:251 | always |
| MAIN-UI-188 | Methods | table | Markdown table: Output · Definition. Rows: Aid at Risk (per Year); Treatment Lost Each Year; Prevention Lost Each Year (top of the Dashboard); Replaced by Government; Net Aid Lost; People Losing a Service (per Year); Biggest risks (top of the Dashboard, Announced donor cuts); What Every US$1 Million Cut Does, by Disease; What Each Service Loses; Can {Country} Fill the Gap?; All Countries. NOTE: "Biggest risks", "What Every US$1 Million Cut Does, by Disease" and "What Each Service Loses" describe components not rendered on main (see §6) | md | M:253-264 | always |
| MAIN-UI-189 | Methods | section | H2 "Step 1: Money (What Aid Is Lost)" | th.section_header | M:271 | always (tab The Model) |
| MAIN-UI-190 | Methods | heading | H3 "Baseline." | md | M:273 | always |
| MAIN-UI-191 | Methods | caption/text block | LaTeX: baseline_c = 1/3 Σ DAH × 1000 | st.latex | M:276-277 | always |
| MAIN-UI-192 | Methods | heading | H3 "Service lines" | md | M:279 | always |
| MAIN-UI-193 | Methods | table | Markdown table: Service line · Bucket · IHME program-area columns (15 rows) | md | M:281-297 | always |
| MAIN-UI-194 | Methods | heading | H3 "Source groups" | md | M:299 | always |
| MAIN-UI-195 | Methods | heading | H3 "Channel groups" | md | M:304 | always |
| MAIN-UI-196 | Methods | heading | H3 "The cut in each cell." | md | M:309 | always |
| MAIN-UI-197 | Methods | caption/text block | LaTeX: cut_c = 1-(1-donor cut)(1-channel cut), loss_c = baseline_c × cut_c | st.latex | M:313 | always |
| MAIN-UI-198 | Methods | heading | H3 "Money with no reported purpose." | md | M:315 | always |
| MAIN-UI-199 | Methods | heading | H3 "Systems money" | md | M:329 | always |
| MAIN-UI-200 | Methods | heading | H3 "HIV testing and care." | md | M:336 | always |
| MAIN-UI-201 | Methods | caption/text block | LaTeX: effective loss_ℓ = ... σ = 0, plus text "where s_p is the share ..." | st.latex / md | M:346-348 | always |
| MAIN-UI-202 | Methods | heading | H3 "Donor scenarios (presets)." | md | M:350 | always |
| MAIN-UI-203 | Methods | table | Markdown table: Scenario · What is cut · Source of the numbers (rows US Bilateral Exit + Multilateral Withdrawals, America First MOUs, IHME 2025 Preliminary Estimates, Total-Aid Cuts (OECD) Applied to Health Aid, Global Fund & Gavi Shortfalls, Combined Retreat, Custom; Announced donor cuts is NOT a row) | md | M:352-360 | always |
| MAIN-UI-204 | Methods | section | H2 "Step 2: Fiscal Response (What the Government Replaces)" | th.section_header | M:363 | always |
| MAIN-UI-205 | Methods | caption/text block | LaTeX: R = min(wanted, capacity), capacity = GHES2023 × max(0, g_strong − max(g_typical,0)) × s | st.latex | M:373 | always |
| MAIN-UI-206 | Methods | caption/text block | LaTeX: s = clip(1 − (interest % of revenue − 10)/40, 0.25, 1) | st.latex | M:388 | always |
| MAIN-UI-207 | Methods | heading | H3 "Why No Government Replacement is the default." | md | M:390 | always |
| MAIN-UI-208 | Methods | heading | H3 "Where replacement money goes." | md | M:397 | always |
| MAIN-UI-209 | Methods | section | H2 "Step 3: Coverage (Who Loses a Service)" | th.section_header | M:403 | always |
| MAIN-UI-210 | Methods | caption/text block | LaTeX: donor-funded_ℓ = min(people covered × external share, aid now ÷ cost per person) | st.latex | M:417 | always |
| MAIN-UI-211 | Methods | caption/text block | LaTeX: people losing service_ℓ = donor-funded × aid lost/aid now × (1 − continuity) | st.latex | M:418 | always |
| MAIN-UI-212 | Methods | heading | H3 "Cost per person" | md | M:443 | always |
| MAIN-UI-213 | Methods | table | Markdown table: Service · Formula · Central value / source (HIV treatment, PMTCT, HIV prevention, Orphans & vulnerable children, TB treatment, Drug-resistant TB, Bednets, Indoor spraying, Malaria testing & treatment, Routine immunization) | md | M:445-456 | always |
| MAIN-UI-214 | Methods | heading | H3 "People in need and current coverage." | md | M:458 | always |
| MAIN-UI-215 | Methods | table | Markdown table: Service · People in need · Current coverage (8 rows) | md | M:467-476 | always |
| MAIN-UI-216 | Methods | section | H2 "Funding Paths Over 2026-2030" | th.section_header | M:482 | always |
| MAIN-UI-217 | Methods | caption/text block | LaTeX: net gap(t) = max(0, aid lost × c(t) − government response(t) − A(t)) | st.latex | M:491 | always |
| MAIN-UI-218 | Methods | heading | H3 "Shapes" | md | M:496 | always |
| MAIN-UI-219 | Methods | table | Markdown table: Shape · c(t), t = 1..5 · 2026-2030 (Sudden (default), Linear phase-out, Front-loaded, Back-loaded, S-curve, Custom) | md | M:498-505 | always |
| MAIN-UI-220 | Methods | heading | H3 "Gradual budget increase." | md | M:507 | always |
| MAIN-UI-221 | Methods | heading | H3 "Health's share of government spending" | md | M:512 | always |
| MAIN-UI-222 | Methods | heading | H3 "Break-even budget increase." | md | M:519 | always |
| MAIN-UI-223 | Methods | heading | H3 "Assumptions." | md | M:524 | always |
| MAIN-UI-224 | Methods | section | H2 "Uncertainty" | th.section_header | M:528 | always |
| MAIN-UI-225 | Methods | section | H2 "Datasets" | th.section_header | M:545 | always (tab Data Sources) |
| MAIN-UI-226 | Methods | table | Markdown table: Dataset · Provider and version · Variables used · Used in (17 rows) | md | M:547-565 | always |
| MAIN-UI-227 | Methods | section | H2 "World Development Indicators Used" | th.section_header | M:570 | always |
| MAIN-UI-228 | Methods | table | Markdown table: Code · Meaning · Used for (17 rows) | md | M:574-592 | always |
| MAIN-UI-229 | Methods | section | H2 "Published Studies Behind the Parameters" (bullet list) | th.section_header | M:594 | always |
| MAIN-UI-230 | Methods | section | H2 "Values That Are Assumptions" | th.section_header | M:622 | always (tab Assumptions & Limitations) |
| MAIN-UI-231 | Methods | caption/text block | "These parameters have no single published source; they are reasoned assumptions with wide ranges:" | md | M:624 | always |
| MAIN-UI-232 | Methods | table | st.table of status == "assumption" params: index "Label"; columns Central · Low · High · Unit · Source | page module | M:623-626 | always |
| MAIN-UI-233 | Methods | caption/text block | "Fixed structural assumptions (not in the parameter table): ..." (5 bullets) | md | M:627-637 | always |
| MAIN-UI-234 | Methods | section | H2 "Limitations" (10 bullets with bold leads: Average, not marginal, costs. / Donor money and service cost do not always line up. / No second-round effects. / No re-allocation by other donors / Post-2023 aid is not observed by recipient. / Inputs come from different years / Malaria coverage is modelled. / Program-area tags are partial / The regressions are associations, not causes. / Treat results as scenario estimates, not forecasts.) | th.section_header + md | M:638-661 | always |
| MAIN-UI-235 | Methods | section | H2 "Every Model Parameter" | th.section_header | M:667 | always (tab Parameters) |
| MAIN-UI-236 | Methods | caption/text block | "Each is drawn from a triangular distribution (low, central, high). ... Edit them under Advanced on the Dashboard ..." | md | M:668-669 | always |
| MAIN-UI-237 | Methods | table | st.table all params: index "Param"; columns Label · Central · Low · High · Unit · Status · Source (46 rows) | page module | M:670-671 | always |
| MAIN-UI-238 | Methods | section | H2 "Regression Estimates" | th.section_header | M:672 | always |
| MAIN-UI-239 | Methods | table | st.table: index "Regression"; columns Outcome · Main Regressor · Coefficient · Standard Error · Countries · Observations · Years (8 rows: Fiscal Replacement, Hiv Art, Tb Treatment, Dtp3, Malaria Incidence, Poisson Tb, Poisson U5, Poisson Malaria via str.title()) | page module | M:673-682 | always |
| MAIN-UI-240 | Methods | caption/text block | "Coverage and fiscal regressions: two-way (country and year) fixed effects, ..." | md | M:683-685 | always |
| MAIN-UI-241 | Methods | table | _u5_share_table: index "WHO Region"; columns Under-5 Share · Rule · Source · Countries With Malaria Deaths | _u5_share_table | M:52-73 | not shown: function never called |

### 5. Validation & Benchmarks (views/3_Validation.py): kept, NOT in navigation

Every row: **not shown: page not registered in th.PAGES**. The "Shown?" column gives the in-page condition if the page were reachable.

| ID | Page | Kind | Name as shown | Rendering function | file:line | Shown? |
|---|---|---|---|---|---|---|
| MAIN-UI-242 | Validation | heading | H1 "Validation & Benchmarks" | page module | V:30 | not in nav; always |
| MAIN-UI-243 | Validation | caption/text block | "How the funding-cut model on the dashboard compares with published studies, and with two other ways of estimating the same cut." | page module | V:31-32 | not in nav; always |
| MAIN-UI-244 | Validation | control | "Country" selectbox, key `v_country` (shared `sel_iso3`), 71 countries | th.shared_select | V:36 | not in nav; always |
| MAIN-UI-245 | Validation | tooltip-bearing control | "Donor Scenario" selectbox, key `v_preset` (shared `sel_preset`), options Announced Donor Cuts, Custom; help PRESETS | ms.donor_scenario_select | V:38 -> ms:508 | not in nav; always |
| MAIN-UI-246 | Validation | caption/text block | MOU notice caption | page module | V:39-40 | not in nav; conditional |
| MAIN-UI-247 | Validation | caption/text block | "{preset description} Government response (...), model parameters and the death-rate setting follow the dashboard." | page module | V:48-49 | not in nav; always |
| MAIN-UI-248 | Validation | section | H2 "How Our Totals Compare with Published Estimates" | th.section_header | V:54 | not in nav; always |
| MAIN-UI-249 | Validation | heading | H3 st.subheader "Model: Extra Deaths Over 5 Years, All {n} Countries" (help "America First MOUs covers only ...") | page module | V:67-68 | not in nav; always |
| MAIN-UI-250 | Validation | table | st.table: index "Scenario" (one row per precomputed preset, title-cased display name; MOU row "(… MOU Countries With Funding Data)"); columns HIV · TB · Malaria · Immunization · All Four · Range Across Parameter Values | page module | V:56-69 | not in nav; always |
| MAIN-UI-251 | Validation | caption/text block | "Read from the precomputed results: No Government Replacement, death rates already falling, default parameters. ..." | page module | V:70-72 | not in nav; always |
| MAIN-UI-252 | Validation | heading | H3 st.subheader "Published Estimates" (help on scopes) | page module | V:102-109 | not in nav; conditional: Full US exit precomputed file exists |
| MAIN-UI-253 | Validation | table | st.table: index "Source"; columns What It Measures · Published · Closest Model Figure (5 rows: Cavalcanti ×2, UNAIDS 2025, Optima, Gavi) | page module | V:78-110 | not in nav; conditional as above |
| MAIN-UI-254 | Validation | caption/text block | "The published studies cover more causes, sectors or years than the model, ..." | page module | V:111-112 | not in nav; conditional |
| MAIN-UI-255 | Validation | section | H2 "Lines Where Donor Money Exceeds the Modelled Service Cost" | th.section_header | V:126 | not in nav; always |
| MAIN-UI-256 | Validation | card/metric | Pills "Country-Service Lines Affected" · "Countries With At Least One" · "Lines in {country}" | th.pills_html | V:130-134 | not in nav; always |
| MAIN-UI-257 | Validation | table | st.table: index "Service"; column Countries | page module | V:135-138 | not in nav; conditional: any excess lines |
| MAIN-UI-258 | Validation | caption/text block | "In these lines, baseline donor aid ÷ cost per person is more than the donor-funded pool ..." | page module | V:139-143 | not in nav; always |
| MAIN-UI-259 | Validation | section | H2 "People on ART Paid for by Donors: Model vs PEPFAR" | th.section_header | V:154 | not in nav; always |
| MAIN-UI-260 | Validation | card/metric | Pills "Model: Donor-Funded People on ART" · "PEPFAR: People on ART It Supports" | th.pills_html | V:156-160 | not in nav; always |
| MAIN-UI-261 | Validation | caption/text block | "Model = for each country, the smaller of the people on ART ..." | page module | V:161-165 | not in nav; always |
| MAIN-UI-262 | Validation | section | H2 "Malaria Inputs: Malaria Atlas Project 2025 vs Previous Sources" | th.section_header | V:170 | not in nav; always |
| MAIN-UI-263 | Validation | card/metric | Pills "Baseline Malaria Deaths, Dashboard Countries" · "WHO Global Malaria Deaths, 2024" · "Share Covered by the Dashboard" | th.pills_html | V:176-182 | not in nav; always |
| MAIN-UI-264 | Validation | table | st.dataframe: index "Country"; columns Treatment: Before · Treatment: Now · Bednets: Before · Bednets: Now · Cases: Before · Cases: MAP 2025 · Cases: Change | ms.malaria_input_comparison | V:183-184 (fn ms:1965-1991) | not in nav; always |
| MAIN-UI-265 | Validation | caption/text block | "Treatment now = MAP effective treatment per 100 malaria cases, 2025; ... ⚑ = cases differ by more than 30% ..." | page module | V:185-192 | not in nav; always |
| MAIN-UI-266 | Validation | caption/text block | Pakistan caption "Pakistan: MAP puts cases at ..." | page module | V:195-206 | not in nav; conditional: PAK modelled |
| MAIN-UI-267 | Validation | section | H2 "Data Years" | th.section_header | V:208 | not in nav; always |
| MAIN-UI-268 | Validation | table | st.table data_years_table (same as Methods) | ms.data_years_table | V:209 | not in nav; always |
| MAIN-UI-269 | Validation | caption/text block | "Year = the most common year across the dashboard countries ..." | page module | V:210-211 | not in nav; always |
| MAIN-UI-270 | Validation | section | H2 "Three Ways to Estimate the Same Cut: {country}" | th.section_header | V:213 | not in nav; always |
| MAIN-UI-271 | Validation | caption/text block | "{scenario} · {response}[ · Death Rates Held Constant]" | page module | V:214 | not in nav; always |
| MAIN-UI-272 | Validation | caption/text block | st.info "{country} has no recorded HIV, TB, malaria or vaccine aid in 2021-2023, so there is nothing to model." (+ st.stop) | page module | V:216-218 | not in nav; conditional |
| MAIN-UI-273 | Validation | chart | "Extra Deaths by Method" / sub "{country}, Over 5 Years"; traces Unit-Cost Model, Poisson Regression, Lancet Rate Ratios; x HIV, TB, Malaria, Under-5, Maternal; y "Extra Deaths Over 5 Years"; error bars | page module -> ms.chart | V:230-250 | not in nav; conditional: country modelled |
| MAIN-UI-274 | Validation | caption/text block | "**Reading:** In {country}, ... land within a factor of two of the unit-cost model ..." | _reading | V:258-286 | not in nav; conditional |
| MAIN-UI-275 | Validation | heading | H3 st.subheader "Estimates by Method" (help = notes) | page module | V:309 | not in nav; conditional |
| MAIN-UI-276 | Validation | table | st.table: index "Bucket" (HIV, TB, Malaria, Under-5, Maternal); columns Unit-Cost Model · Poisson Regression · Lancet Rate Ratios ("Not Covered" where absent) | page module | V:288-310 | not in nav; conditional |
| MAIN-UI-277 | Validation | caption/text block | "Ranges: unit-cost model = range across parameter values ..." | page module | V:311-313 | not in nav; conditional |
| MAIN-UI-278 | Validation | section | H2 "How Each Method Works" | th.section_header | V:318 | not in nav; conditional |
| MAIN-UI-279 | Validation | heading | H3 st.subheader "Unit-Cost Model" (+ text with "**Main limitation:**") | page module | V:321-326 | not in nav; conditional |
| MAIN-UI-280 | Validation | heading | H3 st.subheader "Poisson Regression" (+ text) | page module | V:328-333 | not in nav; conditional |
| MAIN-UI-281 | Validation | heading | H3 st.subheader "Lancet Rate Ratios" (+ text) | page module | V:335-341 | not in nav; conditional |
| MAIN-UI-282 | Validation | heading | H3 st.subheader "Our Poisson Regressions" | page module | V:347 | not in nav; conditional |
| MAIN-UI-283 | Validation | table | st.table: index "Outcome" (TB Deaths, Under-5 Deaths, Child Malaria Deaths (Africa)); columns Aid Measure (Log 1 + US$) · Coefficient · Standard Error · Countries · Observations · Years | page module | V:348-352 | not in nav; conditional |
| MAIN-UI-284 | Validation | caption/text block | "A negative coefficient means more aid has gone with fewer deaths. ..." | page module | V:353-354 | not in nav; conditional |

### 6. Defined in code but never rendered on main (no caller from any page)

Verified by a whole-repo call search over app.py, views/*.py, model_section.py, paths_ui.py, theme.py, scenarios.py (tests excluded). Callers in tests are noted.

| ID | Page | Kind | Name as shown | Rendering function | file:line | Shown? |
|---|---|---|---|---|---|---|
| MAIN-UI-285 | (Dashboard, removed) | table | "What Each Service Loses" service-by-service HTML table (see §C) | ms._service_table_html | ms:1426-1490 | not shown: never called (only tests/test_hiv.py:65, test_malaria.py:142, test_minor.py:85, test_announcement.py:115); call removed in commit aea3e72 |
| MAIN-UI-286 | (Dashboard, removed) | control | Year picker for the service table: former st.selectbox "Year", key `m_svc_year`, options 2026…2030 + "Average 2026-2030" (AVG_LABEL) | ms._year_rows / AVG_LABEL | ms:1508, ms:1516-1532 | not shown: selectbox deleted in aea3e72; _year_rows only used by tests/test_announcement.py:163 |
| MAIN-UI-287 | (Dashboard, removed) | chart | "Coverage of Each Service" / sub "Share of People in Need Covered, %" (one line per service, 2025 (now) → 2030) | ms._coverage_path_fig | ms:1535-1561 | not shown: never called (tests/test_announcement.py:166 only) |
| MAIN-UI-288 | (Dashboard, removed) | chart | "Coverage Lost, by Service" / sub "Percentage Points; Coverage Before → After" (horizontal bars) | ms._coverage_fig | ms:1638-1658 | not shown: never called |
| MAIN-UI-289 | (Dashboard, removed) | chart | "Extra Deaths as More Aid Is Cut" (traces Range Across Parameter Values, Even Cut Across All Donors, This Scenario; axes "Share of This Bucket's Aid Lost" / "Extra Deaths Over 5 Years") | ms._dose_fig (+ ms._dose ms:107, ms._scenario_path ms:116) | ms:1661-1704 | not shown: never called |
| MAIN-UI-290 | (Dashboard, removed) | chart | "Extra Deaths Each Year" / sub "All Four Diseases, 2026-2030" (stacked by disease) | ms._path_fig | ms:1707-1718 | not shown: never called |
| MAIN-UI-291 | (Dashboard, removed) | heading | "What Every US$1 Million Cut Does, by Disease" (CARDS_TITLE) | — | ms:1217 | not shown: subheader removed in aea3e72 |
| MAIN-UI-292 | (Dashboard, removed) | card/metric | Four per-$1M disease cards (HIV/TB/Malaria/Immunization): "People Losing the Main Service", "Coverage Drop (Percentage Points)", foot "Spread across all {disease} services in proportion to current aid" | ms._per_million_cards -> ms._cards_html -> ms._card_html (data ms._card_runs -> hm.per_million_card) | ms:1222-1272 | not shown: _per_million_cards and _cards_html never called (tests/test_hiv.py:91,109 only) |
| MAIN-UI-293 | (Dashboard, removed) | download | "Download Country Brief" button (former key `m_brief`) and its HTML: "{country}: What a Funding Cut Does", sections "The Headline", "What Every US$1 Million Cut Does, by Disease", "Coverage and Deaths"; card line "Extra Deaths Over 5 Years" | ms._brief_html | ms:2261-2314; flag SHOW_BRIEF = False ms:49 | not shown: no st.download_button exists on main (removed in aea3e72); SHOW_BRIEF is referenced nowhere |
| MAIN-UI-294 | (Methods/Dashboard, removed) | heading | "#### Does This Match Published Estimates?" + st.table index "Study"; columns What It Covers · Published · This Model (Current Scenario) | ms._published_estimates | ms:2225-2255 | not shown: never called |
| MAIN-UI-295 | (none) | caption/text block | Cross-check summary sentence "Panel regressions across up to N countries ... imply about N extra deaths over 5 years ..." | ms._crosscheck_summary | ms:2190-2206 | not shown: never called |
| MAIN-UI-296 | (Dashboard, removed) | caption/text block | Biggest-risk lines "Biggest risk: ...", "Sharpest drop: ...", "Hardest-hit service: ..." | ms.risk_lines | ms:970-996 | not shown: never called (tests/test_announcement.py:118,120); Methods M:260 still documents it |
| MAIN-UI-297 | (none) | caption/text block | Deaths after 2030 tooltip / range text (REENGAGE_TIP, AFTER_2030_PARTS) | ms.after_2030_help, ms.reengage_range_text | ms:1092-1118 | not shown: never called |
| MAIN-UI-298 | (none) | caption/text block | "Assumes the cut is sustained for five years." / "Follows {country}'s MOU schedule, 2026-2030." | ms.deaths_basis_text | ms:1156-1162 | not shown: never called |
| MAIN-UI-299 | (none) | caption/text block | Fiscal sentence "{country} loses about $X/yr in aid; under ... the government fills ..." | ms._fiscal_sentence | ms:1772-1783 | not shown: never called |
| MAIN-UI-300 | (none) | caption/text block | "Inputs: aid 2021-23 average; coverage ...; applied to 2026-2030 without projection." | ms.inputs_years_line | ms:1930-1942 | not shown: never called |
| MAIN-UI-301 | (none) | caption/text block | systems_note "X% of lost systems money ... is counted as lost services" | ms.systems_note | ms:1142-1146 | not shown: never called |
| MAIN-UI-302 | (none) | caption/text block | Response kicker ("Government Replaces Up to X%", ...) | ms.response_kicker | ms:860-866 | not shown: never called |
| MAIN-UI-303 | (none) | caption/text block | care_breakdown (people losing a service, all lines) + CARE_TIP | ms.care_breakdown, ms:835 | ms:839-845 | not shown: never called |
| MAIN-UI-304 | (none) | caption/text block | PRESET_SHORT one-line preset descriptions | — | ms:50-66 | not shown: constant never referenced |

### 7. Presets and option lists

### Scenario presets (scenarios.PRESETS, scenarios.py:20-55; UI_PRESETS scenarios.py:59; display names scenarios.py:223)

| ID | Page | Kind | Name as shown | Rendering function | file:line | Shown? |
|---|---|---|---|---|---|---|
| MAIN-UI-305 | Dashboard / All Countries / Validation | preset | "Announced Donor Cuts" (key "Announced donor cuts"; default = UI_PRESETS[0]) | Donor Scenario selectbox | scn:44-53, 58-59 | always offered |
| MAIN-UI-306 | Dashboard / All Countries / Validation | preset | "Custom" | Donor Scenario selectbox | scn:54, 59 | always offered |
| MAIN-UI-307 | — | preset | "US Bilateral Exit + Multilateral Withdrawals" (key "Full US exit") | — | scn:21-25, 223 | not shown in any dropdown (not in UI_PRESETS); appears only as a row of the Validation deaths table and in Validation "Published Estimates" (page not in nav) |
| MAIN-UI-308 | — | preset | "America First MOUs" | — | scn:26-31 | not offered (not in UI_PRESETS); MOU code paths unreachable |
| MAIN-UI-309 | — | preset | "IHME 2025 Preliminary Estimates" | — | scn:32-35 | not offered |
| MAIN-UI-310 | — | preset | "Total-Aid Cuts (OECD) Applied to Health Aid" (key "OECD-reported 2025 aid cuts") | — | scn:36-38, 223 | not offered |
| MAIN-UI-311 | — | preset | "Global Fund & Gavi Shortfalls" | — | scn:39-42 | not offered (its two sliders unreachable) |
| MAIN-UI-312 | — | preset | "Combined Retreat" | — | scn:43 | not offered |
| MAIN-UI-313 | Dashboard | preset | Scenario B options: "Same as Scenario A", "Announced Donor Cuts" | ms._controls | ms:622-625 | conditional: compare toggle on |

### Option lists (displayed form)

- **Donor Scenario** (m_preset, ac_preset, v_preset): Announced Donor Cuts · Custom.
- **Donor Scenario (B)** (mb_preset): Same as Scenario A · Announced Donor Cuts.
- **How Funding Changes** (m_path_shape; scn.PATH_SHAPES scn:263): Sudden (Default) · Linear Phase-Out · Front-Loaded · Back-Loaded · S-Curve · Custom.
- **Budget Increase Shape** (m_gov_shape; scn.GOV_SHAPES scn:264): Steady · Fast Start · Slow Start · Custom.
- **Government Response** (m_mode; ms.GOV_MODES ms:45-46 minus "max"): No Government Replacement · Replace a Set Share · Gradual Budget Increase.
- **Government Response (B)** (mb_mode): No Government Replacement · Replace a Set Share · As Much as Fiscal Space Allows (default) · Gradual Budget Increase.
- **Fiscal-Space Ceiling** (m_effort; ms.CEILINGS ms:67): Strong Year (75th Percentile Growth) · Best Years (90th Percentile Growth).
- **Where Replacement Money Goes** / **(B)** (m_alloc / mb_alloc; ms.ALLOCS ms:70): Pro-Rata to What Was Cut · Hypothetical Best Case (Triage).
- **Show As** (c2_view): US$ Total · US$ per Person · Share of Total (%).
- **Show As** (c3b_view): US$ Total · Share of Total (%).
- **Health Category** (c1_hfa; HFA_LABELS D:53-65): All Focus Areas · HIV/AIDS · Malaria · Tuberculosis · Reproductive & Maternal Health · Newborn & Child Health (Incl. Vaccines) · Other Infectious Diseases · Non-Communicable Diseases · Health Systems Strengthening · Other (Focus Area Known, Not in List) · Unallocated (No Focus Area Info).
- **Program Area** (c1_pa_{hfa}): All Program Areas + the focus area's columns labelled by PA_LABELS (D:68-77), title-cased (e.g. Treatment, Prevention, Prevention of Mother-to-Child Transmission, Orphans & Vulnerable Children, Care & Support, Counseling & Testing, Drug Resistance, Diagnosis, Bednets, Indoor Spraying, Other Vector Control, Community Outreach, Family Planning, Maternal Health, Nutrition, Vaccines, Ebola, Zika, COVID-19, Tobacco, Mental Health, Pandemic Preparedness, HSS - Other, HSS - Human Resources, HSS - ME, Human Resources, Other), sorted alphabetically by raw label.
- **Break Down** (c3b_brk): All Focus Areas · HIV/AIDS · Malaria · Tuberculosis · Reproductive & Maternal Health · Newborn & Child Health (Incl. Vaccines) · Other Infectious Diseases · Non-Communicable Diseases · Health Systems Strengthening.
- **Channels Drawn as NGO / Foundation (Lighter Shade)** (c1_ngo; CHANNEL_LABELS D:43-51): US NGOs (NGO) · International NGOs (INTLNGO) · US Foundations (US_FOUND) · Gates Foundation (Direct) (GATES) · Gavi (GAVI) · Global Fund (GFATM) · CEPI (CEPI) · WHO (WHO) · PAHO (PAHO) · UNICEF (UNICEF) · UNFPA (UNFPA) · UNAIDS (UNAIDS) · Unitaid (UNITAID) · World Bank (IDA) (WB_IDA) · World Bank (IBRD) (WB_IBRD) · World Bank (WB) · African Development Bank (AfDB) · Asian Development Bank (AsDB) · Inter-American Development Bank (IDB) · European Commission (EC) · European Economic Area (EEA) · US Bilateral (USAID/State/Etc.) (BIL_USA).
- **Year** (c4_year_{iso3}): IMF revenue/spending years, newest first.
- **Country** (country_sel, v_country): 71 countries (country_lists.ALLOWED_COUNTRIES / dropdown_countries).
- **Custom channel sliders**: Global Fund · Gavi · WHO · UNICEF.
- **Custom donor rows**: the 14 hm.SOURCE_GROUPS listed in §2.

### A. Coverage / service graphs (service coverage change or people losing services)

Result tables come from `health_model.run_country` (`res["lines"]`, one row per service line; per-year columns built at health_model.py:1315-1318) and `health_model.run_all` (one row per country, health_model.py:1712-1730).

Reachable (rendered on a navigated page):

1. **Dashboard, "Service Coverage, Year by Year" small multiples**: `ms._service_grid` ms:1625 -> `ms._service_paths` ms:1567 -> `ms._service_fig` ms:1604; called from `ms._country_results` ms:1077. Reads `res["lines"]` via `_service_rows` (ms:1381): `cov0`, `cov_drop_pp_2026` … `cov_drop_pp_2030` (years found by `_model_years` ms:1511 from columns starting `cov_drop_pp_`), `need` (hover "people covered" = coverage × need), `unit_cost`, `line`, `bucket`; the `cov_ok` filter uses `need`, `cov0` and the 5-year average `cov_drop_pp`. Excludes `hiv_ovc` and LINKED `hiv_care_ct`.
2. **Dashboard, coverage-drop overview table** (st.html, directly under the charts): `ms._drop_overview_html` ms:1584, called ms:1078. Same `_service_paths` data: `cov0` and `cov_drop_pp_<year>`; reports today → last year and the drop.
3. **Dashboard story lede, "Treatment Lost Each Year" / "Prevention Lost Each Year"** (Custom preset only): `ms.care_split` ms:848, used by `ms.story_lede` ms:935-947. Reads `units_lost` (2026-2030 average) for TREATMENT_LINES (hiv_art, hiv_pmtct, tb_ds, tb_dr, mal_cm) and PREVENTION_LINES (mal_itn, mal_irs, imm).
4. **Dashboard story headline "... about N people a year would lose a service"** (Custom): `ms.people_lost` ms:1149 = sum of `units_lost` excluding hiv_prev and hiv_ovc; ms:928.
5. **Dashboard outcome panel pills "People Losing a Service per Year" and "People Kept in Services vs Sudden Cut With No Response" + sentence** (panel expanded only): `pu.outcome_panel` pu:236-277 with `people_lost(base)` / `people_lost(res)` from ms:765-766 (`units_lost`).
6. **Dashboard comparison pills "People Losing a Service (per Year)" and sentence "Scenario B keeps services for about N ..."** (compare toggle on): `ms._headline_items` ms:1176, `ms._comparison` ms:1198-1200 (`units_lost` via people_lost).
7. **Dashboard "Government replacement ... keeps services for about N people a year"**: ms:1055-1058 (`people_lost(res0) - people_lost(res)`).
8. **All Countries pills** "People Losing a Service per Year", "HIV and TB Treatment Lost per Year", "Children Missing Vaccines per Year": ms:2049-2063, read run_all columns `people_lost`, `people_lost_HIV`, `people_lost_TB`, `people_lost_Immunization` (each = sum of line `units_lost`, average 2026-2030, excluding hiv_prev/hiv_ovc).
9. **All Countries map** "People Losing a Service per 100,000": `ms._world_map` ms:2149, reads `people_per_100k` = `people_lost` / `pop` × 1e5 (ms:2064), hover `people_lost`, `gross_loss_usd`, `loss_pct_ghes`.
10. **All Countries scatter** "Budget Exposure vs. Services Lost": ms:2073-2120, reads `people_per_100k`, `loss_pct_ghes` (×100), `net_loss_usd`, `people_lost`.
11. **All Countries bars** "Most People Losing a Service, per Year": ms:2121-2145, reads `people_lost_HIV`, `people_lost_TB`, `people_lost_Malaria`, `people_lost_Immunization`, `people_lost`.

Not reachable (code exists, never called): `ms._service_table_html` ms:1426 (reads `base_usd`, `net_loss_usd`, `unit_cost`, `units_lost`, `units_lost_5y`, `cov0`, `cov_drop_pp`, `cov_source`; per-year via `ms._year_rows` ms:1516 which swaps in `net_loss_<year>`, `units_lost_<year>`, `cov_drop_pp_<year>` and `res["years"].gap_usd`); `ms._coverage_path_fig` ms:1535 (`cov0`, `cov_drop_pp_<year>`); `ms._coverage_fig` ms:1638 (`cov0`, `after`/`drop` from average `cov_drop_pp`, `cov_source`); per-$1M cards `ms._per_million_cards` ms:1229 (`people`, `cov_drop_pp` from hm.per_million_card); `ms.risk_lines` "Hardest-hit service" ms:990-995 (`drop`); `ms.care_breakdown` ms:839. **No reachable chart or table reads `units_lost_<year>` or `net_loss_<year>`**; the reachable per-year display is coverage only (`cov_drop_pp_<year>`).

### B. Deaths / lives displays

On the three navigated pages (Dashboard, All Countries, Methods) **no number of deaths, lives saved or lives lost is displayed**. The model still computes deaths on every run (`hm.run_country` → lines/buckets `deaths_y1`, `deaths_5y`, `deaths_5y_lo/hi`; totals; `committed.after_2030`; `path`), and run_all carries `deaths_5y`, `deaths_5y_<bucket>`, `deaths_after_2030*` columns (health_model.py:1712-1723), but nothing on those pages reads them. Comment at ms:618: "no setting: the dashboard shows coverage, not deaths".

| Item | Function | file:line | Reachable from a page? |
|---|---|---|---|
| "Hypothetical Best Case (Triage)" allocation refills services in order of the model's deaths per dollar (L-30) | ms._controls radio `m_alloc` / `mb_alloc` → hm | ms:68-70, 613-617 | Yes (Dashboard, Advanced): computed, not displayed |
| Validation deaths table "Model: Extra Deaths Over 5 Years, All {n} Countries" (precomputed `deaths_5y_<bucket>`, `deaths_5y`, hm.total_range) | page module | V:56-69 | No: Validation page not in navigation |
| Validation "Published Estimates" table (Cavalcanti, UNAIDS, Optima, Gavi; model `deaths_5y`, `deaths_5y_HIV`, per-year bucket deaths, `ms.deaths_per_child_immunised`) | page module, ms.deaths_per_child_immunised ms:2209-2222 | V:74-112 | No: page not in navigation |
| Validation chart "Extra Deaths by Method" (bucket `deaths_5y`, `deaths_5y_lo/hi`; hm.poisson_projection, hm.lancet_projection) | page module | V:220-250 | No: page not in navigation |
| Validation "**Reading:**" sentence and "Estimates by Method" table (deaths by method) | _reading, page module | V:258-313 | No |
| Validation "Our Poisson Regressions" table (outcomes TB Deaths, Under-5 Deaths, Child Malaria Deaths (Africa)) | page module | V:343-354 | No |
| Validation malaria pills "Baseline Malaria Deaths, Dashboard Countries", "WHO Global Malaria Deaths, 2024" (baseline burden, not lives lost) and Pakistan caption (baseline deaths) | page module | V:176-182, 195-206 | No |
| Validation caption "· Death Rates Held Constant" | page module | V:214 | No |
| Methods "Regression Estimates" table includes Poisson death regressions (Poisson Tb / U5 / Malaria, outcomes tb_deaths, u5_deaths, mal_child_deaths) | page module | M:672-682 | Yes (Methods, Parameters tab): coefficients only, no death counts |
| Methods "Every Model Parameter" / "Values That Are Assumptions" tables list mortality parameters (art_hazard_mult, tb_cfr_*, imm_deaths_per_child_ref, mal_vc_eff, art_reengage, ...) | page module | M:623-626, 670-671 | Yes: parameter values only |
| `ms._dose_fig` "Extra Deaths as More Aid Is Cut" + data `ms._dose` / `ms._scenario_path` | ms._dose_fig | ms:1661-1704; ms:106-129 | No: never called |
| `ms._path_fig` "Extra Deaths Each Year" (`res["path"]`) | ms._path_fig | ms:1707-1718 | No: never called |
| `ms._published_estimates` "Does This Match Published Estimates?" (`deaths_5y`, `deaths_5y_HIV`) | ms._published_estimates | ms:2225-2255 | No: never called |
| `ms._crosscheck_summary` ("... imply about N extra deaths over 5 years ..."; hm.statistical_crosscheck) | ms._crosscheck_summary | ms:2190-2206 | No: never called |
| Per-$1M cards (`hm.per_million_card` computes `deaths_5y`; CARD_FOOT_TIP ms:1215 "...divided by extra deaths"; NO_DEATHS_REASON ms:1219) | ms._card_runs / _per_million_cards | ms:1222-1251 | No: never called |
| Country brief "Extra Deaths Over 5 Years", "Coverage and Deaths" | ms._brief_html | ms:2265-2309 | No: never called; SHOW_BRIEF = False ms:49 unreferenced |
| Deaths after 2030 text (REENGAGE_TIP, AFTER_2030_PARTS, after_2030_help, reengage_range_text) | ms.after_2030_help, ms.reengage_range_text | ms:1092-1118 | No: never called |
| "5-year deaths" basis text | ms.deaths_basis_text | ms:1156-1162 | No: never called |
| CAUSE_PHRASE (causes of death phrases), MAIN_LINE | constants | ms:815-816, ms:40 | No: unreferenced |
| `ms.deaths_per_child_immunised` | function | ms:2209 | Only from Validation (not in nav) and the uncalled _published_estimates |

### C. Service-by-service table

- **Function:** `model_section._service_table_html(rows, country_name="", T=None, gains=None)`, ms:1426-1490, helpers `_service_rows` ms:1381, `_gain_rows` ms:1499, `_other_aid_sub` ms:1493, `care_ct_tip` ms:1375, `cov_pair` ms:1420, `_pts` ms:1404. Title it carried: "What Each Service Loses" (docstring ms:1428; Methods M:262).
- **Rows** (one per service, grouped by disease with gap rows; order LINE_ORDER ms:1363): HIV Treatment (antiretroviral therapy (ART)), HIV Testing & Care (counselling, testing, care & support), Mother-to-Child Transmission (prevention (PMTCT)), HIV Prevention (PrEP, VMMC, condoms, key populations), TB Treatment (case finding & treatment), Drug-Resistant TB (second-line treatment), Bednets (insecticide-treated nets & other vector control), Indoor Spraying (indoor residual spraying), Malaria Treatment (testing & treatment), Routine Immunization (vaccines + delivery) (LINE_SHORT ms:1350-1360; orphans row dropped); per-disease "Aid to {disease} rises by $X in this scenario; gains aren't modelled." note rows; "Other Aid" row (grey sub "orphan support; systems money not cutting services"); "Total" row.
- **Columns** (ms:1434-1435): "Service" · "Donor Aid Now" (sub "per year") · "Aid Lost" (sub "per year, after government replacement") · "Cost per Person" · "People Losing Service, per Year" (with grey "{N} over 5 years" or the ART full-cost-equivalent note) · "Coverage" ("x% → y%", source, "−n pts"; "No Single Target Group" for HIV prevention; "Not Modelled" otherwise).
- **Year picker:** none on main. The helper `_year_rows(rows, res, T, year)` ms:1516 and `AVG_LABEL = "Average 2026-2030"` ms:1508 remain; the former `st.selectbox("Year", [2026…2030, "Average 2026-2030"], key="m_svc_year")` (default 2030) and the `st.subheader("What Each Service Loses", help=...)` were deleted in commit aea3e72 ("Remove The Numbers, the per-$1M cards, the service table and year picker").
- **Where rendered:** nowhere on main. Only called from tests (tests/test_hiv.py:65, tests/test_malaria.py:142, tests/test_minor.py:85, tests/test_announcement.py:115). Its replacement on main is the per-service small multiples + `_drop_overview_html` under "Service Coverage, Year by Year" (ms:1076-1080).

### Counts per Kind

| Kind | Count (all rows) |
|---|---|
| section | 35 |
| heading | 55 |
| chart | 22 |
| table | 26 |
| card/metric | 37 |
| control | 24 |
| preset | 9 |
| tooltip-bearing control | 20 |
| caption/text block | 75 |
| download | 1 |
| expander | 3 |
| tab | 6 |
| **Total rows** | **313** |

Per page (rows by Kind):

| Page | section | heading | chart | table | card/metric | control | preset | tooltip-bearing control | caption/text block | download | expander | tab | Total |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| (Dashboard, removed) | 0 | 1 | 4 | 1 | 1 | 1 | 0 | 0 | 1 | 1 | 0 | 0 | 10 |
| (Methods/Dashboard, removed) | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| (none) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 9 | 0 | 0 | 0 | 9 |
| All Countries | 0 | 2 | 3 | 0 | 4 | 0 | 0 | 2 | 3 | 0 | 0 | 0 | 14 |
| App shell | 2 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 4 |
| Dashboard | 5 | 12 | 14 | 1 | 29 | 21 | 1 | 17 | 33 | 0 | 3 | 0 | 136 |
| Dashboard / All Countries / Validation | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 2 |
| Methods | 21 | 31 | 0 | 17 | 0 | 0 | 0 | 0 | 13 | 0 | 0 | 6 | 88 |
| Validation (not in nav) | 7 | 8 | 1 | 7 | 3 | 1 | 0 | 1 | 15 | 0 | 0 | 0 | 43 |
| — | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 0 | 0 | 0 | 0 | 0 | 6 |

Notes: card/metric rows that cover a repeated pill (×2 for Scenario A/B, ×5 year sliders counted once as one control row) are one row each. Charts drawn once per service (small multiples) are one row. Rows in §6 and §7 'not offered' presets are code that is not rendered on main.


## 3. Dashboard UI, branch tomato


Read-only inventory of every on-screen element, built from the source (no app run). Line numbers are for the checkout as it stood when this was written.

Conventions:
- **Name as shown** is the displayed form. `title_case` (model_section.py:203) is applied where the code calls it: every figure passed through `chart()` (model_section.py:246) gets its title, legend names, axis titles, colour-bar titles and annotations title-cased by `tc_fig` (model_section.py:228). `pill_row` (model_section.py:258) title-cases its labels and notes; `th.pills_html` called directly does **not**. `st.subheader`, `st.title`, `th.section_header` and widget labels are shown exactly as written. `{country}` = selected country name; `{yr}` = a year chosen or found in data.
- Every pill (`th.pills_html`, theme.py:517) carries a hover tooltip (`title=`). Every `th.section_header(..., help=...)` shows an info-icon tooltip. `st.subheader(..., help=...)` shows Streamlit's help icon.
- Every `chart()` call can add a grey "Note: ... Source: ..." line under the chart (theme.source_html, theme.py:125); listed in the chart row.
- Session keys starting `m_`, `mb_`, `c1_`, `c2_`, `c3b_`, `c4_year_` are persisted across pages by app.py:14-19 (except `m_params`, `m_custom_tbl`, `mb_custom_tbl`).

### Pages

| Page | File | In navigation | Notes |
|---|---|---|---|
| Dashboard (default) | views/1_Dashboard.py | yes (theme.py:480, icon :material/dashboard:) | |
| All Countries | views/2_All_Countries.py | yes (theme.py:481, :material/travel_explore:) | |
| Validation & Benchmarks | views/3_Validation.py | yes (theme.py:482, :material/fact_check:) | |
| Methods | views/4_Methods.py | yes (theme.py:483, :material/menu_book:) | |
| (none kept outside navigation) | | | No `pages/` folder; only app.py, theme.py, model_section.py, paths_ui.py and views/*.py import streamlit. The "Country Brief" HTML page (`_brief_html`, model_section.py:1985) exists in code but its download button is switched off (SHOW_BRIEF = False, model_section.py:49). |

Navigation: `st.navigation(..., position="top")` app.py:20-22; page config title "Health Financing", icon :material/monitor_heart:, layout wide, sidebar collapsed (theme.py:488).

---

### Page 1: Dashboard (views/1_Dashboard.py)

| ID | Page | Kind | Name as shown | Rendering function | file:line | Shown? |
|---|---|---|---|---|---|---|
| TOM-UI-001 | Dashboard | caption/text block | Error: "No `country_data/` folder found. Run `python prepare_data.py <path to the IHME DAH CSV>` first." (st.error, then st.stop) | page body | views/1_Dashboard.py:247 | conditional: country_data/ missing |
| TOM-UI-002 | Dashboard | caption/text block | Warning: "These data folders are missing (or empty) next to this script, so part of the page won't show: ..." (st.warning) | page body | views/1_Dashboard.py:260 | conditional: any of spending_data/_index.csv, cofog_all/, macro_data/, revenue_data/ missing |
| TOM-UI-003 | Dashboard | section | Sticky country header (container key `hdr`) | page body | views/1_Dashboard.py:269 | always |
| TOM-UI-004 | Dashboard | control | Country (selectbox, key `country_sel`, shared via `sel_iso3`; options = allowed countries, shown by name; default Kenya) | th.shared_select | views/1_Dashboard.py:273 (theme.py:493) | always |
| TOM-UI-005 | Dashboard | heading | {country} (big country name) + "All dollar figures in constant 2023 US$ (except MOU amounts)" | page body (HTML) | views/1_Dashboard.py:305 | always |
| TOM-UI-006 | Dashboard | caption/text block | Inputs years line: "Inputs: aid 2021-23 average; coverage {yrs} (malaria: MAP {yr}); government health spending 2023; applied to 2026-2030 without projection." | ms.inputs_years_line | views/1_Dashboard.py:308 (model_section.py:1636) | always |
| TOM-UI-007 | Dashboard | card/metric | Region (pill; tooltip "World Bank region (IHME DAH database)") | th.pills_html | views/1_Dashboard.py:294, 309 | always (value n/a if no profile) |
| TOM-UI-008 | Dashboard | card/metric | Income Group (pill) | th.pills_html | views/1_Dashboard.py:295 | always |
| TOM-UI-009 | Dashboard | card/metric | US MOU (pill; values "MOU Signed" / "No MOU") | th.pills_html | views/1_Dashboard.py:296 | always |
| TOM-UI-010 | Dashboard | card/metric | GDP, {yr} (pill) | th.pills_html | views/1_Dashboard.py:297 | always ("GDP" and n/a when no macro data) |
| TOM-UI-011 | Dashboard | card/metric | Population, {yr} (pill) | th.pills_html | views/1_Dashboard.py:300 | always |
| TOM-UI-012 | Dashboard | section | Story lede (kicker, headline, dek, big numbers); filled after the scenario bar runs | ms.story_lede | views/1_Dashboard.py:313-316 (model_section.py:698) | always |
| TOM-UI-013 | Dashboard | caption/text block | Lede kicker: "Funding-Cut Scenario · {scenario title} · {Sudden Cut or path name} · {response kicker}" or for MOU "America First MOUs · Follows MOU Schedule · {response kicker}" | ms.story_lede | model_section.py:703-704 | always |
| TOM-UI-014 | Dashboard | caption/text block | Link "Change Scenario ↓" (anchor #change-scenario) | ms.story_lede | model_section.py:707 | always |
| TOM-UI-015 | Dashboard | heading | Lede headline (one of: "... receives no recorded HIV, TB, malaria or vaccine aid"; "... would lose almost no aid ..."; "... could keep services running if the government fills the gap"; "... would lose {$} a year in health aid"; "{phrase}, the model estimates about {N} more deaths in {country} in 2026-2030, even if the government replaces {x%} of the lost aid"; "{phrase}, with nothing to replace the money, the model estimates about {N} more deaths in {country} in 2026-2030") | ms.story_lede | model_section.py:709, 718, 721, 725, 730-734 | always (text depends on results) |
| TOM-UI-016 | Dashboard | caption/text block | Lede dek ("Most / The largest share would come from {cause}. ..." etc.) | ms.story_lede | model_section.py:710, 719, 722, 726, 738-744 | always |
| TOM-UI-017 | Dashboard | card/metric | Health Aid Lost Each Year (big number; note "{x%} of aid for these four diseases") | ms.story_lede | model_section.py:754 | conditional: country has modelled aid |
| TOM-UI-018 | Dashboard | card/metric | Treatment Lost Each Year (big number; note top 2 parts e.g. "452K people who stop ART* · ..."; tooltip TREATMENT_TIP) | ms.story_lede / care_split | model_section.py:756 (639) | conditional: country has modelled aid |
| TOM-UI-019 | Dashboard | card/metric | Prevention Lost Each Year (big number; tooltip PREVENTION_TIP) | ms.story_lede / care_split | model_section.py:757 | conditional: country has modelled aid |
| TOM-UI-020 | Dashboard | card/metric | Extra Deaths, 2026-2030 (highlighted big number; note "range {lo} to {hi} · +{N} more in 2031-2035 (assumption-driven)"; tooltip after_2030_help) | ms.story_lede | model_section.py:758-762 | conditional: country has modelled aid |
| TOM-UI-021 | Dashboard | section | Scenario bar (container key `model_controls`) | ms._controls via ms.scenario_bar | views/1_Dashboard.py:314 (model_section.py:408, 544) | always |
| TOM-UI-022 | Dashboard | heading | Change the Scenario (kicker, id `change-scenario`) | ms._controls | model_section.py:409 | always |
| TOM-UI-023 | Dashboard | tooltip-bearing control | Donor Scenario (selectbox, key `m_preset`, shared via `sel_preset`; tooltip = full preset description) | ms.donor_scenario_select | model_section.py:413 (375-388, 380) | always |
| TOM-UI-024 | Dashboard | preset | Donor Scenario options: US Bilateral Exit + Multilateral Withdrawals; America First MOUs (only if MOU group A; shown as "America First MOUs (MOU signed; no funding data available.)" for group B, absent for group C); IHME 2025 Preliminary Estimates; Total-Aid Cuts (OECD) Applied to Health Aid; Global Fund & Gavi Shortfalls; Combined Retreat; Custom | ms.preset_choices | model_section.py:349-359 (scenarios.py:20-46, 231) | always |
| TOM-UI-025 | Dashboard | caption/text block | MOU notice ("America First MOUs: MOU signed; no funding data available." or "{country}: no MOU funding data; showing US Bilateral Exit + Multilateral Withdrawals.") | ms._controls / ms.mou_fallback | model_section.py:414-415 (362-372) | conditional: MOU selected for a country without schedule data |
| TOM-UI-026 | Dashboard | caption/text block | Preset short description (PRESET_SHORT) or MOU schedule text | ms._controls | model_section.py:417-418 (50-64) | always |
| TOM-UI-027 | Dashboard | tooltip-bearing control | Gavi Funding Cut (%) (slider 0-50, default 15, key `m_gavi_cut`; reference marks "~15%: fall vs 2021-23 spending (our estimate)", "24%: gap vs Gavi's US$11.9B target") | ms._shortfall_sliders | model_section.py:318-320 (296) | conditional: preset = Global Fund & Gavi Shortfalls |
| TOM-UI-028 | Dashboard | tooltip-bearing control | Global Fund Funding Cut (%) (slider 0-50, default 20, key `m_gf_cut`; 4 reference marks) | ms._shortfall_sliders | model_section.py:318-320 (303) | conditional: preset = Global Fund & Gavi Shortfalls |
| TOM-UI-029 | Dashboard | expander | Cuts by Donor and Channel (expanded) | ms._preset_options | model_section.py:329 | conditional: preset = Custom |
| TOM-UI-030 | Dashboard | table | Custom cuts data editor (key `m_custom_tbl`): columns Donor, Bilateral & NGO Cut %, Via Multilaterals Cut %; rows United States, United Kingdom, Germany, France, Japan, Canada, Netherlands, Nordics, Other DAC governments, Gates Foundation, Other private, Development-bank lending, Non-DAC governments, Other / unallocable | ms._preset_options (st.data_editor) | model_section.py:330-335 | conditional: preset = Custom |
| TOM-UI-031 | Dashboard | tooltip-bearing control | Global Fund Channel Cut (%) / Gavi Channel Cut (%) / WHO Channel Cut (%) / UNICEF Channel Cut (%) (4 sliders 0-100 step 5, keys `m_ch_Global Fund`, `m_ch_Gavi`, `m_ch_WHO`, `m_ch_UNICEF`) | ms._preset_options | model_section.py:338-341 | conditional: preset = Custom |
| TOM-UI-032 | Dashboard | heading | "Follows {country}'s MOU schedule" (kicker; tooltip "Schedule ends {yr}; ..." when schedule ends early) | ms._controls | model_section.py:421-427 | conditional: preset = America First MOUs |
| TOM-UI-033 | Dashboard | chart | MOU schedule mini-chart (no title; red line of yearly US bilateral cut %, annotation "Held from {yr}") | paths_ui.mou_schedule_chart | model_section.py:428 (paths_ui.py:101-115) | conditional: preset = America First MOUs |
| TOM-UI-034 | Dashboard | tooltip-bearing control | How Funding Changes (selectbox, key `m_path_shape`) | paths_ui.path_selector | model_section.py:431 (paths_ui.py:95) | conditional: preset is not America First MOUs |
| TOM-UI-035 | Dashboard | preset | How Funding Changes options: Sudden (Default); Linear Phase-Out; Front-Loaded; Back-Loaded; S-Curve; Custom | paths_ui.path_selector | paths_ui.py:88 (scenarios.py:271) | as above |
| TOM-UI-036 | Dashboard | tooltip-bearing control | Government Response (selectbox, key `m_mode`; tooltip includes backfill regression sentence) | ms._controls | model_section.py:435-438 | always |
| TOM-UI-037 | Dashboard | preset | Government Response options: No Government Replacement; Replace a Set Share; As Much as Fiscal Space Allows; Gradual Budget Increase | ms._controls | model_section.py:45-46 | always |
| TOM-UI-038 | Dashboard | control | Share of Lost Aid Replaced (%) (slider 0-100, default 25, step 5, key `m_theta`) | ms._controls | model_section.py:441 | conditional: response = Replace a Set Share |
| TOM-UI-039 | Dashboard | control | Budget Increase Shape (selectbox, key `m_gov_shape`; options Steady, Fast Start, Slow Start, Custom) | paths_ui.gradual_controls | paths_ui.py:133 (scenarios.py:272) | conditional: response = Gradual Budget Increase and government spending known |
| TOM-UI-040 | Dashboard | tooltip-bearing control | Points per Year (number_input, key `m_gov_pts`, default 0.5) | paths_ui.gradual_controls | paths_ui.py:135 | conditional: as above |
| TOM-UI-041 | Dashboard | caption/text block | "No data on this government's total spending, so a budget increase can't be modelled." | ms._controls | model_section.py:448 | conditional: Gradual Budget Increase and no government spending data |
| TOM-UI-042 | Dashboard | control | Advanced (popover, icon tune) | ms._controls | model_section.py:452 | always |
| TOM-UI-043 | Dashboard | tooltip-bearing control | Fiscal-Space Ceiling (radio, key `m_effort`; options Strong Year (75th Percentile Growth), Best Years (90th Percentile Growth)) | ms._controls | model_section.py:454 | always (in Advanced; disabled when response = none) |
| TOM-UI-044 | Dashboard | tooltip-bearing control | Where Replacement Money Goes (radio, key `m_alloc`; options Pro-Rata to What Was Cut, Hypothetical Best Case (Triage)) | ms._controls | model_section.py:459 | always (in Advanced; disabled when response = none) |
| TOM-UI-045 | Dashboard | control | Cap Replacement at Fiscal Space (checkbox, key `m_cap`, default on) | ms._controls | model_section.py:464 | always (in Advanced; disabled for none / max) |
| TOM-UI-046 | Dashboard | tooltip-bearing control | Account for Already-Changing Death Rates (toggle, key `m_trend`, default on) | ms._controls | model_section.py:466 | always (in Advanced) |
| TOM-UI-047 | Dashboard | control | Compare with a Second Scenario (toggle, key `m_compare`, default off) | ms._controls | model_section.py:475 | always (in Advanced) |
| TOM-UI-048 | Dashboard | control | Donor Scenario (B) (selectbox, key `mb_preset`; options Same as Scenario A + the six precomputed presets, MOU only for group A) | ms._controls | model_section.py:476-479 | conditional: compare toggle on |
| TOM-UI-049 | Dashboard | tooltip-bearing control | Gavi Funding Cut (%) / Global Fund Funding Cut (%) for B (keys `mb_gavi_cut`, `mb_gf_cut`) | ms._shortfall_sliders | model_section.py:484 (318) | conditional: compare on and B = Global Fund & Gavi Shortfalls |
| TOM-UI-050 | Dashboard | control | Government Response (B) (radio, key `mb_mode`, default As Much as Fiscal Space Allows; same 4 options) | ms._controls | model_section.py:485 | conditional: compare on |
| TOM-UI-051 | Dashboard | control | Share of Lost Aid Replaced (B, %) (slider, key `mb_theta`) | ms._controls | model_section.py:488 | conditional: compare on and B response = Replace a Set Share |
| TOM-UI-052 | Dashboard | control | Where Replacement Money Goes (B) (radio, key `mb_alloc`, default Hypothetical Best Case (Triage)) | ms._controls | model_section.py:490 | conditional: compare on |
| TOM-UI-053 | Dashboard | caption/text block | "Scenario B uses Scenario A's fiscal-space ceiling and model parameters." | ms._controls | model_section.py:493 | conditional: compare on |
| TOM-UI-054 | Dashboard | heading | Model Parameters (bold markdown) + caption "Each parameter is drawn from a triangular distribution ..." | ms._controls | model_section.py:496-497 | always (in Advanced) |
| TOM-UI-055 | Dashboard | table | Parameter editor (data_editor, key `m_params`): columns Label, Central, Low, High, Unit, Status, Source (param hidden) | ms._controls | model_section.py:499-503 | always (in Advanced) |
| TOM-UI-056 | Dashboard | caption/text block | "Not applied: ... Using the last valid values." | ms._controls | model_section.py:507 | conditional: edited parameters invalid |
| TOM-UI-057 | Dashboard | section | Year panel (chart + per-year sliders) | paths_ui.year_panel | model_section.py:518-523 (paths_ui.py:145) | conditional: path shape not Sudden/MOU, or response = Gradual Budget Increase |
| TOM-UI-058 | Dashboard | chart | Funding path chart (no title; traces "Aid Cut in Force" or "US Bilateral Aid Cut (MOU)", "Extra Health Share"; annotations "Unfilled Gap", "Gap Filled") | paths_ui._chart | paths_ui.py:183, 187-222 | conditional: year panel shown |
| TOM-UI-059 | Dashboard | caption/text block | Year labels 2026 ... 2030 | paths_ui.year_panel | paths_ui.py:153 | conditional: year panel shown |
| TOM-UI-060 | Dashboard | control | Aid Cut (5 sliders 0-100%, keys `m_cut_2026` ... `m_cut_2030`) | paths_ui.year_panel | paths_ui.py:156 | conditional: year panel shown and not MOU |
| TOM-UI-061 | Dashboard | control | Extra Health Share (5 sliders "+x.x pts", keys `m_gov_2026` ... `m_gov_2030`) | paths_ui.year_panel | paths_ui.py:161 | conditional: Gradual Budget Increase and room > 0 |
| TOM-UI-062 | Dashboard | caption/text block | "Already at the 15% target" | paths_ui.year_panel | paths_ui.py:164 | conditional: Gradual and room = 0 |
| TOM-UI-063 | Dashboard | caption/text block | "Note: the cut falls in {years}. That is read as aid returning, and people return to care." | paths_ui.year_panel | paths_ui.py:171 | conditional: a year's cut is lower than the year before |
| TOM-UI-064 | Dashboard | control | Reset to Shape (button, key `path_reset_btn`) | paths_ui.year_panel | paths_ui.py:173 | conditional: year panel shown and not MOU |
| TOM-UI-065 | Dashboard | caption/text block | "{country}: health is {x}% of government spending ({yr}); fastest sustained rise in its history: ..." | paths_ui.outcome_panel | paths_ui.py:240 | conditional: year panel shown and model data exist |
| TOM-UI-066 | Dashboard | card/metric | Extra Deaths 2026-2030 (pill, note "Range {lo} to {hi}") | paths_ui.outcome_panel | paths_ui.py:248 | conditional: year panel shown and model data exist |
| TOM-UI-067 | Dashboard | card/metric | Further Deaths, 2031-2035, Set in Motion by 2030 (Assumption-Driven) (pill) | paths_ui.outcome_panel | paths_ui.py:251 | as above |
| TOM-UI-068 | Dashboard | card/metric | Deaths Avoided vs Sudden Cut With No Response (pill, note "of {N}") | paths_ui.outcome_panel | paths_ui.py:255 | as above |
| TOM-UI-069 | Dashboard | card/metric | Break-Even Budget Increase (pill; "Not reachable by 15%" / "None needed" / "+x.x points a year") | paths_ui.outcome_panel | paths_ui.py:257 | as above |
| TOM-UI-070 | Dashboard | caption/text block | Outcome sentence "{path phrase} and {response}, {country} keeps pace ... and avoids about N of the M deaths a sudden cut would cause." | paths_ui.outcome_panel | paths_ui.py:270-277 | as above |
| TOM-UI-071 | Dashboard | caption/text block | "Assumes people return to care when funding returns ..." | paths_ui.outcome_panel | paths_ui.py:278 | as above |
| TOM-UI-072 | Dashboard | section | Money Spent on Health in {country}, Over Time (section header, icon payments; tooltip "DAH = development assistance for health ...") | th.section_header | views/1_Dashboard.py:321 | always |
| TOM-UI-073 | Dashboard | caption/text block | "{country} isn't in the IHME health-spending dataset ..." (st.info) | page body | views/1_Dashboard.py:326 | conditional: no spending file |
| TOM-UI-074 | Dashboard | control | Show As (radio, label hidden, key `c2_view`; options US$ Total, US$ per Person, Share of Total (%)) | page body | views/1_Dashboard.py:330 | conditional: spending data exist |
| TOM-UI-075 | Dashboard | chart | Health Spending by Source (subtitle "2015-2023; Constant 2023 US$"; series Foreign Aid for Health (DAH), Government, Prepaid Private, Out-of-Pocket; y axis "US$ {Millions/Billions/Trillions} (Constant 2023)" / "US$ per Person (Constant 2023)" / "% Of Total Health Spending"; source "IHME Global Health Spending 1995-2023; constant 2023 US$.") | chart() | views/1_Dashboard.py:356-376 | conditional: spending data exist |
| TOM-UI-076 | Dashboard | card/metric | Total Spending, 2023 (pill) | pill_row | views/1_Dashboard.py:380 | conditional: spending data exist |
| TOM-UI-077 | Dashboard | card/metric | Foreign Aid Share of Total, 2023 (pill) | pill_row | views/1_Dashboard.py:381 | conditional: spending data exist |
| TOM-UI-078 | Dashboard | section | Who Is Providing the Money in {country}? (section header, icon public) | th.section_header | views/1_Dashboard.py:389 | always |
| TOM-UI-079 | Dashboard | caption/text block | "{country} is not a recipient in the IHME DAH database ..." (st.info) | page body | views/1_Dashboard.py:392 | conditional: no DAH file |
| TOM-UI-080 | Dashboard | control | Health Category (selectbox, key `c1_hfa`; options All Focus Areas, HIV/AIDS, Malaria, Tuberculosis, Reproductive & Maternal Health, Newborn & Child Health (Incl. Vaccines), Other Infectious Diseases, Non-Communicable Diseases, Health Systems Strengthening, Other (Focus Area Known, Not in List), Unallocated (No Focus Area Info)) | page body | views/1_Dashboard.py:398 | conditional: DAH data exist |
| TOM-UI-081 | Dashboard | control | Program Area (selectbox, key `c1_pa_{hfa}`; "All Program Areas" + program areas of the category, title-cased PA_LABELS) | page body | views/1_Dashboard.py:405 | conditional: category has program areas |
| TOM-UI-082 | Dashboard | control | Channel Settings (popover, icon tune) | page body | views/1_Dashboard.py:410 | conditional: DAH data exist |
| TOM-UI-083 | Dashboard | tooltip-bearing control | Channels Drawn as NGO / Foundation (Lighter Shade) (multiselect, key `c1_ngo`; 22 options e.g. "US NGOs (NGO)", "Gates Foundation (Direct) (GATES)", "US Bilateral (USAID/State/Etc.) (BIL_USA)"; default NGO, INTLNGO, US_FOUND, GATES) | page body | views/1_Dashboard.py:411-417 | conditional: inside Channel Settings |
| TOM-UI-084 | Dashboard | card/metric | Total in {yr} (pill) | pill_row | views/1_Dashboard.py:457 | conditional: funding > 0 |
| TOM-UI-085 | Dashboard | card/metric | Via NGO / Foundation Channels, {yr} (pill) | pill_row | views/1_Dashboard.py:458 | conditional: funding > 0 |
| TOM-UI-086 | Dashboard | card/metric | Largest Funder, {yr} (pill) | pill_row | views/1_Dashboard.py:459 | conditional: funding > 0 |
| TOM-UI-087 | Dashboard | caption/text block | "No funding recorded for this selection." (st.info) | page body | views/1_Dashboard.py:461 | conditional: funding = 0 |
| TOM-UI-088 | Dashboard | chart | Health Aid by Funder (subtitle = selected category, title-cased; funder series with direct labels; annotation "{funder}: x% of {yr} aid"; y "US$ {unit} (Constant 2023)"; note "Lighter shades are aid delivered through NGOs and foundations ..."; source IHME DAH) | chart() | views/1_Dashboard.py:465-502 | conditional: DAH data exist |
| TOM-UI-089 | Dashboard | heading | Where the Aid Is Spent (st.subheader) | page body | views/1_Dashboard.py:508 | always |
| TOM-UI-090 | Dashboard | caption/text block | "{country} is not a recipient in the IHME DAH database, so there is no category breakdown to show." (st.info) | page body | views/1_Dashboard.py:519 | conditional: no DAH file |
| TOM-UI-091 | Dashboard | control | Show As (radio, label hidden, key `c3b_view`; options US$ Total, Share of Total (%)) | page body | views/1_Dashboard.py:524 | conditional: DAH data exist |
| TOM-UI-092 | Dashboard | control | Break Down (selectbox, key `c3b_brk`; options All Focus Areas, HIV/AIDS, Malaria, Tuberculosis, Reproductive & Maternal Health, Newborn & Child Health (Incl. Vaccines), Other Infectious Diseases, Non-Communicable Diseases, Health Systems Strengthening) | page body | views/1_Dashboard.py:528 | conditional: DAH data exist |
| TOM-UI-093 | Dashboard | caption/text block | "No funding recorded for this selection." (st.info) | page body | views/1_Dashboard.py:555 | conditional: nothing in the breakdown |
| TOM-UI-094 | Dashboard | chart | Health Aid by What It Pays For (subtitle "All Focus Areas" or "Inside {focus area}"; series = 6 focus areas + "All Other", or top 6 program areas + "All Other"; y "% Of Health Aid" or "US$ {unit} (Constant 2023)"; source IHME DAH) | chart() | views/1_Dashboard.py:560-584 | conditional: data in breakdown |
| TOM-UI-095 | Dashboard | section | Revenue and Spending in {country} (section header, icon account_balance) | th.section_header | views/1_Dashboard.py:590 | always |
| TOM-UI-096 | Dashboard | caption/text block | "The IMF files have no government revenue or spending-by-function data for {country}." (st.info) | _budget_section | views/1_Dashboard.py:601 | conditional: no IMF data |
| TOM-UI-097 | Dashboard | control | Year (selectbox, key `c4_year_{iso3}`; years with IMF data, newest first) | _budget_section | views/1_Dashboard.py:608 | conditional: IMF data exist |
| TOM-UI-098 | Dashboard | caption/text block | "No IMF revenue or spending data for {country} in {yr}." (st.info) | _budget_section | views/1_Dashboard.py:635 | conditional: chosen year empty |
| TOM-UI-099 | Dashboard | chart | Government Revenue and Spending, {yr} (treemap; boxes "Government Budget", "Money In: Revenue ({level}) + Borrowing", "Money Out: Spending ({level}) + Surplus", revenue items, "Borrowing (Spending Beyond Revenue)", "Health" with sub-functions, other functions, "Surplus (Revenue Not Spent)", Other Levels of Government box; source IMF WEO / WoRLD / COFOG) | chart() | views/1_Dashboard.py:643-731 | conditional: IMF data for the year |
| TOM-UI-100 | Dashboard | card/metric | Revenue, {yr} (pill) | pill_row | views/1_Dashboard.py:748 | conditional: revenue total known |
| TOM-UI-101 | Dashboard | card/metric | Spending, {yr} (pill) | pill_row | views/1_Dashboard.py:750 | conditional: spending total known |
| TOM-UI-102 | Dashboard | card/metric | Deficit (Borrowing) / Surplus (pill) | pill_row | views/1_Dashboard.py:754 | conditional: both sides present |
| TOM-UI-103 | Dashboard | card/metric | Gross Government Debt, {yr} (pill) | pill_row | views/1_Dashboard.py:756 | conditional: debt known |
| TOM-UI-104 | Dashboard | caption/text block | Budget captions: box caption, side notes, "Grey box: the rest of the IMF WEO general-government total ...", "The dark purple box is borrowing: ...", "The green box is the surplus: ...", "The IMF World Economic Outlook has no general-government totals for this year ...", "The IMF records only part of {country}'s health spending ..." | _budget_section | views/1_Dashboard.py:760-784 | conditional (each on its own condition) |
| TOM-UI-105 | Dashboard | section | How Aid Cuts Translate into Coverage and Lives in {country} (section header, icon monitor_heart; tooltip INTRO "A four-step model ...") | ms.render_model_section | views/1_Dashboard.py:805 (model_section.py:773) | always |
| TOM-UI-106 | Dashboard | caption/text block | "{scenario title} · {response label}. Change the scenario at the top of the page." | ms.render_model_section | model_section.py:774 | always |
| TOM-UI-107 | Dashboard | caption/text block | "{country} has no recorded HIV, TB, malaria or vaccine aid in 2021-2023 ... See the All Countries page ..." (st.info) | ms.render_model_section | model_section.py:777 | conditional: country not modelled (rest of model section hidden) |
| TOM-UI-108 | Dashboard | caption/text block | "Under '{preset}' {country} loses no HIV, TB, malaria or vaccine aid ..." (st.success) | ms._country_results | model_section.py:792 | conditional: gross loss = 0 and base > 0 |
| TOM-UI-109 | Dashboard | heading | The Numbers (st.subheader) | ms._country_results | model_section.py:807 | conditional: compare off |
| TOM-UI-110 | Dashboard | card/metric | Aid at Risk (per Year) (pill; note "{x%} of {$} for These Four Buckets") | _headline_items / _stat_grid | model_section.py:989, 808 | conditional: compare off (also in each comparison column) |
| TOM-UI-111 | Dashboard | card/metric | Replaced by Government (pill; note "{x%} of the Loss") | _headline_items | model_section.py:992 | as above |
| TOM-UI-112 | Dashboard | card/metric | Net Aid Lost (pill; note "Incl. {$} Health-Systems Money, ..." or "Per Year"; tooltip net_aid_note) | _headline_items | model_section.py:995 (951) | as above |
| TOM-UI-113 | Dashboard | card/metric | Further Deaths, 2031-2035 (Assumption-Driven) (pill; note "Range {lo} to {hi} · {reengage range}") | _headline_items | model_section.py:996-999 | as above |
| TOM-UI-114 | Dashboard | card/metric | Extra Deaths Over 5 Years (pill; note "Range {lo} to {hi}"; tooltip basis + range text) | _headline_items | model_section.py:1000 | as above |
| TOM-UI-115 | Dashboard | card/metric | New HIV Infections, 5 Years (pill; note "Range ...") | _headline_items | model_section.py:1002 | as above |
| TOM-UI-116 | Dashboard | heading | Scenario A vs Scenario B (st.subheader) | ms._comparison | model_section.py:1017 | conditional: compare on |
| TOM-UI-117 | Dashboard | caption/text block | "**Scenario A:** {title} · {response}" / "**Scenario B:** ..." + a 2-column grid of the six headline pills each | ms._comparison | model_section.py:1025-1026 | conditional: compare on |
| TOM-UI-118 | Dashboard | caption/text block | "Scenario B averts/adds about **N** extra deaths over 5 years in {country} compared with Scenario A." | ms._comparison | model_section.py:1029 | conditional: compare on |
| TOM-UI-119 | Dashboard | chart | Extra Deaths by Disease (subtitle "Scenario A vs. B, Over 5 Years"; series Scenario A, Scenario B; y "Extra Deaths, 5 Years") | ms._comparison | model_section.py:1032-1041 | conditional: compare on |
| TOM-UI-120 | Dashboard | caption/text block | "Government replacement of {$} a year averts about **N deaths over 5 years** compared with no government replacement ({$} per death averted)." | ms._country_results | model_section.py:811 | conditional: response not none and replaced > 0 |
| TOM-UI-121 | Dashboard | download | Download Country Brief (download_button, key `m_brief`) | ms._country_results / _brief_html | model_section.py:816 (1985) | not shown: SHOW_BRIEF = False (model_section.py:49) |
| TOM-UI-122 | Dashboard | heading | What Every US$1 Million Cut Does, by Disease (st.subheader with help) | ms._country_results | model_section.py:824 | conditional: country modelled |
| TOM-UI-123 | Dashboard | card/metric | Per-disease cards HIV, TB, Malaria, Immunization: subtitle "main service: {HIV treatment (ART) / TB treatment / bednets / routine vaccines} ({unit})"; big numbers "People Losing the Main Service", "Coverage Drop (Percentage Points)", "Extra Deaths Over 5 Years"; foot "Spread across all {disease} services ... · Model estimate: about {$} of aid lost per life lost (based on US$1M a year for 5 years)" (tooltip CARD_FOOT_TIP); or "No {disease} aid in {country}" / "No {disease} deaths modelled in {country}" | _per_million_cards / _cards_html | model_section.py:830, 1058-1110 | conditional: country modelled (4 cards) |
| TOM-UI-124 | Dashboard | heading | Where the Money Is Lost (st.subheader) | ms._country_results | model_section.py:833 | conditional: country modelled |
| TOM-UI-125 | Dashboard | caption/text block | "No aid is cut in this scenario." (st.info) | ms._country_results | model_section.py:837 | conditional: no cell loses money |
| TOM-UI-126 | Dashboard | chart | Aid Lost per Year (subtitle "Lighter = Replaced by Government" when anything is replaced; one bar per disease) | _loss_by_bucket_fig | model_section.py:843 (1131-1152) | conditional: some aid cut |
| TOM-UI-127 | Dashboard | chart | Who Cut the Money (bars "US · Bilateral" etc., max 12 incl. "All other") | _who_cut_fig | model_section.py:845 (1169-1183) | conditional: some aid cut |
| TOM-UI-128 | Dashboard | caption/text block | Source line "Note: Donors are who originally paid; the label after the dot is the channel ... Source: Model estimates from IHME aid data ..." | ms._country_results | model_section.py:846 | conditional: some aid cut |
| TOM-UI-129 | Dashboard | heading | What Each Service Loses (st.subheader; help = capped note, flags, HIV prevention / systems / testing notes, deaths-range text) | ms._country_results | model_section.py:865 | conditional: country modelled |
| TOM-UI-130 | Dashboard | table | What Each Service Loses (HTML table; columns Service, Donor Aid Now / per year, Aid Lost / per year, after government replacement, Cost per Person, People Losing Service, per Year, Coverage, Extra Deaths, 5 Years Total; Other Aid and Total rows) - see section B | _service_table_html | model_section.py:866 (1264-1341) | conditional: country modelled |
| TOM-UI-131 | Dashboard | caption/text block | "Other Aid is money the model does not link to deaths: ... The deaths range is for the total, so it is narrower than adding the rows' ranges." | ms._country_results | model_section.py:868-872 | conditional: country modelled |
| TOM-UI-132 | Dashboard | chart | Coverage Lost, by Service (subtitle "Percentage Points; Coverage Before → After"; one bar per service; source "Model estimates; coverage today: UNAIDS/WHO 2025 ...") | _coverage_fig | model_section.py:873-876 (1353-1373) | conditional: any service with coverage drop > 0 |
| TOM-UI-133 | Dashboard | heading | How the Damage Scales (st.subheader with help) | ms._country_results | model_section.py:879 | conditional: country modelled |
| TOM-UI-134 | Dashboard | tooltip-bearing control | Bucket (Left Chart Only) (radio, key `m_dose_b`; options HIV, TB, Malaria, Immunization) | ms._country_results | model_section.py:884 | conditional: country modelled |
| TOM-UI-135 | Dashboard | caption/text block | "An even 10% cut to {bucket} aid adds about **N** extra deaths over 5 years." / "{country} receives no {bucket} aid in the model, so cutting it changes nothing." | ms._country_results | model_section.py:894, 896 | conditional: country modelled |
| TOM-UI-136 | Dashboard | chart | Extra Deaths as More Aid Is Cut (traces Range Across Parameter Values, Even Cut Across All Donors, This Scenario (dashed), dot; annotations "This Scenario: x% Cut, N Deaths", "Even Cut, All Donors", "Range Across Parameter Values"; x "Share of This Bucket's Aid Lost", y "Extra Deaths Over 5 Years") | _dose_fig | model_section.py:899 (1376-1419) | conditional: country modelled (dashed line not for MOU; dot only if current cut > 0) |
| TOM-UI-137 | Dashboard | chart | Extra Deaths Each Year (subtitle "All Four Diseases, 2026-2030"; stacked HIV, TB, Malaria, Immunization; y "Extra Deaths in That Year") | _path_fig | model_section.py:901 (1422-1433) | conditional: country modelled |
| TOM-UI-138 | Dashboard | caption/text block | "The scenario-path line isn't shown for MOU schedules ..." | ms._country_results | model_section.py:903 | conditional: preset = MOU |
| TOM-UI-139 | Dashboard | caption/text block | Source/note line "The solid line cuts every donor and service by the same share. The dashed line is this scenario's actual cut ..." | ms._country_results | model_section.py:905 | conditional: country modelled |
| TOM-UI-140 | Dashboard | heading | Can {country} Fill the Gap? (st.subheader with help) | ms._fiscal_panel | model_section.py:1507 | conditional: country modelled |
| TOM-UI-141 | Dashboard | card/metric | Government Health Spending (2023) (pill; note "${x} per person · x% of GDP") | ms._fiscal_panel | model_section.py:1521 | conditional: country modelled |
| TOM-UI-142 | Dashboard | card/metric | Aid Lost as % of Government Health Spending (pill) | ms._fiscal_panel | model_section.py:1524 | as above |
| TOM-UI-143 | Dashboard | card/metric | Aid Lost as % of Government Revenue (pill) | ms._fiscal_panel | model_section.py:1526 | as above |
| TOM-UI-144 | Dashboard | card/metric | Health Share of Government Spending, {yr} [(estimated)] (pill; note "Abuja Target: 15%") | health_share_pill | model_section.py:1528 (1480) | as above |
| TOM-UI-145 | Dashboard | card/metric | Gap Before Government Steps In (pill; note "2030: {$}" when it differs) | ms._fiscal_panel | model_section.py:1533 | as above |
| TOM-UI-146 | Dashboard | card/metric | Filled by the Government (pill; note "No Government Replacement selected" or "2030: ...") | ms._fiscal_panel | model_section.py:1535 | as above |
| TOM-UI-147 | Dashboard | card/metric | Gap Left After Government Response (pill) | ms._fiscal_panel | model_section.py:1538 | as above |
| TOM-UI-148 | Dashboard | caption/text block | Fiscal sentence "{country} loses about {$}/yr in aid; under {response} the government fills ..." | _fiscal_sentence | model_section.py:1542 (1466) | as above |
| TOM-UI-149 | Dashboard | chart | The Gap and the Government Response (subtitle "US$ per Year"; rows "Average per Year, 2026-2030" and "2030"; traces Gap, Filled by the Government, Gap Left; dashed line annotation "Backfill Capacity (Fiscal Space): {$}"; note when capacity off scale) | ms._fiscal_panel | model_section.py:1545-1582 | conditional: gap > 0 |

### Page 2: All Countries (views/2_All_Countries.py)

| ID | Page | Kind | Name as shown | Rendering function | file:line | Shown? |
|---|---|---|---|---|---|---|
| TOM-UI-150 | All Countries | heading | All Countries (st.title) | page body | views/2_All_Countries.py:20 | always |
| TOM-UI-151 | All Countries | tooltip-bearing control | Donor Scenario (selectbox, key `ac_preset`, shared via `sel_preset`; tooltip = preset description) | th.shared_select | views/2_All_Countries.py:23-25 | always |
| TOM-UI-152 | All Countries | preset | Donor Scenario options (all 7, no MOU filtering): US Bilateral Exit + Multilateral Withdrawals; America First MOUs; IHME 2025 Preliminary Estimates; Total-Aid Cuts (OECD) Applied to Health Aid; Global Fund & Gavi Shortfalls; Combined Retreat; Custom | th.shared_select | views/2_All_Countries.py:23 | always |
| TOM-UI-153 | All Countries | caption/text block | "No country loses aid in this scenario." (st.info) | ms.cross_country | model_section.py:1737 | conditional: no country loses aid |
| TOM-UI-154 | All Countries | caption/text block | "{scenario title} · {response label}[ · Death Rates Held Constant]" | ms.cross_country | model_section.py:1741 | conditional: some country loses aid |
| TOM-UI-155 | All Countries | caption/text block | "This page uses the default cuts (Gavi −15% · Global Fund −20%). Your setting (...) applies to the country Dashboard only." | ms.cross_country | model_section.py:1744 | conditional: shortfalls preset with non-default sliders |
| TOM-UI-156 | All Countries | heading | MOU Countries With Funding Data ({n}) (st.subheader with help) | ms.cross_country | model_section.py:1747 | conditional: preset = America First MOUs |
| TOM-UI-157 | All Countries | card/metric | Aid Lost per Year, {n} of {N} Countries / Aid Lost per Year, MOU Countries With Funding Data ({n}) (pill; note "Net Aid Lost {$}"; tooltip includes SCOPE_NOTE) | ms.cross_country | model_section.py:1759-1762 | conditional: some country loses aid |
| TOM-UI-158 | All Countries | card/metric | Further Deaths, 2031-2035 (Assumption-Driven) (pill; note "Range ...; ... across return-to-care x%-y% a year") | ms.cross_country | model_section.py:1763-1771 | conditional: results have deaths_after_2030 |
| TOM-UI-159 | All Countries | card/metric | Extra Deaths, Year 1 (pill; tooltip "Deaths build up over the five years") | ms.cross_country | model_section.py:1773 | conditional: results lack deaths_after_2030 (fallback) |
| TOM-UI-160 | All Countries | card/metric | Extra Deaths Over 5 Years (pill; note "Range ..."; tooltip ALL_RANGE_TIP) | ms.cross_country | model_section.py:1774 | conditional: some country loses aid |
| TOM-UI-161 | All Countries | card/metric | New HIV Infections, 5 Years (pill) | ms.cross_country | model_section.py:1776 | conditional: some country loses aid |
| TOM-UI-162 | All Countries | tooltip-bearing control | World (toggle, key `m_map_world`, default off; tooltip "Show the whole world instead of Africa and Asia") | ms.cross_country | model_section.py:1783 | conditional: some country loses aid |
| TOM-UI-163 | All Countries | chart | Extra Deaths per 100,000 People (subtitle "Over 5 Years"; choropleth, colour bar "Extra Deaths per 100,000 (5 Years)"; MOU greys "MOU signed; no funding data" / "No MOU"; selected country outlined) | _world_map | model_section.py:1785 (1862-1899) | conditional: some country loses aid |
| TOM-UI-164 | All Countries | chart | Budget Exposure vs. Deaths (subtitle "Each Circle Is a Country"; x "Aid Lost, % of Govt. Health Spending (Log)", y "Extra Deaths per 100,000, 5 Years (Log)"; labels top 8; note "Each circle is a country, sized by aid lost per year; {country} is highlighted. Dotted lines are medians.") | ms.cross_country | model_section.py:1789-1833 | conditional: some country loses aid |
| TOM-UI-165 | All Countries | chart | Most Extra Deaths, 5 Years (subtitle = colour key HIV TB Malaria Immunization; top 15 stacked bars; note "{country} ranks {r} of {n}." when outside top 15) | ms.cross_country | model_section.py:1835-1858 | conditional: some country loses aid |

### Page 3: Validation & Benchmarks (views/3_Validation.py)

| ID | Page | Kind | Name as shown | Rendering function | file:line | Shown? |
|---|---|---|---|---|---|---|
| TOM-UI-166 | Validation | heading | Validation & Benchmarks (st.title) | page body | views/3_Validation.py:30 | always |
| TOM-UI-167 | Validation | caption/text block | "How the funding-cut model on the dashboard compares with published studies, and with two other ways of estimating the same cut." | page body | views/3_Validation.py:31 | always |
| TOM-UI-168 | Validation | control | Country (selectbox, key `v_country`, shared via `sel_iso3`; default KEN) | th.shared_select | views/3_Validation.py:36 | always |
| TOM-UI-169 | Validation | tooltip-bearing control | Donor Scenario (selectbox, key `v_preset`, with MOU rules as on the Dashboard) | ms.donor_scenario_select | views/3_Validation.py:38 | always |
| TOM-UI-170 | Validation | caption/text block | MOU notice | page body | views/3_Validation.py:40 | conditional: MOU fallback |
| TOM-UI-171 | Validation | caption/text block | "{preset description} Government response (...), model parameters and the death-rate setting follow the dashboard." | page body | views/3_Validation.py:48 | always |
| TOM-UI-172 | Validation | section | How Our Totals Compare with Published Estimates (section header, icon fact_check) | th.section_header | views/3_Validation.py:54 | always |
| TOM-UI-173 | Validation | heading | Model: Extra Deaths Over 5 Years, All {n} Countries (st.subheader; help "America First MOUs covers only ...") | page body | views/3_Validation.py:67 | always |
| TOM-UI-174 | Validation | table | Model table: index Scenario (rows = 6 precomputed presets, MOU row "America First MOUs ({n} MOU Countries With Funding Data)"); columns HIV, TB, Malaria, Immunization, All Four, Range Across Parameter Values | page body (st.table) | views/3_Validation.py:56-69 | always |
| TOM-UI-175 | Validation | caption/text block | "Read from the precomputed results: No Government Replacement, ..." | page body | views/3_Validation.py:70 | always |
| TOM-UI-176 | Validation | heading | Published Estimates (st.subheader with help) | page body | views/3_Validation.py:102 | conditional: Full US exit precomputed file exists |
| TOM-UI-177 | Validation | table | Published Estimates: index Source; columns What It Measures, Published, Closest Model Figure (rows Cavalcanti x2, UNAIDS 2025, Optima, Gavi) | page body (st.table) | views/3_Validation.py:78-110 | conditional: as above |
| TOM-UI-178 | Validation | caption/text block | "The published studies cover more causes, sectors or years than the model ..." | page body | views/3_Validation.py:111 | conditional: as above |
| TOM-UI-179 | Validation | section | Lines Where Donor Money Exceeds the Modelled Service Cost (section header, icon rule) | th.section_header | views/3_Validation.py:126 | always |
| TOM-UI-180 | Validation | card/metric | Country-Service Lines Affected (pill; note "of {n} modelled") | th.pills_html | views/3_Validation.py:131 | always |
| TOM-UI-181 | Validation | card/metric | Countries With At Least One (pill) | th.pills_html | views/3_Validation.py:132 | always |
| TOM-UI-182 | Validation | card/metric | Lines in {country} (pill) | th.pills_html | views/3_Validation.py:133 | always |
| TOM-UI-183 | Validation | table | index Service; column Countries | page body (st.table) | views/3_Validation.py:137 | conditional: any line affected |
| TOM-UI-184 | Validation | caption/text block | "In these lines, baseline donor aid ÷ cost per person is more than the donor-funded pool ..." | page body | views/3_Validation.py:139 | always |
| TOM-UI-185 | Validation | section | People on ART Paid for by Donors: Model vs PEPFAR (section header, icon medication) | th.section_header | views/3_Validation.py:155 | always |
| TOM-UI-186 | Validation | card/metric | Model: Donor-Funded People on ART (pill) | th.pills_html | views/3_Validation.py:158 | always |
| TOM-UI-187 | Validation | card/metric | PEPFAR: People on ART It Supports (pill) | th.pills_html | views/3_Validation.py:160 | always |
| TOM-UI-188 | Validation | caption/text block | "Model = for each country, the smaller of the people on ART ..." | page body | views/3_Validation.py:162 | always |
| TOM-UI-189 | Validation | section | Malaria Inputs: Malaria Atlas Project 2025 vs Previous Sources (section header, icon coronavirus) | th.section_header | views/3_Validation.py:171 | always |
| TOM-UI-190 | Validation | card/metric | Baseline Malaria Deaths, Dashboard Countries (pill) | th.pills_html | views/3_Validation.py:178 | always |
| TOM-UI-191 | Validation | card/metric | WHO Global Malaria Deaths, 2024 (pill, 610,000) | th.pills_html | views/3_Validation.py:180 | always |
| TOM-UI-192 | Validation | card/metric | Share Covered by the Dashboard (pill) | th.pills_html | views/3_Validation.py:181 | always |
| TOM-UI-193 | Validation | table | Malaria input comparison (st.dataframe): index Country; columns Treatment: Before, Treatment: Now, Bednets: Before, Bednets: Now, Cases: Before, Cases: MAP 2025, Cases: Change | ms.malaria_input_comparison | views/3_Validation.py:184-185 (model_section.py:1671) | always |
| TOM-UI-194 | Validation | caption/text block | "Treatment now = MAP effective treatment ... ⚑ = cases differ by more than 30% ..." | page body | views/3_Validation.py:186 | always |
| TOM-UI-195 | Validation | caption/text block | "Pakistan: MAP puts cases at ..." | page body | views/3_Validation.py:201 | conditional: PAK modelled |
| TOM-UI-196 | Validation | section | Data Years (section header, icon event) | th.section_header | views/3_Validation.py:209 | always |
| TOM-UI-197 | Validation | table | Data Years: index Input; columns Year, Source, Countries by source (20 rows from DATA_YEARS) | ms.data_years_table | views/3_Validation.py:210 (model_section.py:1651) | always |
| TOM-UI-198 | Validation | caption/text block | "Year = the most common year across the dashboard countries ..." | page body | views/3_Validation.py:211 | always |
| TOM-UI-199 | Validation | section | Three Ways to Estimate the Same Cut: {country} (section header, icon compare_arrows) | th.section_header | views/3_Validation.py:214 | always |
| TOM-UI-200 | Validation | caption/text block | "{scenario title} · {response}[ · Death Rates Held Constant]" | page body | views/3_Validation.py:215 | always |
| TOM-UI-201 | Validation | caption/text block | "{country} has no recorded HIV, TB, malaria or vaccine aid in 2021-2023, so there is nothing to model." (st.info, then st.stop: the rest of the page is hidden) | page body | views/3_Validation.py:218 | conditional: country not modelled |
| TOM-UI-202 | Validation | chart | Extra Deaths by Method (subtitle "{country}, Over 5 Years"; series Unit-Cost Model, Poisson Regression, Lancet Rate Ratios; x HIV, TB, Malaria, Under-5, Maternal; error bars; y "Extra Deaths Over 5 Years") | page body | views/3_Validation.py:231-251 | conditional: country modelled |
| TOM-UI-203 | Validation | caption/text block | "**Reading:** In {country}, ... land within a factor of two of the unit-cost model ..." | _reading | views/3_Validation.py:287 (259) | conditional: country modelled |
| TOM-UI-204 | Validation | heading | Estimates by Method (st.subheader; help = ranges note, US aid per person, HIV baseline deaths source, Poisson note) | page body | views/3_Validation.py:314 | conditional: country modelled |
| TOM-UI-205 | Validation | table | Estimates by Method: index Bucket (HIV, TB, Malaria, Under-5, Maternal); columns Unit-Cost Model, Poisson Regression, Lancet Rate Ratios ("Not Covered" where missing) | page body (st.table) | views/3_Validation.py:289-315 | conditional: country modelled |
| TOM-UI-206 | Validation | caption/text block | "Ranges: unit-cost model = range across parameter values ..." | page body | views/3_Validation.py:316 | conditional: country modelled |
| TOM-UI-207 | Validation | section | How Each Method Works (section header, icon functions) | th.section_header | views/3_Validation.py:323 | conditional: country modelled |
| TOM-UI-208 | Validation | heading | Unit-Cost Model (st.subheader) + description with "**Main limitation:**" | page body | views/3_Validation.py:326-331 | conditional: country modelled |
| TOM-UI-209 | Validation | heading | Poisson Regression (st.subheader) + description | page body | views/3_Validation.py:333-338 | conditional: country modelled |
| TOM-UI-210 | Validation | heading | Lancet Rate Ratios (st.subheader) + description | page body | views/3_Validation.py:340-346 | conditional: country modelled |
| TOM-UI-211 | Validation | heading | Our Poisson Regressions (st.subheader) | page body | views/3_Validation.py:352 | conditional: country modelled |
| TOM-UI-212 | Validation | table | Our Poisson Regressions: index Outcome (TB Deaths, Under-5 Deaths, Child Malaria Deaths (Africa)); columns Aid Measure (Log 1 + US$), Coefficient, Standard Error, Countries, Observations, Years | page body (st.table) | views/3_Validation.py:353-357 | conditional: country modelled |
| TOM-UI-213 | Validation | caption/text block | "A negative coefficient means more aid has gone with fewer deaths. ..." | page body | views/3_Validation.py:358 | conditional: country modelled |

### Page 4: Methods (views/4_Methods.py)

Methods has no widgets other than the tabs; country, scenario and settings come from session state (`sel_iso3`, `sel_preset`, `model_ctx`).

| ID | Page | Kind | Name as shown | Rendering function | file:line | Shown? |
|---|---|---|---|---|---|---|
| TOM-UI-214 | Methods | heading | Methods, Data and Limitations (st.title) | page body | views/4_Methods.py:79 | always |
| TOM-UI-215 | Methods | caption/text block | "A complete guide to how every number on the dashboard is calculated ..." | page body | views/4_Methods.py:80 | always |
| TOM-UI-216 | Methods | tab | Tabs: Overview, Dashboard Sections, The Model, Step by Step, Data Sources, Assumptions & Limitations, Parameters, Cross-Checks | st.tabs | views/4_Methods.py:83 | always |
| TOM-UI-217 | Methods | section | Overview > What the Dashboard Does (section header, icon info) | th.section_header | views/4_Methods.py:90 | tab Overview |
| TOM-UI-218 | Methods | heading | run-in bold: "Description (Sections 1 to 3)." / "Simulation (Section 4 and the All Countries page)." + numbered list Money, Fiscal response, Coverage, Lives | md | views/4_Methods.py:94, 98, 101-106 | tab Overview |
| TOM-UI-219 | Methods | section | Overview > Units and Currency (section header, icon payments) | th.section_header | views/4_Methods.py:111 | tab Overview |
| TOM-UI-220 | Methods | heading | run-in bold: "Every dollar figure is in constant 2023 US dollars (except MOU amounts)" | md | views/4_Methods.py:113 | tab Overview |
| TOM-UI-221 | Methods | section | Overview > Time Periods (section header, icon schedule) | th.section_header | views/4_Methods.py:132 | tab Overview |
| TOM-UI-222 | Methods | table | Time Periods (markdown table): What, Years | md | views/4_Methods.py:134 | tab Overview |
| TOM-UI-223 | Methods | section | Overview > Data Years (section header, icon event) | th.section_header | views/4_Methods.py:145 | tab Overview |
| TOM-UI-224 | Methods | table | Data Years: index Input; Year, Source, Countries by source | ms.data_years_table | views/4_Methods.py:150 | tab Overview |
| TOM-UI-225 | Methods | section | Dashboard Sections > Country Header (section header, icon badge) | th.section_header | views/4_Methods.py:156 | tab Dashboard Sections |
| TOM-UI-226 | Methods | table | Country Header (markdown): Pill, How it is calculated, Source (rows Region, Income Group, US MOU, GDP, Population) | md | views/4_Methods.py:158 | tab Dashboard Sections |
| TOM-UI-227 | Methods | section | Dashboard Sections > Section 1: Money Spent on Health (icon payments) | th.section_header | views/4_Methods.py:167 | tab Dashboard Sections |
| TOM-UI-228 | Methods | heading | run-in bold: "Data:" | md | views/4_Methods.py:169 | tab Dashboard Sections |
| TOM-UI-229 | Methods | table | Section 1 (markdown): Bar, IHME variable, Meaning | md | views/4_Methods.py:173 | tab Dashboard Sections |
| TOM-UI-230 | Methods | section | Dashboard Sections > Section 2: Who Is Providing the Money (icon public) | th.section_header | views/4_Methods.py:188 | tab Dashboard Sections |
| TOM-UI-231 | Methods | heading | run-in bold: "Data:" / "Funders." / "NGO / foundation channels (lighter shade)." / "Pills:" / "Where the Aid Is Spent." | md | views/4_Methods.py:190, 193, 199, 205, 208 | tab Dashboard Sections |
| TOM-UI-232 | Methods | section | Dashboard Sections > Section 3: Revenue and Spending (icon account_balance) | th.section_header | views/4_Methods.py:215 | tab Dashboard Sections |
| TOM-UI-233 | Methods | heading | run-in bold: "Data:" / "How the treemap is built." / "Health check." | md | views/4_Methods.py:217, 225, 247 | tab Dashboard Sections |
| TOM-UI-234 | Methods | table | Section 3 (markdown): Part, Dataset, Variables | md | views/4_Methods.py:219 | tab Dashboard Sections |
| TOM-UI-235 | Methods | section | Dashboard Sections > Section 4 Outputs (icon monitor_heart) | th.section_header | views/4_Methods.py:252 | tab Dashboard Sections |
| TOM-UI-236 | Methods | table | Section 4 Outputs (markdown): Output, Definition (rows Aid at Risk (per Year); Treatment Lost Each Year; Prevention Lost Each Year; Replaced by Government; Net Aid Lost; Further Deaths, 2031-2035 (Assumption-Driven); Extra Deaths Over 5 Years; Further Deaths, 2031-2035; New HIV Infections, 5 Years; What Every US$1 Million Cut Does, by Disease; What Each Service Loses; Extra Deaths as More Aid Is Cut; Extra Deaths Each Year; Can {Country} Fill the Gap?; All Countries) | md | views/4_Methods.py:254-268 | tab Dashboard Sections |
| TOM-UI-237 | Methods | section | The Model, Step by Step > Step 1: Money (What Aid Is Lost) (icon account_tree) | th.section_header | views/4_Methods.py:275 | tab The Model |
| TOM-UI-238 | Methods | heading | run-in bold: "Baseline." / "Service lines" / "Source groups" / "Channel groups" / "The cut in each cell." / "Money with no reported purpose." / "Systems money" / "HIV testing and care." / "Donor scenarios (presets)." | md | views/4_Methods.py:277, 283, 303, 308, 313, 319, 333, 340, 354 | tab The Model |
| TOM-UI-239 | Methods | caption/text block | LaTeX formulas: baseline (280), cut/loss (317), effective loss (350) | st.latex | views/4_Methods.py:280, 317, 350 | tab The Model |
| TOM-UI-240 | Methods | table | Service lines (markdown): Service line, Bucket, IHME program-area columns | md | views/4_Methods.py:285 | tab The Model |
| TOM-UI-241 | Methods | table | Donor scenarios (markdown): Scenario, What is cut, Source of the numbers (rows US Bilateral Exit + Multilateral Withdrawals, America First MOUs, IHME 2025 Preliminary Estimates, Total-Aid Cuts (OECD) Applied to Health Aid, Global Fund & Gavi Shortfalls, Combined Retreat, Custom) | md | views/4_Methods.py:356-364 | tab The Model |
| TOM-UI-242 | Methods | section | Step 2: Fiscal Response (What the Government Replaces) (icon account_balance) | th.section_header | views/4_Methods.py:367 | tab The Model |
| TOM-UI-243 | Methods | heading | run-in bold list: "No Government Replacement:" / "Replace a Set Share:" / "As Much as Fiscal Space Allows:"; paragraphs "Why No Government Replacement is the default." / "Where replacement money goes." | md | views/4_Methods.py:371-373, 400, 407 | tab The Model |
| TOM-UI-244 | Methods | caption/text block | LaTeX: replacement/capacity (377), debt-stress factor (398) | st.latex | views/4_Methods.py:377, 398 | tab The Model |
| TOM-UI-245 | Methods | section | Step 3: Coverage (Who Loses a Service) (icon groups) | th.section_header | views/4_Methods.py:413 | tab The Model |
| TOM-UI-246 | Methods | caption/text block | LaTeX: donor-funded (437), people losing service (438) | st.latex | views/4_Methods.py:437, 438 | tab The Model |
| TOM-UI-247 | Methods | heading | run-in bold: "Cost per person" / "People in need and current coverage." / "Malaria input flags" | md | views/4_Methods.py:463, 478, 501 | tab The Model |
| TOM-UI-248 | Methods | table | Cost per person (markdown): Service, Formula, Central value / source | md | views/4_Methods.py:465 | tab The Model |
| TOM-UI-249 | Methods | table | People in need (markdown): Service, People in need, Current coverage | md | views/4_Methods.py:487 | tab The Model |
| TOM-UI-250 | Methods | section | Step 4: Lives (Extra Deaths) (icon favorite) | th.section_header | views/4_Methods.py:510 | tab The Model |
| TOM-UI-251 | Methods | heading | run-in bold: "HIV treatment." / "Mother-to-child transmission." / "TB." / "TB spread." / "Timing of TB deaths (logic review L-15)." / "Malaria" / "Routine immunization." / "Timing." / "Vaccines by birth cohort." / "Already-changing death rates" / "New HIV infections." | md | views/4_Methods.py:513, 532, 539, 553, 562, 570, 605, 632, 643, 658, 676 | tab The Model |
| TOM-UI-252 | Methods | caption/text block | LaTeX: ART deaths (530), TB ΔCFR (543), malaria LiST (572), deaths per child (630) | st.latex | views/4_Methods.py:530, 543, 572, 630 | tab The Model |
| TOM-UI-253 | Methods | table | Under-5 share of malaria deaths: index WHO Region; columns Under-5 Share, Rule, Source, Countries With Malaria Deaths | _u5_share_table | views/4_Methods.py:603 (51) | tab The Model |
| TOM-UI-254 | Methods | table | Timing (markdown): Service, Year 1, Year 2, Year 3, Year 4, Year 5 | md | views/4_Methods.py:634 | tab The Model |
| TOM-UI-255 | Methods | section | Funding Paths Over 2026-2030 (icon timeline) | th.section_header | views/4_Methods.py:691 | tab The Model |
| TOM-UI-256 | Methods | caption/text block | LaTeX: net gap (700) | st.latex | views/4_Methods.py:700 | tab The Model |
| TOM-UI-257 | Methods | heading | run-in bold: "Shapes" / "Gradual budget increase." / "Health's share of government spending" / "Which services are tracked how." / "Committed deaths." / "Break-even budget increase." / "Assumptions." | md | views/4_Methods.py:705, 716, 727, 734, 746, 762, 767 | tab The Model |
| TOM-UI-258 | Methods | table | Shapes (markdown): Shape, c(t), t = 1..5, 2026-2030 | md | views/4_Methods.py:707 | tab The Model |
| TOM-UI-259 | Methods | table | Which services are tracked how (markdown): Service, Method | md | views/4_Methods.py:736 | tab The Model |
| TOM-UI-260 | Methods | table | Further deaths parts (markdown): Part, What is counted in 2031-2035 | md | views/4_Methods.py:751 | tab The Model |
| TOM-UI-261 | Methods | section | Uncertainty (icon casino) | th.section_header | views/4_Methods.py:772 | tab The Model |
| TOM-UI-262 | Methods | section | Data Sources > Datasets (icon database) | th.section_header | views/4_Methods.py:789 | tab Data Sources |
| TOM-UI-263 | Methods | table | Datasets (markdown): Dataset, Provider and version, Variables used, Used in | md | views/4_Methods.py:791 | tab Data Sources |
| TOM-UI-264 | Methods | section | World Development Indicators Used (icon table_chart) | th.section_header | views/4_Methods.py:815 | tab Data Sources |
| TOM-UI-265 | Methods | table | WDI (markdown): Code, Meaning, Used for | md | views/4_Methods.py:819 | tab Data Sources |
| TOM-UI-266 | Methods | section | Published Studies Behind the Parameters (icon menu_book) | th.section_header | views/4_Methods.py:841 | tab Data Sources |
| TOM-UI-267 | Methods | section | Assumptions & Limitations > Values That Are Assumptions (icon rule) | th.section_header | views/4_Methods.py:869 | tab Assumptions & Limitations |
| TOM-UI-268 | Methods | table | Assumptions: index Label; columns Central, Low, High, Unit, Source | page body (st.table) | views/4_Methods.py:872 | tab Assumptions & Limitations |
| TOM-UI-269 | Methods | heading | run-in bold: "Unverified review figures" | md | views/4_Methods.py:876 | conditional: any parameter with status unverified |
| TOM-UI-270 | Methods | table | Unverified: index Label; columns Central, Low, High, Unit, Source | page body (st.table) | views/4_Methods.py:878 | conditional: as above |
| TOM-UI-271 | Methods | section | Limitations (icon report) | th.section_header | views/4_Methods.py:891 | tab Assumptions & Limitations |
| TOM-UI-272 | Methods | section | Parameters > Every Model Parameter (icon tune) | th.section_header | views/4_Methods.py:920 | tab Parameters |
| TOM-UI-273 | Methods | table | Every Model Parameter: index Param; columns Label, Central, Low, High, Unit, Status, Source | page body (st.table) | views/4_Methods.py:924 | tab Parameters |
| TOM-UI-274 | Methods | section | Regression Estimates (icon functions) | th.section_header | views/4_Methods.py:925 | tab Parameters |
| TOM-UI-275 | Methods | table | Regression Estimates: index Regression; columns Outcome, Main Regressor, Coefficient, Standard Error, Countries, Observations, Years | page body (st.table) | views/4_Methods.py:935 | tab Parameters |
| TOM-UI-276 | Methods | section | Cross-Checks > Cross-Checks for the Current Selection (icon fact_check) | th.section_header | views/4_Methods.py:944 | tab Cross-Checks |
| TOM-UI-277 | Methods | caption/text block | "{country} · {scenario title} · {response}[ · Death Rates Held Constant]" | page body | views/4_Methods.py:945 | tab Cross-Checks |
| TOM-UI-278 | Methods | heading | What 20 Years of Data Say (st.subheader) | page body | views/4_Methods.py:950 | tab Cross-Checks |
| TOM-UI-279 | Methods | caption/text block | Cross-check summary "Panel regressions across up to N countries ... imply about N extra deaths ... against M from the unit-cost model ..." | ms._crosscheck_summary | views/4_Methods.py:951 (model_section.py:1905) | tab Cross-Checks |
| TOM-UI-280 | Methods | heading | Does This Match Published Estimates? (markdown h4) | ms._published_estimates | model_section.py:1950 | tab Cross-Checks |
| TOM-UI-281 | Methods | caption/text block | "The current scenario cuts no aid, so there is nothing to compare." (st.info) | ms._published_estimates | model_section.py:1952 | conditional: no country loses aid |
| TOM-UI-282 | Methods | table | Published estimates: index Study (Cavalcanti et al., Lancet 2025; ten Brink et al., Lancet HIV 2025; Gavi (2000-2024)); columns What It Covers, Published, This Model (Current Scenario) | ms._published_estimates | model_section.py:1956-1972 | conditional: some country loses aid |
| TOM-UI-283 | Methods | caption/text block | "The published studies cover more causes, programs, countries or years than this model ..." | ms._published_estimates | model_section.py:1973 | conditional: some country loses aid |
| TOM-UI-284 | Methods | section | Validation Against External Benchmarks (icon rule) + bullet list HIV vs Optima HIV, People on ART, TB, Malaria, Vaccines, Context | th.section_header / md | views/4_Methods.py:955-987 | tab Cross-Checks |

---

### (A) Deaths / lives displays

Result columns referenced: per-country run `res` from `hm.run_country` (health_model.py:1295-1311): `totals.deaths_5y`, `totals.deaths_5y_lo/_hi`, `totals.deaths_y1`, `committed.deaths`, `committed.after_2030`, `committed.after_2030_lo/_hi`, `committed.after_parts`, `committed.after_2030_reengage`, `committed.reengage_values`; `buckets.deaths_5y`, `buckets.deaths_5y_lo/_hi`, `buckets.infections_5y(_lo/_hi)`; `lines.deaths_5y`, `lines.deaths_5y_lo/_hi` (health_model.py:1227-1230); `path` (deaths per year by bucket). All-country frame from `hm.run_all` / precomputed CSV: `deaths_5y`, `deaths_y1`, `deaths_5y_{HIV,TB,Malaria,Immunization}`, `deaths_after_2030`, `deaths_after_2030_reengage_min/_max`, `hiv_infections_5y`, per-draw totals via `hm.total_range`.

| # | Where | What is shown | Function | file:line | Columns read |
|---|---|---|---|---|---|
| A1 | Dashboard lede | Headline "... the model estimates about {N} more deaths in {country} in 2026-2030 ..." (rounded to 2 s.f. by approx_words) | story_lede | model_section.py:716, 729-734 | totals.deaths_5y, totals.replaced, totals.gross |
| A2 | Dashboard lede | Dek "Most / The largest share would come from {cause phrase}" | story_lede | model_section.py:735-738 | buckets.deaths_5y (idxmax, share of totals.deaths_5y) |
| A3 | Dashboard lede | Big number "Extra Deaths, 2026-2030" + note "range ... · +N more in 2031-2035 (assumption-driven)" + tooltip | story_lede / after_2030_help | model_section.py:758-762, 923 | totals.deaths_5y, deaths_5y_lo/_hi, committed.after_2030, committed.after_parts |
| A4 | Dashboard section header | "How Aid Cuts Translate into Coverage and Lives in {country}" + INTRO tooltip (extra deaths) | render_model_section | model_section.py:773, 537 | text only |
| A5 | Dashboard outcome panel | Pills "Extra Deaths 2026-2030", "Further Deaths, 2031-2035, Set in Motion by 2030 (Assumption-Driven)", "Deaths Avoided vs Sudden Cut With No Response"; outcome sentence "avoids about N of the M deaths" | paths_ui.outcome_panel | paths_ui.py:243-277 | totals.deaths_5y(_lo/_hi); committed.deaths, after_2030(_lo/_hi), after_2030_reengage, reengage_values; base run committed.deaths (model_section.py:554-557) |
| A6 | Dashboard The Numbers | Pills "Further Deaths, 2031-2035 (Assumption-Driven)", "Extra Deaths Over 5 Years", "New HIV Infections, 5 Years" | _headline_items | model_section.py:996-1005 | committed.after_2030(_lo/_hi), after_2030_reengage, reengage_values; totals.deaths_5y(_lo/_hi); buckets HIV infections_5y(_lo/_hi) |
| A7 | Dashboard | "Government replacement of {$} a year averts about N deaths over 5 years ... ({$} per death averted)" | _country_results | model_section.py:809-814 | res0.totals.deaths_5y - res.totals.deaths_5y; totals.replaced |
| A8 | Dashboard comparison | "Scenario B averts/adds about N extra deaths ..." + chart "Extra Deaths by Disease" + per-scenario pill grids | _comparison | model_section.py:1027-1041 | totals.deaths_5y (A and B), buckets.deaths_5y |
| A9 | Dashboard cards | "Extra Deaths Over 5 Years" per disease; foot "about {$} of aid lost per life lost" (= 5e6 / deaths); "No {disease} deaths modelled" | _per_million_cards / _card_html | model_section.py:1071-1086, 1099-1100 | hm.per_million_card(...)["deaths_5y"] (health_model.py:291 = buckets.deaths_5y scaled) |
| A10 | Dashboard | "What Each Service Loses" column "Extra Deaths, 5 Years Total" + Total row + help text + caption on deaths range | _service_table_html | model_section.py:1298-1307, 1337, 865, 868 | lines.deaths_5y, deaths_5y_lo/_hi; totals.deaths_5y_lo/_hi (see B) |
| A11 | Dashboard | "An even 10% cut to {bucket} aid adds about N extra deaths over 5 years." | _country_results | model_section.py:893-894 | hm.dose_response deaths_5y (interp at 10%) |
| A12 | Dashboard | Chart "Extra Deaths as More Aid Is Cut" (band, even-cut line, dashed scenario line, dot) | _dose_fig | model_section.py:899, 1376-1419 | dose_response cut, deaths_5y, lo, hi, net_loss_usd, cov_drop_pp; _scenario_path deaths_5y; buckets.deaths_5y, gross_loss_usd, base_usd |
| A13 | Dashboard | Chart "Extra Deaths Each Year" | _path_fig | model_section.py:901, 1422-1433 | res["path"][HIV/TB/Malaria/Immunization] |
| A14 | Dashboard | "How the Damage Scales" help text; source note "where each dollar saves more lives" | _country_results | model_section.py:879-883, 905-909 | text only |
| A15 | Dashboard | "Lives first": Advanced radio "Where Replacement Money Goes" option "Hypothetical Best Case (Triage)" (key m_alloc; internal value `lives_first`) and Scenario B radio (mb_alloc, default triage); response label suffix ", Hypothetical Best Case (Triage)" in model-section caption, All Countries caption, Validation captions, Methods Cross-Checks caption; tooltip of "New HIV Infections, 5 Years" ("refills treatment and vaccines first ...") | _controls / _resp_label / _headline_items | model_section.py:67-68, 459-463, 490-492, 286, 774, 1004; views/3_Validation.py:48, 215; views/4_Methods.py:945 | fiscal_t alloc |
| A16 | All Countries | Pills "Further Deaths, 2031-2035 (Assumption-Driven)" (or fallback "Extra Deaths, Year 1"), "Extra Deaths Over 5 Years", "New HIV Infections, 5 Years" | cross_country | model_section.py:1753-1778 | deaths_after_2030, deaths_after_2030_reengage_min/_max, total_range(deaths_after_2030); deaths_y1; deaths_5y + total_range(deaths_5y); hiv_infections_5y |
| A17 | All Countries | Map "Extra Deaths per 100,000 People" (z) with hover deaths and new infections | _world_map | model_section.py:1779, 1862-1899 | deaths_per_100k = deaths_5y / pop x 1e5; deaths_5y; hiv_infections_5y |
| A18 | All Countries | Scatter "Budget Exposure vs. Deaths" (y = deaths per 100,000; labels = top 8 by deaths per 100,000) | cross_country | model_section.py:1789-1833 | deaths_per_100k, deaths_5y |
| A19 | All Countries | Bar "Most Extra Deaths, 5 Years" (top 15 ranked by deaths_5y; note "ranks r of n") | cross_country | model_section.py:1835-1858 | deaths_5y_{bucket}, deaths_5y |
| A20 | Validation | Table "Model: Extra Deaths Over 5 Years, All {n} Countries" | page body | views/3_Validation.py:56-69 | precomputed deaths_5y_{bucket}, deaths_5y, total_range(deaths_5y) |
| A21 | Validation | Table "Published Estimates" (Closest Model Figure column) | page body | views/3_Validation.py:74-110 | deaths_5y_{bucket}/5, deaths_5y, deaths_5y_HIV; ms.deaths_per_child_immunised (model_section.py:1924) |
| A22 | Validation | Chart "Extra Deaths by Method", "**Reading:**" sentence, table "Estimates by Method" (+ help with HIV baseline deaths) | page body / _reading | views/3_Validation.py:221-318 | buckets.deaths_5y(_lo/_hi); hm.poisson_projection deaths_5y(_lo/_hi); hm.lancet_projection deaths_5y; ci hiv_deaths_unaids / hiv_deaths_est |
| A23 | Validation | Malaria pills "Baseline Malaria Deaths, Dashboard Countries", "WHO Global Malaria Deaths, 2024", "Share Covered by the Dashboard"; Pakistan caption (baseline deaths) | page body | views/3_Validation.py:175-207 | ci malaria_deaths (input, not model output) |
| A24 | Validation | "Our Poisson Regressions" (TB Deaths, Under-5 Deaths, Child Malaria Deaths) + caption | page body | views/3_Validation.py:349-359 | regressions.json |
| A25 | Methods Cross-Checks | "What 20 Years of Data Say" summary ("imply about N extra deaths ... against M from the unit-cost model") | _crosscheck_summary | views/4_Methods.py:951; model_section.py:1905-1921 | hm.statistical_crosscheck deaths_5y, mech_deaths_5y |
| A26 | Methods Cross-Checks | "Does This Match Published Estimates?" table | _published_estimates | model_section.py:1949-1979 | deaths_5y, total_range(deaths_5y), deaths_5y_HIV, deaths per child |
| A27 | Methods text | Overview step "4. **Lives**"; Section 4 Outputs rows (Further Deaths, Extra Deaths Over 5 Years, US$1M cards "per life lost", What Each Service Loses, Extra Deaths as More Aid Is Cut, Extra Deaths Each Year, All Countries deaths per 100,000); Step 2 "Where replacement money goes" (triage); Step 4: Lives (Extra Deaths) whole section; Committed deaths / Deaths avoided / Break-even; Uncertainty; Validation Against External Benchmarks; u5-share table "Countries With Malaria Deaths"; Data Years row "Malaria deaths (baseline)" | md / tables | views/4_Methods.py:105, 254-268, 407-410, 510-690, 746-765, 772-783, 955-987, 603, 150 | text / params |
| A28 | Not shown | Country Brief "Extra Deaths Over 5 Years" cards and headline | _brief_html | model_section.py:1985-2038 | not shown (SHOW_BRIEF = False) |

### (B) Service-by-service table with lives (deaths) saved

- **Name on screen:** "What Each Service Loses" (st.subheader with help tooltip, model_section.py:865). Table rendered by `st.html(_service_table_html(rows, country_name, T, gains))` at model_section.py:866; builder `_service_table_html` model_section.py:1264-1341; row prep `_service_rows` model_section.py:1219-1239; data `show = L[(L["base_usd"] > 0) | (L["net_loss_usd"] != 0)]` model_section.py:796 where L = `res["lines"]` (central run of `hm.run_country`).
- **Where on the page:** Dashboard, inside "How Aid Cuts Translate into Coverage and Lives in {country}", after "Where the Money Is Lost" and before the "Coverage Lost, by Service" chart and "How the Damage Scales". Shown when the country is modelled.
- **Rows:** one per service line, grouped by disease (HIV, TB, Malaria, Immunization; order LINE_ORDER model_section.py:1201), Orphans & Vulnerable Children dropped. Names (LINE_SHORT model_section.py:1188): HIV Treatment; HIV Testing & Care; Mother-to-Child Transmission; HIV Prevention; TB Treatment; Drug-Resistant TB; Bednets; Indoor Spraying; Malaria Treatment; Routine Immunization (each with a grey detail line). Grey gap row between diseases; optional "Aid to {disease} rises by {$} in this scenario; gains aren't modelled." row (_gain_rows, 1344); optional **Other Aid** row ("orphan support; systems money not cutting services"); **Total** row.
- **Columns (header text / grey sub-line) and how computed:**

| Column | Per-row value | Other Aid row | Total row |
|---|---|---|---|
| Service | name + detail; coloured left border by bucket | "Other Aid" | "Total" |
| Donor Aid Now / "per year" | money(lines.base_usd) | T.base - sum(rows.base_usd) | T.base if T given, else sum(rows.base_usd) |
| Aid Lost / "per year, after government replacement" | money(lines.net_loss_usd) | T.net - sum(rows.net_loss_usd) | T.net if T given, else sum(rows.net_loss_usd) |
| Cost per Person | money(lines.unit_cost) + unit ("per {UNIT_SINGULAR}", PMTCT "per woman per year, including her ART"); "–" for HIV Testing & Care | blank | blank |
| People Losing Service, per Year | num(lines.units_lost) (central-run yearly average) + grey "{num(units_lost_5y)} over 5 years"; HIV Treatment instead shows "people who stop ART: full-cost equivalents of the lost money; mostly the same people each year"; "Not Modelled" if 0 and no coverage; "–" for HIV Testing & Care | "Not Modelled" | sum(rows.units_lost) excluding hiv_prev (HIV Testing & Care has NaN/0) |
| Coverage | cov_pair(cov0, after) e.g. "66% → 65%" + "(source)" + drop "−6.6 pts", where after = cov0 - cov_drop_pp/100 (clipped 0-1), shown when need > 0, cov0 known, cov_drop_pp finite; HIV Prevention "No Single Target Group"; otherwise "Not Modelled"; HIV Testing & Care "–" | blank | blank |
| Extra Deaths, 5 Years Total | bold num(lines.deaths_5y) + grey "{lo} to {hi}" from lines.deaths_5y_lo/_hi; HIV Prevention with deaths < 0.5 shows "See New Infections" (tooltip); "~0" (tooltip) when deaths_5y_hi = 0 and net loss > 0; HIV Testing & Care shows "In HIV Treatment" (tooltip care_ct_tip) | "Not Modelled" | bold num(sum(rows.deaths_5y)) (sum of the shown rows' central deaths) + grey range = T.deaths_5y_lo to T.deaths_5y_hi (the run's own total range, not a sum of row ranges); without T, sum of row lo / hi |

- Note: there is no "lives saved" column as such; the table shows **extra deaths** per service (lives lost). Lives saved appear only as "averts about N deaths" (A7), "Deaths Avoided vs Sudden Cut" (A5) and the Scenario B comparison (A8).

### (C) Coverage / service graphs and tables

| # | Name as shown | Kind | Function | file:line | Data |
|---|---|---|---|---|---|
| C1 | Coverage Lost, by Service (subtitle "Percentage Points; Coverage Before → After") | chart (horizontal bars, one per service, row label "Name / cov0 → after (source)", bar text "−x.x pts") | _coverage_fig | model_section.py:873-876, 1353-1373 | rows with cov_ok and drop > 0: drop = (cov0 - after) x 100 from lines.cov0, cov_drop_pp, cov_source; hidden when no service loses coverage |
| C2 | What Each Service Loses: "People Losing Service, per Year" and "Coverage" columns | table | _service_table_html | model_section.py:866, 1291-1314 | lines.units_lost, units_lost_5y, cov0, cov_drop_pp, need |
| C3 | Lede big numbers "Treatment Lost Each Year" / "Prevention Lost Each Year" | card/metric | story_lede / care_split | model_section.py:745-757, 639-648 | lines.units_lost for hiv_art, hiv_pmtct, tb_ds, tb_dr, mal_cm / mal_itn, mal_irs, imm |
| C4 | Cards "People Losing the Main Service", "Coverage Drop (Percentage Points)" | card/metric | _per_million_cards | model_section.py:1076-1080, 1096-1098 | per_million_card people, cov_drop_pp |
| C5 | Extra Deaths as More Aid Is Cut: hover "coverage -x.x percentage points" | chart (hover only) | _dose_fig | model_section.py:1386-1389 | dose_response cov_drop_pp |
| C6 | Validation: Lines Where Donor Money Exceeds the Modelled Service Cost (pills + Service/Countries table) | card/metric, table | page body | views/3_Validation.py:126-144 | hm.donor_cost_excess |
| C7 | Validation: People on ART Paid for by Donors (pills) | card/metric | page body | views/3_Validation.py:155-166 | hm.donor_funded_on_art |
| C8 | Validation: Malaria input comparison (treatment / bednet coverage before vs now) | table | ms.malaria_input_comparison | views/3_Validation.py:184-185 | ci coverage inputs |
| C9 | Methods: Step 3: Coverage (Who Loses a Service) text, LaTeX, Cost per person and People in need tables | text / table | md | views/4_Methods.py:413-508 | text |
| C10 | Not present | No chart of coverage over time or of people losing services by year exists on this branch; Treatment/Prevention lost and People Losing Service are yearly averages; the 5-year people total is only a grey sub-line in the service table. `care_breakdown` (model_section.py:630) and `CARE_TIP` (model_section.py:626) are defined but never rendered. | | | |

### Other things defined but not shown

- `SHOW_BRIEF = False` (model_section.py:49): "Download Country Brief" button and `_brief_html` page.
- `care_breakdown` (model_section.py:630) and `CARE_TIP` (model_section.py:626): not called.
- Methods text (views/4_Methods.py:501) mentions malaria flag "columns ... in the All Countries download"; there is **no** download control on the All Countries page in this branch.
- Story lede docstring says "three big numbers" (model_section.py:699) but four are rendered.
- In this branch the Dashboard "Where the Aid Is Spent" grouping label is "All other" (ALL_OTHER, views/1_Dashboard.py:514), shown as "All Other".


### Counts per Kind

| Kind | Count |
|---|---|
| section | 39 |
| heading | 37 |
| chart | 17 |
| table | 32 |
| card/metric | 49 |
| control | 21 |
| preset | 4 |
| tooltip-bearing control | 16 |
| caption/text block | 66 |
| download | 1 |
| expander | 1 |
| tab | 1 |
| **Total** | **284** |

| Page | Rows |
|---|---|
| Dashboard | 149 |
| All Countries | 16 |
| Validation | 48 |
| Methods | 71 |

Notes on counting: one row can stand for a group of identical widgets (e.g. the 5 "Aid Cut" year sliders, the 4 channel-cut sliders, the 4 per-disease cards) or several run-in bold labels in one Methods block; options lists are counted under preset. Section (A), (B), (C) entries are cross-references and are not counted again.


## 4. Model functions, parameters, inputs, tests and checks


### Model and UI functions, classes and module constants

main 544, tomato 506, on both 463, main only 81, tomato only 43.

| Item | main | tomato |
|---|---|---|
| `add_constant_dollars.py::ANCHOR_YEAR (constant)` | yes | yes |
| `add_constant_dollars.py::GDP_FILE (constant)` | yes | yes |
| `add_constant_dollars.py::ROOT (constant)` | yes | yes |
| `add_constant_dollars.py::SPEND_FILE (constant)` | yes | yes |
| `add_constant_dollars.py::main` | yes | yes |
| `announcement_model/project_cuts.py::AREAS (constant)` | yes | **no** |
| `announcement_model/project_cuts.py::AREA_COLS (constant)` | yes | **no** |
| `announcement_model/project_cuts.py::B (constant)` | yes | **no** |
| `announcement_model/project_cuts.py::BIG (constant)` | yes | **no** |
| `announcement_model/project_cuts.py::D (constant)` | yes | **no** |
| `announcement_model/project_cuts.py::E (constant)` | yes | **no** |
| `announcement_model/project_cuts.py::EXIT (constant)` | yes | **no** |
| `announcement_model/project_cuts.py::F_AVG (constant)` | yes | **no** |
| `announcement_model/project_cuts.py::GAVI_WIDE (constant)` | yes | **no** |
| `announcement_model/project_cuts.py::HERE (constant)` | yes | **no** |
| `announcement_model/project_cuts.py::KEY (constant)` | yes | **no** |
| `announcement_model/project_cuts.py::KN (constant)` | yes | **no** |
| `announcement_model/project_cuts.py::M (constant)` | yes | **no** |
| `announcement_model/project_cuts.py::M_ (constant)` | yes | **no** |
| `announcement_model/project_cuts.py::N (constant)` | yes | **no** |
| `announcement_model/project_cuts.py::NG (constant)` | yes | **no** |
| `announcement_model/project_cuts.py::NONDAC (constant)` | yes | **no** |
| `announcement_model/project_cuts.py::NORDIC (constant)` | yes | **no** |
| `announcement_model/project_cuts.py::NY (constant)` | yes | **no** |
| `announcement_model/project_cuts.py::OUTDIR (constant)` | yes | **no** |
| `announcement_model/project_cuts.py::P (constant)` | yes | **no** |
| `announcement_model/project_cuts.py::PM (constant)` | yes | **no** |
| `announcement_model/project_cuts.py::SHAPE3 (constant)` | yes | **no** |
| `announcement_model/project_cuts.py::SHAPE5 (constant)` | yes | **no** |
| `announcement_model/project_cuts.py::T (constant)` | yes | **no** |
| `announcement_model/project_cuts.py::UK_AFRICA (constant)` | yes | **no** |
| `announcement_model/project_cuts.py::W (constant)` | yes | **no** |
| `announcement_model/project_cuts.py::X (constant)` | yes | **no** |
| `announcement_model/project_cuts.py::YRS (constant)` | yes | **no** |
| `announcement_model/project_cuts.py::chan_grp` | yes | **no** |
| `announcement_model/project_cuts.py::fit_grp` | yes | **no** |
| `announcement_model/project_cuts.py::health_path` | yes | **no** |
| `announcement_model/project_cuts.py::latest` | yes | **no** |
| `announcement_model/project_cuts.py::oda_path` | yes | **no** |
| `announcement_model/project_cuts.py::rule_for` | yes | **no** |
| `announcement_model/project_cuts.py::spread` | yes | **no** |
| `announcement_model/project_cuts.py::src_grp` | yes | **no** |
| `batch34_inputs.py::CATS (constant)` | yes | yes |
| `batch34_inputs.py::CI_PATH (constant)` | yes | yes |
| `batch34_inputs.py::DISEASES (constant)` | yes | yes |
| `batch34_inputs.py::EV (constant)` | yes | yes |
| `batch34_inputs.py::ROOT (constant)` | yes | yes |
| `batch34_inputs.py::apply_art` | yes | yes |
| `batch34_inputs.py::apply_art_full` | yes | yes |
| `batch34_inputs.py::apply_art_full56` | **no** | yes |
| `batch34_inputs.py::apply_donor` | yes | yes |
| `batch34_inputs.py::apply_donor56_hiv_imm` | **no** | yes |
| `batch34_inputs.py::apply_donor56_malaria` | **no** | yes |
| `batch34_inputs.py::apply_flags` | **no** | yes |
| `batch34_inputs.py::apply_shares` | yes | yes |
| `batch34_inputs.py::apply_tb` | yes | yes |
| `batch34_inputs.py::apply_vaccines` | **no** | yes |
| `batch34_inputs.py::main` | yes | yes |
| `budget_section.py::CENTRAL_ABOVE_WEO (constant)` | yes | yes |
| `budget_section.py::DIFFERENT_LEVELS (constant)` | yes | yes |
| `budget_section.py::OTHER_LEVELS (constant)` | yes | yes |
| `budget_section.py::SUM_TOL (constant)` | yes | yes |
| `budget_section.py::_side` | yes | yes |
| `budget_section.py::budget_boxes` | yes | yes |
| `budget_section.py::coverage_level` | yes | yes |
| `budget_section.py::side_box_sum` | yes | yes |
| `budget_section.py::spending_shares` | yes | yes |
| `build_sections.py::DAH (constant)` | **no** | yes |
| `build_sections.py::EXPECTED (constant)` | **no** | yes |
| `build_sections.py::HERE (constant)` | **no** | yes |
| `build_sections.py::SPEND (constant)` | **no** | yes |
| `build_sections.py::SPEND_COLS (constant)` | **no** | yes |
| `build_sections.py::build_country_data` | **no** | yes |
| `build_sections.py::build_spending_data` | **no** | yes |
| `build_sections.py::compare` | **no** | yes |
| `build_sections.py::country_iso_map` | **no** | yes |
| `build_sections.py::main` | **no** | yes |
| `country_lists.py::ALLOWED_COUNTRIES (constant)` | yes | yes |
| `country_lists.py::dropdown_countries` | yes | yes |
| `fiscal_inputs.py::API (constant)` | yes | yes |
| `fiscal_inputs.py::CODES (constant)` | yes | yes |
| `fiscal_inputs.py::DOWNLOADED (constant)` | yes | yes |
| `fiscal_inputs.py::HERE (constant)` | yes | yes |
| `fiscal_inputs.py::IMF_LABEL (constant)` | yes | yes |
| `fiscal_inputs.py::INPUTS_FILE (constant)` | yes | yes |
| `fiscal_inputs.py::OUT (constant)` | yes | yes |
| `fiscal_inputs.py::OUT_DIR (constant)` | yes | yes |
| `fiscal_inputs.py::RAW (constant)` | yes | yes |
| `fiscal_inputs.py::SOURCE (constant)` | yes | yes |
| `fiscal_inputs.py::WB_LABEL (constant)` | yes | yes |
| `fiscal_inputs.py::apply` | yes | yes |
| `fiscal_inputs.py::download` | yes | yes |
| `fiscal_inputs.py::first_estimate_year` | yes | yes |
| `fiscal_inputs.py::imf_latest` | yes | yes |
| `fiscal_inputs.py::main` | yes | yes |
| `fiscal_inputs.py::process` | yes | yes |
| `fiscal_inputs.py::weo_nominal_growth` | **no** | yes |
| `health_model.py::ABUJA_CEILING (constant)` | yes | yes |
| `health_model.py::AID_BASE_YEARS (constant)` | yes | yes |
| `health_model.py::ALL_DIRECT (constant)` | yes | yes |
| `health_model.py::ANNOUNCE_FILE (constant)` | yes | **no** |
| `health_model.py::ART_HAZARD (constant)` | yes | yes |
| `health_model.py::ART_HAZARD_LEGACY (constant)` | yes | yes |
| `health_model.py::ART_INFECT_LAG (constant)` | yes | yes |
| `health_model.py::ART_MULT_UP (constant)` | yes | yes |
| `health_model.py::ART_REENGAGE_LEGACY (constant)` | yes | yes |
| `health_model.py::ART_TRANSMISSION_FALLBACK (constant)` | yes | yes |
| `health_model.py::BUCKETS (constant)` | yes | yes |
| `health_model.py::BUCKET_COLORS (constant)` | yes | yes |
| `health_model.py::CPI_U (constant)` | yes | yes |
| `health_model.py::DIRECT (constant)` | yes | yes |
| `health_model.py::DIRECT_CHANNELS (constant)` | yes | yes |
| `health_model.py::DONOR_SHARE_LINE (constant)` | yes | yes |
| `health_model.py::DONOR_SHARE_TAG (constant)` | yes | yes |
| `health_model.py::FALLBACK_MORTALITY_TREND (constant)` | yes | yes |
| `health_model.py::FULL_LINE_BUCKET (constant)` | yes | yes |
| `health_model.py::Fiscal` | yes | yes |
| `health_model.py::GHES_YEAR (constant)` | yes | yes |
| `health_model.py::HEALTH_SHARE_FILE (constant)` | yes | yes |
| `health_model.py::HERE (constant)` | yes | yes |
| `health_model.py::HIV_WEIBULL_SHAPE (constant)` | yes | yes |
| `health_model.py::HSS (constant)` | yes | yes |
| `health_model.py::IMM_LAGS (constant)` | **no** | yes |
| `health_model.py::LAG (constant)` | yes | yes |
| `health_model.py::LANCET_BASELINE (constant)` | yes | yes |
| `health_model.py::LANCET_FUNDING (constant)` | yes | yes |
| `health_model.py::LANCET_RR (constant)` | yes | yes |
| `health_model.py::LINE_BUCKET (constant)` | yes | yes |
| `health_model.py::LINE_LABELS (constant)` | yes | yes |
| `health_model.py::LINKED (constant)` | yes | yes |
| `health_model.py::LINKED_IN (constant)` | yes | yes |
| `health_model.py::MALARIA_U5_SHARE_FALLBACK (constant)` | yes | yes |
| `health_model.py::MODEL_DIR (constant)` | yes | yes |
| `health_model.py::MONEY_LINES (constant)` | yes | yes |
| `health_model.py::N_YEARS (constant)` | yes | yes |
| `health_model.py::PARAMS_FILE (constant)` | yes | yes |
| `health_model.py::PEPFAR_ON_ART (constant)` | yes | yes |
| `health_model.py::POISSON_SPECS (constant)` | yes | yes |
| `health_model.py::POLICY_RAMP (constant)` | yes | **no** |
| `health_model.py::POST_YEARS (constant)` | yes | yes |
| `health_model.py::PRICE_YEAR (constant)` | yes | yes |
| `health_model.py::SOURCE_GROUPS (constant)` | yes | yes |
| `health_model.py::STAT_SPECS (constant)` | yes | yes |
| `health_model.py::Scenario` | yes | yes |
| `health_model.py::TAX_BENCHMARK (constant)` | yes | **no** |
| `health_model.py::TREAT_SHARE (constant)` | yes | **no** |
| `health_model.py::TREND_COLUMNS (constant)` | yes | yes |
| `health_model.py::UC_REF_FILE (constant)` | yes | yes |
| `health_model.py::UNIT_LABELS (constant)` | yes | yes |
| `health_model.py::UNIT_SINGULAR (constant)` | yes | yes |
| `health_model.py::UNSPEC (constant)` | yes | yes |
| `health_model.py::UNSPEC_PREV (constant)` | yes | yes |
| `health_model.py::UNSPEC_TAG (constant)` | yes | yes |
| `health_model.py::UNSPEC_TEST_TARGET (constant)` | yes | yes |
| `health_model.py::UNSPEC_TREAT (constant)` | yes | yes |
| `health_model.py::YEAR0 (constant)` | yes | **no** |
| `health_model.py::_announcement_cuts_default` | yes | **no** |
| `health_model.py::_money_by_year` | yes | yes |
| `health_model.py::_path` | yes | yes |
| `health_model.py::_series` | yes | yes |
| `health_model.py::_share_history` | yes | yes |
| `health_model.py::_uc_ref` | yes | yes |
| `health_model.py::_units_lost` | yes | yes |
| `health_model.py::_v` | yes | yes |
| `health_model.py::announcement_lookup` | yes | **no** |
| `health_model.py::announcement_sources` | yes | **no** |
| `health_model.py::announcement_totals` | yes | **no** |
| `health_model.py::art_cohorts` | yes | yes |
| `health_model.py::break_even_share` | yes | yes |
| `health_model.py::budget_growth_factors` | **no** | yes |
| `health_model.py::coverage_source` | yes | yes |
| `health_model.py::donor_cost_excess` | yes | yes |
| `health_model.py::donor_funded_on_art` | yes | yes |
| `health_model.py::dose_response` | yes | yes |
| `health_model.py::draw_params` | yes | yes |
| `health_model.py::epi` | yes | yes |
| `health_model.py::fiscal_space` | yes | yes |
| `health_model.py::gov_add_from_points` | yes | yes |
| `health_model.py::health_budget` | yes | yes |
| `health_model.py::health_share` | yes | yes |
| `health_model.py::hiv_art_params` | yes | yes |
| `health_model.py::hiv_death_timing` | yes | yes |
| `health_model.py::imm_legacy` | **no** | yes |
| `health_model.py::imm_per_child` | **no** | yes |
| `health_model.py::income_group` | yes | yes |
| `health_model.py::inflate` | yes | yes |
| `health_model.py::known_loss_by_year` | yes | **no** |
| `health_model.py::lancet_log_rr` | yes | yes |
| `health_model.py::lancet_projection` | yes | yes |
| `health_model.py::load_announcement_cuts` | yes | **no** |
| `health_model.py::load_inputs` | yes | yes |
| `health_model.py::load_params` | yes | yes |
| `health_model.py::malaria_deaths` | yes | yes |
| `health_model.py::malaria_levels` | yes | yes |
| `health_model.py::malaria_u5_share` | yes | yes |
| `health_model.py::malaria_u5_share_country_series` | yes | yes |
| `health_model.py::mortality_trend_factors` | yes | yes |
| `health_model.py::per_million_card` | yes | yes |
| `health_model.py::per_unit_deaths` | yes | yes |
| `health_model.py::per_unit_levels` | yes | yes |
| `health_model.py::poisson_projection` | yes | yes |
| `health_model.py::policy_money` | yes | **no** |
| `health_model.py::run_all` | yes | yes |
| `health_model.py::run_country` | yes | yes |
| `health_model.py::statistical_crosscheck` | yes | yes |
| `health_model.py::tax_effort` | yes | **no** |
| `health_model.py::theta_historical` | yes | yes |
| `health_model.py::total_range` | yes | yes |
| `health_model.py::uniform_scenario` | yes | yes |
| `health_model.py::unit_costs` | yes | yes |
| `health_model.py::validate_params` | yes | yes |
| `hiv_transmission_inputs.py::COLS (constant)` | yes | yes |
| `hiv_transmission_inputs.py::MODEL_DIR (constant)` | yes | yes |
| `hiv_transmission_inputs.py::ROOT (constant)` | yes | yes |
| `hiv_transmission_inputs.py::UNAIDS_FILE (constant)` | yes | yes |
| `hiv_transmission_inputs.py::apply` | yes | yes |
| `hiv_transmission_inputs.py::main` | yes | yes |
| `hiv_transmission_inputs.py::unaids_rates` | yes | yes |
| `immunization_inputs.py::ANTIGENS (constant)` | **no** | yes |
| `immunization_inputs.py::BIRTH_YEARS (constant)` | **no** | yes |
| `immunization_inputs.py::HERE (constant)` | **no** | yes |
| `immunization_inputs.py::INPUTS_FILE (constant)` | **no** | yes |
| `immunization_inputs.py::SOURCE (constant)` | **no** | yes |
| `immunization_inputs.py::WPP_FILE (constant)` | **no** | yes |
| `immunization_inputs.py::WPP_SOURCE (constant)` | **no** | yes |
| `immunization_inputs.py::WUENIC_FILE (constant)` | **no** | yes |
| `immunization_inputs.py::apply` | **no** | yes |
| `immunization_inputs.py::apply_births` | **no** | yes |
| `immunization_inputs.py::main` | **no** | yes |
| `immunization_inputs.py::wuenic_latest` | **no** | yes |
| `immunization_inputs.py::wuenic_series` | **no** | yes |
| `malaria_inputs.py::DOWNLOAD_DATE (constant)` | yes | yes |
| `malaria_inputs.py::HERE (constant)` | yes | yes |
| `malaria_inputs.py::INPUTS_FILE (constant)` | yes | yes |
| `malaria_inputs.py::ITN_SURVEY_MIN_YEAR (constant)` | yes | yes |
| `malaria_inputs.py::MAL_CM_MIN_INCIDENCE (constant)` | yes | yes |
| `malaria_inputs.py::MAP_DIR (constant)` | yes | yes |
| `malaria_inputs.py::MAP_YEAR (constant)` | yes | yes |
| `malaria_inputs.py::RAW (constant)` | yes | yes |
| `malaria_inputs.py::RAW_DIR (constant)` | yes | yes |
| `malaria_inputs.py::SOURCE (constant)` | yes | yes |
| `malaria_inputs.py::TREND_CLIP (constant)` | yes | yes |
| `malaria_inputs.py::TREND_START (constant)` | yes | yes |
| `malaria_inputs.py::WHO_DEATHS_FILE (constant)` | yes | yes |
| `malaria_inputs.py::WHO_REGIONS_FILE (constant)` | yes | yes |
| `malaria_inputs.py::WMR_U5_REGIONS (constant)` | yes | yes |
| `malaria_inputs.py::_wdi_latest` | yes | yes |
| `malaria_inputs.py::apply` | yes | yes |
| `malaria_inputs.py::at_year` | yes | yes |
| `malaria_inputs.py::death_trend` | yes | yes |
| `malaria_inputs.py::irs_modelled` | yes | yes |
| `malaria_inputs.py::load` | yes | yes |
| `malaria_inputs.py::main` | yes | yes |
| `malaria_inputs.py::process` | yes | yes |
| `model_section.py::AFTER_2030_PARTS (constant)` | yes | yes |
| `model_section.py::ALLOCS (constant)` | yes | yes |
| `model_section.py::ALL_RANGE_TIP (constant)` | yes | yes |
| `model_section.py::ANNOUNCED_SHAPE (constant)` | yes | **no** |
| `model_section.py::ART_UNIT_NOTE (constant)` | yes | yes |
| `model_section.py::AVG_LABEL (constant)` | yes | **no** |
| `model_section.py::BUCKET_COLORS (constant)` | yes | yes |
| `model_section.py::BUCKET_WORD (constant)` | yes | yes |
| `model_section.py::CARDS_TITLE (constant)` | yes | yes |
| `model_section.py::CARD_FOOT_TIP (constant)` | yes | yes |
| `model_section.py::CARD_MAIN (constant)` | yes | yes |
| `model_section.py::CARE_LABELS (constant)` | yes | yes |
| `model_section.py::CARE_TIP (constant)` | yes | yes |
| `model_section.py::CAUSE_PHRASE (constant)` | yes | yes |
| `model_section.py::CEILINGS (constant)` | yes | yes |
| `model_section.py::CHAN_SHORT (constant)` | yes | yes |
| `model_section.py::COST_UNIT (constant)` | yes | yes |
| `model_section.py::COVERAGE_YEAR_COLS (constant)` | yes | yes |
| `model_section.py::DATA_YEARS (constant)` | yes | yes |
| `model_section.py::DISEASE_WORD (constant)` | yes | yes |
| `model_section.py::FIRST_YEAR (constant)` | yes | yes |
| `model_section.py::GOV_MODES (constant)` | yes | yes |
| `model_section.py::HSS_LINES (constant)` | yes | yes |
| `model_section.py::INTRO (constant)` | yes | yes |
| `model_section.py::LABEL_GAP_LOG (constant)` | yes | yes |
| `model_section.py::LINE_ORDER (constant)` | yes | yes |
| `model_section.py::LINE_SHORT (constant)` | yes | yes |
| `model_section.py::LIVES_FIRST (constant)` | yes | yes |
| `model_section.py::LOG_TICKS (constant)` | yes | yes |
| `model_section.py::MAIN_LINE (constant)` | yes | yes |
| `model_section.py::MAP_FOCUS (constant)` | yes | yes |
| `model_section.py::MAX_WHO_CUT_BARS (constant)` | yes | yes |
| `model_section.py::MOU (constant)` | yes | yes |
| `model_section.py::MOU_SHAPE (constant)` | yes | yes |
| `model_section.py::NO_DEATHS_REASON (constant)` | yes | yes |
| `model_section.py::NO_REPLACEMENT (constant)` | yes | yes |
| `model_section.py::PHASE_MAIN (constant)` | yes | **no** |
| `model_section.py::PHASE_OECD (constant)` | yes | **no** |
| `model_section.py::PHASE_OTHERS (constant)` | yes | **no** |
| `model_section.py::PRESET_SHORT (constant)` | yes | yes |
| `model_section.py::PREVENTION_LINES (constant)` | yes | yes |
| `model_section.py::PREVENTION_TIP (constant)` | yes | yes |
| `model_section.py::REENGAGE_TIP (constant)` | yes | yes |
| `model_section.py::REPLACED_ALPHA (constant)` | yes | yes |
| `model_section.py::SCATTER_LABELS (constant)` | yes | yes |
| `model_section.py::SCENARIO_PHRASE (constant)` | yes | yes |
| `model_section.py::SCOPE_NOTE (constant)` | yes | yes |
| `model_section.py::SHORTFALL_SLIDERS (constant)` | yes | yes |
| `model_section.py::SHOW_BRIEF (constant)` | yes | yes |
| `model_section.py::SHOW_GOV_OPTIONS (constant)` | yes | **no** |
| `model_section.py::SPELLED (constant)` | yes | yes |
| `model_section.py::SRC_MODEL (constant)` | yes | yes |
| `model_section.py::SRC_SHORT (constant)` | yes | yes |
| `model_section.py::TREATMENT_LINES (constant)` | yes | yes |
| `model_section.py::TREATMENT_TIP (constant)` | yes | yes |
| `model_section.py::WHO_MALARIA_DEATHS_2024 (constant)` | yes | yes |
| `model_section.py::WIDE (constant)` | yes | yes |
| `model_section.py::_KEEP (constant)` | yes | yes |
| `model_section.py::_SMALL (constant)` | yes | yes |
| `model_section.py::_all_country_results` | yes | yes |
| `model_section.py::_break_even` | yes | yes |
| `model_section.py::_brief_html` | yes | yes |
| `model_section.py::_card_html` | yes | yes |
| `model_section.py::_card_runs` | yes | yes |
| `model_section.py::_cards_html` | yes | yes |
| `model_section.py::_comparison` | yes | yes |
| `model_section.py::_controls` | yes | yes |
| `model_section.py::_country_results` | yes | yes |
| `model_section.py::_coverage_fig` | yes | yes |
| `model_section.py::_coverage_path_fig` | yes | **no** |
| `model_section.py::_crosscheck_summary` | yes | yes |
| `model_section.py::_default_params` | yes | yes |
| `model_section.py::_dose` | yes | yes |
| `model_section.py::_dose_fig` | yes | yes |
| `model_section.py::_drop_color` | yes | **no** |
| `model_section.py::_drop_overview_html` | yes | **no** |
| `model_section.py::_esc` | yes | yes |
| `model_section.py::_fiscal_panel` | yes | yes |
| `model_section.py::_fiscal_sentence` | yes | yes |
| `model_section.py::_gain_rows` | yes | yes |
| `model_section.py::_headline_items` | yes | yes |
| `model_section.py::_inputs` | yes | yes |
| `model_section.py::_layout` | yes | yes |
| `model_section.py::_loss_by_bucket_fig` | yes | yes |
| `model_section.py::_loss_layout` | yes | yes |
| `model_section.py::_model_years` | yes | **no** |
| `model_section.py::_money_lede` | yes | **no** |
| `model_section.py::_other_aid_sub` | yes | **no** |
| `model_section.py::_path_fig` | yes | yes |
| `model_section.py::_per_million_cards` | yes | yes |
| `model_section.py::_precomputed` | yes | yes |
| `model_section.py::_preset_options` | yes | yes |
| `model_section.py::_pts` | yes | yes |
| `model_section.py::_published_estimates` | yes | yes |
| `model_section.py::_resp_label` | yes | yes |
| `model_section.py::_response_phrase_short` | yes | yes |
| `model_section.py::_risk_source` | yes | **no** |
| `model_section.py::_run` | yes | yes |
| `model_section.py::_run_all` | yes | yes |
| `model_section.py::_scenario_path` | yes | yes |
| `model_section.py::_service_fig` | yes | **no** |
| `model_section.py::_service_grid` | yes | **no** |
| `model_section.py::_service_paths` | yes | **no** |
| `model_section.py::_service_rows` | yes | yes |
| `model_section.py::_service_table_html` | yes | yes |
| `model_section.py::_shortfall_sliders` | yes | yes |
| `model_section.py::_source_kind` | yes | yes |
| `model_section.py::_spread` | yes | **no** |
| `model_section.py::_stat_grid` | yes | yes |
| `model_section.py::_tc_part` | yes | yes |
| `model_section.py::_title` | yes | yes |
| `model_section.py::_visible` | yes | yes |
| `model_section.py::_who_cut_bars` | yes | yes |
| `model_section.py::_who_cut_fig` | yes | yes |
| `model_section.py::_world_map` | yes | yes |
| `model_section.py::_year_rows` | yes | **no** |
| `model_section.py::_yr_range` | yes | yes |
| `model_section.py::after_2030_help` | yes | yes |
| `model_section.py::announced_path` | yes | **no** |
| `model_section.py::approx_words` | yes | yes |
| `model_section.py::backfill_regression_text` | yes | yes |
| `model_section.py::budget_sliders` | yes | **no** |
| `model_section.py::budget_targets` | yes | **no** |
| `model_section.py::care_breakdown` | yes | yes |
| `model_section.py::care_ct_note` | yes | yes |
| `model_section.py::care_ct_tip` | yes | yes |
| `model_section.py::care_split` | yes | yes |
| `model_section.py::chart` | yes | yes |
| `model_section.py::cov_pair` | yes | yes |
| `model_section.py::cross_country` | yes | yes |
| `model_section.py::data_years_table` | yes | yes |
| `model_section.py::deaths_basis_text` | yes | yes |
| `model_section.py::deaths_per_child_immunised` | yes | yes |
| `model_section.py::donor_scenario_select` | yes | yes |
| `model_section.py::fiscal_gap_values` | yes | yes |
| `model_section.py::gains_note` | yes | yes |
| `model_section.py::health_share_pill` | yes | yes |
| `model_section.py::inputs_years_line` | yes | yes |
| `model_section.py::interest_text` | yes | yes |
| `model_section.py::known_vs_predicted_chart` | yes | **no** |
| `model_section.py::malaria_input_comparison` | yes | yes |
| `model_section.py::money` | yes | yes |
| `model_section.py::money_words` | yes | yes |
| `model_section.py::mou_fallback` | yes | yes |
| `model_section.py::net_aid_note` | yes | yes |
| `model_section.py::num` | yes | yes |
| `model_section.py::pct_smart` | yes | yes |
| `model_section.py::people_lost` | yes | **no** |
| `model_section.py::phase_out_by_donor` | yes | **no** |
| `model_section.py::phase_out_by_donor_chart` | yes | **no** |
| `model_section.py::pill_row` | yes | yes |
| `model_section.py::policy_caption` | yes | **no** |
| `model_section.py::preset_choices` | yes | yes |
| `model_section.py::reengage_range_text` | yes | yes |
| `model_section.py::render_model_section` | yes | yes |
| `model_section.py::response_kicker` | yes | yes |
| `model_section.py::response_phrase` | yes | yes |
| `model_section.py::risk_lines` | yes | **no** |
| `model_section.py::rng` | yes | yes |
| `model_section.py::round_words` | yes | yes |
| `model_section.py::run_ctl` | yes | yes |
| `model_section.py::scenario_bar` | yes | yes |
| `model_section.py::scenario_phrase` | yes | yes |
| `model_section.py::scenario_title` | yes | yes |
| `model_section.py::story_lede` | yes | yes |
| `model_section.py::systems_note` | yes | yes |
| `model_section.py::tc_fig` | yes | yes |
| `model_section.py::title_case` | yes | yes |
| `model_section.py::with_all_aid` | yes | **no** |
| `paths_ui.py::CUT_KEYS (constant)` | yes | yes |
| `paths_ui.py::DEFAULT_POINTS (constant)` | yes | yes |
| `paths_ui.py::GOV_KEYS (constant)` | yes | yes |
| `paths_ui.py::PATH_PHRASE (constant)` | yes | yes |
| `paths_ui.py::SUDDEN (constant)` | yes | yes |
| `paths_ui.py::YEARS (constant)` | yes | yes |
| `paths_ui.py::_chart` | yes | yes |
| `paths_ui.py::_fill_cut` | yes | yes |
| `paths_ui.py::_fill_gov` | yes | yes |
| `paths_ui.py::_fmt` | yes | yes |
| `paths_ui.py::_on_cut_slider` | yes | yes |
| `paths_ui.py::_on_gov_shape` | yes | yes |
| `paths_ui.py::_on_gov_slider` | yes | yes |
| `paths_ui.py::_on_shape` | yes | yes |
| `paths_ui.py::_reset` | yes | yes |
| `paths_ui.py::gradual_controls` | yes | yes |
| `paths_ui.py::mou_schedule_chart` | yes | yes |
| `paths_ui.py::outcome_panel` | yes | yes |
| `paths_ui.py::path_selector` | yes | yes |
| `paths_ui.py::year_panel` | yes | yes |
| `prepare_model.py::BASE_YEARS (constant)` | yes | yes |
| `prepare_model.py::BUCKET_TOTAL_COL (constant)` | yes | yes |
| `prepare_model.py::DASHBOARD_ISO3 (constant)` | yes | yes |
| `prepare_model.py::ENT_URL (constant)` | yes | yes |
| `prepare_model.py::EXT (constant)` | yes | yes |
| `prepare_model.py::HERE (constant)` | yes | yes |
| `prepare_model.py::HIV_SHARE_FILE (constant)` | yes | yes |
| `prepare_model.py::HIV_SHARE_URL (constant)` | yes | yes |
| `prepare_model.py::ISO3 (constant)` | yes | yes |
| `prepare_model.py::KFF_MOU_FILE (constant)` | yes | yes |
| `prepare_model.py::KFF_NAME_FIX (constant)` | yes | yes |
| `prepare_model.py::KFF_SOURCE (constant)` | yes | yes |
| `prepare_model.py::LINES (constant)` | yes | yes |
| `prepare_model.py::MOU_SCHEDULE_EXTRA (constant)` | yes | **no** |
| `prepare_model.py::OUT (constant)` | yes | yes |
| `prepare_model.py::SG (constant)` | yes | yes |
| `prepare_model.py::SG_URL (constant)` | yes | yes |
| `prepare_model.py::SOURCE_GROUPS (constant)` | yes | yes |
| `prepare_model.py::SSA (constant)` | yes | yes |
| `prepare_model.py::TREND_CLIP (constant)` | yes | yes |
| `prepare_model.py::TREND_YEARS (constant)` | yes | yes |
| `prepare_model.py::WB_REGIONS (constant)` | yes | yes |
| `prepare_model.py::WDI (constant)` | yes | yes |
| `prepare_model.py::WDI_URL (constant)` | yes | yes |
| `prepare_model.py::annual_trend` | yes | yes |
| `prepare_model.py::build_mou_signed` | yes | yes |
| `prepare_model.py::channel_group` | yes | yes |
| `prepare_model.py::download_ext` | yes | yes |
| `prepare_model.py::latest` | yes | yes |
| `prepare_model.py::main` | yes | yes |
| `prepare_model.py::poisson_fe` | yes | yes |
| `prepare_model.py::precompute_all` | yes | yes |
| `prepare_model.py::read_ext` | yes | yes |
| `prepare_model.py::series` | yes | yes |
| `prepare_model.py::source_group` | yes | yes |
| `prepare_model.py::tb_deaths_series` | yes | yes |
| `prepare_model.py::twoway_fe` | yes | yes |
| `scenarios.py::ALL_COUNTRY_DRAWS (constant)` | yes | yes |
| `scenarios.py::ANNOUNCED (constant)` | yes | **no** |
| `scenarios.py::DEFAULT_FISCAL (constant)` | yes | yes |
| `scenarios.py::DEFAULT_MORTALITY_TREND (constant)` | yes | yes |
| `scenarios.py::GAVI_CUT_DEFAULT (constant)` | yes | yes |
| `scenarios.py::GF_CUT_DEFAULT (constant)` | yes | yes |
| `scenarios.py::GOV_SHAPES (constant)` | yes | yes |
| `scenarios.py::MOU_PRICE_BASE_YEAR (constant)` | **no** | yes |
| `scenarios.py::MOU_SIGNED_FILE (constant)` | yes | yes |
| `scenarios.py::NO_MOU_DATA (constant)` | yes | yes |
| `scenarios.py::OECD_2025 (constant)` | yes | yes |
| `scenarios.py::PATH_SHAPES (constant)` | yes | yes |
| `scenarios.py::PRECOMPUTED_PRESETS (constant)` | yes | yes |
| `scenarios.py::PRESETS (constant)` | yes | yes |
| `scenarios.py::PRESET_DISPLAY (constant)` | yes | yes |
| `scenarios.py::SHORTFALLS (constant)` | yes | yes |
| `scenarios.py::S_CURVE_STEEPNESS (constant)` | yes | yes |
| `scenarios.py::UI_PRESETS (constant)` | yes | **no** |
| `scenarios.py::US_MULTI_EXITS (constant)` | yes | yes |
| `scenarios.py::YEARS (constant)` | yes | yes |
| `scenarios.py::build_scenario` | yes | yes |
| `scenarios.py::default_opts` | yes | yes |
| `scenarios.py::display_name` | yes | yes |
| `scenarios.py::gov_shape` | yes | yes |
| `scenarios.py::load_precomputed` | yes | yes |
| `scenarios.py::mou_deflate_settings` | **no** | yes |
| `scenarios.py::mou_group` | yes | yes |
| `scenarios.py::mou_groups` | yes | yes |
| `scenarios.py::mou_schedule` | yes | yes |
| `scenarios.py::mou_schedule_text` | yes | yes |
| `scenarios.py::mou_signed` | yes | yes |
| `scenarios.py::path_shape` | yes | yes |
| `scenarios.py::precomputed_draws_path` | yes | yes |
| `scenarios.py::precomputed_path` | yes | yes |
| `scenarios.py::preset_description` | yes | yes |
| `scenarios.py::preset_slug` | yes | yes |
| `scenarios.py::scenario_from_key` | yes | yes |
| `scenarios.py::scenario_key` | yes | yes |
| `scenarios.py::shortfall_cuts` | yes | yes |
| `scenarios.py::shortfall_label` | yes | yes |
| `theme.py::ACCENT (constant)` | yes | yes |
| `theme.py::AMBER (constant)` | yes | yes |
| `theme.py::BRAND (constant)` | yes | yes |
| `theme.py::BRAND_LIGHT (constant)` | yes | yes |
| `theme.py::CSS (constant)` | yes | yes |
| `theme.py::DEEP (constant)` | yes | yes |
| `theme.py::DISEASE_COLORS (constant)` | yes | yes |
| `theme.py::FONTS_URL (constant)` | yes | yes |
| `theme.py::FUNDER_ALIASES (constant)` | yes | yes |
| `theme.py::FUNDER_COLORS (constant)` | yes | yes |
| `theme.py::GENERIC_SOURCES (constant)` | yes | yes |
| `theme.py::ICONS_URL (constant)` | yes | yes |
| `theme.py::INK (constant)` | yes | yes |
| `theme.py::LEGEND_GAP_PX (constant)` | yes | yes |
| `theme.py::MAP_RAMP (constant)` | yes | yes |
| `theme.py::MUTED (constant)` | yes | yes |
| `theme.py::OTHER (constant)` | yes | yes |
| `theme.py::OTHER_SOURCES (constant)` | yes | yes |
| `theme.py::PAGES (constant)` | yes | yes |
| `theme.py::PALETTE (constant)` | yes | yes |
| `theme.py::RANGE_LABEL (constant)` | yes | yes |
| `theme.py::RANGE_TIP (constant)` | yes | yes |
| `theme.py::RULE (constant)` | yes | yes |
| `theme.py::SANS (constant)` | yes | yes |
| `theme.py::SERIF (constant)` | yes | yes |
| `theme.py::SHORT_NAMES (constant)` | yes | yes |
| `theme.py::SPARE_FUNDER_COLORS (constant)` | yes | yes |
| `theme.py::SURFACE (constant)` | yes | yes |
| `theme.py::SURFACE_TINT (constant)` | yes | yes |
| `theme.py::TOP_FUNDERS (constant)` | yes | yes |
| `theme.py::ZERO_LINE (constant)` | yes | yes |
| `theme.py::_horizontal` | yes | yes |
| `theme.py::_trace_color` | yes | yes |
| `theme.py::blend` | yes | yes |
| `theme.py::color_key` | yes | yes |
| `theme.py::direct_labels` | yes | yes |
| `theme.py::funder_color` | yes | yes |
| `theme.py::funder_group` | yes | yes |
| `theme.py::pills_html` | yes | yes |
| `theme.py::section_header` | yes | yes |
| `theme.py::setup` | yes | yes |
| `theme.py::shared_select` | yes | yes |
| `theme.py::short_name` | yes | yes |
| `theme.py::source_html` | yes | yes |
| `theme.py::style_fig` | yes | yes |
| `theme.py::tint` | yes | yes |
| `theme.py::title_sub` | yes | yes |
| `theme.py::year_axis` | yes | yes |
| `unaids_inputs.py::HERE (constant)` | **no** | yes |
| `unaids_inputs.py::INPUTS_FILE (constant)` | **no** | yes |
| `unaids_inputs.py::SOURCE (constant)` | **no** | yes |
| `unaids_inputs.py::UNAIDS_FILE (constant)` | **no** | yes |
| `unaids_inputs.py::WANT (constant)` | **no** | yes |
| `unaids_inputs.py::apply` | **no** | yes |
| `unaids_inputs.py::main` | **no** | yes |
| `unaids_inputs.py::unaids_latest` | **no** | yes |
| `who_inputs.py::GHO (constant)` | yes | yes |
| `who_inputs.py::GHO_DIR (constant)` | yes | yes |
| `who_inputs.py::GHO_URL (constant)` | yes | yes |
| `who_inputs.py::HERE (constant)` | yes | yes |
| `who_inputs.py::INPUTS_FILE (constant)` | yes | yes |
| `who_inputs.py::_put` | yes | yes |
| `who_inputs.py::apply` | yes | yes |
| `who_inputs.py::download` | yes | yes |
| `who_inputs.py::latest` | yes | yes |
| `who_inputs.py::main` | yes | yes |
| `who_inputs.py::series` | yes | yes |

### Parameters (model_params.csv)

main 46, tomato 51, on both 46, main only 0, tomato only 5.

| Item | main | tomato |
|---|---|---|
| `art_hazard_mult` | yes | yes |
| `art_reengage` | yes | yes |
| `art_transmission` | yes | yes |
| `art_transmission_mult` | yes | yes |
| `asd_share` | yes | yes |
| `budget_growth` | **no** | yes |
| `continuity` | yes | yes |
| `cpia_ref` | yes | yes |
| `hiv_inf_death_treated` | yes | yes |
| `hiv_inf_death_untreated` | yes | yes |
| `hiv_legacy_art_params` | yes | yes |
| `hiv_new_inf_unsup_years` | yes | yes |
| `hiv_survival_median` | yes | yes |
| `hss_kappa` | yes | yes |
| `hss_service_share` | yes | yes |
| `imm_deaths_per_child_ref` | yes | yes |
| `imm_dpc_mult` | **no** | yes |
| `imm_legacy_u5mr_scaling` | **no** | yes |
| `imm_u5_share` | yes | yes |
| `mal_adult_effect_frac` | yes | yes |
| `mal_cm_default_cov` | yes | yes |
| `mal_cm_eff` | yes | yes |
| `mal_itn_default_use` | yes | yes |
| `mal_resurgence` | yes | yes |
| `mal_u5_share_afr` | yes | yes |
| `mal_u5_share_amr` | yes | yes |
| `mal_u5_share_emr` | yes | yes |
| `mal_u5_share_sea` | yes | yes |
| `mal_u5_share_wpr` | yes | yes |
| `mal_u5_use_country_series` | yes | yes |
| `mal_vc_eff` | yes | yes |
| `mou_deflate` | **no** | yes |
| `mou_us_inflation` | **no** | yes |
| `pmtct_infant_mort` | yes | yes |
| `pmtct_vt_reduction` | yes | yes |
| `tb_cfr_treated_neg` | yes | yes |
| `tb_cfr_treated_pos` | yes | yes |
| `tb_cfr_untreated_neg` | yes | yes |
| `tb_cfr_untreated_pos` | yes | yes |
| `tb_cfr_untreated_pos_art` | yes | yes |
| `tb_dr_dcfr` | yes | yes |
| `tb_secondary` | yes | yes |
| `uc_art_mult` | yes | yes |
| `uc_imm` | yes | yes |
| `uc_irs` | yes | yes |
| `uc_itn` | yes | yes |
| `uc_mal_cm` | yes | yes |
| `uc_ovc` | yes | yes |
| `uc_pmtct` | yes | yes |
| `uc_scale_elast` | yes | yes |
| `uc_tb_mult` | yes | yes |

### Model input files (model_data/, announcement_model/ data, unit_cost_reference.csv)

main 27, tomato 20, on both 20, main only 7, tomato only 0.

| Item | main | tomato |
|---|---|---|
| `announcement_model/.gitignore` | yes | **no** |
| `announcement_model/oda_history.csv` | yes | **no** |
| `announcement_model/project_cuts.py` | yes | **no** |
| `model_data/all_countries_America_First_MOUs.csv` | yes | yes |
| `model_data/all_countries_America_First_MOUs_draws.csv` | yes | yes |
| `model_data/all_countries_Announced_donor_cuts.csv` | yes | **no** |
| `model_data/all_countries_Announced_donor_cuts_draws.csv` | yes | **no** |
| `model_data/all_countries_Combined_retreat.csv` | yes | yes |
| `model_data/all_countries_Combined_retreat_draws.csv` | yes | yes |
| `model_data/all_countries_Full_US_exit.csv` | yes | yes |
| `model_data/all_countries_Full_US_exit_draws.csv` | yes | yes |
| `model_data/all_countries_Global_Fund_Gavi_shortfalls.csv` | yes | yes |
| `model_data/all_countries_Global_Fund_Gavi_shortfalls_draws.csv` | yes | yes |
| `model_data/all_countries_IHME_2025_preliminary_estimates.csv` | yes | yes |
| `model_data/all_countries_IHME_2025_preliminary_estimates_draws.csv` | yes | yes |
| `model_data/all_countries_OECD_reported_2025_aid_cuts.csv` | yes | yes |
| `model_data/all_countries_OECD_reported_2025_aid_cuts_draws.csv` | yes | yes |
| `model_data/announcement_areas.csv` | yes | **no** |
| `model_data/announcement_cuts.csv` | yes | **no** |
| `model_data/country_inputs.csv` | yes | yes |
| `model_data/country_profile.csv` | yes | yes |
| `model_data/dah_lines.csv` | yes | yes |
| `model_data/ihme_trend.csv` | yes | yes |
| `model_data/mou_signed.csv` | yes | yes |
| `model_data/panel.csv` | yes | yes |
| `model_data/regressions.json` | yes | yes |
| `unit_cost_reference.csv` | yes | yes |

### Input columns (model_data/country_inputs.csv)

main 218, tomato 262, on both 218, main only 0, tomato only 44.

| Item | main | tomato |
|---|---|---|
| `all_forms_of_tb_incidence_estimated` | yes | yes |
| `all_forms_of_tb_incidence_estimated_year` | yes | yes |
| `all_forms_of_tb_number_of_deaths_estimated` | yes | yes |
| `all_forms_of_tb_number_of_deaths_estimated_year` | yes | yes |
| `art_cost_full` | yes | yes |
| `art_cost_full_hi` | yes | yes |
| `art_cost_full_lo` | yes | yes |
| `art_cost_full_source` | yes | yes |
| `art_cost_full_year` | yes | yes |
| `art_site_cost` | yes | yes |
| `art_site_cost_hi` | yes | yes |
| `art_site_cost_lo` | yes | yes |
| `art_site_cost_source` | yes | yes |
| `art_site_cost_year` | yes | yes |
| `art_transmission_rate` | yes | yes |
| `art_transmission_rate_hi` | yes | yes |
| `art_transmission_rate_lo` | yes | yes |
| `art_transmission_source` | yes | yes |
| `art_transmission_year` | yes | yes |
| `births` | yes | yes |
| `births_2026` | **no** | yes |
| `births_2027` | **no** | yes |
| `births_2028` | **no** | yes |
| `births_2029` | **no** | yes |
| `births_2030` | **no** | yes |
| `births_proj_source` | **no** | yes |
| `dah_2023` | yes | yes |
| `dah_2026_expected` | yes | yes |
| `dah_all_purposes_base` | yes | yes |
| `dah_nch_base` | yes | yes |
| `dah_share_the_2023` | yes | yes |
| `donor_share_hiv` | yes | yes |
| `donor_share_hiv_source` | yes | yes |
| `donor_share_hiv_year` | yes | yes |
| `donor_share_imm` | yes | yes |
| `donor_share_imm_source` | yes | yes |
| `donor_share_imm_year` | yes | yes |
| `donor_share_mal_cm` | **no** | yes |
| `donor_share_mal_cm_source` | **no** | yes |
| `donor_share_mal_irs` | **no** | yes |
| `donor_share_mal_irs_source` | **no** | yes |
| `donor_share_mal_itn` | **no** | yes |
| `donor_share_mal_itn_source` | **no** | yes |
| `donor_share_malaria` | yes | yes |
| `donor_share_malaria_prev` | yes | yes |
| `donor_share_malaria_prev_source` | yes | yes |
| `donor_share_malaria_prev_year` | yes | yes |
| `donor_share_malaria_source` | yes | yes |
| `donor_share_malaria_year` | yes | yes |
| `donor_share_tb` | yes | yes |
| `donor_share_tb_source` | yes | yes |
| `donor_share_tb_year` | yes | yes |
| `flag_interest_alt_def` | **no** | yes |
| `flag_irs_household` | **no** | yes |
| `flag_irs_implied` | **no** | yes |
| `flag_itn_default` | **no** | yes |
| `flag_map_who_gap` | **no** | yes |
| `gc_dod_totl_gd_zs` | yes | yes |
| `gc_dod_totl_gd_zs_year` | yes | yes |
| `gc_rev_xgrt_gd_zs` | yes | yes |
| `gc_rev_xgrt_gd_zs_year` | yes | yes |
| `gc_xpn_intp_rv_zs` | yes | yes |
| `gc_xpn_intp_rv_zs_year` | yes | yes |
| `gc_xpn_totl_gd_zs` | yes | yes |
| `gc_xpn_totl_gd_zs_year` | yes | yes |
| `gdp_growth_weo_2026_30` | **no** | yes |
| `gdp_growth_weo_2026_30_source` | **no** | yes |
| `gdp_pc` | yes | yes |
| `ghes_2023` | yes | yes |
| `ghes_2026_expected` | yes | yes |
| `ghes_2030_expected` | yes | yes |
| `ghes_growth_median` | yes | yes |
| `ghes_growth_p75` | yes | yes |
| `ghes_growth_p90` | yes | yes |
| `ghes_pc_2023` | yes | yes |
| `ghes_pct_gdp_2023` | yes | yes |
| `hiv_death_share` | yes | yes |
| `hiv_death_share_year` | yes | yes |
| `hiv_deaths_est` | yes | yes |
| `hiv_deaths_unaids` | **no** | yes |
| `hiv_deaths_unaids_source` | **no** | yes |
| `hiv_deaths_unaids_year` | **no** | yes |
| `hiv_pos_pregnancies` | yes | yes |
| `hiv_pos_pregnancies_source` | yes | yes |
| `hiv_pos_pregnancies_year` | yes | yes |
| `imm_antigens` | **no** | yes |
| `imm_antigens_excluded_zero_coverage` | **no** | yes |
| `imm_dpc` | **no** | yes |
| `imm_dpc_beyond_window` | **no** | yes |
| `imm_dpc_hi` | **no** | yes |
| `imm_dpc_lag0` | **no** | yes |
| `imm_dpc_lag1` | **no** | yes |
| `imm_dpc_lag2` | **no** | yes |
| `imm_dpc_lag3` | **no** | yes |
| `imm_dpc_lag4` | **no** | yes |
| `imm_dpc_lag5` | **no** | yes |
| `imm_dpc_lag6` | **no** | yes |
| `imm_dpc_lag7` | **no** | yes |
| `imm_dpc_lag8` | **no** | yes |
| `imm_dpc_lag9` | **no** | yes |
| `imm_dpc_lo` | **no** | yes |
| `imm_dpc_source` | **no** | yes |
| `imm_in_vimc` | **no** | yes |
| `imm_q5_ratio` | **no** | yes |
| `income_group` | yes | yes |
| `interest_estimated` | yes | yes |
| `interest_imf` | yes | yes |
| `interest_imf_year` | yes | yes |
| `interest_pct_revenue` | yes | yes |
| `interest_pct_revenue_source` | yes | yes |
| `interest_pct_revenue_year` | yes | yes |
| `is_ssa` | yes | yes |
| `iso3` | yes | yes |
| `mal_cm_cov` | yes | yes |
| `mal_cm_cov_source` | yes | yes |
| `mal_cm_cov_year` | yes | yes |
| `mal_irs_cov` | yes | yes |
| `mal_irs_cov_source` | yes | yes |
| `mal_irs_cov_year` | yes | yes |
| `mal_itn_cov` | yes | yes |
| `mal_itn_cov_source` | yes | yes |
| `mal_itn_cov_year` | yes | yes |
| `malaria_at_risk_share` | yes | yes |
| `malaria_cases` | yes | yes |
| `malaria_cases_prev` | yes | yes |
| `malaria_cases_prev_source` | yes | yes |
| `malaria_cases_source` | yes | yes |
| `malaria_cases_year` | yes | yes |
| `malaria_deaths` | yes | yes |
| `malaria_deaths_in_children_1_59_months_total_deaths` | yes | yes |
| `malaria_deaths_in_children_1_59_months_total_deaths_year` | yes | yes |
| `malaria_deaths_source` | yes | yes |
| `malaria_deaths_year` | yes | yes |
| `malaria_pop_at_risk` | yes | yes |
| `malaria_pop_at_risk_source` | yes | yes |
| `malaria_pop_at_risk_year` | yes | yes |
| `malaria_u5_share_param` | yes | yes |
| `malaria_u5_share_rule` | yes | yes |
| `measles_deaths_in_children_1_59_months_total_deaths` | yes | yes |
| `measles_deaths_in_children_1_59_months_total_deaths_year` | yes | yes |
| `mou_gavi_2026_30` | yes | yes |
| `mou_gavi_ref` | yes | yes |
| `mou_gf_gc8_hiv` | yes | yes |
| `mou_gf_gc8_mal` | yes | yes |
| `mou_gf_gc8_rssh` | yes | yes |
| `mou_gf_gc8_tb` | yes | yes |
| `mou_gf_ref` | yes | yes |
| `mou_oth_ref` | yes | yes |
| `mou_us_2026` | yes | yes |
| `mou_us_2027` | yes | yes |
| `mou_us_2028` | yes | yes |
| `mou_us_2029` | yes | yes |
| `mou_us_2030` | yes | yes |
| `mou_us_ref` | yes | yes |
| `mou_wb_2026_30` | yes | yes |
| `mou_wb_ref` | yes | yes |
| `oop_2023` | yes | yes |
| `people_living_with_hiv_number_all_ages` | yes | yes |
| `people_living_with_hiv_number_all_ages_year` | yes | yes |
| `plhiv` | yes | yes |
| `plhiv_calibration` | yes | yes |
| `plhiv_source` | yes | yes |
| `plhiv_year` | yes | yes |
| `pneumonia_deaths_in_children_1_59_months_total_deaths` | yes | yes |
| `pneumonia_deaths_in_children_1_59_months_total_deaths_year` | yes | yes |
| `ppp_2023` | yes | yes |
| `sh_dth_mort` | yes | yes |
| `sh_dth_mort_year` | yes | yes |
| `sh_dyn_aids_zs` | yes | yes |
| `sh_dyn_aids_zs_year` | yes | yes |
| `sh_dyn_mort` | yes | yes |
| `sh_dyn_mort_year` | yes | yes |
| `sh_hiv_0014` | yes | yes |
| `sh_hiv_0014_year` | yes | yes |
| `sh_hiv_artc_zs` | yes | yes |
| `sh_hiv_artc_zs_source` | yes | yes |
| `sh_hiv_artc_zs_year` | yes | yes |
| `sh_hiv_incd_tl` | yes | yes |
| `sh_hiv_incd_tl_source` | **no** | yes |
| `sh_hiv_incd_tl_year` | yes | yes |
| `sh_hiv_pmtc_zs` | yes | yes |
| `sh_hiv_pmtc_zs_source` | yes | yes |
| `sh_hiv_pmtc_zs_year` | yes | yes |
| `sh_imm_idpt` | yes | yes |
| `sh_imm_idpt_source` | **no** | yes |
| `sh_imm_idpt_year` | yes | yes |
| `sh_imm_meas` | yes | yes |
| `sh_imm_meas_source` | **no** | yes |
| `sh_imm_meas_year` | yes | yes |
| `sh_mlr_incd_p3` | yes | yes |
| `sh_mlr_incd_p3_year` | yes | yes |
| `sh_mlr_nets_zs` | yes | yes |
| `sh_mlr_nets_zs_source` | yes | yes |
| `sh_mlr_nets_zs_year` | yes | yes |
| `sh_mlr_tret_zs` | yes | yes |
| `sh_mlr_tret_zs_year` | yes | yes |
| `sh_mmr_dths` | yes | yes |
| `sh_mmr_dths_year` | yes | yes |
| `sh_tbs_cure_zs` | yes | yes |
| `sh_tbs_cure_zs_year` | yes | yes |
| `sh_tbs_dtec_zs` | yes | yes |
| `sh_tbs_dtec_zs_year` | yes | yes |
| `sh_tbs_incd` | yes | yes |
| `sh_tbs_incd_year` | yes | yes |
| `sh_uhc_sci` | yes | yes |
| `sh_uhc_sci_year` | yes | yes |
| `sh_xpd_ghed_ge_zs` | yes | yes |
| `sh_xpd_ghed_ge_zs_year` | yes | yes |
| `sp_dyn_cbrt_in` | yes | yes |
| `sp_dyn_cbrt_in_year` | yes | yes |
| `sp_dyn_cdrt_in` | yes | yes |
| `sp_dyn_cdrt_in_year` | yes | yes |
| `sp_pop_0014_to` | yes | yes |
| `sp_pop_0014_to_year` | yes | yes |
| `sp_pop_1564_to` | yes | yes |
| `sp_pop_1564_to_year` | yes | yes |
| `sp_pop_totl` | yes | yes |
| `sp_pop_totl_year` | yes | yes |
| `tb_cost_year` | yes | yes |
| `tb_deaths_total` | yes | yes |
| `tb_dr_cost` | yes | yes |
| `tb_dr_cost_hi` | yes | yes |
| `tb_dr_cost_lo` | yes | yes |
| `tb_dr_cost_source` | yes | yes |
| `tb_ds_cost` | yes | yes |
| `tb_ds_cost_hi` | yes | yes |
| `tb_ds_cost_lo` | yes | yes |
| `tb_ds_cost_source` | yes | yes |
| `tb_hiv_share` | yes | yes |
| `tb_hivplus_incidence_estimated` | yes | yes |
| `tb_hivplus_incidence_estimated_year` | yes | yes |
| `tb_hivplus_number_of_deaths_estimated` | yes | yes |
| `tb_hivplus_number_of_deaths_estimated_year` | yes | yes |
| `tb_rr_cov` | yes | yes |
| `tb_rr_share` | yes | yes |
| `tb_rr_source` | yes | yes |
| `the_2023` | yes | yes |
| `trend_malaria_deaths` | yes | yes |
| `trend_malaria_deaths_fit` | yes | yes |
| `trend_malaria_deaths_source` | yes | yes |
| `trend_u5mr` | yes | yes |
| `unspec_hiv_pm` | yes | yes |
| `unspec_hiv_prevention` | yes | yes |
| `unspec_hiv_rssh` | yes | yes |
| `unspec_hiv_source` | yes | yes |
| `unspec_hiv_testing` | yes | yes |
| `unspec_hiv_treatment` | yes | yes |
| `unspec_malaria_pm` | yes | yes |
| `unspec_malaria_prevention` | yes | yes |
| `unspec_malaria_rssh` | yes | yes |
| `unspec_malaria_source` | yes | yes |
| `unspec_malaria_testing` | yes | yes |
| `unspec_malaria_treatment` | yes | yes |
| `unspec_tb_pm` | yes | yes |
| `unspec_tb_prevention` | yes | yes |
| `unspec_tb_rssh` | yes | yes |
| `unspec_tb_source` | yes | yes |
| `unspec_tb_testing` | yes | yes |
| `unspec_tb_treatment` | yes | yes |
| `us_health_aid_base` | yes | yes |
| `vpd_child_deaths` | yes | yes |
| `who_region` | yes | yes |

### Tests (tests/, by function; parametrised cases count once)

main 155, tomato 69, on both 68, main only 87, tomato only 1.

| Item | main | tomato |
|---|---|---|
| `tests/test_announcement.py::test_abuja_and_tax_options` | yes | **no** |
| `tests/test_announcement.py::test_all_countries_people_columns` | yes | **no** |
| `tests/test_announcement.py::test_cells_take_their_own_yearly_path` | yes | **no** |
| `tests/test_announcement.py::test_dashboard_is_coverage_only` | yes | **no** |
| `tests/test_announcement.py::test_donor_cut_is_uniform_across_its_predicted_channels` | yes | **no** |
| `tests/test_announcement.py::test_file_covers_every_country_and_cuts_are_bounded` | yes | **no** |
| `tests/test_announcement.py::test_fiscal_panel_uses_all_health_aid_lost` | yes | **no** |
| `tests/test_announcement.py::test_global_fund_cut_is_the_allocation_not_stacked_on_donor_cuts` | yes | **no** |
| `tests/test_announcement.py::test_inputs_cached_before_the_file_existed_still_cut` | yes | **no** |
| `tests/test_announcement.py::test_known_loss_is_part_of_total_loss` | yes | **no** |
| `tests/test_announcement.py::test_phase_out_by_funder` | yes | **no** |
| `tests/test_announcement.py::test_preset_registered` | yes | **no** |
| `tests/test_announcement.py::test_run_country_and_precomputed_file` | yes | **no** |
| `tests/test_announcement.py::test_services_by_year` | yes | **no** |
| `tests/test_announcement.py::test_total_health_aid_uses_the_2019_2023_average` | yes | **no** |
| `tests/test_announcement.py::test_treatment_gets_its_share_of_each_disease` | yes | **no** |
| `tests/test_announcement.py::test_without_the_file_nothing_is_cut` | yes | **no** |
| `tests/test_budget_section 2.py::test_caption_when_sides_differ` | yes | **no** |
| `tests/test_budget_section 2.py::test_central_above_weo_shown_alone_with_note` | yes | **no** |
| `tests/test_budget_section 2.py::test_central_breakdown_own_size_plus_grey_box` | yes | **no** |
| `tests/test_budget_section 2.py::test_general_government_breakdown_scaled_to_weo` | yes | **no** |
| `tests/test_budget_section.py::test_caption_when_sides_differ` | yes | yes |
| `tests/test_budget_section.py::test_central_above_weo_shown_alone_with_note` | yes | yes |
| `tests/test_budget_section.py::test_central_breakdown_own_size_plus_grey_box` | yes | yes |
| `tests/test_budget_section.py::test_general_government_breakdown_scaled_to_weo` | yes | yes |
| `tests/test_fiscal 2.py::test_every_country_has_interest_and_stress_is_never_a_silent_1` | yes | **no** |
| `tests/test_fiscal 2.py::test_imf_net_interest_formula_and_actual_years` | yes | **no** |
| `tests/test_fiscal 2.py::test_imf_net_interest_is_primary_and_the_world_bank_fallback_is_flagged` | yes | **no** |
| `tests/test_fiscal 2.py::test_income_group_median_when_both_missing` | yes | **no** |
| `tests/test_fiscal 2.py::test_inputs_years_line` | yes | **no** |
| `tests/test_fiscal 2.py::test_interest_text_shows_source_and_year` | yes | **no** |
| `tests/test_fiscal.py::test_every_country_has_interest_and_stress_is_never_a_silent_1` | yes | yes |
| `tests/test_fiscal.py::test_imf_net_interest_formula_and_actual_years` | yes | yes |
| `tests/test_fiscal.py::test_imf_net_interest_is_primary_and_the_world_bank_fallback_is_flagged` | **no** | yes |
| `tests/test_fiscal.py::test_income_group_median_when_both_missing` | yes | yes |
| `tests/test_fiscal.py::test_inputs_years_line` | yes | yes |
| `tests/test_fiscal.py::test_interest_text_shows_source_and_year` | yes | yes |
| `tests/test_fiscal.py::test_more_recent_source_wins_ties_go_to_world_bank` | yes | **no** |
| `tests/test_hiv 2.py::test_card_is_full_model_for_1m_uniform_cut` | yes | **no** |
| `tests/test_hiv 2.py::test_card_without_aid_says_so` | yes | **no** |
| `tests/test_hiv 2.py::test_care_line_has_money_but_no_units` | yes | **no** |
| `tests/test_hiv 2.py::test_kappa_of_care_loss_counts_toward_art` | yes | **no** |
| `tests/test_hiv 2.py::test_line_mapping` | yes | **no** |
| `tests/test_hiv 2.py::test_pmtct_cost` | yes | **no** |
| `tests/test_hiv 2.py::test_pmtct_women_outside_art_pool` | yes | **no** |
| `tests/test_hiv 2.py::test_service_table_care_row` | yes | **no** |
| `tests/test_hiv.py::test_card_is_full_model_for_1m_uniform_cut` | yes | yes |
| `tests/test_hiv.py::test_card_without_aid_says_so` | yes | yes |
| `tests/test_hiv.py::test_care_line_has_money_but_no_units` | yes | yes |
| `tests/test_hiv.py::test_kappa_of_care_loss_counts_toward_art` | yes | yes |
| `tests/test_hiv.py::test_line_mapping` | yes | yes |
| `tests/test_hiv.py::test_pmtct_cost` | yes | yes |
| `tests/test_hiv.py::test_pmtct_women_outside_art_pool` | yes | yes |
| `tests/test_hiv.py::test_service_table_care_row` | yes | yes |
| `tests/test_i07 2.py::test_aid_lost_is_the_cut_times_each_funds_baseline` | yes | **no** |
| `tests/test_i07 2.py::test_defaults_are_gavi_15_global_fund_20` | yes | **no** |
| `tests/test_i07 2.py::test_labels_reflect_the_chosen_values` | yes | **no** |
| `tests/test_i07 2.py::test_precomputed_file_uses_the_defaults` | yes | **no** |
| `tests/test_i07 2.py::test_sliders_cover_0_to_50_with_defaults_in_range` | yes | **no** |
| `tests/test_i07 2.py::test_us_gavi_money_is_cut_once` | yes | **no** |
| `tests/test_i07.py::test_aid_lost_is_the_cut_times_each_funds_baseline` | yes | yes |
| `tests/test_i07.py::test_defaults_are_gavi_15_global_fund_20` | yes | yes |
| `tests/test_i07.py::test_labels_reflect_the_chosen_values` | yes | yes |
| `tests/test_i07.py::test_precomputed_file_uses_the_defaults` | yes | yes |
| `tests/test_i07.py::test_sliders_cover_0_to_50_with_defaults_in_range` | yes | yes |
| `tests/test_i07.py::test_us_gavi_money_is_cut_once` | yes | yes |
| `tests/test_malaria 2.py::test_apply_is_idempotent` | yes | **no** |
| `tests/test_malaria 2.py::test_bednets_map_else_survey_from_2015_else_default` | yes | **no** |
| `tests/test_malaria 2.py::test_cases_are_map_pf_plus_pv` | yes | **no** |
| `tests/test_malaria 2.py::test_combined_vector_control_formula` | yes | **no** |
| `tests/test_malaria 2.py::test_data_years_lists_malaria_as_map_2025` | yes | **no** |
| `tests/test_malaria 2.py::test_each_vector_line_capped_at_its_own_coverage` | yes | **no** |
| `tests/test_malaria 2.py::test_malaria_treatment_cost_sourced` | yes | **no** |
| `tests/test_malaria 2.py::test_malaria_u5_share_and_adult_fraction` | yes | **no** |
| `tests/test_malaria 2.py::test_service_table_shows_source_and_year` | yes | **no** |
| `tests/test_malaria 2.py::test_spraying_map_africa_only` | yes | **no** |
| `tests/test_malaria 2.py::test_spraying_without_map_estimate_uses_what_donor_money_buys` | yes | **no** |
| `tests/test_malaria 2.py::test_treatment_coverage_is_map_effective_treatment` | yes | **no** |
| `tests/test_malaria 2.py::test_trend_is_who_malaria_deaths_2015_2024_clipped` | yes | **no** |
| `tests/test_malaria 2.py::test_under5_trend_unchanged` | yes | **no** |
| `tests/test_malaria.py::test_apply_is_idempotent` | yes | yes |
| `tests/test_malaria.py::test_bednets_map_else_survey_from_2015_else_default` | yes | yes |
| `tests/test_malaria.py::test_cases_are_map_pf_plus_pv` | yes | yes |
| `tests/test_malaria.py::test_combined_vector_control_formula` | yes | yes |
| `tests/test_malaria.py::test_data_years_lists_malaria_as_map_2025` | yes | yes |
| `tests/test_malaria.py::test_each_vector_line_capped_at_its_own_coverage` | yes | yes |
| `tests/test_malaria.py::test_malaria_treatment_cost_sourced` | yes | yes |
| `tests/test_malaria.py::test_malaria_u5_share_and_adult_fraction` | yes | yes |
| `tests/test_malaria.py::test_service_table_shows_source_and_year` | yes | yes |
| `tests/test_malaria.py::test_spraying_map_africa_only` | yes | yes |
| `tests/test_malaria.py::test_spraying_without_map_estimate_uses_what_donor_money_buys` | yes | yes |
| `tests/test_malaria.py::test_treatment_coverage_is_map_effective_treatment` | yes | yes |
| `tests/test_malaria.py::test_trend_is_who_malaria_deaths_2015_2024_clipped` | yes | yes |
| `tests/test_malaria.py::test_under5_trend_unchanged` | yes | yes |
| `tests/test_minor 2.py::test_central_outside_range_is_rejected` | yes | **no** |
| `tests/test_minor 2.py::test_fiscal_gap_values_match_headline` | yes | **no** |
| `tests/test_minor 2.py::test_gain_note_under_the_disease` | yes | **no** |
| `tests/test_minor 2.py::test_health_share_estimated_when_world_bank_missing` | yes | **no** |
| `tests/test_minor 2.py::test_health_share_prefers_world_bank_latest_year` | yes | **no** |
| `tests/test_minor 2.py::test_low_above_high_is_rejected` | yes | **no** |
| `tests/test_minor 2.py::test_low_equals_high_is_a_constant_and_runs` | yes | **no** |
| `tests/test_minor 2.py::test_no_negative_losses_under_aid_rises` | yes | **no** |
| `tests/test_minor 2.py::test_other_draws_unchanged_when_one_parameter_is_fixed` | yes | **no** |
| `tests/test_minor 2.py::test_pts_formatter_never_shows_double_sign` | yes | **no** |
| `tests/test_minor.py::test_central_outside_range_is_rejected` | yes | yes |
| `tests/test_minor.py::test_fiscal_gap_values_match_headline` | yes | yes |
| `tests/test_minor.py::test_gain_note_under_the_disease` | yes | yes |
| `tests/test_minor.py::test_health_share_estimated_when_world_bank_missing` | yes | yes |
| `tests/test_minor.py::test_health_share_prefers_world_bank_latest_year` | yes | yes |
| `tests/test_minor.py::test_low_above_high_is_rejected` | yes | yes |
| `tests/test_minor.py::test_low_equals_high_is_a_constant_and_runs` | yes | yes |
| `tests/test_minor.py::test_no_negative_losses_under_aid_rises` | yes | yes |
| `tests/test_minor.py::test_other_draws_unchanged_when_one_parameter_is_fixed` | yes | yes |
| `tests/test_minor.py::test_pts_formatter_never_shows_double_sign` | yes | yes |
| `tests/test_mou 2.py::test_all_countries_only_group_a` | yes | **no** |
| `tests/test_mou 2.py::test_applied_us_bilateral_cut_equals_schedule` | yes | **no** |
| `tests/test_mou 2.py::test_easing_schedule_returns_people_to_care` | yes | **no** |
| `tests/test_mou 2.py::test_groups_b_and_c_cannot_run` | yes | **no** |
| `tests/test_mou 2.py::test_nothing_rescales_a_schedule` | yes | **no** |
| `tests/test_mou 2.py::test_schedule_rules` | yes | **no** |
| `tests/test_mou 2.py::test_signed_list_and_groups` | yes | **no** |
| `tests/test_mou.py::test_all_countries_only_group_a` | yes | yes |
| `tests/test_mou.py::test_applied_us_bilateral_cut_equals_schedule` | yes | yes |
| `tests/test_mou.py::test_easing_schedule_returns_people_to_care` | yes | yes |
| `tests/test_mou.py::test_groups_b_and_c_cannot_run` | yes | yes |
| `tests/test_mou.py::test_nothing_rescales_a_schedule` | yes | yes |
| `tests/test_mou.py::test_schedule_rules` | yes | yes |
| `tests/test_mou.py::test_signed_list_and_groups` | yes | yes |
| `tests/test_paths 2.py::test_break_even_share` | yes | **no** |
| `tests/test_paths 2.py::test_default_path_reproduces_original` | yes | **no** |
| `tests/test_paths 2.py::test_full_government_money_zero_deaths` | yes | **no** |
| `tests/test_paths 2.py::test_hiv_infection_deaths` | yes | **no** |
| `tests/test_paths 2.py::test_late_cut_committed` | yes | **no** |
| `tests/test_paths 2.py::test_late_vaccine_cut_committed` | yes | **no** |
| `tests/test_paths 2.py::test_malaria_resurgence` | yes | **no** |
| `tests/test_paths 2.py::test_slower_path_fewer_committed_deaths` | yes | **no** |
| `tests/test_paths 2.py::test_tb_transmission` | yes | **no** |
| `tests/test_paths 2.py::test_year_by_year_services_ignore_later_years` | yes | **no** |
| `tests/test_paths 2.py::test_zero_path_zero_deaths` | yes | **no** |
| `tests/test_paths.py::test_break_even_share` | yes | yes |
| `tests/test_paths.py::test_default_path_reproduces_original` | yes | yes |
| `tests/test_paths.py::test_full_government_money_zero_deaths` | yes | yes |
| `tests/test_paths.py::test_hiv_infection_deaths` | yes | yes |
| `tests/test_paths.py::test_late_cut_committed` | yes | yes |
| `tests/test_paths.py::test_late_vaccine_cut_committed` | yes | yes |
| `tests/test_paths.py::test_malaria_resurgence` | yes | yes |
| `tests/test_paths.py::test_slower_path_fewer_committed_deaths` | yes | yes |
| `tests/test_paths.py::test_tb_transmission` | yes | yes |
| `tests/test_paths.py::test_year_by_year_services_ignore_later_years` | yes | yes |
| `tests/test_paths.py::test_zero_path_zero_deaths` | yes | yes |
| `tests/test_tb 2.py::test_detection_rate_capped_at_100_and_flagged` | yes | **no** |
| `tests/test_tb 2.py::test_no_tb_death_trend` | yes | **no** |
| `tests/test_tb 2.py::test_untreated_hiv_tb_cfr_is_who_table5_blend` | yes | **no** |
| `tests/test_tb.py::test_detection_rate_capped_at_100_and_flagged` | yes | yes |
| `tests/test_tb.py::test_no_tb_death_trend` | yes | yes |
| `tests/test_tb.py::test_untreated_hiv_tb_cfr_is_who_table5_blend` | yes | yes |

### Checks (audit/checks.py check names)

main 53, tomato 53, on both 53, main only 0, tomato only 0.

| Item | main | tomato |
|---|---|---|
| `aid_at_risk_is_per_year_not_5yr_total` | yes | yes |
| `all_country_range_brackets_total` | yes | yes |
| `card_deaths_equal_full_model_1M_uniform_cut` | yes | yes |
| `card_says_no_aid_when_none` | yes | yes |
| `coverage_in_0_1_and_after_le_before` | yes | yes |
| `coverage_is_fraction_not_percent` | yes | yes |
| `cut_formula_matches_documented_scenario` | yes | yes |
| `dashboard_country_equals_all_countries_row` | yes | yes |
| `deaths_le_people_affected` | yes | yes |
| `deaths_nonnegative` | yes | yes |
| `displayed_finite` | yes | yes |
| `displayed_nonnegative` | yes | yes |
| `displayed_value_equals_central_run` | yes | yes |
| `fiscal_gap_left_equals_headline_net_and_gap_equals_filled_plus_left` | yes | yes |
| `fraction_scale_` | yes | yes |
| `gdp_constant2023_equals_nominal_in_2023` | yes | yes |
| `headline_people_and_deaths_equal_table_totals` | yes | yes |
| `health_share_in_0_100` | yes | yes |
| `hero_people_equals_table_people` | yes | yes |
| `line_net_le_line_gross` | yes | yes |
| `lines_sum_to_buckets_sum_to_totals` | yes | yes |
| `modelled_aid_equals_IHME_bucket_total_elim_ch0` | yes | yes |
| `modelled_aid_equals_IHME_bucket_total_strict_0.5pct` | yes | yes |
| `more_cut_never_fewer_deaths` | yes | yes |
| `more_cut_never_less_net_loss` | yes | yes |
| `net_le_gross_le_base_and_replaced_le_gross` | yes | yes |
| `no_line_in_two_buckets` | yes | yes |
| `no_negative_people_or_coverage_drop` | yes | yes |
| `path_chart_sums_to_headline` | yes | yes |
| `people_losing_le_people_covered` | yes | yes |
| `percent_scale_` | yes | yes |
| `precomputed_csv_has_all_columns` | yes | yes |
| `precomputed_csv_matches_fresh_run` | yes | yes |
| `precomputed_draw_totals_match_fresh_run` | yes | yes |
| `precomputed_draw_totals_present` | yes | yes |
| `range_lo_le_central_le_hi` | yes | yes |
| `replaced_le_fiscal_capacity` | yes | yes |
| `section1_2023_matches_raw_IHME_file` | yes | yes |
| `section1_components_sum_to_total` | yes | yes |
| `section1_dah_equals_section2_dah_same_year` | yes | yes |
| `section3_` | yes | yes |
| `section3_central_breakdown_not_rescaled` | yes | yes |
| `section3_cofog_shares_sum_to_100` | yes | yes |
| `section3_has_data` | yes | yes |
| `section3_revenue_items_sum_to_file_total` | yes | yes |
| `section3_side_boxes_sum_to_weo_total` | yes | yes |
| `section3_weo_spending_minus_revenue_equals_borrowing` | yes | yes |
| `section3_weo_totals_present_for_default_year` | yes | yes |
| `table_total_row_equals_headline` | yes | yes |
| `unit_costs_inside_parameter_range` | yes | yes |
| `unspec_and_kappa_conserve_money` | yes | yes |
| `year1_le_5year` | yes | yes |
| `zero_cut_gives_zero` | yes | yes |


## 5. Output snapshots

`audit/merge/snapshot_merge.py` (seed 7, 400 draws), run from each branch's root: every preset (incl. Custom at its defaults) x every country x 5 funding paths x 4 government responses, plus All Countries file sums, main's Announced donor cuts projection outputs (PROJ rows) and sha1 of the projection and precomputed files (FILE rows). main: 9,974 rows x 810 values; tomato: 8,552 x 507. Full files (60 MB / 36 MB) are gitignored: `audit/merge/snapshot_main.csv`, `snapshot_tomato.csv`; the committed `*_headline.csv` files hold totals per country x preset (sudden cut, no response).

