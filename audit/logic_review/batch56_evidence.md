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
