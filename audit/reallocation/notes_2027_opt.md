### How to read this report

The three scenarios are the best allocations of the 2027 US MOU money for deaths found by
`audit/reallocation/run_optimal_realloc_2027.py` (RESULTS_optimal_2027.md), with each country's change limited to
±10%, ±20% or ±30% of its signed 2027 amount. They are defined **dollar for dollar**: US$1 taken from one country is
US$1 of US direct aid given to another, so the model's aid lost in 2027 is unchanged (tables 4a-4b: +0.00 US$M), and
no country is raised above its 2021-23 US aid level (a 0% cut; the model has no coverage above baseline) or cut below
zero US aid.

This report's script works in MOU dollars and turns them into cut fractions, so each allocation was converted into
the MOU amount that produces exactly that aid change in the model (`allocations_2027_opt_mou.csv`; MOU amount = ref x
(1 - (Original cut - aid change / US direct baseline)); the aid change matches to within US$0.01). Because one MOU dollar
moves a different amount of modelled aid in each country (Step 2 and table 5a), these MOU-equivalent amounts do not add
up to the Original total: Step 1 flags the spread (US$2,500M / 2,485M / 2,529M against US$2,469.9M) and that is
expected, not an error. In table 4e, the "MOU US$M moved" column is this MOU-equivalent amount; **the "Modelled aid US$M"
column is the real dollar change**, and it sums to zero. (The TOTAL row prints 0.00 for MOU dollars moved by
construction; the MOU-equivalent amounts sum to +US$30.5M / +US$15.1M / +US$59.5M.)

The actual dollar changes (US$M of US aid, face value):

| Country | ±10% | ±20% | ±30% | Original 2027 cut |
|---|---|---|---|---|
| Botswana | +3.0 | +5.0 | +5.0 | 13.5% |
| Burundi | -3.0 | -6.0 | -9.0 | 38.3% |
| Cameroon | +9.0 | +16.0 | +16.0 | 24.0% |
| Eswatini | +4.0 | +9.0 | +10.0 | 24.9% |
| Ethiopia | +7.0 | +7.0 | +7.0 | 7.2% |
| Kenya | -38.0 | -77.0 | -116.0 | 4.5% |
| Lesotho | -5.0 | +11.0 | +16.0 | 37.3% |
| Liberia | -3.0 | -6.0 | +7.0 | 40.9% |
| Madagascar | +3.0 | 0.0 | +9.0 | 59.6% |
| Malawi | -16.0 | +33.0 | +47.0 | 30.6% |
| Mozambique | +39.0 | +39.0 | +39.0 | 14.6% |
| Nigeria | +29.0 | +29.0 | +29.0 | 11.0% |
| Rwanda | +6.0 | +12.0 | +19.0 | 45.8% |
| Sierra Leone | +3.0 | +4.0 | +4.0 | 30.8% |
| Uganda | -38.0 | -76.0 | -83.0 | 12.2% |
| **Moved** | **103** | **165** | **208** | |

### What drives the result (numbers from tables 4b-4e and 5a)

1. **Money goes where restoring a cut saves the most lives per dollar.** The receivers are mostly HIV-heavy countries
   whose Original MOU cuts US aid deeply (Rwanda 46%, Lesotho 37%, Malawi 31%, Eswatini 25%, Cameroon 24%) or whose aid
   buys treatment cheaply (Nigeria, Mozambique: ART US$208-227 per patient-year). For these HIV-heavy receivers, restoring that money
   averts 145-211 deaths per US$1M in the ±30% scenario (table 4e, per US$1M modelled: Eswatini 211, Lesotho 206, Cameroon 204, Malawi
   202, Nigeria 197, Mozambique 187), more than the marginal US$1M at the Original level suggests (Malawi 119, table
   5a): when a 2027 cut is reversed, people who stopped ART in 2026 return to care, so each dollar restored first brings
   back people already at high risk.

2. **Money comes from where a cut costs the fewest lives per dollar.** Kenya and Uganda: ART costs US$308-314 per
   patient-year, a fifth to almost a third of their HIV money goes to testing and care with no modelled deaths (Uganda
   21%, Kenya 29%), and their Original cuts
   are shallow (4.5% and 12.2%), so cutting further costs about 50 deaths per US$1M (table 4e: Kenya 51.0, Uganda 49.9).
   Burundi (29 per US$1M) gives in every scenario.

3. **The curves are not straight lines, so the allocation changes shape with the bound.** Lesotho and Malawi give
   money at ±10% but receive at ±20% and ±30%; Liberia gives at ±10-20% and receives at ±30%. Their first dollars
   restored are worth less than later ones (the 2026 cohort returns only once the 2027 cut falls below the 2026 cut),
   so they only pay off when enough money can be moved.

4. **Everything improves at once.** Unlike the team's ceilings, the best allocations reduce deaths in every disease
   (±30%: HIV -23,552, TB -1,872, malaria -1,746, immunization -210), avert 21,622 / 54,869 / 65,964 HIV infections and
   keep 1.0-2.1 million more people on a service in 2027 (table 4b). Deaths fall most in 2027 itself (-4,597 / -5,823 /
   -7,080) and the gain persists to 2035 (table 4d, by calendar year).

5. **Ranges.** The paired ranges of the change in deaths are well below zero in all three scenarios (±10% -17,409 to
   -7,863; ±20% -36,289 to -15,487; ±30% -44,668 to -19,312), so the direction does not depend on the uncertain
   parameters.

### Who pays for it

The gains are paid for by Kenya, Uganda and Burundi. In the ±30% scenario ART coverage in 2027 falls from 90.0% to
78.9% in Kenya (164,000 more people off treatment), from 82.4% to 75.4% in Uganda (109,000) and from 81.3% to 70.8% in
Burundi, while Malawi returns from 79.0% to 89.0%, Lesotho from 79.5% to 92.3%, Eswatini from 84.9% to 94.3% and
Rwanda from 80.5% to 91.0% (RESULTS_optimal_2027.md, section 3). Kenya and Uganda alone add 10,066 deaths over
2026-2030 (table 4e); the other twelve countries avert 37,445.

### In plain language

1. Moving 4-8% of the 2027 US MOU money between the same 15 countries, with no new money, could avert 11,600 to 27,400
   deaths over 2026-2030 in the model (6-14% of the 189,629 under the Original MOU), and every disease improves.
2. The money should go back to countries whose US HIV aid is cut deeply or buys treatment cheaply (Malawi, Mozambique,
   Nigeria, Rwanda, Lesotho, Cameroon, Eswatini), and come mainly from Kenya and Uganda, where treatment is expensive and
   the Original cuts are small.
3. This is the model's answer to "fewest deaths in total". It is not neutral between countries: Kenya, Uganda and
   Burundi lose 7-11 points of ART coverage in the widest version. A fairness limit (for example, no country's ART
   coverage more than a few points below its Original MOU level) would keep part of the gain.
4. Limits: these are the model's numbers (unit costs, the ART cohort rule, central parameters for the allocation itself);
   the allocation is the best one found on US$1M steps, not a proven optimum; and each MOU is a separate bilateral
   agreement, so this shows where money does most in the model, not what is negotiable.
