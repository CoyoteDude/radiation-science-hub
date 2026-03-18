"""
forensic_engine.py  —  Full-spectrum forensic analysis engine
──────────────────────────────────────────────────────────────
Replaces / extends inference_engine.py with:

  1. ENSDF-backed peak matching  — uses full 3,400-isotope gamma database
  2. Dynamic decay chain reconstruction — radioactivedecay for any nuclide
  3. Isotope ratio analysis      — secular equilibrium across any chain
  4. Enrichment indicators       — U/Th/Pu processing flags
  5. Medical/industrial/weapons classification
  6. Provenance narrative        — natural / NORM / anthropogenic / special
  7. Age estimation              — from daughter/parent activity ratios
  8. Detailed per-isotope confidence reasoning
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Optional

# ── Local imports ──────────────────────────────────────────────────────────────
from ensdf_parser import get_gamma_db, search_by_energy
from isotope_db   import (
    RAD_AVAILABLE, YEAR_S, INF,
    is_detectable, get_half_life, get_daughters, build_chain,
)

if RAD_AVAILABLE:
    import radioactivedecay as rd


# ══════════════════════════════════════════════════════════════════════════════
#  CONSTANTS & CLASSIFICATION TABLES
# ══════════════════════════════════════════════════════════════════════════════

# Natural / NORM isotopes (primordial + cosmogenic + decay products)
NATURAL_ISOTOPES = {
    "K-40","U-238","U-235","U-234","Th-232","Th-228","Th-234",
    "Ra-226","Ra-224","Ra-228","Ra-223",
    "Rn-222","Rn-220","Rn-219",
    "Pb-210","Pb-212","Pb-214","Pb-211",
    "Bi-210","Bi-212","Bi-214","Bi-211",
    "Po-210","Po-212","Po-214","Po-216","Po-218",
    "Tl-208","Tl-207","Tl-210",
    "Pa-234m","Pa-231","Ac-228","Ac-227",
    "Fr-223","At-219",
    "Be-7","Be-10","C-14","Na-22","Al-26","Cl-36","Ca-41","Mn-53",
}

# Reactor / activation products
ACTIVATION_ISOTOPES = {
    "Co-57","Co-58","Co-60","Mn-54","Fe-59","Zn-65","Cr-51","Sc-46",
    "Sb-124","Sb-125","Sb-126","Ta-182","W-187","Ir-192","Au-198",
    "Na-24","Mg-27","Al-28","Cl-38","Ar-41","K-42","K-43",
    "Mo-99","Tc-99m","Tc-99",
}

# Fission products
FISSION_PRODUCTS = {
    "Kr-85","Sr-89","Sr-90","Y-90","Y-91",
    "Zr-95","Nb-95","Mo-99","Tc-99",
    "Ru-103","Ru-106","Rh-106",
    "Cs-134","Cs-136","Cs-137","Ba-140","La-140",
    "Ce-141","Ce-144","Pr-144","Nd-147","Pm-147",
    "Sm-151","Eu-154","Eu-155",
    "I-129","I-131","I-132","I-133","Xe-133","Xe-135",
    "Te-129m","Te-131m","Te-132",
}

# Medical / diagnostic isotopes
MEDICAL_ISOTOPES = {
    "Tc-99m","In-111","Ga-67","Tl-201","I-123","I-131",
    "F-18","C-11","N-13","O-15",
    "Lu-177","Y-90","Ho-166","Re-188","Sm-153",
    "Rb-82","Sr-82","Ge-68","Ga-68",
    "Mo-99","Pd-103","I-125","Ir-192","Cs-131","Pd-103",
}

# Industrial / sealed source isotopes
INDUSTRIAL_ISOTOPES = {
    "Am-241","Cf-252","Cs-137","Co-60","Ir-192","Se-75",
    "Yb-169","Tm-170","Ba-133","Cd-109","Fe-55","Ni-63",
    "Kr-85","Pm-147","Sr-90","H-3","C-14","Ra-226",
}

# Weapons-relevant isotopes (handled with care — flags only)
WEAPONS_RELEVANT = {
    "Pu-239","Pu-240","Pu-241","Pu-238",
    "U-235","U-238","U-234",
    "Am-241","Np-237","Cm-244","Cm-242",
    "Li-6","B-10",
}

# Half-life bins (seconds) for classification
HL_VERY_SHORT  = 60           # < 1 min
HL_SHORT       = 3600 * 24    # < 1 day
HL_MEDIUM      = YEAR_S       # < 1 year
HL_LONG        = YEAR_S * 100 # < 100 years

# Uranium enrichment: ratio of U-235 to U-238 activity
# Natural uranium: ~0.046 (0.72% by mass)
# Depleted:        < 0.046
# Low-enriched:    0.046 – 0.20
# Highly enriched: > 0.20
U235_U238_NATURAL = 0.046


# ══════════════════════════════════════════════════════════════════════════════
#  DATA CLASSES
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class IsotopeMatch:
    symbol:          str
    confidence:      float        # 0–1
    pct:             float        # 0–100
    n_matched:       int
    n_total:         int
    matched:         list[dict]   # matched peak details
    unmatched:       list[dict]   # missing strong lines
    half_life:       str
    half_life_s:     float
    detectable:      bool
    detect_reason:   str
    category:        str          # natural / fission / activation / medical / industrial / special
    reasoning:       str          # plain-English explanation of why this score
    strong_lines:    list[float]  # top 3 library energies


@dataclass
class ChainNode:
    symbol:       str
    depth:        int
    half_life_s:  float
    half_life:    str
    decay_mode:   str
    detectable:   bool
    detected:     bool
    strong_gammas: list[tuple[float, float]]  # (keV, intensity%)


@dataclass
class ChainReconstruction:
    root:              str
    nodes:             list[ChainNode]
    n_detectable:      int
    n_detected:        int
    completeness_pct:  float
    missing:           list[str]
    invisible:         list[str]
    interpretation:    str


@dataclass
class RatioResult:
    parent:          str
    daughter:        str
    parent_cps:      float
    daughter_cps:    float
    observed_ratio:  float
    expected_ratio:  float
    deviation_pct:   float
    status:          str    # equilibrium / disrupted / broken
    interpretation:  str
    age_estimate_y:  Optional[float] = None


@dataclass
class ForensicReport:
    # Core identification
    detected_isotopes:   list[IsotopeMatch]
    # Chain reconstruction
    chain_reconstructions: list[ChainReconstruction]
    # Ratio analysis
    ratio_results:       list[RatioResult]
    # Classification
    classification:      str    # NATURAL / NORM / FISSION_PRODUCT / ACTIVATION / MEDICAL / INDUSTRIAL / MIXED / SPECIAL
    classification_confidence: float
    classification_reasoning: str
    # Enrichment
    enrichment_flags:    list[str]
    enrichment_verdict:  str
    u_enrichment_level:  Optional[str]   # natural / depleted / LEU / HEU
    # Age
    age_estimates:       list[dict]
    age_consensus_y:     Optional[float]
    # Provenance
    provenance_narrative: str
    # Anomalies
    anomalies:           list[dict]
    # Processing history
    processing_flags:    list[str]
    # Summary
    summary:             str
    confidence_overall:  float


# ══════════════════════════════════════════════════════════════════════════════
#  1. ENSDF-BACKED PEAK MATCHING
# ══════════════════════════════════════════════════════════════════════════════

def match_peaks_ensdf(
        detected_peaks:  list[dict],
        tolerance_kev:   float = 10.0,
        min_intensity:   float = 0.5,
        max_results:     int   = 30,
        min_confidence:  float = 0.05,
) -> list[IsotopeMatch]:
    """
    Match detected peaks against the full ENSDF gamma database.
    Returns isotope matches ranked by confidence, with detailed reasoning.
    """
    gamma_db    = get_gamma_db()
    det_energies = [p["energy_keV"] for p in detected_peaks]
    peak_map     = {p["energy_keV"]: p for p in detected_peaks}

    matches: list[IsotopeMatch] = []

    for symbol, lib_lines in gamma_db.items():
        # Filter to significant lines above threshold
        sig = [(e, i, n) for e, i, n in lib_lines
               if e >= 40.0 and i >= min_intensity]
        if not sig:
            continue

        matched_lines   = []
        unmatched_lines = []

        for lib_kev, lib_int, note in sig:
            best_det, best_delta = None, tolerance_kev + 1
            for det_kev in det_energies:
                d = abs(det_kev - lib_kev)
                if d < best_delta:
                    best_delta, best_det = d, det_kev
            if best_delta <= tolerance_kev:
                matched_lines.append({
                    "lib_keV":   lib_kev,
                    "det_keV":   best_det,
                    "delta_keV": round(best_delta, 2),
                    "intensity": lib_int,
                    "note":      note,
                    "peak_data": peak_map.get(best_det, {}),
                })
            else:
                unmatched_lines.append({
                    "lib_keV":   lib_kev,
                    "intensity": lib_int,
                    "note":      note,
                })

        if not matched_lines:
            continue

        # ── Confidence scoring ─────────────────────────────────────────────────
        total_int   = sum(l[1] for l in sig)
        matched_int = sum(m["intensity"] for m in matched_lines)
        int_cov     = matched_int / total_int if total_int > 0 else 0
        pk_cov      = len(matched_lines) / len(sig)
        avg_delta   = sum(m["delta_keV"] for m in matched_lines) / len(matched_lines)
        delta_score = max(0.0, 1.0 - avg_delta / tolerance_kev)

        # Strongest line bonus
        strongest = max(sig, key=lambda x: x[1])
        top_hit   = any(abs(m["lib_keV"] - strongest[0]) < tolerance_kev
                        for m in matched_lines)
        top_bonus = 0.15 if top_hit else 0.0

        # Penalty for many unmatched strong lines
        strong_unmatched = [u for u in unmatched_lines if u["intensity"] > 20]
        miss_penalty     = min(0.20, len(strong_unmatched) * 0.05)

        confidence = (0.45 * int_cov +
                      0.25 * pk_cov  +
                      0.15 * delta_score +
                      0.15 * top_bonus -
                      miss_penalty)
        confidence = round(max(0.0, min(confidence, 1.0)), 4)

        if confidence < min_confidence:
            continue

        # ── Half-life & detectability ──────────────────────────────────────────
        hl_s, hl_r = get_half_life(symbol)
        det, det_r = is_detectable(symbol)

        # ── Category ──────────────────────────────────────────────────────────
        category = _classify_isotope(symbol, hl_s)

        # ── Reasoning ─────────────────────────────────────────────────────────
        reasoning = _build_reasoning(
            symbol, confidence, matched_lines, unmatched_lines,
            sig, int_cov, pk_cov, avg_delta, top_hit, strong_unmatched
        )

        strong_lines = sorted([l[0] for l in sig], key=lambda x: -dict(
            (l[0], l[1]) for l in sig).get(x, 0))[:3]

        matches.append(IsotopeMatch(
            symbol        = symbol,
            confidence    = confidence,
            pct           = round(confidence * 100, 1),
            n_matched     = len(matched_lines),
            n_total       = len(sig),
            matched       = matched_lines,
            unmatched     = unmatched_lines,
            half_life     = hl_r,
            half_life_s   = hl_s,
            detectable    = det,
            detect_reason = det_r,
            category      = category,
            reasoning     = reasoning,
            strong_lines  = strong_lines,
        ))

    matches.sort(key=lambda x: x.confidence, reverse=True)
    return matches[:max_results]


def _classify_isotope(symbol: str, hl_s: float) -> str:
    if symbol in MEDICAL_ISOTOPES:    return "medical"
    if symbol in FISSION_PRODUCTS:    return "fission"
    if symbol in ACTIVATION_ISOTOPES: return "activation"
    if symbol in INDUSTRIAL_ISOTOPES: return "industrial"
    if symbol in NATURAL_ISOTOPES:    return "natural"
    if symbol in WEAPONS_RELEVANT:    return "special"
    if hl_s < HL_SHORT:               return "short-lived"
    return "unknown"


def _build_reasoning(symbol, confidence, matched, unmatched,
                      sig, int_cov, pk_cov, avg_delta,
                      top_hit, strong_unmatched) -> str:
    parts = []
    parts.append(f"Matched {len(matched)}/{len(sig)} significant lines "
                 f"({int_cov*100:.0f}% intensity coverage, "
                 f"{pk_cov*100:.0f}% line coverage).")
    if top_hit:
        strongest_kev = max(sig, key=lambda x: x[1])[0]
        parts.append(f"Strongest library line ({strongest_kev:.1f} keV) is present.")
    else:
        strongest_kev = max(sig, key=lambda x: x[1])[0]
        parts.append(f"⚠ Strongest library line ({strongest_kev:.1f} keV) was NOT detected — lowers confidence.")
    if avg_delta < 3:
        parts.append(f"Peak centroids match very closely (avg Δ={avg_delta:.1f} keV).")
    elif avg_delta < 7:
        parts.append(f"Peak centroids match reasonably (avg Δ={avg_delta:.1f} keV).")
    else:
        parts.append(f"Peak centroids are loosely matched (avg Δ={avg_delta:.1f} keV) — may be coincidental.")
    if strong_unmatched:
        syms = ", ".join(f"{u['lib_keV']:.1f} keV ({u['intensity']:.0f}%)"
                         for u in strong_unmatched[:3])
        parts.append(f"Strong lines expected but absent: {syms}.")
    if symbol in NATURAL_ISOTOPES:
        parts.append("This is a primordial or cosmogenic isotope — expected in all rock, soil, and mineral samples.")
    elif symbol in FISSION_PRODUCTS:
        parts.append("Fission product — implies exposure to neutron flux (reactor or weapon).")
    elif symbol in MEDICAL_ISOTOPES:
        parts.append("Medical radionuclide — implies recent radiopharmaceutical use or contamination.")
    return " ".join(parts)


# ══════════════════════════════════════════════════════════════════════════════
#  2. DYNAMIC DECAY CHAIN RECONSTRUCTION
# ══════════════════════════════════════════════════════════════════════════════

def reconstruct_chain(
        root_symbol:       str,
        detected_isotopes: list[str],
        max_depth:         int = 30,
) -> ChainReconstruction:
    """
    Build a full decay chain from root_symbol using radioactivedecay if
    available, falling back to the curated isotope_db chains.
    """
    detected_set = set(detected_isotopes)
    nodes: list[ChainNode] = []

    if RAD_AVAILABLE:
        nodes = _build_chain_rad(root_symbol, detected_set, max_depth)
    else:
        raw_chain = build_chain(root_symbol, max_depth=max_depth)
        for m in raw_chain:
            hl_s, hl_r = get_half_life(m["symbol"])
            det, _     = is_detectable(m["symbol"])
            nodes.append(ChainNode(
                symbol        = m["symbol"],
                depth         = m["depth"],
                half_life_s   = hl_s,
                half_life     = m.get("half_life", hl_r),
                decay_mode    = m.get("decay_mode", "?"),
                detectable    = det,
                detected      = m["symbol"] in detected_set,
                strong_gammas = m.get("strong_gammas", []),
            ))

    if not nodes:
        return ChainReconstruction(
            root=root_symbol, nodes=[], n_detectable=0, n_detected=0,
            completeness_pct=0.0, missing=[], invisible=[],
            interpretation=f"Could not build chain for {root_symbol}")

    detectable = [n for n in nodes if n.detectable]
    detected   = [n for n in detectable if n.detected]
    missing    = [n.symbol for n in detectable if not n.detected]
    invisible  = [n.symbol for n in nodes if not n.detectable]
    pct        = round(len(detected) / max(len(detectable), 1) * 100, 1)

    return ChainReconstruction(
        root              = root_symbol,
        nodes             = nodes,
        n_detectable      = len(detectable),
        n_detected        = len(detected),
        completeness_pct  = pct,
        missing           = missing,
        invisible         = invisible,
        interpretation    = _chain_interpretation(root_symbol, pct, missing, detected),
    )


def _build_chain_rad(root: str, detected_set: set,
                      max_depth: int) -> list[ChainNode]:
    """Walk decay chain using radioactivedecay library."""
    nodes   = []
    visited = set()

    def walk(symbol: str, depth: int):
        if depth > max_depth or symbol in visited:
            return
        visited.add(symbol)
        try:
            nuc    = rd.Nuclide(symbol)
            hl_s   = nuc.half_life("s")
            hl_r   = _fmt_hl(hl_s)
            modes  = nuc.decay_modes()
            mode_s = "/".join(modes) if modes else "stable"
            det, _ = is_detectable(symbol)
            # Get strong gamma lines from ENSDF db
            from ensdf_parser import get_lines_for_isotope
            lines = get_lines_for_isotope(symbol)
            strong = [(e, i) for e, i, _ in lines if i > 5 and e > 40]
            strong.sort(key=lambda x: -x[1])
            nodes.append(ChainNode(
                symbol        = symbol,
                depth         = depth,
                half_life_s   = float(hl_s) if hl_s != float("inf") else 1e30,
                half_life     = hl_r,
                decay_mode    = mode_s,
                detectable    = det,
                detected      = symbol in detected_set,
                strong_gammas = strong[:4],
            ))
            for daughter, _ in nuc.progeny():
                walk(daughter, depth + 1)
        except Exception:
            return

    walk(root, 0)
    return nodes


def _fmt_hl(seconds) -> str:
    if seconds >= 1e30: return "stable"
    if seconds > YEAR_S * 1e6: return f"{seconds/YEAR_S:.3e} y"
    if seconds > YEAR_S:       return f"{seconds/YEAR_S:.2f} y"
    if seconds > 86400:        return f"{seconds/86400:.1f} d"
    if seconds > 3600:         return f"{seconds/3600:.1f} h"
    if seconds > 60:           return f"{seconds/60:.1f} min"
    return f"{seconds:.1f} s"


def _chain_interpretation(root, pct, missing, detected) -> str:
    det_names = ", ".join(n.symbol for n in detected[:4])
    if pct >= 85:
        return (f"Chain is essentially complete ({pct:.0f}%). "
                f"{root} present and in secular equilibrium. Detected: {det_names}.")
    if pct >= 50:
        miss_s = ", ".join(missing[:4])
        return (f"Partial chain ({pct:.0f}% complete). "
                f"Missing: {miss_s}. Possible Rn escape, chemical processing, or young sample.")
    if pct >= 20:
        return (f"Weak chain signature ({pct:.0f}%). "
                f"Chain significantly disrupted or {root} activity is very low.")
    return (f"Very incomplete ({pct:.0f}%). May be trace contamination rather than "
            f"a primary {root} source.")


# ══════════════════════════════════════════════════════════════════════════════
#  3. ISOTOPE RATIO ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════

# Known secular equilibrium pairs with expected ratios and age context
# Format: (parent, daughter, expected_ratio, condition, age_sensitive)
RATIO_PAIRS = [
    # U-238 chain
    ("Ra-226",  "Pb-214",  1.0,    "Rn in sample",      False),
    ("Ra-226",  "Bi-214",  1.0,    "Rn in sample",      False),
    ("Pb-214",  "Bi-214",  1.0,    "Fast equilibrium",  False),
    ("Th-234",  "Pa-234m", 1.0,    "Fast equilibrium",  False),
    # Th-232 chain
    ("Ac-228",  "Pb-212",  1.0,    "Th-232 chain",      False),
    ("Pb-212",  "Tl-208",  0.3594, "36% Bi-212 branch", False),
    ("Pb-212",  "Bi-212",  1.0,    "Direct",            False),
    ("Ra-228",  "Ac-228",  1.0,    "Fast equilibrium",  False),
    # U-235 chain
    ("Ra-223",  "Bi-211",  1.0,    "U-235 chain",       False),
    # Cs-137 / Ba-137m (instantaneous — ratio reveals detector timing)
    ("Cs-137",  "Ba-137m", 0.946,  "IT branch 94.6%",   False),
    # Anthropogenic markers
    ("Cs-134",  "Cs-137",  None,   "Fission ratio — age proxy", True),
    ("Eu-154",  "Eu-155",  None,   "Activation ratio",  True),
]


def analyse_ratios(
        matches:     list[IsotopeMatch],
        detected_peaks: list[dict],
        live_time_s: float,
) -> list[RatioResult]:
    """
    Compute activity ratios for all detectable pairs among identified isotopes.
    Uses CPS of the strongest matched peak as activity proxy.
    """
    # Build activity map: symbol → CPS of strongest matched line
    activity: dict[str, float] = {}
    for m in matches:
        if m.matched and m.confidence > 0.15:
            best = max(m.matched, key=lambda x: x["intensity"])
            pd   = best.get("peak_data", {})
            cps  = pd.get("counts", 0) / max(live_time_s, 1)
            if cps > 0:
                activity[m.symbol] = cps

    results: list[RatioResult] = []

    for parent, daughter, exp_ratio, condition, age_sensitive in RATIO_PAIRS:
        a_p = activity.get(parent)
        a_d = activity.get(daughter)
        if a_p is None or a_d is None or a_p <= 0:
            continue

        obs = a_d / a_p
        if exp_ratio is None:
            # Can't compute equilibrium deviation without expected — just report ratio
            results.append(RatioResult(
                parent=parent, daughter=daughter,
                parent_cps=round(a_p,6), daughter_cps=round(a_d,6),
                observed_ratio=round(obs,4), expected_ratio=0.0,
                deviation_pct=0.0, status="informational",
                interpretation=_ratio_narrative_info(parent, daughter, obs),
            ))
            continue

        dev  = abs(obs - exp_ratio) / max(exp_ratio, 1e-9)
        status = ("equilibrium" if dev < 0.20 else
                  "disrupted"   if dev < 0.50 else "broken")

        # Age estimate from ratio (for age-sensitive pairs)
        age_est = None
        if age_sensitive and obs > 0:
            age_est = _estimate_age_from_ratio(parent, daughter, obs)

        results.append(RatioResult(
            parent=parent, daughter=daughter,
            parent_cps=round(a_p,6), daughter_cps=round(a_d,6),
            observed_ratio=round(obs,4), expected_ratio=round(exp_ratio,4),
            deviation_pct=round(dev*100,1), status=status,
            interpretation=_ratio_narrative(parent, daughter, status, obs, exp_ratio),
            age_estimate_y=age_est,
        ))

    return results


def _ratio_narrative_info(parent, daughter, obs) -> str:
    if parent == "Cs-134" and daughter == "Cs-137":
        if obs > 0.5:
            return ("Cs-134/Cs-137 ratio > 0.5 — very recent irradiation (< ~5 years). "
                    "Consistent with recent reactor accident or nuclear test fallout.")
        if obs > 0.1:
            return ("Cs-134/Cs-137 ratio 0.1–0.5 — irradiation within ~10–20 years. "
                    "Consistent with Chernobyl-era or post-2000 reactor fallout.")
        return ("Low Cs-134/Cs-137 ratio — irradiation > 20 years ago. "
                "Cs-134 has largely decayed away (t½=2.06y).")
    return f"Activity ratio {parent}/{daughter}: {obs:.4f} — informational."


def _ratio_narrative(parent, daughter, status, obs, exp) -> str:
    if status == "equilibrium":
        return (f"{parent}→{daughter}: secular equilibrium (obs={obs:.3f}, exp={exp:.3f}). "
                f"Closed system — no chemical processing or Rn escape detected.")
    if status == "broken":
        if obs < exp * 0.5:
            if "Pb-214" in (parent,daughter) or "Bi-214" in (parent,daughter):
                return (f"{daughter} strongly depleted (obs={obs:.3f} vs exp={exp:.3f}): "
                        f"Rn-222 escaping from sample before decaying to solid daughters. "
                        f"Sample is open, porous, or stored in gas-permeable container.")
            if "Pb-212" in (parent,daughter) or "Tl-208" in (parent,daughter):
                return (f"{daughter} depleted (obs={obs:.3f} vs exp={exp:.3f}): "
                        f"Rn-220 (thoron) escaping or recent Th chemical separation.")
            return (f"{daughter} depleted relative to {parent} (obs={obs:.3f} vs exp={exp:.3f}): "
                    f"Chain disrupted — chemical separation, young sample, or open system.")
        return (f"{daughter} elevated relative to {parent} (obs={obs:.3f} vs exp={exp:.3f}): "
                f"Daughter excess — transient disequilibrium, external contamination, "
                f"or recent parent ingrowth after separation.")
    return (f"{parent}→{daughter}: mild deviation {abs(obs-exp)/max(exp,1e-9)*100:.0f}% "
            f"from equilibrium (obs={obs:.3f}, exp={exp:.3f}). Marginal disruption.")


def _estimate_age_from_ratio(parent, daughter, obs_ratio) -> Optional[float]:
    """Estimate sample age from ingrowth/decay ratios where applicable."""
    # Cs-134 / Cs-137: both from fission, Cs-134 t½=2.065y, Cs-137 t½=30.17y
    if parent == "Cs-134" and daughter == "Cs-137":
        # ratio ≈ (initial_134/137) × exp(-λ_134 × t) / exp(-λ_137 × t)
        # assuming initial ratio ~1 (fresh fission product)
        try:
            lam_134 = math.log(2) / (2.065  * YEAR_S)
            lam_137 = math.log(2) / (30.17  * YEAR_S)
            # obs_ratio = exp(-(λ_134 - λ_137) × t)
            t = -math.log(max(obs_ratio, 1e-6)) / (lam_134 - lam_137)
            return round(t / YEAR_S, 1)
        except Exception:
            return None
    return None


# ══════════════════════════════════════════════════════════════════════════════
#  4. ENRICHMENT ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════

def analyse_enrichment(matches: list[IsotopeMatch],
                        detected_peaks: list[dict],
                        live_time_s: float) -> dict:
    """
    Examine U/Th/Pu isotope ratios to flag enrichment or processing.
    """
    flags   = []
    verdict = "No enrichment indicators detected."
    u_level = None

    syms = {m.symbol: m for m in matches if m.confidence > 0.15}

    # Build CPS proxy
    cps: dict[str, float] = {}
    for m in matches:
        if m.matched and m.confidence > 0.15:
            best = max(m.matched, key=lambda x: x["intensity"])
            pd   = best.get("peak_data", {})
            c    = pd.get("counts", 0) / max(live_time_s, 1)
            if c > 0:
                cps[m.symbol] = c

    # ── Uranium enrichment ────────────────────────────────────────────────────
    has_u235 = "U-235"  in syms
    has_u238 = "U-238"  in syms or "Th-234" in syms or "Bi-214" in syms
    has_u234 = "U-234"  in syms

    if has_u235 and has_u238:
        a235 = cps.get("U-235",  cps.get("Pa-231", 0))
        a238 = cps.get("Th-234", cps.get("Bi-214", 0))  # U-238 proxy daughters
        if a235 > 0 and a238 > 0:
            ratio = a235 / a238
            if ratio < U235_U238_NATURAL * 0.5:
                u_level = "depleted"
                flags.append("⚠ U-235/U-238 ratio BELOW natural — depleted uranium (DU) indicated.")
            elif ratio < U235_U238_NATURAL * 1.5:
                u_level = "natural"
            elif ratio < 0.20:
                u_level = "LEU"
                flags.append("⚠ U-235/U-238 ratio elevated — LOW-ENRICHED URANIUM (LEU) possible.")
            else:
                u_level = "HEU"
                flags.append("🚨 U-235/U-238 ratio strongly elevated — HIGHLY ENRICHED URANIUM (HEU) possible. Expert verification required.")
        elif has_u235 and not has_u238:
            flags.append("⚠ U-235 detected without natural U-238 daughters — possible enriched uranium.")
            u_level = "unknown (U-238 daughters absent)"

    # ── Plutonium ─────────────────────────────────────────────────────────────
    pu_isotopes = [s for s in ["Pu-238","Pu-239","Pu-240","Pu-241"] if s in syms]
    if pu_isotopes:
        am241 = "Am-241" in syms  # Am-241 ingrows from Pu-241 decay
        if "Pu-241" in pu_isotopes and am241:
            flags.append("Pu-241 + Am-241 detected: Am-241 has ingrown from Pu-241 (t½=14.4y) — "
                         "material is at least several years post-irradiation.")
        if len(pu_isotopes) > 1:
            flags.append(f"Multiple Pu isotopes detected ({', '.join(pu_isotopes)}) — "
                         "reactor-grade plutonium composition signature.")
        else:
            flags.append(f"{pu_isotopes[0]} detected — weapons-grade Pu cannot be ruled out "
                         "without Pu-240 assessment (RC-103 cannot detect Pu-239 directly).")

    # ── Thorium processing ────────────────────────────────────────────────────
    has_th232  = "Th-232"  in syms or "Ac-228" in syms
    has_th228  = "Th-228"  in syms or "Ra-224" in syms
    has_ra228  = "Ra-228"  in syms or "Ac-228" in syms
    if has_th232 and has_th228 and not has_ra228:
        flags.append("Th-232 and Th-228 detected without Ra-228: "
                     "thorium has been chemically separated from radium — processed material.")

    # ── Ra-226 without U-238 chain ────────────────────────────────────────────
    if "Ra-226" in syms:
        u238_daughters = {"Pb-214","Bi-214","Th-234","Pa-234m"}
        present_u238   = u238_daughters & set(syms.keys())
        if not present_u238:
            flags.append("Ra-226 present without U-238 chain daughters — "
                         "radium has been separated from uranium ore (NORM processing).")

    if not flags:
        verdict = ("Isotope ratios consistent with natural abundance. "
                   "No enrichment or chemical separation indicators detected.")
    elif u_level in ("LEU", "HEU"):
        verdict = f"ENRICHMENT INDICATORS PRESENT — {u_level} uranium signature."
    else:
        verdict = "Processing or separation indicators detected — see flags."

    return {
        "flags":       flags,
        "verdict":     verdict,
        "u_level":     u_level,
        "n_flags":     len(flags),
    }


# ══════════════════════════════════════════════════════════════════════════════
#  5. CLASSIFICATION
# ══════════════════════════════════════════════════════════════════════════════

def classify_sample(matches: list[IsotopeMatch]) -> dict:
    """
    Classify the overall sample type from detected isotopes.
    Returns classification, confidence, and reasoning.
    """
    good = [m for m in matches if m.confidence > 0.20]
    if not good:
        return {"classification": "UNKNOWN", "confidence": 0.0,
                "reasoning": "No isotopes identified with sufficient confidence."}

    syms  = {m.symbol for m in good}
    cats  = [m.category for m in good]

    n_nat    = sum(1 for c in cats if c == "natural")
    n_fis    = sum(1 for c in cats if c == "fission")
    n_act    = sum(1 for c in cats if c == "activation")
    n_med    = sum(1 for c in cats if c == "medical")
    n_ind    = sum(1 for c in cats if c == "industrial")
    n_spc    = sum(1 for c in cats if c == "special")
    total    = len(good)

    # Special / weapons-relevant takes priority
    if n_spc > 0:
        spc_syms = [m.symbol for m in good if m.category == "special"]
        return {
            "classification": "SPECIAL NUCLEAR MATERIAL",
            "confidence": 0.85,
            "reasoning": (f"Weapons-relevant isotopes detected: {', '.join(spc_syms)}. "
                          "This classification requires expert verification. "
                          "RC-103 cannot directly detect Pu-239 or U-235 at trace levels."),
        }

    if n_med >= 1 and n_fis == 0 and n_spc == 0:
        med_syms = [m.symbol for m in good if m.category == "medical"]
        return {
            "classification": "MEDICAL / RADIOPHARMACEUTICAL",
            "confidence": round(n_med / total, 2),
            "reasoning": (f"Short-lived medical isotopes dominate: {', '.join(med_syms)}. "
                          "Consistent with recent nuclear medicine procedure, PET/SPECT imaging, "
                          "or medical waste."),
        }

    if n_fis > 0 and n_nat == 0:
        fis_syms = [m.symbol for m in good if m.category == "fission"]
        return {
            "classification": "FISSION PRODUCTS",
            "confidence": round(n_fis / total, 2),
            "reasoning": (f"Fission products detected: {', '.join(fis_syms)}. "
                          "Implies exposure to reactor irradiation, nuclear weapon detonation, "
                          "or fallout contamination."),
        }

    if n_fis > 0 and n_nat > 0:
        return {
            "classification": "MIXED — NATURAL + FISSION",
            "confidence": 0.70,
            "reasoning": ("Both natural decay chain isotopes and fission products detected. "
                          "Consistent with NORM material contaminated by fallout, or a sample "
                          "that was inside or near a reactor."),
        }

    if n_act > 0 and n_nat == 0:
        act_syms = [m.symbol for m in good if m.category == "activation"]
        return {
            "classification": "ACTIVATION PRODUCTS",
            "confidence": round(n_act / total, 2),
            "reasoning": (f"Neutron activation products: {', '.join(act_syms)}. "
                          "Consistent with material exposed to neutron flux — reactor components, "
                          "accelerator targets, or industrial irradiation."),
        }

    if n_ind >= 1 and n_nat == 0 and n_fis == 0:
        ind_syms = [m.symbol for m in good if m.category == "industrial"]
        return {
            "classification": "INDUSTRIAL / SEALED SOURCE",
            "confidence": round(n_ind / total, 2),
            "reasoning": (f"Industrial isotopes detected: {', '.join(ind_syms)}. "
                          "Consistent with sealed calibration sources, density gauges, "
                          "well-logging tools, or radiography sources."),
        }

    # Natural / NORM
    nat_syms = [m.symbol for m in good if m.category == "natural"]
    u_present  = any(s in syms for s in ["U-238","Th-234","Pa-234m","Bi-214","Pb-214"])
    th_present = any(s in syms for s in ["Th-232","Ac-228","Tl-208","Pb-212","Bi-212"])
    k_present  = "K-40" in syms

    if u_present or th_present:
        return {
            "classification": "NORM — NATURALLY OCCURRING RADIOACTIVE MATERIAL",
            "confidence": round(n_nat / max(total, 1), 2),
            "reasoning": (f"Natural decay chain isotopes present: {', '.join(nat_syms[:6])}. "
                          f"Consistent with uranium/thorium-bearing minerals, soil, rock, "
                          f"or NORM industrial waste (phosphogypsum, red mud, scale)."),
        }

    return {
        "classification": "NATURAL BACKGROUND",
        "confidence": round(n_nat / max(total, 1), 2),
        "reasoning": (f"Only natural isotopes detected: {', '.join(nat_syms[:6])}. "
                      "Spectrum consistent with normal environmental background radiation."),
    }


# ══════════════════════════════════════════════════════════════════════════════
#  6. PROVENANCE NARRATIVE
# ══════════════════════════════════════════════════════════════════════════════

def build_provenance_narrative(
        classification: dict,
        matches:        list[IsotopeMatch],
        chains:         list[ChainReconstruction],
        ratios:         list[RatioResult],
        enrichment:     dict,
        anomalies:      list[dict],
        age_estimates:  list[dict],
) -> str:
    """Generate a detailed plain-English provenance narrative."""
    cls    = classification["classification"]
    good   = [m for m in matches if m.confidence > 0.20]
    syms   = {m.symbol for m in good}
    paras  = []

    # Opening
    paras.append(
        f"SAMPLE CLASSIFICATION: {cls} "
        f"(confidence {classification['confidence']*100:.0f}%).\n"
        f"{classification['reasoning']}"
    )

    # Isotope inventory
    if good:
        by_cat: dict[str, list] = {}
        for m in good:
            by_cat.setdefault(m.category, []).append(m.symbol)
        inv_parts = []
        for cat, iso_list in by_cat.items():
            inv_parts.append(f"{cat}: {', '.join(iso_list)}")
        paras.append("Isotope inventory — " + ";  ".join(inv_parts) + ".")

    # Chain reconstructions
    for chain in chains:
        if chain.completeness_pct > 10:
            paras.append(
                f"Decay chain {chain.root}: {chain.completeness_pct:.0f}% complete "
                f"({chain.n_detected}/{chain.n_detectable} detectable members found). "
                f"{chain.interpretation}"
            )

    # Secular equilibrium
    eq_broken  = [r for r in ratios if r.status == "broken"]
    eq_ok      = [r for r in ratios if r.status == "equilibrium"]
    if eq_ok:
        pairs = ", ".join(f"{r.parent}→{r.daughter}" for r in eq_ok[:3])
        paras.append(f"Secular equilibrium confirmed for: {pairs}. "
                     "These pairs indicate a closed, undisturbed system.")
    if eq_broken:
        for r in eq_broken:
            paras.append(f"Equilibrium broken: {r.interpretation}")

    # Age
    if age_estimates:
        for ae in age_estimates:
            paras.append(f"Age estimate from {ae['method']}: {ae['value_y']:.1f} years. {ae['basis']}")

    # Enrichment
    if enrichment["flags"]:
        paras.append("ENRICHMENT / PROCESSING ANALYSIS: " + "  ".join(enrichment["flags"]))

    # Anomalies
    for anom in anomalies:
        paras.append(f"ANOMALY [{anom['level'].upper()}]: {anom['title']} — {anom['detail']}")

    # Processing history inference
    processing = _infer_processing(syms, ratios, chains)
    if processing:
        paras.append("PROCESSING HISTORY: " + "  ".join(processing))

    return "\n\n".join(paras)


def _infer_processing(syms: set, ratios: list, chains: list) -> list[str]:
    flags = []
    # Ra-226 isolated from U-238 chain?
    if "Ra-226" in syms:
        u_daughters = {"Pb-214","Bi-214","Th-234","Pa-234m","U-238"}
        if not (u_daughters & syms):
            flags.append("Ra-226 present without U-238 chain — radium extracted from ore.")
    # Th-228 without Ra-228?
    if ("Th-228" in syms or "Ra-224" in syms) and "Ra-228" not in syms and "Ac-228" not in syms:
        flags.append("Th-228 chain members without Ra-228/Ac-228 — possible thorium processing.")
    # Am-241 alone?
    if "Am-241" in syms:
        pu_related = {"Pu-239","Pu-241","Np-237","U-235"}
        if not (pu_related & syms):
            flags.append("Am-241 without Pu/Np chain — possible sealed smoke detector or calibration source.")
    # Cs-137 without fission companions?
    if "Cs-137" in syms:
        fission_companions = {"Cs-134","Sr-90","Co-60","Eu-154","Ba-140"}
        if not (fission_companions & syms):
            flags.append("Cs-137 in isolation — likely calibration source or single-nuclide contamination, not bulk fallout.")
    return flags


# ══════════════════════════════════════════════════════════════════════════════
#  7. AGE ESTIMATION
# ══════════════════════════════════════════════════════════════════════════════

def estimate_ages(matches: list[IsotopeMatch],
                   ratios: list[RatioResult],
                   detected_peaks: list[dict],
                   live_time_s: float) -> list[dict]:
    """Compile all available age constraints."""
    ages = []

    # From ratio analysis
    for r in ratios:
        if r.age_estimate_y is not None:
            ages.append({
                "method":   f"{r.parent}/{r.daughter} activity ratio",
                "value_y":  r.age_estimate_y,
                "basis":    r.interpretation,
                "confidence": "moderate",
            })

    # Cs-137 alone (known injection date ~1945 for weapons, 1986 for Chernobyl)
    cs137 = next((m for m in matches if m.symbol == "Cs-137" and m.confidence > 0.3), None)
    if cs137:
        ages.append({
            "method":   "Cs-137 presence",
            "value_y":  None,
            "basis":    ("Cs-137 was first released to the environment in 1945 (Trinity test). "
                         "Presence constrains sample collection to post-1945, or indicates "
                         "anthropogenic contamination."),
            "confidence": "qualitative",
        })

    # Pb-210 / Bi-214 ingrowth (U-238 chain, sensitive to Rn history)
    syms = {m.symbol for m in matches if m.confidence > 0.2}
    if "Pb-210" in syms and "Ra-226" in syms:
        ages.append({
            "method":   "Pb-210/Ra-226 ingrowth",
            "value_y":  None,
            "basis":    ("Pb-210 (t½=22.3y) grows into closed systems from Rn-222. "
                         "If Pb-210/Ra-226 ≈ 1, system has been closed > 100 years. "
                         "Quantitative age requires activity measurement."),
            "confidence": "qualitative",
        })

    return ages


# ══════════════════════════════════════════════════════════════════════════════
#  8. ANOMALY DETECTION (UPGRADED)
# ══════════════════════════════════════════════════════════════════════════════

def detect_anomalies_full(
        matches:     list[IsotopeMatch],
        ratios:      list[RatioResult],
        chains:      list[ChainReconstruction],
        enrichment:  dict,
) -> list[dict]:
    """Comprehensive anomaly detector using all available data."""
    anomalies = []
    syms      = {m.symbol for m in matches if m.confidence > 0.2}

    # Rn-222 escape
    if "Ra-226" in syms and not ({"Pb-214","Bi-214"} & syms):
        anomalies.append({
            "level": "high", "type": "chain_break",
            "title": "Rn-222 escape",
            "detail": ("Ra-226 present but Pb-214 and Bi-214 absent. "
                       "Rn-222 gas escaping from sample before decaying to solid daughters. "
                       "Sample is open or porous — indoor contamination risk."),
        })

    # Th chain broken
    if "Ac-228" in syms and not ({"Tl-208","Pb-212","Bi-212"} & syms):
        anomalies.append({
            "level": "medium", "type": "chain_break",
            "title": "Th-232 chain disruption",
            "detail": ("Ac-228 detected without Tl-208/Pb-212/Bi-212. "
                       "Rn-220 escaping or recent Ra/Th chemical separation."),
        })

    # Recent reactor exposure
    if "Cs-134" in syms:
        anomalies.append({
            "level": "high", "type": "reactor_exposure",
            "title": "Cs-134 detected — recent reactor exposure",
            "detail": ("Cs-134 (t½=2.06y) implies irradiation within the last ~15 years. "
                       "Consistent with nuclear accident fallout (Fukushima 2011, "
                       "Chernobyl 1986 residual at very low levels), medical waste, "
                       "or reactor component activation."),
        })

    # Enrichment anomalies
    for flag in enrichment.get("flags", []):
        if "LEU" in flag or "HEU" in flag or "depleted" in flag.lower():
            anomalies.append({
                "level": "high" if "HEU" in flag else "medium",
                "type":  "enrichment",
                "title": "Uranium enrichment anomaly",
                "detail": flag,
            })

    # Broken equilibrium from ratios
    for r in ratios:
        if r.status == "broken":
            anomalies.append({
                "level": "medium", "type": "disequilibrium",
                "title": f"Secular equilibrium broken: {r.parent}→{r.daughter}",
                "detail": r.interpretation,
            })

    # Incomplete chains with specific missing members
    for chain in chains:
        if 20 < chain.completeness_pct < 60 and chain.n_detected >= 2:
            anomalies.append({
                "level": "low", "type": "incomplete_chain",
                "title": f"{chain.root} chain only {chain.completeness_pct:.0f}% complete",
                "detail": (f"Missing expected members: {', '.join(chain.missing[:5])}. "
                           f"{chain.interpretation}"),
            })

    return anomalies


# ══════════════════════════════════════════════════════════════════════════════
#  MASTER FUNCTION
# ══════════════════════════════════════════════════════════════════════════════

def full_forensic_analysis(
        detected_peaks:  list[dict],
        live_time_s:     float,
        tolerance_kev:   float = 10.0,
        max_matches:     int   = 30,
        chains_to_build: list[str] | None = None,
) -> ForensicReport:
    """
    Run the complete forensic analysis pipeline on a spectrum.

    detected_peaks: from find_spectrum_peaks()
    live_time_s:    measurement live time
    tolerance_kev:  peak matching window
    chains_to_build: root symbols to reconstruct (auto-detected if None)

    Returns a ForensicReport with all fields populated.
    """
    # 1. Match peaks → isotopes using full ENSDF database
    matches = match_peaks_ensdf(detected_peaks, tolerance_kev, max_results=max_matches)

    # 2. Reconstruct decay chains for top candidates
    good_syms = [m.symbol for m in matches if m.confidence > 0.25]
    if chains_to_build is None:
        # Auto-select: find likely chain roots
        chains_to_build = _auto_select_roots(good_syms)

    chains = []
    for root in chains_to_build[:6]:  # limit to 6 chains
        chain = reconstruct_chain(root, good_syms)
        if chain.nodes:
            chains.append(chain)

    # 3. Ratio analysis
    ratios = analyse_ratios(matches, detected_peaks, live_time_s)

    # 4. Classification
    classification = classify_sample(matches)

    # 5. Enrichment
    enrichment = analyse_enrichment(matches, detected_peaks, live_time_s)

    # 6. Age estimates
    age_estimates = estimate_ages(matches, ratios, detected_peaks, live_time_s)

    # 7. Anomalies
    anomalies = detect_anomalies_full(matches, ratios, chains, enrichment)

    # 8. Processing history
    syms_set     = {m.symbol for m in matches if m.confidence > 0.2}
    processing   = _infer_processing(syms_set, ratios, chains)

    # 9. Provenance narrative
    narrative = build_provenance_narrative(
        classification, matches, chains, ratios,
        enrichment, anomalies, age_estimates
    )

    # 10. Overall confidence
    n_good = sum(1 for m in matches if m.confidence > 0.3)
    overall_conf = round(min(0.95, n_good * 0.1 + 0.3), 2) if n_good else 0.1

    # Consensus age
    numeric_ages = [a["value_y"] for a in age_estimates if a.get("value_y")]
    age_consensus = round(sum(numeric_ages) / len(numeric_ages), 1) if numeric_ages else None

    return ForensicReport(
        detected_isotopes          = matches,
        chain_reconstructions      = chains,
        ratio_results              = ratios,
        classification             = classification["classification"],
        classification_confidence  = classification["confidence"],
        classification_reasoning   = classification["reasoning"],
        enrichment_flags           = enrichment["flags"],
        enrichment_verdict         = enrichment["verdict"],
        u_enrichment_level         = enrichment["u_level"],
        age_estimates              = age_estimates,
        age_consensus_y            = age_consensus,
        provenance_narrative       = narrative,
        anomalies                  = anomalies,
        processing_flags           = processing,
        summary                    = classification["reasoning"],
        confidence_overall         = overall_conf,
    )


def _auto_select_roots(detected_syms: list[str]) -> list[str]:
    """Pick the most likely chain roots to reconstruct based on detected isotopes."""
    CHAIN_INDICATORS = {
        "U-238":  {"Bi-214","Pb-214","Ra-226","Th-234","Pa-234m","Pb-210"},
        "Th-232": {"Ac-228","Tl-208","Pb-212","Bi-212","Ra-228"},
        "U-235":  {"Ra-223","Rn-219","Bi-211","Tl-207","Ac-227","Pa-231"},
        "Pu-239": {"U-235","Np-237","Am-241"},
        "Cs-137": {"Cs-137","Ba-137m"},
        "Co-60":  {"Co-60"},
        "Ra-226": {"Pb-214","Bi-214","Pb-210","Po-210"},
    }
    det_set = set(detected_syms)
    scores  = {}
    for root, indicators in CHAIN_INDICATORS.items():
        score = len(indicators & det_set)
        if score > 0:
            scores[root] = score
    return sorted(scores, key=lambda x: -scores[x])
