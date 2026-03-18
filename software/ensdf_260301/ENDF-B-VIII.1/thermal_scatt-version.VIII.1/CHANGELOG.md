ENDF/B-VIII.1 Release Change Log
=====================================

Maintainer: G.P.A. Nobre

Affiliation: NNDC, Brookhaven National Laboratory



ENDF/B-VIII.1 final release (30 August, 2024)
---------------------------------------------

The were changes in data content for 81 files in the thermal neutron scattering law (TSL) sublibrary since ENDF/B-VIII.1-Beta4. They were due to simply running dos2unix and removing line numbers or very minor fix (H in UH3). There was also a minor update in the comment lines of the TSL_MAT_numbers.csv CSV file to improve the readability with some CSV editors. The complete list of files with data content changes since ENDF/B-VIII.1-Beta4 can be seen below.
Additionally, **ALL** files had their metadata in the file headers updated to match the correct information for the final ENDF/B-VIII.1 release.

List of files with data content changes since ENDF/B-VIII.1-Beta4:

* TSL_MAT_numbers.csv
* tsl-AlinAl2O3.endf
* tsl-Be-metal+Sd.endf
* tsl-Be-metal.endf
* tsl-BeinBeF2.endf
* tsl-BeinBeO.endf
* tsl-CainCaH2.endf
* tsl-CinC5O2H8.endf
* tsl-CinC8H8.endf
* tsl-CinCF2.endf
* tsl-CinSiC.endf
* tsl-CinUC-100P.endf
* tsl-CinUC-10P.endf
* tsl-CinUC-5P.endf
* tsl-CinUC-HALEU.endf
* tsl-CinUC-HEU.endf
* tsl-CinUC.endf
* tsl-FinBeF2.endf
* tsl-FinCF2.endf
* tsl-FinHF.endf
* tsl-FinMgF2.endf
* tsl-H1inCaH2.endf
* tsl-H2inCaH2.endf
* tsl-HinC5O2H8.endf
* tsl-HinC8H8.endf
* tsl-HinHF.endf
* tsl-HinParaffinicOil.endf
* tsl-HinUH3.endf
* tsl-HinYH2.endf
* tsl-MginMgF2.endf
* tsl-MginMgO.endf
* tsl-NinUN-100P.endf
* tsl-NinUN-10P.endf
* tsl-NinUN-5P.endf
* tsl-NinUN-HALEU.endf
* tsl-NinUN-HEU.endf
* tsl-NinUN.endf
* tsl-OinAl2O3.endf
* tsl-OinBeO.endf
* tsl-OinC5O2H8.endf
* tsl-OinMgO.endf
* tsl-OinPuO2.endf
* tsl-OinSiO2-alpha.endf
* tsl-OinUO2-100P.endf
* tsl-OinUO2-10P.endf
* tsl-OinUO2-5P.endf
* tsl-OinUO2-HALEU.endf
* tsl-OinUO2-HEU.endf
* tsl-OinUO2.endf
* tsl-PuinPuO2.endf
* tsl-SiinSiC.endf
* tsl-SiinSiO2-alpha.endf
* tsl-U-metal-100P.endf
* tsl-U-metal-10P.endf
* tsl-U-metal-5P.endf
* tsl-U-metal-HALEU.endf
* tsl-U-metal-HEU.endf
* tsl-U-metal.endf
* tsl-UinUC-100P.endf
* tsl-UinUC-10P.endf
* tsl-UinUC-5P.endf
* tsl-UinUC-HALEU.endf
* tsl-UinUC-HEU.endf
* tsl-UinUC.endf
* tsl-UinUN-100P.endf
* tsl-UinUN-10P.endf
* tsl-UinUN-5P.endf
* tsl-UinUN-HALEU.endf
* tsl-UinUN-HEU.endf
* tsl-UinUN.endf
* tsl-UinUO2-100P.endf
* tsl-UinUO2-10P.endf
* tsl-UinUO2-5P.endf
* tsl-UinUO2-HALEU.endf
* tsl-UinUO2-HEU.endf
* tsl-UinUO2.endf
* tsl-YinYH2.endf
* tsl-ortho-D.endf
* tsl-ortho-H.endf
* tsl-para-D.endf
* tsl-para-H.endf
* tsl-reactor-graphite-20P.endf








