# World Bank GRPH 2025 cross-check and double-counting audit

**Review only. No model code, parameter, input, test, baseline or dashboard file was changed.** Everything in this
folder is new: the review, the Appendix 4 extraction, five analysis scripts and their CSV outputs.

Source: `datasets/WorldBank_GRPH_2025_At_a_Crossroads.pdf` (gitignored), Kumar A, Gabani J, Marino A, Mieses Ramirez
JC, Eozenou PH-V, *At a Crossroads: Prospects for Government Health Financing Amidst Declining Aid*, World Bank
Government Resources and Projections for Health (GRPH) Series, November 2025, 79 pages. Page numbers below are the
report's printed page numbers. Code references are `file:line` on branch `tomato` at commit d582f2d.

Branch: `tomato`. Date of review: 18 October 2026.

---

## Step 0: the source file

- `datasets/content.pdf` opened with pypdf: page 2 reads "At a Crossroads: Prospects for Government Health Financing
  Amidst Declining Aid / Government Resources and Projections for Health (GRPH) Series / Anurag Kumar, Jacopo Gabani,
  Alberto Marino, Julio Cesar Mieses Ramirez, and Patrick Hoang-Vu Eozenou / November 2025"; page 3 is the World Bank
  copyright page; PDF metadata: Author "Anurag Kumar", Company "WBG", created 2025-11-19. **Confirmed.**
- Renamed with `mv` to `datasets/WorldBank_GRPH_2025_At_a_Crossroads.pdf`. `datasets/` is gitignored
  (`.gitignore:23`), so neither the PDF nor `datasets/MANIFEST.md` is committed.
- One line added to `datasets/MANIFEST.md` (Files table): path, producer (World Bank GRPH), report date (November
  2025), contents (Appendix 4 pp. 74-79, Table A2.3, Box 2), units (**2024 US$ per capita; population in
  thousands**; DAH from OECD CRS sector codes 120-130, not IHME), "Used for cross-checks only".

### Definitions in the report that matter for every comparison

| Term | Report definition | Where |
|---|---|---|
| GHE = PHE | Government budget transfers + compulsory social health insurance + **on-budget DAH** (SHA 2011); executed budgets from >5,000 budget documents; central + subnational + SHI | p. 17 notes 1 and 4; p. 64 |
| Off-budget DAH | Aid not channelled through government ministries, departments or agencies; OECD CRS, sector codes 120-130, flow codes 11, 13, 30; recipient-country-tagged only (no regional or global programmes); 2024 = 2023 level in real terms | p. 17 note 5; p. 34 fn 21; p. 36 note 1; p. 65 |
| Projection of GHE | Health's share of **post-interest GGE** held at its 2024 level, so GHE per capita grows at the IMF WEO (October 2025) post-interest GGE per capita growth rate | p. 17 note 2; p. 32 fn 20; p. 66 eq. [6] |
| Fiscal class | Cumulative post-interest GGE per capita growth 2024-30: <0 contraction, 0-10% stagnation, >10% expansion | p. 31 (Map 2 note) |
| On-budget aid and GGE | "GGE projections in the IMF's World Economic Outlook already factor in a decline in grant revenue"; the on-budget part of the DAH decline "is already reflected in the GHE outlook" | p. 35 fn 26 |
| WHO Progress benchmark | Stenberg et al. 2017 progress scenario, income-group estimates (2014 US$) converted to constant 2024 US$ per capita with country-specific prices, exchange rates and 2030 population; "around $60 per capita" in LICs and "at least $90" in LMICs; a minimum, not a target | p. 21; p. 22 note 1; p. 26 note 1-2 (the Appendix 4 table notes say "Stenberg et al. 2014", pp. 75 and 78, an inconsistency in the report) |
| WHO government gap | benchmark - PHE - off-budget DAH (verified below) | Appendix 4 |
| Interest | Interest payments as a share of **GGE** (not revenue) | Box 2, p. 32 |

---

## Part 1: extraction of Appendix 4

**Files.** `audit/crossroads/extract_appendix4.py` -> `audit/crossroads/wb_grph_appendix4.csv`
(columns: country, iso3, income_group, year, population_thousands, gge_pc, phe_pc, offbudget_dah_pc,
who_benchmark_pc, who_gov_gap_pc, page).

**Result.** 207 rows = 69 countries x 3 years (2018, 2024, 2030); 22 low-income (Table A4.1, pp. 74-75) and 47
lower-middle-income (Table A4.2, pp. 76-78). Every country has exactly three rows.

**Spot checks against the PDF text** (all match):

| Country, year | Page | Population | GGE | PHE | Off-budget DAH | Benchmark | Gap |
|---|---|---|---|---|---|---|---|
| Kenya 2024 | 77 | 56,433 | 492 | 19.6 | 12.3 | 87 | 55 |
| Mozambique 2024 | 75 | 34,632 | 218 | 13.2 | 17.3 | 51 | 20 |
| Malawi 2024 | 74 | 21,655 | 161 | 11.8 | 16.6 | 58 | 30 |
| Malawi 2030 (first row of a header-less page) | 75 | 25,160 | 158 | 11.6 | 3.8 | 58 | 45 |
| Nigeria 2024 | 77 | 232,679 | 134 | 3.6 | 4.6 | 22 | 13 |
| India 2030 | 77 | 1,525,139 | 1,016 | 32.3 | 0.2 | 84 | 52 |
| Honduras 2030 (first row of a header-less page) | 77 | 11,885 | 1,002 | 145.4 | 3.0 | 106 | -41 |
| Sao Tome and Principe 2024 (name wrapped over three lines) | 78 | 236 | 868 | 91.3 | 22.5 | 174 | 60 |

**Extraction problems found and how they were handled.**
1. Pages 75, 77 and 78 continue the tables with no header row, so the first country name on each was initially
   truncated ("Malawi" -> "i", "Honduras" -> "ras"). Fixed: the parser starts at the page top when no header is
   present and drops the bare page number.
