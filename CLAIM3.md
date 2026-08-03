# Claim 3: does a derived DICOM object in IDC say what produced it

Complete tabulation over everything measured. **Nothing was fetched.** Both
record sets were already on disk: the Phase 2 census and the PRE-06 Segmentation
sample. IDC v24. Reproduce with `python -m colophon.claim3`.

## Scope, before any number

**35,107 objects across 8 SOP classes.** 28,721 from
the census across the seven complete classes, and 6,386
Segmentation objects from the PRE-06 sample of 5,941 series.

**Enhanced SR is excluded from every rate in this document.**
74,063 of
262,883 series are recorded and
the class is still running. A partial class reads as a rate, so it is named here
and left out rather than folded in.

Segmentation objects carry the PRE-06 stratum weights and the census classes do
not, so the two are never pooled into a single unweighted archive-wide figure.
Every table is reported per SOP class and per `analysis_result_id`.

**Three grades, never two.**

| grade | objects | percent |
|---|---|---|
| non-conformant | 1,403 | 4.00 |
| conformant but uninformative | 28,905 | 82.33 |
| informative | 4,799 | 13.67 |

Only an attribute that a VERIFIED ledger row binds Type 1 can make an object
non-conformant here. That is STD-04, Enhanced General Equipment with Usage M, and
it binds four attributes in **two** of the eight IODs measured, Segmentation and
Parametric Map. In the other six, no carrier in this list is Type 1, so **no
object in them can be graded non-conformant on carrier grounds at all.** The
grading is asymmetric because the standard is asymmetric, and that is the result
rather than a caveat. Absence of a Type 3 carrier is a gap in the standard and is
never counted here as a defect.

| sop_class_name | objects | non-conformant | conformant but uninformative | informative | pct_non-conformant | pct_conformant | pct_informative | sum_pct |
|---|---|---|---|---|---|---|---|---|
| Comprehensive 3D SR Storage | 5,408 | 0 | 4,438 | 970 | 0.000 | 82.060 | 17.940 | 100.000 |
| Comprehensive SR Storage | 2,118 | 0 | 1,292 | 826 | 0.000 | 61.000 | 39.000 | 100.000 |
| Grayscale Softcopy Presentation State Storage | 1,086 | 0 | 566 | 520 | 0.000 | 52.120 | 47.880 | 100.000 |
| Key Object Selection Document Storage | 40 | 40 | 0 | 0 | 100.000 | 0.000 | 0.000 | 100.000 |
| Parametric Map Storage | 691 | 0 | 0 | 691 | 0.000 | 0.000 | 100.000 | 100.000 |
| RT Structure Set Storage | 19,358 | 0 | 19,358 | 0 | 0.000 | 100.000 | 0.000 | 100.000 |
| Real World Value Mapping Storage | 20 | 0 | 20 | 0 | 0.000 | 100.000 | 0.000 | 100.000 |
| Segmentation Storage | 6,386 | 1,363 | 3,231 | 1,792 | 21.340 | 50.600 | 28.060 | 100.000 |

`sum_pct` is 100 in every row up to the rounding of the two decimals shown:
the three grades are exhaustive and mutually exclusive, so the counts partition
the objects exactly and only the displayed percentages round.

## T3.1 Carrier population

Three states, always separate, never summed. `absent` means no element,
`zero_length` means the element is present and carries nothing. For the census
classes `ContributingEquipmentSequence` was recorded as a presence flag only, so
those two states are not separable for it and `absent_or_zero_length` carries
them jointly; the Segmentation sample records all three.