ENDF/B-VIII.1-Beta4 release (28 June, 2024)
---------------------------------------------

Relative to the previous release (VIII.1-Beta3), there are 21 ENDF-6 files changed, either updated or added, in addition to associated files (LEAPR, README, FLASSH, etc.). The CSV file with unique identification of MAT numbers ('TSL_MAT_numbers.csv') was also updated to include assginments for new materials. Highlights in this release are updated evaluations for YH2 and special purpose evaluations for BeF2, MgF2, and MgO for filter applications. There were also many fixes done of different degrees of complexity.

The full list of changed files is below:


* tsl-7Liin7LiD-mixed.endf
* tsl-7Liin7LiH-mixed.endf
* tsl-BeinBe2C.endf
* tsl-BeinBeF2.endf
* tsl-CinBe2C.endf
* tsl-CinZrC.endf
* tsl-Din7LiD-mixed.endf
* tsl-FinBeF2.endf
* tsl-FinMgF2.endf
* tsl-Hin7LiH-mixed.endf
* tsl-HinUH3.endf
* tsl-HinYH2.endf
* tsl-HinZrH2.endf
* tsl-HinZrHx.endf
* tsl-MginMgF2.endf
* tsl-MginMgO.endf
* tsl-OinMgO.endf
* tsl-YinYH2.endf
* tsl-ZrinZrC.endf
* tsl-ZrinZrH2.endf
* tsl-ZrinZrHx.endf





ENDF/B-VIII.1-Beta3 release (11 January, 2024)
---------------------------------------------

There are 99 ENDF-6 files changed, either updated or added, in addition to associated files (LEAPR, README, FLASSH, etc.) and the CSV file with unique identification of MAT numbers. Highlights are new unique MAT numbers,  implementation of the approved format proposal that expanded metadata describing the stoichiometry and isotopic content,  new enirchment files for fuel materials, new complete lucite evaluation, low-energy extrapolation for light water, criogenic para- and ortho-deuterium and hydrogen, new plutonium dioxide and zyrconium carbide evaluations, and other fixes of different degrees of complexity. 

The full list of changed files is below:

* tsl-7Liin7LiD-mixed.endf
* tsl-7Liin7LiH-mixed.endf
* tsl-AlinAl2O3.endf
* tsl-Be-metal+Sd.endf
* tsl-Be-metal.endf
* tsl-BeinBe2C.endf
* tsl-BeinBeO.endf
* tsl-BeinFLiBe.endf
* tsl-CainCaH2.endf
* tsl-CinBe2C.endf
* tsl-CinC5O2H8.endf
* tsl-CinC8H8.endf
* tsl-CinCF2.endf
* tsl-CinSiC.endf
* tsl-CinUC-100P.endf
* tsl-CinUC-10P.endf
* tsl-CinUC-5P.endf
* tsl-CinUC-HALEU.endf
* tsl-CinUC-HEU.endf
* tsl-CinUC.endf
* tsl-CinZrC.endf
* tsl-Din7LiD-mixed.endf
* tsl-DinD2O.endf
* tsl-FinCF2.endf
* tsl-FinFLiBe.endf
* tsl-FinHF.endf
* tsl-H1inCaH2.endf
* tsl-H2inCaH2.endf
* tsl-Hin7LiH-mixed.endf
* tsl-HinC5O2H8.endf
* tsl-HinC8H8.endf
* tsl-HinH2O.endf
* tsl-HinHF.endf
* tsl-HinIceIh.endf
* tsl-HinParaffinicOil.endf
* tsl-HinUH3.endf
* tsl-HinYH2.endf
* tsl-HinZrH2.endf
* tsl-HinZrHx.endf
* tsl-LiinFLiBe.endf
* tsl-NinUN-100P.endf
* tsl-NinUN-10P.endf
* tsl-NinUN-5P.endf
* tsl-NinUN-HALEU.endf
* tsl-NinUN-HEU.endf
* tsl-NinUN.endf
* tsl-OinAl2O3.endf
* tsl-OinBeO.endf
* tsl-OinC5O2H8.endf
* tsl-OinD2O.endf
* tsl-OinIceIh.endf
* tsl-OinPuO2.endf
* tsl-OinSiO2-alpha.endf
* tsl-OinUO2-100P.endf
* tsl-OinUO2-10P.endf
* tsl-OinUO2-5P.endf
* tsl-OinUO2-HALEU.endf
* tsl-OinUO2-HEU.endf
* tsl-OinUO2.endf
* tsl-PuinPuO2.endf
* tsl-SiinSiC.endf
* tsl-SiinSiO2-alpha.endf
* tsl-U-metal-100P.endf
* tsl-U-metal-10P.endf
* tsl-U-metal-5P.endf
* tsl-U-metal-HALEU.endf
* tsl-U-metal-HEU.endf
* tsl-U-metal.endf
* tsl-UinUC-100P.endf
* tsl-UinUC-10P.endf
* tsl-UinUC-5P.endf
* tsl-UinUC-HALEU.endf
* tsl-UinUC-HEU.endf
* tsl-UinUC.endf
* tsl-UinUN-100P.endf
* tsl-UinUN-10P.endf
* tsl-UinUN-5P.endf
* tsl-UinUN-HALEU.endf
* tsl-UinUN-HEU.endf
* tsl-UinUN.endf
* tsl-UinUO2-100P.endf
* tsl-UinUO2-10P.endf
* tsl-UinUO2-5P.endf
* tsl-UinUO2-HALEU.endf
* tsl-UinUO2-HEU.endf
* tsl-UinUO2.endf
* tsl-YinYH2.endf
* tsl-ZrinZrC.endf
* tsl-ZrinZrH2.endf
* tsl-ZrinZrHx.endf
* tsl-graphiteSd.endf
* tsl-ortho-D.endf
* tsl-ortho-H.endf
* tsl-para-D.endf
* tsl-para-H.endf
* tsl-reactor-graphite-10P.endf
* tsl-reactor-graphite-20P.endf
* tsl-reactor-graphite-30P.endf
* tsl-s-CH4.endf




ENDF/B-VIII.1-Beta2 release (4 August, 2023)
---------------------------------------------

The list of updated files for the Thermal Neutron Scattering Law sublibrary relative to the previous Beta release (ENDF/B-VIII.1-Beta1.1) is below. Please note that many evaluations have additional accompanying associated files (LEAPR, README, etc.) not listed here, but present in the release package. 

* tsl-AlinAl2O3.endf
* tsl-BeinFLiBe.endf
* tsl-CinC8H8.endf
* tsl-FinFLiBe.endf
* tsl-FinHF.endf
* tsl-HinC8H8.endf
* tsl-HinHF.endf
* tsl-HinParaffinicOil.endf
* tsl-LiinFLiBe.endf
* tsl-OinAl2O3.endf




ENDF/B-VIII.1-Beta1.1 release (18 April, 2023)
---------------------------------------------

