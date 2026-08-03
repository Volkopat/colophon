# Phase 3: the Segmentation Storage sample, and what it says about algorithm identification

The PRE-06 frame, executed. `colophon.sample.EXECUTE` was set True on approval
and nothing else in the frame moved: 21 strata, seed 20260802, registered
minimum n = 384, one per-stratum byte cap, the same nested
draw. Reproduce with `python -m colophon.phase3 --run` then `python -m colophon.phase3 --report`.

Manifest 5,941 series, 129.77 GB
exact against a 150 GB budget. The pre-registered byte gate
fired **0 time(s)**.

## The question

Of all sampled Segmentation objects, what fraction declare
`SegmentAlgorithmType (0062,0008)` as AUTOMATIC or SEMIAUTOMATIC while
`SegmentationAlgorithmIdentificationSequence (0062,0007)` is absent, and what
fraction have it present but incomplete, missing any Type 1 child.

**The two are never merged, and the reason is not stylistic.** STD-02 settled it
against PS3.3 2026c: in the Segmentation IOD (0062,0007) is Type 3 with no
condition of any kind. Omitting it on an AUTOMATIC segment is conformant, and no
validator can flag it. The 1C form of that sequence exists only in the Height Map
Segmentation Image Module, which Table A.51-1 does not include. So **absence is a
gap in the standard**. Once the sequence is present its three Type 1 children are
mandatory, so **incompleteness is a defect in the object**. A single combined
number would be a statement about neither.

## The answer

Coverage at the time of writing: **5,941 of
5,941 sampled series, 100.0 percent**, carrying
6,386 objects and 41,258 segments.

### Segment level

Denominator: the 36,488 segments declaring AUTOMATIC or
SEMIAUTOMATIC.

| state of (0062,0007) | segments | percent of non-MANUAL segments |
|---|---|---|
| **absent** | 34,234 | **93.82** |
| **present but incomplete**, missing a Type 1 child | 0 | **0.00** |
| present and carrying zero items | 0 | 0.00 |
| present and complete | 2,254 | 6.18 |

### Object level

One object holds many segments, so the object-level question has two readings and
both are reported. Denominator: the 4,213 objects
carrying at least one non-MANUAL segment, of 6,386 objects.

| reading | objects | percent of objects with a non-MANUAL segment | percent of all objects |
|---|---|---|---|
| at least one non-MANUAL segment with (0062,0007) **absent** | 2,828 | 67.13 | 44.28 |
| at least one with (0062,0007) **present but incomplete** | 0 | 0.00 | 0.00 |
| at least one with (0062,0007) present and complete | 1,385 | 32.87 | 21.69 |

### Per stratum

The reporting rule is the one PRE-06 registered, applied to the series validated
in the cell: at or above 384, a rate with a Wilson interval;
30 to 383, the same with a
below-registered-n flag; under 30, counts only and never a rate.

Segment-level intervals are **unadjusted for clustering**. Segments nest in
objects and objects in collections, and the frame measured a collection-level
planning rho of 0.919, so these intervals are narrower than the truth. The
population estimate below carries the clustered variance.

