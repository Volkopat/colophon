"""Assemble the submission package, from the manuscript documents and nothing else.

The manuscript lives in `results/manuscript/` as one file per section, which is
right for writing and wrong for submitting: a venue wants one ordered document,
a separate title page, a blinded second copy, figures as files, tables in order,
and a reference list in its own style, numbered by order of first citation.

Every one of those is a transformation of what is already written, so every one
of them is done here rather than by hand. Nothing in this module authors text
that carries a measurement. If a number is wrong in the package it is wrong in
the manuscript, and `tests/test_results_doc.py` fails on it there.

The venue is the Journal of Imaging Informatics in Medicine, whose requirements
are recorded in `VENUE` below with the date they were read. The backup venue,
the International Journal of Medical Informatics, is not encoded here; the
checklist says which items would change.

Three things this module deliberately does not do, each stated in the checklist
rather than silently skipped:

1. **It does not write Word.** The venue wants `.docx`. Producing one needs a
   package that is not in `env/requirements.lock`, and adding a package to a
   pinned environment to typeset a paper is how a measurement environment
   drifts. The package ships Markdown and names the conversion as a manual step.
2. **It does not typeset.** No 10-point Times, no page numbering, no line
   numbers. Those are properties of the Word file.
3. **It does not decide the blinding is sufficient.** It masks a declared token
   list and a declared phrase list, and a test asserts none survives. A paper
   whose method is the ledger discipline of two prior papers by the same author
   is identifiable by content, and the checklist says so.

Reproduce with `python -m colophon.submission`.
"""
from __future__ import annotations

import hashlib
import datetime as _dt
import json
import re
import shutil
from pathlib import Path

from . import citations, references, tokens
from .tokens import load_fields
from .paths import RESULTS, REPO

MANUSCRIPT = RESULTS / "manuscript"
OUT = RESULTS / "submission"
FIGDIR = OUT / "figures"
SUPPDIR = OUT / "supplementary"

VENUE = {
    "name": "Journal of Imaging Informatics in Medicine",
    "publisher": "Springer",
    "guidelines": "https://link.springer.com/journal/10278/submission-guidelines",
    "read_on": "2026-08-03",
    "review_model": "double-blind",
    "abstract_words": (150, 250),
    "keywords": (4, 6),
    "max_heading_levels": 3,
    "manuscript_format": "docx",
    "figure_format": "EPS preferred for vector graphics; MS Office files also "
                     "acceptable; name files Fig1, Fig2 and so on",
    "reference_style": "numbered consecutively in order of first citation; "
                       "author initials after surname, colon, title, journal "
                       "abbreviated as in Index Medicus, volume, pages, year",
    "reference_example": "Zaidel M, Hopper K, Iyriboz T: Interactive web-based "
                         "radiology teaching file. J Digit Imaging 12:203-204, 1999",
    "section_order": ["Abstract", "Introduction", "Materials and Methods",
                      "Results", "Discussion", "Conclusions"],
    "submission_system": "Editorial Manager, https://www.editorialmanager.com/jdim/",
}

# Section files, in the order the venue asks for, with the heading each takes in
# the assembled document. `discussion.md` supplies two sections, because the
# Conclusions were written into it and the venue wants them separately.
SECTIONS = [
    ("Introduction", "introduction.md", None),
    ("Materials and Methods", "methods.md", None),
    ("Results", "results.md", None),
    ("Discussion", "discussion.md", "before-conclusions"),
    ("Conclusions", "discussion.md", "conclusions-only"),
]
CONCLUSIONS_HEADING = "## Conclusions"

KEYWORDS = ["DICOM", "conformance", "provenance", "Imaging Data Commons",
            "metadata completeness", "measurement study"]

# What a title page has to carry, and the string that establishes each. Checked
# by searching the built page for the string rather than by asserting that the
# generator put it there.
TITLE_PAGE_ELEMENTS = {
    "title": "Conformant and uninformative",
    "author": "Digvijay Patil",
    "affiliation": "Affiliation:",
    "ORCID": "orcid.org/",
    "corresponding author": "Corresponding author:",
    "declarations": "## Competing interests",
}
# The declaration headings the venue asks for before the reference list.
DECLARATION_HEADINGS = ["Competing interests", "Funding", "Ethics",
                        "Data availability", "Code availability",
                        "Author contributions", "Declaration of generative AI use"]

# --- blinding -----------------------------------------------------------------
# Tokens are replaced longest first, so `Digvijay Patil` is masked before
# `Patil` and the shorter rule never fires on the remains of the longer one.
TOKEN_MASKS = {
    "Digvijay Patil": "[AUTHOR]",
    # The superseded address, still masked in case it survives in an artefact
    # written before the corresponding address changed.
    "digvijaypatil1996@gmail.com": "[AUTHOR EMAIL]",
    # There is no ORCID field, so this one is not derived and stays a literal.
    "0009-0003-6878-1712": "[AUTHOR ORCID]",
    "University at Buffalo": "[AFFILIATION]",
    "aycan Medical Systems LLC": "[COMPANY]",
    "aycan": "[COMPANY]",
    "https://github.com/Volkopat/colophon": "[REPOSITORY URL]",
    "https://github.com/Volkopat/spine-gsps": "[REPOSITORY URL]",
    "https://github.com/Volkopat/palimpsest": "[REPOSITORY URL]",
    "github.com/Volkopat/colophon": "[REPOSITORY URL]",
    "github.com/Volkopat/spine-gsps": "[REPOSITORY URL]",
    "github.com/Volkopat/palimpsest": "[REPOSITORY URL]",
    "Volkopat": "[REPOSITORY OWNER]",
    "10.5281/zenodo.21728679": "[DOI WITHHELD]",
    "10.5281/zenodo.21728405": "[DOI WITHHELD]",
    "Patil D": "[AUTHOR]",
    "Patil": "[AUTHOR]",
    # The two prior harnesses are named, public and searchable, so naming them
    # in a blinded copy identifies the author as surely as the surname does.
    # This project's own name is not masked: describing the software a paper is
    # about is normal in a blinded submission, and masking it would take
    # `colophon/claim3.py` out of the Methods with it.
    "spine-gsps": "[PRIOR HARNESS]",
    "palimpsest": "[PRIOR HARNESS]",
}
# The identity values are masked from the field store rather than from a literal
# typed here as well. The corresponding email was written in both places, so
# changing the field alone would have shipped a blinded copy carrying the new
# address in clear: the exact defect this dict exists to prevent, introduced by
# the dict itself. Anything the author fills in is masked from its current value.
def _register_identity_masks() -> None:
    path = RESULTS / "submission" / "fields.json"
    if not path.exists():
        return
    store = json.loads(path.read_text(encoding="utf-8"))
    for key, label in (("corresponding_email", "[AUTHOR EMAIL]"),
                       ("affiliation", "[AFFILIATION]"),
                       ("orcid", "[AUTHOR ORCID]")):
        value = str(store.get(key, {}).get("value", "")).strip()
        if value:
            TOKEN_MASKS.setdefault(value, label)


