"""
Who funds health in each country?  (IHME Development Assistance for Health, 1990-2025)

Run:   streamlit run app.py
Data:  ./country_data/<Country>.csv   (created by prepare_data.py)
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

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
TOP_N_FUNDERS = 10                       # chart 1 shows this many funders individually, fixed
DEFAULT_COUNTRY = "Kenya"
# Only these countries appear in the dropdown (ISO3 code -> name shown)
ALLOWED_COUNTRIES = {
    "AFG": "Afghanistan",
    "ALB": "Albania",
    "AGO": "Angola",
    "ARM": "Armenia",
    "AZE": "Azerbaijan",
    "BGD": "Bangladesh",
    "BLR": "Belarus",
    "BLZ": "Belize",
    "BEN": "Benin",
    "BOL": "Bolivia",
    "BWA": "Botswana",
    "BRA": "Brazil",
    "BFA": "Burkina Faso",
    "BDI": "Burundi",
    "KHM": "Cambodia",
    "CMR": "Cameroon",
    "CAF": "Central African Republic",
    "CHN": "China",
    "COL": "Colombia",
    "CRI": "Costa Rica",
    "CIV": "Cote d'Ivoire",
    "COD": "Democratic Republic of the Congo",
    "DJI": "Djibouti",
    "DOM": "Dominican Republic",
    "ECU": "Ecuador",
    "EGY": "Egypt",
    "SLV": "El Salvador",
    "SWZ": "Eswatini",
    "ETH": "Ethiopia",
    "FJI": "Fiji",
    "GMB": "Gambia",
    "GEO": "Georgia",
    "GHA": "Ghana",
    "GTM": "Guatemala",
    "GIN": "Guinea",
    "GUY": "Guyana",
    "HTI": "Haiti",
    "HND": "Honduras",
    "IND": "India",
    "IDN": "Indonesia",
    "IRQ": "Iraq",
    "JAM": "Jamaica",
    "JOR": "Jordan",
    "KAZ": "Kazakhstan",
    "KEN": "Kenya",
    "KSV": "Kosovo",
    "KGZ": "Kyrgyzstan",
    "LAO": "Laos",
    "LSO": "Lesotho",
    "LBR": "Liberia",
    "LBY": "Libya",
    "MDG": "Madagascar",
    "MWI": "Malawi",
    "MLI": "Mali",
    "MUS": "Mauritius",
    "MEX": "Mexico",
    "MDA": "Moldova",
    "MNG": "Mongolia",
    "MAR": "Morocco",
    "MOZ": "Mozambique",
    "MMR": "Burma (Myanmar)",
    "NAM": "Namibia",
    "NPL": "Nepal",
    "NIC": "Nicaragua",
    "NER": "Niger",
    "NGA": "Nigeria",
    "PAK": "Pakistan",
    "PAN": "Panama",
    "PNG": "Papua New Guinea",
    "PRY": "Paraguay",
    "PER": "Peru",
    "PHL": "Philippines",
    "ROU": "Romania",
    "RUS": "Russia",
    "RWA": "Rwanda",
    "STP": "Sao Tome and Principe",
    "SEN": "Senegal",
    "SLE": "Sierra Leone",
    "SOM": "Somalia",
    "ZAF": "South Africa",
    "SSD": "South Sudan",
    "SDN": "Sudan",
    "TJK": "Tajikistan",
    "TZA": "Tanzania",
    "THA": "Thailand",
    "TLS": "Timor-Leste",
    "TGO": "Togo",
    "TTO": "Trinidad and Tobago",
    "TKM": "Turkmenistan",
    "UGA": "Uganda",
    "UKR": "Ukraine",
    "UZB": "Uzbekistan",
    "VEN": "Venezuela",
    "VNM": "Vietnam",
    "PSE": "West Bank and Gaza",
    "YEM": "Yemen",
    "ZMB": "Zambia",
    "ZWE": "Zimbabwe",
}

HATCH_SHAPE = "+"                        # plotly pattern: "+" grid, "x" crosshatch, "/" diagonal

# Channels treated as "NGO / foundation" money. IHME does NOT record whether a
# recipient government knew about a flow -- channel is only a proxy. These are
# the defaults; the sidebar lets you change them live.
DEFAULT_NONGOV_CHANNELS = ["NGO", "INTLNGO", "US_FOUND", "GATES"]

CHANNEL_LABELS = {
    "NGO": "US NGOs", "INTLNGO": "International NGOs", "US_FOUND": "US foundations",
    "GATES": "Gates Foundation", "GAVI": "Gavi", "GFATM": "Global Fund", "CEPI": "CEPI",
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
    "nch": "Newborn & child health",
    "oid": "Other infectious diseases",
    "ncd": "Non-communicable diseases",
    "swap_hss_total": "Health systems strengthening / SWAps",
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

# Chart 2 components: (column prefix, label, colour). Stack order = bottom to top.
SPEND_PARTS = [
    ("ghes", "Government spending", "#1b6ca8"),
    ("ppp", "Prepaid private spending", "#7a5195"),
    ("oop", "Out-of-pocket spending", "#e08a1e"),
    ("dah", "Development assistance for health (DAH)", "#2a9d6f"),
]
COFOG_ALL_DIR = Path(__file__).parent / "cofog_all"        # IMF: whole-government spending by function, per ISO3
HEALTH_REDS = {"Medical products": "#f1948a", "Outpatient services": "#ec7063", "Hospital services": "#cb4335",
               "Public health services": "#e59866", "Health R&D": "#a93226", "Other health": "#d98880",
               "Health (no breakdown)": "#cb4335"}
OTHER_FUNCS = {"General public services": "#7f8c8d", "Defence": "#5d6d7e", "Public order and safety": "#566573",
               "Economic affairs": "#2e86c1", "Environmental protection": "#28b463", "Housing and community amenities": "#a569bd",
               "Recreation, culture and religion": "#f5b041", "Education": "#17a589", "Social protection": "#5b7db1",
               "Interest on public debt": "#884ea0"}
MACRO_DIR = Path(__file__).parent / "macro_data"          # IMF WEO: GDP, population, debt, per ISO3
REVENUE_DIR = Path(__file__).parent / "revenue_data"      # IMF WoRLD: government revenue by type, per ISO3
REV_GROUP_COLORS = {"Taxes": "#2e86c1", "Social contributions": "#17a589", "Grants": "#58b368",
                    "Other revenue": "#e59b2d", "Unclassified": "#bdc3c7"}
REV_TAX_COLORS = {"Personal income tax": "#1f618d", "Corporate income tax": "#2874a6", "Other income taxes": "#5499c7",
                  "Income taxes": "#2874a6", "VAT / sales tax": "#3498db", "Excise taxes": "#5dade2",
                  "Other goods & services taxes": "#85c1e9", "Goods & services taxes": "#3498db",
                  "Trade taxes (customs)": "#7fb3d5", "Property taxes": "#a9cce3", "Other taxes": "#d4e6f1"}
def _resolve_dir(d: Path) -> Path:
    """Use <d>/<d.name> if the folder was unzipped one level too deep."""
    inner = d / d.name
    if not any(d.glob("*.csv")) and inner.is_dir() and any(inner.glob("*.csv")):
        return inner
    return d


DATA_DIR, SPEND_DIR, COFOG_ALL_DIR, REVENUE_DIR, MACRO_DIR = (_resolve_dir(p) for p in (DATA_DIR, SPEND_DIR, COFOG_ALL_DIR, REVENUE_DIR, MACRO_DIR))
SPEND_LAST_OBSERVED = 2023                 # 2024+ are IHME expected values

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


def load_cofog_all(iso3: str):
    p = COFOG_ALL_DIR / f"{iso3}.csv"
    return pd.read_csv(p) if p.exists() else None


def load_macro(iso3: str):
    p = MACRO_DIR / f"{iso3}.csv"
    return pd.read_csv(p) if p.exists() else None


def load_revenue(iso3: str):
    p = REVENUE_DIR / f"{iso3}.csv"
    return pd.read_csv(p) if p.exists() else None


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
    df["source"] = df["source"].str.replace("_", " ").str.strip()
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


def hex_to_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


# --------------------------------------------------------------------------- #
# Page
# --------------------------------------------------------------------------- #
st.set_page_config(page_title="Health financing", page_icon="📊", layout="wide")
st.title("Health financing by country")
st.caption("IHME Development Assistance for Health (1990-2025) and Global Health Spending (1995-2023, "
           "expected 2024-2050). Constant 2023 US$.")

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

# ---- country picker (left) with GDP / population / health-spend pills to its right ------ #
pick_col, pill1, pill2 = st.columns([1.5, 2, 2])
with pick_col:
    default_i = int(countries.index[countries["name"] == DEFAULT_COUNTRY][0]) if (countries["name"] == DEFAULT_COUNTRY).any() else 0
    country_label = st.selectbox("Country", countries["label"], index=default_i)
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
_hs_cents, _hs_yr = None, None
if crow["has_spend"] and (SPEND_DIR / f"{crow['iso3']}.csv").exists():
    _sp0 = load_spending(crow["iso3"])
    if "the_per_gdp_mean" in _sp0.columns:
        _r0 = _sp0[_sp0["year"] == SPEND_LAST_OBSERVED]
        if len(_r0) and pd.notna(_r0["the_per_gdp_mean"].iloc[0]):
            _hs_cents, _hs_yr = float(_r0["the_per_gdp_mean"].iloc[0]) * 100, SPEND_LAST_OBSERVED


def _pill(label, value, rgb, tip=""):
    return (f"<div title='{tip}' style='margin-top:1.8rem;min-height:38px;border-radius:20px;display:flex;align-items:center;"
            f"justify-content:center;gap:8px;padding:0 14px;box-sizing:border-box;background:rgba({rgb},0.14);"
            f"border:2px solid rgba({rgb},0.7);white-space:nowrap'>"
            f"<span style='font-size:13px;opacity:0.75'>{label}</span><span style='font-size:16px;font-weight:700'>{value}</span></div>")


with pill1:
    st.markdown(_pill(f"GDP{', ' + str(_gdp_yr) if _gdp_yr else ''}", fmt_usd(_gdp_bn * 1e3) if _gdp_bn else "n/a", "46,134,193",
                      "Current US$, IMF World Economic Outlook"), unsafe_allow_html=True)
with pill2:
    st.markdown(_pill(f"Population{', ' + str(_pop_yr) if _pop_yr else ''}",
                      ((f"{_pop_m:,.1f}" if _pop_m >= 1 else f"{_pop_m:,.2f}") + "M") if _pop_m else "n/a", "39,174,96",
                      "Millions of people, IMF World Economic Outlook"), unsafe_allow_html=True)

st.divider()

# =========================================================================== #
# CHART 2 - total health spending by source: past vs expected
# =========================================================================== #
st.header(f"1. Money spent on health in {country_name}, over time")

if not crow["has_spend"] or not (SPEND_DIR / f"{crow['iso3']}.csv").exists():
    st.info(f"{country_name} isn't in the IHME health-spending dataset (it covers 204 countries and territories), "
            "so there is no spending breakdown to show.")
else:
    sp = load_spending(crow["iso3"])
    if True:
        view = st.radio("Show as", ["US$ total", "US$ per person", "Share of total (%)"],
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

        opac = [0.55 if p else 1.0 for p in proj]
        for k, label, col in SPEND_PARTS:
            fig2.add_bar(
                x=w["year"], y=w[f"v_{k}"], name=label,
                customdata=[[fmt_usd(v * _div)] for v in w[f"v_{k}"]] if view == "US$ total" else None,
                marker=dict(color=col, line=dict(color=col, width=0.5), opacity=opac),
                hovertemplate=_hov(label) + "<extra></extra>",
            )
        if y1 > SPEND_LAST_OBSERVED:
            fig2.add_vrect(x0=max(y0, SPEND_LAST_OBSERVED + 1) - 0.5, x1=y1 + 0.5, fillcolor="rgba(128,128,128,0.10)",
                           line_width=0, annotation_text="IHME expected (projected)", annotation_position="top left",
                           annotation_font=dict(size=12, color="gray"))
        fig2.update_layout(
            barmode="stack", height=680, margin=dict(l=10, r=10, t=30, b=10),
            xaxis=dict(range=[y0 - 0.5, y1 + 0.5], dtick=1, tickangle=-45, title="", automargin=True),
            yaxis=dict(title=ylab, rangemode="tozero", automargin=True, **({"range": [0, 100]} if view.startswith("Share") else {})),
            legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="left", x=0),
            bargap=0.15, hovermode="closest",
        )
        st.plotly_chart(fig2, **WIDE)

        last_obs = sp[sp["year"] == SPEND_LAST_OBSERVED].iloc[0]
        end = sp[sp["year"] == min(y1, int(sp["year"].max()))].iloc[0]
        k1, k2, k3 = st.columns(3)
        k1.metric(f"Total spending, {SPEND_LAST_OBSERVED}", fmt_usd(last_obs['the_total_mean'] / 1e3))
        k2.metric(f"DAH share of total, {SPEND_LAST_OBSERVED}", f"{last_obs['dah_total_mean'] / last_obs['the_total_mean']:.0%}")
        k3.metric(f"DAH share of total, {int(end['year'])} (expected)" if end["year"] > SPEND_LAST_OBSERVED else f"DAH share, {int(end['year'])}",
                  f"{end['dah_total_mean'] / end['the_total_mean']:.0%}")
        st.caption(
            "Solid bars are IHME's estimates through 2023; paler bars after 2023 are IHME's *expected* (projected) spending. "
            "Government, prepaid private and out-of-pocket are domestic sources; DAH is aid from abroad. The four parts add up "
            "to total health spending."
        )


st.divider()

# =========================================================================== #
# CHART 1 - who funds health (DAH)
# =========================================================================== #
st.header(f"2. Health aid in {country_name}: who is providing the money")

if pd.isna(crow["dah_file"]):
    st.info(f"{country_name} is not a recipient in the IHME DAH database (typically a high-income country), "
            "so there is no aid-funder breakdown to show.")
else:
    df = load_country(crow["dah_file"])
    c1, c2 = st.columns(2)
    with c1:
        hfa = st.selectbox("Health category", list(HFA_LABELS), format_func=HFA_LABELS.get, key="c1_hfa")
    value_col, metric_label = "dah_23", HFA_LABELS["total"]
    if hfa != "total":
        value_col, metric_label = f"{hfa}_dah_23", HFA_LABELS[hfa]
        pas = program_area_options(df, hfa) if hfa in HFAS_WITH_PROGRAM_AREAS else {}
        if pas:
            with c2:
                pa = st.selectbox("Program area", ["All program areas"] + list(pas),
                                  format_func=lambda k: k if k == "All program areas" else pas[k],
                                  key=f"c1_pa_{hfa}")
            if pa != "All program areas":
                value_col, metric_label = pa, f"{HFA_LABELS[hfa]}: {pas[pa]}"
    nongov = st.multiselect(
        "Channels drawn as NGO / foundation (checkered)",
        options=list(CHANNEL_LABELS), default=DEFAULT_NONGOV_CHANNELS, key="c1_ngo",
        format_func=lambda c: f"{CHANNEL_LABELS[c]} ({c})",
        help="IHME doesn't record whether a government knew about a flow. "
             "The channel that delivered the money is used as a proxy.",
    )

    d = df[["year", "source", "channel", value_col]].rename(columns={value_col: "val"})
    d["val"] = d["val"] / 1e3                       # thousands of US$ -> millions of US$
    d["route"] = d["channel"].isin(nongov).map({True: "ngo", False: "gov"})
    last_data_year = int(df.loc[df["dah_23"] != 0, "year"].max()) if (df["dah_23"] != 0).any() else YEAR_MIN

    window = d[(d["year"] >= YEAR_MIN) & (d["year"] <= YEAR_MAX)]
    ranked = window.groupby("source")["val"].sum().sort_values(ascending=False)
    ranked = ranked[ranked > 0]
    top = list(ranked.index[:TOP_N_FUNDERS])
    window = window.assign(source=window["source"].where(window["source"].isin(top), "All other sources"))
    agg = window.groupby(["year", "source", "route"], as_index=False)["val"].sum()
    # which organizations the checkered money went through, per bar (for hover text)
    ngo_detail = (window[window["route"] == "ngo"].groupby(["year", "source", "channel"])["val"].sum().reset_index())
    ngo_detail = ngo_detail[ngo_detail["val"] > 0]
    ngo_detail["txt"] = ngo_detail["channel"].map(lambda c: CHANNEL_LABELS.get(c, c)) + ": " + ngo_detail["val"].map(fmt_usd)
    ngo_hover = ngo_detail.groupby(["year", "source"])["txt"].apply("<br>".join).to_dict()
    # axis unit adapts to size (millions / billions / trillions)
    unit_div, unit_name, unit_sfx = pick_unit(agg.groupby("year")["val"].sum().max() if len(agg) else 0)
    agg["val"] = agg["val"] / unit_div
    order = top + (["All other sources"] if (agg["source"] == "All other sources").any() else [])

    palette = ["#1f77b4", "#d62728", "#2ca02c", "#ff7f0e", "#9467bd", "#8c564b", "#e377c2",
               "#17becf", "#bcbd22", "#393b79", "#637939", "#843c39", "#7b4173", "#3182bd", "#e6550d"]
    colors = {s: palette[i % len(palette)] for i, s in enumerate(top)}
    colors["All other sources"] = "#9aa0a6"

    st.subheader(f"{country_name} - {metric_label}")
    latest = d[d["year"] == last_data_year]
    tot = latest["val"].sum()
    if tot > 0:
        ngo_share = latest.loc[latest["route"] == "ngo", "val"].sum() / tot
        top_src = latest.groupby("source")["val"].sum().idxmax()
        m1, m2, m3 = st.columns(3)
        m1.metric(f"Total in {last_data_year}", fmt_usd(tot))
        m2.metric(f"Via NGO / foundation channels, {last_data_year}", f"{ngo_share:.0%}")
        m3.metric(f"Largest funder, {last_data_year}", top_src)
    else:
        st.info("No funding recorded for this selection.")

    fig = go.Figure()
    for s in order:
        col = colors[s]
        for route in ("gov", "ngo"):
            sub = agg[(agg["source"] == s) & (agg["route"] == route)]
            if sub.empty:
                continue
            marker = dict(color=col, line=dict(color=col, width=0.5))
            if route == "ngo":
                marker = dict(
                    color=hex_to_rgba(col, 0.25), line=dict(color=col, width=0.8),
                    pattern=dict(shape=HATCH_SHAPE, fgcolor=col, bgcolor=hex_to_rgba(col, 0.15), size=7, solidity=0.55),
                )
            amts = [fmt_usd(v * unit_div) for v in sub["val"]]          # exact amount with its own unit (M / B / T)
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
    fig.add_bar(x=[None], y=[None], name="Solid: government-facing channels", legendgroup="_key1",
                marker=dict(color="#555"), hoverinfo="skip")
    for ch in nongov:
        fig.add_bar(x=[None], y=[None], name=f"Checkered: via {CHANNEL_LABELS.get(ch, ch)}", legendgroup=f"_key_{ch}",
                    marker=dict(color="rgba(85,85,85,0.25)", line=dict(color="#555", width=0.8),
                                pattern=dict(shape=HATCH_SHAPE, fgcolor="#555", bgcolor="rgba(85,85,85,0.15)", size=7, solidity=0.55)),
                    hoverinfo="skip")
    if last_data_year < YEAR_MAX:
        fig.add_vrect(x0=last_data_year + 0.5, x1=YEAR_MAX + 0.5, fillcolor="rgba(128,128,128,0.10)", line_width=0,
                      annotation_text="no data yet (forecast to come)", annotation_position="top left",
                      annotation_font=dict(size=12, color="gray"))
    fig.update_layout(
        barmode="stack", height=560, margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(range=[YEAR_MIN - 0.5, YEAR_MAX + 0.5], dtick=1, tickangle=-45, title=""),
        yaxis=dict(title=f"US$ {unit_name} (constant 2023)", rangemode="tozero"),
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.01),
        bargap=0.15, hovermode="closest",
    )
    st.plotly_chart(fig, **WIDE)

    if crow["is_country"] and last_data_year < 2024:
        st.caption(f"IHME's recipient-level aid data ends in {last_data_year}: 2024-2025 estimates exist only as "
                   "unallocated totals with no country attached, so they can't be shown here.")
    st.caption(
        "**Reading the chart:** colour = who the money originally came from (source). Checkered = delivered through "
        "NGO/foundation channels, a *proxy* for flows that may bypass the recipient government. IHME does not record "
        "government awareness directly, and some government-facing channels (e.g. bilateral agencies, the Global Fund) "
        "also fund NGOs on the ground."
    )


# =========================================================================== #
# CHART 3 - what health aid is spent on (DAH by health focus area)
# =========================================================================== #
st.subheader("...and where is it being spent?")

FOCUS_COLORS = {
    "hiv": "#c0392b", "mal": "#e67e22", "tb": "#8e5ea2", "rmh": "#e377c2", "nch": "#2e86c1",
    "oid": "#27ae60", "ncd": "#7f6a3a", "swap_hss_total": "#16a085", "other": "#95a5a6", "unalloc": "#cfd4d8",
}
if pd.isna(crow["dah_file"]):
    st.info(f"{country_name} is not a recipient in the IHME DAH database, so there is no category breakdown to show.")
else:
    df3 = load_country(crow["dah_file"])
    e1, e2, e3 = st.columns([2, 2, 2])
    with e1:
        view3 = st.radio("Show as", ["US$ total", "Share of total (%)"], horizontal=True, key="c3b_view")
    with e2:
        brk = st.selectbox("Break down", ["Health focus areas (HIV, TB, malaria, ...)"] +
                           [f"Inside: {HFA_LABELS[h]}" for h in HFAS_WITH_PROGRAM_AREAS], key="c3b_break")

    parts = []                      # (column, label, color)
    if brk.startswith("Health focus"):
        parts = [(f"{h}_dah_23", HFA_LABELS[h], FOCUS_COLORS[h]) for h in FOCUS_COLORS]
        sub_title = "all health focus areas"
    else:
        h = next(k for k in HFAS_WITH_PROGRAM_AREAS if brk == f"Inside: {HFA_LABELS[k]}")
        pas3 = program_area_options(df3, h)
        shades = ["#1b4f72", "#2874a6", "#5dade2", "#aed6f1", "#117a65", "#52be80", "#f5b041", "#e59866", "#af7ac5", "#bfc9ca", "#7f8c8d"]
        parts = [(c, lab, shades[i % len(shades)]) for i, (c, lab) in enumerate(pas3.items())]
        sub_title = HFA_LABELS[h]

    cols = [c for c, _, _ in parts if c in df3.columns]
    byyr = df3.groupby("year")[cols].sum() / 1e3                     # thousands of US$ -> millions
    byyr = byyr.reindex(range(YEAR_MIN, YEAR_MAX + 1))
    byyr = byyr.loc[:, byyr.fillna(0).abs().sum() > 0]               # drop categories with nothing
    data_end = int(df3.loc[df3["dah_23"] != 0, "year"].max()) if (df3["dah_23"] != 0).any() else YEAR_MIN
    byyr.loc[byyr.index > data_end] = np.nan                         # blank after data ends
    if byyr.empty or byyr.fillna(0).abs().to_numpy().sum() == 0:
        st.info("No funding recorded for this selection.")
    else:
        tot_y = byyr.sum(axis=1, min_count=1)
        div3, name3, sfx3 = pick_unit(tot_y.max())
        fig4 = go.Figure()
        order3 = byyr.sum().sort_values(ascending=False).index
        lab3 = {c: (lab, col) for c, lab, col in parts}
        for c in order3:
            lab, col = lab3[c]
            if view3.startswith("Share"):
                yv = 100 * byyr[c] / tot_y.where(tot_y > 0)
                hov = f"<b>{lab}</b><br>%{{x}}: %{{y:,.1f}}% of aid<extra></extra>"
            else:
                yv = byyr[c] / div3
                hov = f"<b>{lab}</b><br>%{{x}}: %{{customdata[0]}}<extra></extra>"
            fig4.add_bar(x=byyr.index, y=yv, name=lab, marker=dict(color=col, line=dict(color=col, width=0.5)), hovertemplate=hov,
                         customdata=None if view3.startswith("Share") else [[fmt_usd(v)] for v in byyr[c]])
        fig4.update_layout(
            barmode="stack", height=560, margin=dict(l=10, r=10, t=30, b=10),
            xaxis=dict(range=[YEAR_MIN - 0.5, YEAR_MAX + 0.5], dtick=1, tickangle=-45, title="", automargin=True),
            yaxis=dict(title=("% of health aid" if view3.startswith("Share") else f"US$ {name3} (constant 2023)"),
                       rangemode="tozero", automargin=True, **({"range": [0, 100]} if view3.startswith("Share") else {})),
            legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="left", x=0),
            bargap=0.15, hovermode="closest",
        )
        if data_end < YEAR_MAX:
            fig4.add_vrect(x0=data_end + 0.5, x1=YEAR_MAX + 0.5, fillcolor="rgba(128,128,128,0.08)", line_width=0,
                           annotation_text="No data yet", annotation_position="top left", annotation_font=dict(size=12, color="gray"))
        st.plotly_chart(fig4, **WIDE)
        st.caption(
            f"{country_name}: development assistance for health received, split by what it pays for ({sub_title}). "
            "Source: IHME DAH database, constant 2023 US$. This is aid only: IHME's total-spending files (government, "
            "private, out-of-pocket) are not split by disease. 'Unallocated' is aid with no focus-area information."
        )


st.divider()

# =========================================================================== #
# SECTION 4 - the government budget: one treemap, revenue side and spending side sized to each other
# =========================================================================== #
st.header(f"3. The government's role in {country_name}: revenue (money in) and spending (money out)")

def _budget_section():
    rev = load_revenue(crow["iso3"]) if REVENUE_DIR.exists() else None
    spd = load_cofog_all(crow["iso3"]) if COFOG_ALL_DIR.exists() else None
    rev_years = set(rev["year"].unique()) if rev is not None and not rev.empty else set()
    spd_years = set(spd["year"].unique()) if spd is not None and not spd.empty else set()

    if not rev_years and not spd_years:
        st.info(f"The IMF files have no government revenue or spending-by-function data for {country_name}.")
    else:
        both = sorted(rev_years & spd_years, reverse=True)
        years_all = sorted(rev_years | spd_years, reverse=True)
        default_y = both[0] if both else years_all[0]
        _, ymid, _ = st.columns([1, 1, 1])
        with ymid:
            yr4 = st.selectbox("Year", years_all, index=years_all.index(default_y), key=f"c4_year_{crow['iso3']}")

        # GDP used to turn IMF "% of GDP" into dollars: IMF WEO GDP in current US$ for that year (actual figures);
        # falls back to GDP backed out of IHME's health-spending ratios (constant 2023 US$, approximate)
        gdp_m, gdp_basis, debt_pct = None, "", None
        _mac = load_macro(crow["iso3"]) if any(MACRO_DIR.glob("*.csv")) else None
        if _mac is not None:
            _r = _mac[_mac["year"] == yr4]
            if len(_r):
                if pd.notna(_r["gdp_usd_bn"].iloc[0]):
                    gdp_m, gdp_basis = float(_r["gdp_usd_bn"].iloc[0]) * 1e3, "current US$ (IMF World Economic Outlook)"
                if "gov_gross_debt_pct_gdp" in _r.columns and pd.notna(_r["gov_gross_debt_pct_gdp"].iloc[0]):
                    debt_pct = float(_r["gov_gross_debt_pct_gdp"].iloc[0])
        if gdp_m is None and crow["has_spend"] and (SPEND_DIR / f"{crow['iso3']}.csv").exists():
            _sp = load_spending(crow["iso3"])
            if "gdp_usd_k" in _sp.columns:
                _gdp_k = _sp["gdp_usd_k"]
            elif {"the_total_mean", "the_per_gdp_mean"} <= set(_sp.columns):
                _gdp_k = _sp["the_total_mean"] / _sp["the_per_gdp_mean"].where(_sp["the_per_gdp_mean"] > 0)
            else:
                _gdp_k = None
            if _gdp_k is not None:
                _g = _gdp_k[_sp["year"] == yr4]
                if len(_g) and pd.notna(_g.iloc[0]) and _g.iloc[0] > 0:
                    gdp_m, gdp_basis = float(_g.iloc[0]) / 1e3, "constant 2023 US$ (backed out of IHME ratios, approximate)"

        def _amt(pct_gdp):
            """US$ (as text) for an item given as % of GDP; empty when GDP isn't available."""
            return fmt_usd(pct_gdp / 100 * gdp_m) if (gdp_m and pd.notna(pct_gdp)) else ""

        rg = rev[rev["year"] == yr4] if rev is not None else None
        g = spd[spd["year"] == yr4] if spd is not None else None
        has_rev = rg is not None and not rg.empty
        has_spd = g is not None and not g.empty
        if not has_rev:
            if rev_years:
                st.info(f"No IMF revenue data for {country_name} in {int(yr4)}; revenue is available for "
                        f"{int(min(rev_years))}-{int(max(rev_years))} - pick another year.")
            elif not any(REVENUE_DIR.glob("*.csv")):
                st.info("Revenue isn't showing because the `revenue_data/` folder wasn't found next to this script.")
            else:
                st.info(f"The IMF revenue file has no data for {country_name}.")

        # ---- sizes in % of GDP, so the revenue side and the spending side are directly comparable ----
        R = float(rg["pct_gdp"].sum()) if has_rev else None
        T = None
        if has_spd:
            if "total_pct_gdp" in g.columns and g["total_pct_gdp"].notna().any():
                T = float(g["total_pct_gdp"].dropna().iloc[0])
            else:
                _both = g[g["pct_gdp"].notna() & (g["pct_outlays"] > 0)]
                T = float((100 * _both["pct_gdp"] / _both["pct_outlays"]).median()) if len(_both) else None
        can_compare = has_rev and has_spd and T is not None
        if has_spd and T is None:
            st.info("The IMF spending data for this year has no size information (% of GDP), so spending can't be drawn to scale"
                    + ("; showing revenue only." if has_rev else "."))
            has_spd = False
        if not (has_rev or has_spd):
            st.info(f"No IMF revenue or spending data for {country_name} in {int(yr4)}.")
            return

        gap = (T - R) if can_compare else 0.0
        ids, labels, parents, values, colors_, texts, hov = [], [], [], [], [], [], []

        def node(id_, label, parent, value, color, hover="", side_total=None):
            ids.append(id_); labels.append(label); parents.append(parent); values.append(float(value)); colors_.append(color)
            amt = _amt(value)
            share = (100 * value / side_total) if side_total else None
            texts.append(" - ".join(x for x in (amt, f"{share:.0f}%" if share is not None else "") if x))
            hov.append(" | ".join(x for x in (amt, f"{value:.1f}% of GDP", f"{share:.1f}% of this side" if share is not None else "", hover) if x))

        side = max(R or 0.0, T or 0.0) if can_compare else None       # both sides are drawn to this same total
        node("root", "Government budget", "", 0.0, "#d5d8dc")

        # ----- revenue side (+ borrowing when spending exceeds revenue) -----
        if has_rev:
            rev_side = (R + max(gap, 0.0)) if can_compare else R
            node("rev", "Money in: revenue + borrowing" if (can_compare and gap > 0.05) else "Money in: revenue", "root", rev_side, "#d6eaf8",
                 f"Revenue alone: {_amt(R) + ' = ' if gdp_m else ''}{R:.1f}% of GDP", rev_side)
            tx = rg[rg["group"] == "Taxes"]
            if not tx.empty:
                node("rev:Taxes", "Taxes", "rev", tx["pct_gdp"].sum(), REV_GROUP_COLORS["Taxes"], side_total=rev_side)
            for _, r in rg.iterrows():
                node(f"rev:{r['label']}", r["label"], "rev:Taxes" if r["group"] == "Taxes" else "rev", r["pct_gdp"],
                     REV_TAX_COLORS.get(r["label"], "#5499c7") if r["group"] == "Taxes" else REV_GROUP_COLORS.get(r["group"], "#7f8c8d"),
                     "not broken out by the IMF" if r["group"] == "Unclassified" else "", rev_side)
            if can_compare and gap > 0.05:
                node("rev:debt", "Borrowing / debt (spending beyond revenue)", "rev", gap, "#4a235a",
                     "Spending exceeded revenue by this much; the gap is financed by new borrowing or drawing down reserves", rev_side)

        # ----- spending side (+ surplus when revenue exceeds spending) -----
        if has_spd:
            spd_side = (T + max(-gap, 0.0)) if can_compare else T
            node("spd", "Money out: spending + surplus" if (can_compare and gap < -0.05) else "Money out: spending", "root", spd_side, "#fadbd8",
                 f"Spending alone: {_amt(T) + ' = ' if gdp_m else ''}{T:.1f}% of GDP", spd_side)
            hg = g[g["group"] == "Health"]
            if not hg.empty:
                node("spd:Health", "Health", "spd", hg["pct_outlays"].sum() / 100 * T, "#cb4335", side_total=spd_side)
            for _, r in g.iterrows():
                is_h = r["group"] == "Health"
                node(f"spd:{r['label']}", r["label"], "spd:Health" if is_h else "spd", r["pct_outlays"] / 100 * T,
                     "#bdc3c7" if r["group"] == "Unclassified" else (HEALTH_REDS.get(r["label"], "#cb4335") if is_h else OTHER_FUNCS.get(r["label"], "#7f8c8d")),
                     "not reported by the IMF for this country-year" if r["group"] == "Unclassified" else
                     ("debt interest, split out of general public services" if r["label"] == "Interest on public debt" else ""), spd_side)
            if can_compare and gap < -0.05:
                node("spd:surplus", "Surplus (revenue not spent)", "spd", -gap, "#a9dfbf",
                     "Revenue exceeded spending by this much (saved or used to pay down debt)", spd_side)

        # parents hold (slightly more than) the sum of their children, computed bottom-up so branchvalues="total" always validates
        acc = {}
        for idx in range(len(ids) - 1, -1, -1):
            if ids[idx] in acc:
                values[idx] = acc[ids[idx]] * 1.000001
            acc[parents[idx]] = acc.get(parents[idx], 0.0) + values[idx]
        texts[0], hov[0] = "", ""
        fig4 = go.Figure(go.Treemap(
            ids=ids, labels=labels, parents=parents, values=values, branchvalues="total", text=texts,
            marker=dict(colors=colors_, line=dict(width=1.5, color="white")), customdata=hov, textinfo="label+text",
            hovertemplate="<b>%{label}</b><br>%{customdata}<extra></extra>", sort=False,
        ))
        fig4.update_layout(height=720, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig4, **WIDE)

        covs = []
        if has_rev:
            covs.append(f"revenue: {rg['coverage'].iloc[0].lower()}")
        if has_spd:
            covs.append(f"spending: {g['coverage'].iloc[0].lower()}")
        st.caption(
            f"{int(yr4)}. The revenue box (left) and spending box (right) are drawn to the same scale. When spending is larger, the "
            "difference is shown as dark-purple 'Borrowing / debt' on the revenue side; when revenue is larger, a green 'Surplus' "
            "box appears on the spending side. Debt interest is split out of general public services. "
            f"Level of government ({'; '.join(covs)}). Grey = amounts the IMF doesn't break out.")

        # ---------------- headline numbers ----------------
        mcols = st.columns(4)
        def _m(col, label, pct, signed=False):
            if gdp_m:
                col.metric(label, (("-" if pct < 0 else "+") if signed else "") + _amt(abs(pct)))
            else:
                col.metric(label, f"{pct:+.1f}% of GDP" if signed else f"{pct:.1f}% of GDP")
        if R is not None:
            _m(mcols[0], f"Revenue, {int(yr4)}", R)
        if T is not None and has_spd:
            _m(mcols[1], f"Spending, {int(yr4)}", T)
        if can_compare:
            _m(mcols[2], "Revenue minus spending", -gap, signed=True)
        if debt_pct is not None:
            mcols[3].metric(f"Gross government debt, {int(yr4)}", _amt(debt_pct) if gdp_m else f"{debt_pct:.0f}% of GDP")
        st.caption(
            "Both IMF datasets report each item as a share of GDP, so dollar amounts = that share x GDP"
            + (f" (GDP in {gdp_basis})" if gdp_m else "") + ". After the IMF's latest actual year, GDP is the IMF's projection. "
            "Revenue and spending come from two different IMF datasets and a country can be reported at a different level of "
            "government in each, in which case the 'borrowing' or 'surplus' box is only a rough indication. Neither file has loan "
            "principal or financing detail, so the borrowing box is simply spending minus revenue; gross debt (WEO) is the stock of "
            "debt outstanding, not the yearly borrowing.")


_budget_section()


st.divider()

# =========================================================================== #
# SECTION 4 - the model: funding cut -> fiscal response -> coverage -> lives
# =========================================================================== #
from model_section import render_model_section  # noqa: E402

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
render_model_section(crow["iso3"], country_name, _imf)
