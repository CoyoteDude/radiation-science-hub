"""
peak_fitting.py  —  Gaussian peak fitting for gamma spectroscopy
────────────────────────────────────────────────────────────────
Fits each detected peak with a Gaussian + linear background to extract:
  • Precise centroid energy (keV)
  • Peak area (net counts)
  • FWHM and energy resolution
  • Goodness-of-fit (reduced χ²)

Used by:
  • activity_calculator.py   (net area → activity)
  • efficiency_cal.py        (calibration source peak areas)
  • mda_calculator.py        (peak + background counts)
"""

from __future__ import annotations
import numpy as np
from scipy.optimize import curve_fit
from scipy.signal import find_peaks, savgol_filter
from dataclasses import dataclass, field
from typing import Optional


# ══════════════════════════════════════════════════════════════════════════════
#  DATA CLASSES
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class FittedPeak:
    """Result of a Gaussian fit to a single gamma peak."""
    # Input
    energy_keV_rough:  float          # from channel→energy calibration
    channel_centroid:  float          # peak channel (rough)

    # Fit results
    energy_keV:        float  = 0.0   # fitted centroid in keV
    area_net:          float  = 0.0   # net peak area (counts)
    area_gross:        float  = 0.0   # gross area under Gaussian
    area_uncertainty:  float  = 0.0   # 1σ uncertainty on net area
    fwhm_keV:          float  = 0.0   # fitted FWHM in keV
    fwhm_channels:     float  = 0.0   # fitted sigma * 2.355 in channels
    resolution_pct:    float  = 0.0   # FWHM / centroid × 100
    background_left:   float  = 0.0   # local background CPS (left side)
    background_right:  float  = 0.0   # local background CPS (right side)
    background_total:  float  = 0.0   # total background under peak
    chi2_reduced:      float  = 0.0   # goodness of fit
    fit_ok:            bool   = False
    fit_message:       str    = ""

    # Fit parameters [amplitude, centroid, sigma, bg_slope, bg_intercept]
    params:            list   = field(default_factory=list)
    params_err:        list   = field(default_factory=list)

    # Raw data used for fit
    channels_fit:      list   = field(default_factory=list)
    counts_fit:        list   = field(default_factory=list)
    counts_fitted:     list   = field(default_factory=list)  # model values


@dataclass
class FitSummary:
    """Summary statistics across all fitted peaks in a spectrum."""
    n_peaks_attempted:  int   = 0
    n_peaks_fitted:     int   = 0
    n_peaks_failed:     int   = 0
    mean_chi2:          float = 0.0
    mean_resolution_pct:float = 0.0
    fitted_peaks:       list  = field(default_factory=list)


# ══════════════════════════════════════════════════════════════════════════════
#  MODEL FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def _gaussian_plus_linear(x: np.ndarray,
                           amplitude: float, centroid: float, sigma: float,
                           bg_slope: float, bg_intercept: float) -> np.ndarray:
    """Gaussian peak on a linear background."""
    gauss = amplitude * np.exp(-0.5 * ((x - centroid) / sigma) ** 2)
    bg    = bg_slope * (x - centroid) + bg_intercept
    return gauss + bg


def _gaussian_only(x: np.ndarray,
                    amplitude: float, centroid: float, sigma: float) -> np.ndarray:
    return amplitude * np.exp(-0.5 * ((x - centroid) / sigma) ** 2)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN FITTER
# ══════════════════════════════════════════════════════════════════════════════