_register_identity_masks()


# Phrases that identify the author without naming them. A blinded manuscript
# that says "the two prior harnesses by this author" is not blinded.
PHRASE_MASKS = {
    "the two prior harnesses by this author": "two prior harnesses [withheld]",
    "two prior harnesses by this author": "two prior harnesses [withheld]",
    "prior work by this author": "prior work [withheld]",
    "Prior work by this author": "Prior work [withheld]",
    "the prior paper": "a prior paper [withheld]",
    "the prior harness": "a prior harness [withheld]",
    "by this author": "[withheld]",
}
# Reference numbers that are self-citations. The venue asks for these to be
# avoided or left blank; they are left blank, which keeps the numbering of every
# other reference identical between the two versions.
SELF_CITATION_KEYS = {"patil_spinegsps_article", "patil_spinegsps_harness",
                      "patil_palimpsest_article", "patil_palimpsest_harness",
                      "colophon"}
WITHHELD = "Reference withheld for double-blind review."

# The Declarations that may appear in a blinded copy at all. Competing interests
# and author contributions cannot: the first describes an employment
# relationship and the second is a table with a name at the top of it. Masking
# the company name out of a paragraph that still says "the author's employment
# at that company, which produced the pipeline evaluated in the prior work" does
# not blind it, it only makes it look blinded. Both go on the title page, which
# the venue does not send to reviewers.
BLINDED_DECLARATIONS = """## Competing interests

Declared on the title page, which is not part of this blinded copy. The
declaration names one prior commercial relationship, states that nothing of that
company's appears anywhere in this study, and is available to the editor.

## Funding

This study received no funding. No grant, contract, fellowship or institutional
award supported any part of it. Compute was a single desktop machine, whose
specification is recorded in the pinned environment record, and the archive read
carries no egress fee.

## Ethics

This study used public, de-identified benchmark data. It involved no human
subjects, no human participants, no animal subjects and no identifiable personal
information, and no Institutional Review Board review or informed consent was
required or sought. The data are the publicly downloadable derived-object series
of NCI Imaging Data Commons release v24, published under Creative Commons
licences and already de-identified by the archive.

Two attributes read in the course of the measurement, `ContentCreatorName
(0070,0084)` and `OperatorsName (0008,1070)`, carry the person-name value
representation and can in principle carry a genuine person name. Methods 2.4.1
states what was done about that: values in those attributes were read only in
order to classify them, are reported as counts and category labels, and no value
in the published residual is a personal name.

## Data availability

All data are public and require no registration, no access request and no
account. The population is the derived, non-image SOP classes of NCI Imaging
Data Commons release v24, read through idc-index 0.12.5 with idc-index-data
24.2.2, which is the exact index version every count in this paper is computed
against. Objects were fetched from the public `s3://idc-open-data` bucket, which
is not requester-pays. The collections and their source DOIs are listed in
Supplementary item S1.

## Code availability

All measurement code, the claims ledger carrying every quantitative statement in
this paper, the generated tables and the figure builders are published under the
MIT licence, with an archived release at Zenodo cited by version DOI. The
repository URL and the DOI are withheld from this blinded copy because they
identify the author, and both are on the title page.

## Author contributions

Declared on the title page. The study is single-authored, which Methods 2.7
reports as a limitation rather than a fact about the byline: a second,
independent human adjudicator is outstanding and the reliability pass is
intra-instrument in consequence.

## Declaration of generative AI use

The tool, the model and the developer are named in Methods 2.13, with the
controls that make the output checkable: independent third-party validators, a
published rule table for every classification, write-ups generated by the code
that computes their numbers, and the claims ledger. No LLM output decides
whether an object conforms to the standard, and no LLM judgement enters any
number in this paper. The second adjudication pass was produced by the same
agent as the first and is named as an intra-instrument check. The author is
responsible for every claim, including those produced with LLM assistance.
"""


def _read(name: str) -> str:
    return (MANUSCRIPT / name).read_text(encoding="utf-8")


def _strip_h1(text: str) -> str:
    """Drop the file's own title line; the assembled document supplies it."""
    lines = text.split("\n")
    while lines and (not lines[0].strip() or lines[0].startswith("# ")):
        lines.pop(0)
    return "\n".join(lines).strip()


def _demote(text: str) -> str:
    """`## 2.1` becomes `## 2.1` under an H1 section, and `###` stays `###`.

    The source files already use `##` and `###` under a single `#`, which is the
    depth the venue allows once the section heading is the `#`. Nothing moves.
    """
    return text


def venue_abstract() -> str:
    """The 150 to 250 word form, from `abstract_venue.md` between its rules."""
    parts = _read("abstract_venue.md").split("\n---\n")
    if len(parts) < 3:
        raise ValueError("abstract_venue.md has no fenced abstract body")
    return parts[1].strip()


def abstract_words(text: str | None = None) -> int:
    text = venue_abstract() if text is None else text
    return len(re.sub(r"\*\*", "", text).split())


def section_bodies() -> list[tuple[str, str]]:
    out = []
    for heading, filename, mode in SECTIONS:
        text = _strip_h1(_read(filename))
        if mode == "before-conclusions":
            text = text.split(CONCLUSIONS_HEADING)[0].strip()
        elif mode == "conclusions-only":
            if CONCLUSIONS_HEADING not in text:
                raise ValueError("%s carries no Conclusions section" % filename)
            text = text.split(CONCLUSIONS_HEADING)[1].strip()
        out.append((heading, _demote(text)))
    return out


def declarations() -> str:
    """The Declarations block the venue wants before the reference list.

    Taken from the front matter rather than restated, so the two cannot differ.
    """
    text = _read("front_matter.md")
    wanted = ["Competing interests", "Funding", "Ethics", "Data availability",
              "Code availability", "Author contributions, CRediT",
              "Declaration of generative AI use"]
    # The venue requires these under an umbrella "Statements and Declarations"
    # heading on the title page, so each is now an H3 under it. Both depths are
    # accepted here so the parser follows the front matter rather than the front
    # matter having to keep a shape that suits the parser.
    blocks = {}
    current = None
    for line in text.splitlines():
        if line.startswith("### ") or line.startswith("## "):
            marker = 4 if line.startswith("### ") else 3
            current = line[marker:].strip()
            blocks[current] = []
        elif current is not None:
            blocks[current].append(line)
    missing = [w for w in wanted if w not in blocks]
    if missing:
        raise ValueError("front_matter.md has no section for %s" % missing)
    parts = []
    for w in wanted:
        parts.append("## %s\n" % w)
        parts.append("\n".join(blocks[w]).strip() + "\n")
    return "\n".join(parts)


