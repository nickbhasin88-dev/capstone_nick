# Archived audit scripts

`analysis.py` belongs to commit **4cbb7ff**, the commit the full audit (`audit/AUDIT.md`) was run on. It produced
`audit/fallbacks.csv`, `audit/outliers.csv`, `audit/sensitivity.csv` and `audit/analysis.json`, the evidence for
Steps 2, 5 and 6 of that audit.

It tests the MOU functions that the I-02/I-03/I-08 fix (commit bba5405) replaced (`mou_cuts`, `mou_cut_path`,
`mou_average_cut_pct`, `DEFAULT_MOU_YEAR`), so it does not run on later commits; it stops with a message instead.
To reproduce its outputs:

    git checkout 4cbb7ff
    .venv/bin/python audit/analysis.py      # its path at that commit

Everything else in `audit/` runs on the current commit.
