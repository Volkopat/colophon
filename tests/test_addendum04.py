"""The fourth addendum's six items, asserted.

Each item ended in either a computed number or an explicit statement that
something is not computed. This is where those stop being true quietly.
"""
from __future__ import annotations

import json
import re

import pytest

from colophon import absence, disclosure, figures, release, submission, tokens
from colophon.paths import RESULTS, REPO

# The public archive ships the harness that produces the measurements, not the
# manuscript. `results/manuscript/` narrative sources and `results/submission/`
# are excluded from it, so on a clone of the archive there is no package to
# assert against and these tests skip with a reason rather than erroring at
# import. They run in full in the working repository, which is where the
# submission is actually built. The ledger rows that name tests in this file
# stay valid either way, because the test still exists.
if not (RESULTS / "submission" / "fields.json").exists():
    pytest.skip("the assembled submission package is not in this checkout: "
                "fields.json holds author-held values that the archive does "
                "not carry, so the package cannot be rebuilt here; see README, "
                "'What this archive does not contain'",
                allow_module_level=True)



# --- item 1, the checklist ------------------------------------------------------
def test_the_figure_set_reproduces_across_processes():
    """Row 25 used to assert a mechanism. It reports a diff now, and the diff
    has to be clean in every format rather than in the one that was checked."""
    path = RESULTS / "figures" / "reproducibility.json"
    if not path.exists():
        pytest.skip("run python -m colophon.reproducibility")
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["ran"], report.get("error", "")
    for fmt, rec in report["formats"].items():
        assert rec["files"] > 0, "no %s files were compared" % fmt
        assert rec["reproducible"], (
            "%s: %d of %d identical, differing %s"
            % (fmt, rec["identical"], rec["files"],
               [d["file"] for d in report["differing_files"]
                if d["format"] == fmt]))


def test_no_automatic_checklist_row_states_a_reason_instead_of_a_count():
    """The acceptance test the addendum names: the header sentence is true.

    A detail that carries no digit and no explicit match is an assertion. The
    check is crude on purpose, because the failure mode it exists for is prose
    that sounds like a measurement.
    """
    text = (submission.OUT / "07_checklist.md").read_text(encoding="utf-8")
    first = text.split("## Not checkable here")[0]
    rows = [l for l in first.splitlines()
            if l.startswith("|") and l.count("|") >= 4
            and not l.startswith("| requirement")
            and set(l.strip()) - set("|- ")]
    assert len(rows) >= 15, "the automatic table has shrunk to %d rows" % len(rows)
    for row in rows:
        cells = [c.strip() for c in row.strip("|").split("|")]
        detail = cells[2] if len(cells) > 2 else ""
        assert re.search(r"\d", detail), (
            "this row's detail carries no computed value:\n  %s" % row[:200])
        assert cells[1] in ("yes", "**NO**"), (
            "a row in the computed table has value %r, which is not a verdict"
            % cells[1])


def test_the_checklist_reports_no_unmet_requirement():
    text = (submission.OUT / "07_checklist.md").read_text(encoding="utf-8")
    assert "**NO**" not in text, "\n".join(
        l for l in text.splitlines() if "**NO**" in l)


# --- item 2, the disclosure -----------------------------------------------------
def test_the_company_search_reports_what_it_could_not_search():
    """Five of the seven attributes are captured by this study. A search that
    reported `seven` would be the assertion it replaced."""
    path = RESULTS / "claim3" / "disclosure_search.json"
    if not path.exists():
        pytest.skip("run python -m colophon.disclosure")
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["objects_searched"] >= 35107
    assert report["matching_objects"] == 0, report["values_matched"]
    missing = {a["name"] for a in report["attributes_not_captured_by_this_study"]}
    assert missing == {"InstitutionName", "StationName"}, missing
    assert "5 of the 7" in disclosure.sentence(report)


def test_the_disclosure_is_three_separable_claims():
    page = " ".join((submission.OUT / "01_title_page.md")
                    .read_text(encoding="utf-8").split())
    for marker in ("Where this study was done. Stated by the author.",
                   "The employment window.",
                   "Whether any object in the measured set came from that "
                   "company. Measured."):
        assert marker in page, marker
    assert "was not carried out at aycan Medical Systems LLC" in page
    letter = (submission.OUT / "00_cover_letter.md").read_text(encoding="utf-8")
    assert "**Measured:**" in letter and "**Stated:**" in letter


# --- item 3, the absence sweep --------------------------------------------------
def test_the_absence_sweep_runs_and_reports_rather_than_edits():
    report = absence.sweep()
    assert report["sentences_scanned"] > 500
    assert report["claims_found"] > 0
    assert set(report["by_verdict"]) <= {"backed", "adjacent", "unbacked"}
    doc = RESULTS / "manuscript" / "absence_claims.md"
    assert doc.exists(), "run python -m colophon.absence"
    text = doc.read_text(encoding="utf-8")
    assert "reports and changes nothing" in text
    assert text.count("|") > report["claims_found"]


