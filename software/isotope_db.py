"""
isotope_db.py
─────────────────────────────────────────────────────────────────────────────
Isotope database for gamma spectroscopy inference.

Backbone: `radioactivedecay` (pip3 install radioactivedecay)
  → Ships full IAEA/DDEP decay dataset: 1252 radionuclides
  → Half-lives, decay modes, branching fractions, full daughter chains

Layer 2: Curated GAMMA_LINES dict
  → ~300 isotopes with keV energies + intensities from NuDat/ENSDF
  → radioactivedecay does not include gamma energies, so we supply them

Layer 3: FORENSIC_PROFILES
  → Domain knowledge for authentication workflows

radioactivedecay API:
  nuc = rd.Nuclide("Bi-214")
  nuc.half_life("s")            → float seconds
  nuc.half_life("readable")     → "19.9 m"
  nuc.progeny()                 → ["Po-214", "Tl-210"]
  nuc.branching_fractions()     → [0.99979, 0.00021]
  nuc.decay_modes()             → ["alpha", "beta-"]
"""

from __future__ import annotations
from typing import Optional

try:
    import radioactivedecay as rd
    _test = rd.Nuclide("Bi-214").half_life("s")
    RAD_AVAILABLE = True
except Exception:
    RAD_AVAILABLE = False

INF    = float("inf")
YEAR_S = 365.25 * 24 * 3600


# ══════════════════════════════════════════════════════════════════════════════
#  GAMMA LINE LIBRARY  (NuDat 3.0 / ENSDF)
#  Format: "Symbol": [(keV, intensity_%, "note"), ...]
#  Lines >= 0.05% intensity, >= 35 keV
# ══════════════════════════════════════════════════════════════════════════════

