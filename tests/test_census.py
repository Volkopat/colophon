"""Guards on the Phase 2 census. A census that quietly reports a partial class
as a rate is worse than one that reports nothing."""
from __future__ import annotations

import csv

import pytest

from conftest import need_census

from colophon import census
from colophon.paths import RESULTS

PHASE2 = RESULTS / "phase2"


def _rows(name):
    p = PHASE2 / name
    if not p.exists():
        pytest.skip("run python -m colophon.census --report first")
    with p.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_segmentation_is_out_of_scope():
    assert census.EXCLUDED == "Segmentation Storage"
    assert census.EXCLUDED not in census.CLASS_ORDER
    for r in _rows("census_rates.csv"):
        assert r["sop_class_name"] != census.EXCLUDED


def test_class_order_is_the_eight_non_seg_classes():
    assert len(census.CLASS_ORDER) == 8
    assert census.CLASS_ORDER[0] == "Real World Value Mapping Storage"
    assert census.CLASS_ORDER[-1] == "Enhanced SR Storage"


def test_no_partial_class_is_reported():
    """Ledger P2C-01. Only classes whose validated count reaches the manifest
    count may appear in the write-up."""
    need_census()
    md = RESULTS / "phase2_census.md"
    if not md.exists():
        pytest.skip("no census write-up yet")
    text = md.read_text(encoding="utf-8")
    body = text.split("## Error and warning class rates")[1]
    totals = census.class_totals()
    seen = {}
    for r in _rows("census_rates.csv"):
        seen[r["sop_class_name"]] = seen.get(r["sop_class_name"], 0) + int(r["objects"])
    for name, total in totals.items():
        if seen.get(name, 0) < total:
            assert name not in body, (
                "%s is only %d of %d validated but appears in the rates section"
                % (name, seen.get(name, 0), total))


def test_three_state_provenance():
    """Ledger P2C-03. Absent, zero-length and non-empty stay separate."""
    rows = _rows("census_provenance_states.csv")
    assert rows
    assert {r["state"] for r in rows} <= {"absent", "empty", "non_empty"}
    by = {}
    for r in rows:
        by.setdefault((r["sop_class_name"], r["carrier"]), 0)
        by[(r["sop_class_name"], r["carrier"])] += int(r["objects"])
    assert len(set(by.values())) >= 1
    assert any(r["state"] == "empty" and int(r["objects"]) > 0 for r in rows), (
        "zero-length values were observed in this census and must not vanish")


def test_dcmpschk_pass_line_is_not_a_finding():
    """Ledger P2C-04. dcmpschk prefixes its success line with a severity."""
    import subprocess, types
    captured = {}

    class FakeProc:
        stdout = "W: Test passed.\n"
        stderr = ""
        returncode = 0

    real = subprocess.run
    subprocess.run = lambda *a, **k: FakeProc()
    try:
        out = census.run_dcmpschk(__file__)
    finally:
        subprocess.run = real
    assert out["findings"] == [], (
        "dcmpschk reporting a pass must not be recorded as a warning")
