# Table 1: writers, sentinels and where identity is recoverable

IDC v24. Index evidence only, zero bytes downloaded. Reproduce with
`python -m colophon.writers`.

## Writer census

Which toolkit wrote each derived series, inferred from the two equipment
attributes the index carries. This is **provisional**: ImplementationVersionName
(0002,0013) and ContributingEquipmentSequence (0018,A001) are stronger writer
evidence and are only readable from fetched objects, so the table is recomputed
in Phase 2.

| writer | series | pct | collections | analysis_results | sop_classes |
|---|---|---|---|---|---|
| dcmqi | 411,865 | 85.490 | 35 | 10 | 2 |
| not identifiable from index | 47,826 | 9.930 | 52 | 10 | 7 |
| OHIF-XNAT Viewer | 16,184 | 3.360 | 4 | 4 | 1 |
| highdicom | 2,097 | 0.440 | 3 | 2 | 2 |
| pydicom-seg | 1,991 | 0.410 | 3 | 0 | 1 |
| PixelMed | 1,292 | 0.270 | 4 | 1 | 1 |
| QIICR Reporting via 3D Slicer | 494 | 0.100 | 6 | 1 | 2 |
| Plastimatch | 1 | 0.000 | 1 | 0 | 1 |

47,826 series, 9.9 percent, cannot be attributed to
a writer from the index. That number is an input to Phase 2, not a finding.

This table exists because ledger row PRE-02 excludes round-trip passes from the
pass numerator, and the exclusion cannot be applied without knowing who wrote
each object.

Per SOP class:

| sop_class_name | writer | series |
|---|---|---|
| Comprehensive 3D SR Storage | not identifiable from index | 5,312 |
| Comprehensive 3D SR Storage | highdicom | 96 |
| Comprehensive SR Storage | PixelMed | 1,292 |
| Comprehensive SR Storage | not identifiable from index | 826 |
| Enhanced SR Storage | dcmqi | 262,883 |
| Grayscale Softcopy Presentation State Storage | not identifiable from index | 1,086 |
| Key Object Selection Document Storage | not identifiable from index | 40 |
| Parametric Map Storage | not identifiable from index | 691 |
| RT Structure Set Storage | OHIF-XNAT Viewer | 16,184 |
| RT Structure Set Storage | not identifiable from index | 3,173 |
| RT Structure Set Storage | Plastimatch | 1 |
| Real World Value Mapping Storage | QIICR Reporting via 3D Slicer | 20 |
| Segmentation Storage | dcmqi | 148,982 |
| Segmentation Storage | not identifiable from index | 36,698 |
| Segmentation Storage | highdicom | 2,001 |
| Segmentation Storage | pydicom-seg | 1,991 |
| Segmentation Storage | QIICR Reporting via 3D Slicer | 474 |

## Sentinel values

A sentinel is a producer-identity string an encoding toolkit writes
unconditionally. Where the standard makes an attribute Type 1, as Enhanced
General Equipment does for Manufacturer, ManufacturerModelName,
DeviceSerialNumber and SoftwareVersions, the attribute is always present and a
presence check reports 100 percent while measuring nothing. Sentinels are
excluded from the numerator of any informativeness rate.

The list is published as `results/sentinels.json` so that a reader can reject a
specific entry rather than having to reverse engineer a regex.
14 entries at present, every one carrying the basis on which it
qualifies and its verification status.

## Where identity is recoverable

Producer identity is not one attribute. It is a ranked set of places identity
might be recorded, and the useful question is the level at which it first
appears, not whether level 1 carries it.

| level | carrier | in the object | in the index |
|---|---|---|---|
| 1 | DICOM equipment attributes | yes | yes |
| 2 | ContributingEquipmentSequence, Algorithm Identification Macro | yes | no, Phase 2 |
| 3 | free-text description | yes | yes |
| 4 | IDC registry metadata | **no** | yes |

Level 4 is not in the object. Identity available only there is identity a
downloaded file does not carry.

| analysis_result_id | series | first_informative_level | version_in_free_text | version_example |
|---|---|---|---|---|
| totalsegmentator_ct_segmentations | 378,153 | 3 | 1 | v1.5.6 |
| tcga_sbu_til_maps | 21,030 | 1 | 0 |  |
| eay131_tumor_annotations | 15,799 | 1 | 0 |  |
| dicom_lidc_idri_nodules | 13,718 | 3 | 0 |  |
| bamf_aimi_annotations | 8,202 | 3 | 0 |  |
| nnu_net_bpr_annotations | 7,817 | 1 | 0 |  |
| pan_cancer_nuclei_seg_dicom | 6,074 | 1 | 0 |  |
| prostate_mri_us_biopsy_dicom_annotations | 2,328 | 3 | 0 |  |
| nlstseg | 1,803 | 3 | 0 |  |
| qiba_volct_1b | 1,508 | 1 | 0 |  |
| dicom_sr_breast_clinical | 1,292 | 1 | 0 |  |
| lung_pet_ct_dx_annotations | 1,091 | 1 | 0 |  |
| nlst_sybil | 970 | 1 | 0 |  |
| tcga_gbm360 | 691 | 1 | 0 |  |
| cptac_ccrcc_tumor_annotations | 636 | 1 | 0 |  |
| cptac_ucec_tumor_annotations | 617 | 1 | 0 |  |
| cptac_pda_tumor_annotations | 536 | 1 | 0 |  |
| qin_lungct_seg | 378 | 1 | 0 |  |
| prostatex_targets | 345 | 1 | 0 |  |
| rms_mutation_prediction_expert_annotations | 193 | 1 | 0 |  |
| rider_lungct_seg | 118 | 1 | 0 |  |

### The largest analysis result

`totalsegmentator_ct_segmentations`, 378,153
series, carries at level 1 only `QIICR` and a git URL. At level 3 every one of
its series carries a `SeriesDescription` of the form
`TotalSegmentator(v1.5.6) Segmentation of Series 2`.

So the algorithm **and a version string** are recoverable. Not from a provenance
carrier, not from anywhere the standard or any profile directs a consumer to
look, and not in a form any convention makes machine-parseable, but recoverable.
The claim this study can defend is therefore about where identity lives and what
it costs to find, not about identity being absent.

One ambiguity is left open rather than resolved: the version token `v1.5.6` is
not labelled, and dcmqi also has a 1.5.6 release. Whether it denotes the
TotalSegmentator version or the encoder version cannot be settled from the
index. Phase 2 reads SoftwareVersions (0018,1020), which is Type 1 in Enhanced
General Equipment, and settles it.

## What unstable spellings cost

An unstable declared name is a triviality until harm is shown, so it is
measured. A consumer assembling every series produced through dcmqi
queries the declared model name.

| | |
|---|---|
| series truly produced through dcmqi | 411,865 |
| distinct declared spellings | 6 |
| recall, exact match on the most common spelling | 92.44 percent |
| **series missed by that query** | **31,153** |
| distinct groups after normalising scheme, case and suffix | 2 |

The missed count is not a rounding error, so the finding stands as a measured
result rather than an observation. Normalisation collapses the spellings to
2 groups, of which the smaller is a
personal fork and arguably a genuinely different build rather than a spelling of
the same one.

## What was dropped

Nothing from the writer census or the cohort measurement: both run over all
481,750 derived series. The carrier hierarchy reports analysis results of at
least 100 series, which covers 463,299 series;
smaller analysis results are in the CSV.
