"""
library_match_tab.py — Spectral library matching UI for GammaLab
─────────────────────────────────────────────────────────────────
Renders the 📚 Library Match section. Wired into app.py as:

    from library_match_tab import render_library_match_tab
    elif section == "library_match": render_library_match_tab(db)

And added to the sidebar in app.py:
    if st.button("📚  Library Match", key="nav_lib", use_container_width=True):
        st.session_state["section"] = "library_match"
"""

from __future__ import annotations
import json
import streamlit as st
import numpy as np
import pandas as pd
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from spectrum_db       import find_spectrum_peaks
from spectral_library  import (
    load_library, match_spectrum, peaks_from_spectrum,
    all_categories, save_user_entry, list_user_files, delete_user_entry,
    MatchResult, LIBRARY_DIR,
)

BG = "#0e0e0c"


# ══════════════════════════════════════════════════════════════════════════════
#  SHARED STYLE HELPERS  (same palette as the rest of GammaLab)
# ══════════════════════════════════════════════════════════════════════════════

def _slabel(text: str):
    st.markdown(
        f'<div style="font-family:\'Courier New\',monospace;font-size:.68rem;'
        f'color:#d4a843;letter-spacing:.15em;text-transform:uppercase;'
        f'margin:1rem 0 .3rem">{text}</div>',
        unsafe_allow_html=True)


def _ok(text: str):
    st.markdown(
        f'<div style="font-family:\'Courier New\',monospace;font-size:.72rem;'
        f'color:#27ae60;background:#0a1f0e;border:1px solid #1a4a22;'
        f'border-radius:2px;padding:.3rem .7rem;display:inline-block;margin:.3rem 0">'
        f'✓ {text}</div>', unsafe_allow_html=True)


def _warn(text: str):
    st.markdown(
        f'<div style="font-family:\'Courier New\',monospace;font-size:.72rem;'
        f'color:#e87050;background:#1a0a0a;border:1px solid #4a1a1a;'
        f'border-radius:2px;padding:.3rem .7rem;margin:.3rem 0">'
        f'⚠ {text}</div>', unsafe_allow_html=True)


def _row(label: str, value, unit: str = "", color: str = "#e8dfc8"):
    st.markdown(
        f'<div style="font-family:\'Courier New\',monospace;font-size:.72rem;'
        f'background:#0f0f0c;border-left:2px solid #2a2820;'
        f'padding:.25rem .7rem;margin:.15rem 0;display:flex;justify-content:space-between">'
        f'<span style="color:#5a5040">{label}</span>'
        f'<span style="color:{color}">{value} {unit}</span></div>',
        unsafe_allow_html=True)


def _score_bar(score: float, width_px: int = 180) -> str:
    """Return an HTML mini progress bar for a 0–1 score."""
    pct   = int(score * 100)
    color = "#27ae60" if pct >= 80 else "#d4a843" if pct >= 50 else "#c0392b"
    filled = int(width_px * score)
    return (
        f'<span style="display:inline-flex;align-items:center;gap:6px">'
        f'<span style="display:inline-block;width:{width_px}px;height:6px;'
        f'background:#1a1a16;border-radius:3px;overflow:hidden">'
        f'<span style="display:block;width:{filled}px;height:6px;'
        f'background:{color};border-radius:3px"></span></span>'
        f'<span style="font-size:.68rem;color:{color};font-family:monospace">'
        f'{pct}%</span></span>'
    )


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN RENDER
# ══════════════════════════════════════════════════════════════════════════════

def render_library_match_tab(db: dict):
    st.markdown(
        '<div style="font-family:Georgia,serif;font-size:1.6rem;font-weight:700;'
        'color:#f0e8d8">Spectral Library Matching</div>', unsafe_allow_html=True)
    st.caption(
        "Compare detected peaks against reference spectra · "
        "30 built-in materials + user library · composite scoring"
    )

    subtabs = st.tabs([
        "🔍  Match spectrum",
        "📖  Browse library",
        "➕  Add custom entry",
        "🗂  Manage library",
    ])

    with subtabs[0]:
        _render_match_tab(db)
    with subtabs[1]:
        _render_browse_tab()
    with subtabs[2]:
        _render_add_tab()
    with subtabs[3]:
        _render_manage_tab()


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 1 — MATCH SPECTRUM
# ══════════════════════════════════════════════════════════════════════════════

