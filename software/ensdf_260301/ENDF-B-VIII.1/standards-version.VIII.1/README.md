ENDF/B-VIII.1 Standards Sublibrary README
==============================================================================

Maintainer: G.P.A. Nobre, NNDC, BNL

Affiliation: NNDC, Brookhaven National Laboratory

Date: 30 August, 2024


This is the final ENDF/B-VIII.1 release for the *standards sublibrary*. The full list of changes across multiple ENDF/B-VIII.1-Beta releases, since ENDF/B-VIII.0, are listed in detail in the file CHANGELOG.md. A summarized list is also shown below.

Although standards data are distributed in the ENDF-6 format, they are NOT meant to be processed for nor used in transport calculations. Only specific reactions in specific energy ranges are regarded as standards, while to produce ENDF-102-compliant ENDF-6 formatted files additional non-standards data need to be included. We refer the user to the article Nuclear Data Sheets 148 (2018) 143–188 for complete information on standards reactions and energy ranges from ENDF/B-VIII.0 which were adopted for ENDF/B-VIII.1. This information, alongside the corresponding data, can also be found in the IAEA-maintained website https://nds.iaea.org/standards/.


The ENDF-6 files in this ENDF/B-VIII.1 release were successfully processed using NJOY-16.76 and FUDGE-6.7 for all sublibraries, and AMPX (SCALE-7.0b08) for neutrons and photo-atomic sublibraries.  Note: AMPX processing for the thermal neutron scattering sublibrary used features to be made available in a future SCALE-7.0 beta.

Complete and detailed information on the ENDF/B-VIII.1 release can be found in the accompanying article that will be submitted for publication in the Nuclear Data Sheets journal shortly after the ENDF/B-VIII.1 release.




History of ENDF/B-VIII.1-Beta releases for the *standards sublibrary*:
----

* VIII.1 final release (30 August, 2024): No changes, apart from updates to the metadata in file headers, which impacted all files.

* VIII.1-Beta4 (28 June, 2024): Same as ENDF/B-VIII.0.

* VIII.1-Beta3 (11 January, 2024): No changes, not part of the release.

* VIII.1-Beta2 (4 August, 2023): No changes, not part of the release.

* VIII.1-Beta1.1 (18 April, 2023): No changes, not part of the release.

* VIII.1-Beta1 (1 March 2023): Not part of the release, as there were no updates from VIII.0.









ENDF/B-VIII.0 Standards Sublibrary README
=========================================

Maintainer: D.A. Brown, NNDC, BNL

Affiliation: NNDC, Brookhaven National Laboratory

Date: 2 Feb 2018

Neutron cross-section standards are explicitly or implicitly used in the
measurement and evaluation of all other neutron reaction cross-sections.
Very few cross-sections can be defined as absolute - most cross-sections are
measured relative to the cross-section standards for normalization to absolute
values.  This sublibrary collects the results of the 2017 Neutron Standards
Evaluation project (see https://www-nds.iaea.org/standards/) and is summarized
in A.D. Carlson, et al. "Evaluation of the Neutron Data Standards" Nuclear Data
Sheets 148, 143 (2018).

The 2017 Neutron Standards were evaluated in tandem with the ENDF/B-VIII.0 and
CIELO evaluation projects.  Indeed the CIELO 238U and 235U evaluations adopted
by CSEWG for ENDF/B-VIII.0 are identical to the standards (n,f) cross sections
over the energy ranges common to both projects.  Therefore, all standards
evaluations are actually incorporated into their respective FULL neutron or
decay data files.  In this release of this sublibrary, we have collected all the
FULL evaluations that contain part or all of the 2017 Neutron Standards
Evaluations.

The standards files (with mean values and covariances) are provided for
informational purposes.  While the files in the standards sublibrary are
complete (for transport purposes), this sublibrary does not include enough
materials for any known application.

Below we tabulate the standards and point to the appropriate file(s) containing
the standards data.


| REACTION   | STANDARDS ENERGY RANGE | ENDF FILE           |  MF |  MT |
|------------|------------------------|---------------------|-----|-----|
| H(n,n)     | 1 keV to 20 MeV        | std-001_H_001.endf  | 3,4 |   2 |
| 3He(n,p)   | 0.0253 eV to 50 keV    | std-002_He_003.endf |   3 | 103 |
| 6Li(n,t)   | 0.0253 eV to 1.0 MeV   | std-003_Li_006.endf |   3 | 105 |
| 10B(n,a)   | 0.0253 eV to 1 MeV     | std-005_B_010.endf  |   3 | 800 |
| 10B(n,a1+g)| 0.0253 eV to 1 MeV     | std-005_B_010.endf  |   3 | 801 |
| (sum)      | 0.0253 eV to 1 MeV     | std-005_B_010.endf  |   3 | 107 |
| natC(n,n)  | 10 eV to 1.8 MeV       | std-006_C_012.endf  | 3,4 |   2 |
|            |                        | std-006_C_013.endf  | 3,4 |   2 |
|            |                        | std-006_C_000.endf  | 3,4 |   2 |
| 197Au(n,g) | 0.0253 eV,             | std-079_Au_197.endf |   3 | 102 |
|            | 0.2 to 2.5 MeV,        |                     |     |     |
|            | 30 keV MACS            |                     |     |     |
| 235U(n,f)  | 0.0253 eV,             | std-092_U_235.endf  |   3 |  18 |
|            | 7.8-11 eV,             |                     |     |     |
|            | 0.15 MeV to 200 MeV    |                     |     |     |
| 238U(n,f)  | 2 MeV to 200 MeV       | std-092_U_238.endf  |   3 |  18 |
| 252Cf(sf)  | PFNS                   | std-098_Cf_252.endf |   5 |  18 |
|            |                        |                     |   1 | 456 |



Comments about the covariance in the 2017 Neutron Standards evaluations
-----------------------------------------------------------------------

1.  The covariance data in the 2017 Neutron Standards evaluations represents
    uncertainties and correlations in differential data only.
2.  The use of this covariance to calculate uncertainties for integral
    quantities such as Keff will usually result in an overestimate of the
    uncertainty.
