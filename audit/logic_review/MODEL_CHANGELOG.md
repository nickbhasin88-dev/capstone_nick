# Model changelog: every parameter, input and rule changed in the logic-review batches

Scope: Batch 1 (the "Do now" items, commits `cff29af`..`91d48fa`), the malaria under-5 share (`c0d7587`), Batch 2
(`c625037`, `49767e9`, `cd42746`), Batch 3+4 (`18b6a24`..`c1b0846`), Batch 4b (`6b652b1`..`d62a15d`) and Batch 5+6
(`a0c2082`..this branch, `tomato`). Values are central (low-high). "Labelled assumption" means no source measures the
quantity and the value carries a stated range. Full evidence: `batch2_evidence.md`, `batch34_evidence.md`,
`batch4b_evidence.md`, `batch56_evidence.md`; the specification is `docs/SPEC.md`.

Headline (all countries, Full US Exit, central, deaths 2026-2030) at each boundary, each re-run at its own commit
with its own inputs (Batch 7 item 2): before Batch 1 1,969,304 -> after Batch 1 1,945,605 -> after the malaria
under-5 share 1,965,386 -> after Batch 2 2,055,422 (HIV 1,006,114 -> 1,096,151) -> after Batch 3+4 1,379,963 ->
after Batch 4b 1,695,601 -> after Batch 5+6 1,927,405.

## Batch 1: "Do now" items (14 October 2026)

| Change | Old | New | Source | Commit |
|---|---|---|---|---|
| `mal_cm_eff` (case-management effect on malaria deaths) | 0.82 (0.60-0.99), severe-malaria effect | 0.97 (0.82-0.99) | Thwing, Eisele & Steketee 2011, BMC Public Health 11(S3):S14, abstract: ACT for uncomplicated malaria 97% (86-99%) at 24-59 months; low end 82% severe malaria | `c6dd075` |
| Malaria effect sizes by age (new rule) | LiST child effects applied to all-age deaths | applied in full to under-5 deaths, x `mal_adult_effect_frac` at 5+ | L-04; Eisele et al. 2010 and Thwing et al. 2011 are 1-59-month effects | `c6dd075` |
| `mal_adult_effect_frac` (new) | - | 0.5 (0-1) | labelled assumption (no published adult effect) | `c6dd075` |
| Malaria death trend (`trend_malaria_deaths` input) | P. falciparum case trend, clipped ±5% | WHO estimated malaria deaths 2015-2024, log-linear fit, clipped ±5% (clip = labelled assumption) | WHO GHO MALARIA_EST_DEATHS (World Malaria Report); L-25 | `719ff89` |
| TB counterfactual trend | `trend_tb_deaths` defined, unused | removed: TB deaths are per patient | L-10 | `911fbfe` |
| TB detection rate | could exceed 100% | capped at 100% and flagged | L-12 (WDI definition) | `911fbfe` |
| `tb_cfr_untreated_pos` | 0.62 (0.45-0.78) | 0.78 (0.65-0.94), off ART | WHO TB burden estimation methods (Glaziou et al.), Table 5, p. 28 | `911fbfe` |
| `tb_cfr_untreated_pos_art` (new) | - | 0.49 (0.31-0.70); blended 0.78 (1 - a) + 0.49 a by ART coverage a | WHO Table 5, p. 28 | `911fbfe` |
| `asd_share` citation | "PEPFAR 2014" (not found) | 0.45 (0.30-0.55) unchanged; cited to KFF 2025 (non-service delivery 47% of PEPFAR spending 2018-23) | Gaba, Razavi, Kates & Nandakumar, KFF, Sept 2025 | `ba496d1` |
| All Countries range | sum of country percentiles | percentile of the summed draws | L-02 / IMP-10 | `581c013` |
| Labels only: presets renamed, triage labelled hypothetical, further deaths labelled assumption-driven with the `art_reengage` range, claims reworded, treatment/prevention split | | | IMP-14, L-30, L-33, IMP-21, L-40 | `752f611`, `8b89420`, `f8566e4`, `576a8d8`, `c56214a` |
| One specification | `audit/METHOD.md` and `logic.md` | `docs/SPEC.md`, reproduced independently (1,860 of 1,860 cells within 0.5%) | IMP-20 | `cff29af` |

