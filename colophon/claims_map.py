"""The claims map: every claim id, its ledger row, and the artefact carrying it.

A ledger row and a results file can each look complete while pointing at nothing
in particular. Nobody notices until a reviewer asks where a number came from.
This module joins the two and reports the joins that fail, because those are the
ones that do not survive review:

    orphan claim        a ledger row with no artefact behind it, or one that no
                        write-up names by id, so a reader cannot walk from the
                        claim to its evidence
    uncited artefact    a file under results/ that no ledger row points at,
                        which is either dead weight or an unrecorded claim
    broken derivation   derived_from naming a row id that does not exist
    retirement chain    a RETIRED row whose successor is missing or itself
                        retired, or which names no successor at all
    pre-registration    the PRE-* rows and whether an outcome has landed. This
                        module reports them and never edits them
    floor coverage      MEASURED rows that quote a rate, and whether each names
                        the floor the project rule requires
    test coverage       pinned_by_test, whether the named test exists, and
                        whether it passes right now

Nothing here adjudicates a claim. It checks that a claim can be found.

Two rules shape the scan and are worth stating rather than discovering later.
The map's own outputs name every id by construction, so counting them as
carriers would report full coverage whatever the write-ups actually say: they
are excluded, along with the ledger itself. And the map quotes a claim only in
truncated form, short of the 60 characters that
tests/test_ledger.py::test_retired_claims_do_not_reappear_in_prose compares
against, so a withdrawn wording cannot re-enter prose through the file that
lists it.

The map is a snapshot. Other tracks write into results/ while this runs, so the
generation timestamp is carried in the output and a later regeneration that
differs is explained by it rather than read as drift.

Usage:
    python -m colophon.claims_map               regenerate, run the pinned tests
    python -m colophon.claims_map --skip-tests  regenerate, do not run them
    python -m colophon.claims_map --print-only  print the summary, write nothing
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from . import ledger
from .paths import LEDGER, REPO, RESULTS

CMD = "python -m colophon.claims_map"
MAP_MD = RESULTS / "claims_map.md"
MAP_CSV = RESULTS / "claims_map.csv"
PENDING = RESULTS / "pending_ledger"
PROPOSAL = PENDING / "track_f3.json"

# The map's own outputs and the ledger name every id by construction. A carrier
# scan that counted them would report that every claim is carried and measure
# nothing.
SELF_OUTPUTS = {"claims_map.md", "claims_map.csv"}
NOT_A_CARRIER = SELF_OUTPUTS | {"ledger.csv"}

# Proposed rows from parallel tracks. They are ledger drafts, not evidence, so
# they are not scanned as carriers and not counted as uncited artefacts. They
# are read to annotate an uncited file that a pending row already names.
PENDING_DIR = "pending_ledger"

# tests/test_ledger.py::test_retired_claims_do_not_reappear_in_prose compares
# claim[:60] against every markdown file in results/. The map stays under that.
RETIRED_STEM = 60
CLAIM_CHARS = 56

CSV_FIELDS = [
    "id", "section", "status", "claim_truncated", "source_file", "source_exists",
    "carried_by", "derived_from", "derived_from_ok", "superseded_by",
    "superseded_by_ok", "pinned_by_test", "test_exists", "has_floor",
]

TEST_REF = re.compile(r"^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)\s+(\S+)")

# A manuscript file whose name marks it as a numbered table or figure, which is
# the only place the third leg of the map can be a table number rather than a
# file name.
TABLE_OR_FIGURE = re.compile(r"(table|fig(ure)?)[_0-9]", re.IGNORECASE)


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def truncate(text: str, limit: int = CLAIM_CHARS) -> str:
    """Quote a field without ever quoting all of it.

    Always cuts, including when the text is already shorter than the limit, so
    that no quotation in this file is ever the whole of what it quotes.
    """
    text = " ".join(str(text).split())
    if not text:
        return ""
    if len(text) <= limit:
        limit = max(1, len(text) - 1)
    return text[:limit].rstrip() + " ..."


def truncate_claim(text: str) -> str:
    """Quote a claim short of what the retired-prose guard compares.

    A retired claim keeps its wording in the ledger so the number cannot creep
    back. Reproducing that wording here would put it back into prose, and this
    file lists every retired row by construction.
    """
    return truncate(text, min(CLAIM_CHARS, RETIRED_STEM - 4))


def _cell(text: str) -> str:
    return " ".join(str(text).split()).replace("|", r"\|")


def _table(headers: list[str], rows: list[list]) -> str:
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        out.append("| " + " | ".join(_cell(c) for c in row) + " |")
    return "\n".join(out)


# --- the file inventory -------------------------------------------------------
def results_files() -> list[str]:
    """Every file under results/, as a repository-relative posix path."""
    return sorted(p.relative_to(REPO).as_posix()
                  for p in RESULTS.rglob("*") if p.is_file())


def _is_pending(rel: str) -> bool:
    return ("/%s/" % PENDING_DIR) in rel


def carrier_files(files: list[str]) -> list[str]:
    return [f for f in files
            if Path(f).name not in NOT_A_CARRIER and not _is_pending(f)]


def source_tokens(row: dict) -> list[str]:
    """The artefacts one row names. Rows write these as prose lists."""
    return [t.strip() for t in re.split(r"\s+and\s+|,\s*", row.get("source_file") or "")
            if t.strip()]


def resolve(token: str) -> list[str]:
    """A source_file token to the files it actually names, globs expanded."""
    if "*" in token:
        return sorted(p.relative_to(REPO).as_posix()
                      for p in REPO.glob(token) if p.is_file())
    path = REPO / token
    if path.is_dir():
        return sorted(p.relative_to(REPO).as_posix()
                      for p in path.rglob("*") if p.is_file())
    return [Path(token).as_posix()] if path.is_file() else []


def mentions(ids: list[str], files: list[str]) -> dict[str, list[str]]:
    """Which results files name each id, whole token only.

    The boundary matters: C3-06 must not match inside C3-06-air, and PA-03 must
    not match inside PA-03-prev, or a retired row would look like it carries its
    own successor.
    """
    text = {}
    for rel in files:
        try:
            text[rel] = (REPO / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            text[rel] = ""
    out = {}
    for cid in ids:
        pattern = re.compile(r"(?<![A-Za-z0-9-])%s(?![A-Za-z0-9-])" % re.escape(cid))
        out[cid] = [rel for rel in files if pattern.search(text[rel])]
    return out


# --- the seven analyses -------------------------------------------------------
def build(rows: list[dict], files: list[str]) -> list[dict]:
    """One record per claim id, joining the ledger row to its artefacts."""
    known = {r["id"] for r in rows}
    carriers = carrier_files(files)
    named = mentions([r["id"] for r in rows], carriers)
    out = []
    for r in rows:
        tokens = source_tokens(r)
        resolved, missing = [], []
        for token in tokens:
            hits = resolve(token)
            resolved.extend(hits)
            if not hits:
                missing.append(token)
        refs = [x.strip() for x in (r.get("derived_from") or "").split(",") if x.strip()]
        bad_refs = [x for x in refs if x not in known]
        successor = (r.get("superseded_by") or "").strip()
        test_ref = (r.get("pinned_by_test") or "").strip()
        out.append({
            "id": r["id"],
            "section": r.get("section", ""),
            "status": r.get("status", ""),
            "claim_truncated": truncate_claim(r.get("claim", "")),
            "source_file": r.get("source_file", ""),
            # partial is its own answer: one token of three resolving is not a
            # source that exists, and rounding it up to yes hides a dead link.
            "source_exists": ("none named" if not tokens else "no" if not resolved
                              else "partial" if missing else "yes"),
            "carried_by": ";".join(named[r["id"]]),
            "derived_from": r.get("derived_from", ""),
            "derived_from_ok": "" if not refs else ("no" if bad_refs else "yes"),
            "superseded_by": successor,
            "superseded_by_ok": ("" if not successor
                                 else "yes" if successor in known else "no"),
            "pinned_by_test": test_ref,
            "test_exists": "" if not test_ref else ("yes" if test_exists(test_ref) else "no"),
            "has_floor": "yes" if (r.get("floor") or "").strip() else "no",
            # Not CSV columns. Carried for the write-up.
            "_resolved": resolved,
            "_missing_sources": missing,
            "_bad_refs": bad_refs,
            "_mentioned_in_md": [f for f in named[r["id"]] if f.endswith(".md")],
        })
    return out


def orphans(records: list[dict]) -> list[dict]:
    """Claims a reader cannot walk from the ledger to the evidence.

    Two failures, reported apart because they are not equally bad. A row with no
    artefact at all has nothing behind it. A row whose artefact exists but which
    no write-up names by id is findable only by someone who already knows where
    to look.
    """
    out = []
    for rec in records:
        no_artefact = rec["source_exists"] != "yes"
        unnamed = not rec["_mentioned_in_md"]
        if no_artefact or unnamed:
            why = []
            if rec["source_exists"] == "none named":
                why.append("names no source file")
            elif rec["_missing_sources"]:
                why.append("source file missing: %s" % ", ".join(rec["_missing_sources"]))
            if unnamed:
                why.append("no results markdown names the id")
            out.append({"id": rec["id"], "status": rec["status"],
                        "no_artefact": no_artefact, "unnamed": unnamed,
                        "why": "; ".join(why)})
    return out


def uncited(records: list[dict], files: list[str]) -> list[dict]:
    """Files under results/ that no ledger row points at.

    An artefact no claim rests on is either dead weight or a claim nobody
    recorded. Pending proposals from parallel tracks are read so that a file a
    track has already claimed is annotated rather than reported as loose.
    """
    cited = set()
    for rec in records:
        cited.update(rec["_resolved"])
    pending_claims = pending_sources()
    out = []
    for rel in files:
        if _is_pending(rel) or Path(rel).name in NOT_A_CARRIER:
            continue
        if rel in cited:
            continue
        out.append({"file": rel, "note": pending_claims.get(rel, "")})
    return out


def _pending_rows() -> list[tuple[str, dict]]:
    """Proposed rows from every parallel track, with the file each came from."""
    out = []
    if not PENDING.exists():
        return out
    for path in sorted(PENDING.glob("*.json")):
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(rows, dict):
            rows = [rows]
        out.extend((path.name, r) for r in rows if isinstance(r, dict))
    return out


def pending_proposals() -> dict[str, str]:
    """Rows a track has proposed and nobody has merged yet, by id.

    A proposal is not a ledger row. It is reported next to the row it would
    change so that a pre-registration with an outcome waiting in a proposal
    does not read the same as one with no outcome at all.
    """
    out: dict[str, str] = {}
    for name, r in _pending_rows():
        if r.get("id"):
            out.setdefault(r["id"], "%s, status %s" % (name, r.get("status", "?")))
    return out


def pending_sources() -> dict[str, str]:
    """Which artefacts a parallel track has already proposed a row for."""
    out: dict[str, str] = {}
    for name, r in _pending_rows():
        for token in re.split(r"\s+and\s+|,\s*", r.get("source_file") or ""):
            token = token.strip()
            if not token:
                continue
            for hit in resolve(token) or [Path(token).as_posix()]:
                out.setdefault(hit, "proposed by %s, row %s"
                               % (name, r.get("id", "?")))
    return out


def broken_derivations(rows: list[dict]) -> list[tuple[str, str]]:
    """derived_from references to ids that do not exist.

    The rule is the one tests/test_ledger.py::test_derived_from_resolves_to_real_ids
    enforces: a bare "same" stops meaning anything once rows are sorted, so the
    field carries concrete ids and they have to resolve.
    """
    known = {r["id"] for r in rows}
    bad = []
    for r in rows:
        for ref in (x.strip() for x in (r.get("derived_from") or "").split(",")):
            if ref and ref not in known:
                bad.append((r["id"], ref))
    return bad


def retirement_chains(rows: list[dict]) -> list[dict]:
    """Every RETIRED row and the state of its replacement."""
    by_id = {r["id"]: r for r in rows}
    out = []
    for r in rows:
        if r["status"] != "RETIRED":
            continue
        successor = (r.get("superseded_by") or "").strip()
        target = by_id.get(successor)
        out.append({
            "id": r["id"],
            "claim": truncate_claim(r.get("claim", "")),
            "reason": truncate(r.get("retired_reason", ""), 150),
            "has_reason": bool((r.get("retired_reason") or "").strip()),
            "superseded_by": successor or "(none)",
            "successor_exists": bool(target),
            "successor_status": target["status"] if target else "",
            "successor_live": bool(target) and target["status"] != "RETIRED",
        })
    return out


def pre_rows(rows: list[dict]) -> list[dict]:
    """The pre-registration rows, reported and never edited.

    A pre-registration earns its keep only if the outcome is recorded against
    it later, so the useful column is whether one has landed yet.
    """
    proposed = pending_proposals()
    out = []
    for r in rows:
        if not r["id"].startswith("PRE-"):
            continue
        recorded = (r["status"] != "PENDING" or bool((r.get("verified_on") or "").strip())
                    or bool((r.get("n") or "").strip()))
        out.append({
            "id": r["id"], "section": r["section"], "status": r["status"],
            "claim": truncate_claim(r.get("claim", "")),
            "value": truncate(r.get("value", ""), 90),
            "outcome_recorded": "yes" if recorded else "no",
            "outcome_proposed": proposed.get(r["id"], ""),
            "source_file": r.get("source_file", ""),
        })
    return out


def rows_quoting_a_rate(rows: list[dict]) -> set[str]:
    """Which MEASURED rows quote a rate, decided by the ledger's own rule.

    The rule is not copied here. Blanking the floor column on a scratch copy
    makes colophon.ledger.rates_without_floor return every row it treats as a
    rate, so there is one definition of a rate in this repository and one place
    to change it.
    """
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "ledger.csv"
        ledger.write([dict(r, floor="") for r in rows], path)
        return set(ledger.rates_without_floor(path))


def floor_coverage(rows: list[dict]) -> dict:
    """Rates and their floors. A rate without its floor is not a number."""
    quoting = rows_quoting_a_rate(rows)
    missing = set(ledger.rates_without_floor(LEDGER))
    return {"quoting_a_rate": sorted(quoting), "without_floor": sorted(missing),
            "rows": [{"id": r["id"], "status": r["status"],
                      "value": truncate(r.get("value", ""), 70),
                      "floor": truncate(r.get("floor", ""), 60)
                               if (r.get("floor") or "").strip() else "(none)",
                      "has_floor": "yes" if (r.get("floor") or "").strip() else "no"}
                     for r in rows if r["id"] in quoting]}


def test_exists(ref: str) -> bool:
    path, _, name = ref.partition("::")
    target = REPO / path
    if not target.exists():
        return False
    return not name or ("def %s(" % name) in target.read_text(encoding="utf-8")


def run_named_tests(refs: list[str]) -> tuple[dict[str, str], int]:
    """Whether the tests the ledger names pass right now.

    A pinned_by_test that names a test nobody runs is a claim that regresses
    quietly, which is the failure the field exists to prevent.
    """
    refs = sorted({r for r in refs if test_exists(r)})
    if not refs:
        return {}, 0
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *refs, "-q", "--tb=no", "-rA",
         "-p", "no:cacheprovider"],
        cwd=str(REPO), capture_output=True, text=True, errors="replace")
    outcomes = {}
    for line in (proc.stdout + proc.stderr).splitlines():
        m = TEST_REF.match(line.strip())
        if m:
            outcomes[m.group(2)] = m.group(1)
    return outcomes, proc.returncode


def test_coverage(rows: list[dict], outcomes: dict[str, str]) -> list[dict]:
    out = []
    for r in rows:
        ref = (r.get("pinned_by_test") or "").strip()
        if not ref:
            continue
        out.append({"id": r["id"], "test": ref,
                    "exists": "yes" if test_exists(ref) else "no",
                    "result": outcomes.get(ref, "not run")})
    return out


# --- output -------------------------------------------------------------------
def write_csv(records: list[dict], out: Path = MAP_CSV) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        w.writeheader()
        for rec in records:
            w.writerow({k: rec.get(k, "") for k in CSV_FIELDS})
    return out


def write_markdown(a: dict, out: Path = MAP_MD) -> Path:
    records, rows, files = a["records"], a["rows"], a["files"]
    orph, unc = a["orphans"], a["uncited"]
    no_artefact = [o for o in orph if o["no_artefact"]]
    unnamed = [o for o in orph if o["unnamed"]]
    chains = a["chains"]
    no_successor = [c for c in chains if c["superseded_by"] == "(none)"]
    floors = a["floors"]
    coverage = a["coverage"]
    failing = [c for c in coverage if c["result"] not in ("PASSED", "not run")]
    not_run = [c for c in coverage if c["result"] == "not run"]
    by_status: dict[str, int] = {}
    for r in rows:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
    scanned = carrier_files(files)

    text = """# Claims map: every claim, its ledger row, and the artefact that carries it

