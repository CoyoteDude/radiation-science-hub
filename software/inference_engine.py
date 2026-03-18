"""
inference_engine.py
─────────────────────────────────────────────────────────────────────────────
Nuclear forensics inference engine for gamma spectroscopy.

Features:
  1. Alpha-blind parent inference  — predict invisible alpha/beta emitters
                                     from visible daughter gamma lines
  2. Secular equilibrium checker   — compare observed vs expected activity ratios
  3. Chain completeness scorer     — what % of expected chain is visible?
  4. Anomaly flagging              — missing daughters that SHOULD be present
  5. Forensic profile matching     — authenticate against known material signatures
  6. Nuclide lookup                — search 1252 nuclides via radioactivedecay
"""

from __future__ import annotations
import math
from typing import Optional

from isotope_db import (
    GAMMA_LINES, FORENSIC_PROFILES, SERIES_COLORS,
    RAD_AVAILABLE, INF, YEAR_S,
    is_detectable, get_half_life, get_daughters,
    build_chain, get_all_nuclides, secular_equilibrium_ratio,
)


# ══════════════════════════════════════════════════════════════════════════════
#  1. PEAK → ISOTOPE MATCHING
# ══════════════════════════════════════════════════════════════════════════════

def match_peaks_to_isotopes(
    detected_peaks: list[dict],
    tolerance_keV: float = 12.0,
    min_intensity: float = 0.5,
    max_results: int = 20,
) -> list[dict]:
    """
    Match a list of detected peaks against the GAMMA_LINES library.
    Returns isotope matches ranked by confidence score.

    detected_peaks: list of {energy_keV, counts, prominence, ...}
    """
    det_energies = [p["energy_keV"] for p in detected_peaks]
    peak_map     = {p["energy_keV"]: p for p in detected_peaks}

    results = []

    for symbol, lib_lines in GAMMA_LINES.items():
        # Only consider lines above threshold
        sig_lines = [(e,i,n) for e,i,n in lib_lines if e >= 40 and i >= min_intensity]
        if not sig_lines:
            continue

        matched   = []
        unmatched = []

        for lib_kev, lib_int, transition in sig_lines:
            # Find closest detected peak within tolerance
            best_det   = None
            best_delta = tolerance_keV + 1
            for det_kev in det_energies:
                delta = abs(det_kev - lib_kev)
                if delta < best_delta:
                    best_delta = delta
                    best_det   = det_kev

            if best_delta <= tolerance_keV:
                matched.append({
                    "lib_keV":    lib_kev,
                    "det_keV":    best_det,
                    "delta_keV":  round(best_delta, 2),
                    "intensity":  lib_int,
                    "transition": transition,
                    "peak_data":  peak_map.get(best_det, {}),
                })
            else:
                unmatched.append({
                    "lib_keV":    lib_kev,
                    "intensity":  lib_int,
                    "transition": transition,
                })

        if not matched:
            continue

        # ── Confidence score ──────────────────────────────────────────────────
        total_int    = sum(l[1] for l in sig_lines)
        matched_int  = sum(m["intensity"] for m in matched)
        int_coverage = matched_int / total_int if total_int > 0 else 0
        pk_coverage  = len(matched) / len(sig_lines)
        avg_delta    = sum(m["delta_keV"] for m in matched) / len(matched)
        delta_score  = max(0.0, 1.0 - avg_delta / tolerance_keV)

        # Bonus if the strongest library line is matched
        strongest_lib = max(sig_lines, key=lambda x: x[1])
        top_matched   = any(abs(m["lib_keV"] - strongest_lib[0]) < tolerance_keV
                            for m in matched)
        top_bonus     = 0.15 if top_matched else 0.0

        confidence = (0.50 * int_coverage +
                      0.25 * pk_coverage  +
                      0.10 * delta_score  +
                      0.15 * top_bonus)
        confidence = round(min(confidence, 1.0), 4)

        hl_s, hl_r = get_half_life(symbol)
        det, det_r = is_detectable(symbol)

        results.append({
            "symbol":      symbol,
            "confidence":  confidence,
            "pct":         round(confidence * 100, 1),
            "matched":     matched,
            "unmatched":   unmatched,
            "n_matched":   len(matched),
            "n_total":     len(sig_lines),
            "half_life":   hl_r,
            "detectable":  det,
        })

    results.sort(key=lambda x: x["confidence"], reverse=True)
    return results[:max_results]


