"""
Section 3 (Revenue and Spending): the boxes each side of the treemap shows, as plain numbers (% of GDP), so the
dashboard draws them and audit/checks.py can check them (audit I-10).

Each side (revenue, spending) is sized to the IMF World Economic Outlook general-government total:
  - a general-government breakdown (IMF revenue data / COFOG coverage "General government") is used as is, scaled to
    the WEO total (same level of government; only the two IMF sources' small differences are reconciled);
  - a central-government breakdown is shown at its own size, labelled "Central Government", plus one grey box for the
    rest of the WEO total, "Other Levels of Government (no breakdown)";
  - if the central total is larger than the WEO total, the central breakdown is shown alone with a short note;
  - without a breakdown, one box holds the WEO total; without WEO totals, each side is its own file's total.
"""
from __future__ import annotations

import logging

import pandas as pd

log = logging.getLogger("budget_section")
SUM_TOL = 0.5          # percentage points: how far a side's items may be from its total before a warning is logged
OTHER_LEVELS = "Other Levels of Government (no breakdown)"
CENTRAL_ABOVE_WEO = ("Central-government figures exceed the IMF WEO general-government total this year, so the "
                     "central breakdown is shown alone.")
DIFFERENT_LEVELS = "Revenue and spending come from different levels of government in this year's data."


def coverage_level(rows: pd.DataFrame | None) -> str | None:
    """'General Government', 'Central Government' or None (no breakdown)."""
    if rows is None or rows.empty or "coverage" not in rows:
        return None
    c = str(rows["coverage"].dropna().iloc[0]).lower() if rows["coverage"].notna().any() else ""
    return "General Government" if "general" in c else "Central Government" if "central" in c else None


def spending_shares(g: pd.DataFrame, where: str = "") -> pd.Series:
    """COFOG shares of outlays (label -> %), checked and rescaled to sum to 100. Interest is its own box, so if the
    shares overshoot 100 by about the interest share, interest is also inside General public services and is taken out
    of it; any other mismatch is rescaled proportionally. Both are logged."""
    sh = g.groupby("label", sort=False)["pct_outlays"].sum()
    tot = float(sh.sum())
    if abs(tot - 100) > SUM_TOL:
        intr, gps = sh.get("Interest on public debt", 0.0), sh.get("General public services", 0.0)
        if intr > 0 and gps >= intr and abs((tot - 100) - intr) <= SUM_TOL:
            log.warning("%s: COFOG shares sum to %.1f%%; interest (%.1f%%) is counted twice, removing it from general "
                        "public services", where, tot, intr)
            sh["General public services"] = gps - intr
        else:
            log.warning("%s: COFOG shares sum to %.1f%%, not 100%%; rescaling", where, tot)
    return sh * 100 / sh.sum()


def _side(items: pd.DataFrame, own_total: float | None, weo: float | None, level: str | None) -> dict:
    """items: label, group, pct_gdp (the file's own size). Returns the side's boxes and total (% of GDP)."""
    out = {"level": level, "items": items.assign(v=items["pct_gdp"]) if items is not None else None, "other": 0.0,
           "note": None, "scaled": False, "weo": weo}
    if items is None or items.empty:                          # no breakdown: one box of the total
        out["items"] = None
        out["total"] = weo if weo is not None else own_total
        return out
    mix = float(items["pct_gdp"].sum())
    if weo is None:                                           # no WEO total: the file's own size
        out["total"] = mix
    elif level == "General Government":                       # same level as WEO: reconcile the two IMF sources
        out["items"] = items.assign(v=items["pct_gdp"] * (weo / mix if mix > 0 else 0.0))
        out["scaled"] = abs(mix - weo) > 1e-9
        out["total"] = weo
    elif mix > weo + 0.005:                                   # central above general: central alone, with a note
        out["note"], out["total"] = CENTRAL_ABOVE_WEO, mix
    else:                                                     # central at its own size + the rest of the WEO total
        out["other"] = weo - mix if weo - mix > 0.005 else 0.0
        out["total"] = mix + out["other"]
    return out


def budget_boxes(rg: pd.DataFrame | None, g: pd.DataFrame | None, R_w: float | None, E_w: float | None,
                 where: str = "") -> dict:
    """Both sides for one country-year. rg: revenue rows (label, group, pct_gdp, coverage); g: COFOG rows (label,
    group, pct_outlays, pct_gdp, coverage, total_pct_gdp); R_w, E_w: WEO general-government revenue and expenditure
    (% of GDP) or None. Returns {'rev': side, 'spd': side, 'gap': spending - revenue (WEO; else the sides' totals),
    'caption': the different-levels caption or None}."""
    weo = R_w is not None and E_w is not None
    rev = spd = None
    if rg is not None and not rg.empty:
        items = rg.groupby(["label", "group"], sort=False)["pct_gdp"].sum().reset_index()
        rev = _side(items, float(items["pct_gdp"].sum()), R_w if weo else None, coverage_level(rg))
    elif weo:
        rev = _side(None, None, R_w, None)
    if g is not None and not g.empty:
        sh = spending_shares(g, where)
        grp = g.groupby("label", sort=False)["group"].first()
        if "total_pct_gdp" in g and g["total_pct_gdp"].notna().any():
            own = float(g["total_pct_gdp"].dropna().iloc[0])
        else:
            b = g[g["pct_gdp"].notna() & (g["pct_outlays"] > 0)]
            own = float((100 * b["pct_gdp"] / b["pct_outlays"]).median()) if len(b) else None
        if own is not None:
            items = pd.DataFrame({"label": sh.index, "group": [grp[l] for l in sh.index], "pct_gdp": sh.values / 100 * own})
            spd = _side(items, own, E_w if weo else None, coverage_level(g))
    elif weo:
        spd = _side(None, None, E_w, None)
    if weo:
        gap = E_w - R_w
    else:
        gap = (spd["total"] - rev["total"]) if (rev and spd) else 0.0
    levels = {s["level"] for s in (rev, spd) if s and s["level"]}
    return {"rev": rev, "spd": spd, "gap": gap, "weo": weo,
            "caption": DIFFERENT_LEVELS if len(levels) > 1 else None}


def side_box_sum(side: dict) -> float:
    """What a side's boxes add up to (items + the grey box, or the single box)."""
    if side["items"] is None:
        return side["total"]
    return float(side["items"]["v"].sum()) + side["other"]
