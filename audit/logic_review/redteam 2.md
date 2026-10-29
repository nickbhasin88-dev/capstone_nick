# Part 7: Independent red-team review

## How it was run

- **Reviewer:** a separate subagent, briefed as "a skeptical WHO health economist reviewing ... before publication".
- **It received:**
  - README;
  - the Methods page source;
  - a copy of `logic.md` with only the specification (sections 0-6), so it could not see this review's findings;
  - `model_params.csv`, `unit_cost_reference.csv`, `model_data/`;
  - the running app, rendered through Streamlit AppTest for 8 countries and 4 presets;
  - web search.
- **Forbidden:** everything under `audit/`.
- **Output:** 20 ranked points with evidence and requested actions. The full text is reproduced in the appendix
  below; the reviewer's scripts are in the session scratchpad (`redteam/`).

## Comparison with this review

| RT # | Red-team point (short) | In my findings? | Resolution |
|---|---|---|---|
| 1 | HIV hazard calibrated to 20.6M, applied to 5.3M; HIV deaths and infections 3-4x below benchmarks; Validation calls it agreement; Optima 0.77M is not the PEPFAR scenario | **Yes:** L-01 (URGENT), L-41 (infections) | **Agree.** The reviewer added a point I had missed: Optima's upper figure (2.93M) is the PEPFAR-discontinuation scenario, confirmed via Science Media Centre commentary; the lower one is unverified. Added to `benchmarks.md` and **L-47** (Validation row presents the wrong comparison range). |
| 2 | TB deaths built on converting untagged and systems money into untreated patients; about 2x published US-cut TB mortality; Tajikistan extra TB deaths 108% of current TB deaths | **Partly** (L-14, L-15, L-16; I treated TB as within benchmarks) | **Investigated:**<br>- Verified: of US$1,522M/yr TB aid, only US$352M (23%) is tagged tb_ds or tb_dr. US$700M (46%) is `tb_unspec` and goes 100% to services by the known-line mix. US$469M (31%) is HSS at kappa (`dah_lines.csv`; `health_model.py:638-658`). Effective TB service money = 352 + 700 + 0.5 x 469 = US$1,286M, 3.7x the tagged amount.<br>- Verified: extra TB deaths per year / current TB deaths = 1.08 in Tajikistan, 0.73 in Mozambique, 0.55 in Cambodia (all countries 0.08).<br>- Disagree in part on size: against Clark et al. the model is about 1.7-1.9x per year, but Clark covers USAID TB funding only (79 countries, to 2035), while Full US Exit also cuts the US share of Global Fund TB money. So "2x too high" overstates the like-for-like gap.<br>- Agree on the mechanism. **New finding L-43 (Major):** unspecified money should be spread over services and systems together, not services only. Rough effect: TB service money -15%, about -3 to -4% of the headline. The same applies to HIV and malaria unspecified money (US$819M, US$511M), about -5 to -8% of the headline in total (Low confidence; not run, needs a code change). |
| 3 | Above-site costs counted twice: 1/(1-asd) markup, plus kappa x HSS and testing & care money turned into patients | **Partly** (`assumptions.md`, hss_kappa note; L-05) | **Agree.** Upgraded L-05 to cover the double count explicitly. The reviewer measured kappa = 0 at -20% and asd = 0 at +46% (my sensitivity: kappa 0.25 gives -10.1%; asd 0.30 gives +17.8%). Testing & care money funds a flow (new initiations), not a stock; added to L-27. |
| 4 | 2025 cuts modelled as starting 2026 from a 2021-23 baseline; 2025 deaths excluded; ART year-1 hazard restarts in 2026 | **Yes:** L-06 | **Agree.** The timing aspect (people who lost ART in 2025 enter 2026 at the year-1 hazard) is added to L-06. |
| 5 | OECD total-ODA cuts applied to health aid | **Yes:** L-28 | Agree. |
| 6 | MOU preset omits co-financing; nominal vs real | **Yes:** L-08, L-35 | **Agree.** The reviewer cites Kenya's US$850M five-year co-financing pledge (*The EastAfrican*). I did not verify it independently (UNVERIFIED); KFF confirms the commitment structure. |
| 7 | No-replacement default and "historically governments have not replaced falling aid" go beyond the evidence | **Partly** (claim C2: "supported with qualifier") | **Disagreement, resolved.** My view: the sentence matches the regression's point estimate and CI (upper bound +0.07), so "have not replaced" is fair *for past declines*. The reviewer's view: past declines were small and gradual, so this is out of sample for a sudden exit; 2025 brought examples of partial replacement (South Africa, Nigeria; UNVERIFIED amounts). **Resolution:** keep C2 as "needs qualifier" and adopt the reviewer's wording request: label headlines "if no one replaces the money" (added to L-48, claims wording). |
| 8 | 95% ranges are parameter-only | **Yes:** L-02 | Agree. The reviewer adds the Validation page's own method spread (Poisson malaria 0.1x; Lancet HIV 2.5x) as evidence of structural uncertainty. |
| 9 | Proportional-cap rule ("donor money buys more than everyone covered") assumes donors fund 100% of covered people; 160 of 695 lines, 65 countries | **No** | **Investigated, agree.** The Validation page shows "Country-Service Lines Affected" with its count (`views/3_Validation.py:130`). The rule (`health_model.py:438-450`) scales the loss over *all* covered people, so a 100% donor exit removes everyone covered, including government-funded patients. Tajikistan TB (108% of current TB deaths) comes from it. The Validation caption says the excess "pays for things other than the service", which contradicts using all covered people as the donor-funded pool. **New finding L-44 (Major):** cap the donor-funded share with an external estimate (GHED/NHA donor share by disease, or Global Fund/PEPFAR commodity shares). The reviewer's estimate of the effect is 50-100K deaths too many (about 3-5%); I did not run it. |
| 10 | Immunization: cost, effect and coverage describe different interventions; circular Gavi validation | **Yes:** L-18, L-42 | **Agree,** and add: the Validation "Gavi 0.017 vs model 0.019" row compares the model with its own calibration source. That is not validation; added to L-47. The reviewer quotes the model's own "median donor vaccine aid per immunized child US$40" (Validation) against the US$87 unit cost. |
| 11 | Hero "People Losing Care" sums bednet person-years, malaria episodes and ART patient-years as people | **Yes:** L-40 | **Agree.** Kenya example: "6.10M People Losing Care Each Year — 4.90M bednet users". |
| 12 | Malaria child effect sizes on all-age deaths; resurgence and Pf trend compound to x1.78 by year 5 in high-trend countries | **Yes:** L-04, L-25 | **Agree in part.** The compounding is real for countries at the +5% clip (`health_model.py:860-866`). But the trend applies to D0 for all malaria lines, and resurgence only to vector-control deaths; they are not the same effect counted twice. Sensitivity: trend 0 gives -0.8%; resurgence 0 gives -2.2%. Noted under L-25. |
| 13 | TB secondary cases too early and too large | **Partly** (L-15 timing) | **Agree on timing; disagree on size.** 0.4 per untreated case is within the published range (`assumptions.md`). Sensitivity: tb_secondary = 0 gives -2.5% (reviewer) and the 0.2 low gives -1.2% (mine). Folded into L-15. |
| 14 | Bednet default 50% where old surveys show 4-31% (Indonesia 4% 2007, Namibia 6%, Botswana 31%) | **Partly** (L-07) | **Agree.** Low effect on deaths (sensitivity 0), but a visible credibility problem: Indonesia's hero shows bednet users at 50% assumed use. L-07 extended. |
| 15 | "Full US Exit" is neither full (keeps 77% of the US Global Fund pledge) nor current policy; contradicts the MOU preset in MOU countries | **No** | **Agree on presentation.** The 0.23 Global Fund cut is the verified pledge change, so the label "Full" is literally inaccurate. **New finding L-45 (Presentation):** rename, e.g. "US bilateral exit + multilateral withdrawals". Add a "current US policy" preset for MOU countries (IMP-14). |
| 16 | Fiscal capacity is one strong year's growth held flat, not cumulative; stress thresholds unsourced | **Yes:** L-29 | Agree. Cumulative capacity added to L-29. |
| 17 | IHME 2025 preset called "Data-driven" though the country split is an assumption | **No** | **Agree.** `scenarios.py` PRESETS text says "Data-driven: applies IHME's own 2025 preliminary DAH estimates ... (IHME has no recipient-level split ...)". **New finding L-46 (Presentation):** drop "data-driven" from the country-level description. |
| 18 | Validation framed to pass ("should come in below most of these figures"); no TB, malaria or South Africa benchmarks; `hiv_deaths_est` wrong (Honduras 85/yr) | **Partly** (L-11) | **Agree.** L-11 raised to Minor+ (it affects only the Validation Lancet comparison). Validation framing becomes **L-47**: state an acceptance band before comparing and add Clark, Mandal, MAP/PMI and Thembisa (`benchmarks.md`). |
| 19 | Post-2030 deaths assume funding returns in 2031; infection deaths cut at 2035 | **Partly** (`uncertainty_scope.md` scope table) | **Agree.** The labels already state it ("with funding back from 2031"). Added as an omission: most deaths from new HIV infections fall after 2035. No new finding (Presentation is adequate). |
| 20 | DR-TB share and coverage fixed; costs non-monotone; pre-BPaLM; Central Asian outliers | **Yes:** L-16; DR_TB_SHARE class (d) | Agree. |

