"""
forensic_tab.py  —  Full forensic analysis UI tab
───────────────────────────────────────────────────
Renders the upgraded ☣ Forensic Analysis page using forensic_engine.py.
"""

from __future__ import annotations
import streamlit as st
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from spectrum_db    import find_spectrum_peaks, load_db
from forensic_engine import (
    full_forensic_analysis, ForensicReport,
    IsotopeMatch, ChainReconstruction, RatioResult,
    NATURAL_ISOTOPES, FISSION_PRODUCTS, MEDICAL_ISOTOPES,
    INDUSTRIAL_ISOTOPES, ACTIVATION_ISOTOPES, WEAPONS_RELEVANT,
)

BG = "#0e0e0c"

# ── Category colours ──────────────────────────────────────────────────────────
CAT_COLORS = {
    "natural":     "#6b8e6b",
    "fission":     "#c0392b",
    "activation":  "#e67e22",
    "medical":     "#2980b9",
    "industrial":  "#8e44ad",
    "special":     "#e74c3c",
    "short-lived": "#7f8c8d",
    "unknown":     "#4a4a40",
}

LEVEL_COLORS = {
    "high":   "#e74c3c",
    "medium": "#e67e22",
    "low":    "#f1c40f",
}


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _slabel(text: str):
    st.markdown(
        f'<div style="font-family:\'Courier New\',monospace;font-size:.65rem;'
        f'color:#d4a843;letter-spacing:.18em;text-transform:uppercase;'
        f'margin:1.2rem 0 .35rem;border-bottom:1px solid #2a2820;padding-bottom:.2rem">'
        f'{text}</div>', unsafe_allow_html=True)


def _badge(text: str, color: str = "#d4a843", bg: str = "#1a1a10"):
    st.markdown(
        f'<span style="font-family:\'Courier New\',monospace;font-size:.65rem;'
        f'color:{color};background:{bg};border:1px solid {color}44;'
        f'border-radius:2px;padding:.1rem .4rem;margin:.1rem .1rem;'
        f'display:inline-block">{text}</span>', unsafe_allow_html=True)


def _card(title: str, body: str, border_color: str = "#2a2820"):
    st.markdown(
        f'<div style="background:#0c0c0a;border:1px solid {border_color};'
        f'border-radius:3px;padding:.7rem 1rem;margin:.4rem 0">'
        f'<div style="font-family:Georgia,serif;font-size:.85rem;font-weight:700;'
        f'color:#d4a843;margin-bottom:.35rem">{title}</div>'
        f'<div style="font-family:\'Libre Baskerville\',serif;font-size:.78rem;'
        f'color:#9a9080;line-height:1.55">{body}</div></div>',
        unsafe_allow_html=True)


