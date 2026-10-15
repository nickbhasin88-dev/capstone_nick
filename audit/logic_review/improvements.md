# Part 9: Model improvements

**Ranked:** by value for a WHO-facing presentation, which combines the effect on headline numbers, defensibility and
effort.

**Each improvement gives:**
- what it addresses (finding IDs and the `sensitivity.csv` swing);
- the evidence or data behind it;
- effort and the risk of breaking existing results;
- the expected effect;
- priority: **Do now**, **Do before presenting** or **Nice to have**.

Nothing here has been implemented.

## Ranked list

### IMP-01. Resolve the ART and HIV-infection concept, and show both readings (Do now)

- **Addresses:** L-01 and L-41, both Critical. `art_hazard_mult` has the largest swing (-18.6% / +23.3%).
- **What to do:** choose one population and calibrate to it.
  - **Reading A:** keep full-cost equivalents; use a 5-year mortality among people who actually stop ART.
    - Brinkhof 2009, *PLoS ONE*: "The combined mortality was 40%"; 20-60% among traced patients.
    - Recalibrate transmission per person off ART (Partners PrEP: about 2.2-8.8 per 100 person-years).
  - **Reading B:** affected people = patients at donor-supported sites (PEPFAR TX_CURR by country, DR-01), each with
    the calibrated 17% and 0.04.
- **Show:** both, as a structural range on the HIV card and in the headline footnote.
- **Fix the source text:** `model_params.csv` rows `art_hazard_mult` and `art_transmission`.
- **Effort:** small for A (parameter values plus text); medium for B (new input, one formula). **Risk:** low; tests
  that pin the HIV numbers will need updating.
- **Expected effect** (tested by arithmetic on model output, `URGENT.md`; extra run: hazard rescaled to 20/40/60%):

| Reading | Deaths 2026-30 | Change | HIV infections |
|---|---|---|---|
| A, 40% risk | 3.17M | +61% | about 1.6M → about 3M+ |
| A, 20% / 60% | | +7% / +115% | |
| B | about 4.5M | about +130% | about 3.7M+ |

  Both readings bring HIV in line with Optima's PEPFAR-ending scenario (about 2.9M) and UNAIDS (more than 4M).
- **Data:** none for A; DR-01 for B.

### IMP-02. Fix the money-to-services conversion: spread unspecified money over services and systems, and remove the double count of above-site costs (Do before presenting)

**Status: ◐ partly done (Batch 3+4, 14 October 2026).** (b) one treatment of above-site costs: done, option (ii)
(item 1, L-05: systems money not converted, `hss_service_share` = 0, commit `4f9f0c0`). (a) unspecified money
spread by purpose: done through item 2 (L-43, Global Fund module shares). (c) testing-and-care as a flow of initiations: **BLOCKED** (no cost
per initiation; the flow formulation triples the count rather than lowering it; `batch34_evidence.md` C).

- **Addresses:** L-43, L-05, L-27. `hss_kappa` swing -10.1% / +16.2%; `asd_share` +17.8% / -12.2%.
- **What to do:**
  - Spread `*_unspec` money in proportion to all known lines, including HSS. Today it goes to services only: TB
    US$700M of US$1,522M (46%) is treated as patients.
  - Then choose one of:
    - (i) site-level unit costs plus kappa x HSS money; or
    - (ii) fully loaded costs (1/(1-asd)) with no HSS-to-services conversion.
  - Model testing-and-care money as lost new initiations (a flow), not a stock of people losing ART.
- **Evidence:**
  - IHME DAH codebook (program areas; `_other` = unallocated);
  - KFF 2025 on PEPFAR non-service-delivery spending (47%);
  - red-team review point 3, which measured kappa = 0 at -20% of deaths and asd = 0 at +46%.
- **Effort:** medium. **Risk:** medium. It moves every country's numbers, so update `logic.md` and the tests.
- **Expected effect:** about -5% to -15% of the headline (Low confidence; depends on the choice). TB falls most.
- **Data:** none.

### IMP-03. Country-specific unit costs (Do before presenting)

**Status: ✅ done for ART (Batch 3+4 item 4, 14 October 2026; GHCC UCSR + Rosen 2021, 7 countries with their own
value, the rest regional or income-group medians) and for TB (item 5; Value TB and GHCC course costs with WHO RR-TB
shares). PEPFAR Expenditure Analysis per patient (DR-01) was not available. `batch34_evidence.md` D and E.**

