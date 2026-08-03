"""Guards on the Results section of the manuscript.

`tests/test_census.py::test_no_partial_class_is_reported` keeps a partial class
out of `results/phase2_census.md`. The manuscript needs the same rule and one
more besides, because a class can be complete in the census and still have no
adjudication behind it, and a rate with no floor beneath it is not a number.

Completeness is recomputed here from the census state files rather than read out
of a write-up. A census may be appending to `_cache/census/records.jsonl` while
this runs, so the reader skips an unparseable line and counts it rather than
raising. The file is never written to.
"""
from __future__ import annotations

import csv
import json
import re

import pytest

from colophon import census
from colophon.paths import REPO, LEDGER, RESULTS

DOC = RESULTS / "manuscript" / "results.md"
PHASE2 = RESULTS / "phase2"
PENDING_DIR = RESULTS / "pending_ledger"
# colophon.merge_ledger moves a track file into merged/ once it has been folded
# into the ledger, so the row set lives in one of two places.
PENDING_CANDIDATES = (PENDING_DIR / "track_f4.json",
                      PENDING_DIR / "merged" / "track_f4.json")
PRE01_OUTCOME = PENDING_DIR / "merged" / "zz_pre01_outcome.json"

# The rate-bearing region of the document. Sections 3.1 and 3.5 name classes
# that carry no rate, with their coverage counts, which is required rather than
# forbidden.
CONFORMANCE_HEADING = "## 3.5 Claim 1"
LIMITATIONS_HEADING = "## 3.6 Limitations"

RATE = re.compile(r"percent|%")


def _doc() -> str:
    if not DOC.exists():
        pytest.skip("no Results draft yet")
    return DOC.read_text(encoding="utf-8")


def _rate_sections(text: str) -> str:
    assert CONFORMANCE_HEADING in text, "the conformance section moved or was renamed"
    assert LIMITATIONS_HEADING in text, "the limitations section moved or was renamed"
    return text.split(CONFORMANCE_HEADING)[1].split(LIMITATIONS_HEADING)[0]


def _pending_path():
    for path in PENDING_CANDIDATES:
        if path.exists():
            return path
    raise AssertionError(
        "track_f4.json is in neither %s" % " nor ".join(str(p) for p in PENDING_CANDIDATES))


def _recorded_series() -> tuple[dict[str, set[str]], int, int]:
    """Distinct series per SOP class in the census records, read defensively.

    Returns the per-class series sets, the number of lines seen and the number
    skipped as unparseable.
    """
    if not census.RECORDS.exists():
        pytest.skip("no census records file")
    per_class: dict[str, set[str]] = {}
    seen = skipped = 0
    with census.RECORDS.open(encoding="utf-8") as fh:
        for line in fh:
            seen += 1
            line = line.strip()
            if not line:
                skipped += 1
                continue
            try:
                rec = json.loads(line)
                sop = rec["sop_class_name"]
                uid = rec["series_instance_uid"]
            except Exception:
                skipped += 1
                continue
            per_class.setdefault(sop, set()).add(uid)
    return per_class, seen, skipped


def _complete_classes() -> tuple[set[str], dict[str, tuple[int, int]]]:
    totals = census.class_totals()
    recorded, _, _ = _recorded_series()
    counts = {name: (len(recorded.get(name, ())), int(total))
              for name, total in totals.items()}
    complete = {name for name, (got, total) in counts.items()
                if total > 0 and got >= total}
    return complete, counts


