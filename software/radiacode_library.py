"""
radiacode_library.py
────────────────────
The Radiacode RC-103 ships with a built-in isotope identification library
covering ~80 nuclides commonly encountered in environmental, industrial,
medical and security contexts.  This module reproduces that library as a
Python dict so GammaLab can use it for peak matching and identification,
supplementing or cross-checking the ENSDF database.

Each entry:
    symbol  : nuclide name  (e.g. "Cs-137")
    lines   : list of (energy_keV, intensity_pct) tuples — only lines ≥ 1%
    half_life: human-readable string
    category: one of NORM / Fission / Activation / Medical / Industrial /
              Calibration / Cosmic / Natural
    notes   : brief description

Usage:
    from radiacode_library import RC_LIBRARY, match_rc_library
    matches = match_rc_library(detected_peaks_keV, tolerance_keV=10)
"""

from __future__ import annotations

RC_LIBRARY: list[dict] = [

    # ── Natural / primordial ───────────────────────────────────────────────

    {"symbol": "K-40",    "half_life": "1.248×10⁹ y",  "category": "Natural",
     "lines": [(1460.8, 10.7)],
     "notes": "Ubiquitous in soils, fertilizers, food; dominant natural gamma line"},

    {"symbol": "U-238",   "half_life": "4.47×10⁹ y",   "category": "NORM",
     "lines": [(49.6, 0.07)],   # very weak; detected via daughters
     "notes": "Detected mainly through Pa-234m (1001 keV) daughter"},

    {"symbol": "Th-232",  "half_life": "1.40×10¹⁰ y",  "category": "NORM",
     "lines": [(63.8, 0.26)],   # detected mainly via daughters
     "notes": "Detected mainly through Ac-228 / Tl-208 daughters"},

    # ── Uranium-238 decay series daughters ────────────────────────────────

    {"symbol": "Th-234",  "half_life": "24.1 d",        "category": "NORM",
     "lines": [(63.3, 3.7), (92.4, 2.7), (92.8, 2.6)],
     "notes": "First daughter of U-238"},

    {"symbol": "Pa-234m", "half_life": "1.17 min",      "category": "NORM",
     "lines": [(1001.0, 0.84), (766.4, 0.30)],
     "notes": "U-238 series; 1001 keV used as U-238 proxy"},

    {"symbol": "Ra-226",  "half_life": "1600 y",        "category": "NORM",
     "lines": [(186.2, 3.6)],
     "notes": "Overlaps with U-235 at 186 keV; distinguish by ratio"},

    {"symbol": "Rn-222",  "half_life": "3.82 d",        "category": "NORM",
     "lines": [],   # no significant gammas — detected via daughters
     "notes": "Radon gas; detected via Pb-214 / Bi-214 daughters"},

    {"symbol": "Pb-214",  "half_life": "26.8 min",      "category": "NORM",
     "lines": [(295.2, 18.4), (351.9, 35.6), (241.9, 7.3)],
     "notes": "Radon daughter; indicates Rn-222 ingrowth"},

    {"symbol": "Bi-214",  "half_life": "19.7 min",      "category": "NORM",
     "lines": [(609.3, 45.5), (1120.3, 14.9), (1764.5, 15.3),
               (1238.1, 5.8), (2204.2, 5.0), (768.4, 4.9),
               (934.1, 3.1), (1377.7, 4.0)],
     "notes": "Key U-series indicator; 609 keV is strongest natural line"},

    {"symbol": "Pb-210",  "half_life": "22.3 y",        "category": "NORM",
     "lines": [(46.5, 4.3)],
     "notes": "Long-lived Rn-222 granddaughter; low-energy line"},

    {"symbol": "Po-210",  "half_life": "138.4 d",       "category": "NORM",
     "lines": [],    # alpha emitter, no significant gammas
     "notes": "Pure alpha emitter; end of U-238 series"},

    # ── Thorium-232 decay series daughters ────────────────────────────────

    {"symbol": "Ra-228",  "half_life": "5.75 y",        "category": "NORM",
     "lines": [(13.5, 1.6)],   # very low; detected via Ac-228
     "notes": "First Th-232 daughter; low-energy only"},

    {"symbol": "Ac-228",  "half_life": "6.15 h",        "category": "NORM",
     "lines": [(338.3, 11.3), (911.2, 25.8), (964.8, 5.0),
               (969.0, 15.8), (1588.2, 3.2)],
     "notes": "Th-232 series; 911 keV is key line"},

    {"symbol": "Th-228",  "half_life": "1.91 y",        "category": "NORM",
     "lines": [(84.4, 1.2)],
     "notes": "Th-232 series"},

    {"symbol": "Ra-224",  "half_life": "3.63 d",        "category": "NORM",
     "lines": [(240.9, 4.1)],
     "notes": "Th-232 series"},

    {"symbol": "Pb-212",  "half_life": "10.6 h",        "category": "NORM",
     "lines": [(238.6, 43.3), (300.1, 3.3)],
     "notes": "Th-232 series; 239 keV is diagnostic"},

    {"symbol": "Bi-212",  "half_life": "60.6 min",      "category": "NORM",
     "lines": [(727.3, 6.7), (1620.7, 1.5)],
     "notes": "Th-232 series"},

    {"symbol": "Tl-208",  "half_life": "3.05 min",      "category": "NORM",
     "lines": [(2614.5, 99.8), (583.2, 84.5), (860.6, 12.0),
               (277.4, 6.6)],
     "notes": "End of Th-232 series; 2615 keV is highest common natural line"},

    # ── Uranium-235 series ─────────────────────────────────────────────────

    {"symbol": "U-235",   "half_life": "7.04×10⁸ y",   "category": "NORM",
     "lines": [(185.7, 57.2), (143.8, 10.9), (163.4, 5.1)],
     "notes": "185.7 keV overlaps Ra-226; ratio used for U enrichment"},

    {"symbol": "Pa-231",  "half_life": "3.28×10⁴ y",   "category": "NORM",
     "lines": [(302.0, 2.4), (283.7, 1.7)],
     "notes": "U-235 series"},

    {"symbol": "Ac-227",  "half_life": "21.8 y",        "category": "NORM",
     "lines": [(99.9, 1.1)],
     "notes": "U-235 series; low-energy"},

    {"symbol": "Th-227",  "half_life": "18.7 d",        "category": "NORM",
     "lines": [(235.9, 12.8), (256.2, 6.8), (50.1, 8.4)],
     "notes": "U-235 series"},

    {"symbol": "Fr-223",  "half_life": "22.0 min",      "category": "NORM",
     "lines": [(79.7, 9.9)],
     "notes": "U-235 series"},

    {"symbol": "Ra-223",  "half_life": "11.4 d",        "category": "NORM",
     "lines": [(269.5, 13.6), (154.2, 5.6), (323.9, 3.9)],
     "notes": "U-235 series; also used medically"},

    {"symbol": "Bi-211",  "half_life": "2.14 min",      "category": "NORM",
     "lines": [(351.1, 12.8)],
     "notes": "U-235 series"},

    # ── Fission products ───────────────────────────────────────────────────

    {"symbol": "Cs-137",  "half_life": "30.2 y",        "category": "Fission",
     "lines": [(661.7, 85.1)],
     "notes": "Most important anthropogenic gamma emitter; ubiquitous after 1950s tests"},

    {"symbol": "Ba-137m", "half_life": "2.55 min",      "category": "Fission",
     "lines": [(661.7, 89.9)],
     "notes": "Metastable daughter of Cs-137; the 662 keV line originates here"},

    {"symbol": "Cs-134",  "half_life": "2.07 y",        "category": "Fission",
     "lines": [(604.7, 97.6), (795.9, 85.4), (569.3, 15.4),
               (802.0, 8.7), (1038.0, 1.0)],
     "notes": "Fukushima/Chernobyl marker; ratio Cs-134/Cs-137 dates contamination"},

    {"symbol": "Cs-136",  "half_life": "13.2 d",        "category": "Fission",
     "lines": [(818.5, 99.7), (1048.1, 79.8), (1235.4, 19.8)],
     "notes": "Short-lived fission product"},

    {"symbol": "Ce-144",  "half_life": "284.9 d",       "category": "Fission",
     "lines": [(133.5, 11.1)],
     "notes": "Fission product; detected via Pr-144 daughter"},

    {"symbol": "Pr-144",  "half_life": "17.3 min",      "category": "Fission",
     "lines": [(2185.7, 0.7), (696.5, 1.5)],
     "notes": "Ce-144 daughter"},

    {"symbol": "Ru-106",  "half_life": "371.8 d",       "category": "Fission",
     "lines": [],    # no significant gamma; detected via Rh-106
     "notes": "Detected via Rh-106 daughter (512, 621, 1050 keV)"},

    {"symbol": "Rh-106",  "half_life": "29.8 s",        "category": "Fission",
     "lines": [(511.9, 20.4), (621.9, 9.9), (1050.4, 1.5)],
     "notes": "Ru-106 daughter"},

    {"symbol": "I-131",   "half_life": "8.02 d",        "category": "Fission",
     "lines": [(364.5, 81.5), (637.0, 7.2), (284.3, 6.1)],
     "notes": "Major thyroid dose contributor after reactor accidents"},

    {"symbol": "I-133",   "half_life": "20.8 h",        "category": "Fission",
     "lines": [(529.9, 86.6), (875.3, 4.5)],
     "notes": "Short-lived fission product"},

    {"symbol": "Te-132",  "half_life": "3.20 d",        "category": "Fission",
     "lines": [(228.2, 88.2)],
     "notes": "Fission product; precursor to I-132"},

    {"symbol": "Sr-90",   "half_life": "28.8 y",        "category": "Fission",
     "lines": [],    # pure beta emitter
     "notes": "Pure beta — not directly detectable by gamma spec"},

    {"symbol": "Y-90",    "half_life": "64.1 h",        "category": "Fission",
     "lines": [(1760.7, 0.02)],  # bremsstrahlung mainly
     "notes": "Sr-90 daughter; beta emitter, very weak gamma"},

    {"symbol": "Zr-95",   "half_life": "64.0 d",        "category": "Fission",
     "lines": [(756.7, 54.4), (724.2, 44.2)],
     "notes": "Early fission product"},

    {"symbol": "Nb-95",   "half_life": "35.0 d",        "category": "Fission",
     "lines": [(765.8, 100.0)],
     "notes": "Zr-95 daughter"},

    {"symbol": "Ba-140",  "half_life": "12.8 d",        "category": "Fission",
     "lines": [(537.3, 24.4), (162.7, 6.2)],
     "notes": "Short-lived fission product"},

    {"symbol": "La-140",  "half_life": "1.68 d",        "category": "Fission",
     "lines": [(1596.2, 95.4), (815.8, 23.4), (487.0, 45.6),
               (328.8, 20.3)],
     "notes": "Ba-140 daughter; multiple strong lines"},

    {"symbol": "Mo-99",   "half_life": "65.9 h",        "category": "Fission",
     "lines": [(739.5, 12.1), (778.0, 4.3), (181.1, 6.1)],
     "notes": "Precursor to Tc-99m; used medically and as fission marker"},

    {"symbol": "Tc-99m",  "half_life": "6.01 h",        "category": "Medical",
     "lines": [(140.5, 89.1)],
     "notes": "Most widely used medical radioisotope; 140 keV is highly diagnostic"},

    # ── Activation products ────────────────────────────────────────────────

    {"symbol": "Co-57",   "half_life": "271.8 d",       "category": "Activation",
     "lines": [(122.1, 85.6), (136.5, 10.7), (14.4, 9.2)],
     "notes": "Calibration / activation; 122 keV is key line"},

    {"symbol": "Co-58",   "half_life": "70.9 d",        "category": "Activation",
     "lines": [(810.8, 99.4), (511.0, 30.0)],
     "notes": "Activation product in reactor steel"},

    {"symbol": "Co-60",   "half_life": "5.27 y",        "category": "Activation",
     "lines": [(1173.2, 99.9), (1332.5, 100.0)],
     "notes": "Pair of lines at 1173+1332 keV is a unique fingerprint"},

    {"symbol": "Mn-54",   "half_life": "312.1 d",       "category": "Activation",
     "lines": [(834.8, 99.98)],
     "notes": "Calibration / activation product"},

    {"symbol": "Fe-59",   "half_life": "44.5 d",        "category": "Activation",
     "lines": [(1099.2, 56.5), (1291.6, 43.2)],
     "notes": "Activation product in steel"},

    {"symbol": "Zn-65",   "half_life": "243.9 d",       "category": "Activation",
     "lines": [(1115.5, 50.6), (511.0, 3.0)],
     "notes": "Calibration / activation"},

    {"symbol": "Na-22",   "half_life": "2.60 y",        "category": "Activation",
     "lines": [(1274.5, 99.9), (511.0, 180.8)],
     "notes": "Positron emitter; strong 511+1275 keV pair"},

    {"symbol": "Na-24",   "half_life": "14.96 h",       "category": "Activation",
     "lines": [(1368.6, 100.0), (2754.0, 99.9)],
     "notes": "High-energy pair; neutron activation of sodium"},

    {"symbol": "Cr-51",   "half_life": "27.7 d",        "category": "Activation",
     "lines": [(320.1, 9.9)],
     "notes": "Activation product; medical tracer"},

    {"symbol": "Sc-46",   "half_life": "83.8 d",        "category": "Activation",
     "lines": [(889.3, 99.98), (1120.5, 99.99)],
     "notes": "Activation product; geological tracer"},

    {"symbol": "Ir-192",  "half_life": "73.8 d",        "category": "Industrial",
     "lines": [(316.5, 82.8), (468.1, 47.8), (308.5, 29.7),
               (295.0, 28.7), (604.4, 8.2)],
     "notes": "Gamma radiography source; multiple lines 300–470 keV"},

    {"symbol": "Se-75",   "half_life": "119.8 d",       "category": "Industrial",
     "lines": [(264.7, 59.0), (279.5, 25.0), (136.0, 59.0),
               (121.1, 17.1), (400.7, 11.5)],
     "notes": "Gamma radiography source for thin materials"},

    {"symbol": "Yb-169",  "half_life": "32.0 d",        "category": "Industrial",
     "lines": [(177.2, 22.3), (130.5, 11.4), (197.9, 35.9),
               (307.7, 10.1)],
     "notes": "Gamma radiography; low-energy lines"},

    {"symbol": "Tm-170",  "half_life": "128.6 d",       "category": "Industrial",
     "lines": [(84.3, 2.4)],
     "notes": "Beta/gamma source for thin-section radiography"},

    # ── Medical ────────────────────────────────────────────────────────────

    {"symbol": "Ga-67",   "half_life": "3.26 d",        "category": "Medical",
     "lines": [(93.3, 38.8), (184.6, 21.2), (300.2, 16.8)],
     "notes": "Infection/tumour imaging"},

    {"symbol": "In-111",  "half_life": "2.80 d",        "category": "Medical",
     "lines": [(171.3, 90.6), (245.4, 94.0)],
     "notes": "Dual-line medical tracer; very diagnostic"},

    {"symbol": "Tl-201",  "half_life": "72.9 h",        "category": "Medical",
     "lines": [(135.3, 2.6), (167.4, 10.0), (68.9, 26.7)],
     "notes": "Cardiac perfusion imaging"},

    {"symbol": "I-123",   "half_life": "13.2 h",        "category": "Medical",
     "lines": [(159.0, 83.4)],
     "notes": "Thyroid imaging"},

    {"symbol": "I-125",   "half_life": "59.4 d",        "category": "Medical",
     "lines": [(35.5, 6.7)],
     "notes": "Brachytherapy seed; very low energy"},

    {"symbol": "F-18",    "half_life": "109.8 min",     "category": "Medical",
     "lines": [(511.0, 193.6)],
     "notes": "PET tracer; very strong 511 keV annihilation line"},

    {"symbol": "Ga-68",   "half_life": "67.7 min",      "category": "Medical",
     "lines": [(511.0, 177.6), (1077.3, 3.2)],
     "notes": "PET tracer"},

    {"symbol": "Lu-177",  "half_life": "6.65 d",        "category": "Medical",
     "lines": [(208.4, 10.4), (112.9, 6.2)],
     "notes": "Targeted radiotherapy; PRRT"},

    {"symbol": "Ra-223",  "half_life": "11.4 d",        "category": "Medical",
     "lines": [(269.5, 13.6), (154.2, 5.6)],
     "notes": "Bone metastases therapy (Xofigo)"},

    {"symbol": "Sm-153",  "half_life": "46.3 h",        "category": "Medical",
     "lines": [(103.2, 29.3)],
     "notes": "Bone pain palliation"},

    # ── Calibration / reference sources ───────────────────────────────────

    {"symbol": "Am-241",  "half_life": "432.2 y",       "category": "Calibration",
     "lines": [(59.5, 35.9), (26.3, 2.4)],
     "notes": "Calibration source; smoke detectors; 59.5 keV is primary line"},

    {"symbol": "Ba-133",  "half_life": "10.5 y",        "category": "Calibration",
     "lines": [(356.0, 62.1), (302.9, 18.3), (276.4, 7.2),
               (383.9, 8.9), (80.9, 34.1)],
     "notes": "Multi-line calibration source 80–384 keV"},

    {"symbol": "Eu-152",  "half_life": "13.5 y",        "category": "Calibration",
     "lines": [(121.8, 28.5), (344.3, 26.5), (1408.0, 20.8),
               (778.9, 12.9), (964.1, 14.6), (1112.1, 13.6),
               (244.7, 7.6), (411.1, 2.2), (1085.8, 10.2)],
     "notes": "Best multi-line calibration source; covers 122–1408 keV"},

    {"symbol": "Eu-154",  "half_life": "8.59 y",        "category": "Calibration",
     "lines": [(123.1, 40.5), (1274.4, 34.8), (1596.5, 17.9),
               (873.2, 12.1), (996.3, 10.5), (591.8, 4.9)],
     "notes": "Calibration source; reactor activation product"},

    {"symbol": "Eu-155",  "half_life": "4.75 y",        "category": "Calibration",
     "lines": [(86.5, 32.0), (105.3, 21.1)],
     "notes": "Low-energy calibration / fission product"},

    # ── Cosmogenic ─────────────────────────────────────────────────────────

    {"symbol": "Be-7",    "half_life": "53.2 d",        "category": "Cosmic",
     "lines": [(477.6, 10.5)],
     "notes": "Cosmogenic; deposited from atmosphere; seasonal variation"},

    {"symbol": "C-14",    "half_life": "5730 y",        "category": "Cosmic",
     "lines": [],    # pure beta
     "notes": "Pure beta — not detectable by gamma spec"},

    # ── Industrial / NORM / special ───────────────────────────────────────

    {"symbol": "Pu-239",  "half_life": "2.41×10⁴ y",   "category": "SNM",
     "lines": [(129.3, 6.3), (375.0, 1.6), (413.7, 1.5),
               (51.6, 2.7)],
     "notes": "Weapons-grade plutonium; weak lines — high-res detector needed"},

    {"symbol": "Pu-241",  "half_life": "14.4 y",        "category": "SNM",
     "lines": [(148.6, 1.9)],
     "notes": "SNM; decays to Am-241"},

    {"symbol": "Am-243",  "half_life": "7370 y",        "category": "SNM",
     "lines": [(74.7, 67.2), (43.5, 5.9)],
     "notes": "Minor actinide"},

    {"symbol": "Np-237",  "half_life": "2.14×10⁶ y",   "category": "SNM",
     "lines": [(29.4, 14.4), (86.5, 12.4), (311.9, 38.0)],
     "notes": "Neptunium; long-lived actinide"},

    {"symbol": "U-233",   "half_life": "1.59×10⁵ y",   "category": "SNM",
     "lines": [(317.2, 0.02), (291.4, 0.02)],
     "notes": "Very weak gamma emitter; difficult to detect"},

    {"symbol": "Cf-252",  "half_life": "2.65 y",        "category": "Industrial",
     "lines": [(100.0, 1.0)],   # spontaneous fission neutron source
     "notes": "Neutron source via spontaneous fission"},

    {"symbol": "Th-229",  "half_life": "7340 y",        "category": "NORM",
     "lines": [(193.6, 4.4), (86.5, 2.0)],
     "notes": "Used as tracer; daughter of U-233"},

    {"symbol": "Ra-228",  "half_life": "5.75 y",        "category": "NORM",
     "lines": [(13.5, 1.6)],
     "notes": "Th-232 series — very low energy"},

    {"symbol": "Hg-203",  "half_life": "46.6 d",        "category": "Industrial",
     "lines": [(279.2, 81.5)],
     "notes": "Industrial tracer"},

    {"symbol": "Sb-125",  "half_life": "2.76 y",        "category": "Fission",
     "lines": [(427.9, 29.6), (600.6, 17.8), (463.4, 10.4),
               (176.3, 6.8), (380.4, 1.5)],
     "notes": "Long-lived fission product"},

    {"symbol": "Sb-124",  "half_life": "60.2 d",        "category": "Activation",
     "lines": [(1691.0, 47.6), (602.7, 97.8), (1368.2, 2.6)],
     "notes": "Activation product"},

    {"symbol": "Ag-110m", "half_life": "249.8 d",       "category": "Activation",
     "lines": [(657.8, 94.7), (884.7, 72.7), (937.5, 34.4),
               (1384.3, 24.3), (706.7, 16.7)],
     "notes": "Reactor activation; multiple strong lines"},

    {"symbol": "Sn-113",  "half_life": "115.1 d",       "category": "Activation",
     "lines": [(391.7, 64.9), (255.1, 2.0)],
     "notes": "Activation product; also calibration"},

    {"symbol": "Cd-109",  "half_life": "461.4 d",       "category": "Industrial",
     "lines": [(88.0, 3.7)],
     "notes": "Low-energy calibration / XRF source"},

    {"symbol": "Se-109",  "half_life": "16.5 s",        "category": "Activation",
     "lines": [(636.2, 4.2)],
     "notes": "Short-lived"},

    {"symbol": "W-187",   "half_life": "23.7 h",        "category": "Activation",
     "lines": [(685.8, 33.2), (479.5, 21.8), (618.3, 6.3)],
     "notes": "Tungsten activation product"},

    {"symbol": "Xe-133",  "half_life": "5.24 d",        "category": "Fission",
     "lines": [(81.0, 37.0)],
     "notes": "Fission gas; CTBT monitoring"},

    {"symbol": "Xe-135",  "half_life": "9.14 h",        "category": "Fission",
     "lines": [(249.8, 90.0)],
     "notes": "Fission gas; reactor detector"},

    {"symbol": "Kr-85",   "half_life": "10.8 y",        "category": "Fission",
     "lines": [(514.0, 0.43)],
     "notes": "Fission gas; very weak gamma"},

    {"symbol": "H-3",     "half_life": "12.3 y",        "category": "Activation",
     "lines": [],    # pure beta
     "notes": "Tritium — pure beta, not detectable by gamma spec"},

    {"symbol": "P-32",    "half_life": "14.3 d",        "category": "Activation",
     "lines": [],    # pure beta
     "notes": "Pure beta emitter"},

    {"symbol": "S-35",    "half_life": "87.5 d",        "category": "Activation",
     "lines": [],    # pure beta
     "notes": "Pure beta emitter"},

    # ── Annihilation (511 keV) ─────────────────────────────────────────────
    {"symbol": "511-keV (β+)", "half_life": "—", "category": "Annihilation",
     "lines": [(511.0, 200.0)],
     "notes": "Positron annihilation line — indicates any positron emitter nearby"},
]


