# Results

## 3.1 Population and coverage

**35,107 objects across eight SOP classes** were measured: seven classes
censused completely, and 6,386 Segmentation objects drawn under the
pre-registered PRE-06 frame, which read 5,941 of 190,146 series, 129.77 GB
against a 150 GB budget, with zero fetch failures and zero read failures
(PRE-06). Per-class counts are in Table 1.

**Enhanced SR Storage is excluded from every object-weighted rate reported
below**, 35,161 of 262,883 series recorded and the class still running.

The analysis-result unit is complete for the seven censused classes; for
Segmentation it is the identifiers observed in the PRE-06 sample and frame
coverage is unmeasured (C3T-13). The object-weighted unit is not complete, by
that exclusion, and it is additionally distorted by concentration. Both are given, and no object-weighted figure appears in this
section without the exclusion in the same sentence.

## 3.2 Claim 3: the encoder is recorded, the producer is not

### 3.2.1 The lead result

Of the 35,107 objects measured, excluding Enhanced SR, **28,905, 82.33 percent,
are conformant but uninformative**: everything the standard requires of them is
present, and none of it identifies what produced the result. 4,799, 13.67
percent, are informative. 1,403, 4.00 percent, are non-conformant (C3T-00).
Table 2, with the three grades by class in Figure 2.

Over the unit that is complete, the result is starker. Of **36 analysis-result
cells, producer identity appears at no carrier level in 25**. It appears at
level 1, the equipment attributes, in 8; at level 3, free text, in 2; at level 4,
the in-object algorithm carriers, in 1. **A version accompanies the identity in
4 cells of the 36** (C3T-03). Table 3, and every cell is drawn in Figure 1.

**The object-weighted rate is concentrated and the concentration is reported
rather than argued around.** One class, RT Structure Set Storage, supplies
**55.14 percent of the 35,107 objects** and is 100.00 percent uninformative, 0
informative, 0 non-conformant. Dropping that one class moves the archive-wide
figures to **60.62 percent uninformative and 30.47 percent informative**, a shift
of about twenty points in each. Table 2 carries the leave-one-class-out column
for every class, and no other class moves the uninformative rate by more than
about one and a half points except Segmentation, which moves it up to 89.39
percent.

This is why the analysis-result unit is the lead. **It is complete, it is immune
to that concentration, and it does not move**: 25 of 36 cells is a count over
cells, not a weighted average over objects, so no class can dominate it by being
large.

### 3.2.1a Two attributes, two claims, never blurred

At the segment level two attributes carry the question and **they are governed
differently, so they are two claims and not one** (STD-07).

**(0062,0007), the identification sequence, is Type 3 with no condition** inside
Segment Sequence. Of **36,488 segments declaring SegmentAlgorithmType AUTOMATIC
or SEMIAUTOMATIC, 34,234, 93.82 percent, carry no identification sequence at
all** (P3-01). **Omitting it is legal and no validator can flag it.** This claim
is about the permissiveness of the standard, not about the objects.

**(0062,0009), the algorithm name, is Type 1C, required when the type is not
MANUAL.** Omitting it is a conformance violation. Across **all 21 strata**, not
only the one where it surfaced, it is omitted on **12 of 36,488 non-MANUAL
segments, 0.03 percent, on 4 objects in 1 of 21 strata** (P3-05). Where the
standard compels a name, the archive supplies one almost everywhere.

The two together are the finding: the attribute the standard compels is populated
almost everywhere, and the attribute that would actually identify an algorithm is
optional and is absent from 93.82 percent of the same segments.

**A validator note, and it is a claim 2 finding.** On the 4 objects carrying the
12 omissions, `dciodvfy` raises the missing Type 1C message on every one.
`dicom-validator` does not raise it on all of them, which is consistent with its
registered behaviour of demoting conditional attributes it cannot parse and
failing open (P3-05).

**Incompleteness is a third state and it is zero.** Not one segment carries
the sequence present but incomplete (P3-02). That zero is **partly by
construction**: CP-2273 [10], applied to the standard at edition 2026b,
settles in PS3.5 7.4.5 [9] that a zero-length Type 3 element means the same as
absence, so an encoder that writes the sequence with nothing in it produces
absence rather than incompleteness under the current standard. The observed
zero is therefore not only an empirical result about these writers, and this
text says so rather than claiming the stronger reading.

### 3.2.1b The rule table undercounts, and the undercount runs one way

The classification rule is ordered and first match wins (2.4), and on two
analysis-result cells that ordering reaches a category before it reaches a
producer rule. Both are declared here with the value that decides them, because
the alternative is a reader finding it in a figure.

