# Part 2: Assumptions and evidence

**Classes:**
- **(a)** supported by evidence;
- **(b)** evidence exists and suggests a different value;
- **(c)** no evidence found after searching (a genuine assumption);
- **(d)** shouldn't be an assumption: data exists.

**Sensitivity.**
- **What it measures:** all-country deaths 2026-2030, Full US Exit, No Government Replacement, death-rate trend on,
  central run. One input moves to its low and then its high value while everything else stays central.
- **Base:** 1,969,304 deaths in 2026-2030 and 494,715 in 2031-2035.
- **Files:** `sensitivity.py` produces `sensitivity.csv`; `tornado.png` charts the 20 largest swings.
- **Extra tests** in this file (the malaria under-5 restriction and the ART risk rescaling) were run with the same
  harness (`sensitivity.py` helpers), changing inputs in memory only.

![tornado](tornado.png)

## Summary by class

| Class | Count | Items |
|---|---|---|
| (a) supported | 15 | tb_cfr_untreated_neg, tb_cfr_treated_neg, tb_cfr_treated_pos, pmtct_vt_reduction, pmtct_infant_mort, hiv_inf_death_untreated, hiv_survival_median, HIV Weibull shape, imm_deaths_per_child_ref, imm_u5_share, mal_vc_eff (value), uc_itn, uc_irs, GF_CUT_DEFAULT 20%, US Global Fund cut 0.23 |
| (b) evidence suggests a different value | 9 | art_hazard_mult (L-01), mal_vc_eff / mal_cm_eff population (L-04), mal_cm_eff value (L-20), tb_cfr_untreated_pos blend (L-13), DR-TB cost (L-16), TB DS cost for country studies (IMP-03), OECD cuts for health (L-28), asd_share citation (L-26: 47% found, not 45%), TB death timing (L-15) |
| (c) genuine assumption | 22 | hss_kappa, continuity, uc_scale_elast, cpia_ref, uc_ovc, tb_dr_dcfr, mal_resurgence, mal_itn_default_use, mal_cm_default_cov, hiv_inf_death_treated, art_reengage, art_transmission year-1 factor, LAG ramps, ART_HAZARD shape, U5MR/50 scaling, debt-stress thresholds, fiscal capacity rule, lives-first order, malaria trend ±5% clip, GAVI_CUT_DEFAULT 15%, MOU rules (increase = 0, flat after 2028), 5-year horizon |
| (d) data exists | 7 | DR_TB_SHARE, DR_TB_COV (WHO country estimates), malaria_at_risk_share fallback, 1.15 female-prevalence factor (UNAIDS pregnant women estimates), continuity for TB (private-sector notification share), malaria death trend (WHO death series), aid baseline year (IHME 2024 actuals) |

## Each assumption

Values are central (low-high). "Swing" is deaths 2026-30 at the low and high values, as % change from the base.

### HIV

**art_hazard_mult**: 1 (0.6-1.5) on the hazards 1.2/2.8/3.8/4.5/5.0% a year (17.3% over 5 years).
- **Swing:** -18.6% / +23.3%. Largest in the model.
- **Origin:** a calibration to 20.6M PEPFAR-supported patients (`model_params.csv`).
- **Evidence** (full detail in L-01 and `URGENT.md`):
  - Brinkhof et al. 2009, *PLoS ONE* 4:e5790: "The combined mortality was 40%"; "among those traced 20% to 60% had
    died".
  - Marsh et al. 2020, *Lancet HIV* 7(9):e629: a 6-month interruption for 50% of people on ART gives "a median
    excess of HIV deaths ... of 296,000" in one year in sub-Saharan Africa.
- **Test** (rescaled hazard reaching 20% / 40% / 60% over 5 years):
  - deaths 2026-30: 2,112,504 / 3,173,246 / 4,233,987;
  - change: +7.3% / +61.1% / +115.0%.
- **Recommended:**
  - If units stay full-cost equivalents who actually stop ART: a 5-year risk of 40% (20-60%), from Brinkhof 2009.
    That is art_hazard_mult 2.31 (1.16-3.47).
  - Or keep 17% and apply it to everyone at supported sites (reading B).
