# Batch 7: closing the small open items (15 October 2026)

Branch `tomato`. Rules: one commit per item; the headline (all countries, Full US Exit, central, deaths 2026-2030)
and the per-disease totals are recorded after every commit; any item that moves the headline by more than 0.5% is
reported with before and after values; tests run after every commit; new constants carry a central value, a range, a
source line and a "labelled assumption" tag where no source measures them; nothing is downloaded. Starting point
(commit `95cc16a`): **1,927,405** (HIV 998,535; TB 463,973; malaria 276,952; vaccines 187,945; HIV infections
3,966,261; further deaths 2031-35 990,588).

## Item 1. L-43 status reconciled: done, with a stated gap

The split of unspecified aid by purpose was implemented in Batch 3+4 item 2 (`2a792f7`): the country's Global Fund
Grant Cycle 7 module shares send the treatment share to treatment lines, the prevention share to prevention lines,
the testing share to testing and care, the systems share to systems money and the programme-management share to
non-service money (`docs/SPEC.md` section 3). What remains is a stated gap, not an open mechanism:

- **34 of 210 country-disease lines use a WHO-region median** instead of the country's own grant (the findings table
  said 38; the current `batch34_gf_shares.csv` has 34 for the 70 modelled countries): HIV Fiji, Iraq, Jordan, Libya,
  Rwanda; TB Belize, Dominican Republic, Fiji, Guyana, Iraq, Jamaica, Jordan, Libya, Mauritius, Rwanda, El Salvador;
  malaria Belize, Botswana, Dominican Republic, Egypt, Fiji, Iraq, Jamaica, Jordan, Cambodia, Laos, Libya, Lesotho,
  Mongolia, Mauritius, Rwanda, El Salvador, Viet Nam, South Africa. These are countries without a Global Fund grant
  for that disease; their unspecified money is small.
- **The Tajikistan-type cases** (donor money would buy more than the donor-funded pool, so units lost are the pool
  times the share of money lost; `donor_exceeds_cost`) under Full US Exit at the central run: TB treatment in
  Azerbaijan, Burundi, Benin, Burkina Faso, Belize, Botswana, Côte d'Ivoire, Cameroon, Djibouti, Dominican Republic,
  Egypt, Ghana, Gambia, Guatemala, Honduras, Haiti, Jamaica, Jordan, Kyrgyzstan, Cambodia, Laos, Lesotho, Moldova,
  Mali, Mongolia, Mauritius, Malawi, Nicaragua, Rwanda, Senegal, El Salvador, São Tomé and Príncipe, Eswatini, Togo,
  Tajikistan, Timor-Leste, South Africa, Zambia, Zimbabwe (39); drug-resistant TB in 41 countries; HIV treatment in
  30; malaria treatment in 31. The cap now holds every one of these below the people covered (the Validation page
  counts them), and the largest TB excess as a share of current TB deaths is Mozambique at 0.79 (validation.md),
  against the 1.08 Tajikistan showed before the cap.

**Status in both places:** done, with stated gap (34 of 210 lines on regional medians; capped cases listed above).
No model change; no headline change.

## Item 2. Headline chain re-run at each boundary commit

Each boundary commit was checked out in its own worktree and re-run with its own code and input files (central run,
Full US Exit, no response, sudden; `audit/.../chain_check.py`), and compared with the precomputed file committed at
that point. Every fresh run matched its own precomputed file exactly.

