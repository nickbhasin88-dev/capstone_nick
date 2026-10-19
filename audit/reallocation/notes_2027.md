### What drives the differences (numbers from tables 5a and 5b)

1. **Leverage: how much modelled aid one MOU dollar carries.** The model never applies the MOU dollar amounts. It
   turns them into a cut fraction, 1 - amount / `mou_us_ref`, and applies that fraction to the country's 2021-23 US
   direct-channel aid for HIV, TB, malaria and immunization in `model_data/dah_lines.csv`. The team sheet's reference
   is all US funding (2021-25), so one nominal MOU dollar carries 0.90 modelled dollars in Botswana, 0.65 in Kenya and
   Malawi, 0.70 in Eswatini, 0.57 in Cameroon and 0.53 in Nigeria, but only 0.23 in Madagascar, 0.32 in Sierra Leone,
   0.33 in Liberia and 0.34 in Burundi. Under the Low Ceiling US$50.9M leaves the four donor countries plus Lesotho and
   Rwanda as US$29.9M of modelled aid, and US$51.0M arrives in the six recipients as US$17.0M of modelled aid: 43% of
   the modelled money disappears in the conversion, and the 15-country aid lost in 2027 rises by US$12.9M (US$17.6M
   Medium, US$20.9M High). This is the largest single reason the reallocation is not zero-sum, and it is a property of
   how the MOU reference compares with the model's IHME-based baseline, not of the countries' health systems.

2. **Disease mix and what the money buys.** The cut is uniform across a country's US direct rows, so the money lost
   follows the country's US disease mix. In Botswana, Eswatini, Lesotho (95-99% HIV), Malawi (89%) and Kenya (87%)
   roughly US$250-300K of every nominal US$1M lands on ART treatment money, buying 1,300-1,400 patient-years at
   US$190-230 each. In Madagascar (95% malaria), Sierra Leone and Liberia (57% malaria) US$35-60K lands on bednets at
   US$2.20 and US$8-32K on malaria treatment at US$14, so one US$1M keeps 14,000-27,000 people on a service but only
   0-300 on ART. People counts are therefore dominated by bednets: the High Ceiling moves 424,000 more people off a
   service in 2027, almost all bednets lost in Nigeria and Kenya, while HIV deaths fall.

3. **Health effect per person losing a service.** An ART patient-year lost costs 0.05 deaths over 2026-2030 in most
   countries (the Batch 2 cohort hazard plus deaths from onward infections at the country's UNAIDS transmission rate,
   0.07 Kenya to 0.31 Botswana). A TB course lost costs 0.34-0.54 deaths. A thousand bednets lost cost 0.06 (Kenya) to 0.64 (Sierra Leone)
   deaths, depending on malaria deaths per case (1.2-6.1 per 1,000) and bednet use; a
   thousand untreated malaria cases 1.6-10.0 deaths; a thousand unvaccinated children 13-41 deaths (VIMC deaths averted
   per child 19-65 per 1,000). Per modelled dollar, ART money saves about 0.05 / US$208 = 240 lives per US$1M of pure
   treatment money, bednets 0.3 / US$2.20 = 140, so even per modelled dollar HIV-heavy money is worth more here, and the
   recipients with the lowest ranking (Liberia 53, Burundi 58 deaths per US$1M modelled) also lose a larger share of
   their money to testing, programme management and systems lines that have no modelled deaths.

4. **Caps and nonlinearity.** No line is capped at the people covered in any run, and the -US$1M and +US$1M marginals
   agree within 2% for 14 countries, so the results are close to linear in the money moved. The exception is the ART
   cohort rule (`health_model.art_cohorts`): when a year's cut is smaller than the previous year's, the newest cohorts
   return to care first. Where the 2027 cut is below the 2026 cut (Botswana 22.8% to 13.5%, Rwanda 73% to 46%,
   Ethiopia 23% to 7%) a marginal person kept off ART in 2027 is a 2026-cohort member who otherwise would have returned
   and who then stays off through 2030, so deaths per ART person-year are 0.10 instead of 0.05. Eswatini's flat
   2026-27 schedule makes the effect one-sided: taking US$1M away adds a young cohort (79 deaths per US$1M) while
   adding US$1M returns older cohort members (148 per US$1M), which is why Eswatini gains the most per dollar under the
   Medium and High ceilings. Malaria's Lives Saved Tool and the TB spread terms are mildly nonlinear but do not change
   the ranking.

### In plain language: why the reallocation raises deaths

1. The money leaves countries where a US dollar in the MOU is mostly HIV treatment money that the model counts almost in
   full (Kenya, Nigeria, Botswana, Cameroon), and arrives in countries where the same dollar is mostly malaria money
   that the model counts at a quarter to a third of its face value (Madagascar, Burundi, Liberia, Sierra Leone).
2. Because of that conversion, the 15 countries end up with US$13-21M less modelled aid in 2027, so there is simply
   less money in the system that the model can turn into services.
3. The services that are lost are ART patient-years, each worth about one death in twenty over 2026-2030 plus onward HIV
   infections; the services gained are mainly bednets and malaria treatment, each worth far less per person, so even
   where the people numbers improve (Low Ceiling: 5,800 fewer people lose a service) deaths still rise.
4. Malawi and Eswatini are the two recipients that pull the other way: their US money is HIV money and their leverage
   is high, so the US$42M and US$7M they receive under the High Ceiling avert about 5,100 and 1,100 deaths, which is
   why the High Ceiling adds only 700 deaths against 2,300 under the Low Ceiling, and its range includes zero.
5. In the model's terms the reallocation is not zero-sum and goes the wrong way: all three ceilings add deaths over
   2026-2030 (+2,327 Low, +2,073 Medium, +707 High, against a Baseline of 189,629) and HIV infections (+4,500 to
   +7,100), while cutting malaria deaths by 115-290. A reallocation that kept the HIV-heavy countries whole and moved money within the malaria countries, or
   that was expressed in the model's own aid dollars rather than nominal MOU totals, would not show this loss.

### Caveats

- US bilateral aid only: the preset's exits from WHO, Gavi, UNFPA and 23% of the Global Fund are switched off, so
  the Baseline here (189,629 deaths 2026-2030 in the 15 countries) is below the dashboard's America First MOUs figure
  (356,197), which includes them. The reallocation changes are almost the same either way (the multilateral exits are
  a constant in both arms; with them on the changes were +2,413, +2,243 and +958).

- Only 2027 changes; every other year keeps the signed schedule, so the deaths attributed here are the 2027 change
  and its knock-on effects (ART cohort ageing, TB spread in 2028-29, missed vaccine cohorts).
- South Sudan is excluded from every number. Ethiopia, Uganda and Mozambique (Low and Medium) receive +US$1, treated
  as rounding.
- Dashboard defaults: no government response, death-rate trends on. Government co-financing in the MOUs is not
  modelled.
- People losing a service are full-cost equivalents after the 15% continuity assumption, and totals across services
  are dominated by bednets; the deaths columns are the better guide to welfare.