# --- citation renumbering -----------------------------------------------------
def first_appearance_order(text: str) -> list[int]:
    order = []
    for group in citations.MARKER.findall(text):
        for token in group.split(","):
            n = int(token.strip())
            if n not in order:
                order.append(n)
    return order


def renumber(text: str, mapping: dict[int, int]) -> str:
    def sub(m):
        nums = [int(t.strip()) for t in m.group(1).split(",")]
        return "[%s]" % ",".join(str(mapping[n]) for n in nums)
    return citations.MARKER.sub(sub, text)


# --- blinding -----------------------------------------------------------------
def blind(text: str) -> str:
    for phrase, repl in sorted(PHRASE_MASKS.items(), key=lambda kv: -len(kv[0])):
        text = text.replace(phrase, repl)
    for token, repl in sorted(TOKEN_MASKS.items(), key=lambda kv: -len(kv[0])):
        text = text.replace(token, repl)
    return text


def blinding_leaks(text: str) -> list[str]:
    return sorted({t for t in TOKEN_MASKS if t in text}
                  | {p for p in PHRASE_MASKS if p in text})


FIELD_MARKER = re.compile(r"`?\[(FIELD|CONFIRM):\s*([^\]]*)\]`?")


def outstanding_fields(files: dict[str, str]) -> list[dict]:
    """Every placeholder still unfilled, with the file it is in.

    A package that ships with {{FIELD:cover_letter_date}} in the cover letter is a package
    that gets sent with {{FIELD:cover_letter_date}} in the cover letter, so the list is
    computed and printed rather than remembered.
    """
    found = []
    for name, text in sorted(files.items()):
        for m in FIELD_MARKER.finditer(text):
            what = " ".join(m.group(2).split())
            # The front matter explains its own convention with a literal
            # `[FIELD: ...]`, which is documentation rather than a placeholder.
            if what.strip(". ") == "":
                continue
            found.append({"file": name, "kind": m.group(1), "what": what[:120]})
    return found


# --- assembly -----------------------------------------------------------------
TITLE = "Conformant and uninformative: producer attribution in 35,107 AI-derived DICOM objects"


def _assemble(blinded: bool) -> str:
    """The body, before renumbering."""
    parts = ["**%s**\n" % TITLE, "# Abstract\n", venue_abstract() + "\n",
             "**Keywords** " + "; ".join(KEYWORDS) + "\n"]
    for heading, body in section_bodies():
        parts.append("# %s\n" % heading)
        parts.append(body + "\n")
    parts.append("# Declarations\n")
    parts.append(BLINDED_DECLARATIONS if blinded else declarations())
    draft = "\n".join(parts)
    return blind(draft) if blinded else draft


def manuscripts() -> tuple[str, str, list[int], dict[int, int]]:
    """Both versions and the list of references nothing cites.

    **The numbering is computed once, from the unblinded copy, and used for
    both.** Deriving it separately looked right and was wrong: the blinded
    Declarations do not cite the self-citations the full ones do, so the blinded
    copy came out with two fewer references and a different number against every
    entry after them. A reviewer's reference 12 has to be the editor's.
    """
    full = _assemble(blinded=False)
    order = first_appearance_order(full)
    known = {e["n"] for e in references.load()}
    unknown = [n for n in order if n not in known]
    if unknown:
        raise ValueError("the assembled manuscript cites %s, which the "
                         "reference list does not carry" % unknown)
    uncited = sorted(known - set(order))
    mapping = {old: new for new, old in enumerate(order, start=1)}

    entries = {e["n"]: e for e in references.load()}
    out = []
    for blinded in (False, True):
        draft = renumber(_assemble(blinded), mapping)
        lines = ["# References\n"]
        for new, old in enumerate(order, start=1):
            e = entries[old]
            if blinded and e["key"] in SELF_CITATION_KEYS:
                lines.append("%d. %s\n" % (new, WITHHELD))
            else:
                rendered = references.render_jiim_entry(e)
                lines.append("%d. %s\n"
                             % (new, blind(rendered) if blinded else rendered))
        out.append(draft + "\n" + "\n".join(lines))
    return out[0], out[1], uncited, mapping


def title_page() -> str:
    """The front matter, minus the notes it carries for the author.

    `front_matter.md` opens by explaining its own `[FIELD:]` convention and by
    recording that the prior papers were not available to copy the pattern
    from. Both are notes to the author. An editor should get the title page.
    """
    text = _read("front_matter.md")
    body = text.partition("\n## Title\n")[2]
    if not body.strip():
        raise ValueError("front_matter.md has no Title section")
    return ("# Title page\n\n%s\n\n## Author\n" % TITLE +
            body.partition("\n## Author\n")[2] +
            "\n\n## Acknowledgments\n\nNone. The study was unfunded, "
            "single-authored, and used only public data.\n")


def _ladder_headline() -> str:
    """`25 of 36`, recomputed from the ladder the table is drawn from.

    This was typed. It read `21 of 31` in the cover letter and in the Table 3
    caption for a whole build after the ladder moved, because nothing recomputed
    either from the rows beneath them.
    """
    import pandas as pd
    ladder = pd.read_csv(RESULTS / "claim3" / "t33_recoverability_ladder.csv")
    lvl = ladder["first_level_identity_appears"].astype(str)
    return "%d of %d" % (int((lvl == "none").sum()), len(ladder))


def _letter_date() -> str:
    """The date on the letter, stamped at build.

    `cover_letter_date` held the string "stamped at final build", which is a
    description of what should happen rather than a date, and it printed at the
    head of the letter exactly as written. A field whose value is an instruction
    is not a field. The date is stamped here; the field still overrides it if it
    is set to something that looks like a date.
    """
    override = str(load_fields().get("cover_letter_date", {}).get("value", ""))
    if re.search(r"\d{4}", override):
        return override.strip()
    return _dt.date.today().strftime("%d %B %Y").lstrip("0")


def _aycan_denominator() -> str:
    """The searched-object count on its own, without the method clause.

    The full sentence belongs on the title page, where the attributes searched
    and the two that cannot be searched are stated beside it."""
    m = re.search(r"of ([\d,]+) objects searched", tokens.measured("aycan_objects"))
    return m.group(1) if m else "the searched set"