| stratum | series_validated | segments_non_manual | segments_ident_absent | pct_absent | segments_ident_present_incomplete | pct_present_incomplete | segments_ident_present_complete | reporting_rule |
|---|---|---|---|---|---|---|---|---|
| dcmqi / totalsegmentator_ct_segmentations | 384 | 29,226 | 29,226 | 100.000 | 0 | 0.000 | 0 | rate with Wilson interval |
| dcmqi / nnu_net_bpr_annotations | 384 | 1,536 | 1,536 | 100.000 | 0 | 0.000 | 0 | rate with Wilson interval |
| dcmqi / (null) | 384 | 1,095 | 1,095 | 100.000 | 0 | 0.000 | 0 | rate with Wilson interval |
| not identifiable from index / rms_mutation_prediction_expert_annotations | 97 | 1,044 | 0 | 0.000 | 0 | 0.000 | 1,044 | rate with Wilson interval, below-registered-n flag |
| dcmqi / bamf_aimi_annotations | 384 | 859 | 859 | 100.000 | 0 | 0.000 | 0 | rate with Wilson interval |
| not identifiable from index / tcga_sbu_til_maps | 384 | 470 | 0 | 0.000 | 0 | 0.000 | 470 | rate with Wilson interval |
| not identifiable from index / qiba_volct_1b | 384 | 384 | 384 | 100.000 | 0 | 0.000 | 0 | rate with Wilson interval |
| highdicom / eay131_tumor_annotations | 384 | 384 | 0 | 0.000 | 0 | 0.000 | 384 | rate with Wilson interval |
| QIICR Reporting via 3D Slicer / qin_lungct_seg | 378 | 378 | 378 | 100.000 | 0 | 0.000 | 0 | rate with Wilson interval, below-registered-n flag |
| not identifiable from index / pan_cancer_nuclei_seg_dicom | 75 | 356 | 0 | 0.000 | 0 | 0.000 | 356 | rate with Wilson interval, below-registered-n flag |
| not identifiable from index / (null) | 384 | 330 | 330 | 100.000 | 0 | 0.000 | 0 | rate with Wilson interval |
| dcmqi / prostate_mri_us_biopsy_dicom_annotations | 384 | 189 | 189 | 100.000 | 0 | 0.000 | 0 | rate with Wilson interval |
| QIICR Reporting via 3D Slicer / (null) | 96 | 96 | 96 | 100.000 | 0 | 0.000 | 0 | rate with Wilson interval, below-registered-n flag |
| pydicom-seg / (null) | 384 | 83 | 83 | 100.000 | 0 | 0.000 | 0 | rate with Wilson interval |
| dcmqi / rider_lungct_seg | 59 | 58 | 58 | 100.000 | 0 | 0.000 | 0 | rate with Wilson interval, below-registered-n flag |
| dcmqi / dicom_lidc_idri_nodules | 384 | 0 | 0 | nan | 0 | nan | 0 | rate with Wilson interval |
| dcmqi / pancreas_ct_seg | 80 | 0 | 0 | nan | 0 | nan | 0 | rate with Wilson interval, below-registered-n flag |
| dcmqi / prostatex_seg_hires | 66 | 0 | 0 | nan | 0 | nan | 0 | rate with Wilson interval, below-registered-n flag |
| dcmqi / prostatex_seg_zones | 98 | 0 | 0 | nan | 0 | nan | 0 | rate with Wilson interval, below-registered-n flag |
| dcmqi / nlstseg | 384 | 0 | 0 | nan | 0 | nan | 0 | rate with Wilson interval |
| highdicom / (null) | 384 | 0 | 0 | nan | 0 | nan | 0 | rate with Wilson interval |

Object level, same strata:

| stratum | objects | objects_with_non_manual_segment | objects_any_ident_absent | pct_any_ident_absent_of_objects_with_non_manual | objects_any_ident_incomplete | pct_any_ident_incomplete_of_objects_with_non_manual | reporting_rule |
|---|---|---|---|---|---|---|---|
| dcmqi / (null) | 384 | 170 | 170 | 100.000 | 0 | 0.000 | rate with Wilson interval |
| dcmqi / dicom_lidc_idri_nodules | 384 | 0 | 0 | nan | 0 | nan | rate with Wilson interval |
| dcmqi / bamf_aimi_annotations | 384 | 384 | 384 | 100.000 | 0 | 0.000 | rate with Wilson interval |
| dcmqi / nnu_net_bpr_annotations | 384 | 384 | 384 | 100.000 | 0 | 0.000 | rate with Wilson interval |
| dcmqi / nlstseg | 384 | 0 | 0 | nan | 0 | nan | rate with Wilson interval |
| pydicom-seg / (null) | 384 | 83 | 83 | 100.000 | 0 | 0.000 | rate with Wilson interval |
| not identifiable from index / tcga_sbu_til_maps | 384 | 384 | 0 | 0.000 | 0 | 0.000 | rate with Wilson interval |
| dcmqi / prostate_mri_us_biopsy_dicom_annotations | 384 | 189 | 189 | 100.000 | 0 | 0.000 | rate with Wilson interval |
| dcmqi / totalsegmentator_ct_segmentations | 384 | 384 | 384 | 100.000 | 0 | 0.000 | rate with Wilson interval |
| not identifiable from index / qiba_volct_1b | 384 | 384 | 384 | 100.000 | 0 | 0.000 | rate with Wilson interval |
| not identifiable from index / (null) | 384 | 318 | 318 | 100.000 | 0 | 0.000 | rate with Wilson interval |
| highdicom / eay131_tumor_annotations | 384 | 384 | 0 | 0.000 | 0 | 0.000 | rate with Wilson interval |
| highdicom / (null) | 384 | 0 | 0 | nan | 0 | nan | rate with Wilson interval |
| QIICR Reporting via 3D Slicer / qin_lungct_seg | 378 | 378 | 378 | 100.000 | 0 | 0.000 | rate with Wilson interval, below-registered-n flag |
| not identifiable from index / pan_cancer_nuclei_seg_dicom | 356 | 356 | 0 | 0.000 | 0 | 0.000 | rate with Wilson interval, below-registered-n flag |
| not identifiable from index / rms_mutation_prediction_expert_annotations | 261 | 261 | 0 | 0.000 | 0 | 0.000 | rate with Wilson interval, below-registered-n flag |
| dcmqi / prostatex_seg_zones | 98 | 0 | 0 | nan | 0 | nan | rate with Wilson interval, below-registered-n flag |
| QIICR Reporting via 3D Slicer / (null) | 96 | 96 | 96 | 100.000 | 0 | 0.000 | rate with Wilson interval, below-registered-n flag |
| dcmqi / pancreas_ct_seg | 80 | 0 | 0 | nan | 0 | nan | rate with Wilson interval, below-registered-n flag |
| dcmqi / prostatex_seg_hires | 66 | 0 | 0 | nan | 0 | nan | rate with Wilson interval, below-registered-n flag |
| dcmqi / rider_lungct_seg | 59 | 58 | 58 | 100.000 | 0 | 0.000 | rate with Wilson interval, below-registered-n flag |

### Per analysis_result_id

| analysis_result_id | series_validated | segments_non_manual | segments_ident_absent | pct_absent | segments_ident_present_incomplete | pct_present_incomplete | segments_ident_present_complete | reporting_rule |
|---|---|---|---|---|---|---|---|---|
| totalsegmentator_ct_segmentations | 384 | 29,226 | 29,226 | 100.000 | 0 | 0.000 | 0 | rate with Wilson interval |
| (null) | 1,632 | 1,604 | 1,604 | 100.000 | 0 | 0.000 | 0 | rate with Wilson interval |
| nnu_net_bpr_annotations | 384 | 1,536 | 1,536 | 100.000 | 0 | 0.000 | 0 | rate with Wilson interval |
| rms_mutation_prediction_expert_annotations | 97 | 1,044 | 0 | 0.000 | 0 | 0.000 | 1,044 | rate with Wilson interval, below-registered-n flag |
| bamf_aimi_annotations | 384 | 859 | 859 | 100.000 | 0 | 0.000 | 0 | rate with Wilson interval |
| tcga_sbu_til_maps | 384 | 470 | 0 | 0.000 | 0 | 0.000 | 470 | rate with Wilson interval |
| qiba_volct_1b | 384 | 384 | 384 | 100.000 | 0 | 0.000 | 0 | rate with Wilson interval |
| eay131_tumor_annotations | 384 | 384 | 0 | 0.000 | 0 | 0.000 | 384 | rate with Wilson interval |
| qin_lungct_seg | 378 | 378 | 378 | 100.000 | 0 | 0.000 | 0 | rate with Wilson interval, below-registered-n flag |
| pan_cancer_nuclei_seg_dicom | 75 | 356 | 0 | 0.000 | 0 | 0.000 | 356 | rate with Wilson interval, below-registered-n flag |
| prostate_mri_us_biopsy_dicom_annotations | 384 | 189 | 189 | 100.000 | 0 | 0.000 | 0 | rate with Wilson interval |
| rider_lungct_seg | 59 | 58 | 58 | 100.000 | 0 | 0.000 | 0 | rate with Wilson interval, below-registered-n flag |
| dicom_lidc_idri_nodules | 384 | 0 | 0 | nan | 0 | nan | 0 | rate with Wilson interval |
| pancreas_ct_seg | 80 | 0 | 0 | nan | 0 | nan | 0 | rate with Wilson interval, below-registered-n flag |
| nlstseg | 384 | 0 | 0 | nan | 0 | nan | 0 | rate with Wilson interval |
| prostatex_seg_hires | 66 | 0 | 0 | nan | 0 | nan | 0 | rate with Wilson interval, below-registered-n flag |
| prostatex_seg_zones | 98 | 0 | 0 | nan | 0 | nan | 0 | rate with Wilson interval, below-registered-n flag |