def _render_match_tab(db: dict):
    if not db:
        st.info("No spectra imported. Go to 📥 Import first.")
        return

    # ── Spectrum selector ────────────────────────────────────────────────
    labels = {eid: f"{e['sample_name']}  ·  {e.get('mineral_type','')}  ·  {e['meas_time_s']:,}s"
              for eid, e in db.items()}
    eid = st.selectbox("Spectrum to match", list(db.keys()),
                       format_func=lambda x: labels[x], key="lib_sel_spectrum")
    entry = db[eid]

    c1, c2, c3 = st.columns(3)
    prom   = c1.slider("Peak prominence %", 0.5, 10.0, 2.0, 0.5, key="lib_prom") / 100
    mine   = c2.slider("Min energy (keV)",  10.0, 200.0, 40.0, 5.0, key="lib_mine")
    tol_sc = c3.slider("Tolerance scale ×", 0.5, 3.0, 1.0, 0.1, key="lib_tol",
                        help="Multiply all library tolerances. >1 = looser match (good for poor calibration)")

    # Category filter
    library = load_library()
    cats    = ["All"] + all_categories(library)
    cat_sel = st.multiselect("Category filter", cats, default=["All"], key="lib_cats")
    cat_filter = None if "All" in cat_sel else cat_sel

    top_n   = st.slider("Show top N results", 3, 30, 10, key="lib_topn")
    min_sc  = st.slider("Min score threshold", 0.0, 0.8, 0.10, 0.05, key="lib_minscore")

    if st.button("▶  Run library match", type="primary", key="lib_run"):
        counts   = np.array(entry["counts"])
        energies = np.array(entry["energies"])
        peaks    = find_spectrum_peaks(counts, energies,
                                       prominence_pct=prom, min_energy=mine)
        if not peaks:
            _warn("No peaks detected — lower prominence or min energy threshold.")
            return

        det_peaks = peaks_from_spectrum(counts, energies, peaks)

        with st.spinner(f"Scoring {len(library)} library entries against {len(det_peaks)} peaks…"):
            results = match_spectrum(
                det_peaks,
                library          = library,
                min_score        = min_sc,
                top_n            = top_n,
                tolerance_scale  = tol_sc,
                category_filter  = cat_filter,
            )

        st.session_state["lib_results"]  = results
        st.session_state["lib_det_peaks"]= det_peaks
        st.session_state["lib_entry"]    = entry
        st.session_state["lib_peaks_raw"]= peaks

        _ok(f"Scored {len(library)} entries · {len(results)} above threshold · "
            f"{len(det_peaks)} peaks used")

    # ── Results display ───────────────────────────────────────────────────
    results   = st.session_state.get("lib_results")
    det_peaks = st.session_state.get("lib_det_peaks")
    lib_entry = st.session_state.get("lib_entry")

    if not results:
        return

    _slabel(f"Top {len(results)} matches")
    _render_results_table(results)

    # ── Detail expander for selected result ───────────────────────────────
    result_names = [r.entry_name for r in results]
    sel_name = st.selectbox("Inspect result in detail", result_names, key="lib_detail_sel")
    sel_result = next((r for r in results if r.entry_name == sel_name), None)

    if sel_result and lib_entry:
        _render_detail(sel_result, lib_entry, det_peaks or [])