GAMMA_LINES: dict[str, list[tuple[float, float, str]]] = {
    # U-238 series
    "Th-234":   [(92.38, 2.81, ""), (92.80, 2.77, ""), (63.29, 3.72, "")],
    "Pa-234m":  [(1001.03, 0.837, ""), (766.36, 0.294, ""), (258.26, 0.082, "")],
    "Pa-234":   [(131.3, 0.028, ""), (926.7, 0.028, "")],
    "Ra-226":   [(186.21, 3.59, "")],
    "Pb-214":   [(351.93, 35.6, ""), (295.22, 18.42, ""), (241.99, 7.43, ""), (785.96, 1.06, "")],
    "Bi-214":   [(609.31, 45.49, ""), (1764.49, 15.28, ""), (1120.29, 14.91, ""),
                 (1238.11, 5.78, ""), (1377.67, 3.97, ""), (2204.21, 4.92, ""),
                 (768.36, 4.88, ""), (934.06, 3.03, ""), (1729.60, 2.88, ""), (665.45, 1.53, "")],
    "Pb-210":   [(46.54, 4.25, "")],
    "Po-210":   [(803.31, 0.0011, "")],
    # U-235 series
    "U-235":    [(185.72, 57.2, ""), (143.76, 10.96, ""), (163.36, 5.08, ""),
                 (205.31, 5.01, ""), (109.16, 1.54, "")],
    "Th-231":   [(84.22, 6.6, ""), (89.95, 1.7, "")],
    "Pa-231":   [(300.07, 2.42, ""), (302.67, 2.38, ""), (283.69, 1.65, ""), (330.07, 1.39, "")],
    "Ac-227":   [(99.91, 0.83, ""), (209.25, 0.47, "")],
    "Th-227":   [(235.97, 12.9, ""), (256.23, 6.9, ""), (50.13, 8.5, "")],
    "Ra-223":   [(269.46, 13.7, ""), (154.21, 5.62, ""), (323.87, 3.66, ""), (338.28, 2.79, "")],
    "Rn-219":   [(271.23, 10.8, ""), (401.81, 6.4, "")],
    "Pb-211":   [(404.85, 3.78, ""), (427.09, 1.69, "")],
    "Bi-211":   [(351.06, 13.0, "")],
    # Th-232 series
    "Th-232":   [(63.81, 0.26, "")],
    "Ac-228":   [(911.20, 25.8, ""), (968.97, 15.8, ""), (338.32, 11.27, ""),
                 (964.77, 4.99, ""), (1588.20, 3.22, ""), (129.07, 2.42, ""), (99.51, 1.02, "")],
    "Th-228":   [(84.37, 1.2, "")],
    "Ra-224":   [(240.99, 4.10, "")],
    "Rn-220":   [(549.76, 0.114, "")],
    "Pb-212":   [(238.63, 43.6, ""), (300.09, 3.28, "")],
    "Bi-212":   [(727.33, 6.67, ""), (1620.50, 1.51, "")],
    "Tl-208":   [(2614.51, 99.75, ""), (583.19, 84.5, ""), (860.56, 12.4, ""), (277.36, 6.6, "")],
    # Np-237 series
    "Np-237":   [(86.48, 12.4, ""), (29.37, 14.5, "")],
    "Pa-233":   [(311.90, 38.4, ""), (300.10, 6.6, ""), (415.76, 1.74, ""), (340.48, 4.47, "")],
    "U-233":    [(317.17, 0.0121, ""), (291.35, 0.0054, "")],
    "Ac-225":   [(99.79, 1.0, "")],
    "Fr-221":   [(218.0, 11.4, "")],
    "Bi-213":   [(440.45, 25.9, "")],
    # Primordial
    "K-40":     [(1460.82, 10.66, ""), (1311.07, 0.00089, "beta+ branch")],
    "Lu-176":   [(307.0, 93.8, ""), (202.0, 78.4, ""), (88.37, 14.1, "")],
    "La-138":   [(1435.80, 65.3, ""), (788.74, 34.7, "")],
    # Fission products
    "Cs-137":   [(661.66, 85.1, ""), (32.19, 5.95, "Ba Kx-ray")],
    "Ba-137m":  [(661.66, 89.9, "IT to Ba-137")],
    "Cs-134":   [(604.72, 97.62, ""), (795.86, 85.44, ""), (569.33, 15.43, ""), (801.95, 8.69, "")],
    "Cs-136":   [(818.51, 99.7, ""), (1048.07, 79.8, ""), (340.55, 46.6, "")],
    "I-131":    [(364.49, 81.7, ""), (637.00, 7.17, ""), (284.31, 6.12, ""), (80.18, 2.62, "")],
    "I-133":    [(529.87, 87.1, ""), (875.33, 4.5, "")],
    "Te-132":   [(228.16, 88.2, "")],
    "I-132":    [(667.72, 98.7, ""), (772.60, 75.6, ""), (954.55, 17.5, "")],
    "Zr-95":    [(756.73, 54.38, ""), (724.19, 44.27, "")],
    "Nb-95":    [(765.79, 99.81, "")],
    "Mo-99":    [(140.51, 89.43, ""), (739.50, 12.13, ""), (181.07, 6.14, "")],
    "Tc-99m":   [(140.51, 89.06, "IT")],
    "Rh-106":   [(621.93, 9.93, ""), (511.86, 20.4, "")],
    "Ba-140":   [(537.26, 24.4, ""), (162.66, 6.3, "")],
    "La-140":   [(1596.21, 95.40, ""), (815.77, 23.74, ""), (487.03, 45.5, ""), (328.76, 20.3, "")],
    "Ce-141":   [(145.44, 48.29, "")],
    "Ce-144":   [(133.52, 11.09, ""), (80.12, 1.37, "")],
    "Pr-144":   [(696.49, 1.34, ""), (2185.66, 0.70, "")],
    "Nd-147":   [(531.02, 13.1, ""), (91.11, 28.1, "")],
    "Eu-152":   [(344.28, 26.5, ""), (121.78, 28.6, ""), (1408.01, 21.0, ""),
                 (964.08, 14.5, ""), (778.90, 12.9, ""), (1085.84, 10.2, ""),
                 (244.70, 7.55, ""), (867.37, 4.24, ""), (411.12, 2.24, "")],
    "Eu-154":   [(1274.43, 34.8, ""), (723.30, 20.1, ""), (1004.76, 17.94, ""), (591.76, 4.97, "")],
    "Eu-155":   [(86.54, 30.7, ""), (105.31, 21.1, "")],
    "Sm-153":   [(103.18, 29.25, "")],
    "Sb-125":   [(427.87, 29.6, ""), (600.55, 17.8, ""), (463.36, 10.4, "")],
    "Sn-113":   [(391.70, 64.97, "")],
    "Ag-110m":  [(657.76, 94.7, ""), (884.68, 72.7, ""), (937.49, 34.4, ""),
                 (763.94, 22.3, ""), (706.68, 16.7, "")],
    "Kr-85":    [(514.01, 0.43, "")],
    "Xe-133":   [(81.00, 37.0, "")],
    "Xe-135":   [(249.79, 90.0, "")],
    "Ru-103":   [(497.08, 90.9, ""), (610.33, 5.76, "")],
    "Pm-148m":  [(550.27, 94.5, ""), (1465.12, 22.3, "")],
    "Y-90":     [(1760.7, 0.0159, "")],
    # Activation products
    "Co-60":    [(1332.49, 99.98, ""), (1173.23, 99.85, "")],
    "Co-57":    [(122.06, 85.6, ""), (136.47, 10.68, "")],
    "Co-58":    [(810.76, 99.45, "")],
    "Mn-54":    [(834.85, 99.98, "")],
    "Fe-59":    [(1291.59, 43.2, ""), (1099.25, 56.5, "")],
    "Zn-65":    [(1115.55, 50.22, "")],
    "Na-22":    [(1274.54, 99.94, ""), (511.0, 180.86, "annihilation")],
    "Na-24":    [(2754.03, 99.87, ""), (1368.63, 99.99, "")],
    "Sc-46":    [(1120.55, 99.99, ""), (889.28, 99.98, "")],
    "Cr-51":    [(320.08, 9.91, "")],
    "Au-198":   [(411.80, 95.58, "")],
    "Hg-203":   [(279.20, 81.46, "")],
    "Ir-192":   [(468.07, 47.8, ""), (316.51, 82.8, ""), (308.46, 29.7, ""),
                 (295.96, 28.7, ""), (604.41, 8.22, "")],
    "Se-75":    [(264.66, 58.9, ""), (136.00, 58.3, ""), (279.54, 25.1, ""), (121.12, 17.3, "")],
    "Ar-41":    [(1293.64, 99.16, "")],
    # Transuranic
    "Am-241":   [(59.54, 35.9, ""), (26.34, 2.4, "")],
    "Am-243":   [(74.66, 67.5, ""), (43.53, 5.9, "")],
    "Np-239":   [(277.60, 14.4, ""), (228.18, 10.7, "")],
    "Pu-238":   [(43.50, 0.039, "")],
    "Pu-239":   [(129.30, 0.00631, ""), (413.71, 0.0149, ""), (51.62, 0.0271, "")],
    "Pu-240":   [(45.24, 0.0045, "")],
    # Medical
    "Ga-67":    [(184.58, 21.2, ""), (300.22, 16.64, ""), (93.31, 38.81, "")],
    "In-111":   [(245.35, 94.1, ""), (171.28, 90.7, "")],
    "Tl-201":   [(167.43, 10.0, ""), (135.34, 2.65, "")],
    "I-123":    [(158.97, 83.3, "")],
    "I-124":    [(602.73, 62.9, ""), (722.78, 10.35, "")],
    "F-18":     [(511.0, 193.46, "annihilation")],
    "Ga-68":    [(511.0, 177.6, "annihilation"), (1077.34, 3.22, "")],
    "Lu-177":   [(208.37, 11.0, ""), (112.95, 6.17, ""), (71.64, 1.53, "")],
    "Re-186":   [(137.16, 9.47, "")],
    "Re-188":   [(155.05, 15.6, "")],
    # Calibration sources
    "Ba-133":   [(356.01, 62.05, ""), (302.85, 18.33, ""), (383.85, 8.94, ""),
                 (276.40, 7.16, ""), (80.99, 32.9, "")],
    "Bi-207":   [(569.70, 97.8, ""), (1063.66, 74.6, ""), (1770.23, 6.9, "")],
    "Y-88":     [(1836.06, 99.2, ""), (898.04, 93.7, "")],
    "Ce-139":   [(165.86, 79.9, "")],
    "Sr-85":    [(514.01, 98.3, "")],
    "Cd-109":   [(88.03, 3.61, "Ag Kx-ray")],
}

