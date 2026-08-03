# Conformant and uninformative: producer attribution in 35,107 AI-derived DICOM objects

## Abstract

**Background.** The archive records the serialiser and not the algorithm.
Conformance and attribution are independent properties of an AI result delivered
as a DICOM object: an object can satisfy every stated requirement of the
standard and still not record what produced it. Curation of public imaging
archives is documented and routine, but the published record reports that
validation was performed rather than what it found, and no attribute population
statistics have been published.

**Objective.** To measure, in one release of a reference public archive, whether
a derived DICOM object records the algorithm that produced it, and to report that
beside its conformance rather than merged with it.

**Methods.** Conformance and provenance census of the derived, non-image SOP
classes of NCI Imaging Data Commons v24: seven classes censused completely and
Segmentation Storage sampled under a frame pre-registered before any object was
drawn (5,941 of 190,146 series). Conformance was scored only by third-party
validators, dciodvfy and dicom-validator, never by the authors. Every validator
message was normalised to a message class and counted as a distinct
(SOPInstanceUID, message class) pair. Objects were graded in three categories,
non-conformant, conformant but uninformative, and informative, where
informativeness is decided by an ordered published rule table. Every Type
designation relied on was re-verified against PS3.3 2026c read directly. Rates
are reported both object-weighted and with the analysis result as the independent
unit.

**Results.** Of **35,107 objects**, **28,905, 82.33 percent, are conformant but
uninformative**: everything the standard requires of them is present and none of
it identifies what produced the result. One class, RT Structure Set Storage,
supplies 55.14 percent of that denominator and is 100.00 percent uninformative;
dropping it alone moves the rate to **60.62 percent uninformative and 30.47
percent informative**, which is why the analysis-result unit below is the lead
and the object-weighted rate is reported beside it rather than instead of it.
Across all 35,107, 4,799, 13.67 percent, are informative and 1,403, 4.00
percent, are non-conformant. Over the unit that is complete, producer
identity appears at **no carrier level in 25 of 36 analysis-result cells**, and a
version accompanies it in 4. The two segment-level attributes are governed
differently and are reported apart: the optional identification sequence is
absent from **34,234 of 36,488 non-MANUAL segments, 93.82 percent**, which is
legal because it is Type 3 with no condition, while the conditionally required
algorithm name is absent from **12 of the same 36,488**. Both dominant writers
record the serialiser exactly and neither records the producer: one assigns its
equipment attributes at compile time so no caller can place an algorithm in them,
and the other records its own release, six of which are present in the corpus.
The ceiling is the standard's: a non-empty equipment value is compelled in **2 of
8 IODs**, presence of a manufacturer string in **8 of 8**, and nothing about
model, serial or software version in the remaining 6.

**Reliability and limits.** A second adjudication pass over 2,256 message classes
agreed with the first at **kappa 0.6241** on the decision that reaches a rate;
the pass is intra-instrument rather than an independent human check. Both
readings of the informativeness rule are reported as a declared sensitivity,
95.91 percent and 13.67 percent. Enhanced SR Storage is excluded from every
object-weighted rate and named. Two registered tool pins were not satisfied and
each carries a measured exposure bound.

**Conclusion.** In this archive the encoder is recorded with high fidelity and
the producer is not recorded at all. The gap is permitted rather than violated:
the structured, coded, versioned carrier of algorithm identity is Type 3 while
the free-text carrier one row above it, in the same table, is Type 1C. A
Correction Proposal harmonising the two by copying the existing condition
verbatim is **{{CP_STATUS_SHORT}}**; its status is carried in the claims ledger
and is rendered from one source value rather than repeated in prose.

**Data and code.** All measurement code, the claims ledger carrying every figure
in this abstract, and the generated tables are published. Two of the three
attribute names measured here return zero hits across Europe PMC.
