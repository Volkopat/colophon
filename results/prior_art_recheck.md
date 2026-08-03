# Prior art recheck and targeted finding sweeps, searched 2026-08-02

Companion to `results/prior_art.md`, which records the sweep of 2026-08-01. This
file records two things: a recheck of the headline negative result, and three
targeted sweeps on the specific findings the census now has in hand.

The reason for the second part: a known issue that we present as novel is the
most expensive error available to us, and it is the one a reviewer who built the
tool will catch first.

## Part 1: recheck of the headline negative result

### The recheck window is one day

The prior sweep ran on 2026-08-01. This recheck ran on 2026-08-02. The window is
24 hours. That is stated plainly because a "recheck found nothing" line is
worthless without the interval it covers, and no indexing pipeline resolves a
one-day window. The recheck is therefore weak evidence by construction, and its
value is that it is cheap, dated and repeatable rather than that it is
informative.

### Verdict

**Unchanged. The ground is still clear.** No publication appeared on or after
1 August 2026 that measures conformance or provenance completeness of AI-derived
or derived DICOM objects across a population of producers in a public archive,
that quantifies inter-validator disagreement on a shared corpus, or that measures
producer-attribution attributes at population scale.

The strongest evidence is not the web searches, which cannot resolve a one-day
window, but the two date-scoped index queries below. Both return an empty set for
the window.

### Date-scoped index queries, verbatim

arXiv API, retrieved 2026-08-02:

- `https://export.arxiv.org/api/query?search_query=all:DICOM&sortBy=submittedDate&sortOrder=descending&max_results=40`
  Most recent submission returned: **2026-07-28**, `2607.25589v1`. Nothing on or
  after 2026-08-01.
- `https://export.arxiv.org/api/query?search_query=all:%22Imaging+Data+Commons%22&sortBy=submittedDate&sortOrder=descending&max_results=20`
  Most recent submission returned: **2025-01-15**, `2501.09001v2`.
- `https://export.arxiv.org/api/query?search_query=all:conformance+AND+all:medical+AND+all:imaging&sortBy=submittedDate&sortOrder=descending&max_results=20`
  Most recent submission returned: **2026-07-09**, `2607.08084v1`.

PubMed E-utilities, `datetype=edat`, `mindate=2026/08/01`, `maxdate=2026/12/31`,
retrieved 2026-08-02:

- `term=DICOM+AND+(conformance+OR+validation)` returns **2** records:
  PMID 42539165, "Dual-Filament 3D Printing of Patient-Specific CT Phantoms with
  Embedded Implants and Tunable Metal-Artifact Intensity", medRxiv; and
  PMID 42537905, "Artificial Intelligence Based Ultrasound Screening for
  Antenatal Detection of Placenta Accreta Spectrum", American Journal of
  Obstetrics and Gynecology MFM. Neither is a conformance study.
- `term=%22Imaging+Data+Commons%22` returns **0** records.
- `term=DICOM+AND+provenance` returns **0** records.

### General web queries issued, verbatim

- `DICOM conformance census AI-derived objects public archive 2026 measurement study`
- `arxiv August 2026 DICOM conformance validation Imaging Data Commons derived objects`
- `inter-validator disagreement DICOM conformance quantified study 2026`
- `population measurement DICOM producer attribution Manufacturer provenance attributes archive 2026`
- `new 2026 study conformance provenance derived DICOM objects archive census validators published August`
- `arXiv new submission medical imaging DICOM metadata conformance audit archive August 2026`

### Two items seen that predate the sweep and were not in its record

Neither occupies the ground. Both are logged so they are not rediscovered later
and mistaken for something new.

- **arXiv:2508.01889v1**, "Medical Image De-Identification Resources: Synthetic
  DICOM Data and Tools for Validation", submitted 2025-08-03,
  <https://arxiv.org/abs/2508.01889>. Title and date verified through the arXiv
  API `id_list` endpoint. It runs dciodvfy as one report inside a
  de-identification benchmark, on synthetic data the authors built, to show that
  de-identification does not degrade conformance. It is a de-identification
  benchmark, not an archive census, and it does not report conformance rates for
  a population of third-party producers. Its existence does mean the manuscript
  should not imply that nobody runs dciodvfy programmatically in a published
  pipeline. That was already the substance of correction PA-C1.
- **arXiv:2607.25589v1**, "Forensic Reproducibility Audit of a Radiology
  Vision-Language Model Benchmark: From Intended Protocol to Released Artifact",
  submitted 2026-07-28, <https://arxiv.org/abs/2607.25589>. Title and date
  verified through the arXiv API `id_list` endpoint. Benchmark reproducibility,
  not DICOM conformance. Not retrieved in full.

