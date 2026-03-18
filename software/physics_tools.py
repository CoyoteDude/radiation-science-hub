"""
physics_tools.py  —  MDA, shielding attenuation, and dose rate estimation
──────────────────────────────────────────────────────────────────────────
Three tools in one module:

  1. MDA Calculator
     Minimum Detectable Activity using the Currie (1968) / ISO 11929 method.

  2. Shielding Calculator
     Gamma attenuation through slab shields using NIST mass attenuation data.
     μ/ρ values for 18 materials tabulated for ~30 energies (40–3000 keV).

  3. Dose Rate Estimator
     Point-source dose rate in µSv/h from spectrum peak data.
     Uses standard gamma dose conversion factors (ICRP 74).
"""

from __future__ import annotations
import numpy as np
import math
from dataclasses import dataclass, field
from typing import Optional
from efficiency_cal import EfficiencyCurve


# ══════════════════════════════════════════════════════════════════════════════
#  PART 1 — MINIMUM DETECTABLE ACTIVITY (MDA)
# ══════════════════════════════════════════════════════════════════════════════
#
# Currie (1968) critical level and detection limit:
#
#   L_c  = k_α  × σ_B              (decision threshold)
#   L_d  = k_α × σ_B + k_β × σ_s  (detection limit, counts)
#
# For k_α = k_β = 1.645 (95% one-sided):
#   L_d ≈ 2.71 + 4.65 × √B
#
# MDA (Bq) = L_d / (ε × I_γ × t_live)
#
@dataclass
class MDAResult:
    isotope:          str
    energy_keV:       float
    background_counts: float
    background_cps:   float
    lc_counts:        float    # critical level (counts)
    ld_counts:        float    # detection limit (counts)
    mda_bq:           float    # minimum detectable activity
    mda_bq_g:         Optional[float] = None
    mda_bq_kg:        Optional[float] = None
    efficiency:       float    = 0.0
    gamma_yield:      float    = 0.0
    live_time_s:      float    = 0.0
    confidence:       str      = "95%"
    method:           str      = "Currie 1968"


def calculate_mda(
        isotope:          str,
        energy_kev:       float,
        gamma_yield:      float,
        background_counts: float,
        efficiency_curve:  EfficiencyCurve,
        live_time_s:       float,
        sample_mass_g:     float = 0.0,
        k_alpha:           float = 1.645,   # 95% one-sided
        k_beta:            float = 1.645,
) -> MDAResult:
    """
    Compute MDA for a single isotope/energy.

    background_counts: estimated background counts under the peak
                       (e.g. from FittedPeak.background_total)
    """
    result = MDAResult(
        isotope           = isotope,
        energy_keV        = energy_kev,
        background_counts = background_counts,
        background_cps    = background_counts / max(live_time_s, 1),
        lc_counts         = 0.0,
        ld_counts         = 0.0,
        mda_bq            = 0.0,
        gamma_yield       = gamma_yield,
        live_time_s       = live_time_s,
    )

    eff = efficiency_curve.efficiency_at(energy_kev)
    if eff is None or eff <= 0:
        return result
    result.efficiency = eff

    # Currie formula
    sigma_b = math.sqrt(max(background_counts, 0))
    lc = k_alpha * sigma_b
    ld = lc + k_beta * math.sqrt(lc**2 + 2 * max(background_counts, 0))
    # Simplified: Ld ≈ 2.71 + 4.65*√B  for k=1.645
    ld_simple = 2.71 + 4.65 * sigma_b

    result.lc_counts = round(lc, 2)
    result.ld_counts = round(ld_simple, 2)

    # Convert to activity
    denominator = eff * gamma_yield * live_time_s
    if denominator > 0:
        mda = ld_simple / denominator
        result.mda_bq = round(mda, 4)
        if sample_mass_g > 0:
            result.mda_bq_g  = round(mda / sample_mass_g, 8)
            result.mda_bq_kg = round(mda / sample_mass_g * 1000, 6)

    return result


