"""Pin the Phase 1 variant ladder.

The ladder exists to stop one fragile number being quoted as though it were
robust, so the tests here pin the ladder's own numbers to the same standard. Two
things are pinned: the measured Jaccard at every rung, and the conclusion drawn
from them. If a validator build changes, or a variant definition drifts, or the
fixture is rebuilt differently, these fail loudly rather than quietly reporting
a different finding under the same sentence.

The tests read `results/phase1_variants.csv` rather than re-running the
validators, so a test run is fast and pins the artefact that the manuscript
would cite rather than a fresh measurement that might not match it.
"""
from __future__ import annotations

import csv
import json

import pytest

from colophon import ledger, variants
from colophon.paths import RESULTS

CSV = RESULTS / "phase1_variants.csv"
PENDING = RESULTS / "pending_ledger" / "track_b.json"

# Measured on 2026-08-02, dicom3tools snapshot 20260701065818 and
# dicom-validator 0.8.2 edition 2026c, on the Phase 1 fixture.
SEG_DCIODVFY = {"V0": 0.0, "V0R": 0.0, "V1": 0.6667, "V2": 0.0, "V3": 0.6667,
                "V4": 0.5, "V5": 0.5, "V6": 0.5, "V7": 0.8, "V8": 0.5,
                "V9": 0.8571}
SEG_DICOM_VALIDATOR = {"V0": 0.8571, "V0R": 0.8571, "V1": 0.875, "V2": 0.8571,
                       "V3": 0.8571, "V4": 0.8571, "V5": 0.8571, "V6": 0.8571,
                       "V7": 0.875, "V8": 0.8571, "V9": 0.8571}

# Classes held by exactly one writer. The quantity the transfer question turns
# on, and the one a shared perturbation does not dilute.
SEG_RESIDUE_DCIODVFY = {v: 1 for v in SEG_DCIODVFY}
SEG_RESIDUE_DCIODVFY["V9"] = 2
SEG_RESIDUE_DICOM_VALIDATOR = {v: 1 for v in SEG_DICOM_VALIDATOR}


@pytest.fixture(scope="module")
def rows():
    if not CSV.exists():
        pytest.skip("run python -m colophon.variants first")
    with CSV.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def cmp_rows(rows):
    return variants.compare(rows)


def _cell(cmp_rows, sop_class, validator, variant):
    return next(c for c in cmp_rows if c["sop_class"] == sop_class
                and c["validator"] == validator and c["variant"] == variant)


def test_baseline_reproduces_phase_one(cmp_rows):
    """Ledger B-01. If the harness does not reproduce the Phase 1 baseline it is
    measuring something else and every rung above it is uninterpretable."""
    c = _cell(cmp_rows, "SEG BINARY", "dciodvfy", "V0")
    assert (c["w1"], c["w2"], c["shared"]) == (0, 1, 0)
    assert c["jaccard"] == 0.0
    d = _cell(cmp_rows, "SEG BINARY", "dicom-validator", "V0")
    assert (d["w1"], d["w2"], d["shared"]) == (6, 7, 6)
    assert d["jaccard"] == 0.8571


def test_dciodvfy_ladder_jaccards(cmp_rows):
    """Ledger B-02. Every rung, pinned to the measured value.

    The set of values matters as much as any single one: the baseline 0.0 holds
    at only one of the nine rungs, so quoting 0.0 as the ladder's answer would
    be quoting the rung that happens to agree with the headline.
    """
    for variant_id, expected in SEG_DCIODVFY.items():
        c = _cell(cmp_rows, "SEG BINARY", "dciodvfy", variant_id)
        assert c["jaccard"] == expected, variant_id
    ladder = [SEG_DCIODVFY[v] for v in variants.LADDER]
    assert sum(1 for j in ladder if j == 0.0) == 1
    assert min(ladder) == 0.0 and max(ladder) == 0.8571


def test_dicom_validator_ladder_jaccards(cmp_rows):
    """Ledger B-03. Same pin on the second validator, which never reaches
    equality either but starts far closer to it."""
    for variant_id, expected in SEG_DICOM_VALIDATOR.items():
        c = _cell(cmp_rows, "SEG BINARY", "dicom-validator", variant_id)
        assert c["jaccard"] == expected, variant_id
        assert c["w1_subset_of_w2"], variant_id


