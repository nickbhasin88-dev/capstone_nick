# Validation: model results against external benchmarks (Batch 5+6, item VAL1; IMP-19)

Script `audit/batch56_validation.py`; every row in `validation_tables.csv`. Model values are the Full US Exit preset
(US Bilateral Exit + Multilateral Withdrawals), central run, no government response, sudden cut, 2026-2030, after
items A1-V2 of Batch 5+6. **Acceptance band, stated before the results:** a ratio of model to benchmark between 0.5
and 2 counts as agreement for like-for-like quantities; ratios outside it are flagged with a one-line likely
explanation. Nothing was tuned to any benchmark. Where the benchmark's scope differs from the model's, the difference
is stated and the ratio is read as a cross-check, not a test.

## 1. HIV: excess deaths and infections vs Optima HIV (ten Brink et al. 2025, *Lancet HIV*, appendix Table C2, p. 11)

Benchmark: scenario 5 ("PEPFAR discontinued, no mitigation") minus scenario 1 (status quo), cumulative **2025-2030**
(six years). Model: 2026-2030 (five years), US bilateral aid ending plus the US leaving WHO, Gavi and UNFPA and 23% of
its Global Fund pledge; other donors unchanged. Scope differences: Optima's scenario also removes PEPFAR's support of
prevention and testing and models zero ART initiations with partial retention through multi-month dispensing, and its
scenarios 2-5 all include a 24% cut by the five largest donors from 2026 (Table B1); the model keeps continuity at
15% and converts lost money at the full cost per patient-year.

| Country | Model HIV deaths 2026-30 | Optima excess deaths 2025-30 | Ratio | Flag | Model infections 2026-30 | Optima excess infections | Ratio | Flag |
|---|---|---|---|---|---|---|---|---|
| Azerbaijan | 48 | 320 | 0.15 | <0.5 | 245 | 1,080 | 0.23 | <0.5 |
| Cambodia | 472 | 2,930 | 0.16 | <0.5 | 2,796 | 14,990 | 0.19 | <0.5 |
| Côte d'Ivoire | 16,759 | 45,310 | 0.37 | <0.5 | 55,583 | 67,280 | 0.83 | ok |
| Dominican Republic | 6,184 | 5,660 | 1.09 | ok | 21,721 | 22,930 | 0.95 | ok |
| Eswatini | 18,276 | 15,630 | 1.17 | ok | 79,537 | 119,430 | 0.67 | ok |
| Kenya | 78,776 | 75,950 | 1.04 | ok | 164,310 | 187,890 | 0.87 | ok |
| Kyrgyzstan | 261 | 620 | 0.42 | <0.5 | 1,400 | 3,050 | 0.46 | <0.5 |
| Malawi | 68,052 | 127,660 | 0.53 | ok | 196,570 | 420,540 | 0.47 | <0.5 |
| Moldova | 7 | 560 | 0.01 | <0.5 | 88 | 940 | 0.09 | <0.5 |
| Mongolia | 4 | 10 | 0.38 | <0.5 | 35 | 50 | 0.69 | ok |
| Mozambique | 108,445 | 265,000 | 0.41 | <0.5 | 435,314 | 947,800 | 0.46 | <0.5 |
| South Africa | 89,717 | 491,750 | 0.18 | <0.5 | 327,525 | 2,391,020 | 0.14 | <0.5 |
| Tajikistan | 474 | 130 | 3.65 | >2 | 977 | 410 | 2.38 | >2 |
| Uganda | 79,995 | 200,580 | 0.40 | <0.5 | 293,626 | 581,180 | 0.51 | ok |
| Zimbabwe | 63,396 | 133,260 | 0.48 | <0.5 | 250,752 | 324,270 | 0.77 | ok |
| **15 countries** | **530,867** | **1,365,370** | **0.39** | <0.5 | **1,830,478** | **5,082,860** | **0.36** | <0.5 |

Flags and likely explanations (one line each):
- **Total 0.39 (deaths), 0.36 (infections).** Optima's scenario removes all PEPFAR support for six years, including
  prevention and testing, with zero new initiations; the model's cut is five years, keeps 15% continuity and buys
  people at the full cost per patient-year, so it removes fewer people from ART than Optima's coverage drop (Table
  C1: ART coverage 90% -> 66% in Kenya, 96% -> 32% in Mozambique, 89% -> 32% in Uganda under PEPFAR discontinuation).
- **South Africa 0.18 / 0.14.** PEPFAR is 21% of South Africa's HIV spending (Table B2) and the model's donor-funded
  pool is the GHED external share of public HIV spending, 10%, so the model lets 7% of people on ART stop; Optima
  projects a 17-point drop in ART coverage (80% -> 63%) and the largest infection rise of any country.
- **Mozambique 0.41 / 0.46, Uganda 0.40 / 0.51, Zimbabwe 0.48, Côte d'Ivoire 0.37, Malawi 0.53 / 0.47.** The
  high-PEPFAR-share countries: Optima removes PEPFAR's 57-66% of spending outright with ART coverage falling to
  32-40%; the model's share of people who stop ART is 25-40% of those on ART (continuity, the 23% Global Fund cut
  only, and the testing-and-care proxy), see `batch4b_evidence.md` reconciliation.
