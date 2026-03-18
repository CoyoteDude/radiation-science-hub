# Radioisotope Forensics Software

## Overview

This software is an independent research tool developed to address a specific gap in
portable gamma spectrometry: the inability to directly detect pure alpha emitters via
gamma spectroscopy. By analyzing detectable daughter nuclide signatures within a
spectrum and mapping them against known decay chains, the software infers the probable
identity of parent alpha emitters that would otherwise go undetected.

The project is written in Python and is currently operational at the prototype stage.
Active development is ongoing, with continued improvements to accuracy, spectral
interpretation, and isotope identification reliability.

---

## Capabilities

### Spectrum Analysis
Upload a gamma spectrum file for automated analysis. The software parses the spectral
data, identifies daughter nuclide signatures, and uses decay chain relationships to
infer probable parent isotopes — including alpha emitters with no direct gamma
signature.

### Isotope Database
An integrated database of over 2,000 isotopes can be queried independently of any
spectrum upload. Users can search by isotope name, decay mode, energy, or activity
level to retrieve nuclear data and decay chain information.

### Activity-Based Search
Search and filter isotopes by activity level to narrow identification candidates or
cross-reference measured source activities against known isotope profiles.

### Parent Isotope Inference
The core output of the software is a ranked list of probable parent alpha emitters,
each assigned a percent probability score derived from decay chain analysis of the
detected daughter nuclides.

---

## Current Limitations

This software is a working research prototype. Users should be aware of the following:

!!! warning "Development Status"
    - Spectral interpretation is still being refined and may produce incomplete or
      inconsistent results depending on spectrum quality
    - Probability scores should be treated as investigative leads, not definitive
      identifications
    - Accuracy improves with clean, high-resolution input spectra and well-characterized
      sources
    - The software is not validated for regulatory, forensic, or clinical use

These limitations are expected at this stage of development and are actively being
addressed.

---

## Intended Applications

- **Research validation** — confirming source composition in experimental settings
  where alpha emitters are present but not directly measurable
- **Source provenance** — inferring the likely origin or history of a radioactive
  sample based on its decay chain fingerprint
- **Nuclear forensics** — supporting investigative analysis of unknown or
  uncharacterized radioactive materials
- **Educational use** — exploring decay chain relationships and isotope identification
  interactively

---

## Development Roadmap

- [ ] Improved spectral parsing and peak identification
- [ ] Expanded decay chain database coverage
- [ ] Bayesian inference layer for improved probability scoring
- [ ] Validation against characterized reference sources
- [ ] Open source release via GitHub *(planned)*
- [ ] Command-line interface and documentation

---

!!! note "Availability"
    The software is not yet publicly released. An open source release on GitHub is
    planned following further validation and documentation. If you are a researcher
    interested in early access or collaboration, please reach out at awalsh35@asu.edu.