## Part 2: the three findings

Definitions used below. **NOVEL** means no prior description was located by the
searches recorded here, which is a statement about this search and not about the
literature. **KNOWN** means a prior description was located and is cited.
**UNRESOLVED** means the question could not be settled either way.

---

### Finding (a): Key Object Selection Document objects missing Manufacturer (0008,0070)

Measured: 40 of 40 KOS objects in IDC v24, flagged by two independent validators
(`dciodvfy`: `Error - Missing attribute Type 2 Required Element=<Manufacturer>
Module=<GeneralEquipment>`; `dicom-validator`: `Module <General Equipment> Tag
(TAG) (Manufacturer) is missing`). Source: `results/phase2/census_message_classes.csv`.

#### Verdict: NOVEL

No prior description of KOS objects lacking General Equipment attributes was
located, in IDC, in TCIA, or anywhere else. This is a statement about the search
below, not a claim that the observation has never been made.

Two things make the finding harder to dismiss and are worth stating alongside it.
First, the requirement is not in dispute: PS3.3 Table A.35.4.3-1 lists the
General Equipment module with Usage **M** in the Key Object Selection Document
IOD, and Manufacturer (0008,0070) is Type 2 in the General Equipment module
(C.7.5.1), so it must be present and may be zero length. Absent is not a
permitted state. Second, unlike findings (b) and (c), two validators from
different codebases agree, so this is not a candidate validator artefact.

#### Queries run, verbatim

General web search:

- `"Key Object Selection" DICOM missing Manufacturer General Equipment module validation error`
- `discourse.canceridc.dev Key Object Selection validation Manufacturer missing`
- `"Key Object Selection Document" validation error General Equipment module Manufacturer Type 2 missing dcmtk dcmqrscp`
- `dciodvfy "Missing attribute Type 2 Required Element=<Manufacturer>" GeneralEquipment`
- `Posda TCIA curation "Key Object Selection" KOS conformance errors report`
- `"Key Object Selection" DICOM conformance study validation objects archive published`
- `comp.protocols.dicom Key Object Selection Document General Equipment module required Manufacturer`
- `IDC Imaging Data Commons "Key Object Selection Document" collection QIN breast validation errors`
- `QIN-Breast-DCE-MRI TCIA Key Object Selection Document series DICOM`
- `"key object selection" DICOM objects TCIA de-identification stripped Manufacturer equipment attributes`

GitHub issue and pull request search, all repositories, through
`api.github.com/search/issues`, query strings exactly as passed in `q`:

- `"Element=<Manufacturer> Module=<GeneralEquipment>"` returns **0**
- `"Module=<GeneralEquipment>"` returns **0**
- `"Required Element=<Manufacturer>"` returns **5**, none of them DICOM related
- `"KeyObjectSelectionDocument" dciodvfy` returns **0**
- `KeyObjectSelectionDocument Manufacturer` returns **0**
- `"Key Object Selection" dciodvfy` returns **1**, RSNA/anonymizer issue 11,
  which is an unrelated `SOPClassUID` attribute error

IDC community forum, `discourse.canceridc.dev/search.json?q=`:

- `Key Object Selection` returns **1** topic, 286, "Storing definitions of data
  collections as DICOM entities", which discusses using KOS as a container format
  and does not mention conformance or equipment attributes
- `Manufacturer missing` returns **0** topics
- `dciodvfy` returns **1** topic, the same topic 286

PubMed E-utilities, no date restriction:

- `term=DICOM+AND+%22Key+Object+Selection%22` returns **3** records, PMIDs
  40899556, 23595099 and 22403116, respectively on de-identification tool
  evaluation, structured reporting in German, and CouchDB storage of DICOM
  objects. None concerns KOS conformance.
- `term=DICOM+AND+%22General+Equipment%22+AND+conformance` returns **0** records
- `term=%22Key+Object+Selection%22+AND+conformance` returns **29** records, which
  is a loose unphrased match across unrelated clinical topics and was not
  triaged further

#### Citations found

None.

---

### Finding (b): Referenced Frame Number (0008,1160) present for a Referenced SOP Class that is not multi-frame

Measured: 722 Comprehensive SR objects, `dciodvfy`: `Error - Shall not be present
for Referenced SOP Class that is not multi-frame - attribute
<ReferencedFrameNumber>`, split 462 with no `analysis_result_id` and 260 under
`qiba_volct_1b`. Source: `results/phase2/census_message_classes.csv`.

#### Verdict: KNOWN

This dciodvfy check firing on an AI or analysis-derived DICOM object is publicly
documented, in the DICOM4QI connectathon results, and has been for years. We must
cite it and must not present the check as a discovery.

