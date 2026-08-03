"""Track C: Comprehensive 3D SR Storage, and its adjudication.

The triples are pinned because a triple that drifts is a triple nobody notices
drifting. If the census is re-run and these change, this fails and the ledger
rows that quote them have to be rewritten rather than quietly re-derived.

The rubric guards are the other half. A rule that reaches NET without a section
and a table, or an UNDECIDABLE rule that quietly acquires a verdict, is the
failure mode this project is most exposed to, so both are asserted here rather
than trusted to review.
"""
from __future__ import annotations

import json

import pytest

from colophon import adjudicate_c3dsr as A
from colophon import ledger as L

pytestmark = pytest.mark.skipif(
    not A.RECORDS.exists() or not A.CLASSES_CSV.exists(),
    reason="the Phase 2 census records are not present")

VERDICTS = {"FLOOR", "NET", "NOT-IOD", "PLAUSIBILITY", "UNDECIDABLE"}


@pytest.fixture(scope="module")
def rep():
    return A.build()


# --- coverage -----------------------------------------------------------------
def test_every_message_class_is_adjudicated(rep):
    """None skipped. The census CSV and the records file are both checked,
    because a class can appear in one and not the other if the census appended
    while the CSV was being written."""
    assert rep["per_class"], "no message class was read for this SOP class"
    for key, entry in rep["per_class"].items():
        assert entry["rule"]["adjudication"] in VERDICTS, key
    tabled = set(rep["per_class"])
    seen = {k for o in rep["objects"] for k in o["classes"]}
    assert not seen - tabled, (
        "a message class in the records was never adjudicated: %s"
        % sorted(seen - tabled)[:5])


def test_no_message_class_falls_through_the_rules(rep):
    """UNDECIDABLE is allowed as a verdict and forbidden as an accident."""
    unmatched = [k for k, v in rep["per_class"].items()
                 if v["rule"]["name"] == "UNMATCHED"]
    assert not unmatched, (
        "%d message classes matched no rule: %s"
        % (len(unmatched), unmatched[:5]))


def test_the_census_is_complete_and_nothing_was_dropped(rep):
    assert rep["n_objects"] == 5408
    assert rep["n_series"] == 5408
    assert dict(rep["statuses"]) == {"OK": 5408}
    assert rep["lines_skipped"] == 0


# --- the rubric ---------------------------------------------------------------
def test_no_net_without_a_section_and_a_table():
    for rule in A.RULES:
        if rule["adjudication"] != "NET":
            continue
        assert "Section" in rule["section"], rule["name"]
        assert "Table" in rule["table"], rule["name"]
        assert rule["quote"].strip(), rule["name"]
        assert rule["rationale"].strip(), rule["name"]


def test_floor_carries_a_citation_that_permits_the_construct():
    for rule in A.RULES:
        if rule["adjudication"] != "FLOOR":
            continue
        assert rule["quote"].strip(), rule["name"]
        assert "Table" in rule["table"], rule["name"]


def test_only_the_five_categories_exist():
    for rule in A.RULES + [A.UNMATCHED]:
        assert rule["adjudication"] in VERDICTS, rule["name"]


def test_rule_names_are_unique():
    names = [r["name"] for r in A.RULES]
    assert len(names) == len(set(names))


def test_the_sensitivity_sets_name_real_rules():
    names = {r["name"] for r in A.RULES}
    assert A.OFF_PART_RULES <= names
    assert A.MODULE_PRESENCE_RULES <= names
    for name in A.OFF_PART_RULES | A.MODULE_PRESENCE_RULES:
        rule = next(r for r in A.RULES if r["name"] == name)
        assert rule["adjudication"] == "NET", (
            "%s is demoted in the sensitivity table but is not NET" % name)


def test_classify_is_deterministic_and_first_match_wins():
    rule = A.classify(
        "dciodvfy",
        "Error - Missing attribute Type 2 Required "
        "Element=<ClinicalTrialSiteName> Module=<ClinicalTrialSubject>")
    assert rule["name"] == "CT_SUBJECT_TYPE2"
    assert A.classify("dciodvfy", "Error - something nobody has seen"
                      )["name"] == "UNMATCHED"
    # A dciodvfy template must not be matched by a dicom-validator rule.
    assert A.classify(
        "dicom-validator",
        "Error - Missing attribute Type 2 Required "
        "Element=<ClinicalTrialSiteName> Module=<ClinicalTrialSubject>"
    )["name"] == "UNMATCHED"


def test_the_undecidable_rule_is_a_verdict_not_a_gap():
    """PROC_CODE_SEQ_VM is UNDECIDABLE on purpose, and the reasoning is
    recorded. A future edit that hands it a verdict has to change this test."""
    rule = next(r for r in A.RULES if r["name"] == "PROC_CODE_SEQ_VM")
    assert rule["adjudication"] == "UNDECIDABLE"
    assert "Value Multiplicity" in rule["rationale"]


# --- the numbers --------------------------------------------------------------
def test_the_triples_are_pinned(rep):
    tri = rep["triples"]["as_adjudicated"]
    got = {(v, s): (t["gross"], t["floor"], t["net"], t["other"])
           for v in rep["validators"]
           for s, t in ((s, tri[v][s]["overall"]) for s in ("ERROR", "WARNING"))}
    assert got == {
        ("dciodvfy", "ERROR"): (1801, 0, 1801, 0),
        ("dciodvfy", "WARNING"): (5408, 5408, 0, 0),
        ("dicom-validator", "ERROR"): (1892, 91, 1801, 0),
        ("dicom-validator", "WARNING"): (0, 0, 0, 0),
    }


