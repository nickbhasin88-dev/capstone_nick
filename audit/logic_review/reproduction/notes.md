# Independent reproduction: notes

Script: `repro.py`. Run it with no arguments to write `independent.csv`. It implements the current `docs/SPEC.md`
(sections 0-7 and the §6 "further deaths across the return-to-care assumption" range) from the SPEC text and the data
files it names only; no model code was read. Central values only, for KEN, NGA, IND, HND and MOZ and cases 1-4:

1. Full US exit, no response, sudden.
2. Full US exit, custom theta = 0.25 capped at fiscal capacity (p75), pro rata, sudden.
3. OECD-reported 2025 aid cuts, no response, sudden.
4. Full US exit, no response, linear phase-out.

Money is conserved exactly in every run (the sum of E over the money lines plus the nonservice amounts equals L_t to
machine precision). `first` = 0 in every case (the linear path has p_0 = 0.2).

## (a) Places where SPEC.md is ambiguous, incomplete or contradicts the data, and the reading chosen

1. **§2 "Direct channels" lists `Other`.** The spec says itself that `Other` does not occur as a channel. Confirmed: the
   data has 11 channel groups and none is `Other`. No effect.
2. **§2 presets table writes "US".** The donor group in `dah_lines.csv` is `United States`; I matched "US" to it.
   Germany, France, United Kingdom and Japan match exactly.
3. **§6 "Death-rate switch".** It is "on by default" and every audit run uses it on, so trends are on in all four cases.
   With the VIMC vaccine pathway the switch now only affects malaria (`f_mal,t`); `f_u5,t` is used by the legacy
   vaccine rule only.
4. **§4 custom response: "when 'cap to fiscal space' is on".** No default is given; the task defines case 2 as capped,
   so it is capped. g_top = `ghes_growth_p75` (the "best years" p90 variant is not used).
5. **§4 "Allocation of B_t" and §3 nonservice amounts.** §3 defines nonservice[care] (HIV only) and nonservice[b] per
   bucket; §4 says each is a separate amount. I kept them separate. Under pro rata the result is the same either way:
   every E and nonservice amount is >= 0 and they add up to L_t, so pro rata equals scaling every line by B_t / L_t.
6. **§3 "if any is missing, the median of the countries' shares, renormalised".** Read as: for each disease, the median
   of each of the five `unspec_*` shares over all 71 rows of `country_inputs.csv`, divided by the sum of the five
   medians; used when any of the country's five shares is NaN. One country in the file needs it; none of the five here.
7. **§3 "add[l] = sigma x S' x mix_l for every known line".** K_b includes `hiv_care_ct`, so with sigma > 0 the care
   line would get its share of systems money in its pool. Central sigma = 0, so this does not matter here. I also read
   "Immunization has neither" as U = S = 0 for that bucket, so E[imm] = X[imm] and nonservice[Immunization] = 0.
8. **§5 ART unit cost fallback chain.** "Only if `art_cost_full` is missing: `art_site_cost` x uc_art_mult x markup; and
   if that is missing too, (art_site_cost[country] from `unit_cost_reference.csv` inflated ...) or (arv default +
   non_arv default x sc) inflated from 2018." It is not said whether the multiplier and markup apply to the
   `unit_cost_reference.csv` values; I read the parenthetical as replacing `art_site_cost` in the expression, so they
   do. All five countries have `art_cost_full`, so at the central run (m = 1) the cost is simply `art_cost_full`.
   Likewise for TB: "Only if a column is missing: tb_ds_cost or tb_dr_cost for the income group from
   `unit_cost_reference.csv`"; I apply uc_tb_mult x markup to the fallback as to the country value. Not exercised.
9. **§5 TB cost, missing income group.** Guessed from GDP per person; if GDP is also missing the §1 default of 1,000 is
   used first (gives `low_income`). Not exercised.
10. **§5 "Covered" for hiv_art: max(ART % x PLHIV - PMTCT % x HIV+ pregnancies, 0).** Not said what happens when HIV+
    pregnancies is missing: I subtract nothing. "NaN if either is missing" is applied to ART % and PLHIV only. Nothing
    missing here.
11. **§6 HIV cohorts, "age_at_end_2030 is the cohort's age after the 2030 increment".** Applied literally: a cohort
    started at t = 0 has age 1 in 2026 and age 6 in 2031 (hazard index 6), reaching 10 in 2035. The negative-stock
    rule ("stock_t x h[t + 1]") cannot occur because units >= 0; it is coded but unused.
12. **§6 "Duration": no row ever cut.** Not covered; first = 0 (no losses then, so no effect). "Any row" is read as any
    row of the country, in any bucket.
13. **§6 TB spread, coverage c_t.** The spec defines one coverage, from TB detection % and `units_tb_ds,t`, and says
    tb_dr cases add to the tb_dr line. I use the same c_t (the DS coverage) for both lines' arriving cases; the spec
    gives no DR-specific coverage. The arrival year's c is used, c_4 after 2030. The arriving case's death probability
    is counted in full (c x cfr_t + (1 - c) x cfr_u), as written, not as a difference against treatment.
14. **§6 Malaria under-5 share.** s = the parameter named in `malaria_u5_share_param` (e.g. `mal_u5_share_afr`); if
    the name is missing or not a parameter (rule "none"), s = 0. For HND D0 = 0, so no malaria deaths and s is unused.
    The sensitivity switch `mal_u5_use_country_series` = 1 (old rule) is coded but off.