def _adjudicated_classes() -> set[str]:
    """SOP classes with at least one adjudicated message class on disk.

    Two shapes exist. `adjudication_rwv_kos.csv` carries a `sop_class_name`
    column because it covers two classes; the single-class files do not, so
    their class is taken from the filename stem they were generated for.
    """
    by_stem = {
        "adjudication_comprehensive_sr.csv": "Comprehensive SR Storage",
        "adjudication_gsps.csv": "Grayscale Softcopy Presentation State Storage",
        "adjudication_parametric_map.csv": "Parametric Map Storage",
        "adjudication_comprehensive_3d_sr.csv": "Comprehensive 3D SR Storage",
        "adjudication_rwv_kos.csv": None,  # carries sop_class_name itself
    }
    found: set[str] = set()
    for path in sorted(PHASE2.glob("adjudication_*.csv")):
        with path.open(newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        if not rows:
            continue
        if "sop_class_name" in rows[0]:
            found |= {r["sop_class_name"] for r in rows if r["sop_class_name"]}
        elif path.name in by_stem:
            if by_stem[path.name] is not None:
                found.add(by_stem[path.name])
        else:
            raise AssertionError(
                "%s has no sop_class_name column and no registered class. Add "
                "it to by_stem rather than letting the file go unattributed."
                % path.name)
    return found


def _reportable() -> set[str]:
    return _complete_classes()[0] & _adjudicated_classes()


# --- the rule ----------------------------------------------------------------
def test_no_partial_class_carries_a_rate():
    """A class the census has not finished must appear nowhere near a rate.

    The same rule as ledger P2C-01 and `test_no_partial_class_is_reported`,
    applied to the manuscript. Naming the class with its coverage counts is
    allowed and required; putting a percentage on the same line is not.
    """
    text = _doc()
    complete, counts = _complete_classes()
    partial = [n for n in counts if n not in complete]
    assert partial, "expected at least one class still in flight"
    for name in partial:
        got, total = counts[name]
        for n, line in enumerate(text.splitlines(), 1):
            if name in line and RATE.search(line):
                raise AssertionError(
                    "results.md:%d quotes a rate beside %s, which is only %d of "
                    "%d series recorded" % (n, name, got, total))


def test_partial_classes_are_absent_from_the_rate_sections():
    """Not even a bare count, once the document starts reporting rates."""
    body = _rate_sections(_doc())
    complete, counts = _complete_classes()
    for name in counts:
        if name in complete:
            continue
        assert name not in body, (
            "%s is not complete in the census but appears in the conformance "
            "and disagreement sections" % name)


def test_unadjudicated_class_carries_no_rate():
    """Ledger F4-02. Complete is one gate, adjudicated is the other.

    A class with no adjudication has no FLOOR determination, so it has no floor
    to quote a rate against, and the project rule is that a rate without its
    floor is not a number.
    """
    text = _doc()
    body = _rate_sections(text)
    complete, _ = _complete_classes()
    unadjudicated = complete - _adjudicated_classes()
    for name in unadjudicated:
        for n, line in enumerate(text.splitlines(), 1):
            if name in line and RATE.search(line):
                raise AssertionError(
                    "results.md:%d quotes a rate beside %s, which is complete "
                    "in the census but has no adjudication" % (n, name))
        assert name not in body, (
            "%s has no adjudication and must not appear in the conformance or "
            "disagreement sections" % name)


def test_every_class_reported_with_a_rate_is_complete_and_adjudicated():
    """The positive form, so the guard cannot pass by the document going empty."""
    body = _rate_sections(_doc())
    reportable = _reportable()
    assert reportable, "no class is both complete and adjudicated"
    named = {n for n in census.CLASS_ORDER if n in body}
    # One table names classes without the trailing word Storage.
    named |= {n for n in census.CLASS_ORDER
              if n.endswith(" Storage") and n[:-len(" Storage")] in body}
    assert named, "the conformance section names no SOP class"
    assert named <= reportable, (
        "the conformance section reports %s, which is not both complete and "
        "adjudicated" % sorted(named - reportable))
    assert census.EXCLUDED not in body, (
        "Segmentation Storage is outside the census scope and carries no rate")


# --- backing and house style --------------------------------------------------
def _backing() -> str:
    parts = [LEDGER.read_text(encoding="utf-8")]
    for path in PENDING_CANDIDATES:
        if path.exists():
            parts.append(path.read_text(encoding="utf-8"))
    for path in sorted(PHASE2.glob("*.csv")):
        parts.append(path.read_text(encoding="utf-8"))
    for path in sorted(PHASE2.glob("net_rates_*.md")):
        parts.append(path.read_text(encoding="utf-8"))
    for name in ("environment.json", "standards.json", "floor_overlap.md",
                 "phase1_variants.md", "claim3_provenance.md",
                 "phase2_census.md"):
        path = RESULTS / name
        if path.exists():
            parts.append(path.read_text(encoding="utf-8"))
    # The Type re-verification artefacts. The manuscript and the references
    # quote the standard's own byte counts and table numbers out of these, and
    # they are as much a source as the ledger is.
    typecheck = RESULTS / "typecheck"
    if typecheck.exists():
        for path in sorted(typecheck.iterdir()):
            if path.suffix in (".md", ".csv", ".json"):
                parts.append(path.read_text(encoding="utf-8"))
    # The pinned DICOM status rows behind every CP and Supplement citation.
    status = RESULTS / "cp" / "dicom_status_rows.json"
    if status.exists():
        parts.append(status.read_text(encoding="utf-8"))
    # The submission manifest and the release snapshot. Both carry numbers the
    # package computes about itself, the word count and the tracked-file count
    # among them, and a number computed into an artefact is backed by it.
    for rel in ("submission/manifest.json", "release/snapshot.json",
                "figures/reproducibility.json", "claim3/disclosure_search.json"):
        path = RESULTS / rel
        if path.exists():
            parts.append(path.read_text(encoding="utf-8"))
    for path in sorted((RESULTS / "manuscript").glob("table*")):
        parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)