This is the first beta release for the Thermal Neutron Scattering Law sublibrary. This release contains updates and new files developed mainly at NCSU, NNL, and ORNL. 

    The list of files changed from ENDF/B-VIII.0 is as follows:

    * tsl-7Liin7LiD-mixed.endf
    * tsl-7Liin7LiH-mixed.endf
    * tsl-AlinAl2O3.endf
    * tsl-Be-metal+Sd.endf
    * tsl-Be-metal.endf
    * tsl-BeinBe2C.endf
    * tsl-BeinBeO.endf
    * tsl-BeinFLiBe.endf
    * tsl-CainCaH2.endf
    * tsl-CinBe2C.endf
    * tsl-CinC5O2H8.endf
    * tsl-CinCF2.endf
    * tsl-CinSiC.endf
    * tsl-CinUC-10P.endf
    * tsl-CinUC-5P.endf
    * tsl-CinUC-HEU.endf
    * tsl-CinUC.endf
    * tsl-Din7LiD-mixed.endf
    * tsl-FinCF2.endf
    * tsl-FinFLiBe.endf
    * tsl-FinHF.endf
    * tsl-H1inCaH2.endf
    * tsl-H2inCaH2.endf
    * tsl-Hin7LiH-mixed.endf
    * tsl-HinHF.endf
    * tsl-HinParaffinicOil.endf
    * tsl-HinUH3.endf
    * tsl-HinZrH2.endf
    * tsl-HinZrHx.endf
    * tsl-LiinFLiBe.endf
    * tsl-NinUN-10P.endf
    * tsl-NinUN-5P.endf
    * tsl-NinUN-HEU.endf
    * tsl-NinUN.endf
    * tsl-OinAl2O3.endf
    * tsl-OinBeO.endf
    * tsl-OinC5O2H8.endf
    * tsl-OinSiO2-alpha.endf
    * tsl-OinUO2-10P.endf
    * tsl-OinUO2-5P.endf
    * tsl-OinUO2-HEU.endf
    * tsl-OinUO2.endf
    * tsl-SiinSiC.endf
    * tsl-SiinSiO2-alpha.endf
    * tsl-U-metal-10P.endf
    * tsl-U-metal-5P.endf
    * tsl-U-metal-HEU.endf
    * tsl-U-metal.endf
    * tsl-UinUC-10P.endf
    * tsl-UinUC-5P.endf
    * tsl-UinUC-HEU.endf
    * tsl-UinUC.endf
    * tsl-UinUN-10P.endf
    * tsl-UinUN-5P.endf
    * tsl-UinUN-HEU.endf
    * tsl-UinUN.endf
    * tsl-UinUO2-10P.endf
    * tsl-UinUO2-5P.endf
    * tsl-UinUO2-HEU.endf
    * tsl-UinUO2.endf
    * tsl-ZrinZrH2.endf
    * tsl-ZrinZrHx.endf
    * tsl-graphiteSd.endf
    * tsl-reactor-graphite-20P.endf












---------------------
ENDF/B-VIII.0 Change Log
========================

Maintainer: D.A. Brown, NNDC, BNL

Affiliation: NNDC, Brookhaven National Laboratory

ENDF/B-VIII.0 Final (2 Feb 2018)
--------------------------------

* Added smin value to H2O and D2O LEAPR inputs

* Update ENDF header and distribution date in all files


ENDF/B-VIII.0beta7 (16 Jan 2018)
--------------------------------

* Reorganize graphite evaluations.  Elaborating on the changes in beta6, "cubic graphite"
  is a model for coherent elastic cross sections (as implemented in NJOY) with graphite
  structural factors calculated using the hexagonal lattice geometry data and with a
  scalar Debye-Waller factor for temperature and lattice vibration correction.  Given this

  Previously, in beta6, we have 2 graphites:
    tsl-reactor-graphite  MAT=32, 30% porosity
    tsl-graphite          MAT=31, 0% porosity

  Now we have:
    tsl-reactor-graphite-30P   MAT=32, 30% porosity
    tsl-reactor-graphite-10P   MAT=31, 10% porosity
    tsl-crystalline-graphite   MAT=30, 0% porosity

  Note: the 10% porosity graphite is "new"


ENDF/B-VIII.0beta6 (15 Dec 2017)
--------------------------------
* Make "Trial B" version of light water (HinH2O) the official light water of beta6.
  This is suspected to be the good one, so let's just jump the gun, shall we?

* Replace the hexagonal version of graphite and reactor-graphite with the cubic
  approximation version.  The cubic versions perform nearly as good as ENDF/B-VII.1
  (in some cases better) and the provided LEAPR files can be processed.  Note: in this
  release, reactor-graphite corresponds to the 30% porosity version, arguably the upper
  bound for porosity seen in practice.  The 10% porosity version, which performs best of
  the three in many tests, is NOT included in this release.


ENDF/B-VIII.0beta5 (29 Sep 2017)
--------------------------------
* SiC, BeO, lucite (C5O2H8): The coherent elastic xsec and the alpha, beta grid for
  S(a,b) are updated.

