# Phase 1 variant ladder: does the writer-specific floor survive perturbation?

Phase 1 measured Jaccard 0.0 between the two writers' floor sets on SEG BINARY
under `dciodvfy`, on one fixture, from 0 message classes against 1. This ladder
perturbs each writer's own baseline nine ways and re-measures, so the finding
either holds under perturbation or it does not. Reproduce with `python -m colophon.variants`.

Every variant is applied within a writer, to that writer's own baseline. No W1
variant is ever compared against a W2 baseline.

## Baseline, as emitted

| sop_class | validator | W1 | W2 | shared | union | Jaccard |
|---|---|---|---|---|---|---|
| SEG BINARY | dciodvfy | 0 | 1 | 0 | 1 | 0.0000 |
| SEG BINARY | dicom-validator | 6 | 7 | 6 | 7 | 0.8571 |
| TID 1500 SR | dciodvfy | 0 | 0 | 0 | 0 | 1.0000 (vacuous) |
| TID 1500 SR | dicom-validator | 1 | 1 | 1 | 1 | 1.0000 |

Jaccard is over sets of normalised `message_class_id`, counted as distinct
`(SOPInstanceUID, message_class_id)` pairs, never raw lines.

## Round-trip control

The round-trip control moved nothing. Every one of the six baseline objects draws exactly the same message classes after a pydicom read and re-save as it does as emitted, under both validators, so no variant delta below is a round-trip artefact.

## How to read the Jaccard column

Every variant adds the same attribute to both writers' objects, so where it
draws a message it usually draws the same message class on both sides. That
inflates the intersection and pushes the Jaccard toward 1 without touching the
part of the floor set that belongs to the writer. The Jaccard therefore rises
along the ladder for a reason that has nothing to do with whether the floor
transfers.

The column headed **held by one writer only** is the size of the symmetric
difference, and it is the quantity the transfer question actually turns on: it
counts the message classes one writer draws and the other does not. It is
reported next to the Jaccard at every rung, and on its own below.

## The ladder, SEG BINARY

Both writers emit this class, so the Jaccard is a comparison rather than a
single-writer count.

