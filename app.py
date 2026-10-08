"""
Health financing dashboard: navigation only. Run:  streamlit run app.py

The pages live in views/ (not pages/, which Streamlit would auto-load and bypass this navigation) (Dashboard, All Countries, Validation & Benchmarks, Methods); theme.py holds the look.
"""
import streamlit as st

import theme as th

th.setup()

# Streamlit forgets a widget's value when the page that draws it is not shown. Writing these values back on every run
# keeps the model settings when switching pages (country and scenario are shared through sel_iso3 / sel_preset).
PERSIST_PREFIXES = ("m_", "mb_", "c1_", "c2_", "c3b_", "c4_year_")
NOT_PERSISTED = {"m_params", "m_custom_tbl", "mb_custom_tbl"}          # data editors cannot be set this way
for _k in list(st.session_state.keys()):
    if isinstance(_k, str) and _k.startswith(PERSIST_PREFIXES) and _k not in NOT_PERSISTED:
        st.session_state[_k] = st.session_state[_k]

pg = st.navigation([st.Page(path, title=title, icon=icon, default=(i == 0))
                    for i, (path, title, icon) in enumerate(th.PAGES)], position="top")
pg.run()