#### The citation

**DICOM4QI, "Siemens syngo.via", Results, Segmentation.**
<https://dicom4qi.readthedocs.io/en/latest/results/seg/syngovia/>, retrieved
2026-08-02. Text verified against the raw HTML, not against a page summary.

The page carries this attribution:

> DISCLAIMER: This section was completed by Andrey Fedorov using the version of
> software installed at Brigham and Women's Hospital. Representatives of Siemens
> were not involved in the presented evaluation.

and, under "4. Write task", this:

> Errors reported by dciodvfy :
>
> Error - Empty attribute (no value) Type 1C Conditional Element=<SegmentAlgorithmName> Module=<SegmentationImage>
> Error - May not be present for Referenced SOP Class that is not multi-frame - attribute <ReferencedFrameNumber>

#### What the citation does and does not establish

It establishes that the check exists, that it fires on real derived objects
produced by a real tool, and that this was written down publicly. It does not
establish our finding. Three differences, stated so the manuscript does not
overreach in either direction:

1. **Different SOP class.** DICOM4QI reports it on a Segmentation object. We
   report it on Comprehensive SR.
2. **Different message wording.** DICOM4QI records `May not be present`, our
   census records `Shall not be present`. This is presumably a dciodvfy version
   difference. We do not resolve it, and we do not know which version DICOM4QI
   ran. Reported as an ambiguity, not adjudicated.
3. **Different design.** DICOM4QI is one hand-picked object written at a
   connectathon by one participant. There is no sampling frame, no denominator
   and no rate. Our 722 is a census count.

So the defensible framing is: the check and its occurrence on derived objects are
known and cited; the population prevalence in Comprehensive SR is what we add.

#### Where it was searched for and not found

No description of the underlying encoding defect was found in any issue tracker,
correction proposal or committee correspondence.

- **dcmqi**: not a known issue. `api.github.com/search/issues` with
  `ReferencedFrameNumber repo:QIICR/dcmqi` returns **0**.
  `Referenced Frame Number repo:QIICR/dcmqi` returns **7** issues, none about
  this attribute in SR (they concern non-volumetric modalities, PixelData
  encoding, segment numbering, slice counts and geometry).
  `multi-frame dciodvfy repo:QIICR/dcmqi` returns **1**, issue 150, about
  converting segmentations of multi-frame input series.
- **GitHub, all repositories**: `"Shall not be present for Referenced SOP Class
  that is not multi-frame"` returns **0**. `"Referenced SOP Class that is not
  multi-frame"` returns **0**. `"Shall not be present for Referenced SOP Class"`
  returns **0**. `"May not be present for Referenced SOP Class"` returns **0**.
  `"ReferencedFrameNumber" dciodvfy` returns **1**, a cornerstone3D pull request
  about compressed image loading, unrelated.
- **DICOM CP or WG-06 correction proposal**: none located. Searched with
  `DICOM CP correction proposal Referenced Frame Number single frame SOP class SR SCOORD IMAGE content item`
  and
  `DICOM correction proposal CP "Referenced Frame Number" conditional required multi-frame image reference macro SR`.
  Candidates surfaced (CP-2035, CP-2450, CP-883, CP-1304, CP-2330, CP-2477) were
  not retrieved and are **not cited**: we cannot state that any of them addresses
  this, and we do not.
- **PixelMed and dcm4che trackers**: nothing located. Searched with
  `dcm4che PixelMed "ReferencedFrameNumber" structured report IMAGE content item single frame bug`.
- **Mailing list**: nothing located. Searched with
  `comp.protocols.dicom "Referenced Frame Number" structured report single frame image reference error validator`.
- **All other DICOM4QI results pages** were enumerated from the site index and
  fetched individually (`results/sr-tid1500/` and its three participant pages,
  `results/seg/` and its thirteen participant pages, `results/pm/`, `results/tr/`).
  The string appears on the syngo.via segmentation page and nowhere else. In
  particular it does not appear on any TID1500 SR results page.

Other verbatim queries run for this finding:

- `dciodvfy "Referenced Frame Number" "not multi-frame" error structured report`
- `QIICR dcmqi issue ReferencedFrameNumber structured report multi-frame`
- `github QIICR dcmqi issues "ReferencedFrameNumber" OR "Referenced Frame Number"`
- `"ReferencedFrameNumber" dciodvfy error "Shall not be present" Referenced SOP Class multi-frame`
- `dicom4qi structured report results dciodvfy ReferencedFrameNumber error validation`
- `"Referenced Frame Number" incorrectly present single frame image reference DICOM SR encoder bug known issue`

