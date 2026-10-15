# Batch 5+6: ART cost floor, input-share check, malaria cap concept, vaccines, validation, SPEC reproduction

Follows Batch 4b (`batch4b_evidence.md`). Rules: real citations only (author, year, table or page); labelled
assumptions with a range where no evidence exists; every input must measure what the model uses it for, or carry a
labelled adjustment; never choose a value for its effect on results; all money in constant 2023 US$ through
`health_model.inflate` (CPI-U). Branch `tomato`. Before snapshot: `audit/before_batch56.csv` (local, uncommitted;
`audit/snapshot_numbers.py` at commit `178733c`). Headline = all countries, Full US Exit (US Bilateral Exit +
Multilateral Withdrawals), central run, no government response, sudden cut, deaths 2026-2030. Before this batch:
**1,695,601** (HIV 938,069; TB 463,973; malaria 190,824; vaccines 102,735; further deaths 2031-35 933,796; HIV
infections 3,785,457; people who stop ART 4,563,706 a year).

Scripts (read-only with respect to the model; outputs beside this file):

| Item | Script | Output |
|---|---|---|
| A1 | `audit/batch56_art_cost.py` | `batch56_art_cost.csv` (70 countries, old and new ART cost, rule applied) |
| A2, A3 | `audit/batch56_donor_share.py`, `audit/batch56_malaria_cap.py` | `batch56_donor_share.csv`, `batch56_malaria_cap.csv` |
| V1 | `audit/batch56_vaccines.py` | `batch56_vaccines.csv` (country x antigen), `batch56_vaccine_timing.csv` |
| VAL1 | `audit/batch56_validation.py` | `validation.md` |

Decisions that needed a judgement are marked **Decision** with the reason.

## A1. ART cost: validity of the observed-spending measure, a delivery-cost floor, the gate on the final value

**Problem (Batch 4b item 2).** Observed HIV treatment spending per person on ART, (b) = total HIV spending x the
country's Global Fund GC7 treatment-and-care module share / UNAIDS people on ART, used the Global Fund share as a
proxy for the national treatment share. Where the Global Fund funds little HIV the proxy fails (South Africa US$35,
Dominican Republic US$51, Eswatini US$80, Niger US$29 per patient-year), and the US$57 floor (TLD + one viral load
test) is a commodity price, not a delivery cost.

**Rule 1: validity.** (b) is used only where the Global Fund's share of total HIV spending is at least 10%. Global
Fund share = HIV and TB/HIV disbursements to the country (Global Fund Data Explorer, `datasets/GlobalFund/
GF_disbursements_2026-10-14.csv`; the mean of the spending year and the two years around it, because disbursements
are lumpy) / total HIV spending in the spending year (ten Brink et al. 2025 appendix Table B2, p. 8, for the Optima
countries; WHO GHED `dis11_usd` elsewhere, as in Batch 4b). Table B2 gives PEPFAR and "other international" funding
but not the Global Fund alone, so the Global Fund amount comes from its own disbursement records in every country
(stated source). 43 countries have (b); 35 are valid; invalid: Botswana (0.04), Dominican Republic (0.09), Guyana
(0.05), Namibia (0.06), Nigeria (0.07), Philippines (0.06), São Tomé and Príncipe (0.00), South Africa (0.09).
Invalid and missing countries use (a) x the WHO-region median of (b)/(a) over the valid countries only: AFR 0.52
(27 countries), EUR 0.92 (4); AMR (1 valid), EMR (1), WPR (2) and SEA (0) have fewer than 3 valid countries and use
the median over all 35 valid countries, 0.54. **Decision:** the 3-country minimum follows `audit/batch34_art_costs.py`
(the same rule for the site costs); with it, the Americas and Asian countries that in Batch 4b took their region's
median from 1-3 countries (AMR 1.66, so (a) itself; WPR 0.89) now take the overall median, which is why Belize,
Bolivia, Guatemala, Honduras, Jamaica, Nicaragua, El Salvador, Venezuela, Indonesia, Laos, Viet Nam, Papua New
Guinea, Fiji, the Philippines and Guyana move from US$356-400 to US$216.

**Rule 2: floor.** The lowest measured site-level ART delivery cost in `unit_cost_reference.csv` is Malawi,
US$86.50 per patient-year in 2018 US$ (Rosen et al. 2021, *Gates Open Research* 5:177, AMBIT synthesis:
conventional facility-based care; ARVs, laboratory tests, staff, space and overhead at site level). Inflated to 2023
US$ (`health_model.inflate`, CPI-U 304.702 / 251.107): US$104.96. Multiplied by the above-site markup
1 / (1 - asd_share) = 1.818 (asd_share 0.45: KFF 2025, Gaba, Razavi, Kates & Nandakumar, *Which PEPFAR Investments
Drive HIV Outcomes?*, PEPFAR expenditure data 2018-2023, non-service delivery 47% of spending): **US$190.84**.
Basis: a full programme cost per patient-year (site delivery cost plus above-site programme cost), the same basis as
(a) and as the model's use of the cost (lost programme money / full cost per patient-year = people who stop ART).