| Boundary | Commit | Recorded in the changelog header | Re-run | HIV | TB | Malaria | Vaccines |
|---|---|---|---|---|---|---|---|
| Before Batch 1 (logic review read-only) | `2cfcb14` | 2,017,000 (rounded) | **1,969,304** | 1,006,114 | 460,067 | 385,713 | 117,411 |
| After Batch 1 | `91d48fa` | 2,055,422 (wrong: that is the post-Batch-2 value) | **1,945,605** | 1,006,114 | 472,436 | 349,644 | 117,411 |
| After the malaria under-5 share | `c0d7587` | (not stated separately) | **1,965,386** | 1,006,114 | 472,436 | 369,425 | 117,411 |
| After Batch 2 | `cd42746` | 2,055,422 ("not changed by it") | 2,055,422 (**changed by it: HIV 1,006,114 -> 1,096,151**) | 1,096,151 | 472,436 | 369,425 | 117,411 |
| After Batch 3+4 | `c1b0846` | 1,379,963 | 1,379,963 | 669,366 | 463,973 | 143,889 | 102,735 |
| After Batch 4b | `d62a15d` | 1,695,601 | 1,695,601 | 938,069 | 463,973 | 190,824 | 102,735 |
| After Batch 5+6 | `26d6cd4` | 1,927,405 | 1,927,405 | 998,535 | 463,973 | 276,952 | 187,945 |

