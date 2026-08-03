# PRE-06: the Segmentation Storage sampling frame

**Status: proposal. Nothing has been drawn and nothing has been fetched.**
`colophon.sample.EXECUTE` is False and every function that would select a series
or move a byte raises while it stays that way. Approving this frame means
closing ledger row PRE-06.

IDC v24, index evidence only. Reproduce with `python -m colophon.sample`.

## Why this class needs a frame at all

Segmentation Storage is 190,146 series and 18.58 TB. The six
small classes of Phase 2 were taken whole for under 1 GB. This one cannot be,
and it is now the only one of the nine derived classes left unmeasured.

Because it is a single SOP class, the general-purpose frame the brief sketched
is unnecessary. Stratification is by **writing toolkit and
`analysis_result_id`**, and by nothing else.

Both stratifiers earn their place from a measured row rather than from taste.
Writer, because F1-01 measured the validator floor to be writer-specific, so a
post-floor rate is only defined inside a stratum of known writer. Analysis
result, because C3-13 measured that a single analysis result moves a
population rate by 49.5 points, so pooling across analysis results reports the
largest producer rather than the archive.

## The strata

21 strata, exhaustive and disjoint over the 190,146 series.

| stratum | series | size_GB | mean_MB | collections | patients | largest_collection_pct | floor_measured |
|---|---|---|---|---|---|---|---|
| dcmqi / totalsegmentator_ct_segmentations | 126,051 | 13,854.6 | 112.550 | 1 | 26,194 | 100.000 | yes |
| not identifiable from index / tcga_sbu_til_maps | 21,030 | 1.994 | 0.097 | 23 | 7,600 | 14.920 | no |
| not identifiable from index / (null) | 8,977 | 46.814 | 5.340 | 8 | 1,666 | 29.940 | no |
| dcmqi / bamf_aimi_annotations | 8,202 | 26.249 | 3.277 | 22 | 4,226 | 29.070 | yes |
| dcmqi / dicom_lidc_idri_nodules | 6,859 | 1.326 | 0.198 | 1 | 875 | 100.000 | yes |
| not identifiable from index / pan_cancer_nuclei_seg_dicom | 6,074 | 5,025.6 | 847.257 | 14 | 5,184 | 17.880 | no |
| dcmqi / (null) | 2,357 | 22.711 | 9.867 | 13 | 1,963 | 21.760 | yes |
| dcmqi / prostate_mri_us_biopsy_dicom_annotations | 2,328 | 1.382 | 0.608 | 1 | 842 | 100.000 | yes |
| dcmqi / nnu_net_bpr_annotations | 2,281 | 20.834 | 9.353 | 2 | 985 | 54.450 | yes |
| pydicom-seg / (null) | 1,991 | 8.029 | 4.130 | 3 | 34 | 69.210 | no |
| highdicom / eay131_tumor_annotations | 1,404 | 0.676 | 0.493 | 1 | 438 | 100.000 | yes |
| dcmqi / nlstseg | 601 | 0.244 | 0.415 | 1 | 601 | 100.000 | yes |
| highdicom / (null) | 597 | 0.491 | 0.842 | 1 | 378 | 100.000 | yes |
| not identifiable from index / qiba_volct_1b | 520 | 0.345 | 0.679 | 2 | 40 | 61.540 | no |
| QIICR Reporting via 3D Slicer / qin_lungct_seg | 378 | 2.768 | 7.497 | 4 | 31 | 28.570 | no |
| dcmqi / prostatex_seg_zones | 98 | 0.146 | 1.525 | 1 | 98 | 100.000 | yes |
| not identifiable from index / rms_mutation_prediction_expert_annotations | 97 | 6.810 | 71.891 | 1 | 96 | 100.000 | no |
| QIICR Reporting via 3D Slicer / (null) | 96 | 0.797 | 8.505 | 1 | 96 | 100.000 | no |
| dcmqi / pancreas_ct_seg | 80 | 0.224 | 2.869 | 1 | 80 | 100.000 | yes |
| dcmqi / prostatex_seg_hires | 66 | 0.122 | 1.897 | 1 | 66 | 100.000 | yes |
| dcmqi / rider_lungct_seg | 59 | 0.924 | 16.033 | 1 | 31 | 100.000 | yes |

