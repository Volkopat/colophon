"""Track D: re-close the dcmpschk column for Grayscale Softcopy Presentation State.

Why this module exists rather than a census re-run. dcmpschk prefixes every line
it writes with a severity letter, its own verdict included, and the verdict reads
`W: Test passed.` The census filter tested whether a line began "Test passed",
never saw it, and recorded a pass as a warning class on all 1,086 GSPS objects.
The filter is fixed in `colophon.census.parse_dcmpschk`, which this module calls,
so there is one implementation of the rule and not two. Only the dcmpschk column
is recomputed: the dciodvfy and dicom-validator columns for this class were not
touched by the defect, and re-running them would risk moving a closed number.

The census may be running while this runs. This module reads the census manifest
and the committed census outputs, and writes only under its own state directory.
It never opens the census records file for writing.

Fetching is a small parallel pool of single-series `colophon.fetch.fetch_series`
calls, validation is serial, and each series is deleted as soon as its validator
has run. Free space is checked before every batch. The whole class is about 1.5
MB, so the guard is cheap insurance rather than a real constraint, but a fetch
loop with no floor is the one that eventually fills a disk.

Resumability: one append-only JSONL record per series, flushed per series, so a
crash resumes rather than restarts.

Usage:
    python -m colophon.gsps_dcmpschk --run --report
    python -m colophon.gsps_dcmpschk --report
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

from . import census, fetch, floor, ledger, paths
from .paths import CACHE, RESULTS

CMD = "python -m colophon.gsps_dcmpschk --run --report"

SOP_CLASS = "Grayscale Softcopy Presentation State Storage"
VALIDATOR = "dcmpschk"

STATE = CACHE / "track_d"
WORK = STATE / "work"
RECORDS = STATE / "records.jsonl"

# Read only. The census owns this file and may be appending to its neighbour.
MANIFEST = CACHE / "census" / "manifest.csv"

PHASE2 = RESULTS / "phase2"
OUT_CSV = PHASE2 / "gsps_dcmpschk.csv"
OUT_MD = RESULTS / "phase2_gsps_dcmpschk.md"
PENDING = RESULTS / "pending_ledger" / "track_d.json"

MIN_FREE_GB = 20.0
BATCH = 64
# Measured on this machine with the census running alongside: a batch of 64
# takes 110 s to fetch at 16 workers against 175 s at 8, and 5.6 s to validate.
# The whole class is 1.5 MB, so a batch in flight is under 100 KB.
FETCH_WORKERS = 16

FIELDS = ["sop_class_name", "collection_id", "analysis_result_id",
          "series_instance_uid", "sop_instance_uid", "validator",
          "message_class_id", "message_template", "severity_as_emitted",
          "raw_example", "test_passed_line", "dcmpschk_pass", "returncode",
          "banner_lines"]


# --- selection ----------------------------------------------------------------
def gsps_series() -> pd.DataFrame:
    """The 1,086 GSPS series, read from the census manifest, never rebuilt."""
    if not MANIFEST.exists():
        raise FileNotFoundError(
            "census manifest not found at %s. Run "
            "`python -m colophon.census --manifest` first." % MANIFEST)
    man = pd.read_csv(MANIFEST)
    sel = man[man.sop_class_name == SOP_CLASS].copy()
    return sel.sort_values("SeriesInstanceUID").reset_index(drop=True)


def _disk_guard() -> float:
    free = paths.free_gb(CACHE)
    if free < MIN_FREE_GB:
        raise RuntimeError("aborting: %.1f GB free on the cache volume, floor "
                           "is %.0f GB" % (free, MIN_FREE_GB))
    return free


def completed_uids() -> set[str]:
    """Series that have a successful record, so a re-run retries the rest.

    A fetch failure is recorded rather than dropped, but it is not a result. If
    it counted as done, a transient failure would become a permanent hole in the
    census with no way to close it short of deleting the state file.
    """
    done: set[str] = set()
    if RECORDS.exists():
        with RECORDS.open(encoding="utf-8") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                if rec.get("status") == "OK":
                    done.add(rec["series_instance_uid"])
    return done


def _lock_held_by() -> int | None:
    """The pid of another copy of this run, if one is alive.

    Two copies appending to the same records file re-fetch the same series and
    double the write. The duplicates are harmless because `load_records` drops
    them, but re-fetching a thousand objects for nothing is not, so a second
    start says whose run it is colliding with.
    """
    lock = STATE / "run.pid"
    if not lock.exists():
        return None
    try:
        pid = int(lock.read_text(encoding="utf-8").strip())
    except Exception:
        return None
    import subprocess as _sp
    out = _sp.run(["tasklist", "/FI", "PID eq %d" % pid], capture_output=True,
                  text=True, errors="replace").stdout
    return pid if str(pid) in out else None


# --- the run ------------------------------------------------------------------
def _validate_series(row: dict, series_dir: Path) -> dict:
    import pydicom
    files = sorted(p for p in series_dir.rglob("*") if p.is_file())
    rec = {"series_instance_uid": row["SeriesInstanceUID"],
           "sop_class_name": row["sop_class_name"],
           "collection_id": row["collection_id"],
           "analysis_result_id": row["analysis_result_id"],
           "status": "OK", "objects": []}
    if not files:
        rec["status"] = "FETCH_FAILED"
        return rec
    for f in files:
        try:
            ds = pydicom.dcmread(f, stop_before_pixels=True)
            uid = str(getattr(ds, "SOPInstanceUID", ""))
        except Exception as exc:
            rec["objects"].append({"status": "READ_FAILED",
                                   "error": "%s: %s" % (type(exc).__name__, exc)})
            continue
        out = census.run_dcmpschk(f)
        rec["objects"].append({
            "status": "OK",
            "sop_instance_uid": uid,
            "test_passed": bool(out["test_passed"]),
            "returncode": out["returncode"],
            "banner_lines": len(out["banners"]),
            "findings": out["findings"],
        })
    return rec


def run(limit: int | None = None) -> int:
    paths.require(paths.DCMPSCHK, "dcmpschk")
    STATE.mkdir(parents=True, exist_ok=True)
    other = _lock_held_by()
    if other is not None:
        raise RuntimeError(
            "another copy of this run is alive as pid %d. Two copies append to "
            "%s and re-fetch the same series. Wait for it, or delete %s if that "
            "pid is stale." % (other, RECORDS, STATE / "run.pid"))
    import os
    (STATE / "run.pid").write_text(str(os.getpid()), encoding="utf-8")
    try:
        return _run(limit)
    finally:
        shutil.rmtree(WORK, ignore_errors=True)
        (STATE / "run.pid").unlink(missing_ok=True)


def _run(limit: int | None) -> int:
    sel = gsps_series()
    done = completed_uids()
    todo = sel[~sel.SeriesInstanceUID.isin(done)]
    if limit:
        todo = todo.head(limit)
    print("track D: %s of %s GSPS series remaining (%s already recorded)"
          % (f"{len(todo):,}", f"{len(sel):,}", f"{len(done):,}"))
    if todo.empty:
        return 0

    started, n_done = time.time(), 0
    with RECORDS.open("a", encoding="utf-8") as sink:
        for start in range(0, len(todo), BATCH):
            batch = todo.iloc[start:start + BATCH].to_dict("records")
            free = _disk_guard()
            shutil.rmtree(WORK, ignore_errors=True)
            WORK.mkdir(parents=True, exist_ok=True)
            with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as pool:
                list(pool.map(
                    lambda r: fetch.fetch_series(
                        r["series_aws_url"], WORK / r["SeriesInstanceUID"]),
                    batch))
            for r in batch:
                d = WORK / r["SeriesInstanceUID"]
                sink.write(json.dumps(_validate_series(r, d)) + "\n")
                sink.flush()
                # Deleted as soon as its validator has run. Nothing accumulates.
                shutil.rmtree(d, ignore_errors=True)
                n_done += 1
            rate = n_done / max(time.time() - started, 1e-6)
            print("  %s/%s  %.1f series/s  free %.0f GB"
                  % (f"{n_done:,}", f"{len(todo):,}", rate, free), flush=True)
    return n_done


# --- reading back -------------------------------------------------------------
def load_records() -> dict:
    """One record per series. A success beats a failure, otherwise first wins.

    The records file is append-only and resumable, which means a second copy of
    this module started while the first was still running will re-fetch and
    re-append the series the first had not yet reached. That happened, and it
    also caused the only 17 fetch failures in the run, because both copies used
    the same work directory and each cleared it at the top of a batch. The
    duplicates are dropped on read rather than trusted not to exist, and the
    count is reported by `--report` so a silent double count is impossible.

    A retry appends a second record for a series that failed, so a success has
    to win over a failure or the retry would have no effect.

    Lines that will not parse are skipped for the same reason: two processes
    appending can in principle interleave a write.
    """
    if not RECORDS.exists():
        return {"records": [], "duplicate_lines": 0, "unparsable_lines": 0,
                "repeat_disagreements": 0, "failed_at_least_once": 0}
    by_uid: dict[str, dict] = {}
    failed_once: set[str] = set()
    duplicates, unparsable, disagreements = 0, 0, 0
    with RECORDS.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                uid = rec["series_instance_uid"]
            except Exception:
                unparsable += 1
                continue
            if rec.get("status") != "OK":
                failed_once.add(uid)
            if uid in by_uid:
                duplicates += 1
                prior = by_uid[uid]
                if prior.get("status") == "OK" == rec.get("status"):
                    # Two independent measurements of the same bytes. If they
                    # differ, the tool is not deterministic on this input and
                    # that is a finding in itself, so it is counted rather than
                    # resolved by whichever line happened to land first.
                    if _verdict(prior) != _verdict(rec):
                        disagreements += 1
                if not (prior.get("status") != "OK" and rec.get("status") == "OK"):
                    continue
            by_uid[uid] = rec
    recovered = sum(1 for uid in failed_once
                    if by_uid.get(uid, {}).get("status") == "OK")
    return {"records": list(by_uid.values()), "duplicate_lines": duplicates,
            "unparsable_lines": unparsable,
            "repeat_disagreements": disagreements,
            "failed_at_least_once": recovered}


def _verdict(rec: dict) -> list:
    return sorted((o.get("sop_instance_uid", ""), o.get("test_passed"),
                   tuple(sorted(f["message"] for f in o.get("findings", []))))
                  for o in rec.get("objects", []))


def rows_from_records(records: list[dict]) -> list[dict]:
    """One row per (sop_instance_uid, message_class_id).

    An object dcmpschk says nothing about still gets a row, with the message
    columns empty. Without it a pass would be invisible in the CSV and the pass
    count would have to be inferred from an absence.
    """
    rows = []
    for r in records:
        base = {"sop_class_name": r["sop_class_name"],
                "collection_id": r["collection_id"],
                "analysis_result_id": r["analysis_result_id"],
                "series_instance_uid": r["series_instance_uid"],
                "validator": VALIDATOR}
        if r["status"] != "OK":
            rows.append({**base, "sop_instance_uid": "",
                         "message_class_id": "", "message_template": "",
                         "severity_as_emitted": "", "raw_example": "",
                         "test_passed_line": "", "dcmpschk_pass": r["status"],
                         "returncode": "", "banner_lines": ""})
            continue
        for o in r["objects"]:
            if o.get("status") != "OK":
                rows.append({**base, "sop_instance_uid": "",
                             "message_class_id": "", "message_template": "",
                             "severity_as_emitted": "", "raw_example": "",
                             "test_passed_line": "",
                             "dcmpschk_pass": o.get("status", "READ_FAILED"),
                             "returncode": "", "banner_lines": ""})
                continue
            common = {**base,
                      "sop_instance_uid": o["sop_instance_uid"],
                      "test_passed_line": "yes" if o["test_passed"] else "no",
                      "dcmpschk_pass": "pass" if o["test_passed"] else "fail",
                      "returncode": o["returncode"],
                      "banner_lines": o["banner_lines"]}
            if not o["findings"]:
                rows.append({**common, "message_class_id": "",
                             "message_template": "", "severity_as_emitted": "",
                             "raw_example": ""})
                continue
            seen = set()
            for fi in o["findings"]:
                template = floor.normalise(fi["message"])
                mcid = floor.message_class_id(VALIDATOR, template)
                if mcid in seen:
                    continue
                seen.add(mcid)
                rows.append({**common, "message_class_id": mcid,
                             "message_template": template,
                             "severity_as_emitted": fi["severity"],
                             "raw_example": fi["message"][:300]})
    rows.sort(key=lambda x: (x["sop_instance_uid"], x["message_class_id"]))
    return rows


def summarise(records: list[dict]) -> dict:
    objects, passed, failed = 0, 0, 0
    banners, with_finding = 0, 0
    classes: Counter = Counter()
    class_meta: dict[str, tuple[str, str]] = {}
    fetch_failed = 0
    read_failed = 0
    returncodes: Counter = Counter()
    for r in records:
        if r["status"] != "OK":
            fetch_failed += 1
            continue
        for o in r["objects"]:
            if o.get("status") != "OK":
                read_failed += 1
                continue
            objects += 1
            banners += o["banner_lines"]
            returncodes[o["returncode"]] += 1
            if o["test_passed"]:
                passed += 1
            else:
                failed += 1
            if o["findings"]:
                with_finding += 1
            seen = set()
            for fi in o["findings"]:
                template = floor.normalise(fi["message"])
                mcid = floor.message_class_id(VALIDATOR, template)
                if mcid in seen:
                    continue
                seen.add(mcid)
                class_meta[mcid] = (template, fi["severity"])
                classes[mcid] += 1
    return {"series": len(records), "objects": objects, "passed": passed,
            "failed": failed, "banners": banners, "classes": classes,
            "class_meta": class_meta, "fetch_failed": fetch_failed,
            "read_failed": read_failed, "returncodes": returncodes,
            "objects_with_finding": with_finding}


# --- what the other two validators said about the same objects ------------------
def _ar(value) -> str:
    text = "" if value is None else str(value).strip()
    return "(null)" if text in ("", "nan", "NaN", "None") else text


def cross_validator() -> dict:
    """What dciodvfy and dicom-validator recorded for the same 1,086 objects.

    Read back from the committed census outputs rather than recomputed, because
    those two columns were not affected by the dcmpschk defect and re-running
    them would risk moving a closed number.

    `census_message_classes.csv` counts objects per message class, not per
    object, so the number of objects carrying at least one class from a given
    validator is bracketed rather than read off: the largest single class in an
    analysis result is a lower bound, the analysis result's object count is the
    upper bound. Where the two meet, the count is exact, and that is stated per
    validator instead of assumed.
    """
    mc = pd.read_csv(PHASE2 / "census_message_classes.csv")
    rates = pd.read_csv(PHASE2 / "census_rates.csv")
    g = mc[mc.sop_class_name == SOP_CLASS].copy()
    g["ar"] = g.analysis_result_id.map(_ar)
    r = rates[rates.sop_class_name == SOP_CLASS].copy()
    r["ar"] = r.analysis_result_id.map(_ar)
    ar_totals = r.groupby("ar")["objects"].sum().to_dict()

    out = {"total_objects": int(sum(ar_totals.values())), "validators": {}}
    for v in sorted(set(mc.validator) | {"dciodvfy", "dicom-validator"}):
        if v == VALIDATOR:
            continue
        sub = g[g.validator == v]
        lower, exact = 0, True
        for ar, total in ar_totals.items():
            chunk = sub[sub.ar == ar]
            best = int(chunk.objects.max()) if len(chunk) else 0
            lower += best
            if best != total and best != 0:
                exact = False
            if best == 0 and len(chunk):
                exact = False
        out["validators"][v] = {
            "classes": int(sub.message_class_id.nunique()),
            "objects_lower_bound": lower,
            "exact": bool(exact),
            "error_classes": int(sub[sub.severity_as_emitted.astype(str)
                                     .str.upper().str.startswith("ERROR")]
                                 .message_class_id.nunique()),
        }
    # The old dcmpschk column, kept visible so the correction is legible.
    old = g[g.validator == VALIDATOR]
    out["dcmpschk_before"] = {
        "classes": int(old.message_class_id.nunique()),
        "pass_line_recorded_on": int(
            old[old.message_template.astype(str).str.contains("Test passed")]
            .objects.sum()),
        "banner_classes": int(
            old[old.message_template.astype(str).str.contains("Testing:")]
            .message_class_id.nunique()),
    }
    return out


# --- outputs ------------------------------------------------------------------
def write_csv(rows: list[dict]) -> Path:
    PHASE2.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=FIELDS).to_csv(OUT_CSV, index=False)
    return OUT_CSV


MARKER = "<!-- generated by colophon.gsps_dcmpschk -->"

PREAMBLE = """# Grayscale Softcopy Presentation State: the dcmpschk column, re-closed