- **Addresses:** `uc_art_mult` (-10.6% / +14.5%), `uc_tb_mult` (-8.1% / +11.7%), `uc_scale_elast`, L-16, L-26.
- **What to do:**
  - Replace the ART default formula (used in 65 countries) and the TB income-group means with country estimates.
  - Sources: GHCC Unit Cost Study Repository; PEPFAR Expenditure Analysis per patient; Sweeney et al. 2024 (TB: India
    US$450, Philippines US$560, South Africa US$730 per person treated); WHO-CHOICE.
  - DR-TB: Global Drug Facility BPaLM price (US$284 per course) plus delivery costs.
- **Effort:** medium (data assembly). **Risk:** low.
- **Expected effect:** ±5-10% by country. India, Philippines and South Africa TB costs fall 30% vs the model's
  US$638, so more TB patients are affected there. Global net effect small and uncertain.
- **Data:** DR-08, DR-01.

### IMP-04. Cap the donor-funded share of covered people (Do before presenting)

**Status: ✅ done (Batch 3+4 item 6, 14 October 2026; shares revised in Batch 4b item 3 and Batch 5+6 items A2-A3).**
External shares from WHO GHED disease accounts (HIV, malaria, immunization) and WHO TB financing; `batch34_evidence.md`
F. Batch 4b: bednets and spraying use the external share of public malaria spending. Batch 5+6: HIV and immunization
use the external share of public spending (A2, L-51); the three malaria lines use an intervention-specific share, the
people the donor money for that intervention pays for as a share of the people covered (A3); `batch56_evidence.md`.

- **Addresses:** L-44 (red-team point 9). The proportional-cap rule treats all covered people as donor-funded in 160
  of 695 country-service lines; Tajikistan's extra TB deaths reach 108% of current TB deaths.
- **What to do:** in the branch where donor money ÷ cost exceeds people covered, cap the donor-funded pool at an
  external donor share, from GHED disease accounts (DR-04), WHO TB financing (DR-02) or PEPFAR/Global Fund commodity
  shares.
- **Effort:** small to medium. **Risk:** low.
- **Expected effect:** -3% to -5% of deaths (reviewer's estimate 50-100K; not run).
- **Data:** DR-04, DR-02.

### IMP-05. Malaria: apply Lives Saved Tool effects to under-5 deaths, and use the LiST treatment effect for uncomplicated cases (Do now)

**Status: ✅ done (c6dd075, 14 October 2026).**

- **Addresses:** L-04 (-4.9%, tested) and L-20 (`mal_cm_eff` at 0.99 gives +4.1%).
- **Evidence:**
  - Eisele 2010 and Thwing 2011 (children 1-59 months).
  - WMR 2025: 75% of African Region malaria deaths are under-5.
  - For adults, use a conservative fraction of the child effect, or 0. No published adult LiST effect was found
    (UNVERIFIED).
- **Effort:** small. **Risk:** low.
- **Expected effect:** about -5%, partly offset by +4% if Ec becomes 0.99. Net about -1% to -5%.
- **Data:** none. WHO/MCEE child malaria deaths are already in `ext_data/sg`.

### IMP-06. A 2025 baseline option (Do before presenting)

- **Addresses:** L-06 (baseline years; timing of 2025 cuts).
- **What to do:**
  - Rebuild baseline aid per country for 2025 from ForeignAssistance.gov (US), Global Fund disbursements, Gavi
    country disbursements and IHME 2025 global ratios for other donors.
  - Offer "remaining cut from 2025" as an option.
  - Alternatively, start scenarios in 2025 so people who lost ART in 2025 have the right hazard year.
- **Effort:** large. **Risk:** medium.
- **Expected effect:** Aid at Risk for US scenarios falls by tens of percent. Deaths relative to 2025 service levels
  fall similarly. Deaths relative to 2021-23 levels rise if 2025 is counted.
- **Data:** DR-03.

### IMP-07. Channel-specific above-site share (Nice to have)

- **Addresses:** `asd_share` concept (`assumptions.md`).
- **What to do:** PEPFAR's implementing-partner model carries about 45-47% above-site costs; Global Fund grants and
  government channels carry less. Use asd by channel.
- **Effort:** small. **Risk:** low.
- **Expected effect:** more people losing services where Global Fund money dominates (+ a few %).
- **Data:** Global Fund budget data (DR-03b), program management share UNVERIFIED.

### IMP-08. MOU preset with co-financing, in real terms (Do before presenting, if MOUs are shown)

- **Addresses:** L-08, L-35.
- **What to do:** load each MOU's co-financing schedule as the default government response, with a compliance slider.
  Deflate nominal MOU amounts to 2023 US$.
- **Effort:** medium (data entry). **Risk:** low.
- **Expected effect:** MOU preset deaths (360K) fall substantially. Kenya's pledge (US$850M over 5 years, reported by
  *The EastAfrican*, UNVERIFIED) exceeds its MOU-implied loss. Deflation raises the real cut by about 2-3% a year.