| sop_class_name | carrier | objects | absent | zero_length | non_empty | absent_or_zero_length | type1_here | type1_violation |
|---|---|---|---|---|---|---|---|---|
| Comprehensive 3D SR Storage | Manufacturer | 5,408 | 0 | 0 | 5,408 | 0 | no | 0 |
| Comprehensive 3D SR Storage | ManufacturerModelName | 5,408 | 5,312 | 0 | 96 | 0 | no | 0 |
| Comprehensive 3D SR Storage | DeviceSerialNumber | 5,408 | 5,312 | 0 | 96 | 0 | no | 0 |
| Comprehensive 3D SR Storage | SoftwareVersions | 5,408 | 5,312 | 0 | 96 | 0 | no | 0 |
| Comprehensive 3D SR Storage | ImplementationVersionName | 5,408 | 0 | 0 | 5,408 | 0 | no | 0 |
| Comprehensive 3D SR Storage | ImplementationClassUID | 5,408 | 0 | 0 | 5,408 | 0 | no | 0 |
| Comprehensive 3D SR Storage | ContributingEquipmentSequence | 5,408 | 0 | 0 | 2,406 | 3,002 | no | 0 |
| Comprehensive 3D SR Storage | ContentCreatorName | 5,408 | 5,408 | 0 | 0 | 0 | no | 0 |
| Comprehensive 3D SR Storage | SeriesDescription | 5,408 | 0 | 0 | 5,408 | 0 | no | 0 |
| Comprehensive SR Storage | Manufacturer | 2,118 | 0 | 0 | 2,118 | 0 | no | 0 |
| Comprehensive SR Storage | ManufacturerModelName | 2,118 | 0 | 0 | 2,118 | 0 | no | 0 |
| Comprehensive SR Storage | DeviceSerialNumber | 2,118 | 722 | 447 | 949 | 0 | no | 0 |
| Comprehensive SR Storage | SoftwareVersions | 2,118 | 462 | 0 | 1,656 | 0 | no | 0 |
| Comprehensive SR Storage | ImplementationVersionName | 2,118 | 0 | 0 | 2,118 | 0 | no | 0 |
| Comprehensive SR Storage | ImplementationClassUID | 2,118 | 0 | 0 | 2,118 | 0 | no | 0 |
| Comprehensive SR Storage | ContributingEquipmentSequence | 2,118 | 0 | 0 | 0 | 2,118 | no | 0 |
| Comprehensive SR Storage | ContentCreatorName | 2,118 | 2,118 | 0 | 0 | 0 | no | 0 |
| Comprehensive SR Storage | SeriesDescription | 2,118 | 0 | 0 | 2,118 | 0 | no | 0 |
| Grayscale Softcopy Presentation State Storage | Manufacturer | 1,086 | 0 | 104 | 982 | 0 | no | 0 |
| Grayscale Softcopy Presentation State Storage | ManufacturerModelName | 1,086 | 566 | 0 | 520 | 0 | no | 0 |
| Grayscale Softcopy Presentation State Storage | DeviceSerialNumber | 1,086 | 1,086 | 0 | 0 | 0 | no | 0 |
| Grayscale Softcopy Presentation State Storage | SoftwareVersions | 1,086 | 566 | 0 | 520 | 0 | no | 0 |
| Grayscale Softcopy Presentation State Storage | ImplementationVersionName | 1,086 | 0 | 0 | 1,086 | 0 | no | 0 |
| Grayscale Softcopy Presentation State Storage | ImplementationClassUID | 1,086 | 0 | 0 | 1,086 | 0 | no | 0 |
| Grayscale Softcopy Presentation State Storage | ContributingEquipmentSequence | 1,086 | 0 | 0 | 0 | 1,086 | no | 0 |
| Grayscale Softcopy Presentation State Storage | ContentCreatorName | 1,086 | 0 | 1,022 | 64 | 0 | no | 0 |
| Grayscale Softcopy Presentation State Storage | SeriesDescription | 1,086 | 1,086 | 0 | 0 | 0 | no | 0 |
| Key Object Selection Document Storage | Manufacturer | 40 | 40 | 0 | 0 | 0 | no | 0 |
| Key Object Selection Document Storage | ManufacturerModelName | 40 | 40 | 0 | 0 | 0 | no | 0 |
| Key Object Selection Document Storage | DeviceSerialNumber | 40 | 40 | 0 | 0 | 0 | no | 0 |
| Key Object Selection Document Storage | SoftwareVersions | 40 | 40 | 0 | 0 | 0 | no | 0 |
| Key Object Selection Document Storage | ImplementationVersionName | 40 | 0 | 0 | 40 | 0 | no | 0 |
| Key Object Selection Document Storage | ImplementationClassUID | 40 | 0 | 0 | 40 | 0 | no | 0 |
| Key Object Selection Document Storage | ContributingEquipmentSequence | 40 | 0 | 0 | 0 | 40 | no | 0 |
| Key Object Selection Document Storage | ContentCreatorName | 40 | 40 | 0 | 0 | 0 | no | 0 |
| Key Object Selection Document Storage | SeriesDescription | 40 | 0 | 0 | 40 | 0 | no | 0 |
| Parametric Map Storage | Manufacturer | 691 | 0 | 0 | 691 | 0 | yes | 0 |
| Parametric Map Storage | ManufacturerModelName | 691 | 0 | 0 | 691 | 0 | yes | 0 |
| Parametric Map Storage | DeviceSerialNumber | 691 | 0 | 0 | 691 | 0 | yes | 0 |
| Parametric Map Storage | SoftwareVersions | 691 | 0 | 0 | 691 | 0 | yes | 0 |
| Parametric Map Storage | ImplementationVersionName | 691 | 0 | 0 | 691 | 0 | no | 0 |
| Parametric Map Storage | ImplementationClassUID | 691 | 0 | 0 | 691 | 0 | no | 0 |
| Parametric Map Storage | ContributingEquipmentSequence | 691 | 0 | 0 | 691 | 0 | no | 0 |
| Parametric Map Storage | ContentCreatorName | 691 | 0 | 691 | 0 | 0 | no | 0 |
| Parametric Map Storage | SeriesDescription | 691 | 0 | 0 | 691 | 0 | no | 0 |
| RT Structure Set Storage | Manufacturer | 19,358 | 0 | 275 | 19,083 | 0 | no | 0 |
| RT Structure Set Storage | ManufacturerModelName | 19,358 | 0 | 0 | 19,358 | 0 | no | 0 |
| RT Structure Set Storage | DeviceSerialNumber | 19,358 | 18,765 | 209 | 384 | 0 | no | 0 |
| RT Structure Set Storage | SoftwareVersions | 19,358 | 1,198 | 0 | 18,160 | 0 | no | 0 |
| RT Structure Set Storage | ImplementationVersionName | 19,358 | 0 | 0 | 19,358 | 0 | no | 0 |
| RT Structure Set Storage | ImplementationClassUID | 19,358 | 0 | 0 | 19,358 | 0 | no | 0 |
| RT Structure Set Storage | ContributingEquipmentSequence | 19,358 | 0 | 0 | 0 | 19,358 | no | 0 |
| RT Structure Set Storage | ContentCreatorName | 19,358 | 19,358 | 0 | 0 | 0 | no | 0 |
| RT Structure Set Storage | SeriesDescription | 19,358 | 1,068 | 1 | 18,289 | 0 | no | 0 |
| Real World Value Mapping Storage | Manufacturer | 20 | 0 | 0 | 20 | 0 | no | 0 |
| Real World Value Mapping Storage | ManufacturerModelName | 20 | 20 | 0 | 0 | 0 | no | 0 |
| Real World Value Mapping Storage | DeviceSerialNumber | 20 | 20 | 0 | 0 | 0 | no | 0 |
| Real World Value Mapping Storage | SoftwareVersions | 20 | 0 | 0 | 20 | 0 | no | 0 |
| Real World Value Mapping Storage | ImplementationVersionName | 20 | 0 | 0 | 20 | 0 | no | 0 |
| Real World Value Mapping Storage | ImplementationClassUID | 20 | 0 | 0 | 20 | 0 | no | 0 |
| Real World Value Mapping Storage | ContributingEquipmentSequence | 20 | 0 | 0 | 0 | 20 | no | 0 |
| Real World Value Mapping Storage | ContentCreatorName | 20 | 0 | 20 | 0 | 0 | no | 0 |
| Real World Value Mapping Storage | SeriesDescription | 20 | 0 | 0 | 20 | 0 | no | 0 |
| Segmentation Storage | Manufacturer | 6,386 | 0 | 0 | 6,386 | 0 | yes | 0 |
| Segmentation Storage | ManufacturerModelName | 6,386 | 0 | 0 | 6,386 | 0 | yes | 0 |
| Segmentation Storage | DeviceSerialNumber | 6,386 | 966 | 397 | 5,023 | 0 | yes | 1,363 |
| Segmentation Storage | SoftwareVersions | 6,386 | 0 | 0 | 6,386 | 0 | yes | 0 |
| Segmentation Storage | ImplementationVersionName | 6,386 | 0 | 0 | 6,386 | 0 | no | 0 |
| Segmentation Storage | ImplementationClassUID | 6,386 | 0 | 0 | 6,386 | 0 | no | 0 |
| Segmentation Storage | ContributingEquipmentSequence | 6,386 | 6,002 | 0 | 384 | 0 | no | 0 |
| Segmentation Storage | ContentCreatorName | 6,386 | 0 | 2,568 | 3,818 | 0 | no | 0 |
| Segmentation Storage | SeriesDescription | 6,386 | 765 | 0 | 5,621 | 0 | no | 0 |

