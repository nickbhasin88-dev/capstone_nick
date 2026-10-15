# Data Sources Inventory

Every data source the funding-cut model actually uses, found by reading the code: `prepare_model.py`,
`health_model.py`, `scenarios.py`, `who_inputs.py`, `hiv_transmission_inputs.py`, `fiscal_inputs.py`,
`malaria_inputs.py`, `batch34_inputs.py` and the `audit/batch*_*.py` scripts that build the columns of
`model_data/country_inputs.csv`, plus `model_params.csv`, `unit_cost_reference.csv`, `datasets/MANIFEST.md` and
`docs/SPEC.md`. Branch `tomato`, 15 October 2026. Only what the current code reads or cites is counted; files present
in the repository but unused are listed separately in Table D.

Counting rule: a dataset is one named data product from one producer (several extracts or indicator files from the
same product count once, and are listed in the "file path" column); the project's own unit-cost table and the Gavi
and Global Fund replenishment figures typed into the code are not counted as datasets. A published study counts once
even if it supplies several parameters.

## Summary Counts

| Count | Value |
|---|---|
| Distinct datasets the code reads | 26 |
| Distinct organizations producing them | 16 (plus Gapminder as the mirror through which the World Bank, WHO and UN IGME series are downloaded) |
| Published studies cited for parameter values in the current model | 32 (Table B, excluding the three cross-check studies and the superseded and legacy values) |
| Countries covered | 70 modelled (71 in the country list; Panama has no recorded aid for the four disease areas) |
| Years covered | aid baseline 2021 to 2023 (IHME 2025 preliminary for one preset); epidemiology, coverage and spending inputs 2016 to 2025 (latest year per country); projections 2026 to 2030, deaths set in motion followed to 2035 |

**Slide sentence:** The model combines 26 datasets from 16 organizations and 32 published studies, covering 70
countries, to turn a cut in aid into people losing services, extra deaths and new HIV infections over 2026 to 2030.

Organizations: Institute for Health Metrics and Evaluation (IHME); International Monetary Fund (IMF); World Bank;
World Health Organization (WHO: Global Health Observatory, Global TB Programme, Global Health Expenditure Database,
World Malaria Report); UNAIDS; UNICEF (with WHO, WUENIC); UN DESA Population Division; Malaria Atlas Project (MAP);
The Global Fund; Global Health Cost Consortium (GHCC); the Value TB consortium (LSHTM and partners); the Vaccine
Impact Modelling Consortium (VIMC, Imperial College); KFF; the Burnet Institute (Optima HIV); OECD; and the project
team (MOU schedules).

## Table A. Datasets The Code Reads

Grouped by model step. "Step" names the part of the model in `docs/SPEC.md`.

### Aid Baseline

| Dataset | Producer | Version or year | What it contains | File path | Units and currency | Model step | Used for |
|---|---|---|---|---|---|---|---|
| Development Assistance for Health (DAH) database 1990-2026 | IHME | released September 2026 (`Y2026M09D18`) | Aid by year, source, channel, recipient country and programme area; `elim_ch` flag for double-counted transfers; 2025 preliminary totals | `datasets/IHME_DAH_DATABASE_1990_2026_Y2026M09D18.CSV`; outputs `model_data/dah_lines.csv`, `model_data/ihme_trend.csv`, `model_data/country_profile.csv` (region) | thousands of constant 2023 US$ (x 1,000 in the model) | Aid Baseline; Scenarios (IHME 2025 preset) | The 2021-23 average aid by country x donor group x channel x service line; the IHME 2025 / 2021-23 ratios; the World Bank region label |

### Scenarios

| Dataset | Producer | Version or year | What it contains | File path | Units and currency | Model step | Used for |
|---|---|---|---|---|---|---|---|
| KFF Tracker: America First MOU Bilateral Global Health Agreements | KFF | data as of 8 October 2026 | Countries that have signed an MOU and the agreement date | `datasets/KFF_MOU_Tracker_2026-10-08.xlsx`; output `model_data/mou_signed.csv` | n/a | Scenarios (America First MOUs) | Which countries can run the MOU preset; MOU status in the dashboard header |
| MOU and co-financing sheet | project team | 2026 | US funding reference (2021-25) and yearly US funding 2026-2030 under each signed MOU; Global Fund, Gavi and World Bank reference amounts | `datasets/co-financing_MOU.xlsx`; columns `mou_us_ref`, `mou_us_2026` to `mou_us_2030`, `mou_gf_*`, `mou_gavi_2026_30`, `mou_wb_2026_30` in `model_data/country_inputs.csv` | nominal US$ (used only as ratios) | Scenarios (America First MOUs) | Year-by-year US bilateral cut for the 16 countries with a schedule |
| Preliminary 2025 official development assistance | OECD | April 2026 release | Change in each donor's total ODA in 2025 | values entered in `scenarios.py` (`OECD_2025`: United States -57%, Germany -17.4%, France -10.9%, United Kingdom -10.8%, Japan -5.6%) | % change | Scenarios (Total-Aid Cuts (OECD) Applied to Health Aid; Combined Retreat) | The donor cuts in two presets |
| Gavi 6.0 pledging outcome and Global Fund Eighth Replenishment | Gavi; The Global Fund | June 2025; November 2025 and February 2026 | Pledged totals against targets and the previous cycle | values entered in `scenarios.py` (`GAVI_CUT_DEFAULT` 15, `GF_CUT_DEFAULT` 20) and the slider reference marks in `model_section.py` | % | Scenarios (Global Fund & Gavi Shortfalls; the 23% US Global Fund cut in the US exit presets) | Default slider values and the US Global Fund pledge cut |

