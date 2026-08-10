# Methods

## 2.1 Study design and the question the design answers

This is a measurement study of a single archive release. It trains nothing,
repairs nothing and re-emits nothing. It counts.

The design separates two properties of a delivered result that are routinely
conflated: whether an object **conforms** to the standard it claims, and whether
it **attributes** itself to whatever produced it. These are independent. An
object can satisfy every stated requirement of PS3.3 [8] and say nothing about
what made it, and the study is built so that the second question can be answered
without the first being settled.

Three claims follow. Claim 3, producer attribution, is the spine. Claim 1,
conformance, is reported for the classes that are complete and adjudicated.
Claim 2, disagreement between validators, is reported as direction only.

Conformance is never scored by the authors. It is scored by third-party
validators, and where they disagree the disagreement is the datum. The one
conformance judgement the authors make is reading a Type designation out of the
standard, and every such reading carries its section and table.

## 2.2 Population, unit of analysis and what is excluded

The population is the derived, non-image SOP classes of NCI Imaging Data Commons
[6] at index version v24, read through `idc-index` [25]. Seven classes were
censused completely. Segmentation Storage, 190,146 series and 18.58 TB, was
sampled under a frame pre-registered before any object was drawn (PRE-06).

**35,107 objects are measured**: 6,386 Segmentation objects from a
5,941-series sample and seven classes censused completely (Table 1).

**Enhanced SR Storage is excluded from every object-weighted rate in this
paper**, 35,161 of 262,883 series recorded and the class still running. A
partial class read as a rate is a fabricated denominator. The exclusion is
repeated in the sentence that carries each object-weighted figure rather than
deferred to a footnote, because a reader who takes one sentence out of context
must still take the exclusion with it.

**Two units are reported and they are not interchangeable.** The
object-weighted unit is incomplete, by the exclusion above, and is distorted by
concentration: one collection supplies most of the archive. The
**analysis-result unit is complete for the seven censused classes** and is
immune to that concentration, which is why the paper's lead result is stated over
analysis results and the object-weighted figures are stated beside them rather
than instead of them. For Segmentation the cells are the identifiers observed in
the PRE-06 sample, and whether the frame holds an identifier the sample did not
draw is unmeasured (C3T-13).

**`(null)` is a residual cell, not an analysis result.** Six of the 36 cells
carry `(null)` as their identifier, holding 5,731 of 35,107 objects, 16.32
percent of the denominator, and 4 of the 6 sit inside the headline numerator. A
`(null)` cell is every object in its class to which the archive index gives no
`analysis_result_id`, so it is one bucket rather than one producer and is not
homogeneous in producer the way a named cell is. It is counted because excluding
it would drop 16.32 percent of the population out of the unit entirely, which is
the defect this replaced; the sensitivity of excluding it is reported in Results
3.2.1c (C3T-12).

## 2.3 Three grades, never two, and why presence is not measurement

Results are graded in three categories, and the middle one is the finding:

- **non-conformant**: a stated requirement of PS3.3 is violated.
- **conformant but uninformative**: everything the standard requires is present,
  and none of it identifies the producing algorithm.
- **informative**: the producer is identifiable from the object itself, by a
  value that is not a sentinel.

Two-grade reporting destroys the middle category, which is where most of this
archive sits.

**Presence is not measurement.** Enhanced General Equipment has Usage M in the
Segmentation and Parametric Map IODs, which makes Manufacturer,
ManufacturerModelName, DeviceSerialNumber and SoftwareVersions Type 1 there
(STD-04). A presence check over Type 1 attributes reports close to 100 percent
and measures nothing except that the encoder obeyed the standard. The
measurement is therefore semantic: what does the populated value **name**.

**Only a VERIFIED reading of the standard can make an object non-conformant
here**, and there are two such readings, both re-verified against PS3.3 2026c
read directly (STD-07, STD-08). **Type 1**: Enhanced General Equipment has Usage
M in two of the eight IODs measured, binding four equipment attributes, where
absent and zero length are both violations. **Type 2**: General Equipment has
Usage M in all eight and carries Manufacturer, where absent is a violation and
zero length is not. Model, serial and software version are Type 3 in General
Equipment, so their absence is legal in the other six. The asymmetry is the
standard's and it is reported as a result, not carried as a caveat.