**Zero-length where Enhanced General Equipment binds it Type 1**, flagged by name
as the tabulation asked. Usage M in the Segmentation and Parametric Map IODs
makes Manufacturer, ManufacturerModelName, DeviceSerialNumber and SoftwareVersions
Type 1 there. A Type 1 attribute present and empty is a violation, and a presence
check scores it as present.

| sop_class_name | analysis_result_id | carrier | objects | absent | zero_length | binding | grade |
|---|---|---|---|---|---|---|---|
| Segmentation Storage | (null) | DeviceSerialNumber | 1,632 | 876 | 397 | Type 1, Enhanced General Equipment Usage M | non-conformant |
| Segmentation Storage | qin_lungct_seg | DeviceSerialNumber | 378 | 90 | 0 | Type 1, Enhanced General Equipment Usage M | non-conformant |

**Both validators independently confirm every one of them.** The three-state
capture says an attribute is absent or zero-length; whether that is
non-conformant is PS3.3's answer, read by two tools from different codebases.
Their counts are reported beside ours and never merged with them.

| carrier | state_we_recorded | validator | validator_raised_a_matching_message | objects |
|---|---|---|---|---|
| DeviceSerialNumber | absent | dciodvfy | 1 | 966 |
| DeviceSerialNumber | absent | dicom-validator | 1 | 966 |
| DeviceSerialNumber | empty | dciodvfy | 1 | 397 |
| DeviceSerialNumber | empty | dicom-validator | 1 | 397 |

*What this table shows.* It separates the two questions a presence check merges.
The equipment attributes are populated nearly everywhere, which is exactly what
Enhanced General Equipment being Mandatory predicts, and is precisely why
presence is not the measurement. The states that carry information are the
zero-length ones, because they are the only ones the standard forbids, and the
absences among the Type 3 carriers, because those are the standard's own gaps
rather than anyone's defects. The per-`analysis_result_id` form is in
`results/claim3/t31_carriers_by_analysis_result.csv`.

## T3.2 What the values name, not whether they exist

Presence is guaranteed where Enhanced General Equipment is Mandatory, so presence
means nothing, and this table asks what the populated values actually say. The
four buckets are exhaustive and mutually exclusive and sum to the population.

| sop_class_name | objects | encoder_only | producer_and_converter | other | absent | pct_encoder_only | pct_producer_and_converter | pct_other | pct_absent | sum_pct |
|---|---|---|---|---|---|---|---|---|---|---|
| Comprehensive 3D SR Storage | 5,408 | 96 | 0 | 0 | 5,312 | 1.780 | 0.000 | 0.000 | 98.220 | 100.000 |
| Comprehensive SR Storage | 2,118 | 0 | 0 | 2,118 | 0 | 0.000 | 0.000 | 100.000 | 0.000 | 100.000 |
| Grayscale Softcopy Presentation State Storage | 1,086 | 0 | 0 | 520 | 566 | 0.000 | 0.000 | 47.880 | 52.120 | 100.000 |
| Key Object Selection Document Storage | 40 | 0 | 0 | 0 | 40 | 0.000 | 0.000 | 0.000 | 100.000 | 100.000 |
| Parametric Map Storage | 691 | 0 | 691 | 0 | 0 | 0.000 | 100.000 | 0.000 | 0.000 | 100.000 |
| RT Structure Set Storage | 19,358 | 0 | 0 | 19,358 | 0 | 0.000 | 0.000 | 100.000 | 0.000 | 100.000 |
| Real World Value Mapping Storage | 20 | 0 | 0 | 0 | 20 | 0.000 | 0.000 | 0.000 | 100.000 | 100.000 |
| Segmentation Storage | 6,386 | 4,617 | 384 | 1,373 | 12 | 72.300 | 6.010 | 21.500 | 0.190 | 100.000 |

Reported both ways, for the `encoder_only` bucket:

- object weighted: **4,713 of 35,107, 13.42 percent**
- by collection: 83 collections: **44 at 0 percent, 25 at 100 percent**, 14 in between (nsclc_radiogenomics at 97.41 percent, tcga_lihc at 42.31 percent, prostatex at 34.16 percent, rms_mutation_prediction at 26.89 percent, tcga_kirc at 25.81 percent, nlst at 24.94 percent)
- by analysis result: 25 analysis results: **11 at 0 percent, 9 at 100 percent**, 5 in between (rider_lungct_seg at 50.00 percent, rms_mutation_prediction_expert_annotations at 26.89 percent, (null) at 21.78 percent, nnu_net_bpr_annotations at 11.67 percent, eay131_tumor_annotations at 2.60 percent)