### Government Response

| Dataset | Producer | Version or year | What it contains | File path | Units and currency | Model step | Used for |
|---|---|---|---|---|---|---|---|
| Global Health Spending 1995-2023 | IHME | released September 2026 (`Y2026M09D21`) | Government, out-of-pocket, prepaid private and development-assistance health spending by country-year | `datasets/IHME_HEALTH_SPENDING_1995_2023_Y2026M09D21.CSV`; columns `ghes_2023`, `ghes_growth_median`, `ghes_growth_p75`, `ghes_growth_p90`, `ghes_pc_2023`, `ghes_pct_gdp_2023` in `country_inputs.csv`; `model_data/panel.csv` | constant 2023 US$ (thousands in the raw file) | Government Response | Fiscal space (government health spending and its growth history); the fiscal-replacement regression |
| Expected Health Spending 2024-2050 | IHME | released September 2026 (`Y2026M09D23`) | Projected government and donor health spending | `datasets/IHME_EXPECTED_HEALTH_SPENDING_2024_2050_Y2026M09D23.CSV`; columns `ghes_2026_expected`, `dah_2026_expected`, `ghes_2030_expected` | constant 2023 US$ | Government Response (context columns) | Expected spending shown with the fiscal panel |
| GDP 1960-2050 (Financing Global Health 2026) | IHME | released June 2026 (`Y2026M06D11`) | GDP and GDP per person by country-year | `datasets/IHME_GDP_1960_2050_FGH_2026_Y2026M06D11.CSV`; column `gdp_pc` in `country_inputs.csv`; `panel.csv` | constant 2023 US$ | Government Response; Services Lost (income group guess and the legacy staff-cost scaling) | GDP per person for the regression panel and cost fallbacks |
| World Economic Outlook, October 2026 (general government balances) | IMF | October 2026 (downloaded 13 October 2026) | Primary balance, overall balance and revenue as % of GDP, 2000 onward | `datasets/IMF_WEO_Oct2026_GG_balances_2026-10-13.csv`; processed `macro_data/weo_fiscal/weo_balances.csv`; columns `interest_pct_revenue`, `interest_imf` in `country_inputs.csv` | % of GDP | Government Response | Net interest as a share of revenue (the debt-stress factor), where more recent than the World Bank series |
| World Development Indicators (25 series) | World Bank, via the Gapminder open-numbers mirror | downloaded 2026 (latest year per country, 2010-2024) | Government revenue, debt, interest payments and expenditure as % of GDP or revenue; health share of government spending; HIV, TB, malaria and immunization coverage; population and births; under-5 mortality; UHC index | `ext_data/wdi/*.csv` (series listed in `prepare_model.WDI`); `ext_data/wdi/sh_xpd_ghed_ge_zs.csv` read directly by `health_model.health_share` | % and counts | Government Response; Coverage; Health Outcomes (legacy vaccine rule); Validation | Interest % of revenue (`GC.XPN.INTP.RV.ZS`), health share of government spending (`SH.XPD.GHED.GE.ZS`), DTP3 (`SH.IMM.IDPT`), TB detection (`SH.TBS.DTEC.ZS`), ART and PMTCT coverage fallbacks, HIV incidence (`SH.HIV.INCD.TL`), population (`SP.POP.TOTL`), crude birth rate (`SP.DYN.CBRT.IN`), under-5 mortality (`SH.DYN.MORT`), bednet surveys (`SH.MLR.NETS.ZS`), fever treatment surveys (`SH.MLR.TRET.ZS`); the regression panel |
| World Bank country classification (income groups) | World Bank, via the Gapminder open-numbers mirror | 2026 | Income group and region per country | `ext_data/wb_country_entities.csv`; column `income_group` in `country_inputs.csv` | n/a | Government Response (interest fallback by income group); Services Lost (TB and ART cost fallbacks by income group) | Income-group medians where a country has no own value |

### Services Lost (Costs And The Donor-Funded Pool)

