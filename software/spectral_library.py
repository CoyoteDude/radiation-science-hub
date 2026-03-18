"""
spectral_library.py — Spectral library matching for GammaLab
──────────────────────────────────────────────────────────────
Compares a measured spectrum's detected peaks against a library of
reference spectra stored in ~/Documents/GammaLab/spectral_library/.

Each reference entry is a JSON file describing a known material's
expected gamma lines and their relative intensities. The engine
computes a composite match score for each library entry against the
measured spectrum, combining:

  1. Peak presence score    — fraction of reference lines found in spectrum
  2. Energy match score     — how closely detected energies align (sub-keV)
  3. Intensity ratio score  — how well relative peak heights match reference
  4. Unexplained peaks penalty — penalises spectrum peaks not covered by match

Score range: 0.0 (no match) → 1.0 (perfect match)

Built-in library covers ~30 common materials/sources. Users can add
their own .json reference files to the library directory.
"""

from __future__ import annotations
import json
import math
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# ── Storage paths ────────────────────────────────────────────────────────────
LIBRARY_DIR = Path.home() / "Documents" / "GammaLab" / "spectral_library"
LIBRARY_DIR.mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
#  DATA CLASSES
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class LibraryLine:
    """A single gamma line in a reference entry."""
    energy_keV:   float         # nominal energy
    rel_intensity: float        # relative intensity 0–100 (strongest = 100)
    isotope:      str   = ""    # isotope responsible for this line
    tolerance_keV: float = 4.0  # match window (keV) — widened for Radiacode-103


@dataclass
class LibraryEntry:
    """One reference spectrum (a known material or source)."""
    name:         str
    category:     str           # e.g. "Natural", "Industrial", "Medical", "Calibration"
    description:  str   = ""
    lines:        list[LibraryLine] = field(default_factory=list)
    tags:         list[str]         = field(default_factory=list)
    source_file:  str   = ""


@dataclass
class LineMatch:
    """Result of matching one library line against detected peaks."""
    lib_keV:      float
    lib_rel_int:  float
    isotope:      str
    matched:      bool  = False
    det_keV:      float = 0.0
    det_counts:   float = 0.0
    delta_keV:    float = 0.0


@dataclass
class MatchResult:
    """Full scoring result for one library entry vs one spectrum."""
    entry_name:       str
    category:         str
    description:      str
    overall_score:    float          # 0–1 composite score
    presence_score:   float          # fraction of key lines found
    energy_score:     float          # mean energy alignment quality
    intensity_score:  float          # relative intensity pattern match
    coverage_score:   float          # fraction of spectrum peaks explained
    n_lines_matched:  int
    n_lines_total:    int
    n_peaks_spectrum: int
    n_peaks_explained:int
    line_matches:     list[LineMatch] = field(default_factory=list)
    verdict:          str = ""       # human-readable summary
    tags:             list[str] = field(default_factory=list)


# ══════════════════════════════════════════════════════════════════════════════
#  BUILT-IN REFERENCE LIBRARY
# ══════════════════════════════════════════════════════════════════════════════