**The worked example is `tcga_sbu_til_maps`.** All 470 of its non-MANUAL
segments carry an Algorithm Identification Macro that is present and complete,
and its `AlgorithmName` reads `Stony Brook TIL Segmentation Inception-V4 2022`.
A human reader calls that a producer. The rule table does not reach that
question: the string matches the institution rule on `Stony Brook University`
first, and an institution names an organisation without naming what it ran, so
the cell resolves to identity at no level. `eay131_tumor_annotations` is the same
shape by a different route: its macro is complete on all 384 non-MANUAL segments
and names `Manual Segmentation`, which is on the published declined list as a
procedure rather than an algorithm (FIG-03).

**This is visible on the face of the paper and it is meant to be.** Figure 3's
third column is drawn from `tcga_sbu_til_maps` and prints that algorithm name,
while Table 3 lists the same analysis result among the 25 cells where identity
appears at no level. Both statements are correct under the published rule table
and neither is a transcription error. The figure is where a reader will notice
it.

**The direction is the point.** Counting both as producer identity would move
the lead result from 25 of 36 cells to 23 of 36 and would raise the informative
rate, not lower it. The rule table is therefore conservative against this
paper's own finding, which is what Methods 2.4 registers when it says a named
analysis with no matching rule is graded uninformative and the reported figure is
a lower bound on informativeness. Nothing is reclassified here: the rule table is
published, the residual is published, and moving a rule to catch these two would
be adjudicating our own result.

### 3.2.1c The residual cell, and the sensitivity of excluding it

Six of the 36 cells carry `(null)` as their analysis-result identifier, holding
5,731 of 35,107 objects, 16.32 percent of the denominator. A `(null)` cell is
every object in its class that the archive index gives no identifier, so it is a
residual bucket rather than one producer, and Methods 2.2 says so where the unit
is defined. Four of the six resolve at no carrier level and therefore sit inside
the headline numerator.

**Excluding the residual cells the ladder reads 21 of 30.** The headline is
**25 of 36**, which is the figure stated everywhere it is a headline; this is the
sensitivity beneath it and not a competing result (C3T-12). The direction is
small and it is toward the same conclusion, which is why one number is put in
front of a reader and this one is kept underneath it.

### 3.2.2 The mechanism

Both dominant writers record the serialiser with high fidelity. Neither records
the producer, and in one case the field is structurally incapable of carrying
it. Table 4, and Figure 3 traces one object of each kind carrier by carrier.

**dcmqi** [24] writes the git remote URL of the working copy that built the binary
into ManufacturerModelName, and that working copy's abbreviated HEAD SHA into
SoftwareVersions. Both are assigned at compile time from a constants header, so
**no caller can place a producing algorithm in either**. The corpus carries 28
distinct combinations of SHA, declared repository, class and analysis result over
3,023 objects; the repository class resolves offline, and commit date and nearest
tag require the upstream history and are unresolved (C3T-06).

**highdicom** [23] writes its own exact release, and **six distinct releases are
present in the corpus**: 0.20.0, 0.21.1, 0.22.0, 0.23.0, 0.26.1 and 0.27.0
(DEV-02). The identification is precise, and what it identifies is the library
that serialised the object.

The recurrence one layer down is the same pathology: for dcmqi objects the file
meta identifies DCMTK [19], the encoding library's own encoding library. At no
level does either writer name the analysis.

### 3.2.3 The ceiling, and it is the standard's

**In one sentence: PS3.3 2026c [8] compels a non-empty equipment value in 2 of
the 8 IODs measured, compels the mere presence of a manufacturer string,
possibly zero length, in 8 of 8, and compels nothing at all about model, serial
or software version in the remaining 6.**

This is a property of the standard, derived from the IOD module tables of PS3.3
2026c read directly, not an observation about the data (STD-07, STD-08). The
three tiers in full:

1. **A non-empty value is compelled in 2 of 8 IODs.** Enhanced General Equipment
   has Usage M in Segmentation and Parametric Map, making Manufacturer,
   ManufacturerModelName, DeviceSerialNumber and SoftwareVersions Type 1 there.
2. **Presence, possibly zero length, is compelled in 8 of 8.** General Equipment
   has Usage M in every class measured and carries Manufacturer at Type 2.
3. **Nothing at all is compelled in 6 of 8** for model, serial or software
   version, which are Type 3 in General Equipment.

Outside two IODs the standard compels the existence of a manufacturer string and
never compels it to mean anything. Table 2, final column.

