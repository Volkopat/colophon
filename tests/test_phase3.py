"""Phase 3: the rules that must not drift, pinned.

The question this phase answers turns on keeping two things apart that a careless
aggregation would add together, and on descending into two nested sequences that
a flat tag scan cannot reach. Both are asserted here rather than trusted.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

import pandas as pd
import pytest

from colophon import floor, phase3, phase3_report, sample, standards

pydicom = pytest.importorskip("pydicom")
from pydicom.dataset import Dataset  # noqa: E402


# --- the tags -----------------------------------------------------------------
def test_macro_tags_come_from_standards_and_carry_the_corrections():
    """The brief gave two tags wrongly. A scan on its tags scores AlgorithmSource
    absent everywhere, which is a null result manufactured by a typo."""
    assert phase3.MACRO["AlgorithmParameters"]["tag"] == "(0066,0032)"
    assert phase3.MACRO["AlgorithmSource"]["tag"] == "(0024,0202)"
    assert phase3._tag("(0066,0032)") == (0x0066, 0x0032)
    assert phase3._tag("(0024,0202)") == (0x0024, 0x0202)
    # The withdrawn tags must not come back.
    assert "(0066,0033)" not in {d["tag"] for d in
                                 standards.ALGORITHM_IDENTIFICATION_MACRO}


def test_the_three_type1_children_are_exactly_these():
    assert sorted(phase3.MACRO_TYPE1) == ["AlgorithmFamilyCodeSequence",
                                          "AlgorithmName", "AlgorithmVersion"]


def test_segment_attribute_tags():
    assert phase3.SEGMENT_ALGORITHM_TYPE == (0x0062, 0x0008)
    assert phase3.SEGMENT_ALGORITHM_NAME == (0x0062, 0x0009)
    assert phase3.ALGORITHM_IDENTIFICATION == (0x0062, 0x0007)
    assert phase3.SEGMENT_SEQUENCE == (0x0062, 0x0002)


# --- three states, never two --------------------------------------------------
def _element(tag, vr, value):
    ds = Dataset()
    ds.add_new(tag, vr, value)
    return ds.get(tag)


def test_state_separates_absent_from_zero_length():
    assert phase3.state_of(None) == "absent"
    assert phase3.state_of(_element((0x0018, 0x1020), "LO", "")) == "empty"
    assert phase3.state_of(_element((0x0018, 0x1020), "LO", "1.2.3")) == "non_empty"


def test_state_separates_absent_sequence_from_zero_item_sequence():
    assert phase3.state_of(_element((0x0062, 0x0007), "SQ", [])) == "empty"
    assert phase3.state_of(_element((0x0062, 0x0007), "SQ", [Dataset()])) == "non_empty"


# --- the descent --------------------------------------------------------------
def _segment(algorithm_type="AUTOMATIC", name="seg", macro=None,
             include_sequence=True, items=1):
    item = Dataset()
    item.SegmentNumber = 1
    item.SegmentLabel = "label"
    item.SegmentAlgorithmType = algorithm_type
    if name is not None:
        item.SegmentAlgorithmName = name
    if include_sequence:
        item.SegmentationAlgorithmIdentificationSequence = [
            macro if macro is not None else _complete_macro()
            for _ in range(items)]
    return item


def _complete_macro():
    macro = Dataset()
    family = Dataset()
    family.CodeValue = "123456"
    family.CodingSchemeDesignator = "DCM"
    family.CodeMeaning = "Artificial Intelligence"
    macro.AlgorithmFamilyCodeSequence = [family]
    macro.AlgorithmName = "TotalSegmentator"
    macro.AlgorithmVersion = "2.0.5"
    return macro


def test_absent_sequence_reads_as_absent_and_lists_no_missing_children():
    rec = phase3.read_segment(_segment(include_sequence=False))
    assert rec["identification"] == "absent"
    assert rec["missing_type1"] == []
    assert rec["non_manual"] is True


def test_complete_sequence_reads_as_complete():
    rec = phase3.read_segment(_segment())
    assert rec["identification"] == "present_complete"
    assert rec["missing_type1"] == []


def test_sequence_missing_a_type1_child_reads_as_incomplete():
    macro = _complete_macro()
    del macro.AlgorithmVersion
    rec = phase3.read_segment(_segment(macro=macro))
    assert rec["identification"] == "present_incomplete"
    assert rec["missing_type1"] == ["AlgorithmVersion"]


def test_zero_length_type1_child_is_incomplete_not_complete():
    """Type 1 present and empty is a violation, not a pass."""
    macro = _complete_macro()
    macro.AlgorithmName = ""
    rec = phase3.read_segment(_segment(macro=macro))
    assert rec["identification"] == "present_incomplete"
    assert "AlgorithmName" in rec["missing_type1"]


def test_zero_item_sequence_is_its_own_state():
    item = _segment(include_sequence=False)
    item.SegmentationAlgorithmIdentificationSequence = []
    rec = phase3.read_segment(item)
    assert rec["identification"] == "present_zero_items"
    assert rec["identification"] not in ("absent", "present_incomplete")


def test_manual_segments_are_not_counted_as_non_manual():
    assert phase3.read_segment(_segment("MANUAL", include_sequence=False))["non_manual"] is False
    assert phase3.read_segment(_segment("SEMIAUTOMATIC", include_sequence=False))["non_manual"] is True


def test_algorithm_name_type1c_state_is_captured():
    item = _segment(name=None, include_sequence=False)
    assert phase3.read_segment(item)["SegmentAlgorithmName_state"] == "absent"
    item = _segment(name="", include_sequence=False)
    assert phase3.read_segment(item)["SegmentAlgorithmName_state"] == "empty"


# --- absence and incompleteness are never merged ------------------------------
def test_object_rollup_keeps_absence_and_incompleteness_apart():
    macro = _complete_macro()
    del macro.AlgorithmName
    segments = [phase3.read_segment(_segment(include_sequence=False)),
                phase3.read_segment(_segment(macro=macro)),
                phase3.read_segment(_segment()),
                phase3.read_segment(_segment("MANUAL", include_sequence=False))]
    out = phase3.summarise_segments(segments)
    assert out["n_segments"] == 4
    assert out["n_non_manual"] == 3
    assert out["segments_ident_absent"] == 1
    assert out["segments_ident_present_incomplete"] == 1
    assert out["segments_ident_present_complete"] == 1
    assert out["any_ident_absent"] is True
    assert out["all_ident_absent"] is False
    assert out["any_ident_incomplete"] is True
    assert out["missing_type1_children"] == {"AlgorithmName": 1}


def test_no_emitted_column_sums_absence_and_incompleteness():
    """The one aggregation error this phase must not make."""
    objects = pd.DataFrame([
        {"stratum": "s", "analysis_result_id": "a", "n_segments": 3,
         "n_non_manual": 3, "has_non_manual": True,
         "segments_ident_absent": 2, "segments_ident_present_zero_items": 0,
         "segments_ident_present_incomplete": 1,
         "segments_ident_present_complete": 0,
         "segments_algorithm_name_absent": 0, "segments_algorithm_name_empty": 0,
         "any_ident_absent": True, "all_ident_absent": False,
         "any_ident_incomplete": True, "all_ident_incomplete": False,
         "any_ident_present_zero_items": False, "any_ident_complete": False},
    ])
    series = pd.DataFrame([{"stratum": "s", "analysis_result_id": "a",
                            "status": "OK", "series_instance_uid": "u"}] * 40)
    table = phase3_report.segment_level(objects, series, "stratum")
    row = table.iloc[0]
    assert row["segments_ident_absent"] == 2
    assert row["segments_ident_present_incomplete"] == 1
    merged = row["segments_ident_absent"] + row["segments_ident_present_incomplete"]
    for column in table.columns:
        value = table.iloc[0][column]
        if isinstance(value, (int, float)) and value == merged and merged != 0:
            assert column not in ("segments_ident_absent",
                                  "segments_ident_present_incomplete")
            # No column may carry the merged quantity under any name.
            assert not str(column).startswith("segments_ident_"), column


# --- the reporting rule PRE-06 registered -------------------------------------
def test_reporting_rule_thresholds():
    assert phase3_report.reporting_rule(29) == "counts only, no rate"
    assert "below-registered-n" in phase3_report.reporting_rule(30)
    assert "below-registered-n" in phase3_report.reporting_rule(383)
    assert phase3_report.reporting_rule(384) == "rate with Wilson interval"


def test_a_cell_under_thirty_series_reports_no_rate():
    assert phase3_report.rate(5, 10, n_series=29)["pct"] is None
    assert phase3_report.rate(5, 10, n_series=30)["pct"] == 50.0


# --- the frame did not move when the fence came down --------------------------
def test_frame_constants_are_unchanged():
    assert sample.EXECUTE is True
    assert sample.SEED == 20260802
    assert sample.REGISTERED_N == 384
    assert sample.MIN_RATE_N == 30
    assert sample.BUDGET_GB == 150.0
    assert sample.TARGET_P == 0.05


# --- never gate on exit status ------------------------------------------------
def test_return_code_is_recorded_but_never_branched_on():
    """dciodvfy returns rc=0 on a Segmentation with SegmentSequence and Rows
    deleted, so any branch on it is a wrong answer waiting to happen."""
    tree = ast.parse(Path(phase3.__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, (ast.If, ast.While, ast.Assert)):
            continue
        for child in ast.walk(node.test):
            if isinstance(child, ast.Name) and "returncode" in child.id:
                raise AssertionError("phase3 branches on a return code")
            if isinstance(child, ast.Attribute) and "returncode" in child.attr:
                raise AssertionError("phase3 branches on a return code")
            if isinstance(child, ast.Constant) and child.value == "returncode":
                raise AssertionError("phase3 branches on a return code")


def test_severity_matches_both_documented_forms():
    """The line-start form is dciodvfy's common one and the embedded form is the
    private-tag one. Matching only one of them silently drops findings."""
    assert floor.SEVERITY.search("Error - Missing attribute Type 1 Element=<Rows>")
    assert floor.SEVERITY.search(
        "(0x0099,0x1001)  ?  - Warning - Unrecognized tag in private block")


# --- the panel is not overstated ----------------------------------------------
def test_dcmpschk_is_not_used_on_segmentation():
    """On a Segmentation missing two Type 1 attributes dcmpschk printed
    'Test passed.', so including it would manufacture a zero percent rate."""
    source = Path(phase3.__file__).read_text(encoding="utf-8")
    assert "run_dcmpschk" not in source
    from colophon import validate
    assert "dcmpschk" not in validate.PANEL[phase3.SOP_CLASS]["conformance"]


def test_carrier_list_is_the_one_the_question_named():
    names = [n for n, _, _ in phase3.CARRIERS]
    for required in ("Manufacturer", "ManufacturerModelName", "DeviceSerialNumber",
                     "SoftwareVersions", "ImplementationVersionName",
                     "ImplementationClassUID", "ContentCreatorName",
                     "SeriesDescription"):
        assert required in names, required
    assert phase3.CONTRIBUTING_EQUIPMENT == (0x0018, 0xA001)
    assert phase3.PURPOSE_OF_REFERENCE == (0x0040, 0xA170)


def test_disk_floor_is_twenty_gb():
    assert phase3.MIN_FREE_GB == 20.0


def test_a_validator_failure_does_not_cost_the_capture():
    """The segment capture is the answer to the question. A tool that dies on a
    large object must not take the object's record with it."""
    source = Path(phase3.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = next(n for n in ast.walk(tree)
                    if isinstance(n, ast.FunctionDef) and n.name == "validate_object")
    handlers = [n for n in ast.walk(function) if isinstance(n, ast.Try)]
    assert len(handlers) >= 2, "each validator must be wrapped separately"
    assert "TOOL_ERROR" in source


def test_dciodvfy_uses_the_phase_one_parser_and_normaliser():
    """message_class_id must stay comparable across phases, so the parser and
    the normaliser are Phase 1's even though the timeout is not."""
    source = Path(phase3.__file__).read_text(encoding="utf-8")
    assert "floor.parse_dciodvfy" in source
    assert "floor.normalise" in source
    assert "floor.message_class_id" in source
    assert phase3.DCIODVFY_TIMEOUT > 300


def test_writer_relabel_reuses_the_phase0_rule_table():
    """A new rule invented here would silently move the W-01 census. Only the
    evidence widens: the table itself is imported unchanged."""
    from colophon import writers
    source = Path(phase3_report.__file__).read_text(encoding="utf-8")
    assert "writers.WRITER_RULES" in source
    assert "WRITER_RULES: list" not in source, "the rule table must not be restated"

    class Row:
        ContributingEquipmentSequence_items = json.dumps(
            [{"Manufacturer": "Highdicom open-source contributors",
              "ManufacturerModelName": "highdicom"}])
        ImplementationVersionName = "highdicom0.27.0"
        Manufacturer = "Stony Brook University converted by Imaging Data Commons"
        ManufacturerModelName = "TIL Inception-V4 2022"

    name, carrier = phase3_report.writer_from_object(Row())
    assert name == "highdicom"
    assert carrier == phase3_report.WRITER_CARRIERS[0]

    class Unknown:
        ContributingEquipmentSequence_items = "[]"
        ImplementationVersionName = "dcm4che-1.4.35"
        Manufacturer = "SIEMENS"
        ManufacturerModelName = "Sonata"

    name, carrier = phase3_report.writer_from_object(Unknown())
    assert name == writers.UNKNOWN_WRITER, (
        "a value the Phase 0 table has no rule for must stay unidentified")


def test_out_of_enumeration_values_are_excluded_and_counted_not_dropped():
    """SegmentAlgorithmType has Enumerated Values, not Defined Terms. A fourth
    value is outside the question's denominator, so it has to be reported
    somewhere or it has been silently dropped."""
    assert phase3_report.ENUMERATED == ("AUTOMATIC", "SEMIAUTOMATIC", "MANUAL")
    rec = phase3.read_segment(_segment("SEMIAUTOMATED", include_sequence=False))
    assert rec["non_manual"] is False, (
        "a value outside the enumeration must not enter the "
        "AUTOMATIC-or-SEMIAUTOMATIC denominator")
    assert rec["SegmentAlgorithmType"] == "SEMIAUTOMATED"
    summary = phase3.summarise_segments([rec])
    assert summary["n_segments"] == 1
    assert summary["n_non_manual"] == 0
    # It is still visible in the type distribution, which is what stops it
    # vanishing from the record entirely.
    assert summary["algorithm_types"] == {"SEMIAUTOMATED": 1}


def test_type_and_name_disagreement_is_observed_not_scored():
    """A segment declaring AUTOMATIC whose macro names a manual procedure is
    conformant. PS3.3 states no relation between the two attributes."""
    macro = pd.DataFrame([
        {"stratum": "s", "analysis_result_id": "a",
         "SegmentAlgorithmType": "AUTOMATIC", "AlgorithmName": "Manual Segmentation",
         "AlgorithmVersion": "1.0", "AlgorithmFamilyCode": "113076,DCM,Segmentation",
         "AlgorithmSource": "", "segments": 7},
        {"stratum": "s", "analysis_result_id": "a",
         "SegmentAlgorithmType": "AUTOMATIC", "AlgorithmName": "nnUNet",
         "AlgorithmVersion": "2.0", "AlgorithmFamilyCode": "123110,DCM,Artificial Intelligence",
         "AlgorithmSource": "", "segments": 3},
    ])
    hit = int(macro[
        macro["SegmentAlgorithmType"].str.upper().isin(phase3.NON_MANUAL)
        & macro["AlgorithmName"].str.lower().str.contains("manual", na=False)
    ]["segments"].sum())
    assert hit == 7
    # It is never counted as incompleteness: both rows are complete macros.
    assert "present_incomplete" not in set(macro.columns)