def test_residue_is_stable_under_perturbation(cmp_rows):
    """Ledger B-10. The Jaccard moves along the ladder, the residue does not.

    A perturbation applied to both writers draws the same message class on both
    sides, which inflates the intersection. The count of classes held by exactly
    one writer is what survives that, and it is 1 at every rung under both
    validators, except under dciodvfy at V9 where the reader fails.
    """
    for variant_id, expected in SEG_RESIDUE_DCIODVFY.items():
        c = _cell(cmp_rows, "SEG BINARY", "dciodvfy", variant_id)
        assert c["symmetric_difference"] == expected, variant_id
    for variant_id, expected in SEG_RESIDUE_DICOM_VALIDATOR.items():
        c = _cell(cmp_rows, "SEG BINARY", "dicom-validator", variant_id)
        assert c["symmetric_difference"] == expected, variant_id


def test_direction_never_flips(cmp_rows):
    """Ledger B-04. The conclusion, pinned as a conclusion and not as prose.

    A flip is set equality or W2 becoming a strict subset of W1, on a cell whose
    baseline sets already differ.
    """
    text, flips = variants._flip_sentence(cmp_rows)
    assert flips == [], "a variant flipped the direction: %s" % [
        (c["sop_class"], c["validator"], c["variant"]) for c in flips]
    assert "No variant flips the direction of the finding." in text
    for variant_id in variants.LADDER:
        for validator in ("dciodvfy", "dicom-validator"):
            c = _cell(cmp_rows, "SEG BINARY", validator, variant_id)
            assert not c["equal"], variant_id
            assert not c["w2_subset_of_w1"], variant_id


def test_the_flip_test_can_detect_a_flip(cmp_rows):
    """A guard that cannot fail is not a guard.

    The flip test is the whole conclusion of this phase, so it is exercised
    against a fabricated cell that does flip, rather than trusted because the
    real data happens not to.
    """
    fake = dict(_cell(cmp_rows, "SEG BINARY", "dciodvfy", "V1"))
    fake.update(equal=True, w2_subset_of_w1=False, flip=True, jaccard=1.0)
    text, flips = variants._flip_sentence(
        [c for c in cmp_rows if c is not None and
         not (c["sop_class"] == "SEG BINARY" and c["validator"] == "dciodvfy"
              and c["variant"] == "V1")] + [fake])
    assert len(flips) == 1
    assert "At least one variant flips" in text


def test_sr_baseline_is_degenerate_for_the_flip_test(cmp_rows):
    """Ledger B-09. The SR cells are equal at baseline, so they cannot flip and
    they are not counted as evidence that nothing flipped."""
    for validator in ("dciodvfy", "dicom-validator"):
        c = _cell(cmp_rows, "TID 1500 SR", validator, "V0")
        assert c["equal"] and not c["testable"]
    text, _ = variants._flip_sentence(cmp_rows)
    assert "degenerate" in text


def test_round_trip_control_moves_nothing(rows):
    """Ledger B-07. Every variant object is a pydicom re-save. If re-saving
    alone moved a message class, every delta in the ladder would be confounded
    by it, and the ladder would be measuring pydicom."""
    from colophon import floor
    for writer, sop_class, _ in floor.OBJECTS:
        for validator in floor.VALIDATORS:
            emitted = variants.classes(rows, writer, sop_class, "V0", validator)
            resaved = variants.classes(rows, writer, sop_class, "V0R", validator)
            assert emitted == resaved, "%s %s %s" % (writer, sop_class, validator)


def test_not_applicable_cells_are_recorded(rows):
    """Ledger B-06. A skipped cell and a cell that does not apply read the same
    in a table only if the table lies."""
    na = {(r["sop_class"], r["variant"]) for r in rows
          if r["not_applicable"] == "True"}
    assert na == {("Parametric Map", "V2"), ("Parametric Map", "V4"),
                  ("TID 1500 SR", "V2"), ("TID 1500 SR", "V4")}
    for r in rows:
        if r["not_applicable"] == "True":
            assert r["not_applicable_reason"].strip()
            assert not r["message_class_id"]
    # And the cells that do apply must actually have been run.
    for sop_class in ("SEG BINARY", "SEG FRACTIONAL"):
        for variant_id in ("V2", "V4"):
            applies, _ = variants.applicability(variant_id, sop_class)
            assert applies