**The restatement does not weaken the asymmetry the Discussion builds on.** That
asymmetry is in a different table: inside the Segmentation Image Module,
`SegmentAlgorithmName (0062,0009)` is Type 1C, required when the algorithm type
is not MANUAL, while `SegmentationAlgorithmIdentificationSequence (0062,0007)`,
the structured coded versioned form of the same fact, is Type 3 with no
condition. Both sit inside Segment Sequence in Table C.8.20-2 and both were
re-verified against PS3.3 2026c (STD-07). The equipment-module correction
concerns Tables C.7.5.1 and C.7.5.2 and leaves that pair untouched, so the
rationale in section 4 of the Discussion stands unaltered.

The consequence is visible in the grades, and it splits by tier. **1,363
Segmentation objects fail the Type 1 tier**: DeviceSerialNumber is absent on 966
and zero-length on 397, and dciodvfy and dicom-validator each raise a matching
message on all 1,363, splitting absent from empty exactly as the three-state
capture does (C3T-08). **40 Key Object Selection objects fail the Type 2 tier**,
with Manufacturer absent rather than merely empty. Those are the only two ways an
object in this archive can be non-conformant on carrier grounds, and between them
they account for every one of the 1,403.

The instrument's ceiling is therefore set by the standard and not by the data.
Where the standard binds, defects are found and confirmed. Where it does not,
the measurement can only report silence, and the silence is legal.

### 3.2.4 Complete is not informative

384 segments carry a complete and conformant Algorithm Identification Macro
whose three Type 1 children are all populated, and what the macro names is a
manual procedure, on segments whose own declared SegmentAlgorithmType is
AUTOMATIC (P3-10, C3T-05). PS3.3 states no relation between the two attributes,
so these objects are conformant and the contradiction is reported and not
resolved. Completeness and informativeness are separable properties, and this is
the case that separates them.

### 3.2.5 The catalogue disagrees with the object

**This is not a conformance finding and it enters no conformance rate.** No
object is non-conformant for an index that disagrees with it, because the index
is not part of the object. Its headline is **691 of 691 Parametric Map objects**,
a whole class in which the catalogue cannot name the writer and the object can.

The archive index and the object disagree about what produced the object on
**7,004 of 35,107 objects, 19.95 percent** excluding Enhanced SR, and the
disagreement runs in one direction: the index reports the writer as
unidentifiable and the object identifies it (C3T-07). Every move is decided by a
carrier the index does not expose. **Measured over the writer label derived from
`Manufacturer` and `ManufacturerModelName` together with
`ContributingEquipmentSequence` and `ImplementationVersionName`**, the
distribution by collection is two camps: 54 at 0 percent and 19 at 100 percent
of 83, with 10 between. The two carriers that make it non-trivial are
`ContributingEquipmentSequence (0018,A001)`, Type 3, and the Algorithm
Identification Macro, conditional. On the Enhanced General Equipment Type 1
attributes a comparable split would be a tautology, because 100 percent
population there is true by construction, and no bimodality is reported on
them. For Segmentation
alone the count is 1,001 objects, and the pre-registered response to a writer
label moving was to relabel and report the reallocation, never to redraw; nothing
was redrawn (P3-12).

A cohort selected on the index's writer attribution therefore rests on a weaker
reading of the object than the object itself supports.

## 3.3 Second result: floors are per-writer, not per-standard

This result stands alone and does not depend on claim 3.

Two conformant writers, given byte-identical content, draw different validator
messages, so **a floor measured on one writer does not transfer to the other**
(F1-01). A single scalar floor would silently convert the whole audit into
counting all validator messages.

**The Jaccard between the two writers' floor sets is the wrong statistic, and
the reason is sharper than a trend.** Under `dciodvfy` on SEG BINARY it is
0.0000 at baseline and ranges from 0.0000 to 0.8571 across the nine variant
rungs (B-02), oscillating rather than moving in any direction. Under
`dicom-validator` it ranges only from 0.8571 to 0.8750 (B-03). **The same
statistic is unstable under one validator and stable under the other**, which
makes it worse than a statistic that merely drifts: its value depends on which
tool is asked, so no floor can be quoted against it.

**The residue is stable under both validators**: the number of message classes
held by one writer only is **1 at all nine rungs under `dicom-validator`** and
**1 at eight rungs and 2 at V9 under `dciodvfy`** (B-10). The single departure is
V9, the deflated transfer syntax, which the pinned `dciodvfy` build cannot read
at all, and that rung is adjudicated UNDECIDABLE for exactly that reason (B-05).
Table 5, drawn on the nine rungs in Figure 4.