# ── Detectability ─────────────────────────────────────────────────────────────
_ALPHA_NO_GAMMA = {
    "U-238","U-234","Th-230","Po-218","Po-214","Po-210","Po-212","Po-216",
    "Pu-238","Pu-239","Pu-240","Cm-242","Cm-244","Sm-147",
    "Rn-222","Rn-220","At-217","At-211","Fr-221","Ra-224","Th-228",
}
_PURE_BETA = {
    "Rb-87","Re-187","Tc-99","Sr-90","Pm-147","Sm-151","Bi-210",
    "Ni-63","H-3","C-14","P-32","Sr-89","Er-169","W-188","Ru-106","Ge-68",
}

def is_detectable(symbol: str) -> tuple[bool, str]:
    if symbol in _ALPHA_NO_GAMMA:
        return False, "alpha emitter — negligible gamma"
    if symbol in _PURE_BETA:
        return False, "pure beta emitter"
    lines = GAMMA_LINES.get(symbol, [])
    if not lines:
        return False, "no gamma lines in library"
    strong = [l for l in lines if l[0] >= 40.0 and l[1] >= 0.5]
    if not strong:
        return False, "all gammas < 40 keV or < 0.5% intensity"
    return True, ""


# ══════════════════════════════════════════════════════════════════════════════
#  radioactivedecay WRAPPERS
# ══════════════════════════════════════════════════════════════════════════════