def test_the_verdict_counts_are_pinned(rep):
    assert dict(rep["verdict_counts"]) == {
        "PLAUSIBILITY": 1209, "NET": 11, "NOT-IOD": 2, "FLOOR": 1,
        "UNDECIDABLE": 1}
    assert len(rep["per_class"]) == 1224


def test_the_net_findings_partition_the_union(rep):
    """Measured, not asserted. If the three findings ever overlap, the sum in
    the write-up stops being the union and the sentence has to change."""
    f = rep["facts"]
    assert f["three_findings_disjoint"]
    assert f["three_findings_sum"] == rep["unions"]["as_adjudicated"]["net"]
    assert f["site_id_within_site_name"]
    assert f["proc_within_deident"]
    assert f["net_sets_identical"]
    assert (f["site_name"], f["site_id"], f["deident"], f["refuid"],
            f["proc"], f["ethnic"]) == (935, 8, 828, 38, 2, 129)


def test_pre05_inputs_are_pinned(rep):
    base = rep["unions"]["as_adjudicated"]
    assert (base["net"], base["pct_net"]) == (1801, 33.30)
    assert base["median_collection"] == 3.48
    assert {c: (d["objects"], d["net"], d["pct_net"])
            for c, d in base["per_collection"].items()} == {
        "lung_pet_ct_dx": (1091, 38, 3.48),
        "nlst": (3048, 935, 30.68),
        "nsclc_radiomics": (828, 828, 100.0),
        "prostatex": (345, 0, 0.0),
        "rms_mutation_prediction": (96, 0, 0.0),
    }


def test_pre05_verdict_is_the_conjunction(rep):
    base = rep["unions"]["as_adjudicated"]
    assert base["pct_net"] > 5.0, "the class-level limb clears"
    assert base["median_collection"] <= 5.0, "the collection-level limb does not"
    assert not (base["pct_net"] > 5.0 and base["median_collection"] > 5.0)


def test_no_demotion_changes_the_pre05_verdict(rep):
    for key, _demote, _label in A.SENSITIVITY:
        u = rep["unions"][key]
        assert not (u["pct_net"] > 5.0 and u["median_collection"] > 5.0), key


def test_the_two_groupings_are_not_nested(rep):
    """One collection carries two analysis results and one analysis result
    spans two collections, which is why the write-up publishes both tables."""
    base = rep["unions"]["as_adjudicated"]
    assert len(base["per_arid"]["nnu_net_bpr_annotations"]["collections"]) == 2
    assert len(base["per_collection"]["nlst"]["arids"]) == 2


# --- outputs ------------------------------------------------------------------
def test_the_ledger_rows_are_well_formed(rep):
    entries = A.ledger_entries(rep)
    ids = [e["id"] for e in entries]
    assert len(ids) == len(set(ids))
    assert all(i.startswith("C-C3D-") for i in ids), ids
    allowed = set(L.FIELDS) | {"fields_changed"}
    for e in entries:
        assert not set(e) - allowed, e["id"]
        assert e["status"] in L.VALID_STATUS, e["id"]
        if e["status"] in ("MEASURED", "DERIVED"):
            for field in ("command", "source_file", "dropped", "floor"):
                assert e.get(field), "%s has no %s" % (e["id"], field)


def test_no_pre_row_is_proposed(rep):
    """Two tracks already collided on PRE-05 and the orchestrator reconciled it
    by hand. PRE-01 is retired. This track proposes neither."""
    ids = {e["id"] for e in A.ledger_entries(rep)}
    assert "PRE-05" not in ids
    assert "PRE-01" not in ids


def test_the_pre05_row_carries_the_fold_in_sentence(rep):
    entries = {e["id"]: e for e in A.ledger_entries(rep)}
    row = entries["C-C3D-12"]
    assert "PRE-05" in row["derived_from"]
    assert row["notes"].startswith("Exact sentence to fold into PRE-05:")
    assert "Comprehensive 3D SR" in row["notes"]
    assert "33.30 percent" in row["notes"]
    assert "3.48 percent" in row["notes"]


def test_the_written_ledger_file_matches(rep):
    if not A.OUT_LEDGER.exists():
        pytest.skip("the pending ledger file has not been written yet")
    data = json.loads(A.OUT_LEDGER.read_text(encoding="utf-8"))
    assert data["sop_class"] == A.SOP_CLASS
    assert data["generated_by"] == A.CMD
    assert [r["id"] for r in data["rows"]] == [
        e["id"] for e in A.ledger_entries(rep)]


def test_the_write_ups_exist_and_carry_the_headline(rep):
    if not A.OUT_MD.exists() or not A.OUT_CSV.exists():
        pytest.skip("the write-ups have not been generated yet")
    md = A.OUT_MD.read_text(encoding="utf-8")
    assert "33.30 percent" in md
    assert "3.48 percent" in md
    assert "not substantial" in md
    assert chr(0x2014) not in md, "em-dash in a generated write-up"
    csv_text = A.OUT_CSV.read_text(encoding="utf-8")
    for name in {r["name"] for r in A.RULES}:
        assert name in csv_text, "%s appears in no CSV row" % name
