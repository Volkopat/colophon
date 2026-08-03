# Figure list

Six figures, drawn. Each is generated from the artefact named beside it and from nothing else, and every value annotated on a figure is checked against the ledger rows listed here by `tests/test_figures.py`.

Vector PDF for typesetting and a 300 dpi PNG for submission systems that demand raster. Regeneration is byte-identical and a test asserts it.

## Figure 1. The lead result, over the unit that is complete

All 36 analysis-result cells, one bar each, ordered by the level at which producer identity first appears. 25 cells resolve at no level, 8 at level 1, 2 at level 3 and 1 at level 4, and the 4 cells that also carry a version are marked. 36 is few enough to label every cell, so none is binned.

| | |
|---|---|
| artefact | `results/claim3/t33_recoverability_ladder.csv` |
| ledger rows | `C3T-03` |
| command | `python -m colophon.figures` |
| output | `results/figures/figure1.pdf`, `results/figures/figure1.png` |
| annotated values | cells = 36, none = 25, version = 4, level_1 = 8, level_3 = 2, level_4 = 1 |

## Figure 2. Conformance and attribution are independent

Three grades per SOP class as percentages, with a separate strip below the axis showing whether Enhanced General Equipment binds four attributes at Type 1 in that IOD. The binding is in its own register rather than drawn as a bar, because an earlier version drew it as a full-height hatched rectangle that read as a 100 percent bar, the opposite of its meaning.

| | |
|---|---|
| artefact | `results/manuscript/table2.csv` |
| ledger rows | `C3T-00`, `STD-04`, `STD-08` |
| command | `python -m colophon.figures` |
| output | `results/figures/figure2.pdf`, `results/figures/figure2.png` |
| annotated values | objects = 35107, iods_binding_type1 = 2, iods_not_binding = 6 |

## Figure 3. The mechanism, one layer at a time

Three real objects side by side, values verbatim from the Phase 3 records, tracing every carrier from the equipment attributes through the file meta to the algorithm carriers. A rule marks where the standard stops compelling anything. Values are truncated only on a word boundary and marked with an ellipsis, so a clipped string is never mistaken for the value.

**All three declare a non-MANUAL segment**, so the Type 1C condition on `SegmentAlgorithmName (0062,0009)` fires on all three and the three columns differ in what they say rather than in whether they were asked to say anything. That is the point of the figure and it is why the silent column changed.

The silent column was drawn from `dicom_lidc_idri_nodules`, every segment of which declares MANUAL. That silence is legitimate: the condition never fires, so nothing was omitted and nothing was avoided, and it is not the case this paper is about. It is now `rider_lungct_seg`, whose segments declare AUTOMATIC, whose `SegmentAlgorithmName` is the single character `0`, and whose identification sequence is absent. The condition fires, the standard is satisfied, and nothing at any level names a producer. `colophon.silent_column` found it and ledger row `FIG-02` records the four candidates and why this one.

| | |
|---|---|
| artefact | `results/figures/figure3_objects.json` |
| ledger rows | `C3T-06`, `DEV-02`, `FIG-02`, `P3-01`, `P3-05` |
| command | `python -m colophon.figures` |
| output | `results/figures/figure3.pdf`, `results/figures/figure3.png` |
| annotated values | dcmqi_sha = 7ae0873, dcmqi_algorithm_name = TotalSegmentator v1.5.6, highdicom_algorithm_name = Stony Brook TIL Segmentation Inception-V4 2022, silent_algorithm_type = AUTOMATIC, silent_algorithm_name = 0 |

## Figure 4. The residue is stable where the Jaccard is not

Two panels on the nine variant rungs. Panel a is the Jaccard between the two writers' floor sets: under dciodvfy it oscillates between 0.00 and 0.86 with no trend, and under dicom-validator it sits between 0.86 and 0.88 throughout, so the same statistic is unstable under one validator and stable under the other and its value depends on which tool is asked. Panel b is the residue, which is 1 at every rung under dicom-validator and 1 at eight rungs and 2 at V9 under dciodvfy. V9 is annotated with its cause, the pinned build being unable to read the deflated transfer syntax, not with its value alone.

The earlier wording here said the Jaccard "moves from 0.00 to 0.86", which is the reading Methods 2.8, Results 3.3 and Table 5 were all corrected away from: it does not move, it oscillates. The panel titles said the same thing twice over, one of them contradicting the figure title, and both are now panel letters with the description here.

| | |
|---|---|
| artefact | `results/phase1_variants.csv` |
| ledger rows | `B-02`, `B-03`, `B-05`, `B-10` |
| command | `python -m colophon.figures` |
| output | `results/figures/figure4.pdf`, `results/figures/figure4.png` |
| annotated values | rungs = 9, residue_dicom_validator_max = 1, residue_dciodvfy_max = 2 |