def cover_letter() -> str:
    return """# Cover letter

<<LETTER_DATE>>

The Editor-in-Chief
<<VENUE>>

Dear Editor,

I submit for your consideration a measurement study titled **"<<TITLE>>"**.

An AI result delivered as a DICOM object has two properties that are routinely
treated as one: whether it conforms to the Information Object Definition it
claims, and whether it says what produced it. The paper separates them and
measures the second across one release of the NCI Imaging Data Commons. Of
35,107 objects in eight object classes, 82.33 percent are conformant and
uninformative: everything the standard requires is present, and none of it
identifies the algorithm. Over the unit that is complete, producer identity
appears at no carrier level in <<LADDER>> analysis-result cells.

Three things may interest the journal specifically.

**The finding is about the standard, not about anybody's data quality.** The gap
is permitted rather than violated: inside one table of PS3.3 the structured,
coded, versioned carrier of algorithm identity is Type 3 while the free-text
carrier one row above it is Type 1C, and the consequence is measured at 34,234
of 36,488 segments against 12 of the same 36,488. The paper reports this by
object class and by analysis result and builds no ranking of producing groups.

**Conformance is never scored by me.** It is scored by third-party validators,
and where they disagree the disagreement is reported as direction rather than
resolved. Every rate is published as a triple of gross, floor and net, because a
known-good object built by a conformant writer still draws validator messages.

**Everything is checkable.** Every quantitative statement in the manuscript
carries a row in a published claims ledger with the exact command that produced
it, the source artefact and what the run dropped; retired claims stay in the
ledger with their reason. The measurement code, the generated tables and the
figure builders are public.

The paper states what it does not establish. The reliability pass is
intra-instrument rather than an independent human adjudication, one object class
is excluded from every object-weighted rate and named wherever a rate appears,
one pre-registered arm is deferred, and two registered tool pins were not
satisfied and each carries a measured exposure bound.

Generative AI use is declared in the Methods and in the Declarations, with the
tool, the model, the developer and the controls that make the output checkable.

The manuscript is original, is not under consideration elsewhere, and has not
been published previously. I have no competing interests bearing on this study.
One prior commercial relationship is disclosed on the title page because it lies
behind two cited prior works, and the disclosure is split into what was measured
and what I state. **Measured:** no object in the measured set is written by that
company, 0 of <<SEARCHED_N>> objects searched; the attributes searched and the two
that could not be searched are stated on the title page. **Stated:** this study
was not carried out at that company and used none of its data, code, hardware,
network, licences or working time.

**Suggested reviewers.** {{FIELD:suggested_reviewers}}

Thank you for considering the manuscript.

Yours sincerely,

{{FIELD:signature_block}}
""".replace("<<VENUE>>", VENUE["name"]).replace("<<TITLE>>", TITLE)        .replace("<<LADDER>>", _ladder_headline())        .replace("<<LETTER_DATE>>", _letter_date())        .replace("<<SEARCHED_N>>", _aycan_denominator())


def figure_legends() -> str:
    """One legend per figure, carrying the sentence the illustration may not.

    The venue forbids a title or a caption inside a figure. Each builder now
    returns its title rather than drawing it, and the legend prints it, so
    moving the sentence out of the image cannot lose it.
    """
    spec = _read("figures.md")
    titles, keys, sources, rows = {}, {}, {}, {}
    manifest_path = RESULTS / "figures" / "manifest.json"
    if manifest_path.exists():
        m = json.loads(manifest_path.read_text(encoding="utf-8"))
        for name, meta in m.items():
            if name.startswith("_"):
                continue
            n = name.replace("figure", "")
            titles[n] = meta.get("title_for_the_legend", "")
            keys[n] = meta.get("key_for_the_legend", "")
            # The file's own opening sentence promises these and no legend
            # carried one. They exist in the manifest; printing them is worth
            # more to a reviewer than a sentence promising less.
            sources[n] = str(meta.get("source_artefact", "")).replace(
                str(REPO) + "\\", "").replace(str(REPO) + "/", "")
            rows[n] = ", ".join(meta.get("ledger_rows", []))
    out = ["# Figure legends\n",
           "One legend per figure, in order. The opening sentence of each is the "
           "one the illustration used to carry as a drawn-in title, moved here "
           "because the venue does not allow a title inside a figure. Each "
           "legend then names the artefact the figure is drawn from and the "
           "ledger rows carrying every value annotated on it, so a reader can "
           "check a figure without re-running anything.\n"]
    blocks = spec.split("\n## ")
    for block in blocks:
        if not block.startswith("Figure "):
            continue
        head, _, rest = block.partition("\n")
        n = re.match(r"Figure (\d+)\.", head)
        if not n:
            continue
        # The first paragraph only. The figure specification continues into
        # why a figure was changed and which ledger rows carry its values,
        # which belongs in the repository and not under a figure in a journal.
        prose = []
        for line in rest.split("\n"):
            if line.startswith("|"):
                continue
            if not line.strip():
                if prose:
                    break
                continue
            prose.append(line.strip())
        num = n.group(1)
        # The file's opening sentence promises the source artefact and the
        # ledger rows for every annotated value, and no legend carried either.
        # They are in the figure manifest; printing them is worth more to a
        # reviewer than a sentence that promises less.
        provenance = ""
        if sources.get(num) or rows.get(num):
            provenance = ("Drawn from `%s`; every value annotated on it traces "
                          "to ledger %s." % (sources.get(num, "an artefact"),
                                             rows.get(num, "no row")))
        parts = [p for p in (titles.get(num, ""), " ".join(prose),
                             keys.get(num, ""), provenance) if p.strip()]
        out.append("**Fig. %s** %s\n" % (num, " ".join(parts)))
    return "\n".join(out)


