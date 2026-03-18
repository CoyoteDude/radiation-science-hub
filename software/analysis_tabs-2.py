"""
analysis_tabs.py  —  UI tabs for the new analysis modules
──────────────────────────────────────────────────────────
Renders six new tabs inside the spectroscopy app:

  • 📐 Efficiency Cal    — build & manage detector efficiency curves
  • 🎯 Peak Fitting      — Gaussian fits for precise areas & FWHM
  • ⚡ Activity          — convert peak areas to Bq / Bq·g⁻¹
  • 🛡 Shielding         — attenuation through slab shields
  • 📡 MDA              — minimum detectable activity
  • ☢ Dose Rate         — ambient dose equivalent H*(10)
  • 🗃 ENSDF Library     — full gamma line database management
"""

from __future__ import annotations
import streamlit as st
import numpy as np
import json
from pathlib import Path
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ── Local imports ──────────────────────────────────────────────────────────────
from spectrum_db     import find_spectrum_peaks
from peak_fitting    import fit_all_peaks, fit_resolution_curve, predict_fwhm
from efficiency_cal  import (
    build_efficiency_curve, calibration_point_from_measurement,
    CalibrationPoint, EfficiencyCurve,
    save_curve, load_curve, list_saved_curves, CAL_SOURCES,
    distance_scale_efficiency,
)
from activity_calculator import (
    calculate_all_activities, bq_to_uci, bq_to_dpm, ActivityResult,
)
from physics_tools import (
    calculate_mda, calculate_mda_spectrum, calculate_shielding,
    thickness_for_transmission, available_materials,
    estimate_dose_rate, dose_at_distances,
)
from ensdf_parser import (
    get_gamma_db, database_source, isotope_count,
    search_by_energy, rebuild_cache, clear_cache,
    ENSDF_DIR, CACHE_FILE,
)

BG = "#0e0e0c"


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _slabel(text):
    st.markdown(
        f'<div style="font-family:\'Courier New\',monospace;font-size:.68rem;'
        f'color:#d4a843;letter-spacing:.15em;text-transform:uppercase;'
        f'margin:1rem 0 .3rem">{text}</div>',
        unsafe_allow_html=True)


def _ok(text):
    st.markdown(
        f'<div style="font-family:\'Courier New\',monospace;font-size:.72rem;'
        f'color:#27ae60;background:#0a1f0e;border:1px solid #1a4a22;'
        f'border-radius:2px;padding:.3rem .7rem;display:inline-block;margin:.3rem 0">'
        f'✓ {text}</div>', unsafe_allow_html=True)


def _warn(text):
    st.markdown(
        f'<div style="font-family:\'Courier New\',monospace;font-size:.72rem;'
        f'color:#e87050;background:#1a0a0a;border:1px solid #4a1a1a;'
        f'border-radius:2px;padding:.3rem .7rem;margin:.3rem 0">'
        f'⚠ {text}</div>', unsafe_allow_html=True)


def _row(label, value, unit="", color="#e8dfc8"):
    st.markdown(
        f'<div style="font-family:\'Courier New\',monospace;font-size:.72rem;'
        f'background:#0f0f0c;border-left:2px solid #2a2820;'
        f'padding:.25rem .7rem;margin:.15rem 0;display:flex;justify-content:space-between">'
        f'<span style="color:#5a5040">{label}</span>'
        f'<span style="color:{color}">{value} {unit}</span></div>',
        unsafe_allow_html=True)


def _get_entry_and_peaks(db, key):
    """Select a spectrum and run find_spectrum_peaks. Returns (entry, peaks) or (None,[])."""
    if not db:
        st.info("No spectra imported. Go to 📥 Import first.")
        return None, []

    labels = {eid: f"{e['sample_name']}  ·  {e.get('mineral_type','')}  ·  {e['meas_time_s']:,}s"
              for eid, e in db.items()}
    default = 0
    if "sel_id" in st.session_state and st.session_state["sel_id"] in db:
        default = list(db.keys()).index(st.session_state["sel_id"])

    eid = st.selectbox("Spectrum", list(db.keys()),
                        format_func=lambda x: labels[x],
                        index=default, key=f"sel_{key}")
    if not eid:
        return None, []
    entry = db[eid]
    prom  = st.slider("Peak prominence %", 0.5, 10.0, 2.0, 0.5, key=f"prom_{key}") / 100
    mine  = st.slider("Min energy (keV)",  10.0, 100.0, 40.0, 5.0, key=f"mine_{key}")
    peaks = find_spectrum_peaks(entry["counts"], entry["energies"],
                                 prominence_pct=prom, min_energy=mine)
    return entry, peaks


