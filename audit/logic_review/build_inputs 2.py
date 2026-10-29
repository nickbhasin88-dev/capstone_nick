"""
Builds inputs.csv (Part 1 of the logic review): one row per input the model or the dashboard uses. Read-only with
respect to the model: it only reads model_data/country_inputs.csv to count years, sources and fallbacks.

    .venv/bin/python audit/logic_review/build_inputs.py
"""
import csv
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
ci = pd.read_csv(ROOT / "model_data/country_inputs.csv")
dl = pd.read_csv(ROOT / "model_data/dah_lines.csv")
m = ci[ci.iso3.isin(dl.iso3.unique())]          # the 70 countries with modelled aid lines


def yrs(col):
    if col not in m:
        return ""
    v = m[col].value_counts(dropna=False)
    return "; ".join(f"{'none' if pd.isna(k) else int(k)}: {n}" for k, n in v.items())


def srcs(col):
    if col not in m:
        return ""
    return "; ".join(f"{k}: {n}" for k, n in m[col].value_counts(dropna=False).items())


F = ["id", "group", "name_in_code", "defined_at", "used_at", "affects", "model_needs", "source", "source_definition",
     "production", "years_used", "latest_available", "concept_match", "match_reason", "currency", "fallback",
     "n_fallback_of_70", "status", "confidence", "finding"]
R = []


def add(group, name, defined, used, affects, needs, source, definition, production, years, latest, match, reason,
        currency, fallback, nfb, status, conf, finding="no issue"):
    R.append(dict(zip(F, [f"I-{len(R) + 1:03d}", group, name, defined, used, affects, needs, source, definition,
                          production, years, latest, match, reason, currency, fallback, nfb, status, conf, finding])))


CI = "model_data/country_inputs.csv"
# ---------------------------------------------------------------- aid
add("aid", "dah_lines.csv: aid by country x donor x channel x line (A)", "prepare_model.py:294-318 (BASE_YEARS :40)",
    "health_model.py:609-626 (gross loss), :638-658 (effective)", "every Section 4 number; All Countries; Validation",
    "Yearly donor money currently paying for each HIV/TB/malaria/immunization service in the country, US$/yr, constant 2023 US$, by donor and channel",
    "IHME Financing Global Health, DAH Database 1990-2026 (GHDx, file Y2026M09D18)",
    "IHME DAH = 'financial and in-kind contributions ... channelled through major health development agencies ... to low- and middle-income countries' (DAH User Guide); program-area columns e.g. hiv_treat, tb_treat, mal_con_nets, nch_cnv",
    "administrative + IHME estimation (project databases, imputed for some channels)", "average of 2021, 2022, 2023; elim_ch == 0",
    "same release (Sept 2026) has 2024 actuals and 2025-26 preliminary totals, but not by recipient for 2025-26",
    "close", "Correct concept for donor money; but 2021-23 levels overstate what was still flowing in 2025 (US -67% in 2025, IHME FGH 2025)",
    "current release; base years old", "global program-area mix if a country has none", "0", "sourced", "High", "L-06")
add("aid", "unspecified / systems money spread (mix, kappa)", "health_model.py:638-658", "every line's effective loss",
    "people losing service, deaths", "How much of untagged and health-system money pays for each service",
    "IHME program areas hiv_other, hiv_hss_*, tb_other, tb_hss_*, mal_other, mal_hss_*", "IHME: '_other' = not assigned to a program area; '_hss' = health systems strengthening (DAH codebook)",
    "our allocation rule", "2021-23", "", "mismatch", "Unspecified money goes 100% to services (TB: US$700M of 1,522M); kappa has no source", "n/a", "", "", "assumption", "High", "L-05, L-27, L-43")
add("aid", "IHME 2025 ratios (ihme_trend.csv)", "prepare_model.py (ihme_trend)", "health_model.py:181-197", "IHME 2025 preset",
    "2025 donor money relative to 2021-23 by donor x channel x disease", "IHME DAH 1990-2026, preliminary 2025",
    "IHME FGH 2025: DAH 2025 US$39.1B, 'declined 21% between 2024 and 2025'", "IHME preliminary estimates (budgets, appropriations)",
    "2025 / 2021-23 avg", "2026 preliminary also in file", "close", "Global ratio applied to every country's mix; no recipient detail exists", "current", "", "", "sourced", "High", "L-06")
add("aid", "dah_nch_base, us_health_aid_base", "prepare_model.py:386-387", "health_model.py:1297, :1352 (Validation statistical and Lancet cross-checks)",
    "Validation page only", "Child-health aid and US health aid totals", "IHME DAH", "IHME DAH program area nch_cnv (child vaccines) and source = United States, 2021-23 average, elim_ch == 0", "administrative", "2021-23", "", "exact", "", "current", "0", "0", "sourced", "High")