def _anomaly_card(anom: dict):
    color = LEVEL_COLORS.get(anom["level"], "#d4a843")
    st.markdown(
        f'<div style="background:#0e0a08;border-left:3px solid {color};'
        f'border:1px solid {color}55;border-radius:2px;padding:.6rem 1rem;margin:.3rem 0">'
        f'<div style="font-family:\'Courier New\',monospace;font-size:.7rem;'
        f'color:{color};font-weight:700;letter-spacing:.1em">'
        f'[{anom["level"].upper()}] {anom["title"]}</div>'
        f'<div style="font-family:\'Libre Baskerville\',serif;font-size:.75rem;'
        f'color:#7a7060;margin-top:.3rem;line-height:1.5">{anom["detail"]}</div>'
        f'</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN RENDER
# ══════════════════════════════════════════════════════════════════════════════

def render_forensic_tab():
    st.markdown(
        '<div style="font-family:Georgia,serif;font-size:1.65rem;font-weight:700;'
        'color:#f0e8d8;letter-spacing:.02em">☣ Forensic Analysis</div>',
        unsafe_allow_html=True)
    st.caption("Full ENSDF-backed identification · Decay chain reconstruction · "
               "Isotope ratios · Enrichment · Classification · Provenance narrative")

    db = load_db()
    if not db:
        st.info("No spectra imported. Go to 📥 Import first.")
        return

    # ── Spectrum selector ──────────────────────────────────────────────────────
    labels = {eid: f"{e['sample_name']}  ·  {e.get('mineral_type','')}  ·  {e['meas_time_s']:,} s"
              for eid, e in db.items()}
    eid = st.selectbox("Spectrum", list(db.keys()),
                        format_func=lambda x: labels[x], key="for_sel")
    if not eid:
        return
    entry    = db[eid]
    counts   = np.array(entry["counts"])
    energies = np.array(entry["energies"])
    lt       = float(entry["meas_time_s"])

    # ── Parameters ────────────────────────────────────────────────────────────
    with st.expander("⚙  Analysis parameters", expanded=False):
        c1, c2, c3 = st.columns(3)
        prom      = c1.slider("Peak prominence %",  0.3, 8.0, 1.5, 0.2, key="for_prom") / 100
        tol       = c2.slider("Match tolerance keV", 3.0, 20.0, 10.0, 0.5, key="for_tol")
        max_match = c3.slider("Max isotope results",  5, 50, 25, 5, key="for_maxm")
        mine      = c1.slider("Min energy keV",       10.0, 100.0, 40.0, 5.0, key="for_mine")

    run = st.button("▶  Run full forensic analysis", type="primary", key="for_run")

    if run:
        peaks = find_spectrum_peaks(counts, energies,
                                     prominence_pct=prom, min_energy=mine)
        if not peaks:
            st.warning("No peaks detected — try lowering the prominence threshold.")
            return
        with st.spinner(f"Analysing {len(peaks)} peaks against ENSDF database…"):
            report = full_forensic_analysis(
                detected_peaks  = peaks,
                live_time_s     = lt,
                tolerance_kev   = tol,
                max_matches     = max_match,
            )
        st.session_state["forensic_report"] = report
        st.session_state["forensic_peaks"]  = peaks
        st.session_state["forensic_entry"]  = entry
        # Also cache matches for activity tab
        st.session_state["matches_cache"] = [
            {"isotope": m.symbol,
             "matched": m.matched,
             "confidence": m.confidence}
            for m in report.detected_isotopes
        ]

    report: ForensicReport | None = st.session_state.get("forensic_report")
    if not report:
        return

    peaks = st.session_state.get("forensic_peaks", [])
    entry = st.session_state.get("forensic_entry", entry)

    # ══════════════════════════════════════════════════════════════════════════
    #  CLASSIFICATION BANNER
    # ══════════════════════════════════════════════════════════════════════════

    cls_color = {
        "NATURAL BACKGROUND":                "#27ae60",
        "NORM — NATURALLY OCCURRING RADIOACTIVE MATERIAL": "#f39c12",
        "FISSION PRODUCTS":                  "#e74c3c",
        "ACTIVATION PRODUCTS":               "#e67e22",
        "MEDICAL / RADIOPHARMACEUTICAL":     "#2980b9",
        "INDUSTRIAL / SEALED SOURCE":        "#8e44ad",
        "MIXED — NATURAL + FISSION":         "#c0392b",
        "SPECIAL NUCLEAR MATERIAL":          "#e74c3c",
    }.get(report.classification, "#d4a843")

    st.markdown(
        f'<div style="background:#0c0c0a;border:2px solid {cls_color};'
        f'border-radius:3px;padding:.8rem 1.2rem;margin:.5rem 0 1rem">'
        f'<div style="font-family:\'Courier New\',monospace;font-size:1rem;'
        f'font-weight:700;color:{cls_color};letter-spacing:.15em">'
        f'{report.classification}</div>'
        f'<div style="font-family:\'Libre Baskerville\',serif;font-size:.78rem;'
        f'color:#7a7060;margin-top:.4rem">{report.classification_reasoning}</div>'
        f'<div style="font-family:\'Courier New\',monospace;font-size:.62rem;'
        f'color:{cls_color}88;margin-top:.3rem">'
        f'Overall confidence: {report.confidence_overall*100:.0f}%  ·  '
        f'{len(report.detected_isotopes)} isotopes matched  ·  '
        f'{len(peaks)} peaks detected</div>'
        f'</div>', unsafe_allow_html=True)

    # Anomaly banners at top
    if report.anomalies:
        high = [a for a in report.anomalies if a["level"] == "high"]
        for a in high:
            _anomaly_card(a)

    # ══════════════════════════════════════════════════════════════════════════
    #  TABS
    # ══════════════════════════════════════════════════════════════════════════
    tabs = st.tabs([
        "🔬 Identified Isotopes",
        "⛓ Decay Chains",
        "⚖ Ratio Analysis",
        "⚛ Enrichment",
        "📖 Narrative",
        "⚠ Anomalies",
        "📊 Spectrum",
    ])

    # ── TAB 1: Identified isotopes ─────────────────────────────────────────────
    with tabs[0]:
        _render_isotopes_tab(report)

    # ── TAB 2: Decay chains ────────────────────────────────────────────────────
    with tabs[1]:
        _render_chains_tab(report)

    # ── TAB 3: Ratio analysis ──────────────────────────────────────────────────
    with tabs[2]:
        _render_ratios_tab(report)

    # ── TAB 4: Enrichment ─────────────────────────────────────────────────────
    with tabs[3]:
        _render_enrichment_tab(report)

    # ── TAB 5: Narrative ──────────────────────────────────────────────────────
    with tabs[4]:
        _render_narrative_tab(report)

    # ── TAB 6: Anomalies ──────────────────────────────────────────────────────
    with tabs[5]:
        _render_anomalies_tab(report)

    # ── TAB 7: Spectrum ────────────────────────────────────────────────────────
    with tabs[6]:
        _render_spectrum_tab(entry, peaks, report, counts, energies, lt)


# ══════════════════════════════════════════════════════════════════════════════
#  TAB RENDERERS
# ══════════════════════════════════════════════════════════════════════════════

def _render_isotopes_tab(report: ForensicReport):
    _slabel(f"{len(report.detected_isotopes)} isotopes matched — ranked by confidence")

    good = [m for m in report.detected_isotopes if m.confidence > 0.15]
    if not good:
        st.info("No isotopes matched above threshold.")
        return

    # Summary badges by category
    cats: dict[str, list] = {}
    for m in good:
        cats.setdefault(m.category, []).append(m.symbol)
    for cat, syms in cats.items():
        col = CAT_COLORS.get(cat, "#d4a843")
        _badge(f"{cat.upper()}: {', '.join(syms)}", color=col)

    st.markdown("")

    # Full table
    rows = []
    for m in good:
        rows.append({
            "Isotope":      m.symbol,
            "Confidence":   f"{m.pct:.1f}%",
            "Matched lines":f"{m.n_matched}/{m.n_total}",
            "Half-life":    m.half_life,
            "Category":     m.category,
            "Top lines (keV)": "  ".join(f"{e:.1f}" for e in m.strong_lines[:3]),
            "Detectable":   "✓" if m.detectable else f"✗ {m.detect_reason[:30]}",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Confidence bar chart
    fig, ax = plt.subplots(figsize=(9, max(3, len(good) * 0.35)))
    fig.patch.set_facecolor(BG); ax.set_facecolor("#0a0a08")
    syms  = [m.symbol  for m in reversed(good)]
    confs = [m.pct     for m in reversed(good)]
    bcolors = [CAT_COLORS.get(m.category, "#d4a843") for m in reversed(good)]
    bars = ax.barh(syms, confs, color=bcolors, height=0.65, alpha=0.85)
    ax.set_xlabel("Confidence %", color="#6b6350", fontsize=8)
    ax.set_xlim(0, 105)
    ax.axvline(30, color="#3a3020", lw=0.6, ls="--")
    ax.axvline(60, color="#3a3020", lw=0.6, ls="--")
    for bar, val in zip(bars, confs):
        ax.text(val + 1, bar.get_y() + bar.get_height()/2,
                f"{val:.0f}%", va="center", fontsize=6, color="#6b6350")
    ax.tick_params(colors="#6b6350", labelsize=7)
    for sp in ax.spines.values(): sp.set_color("#2a2820")
    # Legend
    legend_patches = [mpatches.Patch(color=v, label=k)
                      for k, v in CAT_COLORS.items()
                      if any(m.category == k for m in good)]
    ax.legend(handles=legend_patches, fontsize=6,
               facecolor="#1a1a16", labelcolor="#d4a843", loc="lower right")
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True); plt.close()

    # Per-isotope reasoning
    _slabel("Confidence reasoning")
    for m in good[:15]:
        with st.expander(f"{m.symbol}  —  {m.pct:.1f}%  ·  {m.category}  ·  {m.half_life}",
                          expanded=False):
            st.markdown(
                f'<div style="font-family:\'Libre Baskerville\',serif;font-size:.76rem;'
                f'color:#9a9080;line-height:1.55">{m.reasoning}</div>',
                unsafe_allow_html=True)
            if m.matched:
                df_m = pd.DataFrame([{
                    "Library keV": x["lib_keV"],
                    "Detected keV": x["det_keV"],
                    "Δ keV": x["delta_keV"],
                    "Intensity %": x["intensity"],
                } for x in m.matched])
                st.dataframe(df_m, use_container_width=True, hide_index=True)
            if m.unmatched:
                strong_miss = [u for u in m.unmatched if u["intensity"] > 5]
                if strong_miss:
                    st.caption(f"Strong unmatched lines: " +
                               ", ".join(f"{u['lib_keV']:.1f} keV ({u['intensity']:.0f}%)"
                                         for u in strong_miss[:5]))


def _render_chains_tab(report: ForensicReport):
    _slabel("Decay chain reconstructions")

    if not report.chain_reconstructions:
        st.info("No decay chains reconstructed. Run analysis with higher-confidence matches.")
        return

    for chain in report.chain_reconstructions:
        pct_color = ("#27ae60" if chain.completeness_pct >= 70 else
                     "#f39c12" if chain.completeness_pct >= 40 else "#e74c3c")
        with st.expander(
            f"{chain.root}  —  {chain.completeness_pct:.0f}% complete  "
            f"({chain.n_detected}/{chain.n_detectable} detectable members)",
            expanded=chain.completeness_pct > 50
        ):
            st.markdown(
                f'<div style="font-family:\'Libre Baskerville\',serif;font-size:.78rem;'
                f'color:#9a9080;line-height:1.55;margin-bottom:.5rem">'
                f'{chain.interpretation}</div>', unsafe_allow_html=True)

            # Chain visualisation — horizontal node graph
            _draw_chain(chain)

            # Table
            if chain.nodes:
                rows = []
                for n in chain.nodes:
                    rows.append({
                        "Depth":      n.depth,
                        "Isotope":    n.symbol,
                        "Half-life":  n.half_life,
                        "Decay mode": n.decay_mode,
                        "Detectable": "✓" if n.detectable else "—",
                        "Detected":   "✓ FOUND" if n.detected else ("— absent" if n.detectable else "invisible"),
                        "Top γ lines": "  ".join(f"{e:.1f}" for e,_ in n.strong_gammas[:3]),
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            if chain.missing:
                st.caption(f"Missing detectable members: {', '.join(chain.missing)}")
            if chain.invisible:
                st.caption(f"Invisible (alpha/β-only) members: {', '.join(chain.invisible[:8])}")


def _draw_chain(chain: ChainReconstruction):
    """Draw a vertical chain diagram."""
    nodes = chain.nodes
    if not nodes:
        return

    height = max(3, len(nodes) * 0.55)
    fig, ax = plt.subplots(figsize=(7, height))
    fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
    ax.axis("off")
    ax.set_xlim(0, 10); ax.set_ylim(0, len(nodes))

    for i, node in enumerate(nodes):
        y = len(nodes) - i - 0.5
        if node.detected:
            fc, ec, tc = "#0a2a0a", "#27ae60", "#27ae60"
        elif node.detectable:
            fc, ec, tc = "#1a1008", "#d4a843", "#d4a843"
        else:
            fc, ec, tc = "#0a0a0a", "#3a3020", "#3a3020"

        ax.add_patch(mpatches.FancyBboxPatch(
            (1, y - 0.22), 5.5, 0.44,
            boxstyle="round,pad=0.04", facecolor=fc, edgecolor=ec, lw=0.8))
        ax.text(3.75, y, f"{node.symbol}  {node.half_life}  {node.decay_mode}",
                va="center", ha="center", fontsize=6.5, color=tc,
                fontfamily="monospace")
        if node.detected:
            ax.text(7.2, y, "✓ DETECTED", va="center", fontsize=6,
                    color="#27ae60", fontfamily="monospace")

        # Arrow to next
        if i < len(nodes) - 1:
            ax.annotate("", xy=(3.75, y - 0.22),
                        xytext=(3.75, y - 0.5),
                        arrowprops=dict(arrowstyle="->", color="#3a3820", lw=0.7))

    fig.tight_layout(pad=0.2)
    st.pyplot(fig, use_container_width=True); plt.close()


def _render_ratios_tab(report: ForensicReport):
    _slabel("Isotope ratio analysis")

    if not report.ratio_results:
        st.info("No equilibrium pairs detected — need both parent and daughter identified.")
        return

    rows = []
    for r in report.ratio_results:
        status_icon = {"equilibrium": "✓", "disrupted": "~", "broken": "✗",
                       "informational": "ℹ"}.get(r.status, "?")
        rows.append({
            "Parent":       r.parent,
            "Daughter":     r.daughter,
            "Observed":     f"{r.observed_ratio:.4f}",
            "Expected":     f"{r.expected_ratio:.4f}" if r.expected_ratio else "—",
            "Deviation %":  f"{r.deviation_pct:.1f}%" if r.expected_ratio else "—",
            "Status":       f"{status_icon} {r.status}",
            "Age estimate": f"{r.age_estimate_y:.1f} y" if r.age_estimate_y else "—",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    _slabel("Interpretations")
    for r in report.ratio_results:
        color = ("#27ae60" if r.status == "equilibrium" else
                 "#e67e22" if r.status == "disrupted" else
                 "#e74c3c" if r.status == "broken" else "#7a7060")
        st.markdown(
            f'<div style="font-family:\'Libre Baskerville\',serif;font-size:.76rem;'
            f'color:{color};line-height:1.5;border-left:2px solid {color}44;'
            f'padding:.3rem .7rem;margin:.25rem 0">'
            f'<strong>{r.parent} → {r.daughter}:</strong> {r.interpretation}</div>',
            unsafe_allow_html=True)

    if report.age_estimates:
        _slabel("Age constraints")
        for ae in report.age_estimates:
            if ae.get("value_y"):
                st.markdown(
                    f'<div style="font-family:\'Courier New\',monospace;font-size:.72rem;'
                    f'color:#d4a843;padding:.3rem .7rem">'
                    f'{ae["method"]}: <strong>{ae["value_y"]:.1f} years</strong><br>'
                    f'<span style="color:#6a6050;font-size:.68rem">{ae["basis"]}</span></div>',
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    f'<div style="font-family:\'Libre Baskerville\',serif;font-size:.74rem;'
                    f'color:#6a6050;padding:.2rem .7rem">{ae["method"]}: {ae["basis"]}</div>',
                    unsafe_allow_html=True)


def _render_enrichment_tab(report: ForensicReport):
    _slabel("Enrichment & processing indicators")

    # U enrichment level
    if report.u_enrichment_level:
        ul     = report.u_enrichment_level
        color  = ("#e74c3c" if "HEU" in ul else
                  "#e67e22" if "LEU" in ul else
                  "#27ae60" if ul == "natural" else "#d4a843")
        st.markdown(
            f'<div style="font-family:\'Courier New\',monospace;font-size:.85rem;'
            f'font-weight:700;color:{color};border:1px solid {color}55;'
            f'background:#0c0c0a;border-radius:2px;padding:.5rem 1rem;margin:.5rem 0">'
            f'URANIUM ENRICHMENT LEVEL: {ul.upper()}</div>',
            unsafe_allow_html=True)

    # Verdict
    _card("Enrichment verdict", report.enrichment_verdict,
          border_color="#d4a843" if report.enrichment_flags else "#2a2820")

    # Flags
    if report.enrichment_flags:
        _slabel(f"{len(report.enrichment_flags)} indicator(s) detected")
        for flag in report.enrichment_flags:
            color = "#e74c3c" if "🚨" in flag else "#e67e22" if "⚠" in flag else "#d4a843"
            st.markdown(
                f'<div style="font-family:\'Libre Baskerville\',serif;font-size:.77rem;'
                f'color:{color};border-left:2px solid {color};padding:.35rem .8rem;'
                f'margin:.2rem 0">{flag}</div>', unsafe_allow_html=True)
    else:
        st.success("No enrichment or processing anomalies detected.")

    # Processing history
    if report.processing_flags:
        _slabel("Processing history inference")
        for flag in report.processing_flags:
            st.markdown(
                f'<div style="font-family:\'Libre Baskerville\',serif;font-size:.77rem;'
                f'color:#9a9080;border-left:2px solid #3a3020;padding:.3rem .8rem;'
                f'margin:.2rem 0">{flag}</div>', unsafe_allow_html=True)

    # Classification
    _slabel("Material classification")
    good = [m for m in report.detected_isotopes if m.confidence > 0.2]
    if good:
        cats: dict[str, list] = {}
        for m in good:
            cats.setdefault(m.category, []).append(m.symbol)

        fig, ax = plt.subplots(figsize=(5, 3))
        fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
        labels = list(cats.keys())
        sizes  = [len(v) for v in cats.values()]
        colors = [CAT_COLORS.get(k, "#4a4a40") for k in labels]
        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, colors=colors,
            autopct="%1.0f%%", startangle=90,
            textprops={"color": "#9a9080", "fontsize": 7},
            pctdistance=0.75,
        )
        for at in autotexts:
            at.set_color("#d4a843"); at.set_fontsize(7)
        ax.set_title("Isotope categories", color="#d4a843", fontsize=8, pad=10)
        fig.tight_layout()
        st.pyplot(fig, use_container_width=True); plt.close()


def _render_narrative_tab(report: ForensicReport):
    _slabel("Provenance narrative")
    paras = report.provenance_narrative.split("\n\n")
    for para in paras:
        if para.startswith("SAMPLE CLASSIFICATION"):
            lines = para.split("\n")
            st.markdown(
                f'<div style="font-family:\'Courier New\',monospace;font-size:.72rem;'
                f'font-weight:700;color:#d4a843;margin:.5rem 0 .2rem">'
                f'{lines[0]}</div>'
                f'<div style="font-family:\'Libre Baskerville\',serif;font-size:.8rem;'
                f'color:#9a9080;line-height:1.6">{" ".join(lines[1:])}</div>',
                unsafe_allow_html=True)
        elif para.startswith("ANOMALY") or para.startswith("ENRICHMENT"):
            color = "#e74c3c" if "high" in para.lower() or "HEU" in para else "#e67e22"
            st.markdown(
                f'<div style="font-family:\'Libre Baskerville\',serif;font-size:.78rem;'
                f'color:{color};border-left:3px solid {color};padding:.4rem .8rem;'
                f'margin:.3rem 0;line-height:1.55">{para}</div>',
                unsafe_allow_html=True)
        elif para.startswith("PROCESSING"):
            st.markdown(
                f'<div style="font-family:\'Libre Baskerville\',serif;font-size:.78rem;'
                f'color:#8e44ad;border-left:3px solid #8e44ad44;padding:.4rem .8rem;'
                f'margin:.3rem 0;line-height:1.55">{para}</div>',
                unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div style="font-family:\'Libre Baskerville\',serif;font-size:.8rem;'
                f'color:#8a8070;line-height:1.65;padding:.2rem 0">{para}</div>',
                unsafe_allow_html=True)

    # Export narrative as text
    if st.button("📋  Copy narrative to clipboard", key="for_copy"):
        st.code(report.provenance_narrative, language=None)


def _render_anomalies_tab(report: ForensicReport):
    _slabel(f"{len(report.anomalies)} anomalies detected")

    if not report.anomalies:
        st.success("No anomalies detected — spectrum is consistent with stated classification.")
        return

    for anom in report.anomalies:
        _anomaly_card(anom)


def _render_spectrum_tab(entry, peaks, report: ForensicReport,
                          counts, energies, lt):
    _slabel("Annotated spectrum")

    good_matches = [m for m in report.detected_isotopes if m.confidence > 0.25]
    log_y = st.checkbox("Log Y axis", True, key="for_logy")

    cps = counts / max(lt, 1)
    fig, ax = plt.subplots(figsize=(12, 4.5))
    fig.patch.set_facecolor(BG); ax.set_facecolor("#0a0a08")

    ax.plot(energies, cps, color="#6b6350", lw=0.5, alpha=0.8)
    ax.fill_between(energies, cps, alpha=0.08, color="#d4a843")

    # Annotate peaks with isotope labels
    labeled: set[str] = set()
    for pk in peaks:
        e = pk["energy_keV"]
        c = pk["counts"] / max(lt, 1)

        # Find best matching isotope for this peak
        best_iso  = None
        best_conf = 0.0
        for m in good_matches:
            for line in m.matched:
                if abs(line.get("det_keV", 0) - e) < 2:
                    if m.confidence > best_conf:
                        best_conf = m.confidence
                        best_iso  = m
                    break

        if best_iso:
            cat_col = CAT_COLORS.get(best_iso.category, "#d4a843")
            ax.axvline(e, color=cat_col, lw=0.7, alpha=0.5)
            if best_iso.symbol not in labeled:
                ax.text(e, c * 1.15, best_iso.symbol,
                        rotation=65, fontsize=5.5, color=cat_col,
                        va="bottom", ha="center",
                        fontfamily="monospace")
                labeled.add(best_iso.symbol)
        else:
            ax.axvline(e, color="#3a3820", lw=0.5, alpha=0.4)

    if log_y:
        ax.set_yscale("log")
    ax.set_xlabel("Energy (keV)", color="#6b6350", fontsize=8)
    ax.set_ylabel("CPS",          color="#6b6350", fontsize=8)
    ax.set_title(f"{entry['sample_name']}  ·  {lt:.0f}s live  ·  "
                  f"{len(good_matches)} isotopes annotated",
                  color="#d4a843", fontsize=8)
    ax.tick_params(colors="#6b6350", labelsize=7)
    ax.set_xlim(0, energies.max())
    for sp in ax.spines.values(): sp.set_color("#2a2820")

    # Category legend
    legend_patches = [mpatches.Patch(color=v, label=k.capitalize())
                      for k, v in CAT_COLORS.items()
                      if any(m.category == k for m in good_matches)]
    if legend_patches:
        ax.legend(handles=legend_patches, fontsize=6,
                   facecolor="#1a1a16", labelcolor="#d4a843",
                   loc="upper right", ncol=2)

    fig.tight_layout()
    st.pyplot(fig, use_container_width=True); plt.close()
