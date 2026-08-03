# Phase 2 pilot: ten dcmqi-written Segmentation objects

Ten series, 5 analysis results, fetched from IDC, validated, deleted.
Reproduce with `python -m colophon.fetch --pilot`.

**This is a pilot, not a sample.** The selection is a deterministic
smallest-first pick spread across analysis results, chosen to exercise the
pipeline. No sampling frame was built and no rate is computed from ten objects.

## The question asked

Does the message class seen on the Phase 1 dcmqi fixture appear in the corpus?

`Error - Missing attribute Type 2 Required Element=<ClinicalTrialCoordinatingCenterName> Module=<ClinicalTrialSeries>`

message_class_id `cc372fb8c40c`

**Present on 0 of 10 objects.**

## Every message class observed

Counted as distinct (SOPInstanceUID, message_class_id) pairs, using the Phase 1
normaliser. Never raw lines.

| validator | message_class_id | severity | objects | template |
|---|---|---|---|---|
| dciodvfy | `815f5dab3ba7` | Warning | 10 / 10 | Warning - Missing attribute or value that would be needed to build DICOMDIR - Study ID |
| dciodvfy | `4a71864409dc` | Warning | 7 / 10 | Warning - Missing attribute or value that would be needed to build DICOMDIR - Study Time |
| dciodvfy | `3cc801c58c5f` | Warning | 4 / 10 | Warning - Value dubious for this VR - (TAG) PN Content Creator's Name PN [1] = <IDC> - Retired Person Name form |
| dciodvfy | `4f1c684b72ff` | Warning | 2 / 10 | Warning - Value dubious for this VR - (TAG) PN Content Creator's Name PN [1] = <Imaging Data Commons> - Retired Person Name form |
| dciodvfy | `74637eecf0ac` | Warning | 2 / 10 | Warning - Value dubious for this VR - (TAG) PN Content Creator's Name PN [1] = <Reader1> - Retired Person Name form |
| dciodvfy | `76ab0c6981d2` | Warning | 2 / 10 | Warning - CodingSchemeDesignator is deprecated - attribute <CodingSchemeDesignator> = <SRT> |
| dciodvfy | `9ee22e1c2108` | Warning | 2 / 10 | Warning - Unrecognized defined term <GEIIS> for value 1 of attribute <Coding Scheme Designator> |
| dciodvfy | `c3858e46e8c5` | Warning | 2 / 10 | Warning - Value dubious for this VR - (TAG) PN Patient's Name PN [1] = <Prostate-MRI-US-Biopsy-1149> - Retired Person Name form |
| dciodvfy | `0507257941dd` | Warning | 1 / 10 | Warning - Value is zero for value 1 of attribute <Patient's Size> |
| dciodvfy | `0786a34e0c26` | Warning | 1 / 10 | Warning - Value is zero for value 1 of attribute <Patient's Weight> |
| dciodvfy | `8c857ef640a3` | Warning | 1 / 10 | Warning - Value dubious for this VR - (TAG) PN Patient's Name PN [1] = <UPENN-GBM-00201> - Retired Person Name form |
| dciodvfy | `fa52cde9c940` | Warning | 1 / 10 | Warning - Value dubious for this VR - (TAG) PN Patient's Name PN [1] = <TCGA-KM-8639> - Retired Person Name form |
| dicom-validator | `380880930b44` | ERROR | 10 / 10 | Module <Multi-frame Functional Groups> (TAG) (Per-Frame Functional Groups Sequence) Tag (TAG) (Plane Position Sequence) is unexpected |
| dicom-validator | `6f01abd4f319` | ERROR | 10 / 10 | Module <Multi-frame Functional Groups> (TAG) (Shared Functional Groups Sequence) Tag (TAG) (Plane Orientation Sequence) is unexpected |
| dicom-validator | `972394b5bb82` | ERROR | 10 / 10 | Module <Multi-frame Functional Groups> (TAG) (Per-Frame Functional Groups Sequence) Tag (TAG) (Segment Identification Sequence) is unexpected |
| dicom-validator | `d0eabe730084` | ERROR | 10 / 10 | Module <Multi-frame Functional Groups> (TAG) (Per-Frame Functional Groups Sequence) Tag (TAG) (Frame Content Sequence) is unexpected |
| dicom-validator | `d81147d20e87` | ERROR | 10 / 10 | Module <Multi-frame Functional Groups> (TAG) (Shared Functional Groups Sequence) Tag (TAG) (Pixel Measures Sequence) is unexpected |
| dicom-validator | `f782376ec325` | ERROR | 10 / 10 | Module <Multi-frame Functional Groups> (TAG) (Per-Frame Functional Groups Sequence) Tag (TAG) (Derivation Image Sequence) is unexpected |

## Provenance captured, for later

Three states are reported, never two: a Type 1 attribute present but zero length
is a different finding from one that is absent.

`SoftwareVersions (0018,1020)`:

| value | objects |
|---|---|
| `7ae0873` | 2 |
| `f86b34f` | 2 |
| `451bf84` | 2 |
| `4e5b700` | 2 |
| `ef9e227` | 2 |

`ImplementationVersionName (0002,0013)`:

| value | objects |
|---|---|
| `OFFIS_DCMTK_366` | 6 |
| `0.5` | 2 |
| `OFFIS_DCMTK_368` | 2 |

`ImplementationClassUID (0002,0012)`:

| value | objects |
|---|---|
| `1.2.276.0.7230010.3.0.3.6.6` | 6 |
| `1.3.6.1.4.1.22213.1.143` | 2 |
| `1.2.276.0.7230010.3.0.3.6.8` | 2 |

`ContributingEquipmentSequence (0018,A001)` present on
**0 of 10** objects.

## Fetch

`s5cmd` was used rather than the AWS CLI, which is not installed on this
machine. Both are named in the study brief. The substitution is recorded rather
than absorbed.

Free space was checked before every fetch and every series was deleted
immediately after its validators ran. Nothing accumulated.

## What was dropped

Nothing within the pilot: all ten selected series were fetched and every fetched
object was run through both validators. The pilot itself is bounded at ten
series by instruction and is not a sample of anything.