# ---------------------------------------------------------------- HIV
add("HIV", "plhiv", "who_inputs.py:29-31 (GHO HIV_0000000001); fallback prepare_model.py:410", "health_model.py:305-330 (epi)",
    "ART need, coverage after, ART deaths (via cap)", "People living with HIV, all ages, latest year, number",
    "UNAIDS/WHO via WHO GHO HIV_0000000001", "'Estimated number of people (all ages) living with HIV' (GHO)",
    "modelled (UNAIDS Spectrum)", yrs("plhiv_year"), "UNAIDS 2026 round (2025 data, July 2026): 41.0M globally",
    "exact", "", "current", "adult prevalence x pop 15-64 x 2011 calibration + children", srcs("plhiv_source"), "sourced", "High")
add("HIV", "sh_hiv_artc_zs (ART coverage)", "who_inputs.py:31 (GHO HIV_ARTCOVERAGE); fallback WDI SH.HIV.ARTC.ZS", "health_model.py:305-330, :461 (TB CFR), :770 (ART pool)",
    "ART coverage card, covered pool, TB HIV+ CFR", "Share of PLHIV on ART, %", "UNAIDS/WHO via GHO HIV_ARTCOVERAGE",
    "'Estimated antiretroviral therapy coverage among people living with HIV (%)' (GHO)", "programme data / Spectrum",
    yrs("sh_hiv_artc_zs_year"), "2025 (UNAIDS 2026)", "exact", "", "current", "WDI (UNAIDS) older year", srcs("sh_hiv_artc_zs_source"), "sourced", "High")
add("HIV", "sh_hiv_pmtc_zs (PMTCT coverage)", "who_inputs.py:34 (GHO HIV_0000000020)", "health_model.py:305-330, :770",
    "PMTCT line coverage; ART pool exclusion", "Share of HIV+ pregnant women receiving ARVs, %", "UNAIDS/WHO via GHO HIV_0000000020",
    "GHO catalogue name 'Estimated number of pregnant women living with HIV' but values are % coverage (who_inputs.py:32-33)",
    "programme data / Spectrum", yrs("sh_hiv_pmtc_zs_year"), "2025", "exact",
    "Values checked as coverage (Kenya 2025 '91 [83-100]'); the GHO label is wrong, the code handles it", "current", "WDI SH.HIV.PMTC.ZS; else ART coverage", srcs("sh_hiv_pmtc_zs_source"), "sourced", "High")
add("HIV", "hiv_pos_pregnancies", "who_inputs.py (HIV_0000000016 / PMTCT %); fallback prepare_model.py:417", "health_model.py:305-330, :770",
    "PMTCT need; ART pool", "HIV+ pregnant women per year", "UNAIDS/WHO: women receiving ARVs / PMTCT coverage",
    "GHO HIV_0000000016 'pregnant women living with HIV who received ARVs for PMTCT'", "derived from two UNAIDS series",
    yrs("hiv_pos_pregnancies_year"), "2025", "exact", "", "current", "births x adult prevalence x 1.15 (factor unsourced)", srcs("hiv_pos_pregnancies_source"), "derived", "Medium")
add("HIV", "sh_hiv_incd_tl (new HIV infections)", "prepare_model.py:125 (WDI SH.HIV.INCD.TL via open-numbers mirror)", "health_model.py:310, :403 (prevention unit cost)",
    "Prevention unit cost -> infections from lost prevention", "New HIV infections per year", "World Bank WDI SH.HIV.INCD.TL (UNAIDS)",
    "'Adults (ages 15+) and children (ages 0-14) newly infected with HIV' (WDI)", "modelled (UNAIDS)", yrs("sh_hiv_incd_tl_year"),
    "2025 (UNAIDS 2026)", "exact", "", "one year behind (2024 vs 2025 via GHO)", "", "", "sourced", "High", "L-24 (minor currency)")
add("HIV", "hiv_deaths_est", "prepare_model.py:442", "health_model.py:1332 (Lancet cross-check); views/3_Validation.py:298",
    "Validation page Lancet comparison only", "HIV deaths per year", "IHME GBD HIV share of all deaths via Gapminder fasttrack x crude death rate x population",
    "Gapminder 'ihme_hiv_death' (% of all deaths)", "modelled (GBD 2019 release via mirror)", yrs("hiv_death_share_year"),
    "UNAIDS 2025 deaths (GHO HIV_0000000006) or GBD 2023", "close", "Right concept; old (2019) and indirect", "outdated (2019)", "", "", "derived", "High", "L-11")
