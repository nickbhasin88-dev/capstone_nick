# Independent recomputation: ambiguities and choices

Script: `audit/recompute.py` (built only from `audit/METHOD.md` and the data files; no model code was opened).
Output: `audit/recompute_results.csv` (long format, 1,880 rows).

## Ambiguities and the reading chosen

1. **Non-MOU default for the US direct cut ("for 2028").** Read as: for every country with `mou_us_ref` > 0 and at
   least one of `mou_us_2026..2028`, compute its own x (latest year <= 2028, clipped to [-0.5, 1]), take the mean
   over those countries, round to 2 decimals. Result 0.36, which matches the value the spec expects. HND and IRQ use it.
2. **Global mix when a bucket's direct baseline is 0.** Read as each direct line's share of the summed baseline of
   that bucket's *direct* lines across all countries (so the shares add to 1). Not triggered: every one of the
   five countries has positive direct-line baseline in every bucket. Implemented anyway.
3. **Allocation of R.** Only lines/buckets with a positive amount get a share; negative eff_l get 0 replaced. The
   nonserv_b shares of R are absorbed and do not reach any line (they only dilute the service share).
4. **Units clip when coverage is known**: applied after continuity, as written.
5. **Bednet/spraying pool**: the limit is (bednet use x population at risk); scaling only when the sum is positive
   and exceeds the limit. Coverage after for mal_itn and mal_irs is each computed separately against the
   population at risk (they are not combined).
6. **Coverage after when need = 0** (IRQ `malaria_cases` = 0): reported as missing (NaN) rather than dividing by 0.
7. **TB spread**: secondary cases from year s use un-ramped units (spec says units x tb_secondary; no ramp mentioned).
   Arrivals use one death probability with c_t constant over all years (sudden cut). Secondary cases from tb_dr
   units are also added to tb_ds deaths. Arrivals in 2031 and 2032 are both counted in after_tb.
8. **TB c_t when TB need/coverage missing**: falls back to c = 0 (not triggered here).
9. **Malaria**: D0 "none if missing or 0" -> all malaria deaths 0 (HND, IRQ). If `malaria_cases` is 0 the
   treatment ratio is set to rc = 1 (cc1 = cc0); not reached because D0 is 0 for IRQ.
   The malaria split is computed once from the year's units (same every year for a sudden cut), then multiplied by
   ramp, trend and (vector parts only) the rebound factor. Malaria contributes nothing to 2031-2035.
10. **Immunization after 2030**: level for year 2030+k = (clipped) 2030 level x (1 + trend_u5mr)^k; remaining weights
    of the 2028-2030 cohorts are summed over 2031-2033. The clip [0.3, 2.5] is not re-applied after 2030.
11. **HIV infections after 2030**: lost-prevention infections stop in 2031 (funding is back); infections from people
    still off ART continue at art_transmission x people still off (no 0.5 first-year factor). The after_hiv_infections
    part counts 2031-2035 deaths from off-ART and prevention infections of 2026-2035; **PMTCT infections are excluded**
    from the death calculation (their deaths are already in the PMTCT infant-mortality line).
12. **c_t for HIV infection deaths**: c_t = clip(ART coverage - off_t / PLHIV, 0, 1) with off_t = U for 2026-2030 and
    U x (1 - art_reengage)^(k+0.5) for 2031+k. c_t uses the death year t, not the infection year.
13. **People still off ART after 2030** use the year-5 hazard for all of 2031-2035 (they have been off >5 years).
14. **New HIV infections over 5 years**: PMTCT infections counted as PMTCT units x pmtct_vt_reduction in *each* of the
    5 years, without the PMTCT ramp (0.6 in year 1). Off-ART infections include the 0.5 first-year factor
    (total = U x 0.04 x 4.5). Prevention units x 5.
15. **Cards**: independent of the government response (same values for "none" and "custom25"). Coverage drop uses
    the main line's need (PLHIV, TB incidence, population at risk, births); people are not clipped to coverage.
    The bednet card runs the malaria formula with itn = 1,000,000/uc_itn, irs = cm = 0, with ramp 0.5,1,1,1,1 and the
    malaria-death trend, no rebound, then x (1 - continuity). The ART card uses the hazards x art_hazard_mult.
    Where the card's deaths are 0 (no malaria deaths in HND/IRQ) aid per death is reported as NaN.
16. **Year-1 deaths** are 2026 deaths including the first-year HIV-infection deaths (tiny) and no TB spread (arrivals
    start in 2027).
17. **CPI for ART site cost** applies by the row's cost_year (2018 or 2020); none of the five countries has a
    country site cost, so all use (95 + 23 x sc) x CPI2018 x 1 x markup.
18. **Prevention cost**: inc = `sh_hiv_incd_tl` / `sp_pop_totl` x 1000 (new infections per 1,000 population),
    clipped to [0.05, 10]; cost = 5000 x inc^-0.5.

## Things in the spec that look odd or possibly wrong

- The direct-channel list includes `Other`, but no row of dah_lines has chan_grp `Other` (channels present:
  Global Fund, UNAIDS, UNICEF, Development banks, Bilateral agency, NGOs, Gates direct, WHO, UNFPA, EU institutions,
  Gavi, CEPI). Harmless but suggests a stale label.
- The 0.3a ART adjustment is applied to both untreated and treated HIV-positive TB case fatality, and inside dCFR it
  multiplies the difference; consistent, but the treated/untreated asymmetry is not explained.
- Malaria `cfr`-style ratio uses `mal_cm_default_cov` whenever incidence < 50 per 1,000 even when survey treatment
  data exist (HND has 0.2% treated but gets 40%). Literal reading implemented.
- PMTCT infections enter the 5-year infection count with no ramp-up while PMTCT deaths have a 0.6 first-year ramp;
  the spec does not say whether the ramp applies to infections.
- The `America First MOUs` default 0.36 for countries without an MOU means HND/IRQ lose a large share of US
  bilateral aid; IRQ has `mou_us_ref` = 695,657 but no year values, so the default is used.
- `hiv_ovc` is a "direct" line but has no need/coverage or deaths; it still absorbs a share of unspec/hss money and of R.
