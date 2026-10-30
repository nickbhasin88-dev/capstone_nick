# HIV inputs vs UNAIDS Goals / Resource Needs Model sources (read-only cross-check)

Branch chipmunk, 2026-10-29. Script: `audit/goals_crosscheck/crosscheck.py` (reads the two workbooks and calls
`health_model.unit_costs()` with central parameters, so no model value is re-typed). No model code, parameter or
output was changed.

**Inputs.**
- `datasets/goals/Goals Lite (1) (1).xlsx`: the file is named this way, not `Goals_Lite_1_1.xlsx`. Its tabs match the brief (Malawi: Dashboard, Calculations, GAM 2024, CEA).
- `datasets/goals/Unit costs 11april2025.xlsx`: UCdatabase, 2,371 rows.

Both files were readable. All 71 modelled countries appear in UCdatabase. The brief said 70, but the model has 71.

## Verdict

The model's HIV costs are broadly consistent with the Goals/RNM sources where the two measure the same thing, and two places need follow-up.

**Malawi passes the spending-bounds check (B).** Our ART full cost is $199 per patient-year. That is:
- above GAM ARV spend per person on ART ($88);
- above treatment, care and support spend per person ($158);
- below total HIV spend per person on ART ($286).

It is also close to Goals Lite's own adult ART unit cost of $160 (2024 US$).

**PMTCT ($250) is in line with most of the 8 database PMTCT rows.** Five sit within 0.5x to 2x of ours.

**The ART check against UCdatabase (A) is mostly a mismatch of concept, not a set of discrepancies.**
- UCdatabase has no ART cost per patient-year, only components. The comparator I built from them (ARVs, viral load and labs, plus CHOICE "routine visit" costs at a median of $2.48 a visit) is close to commodities only.
- Our cost is a full programme cost. It includes the above-site markup and is capped at observed spending.
- So 48 of 71 countries come out above 2x. Put on the same site-level basis (×0.55), 46 of 71 fall within 0.5x to 2x.

**The real findings are at the low end.**
- South Africa, Namibia and the Dominican Republic sit on our $57 floor. That is below the database's ARV price alone for those countries ($108 in 2023 US$).
- Indonesia ($356) is below the database's ARVs plus viral load ($426).

**Prevention (C).** Our cost per infection averted for Malawi is $6,717. That is low compared with the CEA tab's scale-up costs, but those measure the marginal cost of expanding coverage, not the average cost of the existing programme. Against the Calculations tab's cost of halving existing prevention programmes, ours sits within the range: $2,731 with condoms, $12,768 without.

## Deflator

All values are in constant 2023 US$, using US CPI-U annual averages (BLS series CUUR0000SA0). This is the same index the model uses (`health_model.CPI_U`).

| Cost year | CPI-U | Factor to 2023 |
|---|---|---|
| 2016 | 240.007 | 1.2696 |
| 2017 | 245.120 | 1.2431 |
| 2018 | 251.107 | 1.2134 |
| 2022 | 292.655 | 1.0412 |
| 2023 | 304.702 | 1.0000 |
| 2024 | 313.689 | 0.9714 |

The model's table lacks 2016, 2017 and 2024; I added them in the script, not in the model.

**Currency year in the Stover file.** The workbook has no single currency-year field.
- Its `Year` column is 2024 for 1,732 rows, 2022 for 379, 2023 for 157, and older for the rest. 25 rows are "?".
- One source note says costs were "inflated ... to 2024 US$".

I treated `Year` as each row's cost year. If every value were in fact already 2024 US$, the 2022 rows (HIV test, EID, VMMC, condoms) would move by about 7% (factor 0.971 instead of 1.041). No flag changes.

## Check A: ART cost per patient-year (71 countries)

**Ours.** `art_cost_full` from `country_inputs.csv`, in 2023 US$. It is the lower of two measures:
- the GHCC-based full cost: site cost × 1/(1 − 0.45);
- observed treatment spend per person on ART.

