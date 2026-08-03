# Phase 0: census of derived objects in IDC v24

Zero bytes downloaded. Every number here comes from the local `idc-index`
dataframe, one row per series, 1,032,911 rows in total.

Reproduce with `python -m colophon.index`. Version pins in `results/environment.json`.

## What counts as a derived object

Nine SOP classes, listed in `colophon/index.py` as `DERIVED_SOP_CLASSES`.
Counting exactly these nine gives **481,750 series and 504,727
instances**, which reproduces the figure the study was scoped against. The set
was not chosen to hit that number: it was recovered by searching SOP class
subsets, and only one subset of the plausible candidates matches on both series
and instance counts simultaneously.

Six further produced-not-acquired classes sit outside that denominator and are
reported separately, 9,912 series in total, so the
boundary is visible rather than implicit.

| | series | instances | size |
|---|---|---|---|
| whole archive | 1,032,911 | 57,409,445 | 94.67 TB |
| derived, nine classes | 481,750 | 504,727 | 18.72 TB |
| adjacent, six classes | 9,912 | 10,129 | 1.74 TB |

## Census by SOP class

| sop_class_name | series | instances | size_GB | collections | patients | mean_MB_per_series |
|---|---|---|---|---|---|---|
| Enhanced SR Storage | 262,883 | 262,883 | 139.475 | 4 | 27,507 | 0.543 |
| Segmentation Storage | 190,146 | 213,123 | 19,023.1 | 69 | 42,900 | 102.446 |
| RT Structure Set Storage | 19,358 | 19,358 | 10.088 | 18 | 4,248 | 0.534 |
| Comprehensive 3D SR Storage | 5,408 | 5,408 | 0.355 | 5 | 1,861 | 0.067 |
| Comprehensive SR Storage | 2,118 | 2,118 | 0.033 | 7 | 515 | 0.016 |
| Grayscale Softcopy Presentation State Storage | 1,086 | 1,086 | 0.002 | 3 | 41 | 0.001 |
| Parametric Map Storage | 691 | 691 | 0.355 | 1 | 336 | 0.526 |
| Key Object Selection Document Storage | 40 | 40 | 0.046 | 1 | 10 | 1.187 |
| Real World Value Mapping Storage | 20 | 20 | 0.001 | 1 | 20 | 0.043 |

Adjacent classes, outside the denominator above:

| sop_class_name | series | instances | size_GB | collections |
|---|---|---|---|---|
| Microscopy Bulk Simple Annotations Storage | 7,102 | 7,102 | 1,781.6 | 15 |
| Encapsulated STL Storage | 2,328 | 2,328 | 0.341 | 1 |
| Acquisition Context SR Storage | 277 | 277 | 0.001 | 6 |
| Advanced Blending Presentation State Storage | 107 | 324 | 0.022 | 4 |
| Spatial Registration Storage | 97 | 97 | 0.008 | 1 |
| X-Ray Radiation Dose SR Storage | 1 | 1 | 0.000 | 1 |

## Transfer syntax

Every derived class is Explicit VR Little Endian except the two rows below.


| sop_class_name | transfer_syntax_name | TransferSyntaxUID | series | pct_of_sop_class |
|---|---|---|---|---|
| RT Structure Set Storage | Implicit VR Little Endian | 1.2.840.10008.1.2 | 3,174 | 16.400 |
| Segmentation Storage | JPEG-LS Lossless | 1.2.840.10008.1.2.4.80 | 97 | 0.050 |

Two observations follow. Segmentation Storage carries a compressed transfer
syntax on a small minority of series, which matters for Phase 2 and 3 because a
validator that cannot decode JPEG-LS will report a different class of failure
than a conformance defect. RT Structure Set Storage carries Implicit VR Little
Endian on part of its population, which is the only derived class in the archive
where the transfer syntax is not self-describing.

## The GSPS attribution split

| collection_id | analysis_result_id | series | Manufacturer | ManufacturerModelName | source_DOI | license_short_name |
|---|---|---|---|---|---|---|
| rider_lung_ct | qiba_volct_1b | 320 | Siemens Corporate Research | DIRS2 | 10.7937/tcia.2020.1c3h-vp70 | CC BY 4.0 |
| qiba_ct_1c | (null) | 252 | Philips | nan | 10.7937/k9/tcia.2016.yxgr4blu | CC BY 3.0 |
| rider_pilot | qiba_volct_1b | 200 | Siemens Corporate Research | DIRS2 | 10.7937/tcia.2020.1c3h-vp70 | CC BY 4.0 |
| qiba_ct_1c | (null) | 84 | GE MEDICAL SYSTEMS | nan | 10.7937/k9/tcia.2016.yxgr4blu | CC BY 3.0 |
| qiba_ct_1c | (null) | 84 | TOSHIBA | nan | 10.7937/k9/tcia.2016.yxgr4blu | CC BY 3.0 |
| rider_lung_ct | qiba_volct_1b | 64 | nan | nan | 10.7937/tcia.2020.1c3h-vp70 | CC BY 4.0 |
| qiba_ct_1c | (null) | 42 | SIEMENS | nan | 10.7937/k9/tcia.2016.yxgr4blu | CC BY 3.0 |
| rider_pilot | qiba_volct_1b | 40 | nan | nan | 10.7937/tcia.2020.1c3h-vp70 | CC BY 4.0 |