The Phase 2 census recorded a dcmpschk pass as a warning class on every
Grayscale Softcopy Presentation State object. dcmpschk prefixes every line it
writes with a severity letter, its own verdict included, and the verdict reads
`W: Test passed.` The census filter tested whether a line began "Test passed"
and so never saw it.

This file reports the re-run. dcmpschk only: the dciodvfy and dicom-validator
columns for this class were unaffected and are read back from the census outputs
rather than recomputed.

Reproduce with `%s`.
""" % CMD


def _severity_letters() -> str:
    return ", ".join("`%s`" % p.strip() for p in census.DCMPSCHK_PREFIXES)


def write_markdown(s: dict, xv: dict) -> Path:
    n = s["objects"]
    total = xv["total_objects"]

    if s["classes"]:
        cls_rows = "\n".join(
            "| `%s` | %s | %s | %s | %s |"
            % (mcid, s["class_meta"][mcid][1], f"{count:,}", f"{n:,}",
               s["class_meta"][mcid][0][:150])
            for mcid, count in s["classes"].most_common())
    else:
        cls_rows = "| | | 0 | %s | none: dcmpschk emitted no finding on any object |" % f"{n:,}"

    here = s["objects_with_finding"]
    n_err_classes = sum(1 for m in s["class_meta"]
                        if s["class_meta"][m][1].upper().startswith("ERROR"))
    xrows = []
    for v in sorted(xv["validators"]):
        d = xv["validators"][v]
        xrows.append("| %s | %s | %s | %s | %s |"
                     % (v, f"{d['objects_lower_bound']:,}",
                        "exact" if d["exact"] else "lower bound",
                        f"{d['classes']:,}", f"{d['error_classes']:,}"))
    xrows.append("| %s, this run | %s | exact | %s | %s |"
                 % (VALIDATOR, f"{here:,}", f"{len(s['classes']):,}",
                    f"{n_err_classes:,}"))

    # An exact agreement count needs a per-object join, which the census
    # aggregates do not carry. When dcmpschk flags nothing it is silent on every
    # object, so the intersection collapses to the other tool's silent count and
    # is exact. When it flags something, say so rather than estimate.
    agree = []
    for v in sorted(xv["validators"]):
        d = xv["validators"][v]
        flagged = d["objects_lower_bound"]
        if here == 0:
            same = total - flagged
            cell = "%s of %s (%.1f percent)" % (f"{same:,}", f"{total:,}",
                                                100.0 * same / total)
        else:
            cell = "not derivable from the census aggregates"
        agree.append("| %s | %s | %s | %s |"
                     % (v, f"{flagged:,}", f"{here:,}", cell))

    rc = ", ".join("%s on %s objects" % (k, f"{v:,}")
                   for k, v in sorted(s["returncodes"].items()))

    # The narrative sentence is derived from the same counters as the tables, so
    # it cannot drift away from them.
    verdict = []
    for v in sorted(xv["validators"]):
        flagged = xv["validators"][v]["objects_lower_bound"]
        if here == 0 and flagged == 0:
            verdict.append("dcmpschk and %s agree on all %s objects: neither "
                           "emits anything." % (v, f"{total:,}"))
        elif here == 0 and flagged == total:
            verdict.append("dcmpschk and %s disagree on all %s objects: %s "
                           "emits at least one message class on every object "
                           "that dcmpschk passes. The disagreement runs in one "
                           "direction only, because dcmpschk flags none."
                           % (v, f"{total:,}", v))
        else:
            verdict.append("dcmpschk flags %s objects and %s flags %s of %s. "
                           "An object level agreement count is not derivable "
                           "from the census aggregates."
                           % (f"{here:,}", v, f"{flagged:,}", f"{total:,}"))
    verdict = "\n\n".join(verdict)

    manifest_total = len(gsps_series())
    retried = s.get("failed_at_least_once", 0)
    retry_note = ("" if not retried else
                  " %s series failed to fetch during the run and succeeded on "
                  "retry, so they are in the counts above. The failures were "
                  "caused by two copies of this run sharing one work directory "
                  "and are recorded rather than absorbed."
                  % f"{retried:,}")
    if s["series"] >= manifest_total:
        dropped = ("Nothing. All %s GSPS series in the census manifest were "
                   "fetched, validated and deleted, with %s unresolved fetch "
                   "failures and %s read failures.%s"
                   % (f"{manifest_total:,}", f"{s['fetch_failed']:,}",
                      f"{s['read_failed']:,}", retry_note))
    else:
        dropped = ("**This run is incomplete and its counts are not a rate.** "
                   "%s of %s GSPS series in the census manifest were fetched "
                   "and validated, with %s fetch failures and %s read failures. "
                   "The remaining %s were not reached."
                   % (f"{s['series']:,}", f"{manifest_total:,}",
                      f"{s['fetch_failed']:,}", f"{s['read_failed']:,}",
                      f"{manifest_total - s['series']:,}"))

    dupes = s.get("duplicate_lines", 0)
    dupe_note = ("" if not dupes else
                 "\n\nThe records file holds %s repeat records, resolved to one "
                 "per series on read. A second copy of this run was started "
                 "while the first was in flight and both appended to the same "
                 "file, and the failed fetches were retried, which appends "
                 "again. A success supersedes a failure for the same series; "
                 "otherwise the first write is kept. Where the same series was "
                 "measured twice and both attempts succeeded, the two verdicts "
                 "differed on %s of them."
                 % (f"{dupes:,}", f"{s.get('repeat_disagreements', 0):,}"))

    section = f"""## Coverage

