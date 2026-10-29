# Slide Numbers

Every number below is from the current `tomato` model (commit `e67e85f`, after Batch 7, 15 October 2026), computed
from the precomputed All Countries files (`model_data/all_countries_<preset>.csv` and `_draws.csv`) and fresh
`health_model.run_country` runs with the dashboard defaults. They match `docs/EXPLAINER.md`.

**The range.** Where a range is given it is the dashboard's Range Across Parameter Values: the 2.5th to 97.5th
percentile of 400 Monte Carlo draws in which every parameter in `model_params.csv` is drawn from a triangular
distribution between its low and high values (seed 7, the same draws in every country). For all-country totals the
range is the percentile of the total over all countries in each draw (not the sum of country percentiles). It is
parameter uncertainty only, not a confidence interval; data and model-structure uncertainty are not included.

Rounding: the "slide" column rounds deaths and people to 3 significant figures; the "exact" column keeps the model's
value to the unit.

## a. Full US Exit, All Countries, 2026 To 2030, Dashboard Defaults

Preset US Bilateral Exit + Multilateral Withdrawals (internal key `Full US exit`); No Government Replacement; Sudden
(default) cut path; Account for Already-Changing Death Rates on; 70 countries.

| Output | Slide | Exact | Range (2.5th to 97.5th percentile) |
|---|---|---|---|
| All-disease deaths 2026-2030 (Extra Deaths Over 5 Years) | 1.93 million | 1,928,289 | 1,464,108 to 2,599,999 |
| HIV deaths | 999,000 | 998,517 | 693,230 to 1,646,777 (a) |
| TB deaths | 464,000 | 463,966 | 288,309 to 611,483 (a) |
| Malaria deaths | 277,000 | 276,952 | 141,485 to 314,157 (a) |
| Vaccine deaths (Immunization) | 189,000 | 188,853 | 138,628 to 353,156 (a) |
| New HIV Infections, 5 Years | 3.94 million | 3,936,613 | 2,475,974 to 5,761,482 (b) |
| People who stop ART per year (full-cost equivalents) | 4.86 million | 4,863,492 | 3,402,555 to 6,499,415 (b) |
| Further Deaths, 2031-2035 (Assumption-Driven) | 989,000 | 988,791 | 558,057 to 1,761,321 |
| of which people still off ART | 693,000 | 694,425 | |
| of which new HIV infections | 260,000 | 259,545 | |
| of which TB spread | 19,500 | 19,498 | |
| of which missed vaccines | 15,300 | 15,323 | |
| Aid lost per year (Aid at Risk) | US$3.96 billion | US$3,957,252,047 | not drawn (input) |
| Baseline aid per year | US$10.3 billion | US$10,344,582,000 | not drawn (input) |

(a) Per-disease ranges are computed the same way as the total's range (percentile of the all-country disease total in
each of the 400 draws); the dashboard displays the range only for the all-disease total and for Further Deaths.
(b) The dashboard shows these two as central values only at the all-country level; the ranges given are the sums of
the 70 countries' own 2.5th and 97.5th percentiles, which overstate the true width.

## b. All Six Presets

All countries (America First MOUs: the 16 countries with a signed MOU and a funding schedule), No Government
Replacement, Sudden (default), 2026-2030. Aid lost per year in constant 2023 US$.

| Donor Scenario (dashboard label) | Deaths, slide | Deaths, exact | Range | Aid lost per year | HIV | TB | Malaria | Vaccines | Further Deaths 2031-35 | HIV infections |
|---|---|---|---|---|---|---|---|---|---|---|
| US Bilateral Exit + Multilateral Withdrawals | 1.93 million | 1,928,289 | 1,464,108 to 2,599,999 | US$3,957 million | 998,517 | 463,966 | 276,952 | 188,853 | 988,791 | 3,936,613 |
| America First MOUs (16 countries) | 365,000 | 364,893 | 277,432 to 482,885 | US$699 million | 141,340 | 80,604 | 60,715 | 82,235 | 218,419 | 603,134 |
| IHME 2025 Preliminary Estimates | 1.43 million | 1,432,531 | 1,053,620 to 1,841,909 | US$2,887 million | 584,944 | 614,992 | 209,756 | 22,838 | 563,215 | 2,314,147 |
| Total-Aid Cuts (OECD) Applied to Health Aid | 1.76 million | 1,760,137 | 1,314,369 to 2,236,359 | US$3,242 million | 657,648 | 623,577 | 290,879 | 188,033 | 653,988 | 2,605,168 |
| Global Fund & Gavi Shortfalls (Gavi -15%, Global Fund -20%) | 731,000 | 731,380 | 545,254 to 930,421 | US$1,022 million | 86,231 | 347,169 | 127,082 | 170,899 | 101,389 | 337,780 |
| Combined Retreat | 2.13 million | 2,130,765 | 1,616,025 to 2,825,831 | US$4,233 million | 1,020,690 | 552,284 | 309,218 | 248,573 | 1,018,030 | 4,022,663 |