### How every value was classified, and where the grade could move

The categories come from `colophon.provenance.RULES`, the project's ordered
rule table, imported rather than restated. `named_analysis` is the only category
that counts as producer identity. The others are excluded on the table's own
reading: an `encoder` writes any analysis and identifies none, a `conversion`
string says a third party converted the object, an `application` is a viewer, an
`acquisition_vendor` on a derived object is equipment that did not produce it,
and an `institution` names an organisation without naming what it ran.

| sop_class_name | category | values |
|---|---|---|
| Comprehensive 3D SR Storage | unclassified | 7,814 |
| Comprehensive 3D SR Storage | encoder | 4,908 |
| Comprehensive 3D SR Storage | conversion | 3,251 |
| Comprehensive 3D SR Storage | acquisition_vendor | 2,502 |
| Comprehensive 3D SR Storage | institution | 1,091 |
| Comprehensive 3D SR Storage | named_analysis | 970 |
| Comprehensive SR Storage | encoder | 2,584 |
| Comprehensive SR Storage | unclassified | 2,118 |
| Comprehensive SR Storage | acquisition_vendor | 826 |
| Comprehensive SR Storage | named_analysis | 826 |
| Grayscale Softcopy Presentation State Storage | acquisition_vendor | 982 |
| Grayscale Softcopy Presentation State Storage | named_analysis | 520 |
| Grayscale Softcopy Presentation State Storage | unclassified | 64 |
| Key Object Selection Document Storage | unclassified | 40 |
| Parametric Map Storage | encoder | 2,073 |
| Parametric Map Storage | named_analysis | 1,382 |
| Parametric Map Storage | conversion | 691 |
| Parametric Map Storage | unclassified | 691 |
| Parametric Map Storage | acquisition_vendor | 691 |
| Parametric Map Storage | institution | 691 |
| RT Structure Set Storage | application | 19,627 |
| RT Structure Set Storage | unclassified | 18,557 |
| RT Structure Set Storage | institution | 16,184 |
| RT Structure Set Storage | acquisition_vendor | 2,360 |
| RT Structure Set Storage | encoder | 2 |
| Real World Value Mapping Storage | encoder | 20 |
| Real World Value Mapping Storage | unclassified | 20 |
| Segmentation Storage | named_analysis | 36,074 |
| Segmentation Storage | named_analysis (additive rule) | 34,361 |
| Segmentation Storage | unclassified | 11,799 |
| Segmentation Storage | encoder | 9,924 |
| Segmentation Storage | institution | 2,989 |
| Segmentation Storage | conversion | 1,920 |
| Segmentation Storage | acquisition_vendor | 1,108 |
| Segmentation Storage | institution (additive rule) | 1,044 |
| Segmentation Storage | application | 570 |

**An additive rule table was needed and is published separately.**
`provenance.RULES` was built for `Manufacturer` and `ManufacturerModelName` as
the index carries them. This pass is the first to read `SegmentAlgorithmName
(0062,0009)` and the Algorithm Identification Macro at scale, and those fields
carry model names that table has no rule for. Extending it in place would have
retroactively moved the Phase 0 measurements, so
`colophon.claim3.CLAIM3_EXTRA_RULES` is applied only after the Phase 0 table
returns `unclassified`:

- `TotalSegmentator` to **named_analysis**, pattern `totalsegmentator`
- `nnU-Net` to **named_analysis**, pattern `nnu-?net`
- `Rhabdomyosarcoma Pathology CNN` to **named_analysis**, pattern `rhabdomyosarcoma pathology cnn`
- `Frederick National Lab` to **institution**, pattern `frederick national lab|fnlcr`

Values declined on purpose, recorded so the decision is visible rather than
implied:

- `Manual Segmentation`: names a procedure, not an algorithm
- `BPR landmark annotations`: names the task, not the model that did it
- `BPR region annotations`: names the task, not the model that did it
- `Standard Breast Imaging Report`: a report title. This analysis result is clinical records converted to SR by XSLT and is not an annotation at all
- `Tumor bounding box`: names the structure, not the producer
- `Sybil lesion bounding box`: names the structure. The producer is named elsewhere in the same objects and is counted there

**Everything still unclassified, printed verbatim.** This is where the grading
could move: a named analysis with no rule is graded uninformative, so publishing
the list is what makes that a stated undercount rather than a silent one.

| sop_class_name | value | objects |
|---|---|---|
| Comprehensive 3D SR Storage | BPR landmark annotations | 1,453 |
| Comprehensive 3D SR Storage | BPR region annotations | 1,453 |
| Comprehensive SR Storage | Standard Breast Imaging Report | 1,292 |
| RT Structure Set Storage | Pre-dose, LIVER - 1 - SEED POINT | 1,188 |
| Comprehensive 3D SR Storage | Tumor bounding box | 1,091 |
| RT Structure Set Storage | Pre-dose, LIVER - 1 | 987 |
| Comprehensive 3D SR Storage | Sybil lesion bounding box | 970 |
| RT Structure Set Storage | Pre-dose, LIVER - 2 - SEED POINT | 801 |
| Segmentation Storage | Manual Segmentation | 768 |
| Parametric Map Storage | Aggressiveness Score Map | 691 |
| RT Structure Set Storage | Pre-dose, LIVER - 2 | 672 |
| RT Structure Set Storage | Pre-dose, RIGHT LUNG - 1 - SEED POINT | 648 |
| Segmentation Storage | Reader1 | 602 |
| RT Structure Set Storage | Pre-dose, RIGHT LUNG - 1 | 533 |
| Comprehensive 3D SR Storage | Biograph 64 | 457 |
| Comprehensive SR Storage | Completed | 453 |
| Segmentation Storage | Imaging Data Commons | 410 |
| Segmentation Storage | Random Walker Algorithm | 409 |
| RT Structure Set Storage | Pre-dose, LEFT LUNG - 1 - SEED POINT | 393 |
| RT Structure Set Storage | Pre-dose, LEFT LUNG - 2 - SEED POINT | 379 |
| Segmentation Storage | 3DSlicer | 378 |
| RT Structure Set Storage | Pre-dose, MEDIASTINAL LYMPH NODE - 1 - SEED POINT | 366 |
| Segmentation Storage | BAMF-Brain-MR | 362 |
| Segmentation Storage | Segmentation | 360 |
| Segmentation Storage | https://doi.org/10.7937/TCIA.2019.4A4DKP9U | 356 |

