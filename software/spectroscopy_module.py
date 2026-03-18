"""
spectroscopy_module.py
Radiacode-103 Gamma Spectroscopy — full UI with forensic inference engine.
Tabs: Import · Analyze & Identify · Chain Inference · Forensic Profile ·
      Secular Equilibrium · Nuclide Database · Compare
"""

import streamlit as st
import numpy as np
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from scipy.signal import find_peaks, savgol_filter

from isotope_db import (
    GAMMA_LINES, FORENSIC_PROFILES, SERIES_COLORS,
    RAD_AVAILABLE, is_detectable, get_half_life, build_chain,
)
from inference_engine import (
    match_peaks_to_isotopes,
    infer_invisible_parents,
    score_chain_completeness,
    detect_anomalies,
    match_forensic_profile,
    check_secular_equilibrium,
    search_nuclides,
    get_nuclide_full,
)

HOME      = Path.home()
SPEC_DIR  = HOME / "Documents" / "chem_lab" / "spectroscopy"
SPEC_JSON = HOME / "Documents" / "chem_lab" / ".spectra_db.json"
SPEC_DIR.mkdir(parents=True, exist_ok=True)

MINERAL_TYPES = [
    'Unknown / unclassified',
    'Custom (see notes)',
    'Granite',
    'Granodiorite',
    'Diorite',
    'Gabbro',
    'Basalt',
    'Andesite',
    'Rhyolite',
    'Obsidian',
    'Pumice',
    'Tuff',
    'Pegmatite',
    'Syenite',
    'Nepheline syenite',
    'Peridotite',
    'Dunite',
    'Phonolite',
    'Gneiss',
    'Schist',
    'Phyllite',
    'Slate',
    'Quartzite',
    'Marble',
    'Hornfels',
    'Amphibolite',
    'Eclogite',
    'Migmatite',
    'Greenstone',
    'Sandstone',
    'Shale',
    'Mudstone',
    'Siltstone',
    'Limestone',
    'Chalk',
    'Dolomite rock',
    'Conglomerate',
    'Breccia',
    'Chert / Flint',
    'Ironstone',
    'Coal',
    'Lignite',
    'Oil shale',
    'Evaporite',
    'Rock salt (halite)',
    'Gypsum rock',
    'Travertine',
    'Quartz',
    'Feldspar',
    'Mica (muscovite/biotite)',
    'Amphibole',
    'Pyroxene',
    'Olivine',
    'Calcite',
    'Dolomite mineral',
    'Apatite',
    'Zircon',
    'Tourmaline',
    'Garnet',
    'Epidote',
    'Chlorite',
    'Serpentine',
    'Talc',
    'Kaolin / Kaolinite',
    'Montmorillonite / Smectite',
    'Illite',
    'Barite',
    'Fluorite',
    'Gypsum mineral',
    'Anhydrite',
    'Halite',
    'Sylvite',
    'Pyrite',
    'Pyrrhotite',
    'Chalcopyrite',
    'Galena',
    'Sphalerite',
    'Magnetite',
    'Hematite',
    'Ilmenite',
    'Rutile',
    'Chromite',
    'Spinel',
    'Corundum',
    'Graphite',
    'Sulfur',
    'Monazite',
    'Xenotime',
    'Uraninite (pitchblende)',
    'Uranophane',
    'Autunite',
    'Carnotite',
    'Coffinite',
    'Thorianite',
    'Thorite',
    'Allanite',
    'Euxenite',
    'Samarskite',
    'Columbite-tantalite',
    'Pyrochlore',
    'Betafite',
    'Davidite',
    'Brannerite',
    'Phosphate rock (apatite ore)',
    'Phosphorite',
    'Triple superphosphate',
    'Single superphosphate',
    'Ammonium phosphate',
    'Potassium fertilizer (KCl/K2SO4)',
    'NPK fertilizer blend',
    'Topsoil',
    'Sandy soil',
    'Clay soil',
    'Loam',
    'Peat',
    'Alluvial sediment',
    'Marine sediment',
    'Lake sediment',
    'River sand',
    'Beach sand',
    'Mineral sand (heavy mineral)',
    'Black sand (ilmenite/magnetite)',
    'Volcanic ash',
    'Laterite',
    'Bauxite',
    'Red mud (bauxite residue)',
    'Water sample (tap/river/lake)',
    'Groundwater',
    'Seawater',
    'Mineral water',
    'Brine',
    'Sediment slurry',
    'Cement',
    'Concrete',
    'Mortar',
    'Brick (fired clay)',
    'Ceramic tile',
    'Gypsum board / plasterboard',
    'Plaster (gypsum)',
    'Fly ash (coal combustion)',
    'Bottom ash',
    'Slag (blast furnace)',
    'Phosphogypsum (by-product)',
    'TENORM pipe scale',
    'TENORM sludge',
    'Asphalt / bitumen',
    'Coal ash',
    'Zircon sand (industrial)',
    'Steel / iron',
    'Stainless steel',
    'Aluminium',
    'Copper',
    'Lead',
    'Tungsten',
    'Uranium metal / alloy',
    'Thorium metal',
    'Depleted uranium',
    'Sealed radioactive source',
    'Smoke detector (Am-241)',
    'Luminous paint / dial',
    'Radium legacy source',
    'Industrial gauge source',
    'Well logging source',
    'Radiography source (Ir-192/Se-75)',
    'Calibration source -- Cs-137',
    'Calibration source -- Co-60',
    'Calibration source -- Eu-152',
    'Calibration source -- Ba-133',
    'Calibration source -- Am-241',
    'Calibration source -- Na-22',
    'Calibration source -- Mn-54',
    'Calibration source -- Zn-65',
    'Mixed calibration source',
    'Marinelli beaker standard',
    'Medical waste',
    'Nuclear medicine patient sample',
    'Radiopharmaceutical',
    'Air filter',
    'Air particulate',
    'Vegetation / plant matter',
    'Food sample',
    'Milk / dairy',
    'Meat / fish',
    'Grain / cereal',
    'Bone / tissue',
    'Urine / biological fluid',
    'Swipe / wipe sample',
    'Background measurement',
    'Blank / empty container',
    'Reference material (certified)',
]




