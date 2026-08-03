"""Cross-document consistency, and the sensitivities a headline must carry.

The build guard checks every figure against the ledger. It does not check
documents against each other, and a stale writer census shipped alongside a
current Table 1 fell straight through that gap: one said RT Structure Set was a
complete census of 19,358 objects, the other said it was in flight at 9,183 and
that incomplete classes "contribute nothing, not even a partial count". Both
were in the same deliverable. These are the checks that close it.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import pytest

MANUSCRIPT = Path("results/manuscript")


def _table(n: int) -> pd.DataFrame:
    p = MANUSCRIPT / ("table%d.csv" % n)
    if not p.exists():
        pytest.skip("tables not generated")
    return pd.read_csv(p)


def test_table1_and_the_writer_census_agree_on_every_class():
    """The exact gap that shipped. Two documents, one deliverable, opposite
    claims about whether a class is complete."""
    census = MANUSCRIPT / "table1_writers.md"
    if not census.exists():
        pytest.skip("writer census not generated")
    text = census.read_text(encoding="utf-8")
    t1 = _table(1)
    for row in t1.itertuples():
        name = row.sop_class
        line = next((l for l in text.splitlines()
                     if l.startswith("| %s |" % name)), None)
        if line is None:
            continue
        complete_in_t1 = "complete" in str(row.coverage) or "sample" in str(row.coverage)
        complete_in_census = "in flight" not in line
        assert complete_in_t1 == complete_in_census, (
            "Table 1 and the writer census disagree about %s.\n  Table 1: %s\n"
            "  census: %s" % (name, row.coverage, line.strip()))


def test_no_manuscript_table_prints_nan():
    """A nan in a published table reads as a defect in the measurement. An empty
    cell that means something has to say what it means."""
    # Scoped to the six tables of this manuscript. table2_floor_set.csv is a
    # different artefact whose empty cells mean "not applicable to this floor
    # class", and its markdown renders them blank rather than as nan, so the
    # rule that matters is checked on every document below.
    for n in range(1, 7):
        path = MANUSCRIPT / ("table%d.csv" % n)
        if not path.exists():
            continue
        frame = pd.read_csv(path)
        bad = {c: int(frame[c].isna().sum()) for c in frame.columns
               if frame[c].isna().any()}
        assert not bad, "%s has nan cells: %s" % (path.name, bad)
    for md in sorted(MANUSCRIPT.glob("*.md")):
        text = md.read_text(encoding="utf-8")
        assert "| nan |" not in text and " nan " not in text, (
            "%s prints nan" % md.name)


def test_table2_caption_matches_its_own_rows():
    """The caption was written for a two-tier ceiling and the Type 2 tier was
    added later, leaving a caption that its own KOS row contradicted."""
    md = MANUSCRIPT / "tables.md"
    if not md.exists():
        pytest.skip("tables not generated")
    text = md.read_text(encoding="utf-8")
    caption = text.split("## Table 2")[1].split("## Table 3")[0]
    t2 = _table(2)
    # Any class with non-conformant objects but no Type 1 binding must be
    # explicable from the caption, which means the caption has to name Type 2.
    anomalous = t2[(t2["non-conformant"] > 0)
                   & (t2["binds_provenance_type1"].astype(str).str.contains("no"))]
    if len(anomalous):
        assert "Type 2" in caption, (
            "%s has non-conformant objects without a Type 1 binding, so the "
            "caption must explain the second tier"
            % list(anomalous["sop_class_name"]))
        assert "cannot be non-conformant" not in caption


def test_leave_one_class_out_is_reported():
    """Ledger C3T-10. The paper argues object-weighted rates are distorted by
    concentration, so its own headline has to carry that sensitivity."""
    t2 = _table(2)
    assert "pct_uninformative_without_this_class" in t2.columns
    assert "pct_of_denominator" in t2.columns
    # The largest class must actually move the rate, or the column is decorative.
    largest = t2.sort_values("objects", ascending=False).iloc[0]
    headline = 100 * t2["conformant but uninformative"].sum() / t2["objects"].sum()
    shift = abs(float(largest["pct_uninformative_without_this_class"]) - headline)
    assert shift > 1.0, (
        "the largest class moves the headline by only %.2f points, so either the "
        "concentration argument or this column is wrong" % shift)


def test_table3_shows_every_level_not_only_the_first():
    """Rendering only the first level invites the reader to conclude identity
    appears nowhere else. For totalsegmentator that would be wrong."""
    t3 = _table(3)
    assert "levels_where_identity_appears" in t3.columns
    row = t3[t3.analysis_result_id == "totalsegmentator_ct_segmentations"]
    if len(row):
        levels = str(row.iloc[0]["levels_where_identity_appears"])
        assert "3" in levels and "4" in levels, levels


def test_the_paper_does_not_assert_an_unfiled_submission():
    """The abstract once said a Correction Proposal was submitted while the
    Discussion still carried unfilled placeholders."""
    for name in ("abstract.md", "discussion.md"):
        p = MANUSCRIPT / name
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        for placeholder in ("[DATE]", "[SUBMITTER]", "[LOG SUMMARY]", "[CP-ROW]"):
            assert placeholder not in text, "%s still carries %s" % (name, placeholder)
        if re.search(r"was submitted to the DICOM Secretariat", text):
            assert "has not been filed" not in text, (
                "%s both asserts and denies the submission" % name)