| Dataset | Producer | Version or year | What it contains | File path | Units and currency | Model step | Used for |
|---|---|---|---|---|---|---|---|
| Unit Cost Study Repository, HIV adult ART records | Global Health Cost Consortium | export of 14 October 2026; studies 2015-2018 | 99 unit-cost records, 12 countries, perspective, output unit, above-service costs flag | `datasets/GHCC_UCSR/GHCC_UCSR_HIV_ART.xlsx`; via `audit/batch34_art_costs.py` to `art_site_cost` in `country_inputs.csv` | 2020 US$ (inflated to 2023 with the US CPI-U) | Services Lost | Site-level ART cost per patient-year by country (pooled with Rosen 2021) |
| Unit Cost Study Repository, TB treatment records | Global Health Cost Consortium | export of 14 October 2026; studies 2015-2021 | 1,370 unit-cost records, 12 countries | `datasets/GHCC_UCSR/GHCC_UCSR_TB.xlsx`; via `audit/batch34_tb_costs.py` to `tb_ds_cost`, `tb_dr_cost` | 2020 US$ | Services Lost | South Africa TB course costs (Vassall 2017; Cox 2015) |
| Value TB pooled patient-level cost dataset | Value TB consortium (Sweeney et al.) | 2018 prices | Facility and patient costs per TB treatment phase, five countries, four cost variants | `datasets/ValueTB/ValueTB_pooled_patient.dta` (+ codebook) | 2018 US$ | Services Lost | Drug-susceptible and drug-resistant course costs for Ethiopia, India, Kenya, Philippines; the financial / economic ratio applied to GHCC ART records |
| Project unit-cost reference table | project table compiled from Rosen et al. 2021 and Laurence, Griffiths & Vassall 2015 | 2018-2020 (ART); 2014 inflated to 2023 (TB) | Five Rosen ART site costs, ART default components, TB course costs by income group | `unit_cost_reference.csv` | US$ with `cost_year` per row (inflated by `health_model.inflate`) | Services Lost | The ART cost floor (lowest Rosen site cost) and the fallbacks when a country column is missing |
| Optima HIV appendix Table B2 (ten Brink et al. 2025) | Burnet Institute (Optima HIV) | GAM expenditure, most recent year per country (2019-2023) | Total HIV spending by country, domestic, PEPFAR, other international | `datasets/Optima_tenBrink2025_appendix.pdf` p. 8; values entered in `audit/batch4b_art_check.py` (`B2`) | nominal US$ of the spending year | Services Lost | Observed HIV treatment spending per person on ART for 15 Optima countries; the Global Fund share validity test |
| Global Health Expenditure Database (December 2025 update) | WHO | data to 2023, latest year per country 2016-2023 | Spending on HIV/AIDS and STDs, malaria and immunization by financing source (external, domestic government, private) | `datasets/WHO_GHED/GHED_data_2026-10-14.xlsx` (sheet `Data`: `dis11_*`, `dis13_*`, `hc62_*`); via `audit/batch34_donor_share.py`, `audit/batch56_donor_share.py`, `audit/batch4b_art_check.py` to `donor_share_hiv`, `donor_share_imm`, `donor_share_malaria`, `donor_share_malaria_prev`, `art_cost_full` | million current US$ and NCU | Services Lost (donor-funded pool; ART observed spending outside the Optima countries) | External share of public spending on HIV and immunization; total HIV spending for 28 countries |
| Global Fund Data Explorer (grant budgets by module, expenditures by module, disbursements) | The Global Fund | downloaded 14 October 2026; Grant Cycle 7 (2023-2025); disbursements 2002-2025 | Budgets and expenditures by module and intervention; disbursements by grant and date | `datasets/GlobalFund/GF_budgets_2026-10-14.csv`, `GF_expenditures_modules_2026-10-14.csv`, `GF_disbursements_2026-10-14.csv`; via `audit/batch34_gf_shares.py` and `audit/batch56_art_cost.py` to `unspec_<disease>_*` and `art_cost_full` | reference-rate US$ (nominal) | Services Lost | Split of unspecified aid by purpose (treatment, prevention, testing, systems, management); the treatment share in the ART observed-spending measure; the Global Fund share of HIV spending (validity test) |
| WHO Global TB Programme financing files (budget; expenditure and utilisation) | WHO | 2024 expenditure, 2025 budgets | Funding received by source; budgets by line | `datasets/WHO_TB/TB_budget_2026-10-14.csv`, `TB_expenditure_utilisation_2026-10-14.csv`; via `audit/batch34_donor_share.py` to `donor_share_tb` | nominal US$ | Services Lost; Validation | External share of TB funding (the TB donor-funded pool); budget per notified patient (validation) |

### Coverage (People In Need And Baseline Coverage)