`size_GB` is the sum of `series_size_MB` over the stratum, divided by 1024.
`mean_MB` is what one series costs to fetch, and it runs from
0.097 MB to 847.3 MB, a factor of
**8,726** across the frame. That
spread, and not the spread in series counts, is what makes a
series-proportional allocation the wrong instrument here.

`floor_measured` says whether Phase 1 emitted a conformant object with that
stratum's writer. Where it says no, a raw failure rate is reportable and a
post-floor rate is not.

12 of the 21 strata contain exactly one collection,
covering 138,336 series,
72.8 percent of the class. That fact governs
the variance section below and it is not a detail.

## The registered minimum

**n = 384 per published stratum.** It is carried from ledger row
PRE-05 unchanged and is not rederived here. What it buys is computed rather than
asserted:

| | |
|---|---|
| 95 percent Wilson half-width at the PRE-05 threshold p = 0.05 | 2.21 points |
| 95 percent Wilson half-width at the least favourable p = 0.50 | 4.98 points |
| smallest n reaching 5 points at p = 0.50, Wilson | 381 |
| the same figure by the conventional Wald formula z^2 p(1-p) / e^2 | 385 |

So 384 sits between the Wilson worst case minimum of
381 and the Wald figure of
385 that the convention rounds from, and at the threshold
the interval it buys is 2.21 points wide
either side.

Allocation, by stratum size N_h:

| N_h | allocation |
|---|---|
| at or under 384 | the whole stratum |
| above 384 | 384, or what the byte cap allows, never below 30 |

Reporting, by the number of series actually validated n_h. This is the rule, not
a suggestion, and it is applied whether the series were sampled or taken whole:

| n_h | what is reported |
|---|---|
| at or above 384 | a rate with a Wilson interval |
| 30 to 383 | a rate with a Wilson interval and a below-registered-n flag |
| under 30 | counts only, never a rate |

## What the registered minimum would cost everywhere

Giving every stratum its registered allocation costs
**385.0 GB**, which is
2.57 times the
150 GB budget. One stratum accounts for most of it:
`not identifiable from index / pan_cancer_nuclei_seg_dicom` alone would cost
317.7 GB for
384 series, because its mean series is
847 MB.

So the registered minimum does not fit everywhere and something has to give.

## The allocation that was rejected

**Proportional to series.** At the archive's mean of
102.4 MB per series,
150 GB buys 1,499 series in
total. Allocating those proportionally puts
66.8 percent of the sample in one
stratum and leaves **15 of the
21 strata under 30 series**, of which
6 would get no series at all. It
spends the budget and returns no reportable rate for most of the frame. That is
C3-13 repeated as a sampling design.

## The allocation that is proposed

Cost-capped, in four steps, all of them stated before any draw:

1. A stratum at or under 384 series is taken whole.
2. Every other stratum is offered the registered minimum of 384.
3. If that does not fit, one per-stratum byte cap B is lowered until it does. A
   stratum whose registered allocation already costs less than B is untouched,
   so precision is bought where it is cheap first and only the expensive strata
   are cut.
4. No stratum is cut below 30, because under that no rate is reported
   and the bytes buy nothing reportable.

The cap that fits is **B = 64,392 MB per stratum**.

