"""
activity_calculator.py  —  Convert peak areas to activities (Bq, Bq/g, Bq/kg)
────────────────────────────────────────────────────────────────────────────────
Uses: net peak area + efficiency calibration + gamma yield + sample mass

  A [Bq] = N_net / (ε(E) × I_γ × t_live)

where:
  N_net  = net counts under peak  (from Gaussian fit)
  ε(E)   = full-energy peak efficiency at energy E
  I_γ    = absolute gamma emission probability (from isotope library)
  t_live = live measurement time (seconds)
"""

from __future__ import annotations
import numpy as np
from dataclasses import dataclass, field
from typing import Optional

from efficiency_cal import EfficiencyCurve
from peak_fitting   import FittedPeak


# ══════════════════════════════════════════════════════════════════════════════
#  DATA CLASSES
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ActivityResult:
    isotope:         str
    energy_keV:      float
    gamma_yield:     float       # I_γ (fraction, 0–1)
    net_counts:      float
    count_rate_cps:  float
    efficiency:      float       # ε(E)
    efficiency_unc:  float
    activity_bq:     float       # A in Bq
    activity_unc_bq: float       # 1σ combined uncertainty
    activity_bq_g:   Optional[float] = None   # Bq/g  (if mass given)
    activity_bq_kg:  Optional[float] = None   # Bq/kg
    activity_unc_g:  Optional[float] = None
    specific_activity_ref: Optional[float] = None  # reference value (Bq/g)
    ratio_to_ref:    Optional[float] = None
    live_time_s:     float = 0.0
    sample_mass_g:   float = 0.0
    fit_chi2:        float = 0.0
    notes:           str   = ""


@dataclass
class ActivityReport:
    """Full activity report for one spectrum."""
    sample_name:     str
    live_time_s:     float
    sample_mass_g:   float
    results:         list[ActivityResult] = field(default_factory=list)
    total_activity_bq: float = 0.0
    geometry:        str   = ""
    efficiency_curve: str  = ""
    warnings:        list  = field(default_factory=list)


# ══════════════════════════════════════════════════════════════════════════════
#  REFERENCE SPECIFIC ACTIVITIES  (Bq/g, secular equilibrium with primordial)
# ══════════════════════════════════════════════════════════════════════════════

REFERENCE_SPECIFIC_ACTIVITIES: dict[str, float] = {
    # Natural concentrations in average crustal rock (Bq/g)
    "K-40":   0.850e-3,    # ~850 Bq/kg
    "U-238":  25.3e-6,     # ~25 Bq/kg for 1 ppm U
    "Th-232": 4.06e-6,     # ~4 Bq/kg for 1 ppm Th
    "Ra-226": 25.3e-6,     # in equilibrium with U-238
    "Pb-210": 25.3e-6,
    "Bi-214": 25.3e-6,
    "Pb-214": 25.3e-6,
    "Tl-208": 4.06e-6,
    "Bi-212": 4.06e-6,
    "Pb-212": 4.06e-6,
    "Cs-137": 0.0,         # anthropogenic, no "natural" level
    "Co-60":  0.0,
    "Am-241": 0.0,
}


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN CALCULATION
# ══════════════════════════════════════════════════════════════════════════════

def calculate_activity(
        isotope:        str,
        energy_kev:     float,
        gamma_yield:    float,
        fitted_peak:    FittedPeak,
        efficiency_curve: EfficiencyCurve,
        live_time_s:    float,
        sample_mass_g:  float = 0.0,
) -> ActivityResult:
    """
    Calculate activity for a single isotope peak.

    Parameters
    ----------
    isotope         : symbol, e.g. "Cs-137"
    energy_kev      : gamma line energy (keV)
    gamma_yield     : absolute emission probability (0–1), e.g. 0.851 for Cs-137
    fitted_peak     : FittedPeak from peak_fitting.fit_peak()
    efficiency_curve: EfficiencyCurve from efficiency_cal
    live_time_s     : measurement live time in seconds
    sample_mass_g   : sample mass in grams (0 = not specified)
    """
    result = ActivityResult(
        isotope        = isotope,
        energy_keV     = energy_kev,
        gamma_yield    = gamma_yield,
        net_counts     = fitted_peak.area_net,
        count_rate_cps = fitted_peak.area_net / max(live_time_s, 1),
        efficiency     = 0.0,
        efficiency_unc = 0.0,
        activity_bq    = 0.0,
        activity_unc_bq= 0.0,
        live_time_s    = live_time_s,
        sample_mass_g  = sample_mass_g,
        fit_chi2       = fitted_peak.chi2_reduced,
    )

    if not fitted_peak.fit_ok:
        result.notes = f"Peak fit failed: {fitted_peak.fit_message}"
        return result

    # Look up efficiency
    eff = efficiency_curve.efficiency_at(energy_kev)
    if eff is None or eff <= 0:
        result.notes = (f"Energy {energy_kev} keV outside calibration range "
                        f"{efficiency_curve.energy_range}")
        return result

    eff_unc = efficiency_curve.uncertainty_at(energy_kev)
    result.efficiency     = round(eff,     6)
    result.efficiency_unc = round(eff_unc, 6)

    # Core calculation: A = N_net / (ε × I_γ × t_live)
    denominator = eff * gamma_yield * live_time_s
    if denominator <= 0:
        result.notes = "Zero denominator (ε × I_γ × t = 0)"
        return result

    activity = fitted_peak.area_net / denominator

    # Combined uncertainty (quadrature sum of fractional uncertainties)
    frac_count = fitted_peak.area_uncertainty / max(fitted_peak.area_net, 1)
    frac_eff   = eff_unc / max(eff, 1e-10)
    frac_yield = 0.005   # assume 0.5% yield uncertainty
    total_frac = np.sqrt(frac_count**2 + frac_eff**2 + frac_yield**2)
    activity_unc = activity * total_frac

    result.activity_bq     = round(float(activity),     3)
    result.activity_unc_bq = round(float(activity_unc), 3)

    # Specific activity (per gram)
    if sample_mass_g > 0:
        result.activity_bq_g   = round(activity     / sample_mass_g, 6)
        result.activity_bq_kg  = round(activity     / sample_mass_g * 1000, 4)
        result.activity_unc_g  = round(activity_unc / sample_mass_g, 6)

        # Compare to reference
        ref = REFERENCE_SPECIFIC_ACTIVITIES.get(isotope)
        if ref and ref > 0:
            result.specific_activity_ref = ref
            result.ratio_to_ref = round(result.activity_bq_g / ref, 2)

    return result


