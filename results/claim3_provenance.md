# Claim 3: producer identification in IDC v24 derived objects

Population: **481,750 derived series**, the nine SOP classes defined in
`colophon/index.py`. Zero bytes downloaded. Reproduce with `python -m colophon.provenance`.

## What this settles and what it does not

The claim names five provenance carriers. Two are index columns and are settled
here across the entire population. Three are not in the index and require the
objects themselves, so they are logged as pending rather than dropped.

| carrier | tag | in index | status |
|---|---|---|---|
| Manufacturer | (0008,0070) | yes | measured, whole population |
| ManufacturerModelName | (0008,1090) | yes | measured, whole population |
| ImplementationVersionName | (0002,0013) | no | pending, needs file meta, Phase 2 and 3 |
| ContributingEquipmentSequence | (0018,A001) | no | pending, needs dataset read, Phase 2 and 3 |
| SegmentAlgorithmType | (0062,0008) | no | pending, SEG only, Phase 2 and 3 |
| SegmentAlgorithmName | (0062,0009) | no | pending, SEG only, Phase 2 and 3 |
| ContentCreatorName | (0070,0084) | no | pending, Phase 2 and 3 |
| AlgorithmIdentificationSequence | Algorithm Identification Macro | no | pending, Phase 2 and 3 |
| SR TID 4019 algorithm identification | template | no | pending, SR only, Phase 2 and 3 |

The last five are not in the brief's list of five carriers. They are added
because the published IDC AI-annotation dataset descriptors record producer
information in them, so scoring only the brief's five would report an absence
that the objects may not have. The primary measure stays the four named
equipment attributes. A secondary measure, attribution present anywhere, runs
over the alternative locations, and both numbers go in the manuscript.

IHE Radiology Technical Framework Supplement, AI Results, section 6.5.3.1
requires AI algorithm identification in ContributingEquipmentSequence, with the
Algorithm Identification Macro as the alternative. That is a published,
versioned, citable requirement, and it is the yardstick this claim is measured
against. Without it the claim is a generic complaint about metadata
completeness.

## Population rates

Both attributes are populated on almost every derived series, so the finding is
not absence. It is what the populated values name.

By SOP class, Manufacturer:

| sop_class_name | series | null | empty | populated | pct_populated | distinct_values |
|---|---|---|---|---|---|---|
| Enhanced SR Storage | 262,883 | 0 | 0 | 262,883 | 100.000 | 1 |
| Segmentation Storage | 190,146 | 0 | 0 | 190,146 | 100.000 | 15 |
| RT Structure Set Storage | 19,358 | 275 | 0 | 19,083 | 98.580 | 7 |
| Comprehensive 3D SR Storage | 5,408 | 0 | 0 | 5,408 | 100.000 | 4 |
| Comprehensive SR Storage | 2,118 | 0 | 0 | 2,118 | 100.000 | 3 |
| Grayscale Softcopy Presentation State Storage | 1,086 | 104 | 0 | 982 | 90.420 | 5 |
| Parametric Map Storage | 691 | 0 | 0 | 691 | 100.000 | 1 |
| Key Object Selection Document Storage | 40 | 40 | 0 | 0 | 0.000 | 0 |
| Real World Value Mapping Storage | 20 | 0 | 0 | 20 | 100.000 | 1 |

By SOP class, ManufacturerModelName:

| sop_class_name | series | null | empty | populated | pct_populated | distinct_values |
|---|---|---|---|---|---|---|
| Enhanced SR Storage | 262,883 | 0 | 0 | 262,883 | 100.000 | 3 |
| Segmentation Storage | 190,146 | 0 | 0 | 190,146 | 100.000 | 44 |
| RT Structure Set Storage | 19,358 | 0 | 0 | 19,358 | 100.000 | 9 |
| Comprehensive 3D SR Storage | 5,408 | 5,312 | 0 | 96 | 1.780 | 1 |
| Comprehensive SR Storage | 2,118 | 0 | 0 | 2,118 | 100.000 | 3 |
| Grayscale Softcopy Presentation State Storage | 1,086 | 566 | 0 | 520 | 47.880 | 1 |
| Parametric Map Storage | 691 | 0 | 0 | 691 | 100.000 | 1 |
| Key Object Selection Document Storage | 40 | 40 | 0 | 0 | 0.000 | 0 |
| Real World Value Mapping Storage | 20 | 20 | 0 | 0 | 0.000 | 0 |

