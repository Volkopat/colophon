# The second adjudication pass, and the agreement between the two

PRE-03 and addendum 02 section 5 register **two independent adjudicators, with
any disagreement staying undecidable**. The first pass used one adjudicator per
class. This is the second, reported beside the first rather than replacing it.
Reproduce with `python -m colophon.adjudicate2`.

## What this is, and what it is not

The second pass was performed by **the same LLM agent** that produced the first,
under the ordered rule table published in `colophon/adjudicate2.py`, after
re-reading the message templates without the first pass's verdict columns.

That makes it an **intra-instrument repeatability check, not an independent
human adjudication**. It establishes that the rule table is applied reproducibly
and it surfaces the classes where the reading is unstable. It does **not**
establish that either reading is correct, and it does not satisfy the intent of
two independent adjudicators, which is two people who can disagree for reasons
the instrument cannot generate. Methods carries that sentence and not a weaker
one.

**Blindness is partial, and the compromise is measured.** `MORNING_REPORT.md` is
part of the session's required reading and it discloses several first-pass
verdicts in prose. **147 of 2,256
message classes** match a disclosed family and are flagged `PRE_DISCLOSED`.
Agreement is reported over all classes and over the blind subset separately, and
the blind figure is the one to quote.

**Two regexes were corrected after the first comparison run.** Both failed to
match the text they were written for: the functional-group message says
`is unexpected` where the rule said `is missing`, and a literal `>` had been
written `)`. The verdicts and rationales those rules carry were not changed, only
the patterns that select them. Recorded because it is a departure from strict
blindness even though it is a coding defect rather than a revision of judgement.

## The two scales, and the crosswalk between them

The passes used different vocabularies, which is itself a result of running two.
The first has five terms and the second three: the first splits what the second
calls floor into three cases, by **why** the message is not a defect.

| first pass | second pass | meaning |
|---|---|---|
| `FLOOR` | `FLOOR` | a floor class, legal by a cited section |
| `NOT-IOD` | `FLOOR` | not a requirement of this object's IOD at all |
| `PLAUSIBILITY` | `FLOOR` | a heuristic of the validator's own, citing no Type and no condition |
| `NET` | `NET` | a genuine defect against a cited requirement |
| `UNDECIDABLE` | `UNDECIDABLE` | not adjudicable from the object and the text |

All three of the first pass's exclusion terms mean the same thing for any rate:
the class does not count toward a net numerator. The crosswalk is published here
rather than applied silently. Comparing on the second pass's coarser scale
without it measured the vocabulary rather than the judgement, and returned an
agreement of 16.62 percent that meant nothing.

## Agreement

| comparison | classes | agreement | Cohen's kappa |
|---|---|---|---|
| three-way, crosswalked, all classes | 2,256 | 84.35 percent | 0.5929 |
| three-way, crosswalked, **blind subset** | 2,109 | 89.66 percent | **0.7052** |
| counts toward the net numerator, all classes | 2,256 | 90.56 percent | 0.6352 |
| counts toward the net numerator, **blind subset** | 2,109 | 89.9 percent | **0.6241** |

The net-relevant binary is the comparison that matters, because it is the only
decision that reaches a published rate. Everything else is a difference in how an
exclusion is explained.

## Where the two passes disagree