def calculate_all_activities(
        identified_isotopes: list[dict],
        fitted_peaks:        list[FittedPeak],
        efficiency_curve:    EfficiencyCurve,
        live_time_s:         float,
        sample_mass_g:       float = 0.0,
        sample_name:         str   = "",
) -> ActivityReport:
    """
    Calculate activities for all identified isotopes in a spectrum.

    identified_isotopes: list of match dicts from inference_engine
    fitted_peaks:        list of FittedPeak from peak_fitting
    """
    report = ActivityReport(
        sample_name    = sample_name,
        live_time_s    = live_time_s,
        sample_mass_g  = sample_mass_g,
        efficiency_curve = efficiency_curve.geometry,
    )

    # Build a lookup: energy_keV → FittedPeak
    peak_by_energy: dict[float, FittedPeak] = {}
    for fp in fitted_peaks:
        if fp.fit_ok:
            # Round to nearest 0.5 keV for matching
            key = round(fp.energy_keV * 2) / 2
            peak_by_energy[key] = fp

    for iso_match in identified_isotopes:
        symbol   = iso_match.get("isotope", "")
        matched  = iso_match.get("matched", [])

        # Use the strongest matched line
        if not matched:
            continue
        best_match = max(matched, key=lambda x: x.get("intensity", 0))
        lib_kev    = best_match.get("lib_keV", 0)
        intensity  = best_match.get("intensity", 0) / 100.0  # % → fraction
        det_kev    = best_match.get("det_keV", lib_kev)

        # Find fitted peak
        key = round(det_kev * 2) / 2
        fp  = peak_by_energy.get(key)
        if fp is None:
            # Try nearest within 2 keV
            for k, p in peak_by_energy.items():
                if abs(k - det_kev) < 2.0:
                    fp = p
                    break
        if fp is None:
            report.warnings.append(f"{symbol}: no fitted peak at {det_kev} keV")
            continue

        result = calculate_activity(
            isotope         = symbol,
            energy_kev      = lib_kev,
            gamma_yield     = intensity,
            fitted_peak     = fp,
            efficiency_curve= efficiency_curve,
            live_time_s     = live_time_s,
            sample_mass_g   = sample_mass_g,
        )
        report.results.append(result)

    # Total activity
    report.total_activity_bq = round(
        sum(r.activity_bq for r in report.results if r.activity_bq > 0), 2
    )
    return report


# ══════════════════════════════════════════════════════════════════════════════
#  UNIT CONVERSIONS
# ══════════════════════════════════════════════════════════════════════════════

def bq_to_uci(bq: float) -> float:
    return bq / 37000.0

def bq_to_dpm(bq: float) -> float:
    return bq * 60.0

def bq_to_mrem_h(bq: float, energy_kev: float, distance_cm: float = 100.0) -> float:
    """
    Very rough dose rate estimate (mrem/h) at distance_cm.
    Uses Γ ≈ 0.5 × E[MeV] × I_γ  (R·h⁻¹·Ci⁻¹·m² approximation).
    """
    ci = bq / 3.7e10
    e_mev = energy_kev / 1000
    gamma_factor = 0.5 * e_mev  # R/(h·Ci) at 1 m
    dose_r_h = ci * gamma_factor / (distance_cm / 100)**2
    return dose_r_h * 1000  # R → mR, then ≈ mrem