add("HIV", "ART site cost (Rosen et al. 2021) and default 95 + 23 x (GDPpc/1000)^0.4", "unit_cost_reference.csv rows 2-8; health_model.py:385-417",
    "health_model.py:438-450", "ART people losing, deaths, per-US$1M cards", "Cost of one patient-year on ART paid by donors, 2023 US$",
    "Rosen et al. 2021 Gates Open Res 5:177 (AMBIT)", "'average cost per patient per year ... conventional facility-based care' (site level incl. ARVs and labs)",
    "costing studies (5 countries); rest extrapolated", "2018-2020 prices x US CPI", "GHCC UCSR; PEPFAR expenditure analysis; UNAIDS HIV financing", "close",
    "Site cost; the model adds above-site share via asd_share. Five SSA countries only, applied to all 70", "dated (2018-20)",
    "default formula for 65 countries", "65", "sourced", "Medium", "L-26")
add("HIV", "CPI_U (US CPI deflators)", "health_model.py:354", "health_model.py:385-417", "unit costs", "Price index to convert to 2023 US$",
    "US BLS CPI-U annual averages", "CPI-U annual average", "official statistic", "2014-2023", "2025", "exact", "", "current", "", "", "sourced", "High")
# ---------------------------------------------------------------- TB
add("TB", "all_forms_of_tb_incidence_estimated (TB need)", "prepare_model.py:130 (Gapminder Systema Globalis mirror of WHO)", "health_model.py:305-330",
    "TB people losing cap, coverage after", "New TB cases per year, all forms", "WHO Global TB Programme estimates via Gapminder",
    "WHO: 'estimated number of incident cases (all forms)'", "modelled (WHO)", yrs("all_forms_of_tb_incidence_estimated_year"),
    "2024 (Global TB Report 2025); 2026 report due ~Nov 2026", "exact", "", "current", "", "0", "sourced", "High")
add("TB", "sh_tbs_dtec_zs (case detection rate)", "prepare_model.py:125 (WDI SH.TBS.DTEC.ZS)", "health_model.py:305-330", "TB coverage, cap",
    "Share of TB patients on treatment", "World Bank WDI SH.TBS.DTEC.ZS (WHO)",
    "'the number of new and relapse tuberculosis cases notified to WHO in a given year, divided by WHO's estimate of the number of incident tuberculosis cases for the same year' (WDI)",
    "administrative (notifications) / modelled denominator", yrs("sh_tbs_dtec_zs_year"), "2024", "close",
    "Notified = started on treatment (public + notified private); can exceed 100%", "current", "", "0", "sourced", "High", "L-12")
add("TB", "tb_hiv_share", "prepare_model.py:418 (clip 0-0.8)", "health_model.py:461-469, :840", "TB CFR, TB deaths",
    "Share of TB cases that are HIV-positive", "WHO TB estimates (HIV+ incidence / total incidence) via Gapminder",
    "WHO 'estimated incidence of TB among people living with HIV'", "modelled", "2024", "2024", "exact", "", "current", "", "0", "derived", "High")
add("TB", "tb_deaths_total", "prepare_model.py:419", "health_model.py:1295 (Validation statistical cross-check)", "Validation page",
    "TB deaths incl. HIV+", "WHO TB estimates via Gapminder", "WHO: deaths HIV-negative + HIV-positive TB deaths", "modelled", "2024", "2024",
    "exact", "Sum is correct: WHO reports HIV-negative TB deaths and HIV+ TB deaths separately", "current", "", "0", "derived", "High")
add("TB", "TB unit cost DS (Laurence 2015 income group)", "unit_cost_reference.csv rows 9-11", "health_model.py:385-417", "TB people losing, deaths",
    "Full cost of treating one DS-TB patient, 2023 US$", "Laurence, Griffiths & Vassall 2015, PharmacoEconomics 33:939",
    "'mean provider cost per patient treated' LIC 258, LMIC 273, UMIC 840 (2014 US$)", "literature synthesis", "2014 x1.287",
    "Sweeney et al. 2024 Lancet GH (India 450, Philippines 560, South Africa 730 per person treated); GHCC UCSR", "close",
    "Income-group means, divided by (1-asd) again; country studies exist for the top TB countries", "dated (2014)", "", "", "sourced", "Medium", "L-14 (unit cost part), improvement IMP-03")
add("TB", "TB unit cost DR (Laurence 2015)", "unit_cost_reference.csv rows 12-14", "health_model.py:385-417", "DR-TB people losing, deaths",
    "Cost per DR-TB patient treated", "Laurence et al. 2015 (single study per group)", "LMIC MDR-TB $6,313 (2014 US$)", "literature", "2014",
    "GDF BPaLM 'US$284 per course' (Sept 2025); WHO 6-month all-oral regimens", "mismatch", "18-24-month regimens, superseded", "outdated", "", "", "sourced", "High", "L-16")