## Malaria under-5 share (14 October 2026)

| Change | Old | New | Source | Commit |
|---|---|---|---|---|
| Under-5 share of malaria deaths (rule) | WHO/MCEE child malaria deaths 2021 / WHO all-age deaths 2024, clipped 0-1 (0.76 SSA / 0.40 elsewhere if missing) | the World Malaria Report 2025 share for the country's WHO region | WMR 2025 sections 2.3-2.8 | `c0d7587` |
| `mal_u5_share_afr`, `_amr`, `_emr`, `_sea`, `_wpr` (new) | - | 0.75 (0.70-0.80), 0.20 (0.15-0.25), 0.364 (0.314-0.414), 0.25 (0.20-0.30), 0.40 (0.35-0.45) | WMR 2025 p. 20 ("just over 75%"), p. 24 ("less than 25%"; central and range an assumption within the bound), p. 28 (36.4%), pp. 31-32 ("just under a quarter"), p. 35 (40.0%); ±5-point ranges are assumptions around the WHO figure | `c0d7587` |
| `mal_u5_use_country_series` (new switch) | - | 0 (constant): 1 restores the old rule | sensitivity | `c0d7587` |

## Batch 2: ART death risk and HIV transmission (14 October 2026)

| Change | Old | New | Source | Commit |
|---|---|---|---|---|
| `ART_HAZARD` (excess deaths per person-year off ART, years 1-5, then 6-10 after 2030) | 1.2, 2.8, 3.8, 4.5, 5.0% (year-5 value after 2030); calibrated to PEPFAR totals | 1.3, 2.5, 3.7, 4.9, 6.0%; 6.8, 7.2, 7.3, 7.1, 6.7% | CD4-stage cohort calculation (`audit/batch2_cohort.py`): ZIMPHIA 2020 Table 10.1 (p. 89) starting CD4; Optima HIV appendix Tables A1-A2 (pp. 2-3) progression and death rates; 23% relative death rate on suppressive ART | `49767e9` |
| `art_hazard_mult` range | 1 (0.60-1.50) | 1 (0.65-1.70) | women + Optima low rates (12.0%) to men + Optima high rates (31.7%) over 5 years | `49767e9` |
| HIV transmission from people off ART | `art_transmission` 0.04 (0.02-0.08) for every country | country rate `art_transmission_rate` = UNAIDS 2025 new infections / (PLHIV - suppressed) (median 0.12; WHO-region median for 14 countries) x `art_transmission_mult` 1 (0.71-1.38) | UNAIDS AIDSinfo 2026 estimates; range = ratio of UNAIDS bounds to the estimate | `49767e9` |
| `hiv_new_inf_unsup_years` (new; second generation of infections) | none | 4 (2.5-5.5) years | labelled assumption from Giguère et al. 2021 Lancet HIV 8:e284 (2.6-year median time to diagnosis) + Optima Table A2 (0.2 years to suppression) | `49767e9` |
| `art_reengage` | 0.5 (0.25-0.75), assumption | 0.35 (0.17-0.68) | Kranzer et al. 2010 JAIDS 55:e17 (0.17/yr); Kaplan et al. 2017 PLoS Med (about 0.3/yr); Mody et al. 2026 PLoS Med 23:e1005052 (0.68) | `49767e9` |
| `hiv_legacy_art_params` (new switch) | - | 0 (constant): 1 restores the pre-Batch-2 ART values | sensitivity | `49767e9` |

## Batch 3+4: money-to-people conversion, unit costs, cap rule, TB costs, continuity (14 October 2026)