| Dataset | Producer | Version or year | What it contains | File path | Units and currency | Model step | Used for |
|---|---|---|---|---|---|---|---|
| Global Health Observatory (8 indicators) | WHO (UNAIDS/WHO HIV estimates; World Malaria Report malaria estimates) | 2025 (HIV), 2024 (malaria); downloaded via the GHO API | People living with HIV; ART coverage; PMTCT coverage and number of women on ARVs; malaria deaths, cases, incidence; ITN use | `ext_data/gho/HIV_0000000001.csv`, `HIV_ARTCOVERAGE.csv`, `HIV_0000000020.csv`, `HIV_0000000016.csv`, `MALARIA_EST_DEATHS.csv`, `MALARIA_EST_CASES.csv`, `MALARIA_EST_INCIDENCE.csv`, `MALARIA_ITN_USE.csv`; via `who_inputs.py` to `plhiv`, `sh_hiv_artc_zs`, `sh_hiv_pmtc_zs`, `hiv_pos_pregnancies`, `malaria_deaths`, `malaria_pop_at_risk`, `trend_malaria_deaths` | counts, %, per 1,000 at risk | Coverage; Health Outcomes (malaria baseline deaths and trend) | People in need and coverage for ART and PMTCT; malaria deaths, population at risk and the 2015-2024 death trend |
| Gapminder Systema Globalis (8 series mirroring WHO, UNAIDS and WHO/MCEE estimates) | Gapminder (mirror of WHO Global TB Report and WHO/MCEE child-cause estimates) | downloaded 2026; latest year per country | TB incidence and deaths (all forms, HIV-positive); PLHIV; child deaths from malaria, measles and pneumonia (1-59 months) | `ext_data/sg/ddf--datapoints--*.csv` (series in `prepare_model.SG`); columns `all_forms_of_tb_incidence_estimated`, `tb_hiv_share`, `tb_deaths_total`, `malaria_deaths_in_children_1_59_months_total_deaths`, `vpd_child_deaths` | counts | Coverage (TB need); Health Outcomes (TB-HIV share); Validation (Poisson regressions); the legacy malaria under-5 rule | TB incidence and the HIV share of TB; child cause-of-death series for the regression panel |
| Malaria Atlas Project national estimates (effective treatment, ITN access and use, IRS coverage, P. falciparum and P. vivax clinical cases) | Malaria Atlas Project | 2025 (downloaded 13 October 2026) | Modelled national coverage and case estimates by year | `datasets/MAP_national_*_2026-10-13.csv`; processed `ext_data/map/treatment.csv`, `itn.csv`, `irs.csv`, `pf_cases.csv`, `pv_cases.csv`; via `malaria_inputs.py` to `mal_cm_cov`, `mal_itn_cov`, `mal_irs_cov`, `malaria_cases` | % and counts | Coverage; Services Lost (malaria donor shares) | Malaria coverage and cases for the three malaria lines |
| WHO Global TB Programme burden, notifications and drug-resistance files | WHO | 2024 (downloaded 14 October 2026) | TB incidence and mortality estimates; notifications and RR-TB treatment starts; RR-TB incidence; WHO region per country | `datasets/WHO_TB/TB_burden_countries_2026-10-14.csv`, `TB_notifications_2026-10-14.csv`, `MDR_RR_TB_burden_estimates_2026-10-14.csv`; via `audit/batch34_tb_costs.py` to `tb_rr_share`, `tb_rr_cov`; `ext_data/who_regions.csv` | counts, per 100,000 | Coverage (drug-resistant TB need and coverage); Health Outcomes (WHO region for the malaria under-5 share and every regional median); Validation | RR-TB share of incidence and enrolment; WHO regions; validation benchmarks (deaths, notifications) |
| AIDSinfo 2026 estimates | UNAIDS | 2025 data (2026 estimates round) | New infections, PLHIV, suppressed viral load, people receiving ART, with bounds | `datasets/UNAIDS_2026/UNAIDS_Estimates_2026.csv`; via `hiv_transmission_inputs.py` to `art_transmission_rate` (+ `_lo`, `_hi`, `_year`); via `audit/batch4b_art_check.py` to the ART observed-spending denominator | counts (unrounded `Data value`) | Health Outcomes (HIV transmission); Services Lost (ART cost); Validation (people on ART) | Transmission per person with unsuppressed viral load; people on ART per country |

### Health Outcomes

