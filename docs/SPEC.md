# Model specification

This is the single, current specification of the funding-cut model behind Section 4 of the dashboard, the All
Countries page and the Validation page. It replaces `audit/METHOD.md` and the specification part of
`audit/logic_review/logic.md`. It is written so that every displayed Section 4 number can be recomputed with pandas
and numpy from the data files alone, without the model code. The independent reproduction in
`audit/logic_review/reproduction/` is built from this file only.

When the code changes, this file changes in the same commit. References `file:line` point to the implementation for
readers who want to check it; nothing here requires reading the code.

## 0. Conventions

- Money: constant 2023 US$ per year unless stated. MOU amounts are nominal (used only as ratios).
- Years: t = 0..4 is 2026..2030 (code index); "year 1..5" in prose means the same years. POST years k = 0..4 are
  2031..2035.
- Shares are 0-1 in formulas. Coverage columns in `country_inputs.csv` named `sh_*` are percentages: divide by 100.
- A missing value (NaN) in an input is handled as stated next to each formula; nothing is filled silently.
- clip(x, a, b) = min(max(x, a), b).
- The **central run** uses every parameter at `central` from `model_params.csv`. All displayed point values are from
  the central run. Ranges come from the draws (section 9).

## 1. Files and columns

| File | Contents |
|---|---|
| `model_data/dah_lines.csv` | Baseline aid, average of 2021-2023, US$ a year: `iso3, src_grp, chan_grp, usd, line, bucket`. One row = country x donor group x channel group x line |
| `model_data/country_inputs.csv` | One row per country (`iso3`) |
| `model_data/ihme_trend.csv` | IHME 2025 / 2021-23 ratio: `src_grp, chan_grp, bucket, ratio` |
| `model_params.csv` | Parameters: `central, low, high` |
| `unit_cost_reference.csv` | ART site costs (`art_site_cost` by country, `art_site_default` arv / non_arv) and TB costs (`tb_ds_cost`, `tb_dr_cost` by income group), with `cost_year` |

Country columns used (`country_inputs.csv`):