# ══════════════════════════════════════════════════════════════════════════════
#  2. ALPHA-BLIND PARENT INFERENCE
# ══════════════════════════════════════════════════════════════════════════════

def infer_invisible_parents(
    detected_isotopes: list[str],
    confidence_threshold: float = 0.25,
) -> list[dict]:
    """
    Given a list of isotopes identified from peaks, walk backwards up
    decay chains to infer parent isotopes that are invisible to RC-103
    (alpha emitters, pure beta, low-energy gamma).

    Returns list of inferred parent dicts with supporting evidence.
    """
    detected_set = set(detected_isotopes)
    inferred     = {}

    for detected_sym in detected_set:
        # For each detected isotope, find what invisible parents could produce it
        # by walking the full decay chains of known invisible parents
        for parent_sym in _INVISIBLE_PARENTS:
            chain = build_chain(parent_sym, max_depth=25)
            chain_syms = {m["symbol"] for m in chain}

            if detected_sym not in chain_syms:
                continue

            # How many visible chain members are detected?
            visible_members = [m for m in chain if m["detectable"]]
            detected_visible = [m for m in visible_members
                                if m["symbol"] in detected_set]

            if not detected_visible:
                continue

            coverage = len(detected_visible) / max(len(visible_members), 1)

            if parent_sym not in inferred:
                inferred[parent_sym] = {
                    "parent":           parent_sym,
                    "invisible_reason": is_detectable(parent_sym)[1],
                    "half_life":        get_half_life(parent_sym)[1],
                    "evidence":         [],
                    "chain_coverage":   0.0,
                    "chain_length":     len(chain),
                    "visible_expected": len(visible_members),
                    "visible_detected": 0,
                    "confidence":       0.0,
                }

            entry = inferred[parent_sym]
            for m in detected_visible:
                if m["symbol"] not in [e["symbol"] for e in entry["evidence"]]:
                    entry["evidence"].append({
                        "symbol":    m["symbol"],
                        "half_life": m["half_life"],
                        "gammas":    m["strong_gammas"][:3],
                    })

            entry["visible_detected"] = len(set(
                e["symbol"] for e in entry["evidence"]
            ))
            entry["chain_coverage"]   = round(
                entry["visible_detected"] / max(entry["visible_expected"], 1), 3
            )
            entry["confidence"]       = round(
                min(entry["chain_coverage"] * 1.2, 1.0), 3
            )

    # Filter by threshold and sort
    result = [v for v in inferred.values()
              if v["confidence"] >= confidence_threshold]
    result.sort(key=lambda x: x["confidence"], reverse=True)
    return result


# Isotopes that are invisible to RC-103 but important parents
_INVISIBLE_PARENTS = [
    "U-238","U-234","Th-230","Th-232","Th-228","Ra-224","Ra-228",
    "Rn-222","Rn-220","Po-218","Po-214","Po-210","Po-212","Po-216",
    "Pu-238","Pu-239","Pu-240","Pu-241","Sm-147","Rb-87","Re-187",
    "Np-237","U-235",  # U-235 is detectable but Pu-239→U-235 is an inference chain
]


# ══════════════════════════════════════════════════════════════════════════════
#  3. SECULAR EQUILIBRIUM CHECKER
# ══════════════════════════════════════════════════════════════════════════════

# Expected activity pairs to check for secular equilibrium
# (parent_sym, daughter_sym, equilibrium_condition)
EQUILIBRIUM_PAIRS = [
    # U-238 chain
    ("Ra-226",  "Pb-214",  "Rn-222 must stay in sample"),
    ("Ra-226",  "Bi-214",  "Rn-222 must stay in sample"),
    ("Pb-214",  "Bi-214",  "Short-lived pair — always in equilibrium"),
    ("Th-234",  "Pa-234m", "Very short-lived pair"),
    # Th-232 chain
    ("Ac-228",  "Pb-212",  "Ra-228 → Ac-228 → Th-228 → ... → Pb-212"),
    ("Pb-212",  "Tl-208",  "Bi-212 branch 36% → Tl-208"),
    ("Pb-212",  "Bi-212",  "Direct decay"),
    # U-235 chain
    ("Ra-223",  "Rn-219",  "Short-lived pair"),
]