* UN: The incoherent bound xsec for N in UN used to calculate the incoherent elastic xsec
  is updated. The coherent bound xsec of U in UN used to calculate the coherent elastic
  xsec is also updated. The alpha, beta grid for S(a,b) is updated.

* UO2: The coherent bound xsec used to calculate the coherent elastic xsec is updated.

* graphite The coherent elastic component is updated. For coherent elastic scattering
  (MT=2),  the Debye-Waller matrix approach was used based on the same phonon spectrum
  implemented in the calculation of the inelastic cross section (MT=4).

* reactor-graphite: The coherent elastic component and alpha, beta grid for S(a,b) are
  updated. For coherent elastic scattering (MT=2) the Debye-Waller matrix approach was
  used based on the same phonon spectrum implemented in the calculation of the inelastic
  cross section (MT=4).

* polyethylene (CH2) The alpha, beta grid for S(a,b) is updated and temperature 5 K and
  293 K are removed.

* Be-metal The coherent elastic xsec (MT = 2) was generated using an 'in-house'
  Generalized Coherent Elastic Scattering Formulation routine


ENDF/B-VIII.0beta4.1 (2 Sep 2017)
--------------------------------

* Added LEAPR inputs and README's for most evaluations from NCSU, Bettis, CAB and LANL:
  IceIh (tsl-HinIceIh, tsl-OinIceIh), Al (tsl-013_Al_027), Fe (tsl-026_Fe_056),
  YH2 (tsl-HinYH2, tsl-YinYH2), D2O (tsl-DinD2O, tsl-OinD2O), H2O (tsl-HinH2O),
  ZrH (tsl-HinZrH, tsl-ZrinZrH), ortho-D (tsl-ortho-D), ortho-H (tsl-ortho-H),
  para-D (tsl-para-D), para-H (tsl-para-H), liquid methane (tsl-l-CH4),
  solid methane (tsl-s-CH4), Be (tsl-Be-metal), BeO (tsl-BeinBeO, tsl-OinBeO),
  UN (tsl-UinUN, tsl-NinUN), UO2 (tsl-OinUO2, tsl-UinUO2), SiC (tsl-CinSiC, tsl-SiinSiC),
  graphite (tsl-graphite), reactor grade graphite (tsl-reactor-graphite),
  alpha and beta phase SiO2 (tsl-SiO2-alpha, tsl-SiO2-beta), polyethylene (tsl-HinCH2),
  lucite (tsl-HinC5O2H8)

* Heavy water: The new evaluation fixes the issues with the angular differential cross
  section for, which were more noticeable in O(D2O), but actually affected
  both oxygen and deuterium evaluations. The problem was traced to an
  error in the calculation of the Skold correction factors from molecular
  dynamics calculations by Fourier transform.

* Light water: To improve the temperature behavior of the H(H2O) evaluation CAB produced
  two trial evaluations to be tested as candidates for beta5:

    ** Trial evaluation A:
      *** Trial evaluation A simplifies the interpolation between temperatures
          of the frequency spectra by adopting a common grid for all temperatures,
          with a step of E = 0.001265 eV, which is consistent with the spacing of
          0.05 in the beta grid and LAT=1.
      *** The interpolation of the diffusion parameter c is improved and
          matches better the experimental data by Lappi.
      *** The evaluated point at 300K was improved by interpolation of the
          LEAPR parameters between 293.6 K and 350 K. Extrapolated points at 650
          and 800 K are also included.

    ** Trial evaluation B: In addition to the improvements in Trial evaluation A, the
       frequency spectra in for T = 323.6, 350, 373.6, 400, 423,6 K was modified to
       smooth the noise introduced from individual molecular dynamics simulations at
       each temperature.

  In both trial evaluations for light water the point at room temperature
  (T = 293.6 K) remains the same as in ENDF/B-VIII.0-beta4.

  The new evaluations improve the temperature behavior of the total cross
  section, with Trial Evaluation B being slightly better than Trial
  Evaluation A. The libraries were also tested using using benchmark
  LEU-COMP-THERM-046 with differences of 10 - 20 pcm in 293.6 - 350 K. To
  test the effect of the libraries in reflection - moderation, a numerical
  benchmark was created with two sub-assemblies of the IPEN/MB-01 reactor
  separated by 6 cm of water. Differences of 20 - 30 pcm were found
  in 293.6 - 350 K, with Trial evaluation B being behaving better. In
  testing it was found that these systems are very sensitive to how the
  ENDF/B-VII.1 evaluation is used to obtain a baseline.

  Based on this, we recommend that each temperature point should be
  obtained from an interpolated LEAPR input instead of using cross section
  interpolation.

  Overall, we recommend using Trial evaluation B, but include both to have
  feedback on the different changes we introduced.

