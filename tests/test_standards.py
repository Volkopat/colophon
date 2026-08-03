"""Pin the standard-level facts, so a wrong tag cannot return.

Two tags in the study brief were wrong. An extractor built on them would have
scored AlgorithmSource as absent on every object in the archive, and the error
would have looked like a finding.
"""
from __future__ import annotations

from colophon import standards, validate


def test_macro_tags():
    """Ledger STD-01."""
    by_keyword = {a["keyword"]: a for a in standards.ALGORITHM_IDENTIFICATION_MACRO}
    assert by_keyword["AlgorithmParameters"]["tag"] == "(0066,0032)"
    assert by_keyword["AlgorithmSource"]["tag"] == "(0024,0202)"
    assert by_keyword["AlgorithmFamilyCodeSequence"]["type"] == "1"
    assert by_keyword["AlgorithmName"]["type"] == "1"
    assert by_keyword["AlgorithmVersion"]["type"] == "1"
    assert len(standards.ALGORITHM_IDENTIFICATION_MACRO) == 6


def test_withdrawn_tags_cannot_return():
    assert "(0066,0033)" in standards.WITHDRAWN_TAGS
    used = {a["tag"] for a in standards.ALGORITHM_IDENTIFICATION_MACRO}
    assert "(0066,0033)" not in used


def test_segmentation_hypothesis_is_dead():
    """Ledger STD-02. The attractive hypothesis is false and stays recorded."""
    seg_iod = [a for a in standards.SEGMENT_ATTRIBUTES
               if a["keyword"] == "SegmentationAlgorithmIdentificationSequence"
               and "Height Map" not in a["location"]]
    assert len(seg_iod) == 1
    assert seg_iod[0]["type"] == "3"
    assert seg_iod[0]["condition"] is None, (
        "if this ever gains a condition the retired hypothesis is back in play")
    height_map = [a for a in standards.SEGMENT_ATTRIBUTES
                  if "Height Map" in a["location"]]
    assert len(height_map) == 1
    assert height_map[0]["type"] == "1C"
    assert "not part of the segmentation iod" in height_map[0]["note"].lower()


def test_surviving_hooks():
    """Ledger STD-03. Absence is conformant, incompleteness is not."""
    name = [a for a in standards.SEGMENT_ATTRIBUTES
            if a["keyword"] == "SegmentAlgorithmName"][0]
    assert name["type"] == "1C"
    assert "not MANUAL" in name["condition"]
    type1_children = [a["keyword"] for a in standards.ALGORITHM_IDENTIFICATION_MACRO
                      if a["type"] == "1"]
    assert set(type1_children) == {"AlgorithmFamilyCodeSequence", "AlgorithmName",
                                   "AlgorithmVersion"}


def test_enhanced_general_equipment():
    """Ledger STD-04. The primary yardstick for claim 3."""
    assert len(standards.ENHANCED_GENERAL_EQUIPMENT) == 4
    assert all(a["type"] == "1" for a in standards.ENHANCED_GENERAL_EQUIPMENT)
    keywords = {a["keyword"] for a in standards.ENHANCED_GENERAL_EQUIPMENT}
    assert keywords == {"Manufacturer", "ManufacturerModelName",
                        "DeviceSerialNumber", "SoftwareVersions"}
    assert standards.ENHANCED_GENERAL_EQUIPMENT_IODS == [
        "Segmentation Storage", "Parametric Map Storage"]


def test_three_grades_not_two():
    """Ledger STD-05. Two grades would score a gap in the standard as a failure
    by a producer."""
    assert set(standards.GRADES) == {
        "non_conformant", "conformant_but_uninformative", "informative"}


def test_air_is_normative_and_tested():
    """Ledger STD-06. The claim that AIR is untested was refuted."""
    air = standards.AIR
    assert air["status"] == "Trial Implementation"
    assert air["tested"]["gazelle_test_definitions"] == 22
    assert air["tested"]["connectathon_passing_records"] == 31
    assert air["creator_requirement"]["force"] == "shall, unconditional"
    assert "shall describe each algorithm" in air["creator_requirement"]["text"]
    # But it cannot be cited as requiring the SR content items to exist.
    assert air["consistency_requirement"]["force"].startswith("will")
    assert air["table_6531_1"]["columns"] == 4


def test_air_table_6531_1_is_a_map_not_a_requirement():
    """Ledger G3-01 to G3-04. Read from the PDF, not reconstructed.

    The grid was confirmed against the page's own ruling lines and against a
    visual render, so the shape below is a transcription. If any of it changes,
    the manuscript's reading of AIR changes with it.
    """
    t = standards.AIR["table_6531_1"]
    assert t["columns"] == 4 and t["rows"] == 4
    assert len(t["column_headers"]) == 4
    assert t["column_headers"][0] == "Contributing Equipment Sequence Attribute"
    assert t["column_headers"][3] == "Algorithm Identification Sequence Attribute"
    assert len(t["cells"]) == 4
    assert all(len(row) == 4 for row in t["cells"])

    # Four cells are empty in the document. Four, not three: an earlier
    # reconstruction missed the Device UID row's fourth column.
    empty = [(r, c) for r, row in enumerate(t["cells"])
             for c, cell in enumerate(row) if not cell]
    assert empty == [(0, 2), (2, 1), (3, 2), (3, 3)]
    assert len(t["empty_cells"]) == 4

    # The reading that decided the study's use of AIR: the Device Observer UID
    # content item sits on the Device UID row, not the Software Versions row.
    assert t["cells"][3][0].startswith("Device UID (0018,1002)")
    assert "121012" in t["cells"][3][1]
    assert t["cells"][2][0].startswith("Software Versions")
    assert t["cells"][2][1] == ""

    # The central question. The table imposes nothing of its own.
    assert t["adds_requirement_beyond_6531_shall"] is False
    assert t["normative_force"].startswith("none of its own")
    assert "shall" not in t["caption_verbatim"]
    assert "should" not in t["caption_verbatim"]
    assert "will" not in t["caption_verbatim"]
    for row in t["cells"]:
        for cell in row:
            low = cell.lower()
            assert "shall" not in low and "should" not in low

    # The one obligation that reaches the table is conditional and is about
    # value equality, never about presence.
    assert "if present, shall contain the same value" in \
        t["invoking_sentence_verbatim"]
    assert t["invoking_sentence_verbatim"] in \
        standards.AIR["consistency_requirement"]["text"]


def test_air_table_write_up_is_rendered_from_the_data():
    md = standards.air_table_markdown()
    t = standards.AIR["table_6531_1"]
    assert t["caption_verbatim"] in md
    assert t["invoking_sentence_verbatim"] in md
    for header in t["column_headers"]:
        assert header in md
    assert "*(empty)*" in md, "empty cells have to be visible as empty"


def test_pixelmed_instance_only_where_it_has_an_iod():
    """Verified: DicomInstanceValidator recognises seven IODs, of which only
    Segmentation is in this population. Listing it elsewhere would record an
    unrecognized-IOD message as a conformance opinion."""
    for sop, axes in validate.PANEL.items():
        if "pixelmed_instance" in axes["conformance"]:
            assert sop == "Segmentation Storage", (
                "%s cannot be checked by DicomInstanceValidator" % sop)