| Symbol | Column | Notes |
|---|---|---|
| PLHIV | `plhiv` (`_year`, `_source`) | people living with HIV, all ages: UNAIDS AIDSinfo 2026 estimates, 2025 (`unaids_inputs.py`, Batch 7 item 4); WHO GHO or the derived value where UNAIDS has none |
| ART % | `sh_hiv_artc_zs` (`_year`, `_source`) | UNAIDS 2026 estimates, all ages, 2025; GHO / WDI where missing |
| PMTCT % | `sh_hiv_pmtc_zs` (`_year`, `_source`) | UNAIDS 2026 estimates (coverage of pregnant women receiving ARV), 2025; GHO where missing; if missing altogether, ART % is used |
| HIV+ pregnancies | `hiv_pos_pregnancies` (`_year`, `_source`) | UNAIDS 2026 estimates, pregnant women needing ARV for PMTCT, 2025; the GHO-derived value where missing |
| new HIV infections | `sh_hiv_incd_tl` (`_year`, `_source`) | number a year: UNAIDS 2026 estimates, all ages, 2025; the WDI mirror (2024) where missing |
| HIV transmission rate per unsuppressed person | `art_transmission_rate` (`_lo`, `_hi`, `_year`, `_source`) | UNAIDS new infections / (PLHIV - suppressed), latest year with all three (`hiv_transmission_inputs.py`); WHO-region median of the dashboard countries where missing |
| population | `sp_pop_totl` | |
| AIDS-related deaths | `hiv_deaths_unaids` (`_year`, `_source`) | UNAIDS 2026 estimates, all ages, 2025 (`unaids_inputs.py`); Validation page only (Lancet rate-ratio baseline); `hiv_deaths_est` (GBD-2019 share x crude death rate) where missing |
| TB incidence | `all_forms_of_tb_incidence_estimated` | number a year (not `sh_tbs_incd`, which is per 100,000) |
| TB detection % | `sh_tbs_dtec_zs` | capped at 100 (flagged when above) |
| h (TB-HIV share) | `tb_hiv_share` | 0 if missing |
| malaria population at risk (PAR) | `malaria_pop_at_risk` | |
| malaria cases | `malaria_cases` | |
| D0 (malaria deaths, all ages) | `malaria_deaths` | |
| child malaria deaths, 1-59 months | `malaria_deaths_in_children_1_59_months_total_deaths` | WHO/MCEE, 2021; for the under-5 share |
| sub-Saharan Africa | `is_ssa` | True / False (sensitivity switch only) |
| WHO region; under-5 rule | `who_region`, `malaria_u5_share_rule`, `malaria_u5_share_param` | from `ext_data/who_regions.csv` (WHO TB data `g_whoregion`), written by `malaria_inputs.py` |
| bednet use, spraying, treatment coverage | `mal_itn_cov`, `mal_irs_cov`, `mal_cm_cov` | shares 0-1 (not percentages); NaN = see section 5 |
| births | `births` | |
| DTP3 % | `sh_imm_idpt` (`_year`, `_source`) | WHO/UNICEF WUENIC 2025 revision, latest year (2025 for every country), % of surviving infants (`immunization_inputs.py`; Batch 7 item 3; before: the World Bank WDI mirror) |
| U5MR | `sh_dyn_mort` | 50 if missing (legacy vaccine rule only) |
| deaths averted per fully immunized child | `imm_dpc` (`_lo`, `_hi`), `imm_dpc_lag0` .. `imm_dpc_lag9`, `imm_dpc_beyond_window`, `imm_q5_ratio`, `imm_antigens`, `imm_dpc_source` | Batch 5+6 V2: VIMC deaths averted per vaccinated child (Toor et al. 2021, supplementary data) summed over the routine antigens the country uses, x the WPP Q5 2026-30 / 2015-19 ratio; `_lag<k>` = the part falling k years after vaccination (`audit/batch56_vaccines.py`; `batch34_inputs.py --vaccines`); if missing, the legacy rule applies |
| ART site cost | `art_site_cost` (`_lo`, `_hi`, `_source`, `_year`) | US$ per patient-year at site level, 2023 US$ (`batch34_inputs.py --art`; `audit/batch34_art_costs.py`) |
| ART cost per patient-year used | `art_cost_full` (`_lo`, `_hi`, `_source`, `_year`) | 2023 US$: min(GHCC-based full cost, observed treatment spending per person on ART where valid), floored at 190.84 and gated 50-600 on the final value (`batch34_inputs.py --art-full56`; `audit/batch56_art_cost.py`) |
| TB course costs | `tb_ds_cost`, `tb_dr_cost` (`_lo`, `_hi`, `_source`), `tb_cost_year` | US$ per treatment course, provider, 2023 US$ (`batch34_inputs.py --tb`; `audit/batch34_tb_costs.py`) |
| RR-TB share and enrolment | `tb_rr_share`, `tb_rr_cov` (`tb_rr_source`) | WHO 2024: RR-TB incidence / all-forms incidence; RR patients started on treatment / RR incidence, capped at 1 |
| intervention-specific malaria donor share | `donor_share_mal_itn`, `donor_share_mal_irs`, `donor_share_mal_cm` (`_source`) | 0-1 (Batch 5+6 item A3): E_base[l] at the central run / (coverage x need x cost_l), capped at 1 (`audit/batch56_malaria_cap.py`; `batch34_inputs.py --donor56-malaria`); the WHO-region median where a country has no IHME malaria programme-area line (none) |
| external share of public malaria spending | `donor_share_malaria_prev` (`_source`, `_year`) | 0-1: GHED dis13_ext_usd / (dis13_ext_usd + dis13_gghed_usd), latest year; WHO-region median where missing; Batch 4b rule for bednets and spraying, kept as the fallback only |
| external share of disease spending | `donor_share_<hiv|tb|malaria|imm>` (`_source`, `_year`) | 0-1. HIV and immunization (Batch 5+6 item A2): the external share of PUBLIC spending, GHED dis11_ext_usd / (dis11_ext_usd + dis11_gghed_usd) and hc62_ext_usd / (hc62_ext_usd + hc62_gghed_usd), latest year (`batch34_inputs.py --donor56-hiv-imm`; `audit/batch56_donor_share.py`). Malaria (all-source, kept for reference only): GHED external funding on malaria / spending on it (dis13). TB: WHO TB financing, funding received from the Global Fund, USAID and other grants / all received (2024; 2025 expected funding if missing). WHO-region median where missing (`batch34_inputs.py --donor`; `audit/batch34_donor_share.py`) |
| split of unspecified money | `unspec_<hiv|tb|malaria>_<treatment|prevention|testing|rssh|pm>` (`_source`) | shares 0-1 summing to 1 per disease: Global Fund grant budgets by module, GC7 (`batch34_inputs.py --shares`; `audit/batch34_gf_shares.py`); WHO-region median where the country has no grant |
| trends | `trend_u5mr`, `trend_malaria_deaths` | yearly change (shares); -0.009 if missing. `trend_u5mr`: UN IGME under-5 mortality 2010-2019. `trend_malaria_deaths`: WHO estimated malaria deaths (GHO `MALARIA_EST_DEATHS`) 2015-2024, log-linear fit (at least 5 positive years), clipped to ±5% a year (the clip is an assumption); 0 where WHO has no series (built by `malaria_inputs.py`) |
| GDP per person | `gdp_pc` | 1,000 if missing |
| income group | `income_group` | `low_income`, `lower_middle_income`, `upper_middle_income` |
| GHES | `ghes_2023` | government health spending, US$ |
| WEO nominal GDP growth 2026-2030 | `gdp_growth_weo_2026_30` (`_source`) | mean year-on-year growth of nominal US$ GDP 2026-2030 in `macro_data/<ISO3>.csv` (IMF WEO projections); the upper end of the `budget_growth` sensitivity (Batch 7 item 10); 0 if missing |
| growth | `ghes_growth_median`, `ghes_growth_p75`, `ghes_growth_p90` | shares a year; 0 if missing |
| interest | `interest_pct_revenue` (`_year`, `_source`) | % of revenue; never missing. IMF World Economic Outlook, October 2026 release (`datasets/IMF_WEO_Oct2026_GG_balances_2026-10-13.csv`, downloaded 13 October 2026), with World Bank WDI as the fallback (Batch 7 item 7). The GDP, revenue and expenditure series in `macro_data/` carry no recorded WEO vintage; their projection horizon ends in 2031, consistent with the October 2026 release |
| MOU | `mou_us_ref`, `mou_us_2026` .. `mou_us_2030` | nominal US$ |

**Lines.**
- HIV: `hiv_art`, `hiv_pmtct`, `hiv_prev`, `hiv_ovc` (direct), `hiv_care_ct` (linked to `hiv_art`), `hiv_unspec`,
  `hiv_hss`.
- TB: `tb_ds`, `tb_dr` (direct), `tb_unspec`, `tb_hss`.
- Malaria: `mal_itn`, `mal_irs`, `mal_cm` (direct), `mal_unspec`, `mal_hss`.
- Immunization: `imm` (direct).
- Known lines K_b of bucket b = its direct lines, plus `hiv_care_ct` for HIV.

**Constants.**