**Rule 3: gate.** US$50-600 on the final value (no country touches it).

**Result** (`batch56_art_cost.csv`): median US$216 (191-400), was 274 (57-400). 43 of 70 countries change:

| Rule applied | Countries (old -> new, 2023 US$) |
|---|---|
| Observed spending invalid (Global Fund share < 0.10), regional ratio | South Africa 57 -> 208; Namibia 57 -> 208; Nigeria 400 -> 208; Botswana 137 -> 208; São Tomé and Príncipe 355 -> 208; Dominican Republic 57 -> 216; Guyana 400 -> 216; Philippines 356 -> 216 |
| Floor (observed spending valid but below US$191) | Niger 57 -> 191 (observed 29); Mali 69 -> 191; Eswatini 80 -> 191; Central African Republic 99 -> 191; Sierra Leone 103 -> 191; Mauritius 108 -> 191; Tajikistan 116 -> 191; Zimbabwe 129 -> 191; Burkina Faso 132 -> 191; Togo 142 -> 191; South Sudan 154 -> 191; Benin 172 -> 191 |
| Floor (regional ratio below US$191) | Lesotho 135 -> 191 |
| No observed spending, regional ratio changed (AFR 0.50 -> 0.52) | Angola, Côte d'Ivoire, Rwanda 200 -> 208 |
| No observed spending, region with < 3 valid countries -> overall median 0.54 | Belize, Bolivia, Guatemala, Honduras, Jamaica, Nicaragua, El Salvador, Venezuela 400 -> 216; Indonesia, Laos, Viet Nam, Papua New Guinea, Fiji 356 -> 216; Egypt, Iraq, Jordan, Libya, Pakistan, Somalia 274 -> 216 |

Unchanged: Kenya 308, Uganda 314, Mozambique 227, Malawi 199, Zambia 224, Tanzania 367, Ethiopia 314, DR Congo 314,
Cambodia 195, Moldova 199, Ghana 232, Senegal 208, Cameroon 216, Guinea 325, Burundi 299, Gambia 297, Djibouti 274,
Azerbaijan, Kyrgyzstan, Mongolia, Haiti, Liberia, Madagascar, Bangladesh, Nepal, Timor-Leste, India (216, overall
ratio as before) and the other countries whose regional ratio did not move.

**Range.** `uc_art_mult` keeps 0.68-1.38; `art_cost_full_hi` = the higher of (a) and the candidate within the gate
(South Africa 208 -> 400 at 1.38; Kenya 308 -> 600).

**Effect** (Full US Exit, all countries, central): deaths 2026-30 1,695,601 -> **1,666,755 (-1.7%)**; HIV deaths
938,069 -> 909,223 (-3.1%); people who stop ART 4,563,706 -> 4,418,867 a year; HIV infections 3.79M -> 3.64M; further
deaths 2031-35 933,796 -> 904,798; TB, malaria and vaccines unchanged. South Africa's HIV deaths fall (cost x3.6) while
Nigeria's rise (cost 400 -> 208) and the Americas and Asian countries rise. HIV baseline only rebuilt
(`tests/make_baseline.py --batch34 HIV`: 42 entries, only `hiv_art` moved; no lives-first entry moved other lines).

## A2. L-51: the spending share used for the HIV and immunization pools (fix applied)

Script `audit/batch56_donor_share.py`, output `batch56_donor_share.csv`. The cap on the donor-funded pool (Batch 3+4
item 6) uses the external share of the country's spending on the disease. Composition of the GHED totals, latest year
(million current US$):

| Country | HIV year | HIV total | external | domestic government | domestic private | all-source share (used before) | public share (used now) | Imm year | Imm total | external | government | private | all-source | public |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Kenya | 2019 | 825 | 555 | 206 | 65 | 0.67 | 0.73 | 2019 | 29.4 | 26.5 | 2.8 | - | 0.90 | 0.90 |
| Nigeria | 2022 | 1,636 | 302 | 245 | 1,089 | 0.18 | 0.55 | 2022 | 658 | 261 | 154 | 243 | 0.40 | 0.63 |
| Mozambique | 2018 | 541 | 452 | 59 | 30 | 0.84 | 0.88 | 2018 | 34.5 | 27.5 | 6.8 | 0.1 | 0.80 | 0.80 |
| South Africa | 2019 | 3,288 | 331 | 2,958 | - | 0.10 | 0.10 | - | no GHED value: AFR median 0.64 -> 0.68 | | | | | |
| Uganda | 2021 | 350 | 273 | 66 | 11 | 0.78 | 0.81 | 2021 | 16.8 | 5.0 | 11.8 | - | 0.30 | 0.30 |
| India | - | no GHED value: median of model countries 0.59 -> 0.68 | | | | | | 2019 | 1,134 | 14 | 738 | 382 | 0.013 | 0.019 |