Object level, same grouping:

| analysis_result_id | objects | objects_with_non_manual_segment | objects_any_ident_absent | pct_any_ident_absent_of_objects_with_non_manual | objects_any_ident_incomplete | pct_any_ident_incomplete_of_objects_with_non_manual | reporting_rule |
|---|---|---|---|---|---|---|---|
| (null) | 1,632 | 667 | 667 | 100.000 | 0 | 0.000 | rate with Wilson interval |
| bamf_aimi_annotations | 384 | 384 | 384 | 100.000 | 0 | 0.000 | rate with Wilson interval |
| dicom_lidc_idri_nodules | 384 | 0 | 0 | nan | 0 | nan | rate with Wilson interval |
| eay131_tumor_annotations | 384 | 384 | 0 | 0.000 | 0 | 0.000 | rate with Wilson interval |
| nlstseg | 384 | 0 | 0 | nan | 0 | nan | rate with Wilson interval |
| nnu_net_bpr_annotations | 384 | 384 | 384 | 100.000 | 0 | 0.000 | rate with Wilson interval |
| prostate_mri_us_biopsy_dicom_annotations | 384 | 189 | 189 | 100.000 | 0 | 0.000 | rate with Wilson interval |
| totalsegmentator_ct_segmentations | 384 | 384 | 384 | 100.000 | 0 | 0.000 | rate with Wilson interval |
| qiba_volct_1b | 384 | 384 | 384 | 100.000 | 0 | 0.000 | rate with Wilson interval |
| tcga_sbu_til_maps | 384 | 384 | 0 | 0.000 | 0 | 0.000 | rate with Wilson interval |
| qin_lungct_seg | 378 | 378 | 378 | 100.000 | 0 | 0.000 | rate with Wilson interval, below-registered-n flag |
| pan_cancer_nuclei_seg_dicom | 356 | 356 | 0 | 0.000 | 0 | 0.000 | rate with Wilson interval, below-registered-n flag |
| rms_mutation_prediction_expert_annotations | 261 | 261 | 0 | 0.000 | 0 | 0.000 | rate with Wilson interval, below-registered-n flag |
| prostatex_seg_zones | 98 | 0 | 0 | nan | 0 | nan | rate with Wilson interval, below-registered-n flag |
| pancreas_ct_seg | 80 | 0 | 0 | nan | 0 | nan | rate with Wilson interval, below-registered-n flag |
| prostatex_seg_hires | 66 | 0 | 0 | nan | 0 | nan | rate with Wilson interval, below-registered-n flag |
| rider_lungct_seg | 59 | 58 | 58 | 100.000 | 0 | 0.000 | rate with Wilson interval, below-registered-n flag |

### Which Type 1 child is missing, where incompleteness occurs

| missing Type 1 child | stratum | segments |
|---|---|---|
| none | | |

### What is not in the denominator, and why

`SegmentAlgorithmType (0062,0008)` is Type 1 and its values are **Enumerated**,
not Defined Terms: PS3.3 2026c Table C.8.20-4 gives AUTOMATIC, SEMIAUTOMATIC and
MANUAL and nothing else. The sample contains a fourth value.

**25 segments carry a value that
is none of the three.** They are outside the AUTOMATIC-or-SEMIAUTOMATIC
denominator by the wording of the question, so they are counted here rather than
dropped silently.

Whether that value is also non-conformant is not decided here.
**`dciodvfy` scores it independently and flags it at Error severity**,
`Error - Unrecognized enumerated value <...> for value 1 of attribute
<Segment Algorithm Type>`, on the objects carrying
25 of them. The adjudication is a
third party's and the citation is the third party's own.