---

### Finding (c): Laterality (0020,0060) reported as an Error where the condition cannot be evaluated

Measured: 462 GSPS objects and 20 Real World Value Mapping objects, `dciodvfy`:
`Error - Missing attribute Type 2C Conditional Element=<Laterality>
Module=<GeneralSeries>`. Source: `results/phase2/census_message_classes.csv`.

#### Verdict: KNOWN

Comprehensively so. The behaviour is documented by the validator's own author, in
the validator's own documentation, and the exact error string we measured appears
in a 2023 mailing list thread in which the author explains it. We must present
this as a measurement of an acknowledged validator behaviour, never as a
discovery, and the manuscript should quote the author rather than characterise
the behaviour in our own words.

#### Citation 1: the dciodvfy documentation

**David Clunie, "DICOM Validator, dciodvfy", dicom3tools documentation.**
<http://www.dclunie.com/dicom3tools/dciodvfy.html>, retrieved 2026-08-02. Text
verified against the raw HTML.

Under "How do I interpret errors and warnings related to the Laterality
attribute?":

> Regardless, dciodvfy will complain when the attribute is absent if the body
> part is unknown or if it is not known to be unpaired, and also when it is
> present (zero length or not) if the body part is not specified or is specified
> and is not known to be unpaired.

> The presence or absence of the Laterality attribute when it is expected or not
> is reported as an error, not a warning, since it depends on the general
> mechanism of attribute condition checking used throughout, which always reports
> errors when conditional required attributes (those that are Type 1C or 2C) are
> not present if required, or are present if not required and "may be present
> otherwise" is not specified.

And in the section on the tool's limitations, laterality is named as the worked
example:

> Some of the warnings and errors may seem extremely if not excessively picky, or
> even beyond what is defined in the standard. This is particularly true of
> warnings that values are implausible or unlikely (such as 0), or creative
> attempts to determine real world conditions (such as laterality being dependent
> on a paired body part, or the body part being supposedly "unknown").

> Some of the reported errors and warnings may be spurious, particularly when
> conditions described in the DICOM standard depend on "real world" information
> that is not derivable from the DICOM Dataset itself.

The same page also disclaims any official standing:

> Are dciodvfy and dcentvfy an officially recognized or supported tool for
> certifying DICOM compliance? No. Neither the DICOM Standards Committee nor MITA
> (NEMA) have any official tool or certification mechanism.

#### Citation 2: comp.protocols.dicom, 2023

**Thread: "Condition for Laterality (0020,0060) required (Body Part Examined is a
paired structure)", comp.protocols.dicom.**
<https://groups.google.com/g/comp.protocols.dicom/c/vDk2wnk-KaU>, retrieved
2026-08-02. Text verified against the raw HTML, not against a page summary.

Simon Doran, 26 May 2023, quoting the error string that our census also records,
character for character:

> Laterality is 2C, based on whether Body Part Examined has a certain type. But
> Body Part Examined is Type 3, so in this case, whether Laterality should be
> present is formally undefined.
>
> However, in this case, dciodvfy reports an error. Is that correct behaviour?
>
> Error - Missing attribute Type 2C Conditional Element=<Laterality> Module=<GeneralSeries>

David Clunie, 28 May 2023:

> My dciodvfy tool is very aggressive about Laterality and Body Part Examined in
> order to encourage them to be populated correctly and consistently rather than
> be left empty or absent, using the Type 2(C) definition of required to have a
> value unless unknown as a reason to force the issue (begging the question of
> unknown to whom?).

> So if you just include Laterality with zero length, and BodyPartExamined is not
> present or has a value that is a recognized unpaired body part (e.g., ABDOMEN
> rather than ARM), it will still complain until you get it right, reporting
> either:
>
> Warning - is only permitted to be empty when actually unknown; should be absent
> (not empty) if an unpaired body part, and have a value if a paired body part -
> attribute <Laterality>
>
> or
>
> Error - Attribute present when condition unsatisfied (which may not be present
> otherwise) Type 2C Conditional Element=<Laterality> Module=<GeneralSeries>

Simon Doran's reply, 28 May 2023, which is the objection a reviewer will also
raise and which the manuscript should therefore not pretend to be raising first:

> I agree with the desirability of what you are trying to do, but surely it's
> slightly unfair to be "aggressive" when a decision was obviously made somewhere
> along the line to make Body Part Examined a Type 3 element?

