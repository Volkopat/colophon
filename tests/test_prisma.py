"""What makes the PRISMA-S appendix binding rather than decorative.

The appendix exists so a negative prior-art claim can be audited. That only
works if the appendix is a faithful rendering of `colophon/prior_art.py` rather
than a prettier retelling of it, so the two checks that matter are: every
recorded query reaches the table, and no row states a hit count the record did
not capture. A generated appendix that quietly invented a number would be worse
than the prose it replaced, because it would look checkable.
"""
from __future__ import annotations

import csv
import json
import re

import pytest

from colophon import ledger, prior_art, prisma

ROWS = prisma.build_rows()
COUNTS = prisma.counts(ROWS)
APPENDIX_TEXT = prisma.APPENDIX.read_text(encoding="utf-8")


def _csv_rows() -> list[dict]:
    with prisma.ROWS_CSV.open(newline="", encoding="utf-8") as fh:
        return [dict(r) for r in csv.DictReader(fh)]


CSV_ROWS = _csv_rows()


# --- the two checks the appendix exists for ----------------------------------

def test_every_query_appears_in_the_csv():
    """A query that does not reach the table is a query a reviewer cannot
    re-run, and its absence would be invisible in a 168 row file."""
    in_csv = [r["query"] for r in CSV_ROWS if r["row_type"] == "web_search_query"]
    missing = [q for q in prior_art.QUERIES if q not in in_csv]
    assert not missing, "queries absent from the CSV: %s" % missing[:5]
    assert len(in_csv) == len(prior_art.QUERIES), (
        "%d web search rows for %d recorded queries"
        % (len(in_csv), len(prior_art.QUERIES)))
    assert in_csv == list(prior_art.QUERIES), (
        "the CSV reorders or duplicates the recorded queries")


# Rows for searches the author executed directly against a public interface.
# Every other row in this appendix describes an LLM-assisted search whose
# interface was not captured, which is why so many of its cells read "not
# captured". These rows are the opposite case: the query, the interface and the
# integer returned are all recorded, and the numbers come from the interface
# rather than from colophon.prior_art. Each guard below names them explicitly
# rather than quietly widening.
EXECUTED_ROW_TYPES = {"database_query", "documentary_search"}


def _executed(row):
    return row["row_type"] in EXECUTED_ROW_TYPES


def test_no_row_claims_an_uncaptured_hit_count():
    """Every number in the hits column has to be transcribed from the entry it
    came from. Anything else is a hit count this project invented."""
    for row in CSV_ROWS:
        value = row["hits_returned"].strip()
        if not re.fullmatch(r"\d+", value):
            continue
        if _executed(row):
            # The number came from the interface named in the row, and the
            # ledger row it cites carries it. Checked by
            # test_executed_search_hit_counts_are_in_the_ledger below.
            continue
        assert value in row["source_record"], (
            "row %r states hit count %s, which does not appear in the record "
            "it came from: %s" % (row["query"][:40], value, row["source_record"]))


def test_the_captured_hit_counts_are_exactly_the_recorded_ones():
    """Extracted independently of colophon.prisma, so a bug in its parser shows
    up as a disagreement rather than as a matching pair of wrong numbers."""
    expected = []
    for record in prior_art.RETRIEVED:
        expected += re.findall(r"\((\d+) record", record)
        expected += re.findall(r"hitCount (\d+)", record)
    found = [r["hits_returned"] for r in CSV_ROWS
             if re.fullmatch(r"\d+", r["hits_returned"].strip())
             and not _executed(r)]
    assert sorted(found, key=int) == sorted(expected, key=int)


def test_web_search_rows_never_state_a_hit_count():
    """General web search returned no count that was recorded, so no row may
    imply one. This is the rule the appendix reports itself as failing."""
    for row in CSV_ROWS:
        if row["row_type"] != "web_search_query":
            continue
        assert row["hits_returned"] == prisma.NOT_CAPTURED
        assert row["records_screened"] == prisma.NOT_CAPTURED
        assert row["records_included"] == prisma.NOT_CAPTURED


def test_the_hit_count_check_can_fail():
    """A guard that cannot fail is not a guard."""
    bad = dict(hits_returned="9999", source_record="colophon.prior_art.QUERIES[0]")
    assert re.fullmatch(r"\d+", bad["hits_returned"])
    assert bad["hits_returned"] not in bad["source_record"]


# --- the table itself ---------------------------------------------------------

def test_csv_header_matches_the_module_schema():
    with prisma.ROWS_CSV.open(newline="", encoding="utf-8") as fh:
        header = next(csv.reader(fh))
    assert header == prisma.COLUMNS
    assert [name for name, _ in prisma.COLUMN_MEANING] == prisma.COLUMNS, (
        "every column has to be defined in the appendix schema table")