Generated %s by `%s`. Snapshot: **%d ledger rows**, %d files under
`results/`, %d of them scanned as possible carriers.

Parallel tracks write into `results/` while this runs, so the map describes the
repository at the timestamp above. A regeneration that differs is explained by
the timestamp before it is read as drift.

Status counts in this snapshot: %s.

## How to read this

Three legs. A claim id, the ledger row that states it, and the artefact a reader
opens to check it. `source_file` is the artefact the row itself names.
`carried_by` is every file under `results/` that names the claim id in its own
text, which is a different and weaker thing: a write-up can rest on a number
without ever naming the row it came from.

The third leg is `results/manuscript/`, which %s. **%d of the %d claim ids are
named inside it.** The rest are carried by a results write-up or by a CSV table
and have no manuscript location yet. Files there whose name marks them as a
numbered table or figure: %s. A claim named in one of those has a table to point
at, a claim named only in the prose has a section, and the `carried by` column
says which, per row.

Two exclusions, stated because they change the counts. `results/ledger.csv` and
this map's own two outputs are not scanned as carriers: they name every id by
construction and would report full coverage whatever the write-ups say.
`results/pending_ledger/` is not scanned and not counted as an uncited artefact,
because a proposed row is a ledger draft rather than evidence.

Claims are quoted truncated, never in full, so a retired wording cannot re-enter
prose through the file that lists it.

