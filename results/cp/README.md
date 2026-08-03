# results/cp

One drafted DICOM Correction Proposal, and everything needed to check it.

**Status: drafted, ready, not filed.** Nothing in this directory has been sent to
anyone. Filing is a deliberate act by the author, and if it happens the
submission date, the assigned CP number and the disposition are carried in
`results/ledger.csv` and updated there.

| file | what it is |
|---|---|
| `cp_segmentation_algorithm_identification.md` | the proposal, in the field order of the WG-06 CP template |

## The template it follows

| | |
|---|---|
| name | DICOM_WG-06_CP_Template.docx |
| source | https://www.dicomstandard.org/resources/templates |
| url | https://www.dicomstandard.org/docs/librariesprovider2/dicomdocuments/dicom/wp-content/uploads/2024/09/dicom_wg-06_cp_template.docx |
| retrieved | 2026-08-03 |
| sha256 | `eceef650aac48cbfce544e79b4be843e525e08c397ab329b01bd694058e6b1df` |

Its field order, which the draft reproduces: STATUS, Date of Last Update, Person
Assigned, Submitter Name, Submission Date, Change Number, Log Summary, Name of
Standard, Rationale for Change, Change Wording.

Note the template's own field is **Change Wording**, not Correction Wording. The
draft uses the template's spelling.

## Fields left for the submitter

Four, and they are the four nobody else can supply:

| field | why it is not filled |
|---|---|
| Submitter Name | the submitter's name and e-mail address |
| Submission Date | the date the proposal is actually sent |
| Date of Last Update | the same, on the version sent |
| Log Summary | one line, and it becomes the document title in the file listing |

Two further fields are filled by the DICOM Secretariat rather than by anyone
here: **Person Assigned** and **Change Number**.

## To turn this into the submittable document

The draft is markdown because everything else in this repository is. The
Secretariat receives a `.docx`. Four things the template requires that markdown
cannot carry:

1. **Build it in the template file itself**, not in a fresh document. The Log
   Summary is a Word field, and the template says in terms that it is edited
   through *Edit Field* rather than retyped.
2. **Take the existing Standard text from the Word version of PS3.3**, not from
   the HTML, the PDF or from this repository. The template says this explicitly,
   because copying from HTML breaks the Standard's styles. It matters here for
   one specific reason: the description of (0062,0007) ends in a cross-reference
   whose link text does not survive plain-text extraction, so the last sentence
   reads `See PS3.3-2016d.` in this draft and must be taken from the Word source
   in the document that is sent.
3. **Tracked-edit formatting**: additions bold and underlined, removals bold and
   struck through. The markdown draft marks these with `<ins>` and `~~`, which is
   a stand-in for the formatting and not the formatting.
4. **Line numbering on**, per the template's instruction.

File naming, from the template: `cpnnnn_xx_title.docx`, where `nnnn` is the CP
number the Secretariat assigns, `xx` is a two-digit version starting `01`, and
`title` is an abbreviated title with no spaces. So the first version of this one
would be `cpNNNN_01_HarmoniseSegAlgIdentSeqType.docx` once a number exists.

## How it is sent

To the DICOM Secretariat at `dicom@dicomstandard.org`. No membership, sponsor or
fee is required. The process is described at
https://www.dicomstandard.org/process.

## Provenance of every fact asserted in the draft

Nothing in the proposal is asserted from memory. Each row below names where the
fact was read and, where one exists, the ledger row that carries it.

| fact in the draft | source | ledger |
|---|---|---|
| (0062,0009) is Type 1C in Table C.8.20-2 with the condition quoted | PS3.3 2026c DocBook, `results/typecheck/segment_tables_verbatim.md` row 18 | STD-07 |
| (0062,0007) is Type 3 in Table C.8.20-2 with no condition | same, row 19 | STD-07 |
| (0062,0008) is Type 1 in the Segment Description Macro, Table C.8.20-4 | same, Table C.8.20-4 row 04 | STD-07 |
| (0062,0007) is **already Type 1C** in Table C.8.20-5 with exactly the proposed condition | same, Table C.8.20-5 rows | STD-07, and `TYPECHECK.md` row 4 |
| Table C.8.20-5 permits a single Item where C.8.20-2 permits one or more | same | STD-07 |
| 34,234 of 36,488 non-MANUAL Segments carry no identification sequence | `results/phase3/` | P3-01 |
| 12 of 36,488 non-MANUAL Segments omit (0062,0009) | `results/phase3/` | P3-05 |
| no Segment carries the sequence present but incomplete | `results/phase3/` | P3-02 |
| the sample is 5,941 of 190,146 series | pre-registered frame | PRE-06 |
| CP-2273 settles zero length Type 3 in PS3.5 7.4.5 | DICOM status table | PA-11, reference 10 |
| CP-1258, CP-1597, CP-2115 left the Types unchanged | DICOM status table, titles and editions verbatim | PA-11, references 14 to 16 |
| CP-2428 and CP-2320 add provenance at Type 3 | DICOM status table | PA-11, references 12 and 13 |
| Supplement 243 is Final Text 2024-09-14, applied at edition 2024c, and left all three Types unchanged | the supplement PDF and the DICOM status table | STD-10, reference 11 |

## What the draft deliberately does not do

- It does not argue that provenance ought to be mandatory. Ledger row PA-11 and
  the Discussion both record that WG-06's recent pattern adds AI provenance at
  Type 3, and an argument against that pattern is not the argument being made.
- It does not describe any Instance in the archive as defective. Omitting a Type
  3 Attribute is legal, and the draft says so in the sentence that introduces the
  measurement.
- It does not name a producing group, a collection or an analysis result. The
  evidence is reported in aggregate, as everywhere else in this project.
- It does not predict an outcome. Observed disposition of comparable proposals
  ranges from months to years, and a proposal may sit in Assigned indefinitely.