2. "Sao Tome and Principe" is wrapped over three lines before its year; handled by tokenising the whole page.
3. Samoa 2030 has a **blank WHO government gap in the PDF itself** (p. 78); stored as missing.
4. Identity check: the "WHO government gap" column equals benchmark - PHE - off-budget DAH to within rounding
   (<= 1.2) in **every 2018 and 2024 row**, which confirms the column's meaning. In **21 of 69 2030 rows** the
   printed gap differs from that identity by 1.3 to 17.3 (Bhutan -122 vs -139.3; Ethiopia 55 vs 53.7; Malawi 45 vs
   42.6). The report's 2030 gap column therefore does not reproduce from the same row's printed figures; this review
   recomputes the gap from the components wherever it needs a 2030 value.
5. The table notes cite "Stenberg et al. 2014" where the text cites "Stenberg et al. 2017" (report inconsistency,
   not an extraction error).

**Coverage of the model's countries.** The dashboard lists 71 countries (`country_lists.py:8`); 70 have aid in
`model_data/dah_lines.csv` (Panama has none). The report covers **51** of them:
AGO BDI BEN BFA BGD CAF CIV CMR COD DJI EGY ETH GHA GIN GMB HND HTI IND JOR KEN KGZ KHM LAO LBR LSO MDG MLI MOZ MWI
NER NGA NIC NPL PAK PHL PNG RWA SEN SLE SOM SSD STP SWZ TGO TJK TLS TZA UGA VNM ZMB ZWE.

Not covered (20): 14 upper-middle-income (Azerbaijan, Belize, Botswana, Dominican Republic, Fiji, Guatemala,
Guyana, Iraq, Jamaica, Libya, Mauritius, Namibia, Venezuela, **South Africa**), 5 lower-middle-income the report
does not include (Bolivia, Indonesia, Moldova, Mongolia, El Salvador) and Panama (high-income in the model's
income-group column). 18 report countries are not on the dashboard (Bhutan, Congo Rep., Comoros, Cabo Verde,
Micronesia, Guinea-Bissau, Kiribati, Morocco, Myanmar, Mauritania, Sudan, Solomon Islands, Chad, Tunisia,
Uzbekistan, Vanuatu, Samoa, Yemen).

---

## Part 2: fiscal cross-comparison (compare only)

**Script and output.** `audit/crossroads/fiscal_crosscheck.py` -> `audit/crossroads/part2_fiscal_comparison.csv`
(one row per overlapping country, every quantity below).

**Currency.** The model works in constant 2023 US$. Its `inflate()` (`health_model.py:426`) moves study costs between
price years with the US CPI-U annual average (BLS series CUUR0000SA0; `CPI_U` dict at `health_model.py:422`,
2023 = 304.702). The same logic moves the report's 2024 US$ to 2023 US$ by 304.702 / 313.689 = **0.9714**. The 2024
annual average (313.689) is not in the code's table; it is the BLS CUUR0000SA0 2024 annual average (the web lookup in
this session returned the BLS historical table but not the 2024 row itself, so treat the fourth decimal as to be
verified; the ratios below move by less than 0.5% for any plausible value). The report built its constant-2024 series
with GDP deflators and exchange rates (p. 22 note 1), so this is an approximate alignment.

### 2a. Current government health spending per capita

**Model input.** `ghes_2023` in `model_data/country_inputs.csv` = IHME Global Health Spending 1995-2023
(`IHME_HEALTH_SPENDING_1995_2023_Y2026M09D21.CSV`, `ghes_total_mean`, 2023, constant 2023 US$; built at
`prepare_model.py:376`). Per capita here = `ghes_2023` / `sp_pop_totl` (the file's `ghes_pc_2023` is IHME's rounded
integer). IHME's GHES is **domestic** government health spending: in the same file total health spending =
GHES + prepaid private + out-of-pocket + DAH, and that identity holds to 2e-5 across the 71 rows of
`country_inputs.csv` (`the_2023` vs the four components), so DAH, including the part that goes through governments,
is **outside** GHES. The report's PHE **includes** on-budget DAH, SHI and subnational spending (p. 17 note 4).