| variant | what it changes | validator | W1 | W2 | shared | union | Jaccard | held by one writer only | direction |
|---|---|---|---|---|---|---|---|---|---|
| V0 | baseline as emitted | dciodvfy | 0 | 1 | 0 | 1 | 0.0000 | 1 | W1 strict subset of W2 |
| V0 | baseline as emitted | dicom-validator | 6 | 7 | 6 | 7 | 0.8571 | 1 | W1 strict subset of W2 |
| V0R | round-trip control, pydicom read and re-save, no change | dciodvfy | 0 | 1 | 0 | 1 | 0.0000 | 1 | W1 strict subset of W2 |
| V0R | round-trip control, pydicom read and re-save, no change | dicom-validator | 6 | 7 | 6 | 7 | 0.8571 | 1 | W1 strict subset of W2 |
| V1 | Standard Extended copy-forward of SliceThickness from the source CT | dciodvfy | 2 | 3 | 2 | 3 | 0.6667 | 1 | W1 strict subset of W2 |
| V1 | Standard Extended copy-forward of SliceThickness from the source CT | dicom-validator | 7 | 8 | 7 | 8 | 0.8750 | 1 | W1 strict subset of W2 |
| V2 | SegmentIdentificationSequence moved from Per-Frame to Shared | dciodvfy | 0 | 1 | 0 | 1 | 0.0000 | 1 | W1 strict subset of W2 |
| V2 | SegmentIdentificationSequence moved from Per-Frame to Shared | dicom-validator | 6 | 7 | 6 | 7 | 0.8571 | 1 | W1 strict subset of W2 |
| V3 | zero-length Laterality (0020,0060) | dciodvfy | 2 | 3 | 2 | 3 | 0.6667 | 1 | W1 strict subset of W2 |
| V3 | zero-length Laterality (0020,0060) | dicom-validator | 6 | 7 | 6 | 7 | 0.8571 | 1 | W1 strict subset of W2 |
| V4 | SegmentAlgorithmType MANUAL with (0062,0007) absent | dciodvfy | 1 | 2 | 1 | 2 | 0.5000 | 1 | W1 strict subset of W2 |
| V4 | SegmentAlgorithmType MANUAL with (0062,0007) absent | dicom-validator | 6 | 7 | 6 | 7 | 0.8571 | 1 | W1 strict subset of W2 |
| V5 | Extended Defined Term in BodyPartExamined (0018,0015) | dciodvfy | 1 | 2 | 1 | 2 | 0.5000 | 1 | W1 strict subset of W2 |
| V5 | Extended Defined Term in BodyPartExamined (0018,0015) | dicom-validator | 6 | 7 | 6 | 7 | 0.8571 | 1 | W1 strict subset of W2 |
| V6 | well-formed private block with one private attribute | dciodvfy | 1 | 2 | 1 | 2 | 0.5000 | 1 | W1 strict subset of W2 |
| V6 | well-formed private block with one private attribute | dicom-validator | 6 | 7 | 6 | 7 | 0.8571 | 1 | W1 strict subset of W2 |
| V7 | retained retired attribute DataSetSubtype (0008,0041) | dciodvfy | 4 | 5 | 4 | 5 | 0.8000 | 1 | W1 strict subset of W2 |
| V7 | retained retired attribute DataSetSubtype (0008,0041) | dicom-validator | 7 | 8 | 7 | 8 | 0.8750 | 1 | W1 strict subset of W2 |
| V8 | populated ContentCreatorName (0070,0084) and identification sequence | dciodvfy | 1 | 2 | 1 | 2 | 0.5000 | 1 | W1 strict subset of W2 |
| V8 | populated ContentCreatorName (0070,0084) and identification sequence | dicom-validator | 6 | 7 | 6 | 7 | 0.8571 | 1 | W1 strict subset of W2 |
| V9 | Deflated Explicit VR LE, 1.2.840.10008.1.2.1.99 | dciodvfy | 13 | 13 | 12 | 14 | 0.8571 | 2 | overlapping, neither contains the other |
| V9 | Deflated Explicit VR LE, 1.2.840.10008.1.2.1.99 | dicom-validator | 6 | 7 | 6 | 7 | 0.8571 | 1 | W1 strict subset of W2 |

## The ladder, TID 1500 SR

Both writers emit TID 1500, but not in the same SOP class: highdicom uses
Comprehensive 3D SR (1.2.840.10008.5.1.4.1.1.88.34) and dcmqi uses Enhanced SR
(1.2.840.10008.5.1.4.1.1.88.22). The comparison holds at the template level and
not at the IOD level.

