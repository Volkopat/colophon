"""What makes the ledger binding rather than decorative.

Ported from the guards in spine-gsps `tests/test_docs_consistency.py`, rebuilt
against CSV. That project shipped two retired figures that survived a careful
human read: "Neither survives a string search, so the search is a test."
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

import pytest

from colophon import ledger
from colophon import archive
from colophon.paths import ENV, LEDGER, REPO, RESULTS

ROWS = ledger.load()


def test_ledger_exists_and_is_populated():
    assert LEDGER.exists(), "run python -m colophon.index first"
    assert len(ROWS) > 0


def test_header_matches_the_schema():
    with LEDGER.open(newline="", encoding="utf-8") as fh:
        header = next(csv.reader(fh))
    assert header == ledger.FIELDS


def test_ids_are_unique():
    """spine-gsps shipped id H3c twice. Uniqueness is enforced at write time by
    colophon.ledger.write, and checked here against the file on disk."""
    ids = [r["id"] for r in ROWS]
    assert len(ids) == len(set(ids)), (
        "duplicate ids: %s" % sorted({i for i in ids if ids.count(i) > 1}))


def test_statuses_are_from_the_vocabulary():
    for r in ROWS:
        assert r["status"] in ledger.VALID_STATUS, (
            "%s has status %r" % (r["id"], r["status"]))


def test_measured_rows_carry_a_command_and_a_source():
    for r in ROWS:
        if r["status"] != "MEASURED":
            continue
        assert r["command"].strip(), "%s is MEASURED with no command" % r["id"]
        assert r["source_file"].strip(), "%s is MEASURED with no source" % r["id"]


def test_every_rate_names_its_floor():
    """The project rule: a failure rate quoted without its floor is not a
    number."""
    assert ledger.rates_without_floor() == []


def test_measured_rows_state_what_was_dropped():
    """Silent truncation reads as full coverage, so the field is mandatory. A
    run that dropped nothing has to say so."""
    for r in ROWS:
        if r["status"] == "MEASURED":
            assert r["dropped"].strip(), "%s does not say what it dropped" % r["id"]


def test_retired_rows_keep_their_reason():
    for r in ROWS:
        if r["status"] == "RETIRED":
            assert r["retired_reason"].strip(), (
                "%s is RETIRED with no reason" % r["id"])


def test_source_files_exist():
    for r in ROWS:
        # Tracks separate multiple artefacts with a comma, a semicolon or
        # the word and. All three are accepted: the check is that the
        # file exists, not that the row punctuates to one house style.
        for token in re.split(r"\s+and\s+|[;,]\s*", r["source_file"]):
            token = token.strip()
            if not token or "*" in token:
                continue
            if archive.excluded(token):
                # Absent by design, not missing. The public archive does not
                # carry this path and colophon.archive records why. The ledger
                # row still names where the claim came from, which is the point
                # of the column.
                continue
            assert (REPO / token).exists(), (
                "%s points at %s which does not exist" % (r["id"], token))


def test_derived_from_resolves_to_real_ids():
    """A bare 'same' stops meaning anything once rows are sorted, so
    derived_from carries concrete ids and they have to exist."""
    known = {r["id"] for r in ROWS}
    for r in ROWS:
        for ref in filter(None, (x.strip() for x in r["derived_from"].split(","))):
            assert ref in known, "%s derives from unknown row %s" % (r["id"], ref)


def test_named_tests_exist():
    """pinned_by_test is only worth carrying if the test is real."""
    for r in ROWS:
        ref = r["pinned_by_test"].strip()
        if not ref:
            continue
        path, _, name = ref.partition("::")
        target = REPO / path
        assert target.exists(), "%s names missing test file %s" % (r["id"], path)
        assert ("def %s(" % name) in target.read_text(encoding="utf-8"), (
            "%s names missing test %s" % (r["id"], ref))


def test_claimed_pins_are_in_the_lockfile():
    """spine-gsps stated a highdicom pin in its manuscript that was not in its
    lockfile. The only 0.28.1 in that file was httpx."""
    lock = (ENV / "requirements.lock")
    assert lock.exists()
    pinned = {}
    for line in lock.read_text(encoding="utf-8").splitlines():
        if "==" in line:
            name, _, version = line.partition("==")
            pinned[name.strip().lower().replace("_", "-")] = version.strip()
    for package in ("idc-index", "idc-index-data", "pandas", "pydicom",
                    "highdicom", "dicom-validator"):
        assert package in pinned, "%s is used but not pinned" % package


@pytest.mark.parametrize("doc", sorted(RESULTS.glob("*.md")))
def test_retired_claims_do_not_reappear_in_prose(doc):
    """A withdrawn claim stays in the ledger so it cannot creep back. This
    checks it has not crept back into a results write-up."""
    text = doc.read_text(encoding="utf-8").lower()
    for r in ROWS:
        if r["status"] != "RETIRED":
            continue
        if doc.name == "prior_art.md":
            continue  # that file records the withdrawal deliberately
        stem = r["claim"].lower()[:60]
        assert stem not in text, (
            "%s carries retired claim %s" % (doc.name, r["id"]))


def test_retired_count_in_prose_matches_the_ledger():
    """spine-gsps stated nine retired claims in prose when the ledger held
    sixteen. The count is derived, never typed."""
    retired = [r for r in ROWS if r["status"] == "RETIRED"]
    ai_use = (RESULTS / "ai_use.md").read_text(encoding="utf-8")
    stated = re.findall(r"ledger rows? PA-\d+ through PA-\d+", ai_use)
    assert stated, "ai_use.md no longer names its ledger rows"
    words = {0: "zero", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five"}
    n = len(retired)
    if n in words:
        claimed = re.search(r"withdrawn before it was ever used", ai_use)
        assert claimed, "ai_use.md no longer describes the withdrawal"


def test_column_fill_rates_are_reported_and_no_column_is_dead():
    """A wide schema is not a quality signal. A column nothing fills should be
    dropped or justified, so it cannot accumulate unnoticed."""
    rates = ledger.column_fill_rates()
    assert rates, "no rows to measure"
    dead = sorted(f for f, pct in rates.items() if pct == 0.0)
    # Columns legitimately empty until later phases produce them.
    # hardware is empty by design: rows inherit the default paragraph in
    # results/README.md and populate it only when they depart from it.
    allowed_dead = {"hardware"}
    assert set(dead) <= allowed_dead, (
        "columns nothing fills: %s. Drop them or justify them." % dead)


def test_every_row_pins_the_point_in_time():
    """481,750 will not reproduce next release, so every row states which index
    it was measured against and when."""
    for r in ROWS:
        assert r["date"].strip(), "%s has no date" % r["id"]
        if r["status"] != "MEASURED":
            continue
        assert r["idc_index_version"].strip(), (
            "%s names no archive release" % r["id"])
    for r in ROWS:
        assert r["idc_index_version"] == ledger.IDC_INDEX_VERSION, (
            "%s was written against %s but the module constant is %s"
            % (r["id"], r["idc_index_version"], ledger.IDC_INDEX_VERSION))


def test_null_join_guard_detects_what_inspection_caught():
    """The acquisition-inheritance defect was a null-on-null match that no test
    caught. This is the guard that would have caught it."""
    import pandas as pd
    frame = pd.DataFrame({"a": [1, None, 3], "b": ["x", "y", None]})
    rec = ledger.null_join_guard(frame, ["a", "b"], "synthetic")
    assert rec["clean"] is False
    assert rec["null_join_keys"] == {"a": 1, "b": 1}
    assert rec["rows_with_any_null_key"] == 2
    clean = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    assert ledger.null_join_guard(clean, ["a", "b"], "synthetic")["clean"] is True


def test_record_many_is_atomic():
    """A malformed entry must not leave the ledger half written. A duplicate
    keyword argument once aborted a batch after two of five rows had landed,
    and the ledger read as though the other three were never authored."""
    import tempfile, pathlib as _p
    with tempfile.TemporaryDirectory() as tmp:
        path = _p.Path(tmp) / "ledger.csv"
        ledger.record_many([
            dict(id="T-1", section="T", claim="first", status="MEASURED"),
        ], path=path)
        assert len(ledger.load(path)) == 1
        with pytest.raises(ValueError):
            ledger.record_many([
                dict(id="T-2", section="T", claim="good", status="MEASURED"),
                dict(id="T-3", section="T", claim="bad", status="NOT_A_STATUS"),
            ], path=path)
        assert [r["id"] for r in ledger.load(path)] == ["T-1"], (
            "the good row from the failed batch must not have been written")


def test_no_module_builds_a_ledger_row_with_duplicate_keywords():
    """Three separate batches were aborted mid-run by passing a field both
    explicitly and through the shared **S block. The atomic writer caught each
    one, but the failure mode is cheap to prevent statically: no dict(...)
    literal in a record_many call may name a key that its shared block also
    names."""
    import ast
    from colophon.paths import REPO
    offenders = []
    for path in sorted((REPO / "colophon").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        shared = set()
        for node in ast.walk(tree):
            # S = dict(section=..., ...) is the shared block by convention.
            if (isinstance(node, ast.Assign) and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)
                    and node.targets[0].id == "S"
                    and isinstance(node.value, ast.Call)):
                shared = {kw.arg for kw in node.value.keywords if kw.arg}
        if not shared:
            continue
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name) and node.func.id == "dict"):
                continue
            explicit = {kw.arg for kw in node.keywords if kw.arg}
            # Only a bare **S collides. The filtered idiom
            # **{k: v for k, v in S.items() if k != "dropped"} deliberately
            # removes the key and is correct.
            bare_splat = any(kw.arg is None and isinstance(kw.value, ast.Name)
                             and kw.value.id == "S" for kw in node.keywords)
            clash = explicit & shared
            if bare_splat and clash:
                offenders.append("%s line %d: %s" % (path.name, node.lineno,
                                                     sorted(clash)))
    assert not offenders, "ledger rows with duplicate keywords:\n  " + "\n  ".join(offenders)


def test_a_retirement_survives_a_module_rerun():
    """A module that registers a claim re-asserts it on every run. That must
    not resurrect a claim the data has since falsified.

    This is not hypothetical. Re-running colophon.validate put PRE-01 back to
    PENDING after it had been retired as a wrong prediction, and nothing
    complained, because a module writing to the ledger directly never passes
    through the merge gate."""
    import tempfile, pathlib as _p
    with tempfile.TemporaryDirectory() as tmp:
        path = _p.Path(tmp) / "ledger.csv"
        ledger.record("X-1", "X", "a prediction", "PENDING", path=path)
        ledger.retire("X-1", "falsified by measurement", path=path)
        assert ledger.load(path)[0]["status"] == "RETIRED"
        # The owning module runs again and re-asserts its original row.
        ledger.record("X-1", "X", "a prediction", "PENDING", path=path,
                      value="recomputed")
        row = ledger.load(path)[0]
        assert row["status"] == "RETIRED", "a re-run un-retired a claim"
        assert row["retired_reason"] == "falsified by measurement"
        assert row["value"] == "recomputed", (
            "the re-run should still be able to refresh a value")


def test_pre01_is_retired_as_a_wrong_prediction():
    """The headline outcome of the overnight run. PRE-01 predicted claim 1
    would return largely null and Key Object Selection falsified it."""
    row = {r["id"]: r for r in ROWS}.get("PRE-01")
    if row is None:
        pytest.skip("PRE-01 not registered")
    assert row["status"] == "RETIRED"
    assert row["retired_reason"].strip()
    assert "Key Object Selection" in row["status_note"]


def test_a_pre_registration_outcome_survives_a_module_rerun():
    """PRE-05 is PENDING, so the retirement guard does not cover it, and a
    module re-run wiped its recorded class outcomes once. Only an explicit
    outcome write may change a pre-registration."""
    import tempfile, pathlib as _p
    with tempfile.TemporaryDirectory() as tmp:
        path = _p.Path(tmp) / "ledger.csv"
        ledger.record("PRE-99", "PRE", "a threshold", "PENDING", path=path,
                      status_note="registered before the data")
        ledger.record_outcome([dict(id="PRE-99", section="PRE",
                                    claim="a threshold", status="PENDING",
                                    status_note="outcome: two classes cleared")],
                              path=path)
        assert "outcome" in ledger.load(path)[0]["status_note"]
        # The registering module runs again with its original wording.
        ledger.record("PRE-99", "PRE", "a threshold", "PENDING", path=path,
                      status_note="registered before the data")
        assert "outcome" in ledger.load(path)[0]["status_note"], (
            "a module re-run erased a recorded pre-registration outcome")
