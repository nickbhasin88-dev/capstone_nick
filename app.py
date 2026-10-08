"""
Who funds health in each country?  (IHME Development Assistance for Health, 1990-2025)

Run:   streamlit run app.py
Data:  ./country_data/<Country>.csv   (created by prepare_data.py)
"""
import html
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from country_lists import ALLOWED_COUNTRIES
import theme as th
from model_section import chart, render_model_section, stat, title_case

# Full-width kwarg differs by Streamlit version (older: use_container_width, 1.50+: width="stretch")
_ver = tuple(int(x) for x in st.__version__.split(".")[:2] if x.isdigit())
WIDE = {"width": "stretch"} if _ver >= (1, 50) else {"use_container_width": True}

# --------------------------------------------------------------------------- #
# Settings you may want to edit
# --------------------------------------------------------------------------- #
DATA_DIR = Path(__file__).parent / "country_data"          # DAH, one file per recipient
SPEND_DIR = Path(__file__).parent / "spending_data"        # total spending, one file per ISO3
YEAR_MIN, YEAR_MAX = 2015, 2030          # chart 1 x-axis window, fixed (future years stay blank)
SPEND_YEAR_MIN, SPEND_YEAR_MAX = 2015, 2030   # chart 2 x-axis window, fixed
DEFAULT_COUNTRY = "Kenya"
NGO_SHADE = 0.45                         # NGO/foundation channels: the funder's colour at this opacity
# funders shown individually (fixed colours in theme.FUNDER_COLORS); everything else is "All Other Sources"

# Channels treated as "NGO / foundation" money. IHME does NOT record whether a
# recipient government knew about a flow -- channel is only a proxy. These are
# the defaults; the sidebar lets you change them live.
DEFAULT_NONGOV_CHANNELS = ["NGO", "INTLNGO", "US_FOUND", "GATES"]

CHANNEL_LABELS = {
    "NGO": "US NGOs", "INTLNGO": "International NGOs", "US_FOUND": "US foundations",
    "GATES": "Gates Foundation (direct)", "GAVI": "Gavi", "GFATM": "Global Fund", "CEPI": "CEPI",
    "WHO": "WHO", "PAHO": "PAHO", "UNICEF": "UNICEF", "UNFPA": "UNFPA", "UNAIDS": "UNAIDS",
    "UNITAID": "Unitaid", "WB_IDA": "World Bank (IDA)", "WB_IBRD": "World Bank (IBRD)",
    "WB": "World Bank", "AfDB": "African Development Bank", "AsDB": "Asian Development Bank",
    "IDB": "Inter-American Development Bank", "EC": "European Commission",
    "EEA": "European Economic Area", "BIL_USA": "US bilateral (USAID/State/etc.)",
}

HFA_LABELS = {
    "total": "Total health (all focus areas)",
    "hiv": "HIV/AIDS",
    "mal": "Malaria",
    "tb": "Tuberculosis",
    "rmh": "Reproductive & maternal health",
    "nch": "Newborn & child health (incl. vaccines)",
    "oid": "Other infectious diseases",
    "ncd": "Non-communicable diseases",
    "swap_hss_total": "Health systems strengthening",
    "other": "Other (focus area known, not in list)",
    "unalloc": "Unallocated (no focus area info)",
}
HFAS_WITH_PROGRAM_AREAS = ["hiv", "mal", "tb", "rmh", "nch", "oid", "ncd", "swap_hss_total"]

PA_LABELS = {
    "treat": "Treatment", "prev": "Prevention", "pmtct": "Prevention of mother-to-child transmission",
    "ovc": "Orphans & vulnerable children", "care": "Care & support", "ct": "Counseling & testing",
    "amr": "Drug resistance", "diag": "Diagnosis", "con_nets": "Bednets", "con_irs": "Indoor spraying",
    "con_oth": "Other vector control", "comm_con": "Community outreach", "fp": "Family planning",
    "mh": "Maternal health", "cnn": "Nutrition", "cnv": "Vaccines", "ebz": "Ebola", "zika": "Zika",
    "covid": "COVID-19", "tobac": "Tobacco", "mental": "Mental health", "pp": "Pandemic preparedness",
    "hss_other": "HSS - other", "hss_hrh": "HSS - human resources", "hss_me": "HSS - ME",
    "hrh": "Human resources", "other": "Other",
}
NON_COUNTRY_ISO = {"WLD", "INKIND", "QZA"}
SOURCE_LABELS = {"Debt repayments": "World Bank Lending (Loan Repayments)", "Private other": "Private Philanthropy"}

# Chart 2 components: (column prefix, label, colour). Stack order = bottom to top.
SPEND_PARTS = [
    ("ghes", "Government", th.GRAPE),
    ("ppp", "Prepaid Private", th.BLUE),
    ("oop", "Out-of-Pocket", th.TEAL),
    ("dah", "Foreign Aid for Health (DAH)", th.ROSE),
]
COFOG_ALL_DIR = Path(__file__).parent / "cofog_all"        # IMF: whole-government spending by function, per ISO3
_HEALTH = ["Hospital services", "Outpatient services", "Medical products", "Public health services", "Health R&D",
           "Other health"]
HEALTH_REDS = {k: th.blend(th.ROSE, a) for k, a in zip(_HEALTH, (1.0, 0.85, 0.7, 0.58, 0.46, 0.36))}
HEALTH_REDS["Health (no breakdown)"] = HEALTH_REDS["Health (not broken down)"] = th.ROSE
# other spending functions in muted grey-lavenders (so Health stands out); interest in BRAND
_OTHER_FUNCS = ["Social protection", "Education", "General public services", "Economic affairs", "Defence",
                "Public order and safety", "Housing and community amenities", "Environmental protection",
                "Recreation, culture and religion"]
OTHER_FUNCS = dict(zip(_OTHER_FUNCS, [th.blend(th.MUTED, a) for a in (0.62, 0.5, 0.56, 0.44, 0.38, 0.32, 0.27, 0.23, 0.2)]))
OTHER_FUNCS["Interest on public debt"] = th.BRAND
MACRO_DIR = Path(__file__).parent / "macro_data"          # IMF WEO: GDP, population, debt, per ISO3
REVENUE_DIR = Path(__file__).parent / "revenue_data"      # IMF WoRLD: government revenue by type, per ISO3
# revenue: taxes in blues, everything else in teals
REV_GROUP_COLORS = {"Taxes": th.BLUE, "Social contributions": th.TEAL, "Grants": th.blend(th.TEAL, 0.7),
                    "Other revenue": th.blend(th.TEAL, 0.5), "Unclassified": th.OTHER}