# --- item 4, the fields ---------------------------------------------------------
def test_a_final_package_refuses_while_a_field_is_empty(monkeypatch):
    """The refusal must be demonstrable when every field is filled.

    This used to skip once nothing was unfilled, which is the moment the package
    is ready to ship and therefore the moment the guard most needs to be known
    to work. A test that goes quiet exactly when the thing it guards is about to
    happen is not evidence of anything. It empties one field in a copy of the
    store instead, so the refusal is exercised on a real build every run.
    """
    real = tokens.load_fields()
    assert real, "there is no field store to empty"
    victim = sorted(real)[0]
    hobbled = {k: dict(v) for k, v in real.items()}
    hobbled[victim]["value"] = ""
    monkeypatch.setattr(tokens, "load_fields", lambda: hobbled)

    assert tokens.unfilled() == [victim]
    with pytest.raises(tokens.UnfilledField):
        submission.build(final=True)


def test_the_refusal_is_not_an_artefact_of_the_monkeypatch():
    """The real store is intact and a real final build is permitted."""
    assert tokens.unfilled() == [] or submission.build(final=False)


def test_a_draft_package_renders_every_unfilled_field_visibly():
    manifest = submission.build(final=False)
    state = manifest["state"]
    assert state["fields_total"] >= 12
    assert state["surviving_markers_in_bytes"] >= len(state["fields_unfilled"]), (
        "a field is unfilled and leaves no visible marker, which is how one "
        "ships")


def test_every_placeholder_is_a_key_in_fields_json():
    """No file in the package may carry a placeholder that is not a field."""
    fields = set(tokens.load_fields())
    for path in submission.OUT.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        for m in re.finditer(r"\[FIELD ([a-z_]+):", text):
            assert m.group(1) in fields, (
                "%s carries placeholder %r, which is not a key in fields.json"
                % (path.name, m.group(1)))


# --- item 5, the release --------------------------------------------------------
def test_the_release_metadata_exists_and_the_snapshot_is_stated():
    for path in (REPO / "LICENSE", REPO / ".zenodo.json",
                 RESULTS / "release" / "RELEASE_NOTES.md",
                 RESULTS / "release" / "COMMANDS.md"):
        assert path.exists(), path
    state = release.build()
    assert state["tracked"]["dicom_files"] == 0, (
        "a DICOM object is tracked, so it would be redistributed by the tag")
    notes = (RESULTS / "release" / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    assert "deliberately excludes" in notes
    assert "CC BY-NC" in notes, (
        "the reason the derived records are excluded is the licence mix, and "
        "the notes have to say so")


def test_the_release_touches_nothing_remote():
    """It may print `git push`. It may not run one.

    The distinction is the whole point of the item: the module prepares and the
    author acts, so the check is on what it executes rather than on what it
    documents.
    """
    import ast
    source = (REPO / "colophon" / "release.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    executed = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = ast.unparse(node.func)
        if name in ("subprocess.run", "subprocess.call",
                    "subprocess.check_output", "os.system") or                 name.startswith("requests."):
            executed.append((name, ast.unparse(node.args[0])
                             if node.args else ""))
    for name, first in executed:
        assert name.startswith("subprocess."), name
        assert "ls-files" in first, (
            "release.py executes %s(%s); the only command it may run is a "
            "read-only one" % (name, first))
    assert executed, "the snapshot is measured, so something must run"


# --- item 6, the two decisions --------------------------------------------------
def test_the_correction_proposal_status_has_one_source_and_three_states():
    assert set(tokens.STATES) == {"drafted_not_filed", "filed_awaiting_number",
                                  "assigned"}
    status = tokens.cp_status()
    assert status["state"] in tokens.STATES
    assert status.get("decision"), "the decision is recorded with its reason"
    # Every state renders, so filing does not discover a broken template.
    import copy
    for state in tokens.STATES:
        probe = copy.deepcopy(status)
        probe.update({"state": state, "filed_on": "2026-09-01",
                      "number": "CP-9999", "status": "Assigned"})
        path = tokens.CP_STATUS
        original = path.read_text(encoding="utf-8")
        try:
            path.write_text(json.dumps(probe), encoding="utf-8")
            assert tokens.cp_sentence()
            assert tokens.cp_sentence(short=True)
        finally:
            path.write_text(original, encoding="utf-8")


def test_the_manuscript_never_types_the_proposal_status():
    """Three passages used to say it. They read from the one value now."""
    for name in ("abstract.md", "discussion.md"):
        text = (RESULTS / "manuscript" / name).read_text(encoding="utf-8")
        assert "{{CP_STATUS" in text, "%s does not read the status token" % name
        assert "has not been filed at the time of writing" not in text, (
            "%s still types the status" % name)
    full = (submission.OUT / "02_manuscript_full.md").read_text(encoding="utf-8")
    assert "{{" not in full, "a token survived into the built manuscript"
    assert tokens.cp_sentence() in full
