# DICOM Change Proposal

Drafted against **DICOM_WG-06_CP_Template.docx**, retrieved 2026-08-03 from
https://www.dicomstandard.org/docs/librariesprovider2/dicomdocuments/dicom/wp-content/uploads/2024/09/dicom_wg-06_cp_template.docx
sha256 `eceef650aac48cbfce544e79b4be843e525e08c397ab329b01bd694058e6b1df`. The
field order below is the template's own. See `results/cp/README.md` for what
still has to happen to turn this into the submittable `.docx`, and for the
provenance of every fact asserted here.

**This proposal has not been filed.**

---

| | |
|---|---|
| **STATUS** | New |
| **Date of Last Update** | `[FIELD: 20yy/mm/dd]` |
| **Person Assigned** | *assigned by the DICOM Secretariat* |
| **Submitter Name** | `[FIELD: submitter's name and e-mail]` |
| **Submission Date** | `[FIELD: 20yy/mm/dd]` |
| **Change Number** | CP- *assigned by the DICOM Secretariat* |
| **Log Summary** | `[FIELD: short summary of the proposed change]` |
| **Name of Standard** | PS3.3 |

---

## Rationale for Change

Table C.8.20-2, Segmentation Image Module Attributes, carries two adjacent
Attributes inside Segment Sequence (0062,0002) that describe the same fact, and
gives them different Types.

- **Segment Algorithm Name (0062,0009)**, free text, is **Type 1C**, with the
  condition *"Required if Segment Algorithm Type (0062,0008) is not MANUAL."*
- **Segmentation Algorithm Identification Sequence (0062,0007)**, the
  structured, coded and versioned form of the same fact, is **Type 3** with no
  condition of any kind.

The second row is directly below the first in the same table. The proposal is to
attach the condition the table already contains to the second row as well, so
that the two rows are governed alike.

**This is a harmonisation, not a new requirement.** No new concept, code,
Attribute or condition text is introduced. The condition is copied verbatim from
the row above, and the trigger Attribute it names, Segment Algorithm Type
(0062,0008), is already Type 1 in the Segment Description Macro included by this
same table, so every Instance affected already carries the value the condition
tests.

### The proposed wording already exists in the Standard, for this Attribute

Table C.8.20-5, Height Map Segmentation Image Module Attributes, already
specifies Segmentation Algorithm Identification Sequence (0062,0007) as **Type
1C** with the condition *"Required if Segment Algorithm Type (0062,0008) is not
MANUAL."*

The same Attribute, under the same condition, at the same Type, is therefore
already normative in a sibling Segmentation module. The present proposal asks
that Table C.8.20-2 be brought into line with Table C.8.20-5 rather than that
new language be written. The one difference between the two rows is left
untouched: Table C.8.20-5 permits a single Item and Table C.8.20-2 permits one or
more, and this proposal does not change the Item cardinality in either table.

### Evidence that the two rows behave differently in practice

A census of the derived, non-image SOP Classes of one public archive release, NCI
Imaging Data Commons v24, measured both Attributes over the same Segments. This
is offered as evidence of what the difference in Type produces, not as an
argument that any Instance is defective. **Omitting a Type 3 Attribute is legal
and no validator can flag it.**

Over 36,488 Segments declaring Segment Algorithm Type (0062,0008) as AUTOMATIC
or SEMIAUTOMATIC, drawn from a pre-registered sample of 5,941 of 190,146
Segmentation series:

| Attribute | Type in Table C.8.20-2 | Absent |
|---|---|---|
| Segment Algorithm Name (0062,0009) | 1C | **12** of 36,488, 0.03 percent |
| Segmentation Algorithm Identification Sequence (0062,0007) | 3 | **34,234** of 36,488, 93.82 percent |

Where the Standard states a condition, encoders satisfy it almost everywhere.
Where it does not, the structured carrier is generally not written. No Segment in
the measured set carried the Sequence present but incomplete, which is consistent
with CP-2273 settling in PS3.5 Section 7.4.5 that a zero length Type 3 Element
means the same as absence.

### Prior actions on this table

Three Correction Proposals have edited this material and left all three
Attributes at their existing Types:

- **CP-1258**, *Refactor segment description, extend segment types and anatomy*,
  Parts 3 and 16, applied at edition 2011.