_TAXES = ["Personal income tax", "Corporate income tax", "Other income taxes", "Income taxes", "VAT / sales tax",
          "Excise taxes", "Other goods & services taxes", "Goods & services taxes", "Trade taxes (customs)",
          "Property taxes", "Other taxes"]
_TAX_SHADES = [1.0, 0.85, 0.7, 0.9, 0.78, 0.6, 0.5, 0.75, 0.42, 0.34, 0.28]
REV_TAX_COLORS = {k: th.blend(th.BLUE, a) for k, a in zip(_TAXES, _TAX_SHADES)}
REV_LABELS = {"Grants (e.g. foreign aid)": "Grants (Mostly Foreign Aid)"}
BORROWING_COLOR = th.DEEP


def _resolve_dir(d: Path) -> Path:
    """Use <d>/<d.name> if the folder was unzipped one level too deep."""
    inner = d / d.name
    if not any(d.glob("*.csv")) and inner.is_dir() and any(inner.glob("*.csv")):
        return inner
    return d


log = logging.getLogger("dashboard.budget")
DATA_DIR, SPEND_DIR, COFOG_ALL_DIR, REVENUE_DIR, MACRO_DIR = (_resolve_dir(p) for p in (DATA_DIR, SPEND_DIR, COFOG_ALL_DIR, REVENUE_DIR, MACRO_DIR))
SPEND_LAST_OBSERVED = 2023                 # 2024+ are IHME expected values
PROJECTED_OPACITY = 0.45                   # projected years drawn at this opacity
PROJECTION_BAND = th.tint(th.RULE, 0.45)    # background band behind projected / no-data years

# --------------------------------------------------------------------------- #
# Data loading
# --------------------------------------------------------------------------- #
def load_countries() -> pd.DataFrame:
    """One row per selectable location, keyed by ISO3, with whichever files exist."""
    dah = load_index()[["recipient_country", "recipient_isocode", "file", "is_country"]]
    dah = dah.rename(columns={"recipient_isocode": "iso3", "file": "dah_file"})
    sp_path = SPEND_DIR / "_index.csv"
    sp = pd.read_csv(sp_path) if sp_path.exists() else pd.DataFrame(columns=["iso3", "location_name"])
    m = dah.merge(sp, on="iso3", how="outer")
    m["name"] = m["location_name"].fillna(m["recipient_country"])   # prefer the spending-file name
    m["is_country"] = m["is_country"].fillna(True).astype(bool)
    m["has_spend"] = m["location_name"].notna()
    m = m[m["iso3"].isin(ALLOWED_COUNTRIES)].copy()
    m["name"] = m["iso3"].map(ALLOWED_COUNTRIES)
    m["is_country"] = True
    m["label"] = m["name"]
    return m.sort_values(["is_country", "name"], ascending=[False, True]).reset_index(drop=True)


INCOME_LABELS = {"low_income": "Low Income", "lower_middle_income": "Lower-Middle Income",
                 "upper_middle_income": "Upper-Middle Income", "high_income": "High Income"}
PROFILE_FILE = Path(__file__).parent / "model_data" / "country_profile.csv"   # built by prepare_model.py


def load_profile() -> dict:
    """iso3 -> {region, income_group, mou_status}. Read fresh every run (98 rows, ~1 ms): a cached copy could stay
    empty if the app reran while a deploy was still writing the file, which showed n/a for every country."""
    if not PROFILE_FILE.exists():
        return {}
    d = pd.read_csv(PROFILE_FILE).set_index("iso3")
    return {k: {c: (v if pd.notna(v) else None) for c, v in r.items()} for k, r in d.iterrows()}


def load_cofog_all(iso3: str):
    p = COFOG_ALL_DIR / f"{iso3}.csv"
    return pd.read_csv(p) if p.exists() else None


def load_macro(iso3: str):
    p = MACRO_DIR / f"{iso3}.csv"
    return pd.read_csv(p) if p.exists() else None


def load_revenue(iso3: str):
    p = REVENUE_DIR / f"{iso3}.csv"
    if not p.exists():
        return None
    d = pd.read_csv(p)
    d["label"] = d["label"].replace(REV_LABELS)
    return d


def load_spending(iso3: str) -> pd.DataFrame:
    return pd.read_csv(SPEND_DIR / f"{iso3}.csv")


def load_index() -> pd.DataFrame:
    idx_path = DATA_DIR / "_index.csv"
    if idx_path.exists():
        idx = pd.read_csv(idx_path)
    else:  # fall back to scanning the folder
        rows = []
        for f in sorted(DATA_DIR.glob("*.csv")):
            if f.name.startswith("_"):
                continue
            head = pd.read_csv(f, nrows=1, usecols=["recipient_country", "recipient_isocode"])
            rows.append({**head.iloc[0].to_dict(), "file": f.name})
        idx = pd.DataFrame(rows)
    idx["is_country"] = ~idx["recipient_isocode"].isin(NON_COUNTRY_ISO)
    idx["label"] = idx["recipient_country"] + idx["is_country"].map({True: "", False: "  (non-country)"})
    return idx.sort_values(["is_country", "recipient_country"], ascending=[False, True]).reset_index(drop=True)


@st.cache_data(show_spinner="Loading country spreadsheet...")
def _load_country(file: str, _mtime: float) -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / file)
    df["source"] = df["source"].str.replace("_", " ").str.strip().replace(SOURCE_LABELS)
    return df


def load_country(file: str) -> pd.DataFrame:
    p = DATA_DIR / file
    return _load_country(file, p.stat().st_mtime if p.exists() else 0.0)


def program_area_options(df: pd.DataFrame, hfa: str) -> dict:
    # SWAp/HSS columns are named swap_hss_<area>_dah_23 (the category itself is swap_hss_total)
    prefix = "swap_hss_" if hfa == "swap_hss_total" else f"{hfa}_"
    opts = {}
    for c in df.columns:
        if c.startswith(prefix) and c.endswith("_dah_23") and c != f"{hfa}_dah_23":
            key = c[len(prefix):-len("_dah_23")]
            opts[c] = PA_LABELS.get(key, key)
    return dict(sorted(opts.items(), key=lambda kv: kv[1]))