15. **§6 Malaria "If both are 0, divide by 1" / "half each if both are 0".** fi + fr = 0 with fi, fr of opposite sign is
    not covered; it cannot happen because units >= 0. Followed literally.
16. **§6 Vaccines, "lags that fall after 2035 ... are not counted".** Deaths in year t = sum over s and k with s + k = t
    for t <= 9; s + k > 9 is dropped. With m = 1 the draw factor is 1, so `imm_dpc_lo/hi` do not matter here. The §1
    LAG row for imm is legacy-only and unused.
17. **§6 Second-generation infections.** "first_s = the infections above in year s (s = 0..9)" is read as the
    first-generation off-ART infections of 2026-2035 (cohorts in 2026-2030 and people still off care in 2031-2035);
    the extra infections are added to the off-ART infections of the same years and therefore run through the
    infection-death curve and count in Displayed New HIV Infections (L.hiv_art.infections_5y). w[0] =
    F(0.5) - F(-0.5) = F(0.5) because F(x) = 0 for x <= 0.
18. **§6 "Displayed New HIV Infections" by line.** `L.hiv_art.infections_5y` = off-ART infections 2026-2030 (first and
    second generation); `L.hiv_prev.infections_5y` = lost-prevention infections; `L.hiv_pmtct.infections_5y` =
    infant infections (units x pmtct_vt_reduction, no LAG).
19. **§6 Further deaths part "hiv_art".** `C.after_2030` is the sum of the four parts: hiv_art (cohort hazard deaths
    2031-2035), hiv_infections (2031-2035 Weibull deaths from both off-ART and prevention infections), imm, tb
    (tb_ds and tb_dr arrivals in 2031-2032). The reengage range (`C.after_2030_reengage_min/max`) sets art_reengage to
    its `high` / `low` column value and recomputes everything (the post-2030 people still off care also change
    cov_t and so the risk of the infection deaths), every other parameter central.
20. **§5 donor-funded pool, b = 0.** "raw = pool x n / b" divides by E_base; if a line has no baseline money it also has
    no loss, so I return 0 there. Not exercised. Which branch binds at the central run (case 1): KEN hiv_pmtct and
    mal_irs; NGA hiv_pmtct and mal_cm; IND imm; HND hiv_art, hiv_pmtct, tb_ds, tb_dr, mal_cm, imm; MOZ tb_dr, mal_itn,
    mal_irs, mal_cm. All other lines use n / cost.
21. **§5 hiv_prev unit cost.** inc = 0.3 if either input is missing or population is 0; then clipped to 0.05-10. IND
    (0.044) and HND (0.046) hit the 0.05 floor.
22. **§4 "Lives first" and §8 cards.** Not needed for the four cases (pro rata only) and not implemented; §4 gradual
    budget increase and the MOU preset likewise (not used).
23. **Output columns.** The task mentions `path.<bucket>.<t>` columns; the old script never wrote them and the spec
    does not define a "path" quantity by bucket, so they are not written. `B.<bucket>.deaths_5y` (§7, sum over the
    bucket's direct lines) is added. Everything else is the old script's column list.

## (b) What changed in repro.py versus the old version

- §3: unspecified money is split by purpose with the Global Fund module shares (`unspec_<disease>_<purpose>`):
  treatment to the treatment lines by their mix, prevention to the prevention lines, testing to `hiv_care_ct` (HIV) or
  kappa x testing to tb_ds / mal_cm, rssh into systems money, pm to nonservice. Systems money S' is no longer converted
  (sigma = `hss_service_share`, central 0) and goes to nonservice; the old `(U + kappa S) x mix` rule is gone.
  Median-share fallback added.
- §5: hiv_art cost = `art_cost_full` (with the uc_art_mult draw rule and the old fallbacks behind it); tb_ds / tb_dr
  costs = `tb_ds_cost` / `tb_dr_cost` x uc_tb_mult x markup (reference file only as fallback); tb_dr need and coverage
  from `tb_rr_share` / `tb_rr_cov` (0.04 / 0.45 only as fallbacks).
- §5: the donor-funded pool cap: pool = covered x d with d = `donor_share_<hiv|tb|imm>` or the per-intervention
  `donor_share_mal_<itn|irs|cm>` (fallbacks `donor_share_malaria_prev` / `donor_share_malaria`); the old code compared
  against `covered` alone (d = 1).
- §6 HIV: 10-value ART hazard (0.013 ... 0.067) with H = 10, country transmission rate `art_transmission_rate` x
  art_transmission_mult (fallback 0.118), post-2030 hazard by years since stopping up to 10, and second-generation
  infections (exponential unsuppressed time, mean `hiv_new_inf_unsup_years`). Legacy switch coded.
- §6 TB spread: secondary cases from tb_dr patients now add to the tb_dr line (were all on tb_ds).
- §6 Malaria: under-5 share from the WMR 2025 regional parameter named in `malaria_u5_share_param`; the country-series
  rule kept behind `mal_u5_use_country_series`.
- §6 Vaccines: VIMC pathway, deaths by years since vaccination `imm_dpc_lag0..9` with the imm_dpc_mult draw factor, no
  mortality trend; legacy U5MR rule kept behind `imm_legacy_u5mr_scaling` or a missing `imm_dpc`.
- Output: `B.<bucket>.deaths_5y` added; further-deaths parts reported in the diagnostics print.