{s['series']:,} of the {manifest_total:,} GSPS series in the census manifest,
{n:,} objects. {"Complete." if s['series'] >= manifest_total else
"**Incomplete. The counts below are not a rate.**"}{dupe_note}

## What dcmpschk says, re-run

| objects | passes | non-passes | fetch failures | read failures |
|---|---|---|---|---|
| {n:,} | {s['passed']:,} | {s['failed']:,} | {s['fetch_failed']:,} | {s['read_failed']:,} |

**dcmpschk emits `Test passed.` on {s['passed']:,} of the {n:,} objects it was
run over, out of {manifest_total:,} in the census manifest for this class.**

Exit status was not used to decide anything: dcmpschk returned {rc}.

### Message classes dcmpschk emits

| message_class_id | severity as emitted | objects | of | template |
|---|---|---|---|---|
{cls_rows}

The tool also writes one banner line per object, `Testing: <path>`, naming the
file it was given: {s['banners']:,} banner lines across {n:,} objects. They are
recorded as banners rather than as findings, because the line carries no
diagnostic and its text is a local temporary path. Counted as findings they
produced {xv['dcmpschk_before']['banner_classes']:,} distinct message classes in
the census output, one per object.

### What the census recorded before the fix

The census recorded the verdict line as a warning class on
{xv['dcmpschk_before']['pass_line_recorded_on']:,} objects, and recorded
{xv['dcmpschk_before']['classes']:,} distinct dcmpschk message classes for this
SOP class in total. Both figures are artefacts of the filter, not of the corpus.
The severity letters dcmpschk uses are {_severity_letters()}.

