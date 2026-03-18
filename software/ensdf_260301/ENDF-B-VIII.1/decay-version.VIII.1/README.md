ENDF/B-VIII.1 Decay Sublibrary README
==============================================================================

Maintainer: G.P.A. Nobre, NNDC, BNL

Affiliation: NNDC, Brookhaven National Laboratory

Date: 30 August, 2024


This is the final ENDF/B-VIII.1 release for the *decay sublibrary*. The full list of changes across multiple ENDF/B-VIII.1-Beta releases, since ENDF/B-VIII.0, are listed in detail in the file CHANGELOG.md. A summarized list is also shown below.

The ENDF-6 files in this ENDF/B-VIII.1 release were successfully processed using NJOY-16.76 and FUDGE-6.7 for all sublibraries, and AMPX (SCALE-7.0b08) for neutrons and photo-atomic sublibraries.  Note: AMPX processing for the thermal neutron scattering sublibrary used features to be made available in a future SCALE-7.0 beta.

Complete and detailed information on the ENDF/B-VIII.1 release can be found in the accompanying article that will be submitted for publication in the Nuclear Data Sheets journal shortly after the ENDF/B-VIII.1 release.





History of ENDF/B-VIII.1-Beta releases for the *decay sublibrary*:
----

* VIII.1 final release (30 August, 2024): No changes, apart from updates to the metadata in file headers, which impacted all files.

* VIII.1-Beta4 (28 June, 2024): No updates.

* VIII.1-Beta3 (11 January, 2024): Same as ENDF/B-VIII.0.

* VIII.1-Beta2 (4 August, 2023): No changes, not part of the release.

* VIII.1-Beta1.1 (18 April, 2023): No changes, not part of the release.

* VIII.1-Beta1 (1 March 2023): Not part of the release, as there were no updates from VIII.0.








ENDF/B-VIII.0 Decay Sublibrary README
=======================================

Maintainer: D.A. Brown, NNDC, BNL

Affiliation: NNDC, Brookhaven National Laboratory

Date: 2 Feb 2018

In the ENDF/B-VIII.0 release, the decay data sublibrary underwent a number of
checks and updates, mainly on the beta intensities following beta-minus decay,
X-ray energies for actinide nuclides, and some error fixes.
As in the previous library release, beta intensities from Total Absorption Gamma
Spectroscopy (TAGS) experiments were incorporated in order to improve the
electron and antineutrino spectra predictions following fission.  Additionally,
for another set of neutron-rich nuclides lacking TAGS data and yet deemed
important in antineutrino spectra applications, beta intensities obtained from
adjusting the electron spectra measured have been used.

Another update had to do with X-ray energies, which are produced following decay
under two circumstances, electron capture or electron conversion.  These
processes create vacancies in the atomic orbitals, and as these vacancies are
filled, X-rays and Auger electrons are emitted.  For ENDF/B-VII.1, LLNL’s EADL
data, also part of the ENDF/B library, were used to calculate the energy and
intensity of the transitions.  The energies are calculated by a simple
difference of the atomic shell binding energies listed in EADL.  However, it
was noticed that the K_alpha1 X-ray energy for Uranium was shifted by +0.4 keV.
An interim solution was implemented for ENDF/B-VIII.0, where K X-ray energies
from the NIST X-ray Transition Energy Database were used, for decay datasets
with Z=89-96.

Finally, the datasets for the following nuclides were corrected: 86As, 98mY,
149mEr, 209Rn, 220Fr, 177Ir, 203Po, 224Ac, 231U, 236mNp, 239Am, and 253Es.

The decay sublibrary is detailed in

* D. Brown, et al. "ENDF/B-VIII.0: The 8th Major Release of the Nuclear
  Reaction Data Library with CIELO-project Cross Sections, New Standards
  and Thermal Scattering Data," Nuclear Data Sheets 148, 1 (2018).