def test_no_cell_is_silently_blank():
    """A blank cell and "not captured" read the same to a reviewer and mean
    different things. Only `notes` is allowed to be empty."""
    for row in CSV_ROWS:
        for column in prisma.COLUMNS:
            if column == "notes":
                continue
            assert row[column].strip(), (
                "%s is blank on a %s row: %s"
                % (column, row["row_type"], row["source_record"][:60]))


def test_every_recorded_entry_reaches_a_row():
    """Nothing in the record may be dropped by this rendering of it."""
    expected = {
        "web_search_query": len(prior_art.QUERIES),
        "targeted_retrieval": len(prior_art.RETRIEVED),
        "failed_retrieval": len(prior_art.FAILED_RETRIEVALS),
        "excluded_record": len(prior_art.UNVERIFIED),
        "included_record": len(prior_art.NEIGHBOURS),
        "source_not_searched": len(prisma.NOT_SEARCHED),
    }
    for entry in prisma.EXECUTED_SEARCHES:
        expected[entry["row_type"]] = expected.get(entry["row_type"], 0) + 1
    actual = {}
    for row in CSV_ROWS:
        actual[row["row_type"]] = actual.get(row["row_type"], 0) + 1
    assert actual == expected
    assert len(CSV_ROWS) == sum(expected.values())


def test_the_angles_come_from_the_recorded_comments():
    """The sweep labels are read from colophon/prior_art.py rather than retyped,
    so a query cannot end up under a label that is not above it in the source."""
    angles = prisma.query_angles()
    assert len(angles) == len(prior_art.QUERIES)
    assert prisma.NOT_CAPTURED not in angles, (
        "a query fell outside every angle comment")
    assert len(set(angles)) == 5, "five sweeps were recorded, found %s" % sorted(set(angles))


def test_not_searched_venues_are_in_the_recorded_coverage_limits():
    """The not-searched list is data in colophon/prisma.py. It has to keep
    agreeing with the prose it was read out of, or it becomes a second and
    quietly different record of the same fact."""
    limits = prior_art.COVERAGE_LIMITS
    for venue in prisma.NOT_SEARCHED:
        assert venue in limits, (
            "%s is carried as not searched but does not appear in "
            "colophon.prior_art.COVERAGE_LIMITS" % venue)


def test_included_records_are_checked_against_the_retrieval_log():
    """The record says every nearest neighbour was retrieved and read. The
    retrieval log lists fewer of them, and the appendix has to say so."""
    blob = "\n".join(prior_art.RETRIEVED)
    unlogged = [n for n in prior_art.NEIGHBOURS if n["url"] not in blob]
    assert COUNTS["included_unlogged"] == len(unlogged)
    if unlogged:
        assert "GAP-14" in APPENDIX_TEXT


# --- the appendix -------------------------------------------------------------

def test_generated_files_are_current(tmp_path):
    """Both artefacts are generated, so a committed copy that no longer matches
    its generator is a number that has drifted out of agreement with its data."""
    assert APPENDIX_TEXT == prisma.render_markdown(ROWS)
    scratch = tmp_path / "rows.csv"
    prisma.write_csv(ROWS, scratch)
    assert (prisma.ROWS_CSV.read_text(encoding="utf-8")
            == scratch.read_text(encoding="utf-8"))


def test_prisma_s_items_are_all_answered():
    numbers = [n for n, _, _, _ in prisma.PRISMA_S]
    assert numbers == list(range(1, 17)), "PRISMA-S has 16 items"
    vocabulary = {status for status, _ in prisma.PRISMA_STATUS}
    for n, title, status, text in prisma.PRISMA_S:
        assert status in vocabulary, "item %d has status %r" % (n, status)
        assert len(text.split()) >= 8, "item %d is answered in a fragment" % n
        assert title in APPENDIX_TEXT
    assert sum(COUNTS["prisma_status"].values()) == len(prisma.PRISMA_S)


def test_the_appendix_does_not_claim_to_be_a_systematic_review():
    lowered = APPENDIX_TEXT.lower()
    assert "this was not a systematic review" in lowered
    assert "no librarian" in lowered or "librarian" in lowered
    assert "**librarian.** none" in lowered
    assert "**peer review of the search.** none" in lowered


def test_the_auditability_rule_is_stated_and_applied():
    """The rule is only worth stating if the appendix then applies it and
    reports the answer, including where the answer is that the search fails."""
    assert "if and only if" in prisma.AUDITABILITY_RULE
    # The rule is reflowed into a blockquote, so compare on the words.
    flat = " ".join(APPENDIX_TEXT.replace("\n> ", " ").split())
    assert " ".join(prisma.AUDITABILITY_RULE.split()) in flat
    for fragment in ("Condition (a) is met for", "Condition (b) is met only for",
                     "## S.3 Tolerance", "5 percent",
                     "not reproducible in the way a database query is"):
        assert fragment in APPENDIX_TEXT, "the appendix omits %r" % fragment
    assert COUNTS["hits_captured"] < COUNTS["query_rows"], (
        "if every query row carried a count, the appendix text would be wrong")