| stratum | series | n | sampling_fraction | expected_GB | allocation_rule | reporting_rule |
|---|---|---|---|---|---|---|
| dcmqi / totalsegmentator_ct_segmentations | 126,051 | 384 | 0.003 | 42.206 | registered minimum, n = 384 | rate with Wilson interval |
| not identifiable from index / tcga_sbu_til_maps | 21,030 | 384 | 0.018 | 0.036 | registered minimum, n = 384 | rate with Wilson interval |
| not identifiable from index / (null) | 8,977 | 384 | 0.043 | 2.003 | registered minimum, n = 384 | rate with Wilson interval |
| dcmqi / bamf_aimi_annotations | 8,202 | 384 | 0.047 | 1.229 | registered minimum, n = 384 | rate with Wilson interval |
| dcmqi / dicom_lidc_idri_nodules | 6,859 | 384 | 0.056 | 0.074 | registered minimum, n = 384 | rate with Wilson interval |
| not identifiable from index / pan_cancer_nuclei_seg_dicom | 6,074 | 75 | 0.012 | 62.055 | byte capped at 64392 MB, below the registered minimum | rate with Wilson interval, below-registered-n flag |
| dcmqi / (null) | 2,357 | 384 | 0.163 | 3.700 | registered minimum, n = 384 | rate with Wilson interval |
| dcmqi / prostate_mri_us_biopsy_dicom_annotations | 2,328 | 384 | 0.165 | 0.228 | registered minimum, n = 384 | rate with Wilson interval |
| dcmqi / nnu_net_bpr_annotations | 2,281 | 384 | 0.168 | 3.507 | registered minimum, n = 384 | rate with Wilson interval |
| pydicom-seg / (null) | 1,991 | 384 | 0.193 | 1.549 | registered minimum, n = 384 | rate with Wilson interval |
| highdicom / eay131_tumor_annotations | 1,404 | 384 | 0.274 | 0.185 | registered minimum, n = 384 | rate with Wilson interval |
| dcmqi / nlstseg | 601 | 384 | 0.639 | 0.156 | registered minimum, n = 384 | rate with Wilson interval |
| highdicom / (null) | 597 | 384 | 0.643 | 0.316 | registered minimum, n = 384 | rate with Wilson interval |
| not identifiable from index / qiba_volct_1b | 520 | 384 | 0.738 | 0.255 | registered minimum, n = 384 | rate with Wilson interval |
| QIICR Reporting via 3D Slicer / qin_lungct_seg | 378 | 378 | 1.000 | 2.768 | whole stratum, N at or under the registered minimum | rate with Wilson interval, below-registered-n flag |
| dcmqi / prostatex_seg_zones | 98 | 98 | 1.000 | 0.146 | whole stratum, N at or under the registered minimum | rate with Wilson interval, below-registered-n flag |
| not identifiable from index / rms_mutation_prediction_expert_annotations | 97 | 97 | 1.000 | 6.810 | whole stratum, N at or under the registered minimum | rate with Wilson interval, below-registered-n flag |
| QIICR Reporting via 3D Slicer / (null) | 96 | 96 | 1.000 | 0.797 | whole stratum, N at or under the registered minimum | rate with Wilson interval, below-registered-n flag |
| dcmqi / pancreas_ct_seg | 80 | 80 | 1.000 | 0.224 | whole stratum, N at or under the registered minimum | rate with Wilson interval, below-registered-n flag |
| dcmqi / prostatex_seg_hires | 66 | 66 | 1.000 | 0.122 | whole stratum, N at or under the registered minimum | rate with Wilson interval, below-registered-n flag |
| dcmqi / rider_lungct_seg | 59 | 59 | 1.000 | 0.924 | whole stratum, N at or under the registered minimum | rate with Wilson interval, below-registered-n flag |

### The arithmetic

| | |
|---|---|
| strata | 21 |
| strata taken whole | 7 |
| strata at the registered minimum | 13 |
| strata cut by the byte cap | 1 |
| strata reporting counts only | 0 |
| **series to fetch** | **5,941** of 190,146, 3.12 percent |
| expected bytes | **129.29 GB** |
| standard deviation of the realised byte total | 4.38 GB |
| 3 sigma upper bound on the realised total | **142.44 GB** |
| budget | 150 GB |
| headroom at the upper bound | 7.56 GB |

