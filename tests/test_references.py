"""The citation guard, asserted.

`colophon.citations` computes the report. This file is where a defect in it
fails the build, on the same argument as `tests/test_prose.py`: the prior
project shipped two retired figures that survived a careful human read, so
prose is tested rather than read. A bare surname is the citation equivalent, and
it survives a read even better than a stale number does, because there is
nothing in it to look wrong.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from conftest import need_submission

from colophon import citations
from colophon.paths import RESULTS

REPORT = citations.check()
MANUSCRIPT = RESULTS / "manuscript"


def test_the_reference_list_is_contiguous_from_one():
    n = REPORT["references"]
    assert n["count"] > 0, "references.md parses to no entries"
    assert n["contiguous_from_one"], "missing numbers: %s" % n["missing"]


def test_every_marker_in_the_text_resolves():
    assert not REPORT["cited_but_missing"], (
        "the manuscript cites %s, which references.md does not carry"
        % REPORT["cited_but_missing"])


def test_every_entry_is_cited():
    """A reference nothing cites is padding, and padding is how a list stops
    being a record of what was read."""
    assert not REPORT["listed_but_never_cited"], (
        "references.md lists %s, which nothing cites"
        % REPORT["listed_but_never_cited"])


def test_every_entry_carries_a_resolvable_identifier():
    """A DOI, an arXiv id or a URL. A citation that resolves to nothing is
    removed from the text rather than left as a name."""
    assert not REPORT["entries_without_an_identifier"], (
        "entries %s carry no DOI, arXiv id or URL"
        % REPORT["entries_without_an_identifier"])


def test_no_bare_surname_citation_remains():
    bare = REPORT["bare_citations"]
    assert not bare, "\n".join(
        "%s: %s (%s)" % (b["file"], b["text"], b["context"]) for b in bare)


def test_the_standards_rows_match_the_pinned_status_table():
    """Every Correction Proposal and Supplement is stated with the title,
    status and edition the DICOM status table carries, read from the retrieved
    copy on disk rather than from memory."""
    assert not REPORT["standards_rows_disagreeing"], (
        "\n".join(REPORT["standards_rows_disagreeing"]))


def test_the_air_quotation_is_at_the_revision_and_page_the_discussion_names():
    """The drafted Discussion cited Rev 1.2 at page 16. The pinned document is
    Rev 1.3 and the passage is on printed page 17, so this checks both."""
    air = REPORT["air_quotation"]
    if not air["available"]:
        pytest.skip("the pinned AIR PDF is not in _cache")
    assert air["quote_found"], "the quoted passage is not in the pinned PDF"
    assert air["revision"] == "Rev. 1.3", air["revision"]
    assert air["printed_page"] == 17, air["printed_page"]
    discussion = (MANUSCRIPT / "discussion.md").read_text(encoding="utf-8")
    assert "IHE AIR Rev 1.3" in discussion
    assert "printed page 17" in discussion
    assert "Rev 1.2" not in discussion


def test_the_citing_document_list_is_complete():
    """A hand-written manuscript document that quietly stops being scanned is
    how this guard decays. Generated documents are exempt by name, because a
    marker typed into one is erased by the next run of its module."""
    generated = {"tables.md": "colophon/manuscript_tables.py",
                 "table1_writers.md": "colophon/tables.py",
                 "table2_floor_set.md": "colophon/tables.py",
                 "absence_claims.md": "colophon/absence.py"}
    exempt = set(generated) | {"references.md"}
    for path in MANUSCRIPT.glob("*.md"):
        if path.name in exempt:
            continue
        assert path.name in citations.CITING_DOCS, (
            "%s is a hand-written manuscript document and is not scanned for "
            "citations" % path.name)
    for name, module in generated.items():
        source = Path(module).read_text(encoding="utf-8")
        assert name in source, "%s does not write %s" % (module, name)


def test_no_generated_document_carries_a_citation_marker():
    """The other half of the same rule. A marker in a generated file would look
    like a citation and would not survive regeneration."""
    for name in ("tables.md", "table1_writers.md", "table2_floor_set.md"):
        path = MANUSCRIPT / name
        if not path.exists():
            continue
        found = citations.MARKER.findall(path.read_text(encoding="utf-8"))
        assert not found, "%s carries citation markers %s" % (name, found)


def test_the_front_matter_leaves_its_unknowns_as_fields():
    """The Zenodo version DOI does not exist until the release is cut, and the
    employment dates are the author's to state. Both must stay visible as
    fields rather than be filled with something plausible."""
    text = (MANUSCRIPT / "front_matter.md").read_text(encoding="utf-8")
    for needed in ("[FIELD:", "version DOI", "concept DOI"):
        assert needed in text, needed
    assert "10.5281/zenodo." in text, (
        "the prior harness DOI is the worked example of the pattern and is "
        "quoted so the field is unambiguous")


def test_the_guard_can_fail():
    """A guard that cannot fail is not a guard."""
    parsed = citations.entries("## H\n1. A doi:10.1000/x\n3. B no identifier\n")
    assert parsed == {1: "A doi:10.1000/x", 3: "B no identifier"}
    assert not citations.IDENTIFIER.search(parsed[3])
    assert citations.MARKER.findall("cited [7] and [8,9]") == ["7", "8,9"]
    assert citations.ET_AL.search("Longpre et al audited")


def test_every_version_string_derives_from_one_source():
    """Four files name this software's version and they must agree.

    The self-citation said `version 0.1.0` while `release_tag`, CITATION.cff
    and .zenodo.json all said v1.0.0, so the paper would have cited a Zenodo
    version that is never minted. The reference entry now takes
    `colophon.__version__` and this asserts the rest agree with it.
    """
    need_submission()
    import json
    import re
    from colophon import __version__
    from colophon.paths import REPO, RESULTS

    cff = (REPO / "CITATION.cff").read_text(encoding="utf-8")
    assert re.search(r'^version:\s*"?%s"?\s*$' % re.escape(__version__),
                     cff, re.M), "CITATION.cff disagrees with __version__"

    zen = json.loads((REPO / ".zenodo.json").read_text(encoding="utf-8"))
    assert zen["version"].lstrip("v") == __version__, (
        ".zenodo.json says %s" % zen["version"])

    fields = json.loads(
        (RESULTS / "submission" / "fields.json").read_text(encoding="utf-8"))
    tag = fields["release_tag"]["value"]
    assert tag.lstrip("v") == __version__, (
        "release_tag is %s and __version__ is %s, so the tag Zenodo archives "
        "and the version the paper cites are different things" % (tag, __version__))

    shipped = (RESULTS / "submission" / "02_manuscript_full.md").read_text(
        encoding="utf-8")
    entry = [l for l in shipped.split("# References")[-1].splitlines()
             if "colophon:" in l]
    assert entry, "the self-citation is not in the shipped reference list"
    assert "version %s," % __version__ in entry[0], entry[0][:160]