## c. Top 10 Countries Under Full US Exit

Population: UN World Population Prospects 2024, medium variant, 1 July 2024.

| Rank | Country | Deaths 2026-30, slide | Exact | Range | Population 2024 | Deaths per 100,000 |
|---|---|---|---|---|---|---|
| 1 | Nigeria | 267,000 | 267,231 | 193,821 to 351,055 | 232,679,478 | 114.8 |
| 2 | Mozambique | 179,000 | 179,236 | 131,263 to 264,017 | 34,631,766 | 517.5 |
| 3 | South Africa | 128,000 | 128,455 | 102,786 to 185,685 | 64,007,187 | 200.7 |
| 4 | Tanzania | 116,000 | 115,834 | 85,468 to 164,309 | 68,560,157 | 168.9 |
| 5 | Kenya | 113,000 | 112,827 | 75,222 to 170,029 | 56,432,944 | 199.9 |
| 6 | Uganda | 111,000 | 110,746 | 73,662 to 166,611 | 50,015,092 | 221.4 |
| 7 | DR Congo | 106,000 | 105,780 | 81,489 to 147,762 | 109,276,265 | 96.8 |
| 8 | Zambia | 89,400 | 89,423 | 68,615 to 126,100 | 21,314,956 | 419.5 |
| 9 | Malawi | 80,000 | 80,036 | 58,467 to 126,477 | 21,655,286 | 369.6 |
| 10 | Ethiopia | 70,900 | 70,859 | 53,675 to 99,908 | 132,059,767 | 53.7 |

| Rank | Country | Deaths per 100,000 (2026-30) | Deaths, exact | Population 2024 |
|---|---|---|---|---|
| 1 | Eswatini | 1,588.5 | 19,670 | 1,242,822 |
| 2 | Lesotho | 1,122.3 | 26,237 | 2,337,423 |
| 3 | Namibia | 564.3 | 17,104 | 3,030,131 |
| 4 | Mozambique | 517.5 | 179,236 | 34,631,766 |
| 5 | Botswana | 484.7 | 12,220 | 2,521,139 |
| 6 | Zimbabwe | 418.4 | 69,607 | 16,634,373 |
| 7 | Zambia | 419.5 | 89,423 | 21,314,956 |
| 8 | Malawi | 369.6 | 80,036 | 21,655,286 |
| 9 | Uganda | 221.4 | 110,746 | 50,015,092 |
| 10 | South Africa | 200.7 | 128,455 | 64,007,187 |

## d. Government Response Options (Full US Exit, All Countries)

The dashboard's Government Response selector offers four options; the slider default for Replace a Set Share is 25%;
Where Replacement Money Goes defaults to Pro-rata to what was cut, with Hypothetical best case (triage) under
Advanced; Gradual Budget Increase is shown at its Steady shape, 0.5 points of the government budget a year. Central
run (ranges are not precomputed for the response options).

| Government Response | Deaths 2026-30, slide | Exact | Replaced per year (2023 US$) | Deaths averted vs No Government Replacement | Share averted |
|---|---|---|---|---|---|
| No Government Replacement (default) | 1.93 million | 1,928,289 | 0 | 0 | 0% |
| Replace a Set Share, 25%, pro-rata | 1.58 million | 1,577,677 | US$671 million | 350,136 | 18.2% |
| Replace a Set Share, 25%, hypothetical best case (triage) | 971,000 | 970,553 | US$671 million | 957,221 | 49.7% |
| As Much as Fiscal Space Allows, pro-rata | 1.20 million | 1,197,742 | US$1,487 million | 728,245 | 37.8% |
| Gradual Budget Increase, Steady, 0.5 points a year | 535,000 | 535,064 | US$2,398 million | 1,391,904 | 72.2% |

## e. Kenya Walkthrough (Full US Exit, Default Settings)

Dashboard page: Section 4, "How Aid Cuts Translate into Coverage and Lives in Kenya", unless stated.

**Aid lost per year** (The Numbers: Aid at Risk (per Year); Where the Money Is Lost chart): **US$277.7 million**
(exact US$277,718,187), 57% of Kenya's US$483.6 million baseline.

By source (baseline, lost): United States US$323.8 million, US$277.7 million lost; United Kingdom 25.7, 0; Gates
Foundation 24.7, 0; Other Private 21.4, 0; Germany 18.9, 0; France 18.0, 0; Other DAC Governments 15.1, 0; Nordics
9.4, 0; Canada 9.4, 0; Japan 6.9, 0; Netherlands 5.4, 0; Non-DAC Governments 2.7, 0; Other / Unallocable 2.0, 0;
Development-Bank Lending 0.3, 0. By channel (lost): Bilateral Agency US$202.5 million, NGOs 60.0, Global Fund 13.2
(23% of US money), Gavi 1.9, WHO 0.15, UNFPA 0.03.