def fmt_usd(m: float) -> str:
    """Format an amount given in US$ millions as $x.xM / $x.xB / $x.xT."""
    a = abs(m)
    if a >= 1e6:
        return f"${m / 1e6:,.1f}T"
    if a >= 1e3:
        return f"${m / 1e3:,.1f}B"
    return f"${m:,.1f}M"


def pick_unit(max_millions: float):
    """Choose axis unit for values given in US$ millions -> (divisor, word, suffix)."""
    if max_millions >= 1e6:
        return 1e6, "trillions", "T"
    if max_millions >= 1e3:
        return 1e3, "billions", "B"
    return 1.0, "millions", "M"


# --------------------------------------------------------------------------- #
# Page
# --------------------------------------------------------------------------- #
th.apply_page("Health Financing")

if not DATA_DIR.exists():
    st.error("No `country_data/` folder found. Run `python prepare_data.py <path to the IHME DAH CSV>` first.")
    st.stop()

_missing = []
if not (SPEND_DIR / "_index.csv").exists():
    _missing.append(f"`spending_data/` (health spending graph) - build with `prepare_spending.py`")
if not any(COFOG_ALL_DIR.glob("*.csv")):
    _missing.append("`cofog_all/` (government spending treemap) - unzip `cofog_all.zip` or build with `prepare_cofog.py`")
if not any(MACRO_DIR.glob("*.csv")):
    _missing.append("`macro_data/` (GDP and population bubbles) - unzip `macro_data.zip` or build with `prepare_weo.py`")
if not any(REVENUE_DIR.glob("*.csv")):
    _missing.append("`revenue_data/` (government revenue treemap) - unzip `revenue_data.zip` or build with `prepare_revenue.py`")
if _missing:
    st.warning(
        "These data folders are missing (or empty) next to this script, so part of the page won't show:\n\n- "
        + "\n- ".join(_missing)
        + f"\n\nI'm looking in: `{Path(__file__).parent}`"
    )

countries = load_countries()

# ---- sticky country header: name and profile pills on the left, the country picker on the right ------ #
_ctx = st.session_state.get("model_ctx", {})
_start = ALLOWED_COUNTRIES.get(_ctx.get("iso3"), DEFAULT_COUNTRY)          # keep the country chosen on another page
# seed the box once (stable key, so later picks always register); after a page switch it is seeded again
if st.session_state.get("country_sel") not in set(countries["label"]):
    st.session_state["country_sel"] = _start if (countries["label"] == _start).any() else countries["label"].iloc[0]
hdr = st.container(key="hdr")
hdr_left, hdr_right = hdr.columns([4, 1], vertical_alignment="bottom")
with hdr_right:
    country_label = st.selectbox("Country", countries["label"], key="country_sel")
crow = countries[countries["label"] == country_label].iloc[0]
country_name = crow["name"]

_mac0 = load_macro(crow["iso3"]) if any(MACRO_DIR.glob("*.csv")) else None
_gdp_bn, _gdp_yr = None, None
if _mac0 is not None and "gdp_usd_bn" in _mac0.columns:
    _gf = _mac0[_mac0["gdp_usd_bn"].notna() & ~_mac0["gdp_is_estimate"].astype(bool)]
    if len(_gf):
        _gdp_bn, _gdp_yr = float(_gf["gdp_usd_bn"].iloc[-1]), int(_gf["year"].iloc[-1])
_pop_m, _pop_yr = None, None          # same year as GDP (IMF's own population "actual" is the last census, often years old)
if _mac0 is not None and "population_m" in _mac0.columns:
    _pf = _mac0[_mac0["population_m"].notna() & (_mac0["year"] <= (_gdp_yr or 2024))]
    if len(_pf):
        _pop_m, _pop_yr = float(_pf["population_m"].iloc[-1]), int(_pf["year"].iloc[-1])

_prof = load_profile().get(crow["iso3"], {})
_items = [
    ("Region", _prof.get("region") or "n/a", "World Bank region (IHME DAH database)"),
    ("Income Group", INCOME_LABELS.get(_prof.get("income_group"), "n/a"), "World Bank income group"),
    ("US MOU", _prof.get("mou_status") or "n/a", "US bilateral health MOU, from the team's MOU / co-financing sheet"),
    (f"GDP{', ' + str(_gdp_yr) if _gdp_yr else ''}", fmt_usd(_gdp_bn * 1e3) if _gdp_bn else "n/a",
     "Current US$, IMF World Economic Outlook"),
    (f"Population{', ' + str(_pop_yr) if _pop_yr else ''}",
     ((f"{_pop_m:,.1f}" if _pop_m >= 1 else f"{_pop_m:,.2f}") + "M") if _pop_m else "n/a",
     "Millions of people, IMF World Economic Outlook"),
]
with hdr_left:
    st.markdown(f"<div class='ed-country'>{html.escape(country_name)}</div>" + th.pills_html(_items),
                unsafe_allow_html=True)

# =========================================================================== #
# CHART 2 - total health spending by source: past vs expected
# =========================================================================== #
th.section_header("payments", f"Money Spent on Health in {country_name}, Over Time",
                  "How much is spent on health each year, and who pays for it?", rule=False,
                  help="DAH = development assistance for health: money from foreign governments, multilaterals and "
                       "foundations.")

if not crow["has_spend"] or not (SPEND_DIR / f"{crow['iso3']}.csv").exists():
    st.info(f"{country_name} isn't in the IHME health-spending dataset (it covers 204 countries and territories), "
            "so there is no spending breakdown to show.")