- **Azerbaijan 0.15, Cambodia 0.16, Kyrgyzstan 0.42, Moldova 0.01, Mongolia 0.38.** Little or no PEPFAR money (Table
  B2: US$0-4.8M); Optima's excess comes mostly from the 24% cut by the five largest donors that is in every Optima
  scenario, which the Full US Exit preset does not include (the OECD and Combined presets do).
- **Tajikistan 3.65 / 2.38.** Table B2 records no international HIV funding at all for Tajikistan, so Optima's
  scenario 5 is nearly its status quo (130 excess deaths), while IHME records US bilateral HIV aid to Tajikistan,
  which the model cuts; the two sources disagree on the inputs, not the mechanism.

### People on ART: model vs UNAIDS 2026 estimates (People receiving antiretroviral therapy, all ages, 2025)

Model people on ART = ART coverage x people living with HIV (GHO, UNAIDS 2025 round) minus women on PMTCT; both sides
come from the UNAIDS estimates, so this checks the inputs, not the model. 65 countries: ratio median 1.00, none
flagged (Kenya 1.01, Nigeria 1.01, Mozambique 1.02, South Africa 1.00, Uganda 0.97, India 1.01). People who stop ART
under Full US Exit as a share of UNAIDS people on ART: median 0.13; Nigeria 0.36, Kenya 0.28, Uganda 0.27, Mozambique
0.25, South Africa 0.07, India 0.01; maximum Haiti 0.68.

## 2. TB

Benchmarks: WHO Global TB Programme 2024 estimates (`TB_burden_countries`, `e_mort_num`), 2024 notifications
(`c_newinc`), 2025 national TB programme budgets (`budget_tot`, nominal US$).

- **Excess TB deaths a year (2026-30 / 5) as a share of WHO 2024 TB deaths**: median 0.087 across 70 countries; above
  0.5 only in **Mozambique (0.79)**; none above 1. Kenya 0.17, Nigeria 0.20, South Africa 0.15, Uganda 0.21, India
  0.01. Mozambique: 96% of HIV spending and most TB money is external (WHO TB financing share 0.83), so losing US
  money removes a large share of treated patients (106,000 treated; 14,000 TB deaths a year); the ratio is high but
  below 1.
- **Patients treated (model: detection rate x incidence) vs WHO notifications 2024**: median 1.00, none flagged (the
  WDI detection rate is notifications / incidence, so this confirms the inputs line up).
- **Blended full cost per patient (DS and DR weighted by patients, 2023 US$, after the 1.818 above-site markup) vs
  the WHO 2025 programme budget per notified patient**: median 0.47; flagged below 0.5 in 33 countries (Kenya 0.20,
  Nigeria 0.28, Zambia 0.33, Malawi 0.31, Ethiopia 0.50, Indonesia 0.47, Bangladesh 0.31; Timor-Leste 0.00 and Jordan
  0.08 because their budgets per patient are US$58,000 and US$16,000), above 2 in 6 (Madagascar 8.2, Venezuela 7.7,
  South Sudan 7.4, Fiji 4.3, Guinea 3.4, Pakistan 2.6); ok in India 1.03, Mozambique 1.41, South Africa 0.78, Uganda
  0.79. Likely explanation: the model's cost is the provider cost of a treatment course plus the above-site markup
  (what a lost dollar of treatment money pays for per patient), while a national programme budget also funds
  laboratories, staff, surveillance, TB/HIV, preventive treatment and drug-resistant management for the whole
  country (and is a budget, not spending), so budget per notified patient is 2-5 times the course cost in most
  countries; where it is below the course cost (Madagascar US$62, South Sudan US$71, Pakistan US$112 per patient)
  the WHO budget is incomplete or externally funded off-budget. Not used to change the cost (Batch 4b item 4 reached
  the same reading).

## 3. Malaria

Benchmark: WHO World Malaria Report 2025 estimated deaths for 2024 (GHO `MALARIA_EST_DEATHS`, the file the model
uses for D0). Excess malaria deaths a year (2026-30 / 5) as a share of current deaths: 46 countries, median 0.060,
maximum **Zambia 0.28**, then Rwanda 0.27, Senegal 0.23, Kenya 0.22, Liberia 0.21, Tanzania 0.20; none above 0.5, none
flagged. Nigeria 0.055, DR Congo 0.09, Niger 0.17, Mozambique 0.11, Uganda 0.17.

