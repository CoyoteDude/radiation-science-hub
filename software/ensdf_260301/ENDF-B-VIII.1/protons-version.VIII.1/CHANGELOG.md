ENDF/B-VIII.1 Release Change Log
=====================================

Maintainer: G.P.A. Nobre

Affiliation: NNDC, Brookhaven National Laboratory



ENDF/B-VIII.1 final release (30 August, 2024)
---------------------------------------------

There are no changes in data content for the protons sublibrary since ENDF/B-VIII.1-Beta4. 
However, all files had their metadata in the file headers updated to match the correct information for the final ENDF/B-VIII.1 release.





ENDF/B-VIII.1-Beta4 release (28 June, 2024)
---------------------------------------------

There were no updates for the protons sublibrary in ENDF/B-VIII.1-Beta4 when compared to ENDF/B-VIII.1-Beta3.




ENDF/B-VIII.1-Beta3 release (11 January, 2024)
---------------------------------------------

This release basically consists of evaluation updates from LANL to 4He and fixes to 13C.
The list of files changed can be seen below:

* p-002_He_004.endf
* p-006_C_013.endf



ENDF/B-VIII.1-Beta2 release (4 August, 2023)
---------------------------------------------

Only one file in the protons sublibrary has been updated since ENDF/B-VIII.0, only to correct a minor issues. The list of changed files is:

* p-002_He_004.endf



ENDF/B-VIII.1-Beta1.1 (18 April, 2023)
--------------------------------------

No changes, not part of the release.

ENDF/B-VIII.1-Beta1 (1 March 2023)
----------------------------------

Not part of the release, as there were no updates from VIII.0.






----------
ENDF/B-VIII.0 Change Log
========================

Maintainer: D.A. Brown, NNDC, BNL

Affiliation: NNDC, Brookhaven National Laboratory

ENDF/B-VIII.0 Final (2 Feb 2018)
--------------------------------

* Update ENDF header and distribution date in all files


ENDF/B-VIII.0beta6 (15 Dec 2017)
--------------------------------

* p-002_He_004.endf Corrected scaling of Coulomb-nuclear interference in MF=3.
  There is no 2.pi factor in eq. (6.20), unlike eq. (4.3) of manual


ENDF/B-VIII.0beta5 (29 Sep 2017)
--------------------------------

* Add explicit recoil products (MF6 LAW4) for some 2-body reactions in charged particles.
  Otherwise masses for the recoil product are not present anywhere in the file.
  Masses came from AME2003.  Files affected: p-003_Li_007.endf, p-004_Be_009.endf


ENDF/B-VIII.0beta4.1 (2 Sep 2017)
--------------------------------

* p-003_Li_007.endf: Fixed starting cross section for MT=51

* p-006_C_013.endf: several changes, including
    ** Fix proton mass to 9.98623-1 from 9.98620-1
    ** Fix MAT number
    ** Add Rutherford elastic scattering
    ** extend upper energy range of capture by extrapolating last point so now there
       isn't a gap this is a kludgy solution that gets the file through NJOY

* Fixed NLIB, NMOD & removed line numbers on many files


ENDF/B-VIII.0beta4 (28 Feb 2017)
--------------------------------

* No Changes since beta3


ENDF/B-VIII.0beta3.1 (18 Jan 2017)
----------------------------------

* No Changes since beta3


ENDF/B-VIII.0beta3 (1 Nov 2016)
-------------------------------

* p-003_Li_007.endf: Evaluation for p + 7Li from ECPL in ENDL2009, by Brown and Navratil;
  also fixed outgoing masses for Z=1,2 nuclei (removing electrons) and tweaked starting
  energies to above thresholds

* p-002_He_004.endf: Elastic scattering for p+4He ECPL at LLNL by R.M.White, D.A.Resler,
  S.I.Warshaw; also fixed outgoing masses for Z=1,2 nuclei (removing electrons)

* p-006_C_013.endf: The N14 mass in C13 (p,gamma) was off by an order of magnitude.


ENDF/B-VIII.0beta2 (19 Aug 2016)
--------------------------------

* No changes since beta1


ENDF/B-VIII.0beta1 (25 Apr 2016)
--------------------------------

* No changes since beta0


ENDF/B-VIII.0beta0 (8 Apr 2016)
-------------------------------

* Fix formatting error in p-014_Si_028.endf outgoing distributions