The byte total of a draw is a random sum of skewed series sizes, so the budget
is checked against the 3 sigma upper bound rather than the
expectation. Both are under 150 GB.

Before any byte moves, the exact byte total of the drawn manifest is recomputed
from `series_size_MB` and compared against 150 GB. If it exceeds it,
the deterministic remedy is to lower B by 5 percent and shorten the same
permutations, never to redraw, and the fact that the gate fired is recorded.

### What the byte cap costs in precision

- `not identifiable from index / pan_cancer_nuclei_seg_dicom`: 75 of 6,074 series, 62.05 GB of a 5025.62 GB stratum. Wilson half-width at p = 5 percent widens from 2.21 to 5.29 points.

That is the whole precision loss in the frame. Every other stratum is at its
registered allocation or taken whole.

## The estimator

**Population failure rate.** Stratified, series weighted. With
W_h = N_h / N and p_h the observed failure fraction in stratum h:

    p = sum_h W_h p_h

Equivalently the ratio form with design weights w_i = N_h / n_h for series i in
stratum h, which is what the code computes:

    p = ( sum_i w_i y_i ) / ( sum_i w_i ),    y_i in 0, 1

The weights are known exactly because N_h is read from a complete index rather
than estimated. The rate is reported by SOP class and by `analysis_result_id`,
never as a ranking of writers.

**Variance, clustered at the collection.** C3-12 measured that series inside a
collection are not independent, and C3-13 measured the size of the effect:
removing one collection moves a rate from 86.4 to 34.81 percent. The variance
estimator therefore treats the **collection as the primary sampling unit** inside
each stratum. Taylor linearised, ultimate cluster form, for the ratio p:

    u_i  = w_i ( y_i - p ) / sum_i w_i
    u_hj = sum over series i in collection j of stratum h of u_i
    ubar_h = ( 1 / c_h ) sum_j u_hj

    v_clustered(p) = sum_h ( 1 - f_h ) ( c_h / ( c_h - 1 ) )
                     sum_{j=1}^{c_h} ( u_hj - ubar_h )^2

with f_h = n_h / N_h the sampling fraction and c_h the number of distinct
collections that stratum h's sample actually hit. Degrees of freedom
df = sum_h ( c_h - 1 ) over strata with c_h at least 2, and the interval is
p plus or minus t(df, 0.975) times sqrt(v_clustered).

**The singleton problem, and the fix, both pre-registered.** A stratum with
c_h = 1 contributes no degrees of freedom and no variance term, and
12 of the 21 strata are single collection. The
collapsed strata method is used: every c_h = 1 stratum is pooled into one
variance stratum whose primary sampling units are its collections. Point
estimation is untouched. The method is conservative, that is, it charges genuine
between-stratum differences to sampling error and so overstates the width, and
its conservatism is not quantified here.

**Design based variance, reported beside it.** For the finite population target,
which is the number of non-conformant objects actually in IDC v24, the
correct variance is the stratified simple random sampling variance with the
finite population correction:

    v_design(p) = sum_h W_h^2 ( 1 - f_h ) p_h ( 1 - p_h ) / ( n_h - 1 )

Clustering does not enter it, because series were sampled directly rather than
in clusters. Both are reported. The clustered interval is the wider of the two
and is the one quoted, which is conservative. The design based interval is the
correct width for the only claim this study is scoped to make, which is a claim
about IDC v24 and not about DICOM practice.

## The intracluster correlation and the design effect

Kish, per stratum, with mbar_h the mean number of sampled series per sampled
collection:

    D_h     = 1 + ( mbar_h - 1 ) rho_h
    n_eff,h = n_h / D_h

rho is estimated from the realised sample by one way analysis of variance on the
binary outcome, with the collection as the grouping factor:

    MSB = ( 1 / ( c - 1 ) ) sum_j m_j ( ybar_j - ybar )^2
    MSW = ( 1 / ( M - c ) ) sum_j sum_i ( y_ij - ybar_j )^2
    m0  = ( 1 / ( c - 1 ) ) ( M - sum_j m_j^2 / M ),   M = sum_j m_j
    rho = ( MSB - MSW ) / ( MSB + ( m0 - 1 ) MSW )