def load_db():
    if SPEC_JSON.exists():
        try:    return json.loads(SPEC_JSON.read_text())
        except: return {}
    return {}

def save_db(db):
    SPEC_JSON.write_text(json.dumps(db, indent=2, default=str))


# ── Parser ─────────────────────────────────────────────────────────────────────

def parse_radiacode_xml(content: bytes) -> dict:
    root = ET.fromstring(content)
    rd_el = root.find(".//ResultData")
    if rd_el is None:
        raise ValueError("No ResultData element found.")

    sample_name = ""
    sn = rd_el.find(".//SampleInfo/n")
    if sn is not None and sn.text: sample_name = sn.text.strip()
    serial    = (rd_el.findtext(".//SerialNumber") or "").strip()
    start_time= rd_el.findtext(".//StartTime", "")
    end_time  = rd_el.findtext(".//EndTime",   "")
    meas_time = int(rd_el.findtext(".//MeasurementTime", "0"))

    coeffs = []
    for c in rd_el.findall(".//EnergyCalibration/Coefficients/Coefficient"):
        coeffs.append(float(c.text))
    if len(coeffs) < 2:
        coeffs = [0.0, 3.0, 0.0]

    counts = [int(dp.text or 0) for dp in rd_el.findall(".//Spectrum/DataPoint")]
    n      = len(counts)
    ch     = np.arange(n, dtype=float)
    if len(coeffs) == 3:
        energies = coeffs[0] + coeffs[1]*ch + coeffs[2]*ch**2
    else:
        energies = coeffs[0] + coeffs[1]*ch

    return {
        "sample_name": sample_name, "serial": serial,
        "start_time":  start_time,  "end_time": end_time,
        "meas_time_s": meas_time,   "n_channels": n,
        "coeffs":      coeffs,      "counts": counts,
        "energies":    energies.tolist(),
    }


# ── Peak finder ────────────────────────────────────────────────────────────────