| Change | Old | New | Source | Commit |
|---|---|---|---|---|
| Systems money (HSS) | kappa (0.5) of it converted to service units | `hss_service_share` 0 (constant): not converted (above-site money already in the 1.818 markup); `hss_kappa` applies to testing-and-care money only | L-05; labelled assumption (option ii) | `4f9f0c0` |
| Unspecified money split (new inputs `unspec_<hiv|tb|malaria>_<treatment|prevention|testing|rssh|pm>`) | spread over known lines by mix (45% HIV, 77% TB, 40% malaria to treatment) | the country's Global Fund GC7 module shares (medians: HIV 35/23/6/11/22%; TB 49/1/21/10/17%; malaria 22/48/0/14/15%); WHO-region median for 38 of 210 lines | Global Fund Data Explorer grant budgets by module, GC7 (`audit/batch34_gf_shares.py`) | `2a792f7` |
| IMP-02c (testing-and-care money as a flow of initiations) | kappa proxy | BLOCKED: no cost per initiation; kappa proxy kept and labelled | `batch34_evidence.md` C | `85440df` |
| ART site cost per patient-year (new input `art_site_cost`) | Rosen 2021 for 5 countries; elsewhere ARVs US$95 + non-ARV US$23 x income scaling (2018 US$) | GHCC UCSR records (per person-year, provider, no above-service costs, price year 2015+, economic x 0.981 financial/economic ratio from Value TB) pooled with Rosen 2021: own value for 7 countries (Kenya 354, Uganda 371, Malawi 151, Eswatini 255, Zimbabwe 220, Lesotho 148, Zambia 141); AFR median 220 elsewhere; 2023 US$ | GHCC Unit Cost Study Repository (2020 US$); Rosen et al. 2021 Gates Open Research 5:177 | `810df94` |
| `uc_art_mult` range | 1 (0.75-1.30) | 1 (0.68-1.38) | spread of the country cost studies | `810df94` |
| TB course costs (new inputs `tb_ds_cost`, `tb_dr_cost`) | Laurence et al. 2015 income-group means: DS 332 / 351 / 1,081; DR 1,568 / 8,125 / 6,800 (2014 US$ x 1.287) | Value TB facility costs (Sweeney et al., 2018 US$, financial bottom-up): DS Ethiopia 218, India 105, Kenya 150, Philippines 120; DR Kenya 2,818, Philippines 1,580; GHCC South Africa DS 274, DR 9,256 (Vassall 2017; Cox 2015); income-group medians pooled with Laurence 2015 elsewhere: DS 275 / 135 / 678, DR 1,568 / 2,818 / 8,028 | Value TB dataset; GHCC UCSR TB | `e6fa30f` |
| `uc_tb_mult` range | 1 (0.60-1.60) | 1 (0.78-1.60) | median country range | `e6fa30f` |
| DR-TB share and enrolment (new inputs `tb_rr_share`, `tb_rr_cov`) | 4% and 45% globally | WHO 2024 country RR-TB incidence / incidence (median 2.1%) and RR patients started / RR incidence (median 35%) | WHO Global TB Programme | `e6fa30f` |
| Donor-funded pool (cap rule; new inputs `donor_share_<hiv|tb|malaria|imm>`) | everyone covered | people covered x the external share of spending on the disease (GHED all-source; WHO TB financing for TB; regional median where missing) | IMP-04 / L-44; labelled: a spending share is the closest external measure | `f7fbb88` |
| `continuity` | 0.15 (0-0.35), assumption | 0.15 (0-0.30), assumption kept by rule; 0.30 recorded as a sensitivity value | KFF April 2026; Cust & Chabata 2026 Lancet Global Health; WHO Global TB Report 2025 (none measures the quantity) | `f424606` |
| Secondary TB deaths attribution | all on `tb_ds` | to the line whose lost patients generated them | first full check | `225e532` |

## Batch 4b: ART unit cost consistency, malaria cap share (14 October 2026)

