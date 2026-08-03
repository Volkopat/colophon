# Discussion

## The finding, and the two places it was already written down

The archive records the serialiser precisely and the producer not at all. That is
not a discovery about carelessness. It is what the format compels, and two
documents say so in other people's words.

**IHE AIR Rev 1.3, Vol 1, Closed Issue 26, printed page 17** [17], verbatim:
*"Many deployment models involve the AI Models being separate from the Evidence
Creator (which would appear in General Equipment) that packages their results."*
The standards body wrote the thesis of this paper down as an expectation, and the
expectation was never checked against a corpus.

**Project-MONAI/monai-deploy-app-sdk Discussion 528** [26] is the only public
place anyone has hit the wall from the writing side: the DICOM SEG writer
hardcodes manufacturer details while the SR and PDF writers in the same SDK
accept a configurable `ModelInfo`. The asymmetry is in one toolkit, between
two of its own writers.

Our mechanism section measures the same thing from the reading side. dcmqi [24]
assigns its equipment attributes at compile time from a constants header, so no
caller can place a producing algorithm in them; highdicom [23] records its own
release exactly. Both are working as designed and neither is doing anything wrong.

**The loose form of the claim is false and the counterexample matters.**
Producers do sometimes route identity into whatever slot survives. Murugesan
et al [27] populate `SegmentAlgorithmName` with model identity, and our own
measurement finds the same: the TotalSegmentator collection carries
`TotalSegmentator v1.5.6` in `SegmentAlgorithmName`, which is level 4, and a
matching string in `SeriesDescription`, which is level 3. Identity therefore
**first** appears at level 3 and appears again at level 4, and Table 3 reports
both the first level and every level at which it appears so the two cannot be
confused. The correct statement is not that producers never record identity.
It is that **where the standard compels a name they supply one, and where it
does not the name is usually absent**, which is why the two attributes have to
be reported apart.

## Two camps, not a spread

The nearest structural analogue is Balliu et al [28], who ran six software
bill-of-materials producers over identical inputs and reported precision from
roughly 50 to 96 percent. That is a **spread**: producers differ by degree.

What we observe is not a spread. Measured over **what `Manufacturer` and
`ManufacturerModelName` name**, rather than over whether they are populated,
which is fixed by construction in two of the eight IODs, the encoder-only share
by collection is **44 collections at 0 percent, 25 at 100 percent and 14 between,
of 83** (C3T-02). The writer-attribution measurement behaves the same way: **54
at 0 percent, 19 at 100 percent and 10 between, of the same 83** (C3T-07). A
collection is one pipeline run and a pipeline run uses one encoder, so the
outcome is a property of the toolkit rather than of the study. Figure 6 draws
all 83 collections as points, which is what makes the two masses visible. This is why no median is reported for these distributions anywhere in
this paper: a median would report one camp as though it were a centre.

## The ceiling, and a correction that follows from it

The instrument's ceiling is set by the standard. A non-empty equipment value is
compelled in two of the eight IODs measured, mere presence of a manufacturer
string is compelled in all eight, and nothing at all is compelled about model,
serial or software version in the other six. That statement is derived from the
IOD module tables of PS3.3 2026c [8] read directly, which makes it the most
defensible thing in this paper: it is not a classification of ours.

Inside the Segmentation Image Module the same asymmetry appears one level down,
and it is sharper. `SegmentAlgorithmName (0062,0009)` is **Type 1C, "Required if
Segment Algorithm Type (0062,0008) is not MANUAL"**. One row away,
`SegmentationAlgorithmIdentificationSequence (0062,0007)`, which is the
structured, coded, versioned form of the same fact, is **Type 3 with no condition
of any kind**. Both were re-verified against PS3.3 2026c for this paper, and both
sit inside Segment Sequence in the same table. The consequence is measured: the
attribute carrying the condition is omitted on 12 of 36,488 non-MANUAL segments,
and the attribute carrying none is omitted on 34,234 of the same 36,488.

The process of measuring this led to the development of the following correction
proposal.