Corrections made to the changelog header: the starting value is 1,969,304, not "2,017,000 (rounded)" (the rounded
figure had been taken from the Batch 1 before/after table's pre-cleanup baseline); Batch 1 moved the headline to
1,945,605 (malaria -9%, TB +3%), the under-5 share to 1,965,386, and Batch 2 to 2,055,422 (HIV +9%), which the
header had wrongly described as unchanged by Batch 2. The Batch 3+4, 4b and 5+6 values reproduce.

## Item 3. L-17: DTP3 coverage from WUENIC 2025

`immunization_inputs.py` reads `datasets/WUENIC_2025.xlsx` (sheet `country`) and writes `sh_imm_idpt` (DTP3) and
`sh_imm_meas` (MCV1) with `_year` and `_source`; `prepare_model.py` calls it after `who_inputs.apply()`. Every one of
the 70 countries has a 2025 value (the WDI mirror was 2024, Nicaragua 2023). Countries where the two differ by more
than 2 points (WDI -> WUENIC 2025): Angola 64 -> 52, Venezuela 62 -> 50, Tajikistan 97 -> 86, South Africa 74 -> 65,
Côte d'Ivoire 77 -> 70, Iraq 90 -> 84, Bangladesh 97 -> 92, Belize 88 -> 83, Nigeria 67 -> 62, Guatemala 81 -> 77,
Jamaica 99 -> 95, Moldova 86 -> 82, Kenya 91 -> 88, Kyrgyzstan 85 -> 82, Rwanda 98 -> 95; and upward: Honduras 75 ->
86, Ethiopia 73 -> 81, Namibia 74 -> 82, Nicaragua 89 -> 96, Benin 63 -> 69, Cameroon 77 -> 83, Djibouti 77 -> 83,
Uganda 91 -> 97, Central African Republic 42 -> 46, Ghana 95 -> 99, Indonesia 78 -> 82, Libya 86 -> 90, Madagascar 60
-> 64, Mauritius 93 -> 96, El Salvador 95 -> 99 (30 countries; median absolute change 2 points). Part of the
difference is the year (2025 vs 2024) and part is the mirror's rounding and vintage: 13 countries differ from WUENIC's
own 2024 value as well.

Effect: immunization baseline refreshed (22 entries, `imm` only); headline **1,927,405 -> 1,927,871 (+0.02%)**;
vaccine deaths 187,945 -> 188,412; no other disease moved. 357 tests pass.

## Item 4. IMP-24: the UNAIDS and WUENIC files as the direct sources

**Immunization.** Item 3 made WUENIC the source of DTP3 and MCV1 in `country_inputs.csv`; this item also feeds the
coverage regression's DTP3 history from WUENIC (`immunization_inputs.wuenic_series`, 8,340 country-years 1980-2025)
and removes `sh_imm_idpt` and `sh_imm_meas` from the WDI download list. The committed `regressions.json` was built
with the mirror series and changes only at the next full `prepare_model.py` rebuild (Validation page only).

**HIV.** `unaids_inputs.py` reads the UNAIDS 2026 file (Area Level 2, latest year, 2025) for every HIV input the
model uses: people living with HIV (66 of 71 countries; new / old ratio median 1.000, none outside 0.9-1.1, the GHO
values were the same estimates), ART coverage (66; 1.001), PMTCT coverage (69; 2 countries outside 0.9-1.1),
HIV-positive pregnancies = women needing ARV for PMTCT (69; 14 outside 0.9-1.1, because the GHO-derived value divided
women on ARVs by rounded coverage), new HIV infections (64; median ratio 0.936, 43 outside 0.9-1.1: UNAIDS 2025
estimates against the WDI mirror's 2024 vintage), and AIDS-related deaths (65, a new column `hiv_deaths_unaids` for
item 5). Countries without a UNAIDS value keep the GHO or derived value and its source label (Côte d'Ivoire,
Guatemala, Iraq, Jordan, Nicaragua for PLHIV and ART; Venezuela and Libya for infections).

**Still from the World Bank mirror:** adult HIV prevalence (`sh_dyn_aids_zs`), used only in the pregnancy fallback for
countries without a UNAIDS value and in the regression panel. Not BLOCKED (the UNAIDS file has prevalence), simply
out of the model's path; left as is.

**Effect.** HIV and TB baselines refreshed (74 entries: `hiv_art`, `hiv_pmtct`, `hiv_prev`; and `tb_ds` in 54 entries
because ART coverage enters the HIV-positive TB case fatality). Headline **1,927,871 -> 1,927,847 (-0.001%)**; HIV
998,535 -> 998,517; TB 463,973 -> 463,966; HIV infections 3,966,261 -> 3,936,613 (the lower UNAIDS 2025 incidence
raises the cost per infection averted on the prevention line). 357 tests pass.

## Item 5. L-11: UNAIDS AIDS-related deaths for the Lancet rate-ratio method

The UNAIDS 2026 file includes "AIDS-related deaths" (all ages estimate, 2025) for 65 of the 70 countries, written
to `hiv_deaths_unaids` by `unaids_inputs.py` (item 4). `health_model.LANCET_BASELINE` now uses it, with
`hiv_deaths_est` (GBD-2019 HIV share of all deaths x crude death rate x population) as the fallback for Côte
d'Ivoire, Guatemala, Iraq, Jamaica, Jordan and Nicaragua; the Validation page note says which applies. Change in the
Lancet-method HIV row (five-year deaths, Full US Exit): Kenya 221,301 -> 60,943 (baseline deaths 70,569 -> 19,434 a
year); Nigeria 260,631 -> 60,245; Mozambique 72,764 -> 46,230; South Africa 521,748 -> 133,701; Uganda 45,793 ->
43,463; Honduras 163 -> 581. Validation page only; the model's own numbers do not change. 357 tests pass.

## Item 6. L-31: the WEO vintage, labelled

The interest series comes from `datasets/IMF_WEO_Oct2026_GG_balances_2026-10-13.csv`, which `fiscal_inputs.py`
downloaded from the IMF SDMX API on 13 October 2026 (dataflow IMF.RES:WEO) and labels as the October 2026 release; the
source label now reads "net interest (IMF WEO October 2026: primary minus overall balance)" in `country_inputs.csv`,
the fiscal panel ("IMF WEO Oct 2026, 2024") and the Methods page. The per-country GDP, revenue, expenditure and debt
series in `macro_data/<ISO3>.csv` were built by a script that is not in the repository (L-38) and carry no vintage in
their headers; their projection horizon ends in 2031 for all 71 files, which is consistent with the October 2026
release, so they are labelled "vintage not recorded; horizon consistent with October 2026" rather than asserted.
Label only; no value changes.

## Item 7. L-34: one primary interest definition, with a flag for the fallback

Coverage: the IMF WEO net-interest series (October 2026; (primary balance - overall balance) / revenue, general
government, latest actual year) exists for all 70 modelled countries; the World Bank WDI interest-payments series
(`GC.XPN.INTP.RV.ZS`, gross interest paid, central government, 2015-2024) exists for 52. The IMF series is therefore
the primary definition. `fiscal_inputs.apply` now uses it wherever it exists and keeps the World Bank value only where
the IMF one is missing, marking those rows `flag_interest_alt_def = True`; today no country needs the fallback, so the
flag is False everywhere and the mix is gone. Before this item the rule was "the more recent of the two sources", which
had put 17 countries on the World Bank definition without saying so.

How the two definitions differ for the 52 countries with both (IMF minus World Bank, points of revenue): median
+0.2; within plus or minus 2 points in 36 countries; IMF lower in India (-11.1), Zimbabwe (-9.2), Honduras (-7.6),
Jamaica (-5.4), Ethiopia (-4.9), Philippines (-3.5); IMF higher in Egypt (+22.5, World Bank value from 2015),
Senegal (+8.2), Bangladesh and Burundi (+6.7), Kenya (+5.7), Malawi (+5.6), Ghana (+3.7). Net interest is interest
paid minus interest received, so it sits below gross interest where governments hold interest-bearing assets
(India, Zimbabwe), and the World Bank series is central government only, so it sits below net general-government
interest where sub-national or social-security debt matters.

The 17 countries that change value (World Bank -> IMF, % of revenue): Ethiopia 12.6 -> 7.8, Mozambique 15.1 ->
13.3, Uganda 21.0 -> 22.4, Tanzania 13.9 -> 14.2, Angola 25.2 -> 25.6, Kyrgyzstan 2.6 -> 3.4, Botswana 3.4 -> 4.7,
Mauritius 10.4 -> 11.7, El Salvador 14.3 -> 17.1, Guatemala 12.5 -> 13.0, Fiji 13.9 -> 14.6, Lesotho 3.5 -> 2.0,
Madagascar 4.8 -> 4.6, Somalia 0.6 -> 0.6, Tajikistan 2.9 -> 2.8, Togo 14.0 -> 14.0, Central African Republic 4.2 ->
1.9. Only Mozambique's fiscal capacity changed enough to move a locked baseline (13 entries with a government
response refreshed with `make_baseline.py --fiscal`, which checks that no-response entries are unchanged). Headline
unchanged (the default response is none). The test that encoded the old rule is updated in the same commit.