add("TB", "DR_TB_SHARE = 0.04, DR_TB_COV = 0.45", "health_model.py:85", "health_model.py:305-330", "DR-TB need and coverage",
    "MDR/RR share of incident TB; share of DR-TB patients treated", "our constants",
    "WHO GTB 2025: ~390,000 MDR/RR-TB incident 2024 of 10.7M (3.6%); ~44% enrolled on treatment (WHO GTB 2024 key facts)",
    "assumption (global averages)", "", "WHO GTB country MDR/RR estimates and enrolments", "close", "Global average applied to every country (India ~ 2.5-3%, Pakistan ~3%)", "n/a",
    "", "70 (all)", "assumption", "Medium", "L-16")
# ---------------------------------------------------------------- malaria
add("malaria", "malaria_deaths (D0)", "who_inputs.py:35 (GHO MALARIA_EST_DEATHS); fallback prepare_model.py:423", "health_model.py:539-577",
    "malaria deaths", "Malaria deaths per year, all ages", "WHO World Malaria Report via GHO MALARIA_EST_DEATHS", "'Estimated number of malaria deaths'",
    "modelled (WHO)", yrs("malaria_deaths_year"), "2024 (WMR 2025); WMR 2026 due Dec 2026", "exact (for D0)",
    "D0 is all ages but effect sizes are for children (L-04)", "current", "child malaria deaths (MCEE 2021) / 0.76 (SSA) or 0.40", srcs("malaria_deaths_source"), "sourced", "High", "L-04")
add("malaria", "malaria_pop_at_risk", "who_inputs.py (cases / incidence); fallback prepare_model.py:424-425", "health_model.py:305-330, :539-577",
    "ITN and IRS need, malaria coverage drop", "People living in malaria-risk areas", "WHO WMR: estimated cases / incidence per 1,000 at risk",
    "WHO 'incidence per 1,000 population at risk'", "derived from WHO", yrs("malaria_pop_at_risk_year"), "2024", "exact", "", "current",
    "95% (SSA) or 35% of population (assumption)", srcs("malaria_pop_at_risk_source"), "derived", "High")
add("malaria", "malaria_cases (MAP Pf + Pv clinical)", "malaria_inputs.py:113", "health_model.py:539-577 (cm coverage drop denominator)",
    "treatment coverage drop", "Malaria cases needing treatment per year", "Malaria Atlas Project national unit data, 'Clinical Cases' Pf and Pv",
    "MAP: modelled incidence of clinical (symptomatic) cases", "modelled (geostatistical)", yrs("malaria_cases_year"),
    "MAP download 2026-10-13 (2025)", "close", "MAP and WHO differ >30% in 20 of 46 countries (Pakistan 14.4M vs 3.15M)", "current",
    "WHO estimate; derived", srcs("malaria_cases_source"), "sourced", "High", "L-23")
add("malaria", "mal_cm_cov (effective treatment)", "malaria_inputs.py:100", "health_model.py:539-577", "treatment coverage card, malaria deaths",
    "Share of malaria cases effectively treated", "MAP 'Effective Treatment' (in 100 malaria cases)",
    "'the fraction of malaria cases that were effectively treated' (PMC11549775)", "modelled", yrs("mal_cm_cov_year"),
    "2025 (MAP notes ITN and treatment 2025 repeat 2024, malaria_inputs.py:32)", "exact", "", "current (2024 value)",
    "0.40 default", srcs("mal_cm_cov_source"), "sourced", "High")
add("malaria", "mal_itn_cov (ITN use)", "malaria_inputs.py:123", "health_model.py:539-577", "bednet coverage card, deaths",
    "Share of at-risk population sleeping under a net", "MAP ITN 'Use' (in 100 people); else WDI SH.MLR.NETS.ZS survey from 2015",
    "MAP: 'proportion of the population sleeping under an ITN'; WDI: 'children under age five sleeping under insecticide-treated bednets'",
    "modelled; survey", yrs("mal_itn_cov_year"), "2025", "exact (MAP); close (survey: children under 5 only)",
    "8 countries use the under-5 survey figure for the whole population", "current (MAP); surveys 2016-2021", "0.50 default",
    srcs("mal_itn_cov_source"), "sourced", "High", "L-07")
add("malaria", "mal_irs_cov (spraying) and the max() rule", "malaria_inputs.py:132; health_model.py:688-695", "health_model.py:539-577",
    "spraying coverage, deaths", "Share of at-risk population protected by indoor residual spraying", "MAP IRS 'Coverage'",
    "MAP: 'the proportion of household sprayed with IRS annually'; WHO indicator: 'population at risk protected by IRS'",
    "modelled (Africa)", yrs("mal_irs_cov_year"), "2025", "close", "households vs people; max() credits money where MAP shows none (e.g. Nigeria)",
    "current", "money-implied coverage", srcs("mal_irs_cov_source"), "sourced", "Medium", "L-21, L-22")
