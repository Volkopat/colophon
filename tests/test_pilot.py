"""Pin the Phase 2 pilot. Ten objects, not a sample, and nothing here is a rate.

The pilot's job was to answer one question and to capture provenance for later.
These tests pin the answer and the capture, and they guard the two rules that
would silently corrupt either: counting raw lines, and treating ten objects as
an estimate of anything.
"""
from __future__ import annotations

import csv

import pytest

from colophon import fetch, floor
from colophon.paths import RESULTS

PHASE2 = RESULTS / "phase2"


def _load(name):
    p = PHASE2 / name
    if not p.exists():
        pytest.skip("run python -m colophon.fetch --pilot first")
    with p.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def prov():
    return _load("pilot_provenance.csv")


@pytest.fixture(scope="module")
def classes():
    return _load("pilot_message_classes.csv")


def test_pilot_shape(prov):
    """Ledger P2P-01. Ten objects, at least three analysis results."""
    assert len(prov) == 10
    assert len({r["analysis_result_id"] for r in prov}) >= 3
    assert {r["sop_class_uid"] for r in prov} == {"1.2.840.10008.5.1.4.1.1.66.4"}
    assert {r["Manufacturer"] for r in prov} == {"QIICR"}


def test_pilot_is_capped_at_ten():
    """The instruction bounded this at ten series and the code enforces it."""
    import pandas as pd, tempfile, pathlib
    with tempfile.TemporaryDirectory() as tmp:
        p = pathlib.Path(tmp) / "sel.csv"
        pd.DataFrame({"SeriesInstanceUID": [str(i) for i in range(11)],
                      "series_size_MB": [1.0] * 11,
                      "series_aws_url": ["s3://x"] * 11,
                      "analysis_result_id": ["a"] * 11,
                      "collection_id": ["c"] * 11,
                      "ManufacturerModelName": ["m"] * 11}).to_csv(p, index=False)
        with pytest.raises(ValueError):
            fetch.pilot(p)


def test_target_message_class(classes):
    """Ledger P2P-02. The Phase 1 fixture's dcmqi message class in the corpus."""
    target = floor.message_class_id(
        "dciodvfy", floor.normalise(fetch.TARGET_TEMPLATE))
    hits = [c for c in classes if c["message_class_id"] == target]
    assert not hits, (
        "the ClinicalTrialSeries class appeared in the corpus pilot; the "
        "Phase 1 finding that it is fixture-specific no longer holds")


def test_no_dciodvfy_errors_in_the_pilot(classes):
    """Every dciodvfy message on these ten objects was a Warning. Recorded as
    an observation on ten objects, never as a rate."""
    sev = {c["severity_as_emitted"] for c in classes if c["validator"] == "dciodvfy"}
    assert sev == {"Warning"}


def test_dicom_validator_classes_are_the_phase1_floor(classes):
    """The six functional-group classes seen on both Phase 1 writers appear on
    every corpus object too, which is what a transferable floor looks like."""
    dv = [c for c in classes if c["validator"] == "dicom-validator"]
    assert len(dv) == 6
    assert all(int(c["objects"]) == 10 for c in dv)
    assert all("is unexpected" in c["message_template"] for c in dv)


def test_provenance_states(prov):
    """Ledger P2P-04. Three states, never two."""
    for r in prov:
        assert r["SoftwareVersions_state"] in {"absent", "empty", "non_empty"}
    assert {r["SoftwareVersions_state"] for r in prov} == {"non_empty"}, (
        "no zero-length SoftwareVersions in this pilot; a Type 1 violation "
        "would be a finding and must not appear silently")


def test_software_versions_are_commit_hashes(prov):
    """Ledger P2P-09."""
    vals = [r["SoftwareVersions"] for r in prov]
    for v in vals:
        assert len(v) == 7 and all(c in "0123456789abcdef" for c in v), v
    assert len(set(vals)) == 5


def test_file_meta_names_dcmtk(prov):
    """Ledger P2P-05. The encoding library's encoding library."""
    ivn = [r["ImplementationVersionName"] for r in prov]
    assert sum(v.startswith("OFFIS_DCMTK") for v in ivn) == 8
    assert not any("dcmqi" in v.lower() for v in ivn), (
        "no object names dcmqi in its file meta, which is the point")


def test_contributing_equipment(prov):
    """Ledger P2P-06. dcmqi never writes it."""
    present = [r for r in prov
               if str(r["ContributingEquipmentSequence_present"]).lower() == "true"]
    assert not present


def test_counting_unit_is_the_object_not_the_line(classes, prov):
    """A class cannot be reported on more objects than were validated. This is
    the guard against the numerator-exceeds-denominator failure the prior
    project shipped."""
    n = len(prov)
    for c in classes:
        assert 1 <= int(c["objects"]) <= n, (
            "%s reported on %s of %d objects" % (c["message_class_id"],
                                                 c["objects"], n))
