# Abstract, venue form

The Journal of Imaging Informatics in Medicine asks for 150 to 250 words with no
undefined abbreviations and no unspecified references. The repository abstract,
`abstract.md`, is 695 words and carries fifteen figures with their denominators,
which is right for a preprint and is three times the limit here.

This is the abstract the submission package uses. What it drops is listed below
the rule, because a shortened abstract is a sampling decision and silent
truncation reads as full coverage.

---

**Background.** The archive records the serialiser and not the algorithm. An AI
result delivered as a DICOM object can satisfy every requirement of the standard
and still not record what produced it: conformance and attribution are
independent properties. This study measures the second in one release of a
reference archive and reports it beside the first.

**Methods.** Conformance and provenance census of the derived, non-image object
classes of the National Cancer Institute Imaging Data Commons, release 24. Seven
classes were censused completely and the segmentation class sampled under a
pre-registered frame. Conformance was scored only by third-party validators, not
by the author. Objects were graded non-conformant, conformant but uninformative,
or informative by a published rule table, and every attribute Type relied on was
re-verified against the standard.

**Results.** Of 35,107 objects, 28,905 (82.33 percent) are conformant but
uninformative: everything the standard requires is present and none of it
identifies the producer. 4,799 (13.67 percent) are informative and 1,403 (4.00
percent) are non-conformant. Producer identity appears at no carrier level in 25
of 36 analysis-result cells, the unit that is complete. The optional structured
carrier of algorithm identity is absent from 34,234 of 36,488 segments declaring
an automatic or semi-automatic algorithm; the conditionally required free-text
carrier one row above it is absent from 12.

**Conclusion.** The encoder is recorded with high fidelity and the producer is
not; the gap is permitted by the standard rather than violated. One class is
excluded from every object-weighted rate and named in the paper.

---

## What the venue form drops, and why

Each of these is in the repository abstract and in the paper, and none of it is
withdrawn. It is out of the venue abstract because 250 words will not hold it.

- **The concentration in the object-weighted rate.** One class supplies 55.14
  percent of the objects and is 100.00 percent uninformative, and dropping it
  moves the archive-wide figures to 60.62 percent uninformative and 30.47
  percent informative. This is the most important omission of the five, it is
  why the analysis-result unit is the lead, and it is in Results 3.2.1.
- **The named exclusion.** The venue form says one class is excluded and does
  not name it or give its counts. Enhanced SR Storage, 35,161 of 262,883 series
  recorded and the class still running, is named in the paper wherever an
  object-weighted figure appears.
- **The reliability pass.** Binary kappa 0.6241 on the blind subset, and the
  disclosure that the pass is intra-instrument rather than an independent human
  check.
- **The declared grading sensitivity.** 95.91 percent against 13.67 percent
  informative on identical objects under a permissive and a rule-table reading.
- **The ceiling, the mechanism and the correction proposal.** That a non-empty
  equipment value is compelled in 2 of 8 object types, that both dominant
  writers record their own release exactly, and that a Correction Proposal is
  drafted and not filed.