| stratum | analysis_result_id | collection_id | SegmentAlgorithmType | segments | segments_in_objects_dciodvfy_flagged |
|---|---|---|---|---|---|
| not identifiable from index / (null) | (null) | qiba_ct_1c | SEMIAUTOMATED | 25 | 25 |

### What a complete macro actually says

A complete macro is not the same thing as an informative one, and the two
attributes can contradict each other in plain text. This table is observation
only. `SegmentAlgorithmType (0062,0008)` is Type 1 with enumerated values and
`AlgorithmName (0066,0036)` is a free-text LO, and PS3.3 states no relation
between them, so a segment whose declared type and whose named algorithm
disagree is **conformant** and is reported here without being scored either way.

**384 segments declare AUTOMATIC or
SEMIAUTOMATIC while their macro names the algorithm as a manual one.** The
disagreement is recorded and not resolved.

| analysis_result_id | SegmentAlgorithmType | AlgorithmName | AlgorithmVersion | AlgorithmFamilyCode | segments |
|---|---|---|---|---|---|
| rms_mutation_prediction_expert_annotations | AUTOMATIC | Rhabdomyosarcoma Pathology CNN AI Segmentation Model | V1.0 | 123110,DCM,Artificial Intelligence | 1,044 |
| eay131_tumor_annotations | AUTOMATIC | Manual Segmentation | 1.0 | 113076,DCM,Segmentation | 384 |
| pan_cancer_nuclei_seg_dicom | AUTOMATIC | Pan-Cancer-Nuclei-Seg | 1.0 | 123110,DCM,Artificial Intelligence | 356 |
| tcga_sbu_til_maps | AUTOMATIC | Stony Brook TIL Segmentation Inception-V4 2022 | 1.0 | 123110,DCM,Artificial Intelligence | 298 |
| tcga_sbu_til_maps | AUTOMATIC | Stony Brook TIL Segmentation CNN 2018 | 1.0 | 123110,DCM,Artificial Intelligence | 172 |

## The population estimate, both variances

The estimator PRE-06 registered: stratified, series weighted, with design weights
w_i = N_h / n_h read from a complete index rather than estimated. The unit is the
series and the outcome is "at least one non-MANUAL segment in the series shows
the state".

| | absence | incompleteness |
|---|---|---|
| point estimate, percent of series | **77.645** | **0.0** |
| standard error, design based with fpc | 0.1 | 0.0 |
| standard error, clustered on collection | 15.377 | 0.0 |
| degrees of freedom, clustered | 90 | 90 |
| single-collection strata collapsed into one variance stratum | 12 | 12 |
| series contributing | 5,941 | 5,941 |

The clustered standard error is the wider of the two and is the one to quote. The
design-based one is the correct width for the only claim this study is scoped to
make, which is a count of objects in IDC v24 and not
a statement about DICOM practice.

## Secondary: the provenance carriers, three states, never two

Absent and zero-length are different findings and are never collapsed. In the
Segmentation IOD, Enhanced General Equipment is Mandatory, so Manufacturer,
ManufacturerModelName, DeviceSerialNumber and SoftwareVersions are all Type 1:
for those four, both absent and zero-length are conformance violations.

| carrier | objects | absent | zero_length | non_empty |
|---|---|---|---|---|
| ContentCreatorName | 6,386 | 0 | 2,568 | 3,818 |
| ContributingEquipmentSequence | 6,386 | 6,002 | 0 | 384 |
| DeviceSerialNumber | 6,386 | 966 | 397 | 5,023 |
| ImplementationClassUID | 6,386 | 0 | 0 | 6,386 |
| ImplementationVersionName | 6,386 | 0 | 0 | 6,386 |
| Manufacturer | 6,386 | 0 | 0 | 6,386 |
| ManufacturerModelName | 6,386 | 0 | 0 | 6,386 |
| SeriesDescription | 6,386 | 765 | 0 | 5,621 |
| SoftwareVersions | 6,386 | 0 | 0 | 6,386 |

`ContributingEquipmentSequence (0018,A001)` items, by declared purpose:

| stratum | PurposeOfReference | Manufacturer | ManufacturerModelName | SoftwareVersions | items |
|---|---|---|---|---|---|
| not identifiable from index / tcga_sbu_til_maps | 109102,DCM,Processing Equipment | Highdicom open-source contributors | highdicom | 0.27.0 | 384 |
| not identifiable from index / tcga_sbu_til_maps | 109101,DCM,Acquisition Equipment | Leica Biosystems | Aperio converted by com.pixelmed.convert.TIFFToDicom | ['v10.2.41', 'Sat May 28 11:42:06 EDT 2022'] | 115 |
| not identifiable from index / tcga_sbu_til_maps | 109101,DCM,Acquisition Equipment | Leica Biosystems | Aperio converted by com.pixelmed.convert.TIFFToDicom | ['v12.0.15', 'Sat May 28 11:42:06 EDT 2022'] | 86 |
| not identifiable from index / tcga_sbu_til_maps | 109101,DCM,Acquisition Equipment | Leica Biosystems | Aperio converted by com.pixelmed.convert.TIFFToDicom | ['vFS90 01', 'Sat May 28 11:42:06 EDT 2022'] | 76 |
| not identifiable from index / tcga_sbu_til_maps | 109101,DCM,Acquisition Equipment | Leica Biosystems | Aperio converted by com.pixelmed.convert.TIFFToDicom | ['v12.0.11', 'Sat May 28 11:42:06 EDT 2022'] | 41 |
| not identifiable from index / tcga_sbu_til_maps | 109101,DCM,Acquisition Equipment | Carl Zeiss | Mirax converted by com.pixelmed.convert.TIFFToDicom | Thu Feb 15 07:25:54 EST 2024 | 19 |
| not identifiable from index / tcga_sbu_til_maps | 109101,DCM,Acquisition Equipment | Leica Biosystems | Aperio converted by com.pixelmed.convert.TIFFToDicom | ['v10.2.20', 'Sat May 28 11:42:06 EDT 2022'] | 9 |
| not identifiable from index / tcga_sbu_til_maps | 109101,DCM,Acquisition Equipment | Hamamatsu | NanoZoomer converted by com.pixelmed.convert.TIFFToDicom | Thu Feb 15 07:25:54 EST 2024 | 9 |
| not identifiable from index / tcga_sbu_til_maps | 109101,DCM,Acquisition Equipment | Leica Biosystems | Aperio converted by com.pixelmed.convert.TIFFToDicom | ['v10.2.23', 'Sat May 28 11:42:06 EDT 2022'] | 9 |
| not identifiable from index / tcga_sbu_til_maps | 109101,DCM,Acquisition Equipment | Leica Biosystems | Aperio converted by com.pixelmed.convert.TIFFToDicom | ['v10.0.50', 'Sat May 28 11:42:06 EDT 2022'] | 5 |
| not identifiable from index / tcga_sbu_til_maps | 109101,DCM,Acquisition Equipment | Leica Biosystems | Aperio converted by com.pixelmed.convert.TIFFToDicom | ['v12.1.3', 'Sat May 28 11:42:06 EDT 2022'] | 5 |
| not identifiable from index / tcga_sbu_til_maps | 109101,DCM,Acquisition Equipment | Leica Biosystems | Aperio converted by com.pixelmed.convert.TIFFToDicom | ['v10.2.24', 'Sat May 28 11:42:06 EDT 2022'] | 3 |

## The writer label moved, and PRE-06 registered what to do about it

Limitation 3 of the frame said this in advance: the writer label is inferred
from the two equipment attributes the index carries, Phase 3 reads
`ImplementationVersionName` and `ContributingEquipmentSequence` which are
stronger evidence, and **if those change a series' writer the pre-registered
response is to relabel and report the reallocation, never to silently redraw.**

They do change it. **1,001 objects across
3 strata carry object-level evidence naming a
writer the index could not name.** The draw is unchanged and nothing has been
redrawn. The rule table is `colophon.writers.WRITER_RULES`, imported unchanged
from Phase 0: only the evidence widens, so nothing the existing table does not
match has been newly classified, and anything it misses stays unidentified.

The carriers are asked in this order: `ContributingEquipmentSequence`, `ImplementationVersionName`, `Manufacturer and ManufacturerModelName`.