def check_secular_equilibrium(
    peak_activities: dict[str, float],   # {symbol: CPS}
    sample_age_years: float = 1e6,
) -> list[dict]:
    """
    For each equilibrium pair where both members are detected,
    compare observed activity ratio to expected.

    peak_activities: dict of {isotope_symbol: CPS_value}
    Returns list of equilibrium check results.
    """
    results = []

    for parent, daughter, condition in EQUILIBRIUM_PAIRS:
        a_parent   = peak_activities.get(parent)
        a_daughter = peak_activities.get(daughter)

        if a_parent is None or a_daughter is None:
            continue
        if a_parent <= 0:
            continue

        # Expected ratio at this sample age
        expected_ratio = secular_equilibrium_ratio(parent, daughter, sample_age_years)
        # Correct for Tl-208 branching (36% of Bi-212 → Tl-208)
        if daughter == "Tl-208":
            expected_ratio *= 0.3594

        observed_ratio = a_daughter / a_parent

        # How far from expected? (in fraction)
        if expected_ratio > 0:
            deviation = abs(observed_ratio - expected_ratio) / expected_ratio
        else:
            deviation = 1.0

        status = "equilibrium" if deviation < 0.20 else (
                 "mild deviation" if deviation < 0.50 else "broken")

        results.append({
            "parent":         parent,
            "daughter":       daughter,
            "observed_ratio": round(observed_ratio, 4),
            "expected_ratio": round(expected_ratio, 4),
            "deviation_pct":  round(deviation * 100, 1),
            "status":         status,
            "condition":      condition,
            "interpretation": _equilibrium_interpretation(
                parent, daughter, status, observed_ratio, expected_ratio
            ),
        })

    return results


def _equilibrium_interpretation(parent, daughter, status, obs, exp) -> str:
    if status == "equilibrium":
        return f"{parent}→{daughter}: in secular equilibrium — closed system, undisturbed."
    if status == "broken":
        if obs < exp * 0.5:
            # Daughter depleted
            if "Pb-214" in (parent, daughter) or "Bi-214" in (parent, daughter):
                return (f"{daughter} lower than expected from {parent}: "
                        f"Rn-222 is escaping — sample is open or porous. "
                        f"Observed ratio {obs:.3f} vs expected {exp:.3f}.")
            return (f"{daughter} depleted relative to {parent}: "
                    f"chain may have been chemically separated, or sample is young.")
        else:
            return (f"{daughter} elevated relative to {parent}: "
                    f"transient equilibrium or daughter was externally added.")
    return f"{parent}→{daughter}: mild deviation ({abs(obs-exp)/max(exp,1e-9)*100:.0f}%) — marginal."


# ══════════════════════════════════════════════════════════════════════════════
#  4. CHAIN COMPLETENESS SCORER
# ══════════════════════════════════════════════════════════════════════════════

def score_chain_completeness(
    parent_symbol: str,
    detected_isotopes: list[str],
) -> dict:
    """
    Walk the full decay chain from parent_symbol.
    Score what fraction of the expected detectable members are present.
    Returns completeness dict.
    """
    chain = build_chain(parent_symbol, max_depth=30)
    if not chain:
        return {"error": f"Could not build chain for {parent_symbol}"}

    detectable_members = [m for m in chain if m["detectable"]]
    invisible_members  = [m for m in chain if not m["detectable"]]
    detected_in_chain  = [m for m in detectable_members
                          if m["symbol"] in detected_isotopes]
    missing_detectable = [m for m in detectable_members
                          if m["symbol"] not in detected_isotopes]

    completeness = (len(detected_in_chain) / max(len(detectable_members), 1))

    return {
        "parent":              parent_symbol,
        "chain_length":        len(chain),
        "detectable_expected": len(detectable_members),
        "detectable_found":    len(detected_in_chain),
        "missing_detectable":  missing_detectable,
        "invisible_members":   invisible_members,
        "completeness_pct":    round(completeness * 100, 1),
        "detected_members":    detected_in_chain,
        "full_chain":          chain,
        "interpretation":      _completeness_interpretation(
            parent_symbol, completeness, missing_detectable, detected_in_chain
        ),
    }


