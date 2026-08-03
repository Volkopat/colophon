"""Guards on the two manuscript tables.

The tables are generated, so the risk is not a typo. It is that a class the
census had not finished slips into Table 1 and reads as a rate over the whole
class, or that a cell only one writer could reach reads as agreement between
two. Both of those are silent failures: the output still looks like a table.

Every assertion here recomputes from the same sources the module reads, rather
than pinning a literal. Pinned literals would have to be edited every time the
census advances, and a number that gets edited to make a test pass is not a
pinned number. The one thing that does hold still is that a SOP class the census
has finished stays finished: the census skips a series it has already recorded,
so a complete class never gains or loses objects.
"""
from __future__ import annotations

import csv
import json

import pytest

from colophon import census, floor, tables
from colophon.paths import RESULTS

MANUSCRIPT = RESULTS / "manuscript"
TABLE1 = MANUSCRIPT / "table1_writers.csv"
TABLE2 = MANUSCRIPT / "table2_floor_set.csv"


def _rows(path):
    if not path.exists():
        pytest.skip("run python -m colophon.tables first")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@pytest.fixture(scope="module")
def scanned():
    if not tables.RECORDS.exists():
        pytest.skip("no census records to read")
    return tables.scan()


@pytest.fixture(scope="module")
def table1():
    return _rows(TABLE1)


@pytest.fixture(scope="module")
def table2():
    return _rows(TABLE2)


# --- Table 1 ------------------------------------------------------------------
def test_no_incomplete_class_in_table1(table1, scanned):
    """Ledger F2-08. A class the census has not finished must not appear at all,
    not even with a partial count that a reader could mistake for the whole."""
    totals = census.class_totals()
    for name in {r["sop_class_name"] for r in table1}:
        in_manifest = totals.get(name, 0)
        recorded = scanned["series"].get(name, 0)
        assert in_manifest > 0, "%s is in Table 1 but not in the census manifest" % name
        assert recorded >= in_manifest, (
            "%s appears in Table 1 with only %d of %d series recorded"
            % (name, recorded, in_manifest))


def test_segmentation_never_appears_in_table1(table1):
    """It is outside the census scope entirely, so any row for it would have come
    from somewhere this module does not read."""
    assert census.EXCLUDED not in {r["sop_class_name"] for r in table1}


def test_object_counts_match_the_census(table1, scanned):
    """Ledger F2-01. The objects attributed in Table 1 for a class have to be
    every object the census recorded for that class, with nothing dropped in the
    cross-tabulation and nothing counted twice."""
    per_class = {}
    for row in table1:
        per_class[row["sop_class_name"]] = (
            per_class.get(row["sop_class_name"], 0) + int(row["objects"]))
    assert per_class, "Table 1 is empty"
    for name, counted in per_class.items():
        assert counted == scanned["objects"].get(name, 0), (
            "%s: Table 1 accounts for %d objects, the census recorded %d"
            % (name, counted, scanned["objects"].get(name, 0)))


def test_every_object_carries_a_verdict(table1):
    """A row with no verdict is a row that escaped the comparison the table
    exists to make."""
    allowed = {tables.AGREE, tables.DISAGREE, tables.NO_EXPECTATION,
               tables.EQUIPMENT_SILENT}
    for row in table1:
        assert row["verdict"] in allowed, "unknown verdict %r" % row["verdict"]


def test_disagreement_rests_on_a_registered_expectation(table1):
    """Ledger F2-03. Only a toolkit whose file-meta signature was established
    independently of this corpus may generate a disagreement. Otherwise the
    count measures the vocabulary of two rules rather than the objects."""
    for row in table1:
        if row["verdict"] in (tables.AGREE, tables.DISAGREE):
            assert row["equipment_writer"] in tables.EXPECTED_FILE_META, (
                "%s was scored %s with no registered expectation"
                % (row["equipment_writer"], row["verdict"]))
            assert row["expectation_status"].strip()
        else:
            assert row["expectation_status"] == "not applicable"


def test_the_scored_expectations_are_source_confirmed_or_labelled():
    """A disagreement resting on a guess is a guess. Each expectation states
    whether it came out of the toolkit's source or only out of observed values,
    and the table carries that status on every scored row."""
    for writer, expectation in tables.EXPECTED_FILE_META.items():
        assert expectation["expects"]
        assert ("CONFIRMED from source" in expectation["status"]
                or "NOT source confirmed" in expectation["status"]), (
            "%s states neither that it is source confirmed nor that it is not"
            % writer)