Sources: WHO GHED (`datasets/WHO_GHED/GHED_data_2026-10-14.xlsx`): `dis11_usd`, `dis11_ext_usd`, `dis11_gghed_usd`,
`dis11_pvtd_usd` (HIV/AIDS and other STDs); `hc62_*` (immunization programmes). Across the model countries: HIV data
for 40 of 70; private share median 0.08 (IQR 0.04-0.17); public minus all-source share above 0.10 in 10 countries
(Nigeria 0.37, Guinea 0.42, Senegal 0.22, Niger 0.15, Liberia 0.18, Togo 0.19, Central African Republic 0.30,
Madagascar 0.24, Malawi 0.12, Tanzania 0.10). Immunization data for 48 of 70; private share median 0 (IQR 0-0.22);
gap above 0.10 in 5 countries (Togo, Nigeria, Senegal, Madagascar, Mongolia).

**Decision: fix applied (same mismatch as Batch 4b item 3, shown with numbers).** GHED's `dis11` is "HIV/AIDS and
other STDs"; its domestic private part is household spending on STI treatment and private-sector HIV care, which is
not the ART donors and governments finance (ART is free at public facilities in every model country). Private
immunization spending is private-sector vaccination outside the national programme. Neither is the service the
donor money buys, so dividing donor money by a total that includes them understates the donor-funded pool, exactly
as household treatment spending did for nets. Both lines now use external / (external + domestic government), the
rule bednets and spraying use since Batch 4b; nothing changes where private spending is zero (South Africa, Kenya
immunization, Uganda immunization). Fallbacks (regional / overall median of the public share) move slightly (HIV
median of model countries 0.59 -> 0.68; AFR immunization 0.64 -> 0.68). Labelled as before: a spending share is the
closest external measure of the share of covered people whose service donors fund, not that share itself.

**Effect** (Full US Exit, all countries, central): deaths 1,666,755 -> **1,757,745 (+5.5%)**; HIV deaths 909,223 ->
998,535; vaccine deaths 102,735 -> 104,413; people who stop ART 4,418,867 -> 4,861,100 a year; HIV infections 3.64M ->
3.97M; further deaths 2031-35 904,798 -> 996,769. Nigeria carries most of it: ART pool 0.18 -> 0.55 of people on
ART, people who stop ART 184,289 -> 562,261 a year, deaths 141,057 -> 217,224. HIV and immunization baselines rebuilt
(`tests/make_baseline.py --batch34 HIV,Immunization`: 67 entries; `hiv_art`, `hiv_pmtct` (the PMTCT line shares the
HIV pool share) and `imm` moved; no lives-first entry moved other lines).

## A3. Malaria cap: the donor share must be the share of the intervention (fix applied)

Scripts `audit/batch56_malaria_cap.py` (diagnosis; `batch56_malaria_cap.csv`) and `audit/batch56_donor_share.py`
(shares written to `country_inputs.csv` by `batch34_inputs.py --donor56-malaria`).

