# Introduction

An AI result delivered as a DICOM object carries two properties that are
routinely treated as one. It either **conforms** to the Information Object
Definition it claims, or it does not. And it either **attributes** itself to
whatever produced it, or it does not. These are independent. An object can
satisfy every stated requirement of PS3.3 [8] and say nothing about what made
it, and nothing in the standard makes that a defect.

This paper measures the second property in the archive that has become the
reference corpus for AI-derived medical imaging, and reports it beside the
first.

## The genre, before the substrate

Auditing what a repository records about the provenance of what it holds is an
established genre with a consistent result. Longpre et al [1] audited dataset
licensing and attribution across more than 1,800 datasets and found licence
information omitted in over 70 percent of them. Huang et al [2] measured
metadata completeness in the Gene Expression Omnibus and reported the same shape
of gap in a different substrate.

**What differentiates this study is the substrate, not the question.** Their unit
is a free-text card in a repository with no formal conformance definition, so
"incomplete" is a judgement the auditors must define and defend. Our unit is a
**typed attribute inside a binary format with a normative Type system and
third-party validators**, so conformance is defined by a standards body and
scored by tools written by other people. That is what makes a three-grade split
possible at all: an object can be non-conformant, or conformant and
uninformative, or informative, and the middle grade is available only because
somebody else already fixed what "conformant" means.

## What has and has not been measured in this archive

Validation and curation of this archive are documented and routine. Clark et al
[3] describe the curation pipeline, Prior et al [4] and Bennett and Smith [5]
describe the quality-control steps, and Fedorov et al [6] describe the
conversion and validation of derived objects. **In every case the published
record reports that validation was performed, not what it found.** No attribute
population statistics appear.

Every claim of a first in this paper is therefore a claim of **first published
measurement, never of first performed**. The contribution is scoped to published
rates, denominators, per-class breakdowns and cross-validator disagreement.

Two of the three DICOM attribute names this study measures return **zero hits
across the whole of Europe PMC**, and the third returns two, neither of which
reports a population or a rate over it (PA-10).

The nearest same-archive study asks a different question. Krishnaswamy et al [7]
evaluate the AI-generated annotations themselves: **they ask whether the mask is
right, we ask whether you can tell who made it.** Both matter and neither
substitutes for the other, because a correct mask of unknown provenance is not
reusable evidence.

## What this paper does

It reports a conformance and provenance census of the derived, non-image SOP
classes of one archive release: seven classes censused completely and one
sampled under a frame pre-registered before any object was drawn. Conformance is
scored only by third-party validators, and where they disagree the disagreement
is reported as direction rather than resolved. Every rate is published as a
triple of gross, floor and net, because a known-good object drawn by a
conformant writer still trips a validator and a rate quoted without its floor is
not a number.

The result is that the encoder is recorded with high fidelity and the producer is
not recorded at all, and that the ceiling on how much better this could be is set
by the standard rather than by the archive or by anyone who wrote to it.
