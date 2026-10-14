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
