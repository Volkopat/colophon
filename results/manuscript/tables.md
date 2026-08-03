# Tables 1 to 6

Generated from the measurement artefacts by `python -m colophon.manuscript_tables`. No cell is typed. Every table names the ledger rows it rests on.

## Table 1

**Table 1. Population, coverage and the unit each result is scoped to.** Seven classes are a complete census; Segmentation is the PRE-06 stratified probability sample. Enhanced SR Storage is **excluded from every object-weighted rate in this paper**, 35,161 of 262,883 series recorded and the class still running, because a partial class reads as a rate. Analysis-result cells are complete for the seven censused classes. For Segmentation they are the identifiers observed in the PRE-06 sample of 5,941 of 190,146 series; frame coverage of that class's cells is unmeasured (C3T-13). Ledger PRE-06, C3T-00, P2C-01.

| SOP class | objects | analysis-result cells | coverage |
|---|---|---|---|
| RT Structure Set Storage | 19,358 | 6 | complete census |
| Segmentation Storage | 6,386 | 17 | PRE-06 probability sample, 5,941 of 190,146 series |
| Comprehensive 3D SR Storage | 5,408 | 5 | complete census |
| Comprehensive SR Storage | 2,118 | 3 | complete census |
| Grayscale Softcopy Presentation State Storage | 1,086 | 2 | complete census |
| Parametric Map Storage | 691 | 1 | complete census |
| Key Object Selection Document Storage | 40 | 1 | complete census |
| Real World Value Mapping Storage | 20 | 1 | complete census |

## Table 2

**Table 2. Three grades, never two, by SOP class, with the ceiling the standard sets.** Two bindings can make an object non-conformant, and the final column reports only the first. **Type 1**, Enhanced General Equipment with Usage M, binds four equipment attributes in the two IODs marked `yes`, where absent and zero length are both violations. **Type 2**, General Equipment with Usage M, binds Manufacturer in all eight, where absent is a violation and zero length is not. That second tier is why Key Object Selection shows 40 non-conformant objects while its Type 1 column reads `no`: its Manufacturer is absent, not merely empty. Percentages sum to 100 up to the rounding shown; the counts partition exactly. Ledger C3T-00, C3T-01, STD-04, STD-08.

| SOP class | objects | pct of denominator | non-conformant | conformant but uninformative | informative | pct non-conf | pct uninformative | pct informative | binds Type 1 | archive pct uninformative if this class is dropped |
|---|---|---|---|---|---|---|---|---|---|---|
| RT Structure Set Storage | 19,358 | 55.14 | 0 | 19,358 | 0 | 0.00 | 100.00 | 0.00 | **no** | 60.62 |
| Segmentation Storage | 6,386 | 18.19 | 1,363 | 3,231 | 1,792 | 21.34 | 50.60 | 28.06 | yes | 89.39 |
| Comprehensive 3D SR Storage | 5,408 | 15.40 | 0 | 4,438 | 970 | 0.00 | 82.06 | 17.94 | **no** | 82.38 |
| Comprehensive SR Storage | 2,118 | 6.03 | 0 | 1,292 | 826 | 0.00 | 61.00 | 39.00 | **no** | 83.70 |
| Grayscale Softcopy Presentation State Storage | 1,086 | 3.09 | 0 | 566 | 520 | 0.00 | 52.12 | 47.88 | **no** | 83.30 |
| Parametric Map Storage | 691 | 1.97 | 0 | 0 | 691 | 0.00 | 0.00 | 100.00 | yes | 83.99 |
| Key Object Selection Document Storage | 40 | 0.11 | 40 | 0 | 0 | 100.00 | 0.00 | 0.00 | **no** | 82.43 |
| Real World Value Mapping Storage | 20 | 0.06 | 0 | 20 | 0 | 0.00 | 100.00 | 0.00 | **no** | 82.32 |

## Table 3