- **Data:** DR-12.

### IMP-09. Better uncertainty: correlated draws, and structural alternatives in the range (Do before presenting)

- **Addresses:** L-02.
- **What to do:**
  - Draw `asd_share`, `uc_art_mult` and `uc_tb_mult` from one shared "cost" factor, and `art_hazard_mult` and
    `art_transmission` from one shared "severity" factor.
  - Add a structural switch (ART readings A/B; kappa on/off) whose results are shown alongside, not mixed into, the
    parameter range.
  - Add data uncertainty for PLHIV and malaria cases from UNAIDS and MAP bounds.
- **Effort:** medium. **Risk:** low.
- **Expected effect:** wider ranges. Correlated cost draws alone widen the range by a few percent.

### IMP-10. All-country range from summed draws, and honest range labels (Do now)

**Status: ✅ done (581c013, 14 October 2026).**

- **Addresses:** L-02.
- **What to do:**
  - Store per-draw totals in the precomputed files and take the percentile of the sum. Measured: 1.39-2.70M vs the
    displayed 1.34-2.81M.
  - Replace "95% interval" with "range across parameter values (excludes data and model-structure uncertainty)".
- **Effort:** small. **Risk:** low (precomputed files change).

### IMP-11. TB timing and inputs (Do before presenting)