**Step 1: diagnosis** (Full US Exit, central; the five largest malaria countries by WHO 2024 deaths; "before the
cap" = the pre-IMP-04 rule, every covered person in the pool; "now" = the Batch 4b rule):

| Country | Line | Lost donor money (US$/yr) | People that money covers (lost money / unit cost) | Current coverage (MAP 2025) x base | People covered | Share used in the cap | Pool now | Deaths 2026-30 before the cap | now |
|---|---|---|---|---|---|---|---|---|---|
| Nigeria | bednets | 32.7M | 14.9M person-years of use | ITN use 0.279 x 232.7M at risk | 65.0M | 0.218 (public malaria spending) | 14.1M | 32,806 | 11,221 |
| Nigeria | spraying | 5.1M | 0.60M | donor-implied 0.009 (MAP 0%) x 232.7M | 2.18M | 0.218 | 0.48M | 1,021 | 220 |
| Nigeria | case management | 11.3M | 0.81M cases | effective treatment 0.558 x 69.0M cases | 38.5M | 0.029 (all-source) | 1.10M | 16,643 | 5,119 |
| DR Congo | bednets | 21.7M | 9.9M | 0.463 x 109.3M | 50.6M | 0.769 | 38.9M | 19,035 | 19,033 |
| DR Congo | case management | 11.2M | 0.80M | 0.419 x 27.9M | 11.7M | 0.423 | 4.9M | 11,733 | 11,733 |
| Niger | bednets | 6.7M | 3.1M | 0.886 x 27.0M | 23.9M | 0.503 | 12.0M | 17,686 | 17,654 |
| Niger | case management | 1.8M | 0.13M | 0.535 x 7.5M | 4.0M | 0.219 | 0.88M | 4,392 | 4,391 |
| Tanzania | bednets | 13.8M | 6.3M | 0.615 x 68.6M | 42.2M | 0.220 | 9.3M | 8,564 | 4,569 |
| Tanzania | case management | 8.4M | 0.60M | 0.664 x 9.1M | 6.0M | 0.163 | 0.98M | 17,560 | 7,973 |
| Ethiopia | bednets | 11.0M | 5.0M | 0.086 x 89.8M | 7.7M | 0.652 | 5.0M | 1,740 | 1,132 |
| Ethiopia | case management | 6.5M | 0.47M | 0.291 x 16.7M | 4.9M | 0.404 | 1.97M | 3,184 | 3,177 |

(Spraying rows for DR Congo, Niger, Tanzania and Ethiopia are in the CSV; deaths under 300 each.) Across the 46
malaria countries the Batch 4b cap binds in 24 bednet, 35 spraying and 32 case-management lines and removes 86,128
of 276,952 malaria deaths (bednets 148,831 -> 104,023; spraying 4,299 -> 2,726; case management 123,822 -> 84,075);
Nigeria alone accounts for 33,900 of them. The mechanism: in Nigeria donor bednet money buys 40.9M person-years of
net use a year, 63% of the 65.0M people MAP counts as sleeping under a net, but the public-spending share (0.218)
gives the pool 14.1M, so the cap says donors fund 22% of net users while their money pays for 63%.

**Step 2: intervention-specific share.** share_l = donor money for the intervention (baseline, after the Batch 3+4
split of unspecified money by Global Fund module shares) / (people covered x the model's unit cost for l), capped at
1. Donor money for l is the model's own E_base[l] (IHME programme areas `mal_con_nets` + `mal_con_oth`,
`mal_con_irs`, `mal_diag` + `mal_treat` + `mal_comm_con`, plus the prevention or treatment share of unspecified
money). Unit costs: `uc_itn` 2.2 per person-year of net use, `uc_irs` 8.5 per person-year protected, `uc_mal_cm`
14 per case treated. Every one of the 70 countries has at least one IHME malaria programme-area line, so the regional
median fallback is not needed (coded for completeness). Result: median share bednets 0.53 (Nigeria 0.63, DR Congo
0.65, Niger 0.35, Tanzania 0.40, Ethiopia 1.0), spraying 1.0 (donor money is what sets the coverage in most countries,
L-22), case management 0.39 (Nigeria 0.09, DR Congo 0.28, Tanzania 0.35). New pool = people covered x share_l =
min(people covered, people the donor money pays for). Cross-check on the direction: the World Malaria Report 2025
(chapter 4, p. 60-63) puts international funding at 56% of all malaria funding in 2024 and reports that "most
countries completed their mass campaigns as planned with Global Fund-financed nets" when PMI nets were delayed
(chapter 8); WMR's own expenditure series excludes out-of-pocket spending and "are thus not comparable with the
disease expenditure data ... reported in WHO's Global Health Expenditure Database" (p. 60, note a), which is the GHED
total the Batch 3+4 cap divided by.

**Step 3: coverage concept.** Bednets: the cap uses MAP ITN *use* (people sleeping under a net) x population at risk;
the money buys person-years of use at `uc_itn`, which is already a cost per person-year of *use* (GiveWell: cost per
net / (people per net x years of protection) / share of nets used), and the Lives Saved Tool effect (Eisele et al.
2010) is per child *sleeping under* a net, so use is the right measure on all three sides and no use-to-access
conversion is needed (MAP use / access: median 0.93 across 40 African countries, Nigeria 0.75). Spraying: MAP IRS
coverage is households sprayed, applied to people at risk (L-21, noted); money buys person-years protected. Case
management: MAP effective treatment per 100 cases x MAP clinical cases; money buys cases treated at the diagnosis +
treatment cost; `mal_cm_eff` is the effect of effective treatment (Thwing et al. 2011). Consistent.

**Step 4: annualisation of the net cost.** `uc_itn` = US$2.20 per person-year of net use = US$5 per net delivered
(GiveWell, US$4-6) / (1.8 people per net x 2 years of protection) / 0.63 of nets in use = 5 / 3.6 / 0.63 = 2.20. It
is per person-year, not per net: no error. With a 3-year life (WHO's planning assumption; the WMR 2025 notes that
Madagascar's 2021 nets "have exceeded their effective lifespan" by 2024, p. 20) the cost is US$1.47, inside the
parameter's 1.4-3.5 range; the central value is kept (the range already covers it; changing it would be tuning).

**Step 5: concept fix, not tuning.** The cap exists to stop donor money from being credited with more people than it
pays for (L-44). A share of *all* public malaria spending is not the share of *net users* donors pay for; the people
the net money pays for is. **Decision:** implement for all three lines (the same rule the user set in step 2; for case
management the household share of treatment spending is now irrelevant because the pool is set by the donor money for
treatment itself, at the model's unit cost). Implementation: `country_inputs.csv` `donor_share_mal_itn`, `_mal_irs`,
`_mal_cm` (+ `_source`); `health_model.DONOR_SHARE_LINE` maps the malaria lines to them; `donor_share_malaria_prev`
and `donor_share_malaria` stay in the file for reference and as the fallback if a column is missing.

**Effect** (Full US Exit, central, all countries): malaria deaths 2026-30 190,824 -> **276,952 (+45%)**: bednets
104,023 -> 148,831, spraying 2,726 -> 4,299, case management 84,075 -> 123,822; the cap now binds only where donor
money exceeds the full cost of current coverage (9 bednet lines, 14 case-management lines, 0 spraying lines). Five
largest: Nigeria 16,559 -> 50,470 (bednets 11,221 -> 32,806; case management 5,119 -> 16,643; spraying 220 -> 1,021);
DR Congo 30,807 -> 30,821; Niger 22,086 -> 22,157; Tanzania 12,603 -> 26,411 (bednets 4,569 -> 8,564; case management
7,973 -> 17,560); Ethiopia 4,608 -> 5,223. Headline 1,757,745 -> **1,843,873 (+4.9%)**. **FLAG check:** no country's
annual excess malaria deaths (deaths 2026-30 / 5) exceed its current annual malaria deaths (WHO 2024, the World
Malaria Report 2025 estimates in `ext_data/gho/MALARIA_EST_DEATHS.csv`); the highest ratios are Zambia 0.28, Rwanda
0.27, Senegal 0.23, Kenya 0.22, Tanzania 0.20. Malaria baseline only rebuilt (84 entries; `mal_itn`, `mal_irs`,
`mal_cm`; no lives-first entry moved other lines).

## V1. Vaccine evidence (no model change in this item)

Script `audit/batch56_vaccines.py`; outputs `batch56_vaccines.csv` (620 country-antigen rows: 112 VIMC countries plus
the 4 model countries not in VIMC), `batch56_vaccine_timing.csv`, `batch56_vaccine_country.csv` (70 model countries).
Sources: Vaccine Impact Modelling Consortium estimates (Toor et al. 2021, *eLife* 10:e67635, supplementary data:
`datasets/Toor2021/VIMC_deaths_by_year_of_vac.csv`, `_cross_section.csv`, `_cohort.csv`); WHO/UNICEF Estimates of
National Immunization Coverage, 2025 revision (`datasets/WUENIC_2025.xlsx`, sheet `country`); UN WPP 2024
(`datasets/WPP2024/WPP2024_Demographic_Indicators_Medium.csv`: `LBsurvivingAge1`, `Births`, `Q5`; counts in thousands).

**1. Scope and mapping.** Routine infant vaccines in the cost per fully immunized child (`uc_imm`: Lydon et al. 2014
delivery cost per infant + MSF *The Right Shot* vaccine prices). HPV is excluded: an adolescent vaccine (girls 9-14),
not in the infant schedule or in `uc_imm`. VIMC disease -> WUENIC antigen: HepB -> `hepb3` (the birth dose `hepbb`
is in WUENIC but the same child is counted by `hepb3`); Hib -> `hib3`; PCV -> `pcvc`; Rota -> `rotac`; Measles ->
`mcv1` (MCV2 is a second dose to the same children); Rubella -> `rcv1`; YF -> `yfv`; MenA -> `menga`. **Cannot be
mapped:** JE (no WUENIC antigen in the 2025 file; VIMC has JE estimates for 17 countries, among the model countries
Cambodia, Laos, Viet Nam, Nepal, Indonesia, the Philippines, Bangladesh, India, Timor-Leste, Myanmar is not modelled);
excluded.

**2. Denominators** (WUENIC definitions: all antigens used here are measured against surviving infants; BCG and the
HepB birth dose against live births). Vaccinated children in year y = coverage(y) / 100 x WPP `LBsurvivingAge1`(y) x
1,000.

**3. Deaths averted per vaccinated child** = VIMC year-of-vaccination deaths averted (lifetime deaths averted
attributed to the vaccination year; Toor et al. 2021, Methods "Impact by year of vaccination") / vaccinated children,
mean over 2015-2019 (VIMC used reported WUENIC coverage up to 2018 and Gavi forecasts from 2019; 2015-2019 is the
window set for this item). Range from `deaths_av_lo` / `deaths_av_hi` (95% credible intervals). Six negative YF
values (small countries) are clipped at 0.

**4. Mortality trend adjustment (labelled).** value x [mean WPP Q5 2026-2030 / mean WPP Q5 2015-2019] of the country
(Kenya 0.84, Nigeria 0.81, Mozambique 0.75, South Africa 0.80, Uganda 0.66, India 0.62). It is applied to the whole
value; the part the model counts (deaths within ten years of vaccination, section 7) is child mortality, for which the
under-5 trend is the right scaler; the adult part (HepB) is not counted in the model's window.

**5. Routine vs campaign.** The VIMC files do not separate routine from campaign vaccination: one value per
disease-year, with both RI and NRI attributed to the year of vaccination (Toor et al. 2021: "impact ratios stratified
by vaccine activity type", Methods). Estimated inflation = mean / minimum of the five yearly per-child values (a year
without a campaign is closest to routine-only), median across countries: MenA 3.9x, measles 1.10x, YF 1.10x, rubella
1.07x, others 1.04-1.06x. **Decision (conservative, labelled):** measles, MenA and YF use the minimum-year value with
its own lo/hi. The measles per-child value (median 12.8 per 1,000 MCV1 recipients) is about twice Toor's 6.5 per
1,000 FVPs because Toor's denominator counts MCV1, MCV2 and campaign doses separately; "Most of the mortality
reduction from measles is attributable to routine MCV1" (Toor et al. 2021, Results). Rubella introduction campaigns
inflate India (30.9x Toor) and Indonesia (13.7x); the gate below catches them.

**6. DTP (pertussis, tetanus, diphtheria), polio and BCG.** Not in VIMC. Shattock et al. 2024 (*Lancet* 403:2307,
"Contribution of vaccination to improved survival and health: modelling 50 years of the Expanded Programme on
Immunization") report 154M deaths averted over 1974-2024 by pathogen (measles 93.7M; tetanus, pertussis, TB and
polio among the rest) for the world and WHO regions, but no deaths averted per vaccinated child by country or region
could be found in the article or located in its appendix (web search, 14 October 2026). **Decision:** excluded, not
invented; the dashboard states that vaccine deaths exclude DTP, polio and BCG and are therefore a conservative floor
(item V2).

**7. Timing by years since vaccination.** Identified by non-negative least squares (`scipy.optimize.nnls`), pooling
all VIMC countries and calendar years 2000-2019: under-5 deaths averted in calendar year y (cross-section file) =
sum over k = 0..4 of under-5 lifetime deaths averted of birth cohort y - k (cohort file) x v_k. Fit (R2): HepB 1.000,
Hib 1.000, PCV 0.999, Rota 0.999, Rubella 1.000, measles 0.991, YF 0.998, MenA 0.968 (2,240 country-years; 520 for
MenA, 720 for YF). Weights v_0..v_4 (share of the under-5 deaths by years since vaccination): measles 0.77 / 0.23 / 0
/ 0 / 0; Hib 0.59 / 0.23 / 0.09 / 0.04 / 0.06; PCV 0.57 / 0.24 / 0.07 / 0.08 / 0.03; Rota 0.64 / 0.36 / 0 / 0 / 0;
rubella 1 / 0 / 0 / 0 / 0 (congenital rubella deaths in infancy); HepB 0.42 / 0.21 / 0.16 / 0.13 / 0.09; MenA 0 /
0.13 / 0.71 / 0.16 / 0; YF 0.20 / 0.17 / 0.24 / 0.19 / 0.20. The under-5 share of lifetime deaths averted is
country-specific (cohort file, under5 / all, cohorts 2015-2019; pooled: Hib, PCV, Rota, rubella 1.00; measles 0.94;
JE 0.37; MenA 0.15; YF 0.08; HepB 0.015, its deaths are adult liver disease). Years 5-9: the same fit on all-age
deaths with lags 0-11 identifies small shares for measles (0.4% and 0.6% of lifetime deaths at lags 7-8; R2 0.99) and
HepB (0.4% in total; R2 0.975); for MenA and YF the all-age fit fails (R2 0.69, 0.66), so deaths at age 5 and over are
counted as lifetime deaths beyond the model's window (labelled assumption, conservative). Hib, PCV, Rota and rubella
have no deaths after age 5 by construction.

**GATE** (0.1x-10x of Toor 2021 Table 3, deaths averted per 1,000 FVPs: measles 6.5, HepB 7.7, YF 2.1, Hib 2.4,
PCV 2.3, rubella 0.3, Rota 0.8, MenA 1.0): 38 of 620 country-antigen values fail; 36 are below 0.1x (Hib, PCV, Rota,
HepB in low-mortality countries of Europe, the Americas, the Eastern Mediterranean and Sri Lanka; MenA in Côte
d'Ivoire, Central African Republic and Ghana) and 2 above 10x (rubella in India 30.9x and Indonesia 13.7x, campaign
years; YF in Cameroon 10.8x). They take the WHO-region median of the passing countries (the median over all passing
countries where the region has fewer than 3). Model countries affected: Belize HepB, Jamaica HepB and Hib, El
Salvador HepB, Jordan Rota, Moldova Hib / PCV / Rota, Haiti PCV, Ghana and Côte d'Ivoire MenA, India and Indonesia
rubella, Cameroon YF. Countries not in VIMC (Botswana, Dominican Republic, Libya, Mauritius) take the regional median
for every antigen they use.

**Result for the model countries** (`batch56_vaccine_country.csv`; deaths averted per fully immunized child = sum
over the antigens with WUENIC coverage > 0 in 2025): median 0.0252 (0.0079-0.0648); Kenya 0.0209 (7 antigens),
Nigeria 0.0590 (5: no rotavirus or rubella), Mozambique 0.0304, South Africa 0.0214, Uganda 0.0270, India 0.0122. Of
these, the part falling within ten years of vaccination is Kenya 0.0143, Nigeria 0.0415, Mozambique 0.0225, South
Africa 0.0161, Uganda 0.0191, India 0.0096; the rest (HepB, MenA, YF adult deaths) is lifetime deaths beyond the
window. For comparison the previous rule (0.020 x 0.65 x clip(U5MR / 50)) gave Kenya 0.0101, Nigeria 0.0301,
Mozambique 0.0154, South Africa 0.0091, Uganda 0.0127, India 0.0069. Lo / central median 0.56, hi / central 1.64.

## V2. Vaccines implemented (one commit)

**Rule.** Deaths per fully immunized child lost = the country's `imm_dpc` (item V1: sum over the routine antigens the
country uses of the adjusted VIMC deaths averted per vaccinated child), spread over years since vaccination by
`imm_dpc_lag0..lag9` (item V1 step 7). For each vaccination-year cohort s = 2026..2030, deaths in year s + k count in
2026-2030 while s + k <= 2030 and in further deaths 2031-2035 while s + k <= 2035; the lifetime remainder
(`imm_dpc_beyond_window`, mostly adult hepatitis B) is not counted anywhere (`health_model.imm_per_child`,
`lives()`). No calendar mortality trend applies to vaccines (the Q5 2026-30 ratio is in the value), so the
"already-changing death rates" switch no longer moves vaccine deaths. Countries not in VIMC take the regional median
per antigen (V1). `uc_imm` is unchanged. **Monte Carlo:** `imm_dpc_mult` (central 1, low 0.56, high 1.64 = the
medians over the model countries of the VIMC low / central and high / central ratios) maps linearly onto each
country's own `imm_dpc_lo` and `imm_dpc_hi`, as `uc_art_mult` does for the ART cost, so the central run stays inside
the displayed range. **Legacy:** `imm_legacy_u5mr_scaling` = 1 (default 0, constant) restores the previous rule
(0.020 x 0.65 x clip(U5MR / 50), weights 0.40 / 0.35 / 0.20 / 0.05, under-5 trend); `imm_deaths_per_child_ref` and
`imm_u5_share` are relabelled as legacy parameters. The two new parameters are appended at the end of
`model_params.csv` so the other parameters' draws do not shift. Lives-first ranking and the Poisson cross-check use the
cumulative per-child deaths over years 1-5 (`per_unit_deaths`). The dashboard's Routine Immunization row and the
Methods and Validation pages state that vaccine deaths exclude DTP, polio and BCG and are a conservative floor.

**Effect** (Full US Exit, central, all countries): vaccine deaths 2026-30 104,413 -> **187,945 (+80%)**; the vaccine
part of further deaths 2031-35 21,424 -> 15,243 (the VIMC timing puts 64-100% of under-5 deaths in the first two
years after vaccination, against 40% / 35% / 20% / 5% before, so less spills past 2030); headline 1,843,873 ->
**1,927,405 (+4.5%)**; further deaths 996,769 -> 990,588. Immunization baseline rebuilt (`tests/make_baseline.py
--batch34 Immunization`: 73 entries, `imm` in all of them; 13 Kenya and Mozambique lives-first entries also moved
`hiv_art`, `hiv_care_ct`, `tb_dr` and the malaria lines through the refill order, because vaccines' deaths per
dollar rose). `--quick`: 0 failures, 6 known warnings.

## V3. Vaccine check (before = commit `7f07d6b`, after item A3; after = item V2)

Vaccine deaths 2026-2030 and the vaccine part of further deaths 2031-2035 (central, no response, sudden cut), all
countries (`audit/logic_review/batch56_vaccine_check.py` run in a worktree at `7f07d6b` and in the working tree;
full before/after by preset and country in `batch56_before_after.md`):

| Preset | Vaccine deaths 2026-30 before -> after | Vaccine further deaths 2031-35 before -> after | All-disease deaths before -> after |
|---|---|---|---|
| Full US Exit | 104,413 -> 187,945 (+80%) | 21,424 -> 15,243 | 1,843,873 -> 1,927,405 (+4.5%) |
| America First MOUs (16 countries) | 46,508 -> 81,556 (+75%) | 9,870 -> 6,675 | 328,910 -> 363,958 (+10.7%) |
| IHME 2025 preliminary estimates | 13,316 -> 22,489 (+69%) | 2,674 -> 1,742 | 1,423,360 -> 1,432,533 (+0.6%) |
| Total-Aid Cuts (OECD) | 104,120 -> 187,058 (+80%) | 21,357 -> 15,125 | 1,676,407 -> 1,759,346 (+4.9%) |
| Global Fund & Gavi shortfalls | 93,934 -> 170,248 (+81%) | 19,271 -> 13,722 | 654,584 -> 730,898 (+11.7%) |
| Combined retreat | 137,346 -> 247,416 (+80%) | 28,178 -> 20,023 | 2,019,609 -> 2,129,679 (+5.4%) |

Six focus countries, Full US Exit: Kenya 966 -> 1,630 (further 197 -> 123); Nigeria 27,469 -> 43,543 (5,887 ->
3,375); Mozambique 4,065 -> 7,280 (796 -> 562); South Africa 9 -> 20 (2 -> 2); Uganda 3,181 -> 5,970 (613 -> 444);
India 305 -> 542 (56 -> 42). Against the batch start (`178733c`): vaccine deaths 102,735 -> 187,945 (+83%; A2 added
1.6 points, V2 the rest).

**First full check** (after item V3, commit `c53a969`): `audit/checks.py --full`, 59 checks, 76,501 rows, **0 failures,
6 known warnings** (Section 1 vs Section 2 DAH, 2-5% in small countries); 14 min 53 s. `--quick` had 0 failures after
each model item (A1, A2, A3, V2). Tests: 352 pass, 5 fail: `tests/test_paths.py::test_late_vaccine_cut_committed`
for every test country asserts that for a vaccine cut in 2030 only "60% of the cohort's deaths fall after its first
year", the pre-batch cohort weights (0.40 / 0.35 / 0.20 / 0.05); with the VIMC timing 64-100% of a cohort's under-5
deaths fall in the first two years, so the assertion fails by design. The test was not edited (rule: never edit tests
to make them pass) and the failure is recorded here and in `MODEL_CHANGELOG.md` for the user to decide.

## VAL2. Independent reproduction from SPEC.md (no model change)

A separate agent rewrote `audit/logic_review/reproduction/repro.py` from `docs/SPEC.md` (sections 0-7 and the §6
return-to-care range) and the four data files it names only, without reading any model code, for Kenya, Nigeria,
India, Honduras and Mozambique and the four cases (Full US Exit sudden / no response; Full US Exit with a 25%
replacement capped at fiscal capacity; OECD cuts; Full US Exit with a linear phase-out). It now follows every current
rule: unspecified money split by Global Fund module shares and systems money not converted (Batch 3+4), the ART
cohort hazard by years since stopping with second-generation infections (Batch 2), country ART and TB costs
(Batch 3+4, 4b, A1), the donor-funded pool with per-disease public-spending shares (A2) and per-intervention malaria
shares (A3), the World Malaria Report under-5 regional share, and the VIMC vaccine pathway with timing by years since
vaccination (V2). Compared with the dashboard's own numbers (`audit/after_batch56.csv`, `audit/snapshot_numbers.py`
at the end of the batch) by `compare.py`: **1,980 of 1,980 cells within 0.5%, largest difference 0.0000%** (central
values: totals, further deaths, every line's money, units, coverage, deaths and infections, bucket deaths).

The agent listed 23 places where the SPEC was silent or ambiguous (`reproduction/notes.md`, section a). None changed a
number (each reading matched the model), so none is a model bug; the SPEC was clarified where it was silent: the
donor group name behind "US" (§2); TB spread uses the same arrival-year coverage for secondary cases from drug-resistant
patients (§6); ART covered is NaN only if ART % or PLHIV is missing, with nothing subtracted when the PMTCT inputs
are missing (§5); the proportional branch returns 0 when the line's baseline money is 0 (§5); first = 0 when no row is
cut, "any row" meaning any row of the country (§6); the unit-cost fallbacks from `unit_cost_reference.csv` carry the
same multiplier and markup (§5). The others are already determined by the text or concern parts the four cases do not
exercise (lives-first allocation, gradual budget increase, the MOU and IHME presets, cards, draws). No new finding.

**Final full check** (after VAL1, VAL2 and DOC; nothing but documents, the reproduction script and check text changed
since the first): `audit/checks.py --full`, 59 checks, 76,501 rows, **0 failures, 6 known warnings**; 15 min 07 s.
Pushed to `origin/tomato`.
