"""The claims ledger.

Every quantitative statement that may reach the manuscript gets a row here, with
the exact command that produced it and the file that holds the evidence. Rows
are written as the measurement runs, not reconstructed at submission time.

The schema is wider than the markdown table spine-gsps used, because reading
that project's failure log showed which meaning kept getting crammed into free
text and then lost. Specifically:

    floor        every rate in this project has to name its floor, so the floor
                 is a column rather than a sentence somewhere else
    dropped      what a run sampled, truncated or skipped, so silent truncation
                 cannot read as full coverage
    n            stated, never inferred from the prose of the claim
    denominator
    validator    which third party tool produced the number, and the version
    validator_   string it reported, because a rate is not comparable across
    version      tool versions
    status_note  the qualifiers that were previously appended after a comma
                 inside the status cell
    derived_from concrete row ids, resolved at write time. A bare "same" stops
                 meaning anything once rows are sorted
    supersedes / a retired claim is never deleted. Its wording stays, its
    superseded_  replacement is named by id
    by

Status vocabulary:

    MEASURED    run in this project, on this hardware, reproducible by the
                listed command
    VERIFIED    checked against a primary source, for example the DICOM standard
                or a published specification, rather than measured here
    DERIVED     follows from other rows by arithmetic or logic, with those rows
                named in derived_from
    PENDING     the measurement is defined and scheduled, no number yet
    LITERATURE  taken from a cited source, never presented as ours
    RETIRED     previously believed, now known wrong. The row stays so the
                number cannot creep back. The reason goes in retired_reason.

A row is keyed by `id`, which is unique by construction: writing a second row
with an existing id replaces it rather than appending a duplicate.
"""
from __future__ import annotations

import csv
import datetime as _dt
from pathlib import Path

from .paths import LEDGER

FIELDS = [
    "id",                 # stable key, for example C3-02. Never renumbered.
    "section",            # short section code, for example C3
    "section_title",      # human readable section name
    "claim",              # the statement, as it would appear in the manuscript
    "status",             # see vocabulary above
    "status_note",        # qualifier on the status, not on the claim
    "value",              # the number itself, plain text, units included
    "sop_class",          # which SOP class the row applies to, or "all"
    "n",                  # numerator or count, stated
    "denominator",        # stated, never inferred
    "floor",              # the validator floor this rate is measured against
    "dropped",            # what this run sampled, truncated or skipped
    "validator",          # third party tool that produced the number
    "validator_version",  # its captured version string
    "command",            # the exact runnable invocation
    "source_file",        # the artefact holding the evidence
    "derived_from",       # other row ids this depends on
    "external_source",    # primary standard or document, with section number
    "pinned_by_test",     # the test that stops this claim regressing silently
    "supersedes",
    "superseded_by",
    "retired_reason",
    "idc_index_version",  # the archive release this row was measured against
    "date",               # when the row was last written
    "verified_on",        # when an external source was last checked
    "hardware",           # empty means inherit the default in results/README.md
    "notes",
]

# 481,750 will not reproduce next release, so every row records which release it
# was written against, whether or not it reads the index. Bump this and re-run
# every module when IDC ships a new version: do not edit rows by hand.
IDC_INDEX_VERSION = "v24"

VALID_STATUS = {"MEASURED", "VERIFIED", "DERIVED", "PENDING", "LITERATURE", "RETIRED"}


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load(path: Path = LEDGER) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return [dict(r) for r in csv.DictReader(fh)]


