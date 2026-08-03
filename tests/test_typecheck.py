"""Type re-verification: the standard is read directly, and the ceiling is derived."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from colophon import claim3, typecheck


def test_every_type_reproduces():
    """17 assertions against PS3.3 2026c. A failure means a claim built on that
    Type has to drop to PENDING until it is resolved."""
    if not typecheck.MODULE_INFO.exists():
        pytest.skip("pre-seeded standard not present")
    types = typecheck.verify_types()
    failed = types[types.reproduces != "yes"]
    assert failed.empty, failed.to_dict("records")
    assert len(types) >= 17


def test_the_two_attributes_of_the_lead_finding_are_governed_differently():
    """The split the lead finding rests on: 1C against 3, in the same sequence."""
    if not typecheck.MODULE_INFO.exists():
        pytest.skip("pre-seeded standard not present")
    types = typecheck.verify_types().set_index(["tag", "table"])
    assert types.loc[("(0062,0009)", "C.8.20.2"), "type_in_2026c"] == "1C"
    assert types.loc[("(0062,0007)", "C.8.20.2"), "type_in_2026c"] == "3"
    assert types.loc[("(0062,0007)", "C.8.20.5"), "type_in_2026c"] == "1C"


def test_the_ceiling_has_three_tiers():
    """Written from Enhanced General Equipment alone, the ceiling sentence was
    false: General Equipment is a second module with Usage M everywhere."""
    if not typecheck.IOD_INFO.exists():
        pytest.skip("pre-seeded standard not present")
    _, summary = typecheck.verify_ceiling()
    assert summary["measured_iods"] == 8
    assert summary["iods_with_enhanced_general_equipment_usage_M"] == 2
    assert summary["iods_with_general_equipment_usage_M"] == 8
    assert summary["manufacturer_type_in_general_equipment"] == ["2"]


def test_grading_carries_the_type2_binding():
    """Without it, the attribution arm and the conformance arm contradict each
    other on the 40 Key Object Selection objects."""
    assert claim3.TYPE2_CARRIER == "Manufacturer"
    source = Path(claim3.__file__).read_text(encoding="utf-8")
    assert "Type 2 in a module with Usage M here" in source


def test_absent_manufacturer_is_non_conformant_in_every_class():
    import pandas as pd
    base = {"sop_class_name": "Key Object Selection Document Storage",
            "ces_items": "[]", "segments": "[]", "Manufacturer": "",
            "ManufacturerModelName": "", "SeriesDescription": "",
            "ContentCreatorName": "", "DeviceSerialNumber": ""}
    for carrier in claim3.TYPE1_CARRIERS:
        base[carrier + "_state"] = "non_empty"
    absent = dict(base, Manufacturer_state="absent")
    empty = dict(base, Manufacturer_state="empty")
    graded = claim3.grade_objects(pd.DataFrame([absent, empty]))
    assert graded.iloc[0]["grade"] == "non-conformant"
    # Type 2 permits zero length, so an empty Manufacturer is not a violation.
    assert graded.iloc[1]["grade"] != "non-conformant"


def test_the_dcmqi_clone_resolves_shas_offline():
    if not claim3.DCMQI_CLONE.exists():
        pytest.skip("clone absent")
    out = claim3.resolve_sha("4e5b700")
    assert out["resolution"] == "upstream"
    assert out["resolved_commit_date"].startswith("20")
    assert out["nearest_tag"].startswith("v")
    missing = claim3.resolve_sha("0000000")
    assert missing["resolution"].startswith("orphaned")


def test_the_two_attributes_are_adjacent_rows_of_C_8_20_2():
    """STD-09. A summarising fetch of Table C.8.20-4 returned neither attribute,
    which was right: they live in C.8.20-2, adjacent, inside Segment Sequence,
    immediately after the row that includes C.8.20-4. The harmonisation argument
    in the Discussion depends on that adjacency, so it is pinned."""
    if not typecheck.DOCBOOK.exists():
        pytest.skip("pre-seeded standard not present")
    import re
    xml = typecheck.DOCBOOK.read_text(encoding="utf-8", errors="replace")
    tables = dict(re.findall(r'<table[^>]*xml:id="([^"]+)"[^>]*>(.*?)</table>',
                             xml, re.S))
    macro = tables["table_C.8.20-4"]
    module = tables["table_C.8.20-2"]

    # The macro carries the algorithm type and neither of the other two.
    assert "(0062,0008)" in macro
    assert "(0062,0009)" not in macro
    assert "(0062,0007)" not in macro

    # The module carries both, and they are adjacent.
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", module, re.S)
    where = {}
    for n, row in enumerate(rows):
        for tag in ("(0062,0009)", "(0062,0007)"):
            if tag in row:
                where.setdefault(tag, n)
    assert set(where) == {"(0062,0009)", "(0062,0007)"}
    assert where["(0062,0007)"] == where["(0062,0009)"] + 1, (
        "the two rows are no longer adjacent: %s" % where)


def test_the_condition_text_is_unchanged():
    """STD-09 and the CP rationale. The condition the proposal would copy has to
    read exactly this."""
    if not typecheck.DOCBOOK.exists():
        pytest.skip("pre-seeded standard not present")
    import re
    xml = typecheck.DOCBOOK.read_text(encoding="utf-8", errors="replace")
    module = re.search(r'<table[^>]*xml:id="table_C\.8\.20-2"[^>]*>(.*?)</table>',
                       xml, re.S).group(1)
    row = next(r for r in re.findall(r"<tr[^>]*>(.*?)</tr>", module, re.S)
               if "(0062,0009)" in r)
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", row))
    assert ("Required if Segment Algorithm Type (0062,0008) is not MANUAL"
            in text)