| Dataset | Producer | Version or year | What it contains | File path | Units and currency | Model step | Used for |
|---|---|---|---|---|---|---|---|
| VIMC vaccine impact estimates published with Toor et al. 2021 | Vaccine Impact Modelling Consortium | 2000-2030 (2015-2019 used) | Deaths averted by year of vaccination, by calendar year and by birth cohort, 10 pathogens, 112 countries, with credible intervals | `datasets/Toor2021/VIMC_deaths_by_year_of_vac.csv`, `VIMC_deaths_by_cross_section.csv`, `VIMC_deaths_by_cohort.csv`; via `audit/batch56_vaccines.py` to `imm_dpc`, `imm_dpc_lo`, `imm_dpc_hi`, `imm_dpc_lag0` to `imm_dpc_lag9` | counts of deaths | Health Outcomes (vaccines) | Deaths averted per fully immunized child by country and their timing by years since vaccination |
| WHO/UNICEF Estimates of National Immunization Coverage (WUENIC), 2025 revision | WHO and UNICEF | released July 2026 | Coverage by antigen and year, 1980-2025; WHO region | `datasets/WUENIC_2025.xlsx` (sheet `country`) | % | Health Outcomes (vaccines) | Vaccinated-children denominators (2015-2019) and which antigens each country uses (2025 coverage above zero) |
| World Population Prospects 2024, medium variant | UN DESA Population Division | 2024 revision | Births, surviving infants, under-5 mortality (Q5), population, 1950-2101 | `datasets/WPP2024/WPP2024_Demographic_Indicators_Medium.csv` | thousands (x 1,000); per 1,000 | Health Outcomes (vaccines) | Surviving infants (denominator), the Q5 2026-30 / 2015-19 adjustment; population for deaths per 100,000 in the slide numbers |
| World Malaria Report 2025 | WHO | 2025 (2024 data) | Regional under-5 shares of malaria deaths; funding and net distribution context | `datasets/WHO_World_Malaria_Report_2025.pdf` (sections 2.3-2.8, chapter 4); values in `model_params.csv` (`mal_u5_share_afr`, `_amr`, `_emr`, `_sea`, `_wpr`) | % | Health Outcomes (malaria) | The under-5 share of malaria deaths by WHO region |
| Optima HIV appendix Tables A1-A2 (ten Brink et al. 2025) | Burnet Institute (Optima HIV) | 2025 | Untreated CD4 progression times and stage death rates; relative death rate on suppressive ART | `datasets/Optima_tenBrink2025_appendix.pdf` pp. 2-3; used by `audit/batch2_cohort.py` to derive `health_model.ART_HAZARD` | rates per year | Health Outcomes (HIV) | The excess death risk by years since stopping ART |
| Gapminder fasttrack: IHME HIV share of all deaths | IHME (GBD 2019), via Gapminder | 2019 | HIV deaths as % of all deaths | `ext_data/gm/ddf--datapoints--ihme_hiv_death--by--country--time.csv`; column `hiv_deaths_est` | % | Validation (Lancet rate-ratio method) | Baseline HIV deaths for the rate-ratio comparison on the Validation page |

### Validation

| Dataset | Producer | Version or year | What it contains | File path | Units and currency | Model step | Used for |
|---|---|---|---|---|---|---|---|
| Optima HIV appendix Table C2 (ten Brink et al. 2025) | Burnet Institute (Optima HIV) | 2025 | Cumulative 2025-2030 infections and HIV deaths by scenario for 26 countries | `datasets/Optima_tenBrink2025_appendix.pdf` p. 11; values entered in `audit/batch56_validation.py` (`OPTIMA_C2`) | counts | Validation | The HIV benchmark (scenario 5 minus status quo, 15 overlapping countries) |
| (also used here) WHO Global TB Programme files, UNAIDS AIDSinfo, WHO GHO malaria deaths, VIMC and Toor 2021 Table 3 | WHO, UNAIDS, VIMC | as above | | `audit/batch56_validation.py`; `audit/logic_review/validation.md` | | Validation | TB deaths, notifications and budgets; people on ART; malaria deaths; vaccine deaths per 1,000 children |

Dashboard context data (Sections 1 to 3, not read by the model): IHME DAH per-country files (`country_data/`),
IHME health spending (`spending_data/`), IMF WEO macro series (`macro_data/<ISO3>.csv`), IMF Government Finance
Statistics revenue (`revenue_data/`) and COFOG spending (`cofog_all/`), built by a script that is not in the
repository (logic review L-38). `health_model.health_share` reads `spending_data/` and `macro_data/` only as a
fallback when the World Bank health-share series is missing.

## Table B. Published Studies Cited For Parameter Values