| family | pass 1 | pass 2 | message classes | object hits |
|---|---|---|---|---|
| `Module <SR Document Content> (TAG) (Content Sequence) [xN] / (TAG) (Referenced SOP Seq` | FLOOR | UNDECIDABLE | 2 | 1,548 |
| `Module <SR Document Content> (TAG) (Content Sequence) [xN] / (TAG) (Referenced SOP Seq` | FLOOR | UNDECIDABLE | 2 | 1,444 |
| `Warning - Unrecognized defined term <RP-101030> for value 1 of attribute <Coding Schem` | UNDECIDABLE | FLOOR | 1 | 462 |
| `Error - DisplayedAreaSelectionSequence is internally inconsistent - DisplayedAreaTopLe` | FLOOR | UNDECIDABLE | 111 | 128 |
| `Module <SR Document Content> (TAG) (Content Sequence) [xN] / (TAG) (Measured Value Seq` | NET | UNDECIDABLE | 1 | 4 |
| `Module <SR Document Content> (TAG) (Content Sequence) [xN] / (TAG) (Measured Value Seq` | NET | UNDECIDABLE | 1 | 3 |
| `Module <SR Document Content> (TAG) (Content Sequence) [xN] / (TAG) (Measured Value Seq` | NET | UNDECIDABLE | 1 | 3 |
| `Module <SR Document Content> (TAG) (Content Sequence) [xN] / (TAG) (Measured Value Seq` | NET | UNDECIDABLE | 1 | 2 |
| `Module <SR Document Content> (TAG) (Content Sequence) [xN] / (TAG) (Measured Value Seq` | NET | UNDECIDABLE | 1 | 2 |
| `Module <SR Document Content> (TAG) (Content Sequence) [xN] / (TAG) (Measured Value Seq` | NET | UNDECIDABLE | 1 | 2 |
| `Module <SR Document Content> (TAG) (Content Sequence) [xN] / (TAG) (Measured Value Seq` | NET | UNDECIDABLE | 1 | 2 |
| `Error - Bad attribute Value Multiplicity Type 3 Optional Element=<ProcedureCodeSequenc` | UNDECIDABLE | NET | 1 | 2 |
| `Module <SR Document Content> (TAG) (Content Sequence) [xN] / (TAG) (Measured Value Seq` | NET | UNDECIDABLE | 1 | 2 |
| `Module <SR Document Content> (TAG) (Content Sequence) [xN] / (TAG) (Measured Value Seq` | NET | UNDECIDABLE | 1 | 2 |

The dominant disagreement is principled rather than an oversight. The first pass
adjudicated several `dicom-validator` findings inside SR content sequences as
net. The second pass declines them, because addendum 02 section 2 registers that
dicom-validator 0.8.2 emits no severity levels and demotes any 1C or 2C
condition it cannot parse to Type 3, so it **fails open** and is registered as a
second opinion rather than a rate source. Under the registered rule the
disagreement drops to undecidable and the class leaves the numerator.

## Net rates under each pass and under the consensus

A class counts toward the numerator only where **both** passes called it net.
Every disagreement drops to undecidable and is excluded, so the consensus rate
can only move down. That is the conservative direction and it is what a
two-adjudicator design is for.

| SOP class | objects | net, pass 1 | percent | net, pass 2 | percent | net, consensus | percent |
|---|---|---|---|---|---|---|---|
| Real World Value Mapping Storage | 20 | 0 | 0.00 | 0 | 0.00 | **0** | **0.00** |
| Key Object Selection Document Storage | 40 | 40 | 100.00 | 40 | 100.00 | **40** | **100.00** |
| Grayscale Softcopy Presentation State Storage | 1,086 | 0 | 0.00 | 0 | 0.00 | **0** | **0.00** |
| Parametric Map Storage | 691 | 0 | 0.00 | 0 | 0.00 | **0** | **0.00** |
| Comprehensive SR Storage | 2,118 | 723 | 34.14 | 723 | 34.14 | **723** | **34.14** |
| Comprehensive 3D SR Storage | 5,408 | 1,801 | 33.30 | 1,801 | 33.30 | **1,801** | **33.30** |

The collection-level boundary counts PRE-05 condition (b) needs are in
`results/adjudication2/net_rates_two_pass.csv`, as counts at 0 and at 100 rather
than as a median.

## What this changes and what it does not

- **No first-pass verdict was edited.** Both adjudications are published side by
  side in `results/adjudication2/two_pass_comparison.csv`, one row per message
  class, with both citations.
- **No net rate should be quoted from a single pass now that two exist.** The
  consensus column is the one PRE-03 licenses.
- **The check is intra-instrument.** A second human adjudicator is still
  required and is still outstanding, and that is stated in Methods rather than
  in limitations.