def fit_peak(counts:   np.ndarray,
             energies: np.ndarray,
             peak_channel: int,
             window_channels: int = 20,
             min_counts: int = 10) -> FittedPeak:
    """
    Fit a single Gaussian + linear background to the region around peak_channel.

    Parameters
    ----------
    counts          : full spectrum counts array
    energies        : full spectrum energies array (keV)
    peak_channel    : approximate channel of the peak centroid
    window_channels : half-width of fit window in channels (default ±20)
    min_counts      : minimum counts required to attempt fit

    Returns FittedPeak (fit_ok=False if fit failed).
    """
    n = len(counts)
    ch_lo = max(0,   peak_channel - window_channels)
    ch_hi = min(n-1, peak_channel + window_channels)

    x = np.arange(ch_lo, ch_hi + 1, dtype=float)
    y = counts[ch_lo:ch_hi+1].astype(float)

    rough_energy = float(energies[peak_channel])
    result = FittedPeak(
        energy_keV_rough = rough_energy,
        channel_centroid = float(peak_channel),
    )

    if y.max() < min_counts or len(x) < 6:
        result.fit_message = "Too few counts or points for fit"
        return result

    # Initial parameter estimates
    amp0      = float(y.max() - y.min())
    cen0      = float(peak_channel)
    # Estimate sigma from FWHM ≈ 2.355σ
    # Use half-max width as initial guess
    half_max  = y.min() + amp0 / 2
    above_hm  = x[y >= half_max]
    sigma0    = max((above_hm[-1] - above_hm[0]) / 2.355, 0.5) if len(above_hm) >= 2 else 2.0
    bg_int0   = float(y.min())
    bg_slp0   = 0.0

    p0     = [amp0, cen0, sigma0, bg_slp0, bg_int0]
    bounds = (
        [0,      ch_lo, 0.3,  -np.inf, 0      ],
        [np.inf, ch_hi, window_channels * 0.8, np.inf, np.inf],
    )

    try:
        popt, pcov = curve_fit(
            _gaussian_plus_linear, x, y,
            p0=p0, bounds=bounds,
            maxfev=5000,
            sigma=np.sqrt(np.maximum(y, 1)),  # Poisson weights
            absolute_sigma=True,
        )
        perr = np.sqrt(np.diag(pcov))

        amplitude, centroid, sigma, bg_slope, bg_intercept = popt
        sigma = abs(sigma)
        fwhm_ch = 2.355 * sigma

        # Map fitted centroid channel → keV
        # Use linear interpolation across the calibration array
        fitted_kev = float(np.interp(centroid, np.arange(n), energies))

        # Net area = Gaussian integral = amplitude × sigma × √(2π)
        area_gross = amplitude * sigma * np.sqrt(2 * np.pi)
        # Background under peak (linear × window width)
        bg_under   = bg_intercept * fwhm_ch * 2 + 0  # simplified
        area_net   = area_gross
        area_err   = float(np.sqrt(abs(area_gross) + abs(bg_under)))

        # FWHM in keV
        # Slope of energy cal at this channel
        ch_int = int(centroid)
        de_dch = (float(energies[min(ch_int+1, n-1)]) -
                  float(energies[max(ch_int-1, 0)])) / 2
        fwhm_kev = fwhm_ch * abs(de_dch)

        # Reduced chi-squared
        y_model = _gaussian_plus_linear(x, *popt)
        residuals = y - y_model
        dof = max(len(x) - 5, 1)
        chi2_r = float(np.sum(residuals**2 / np.maximum(y_model, 1)) / dof)

        # Background on each side (for MDA)
        bg_l = float(bg_intercept - bg_slope * fwhm_ch)
        bg_r = float(bg_intercept + bg_slope * fwhm_ch)
        bg_total = (bg_l + bg_r) / 2 * fwhm_ch * 2

        result.energy_keV        = round(fitted_kev, 3)
        result.area_net          = round(area_net, 1)
        result.area_gross        = round(area_gross, 1)
        result.area_uncertainty  = round(area_err, 1)
        result.fwhm_keV          = round(fwhm_kev, 3)
        result.fwhm_channels     = round(fwhm_ch, 2)
        result.resolution_pct    = round(fwhm_kev / max(fitted_kev, 1) * 100, 3)
        result.background_left   = round(bg_l, 2)
        result.background_right  = round(bg_r, 2)
        result.background_total  = round(bg_total, 1)
        result.chi2_reduced      = round(chi2_r, 3)
        result.fit_ok            = True
        result.fit_message       = "OK"
        result.params            = [round(float(p), 4) for p in popt]
        result.params_err        = [round(float(e), 4) for e in perr]
        result.channels_fit      = x.tolist()
        result.counts_fit        = y.tolist()
        result.counts_fitted     = y_model.tolist()

    except (RuntimeError, ValueError) as e:
        result.fit_message = f"Fit failed: {e}"

    return result


def fit_all_peaks(counts:   list | np.ndarray,
                  energies: list | np.ndarray,
                  rough_peaks: list[dict],
                  window_channels: int = 20,
                  min_counts: int = 10) -> FitSummary:
    """
    Fit Gaussians to all peaks detected by find_spectrum_peaks().

    rough_peaks: list of dicts from spectrum_db.find_spectrum_peaks()
    Returns FitSummary with individual FittedPeak results.
    """
    counts_arr   = np.array(counts,   dtype=float)
    energies_arr = np.array(energies, dtype=float)

    summary = FitSummary(n_peaks_attempted=len(rough_peaks))
    chi2s, ress = [], []

    for pk in rough_peaks:
        fp = fit_peak(
            counts_arr, energies_arr,
            peak_channel    = pk["channel"],
            window_channels = window_channels,
            min_counts      = min_counts,
        )
        # Copy rough peak data into fitted peak for reference
        fp.energy_keV_rough = pk["energy_keV"]

        summary.fitted_peaks.append(fp)
        if fp.fit_ok:
            summary.n_peaks_fitted += 1
            chi2s.append(fp.chi2_reduced)
            ress.append(fp.resolution_pct)
        else:
            summary.n_peaks_failed += 1

    if chi2s:
        summary.mean_chi2           = round(float(np.mean(chi2s)), 3)
        summary.mean_resolution_pct = round(float(np.mean(ress)), 3)

    return summary


# ══════════════════════════════════════════════════════════════════════════════
#  RESOLUTION CURVE  (FWHM vs energy)
# ══════════════════════════════════════════════════════════════════════════════

def fit_resolution_curve(fitted_peaks: list[FittedPeak]
                          ) -> tuple[Optional[np.ndarray], dict]:
    """
    Fit a resolution curve: FWHM(E) = a + b*√E  (detector broadening model)
    to a set of fitted peaks.

    Returns (popt, info_dict) where popt = [a, b] if fit succeeded.
    """
    good = [(fp.energy_keV, fp.fwhm_keV)
            for fp in fitted_peaks
            if fp.fit_ok and fp.fwhm_keV > 0 and fp.energy_keV > 50]

    if len(good) < 3:
        return None, {"error": "Need ≥3 fitted peaks for resolution curve"}

    energies = np.array([g[0] for g in good])
    fwhms    = np.array([g[1] for g in good])

    def model(e, a, b):
        return a + b * np.sqrt(e)

    try:
        popt, pcov = curve_fit(model, energies, fwhms,
                                p0=[1.0, 0.05], maxfev=2000)
        r2 = _r_squared(fwhms, model(energies, *popt))
        return popt, {
            "a": round(float(popt[0]), 4),
            "b": round(float(popt[1]), 4),
            "r2": round(r2, 4),
            "n_points": len(good),
            "model": "FWHM(E) = a + b·√E",
        }
    except Exception as e:
        return None, {"error": str(e)}


def predict_fwhm(energy_kev: float, popt: np.ndarray) -> float:
    """Predict FWHM at a given energy using the fitted resolution curve."""
    a, b = popt
    return max(a + b * np.sqrt(energy_kev), 0.1)


def _r_squared(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return 1 - ss_res / max(ss_tot, 1e-10)
