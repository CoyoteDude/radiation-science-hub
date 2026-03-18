"""
efficiency_cal.py  —  Detector efficiency calibration
───────────────────────────────────────────────────────
Builds a full-energy peak efficiency curve ε(E) from one or more
calibration sources with known activities.

  ε(E) = (net_count_rate) / (source_activity × gamma_yield)

Supports:
  • Point-source calibration  (single geometry)
  • Multi-geometry calibration with distance correction
  • Empirical polynomial fit: ln ε = Σ aᵢ (ln E)ⁱ  (i=0..4)
  • Marinelli beaker correction factor (volume source)
  • Save/load calibration to JSON

Known sources built-in: Cs-137, Co-60, Ba-133, Eu-152, Na-22, Am-241, Mn-54
"""

from __future__ import annotations
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from scipy.optimize import curve_fit
from typing import Optional

HOME     = Path.home()
CAL_DIR  = HOME / "Documents" / "GammaLab" / "calibrations"
CAL_DIR.mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
#  KNOWN CALIBRATION SOURCE LIBRARY
# ══════════════════════════════════════════════════════════════════════════════
#
# Format: { symbol: [(energy_keV, gamma_yield_fraction), ...] }
# gamma_yield = absolute gamma emission probability per decay
#
CAL_SOURCES: dict[str, list[tuple[float, float]]] = {
    "Am-241": [
        (26.34, 0.024),
        (59.54, 0.3578),
    ],
    "Ba-133": [
        (53.16,  0.0214),
        (79.61,  0.0265),
        (80.99,  0.329),
        (160.61, 0.00645),
        (223.11, 0.00453),
        (276.40, 0.0716),
        (302.85, 0.1834),
        (356.01, 0.6205),
        (383.85, 0.0894),
    ],
    "Cs-137": [
        (661.66, 0.8510),
    ],
    "Co-57": [
        (14.41,  0.0916),
        (122.06, 0.8560),
        (136.47, 0.1068),
    ],
    "Co-60": [
        (1173.23, 0.9985),
        (1332.49, 0.9998),
    ],
    "Eu-152": [
        (121.78,  0.2837),
        (244.70,  0.0753),
        (344.28,  0.2657),
        (411.12,  0.02238),
        (443.97,  0.03125),
        (778.90,  0.1293),
        (867.37,  0.04214),
        (964.08,  0.1463),
        (1085.84, 0.1013),
        (1112.07, 0.1354),
        (1408.01, 0.2085),
    ],
    "Mn-54": [
        (834.85, 0.9998),
    ],
    "Na-22": [
        (511.00, 1.7994),   # annihilation (2 photons per decay)
        (1274.54, 0.9994),
    ],
    "Y-88": [
        (898.04,  0.9370),
        (1836.06, 0.9928),
    ],
    "Zn-65": [
        (511.00, 0.284),
        (1115.55, 0.5060),
    ],
    "Cd-109": [
        (88.03, 0.0363),
    ],
    "In-111": [
        (171.28, 0.9071),
        (245.40, 0.9410),
    ],
}

# Half-lives in years for decay-correction
CAL_HALF_LIVES_Y: dict[str, float] = {
    "Am-241": 432.2,
    "Ba-133": 10.511,
    "Cs-137": 30.17,
    "Co-57":  0.7448,
    "Co-60":  5.2714,
    "Eu-152": 13.517,
    "Mn-54":  0.8549,
    "Na-22":  2.6019,
    "Y-88":   0.2964,
    "Zn-65":  0.6685,
    "Cd-109": 1.267,
    "In-111": 0.00765,
}


# ══════════════════════════════════════════════════════════════════════════════
#  DATA CLASSES
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class CalibrationPoint:
    """One measured efficiency point at a single energy."""
    energy_keV:    float
    efficiency:    float         # ε  (dimensionless, 0–1)
    uncertainty:   float = 0.0   # absolute 1σ uncertainty on ε
    source:        str   = ""
    net_counts:    float = 0.0
    count_rate:    float = 0.0   # CPS
    activity_bq:   float = 0.0   # source activity at measurement date
    gamma_yield:   float = 0.0