**The audit measures conformance as dicom3tools 2024-01-18 sees it, not
conformance.** The registered build was never satisfied and the build that ran is
the one the prior paper used. Exposure to the difference is 1,001 TILED_FULL
objects, 2.85 percent of the measured set, and zero LABELMAP objects (DEV-01).

## 3.4 Claim 2: three validators, one corpus, three answers

On the same **1,086 Grayscale Softcopy Presentation State objects** the three
validators return three different answers: **`dciodvfy` flags 1,086 of 1,086
across 172 distinct message classes, `dicom-validator` flags 0 of 1,086, and
`dcmpschk` flags 0 of 1,086** (D-04).
`dcmpschk` emits no findings at all on this class (D-01).

Direction only. No validator is adjudicated correct against another, per PRE-03.
The anchor for this claim is the manual verification sample, PRE-07, which is
deferred, so this is reported as a disagreement and not as an error rate in
either tool.

## 3.5 Claim 1: conformance, where a class is complete and adjudicated

Net rates are reported under the two-pass consensus, where a message class counts
only where both adjudication passes called it net and every disagreement drops to
UNDECIDABLE. **The consensus rate is identical to the first pass in all six
classes**, so the rates are stable under a second reading (ADJ2-03). Table 6,
with the two-pass confusion matrix and the excluded pre-disclosed classes in
Figure 5.

**Comprehensive 3D SR Storage leads it: 1,801 of 5,408 objects, 33.30 percent
net** (C-C3D-06). Three disjoint defects account for it, each with its own
verified citation: Clinical Trial Site Name and Site ID absent from an included
Type 2 module (C-C3D-01), De-identification Method absent where Patient Identity
Removed is YES (C-C3D-02), and a Referenced Study Sequence item without
Referenced SOP Class UID (C-C3D-03). **Both validators return the same net count
of 1,801**: `dciodvfy` gross 1,801 with floor 0, and `dicom-validator` gross
1,892 with floor 91, net 1,801 (C-C3D-06, C-C3D-08). The floor triple is
therefore not a rounding of the gross figure in either tool.

The class fails the pre-registered threshold on the clustering condition rather
than on the rate. PRE-05 requires both a class-level net rate above 5.0 percent
and a collection-level median above it; the class rate is 33.30 percent and the
collection-level median is **3.48 percent across five collections**, so the
conjunction fails and the finding is reported as not substantial under the rule
as registered (C-C3D-10, C-C3D-12). Changing a pre-registered rule after seeing
the data is what PRE-05 exists to prevent. The per-analysis-result breakdown is
reported instead, and it shows the defects concentrating rather than spreading:
nnu_net_bpr_annotations 1,438 of 2,906, 49.48 percent, against
lung_pet_ct_dx_annotations 38 of 1,091, 3.48 percent (C-C3D-09).

**Key Object Selection Document Storage is the only class clearing PRE-05 on
both conditions**, at 100.00 percent of its objects, and it is stated
qualitatively rather than as a headline because **n is 40**: Manufacturer is
absent from a module PS3.3 gives Usage M in that IOD, and two validators from
different codebases report it independently. Real World Value Mapping, Grayscale
Softcopy Presentation State and Parametric Map are at 0.00 percent net after
adjudication (ADJ2-03). Segmentation is absent from Table 6 because its message
classes are reported gross and have not been adjudicated, so no net rate is
quoted for it.

### 3.5.1 The pre-registered prediction was wrong

PRE-01 predicted that claim 1 would return largely null, on the reasoning that
the archive validates its own structured reports and that dcmqi wrote most of
the segmentations. Key Object Selection clears the registered threshold on both
conditions and Comprehensive 3D SR clears it on the class rate. **PRE-01 is
retired as a wrong prediction and stays in the ledger with its reason**, which
is the evidence that the interpretation was registered in advance rather than
written afterwards.

### 3.5.2 On priority

Every claim of a first in this paper is a claim of **first published
measurement**, never of first performed. Validation is a documented, routine
curation step in this archive and elsewhere; what the published record reports is
that validation was performed, not what it found. The contribution is scoped to
published rates, denominators, per-class breakdowns and cross-validator
disagreement.

## 3.6 Limitations

Each carries its bound rather than a hedge.

**Enhanced SR Storage is excluded from every object-weighted rate**, 35,161 of
262,883 series recorded and the class still running. It is 95.9 percent one
pipeline, so completing it will move object-weighted rates and will not move the
analysis-result unit the lead result is stated over.

