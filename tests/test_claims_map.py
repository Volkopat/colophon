"""Guards on the claims map.

The map is the thing a reviewer uses to walk from a number in the manuscript to
the row that states it and the file that holds the evidence. Three of those
walks have to be unbroken or the map is decoration: a derivation that names a
row nobody wrote, a retired claim with no reason attached, and a pinning test
that does not exist.

`tests/test_ledger.py` already checks the same three properties against the CSV
directly. These check them through the map, which is what fails if the map's own
join logic drifts away from the ledger it describes.
"""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from colophon import claims_map, ledger
from colophon.paths import LEDGER, REPO

ROWS = ledger.load()

STALE = ("results/ has changed since the map was generated. Rerun "
         "python -m colophon.claims_map")


def _map_rows():
    if not claims_map.MAP_CSV.exists():
        pytest.skip("run python -m colophon.claims_map first")
    with claims_map.MAP_CSV.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _map_is_current() -> bool:
    """Whether the snapshot still describes the directory.

    Parallel tracks write into results/ minutes after a run, so a map older
    than the newest artefact is stale rather than wrong. The tests that compare
    the map against the directory say which, instead of failing on somebody
    else's new file.
    """
    if not claims_map.MAP_MD.exists():
        return False
    newest = max([LEDGER.stat().st_mtime] +
                 [(REPO / f).stat().st_mtime for f in claims_map.results_files()
                  if Path(f).name not in claims_map.NOT_A_CARRIER
                  and "/pending_ledger/" not in f])
    return claims_map.MAP_MD.stat().st_mtime >= newest


def test_no_broken_derivations():
    """A derived row that names a row nobody wrote states nothing checkable."""
    assert claims_map.broken_derivations(ROWS) == []


def test_retired_rows_keep_a_reason():
    """A withdrawn claim stays so the number cannot creep back. Without the
    reason it is just an old claim sitting in the file."""
    for chain in claims_map.retirement_chains(ROWS):
        assert chain["has_reason"], "%s is RETIRED with no reason" % chain["id"]


def test_named_tests_exist():
    """pinned_by_test is only worth carrying if the test is real."""
    for row in ROWS:
        ref = (row.get("pinned_by_test") or "").strip()
        if not ref:
            continue
        assert claims_map.test_exists(ref), (
            "%s names %s, which does not exist" % (row["id"], ref))


def test_every_ledger_row_is_mapped():
    """The map is regenerated rather than maintained.

    If it is older than the ledger, this asserts only that it invented nothing,
    and names the command that brings it back into step.
    """
    records = claims_map.build(ROWS, claims_map.results_files())
    assert [r["id"] for r in records] == [r["id"] for r in ROWS]
    mapped = {r["id"] for r in _map_rows()}
    known = {r["id"] for r in ROWS}
    assert mapped <= known, (
        "the map carries ids the ledger does not: %s" % sorted(mapped - known))
    if claims_map.MAP_CSV.stat().st_mtime >= LEDGER.stat().st_mtime:
        assert mapped == known, (
            "the map is newer than the ledger but misses %s. Regenerate with "
            "python -m colophon.claims_map" % sorted(known - mapped))


def test_orphans_are_reported_not_hidden():
    """An orphan that the write-up omits is worse than one it lists."""
    records = claims_map.build(ROWS, claims_map.results_files())
    orphans = claims_map.orphans(records)
    if not _map_is_current():
        pytest.skip(STALE)
    text = claims_map.MAP_MD.read_text(encoding="utf-8")
    for o in orphans:
        assert o["id"] in text, "%s is an orphan the map does not list" % o["id"]


def test_uncited_artefacts_are_reported():
    """A file no claim rests on is either dead weight or an unrecorded claim,
    and it cannot be either quietly."""
    records = claims_map.build(ROWS, claims_map.results_files())
    loose = claims_map.uncited(records, claims_map.results_files())
    if not _map_is_current():
        pytest.skip(STALE)
    text = claims_map.MAP_MD.read_text(encoding="utf-8")
    for item in loose:
        assert item["file"] in text, (
            "%s is uncited and the map does not say so" % item["file"])


def test_pre_rows_are_reported_unchanged():
    """This track reports the pre-registrations. It never rewords one.

    The map quotes a truncation of the registered claim, so the truncation has
    to be a prefix of what the ledger holds, and the module must not hold a
    write path to the ledger at all.
    """
    registered = {r["id"]: r for r in ROWS if r["id"].startswith("PRE-")}
    reported = {p["id"]: p for p in claims_map.pre_rows(ROWS)}
    assert set(reported) == set(registered)
    for rid, p in reported.items():
        stem = p["claim"].rsplit(" ...", 1)[0]
        assert " ".join(registered[rid]["claim"].split()).startswith(stem)
    source = (REPO / "colophon" / "claims_map.py").read_text(encoding="utf-8")
    for forbidden in ("ledger.record(", "ledger.record_many(", "ledger.retire("):
        assert forbidden not in source, (
            "the claims map must propose rows, not write them: %s" % forbidden)


def test_floor_rule_is_the_ledgers_own():
    """One definition of a rate in this repository, not two.

    The map decides which rows quote a rate by asking
    colophon.ledger.rates_without_floor over a copy with the floors blanked, so
    a change to that rule changes the map with it.
    """
    quoting = claims_map.rows_quoting_a_rate(ROWS)
    missing = set(ledger.rates_without_floor(LEDGER))
    assert missing <= quoting
    expected = {r["id"] for r in ROWS
                if r["id"] in quoting and not (r.get("floor") or "").strip()}
    assert expected == missing


def test_the_map_never_quotes_a_retired_claim_in_full():
    """The retired-prose guard compares claim[:60] against every markdown file
    in results/. The map lists every retired row by construction, so it has to
    stay under that or it fails the guard it is describing."""
    for row in ROWS:
        quoted = claims_map.truncate_claim(row["claim"])
        stem = " ".join(row["claim"].split())[:60]
        assert stem not in quoted, "%s is quoted in full" % row["id"]
    if claims_map.MAP_MD.exists():
        text = claims_map.MAP_MD.read_text(encoding="utf-8").lower()
        for row in ROWS:
            if row["status"] != "RETIRED":
                continue
            assert row["claim"].lower()[:60] not in text, (
                "the map reproduces retired claim %s" % row["id"])


def test_the_carrier_scan_excludes_the_maps_own_output():
    """The map names every id. Counting it as a carrier would report full
    coverage whatever the write-ups say, which is the measurement failing
    silently rather than loudly."""
    files = claims_map.results_files() + [
        "results/claims_map.md", "results/claims_map.csv", "results/ledger.csv"]
    scanned = claims_map.carrier_files(files)
    assert not [f for f in scanned
                if f.endswith(("claims_map.md", "claims_map.csv", "ledger.csv"))]
    assert not [f for f in scanned if "/pending_ledger/" in f]


def test_the_checks_can_fail():
    """A guard that cannot fail is not a guard."""
    invented = ROWS + [dict.fromkeys(ledger.FIELDS, "")]
    invented[-1].update(id="X-99", section="X", claim="synthetic",
                        status="RETIRED", derived_from="NOT-A-ROW")
    assert claims_map.broken_derivations(invented) == [("X-99", "NOT-A-ROW")]
    assert claims_map.retirement_chains(invented)[-1]["has_reason"] is False
    assert claims_map.test_exists("tests/test_claims_map.py::not_a_test") is False
    assert claims_map.test_exists("tests/test_claims_map.py::test_the_checks_can_fail")