add("malaria", "trend_malaria_deaths (Pf case trend, +/-5%)", "malaria_inputs.py:42, :73", "health_model.py:860-866", "malaria deaths by year",
    "Expected change in malaria deaths 2026-30 without the cut", "MAP Pf clinical cases 2015-2025, log-linear fit, clipped +/-5%",
    "MAP clinical cases", "modelled + our fit", "2015-2025", "WHO death series MALARIA_EST_DEATHS 2015-2024 (already in ext_data/gho)",
    "close", "Case trend as proxy for deaths; clip unsourced", "current", "0", srcs("trend_malaria_deaths_source"), "derived", "Medium", "L-25")
add("malaria", "uc_itn 2.2, uc_irs 8.5, uc_mal_cm 14", "model_params.csv rows 8-10", "health_model.py:385-417", "malaria people losing, deaths",
    "Cost per person-year of net use / spraying; per case treated", "GiveWell ITN analysis; PMI Mali IRS (Malaria J 2018); White et al. 2011",
    "GiveWell: '<$5 per net'; White 2011: median financial cost per uncomplicated case", "literature", "2009-2024", "", "close",
    "GiveWell net cost is for AMF campaigns; uc_mal_cm 14 (4-47) wide", "partly dated", "", "", "sourced", "Medium", "assumptions.md")
add("malaria", "mal_vc_eff 0.55, mal_cm_eff 0.82", "model_params.csv rows 19-20", "health_model.py:539-577", "malaria deaths",
    "Reduction in malaria deaths at full coverage", "Eisele et al. 2010; Thwing et al. 2011 (Lives Saved Tool)",
    "Eisele: '55% ... against malaria-attributable deaths in children aged 1-59 months'; Thwing: ACT 99% (1-23 m), severe 82%",
    "meta-analysis", "", "LiST current values unchanged", "mismatch (population)", "child effect sizes applied to all-age deaths", "current", "", "", "sourced", "High", "L-04, L-20")
# ---------------------------------------------------------------- immunization
add("immunization", "sh_imm_idpt (DTP3)", "prepare_model.py:125 (WDI SH.IMM.IDPT)", "health_model.py:305-330", "vaccine coverage card, cap",
    "Share of infants fully immunized", "WHO/UNICEF WUENIC via WDI", "'Child immunization, DPT (% of children ages 12-23 months)'", "modelled from admin + surveys",
    yrs("sh_imm_idpt_year"), "2025 (WUENIC released July 2026: global DTP3 85%)", "close", "standard proxy for routine coverage", "one release behind", "", "0", "sourced", "High", "L-17")
add("immunization", "births", "prepare_model.py:412", "health_model.py:305-330", "vaccine need", "Births per year",
    "WDI SP.DYN.CBRT.IN x SP.POP.TOTL (UN WPP 2024)", "'Crude birth rate (per 1,000 people)'", "modelled (UN WPP)", "2024",
    "WPP 2024 (2026 revision UNVERIFIED)", "exact", "", "current", "", "0", "derived", "High", "L-24")
add("immunization", "sh_dyn_mort (U5MR) and trend_u5mr", "prepare_model.py:125, :431 (2010-2019, clip -8%/+2%)", "health_model.py:464, :471",
    "vaccine deaths", "Child mortality level and trend", "UN IGME via WDI SH.DYN.MORT", "'Mortality rate, under-5 (per 1,000 live births)'",
    "modelled", yrs("sh_dyn_mort_year"), "2024 (IGME March 2026)", "exact", "", "current", "U5MR 50 if missing", "0", "sourced", "High")
add("immunization", "imm_deaths_per_child_ref 0.020, imm_u5_share 0.65, U5MR/50 scaling clip 0.3-2.5", "model_params.csv; health_model.py:471",
    "health_model.py:825-835", "vaccine deaths", "Deaths averted per child fully immunized", "Gavi; Li et al. 2021 (VIMC)",
    "Gavi: 20.6M deaths averted / 1.2B children 2000-2024", "derived", "", "VIMC country estimates (Montagu)", "close",
    "Full-schedule deaths per child; scaling by U5MR/50 is ours", "current", "", "", "sourced (scaling: assumption)", "Medium", "L-18, L-19")
add("immunization", "uc_imm 87", "model_params.csv row 11", "health_model.py:385-417", "vaccine people losing", "Full cost per child immunized",
    "Lydon et al. 2014 delivery + vaccine prices", "Lydon: non-vaccine cost per infant US$32.6 (2010 US$)", "literature", "2010-2020",
    "Gavi country financial data FY2021-25 (in datasets/)", "close", "", "dated", "", "", "sourced", "Medium")
# ---------------------------------------------------------------- fiscal
add("fiscal", "ghes_2023, ghes_pc_2023, ghes_pct_gdp_2023", "prepare_model.py:370-380", "health_model.py:269-301", "fiscal panel, capacity",
    "Government health spending", "IHME Health Spending 1995-2023 (Sept 2026)", "IHME 'government health spending' (domestic, excl. DAH)",
    "estimated (WHO GHED + IHME)", "2023", "2023", "exact", "", "current", "", "0", "sourced", "High")