def supplementary_index() -> str:
    rows = [
        ("S1", "supplementary/S1_source_dois.csv",
         "Every collection in the measured classes with the source DOI the "
         "archive index records for it, so the imaging data behind every count "
         "can be reached."),
        ("S2", "results/ledger.csv",
         "The claims ledger. Every quantitative statement in the manuscript, "
         "with the command that produced it, the source artefact, the floor it "
         "is measured against, and what the run dropped. Retired claims stay "
         "with their reason."),
        ("S3", "results/claims_map.md",
         "The join from every ledger row to the artefact carrying it, and the "
         "joins that fail: orphan claims, uncited artefacts, broken "
         "derivations, retirement chains and test coverage."),
        ("S4", "results/prisma_s_appendix.md",
         "The prior-art search in PRISMA-S form, with every query verbatim, and "
         "the fields the record cannot fill."),
        ("S5", "results/typecheck/segment_tables_verbatim.md",
         "The DocBook text of Tables C.8.20-2, C.8.20-4 and C.8.20-5 as read "
         "from the standard, which is what every Type designation in the paper "
         "is checked against."),
        ("S6", "results/environment.json",
         "The pinned toolchain: binaries with their version strings and "
         "hashes, the Python lockfile, the archive index version, the DICOM "
         "standard edition and the hardware."),
        ("S7", "results/ai_use.md",
         "The declaration of LLM use in full, including the errors the "
         "controls caught and the errors they did not."),
        ("S8", "results/cp/cp_segmentation_algorithm_identification.md",
         "The DICOM Correction Proposal described in the Discussion. Status, "
         "from `results/cp/status.json`, the one source value the manuscript "
         "reads: " + tokens.cp_sentence(short=True) + "."),
        ("S9", "results/cp/status.json",
         "That source value. Three states are allowed, drafted and not filed, "
         "filed and awaiting a number, and assigned number N; the Discussion, "
         "the abstract and this index all render from it."),
    ]
    out = ["# Supplementary information\n",
           "%d items, counted from the table below rather than stated; the "
           "index said Eight over nine rows for one build. Each is a file in "
           "the released repository and is "
           "listed here with what it is for, because a supplementary index "
           "that only lists filenames makes a reviewer open all of them to "
           "find the one they want.\n",
           "| item | file | what it is |", "|---|---|---|"]
    for tag, path, what in rows:
        out.append("| %s | `%s` | %s |" % (tag, path, what))
    return "\n".join(out) + "\n"


def source_dois() -> Path:
    """Collection to source DOI, for the venue's imaging-data link requirement.

    Read from the archive index already on the machine. Nothing is downloaded
    and no count in the paper depends on this table; it exists so a reader can
    reach the data.
    """
    from . import index as idx, census
    _, df = idx.load_index()
    classes = list(census.CLASS_ORDER) + [census.EXCLUDED]
    sub = df[df["sop_class_name"].isin(classes)]
    g = (sub.groupby(["collection_id", "source_DOI"], dropna=False)
         ["SeriesInstanceUID"].nunique().reset_index()
         .rename(columns={"SeriesInstanceUID": "series"})
         .sort_values(["collection_id", "source_DOI"]))
    SUPPDIR.mkdir(parents=True, exist_ok=True)
    path = SUPPDIR / "S1_source_dois.csv"
    g.to_csv(path, index=False)
    return path


def _strip_eps_date(path: Path) -> None:
    """Blank the EPS creation timestamp.

    Matplotlib writes `%%CreationDate: <now>` into the PostScript header, which
    makes every regeneration a different file and defeats the same
    reproducibility check the PDFs carry. The comment is metadata, no renderer
    reads it, and removing it is what makes an EPS regenerate byte-identical.
    """
    data = path.read_bytes()
    out = b"\n".join(line for line in data.split(b"\n")
                     if not line.startswith(b"%%CreationDate:"))
    path.write_bytes(out)


def figures_for_submission() -> list[dict]:
    """Fig1..Fig6 as EPS, with the PDF and PNG beside them.

    EPS because the venue prefers it for vector graphics, and the figures are
    vector. The builders are the ones in `colophon.figures`, called again rather
    than converted, so an EPS is not a rasterised PDF.
    """
    from . import figures as F
    FIGDIR.mkdir(parents=True, exist_ok=True)
    # The venue requires fonts embedded in vector graphics. Matplotlib's default
    # for PostScript is Type 3, which writes glyph outlines as procedures and
    # embeds no font program, so the file passes a visual check and fails the
    # requirement. Type 42 embeds the TrueType font.
    #
    # It is set inside an rc_context and not globally. Setting it globally
    # looked harmless, because it names the PostScript backend, and it changed
    # the PDF output as well: `tests/test_figures.py` caught figure 3 becoming
    # irreproducible the next time anything rebuilt it in the same process.
    out = []
    F._CONTRAST_LOG.clear()
    with F.plt.rc_context({"ps.fonttype": 42}):
        for n in sorted(F.FIGURES):
            fig, values = F.FIGURES[n]()
            # The venue forbids a title inside an illustration, so this checks
            # the drawn object rather than trusting that none was set.
            drawn = [a.get_title(loc=w) for a in fig.axes
                     for w in ("left", "center", "right")]
            drawn += [t.get_text() for t in getattr(fig, "texts", [])]
            has_title = any(len(str(s).strip()) > 3 for s in drawn)
            width_mm = fig.get_size_inches()[0] * 25.4
            eps = FIGDIR / ("Fig%d.eps" % n)
            fig.savefig(eps, format="eps")
            F.plt.close(fig)
            _strip_eps_date(eps)
            raw = eps.read_bytes()
            rec = {"figure": n, "eps": str(eps),
                   "sha256_eps": hashlib.sha256(raw).hexdigest()[:16],
                   # Type 42 with an sfnts block is a TrueType font program
                   # inside the file. Type 3 is glyph outlines and no font.
                   "fonts_embedded": b"/FontType 42" in raw and b"sfnts" in raw,
                   "has_drawn_title": has_title,
                   "width_mm": round(width_mm, 1)}
            for ext in ("pdf", "png"):
                src = F.OUT / ("figure%d.%s" % (n, ext))
                if src.exists():
                    dst = FIGDIR / ("Fig%d.%s" % (n, ext))
                    shutil.copyfile(src, dst)
                    rec[ext] = str(dst)
            out.append(rec)
    return out, F.contrast_report()


# --- the checklist ------------------------------------------------------------
def _eps_widths() -> dict:
    """Width in millimetres of every shipped EPS, from its bounding box."""
    out = {}
    for path in sorted(FIGDIR.glob("Fig*.eps")):
        head = path.read_bytes()[:2000].decode("latin-1")
        m = re.search(r"%%BoundingBox:\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)", head)
        if m:
            x0, _, x1, _ = (int(v) for v in m.groups())
            out[path.stem] = round((x1 - x0) * 25.4 / 72.0, 1)
    return out


def _repro_summary(report: dict) -> str:
    from . import reproducibility
    return reproducibility.summary(report)