Note on characterisation. The tool's author frames this as deliberate policy, not
as a bug: the word "aggressive" is his, and the intent is to push implementers
toward populating the attributes. The word "spurious" is also his, but it appears
in the general limitations section, not attached specifically to Laterality. The
manuscript must not put "false positive" in his mouth. Our own project rule
forbids us adjudicating it either way, so the correct treatment is to quote both
the mechanism and the author's stated intent and let the reader classify it.

#### Corroboration that the string occurs widely in the wild

Not cited as prior art, since none of these describes the behaviour, but they
show the error is common and that its recipients do not recognise it as expected
behaviour. `api.github.com/search/issues` with
`"Type 2C Conditional Element=<Laterality>"` returns **9** results, including
ImagingDataCommons/libdicom issue 48 (2023-03-29), zdavatz/gdt2dicom issue 4
(2023-03-15) and RSNA/anonymizer issue 22 (2025-01-14).

#### Query run, verbatim

- `dciodvfy Laterality Type 2C "General Series" false positive unpaired body part`
- GitHub issue search, `q` exactly: `"Type 2C Conditional Element=<Laterality>"`
- Direct retrieval of <http://www.dclunie.com/dicom3tools/dciodvfy.html> and
  <https://groups.google.com/g/comp.protocols.dicom/c/vDk2wnk-KaU>

Note that the very first query issued for this finding returned the answer. That
is worth recording: the cost of not checking would have been a claim of novelty
falsified by one search, in a paper whose plausible reviewers include the person
quoted above.

---

## Part 3: the three verdicts

| finding | verdict | basis |
|---|---|---|
| (a) KOS objects missing Manufacturer (0008,0070) | **NOVEL** | No prior description located across web search, GitHub issue search on the exact error strings, the IDC community forum, and PubMed. Requirement independently confirmed against PS3.3 A.35.4.3-1 and C.7.5.1. Two validators from different codebases agree, so it is not a candidate validator artefact. |
| (b) Referenced Frame Number present for a non-multi-frame Referenced SOP Class | **KNOWN** | DICOM4QI publishes the same dciodvfy check firing on a derived object. Cite it. Our addition is the population prevalence in Comprehensive SR, not the phenomenon. Not found in the dcmqi tracker, in any CP we could verify, or on the mailing list. |
| (c) Laterality Type 2C reported as an Error where the condition cannot be evaluated | **KNOWN** | Documented by the validator's author in the dciodvfy documentation and explained by him, against our exact error string, in a 2023 comp.protocols.dicom thread. Quote him; do not characterise it ourselves. |

## Consequences for the manuscript

1. Finding (b) is reframed from phenomenon to prevalence, and DICOM4QI is cited
   at the point the finding is introduced, not only in related work.
2. Finding (c) is reframed as a worked example of a validator behaviour its own
   author documents, which is the sharpest available illustration of why claim 2
   is pitched as measurement rather than discovery. It also supplies the floor
   argument in the author's own words.
3. Finding (a) is the only one of the three that carries a novelty claim, and
   that claim is scoped to "no prior description located by the search recorded
   in this file", never to "nobody has observed this".
4. The `May not be present` versus `Shall not be present` wording difference in
   dciodvfy across versions is an unresolved ambiguity and is reported as one.

## Coverage limits of this recheck

Carried over unchanged from `results/prior_art.md`, and extended.

Not searched, in this pass or the previous one: Google Scholar, Scopus, Web of
Science, Embase, IEEE Xplore, and the SPIE Medical Imaging, SIIM, EuroPACS, CARS
and RSNA abstract archives. Semantic Scholar was not retried.

Specific to this pass:

- **The DICOM Standards Committee correspondence is not searchable by us.** The
  public CP packs at dicom.nema.org were reached only through general web search,
  not enumerated. WG-06 minutes, ballot comments and the committee mailing lists
  were not searched at all. For finding (b) this is the single most likely place
  a prior description would sit, and its absence from our search is the main
  reason (b) is not stated more strongly in either direction.
- **Issue tracker coverage is GitHub only.** The DCMTK Redmine at
  support.dcmtk.org, the dcm4che Jira, the PixelMed issue list and SourceForge
  trackers, including GDCM, were reached only through general web search, not
  queried directly.
- **comp.protocols.dicom was searched through Google Groups and general web
  search, not through a complete archive dump.** A thread that no search engine
  surfaced would be missed.
- **Non-English sources were not searched.**
- **The web searches are US-region general web search.** They are not a database
  and their recall is unknown.
- One-day recheck window, as stated in Part 1. This recheck cannot detect a
  publication that appeared on 1 or 2 August 2026 and has not yet been indexed.

The pre-submission manual pass over the ten venues named in PA-07 is still
outstanding and now also owes a pass over the DICOM CP packs and the DCMTK,
dcm4che and PixelMed trackers.