No derived series in the archive carries a zero length string in either
attribute. Where a value is missing it is absent from the index entirely, which
is a different failure mode from the zero length value that spine-gsps found
draws a worse validator diagnostic than absence.

## What the populated values name

Four buckets, exhaustive and mutually exclusive, summing to the population. The
rules are in `colophon/provenance.py` as plain substrings over the lowercased
value, so any single assignment can be checked by eye. The buckets describe what
kind of entity a declared pair names. They do not say whether naming it is
correct.

Exhaustiveness is the point. Reporting an encoder share against a named-model
share leaves a residual, and the residual here contains the counter-example that
changes the finding.

| label | series | pct | distinct_pairs |
|---|---|---|---|
| encoding library only | 416,427 | 86.440 | 11 |
| producing entity and converter both named | 21,721 | 4.510 | 3 |
| other: named model, scanner, planning system or viewer | 37,454 | 7.770 | 42 |
| absent or NA | 6,148 | 1.280 | 1 |

**86.44 percent of derived series declare a general purpose DICOM encoding library and nothing else.** The library can encode any analysis, so it identifies none. But 4.51 percent name the producing entity, the producing model and the converter together, which is the case that makes the finding a conflict of conventions rather than an absence.

## The counter-example, and why it changes the claim

The second bucket is a positive control. 21,721 series
declare the producing entity, the producing model and the converter, all three,
in the equipment attributes:

| Manufacturer | ManufacturerModelName | series |
|---|---|---|
| Stony Brook University converted by Imaging Data Commons | TIL Inception-V4 2022 converted by Imaging Data Commons | 15,868 |
| Stony Brook University converted by Imaging Data Commons | TIL Custom CNN 2018 converted by Imaging Data Commons | 5,162 |
| Gevaert Lab Converted By Imaging Data Commons | GBM360 | 691 |

IDC already has a working convention for the thing an absence-based reading of
this data would call missing, and applies it to 4.5
percent of its own holdings. So the defensible claim is not that the archive
fails to record producers. It is that several incompatible conventions coexist
in one archive curated by one team, and a consumer cannot tell from the
attributes which convention a given object follows.

Even inside the positive control the convention is not applied consistently: one
analysis result writes "Converted By" and the other writes "converted by".

## The unit of analysis, stated before any rate is read

**Series in this archive are not independent observations.** They are produced
by one pipeline, in one run, under one set of choices, so a series-weighted rate
is a statement about which producer contributed the most objects at least as
much as it is a statement about the archive.

| | |
|---|---|
| derived series | 481,750 |
| collections | 85 |
| analysis results | 24 |
| patients | 46,571 |
| largest collection, `nlst` | 386,226 series, 80.2 percent of the census |

The effective sample size is on the order of the 85 collections,
not the 481,750 series. Every rate in this study is therefore
reported three ways and never one.

**Series-weighted**, over the whole population: 86.4 percent.

**Collection-level**, the collection as the unit: median
0.0 percent, IQR 0.0 to
100.0. The distribution is not centred, it is bimodal:
44 collections sit at 0 percent and
27 sit at 100 percent. A convention is adopted by a
producer and applied to everything that producer emits, so the object is the
wrong unit for asking how common a convention is.

**Leave-one-out sensitivity**:

| collection_id | series_removed | series_remaining | pct_after_removal | shift_from_full |
|---|---|---|---|---|
| nlst | 386,226 | 95,524 | 34.810 | -51.630 |
| eay131 | 15,799 | 465,951 | 89.070 | 2.630 |
| lidc_idri | 13,808 | 467,942 | 86.040 | -0.400 |
| nsclc_radiomics | 4,504 | 477,246 | 86.570 | 0.130 |
| tcga_brca | 4,388 | 477,362 | 87.240 | 0.790 |
| ispy1 | 3,413 | 478,337 | 87.060 | 0.620 |

| analysis_result_id | series_removed | series_remaining | pct_after_removal | shift_from_full |
|---|---|---|---|---|
| totalsegmentator_ct_segmentations | 378,153 | 103,597 | 36.950 | -49.500 |
| tcga_sbu_til_maps | 21,030 | 460,720 | 90.390 | 3.950 |
| (null) | 18,207 | 463,543 | 88.730 | 2.290 |
| eay131_tumor_annotations | 15,799 | 465,951 | 89.070 | 2.630 |

Removing the single collection `nlst` moves the rate from
86.4 percent to
34.81 percent. Removing the single analysis
result `totalsegmentator_ct_segmentations` moves it to
36.95 percent.

**So the series-weighted figure is substantially one analysis result.** It is
reported because it describes the archive as it exists, which is what a consumer
downloads, and it is never reported without the collection-level distribution
and the sensitivity beside it. Percentages are given without decimal places
where no interval justifies the precision.

This is a census of one release of one archive. It licenses no inference beyond
IDC v24, and no claim in this study is stated about DICOM practice in general.

## The competing conventions

| convention | series | pct | analysis_results | example_manufacturer | example_model |
|---|---|---|---|---|---|
| encoding library as manufacturer | 417,623 | 86.690 | 13 | QIICR | git@github.com:QIICR/dcmqi.git |
| producing lab plus model plus converter | 21,721 | 4.510 | 2 | Stony Brook University converted by Imaging Data Commons | TIL Inception-V4 2022 converted by Imaging Data Commons |
| viewer or workstation as manufacturer | 19,153 | 3.980 | 6 | ADAC | Pinnacle3 |
| acquisition equipment as manufacturer | 8,687 | 1.800 | 0 | GE MEDICAL SYSTEMS | Signa HDxt |
| institution as manufacturer, model named | 6,171 | 1.280 | 2 | NCI/FNLCR | FNLCR_IVG_RMS_iou_0.7343_0.7175_epoch_60 |
| manufacturer only, model absent | 5,034 | 1.040 | 3 | QIICR | NA |
| unclassified convention | 2,247 | 0.470 | 1 | nan | Vision 7.3 - External Beam Planning |
| producing model as manufacturer, model field absent | 970 | 0.200 | 1 | Sybil | nan |
| nothing declared | 144 | 0.030 | 1 | nan | nan |

The scanner case is not identified from a list of vendor names. It is the
measured cross-reference described below, so the archive identifies it rather
than the author.

## One tool, several spellings

The declared encoder strings are not stable. Counting distinct spellings of the
same tool, over series that declare an encoder, a conversion or an application:

| rule | category | distinct_spellings | series |
|---|---|---|---|
| dcmqi | encoder | 6 | 411,865 |
| converted by IDC | conversion | 2 | 21,030 |
| OHIF | application | 1 | 16,184 |
| highdicom | encoder | 3 | 2,097 |
| pydicom-seg | encoder | 1 | 1,991 |
| XSLT | encoder | 1 | 1,292 |
| ARIA | application | 2 | 992 |
| Pinnacle | application | 1 | 800 |
| MIM | application | 1 | 563 |
| GammaPlan | application | 1 | 484 |
| QIICR Reporting | encoder | 1 | 474 |
| plastimatch | encoder | 1 | 1 |

The largest case in full:

    https://github.com/QIICR/dcmqi [380,712]
    https://github.com/QIICR/dcmqi.git [16,668]
    git@github.com:QIICR/dcmqi.git [13,478]
    https://github.com/qiicr/dcmqi.git [720]
    git://github.com/QIICR/dcmqi.git [197]
    https://github.com/fedorov/dcmqi.git [90]