| Study (author, year, journal or publisher) | Parameter(s) supplied | Value used | Table or page |
|---|---|---|---|
| Gaba, Razavi, Kates & Nandakumar 2025, KFF, "Which PEPFAR Investments Drive HIV Outcomes?" | `asd_share` (above-site programme share) | 0.45 (0.30-0.55) | non-service delivery 47% of PEPFAR spending, 22 countries, 2018-2023 |
| Rosen et al. 2021, Gates Open Research 5:177 (AMBIT synthesis) | ART site costs (`unit_cost_reference.csv`); the ART cost floor; pooled into `art_site_cost` | Malawi 86.50, Zambia 116.05, Lesotho 122.28, Uganda 152.49 (2018 US$), Zimbabwe 187.04 (2020 US$); floor US$190.84 after inflation and markup | conventional facility care per country |
| ten Brink et al. 2025, Lancet HIV (Optima HIV), appendix | total HIV spending (ART observed spending); CD4 progression and death rates (`ART_HAZARD`); validation benchmark | Table B2 totals; Tables A1-A2 rates; Table C2 outcomes | pp. 2-3, 8, 11 |
| ZIMPHIA 2020 (Zimbabwe Population-based HIV Impact Assessment) | starting CD4 distribution of people on ART (`ART_HAZARD` derivation) | median 528 cells/uL (Q1 366, Q3 706) | Table 10.1, p. 89 |
| Brinkhof et al. 2009; Zurcher et al. 2017; Kaplan et al. 2017 (PLoS Med) | cross-checks on the ART hazard | 40%, 24%, 3% mortality among people lost to follow-up | cited in `model_params.csv` `art_hazard_mult` |
| Kranzer et al. 2010, JAIDS 55:e17; Kaplan et al. 2017, PLoS Med 14:e1002407; Mody et al. 2026, PLoS Med 23:e1005052 | `art_reengage` | 0.35 (0.17-0.68) a year | 42% within 3 years; about 50% by 2.5 years; 67.7% within 12 months |
| Giguere et al. 2021, Lancet HIV 8:e284 (Shiny90) | `hiv_new_inf_unsup_years` (basis of the assumption) | 4 (2.5-5.5) years | median time to diagnosis 2.6 years |
| Donnell et al. 2010, Lancet 375:2092 | cross-check on the transmission rate | 2.24 per 100 person-years in serodiscordant couples | cited in `art_transmission_mult` |
| Health Policy and Planning 2016;31(8):1133 (review of Option B+ cost-effectiveness analyses) | `uc_pmtct` | 250 (150-450) US$ per woman-year | annual costs of five studies (US$114-470) |
| WHO AFRO (PMTCT transmission) | `pmtct_vt_reduction` | 0.25 (0.10-0.40) | 15-45% without, under 5% with intervention |
| Newell et al. 2004, Lancet (pooled analysis) | `pmtct_infant_mort` | 0.45 (0.35-0.525) | 35.2% dead by age 1, 52.5% by age 2 |
| Todd et al. 2007, AIDS 21 Suppl 6 (ALPHA network); CASCADE | `hiv_survival_median`, `hiv_inf_death_untreated`; Weibull shape 2.25 (UNAIDS Spectrum) | 10.5 (8.6-12.5) years; 0.85 (0.70-0.95) | median survival by age at infection |
| Sweeney et al., Value TB (patient-level dataset) | `tb_ds_cost`, `tb_dr_cost` for Ethiopia, India, Kenya, Philippines; financial / economic ratio | DS 218 / 105 / 150 / 120; DR Kenya 2,818, Philippines 1,580 (2018 US$) | financial bottom-up, intensive + continuation phase |
| Vassall et al. 2017 (GHCC repository, South Africa) | `tb_ds_cost`, `tb_dr_cost` South Africa | DS 274; DR 9,256 (2023 US$) | GHCC UCSR records |
| Cox et al. 2015 (GHCC repository, South Africa) | `tb_dr_cost` South Africa (pooled) | with Vassall 2017 | GHCC UCSR records |
| Laurence, Griffiths & Vassall 2015, PharmacoEconomics | TB course costs by income group (pooled with the country studies) | DS 258 / 273 / 840 and DR 1,218 / 6,313 / 5,284 (2014 US$) x 1.287 | income-group means |
| WHO TB burden estimation methods (Glaziou et al.) | `tb_cfr_untreated_neg`, `tb_cfr_treated_neg`, `tb_cfr_untreated_pos`, `tb_cfr_untreated_pos_art`, `tb_cfr_treated_pos` | 0.43 / 0.03; 0.78 (0.65-0.94); 0.49 (0.31-0.70); 0.06 | Table 4; Table 5, p. 28 |
| Styblo 1991, Bull Int Union Tuberc Lung Dis; Vynnycky & Fine 1997, Epidemiol Infect; WHO (smear-positive share) | `tb_secondary` (derived) | 0.4 (0.2-0.8) cases per untreated patient-year | 10 infections a year x 60% smear-positive x 5-10% progression |
| GiveWell, insecticide-treated net analysis | `uc_itn` | 2.2 (1.4-3.5) US$ per person-year of net use | US$4-6 per net, 1.8 people per net, about 2 years, about 63% used |
| PMI Africa IRS project, Mali 2012-14 (Malaria Journal 2018, s12936-017-2168-2) | `uc_irs` | 8.5 (6-10) US$ per person-year | US$6.08-7.40 per person covered (2014 US$) x 1.287 |
| White et al. 2011, Malaria Journal 10:337 (systematic review) | `uc_mal_cm` | 14 (4-47) US$ per case | median US$5.84 treatment + US$4.32 diagnosis (2009 US$) x 1.42 |
| Eisele, Larsen & Steketee 2010, Int J Epidemiol (Lives Saved Tool) | `mal_vc_eff` | 0.55 (0.40-0.61) | 55% (49-61%) |
| Thwing, Eisele & Steketee 2011, BMC Public Health 11(Suppl 3):S14 | `mal_cm_eff` | 0.97 (0.82-0.99) | abstract: 97% (86-99%) at 24-59 months; 82% severe malaria |
| Cohen et al. 2012, Malaria Journal 11:122 | direction of `mal_resurgence` (the size is an assumption) | 0.10 (0-0.25) a year | 75 resurgence events, 61 countries |
| WHO World Malaria Report 2025 | `mal_u5_share_afr`, `_amr`, `_emr`, `_sea`, `_wpr`; net lifespan note | 0.75, 0.20, 0.364, 0.25, 0.40 | sections 2.3-2.8 (pp. 20, 24, 28, 31-32, 35); p. 20 |
| Lydon et al. 2014, Bull WHO 92:382 | `uc_imm` (delivery component) | US$32.6 per infant (2010 US$) = 45.6 in 2023 US$ | non-vaccine health-system cost per infant 2016-20 |
| MSF, The Right Shot 2015 | `uc_imm` (vaccine component and high end) | US$32.09-45.59 (2014 US$) = 41.3-58.7 in 2023 US$ | price to fully vaccinate a child, poorest countries |
| Brenzel 2015, Vaccine | `uc_imm` (low end) | US$27 (2010 US$) = 38 in 2023 US$ | full cost per DTP3-vaccinated child, Gavi cMYPs |
| Toor et al. 2021, eLife 10:e67635 (VIMC) | `imm_dpc*` country values (via the VIMC data); the 0.1-10x gate | median 0.025 deaths averted per fully immunized child; gate values measles 6.5, HepB 7.7, YF 2.1, Hib 2.4, PCV 2.3, rubella 0.3, Rota 0.8, MenA 1.0 per 1,000 FVPs | Table 3, p. 9; Methods |
| Cavalcanti et al. 2025, Lancet | fallback mortality trend; Lancet rate-ratio method (Validation page) | -0.009 a year; rate ratios HIV 0.83 / 0.81 / 0.50, malaria 0.94 / 0.78 / 0.58, maternal 0.91 / 0.83 / 0.67 at US$0.71 / 1.37 / 5.76 per person | appendix 10.2; Web Table 19 |
| Global Fund news release, 30 August 2023 (TLD price); CHAI 2015 (viral load access price) | the superseded US$57 ART floor (Batch 4b), recorded in `art_cost_full_source` history | US$45 + US$12.08 | superseded by the Rosen-based floor in Batch 5+6 |
| Li et al. 2021, Lancet (VIMC); Gavi (deaths averted per child) | legacy `imm_u5_share` 0.65 and `imm_deaths_per_child_ref` 0.020 | used only when `imm_legacy_u5mr_scaling` = 1 | 38M hepatitis B vs 58M measles deaths averted; 20.6M / 1.2B |