| variant | what it changes | validator | W1 | W2 | shared | union | Jaccard | held by one writer only | direction |
|---|---|---|---|---|---|---|---|---|---|
| V0 | baseline as emitted | dciodvfy | 0 | 0 | 0 | 0 | 1.0000 | 0 | equal, both sets empty |
| V0 | baseline as emitted | dicom-validator | 1 | 1 | 1 | 1 | 1.0000 | 0 | equal, as at baseline |
| V0R | round-trip control, pydicom read and re-save, no change | dciodvfy | 0 | 0 | 0 | 0 | 1.0000 | 0 | equal, both sets empty |
| V0R | round-trip control, pydicom read and re-save, no change | dicom-validator | 1 | 1 | 1 | 1 | 1.0000 | 0 | equal, as at baseline |
| V1 | Standard Extended copy-forward of SliceThickness from the source CT | dciodvfy | 2 | 2 | 2 | 2 | 1.0000 | 0 | equal, as at baseline |
| V1 | Standard Extended copy-forward of SliceThickness from the source CT | dicom-validator | 2 | 2 | 2 | 2 | 1.0000 | 0 | equal, as at baseline |
| V2 | SegmentIdentificationSequence moved from Per-Frame to Shared | dciodvfy | n/a | n/a | n/a | n/a | NOT_APPLICABLE | n/a | variant is defined on Segmentation functional groups and segment attributes, which this IOD does not carry |
| V2 | SegmentIdentificationSequence moved from Per-Frame to Shared | dicom-validator | n/a | n/a | n/a | n/a | NOT_APPLICABLE | n/a | variant is defined on Segmentation functional groups and segment attributes, which this IOD does not carry |
| V3 | zero-length Laterality (0020,0060) | dciodvfy | 2 | 2 | 2 | 2 | 1.0000 | 0 | equal, as at baseline |
| V3 | zero-length Laterality (0020,0060) | dicom-validator | 2 | 2 | 2 | 2 | 1.0000 | 0 | equal, as at baseline |
| V4 | SegmentAlgorithmType MANUAL with (0062,0007) absent | dciodvfy | n/a | n/a | n/a | n/a | NOT_APPLICABLE | n/a | variant is defined on Segmentation functional groups and segment attributes, which this IOD does not carry |
| V4 | SegmentAlgorithmType MANUAL with (0062,0007) absent | dicom-validator | n/a | n/a | n/a | n/a | NOT_APPLICABLE | n/a | variant is defined on Segmentation functional groups and segment attributes, which this IOD does not carry |
| V5 | Extended Defined Term in BodyPartExamined (0018,0015) | dciodvfy | 2 | 2 | 2 | 2 | 1.0000 | 0 | equal, as at baseline |
| V5 | Extended Defined Term in BodyPartExamined (0018,0015) | dicom-validator | 2 | 2 | 2 | 2 | 1.0000 | 0 | equal, as at baseline |
| V6 | well-formed private block with one private attribute | dciodvfy | 1 | 1 | 1 | 1 | 1.0000 | 0 | equal, as at baseline |
| V6 | well-formed private block with one private attribute | dicom-validator | 1 | 1 | 1 | 1 | 1.0000 | 0 | equal, as at baseline |
| V7 | retained retired attribute DataSetSubtype (0008,0041) | dciodvfy | 4 | 4 | 4 | 4 | 1.0000 | 0 | equal, as at baseline |
| V7 | retained retired attribute DataSetSubtype (0008,0041) | dicom-validator | 2 | 2 | 2 | 2 | 1.0000 | 0 | equal, as at baseline |
| V8 | populated ContentCreatorName (0070,0084) and identification sequence | dciodvfy | 8 | 8 | 8 | 8 | 1.0000 | 0 | equal, as at baseline |
| V8 | populated ContentCreatorName (0070,0084) and identification sequence | dicom-validator | 3 | 3 | 3 | 3 | 1.0000 | 0 | equal, as at baseline |
| V9 | Deflated Explicit VR LE, 1.2.840.10008.1.2.1.99 | dciodvfy | 13 | 13 | 12 | 14 | 0.8571 | 2 | overlapping, neither contains the other |
| V9 | Deflated Explicit VR LE, 1.2.840.10008.1.2.1.99 | dicom-validator | 1 | 1 | 1 | 1 | 1.0000 | 0 | equal, as at baseline |

## Writer-specific residue, rung by rung

Message classes held by exactly one writer, at every rung.

| sop_class | validator | V0 | V0R | V1 | V2 | V3 | V4 | V5 | V6 | V7 | V8 | V9 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SEG BINARY | dciodvfy | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 2 |
| SEG BINARY | dicom-validator | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| TID 1500 SR | dciodvfy | 0 | 0 | 0 | n/a | 0 | n/a | 0 | 0 | 0 | 0 | 2 |
| TID 1500 SR | dicom-validator | 0 | 0 | 0 | n/a | 0 | n/a | 0 | 0 | 0 | 0 | 0 |

The only departure from a flat row is V9 under `dciodvfy`, and the enumeration
below shows what it is: the two residual classes are the same diagnostic, a bad
value length, carrying different byte counts. The Phase 1 normaliser strips
tags, UIDs, frame indices, item indices and quoted values, and it does not strip
hexadecimal lengths, so two byte counts are two message classes. That is stated
rather than fixed, because changing the normaliser to suit one rung would change
every number Phase 1 and Phase 2 have already recorded.

## Does any variant flip the direction of the finding?