add("fiscal", "ghes_growth_median / p75 / p90", "prepare_model.py:389-395", "health_model.py:269-301", "fiscal capacity, Max replacement",
    "How fast the government could raise health spending", "IHME GHES 2001-2023 yearly real growth", "derived", "derived", "2001-2023", "", "close",
    "Capacity concept is ours (L-29)", "current", "", "0", "derived", "Medium", "L-29")
add("fiscal", "interest_pct_revenue", "fiscal_inputs.py:79, :97-110", "health_model.py:288", "debt stress, capacity",
    "Interest as share of government revenue", "IMF WEO Oct 2026 (GGXONLB - GGXCNL)/GGR; else WDI GC.XPN.INTP.RV.ZS",
    "IMF: overall minus primary balance = net interest (general government); WDI: 'interest payments on government debt' (central government, gross)",
    "official statistics", yrs("interest_pct_revenue_year"), "WEO Oct 2026", "close", "net vs gross; general vs central", "current", "WDI",
    srcs("interest_pct_revenue_source"), "derived", "Medium", "L-34")
add("fiscal", "debt stress thresholds (10%, 40%, floor 0.25)", "health_model.py:288", "fiscal capacity", "Max / custom replacement",
    "How interest burden limits new spending", "our assumption", "", "assumption", "", "", "n/a", "no source found", "n/a", "", "70", "assumption", "Low", "L-29")
add("fiscal", "gc_rev_xgrt_gd_zs, gc_dod_totl_gd_zs", "prepare_model.py:125 (WDI)", "health_model.py:290, :300", "fiscal panel display",
    "Revenue and debt % GDP", "WDI (IMF GFS, central government)", "'Revenue, excluding grants (% of GDP)'; 'Central government debt, total (% of GDP)'",
    "official", yrs("gc_rev_xgrt_gd_zs_year"), "WEO Oct 2026 general government", "close", "central government only; 41/70 have no debt figure", "mixed years",
    "shown as n/a", "rev 18, debt 41", "sourced", "High", "L-31")
add("fiscal", "sh_xpd_ghed_ge_zs (health share of spending)", "health_model.py:1127, :1150", "budget panel, break-even", "Section 4 budget panel",
    "Health share of government spending", "WHO GHED via WDI", "'Domestic general government health expenditure (% of general government expenditure)'",
    "official", "2023", "GHED Dec 2025 (2023)", "exact", "", "current", "", "0", "sourced", "High")
add("fiscal", "backfill regression theta (regressions.json)", "prepare_model.py:526", "Validation, Methods", "Validation page; custom theta default",
    "How much governments replace when aid falls", "own panel regression, 97 countries 2001-2023, n=2,134", "theta = -(b_fall + b_fall_l1) = -0.19 (95% CI -0.45 to 0.07)",
    "own estimate", "2001-2023", "", "close", "Lu et al. 2010 studies rises; falls thin", "current", "", "", "derived", "Medium")
# ---------------------------------------------------------------- scenarios
add("scenario", "US_MULTI_EXITS (WHO, Gavi, UNFPA 1.0; Global Fund 0.23)", "scenarios.py:17", "health_model.py:181-197", "Full US Exit, MOUs, Combined",
    "US cut via multilaterals", "US pledges", "US Global Fund 8th replenishment pledge US$4.6B vs US$6.0B", "policy", "2025", "", "exact", "", "current", "", "", "sourced", "High")
add("scenario", "OECD_2025", "scenarios.py:19", "health_model.py:181-197", "OECD preset", "Health aid change 2025 by donor",
    "OECD preliminary 2025 ODA (April 2026)", "US -56.9%, DE -17.4%, FR -10.9%, UK -10.8%, JP -5.6% (total ODA)", "official", "2025", "", "mismatch",
    "total ODA, not health ODA; IHME health: UK -39%, FR -33%, DE -12%", "current", "", "", "sourced", "High", "L-28")
add("scenario", "GAVI_CUT_DEFAULT 15%", "scenarios.py:48", "Global Fund & Gavi preset", "preset", "Fall in Gavi spending 2026-30",
    "our estimate", "Gavi 6.0: 'only US$6 billion of the funding secured comprises new pledges' (Donor Tracker)", "assumption", "", "", "n/a", "no disbursement forecast published", "n/a", "", "", "assumption", "Low", "L-09")
add("scenario", "GF_CUT_DEFAULT 20%", "scenarios.py:49", "Global Fund & Gavi preset", "preset", "Fall in Global Fund money",
    "Global Fund 8th replenishment US$12.64B vs 7th US$15.7B", "-19.5%", "official", "2025", "", "close", "pledges, not country allocations", "current", "", "", "sourced", "High")
