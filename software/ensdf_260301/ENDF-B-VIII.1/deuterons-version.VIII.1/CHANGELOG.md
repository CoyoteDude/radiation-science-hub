ENDF/B-VIII.1 Release Change Log
=====================================

Maintainer: G.P.A. Nobre

Affiliation: NNDC, Brookhaven National Laboratory



ENDF/B-VIII.1 final release (30 August, 2024)
---------------------------------------------

The only changes in data content for the deuterons sublibrary since ENDF/B-VIII.1-Beta4 are to d-001_H_003.endf and d-002_He_003.endf. The change to d+t was to add LAW=6 distributions back and push the first point for the MT=51 neutron distribution & multiplicity up to match cross section domain. The change to d+3He was just a very minor fix involving running "dos2linux" and removing line numbers. The complete list of files with data content changes since ENDF/B-VIII.1-Beta4 can be seen below.
Additionally, **ALL** files had their metadata in the file headers updated to match the correct information for the final ENDF/B-VIII.1 release.

List of files with data content changes since ENDF/B-VIII.1-Beta4:

* d-001_H_003.endf (Added back LAW=6 distribution)
* d-002_He_003.endf (minor fix)






ENDF/B-VIII.1-Beta4 release (28 June, 2024)
---------------------------------------------

There were no updates to the deuterons sublibrary in ENDF/B-VIII.1-Beta4 when compared to ENDF/B-VIII.1-Beta3.



ENDF/B-VIII.1-Beta3 release (11 January, 2024)
---------------------------------------------

This release consists of evaluation updates from LANL to 3H, 3He and 6Li, and fixes for 4He and 7Li. The list of files changed can be seen below:

* d-001_H_003.endf
* d-002_He_003.endf
* d-002_He_004.endf
* d-003_Li_006.endf
* d-003_Li_007.endf






ENDF/B-VIII.1-Beta2 release (4 August, 2023)
---------------------------------------------

No changes, not part of the release.


ENDF/B-VIII.1-Beta1.1 (18 April, 2023)
--------------------------------------

No changes, not part of the release.

ENDF/B-VIII.1-Beta1 (1 March 2023)
----------------------------------

Not part of the release, as there were no updates from VIII.0.






ENDF/B-VIII.0 Change Log
========================

Maintainer: D.A. Brown, NNDC, BNL

Affiliation: NNDC, Brookhaven National Laboratory

ENDF/B-VIII.0 Final (2 Feb 2018)
--------------------------------

* Update ENDF header and distribution date in all files


ENDF/B-VIII.0beta6 (15 Dec 2017)
--------------------------------

* d-003_Li_007.endf Corrected scaling of Coulomb-nuclear interference in MF=3.
  There is no 2.pi factor in eq. (6.20), unlike eq. (4.3) of manual


ENDF/B-VIII.0beta5 (29 Sep 2017)
--------------------------------

* Add explicit recoil products (MF6 LAW4) for some 2-body reactions in charged particles.
  Otherwise masses for the recoil product are not present anywhere in the file.
  Masses came from AME2003.  File affected: d-003_Li_007.endf


ENDF/B-VIII.0beta4.1 (2 Sep 2017)
--------------------------------

* Correct NLIB in header and clean up documentation


ENDF/B-VIII.0beta4 (28 Feb 2017)
--------------------------------

* No Changes since beta3.1


ENDF/B-VIII.0beta3.1 (18 Jan 2017)
----------------------------------

* The deuteron target was incorrectly marked as unstable.


ENDF/B-VIII.0beta3 (1 Nov 2016)
--------------------------------

* New evaluation for d+7Li from Navratil and Brown, 2010, from ECPL at LLNL
  (d-003_Li_007.endf)

* d-003_Li_007.endf Tweaking starting energies to above thresholds and fixing outgoing
  masses for Z=1,2 nuclei (removing electrons) for d+7Li


ENDF/B-VIII.0beta2 (19 Aug 2016)
--------------------------------

* No changes since beta1


ENDF/B-VIII.0beta1 (25 Apr 2016)
--------------------------------

* No changes since beta0


ENDF/B-VIII.0beta0 (8 Apr 2016)
-------------------------------

* For d-001_H_003.endf, the ENDF file documentation indicates that MT=51 is d(t,n)4He*
  and that the 4He* subsequently breaks up into p+t.  In MF=6, the outgoing n, p and t
  are given.  However, in MF=3, the breakup flag (LR) is not set, indicating that
  this reaction is simply d(t,n)4He* and the 4He* deexcites via photon emission.  To fix
  this, I set the breakup flag to LR=1, indicating that the identities and distributions
  of all outgoing particles are specified in the MF=6 file.
