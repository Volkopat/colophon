"""Pin Phase 1: the writer floor-set overlap, and the parser rules it rests on.

The parser is the measurement here. Two defects in it were caught during this
phase and both would have produced a plausible wrong number rather than an
error, so both are pinned.
"""
from __future__ import annotations

import csv

import pytest

from colophon import floor
from colophon.paths import RESULTS

CSV = RESULTS / "floor_set.csv"


@pytest.fixture(scope="module")
def rows():
    if not CSV.exists():
        pytest.skip("run python -m colophon.floor first")
    with CSV.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _classes(rows, writer, sop_class, validator):
    return {r["message_class_id"] for r in rows
            if r["writer"] == writer and r["sop_class"] == sop_class
            and r["validator"] == validator}


def test_headline_overlap(rows):
    """Ledger F1-01. The number this phase exists to produce."""
    w1 = _classes(rows, floor.W1, "SEG BINARY", "dciodvfy")
    w2 = _classes(rows, floor.W2, "SEG BINARY", "dciodvfy")
    assert len(w1) == 0, "highdicom SEG BINARY must draw no dciodvfy messages"
    assert len(w2) == 1, "dcmqi SEG BINARY must draw exactly one"
    assert floor.jaccard(w1, w2) == 0.0


def test_dicom_validator_floor_also_fails_to_transfer(rows):
    """Ledger F1-03, corrected. An earlier version of this test asserted the
    dicom-validator floor transfers perfectly. That was an artefact of a parser
    that dropped every finding on a tag with no parents: the dcmqi object has a
    seventh class, a missing Clinical Trial Coordinating Center Name, that was
    being discarded."""
    w1 = _classes(rows, floor.W1, "SEG BINARY", "dicom-validator")
    w2 = _classes(rows, floor.W2, "SEG BINARY", "dicom-validator")
    assert len(w1) == 6 and len(w2) == 7
    assert w1 < w2, "W1's classes are a strict subset of W2's"
    assert round(floor.jaccard(w1, w2), 4) == 0.8571


def test_unindented_findings_are_not_dropped():
    """The parser defect itself. A finding on a tag with no parents is printed
    without indentation and must still be captured."""
    text = "\n".join([
        'SOP class is "1.2.3" (Segmentation IOD)',
        "Errors",
        "======",
        "",
        'Module "Clinical Trial Series":',
        "Tag (0012,0060) (Clinical Trial Coordinating Center Name) is missing",
        "",
        'Module "Multi-frame Functional Groups":',
        "(5200,9229) (Shared Functional Groups Sequence):",
        "  Tag (0020,9116) (Plane Orientation Sequence) is unexpected",
    ])
    _, findings = floor.parse_dicom_validator(text)
    assert len(findings) == 2
    top = [f for f in findings if "Clinical Trial" in f["message"]][0]
    assert "Shared Functional Groups" not in top["message"], (
        "an unindented finding must not inherit the previous sequence context")


def test_emission_gaps_recorded(rows):
    """Ledger F1-04. Two of four nominated shared classes are single-writer."""
    assert set(floor.W2_EMISSION_GAPS) == {"SEG FRACTIONAL", "Parametric Map"}
    for sop_class in floor.W2_EMISSION_GAPS:
        assert not _classes(rows, floor.W2, sop_class, "dciodvfy")
    assert _classes(rows, floor.W1, "Parametric Map", "dciodvfy"), (
        "the highdicom-only Parametric Map cell must still carry its own floor")


def test_sr_sop_classes_differ(rows):
    """Ledger F1-05."""
    uids = {r["writer"]: r["sop_class_uid"] for r in rows
            if r["sop_class"] == "TID 1500 SR"}
    assert uids[floor.W1] == "1.2.840.10008.5.1.4.1.1.88.34"
    assert uids[floor.W2] == "1.2.840.10008.5.1.4.1.1.88.22"


def test_exit_status_is_not_a_verdict(rows):
    """Ledger F1-06. The object with an Error returned the same code as the
    objects without one."""
    dciodvfy = [r for r in rows if r["validator"] == "dciodvfy"]
    assert dciodvfy
    assert len({r["validator_returncode"] for r in dciodvfy}) == 1


def test_both_severity_forms_match():
    """Ledger F1-07. The separator-only rule missed dciodvfy's common form."""
    line_start = "Error - Missing attribute Type 2 Required Element=<X> Module=<Y>"
    separator = "(0x0099,0x1001)  ?  - Warning - Unrecognized tag or bad value"
    assert floor.SEVERITY.search(line_start).group(1) == "Error"
    assert floor.SEVERITY.search(separator).group(1) == "Warning"
    _, findings = floor.parse_dciodvfy("Segmentation\n" + line_start)
    assert [f["severity"] for f in findings] == ["Error"], (
        "the IOD banner must not be counted and the finding must not be "
        "UNCLASSIFIED")


def test_normalisation_keeps_the_diagnostic_and_drops_the_instance():
    """The over-normalisation defect: two different missing attributes must not
    collapse onto one message class, but the same defect on different frames
    must."""
    a = floor.normalise("Error - Missing attribute Type 2C Conditional "
                        "Element=<Laterality> Module=<GeneralSeries>")
    b = floor.normalise("Error - Missing attribute Type 2 Required "
                        "Element=<ClinicalTrialCoordinatingCenterName> "
                        "Module=<ClinicalTrialSeries>")
    assert a != b, "different attributes must be different message classes"
    assert "Laterality" in a and "Type 2C" in a

    f1 = floor.normalise("Warning - Bad value for frame 1 attribute (0x0028,0x0010)")
    f2 = floor.normalise("Warning - Bad value for frame 17 attribute (0x0028,0x0010)")
    assert f1 == f2, "frame index must not create a new message class"


def test_content_equality(rows):
    """Ledger F1-09. Recorded here so the claim cannot outlive the check."""
    import numpy as np, pydicom, SimpleITK as sitk
    F = floor.FIXTURE
    if not (F / "labels.nrrd").exists():
        pytest.skip("fixture absent")
    truth = sitk.GetArrayFromImage(sitk.ReadImage(str(F / "labels.nrrd"))).astype(np.uint8)
    src = sorted((F / "ct").glob("*.dcm"))
    z_of = {}
    for i, d in enumerate(sorted((pydicom.dcmread(p) for p in src),
                                 key=lambda x: float(x.ImagePositionPatient[2]))):
        z_of[round(float(d.ImagePositionPatient[2]), 3)] = i
    for rel in ("w1/seg_binary.dcm", "w1/seg_fractional.dcm", "w2/seg_binary.dcm"):
        ds = pydicom.dcmread(F / rel)
        frames = ds.pixel_array
        out = np.zeros(truth.shape, dtype=np.uint8)
        maxfrac = float(getattr(ds, "MaximumFractionalValue", 255) or 255)
        for i in range(int(ds.NumberOfFrames)):
            fg = ds.PerFrameFunctionalGroupsSequence[i]
            k = z_of[round(float(fg.PlanePositionSequence[0].ImagePositionPatient[2]), 3)]
            n = int(fg.SegmentIdentificationSequence[0].ReferencedSegmentNumber)
            plane = frames[i]
            mask = (plane.astype(float) / maxfrac >= 0.5
                    if ds.SegmentationType == "FRACTIONAL" else plane.astype(bool))
            out[k][mask] = n
        assert np.array_equal(out, truth), "%s does not decode to the source labels" % rel