def test_equipment_rule_is_reused_verbatim(table1):
    """Ledger F2-10. The equipment side of the comparison has to be the Phase 0
    rule as registered. If this module grew its own rule the disagreement count
    would be comparing two things this project wrote."""
    from colophon import writers
    assert tables.writer_of is writers.writer_of
    labels = {r["equipment_writer"] for r in table1}
    known = {name for name, _ in writers.WRITER_RULES} | {writers.UNKNOWN_WRITER}
    assert labels <= known, "Table 1 invented equipment labels: %s" % (labels - known)


def test_file_meta_beats_equipment_on_the_highdicom_constant():
    """The rule has to actually read the file meta. An object whose equipment
    attributes name nothing but whose ImplementationClassUID is highdicom's
    compile-time constant must come back as highdicom."""
    writer, evidence, status = tables.attribute_file_meta({
        "ImplementationClassUID": "1.2.826.0.1.3680043.9.7433.1.1",
        "ImplementationVersionName": "highdicom0.27.0",
        "Manufacturer": "", "ManufacturerModelName": "",
    })
    assert writer == "highdicom"
    assert evidence.startswith("ImplementationClassUID")
    assert "CONFIRMED from source" in status


def test_conflicting_file_meta_is_not_silently_resolved():
    """Two carriers naming two toolkits is a finding, not a tie to be broken."""
    writer, _, _ = tables.attribute_file_meta({
        "ImplementationClassUID": "1.2.826.0.1.3680043.9.7433.1.1",
        "ImplementationVersionName": "PIXELMEDJAVA001",
    })
    assert writer == tables.INCONSISTENT


def test_an_unknown_implementation_is_recorded_verbatim():
    """An identity this project cannot pin to a toolkit is carried through with
    both values intact, not merged into an 'other' bucket."""
    writer, _, status = tables.attribute_file_meta({
        "ImplementationClassUID": "1.3.6.1.4.1.22213.1.143",
        "ImplementationVersionName": "0.5",
    })
    assert "1.3.6.1.4.1.22213.1.143" in writer and "0.5" in writer
    assert "not resolved" in status


def test_identity_spread_is_reported(table1, scanned):
    """Ledger F2-04. The many-to-one mapping is computed over the complete
    classes only, like everything else in Table 1."""
    complete = sorted({r["sop_class_name"] for r in table1})
    spread = tables.identity_spread(scanned, complete)
    assert len(spread), "no file-meta identities were recorded"
    assert int(spread["objects"].sum()) == sum(
        scanned["objects"].get(name, 0) for name in complete)


def test_reverse_spread_counts_toolkits_not_releases(table1, scanned):
    """Ledger F2-04, second half. Three releases of one toolkit behind one
    declared producer is ordinary. Two different toolkits is the finding, and
    the two must not be conflated."""
    complete = sorted({r["sop_class_name"] for r in table1})
    reverse = tables.equipment_spread(scanned, complete)
    for row in reverse.itertuples():
        writers = [part.rsplit(" (", 1)[0] for part in
                   row.file_meta_writers.split("; ")]
        assert len(set(writers)) == int(row.distinct_file_meta_writers) >= 2
        assert len(set(writers)) == len(writers), (
            "%s lists a writer twice, so releases are being counted as writers"
            % row.declared_Manufacturer)


def test_scan_reports_skipped_lines(scanned):
    """Ledger F2-09. The census appends while this reads, so an unparseable line
    is expected and has to be counted rather than swallowed."""
    assert "lines_skipped" in scanned and "lines_seen" in scanned
    assert scanned["lines_seen"] >= scanned["lines_skipped"] >= 0


def test_a_half_written_line_is_skipped_and_counted(tmp_path):
    """A guard that cannot fail is not a guard, so the truncation is simulated
    rather than waited for."""
    path = tmp_path / "records.jsonl"
    good = json.dumps({"sop_class_name": "Parametric Map Storage",
                       "series_instance_uid": "1.2.3",
                       "collection_id": "c", "analysis_result_id": None,
                       "objects": [{"status": "OK",
                                    "ImplementationClassUID":
                                        "1.2.826.0.1.3680043.9.7433.1.1",
                                    "ImplementationVersionName": "highdicom0.27.0",
                                    "Manufacturer": "IDC",
                                    "ManufacturerModelName": ""}]})
    path.write_text(good + "\n" + good[:60], encoding="utf-8")
    out = tables.scan(path)
    assert out["lines_seen"] == 2
    assert out["lines_skipped"] == 1
    assert out["objects"]["Parametric Map Storage"] == 1