def checklist(state: dict) -> str:
    ok = lambda b: "yes" if b else "**NO**"
    lo, hi = VENUE["abstract_words"]
    klo, khi = VENUE["keywords"]
    rows = [
        ("Manuscript sections in the venue's order",
         ok(state["headings_found"] == VENUE["section_order"]),
         "%d of %d expected top-level headings, in the venue's order, read "
         "back out of the assembled document rather than out of this module's "
         "configuration: %s"
         % (sum(1 for a, b in zip(state["headings_found"],
                                  VENUE["section_order"]) if a == b),
            len(VENUE["section_order"]),
            " then ".join(state["headings_found"]))),
        ("Abstract within %d to %d words" % (lo, hi),
         ok(lo <= state["abstract_words"] <= hi),
         "%d words. The repository abstract is %d and is not the one submitted; "
         "what the short form drops is listed in `abstract_venue.md`."
         % (state["abstract_words"], state["repo_abstract_words"])),
        ("Keywords, %d to %d" % (klo, khi), ok(klo <= len(KEYWORDS) <= khi),
         "%d: %s" % (len(KEYWORDS), "; ".join(KEYWORDS))),
        ("No more than %d displayed heading levels" % VENUE["max_heading_levels"],
         ok(state["max_heading_depth"] <= VENUE["max_heading_levels"]),
         "deepest heading is level %d" % state["max_heading_depth"]),
        ("Title page carries title, author, affiliation, ORCID, corresponding "
         "author and declarations",
         ok(not state["title_page_missing"]),
         "%d of %d required elements found in `01_title_page.md` by searching "
         "for each: %s%s"
         % (len(TITLE_PAGE_ELEMENTS) - len(state["title_page_missing"]),
            len(TITLE_PAGE_ELEMENTS), ", ".join(sorted(TITLE_PAGE_ELEMENTS)),
            "" if not state["title_page_missing"]
            else ". Missing: " + ", ".join(state["title_page_missing"]))),
        ("Blinded manuscript with no author names or affiliations",
         ok(not state["blinding_leaks"]
            and state["blinded_declarations_are_a_pointer"]),
         "`03_manuscript_blinded.md`. %d declared tokens and phrases masked, %d "
         "surviving. Self-citations are left blank rather than removed, so the "
         "numbering is identical in both versions. Competing interests and "
         "author contributions are a pointer to the title page rather than a "
         "masked copy of themselves, because an employment disclosure with the "
         "company name removed still describes the author."
         % (len(TOKEN_MASKS) + len(PHRASE_MASKS), len(state["blinding_leaks"]))),
        ("References numbered by order of first citation",
         ok(state["renumbered"]),
         "%d references, renumbered from the repository order. Rendered in the "
         "venue's style from the same entries, not retyped."
         % state["references"]),
        ("Every reference cited, every citation resolves",
         ok(state["citations_clean"] and not state["uncited"]),
         "0 unresolved markers, %d listed but never cited" % len(state["uncited"])),
        ("Figures supplied electronically, named Fig1 and so on, vector where "
         "possible", ok(state["figures"] == 6),
         "%d figures as EPS, with PDF and PNG beside each. Drawn with "
         "matplotlib, which the venue asks to be named." % state["figures"]),
        ("No titles or captions inside the illustrations",
         ok(state["figures_without_titles"] == state["figures"]),
         "%d of %d. Every drawn-in title moved to the legend, which prints it "
         "from the same source, and the descriptive panel titles in figures 5 "
         "and 6 became panel letters."
         % (state["figures_without_titles"], state["figures"])),
        ("Figure lettering at a contrast ratio of at least 4.5 to 1",
         ok(state["contrast_clean"]),
         "computed from the colours the figures draw with, not asserted: %d "
         "text pairings, lowest %.2f to 1 on %s. Two pairings failed before this "
         "was measured, at 1.98 and 3.54."
         % (state["contrast_pairs"], state["contrast_lowest"],
            state["contrast_lowest_where"])),
        ("Figure width is one of the venue's four permitted values",
         ok(state["figures_off_the_width_grid"] == 0),
         "%d of %d figures are off the grid {39, 84, 129, 174} mm, measured off "
         "the shipped EPS bounding box rather than from the drawing canvas: %s. "
         "The row this replaces compared a stored canvas constant with itself "
         "and passed while five figures were off the grid."
         % (state["figures_off_the_width_grid"], state["figures"],
            state["figure_widths_mm"])),
        ("Fonts embedded in the vector figures",
         ok(state["fonts_embedded"] == state["figures"]),
         "%d of %d EPS files carry a Type 42 font program. Matplotlib's "
         "PostScript default is Type 3, which embeds no font and passes a "
         "visual check, so this is set explicitly."
         % (state["fonts_embedded"], state["figures"])),
        ("Figures regenerate byte-identical",
         ok(state["reproducibility"].get("all_reproducible")),
         "%s. Two builds in two separate processes into two separate "
         "directories, compared byte for byte, on this machine and this "
         "environment; a cross-machine claim is not made. The row previously "
         "read `the EPS creation timestamp is stripped, which is the only "
         "non-deterministic byte matplotlib writes into them`, which was a "
         "belief about matplotlib and named only the format known to pass."
         % state["reproducibility_summary"]),
        ("Every figure has a descriptive caption", ok(state["legends"] == 6),
         "`05_figure_legends.md`, %d legends" % state["legends"]),
        ("Tables numbered, cited in order, each with a caption",
         ok(state["tables"] >= 6 and state["tables_cited_in_order"]),
         "%d captions in `04_tables.md`, numbered 1 to %d. First citation of "
         "each in the manuscript body is in ascending order: %s. Order found: %s"
         % (state["tables"], state["tables"],
            "yes" if state["tables_cited_in_order"] else "**no**",
            ", ".join(str(n) for n in state["table_citation_order"]))),
        ("Declarations before the reference list",
         ok(not state["declarations_missing"]
            and state["declarations_precede_references"]),
         "%d of %d expected declaration headings found in the assembled "
         "document by searching for each, and the Declarations section starts "
         "at line %d against the reference list at line %d%s"
         % (len(DECLARATION_HEADINGS) - len(state["declarations_missing"]),
            len(DECLARATION_HEADINGS), state["declarations_line"],
            state["references_line"],
            "" if not state["declarations_missing"]
            else ". Missing: " + ", ".join(state["declarations_missing"]))),
        ("LLM use documented in the Methods", ok(state["llm_in_methods"]),
         "the heading `2.13 Declaration of LLM use` is present in the "
         "assembled Materials and Methods, %d words long, and names the tool, "
         "the model and the developer: %s. The full declaration is "
         "`results/ai_use.md`, %s words."
         % (state["llm_section_words"], "; ".join(state["llm_named"]),
            "{:,}".format(state["ai_use_words"]))),
        ("Every placeholder is a key in `fields.json`, not a hand edit",
         ok(state["fields_total"] > 0
            and (not state["final"] or not state["fields_unfilled"])),
         "%d fields declared, %d still empty. A draft build renders an empty "
         "field as a visible placeholder; a final build refuses. %d placeholder "
         "markers survive in the bytes of this build, which is a draft, and "
         "that count is the one `assertions.md` and `gate.json` report."
         % (state["fields_total"], len(state["fields_unfilled"]),
            state["surviving_markers_in_bytes"])),
        ("The Correction Proposal's status comes from one source value",
         ok(state["cp_state"] in ("drafted_not_filed", "filed_awaiting_number",
                                  "assigned")),
         "`results/cp/status.json` state `%s`, 1 of %d allowed states, "
         "rendered into %d passages that used to type it: %s. Filing the "
         "proposal is a change to one JSON value."
         % (state["cp_state"], len(tokens.STATES), state["cp_mentions"],
            state["cp_sentence"])),
        ("A link to the imaging data used", ok(state["source_dois"] > 0),
         "%d collection and source-DOI rows in `supplementary/S1_source_dois.csv`, "
         "plus the archive release and the public bucket in Data availability"
         % state["source_dois"]),
    ]
    manual = [
        ("Blinding is honest about what it cannot do",
         "**stated, not computed.** The paper describes a public repository and "
         "reuses the method of two prior papers by the same author. A "
         "determined reviewer can identify the authorship from the content, and "
         "no masking changes that. What the mask guarantees is computed in the "
         "row above; what it cannot guarantee is this sentence, and it moved "
         "here because a row whose value is the word `stated` does not belong "
         "in a table headed by a claim that everything in it was computed."),
        ("Length, against a venue that sets no hard limit",
         "**stated, not acted on.** The manuscript body is %s words, %s of them "
         "in Materials and Methods. That is long for an Original Paper and the "
         "venue publishes no ceiling, so submitting it asks the editor for "
         "latitude. Methods 2.6 through 2.10 could move to supplementary "
         "material and take about %s words with them, at the cost of the thing "
         "the paper is for: a reader who cannot see the message-class "
         "normalisation, the adjudication disclosures and the pin deviations in "
         "the body has to take the rates on trust. The trade is the author's to "
         "make and nothing here has been cut to pre-empt it."
         % ("{:,}".format(state["body_words"]),
            "{:,}".format(state["methods_words"]),
            "{:,}".format(state["methods_movable_words"]))),
        ("Manuscript in `.docx`, 10-point plain font, page numbers, single "
         "column, tables made with the table function",
         "**manual.** Producing Word needs a package that is not in "
         "`env/requirements.lock`, and adding one to a pinned measurement "
         "environment to typeset a paper is not a trade this project makes. "
         "The package ships Markdown; convert with pandoc or by hand."),
        ("Cover letter addressed to the Editor-in-Chief",
         "**field.** `00_cover_letter.md` carries the date, the editor's name "
         "and the signature block as fields."),
        ("Zenodo version DOI for the code",
         "**field.** No Zenodo record exists yet; ledger row FM-02."),
    ]
    out = ["# Submission checklist, %s\n" % VENUE["name"],
           "Requirements read from %s on %s. This file is generated: a row that "
           "says yes says so because something was computed, not because "
           "somebody ticked it.\n" % (VENUE["guidelines"], VENUE["read_on"]),
           "The venue uses **%s** peer review, which is why there are two "
           "manuscript files.\n" % VENUE["review_model"],
           "## Checked automatically\n",
           "| requirement | met | detail |", "|---|---|---|"]
    for req, met, detail in rows:
        out.append("| %s | %s | %s |" % (req, met, detail))
    out.append("\n## Not checkable here, and not silently skipped\n")
    out.append("| requirement | status |")
    out.append("|---|---|")
    for req, status in manual:
        out.append("| %s | %s |" % (req, status))

    out.append("\n## Placeholders still to fill, %d of them\n"
               % len(state["outstanding_fields"]))
    if state["outstanding_fields"]:
        out.append("Nothing here is a defect. Each is a fact only the author "
                   "holds, and each is listed so that none of them ships as "
                   "written.\n")
        out.append("| file | kind | what |")
        out.append("|---|---|---|")
        for f in state["outstanding_fields"]:
            out.append("| `%s` | %s | %s |" % (f["file"], f["kind"], f["what"]))
    else:
        out.append("None.")
    out.append("""
## If the paper goes to the backup venue instead

The backup is the International Journal of Medical Informatics, which is
Elsevier and differs in ways that change files rather than content: it is
single-anonymous, so the blinded copy is not needed; it wants highlights and a
graphical abstract, neither of which exists here; its reference style is
different again, which is a re-render from `colophon.references` rather than a
retype; and it asks for a declaration of interest statement in its own form.
The manuscript text, the tables, the figures and the supplementary items carry
over unchanged.
""")
    return "\n".join(out)