_BUILTIN_ENTRIES: list[dict] = [

    # ── NATURAL / TERRESTRIAL ──────────────────────────────────────────────
    {
        "name": "Natural background (typical)",
        "category": "Natural",
        "description": "Typical indoor background: K-40 + U/Th series daughters + Cs-137 fallout",
        "tags": ["background", "ubiquitous"],
        "lines": [
            {"energy_keV": 1460.8, "rel_intensity": 100, "isotope": "K-40",  "tolerance_keV": 5},
            {"energy_keV":  609.3, "rel_intensity":  80, "isotope": "Bi-214","tolerance_keV": 4},
            {"energy_keV": 1764.5, "rel_intensity":  60, "isotope": "Bi-214","tolerance_keV": 5},
            {"energy_keV":  661.7, "rel_intensity":  40, "isotope": "Cs-137","tolerance_keV": 4},
            {"energy_keV":  583.2, "rel_intensity":  35, "isotope": "Tl-208","tolerance_keV": 4},
            {"energy_keV": 2614.5, "rel_intensity":  30, "isotope": "Tl-208","tolerance_keV": 6},
            {"energy_keV":  351.9, "rel_intensity":  50, "isotope": "Pb-214","tolerance_keV": 4},
            {"energy_keV":  295.2, "rel_intensity":  35, "isotope": "Pb-214","tolerance_keV": 4},
        ],
    },
    {
        "name": "Potassium-40 (K-40)",
        "category": "Natural",
        "description": "Primordial nuclide. Prominent 1461 keV line. Present in potassium-rich minerals, fertilizers, food.",
        "tags": ["natural", "primordial", "K-40"],
        "lines": [
            {"energy_keV": 1460.8, "rel_intensity": 100, "isotope": "K-40", "tolerance_keV": 5},
        ],
    },
    {
        "name": "Uranium-238 decay chain",
        "category": "Natural",
        "description": "U-238 series: Ra-226 through Bi-214/Pb-214. Key lines at 186, 295, 352, 609, 1120, 1764 keV.",
        "tags": ["natural", "uranium", "NORM"],
        "lines": [
            {"energy_keV":  185.7, "rel_intensity":  60, "isotope": "Ra-226", "tolerance_keV": 4},
            {"energy_keV":  295.2, "rel_intensity":  45, "isotope": "Pb-214", "tolerance_keV": 4},
            {"energy_keV":  351.9, "rel_intensity": 100, "isotope": "Pb-214", "tolerance_keV": 4},
            {"energy_keV":  609.3, "rel_intensity":  90, "isotope": "Bi-214", "tolerance_keV": 4},
            {"energy_keV": 1120.3, "rel_intensity":  40, "isotope": "Bi-214", "tolerance_keV": 5},
            {"energy_keV": 1764.5, "rel_intensity":  55, "isotope": "Bi-214", "tolerance_keV": 5},
        ],
    },
    {
        "name": "Thorium-232 decay chain",
        "category": "Natural",
        "description": "Th-232 series: Ra-228 through Tl-208. Diagnostic lines at 239, 338, 583, 911, 969, 2614 keV.",
        "tags": ["natural", "thorium", "NORM"],
        "lines": [
            {"energy_keV":  238.6, "rel_intensity":  80, "isotope": "Pb-212", "tolerance_keV": 4},
            {"energy_keV":  338.3, "rel_intensity":  30, "isotope": "Ac-228", "tolerance_keV": 4},
            {"energy_keV":  583.2, "rel_intensity":  85, "isotope": "Tl-208", "tolerance_keV": 4},
            {"energy_keV":  911.2, "rel_intensity":  55, "isotope": "Ac-228", "tolerance_keV": 5},
            {"energy_keV":  969.0, "rel_intensity":  30, "isotope": "Ac-228", "tolerance_keV": 5},
            {"energy_keV": 2614.5, "rel_intensity": 100, "isotope": "Tl-208", "tolerance_keV": 6},
        ],
    },
    {
        "name": "Radon-222 progeny (indoor)",
        "category": "Natural",
        "description": "Short-lived Rn-222 daughters: Pb-214 and Bi-214. Accumulate on surfaces indoors.",
        "tags": ["natural", "radon", "indoor"],
        "lines": [
            {"energy_keV":  295.2, "rel_intensity":  55, "isotope": "Pb-214", "tolerance_keV": 4},
            {"energy_keV":  351.9, "rel_intensity": 100, "isotope": "Pb-214", "tolerance_keV": 4},
            {"energy_keV":  609.3, "rel_intensity":  95, "isotope": "Bi-214", "tolerance_keV": 4},
            {"energy_keV": 1120.3, "rel_intensity":  40, "isotope": "Bi-214", "tolerance_keV": 5},
            {"energy_keV": 1764.5, "rel_intensity":  55, "isotope": "Bi-214", "tolerance_keV": 5},
        ],
    },

    # ── FALLOUT / ANTHROPOGENIC ────────────────────────────────────────────
    {
        "name": "Cs-137 (fallout / calibration)",
        "category": "Anthropogenic",
        "description": "Reactor fission product. Single sharp line at 661.7 keV. Ubiquitous from nuclear weapons testing and Chernobyl.",
        "tags": ["fallout", "calibration", "Cs-137"],
        "lines": [
            {"energy_keV": 661.7, "rel_intensity": 100, "isotope": "Cs-137", "tolerance_keV": 4},
            {"energy_keV":  32.0, "rel_intensity":  10, "isotope": "Ba-137m","tolerance_keV": 3},
        ],
    },
    {
        "name": "Co-60 (industrial / calibration)",
        "category": "Industrial",
        "description": "Activated cobalt. Two nearly equal lines at 1173 and 1332 keV — their equality is diagnostic.",
        "tags": ["industrial", "calibration", "Co-60"],
        "lines": [
            {"energy_keV": 1173.2, "rel_intensity": 100, "isotope": "Co-60", "tolerance_keV": 5},
            {"energy_keV": 1332.5, "rel_intensity":  99, "isotope": "Co-60", "tolerance_keV": 5},
        ],
    },
    {
        "name": "I-131 (medical / reactor)",
        "category": "Medical",
        "description": "Iodine-131 from thyroid treatment or reactor release. Primary gamma at 364 keV.",
        "tags": ["medical", "reactor", "I-131"],
        "lines": [
            {"energy_keV":  364.5, "rel_intensity": 100, "isotope": "I-131", "tolerance_keV": 4},
            {"energy_keV":  637.0, "rel_intensity":   7, "isotope": "I-131", "tolerance_keV": 4},
            {"energy_keV":  284.3, "rel_intensity":   6, "isotope": "I-131", "tolerance_keV": 4},
        ],
    },
    {
        "name": "Eu-152 (calibration source)",
        "category": "Calibration",
        "description": "Multi-line europium source used for efficiency calibration. Lines from 122 keV to 1408 keV.",
        "tags": ["calibration", "Eu-152"],
        "lines": [
            {"energy_keV":  121.8, "rel_intensity": 100, "isotope": "Eu-152", "tolerance_keV": 3},
            {"energy_keV":  244.7, "rel_intensity":  20, "isotope": "Eu-152", "tolerance_keV": 4},
            {"energy_keV":  344.3, "rel_intensity":  60, "isotope": "Eu-152", "tolerance_keV": 4},
            {"energy_keV":  411.1, "rel_intensity":  10, "isotope": "Eu-152", "tolerance_keV": 4},
            {"energy_keV":  444.0, "rel_intensity":  10, "isotope": "Eu-152", "tolerance_keV": 4},
            {"energy_keV":  778.9, "rel_intensity":  25, "isotope": "Eu-152", "tolerance_keV": 4},
            {"energy_keV":  964.1, "rel_intensity":  25, "isotope": "Eu-152", "tolerance_keV": 5},
            {"energy_keV": 1085.8, "rel_intensity":  20, "isotope": "Eu-152", "tolerance_keV": 5},
            {"energy_keV": 1112.1, "rel_intensity":  20, "isotope": "Eu-152", "tolerance_keV": 5},
            {"energy_keV": 1408.0, "rel_intensity":  55, "isotope": "Eu-152", "tolerance_keV": 5},
        ],
    },
    {
        "name": "Am-241 (smoke detector / calibration)",
        "category": "Industrial",
        "description": "Common in ionisation smoke detectors. Dominant line at 59.5 keV.",
        "tags": ["industrial", "calibration", "Am-241"],
        "lines": [
            {"energy_keV":  59.5,  "rel_intensity": 100, "isotope": "Am-241", "tolerance_keV": 3},
            {"energy_keV":  26.3,  "rel_intensity":  15, "isotope": "Am-241", "tolerance_keV": 3},
        ],
    },
    {
        "name": "Na-22 (positron emitter / calibration)",
        "category": "Calibration",
        "description": "Positron emitter used for PET phantom calibration. 511 keV annihilation + 1274 keV.",
        "tags": ["calibration", "Na-22", "positron"],
        "lines": [
            {"energy_keV":  511.0, "rel_intensity": 100, "isotope": "Na-22",  "tolerance_keV": 4},
            {"energy_keV": 1274.5, "rel_intensity":  85, "isotope": "Na-22",  "tolerance_keV": 5},
        ],
    },
    {
        "name": "Ba-133 (calibration source)",
        "category": "Calibration",
        "description": "Multiple lines from 80–384 keV. Good for low-energy efficiency calibration.",
        "tags": ["calibration", "Ba-133"],
        "lines": [
            {"energy_keV":   80.9, "rel_intensity":  65, "isotope": "Ba-133", "tolerance_keV": 3},
            {"energy_keV":  160.6, "rel_intensity":  10, "isotope": "Ba-133", "tolerance_keV": 3},
            {"energy_keV":  223.1, "rel_intensity":  10, "isotope": "Ba-133", "tolerance_keV": 4},
            {"energy_keV":  276.4, "rel_intensity":  15, "isotope": "Ba-133", "tolerance_keV": 4},
            {"energy_keV":  302.9, "rel_intensity":  45, "isotope": "Ba-133", "tolerance_keV": 4},
            {"energy_keV":  356.0, "rel_intensity": 100, "isotope": "Ba-133", "tolerance_keV": 4},
            {"energy_keV":  383.9, "rel_intensity":  20, "isotope": "Ba-133", "tolerance_keV": 4},
        ],
    },
    {
        "name": "Mn-54 (activation product)",
        "category": "Industrial",
        "description": "Single 834.8 keV line. Produced by neutron activation of Fe/Mn. Found near reactors or accelerators.",
        "tags": ["activation", "Mn-54"],
        "lines": [
            {"energy_keV": 834.8, "rel_intensity": 100, "isotope": "Mn-54", "tolerance_keV": 5},
        ],
    },
    {
        "name": "Zn-65 (activation product)",
        "category": "Industrial",
        "description": "1115.5 keV line + 511 keV annihilation. From neutron activation of zinc in reactor coolant.",
        "tags": ["activation", "Zn-65"],
        "lines": [
            {"energy_keV":  511.0, "rel_intensity":   3, "isotope": "Zn-65", "tolerance_keV": 4},
            {"energy_keV": 1115.5, "rel_intensity": 100, "isotope": "Zn-65", "tolerance_keV": 5},
        ],
    },
    {
        "name": "Ir-192 (industrial radiography)",
        "category": "Industrial",
        "description": "Used in NDT radiography. Complex spectrum 300–600 keV with lines at 316, 468, 604 keV.",
        "tags": ["industrial", "radiography", "Ir-192"],
        "lines": [
            {"energy_keV":  295.9, "rel_intensity":  40, "isotope": "Ir-192", "tolerance_keV": 4},
            {"energy_keV":  308.5, "rel_intensity":  50, "isotope": "Ir-192", "tolerance_keV": 4},
            {"energy_keV":  316.5, "rel_intensity":  95, "isotope": "Ir-192", "tolerance_keV": 4},
            {"energy_keV":  468.1, "rel_intensity":  80, "isotope": "Ir-192", "tolerance_keV": 4},
            {"energy_keV":  588.6, "rel_intensity":  40, "isotope": "Ir-192", "tolerance_keV": 4},
            {"energy_keV":  604.4, "rel_intensity": 100, "isotope": "Ir-192", "tolerance_keV": 4},
        ],
    },
    {
        "name": "Se-75 (industrial radiography)",
        "category": "Industrial",
        "description": "Used as replacement for Ir-192 in petrochemical piping. Lines 66–401 keV.",
        "tags": ["industrial", "radiography", "Se-75"],
        "lines": [
            {"energy_keV":  121.1, "rel_intensity":  50, "isotope": "Se-75", "tolerance_keV": 3},
            {"energy_keV":  136.0, "rel_intensity":  65, "isotope": "Se-75", "tolerance_keV": 3},
            {"energy_keV":  264.7, "rel_intensity":  70, "isotope": "Se-75", "tolerance_keV": 4},
            {"energy_keV":  279.5, "rel_intensity": 100, "isotope": "Se-75", "tolerance_keV": 4},
            {"energy_keV":  400.7, "rel_intensity":  35, "isotope": "Se-75", "tolerance_keV": 4},
        ],
    },
    {
        "name": "Tc-99m (nuclear medicine)",
        "category": "Medical",
        "description": "Most common diagnostic isotope. Single 140.5 keV line. Short 6h half-life.",
        "tags": ["medical", "Tc-99m"],
        "lines": [
            {"energy_keV": 140.5, "rel_intensity": 100, "isotope": "Tc-99m", "tolerance_keV": 3},
        ],
    },
    {
        "name": "Ga-67 (nuclear medicine)",
        "category": "Medical",
        "description": "Used in tumour imaging. Multiple low-energy lines at 93, 185, 300 keV.",
        "tags": ["medical", "Ga-67"],
        "lines": [
            {"energy_keV":  93.3,  "rel_intensity": 100, "isotope": "Ga-67", "tolerance_keV": 3},
            {"energy_keV": 184.6,  "rel_intensity":  45, "isotope": "Ga-67", "tolerance_keV": 4},
            {"energy_keV": 300.2,  "rel_intensity":  20, "isotope": "Ga-67", "tolerance_keV": 4},
        ],
    },
    {
        "name": "In-111 (nuclear medicine)",
        "category": "Medical",
        "description": "Used for SPECT white blood cell imaging. Lines at 171 and 245 keV.",
        "tags": ["medical", "In-111"],
        "lines": [
            {"energy_keV": 171.3, "rel_intensity": 100, "isotope": "In-111", "tolerance_keV": 4},
            {"energy_keV": 245.4, "rel_intensity":  94, "isotope": "In-111", "tolerance_keV": 4},
        ],
    },
    {
        "name": "Tl-201 (nuclear medicine)",
        "category": "Medical",
        "description": "Cardiac perfusion imaging agent. X-rays ~68–80 keV + 167 keV gamma.",
        "tags": ["medical", "Tl-201"],
        "lines": [
            {"energy_keV":  70.8,  "rel_intensity": 100, "isotope": "Tl-201", "tolerance_keV": 3},
            {"energy_keV": 167.4,  "rel_intensity":  15, "isotope": "Tl-201", "tolerance_keV": 4},
        ],
    },
    {
        "name": "F-18 (PET tracer, FDG)",
        "category": "Medical",
        "description": "PET tracer. Annihilation radiation only: two 511 keV photons back-to-back.",
        "tags": ["medical", "PET", "F-18"],
        "lines": [
            {"energy_keV": 511.0, "rel_intensity": 100, "isotope": "F-18", "tolerance_keV": 4},
        ],
    },
    {
        "name": "Granite / granitic rock",
        "category": "Natural",
        "description": "Elevated K, U, Th content. Expect K-40 + both U-238 and Th-232 chain lines simultaneously.",
        "tags": ["geology", "NORM", "granite"],
        "lines": [
            {"energy_keV": 1460.8, "rel_intensity": 100, "isotope": "K-40",  "tolerance_keV": 5},
            {"energy_keV":  609.3, "rel_intensity":  70, "isotope": "Bi-214","tolerance_keV": 4},
            {"energy_keV":  351.9, "rel_intensity":  60, "isotope": "Pb-214","tolerance_keV": 4},
            {"energy_keV":  583.2, "rel_intensity":  55, "isotope": "Tl-208","tolerance_keV": 4},
            {"energy_keV": 2614.5, "rel_intensity":  40, "isotope": "Tl-208","tolerance_keV": 6},
            {"energy_keV":  238.6, "rel_intensity":  45, "isotope": "Pb-212","tolerance_keV": 4},
        ],
    },
    {
        "name": "Monazite sand (NORM)",
        "category": "Natural",
        "description": "High-thorium mineral sand. Strong Th-232 chain; weaker U-238 chain. Tl-208 2614 keV very prominent.",
        "tags": ["geology", "NORM", "thorium", "mineral"],
        "lines": [
            {"energy_keV": 2614.5, "rel_intensity": 100, "isotope": "Tl-208","tolerance_keV": 6},
            {"energy_keV":  583.2, "rel_intensity":  85, "isotope": "Tl-208","tolerance_keV": 4},
            {"energy_keV":  238.6, "rel_intensity":  75, "isotope": "Pb-212","tolerance_keV": 4},
            {"energy_keV":  911.2, "rel_intensity":  50, "isotope": "Ac-228","tolerance_keV": 5},
            {"energy_keV": 1460.8, "rel_intensity":  30, "isotope": "K-40",  "tolerance_keV": 5},
        ],
    },
    {
        "name": "Potassium fertilizer (KCl)",
        "category": "Natural",
        "description": "Potassium chloride or sulphate fertilizer. Dominated by K-40 1461 keV; may show Cs-137 trace.",
        "tags": ["agriculture", "K-40", "NORM"],
        "lines": [
            {"energy_keV": 1460.8, "rel_intensity": 100, "isotope": "K-40", "tolerance_keV": 5},
        ],
    },
    {
        "name": "Depleted uranium (DU)",
        "category": "Industrial",
        "description": "Mainly U-238. Key Ra-226 daughters at 186, 352, 609 keV. Lower Th-232 chain.",
        "tags": ["uranium", "DU", "industrial"],
        "lines": [
            {"energy_keV":  185.7, "rel_intensity":  75, "isotope": "Ra-226","tolerance_keV": 4},
            {"energy_keV":  295.2, "rel_intensity":  35, "isotope": "Pb-214","tolerance_keV": 4},
            {"energy_keV":  351.9, "rel_intensity": 100, "isotope": "Pb-214","tolerance_keV": 4},
            {"energy_keV":  609.3, "rel_intensity":  60, "isotope": "Bi-214","tolerance_keV": 4},
            {"energy_keV":   92.8, "rel_intensity":  30, "isotope": "Th-234","tolerance_keV": 3},
        ],
    },
    {
        "name": "Reactor-released mixed fission products",
        "category": "Anthropogenic",
        "description": "Post-accident or release scenario. Cs-137, Cs-134, I-131, Ba-140/La-140.",
        "tags": ["fission", "reactor", "emergency"],
        "lines": [
            {"energy_keV":  661.7, "rel_intensity": 100, "isotope": "Cs-137","tolerance_keV": 4},
            {"energy_keV":  795.9, "rel_intensity":  80, "isotope": "Cs-134","tolerance_keV": 4},
            {"energy_keV":  604.7, "rel_intensity":  75, "isotope": "Cs-134","tolerance_keV": 4},
            {"energy_keV":  364.5, "rel_intensity":  60, "isotope": "I-131", "tolerance_keV": 4},
            {"energy_keV": 1596.2, "rel_intensity":  50, "isotope": "La-140","tolerance_keV": 5},
            {"energy_keV":  487.0, "rel_intensity":  30, "isotope": "La-140","tolerance_keV": 4},
        ],
    },
    {
        "name": "Cs-134 (reactor activation product)",
        "category": "Anthropogenic",
        "description": "Produced by neutron activation of Cs-133. Found together with Cs-137 after reactor accidents.",
        "tags": ["reactor", "Cs-134", "fallout"],
        "lines": [
            {"energy_keV":  604.7, "rel_intensity": 100, "isotope": "Cs-134","tolerance_keV": 4},
            {"energy_keV":  795.9, "rel_intensity":  85, "isotope": "Cs-134","tolerance_keV": 4},
            {"energy_keV": 1365.2, "rel_intensity":   3, "isotope": "Cs-134","tolerance_keV": 5},
        ],
    },
    {
        "name": "Radium-226 (legacy industrial)",
        "category": "Industrial",
        "description": "Old luminous paint, needles, or antiques. Ra-226 + full Rn-222 chain in secular equilibrium.",
        "tags": ["radium", "legacy", "industrial"],
        "lines": [
            {"energy_keV":  185.7, "rel_intensity":  60, "isotope": "Ra-226","tolerance_keV": 4},
            {"energy_keV":  295.2, "rel_intensity":  50, "isotope": "Pb-214","tolerance_keV": 4},
            {"energy_keV":  351.9, "rel_intensity": 100, "isotope": "Pb-214","tolerance_keV": 4},
            {"energy_keV":  609.3, "rel_intensity":  90, "isotope": "Bi-214","tolerance_keV": 4},
            {"energy_keV": 1764.5, "rel_intensity":  55, "isotope": "Bi-214","tolerance_keV": 5},
        ],
    },
    {
        "name": "Pu-239 / weapons-grade plutonium",
        "category": "Fissile",
        "description": "Weapons-grade Pu. Lines at 129, 203, 375, 413 keV from Pu-239 and decay daughters.",
        "tags": ["fissile", "plutonium", "weapons"],
        "lines": [
            {"energy_keV":  129.3, "rel_intensity":  10, "isotope": "Pu-239","tolerance_keV": 3},
            {"energy_keV":  203.5, "rel_intensity":   5, "isotope": "Pu-239","tolerance_keV": 4},
            {"energy_keV":  375.0, "rel_intensity":   5, "isotope": "Pu-239","tolerance_keV": 4},
            {"energy_keV":  413.7, "rel_intensity":   6, "isotope": "Pu-239","tolerance_keV": 4},
            {"energy_keV":  59.5,  "rel_intensity":  40, "isotope": "Am-241","tolerance_keV": 3},
        ],
    },
    {
        "name": "HEU (highly enriched uranium)",
        "category": "Fissile",
        "description": "Enriched U-235. Distinctive 185.7 keV line from U-235 (not Ra-226). Also 143, 163 keV.",
        "tags": ["fissile", "uranium", "weapons", "HEU"],
        "lines": [
            {"energy_keV":  143.8, "rel_intensity":  15, "isotope": "U-235", "tolerance_keV": 3},
            {"energy_keV":  163.3, "rel_intensity":   8, "isotope": "U-235", "tolerance_keV": 3},
            {"energy_keV":  185.7, "rel_intensity": 100, "isotope": "U-235", "tolerance_keV": 4},
            {"energy_keV":  205.3, "rel_intensity":  10, "isotope": "U-235", "tolerance_keV": 4},
        ],
    },
]


