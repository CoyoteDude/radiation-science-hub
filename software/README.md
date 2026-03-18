# Gamma Spectroscopy Lab — v2
### RC-103 · ENSDF · IAEA · Forensic · Peak Fitting · Activity · Dose

---

## Setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## New in v2

| Module | File | What it does |
|--------|------|-------------|
| ENSDF Parser | `ensdf_parser.py` | Loads full ~3000-isotope gamma database from ENSDF bulk files |
| Peak Fitting | `peak_fitting.py` | Gaussian + linear BG fit → precise centroid, FWHM, net area |
| Efficiency Cal | `efficiency_cal.py` | Build ε(E) curve from calibration sources; NIST data built-in |
| Activity | `activity_calculator.py` | N_net / (ε × I_γ × t) → Bq, Bq/g, Bq/kg |
| MDA | `physics_tools.py` | Currie 1968 / ISO 11929 minimum detectable activity |
| Shielding | `physics_tools.py` | NIST XCOM μ/ρ attenuation + Berger buildup factor, 10 materials |
| Dose Rate | `physics_tools.py` | H*(10) µSv/h from ICRP 74 flux-to-dose coefficients |

---

## Load the full ENSDF database (one-time)

1. Go to https://www.nndc.bnl.gov/ensdf/ensdf/dl_ensdf.jsp
2. Download **ENSDF database (ASCII)** zip (~40 MB)
3. Unzip → place all `*.ens` files in `~/Documents/GammaLab/ensdf/`
4. Click **Rebuild cache** in the 🗃 ENSDF Library tab

---

## Recommended workflow

```
📥 Import XML → 🔍 Identify isotopes
    → 🎯 Peak Fitting (fit Gaussians)
    → 📐 Efficiency Cal (build/load ε curve)
    → ⚡ Activity (get Bq/g)
    → 📡 MDA (detection limits)
    → ☢  Dose Rate (µSv/h at distance)
    → 🛡 Shielding (find required shield thickness)
```