**The malaria total across the batches** (Full US Exit, all countries, 2026-30): before Batch 3+4 369,425; after
Batch 3+4 143,889 (-61%: systems money not converted, unspecified money by purpose, and the GHED all-source cap);
after Batch 4b 190,824 (+33%: public-spending share for nets and spraying); after Batch 5+6 item A3 **276,952** (+45%:
each intervention's own donor share), 25% below the pre-Batch-3+4 figure. The remaining difference is the money that
no longer buys people (systems and programme management, 14% + 15% of unspecified malaria money) and the cap where
donor money exceeds the full cost of current coverage (9 bednet and 14 treatment lines).

## 4. Vaccines: deaths averted per 1,000 fully immunized children vs Toor et al. 2021 Table 3

The model's country-antigen values (item V1, after the 0.1-10x gate) against Toor's deaths averted per 1,000 FVPs
(all 112 countries, 2000-2030, routine and campaign doses):

| Antigen | Model countries using it | Model median per 1,000 | Toor Table 3 per 1,000 FVPs | Ratio (median) | Countries above 2x | below 0.5x |
|---|---|---|---|---|---|---|
| Measles | 66 | 12.8 | 6.5 | 1.97 | 32 | 2 |
| HepB | 66 | 5.7 | 7.7 | 0.74 | 2 | 17 |
| Hib | 66 | 1.7 | 2.4 | 0.71 | 2 | 25 |
| PCV | 55 | 1.6 | 2.3 | 0.71 | 2 | 20 |
| Rota | 43 | 0.52 | 0.8 | 0.65 | 3 | 14 |
| Rubella | 49 | 0.44 | 0.3 | 1.46 | 9 | 0 |
| YF | 19 | 4.8 | 2.1 | 2.26 | 13 | 4 |
| MenA | 6 | 1.6 | 1.0 | 1.60 | 0 | 0 |

Likely explanations: measles and yellow fever above 2x in 32 and 13 countries because Toor's denominator counts every
dose (MCV1, MCV2 and campaign doses) as an FVP while the model divides by children receiving MCV1 or YFV, so a per-child
value about twice the per-dose value is expected (Toor et al. 2021: most of the measles benefit is from routine
MCV1); the high-burden African countries sit at the top. HepB, Hib, PCV and rotavirus below 0.5x in 14-25 countries
because the comparison countries are lower-mortality (Latin America, Asia, Eastern Mediterranean) and the values
carry the 2026-30 Q5 adjustment (0.6-0.85), while Toor's figure averages 2000-2030 over all 112 countries. Both are
scope differences, not errors; the 0.1-10x gate already replaced the 38 extreme values with regional medians.
Births-weighted across the dashboard countries, the model's lifetime deaths averted per fully immunized child is
shown on the Methods and Validation pages against Gavi's 0.017 (20.6M deaths averted / 1.2B children); it excludes
DTP, polio and BCG.

## 5. Context only: published estimates of deaths from aid cuts

Compared directly only where the scope matches; otherwise the difference is stated.

| Study | Donors | Countries | Years | Diseases / causes | Published | Comparison |
|---|---|---|---|---|---|---|
| Cavalcanti et al. 2025, *Lancet* | USAID (all US foreign assistance through USAID) | 133 LMICs | 2025-2030 (defunding scenario) | all causes, all USAID sectors (health, nutrition, water, humanitarian) | more than 14M additional deaths by 2030, 4.5M of them children under 5 | Not directly comparable: all causes and all sectors vs the model's four diseases and health aid only; the model's Full US Exit gives 1.93M deaths over 2026-30 in 70 countries, as expected far below |
| Cavalcanti et al. 2025 (retrospective) | USAID | 133 LMICs | 2001-2021 | HIV 25.5M, malaria 8.0M, TB 4.7M deaths averted (about 1.21M, 0.38M, 0.22M a year) | | Deaths averted per year by past programmes vs the model's extra deaths a year (HIV 0.20M, malaria 0.055M, TB 0.093M); different question (what aid did vs what losing it does), shown on the Validation page |
| UNAIDS 2025 (Goals model) | PEPFAR ending | all PEPFAR countries | 2025-2029 | AIDS deaths | more than 4M additional AIDS deaths; 6.6M new infections | Scope overlaps partly: PEPFAR only, all its countries; the model's Full US Exit HIV deaths 2026-30 are 1.0M in 70 countries (71.5% of country-coded HIV aid), infections 4.0M |
| ten Brink et al. 2025, *Lancet HIV* (Optima) | 24% cut by the five largest donors, plus PEPFAR discontinued | 26 modelled countries, extrapolated to all LMICs (Table C3) | 2025-2030 | HIV deaths and infections | 0.77M-2.93M additional HIV deaths, 4.4M-10.8M infections (all LMICs) | Country-level comparison above for the 15 overlapping countries (ratio 0.39 deaths, 0.36 infections) |

## 6. UNAIDS year used for each country's HIV transmission rate

`art_transmission_rate` = new infections / (PLHIV - people with suppressed viral load), UNAIDS AIDSinfo 2026 estimates,
latest year with all three values: **2025** for 64 of the 70 countries; 2024 for Jamaica, Kyrgyzstan and Pakistan;
2022 for DR Congo; 2019 for Fiji and South Sudan. 14 countries have no suppression estimate and use their WHO-region
median: Angola, Central African Republic, Côte d'Ivoire, Guatemala, Iraq, Jordan, Madagascar, Mali, Mongolia,
Nicaragua, Papua New Guinea, Senegal, Somalia, Venezuela.