add("scenario", "MOU schedules (mou_signed.csv, mou_us_ref)", "prepare_model.py (KFF + team sheet); scenarios.py:73-110", "health_model.py:200-216",
    "America First MOUs", "US bilateral health money by year 2026-2030", "KFF MOU tracker (Oct 2026) + team MOU sheet",
    "KFF: 'Partner countries commit to raising domestic health spending while U.S. assistance falls'", "policy documents", "2026-2030",
    "", "close", "co-financing commitments ignored; increases = 0; after 2028 flat", "current", "", "", "sourced", "Medium", "L-08, L-35")
# ---------------------------------------------------------------- parameters (rest)
for p, need, ev, status, conf, fid in [
    ("asd_share", "Above-site share of donor program cost", "KFF 2025: 'non-service delivery accounted for 47%'; 45% citation UNVERIFIED", "sourced", "Medium", "L-26"),
    ("uc_art_mult", "uncertainty on ART cost", "range judgment", "sourced", "Low", "assumptions.md"),
    ("uc_scale_elast", "staff cost elasticity to GDP pc", "assumption", "assumption", "Low", "assumptions.md"),
    ("uc_pmtct", "PMTCT cost per woman incl. ART", "HPP 2016 review figures UNVERIFIED", "sourced", "Low", "L-32"),
    ("cpia_ref", "cost per infection averted", "assumption", "assumption", "Low", "assumptions.md"),
    ("uc_ovc", "OVC cost (no effect)", "assumption", "assumption", "Low", "no issue (no effect on deaths, sensitivity 0)"),
    ("art_hazard_mult", "ART interruption mortality", "calibration inconsistent", "sourced", "High", "L-01"),
    ("art_transmission", "infections per person-year off ART", "~2.2/100 PY untreated couples", "sourced", "Medium", "assumptions.md"),
    ("pmtct_vt_reduction", "transmission averted by PMTCT", "WHO 15-45% vs <5%", "sourced", "High", "assumptions.md"),
    ("pmtct_infant_mort", "death of infected infants", "Newell 2004 35.2%/52.5%", "sourced", "High", "assumptions.md"),
    ("tb_cfr_untreated_neg", "TB CFR untreated HIV-", "Glaziou Table 4 0.43", "sourced", "High", "no issue"),
    ("tb_cfr_treated_neg", "TB CFR treated HIV-", "Table 4 0.03", "sourced", "High", "no issue"),
    ("tb_cfr_untreated_pos", "TB CFR untreated HIV+", "Table 5 0.78/0.62/0.49", "sourced", "High", "L-13"),
    ("tb_cfr_treated_pos", "TB CFR treated HIV+", "Table 5 0.09/0.06/0.04", "sourced", "High", "L-13"),
    ("tb_dr_dcfr", "DR-TB deaths averted per patient", "assumption", "assumption", "Low", "assumptions.md"),
    ("mal_itn_default_use", "ITN default", "assumption", "assumption", "Low", "L-07"),
    ("mal_cm_default_cov", "treatment default", "assumption", "assumption", "Low", "no issue (9 countries, sensitivity 0)"),
    ("hss_kappa", "systems money -> services", "assumption", "assumption", "Low", "L-05"),
    ("continuity", "patients keeping service", "assumption", "assumption", "Low", "L-14"),
    ("tb_secondary", "secondary TB cases", "derived (Styblo)", "sourced", "Medium", "assumptions.md"),
    ("mal_resurgence", "malaria rebound", "assumption (Cohen 2012 direction)", "assumption", "Low", "assumptions.md"),
    ("hiv_inf_death_untreated", "death after infection, untreated", "Todd 2007", "sourced", "High", "no issue"),
    ("hiv_inf_death_treated", "death after infection, treated", "assumption", "assumption", "Low", "assumptions.md"),
    ("hiv_survival_median", "median survival", "Todd 2007 10.5 years", "sourced", "High", "no issue"),
    ("art_reengage", "return to care after 2030", "assumption", "assumption", "Low", "assumptions.md"),
]:
    add("parameter", p, "model_params.csv", "health_model.py (draw_params :127-148)", "deaths (see sensitivity.csv)", need, "model_params.csv source column",
        ev, "literature / assumption", "", "", "see assumptions.md", "", "see assumptions.md", "", "", status, conf, fid)
