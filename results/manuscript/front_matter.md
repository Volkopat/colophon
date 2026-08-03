# Front matter

Everything a submission portal asks for before the manuscript itself, adapted to
a study that uses only public data and holds no patient contact.

The two prior papers by this author [34,36] are the intended pattern. **Neither
manuscript is in this repository**: `_ref/`, which `CLAUDE.md` points at for
both, does not exist in this checkout. What is carried over from them is
therefore what their released harnesses record, which is the author identity, the
licence and the DOI pattern, and the rest is built from what the requirements
themselves ask for. A section below that reads differently from the prior papers
is as likely to be that absence as a deliberate departure.

Items written as `[FIELD: ...]` are the ones this repository cannot establish
and the author fills in. Items written as `[CONFIRM: ...]` are filled in from a
source named beside them and should be read once before submission.

## Title

**Conformant and uninformative: producer attribution in 35,107 AI-derived DICOM
objects**

Running title: **Conformant and uninformative**

## Author

Digvijay Patil

Affiliation: {{FIELD:affiliation}}

ORCID: 0009-0003-6878-1712, https://orcid.org/0009-0003-6878-1712, taken from
the CITATION.cff files of both prior harnesses [35,37], which agree.

Corresponding author: Digvijay Patil, {{FIELD:corresponding_email}}

Sole author. There are no co-authors, and section 2.7 of the Methods says in
terms what that costs the study: a second, independent human adjudicator is
outstanding and the reliability pass is intra-instrument in consequence.

## Statements and Declarations

The venue requires these under this heading on the title page, and returns submissions that omit them as incomplete. Each is its own subsection below.

### Competing interests

No commercial relationship bears on this study. It uses only public data from
NCI Imaging Data Commons [6], obtained without registration, access request or
egress fee; it evaluates no commercial product; and no company, funder or vendor
had any role in its design, execution, analysis or in the decision to submit it.
The tools whose output is counted here were written by other people and none of
them is the author's.

One relationship is disclosed so that a reader meeting it in the reference list
is not surprised by it. The de-identification pipeline evaluated in the prior
work at [36] is a commercial product of aycan Medical Systems LLC. It is
disclosed as three separate claims, because they are separately checkable and
only one of them bears on the result.

**Where this study was done. Stated by the author.** This study was not carried
out at aycan Medical Systems LLC. It used none of that company's data, code,
hardware, network, licences or working time. The measurements were run on the
author's own machine, whose specification is in the pinned environment record,
against a public archive that requires no account.

**The employment window. Stated by the author.** The two works in the
reference list that this bears on are [36] and [34].
{{FIELD:employment_dates}}
{{FIELD:employment_covers}}

**Whether any object in the measured set came from that company. Measured.**
{{MEASURED:aycan_objects}}. {{MEASURED:aycan_attributes}}. No aycan product is
in the measurement panel either, which is a property of the panel table rather
than of the archive: the panel is `dciodvfy`, `dicom-validator` and `dcmpschk`,
and their provenance is in the reference list.

The prior work is cited for its method, specifically the validator-floor
measurement, the version-pinning appendix and the claims-ledger discipline this
study reuses, and not for any result of the company's.

`[CONFIRM: aycan Medical Systems LLC is named from the public README of the
author's palimpsest harness [37], which states that the pipeline evaluated in
[36] is a commercial product of that company. The employment relationship and
its dates are the author's to state, and are the two fields above.]`

### Funding

This study received no funding. No grant, contract, fellowship or institutional
award supported any part of it. Compute was the author's own machine, the
hardware is recorded in `results/environment.json` and reported in the Methods,
and the archive read carries no egress fee.

### Ethics

This study used public, de-identified benchmark data. It involved no human
subjects, no human participants, no animal subjects and no identifiable personal
information, and no Institutional Review Board review or informed consent was
required or sought. The data are the publicly downloadable derived-object series
of NCI Imaging Data Commons release v24 [6], published under Creative Commons
licences and already de-identified by the archive.

Two attributes read in the course of the measurement, `ContentCreatorName
(0070,0084)` and `OperatorsName (0008,1070)`, carry the person-name value
representation and can in principle carry a genuine person name. Methods 2.4.1
states what was done about that: values in those attributes were read only in
order to classify them, are reported as counts and category labels, and no value
in the published residual is a personal name.

### Data availability