| Constant | Value |
|---|---|
| DR_TB_SHARE | 0.04 (fallback only: `tb_rr_share` is used where present) |
| DR_TB_COV | 0.45 (fallback only: `tb_rr_cov` is used where present) |
| ART_HAZARD (excess deaths per person-year by years since stopping ART 1..10) | 0.013, 0.025, 0.037, 0.049, 0.060, 0.068, 0.072, 0.073, 0.071, 0.067 (Batch 2: CD4-stage cohort calculation, `audit/batch2_cohort.py`) |
| ART_HAZARD_LEGACY (years 1..5; the year-5 value after that; only when hiv_legacy_art_params = 1) | 0.012, 0.028, 0.038, 0.045, 0.050 |
| ART_REENGAGE_LEGACY (only when hiv_legacy_art_params = 1) | 0.5 |
| ART_TRANSMISSION_FALLBACK (if a country has no `art_transmission_rate`) | 0.118 |
| ART_INFECT_LAG (by years off ART 1..5; the year-5 value after that) | 0.5, 1, 1, 1, 1 |
| HIV Weibull shape | 2.25 |
| POST_YEARS | 5 |
| CPI-U | 2014: 236.736, 2018: 251.107, 2019: 255.657, 2020: 258.811, 2021: 270.970, 2022: 292.655, 2023: 304.702 |

**LAG** (share of the full yearly effect by years the cut has been in force, index d = 0..4):

| Line | d = 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| hiv_pmtct | 0.6 | 1 | 1 | 1 | 1 |
| tb_ds, tb_dr | 0.7 | 1 | 1 | 1 | 1 |
| mal_itn | 0.5 | 1 | 1 | 1 | 1 |
| mal_irs | 0.8 | 1 | 1 | 1 | 1 |
| mal_cm | 1 | 1 | 1 | 1 | 1 |
| imm (cumulative; legacy vaccine rule only) | 0.4 | 0.75 | 0.95 | 1 | 1 |

## 2. Scenario cuts

**Direct channels** are `Bilateral agency`, `NGOs`, `Gates direct`, `Other`; every other channel is multilateral.
(`Other` does not occur as a channel in the data; donor "Other / unallocable" is a donor group, not a channel.)

For each row of `dah_lines` (donor s, channel c, bucket b):

    if the IHME preset:  cut = 1 - ratio[s, c, b]      (ratio from ihme_trend.csv; 1 if the cell is not listed)
    else:  x = src_direct[s] if c is direct, else src_multi[s]      (0 if s is not listed)
           x = pair[s, c] if that pair is defined (replaces x)
           y = chan[c]                                               (0 if not listed)
           cut = 1 - (1 - x)(1 - y)
    cut = clip(cut, -1, 1)

**Presets** (any donor or channel not listed: 0; "US" below is the donor group `United States` in `dah_lines.csv`):

| Preset | src_direct | src_multi | pair | chan |
|---|---|---|---|---|
| US Bilateral Exit + Multilateral Withdrawals (key `Full US exit`) | US 1.0 | none | (US, WHO) 1, (US, Gavi) 1, (US, UNFPA) 1, (US, Global Fund) 0.23 | none |
| America First MOUs | US: country schedule (below) | none | as US Bilateral Exit | none |
| IHME 2025 | (ratio rule above) | | | |
| Total-Aid Cuts (OECD) Applied to Health Aid (key `OECD-reported 2025 aid cuts`) | US 0.57, Germany 0.174, France 0.109, United Kingdom 0.108, Japan 0.056 | the same values | none | none |
| Global Fund & Gavi | none | none | none | Global Fund 0.20, Gavi 0.15 (user-set) |
| Combined | US 1.0; Germany, France, UK, Japan as OECD | Germany, France, UK, Japan as OECD (US 0) | as US Bilateral Exit | none |

So under US Bilateral Exit + Multilateral Withdrawals (77% of the US Global Fund pledge kept), US money through every other multilateral channel (UNICEF, UNAIDS, development banks, EU
institutions) has cut 0.

**IHME ratio** (built by `prepare_model.py`):
- ratio = IHME 2025 DAH / 2021-23 average DAH for the (donor group, channel group, bucket) cell, global totals.
- If the cell's baseline is under US$20M a year, the donor group x bucket ratio is used instead.
- Missing ratios count as 1; the ratio is clipped to 0-1.5.

**MOU schedule** for country i (America First MOUs only; countries without a schedule cannot run this preset):
- Requires `mou_us_ref` > 0 and `mou_us_2026` present.
- For each year y = 2026..2030: if `mou_us_<y>` is present, cut_y = clip(1 - mou_us_<y> / mou_us_ref, 0, 1);
  otherwise the last available year's cut is held. Amounts are nominal US$ as written (default). With `mou_deflate`
  = 1 (constant switch, `model_params.csv`; Batch 7 item 8), mou_us_<y> is first divided by (1 + mou_us_inflation)^(y -
  2023), mou_us_inflation = 0.02 (0.01-0.04, labelled assumption), and the reference is unchanged (a 2021-25 average
  centred on 2023). The switch is read from the parameter file at its central value, not from the dashboard editor.
- On US direct-channel rows the yearly cut is x_t = pair[US, c] if defined, else cut_t; then
  1 - (1 - x_t)(1 - y), clipped to -1..1.
- All other rows use the same cut every year.

**Funding path** p_t (share of the full cut in force in year t; 1 for every year = "Sudden"):

| Path | p_t, with u = (t+1)/5 |
|---|---|
| Linear phase-out | u: 0.2, 0.4, 0.6, 0.8, 1.0 |
| Front-loaded | 1 - (1 - u)^2 |
| Back-loaded | u^2 |
| S-curve | s_t / s_4, with s_t = 1 / (1 + exp(-1.5 (t + 1 - 3))) |

The cut in force on row r in year t is cut_r,t x p_t. MOU schedules are never multiplied by a path in the app.

**Gross loss by line and year:** G[l,t] = sum over the country's rows of line l of usd x cut x p_t. If G[l,t] < 0
(aid rises), the rise is recorded as a gain and G[l,t] = 0. Gains are not modelled.

**Aid at Risk** (headline) = mean over t of L_t, with L_t = sum over all lines (direct, linked, unspec, hss, ovc) of
G[l,t].
**Deepest-year loss** `gross_full` = max over t of the same sum with p_t = 1 (fiscal panel and break-even only).
**Baseline aid** = sum of `usd` over all the country's rows.

## 3. Money by service line (effective loss)