def _completeness_interpretation(parent, completeness, missing, detected) -> str:
    if completeness >= 0.85:
        return f"Chain is essentially complete — {parent} present and in equilibrium."
    if completeness >= 0.50:
        missing_names = ", ".join(m["symbol"] for m in missing[:4])
        return (f"Partial chain — {completeness*100:.0f}% complete. "
                f"Missing: {missing_names}. "
                f"Possible Rn escape, chemical separation, or young sample.")
    if completeness >= 0.20:
        det_names = ", ".join(m["symbol"] for m in detected[:3])
        return (f"Weak chain signature — only {det_names} detected. "
                f"Chain significantly disrupted or {parent} activity is very low.")
    return (f"Very incomplete chain — only {completeness*100:.0f}% detected. "
            f"May be trace contamination rather than primary {parent} source.")


# ══════════════════════════════════════════════════════════════════════════════
#  5. ANOMALY DETECTOR
# ══════════════════════════════════════════════════════════════════════════════

def detect_anomalies(
    detected_isotopes: list[str],
    detected_peaks: list[dict],
    sample_age_years: float = 1e6,
) -> list[dict]:
    """
    Flag things that SHOULD be visible but aren't, and things that
    SHOULDN'T be present together.
    """
    detected_set = set(detected_isotopes)
    anomalies    = []

    # ── Rule 1: Rn-222 escape ─────────────────────────────────────────────────
    has_ra226 = "Ra-226" in detected_set
    has_pb214 = "Pb-214" in detected_set
    has_bi214 = "Bi-214" in detected_set
    if has_ra226 and not (has_pb214 or has_bi214):
        anomalies.append({
            "type":   "chain_break",
            "level":  "high",
            "title":  "Rn-222 escape detected",
            "detail": ("Ra-226 is present but Pb-214 and Bi-214 are absent. "
                       "Rn-222 gas is escaping from the sample before decaying to "
                       "its solid daughters. The sample is open, porous, or a gas-permeable "
                       "container. CONTAMINATION RISK if indoors."),
        })

    # ── Rule 2: Th-232 chain broken ───────────────────────────────────────────
    has_ac228 = "Ac-228"  in detected_set
    has_tl208 = "Tl-208"  in detected_set
    has_pb212 = "Pb-212"  in detected_set
    if has_ac228 and not (has_tl208 or has_pb212):
        anomalies.append({
            "type":   "chain_break",
            "level":  "medium",
            "title":  "Th-232 chain interrupted (Ac-228 without Tl-208/Pb-212)",
            "detail": ("Ac-228 detected but Tl-208 and Pb-212 are absent. "
                       "The Th-232 chain is broken between Ra-224/Rn-220 and Pb-212. "
                       "This can occur if the sample was recently chemically processed "
                       "or if Rn-220 (thoron) is escaping."),
        })

    # ── Rule 3: Cs-134 present in old sample ─────────────────────────────────
    if "Cs-134" in detected_set:
        # Cs-134 t½=2.065y — if sample age > 20y, Cs-134 should be gone
        hl_cs134 = 2.065 * YEAR_S
        surviving = math.exp(-math.log(2) * sample_age_years * YEAR_S / hl_cs134)
        if sample_age_years > 20 and surviving < 0.001:
            anomalies.append({
                "type":   "unexpected_isotope",
                "level":  "high",
                "title":  "Cs-134 detected in old sample — recent irradiation implied",
                "detail": (f"Cs-134 (t½=2.06y) should be effectively gone in a "
                           f"{sample_age_years:.0f}-year-old sample. Its presence implies "
                           f"very recent reactor irradiation or nuclear incident exposure "
                           f"(within the last ~15 years)."),
            })

    # ── Rule 4: Am-241 without explanation ───────────────────────────────────
    if "Am-241" in detected_set:
        has_u238_chain = any(s in detected_set for s in ["Bi-214","Pb-214","Th-234"])
        has_fission    = any(s in detected_set for s in ["Cs-137","Cs-134","Co-60"])
        if not (has_u238_chain or has_fission):
            anomalies.append({
                "type":   "unexpected_isotope",
                "level":  "medium",
                "title":  "Am-241 detected in isolation",
                "detail": ("Am-241 detected without accompanying U-238 chain or fission products. "
                           "Possible sources: smoke detector (check for isolated 59.5 keV only), "
                           "Pu-241 decay product in aged nuclear material, or Am-241 sealed source."),
            })

    # ── Rule 5: High-energy peak without Th-232 chain ────────────────────────
    has_2614 = any(abs(p["energy_keV"] - 2614.5) < 15 for p in detected_peaks)
    if has_2614 and not has_tl208:
        # Tl-208 should have been matched if 2614 peak was detected
        anomalies.append({
            "type":   "identification_note",
            "level":  "low",
            "title":  "Peak near 2614 keV detected — probable Tl-208",
            "detail": ("A peak near 2614.5 keV is almost certainly Tl-208, "
                       "the highest naturally-occurring gamma line and a definitive "
                       "Th-232 chain marker. Ensure Tl-208 is in your match results."),
        })

    # ── Rule 6: Pa-234m (1001 keV) without Ra-226 / Bi-214 ──────────────────
    if "Pa-234m" in detected_set and not (has_ra226 or has_bi214):
        anomalies.append({
            "type":   "chain_break",
            "level":  "medium",
            "title":  "Pa-234m detected but lower U-238 chain members absent",
            "detail": ("Pa-234m at 1001 keV confirms U-238 is present. "
                       "However, Ra-226 and its progeny (Pb-214, Bi-214) are not detected. "
                       "This may indicate a young ore sample (Ra-226 not yet built up), "
                       "or the sample has been chemically processed to remove radium."),
        })

    # ── Rule 7: Co-60 doublet completeness ───────────────────────────────────
    has_1173 = any(abs(p["energy_keV"] - 1173.2) < 15 for p in detected_peaks)
    has_1332 = any(abs(p["energy_keV"] - 1332.5) < 15 for p in detected_peaks)
    if has_1173 != has_1332:  # One but not both
        anomalies.append({
            "type":   "identification_note",
            "level":  "medium",
            "title":  "Co-60 doublet incomplete",
            "detail": ("Co-60 always emits both 1173.2 keV and 1332.5 keV in near-100% cascade. "
                       "Detecting only one of these peaks suggests the other may be obscured, "
                       "or the peak is a different isotope (e.g., 1120 keV = Bi-214, "
                       "1333 keV could be Co-60 or overlap)."),
        })

    return anomalies