Evidence reviewed but not used for a value: Shattock et al. 2024, Lancet (no per-child deaths averted for DTP, polio
or BCG); KFF April 2026, Cust & Chabata 2026 (Lancet Global Health) and WHO Global TB Report 2025 (continuity;
none measures the quantity, so `continuity` stays an assumption).

## Table C. Labelled Assumptions (No Source)

| Parameter | Value | Range | Why no evidence exists |
|---|---|---|---|
| `continuity` | 0.15 | 0-0.30 | No study measures the share of patients who keep the same service after its donor funding is withdrawn in a low- or middle-income country; the 2025 evidence covers partial withdrawals with commodities still flowing |
| `hss_kappa` | 0.5 | 0.25-0.9 | Testing-and-care money funds a flow of diagnoses and retention, not a stock of patients; no cost per initiation exists to model the flow |
| `hss_service_share` | 0 | constant (0.5 as a sensitivity case) | No study quantifies how much systems money (labs, HR, M&E, supply chain) becomes service delivery; the unit-cost markup already prices above-site costs |
| `cpia_ref` | 5,000 US$ per infection averted | 2,500-12,000 | Prevention mixes differ by country; no single cost per infection averted; affects infections only |
| `uc_ovc` | 100 US$ per child-year | 60-160 | No mortality effect is modelled, so the value only sizes the money |
| `uc_scale_elast` | 0.4 | 0.25-0.6 | Staff costs rise with income while drugs are priced globally; used only in a fallback |
| `tb_dr_dcfr` | 0.45 | 0.30-0.60 | No WHO table gives a treated-versus-untreated fatality pair for rifampicin-resistant TB |
| `mal_adult_effect_frac` | 0.5 | 0-1 | No published Lives Saved Tool effect size for ages 5 and over |
| `mal_resurgence` | 0.10 a year | 0-0.25 | Resurgence is documented (Cohen 2012) but its speed varies widely; the size is not measured |
| `mal_itn_default_use` | 0.50 | 0.40-0.60 | Used only where no MAP estimate or survey since 2015 exists |
| `mal_cm_default_cov` | 0.40 | 0.30-0.50 | Used only where no MAP value or usable survey exists (no malaria country needs it) |
| `hiv_new_inf_unsup_years` | 4 years | 2.5-5.5 | Time to diagnosis is measured; the time a newly infected person transmits before suppression is not |
| `hiv_inf_death_treated` | 0.10 | 0.05-0.20 | Near-normal life expectancy on ART; allowance for late diagnosis and interruptions is not measured |
| `mal_u5_share_*` ranges | plus or minus 5 points | | WHO gives point estimates (or a bound) without ranges |
| Malaria death-trend clip | plus or minus 5% a year | | Keeps short, noisy WHO series from projecting far; no source |
| Under-5 mortality trend clip | -8% to +2% a year | | As above (legacy vaccine rule) |
| Fiscal-space thresholds | debt stress 1 at 10% interest / revenue, 0.25 at 40% | | Thresholds unsourced (logic review L-29) |
| Ramp-up shares (LAG) | PMTCT 0.6, TB 0.7, bednets 0.5, spraying 0.8 in year 1 | | How fast each service's full effect appears is not measured |
| Vaccine deaths at age 5 and over for meningitis A and yellow fever | 0 within the window | | The all-age VIMC timing fit does not identify them; counted as lifetime deaths beyond 2035 (conservative) |
| Spraying coverage implied by donor money | people donor IRS money pays for / population at risk, where larger than MAP | | MAP models IRS for Africa only and shows 0 in some countries where donors fund spraying |

