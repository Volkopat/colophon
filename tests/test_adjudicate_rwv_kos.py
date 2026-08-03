"""Track C: the two smallest complete classes, and their adjudication.

The numbers are pinned because a triple that drifts is a triple nobody notices
drifting. If the census is re-run and these change, this fails and the ledger
rows that quote them have to be rewritten rather than quietly re-derived.
"""
from __future__ import annotations

import pytest

from colophon import adjudicate_rwv_kos as A

pytestmark = pytest.mark.skipif(
    not A.RECORDS.exists() or not A.MESSAGE_CLASSES.exists(),
    reason="the Phase 2 census records are not present")


@pytest.fixture(scope="module")
def state():
    classes = A.read_message_classes()
    objects = A.read_records()
    return classes, objects


def test_every_message_class_is_adjudicated(state):
    classes, objects = state
    tabled = set()
    for r in classes:
        rule = A.classify(r["message_template"])  # raises unless exactly one rule
        assert rule["adjudication"] in {
            "FLOOR", "NET", "NOT-IOD", "PLAUSIBILITY", "UNDECIDABLE"}
        tabled.add((r["sop_class_name"], r["validator"], r["message_class_id"]))
    seen = {(o["sop_class_name"], m[0], m[1]) for o in objects for m in o["messages"]}
    assert not seen - tabled, "a message class in the records was never adjudicated"


def test_no_net_without_a_section_and_a_table(state):
    for rule in A.RULES:
        assert rule["citation_quote"].strip(), rule["name"]
        if rule["adjudication"] == "NET":
            assert "Section" in rule["citation_section"], rule["name"]
            assert "Table" in rule["citation_table"], rule["name"]
        if rule["adjudication"] == "UNDECIDABLE":
            pytest.fail("%s is UNDECIDABLE and must not carry a citation" % rule["name"])


def test_the_triples_are_pinned(state):
    _, objects = state
    tri = A.triples(objects)
    expected = {
        (A.RWV, "dciodvfy", "Error"): (20, 20, 20, 0),
        (A.RWV, "dciodvfy", "Warning"): (20, 20, 20, 0),
        (A.RWV, "dicom-validator", "Error"): (20, 0, 0, 0),
        (A.RWV, "dicom-validator", "Warning"): (20, 0, 0, 0),
        (A.KOS, "dciodvfy", "Error"): (40, 40, 0, 40),
        (A.KOS, "dciodvfy", "Warning"): (40, 40, 40, 0),
        (A.KOS, "dicom-validator", "Error"): (40, 40, 0, 40),
        (A.KOS, "dicom-validator", "Warning"): (40, 0, 0, 0),
    }
    got = {k: (v["objects"], v["gross"], v["floor"], v["net"]) for k, v in tri.items()}
    assert got == expected


def test_pre05_inputs_are_pinned(state):
    _, objects = state
    assert A.net_objects_any_validator(objects, A.RWV) == (0, 20)
    assert A.net_objects_any_validator(objects, A.KOS) == (40, 40)
    assert A.by_collection(objects, A.RWV) == [
        ("ct_vs_pet_ventilation_imaging", 0, 20, 0.0)]
    assert A.by_collection(objects, A.KOS) == [
        ("qin_breast_dce_mri", 40, 40, 100.0)]