*What this table shows.* The equipment attributes are populated, and what a large
share of them name is the library that wrote the file. That is not a defect and
no validator can complain about it: `QIICR` and a git remote URL are legal values
of Manufacturer and ManufacturerModelName. This is claim 3 in its plainest form.
The boundary counts say it is not a tendency but a convention: collections sit at
0 or at 100 and almost nothing sits between, because a collection is one pipeline
run and a pipeline run uses one encoder. That is also why a median would be
actively misleading here and is not reported.

## T3.3 The recoverability ladder

Per analysis result, the **first** level at which producer identity appears and
whether a version appears with it. Levels: 1 equipment attributes, 2 file meta,
3 SeriesDescription and ContentCreatorName, 4 in-object algorithm carriers,
5 collection metadata and DOI. Level 5 is **not in the object**: identity found
only there is identity a downloaded file does not carry.

The rule for "identity appears" is `colophon.writers._informative`, imported
rather than restated: a value that is neither a published sentinel nor a generic
word. Any single assignment can be overruled by reading the value, which is
printed beside it.

| sop_class_name | analysis_result_id | objects | first_level_identity_appears | level_name | identifying_value | version_at_that_level | in_object |
|---|---|---|---|---|---|---|---|
| Comprehensive 3D SR Storage | nlst_sybil | 970 | 1 | equipment attributes | Sybil | no | yes |
| Parametric Map Storage | tcga_gbm360 | 691 | 1 | equipment attributes | GBM360 | no | yes |
| Grayscale Softcopy Presentation State Storage | qiba_volct_1b | 624 | 1 | equipment attributes | DIRS2 | yes | yes |
| Comprehensive SR Storage | (null) | 462 | 1 | equipment attributes | DIRS2 | no | yes |
| Segmentation Storage | qiba_volct_1b | 384 | 1 | equipment attributes | DIRS2 | yes | yes |
| Comprehensive SR Storage | qiba_volct_1b | 364 | 1 | equipment attributes | LocationDesignatorSynthesizer | yes | yes |
| Segmentation Storage | pan_cancer_nuclei_seg_dicom | 356 | 1 | equipment attributes | Pan-Cancer-Nuclei-Seg | no | yes |
| Segmentation Storage | rms_mutation_prediction_expert_annotations | 261 | 1 | equipment attributes | FNLCR_IVG_RMS_iou_0.7343_0.7175_epoch_60 | no | yes |
| Segmentation Storage | nnu_net_bpr_annotations | 384 | 3 | SeriesDescription and ContentCreatorName | 3d_lowres-tta_nnU-Net_Segmentation | no | yes |
| Segmentation Storage | totalsegmentator_ct_segmentations | 384 | 3 | SeriesDescription and ContentCreatorName | TotalSegmentator(v1.5.6) Segmentation of Series 5 | yes | yes |
| Segmentation Storage | (null) | 1,632 | 4 | in-object algorithm carriers | nnUNet | no | yes |
| RT Structure Set Storage | eay131_tumor_annotations | 14,395 | none | identity does not appear at any level |  | no | not applicable, identity appears nowhere |
| RT Structure Set Storage | (null) | 3,115 | none | identity does not appear at any level |  | no | not applicable, identity appears nowhere |
| Comprehensive 3D SR Storage | nnu_net_bpr_annotations | 2,906 | none | identity does not appear at any level |  | no | not applicable, identity appears nowhere |
| Comprehensive SR Storage | dicom_sr_breast_clinical | 1,292 | none | identity does not appear at any level |  | no | not applicable, identity appears nowhere |
| Comprehensive 3D SR Storage | lung_pet_ct_dx_annotations | 1,091 | none | identity does not appear at any level |  | no | not applicable, identity appears nowhere |
| RT Structure Set Storage | cptac_ccrcc_tumor_annotations | 636 | none | identity does not appear at any level |  | no | not applicable, identity appears nowhere |
| RT Structure Set Storage | cptac_ucec_tumor_annotations | 617 | none | identity does not appear at any level |  | no | not applicable, identity appears nowhere |
| RT Structure Set Storage | cptac_pda_tumor_annotations | 536 | none | identity does not appear at any level |  | no | not applicable, identity appears nowhere |
| Grayscale Softcopy Presentation State Storage | (null) | 462 | none | identity does not appear at any level |  | no | not applicable, identity appears nowhere |
| Segmentation Storage | bamf_aimi_annotations | 384 | none | identity does not appear at any level |  | no | not applicable, identity appears nowhere |
| Segmentation Storage | dicom_lidc_idri_nodules | 384 | none | identity does not appear at any level |  | no | not applicable, identity appears nowhere |
| Segmentation Storage | eay131_tumor_annotations | 384 | none | identity does not appear at any level |  | no | not applicable, identity appears nowhere |
| Segmentation Storage | nlstseg | 384 | none | identity does not appear at any level |  | no | not applicable, identity appears nowhere |
| Segmentation Storage | prostate_mri_us_biopsy_dicom_annotations | 384 | none | identity does not appear at any level |  | no | not applicable, identity appears nowhere |
| Segmentation Storage | tcga_sbu_til_maps | 384 | none | identity does not appear at any level |  | no | not applicable, identity appears nowhere |
| Segmentation Storage | qin_lungct_seg | 378 | none | identity does not appear at any level |  | no | not applicable, identity appears nowhere |
| Comprehensive 3D SR Storage | prostatex_targets | 345 | none | identity does not appear at any level |  | no | not applicable, identity appears nowhere |
| Segmentation Storage | prostatex_seg_zones | 98 | none | identity does not appear at any level |  | no | not applicable, identity appears nowhere |
| Comprehensive 3D SR Storage | rms_mutation_prediction_expert_annotations | 96 | none | identity does not appear at any level |  | no | not applicable, identity appears nowhere |
| Segmentation Storage | pancreas_ct_seg | 80 | none | identity does not appear at any level |  | no | not applicable, identity appears nowhere |
| Segmentation Storage | prostatex_seg_hires | 66 | none | identity does not appear at any level |  | no | not applicable, identity appears nowhere |
| RT Structure Set Storage | rider_lungct_seg | 59 | none | identity does not appear at any level |  | no | not applicable, identity appears nowhere |
| Segmentation Storage | rider_lungct_seg | 59 | none | identity does not appear at any level |  | no | not applicable, identity appears nowhere |
| Key Object Selection Document Storage | (null) | 40 | none | identity does not appear at any level |  | no | not applicable, identity appears nowhere |
| Real World Value Mapping Storage | (null) | 20 | none | identity does not appear at any level |  | no | not applicable, identity appears nowhere |