**No variant flips the direction of the finding.** Across the nine perturbations, on every shared cell whose baseline sets are not already equal, the two writers' floor sets never become equal and W2's set never becomes a subset of W1's.

The flip test is degenerate on TID 1500 SR under dciodvfy, TID 1500 SR under dicom-validator, where the two writers' sets are already equal at baseline. Those cells are reported in the tables but they cannot flip, because there is no direction there to reverse.

## Residual classes that differ, enumerated

Every message class held by one writer and not the other, at every rung.

### SEG BINARY, dciodvfy

- **V0**, baseline as emitted
    - dcmqi only, `cc372fb8c40c`: Error - Missing attribute Type 2 Required Element=<ClinicalTrialCoordinatingCenterName> Module=<ClinicalTrialSeries> [Error]
- **V0R**, round-trip control, pydicom read and re-save, no change
    - dcmqi only, `cc372fb8c40c`: Error - Missing attribute Type 2 Required Element=<ClinicalTrialCoordinatingCenterName> Module=<ClinicalTrialSeries> [Error]
- **V1**, Standard Extended copy-forward of SliceThickness from the source CT
    - dcmqi only, `cc372fb8c40c`: Error - Missing attribute Type 2 Required Element=<ClinicalTrialCoordinatingCenterName> Module=<ClinicalTrialSeries> [Error]
- **V2**, SegmentIdentificationSequence moved from Per-Frame to Shared
    - dcmqi only, `cc372fb8c40c`: Error - Missing attribute Type 2 Required Element=<ClinicalTrialCoordinatingCenterName> Module=<ClinicalTrialSeries> [Error]
- **V3**, zero-length Laterality (0020,0060)
    - dcmqi only, `cc372fb8c40c`: Error - Missing attribute Type 2 Required Element=<ClinicalTrialCoordinatingCenterName> Module=<ClinicalTrialSeries> [Error]
- **V4**, SegmentAlgorithmType MANUAL with (0062,0007) absent
    - dcmqi only, `cc372fb8c40c`: Error - Missing attribute Type 2 Required Element=<ClinicalTrialCoordinatingCenterName> Module=<ClinicalTrialSeries> [Error]
- **V5**, Extended Defined Term in BodyPartExamined (0018,0015)
    - dcmqi only, `cc372fb8c40c`: Error - Missing attribute Type 2 Required Element=<ClinicalTrialCoordinatingCenterName> Module=<ClinicalTrialSeries> [Error]
- **V6**, well-formed private block with one private attribute
    - dcmqi only, `cc372fb8c40c`: Error - Missing attribute Type 2 Required Element=<ClinicalTrialCoordinatingCenterName> Module=<ClinicalTrialSeries> [Error]
- **V7**, retained retired attribute DataSetSubtype (0008,0041)
    - dcmqi only, `cc372fb8c40c`: Error - Missing attribute Type 2 Required Element=<ClinicalTrialCoordinatingCenterName> Module=<ClinicalTrialSeries> [Error]
- **V8**, populated ContentCreatorName (0070,0084) and identification sequence
    - dcmqi only, `cc372fb8c40c`: Error - Missing attribute Type 2 Required Element=<ClinicalTrialCoordinatingCenterName> Module=<ClinicalTrialSeries> [Error]
- **V9**, Deflated Explicit VR LE, 1.2.840.10008.1.2.1.99
    - highdicom only, `6ae74d4e349f`: (TAG) ? - Error - Bad Value Length - not a multiple of 2 - VL is 0x3e1454db should be 0x3e1454dc [Error]
    - dcmqi only, `e88d56414422`: (TAG) ? - Error - Bad Value Length - not a multiple of 2 - VL is 0x3e14451b should be 0x3e14451c [Error]

### SEG BINARY, dicom-validator

- **V0**, baseline as emitted
    - dcmqi only, `6f56c1b01548`: Module <Clinical Trial Series> Tag (TAG) (Clinical Trial Coordinating Center Name) is missing [ERROR]
- **V0R**, round-trip control, pydicom read and re-save, no change
    - dcmqi only, `6f56c1b01548`: Module <Clinical Trial Series> Tag (TAG) (Clinical Trial Coordinating Center Name) is missing [ERROR]