## Points I raised that the red team did not

| Finding | Topic |
|---|---|
| L-03 | Country scope: 71.5% of aid; US$2.67B "Global" |
| L-13 | HIV+ TB CFR blend |
| L-17 | DTP3 currency |
| L-19 | U5MR/50 scaling |
| L-21, L-22 | IRS household vs population; max() rule |
| L-23 | MAP vs WHO cases |
| L-26 | asd_share citation |
| L-30 | Lives-first label |
| L-34 | Interest measure |
| L-36, L-37 | METHOD.md inconsistent with code; spec completeness |
| L-38 | Sections 1-3 not rebuildable |
| L-39 | India TB money routed to DR-TB |
| L-42 | Vaccine deaths per dollar vs Gavi |

## Net view after reconciliation

The two reviews agree on the main conclusion: **the all-country total is the least wrong number. The disease split is
the least reliable.**
- **HIV is understated** (L-01, L-41).
- **TB is likely overstated** (L-43, L-44, L-15).
- **Systems money conversion inflates all buckets** (L-05, L-43).
- **Vaccines are likely understated** (L-42).

The "most deaths from HIV" sentence is directionally robust, because correcting L-01 raises HIV's share.

---

## Appendix: red-team report (verbatim)

The full report, as returned by the reviewer, is in `redteam_report.md`. Its
ranked titles:

1. The HIV death parameter is calibrated to one count of patients and applied to another; deaths and infections are
   3-4x below the stated benchmarks.
2. TB deaths rest on turning untagged and systems money into untreated patients, giving about twice the published
   US-cut TB mortality and impossible country results.
3. Above-service costs are counted twice.
4. Wrong counterfactual and timing: cuts that began in 2025 are modelled from 2026 against a 2021-23 baseline.
5. The OECD preset applies total-ODA cuts to health aid.
6. The America First MOUs preset leaves out co-financing.
7. The no-replacement default and its headline sentence go beyond the evidence.
8. The 95% ranges cover parameter noise only.
9. The "donor money exceeds cost" rule assumes everyone covered is donor-funded (160 lines, 65 countries).
10. Immunization: cost, effect and coverage describe different interventions.
11. The hero figure adds bednet person-years, malaria cases and ART patient-years as people.
12. Malaria: child effect sizes on all-age deaths; two growth multipliers compound.
13. TB secondary transmission comes too early and too large.
14. Bednet use defaults to 50% where surveys show 4-31%.
15. "Full US Exit" is neither full nor realistic.
16. Fiscal space is one strong year held flat for five years.
17. The IHME 2025 preset applies one global ratio but is called "data-driven".
18. The Validation page is framed to pass, and its HIV baseline is wrong.
19. Post-2030 deaths assume funding returns in 2031.
20. Drug-resistant TB inputs are fixed, global and inconsistent.