For bucket b and any money series X (baseline, or year t's G), with kappa = `hss_kappa` and sigma =
`hss_service_share` (central 0):
- mix_l = base_l / sum_{K_b} base. Here base is the country's raw baseline by line. If that sum is 0, the global mix
  is used: each known line's share of the bucket's known-line baseline summed over all countries in `dah_lines`.
- U = X[b_unspec], S = X[b_hss] (0 if absent; Immunization has neither).
- **Split of U by purpose** (L-43): shares s_treat, s_prev, s_test, s_rssh, s_pm from `country_inputs.csv`
  (`unspec_<hiv|tb|malaria>_<treatment|prevention|testing|rssh|pm>`, summing to 1; if any is missing, the median of
  the countries' shares, renormalised). Treatment lines T_b: HIV `hiv_art`; TB `tb_ds`, `tb_dr`; malaria `mal_cm`.
  Prevention lines P_b: HIV `hiv_prev`, `hiv_pmtct`; malaria `mal_itn`, `mal_irs`; TB none. Testing target: HIV the
  linked line `hiv_care_ct`; TB `tb_ds`; malaria `mal_cm`.
  - mix_{l|T} = base_l / sum over T_b of base (the global mix among those lines if the sum is 0); mix_{l|P} the same
    over P_b.
  - S' = S + U x s_rssh (systems money including the systems share of U).
  - add[l] = sigma x S' x mix_l for every known line; plus U x s_treat x mix_{l|T} for l in T_b; plus
    U x s_prev x mix_{l|P} for l in P_b.
  - HIV: add[care] += U x s_test. TB and malaria: add[target] += kappa x U x s_test.
- For each direct line l of b: E[l] = X[l] + add[l].
- For the linked line `hiv_care_ct`: pool = X[care] + add[care]. E[care] = kappa x pool;
  nonservice[care] = (1 - kappa) x pool. (A proxy: the money funds a flow of diagnoses and retention, not a stock
  of patients; a flow-of-initiations treatment is not implemented, IMP-02c, `audit/logic_review/batch34_evidence.md` C.)
- nonservice[b] = (1 - sigma) x S' + U x s_pm + (U x s_prev if P_b is empty) + ((1 - kappa) x U x s_test if b has
  no linked line).
- `hiv_ovc` receives no unspecified money.

Systems money (S) is above-site money that the marked-up unit costs (section 5) already price into every patient,
so it is not converted into service units (Batch 3+4, logic review L-05; sigma is a constant in the draws; sigma > 0
is a sensitivity case set by hand).

Money is conserved: sum of E over K_b plus nonservice = X[direct] + X[care] + U + S.

E_base = the same with X = baseline. **Displayed per-line money** (service table; for hiv_art these are ART's own
amounts: the linked testing-and-care money has its own row, although its kappa share counts toward ART's units):
- base_usd = E_base[l];
- gross = mean over t of E_t[l];
- replaced = mean over t of the replacement allocated to l;
- net = gross - replaced.

## 4. Government response

**Fiscal capacity** (US$ a year):

    surge  = max(0, g_top - max(g_median, 0))      g_top = ghes_growth_p75 (or _p90 for "best years")
    stress = clip(1 - (interest_pct_revenue - 10) / 40, 0.25, 1)
    capacity = ghes_2023 x surge x stress           (0 if ghes_2023 is missing)

The stress thresholds 10 (range 5-15), 40 (30-50) and the floor 0.25 (0.15-0.50) are labelled assumptions held as
constants (`health_model.STRESS_FREE_PCT`, `STRESS_SPAN_PCT`, `STRESS_FLOOR`; not drawn; Batch 7 item 9). Capacity is
the same every year (one strong year's surge held flat); a cumulative alternative is noted, not implemented.

**Wanted replacement** in year t for loss L_t:

| Mode | Wanted | Paid R_t |
|---|---|---|
| none | 0 | 0 |
| gradual | 0 | 0 |
| custom | theta x L_t | min(wanted, capacity) when "cap to fiscal space" is on, else wanted |
| max | L_t | min(L_t, capacity) (always capped) |

**Gradual Budget Increase:** gov_add_t = points_t / 100 x gov_spend x (1 + budget_growth x g)^(t + 1).
- gov_spend = ghes_2023 / (health share of government spending / 100), in 2023 US$.
- budget_growth (model_params.csv, constant, default 0) x g, with g = `gdp_growth_weo_2026_30` (the country's mean
  nominal US$ GDP growth 2026-2030 from the WEO projections in `macro_data/`; 0 if missing): the default keeps the
  budget at its 2023 level; 1 lets it grow with GDP (Batch 7 item 10). The same factors apply in the break-even
  search.
- points_t follow the chosen shape (Steady p x (t+1); Fast start 5p (1 - (1 - u)^2); Slow start 5p u^2), capped at
  the room to the Abuja 15% share.

**Budget** B_t = min(R_t + gov_add_t, L_t): replacement never exceeds the loss.

**Allocation of B_t** over the year's positive effective losses E_t[l] (every money line: direct and `hiv_care_ct`)
and the positive nonservice amounts, each as a separate amount (nonservice[care], and nonservice[b] for each bucket):
- **Pro rata:** each amount gets B_t x amount / (sum of all positive amounts).
- **Lives first** (shown as "Hypothetical best case (triage)"; an optimisation rule, not observed behaviour):
  - Money lines are refilled in descending order of central deaths per US$ (dpd), each up to its own loss, until
    B_t runs out.
  - What is left goes to the nonservice amounts in proportion, each up to its own amount.
  - dpd[l] for hiv_pmtct, hiv_prev, hiv_ovc, tb_ds, tb_dr and imm = (sum over d = 0..4 of level_l,d x LAG_l[d]) /
    cost_l. Levels are as in section 6, at the central run, calendar-indexed. hiv_prev and hiv_ovc have level 0.
  - dpd[hiv_art] = art_hazard_mult x sum(ART_HAZARD[1..5]) / cost_art (ART_HAZARD_LEGACY when hiv_legacy_art_params = 1).
  - dpd for malaria lines = sum over t = 0..4 of (that line's malaria part from section 6, with 1,000,000 / cost_l
    units on that line alone and 0 on the others) x LAG_l[t] x f_mal,t, divided by 1,000,000. This uses calendar t
    and has no rebound factor.
  - dpd[hiv_care_ct] = dpd[hiv_art].

**Net loss** by line: N_t[l] = E_t[l] - replacement_t[l].
**Displayed:** Replaced by Government = mean_t B_t; Net Aid Lost = mean_t (L_t - B_t).

## 5. People losing each service

**Need and baseline coverage:**

| Line | Need | Coverage |
|---|---|---|
| hiv_art | PLHIV | ART % |
| hiv_pmtct | HIV+ pregnancies | PMTCT % (ART % if missing) |
| tb_ds | TB incidence | TB detection % |
| tb_dr | `tb_rr_share` x TB incidence (DR_TB_SHARE if missing) | `tb_rr_cov` (DR_TB_COV if missing) |
| mal_itn | PAR | `mal_itn_cov`; if NaN, `mal_itn_default_use` |
| mal_irs | PAR | see below |
| mal_cm | malaria cases | `mal_cm_cov`; if NaN, `mal_cm_default_cov` |
| imm | births | DTP3 % |
| hiv_prev, hiv_ovc | none | none |

**Spraying coverage.**
- implied = clip((E_base[mal_irs] at the central run / cost_irs) / PAR, 0, 1).
- If `mal_irs_cov` is NaN, or implied > `mal_irs_cov`, the coverage is implied; otherwise `mal_irs_cov`.
- If PAR is missing or 0, the implied value is not computed and the coverage is `mal_irs_cov` (NaN if that is
  missing too; NaN counts as 0 in section 6).

**Covered** = coverage x need (NaN if either is missing).
- For hiv_art: covered = max(ART % x PLHIV - PMTCT % x HIV+ pregnancies, 0). Women on PMTCT get their ART through the
  PMTCT line and its cost. Covered is NaN only if ART % or PLHIV is missing; if PMTCT % or HIV+ pregnancies is
  missing, nothing is subtracted.

**Unit cost** (central run unless drawn):
- markup = 1 / (1 - asd_share).
- sc = (max(gdp_pc, 200) / 1000) ^ uc_scale_elast.
- **hiv_art:** `art_cost_full` from `country_inputs.csv` (2023 US$; Batch 4b, L-50; Batch 5+6 item A1): the lower of
  (a) the GHCC-based full cost = `art_site_cost` x markup (Batch 3+4, IMP-03) and (b) observed HIV treatment spending
  per person on ART (total HIV spending from Optima Table B2 or GHED x the Global Fund treatment share
  `unspec_hiv_treatment` / UNAIDS people on ART, same year, 2023 US$). (b) is **valid** only where the Global Fund's
  share of the country's total HIV spending (Global Fund HIV and TB/HIV disbursements, mean of the spending year and
  the two years around it, / total HIV spending) is at least 0.10 (`audit/batch56_art_cost.py`); where (b) is missing
  or invalid, the candidate is (a) x the WHO-region median of (b)/(a) over the valid countries (the median over all
  valid countries where the region has fewer than 3). Floor = the lowest measured site-level ART delivery cost in
  `unit_cost_reference.csv` (Malawi, Rosen et al. 2021, 86.50 in 2018 US$) inflated to 2023 US$ (104.96) x markup =
  US$190.84 (asd_share 0.45), applied to min(a, candidate); then clipped to 50-600 (the gate is on the final value).
  Draw: with m = uc_art_mult, cost = art_cost_full x m if m <= 1, else art_cost_full x (1 + (m - 1) x
  (art_cost_full_hi / art_cost_full - 1) / 0.38), where art_cost_full_hi = the higher of (a) and the candidate,
  clipped to [art_cost_full, 600]; no markup is applied again. Only if `art_cost_full` is missing: `art_site_cost` x
  uc_art_mult x markup; and if that is missing too, the site cost in that expression is (art_site_cost[country] from
  `unit_cost_reference.csv` inflated from its cost_year by CPI-U to 2023), or (arv default + non_arv default x sc)
  inflated from 2018, each still x uc_art_mult x markup. The TB fallback values from `unit_cost_reference.csv` are
  likewise x uc_tb_mult x markup.
- **hiv_pmtct** = uc_pmtct (includes the mother's ART). **hiv_ovc** = uc_ovc.
- **hiv_prev** = cpia_ref x (1 / inc)^0.5, with inc = new HIV infections / population x 1000, clipped to 0.05-10.
  inc = 0.3 if either input is missing. Unit: infection averted.
- **tb_ds, tb_dr** = `tb_ds_cost`, `tb_dr_cost` from `country_inputs.csv` (2023 US$; Batch 3+4, IMP-11: Value TB
  and GHCC course costs, or the income-group median pooled with Laurence et al. 2015) x uc_tb_mult x markup. Only if
  a column is missing: tb_ds_cost or tb_dr_cost for the income group from `unit_cost_reference.csv`. An income group
  other than low or lower-middle uses upper-middle; a missing group is guessed from GDP per person (< 1,150 low,
  < 4,500 lower-middle, else upper-middle). These values are already 2023 US$.
- **mal_itn** = uc_itn; **mal_irs** = uc_irs; **mal_cm** = uc_mal_cm; **imm** = uc_imm.

**Units lost** in year t, for each direct line:
- **Money.** n = N_t[l], with base b = E_base[l] and test base tb = E_base[l].
  - For hiv_art, n = N_t[hiv_art] + N_t[hiv_care_ct], b = E_base[hiv_art] + E_base[hiv_care_ct], and
    tb = E_base[hiv_art] only.
- **Donor-funded pool** (Batch 3+4, IMP-04 / L-44): pool = covered x d, with d = `donor_share_<hiv|tb|malaria|imm>`
  for the line's disease from `country_inputs.csv` (clipped to 0-1; 1 if missing). For HIV and immunization d is
  the external share of public spending (Batch 5+6 item A2: household spending on STI care and on private-sector
  vaccination is not the service donors fund). For mal_itn, mal_irs and mal_cm, d = `donor_share_mal_<itn|irs|cm>`
  (Batch 5+6 item A3): the people the donor money for that intervention pays for as a share of the people covered,
  min(1, E_base[l] / cost_l / covered) at the central run, so the pool is min(covered, E_base[l] / cost_l) and the
  cap binds only where donor money exceeds the full cost of current coverage. If the column is missing: for mal_itn
  and mal_irs `donor_share_malaria_prev`, else `donor_share_malaria`.
- **Two branches:**
  - If covered is NaN: raw = n / cost.
  - Else, if tb / cost > pool (donor money would buy more than the donor-funded pool): raw = pool x n / b (0 if
    b = 0, in which case n = 0 as well).
  - Else: raw = **n / cost**. (This is the usual case. There is no further scaling here.)
- units = raw x (1 - continuity). continuity = 0.15 (0-0.30; assumption; Batch 3+4 IMP-16 found only indirect
  evidence, recorded with 0.30 as a sensitivity value).
- If need and coverage both exist, units = min(units, cap), with cap = covered for hiv_art and coverage x need
  otherwise.
- units = max(units, 0).
- hiv_prev and hiv_ovc have no cap (continuity applies).

**Displayed:**
- People Losing Service, per Year = mean_t units.
- 5-year total = sum_t units.
- Coverage drop (points) = mean_t units / need x 100 (for hiv_art the need is PLHIV).
- Coverage after = coverage - that.
- Treatment Lost Each Year (top of the Dashboard) = sum of the per-year means over hiv_art, hiv_pmtct, tb_ds, tb_dr,
  mal_cm. Prevention Lost Each Year = the same over mal_itn, mal_irs, imm. Both count the service the lost money
  would have paid for: for hiv_art, the number of people who stop ART = full-cost equivalents of the lost money
  (lost ART money / full cost per patient-year); the model treats each as a person who actually stops treatment
  (Option A, Batch 2). Labelled "people who stop ART" with a tooltip saying so.

## 6. Deaths and infections

**Death-rate switch.** "Account for already-changing death rates" is on by default (the dashboard, the All Countries
files and every audit run use it on). When it is off, every trend factor below is 1.

**Duration.** first = the first year t with any non-zero cut in force on any row of the country, in any bucket (t = 0
for a sudden cut; also 0 if no row is ever cut, which then has no effect). For t >= first, dur_t = t - first;
otherwise dur_t = 0. LAG and the malaria rebound are indexed by dur_t. Mortality
trends are indexed by calendar t.

**Trend factors.** Only malaria deaths and vaccine deaths have a baseline trend. TB and HIV deaths are per patient
(case fatality of an untreated vs a treated patient; the ART hazard), so their counterfactual is flat (L-10).
- f_u5,t = (1 + trend_u5mr)^t.
- f_mal,t = (1 + trend_malaria_deaths)^t.
- Both use -0.009 if the trend is missing, and equal 1 when the "already-changing death rates" switch is off.

**Per-unit levels** (deaths per unit lost, calendar year t):
- a = ART % / 100 (0 if missing).
- hiv_pmtct: pmtct_vt_reduction x pmtct_infant_mort.
- tb_ds:

      dCFR = (1 - h)(tb_cfr_untreated_neg - tb_cfr_treated_neg)
             + h [tb_cfr_untreated_pos (1 - a) + tb_cfr_untreated_pos_art a - tb_cfr_treated_pos (1 - 0.3a)]

- tb_dr: tb_dr_dcfr.
- imm: level_t = imm_deaths_per_child_ref x imm_u5_share x clip(U5MR x f_u5,t / 50, 0.3, 2.5).

**PMTCT, TB treatment:** deaths_t = units_t x level x LAG_l[dur_t].

**TB spread.**
- In each year s, secondary cases = (units_tb_ds,s + units_tb_dr,s) x tb_secondary. Half arrive in year s+1 and half
  in s+2.
- Coverage c_t = clip(TB detection % / 100 - units_tb_ds,t / TB incidence, 0, 1) (0 if TB need or coverage is
  missing). A case arriving in year t uses c_t, the coverage of its **arrival** year; arrivals after 2030 use c_4.
  The same c_t applies to the secondary cases generated by tb_dr patients (there is no DR-specific coverage in the
  spread calculation).
- An arriving case dies with probability c x cfr_t + (1 - c) x cfr_u, where:

      cfr_u = (1 - h) tb_cfr_untreated_neg + h [tb_cfr_untreated_pos (1 - a) + tb_cfr_untreated_pos_art a]
      cfr_t = (1 - h) tb_cfr_treated_neg + h tb_cfr_treated_pos (1 - 0.3a)

- Arrivals in 2027-2030 add to the deaths of the line whose lost patients generated them (tb_ds for cases from
  units_tb_ds, tb_dr for cases from units_tb_dr; Batch 3+4) in that year (no LAG). Arrivals in 2031-2032 count in
  further deaths (part "tb").

**Vaccines** (Batch 5+6, item V2; `imm_legacy_u5mr_scaling` = 0).
- Per-child deaths by years since vaccination, k = 0..9: dpc_k = `imm_dpc_lag<k>` (country_inputs.csv; sum over the
  antigens the country uses of VIMC deaths averted per vaccinated child x the Q5 2026-30 / 2015-19 ratio x the
  pathogen's timing weights; `audit/batch56_vaccines.py`), scaled by the draw: with m = imm_dpc_mult, lo =
  `imm_dpc_lo` / `imm_dpc`, hi = `imm_dpc_hi` / `imm_dpc`, factor = 1 - (1 - m) (1 - lo) / (1 - 0.56) if m < 1,
  else 1 + (m - 1) (hi - 1) / (1.64 - 1). No mortality trend applies (the Q5 ratio is already in the value, and the
  "already-changing death rates" switch does not change vaccine deaths).
- Deaths in year t <= 4 = sum over s <= t of units_imm,s x dpc_(t-s) x factor.
- For 5 <= s + k <= 9 (2031-2035): units_imm,s x dpc_k x factor counts in further deaths (part "imm"); lags that fall
  after 2035 and the lifetime remainder (`imm_dpc_beyond_window`) are not counted.
- Lives-first ranking (section 4): dpd[imm] = (sum over t = 0..4 of the cumulative sum of dpc_0..dpc_t) / cost_imm.
- **Legacy rule** (imm_legacy_u5mr_scaling = 1, or a row without `imm_dpc`): level_t = imm_deaths_per_child_ref x
  imm_u5_share x clip(U5MR x f_u5,t / 50, 0.3, 2.5); each year s's lost children die with weights w = (0.40, 0.35,
  0.20, 0.05) for k = 0..3; deaths in year t <= 4 = sum over s <= t of units_imm,s x w_(t-s) x level_t; for t >= 5:
  units_imm,s x w_(t-s) x level_4 x (1 + u5trend)^(t-4), u5trend = trend_u5mr (-0.009 if missing) when the switch
  is on, else 0 (after 2030 the level is level_4 x the trend without a new clip). For a sudden cut this equals units
  x level_t x (0.4, 0.75, 0.95, 1, 1).

**HIV treatment** (cohorts; Batch 2, L-01 / L-41):
- **Inputs** (hiv_art_params): hazard h[a] = art_hazard_mult x ART_HAZARD[a], a = 1..10 (H = 10); transmission
  r = art_transmission_mult x art_transmission_rate (country_inputs.csv: UNAIDS new infections / (PLHIV -
  suppressed); ART_TRANSMISSION_FALLBACK if missing); return rate g = art_reengage; D = hiv_new_inf_unsup_years.
  With hiv_legacy_art_params = 1: h = art_hazard_mult x ART_HAZARD_LEGACY (H = 5), r = art_transmission,
  g = ART_REENGAGE_LEGACY, no second generation.
- **Stock.** stock_t = units_hiv_art,t. Each year, delta = max(stock_t, 0) - max(stock_(t-1), 0) (stock_-1 = 0).
  - A fall (delta < 0) first removes people from the most recent cohorts.
  - A rise adds a new cohort of size delta with age 1.
- **Each year t, for every cohort** (size, age):
  - deaths += size x h[min(age, H)];
  - infections += size x r x ART_INFECT_LAG[min(age, 5) - 1];
  - then every cohort's age increases by 1.
- **Negative stock** (only possible with gains): adds stock_t x h[t + 1] and stock_t x r x ART_INFECT_LAG[t].
- **After 2030** (funding back): in year k = 0..4, each cohort still off care has size x (1 - g)^(k + 0.5)
  people, with age a = min(age_at_end_2030 + k, H). age_at_end_2030 is the cohort's age after the 2030 increment: a
  cohort that started in 2026 has age 6 in 2031 and 10 in 2035. It adds deaths (people x h[a], part "hiv_art") and
  infections (people x r x ART_INFECT_LAG[min(a, 5) - 1]).
- **Second generation** (unless legacy): the people infected above are unsuppressed for an exponential time with
  mean D and transmit at r. With first_s = the infections above in year s (s = 0..9, 2026-2035), the extra infections
  in year t are sum over s <= t of first_s x w[t - s] x r, where w[k] = F(k + 0.5) - F(k - 0.5), F(x) = D (1 -
  exp(-max(x, 0) / D)) (unsuppressed person-years in year s + k from one infection in mid-year s). They add to the
  off-ART infections of 2026-2030 and 2031-2035 (and so to the deaths from infections below). No third generation.
- **Sudden cut:** one cohort of size U from 2026, so first-generation deaths_t = U x h[t + 1].

**New HIV infections and their deaths** (10 years, 2026-2035):
- **Infections:**
  - from people off ART (above, first and second generation, 2026-2035);
  - lost prevention = units_hiv_prev,t (2026-2030 only);
  - PMTCT infant infections = units_hiv_pmtct,t x pmtct_vt_reduction. These count as infections but their deaths are
    already in the PMTCT line, so they are not run through the curve.
- **Timing:** λ = hiv_survival_median / ln(2)^(1/2.25) and F(x) = 1 - exp(-(max(x, 0) / λ)^2.25). The share of an
  infection's eventual death in year k after infection (k = 0 is the infection year; infections mid-year) is
  F(k + 0.5) - F(k - 0.5).
- **Risk:**
  - Off-ART count: off_t = units_hiv_art,t for 2026-2030, then the people still off care for 2031-2035.
  - ART coverage: cov_t = clip(ART % / 100 - off_t / PLHIV, 0, 1) (0 if PLHIV or ART % is missing).
  - risk_t = cov_t x hiv_inf_death_treated + (1 - cov_t) x hiv_inf_death_untreated.
- **Deaths** in year t from infections in year s <= t: infections_s x [F(t - s + 0.5) - F(t - s - 0.5)] x risk_t.
  - 2026-2030 deaths from off-ART infections add to hiv_art; those from prevention add to hiv_prev.
  - 2031-2035 deaths from both count in further deaths (part "hiv_infections").
- **Displayed New HIV Infections, 5 Years** = sum over 2026-2030 of off-ART infections + lost-prevention infections +
  PMTCT infant infections. By line: off-ART infections belong to hiv_art, lost prevention to hiv_prev, infant
  infections to hiv_pmtct.

**Malaria** (Lives Saved Tool form), for year t with that year's units:
- **If D0 is missing or ≤ 0:** no malaria deaths.
- **Baseline coverage:**
  - n0 = bednet use (default if NaN);
  - r0 = spraying coverage (0 if NaN);
  - m0 = treatment coverage (default if NaN).
- **After the loss:**
  - n1 = clip(n0 - units_itn / PAR, 0, 1);
  - r1 = clip(r0 - units_irs / PAR, 0, 1);
  - m1 = clip(m0 - units_cm / cases, 0, 1).
  - Where PAR or cases are missing or 0, the subtracted term is 0.
- **Combined vector control:** vc(i, r) = 1 - (1 - i)(1 - r); cv0 = vc(n0, r0), cv1 = vc(n1, r1).
- **Age groups** (L-04): s = the World Malaria Report 2025 under-5 share for the country's WHO region: the parameter
  named in `malaria_u5_share_param` (`mal_u5_share_afr` 0.75, `_amr` 0.20, `_emr` 0.364, `_sea` 0.25, `_wpr` 0.40,
  each drawn over its low-high range). Countries with no WMR figure (`malaria_u5_share_rule` = none: European Region,
  no malaria deaths) get s = 0. Sensitivity switch `mal_u5_use_country_series` = 1 (default 0) restores the old rule:
  s = clip(`malaria_deaths_in_children_1_59_months_total_deaths` / D0, 0, 1); if the child value or D0 is missing,
  s = 0.76 where `is_ssa` is True, else 0.40 (a child value of 0 is not missing: s = 0). Under-5 deaths Du = D0 s use Ev = mal_vc_eff and
  Ec = mal_cm_eff; deaths at 5 and over Da = D0 (1 - s) use Ev x mal_adult_effect_frac and Ec x
  mal_adult_effect_frac.
- **Ratios**, for each group g with its (D_g, Ev_g, Ec_g): rv_g = (1 - Ev_g cv1) / (1 - Ev_g cv0);
  rc_g = (1 - Ec_g m1) / (1 - Ec_g m0).
- **Extra deaths:** total = sum_g D_g (rv_g rc_g - 1); dv = sum_g D_g (rv_g - 1); dc = sum_g D_g (rc_g - 1).
- **Split:**
  - Vector part = total x |dv| / (|dv| + |dc|); treatment part = total x |dc| / (|dv| + |dc|). If both are 0,
    divide by 1.
  - The vector part splits between itn and irs in proportion to cv0 - vc(n1, r0) and cv0 - vc(n0, r1); half each if
    both are 0.
- **Year t:**
  - mal_itn and mal_irs: part x LAG_l[dur_t] x f_mal,t x (1 + mal_resurgence)^dur_t.
  - mal_cm: part x f_mal,t (its LAG is 1).

**Totals.**
- Extra Deaths 2026-2030 = sum over direct lines and years of deaths.
- **Further deaths across the return-to-care assumption** (L-33): the central run's further deaths recomputed with
  art_reengage at its high value (fewest deaths) and its low value (most deaths), every other parameter central.
  Shown under Further Deaths, labelled assumption-driven. All Countries: the sum over countries (exact, because the
  same value applies in every country). Precomputed columns `deaths_after_2030_reengage_min` (art_reengage at its
  `high` column value: fewest deaths) and `_max` (at its `low` value: most deaths); the parameter's low/high columns,
  not draw percentiles.
- Year 1 = 2026.
- Further deaths 2031-2035 = sum of the parts:
  - hiv_art: deaths among people still off ART (hazard by years since stopping, up to 10);
  - hiv_infections: 2031-2035 deaths from all infections (off-ART and lost prevention) in 2026-2035;
  - imm: vaccine cohort deaths after 2030;
  - tb: TB spread cases arriving in 2031-2032.

## 7. Displayed totals by disease

For each bucket:
- deaths = sum over its direct lines;
- base / gross = raw line sums of its lines (all, including unspec, hss, ovc, care);
- replaced = mean_t of the replacement allocated to its money lines and nonservice amounts;
- net = gross - replaced.

Deaths per US$1M (bucket) = deaths_5y / 5 / (net / 1e6), shown only if net > US$10,000.

## 8. "What Every US$1 Million Cut Does" cards

- For a disease with total aid A (all of its rows, including unspec, hss, ovc and care), run sections 2-6 with:
  - every row of that disease cut by c = min(1, 1,000,000 / A) for all donors and channels;
  - every other row cut by 0;
  - sudden path, no government response.
- Then k = 1,000,000 / (that run's disease gross loss).
- **Card values:**
  - people = units on the main line (hiv_art, tb_ds, mal_itn, imm) x k;
  - coverage drop = that line's coverage drop x k;
  - deaths = the disease's 5-year deaths x k;
  - aid per death = 5,000,000 / deaths.

## 9. Uncertainty

**Draws.** Each parameter is drawn 400 times, independently, from triangular(low, central, high), with seed 7, in
the order of `model_params.csv`.
- A parameter with high ≤ low is constant. It still consumes its draws, so the others don't shift.
- The draws are identical in every country.

**Each displayed range** is the 2.5th-97.5th percentile of the draws for that quantity. The point value is the central
run, not the median.

**Name.** These ranges are called "range across parameter values". They reflect uncertainty in model parameters only;
uncertainty in the data and in the model's structure is larger and not included. They are not confidence intervals.

**All Countries totals:**
- Totals add up each country's central value.
- The range is the 2.5th and 97.5th percentile, over the 400 draws, of the all-country total in each draw. Because
  the draws are identical in every country, the total of draw i over countries is draw i of the total. Countries
  with no aid loss contribute 0 in every draw. (Adding up country percentiles, as before, overstates the width.)

## 10. Precomputed All Countries files

`model_data/all_countries_<preset>.csv`:
- every preset except Custom;
- no government response, sudden path, trends on, 400 draws;
- one row per country, with the columns written by `health_model.run_all`.

`model_data/all_countries_<preset>_draws.csv`: one row per draw (`draw` 0-399), with the all-country total of
`deaths_5y` (2026-2030) and `deaths_after_2030` (2031-2035) in that draw. The All Countries and Validation ranges come
from these.