**Result (51 countries, model / report, both in 2023 US$):** median ratio 1.10, mean 1.20, range 0.38 to 2.66; 38 of
51 inside 0.67-1.5. Because the report's measure contains on-budget DAH and the model's does not, the report's value
should normally be the **higher** one, yet the model is higher in 29 of 51 countries. The two sources differ by data
source (budget-execution documents vs IHME's GHED-based estimates), year (2024 vs 2023), subnational and SHI
coverage (the report lists adjustments for Kenya, Nigeria, Cote d'Ivoire, Burundi, Haiti and Lao PDR, p. 65), and
constant-dollar method.

Flagged (outside 0.67-1.5), with the most likely reason:

| Country | Model GHES pc 2023 | Report PHE pc 2024 (2023 US$) | Ratio | Likely reason |
|---|---|---|---|---|
| Togo | 6.5 | 17.2 | 0.38 | Report PHE includes on-budget DAH and subnational spending (report 2024 off-budget DAH alone is $4.4) |
| Malawi | 5.3 | 11.5 | 0.46 | Report adjusted Malawi upward for subnational spending not in budget documents (p. 64); on-budget DAH large relative to GHES |
| Benin | 7.1 | 14.6 | 0.49 | On-budget DAH and SHI inside PHE; small base |
| Honduras | 78.1 | 123.9 | 0.63 | SHI (IHSS) and subnational coverage differences |
| Tajikistan | 21.1 | 31.8 | 0.66 | Report adjusted Tajikistan for subnational spending (p. 64) |
| Somalia | 3.1 | 1.7 | 1.86 | Report uses WHO GHED for Somalia (p. 64); tiny base, nowcasting |
| Guinea | 13.1 | 6.8 | 1.92 | Different source and year; budget execution vs IHME estimate |
| **Kenya** | 37.9 | 19.0 | 1.99 | Report adjusted Kenya for SHI (p. 65) but its value is half IHME's; county (subnational) health spending coverage is the likely gap. Fiscal-space capacity scales with GHES, so Kenya's capacity (US$21.1M a year) would halve on the report's figure |
| Nepal | 26.7 | 13.4 | 1.99 | Provincial and local spending coverage |
| Timor-Leste | 110.3 | 51.7 | 2.13 | Oil-fund financed budget; year and execution differences |
| Central African Republic | 7.6 | 3.2 | 2.37 | Report adjusted for subnational (p. 64); fragile-state data |
| South Sudan | 3.6 | 1.5 | 2.47 | Report uses WHO GHED for South Sudan (p. 64); hyperinflation conversion |
| **Nigeria** | 9.3 | 3.5 | 2.66 | Report adjusted Nigeria for SHI (p. 65) and subnational (p. 64) yet is far lower; state-level spending coverage in budget documents is the likely gap |

**Donor spending per capita (for Part 5).** IHME DAH 2023 per capita (`dah_2023` / population, all health areas)
divided by the report's off-budget DAH 2024 per capita (2023 US$): median 2.27, range 1.39 to 7.46. Expected
direction: IHME DAH is on- plus off-budget, includes NGO and foundation money, in-kind transfers and development
bank lending, and IHME's recipient-country allocation differs from the CRS's; the report says off-budget DAH is
about two-thirds of total DAH (p. 35 fn 27), which alone explains a ratio of 1.5. Levels of the two DAH series are
not comparable; only percentage changes are (used in Part 3).

### 2b. Fiscal outlook

**How each government response computes available money** (`health_model.py`):

| Option (dashboard label) | Money available in year t | Code |
|---|---|---|
| No Government Replacement | 0 (the default in every precomputed file; `scenarios.py:56`) | `response()` 920-928: `want = 0` |
| Replace a Set Share | theta x that year's gross loss (slider default 25%, `model_section.py:441`), capped at fiscal-space capacity when "Cap Replacement at Fiscal Space" is on (default on) | 920-928 |
| As Much as Fiscal Space Allows | min(gross loss, capacity); always capped | 920-928 |
| Gradual Budget Increase | extra percentage points of the government budget x total government spending, where total government spending = GHES 2023 / health's share of government spending (WDI `SH.XPD.GHED.GE.ZS`, else IHME GHES / IMF WEO GGE), limited by the room to the Abuja 15% ceiling, times `(1 + budget_growth x WEO nominal GDP growth)^t` (budget_growth = 0 by default); **not** capped at fiscal-space capacity | `health_budget()` 1476, `gov_add_from_points()` 1529, `budget_growth_factors()` 1519; total replacement `budget_t = min(R_t + gov_add, G_t)` at 930 |
| Hypothetical best case (triage) | not a money rule: the same budget allocated to the lines with most deaths averted per dollar first | `allocate()` 963-983 |

Capacity (`fiscal_space()`, 322-351) = GHES 2023 x max(0, strong-year growth p75 (or p90) - max(median growth, 0))
x debt-stress factor (1 at interest <= 10% of revenue, falling linearly to 0.25 at 50%+). It is one year's "surge"
above typical growth, held flat for 2026-2030.

**Report's method.** PHE grows at the post-interest GGE per capita rate (p. 66 eq. [6]), so PHE 2030 / PHE 2024 - 1
**is** that country's cumulative post-interest GGE growth and gives its class directly. In the 51 overlapping
countries: 31 expansion, 15 stagnation (BFA GMB LBR MOZ SLE SOM TGO CMR SWZ GHA JOR LAO LSO PNG TLS), 5 contraction
(CAF MWI AGO SEN STP). Median PHE growth 2024-30 = +14% (range -19% to +93%).

**Comparison.** The model's capacity is a yearly backfill margin; the report's figure is the whole increase in the
health budget by 2030 (which must also fund population growth, wages and existing programmes), so the report's
2024-30 increment is an **upper bound** on what could be redirected to replace aid. Ratio = model capacity per capita
per year (p75) / report's 2024-30 PHE increase per capita (2023 US$), 44 countries with a positive increase: median
0.22, mean 0.99, interquartile 0.11-0.93. The model's capacity is **below** the report's increment in 33 countries
(ratio < 0.67), inside the band in 4, and **above** it in 7:

| Country | Report class | Report PHE growth 2024-30 | Report increment pc | Model capacity pc | Ratio | Likely reason |
|---|---|---|---|---|---|---|
| Lao PDR | stagnation | +6% | 0.87 | 1.37 | 1.57 | p75 - median surge of 15% (volatile GHES history) with stress 0.89 |
| Papua New Guinea | stagnation | +3% | 1.55 | 2.73 | 1.76 | report projects near-zero post-interest GGE growth; model surge 5% of a US$47 pc base |
| Burkina Faso | stagnation | +5% | 0.78 | 2.04 | 2.63 | model surge 9%; report near-stagnant GGE after 2022-24 shocks |
| Sierra Leone | stagnation | +2% | 0.10 | 0.38 | 3.89 | report near-flat; model surge 10% x stress 0.65 |
| Jordan | stagnation | +1% | 1.07 | 4.95 | 4.63 | large GHES base (US$119 pc); report post-interest GGE flat |
| Ghana | stagnation | +1% | 0.29 | 2.44 | 8.36 | report: debt restructuring, flat post-interest GGE; model surge 9% x stress 0.62 |
| Timor-Leste | stagnation | +3% | 1.55 | 13.67 | 8.80 | GHES pc US$110 (2x the report's PHE, 2a) x 12% surge |
| CAF, Malawi, Angola, Senegal, Sao Tome | contraction | -2% to -19% | negative | 0.09 to 2.63 | n/a | report projects a **shrinking** health budget; the model still gives a positive backfill margin (Malawi US$0.09 pc, stress 0.36; Angola 0.90; Senegal 0.94) |

Below 0.67 (33 countries) the model is the more conservative: e.g. Uganda (report +55%, increment US$6.70 pc vs
capacity 0.26), Bangladesh (+56%, 5.25 vs 0.09), India (+33%, 7.77 vs 0.51), Kenya (+17%, 3.30 vs 0.37),
Ethiopia (+91%, 4.95 vs 0.46). In these countries the report's outlook would allow more replacement than the
model's "As Much as Fiscal Space Allows" option, if governments chose to prioritise it; the report itself notes the
median LIC's increment covers "less than five percent" of its UHC gap (p. 32).

Also in the CSV, for reference only: IHME's *expected* GHES 2030 / 2023 (`ghes_2030_expected`, built at
`prepare_model.py:384`) is **not used by the model** (no reference outside `prepare_model.py`).

### 2c. Interest burden

Model: `interest_pct_revenue` = IMF WEO October 2026 net interest / revenue, latest actual year
(`fiscal_inputs.py`, `apply()`; every dashboard country has an IMF value). Report: interest / **GGE**, 2024, IMF WEO
October 2025 (Box 2, p. 32). Converting the model's value with the WEO 2024 revenue / expenditure ratio from
`macro_data/<ISO3>.csv`:

| Country | Model, % of revenue (year) | Converted, % of GGE | Report Box 2, % of GGE 2024 | Ratio |
|---|---|---|---|---|
| Malawi | 35.5 (2024) | 22.3 | 22.3 | 1.00 |
| Somalia | 0.6 (2024) | 0.6 | 0.7 | 0.83 |
| Pakistan | 61.3 (2024) | 39.9 | 39.9 | 1.00 |
| LIC median (18 overlap countries) | | 7.3 | 7.5 | 0.97 |
| LMIC median (33) | | 10.7 | 7.3 | 1.47 |

The three named countries match the report exactly once the denominator is aligned, which confirms the model's
series is the IMF's. The LMIC median is higher in the model because the dashboard's LMIC set is weighted to
high-debt countries (Kenya 22.6% of GGE, Nigeria 20.5, Egypt, Pakistan), not because of a definitional gap. Note
that the debt-stress factor's thresholds (10% and 50% of **revenue**) would read differently on a GGE denominator;
Box 2 gives medians of 7.3-7.5% of GGE, i.e. roughly 10-12% of revenue, right at the model's "no stress" threshold.

### Conclusion and recommendation (Part 2)

- **Support.** The interest series is confirmed (2c). The model's fiscal-space capacity is below the report's
  projected 2024-30 health-budget increase in two-thirds of the overlapping countries, so the default "No
  Government Replacement" and the capped options are conservative relative to the report's outlook there.
- **Contradict.** In the report's 5 contraction countries (CAF, Malawi, Angola, Senegal, Sao Tome) and in 7
  stagnation countries the model's capacity exceeds what the report projects (ratio 1.6 to 8.8, or any positive
  value against a shrinking budget). The model's historical-surge rule knows nothing about the forward fiscal
  outlook.
- **Refine.** Government health spending levels differ by more than 1.5x in 13 of 51 countries (both directions),
  including Kenya (2.0x) and Nigeria (2.7x). Because capacity is proportional to GHES, those countries' fiscal
  space inherits the uncertainty.
- **Recommendation (not implemented):** keep IHME GHES as the model input (it is the only series consistent with the
  IHME DAH baseline and the THE identity, and it excludes on-budget DAH, which matters for Part 4 check 1). Add the
  report's PHE 2024 and 2024-30 class as **cross-check columns** in `country_inputs.csv` with a per-country flag
  where the level ratio is outside 0.67-1.5 or the class is "contraction", shown in the fiscal panel. Offer a
  sensitivity switch (constant, default off) that caps capacity at max(0, report's 2024-30 PHE increment / 6) for
  the 51 covered countries. Do not replace any fiscal input.

---

## Part 3: scenario cross-check

**Script and output.** `audit/crossroads/scenario_crosscheck.py` -> `part3_preset_implied_falls.csv`,
`part3_wb_a23_style_all_countries.csv`.

**Report assumptions (Table A2.3, pp. 65-66; note 1-2 on p. 66).** Bilateral DAH only: United States -60%, Germany
-10%, France -25%, United Kingdom -40%; Gavi and Global Fund 0% in real terms; every other donor 0%. Total DAH falls
"approximately 20 percent in 2025", within OECD's 19-33% and close to IHME's 21% (p. 66). Off-budget DAH per capita
then falls about 45% from 2024 to 2030 in the median LIC and median LMIC (p. 35), a larger number because (i) it is
per capita over six years of population growth, (ii) off-budget DAH falls faster than total DAH (p. 35 fn 28), and
(iii) total off-budget DAH is held flat in real terms after 2025 (p. 67).

**Model.** Implied fall = gross aid lost / baseline aid (both 2021-23 average, constant 2023 US$, the four modelled
disease areas only), from the precomputed All Countries files (`model_data/all_countries_<preset>.csv`, default
settings). Percentage changes only; levels are not comparable (CRS vs IHME).

| Preset (dashboard label) | Countries | Baseline US$bn/yr | Lost US$bn/yr | Implied fall, all | Implied fall, 51 report countries | vs report 20% | Deaths 2026-30 (central) |
|---|---|---|---|---|---|---|---|
| US Bilateral Exit + Multilateral Withdrawals (`Full US exit`) | 70 | 10.34 | 3.96 | **38.3%** | 36.4% | 1.9x | 1,928,289 |
| America First MOUs | 16 | 4.35 | 0.70 | 16.1% | 16.0% (15 countries) | 0.8x | 364,893 |
| IHME 2025 preliminary estimates | 70 | 10.34 | 2.89 | 27.9% | 27.2% | 1.4x | 1,432,531 |
| Total-Aid Cuts (OECD) Applied to Health Aid | 70 | 10.34 | 3.24 | 31.3% | 30.5% | 1.6x | 1,760,137 |
| Global Fund & Gavi shortfalls (-20% / -15%) | 70 | 10.34 | 1.02 | 9.9% | 10.3% | 0.5x | 731,380 |
| Combined retreat | 70 | 10.34 | 4.23 | 40.9% | 39.2% | 2.0x | 2,130,765 |
| *Table A2.3 assumptions on the model's cells* (US direct -60%, DE -10%, FR -25%, UK -40%, multilaterals 0) | 70 | 10.34 | 2.08 | **20.1%** | 18.9% | 1.0x | 917,052 |

Reading: the model's baseline is 42% direct-channel (bilateral, NGO, Gates direct, other) and 50% US-sourced
(33% US direct). Applying the report's donor assumptions to the model's own cells reproduces the report's 20% almost
exactly (20.1%), so the two aid databases agree on the donor mix for these diseases. The model's US-exit presets are
1.5-2x deeper because they remove 100% of US bilateral money plus US contributions to WHO, Gavi and UNFPA and 23% of
the US Global Fund share (`scenarios.py:17`, 186-187), whereas the report cuts US bilateral aid by 60% and keeps the
multilaterals whole. The report's ~45% per-capita off-budget decline is not directly comparable: the model holds
population and aid levels fixed over 2026-30, has no population-growth term, and its "direct channels" are not the
report's "off-budget" (on-budget bilateral aid is inside the model's direct channels). Under the Table A2.3-style
scenario the model's direct-channel money falls 47.5% (2.08 / 4.38), the same order as the report's 45%.

**Would a "World Bank GRPH 2025" preset add anything?** It sits between the Global Fund & Gavi shortfalls (10%) and
the IHME 2025 preliminary estimates (28%) and gives about half the headline deaths (917k vs 1.93M). It adds one
thing the current presets lack: a sourced, documented, **multi-donor bilateral** scenario with multilaterals held
whole, which is a useful lower-middle anchor and a direct link to a World Bank publication for a WHO-facing
audience. It does not add a new mechanism (it is a `Scenario` with four `src_direct` entries). **Recommendation:**
add it only as a documented preset labelled "World Bank GRPH 2025 donor assumptions (bilateral cuts; multilaterals
unchanged)", with the caveat that the report's 60% US figure predates the Global Fund and Gavi announcements the
other presets use; otherwise it is adequately represented by the existing IHME and OECD presets.