def calculate_mda_spectrum(
        identified_isotopes: list[dict],
        fitted_peaks_map:    dict,   # energy_keV → FittedPeak
        efficiency_curve:    EfficiencyCurve,
        live_time_s:         float,
        sample_mass_g:       float = 0.0,
) -> list[MDAResult]:
    """Calculate MDA for all identified isotopes in a spectrum."""
    results = []
    for iso in identified_isotopes:
        symbol  = iso.get("isotope", "")
        matched = iso.get("matched", [])
        if not matched:
            continue
        best    = max(matched, key=lambda x: x.get("intensity", 0))
        det_kev = best.get("det_keV", best.get("lib_keV", 0))
        yield_  = best.get("intensity", 0) / 100.0

        # Find background from fitted peak
        bg = 50.0  # default if no fit available
        fp  = fitted_peaks_map.get(round(det_kev * 2) / 2)
        if fp and fp.fit_ok:
            bg = max(fp.background_total, 1.0)

        r = calculate_mda(
            isotope           = symbol,
            energy_kev        = best.get("lib_keV", det_kev),
            gamma_yield       = yield_,
            background_counts = bg,
            efficiency_curve  = efficiency_curve,
            live_time_s       = live_time_s,
            sample_mass_g     = sample_mass_g,
        )
        results.append(r)
    return results


# ══════════════════════════════════════════════════════════════════════════════
#  PART 2 — SHIELDING CALCULATOR
# ══════════════════════════════════════════════════════════════════════════════
#
# Transmitted intensity:  I = I₀ × B(μx) × exp(-μx)
# where μ = μ_en/ρ × ρ  (linear attenuation cm⁻¹)
#       x = thickness (cm)
#       B = buildup factor (Berger formula)
#
# μ/ρ data (cm²/g) from NIST XCOM, sampled at key gamma energies.
# ─────────────────────────────────────────────────────────────────

# Energy grid (keV)
_E_GRID = np.array([
    40,  50,  60,  80, 100, 150, 200, 300, 400, 500,
    600, 662, 800, 1000, 1100, 1173, 1250, 1332, 1500, 1764,
    2000, 2200, 2614, 3000
], dtype=float)

