# Findings for the WHO presentation (Thursday 22 October 2026)

Analysis engine: the dashboard model in this repository, run in memory (no model code or data file was changed; every
script is read-only with respect to the model and lives under `audit/<topic>/` with a `RESULTS_<topic>.md` beside it).
Branch: the work was done on `tomato`, which contains everything on `claude-work` plus 113 later commits, including the
reallocation audit (`audit/reallocation/RESULTS_2027.md`) these analyses extend; `claude-work` has none of that audit, so
the scripts would not run there unchanged.

Conventions (as in `audit/reallocation/run_reallocation_2027.py`, whose helpers the scripts import): America First MOUs
preset; **US bilateral MOU schedule only** unless stated (the preset's US exits from WHO, Gavi, UNFPA and 23% of the
Global Fund switched off in memory); dashboard defaults (no government response, sudden path, death-rate trends on);
400 draws, seed 7; central run with paired 2.5-97.5 ranges; the 15 countries of the reallocation sheet (South Sudan
excluded except where noted). People on service are the model's full-cost equivalents after the 15% continuity
assumption: ART patient-years, TB courses, bednets, people sprayed, malaria cases treated, children vaccinated.

Reconciliation: the full preset reproduces `model_data/all_countries_America_First_MOUs.csv` exactly (364,893 deaths
2026-30 over 16 countries; 356,197 without South Sudan, the figure in RESULTS_2027.md); the bilateral-only baseline is
189,629 deaths, 455,448 ART patient-years lost in 2027 and 6,914,369 people losing a service in 2027, the same as
RESULTS_2027.md table 4a. Every other number below is a change against one of those baselines.

Labels: **[world]** = a finding about countries and donors; **[model]** = a finding about how the model represents them,
which must not be presented as a policy result.

---

## (a) The findings, ranked by how surprising and defensible they are

### 1. [world, computed with the model] Reallocating the same 2027 money keeps up to 174,000 ART patient-years; the team's ceilings move it the other way

**Headline.** Holding the 15-country 2027 MOU total fixed (US$2,470M) and cutting no country more than 30% below its
signed amount, the allocation that protects ART keeps **173,854 more ART patient-years in 2027** (range 119,476 to
232,881), 38% of the 455,448 the signed amounts lose, with total people on any service unchanged (+4,469) and 23,457
fewer deaths 2026-30. The team's Low, Medium and High ceilings lose 36,000 to 50,000 more ART patient-years than the
signed amounts.

**Mechanism.** A nominal MOU dollar buys ART where US money is HIV treatment money (Botswana, Eswatini, Lesotho,
Malawi, Kenya, Cameroon, Mozambique, Nigeria: 1,000-1,400 patient-years per US$1M) and almost none where it is
malaria money (Madagascar 0, Liberia 111, Sierra Leone 272 per US$1M), so a bounded move from the second group to
the first keeps ART while bednets lost in the malaria countries are offset by bednets kept in Nigeria and Cameroon.

**Slide table** (change versus the signed 2027 amounts; + = kept on service or averted; `audit/coverage_realloc/RESULTS_coverage_realloc.md` Step 2 and Step 3b)

| Allocation of the same US$2,470M | ART patient-years kept (range) | ART coverage pp | People on any service kept | Bednets kept | Deaths averted 2026-30 (secondary) |
|---|---|---|---|---|---|
| Team Low Ceiling | -35,888 (-49,446 to -19,456) | -0.32 | +5,802 | -14,890 | -2,327 |
| Team Medium Ceiling | -45,695 (-65,397 to -19,867) | -0.41 | -212,723 | -239,503 | -2,073 |
| Team High Ceiling | -49,602 (-72,312 to -17,925) | -0.45 | -424,350 | -450,721 | -707 |
| ART-protecting, no country cut >10% | +91,295 (+70,035 to +119,897) | +0.82 | +23,446 | +53,704 | +12,831 |
| ART-protecting, no country cut >20% | +138,949 (+99,880 to +184,340) | +1.25 | +286,529 | +330,350 | +19,463 |
| ART-protecting, no country cut >30% | +173,854 (+119,476 to +232,881) | +1.56 | +4,469 | +125,264 | +23,457 |
| Same, budget held in modelled dollars (leverage removed) | +134,633 (+96,092 to +179,362) | +1.21 | -450,970 | -251,603 | +21,989 |
| Most people on any service, no country cut >30% | -63,241 (-128,923 to -17,963) | -0.57 | +3,334,914 | +3,155,663 | +12,359 |