| Change | Old | New | Source | Commit |
|---|---|---|---|---|
| ART cost per patient-year used (new input `art_cost_full`) | site cost x 1.818 (US$400 in 60 countries; Kenya 644, Uganda 675; gate applied to the site value) | the lower of (a) site cost x 1.818 and (b) observed treatment spending per person on ART = total HIV spending x Global Fund treatment share / UNAIDS people on ART; (a) x regional median (b)/(a) where (b) missing; floor US$57 (TLD US$45 + viral load US$12.08); gate 50-600 on the final value; median US$274 | ten Brink et al. 2025 appendix Table B2 (p. 8); WHO GHED dis11_usd; Global Fund module shares; UNAIDS 2026; Global Fund news release 30 Aug 2023; CHAI 2015 | `d30ecab` |
| Donor share for bednets and spraying (new input `donor_share_malaria_prev`) | external share of all-source malaria spending (Nigeria 0.03) | external share of public malaria spending, GHED dis13_ext / (dis13_ext + dis13_gghed) (Nigeria 0.22; median 0.56) | WHO GHED; concept: household treatment spending is not the donor-funded service | `7342148` |

## Batch 5+6: ART floor and validity, input shares, malaria cap concept, vaccines, validation (14 October 2026)

| Change | Old | New | Source | Commit |
|---|---|---|---|---|
| Validity of observed ART spending (b) | used wherever available (43 countries) | used only where the Global Fund funds >= 10% of total HIV spending (35 countries; invalid: South Africa, Nigeria, Namibia, Dominican Republic, Botswana, Guyana, Philippines, São Tomé and Príncipe); otherwise (a) x regional median (b)/(a) over valid countries (AFR 0.52, EUR 0.92, overall 0.54) | Global Fund Data Explorer disbursements (HIV, TB/HIV); Table B2 / GHED totals | `a0c2082` |
| ART cost floor | US$57 (TLD + one viral load test; commodity price) | US$190.84 = lowest measured site delivery cost (Malawi US$86.50, 2018 US$, Rosen et al. 2021) inflated (104.96) x 1.818 above-site markup; 13 countries at the floor | Rosen et al. 2021 Gates Open Research 5:177; KFF 2025 (markup) | `a0c2082` |
| ART cost gate | 50-600 on the final value (unchanged) | same; median cost 274 -> 216 (South Africa 57 -> 208, Nigeria 400 -> 208, Zimbabwe 129 -> 191) | | `a0c2082` |
| HIV and immunization donor shares (`donor_share_hiv`, `donor_share_imm`) | external share of all-source spending (GHED dis11, hc62) | external share of public spending, ext / (ext + domestic government) (Nigeria HIV 0.18 -> 0.55; immunization 0.40 -> 0.63) | WHO GHED; L-51; concept as Batch 4b item 3 | `b30f4b8` |
| Malaria donor shares (new inputs `donor_share_mal_itn`, `_mal_irs`, `_mal_cm`) | external share of public malaria spending (nets, spraying); all-source share (treatment) | the intervention's own share: donor money for the line / (people covered x unit cost), capped at 1 (medians: nets 0.53, spraying 1.0, treatment 0.39) | IHME programme areas after the Batch 3+4 split; MAP 2025 coverage; model unit costs; WMR 2025 ch. 4 and 8 as direction cross-check | `7f07d6b` |
| Net unit cost `uc_itn` | 2.2 (1.4-3.5) per person-year of use | unchanged; formula stated: US$5 per net / (1.8 people x 2 years) / 0.63 in use; 3-year life gives 1.47, inside the range | GiveWell ITN analysis; WMR 2025 p. 20 (net lifespan) | `7f07d6b` |
| Vaccine deaths per child (new inputs `imm_dpc`, `_lo`, `_hi`, `imm_dpc_lag0-9`, `imm_dpc_beyond_window`, `imm_q5_ratio`, `imm_antigens`) | `imm_deaths_per_child_ref` 0.020 (0.017-0.024) x `imm_u5_share` 0.65 (0.50-0.75) x clip(U5MR / 50, 0.3, 2.5) | sum over the routine antigens the country uses (WUENIC 2025 coverage > 0) of VIMC deaths averted per vaccinated child (2015-19 mean; minimum year for measles, MenA, YF) x WPP Q5 2026-30 / 2015-19 (adjustment); median 0.025 lifetime (Kenya 0.021, Nigeria 0.059, India 0.012); regional medians for 38 of 620 gate outliers and the 4 non-VIMC countries | Toor et al. 2021 eLife 10:e67635 (VIMC data; Table 3 gate); WUENIC 2025; WPP 2024 | `7464034` |
| Vaccine timing | cohort weights 0.40 / 0.35 / 0.20 / 0.05 by years since missed, x U5MR trend | per-pathogen distribution by years since vaccination (NNLS fit to VIMC calendar-year vs birth-cohort deaths; measles 77% / 23%, Hib 59 / 23 / 9 / 4 / 6%, ...), under-5 share by pathogen; lags 5-9 counted where identified (measles, HepB); remainder beyond 2035 not counted | VIMC cross-section and cohort files | `7464034` |
| `imm_dpc_mult` (new) | - | 1 (0.56-1.64), mapped onto each country's VIMC low / high | VIMC 95% credible intervals | `7464034` |
| `imm_legacy_u5mr_scaling` (new switch) | - | 0 (constant): 1 restores the old vaccine rule; `imm_deaths_per_child_ref` and `imm_u5_share` relabelled legacy | sensitivity | `7464034` |
| Vaccine scope statement | none | dashboard, Methods and Validation state that DTP, polio and BCG are excluded (no citable per-child value; Shattock et al. 2024 give totals only), HPV excluded (adolescent), JE unmapped: a conservative floor | | `7464034` |
| Validation | Validation page framed to pass; Gavi row circular | `validation.md` with a stated 0.5-2x band, country-level Optima, UNAIDS, WHO TB, WMR and Toor comparisons, explained flags; Methods section | IMP-19 / L-47 | `a4cd2c2` |