The condition already exists in the standard; it is simply attached to the
weaker of the two attributes. A correction harmonising them would copy the
existing condition text verbatim from the row above rather than invent language,
so that `SegmentationAlgorithmIdentificationSequence` would read *Required if
Segment Algorithm Type (0062,0008) is not MANUAL*. Nothing in that requires a new
concept, a new code or a new attribute.

Two facts belong beside it. **Supplement 243, Label Map Segmentation, Final Text
2024-09-14, applied to the standard at edition 2024c [11], carries tracked edits
to Tables C.8.20-1 through C.8.20-4, including both
the module table that holds these two rows and the macro that holds the attribute
their condition names, and left all three at their existing Types**: (0062,0008)
Type 1, (0062,0009) Type 1C and (0062,0007) Type 3, changing only the
capitalisation of the word segment in their descriptions (STD-10). The most
recent revision of these tables had both rows open in front of it and walked past
the asymmetry. And WG-06's recent pattern runs the other way: **CP-2428 [12]
includes the Algorithm Identification Macro into the RT Dose Module and makes
every added attribute Type 3, and CP-2320 [13], the AI-provenance precedent, is
also Type 3.** When this committee adds AI provenance it adds it optionally. An
argument that provenance ought to be mandatory would run against that pattern;
an argument for harmonising two rows of one table with a condition the table
already contains does not.

A search of the complete numbered Correction Proposal series, CP-1 to CP-2649,
found no proposal promoting a provenance attribute from Type 3 to conditional
(PA-11). The nearest prior actions on this table, CP-1597 [14], CP-1258 [15] and
CP-2115 [16], each left the Type unchanged.

**{{CP_STATUS}}** The mechanism requires no membership, sponsor or fee: the
completed WG-06 template is sent to the DICOM Secretariat at
`dicom@dicomstandard.org`. That sentence is not typed here: it is rendered from
`results/cp/status.json`, which holds one value with three states, so filing the
proposal changes one JSON key rather than three passages of prose. The status is
carried in the claims ledger and updated there. The outcome of
such a proposal is not predictable: observed disposition of comparable
proposals ranges from about 7.5 months to over eight years, and a proposal may
also sit in Assigned indefinitely. We describe it here because it was a byproduct
of the measurement, in the register of Fedorov et al [29], who embedded the
corrections that arose from their own encoding work inline in their Methods
rather than in a section arguing for them.

## What this paper does not establish

It does not establish that either adjudication reading is correct. The
reliability pass is intra-instrument, by the same agent under a published rule
table, and reports binary kappa 0.6241 on the blind subset. A second human
adjudicator would be the honest next instrument and is not available to a sole
author.

It does not establish anything about DICOM practice beyond this archive release.
The estimator is scoped to a finite population and the effective sample size is
bounded by the number of stratum-by-collection cells rather than by the number of
series.

It does not establish that a standards change would follow from a measurement.
Three commonly asserted chains from measurement paper to standards change fail at
primary source: RFC 8461 [30] does not cite the study usually credited for it,
RFC 8996 [31] cites no empirical deployment measurement, and RFC 7919 [32] does
not cite the Logjam paper [33]. The one traceable pattern is the Fedorov one
[29], where the authors filed the paperwork themselves and the paper recorded
that they did. This paper
records a drafted proposal and will record its filing if and when that happens;
it claims no influence either way.

## Conclusions

In one release of the archive that has become the reference corpus for
AI-derived medical imaging, **28,905 of 35,107 objects, 82.33 percent, are
conformant but uninformative**, and over the unit that is complete producer
identity is absent at every carrier level in 25 of 36 analysis-result cells. The
gap is permitted rather than violated: both dominant writers record the
serialiser exactly and neither records the producer, and the structured, coded,
versioned carrier of algorithm identity is Type 3 while the free-text carrier one
row above it in the same table is Type 1C. Conformance and attribution therefore
have to be measured and reported apart, because an archive can sit at its
conformance ceiling and still not say what made anything in it. The correction
that follows from the measurement is a harmonisation rather than a new mandate,
it copies a condition the same table already contains, and it is
**{{CP_STATUS_SHORT}}**.