# ══════════════════════════════════════════════════════════════════════════════
#  TAB: ENSDF LIBRARY
# ══════════════════════════════════════════════════════════════════════════════

def render_ensdf_tab():
    st.markdown(
        '<div style="font-family:Georgia,serif;font-size:1.6rem;font-weight:700;'
        'color:#f0e8d8">ENSDF Gamma Library</div>', unsafe_allow_html=True)

    source = database_source()
    n      = isotope_count()
    _ok(f"{n:,} isotopes loaded  ·  {source}")

    st.markdown("""
    <div style="font-family:'Libre Baskerville',serif;font-size:.82rem;color:#6a6050;
    background:#0c0c0a;border:1px solid #1a1a16;border-radius:2px;padding:.8rem 1rem;margin:.5rem 0">
    <strong style="color:#d4a843">To load the complete ~3,000-isotope ENSDF database:</strong><br><br>
    1. Go to <code>https://www.nndc.bnl.gov/ensdf/ensdf/dl_ensdf.jsp</code><br>
    2. Select <em>All ENSDF data → ENSDF database (ASCII)</em> and download the zip<br>
    3. Unzip it — you get files named <code>A=001.ens, A=002.ens, …</code><br>
    4. Place all <code>.ens</code> files in:
       <code style="color:#d4a843">~/Documents/GammaLab/ensdf/</code><br>
    5. Click <strong>Rebuild cache</strong> below — the app parses and caches everything instantly
    </div>""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    ensdf_path = ENSDF_DIR
    ens_count  = len(list(ensdf_path.glob("*.ens"))) if ensdf_path.exists() else 0
    c1.metric("ENSDF files found", ens_count)
    c2.metric("Isotopes in cache", f"{n:,}")
    c3.metric("Cache file", f"{CACHE_FILE.stat().st_size//1024:,} KB"
              if CACHE_FILE.exists() else "None")

    col1, col2 = st.columns(2)
    if col1.button("🔄  Rebuild cache from ENSDF files", key="ens_rebuild"):
        with st.spinner("Parsing ENSDF files…"):
            n2, src = rebuild_cache()
        _ok(f"Rebuilt — {n2:,} isotopes from {src}")
    if col2.button("🗑  Clear cache (revert to built-in)", key="ens_clear"):
        clear_cache()
        _ok("Cache cleared — restart the app to reload the built-in library")

    _slabel("Energy search — find all isotopes with a line near a given energy")
    c1, c2 = st.columns([2, 1])
    search_kev = c1.number_input("Energy to search (keV)", min_value=1.0, max_value=4000.0,
                                  value=661.0, step=0.5, key="ens_search_kev")
    search_tol = c2.number_input("Tolerance (keV)", min_value=0.5, max_value=30.0,
                                  value=5.0, step=0.5, key="ens_search_tol")

    if st.button("Search library", key="ens_search_btn"):
        results = search_by_energy(search_kev, search_tol, min_intensity=0.5)
        if not results:
            _warn(f"No isotopes with a line within {search_tol} keV of {search_kev} keV")
        else:
            st.caption(f"{len(results)} matches")
            import pandas as pd
            df = pd.DataFrame([{
                "Isotope":    r["symbol"],
                "Library keV": r["lib_keV"],
                "Intensity %": r["intensity"],
                "Δ keV":       r["delta"],
                "Note":        r["note"],
            } for r in results])
            st.dataframe(df, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
#  TAB: PEAK FITTING
# ══════════════════════════════════════════════════════════════════════════════

def render_peak_fitting_tab(db: dict):
    st.markdown(
        '<div style="font-family:Georgia,serif;font-size:1.6rem;font-weight:700;'
        'color:#f0e8d8">Peak Fitting</div>', unsafe_allow_html=True)
    st.caption("Gaussian + linear background fit for precise centroids, areas, and FWHM")

    entry, peaks = _get_entry_and_peaks(db, "fit")
    if entry is None or not peaks:
        if entry: st.info("No peaks detected — lower the prominence threshold.")
        return

    counts   = np.array(entry["counts"])
    energies = np.array(entry["energies"])
    lt       = entry["meas_time_s"]

    win = st.slider("Fit window (±channels)", 5, 40, 20, 5, key="fit_win")

    if st.button("▶  Fit all peaks", type="primary", key="fit_run"):
        with st.spinner(f"Fitting {len(peaks)} peaks…"):
            summary = fit_all_peaks(counts, energies, peaks, window_channels=win)
        st.session_state["fit_summary"] = summary
        _ok(f"Fitted {summary.n_peaks_fitted}/{summary.n_peaks_attempted} peaks  ·  "
            f"mean χ² = {summary.mean_chi2}  ·  mean resolution = {summary.mean_resolution_pct}%")

    summary = st.session_state.get("fit_summary")
    if not summary:
        return

    # Resolution curve
    popt, rinfo = fit_resolution_curve(summary.fitted_peaks)

    c1, c2 = st.columns([2, 1])
    with c2:
        _slabel("Resolution curve")
        if popt is not None:
            _row("Model", rinfo["model"])
            _row("a (offset)",  f"{rinfo['a']:.4f}", "keV")
            _row("b (slope)",   f"{rinfo['b']:.4f}", "keV/√keV")
            _row("R²",          f"{rinfo['r2']:.4f}")
            _row("Points used", str(rinfo["n_points"]))
        else:
            _warn(rinfo.get("error","Fit failed"))

    with c1:
        # Plot spectrum with fitted Gaussians overlaid
        fig, ax = plt.subplots(figsize=(9, 3.5))
        fig.patch.set_facecolor(BG); ax.set_facecolor("#0a0a08")
        cps = counts / max(lt, 1)
        ax.plot(energies, cps, color="#6b6350", lw=0.5, alpha=0.7, label="Raw")

        for fp in summary.fitted_peaks:
            if fp.fit_ok and fp.channels_fit:
                ch_arr  = np.array(fp.channels_fit)
                en_arr  = np.interp(ch_arr, np.arange(len(energies)), energies)
                fit_cps = np.array(fp.counts_fitted) / max(lt, 1)
                ax.plot(en_arr, fit_cps, color="#27ae60", lw=1.0, alpha=0.8)
                ax.axvline(fp.energy_keV, color="#d4a843", lw=0.6, alpha=0.5)

        if popt is not None:
            e_curve = np.linspace(50, energies.max(), 200)
            fwhm_curve = np.array([predict_fwhm(e, popt) for e in e_curve])
            ax2 = ax.twinx()
            ax2.plot(e_curve, fwhm_curve, color="#7eb8d4", lw=1.0,
                     linestyle="--", label="FWHM(E)", alpha=0.7)
            ax2.set_ylabel("FWHM (keV)", color="#7eb8d4", fontsize=7)
            ax2.tick_params(colors="#7eb8d4", labelsize=7)

        ax.set_yscale("log")
        ax.set_xlabel("Energy (keV)", color="#6b6350", fontsize=8)
        ax.set_ylabel("CPS",          color="#6b6350", fontsize=8)
        ax.set_title(f"{entry['sample_name']} — Gaussian fits", color="#d4a843", fontsize=8)
        ax.tick_params(colors="#6b6350", labelsize=7)
        for sp in ax.spines.values(): sp.set_color("#2a2820")
        ax.set_xlim(0, energies.max())
        fig.tight_layout()
        st.pyplot(fig, use_container_width=True); plt.close()

    # Fit results table
    _slabel(f"Fitted peaks ({summary.n_peaks_fitted} ok, {summary.n_peaks_failed} failed)")
    import pandas as pd
    rows = []
    for fp in summary.fitted_peaks:
        rows.append({
            "Energy rough (keV)": fp.energy_keV_rough,
            "Energy fitted (keV)": fp.energy_keV if fp.fit_ok else "—",
            "Net area (cts)":  round(fp.area_net, 0)  if fp.fit_ok else "—",
            "Area unc":        f"±{round(fp.area_uncertainty,1)}" if fp.fit_ok else "—",
            "FWHM (keV)":      fp.fwhm_keV      if fp.fit_ok else "—",
            "Resolution %":    fp.resolution_pct if fp.fit_ok else "—",
            "χ²":              fp.chi2_reduced   if fp.fit_ok else "—",
            "Status":          "✓" if fp.fit_ok else f"✗ {fp.fit_message[:30]}",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
#  TAB: EFFICIENCY CALIBRATION
# ══════════════════════════════════════════════════════════════════════════════

def render_efficiency_tab(db: dict):
    st.markdown(
        '<div style="font-family:Georgia,serif;font-size:1.6rem;font-weight:700;'
        'color:#f0e8d8">Efficiency Calibration</div>', unsafe_allow_html=True)

    subtab_new, subtab_manage = st.tabs(["➕  New Calibration", "📂  Saved Curves"])

    with subtab_new:
        st.caption("Build a full-energy peak efficiency curve from calibration source measurements")

        c1, c2 = st.columns(2)
        cal_name = c1.text_input("Calibration name", placeholder="Lab bench 10cm 2024-03",
                                  key="eff_cal_name")
        geometry = c1.selectbox("Geometry", ["Point source", "Marinelli beaker",
                                              "Petri dish", "Soil container"],
                                 key="eff_geo")
        distance = c2.number_input("Source–detector distance (cm)", value=10.0, step=0.5,
                                    key="eff_dist")
        poly_deg = c2.slider("Polynomial degree", 1, 5, 4, key="eff_poly")

        _slabel("Add calibration points")
        st.caption("Enter one row per calibration source measurement. "
                   "Activity is auto-decay-corrected to measurement date.")

        # Multi-row input
        if "cal_points_raw" not in st.session_state:
            st.session_state["cal_points_raw"] = []

        with st.form("add_cal_point", clear_on_submit=True):
            fc1, fc2, fc3 = st.columns(3)
            src_sym  = fc1.selectbox("Source",        list(CAL_SOURCES.keys()), key="cp_src")
            act_bq   = fc2.number_input("Activity at ref date (Bq)", min_value=0.0,
                                         value=37000.0, step=100.0, key="cp_act")
            ref_date = fc3.text_input("Reference date (YYYY-MM-DD)",
                                       value="2020-01-01", key="cp_ref")
            fd1, fd2, fd3 = st.columns(3)
            meas_date= fd1.text_input("Measurement date", value=datetime.now().strftime("%Y-%m-%d"),
                                       key="cp_mdate")
            net_cts  = fd2.number_input("Net counts (peak area)", min_value=0.0,
                                         value=10000.0, step=10.0, key="cp_cts")
            lt_s     = fd3.number_input("Live time (s)", min_value=1.0,
                                         value=3600.0, step=60.0, key="cp_lt")
            # Show available lines for this source
            lines_for_src = CAL_SOURCES.get(src_sym, [])
            line_choices  = [f"{kev:.2f} keV  (yield={y:.4f})"
                              for kev, y in lines_for_src]
            chosen_line = st.selectbox("Gamma line to use", line_choices, key="cp_line") if line_choices else None
            submitted = st.form_submit_button("Add point")

        if submitted and chosen_line:
            kev_chosen = float(chosen_line.split(" keV")[0])
            pt = calibration_point_from_measurement(
                source_symbol       = src_sym,
                source_activity_bq  = act_bq,
                reference_date      = ref_date,
                measurement_date    = meas_date,
                net_counts          = net_cts,
                live_time_s         = lt_s,
                gamma_energy_kev    = kev_chosen,
            )
            if pt:
                st.session_state["cal_points_raw"].append(pt)
                _ok(f"Added {src_sym} @ {kev_chosen} keV — ε = {pt.efficiency:.4e}")
            else:
                _warn(f"Could not compute efficiency for {src_sym} @ {kev_chosen} keV")

        pts = st.session_state.get("cal_points_raw", [])
        if pts:
            _slabel(f"Calibration points ({len(pts)})")
            import pandas as pd
            df = pd.DataFrame([{
                "Source":       p.source,
                "Energy (keV)": p.energy_keV,
                "Efficiency":   f"{p.efficiency:.4e}",
                "Unc":          f"±{p.uncertainty:.2e}",
                "Activity (Bq)":round(p.activity_bq, 1),
                "Net cts":      round(p.net_counts, 0),
            } for p in pts])
            st.dataframe(df, use_container_width=True, hide_index=True)

        if len(pts) >= 2:
            if st.button("📈  Fit efficiency curve", type="primary", key="eff_fit"):
                curve, info = build_efficiency_curve(pts, poly_deg, geometry, distance)
                if "error" in info:
                    _warn(info["error"])
                else:
                    st.session_state["active_eff_curve"] = curve
                    if cal_name:
                        path = save_curve(curve, cal_name)
                        _ok(f"Saved '{cal_name}'  ·  R² = {info['r2']:.4f}  ·  "
                            f"{info['n_points']} points")
                    _draw_efficiency_curve(curve, info)

    with subtab_manage:
        saved = list_saved_curves()
        if not saved:
            st.info("No saved calibration curves yet.")
        else:
            sel = st.selectbox("Load curve", saved, key="eff_load_sel")
            if sel:
                curve = load_curve(sel)
                if curve:
                    st.session_state["active_eff_curve"] = curve
                    _ok(f"Loaded '{sel}'  ·  {curve.n_points} points  ·  "
                        f"R² = {curve.r2}  ·  {curve.geometry}  ·  {curve.distance_cm} cm")
                    _draw_efficiency_curve(curve, {})

                    # Distance scaling
                    _slabel("Scale to new distance")
                    new_dist = st.number_input("New distance (cm)", value=curve.distance_cm,
                                               step=0.5, key="eff_newdist")
                    if st.button("Scale", key="eff_scale"):
                        scaled = distance_scale_efficiency(curve, new_dist)
                        new_name = f"{sel}_scaled_{new_dist:.0f}cm"
                        save_curve(scaled, new_name)
                        st.session_state["active_eff_curve"] = scaled
                        _ok(f"Scaled to {new_dist} cm, saved as '{new_name}'")


def _draw_efficiency_curve(curve: EfficiencyCurve, info: dict):
    """Plot the efficiency curve with data points."""
    if curve.poly_coeffs is None:
        return
    e_range = curve.energy_range
    e_plot  = np.linspace(max(e_range[0], 30), min(e_range[1], 3000), 300)
    eff_plot= np.array([curve.efficiency_at(e) or 0 for e in e_plot])
    valid   = eff_plot > 0

    fig, ax = plt.subplots(figsize=(8, 3.5))
    fig.patch.set_facecolor(BG); ax.set_facecolor("#0a0a08")

    if valid.any():
        ax.plot(e_plot[valid], eff_plot[valid], color="#d4a843", lw=1.5, label="Fitted curve")

    for p in curve.points:
        ax.errorbar(p.energy_keV, p.efficiency,
                    yerr=p.uncertainty if p.uncertainty > 0 else None,
                    fmt="o", color="#27ae60", ms=5, ecolor="#27ae60",
                    capsize=3, elinewidth=0.8, label=p.source)

    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Energy (keV)", color="#6b6350", fontsize=8)
    ax.set_ylabel("Efficiency ε(E)", color="#6b6350", fontsize=8)
    ax.set_title(f"{curve.geometry} — {curve.distance_cm} cm — R²={curve.r2}",
                  color="#d4a843", fontsize=8)
    ax.tick_params(colors="#6b6350", labelsize=7)
    for sp in ax.spines.values(): sp.set_color("#2a2820")
    # Deduplicate legend
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(),
               fontsize=7, facecolor="#1a1a16", labelcolor="#d4a843")
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True); plt.close()


# ══════════════════════════════════════════════════════════════════════════════
#  TAB: ACTIVITY
# ══════════════════════════════════════════════════════════════════════════════

def render_activity_tab(db: dict):
    st.markdown(
        '<div style="font-family:Georgia,serif;font-size:1.6rem;font-weight:700;'
        'color:#f0e8d8">Activity Calculator</div>', unsafe_allow_html=True)

    curve: EfficiencyCurve | None = st.session_state.get("active_eff_curve")
    if curve is None:
        _warn("No efficiency curve loaded. Go to 📐 Efficiency Cal first.")
        saved = list_saved_curves()
        if saved:
            sel = st.selectbox("Or load one now:", ["—"] + saved, key="act_quickload")
            if sel != "—":
                st.session_state["active_eff_curve"] = load_curve(sel)
                curve = st.session_state["active_eff_curve"]
        if curve is None:
            return

    _ok(f"Efficiency curve: {curve.geometry}  ·  {curve.distance_cm} cm  ·  "
        f"R²={curve.r2}  ·  {curve.n_points} points")

    entry, peaks = _get_entry_and_peaks(db, "act")
    if entry is None or not peaks:
        if entry: st.info("No peaks detected.")
        return

    c1, c2 = st.columns(2)
    mass_g    = c1.number_input("Sample mass (g)  [0 = not specified]",
                                  min_value=0.0, value=0.0, step=0.1, key="act_mass")
    fit_win   = c2.slider("Gaussian fit window (±ch)", 5, 40, 20, key="act_fitwin")

    if st.button("▶  Calculate activities", type="primary", key="act_run"):
        counts   = np.array(entry["counts"])
        energies = np.array(entry["energies"])
        lt       = entry["meas_time_s"]

        with st.spinner("Fitting peaks…"):
            summary  = fit_all_peaks(counts, energies, peaks, window_channels=fit_win)
        with st.spinner("Calculating activities…"):
            matches  = st.session_state.get("matches_cache", [])
            if not matches:
                _warn("Run the Identify tab first to get isotope matches.")
                return
            fp_map = {}
            for fp in summary.fitted_peaks:
                if fp.fit_ok:
                    fp_map[round(fp.energy_keV * 2) / 2] = fp

            report = calculate_all_activities(
                identified_isotopes = matches,
                fitted_peaks        = summary.fitted_peaks,
                efficiency_curve    = curve,
                live_time_s         = lt,
                sample_mass_g       = mass_g,
                sample_name         = entry["sample_name"],
            )
        st.session_state["activity_report"]    = report
        st.session_state["fitted_peaks_cache"] = summary.fitted_peaks
        st.session_state["fitted_peaks_map"]   = fp_map

    report = st.session_state.get("activity_report")
    if not report:
        return

    if report.warnings:
        for w in report.warnings:
            _warn(w)

    _slabel("Activity results")
    import pandas as pd
    rows = []
    for r in report.results:
        row = {
            "Isotope":       r.isotope,
            "Energy (keV)":  r.energy_keV,
            "Activity (Bq)": f"{r.activity_bq:.3g} ± {r.activity_unc_bq:.3g}",
            "Activity (µCi)":f"{bq_to_uci(r.activity_bq):.4g}",
            "Efficiency":    f"{r.efficiency:.3e}",
            "χ² fit":        r.fit_chi2,
        }
        if mass_g > 0:
            row["Bq/g"]    = f"{r.activity_bq_g:.3e}" if r.activity_bq_g else "—"
            row["Bq/kg"]   = f"{r.activity_bq_kg:.3e}" if r.activity_bq_kg else "—"
            if r.ratio_to_ref:
                row["× natural"] = f"{r.ratio_to_ref:.1f}×"
        rows.append(row)

    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        _row("Total activity", f"{report.total_activity_bq:.3g}", "Bq")
        if mass_g > 0:
            tot_bq_g = report.total_activity_bq / mass_g
            _row("Total specific activity", f"{tot_bq_g:.3e}", "Bq/g")


# ══════════════════════════════════════════════════════════════════════════════
#  TAB: MDA
# ══════════════════════════════════════════════════════════════════════════════

def render_mda_tab(db: dict):
    st.markdown(
        '<div style="font-family:Georgia,serif;font-size:1.6rem;font-weight:700;'
        'color:#f0e8d8">Minimum Detectable Activity</div>', unsafe_allow_html=True)
    st.caption("Currie (1968) / ISO 11929 method  ·  95% confidence (k = 1.645)")

    curve: EfficiencyCurve | None = st.session_state.get("active_eff_curve")
    if curve is None:
        _warn("Load an efficiency curve first (📐 Efficiency Cal tab).")
        return

    entry, peaks = _get_entry_and_peaks(db, "mda")
    if entry is None or not peaks:
        if entry: st.info("No peaks detected.")
        return

    c1, c2 = st.columns(2)
    lt         = entry["meas_time_s"]
    custom_lt  = c1.number_input("Live time to use (s)  [default = actual]",
                                   min_value=1.0, value=float(lt), key="mda_lt")
    mass_g     = c2.number_input("Sample mass (g)  [0 = omit specific activity]",
                                   min_value=0.0, value=0.0, key="mda_mass")

    if st.button("▶  Calculate MDA", type="primary", key="mda_run"):
        counts   = np.array(entry["counts"])
        energies = np.array(entry["energies"])
        with st.spinner("Fitting peaks for background estimates…"):
            summary = fit_all_peaks(counts, energies, peaks, window_channels=20)
        fp_map = {round(fp.energy_keV * 2) / 2: fp
                  for fp in summary.fitted_peaks if fp.fit_ok}

        matches = st.session_state.get("matches_cache", [])
        if not matches:
            _warn("Run the Identify tab first.")
            return

        results = calculate_mda_spectrum(matches, fp_map, curve, custom_lt, mass_g)
        st.session_state["mda_results"] = results

    results = st.session_state.get("mda_results", [])
    if not results:
        return

    _slabel(f"MDA results ({len(results)} isotopes)")
    import pandas as pd
    rows = []
    for r in results:
        row = {
            "Isotope":     r.isotope,
            "Energy (keV)":r.energy_keV,
            "Background":  f"{r.background_counts:.1f} cts",
            "Lc (cts)":    r.lc_counts,
            "Ld (cts)":    r.ld_counts,
            "MDA (Bq)":    f"{r.mda_bq:.4g}",
            "MDA (µCi)":   f"{bq_to_uci(r.mda_bq):.4g}",
            "Efficiency":  f"{r.efficiency:.3e}",
        }
        if mass_g > 0:
            row["MDA (Bq/g)"]  = f"{r.mda_bq_g:.3e}" if r.mda_bq_g else "—"
            row["MDA (Bq/kg)"] = f"{r.mda_bq_kg:.3e}" if r.mda_bq_kg else "—"
        rows.append(row)
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
#  TAB: SHIELDING
# ══════════════════════════════════════════════════════════════════════════════

def render_shielding_tab():
    st.markdown(
        '<div style="font-family:Georgia,serif;font-size:1.6rem;font-weight:700;'
        'color:#f0e8d8">Shielding Calculator</div>', unsafe_allow_html=True)
    st.caption("Gamma attenuation through slab shields  ·  NIST XCOM μ/ρ data  ·  Berger buildup factor")

    materials = available_materials()
    c1, c2, c3 = st.columns(3)
    material   = c1.selectbox("Shield material", materials, key="sh_mat")
    thickness  = c2.number_input("Thickness (cm)", min_value=0.0, value=5.0, step=0.5, key="sh_thick")
    energy_kev = c3.number_input("Gamma energy (keV)", min_value=40.0, max_value=3000.0,
                                   value=661.7, step=1.0, key="sh_energy")
    use_buildup= st.checkbox("Include buildup factor (conservative)", True, key="sh_buildup")

    if st.button("Calculate", type="primary", key="sh_calc"):
        r = calculate_shielding(material, thickness, energy_kev,
                                 use_buildup=use_buildup)
        st.session_state["sh_result"] = r

        c1, c2, c3, c4 = st.columns(4)
        bc = "#27ae60" if r.transmission < 0.1 else "#d4a843" if r.transmission < 0.5 else "#e87050"
        c1.metric("Transmission",   f"{r.transmission*100:.3f} %")
        c2.metric("Attenuation",    f"{r.attenuation_db:.1f} dB")
        c3.metric("HVL",            f"{r.half_value_layer:.2f} cm")
        c4.metric("TVL",            f"{r.tenth_value_layer:.2f} cm")

        _row("μ/ρ",            f"{r.mu_rho:.4f}",    "cm²/g")
        _row("μ (linear)",     f"{r.mu_linear:.4f}", "cm⁻¹")
        _row("μx",             f"{r.mu_x:.3f}")
        _row("Buildup factor", f"{r.buildup_factor:.3f}")

    # Find thickness for target transmission
    _slabel("Find thickness for target transmission")
    c1, c2 = st.columns(2)
    target_trans_pct = c1.number_input("Target transmission (%)", min_value=0.01,
                                        max_value=99.0, value=10.0, step=1.0, key="sh_target")
    sh_mat2 = c2.selectbox("Material", materials, key="sh_mat2")
    sh_e2   = st.number_input("Energy (keV)", min_value=40.0, max_value=3000.0,
                                value=661.7, step=1.0, key="sh_e2")
    if st.button("Find thickness", key="sh_find"):
        t = thickness_for_transmission(sh_mat2, sh_e2, target_trans_pct/100, use_buildup)
        _ok(f"{t:.2f} cm of {sh_mat2} gives {target_trans_pct:.1f}% transmission at {sh_e2:.1f} keV")

    # Transmission vs thickness curve
    _slabel("Transmission curve")
    if st.button("Plot transmission vs thickness", key="sh_plot"):
        thicknesses = np.linspace(0, max(thickness * 3, 10), 100)
        trans       = [calculate_shielding(material, float(t), energy_kev,
                                            use_buildup=use_buildup).transmission * 100
                       for t in thicknesses]
        fig, ax = plt.subplots(figsize=(8, 3))
        fig.patch.set_facecolor(BG); ax.set_facecolor("#0a0a08")
        ax.semilogy(thicknesses, trans, color="#d4a843", lw=1.5)
        ax.axvline(thickness, color="#27ae60", lw=0.8, ls="--", alpha=0.6,
                   label=f"Current: {thickness} cm")
        ax.axhline(10, color="#c0392b", lw=0.6, ls=":", alpha=0.5, label="10%")
        ax.set_xlabel("Thickness (cm)", color="#6b6350", fontsize=8)
        ax.set_ylabel("Transmission (%)", color="#6b6350", fontsize=8)
        ax.set_title(f"{material}  ·  {energy_kev:.1f} keV", color="#d4a843", fontsize=8)
        ax.tick_params(colors="#6b6350", labelsize=7)
        ax.legend(fontsize=7, facecolor="#1a1a16", labelcolor="#d4a843")
        for sp in ax.spines.values(): sp.set_color("#2a2820")
        fig.tight_layout()
        st.pyplot(fig, use_container_width=True); plt.close()


# ══════════════════════════════════════════════════════════════════════════════
#  TAB: DOSE RATE
# ══════════════════════════════════════════════════════════════════════════════

def render_dose_tab():
    st.markdown(
        '<div style="font-family:Georgia,serif;font-size:1.6rem;font-weight:700;'
        'color:#f0e8d8">Dose Rate Estimator</div>', unsafe_allow_html=True)
    st.caption("Ambient dose equivalent H*(10)  ·  ICRP 74 flux-to-dose conversion  ·  Point source geometry")

    report = st.session_state.get("activity_report")
    if report is None or not report.results:
        _warn("Calculate activities first (⚡ Activity tab). Dose rate is derived from activity.")
        return

    valid = [r for r in report.results if r.activity_bq > 0]
    if not valid:
        _warn("No non-zero activities to compute dose from.")
        return

    c1, c2 = st.columns(2)
    dist_cm   = c1.number_input("Distance from source (cm)", min_value=1.0,
                                  value=100.0, step=10.0, key="dose_dist")
    occ_h_yr  = c2.number_input("Occupancy (hours/year)", min_value=0.0,
                                  value=2000.0, step=100.0, key="dose_occ")

    if st.button("▶  Estimate dose rate", type="primary", key="dose_run"):
        dr = estimate_dose_rate(valid, distance_cm=dist_cm,
                                 sample_name=report.sample_name)
        st.session_state["dose_result"] = dr

    dr = st.session_state.get("dose_result")
    if not dr:
        return

    # Summary cards
    bc = ("#27ae60" if dr.total_dose_rate_usv_h < 0.1 else
          "#d4a843" if dr.total_dose_rate_usv_h < 1.0 else "#e87050")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("H*(10)", f"{dr.total_dose_rate_usv_h:.4g} µSv/h")
    col2.metric("",       f"{dr.total_dose_rate_mrem_h:.4g} mrem/h")
    col3.metric("Annual (at occupancy)", f"{dr.total_dose_rate_usv_h * occ_h_yr / 1000:.3g} mSv/yr")
    col4.metric("Distance", f"{dist_cm} cm")

    for note in dr.notes:
        _warn(note) if "⚠" in note else _ok(note)

    _slabel("Dose contributions by isotope")
    import pandas as pd
    rows = [{
        "Isotope":      c["isotope"],
        "Energy (keV)": c["energy_keV"],
        "Activity (Bq)":c["activity_bq"],
        "Flux (cm⁻²s⁻¹)":f"{c['flux_cm2_s']:.3e}",
        "H*(10) µSv/h": f"{c['dose_usv_h']:.4g}",
        "% of total":   f"{c['pct_of_total']:.1f}%",
    } for c in dr.contributions]
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Dose vs distance table
    _slabel("Dose rate vs distance")
    distances = [10, 25, 50, 100, 200, 500, 1000]
    table = dose_at_distances(valid, distances)
    df2 = pd.DataFrame([{
        "Distance (cm)": t["distance_cm"],
        "Distance (m)":  t["distance_m"],
        "µSv/h":         f"{t['dose_usv_h']:.4g}",
        "mrem/h":        f"{t['dose_mrem_h']:.4g}",
        "µSv/yr (2000h)":f"{t['dose_usv_y']:.3g}",
    } for t in table])
    st.dataframe(df2, use_container_width=True, hide_index=True)

    # Dose vs distance plot
    fig, ax = plt.subplots(figsize=(8, 3))
    fig.patch.set_facecolor(BG); ax.set_facecolor("#0a0a08")
    d_plot  = np.linspace(5, 1000, 200)
    dr_plot = [estimate_dose_rate(valid, d).total_dose_rate_usv_h for d in d_plot]
    ax.loglog(d_plot, dr_plot, color="#d4a843", lw=1.5)
    ax.axvline(dist_cm, color="#27ae60", lw=0.8, ls="--", label=f"Current: {dist_cm} cm")
    ax.axhline(0.1, color="#6b6350", lw=0.6, ls=":", alpha=0.7, label="0.1 µSv/h")
    ax.set_xlabel("Distance (cm)", color="#6b6350", fontsize=8)
    ax.set_ylabel("H*(10) µSv/h",  color="#6b6350", fontsize=8)
    ax.set_title(f"Dose rate vs distance  —  {report.sample_name}", color="#d4a843", fontsize=8)
    ax.tick_params(colors="#6b6350", labelsize=7)
    ax.legend(fontsize=7, facecolor="#1a1a16", labelcolor="#d4a843")
    for sp in ax.spines.values(): sp.set_color("#2a2820")
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True); plt.close()
