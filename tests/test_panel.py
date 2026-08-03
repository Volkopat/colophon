"""The panel is fixed before the floor is measured, so it is tested as data.

A panel that quietly loses a tool for a SOP class reports agreement where it has
only one opinion. spine-gsps had exactly that failure: when dcmpschk was missing
its runner returned the string "unavailable" and the run completed, scoring
every object as a validator disagreement.
"""
from __future__ import annotations

import pytest

from colophon import validate
from colophon.index import DERIVED_SOP_CLASSES


def test_panel_covers_every_derived_sop_class():
    assert set(validate.PANEL) == set(DERIVED_SOP_CLASSES)


def test_every_class_has_both_axes():
    """Ledger V-01."""
    for sop, axes in validate.PANEL.items():
        assert axes["conformance"], "%s has no conformance tool" % sop
        assert axes["reference_parse"], "%s has no reference reader" % sop


def test_panel_references_only_declared_tools():
    for sop, axes in validate.PANEL.items():
        for axis, keys in axes.items():
            for key in keys:
                assert key in validate.BY_KEY, "%s names unknown tool %s" % (sop, key)
                assert validate.BY_KEY[key].axis == axis, (
                    "%s lists %s under %s but it is a %s tool"
                    % (sop, key, axis, validate.BY_KEY[key].axis))


def test_dcmpschk_is_only_used_for_presentation_states():
    """Its own help says presentation state files. Listing it anywhere else
    would put a tool in the panel that cannot run."""
    for sop, axes in validate.PANEL.items():
        if "dcmpschk" in axes["conformance"]:
            assert "Presentation State" in sop


def test_pixelmed_is_only_used_for_structured_reports():
    for sop, axes in validate.PANEL.items():
        if "pixelmed_sr" in axes["conformance"]:
            assert "SR Storage" in sop


def test_pixelmed_is_in_the_panel_for_every_sr_class():
    """Ledger V-03. The decision was to include it, so a missing entry is a
    regression rather than an omission."""
    sr = [s for s in validate.PANEL if "SR Storage" in s]
    assert len(sr) == 3
    for sop in sr:
        assert "pixelmed_sr" in validate.PANEL[sop]["conformance"]


def test_excluded_tools_carry_a_reason_and_a_consequence():
    assert validate.EXCLUDED
    for rec in validate.EXCLUDED:
        for field in ("name", "axis", "reason", "consequence"):
            assert rec.get(field, "").strip(), (
                "%s is excluded without %s" % (rec.get("name"), field))


def test_pydicom_seg_is_not_in_the_panel():
    """Ledger V-05. It cannot be, under pydicom 3."""
    assert "pydicom_seg" not in validate.BY_KEY
    for axes in validate.PANEL.values():
        assert "pydicom_seg" not in axes["reference_parse"]


def test_same_codebase_pairs_are_declared():
    """Ledger V-06. dcmpschk and dcmp2pgm are one opinion, not two."""
    providers = {t.key: t.provider for t in validate.TOOLS}
    assert providers["dcmpschk"] == providers["dcmp2pgm"] == "DCMTK"
    doc = validate.__doc__
    assert "one opinion, not two" in doc
    assert "not independent authorship" in doc


def test_the_asymmetry_is_stated():
    """Ledger V-02. If this sentence goes, the instrument is being oversold."""
    doc = validate.__doc__
    assert "informative only on failure" in doc
    assert "round trip" in doc


@pytest.mark.parametrize("tool", validate.TOOLS, ids=lambda t: t.key)
def test_every_tool_pins_its_invocation(tool):
    """Any added flag changes the comparison baseline, so the command shape is
    part of the pinned record."""
    assert tool.invocation.strip()
    assert tool.axis in {"conformance", "reference_parse"}
    assert tool.provider.strip()


def test_availability_is_honest_about_gaps():
    """A missing tool has to surface as missing rather than as silence."""
    gaps = validate.missing()
    for rec in validate.availability():
        assert rec["status"], "%s has no status" % rec["name"]
        if rec["status"] == "MISSING":
            assert rec["name"] in gaps


def test_panel_is_not_uniform():
    """Ledger V-08. The panel must never be describable as an N-tool panel."""
    counts = {(r["n_conformance"], r["n_reference_parse"]) for r in validate.panel_table()}
    assert len(counts) > 1, (
        "if every class had the same shape, a single tool count would be "
        "honest and this guard would be pointless")
    doc = validate.__doc__
    assert "not a four-tool panel" in doc
    conformance_sizes = {len(a["conformance"]) for a in validate.PANEL.values()}
    parse_sizes = {len(a["reference_parse"]) for a in validate.PANEL.values()}
    assert len(conformance_sizes) > 1 or len(parse_sizes) > 1, (
        "coverage is uniform, so the per-class table would carry no information")
    # The classes with the thinnest reference-parse coverage are named, because
    # a single reader is not a second opinion.
    thin = sorted(s for s, a in validate.PANEL.items()
                  if len(a["reference_parse"]) == 1)
    assert thin, "if no class has a single reader, this guard is stale"
    for sop in thin:
        assert sop in {"RT Structure Set Storage",
                       "Key Object Selection Document Storage",
                       "Real World Value Mapping Storage"}


def test_lineages_cover_every_tool():
    """Counting tool names overstates independence. Lineage is what counts."""
    covered = {k for v in validate.LINEAGES.values() for k in v["tools"]}
    assert covered == set(validate.BY_KEY), (
        "tools outside a declared lineage: %s" % (set(validate.BY_KEY) - covered))
    assert len(validate.LINEAGES) < len(validate.TOOLS), (
        "there must be fewer lineages than tools, or the declaration says nothing")
    authors = {v["author"] for v in validate.LINEAGES.values()}
    assert len(authors) < len(validate.LINEAGES), (
        "at least one author must own more than one lineage, which is the fact "
        "the disclosure exists to state")


def test_declared_weaknesses_are_scoped_and_sourced():
    assert validate.WEAKNESSES
    for w in validate.WEAKNESSES:
        for field in ("scope", "statement", "status"):
            assert w.get(field, "").strip()