def write(rows: list[dict], path: Path = LEDGER) -> None:
    seen: set[str] = set()
    for r in rows:
        if r["id"] in seen:
            raise ValueError("duplicate ledger id %r" % r["id"])
        seen.add(r["id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})


def record(id: str, section: str, claim: str, status: str, path: Path = LEDGER,
           **fields) -> None:
    """Insert or replace one claim row.

    Every field other than the four positional ones is optional and defaults to
    empty, so a row states only what it actually knows.
    """
    if status not in VALID_STATUS:
        raise ValueError("status %r not in %s" % (status, sorted(VALID_STATUS)))
    unknown = set(fields) - set(FIELDS)
    if unknown:
        raise ValueError("unknown ledger fields: %s" % sorted(unknown))
    _upsert([_build(id, section, claim, status, fields)], path)


def _build(id: str, section: str, claim: str, status: str, fields: dict) -> dict:
    row = {k: "" for k in FIELDS}
    row.update(fields)
    row.update({"id": id, "section": section, "claim": claim, "status": status,
                "date": _now()})
    if not row["idc_index_version"]:
        row["idc_index_version"] = IDC_INDEX_VERSION
    return row


def _upsert(new_rows: list[dict], path: Path, outcome: bool = False) -> None:
    """Insert or replace, except that a retirement is never undone.

    The module that first registers a claim re-asserts it on every run, with
    whatever status it had when it was written. That is right for a measurement,
    which should be recomputed, and wrong for a claim the data has since
    falsified: re-running `colophon.validate` silently put PRE-01 back to
    PENDING after it had been retired as a wrong prediction, and nothing
    complained. The merge gate cannot catch that, because a module writing here
    directly never passes through it.

    A RETIRED row therefore survives any later write that is not itself a
    retirement. The retirement fields are preserved and the incoming row's other
    fields are taken, so a re-run can still refresh a value without resurrecting
    the claim.
    """
    rows = load(path)
    index = {r["id"]: i for i, r in enumerate(rows)}
    for row in new_rows:
        rid = row["id"]
        if rid in index:
            prior = rows[index[rid]]
            # A pre-registration is authored once. The module that registers it
            # re-asserts it on every run, which would erase any outcome later
            # recorded against it: re-running colophon.validate wiped both
            # PRE-01's retirement and PRE-05's consolidated class outcomes.
            # Only an explicit outcome write may change one.
            if rid.startswith("PRE-") and not outcome:
                for field in ("status", "status_note", "notes", "retired_reason",
                              "superseded_by", "derived_from", "source_file",
                              "value"):
                    if prior.get(field):
                        row = dict(row)
                        row[field] = prior[field]
            if prior.get("status") == "RETIRED" and row.get("status") != "RETIRED":
                row = dict(row)
                row["status"] = "RETIRED"
                for field in ("retired_reason", "superseded_by", "status_note",
                              "notes"):
                    if prior.get(field):
                        row[field] = prior[field]
            rows[index[rid]] = row
        else:
            index[rid] = len(rows)
            rows.append(row)
    write(rows, path)


def record_outcome(entries: list[dict], path: Path = LEDGER) -> None:
    """Record an outcome against an already registered claim.

    The only route by which a PRE-* row may change. Everything else that writes
    the ledger re-asserts its own rows on every run and must not be able to
    undo a result.
    """
    built = [_build(dict(e).pop("id") if False else e["id"], e["section"],
                    e["claim"], e["status"],
                    {k: v for k, v in e.items()
                     if k not in ("id", "section", "claim", "status")})
             for e in entries]
    _upsert(built, path, outcome=True)


def record_many(entries: list[dict], path: Path = LEDGER) -> None:
    """Validate every entry, then write once.

    Writing one row at a time meant a single malformed entry left the ledger
    half updated and the failure looked like a missing row rather than an
    error. That happened: a duplicate keyword argument aborted a batch after
    two of five rows had been written, and the ledger read as though the other
    three had never been authored. Building all rows before touching the file
    makes the batch atomic.
    """
    built = []
    for e in entries:
        e = dict(e)
        try:
            built.append(_build(e.pop("id"), e.pop("section"), e.pop("claim"),
                                e.pop("status"), e))
        except KeyError as exc:
            raise ValueError("ledger entry missing required field %s" % exc) from None
        if built[-1]["status"] not in VALID_STATUS:
            raise ValueError("status %r not in %s"
                             % (built[-1]["status"], sorted(VALID_STATUS)))
        unknown = set(e) - set(FIELDS)
        if unknown:
            raise ValueError("unknown ledger fields on %s: %s"
                             % (built[-1]["id"], sorted(unknown)))
    _upsert(built, path)


def retire(id: str, reason: str, superseded_by: str = "", path: Path = LEDGER) -> None:
    """Mark a claim wrong without deleting it."""
    rows = load(path)
    for row in rows:
        if row["id"] == id:
            row["status"] = "RETIRED"
            row["retired_reason"] = reason
            row["superseded_by"] = superseded_by
            row["date"] = _now()
            write(rows, path)
            if superseded_by:
                for other in rows:
                    if other["id"] == superseded_by:
                        other["supersedes"] = id
                        write(rows, path)
            return
    raise KeyError("no ledger row with id %r to retire" % id)


def rates_without_floor(path: Path = LEDGER) -> list[str]:
    """Ids of rows that quote a rate but name no floor.

    The project rule is that a failure rate quoted without its floor is not a
    number. This is the check that enforces it.
    """
    bad = []
    for r in load(path):
        if r["status"] != "MEASURED":
            continue
        v = (r.get("value") or "").lower()
        looks_like_rate = "percent" in v or "%" in v or " of " in v
        if looks_like_rate and not (r.get("floor") or "").strip():
            bad.append(r["id"])
    return bad


def column_fill_rates(path: Path = LEDGER) -> dict[str, float]:
    """How much of the schema is actually carrying meaning.

    A wide schema is not a quality signal. A column nothing ever fills is a
    column that should be dropped or justified, and reporting the fill rate is
    how that stays visible instead of accumulating.
    """
    rows = load(path)
    if not rows:
        return {}
    return {f: round(100 * sum(1 for r in rows if (r.get(f) or "").strip()) / len(rows), 1)
            for f in FIELDS}


def null_join_guard(frame, keys: list[str], what: str) -> dict:
    """Any rate whose denominator contains null join keys must declare them.

    The acquisition-inheritance defect was a null-on-null match that no test
    caught. This is the guard that would have caught it: it refuses to let a
    join key carry nulls silently, and returns the counts so the caller has to
    put them in the output.
    """
    counts = {k: int(frame[k].isna().sum()) for k in keys}
    total = int(len(frame))
    rec = {"measurement": what, "rows": total, "null_join_keys": counts,
           "rows_with_any_null_key": int(frame[keys].isna().any(axis=1).sum())}
    rec["clean"] = rec["rows_with_any_null_key"] == 0
    return rec


def summary(path: Path = LEDGER) -> str:
    rows = load(path)
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    parts = ["%s %d" % (k, counts[k]) for k in sorted(counts)]
    return "%d rows: %s" % (len(rows), ", ".join(parts) if parts else "empty")


if __name__ == "__main__":
    print(summary())
    missing = rates_without_floor()
    if missing:
        print("rows quoting a rate with no floor named: %s" % ", ".join(missing))
