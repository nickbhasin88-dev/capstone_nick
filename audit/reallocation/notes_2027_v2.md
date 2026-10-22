### Where the money goes (table 4e)

All three ceilings take money from the same three countries and give most of it to Mozambique:

| Scenario | Countries giving (nominal US$M) | Countries receiving (nominal US$M) |
|---|---|---|
| Low Ceiling | Nigeria -21.8, Kenya -19.4, Cameroon -3.3 (total -44.5) | Mozambique +43.0, Burundi +1.5 |
| Base Ceiling | Nigeria -43.7, Kenya -38.8, Cameroon -6.6 (total -89.1) | Mozambique +77.3, Uganda +3.9, Sierra Leone +3.6, Lesotho +2.8, Burundi +1.5 |
| Higher Ceiling | Nigeria -65.5, Kenya -58.2, Cameroon -9.9 (total -133.6) | Mozambique +77.3, Uganda +48.4, Sierra Leone +3.6, Lesotho +2.8, Burundi +1.5 |

Botswana, Eswatini, Ethiopia, Liberia, Madagascar, Malawi and Rwanda are unchanged in every scenario, so their results do not move.

### What drives the differences (numbers from tables 4b, 4e, 5a and 5b)

1. **Deaths fall because the money moves to countries where a dollar averts more deaths than in Kenya.** Per US$1M of
   nominal MOU money, Mozambique averts 89-95 deaths over 2026-2030 where it arrives (table 4e), Lesotho 74 and Uganda
   54-69, against 51-57 lost in Kenya and 56-76 in Cameroon where it leaves. Nigeria is close to Mozambique (87-94), so
   the Nigeria-to-Mozambique part of the move is roughly even; the gain comes mainly from Kenya's money. Kenya's money
   averts fewer deaths per dollar because its ART cost is high (US$308 per patient-year against US$227 in Mozambique)
   and about a sixth of each MOU dollar goes to HIV testing and care, which has no modelled deaths (US$165K per US$1M,
   table 5b).
   Net: Low Ceiling 3,858 deaths averted where money arrives against 3,412 caused where it leaves (-446); Base 7,913
   against 6,778 (-1,134); Higher 11,067 against 9,200 (-1,866).

2. **People losing a service rise because Nigeria's money is bednet money.** One US$1M of Nigeria's MOU money keeps
   21,388 people on bednets (US$55K of it lands on bednets at US$2.20 each), against 3,730 in Mozambique (table 5a). So
   moving money out of Nigeria removes many cheap bednet places and moving it into Mozambique adds few. Nigeria alone
   adds 531,373 / 1,062,747 / 1,594,120 people losing a service in 2027 (Low / Base / Higher), more than the whole net
   increase (+554,556 / +1,077,462 / +1,447,387); almost all of it is bednets (+536,777 / +1,033,463 / +1,428,931,
   table 4c). Each bednet place lost costs about 0.5 deaths per 1,000 in Nigeria, against 0.05 deaths per ART
   patient-year lost, so the people count rises while deaths fall. The services gained are mainly ART, PMTCT and HIV
   prevention: HIV deaths fall by 432 / 1,402 / 2,845 and HIV infections by 3,240 / 7,174 / 10,746, while malaria deaths
   rise by 338 / 622 / 849.

3. **Some modelled aid is lost in the conversion, and some money in Mozambique buys nothing.** The model converts each
   MOU amount into a cut fraction of the country's 2021-23 US direct-channel aid, so one MOU dollar is worth 0.65 modelled
   dollars in Kenya, 0.57 in Cameroon and 0.53 in Nigeria, but 0.56 in Mozambique, 0.61 in Uganda, 0.64 in Lesotho, 0.34
   in Burundi and 0.32 in Sierra Leone (table 5a). In addition, the Base and Higher Ceilings give Mozambique US$481.0M,
   US$8.1M above its 2021-25 reference (US$472.9M): its cut is already 0% there, so that US$8.1M averts nothing in the
   model (Step 2). Together these mean the 15 countries lose US$1.1M / US$7.0M / US$5.8M more modelled aid in 2027 than
   under the Original MOU, even though the nominal total is the same. Mozambique's surplus is about US$4.6M of the
   US$7.0M in the Base Ceiling.

4. **Timing.** The gains build up over time. In 2027 itself the Higher Ceiling has 234 more deaths than the Original MOU
   (malaria and TB deaths from the money leaving Nigeria, Kenya and Cameroon happen in the same year), but from 2028 it
   has about 700 fewer each year, because deaths among people who stop ART rise in the years after stopping (table 4d).
   All three ceilings also reduce deaths in 2031-2035 (-201 / -485 / -1,013).

5. **Ranges.** The paired ranges of the change in deaths are below zero in all three ceilings (Low -1,062 to -318, Base
   -2,730 to -843, Higher -4,437 to -1,150), so the direction holds across the parameter draws. No line is capped at
   the people covered, and only Eswatini (unchanged here) is nonlinear in the marginal check.

### In plain language

1. The new allocations take US MOU money from Kenya, Nigeria and Cameroon and give most of it to Mozambique, and in the
   Higher Ceiling a large share to Uganda.
2. In the model, Mozambique and Uganda use that money mostly for HIV treatment and prevention at lower cost per patient
   than Kenya, so the move averts more deaths than it causes: 446 fewer deaths over 2026-2030 under the Low Ceiling,
   1,134 under the Base Ceiling and 1,866 under the Higher Ceiling (0.2-1.0% of the 189,629 under the Original MOU).
3. At the same time, many more people lose a service in 2027 (+0.55M to +1.45M), almost all of them bednets in
   Nigeria. Bednets are cheap per person, so losing them affects many people, but each lost net costs fewer lives than
   a person losing HIV treatment.
4. Malaria deaths go up a little and HIV deaths and infections go down; the net effect on deaths is a gain.
5. Two things to fix in the allocations: the Base and Higher Ceilings give Mozambique US$8.1M more than its
   reference, which the model treats as buying nothing; and Kenya's money averts the fewest deaths per dollar among the
   three countries giving money, so taking more from Kenya and less from Nigeria would avert more deaths, while taking
   more from Nigeria cuts more bednets.
6. This reverses the earlier allocations (allocations_2027.csv, RESULTS_2027.md), which sent money to malaria-heavy
   countries (Madagascar, Burundi, Liberia, Sierra Leone) where one MOU dollar is worth only 0.23-0.34 modelled dollars,
   and added 707 to 2,327 deaths.