An earlier version of this grading used the Type 1 binding alone. It produced a
contradiction inside one paper: the 40 Key Object Selection objects whose
Manufacturer is absent were graded conformant by the attribution arm while the
conformance arm called all 40 net. The Type 2 binding was added and the two now
agree.
`ImplementationClassUID` is captured and reported but never graded, because its
Type designation is not among the standards rows this project verified against a
primary source.

**Absence of a Type 3 carrier is a gap in the standard, not a defect in the
object**, and is never counted as one.

## 2.4 The classification rule, and both readings of it

Whether a populated value names a producer is decided by an ordered, published
rule table, matched over the lowercased value, first match wins. Any single
assignment can be checked by reading the value, which is printed beside it. Only
the `named_analysis` category counts as producer identity. An `encoder` writes
any analysis and identifies none; a `conversion` string says a third party
converted the object; an `application` is a viewer; an `acquisition_vendor` on a
derived object is equipment that did not produce it; an `institution` names an
organisation without naming what it ran.

The Phase 0 table was built for the two equipment attributes the archive index
carries. This study is the first to read `SegmentAlgorithmName (0062,0009)` and
the Algorithm Identification Macro at scale, and those fields carry model names
the Phase 0 table has no rule for. Extending it in place would have
retroactively moved the Phase 0 measurements, so an **additive table is
published separately** and applied only after the Phase 0 table returns
unclassified. Values declined on purpose are named. **Every value still
unclassified is published verbatim**, because a named analysis with no rule is
graded uninformative, and publishing the list is what makes that a stated
undercount rather than a silent one.

### 2.4.1 Why a third-party validator cannot adjudicate this

A validator flag was considered as an external check on the classification and
**is not used**, because probing it shows it carries no information about the
question. `dciodvfy` emits `Value dubious for this VR - PN` on person-name
values, and the check is purely syntactic: it fires on the absence of a caret.

Probed directly against dicom3tools 1.00~20240118131615 [18]:

| value | dciodvfy |
|---|---|
| `TotalSegmentator` | flagged |
| `SIEMENS` | flagged |
| `MyName` | flagged |
| `12345` | flagged |
| `ACME Corp^` | clean |
| `^TotalSegmentator` | clean |
| `Total^Segmentator` | clean |
| `Doe^Jane^^Dr^PhD` | clean |

A tool name, a manufacturer, a person and an integer are all flagged; a
manufacturer with a trailing caret and a person name are both clean. The flag
therefore separates strings that contain a caret from strings that do not, and
says nothing about whether a value names a person, an organisation or a tool.
**This table is in Methods as a mechanistic account of why no third-party
validator in the panel can adjudicate the sentinel question, not as
corroboration that one does.**

Note the probe was run against `1.00~20240118131615`, the build this study
registered, rather than the build it ran. The behaviour probed is a property of
the VR check and not of the message classes counted in Results, so nothing in
section 2.10's exposure analysis turns on it.

The classification is defended instead by what is publishable and checkable: both
rule sets are runnable code with commit history, the complete distinct-value
frequency table carries every value's label under each rule set, and both
headline figures are reported as a declared sensitivity in 2.4.2 rather than one
being presented alone.

**Personal data.** `ContentCreatorName (0070,0084)` and `OperatorsName
(0008,1070)` are PN and can carry genuine person names. The archive measured is
public and de-identified. Values in those two attributes were read only to
classify them and are reported as counts and category labels; where a distinct
value is printed verbatim in a published table it is because the classification
turns on it, and no value in the published residual is a personal name.

### 2.4.2 The grading sensitivity, declared

An earlier reading of the same objects used a permissive test, any token that is
neither a published sentinel nor a generic word. It returned **33,671 of 35,107
objects informative, 95.91 percent**, by counting a viewer string, an
acquisition vendor, an encoder sentinel and a device serial as producer
identity. The rule-table reading returns **4,799 of 35,107, 13.67 percent**
(C3T-09).