The 30% ART-protecting allocation (US$M, change vs signed): Botswana 43.7 (+16%), Eswatini 62.6 (+33%), Lesotho 87.7
(+60%), Malawi 239.1 (+44%), Cameroon 120.4 (+32%), Mozambique 472.9 (+17%), Nigeria 511.7 (+12%), Kenya 354.1 (-9%);
Burundi, Ethiopia, Liberia, Madagascar, Rwanda, Sierra Leone, Uganda -30%. Recipients are filled to their `mou_us_ref`
(a 0% cut in 2027).

**Checks.** The linear programme (exact greedy on per-country marginals) predicts the full-run result to the person
in every case; a second pass with marginals re-measured at the optimum changes no country; the -US$1M and +US$1M
marginals agree within 2% everywhere; no line is capped at the people covered.

**Caveat.** Three-quarters of the ART gain survives when the budget is held in modelled dollars (134,633 instead of
173,854); the rest is the leverage artifact in finding 7. In modelled dollars the trade is explicit: 135,000 ART
patient-years for 252,000 bednets. "Most people on any service" is a bednet count (US$2.20 each) and should not be
the headline. Nothing here models what the MOU partners would accept; it is the model's arithmetic on the sheet's
totals. 2027 only; other years keep the signed schedule.

### 2. [world, computed with the model] The same US$208M a year costs 520,000 children's vaccinations through the multilateral exits, or 315,000 people's ART through bilateral channels

**Headline.** Per US$1M of aid lost per year, a cut to US bilateral money removes **1,424 ART patient-years**; a cut to
Global Fund money removes **519 ART patient-years, 138 TB courses and 36,000 bednets**; a cut to Gavi money removes
**8,566 children's routine vaccinations**. The preset's US multilateral exits (US$208M a year across the 15 countries)
remove 520,247 children's vaccinations and 71,148 ART patient-years a year; a US bilateral cut of the same size
removes 9,346 and 314,934.

**Mechanism.** Each channel's money is a different basket: US bilateral money in these countries is 73% HIV, Global
Fund money 49% HIV, 22% TB and 28% malaria, Gavi money 100% vaccines, and a cut removes services in that mix at the
model's unit costs (ART US$190-400 a patient-year, a TB course US$246-1,232, a bednet US$2.20, a child's routine
schedule US$87).

**Slide table** (per US$1M of aid lost per year, pooled over the 15 countries; `audit/channels/RESULTS_channels.md` Step 1 and Step 3)

| Channel cut | ART patient-years | TB courses | Bednets | Children vaccinated | All six services | Share of money on service lines | Deaths 2026-30 (secondary) |
|---|---|---|---|---|---|---|---|
| US bilateral (direct channels) | 1,424 | 24 | 23,867 | 48 | 28,911 | 57% | 432 |
| US money through the Global Fund | 526 | 137 | 39,087 | 0 | 48,303 | 62% | 586 |
| Global Fund, all donors | 519 | 138 | 36,072 | 0 | 44,519 | 61% | 586 |
| Gavi, all donors | 0 | 0 | 0 | 8,566 | 8,566 | 100% | 941 |
| UNICEF, all donors | 118 | 0 | 0 | 8,262 | 8,380 | 98% | 1,042 |