- **Class:** (b).

**art_transmission**: 0.04 (0.02-0.08) new infections per person-year off ART.
- **Swing:** -0.3% / +0.6% (2031-35: -6% / +12%).
- **Evidence:** untreated serodiscordant couples transmit at about 2.2 per 100 person-years overall, and 8.8 per 100
  at CD4 below 200 (Partners PrEP data via aidsmap). People who stop ART rebound to high viral load within weeks.
- **Assessment:** 0.04 is a reasonable central value for a mixed population with multiple partners, though it is a
  judgment.
- **Class:** (a)/(c). Supported in size, but the value is chosen.

**ART_INFECT_LAG**: 0.5 in year 1.
- **Basis:** viral rebound takes 2-8 weeks, and adherence lapses gradually.
- **Class:** (c). Effect under 0.2%.

**asd_share**: 0.45 (0.30-0.55).
- **Swing:** +17.8% / -12.2%. Third largest.
- **Cited:** "PEPFAR 2014 expenditure analysis: above-service-delivery spending = 45%". I could not find this exact
  figure (UNVERIFIED).
- **Closest found:** KFF (2025), on PEPFAR 2018-2023 in 22 countries: "non-service delivery accounted for 47% of
  spending".
- **Class:** (a) for the value, using KFF 47%; fix the citation (L-26).
- **Concept issue:**
  - Applying 1/(1-asd) to ART and TB costs assumes all donor money carries the same above-site overhead.
  - Global Fund grants to governments carry much less programme management than PEPFAR's
    implementing-partner model. Global Fund programme-management costs are typically 10-20% (Global Fund budgeting
    guidelines; UNVERIFIED exact figure).
  - A channel-specific asd would raise people losing services where Global Fund money dominates (IMP-07).

**uc_art_mult**: 1 (0.75-1.3).
- **Swing:** +14.5% / -10.6%.
- **Evidence:** Rosen 2021 site costs for 5 countries.
- **Better data:** the GHCC Unit Cost Study Repository has ART costs for many more countries; PEPFAR Expenditure
  Analysis gives costs per patient by country (IMP-03, DR-01).
- **Class:** (b)/(d). Country data exists.

**uc_scale_elast**: 0.4. **Class:** (c). Swing +1.0% / -1.5%.

**uc_pmtct**: 250 (150-450) per woman a year, including her ART.
- **Swing:** +1.7% / -1.4%.
- **Cited:** Health Policy & Planning 2016;31(8):1133. The review's per-woman figures could not be read from the
  abstract (UNVERIFIED).
- **Internal consistency:** the model's own ART cost (about US$300 with markup in Kenya) plus PMTCT-specific
  services (about US$50-100) supports about US$250-400.
- **Class:** (a)/(c) (L-32). Batch 7 item 16: relabelled "unverified; review figure" in `model_params.csv`
  (status `unverified`); the figures are in no file on disk; value and range unchanged.

**cpia_ref**: 5,000 (2,500-12,000) per infection averted, scaled by (1/incidence)^0.5.
- **Swing:** +0.3% / -0.2%; affects infections, not deaths.
- **Evidence:** UNAIDS investment-case estimates put the cost per infection averted at several thousand to tens of
  thousands of dollars, varying with incidence (UNVERIFIED specific number).
- **Class:** (c).

**pmtct_vt_reduction**: 0.25 (0.10-0.40). Swing ±2.1%.
- **Evidence:** WHO, "15-45% without intervention ... below 5%".
- **Class:** (a).

**pmtct_infant_mort**: 0.45. Newell et al. 2004, *Lancet*: 35.2% dead by age 1, 52.5% by 2. **Class:** (a).

**hiv_inf_death_untreated** 0.85, **hiv_survival_median** 10.5 years, **Weibull shape** 2.25.
- **Evidence:** Todd et al. 2007 (ALPHA network), median survival about 10.5-11 years.
- **Class:** (a). Swing under ±0.5%.

**hiv_inf_death_treated**: 0.10. **Class:** (c). Swing ±0.1%.