## Table D. Files Present In The Repository But Not Used By The Current Model

| File | Why it is not used |
|---|---|
| `ext_data/reference/wdi/*.csv` (7 World Bank series: GDP per person, communicable-disease death share, infant deaths, neonatal mortality, HepB3 coverage, UHC infectious sub-index, government health spending % of GDP) | Downloaded as possible cross-checks; not in `prepare_model.WDI` and nothing reads the folder (`ext_data/reference/README.md`) |
| `ext_data/reference/sg/*.csv` (9 Gapminder series: TB treatment coverage, HIV deaths, child HIV deaths, reported malaria cases and deaths, meningitis and pertussis child deaths, new HIV infections, child deaths) | Same; kept as benchmarks, not read by any script |
| `ext_data/gho/MALARIA_ITN_USE.csv` | Downloaded by `who_inputs.py`; bednet coverage now comes from the Malaria Atlas Project ITN-use series (`malaria_inputs.py`), so this series is superseded |
| `ext_data/map/incidence_prevalence.csv` and `datasets/MAP_national_incidence_prevalence_2026-10-13.csv` | Processed by `malaria_inputs.process()` but `apply()` uses only treatment, ITN, IRS and the two case files |
| `datasets/GlobalFund/GF_allocations_2026-10-14.csv` | Downloaded for IMP-13 (allocation cuts); the shortfall preset uses user-set slider cuts, so the file is not read |
| `datasets/WPP2024/WPP2024_PopulationByAge5GroupSex_Medium.csv` | Downloaded for the vaccine denominators; the Demographic Indicators file (surviving infants, births, Q5) was sufficient |
| `datasets/Gavi-Country-Financial-Data-FY2021-25_052026 (4).xlsx` | Intended for a cost per child by antigen (IMP-15); that part is not implemented |
| `datasets/mmc1.pdf` | Byte-identical duplicate of `datasets/Optima_tenBrink2025_appendix.pdf` |
| `datasets/world_bank_health_expenditure_as_percent_of_GDP.csv` | Not read by any script; the health share of government spending comes from the WDI series `sh_xpd_ghed_ge_zs` |
| `datasets/dataset_2026-10-06T19_34_47...IMF.FAD_WORLD_3.0.1.csv` | IMF Fiscal Affairs data used by the Sections 1-3 build script, which is not in the repository (L-38); the model does not read it |
| `datasets/IHME_DAH_DATABASE_1990_2026_CB_Y2026M09D18.csv`, the DAH info sheet and user guide PDFs, `datasets/ValueTB/ValueTB_codebook.docx` | Codebooks and documentation, read by people, not by the code |
| `datasets/~$co-financing_MOU.xlsx` | Excel lock file |
| `audit/recompute.py`, `audit/logic_review/build_inputs.py` and the other `audit/*.py` audit scripts not listed in Table A | Audit tools that read the model outputs or earlier inputs; they do not feed the model |
| `model_params.csv` rows `art_transmission`, `imm_deaths_per_child_ref`, `imm_u5_share` | Legacy parameters, used only when the sensitivity switches `hiv_legacy_art_params` or `imm_legacy_u5mr_scaling` are set to 1 |
| `country_inputs.csv` columns `sh_tbs_cure_zs`, `sh_imm_meas`, `sh_uhc_sci`, `sh_hiv_0014`, `sp_pop_1564_to`, `sp_pop_0014_to`, `gc_dod_totl_gd_zs`, `gc_xpn_totl_gd_zs`, `malaria_cases_prev`, `donor_share_malaria` (all-source), `donor_share_malaria_prev` | Downloaded or kept for the Validation page, the fiscal panel, or as the fallback when a newer column is missing; not used in the central calculation |