By disease (baseline, lost): HIV US$340.3 million, US$236.8 million lost; Malaria 81.4, 26.4; TB 34.4, 12.0;
Immunization 27.5, 2.5 (Where the Money Is Lost chart; the Aid Lost per Year bars).

**Government replacement under the default response:** US$0 (No Government Replacement). The Can Kenya Fill the Gap?
panel shows fiscal space of US$21.1 million a year (health spending US$2,138 million x surge 1.97 points x
debt-stress 0.50), health at 8.65% of government spending (2023), and a break-even rise of 1.12 points a year.

**People losing services, by service** (What Each Service Loses table, People Losing Service column; per year,
central with range):

| Service | Slide | Exact | Range | Coverage Before to After (dashboard Coverage column) |
|---|---|---|---|---|
| HIV Treatment (ART), people who stop ART | 378,000 | 377,732 | 222,290 to 538,810 | 91.2% to 65.7% (-25.5 points of people living with HIV) |
| Prevention Of Mother-To-Child Transmission, women | 14,800 | 14,803 | 10,007 to 16,377 | 91.1% to 56.0% (-35.0 points) |
| TB Case Finding & Treatment, patients | 9,180 | 9,178 | 5,991 to 12,272 | 81.0% to 73.2% (-7.8 points) |
| Drug-Resistant TB, patients | 40 | 40 | 26 to 53 | 47.2% to 43.1% (-4.1 points) |
| Bednets & Other Vector Control, person-years of net use | 4.19 million | 4,185,036 | 2,743,894 to 4,630,529 | 43.7% to 36.3% (-7.4 points) |
| Indoor Residual Spraying, people | 178,000 | 177,828 | 148,325 to 197,705 | 2.7% to 2.4% (-0.3 points) |
| Malaria Testing & Treatment, cases | 314,000 | 313,590 | 108,869 to 337,859 | 57.9% to 49.8% (-8.2 points) |
| Routine Immunization, children | 24,700 | 24,728 | 21,402 to 47,769 | 88.0% to 86.4% (-1.6 points) |

Hero pills: Treatment Lost Each Year 715,343 (ART, PMTCT, TB, malaria treatment); Prevention Lost Each Year 4,387,592
(bednets, spraying, vaccines).

**Deaths by disease, 2026-2030** (Extra Deaths Over 5 Years; What Each Service Loses, Extra Deaths column; Extra
Deaths Each Year chart):

| Disease | Slide | Exact | Range |
|---|---|---|---|
| HIV | 78,700 | 78,750 | 48,691 to 138,342 |
| TB | 19,900 | 19,867 | 11,812 to 26,843 |
| Malaria | 12,600 | 12,580 | 5,304 to 13,351 |
| Immunization | 1,630 | 1,630 | 1,147 to 3,822 |
| All four | 113,000 | 112,827 | 75,222 to 170,029 |

Deaths by year 2026 to 2030: 10,945; 18,057; 23,108; 28,022; 32,696. Further Deaths, 2031-2035
(Assumption-Driven): 63,460 (29,576 to 126,674; 29,359 to 97,853 across the return-to-care assumption).

**HIV infections** (New HIV Infections, 5 Years): 162,000 (exact 162,024; 94,462 to 240,064).

**Deaths per US$1 million of aid lost** (What Every US$1 Million Cut Does, by Disease cards; a US$1 million-a-year cut
to that disease for five years): HIV 290 deaths (about US$17,000 of aid per life lost), TB 2,560 (US$2,000), Malaria
581 (US$9,000), Immunization 644 (US$8,000). Deaths per US$1 million of net aid lost per year in this scenario (table
footer): HIV 66.5, TB 330, Malaria 95.4, Immunization 129.

**MOU status shown** (under the Donor Scenario selector): Kenya has a signed America First MOU with funding data
(group A): "US bilateral aid cut: 0% (2026), 4%, 16%, 20%, 60% (2030), per Kenya's MOU"; it applies only when America
First MOUs is selected.

## f. Default Settings Behind The Headline

- Donor Scenario: US Bilateral Exit + Multilateral Withdrawals (internal key `Full US exit`): US direct channels
  -100%; US money through WHO, Gavi and UNFPA -100%; US Global Fund pledge -23%; other US multilateral money and all
  other donors unchanged.