def _render_results_table(results: list[MatchResult]):
    rows = []
    for r in results:
        bar_html = _score_bar(r.overall_score)
        rows.append({
            "Material":       r.entry_name,
            "Category":       r.category,
            "Score":          r.overall_score,
            "Lines matched":  f"{r.n_lines_matched}/{r.n_lines_total}",
            "Peaks explained":f"{r.n_peaks_explained}/{r.n_peaks_spectrum}",
            "Verdict":        r.verdict,
        })

    df = pd.DataFrame(rows)
    # Colour the score column with gradient
    def colour_score(v):
        if v >= 0.80: return "background-color:#0a2a0a;color:#27ae60"
        if v >= 0.55: return "background-color:#1a1a08;color:#d4a843"
        if v >= 0.30: return "background-color:#1a0f08;color:#c0392b"
        return "color:#3a3020"

    styled = (df.style
              .applymap(colour_score, subset=["Score"])
              .format({"Score": "{:.3f}"})
              .hide(axis="index"))
    st.dataframe(df.drop(columns=["Verdict"]), use_container_width=True, hide_index=True)

    # Show verdict for top result prominently
    if results:
        top = results[0]
        colour = "#27ae60" if top.overall_score >= 0.80 else "#d4a843" if top.overall_score >= 0.55 else "#e87050"
        st.markdown(
            f'<div style="font-family:\'Courier New\',monospace;font-size:.8rem;'
            f'color:{colour};background:#0c0c0a;border:1px solid #2a2820;'
            f'border-radius:2px;padding:.5rem 1rem;margin:.5rem 0">'
            f'Best match: <strong>{top.entry_name}</strong> — {top.verdict}</div>',
            unsafe_allow_html=True)