**Status: ◐ partly done (Batch 3+4 item 5, 14 October 2026).** Country MDR/RR-TB shares and enrolment (WHO 2024)
and country treatment costs (Value TB, GHCC) are in; the WHO Table 5 blend was done earlier (L-13). Not done: spreading
the untreated case fatality over about 3 years and secondary cases over 2-5 years (L-15; timing was outside the
batch's scope, which was treatment costs). `batch34_evidence.md` E.

- **Addresses:** L-13, L-15, L-16, `DR_TB_SHARE`, `DR_TB_COV`, `tb_secondary` timing.
- **What to do:**
  - Spread each untreated cohort's case fatality over about 3 years (WHO: "mean duration of untreated disease ...
    about three years").
  - Spread secondary cases over 2-5 years.
  - Use the WHO Table 5 blend 0.78(1-a) + 0.49a.
  - Use country MDR/RR-TB shares and enrolment.
- **Effort:** small to medium. **Risk:** low.
- **Expected effect:** 2026-30 TB deaths fall a few % (moved to 2031-35); the HIV+ CFR change adds under +1%.
- **Data:** DR-02.

### IMP-12. Reproducibility: pin data vintages, and make Sections 1-3 rebuildable (Do before presenting)

- **Addresses:** L-38, the WDI mirror lag, WEO re-download.
- **What to do:**
  - Archive the exact downloaded series with dates (a `datasets/manifest.csv` with URL, date and checksum).
  - Download WDI from the World Bank API, not the open-numbers mirror.
  - Restore or rewrite the scripts that built `country_data/`, `spending_data/`, `revenue_data/` and `cofog_all/`.
- **Effort:** medium. **Risk:** none for results.

### IMP-13. Country-level Global Fund GC8 vs GC7 allocations for the Global Fund & Gavi preset (Do before presenting)

- **Addresses:** L-09, and the uniform 20% channel cut.
- **What to do:** the cut per country = 1 - GC8 allocation / GC7 allocation by component. Published by the Global
  Fund in 2026 allocation letters (UNVERIFIED that all are public).
- **Effort:** small. **Risk:** low.
- **Expected effect:** redistributes the 683K deaths across countries; the total may change ±20% (Low).
- **Data:** DR-03b.

### IMP-14. Rename and add presets (Do now)

**Status: ✅ done (752f611 (labels only; no new preset), 14 October 2026).**

- **Addresses:** L-45, L-46, L-28.
- **What to do:**
  - Rename "Full US exit" to "US bilateral exit + multilateral withdrawals".
  - Drop "data-driven" from the IHME preset's country description.
  - Rename OECD to "Total-ODA cuts applied to health aid".
  - Add a "Current US policy" preset: MOU schedules where signed, PEPFAR bridge funding elsewhere, Gavi exit, Global
    Fund at the pledged US$4.6B.
- **Effort:** small (labels); medium (new preset). **Risk:** low.

### IMP-15. Vaccine pathway by antigen (Nice to have)

**Status: ◐ partly done (Batch 5+6 items V1-V2, 14 October 2026).** Deaths averted per fully immunized child are now
VIMC values by country, summed over the antigens the country uses, with VIMC timing by years since vaccination
(`batch56_evidence.md` V1-V3). Not done: a cost per child by antigen (Gavi country financial data) and WUENIC coverage
per antigen as the unit; the unit is still a full-schedule child at `uc_imm`; DTP, polio and BCG remain excluded.

- **Addresses:** L-18, L-19, L-42.
- **What to do:**
  - Donor (Gavi) money buys specific vaccines. Use Gavi country financial data (on disk) for price per child by
    antigen.
  - Use VIMC or Toor 2021 deaths averted per vaccinated child by country and antigen.
  - Coverage from WUENIC per antigen.
- **Effort:** large. **Risk:** medium.
- **Expected effect:** vaccine deaths likely rise (Gavi's own claim is about 10x the model's 117K; partly scope).
- **Data:** DR-05, DR-09.

### IMP-16. Country-specific continuity (Do before presenting)

**Status: ◐ partly done (Batch 3+4 item 7, 14 October 2026).** The 2025 evidence (KFF FY2025 Q4; Cust & Chabata 2026;
WHO Global TB Report 2025) was reviewed and quoted; none measures the share of patients who keep the same service after
its funding is withdrawn, so `continuity` stays 0.15 (range 0-0.30) with 0.30 as a sensitivity value. Country TB
continuity needs the private-sector notification share, which the 2026 WHO file does not carry; PEPFAR TX_ML (DR-07)
was not available. `batch34_evidence.md` G.

- **Addresses:** L-14. Continuity has the second-largest swing (+18.0% / -23.8%).
- **What to do:**
  - TB: continuity = private-sector share of notifications (WHO), plus public capacity.
  - HIV: calibrate to PEPFAR FY2025 TX_CURR and TX_ML changes after the 2025 cuts. The ART count was "stable
    compared to Quarter 4 of FY 2024" (KFF), which suggests high short-run continuity.
- **Effort:** medium. **Risk:** medium.
- **Expected effect:** down for India, Indonesia, Pakistan and Nigeria TB; HIV unclear.
- **Data:** DR-02, DR-07.

### IMP-17. Project need 2026-2030 (Nice to have)

- **Addresses:** L-24.
- **What to do:** births and population from WPP 2024 projections; PLHIV from UNAIDS trends.
- **Effort:** small. **Risk:** low.
- **Expected effect:** +2% to +5% where need grows; matters only where caps bind.
- **Data:** DR-10, DR-06.

### IMP-18. Malaria trend from WHO death series (Do now)

**Status: ✅ done (719ff89, 14 October 2026).**

- **Addresses:** L-25.
- **What to do:** use `MALARIA_EST_DEATHS` 2015-2024 (already in `ext_data/gho`) for the death trend instead of the Pf
  case trend clipped at ±5%. Also keep `mal_resurgence` as a separate, labelled assumption.
- **Effort:** small. **Risk:** low.
- **Expected effect:** under ±1%.

### IMP-19. Validation page: like-for-like benchmarks with stated acceptance bands (Do before presenting)

**Status: ✅ done (Batch 5+6 item VAL1, 14 October 2026).** `audit/logic_review/validation.md` and the Validation
section of the Methods page: acceptance band 0.5-2x stated first; HIV vs Optima Table C2 by country; people on ART vs
UNAIDS; TB vs WHO deaths, notifications and budgets; malaria vs WMR 2025 deaths; vaccines vs Toor Table 3; context
studies with their scopes. `hiv_deaths_est` (L-11) is still used by the Lancet rate-ratio method on the Validation page.

- **Addresses:** L-47, L-11.
- **What to do:**
  - Compare Full US Exit HIV with Optima scenario 5 (PEPFAR ends; about 2.9M) and with UNAIDS.
  - Add TB (Clark 2025; Mandal 2025), malaria (MAP/PMI) and South Africa (Thembisa; CEPAC).
  - Replace `hiv_deaths_est` with UNAIDS AIDS deaths 2025.
  - Drop the circular Gavi row, or label it "calibration check".
  - State, before showing results, what range counts as agreement (e.g. within a factor of 2).
- **Effort:** small. **Risk:** none.
- **Data:** DR-06.

### IMP-20. One complete, current specification (Do now)

**Status: ✅ done (cff29af, 14 October 2026).**

- **Addresses:** L-36 (METHOD.md contradicts the code on ART units), L-37 (`logic.md` needed 12 items from
  METHOD.md).
- **What to do:** merge into one spec, keep it beside the code, and test it with the independent reproduction (this
  review's harness).
- **Effort:** small. **Risk:** none.

### IMP-21. Claims wording (Do now)

**Status: ✅ done (576a8d8, 14 October 2026).**

- **Addresses:** L-48, L-02, L-40, L-30 and claims C1, C4, C5, C9, C17 (`dashboard.md`).
- **Effort:** small. **Risk:** none.

### IMP-22. Comparison with established models (Nice to have)

- **What to do:** run Spectrum/AIM (HIV, via the country files UNAIDS distributes to national teams), TIME (TB) or the
  OneHealth Tool for 2-3 countries (Kenya, Mozambique, Nigeria) under Full US Exit, as an external check of the
  country numbers.
- **Effort:** large. **Risk:** none.

### IMP-23. Add the main missing recipients (Nice to have)

- **Addresses:** L-03.
- **What to do:** add Myanmar, Sudan, Afghanistan, Chad, Yemen and Ukraine. They are in the 98-country build list
  except Chad, whose data are available from the same sources.
- **Effort:** medium (Sections 1-3 data). **Risk:** low.
- **Expected effect:** the all-country total rises; about +US$0.69B/yr aid at risk at most.

### IMP-24. Direct downloads from WUENIC and UNAIDS (Nice to have)

**Status: ✅ done for the model inputs (Batch 7 items 3-4, 15 October 2026).** `immunization_inputs.py` and `unaids_inputs.py` read the files on disk; GHO and the WDI mirror remain as fallbacks and for adult prevalence and the committed regressions (`batch7_evidence.md`).

- **Addresses:** L-17, L-11. **Effort:** small. **Data:** DR-05, DR-06.

## The 10 most valuable, in order

| Rank | ID | Why |
|---|---|---|
| 1 | IMP-01 | ART concept: Critical; changes the headline by +7% to +130% |
| 2 | IMP-02 | Unspecified and systems money: Major; likely -5% to -15%, mostly TB |
| 3 | IMP-10 + IMP-21 | Honest ranges and claims: cheap; fixes the most visible overclaims |
| 4 | IMP-04 | Donor-funded cap: removes impossible country results (Tajikistan) |
| 5 | IMP-05 | Malaria under-5 effects: -5%, small effort |
| 6 | IMP-19 | Like-for-like validation: what a WHO reviewer reads first |
| 7 | IMP-06 | 2025 baseline: the biggest data improvement for "aid at risk" |
| 8 | IMP-16 | Country continuity: second-largest sensitivity |
| 9 | IMP-03 | Country unit costs: third- to sixth-largest sensitivities |
| 10 | IMP-08 | MOU co-financing: fixes the MOU preset's central premise |

## Recommended sequence

1. **First (no data needed, small effort):**
   - IMP-20: one spec, so later changes can be checked.
   - IMP-10 and IMP-21: labels and claims.
   - IMP-14: preset names.
   - IMP-05: malaria under-5.
   - IMP-18: malaria trend.
   - IMP-01 reading A: parameter values.
   - Then re-run `audit/checks.py --full` and the independent reproduction.
2. **Second:** IMP-02 (money conversion). It changes the base every later improvement builds on, so do it before
   unit costs and caps.
3. **Third, after downloading DR-01, DR-02, DR-04 and DR-08:**
   - IMP-01 reading B;
   - IMP-04 (cap; depends on IMP-02's money allocation);
   - IMP-03 (unit costs);
   - IMP-11 (TB);
   - IMP-16 (continuity).
4. **Fourth:** IMP-19 (validation), done after the model changes so the comparisons show the final model.
5. **Fifth, after DR-03 and DR-12:** IMP-06 (2025 baseline), IMP-08 (MOU co-financing), IMP-13 (Global Fund
   allocations).
6. **Later:** IMP-09, IMP-12, IMP-15, IMP-17, IMP-22, IMP-23, IMP-24.

**Dependencies:**
- IMP-04 depends on IMP-02.
- IMP-09's structural range depends on IMP-01.
- IMP-19 should come after IMP-01, IMP-02 and IMP-04.
- IMP-06 changes the base for every scenario, so the precomputed files and the snapshot baseline must be regenerated
  afterwards.