**art_reengage**: 0.5 a year after 2030.
- **Swing:** 0% for 2026-30; 2031-35: 850,819 at 0.25 vs 298,801 at 0.75.
- **Assessment:** the largest driver of the "further deaths" number. The value is our own (UNVERIFIED in the
  literature).
- **Class:** (c).

**hss_kappa**: 0.5 (0.25-0.9), the share of lost systems money that becomes lost services. Also applied to HIV
testing and care money.
- **Swing:** -10.1% / +16.2%. Fourth largest.
- **Evidence:** none found that quantifies how much health-systems or care-and-support money translates into
  service delivery.
  - IHME program-area definitions make HSS a distinct purpose (human resources, supply chain, information systems).
  - PEPFAR's "above-site" category overlaps it.
- **Double-counting check:**
  - For ART, kappa x care money is added on top of a unit cost already divided by (1-asd).
  - Above-site costs are thus counted twice in the money-to-people conversion: once in the cost and once by moving
    HSS money into services.
  - This partly offsets (more money per person lowers people), but the logic isn't stated anywhere.
- **Class:** (c). **L-05.**

**continuity**: 0.15 (0-0.35).
- **Swing:** +18.0% / -23.8%. Second largest.
- **Evidence:**
  - The PEPFAR FY2025 Q4 ART count was "stable compared to Quarter 4 of FY 2024" (KFF) despite large 2025 cuts. That
    suggests much higher continuity in practice, at least in the first year.
  - Early-2025 disruption surveys (UNAIDS situation reports, 2025) reported clinic closures and stock-outs, but not
    the share of patients interrupted. Specific figures: UNVERIFIED.
  - For TB, the private-sector share of notifications (WHO GTB data; India about 33%) is direct data on alternative
    sources.
- **Class:** (c) overall; (d) for TB.
- **Findings:** L-14; data request DR-07.

### TB

**tb_cfr_untreated_neg** 0.43 (0.28-0.53) and **tb_cfr_treated_neg** 0.03 (0-0.07).
- **Evidence:** WHO methods Table 4 (Glaziou), exact.
- **Swing:** -7.0% / +4.6% and +1.0% / -1.3%.
- **Class:** (a).

**tb_cfr_untreated_pos** 0.62 and **tb_cfr_treated_pos** 0.06, both blended by (1 - 0.3 x ART coverage).
- **Evidence:** WHO Table 5: off ART 0.78; under 1 year on ART 0.62; 1 year or more on ART 0.49.
- **Recommended:** a blend that matches Table 5 at both ends: 0.78 x (1-a) + 0.49 x a.
- **Effect:** Kenya, a = 0.9: 0.52 vs the model's 0.45. TB deaths rise by under 1% of the headline.
- **Class:** (b), minor. **L-13.**

**tb_dr_dcfr**: 0.45 (0.30-0.60).
- **Evidence:** WHO DR-TB treatment success is about 68% (GTB 2025). Untreated MDR-TB fatality is similar to or above
  DS-TB.
- **Assessment:** 0.45 is plausible.
- **Class:** (c)/(a). Swing ±0.2%.

**tb_secondary**: 0.4 (0.2-0.8).
- **Evidence:** the Styblo rule says one untreated smear-positive case infects about 10 people a year, and about 10%
  of those develop disease over a lifetime, mostly within 2 years. That gives about 1 secondary case per year of
  infectiousness.
- **Assessment:** 0.4 is conservative for smear-positive cases but reasonable across all forms (about 60% are
  pulmonary bacteriologically confirmed).
- **Class:** (a). Swing -1.2% / +2.5%.

**TB timing** (whole 10-year case fatality in the year of loss, with the year-1 lag at 0.7).
- **Evidence:** WHO, "the mean duration of untreated disease ... is about three years".
- **Class:** (b). **L-15.**

**DR_TB_SHARE 0.04 and DR_TB_COV 0.45.**
- **Evidence:** WHO GTB 2025 gives MDR/RR-TB incidence by country, and enrolment on treatment by country.
- **Class:** (d). Swing ±0.1%. DR-02.

