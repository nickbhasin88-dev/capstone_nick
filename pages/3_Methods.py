"""
Methods, data and limitations of the funding-cut model, with the full parameter table. Linked from the sidebar; the
cross-check and published-estimate comparisons use the country, scenario and settings chosen on the dashboard.
"""
import io
import re

import pandas as pd
import streamlit as st

import theme as th

th.apply_page("Methods")

import health_model as hm  # noqa: E402  (page config has to come first)
import model_section as ms  # noqa: E402
import scenarios as scn  # noqa: E402
from country_lists import dropdown_countries  # noqa: E402
from model_section import title_case  # noqa: E402

I = ms._inputs()
ctx = st.session_state.get("model_ctx", {})
names = dropdown_countries()
iso3 = ctx.get("iso3") if ctx.get("iso3") in names else "KEN"
country_name = names[iso3]
preset = ctx.get("preset", list(scn.PRESETS)[0])
opts = ctx.get("opts") or scn.default_opts(preset, I["ci"])
fiscal_t = tuple(ctx.get("fiscal_t", scn.DEFAULT_FISCAL))
ptab_json = ctx.get("ptab_json", ms._default_params().to_json(orient="split"))
trend = ctx.get("trend", scn.DEFAULT_MORTALITY_TREND)
ptab = pd.read_json(io.StringIO(ptab_json), orient="split")

st.title("Methods, Data and Limitations")
st.caption("How the funding-cut model on the dashboard turns an aid cut into lost coverage and extra deaths.")

# --------------------------------------------------------------------------- #
# The model, step by step (same text as before, one header per part)
# --------------------------------------------------------------------------- #
th.section_header("account_tree", "How the Model Works", "What happens, step by step, between a cut and a death?",
                  rule=False)
for block in re.split(r"\n\s*\n", ms.METHODS.strip()):
    m = re.match(r"^\*\*(.+?)\*\*\s*(.*)$", block.strip(), flags=re.S)
    if m:
        st.subheader(title_case(re.sub(r"^\d+\.\s*", "", m.group(1)).rstrip(".")))
        if m.group(2).strip():
            st.markdown(ms._esc(m.group(2).strip()))
    else:
        st.markdown(ms._esc(block))

# --------------------------------------------------------------------------- #
# Cross-check and published estimates, for the dashboard's current choices
# --------------------------------------------------------------------------- #
th.section_header("fact_check", "Cross-Checks", "Do 20 years of data and published studies point the same way?")
st.caption(f"{country_name} · {title_case(preset)} · {ms._resp_label(fiscal_t)}"
           + ("" if trend else " · Death Rates Held Constant"))
sk = scn.scenario_key(scn.build_scenario(preset, opts, I["ci"]))
res = ms._run(iso3, sk, fiscal_t, ptab_json, trend) if (iso3 in I["ci"].index and iso3 in set(I["lines"].iso3)) else None
st.subheader("What 20 Years of Data Say")
st.markdown(ms._esc(ms._crosscheck_summary(res, I, ptab, country_name)))
ctl = {"preset": preset, "ptab": ptab, "ptab_json": ptab_json, "fiscal_t": fiscal_t, "trend": trend}
A = ms._all_country_results(sk, ctl)
ms._published_estimates(A[A["gross_loss_usd"] > 0], I, ptab)

# --------------------------------------------------------------------------- #
# Parameters
# --------------------------------------------------------------------------- #
th.section_header("tune", "Model Parameters", "Which numbers drive the model, and where does each one come from?")
params = hm.load_params().reset_index()
st.table(params.rename(columns={c: title_case(c.replace("_", " ")) for c in params.columns}).set_index("Param"))
st.caption("Each parameter is drawn from a triangular distribution (low, central, high); edit them in the dashboard's "
           "model settings to test sensitivity.")
