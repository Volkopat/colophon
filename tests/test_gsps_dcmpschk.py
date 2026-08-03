"""Guards on Track D, the re-closed dcmpschk column for GSPS.

The defect these pin is not a wrong number, it is a right number that looked
like a wrong one: dcmpschk passed every object and the census recorded the pass
as a warning. Nothing in the output was obviously broken, so the guard has to be
a string search rather than a plausibility check.
"""
from __future__ import annotations

import csv
import subprocess

import pytest

from colophon import census, gsps_dcmpschk as track_d
from colophon.paths import RESULTS

PHASE2 = RESULTS / "phase2"

# The census manifest holds 1,086 Grayscale Softcopy Presentation State series,
# one object each. dcmpschk passes all of them.
GSPS_OBJECTS = 1086
GSPS_PASSES = 1086


def _rows():
    p = PHASE2 / "gsps_dcmpschk.csv"
    if not p.exists():
        pytest.skip("run python -m colophon.gsps_dcmpschk --run --report first")
    with p.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# --- the parse ----------------------------------------------------------------
def test_pass_line_is_never_a_finding():
    """Ledger D-02. `W: Test passed.` is a verdict, not a warning."""
    out = census.parse_dcmpschk("W: Test passed.\n")
    assert out["findings"] == []
    assert out["test_passed"] is True
    for row in _rows():
        assert "Test passed" not in row["message_template"], (
            "the dcmpschk verdict is recorded as a finding on %s"
            % row["sop_instance_uid"])


def test_banner_is_not_a_finding():
    """Ledger D-03. `Testing: <path>` names the input file, and counted as a
    finding it mints one message class per object off a temporary path."""
    out = census.parse_dcmpschk("W: Testing: C:\\tmp\\a.dcm\nW: Test passed.\n")
    assert out["findings"] == []
    assert len(out["banners"]) == 1
    assert out["test_passed"] is True
    for row in _rows():
        assert "Testing:" not in row["message_template"]


def test_a_real_finding_is_still_recorded():
    """A filter that drops everything would pass both tests above."""
    out = census.parse_dcmpschk(
        "W: Testing: C:\\tmp\\a.dcm\n"
        "E: Attribute Laterality is missing\n"
        "W: Value dubious for this VR\n")
    assert out["test_passed"] is False
    assert [f["severity"] for f in out["findings"]] == ["Error", "Warning"]
    assert out["findings"][0]["message"].startswith("E: ")


def test_severity_prefix_is_stripped_before_the_body_is_matched():
    assert census.strip_dcmpschk_prefix("W: Test passed.") == ("W", "Test passed.")
    assert census.strip_dcmpschk_prefix("E: boom") == ("E", "boom")
    assert census.strip_dcmpschk_prefix("no prefix") == ("", "no prefix")


def test_the_runner_does_not_gate_on_exit_status():
    """Project rule. dcmpschk returned 0 on every object in this class, pass or
    not, so a runner that branched on it would report the same thing either
    way."""
    class FakeProc:
        stdout = "W: Testing: x.dcm\nE: Attribute Laterality is missing\n"
        stderr = ""
        returncode = 0

    real = subprocess.run
    subprocess.run = lambda *a, **k: FakeProc()
    try:
        out = census.run_dcmpschk(__file__)
    finally:
        subprocess.run = real
    assert out["returncode"] == 0
    assert out["test_passed"] is False
    assert len(out["findings"]) == 1


# --- the measurement ----------------------------------------------------------
def test_pass_count_is_pinned():
    """Ledger D-01."""
    rows = _rows()
    uids = {r["sop_instance_uid"] for r in rows if r["sop_instance_uid"]}
    assert len(uids) == GSPS_OBJECTS, (
        "expected %d GSPS objects, found %d" % (GSPS_OBJECTS, len(uids)))
    passed = {r["sop_instance_uid"] for r in rows if r["dcmpschk_pass"] == "pass"}
    assert len(passed) == GSPS_PASSES
    assert not [r for r in rows if r["dcmpschk_pass"] not in ("pass", "fail")], (
        "a fetch or read failure would leave rows with neither verdict")


def test_every_object_has_a_row_even_with_no_findings():
    """An object dcmpschk says nothing about must still appear, or the pass
    count has to be inferred from an absence."""
    rows = _rows()
    quiet = [r for r in rows if not r["message_class_id"]]
    assert len(quiet) == GSPS_OBJECTS
    assert all(r["test_passed_line"] == "yes" for r in quiet)


def test_one_banner_line_per_object():
    rows = _rows()
    banners = [int(r["banner_lines"]) for r in rows if r["banner_lines"] != ""]
    assert banners and set(banners) == {1}