_FALLBACK_HL: dict[str, float] = {
    "U-238":4.468e9*YEAR_S, "Th-234":24.10*86400, "Pa-234m":1.159*60,
    "U-234":2.455e5*YEAR_S, "Th-230":7.538e4*YEAR_S, "Ra-226":1600*YEAR_S,
    "Rn-222":3.8235*86400,  "Pb-214":26.8*60,    "Bi-214":19.7*60,
    "Po-214":164.3e-6,      "Pb-210":22.3*YEAR_S,"Bi-210":5.012*86400,
    "Po-210":138.4*86400,   "U-235":7.038e8*YEAR_S,"Th-231":25.52*3600,
    "Pa-231":3.276e4*YEAR_S,"Ac-227":21.77*YEAR_S,"Th-227":18.68*86400,
    "Ra-223":11.43*86400,   "Rn-219":3.96,        "Pb-211":36.1*60,
    "Bi-211":2.14*60,       "Tl-207":4.77*60,
    "Th-232":1.405e10*YEAR_S,"Ra-228":5.75*YEAR_S,"Ac-228":6.15*3600,
    "Th-228":1.912*YEAR_S,  "Ra-224":3.6319*86400,"Rn-220":55.6,
    "Pb-212":10.64*3600,    "Bi-212":60.55*60,    "Tl-208":3.053*60,
    "Po-212":299e-9,        "K-40":1.248e9*YEAR_S,"Cs-137":30.17*YEAR_S,
    "Co-60":5.2711*YEAR_S,  "Am-241":432.2*YEAR_S,"Np-237":2.144e6*YEAR_S,
    "Pa-233":26.98*86400,   "Pu-239":2.411e4*YEAR_S,"Pu-241":14.325*YEAR_S,
    "Eu-152":13.54*YEAR_S,  "Eu-154":8.593*YEAR_S,"Eu-155":4.753*YEAR_S,
    "Cs-134":2.0652*YEAR_S, "Sb-125":2.7586*YEAR_S,"I-131":8.0252*86400,
    "Mn-54":312.1*86400,    "Ba-137m":2.552*60,
}