def find_spectrum_peaks(counts, energies, prominence_pct=0.02, min_energy=40.0):
    counts_arr   = np.array(counts, dtype=float)
    energies_arr = np.array(energies)
    window = min(21, len(counts_arr) // 10 * 2 + 1)
    if window < 5: window = 5
    smoothed = savgol_filter(counts_arr, window_length=window, polyorder=3)
    smoothed = np.clip(smoothed, 0, None)
    peaks, props = find_peaks(
        smoothed,
        prominence=smoothed.max() * prominence_pct,
        width=2, distance=4,
    )
    results = []
    for i, ch in enumerate(peaks):
        e = float(energies_arr[ch])
        if e < min_energy: continue
        de = abs(float(energies_arr[min(ch+1,len(energies_arr)-1)]) - e)
        fwhm_kev = props["widths"][i] * de
        results.append({
            "channel":    int(ch),
            "energy_keV": round(e, 2),
            "counts":     int(counts_arr[ch]),
            "smoothed":   float(smoothed[ch]),
            "prominence": float(props["prominences"][i]),
            "fwhm_keV":   round(fwhm_kev, 2),
        })
    results.sort(key=lambda x: x["prominence"], reverse=True)
    return results


# ── Shared CSS ─────────────────────────────────────────────────────────────────

def spec_css():
    st.markdown("""
    <style>
    .spec-h1{font-family:'Cormorant Garamond',serif;font-size:2.2rem;font-weight:700;
             color:#f0e8d8;margin-bottom:0.1rem}
    .spec-tag{font-family:'JetBrains Mono',monospace;font-size:0.62rem;color:#4a4838;
              letter-spacing:.18em;text-transform:uppercase;margin-bottom:1.4rem}
    .sec-label{font-family:'JetBrains Mono',monospace;font-size:0.68rem;color:#d4a843;
               letter-spacing:.15em;margin:1rem 0 .4rem}
    .iso-card{background:#0f0f0c;border:1px solid #2a2820;border-left:3px solid var(--c);
              border-radius:3px;padding:.8rem 1rem;margin:.35rem 0}
    .iso-name{font-family:'Cormorant Garamond',serif;font-size:1.25rem;font-weight:700;color:#f0e8d8}
    .iso-meta{font-family:'JetBrains Mono',monospace;font-size:.62rem;color:#5a5040;margin-top:.15rem}
    .peak-match{font-family:'JetBrains Mono',monospace;font-size:.7rem;padding:.2rem .5rem;
                background:#0c0c0a;border-left:2px solid #27ae60;margin:.15rem 0;color:#90c890}
    .peak-miss{font-family:'JetBrains Mono',monospace;font-size:.7rem;padding:.2rem .5rem;
               background:#0c0c0a;border-left:2px solid #6b3030;margin:.15rem 0;color:#906060}
    .chain-row{font-family:'JetBrains Mono',monospace;font-size:.68rem;padding:.2rem .5rem;
               border-left:2px solid #3a3020;margin:.1rem 0;color:#8a8060}
    .chain-det{border-left-color:#d4a843 !important;color:#d4a843 !important}
    .chain-invis{color:#5a5040 !important}
    .flag-high{background:#1f0a0a;border:1px solid #5a1a1a;border-radius:2px;
               padding:.5rem .8rem;margin:.3rem 0;font-family:'JetBrains Mono',monospace;font-size:.72rem;color:#e07070}
    .flag-med{background:#1a1408;border:1px solid #5a4010;border-radius:2px;
              padding:.5rem .8rem;margin:.3rem 0;font-family:'JetBrains Mono',monospace;font-size:.72rem;color:#d4a843}
    .flag-low{background:#0e0e0c;border:1px solid #2a2820;border-radius:2px;
              padding:.5rem .8rem;margin:.3rem 0;font-family:'JetBrains Mono',monospace;font-size:.72rem;color:#6b6350}
    .verdict-box{padding:.8rem 1.2rem;border-radius:3px;margin:1rem 0;
                 font-family:'Cormorant Garamond',serif;font-size:1.1rem;font-weight:600}
    .infer-card{background:#0c0e0c;border:1px solid #1a2a1a;border-left:3px solid #27ae60;
                border-radius:3px;padding:.8rem 1rem;margin:.4rem 0}
    .status-ok{font-family:'JetBrains Mono',monospace;font-size:.72rem;color:#27ae60;
               padding:.3rem .7rem;background:#0a1f0e;border:1px solid #1a4a22;
               border-radius:2px;display:inline-block;margin:.4rem 0}
    .nuc-row{font-family:'JetBrains Mono',monospace;font-size:.7rem;padding:.3rem .5rem;
             background:#0c0c0a;border:1px solid #1e1e18;border-radius:2px;margin:.15rem 0}
    </style>
    """, unsafe_allow_html=True)


# ── Plot helper ────────────────────────────────────────────────────────────────

def spectrum_plot(entry, peaks=None, log=True, show_smooth=True, title_extra=""):
    import matplotlib.pyplot as plt
    counts   = np.array(entry["counts"], dtype=float)
    energies = np.array(entry["energies"])
    lt       = max(entry["meas_time_s"], 1)
    cps      = counts / lt

    fig, ax = plt.subplots(figsize=(12, 3.8))
    fig.patch.set_facecolor("#0e0e0c")
    ax.set_facecolor("#0a0a08")

    if show_smooth:
        w = min(21, len(cps)//10*2+1); w = max(w,5)
        sm = np.clip(savgol_filter(cps, w, 3), 1e-12 if log else 0, None)
        ax.fill_between(energies, sm, alpha=.22, color="#d4a843")
        ax.plot(energies, sm, color="#d4a843", lw=0.9, label="Smoothed", zorder=3)

    raw = np.clip(cps, 1e-12 if log else 0, None)
    ax.plot(energies, raw, color="#6b6350", lw=0.5, alpha=.7, label="Raw", zorder=2)

    if peaks:
        for pk in peaks[:40]:
            e = pk["energy_keV"]; c = pk["counts"]/lt
            ax.axvline(e, color="#c0392b", lw=0.5, alpha=.4, zorder=4)
            ax.annotate(f"{e:.1f}", xy=(e,c), xytext=(0,6),
                        textcoords="offset points", fontsize=5.2,
                        color="#e07070", ha="center", fontfamily="monospace")

    if log: ax.set_yscale("log")
    ax.set_xlabel("Energy (keV)", color="#6b6350", fontsize=8)
    ax.set_ylabel("CPS", color="#6b6350", fontsize=8)
    lt_h = entry["meas_time_s"]//3600; lt_m = (entry["meas_time_s"]%3600)//60
    ax.set_title(
        f"{entry['sample_name']}  ·  {lt_h}h{lt_m}m  ·  "
        f"{entry.get('mineral_type','')}  ·  "
        f"{entry.get('shielding','no shield')}  ·  "
        f"{entry.get('distance_cm',0)}cm{title_extra}",
        color="#d4a843", fontsize=8, pad=4)
    ax.tick_params(colors="#6b6350", labelsize=7)
    ax.legend(fontsize=7, facecolor="#1a1a16", labelcolor="#d4a843", framealpha=.8)
    for sp in ax.spines.values(): sp.set_color("#2a2820")
    ax.set_xlim(0)
    return fig


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN RENDER
# ══════════════════════════════════════════════════════════════════════════════

def render_spectroscopy():
    # Consume any pending spectrum selection BEFORE widgets instantiate
    _pending_spec = st.session_state.pop("_pending_sel_id", None)
    if _pending_spec and _pending_spec in load_db():
        st.session_state["_active_sel_id"] = _pending_spec
    import matplotlib.pyplot as plt
    import pandas as pd

    spec_css()

    st.markdown('<div class="spec-h1">Gamma Spectroscopy</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="spec-tag">Radiacode-103 · full forensic inference engine · '
        f'{"radioactivedecay ✓ (IAEA 1252 nuclides)" if RAD_AVAILABLE else "radioactivedecay not found — install with pip3"}</div>',
        unsafe_allow_html=True)

    if not RAD_AVAILABLE:
        st.error("radioactivedecay not installed. Run: **pip3 install radioactivedecay**")

    db = load_db()

    tabs = st.tabs([
        "📥 Import",
        "🔍 Identify",
        "🧬 Chain Inference",
        "🔬 Forensic Profile",
        "⚖️ Secular Equilibrium",
        "🗄️ Nuclide Database",
        "🗂️ My Spectra",
        "📊 Compare",
    ])

    # ════════════════════════════════════════════════════════════════════════
    #  TAB 1 — IMPORT
    # ════════════════════════════════════════════════════════════════════════
    with tabs[0]:
        st.markdown('<div class="sec-label">UPLOAD RADIACODE-103 XML EXPORT</div>',
                    unsafe_allow_html=True)
        uploaded = st.file_uploader("Drop .xml file", type=["xml"],
                                    label_visibility="collapsed", key="xml_upload")
        if uploaded:
            try:
                spec = parse_radiacode_xml(uploaded.read())
                st.markdown(
                    f'<div class="status-ok">✓ Parsed — {spec["n_channels"]} channels · '
                    f'{spec["meas_time_s"]:,} s · {spec["serial"]}</div>',
                    unsafe_allow_html=True)

                # Quick preview
                fig = spectrum_plot(
                    {**spec,"mineral_type":"","shielding":"","distance_cm":0},
                    log=True, show_smooth=True)
                st.pyplot(fig, use_container_width=True); plt.close()

                st.markdown('<div class="sec-label">METADATA</div>', unsafe_allow_html=True)
                c1,c2 = st.columns(2)
                sample_name  = c1.text_input("Sample name",  value=spec["sample_name"] or uploaded.name)
                mineral_type = c1.text_input("Mineral / material type",
                                              placeholder="Trinitite, Autunite, Uraninite…")
                distance_cm  = c2.number_input("Distance from source (cm)", value=0.0, step=0.5)
                shielding    = c2.text_input("Shielding", placeholder="None / 1 cm Pb / 5 mm Al…")
                c3,c4 = st.columns(2)
                location = c3.text_input("Location", placeholder="Lab, Field, Trinity Site…")
                notes    = c4.text_area("Notes", height=72)

                if st.button("💾  Save to Database", type="primary"):
                    eid = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uploaded.name[:20]
                    entry = {**spec,
                             "id":eid, "sample_name":sample_name, "mineral_type":mineral_type,
                             "distance_cm":distance_cm, "shielding":shielding,
                             "location":location, "notes":notes,
                             "filename":uploaded.name, "imported_at":datetime.now().isoformat()}
                    db[eid] = entry; save_db(db)
                    st.markdown('<div class="status-ok">✓ Saved to database</div>',
                                unsafe_allow_html=True)
                    st.session_state["sel_id"] = eid
            except Exception as e:
                st.error(f"Parse error: {e}")

    # ── Shared spectrum selector (used by multiple tabs) ──────────────────────
    def spectrum_selector(key_prefix=""):
        if not db:
            st.info("No spectra yet — import one first."); return None
        labels = {eid: f"{e['sample_name']}  ·  {e.get('mineral_type','')}  ·  {e['meas_time_s']:,}s"
                  for eid,e in db.items()}
        default = 0
        if "sel_id" in st.session_state and st.session_state["sel_id"] in db:
            default = list(db.keys()).index(st.session_state["sel_id"])
        return st.selectbox("Select spectrum", list(db.keys()),
                            format_func=lambda x: labels[x],
                            index=default, key=f"sel_{key_prefix}")

    # ════════════════════════════════════════════════════════════════════════
    #  TAB 2 — IDENTIFY
    # ════════════════════════════════════════════════════════════════════════
    with tabs[1]:
        sel = spectrum_selector("id")
        if sel:
            entry   = db[sel]
            counts  = np.array(entry["counts"])
            energies= np.array(entry["energies"])
            lt      = entry["meas_time_s"]

            with st.expander("⚙ Detection settings", expanded=False):
                c1,c2,c3 = st.columns(3)
                prom_pct  = c1.slider("Prominence threshold (%)", 0.5,10.0,2.0,0.5, key="id_prom")/100
                tol_kev   = c2.slider("Match tolerance (keV)", 3.0,30.0,12.0,1.0, key="id_tol")
                min_e     = c3.slider("Min energy (keV)", 10.0,100.0,40.0,5.0, key="id_mine")
                log_y     = c1.checkbox("Log Y", True, key="id_logy")
                sm_on     = c2.checkbox("Show smoothed", True, key="id_smooth")
                max_res   = c3.slider("Max results", 3,30,15, key="id_maxres")

            peaks   = find_spectrum_peaks(counts.tolist(), energies.tolist(),
                                          prominence_pct=prom_pct, min_energy=min_e)
            matches = match_peaks_to_isotopes(peaks, tolerance_keV=tol_kev,
                                              max_results=max_res)

            fig = spectrum_plot(entry, peaks=peaks, log=log_y, show_smooth=sm_on)
            st.pyplot(fig, use_container_width=True); plt.close()

            # Cache for other tabs
            st.session_state["peaks_cache"]   = peaks
            st.session_state["matches_cache"] = matches
            st.session_state["entry_cache"]   = entry

            st.markdown(f'<div class="sec-label">DETECTED PEAKS ({len(peaks)})</div>',
                        unsafe_allow_html=True)
            if peaks:
                df = pd.DataFrame([{
                    "Energy (keV)": p["energy_keV"],
                    "Channel": p["channel"],
                    "Counts": p["counts"],
                    "CPS": round(p["counts"]/max(lt,1),5),
                    "FWHM (keV)": p["fwhm_keV"],
                } for p in peaks])
                st.dataframe(df, use_container_width=True, hide_index=True)

            st.markdown(f'<div class="sec-label">ISOTOPE MATCHES</div>',
                        unsafe_allow_html=True)
            for i,m in enumerate(matches):
                sym   = m["symbol"]
                conf  = m["pct"]
                det   = m["detectable"]
                bar_c = "#27ae60" if conf>=40 else "#d4a843" if conf>=20 else "#6b4030"
                badge = (' <span style="background:#1a4a22;color:#27ae60;'
                         'font-size:.6rem;padding:1px 5px;border-radius:2px">MOST LIKELY</span>'
                         if i==0 and conf>25 else "")
                with st.expander(
                    f"{'★ ' if i==0 else '  '}{sym}  —  {conf}%  "
                    f"({m['n_matched']}/{m['n_total']} lines)  ·  t½={m['half_life']}",
                    expanded=(i==0)
                ):
                    st.markdown(f"""
                    <div class="iso-card" style="--c:{bar_c}">
                      <span class="iso-name">{sym}</span>{badge}
                      <div style="height:4px;background:#1a1a16;border-radius:2px;margin:6px 0">
                        <div style="height:100%;width:{conf}%;background:{bar_c};border-radius:2px"></div>
                      </div>
                      <div class="iso-meta">t½ = {m['half_life']} &nbsp;·&nbsp;
                        {"Directly detectable by RC-103" if det else "⚠ NOT directly detectable"}</div>
                    </div>""", unsafe_allow_html=True)

                    st.markdown('<div class="sec-label" style="font-size:.6rem">MATCHED LINES</div>',
                                unsafe_allow_html=True)
                    for mt in m["matched"]:
                        cps_v = round(mt["peak_data"].get("counts",0)/max(lt,1),5)
                        st.markdown(
                            f'<div class="peak-match">✓ {mt["det_keV"]} keV detected &nbsp;|&nbsp; '
                            f'library: {mt["lib_keV"]} keV &nbsp;|&nbsp; Δ={mt["delta_keV"]} keV &nbsp;|&nbsp; '
                            f'intensity: {mt["intensity"]}% &nbsp;|&nbsp; {cps_v} CPS</div>',
                            unsafe_allow_html=True)
                    if m["unmatched"]:
                        st.markdown('<div class="sec-label" style="font-size:.6rem;color:#904040">UNMATCHED LIBRARY LINES</div>',
                                    unsafe_allow_html=True)
                        for um in m["unmatched"]:
                            st.markdown(
                                f'<div class="peak-miss">✗ {um["lib_keV"]} keV &nbsp;|&nbsp; '
                                f'{um["intensity"]}% — not detected</div>',
                                unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    #  TAB 3 — CHAIN INFERENCE
    # ════════════════════════════════════════════════════════════════════════
    with tabs[2]:
        st.markdown('<div class="sec-label">ALPHA-BLIND PARENT INFERENCE</div>',
                    unsafe_allow_html=True)
        st.caption(
            "Using detected isotopes, the inference engine walks backwards through "
            "decay chains to identify invisible parents (alpha emitters, pure-beta emitters) "
            "whose daughters ARE visible in the spectrum.")

        # Get detected isotopes from session or re-run
        matches_c = st.session_state.get("matches_cache", [])
        peaks_c   = st.session_state.get("peaks_cache",   [])
        entry_c   = st.session_state.get("entry_cache",   {})

        if not matches_c:
            st.info("Run the Identify tab first to populate matches.")
        else:
            conf_thresh = st.slider("Minimum chain coverage for inference (%)",
                                    5, 60, 20, 5, key="ci_thresh") / 100
            detected_syms = [m["symbol"] for m in matches_c if m["confidence"] >= conf_thresh]

            st.markdown(
                f'<div class="sec-label">DETECTED ISOTOPES USED AS EVIDENCE ({len(detected_syms)})</div>',
                unsafe_allow_html=True)
            st.markdown(
                '<div style="font-family:JetBrains Mono,monospace;font-size:.72rem;'
                'color:#d4a843;margin-bottom:.8rem">' +
                "  ·  ".join(detected_syms) + "</div>",
                unsafe_allow_html=True)

            # Alpha-blind inference
            inferred = infer_invisible_parents(detected_syms, confidence_threshold=0.1)

            if not inferred:
                st.info("No invisible parents inferred. Try lowering the confidence threshold "
                        "or run the Identify tab first.")
            else:
                st.markdown(f'<div class="sec-label">INFERRED INVISIBLE PARENTS ({len(inferred)})</div>',
                            unsafe_allow_html=True)
                for inf in inferred:
                    bar_pct = int(inf["confidence"]*100)
                    bar_c   = "#27ae60" if bar_pct>=60 else "#d4a843" if bar_pct>=30 else "#e87070"
                    with st.expander(
                        f"{inf['parent']}  —  {bar_pct}% chain coverage  ·  "
                        f"t½={inf['half_life']}  ·  {inf['invisible_reason']}",
                        expanded=(bar_pct>=50)
                    ):
                        st.markdown(f"""
                        <div class="infer-card">
                          <span style="font-family:'Cormorant Garamond',serif;font-size:1.2rem;
                            font-weight:700;color:#f0e8d8">{inf['parent']}</span>
                          <span style="font-family:'JetBrains Mono',monospace;font-size:.65rem;
                            color:#27ae60;margin-left:8px">INFERRED PARENT</span>
                          <div style="height:4px;background:#1a2a1a;border-radius:2px;margin:6px 0">
                            <div style="height:100%;width:{bar_pct}%;background:{bar_c};border-radius:2px"></div>
                          </div>
                          <div style="font-family:'JetBrains Mono',monospace;font-size:.62rem;color:#5a7050;margin-top:.2rem">
                            Reason invisible: {inf['invisible_reason']} &nbsp;·&nbsp;
                            t½ = {inf['half_life']} &nbsp;·&nbsp;
                            {inf['visible_detected']}/{inf['visible_expected']} visible chain members detected
                          </div>
                        </div>""", unsafe_allow_html=True)

                        st.markdown('<div class="sec-label" style="font-size:.6rem">SUPPORTING EVIDENCE (detected daughters)</div>',
                                    unsafe_allow_html=True)
                        for ev in inf["evidence"]:
                            gammas_str = "  ".join(f"{e:.1f}keV({i:.0f}%)" for e,i,_ in ev["gammas"])
                            st.markdown(
                                f'<div class="peak-match">✓ {ev["symbol"]} &nbsp;·&nbsp; t½={ev["half_life"]} '
                                f'&nbsp;·&nbsp; {gammas_str}</div>',
                                unsafe_allow_html=True)

            # Chain completeness for selected parents
            st.markdown('<div class="sec-label" style="margin-top:1.5rem">CHAIN COMPLETENESS SCORER</div>',
                        unsafe_allow_html=True)
            common_parents = ["U-238","Th-232","U-235","Pu-239","Pu-241","Np-237","Ra-226","Cs-137","Co-60"]
            sel_parent = st.selectbox("Score completeness for parent:", common_parents, key="chain_parent")
            if sel_parent:
                cs = score_chain_completeness(sel_parent, detected_syms)
                if "error" not in cs:
                    pct = cs["completeness_pct"]
                    bar_c = "#27ae60" if pct>=70 else "#d4a843" if pct>=30 else "#e87070"
                    st.markdown(f"""
                    <div style="background:#0c0c0a;border:1px solid #2a2820;border-radius:3px;padding:.8rem 1rem;margin:.5rem 0">
                      <div style="font-family:'JetBrains Mono',monospace;font-size:.65rem;color:#d4a843;margin-bottom:.4rem">
                        {sel_parent} CHAIN — {pct}% COMPLETE
                        ({cs['detectable_found']}/{cs['detectable_expected']} detectable members found)
                      </div>
                      <div style="height:6px;background:#1a1a16;border-radius:3px">
                        <div style="height:100%;width:{pct}%;background:{bar_c};border-radius:3px"></div>
                      </div>
                      <div style="font-family:'Libre Baskerville',serif;font-size:.8rem;color:#9a9080;margin-top:.5rem">
                        {cs['interpretation']}
                      </div>
                    </div>""", unsafe_allow_html=True)

                    # Full chain visualisation
                    with st.expander("View full chain"):
                        for m in cs["full_chain"]:
                            indent = "  " * m["depth"]
                            det    = m["detectable"]
                            found  = m["symbol"] in detected_syms
                            css_cls= "chain-det" if (det and found) else ("chain-row" if det else "chain-invis")
                            icon   = "✓" if found else ("○" if det else "·")
                            gstr   = "  ".join(f"{e:.1f}keV" for e,_,_ in m["strong_gammas"][:3])
                            st.markdown(
                                f'<div class="{css_cls}" style="padding-left:{8+m["depth"]*14}px">'
                                f'{icon} {m["symbol"]} &nbsp;·&nbsp; t½={m["half_life"]} &nbsp;·&nbsp; '
                                f'{m["decay_mode"]} &nbsp;·&nbsp; '
                                f'{"detectable" if det else m["detect_reason"]} &nbsp;·&nbsp; {gstr}'
                                f'</div>', unsafe_allow_html=True)

                    # Anomaly detection
                    anomalies = detect_anomalies(detected_syms, peaks_c)
                    if anomalies:
                        st.markdown('<div class="sec-label" style="margin-top:1rem">ANOMALIES & FLAGS</div>',
                                    unsafe_allow_html=True)
                        for an in anomalies:
                            css_c = f"flag-{an['level']}"
                            st.markdown(
                                f'<div class="{css_c}"><strong>{an["title"]}</strong><br>{an["detail"]}</div>',
                                unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    #  TAB 4 — FORENSIC PROFILE
    # ════════════════════════════════════════════════════════════════════════
    with tabs[3]:
        st.markdown('<div class="sec-label">FORENSIC AUTHENTICATION PROFILE</div>',
                    unsafe_allow_html=True)
        matches_c = st.session_state.get("matches_cache", [])
        if not matches_c:
            st.info("Run the Identify tab first.")
        else:
            prof_name = st.selectbox("Authentication profile:",
                                     list(FORENSIC_PROFILES.keys()), key="fp_prof")
            conf_thresh = st.slider("Isotope confidence threshold (%)",
                                    5, 50, 20, 5, key="fp_thresh") / 100
            detected_syms = [m["symbol"] for m in matches_c if m["confidence"] >= conf_thresh]

            result = match_forensic_profile(
                detected_syms, prof_name,
                detected_peaks=st.session_state.get("peaks_cache",[])
            )

            # Verdict banner
            st.markdown(
                f'<div class="verdict-box" style="background:{result["verdict_color"]}22;'
                f'border:1px solid {result["verdict_color"]}55;color:{result["verdict_color"]}">'
                f'{result["verdict"]}'
                f'<span style="font-family:JetBrains Mono,monospace;font-size:.8rem;'
                f'float:right;font-weight:400">Score: {result["score"]}%</span></div>',
                unsafe_allow_html=True)

            # Score bar
            sc = result["score"]
            bar_c = "#27ae60" if sc>=75 else "#d4a843" if sc>=50 else "#e87060"
            st.markdown(f"""
            <div style="background:#1a1a16;border-radius:3px;height:8px;margin-bottom:1rem">
              <div style="height:100%;width:{sc}%;background:{bar_c};border-radius:3px"></div>
            </div>""", unsafe_allow_html=True)

            st.caption(result["description"])

            # Group results
            st.markdown('<div class="sec-label">EXPECTED SIGNATURE GROUPS</div>',
                        unsafe_allow_html=True)
            for gr in result["group_results"]:
                if gr["complete"]:
                    icon, color = "✓", "#27ae60"
                elif gr["partial"]:
                    icon, color = "◑", "#d4a843"
                else:
                    icon, color = "✗", "#c0392b"
                found_str   = ", ".join(gr["found"])   or "none"
                missing_str = ", ".join(gr["missing"]) or "none"
                st.markdown(f"""
                <div style="background:#0f0f0c;border:1px solid #222018;border-left:3px solid {color};
                  border-radius:2px;padding:.5rem .9rem;margin:.25rem 0;
                  font-family:'JetBrains Mono',monospace;font-size:.7rem">
                  <span style="color:{color}">{icon}</span>
                  <strong style="color:#e8dfc8;margin-left:6px">{gr['group']}</strong>
                  <span style="color:#5a5040;font-size:.62rem;margin-left:8px">{gr['desc']}</span><br>
                  <span style="color:#27ae60">found: {found_str}</span>
                  {"  ·  <span style='color:#c05050'>missing: "+missing_str+"</span>" if missing_str != "none" else ""}
                </div>""", unsafe_allow_html=True)

            # Alpha-blind inferences
            st.markdown('<div class="sec-label" style="margin-top:1rem">ALPHA-BLIND INFERENCES</div>',
                        unsafe_allow_html=True)
            for ab in result["alpha_blind"]:
                conf_pct = int(ab["confidence"]*100)
                bar_c2   = "#27ae60" if conf_pct>=70 else "#d4a843" if conf_pct>=40 else "#6b4030"
                with st.expander(
                    f"{'✓' if conf_pct>=50 else '○'} Inferred: {ab['inferred']}  —  "
                    f"{conf_pct}% evidence ({len(ab['evidence_found'])}/{len(ab['evidence_needed'])} supporting isotopes)",
                    expanded=(conf_pct>=50)
                ):
                    st.markdown(f"""
                    <div class="infer-card">
                      <div style="font-family:'JetBrains Mono',monospace;font-size:.65rem;
                        color:#d4a843;margin-bottom:.4rem">
                        Evidence needed: {", ".join(ab['evidence_needed'])} &nbsp;·&nbsp;
                        Evidence found: {", ".join(ab['evidence_found']) or "none"}
                      </div>
                      <div style="height:4px;background:#1a2a1a;border-radius:2px;margin-bottom:.6rem">
                        <div style="height:100%;width:{conf_pct}%;background:{bar_c2};border-radius:2px"></div>
                      </div>
                      <div style="font-family:'Libre Baskerville',serif;font-size:.82rem;
                        color:#c8c0a8;line-height:1.6">{ab['logic']}</div>
                    </div>""", unsafe_allow_html=True)

            # Anomaly flags
            if result["anomaly_flags"]:
                st.markdown('<div class="sec-label" style="margin-top:1rem">ANOMALY FLAGS</div>',
                            unsafe_allow_html=True)
                for fl in result["anomaly_flags"]:
                    level = "high" if "MAJOR" in fl["title"] else "med"
                    st.markdown(
                        f'<div class="flag-{level}"><strong>{fl["title"]}</strong>'
                        f'<br><span style="font-size:.67rem;opacity:.8">{fl["detail"]}</span></div>',
                        unsafe_allow_html=True)
            else:
                st.markdown('<div class="flag-low">No anomaly flags triggered.</div>',
                            unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    #  TAB 5 — SECULAR EQUILIBRIUM
    # ════════════════════════════════════════════════════════════════════════
    with tabs[4]:
        st.markdown('<div class="sec-label">SECULAR EQUILIBRIUM CHECKER</div>',
                    unsafe_allow_html=True)
        st.caption(
            "Compares measured activity ratios between parent/daughter pairs to "
            "what is expected if the chain is in secular equilibrium. "
            "Deviations indicate chain disruption, Rn escape, or recent chemical processing.")

        matches_c = st.session_state.get("matches_cache", [])
        entry_c   = st.session_state.get("entry_cache",   {})
        peaks_c   = st.session_state.get("peaks_cache",   [])

        if not matches_c:
            st.info("Run the Identify tab first.")
        else:
            age_y = st.number_input("Estimated sample age (years)", value=1_000_000,
                                    step=1000, format="%d", key="se_age",
                                    help="Used to calculate expected equilibrium ratios")

            # Build activity map from peaks
            lt = entry_c.get("meas_time_s", 1)
            activity_map: dict[str,float] = {}
            for m in matches_c:
                if m["matched"] and m["confidence"] >= 0.15:
                    # Use the strongest matched peak CPS as proxy activity
                    best_peak = max(m["matched"], key=lambda x: x["intensity"])
                    cps = best_peak["peak_data"].get("counts",0) / max(lt,1)
                    activity_map[m["symbol"]] = cps

            eq_results = check_secular_equilibrium(activity_map, sample_age_years=age_y)

            if not eq_results:
                st.info("Not enough paired isotopes detected to run equilibrium check. "
                        "Need at least two members of the same decay chain with strong peaks.")
            else:
                for eq in eq_results:
                    status_color = {"equilibrium":"#27ae60",
                                    "mild deviation":"#d4a843",
                                    "broken":"#c0392b"}.get(eq["status"], "#aaa")
                    obs = eq["observed_ratio"]
                    exp = eq["expected_ratio"]
                    max_r = max(obs, exp, 0.01)

                    st.markdown(f"""
                    <div style="background:#0f0f0c;border:1px solid #2a2820;
                      border-left:3px solid {status_color};border-radius:3px;
                      padding:.7rem 1rem;margin:.4rem 0">
                      <div style="display:flex;justify-content:space-between;align-items:center">
                        <span style="font-family:'JetBrains Mono',monospace;font-size:.75rem;color:#e8dfc8">
                          {eq['parent']} → {eq['daughter']}
                        </span>
                        <span style="font-family:'JetBrains Mono',monospace;font-size:.7rem;color:{status_color}">
                          {eq['status'].upper()}  ·  dev={eq['deviation_pct']}%
                        </span>
                      </div>
                      <div style="margin:.4rem 0;font-family:'JetBrains Mono',monospace;font-size:.65rem;color:#5a5040">
                        Observed ratio: {obs:.4f} &nbsp;·&nbsp; Expected: {exp:.4f} &nbsp;·&nbsp; Condition: {eq['condition']}
                      </div>
                      <div style="display:flex;gap:6px;align-items:center;margin:.3rem 0">
                        <span style="font-family:'JetBrains Mono',monospace;font-size:.6rem;color:#4a4030;width:60px">observed</span>
                        <div style="flex:1;background:#1a1a16;border-radius:2px;height:5px">
                          <div style="height:100%;width:{min(obs/max_r,1)*100:.0f}%;background:{status_color};border-radius:2px"></div>
                        </div>
                      </div>
                      <div style="display:flex;gap:6px;align-items:center">
                        <span style="font-family:'JetBrains Mono',monospace;font-size:.6rem;color:#4a4030;width:60px">expected</span>
                        <div style="flex:1;background:#1a1a16;border-radius:2px;height:5px">
                          <div style="height:100%;width:{min(exp/max_r,1)*100:.0f}%;background:#4a4030;border-radius:2px"></div>
                        </div>
                      </div>
                      <div style="font-family:'Libre Baskerville',serif;font-size:.78rem;color:#9a9080;margin-top:.5rem">
                        {eq['interpretation']}
                      </div>
                    </div>""", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    #  TAB 6 — NUCLIDE DATABASE
    # ════════════════════════════════════════════════════════════════════════
    with tabs[5]:
        st.markdown('<div class="sec-label">NUCLIDE DATABASE SEARCH</div>',
                    unsafe_allow_html=True)
        if not RAD_AVAILABLE:
            st.warning("radioactivedecay not installed — only curated gamma lines available.")

        query = st.text_input("Search nuclide (e.g. Bi-214, U, Cs)", placeholder="Bi-214", key="nuc_query")
        if query:
            results = search_nuclides(query, limit=40)
            if not results:
                st.info("No matches found.")
            else:
                st.caption(f"{len(results)} results")
                for nuc in results:
                    with st.expander(
                        f"{nuc['symbol']}  ·  t½={nuc['half_life']}  ·  "
                        f"{'RC-103 detectable' if nuc['detectable'] else '⚠ not directly detectable'}",
                        expanded=False
                    ):
                        full = get_nuclide_full(nuc["symbol"])

                        c1,c2 = st.columns(2)
                        c1.markdown(f"**Half-life:** {full['half_life']}")
                        det_str = "Yes" if full['detectable'] else f"No — {full.get('detect_reason', '')}"
                        c2.markdown(f"**Detectable:** {det_str}")

                        if full["daughters"]:
                            st.markdown("**Daughters:**")
                            for d,bf,mode in full["daughters"]:
                                st.markdown(
                                    f'<div class="nuc-row">{d} &nbsp;·&nbsp; {bf:.2f}% &nbsp;·&nbsp; {mode}</div>',
                                    unsafe_allow_html=True)

                        if full["gammas"]:
                            st.markdown("**Gamma lines:**")
                            gdf = pd.DataFrame([{
                                "Energy (keV)": g[0],
                                "Intensity (%)": g[1],
                                "Note": g[2],
                                "Detectable": "✓" if g[0]>=40 and g[1]>=0.5 else "weak",
                            } for g in full["gammas"]])
                            st.dataframe(gdf, use_container_width=True, hide_index=True)
                        else:
                            st.caption("No gamma lines in library for this nuclide.")

                        if full["chain"]:
                            with st.expander("Full decay chain"):
                                for m in full["chain"]:
                                    det   = m["detectable"]
                                    gstr  = "  ".join(f"{e:.1f}keV" for e,_,_ in m["strong_gammas"][:2])
                                    css_c = "chain-det" if det else "chain-invis"
                                    st.markdown(
                                        f'<div class="{css_c}" style="padding-left:{8+m["depth"]*12}px">'
                                        f'{"→ " if m["depth"]>0 else "⬤ "}{m["symbol"]} &nbsp;·&nbsp; '
                                        f't½={m["half_life"]} &nbsp;·&nbsp; {m["decay_mode"]} '
                                        f'{"·  "+gstr if gstr else ""}</div>',
                                        unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    #  TAB 7 — MY SPECTRA
    # ════════════════════════════════════════════════════════════════════════
    with tabs[6]:
        if not db:
            st.info("No spectra in database yet.")
        else:
            c1,c2,c3 = st.columns(3)
            all_min = sorted(set(e.get("mineral_type","") for e in db.values() if e.get("mineral_type")))
            all_sh  = sorted(set(e.get("shielding","")    for e in db.values() if e.get("shielding")))
            fm = c1.selectbox("Filter mineral", ["All"]+all_min, key="db_fmin")
            fs = c2.selectbox("Filter shielding", ["All"]+all_sh, key="db_fsh")
            so = c3.selectbox("Sort", ["Newest first","Longest measurement","Sample name"], key="db_sort")

            filtered = list(db.values())
            if fm != "All": filtered = [e for e in filtered if e.get("mineral_type")==fm]
            if fs != "All": filtered = [e for e in filtered if e.get("shielding")==fs]
            if so=="Newest first":          filtered.sort(key=lambda x:x.get("imported_at",""),reverse=True)
            elif so=="Longest measurement": filtered.sort(key=lambda x:x.get("meas_time_s",0),reverse=True)
            else:                           filtered.sort(key=lambda x:x.get("sample_name",""))

            st.caption(f"{len(filtered)} entries")
            for entry in filtered:
                lth = entry["meas_time_s"]//3600; ltm=(entry["meas_time_s"]%3600)//60
                c1,c2,c3 = st.columns([5,1,1])
                with c1:
                    st.markdown(f"""
                    <div style="background:#0f0f0c;border:1px solid #222018;border-radius:2px;padding:.6rem .9rem;margin:.2rem 0">
                      <div style="font-family:'Cormorant Garamond',serif;font-size:.95rem;font-weight:600;color:#f0e8d8">
                        {entry['sample_name']}</div>
                      <div style="font-family:'JetBrains Mono',monospace;font-size:.6rem;color:#4a4838;margin-top:.1rem">
                        {entry.get('mineral_type','—')} &nbsp;·&nbsp; {entry.get('distance_cm',0)}cm &nbsp;·&nbsp;
                        {entry.get('shielding','—')} &nbsp;·&nbsp; {lth}h{ltm}m &nbsp;·&nbsp; {entry.get('location','—')}
                      </div>
                    </div>""", unsafe_allow_html=True)
                with c2:
                    if st.button("Analyze", key=f"da_{entry['id']}"):
                        st.session_state["_pending_sel_id"] = entry["id"]
                        st.rerun()
                with c3:
                    if st.button("Delete", key=f"dd_{entry['id']}"):
                        del db[entry["id"]]; save_db(db); st.rerun()

    # ════════════════════════════════════════════════════════════════════════
    #  TAB 8 — COMPARE
    # ════════════════════════════════════════════════════════════════════════
    with tabs[7]:
        if len(db) < 2:
            st.info("Need at least 2 spectra to compare.")
        else:
            labels = {eid: f"{e['sample_name']} · {e.get('mineral_type','')} · {e.get('shielding','')} · {e['meas_time_s']}s"
                      for eid,e in db.items()}
            sel_ids  = st.multiselect("Select spectra (2–5)", list(db.keys()),
                                      format_func=lambda x:labels[x], max_selections=5,
                                      key="cmp_sel")
            norm_cps = st.checkbox("Normalize to CPS", True, key="cmp_norm")
            log_c    = st.checkbox("Log Y", True, key="cmp_log")

            if len(sel_ids)>=2:
                fig,ax = plt.subplots(figsize=(12,4))
                fig.patch.set_facecolor("#0e0e0c"); ax.set_facecolor("#0a0a08")
                palette = ["#d4a843","#7eb8d4","#90ee90","#e87070","#b87ed4"]
                for idx,eid in enumerate(sel_ids):
                    e  = db[eid]
                    c  = np.array(e["counts"],dtype=float)
                    en = np.array(e["energies"])
                    if norm_cps: c = c / max(e["meas_time_s"],1)
                    c = np.clip(c, 1e-12 if log_c else 0, None)
                    clr = palette[idx%len(palette)]
                    lbl = f"{e['sample_name']} · {e.get('shielding','—')} · {e.get('distance_cm',0)}cm"
                    ax.plot(en,c,color=clr,lw=0.9,label=lbl,alpha=0.9)
                if log_c: ax.set_yscale("log")
                ax.set_xlabel("Energy (keV)",color="#6b6350",fontsize=8)
                ax.set_ylabel("CPS" if norm_cps else "Counts",color="#6b6350",fontsize=8)
                ax.set_title("Spectrum Comparison",color="#d4a843",fontsize=9,pad=5)
                ax.tick_params(colors="#6b6350",labelsize=7)
                ax.legend(fontsize=6.5,facecolor="#1a1a16",labelcolor="#f0e8d8",framealpha=.8)
                for sp in ax.spines.values(): sp.set_color("#2a2820")
                ax.set_xlim(0)
                st.pyplot(fig, use_container_width=True); plt.close()