@dataclass
class EfficiencyCurve:
    """Fitted efficiency calibration curve."""
    points:         list[CalibrationPoint] = field(default_factory=list)
    poly_coeffs:    Optional[np.ndarray]   = None   # ln-ln polynomial
    poly_degree:    int                    = 4
    energy_range:   tuple[float, float]    = (0.0, 3000.0)
    geometry:       str                    = "Point source"
    distance_cm:    float                  = 0.0
    detector_id:    str                    = "RC-103"
    created_at:     str                    = ""
    r2:             float                  = 0.0
    n_points:       int                    = 0

    def efficiency_at(self, energy_kev: float) -> Optional[float]:
        """Predict efficiency at energy_kev using the fitted curve."""
        if self.poly_coeffs is None:
            return None
        if not (self.energy_range[0] <= energy_kev <= self.energy_range[1]):
            return None
        ln_e = np.log(energy_kev)
        ln_eff = sum(c * ln_e**i for i, c in enumerate(self.poly_coeffs))
        return float(np.exp(ln_eff))

    def uncertainty_at(self, energy_kev: float, pct: float = 5.0) -> float:
        """Return estimated efficiency uncertainty (default 5% of value)."""
        eff = self.efficiency_at(energy_kev)
        return (eff * pct / 100) if eff else 0.0

    def to_dict(self) -> dict:
        return {
            "poly_coeffs":  self.poly_coeffs.tolist() if self.poly_coeffs is not None else None,
            "poly_degree":  self.poly_degree,
            "energy_range": list(self.energy_range),
            "geometry":     self.geometry,
            "distance_cm":  self.distance_cm,
            "detector_id":  self.detector_id,
            "created_at":   self.created_at,
            "r2":           self.r2,
            "n_points":     self.n_points,
            "points": [
                {"energy_keV":  p.energy_keV,
                 "efficiency":  p.efficiency,
                 "uncertainty": p.uncertainty,
                 "source":      p.source}
                for p in self.points
            ],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "EfficiencyCurve":
        curve = cls(
            poly_degree  = d.get("poly_degree", 4),
            energy_range = tuple(d.get("energy_range", [0, 3000])),
            geometry     = d.get("geometry", ""),
            distance_cm  = d.get("distance_cm", 0),
            detector_id  = d.get("detector_id", ""),
            created_at   = d.get("created_at", ""),
            r2           = d.get("r2", 0),
            n_points     = d.get("n_points", 0),
        )
        if d.get("poly_coeffs"):
            curve.poly_coeffs = np.array(d["poly_coeffs"])
        curve.points = [
            CalibrationPoint(**p) for p in d.get("points", [])
        ]
        return curve


# ══════════════════════════════════════════════════════════════════════════════
#  CORE CALIBRATION FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def build_efficiency_curve(
        cal_points: list[CalibrationPoint],
        poly_degree: int = 4,
        geometry: str = "Point source",
        distance_cm: float = 0.0,
) -> tuple[EfficiencyCurve, dict]:
    """
    Fit an efficiency calibration curve to a list of CalibrationPoints.

    Uses a polynomial in ln(E) vs ln(ε):
        ln(ε) = a₀ + a₁·ln(E) + a₂·(ln E)² + … + aₙ·(ln E)ⁿ

    Returns (EfficiencyCurve, fit_info_dict).
    """
    if len(cal_points) < 2:
        return EfficiencyCurve(), {"error": "Need ≥2 calibration points"}

    # Filter valid points
    valid = [p for p in cal_points if p.efficiency > 0 and p.energy_keV > 0]
    if len(valid) < 2:
        return EfficiencyCurve(), {"error": "No valid calibration points"}

    energies = np.array([p.energy_keV  for p in valid])
    effs     = np.array([p.efficiency  for p in valid])
    weights  = np.array([1.0 / max(p.uncertainty**2, 1e-10) for p in valid])

    ln_e    = np.log(energies)
    ln_eff  = np.log(effs)
    degree  = min(poly_degree, len(valid) - 1)

    # Weighted polynomial fit in log-log space
    try:
        coeffs = np.polyfit(ln_e, ln_eff, degree, w=np.sqrt(weights))
        coeffs = coeffs[::-1]  # ascending order (a₀, a₁, …)
    except Exception as e:
        return EfficiencyCurve(), {"error": str(e)}

    # R²
    ln_eff_pred = np.polyval(coeffs[::-1], ln_e)
    r2 = float(1 - np.sum((ln_eff - ln_eff_pred)**2) /
               max(np.sum((ln_eff - np.mean(ln_eff))**2), 1e-10))

    curve = EfficiencyCurve(
        points       = valid,
        poly_coeffs  = coeffs,
        poly_degree  = degree,
        energy_range = (float(energies.min() * 0.5), float(energies.max() * 1.5)),
        geometry     = geometry,
        distance_cm  = distance_cm,
        detector_id  = "RC-103",
        created_at   = datetime.now().isoformat(),
        r2           = round(r2, 4),
        n_points     = len(valid),
    )

    info = {
        "n_points":    len(valid),
        "r2":          round(r2, 4),
        "poly_degree": degree,
        "energy_min":  round(float(energies.min()), 1),
        "energy_max":  round(float(energies.max()), 1),
        "coeffs":      [round(float(c), 6) for c in coeffs],
    }
    return curve, info