# ══════════════════════════════════════════════════════════════════════════════
#  6. FORENSIC PROFILE MATCHER
# ══════════════════════════════════════════════════════════════════════════════

def match_forensic_profile(
    detected_isotopes: list[str],
    profile_name: str,
    detected_peaks: list[dict] = None,
) -> dict:
    """
    Score a spectrum against a named forensic profile.
    Returns a detailed authentication report.
    """
    profile      = FORENSIC_PROFILES[profile_name]
    detected_set = set(detected_isotopes)
    weights      = profile["score_weights"]

    # ── Score detected isotopes ───────────────────────────────────────────────
    achieved   = {}
    missing    = {}
    total_w    = sum(weights.values())
    scored     = 0

    for sym, w in weights.items():
        if sym in detected_set:
            achieved[sym] = w
            scored += w
        else:
            missing[sym] = w

    score_pct = round(scored / total_w * 100, 1) if total_w > 0 else 0.0

    # ── Check expected groups ─────────────────────────────────────────────────
    group_results = []
    for group_name, group_isos, group_desc in profile["expected"]:
        found   = [s for s in group_isos if s in detected_set]
        missing_g = [s for s in group_isos if s not in detected_set]
        group_results.append({
            "group":    group_name,
            "desc":     group_desc,
            "expected": group_isos,
            "found":    found,
            "missing":  missing_g,
            "complete": len(found) == len(group_isos),
            "partial":  0 < len(found) < len(group_isos),
            "absent":   len(found) == 0,
        })

    # ── Alpha-blind inferences ────────────────────────────────────────────────
    ab_results = []
    for ab in profile.get("alpha_blind", []):
        evidence_found = [e for e in ab["evidence"] if e in detected_set]
        confidence     = len(evidence_found) / max(len(ab["evidence"]), 1)
        ab_results.append({
            "inferred":       ab["inferred"],
            "evidence_needed":ab["evidence"],
            "evidence_found": evidence_found,
            "confidence":     round(confidence, 2),
            "logic":          ab["logic"],
        })

    # ── Anomaly flags ─────────────────────────────────────────────────────────
    triggered_flags = []
    for flag_title, flag_detail in profile["anomaly_flags"]:
        # Simple heuristic: check if the flag condition is triggered
        flag_triggered = _check_flag(flag_title, detected_set, detected_peaks or [])
        if flag_triggered:
            triggered_flags.append({"title": flag_title, "detail": flag_detail})

    # ── Overall verdict ───────────────────────────────────────────────────────
    verdict, verdict_color = _score_to_verdict(score_pct, triggered_flags)

    return {
        "profile_name":   profile_name,
        "description":    profile["description"],
        "score":          score_pct,
        "verdict":        verdict,
        "verdict_color":  verdict_color,
        "achieved":       achieved,
        "missing":        missing,
        "group_results":  group_results,
        "alpha_blind":    ab_results,
        "anomaly_flags":  triggered_flags,
    }