**The planning value, measured rather than assumed.** The conformance outcome
cannot be observed without fetching, so its rho is unknown until Phase 3 runs.
What can be measured now is the collection level clustering of
attribute presence defects, which are the same shape of outcome: a Type 2
attribute is empty or it is not, and a validator either complains or it does
not. Four index columns are used as proxies and are labelled as proxies.

The provenance flag of C3-12 is deliberately **not** used. Its within stratum
variance is exactly zero in all 21 strata, because the stratification is
built from the same two attributes the flag is built from, so it would measure
the stratification and not the clustering. That is itself worth stating: the
frame absorbs the C3-12 clustering entirely for the provenance outcome.

| stratum | proxy | collections | series | rate_pct | rho | m0 |
|---|---|---|---|---|---|---|
| QIICR Reporting via 3D Slicer / qin_lungct_seg | PatientSex empty | 4 | 378 | 33.330 | 0.792 | 94.300 |
| dcmqi / (null) | BodyPartExamined empty | 13 | 2,357 | 8.270 | 0.990 | 171.300 |
| dcmqi / (null) | PatientSex empty | 13 | 2,357 | 22.100 | 0.930 | 171.300 |
| dcmqi / (null) | PatientAge empty | 13 | 2,357 | 48.370 | 0.828 | 171.300 |
| dcmqi / bamf_aimi_annotations | PatientSex empty | 22 | 8,202 | 20.690 | 0.893 | 336.300 |
| dcmqi / bamf_aimi_annotations | PatientAge empty | 22 | 8,202 | 23.290 | 0.848 | 336.300 |
| dcmqi / nnu_net_bpr_annotations | PatientSex empty | 2 | 2,281 | 45.550 | 1.000 | 1,131.5 |
| dcmqi / nnu_net_bpr_annotations | PatientAge empty | 2 | 2,281 | 57.650 | 0.762 | 1,131.5 |
| not identifiable from index / (null) | BodyPartExamined empty | 8 | 8,977 | 6.040 | 1.000 | 971.300 |
| not identifiable from index / (null) | SeriesDescription empty | 8 | 8,977 | 5.150 | 1.000 | 971.300 |
| not identifiable from index / (null) | PatientSex empty | 8 | 8,977 | 2.290 | 0.508 | 971.300 |
| not identifiable from index / (null) | PatientAge empty | 8 | 8,977 | 62.780 | 0.919 | 971.300 |
| not identifiable from index / qiba_volct_1b | PatientSex empty | 2 | 520 | 80.770 | 0.564 | 246.200 |
| pydicom-seg / (null) | BodyPartExamined empty | 3 | 1,991 | 18.830 | 1.000 | 469.100 |
| pydicom-seg / (null) | PatientSex empty | 3 | 1,991 | 18.830 | 1.000 | 469.100 |

Across the 15 stratum by proxy pairs with any within stratum
variation, rho runs from 0.508 to
1.000 with a median of **0.919**. That median is the
planning value used for sizing below. It is not used in any reported interval.

### What the planning rho does to the frame