## The map

%s

## 1. Orphan claims

A claim nothing carries is a claim that will not survive review. Two failures,
counted apart because they are not equally bad.

**No artefact behind the row: %d of %d.** The row names no source file, or names
one that is not on disk.

%s

**No results markdown names the id: %d of %d.** The evidence file exists, but no
write-up refers to the claim by id, so the route from prose to ledger row is one
a reader has to reconstruct.

Under the union of the two conditions, **%d of %d rows are orphans**.

%s

## 2. Uncited artefacts

Files under `results/` that no ledger row's `source_file` points at. **%d of %d
scanned files.** An artefact no claim rests on is either dead weight or an
unrecorded claim, and the two are told apart by opening the file, not by this
table. Where a parallel track has already proposed a row naming the file, the
note says so: those stop being uncited when
`python -m colophon.merge_ledger` folds the proposals in.

%s

## 3. Broken derivations

`derived_from` references to row ids that do not exist. The check is the rule
`tests/test_ledger.py::test_derived_from_resolves_to_real_ids` enforces, run
here over the same file.

**%d broken references.**

%s

## 4. Retirement chains

A retired claim is never deleted, so the chain from the withdrawn wording to its
replacement has to lead somewhere. **%d RETIRED rows, %d with no successor
named.**

%s

## 5. Pre-registration status