The 462 series in `qiba_ct_1c` carry no `analysis_result_id`. The 624 in
`rider_lung_ct` and `rider_pilot` carry `qiba_volct_1b`. All three groups are
the same SOP class and all three originate in QIBA volumetric CT work. The
difference is how IDC ingested them: `qiba_ct_1c` is registered as a collection
in its own right with its own DOI, so its objects are collection content and
carry no analysis-result attribution, while the RIDER-derived objects are
registered as an analysis result computed over a separate source collection.

That is a provenance observation rather than a defect. `analysis_result_id` is
an IDC curation field, not a DICOM attribute, and it records whether IDC
ingested a series as an analysis of another collection. It does not record
whether the object was produced by an algorithm. For 462
GSPS series the field is null while the objects are plainly derived, so the
field cannot be used on its own as the denominator for a derived-object census.

## Parametric Map

| collection_id | analysis_result_id | series | instances | patients | Manufacturer | ManufacturerModelName | license_short_name |
|---|---|---|---|---|---|---|---|
| tcga_gbm | tcga_gbm360 | 691 | 691 | 336 | Gevaert Lab Converted By Imaging Data Commons | GBM360 | CC BY 4.0 |

Matches the brief: 691 series, `tcga_gbm` collection, `tcga_gbm360` analysis
result, CC BY 4.0, single manufacturer string.

## Licence

| license_short_name | series | instances |
|---|---|---|
| CC BY 4.0 | 458,281 | 481,258 |
| CC BY 3.0 | 22,457 | 22,457 |
| CC BY-NC 3.0 | 885 | 885 |
| CC BY-NC 4.0 | 127 | 127 |

Every derived series in the archive is under a Creative Commons licence. None
is restricted, which is what makes an exhaustive census of the small classes
legally straightforward.

## Phase 2 download budget

The classes the brief calls small enough to take whole:

| sop_class_name | series | instances | size_GB |
|---|---|---|---|
| Comprehensive 3D SR Storage | 5,408 | 5,408 | 0.355 |
| Comprehensive SR Storage | 2,118 | 2,118 | 0.033 |
| Grayscale Softcopy Presentation State Storage | 1,086 | 1,086 | 0.002 |
| Parametric Map Storage | 691 | 691 | 0.355 |
| Key Object Selection Document Storage | 40 | 40 | 0.046 |
| Real World Value Mapping Storage | 20 | 20 | 0.001 |

Total **0.791 GB** across 9,363
series. The brief estimated roughly 1 GB. That estimate holds.

## Two denominators

`analysis_result_id` records that IDC ingested a series as an analysis computed
over another collection. 463,543 of the 481,750 derived
series carry one, 96.22 percent.

Both denominators are reported throughout, because neither is the AI-derived
population on its own. The attributed set includes human work:
`eay131_tumor_annotations` was contoured through a viewer and
`lung_pet_ct_dx_annotations` declares "Expert annotation from TCIA". The
unattributed remainder includes 3,115 RT Structure Set
series from Pinnacle, ARIA, MIM and GammaPlan, which are radiotherapy planning
contours drawn by people. A claim about AI results quoted against the derived
denominator counts those, and a reviewer will say so.

## Scope: this census covers non-image derived SOP classes only

Selecting on SOP class omits two populations where a derived object is stored
under an acquisition SOP class. Objects with ImageType (0008,0008) value 1 equal
to DERIVED, and Secondary Capture output from processing pipelines, are exactly
the cases where a derived image is indistinguishable from an acquisition by
class alone.

**ImageType is not an index column**, so the size of the DERIVED stratum cannot
be estimated here at all. The classes it would live in are large: CT Image
Storage holds 266,230
series and Secondary Capture Image Storage holds
10,908.

Every claim in this study is therefore scoped to **non-image derived SOP
classes**, and that wording is used throughout rather than the unqualified word
derived. Sizing the ImageType DERIVED stratum requires reading objects and is
Phase 2 work.

## What per-series rather than per-instance validation would miss

| sop_class_name | series | instances | multi_instance_series | pct_of_series_multi_instance | instances_missed | pct_of_instances_missed |
|---|---|---|---|---|---|---|
| Segmentation Storage | 190,146 | 213,123 | 6,170 | 3.240 | 22,977 | 10.780 |

Across all derived objects the archive holds 1.0477 instances per
series. Validating one file per series therefore reaches 481,750 of
504,727 instances and misses **22,977, or
4.55 percent**. Segmentation Storage is the only derived
class with any multi-instance series at all, and only
3.24 percent of its series are multi-instance.

That is the honest size of the gap, and it is small. It is quoted at this
precision, and it is the secondary point.

The primary point is different and is not about coverage. Validation of public
DICOM archives is a documented, routine curation step, and existing tooling
supports per-series and per-SOP granularity. What the published record reports
is that validation was performed, not what it found. This study is scoped to
published measurement: rates, denominators, per-error-class breakdown, warning
classes and cross-validator disagreement.

## What was dropped

Nothing. This phase reads the complete index and aggregates all
1,032,911 rows. No sampling, no truncation, no filtering other than
the SOP class membership stated above.