---

## Part 4: double-counting and consistency audit

**Scripts and outputs.** `audit/crossroads/double_counting_checks.py` -> `part4_units_vs_pools.csv` (every
country x direct line, central run), `part4_bucket_money.csv`, `part4_care_line_contribution.csv`,
`part4_replacement_bounds.csv`, `part4_tb_hiv_overlap.csv`. Effect sizes refer to the Full US exit preset, central
run, No Government Replacement unless stated. Headline reference (`model_data/all_countries_Full_US_exit.csv`):
aid lost US$3,957M a year; 1,928,289 deaths 2026-30; Kenya 112,827; Nigeria 267,231; Mozambique 179,236; South Africa
128,455; Uganda 110,746; India 28,925.

### Check 1: on-budget aid counted twice. PASS (with two Minor notes)

- **Aid lost** is IHME DAH by cell (`dah_lines.csv`), which includes aid that flows through governments.
- **Government money** in every response option is anchored on IHME GHES 2023 (`fiscal_space()` 322-351;
  `health_budget()` 1476-1495), which **excludes** DAH (THE = GHES + PPP + OOP + DAH holds to 2e-5 in
  `country_inputs.csv`; IHME tracks DAH as a separate financing source). No projected government spending series is
  used anywhere: `ghes_2026_expected` / `ghes_2030_expected` (IHME) are built but unused; `budget_growth_factors()`
  (1519) uses WEO nominal **GDP** growth, which does not move with grants, and is off by default
  (`budget_growth` = 0). So no option uses a series that already embeds the fall in on-budget grants while the same
  grants are counted as aid lost. Overlap in the default and capped options: **US$0**.