It is then floored at $57 and gated to $50-600 (see [health_model.py:598-604](../../health_model.py#L598-L604)).

**Theirs.** UCdatabase has no ART line, so I built a bundle per country from its own rows:
- **Low:** Adult ARVs + 1 viral load + 2 visits.
- **High:** Adult ARVs + 1 viral load + 1 CD4 + 1 creatinine + 4 visits.

Two to four visits a year follows WHO differentiated service delivery (3- to 6-monthly). This is an assumption, labelled as such.

A country is flagged only if ours is outside 0.5x to 2x of the whole low-high range.

**Concept match.** Partial. Ours is a full programme cost per patient-year, including above-site management, supply chain and M&E. Theirs is commodities, labs and CHOICE visit costs per patient-year, with no above-site cost. The CHOICE visit cost looks like a hotel-cost-only figure (median $2.48 a visit, Malawi $0.90), so the bundle leaves out most staff time. A ratio near 1.8x is therefore expected from the concept difference alone and is not a discrepancy.

| Comparison | ok | ours > 2x | ours < 0.5x | no comparator |
|---|---|---|---|---|
| ours full vs bundle | 19 | 48 | 4 | 0 |
| ours site cost (`art_site_cost`) vs bundle | 21 | 48 | 1 | 1 (PAN) |
| ours full × 0.55, site-equivalent, vs bundle | 46 | 19 | 6 | 0 |

The median ratio of full cost to the high bundle is 2.39. On a site-equivalent basis it is 1.32.

### Flags that remain on the site-equivalent basis

| Country | Ours (full) | Theirs low-high | Ratio vs high | Concept match | Flag / reading |
|---|---|---|---|---|---|
| ZAF | 57.1 | 138.4-176.7 | 0.32 | partial | **ours < their ARV price alone ($107.8)**: model floor binds (observed $35) |
| NAM | 57.1 | 132.6-165.2 | 0.35 | partial | **same: observed $42, floor binds** |
| DOM | 57.1 | 141.9-183.7 | 0.31 | partial | **same: observed $51, floor binds** |
| IDN | 356.0 | 426.1-460.7 | 0.77 | partial | **ours < their ARVs + viral load** (country-validation ARV price $377.5) |
| MUS | 108.3 | 144.5-189.0 | 0.57 | partial | ours ≈ their ARVs + viral load; below on the site basis |
| SSD | 153.6 | 521.0-1,001.3 | 0.15 | partial | their visit cost is an outlier ($230 a visit vs median $2.48): data issue on their side |
| BOL, GTM, HND, NIC | 400.4 | about 75-110 | 3.6-4.1 | partial | ours = the regional GHCC fallback × ratio, capped at the $400 gate; no country study or observed spend |
| GUY, HTI, KGZ, LBR, MDG, MNG, NGA | 400.4 | about 57-109 | 3.7-5.3 | partial | observed spend is above the GHCC $400, so the $400 gate binds |
| BDI, COD, ETH, GIN, GHA, STP, TZA | 232-367 | about 42-94 | 3.3-4.3 | partial | ours = observed (GHED × GF treatment share ÷ people on ART) |
| UGA | 314.1 | 62.6-84.5 | 3.72 | partial | ours = observed (Optima B2); own GHCC site study is $371 |

UCdatabase also has an "ART service delivery" row for four countries. This is the closest concept match: ARVs plus a delivery cost per patient-year, though above-site cost is still excluded.

| Country | Ours | Theirs: ARVs + service delivery | Ratio | Flag |
|---|---|---|---|---|
| KGZ | 400.4 | 300.9 | 1.33 | ok |
| MOZ | 227.4 | 144.0 | 1.58 | ok |
| PHL | 356.0 | 188.2 | 1.89 | ok |
| VNM | 356.0 | 60.8 | 5.86 | ours > 2x (their delivery cost is $7.57) |

### Countries with their own GHCC site study

Here our site cost is compared with their bundle, so neither side includes above-site cost.

| Country | Ours (site) | Theirs low-high | Ratio vs high | Flag |
|---|---|---|---|---|
| MWI | 150.6 | 62.0-83.2 | 1.81 | ok |
| ZMB | 140.8 | 69.7-93.6 | 1.50 | ok |
| LSO | 148.4 | 68.1-90.5 | 1.64 | ok |
| SWZ | 254.7 | 75.0-104.3 | 2.44 | ours > 2x |
| KEN | 354.3 | 69.6-93.6 | 3.79 | ours > 2x |
| UGA | 371.4 | 62.7-84.5 | 4.40 | ours > 2x |

The full table is in `check_a_art.csv`.

### PMTCT

**Ours.** `uc_pmtct` = $250 per HIV+ pregnant woman per year, including her ART (2023 US$; [model_params.csv:5](../../model_params.csv#L5)).

**Theirs.** The database's own PMTCT row exists for 8 countries. Its unit is not stated, so the concept match is uncertain.

| Country | Theirs, raw (year) | Theirs, 2023 US$ | Ours ÷ theirs | Flag |
|---|---|---|---|---|
| KEN | 259.50 (2024) | 252.07 | 0.99 | ok |
| CIV | 209.00 (2024) | 203.01 | 1.23 | ok |
| TGO | 160.00 (2016) | 203.13 | 1.23 | ok |
| MOZ | 170.13 (2024) | 165.26 | 1.51 | ok |
| NAM | 100.00 (2018) | 121.34 | 2.06 | ours > 2x (marginal) |
| GHA | 39.62 (2024) | 38.48 | 6.50 | ours > 2x: theirs is probably testing only |
| ZAF | 16.24 (2024) | 15.77 | 15.85 | ours > 2x: theirs cannot include ART |
| KGZ | 689.94 (2024) | 670.17 | 0.37 | ours < 0.5x |

I also built a per-woman-year bundle for all 71 countries: HIV/syphilis test + EID + one year of adult ARVs + 1 viral load + 4 visits. Its median is $113.6 (range $68-1,021). Against it, ours is above 2x in 50 countries.

The concept match is partial. Our figure comes from 2008-2011 Option B+ CEAs priced before ARV prices fell (the parameter's own note says it is "conservative"). The bundle excludes above-site cost. Full table: `check_a_pmtct.csv`.

### Other HIV interventions

The model has no per-person unit cost for prevention, testing, VMMC or PrEP. `hiv_prev` is costed only per infection averted (check C) and `hiv_ovc` is not in UCdatabase, so there is no per-person comparison to make. This is not a discrepancy.

## Check B: Malawi spending bounds (GAM tab, 2024 expenditure)

Numerators come from the GAM tab, column W ("Total expenditures from all sources"):
- **ARVs:** 1.2.1 adult ARVs + 1.2.2 paediatric ARVs = $86.04M.
- **Treatment:** sub-total 1 "Treatment, care and support" minus 1.1 testing = $154.04M.
- **Total:** grand total = $278.56M.

I used two denominators:
- Goals Lite's own: 920,000 adults + 27,000 children on ART, from Dashboard C3:C4.
- The model's: 1.0M PLHIV × 89% = 890,000.

Values are converted from 2024 to 2023 US$ (× 0.9714).

| Measure (per person on ART) | Goals Lite denominator, 2023 US$ | Model denominator, 2023 US$ | Ours ($198.53) ÷ bound | Bound holds? |
|---|---|---|---|---|
| ARV drugs only (lower bound) | 88.25 | 93.90 | 2.25 / 2.11 | yes: ours ≥ drugs |
| Treatment, care & support, excl. testing | 158.00 | 168.12 | 1.26 / 1.18 | (for reference) |
| Total HIV spending (upper bound) | 285.72 | 304.02 | 0.69 / 0.65 | yes: ours ≤ total |

For comparison, Goals Lite's own Malawi adult ART unit cost is $159.68 (2024 US$). It is built as adult ARVs + labs + OIs + unallocated treatment programme spend, divided by 920,000.

Our $198.53 is "min(GHCC-based 274, observed 199 from Optima Table B2 (2022))".

**Concept match.** Partial on both sides of the comparison:
- Both figures are spending per person on ART per year.
- GAM records only $3.0M of domestic public money. Government staff and facilities delivering ART are probably not captured, so GAM's "total" is a reported lower bound on true total spending.
- The upper-bound test is therefore conservative, and it still passes.

Full table: `check_b_malawi_bounds.csv`.

## Check C: cost per HIV infection averted

**Ours.** `hiv_prev = cpia_ref × (1 / incidence per 1,000)^0.5`, from [health_model.py:608](../../health_model.py#L608).
- `cpia_ref` is $5,000 central, with a range of $2,500-12,000 (labelled Assumption; [model_params.csv:6](../../model_params.csv#L6)).
- It is not a flat ~$8K. Across the 71 countries the median is $9,263, and the range is $2,720-22,361 (`ours_cpia_by_country.csv`).
- Malawi has incidence of 12,000 ÷ 21.66M = 0.554 per 1,000, so **ours for Malawi is $6,717**.

**Theirs.** The CEA tab ("Goals / RNM cost effectiveness analysis") is unlabelled by country, but it sits in the Malawi workbook. It gives the incremental cost per infection averted of scaling each intervention from 2024 coverage to 2030 targets.

| Intervention (CEA tab) | Infections averted | $ per infection averted | Ours ($6,717) is |
|---|---|---|---|
| Condoms | 2,600 | −111 (cost-saving) | above |
| Youth out of school | 580 | 208 | above |
| ART - Female | 2,051 | 1,531 | above |
| ART - Male | 2,974 | 1,642 | above |
| Sex workers | 1,276 | 4,251 | above |
| Mass media | 339 | 23,630 | below |
| High-risk heterosexual PrEP | 2,196 | 31,032 | below |
| Community mobilization | 520 | 37,937 | below |
| PWID PrEP | 51 | 38,985 | below |
| PWID drug substitution | 69 | 70,140 | below |
| Male circumcision | 3,175 | 97,993 | below |
| PWID needle exchange | 24 | 137,139 | below |
| Medium-risk heterosexual PrEP | 2,104 | 146,527 | below |
| MSM PrEP | 17 | 314,862 | below |
| MSM outreach | 2 | 807,338 | below |
| Economic strengthening | 153 | 975,391 | below |
| Low-risk heterosexual PrEP | 1,171 | 1,081,278 | below |

Ours is above 5 of the 17 CEA rows and below 12. The infection-weighted CEA average is $150,806 for prevention only and $111,962 including ART.

The Calculations tab prices the opposite move: halving each existing programme, 2026-2030. That matches our concept better, since the model removes existing services.

| Intervention (Calculations tab) | $ per infection averted |
|---|---|
| Condoms | −172 |
| Testing | 1,927 |
| Adult ART | 2,964 |
| Key populations | 3,637 |
| Pediatric ART | 22,644 |
| SBCC | 26,573 |
| PrEP (scale-up) | 31,684 |
| VMMC | 64,754 |
| PMTCT | 79 |

Pooled over the prevention cuts (condoms, key populations, SBCC, VMMC) the figure is **$2,731**, or **$12,768 without condoms**. **Ours ($6,717) sits between the two.**

**Concept match.**
- **CEA tab:** partial. Both are $ per infection averted, but the CEA is the marginal cost of scale-up over 2024-2030 with dynamic transmission, while ours is the average cost of the donor-funded mix that is lost. The CEA's currency year is not stated (probably 2024 US$). So "ours below most CEA rows" is not a discrepancy.
- **Calculations tab (pooled cuts):** closer, since both describe cutting existing programmes, though it is still a Goals Lite approximation.

Full tables: `check_c_cost_per_infection.csv` and `check_c_summary.csv`.

## Recommended changes (not applied)

1. **ART floor.** Make the $57 floor (TLD + one viral load) country-specific, using UCdatabase Adult ARVs + viral load (2024 → 2023 US$). This lifts ZAF, NAM and DOM from $57 to about $119-120, MUS to about $120, and IDN to $426.
   - Today their cost is driven by observed public spending ($35-51 per person), which misses domestic in-kind and insurance spending.
   - A higher cost means fewer people losing ART per dollar cut in these countries. That lowers their deaths, so the change needs a before/after run.
2. **Countries on the $400 GHCC-based value (16 countries; the 11 flagged in check A are listed below).** Review them. Their values come from the WHO-regional GHCC fallback median, not a country study, and they are 3.6-5.3x the UCdatabase bundle.
   - Option: use the four UCdatabase "ART service delivery" rows plus ARVs as an extra observed measure where they exist (KGZ, MOZ, PHL, VNM).
   - Option: add UCdatabase as a third candidate in the min() rule.
3. **PMTCT.** Consider re-basing `uc_pmtct` ($250, from 2008-2011 studies, flagged "unverified" as L-32) on a current bundle: UCdatabase ARVs + tests + EID + delivery, which gives about $114-252 depending on visits and above-site cost. KEN ($252) and CIV/TGO (about $203) support keeping the central at or a little below $250.
4. **`cpia_ref`.** It is consistent with the Malawi Goals Lite cut scenario. To move it from "assumption" to "sourced", cite Goals Lite / CEA. No change to the value is needed.
5. **Docs.** Note in docs/DATA_SOURCES.md that UCdatabase ART comparisons need the above-site markup removed, so the 2x pattern is not misread.

## Tests and outputs

- **Tests:** `pytest`: 408 passed (4 min 4 s).
- **Outputs:** no tracked file changed. `git status` shows only `audit/goals_crosscheck/` as new, and `model_data/` is untouched.
- **Commits:** nothing was committed or pushed.

---

# Follow-up (2026-10-30): country-specific ART minimum cost

Recommendation 1 above has been applied. No other parameter changed. Nothing is committed.

## What changed

**Rule.** In `audit/batch4b_art_check.py`, a country's ART cost per patient-year is now floored at the higher of two values:

- **(i)** The country's ARV drugs plus one viral load test a year, from the Stover HIV unit cost database (Stover et al. 2026, PLOS Glob Public Health 6(10):e0007360; github.com/JGStover/HIV-Unit-Costs). The source is `datasets/Goals/Unit costs 11april2025.xlsx`, items "Adult ARVs" and "Viral load test". Every row used is `Year` 2024.
- **(ii)** The global first-line price used before, $57.08 (TLD + one viral load).

The $50-600 gate still applies afterwards. The 400.37 GHCC-based value is not touched (see the end of this section).

**Pipeline.** `batch34_inputs.py --art-full` copies the result into `model_data/country_inputs.csv`, and `prepare_model.py --precompute-only` rebuilds the All Countries files. The new rows were spliced in for the five affected countries and the deaths draw columns; every other row is byte-identical to before (a fresh precompute differs only by float rounding of at most 5e-15 relative).

**Deflator.** 2024 US$ → 2023 US$ × 0.97135, from US CPI-U annual averages (BLS, FRED series CPIAUCNS): 2023 = 304.702, 2024 = 313.689. South Africa's price is 2025 US$ × 0.94644 (2025 = 321.943; BLS has no October 2025 value, so that average is built from 11 months).

**Why (ii) is kept.** Rule 3 says only countries below their new minimum may change. South Africa's new minimum ($45.55) is below its current $57.08, so dropping (ii) would have lowered South Africa. With (ii) kept, South Africa is the only country where (ii) binds.

## National ARV prices

| Country | Database ARVs, 2023 US$/yr | National price, 2023 US$/yr | Used | Source |
|---|---|---|---|---|
| ZAF | 107.82 (UMIC default, 111 in 2024 US$) | **33.89** (TLD) | national | NDoH contract HP13-2025ARV, Contract Circular Version 2 (Addendum 5, 4 May 2026), items 13 and 23 (TLD 84/90 and 28/30) |
| NAM, DOM, MUS, NER, IDN | 107.82 / 107.82 / 107.82 / 48.57 / 377.48 | not found | database | Global Fund PQR could not be reached: the PQR site is interactive only, and the Global Fund data-service API returned "The request is blocked". No national price was guessed. |

**How the South Africa figure was built.**
- Volume-weighted price per tablet over all 15 TLD awards (quantity awarded × tablets per pack): R2.0937, of which ex-VAT R1.8206.
- The circular says "All prices are inclusive of 15 % VAT" and "on a delivered basis". VAT was removed because the database prices carry no tax.
- × 365 tablets a year, ÷ 17.8782 ZAR per US$ (2025 average, Federal Reserve H.10, FRED AEXSFUS), × 0.94644 to 2023 US$ = **$33.89 a year**.
- Cross-check: the Global Fund PPM reference price list (Q1 2026) gives TLD at $2.80 per 30-pack, $33.60 a year (EXW).

**Concept caveat.** The national figure is TLD only. The database's "Adult ARVs" may include some second-line regimens. It doesn't matter here, because South Africa stays at $57.08 either way.

## Countries that change (5 of 71)

| Country | Old cost | New minimum = new cost | Old / new range (lo-hi) | Source of the new minimum |
|---|---|---|---|---|
| DOM | 57.08 (old floor; observed 51, Optima B2 2022) | 119.48 | 57.08-400.37 / 119.48-400.37 | database ARVs 111 + VL 12 (2024 US$, UMIC, Global Fund procurement data) |
| NAM | 57.08 (old floor; observed 42, GHED 2019) | 119.48 | 57.08-400.37 / 119.48-400.37 | same |
| MUS | 108.29 (observed, GHED 2019) | 119.48 | 108.29-400.37 / 119.48-400.37 | same |
| NER | 57.08 (old floor; observed 29, GHED 2023) | 60.22 | 57.08-400.37 / 60.22-400.37 | database ARVs 50 + VL 12 (2024 US$, low income) |
| IDN | 356.01 (GHCC 400 × WPR ratio 0.89) | 415.74 | 356.01-400.37 / 415.74-415.74 | database ARVs 388.61 + VL 39.39 ("Indonesia country validation") |

South Africa is unchanged at $57.08 (new minimum $45.55).

**South Africa's $57 floor is kept on purpose.** Its national tender (NDoH HP13-2025ARV) puts drugs plus viral load at $45.55, so $57 already sits above its real drug cost and stays conservative. Every other country was already at or above its new minimum.

**Indonesia** now sits above the 400.37 GHCC-based value, because the floor is applied after the min() of the two measures. Its high value moves up to $415.74 with it.

## The $400 GHCC-based values: not changed, listed as conservative

16 countries use 400.37, the GHCC regional-median site cost × 1/(1 − 0.45): AZE, BLZ, BOL, GTM, GUY, HND, HTI, JAM, KGZ, LBR, MDG, MNG, NGA, NIC, SLV, VEN. The rule takes the lower of that and either observed spending or the regional ratio, and here 400.37 is the lower one, so it is a ceiling the countries sit on, not a gate.

**The 11 flagged in check A:** BOL, GTM, HND, NIC, GUY, HTI, KGZ, LBR, MDG, MNG, NGA. These are still more than 2x the Stover bundle on the site-equivalent basis. (Correction, 30 Oct: the five others at 400.37, AZE, BLZ, JAM, SLV and VEN, are within 2x on that basis, so the earlier text that called the 11 "the countries on 400" was incomplete.)

Against the Stover database the 11 are 3.6-5.3x the commodity bundle. So in these countries the model probably counts fewer people losing ART per dollar than a lower cost would give. That is conservative for deaths.

Note on the earlier wording: this section earlier called 400 "the $400 gate". The gate is $50-600.

## Checks

**Tests.** `pytest`: 408 passed. No test was edited.

**`audit/checks.py --full`.** 88,161 of 88,161 checks pass, with the same 6 known warnings. `checks_summary.csv` is identical to before.

In `checks_results.csv`, 270 rows changed in their value/detail text only. They all belong to the five affected countries or the ALL totals: IDN 128, MUS 119, ALL 12, NER 5, DOM 3, NAM 3.

**Snapshot.** Compared with `audit/merge/snapshot_chipmunk.csv`: 8,069,220 values, of which 18,632 differ. Every difference is explained:

| Where | Values | Explanation |
|---|---|---|
| IDN | 6,948 | ART cost up 17% → fewer people losing ART → fewer deaths |
| MUS | 6,766 | see the Mauritius note below |
| DOM | 3,071 | central unchanged; draws only (see below) |
| NAM | 1,453 | central unchanged; draws only |
| NER | 280 | central unchanged; draws only |
| `ALL|<preset>` rows | 17 each × 6 presets | sums of the precomputed files: deaths, their ranges, `people_lost`, `people_lost_HIV`, HIV infections |
| `FILE|` hashes | 12 | the 12 All Countries files that changed |

**What moved inside the affected countries.**
- Only the HIV lines (`hiv_art`, `hiv_prev`): units lost, unit cost, deaths, infections and their ranges, plus the HIV bucket, totals, deaths-after-2030 and card columns.
- No money column moved. The aid-lost, replacement and fiscal columns are identical.
- `hiv_prev` deaths move because deaths from new infections are weighted by ART coverage after the cut ([health_model.py:1283-1287](../../health_model.py#L1283-L1287)).

**Unchanged.** No other country, and no PROJ row, changed. America First MOUs is unchanged because none of the five countries has an MOU schedule.

The 12 rows found only in the old snapshot are the " 2" duplicate files deleted in 20938a5, as in the previous comparison.

**Why DOM, NAM and NER keep their central values.** Their ART loss is set by the donor-funded pool cap: people covered × external share × the share of money lost. That figure doesn't depend on unit cost while aid buys more than the pool. Only draws near the cap move, so only the ranges shift.

**Why Mauritius goes up.** Mauritius's people losing ART rises from 42.5 to 48.5 when its cost rises. Its ART aid now buys slightly fewer people than the pool, so `_units_lost` ([health_model.py:641](../../health_model.py#L641)) switches from the capped branch (pool × share of money lost) to the plain branch (money lost ÷ cost).

The plain branch counts the linked testing-and-care money in "money lost", while the cap test uses treatment money only (audit I-09). So the two branches differ at the switch point by the ratio of all money to treatment money. This is existing model logic, not something this change introduced; the change only moves Mauritius across the switch point. The effect is +6 people and +1 death.

**Methods page.** `views/4_Methods.py`, HIV treatment row: the floor text is rewritten and cites the database. The page renders with no exceptions (Streamlit AppTest).

Wording updated to match:
- the comment at [health_model.py:592-597](../../health_model.py#L592-L597);
- the `uc_art_mult` source text in `model_params.csv` (values unchanged);
- the docstring of `audit/batch4b_art_check.py`.

**Stale docs, not edited.** `docs/SPEC.md` (lines 69 and 300-318) and `docs/DATA_SOURCES.md:146` describe tomato's Batch 5+6 floor of $190.84, which chipmunk does not use. They were already out of date before this change.

## Full US Exit, before → after

Dashboard defaults: no government replacement, sudden cut, death-rate trend on, 400 draws. Full table: `art_floor_before_after.csv`.

| Country | ART cost | People losing ART / yr (range) | Extra deaths 2026-30 (range) |
|---|---|---|---|
| DOM | 57.08 → 119.48 | 23,367 (20,145-33,246) → 23,367 (20,085-35,264) | 4,984 (3,830-8,319) → 4,984 (3,871-8,618) |
| IDN | 356.01 → 415.74 | 13,373 (11,286-18,509) → 11,451 (10,086-15,850) | 30,985 (18,943-41,385) → 30,621 (18,643-40,916) |
| MUS | 108.29 → 119.48 | 42.5 (18-53) → 48.5 (18-56) | 23.4 (16.8-30.1) → 24.5 (16.6-31.1) |
| NAM | 57.08 → 119.48 | 70,016 (60,831-80,055) → 70,016 (60,584-79,394) | 15,608 (11,933-24,265) → 15,608 (11,933-24,266) |
| NER | 57.08 → 60.22 | 339 (295-381) → 339 (295-381) | 33,335 (23,408-47,560) → 33,335 (23,408-47,560) |
| **All 70 countries** | | **4,563,706 → 4,561,791** (−1,915; no all-country draw total exists for ART alone) | **1,777,774 (1,358,188-2,444,614) → 1,777,411 (1,357,886-2,443,985)** (−363) |

### Headline cards

| Country | Aid Lost | People Losing a Service | Largest Coverage Drop | Extra Deaths |
|---|---|---|---|---|
| DOM | $18.3M → same | 44K (incl. 23K people who stop ART) → same | HIV Treatment 65% → 38% → same | 5.0K (3.8K to 8.3K) → 5.0K (3.9K to 8.6K) |
| IDN | $32.2M → same | 331K → 330K (incl. 260K bednet users) | HIV Treatment 48% → 46% → **Mother-to-Child Transmission 64% → 62%** | 31K (19K to 41K) → same |
| MUS | $96K → same | 3.5K → same | TB Treatment 65% → 62% → same | 23 (17 to 30) → 25 (17 to 31) |
| NAM | $56.8M → same | 83K (incl. 70K people who stop ART) → same | HIV Treatment 95% → 63% → same | 16K (12K to 24K) → same |
| NER | $21.7M → same | 2.81M → same | Bednets 89% → 79% → same | 33K (23K to 48K) → same |

In Indonesia the largest coverage drop now comes from Mother-to-Child Transmission. HIV Treatment's 2030 drop shrinks to under 2 points, so it is no longer the largest.

**All Countries page cards (Full US exit).** No card changes at the precision shown:
- Aid Lost per Year: $3.96B (net $3.96B)
- People Losing a Service per Year: 68.36M (exact: 68,359,823 → 68,357,908)
- HIV and TB Treatment Lost per Year: 4.89M
- Children Missing Vaccines per Year: 1.54M

Underlying sums: HIV people lost 4,674,246 → 4,672,330; HIV deaths 938,069 → 937,706.

**Script.** `audit/goals_crosscheck/art_floor_before_after.py <before_dir>`, run against copies of the pre-change files, which are kept in the session scratchpad.