else:
    sp = load_spending(crow["iso3"])
    view = st.radio("Show As", ["US$ total", "US$ per person", "Share of total (%)"], format_func=title_case,
                    horizontal=True, key="c2_view")
    y0, y1 = SPEND_YEAR_MIN, SPEND_YEAR_MAX

    left = st.container()
    with left:
        w = sp[(sp["year"] >= y0) & (sp["year"] <= y1)].copy()
        sfx2 = ""
        _div = 1.0
        if view == "US$ total":
            for k, _, _ in SPEND_PARTS:
                w[f"v_{k}"] = w[f"{k}_total_mean"] / 1e3
            _div, _name, sfx2 = pick_unit(w["the_total_mean"].max() / 1e3 if len(w) else 0)
            for k, _, _ in SPEND_PARTS:
                w[f"v_{k}"] = w[f"v_{k}"] / _div
            ylab = f"US$ {_name} (constant 2023)"
        elif view == "US$ per person":
            for k, _, _ in SPEND_PARTS:
                w[f"v_{k}"] = w[f"{k}_per_cap_mean"]
            ylab = "US$ per person (constant 2023)"
        else:
            for k, _, _ in SPEND_PARTS:
                w[f"v_{k}"] = 100 * w[f"{k}_total_mean"] / w["the_total_mean"]
            ylab = "% of total health spending"

        proj = w["projected"] == 1
        fig2 = go.Figure()
        def _hov(label_txt):
            return (f"<b>{label_txt}</b><br>%{{x}}: "
                    + ("%{y:,.1f}%" if view.startswith("Share") else "$%{y:,.0f}" if view == "US$ per person"
                       else "%{customdata[0]}"))

        opac = [PROJECTED_OPACITY if p else 1.0 for p in proj]
        for k, label, col in SPEND_PARTS:
            fig2.add_bar(
                x=w["year"], y=w[f"v_{k}"], name=label,
                customdata=[[fmt_usd(v * _div)] for v in w[f"v_{k}"]] if view == "US$ total" else None,
                marker=dict(color=col, opacity=opac),
                hovertemplate=_hov(label) + "<extra></extra>",
            )
        if y1 > SPEND_LAST_OBSERVED:
            fig2.add_vrect(x0=max(y0, SPEND_LAST_OBSERVED + 1) - 0.5, x1=y1 + 0.5, fillcolor=PROJECTION_BAND, layer="below",
                           line_width=0, annotation_text="IHME expected (projected)", annotation_position="top left",
                           annotation_font=dict(size=12, color=th.MUTED))
        fig2.update_layout(
            title=dict(text=f"Health Spending by Source, {y0}-{y1}"),
            barmode="stack", height=680, margin=dict(l=10, r=10, t=50, b=10),
            xaxis=dict(range=[y0 - 0.5, y1 + 0.5], dtick=1, tickangle=-45, title="", automargin=True),
            yaxis=dict(title=ylab, rangemode="tozero", automargin=True, **({"range": [0, 100]} if view.startswith("Share") else {})),
            legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="left", x=0),
            bargap=0.15, hovermode="closest",
        )
        chart(fig2)

        last_obs = sp[sp["year"] == SPEND_LAST_OBSERVED].iloc[0]
        end = sp[sp["year"] == min(y1, int(sp["year"].max()))].iloc[0]
        k1, k2, k3 = st.columns(3)
        stat(k1, f"Total Spending, {SPEND_LAST_OBSERVED}", fmt_usd(last_obs['the_total_mean'] / 1e3))
        stat(k2, f"Foreign Aid Share of Total, {SPEND_LAST_OBSERVED}", f"{last_obs['dah_total_mean'] / last_obs['the_total_mean']:.0%}")
        stat(k3, f"Foreign Aid Share of Total, {int(end['year'])}" + (" (Expected)" if end["year"] > SPEND_LAST_OBSERVED else ""),
             f"{end['dah_total_mean'] / end['the_total_mean']:.0%}")
        st.caption("Government, prepaid private and out-of-pocket spending are domestic; development assistance is aid "
                   "from abroad; paler bars after 2023 are IHME projections (constant 2023 US$).")


# =========================================================================== #
# CHART 1 - who funds health (DAH)
# =========================================================================== #
th.section_header("public", f"Who Is Providing the Money in {country_name}?",
                  "Which donors fund health here, and through which channels?")

if pd.isna(crow["dah_file"]):
    st.info(f"{country_name} is not a recipient in the IHME DAH database (typically a high-income country), "
            "so there is no aid-funder breakdown to show.")
