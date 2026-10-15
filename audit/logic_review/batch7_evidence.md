# Batch 7: closing the small open items (15 October 2026)

Branch `tomato`. Rules: one commit per item; the headline (all countries, Full US Exit, central, deaths 2026-2030)
and the per-disease totals are recorded after every commit; any item that moves the headline by more than 0.5% is
reported with before and after values; tests run after every commit; new constants carry a central value, a range, a
source line and a "labelled assumption" tag where no source measures them; nothing is downloaded. Starting point
(commit `95cc16a`): **1,927,405** (HIV 998,535; TB 463,973; malaria 276,952; vaccines 187,945; HIV infections
3,966,261; further deaths 2031-35 990,588).

## Item 1. L-43 status reconciled: done, with a stated gap

The split of unspecified aid by purpose was implemented in Batch 3+4 item 2 (`2a792f7`): the country's Global Fund
Grant Cycle 7 module shares send the treatment share to treatment lines, the prevention share to prevention lines,
the testing share to testing and care, the systems share to systems money and the programme-management share to
non-service money (`docs/SPEC.md` section 3). What remains is a stated gap, not an open mechanism:

- **34 of 210 country-disease lines use a WHO-region median** instead of the country's own grant (the findings table
  said 38; the current `batch34_gf_shares.csv` has 34 for the 70 modelled countries): HIV Fiji, Iraq, Jordan, Libya,
  Rwanda; TB Belize, Dominican Republic, Fiji, Guyana, Iraq, Jamaica, Jordan, Libya, Mauritius, Rwanda, El Salvador;
  malaria Belize, Botswana, Dominican Republic, Egypt, Fiji, Iraq, Jamaica, Jordan, Cambodia, Laos, Libya, Lesotho,
  Mongolia, Mauritius, Rwanda, El Salvador, Viet Nam, South Africa. These are countries without a Global Fund grant
  for that disease; their unspecified money is small.
- **The Tajikistan-type cases** (donor money would buy more than the donor-funded pool, so units lost are the pool
  times the share of money lost; `donor_exceeds_cost`) under Full US Exit at the central run: TB treatment in
  Azerbaijan, Burundi, Benin, Burkina Faso, Belize, Botswana, Côte d'Ivoire, Cameroon, Djibouti, Dominican Republic,
  Egypt, Ghana, Gambia, Guatemala, Honduras, Haiti, Jamaica, Jordan, Kyrgyzstan, Cambodia, Laos, Lesotho, Moldova,
  Mali, Mongolia, Mauritius, Malawi, Nicaragua, Rwanda, Senegal, El Salvador, São Tomé and Príncipe, Eswatini, Togo,
  Tajikistan, Timor-Leste, South Africa, Zambia, Zimbabwe (39); drug-resistant TB in 41 countries; HIV treatment in
  30; malaria treatment in 31. The cap now holds every one of these below the people covered (the Validation page
  counts them), and the largest TB excess as a share of current TB deaths is Mozambique at 0.79 (validation.md),
  against the 1.08 Tajikistan showed before the cap.

**Status in both places:** done, with stated gap (34 of 210 lines on regional medians; capped cases listed above).
No model change; no headline change.

## Item 2. Headline chain re-run at each boundary commit

Each boundary commit was checked out in its own worktree and re-run with its own code and input files (central run,
Full US Exit, no response, sudden; `audit/.../chain_check.py`), and compared with the precomputed file committed at
that point. Every fresh run matched its own precomputed file exactly.

| Boundary | Commit | Recorded in the changelog header | Re-run | HIV | TB | Malaria | Vaccines |
|---|---|---|---|---|---|---|---|
| Before Batch 1 (logic review read-only) | `2cfcb14` | 2,017,000 (rounded) | **1,969,304** | 1,006,114 | 460,067 | 385,713 | 117,411 |
| After Batch 1 | `91d48fa` | 2,055,422 (wrong: that is the post-Batch-2 value) | **1,945,605** | 1,006,114 | 472,436 | 349,644 | 117,411 |
| After the malaria under-5 share | `c0d7587` | (not stated separately) | **1,965,386** | 1,006,114 | 472,436 | 369,425 | 117,411 |
| After Batch 2 | `cd42746` | 2,055,422 ("not changed by it") | 2,055,422 (**changed by it: HIV 1,006,114 -> 1,096,151**) | 1,096,151 | 472,436 | 369,425 | 117,411 |
| After Batch 3+4 | `c1b0846` | 1,379,963 | 1,379,963 | 669,366 | 463,973 | 143,889 | 102,735 |
| After Batch 4b | `d62a15d` | 1,695,601 | 1,695,601 | 938,069 | 463,973 | 190,824 | 102,735 |
| After Batch 5+6 | `26d6cd4` | 1,927,405 | 1,927,405 | 998,535 | 463,973 | 276,952 | 187,945 |

Corrections made to the changelog header: the starting value is 1,969,304, not "2,017,000 (rounded)" (the rounded
figure had been taken from the Batch 1 before/after table's pre-cleanup baseline); Batch 1 moved the headline to
1,945,605 (malaria -9%, TB +3%), the under-5 share to 1,965,386, and Batch 2 to 2,055,422 (HIV +9%), which the
header had wrongly described as unchanged by Batch 2. The Batch 3+4, 4b and 5+6 values reproduce.