- **V1**, Standard Extended copy-forward of SliceThickness from the source CT
    - dcmqi only, `6f56c1b01548`: Module <Clinical Trial Series> Tag (TAG) (Clinical Trial Coordinating Center Name) is missing [ERROR]
- **V2**, SegmentIdentificationSequence moved from Per-Frame to Shared
    - dcmqi only, `6f56c1b01548`: Module <Clinical Trial Series> Tag (TAG) (Clinical Trial Coordinating Center Name) is missing [ERROR]
- **V3**, zero-length Laterality (0020,0060)
    - dcmqi only, `6f56c1b01548`: Module <Clinical Trial Series> Tag (TAG) (Clinical Trial Coordinating Center Name) is missing [ERROR]
- **V4**, SegmentAlgorithmType MANUAL with (0062,0007) absent
    - dcmqi only, `6f56c1b01548`: Module <Clinical Trial Series> Tag (TAG) (Clinical Trial Coordinating Center Name) is missing [ERROR]
- **V5**, Extended Defined Term in BodyPartExamined (0018,0015)
    - dcmqi only, `6f56c1b01548`: Module <Clinical Trial Series> Tag (TAG) (Clinical Trial Coordinating Center Name) is missing [ERROR]
- **V6**, well-formed private block with one private attribute
    - dcmqi only, `6f56c1b01548`: Module <Clinical Trial Series> Tag (TAG) (Clinical Trial Coordinating Center Name) is missing [ERROR]
- **V7**, retained retired attribute DataSetSubtype (0008,0041)
    - dcmqi only, `6f56c1b01548`: Module <Clinical Trial Series> Tag (TAG) (Clinical Trial Coordinating Center Name) is missing [ERROR]
- **V8**, populated ContentCreatorName (0070,0084) and identification sequence
    - dcmqi only, `6f56c1b01548`: Module <Clinical Trial Series> Tag (TAG) (Clinical Trial Coordinating Center Name) is missing [ERROR]
- **V9**, Deflated Explicit VR LE, 1.2.840.10008.1.2.1.99
    - dcmqi only, `6f56c1b01548`: Module <Clinical Trial Series> Tag (TAG) (Clinical Trial Coordinating Center Name) is missing [ERROR]

### TID 1500 SR, dciodvfy

- **V2** not applicable: variant is defined on Segmentation functional groups and segment attributes, which this IOD does not carry
- **V4** not applicable: variant is defined on Segmentation functional groups and segment attributes, which this IOD does not carry
- **V9**, Deflated Explicit VR LE, 1.2.840.10008.1.2.1.99
    - highdicom only, `c84fafacba7d`: (TAG) ? - Error - Bad Value Length - not a multiple of 2 - VL is 0x7f154923 should be 0x7f154924 [Error]
    - dcmqi only, `b12d25ee2fa6`: (TAG) ? - Error - Bad Value Length - not a multiple of 2 - VL is 0x3f15d6db should be 0x3f15d6dc [Error]

### TID 1500 SR, dicom-validator

- **V2** not applicable: variant is defined on Segmentation functional groups and segment attributes, which this IOD does not carry
- **V4** not applicable: variant is defined on Segmentation functional groups and segment attributes, which this IOD does not carry
- no residual classes at any applicable rung: the two writers' sets are identical everywhere, including the baseline


## Not applicable cells

Recorded rather than skipped, so a table with a hole in it cannot read as a
table with a zero in it.

| sop_class | variant | reason |
|---|---|---|
| Parametric Map | V2, SegmentIdentificationSequence moved from Per-Frame to Shared | variant is defined on Segmentation functional groups and segment attributes, which this IOD does not carry |
| Parametric Map | V4, SegmentAlgorithmType MANUAL with (0062,0007) absent | variant is defined on Segmentation functional groups and segment attributes, which this IOD does not carry |
| TID 1500 SR | V2, SegmentIdentificationSequence moved from Per-Frame to Shared | variant is defined on Segmentation functional groups and segment attributes, which this IOD does not carry |
| TID 1500 SR | V4, SegmentAlgorithmType MANUAL with (0062,0007) absent | variant is defined on Segmentation functional groups and segment attributes, which this IOD does not carry |