else:
    df = load_country(crow["dah_file"])
    c1, c2 = st.columns(2)
    with c1:
        hfa = st.selectbox("Health Category", list(HFA_LABELS), format_func=lambda k: title_case(HFA_LABELS[k]), key="c1_hfa")
    value_col, metric_label = "dah_23", HFA_LABELS["total"]
    if hfa != "total":
        value_col, metric_label = f"{hfa}_dah_23", HFA_LABELS[hfa]
        pas = program_area_options(df, hfa) if hfa in HFAS_WITH_PROGRAM_AREAS else {}
        if pas:
            with c2:
                pa = st.selectbox("Program Area", ["All program areas"] + list(pas),
                                  format_func=lambda k: title_case(k if k == "All program areas" else pas[k]),
                                  key=f"c1_pa_{hfa}")
            if pa != "All program areas":
                value_col, metric_label = pa, f"{HFA_LABELS[hfa]}: {pas[pa]}"
    nongov = st.multiselect(
        "Channels Drawn as NGO / Foundation (Lighter Shade)",
        options=list(CHANNEL_LABELS), default=DEFAULT_NONGOV_CHANNELS, key="c1_ngo",
        format_func=lambda c: title_case(f"{CHANNEL_LABELS[c]} ({c})"),
        help="IHME doesn't record whether a government knew about a flow. "
             "The channel that delivered the money is used as a proxy.",
    )

    d = df[["year", "source", "channel", value_col]].rename(columns={value_col: "val"})
    d["val"] = d["val"] / 1e3                       # thousands of US$ -> millions of US$
    d["route"] = d["channel"].isin(nongov).map({True: "ngo", False: "gov"})
    last_data_year = int(df.loc[df["dah_23"] != 0, "year"].max()) if (df["dah_23"] != 0).any() else YEAR_MIN

    window = d[(d["year"] >= YEAR_MIN) & (d["year"] <= YEAR_MAX)]
    window = window.assign(source=window["source"].map(th.funder_group))     # six named funders + All Other Sources
    agg = window.groupby(["year", "source", "route"], as_index=False)["val"].sum()
    # which organizations the lighter-shaded money went through, per bar (for hover text)
    ngo_detail = (window[window["route"] == "ngo"].groupby(["year", "source", "channel"])["val"].sum().reset_index())
    ngo_detail = ngo_detail[ngo_detail["val"] > 0]
    ngo_detail["txt"] = ngo_detail["channel"].map(lambda c: CHANNEL_LABELS.get(c, c)) + ": " + ngo_detail["val"].map(fmt_usd).astype(str)
    ngo_hover = ngo_detail.groupby(["year", "source"])["txt"].apply("<br>".join).to_dict()
    # axis unit adapts to size (millions / billions / trillions)
    unit_div, unit_name, unit_sfx = pick_unit(agg.groupby("year")["val"].sum().max() if len(agg) else 0)
    agg["val"] = agg["val"] / unit_div
    present = set(agg.loc[agg["val"] > 0, "source"])
    order = [s for s in th.FUNDER_COLORS if s in present]          # same order and colours in every country
    colors = th.FUNDER_COLORS

    latest = d[d["year"] == last_data_year]
    tot = latest["val"].sum()
    if tot > 0:
        ngo_share = latest.loc[latest["route"] == "ngo", "val"].sum() / tot
        top_src = latest.groupby("source")["val"].sum().idxmax()
        m1, m2, m3 = st.columns(3)
        stat(m1, f"Total in {last_data_year}", fmt_usd(tot))
        stat(m2, f"Via NGO / Foundation Channels, {last_data_year}", f"{ngo_share:.0%}")
        stat(m3, f"Largest Funder, {last_data_year}", top_src)
    else:
        st.info("No funding recorded for this selection.")

    # every trace gets the same x values (every year), so solid and lighter segments stack in one column per year
    years = list(range(YEAR_MIN, YEAR_MAX + 1))
    fig = go.Figure()
    for s in order:
        col = colors[s]
        for route in ("gov", "ngo"):
            sub = agg[(agg["source"] == s) & (agg["route"] == route)]
            if sub.empty:
                continue
            sub = sub.set_index("year")[["val"]].reindex(years).reset_index()     # missing years -> NaN (no bar)
            # same funder, lighter shade for NGO / foundation channels; no outline on any trace (all the same width)
            marker = dict(color=col if route == "gov" else th.tint(col, NGO_SHADE), line=dict(width=0))
            amts = [fmt_usd(v * unit_div) if pd.notna(v) else "" for v in sub["val"]]   # exact amount, own unit (M / B / T)
            if route == "ngo":
                custom = [[ngo_hover.get((y, s), ""), a] for y, a in zip(sub["year"], amts)]
                hover = f"<b>{s}</b><br>Funneled through:<br>%{{customdata[0]}}<br>%{{x}} total: %{{customdata[1]}}<extra></extra>"
            else:
                custom = [[a] for a in amts]
                hover = f"<b>{s}</b><br>Government-facing channel<br>%{{x}}: %{{customdata[0]}}<extra></extra>"
            fig.add_bar(
                x=sub["year"], y=sub["val"], name=s, legendgroup=s,
                showlegend=(route == "gov" or not ((agg["source"] == s) & (agg["route"] == "gov")).any()),
                marker=marker, customdata=custom, hovertemplate=hover,
            )
    if last_data_year < YEAR_MAX:
        fig.add_vrect(x0=last_data_year + 0.5, x1=YEAR_MAX + 0.5, fillcolor=PROJECTION_BAND, layer="below", line_width=0,
                      annotation_text="No country-level data yet", annotation_position="top left",
                      annotation_font=dict(size=12, color=th.MUTED))
    fig.update_layout(
        title=dict(text=f"Health Aid Received, by Funder: {title_case(metric_label)}"),
        barmode="stack", height=600, margin=dict(l=10, r=10, t=50, b=10),
        xaxis=dict(range=[YEAR_MIN - 0.5, YEAR_MAX + 0.5], dtick=1, tickangle=-45, title=""),
        yaxis=dict(title=f"US$ {unit_name} (constant 2023)", rangemode="tozero"),
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="left", x=0),
        bargap=0.15, hovermode="closest",
    )
    chart(fig)
    st.caption("Lighter shades are aid delivered through NGOs and foundations, a proxy for money that may bypass the "
               f"government; IHME's country-level data end in {last_data_year}.")


# =========================================================================== #
# CHART 3 - what health aid is spent on (DAH by health focus area)
# =========================================================================== #
st.subheader("Where the Aid Is Spent")

# Fixed focus-area colours; the four smallest categories are grouped as "All Other" (breakdown in the hover)
FOCUS_COLORS = {"hiv": th.DISEASE_COLORS["HIV"], "tb": th.DISEASE_COLORS["TB"], "mal": th.DISEASE_COLORS["Malaria"],
                "nch": th.DISEASE_COLORS["Immunization"], "rmh": th.PINK, "swap_hss_total": th.LILAC}
FOCUS_OTHER = ["oid", "ncd", "other", "unalloc"]
ALL_OTHER = "All other"
MAX_PROGRAM_AREAS = 6                              # inside one focus area: the largest 6, then "All Other"
PA_SHADES = (1.0, 0.8, 0.64, 0.5, 0.38, 0.28)      # opacity of the focus area's colour, darkest = largest

if pd.isna(crow["dah_file"]):
    st.info(f"{country_name} is not a recipient in the IHME DAH database, so there is no category breakdown to show.")
