# Registered pins that were not satisfied, and the measured exposure

Two pins are registered and unsatisfied. Neither registration is edited here and
nothing is re-run. This document measures how much of the corpus is exposed to
the known behavioural difference, so each deviation carries a number.

**A pin that was never satisfied is not a pin changed after seeing results.** The
first is a deviation to be quantified and declared. The second is what
pre-registration exists to prevent, and it has not happened. Reproduce with
`python -m colophon.deviations`.

## Pin 1, dicom3tools

| | |
|---|---|
| registered | `1.00~20240118131615-1` |
| actually run | `20260701065818` |
| why the run build | it is the build the prior spine-gsps paper used, so every number here is comparable across the two papers |
| why the registered build was chosen | it predates three relaxations, so it flags conformant objects and turns them into floor classes |

The two builds are known to differ on exactly three changelog entries, so the
exposure is not every object. It is every object that is LABELMAP or TILED_FULL.

| entry | condition | attribute | applies to |
|---|---|---|---|
| `231003` | TILED_FULL | PatientOrientation | any IOD that can be TILED_FULL, which in the measured set is Segmentation and Parametric Map |
| `241003` | TILED_FULL | SegmentationMacro | Segmentation only |
| `241114` | LABELMAP | SegmentNumber | Segmentation only |

### Measured exposure

| | objects |
|---|---|
| measured set, all classes | **35,107** |
| Segmentation objects, where both attributes were captured | 6,386 |
| **LABELMAP** | **0** |
| **TILED_FULL** | **1,001** |
| exposed to any of the three entries | **1,001**, 2.85 percent of the measured set |

`SegmentationType (0062,0001)` values observed: FRACTIONAL 1,167, BINARY 5,219.

`DimensionOrganizationType (0020,9311)` values observed: 3D 727, (absent) 4,658, TILED_FULL 1,001.

Where the exposed objects are:

| SOP class | analysis_result_id | condition | objects | objects in cell | percent of cell |
|---|---|---|---|---|---|
| `Segmentation Storage` | tcga_sbu_til_maps | TILED_FULL | 384 | 384 | 100.00 |
| `Segmentation Storage` | pan_cancer_nuclei_seg_dicom | TILED_FULL | 356 | 356 | 100.00 |
| `Segmentation Storage` | rms_mutation_prediction_expert_annotations | TILED_FULL | 261 | 261 | 100.00 |

**LABELMAP exposure is zero.** Changelog entry `241114` cannot have moved any
number in this study, and that is a measurement rather than an argument.

**TILED_FULL exposure is 1,001 objects**, all of them
whole-slide-imaging segmentations in three analysis results. Entries `231003` and
`241003` do have exposure and it is bounded to those objects.

### Which way the difference runs

The registered build is the **stricter** one: it would emit messages the run
build suppresses, not fewer. Addendum 02 section 2 pre-classifies exactly those
messages as **floor rather than defect**, so a net rate is insulated by
construction and the gross count on the exposed objects is a lower bound rather
than an unknown.

### The observable signature

Not proof of what the registered build would do, and not offered as proof. If the
run build still emitted PatientOrientation or Segmentation-macro findings on
these objects, the relaxations would not be active in it and the argument above
would be wrong.

**0 message classes** touching
`PatientOrientation` or the Segmentation macro appear on the
1,001 exposed objects. That is consistent with the
relaxations being active in the build that ran.

### What is not measured

`DimensionOrganizationType (0020,9311)` was **not captured for the seven census
classes**, because the census capture list predates this question.
Parametric Map Storage is the only one of them whose IOD can carry
TILED_FULL, so exposure there is unmeasured over
**691 objects**. `SegmentationType (0062,0001)` exists
only in the Segmentation IOD, so its exposure in the census classes is
structurally zero rather than unmeasured.

## Pin 2, highdicom

| | |
|---|---|
| registered | `0.28.0` |
| installed | `0.28.1` |
| role | W1, the Phase 1 writer that emits fixture objects for the floor set. Not a validator anywhere in this project. |

Two measurements bound the exposure without needing the changelog.

**No module that produces a measured number uses it as an instrument.** Three
columns, because "the name appears" and "a reader was called" are different
questions and merging them would overstate the case. `floor.py` does import the
package, to read `__version__` for the pinning appendix, and it names highdicom
as W1 because highdicom is the Phase 1 writer. Neither is highdicom producing a
number.

| module | name appears | imports the package | **used as an instrument** |
|---|---|---|---|
| `colophon/census.py` | no | no | **no** |
| `colophon/phase3.py` | no | no | **no** |
| `colophon/floor.py` | yes | yes | **no** |
| `colophon/claim3.py` | yes | no | **no** |

**No object in the measured set was written by either version.** The corpus was
written by these highdicom builds:

| ImplementationVersionName | objects |
|---|---|
| `highdicom0.20.0` | 2,701 |
| `highdicom0.27.0` | 2,391 |
| `highdicom0.26.1` | 1,090 |
| `highdicom0.22.0` | 452 |
| `highdicom0.23.0` | 261 |
| `highdicom0.21.1` | 205 |

Objects written by a pinned version, 0.28.0 or 0.28.1:
**0** of
7,100 highdicom-written objects.

So the highdicom deviation has **zero exposure in Phase 2, Phase 3 and the claim
3 tabulation**, and its exposure is confined to the Phase 1 Arm A floor set,
where highdicom is the writer.

The changelog diff itself is UNRESOLVED OFFLINE. The 0.28.0 source is not on this machine and the diff needs network. Completing command: pip download highdicom==0.28.0 --no-deps --no-binary :all:, then diff its CHANGELOG against the installed 0.28.1.