- **CP-1597**, *Clarify Segmentation Algorithm Parameters*, Part 3, applied at
  edition 2016d.
- **CP-2115**, *Per-segment multiple algorithms and creators*, Part 3, applied at
  edition 2021d.

**Supplement 243, Label Map Segmentation**, Final Text 2024-09-14, applied at
edition 2024c, carries tracked edits to Tables C.8.20-1 through C.8.20-4,
including both the module table holding these two rows and the macro holding the
Attribute their condition names. It left (0062,0008) at Type 1, (0062,0009) at
Type 1C and (0062,0007) at Type 3, changing only the capitalisation of the word
Segment in their descriptions.

### The Working Group's recent pattern, stated rather than argued against

Two recent actions add algorithm provenance at Type 3:

- **CP-2428**, *Add Algorithm Identification to RT Dose Module*, Parts 3, 6 and
  16, applied at edition 2025c, includes the Algorithm Identification Macro into
  the RT Dose Module and makes every added Attribute Type 3.
- **CP-2320**, *Communication that data is synthetic*, Part 3, applied at edition
  2024a, is also Type 3.

This proposal does not ask the Working Group to depart from that pattern. It does
not propose that algorithm provenance be required where the Standard is silent.
It proposes only that where the Standard has **already** stated a condition, in
this table, on this trigger Attribute, the two adjacent rows expressing the same
fact be governed by it alike.

### Impact on existing Instances

Stated because it is the first question this change raises, and because the
census measures it directly.

Instances written before this change that carry non-MANUAL Segments without
Segmentation Algorithm Identification Sequence (0062,0007) would not satisfy the
amended Table C.8.20-2. In the measured sample that is 34,234 of 36,488
non-MANUAL Segments. The corresponding figure for the whole archive is not
measured, because the sample is a sample, and the sampling frame is published.

Two observations bear on how much that matters, and the Working Group is better
placed than the submitter to weigh them:

1. The same exposure already exists for Table C.8.20-5, whose 1C form of this
   Attribute is in the Standard now.
2. The condition constrains only Instances whose own Segment Algorithm Type
   (0062,0008) declares the Segment was not produced by hand.

---

## Change Wording

> **Instruction**
>
> Modify PS3.3 Table C.8.20-2, Segmentation Image Module Attributes, as
> indicated (changes to existing text are **bold and underlined** for additions
> and **bold and struckthrough** for removals).

Row shown in context with the row above it, which is unchanged and is reproduced
here only to show that the condition being copied is the adjacent one.

| Attribute Name | Tag | Type | Attribute Description |
|---|---|---|---|
| \>Segment Algorithm Name | (0062,0009) | 1C | The name(s) of algorithm(s) used to generate the Segment. Required if Segment Algorithm Type (0062,0008) is not MANUAL. |
| \>Segmentation Algorithm Identification Sequence | (0062,0007) | ~~**3**~~ <ins>**1C**</ins> | A description of how this Segment was derived. Algorithm Name (0066,0036) within this Sequence may be identical to Segment Algorithm Name (0062,0009). <ins>**Required if Segment Algorithm Type (0062,0008) is not MANUAL.**</ins> One or more Items are permitted in this Sequence. Previously, the Segment Surface Generation Algorithm Identification Code Sequence (0066,002D) was used, but it has been replaced in this Module, since not all segmentation algorithms involve surface generation. See PS3.3-2016d. |

**Two notes on the wording, for the editor.**

1. The added sentence is placed after the sentence beginning *"Algorithm Name
   (0066,0036) within this Sequence may be identical..."* rather than at the end
   of the description. That is the position the same condition occupies in the
   corresponding row of Table C.8.20-5, so the two rows read alike.

2. Nothing else in the description is altered. The Item cardinality sentence and
   the historical note referring to Segment Surface Generation Algorithm
   Identification Code Sequence (0066,002D) are reproduced unchanged.

---

## What this proposal does not ask for

- It does not add an Attribute, a code, a coding scheme or a Context Group.
- It does not change Segment Algorithm Type (0062,0008), which stays Type 1, or
  Segment Algorithm Name (0062,0009), which stays Type 1C.
- It does not change Table C.8.20-5, which already carries the proposed form.
- It does not change the Item cardinality of (0062,0007) in either table.
- It does not propose that any provenance Attribute be required where the
  Standard states no condition.