## Cross-validator agreement on the same {total:,} objects

Same bytes, three tools, run separately. The dciodvfy and dicom-validator
columns are read back from `results/phase2/census_message_classes.csv` and
`results/phase2/census_rates.csv`. That file counts objects per message class
rather than per object, so the object counts below are stated as exact only
where the largest single class in an analysis result already covers every object
in it.

| validator | objects carrying at least one message class | basis | distinct classes | of which error severity |
|---|---|---|---|---|
{chr(10).join(xrows)}

| dcmpschk versus | that tool flags | dcmpschk flags | objects both are silent on |
|---|---|---|---|
{chr(10).join(agree)}

{verdict}

No attempt is made here to decide which reading is correct. The three tools were
pointed at the same files and their outputs are reported side by side.

## Floor

No dcmpschk floor exists. Phase 1 measured floors for dciodvfy and
dicom-validator only, on Segmentation, Parametric Map and SR fixtures, and
emitted no presentation state, so there is no known-good GSPS object to measure
a dcmpschk floor against. The rate quoted above is a pass rate rather than a
failure rate: dcmpschk emitted {sum(s['classes'].values()):,} findings across
{n:,} objects, and a floor is subtracted from a count of findings, which here is
already zero.

## What was dropped

{dropped}

Only dcmpschk was run. dciodvfy and dicom-validator were deliberately not
re-run, and the numbers given for them above are the census numbers rather than
new measurements.
"""
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    existing = OUT_MD.read_text(encoding="utf-8") if OUT_MD.exists() else PREAMBLE
    head = existing.split(MARKER)[0].rstrip("\n")
    OUT_MD.write_text("%s\n\n%s\n\n%s" % (head, MARKER, section), encoding="utf-8")
    return OUT_MD


def pending_ledger(s: dict, xv: dict) -> list[dict]:
    """Proposed rows, written to results/pending_ledger/ rather than the ledger.

    Track D does not own results/ledger.csv and does not edit it. The rows are
    emitted in the ledger's own schema so that merging them is a copy, not a
    transcription.
    """
    n, total = s["objects"], xv["total_objects"]
    manifest_total = len(gsps_series())
    dci = xv["validators"].get("dciodvfy", {})
    dv = xv["validators"].get("dicom-validator", {})
    dupe_note = ("" if not s.get("duplicate_lines") else
                 "; %s repeat records resolved to one per series on read, from "
                 "a second copy of the run appending to the same file and from "
                 "retrying the failed fetches, with a success superseding a "
                 "failure for the same series"
                 % f"{s['duplicate_lines']:,}")
    if s["series"] >= manifest_total:
        coverage = ("nothing: all %s GSPS series in the census manifest were "
                    "fetched, validated and deleted, %s unresolved fetch "
                    "failures and %s read failures, %s series recovered on "
                    "retry%s"
                    % (f"{manifest_total:,}", f"{s['fetch_failed']:,}",
                       f"{s['read_failed']:,}",
                       f"{s.get('failed_at_least_once', 0):,}", dupe_note))
    else:
        coverage = ("this run reached %s of the %s GSPS series in the census "
                    "manifest and is incomplete, %s fetch failures and %s read "
                    "failures"
                    % (f"{s['series']:,}", f"{manifest_total:,}",
                       f"{s['fetch_failed']:,}", f"{s['read_failed']:,}"))
    S = dict(section="P2D", section_title="Track D, GSPS dcmpschk column re-closed",
             command=CMD, sop_class=SOP_CLASS,
             validator="dcmpschk",
             validator_version="dcmtk dcmpschk 3.7.0, "
                               "dcmtk-3.7.0-win64-dynamic",
             idc_index_version=ledger.IDC_INDEX_VERSION,
             verified_on="2026-08-02")
    floor_note = ("no dcmpschk floor exists: Phase 1 emitted no presentation "
                  "state fixture and did not run dcmpschk, so there is no "
                  "known-good GSPS object to measure one against. The quoted "
                  "rate is a pass rate and the finding count it would be "
                  "subtracted from is zero")
    return [
        dict(id="D-01",
             claim="dcmpschk passes every Grayscale Softcopy Presentation State "
                   "object in the archive census.",
             status="MEASURED",
             value="dcmpschk emits 'Test passed.' on %s of %s GSPS objects and "
                   "emits %s findings in total"
                   % (f"{s['passed']:,}", f"{n:,}",
                      f"{sum(s['classes'].values()):,}"),
             n=str(s["passed"]), denominator=str(n),
             floor=floor_note,
             source_file="results/phase2/gsps_dcmpschk.csv",
             dropped="%s. Only dcmpschk was re-run: the dciodvfy and "
                     "dicom-validator columns for this class were not touched "
                     "by the defect and are read back from the census outputs"
                     % coverage,
             pinned_by_test="tests/test_gsps_dcmpschk.py::test_pass_count_is_pinned",
             status_note="Exit status was not used: the verdict is parsed from "
                         "the text.",
             **S),
        dict(id="D-02",
             claim="The census recorded a dcmpschk pass as a warning class on "
                   "every GSPS object, because the tool prefixes its own "
                   "verdict with a severity letter.",
             status="MEASURED",
             value="dcmpschk writes 'W: Test passed.'; the census filter tested "
                   "for a line beginning 'Test passed' and recorded the pass as "
                   "a warning class on %s objects"
                   % f"{xv['dcmpschk_before']['pass_line_recorded_on']:,}",
             n=str(xv["dcmpschk_before"]["pass_line_recorded_on"]),
             denominator=str(total),
             floor=floor_note,
             source_file="results/phase2/census_message_classes.csv",
             dropped="nothing",
             derived_from="D-01",
             pinned_by_test="tests/test_gsps_dcmpschk.py::test_pass_line_is_never_a_finding",
             status_note="Fixed in colophon.census.parse_dcmpschk, which this "
                         "track calls, so the rule has one implementation.",
             **S),
        dict(id="D-03",
             claim="dcmpschk's banner line names its input file, and counted as "
                   "a finding it gives every object a message class of its own.",
             status="MEASURED",
             value="the census recorded %s distinct dcmpschk message classes "
                   "for this SOP class, of which %s were the banner "
                   "'Testing: <path>'; the banner is now recorded separately "
                   "and %s banner lines were seen across %s objects"
                   % (f"{xv['dcmpschk_before']['classes']:,}",
                      f"{xv['dcmpschk_before']['banner_classes']:,}",
                      f"{s['banners']:,}", f"{n:,}"),
             n=str(xv["dcmpschk_before"]["banner_classes"]),
             denominator=str(total),
             floor=floor_note,
             source_file="results/phase2/gsps_dcmpschk.csv",
             dropped="nothing: the banner is recorded and counted, not "
                     "discarded",
             derived_from="D-02",
             pinned_by_test="tests/test_gsps_dcmpschk.py::test_banner_is_not_a_finding",
             status_note="The banner text is a local temporary path, so it is a "
                         "property of this harness rather than of the object.",
             **S),
        dict(id="D-04",
             claim="On the same GSPS objects the three validators do not agree, "
                   "and the disagreement runs in one direction.",
             status="MEASURED",
             value="dcmpschk flags %s of %s, dicom-validator flags %s of %s, "
                   "dciodvfy flags %s of %s across %s distinct message classes"
                   % (f"{s['objects_with_finding']:,}", f"{n:,}",
                      f"{dv.get('objects_lower_bound', 0):,}", f"{total:,}",
                      f"{dci.get('objects_lower_bound', 0):,}", f"{total:,}",
                      f"{dci.get('classes', 0):,}"),
             n=str(dci.get("objects_lower_bound", 0)), denominator=str(total),
             validator="dcmpschk, dciodvfy, dicom-validator",
             validator_version="dcmtk dcmpschk 3.7.0; dicom3tools snapshot "
                               "20260701065818; dicom-validator 0.8.2 edition "
                               "2026c in process",
             floor=floor_note,
             source_file="results/phase2/gsps_dcmpschk.csv, "
                         "results/phase2/census_message_classes.csv",
             dropped="%s. The dciodvfy and dicom-validator sides of the "
                     "comparison cover all %s objects and were not recomputed"
                     % (coverage, f"{total:,}"),
             derived_from="D-01",
             pinned_by_test="tests/test_gsps_dcmpschk.py::test_cross_validator_direction",
             status_note="Reported tool versus tool. No adjudication of which "
                         "reading is correct is made or implied. The dciodvfy "
                         "and dicom-validator counts are read back from the "
                         "census outputs and were not recomputed.",
             **{k: v for k, v in S.items()
                if k not in ("validator", "validator_version")}),
    ]


def write_pending(rows: list[dict]) -> Path:
    PENDING.parent.mkdir(parents=True, exist_ok=True)
    unknown = {k for r in rows for k in r} - set(ledger.FIELDS)
    if unknown:
        raise ValueError("proposed ledger rows carry unknown fields: %s"
                         % sorted(unknown))
    PENDING.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    return PENDING


def report() -> dict:
    read = load_records()
    records = read["records"]
    if not records:
        raise RuntimeError("no records at %s. Run --run first." % RECORDS)
    s = summarise(records)
    s.update({k: read[k] for k in ("duplicate_lines", "unparsable_lines",
                                   "repeat_disagreements",
                                   "failed_at_least_once")})
    xv = cross_validator()
    write_csv(rows_from_records(records))
    write_markdown(s, xv)
    write_pending(pending_ledger(s, xv))
    return {"summary": s, "cross": xv}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args(argv)
    if not (args.run or args.report):
        args.run = args.report = True

    if args.run:
        run(args.limit)
    if args.report:
        out = report()
        s, xv = out["summary"], out["cross"]
        print("objects %s, passes %s, non-passes %s, findings %s"
              % (f"{s['objects']:,}", f"{s['passed']:,}", f"{s['failed']:,}",
                 f"{sum(s['classes'].values()):,}"))
        for mcid, count in s["classes"].most_common():
            print("  %-13s %-8s %5d  %s"
                  % (mcid, s["class_meta"][mcid][1], count,
                     s["class_meta"][mcid][0][:100]))
        for v, d in sorted(xv["validators"].items()):
            print("  %-16s flags %s of %s (%s), %s classes"
                  % (v, f"{d['objects_lower_bound']:,}",
                     f"{xv['total_objects']:,}",
                     "exact" if d["exact"] else "lower bound",
                     f"{d['classes']:,}"))
        print("wrote %s, %s, %s" % (OUT_CSV, OUT_MD, PENDING))
    return 0


if __name__ == "__main__":
    sys.exit(main())