| US$208.4M a year, 15 countries | ART patient-years | TB courses | Bednets | Children vaccinated | Deaths 2026-30 (secondary) |
|---|---|---|---|---|---|
| The preset's US multilateral exits (WHO, Gavi, UNFPA 100%; Global Fund 23%) | 71,148 | 19,618 | 3,958,622 | 520,247 | 165,537 |
| A US bilateral cut of the same money | 314,934 | 9,676 | 3,406,966 | 9,346 | 105,771 |

**Checks.** Full and half-size cuts give the same people per US$1M within 2% in every country and channel; no capped
lines. The all-70-country pooled values are within about 30% of the 15-country ones (Step 1, second table).

**Caveat.** Multilateral cuts are modelled as a uniform share of every donor's money through that channel in the
country's 2021-23 mix; how the Global Fund or Gavi would actually reallocate a shortfall is not modelled. Bednet,
spraying, malaria treatment and vaccine unit costs are global constants (placeholders by country). Gavi and UNICEF
money has no ART or TB content by construction of the IHME programme areas.

### 3. [world] In the countries facing the cuts, past aid falls were met with neither replacement nor matching cuts: about 0 cents per dollar, not 19

**Headline.** The dashboard's benchmark (GHES falls 19 cents per dollar of aid lost; 95% CI -45 to +7 cents) is a
pooled estimate over 97 countries. In the 26 low-income countries the same regression gives **+1 cent (CI -4 to +6)**;
in the most aid-dependent third -5 cents (-22 to +11); in the 15 MOU countries -9 cents (-26 to +8). The pooled
co-movement comes from middle-income, low-dependence countries (upper-middle income -41 cents, CI -104 to +22).

**Mechanism.** Where aid is small next to government health spending, both move with the economy and the regression
reads the co-movement as a response; where aid is large and GHES is a few dollars a head, GHES did not move when aid
fell, in either direction.

**Slide table** (`audit/fiscal_history/RESULTS_fiscal_history.md` Steps 2-4; theta = change in GHES per person per US$1 of aid lost over that year and the next; < 0 = fell with the aid, > 0 = replaced)