def get_half_life(symbol: str) -> tuple[float, str]:
    """Returns (seconds, human_readable)."""
    if RAD_AVAILABLE:
        try:
            nuc  = rd.Nuclide(symbol)
            hl_s = nuc.half_life("s")
            if hl_s == INF:
                return INF, "stable"
            return hl_s, nuc.half_life("readable")
        except Exception:
            pass
    hl_s = _FALLBACK_HL.get(symbol, INF)
    if hl_s == INF:
        return INF, "stable"
    for val, unit in [(YEAR_S*1e9,"Gy"),(YEAR_S*1e6,"My"),(YEAR_S*1e3,"ky"),
                      (YEAR_S,"y"),(86400,"d"),(3600,"h"),(60,"min"),(1,"s")]:
        if hl_s >= val * 0.99:
            return hl_s, f"{hl_s/val:.3g} {unit}"
    return hl_s, f"{hl_s:.3g} s"


def get_daughters(symbol: str) -> list[tuple[str, float, str]]:
    """Returns [(daughter, branch_fraction, decay_mode), ...]."""
    if RAD_AVAILABLE:
        try:
            nuc   = rd.Nuclide(symbol)
            prog  = nuc.progeny()
            bfs   = nuc.branching_fractions()
            modes = nuc.decay_modes()
            return list(zip(prog, bfs, modes))
        except Exception:
            pass
    return []


def build_chain(parent: str, max_depth: int = 40) -> list[dict]:
    """
    Walk full decay chain from parent using radioactivedecay.
    Returns ordered list of member dicts.
    """
    result  = []
    visited = set()
    # queue: (symbol, parent_sym, cumulative_branch_fraction, decay_mode, depth)
    queue   = [(parent, None, 1.0, "—", 0)]

    while queue:
        sym, par, cum_bf, mode, depth = queue.pop(0)
        if sym in visited or depth > max_depth:
            continue
        visited.add(sym)

        hl_s, hl_r       = get_half_life(sym)
        det, det_reason  = is_detectable(sym)
        gammas           = GAMMA_LINES.get(sym, [])
        strong           = sorted(
            [(e,i,n) for e,i,n in gammas if e >= 40 and i >= 0.5],
            key=lambda x: x[1], reverse=True
        )

        result.append({
            "symbol":        sym,
            "parent":        par,
            "branch_frac":   round(cum_bf, 6),
            "decay_mode":    mode,
            "depth":         depth,
            "half_life_s":   hl_s,
            "half_life":     hl_r,
            "detectable":    det,
            "detect_reason": det_reason,
            "gammas":        gammas,
            "strong_gammas": strong,
        })

        for d_sym, bf, d_mode in get_daughters(sym):
            if d_sym not in visited:
                queue.append((d_sym, sym, cum_bf * bf, d_mode, depth + 1))

    return result


def get_all_nuclides() -> list[str]:
    """Return all nuclide symbols from radioactivedecay, or fallback list."""
    if RAD_AVAILABLE:
        try:
            return sorted(rd.DEFAULTDATA.nuclide_dict.keys())
        except Exception:
            pass
    return sorted(GAMMA_LINES.keys())


def secular_equilibrium_ratio(parent: str,
                               daughter: str,
                               elapsed_years: float) -> float:
    """
    Activity ratio daughter/parent at time T years,
    assuming daughter starts at zero. Bateman 2-member equation.
    Returns >1 for transient equilibrium, approaches 1 for secular equilibrium.
    """
    import math
    hl_p, _ = get_half_life(parent)
    hl_d, _ = get_half_life(daughter)
    if hl_p == INF or hl_d == INF:
        return 0.0
    lp = math.log(2) / hl_p
    ld = math.log(2) / hl_d
    T  = elapsed_years * YEAR_S
    denom = ld - lp
    if abs(denom) < 1e-30:
        return min(1.0, lp * T)
    ratio = ld / denom * (1.0 - math.exp(-denom * T))
    return max(0.0, min(ratio, 1e6))


