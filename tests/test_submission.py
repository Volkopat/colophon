"""The submission package, asserted against the venue's stated requirements.

A checklist that a person ticks is a record of what somebody believed. This
file is what makes the checklist a record of what was computed: every row in
`07_checklist.md` that says yes has a test here behind it, and a requirement
that stops being met fails the build rather than shipping with a tick beside it.

The package is built once for the module, because building it draws six figures.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

from colophon import citations, references, submission
from colophon.paths import RESULTS

# The public archive ships the harness that produces the measurements, not the
# manuscript. `results/manuscript/` narrative sources and `results/submission/`
# are excluded from it, so on a clone of the archive there is no package to
# assert against and these tests skip with a reason rather than erroring at
# import. They run in full in the working repository, which is where the
# submission is actually built. The ledger rows that name tests in this file
# stay valid either way, because the test still exists.
if not (RESULTS / "submission" / "fields.json").exists():
    pytest.skip("the assembled submission package is not in this checkout: "
                "fields.json holds author-held values that the archive does "
                "not carry, so the package cannot be rebuilt here; see README, "
                "'What this archive does not contain'",
                allow_module_level=True)

MANIFEST = submission.build()
OUT = submission.OUT
FULL = (OUT / "02_manuscript_full.md").read_text(encoding="utf-8")
BLINDED = (OUT / "03_manuscript_blinded.md").read_text(encoding="utf-8")
STATE = MANIFEST["state"]


def test_every_file_the_venue_asks_for_is_present():
    for name in ("00_cover_letter.md", "01_title_page.md",
                 "02_manuscript_full.md", "03_manuscript_blinded.md",
                 "04_tables.md", "05_figure_legends.md", "06_supplementary.md",
                 "07_checklist.md", "manifest.json"):
        path = OUT / name
        assert path.exists() and path.stat().st_size > 200, name


def test_the_sections_are_in_the_venues_order():
    headings = re.findall(r"^# (.+)$", FULL, re.M)
    assert headings[:6] == submission.VENUE["section_order"], headings[:6]
    assert headings[6:] == ["Declarations", "References"], headings[6:]


def test_the_abstract_is_within_the_word_limit():
    lo, hi = submission.VENUE["abstract_words"]
    n = submission.abstract_words()
    assert lo <= n <= hi, (
        "the venue abstract is %d words against a %d to %d limit" % (n, lo, hi))
    # And it is the short one that ships, not the repository one.
    assert submission.venue_abstract().split("\n")[0] in FULL
    repo = (RESULTS / "manuscript" / "abstract.md").read_text(encoding="utf-8")
    assert len(repo.split()) > hi, (
        "the repository abstract is now inside the limit, so the two forms "
        "should be reconciled rather than kept apart")


def test_the_keyword_count_is_in_range():
    lo, hi = submission.VENUE["keywords"]
    assert lo <= len(submission.KEYWORDS) <= hi
    assert "**Keywords**" in FULL


def test_no_more_heading_levels_than_the_venue_allows():
    depth = max(len(m.group(1)) for m in re.finditer(r"^(#+) ", FULL, re.M))
    assert depth <= submission.VENUE["max_heading_levels"], depth


# --- citation renumbering -----------------------------------------------------
def test_the_references_are_numbered_by_order_of_first_citation():
    order = submission.first_appearance_order(FULL)
    assert order == sorted(order), (
        "the renumbered manuscript cites %s, which is not in ascending order, "
        "so first-appearance numbering did not take" % order[:12])
    assert order[0] == 1
    assert order == list(range(1, len(order) + 1))


def test_the_renumbering_is_a_bijection_onto_the_reference_list():
    listed = {e["n"] for e in references.load()}
    numbers = {int(t) for g in citations.MARKER.findall(FULL)
               for t in g.split(",")}
    body, _, reflist = FULL.partition("# References\n")
    entries = re.findall(r"^(\d+)\. ", reflist, re.M)
    assert len(entries) == len(listed), (
        "%d references rendered, %d in the list" % (len(entries), len(listed)))
    assert [int(e) for e in entries] == list(range(1, len(listed) + 1))
    assert numbers <= set(range(1, len(listed) + 1))


def test_every_reference_is_cited_in_the_assembled_manuscript():
    assert not STATE["uncited"], (
        "renumbered references %s are cited nowhere" % STATE["uncited"])


def test_the_two_versions_carry_the_same_reference_numbering():
    """Self-citations are left blank rather than deleted, which is what keeps
    the numbering identical, so a reviewer's reference 12 is the editor's."""
    def numbers(text):
        _, _, refs = text.partition("# References\n")
        return [int(n) for n in re.findall(r"^(\d+)\. ", refs, re.M)]
    assert numbers(FULL) == numbers(BLINDED)


# --- blinding -----------------------------------------------------------------
def test_the_blinded_copy_leaks_no_declared_token():
    leaks = submission.blinding_leaks(BLINDED)
    assert not leaks, "the blinded manuscript still contains %s" % leaks


def test_the_blinded_copy_leaks_nothing_a_plain_search_would_find():
    """The mask list is a list, and a list is only as good as what is on it.

    This is the independent check: a case-insensitive search for the things a
    reviewer would actually type, run against the file rather than against the
    mask table.
    """
    for needle in ("patil", "volkopat", "buffalo", "aycan", "digvijay",
                   "orcid", "gmail", "zenodo.21728", "spine-gsps",
                   "palimpsest"):
        assert needle not in BLINDED.lower(), needle


def test_the_blinded_declarations_point_at_the_title_page():
    """A competing-interests paragraph with the company name masked out still
    describes the author's employment. It is replaced, not masked."""
    assert STATE["blinded_declarations_are_a_pointer"]
    assert "Declared on the title page" in BLINDED
    assert "employment" not in BLINDED.split("# Declarations")[1]
    assert submission.WITHHELD in BLINDED