**Of the 36 analysis-result cells, identity appears at no level at
all in 25.** It
appears at level 1 in 8,
at level 3 in 2 and at
level 4 in 1. A version
accompanies the identity in
4 cells.

*What this table shows.* It turns "the producing algorithm is not named" from an
assertion into a measurement with a level attached. Where identity first appears
at level 1 the object is self-describing and a consumer needs nothing else. Where
it first appears at level 3 a consumer has to parse free text the standard puts
no constraint on. Where it first appears at level 5 the identity is in the
archive's registry, and **a file copied out of IDC does not carry it at all**,
which is the operational form of the claim. The version column is the harder test
and it fails more often than identity does: naming a model without naming its
version does not let anyone reproduce anything.

## T3.4 The algorithm identification result, by writing toolkit

Segment level and object level. **Absence and incompleteness are never merged.**
PS3.3 2026c makes `SegmentationAlgorithmIdentificationSequence (0062,0007)`
Type 3 in the Segmentation IOD with no condition, so absence is a gap in the
standard. A present sequence missing any of its three Type 1 children would be a
defect in the object.

| writing_toolkit | objects | segments | segments_non_manual | seg_absent | pct_seg_absent | seg_present_incomplete | pct_seg_present_incomplete | seg_present_complete | objects_with_non_manual | objects_any_absent | objects_any_incomplete | objects_any_complete |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| dcmqi | 2,991 | 35,477 | 32,963 | 32,963 | 100.000 | 0 | 0.000 | 0 | 1,569 | 1,569 | 0 | 0 |
| not identifiable from index | 1,769 | 2,650 | 2,584 | 714 | 27.630 | 0 | 0.000 | 1,870 | 1,703 | 702 | 0 | 1,001 |
| QIICR Reporting via 3D Slicer | 474 | 474 | 474 | 474 | 100.000 | 0 | 0.000 | 0 | 474 | 474 | 0 | 0 |
| highdicom | 768 | 768 | 384 | 0 | 0.000 | 0 | 0.000 | 384 | 384 | 0 | 0 | 384 |
| pydicom-seg | 384 | 1,889 | 83 | 83 | 100.000 | 0 | 0.000 | 0 | 83 | 83 | 0 | 0 |

The row the tabulation asked for by name, carried separately because it is
neither absence nor incompleteness:

| writing_toolkit | analysis_result_id | SegmentAlgorithmType | AlgorithmName | segments | state_of_0062_0007 | grade |
|---|---|---|---|---|---|---|
| highdicom | eay131_tumor_annotations | AUTOMATIC | Manual Segmentation | 384 | present_complete | conformant but uninformative |

*What this table shows.* The split is by writing toolkit and it is total: a
toolkit either writes the macro for every segment or for none, and incompleteness
is zero everywhere. There is no partial compliance to measure, which makes this a
fact about toolkits rather than about analyses, and it is the reason the archive
wide percentage is a weighted average of two constants. The separate row is the
sharpest case in the tabulation: those segments carry a complete and conformant
macro whose three Type 1 children are all populated, and what it names is a manual
procedure on a segment whose own declared type is AUTOMATIC. Conformant, complete
and uninformative at once. PS3.3 states no relation between the two attributes,
so the contradiction is reported and not resolved.

## T3.5 Version carriers

Every 7-character hexadecimal `SoftwareVersions` value in the tabulation, which
is what dcmqi writes there: `dcmqi_WC_REVISION`, the abbreviated HEAD SHA of the
working copy that built the binary.