**PRE-07 is deferred.** The manual verification sample, order 400 series read by
hand against cited Part 3 or Part 16 text, has not been run. It is the anchor for
claim 2, which is why claim 2 is reported as direction and never as an error rate
in any tool.

**TID 1500 template conformance is unmeasured.** The PixelMed jar [22] is absent
from the pinned toolchain (V-04), so the structured-report arm ran two of three
conformance tools and the template layer was not checked at all. No claim is made
about it. The reference-parse axis was also not run.

**The reliability pass is intra-instrument.** Both adjudications were produced by
the same agent under a published rule table, agreeing at kappa 0.6241 on the
binary that reaches a rate. It shows the rule table is applied reproducibly. It
does not show either reading is correct, and 147 of 2,256 message classes were
pre-disclosed and are excluded from that figure.

**The disagreement between the passes is one-directional, and the rates survive
it by luck rather than by design.** Pass 1 called net where pass 2 did not on
**212 classes; the reverse happened once** (ADJ2-02). The consensus rule
therefore discards 212 classes, and every net rate is nonetheless unchanged only
because the objects those classes flagged already carried another net class. Had
the same disagreements fallen on classes that were the sole net finding for
their objects, the consensus rates would have moved substantially. The stability
reported in Table 6 is a property of this corpus, not a property of the
consensus rule.

**The ordered rule table undercounts informativeness on two analysis-result
cells**, and the deciding values are printed in 3.2.1b so a reader can overrule
the call. Reclassifying both would move the lead result from 25 of 36 cells to
23 of 36, so the reported figure is the conservative one (FIG-03).

**Both grading passes are reported as a declared sensitivity**, 95.91 percent and
13.67 percent informative on identical objects under a permissive and a
rule-table reading (C3T-09). The rule-table reading is the one reported, its
residual is published verbatim, and a named analysis with no matching rule is
graded uninformative, so the reported figure is a lower bound on
informativeness.

**Two registered tool pins were not satisfied, each with a measured exposure.**
The dicom3tools pin: the registered build differs from the build that ran on
three changelog entries, all conditioned on LABELMAP or TILED_FULL; exposure is
zero LABELMAP objects and 1,001 TILED_FULL objects, 2.85 percent of the measured
set, and the registered build is the stricter one so a net rate is insulated
(DEV-01). `DimensionOrganizationType` was not captured for the census classes, so
that exposure is unmeasured over 691 Parametric Map objects. The highdicom pin:
exposure is zero, because no module producing a measured number uses highdicom as
an instrument and no object in the measured set was written by either version
(DEV-02).

**Segmentation message classes are gross and unadjudicated**, so no net
conformance rate is quoted for the largest class measured.

**Non-independence, and the interval that is not reported.** Series within a
collection are not independent, and the effective sample size of the
Segmentation frame is bounded by its stratum-by-collection cells rather than by
its series. **No confidence interval, standard error, variance or design effect
is reported anywhere in this paper.** Methods 2.9 registers a clustered interval
as the one that would be quoted and none was computed, so the Segmentation rates
are arithmetically correct over the objects measured and are unbounded rather
than estimated. They are never labelled population estimates. This is a
deviation from 2.9 and is declared here and in 3.7 rather than left to a reader
to notice that the word appears twice as a promise and never as a number.

**One release.** Every figure is scoped to IDC v24 and the frame is void on the
next release.

## 3.7 What this section does not report

- **No net conformance rate for Segmentation**, the largest class measured.
- **No object-weighted rate that includes Enhanced SR Storage.**
- **No axis-2 reference-parse result**, which was not run.
- **No TID 1500 template conformance**, because the PixelMed jar is absent and
  the arm did not run (V-04, P3-09).
- **No claim that either adjudication pass is correct.** The reliability check is
  intra-instrument and a second human adjudicator is outstanding.
- **No commit date or nearest tag** for the dcmqi SHAs, which need the upstream
  history and were not fetched.
- **No confidence interval, standard error, variance or design effect**, for any
  rate in this paper. Methods 2.9 describes a clustered interval as the one that
  would be quoted; none was computed. The Segmentation rates are exact over the
  objects measured and carry no bound.
- **No reclassification of the two cells where the ordered rule table matches an
  institution or a declined value before reaching a producer rule** (3.2.1b,
  FIG-03). They stay as the table decides them, the deciding values are printed,
  and the effect is stated: the undercount runs against the finding rather than
  toward it.
