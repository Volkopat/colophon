"""Phase 3: the PRE-06 Segmentation Storage sample, executed.

PRE-06 was approved and `colophon.sample.EXECUTE` was set True. The frame is
unchanged: 21 strata, seed 20260802, registered minimum n = 384, one per-stratum
byte cap, 5,941 series. This module draws against that frame, fetches each
series, validates it, records it and deletes it, and computes the question the
run was commissioned to answer.

**The question.** Of all sampled Segmentation objects, per stratum and per
`analysis_result_id`, what fraction declare `SegmentAlgorithmType (0062,0008)`
as AUTOMATIC or SEMIAUTOMATIC while
`SegmentationAlgorithmIdentificationSequence (0062,0007)` is absent, and what
fraction have it present but incomplete, missing any Type 1 child.

**Absence and incompleteness are never merged, and this is the reason.** STD-02
settled it against PS3.3 2026c: in the Segmentation IOD (0062,0007) is Type 3
with no condition of any kind, so omitting it on an AUTOMATIC segment is
conformant and no validator can flag it. The 1C form exists only in the Height
Map Segmentation Image Module, which Table A.51-1 does not include. Absence is
therefore a gap in the standard. Incompleteness is not: once the sequence is
present, its three Type 1 children are mandatory, and a present sequence missing
any of them is non-conformant. One is a finding about DICOM, the other is a
finding about the object, and a single combined number would be neither.

Both are reported at segment level and at object level, because one object holds
many segments and the two units answer different questions. Every denominator is
stated. Nothing is inferred from a rate.

**Type 1 children of the macro**, PS3.3 2026c section 10.16 Table 10-19, taken
from `colophon.standards` rather than retyped here: `AlgorithmFamilyCodeSequence
(0066,002F)`, `AlgorithmName (0066,0036)`, `AlgorithmVersion (0066,0031)`. The
corrected Type 3 tags are also captured: `AlgorithmParameters (0066,0032)` and
`AlgorithmSource (0024,0202)`. The study brief gave the last two wrongly, and a
scan built on its tags scores AlgorithmSource absent everywhere.

`SegmentAlgorithmName (0062,0009)` is captured beside them. It is Type 1C,
required when the algorithm type is not MANUAL, and it is the one conditional
requirement in the Segmentation IOD that SegmentAlgorithmType triggers.

**Secondary, in the same pass and with no extra fetching.** The full provenance
carrier list per object in three states that are never collapsed to two, absent
/ zero-length / non-empty, and the dciodvfy and dicom-validator message classes
through the Phase 1 parser and normaliser.

Rules this module inherits and does not restate as options:

- **Never gate on exit status.** dciodvfy returns rc=0 on a Segmentation with
  SegmentSequence and Rows deleted. Return codes are recorded, never tested.
- **Severity is matched in both forms**, ` - (Error|Warning) - ` anywhere in the
  line and the line-start `Error - ` form, by `colophon.floor.SEVERITY`.
- **Normalise before counting.** The unit is the distinct
  (SOPInstanceUID, message_class_id) pair, never a raw line.
- **No adjudication.** Message classes are reported gross. Nothing here is
  marked NET, because a NET verdict needs a cited PS3 section and this module
  cites none. Adjudication is a separate pass with two adjudicators.
- **dcmpschk is not run**, per addendum 02: on a Segmentation missing two Type 1
  attributes it printed `Test passed.`, so it is kept to GSPS only. PixelMed
  DicomInstanceValidator is the third conformance arm for this class and the jar
  is absent (V-04), so it is recorded as NOT RUN and never as passed.

Usage:
    python -m colophon.phase3 --manifest
    python -m colophon.phase3 --run
    python -m colophon.phase3 --report
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

from . import census, floor, ledger, paths, sample, standards
from .paths import CACHE, RESULTS

CMD = "python -m colophon.phase3 --run"
STATE = CACHE / "phase3"
WORK = STATE / "work"
MANIFEST = STATE / "manifest.csv"
RECORDS = STATE / "records.jsonl"
GATE = STATE / "byte_gate.json"
PHASE3 = RESULTS / "phase3"

SOP_CLASS = sample.SOP_CLASS

# The disk floor. Checked before every batch, never approached.
MIN_FREE_GB = 20.0
# Peak bytes on disk at any moment. One stratum has a mean series of 847 MB, so
# batching by series count alone would put tens of GB on disk in one step.
BATCH_GB = 8.0
BATCH_MAX_SERIES = 48
FETCH_WORKERS = 16

STANDARD_PATH = r"C:\Users\dekay\dicom-validator"


# --- tags ---------------------------------------------------------------------
def _tag(text: str) -> tuple[int, int]:
    """(0066,002F) -> (0x0066, 0x002F)."""
    group, element = text.strip("()").split(",")
    return (int(group, 16), int(element, 16))


# Read from colophon.standards so there is one source of truth for the macro and
# a test can assert the two agree. Two of these were wrong in the brief.
MACRO = {d["keyword"]: d for d in standards.ALGORITHM_IDENTIFICATION_MACRO}
MACRO_TYPE1 = [k for k, d in MACRO.items() if d["type"] == "1"]
MACRO_TYPE3 = [k for k, d in MACRO.items() if d["type"] == "3"]

SEGMENT_SEQUENCE = _tag("(0062,0002)")
SEGMENT_NUMBER = _tag("(0062,0004)")
SEGMENT_LABEL = _tag("(0062,0005)")
SEGMENT_ALGORITHM_TYPE = _tag("(0062,0008)")
SEGMENT_ALGORITHM_NAME = _tag("(0062,0009)")
ALGORITHM_IDENTIFICATION = _tag("(0062,0007)")

NON_MANUAL = ("AUTOMATIC", "SEMIAUTOMATIC")

# Secondary capture. Order is the order the question asked for them in.
CARRIERS = [
    ("Manufacturer", _tag("(0008,0070)"), "dataset"),
    ("ManufacturerModelName", _tag("(0008,1090)"), "dataset"),
    ("DeviceSerialNumber", _tag("(0018,1000)"), "dataset"),
    ("SoftwareVersions", _tag("(0018,1020)"), "dataset"),
    ("ImplementationVersionName", _tag("(0002,0013)"), "file_meta"),
    ("ImplementationClassUID", _tag("(0002,0012)"), "file_meta"),
    ("ContentCreatorName", _tag("(0070,0084)"), "dataset"),
    ("SeriesDescription", _tag("(0008,103E)"), "dataset"),
]
CONTRIBUTING_EQUIPMENT = _tag("(0018,A001)")
PURPOSE_OF_REFERENCE = _tag("(0040,A170)")

# Shape confounders, addendum 02 section 10 item 6. Captured because frame count
# correlates with writer and would otherwise confound the message counts.
SHAPE = [
    ("NumberOfFrames", _tag("(0028,0008)")),
    ("Rows", _tag("(0028,0010)")),
    ("Columns", _tag("(0028,0011)")),
    ("SegmentationType", _tag("(0062,0001)")),
    ("BitsAllocated", _tag("(0028,0100)")),
    ("DimensionOrganizationType", _tag("(0020,9311)")),
]


# --- three states, never two --------------------------------------------------
def state_of(element) -> str:
    """absent / empty / non_empty, decided from the element, not its value.

    Deciding from the value alone cannot separate the two failure modes that
    matter here. pydicom renders a zero-length text element as `''` and an
    absent one as no element at all, but that equivalence is a property of the
    VR: for a sequence, zero items and no sequence both arrive as something
    falsy. A Type 1 attribute present and empty is a conformance violation and
    an absent one is a different conformance violation, so they are separated at
    the point of reading rather than downstream.
    """
    if element is None:
        return "absent"
    value = element.value
    if value is None:
        return "empty"
    if isinstance(value, (bytes, str)):
        return "empty" if str(value).strip() == "" else "non_empty"
    try:
        return "empty" if len(value) == 0 else "non_empty"
    except TypeError:
        return "empty" if str(value).strip() == "" else "non_empty"


def text_of(element, cap: int = 200) -> str:
    if element is None or element.value is None:
        return ""
    return str(element.value)[:cap]


# --- the algorithm identification descent -------------------------------------
def read_macro_item(item) -> dict:
    """One item of SegmentationAlgorithmIdentificationSequence."""
    out = {}
    for keyword in MACRO:
        tag = _tag(MACRO[keyword]["tag"])
        element = item.get(tag)
        out[keyword] = state_of(element)
        if keyword in ("AlgorithmName", "AlgorithmVersion", "AlgorithmSource"):
            out[keyword + "_value"] = text_of(element, 120)
    families = item.get(_tag(MACRO["AlgorithmFamilyCodeSequence"]["tag"]))
    codes = []
    if families is not None and families.value:
        for code in families.value:
            codes.append("%s,%s,%s" % (
                text_of(code.get(_tag("(0008,0100)")), 32),
                text_of(code.get(_tag("(0008,0102)")), 32),
                text_of(code.get(_tag("(0008,0104)")), 64)))
    out["AlgorithmFamilyCode"] = "; ".join(codes)
    out["missing_type1"] = sorted(k for k in MACRO_TYPE1
                                  if out[k] in ("absent", "empty"))
    out["complete"] = not out["missing_type1"]
    return out


def read_segment(item) -> dict:
    """One item of SegmentSequence, descended, not scanned.

    A flat tag scan cannot reach any of this. Both attributes that decide the
    question live inside SegmentSequence, and the macro lives one level deeper
    again.
    """
    algorithm_type = text_of(item.get(SEGMENT_ALGORITHM_TYPE), 32).strip()
    rec = {
        "segment_number": text_of(item.get(SEGMENT_NUMBER), 8),
        "segment_label": text_of(item.get(SEGMENT_LABEL), 64),
        "SegmentAlgorithmType": algorithm_type,
        "SegmentAlgorithmType_state": state_of(item.get(SEGMENT_ALGORITHM_TYPE)),
        "SegmentAlgorithmName": text_of(item.get(SEGMENT_ALGORITHM_NAME), 120),
        "SegmentAlgorithmName_state": state_of(item.get(SEGMENT_ALGORITHM_NAME)),
    }
    rec["non_manual"] = algorithm_type.upper() in NON_MANUAL

    sequence = item.get(ALGORITHM_IDENTIFICATION)
    if sequence is None:
        rec["identification"] = "absent"
        rec["identification_items"] = 0
        rec["missing_type1"] = []
        return rec
    items = list(sequence.value or [])
    rec["identification_items"] = len(items)
    if not items:
        # Present and carrying nothing. Reported as its own state rather than
        # folded into either absence or incompleteness: it is neither an omitted
        # optional attribute nor a populated one missing a child, and merging it
        # into either would decide a question the standard's text does not.
        rec["identification"] = "present_zero_items"
        rec["missing_type1"] = sorted(MACRO_TYPE1)
        return rec
    read = [read_macro_item(i) for i in items]
    missing = sorted({k for r in read for k in r["missing_type1"]})
    rec["identification"] = "present_complete" if not missing else "present_incomplete"
    rec["missing_type1"] = missing
    rec["macro"] = read
    return rec


def summarise_segments(segments: list[dict]) -> dict:
    """Object-level roll-up. Absence and incompleteness stay in separate keys."""
    non_manual = [s for s in segments if s["non_manual"]]
    by_state = Counter(s["identification"] for s in non_manual)
    out = {
        "n_segments": len(segments),
        "n_non_manual": len(non_manual),
        "algorithm_types": dict(Counter(
            s["SegmentAlgorithmType"] or "(absent)" for s in segments)),
        "segments_ident_absent": by_state.get("absent", 0),
        "segments_ident_present_zero_items": by_state.get("present_zero_items", 0),
        "segments_ident_present_incomplete": by_state.get("present_incomplete", 0),
        "segments_ident_present_complete": by_state.get("present_complete", 0),
        # Type 1C, PS3.3 Table C.8.20-2: required when the type is not MANUAL.
        "segments_algorithm_name_absent": sum(
            1 for s in non_manual if s["SegmentAlgorithmName_state"] == "absent"),
        "segments_algorithm_name_empty": sum(
            1 for s in non_manual if s["SegmentAlgorithmName_state"] == "empty"),
        "missing_type1_children": dict(Counter(
            k for s in non_manual for k in s.get("missing_type1", []))),
    }
    # Object level, both quantifiers, because "an object with the defect" and
    # "an object entirely of the defect" are different claims and the question
    # does not pick one.
    out["any_ident_absent"] = out["segments_ident_absent"] > 0
    out["all_ident_absent"] = bool(non_manual) and out["segments_ident_absent"] == len(non_manual)
    out["any_ident_incomplete"] = out["segments_ident_present_incomplete"] > 0
    out["all_ident_incomplete"] = bool(non_manual) and out["segments_ident_present_incomplete"] == len(non_manual)
    out["any_ident_present_zero_items"] = out["segments_ident_present_zero_items"] > 0
    out["any_ident_complete"] = out["segments_ident_present_complete"] > 0
    out["has_non_manual"] = bool(non_manual)
    return out


# --- per object capture -------------------------------------------------------
def capture(path: Path):
    import pydicom
    ds = pydicom.dcmread(path, stop_before_pixels=True)
    rec = {
        "sop_instance_uid": str(getattr(ds, "SOPInstanceUID", "")),
        "sop_class_uid": str(getattr(ds, "SOPClassUID", "")),
        "transfer_syntax_uid": str(ds.file_meta.TransferSyntaxUID),
    }
    for name, tag, where in CARRIERS:
        source = ds.file_meta if where == "file_meta" else ds
        element = source.get(tag)
        rec[name] = text_of(element)
        rec[name + "_state"] = state_of(element)

    contributing = ds.get(CONTRIBUTING_EQUIPMENT)
    rec["ContributingEquipmentSequence_state"] = state_of(contributing)
    items = []
    if contributing is not None and contributing.value:
        for item in contributing.value:
            purpose = ""
            p = item.get(PURPOSE_OF_REFERENCE)
            if p is not None and p.value:
                code = p.value[0]
                purpose = "%s,%s,%s" % (
                    text_of(code.get(_tag("(0008,0100)")), 32),
                    text_of(code.get(_tag("(0008,0102)")), 32),
                    text_of(code.get(_tag("(0008,0104)")), 64))
            items.append({
                "Manufacturer": text_of(item.get(_tag("(0008,0070)")), 120),
                "ManufacturerModelName": text_of(item.get(_tag("(0008,1090)")), 120),
                "SoftwareVersions": text_of(item.get(_tag("(0018,1020)")), 120),
                "DeviceSerialNumber": text_of(item.get(_tag("(0018,1000)")), 120),
                "PurposeOfReference": purpose,
            })
    rec["ContributingEquipmentSequence_items"] = items

    for name, tag in SHAPE:
        rec[name] = text_of(ds.get(tag), 64)

    sequence = ds.get(SEGMENT_SEQUENCE)
    rec["SegmentSequence_state"] = state_of(sequence)
    segments = [read_segment(i) for i in (sequence.value or [])] if sequence is not None else []
    rec["segments"] = segments
    rec.update(summarise_segments(segments))
    return rec, ds


# --- the draw -----------------------------------------------------------------
def build_manifest() -> pd.DataFrame:
    """Draw against the approved frame and apply the pre-registered byte gate.

    The gate is quoted from the frame and is not reinvented here: the exact byte
    total of the drawn manifest is recomputed from `series_size_MB` and compared
    against the budget, and if it exceeds it the remedy is to lower the
    per-stratum byte cap by 5 percent and shorten the same permutations, never
    to redraw. The draw is nested by construction, so shortening n_h takes a
    prefix of the permutation the full allocation would have used.
    """
    from .index import load_index
    version, df = load_index()
    t = sample.build(df)
    seg, frame, alloc = t["segmentation"], t["strata"], t["allocation"]

    planned_gb = alloc.attrs["expected_MB_total"] / 1024
    cap = alloc.attrs["byte_cap_MB"]
    fired = 0
    while True:
        drawn = sample.draw(seg, alloc, sample.SEED)
        sizes = seg.set_index("SeriesInstanceUID")["series_size_MB"]
        exact_MB = float(sizes.reindex(drawn["SeriesInstanceUID"]).sum())
        if exact_MB <= sample.BUDGET_GB * 1024:
            break
        fired += 1
        cap *= 0.95
        n, _, _ = sample._cost(frame, cap, sample.REGISTERED_N, sample.MIN_RATE_N)
        alloc = alloc.copy()
        alloc["n"] = n.astype(int)
        alloc.attrs["byte_cap_MB"] = cap

    STATE.mkdir(parents=True, exist_ok=True)
    GATE.write_text(json.dumps({
        "idc_version": version,
        "seed": sample.SEED,
        "budget_GB": sample.BUDGET_GB,
        "gate_fired_times": fired,
        "final_byte_cap_MB": cap,
        "exact_manifest_GB": exact_MB / 1024,
        "planned_expected_GB": planned_gb,
        "series": int(len(drawn)),
    }, indent=2), encoding="utf-8")

    columns = ["SeriesInstanceUID", "stratum", "writer", "analysis_result",
               "collection_id", "series_size_MB", "instanceCount",
               "series_aws_url", "Manufacturer", "ManufacturerModelName"]
    out = drawn.merge(seg[columns].drop(columns=["stratum"]),
                      on="SeriesInstanceUID", how="left")
    # Cheapest first, so a usable partial result exists early and the expensive
    # single stratum cannot starve the other twenty.
    out = out.sort_values(["series_size_MB", "SeriesInstanceUID"])
    out["analysis_result_id"] = out["analysis_result"]
    out.to_csv(MANIFEST, index=False)
    print("manifest: %s series, %.2f GB exact, gate fired %d time(s), idc %s"
          % (f"{len(out):,}", exact_MB / 1024, fired, version))
    return out


# --- the run ------------------------------------------------------------------
def completed_uids() -> set[str]:
    done = set()
    if RECORDS.exists():
        with RECORDS.open(encoding="utf-8") as fh:
            for line in fh:
                try:
                    done.add(json.loads(line)["series_instance_uid"])
                except Exception:
                    # A trailing partial line is what an interrupted append
                    # looks like. Skip it rather than crash the resume.
                    continue
    return done


def batches(todo: pd.DataFrame):
    """Byte-capped batches, so peak disk is bounded by BATCH_GB not by series."""
    rows, size = [], 0.0
    for row in todo.to_dict("records"):
        mb = float(row.get("series_size_MB") or 0.0)
        if rows and (size + mb > BATCH_GB * 1024 or len(rows) >= BATCH_MAX_SERIES):
            yield rows
            rows, size = [], 0.0
        rows.append(row)
        size += mb
    if rows:
        yield rows


# Phase 1 runs dciodvfy against three-slice fixtures and 300 s is generous
# there. One stratum here averages 847 MB per series, so the timeout is raised
# for this phase only. `floor.run_dciodvfy` is left alone rather than having its
# default changed, because the Phase 1 floor sets were measured through it and a
# changed default would silently alter the baseline they are compared against.
# The parser and the normaliser are the Phase 1 ones, so message_class_id values
# stay comparable across phases.
DCIODVFY_TIMEOUT = 1800


def validate_object(path: Path, dv) -> tuple[dict, list]:
    """Capture first, validate second, and never let a validator cost the capture.

    The provenance and segment capture is the answer to the question this phase
    was commissioned to ask. A validator that hangs or dies on a large object
    must not take that with it, so each tool is wrapped separately and its
    failure is recorded as a TOOL_ERROR message class rather than discarding
    the object.
    """
    record, ds = capture(path)
    messages = []
    try:
        result = floor._run([str(paths.require(paths.DCIODVFY, "dciodvfy")),
                             str(path)], timeout=DCIODVFY_TIMEOUT)
        iod, findings = floor.parse_dciodvfy(result["stdout"] + "\n" + result["stderr"])
        for finding in findings:
            template = floor.normalise(finding["message"])
            messages.append(["dciodvfy", floor.message_class_id("dciodvfy", template),
                             finding["severity"], template])
        # Recorded, never tested. dciodvfy returns rc=0 on a Segmentation with
        # SegmentSequence and Rows deleted.
        record["dciodvfy_returncode"] = result["returncode"]
        record["iod_recognised_as"] = iod or ""
    except Exception as exc:
        messages.append(["dciodvfy", "TOOL_ERROR", "TOOL_ERROR",
                         "%s: %s" % (type(exc).__name__, exc)])
        record["dciodvfy_returncode"] = ""
        record["iod_recognised_as"] = ""
    try:
        for finding in dv.validate(ds):
            template = floor.normalise(finding["message"])
            messages.append(["dicom-validator",
                             floor.message_class_id("dicom-validator", template),
                             finding["severity"], template])
    except Exception as exc:
        messages.append(["dicom-validator", "TOOL_ERROR", "TOOL_ERROR",
                         "%s: %s" % (type(exc).__name__, exc)])
    record["messages"] = messages
    record["status"] = "OK"
    return record, messages


def run(limit: int | None = None) -> None:
    if not MANIFEST.exists():
        build_manifest()
    man = pd.read_csv(MANIFEST)
    done = completed_uids()
    todo = man[~man.SeriesInstanceUID.isin(done)]
    if limit:
        todo = todo.head(limit)
    print("phase3: %s of %s series remaining (%s already recorded), %.2f GB to go"
          % (f"{len(todo):,}", f"{len(man):,}", f"{len(done):,}",
             todo["series_size_MB"].sum() / 1024), flush=True)
    if todo.empty:
        return

    dv = census.InProcessDicomValidator(STANDARD_PATH)
    STATE.mkdir(parents=True, exist_ok=True)
    started, n_done = time.time(), 0
    total = len(todo)

    with RECORDS.open("a", encoding="utf-8") as sink:
        for batch in batches(todo):
            need = sum(float(r.get("series_size_MB") or 0.0) for r in batch) / 1024
            free = paths.free_gb(CACHE)
            if free < MIN_FREE_GB or free < need + MIN_FREE_GB:
                raise RuntimeError(
                    "aborting: %.1f GB free, floor is %.0f GB and this batch "
                    "needs %.1f GB" % (free, MIN_FREE_GB, need))
            shutil.rmtree(WORK, ignore_errors=True)
            census.fetch_batch(batch, WORK)

            for row in batch:
                uid = row["SeriesInstanceUID"]
                folder = WORK / uid
                files = (sorted(p for p in folder.rglob("*") if p.is_file())
                         if folder.exists() else [])
                head = {"series_instance_uid": uid,
                        "stratum": row["stratum"],
                        "writer": row["writer"],
                        "analysis_result_id": row["analysis_result"],
                        "collection_id": row["collection_id"],
                        "declared_MB": float(row.get("series_size_MB") or 0.0),
                        "instance_count_declared": int(row.get("instanceCount") or 0)}
                if not files:
                    sink.write(json.dumps(
                        dict(head, status="FETCH_FAILED", objects=[])) + "\n")
                else:
                    objects = []
                    for f in files:
                        try:
                            record, _ = validate_object(f, dv)
                        except Exception as exc:
                            record = {"status": "READ_FAILED",
                                      "error": "%s: %s" % (type(exc).__name__, exc)}
                        objects.append(record)
                    sink.write(json.dumps(
                        dict(head, status="OK", objects=objects)) + "\n")
                # Checkpoint per series, not per batch. An interrupted run loses
                # at most the series in flight.
                sink.flush()
                shutil.rmtree(folder, ignore_errors=True)
                n_done += 1

            shutil.rmtree(WORK, ignore_errors=True)
            rate = n_done / max(time.time() - started, 1e-6)
            print("  %s/%s  %.2f series/s  eta %.1f h  free %.0f GB"
                  % (f"{n_done:,}", f"{total:,}", rate,
                     (total - n_done) / max(rate, 1e-9) / 3600, free), flush=True)
    shutil.rmtree(WORK, ignore_errors=True)


def load_records():
    if not RECORDS.exists():
        return
    with RECORDS.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args(argv)

    if not sample.EXECUTE:
        raise SystemExit(
            "colophon.sample.EXECUTE is False. PRE-06 is not approved and this "
            "module must not run.")
    if args.manifest:
        build_manifest()
    if args.run:
        run(args.limit)
    if args.report:
        from .phase3_report import report
        report()
    if not (args.manifest or args.run or args.report):
        ap.error("one of --manifest, --run, --report is required")
    return 0


if __name__ == "__main__":
    sys.exit(main())