def calibration_point_from_measurement(
        source_symbol:    str,
        source_activity_bq: float,
        reference_date:   str,
        measurement_date: str,
        net_counts:       float,
        live_time_s:      float,
        gamma_energy_kev: float,
) -> Optional[CalibrationPoint]:
    """
    Compute a CalibrationPoint from a measurement.

    Automatically decay-corrects the source activity from reference_date
    to measurement_date.
    """
    # Find gamma yield for this source + energy
    lines     = CAL_SOURCES.get(source_symbol, [])
    gamma_yield = None
    best_delta  = 5.0  # keV tolerance
    for kev, yield_ in lines:
        d = abs(kev - gamma_energy_kev)
        if d < best_delta:
            best_delta, gamma_yield = d, yield_

    if gamma_yield is None:
        return None

    # Decay correct
    t1  = datetime.fromisoformat(reference_date)
    t2  = datetime.fromisoformat(measurement_date)
    dt_years = (t2 - t1).total_seconds() / (365.25 * 24 * 3600)
    hl_years = CAL_HALF_LIVES_Y.get(source_symbol, 1e9)
    activity_at_meas = source_activity_bq * (0.5 ** (dt_years / hl_years))

    # Count rate
    count_rate = net_counts / max(live_time_s, 1)

    # Efficiency
    expected_rate = activity_at_meas * gamma_yield
    efficiency    = count_rate / max(expected_rate, 1e-20)

    # Uncertainty (counting statistics + 2% source uncertainty)
    count_unc = np.sqrt(net_counts) / max(live_time_s, 1) / max(expected_rate, 1e-20)
    total_unc = float(np.sqrt(count_unc**2 + 0.02**2)) * efficiency

    return CalibrationPoint(
        energy_keV    = gamma_energy_kev,
        efficiency    = round(float(efficiency), 6),
        uncertainty   = round(float(total_unc),  6),
        source        = source_symbol,
        net_counts    = net_counts,
        count_rate    = round(count_rate, 6),
        activity_bq   = round(activity_at_meas, 2),
        gamma_yield   = gamma_yield,
    )


def distance_scale_efficiency(curve: EfficiencyCurve,
                                new_distance_cm: float) -> EfficiencyCurve:
    """
    Scale an efficiency curve to a new source-detector distance
    using the inverse-square law:   ε(d₂) = ε(d₁) × (d₁/d₂)²
    """
    if curve.distance_cm <= 0 or new_distance_cm <= 0:
        return curve
    scale   = (curve.distance_cm / new_distance_cm) ** 2
    new_pts = []
    for p in curve.points:
        new_pts.append(CalibrationPoint(
            energy_keV  = p.energy_keV,
            efficiency  = p.efficiency * scale,
            uncertainty = p.uncertainty * scale,
            source      = p.source,
            net_counts  = p.net_counts,
            count_rate  = p.count_rate,
            activity_bq = p.activity_bq,
            gamma_yield = p.gamma_yield,
        ))
    scaled, _ = build_efficiency_curve(
        new_pts, curve.poly_degree, curve.geometry, new_distance_cm
    )
    return scaled


# ══════════════════════════════════════════════════════════════════════════════
#  SAVE / LOAD
# ══════════════════════════════════════════════════════════════════════════════

def save_curve(curve: EfficiencyCurve, name: str) -> Path:
    path = CAL_DIR / f"{name}.json"
    path.write_text(json.dumps(curve.to_dict(), indent=2))
    return path


def load_curve(name: str) -> Optional[EfficiencyCurve]:
    path = CAL_DIR / f"{name}.json"
    if not path.exists():
        return None
    try:
        return EfficiencyCurve.from_dict(json.loads(path.read_text()))
    except Exception:
        return None


def list_saved_curves() -> list[str]:
    return [p.stem for p in sorted(CAL_DIR.glob("*.json"))]