def test_every_class_and_variant_has_a_row(rows):
    """Coverage of the grid itself. A missing cell is the failure mode this
    whole file exists to prevent."""
    from colophon import floor
    grid = {(r["writer"], r["sop_class"], r["variant"], r["validator"])
            for r in rows}
    for writer, sop_class, _ in floor.OBJECTS:
        for variant_id, _, _, _ in variants.VARIANTS:
            for validator in floor.VALIDATORS:
                assert (writer, sop_class, variant_id, validator) in grid, (
                    "%s %s %s %s" % (writer, sop_class, variant_id, validator))


def test_single_writer_classes_carry_no_jaccard(cmp_rows):
    """Ledger B-08. SEG FRACTIONAL and Parametric Map are highdicom-only and
    must never appear in a between-writer comparison."""
    from colophon import floor
    assert set(floor.W2_EMISSION_GAPS) == {"SEG FRACTIONAL", "Parametric Map"}
    compared = {c["sop_class"] for c in cmp_rows}
    assert compared == set(variants.SHARED_CLASSES)
    assert not compared & set(floor.W2_EMISSION_GAPS)


def test_deflate_is_a_reader_failure_not_an_iod_finding(rows, cmp_rows):
    """Ledger B-05. V9 is the one rung where the two validators disagree about
    what they are even looking at, and the disagreement is recorded, not
    resolved. dciodvfy reports a dataset read failure. dicom-validator reports
    exactly what it reported at baseline."""
    from colophon import floor
    for writer in (floor.W1, floor.W2):
        text = " ".join(r["message_template"] for r in rows
                        if r["writer"] == writer and r["sop_class"] == "SEG BINARY"
                        and r["variant"] == "V9" and r["validator"] == "dciodvfy")
        assert "Dicom dataset read failed" in text, writer
    a = _cell(cmp_rows, "SEG BINARY", "dicom-validator", "V0")
    b = _cell(cmp_rows, "SEG BINARY", "dicom-validator", "V9")
    assert (a["w1"], a["w2"]) == (b["w1"], b["w2"])


def test_variants_are_applied_within_a_writer_only(rows):
    """The rule that would invalidate the whole ladder if broken: a variant file
    for one writer must have been built from that writer's own baseline."""
    for r in rows:
        if not r["object_file"] or r["variant"] == "V0":
            continue
        expected = "w1" if r["writer"] == "highdicom" else "w2"
        other = "w2" if expected == "w1" else "w1"
        path = r["object_file"].replace("\\", "/")
        assert "/variants/%s/" % expected in path, path
        assert "/variants/%s/" % other not in path, path


def test_the_nine_are_nine_and_the_control_is_not_one_of_them():
    """The ladder is nine rungs. The baseline and the round-trip control are
    labelled separately everywhere so neither is quoted as a perturbation."""
    assert len(variants.LADDER) == 9
    assert "V0" not in variants.LADDER and "V0R" not in variants.LADDER
    assert variants.LADDER == ["V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9"]


def test_proposed_ledger_rows_are_well_formed():
    """The pending rows are a proposal to the ledger, so they are validated
    against the ledger's own schema before anyone merges them."""
    if not PENDING.exists():
        pytest.skip("run python -m colophon.variants first")
        return
    entries = json.loads(PENDING.read_text(encoding="utf-8"))
    ids = [e["id"] for e in entries]
    assert ids == sorted(ids), "rows must be ordered by id"
    assert len(set(ids)) == len(ids)
    for e in entries:
        assert e["id"].startswith("B-")
        assert not set(e) - set(ledger.FIELDS)
        assert e["status"] in ledger.VALID_STATUS
        if e["status"] == "MEASURED":
            for field in ("command", "source_file", "dropped"):
                assert e.get(field, "").strip(), "%s missing %s" % (e["id"], field)
    # Track B never writes the ledger itself, so no row here may claim to be a
    # pre-registration row belonging to another track.
    assert not any(e["id"].startswith("PRE-") for e in entries)


def test_the_write_up_is_generated_and_states_the_conclusion():
    """The markdown is emitted by the module, never typed, and it has to carry
    the explicit statement the design asks for."""
    md = RESULTS / "phase1_variants.md"
    if not md.exists():
        pytest.skip("run python -m colophon.variants first")
        return
    text = md.read_text(encoding="utf-8")
    assert "flips the direction of the finding" in text
    assert "NOT_APPLICABLE" in text
    assert "non-transferable" in text or "highdicom-only" in text
    assert chr(0x2014) not in text