else:
    df3 = load_country(crow["dah_file"])
    e1, e2, e3 = st.columns([2, 2, 2])
    with e1:
        view3 = st.radio("Show As", ["US$ total", "Share of total (%)"], horizontal=True, key="c3b_view",
                         format_func=title_case)
    with e2:
        brk = st.selectbox("Break Down", ["all"] + HFAS_WITH_PROGRAM_AREAS, key="c3b_brk",
                           format_func=lambda k: "All Focus Areas" if k == "all" else title_case(HFA_LABELS[k]))
    data_end = int(df3.loc[df3["dah_23"] != 0, "year"].max()) if (df3["dah_23"] != 0).any() else YEAR_MIN

    groups = []                     # (label, colour, {column: member label}), bottom of the stack first
    if brk == "all":
        groups = [(HFA_LABELS[h], col, {f"{h}_dah_23": HFA_LABELS[h]}) for h, col in FOCUS_COLORS.items()]
        groups.append((ALL_OTHER, th.OTHER, {f"{h}_dah_23": HFA_LABELS[h] for h in FOCUS_OTHER}))
    else:
        pas3 = program_area_options(df3, brk)
        in_win = df3[(df3["year"] >= YEAR_MIN) & (df3["year"] <= data_end)]
        ranked = in_win[list(pas3)].sum().sort_values(ascending=False)
        ranked = ranked[ranked.abs() > 0]
        base = FOCUS_COLORS.get(brk, th.MUTED)
        top = list(ranked.index[:MAX_PROGRAM_AREAS])
        groups = [(pas3[c], th.blend(base, PA_SHADES[i]), {c: pas3[c]}) for i, c in enumerate(top)]
        rest = {c: pas3[c] for c in ranked.index[MAX_PROGRAM_AREAS:]}
        if rest:
            groups.append((ALL_OTHER, th.OTHER, rest))

    members = [c for _, _, m in groups for c in m if c in df3.columns]
    byyr = df3.groupby("year")[members].sum() / 1e3                  # thousands of US$ -> millions
    byyr = byyr.reindex(range(YEAR_MIN, YEAR_MAX + 1))
    byyr.loc[byyr.index > data_end] = np.nan                         # blank after data ends
    gy = pd.DataFrame({lab: byyr[[c for c in m if c in byyr.columns]].sum(axis=1, min_count=1)
                       for lab, _, m in groups}, index=byyr.index)
    gy = gy.loc[:, gy.fillna(0).abs().sum() > 0]                     # drop categories with nothing
    if gy.empty:
        st.info("No funding recorded for this selection.")
    else:
        tot_y = gy.sum(axis=1, min_count=1)
        div3, name3, sfx3 = pick_unit(tot_y.max())
        share = view3.startswith("Share")
        fig4 = go.Figure()
        for lab, col, m in groups:
            if lab not in gy.columns:
                continue
            cols_m = [c for c in m if c in byyr.columns]
            detail = ["<br>".join(f"{title_case(m[c])}: {fmt_usd(byyr.at[y, c])}" for c in cols_m
                                  if pd.notna(byyr.at[y, c]) and byyr.at[y, c] != 0) if len(cols_m) > 1 else ""
                      for y in gy.index]
            amt = [fmt_usd(v) if pd.notna(v) else "" for v in gy[lab]]
            yv = 100 * gy[lab] / tot_y.where(tot_y > 0) if share else gy[lab] / div3
            hov = (f"<b>{title_case(lab)}</b><br>%{{x}}: " + ("%{y:,.1f}% of aid (%{customdata[0]})" if share
                                                               else "%{customdata[0]}")
                   + ("<br>%{customdata[1]}" if len(cols_m) > 1 else "") + "<extra></extra>")
            fig4.add_bar(x=gy.index, y=yv, name=lab, marker=dict(color=col), hovertemplate=hov,
                         customdata=np.c_[amt, detail])
        fig4.update_layout(
            title=dict(text="Health Aid by What It Pays For" + ("" if brk == "all" else f": {HFA_LABELS[brk]}")),
            barmode="stack", height=560, margin=dict(l=10, r=10, t=50, b=10),
            xaxis=dict(range=[YEAR_MIN - 0.5, YEAR_MAX + 0.5], dtick=1, tickangle=-45, title="", automargin=True),
            yaxis=dict(title=("% of health aid" if share else f"US$ {name3} (constant 2023)"),
                       rangemode="tozero", automargin=True, **({"range": [0, 100]} if share else {})),
            legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="left", x=0),
            bargap=0.15, hovermode="closest",
        )
        if data_end < YEAR_MAX:
            fig4.add_vrect(x0=data_end + 0.5, x1=YEAR_MAX + 0.5, fillcolor=PROJECTION_BAND, layer="below", line_width=0,
                           annotation_text="No data yet", annotation_position="top left",
                           annotation_font=dict(size=12, color=th.MUTED))
        chart(fig4)
        st.caption("Aid only (IHME does not split government, private or out-of-pocket spending by disease); "
                   + ("'All Other' groups other infectious diseases, non-communicable diseases, other and unallocated "
                      "aid (hover for the breakdown)." if brk == "all" else
                      "'All Other' groups the smaller program areas (hover for the breakdown)."))


# =========================================================================== #
# SECTION 4 - the government budget: one treemap, revenue side and spending side sized to each other
# =========================================================================== #
th.section_header("account_balance", f"Revenue and Spending in {country_name}",
                  "Where does government money come from, and where does it go?")

SUM_TOL = 0.5          # percentage points: how far a side's items may be from its total before a warning is logged


def _spending_shares(g: pd.DataFrame, where: str) -> pd.Series:
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