def test_cross_validator_direction():
    """Ledger D-04. Reported tool versus tool, with no adjudication."""
    xv = track_d.cross_validator()
    assert xv["total_objects"] == GSPS_OBJECTS
    dci = xv["validators"]["dciodvfy"]
    dv = xv["validators"]["dicom-validator"]
    assert dci["objects_lower_bound"] == GSPS_OBJECTS and dci["exact"]
    assert dv["objects_lower_bound"] == 0 and dv["exact"]
    rows = _rows()
    flagged = {r["sop_instance_uid"] for r in rows if r["message_class_id"]}
    assert flagged == set(), "dcmpschk flags no object in this class"


def test_the_write_up_names_no_winner():
    """Conformance is scored by third party tools. The write-up reports the
    disagreement and must not resolve it."""
    md = RESULTS / "phase2_gsps_dcmpschk.md"
    if not md.exists():
        pytest.skip("run python -m colophon.gsps_dcmpschk --report first")
    text = md.read_text(encoding="utf-8").lower()
    assert "no attempt is made here to decide which reading is correct" in text
    for banned in ("false positive", "spurious", "wrong", "incorrectly flags"):
        assert banned not in text, (
            "the write-up adjudicates a validator with %r" % banned)


def test_proposed_ledger_rows_match_the_schema():
    """Track D does not own results/ledger.csv. Its rows are proposed in the
    ledger's own schema so that merging them is a copy."""
    import json
    from colophon import ledger
    p = RESULTS / "pending_ledger" / "track_d.json"
    if not p.exists():
        pytest.skip("run python -m colophon.gsps_dcmpschk --report first")
    rows = json.loads(p.read_text(encoding="utf-8"))
    assert [r["id"] for r in rows] == ["D-01", "D-02", "D-03", "D-04"]
    for r in rows:
        assert set(r) <= set(ledger.FIELDS), sorted(set(r) - set(ledger.FIELDS))
        assert r["status"] in ledger.VALID_STATUS
        if r["status"] == "MEASURED":
            for field in ("command", "source_file", "dropped"):
                assert r[field].strip(), "%s has no %s" % (r["id"], field)


def test_a_repeat_measurement_supersedes_a_failure_but_never_a_result():
    """Two copies of the run and a retry both append a second record for the
    same series. A success has to beat a failure or the retry does nothing, and
    a second success must not silently replace the first."""
    import json
    import tempfile
    import pathlib

    def rec(uid, status, passed=True):
        return {"series_instance_uid": uid, "sop_class_name": track_d.SOP_CLASS,
                "collection_id": "c", "analysis_result_id": "a",
                "status": status,
                "objects": ([] if status != "OK" else
                            [{"status": "OK", "sop_instance_uid": uid + ".1",
                              "test_passed": passed, "returncode": 0,
                              "banner_lines": 1, "findings": []}])}

    with tempfile.TemporaryDirectory() as tmp:
        path = pathlib.Path(tmp) / "records.jsonl"
        path.write_text("\n".join(json.dumps(r) for r in [
            rec("A", "FETCH_FAILED"), rec("A", "OK"),
            rec("B", "OK"), rec("B", "FETCH_FAILED"),
            rec("C", "OK"), rec("C", "OK", passed=False),
            "" if False else rec("D", "OK"),
        ]) + "\n{not json}\n", encoding="utf-8")
        real = track_d.RECORDS
        track_d.RECORDS = path
        try:
            out = track_d.load_records()
        finally:
            track_d.RECORDS = real
    by = {r["series_instance_uid"]: r for r in out["records"]}
    assert by["A"]["status"] == "OK", "a retry must supersede a failure"
    assert by["B"]["status"] == "OK", "a failure must not supersede a result"
    assert by["C"]["objects"][0]["test_passed"] is True, "first result wins"
    assert out["duplicate_lines"] == 3
    assert out["unparsable_lines"] == 1
    assert out["repeat_disagreements"] == 1, (
        "two successful measurements that disagree are counted, not resolved")
    assert out["failed_at_least_once"] == 2


def test_track_d_never_writes_the_census_records():
    """The census was running while this track ran. Nothing here may open its
    records file for writing."""
    source = (track_d.__file__ and
              open(track_d.__file__, encoding="utf-8").read())
    assert "census/records.jsonl" not in source.replace("\\", "/")
    assert track_d.RECORDS != census.RECORDS
    assert track_d.STATE != census.STATE


def test_disk_floor_exists_and_can_fire():
    """A guard that cannot fail is not a guard, and this one stands between a
    fetch loop and a full disk."""
    assert track_d.MIN_FREE_GB == 20.0
    assert track_d._disk_guard() >= track_d.MIN_FREE_GB
    real = track_d.MIN_FREE_GB
    track_d.MIN_FREE_GB = 1e9
    try:
        with pytest.raises(RuntimeError, match="aborting"):
            track_d._disk_guard()
    finally:
        track_d.MIN_FREE_GB = real