def _render_detail(result: MatchResult, entry: dict, det_peaks: list[dict]):
    st.markdown("---")
    _slabel(f"Detail — {result.entry_name}")

    # Score breakdown
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Overall",   f"{result.overall_score:.3f}")
    c2.metric("Presence",  f"{result.presence_score:.3f}")
    c3.metric("Energy",    f"{result.energy_score:.3f}")
    c4.metric("Intensity", f"{result.intensity_score:.3f}")

    st.caption(result.description)

    # Line-by-line match table
    _slabel("Line match table")
    rows = []
    for lm in result.line_matches:
        rows.append({
            "Isotope":        lm.isotope,
            "Library (keV)":  lm.lib_keV,
            "Rel. intensity": lm.lib_rel_int,
            "Detected (keV)": f"{lm.det_keV:.1f}" if lm.matched else "—",
            "Δ (keV)":        f"{lm.delta_keV:+.1f}" if lm.matched else "—",
            "Det. counts":    f"{lm.det_counts:,.0f}" if lm.matched else "—",
            "Match":          "✓" if lm.matched else "✗",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Overlay plot
    _render_overlay_plot(result, entry, det_peaks)


def _render_overlay_plot(result: MatchResult, entry: dict, det_peaks: list[dict]):
    """Plot spectrum with library lines overlaid."""
    _slabel("Spectrum overlay")
    counts   = np.array(entry["counts"])
    energies = np.array(entry["energies"])
    lt       = max(entry["meas_time_s"], 1)
    cps      = counts / lt

    fig, ax = plt.subplots(figsize=(10, 3.5))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor("#0a0a08")

    # Spectrum
    ax.fill_between(energies, cps, alpha=0.25, color="#4a6a8a", step="mid")
    ax.plot(energies, cps, color="#6b7a90", lw=0.5, alpha=0.8)

    # Detected peaks (grey ticks)
    for pk in det_peaks:
        ax.axvline(pk["energy_keV"], color="#3a3830", lw=0.8, alpha=0.6, ls=":")

    # Library lines
    for lm in result.line_matches:
        if lm.matched:
            color = "#27ae60"
            lw    = 1.2
            ls    = "-"
        else:
            color = "#c0392b"
            lw    = 0.8
            ls    = "--"
        ax.axvline(lm.lib_keV, color=color, lw=lw, ls=ls, alpha=0.8)
        # Label
        y_top = cps.max() * 0.95
        ax.text(lm.lib_keV + 2, y_top, lm.isotope,
                fontsize=5.5, color=color, rotation=90, va="top",
                fontfamily="monospace", alpha=0.85)

    # Legend
    matched_patch   = mpatches.Patch(color="#27ae60", label="Library line matched")
    unmatched_patch = mpatches.Patch(color="#c0392b", label="Library line missing")
    ax.legend(handles=[matched_patch, unmatched_patch],
              fontsize=7, facecolor="#1a1a16", labelcolor="#e8dfc8",
              loc="upper right")

    ax.set_yscale("log")
    ax.set_xlabel("Energy (keV)", color="#6b6350", fontsize=8)
    ax.set_ylabel("CPS",          color="#6b6350", fontsize=8)
    ax.set_title(f"{entry['sample_name']}  ·  {result.entry_name}  ·  score={result.overall_score:.3f}",
                 color="#d4a843", fontsize=8)
    ax.tick_params(colors="#6b6350", labelsize=7)
    for sp in ax.spines.values():
        sp.set_color("#2a2820")
    ax.set_xlim(0, energies.max())

    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close()


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 2 — BROWSE LIBRARY
# ══════════════════════════════════════════════════════════════════════════════

def _render_browse_tab():
    library = load_library()
    cats    = all_categories(library)

    cat_sel = st.selectbox("Category", ["All"] + cats, key="browse_cat")
    search  = st.text_input("Search name / tag", placeholder="e.g. uranium, medical, Cs-137",
                             key="browse_search")

    filtered = library
    if cat_sel != "All":
        filtered = [e for e in filtered if e.category == cat_sel]
    if search.strip():
        q = search.strip().lower()
        filtered = [e for e in filtered
                    if q in e.name.lower() or any(q in t.lower() for t in e.tags)
                    or q in e.description.lower()]

    st.caption(f"{len(filtered)} entries")

    for ent in filtered:
        with st.expander(f"**{ent.name}**  ·  {ent.category}  ·  {len(ent.lines)} lines"):
            st.caption(ent.description)
            if ent.tags:
                tag_html = " ".join(
                    f'<span style="font-family:monospace;font-size:.65rem;'
                    f'background:#1a1a16;border:1px solid #2a2820;'
                    f'border-radius:2px;padding:.1rem .4rem;color:#6b6350">{t}</span>'
                    for t in ent.tags
                )
                st.markdown(tag_html, unsafe_allow_html=True)

            rows = [{"Isotope": l.isotope,
                     "Energy (keV)": l.energy_keV,
                     "Rel. intensity": l.rel_intensity,
                     "Tolerance (keV)": l.tolerance_keV}
                    for l in ent.lines]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            if ent.source_file != "built-in":
                st.caption(f"Source: {ent.source_file}")


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 3 — ADD CUSTOM ENTRY
# ══════════════════════════════════════════════════════════════════════════════

def _render_add_tab():
    _slabel("Create a new reference entry")
    st.caption(
        f"Saved as JSON to `{LIBRARY_DIR}`. "
        "These appear alongside the built-in library immediately on next match run."
    )

    c1, c2 = st.columns(2)
    name     = c1.text_input("Material name", placeholder="e.g. My granite sample", key="add_name")
    category = c1.selectbox("Category",
                             ["Natural", "Industrial", "Medical", "Calibration",
                              "Anthropogenic", "Fissile", "Geology", "Other"],
                             key="add_cat")
    desc     = c2.text_area("Description", height=80, key="add_desc",
                             placeholder="Brief description of the material and its gamma signature")
    tags_str = c2.text_input("Tags (comma-separated)", key="add_tags",
                              placeholder="e.g. NORM, granite, K-40")

    _slabel("Gamma lines")
    st.caption("Enter one line per row. Rel. intensity: strongest line = 100.")

    if "add_lines" not in st.session_state:
        st.session_state["add_lines"] = []

    with st.form("add_line_form", clear_on_submit=True):
        lc1, lc2, lc3, lc4 = st.columns([2, 2, 2, 2])
        l_energy  = lc1.number_input("Energy (keV)", min_value=10.0, max_value=4000.0,
                                      value=661.7, step=0.1, key="al_energy")
        l_rel     = lc2.number_input("Rel. intensity", min_value=0.1, max_value=100.0,
                                      value=100.0, step=1.0, key="al_rel")
        l_isotope = lc3.text_input("Isotope", placeholder="Cs-137", key="al_iso")
        l_tol     = lc4.number_input("Tolerance (keV)", min_value=1.0, max_value=20.0,
                                      value=4.0, step=0.5, key="al_tol")
        add_line_btn = st.form_submit_button("Add line")

    if add_line_btn:
        st.session_state["add_lines"].append({
            "energy_keV":    round(l_energy, 2),
            "rel_intensity": round(l_rel, 1),
            "isotope":       l_isotope,
            "tolerance_keV": round(l_tol, 1),
        })

    lines = st.session_state.get("add_lines", [])
    if lines:
        st.dataframe(pd.DataFrame(lines), use_container_width=True, hide_index=True)
        if st.button("🗑  Clear all lines", key="add_clear_lines"):
            st.session_state["add_lines"] = []

    if st.button("💾  Save entry to library", type="primary", key="add_save",
                 disabled=(not name or not lines)):
        entry_dict = {
            "name":        name,
            "category":    category,
            "description": desc,
            "tags":        [t.strip() for t in tags_str.split(",") if t.strip()],
            "lines":       lines,
        }
        safe_name = "".join(c if c.isalnum() or c in "-_ " else "_" for c in name)
        filename  = f"{safe_name.replace(' ','_')}.json"
        save_user_entry(entry_dict, filename)
        st.session_state["add_lines"] = []
        _ok(f"Saved '{name}' → {filename}")


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 4 — MANAGE LIBRARY
# ══════════════════════════════════════════════════════════════════════════════

def _render_manage_tab():
    _slabel("User library files")
    user_files = list_user_files()

    if not user_files:
        st.info(f"No user entries yet. Add one in the ➕ tab above.\n\n"
                f"Library directory: `{LIBRARY_DIR}`")
        return

    st.caption(f"{len(user_files)} user file(s)  ·  {LIBRARY_DIR}")

    for fname in user_files:
        path = LIBRARY_DIR / fname
        try:
            data = json.loads(path.read_text())
            entries = data if isinstance(data, list) else [data]
            label = ", ".join(e.get("name","?") for e in entries[:3])
        except Exception:
            label = "⚠ malformed JSON"

        c1, c2 = st.columns([5, 1])
        c1.markdown(
            f'<div style="font-family:monospace;font-size:.75rem;color:#d4a843">'
            f'{fname}</div>'
            f'<div style="font-size:.7rem;color:#5a5040">{label}</div>',
            unsafe_allow_html=True)
        if c2.button("Delete", key=f"del_{fname}"):
            delete_user_entry(fname)
            st.success(f"Deleted {fname}")

    st.markdown("---")
    _slabel("Import JSON file")
    uploaded = st.file_uploader("Upload a library JSON file", type="json",
                                 key="lib_upload")
    if uploaded:
        try:
            data = json.loads(uploaded.read())
            fname = uploaded.name
            path  = LIBRARY_DIR / fname
            path.write_text(json.dumps(data, indent=2))
            _ok(f"Imported {fname}")
        except Exception as e:
            _warn(f"Failed to parse: {e}")

    st.markdown("---")
    _slabel("Export template")
    st.caption("Download a template JSON to fill in for your own material.")
    template = {
        "name":        "My material",
        "category":    "Natural",
        "description": "Brief description",
        "tags":        ["example"],
        "lines": [
            {"energy_keV": 661.7, "rel_intensity": 100, "isotope": "Cs-137", "tolerance_keV": 4},
            {"energy_keV": 1460.8,"rel_intensity":  60, "isotope": "K-40",   "tolerance_keV": 5},
        ],
    }
    st.download_button(
        "⬇  Download template",
        data     = json.dumps(template, indent=2),
        file_name= "gammalab_library_template.json",
        mime     = "application/json",
        key      = "lib_template_dl",
    )