## Batch 7: closing the small open items (15 October 2026)

Evidence: `batch7_evidence.md`. Headline before the batch 1,927,405.

| Change | Old | New | Source | Commit |
|---|---|---|---|---|
| L-43 status reconciled (item 1) | listed open in the findings table; done in the changelog | done, with stated gap: 34 of 210 country-disease lines use a WHO-region median for the split of unspecified money; the capped lines are listed in `batch7_evidence.md` | no model change | `f772662` |
| Headline chain corrected (item 2) | 2,017,000 (rounded) -> 2,055,422 -> 2,055,422 -> ... | 1,969,304 -> 1,945,605 -> 1,965,386 -> 2,055,422 -> 1,379,963 -> 1,695,601 -> 1,927,405, each re-run at its own commit | `batch7_evidence.md` item 2 | `5742b44` |

| L-17 DTP3 coverage (item 3) | World Bank WDI mirror of WUENIC, 2024 (2023 for Nicaragua) | WHO/UNICEF WUENIC 2025 revision read directly, 2025 for all 70 countries (`immunization_inputs.py`, also MCV1); 30 countries differ by more than 2 points (Angola -12, Venezuela -12, Tajikistan -11, Honduras +11, South Africa -9, Ethiopia +8, Namibia +8) | `datasets/WUENIC_2025.xlsx` | `ccb0dcd` |
| IMP-24 HIV and immunization inputs from the source files (item 4) | HIV inputs via the WHO GHO API and the WDI mirror (new infections 2024); DTP3 and MCV1 via the WDI mirror, including the regression panel's DTP3 history | `unaids_inputs.py`: PLHIV (66 of 71 countries), ART coverage (66), PMTCT coverage (69), HIV-positive pregnancies (69), new infections (64; UNAIDS 2025 vs WDI 2024, median ratio 0.94), AIDS deaths (65, new column) from the UNAIDS 2026 file, GHO or derived values as fallbacks; `immunization_inputs.wuenic_series` feeds the DTP3 regression history; `sh_imm_*` removed from the WDI download list. Still from the mirror: adult HIV prevalence (`sh_dyn_aids_zs`, a fallback and regression input) and the committed `regressions.json`, which is rebuilt only by a full `prepare_model.py` run | `datasets/UNAIDS_2026/UNAIDS_Estimates_2026.csv`; `datasets/WUENIC_2025.xlsx` | `67219a4` |
| L-11 Lancet rate-ratio baseline HIV deaths (item 5) | `hiv_deaths_est` = IHME GBD-2019 HIV share of deaths (Gapminder) x crude death rate x population (Kenya 70,569 a year; Honduras 86) | UNAIDS AIDSinfo 2026 AIDS-related deaths, 2025 (`hiv_deaths_unaids`; Kenya 19,434; Honduras 304); the old value stays as the fallback for the 6 countries UNAIDS does not cover (Côte d'Ivoire, Guatemala, Iraq, Jamaica, Jordan, Nicaragua) | UNAIDS 2026 file | `0ed6139` |
| L-31 WEO vintage (item 6) | untagged | interest series labelled "IMF WEO October 2026" (file downloaded 13 October 2026) in the inputs, the fiscal panel, SPEC and Methods; the `macro_data` GDP, revenue and expenditure series labelled "vintage not recorded; projection horizon 2031, consistent with the October 2026 release" | `fiscal_inputs.py` SOURCE; `datasets/IMF_WEO_Oct2026_GG_balances_2026-10-13.csv` | `22638b5` |
| L-34 interest definition (item 7) | the more recent of IMF WEO net interest (53 countries) and World Bank gross interest payments (17), ties to the World Bank | IMF WEO net interest for every country (70 of 70 have a value; 18 have no World Bank value at all); the World Bank series stays as a flagged fallback (`flag_interest_alt_def`, currently no country). 17 countries change value: Ethiopia 12.6 -> 7.8, Mozambique 15.1 -> 13.3, Uganda 21.0 -> 22.4, Tanzania 13.9 -> 14.2, Angola 25.2 -> 25.6, Kyrgyzstan 2.6 -> 3.4, Botswana 3.4 -> 4.7, Mauritius 10.4 -> 11.7, El Salvador 14.3 -> 17.1, Guatemala 12.5 -> 13.0, Fiji 13.9 -> 14.6, Lesotho 3.5 -> 2.0, Madagascar 4.8 -> 4.6, Somalia 0.6 -> 0.6, Tajikistan 2.9 -> 2.8, Togo 14.0 -> 14.0, Central African Republic 4.2 -> 1.9; fiscal capacity changes in those countries only (no headline effect: the default is no replacement) | `fiscal_inputs.py`; `batch7_evidence.md` item 7 | `b033d2a` |
| `mou_deflate` (new switch, item 8) | MOU amounts nominal, compared with a nominal 2021-25 reference | 0 (constant): default unchanged and labelled nominal on the dashboard; 1 divides each year's amount by (1 + `mou_us_inflation`)^(year - 2023) | L-35 | `a90c809` |
| `mou_us_inflation` (new, item 8) | - | 0.02 (0.01-0.04) a year, used only when `mou_deflate` = 1 | labelled assumption: no US inflation projection on disk (the WEO file holds the model countries' balances only; their US$ GDP deflators are the wrong concept for US-dollar budget amounts) | `a90c809` |
| Debt-stress thresholds (item 9) | 10% / 40% / floor 0.25, hard-coded, unsourced | the same values as named constants, labelled assumptions with ranges 5-15% / 30-50 points / 0.15-0.50 (not drawn); cumulative capacity noted as a known alternative, not implemented | no source found in the evidence files (`logic.md`, `redteam_report.md` and `coverage.md` all record the thresholds as class (c) assumptions) | `2f49445` |
| `budget_growth` (new constant, item 10) and `gdp_growth_weo_2026_30` (new input) | Gradual Budget Increase money = points x the 2023 government budget, held flat | x (1 + budget_growth x g)^(t + 1), g = the country's mean nominal US$ GDP growth 2026-2030 from the WEO projections in `macro_data/` (69 of 70 countries; median 0.075, Kenya 0.061); default 0 keeps the current behaviour; at 1 the all-country gradual preset (Steady 0.5 points) gives 419,439 deaths instead of 534,944 (-22%) and Kenya's break-even rise 1.06 instead of 1.12 points a year | IMF WEO projections on disk; labelled sensitivity, not drawn | `267249e` |
| L-09 Gavi -15% default (item 11) | value "our estimate" on the Methods page and the slider marks | value unchanged; the preset description and the Methods text now both say it is our estimate and applies to this preset only | no change | `3f98d1d` |
| L-24 births (item 12) | immunization need = latest-year births (crude birth rate x population) held through 2030 | need in year t = WPP 2024 projected births for 2026 + t (`births_2026` .. `births_2030`, all 70 countries; median +1.7% over the period); displayed need = the five-year mean; PLHIV and TB and malaria incidence still held at the latest year (no projection on disk); PMTCT uses UNAIDS pregnancies, not births (births enter only Iraq's and Jordan's derived fallback) | `datasets/WPP2024/WPP2024_Demographic_Indicators_Medium.csv` | `67163c8` |
| L-15 TB timing (item 13) | case fatality in the year of loss; secondary cases at 1 and 2 years, undocumented | Methods note: both are labelled assumptions about timing (WHO methods: untreated TB lasts about three years; Vynnycky and Fine 1997: most progression within two to five years); no rule change | WHO TB burden estimation methods; Vynnycky & Fine 1997 (already cited for `tb_secondary`) | `72e562d` |
| Malaria input flags (item 14) | caveats L-07, L-21, L-22, L-23 recorded in text only | four boolean columns in `country_inputs.csv` and in the All Countries files: `flag_itn_default` (31 countries), `flag_irs_household` (36), `flag_irs_implied` (56), `flag_map_who_gap` (26); no rule change | `audit/batch7_flags.py`; `batch7_evidence.md` item 14 | `f1f1ca7` |
### Closed in Batch 7
- L-07, L-21, L-22, L-23 (malaria input caveats): flagged per country (no rule change); affected countries listed in `batch7_evidence.md` item 14.
- L-15 (TB timing): closed as a label; no rule change.
- L-24 (births half): closed; headline 1,927,847 -> 1,928,289 (+0.02%), vaccine deaths 188,412 -> 188,853. PLHIV and incidence remain held at the latest year.
- L-09 (Gavi -15% is an estimate): closed as a label; value unchanged.
- Gradual-increase budget growth: the sensitivity exists (`budget_growth`, default 0, no change to the preset default).
- L-29 (labelling half): closed; thresholds labelled with ranges, the non-cumulative capacity rule unchanged and the alternative noted.
- L-35 (nominal MOU amounts): closed with the `mou_deflate` switch (default nominal, labelled); deflated at 2% the MOU preset gives 416,307 deaths instead of 364,586 (+14%) over the 16 MOU countries.
- L-34 (mixed interest definitions): closed; one primary definition with a visible flag for the fallback. 13 Mozambique baseline entries with a government response refreshed.
- L-31 (untagged WEO vintage): closed as a label (October 2026 for interest; vintage not recorded for the macro_data series).
- L-11 (GBD-2019 HIV share on the Validation page): closed; the Lancet rate-ratio row uses UNAIDS 2025 AIDS deaths (Kenya's Lancet HIV estimate 221,301 -> 60,943 over five years). Validation page only; headline unchanged.
- IMP-24 (direct WUENIC and UNAIDS inputs): closed for the model inputs; the regression panel's prevalence series and the committed regressions.json still rest on the mirror (listed). Headline 1,927,871 -> 1,927,847 (-0.001%).
- L-17 (DTP3 via the WDI mirror): closed; the model reads WUENIC 2025 directly. Headline 1,927,405 -> 1,927,871 (+0.02%); vaccine deaths 187,945 -> 188,412.

- L-43 (unspecified money): done with stated gap, 34 of 210 lines on regional medians; capped cases listed in `batch7_evidence.md` item 1.

## Open items and known limitations (one line each)

- **L-14 / IMP-16 continuity**: 0.15 (0-0.30) stays a labelled assumption; no study measures the share of patients who keep a service after its donor funding is withdrawn (0.30 is a sensitivity value).
- **L-27 / IMP-02c**: testing-and-care money is a stock proxy (kappa 0.5, assumption); the flow-of-initiations treatment is blocked for lack of a cost per initiation.
- **L-05 hss_kappa**: 0.5 (0.25-0.9) for testing-and-care money remains an assumption.
- **L-41 / L-49**: HIV infections and deaths are 0.36 / 0.39 of Optima's PEPFAR-discontinued excess over the 15 overlapping countries (South Africa 0.14 / 0.18); the gap is the money-to-people conversion (full-cost equivalents, continuity, the 23% Global Fund cut), not transmission.
- **L-50 / DR-01**: the ART cost level (median US$216; floor US$191 in 13 countries) would still be settled by PEPFAR Expenditure Analysis cost per patient.
- **L-18 / IMP-15 (partly done)**: the vaccine unit is still a full-schedule child at `uc_imm` US$87; donor money buys specific antigens; no cost per antigen.
- **L-42 (done, with a stated gap)**: vaccine deaths exclude DTP, polio and BCG for lack of a citable per-child value; a conservative floor.
- **Vaccine timing beyond 2035**: lifetime deaths averted after the 2031-2035 window (adult hepatitis B, meningitis A and yellow fever at age 5+) are not counted anywhere.
- Test test_late_vaccine_cut_committed updated from the superseded 60% assumption to the VIMC-based timing rule (approved). It now checks that the committed share of a 2030-only vaccine cut equals the share implied by the country's own timing inputs (lags 1-5 of imm_dpc_lag0..9 over lags 0-5), that within-window plus committed deaths equal the cohort's total, and that a late cut still commits deaths after 2030.
- **A3 case management**: the intervention-specific share is applied to malaria treatment as well as nets and spraying; the alternative (GHED all-source share for treatment) would give 84,075 instead of 123,822 treatment deaths under Full US Exit.
- **L-06 / IMP-06**: aid baseline is 2021-23; 2025 US cuts already in force are not netted out; coverage is 2024-25.
- **L-08 / IMP-08 (partly done)**: MOU co-financing commitments are not modelled (labelled).
- **L-28 / IMP-14 (partly done)**: the OECD preset applies total-aid cuts to health aid (labelled).
- **L-03 / IMP-23**: 70 countries, 71.5% of country-coded aid; Myanmar, Sudan, Afghanistan, Chad, Yemen, Ukraine missing.
- **L-07, L-21, L-22, L-23**: bednet survey defaults (50% where no MAP or recent survey), IRS household share applied to people, IRS implied by donor spending where MAP shows none, MAP vs WHO case differences (Pakistan).
- **L-24 / IMP-17**: need (births, PLHIV, incidence) held at the latest year through 2030.
- **L-11**: `hiv_deaths_est` (GBD-2019 share via Gapminder) still feeds the Lancet rate-ratio method on the Validation page.
- **L-15**: TB case fatality is placed in the year of loss; secondary cases all arrive in 1-2 years.
- **L-29, L-31, L-34, L-35**: fiscal-capacity and MOU presentation details (not cumulative capacity; untagged WEO vintage; mixed interest definitions; nominal MOU amounts).
- **L-32**: `uc_pmtct` 250 review figures not verified.
- **L-38 / IMP-12**: Sections 1-3 per-country files cannot be rebuilt from scripts in the repository.
- **L-39**: India's TB systems and unspecified money follows its own line mix toward DR-TB.
- **L-09**: Gavi -15% default is an estimate (preset only).
- **Red-team flags in Batch 3+4**: TB deaths +91% from the lower course costs (item 5) remain in the model; the WHO budget-per-patient cross-check (Validation section 2) shows the course cost at 0.47 of programme budgets at the median.