| stratum | n | collections_in_stratum | expected_collections_sampled | mean_series_per_sampled_collection | design_effect | n_effective | half_width_pts_design_based | half_width_pts_clustered |
|---|---|---|---|---|---|---|---|---|
| dcmqi / totalsegmentator_ct_segmentations | 384 | 1 | 1.000 | 384.000 | 353.000 | 1.090 | 2.210 | 40.000 |
| not identifiable from index / tcga_sbu_til_maps | 384 | 23 | 22.940 | 16.740 | 15.500 | 24.840 | 2.190 | 10.000 |
| not identifiable from index / (null) | 384 | 8 | 7.630 | 50.320 | 46.300 | 8.290 | 2.170 | 18.800 |
| dcmqi / bamf_aimi_annotations | 384 | 22 | 20.410 | 18.810 | 17.400 | 22.110 | 2.160 | 10.710 |
| dcmqi / dicom_lidc_idri_nodules | 384 | 1 | 1.000 | 384.000 | 353.000 | 1.090 | 2.150 | 40.000 |
| not identifiable from index / pan_cancer_nuclei_seg_dicom | 75 | 14 | 13.250 | 5.660 | 5.300 | 14.190 | 5.250 | 13.890 |
| dcmqi / (null) | 384 | 13 | 12.980 | 29.590 | 27.300 | 14.080 | 2.030 | 13.960 |
| dcmqi / prostate_mri_us_biopsy_dicom_annotations | 384 | 1 | 1.000 | 384.000 | 353.000 | 1.090 | 2.020 | 40.000 |
| dcmqi / nnu_net_bpr_annotations | 384 | 2 | 2.000 | 192.000 | 176.500 | 2.180 | 2.020 | 33.600 |
| pydicom-seg / (null) | 384 | 3 | 3.000 | 128.000 | 117.700 | 3.260 | 1.990 | 29.140 |
| highdicom / eay131_tumor_annotations | 384 | 1 | 1.000 | 384.000 | 353.000 | 1.090 | 1.890 | 40.000 |
| dcmqi / nlstseg | 384 | 1 | 1.000 | 384.000 | 353.000 | 1.090 | 1.330 | 40.000 |
| highdicom / (null) | 384 | 1 | 1.000 | 384.000 | 353.000 | 1.090 | 1.320 | 40.000 |
| not identifiable from index / qiba_volct_1b | 384 | 2 | 2.000 | 192.000 | 176.500 | 2.180 | 1.130 | 33.600 |
| QIICR Reporting via 3D Slicer / qin_lungct_seg | 378 | 4 | 4.000 | 94.500 | 86.900 | 4.350 | 0.000 | 25.850 |
| dcmqi / prostatex_seg_zones | 98 | 1 | 1.000 | 98.000 | 90.100 | 1.090 | 0.000 | 40.000 |
| not identifiable from index / rms_mutation_prediction_expert_annotations | 97 | 1 | 1.000 | 97.000 | 89.200 | 1.090 | 0.000 | 40.010 |
| QIICR Reporting via 3D Slicer / (null) | 96 | 1 | 1.000 | 96.000 | 88.300 | 1.090 | 0.000 | 40.010 |
| dcmqi / pancreas_ct_seg | 80 | 1 | 1.000 | 80.000 | 73.600 | 1.090 | 0.000 | 40.010 |
| dcmqi / prostatex_seg_hires | 66 | 1 | 1.000 | 66.000 | 60.700 | 1.090 | 0.000 | 40.010 |
| dcmqi / rider_lungct_seg | 59 | 1 | 1.000 | 59.000 | 54.300 | 1.090 | 0.000 | 40.010 |

Read the two right hand columns together. At rho = 0.919 the design based
half-width of 2.21 points
becomes a clustered half-width of tens of points, and for the single collection
strata the effective sample size falls to about
1 / rho = 1.09, which is one collection. No amount of series level
sampling changes that. It is the same finding as C3-12, arriving as a
consequence rather than as a caveat: **the effective sample size of this frame
is bounded by its 103 stratum by collection cells,
not by its 5,941 series.**

This is the reason the design based interval is reported beside the clustered
one and the reason the study's claims are scoped to IDC v24. A
finite population count of broken objects in one archive release is exactly
estimable from 5,941 series. A statement about what a toolkit does in
general is not, and none is made.

## The seed

**SEED = 20260802.** One integer, fixed here in source, used for every stratified
draw in this frame and for nothing else.

The draw is nested. Each stratum is permuted once under a child seed derived
deterministically as `default_rng([SEED, crc32(stratum name)])`, and the
allocation takes a prefix of that permutation. Two consequences: shortening or
lengthening n_h shortens or lengthens the same draw rather than producing a
different one, and no stratum's draw depends on any other stratum's size or on
the order strata are processed in.