# ══════════════════════════════════════════════════════════════════════════════
#  LIBRARY LOADING
# ══════════════════════════════════════════════════════════════════════════════

def _parse_entry(d: dict, source_file: str = "built-in") -> LibraryEntry:
    lines = [
        LibraryLine(
            energy_keV    = float(l["energy_keV"]),
            rel_intensity = float(l.get("rel_intensity", 100)),
            isotope       = l.get("isotope", ""),
            tolerance_keV = float(l.get("tolerance_keV", 4.0)),
        )
        for l in d.get("lines", [])
    ]
    return LibraryEntry(
        name        = d["name"],
        category    = d.get("category", "Unknown"),
        description = d.get("description", ""),
        lines       = lines,
        tags        = d.get("tags", []),
        source_file = source_file,
    )


def load_library() -> list[LibraryEntry]:
    """Load all library entries: built-ins + user JSON files."""
    entries = [_parse_entry(d) for d in _BUILTIN_ENTRIES]

    for fp in sorted(LIBRARY_DIR.glob("*.json")):
        try:
            data = json.loads(fp.read_text())
            if isinstance(data, list):
                for d in data:
                    entries.append(_parse_entry(d, fp.name))
            elif isinstance(data, dict):
                entries.append(_parse_entry(data, fp.name))
        except Exception:
            pass  # skip malformed user files

    return entries