| Group | theta | 95% CI | Countries | Country-years |
|---|---|---|---|---|
| All (the dashboard's benchmark) | -0.19 | -0.45 to +0.07 | 97 | 2,134 |
| Low income | +0.01 | -0.04 to +0.06 | 26 | 572 |
| Lower-middle income | -0.15 | -0.35 to +0.05 | 37 | 814 |
| Upper-middle income | -0.41 | -1.04 to +0.22 | 32 | 704 |
| Sub-Saharan Africa | -0.09 | -0.36 to +0.18 | 39 | 858 |
| Most aid-dependent third (DAH/THE 2015-23) | -0.05 | -0.22 to +0.11 | 32 | 704 |
| The 15 MOU countries | -0.09 | -0.26 to +0.08 | 15 | 330 |
| Years 2010-2014 (PEPFAR flat funding, Global Fund Round 11 cancelled) | -0.31 | -0.61 to -0.02 | 97 | 485 |

Episode view: 327 falls of at least 15% in DAH per person (87 countries); net of each country's usual growth and
the year's common shock, GHES grew less than usual in 43% of them and more in 45%; median response 0.00, dollar-
weighted +0.10 per person and +0.10 by population. In the 15 MOU countries: 45 episodes, dollar-weighted -0.07.
Leave-one-out: no single country moves the pooled theta by more than 0.044.

**Caveat.** IHME per-person series rounded to whole dollars (coarse for GHES of US$5-10 a head); all health aid, not
the four programme areas; two-year window; many episodes are disbursement timing rather than policy. It is evidence
that governments did not replace aid, not that they cannot. The 2010-14 subsample is the only one whose CI excludes
zero, in the direction of GHES falling with aid.

### 4. [world, computed with the model] Holding ART, TB treatment and vaccination flat would cost the 15 governments US$483M in 2030, 54 cents per aid dollar lost, and exceeds the model's fiscal space in 10 of 15

**Headline.** The smallest replacement share that keeps everyone on ART, TB treatment and routine vaccination (the
model's 'lives first' allocation, no cap) is **30 to 68 cents per dollar of US bilateral aid lost**; in the peak year
(2030) that is US$483M across the 15 countries, 5.6% of their combined 2023 government health spending (US$8.6B),
from 0.6% (Botswana) to 38% (Malawi). With the historical response (19 cents, if it were replacement) 1.2 million of
the 1.5 million people off those three services would still be off them.

**Mechanism.** The share is the part of each country's lost US money that sits on treatment and vaccine lines (plus
the lines the model ranks above them), so it is highest where US money is HIV treatment money (Nigeria 0.68,
Mozambique 0.59) and the cost bites where that money is large next to GHES (Malawi: US$44M against US$115M).

**Slide table** (`audit/gov_response/RESULTS_gov_response.md` Step 1)

| Country | Replacement share needed (cents per aid US$1) | Cost in 2030 US$M | % of GHES 2023 | % of the model's fiscal-space capacity | Years of usual GHES growth it equals |
|---|---|---|---|---|---|
| Malawi | 0.51 | 43.9 | 38.1% | 2,249% | 5.9 |
| Lesotho | 0.48 | 18.8 | 14.5% | 235% | 2.5 |
| Mozambique | 0.59 | 66.0 | 13.8% | 244% | 2.2 |
| Uganda | 0.55 | 59.7 | 12.0% | 455% | >50 (median growth about 0) |
| Sierra Leone | 0.49 | 5.1 | 10.0% | 157% | 2.3 |
| Eswatini | 0.49 | 14.1 | 8.9% | 349% | 1.4 |
| Burundi | 0.37 | 4.9 | 8.4% | 137% | 4.5 |
| Liberia | 0.30 | 4.6 | 7.8% | 103% | 0.5 |
| Rwanda | 0.45 | 23.9 | 6.9% | 193% | 0.6 |
| Cameroon | 0.57 | 23.7 | 6.8% | 63% | 8.3 |
| Nigeria | 0.68 | 98.5 | 4.5% | 98% | 1.9 |
| Kenya | 0.56 | 88.0 | 4.1% | 417% | 0.5 |
| Madagascar | 0.35 | 5.0 | 3.3% | 95% | 1.1 |
| Ethiopia | 0.42 | 21.7 | 2.2% | 36% | 0.5 |
| Botswana | 0.38 | 5.3 | 0.6% | 9% | 0.1 |
| **15 countries** | **0.54** | **483** | **5.6%** | **133%** | |

People off the three services in the peak year, 15 countries: 1,518,591 with no response; 1,208,038 with 19 cents
(capped by fiscal space); 773,059 with the share needed but capped by fiscal space (the dashboard always caps a set
share); 773,008 with 'as much as fiscal space allows'. Deaths 2026-30: 189,629 with no response, 8,685 at the share
needed uncapped (secondary).

**Caveat.** Under the dashboard's default pro-rata allocation the whole loss (theta = 1) has to be replaced to hold any
one service flat. Fiscal-space capacity is a labelled model assumption (a strong year's extra GHES growth times a
debt-stress factor); revenue is missing for Liberia, Nigeria and Sierra Leone; costs are 2023 US$ against nominal MOU
amounts; the MOU co-financing commitments are not modelled. Uganda's median real GHES growth is about zero in the
IHME series, so its "years of growth" is not meaningful.

### 5. [world, computed with the model] Under the signed MOUs ART coverage falls below 90% in 2026 in Eswatini, Lesotho and Rwanda, and in Kenya by 2028; Botswana drops below 95% in 2028

**Headline.** Of the five countries above 90% ART coverage today, the cut to US direct-channel aid at which coverage
crosses 90% is **5% in Kenya, 13% in Eswatini, 14% in Lesotho and Rwanda, 59% in Botswana**; the signed schedules cut
25% (Eswatini), 34% (Lesotho) and 73% (Rwanda) in 2026 and 60% in Kenya by 2030.

**Mechanism.** Coverage after a cut is baseline coverage minus (donor-funded people on ART x share of donor money
lost x 0.85), so the distance to a threshold is a few points of coverage divided by a large donor-funded pool: Kenya
is 1.2 points above 90% with 73% of HIV spending external.

**Slide table** (`audit/concentration/RESULTS_concentration.md` W-9; constant cut to US direct-channel aid; ART coverage = people on ART / people living with HIV)

| Country | ART coverage now | Cut at which coverage < 95% | Cut at which < 90% | Floor at a 100% cut | Coverage 2026-30 under the signed MOU | Below 90% from |
|---|---|---|---|---|---|---|
| Botswana | 100% | 29% | 59% | 83% | 96 / 98 / 94 / 94 / 94% | never (below 95% from 2028) |
| Eswatini | 95% | 0% | 13% | 54% | 85 / 85 / 83 / 75 / 68% | 2026 |
| Kenya | 91% | already below | 5% | 66% | 91 / 90 / 87 / 86 / 76% | 2028 |
| Lesotho | 96% | 3% | 14% | 52% | 81 / 80 / 79 / 72 / 65% | 2026 |
| Rwanda | 94% | already below | 14% | 64% | 72 / 80 / 75 / 68 / 65% | 2026 |
| Other 11 | 24-89% | already below | already below | 24-70% | falls 1-17 points by 2030 | already below |

**Caveat.** Baseline coverage is the UNAIDS/World Bank share of all people living with HIV on treatment (Botswana is
recorded as 100%); the 95-95-95 targets are defined on diagnosed people and are not this quantity. The crossing is a
linear projection with people in need held constant, no re-prioritisation by the programme and no government
response; it extrapolates the cut-fraction rule beyond the observed range. TB treatment is already below its 90%
target in 14 of 16 countries and DTP3 in 11 of 16, so those thresholds add nothing.

### 6. [world] Other donors would have to grow 4.9% a year to 2030 to offset the US bilateral cuts, after shrinking 0.5% a year over 2015-23; in Lesotho, Botswana and Eswatini the 2030 US cut exceeds all other donors' aid combined

**Headline.** Every other donor's aid for HIV, TB, malaria and immunization in the 15 countries averaged US$1,901M in
2021-23, down 0.5% a year from 2015 (US$2,197M); the modelled US bilateral cut reaches US$889M in 2030 (47% of that),
US$1,097M with the multilateral exits. Offsetting it year by year needs **+4.9% a year** (bilateral) or **+5.9%** (with
exits); other-donor aid fell over 2015-23 in 9 of the 15 countries.

**Mechanism.** US money is 55% of the four-disease aid in these countries, and in the three small southern African
countries it is 2-3 times everyone else's combined, so arithmetic alone rules out an other-donor offset there.

**Slide table** (`audit/other_donors/RESULTS_other_donors.md` Step 1; raw IHME DAH database, constant 2023 US$)

| Country | Other donors 2021-23 US$M | Other donors' growth 2015-23 (%/yr) | US cut 2030 US$M (bilateral) | as % of other donors' aid | Growth needed 2023-30 (%/yr) | with multilateral exits |
|---|---|---|---|---|---|---|
| Lesotho | 20.1 | +2.1% | 39.3 | 195% | +18.0% | +19.3% |
| Botswana | 10.1 | -3.3% | 14.1 | 140% | +17.2% | +18.2% |
| Eswatini | 18.6 | +3.2% | 28.7 | 155% | +12.4% | +13.9% |
| Rwanda | 79.3 | -4.9% | 52.6 | 66% | +10.7% | +12.6% |
| Kenya | 159.9 | -6.2% | 158.2 | 99% | +9.0% | +9.6% |
| Malawi | 157.1 | -3.9% | 85.5 | 54% | +5.7% | +8.1% |
| Nigeria | 417.7 | -2.5% | 144.5 | 35% | +3.8% | +4.8% |
| 15 countries | 1,901 | -0.5% | 889 | 47% | +4.9% | +5.9% |

**Caveat.** IHME disbursement estimates (lumpy); the US cut is the model's (cut fraction x 2021-23 US direct baseline),
not the MOU sheet's dollars; Global Fund and Gavi money counts as "other donors" although the US funds part of it;
IHME's 2024-25 preliminary estimates have no country rows, so recent other-donor retrenchment (OECD 2025) is not in
the history. The raw IHME file is in `datasets/` and not committed.

### 7. [model] Half the "non-zero-sum" loss in the reallocation audit is the mou_us_ref conversion; the rest is the disease mix, which is the real policy content

**Headline.** Re-expressing the team's Low ceiling so that recipients receive the modelled dollars the donors release
(the budget held in modelled dollars) cuts its extra deaths from 2,327 to 1,100 (**53% disappears**) and leaves ART
patient-years lost at +29,254 instead of +35,888; for the Medium and High ceilings the extra deaths disappear
entirely (-280 and -2,677) while ART patient-years lost stay at +29,388 and +20,480.

**Mechanism.** The model never applies MOU dollars: it converts them to cut fractions against `mou_us_ref` and
applies those to the 2021-23 US direct-channel baseline, so one nominal dollar is worth 0.23 (Madagascar) to 0.90
(Botswana) modelled dollars and money moved toward the malaria countries evaporates in the conversion; what remains
after the correction is that US$1M moved from an HIV-heavy to a malaria-heavy country trades about 860 ART
patient-years for about 12,000 people on a service, almost all bednets (mean over all such pairs).

**Slide table** (`audit/coverage_realloc/RESULTS_coverage_realloc.md` Step 3a; change vs the signed amounts, + = worse)

| Ceiling | Δ modelled aid lost 2027 US$M: nominal | modelled-neutral | Δ ART patient-years lost: nominal | modelled-neutral | Δ people losing a service: nominal | modelled-neutral | Δ deaths 2026-30: nominal | modelled-neutral |
|---|---|---|---|---|---|---|---|---|
| Low | +12.9 | 0 | +35,888 | +29,254 | -5,802 | -764,995 | +2,327 (+1,444 to +3,918) | +1,100 (+472 to +2,486) |
| Medium | +17.6 | 0 | +45,695 | +29,388 | +212,723 | -627,986 | +2,073 (+944 to +3,287) | -280 (-1,271 to +272) |
| High | +20.9 | 0 | +49,602 | +20,480 | +424,350 | -282,878 | +707 (-697 to +1,289) | -2,677 (-4,956 to -1,633) |

**Caveat.** This is a property of how the team sheet's reference (all US funding, 2021-25) compares with the model's
IHME-based US direct rows; it says nothing about the countries. Present it as a note on method, never as a result.
Recipients that reach their `mou_us_ref` are filled to it and the rest shared out (Madagascar in every ceiling;
Burundi, Liberia and Sierra Leone in the higher ones).

---

## (b) Analyses run and not worth a slide

- **W-5 Timing** (`audit/timing/`). Reshaping each country's 2026-30 cut (flat, front-loaded, back-loaded, linear,
  delayed a year) with the same total leaves ART patient-years and every other coverage count unchanged by
  construction (the yearly cut is applied to a fixed baseline). Only the timing of deaths moves: a one-year delay
  takes 15,067 deaths (8%) out of 2026-30 but only 8,668 (2.3%) off the 380,487 set in motion by 2035, and a flat
  path adds 32,581 deaths in-window while removing 14,598 from the total. The in-window numbers depend on the model's
  boundary (funding back in 2031, re-engagement thereafter). One sentence if asked: a delay changes when, not how much.