## Item 8. L-35: MOU amounts, nominal by default, with a deflation switch

The MOU schedules divide nominal US$ amounts for 2026-2030 by a nominal 2021-25 reference, so inflation over the period
is not deducted and the real cut is understated. Two parameters appended to `model_params.csv`: `mou_deflate`
(constant switch, default 0 = nominal, as written) and `mou_us_inflation` (0.02, range 0.01-0.04, labelled
assumption). With the switch on, `scenarios.mou_schedule` divides each year's amount by (1 + 0.02)^(year - 2023) and
leaves the reference (a 2021-25 average centred on 2023) unchanged. No forward US inflation projection is on disk:
the IMF file in `datasets/` holds general-government balances for the model countries, and the country US$ GDP
deflators in `macro_data/` (Kenya's implies 1.26 by 2030) are the wrong concept for US-dollar budget amounts, whose
purchasing power follows US inflation. The dashboard caption under the MOU scenario now says the amounts are nominal
and that the switch exists. Kenya's schedule: nominal cuts 0%, 4.5%, 16.1%, 19.8%, 60.3%; deflated at 2%: 4.0%,
11.8%, 24.0%, 28.7%, 65.4%. America First MOUs preset, 16 countries, central: nominal 364,586 deaths; deflated at 2%
416,307 (+14%). Default unchanged; headline unchanged; 357 tests pass (the MOU tests check the default schedules).