def test_every_gap_reaches_the_appendix():
    ids = [gid for gid, _, _, _ in GAPS_SORTED]
    assert ids == sorted(ids), "gap ids are out of order"
    for gid, kind, title, text in prisma.GAPS:
        assert gid in APPENDIX_TEXT, "%s is not in the appendix" % gid
        assert title in APPENDIX_TEXT
        assert kind in (prisma.FIELD_GAP, prisma.COVERAGE_GAP)
    assert COUNTS["field_gaps"] + COUNTS["coverage_gaps"] == len(prisma.GAPS)
    assert COUNTS["field_gaps"] > 0


GAPS_SORTED = sorted(prisma.GAPS)


@pytest.mark.parametrize("label", [
    "**Information sources searched.**",
    "**Information sources not searched.**",
    "**Grey literature.**",
    "**Citation chaining.**",
    "**Librarian.**",
    "**Peer review of the search.**",
    "**Date limits.**",
    "**Language limits.**",
    "**Who ran it, and how.**",
])
def test_the_required_narrative_fields_are_present(label):
    assert label in APPENDIX_TEXT, "the appendix omits the %s field" % label


def test_llm_use_is_declared_on_every_row_that_had_one():
    assert "LLM assisted" in prisma.RUN_BY
    assert "results/ai_use.md" in prisma.RUN_BY
    for row in CSV_ROWS:
        if row["row_type"] == "source_not_searched":
            continue
        if _executed(row):
            # Declaring LLM assistance on a search the author ran directly
            # would be a false declaration, which is worse than none.
            assert "author" in row["run_by"]
            assert "LLM" not in row["run_by"]
            continue
        assert row["run_by"] == prisma.RUN_BY


def test_grey_literature_is_reported_as_unsystematic():
    """Posda is the closest prior work and it lives in a repository, so a search
    that did not reach repositories has to say so rather than imply coverage."""
    assert "**Grey literature.** Included, but not systematically." in APPENDIX_TEXT
    assert "PA-08 and PA-09" in APPENDIX_TEXT
    assert "GAP-16" in APPENDIX_TEXT


# --- the proposed ledger rows -------------------------------------------------

PROPOSED = json.loads(prisma.PENDING.read_text(encoding="utf-8"))


def test_proposed_rows_use_only_ledger_fields():
    for row in PROPOSED:
        unknown = sorted(set(row) - set(ledger.FIELDS))
        assert not unknown, "%s carries unknown fields %s" % (row["id"], unknown)
        assert row["status"] in ledger.VALID_STATUS


def test_proposed_measured_rows_carry_what_the_ledger_requires():
    for row in PROPOSED:
        if row["status"] != "MEASURED":
            continue
        for field in ("command", "source_file", "dropped", "floor"):
            assert row.get(field, "").strip(), (
                "%s is MEASURED with no %s" % (row["id"], field))


def test_proposed_rows_are_current():
    assert PROPOSED == prisma.ledger_rows(ROWS)


def test_the_pa07_outcome_reproduces_its_claim_exactly():
    """A pre-existing claim is never reworded. The row is copied from the
    ledger, so anything but status_note differing is a rewrite."""
    proposed = {r["id"]: r for r in PROPOSED}.get("PA-07")
    if proposed is None:
        pytest.skip("no PA-07 outcome proposed")
    existing = {r["id"]: r for r in ledger.load()}["PA-07"]
    assert proposed["claim"] == existing["claim"]
    assert proposed["status"] == existing["status"]
    assert proposed["value"] == existing["value"]
    changed = sorted(k for k in ledger.FIELDS
                     if k not in ("date", "status_note")
                     and proposed.get(k, "") != existing.get(k, ""))
    assert not changed, "the PA-07 proposal alters %s" % changed
    assert proposed["status_note"] == prisma.PA07_NOTE


def test_executed_search_hit_counts_are_in_the_ledger():
    """The executed rows carry numbers from an interface rather than from
    colophon.prior_art, so their backing is the ledger row each cites."""
    from colophon import ledger
    rows = {r["id"]: r for r in ledger.load()}
    executed = [r for r in CSV_ROWS if _executed(r)]
    assert executed, "the executed searches are missing from the appendix"
    for row in executed:
        rid = row["source_record"].replace("ledger", "").strip()
        assert rid in rows, rid
        value = row["hits_returned"].strip()
        if re.fullmatch(r"\d+", value) and value != "0":
            blob = rows[rid]["value"] + rows[rid]["n"] + rows[rid]["denominator"]
            assert value in blob.replace(",", ""), (rid, value)


def test_the_two_zero_hit_attribute_names_are_recorded_as_zero():
    """The single most auditable negative in this appendix. If either becomes
    non-zero the lead finding needs re-reading, so it is pinned here."""
    zeros = {r["query"].strip(): r["hits_returned"].strip()
             for r in CSV_ROWS if _executed(r)}
    assert zeros.get("SegmentationAlgorithmIdentificationSequence") == "0"
    assert zeros.get("ContributingEquipmentSequence") == "0"
