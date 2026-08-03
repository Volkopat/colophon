"""Claim 3 tabulation: the rules that must not drift.

The tabulation turns on four things that are easy to get quietly wrong: grades
that do not partition, buckets that do not sum, a classification rule table that
silently moves an earlier phase's numbers, and a distribution reported by a
median when it is two point masses.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from colophon import claim3, provenance, standards, writers


# --- scope --------------------------------------------------------------------
def test_enhanced_sr_is_excluded_because_it_is_partial():
    assert claim3.PARTIAL_CLASS == "Enhanced SR Storage"
    source = Path(claim3.__file__).read_text(encoding="utf-8")
    assert "excluded from every rate" in source


def test_type1_bindings_come_from_the_verified_standards_row():
    """Only STD-04 can make an object non-conformant here, and it binds four
    attributes in two IODs. Widening either would be adjudicating."""
    assert claim3.TYPE1_CLASSES == {"Segmentation Storage", "Parametric Map Storage"}
    assert sorted(claim3.TYPE1_CARRIERS) == [
        "DeviceSerialNumber", "Manufacturer", "ManufacturerModelName",
        "SoftwareVersions"]
    assert claim3.TYPE1_CARRIERS == [d["keyword"]
                                     for d in standards.ENHANCED_GENERAL_EQUIPMENT]


def test_implementation_class_uid_is_captured_but_not_graded():
    assert "ImplementationClassUID" in claim3.CARRIERS
    assert "ImplementationClassUID" in claim3.NOT_GRADED
    assert "ImplementationClassUID" not in claim3.TYPE1_CARRIERS


# --- grading ------------------------------------------------------------------
def _row(**kw):
    base = {"sop_class_name": "Segmentation Storage", "ces_items": "[]",
            "segments": "[]", "Manufacturer": "", "ManufacturerModelName": "",
            "SeriesDescription": "", "ContentCreatorName": "",
            "DeviceSerialNumber": ""}
    for carrier in claim3.TYPE1_CARRIERS:
        base[carrier + "_state"] = "non_empty"
    base.update(kw)
    return pd.DataFrame([base])


def test_grades_are_exhaustive_and_mutually_exclusive():
    assert claim3.GRADES == ["non-conformant", "conformant but uninformative",
                             "informative"]
    frame = pd.concat([
        _row(DeviceSerialNumber_state="absent"),
        _row(Manufacturer="QIICR", ManufacturerModelName="https://github.com/QIICR/dcmqi"),
        _row(ManufacturerModelName="Sybil"),
    ], ignore_index=True)
    graded = claim3.grade_objects(frame)
    assert list(graded["grade"]) == ["non-conformant",
                                     "conformant but uninformative",
                                     "informative"]
    table = claim3.grade_table(graded, "sop_class_name")
    row = table.iloc[0]
    # The counts partition exactly. Only the displayed percentages round, so the
    # sum is checked against the rounding budget rather than against 100.0.
    assert sum(int(row[g]) for g in claim3.GRADES) == int(row["objects"])
    assert abs(float(row["sum_pct"]) - 100.0) <= 0.05


def test_a_type3_absence_is_never_a_defect():
    """SeriesDescription and ContentCreatorName are Type 3. Absent is a gap in
    the standard, not a violation."""
    frame = _row(SeriesDescription="", ContentCreatorName="",
                 Manufacturer="QIICR")
    graded = claim3.grade_objects(frame)
    assert graded.iloc[0]["grade"] == "conformant but uninformative"


def test_a_type1_absence_outside_the_two_bound_iods_is_not_a_defect():
    frame = _row(sop_class_name="RT Structure Set Storage",
                 DeviceSerialNumber_state="absent")
    graded = claim3.grade_objects(frame)
    assert graded.iloc[0]["grade"] != "non-conformant"


def test_encoders_viewers_vendors_and_institutions_are_not_producer_identity():
    """The rule that replaced a permissive token test which returned 96 percent
    informative by counting any non-generic word."""
    for value in ("QIICR", "highdicom", "OHIF-XNAT Viewer 3.2.0", "PixelMed",
                  "GE MEDICAL SYSTEMS", "SIEMENS", "Stony Brook University",
                  "converted by Imaging Data Commons"):
        named, _, _ = claim3.names_producer([value])
        assert not named, value


def test_a_named_model_is_producer_identity():
    for value in ("Sybil", "GBM360", "TotalSegmentator v1.5.6",
                  "3d_fullres-tta_nnU-Net"):
        named, _, _ = claim3.names_producer([value])
        assert named, value


# --- the additive rule table --------------------------------------------------
def test_the_phase0_rule_table_is_not_mutated():
    """Extending provenance.RULES in place would retroactively move the Phase 0
    C3 measurements. The additive table is separate and applied after it."""
    # Behavioural, not textual: the Phase 0 table must not have gained any of
    # the additive patterns, and the additive table must be a separate object.
    phase0 = {pattern for _, _, pattern in provenance.RULES}
    for _, _, pattern in claim3.CLAIM3_EXTRA_RULES:
        assert pattern not in phase0, pattern
    assert claim3.CLAIM3_EXTRA_RULES is not provenance.RULES
    category, rule, extra = claim3.classify_value("Sybil")
    assert (category, extra) == ("named_analysis", False)
    category, rule, extra = claim3.classify_value("TotalSegmentator v1.5.6")
    assert (category, extra) == ("named_analysis", True)


def test_declined_values_are_recorded_rather_than_implied():
    assert "Manual Segmentation" in claim3.DECLINED
    named, _, _ = claim3.names_producer(["Manual Segmentation"])
    assert not named


def test_writer_rule_table_is_imported_not_restated():
    source = Path(claim3.__file__).read_text(encoding="utf-8")
    assert "writers.WRITER_RULES" in source
    assert "WRITER_RULES: list" not in source


# --- three states never summed ------------------------------------------------
def test_three_states_never_summed():
    """No emitted column may carry absent plus zero-length."""
    frame = pd.concat([
        _row(DeviceSerialNumber_state="absent"),
        _row(DeviceSerialNumber_state="empty"),
        _row(DeviceSerialNumber_state="non_empty"),
    ], ignore_index=True)
    for name in claim3.CARRIERS:
        if name + "_state" not in frame:
            frame[name + "_state"] = "non_empty"
    frame["analysis_result_id"] = "a"
    by_class, _, _ = claim3.t31(frame)
    row = by_class[by_class.carrier == "DeviceSerialNumber"].iloc[0]
    assert int(row["absent"]) == 1
    assert int(row["zero_length"]) == 1
    assert int(row["non_empty"]) == 1
    # type1_violation is the count of the two states, and is a separate column
    # from either of them rather than a replacement for them.
    assert int(row["type1_violation"]) == 2
    assert "absent" in by_class.columns and "zero_length" in by_class.columns


# --- absence and incompleteness -----------------------------------------------
def test_absence_and_incompleteness_stay_apart():
    columns = pd.read_csv(
        Path("results/claim3/t34_algorithm_identification_by_writer.csv")
    ).columns if Path("results/claim3/t34_algorithm_identification_by_writer.csv").exists() else []
    if len(columns):
        assert "seg_absent" in columns
        assert "seg_present_incomplete" in columns
        assert not any("absent_and_incomplete" in c or "absent_or_incomplete" in c
                       for c in columns)


# --- the ladder ---------------------------------------------------------------
def test_ladder_levels_are_the_registered_five():
    assert [lv["level"] for lv in claim3.LADDER] == [1, 2, 3, 4, 5]
    assert claim3.LADDER[0]["name"] == "equipment attributes"
    assert claim3.LADDER[1]["name"] == "file meta"
    assert claim3.LADDER[4]["name"] == "collection metadata and DOI"
    # Level 5 is the only one not in the object, and that is the point of it.
    assert [lv["in_object"] for lv in claim3.LADDER] == [True, True, True, True, False]


def test_a_uid_a_serial_and_a_commit_hash_are_not_versions():
    """All three match a version regex and none is a version of an analysis."""
    assert not claim3.has_version(["1.2.276.0.7230010.3.0.3.6.6"])[0]
    assert not claim3.has_version(["32c5186e72339e60ba8252a68757c5b340294b8b"])[0]
    assert not claim3.has_version(["451bf84"])[0]
    assert not claim3.has_version(["highdicom0.27.0"])[0], "a sentinel version is the encoder's"
    assert claim3.has_version(["TotalSegmentator v1.5.6"])[0]


# --- two camps, never a median ------------------------------------------------
def test_two_camp_reports_boundaries_and_no_median():
    frame = pd.DataFrame({
        "collection_id": ["a", "a", "b", "b", "c", "c"],
        "flag": [True, True, False, False, True, False],
    })
    out = claim3.two_camp(frame, "collection_id", "flag")
    assert out["units"] == 3
    assert out["at_zero"] == 1
    assert out["at_hundred"] == 1
    assert out["between"] == 1
    assert out["between_units"][0]["unit"] == "c"
    assert "median" not in out and "iqr" not in out


def test_no_module_reports_a_median_or_an_iqr_for_these_distributions():
    for module in ("claim3.py", "claim3_report.py"):
        source = (Path("colophon") / module).read_text(encoding="utf-8")
        # Calls, not prose. The modules discuss why a median is wrong here and
        # that discussion is the point, so only an actual computation is banned.
        for banned in (".median(", ".quantile(", "np.median", ".describe("):
            assert banned not in source, (module, banned)


# --- buckets ------------------------------------------------------------------
def test_buckets_are_exhaustive():
    assert provenance.BUCKET_ORDER == ["encoder_only", "producer_and_converter",
                                       "other", "absent"]
    frame = pd.concat([
        _row(Manufacturer="QIICR", ManufacturerModelName="https://github.com/QIICR/dcmqi"),
        _row(Manufacturer="Stony Brook University converted by IDC",
             ManufacturerModelName="TIL model"),
        _row(Manufacturer="SIEMENS", ManufacturerModelName="Biograph"),
        _row(Manufacturer="", ManufacturerModelName="NA"),
    ], ignore_index=True)
    frame["analysis_result_id"] = "a"
    frame["collection_id"] = ["c1", "c1", "c2", "c2"]
    by_class, _, ways = claim3.t32(frame)
    assert float(by_class.iloc[0]["sum_pct"]) == 100.0
    assert ways["objects"] == 4


# --- corroboration ------------------------------------------------------------
def test_type1_violations_are_corroborated():
    """The conformance call belongs to the validators, not to this module."""
    path = Path("results/claim3/t31_type1_validator_corroboration.csv")
    if not path.exists():
        pytest.skip("tabulation has not been run")
    table = pd.read_csv(path)
    if table.empty:
        pytest.skip("no Type 1 violations to corroborate")
    assert set(table["validator"]) == {"dciodvfy", "dicom-validator"}
    missed = table[~table["validator_raised_a_matching_message"].astype(bool)]
    assert missed.empty, (
        "a state recorded as a Type 1 violation that no validator flagged would "
        "mean this module is adjudicating: %s" % missed.to_dict("records"))


def test_claim3_md_is_generated_and_not_typed():
    """The same rule the results write-ups live under: a number cannot drift out
    of agreement with its table, because the sentence containing it is emitted by
    the module that computed it."""
    from colophon import claim3_report
    source = Path(claim3_report.__file__).read_text(encoding="utf-8")
    assert 'REPO / "CLAIM3.md"' in source
    path = Path("CLAIM3.md")
    if path.exists():
        text = path.read_text(encoding="utf-8")
        assert "Reproduce with" in text
        assert "\u2014" not in text, "no em-dashes in project prose"


# Root-level generated write-ups. They sit outside the results/*.md glob that
# tests/test_style.py covers, so the same rule is enforced for them here.
ROOT_GENERATED = {
    "CLAIM3.md": "colophon/claim3_report.py",
    "TYPECHECK.md": "colophon/typecheck.py",
    "DEVIATIONS.md": "colophon/deviations.py",
    "ADJUDICATION2.md": "colophon/adjudicate2_report.py",
}


def test_root_write_ups_are_generated_and_house_style_holds():
    for name, module in ROOT_GENERATED.items():
        source = Path("colophon") / Path(module).name
        assert source.exists(), module
        assert name in source.read_text(encoding="utf-8"), (
            "%s does not write %s" % (module, name))
        path = Path(name)
        if path.exists():
            text = path.read_text(encoding="utf-8")
            assert chr(8212) not in text, "no em-dashes in %s" % name
            assert "Reproduce with" in text, "%s must name its command" % name