## Figure 5. Adjudication agreement, and what it does not establish

A two-by-two confusion matrix of the two adjudication passes on the net-relevant binary over the blind subset, with the 147 pre-disclosed classes drawn beside it and labelled as excluded, so the exclusion is visible rather than stated only in a caption.

| | |
|---|---|
| artefact | `results/adjudication2/two_pass_comparison.csv` |
| ledger rows | `ADJ2-01`, `ADJ2-02` |
| command | `python -m colophon.figures` |
| output | `results/figures/figure5.pdf`, `results/figures/figure5.png` |
| annotated values | blind_classes = 2109, kappa = 0.6241, agreement = 89.9, pre_disclosed = 147, total_classes = 2256 |

## Figure 6. Why the median is banned for these distributions

All 83 collections as points, jittered on a fixed seed, showing the two point masses at 0 and 100 with the 14 collections between them. The masses are the finding, so they are not summarised into bars.

| | |
|---|---|
| artefact | `results/claim3/encoder_only_by_collection.csv` |
| ledger rows | `C3T-02` |
| command | `python -m colophon.figures` |
| output | `results/figures/figure6.pdf`, `results/figures/figure6.png` |
| annotated values | collections = 83, at_zero = 44, at_hundred = 25, between = 14 |

## What the venue requires of an illustration, and what that changed

Three of the venue's figure rules bind on what is drawn rather than on what is
written about it, and all three were being broken.

**No titles or captions inside the illustration.** The guidelines say so in
terms, under FIGURE LETTERING. All six figures carried a title drawn into the
image and Figure 2 carried a two-line explanatory caption along the bottom. Every
one of them has moved into the legend, and each figure now returns its sentence
as `title_for_the_legend` so the legend and the image cannot say different
things. Figures 4 and 5, the floor and adjudication figures, also carried descriptive panel titles; those are panel
letters now, `a` and `b`, with the description in the legend.

**Lettering at a contrast ratio of at least 4.5 to 1.** Two pairings failed.
Figure 1 set white on the medium grey bar, which is **1.98 to 1**, and the
`between` label in Figure 4 used the light accent on white, which is 3.54 to 1.
Contrast is now computed from the colours the figures actually draw with, logged
pair by pair, and reported in the figure manifest: **48 text pairings, worst 5.10
to 1**. A test fails the build on anything under 4.5. This replaces a checklist
row that read "manual, not measured", which was the one manual row that was
failing.

**Numbering.** The six were renumbered so that first citation in the body runs 1 to 6 ascending, which the venue asks of figures in the same sentence as tables. The floor figure was 5 and is 4, the adjudication figure was 6 and is 5, and the collection-mass figure was 4 and is 6. No prose named them, so nothing but the numbers moved.

**Lettering of 2 to 3 mm at print size.** Figure 1 was drawn 193 mm wide against
a 174 mm column, so production would scale it to 90 percent and its 8 pt labels
would print at about 7.2 pt. It is drawn at the column width now and nothing is
scaled.

## Rendering discipline, applied to all six as one system

One accent colour for the thing a figure is about, grey for everything it is compared against, and a second muted tone only where a figure must separate two kinds of absence. No decorative palettes, no gradients, no three-dimensional effects, no shadows. One font at four sizes. Every axis carries its unit, every denominator is in the caption rather than implied, and where a figure shows a rate the floor it is quoted against is on the figure or in its caption.

## What looking at them caught, that no automated check would have

The third QA step is rendering each figure and reading it. It found five defects that no test detects, and they are recorded because the value of a check is what it caught:

- **Figure 2** drew the Type 1 binding as a full-height hatched rectangle. It read as a 100 percent bar, the exact opposite of its meaning. The fact moved into a strip below the axis, which cannot be mistaken for a value.
- **Figure 3** composed its values from summary artefacts and inferred one of them. It now reads two real objects. Its rule also struck through a row and its column headers collided.
- **Figure 1** had its legend overlapping the x-axis label, both unreadable.
- **Figure 5** had the V9 annotation on top of the legend and the right panel's y-label running into the left panel.
- **Figure 5** also counted ten rungs where the paper claims nine, because `V0R`, the round-trip control, is not a rung.

## Not to be drawn

- **No leaderboard of producing groups.** The finding is that nobody measures this, and a ranked chart of which group ships the worst objects is the one figure this study must not produce. A test asserts it.
- **No figure whose unit is the object where the analysis result is available.** Object-weighted figures carry the Enhanced SR exclusion and the concentration distortion, and a figure cannot carry a qualifying sentence.
- **No figure for Segmentation net conformance**, which has not been adjudicated.