* tsl-HinH2O.endf, tsl-HinH2O.leapr: Changed sigma-free to make it consistent with neutron sublibrary

* tsl-DinD2O.endf, tsl-DinD2O.leapr: Changed ZAID to 1002 to comply with ENDF-102, app. C

* tsl-OinD2O.endf, tsl-OinD2O.leapr: Changed MAT to 51 and ZAID to 8016 to comply with ENDF-102, app. C

* tsl-graphite.endf: fix author list so it doesn't spill onto next line

* Fixed revision, release, nlib for DinD20, HinH20(all), OinD20, BeinBeO, HinCh2, OinBe0


ENDF/B-VIII.0beta4 (28 Feb 2017)
--------------------------------

* Revised Be(metal) file (tsl-Be-metal.endf)'s coherent elastic scatt. (LEIP LAB @ NCSU)

* Two new UN files (tsl-UinUN.endf, tsl-NinUN.endf)  (LEIP LAB @ NCSU)

* Correct spelling of benzene


ENDF/B-VIII.0beta3.1 (18 Jan 2017)
----------------------------------

* New water ice (phase Ih): tsl-HinIceIh.endf, tsl-OinIceIh.endf (NPL, Bettis)

* New YH2 evaluation: tsl-HinYH2.endf, tsl-YinYH2.endf (NPL, Bettis)


ENDF/B-VIII.0beta3 (1 Nov 2016)
--------------------------------

* Added 300 K and 623.6 K temperatures to several evaluations: tsl-HinH2O.endf,
  tsl-DinD2O.endf, tsl-OinD2O.endf (CAB)

* New Be(metal) file (tsl-Be-metal.endf) (LEIP LAB @ NCSU)

* Two new UO2 files (tsl-OinUO2.endf and tsl-UinUO2.endf) (LEIP LAB @ NCSU)

* New single graphite crystal file (tslgraphite.endf) (LEIP LAB @ NCSU)

* New "reactor processed" graphite file (tsl-reactor-graphite.endf)(LEIP LAB @ NCSU)


ENDF/B-VIII.0beta2 (19 Aug 2016)
--------------------------------

* New polyethyline (tsl-HinCH2.endf) file from A. Hawari, Y. Zhu (LEIP LAB @ NCSU)

* Two new BeO files (tsl-OinBeO.endf and tsl-BeinBeO.endf) Y. Zhu, A. Hawari (LEIP LAB @
  NCSU)


ENDF/B-VIII.0beta1 (25 Apr 2016)
--------------------------------

* No changes since beta0


ENDF/B-VIII.0beta0 (8 Apr 2016)
-------------------------------
* MAT number fixes in tsl-013_Al_027.endf, tsl-OinBeO.endf, tsl-SiO2.endf
  and tsl-UinUO2.endf

* Add alpha and beta phase SiO2 evaluations from Holmes, Al-Qasir, Hehr, and Hawari (NCSU)

* Add Silicon Carbide evaluations from A. Hawari's group (NCSU)

* Set EMAX in many evaluations to 5 eV (See first paragraph of Chapter 7 in ENDF-102)

* Add Lucite (tsl-HinC5O2H8.endf) from A. Hawari's group (NCSU).  The library was
  generated using classical molecular dynamics methods using a predictive approach.  The
  initial atomistic models were parametrized using the fundamental properties (density
  and glass transition temperature) of C5O2H8.

* Add TSL for hydrogen bound in light water calculated with the CAB Model.

* Add the TSL for deuterium and oxygen bound in heavy water calculated with the CAB Model.