- How Funding Changes: Sudden (default), 100% of the cut in force in every year 2026-2030.
- Government Response: No Government Replacement.
- Advanced: Fiscal-Space Ceiling Strong year (75th percentile growth); Where Replacement Money Goes Pro-rata to what
  was cut; Cap Replacement at Fiscal Space on; Account for Already-Changing Death Rates on.
- Years counted: deaths from 2026 to 2030 (five years). Further Deaths, 2031-2035 (Assumption-Driven) are reported
  separately and are NOT in the headline.
- Parameters at their central values; ranges from 400 draws.
- Money in constant 2023 US$; aid baseline the 2021-2023 average.

## g. Validation Summary

Full US Exit, central; ratios are model / benchmark (band 0.5 to 2); from `audit/logic_review/validation.md`.

| Disease | Ratio vs benchmark | Reason |
|---|---|---|
| HIV | Deaths 0.39 and infections 0.36 of Optima HIV's PEPFAR-discontinued excess (ten Brink 2025 Table C2, 15 countries; Kenya 1.04, South Africa 0.18, Tajikistan 3.65); people on ART 1.00 of UNAIDS 2025 | Optima removes all PEPFAR support for six years with zero initiations and adds a 24% cut by the five largest donors; the model keeps 15% continuity and converts lost money at the full cost per patient-year |
| TB | Excess deaths a year = 0.09 of WHO 2024 TB deaths at the median (Mozambique 0.79); patients treated 1.00 of WHO notifications; cost per patient 0.47 of the national programme budget per notified patient | Programme budgets fund laboratories, staff, surveillance and drug-resistant management for the whole country; the model's cost is what a lost dollar of treatment money pays for per patient |
| Malaria | Excess deaths a year = 0.06 of World Malaria Report 2025 deaths at the median; maximum 0.28 (Zambia); none above 0.5 | Coverage, cases and deaths from MAP and WHO; Lives Saved Tool effects; donors credited only with the people their money pays for |
| Vaccines | Deaths averted per 1,000 children vs Toor 2021 Table 3 per 1,000 doses: measles 1.97, yellow fever 2.26, hepatitis B 0.74, Hib 0.71, PCV 0.71, rotavirus 0.65, rubella 1.46, meningitis A 1.60 | Per child vs per dose (measles, YF above); lower-mortality countries and the 2026-30 mortality adjustment (below); 38 extreme values replaced by regional medians before use |

## h. Sensitivity Results (Full US Exit, All Countries, Central)

| Case | Setting | Result | Current model |
|---|---|---|---|
| Old TB costs | `tb_ds_cost` and `tb_dr_cost` set to missing so the Laurence et al. 2015 income-group values apply (DS US$332 / 351 / 1,081; DR 1,568 / 8,125 / 6,800) | TB deaths 265,626 (slide 266,000); all-disease 1,729,058 | TB 463,966; all-disease 1,928,289 |
| Legacy ART parameters | `hiv_legacy_art_params` = 1 (hazards 1.2-5.0%, transmission 0.04 for every country, 50% a year return to care, no second generation) | HIV deaths 917,132 (slide 917,000); HIV infections 1,413,929 (1.41 million); Further Deaths 2031-35 446,454; all-disease 1,846,002 | HIV 998,517; infections 3,936,613; Further Deaths 988,791 |
| Old vaccine method | `imm_legacy_u5mr_scaling` = 1 (0.020 x 0.65 x clip(U5MR / 50, 0.3, 2.5); cohort weights 0.40 / 0.35 / 0.20 / 0.05) | Vaccine deaths 104,413 (slide 104,000); all-disease 1,843,873 | Vaccines 188,853; all-disease 1,928,289 |

## i. Coverage Of The Model

- Countries: 70 with recorded aid for the four disease areas (71 in the country list; Panama has none), receiving
  71.5% of the country-coded HIV, TB, malaria and immunization aid in IHME's database; 16 of them run the America First
  MOUs preset.
- Diseases and services: HIV (HIV Treatment (ART); HIV Testing & Care; Prevention Of Mother-To-Child Transmission;
  HIV Prevention (PrEP, VMMC, Condoms, Key Populations); Orphans & Vulnerable Children); TB (TB Case Finding &
  Treatment; Drug-Resistant TB); Malaria (Bednets & Other Vector Control; Indoor Residual Spraying; Malaria Testing &
  Treatment); Immunization (Routine Immunization (Vaccines + Delivery)); plus unspecified and systems money for HIV,
  TB and malaria.
- Years modelled: aid baseline 2021-2023 average; cuts and deaths 2026-2030; deaths set in motion by them followed
  to 2035.
- Money year: constant 2023 US$ (IHME DAH in 2023 dollars; study costs inflated with the US CPI-U).
- Aid modelled: US$10.34 billion a year (HIV US$5,273 million, malaria 1,900, immunization 1,650, TB 1,522); the
  United States provides US$5,204 million (50%).