## Non-transferable classes

SEG FRACTIONAL and Parametric Map are **highdicom-only** and carry no Jaccard at
any rung, because dcmqi could not emit them at all. The ladder is still run on
them, so the single-writer floor is known under perturbation, but nothing in
this section is a between-writer comparison.

| sop_class | variant | validator | highdicom message classes |
|---|---|---|---|
| SEG FRACTIONAL | V0 | dciodvfy | 0 |
| SEG FRACTIONAL | V0 | dicom-validator | 6 |
| SEG FRACTIONAL | V0R | dciodvfy | 0 |
| SEG FRACTIONAL | V0R | dicom-validator | 6 |
| SEG FRACTIONAL | V1 | dciodvfy | 2 |
| SEG FRACTIONAL | V1 | dicom-validator | 7 |
| SEG FRACTIONAL | V2 | dciodvfy | 0 |
| SEG FRACTIONAL | V2 | dicom-validator | 6 |
| SEG FRACTIONAL | V3 | dciodvfy | 2 |
| SEG FRACTIONAL | V3 | dicom-validator | 6 |
| SEG FRACTIONAL | V4 | dciodvfy | 1 |
| SEG FRACTIONAL | V4 | dicom-validator | 6 |
| SEG FRACTIONAL | V5 | dciodvfy | 1 |
| SEG FRACTIONAL | V5 | dicom-validator | 6 |
| SEG FRACTIONAL | V6 | dciodvfy | 1 |
| SEG FRACTIONAL | V6 | dicom-validator | 6 |
| SEG FRACTIONAL | V7 | dciodvfy | 4 |
| SEG FRACTIONAL | V7 | dicom-validator | 7 |
| SEG FRACTIONAL | V8 | dciodvfy | 1 |
| SEG FRACTIONAL | V8 | dicom-validator | 6 |
| SEG FRACTIONAL | V9 | dciodvfy | 13 |
| SEG FRACTIONAL | V9 | dicom-validator | 6 |
| Parametric Map | V0 | dciodvfy | 1 |
| Parametric Map | V0 | dicom-validator | 9 |
| Parametric Map | V0R | dciodvfy | 1 |
| Parametric Map | V0R | dicom-validator | 9 |
| Parametric Map | V1 | dciodvfy | 3 |
| Parametric Map | V1 | dicom-validator | 10 |
| Parametric Map | V2 | dciodvfy | NOT_APPLICABLE, variant is defined on Segmentation functional groups and segment attributes, which this IOD does not carry |
| Parametric Map | V2 | dicom-validator | NOT_APPLICABLE, variant is defined on Segmentation functional groups and segment attributes, which this IOD does not carry |
| Parametric Map | V3 | dciodvfy | 1 |
| Parametric Map | V3 | dicom-validator | 9 |
| Parametric Map | V4 | dciodvfy | NOT_APPLICABLE, variant is defined on Segmentation functional groups and segment attributes, which this IOD does not carry |
| Parametric Map | V4 | dicom-validator | NOT_APPLICABLE, variant is defined on Segmentation functional groups and segment attributes, which this IOD does not carry |
| Parametric Map | V5 | dciodvfy | 2 |
| Parametric Map | V5 | dicom-validator | 9 |
| Parametric Map | V6 | dciodvfy | 2 |
| Parametric Map | V6 | dicom-validator | 9 |
| Parametric Map | V7 | dciodvfy | 5 |
| Parametric Map | V7 | dicom-validator | 10 |
| Parametric Map | V8 | dciodvfy | 2 |
| Parametric Map | V8 | dicom-validator | 9 |
| Parametric Map | V9 | dciodvfy | 13 |
| Parametric Map | V9 | dicom-validator | 9 |

## What was dropped

Nothing was sampled. 60 objects were built or reused and every one was
run through both validators. Cells where a variant does not apply are listed
above with their reason and are not counted as measured zeros. No IDC object was
fetched and no network call was made: the ladder is local, on the Phase 1
fixture only.
