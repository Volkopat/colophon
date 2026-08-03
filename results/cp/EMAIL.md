# The filing email, prepared and not sent

**Nothing here has been sent.** Sending is the author's. The status this email
would change is `results/cp/status.json`, and changing it is what updates the
Discussion, the abstract and the supplementary index.

## Address

| | |
|---|---|
| To | `dicom@dicomstandard.org` |
| Source | the DICOM Secretariat address recorded in the Discussion and at ledger row CPD-01 |
| Attachment | the WG-06 template, filled from `cp_segmentation_algorithm_identification.md`, saved as `.docx` |
| Filename | `cpXXXX_01_HarmoniseSegAlgIdentSeqType.docx`, where the number is assigned on receipt |

## Subject

    Correction Proposal submission: harmonise the Type of Segmentation Algorithm
    Identification Sequence (0062,0007) with Segment Algorithm Name (0062,0009)
    in Table C.8.20-2

## Body

> Dear DICOM Secretariat,
>
> I am submitting a Correction Proposal for consideration by WG-06, attached in
> the WG-06 template.
>
> **What it proposes.** Table C.8.20-2, the Segmentation Image Module, gives
> Segment Algorithm Name (0062,0009) as Type 1C, required if Segment Algorithm
> Type (0062,0008) is not MANUAL. The row immediately below it, Segmentation
> Algorithm Identification Sequence (0062,0007), which is the structured, coded
> and versioned form of the same fact, is Type 3 with no condition. The proposal
> attaches the condition the table already contains to the second row as well,
> copied verbatim from the row above.
>
> **It introduces no new language.** Table C.8.20-5, the Height Map Segmentation
> Image Module, already specifies (0062,0007) as Type 1C under exactly that
> condition. The proposal asks that Table C.8.20-2 be brought into line with a
> form the Standard already contains for the same Attribute, rather than that
> new wording be written. The Item cardinality is not changed in either table.
>
> **Evidence, offered as evidence and not as advocacy.** A census of the derived
> non-image SOP Classes of one public archive release measured both Attributes
> over the same Segments. Over 36,488 Segments declaring AUTOMATIC or
> SEMIAUTOMATIC, the conditionally required free-text Attribute is absent from
> 12, and the optional structured Attribute is absent from 34,234. Omitting a
> Type 3 Attribute is legal and no validator can flag it; the proposal describes
> no Instance as defective.
>
> **Backwards compatibility is stated in the proposal rather than omitted.** In
> the measured sample, 34,234 of 36,488 non-MANUAL Segments would not satisfy the
> amended table. The same exposure already exists for Table C.8.20-5.
>
> **Prior actions on this table are cited.** CP-1258, CP-1597 and CP-2115 each
> edited this material and left the Types unchanged, and Supplement 243 carried
> tracked edits to Tables C.8.20-1 through C.8.20-4 and left all three algorithm
> rows at their existing Types. The proposal also records that CP-2428 and
> CP-2320 show the Working Group adding AI provenance at Type 3, and it does not
> ask the Working Group to depart from that pattern.
>
> The measurement behind the evidence is being submitted for publication
> separately. The proposal stands on the asymmetry in the table rather than on
> that paper.
>
> `[FIELD: name]`
> `[FIELD: affiliation and e-mail]`

## After sending

1. Set `state` in `results/cp/status.json` to `filed_awaiting_number` and fill
   `filed_on`.
2. Re-run `python -m colophon.submission`. The Discussion, the abstract and the
   supplementary index change together, because all three render from that value.
3. When a number is assigned, set `state` to `assigned` and fill `number` and
   `status`.
4. Update ledger row CPD-04, which is PENDING until then.