| stratum | writer_from_index | writer_from_object | deciding_carrier | objects |
|---|---|---|---|---|
| not identifiable from index / qiba_volct_1b | not identifiable from index | not identifiable from index | none of the three carriers | 384 |
| dcmqi / (null) | dcmqi | dcmqi | Manufacturer and ManufacturerModelName | 384 |
| not identifiable from index / (null) | not identifiable from index | not identifiable from index | none of the three carriers | 384 |
| not identifiable from index / tcga_sbu_til_maps | not identifiable from index | highdicom | ContributingEquipmentSequence | 384 |
| dcmqi / dicom_lidc_idri_nodules | dcmqi | dcmqi | Manufacturer and ManufacturerModelName | 384 |
| pydicom-seg / (null) | pydicom-seg | pydicom-seg | Manufacturer and ManufacturerModelName | 384 |
| highdicom / eay131_tumor_annotations | highdicom | highdicom | Manufacturer and ManufacturerModelName | 384 |
| highdicom / (null) | highdicom | highdicom | Manufacturer and ManufacturerModelName | 384 |
| dcmqi / nlstseg | dcmqi | dcmqi | Manufacturer and ManufacturerModelName | 384 |
| dcmqi / bamf_aimi_annotations | dcmqi | dcmqi | Manufacturer and ManufacturerModelName | 384 |
| dcmqi / prostate_mri_us_biopsy_dicom_annotations | dcmqi | dcmqi | Manufacturer and ManufacturerModelName | 384 |
| dcmqi / nnu_net_bpr_annotations | dcmqi | dcmqi | Manufacturer and ManufacturerModelName | 384 |
| dcmqi / totalsegmentator_ct_segmentations | dcmqi | dcmqi | Manufacturer and ManufacturerModelName | 384 |
| QIICR Reporting via 3D Slicer / qin_lungct_seg | QIICR Reporting via 3D Slicer | QIICR Reporting via 3D Slicer | Manufacturer and ManufacturerModelName | 378 |
| not identifiable from index / pan_cancer_nuclei_seg_dicom | not identifiable from index | highdicom | ImplementationVersionName | 356 |
| not identifiable from index / rms_mutation_prediction_expert_annotations | not identifiable from index | highdicom | ImplementationVersionName | 261 |
| dcmqi / prostatex_seg_zones | dcmqi | dcmqi | Manufacturer and ManufacturerModelName | 98 |
| QIICR Reporting via 3D Slicer / (null) | QIICR Reporting via 3D Slicer | QIICR Reporting via 3D Slicer | Manufacturer and ManufacturerModelName | 96 |
| dcmqi / pancreas_ct_seg | dcmqi | dcmqi | Manufacturer and ManufacturerModelName | 80 |
| dcmqi / prostatex_seg_hires | dcmqi | dcmqi | Manufacturer and ManufacturerModelName | 66 |
| dcmqi / rider_lungct_seg | dcmqi | dcmqi | Manufacturer and ManufacturerModelName | 59 |

Two consequences, both of which belong to whoever reads this next rather than to
this pass. A stratum that moves to `highdicom` moves from having no measured
Phase 1 floor to having one, so a post-floor rate becomes quotable where the
frame said it was not. And `ImplementationVersionName` in the sample carries
values such as `dcm4che-1.4.27` that `WRITER_RULES` has no rule for, so they
stay unidentified here rather than being classified by a rule invented after
seeing the data.

## Secondary: validator message classes, gross

Counted as distinct (SOPInstanceUID, message_class_id) pairs through the Phase 1
parser and normaliser, never as raw lines. Severity is matched in both forms, the
line-start `Error - ` form and the embedded ` - (Error|Warning) - ` form. Exit
status is recorded and never tested.

**These are gross counts and nothing here is NET.** No message class in this
table has been adjudicated against a cited PS3 section, and an unadjudicated
class is UNDECIDABLE rather than a defect. Adjudication is a separate pass with
two independent adjudicators.