- Minor note A (Gradual Budget Increase only): total government spending = GHES / health share, where the share's
  denominator (WDI `SH.XPD.GHED.GE.ZS`, i.e. domestic GGHE / GGE; or IMF WEO GGE in the fallback,
  `health_share()` 1443-1474) is **total** GGE including grant-financed spending. After a US exit the on-budget part
  of the lost aid shrinks that base. Using the report's rule of thumb that about one-third of DAH is on-budget
  (p. 35 fn 27) and the report's 2024 GGE per capita: the overstatement of each budget point is about 1.2% in Kenya
  (US$16.6 DAH pc / 3 over US$478 GGE pc), 3.8% Uganda, 5.3% Mozambique, 7.5% Malawi; zero in the default option.
  Severity **Minor**. Proposed fix: none required; document in the Methods page under Gradual Budget Increase, or
  deduct an on-budget share of the gross loss from `gov_spend_usd` when the option is on.
- Minor note B: "Aid Lost as % of Government Health Spending" (`loss_pct_ghes`) uses the domestic-only
  denominator, so it reads higher than a World-Bank-style ratio would (report PHE includes on-budget DAH). Label is
  correct ("government health spending (IHME, 2023)"), no change needed.

### Check 2: replacement capacity. PASS (one Minor design note)

- `budget_t = np.minimum(R_t + gov_add, G_t)` (930): total replacement never exceeds that year's gross loss.
- `response()` (920-928): `min(want, capacity)` when the cap is on or the mode is "max".
- `allocate()` (963-983): pro-rata gives each line `budget x loss_l / total_loss` <= `loss_l` because `budget <= G_t`
  and the `effective()` split conserves money (eff + nonservice = gross for every bucket: `part4_bucket_money.csv`,
  no negative nonservice in 280 bucket-rows); lives-first takes `min(left, loss_l)`. Verified numerically for the
  six focus countries x five option settings (`part4_replacement_bounds.csv`): replaced <= gross in 30 of 30,
  replaced <= capacity in every capped setting, and no line receives more than it lost in any setting.
- Design note: "Replace a Set Share" with the cap **off** and "Gradual Budget Increase" can replace more than the
  fiscal-space capacity (Kenya: capacity US$21.1M a year; uncapped 100% share replaces the full US$277.7M;
  1 point a year of the budget replaces US$271.6M), because they are bounded by a different ceiling (the user's
  choice, or the Abuja 15% room). Documented on the Methods page; the cap defaults to on. Severity **Minor**.
  Proposed fix: none needed; optionally show a "exceeds fiscal space" badge in the fiscal panel when replacement >
  capacity.

### Check 3: channels. PASS

- `prepare_model.py:320` keeps `elim_ch == 0` before anything is summed, as IHME's user guide instructs (DAH
  Database 2026 User Guide pp. 3-4: transfers from Gates, US foundations, Gavi and the Global Fund to other channels,
  between UN agencies, and from bilateral agencies to NGOs and other tracked channels are flagged; example code
  `dah_db[elim_ch == 0]`). Re-run on the raw file: 166,895 of 1,475,413 rows (13.9% of `dah_23`) are flagged and
  dropped; the largest flagged channels in 2021-23 are NGO, WHO, Gavi, UNICEF and BIL_USA, i.e. the transfer copies.
- No programme-area column maps to two lines (`LINES`, `prepare_model.py:98-117`; 0 duplicates), and the mapped
  columns sum to 99.9-100.0% of each disease's IHME total for the 70 countries in 2021-23, so no money is dropped or
  double-mapped. `dah_lines.csv` has no duplicate (country, source, channel, line) cell.