A consumer grouping derived objects by declared model name gets 6 groups where there is one tool.

## Identity inherited from the acquisition

An identity is called inherited when the exact Manufacturer and
ManufacturerModelName pair also appears on an acquired image series, meaning a
series whose SOP class is neither derived nor adjacent. This is measured against
the archive itself, so it needs no list of vendor names and cannot be biased by
which vendors the author thought to include.

A series is eligible only when both attributes are present, because matching on
absence would count a missing identity as an inherited one.

| sop_class_name | series | eligible | inherited_same_collection | pct_of_eligible_same_collection | inherited_anywhere | pct_of_eligible_anywhere |
|---|---|---|---|---|---|---|
| Enhanced SR Storage | 262,883 | 262,883 | 0 | 0.000 | 0 | 0.000 |
| Segmentation Storage | 190,146 | 190,146 | 8,687 | 4.570 | 8,687 | 4.570 |
| RT Structure Set Storage | 19,358 | 19,083 | 1,284 | 6.730 | 1,804 | 9.450 |
| Comprehensive 3D SR Storage | 5,408 | 96 | 0 | 0.000 | 0 | 0.000 |
| Comprehensive SR Storage | 2,118 | 2,118 | 0 | 0.000 | 0 | 0.000 |
| Grayscale Softcopy Presentation State Storage | 1,086 | 520 | 0 | 0.000 | 0 | 0.000 |
| Parametric Map Storage | 691 | 691 | 0 | 0.000 | 0 | 0.000 |
| Key Object Selection Document Storage | 40 | 0 | 0 | 0.000 | 0 | 0.000 |
| Real World Value Mapping Storage | 20 | 0 | 0 | 0.000 | 0 | 0.000 |

475,537 of the 481,750 derived series carry both attributes and are eligible for the test. Of those, 9,971, 2.1 percent, declare an identity that also appears on an acquired image series in the same collection. Widening the test to the whole archive gives 10,491, 2.2 percent. Against the full derived population rather than the eligible subset the figures are 2.1 and 2.2 percent.

For those series the equipment identity describes the scanner that produced the
images the result was computed from, not anything that produced the result.

## Declared identity against attributed analysis

`analysis_result_id` is IDC's own record of which analysis a series came from.
Testing whether the declared equipment strings share any distinctive token with
that identifier, for analysis results of at least 100 series:

| analysis_result_id | series | pct_match | top_Manufacturer | top_ManufacturerModelName |
|---|---|---|---|---|
| totalsegmentator_ct_segmentations | 378,153 | 0.000 | QIICR [378,153] | https://github.com/QIICR/dcmqi [378,153] |
| tcga_sbu_til_maps | 21,030 | 100.000 | Stony Brook University converted by Imaging Data Commons [21,030] | TIL Inception-V4 2022 converted by Imaging Data Commons [15,868]; TIL Custom CNN 2018 converted by Imaging Data Commons [5,162] |
| eay131_tumor_annotations | 15,799 | 0.000 | Open Health Imaging Foundation [14,395]; highdicom [1,404] | OHIF-XNAT Viewer 3.2.0 [14,395]; https://github.com/ImagingDataCommons/highdicom.git [1,404] |
| dicom_lidc_idri_nodules | 13,718 | 0.000 | QIICR [13,718] | https://github.com/QIICR/dcmqi.git [13,718] |
| bamf_aimi_annotations | 8,202 | 0.000 | QIICR [8,202] | git@github.com:QIICR/dcmqi.git [8,202] |
| nnu_net_bpr_annotations | 7,817 | 0.000 | QIICR [4,911]; IDC [2,906] | git@github.com:QIICR/dcmqi.git [4,911]; (null) [2,906] |
| pan_cancer_nuclei_seg_dicom | 6,074 | 100.000 | Stony Brook University [6,074] | Pan-Cancer-Nuclei-Seg [6,074] |
| prostate_mri_us_biopsy_dicom_annotations | 2,328 | 0.000 | QIICR [2,328] | https://github.com/QIICR/dcmqi.git [2,328] |
| nlstseg | 1,803 | 0.000 | QIICR [1,803] | https://github.com/QIICR/dcmqi [1,803] |
| qiba_volct_1b | 1,508 | 0.000 | Siemens Corporate Research [1,300]; (null) [104] | DIRS2 [1,300]; (null) [104] |
| dicom_sr_breast_clinical | 1,292 | 0.000 | PixelMed [1,292] | XSLT from di3data csv extract [1,292] |
| lung_pet_ct_dx_annotations | 1,091 | 0.000 | Expert annotation from TCIA [1,091] | (null) [1,091] |
| nlst_sybil | 970 | 100.000 | Sybil [970] | (null) [970] |
| tcga_gbm360 | 691 | 100.000 | Gevaert Lab Converted By Imaging Data Commons [691] | GBM360 [691] |
| cptac_ccrcc_tumor_annotations | 636 | 0.000 | Open Health Imaging Foundation [636] | OHIF-XNAT Viewer 3.2.0 [636] |
| cptac_ucec_tumor_annotations | 617 | 0.000 | Open Health Imaging Foundation [617] | OHIF-XNAT Viewer 3.2.0 [617] |
| cptac_pda_tumor_annotations | 536 | 0.000 | Open Health Imaging Foundation [536] | OHIF-XNAT Viewer 3.2.0 [536] |
| qin_lungct_seg | 378 | 0.000 | 3D Slicer Community [378] | https://github.com/fedorov/Reporting [378] |
| prostatex_targets | 345 | 0.000 | IDC [345] | (null) [345] |
| rms_mutation_prediction_expert_annotations | 193 | 50.260 | NCI/FNLCR [97]; Leica Biosystems [96] | FNLCR_IVG_RMS_iou_0.7343_0.7175_epoch_60 [97]; Aperio ImageScope converted with highdicom [96] |
| rider_lungct_seg | 118 | 0.000 | Varian Medical Systems [59]; QIICR [59] | ARIA RadOnc [59]; git@github.com:QIICR/dcmqi.git [59] |

434,341 series across 16 analysis results of at least 100 series share no distinctive token between the analysis IDC attributes them to and the equipment identity they declare. The unattributed group, where analysis_result_id is itself null, is excluded from that tally.

## The interpretation this measurement does not make

PS3.3 C.7.5.1 defines Manufacturer as the manufacturer of the equipment that
produced the composite instances, and ManufacturerModelName as that equipment's
model name. Conversion software is defensibly the equipment that produced a
converted instance, so declaring the encoder is a defensible reading of the
attribute. The attribute the standard provides for recording equipment that
contributed to an instance without being the creating equipment is
ContributingEquipmentSequence (0018,A001), and that attribute is not in the
index.

So this phase establishes the rates and the ambiguity. Whether the analysis that
computed a result is recorded anywhere in these objects is a question about
ContributingEquipmentSequence and the algorithm identification macros, and it is
answered by reading the objects, in Phase 2 and Phase 3. This module does not
resolve it and does not score any object as non-conformant.

## A confounder that has to be carried into Phases 2 and 3

TCIA and IDC apply PS3.15 Annex E de-identification profiles on ingest, and
attribute retention varies by profile and by submitting site. An absent
Manufacturer can mean the producer never wrote one, or that curation removed it.
The index cannot separate those two, because it carries neither
DeidentificationMethod (0012,0063) nor DeidentificationMethodCodeSequence
(0012,0064). Both are recorded per object once files are fetched, and every
attribution rate from Phase 2 onward is stratified by whether a retention
profile was declared. The Phase 0 rates above are therefore upper bounds on
absence attributable to producers.

The population rates here are high enough that this confounder does not touch
the headline: the finding is not that the attributes are missing, it is what the
present values name.

## What was dropped

Nothing. All 481,750 derived series were classified. Values matching no rule
are reported in the `unclassified` category rather than discarded, and every
distinct value with its count is in `results/phase0/provenance_values.csv`.