## What this frame does not cover

Stated here rather than in limitations, and each item names what is therefore
not claimable.

1. **One SOP class.** Segmentation Storage only. Enhanced SR, 262,883
   series, is the other large class and has no frame yet. No rate here is a rate
   for derived objects as a whole.

2. **Post-floor rates only where a floor exists.** F1-01 measured the floor to
   be writer specific, and Phase 1 emitted objects with dcmqi and highdicom
   only. 150,983 series,
   79.4 percent, sit in strata
   with a measured floor. The other 39,163,
   20.6 percent, do not, so
   for those strata a raw failure rate is reportable and a post-floor rate is
   not. The threshold in PRE-05 is defined above floor, so PRE-05 cannot be
   applied to them.

3. **The writer label is provisional.** W-01 infers it from the two equipment
   attributes the index carries, and
   36,698
   Segmentation series,
   19.3
   percent, are not attributable to a writer from the index at all. Phase 2
   reads ImplementationVersionName and ContributingEquipmentSequence, which are
   stronger evidence. If those change a series' writer the strata change, and
   the pre-registered response is to relabel and report the reallocation, not to
   silently redraw.

4. **Single collection strata generalise to nothing.** 12
   strata, 138,336 series. Their rates describe one collection
   produced by one pipeline in one run. They are reported as such and no claim
   is made from them about the toolkit or the algorithm in general.

5. **Rare defects are bounded, not estimated.** At n = 384 a defect
   affecting fewer than about 1 in 384 series in a stratum will
   usually be absent from the sample. Zero observed failures gives an upper
   bound of 0.99 percent by the Wilson
   interval, and no point rate. Nothing here can find a defect class that
   occurs in a handful of objects.

6. **The compressed transfer syntax minority is covered by accident, not by
   design, and only at n = 97.**
   97 Segmentation series carry a transfer
   syntax other than Explicit VR Little Endian,
   0.051 percent, and all of them
   are JPEG-LS Lossless inside the single stratum
   `not identifiable from index / rms_mutation_prediction_expert_annotations`. That stratum is under the registered minimum and
   is taken whole, so the frame does read every compressed object in the class.
   The rate is exact for IDC v24 and carries a below-registered-n
   flag, and it rests on one collection, so nothing about compressed
   Segmentation encoding in general follows from it. P0-04 flagged that a decode
   failure is not a conformance failure, and that separation has to be applied
   by hand in this stratum because no other stratum can calibrate it.

7. **The unit is the series, not the instance.** One stratum,
   `not identifiable from index / pan_cancer_nuclei_seg_dicom`, is
   100 percent multi instance and holds
   28,887 instances across
   6,074 series. Validating one instance per
   series leaves the rest unread. P0-11 put that gap at 4.55 percent of all
   derived instances; inside Segmentation Storage alone, which is the only derived class
   with any multi-instance series, it is
   10.78 percent of
   213,123 instances. No instance level rate is
   estimable from this frame.

8. **Objects outside the SOP class are outside the frame.** P0-12 records that
   segmentation-like content stored under an acquisition SOP class, with
   ImageType (0008,0008) value 1 equal to DERIVED, cannot be sized from the
   index and is not in this population.

9. **Sizes are the archive's own.** `series_size_MB` is an index field, not a
   figure measured on disk. The budget check inherits whatever error it carries,
   which is why 7.5 GB of the 150 GB cap is reserved and
   the plan is built against 142.5 GB.

10. **One release.** IDC v24. The strata, their sizes and the weights
    W_h are all release specific, and the frame is void on the next release.

## What was dropped

Nothing yet, because nothing has run. The frame proposes to read
5,941 of 190,146 series,
3.12 percent, and 0.68
percent of the class by volume. The
184,205 series not drawn are represented through the stratum
weights W_h and through nothing else.