def save_user_entry(entry_dict: dict, filename: str) -> Path:
    """Save a user-defined library entry as JSON."""
    path = LIBRARY_DIR / filename
    path.write_text(json.dumps(entry_dict, indent=2))
    return path


def list_user_files() -> list[str]:
    return [f.name for f in sorted(LIBRARY_DIR.glob("*.json"))]


def delete_user_entry(filename: str) -> bool:
    path = LIBRARY_DIR / filename
    if path.exists():
        path.unlink()
        return True
    return False


# ══════════════════════════════════════════════════════════════════════════════
#  SCORING ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def _gaussian_weight(delta_keV: float, sigma: float) -> float:
    """Soft matching weight: 1 at perfect match, decaying with Gaussian."""
    return math.exp(-0.5 * (delta_keV / max(sigma, 0.1)) ** 2)


def score_entry(
        entry:           LibraryEntry,
        detected_peaks:  list[dict],   # list of {"energy_keV": float, "counts": float}
        tolerance_scale: float = 1.0,  # multiply all tolerances by this factor
) -> MatchResult:
    """
    Score one library entry against the set of detected peaks.

    detected_peaks: [{"energy_keV": float, "counts": float}, ...]
    Returns MatchResult with composite score and per-line breakdown.
    """
    if not entry.lines or not detected_peaks:
        return MatchResult(
            entry_name=entry.name, category=entry.category,
            description=entry.description, tags=entry.tags,
            overall_score=0.0, presence_score=0.0, energy_score=0.0,
            intensity_score=0.0, coverage_score=0.0,
            n_lines_matched=0, n_lines_total=len(entry.lines),
            n_peaks_spectrum=len(detected_peaks), n_peaks_explained=0,
            verdict="No data",
        )

    det_energies = np.array([p["energy_keV"] for p in detected_peaks], dtype=float)
    det_counts   = np.array([p.get("counts", 1.0) for p in detected_peaks], dtype=float)
    det_counts   = np.maximum(det_counts, 1.0)

    # ── 1. Match each library line to nearest detected peak ────────────────
    line_matches:   list[LineMatch] = []
    matched_det_idx: set[int]       = set()
    presence_weights                = []
    energy_weights                  = []
    intensity_pairs                 = []   # (lib_rel, det_rel) for matched pairs

    for lib_line in entry.lines:
        tol = lib_line.tolerance_keV * tolerance_scale
        sigma = tol / 2.5  # 1σ ≈ tolerance/2.5 so edge of window ≈ 2.5σ

        diffs = np.abs(det_energies - lib_line.energy_keV)
        best_idx = int(np.argmin(diffs))
        delta = float(diffs[best_idx])

        lm = LineMatch(
            lib_keV     = lib_line.energy_keV,
            lib_rel_int = lib_line.rel_intensity,
            isotope     = lib_line.isotope,
        )

        if delta <= tol:
            w = _gaussian_weight(delta, sigma)
            lm.matched    = True
            lm.det_keV    = float(det_energies[best_idx])
            lm.det_counts = float(det_counts[best_idx])
            lm.delta_keV  = round(delta, 2)

            matched_det_idx.add(best_idx)
            presence_weights.append(w * (lib_line.rel_intensity / 100.0))
            energy_weights.append(w)
            intensity_pairs.append((lib_line.rel_intensity, float(det_counts[best_idx])))
        else:
            # Penalty proportional to importance of missed line
            presence_weights.append(0.0)

        line_matches.append(lm)

    # ── 2. Presence score ─────────────────────────────────────────────────
    max_possible = sum(ll.rel_intensity / 100.0 for ll in entry.lines)
    presence_score = sum(presence_weights) / max(max_possible, 1e-9)
    presence_score = min(presence_score, 1.0)

    # ── 3. Energy alignment score ─────────────────────────────────────────
    energy_score = float(np.mean(energy_weights)) if energy_weights else 0.0

    # ── 4. Intensity pattern score ────────────────────────────────────────
    intensity_score = 0.0
    if len(intensity_pairs) >= 2:
        lib_ints = np.array([p[0] for p in intensity_pairs])
        det_ints = np.array([p[1] for p in intensity_pairs])
        # Normalise both to 0–1
        lib_norm = lib_ints / max(lib_ints.max(), 1)
        det_norm = det_ints / max(det_ints.max(), 1)
        # Pearson correlation (clamp to [0,1])
        if lib_norm.std() > 0 and det_norm.std() > 0:
            corr = float(np.corrcoef(lib_norm, det_norm)[0, 1])
            intensity_score = max(0.0, corr)
        else:
            intensity_score = 1.0 - float(np.mean(np.abs(lib_norm - det_norm)))
            intensity_score = max(0.0, intensity_score)
    elif len(intensity_pairs) == 1:
        intensity_score = 0.5  # single-line match: neutral intensity score

    # ── 5. Coverage score (spectrum peaks explained) ──────────────────────
    n_explained   = len(matched_det_idx)
    coverage_score = n_explained / max(len(detected_peaks), 1)

    # ── 6. Composite score ────────────────────────────────────────────────
    # Weights: presence is most important, energy quality next,
    # intensity pattern next, coverage last (avoids over-penalising
    # when spectrum has background peaks not in this entry)
    w_pres, w_en, w_int, w_cov = 0.45, 0.25, 0.20, 0.10
    overall = (
        w_pres * presence_score +
        w_en   * energy_score   +
        w_int  * intensity_score +
        w_cov  * coverage_score
    )

    # ── 7. Verdict text ───────────────────────────────────────────────────
    n_matched = sum(1 for lm in line_matches if lm.matched)
    n_total   = len(entry.lines)

    if overall >= 0.80:
        verdict = f"Strong match — {n_matched}/{n_total} lines present, pattern consistent"
    elif overall >= 0.55:
        verdict = f"Probable match — {n_matched}/{n_total} lines present"
    elif overall >= 0.30:
        verdict = f"Partial match — {n_matched}/{n_total} lines; may be mixture or interference"
    else:
        verdict = f"Weak / no match — only {n_matched}/{n_total} lines detected"

    return MatchResult(
        entry_name        = entry.name,
        category          = entry.category,
        description       = entry.description,
        tags              = entry.tags,
        overall_score     = round(overall, 4),
        presence_score    = round(presence_score, 4),
        energy_score      = round(energy_score, 4),
        intensity_score   = round(intensity_score, 4),
        coverage_score    = round(coverage_score, 4),
        n_lines_matched   = n_matched,
        n_lines_total     = n_total,
        n_peaks_spectrum  = len(detected_peaks),
        n_peaks_explained = n_explained,
        line_matches      = line_matches,
        verdict           = verdict,
    )


