# Phase 2 census: the eight non-Segmentation derived classes

Census, not a sample. Every object in scope is fetched, validated, recorded and
deleted. Segmentation Storage is excluded by assertion. Reproduce with
`python -m colophon.census --run`.

Manifest: **291,604 series, 150.35 GB**, IDC v24. Classes run cheapest bytes
first so a usable result exists before the long pass.

## Coverage, as of this writing

| SOP class | in manifest | validated | status |
|---|---|---|---|
| Real World Value Mapping Storage | 20 | 20 | complete |
| Key Object Selection Document Storage | 40 | 40 | complete |
| Grayscale Softcopy Presentation State Storage | 1,086 | 1,086 | complete |
| Parametric Map Storage | 691 | 691 | complete |
| Comprehensive SR Storage | 2,118 | 2,118 | complete |
| Comprehensive 3D SR Storage | 5,408 | 5,408 | complete |
| RT Structure Set Storage | 19,358 | 18,936 | in flight |
| Enhanced SR Storage | 262,883 | 0 | not started |

**Only the classes marked complete are reported below.** A class in flight
reports nothing, because a partial class would read as a rate.

## Error and warning class rates, complete classes

An object counts once for a class of message, not once per message. Rates are
gross: no floor has been subtracted, because the Phase 1 floor sets are
writer-specific and fixture-specific and do not transfer to these writers.

| SOP class | analysis_result_id | objects | with error class | pct | with warning class | pct | dubious ContentCreatorName |
|---|---|---|---|---|---|---|---|
| Comprehensive 3D SR Storage | nnu_net_bpr_annotations | 2,906 | 1,438 | 49.5 | 2,906 | 100.0 | 0 |
| Comprehensive SR Storage | dicom_sr_breast_clinical | 1,292 | 1 | 0.1 | 1,292 | 100.0 | 0 |
| Comprehensive 3D SR Storage | lung_pet_ct_dx_annotations | 1,091 | 38 | 3.5 | 1,091 | 100.0 | 0 |
| Comprehensive 3D SR Storage | nlst_sybil | 970 | 325 | 33.5 | 970 | 100.0 | 0 |
| Parametric Map Storage | tcga_gbm360 | 691 | 691 | 100.0 | 691 | 100.0 | 0 |
| Grayscale Softcopy Presentation State Storage | qiba_volct_1b | 624 | 51 | 8.2 | 624 | 100.0 | 0 |
| Grayscale Softcopy Presentation State Storage | nan | 462 | 462 | 100.0 | 462 | 100.0 | 0 |
| Comprehensive SR Storage | nan | 462 | 462 | 100.0 | 462 | 100.0 | 0 |
| Comprehensive SR Storage | qiba_volct_1b | 364 | 364 | 100.0 | 364 | 100.0 | 0 |
| Comprehensive 3D SR Storage | prostatex_targets | 345 | 0 | 0.0 | 345 | 100.0 | 0 |
| Comprehensive 3D SR Storage | rms_mutation_prediction_expert_annotations | 96 | 91 | 94.8 | 96 | 100.0 | 0 |
| Key Object Selection Document Storage | nan | 40 | 40 | 100.0 | 40 | 100.0 | 0 |
| Real World Value Mapping Storage | nan | 20 | 20 | 100.0 | 20 | 100.0 | 0 |

## Leading message classes, complete classes