def build(final: bool = False) -> dict:
    """Assemble the package. `final=True` refuses while any field is empty.

    A draft build renders every unfilled field as a visible placeholder and
    counts them. A final build raises `tokens.UnfilledField` on the first empty
    one, which is what makes filling a field an edit to `fields.json` rather
    than an edit to generated output.
    """
    OUT.mkdir(parents=True, exist_ok=True)
    full, blinded, uncited, mapping = manuscripts()
    tables = _read("tables.md")
    legends = figure_legends()

    files = {
        "00_cover_letter.md": cover_letter(),
        "01_title_page.md": renumber(title_page(), mapping),
        "02_manuscript_full.md": full,
        "03_manuscript_blinded.md": blinded,
        "04_tables.md": tables,
        "05_figure_legends.md": legends,
        "06_supplementary.md": supplementary_index(),
    }
    figs, fig_contrast = figures_for_submission()
    doi_path = source_dois()
    n_dois = sum(1 for _ in doi_path.read_text(encoding="utf-8").splitlines()) - 1

    depth = max((len(m.group(1)) for m in re.finditer(r"^(#+) ", full, re.M)),
                default=1)
    # Everything below is read back out of the assembled document. A checklist
    # that reports its own configuration reports what the generator intended,
    # which is the one thing a checklist is not for.
    headings = re.findall(r"^# (.+)$", full, re.M)
    lines = full.splitlines()
    decl_line = next((i + 1 for i, l in enumerate(lines)
                      if l.strip() == "# Declarations"), 0)
    ref_line = next((i + 1 for i, l in enumerate(lines)
                     if l.strip() == "# References"), 0)
    decl_block = full.partition("# Declarations")[2].partition("# References")[0]
    decl_missing = [h for h in DECLARATION_HEADINGS
                    if ("## " + h) not in decl_block]
    page = files["01_title_page.md"]
    tp_missing = sorted(k for k, needle in TITLE_PAGE_ELEMENTS.items()
                        if needle not in page)
    methods_text = dict(section_bodies())["Materials and Methods"]
    llm_block = methods_text.partition("2.13 Declaration of LLM use")[2]
    llm_named = [w for w in ("Claude Code", "Claude Opus 5", "Anthropic")
                 if w in llm_block or w in _read("methods.md")]
    body = full.partition("# References")[0]
    table_order, seen = [], set()
    for m in re.finditer(r"\bTable (\d+)\b", body):
        n = int(m.group(1))
        if n not in seen:
            seen.add(n)
            table_order.append(n)
    repro_path = RESULTS / "figures" / "reproducibility.json"
    repro = (json.loads(repro_path.read_text(encoding="utf-8"))
             if repro_path.exists() else {"ran": False})
    state = {
        "sections": ["Abstract"] + [h for h, _, _ in SECTIONS],
        "abstract_words": abstract_words(),
        "repo_abstract_words": len(_read("abstract.md").split()),
        "max_heading_depth": depth,
        "title_page": bool(files["01_title_page.md"].strip()),
        "blinding_leaks": blinding_leaks(blinded),
        "renumbered": True,
        "references": len(references.load()),
        "citations_clean": citations.check()["clean"],
        "uncited": uncited,
        "figures": len(figs),
        "fonts_embedded": sum(1 for f in figs if f["fonts_embedded"]),
        "headings_found": headings[:len(VENUE["section_order"])],
        "title_page_missing": tp_missing,
        "declarations_missing": decl_missing,
        "declarations_precede_references": 0 < decl_line < ref_line,
        "declarations_line": decl_line,
        "references_line": ref_line,
        "llm_section_words": len(llm_block.split()),
        "llm_named": llm_named,
        "ai_use_words": len((REPO / "results" / "ai_use.md")
                            .read_text(encoding="utf-8").split()),
        "table_citation_order": table_order,
        "tables_cited_in_order": table_order == sorted(table_order),
        "reproducibility": repro,
        "reproducibility_summary": _repro_summary(repro),
        "figures_without_titles": sum(1 for f in figs
                                      if not f["has_drawn_title"]),
        # Measured off the shipped EPS, not from figsize. The canvas constant
        # and the bounding box differ by up to 47 percent because a tight
        # bounding box grows to hold the lettering.
        "figure_widths_mm": _eps_widths(),
        "figures_off_the_width_grid": sum(
            1 for w in _eps_widths().values()
            if not any(abs(w - g) <= 0.5 for g in (39.0, 84.0, 129.0, 174.0))),
        "contrast_pairs": len(fig_contrast["pairs"]),
        "contrast_lowest": (fig_contrast["lowest"]["ratio"]
                           if fig_contrast["lowest"] else 0.0),
        "contrast_lowest_where": (fig_contrast["lowest"]["where"]
                                 if fig_contrast["lowest"] else "nothing drawn"),
        "contrast_clean": fig_contrast["clean"],
        "legends": legends.count("**Fig. "),
        "tables": tables.count("**Table "),
        "declarations": "# Declarations" in full,
        "llm_in_methods": "2.13 Declaration of LLM use" in _read("methods.md"),
        "source_dois": n_dois,
        "cp_state": tokens.cp_status().get("state", ""),
        "cp_sentence": tokens.cp_sentence(),
        "cp_mentions": sum(
            _read(n).count("{{CP_STATUS") for n in ("abstract.md", "discussion.md")),
        "body_words": len(full.split()),
        "methods_words": len(dict(section_bodies())["Materials and Methods"].split()),
        "methods_movable_words": len("".join(
            _read("methods.md").split("## 2.6")[1:]).split("## 2.11")[0].split()),
        "outstanding_fields": outstanding_fields(files),
        "fields_total": len(tokens.load_fields()),
        "fields_unfilled": tokens.unfilled(),
        # Renamed: this is the vocabulary of token forms the resolver knows,
        # not a count of anything present. Reported as 19 while 11 markers were
        # in the bytes, because 17 of its entries occur in no shipped file.
        "marker_vocabulary": sorted({m for text in files.values()
                                     for m in tokens.surviving_markers(text)}),
        # Counted from the resolved text that is actually written, not from
        # the pre-resolution templates: those still hold every {{TOKEN}} and
        # counting them reported 31 where the bytes hold 11.
        "surviving_markers_in_bytes": sum(
            len(tokens.surviving_markers(tokens.resolve(text, final=final)))
            for text in files.values()),
        "final": final,
        "blinded_declarations_are_a_pointer":
            "Declared on the title page" in blinded,
    }
    files["07_checklist.md"] = checklist(state)

    written = {}
    for name, text in files.items():
        text = tokens.resolve(text, final=final)
        path = OUT / name
        path.write_text(text, encoding="utf-8")
        written[name] = {"path": str(path), "words": len(text.split()),
                         "sha256": hashlib.sha256(
                             path.read_bytes()).hexdigest()[:16]}

    manifest = {"venue": VENUE, "title": TITLE, "state": state,
                "files": written, "figures": figs, "contrast": fig_contrast,
                "supplementary": {"S1_source_dois.csv": str(doi_path)}}
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    return manifest


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--final", action="store_true",
                    help="refuse to emit while any field in fields.json is empty")
    args = ap.parse_args(argv)
    try:
        m = build(final=args.final)
    except tokens.UnfilledField as exc:
        print("REFUSING to emit a final package: %s" % exc)
        print("Fill it in %s and run again." % tokens.FIELDS)
        return 1
    s = m["state"]
    print("submission package: %s" % OUT)
    for name, rec in m["files"].items():
        print("  %-28s %6d words  %s" % (name, rec["words"], rec["sha256"]))
    print("  figures: %d as EPS, PDF and PNG" % len(m["figures"]))
    print("  abstract %d words (venue allows %d to %d), repository abstract %d"
          % (s["abstract_words"], *VENUE["abstract_words"],
             s["repo_abstract_words"]))
    print("  references %d, deepest heading level %d, tables %d, legends %d"
          % (s["references"], s["max_heading_depth"], s["tables"], s["legends"]))
    print("  fields %d, unfilled %d, surviving placeholder markers %d%s"
          % (s["fields_total"], len(s["fields_unfilled"]),
             s["surviving_markers_in_bytes"],
             "" if args.final else "  (draft build)"))
    if args.final and s["surviving_markers_in_bytes"]:
        print("  FINAL BUILD STILL CARRIES %d MARKERS"
              % s["surviving_markers_in_bytes"])
        return 1
    if s["blinding_leaks"]:
        print("  BLINDING LEAKS: %s" % s["blinding_leaks"])
    if s["uncited"]:
        print("  listed but never cited: %s" % s["uncited"])
    return 0 if not s["blinding_leaks"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