def _budget_section():
    iso = crow["iso3"]
    rev = load_revenue(iso) if REVENUE_DIR.exists() else None
    spd = load_cofog_all(iso) if COFOG_ALL_DIR.exists() else None
    mac = load_macro(iso) if any(MACRO_DIR.glob("*.csv")) else None
    rev_years = set(rev["year"].unique()) if rev is not None and not rev.empty else set()
    spd_years = set(spd["year"].unique()) if spd is not None and not spd.empty else set()

    if not rev_years and not spd_years:
        st.info(f"The IMF files have no government revenue or spending-by-function data for {country_name}.")
        return
    both = sorted(rev_years & spd_years, reverse=True)
    years_all = sorted(rev_years | spd_years, reverse=True)
    default_y = both[0] if both else years_all[0]
    _, ymid, _ = st.columns([1, 1, 1])
    with ymid:
        yr4 = st.selectbox("Year", years_all, index=years_all.index(default_y), key=f"c4_year_{iso}")
    where = f"{iso} {int(yr4)}"

    # ---- WEO (general government) sizes both sides; GDP turns % of GDP into current US$ ----
    gdp_m, debt_pct, R_w, E_w, NL_w = None, None, None, None, None
    if mac is not None:
        _r = mac[mac["year"] == yr4]
        if len(_r):
            _r = _r.iloc[0]
            _f = lambda c: float(_r[c]) if c in _r.index and pd.notna(_r[c]) else None
            gdp_m = _f("gdp_usd_bn") * 1e3 if _f("gdp_usd_bn") else None
            debt_pct, R_w, E_w, NL_w = (_f("gov_gross_debt_pct_gdp"), _f("gov_revenue_pct_gdp"),
                                        _f("gov_expenditure_pct_gdp"), _f("gov_net_lending_pct_gdp"))
    weo = R_w is not None and E_w is not None
    if weo and NL_w is not None and abs((E_w - R_w) + NL_w) > SUM_TOL:
        log.warning("%s: WEO expenditure - revenue (%.2f) differs from -net lending (%.2f)", where, E_w - R_w, -NL_w)

    def _amt(pct_gdp):
        """US$ (as text) for an item given as % of GDP; empty when GDP isn't available."""
        return fmt_usd(pct_gdp / 100 * gdp_m) if (gdp_m and pd.notna(pct_gdp)) else ""

    rg = rev[rev["year"] == yr4] if rev is not None else None
    g = spd[spd["year"] == yr4] if spd is not None else None
    has_rev_mix = rg is not None and not rg.empty
    has_spd_mix = g is not None and not g.empty

    # ---- side totals (% of GDP) ----
    if weo:
        R, T = R_w, E_w
    else:                       # fallback: each IMF file's own total (they can cover different levels of government)
        R = float(rg["pct_gdp"].sum()) if has_rev_mix else None
        T = None
        if has_spd_mix:
            if "total_pct_gdp" in g.columns and g["total_pct_gdp"].notna().any():
                T = float(g["total_pct_gdp"].dropna().iloc[0])
            else:
                _both = g[g["pct_gdp"].notna() & (g["pct_outlays"] > 0)]
                T = float((100 * _both["pct_gdp"] / _both["pct_outlays"]).median()) if len(_both) else None
    has_rev, has_spd = R is not None, T is not None
    if not (has_rev or has_spd):
        st.info(f"No IMF revenue or spending data for {country_name} in {int(yr4)}.")
        return
    can_compare = has_rev and has_spd
    gap = (T - R) if can_compare else 0.0           # = -WEO net lending when sized from WEO

    ids, labels, parents, values, colors_, texts, hov = [], [], [], [], [], [], []

    def node(id_, label, parent, value, color, hover="", side_total=None):
        ids.append(id_); labels.append(title_case(label)); parents.append(parent); values.append(float(value)); colors_.append(color)
        amt = _amt(value)
        share = (100 * value / side_total) if side_total else None
        texts.append(" - ".join(x for x in (amt, f"{share:.0f}%" if share is not None else "") if x))
        hov.append(" | ".join(x for x in (amt, f"{value:.1f}% of GDP", f"{share:.1f}% of this side" if share is not None else "", hover) if x))

    node("root", "Government budget", "", 0.0, th.RULE)
    leaf_sum = {"rev": 0.0, "spd": 0.0}             # what each side's boxes add up to, checked below

    # ----- revenue side: WEO total, mix from the revenue file rescaled to it (+ borrowing) -----
    if has_rev:
        rev_side = R + max(gap, 0.0)
        node("rev", "Money In: revenue + borrowing" if gap > 0.05 else "Money In: revenue", "root", rev_side,
             th.blend(th.BLUE, 0.12), f"Revenue alone: {_amt(R) + ' = ' if gdp_m else ''}{R:.1f}% of GDP", rev_side)
        if has_rev_mix:
            items = rg.groupby(["label", "group"], sort=False)["pct_gdp"].sum().reset_index()
            mix_tot = float(items["pct_gdp"].sum())
            if "total_pct_gdp" in rg.columns and rg["total_pct_gdp"].notna().any() and \
                    abs(mix_tot - float(rg["total_pct_gdp"].dropna().iloc[0])) > SUM_TOL:
                log.warning("%s: revenue items sum to %.2f%% of GDP, file total is %.2f%%", where, mix_tot,
                            float(rg["total_pct_gdp"].dropna().iloc[0]))
            items["v"] = items["pct_gdp"] * (R / mix_tot) if mix_tot > 0 else 0.0
            tx = items[items["group"] == "Taxes"]
            if not tx.empty:
                node("rev:Taxes", "Taxes", "rev", tx["v"].sum(), REV_GROUP_COLORS["Taxes"], side_total=rev_side)
            for _, r in items.iterrows():
                is_tax = r["group"] == "Taxes"
                node(f"rev:{r['label']}", r["label"], "rev:Taxes" if is_tax else "rev", r["v"],
                     REV_TAX_COLORS.get(r["label"], th.blend(th.BLUE, 0.6)) if is_tax else REV_GROUP_COLORS.get(r["group"], th.OTHER),
                     "not broken out by the IMF" if r["group"] == "Unclassified" else "", rev_side)
                leaf_sum["rev"] += r["v"]
        else:
            node("rev:all", "Revenue (no breakdown)", "rev", R, th.OTHER, "the IMF revenue file has no breakdown for this year", rev_side)
            leaf_sum["rev"] += R
        if gap > 0.05:
            node("rev:debt", "Borrowing (spending beyond revenue)", "rev", gap, BORROWING_COLOR,
                 "Spending exceeded revenue by this much; financed by new borrowing or drawing down reserves", rev_side)
            leaf_sum["rev"] += gap

    # ----- spending side: WEO total, mix from COFOG rescaled to it (+ surplus) -----
    health_pct = None
    if has_spd:
        spd_side = T + max(-gap, 0.0)
        node("spd", "Money out: spending + surplus" if gap < -0.05 else "Money out: spending", "root", spd_side,
             th.blend(th.MUTED, 0.12), f"Spending alone: {_amt(T) + ' = ' if gdp_m else ''}{T:.1f}% of GDP", spd_side)
        if has_spd_mix:
            sh = _spending_shares(g, where)
            grp = g.groupby("label", sort=False)["group"].first()
            hl = [l for l in sh.index if grp[l] == "Health"]
            if hl:
                health_pct = float(sh[hl].sum()) / 100 * T
                node("spd:Health", "Health", "spd", health_pct, th.ROSE, side_total=spd_side)
            for lab, v in sh.items():
                is_h = grp[lab] == "Health"
                node(f"spd:{lab}", lab, "spd:Health" if is_h else "spd", v / 100 * T,
                     th.OTHER if grp[lab] == "Unclassified" else (HEALTH_REDS.get(lab, th.ROSE) if is_h else OTHER_FUNCS.get(lab, th.OTHER)),
                     "not reported by the IMF for this country-year" if grp[lab] == "Unclassified" else
                     ("debt interest, split out of general public services" if lab == "Interest on public debt" else ""), spd_side)
                leaf_sum["spd"] += v / 100 * T
        else:
            node("spd:all", "Spending (no breakdown)", "spd", T, th.OTHER, "no IMF spending-by-function data for this year", spd_side)
            leaf_sum["spd"] += T
        if gap < -0.05:
            node("spd:surplus", "Surplus (revenue not spent)", "spd", -gap, th.blend(th.TEAL, 0.45),
                 "Revenue exceeded spending by this much (saved or used to pay down debt)", spd_side)
            leaf_sum["spd"] += -gap

    # every side's boxes must add up to that side's total
    for side_id, side_tot in (("rev", R + max(gap, 0.0) if has_rev else None), ("spd", T + max(-gap, 0.0) if has_spd else None)):
        if side_tot is not None and abs(leaf_sum[side_id] - side_tot) > 0.01:
            log.warning("%s: %s boxes add up to %.2f%% of GDP, side total is %.2f%%", where, side_id, leaf_sum[side_id], side_tot)

    # parents hold (slightly more than) the sum of their children, computed bottom-up so branchvalues="total" always validates
    acc = {}
    for idx in range(len(ids) - 1, -1, -1):
        if ids[idx] in acc:
            values[idx] = acc[ids[idx]] * 1.000001
        acc[parents[idx]] = acc.get(parents[idx], 0.0) + values[idx]
    texts[0], hov[0] = "", ""
    fig4 = go.Figure(go.Treemap(
        ids=ids, labels=labels, parents=parents, values=values, branchvalues="total", text=texts,
        marker=dict(colors=colors_, line=dict(width=2, color=th.SURFACE)), customdata=hov, textinfo="label+text",
        hovertemplate="<b>%{label}</b><br>%{customdata}<extra></extra>", sort=False,
    ))
    fig4.update_layout(title=dict(text=f"Government Revenue and Spending, {int(yr4)}"), height=720,
                       margin=dict(l=0, r=0, t=50, b=0))
    chart(fig4)

    # ---------------- headline numbers ----------------
    mix = []
    if has_rev_mix:
        mix.append(f"revenue mix: IMF revenue data ({rg['coverage'].iloc[0].lower()})")
    if has_spd_mix:
        mix.append(f"spending mix: IMF COFOG ({g['coverage'].iloc[0].lower()})")
    size = ("Totals: IMF World Economic Outlook, general government" if weo else
            "Totals: the IMF revenue and spending files (WEO totals missing for this year)")
    _basis = f"{size}; {'; '.join(mix)}." + (" Dollar amounts = share of GDP x GDP (current US$, IMF WEO)." if gdp_m else "")
    mcols = st.columns(4)
    def _m(col, label, pct, signed=False, help=None):
        if gdp_m:
            stat(col, label, (("-" if pct < 0 else "+") if signed else "") + _amt(abs(pct)), help=help)
        else:
            stat(col, label, f"{pct:+.1f}% of GDP" if signed else f"{pct:.1f}% of GDP", help=help)
    if has_rev:
        _m(mcols[0], f"Revenue, {int(yr4)}", R, help=f"{R:.1f}% of GDP. " + _basis)
    if has_spd:
        _m(mcols[1], f"Spending, {int(yr4)}", T, help=f"{T:.1f}% of GDP. " + _basis)
    if can_compare:
        _m(mcols[2], "Revenue Minus Spending", -gap, signed=True,
           help=f"{-gap:+.1f}% of GDP. " + ("IMF WEO net lending (+) / borrowing (-), general government."
                                             if weo else "Revenue file minus spending file; they can cover different "
                                                         "levels of government, so treat it as a rough indication."))
    if debt_pct is not None:
        stat(mcols[3], f"Gross Government Debt, {int(yr4)}", _amt(debt_pct) if gdp_m else f"{debt_pct:.0f}% of GDP",
             help=f"{debt_pct:.0f}% of GDP. IMF World Economic Outlook; the stock of debt outstanding.")

    st.caption("Both sides are drawn to the same scale; the dark purple box is borrowing.")
    if not weo:
        st.caption("The IMF World Economic Outlook has no general-government totals for this year, so each side is "
                   "sized from its own IMF file, and the two can cover different levels of government.")
    # COFOG often misses health spending outside central budgets: compare with IHME
    if health_pct is not None and crow["has_spend"] and (SPEND_DIR / f"{iso}.csv").exists():
        _sp = load_spending(iso)
        if "ghes_per_gdp_mean" in _sp.columns:
            _h = _sp.loc[_sp["year"] == yr4, "ghes_per_gdp_mean"]
            if len(_h) and pd.notna(_h.iloc[0]) and health_pct < 0.5 * float(_h.iloc[0]) * 100:
                st.caption(f"The IMF records only part of {country_name}'s health spending (for example, spending by "
                           f"local governments); IHME puts government health spending at {float(_h.iloc[0]) * 100:.1f}% "
                           "of GDP.")


_budget_section()



# =========================================================================== #
# SECTION 4 - the model: funding cut -> fiscal response -> coverage -> lives
# =========================================================================== #
_imf = {}
_mac4 = load_macro(crow["iso3"]) if any(MACRO_DIR.glob("*.csv")) else None
if _mac4 is not None and "gov_gross_debt_pct_gdp" in _mac4.columns:
    _d = _mac4[_mac4["gov_gross_debt_pct_gdp"].notna() & (_mac4["year"] <= 2024)]
    if len(_d):
        _imf["debt_pct_gdp"] = float(_d["gov_gross_debt_pct_gdp"].iloc[-1])
_rev4 = load_revenue(crow["iso3"]) if REVENUE_DIR.exists() else None
if _rev4 is not None and not _rev4.empty:
    _ry = _rev4[_rev4["year"] <= 2024]["year"].max()
    if pd.notna(_ry):
        _imf["revenue_pct_gdp"] = float(_rev4.loc[_rev4["year"] == _ry, "pct_gdp"].sum())
render_model_section(crow["iso3"], country_name, _imf, ALLOWED_COUNTRIES)