**Table 3. The recoverability ladder: the first carrier level at which producer identity appears, per analysis result.** Levels: 1 equipment attributes, 2 file meta, 3 SeriesDescription and ContentCreatorName, 4 in-object algorithm carriers, 5 collection metadata and DOI. **Identity appears at no level in 25 of 36 cells.** A version accompanies it in 4. `(null)` is not an analysis result: it is the residual cell of every object in its class that the archive index gives no `analysis_result_id`, so it is one bucket rather than one producer and is not homogeneous in producer the way a named cell is. There are 6 such cells holding 5,731 objects, 16.32 percent of the denominator, and 4 of them sit inside the 25. Excluding them the ladder reads 21 of 30, which is the sensitivity in Results 3.2.1c; the headline is the full 25 of 36. This is the headline unit because the analysis-result cells are complete for the seven censused classes and immune to the concentration that distorts every object-weighted rate in this study; for Segmentation they are the identifiers observed in the PRE-06 sample. Ledger C3T-03, C3T-12.

| SOP class | analysis_result_id | objects | first level | all levels where identity appears | identifying value at the first | version | version value | in the object |
|---|---|---|---|---|---|---|---|---|
| Comprehensive 3D SR Storage | nlst_sybil | 970 | 1 | 1 | Sybil | no | none | yes |
| Parametric Map Storage | tcga_gbm360 | 691 | 1 | 1, 4, 5 | GBM360 | no | none | yes |
| Grayscale Softcopy Presentation State Storage | qiba_volct_1b | 624 | 1 | 1 | DIRS2 | yes | 2.3 | yes |
| Comprehensive SR Storage | (null) | 462 | 1 | 1 | DIRS2 | no | none | yes |
| Segmentation Storage | qiba_volct_1b | 384 | 1 | 1 | DIRS2 | yes | 2.3 | yes |
| Comprehensive SR Storage | qiba_volct_1b | 364 | 1 | 1 | LocationDesignatorSynthesizer | yes | 2.3 | yes |
| Segmentation Storage | pan_cancer_nuclei_seg_dicom | 356 | 1 | 1, 4 | Pan-Cancer-Nuclei-Seg | no | none | yes |
| Segmentation Storage | rms_mutation_prediction_expert_annotations | 261 | 1 | 1, 4 | FNLCR_IVG_RMS_iou_0.7343_0.7175_epoch_60 | no | none | yes |
| Segmentation Storage | nnu_net_bpr_annotations | 384 | 3 | 3, 4 | 3d_lowres-tta_nnU-Net_Segmentation | no | none | yes |
| Segmentation Storage | totalsegmentator_ct_segmentations | 384 | 3 | 3, 4, 5 | TotalSegmentator(v1.5.6) Segmentation of Series 5 | yes | v1.5.6 | yes |
| Segmentation Storage | (null) | 1,632 | 4 | 4 | nnUNet | no | none | yes |
| RT Structure Set Storage | eay131_tumor_annotations | 14,395 | none | none | no value at any level | no | none | not applicable, identity appears nowhere |
| RT Structure Set Storage | (null) | 3,115 | none | none | no value at any level | no | none | not applicable, identity appears nowhere |
| Comprehensive 3D SR Storage | nnu_net_bpr_annotations | 2,906 | none | none | no value at any level | no | none | not applicable, identity appears nowhere |
| Comprehensive SR Storage | dicom_sr_breast_clinical | 1,292 | none | none | no value at any level | no | none | not applicable, identity appears nowhere |
| Comprehensive 3D SR Storage | lung_pet_ct_dx_annotations | 1,091 | none | none | no value at any level | no | none | not applicable, identity appears nowhere |
| RT Structure Set Storage | cptac_ccrcc_tumor_annotations | 636 | none | none | no value at any level | no | none | not applicable, identity appears nowhere |
| RT Structure Set Storage | cptac_ucec_tumor_annotations | 617 | none | none | no value at any level | no | none | not applicable, identity appears nowhere |
| RT Structure Set Storage | cptac_pda_tumor_annotations | 536 | none | none | no value at any level | no | none | not applicable, identity appears nowhere |
| Grayscale Softcopy Presentation State Storage | (null) | 462 | none | none | no value at any level | no | none | not applicable, identity appears nowhere |
| Segmentation Storage | bamf_aimi_annotations | 384 | none | none | no value at any level | no | none | not applicable, identity appears nowhere |
| Segmentation Storage | dicom_lidc_idri_nodules | 384 | none | none | no value at any level | no | none | not applicable, identity appears nowhere |
| Segmentation Storage | eay131_tumor_annotations | 384 | none | none | no value at any level | no | none | not applicable, identity appears nowhere |
| Segmentation Storage | nlstseg | 384 | none | none | no value at any level | no | none | not applicable, identity appears nowhere |
| Segmentation Storage | prostate_mri_us_biopsy_dicom_annotations | 384 | none | none | no value at any level | no | none | not applicable, identity appears nowhere |
| Segmentation Storage | tcga_sbu_til_maps | 384 | none | none | no value at any level | no | none | not applicable, identity appears nowhere |
| Segmentation Storage | qin_lungct_seg | 378 | none | none | no value at any level | no | none | not applicable, identity appears nowhere |
| Comprehensive 3D SR Storage | prostatex_targets | 345 | none | none | no value at any level | no | none | not applicable, identity appears nowhere |
| Segmentation Storage | prostatex_seg_zones | 98 | none | none | no value at any level | no | none | not applicable, identity appears nowhere |
| Comprehensive 3D SR Storage | rms_mutation_prediction_expert_annotations | 96 | none | none | no value at any level | no | none | not applicable, identity appears nowhere |
| Segmentation Storage | pancreas_ct_seg | 80 | none | none | no value at any level | no | none | not applicable, identity appears nowhere |
| Segmentation Storage | prostatex_seg_hires | 66 | none | none | no value at any level | no | none | not applicable, identity appears nowhere |
| RT Structure Set Storage | rider_lungct_seg | 59 | none | none | no value at any level | no | none | not applicable, identity appears nowhere |
| Segmentation Storage | rider_lungct_seg | 59 | none | none | no value at any level | no | none | not applicable, identity appears nowhere |
| Key Object Selection Document Storage | (null) | 40 | none | none | no value at any level | no | none | not applicable, identity appears nowhere |
| Real World Value Mapping Storage | (null) | 20 | none | none | no value at any level | no | none | not applicable, identity appears nowhere |

