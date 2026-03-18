"""
write_report_export.py
Run from your project directory:
    cd ~/Downloads/pycharm_project
    python write_report_export.py
This writes report_export.py directly — no downloading needed.
"""
from pathlib import Path

CODE = '''
from __future__ import annotations
import io
from datetime import datetime
import numpy as np
import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPORTLAB_OK = False
_NumberedCanvas = None  # defined inside try block below

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, PageBreak, Image as RLImage,
    )
    from reportlab.pdfgen import canvas as _rl_canvas

    C_GOLD  = colors.HexColor("#9a7820")
    C_DARK  = colors.HexColor("#1a1a16")
    C_MID   = colors.HexColor("#4a4840")
    C_RULE  = colors.HexColor("#c8b870")
    PAGE_W, PAGE_H = A4
    MARGIN = 2.0 * cm

    class _NumberedCanvas(_rl_canvas.Canvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._saved_page_states = []
        def showPage(self):
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()
        def save(self):
            n = len(self._saved_page_states)
            for state in self._saved_page_states:
                self.__dict__.update(state)
                self.setFont("Helvetica", 7)
                self.setFillColor(C_MID)
                self.drawRightString(PAGE_W - MARGIN, MARGIN * 0.6,
                                     f"GammaLab  ·  page {self._pageNumber} of {n}")
                self.drawString(MARGIN, MARGIN * 0.6,
                                f"Generated {datetime.now().strftime(\'%Y-%m-%d %H:%M\')}")
                super().showPage()
            super().save()

    REPORTLAB_OK = True

except ImportError:
    pass


def _build_styles():
    styles = {}
    styles["title"]   = ParagraphStyle("title",   fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=C_DARK, alignment=TA_CENTER, spaceAfter=4)
    styles["subtitle"]= ParagraphStyle("subtitle",fontName="Helvetica",      fontSize=10, leading=14, textColor=C_MID,  alignment=TA_CENTER, spaceAfter=2)
    styles["section"] = ParagraphStyle("section", fontName="Helvetica-Bold", fontSize=12, leading=16, textColor=C_GOLD, spaceBefore=14, spaceAfter=4)
    styles["body"]    = ParagraphStyle("body",     fontName="Helvetica",      fontSize=9,  leading=13, textColor=C_DARK)
    styles["caption"] = ParagraphStyle("caption",  fontName="Helvetica-Oblique", fontSize=8, leading=11, textColor=C_MID, spaceAfter=6)
    styles["label"]   = ParagraphStyle("label",    fontName="Helvetica-Bold", fontSize=8,  leading=11, textColor=C_MID)
    return styles


def _rule():
    return HRFlowable(width="100%", thickness=0.5, color=C_RULE, spaceAfter=6)


def _ts(has_header=True):
    cmds = [
        ("FONTNAME",      (0,0),(-1,-1),"Helvetica"),
        ("FONTSIZE",      (0,0),(-1,-1),8),
        ("LEADING",       (0,0),(-1,-1),11),
        ("TEXTCOLOR",     (0,0),(-1,-1),C_DARK),
        ("LEFTPADDING",   (0,0),(-1,-1),4),
        ("RIGHTPADDING",  (0,0),(-1,-1),4),
        ("TOPPADDING",    (0,0),(-1,-1),3),
        ("BOTTOMPADDING", (0,0),(-1,-1),3),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#f4f2ec")]),
        ("GRID",          (0,0),(-1,-1),0.3,colors.HexColor("#d0c8b0")),
    ]
    if has_header:
        cmds += [
            ("FONTNAME",  (0,0),(-1,0),"Helvetica-Bold"),
            ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#2a2820")),
            ("TEXTCOLOR", (0,0),(-1,0),colors.HexColor("#d4a843")),
        ]
    return TableStyle(cmds)


def _fig_to_img(fig, width_cm=15.0):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    buf.seek(0)
    plt.close(fig)
    return RLImage(buf, width=width_cm * cm)


def _spectrum_fig(entry, peaks=None):
    counts   = np.array(entry["counts"])
    energies = np.array(entry["energies"])
    lt       = max(entry["meas_time_s"], 1)
    fig, ax  = plt.subplots(figsize=(10, 3.2))
    fig.patch.set_facecolor("white"); ax.set_facecolor("#fafaf7")
    ax.fill_between(energies, counts/lt, alpha=0.15, color="#4a6a9a", step="mid")
    ax.plot(energies, counts/lt, color="#2a4a7a", lw=0.6)
    if peaks:
        for pk in peaks:
            ax.axvline(pk.get("energy_keV") or pk.get("det_keV", 0), color="#9a7820", lw=0.7, alpha=0.7)
    ax.set_yscale("log"); ax.set_xlabel("Energy (keV)", fontsize=8); ax.set_ylabel("CPS", fontsize=8)
    ax.set_title(f"{entry[\'sample_name\']}  ·  {lt:,.0f} s", fontsize=9)
    ax.tick_params(labelsize=7); ax.grid(True, alpha=0.25, lw=0.4)
    for sp in ax.spines.values(): sp.set_color("#ccccaa")
    fig.tight_layout(); return fig


def build_pdf(entry):
    buf = io.BytesIO()
    aw  = PAGE_W - 2*MARGIN
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN+0.6*cm,
        title=f"GammaLab — {entry.get(\'sample_name\',\'\')}", author="GammaLab")
    S = _build_styles(); story = []

    # Cover
    story += [Spacer(1,1.5*cm), Paragraph("GAMMA SPECTROSCOPY ANALYSIS REPORT", S["title"]),
              Paragraph("GammaLab  ·  Radiacode-103  ·  ENSDF", S["subtitle"]),
              Spacer(1,0.4*cm), _rule(), Spacer(1,0.3*cm)]
    meta = [["Sample name", entry.get("sample_name","—")],
            ["Sample type", entry.get("mineral_type","—")],
            ["Sample ID",   entry.get("id","—")],
            ["Live time",   f"{entry.get(\'meas_time_s\',0):,} s"],
            ["Date",        entry.get("date","—")],
            ["Location",    entry.get("location","—")],
            ["Operator",    entry.get("operator","—")],
            ["Notes",       entry.get("notes","—")],
            ["Report date", datetime.now().strftime("%Y-%m-%d %H:%M")]]
    t = Table(meta, colWidths=[4.5*cm, aw-4.5*cm])
    t.setStyle(TableStyle([("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),("FONTNAME",(1,0),(1,-1),"Helvetica"),
        ("FONTSIZE",(0,0),(-1,-1),9),("LEADING",(0,0),(-1,-1),13),
        ("TEXTCOLOR",(0,0),(0,-1),C_MID),("TEXTCOLOR",(1,0),(1,-1),C_DARK),
        ("LEFTPADDING",(0,0),(-1,-1),3),("RIGHTPADDING",(0,0),(-1,-1),3),
        ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.white,colors.HexColor("#f4f2ec")]),
        ("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#d0c8b0"))]))
    story.append(t)

    # Spectrum
    peaks = st.session_state.get("forensic_peaks") or st.session_state.get("lib_peaks_raw")
    story += [Spacer(1,0.3*cm), _rule(), Paragraph("Spectrum Overview", S["section"]), _rule()]
    total = int(np.array(entry["counts"]).sum())
    story.append(Paragraph(f"Total counts: <b>{total:,}</b>  ·  Live time: <b>{entry.get(\'meas_time_s\',0):,} s</b>  ·  Peaks: <b>{len(peaks) if peaks else 0}</b>", S["body"]))
    story += [Spacer(1,0.2*cm), _fig_to_img(_spectrum_fig(entry, peaks), aw/cm),
              Paragraph("Figure 1 — Full spectrum (log scale). Gold lines = detected peaks.", S["caption"])]

    # Peaks table
    if peaks:
        story += [PageBreak(), Paragraph("Detected Peaks", S["section"]), _rule()]
        rows = [["#","Energy (keV)","Channel","Counts"]]
        for i,pk in enumerate(peaks,1):
            rows.append([str(i), f"{pk.get(\'energy_keV\',0):.2f}", str(pk.get("channel","")), f"{pk.get(\'counts\',0):,.0f}"])
        t = Table(rows, colWidths=[1.2*cm,4*cm,4*cm,None]); t.setStyle(_ts()); story.append(t)

    # Forensic
    fr = st.session_state.get("forensic_report")
    if fr:
        story += [PageBreak(), Paragraph("Forensic Analysis", S["section"]), _rule()]
        story.append(Paragraph(f"<b>Classification:</b>  {getattr(fr,\'classification\',\'—\')}", S["body"]))
        if getattr(fr,"classification_reasoning",""):
            story.append(Paragraph(fr.classification_reasoning, S["body"]))
        isos = getattr(fr,"detected_isotopes",[])
        if isos:
            rows = [["Isotope","Confidence","Key lines (keV)","Category"]]
            for iso in isos:
                mm = getattr(iso,"matched",[]) or []
                rows.append([getattr(iso,"symbol","—"), f"{getattr(iso,\'confidence\',0)*100:.0f}%",
                              ", ".join(f"{m.get(\'lib_keV\',0):.1f}" for m in mm[:4]),
                              getattr(iso,"category","—")])
            t = Table(rows, colWidths=[3*cm,2.5*cm,8*cm,aw-13.5*cm]); t.setStyle(_ts()); story.append(t)
        for a in getattr(fr,"anomalies",[]):
            col = "red" if a.get("level")=="high" else "orange"
            story.append(Paragraph(f\'<font color="{col}"><b>[{a.get("level","").upper()}]</b></font>  {a.get("message","")}\', S["body"]))
        if getattr(fr,"provenance_narrative",""):
            story += [Spacer(1,0.3*cm), Paragraph("Provenance narrative", S["label"])]
            for para in fr.provenance_narrative.split("\\n\\n"):
                if para.strip(): story += [Paragraph(para.strip(), S["body"]), Spacer(1,0.1*cm)]

    # Peak fitting
    fit = st.session_state.get("fit_summary")
    if fit and getattr(fit,"fitted_peaks",None):
        story += [PageBreak(), Paragraph("Peak Fitting (Gaussian)", S["section"]), _rule()]
        story.append(Paragraph(f"Fitted: <b>{fit.n_peaks_fitted}</b>  Failed: <b>{fit.n_peaks_failed}</b>  Mean chi-sq: <b>{fit.mean_chi2}</b>", S["body"]))
        rows = [["Energy rough","Energy fitted","Net area","FWHM","Res %","chi-sq","OK"]]
        for fp in fit.fitted_peaks:
            rows.append([f"{fp.energy_keV_rough:.2f}",
                         f"{fp.energy_keV:.3f}" if fp.fit_ok else "—",
                         f"{fp.area_net:,.0f}" if fp.fit_ok else "—",
                         f"{fp.fwhm_keV:.3f}" if fp.fit_ok else "—",
                         f"{fp.resolution_pct:.3f}" if fp.fit_ok else "—",
                         f"{fp.chi2_reduced:.3f}" if fp.fit_ok else "—",
                         "OK" if fp.fit_ok else "fail"])
        t = Table(rows, colWidths=[aw/7]*7); t.setStyle(_ts()); story.append(t)

    # Activity
    ar = st.session_state.get("activity_report")
    if ar and getattr(ar,"results",None):
        story += [PageBreak(), Paragraph("Activity Calculations", S["section"]), _rule()]
        story.append(Paragraph(f"Total: <b>{getattr(ar,\'total_activity_bq\',0):.3g} Bq</b>  Mass: <b>{getattr(ar,\'sample_mass_g\',0):.1f} g</b>", S["body"]))
        rows = [["Isotope","Energy (keV)","Activity (Bq)","±","Efficiency","chi-sq"]]
        for r in ar.results:
            rows.append([r.isotope,f"{r.energy_keV:.1f}",f"{r.activity_bq:.3g}",f"{r.activity_unc_bq:.3g}",f"{r.efficiency:.3e}",f"{r.fit_chi2:.3f}"])
        t = Table(rows, colWidths=[3*cm,2.5*cm,3*cm,2.5*cm,3*cm,aw-14*cm]); t.setStyle(_ts()); story.append(t)

    # MDA
    mda = st.session_state.get("mda_results")
    if mda:
        story += [Paragraph("Minimum Detectable Activity", S["section"]), _rule()]
        rows = [["Isotope","Energy (keV)","Background","Lc","Ld","MDA (Bq)","Efficiency"]]
        for r in mda:
            rows.append([r.isotope,f"{r.energy_keV:.1f}",f"{r.background_counts:.1f}",f"{r.lc_counts:.2f}",f"{r.ld_counts:.2f}",f"{r.mda_bq:.4g}",f"{r.efficiency:.3e}"])
        t = Table(rows, colWidths=[aw/7]*7); t.setStyle(_ts()); story.append(t)

    # Dose
    dr = st.session_state.get("dose_result")
    if dr:
        story += [Paragraph("Dose Rate", S["section"]), _rule()]
        story.append(Paragraph(f"H*(10) at {dr.distance_cm:.0f} cm: <b>{dr.total_dose_rate_usv_h:.4g} µSv/h</b>  ·  <b>{dr.total_dose_rate_mrem_h:.4g} mrem/h</b>", S["body"]))
        if getattr(dr,"contributions",[]):
            rows = [["Isotope","Energy (keV)","Activity (Bq)","H*(10) µSv/h","% total"]]
            for c in dr.contributions:
                rows.append([c["isotope"],f"{c[\'energy_keV\']:.1f}",f"{c[\'activity_bq\']:.3g}",f"{c[\'dose_usv_h\']:.4g}",f"{c[\'pct_of_total\']:.1f}%"])
            t = Table(rows, colWidths=[3*cm,3*cm,3*cm,3.5*cm,aw-12.5*cm]); t.setStyle(_ts()); story.append(t)

    doc.build(story, canvasmaker=_NumberedCanvas)
    return buf.getvalue()


def _slabel(text):
    st.markdown(f\'<div style="font-family:monospace;font-size:.68rem;color:#d4a843;letter-spacing:.15em;text-transform:uppercase;margin:1rem 0 .3rem">{text}</div>\', unsafe_allow_html=True)

def _warn(text):
    st.markdown(f\'<div style="font-family:monospace;font-size:.72rem;color:#e87050;background:#1a0a0a;border:1px solid #4a1a1a;border-radius:2px;padding:.3rem .7rem;margin:.3rem 0">⚠ {text}</div>\', unsafe_allow_html=True)

def _ok(text):
    st.markdown(f\'<div style="font-family:monospace;font-size:.72rem;color:#27ae60;background:#0a1f0e;border:1px solid #1a4a22;border-radius:2px;padding:.3rem .7rem;display:inline-block;margin:.3rem 0">✓ {text}</div>\', unsafe_allow_html=True)


def render_export_tab(db):
    st.markdown(\'<div style="font-family:Georgia,serif;font-size:1.6rem;font-weight:700;color:#f0e8d8">Export PDF Report</div>\', unsafe_allow_html=True)
    st.caption("Generates a multi-page PDF with all available analysis results")

    if not REPORTLAB_OK:
        _warn("reportlab not installed.")
        st.code("pip install reportlab --break-system-packages")
        return
    if not db:
        st.info("No spectra imported — go to Import first.")
        return

    labels = {eid: f"{e[\'sample_name\']}  ·  {e.get(\'mineral_type\',\'\')}  ·  {e[\'meas_time_s\']:,}s" for eid,e in db.items()}
    eid   = st.selectbox("Spectrum to export", list(db.keys()), format_func=lambda x: labels[x], key="exp_sel")
    entry = db[eid]

    _slabel("Available data")
    checks = {
        "Spectrum + peaks":  bool(st.session_state.get("forensic_peaks") or st.session_state.get("lib_peaks_raw")),
        "Forensic analysis": bool(st.session_state.get("forensic_report")),
        "Peak fitting":      bool(st.session_state.get("fit_summary")),
        "Activity":          bool(st.session_state.get("activity_report")),
        "MDA":               bool(st.session_state.get("mda_results")),
        "Dose rate":         bool(st.session_state.get("dose_result")),
    }
    for label, ok in checks.items():
        c = "#27ae60" if ok else "#3a3020"
        st.markdown(f\'<div style="font-family:monospace;font-size:.75rem;color:{c};padding:.1rem 0">{"✓" if ok else "○"}  {label}</div>\', unsafe_allow_html=True)

    _slabel("Optional metadata")
    c1, c2 = st.columns(2)
    entry["operator"] = c1.text_input("Operator", value=entry.get("operator",""), key="exp_op")
    entry["location"]  = c2.text_input("Location", value=entry.get("location",""),  key="exp_loc")
    entry["notes"]     = st.text_area("Notes",     value=entry.get("notes",""), height=60, key="exp_notes")
    st.markdown("---")

    if st.button("📄  Generate PDF", type="primary", key="exp_run"):
        with st.spinner("Building PDF…"):
            try:
                pdf_bytes = build_pdf(entry)
                safe  = "".join(c if c.isalnum() or c in "-_ " else "_" for c in entry.get("sample_name","report")).replace(" ","_")
                fname = f"GammaLab_{safe}_{datetime.now().strftime(\'%Y%m%d_%H%M\')}.pdf"
                _ok(f"PDF ready — {len(pdf_bytes)//1024:,} KB")
                st.download_button("⬇  Download PDF", data=pdf_bytes, file_name=fname, mime="application/pdf", key="exp_dl")
            except Exception as e:
                _warn(f"PDF generation failed: {e}")
                st.exception(e)
'''

out = Path("report_export.py")
out.write_text(CODE.lstrip(), encoding="utf-8")
print(f"Written: {out.resolve()}  ({out.stat().st_size:,} bytes)")

import py_compile, tempfile, shutil
tmp = Path(tempfile.mktemp(suffix=".py"))
shutil.copy(out, tmp)
try:
    py_compile.compile(str(tmp), doraise=True)
    print("Syntax check: PASSED")
except py_compile.PyCompileError as e:
    print(f"Syntax check: FAILED — {e}")
finally:
    tmp.unlink(missing_ok=True)
