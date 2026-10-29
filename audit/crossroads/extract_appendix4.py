"""
Extract Appendix 4 (Tables A4.1 and A4.2, pp. 74-78) of the World Bank GRPH 2025 report
"At a Crossroads: Prospects for Government Health Financing Amidst Declining Aid" (Kumar et al., November 2025)
into audit/crossroads/wb_grph_appendix4.csv.

    python audit/crossroads/extract_appendix4.py [path to the PDF]

Columns: country, iso3, income_group, year, population_thousands, gge_pc, phe_pc, offbudget_dah_pc, who_benchmark_pc,
who_gov_gap_pc. Units as in the report: population in thousands; all money in 2024 US$ per capita (report p. 75 and
p. 78 table notes). PHE = central + subnational government health spending + social health insurance, INCLUDING
on-budget DAH (report p. 17, note 4); off-budget DAH from OECD CRS sector codes 120-130 (p. 34 footnote 21, p. 36).
Cross-checks only; nothing here feeds the model.
"""
import re
import sys
from pathlib import Path

import pandas as pd
import pypdf

HERE = Path(__file__).parent
PDF = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent.parent / "datasets" / "WorldBank_GRPH_2025_At_a_Crossroads.pdf"
OUT = HERE / "wb_grph_appendix4.csv"
PAGES = {74: "low_income", 75: "low_income", 76: "lower_middle_income", 77: "lower_middle_income", 78: "lower_middle_income"}
YEARS = {"2018", "2024", "2030"}
NUM = re.compile(r"^-?\d+(\.\d+)?$")
INT = re.compile(r"^-?\d+$")
ISO3 = {
    "Burkina Faso": "BFA", "Burundi": "BDI", "Central African Republic": "CAF", "Chad": "TCD", "Congo, Dem. Rep.": "COD",
    "Ethiopia": "ETH", "Gambia, The": "GMB", "Guinea-Bissau": "GNB", "Liberia": "LBR", "Madagascar": "MDG", "Malawi": "MWI",
    "Mali": "MLI", "Mozambique": "MOZ", "Niger": "NER", "Rwanda": "RWA", "Sierra Leone": "SLE", "Somalia": "SOM",
    "South Sudan": "SSD", "Sudan": "SDN", "Togo": "TGO", "Uganda": "UGA", "Yemen, Rep.": "YEM",
    "Angola": "AGO", "Bangladesh": "BGD", "Benin": "BEN", "Bhutan": "BTN", "Cabo Verde": "CPV", "Cambodia": "KHM",
    "Cameroon": "CMR", "Comoros": "COM", "Congo, Rep.": "COG", "Côte d'Ivoire": "CIV", "Djibouti": "DJI",
    "Egypt, Arab Rep.": "EGY", "Eswatini": "SWZ", "Ghana": "GHA", "Guinea": "GIN", "Haiti": "HTI", "Honduras": "HND",
    "India": "IND", "Jordan": "JOR", "Kenya": "KEN", "Kiribati": "KIR", "Kyrgyz Republic": "KGZ", "Lao PDR": "LAO",
    "Lesotho": "LSO", "Mauritania": "MRT", "Micronesia, Fed. Sts.": "FSM", "Morocco": "MAR", "Myanmar": "MMR",
    "Nepal": "NPL", "Nicaragua": "NIC", "Nigeria": "NGA", "Pakistan": "PAK", "Papua New Guinea": "PNG",
    "Philippines": "PHL", "Samoa": "WSM", "São Tomé and Príncipe": "STP", "Senegal": "SEN", "Solomon Islands": "SLB",
    "Tajikistan": "TJK", "Tanzania": "TZA", "Timor-Leste": "TLS", "Tunisia": "TUN", "Uzbekistan": "UZB", "Vanuatu": "VUT",
    "Viet Nam": "VNM", "Zambia": "ZMB", "Zimbabwe": "ZWE",
}


def parse(pdf: Path) -> pd.DataFrame:
    r = pypdf.PdfReader(str(pdf))
    rows = []
    for page, ig in PAGES.items():
        text = r.pages[page - 1].extract_text() or ""
        # the table starts after the header row and ends at the "Sources:" note
        # pages 74 and 76 carry the table header; pages 75, 77 and 78 continue the table with only a page number
        hdr = text.find("WHO government gap")
        start = hdr + len("WHO government gap") if hdr >= 0 else 0
        end = text.find("Sources:")
        body = text[start: end if end > 0 else None]
        toks = body.replace("\u2019", "'").split()
        while toks and INT.match(toks[0]):          # drop the page number before the first country name
            toks.pop(0)
        name, i = [], 0
        while i < len(toks):
            t = toks[i]
            if t in YEARS and i + 5 < len(toks) and all(NUM.match(toks[i + k]) for k in range(1, 6)):
                pop, gge, phe, dah, who = toks[i + 1: i + 6]
                gap, step = None, 6
                if i + 6 < len(toks) and INT.match(toks[i + 6]):
                    gap, step = toks[i + 6], 7
                rows.append({"country": " ".join(name).strip(), "year": int(t), "population_thousands": float(pop),
                             "gge_pc": float(gge), "phe_pc": float(phe), "offbudget_dah_pc": float(dah),
                             "who_benchmark_pc": float(who), "who_gov_gap_pc": float(gap) if gap is not None else None,
                             "income_group": ig, "page": page})
                i += step
                # the next record may reuse the same country name (no name tokens before its year)
                if i < len(toks) and toks[i] in YEARS:
                    continue
                name = []
            else:
                name.append(t)
                i += 1
    df = pd.DataFrame(rows)
    # a country's 2024 and 2030 rows carry no name tokens when the name is on the first row only; fill forward
    df["country"] = df["country"].replace("", None).ffill()
    df["iso3"] = df["country"].map(ISO3)
    cols = ["country", "iso3", "income_group", "year", "population_thousands", "gge_pc", "phe_pc", "offbudget_dah_pc",
            "who_benchmark_pc", "who_gov_gap_pc", "page"]
    return df[cols].sort_values(["income_group", "country", "year"]).reset_index(drop=True)


if __name__ == "__main__":
    df = parse(PDF)
    missing = df[df["iso3"].isna()]["country"].unique().tolist()
    assert not missing, f"no ISO3 for: {missing}"
    df.to_csv(OUT, index=False)
    print(f"{len(df)} rows, {df.iso3.nunique()} countries, {df.year.nunique()} years -> {OUT}")
    print(df.groupby("income_group").iso3.nunique())
    print("rows with a blank WHO gap:", df[df.who_gov_gap_pc.isna()][["country", "year"]].to_dict("records"))