def match_spectrum(
        detected_peaks:   list[dict],
        library:          Optional[list[LibraryEntry]] = None,
        min_score:        float = 0.10,
        top_n:            int   = 10,
        tolerance_scale:  float = 1.0,
        category_filter:  Optional[list[str]] = None,
) -> list[MatchResult]:
    """
    Match detected peaks against the full library.

    Returns top_n results with score >= min_score, sorted descending by score.
    """
    if library is None:
        library = load_library()

    if category_filter:
        library = [e for e in library if e.category in category_filter]

    results = [
        score_entry(e, detected_peaks, tolerance_scale)
        for e in library
    ]
    results = [r for r in results if r.overall_score >= min_score]
    results.sort(key=lambda r: r.overall_score, reverse=True)
    return results[:top_n]


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS FOR UI
# ══════════════════════════════════════════════════════════════════════════════

def peaks_from_spectrum(
        counts:     list | np.ndarray,
        energies:   list | np.ndarray,
        peaks_dict: list[dict],          # from find_spectrum_peaks()
) -> list[dict]:
    """Convert find_spectrum_peaks output to {energy_keV, counts} dicts."""
    counts_arr = np.array(counts)
    result = []
    for pk in peaks_dict:
        ch  = pk["channel"]
        kev = pk["energy_keV"]
        cts = float(counts_arr[ch]) if 0 <= ch < len(counts_arr) else 1.0
        result.append({"energy_keV": kev, "counts": cts})
    return result


def all_categories(library: list[LibraryEntry]) -> list[str]:
    return sorted(set(e.category for e in library))