All data are public and require no registration, no access request and no
account. The population is the derived, non-image SOP classes of **NCI Imaging
Data Commons release v24** [6], read through **idc-index 0.12.5 with
idc-index-data 24.2.2** [25], which is the exact index version every count in
this paper is computed against. Objects were fetched from the public
`s3://idc-open-data` bucket, which is not requester-pays.

The frame is void on the next IDC release, which is stated in the Limitations
rather than left implicit: an index version is part of the measurement, not
context for it.

Every generated artefact behind every figure and table, including the complete
distinct-value frequency table and the published unclassified residual, is in
`results/` in the code repository below.

### Code availability

All measurement code, the claims ledger carrying every quantitative statement in
this paper, the generated tables and the figure builders are published under the
MIT licence at https://github.com/Volkopat/colophon, with `CITATION.cff` in the
repository root.

The archived release is at Zenodo, cited as a **version DOI** rather than a
concept DOI so that a reader retrieves the state of the code this paper was
written from and not whatever the repository holds later [38]:

- version DOI: {{FIELD:zenodo_version_doi}}
- concept DOI: {{FIELD:zenodo_concept_doi}}
- release tag: {{FIELD:release_tag}}

The same pattern was followed for the prior harness, where the version DOI
10.5281/zenodo.21728679 resolves to tag v1.0.1 and the concept DOI
10.5281/zenodo.21728405 resolves to whichever version is newest [35].

Reproduction needs the pinned toolchain in `results/environment.json` and the
lockfile in `env/requirements.lock`. Two registered pins were not satisfied and
both are declared with a measured exposure bound in Methods 2.10; a reproduction
on the registered builds would not be expected to return identical gross counts,
and the direction of the difference is stated there.

### Author contributions, CRediT

Sole author, so every role is the author's. Stated in full rather than
abbreviated to "the author did everything", because the point of CRediT is that
the roles are separable and a reader can see which ones an LLM assisted with,
which is set out in the declaration below.

| CRediT role | Digvijay Patil |
|---|---|
| Conceptualization | yes |
| Methodology | yes |
| Software | yes |
| Validation | yes |
| Formal analysis | yes |
| Investigation | yes |
| Resources | yes |
| Data curation | yes |
| Writing, original draft | yes |
| Writing, review and editing | yes |
| Visualization | yes |
| Supervision | yes |
| Project administration | yes |
| Funding acquisition | not applicable, the study was unfunded |

### Declaration of generative AI use

Consistent with Methods 2.13, and kept current as the work proceeded rather than
written at submission. The full declaration, including the errors the controls
caught and the errors they did not, is `results/ai_use.md` in the repository.

**Tool.** Claude Code, model Claude Opus 5 with 1M context
(`claude-opus-5[1m]`), developer Anthropic, used from 2026-08-01 as an
interactive agent session with file and shell access on the author's machine.

**What it did.** Wrote the measurement code and its tests; ran those modules and
generated the write-ups in `results/`; ran the prior-art search and recorded
every query verbatim; produced the second adjudication pass; and drafted the
manuscript text.

**What it did not do.** It did not score any object's conformance. Conformance is
scored only by `dciodvfy` [18], `dicom-validator` [20] and `dcmpschk` [19], with
highdicom's reader [23] as a fourth opinion, none of which is in this
repository. No LLM output decides whether an object conforms to the standard, and
no LLM judgement enters any number in this paper. It did not supply any figure
from memory: every number in `results/` is computed from the local index at run
time by code in the repository.

**The controls that make this checkable.** Four, all runnable by a reviewer: the
independent third-party validators above; the claims ledger, where a rate quoted
without its floor fails the build; write-ups generated by the same code that
computes their numbers, so a number cannot drift away from its table; and the
test suite, which checks prose numbers against the ledger because the prior
project shipped two retired figures that survived a careful human read.

**Where it is weakest, stated rather than absorbed.** The second adjudication
pass was produced by the same agent as the first, and Methods 2.7 names it as an
intra-instrument repeatability check rather than an independent human
adjudication. Blindness was partial and the 147 pre-disclosed message classes are
excluded from the quoted agreement figures.

**Accountability.** The author is responsible for every claim in this paper and
in the repository behind it, including those produced with LLM assistance. The
controls exist so that the responsibility can be discharged by checking rather
than by trust.

**The venue's own policy.** {{FIELD:venue_ai_policy}} The language-editing
exception in most publisher policies does not apply here, because the tool did
more than edit language.

## Abstract

{{MEASURED:abstract}}

## Keywords

{{MEASURED:keywords}}