def _check_flag(flag_title: str, detected: set, peaks: list) -> bool:
    """Heuristic flag trigger check."""
    t = flag_title.lower()
    if "no am-241"   in t: return "Am-241"  not in detected
    if "no cs-137"   in t: return "Cs-137"  not in detected
    if "no eu"       in t: return not any(s in detected for s in ["Eu-152","Eu-154","Eu-155"])
    if "cs-134 at significant" in t: return "Cs-134" in detected
    if "no tl-208"   in t: return "Tl-208"  not in detected
    if "no cs-137"   in t: return "Cs-137"  not in detected
    if "ra-226 detected but bi-214" in t:
        return "Ra-226" in detected and "Bi-214" not in detected
    if "co-60 without" in t:
        return "Co-60" in detected and "Cs-137" not in detected
    if "strong bi-214 without" in t:
        return "Bi-214" in detected and "Tl-208" not in detected
    if "additional peaks" in t:
        return len(detected) > 2
    return False


def _score_to_verdict(score: float, flags: list) -> tuple[str, str]:
    has_major = any("MAJOR" in f["title"] or "MAJOR" in f.get("detail","")
                    for f in flags)
    if has_major:
        return ("AUTHENTICATION CONCERNS — major anomaly flags triggered", "#c0392b")
    if score >= 75:
        return ("STRONGLY CONSISTENT with profile", "#27ae60")
    if score >= 50:
        return ("CONSISTENT with profile — some signatures missing", "#d4a843")
    if score >= 25:
        return ("PARTIALLY CONSISTENT — significant signatures absent", "#e8a060")
    return ("INCONSISTENT with profile — does not match expected signatures", "#c0392b")


# ══════════════════════════════════════════════════════════════════════════════
#  7. NUCLIDE SEARCH
# ══════════════════════════════════════════════════════════════════════════════

def search_nuclides(query: str, limit: int = 30) -> list[dict]:
    """
    Search all nuclides by symbol or partial name.
    Returns list of nuclide info dicts.
    """
    query   = query.strip().lower()
    all_sym = get_all_nuclides()
    matches = []

    for sym in all_sym:
        if query in sym.lower():
            hl_s, hl_r = get_half_life(sym)
            det, det_r = is_detectable(sym)
            daughters  = get_daughters(sym)
            gammas     = GAMMA_LINES.get(sym, [])
            matches.append({
                "symbol":    sym,
                "half_life": hl_r,
                "detectable":det,
                "detect_reason": det_r,
                "daughters": [(d,round(bf*100,2),m) for d,bf,m in daughters],
                "gammas":    sorted(gammas, key=lambda x: x[1], reverse=True)[:6],
                "n_gammas":  len(gammas),
            })
        if len(matches) >= limit:
            break

    return matches


def get_nuclide_full(symbol: str) -> dict:
    """Full data for a single nuclide."""
    hl_s, hl_r = get_half_life(symbol)
    det, det_r = is_detectable(symbol)
    daughters  = get_daughters(symbol)
    gammas     = sorted(GAMMA_LINES.get(symbol, []),
                        key=lambda x: x[1], reverse=True)
    chain      = build_chain(symbol, max_depth=20)
    return {
        "symbol":     symbol,
        "half_life":  hl_r,
        "half_life_s":hl_s,
        "detectable": det,
        "detect_reason": det_r,
        "daughters":  [(d, round(bf*100,2), m) for d,bf,m in daughters],
        "gammas":     gammas,
        "chain":      chain,
    }
