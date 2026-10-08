"""
All Countries: who is most exposed under a donor scenario (pills, map, scatter, top-15 chart). The scenario is shared
with the other pages; the government response, model parameters and death-rate setting follow the Dashboard.
"""
import io

import pandas as pd
import streamlit as st

import model_section as ms
import scenarios as scn
import theme as th
from country_lists import ALLOWED_COUNTRIES
from model_section import title_case
from scenarios import PRESETS

I = ms._inputs()
ctx = st.session_state.get("model_ctx", {})

st.title("All Countries")
c1, _ = st.columns([1.3, 2])
with c1:
    preset = th.shared_select("Donor Scenario", list(PRESETS), "ac_preset", "sel_preset", list(PRESETS)[0],
                              format_func=title_case,
                              help=ms._esc(PRESETS[st.session_state.get("sel_preset", list(PRESETS)[0])]))

fiscal_t = tuple(ctx.get("fiscal_t", scn.DEFAULT_FISCAL))
ptab_json = ctx.get("ptab_json", ms._default_params().to_json(orient="split"))
trend = ctx.get("trend", scn.DEFAULT_MORTALITY_TREND)
opts = ctx["opts"] if ctx.get("preset") == preset and ctx.get("opts") else scn.default_opts(preset, I["ci"])
ptab = pd.read_json(io.StringIO(ptab_json), orient="split")
sk = scn.scenario_key(scn.build_scenario(preset, opts, I["ci"]))
ctl = {"preset": preset, "ptab": ptab, "ptab_json": ptab_json, "fiscal_t": fiscal_t, "trend": trend}
ms.cross_country(sk, ctl, st.session_state.get("sel_iso3", "KEN"), ALLOWED_COUNTRIES)
