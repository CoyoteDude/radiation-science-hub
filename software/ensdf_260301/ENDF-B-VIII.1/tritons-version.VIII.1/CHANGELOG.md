ENDF/B-VIII.1 Release Change Log
=====================================

Maintainer: G.P.A. Nobre

Affiliation: NNDC, Brookhaven National Laboratory



ENDF/B-VIII.1 final release (30 August, 2024)
---------------------------------------------

There are no changes in data content for the tritons sublibrary since ENDF/B-VIII.1-Beta4. 
However, all files had their metadata in the file headers updated to match the correct information for the final ENDF/B-VIII.1 release.






ENDF/B-VIII.1-Beta4 release (28 June, 2024)
---------------------------------------------

There were no updates for the tritons sublibrary in ENDF/B-VIII.1-Beta4 when compared to ENDF/B-VIII.1-Beta3.







ENDF/B-VIII.1-Beta3 release (11 January, 2024)
---------------------------------------------

This release consists of evaluation updates from LANL for 4He and fixes to 3He.
The list of files changed can be seen below:

* t-002_He_003.endf
* t-002_He_004.endf









ENDF/B-VIII.1-Beta2 release (4 August, 2023)
---------------------------------------------

The only changes relative to ENDF/B-VIII.0 for the tritons sublibrary are:

* t-002_He_004.endf (minor fix)

* t-003_Li_006 (Fix: "Move MT=22 (3-body outputChannel) to MT=50 (2-body + breakup), and remove intermediate Be8 from MF=6 product list.")



ENDF/B-VIII.1-Beta1.1 (18 April, 2023)
--------------------------------------

No changes, not part of the release.

ENDF/B-VIII.1-Beta1 (1 March 2023)
----------------------------------

Not part of the release, as there were no updates from VIII.0.







--------------------
ENDF/B-VIII.0 Change Log
========================

Maintainer: D.A. Brown, NNDC, BNL

Affiliation: NNDC, Brookhaven National Laboratory

ENDF/B-VIII.0 Final (2 Feb 2018)
--------------------------------

* Update ENDF header and distribution date in all files


ENDF/B-VIII.0beta7 (16 Jan 2018)
--------------------------------

* t-002_He_004.endf Eliminate extra spaces after last column so as not to foul the
  punchcard reader.


ENDF/B-VIII.0beta6 (15 Dec 2017)
--------------------------------

* t-002_He_004.endf Corrected scaling of Coulomb-nuclear interference in MF=3.
  There is no 2.pi factor in eq. (6.20), unlike eq. (4.3) of manual


ENDF/B-VIII.0beta5 (29 Sep 2017)
--------------------------------

* Add explicit recoil products (MF6 LAW4) for some 2-body reactions in charged particles.
  Otherwise masses for the recoil product are not present anywhere in the file.
  Masses came from AME2003.  File affected: t-003_Li_007.endf


ENDF/B-VIII.0beta4.1 (2 Sep 2017)
--------------------------------

* Correct NLIB, NMOD in headers

* Clean up documentation, removing ENDL-specific wording

* t-001_H_003.endf: fix energy range in outgoing distribution

* t-003_Li_007.endf: add Coulomb elastic cross section


ENDF/B-VIII.0beta4 (28 Feb 2017)
--------------------------------

* No Changes since beta3


ENDF/B-VIII.0beta3 (1 Nov 2016)
--------------------------------

* t-002_He_004.endf New (for ENDF) t + He4 evaluation from ECPL (R.M.White, D.A.Resler,
  S.I.Warshaw) at LLNL

* t-003_Li_007.endf New t+7Li evaluation from LLNL in 2016 by Thompson, Navratil, Brown


ENDF/B-VIII.0beta2 (19 Aug 2016)
--------------------------------

* No changes since beta1


ENDF/B-VIII.0beta1 (25 Apr 2016)
--------------------------------

* No changes since beta0


ENDF/B-VIII.0beta0 (8 Apr 2016)
-------------------------------

* No changes since ENDF/B-VII.1