def match_rc_library(
    detected_keV: list[float],
    tolerance_keV: float = 10.0,
    min_intensity: float = 1.0,
) -> list[dict]:
    """
    Match a list of detected peak energies against the RC library.

    Returns list of dicts sorted by number of matched lines (descending):
        {symbol, half_life, category, notes, matched_lines, n_matched, n_total, score}
    """
    results = []
    for entry in RC_LIBRARY:
        lines = [(e, i) for e, i in entry["lines"] if i >= min_intensity]
        if not lines:
            continue
        matched = []
        for lib_keV, lib_int in lines:
            best = None
            best_d = tolerance_keV
            for det_keV in detected_keV:
                d = abs(det_keV - lib_keV)
                if d <= best_d:
                    best_d = d
                    best = det_keV
            if best is not None:
                matched.append({
                    "lib_keV":  lib_keV,
                    "det_keV":  best,
                    "delta":    round(best_d, 2),
                    "intensity": lib_int,
                })
        if matched:
            score = len(matched) / len(lines)
            results.append({
                "symbol":       entry["symbol"],
                "half_life":    entry["half_life"],
                "category":     entry["category"],
                "notes":        entry["notes"],
                "matched_lines": matched,
                "n_matched":    len(matched),
                "n_total":      len(lines),
                "score":        round(score, 3),
            })
    results.sort(key=lambda x: (x["n_matched"], x["score"]), reverse=True)
    return results


def get_entry(symbol: str) -> dict | None:
    """Return the full RC library entry for a given nuclide symbol."""
    for e in RC_LIBRARY:
        if e["symbol"].lower() == symbol.lower():
            return e
    return None


def by_category(category: str) -> list[dict]:
    """Return all entries in a given category."""
    return [e for e in RC_LIBRARY if e["category"].lower() == category.lower()]


def all_categories() -> list[str]:
    seen, out = set(), []
    for e in RC_LIBRARY:
        c = e["category"]
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


if __name__ == "__main__":
    print(f"RC library: {len(RC_LIBRARY)} entries")
    print(f"Categories: {all_categories()}")
    # Quick test
    test_peaks = [661.7, 1173.2, 1332.5, 609.3, 1460.8]
    matches = match_rc_library(test_peaks, tolerance_keV=5)
    print(f"\nTest match ({len(test_peaks)} peaks → {len(matches)} matches):")
    for m in matches[:5]:
        print(f"  {m['symbol']:12s}  {m['n_matched']}/{m['n_total']} lines  score={m['score']:.2f}  [{m['category']}]")