def test_the_self_citations_are_withheld_and_counted():
    keys = {e["key"] for e in references.load()}
    assert submission.SELF_CITATION_KEYS <= keys
    assert BLINDED.count(submission.WITHHELD) == len(submission.SELF_CITATION_KEYS)


def test_the_unblinded_copy_is_not_blinded():
    """A guard that cannot fail is not a guard: if the mask ran on both, this
    test is what notices."""
    assert "[AUTHOR]" not in FULL
    assert submission.WITHHELD not in FULL


# --- figures and tables -------------------------------------------------------
def test_six_figures_named_and_vector_with_fonts_embedded():
    figs = MANIFEST["figures"]
    assert len(figs) == 6
    for rec in figs:
        eps = Path(rec["eps"])
        assert eps.name == "Fig%d.eps" % rec["figure"]
        assert eps.exists() and eps.stat().st_size > 10000
        assert rec["fonts_embedded"], (
            "%s embeds no font program, which the venue requires of vector "
            "graphics" % eps.name)
        raw = eps.read_bytes()
        assert raw.startswith(b"%!PS-Adobe-3.0 EPSF-3.0")
        assert b"%%CreationDate" not in raw


def test_the_figures_regenerate_byte_identical():
    before = {rec["figure"]: rec["sha256_eps"] for rec in MANIFEST["figures"]}
    figs, _contrast = submission.figures_for_submission()
    rebuilt = {rec["figure"]: rec["sha256_eps"] for rec in figs}
    assert before == rebuilt


def test_every_figure_and_table_has_a_caption():
    legends = (OUT / "05_figure_legends.md").read_text(encoding="utf-8")
    assert legends.count("**Fig. ") == 6
    tables = (OUT / "04_tables.md").read_text(encoding="utf-8")
    assert tables.count("**Table ") >= 6


def test_the_supplementary_index_points_at_files_that_exist():
    from colophon.paths import REPO
    text = (OUT / "06_supplementary.md").read_text(encoding="utf-8")
    paths = re.findall(r"\| `([^`]+)` \|", text)
    assert len(paths) >= 8
    for rel in paths:
        target = OUT / rel if rel.startswith("supplementary/") else REPO / rel
        assert target.exists(), "supplementary index names missing %s" % rel