Both are published. The two differ by a factor of seven on identical objects,
which is the largest single sensitivity in this study, and it would be invisible
if only the reported figure appeared. The rule-table reading is the one
reported, it is reproducible, and its residual is published. The permissive rule
is superseded and its code is not retained, so C3T-09 records the figure rather
than a command that reproduces it, and says so.

## 2.5 The measurement panel

The panel is **not uniform across SOP classes and is never described as an
N-tool panel**. Coverage per class is given in the panel table rather than as a
single number, because a single number is the easiest claim in a paper of this
kind to falsify by opening the table.

Conformance validators: `dciodvfy` from dicom3tools [18], `dicom-validator` from
the pydicom project [20,21], `dcmpschk` from DCMTK [19] for presentation states
only.

Two declared limits on the panel, stated here rather than in limitations.
`dicom-validator` emits no severity levels and demotes any 1C or 2C condition it
cannot parse to Type 3, so it **fails open**; it is a second opinion on
conditional attributes and never a rate source. `dcmpschk` printed `Test passed.`
on a Segmentation missing two Type 1 attributes, so it is confined to the IOD it
was written for.

**PixelMed DicomInstanceValidator did not run** [22]: the jar is absent from the
pinned toolchain (V-04). For Segmentation, two of the three conformance tools
ran, recorded as NOT RUN and never as passed. The reference-parse axis was not
run in this pass and no axis-2 result is reported.

Lineage, not tool count, is what bounds independence. `dciodvfy` and PixelMed
share an author; `dcmpschk`, `dcmp2pgm` and `dsrdump` are one codebase and one
opinion (V-06).

## 2.6 Message-class normalisation, the unit of count, and exit status

Raw validator lines are never counted. Frame count is a confounder that
correlates with writer, so one logical defect over three frames would otherwise
produce six findings. Every message is reduced to a template with tag values,
UIDs, frame and item indices and quoted values stripped, hashed to a
`message_class_id`, and **the unit of count is the distinct (SOPInstanceUID,
message_class_id) pair**. Attribute names, module names and Type designations
are kept, because they identify the diagnostic rather than vary between
instances of it.

Severity is matched in **both** emitted forms: the line-start `Error - ` form,
which is the common one, and the ` - (Error|Warning) - ` form that appears in the
private-tag rendering. Matching only one silently discards findings.

**Exit status is never a verdict.** `dciodvfy` returns rc=0 on a Segmentation
with `SegmentSequence` and `Rows` deleted. Return codes are recorded and never
tested, and a static check asserts no module branches on one.

## 2.7 Adjudication, and the reliability of it

A message class becomes a **net** finding only against a cited PS3 section and
table. **Uncited is UNDECIDABLE**, by construction rather than by omission.
PRE-03 registers that where validators disagree the authors do not decide who is
right; direction is defined tool against tool.

PRE-03 and the study addenda register **two adjudicators, with any disagreement
staying undecidable**. The first pass used one adjudicator per class. A second
pass was run over all **2,256 message classes** under a published ordered rule
table, after re-reading the templates without the first pass's verdict columns.
Consensus keeps only classes both passes called net; every disagreement drops to
UNDECIDABLE, so the consensus rate can only move down and is a lower bound.

**This is an intra-instrument repeatability check, not an independent human
adjudication.** Both passes were produced by the same LLM agent. It establishes
that the rule table is applied reproducibly and it surfaces unstable classes. It
does not establish that either reading is correct and it does not satisfy the
intent of two independent adjudicators, which is two people who can disagree for
reasons the instrument cannot generate. A second human adjudicator is
outstanding.

Four disclosures, each of which weakens the check and each of which is reported
rather than absorbed:

1. **Agreement, binary first.** The only adjudication decision that reaches a
   published rate is whether a class counts toward the net numerator.
   On that binary the blind subset agrees at **89.9 percent, Cohen's kappa
   0.6241**. On the fuller three-way scale the blind subset agrees at 89.66
   percent, **kappa 0.7052** (ADJ2-01, ADJ2-02).
2. **Blindness is partial.** The project's own overnight report discloses several
   first-pass verdicts in prose, and it is required reading for the session that
   produced the second pass. **147 of 2,256 message classes** match a disclosed
   family, are flagged pre-disclosed, and are excluded from the blind figures,
   which are the ones quoted.