| SOP class | validator | severity | objects | template |
|---|---|---|---|---|
| Comprehensive 3D SR Storage | dciodvfy | Warning | 5,312 | Warning - Missing attribute or value that would be needed to build DICOMDIR - Study ID |
| Comprehensive 3D SR Storage | dciodvfy | Warning | 3,178 | Warning - Missing attribute or value that would be needed to build DICOMDIR - Study Time |
| Comprehensive 3D SR Storage | dciodvfy | Error | 935 | Error - Missing attribute Type 2 Required Element=<ClinicalTrialSiteName> Module=<ClinicalTrialSubject> |
| Comprehensive 3D SR Storage | dicom-validator | ERROR | 935 | Module <Clinical Trial Subject> Tag (TAG) (Clinical Trial Site Name) is missing |
| Comprehensive 3D SR Storage | dciodvfy | Error | 828 | Error - Missing attribute Type 1C Conditional Element=<DeidentificationMethod> Module=<Patient> |
| Comprehensive 3D SR Storage | dciodvfy | Error | 828 | Error - Missing attribute Type 1C Conditional Element=<DeidentificationMethodCodeSequence> Module=<Patient> |
| Comprehensive SR Storage | dciodvfy | Warning | 2,118 | Warning - CodingSchemeDesignator is deprecated - attribute <CodingSchemeDesignator> = <SRT> |
| Comprehensive SR Storage | dciodvfy | Warning | 1,356 | Warning - Missing attribute or value that would be needed to build DICOMDIR - Study Time |
| Comprehensive SR Storage | dciodvfy | Warning | 891 | Warning - Missing attribute or value that would be needed to build DICOMDIR - Study ID |
| Comprehensive SR Storage | dicom-validator | ERROR | 826 | Module <SR Document Content> (TAG) (Content Sequence) / (TAG) (Content Sequence) / (TAG) (Content Sequence) / (TAG) (Content Sequence) / (TAG) (Conten |
| Comprehensive SR Storage | dciodvfy | Error | 722 | Error - Shall not be present for Referenced SOP Class that is not multi-frame - attribute <ReferencedFrameNumber> |
| Comprehensive SR Storage | dicom-validator | ERROR | 722 | Module <SR Document Content> (TAG) (Content Sequence) / (TAG) (Content Sequence) / (TAG) (Content Sequence) / (TAG) (Content Sequence) / (TAG) (Conten |
| Grayscale Softcopy Presentation State Storage | dcmpschk | Warning | 1,086 | W: Test passed. |
| Grayscale Softcopy Presentation State Storage | dciodvfy | Warning | 624 | Warning - Missing attribute or value that would be needed to build DICOMDIR - Study ID |
| Grayscale Softcopy Presentation State Storage | dciodvfy | Error | 462 | Error - Missing attribute Type 2C Conditional Element=<Laterality> Module=<GeneralSeries> |
| Grayscale Softcopy Presentation State Storage | dciodvfy | Warning | 462 | Warning - Value dubious for this VR - (TAG) PN Patient's Name PN [1] = <QIBA_CT_1C> - Retired Person Name form |
| Grayscale Softcopy Presentation State Storage | dciodvfy | Warning | 384 | Warning - Missing attribute or value that would be needed to build DICOMDIR - Study Time |
| Grayscale Softcopy Presentation State Storage | dciodvfy | Warning | 240 | Warning - Value dubious for this VR - (TAG) PN Patient's Name PN [1] = <UID> - Retired Person Name form |
| Key Object Selection Document Storage | dciodvfy | Error | 40 | Error - Missing attribute Type 2 Required Element=<Manufacturer> Module=<GeneralEquipment> |
| Key Object Selection Document Storage | dciodvfy | Warning | 40 | Warning - Missing attribute or value that would be needed to build DICOMDIR - Study ID |
| Key Object Selection Document Storage | dicom-validator | ERROR | 40 | Module <General Equipment> Tag (TAG) (Manufacturer) is missing |
| Key Object Selection Document Storage | dciodvfy | Warning | 4 | Warning - Value dubious for this VR - (TAG) PN Patient's Name PN [1] = <QIN-Breast-DCE-MRI-BC01> - Retired Person Name form |
| Key Object Selection Document Storage | dciodvfy | Warning | 4 | Warning - Value dubious for this VR - (TAG) PN Patient's Name PN [1] = <QIN-Breast-DCE-MRI-BC05> - Retired Person Name form |
| Key Object Selection Document Storage | dciodvfy | Warning | 4 | Warning - Value dubious for this VR - (TAG) PN Patient's Name PN [1] = <QIN-Breast-DCE-MRI-BC06> - Retired Person Name form |
| Parametric Map Storage | dciodvfy | Warning | 691 | Warning - Unrecognized defined term <AGGRESSIVENESS> for value 3 of attribute <Image Type> |
| Parametric Map Storage | dciodvfy | Warning | 691 | Warning - Unrecognized defined term <AI> for value 4 of attribute <Image Type> |
| Parametric Map Storage | dicom-validator | ERROR | 691 | Module <General> Tag (TAG) (Columns) is unexpected |
| Parametric Map Storage | dicom-validator | ERROR | 691 | Module <General> Tag (TAG) (Rows) is unexpected |
| Parametric Map Storage | dicom-validator | ERROR | 691 | Module <Multi-frame Functional Groups> (TAG) (Shared Functional Groups Sequence) Tag (TAG) (Frame VOI LUT Sequence) is unexpected |
| Parametric Map Storage | dicom-validator | ERROR | 691 | Module <Multi-frame Functional Groups> (TAG) (Shared Functional Groups Sequence) Tag (TAG) (Parametric Map Frame Type Sequence) is unexpected |
| Real World Value Mapping Storage | dciodvfy | Error | 20 | Error - Missing attribute Type 2C Conditional Element=<Laterality> Module=<GeneralSeries> |
| Real World Value Mapping Storage | dciodvfy | Warning | 20 | Warning - CodingSchemeDesignator is deprecated - attribute <CodingSchemeDesignator> = <SRT> |
| Real World Value Mapping Storage | dciodvfy | Warning | 20 | Warning - Missing attribute or value that would be needed to build DICOMDIR - Study ID |
| Real World Value Mapping Storage | dciodvfy | Warning | 1 | Warning - Unrecognized defined term <L> for value 1 of attribute <Coding Scheme Designator> |
| Real World Value Mapping Storage | dciodvfy | Warning | 1 | Warning - Value dubious for this VR - (TAG) PN Patient's Name PN [1] = <CT-PET-VI-01> - Retired Person Name form |
| Real World Value Mapping Storage | dciodvfy | Warning | 1 | Warning - Value dubious for this VR - (TAG) PN Patient's Name PN [1] = <CT-PET-VI-02> - Retired Person Name form |

## Provenance carriers, three states

Absent, zero length and non-empty are counted separately throughout. Zero length
is a distinct finding: in the two IODs where Enhanced General Equipment is
Mandatory, Manufacturer, ManufacturerModelName, DeviceSerialNumber and
SoftwareVersions are Type 1, so a zero-length value there is a conformance
violation while an absent one in another IOD may not be.

| SOP class | carrier | absent | zero length | non-empty |
|---|---|---|---|---|
| Comprehensive 3D SR Storage | ContentCreatorName | 5408 | 0 | 0 |
| Comprehensive 3D SR Storage | DeviceSerialNumber | 5312 | 0 | 96 |
| Comprehensive 3D SR Storage | ImplementationClassUID | 0 | 0 | 5408 |
| Comprehensive 3D SR Storage | ImplementationVersionName | 0 | 0 | 5408 |
| Comprehensive 3D SR Storage | Manufacturer | 0 | 0 | 5408 |
| Comprehensive 3D SR Storage | ManufacturerModelName | 5312 | 0 | 96 |
| Comprehensive 3D SR Storage | SeriesDescription | 0 | 0 | 5408 |
| Comprehensive 3D SR Storage | SoftwareVersions | 5312 | 0 | 96 |
| Comprehensive SR Storage | ContentCreatorName | 2118 | 0 | 0 |
| Comprehensive SR Storage | DeviceSerialNumber | 722 | 447 | 949 |
| Comprehensive SR Storage | ImplementationClassUID | 0 | 0 | 2118 |
| Comprehensive SR Storage | ImplementationVersionName | 0 | 0 | 2118 |
| Comprehensive SR Storage | Manufacturer | 0 | 0 | 2118 |
| Comprehensive SR Storage | ManufacturerModelName | 0 | 0 | 2118 |
| Comprehensive SR Storage | SeriesDescription | 0 | 0 | 2118 |
| Comprehensive SR Storage | SoftwareVersions | 462 | 0 | 1656 |
| Grayscale Softcopy Presentation State Storage | ContentCreatorName | 0 | 1022 | 64 |
| Grayscale Softcopy Presentation State Storage | DeviceSerialNumber | 1086 | 0 | 0 |
| Grayscale Softcopy Presentation State Storage | ImplementationClassUID | 0 | 0 | 1086 |
| Grayscale Softcopy Presentation State Storage | ImplementationVersionName | 0 | 0 | 1086 |
| Grayscale Softcopy Presentation State Storage | Manufacturer | 0 | 104 | 982 |
| Grayscale Softcopy Presentation State Storage | ManufacturerModelName | 566 | 0 | 520 |
| Grayscale Softcopy Presentation State Storage | SeriesDescription | 1086 | 0 | 0 |
| Grayscale Softcopy Presentation State Storage | SoftwareVersions | 566 | 0 | 520 |
| Key Object Selection Document Storage | ContentCreatorName | 40 | 0 | 0 |
| Key Object Selection Document Storage | DeviceSerialNumber | 40 | 0 | 0 |
| Key Object Selection Document Storage | ImplementationClassUID | 0 | 0 | 40 |
| Key Object Selection Document Storage | ImplementationVersionName | 0 | 0 | 40 |
| Key Object Selection Document Storage | Manufacturer | 40 | 0 | 0 |
| Key Object Selection Document Storage | ManufacturerModelName | 40 | 0 | 0 |
| Key Object Selection Document Storage | SeriesDescription | 0 | 0 | 40 |
| Key Object Selection Document Storage | SoftwareVersions | 40 | 0 | 0 |
| Parametric Map Storage | ContentCreatorName | 0 | 691 | 0 |
| Parametric Map Storage | DeviceSerialNumber | 0 | 0 | 691 |
| Parametric Map Storage | ImplementationClassUID | 0 | 0 | 691 |
| Parametric Map Storage | ImplementationVersionName | 0 | 0 | 691 |
| Parametric Map Storage | Manufacturer | 0 | 0 | 691 |
| Parametric Map Storage | ManufacturerModelName | 0 | 0 | 691 |
| Parametric Map Storage | SeriesDescription | 0 | 0 | 691 |
| Parametric Map Storage | SoftwareVersions | 0 | 0 | 691 |
| Real World Value Mapping Storage | ContentCreatorName | 0 | 20 | 0 |
| Real World Value Mapping Storage | DeviceSerialNumber | 20 | 0 | 0 |
| Real World Value Mapping Storage | ImplementationClassUID | 0 | 0 | 20 |
| Real World Value Mapping Storage | ImplementationVersionName | 0 | 0 | 20 |
| Real World Value Mapping Storage | Manufacturer | 0 | 0 | 20 |
| Real World Value Mapping Storage | ManufacturerModelName | 20 | 0 | 0 |
| Real World Value Mapping Storage | SeriesDescription | 0 | 0 | 20 |
| Real World Value Mapping Storage | SoftwareVersions | 0 | 0 | 20 |

## What was dropped

Nothing within the completed classes: every series in the manifest for those
classes was fetched and validated. Fetch failures, if any, are recorded in the
records file with status FETCH_FAILED and are visible in the counts above as a
shortfall against the manifest.

Classes marked in flight or not started are exactly that, and no number is
reported for them.
