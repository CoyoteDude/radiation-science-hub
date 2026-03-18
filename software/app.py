"""
app.py — Gamma Spectroscopy Lab  v3
Run with: streamlit run app.py
"""
import streamlit as st
from download_ensdf import ensure_ensdf
ensure_ensdf()

st.set_page_config(
    page_title="Gamma Spectroscopy Lab",
    page_icon="☢",
    layout="wide",
    initial_sidebar_state="expanded",
)

from spectroscopy_module import render_spectroscopy
from forensic_tab import render_forensic_tab
from analysis_tabs import (
    render_ensdf_tab,
    render_peak_fitting_tab,
    render_efficiency_tab,
    render_activity_tab,
    render_mda_tab,
    render_shielding_tab,
    render_dose_tab,
)
from spectrum_db import load_db
from library_match_tab import render_library_match_tab
from report_export import render_export_tab

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=Libre+Baskerville&family=JetBrains+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { background-color: #0e0e0c; color: #e8dfc8; }
section[data-testid="stSidebar"] { background-color: #0a0a08; border-right: 1px solid #1a1a16; }
.block-container { padding-top: 1.5rem; }
div[data-testid="stMetricValue"] { color: #d4a843 !important; font-family: 'JetBrains Mono', monospace; }
div[data-testid="stMetricLabel"] { color: #5a5040 !important; font-size: .7rem; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown(
        '<div style="font-family:\'Courier New\',monospace;font-size:.88rem;'
        'font-weight:700;color:#d4a843;letter-spacing:.2em;padding:.5rem 0 1rem">☢ GAMMA LAB</div>',
        unsafe_allow_html=True)

    def _div(text):
        st.markdown(
            f'<div style="font-family:\'Courier New\',monospace;font-size:.55rem;'
            f'color:#2a2818;letter-spacing:.2em;padding:.8rem 0 .2rem">{text}</div>',
            unsafe_allow_html=True)

    _div("── SPECTROSCOPY ──")
    if st.button("📥  Import / Spectra",       key="nav_spec",  use_container_width=True):
        st.session_state["section"] = "spectroscopy"
    if st.button("☣   Forensic Analysis",      key="nav_for",   use_container_width=True):
        st.session_state["section"] = "forensic"

    _div("── QUANTITATIVE ──")
    if st.button("🗃  ENSDF Library",           key="nav_ensdf", use_container_width=True):
        st.session_state["section"] = "ensdf"
    if st.button("🎯  Peak Fitting",            key="nav_peaks", use_container_width=True):
        st.session_state["section"] = "peaks"
    if st.button("📐  Efficiency Cal",          key="nav_eff",   use_container_width=True):
        st.session_state["section"] = "efficiency"
    if st.button("⚡  Activity (Bq/g)",        key="nav_act",   use_container_width=True):
        st.session_state["section"] = "activity"
    if st.button("📡  MDA",                    key="nav_mda",   use_container_width=True):
        st.session_state["section"] = "mda"

    _div("── SAFETY ──")
    if st.button("🛡  Shielding",               key="nav_sh",    use_container_width=True):
        st.session_state["section"] = "shielding"
    if st.button("☢  Dose Rate",               key="nav_dose",  use_container_width=True):
        st.session_state["section"] = "dose"

    if st.button("📚  Library Match",  key="nav_lib",    use_container_width=True):
        st.session_state["section"] = "library_match"
    if st.button("📄  Export PDF",     key="nav_export", use_container_width=True):
        st.session_state["section"] = "export"

    st.markdown("---")
    curve = st.session_state.get("active_eff_curve")
    if curve:
        st.markdown(
            f'<div style="font-family:\'Courier New\',monospace;font-size:.58rem;'
            f'color:#27ae60;background:#0a1a0a;border:1px solid #1a3a1a;'
            f'border-radius:2px;padding:.3rem .6rem">'
            f'✓ Eff: {curve.geometry[:18]}<br>{curve.distance_cm}cm · R²={curve.r2}</div>',
            unsafe_allow_html=True)
    else:
        st.markdown(
            '<div style="font-family:\'Courier New\',monospace;font-size:.58rem;'
            'color:#2a2010;padding:.3rem .6rem">⚬ No efficiency curve</div>',
            unsafe_allow_html=True)

if "section" not in st.session_state:
    st.session_state["section"] = "spectroscopy"

section = st.session_state["section"]
db = load_db()

if   section == "spectroscopy": render_spectroscopy()
elif section == "forensic":     render_forensic_tab()
elif section == "ensdf":        render_ensdf_tab()
elif section == "peaks":        render_peak_fitting_tab(db)
elif section == "efficiency":   render_efficiency_tab(db)
elif section == "activity":     render_activity_tab(db)
elif section == "mda":          render_mda_tab(db)
elif section == "shielding":    render_shielding_tab()
elif section == "dose":         render_dose_tab()