3. **The two passes used different vocabularies**, five terms against three: the
   first splits what the second calls floor into three cases by why the message
   is not a defect. The crosswalk is published. Comparing without it returned
   16.62 percent agreement, which measured the vocabulary and not the judgement.
4. **Two regular expressions were corrected** after the first comparison run,
   because they failed to match the text they were written for. The verdicts and
   rationales they carry were not changed, only the patterns that select them.
   This is a departure from strict blindness even though it is a coding defect.

## 2.8 The floor

A known-good object built by a conformant writer still draws validator messages,
so **a rate quoted without its floor is not a number**. Every rate is published
as a triple: gross, floor, net.

The floor is **writer-specific and does not transfer** (F1-01). It is therefore
never a scalar. It is keyed on writer, writer version, validator build, SOP class
and message class.

The **Jaccard between two writers' floor sets is the wrong statistic** and is not
reported as the headline. Across the variant ladder it is **unstable under one
validator and stable under the other**: under `dciodvfy` it oscillates between
0.00 and 0.86 with no trend, while under `dicom-validator` it sits between 0.86
and 0.88 throughout. A statistic whose value depends on which tool is asked
cannot license a floor. The **residue**, the number of message classes held by
one writer only, is stable under both (B-10). The measurement is in section 3.3,
where the table carrying it is cited.

## 2.9 Statistical treatment

Rates are reported **twice**: object-weighted, and with the collection or the
analysis result as the independent unit.

**Median and interquartile range are not reported for these distributions.** They
are two point masses, at 0 and at 100, because a collection is typically one
pipeline run and a pipeline run uses one encoder. A median reports one camp as
though it were a centre and an interquartile range of zero reads as agreement.
The **boundary counts** are given instead: how many units sit at 0, how many at
100, how many between, and which ones.

For the Segmentation sample the pre-registered estimator is stratified and
series-weighted with design weights known exactly from a complete index, and two
variances are reported beside each other: the design-based stratified form with
the finite population correction, correct for a claim about this archive
release, and a Taylor-linearised ultimate-cluster form taking the collection as
the primary sampling unit. The clustered interval is the wider and is the one
quoted.

## 2.10 Pre-registration, and every deviation from it

PRE-01 through PRE-07 were registered before the measurements they govern.
PRE-01 was **retired as a wrong prediction** and remains in the ledger with its
reason. Every deviation below is declared with a **measured bound**, and no
registration was edited after the fact.

**The dicom3tools pin was never satisfied.** Registered
`1.00~20240118131615-1`, run `20260701065818`. A pin never satisfied is a
different object from a pin changed after seeing results, and only the second is
what pre-registration exists to prevent. The build that ran is the one the prior
paper used, which buys cross-paper comparability. The two builds differ on
exactly three changelog entries, all conditioned on LABELMAP or TILED_FULL.
Measured exposure: **LABELMAP zero objects**, so one of the three entries cannot
have moved any number, and **TILED_FULL 1,001 objects, 2.85 percent of the
measured set** (DEV-01). **Direction matters as much as size**: the registered
build is the stricter one, it would emit messages the run build suppresses, and
those messages are pre-classified as floor rather than defect, so a net rate is
insulated by construction and a gross count on the exposed objects is a lower
bound. **Not measured**: `DimensionOrganizationType` was never captured for the
census classes, so TILED_FULL exposure is unmeasured over **691 Parametric Map
objects**, the only census class whose IOD can carry it.

**The highdicom pin was never satisfied.** Registered 0.28.0, installed 0.28.1
[23].
Exposure is **zero**: no module producing a measured number uses highdicom as an
instrument, and **0 of 7,100** highdicom-written objects in the measured set were
written by either version (DEV-02). Its exposure is confined to the Phase 1
floor set, where highdicom is a writer. The changelog diff between the two
releases requires network access and is unresolved; the completing command is
recorded.

**The clustered interval is not reported; the unclustered one is.** Section 2.9
specifies a stratified design-based variance and a Taylor-linearised clustered
variance and says the clustered interval is the one that would be quoted. It was
not computed, because an outcome-specific intracluster correlation cannot be
derived from the shipped artefacts, in which per-series conformance outcomes are
aggregated to the stratum. What is quoted for Segmentation, the one class drawn
as a sample, is the Wilson interval unadjusted for clustering, reported in 3.6
as a lower bound on width with the design effect implied by the frame's
registered planning value stated beside it. That planning value is not
substituted for an outcome correlation. The seven censused classes carry no
interval and need none, being complete enumerations with no sampling error.

