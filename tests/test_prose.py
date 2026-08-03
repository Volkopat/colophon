"""Numbers stated in hand-written prose have to exist in the ledger.

This is the control the prior project added after two retired figures reached a
manuscript: "Both survived a careful human read. Neither survives a string
search, so the search is a test."

Generated write-ups are not checked here, because they cannot drift: the module
that computes a number is the module that writes the sentence containing it.
Hand-written files are exactly where a number gets typed, and typed numbers are
the ones that go stale.
"""
from __future__ import annotations

import re

import pytest

from colophon.paths import LEDGER, REPO

# Hand-written files that quote measurements.
HAND_WRITTEN = [
    "README.md",
    "CITATION.cff",
    "results/README.md",
    "results/ai_use.md",
    "results/prior_art_recheck.md",
]

# Tokens that are identifiers rather than measurements: DICOM tags, DOIs,
# version strings, dates and the snapshot datestamp.
TAG = re.compile(r"\(\d{4},[0-9A-Fa-f]{4}\)")
DOI = re.compile(r"10\.\d{4,9}/\S+")
VERSION = re.compile(r"\b\d+\.\d+\.\d+\b")
DATESTAMP = re.compile(r"\b\d{8,}\b")
ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")

# What counts as a measurement in prose: a thousands-separated integer, or a
# decimal followed by a unit word.
THOUSANDS = re.compile(r"\b\d{1,3}(?:,\d{3})+\b")
DECIMAL_UNIT = re.compile(r"\b(\d+\.\d+)\s*(?:percent|TB|GB|MB)\b")


def _strip_identifiers(text: str) -> str:
    for pattern in (TAG, DOI, VERSION, DATESTAMP, ISO_DATE):
        text = pattern.sub(" ", text)
    return text


def _backing_text() -> str:
    """Everything a number in prose is allowed to be backed by.

    The ledger carries claims. `environment.json` carries pins, which are also
    numbers that appear in prose and also go stale, so it counts as backing. A
    number in neither is a number nothing generated.
    """
    from colophon.paths import RESULTS
    parts = [LEDGER.read_text(encoding="utf-8")]
    env = RESULTS / "environment.json"
    if env.exists():
        parts.append(env.read_text(encoding="utf-8"))
    return "\n".join(parts)


@pytest.mark.parametrize("name", HAND_WRITTEN)
def test_prose_numbers_are_in_the_ledger(name):
    path = REPO / name
    assert path.exists(), "%s is listed as hand-written but does not exist" % name
    text = _strip_identifiers(path.read_text(encoding="utf-8"))
    ledger_text = _backing_text()

    quoted = set(THOUSANDS.findall(text)) | set(DECIMAL_UNIT.findall(text))
    unbacked = sorted(q for q in quoted if q not in ledger_text)
    assert not unbacked, (
        "%s quotes %s, which no ledger row carries. Either the number is stale "
        "or the claim was never recorded." % (name, ", ".join(unbacked)))


def test_the_hand_written_list_is_complete():
    """A file that quietly stops being checked is how the guard decays."""
    from colophon.paths import RESULTS
    generated = {"phase0_census.md", "claim3_provenance.md", "prior_art.md",
                 "prisma_s_appendix.md",
                 "table1_writers.md", "floor_overlap.md", "phase1_variants.md",
                 "phase2_pilot.md", "phase2_census.md",
                 "phase2_gsps_dcmpschk.md", "claims_map.md",
                 "pre06_sampling_frame.md", "phase3_segmentation.md",
                 "ihe_air_table.md"}
    for path in RESULTS.glob("*.md"):
        if path.name in generated:
            continue
        rel = "results/%s" % path.name
        assert rel in HAND_WRITTEN, "%s is hand-written but unchecked" % rel


GENERATED_PHASE2 = {
    "net_rates_rwv_kos.md": "colophon/adjudicate_rwv_kos.py",
    "net_rates_gsps.md": "colophon/adjudicate_gsps.py",
    "net_rates_parametric_map.md": "colophon/adjudicate_pm.py",
    "net_rates_comprehensive_sr.md": "colophon/adjudicate_csr.py",
    "net_rates_comprehensive_3d_sr.md": "colophon/adjudicate_c3dsr.py",
}


def test_phase2_adjudications_are_exempt_by_rule_not_by_oversight():
    """results/phase2/ is outside the glob at the top of this file.

    That is correct rather than accidental: every markdown file there is
    emitted by the module that computes its numbers, so a rate cannot drift
    away from the table it came from. The exemption is recorded here so a file
    that stops being generated stops being exempt. Numbers in these files are
    checked against the rest of results/ by
    tests/test_results_doc.py::test_every_number_in_the_results_draft_is_backed,
    which reads them as backing for the manuscript.
    """
    from colophon.paths import RESULTS
    phase2 = RESULTS / "phase2"
    if not phase2.exists():
        return
    for path in phase2.glob("*.md"):
        assert path.name in GENERATED_PHASE2, (
            "%s is in results/phase2/ and is neither generated nor declared "
            "hand-written" % path.name)
    for name, module in GENERATED_PHASE2.items():
        source = (REPO / module).read_text(encoding="utf-8")
        assert name in source, "%s does not write %s" % (module, name)


def test_the_check_can_fail():
    """A guard that cannot fail is not a guard."""
    text = _strip_identifiers("the archive holds 999,999 derived series")
    assert THOUSANDS.findall(text) == ["999,999"]
    assert "999,999" not in _backing_text()