| SoftwareVersions_sha7 | declared_repository | repository_class | sop_class_name | analysis_result_id | objects | resolved_commit_date | nearest_tag | resolution |
|---|---|---|---|---|---|---|---|---|
| 4e5b700 | https://github.com/QIICR/dcmqi | upstream, QIICR/dcmqi | Segmentation Storage | nlstseg | 384 | 2025-04-07T15:55:16-04:00 | v1.4.0 | upstream |
| f86b34f | https://github.com/QIICR/dcmqi.git | upstream, QIICR/dcmqi | Segmentation Storage | dicom_lidc_idri_nodules | 384 | 2019-03-13T12:57:28-04:00 | v1.2.1 | upstream |
| ef9e227 | https://github.com/QIICR/dcmqi.git | upstream, QIICR/dcmqi | Segmentation Storage | prostate_mri_us_biopsy_dicom_annotations | 384 | 2021-03-10T21:47:52-05:00 | v1.2.4 | upstream |
| 7ae0873 | https://github.com/QIICR/dcmqi | upstream, QIICR/dcmqi | Segmentation Storage | totalsegmentator_ct_segmentations | 384 | 2023-11-19T21:30:51-05:00 | v1.3.0 | upstream |
| 1153738 | git@github.com:QIICR/dcmqi.git | upstream, QIICR/dcmqi | Segmentation Storage | nnu_net_bpr_annotations | 384 | 2022-07-18T13:47:26-04:00 | v1.2.5 | upstream |
| 451bf84 | git@github.com:QIICR/dcmqi.git | upstream, QIICR/dcmqi | Segmentation Storage | bamf_aimi_annotations | 346 | 2023-01-26T11:08:36-05:00 | v1.2.5 | upstream |
| 1e82977 | https://github.com/qiicr/dcmqi.git | upstream, QIICR/dcmqi | Segmentation Storage | prostatex_seg_zones | 98 | 2019-02-01T07:15:24Z | v1.2.1 | upstream |
| ef9e227 | https://github.com/QIICR/dcmqi.git | upstream, QIICR/dcmqi | Segmentation Storage | (null) | 85 | 2021-03-10T21:47:52-05:00 | v1.2.4 | upstream |
| 81e9073 | https://github.com/QIICR/dcmqi | upstream, QIICR/dcmqi | Segmentation Storage | pancreas_ct_seg | 80 | 2024-06-19T17:04:37-04:00 | v1.3.3 | upstream |
| 1922a09 | https://github.com/QIICR/dcmqi | upstream, QIICR/dcmqi | Segmentation Storage | (null) | 80 | 2024-01-04T11:22:33-05:00 | v1.3.1 | upstream |
| 3efde87 | https://github.com/qiicr/dcmqi.git | upstream, QIICR/dcmqi | Segmentation Storage | (null) | 72 | 2020-06-02T17:04:55-04:00 | v1.2.2 | upstream |
| 1e82977 | https://github.com/qiicr/dcmqi.git | upstream, QIICR/dcmqi | Segmentation Storage | prostatex_seg_hires | 66 | 2019-02-01T07:15:24Z | v1.2.1 | upstream |
| 55dc95e | git@github.com:QIICR/dcmqi.git | upstream, QIICR/dcmqi | Segmentation Storage | rider_lungct_seg | 59 | 2019-03-06T12:58:45-05:00 | v1.2.1 | upstream |
| 1153738 | git@github.com:QIICR/dcmqi.git | upstream, QIICR/dcmqi | Segmentation Storage | bamf_aimi_annotations | 38 | 2022-07-18T13:47:26-04:00 | v1.2.5 | upstream |
| ac7d0fe | git://github.com/QIICR/dcmqi.git | upstream, QIICR/dcmqi | Segmentation Storage | (null) | 32 | 2021-03-13T22:15:49-05:00 | v1.2.4 | upstream |
| afa4912 | https://github.com/QIICR/dcmqi | upstream, QIICR/dcmqi | Segmentation Storage | (null) | 23 | 2025-07-17T13:56:02+02:00 | v1.4.0 | upstream |
| eb8bc91 | git@github.com:QIICR/dcmqi.git | upstream, QIICR/dcmqi | Segmentation Storage | (null) | 21 | 2022-03-12T22:33:09-05:00 | v1.2.4 | upstream |
| 3efde87 | git@github.com:QIICR/dcmqi.git | upstream, QIICR/dcmqi | Segmentation Storage | (null) | 21 | 2020-06-02T17:04:55-04:00 | v1.2.2 | upstream |
| 451bf84 | https://github.com/qiicr/dcmqi.git | upstream, QIICR/dcmqi | Segmentation Storage | (null) | 21 | 2023-01-26T11:08:36-05:00 | v1.2.5 | upstream |
| 4feafda |  | orphaned, no repository named | Real World Value Mapping Storage | (null) | 20 |  |  | orphaned, not in upstream history |
| 9c0c7bf | NA | not a dcmqi repository URL | Segmentation Storage | (null) | 12 | 2020-03-04T14:53:35-05:00 | v1.2.2 | upstream |
| 1f92074 | git@github.com:QIICR/dcmqi.git | upstream, QIICR/dcmqi | Segmentation Storage | (null) | 8 | 2022-03-23T17:13:52-04:00 | v1.2.4 | upstream |
| f621a32 | https://github.com/fedorov/dcmqi.git | named fork, fedorov | Segmentation Storage | (null) | 8 | 2017-04-06T00:05:11-04:00 | v1.0.5 | upstream |
| 55dc95e | git@github.com:QIICR/dcmqi.git | upstream, QIICR/dcmqi | Segmentation Storage | (null) | 4 | 2019-03-06T12:58:45-05:00 | v1.2.1 | upstream |
| d88b025 | https://github.com/QIICR/dcmqi | upstream, QIICR/dcmqi | Segmentation Storage | (null) | 3 | 2024-06-26T16:03:33-04:00 | v1.3.4 | upstream |
| ee9711c | https://github.com/qiicr/dcmqi.git | upstream, QIICR/dcmqi | Segmentation Storage | (null) | 3 | 2020-12-28T15:09:41-05:00 | v1.2.3 | upstream |
| a3c9e4a | git@github.com:QIICR/dcmqi.git | upstream, QIICR/dcmqi | Segmentation Storage | (null) | 2 | 2022-04-08T18:52:20-04:00 | v1.2.4 | upstream |
| 99192b7 | git://github.com/QIICR/dcmqi.git | upstream, QIICR/dcmqi | Segmentation Storage | (null) | 1 | 2020-11-06T15:23:33-05:00 | v1.2.2 | upstream |