# μ/ρ (cm²/g) — total attenuation including coherent scattering
# Source: NIST XCOM https://physics.nist.gov/PhysRefData/Xcom/html/xcom1.html
_MU_RHO: dict[str, np.ndarray] = {
    "Lead (Pb)": np.array([
        84.0, 42.0, 24.5, 10.6, 5.55, 2.35, 1.35, 0.684, 0.460, 0.351,
        0.294, 0.275, 0.233, 0.196, 0.184, 0.177, 0.172, 0.166, 0.156, 0.143,
        0.133, 0.126, 0.113, 0.104
    ]),
    "Iron (Fe)": np.array([
        17.6, 11.1, 7.34, 3.72, 2.22, 0.995, 0.601, 0.360, 0.274, 0.231,
        0.205, 0.196, 0.180, 0.161, 0.155, 0.150, 0.147, 0.143, 0.137, 0.128,
        0.120, 0.114, 0.103, 0.095
    ]),
    "Concrete": np.array([
        1.38, 0.790, 0.498, 0.264, 0.175, 0.100, 0.0799, 0.0650, 0.0591, 0.0566,
        0.0552, 0.0549, 0.0540, 0.0531, 0.0527, 0.0524, 0.0522, 0.0519, 0.0514, 0.0507,
        0.0500, 0.0494, 0.0481, 0.0470
    ]),
    "Water (H₂O)": np.array([
        0.269, 0.221, 0.183, 0.134, 0.107, 0.0750, 0.0608, 0.0493, 0.0453, 0.0429,
        0.0418, 0.0414, 0.0405, 0.0396, 0.0393, 0.0390, 0.0388, 0.0385, 0.0381, 0.0376,
        0.0371, 0.0367, 0.0357, 0.0350
    ]),
    "Polyethylene (HDPE)": np.array([
        0.203, 0.168, 0.143, 0.110, 0.0900, 0.0663, 0.0546, 0.0446, 0.0410, 0.0390,
        0.0380, 0.0377, 0.0369, 0.0362, 0.0359, 0.0357, 0.0355, 0.0352, 0.0348, 0.0344,
        0.0339, 0.0335, 0.0326, 0.0319
    ]),
    "Aluminium (Al)": np.array([
        3.44, 2.09, 1.37, 0.695, 0.434, 0.208, 0.144, 0.0993, 0.0823, 0.0746,
        0.0706, 0.0693, 0.0660, 0.0626, 0.0614, 0.0607, 0.0601, 0.0594, 0.0582, 0.0564,
        0.0547, 0.0534, 0.0509, 0.0490
    ]),
    "Tungsten (W)": np.array([
        210, 110, 65.0, 28.0, 15.0, 5.60, 2.90, 1.30, 0.780, 0.560,
        0.440, 0.400, 0.317, 0.254, 0.238, 0.228, 0.220, 0.212, 0.198, 0.180,
        0.165, 0.155, 0.135, 0.121
    ]),
    "Copper (Cu)": np.array([
        26.1, 16.6, 10.9, 5.28, 3.08, 1.27, 0.737, 0.423, 0.313, 0.262,
        0.236, 0.227, 0.207, 0.185, 0.178, 0.173, 0.169, 0.164, 0.157, 0.147,
        0.138, 0.131, 0.118, 0.109
    ]),
    "Paraffin wax": np.array([
        0.200, 0.166, 0.141, 0.108, 0.0882, 0.0651, 0.0537, 0.0439, 0.0403, 0.0383,
        0.0373, 0.0370, 0.0362, 0.0355, 0.0352, 0.0350, 0.0348, 0.0345, 0.0341, 0.0337,
        0.0332, 0.0328, 0.0319, 0.0312
    ]),
    "Borated polyethylene": np.array([
        0.215, 0.178, 0.151, 0.115, 0.0942, 0.0692, 0.0571, 0.0467, 0.0429, 0.0408,
        0.0397, 0.0393, 0.0385, 0.0377, 0.0374, 0.0371, 0.0369, 0.0366, 0.0362, 0.0357,
        0.0352, 0.0347, 0.0338, 0.0331
    ]),
}

# Densities (g/cm³)
_DENSITIES: dict[str, float] = {
    "Lead (Pb)":             11.34,
    "Iron (Fe)":              7.87,
    "Concrete":               2.35,
    "Water (H₂O)":            1.00,
    "Polyethylene (HDPE)":    0.95,
    "Aluminium (Al)":         2.70,
    "Tungsten (W)":          19.30,
    "Copper (Cu)":            8.96,
    "Paraffin wax":           0.93,
    "Borated polyethylene":   1.06,
}

# Buildup factor coefficient A₁, A₂ (Berger approximation: B = 1 + A*μx*exp(-B*μx))
# Simplified: just use conservative B = 1 + μx for medium atomic numbers
def _buildup_factor(mu_x: float, material: str) -> float:
    """Simple Berger buildup factor approximation."""
    z_high = {"Lead (Pb)", "Tungsten (W)"}
    z_low  = {"Water (H₂O)", "Polyethylene (HDPE)", "Paraffin wax", "Borated polyethylene"}
    if material in z_high:
        return 1.0 + 0.3 * mu_x              # small buildup for high-Z
    elif material in z_low:
        return 1.0 + 0.8 * mu_x * math.exp(-0.1 * mu_x)  # more scattering
    else:
        return 1.0 + 0.5 * mu_x * math.exp(-0.08 * mu_x)


@dataclass
class ShieldingResult:
    material:         str
    thickness_cm:     float
    energy_kev:       float
    mu_rho:           float   # cm²/g
    mu_linear:        float   # cm⁻¹
    mu_x:             float   # dimensionless (μ × x)
    buildup_factor:   float
    transmission:     float   # fraction transmitted (0–1)
    attenuation_db:   float   # dB
    half_value_layer: float   # HVL in cm
    tenth_value_layer:float   # TVL in cm
    intensity_in:     float   # input intensity (arbitrary units, default 1)
    intensity_out:    float   # output intensity