def _is_backed(token: str, backing: str) -> bool:
    """A ledger row or a CSV writes 2118 where prose writes 2,118."""
    return token in backing or token.replace(",", "") in backing


TAG = re.compile(r"\(\d{4},[0-9A-Fa-f]{4}\)")
VERSION = re.compile(r"\b\d+\.\d+\.\d+\b")
UID = re.compile(r"\b\d+(?:\.\d+){3,}\b")
DATESTAMP = re.compile(r"\b\d{8,}\b")
ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
THOUSANDS = re.compile(r"\b\d{1,3}(?:,\d{3})+\b")
DECIMAL_UNIT = re.compile(r"\b(\d+\.\d+)\s*(?:percent|TB|GB|MB)\b")


def test_every_number_in_the_results_draft_is_backed():
    """Ledger F4-03. The same control as tests/test_prose.py, widened.

    results/manuscript/ is outside the glob of tests/test_prose.py, which reads
    results/*.md only, so this is where the manuscript's numbers are checked.
    Backing is widened beyond the ledger to the results CSVs and the adjudication
    write-ups, because a Results section quotes per-class tables the ledger
    summarises rather than reproduces.
    """
    text = _doc()
    for pattern in (TAG, UID, VERSION, DATESTAMP, ISO_DATE):
        text = pattern.sub(" ", text)
    backing = _backing()
    quoted = set(THOUSANDS.findall(text)) | set(DECIMAL_UNIT.findall(text))
    unbacked = sorted(q for q in quoted if not _is_backed(q, backing))
    assert not unbacked, (
        "results.md quotes %s, which nothing in results/ carries. Either the "
        "number is stale or the claim was never recorded."
        % ", ".join(unbacked))


def test_the_draft_cites_the_retired_prediction_and_the_threshold():
    """PRE-01 and PRE-05 carry their own outcomes and are reported, not restated.

    PRE-01 is RETIRED as a wrong prediction. A Results section that reports a
    100 percent net rate on Key Object Selection and does not say so is
    laundering the prediction.

    The retirement is looked for in the live ledger first and in the merged
    outcome file second. Concurrent tracks merge into results/ledger.csv while
    this repository is being written, and a row that reverts is a fact to report
    rather than a reason for the manuscript to soften.
    """
    text = _doc()
    assert "PRE-01" in text and "retired" in text.lower()
    assert "PRE-05" in text

    with LEDGER.open(newline="", encoding="utf-8") as fh:
        rows = {r["id"]: r for r in csv.DictReader(fh)}
    if rows.get("PRE-01", {}).get("status") == "RETIRED":
        return
    assert PRE01_OUTCOME.exists(), (
        "PRE-01 is %s in results/ledger.csv and no merged outcome file carries "
        "the retirement, so the Results wording has nothing behind it"
        % rows.get("PRE-01", {}).get("status"))
    outcome = {r["id"]: r for r in json.loads(PRE01_OUTCOME.read_text(encoding="utf-8"))}
    assert outcome["PRE-01"]["status"] == "RETIRED", (
        "neither results/ledger.csv nor %s retires PRE-01" % PRE01_OUTCOME.name)
    pytest.skip(
        "PRE-01 reads %s in results/ledger.csv but RETIRED in %s. A concurrent "
        "merge reverted the row. The Results wording follows the outcome file "
        "and the ledger needs reconciling before submission."
        % (rows.get("PRE-01", {}).get("status"), PRE01_OUTCOME.name))