# --- the checklist ------------------------------------------------------------
def test_the_checklist_records_no_unmet_requirement():
    text = (OUT / "07_checklist.md").read_text(encoding="utf-8")
    assert "**NO**" not in text, (
        "the checklist reports an unmet requirement:\n" +
        "\n".join(l for l in text.split("\n") if "**NO**" in l))


def test_the_checklist_lists_every_outstanding_placeholder():
    text = (OUT / "07_checklist.md").read_text(encoding="utf-8")
    for field in STATE["outstanding_fields"]:
        assert field["file"] in text
    assert "Placeholders still to fill" in text


def test_the_checklist_names_what_it_cannot_check():
    """Silent truncation reads as full coverage, here as much as anywhere."""
    text = (OUT / "07_checklist.md").read_text(encoding="utf-8")
    assert "Not checkable here, and not silently skipped" in text
    assert "docx" in text and "manual" in text


# --- numbers ------------------------------------------------------------------
TAG = re.compile(r"\(\d{4},[0-9A-Fa-f]{4}\)")
VERSION = re.compile(r"\b\d+\.\d+\.\d+\b")
UID = re.compile(r"\b\d+(?:\.\d+){3,}\b")
DATESTAMP = re.compile(r"\b\d{8,}\b")
ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
THOUSANDS = re.compile(r"\b\d{1,3}(?:,\d{3})+\b")
DECIMAL_UNIT = re.compile(r"\b(\d+\.\d+)\s*(?:percent|TB|GB|MB)\b")

PACKAGE_DOCS = ["00_cover_letter.md", "02_manuscript_full.md",
                "03_manuscript_blinded.md", "07_checklist.md"]


@pytest.mark.parametrize("name", PACKAGE_DOCS)
def test_every_number_in_the_package_is_backed(name):
    """The cover letter is the one document in the package that is authored
    here rather than assembled, so it is the one that can invent a number."""
    from tests.test_results_doc import _backing, _is_backed
    text = (OUT / name).read_text(encoding="utf-8")
    for pattern in (TAG, UID, VERSION, DATESTAMP, ISO_DATE):
        text = pattern.sub(" ", text)
    backing = _backing()
    quoted = set(THOUSANDS.findall(text)) | set(DECIMAL_UNIT.findall(text))
    unbacked = sorted(q for q in quoted if not _is_backed(q, backing))
    assert not unbacked, "%s quotes %s, which nothing in results/ carries" % (
        name, ", ".join(unbacked))


def test_the_manifest_records_what_shipped():
    m = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
    assert m["venue"]["name"] == submission.VENUE["name"]
    assert m["title"] == submission.TITLE
    for name, rec in m["files"].items():
        path = Path(rec["path"])
        assert path.exists()
        assert hashlib.sha256(path.read_bytes()).hexdigest()[:16] == rec["sha256"]


def test_the_title_is_the_one_the_manuscript_carries():
    abstract = (RESULTS / "manuscript" / "abstract.md").read_text(encoding="utf-8")
    assert submission.TITLE in abstract
    assert submission.TITLE in (OUT / "01_title_page.md").read_text(encoding="utf-8")