**TB unit costs** (Laurence 2015 income-group means x 1/(1-asd)).
- **Swing (uc_tb_mult):** +11.7% / -8.1%.
- **Evidence:** Sweeney et al. 2024, *Lancet Global Health*, "cost per person treated" under standard of care:
  - India US$450;
  - Philippines US$560;
  - South Africa US$730.
- **Comparison:** the model's lower-middle-income cost is 351/0.55 = US$638 per patient.
- **Class:** (b)/(d). IMP-03.

**DR-TB unit costs.**
- **Evidence:** LMIC US$8,125 from a single 2014 study.
- **Current regimens:** BPaLM costs "US$284 per course" in drugs (Stop TB GDF 2025). Full programme costs with BPaLM
  are estimated at about US$1,500-3,000 per patient. That range is UNVERIFIED; the GHCC repository would settle it.
- **Class:** (b). **L-16.**

### Malaria

**mal_vc_eff**: 0.55 (0.40-0.61).
- **Evidence:** Eisele 2010, 55% (49-61%), for children aged 1-59 months.
- **Value:** supported. **Population:** wrong (L-04).
- **Test:** applying the effects to under-5 deaths only (75% of D0 in sub-Saharan Africa, 40% elsewhere) gives deaths
  2026-30 of 1,872,379, -4.9%.
- **Class:** (b).

**mal_cm_eff**: 0.82 (0.60-0.99).
- **Evidence:** Thwing 2011, ACT 99% for uncomplicated malaria, 82% for severe.
- **Assessment:** applied to MAP effective treatment, which is mostly uncomplicated cases. LiST applies 99% to ACT
  coverage.
- **Class:** (b). **L-20.** Swing -3.5% / +4.1%.

**uc_mal_cm**: 14 (4-47) per case.
- **Swing:** +13.5% / -6.1%.
- **Evidence:**
  - White et al. 2011, median financial cost per case treated: "US$5.84" (2009$).
  - A 2021 review: US$9.31 per case treated plus US$6.06 per RDT.
- **Assessment:** about US$14 in 2023$, so supported. The 4-47 range is very wide and is the third-largest malaria
  driver.
- **Class:** (a).

**uc_itn**: 2.2 per person-year.
- **Evidence:** GiveWell, "<$5 per net", about 1.8 people per net, about 2 years of protection, 63% used. Swing
  +3.9% / -3.8%.
- **Class:** (a).

**uc_irs**: 8.5. PMI Mali US$6.08-7.40 per person (2014$). **Class:** (a). Swing ±0.1%.

**mal_resurgence**: 0.10 (0-0.25) a year.
- **Evidence:** Cohen et al. 2012, *Malaria Journal* 11:122: 75 resurgence events, 91% "attributed at least in part
  to the weakening of malaria control programs". This supports the direction, not the size.
- **Class:** (c). Swing -2.2% / +4.2%.

**Malaria death trend** (Pf case trend, clipped ±5%).
- **Swing:** flat -0.8%, unclipped +0.1%.
- **Class:** (d), since WHO death series exist. **L-25.**

**mal_itn_default_use** 0.5 and **mal_cm_default_cov** 0.4.
- **Class:** (c). Swing 0: the countries that use them have negligible malaria deaths.

**IRS max() rule.** **Class:** (c). L-22.

**malaria_at_risk_share fallback** 0.95 / 0.35.
- **Class:** (d). WHO publishes population at risk for all endemic countries; the 16 fallback countries have
  negligible malaria.

### Immunization

**imm_deaths_per_child_ref**: 0.020 (0.017-0.024).
- **Evidence:** Gavi, "more than 20.6 million" future deaths averted, "more than 1.2 billion unique children" (=
  0.017); 2024: 1.7M / 72M (= 0.024).
- **Class:** (a). Swing -0.9% / +1.2%.

**imm_u5_share**: 0.65 (0.50-0.75).
- **Evidence:** Li et al. 2021, *Lancet* 397:398: of cohort deaths averted, hepatitis B (adult deaths) is 38M of
  120M. 1 - 38/120 = 0.68.
- **Class:** (a). Swing -1.4% / +0.9%.