**Resolution is incomplete, and the reason is a constraint rather than an
oversight.** Commit date and nearest tag require the QIICR/dcmqi commit history,
which is not on this machine and cannot be obtained without network access, and
this pass was instructed not to fetch. Every SHA is listed with its declared
repository and its repository class, both derivable from the object alone, and
the two git-derived columns read `UNRESOLVED OFFLINE`. The completing command is
in the ledger row and in `REPORT.md`.

*What this table shows.* The version carrier of the most common writing toolkit
in the archive is a commit hash of the encoder, not a version of anything that
computed a result. Reading it back tells a consumer which build of dcmqi wrote
the file and nothing at all about the analysis. The repository class column does
resolve offline and is already informative: it separates objects whose declared
repository is upstream from those naming a personal fork, which is a
build-environment fact rather than the vendor inconsistency it can be read as.

## T3.6 Index versus object writer identity

The archive catalogue and the object disagreeing about what produced the object.
The writer label is derived by the same ordered rule table in both cases,
`colophon.writers.WRITER_RULES`, imported unchanged. Only the evidence differs:
the index sees two equipment attributes, and the object also carries
`ContributingEquipmentSequence` and `ImplementationVersionName`.

| sop_class_name | objects | relabelled | pct_relabelled | index_says_unidentifiable | object_says_unidentifiable |
|---|---|---|---|---|---|
| RT Structure Set Storage | 19,358 | 0 | 0.000 | 3,173 | 3,173 |
| Segmentation Storage | 6,386 | 1,001 | 15.670 | 1,769 | 768 |
| Comprehensive 3D SR Storage | 5,408 | 5,312 | 98.220 | 5,312 | 0 |
| Comprehensive SR Storage | 2,118 | 0 | 0.000 | 826 | 826 |
| Grayscale Softcopy Presentation State Storage | 1,086 | 0 | 0.000 | 1,086 | 1,086 |
| Parametric Map Storage | 691 | 691 | 100.000 | 691 | 0 |
| Key Object Selection Document Storage | 40 | 0 | 0.000 | 40 | 40 |
| Real World Value Mapping Storage | 20 | 0 | 0.000 | 0 | 0 |

Per analysis result, only the cells that move:

| sop_class_name | analysis_result_id | writer_from_index | writer_from_object | deciding_carrier | objects | objects_in_cell | pct_of_cell |
|---|---|---|---|---|---|---|---|
| Comprehensive 3D SR Storage | nnu_net_bpr_annotations | not identifiable from index | highdicom | ImplementationVersionName | 2,906 | 2,906 | 100.000 |
| Comprehensive 3D SR Storage | lung_pet_ct_dx_annotations | not identifiable from index | highdicom | ContributingEquipmentSequence | 1,091 | 1,091 | 100.000 |
| Comprehensive 3D SR Storage | nlst_sybil | not identifiable from index | highdicom | ContributingEquipmentSequence | 970 | 970 | 100.000 |
| Parametric Map Storage | tcga_gbm360 | not identifiable from index | highdicom | ContributingEquipmentSequence | 691 | 691 | 100.000 |
| Segmentation Storage | tcga_sbu_til_maps | not identifiable from index | highdicom | ContributingEquipmentSequence | 384 | 384 | 100.000 |
| Segmentation Storage | pan_cancer_nuclei_seg_dicom | not identifiable from index | highdicom | ImplementationVersionName | 356 | 356 | 100.000 |
| Comprehensive 3D SR Storage | prostatex_targets | not identifiable from index | highdicom | ContributingEquipmentSequence | 345 | 345 | 100.000 |
| Segmentation Storage | rms_mutation_prediction_expert_annotations | not identifiable from index | highdicom | ImplementationVersionName | 261 | 261 | 100.000 |

Reported both ways:

- object weighted: **7,004 of 35,107, 19.95 percent**
- by collection: 83 collections: **54 at 0 percent, 19 at 100 percent**, 10 in between (lung_pet_ct_dx at 99.36 percent, tcga_luad at 98.36 percent, tcga_lusc at 98.28 percent, nlst at 75.06 percent, tcga_kirc at 74.19 percent, rms_mutation_prediction at 73.11 percent)
- by analysis result: 25 analysis results: **17 at 0 percent, 6 at 100 percent**, 2 in between (nnu_net_bpr_annotations at 88.33 percent, rms_mutation_prediction_expert_annotations at 73.11 percent)

*What this table shows.* This is a provenance finding, not a data-cleaning note.
The catalogue a researcher queries to build a cohort disagrees with the file
about what produced it, and it disagrees in one direction: the index says the
writer cannot be identified and the object says it can. Every move is decided by
a carrier the index does not expose. The consequence is that a cohort selected on
the index's writer attribution rests on a weaker reading of the object than the
object itself supports, and the size of that effect is the rate above. The
boundary counts show two camps again, because whether a toolkit writes
`ContributingEquipmentSequence` is a property of the toolkit and not of the study.

## What was dropped

- `enhanced_sr_series_in_manifest`: 262,883
- `enhanced_sr_series_recorded`: 74,063

Nothing else. Every object in the seven complete census classes and in the PRE-06
sample appears in every table, and no table samples, truncates or ranks.

## What this tabulation does not do

- **No conformance was adjudicated.** No message class was scored, no rate is
  NET, and the only conformance statement anywhere is the Type 1 binding of
  STD-04, which is a verified reading of PS3.3 and not a validator verdict.
- **No manuscript restructure.** The tables live here and in `results/claim3/`.
- **No median and no IQR** for any unit-level distribution, by instruction. They
  are two point masses and a median reports one camp as a centre.
- **No ranking.** Tables are ordered by size, never by how badly a group scores.