# --- Table 2 ------------------------------------------------------------------
def test_single_writer_cells_are_marked(table2):
    """Ledger F2-05. dcmqi could not emit SEG FRACTIONAL or Parametric Map, so
    those cells describe one writer and transfer to nobody. Marked with the
    reason, so the cell cannot be read as two writers agreeing."""
    assert floor.W2_EMISSION_GAPS, "the emission gaps went missing from Phase 1"
    marked = set()
    for row in table2:
        expected = "yes" if row["sop_class"] in floor.W2_EMISSION_GAPS else "no"
        assert row["cell_single_writer"] == expected, (
            "%s / %s / %s is marked %s" % (row["writer"], row["sop_class"],
                                           row["validator"],
                                           row["cell_single_writer"]))
        if expected == "yes":
            assert row["single_writer_reason"].strip(), (
                "%s is single-writer with no reason given" % row["sop_class"])
            assert row["cell_jaccard"] in ("", "n/a"), (
                "%s is single-writer but carries a Jaccard" % row["sop_class"])
            marked.add(row["sop_class"])
        else:
            assert not row["single_writer_reason"].strip()
    assert marked == set(floor.W2_EMISSION_GAPS), (
        "not every emission gap reached Table 2: %s"
        % (set(floor.W2_EMISSION_GAPS) - marked))


def test_zero_floors_are_present_not_omitted(table2):
    """A writer that drew nothing is the most important cell in the table, and
    an absent row would read as missing data rather than as a floor of zero."""
    cells = {(r["writer"], r["sop_class"], r["validator"]) for r in table2}
    expected = {(w, c, v) for w, c in tables.floor_cells() for v in floor.VALIDATORS}
    assert cells == expected
    empty = [r for r in table2 if not r["message_class_id"]]
    assert empty, "no zero-floor cell survived, but Phase 1 measured several"
    for row in empty:
        assert "zero" in row["message_template"]


def test_seg_binary_jaccard_is_the_corrected_value(table2):
    """Ledger F2-06, and F1-03-prev which it replaces. 6 of 7, not 1.0."""
    values = {r["cell_jaccard"] for r in table2
              if r["sop_class"] == "SEG BINARY" and r["validator"] == "dicom-validator"}
    assert values == {"0.8571"}, values


def test_every_floor_message_class_is_in_table2(table2):
    """Table 2 is the floor set, so it has to be the whole floor set."""
    rows = tables.load_floor_rows()
    assert {r["message_class_id"] for r in rows} == {
        r["message_class_id"] for r in table2 if r["message_class_id"]}


def test_corpus_context_is_bounded(table2):
    """Ledger F2-07. A corpus count must name the SOP class and the snapshot
    denominator it came from, so a zero cannot be read as absence."""
    for row in table2:
        if not row["message_class_id"]:
            continue
        assert row["corpus_context"].strip()
        if int(row["corpus_objects"]) == 0:
            assert "not observed" in row["corpus_context"]
        else:
            assert " of " in row["corpus_context"]


# --- the proposed ledger rows -------------------------------------------------
def test_pending_ledger_rows_are_well_formed():
    """Proposals are merged by colophon.merge_ledger without a human reading
    them, so a malformed key would land in the ledger unnoticed."""
    from colophon import ledger
    path = tables.PENDING / "track_f2.json"
    if not path.exists():
        pytest.skip("run python -m colophon.tables first")
    rows = json.loads(path.read_text(encoding="utf-8"))
    assert rows
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids)), "duplicate id in the proposal"
    for row in rows:
        assert row["id"].startswith("F2-"), row["id"]
        assert set(row) <= set(ledger.FIELDS), sorted(set(row) - set(ledger.FIELDS))
        assert row["status"] in ledger.VALID_STATUS
        assert row["claim"].strip() and row["value"].strip()
        if row["status"] == "MEASURED":
            for field in ("command", "source_file", "dropped", "floor"):
                assert row.get(field, "").strip(), "%s has no %s" % (row["id"], field)


def test_no_pre_registration_is_touched():
    """A track may record an outcome. It may never author or edit a PRE- row."""
    path = tables.PENDING / "track_f2.json"
    if not path.exists():
        pytest.skip("run python -m colophon.tables first")
    rows = json.loads(path.read_text(encoding="utf-8"))
    assert not [r for r in rows if r["id"].startswith("PRE-")]