**PRE-07 is deferred.** The manual verification sample, order 400 series
inspected by hand against cited Part 3 or Part 16 text, has not been run. It is
the anchor for claim 2, and claim 2 is reported as direction only in consequence.

**Enhanced SR Storage is excluded and named**, as in section 2.2.

**Segmentation message classes are reported gross and are not adjudicated**, so
no net conformance rate is quoted for that class.

## 2.10a Type re-verification

Every Type designation this paper relies on was re-read from **the standard
itself**, edition PS3.3 2026c [8], keyed by the table number the standard
uses, with descent into nested sequences because the two attributes the lead
finding rests on sit inside Segment Sequence rather than at module level. **17
of 17 assertions reproduce, zero failures** (STD-07). Nothing was fetched: the
DocBook and the parsed module and IOD tables are pre-seeded on the measurement
machine under PRE-04, and the DocBook neighbourhood of each load-bearing row
is published so a reader can check the parse against the text.

This was done because an earlier verification pass confirmed Types against a
third-party rendering last synchronised on 2024-04-18, roughly eight editions
stale. No Type moved. One **derived** claim did, and it is recorded as STD-08
rather than repaired silently: the ceiling sentence had been written from
Enhanced General Equipment alone and did not account for General Equipment.

**CP-2273 [10], applied to the standard at edition 2026b**, settles in PS3.5
7.4.5 [9] that a zero-length Type 3 element means the same as absence. The
present-but-incomplete cell of the
lead finding is therefore zero partly by construction of the standard and not
only by observation of these writers, and Results says which.

## 2.11 Version pinning

Reported exactly as run, in the pattern of Appendix E of the prior paper [34]
and its released harness [35]: tool binaries with the version string each
reported, the Python environment as a lockfile, the archive index version, the
dicom3tools snapshot date, the DICOM standard edition and the hardware. Where a
registered pin was not satisfied, both
the registered value and the value that ran are given, with the measured exposure
from section 2.10. `dicom-validator` was run against a pre-seeded standard path
so that no measurement depends on a network fetch at run time.

## 2.11a What is in the supplementary material

Nine items accompany this paper and each is cited where it is used: the
collection and source-DOI table (Online Resource S1), the claims ledger (Online
Resource S2), the claims map (Online Resource S3), the PRISMA-S prior-art
appendix (Online Resource S4), the DocBook text of the Segmentation tables
(Online Resource S5), the pinned environment record (Online Resource S6), the
declaration of LLM use in full (Online Resource S7), the drafted Correction
Proposal (Online Resource S8) and its status value (Online Resource S9).

## 2.12 Reproducibility and the claims ledger

Every quantitative statement that reaches this manuscript carries a row in
`results/ledger.csv` with the exact command, the source artefact, the floor it is
measured against, and what the run dropped. The ledger and the
generated-write-up discipline are carried forward from the two prior harnesses
by this author [35,37]. **A figure in the text with no ledger row fails the
build.** Withdrawn claims stay in the ledger with the reason, so a
number that was wrong cannot quietly return. Tables are generated from the
measurement artefacts and no cell is typed.

## 2.13 Declaration of LLM use

**The tool is Claude Code, the model is Claude Opus 5 with 1M context
(`claude-opus-5[1m]`), and the developer is Anthropic**, used from 2026-08-01 as
an interactive agent session with file and shell access on the author's machine.
An earlier version of this section said that tool, model and developer are named
and did not name them, which a checklist row caught by looking for the names
rather than for the heading.

They are named with the controls that make the output
checkable: independent third-party validators, a published rule table for every
classification, generated rather than typed write-ups, and the claims ledger. No
LLM output decides whether an object conforms to the standard. The second
adjudication pass was produced by the same agent as the first and is named as an
intra-instrument check in section 2.7. Errors the controls caught, and errors
they did not, are listed with the route by which each was actually found.