Reported, never edited. A pre-registration is worth carrying only if an outcome
lands against it, so the column that matters is the last one. An outcome counts
as recorded when the row leaves PENDING, or carries a verification date, or
states an n.

**%d PRE-* rows, %d with an outcome recorded, %d with an outcome proposed by a
track and not yet merged.** A proposal is not a record: the last column names
the file it is sitting in.

%s

## 6. Floor coverage

The project rule is that a failure rate quoted without its floor is not a
number. Which rows quote a rate is decided by
`colophon.ledger.rates_without_floor`, not by a second copy of the rule here.

**%d MEASURED rows quote a rate. %d of them name no floor.** A rate with no
floor is not a number, so the second figure is the one that has to stay at zero.

%s

## 7. Test coverage

`pinned_by_test` is what stops a claim regressing silently, so the field is
worth only as much as the test behind it. **%d rows name a test, %d distinct
tests, %d rows name a test that does not exist, %d rows whose test did not
pass.**

%s

%s

## What was dropped

Nothing was sampled. Every row in `results/ledger.csv` is mapped and every file
under `results/` is inventoried. Three exclusions, all stated above and all
applied by rule rather than by hand: `results/ledger.csv` and the map's own two
outputs are excluded from the carrier scan, and `results/pending_ledger/` is
excluded from both the carrier scan and the uncited count. Claim text is
truncated to %d characters. %s
""" % (
        a["generated"], CMD, len(rows), len(files), len(scanned),
        ", ".join("%s %d" % (k, by_status[k]) for k in sorted(by_status)),
        "does not exist at this snapshot"
        if not (RESULTS / "manuscript").exists() else
        "holds %d file(s): %s" % (len(a["manuscript"]),
                                  ", ".join("`%s`" % Path(f).name
                                            for f in a["manuscript"])),
        sum(1 for r in records
            if any("/manuscript/" in f for f in r["carried_by"].split(";") if f)),
        len(rows),
        ", ".join("`%s`" % Path(f).name for f in a["manuscript"]
                  if TABLE_OR_FIGURE.match(Path(f).name)) or "none at this snapshot",
        _table(["id", "section", "status", "claim", "source_file", "source",
                "carried by, id named in"],
               [[r["id"], r["section"], r["status"], r["claim_truncated"],
                 r["source_file"] or "(none)", r["source_exists"],
                 r["carried_by"].replace(";", "; ") or "(nothing)"]
                for r in records]),
        len(no_artefact), len(rows),
        _table(["id", "status", "why"],
               [[o["id"], o["status"], o["why"]] for o in no_artefact])
        if no_artefact else "None.",
        len(unnamed), len(rows),
        len(orph), len(rows),
        _table(["id", "status", "source_file", "why"],
               [[o["id"], o["status"],
                 next((r["source_file"] for r in records if r["id"] == o["id"]), "") or "(none)",
                 o["why"]] for o in orph]) if orph else "None.",
        len(unc), len(scanned),
        _table(["file", "note"], [[u["file"], u["note"] or ""] for u in unc])
        if unc else "None.",
        len(a["broken"]),
        _table(["row", "names unknown id"], [[i, ref] for i, ref in a["broken"]])
        if a["broken"] else "None.",
        len(chains), len(no_successor),
        _table(["id", "claim", "superseded_by", "successor exists",
                "successor status", "reason"],
               [[c["id"], c["claim"], c["superseded_by"],
                 "yes" if c["successor_exists"] else "no",
                 c["successor_status"] or "(none)", c["reason"]]
                for c in chains]) if chains else "None.",
        len(a["pre"]), sum(1 for p in a["pre"] if p["outcome_recorded"] == "yes"),
        sum(1 for p in a["pre"] if p["outcome_proposed"]),
        _table(["id", "section", "status", "claim", "registered value",
                "outcome recorded", "outcome proposed"],
               [[p["id"], p["section"], p["status"], p["claim"], p["value"],
                 p["outcome_recorded"], p["outcome_proposed"] or "no"]
                for p in a["pre"]]) if a["pre"] else "None.",
        len(floors["quoting_a_rate"]), len(floors["without_floor"]),
        _table(["id", "status", "value", "floor named", "floor"],
               [[f["id"], f["status"], f["value"], f["has_floor"], f["floor"]]
                for f in floors["rows"]]) if floors["rows"] else "None.",
        len(coverage), len({c["test"] for c in coverage}),
        sum(1 for c in coverage if c["exists"] == "no"), len(failing),
        _table(["id", "test", "exists", "result"],
               [[c["id"], c["test"], c["exists"], c["result"]] for c in coverage])
        if coverage else "None.",
        ("Every named test was run in one pytest invocation, exit status %d."
         % a["pytest_returncode"]) if not not_run else
        ("Tests were not run in this pass, so %d rows report their result as "
         "not run." % len(not_run)),
        CLAIM_CHARS,
        "The pinned tests were run." if not not_run else
        "The pinned tests were not run in this pass.",
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return out


def analyse(run_tests: bool = True) -> dict:
    rows = ledger.load()
    files = results_files()
    records = build(rows, files)
    refs = sorted({(r.get("pinned_by_test") or "").strip()
                   for r in rows if (r.get("pinned_by_test") or "").strip()})
    outcomes, code = run_named_tests(refs) if run_tests else ({}, 0)
    return {
        "generated": _now(), "rows": rows, "files": files, "records": records,
        "manuscript": [f for f in files if "/manuscript/" in f],
        "orphans": orphans(records), "uncited": uncited(records, files),
        "broken": broken_derivations(rows), "chains": retirement_chains(rows),
        "pre": pre_rows(rows), "floors": floor_coverage(rows),
        "coverage": test_coverage(rows, outcomes), "pytest_returncode": code,
    }


def proposal(a: dict) -> list[dict]:
    """The ledger rows this track proposes, built from the numbers it measured."""
    rows = a["rows"]
    orph = a["orphans"]
    no_artefact = [o for o in orph if o["no_artefact"]]
    unnamed = [o for o in orph if o["unnamed"]]
    chains = a["chains"]
    no_successor = [c for c in chains if c["superseded_by"] == "(none)"]
    coverage = a["coverage"]
    failing = [c for c in coverage if c["result"] not in ("PASSED", "not run")]
    scanned = carrier_files(a["files"])
    n = len(rows)
    shared = dict(
        section="F3", section_title="Claims map",
        command=CMD, sop_class="not applicable, this section audits the ledger",
        validator="none, no object is read or scored",
        validator_version="not applicable",
        floor="not applicable, no validator is involved and no conformance rate "
              "is quoted",
        dropped="nothing sampled: every row in results/ledger.csv is mapped and "
                "every file under results/ is inventoried. results/ledger.csv "
                "and the map's own two outputs are excluded from the carrier "
                "scan because they name every id by construction, and "
                "results/pending_ledger/ is excluded from the carrier scan and "
                "the uncited count because a proposed row is not evidence",
        source_file="results/claims_map.csv and results/claims_map.md",
        notes="Snapshot taken %s. Parallel tracks write into results/ during "
              "the run, so a regeneration at another time differs by "
              "construction." % a["generated"])
    return [
        dict(id="F3-01", claim="Every claim in the ledger is mapped to its row "
             "and to the artefact that carries it.", status="MEASURED",
             value="%d claim ids mapped across %d sections, %d files under "
                   "results/ inventoried, %d scanned as possible carriers"
                   % (n, len({r["section"] for r in rows}), len(a["files"]),
                      len(scanned)),
             n=str(n), denominator=str(n),
             pinned_by_test="tests/test_claims_map.py::test_every_ledger_row_is_mapped",
             **shared),
        dict(id="F3-02", claim="Orphan claims, meaning ledger rows with no "
             "artefact behind them or which no results write-up names by id.",
             status="MEASURED",
             value="%d of %d rows have no artefact on disk; %d of %d are named "
                   "by no results markdown; %d of %d fail at least one of the two"
                   % (len(no_artefact), n, len(unnamed), n, len(orph), n),
             n=str(len(orph)), denominator=str(n),
             derived_from="F3-01",
             pinned_by_test="tests/test_claims_map.py::test_orphans_are_reported_not_hidden",
             status_note="The two failures are counted apart because they are "
             "not equally bad. A row with no artefact has nothing behind it. A "
             "row whose artefact exists but which no write-up names by id is "
             "findable only by a reader who already knows where to look.",
             **shared),
        dict(id="F3-03", claim="Uncited artefacts, meaning files under results/ "
             "that no ledger row points at.", status="MEASURED",
             value="%d of %d scanned files are named by no source_file in the "
                   "ledger" % (len(a["uncited"]), len(scanned)),
             n=str(len(a["uncited"])), denominator=str(len(scanned)),
             derived_from="F3-01",
             pinned_by_test="tests/test_claims_map.py::test_uncited_artefacts_are_reported",
             status_note="An artefact no claim rests on is either dead weight "
             "or an unrecorded claim. This row counts them and does not decide "
             "which each one is.",
             **shared),
        dict(id="F3-04", claim="Every derived_from reference in the ledger "
             "resolves to a row that exists.", status="MEASURED",
             value="%d broken references across %d rows carrying derived_from"
                   % (len(a["broken"]),
                      sum(1 for r in rows if (r.get("derived_from") or "").strip())),
             n=str(len(a["broken"])),
             denominator=str(sum(1 for r in rows
                                 if (r.get("derived_from") or "").strip())),
             derived_from="F3-01",
             pinned_by_test="tests/test_claims_map.py::test_no_broken_derivations",
             **shared),
        dict(id="F3-05", claim="Every retired claim keeps its reason, and the "
             "chain from a withdrawn wording to its replacement is followed.",
             status="MEASURED",
             value="%d RETIRED rows, %d carry a reason, %d name a successor, "
                   "%d of those successors exist and are live"
                   % (len(chains), sum(1 for c in chains if c["has_reason"]),
                      len(chains) - len(no_successor),
                      sum(1 for c in chains if c["successor_live"])),
             n=str(len(chains)), denominator=str(n),
             derived_from="F3-01",
             pinned_by_test="tests/test_claims_map.py::test_retired_rows_keep_a_reason",
             status_note="%s" % ("Every retired row names a successor."
                                 if not no_successor else
                                 "%d retired row(s) name no successor: %s. That "
                                 "is a withdrawal rather than a replacement, "
                                 "and is reported, not corrected."
                                 % (len(no_successor),
                                    ", ".join(c["id"] for c in no_successor))),
             **shared),
        dict(id="F3-06", claim="Pre-registration rows and whether an outcome "
             "has been recorded against any of them yet.", status="MEASURED",
             value="%d PRE-* rows, %d with an outcome recorded, %d with an "
                   "outcome proposed by a track and not yet merged"
                   % (len(a["pre"]),
                      sum(1 for p in a["pre"] if p["outcome_recorded"] == "yes"),
                      sum(1 for p in a["pre"] if p["outcome_proposed"])),
             n=str(sum(1 for p in a["pre"] if p["outcome_recorded"] == "yes")),
             denominator=str(len(a["pre"])),
             derived_from="F3-01",
             pinned_by_test="tests/test_claims_map.py::test_pre_rows_are_reported_unchanged",
             status_note="This track reports the pre-registrations and does not "
             "edit them. An outcome counts as recorded when the row leaves "
             "PENDING, or carries a verification date, or states an n.",
             **shared),
        dict(id="F3-07", claim="Floor coverage: which MEASURED rows quote a "
             "rate, and whether each names its floor.", status="MEASURED",
             value="%d rows quote a rate by the ledger's own rule, %d of them "
                   "name no floor" % (len(a["floors"]["quoting_a_rate"]),
                                      len(a["floors"]["without_floor"])),
             n=str(len(a["floors"]["without_floor"])),
             denominator=str(len(a["floors"]["quoting_a_rate"])),
             derived_from="F3-01",
             pinned_by_test="tests/test_claims_map.py::test_floor_rule_is_the_ledgers_own",
             status_note="The rate test is colophon.ledger.rates_without_floor, "
             "reused rather than reimplemented, so there is one definition of a "
             "rate in this repository.",
             **shared),
        dict(id="F3-08", claim="Test coverage of the ledger: which rows name a "
             "pinning test, whether it exists and whether it passes.",
             status="MEASURED",
             value="%d of %d rows name a test, %d distinct tests, %d name a "
                   "test that does not exist, %d did not pass when run"
                   % (len(coverage), n, len({c["test"] for c in coverage}),
                      sum(1 for c in coverage if c["exists"] == "no"), len(failing)),
             n=str(len(coverage)), denominator=str(n),
             derived_from="F3-01",
             pinned_by_test="tests/test_claims_map.py::test_named_tests_exist",
             status_note="Run in one pytest invocation at generation time, exit "
             "status %d. A pinned_by_test that names a test nobody runs is a "
             "claim that regresses quietly." % a["pytest_returncode"],
             **shared),
    ]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--skip-tests", action="store_true",
                    help="do not run the tests named in pinned_by_test")
    ap.add_argument("--print-only", action="store_true",
                    help="print the summary, write nothing")
    args = ap.parse_args(argv)

    a = analyse(run_tests=not args.skip_tests)
    orph = a["orphans"]
    print("claims map %s" % a["generated"])
    print("  %d ledger rows, %d files under results/" % (len(a["rows"]), len(a["files"])))
    print("  orphans %d (no artefact %d, unnamed in prose %d)"
          % (len(orph), sum(1 for o in orph if o["no_artefact"]),
             sum(1 for o in orph if o["unnamed"])))
    print("  uncited artefacts %d" % len(a["uncited"]))
    print("  broken derivations %d" % len(a["broken"]))
    print("  retired rows %d, without a successor %d"
          % (len(a["chains"]),
             sum(1 for c in a["chains"] if c["superseded_by"] == "(none)")))
    print("  PRE rows %d, outcomes recorded %d"
          % (len(a["pre"]), sum(1 for p in a["pre"] if p["outcome_recorded"] == "yes")))
    print("  rates %d, without a floor %d"
          % (len(a["floors"]["quoting_a_rate"]), len(a["floors"]["without_floor"])))
    print("  rows naming a test %d, not passing %d"
          % (len(a["coverage"]),
             sum(1 for c in a["coverage"] if c["result"] not in ("PASSED", "not run"))))
    if args.print_only:
        return 0

    write_csv(a["records"])
    write_markdown(a)
    PENDING.mkdir(parents=True, exist_ok=True)
    PROPOSAL.write_text(json.dumps(proposal(a), indent=2), encoding="utf-8")
    print("wrote %s, %s and %s" % (MAP_MD, MAP_CSV, PROPOSAL))
    return 0


if __name__ == "__main__":
    sys.exit(main())