- **W-8 Concentration** (`audit/concentration/`). The loss is spread: 8 of 16 countries hold 85% of the ART loss
  (Nigeria 16%, Malawi 16%, Mozambique 15%), which is the size distribution, not a short list. ART is 43% of the
  service money lost and 4% of the people; bednets 9% of the money and 78% of the people. Protecting the 20 best
  treatment and vaccine lines keeps 74% of treatment coverage for US$173M a year (37% of the lost service money);
  97% takes US$269M (58%). There is no cheap protected list.
- **W-4 Within versus across disease** (`audit/coverage_realloc/` Step 4). Restates the disease mix: the best
  malaria-to-HIV move (Liberia to Nigeria, US$10M) gains on every count, +9,647 ART patient-years and +97,819 people;
  the best within-HIV move (Lesotho to Nigeria) buys 230,000 people on bednets for 2,236 ART patient-years; an
  HIV-to-malaria move (Lesotho to Sierra Leone) buys 252,000 for 10,269. Folded into findings 1 and 7.
- **"Most people on any service" objective** (W-2). Bednet-dominated: +3.3M people at the 30% cap, 63,000 fewer ART
  patient-years; kept in the table as the trade-off row, not a finding.
- **"Sum of each country's ART coverage drop" objective** (W-2). Tried and dropped: it favours small countries and
  makes the pooled ART coverage drop larger than the signed allocation's.