## Table 4

**Table 4. The mechanism: both writers record the serialiser precisely and neither records the producer, but they do it differently.** dcmqi's equipment attributes are hardcoded at compile time, so no caller can place a producing algorithm in them; the field is structurally incapable of carrying the thing an audit looks for. highdicom is not: it writes its own release to ImplementationVersionName, six distinct releases being present in the corpus, and leaves SoftwareVersions to the caller. Of 7,100 highdicom-written objects the caller fills it with a conversion-pipeline repository URL on 1,788 (Comprehensive 3D SR Storage 96; Parametric Map Storage 691; Segmentation Storage 1,001) and leaves it empty on 5,312, every one of those being a Comprehensive 3D SR, where SoftwareVersions is Type 3 rather than the Type 1 it is under Enhanced General Equipment. **Where the standard compels a non-empty value the caller supplies one and it names a conversion pipeline; where it does not, the caller supplies nothing.** One toolkit forecloses the slot; the other leaves it open and the caller does not use it for the producer. Repository class of the dcmqi SHAs resolves offline: named fork, fedorov 8 objects; not a dcmqi repository URL 12 objects; orphaned, no repository named 20 objects; upstream, QIICR/dcmqi 2,983 objects. Commit date and nearest tag require the upstream history and are unresolved. Ledger C3-11, P2P-05, P2P-09, C3T-06, DEV-02.

