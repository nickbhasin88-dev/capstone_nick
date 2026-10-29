"""Tests for audit fix I-10: Section 3 boxes by level of government. Run:  python -m pytest tests"""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import budget_section as bs  # noqa: E402


def rev(level, vals):
    return pd.DataFrame({"label": list(vals), "group": "Taxes", "pct_gdp": list(vals.values()), "coverage": level})


def cofog(level, shares, total):
    return pd.DataFrame({"label": list(shares), "group": ["Health" if k == "Health" else "Government spending"
                                                           for k in shares],
                         "pct_outlays": list(shares.values()), "pct_gdp": [v / 100 * total for v in shares.values()],
                         "coverage": level, "total_pct_gdp": total})


def test_general_government_breakdown_scaled_to_weo():
    bx = bs.budget_boxes(rev("General government", {"VAT": 6.0, "Income": 4.0}), None, 11.0, 12.0)
    r = bx["rev"]
    assert r["level"] == "General Government" and r["other"] == 0
    assert r["items"]["v"].sum() == pytest.approx(11.0) and bs.side_box_sum(r) == pytest.approx(11.0)


def test_central_breakdown_own_size_plus_grey_box():
    bx = bs.budget_boxes(None, cofog("Central government (budgetary)", {"Health": 10, "Defence": 90}, 15.0), 18.0, 25.0)
    s = bx["spd"]
    assert s["level"] == "Central Government"
    assert s["items"]["v"].tolist() == pytest.approx([1.5, 13.5])           # not rescaled
    assert s["other"] == pytest.approx(10.0) and bs.side_box_sum(s) == pytest.approx(25.0)


def test_central_above_weo_shown_alone_with_note():
    bx = bs.budget_boxes(rev("Central government", {"Oil": 39.0}), None, 38.0, 40.0)
    r = bx["rev"]
    assert r["note"] == bs.CENTRAL_ABOVE_WEO and r["other"] == 0 and r["total"] == pytest.approx(39.0)


def test_caption_when_sides_differ():
    bx = bs.budget_boxes(rev("Central government", {"VAT": 5.0}), cofog("General government", {"Health": 100}, 9.0),
                         7.0, 9.0)
    assert bx["caption"] == bs.DIFFERENT_LEVELS
    bx = bs.budget_boxes(rev("General government", {"VAT": 5.0}), cofog("General government", {"Health": 100}, 9.0),
                         7.0, 9.0)
    assert bx["caption"] is None
    assert bx["gap"] == pytest.approx(2.0)                                  # WEO spending - revenue