# ---------------------------------------------------------------- constants
for name, where, used, val, ev, fid in [
    ("LAG ramps", "health_model.py:74-80", "health_model.py:821-866", "PMTCT 0.6, TB 0.7, ITN 0.5, IRS 0.8 in year 1", "assumption; sensitivity <2%", "assumptions.md"),
    ("ART_HAZARD shape", "health_model.py:81", "health_model.py:856-858", "1.2/2.8/3.8/4.5/5.0%", "shape has 0 effect for a sudden cut", "L-01"),
    ("ART_INFECT_LAG", "health_model.py:82", "health_model.py:868-896", "0.5 in year 1", "assumption", "assumptions.md"),
    ("POST_YEARS = 5", "health_model.py:83", "further deaths", "2031-2035", "framing", "no issue (labelled)"),
    ("HIV_WEIBULL_SHAPE 2.25", "health_model.py:84", "HIV infection deaths", "Todd 2007", "sourced", "no issue"),
    ("TB ART adjustment 0.3", "health_model.py:461-462, :840-841", "TB HIV+ CFR", "(1 - 0.3 a)", "approximation of WHO Table 5", "L-13"),
    ("U5MR reference 50, clip 0.3-2.5", "health_model.py:471", "vaccine deaths", "", "assumption", "L-19"),
    ("tb_hiv_share clip 0.8", "prepare_model.py:418", "TB CFR", "", "never binds (max share < 0.8)", "no issue"),
    ("malaria_at_risk_share 0.95 / 0.35", "prepare_model.py:424", "16 countries", "", "assumption", "assumptions.md"),
    ("malaria u5 share 0.76 / 0.40 (fallback D0)", "prepare_model.py:422", "7 countries", "", "WMR 2025: 75% in African Region", "no issue"),
    ("1.15 female prevalence factor", "prepare_model.py:417", "10 countries", "", "assumption", "assumptions.md"),
    ("MAL_CM_MIN_INCIDENCE 50", "malaria_inputs.py:44", "survey fallback", "", "assumption", "no issue"),
    ("ITN_SURVEY_MIN_YEAR 2015", "malaria_inputs.py:43", "survey fallback", "", "assumption", "L-07"),
    ("malaria trend clip +/-5%", "malaria_inputs.py:42", "malaria deaths", "", "assumption; sensitivity -0.8%/+0.1%", "L-25"),
    ("U5MR trend window 2010-2019, clip -8%/+2%", "prepare_model.py:145-146", "vaccine deaths", "", "assumption; sensitivity small", "assumptions.md"),
    ("FALLBACK_MORTALITY_TREND -0.009", "health_model.py:422", "countries without a trend", "", "Cavalcanti 2025 appendix", "no issue"),
    ("trend_tb_deaths (unused)", "health_model.py:423", "none at runtime", "", "listed but never applied", "L-10"),
    ("AID_BASE_YEARS 2021-2023", "health_model.py:420; prepare_model.py:40", "baseline", "", "", "L-06"),
    ("N_YEARS = 5 (2026-2030 horizon)", "health_model.py:72", "all", "", "framing", "assumptions.md"),
    ("PEPFAR_ON_ART 20.6M", "health_model.py:1096", "Validation", "", "KFF fact sheet FY2024", "no issue"),
    ("ABUJA_CEILING 15%", "health_model.py:1126", "budget panel", "", "Abuja Declaration 2001", "no issue"),
    ("LANCET_FUNDING, LANCET_RR", "health_model.py:1329-1332", "Validation Lancet comparison", "", "Cavalcanti 2025", "benchmarks.md"),
    ("S_CURVE_STEEPNESS 1.5; path shapes", "scenarios.py:219-243", "funding paths", "", "illustrative", "no issue"),
    ("ALL_COUNTRY_DRAWS 400, seed 7", "scenarios.py:55", "ranges", "", "", "uncertainty_scope.md"),
]:
    add("constant", name, where, used, "see used_at", val, "hard-coded", ev, "assumption / literature", "", "", "n/a", "", "n/a", "", "", "hard-coded", "Medium", fid)
# ---------------------------------------------------------------- descriptive sections
for name, src, defin, yrs_, latest, fid in [
    ("Section 1: spending_data/ (IHME health spending by source)", "IHME Global Health Spending 1995-2023", "government, prepaid private, out-of-pocket, DAH; constant 2023 US$", "1995-2023", "Sept 2026 release", "no issue"),
    ("Section 2: country_data/ (DAH by funder, channel, area)", "IHME DAH 1990-2026", "elim_ch == 0", "1990-2026", "Sept 2026", "no issue"),
    ("Section 3: revenue_data/, cofog_all/, macro_data/", "IMF WoRLD; IMF COFOG; IMF WEO", "levels of government shown; WEO GG totals", "various", "WEO Oct 2026", "L-31"),
    ("population for per-person figures (macro_data)", "IMF WEO", "population", "", "vintage tag missing", "L-31"),
]:
    add("descriptive", name, "earlier scripts (not in repo)", "views/1_Dashboard.py", "Sections 1-3", "", src, defin, "official / IHME estimates", yrs_, latest,
        "exact", "", "current", "", "", "sourced", "Medium", fid)

with open(Path(__file__).parent / "inputs.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=F)
    w.writeheader()
    w.writerows(R)
print(len(R), "inputs")