| validator | severity_as_emitted | message_class_id | objects | message_template |
|---|---|---|---|---|
| dicom-validator | ERROR | d81147d20e87 | 6,386 | Module <Multi-frame Functional Groups> (TAG) (Shared Functional Groups Sequence) Tag (TAG) (Pixel Measures Sequence) is unexpected |
| dicom-validator | ERROR | 6f01abd4f319 | 5,385 | Module <Multi-frame Functional Groups> (TAG) (Shared Functional Groups Sequence) Tag (TAG) (Plane Orientation Sequence) is unexpected |
| dicom-validator | ERROR | 380880930b44 | 5,385 | Module <Multi-frame Functional Groups> (TAG) (Per-Frame Functional Groups Sequence) Tag (TAG) (Plane Position Sequence) is unexpected |
| dicom-validator | ERROR | d0eabe730084 | 5,385 | Module <Multi-frame Functional Groups> (TAG) (Per-Frame Functional Groups Sequence) Tag (TAG) (Frame Content Sequence) is unexpected |
| dicom-validator | ERROR | 972394b5bb82 | 4,498 | Module <Multi-frame Functional Groups> (TAG) (Per-Frame Functional Groups Sequence) Tag (TAG) (Segment Identification Sequence) is unexpected |
| dciodvfy | Warning | 815f5dab3ba7 | 4,296 | Warning - Missing attribute or value that would be needed to build DICOMDIR - Study ID |
| dicom-validator | ERROR | f782376ec325 | 4,104 | Module <Multi-frame Functional Groups> (TAG) (Per-Frame Functional Groups Sequence) Tag (TAG) (Derivation Image Sequence) is unexpected |
| dciodvfy | Warning | 4a71864409dc | 1,729 | Warning - Missing attribute or value that would be needed to build DICOMDIR - Study Time |
| dciodvfy | Warning | 76ab0c6981d2 | 1,697 | Warning - CodingSchemeDesignator is deprecated - attribute <CodingSchemeDesignator> = <SRT> |
| dciodvfy | Warning | 3cc801c58c5f | 1,152 | Warning - Value dubious for this VR - (TAG) PN Content Creator's Name PN [1] = <IDC> - Retired Person Name form |
| dciodvfy | Error | 702e93617425 | 966 | Error - Missing attribute Type 1 Required Element=<DeviceSerialNumber> Module=<EnhancedGeneralEquipment> |
| dicom-validator | ERROR | 6a2af7ccf9a8 | 966 | Module <Enhanced General Equipment> Tag (TAG) (Device Serial Number) is missing |
| dicom-validator | ERROR | f6bdf6ba947e | 887 | Module <Multi-frame Functional Groups> (TAG) (Shared Functional Groups Sequence) Tag (TAG) (Segment Identification Sequence) is unexpected |
| dciodvfy | Error | 8b9d6770833b | 617 | Error - Value is zero for value 1 of attribute <Slice Thickness> |
| dciodvfy | Warning | 50a67d7318c0 | 617 | Warning - DimensionIndexPointer Attribute not present in any Shared or Per-Frame Functional Group - (TAG) |

## The panel that ran, and the arm that did not

For this SOP class the conformance panel is dciodvfy, dicom-validator and
PixelMed `DicomInstanceValidator`. **Two of the three ran.** The PixelMed jar is
absent from the pinned toolchain, V-04, so its arm is recorded as NOT RUN and
never as passed. `dcmpschk` was not run at all: on a Segmentation missing two
Type 1 attributes it printed `Test passed.`, so addendum 02 keeps it to GSPS.

The reference-parse axis, `segimage2itkimage` and the highdicom reader, was not
run in this pass and no axis-2 result is reported.

## What was dropped

- **0 series failed to fetch** and
  carry a FETCH_FAILED record rather than being silently absent.
- **0 objects failed to read** and
  carry a READ_FAILED record.
- The sample reads 5,941 of 190,146 series in the class,
  3.12 percent. The 184,205 series not drawn are
  represented through the stratum weights W_h and through nothing else.
- One stratum was cut below the registered minimum by the byte cap, at n = 75 of
  6,074 series, and its Wilson half-width at p = 5 percent widens from 2.21 to
  5.29 points.
- Every limitation the frame declared still holds and is not restated here.
  `results/pre06_sampling_frame.md` carries all ten.