def test_house_style():
    text = _doc()
    assert chr(0x2014) not in text, "results.md contains an em-dash"
    for token in ("A" + "ycan", "AY" + "CAN", "Ay" + "Can"):
        assert token not in text


def test_the_pending_rows_match_the_ledger_schema():
    """A proposed row that cannot be merged is not a record of anything."""
    from colophon import ledger
    path = _pending_path()
    rows = json.loads(path.read_text(encoding="utf-8"))
    assert rows, "track_f4.json is empty"
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids)), "duplicate id in track_f4.json"
    for row in rows:
        assert set(row) == set(ledger.FIELDS), (
            "%s keys do not match colophon.ledger.FIELDS: missing %s, extra %s"
            % (row.get("id"), sorted(set(ledger.FIELDS) - set(row)),
               sorted(set(row) - set(ledger.FIELDS))))
        assert row["status"] in ledger.VALID_STATUS
        assert row["id"].startswith("F4-")
        value = (row["value"] or "").lower()
        if row["status"] == "MEASURED" and ("percent" in value or " of " in value):
            assert row["floor"].strip(), (
                "%s quotes a rate and names no floor" % row["id"])

    existing = {r["id"]: r for r in ledger.load()}
    if path.parent.name == "merged":
        missing = [i for i in ids if i not in existing]
        assert not missing, (
            "track_f4.json is filed as merged but %s never reached the ledger"
            % missing)
        for row in rows:
            assert existing[row["id"]]["value"] == row["value"], (
                "%s was merged with a different value than it was proposed with"
                % row["id"])
    else:
        # A track may re-propose its own rows, which is how a self-referential
        # count is corrected after the first merge changed it. It may never
        # replace a row belonging to another track.
        clash = sorted(i for i in set(ids) & set(existing) if not i.startswith("F4-"))
        assert not clash, (
            "track_f4.json would replace ledger rows this track does not own: %s"
            % clash)


def test_no_pre_row_is_proposed():
    """This track reads PRE-01 and PRE-05 and edits neither.

    colophon.merge_ledger replaces a row whole and resolves duplicate ids last
    file wins, so a PRE-* row proposed here would silently discard the
    orchestrator's consolidated one.
    """
    rows = json.loads(_pending_path().read_text(encoding="utf-8"))
    assert not [r for r in rows if r["id"].startswith("PRE-")]


def test_the_guard_can_fail():
    """A guard that cannot fail is not a guard."""
    complete, counts = _complete_classes()
    assert set(counts) - complete, (
        "every class is complete, so the partial-class guards are vacuous and "
        "the Results section needs re-reading rather than re-running")
    assert RATE.search("net rate 100.00 percent")
    assert not RATE.search("13,741 of 19,358 series")


def test_the_records_read_is_defensive_and_reports_what_it_skipped():
    """Ledger F4-01. A silent skip makes a truncated read look complete."""
    _, seen, skipped = _recorded_series()
    assert seen > 0
    assert skipped >= 0
    if skipped:
        pytest.skip(
            "%d of %d lines of records.jsonl were unparseable at this read; "
            "the count belongs in the write-up, not in a silent pass"
            % (skipped, seen))


# The re-spined manuscript carries figures in Methods and in the figure list as
# well as in Results, and the rule is the same for all three: a number in the
# text with no row behind it fails the build.
#
# front_matter.md and references.md are inside the rule for the same reason. The
# front matter quotes the object count in its title and the reference list quotes
# tool versions and byte counts, and both are exactly the kind of number that
# goes stale after the measurement it came from moves.
MANUSCRIPT_DOCS = ("methods.md", "results.md", "figures.md", "tables.md",
                   "introduction.md", "discussion.md", "abstract.md",
                   "front_matter.md", "references.md")

# The drafted Correction Proposal quotes the census as evidence, so its numbers
# are under the same rule. It lives outside results/manuscript/ because it is not
# part of the manuscript and is filed, if at all, separately.
CP_DOCS = ("cp_segmentation_algorithm_identification.md", "README.md")