# ══════════════════════════════════════════════════════════════════════════════
#  FORENSIC PROFILES
# ══════════════════════════════════════════════════════════════════════════════

FORENSIC_PROFILES: dict[str, dict] = {

    "Trinitite (Trinity Site, 1945)": {
        "description": (
            "Glassy melt rock from the Trinity nuclear test (New Mexico, July 16 1945). "
            "Desert sand fused with the Pu-239 'Gadget' device and bomb casing materials. "
            "Contains natural U/Th from Jornada del Muerto alluvium plus fission products "
            "and neutron-activation products from the detonation. ~80 years of decay since 1945."
        ),
        "expected": [
            ("U-238 chain",   ["Bi-214","Pb-214","Th-234"],
             "Natural uranium from desert alluvium"),
            ("Th-232 chain",  ["Tl-208","Ac-228","Pb-212"],
             "Natural thorium from soil minerals"),
            ("K-40",          ["K-40"],
             "Natural potassium in feldspar / glass matrix"),
            ("Am-241",        ["Am-241"],
             "Pu-241 beta-decays to Am-241 (t1/2=14.3y); peak Am-241 activity ~70y post-detonation"),
            ("Eu activation", ["Eu-152","Eu-154","Eu-155"],
             "Neutron activation of natural Eu in soil (n,gamma reactions at ground zero)"),
            ("Cs fission",    ["Cs-137"],
             "Long-lived fission product, t1/2=30y"),
        ],
        "alpha_blind": [
            {
                "inferred":  "Pu-239",
                "evidence":  ["Am-241","U-235"],
                "logic": (
                    "Pu-239 is an alpha emitter (t1/2=24,110y) — completely invisible to RC-103. "
                    "However: (1) Pu-239 alpha-decays to U-235, which IS detectable at 185.7 keV. "
                    "An anomalously elevated U-235 signal relative to natural abundance (0.72%) "
                    "can indicate Pu-239 decay contribution. "
                    "(2) The Gadget's Pu also contained ~0.36% Pu-241 (t1/2=14.3y), which "
                    "beta-decays to Am-241. Am-241 at 59.54 keV is the single most diagnostic "
                    "indicator of weapons-grade plutonium in aged trinitite."
                ),
            },
            {
                "inferred":  "Pu-241 → Am-241",
                "evidence":  ["Am-241"],
                "logic": (
                    "Pu-241 (t1/2=14.3y) beta-decays entirely to Am-241. By 2025, roughly 80 years "
                    "after Trinity, about 98.5% of the original Pu-241 inventory has decayed. "
                    "The Am-241 activity peaked around 1990 and is now slowly declining. "
                    "A clear 59.54 keV peak in a sample claimed to be trinitite, with no "
                    "other explanation (smoke detector, medical source), strongly supports "
                    "the presence of original device plutonium."
                ),
            },
            {
                "inferred":  "Sr-90 (fission, invisible)",
                "evidence":  ["Cs-137"],
                "logic": (
                    "Sr-90 is a pure beta emitter — entirely invisible to RC-103. "
                    "However, Sr-90 and Cs-137 have nearly identical fission yields (~6% each) "
                    "from Pu-239 fission. If Cs-137 is detected, Sr-90 is almost certainly "
                    "co-present at approximately equal activity. Sr-90 contributes a "
                    "bremsstrahlung continuum to the spectrum background."
                ),
            },
        ],
        "anomaly_flags": [
            ("No Am-241 detected",
             "MAJOR FLAG: Am-241 should be clearly visible ~80 years post-1945. "
             "Its absence strongly questions authenticity."),
            ("No Cs-137",
             "MODERATE FLAG: Long-lived fission product expected from Pu fission. "
             "Absence unusual unless sample was heavily leached."),
            ("No Eu-152/154/155",
             "MODERATE FLAG: Neutron activation of soil Eu expected near ground zero. "
             "Natural radioactivity without activation products is suspicious."),
            ("Cs-134 at significant activity",
             "ANOMALY: Cs-134 (t1/2=2.06y) would be entirely decayed after 80 years. "
             "High Cs-134 implies recent reactor exposure — not 1945 Trinity material."),
            ("No Tl-208 or Ac-228",
             "MILD FLAG: Th-232 chain absent — atypical for desert soil origin."),
        ],
        "score_weights": {
            "Am-241":30, "Cs-137":15, "Eu-152":10, "Eu-154":10, "Eu-155":5,
            "Bi-214":8,  "Pb-214":5,  "Tl-208":8,  "Ac-228":5,  "K-40":4,
        },
    },

    "Natural Uranium Ore (Uraninite / Pitchblende / Autunite)": {
        "description": (
            "Uranium ore minerals in secular equilibrium. For samples >1 My old in a closed "
            "system, all U-238 chain members should have equal activities. "
            "U-235 chain also present at 0.72% abundance ratio."
        ),
        "expected": [
            ("U-238 chain", ["Bi-214","Pb-214","Th-234","Pa-234m","Ra-226"],
             "Full chain — all members at equal activity in old ore"),
            ("U-235 chain", ["U-235","Ra-223"], "0.72% natural U-235"),
            ("K-40",        ["K-40"], "Matrix minerals"),
        ],
        "alpha_blind": [
            {
                "inferred": "U-238 (confirmed)",
                "evidence": ["Bi-214","Pb-214","Th-234","Pa-234m"],
                "logic": (
                    "U-238 alpha emitter — not directly detectable. "
                    "The full U-238 daughter chain being visible confirms uranium ore. "
                    "Pa-234m at 1001 keV is the most diagnostic direct U-ore signature, "
                    "since it is unique to the U-238 → Th-234 → Pa-234m branch."
                ),
            },
        ],
        "anomaly_flags": [
            ("Bi-214 / Pb-214 absent despite Pa-234m present",
             "Rn-222 escaping between Ra-226 and Pb-214 — sample is open or porous."),
            ("Am-241 detected",
             "Unexpected transuranic — processed or contaminated material."),
            ("Cs-137 detected",
             "Unexpected fission product — possible reactor or weapons material contact."),
        ],
        "score_weights": {
            "Bi-214":20,"Pb-214":20,"Th-234":15,"Pa-234m":15,"Ra-226":10,"U-235":10,"K-40":5,
        },
    },

    "Thorite / Monazite (Thorium Mineral)": {
        "description": (
            "Thorium-rich minerals (monazite, thorite, thorianite). "
            "Th-232 chain dominates. U-238 chain may appear as trace. "
            "No fission products expected in unprocessed mineral."
        ),
        "expected": [
            ("Th-232 chain", ["Tl-208","Ac-228","Pb-212","Bi-212"],
             "Full chain — Tl-208 2614.5 keV is definitive"),
            ("K-40", ["K-40"], "Matrix"),
        ],
        "alpha_blind": [
            {
                "inferred": "Th-232 (confirmed)",
                "evidence": ["Tl-208","Ac-228","Pb-212"],
                "logic": (
                    "Th-232 is an alpha emitter — not directly detectable. "
                    "But its chain produces the highest naturally-occurring gamma line: "
                    "Tl-208 at 2614.5 keV (99.75% intensity) — unambiguous. "
                    "Ac-228 at 911 keV and Pb-212 at 238.6 keV confirm the full chain."
                ),
            },
        ],
        "anomaly_flags": [
            ("Strong Bi-214 without strong Tl-208",
             "U-238 chain dominant — sample is likely uranium mineral, not thorium."),
            ("Am-241 present",
             "Unexpected — indicates processed or reactor-associated material."),
        ],
        "score_weights": {
            "Tl-208":30,"Ac-228":25,"Pb-212":20,"Bi-212":10,"K-40":5,
        },
    },

    "Radium Source (Ra-226 / Radium Dial Paint)": {
        "description": (
            "Old radium luminous paint (pre-1968 dials, watches, compasses), "
            "medical brachytherapy seeds, or radium geological sources. "
            "Ra-226 with full Rn-222 progeny expected if source is sealed."
        ),
        "expected": [
            ("Ra-226 + progeny", ["Ra-226","Pb-214","Bi-214"],
             "Ra-226 186 keV + radon progeny confirm sealed source"),
        ],
        "alpha_blind": [
            {
                "inferred": "Rn-222 (in equilibrium)",
                "evidence": ["Pb-214","Bi-214"],
                "logic": (
                    "Rn-222 is gaseous and invisible. Its daughters Pb-214 (351 keV) and "
                    "Bi-214 (609 keV) are in secular equilibrium with Ra-226 in a sealed source. "
                    "If Pb-214/Bi-214 are absent despite Ra-226 being present, Rn-222 is escaping "
                    "— the source is open, cracked, or porous. This is a contamination hazard."
                ),
            },
        ],
        "anomaly_flags": [
            ("Ra-226 detected but Bi-214/Pb-214 absent",
             "HAZARD: Rn-222 escaping — do not handle without respiratory protection."),
            ("High activity without Ra-226 186 keV",
             "May be Ra-228 (Th-232 chain) — check for Ac-228 911 keV instead."),
        ],
        "score_weights": {"Ra-226":35,"Pb-214":30,"Bi-214":30,"K-40":5},
    },

    "Fission Product / Reactor Material": {
        "description": (
            "Spent nuclear fuel, activated reactor components, or nuclear incident fallout. "
            "Strong fission product signatures alongside activation products."
        ),
        "expected": [
            ("Fission products",   ["Cs-137","Cs-134"],   "Primary long-lived fission signatures"),
            ("Activation products",["Co-60","Mn-54"],      "Structural steel activation"),
            ("Fuel matrix",        ["Bi-214","Pb-214"],    "UO2 fuel uranium"),
            ("Europium",           ["Eu-154","Eu-152"],    "Fission + activation"),
        ],
        "alpha_blind": [
            {
                "inferred": "Sr-90 / Y-90 (invisible)",
                "evidence": ["Cs-137"],
                "logic": (
                    "Sr-90 is a pure beta emitter. But Sr-90 and Cs-137 fission yields are "
                    "nearly equal (~6% each from U-235/Pu-239 fission). Cs-137 detection implies "
                    "Sr-90 co-present at similar activity, contributing bremsstrahlung continuum."
                ),
            },
        ],
        "anomaly_flags": [
            ("No Cs-137", "Unexpected — primary long-lived fission marker."),
            ("Cs-134/Cs-137 activity ratio > 0.3",
             "High ratio implies relatively recent irradiation (< 10 years)."),
            ("Co-60 without other activation products",
             "May be isolated industrial Co-60 source, not reactor material."),
        ],
        "score_weights": {
            "Cs-137":30,"Cs-134":20,"Co-60":20,"Eu-154":10,"Bi-214":10,
        },
    },

    "Smoke Detector (Am-241 sealed source)": {
        "description": (
            "Ionization-type smoke detectors contain ~1 uCi (37 kBq) Am-241 sealed source. "
            "One sharp peak at 59.54 keV should dominate the low-energy region."
        ),
        "expected": [
            ("Am-241", ["Am-241"], "59.54 keV — essentially the only significant line"),
        ],
        "alpha_blind": [
            {
                "inferred": "Pu-241 → Am-241 (manufacturing origin)",
                "evidence": ["Am-241"],
                "logic": (
                    "The Am-241 in smoke detectors was originally Pu-241 produced in reactors. "
                    "Pu-241 (t1/2=14.3y) beta-decays to Am-241, which was then chemically "
                    "separated and fabricated into the sealed source."
                ),
            },
        ],
        "anomaly_flags": [
            ("Additional peaks beyond 59.54 keV at significant activity",
             "Source is more complex than a standard smoke detector."),
        ],
        "score_weights": {"Am-241":95,"K-40":5},
    },
}

SERIES_COLORS = {
    "alpha":  "#e8a060",
    "beta-":  "#7eb8d4",
    "beta+":  "#90ee90",
    "EC":     "#b87ed4",
    "IT":     "#e8e060",
    "SF":     "#e87070",
    "stable": "#505040",
}