- **TB treatment and DTP3 thresholds** (W-9). Already below the 90% targets in 13 of 16 countries before any cut.
- **Named historical episodes one by one** (W-1 Step 4). The per-episode responses are dominated by the IHME file's
  whole-dollar rounding (GHES of US$5-10 a head) and disbursement timing; the subsample regressions and the dollar-
  weighted summary in finding 3 are the defensible form.

## Flags on inputs behind the numbers above

- Placeholders by country: bednet US$2.20, spraying US$8.50 a person, malaria treatment US$14 a case and routine
  vaccination US$87 a child are global constants; PMTCT cost US$250 is labelled "unverified; review figure".
- Assumptions: 15% continuity (people kept on service without the donor money); donor-funded pool = external share
  of disease spending x people covered; fiscal-space capacity; `mou_us_ref` and the MOU amounts are the team sheet's
  (nominal, `mou_deflate` off); ART coverage inputs are UNAIDS/World Bank (Botswana recorded at 100%).
- Extrapolation: the threshold scan applies the cut-fraction rule up to 100%; the W-6 replacement shares use the
  'lives first' allocation the dashboard labels hypothetical; deaths after 2030 assume funding returns in 2031.
- Data not in the repository: the raw IHME DAH database (W-6 and W-10 read it from `datasets/`).

## (c) Reproduce

From the repository root on branch `tomato` (each run is read-only; times on a laptop):

```
.venv/bin/python audit/fiscal_history/run_fiscal_history.py        # W-1, finding 3; about 1 min
.venv/bin/python audit/coverage_realloc/run_coverage_realloc.py    # W-2, W-3, W-4, findings 1 and 7; about 45 s
.venv/bin/python audit/timing/run_timing.py                        # W-5; about 15 s
.venv/bin/python audit/gov_response/run_gov_response.py            # W-6, finding 4; about 20 s
.venv/bin/python audit/channels/run_channels.py                    # W-7, finding 2; about 30 s
.venv/bin/python audit/concentration/run_concentration.py          # W-8, W-9, finding 5; about 2 min
.venv/bin/python audit/other_donors/run_other_donors.py            # W-10, finding 6; needs datasets/IHME_DAH_DATABASE_1990_2026_Y2026M09D18.CSV; about 5 s
```

Each script writes `RESULTS_<topic>.md` and its CSVs next to itself; all accept `--draws` where draws are used
(default 400). The reallocation audit they build on: `.venv/bin/python audit/reallocation/run_reallocation_2027.py`.