@pytest.mark.parametrize("name", MANUSCRIPT_DOCS)
def test_every_number_in_the_manuscript_is_backed(name):
    """Widened from results.md to every manuscript document.

    Methods carries the deviation bounds, the reliability figures and the
    declared grading sensitivity, and those are exactly the numbers a reader
    checks first. The figure list carries the counts each figure must show, so
    a figure cannot be specified around a number nothing measured.
    """
    path = RESULTS / "manuscript" / name
    if not path.exists():
        pytest.skip("%s not written yet" % name)
    text = path.read_text(encoding="utf-8")
    for pattern in (TAG, UID, VERSION, DATESTAMP, ISO_DATE):
        text = pattern.sub(" ", text)
    backing = _backing()
    quoted = set(THOUSANDS.findall(text)) | set(DECIMAL_UNIT.findall(text))
    unbacked = sorted(q for q in quoted if not _is_backed(q, backing))
    assert not unbacked, (
        "%s quotes %s, which nothing in results/ carries. Either the number is "
        "stale or the claim was never recorded." % (name, ", ".join(unbacked)))


@pytest.mark.parametrize("name", CP_DOCS)
def test_every_number_in_the_correction_proposal_is_backed(name):
    """The proposal cites the census as evidence. A number in it with no ledger
    row behind it would be advocacy dressed as measurement."""
    path = RESULTS / "cp" / name
    if not path.exists():
        pytest.skip("%s not written yet" % name)
    text = path.read_text(encoding="utf-8")
    for pattern in (TAG, UID, VERSION, DATESTAMP, ISO_DATE):
        text = pattern.sub(" ", text)
    backing = _backing()
    quoted = set(THOUSANDS.findall(text)) | set(DECIMAL_UNIT.findall(text))
    unbacked = sorted(q for q in quoted if not _is_backed(q, backing))
    assert not unbacked, (
        "%s quotes %s, which nothing in results/ carries" % (name, ", ".join(unbacked)))


def test_the_correction_proposal_is_not_filed_until_it_says_so():
    """The manuscript states in three places that the proposal is drafted and
    not filed. If that ever stops being true the three statements move together,
    and this is what makes them move together."""
    cp = RESULTS / "cp" / "cp_segmentation_algorithm_identification.md"
    if not cp.exists():
        pytest.skip("no correction proposal draft")
    draft = cp.read_text(encoding="utf-8")
    readme = (RESULTS / "cp" / "README.md").read_text(encoding="utf-8")
    unfiled = "has not been filed" in draft or "not filed" in readme
    for name in ("abstract.md", "discussion.md"):
        text = (RESULTS / "manuscript" / name).read_text(encoding="utf-8")
        if "not been filed" in text or "not filed" in text:
            assert unfiled, (
                "%s says the proposal is not filed and results/cp/ no longer "
                "does" % name)
    # Submitter, date and Log Summary stay as fields until the author fills
    # them, and a filled field with an unfiled proposal is a contradiction.
    if unfiled:
        assert "[FIELD:" in draft, (
            "the proposal is unfiled but carries no unfilled field")


def test_the_manuscript_scopes_object_weighted_rates_in_the_same_sentence():
    """Enhanced SR is excluded from every object-weighted rate. The exclusion
    has to travel with the figure, not sit in a footnote a quotation drops."""
    path = RESULTS / "manuscript" / "results.md"
    if not path.exists():
        pytest.skip("no Results draft yet")
    text = path.read_text(encoding="utf-8")
    assert "excluding Enhanced SR" in text
    assert "35,161 of 262,883" in text, (
        "the excluded count must be named where the exclusion is declared")
    # The lead result is stated over the complete unit as well as the object
    # unit. The cell counts are read from the ladder rather than hard-coded
    # here: they moved from 21 of 31 to 25 of 36 when the null-analysis-result
    # objects that pandas had been dropping were given rows (A2, C3T-03).
    import pandas as pd
    ladder = pd.read_csv(RESULTS / "claim3" / "t33_recoverability_ladder.csv")
    cells = len(ladder)
    none = int((ladder["first_level_identity_appears"].astype(str) == "none").sum())
    assert "%d analysis-result" % cells in text, (
        "the ladder has %d cells and the Results section does not say so" % cells)
    assert str(none) in text


def test_the_manuscript_does_not_claim_a_stable_residue_at_every_rung():
    """Ledger B-10 records the residue as 1 at eight dciodvfy rungs and 2 at V9.
    A claim of stability at every rung would overstate it."""
    path = RESULTS / "manuscript" / "results.md"
    if not path.exists():
        pytest.skip("no Results draft yet")
    text = path.read_text(encoding="utf-8")
    if "residue" in text:
        assert "V9" in text, "the one rung that departs must be named"