- Within the model a cell's money is cut once (`cuts()` 225-242: donor cut and channel cut combine as
  `1 - (1-x)(1-y)`, never additively).

### Check 4: multilaterals in US-exit presets. PASS

- IHME attributes Global Fund and Gavi disbursements to source donors, so "United States x Global Fund" is a
  separate cell from "United States x Bilateral agency". `Full US exit` and `Combined retreat` cut US direct cells
  100% and the US x Global Fund cell 23%, US x Gavi / WHO / UNFPA 100% (`scenarios.py:17-18`, 186-187); other
  donors' Global Fund money is untouched in `Full US exit`, and in `Combined retreat` other donors' cells get their
  own OECD cut (the US is skipped in that loop, 199). The US share of the Global Fund channel in the 70 countries is
  27% of Global Fund money; it is cut once, by 23%.
- `Global Fund & Gavi shortfalls` is a channel cut for all sources with no US exit (206; comment at 204-205), so the
  US's part of the Global Fund fall is inside the 20% and is not also cut as US money. `tests/test_i07.py::
  test_us_gavi_money_is_cut_once` covers the Gavi case.
- `Custom` can combine a US multilateral cut with a channel cut, but multiplicatively (241), so a cell is never cut
  more than 100% and the overlap is the intended compound cut, not a double count.

### Check 5: MOU countries. PASS

`America First MOUs` does not set `src_direct["United States"]` (only `Full US exit` and `Combined retreat` do,
186); `cuts_by_year()` (244-258) replaces the US direct-channel cut with the country's schedule
(`us_direct_path_by_country`), and the only `pair` entries are US x multilateral channels, none of which is a
direct channel, so no schedule cell also carries a generic US cut. `tests/test_mou.py::
test_applied_us_bilateral_cut_equals_schedule` and `test_nothing_rescales_a_schedule` confirm. The preset covers the
16 group-A countries (BWA BDI CMR SWZ ETH KEN LSO LBR MDG MWI MOZ NGA RWA SLE SSD UGA).

### Check 6: services. PASS on every sub-check; one Minor overlap, one definitional note

- **ART vs HIV testing & care.** `hiv_care_ct` has no units of its own (`LINKED`, 49); kappa x its lost money adds to
  the ART line's money (1042-1044) and the ART line is capped at people covered (1052-1054). People on ART from
  testing-and-care money are therefore counted once, on the ART line. Effect of that design (kappa = 0.5 vs 0):
  ART people lost 4,863,492 vs 4,156,094 a year (+707k, +17%) and ART deaths 933,698 vs 795,657 (+138k, 7.2% of the
  headline); Kenya +93k people / +17.6k deaths; Nigeria +128k / +25.2k; Mozambique +99k / +19.2k; Uganda +64k /
  +12.4k; India +7.5k / +1.4k; South Africa -7.9k / -1.5k (its care money is cut proportionally less than its
  treatment money, so blending lowers the share lost). This is the labelled assumption `hss_kappa` (audit I-09), not
  a double count.
- **PMTCT vs ART.** Women on PMTCT are removed from the ART pool (`covered = max(covered - pmtct_covered, 0)`, 1021)
  and their infants' infections are counted under PMTCT only (comment at 1150-1151 "Infant infections from PMTCT are
  already counted under PMTCT"). `tests/test_hiv.py::test_pmtct_women_outside_art_pool`. PASS.
- **TB-HIV.** TB deaths use the country's HIV-positive share of TB and a case-fatality blend at **baseline** ART
  coverage (`per_unit_levels()` 562-564, `lives()` 1114-1116); ART deaths use the post-ART-stop hazard, which
  includes TB deaths among people off ART. A person who loses both ART and TB treatment could be counted on both
  lines. Upper bound = TB deaths x HIV-positive share x share of PLHIV off ART (`part4_tb_hiv_overlap.csv`): Kenya
  <= 1,082 of 112,827 (1.0%); Nigeria 865 (0.3%); Mozambique 2,664 (1.5%); South Africa 1,280 (1.0%); Uganda 783
  (0.7%); India 3. Severity **Minor**. Proposed fix: in `lives()`, scale the HIV-positive share of TB deaths by
  (1 - share of PLHIV off ART) in that year, or document the overlap as < 2%.
- **Malaria lines.** Bednets and spraying combine into one vector-control coverage `1 - (1 - ITN)(1 - IRS)`
  (`vc()` 767) so protection is never counted twice in deaths; each line is capped at its own people covered
  (`tests/test_malaria.py::test_each_vector_line_capped_at_its_own_coverage`); treatment is a separate multiplicative
  step. PASS. Definitional note: the "People Losing Service" total adds person-years across lines, so one person who
  loses both a net and spraying counts twice in that total (as the tooltip's unit definitions imply); not a deaths
  issue.
- **Unspecified-money split.** `unspec_shares()` (846-855) renormalises the five purpose shares; in
  `country_inputs.csv` they sum to 1.000 in 70 of 71 rows and the exception is Panama (no shares, no aid, never
  run). PASS.
- **Overhead once (L-05).** Above-site money is handled in exactly one place per line: ART and TB site costs are
  grossed up by `1 / (1 - asd_share)` (458, 504-505), and the separate HSS lines plus the systems share of
  unspecified money go to `nonservice` with no service effect (`hss_service_share` = 0; 885-907). Nonservice money is
  15% of the HIV gross loss, 54% of TB, 33% of malaria, 0% of immunization. The same overhead is not both marked up
  and lost as a service. PASS (conservative direction, as the logic review recorded).
- **Caps.** Units lost never exceed people currently covered on any of the 70 x 10 country-lines
  (`part4_units_vs_pools.csv`: 0 breaches), nor the donor-funded pool (covered x external share): 0 breaches. On
  3 country-lines (all ART) units lost exceed the people the line's **own** treatment money pays for because
  testing-and-care money is added (I-09 design), but they stay inside the pool.

### Check 7: country count. ISSUE, Minor

- Data: 71 countries in `country_lists.py` (including Panama); 71 rows in `country_inputs.csv` and
  `country_profile.csv`; 70 in `dah_lines.csv` and in every `all_countries_<preset>.csv` (`run_all()` 1571 runs
  only countries with aid cells). Panama's own page shows "has no recorded HIV, TB, malaria or vaccine aid in
  2021-2023" (`model_section.py:777`). The All Countries page says "Aid Lost per Year, 70 of 71 Countries"
  (`model_section.py:1760`). Consistent.
- Inconsistent wording: `SCOPE_NOTE` (`model_section.py:1724`) says "The **71** dashboard countries receive about
  **72%** of the HIV, TB, malaria and vaccine aid", while `docs/EXPLAINER.md:65` and `:646` and
  `audit/slide_numbers.md:19` say "**70** countries ... **71.5%**", and `views/4_Methods.py:425` and `:985` say 70.
  Numerically the same (Panama adds nothing), but the two counts and two percentages appear side by side on the
  dashboard and in the explainer. Effect on results: none. Proposed fix: one sentence everywhere: "70 countries with
  aid (71 listed; Panama has none) receive 71.5%".

### Check 8: other mixed definitions found

| # | Finding | Evidence | Effect | Severity | Proposed fix |
|---|---|---|---|---|---|
| 8a | Fiscal-space capacity scales with IHME GHES, which differs from the report's PHE by >1.5x in 13 of 51 countries (Kenya 2.0x, Nigeria 2.7x; Malawi, Togo, Benin < 0.5x) | Part 2a; `fiscal_space()` 322 | Headline unaffected (default = no replacement). "As Much as Fiscal Space Allows": Kenya replaces US$21.1M a year (deaths 104,123 vs 112,827); on the report's GHES this would be about US$10.6M | Minor (not a double count; a level uncertainty) | Cross-check flag (Part 2 recommendation) |
| 8b | Model capacity is positive in the report's 5 contraction countries (Malawi US$0.09 pc, Senegal 0.94, Angola 0.90, CAF 0.45, STP 2.63) and 1.6-8.8x the report's increment in 7 stagnation countries | Part 2b | Only with a replacement option on; Malawi's capacity is 1.1% of its loss, so the headline is unaffected | Minor | Sensitivity switch (Part 2) |
| 8c | Nominal MOU amounts vs a 2023 US$ reference (switch `mou_deflate` = 0 by default) | `scenarios.py:89-112`; Methods | MOU preset only; documented, labelled | Minor, known (L-35) | none |
| 8d | Gradual Budget Increase growth uses **nominal** US$ GDP growth on a constant-2023 budget (`budget_growth` default 0) | `budget_growth_factors()` 1519; `fiscal_inputs.py` `weo_nominal_growth` | none by default; with budget_growth = 1 it overstates real growth by US inflation | Minor, known (Batch 7 item 10 labels it the upper end) | none |
| 8e | Interest thresholds are on **revenue**; the report's Box 2 and most fiscal-space literature use **GGE**; medians of 7.3-7.5% of GGE correspond to about 10-12% of revenue, exactly at the model's "no stress" threshold | 2c; `STRESS_FREE_PCT` 319 | sensitivity of capacity only | Minor | state the GGE equivalent in the Methods text |
| 8f | Report inconsistency: Appendix 4 notes cite Stenberg 2014; text cites Stenberg 2017; 21 of 69 printed 2030 gaps do not equal benchmark - PHE - DAH | Part 1 | none on the model | n/a | compute the gap from components |

**Overall:** no Critical or Major double counting found. The code counts each dollar once (channel elimination,
cell-level cuts, conserved money split, replacement bounded by loss and capacity, service caps). The two Minor
overlaps (TB-HIV, < 2% of a country's deaths; Gradual-option budget base, <= 7.5% of a budget point) and the 70/71
wording are the only issues.

---

## Part 5: UHC financing gap indicator (design only)

**Script and output.** `audit/crossroads/uhc_gap.py` -> `part5_uhc_gap.csv`.

**Report's measure.** Gap = benchmark - (PHE + off-budget DAH) per capita; gap share = gap / benchmark (p. 26 note 1,
p. 38 note 1; Appendix 4 "WHO government gap", confirmed to rounding in every 2018 and 2024 row).

**Illustration, Kenya and the report's focus countries.** Model side in 2023 US$: government = IHME GHES 2023 per
capita (`ghes_2023` / `sp_pop_totl`); donor = IHME DAH 2023 per capita, all health areas (`dah_2023`); benchmark =
the report's per-country WHO Progress value x 0.9714; after Full US exit = minus the model's gross aid lost per
capita (no replacement) or minus the net loss after "As Much as Fiscal Space Allows" (central run). Report side in
2024 US$ from Appendix 4. South Africa has no benchmark (upper-middle-income): not shown.

| Country | Benchmark (2023 US$) | Gov pc | Donor pc (IHME) | Aid lost pc | Gap share before | After, no replacement | After, fiscal space | Report 2024 | Report 2030 (proj.) |
|---|---|---|---|---|---|---|---|---|---|
| **Kenya** | 84.5 | 37.9 | 16.6 | 4.9 | 35% | 41% | 41% | 63% | 66% |
| Nigeria | 21.4 | 9.3 | 8.3 | 1.4 | 18% | 24% | 22% | 63% | 72% |
| Mozambique | 49.5 | 13.8 | 33.7 | 8.5 | 4% | 21% | 20% | 40% | 59% |
| Uganda | 54.4 | 10.0 | 23.2 | 5.9 | 39% | 50% | 49% | 54% | 55% |
| India | 81.6 | 32.8 | 1.0 | 0.03 | 59% | 59% | 59% | 71% | 61% |
| South Africa | none | 325.7 | 15.9 | 7.1 | not shown | not shown | not shown | n/a | n/a |
| DR Congo | 67.0 | 4.1 | 12.9 | 1.3 | 75% | 77% | 76% | 83% | 86% |
| Liberia | 72.9 | 10.5 | 28.6 | 3.9 | 46% | 52% | 50% | 64% | 72% |
| Viet Nam | 82.6 | 86.8 | 2.5 | 0.3 | -8% | -8% | -8% | 27% | -3% |
| Burkina Faso | 57.3 | 22.1 | 21.9 | 1.3 | 23% | 26% | 23% | 61% | 65% |
| Lao PDR | 59.3 | 10.6 | 16.2 | 0.5 | 55% | 56% | 55% | 63% | 65% |
| Cote d'Ivoire | 74.8 | 35.0 | 17.3 | 2.4 | 30% | 33% | 32% | 50% | 38% |
| Malawi | 56.3 | 5.3 | 35.1 | 8.0 | 28% | 42% | 42% | 51% | 73% |
| Angola | 183.6 | 33.2 | 5.1 | 0.5 | 79% | 79% | 79% | 78% | 81% |
| Senegal | 74.8 | 19.7 | 19.8 | 1.5 | 47% | 49% | 48% | 70% | 78% |
| Ethiopia | 66.1 | 7.6 | 11.3 | 1.0 | 71% | 73% | 72% | 84% | 79% |
| Niger | 57.3 | 6.1 | 12.6 | 0.8 | 67% | 69% | 68% | 78% | 78% |
| Bangladesh | 89.4 | 8.4 | 5.5 | 0.2 | 84% | 85% | 84% | 88% | 82% |

Reading: the model-side gaps are **systematically smaller** than the report's (Kenya 35% vs 63%) because IHME DAH
is on- plus off-budget and 1.4-7.5x the CRS off-budget series (Part 2a), and because IHME GHES exceeds the report's
PHE in Kenya and Nigeria. The **change** caused by the US exit is the meaningful model output: Kenya +6 points,
Mozambique +17, Malawi +14, Uganda +11, Nigeria +6, India 0. The fiscal-space option barely moves it because
capacity is small relative to the loss in these countries (Kenya 8%, Mozambique 9%, Uganda 4%).

**Proposed indicator specification.**

- *Formula.* Gap share = 1 - (G + D - L + R) / B, where G = government health spending per capita, D = donor health
  spending per capita, L = the scenario's gross aid lost per capita, R = government replacement per capita (0 under
  No Government Replacement), B = the minimum benchmark per capita. Report as a percentage of the benchmark with the
  dollar gap underneath; show before and after side by side.
- *Data sources.* G: IHME GHES 2023 (`ghes_2023`) by default, with the report's PHE 2024 as a second line where the
  country is covered (51 countries), because the two disagree by >1.5x in 13 of them. D: IHME DAH 2023
  (`dah_2023`), all health areas, labelled "all donor health aid (IHME)"; show the modelled four-disease baseline
  (`base_usd`) as a sub-line so readers see that L is a subset of D. L and R: the run's `totals["gross"]` and
  `totals["replaced"]`. B: the report's Appendix 4 per-country WHO Progress value (preferred, because it carries
  the report's country-specific price conversion), falling back to the income-group medians (LIC 59, LMIC 84 in
  the extracted table) for covered income groups only.
- *Units and year alignment.* Everything in constant 2023 US$ per person, population = `sp_pop_totl`; the report's
  2024 US$ moved with the model's own `inflate()` logic (CPI-U 304.702 / 313.689 = 0.9714), stated on the panel.
  The aid loss is a 2026-30 average applied to 2023 levels, the same convention as the rest of the dashboard.
- *Coverage.* 51 of the 70 countries with aid have a benchmark. For the 14 upper-middle-income countries (South
  Africa, Namibia, Botswana, Dominican Republic, Guatemala, Iraq, Jamaica, Libya, Mauritius, Venezuela, Azerbaijan,
  Belize, Fiji, Guyana) and the 5 LMICs the report omits (Bolivia, Indonesia, Moldova, Mongolia, El Salvador): the
  Stenberg et al. 2017 and DCP3 (Watkins et al.) benchmarks exist only for low- and lower-middle-income countries;
  the search found no published per-capita minimum UHC cost for upper-middle-income countries except a 2026
  medRxiv preprint (WHO UHC Compendium core interventions, about US$363 per capita in UMICs) that is not
  peer-reviewed and uses a different package, and the McIntyre, Meheus and Rottingen (2017, *Health Economics,
  Policy and Law* 12:125-137) target of government health spending of at least **5% of GDP** (plus US$86 per
  capita, 2012 prices, for primary care in low-income countries), which is a relative target, not a minimum cost.
  Recommendation: show "**not shown** (no published minimum-cost benchmark for upper-middle-income countries)" and,
  optionally, the 5%-of-GDP target as a separate relative indicator labelled as a target. For the 5 omitted LMICs,
  use the LMIC median benchmark from the extracted table, flagged "income-group median".
- *Caveats to print with the indicator.* (1) The benchmark is a **minimum** cost of a core package (p. 21, p. 26
  note 2), not a target, and assumes full efficiency. (2) IHME DAH is defined differently from the report's OECD
  CRS off-budget DAH (on- plus off-budget; NGO, foundation, in-kind and development-bank money; different
  recipient allocation), so model-side gaps are smaller than the report's and the two must not be mixed in one
  number; the report's own 2024 figure is shown for comparison only. (3) The indicator compares **money, not
  services**: a dollar of lost aid is not a dollar of lost services, and government spending counts whatever it
  buys. (4) Government spending year (2023) and the aid loss (2026-30 average) differ. (5) The report's 2030 gap
  column does not reproduce from its components in 21 rows; the indicator uses components.
- *Dashboard fit.* Yes: it is a coverage-and-financing measure with no deaths, so it can sit in the fiscal panel
  ("Can {Country} Fill the Gap?") or the All Countries table as "UHC financing gap vs minimum benchmark: before ->
  after", using only `totals`, two existing input columns and one new benchmark column. It should not be shown as
  a headline because levels depend on the DAH definition; the **change** in the gap is the defensible output.

---

## Files in this folder

| File | What |
|---|---|
| `CROSSROADS_REVIEW.md` | this review |
| `extract_appendix4.py`, `wb_grph_appendix4.csv` | Part 1 extraction (207 rows) |
| `fiscal_crosscheck.py`, `part2_fiscal_comparison.csv` | Part 2 (51 countries) |
| `scenario_crosscheck.py`, `part3_preset_implied_falls.csv`, `part3_wb_a23_style_all_countries.csv` | Part 3 |
| `double_counting_checks.py`, `part4_units_vs_pools.csv`, `part4_bucket_money.csv`, `part4_care_line_contribution.csv`, `part4_replacement_bounds.csv`, `part4_tb_hiv_overlap.csv` | Part 4 evidence |
| `uhc_gap.py`, `part5_uhc_gap.csv` | Part 5 illustration |

All scripts are read-only with respect to the model (they import `health_model` and `scenarios` and read
`model_data/`; they write only into this folder).