**U5MR/50 scaling** (clip 0.3-2.5).
- **Evidence:** VIMC country-level impact per vaccinated child does rise with baseline mortality, but the linear form
  and the reference 50 are ours.
- **Class:** (c), with data available from VIMC country estimates (DR-09). **L-19.**

**uc_imm**: 87 (38-104).
- **Evidence:** Lydon 2014 delivery cost plus vaccine prices. Gavi country financial data FY2021-25 is in `datasets/`
  but not used.
- **Class:** (a)/(d). Swing +6.1% / -1.0%.

### Fiscal and response

**Backfill theta** (regression, -0.19, CI -0.45 to 0.07): own estimate, consistent with Lu 2010. **Class:** (a).

**Fiscal capacity** = GHES x (p75 - median growth) x stress.
- **Class:** (c). L-29.
- **Evidence:** none for this exact rule. WHO/World Bank fiscal-space analyses (Tandon & Cashin 2010) use
  macro-fiscal decomposition, not historical percentiles.

**Debt stress** (10% / 40% / floor 0.25). **Class:** (c).
- **Evidence:** IMF/World Bank LIC debt sustainability thresholds use debt service to revenue of 14-23% (LIC DSF).
  Those are a different metric.

**Lives-first order.** **Class:** (c). **L-30** (a normative rule, not behaviour).

### Scenarios and framing

**GAVI_CUT_DEFAULT 15%.**
- **Evidence:** Gavi 6.0 replenishment raised more than US$9B against a US$11.9B target, with "only US$6 billion"
  in new pledges (Donor Tracker).
- **Class:** (c), plausible. **L-09.**

**GF_CUT_DEFAULT 20%.** Global Fund 8th replenishment US$12.64B vs US$15.7B: -19.5%. **Class:** (a).

**US Global Fund cut 0.23.** US pledge US$4.6B vs US$6.0B. **Class:** (a). (Delivery is lower: the US paid
US$3.12B of US$6B in the 7th cycle, ThinkGlobalHealth.)

**OECD cuts.** **Class:** (b). These are total-ODA cuts; IHME health-specific cuts differ (L-28).

**MOU schedule rules** (increase = 0; schedules ending 2028 held flat).
- **Class:** (c). Labelled in the app.
- **Also:** partner co-financing commitments exist in the MOU texts but are ignored (L-08).

**5-year horizon and 2031-35 tail.** **Class:** (c). This is framing; Cavalcanti 2025 and Optima use 2025-2030.

**LAG ramps.** **Class:** (c). Each swing is under 1.3% (TB year-1 lag -0.9% / +1.3%; bednets -0.4% / +0.6%).

**ART_HAZARD shape.**
- **5-year effect:** 0 for a sudden cut (same total).
- **2031-35 effect:** 382,816 if flat vs 218,600 if front-loaded (base 494,715). It matters for further deaths and
  for phased paths.
- **Class:** (c).

**Aid baseline 2021-23.** **Class:** (d). IHME has 2024 actuals by recipient (L-06, DR-03).

## Recommended value changes, ranked by effect

| Parameter | Now | Recommended | Source | Change in deaths 2026-30 |
|---|---|---|---|---|
| art_hazard_mult (or the ART units concept) | 1 | 2.31 (1.16-3.47) | Brinkhof 2009 | +61% (+7% to +115%) |
| Malaria effect sizes applied to under-5 deaths only | all ages | under-5 share | Eisele 2010; Thwing 2011; WMR 2025 | -4.9% |
| TB unit costs from country studies (IND, PHL, ZAF) | income group | Sweeney 2024 | Sweeney 2024 | small: donor TB money in these countries is small |
| DR-TB cost | 8,125 LMIC | about 2,000-3,000 (UNVERIFIED) | GDF; GHCC | under +1% |
| tb_cfr_untreated_pos blend | 0.62(1-0.3a) | 0.78(1-a) + 0.49a | WHO Table 5 | under +1% |
| mal_cm_eff | 0.82 | 0.99 for uncomplicated (LiST) | Thwing 2011 | +4.1% (offsets part of the malaria under-5 change) |
| asd_share | 0.45 | 0.47 (cite KFF) | KFF 2025 | about -2% |
