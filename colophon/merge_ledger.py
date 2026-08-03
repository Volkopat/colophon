"""Merge ledger rows proposed by parallel tracks, serially.

`colophon.ledger.write` rewrites the whole CSV, so two tracks writing at once
would silently lose rows. During a parallel run no track touches
`results/ledger.csv`. Each writes a JSON list of proposed rows to
`results/pending_ledger/<track>.json`, and this module folds them in one at a
time, in filename order, so the result is deterministic regardless of which
track finished first.

Rows are validated before any are written, so a malformed proposal from one
track cannot leave the ledger half updated.

Usage:
    python -m colophon.merge_ledger            merge and archive the proposals
    python -m colophon.merge_ledger --dry-run
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from . import ledger
from .paths import RESULTS

PENDING = RESULTS / "pending_ledger"
ARCHIVE = PENDING / "merged"

# A track may never invent or alter a pre-registration. It may only record an
# outcome, and only through the fields that carry one.
PROTECTED_PREFIXES = ("PRE-",)
OUTCOME_FIELDS = {"id", "section", "section_title", "claim", "status",
                  "status_note", "value", "notes", "verified_on", "n",
                  "denominator", "source_file", "command", "derived_from",
                  "pinned_by_test", "floor", "dropped", "sop_class",
                  "validator", "validator_version", "external_source",
                  # A pre-registration that the data falsifies is retired, and
                  # a retired row without a reason breaks the project's own
                  # rule that a withdrawn claim keeps its reason. Recording why
                  # a prediction failed is the outcome, not a rewording of it.
                  "retired_reason"}


def collect() -> list[tuple[str, dict]]:
    out = []
    for path in sorted(PENDING.glob("*.json")):
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise ValueError("%s is not valid JSON: %s" % (path.name, exc))
        # Tracks proposed rows in two shapes: a bare list, and an envelope
        # {"track": ..., "rows": [...]} carrying provenance about the run.
        # Both are accepted. Keys that are not ledger fields, such as a
        # per-row "fields_changed" audit note, are dropped here with a count
        # rather than rejected, because the note is useful to a human reading
        # the proposal and meaningless to the CSV.
        if isinstance(rows, dict):
            rows = rows.get("rows", [rows])
        stripped = 0
        for r in rows:
            if not isinstance(r, dict) or "id" not in r:
                raise ValueError("%s contains a row with no id" % path.name)
            extra = set(r) - set(ledger.FIELDS)
            if extra:
                stripped += len(extra)
                r = {k: v for k, v in r.items() if k in ledger.FIELDS}
            out.append((path.name, r))
        if stripped:
            print("  %s: dropped %d non-ledger key(s) from its proposal"
                  % (path.name, stripped))
    return out


def check_protected(rows: list[tuple[str, dict]]) -> list[str]:
    """A pre-registered row may gain an outcome. It may not be reworded."""
    existing = {r["id"]: r for r in ledger.load()}
    problems = []
    for src, r in rows:
        rid = r["id"]
        if not rid.startswith(PROTECTED_PREFIXES):
            continue
        prior = existing.get(rid)
        if prior is None:
            problems.append("%s proposes new pre-registration %s" % (src, rid))
            continue
        if r.get("claim") and r["claim"].strip() != prior["claim"].strip():
            problems.append("%s rewords the claim of %s" % (src, rid))
        stray = set(r) - OUTCOME_FIELDS
        if stray:
            problems.append("%s sets %s on %s" % (src, sorted(stray), rid))
    return problems


def check_retired(rows: list[tuple[str, dict]]) -> list[str]:
    """A retired claim is never reworded and never un-retired."""
    existing = {r["id"]: r for r in ledger.load()}
    problems = []
    for src, r in rows:
        prior = existing.get(r["id"])
        if prior is None or prior["status"] != "RETIRED":
            continue
        if r.get("status") and r["status"] != "RETIRED":
            problems.append("%s un-retires %s" % (src, r["id"]))
        if r.get("claim") and r["claim"].strip() != prior["claim"].strip():
            problems.append("%s rewords retired claim %s" % (src, r["id"]))
    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    PENDING.mkdir(parents=True, exist_ok=True)
    rows = collect()
    if not rows:
        print("no pending ledger proposals")
        return 0

    problems = check_protected(rows) + check_retired(rows)
    if problems:
        print("REFUSING to merge, %d violation(s):" % len(problems))
        for p in problems:
            print("  " + p)
        return 1

    by_id = {}
    order = []
    for src, r in rows:
        if r["id"] not in by_id:
            order.append(r["id"])
        by_id[r["id"]] = (src, r)
    print("merging %d rows from %d proposals"
          % (len(order), len({s for s, _ in rows})))
    if args.dry_run:
        for rid in order:
            src, r = by_id[rid]
            print("  %-12s %-11s %s  <- %s"
                  % (rid, r.get("status", "?"), r.get("claim", "")[:60], src))
        return 0

    proposals = [by_id[rid][1] for rid in order]
    # The merge gate is the sanctioned route for an outcome, so it writes
    # pre-registrations through record_outcome and everything else normally.
    pre = [r for r in proposals if r["id"].startswith(PROTECTED_PREFIXES)]
    rest = [r for r in proposals if not r["id"].startswith(PROTECTED_PREFIXES)]
    if rest:
        ledger.record_many(rest)
    if pre:
        ledger.record_outcome(pre)
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    for path in sorted(PENDING.glob("*.json")):
        shutil.move(str(path), str(ARCHIVE / path.name))
    print("ledger: %s" % ledger.summary())
    return 0


if __name__ == "__main__":
    sys.exit(main())