def test_the_employment_disclosure_names_the_two_works_it_says_it_names():
    """The declaration carries two citation numbers inside a field value.

    Reference numbers are computed from citation order, so a number typed into
    a field is not renumbered with the rest and would go stale in silence the
    next time the reference list moves. The first attempt at this field said
    `[18] and [19]`, which named the prior article and its own Zenodo archive
    rather than the two prior works the sentence above it names. This asserts
    the field agrees with that sentence, read out of the shipped file.
    """
    import re
    from colophon.paths import RESULTS
    page = (RESULTS / "submission" / "01_title_page.md").read_text(encoding="utf-8")
    block = page[page.find("The employment window"):]
    block = block[:block.find("**Whether any object")]
    named = re.findall(r"\[(\d+)\]", block)
    assert len(named) == 4, (
        "expected two works named twice, once by the sentence and once by the "
        "field, found %r" % named)
    sentence, field = set(named[:2]), set(named[2:])
    assert sentence == field, (
        "the sentence names %s and the field names %s, so one of them is stale"
        % (sorted(sentence), sorted(field)))
    refs = (RESULTS / "submission" / "02_manuscript_full.md").read_text(encoding="utf-8")
    refs = refs.split("# References")[-1]
    for n in sorted(sentence, key=int):
        entry = [l for l in refs.splitlines()
                 if re.match(r"^\s*%s\.\s" % n, l)]
        assert entry, "reference %s does not exist" % n
        assert "Patil D" in entry[0], (
            "reference %s is not a prior work of the author: %s"
            % (n, entry[0][:90]))


def test_no_identifier_of_any_shape_reaches_the_blinded_copy():
    """Blinding is a mask list, and a mask list goes stale silently.

    The corresponding email was written twice, once in `fields.json` and once as
    a literal in `TOKEN_MASKS`. Changing the field alone would have shipped a
    blinded copy carrying the new address in clear, because the mask still named
    the old one. That is not a defect in a value, it is a defect in keying a
    guard to a copy of the thing it guards.

    So this does not check the mask list. It checks the shipped blinded copy for
    anything shaped like an identifier, whatever the mask list happens to say.
    """
    import json
    import re
    from colophon.paths import RESULTS

    blinded = (submission.OUT / "03_manuscript_blinded.md").read_text(
        encoding="utf-8")

    store = json.loads(
        (RESULTS / "submission" / "fields.json").read_text(encoding="utf-8"))
    for key in ("affiliation", "corresponding_email", "signature_block"):
        value = str(store.get(key, {}).get("value", "")).strip()
        if value and "{{" not in value:
            assert value not in blinded, (
                "the blinded copy carries the %s field verbatim: %r" % (key, value))

    # Shapes, not values. An address or an ORCID that no mask names still fails.
    allowed_emails = {"dicom@dicomstandard.org"}
    found = set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
                           blinded)) - allowed_emails
    assert not found, "unmasked email in the blinded copy: %s" % sorted(found)

    orcids = re.findall(r"\b\d{4}-\d{4}-\d{4}-\d{3}[\dX]\b", blinded)
    assert not orcids, "unmasked ORCID in the blinded copy: %s" % orcids


def test_the_one_sampled_class_carries_an_interval_and_the_censuses_do_not():
    """An interval on a complete enumeration is not conservative, it is wrong.

    Seven classes are censuses and carry none. Segmentation is a PRE-06 draw,
    so every proportion on it is an estimate, and the paper previously quoted
    those proportions bare while Methods promised an interval twice. The
    interval is quoted now, unadjusted, with the deficit named rather than
    papered over with the frame's planning ICC.
    """
    from colophon import seg_intervals
    report = seg_intervals.compute()
    body = (submission.OUT / "02_manuscript_full.md").read_text(encoding="utf-8")
    # Markdown wraps prose, so an interval can straddle a newline. Line
    # wrapping is cosmetic and the test should not force the paragraph to
    # bend around it.
    flat = " ".join(body.split())

    for label, g in report["grades"].items():
        pair = "%.2f to %.2f" % (g["lo"], g["hi"])
        assert pair in flat, (
            "the %s interval %s is not in the shipped manuscript" % (label, pair))
        assert g["lo"] < g["pct"] < g["hi"], (label, g)

    # The deficit is named, not hidden: the interval is declared a lower bound
    # and the implied design effect is stated beside it.
    assert "lower bound on width" in flat
    assert "%.1f" % report["design_effect_at_planning_icc"] in flat
    # And the planning value is explicitly not used to widen anything.
    assert "not used to widen" in flat

    # No interval is attached to a censused class.
    assert "carry no interval and need none" in flat