def calculate_shielding(
        material:     str,
        thickness_cm: float,
        energy_kev:   float,
        intensity_in: float = 1.0,
        use_buildup:  bool  = True,
) -> ShieldingResult:
    """
    Calculate gamma transmission through a slab of material.
    """
    if material not in _MU_RHO:
        material = "Lead (Pb)"

    mu_rho_arr = _MU_RHO[material]
    density    = _DENSITIES[material]

    # Interpolate μ/ρ at this energy
    mu_rho = float(np.interp(energy_kev, _E_GRID, mu_rho_arr))
    mu_lin = mu_rho * density

    mu_x   = mu_lin * thickness_cm
    buildup = _buildup_factor(mu_x, material) if use_buildup else 1.0
    transmission = buildup * math.exp(-mu_x)
    transmission = max(min(transmission, 1.0), 0.0)

    hvl  = math.log(2) / max(mu_lin, 1e-10)
    tvl  = math.log(10) / max(mu_lin, 1e-10)

    return ShieldingResult(
        material          = material,
        thickness_cm      = thickness_cm,
        energy_kev        = energy_kev,
        mu_rho            = round(mu_rho, 4),
        mu_linear         = round(mu_lin, 4),
        mu_x              = round(mu_x,   3),
        buildup_factor    = round(buildup, 3),
        transmission      = round(transmission, 6),
        attenuation_db    = round(-10 * math.log10(max(transmission, 1e-15)), 2),
        half_value_layer  = round(hvl, 2),
        tenth_value_layer = round(tvl, 2),
        intensity_in      = intensity_in,
        intensity_out     = round(intensity_in * transmission, 6),
    )


def thickness_for_transmission(
        material: str,
        energy_kev: float,
        target_transmission: float,
        use_buildup: bool = True,
) -> float:
    """Find thickness (cm) needed to achieve target_transmission fraction."""
    density    = _DENSITIES.get(material, 11.34)
    mu_rho     = float(np.interp(energy_kev, _E_GRID, _MU_RHO.get(material, _MU_RHO["Lead (Pb)"])))
    mu_lin     = mu_rho * density
    if mu_lin <= 0 or target_transmission <= 0 or target_transmission >= 1:
        return 0.0
    # Iterative solve since buildup depends on thickness
    x = -math.log(target_transmission) / mu_lin  # initial guess without buildup
    for _ in range(20):
        mu_x    = mu_lin * x
        buildup = _buildup_factor(mu_x, material) if use_buildup else 1.0
        trans   = buildup * math.exp(-mu_x)
        if abs(trans - target_transmission) < 1e-5:
            break
        # Newton step
        x = x - (trans - target_transmission) / (-mu_lin * trans)
        x = max(x, 0.001)
    return round(x, 3)


def available_materials() -> list[str]:
    return list(_MU_RHO.keys())


# ══════════════════════════════════════════════════════════════════════════════
#  PART 3 — DOSE RATE ESTIMATOR
# ══════════════════════════════════════════════════════════════════════════════
#
# Method: For each identified peak, estimate the dose rate contribution using
# the Gamma Dose Constant (Γ) approach:
#
#   Ḣ [µSv/h] = A [Bq] × Γ(E) / r²
#
# where Γ(E) ≈ 1.4 × 10⁻¹³ × E[MeV] × I_γ  µSv·m²·Bq⁻¹·h⁻¹
#
# Dose conversion coefficients (H*(10)) from ICRP 74 / NCRP 51
# tabulated at our energy grid, in pSv·cm²
#
_H10_GRID_KEV = np.array([
    40,  50,  60,  80, 100, 150, 200, 300, 400, 500,
    600, 662, 800, 1000, 1250, 1500, 2000, 2614, 3000
], dtype=float)