| writer | ManufacturerModelName carries | SoftwareVersions carries | set at | can a caller place the producing algorithm here | distinct identifiers in the corpus |
|---|---|---|---|---|---|
| dcmqi | the git remote URL of the working copy that built the binary | the abbreviated HEAD SHA of that working copy | compile time, from QIICRConstants.h | **no** | 22 distinct 7-character SHAs over 3,023 objects |
| highdicom | the library name | nothing of its own: the value is the caller's. In this corpus 1,788 of 7,100 highdicom-written objects carry a conversion-pipeline repository URL there rather than a release, and the other 5,312 carry nothing at all | the release goes to ImplementationVersionName at import time; SoftwareVersions is left to the caller | **no** | 6 distinct releases: highdicom0.20.0, highdicom0.21.1, highdicom0.22.0, highdicom0.23.0, highdicom0.26.1, highdicom0.27.0 |

## Table 5

**Table 5. Floors are per-writer, not per-standard, and the residue is the stable quantity.** Two conformant writers given byte-identical content draw different validator messages, so a floor measured on one does not transfer to the other. The Jaccard is the wrong statistic because it is unstable under one validator and stable under the other: it oscillates between 0.00 and 0.86 under dciodvfy with no trend, and sits between 0.86 and 0.88 under dicom-validator throughout. Its value depends on which tool is asked. The residue, the number of message classes held by one writer only, is 1 at every rung under both validators except V9 under dciodvfy, where it is 2 because the pinned build cannot read the deflated transfer syntax and the rung is adjudicated UNDECIDABLE. Ledger F1-01, F1-03, B-02, B-03, B-05, B-10.

| quantity | baseline | across the nine variant rungs | stable |
|---|---|---|---|
| Jaccard between the two writers' floor sets, SEG BINARY, dciodvfy | 0.0000 | oscillates 0.0000 to 0.8571, no trend | **no** |
| Jaccard, SEG BINARY, dicom-validator | 0.8571 | 0.8571 to 0.8750 | yes, but at a different value from dciodvfy |
| residue: message classes held by one writer only, dciodvfy | 1 | 1 at eight rungs, 2 at V9 | **yes, except V9** |
| residue, dicom-validator | 1 | 1 at all nine | **yes** |

## Table 6

**Table 6. Claim 1: net conformance by class, under each adjudication pass and under the two-pass consensus.** A message class counts toward the numerator only where both passes independently called it net; every disagreement drops to UNDECIDABLE and is excluded, so the consensus column can only move down and is a lower bound. The consensus rate is identical to the first pass in all six classes. Segmentation is absent because its message classes are reported gross and have not been adjudicated. Ledger ADJ2-01, ADJ2-02, ADJ2-03, C-C3D-06, C-C3D-08, PRE-05.

| SOP class | objects | collections | net pass 1 | pct | net pass 2 | pct | net consensus | pct |
|---|---|---|---|---|---|---|---|---|
| Comprehensive 3D SR Storage | 5,408 | 5 | 1,801 | 33.30 | 1,801 | 33.30 | 1,801 | 33.30 |
| Comprehensive SR Storage | 2,118 | 7 | 723 | 34.14 | 723 | 34.14 | 723 | 34.14 |
| Grayscale Softcopy Presentation State Storage | 1,086 | 3 | 0 | 0.00 | 0 | 0.00 | 0 | 0.00 |
| Parametric Map Storage | 691 | 1 | 0 | 0.00 | 0 | 0.00 | 0 | 0.00 |
| Key Object Selection Document Storage | 40 | 1 | 40 | 100.00 | 40 | 100.00 | 40 | 100.00 |
| Real World Value Mapping Storage | 20 | 1 | 0 | 0.00 | 0 | 0.00 | 0 | 0.00 |