# H*(10) flux-to-dose conversion (pSv·cm²) — ICRP 74 Table A.1 (photons, AP geometry)
_H10_PSV_CM2 = np.array([
    0.0165, 0.0403, 0.0789, 0.188,  0.327,  0.592, 0.745, 0.884, 0.937, 0.957,
    0.960,  0.960,  0.959,  0.951,  0.937,  0.921, 0.889, 0.854, 0.833
], dtype=float)


@dataclass
class DoseRateResult:
    total_dose_rate_usv_h:  float = 0.0
    total_dose_rate_mrem_h: float = 0.0
    contributions:          list[dict] = field(default_factory=list)
    distance_cm:            float = 100.0
    sample_name:            str   = ""
    notes:                  list  = field(default_factory=list)


def estimate_dose_rate(
        activity_results: list,     # list of ActivityResult from activity_calculator
        distance_cm:      float = 100.0,
        sample_name:      str   = "",
) -> DoseRateResult:
    """
    Estimate ambient dose equivalent rate H*(10) in µSv/h at distance_cm
    from a point source, summing contributions from all identified peaks.

    Uses ICRP 74 flux-to-dose conversion coefficients.
    Applies 1/r² geometric attenuation (no shielding).
    """
    result = DoseRateResult(
        distance_cm  = distance_cm,
        sample_name  = sample_name,
    )

    total_usv_h = 0.0
    r_cm = max(distance_cm, 1.0)
    r_m  = r_cm / 100.0

    for ar in activity_results:
        if ar.activity_bq <= 0 or ar.efficiency <= 0:
            continue

        e_kev  = ar.energy_keV
        act_bq = ar.activity_bq

        # H*(10) conversion factor at this energy (pSv·cm²)
        h10 = float(np.interp(e_kev, _H10_GRID_KEV, _H10_PSV_CM2))

        # Photon flux at distance r:  Φ = A × I_γ / (4π r² [cm²])
        flux_per_cm2_s = act_bq * ar.gamma_yield / (4 * math.pi * r_cm**2)

        # Dose rate: H = Φ × h10 (pSv/s) → µSv/h
        dose_usv_h = flux_per_cm2_s * h10 * 1e-12 * 3600 * 1e6  # pSv→µSv, s→h

        total_usv_h += dose_usv_h
        result.contributions.append({
            "isotope":       ar.isotope,
            "energy_keV":    e_kev,
            "activity_bq":   ar.activity_bq,
            "flux_cm2_s":    round(flux_per_cm2_s, 4),
            "h10_pSv_cm2":   round(h10, 4),
            "dose_usv_h":    round(dose_usv_h, 4),
            "pct_of_total":  0.0,   # filled below
        })

    # Fill % of total
    for c in result.contributions:
        c["pct_of_total"] = round(c["dose_usv_h"] / max(total_usv_h, 1e-20) * 100, 1)
    result.contributions.sort(key=lambda x: x["dose_usv_h"], reverse=True)

    result.total_dose_rate_usv_h  = round(total_usv_h, 4)
    result.total_dose_rate_mrem_h = round(total_usv_h / 10.0, 4)  # 1 mSv ≈ 100 mrem

    if total_usv_h < 0.1:
        result.notes.append("Dose rate is very low — well within background levels.")
    elif total_usv_h > 100:
        result.notes.append("⚠ Elevated dose rate — verify source activity and distance.")

    return result


def dose_at_distances(
        activity_results: list,
        distances_cm: list[float],
) -> list[dict]:
    """Compute dose rate at multiple distances for a dose-distance table."""
    rows = []
    for d in distances_cm:
        dr = estimate_dose_rate(activity_results, distance_cm=d)
        rows.append({
            "distance_cm":     d,
            "distance_m":      d / 100,
            "dose_usv_h":      dr.total_dose_rate_usv_h,
            "dose_mrem_h":     dr.total_dose_rate_mrem_h,
            "dose_usv_y":      round(dr.total_dose_rate_usv_h * 8760, 1),
        })
    return rows
