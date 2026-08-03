"""Phase 2 census of the eight non-Segmentation derived classes.

291,604 series, roughly 150 GB. Every object is fetched, validated, recorded and
deleted. Segmentation Storage is out of scope and is never touched.

This is a census, not a sample. No sampling frame is built and none is implied.
If the run is interrupted, the classes that completed are complete, and the
class that was in flight reports how far it got.

**Ordering.** Classes run in the order given by the study design, cheapest total
bytes first, so a usable result exists before the long pass starts. Enhanced SR
is 90 percent of the object count and 93 percent of the bytes, and it runs last
for that reason.

**Resumability.** One append-only JSONL record per object. On restart the
completed SeriesInstanceUIDs are read back and skipped, so a crash resumes
rather than restarts. Nothing is held only in memory.

**Throughput.** dicom-validator is run in process against a standard loaded once,
measured at 0.009 s per object against 0.9 s as a subprocess. A subprocess per
file would have put this census in the region of three days rather than three
hours. dciodvfy has no in-process form and stays a subprocess at 0.032 s per
object.

**Fetch is parallel, validation is serial.** The fetch is I/O bound and s5cmd
parallelises it. Validation is deterministic and single threaded so that the
message classes a given object produces do not depend on scheduling.

Usage:
    python -m colophon.census --manifest
    python -m colophon.census --run [--classes "Real World Value Mapping Storage,..."]
    python -m colophon.census --report
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

from . import floor, ledger, paths
from .paths import CACHE, RESULTS

CMD = "python -m colophon.census --run"
STATE = CACHE / "census"
WORK = STATE / "work"
MANIFEST = STATE / "manifest.csv"
RECORDS = STATE / "records.jsonl"
PHASE2 = RESULTS / "phase2"

MIN_FREE_GB = 20.0
BATCH = 64

# Study-design order: cheapest total bytes first.
CLASS_ORDER = [
    "Real World Value Mapping Storage",
    "Key Object Selection Document Storage",
    "Grayscale Softcopy Presentation State Storage",
    "Parametric Map Storage",
    "Comprehensive SR Storage",
    "Comprehensive 3D SR Storage",
    "RT Structure Set Storage",
    "Enhanced SR Storage",
]
EXCLUDED = "Segmentation Storage"

PROV_TAGS = [
    ("Manufacturer", (0x0008, 0x0070), "dataset"),
    ("ManufacturerModelName", (0x0008, 0x1090), "dataset"),
    ("SoftwareVersions", (0x0018, 0x1020), "dataset"),
    ("DeviceSerialNumber", (0x0018, 0x1000), "dataset"),
    ("ContentCreatorName", (0x0070, 0x0084), "dataset"),
    ("SeriesDescription", (0x0008, 0x103E), "dataset"),
    ("ImplementationVersionName", (0x0002, 0x0013), "file_meta"),
    ("ImplementationClassUID", (0x0002, 0x0012), "file_meta"),
]


# --- manifest -----------------------------------------------------------------
def build_manifest() -> Path:
    from .index import load_index
    version, df = load_index()
    sel = df[df["sop_class_name"].isin(CLASS_ORDER)].copy()
    assert EXCLUDED not in set(sel["sop_class_name"]), "Segmentation is out of scope"
    sel["_order"] = sel["sop_class_name"].map(CLASS_ORDER.index)
    sel = sel.sort_values(["_order", "series_size_MB", "SeriesInstanceUID"])
    out = sel[["sop_class_name", "collection_id", "analysis_result_id",
               "SeriesInstanceUID", "instanceCount", "series_size_MB",
               "series_aws_url", "Manufacturer", "ManufacturerModelName"]]
    STATE.mkdir(parents=True, exist_ok=True)
    out.to_csv(MANIFEST, index=False)
    print("manifest: %s rows, %.2f GB, idc-index %s"
          % (f"{len(out):,}", out["series_size_MB"].sum() / 1024, version))
    for name in CLASS_ORDER:
        sub = out[out.sop_class_name == name]
        print("  %-46s %8s series  %9.2f GB"
              % (name, f"{len(sub):,}", sub["series_size_MB"].sum() / 1024))
    return MANIFEST


# --- validators ---------------------------------------------------------------
class InProcessDicomValidator:
    """dicom-validator with the standard loaded once.

    Its own README disclaims correctness and describes the package as a
    beta-stage proof of concept, and it emits no severity levels. The section
    header it groups findings under is recorded as the severity as emitted.
    """

    def __init__(self, standard_path: str, edition: str = "2026c"):
        from dicom_validator.spec_reader.edition_reader import EditionReader
        self.edition = edition
        self.reader = EditionReader(standard_path)
        self.info = self.reader.load_dicom_info(edition)

    def validate(self, dataset) -> list[dict]:
        """Render findings in the command line tool's own wording.

        `IODValidator.validate` returns a structured `ValidationResult`, not the
        text the CLI prints. Inventing a wording here would give every
        dicom-validator message a different `message_class_id` from the ones
        Phase 1 and the pilot recorded through the CLI, and the two would look
        like different findings. The package's own `LoggingResultHandler`
        renderer is reused so the strings, and therefore the ids, match. A test
        asserts that equality on a fixture object.
        """
        from dicom_validator.validator.iod_validator import IODValidator
        from dicom_validator.validator.error_handler import (
            LoggingResultHandler, tag_name_from_id)

        import logging
        result = IODValidator(dataset, self.info, log_level=50).validate()
        quiet = logging.getLogger("colophon.census.dv")
        quiet.setLevel(logging.CRITICAL)
        handler = LoggingResultHandler(self.info, quiet)
        dictionary = self.info.dictionary
        findings = []
        for module_name, tag_errors in (result.module_errors or {}).items():
            for tag_id, tag_error in sorted((tag_errors or {}).items(),
                                            key=lambda x: x[0]):
                indent = 1 if getattr(tag_id, "parents", None) else 0
                parents = ""
                if indent:
                    parents = " / ".join(tag_name_from_id(p, dictionary)
                                         for p in tag_id.parents)
                body = "Tag %s%s" % (tag_name_from_id(tag_id.tag, dictionary),
                                     handler.error_message(tag_error, indent))
                findings.append({
                    "severity": "ERROR" if tag_error.is_error else "WARNING",
                    "message": ("Module <%s> %s %s" % (module_name, parents, body)
                                if parents else "Module <%s>  %s" % (module_name, body)),
                })
        return findings


DCMPSCHK_PREFIXES = ("W: ", "E: ", "I: ")
DCMPSCHK_BANNER = re.compile(r"^Testing:\s")
DCMPSCHK_PASS = "Test passed"


def strip_dcmpschk_prefix(line: str) -> tuple[str, str]:
    """Split a dcmpschk line into its severity letter and its body.

    The letter has to come off before the body is matched, because dcmpschk
    prefixes every line it writes, its own verdict included.
    """
    if line[:3] in DCMPSCHK_PREFIXES:
        return line[0], line[3:].strip()
    return "", line.strip()


def parse_dcmpschk(text: str) -> dict:
    """Separate dcmpschk's banner and verdict from its findings.

    Two of the lines carry no diagnostic and both were being counted as one.

    The verdict reads `W: Test passed.` A filter testing whether a line starts
    with "Test passed" never sees it, so a pass was recorded as a warning class
    on every conformant presentation state.

    The banner reads `Testing: <path>` and names the input file. Recorded as a
    finding it gives every object a message class of its own, keyed on a local
    temporary path, which is a property of this harness and not of the object.
    It is returned separately rather than discarded so the count stays visible.
    """
    banners, findings, passed = [], [], False
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        letter, body = strip_dcmpschk_prefix(line)
        if DCMPSCHK_BANNER.match(body):
            banners.append(line)
            continue
        if body.startswith(DCMPSCHK_PASS):
            passed = True
            continue
        m = floor.SEVERITY.search(line)
        sev = m.group(1) if m else ("Warning" if letter == "W"
                                    else "Error" if letter == "E"
                                    else "UNCLASSIFIED")
        findings.append({"severity": sev, "message": line})
    return {"banners": banners, "findings": findings, "test_passed": passed}


def run_dcmpschk(path: Path) -> dict:
    """GSPS only. On a Segmentation missing two Type 1 attributes it printed
    'Test passed.', so it is used only for the IOD it was written for."""
    paths.require(paths.DCMPSCHK, "dcmpschk")
    proc = subprocess.run([str(paths.DCMPSCHK), str(path)], capture_output=True,
                          text=True, errors="replace", timeout=300)
    parsed = parse_dcmpschk(proc.stdout + "\n" + proc.stderr)
    return {"validator": "dcmpschk", "returncode": proc.returncode,
            "iod": None, **parsed}


# --- provenance ---------------------------------------------------------------
def _state(value) -> str:
    if value is None:
        return "absent"
    return "empty" if str(value).strip() == "" else "non_empty"


def capture(path: Path) -> dict:
    import pydicom
    ds = pydicom.dcmread(path, stop_before_pixels=True)
    rec = {"sop_instance_uid": str(getattr(ds, "SOPInstanceUID", "")),
           "sop_class_uid": str(getattr(ds, "SOPClassUID", "")),
           "transfer_syntax_uid": str(ds.file_meta.TransferSyntaxUID)}
    for name, tag, where in PROV_TAGS:
        src = ds.file_meta if where == "file_meta" else ds
        el = src.get(tag)
        value = None if el is None else el.value
        rec[name] = "" if value is None else str(value)[:200]
        rec[name + "_state"] = _state(value)
    ces = ds.get((0x0018, 0xA001))
    items = []
    if ces is not None and ces.value:
        for it in ces.value:
            purpose = ""
            p = it.get((0x0040, 0xA170))
            if p is not None and p.value:
                c = p.value[0]
                purpose = "%s,%s,%s" % (getattr(c, "CodeValue", ""),
                                        getattr(c, "CodingSchemeDesignator", ""),
                                        getattr(c, "CodeMeaning", ""))
            items.append({
                "Manufacturer": str(it.get((0x0008, 0x0070), "") and
                                    it[(0x0008, 0x0070)].value or "")[:120],
                "ManufacturerModelName": str(it.get((0x0008, 0x1090), "") and
                                             it[(0x0008, 0x1090)].value or "")[:120],
                "SoftwareVersions": str(it.get((0x0018, 0x1020), "") and
                                        it[(0x0018, 0x1020)].value or "")[:120],
                "PurposeOfReference": purpose,
            })
    rec["ContributingEquipmentSequence_present"] = bool(items)
    rec["ContributingEquipmentSequence_items"] = items
    return rec, ds


# --- fetch --------------------------------------------------------------------
def s5cmd() -> Path:
    from idc_index import IDCClient
    return Path(IDCClient().s5cmdPath)


def fetch_batch(rows: list[dict], dest_root: Path) -> dict:
    """Parallel fetch of one batch via s5cmd's own command runner."""
    dest_root.mkdir(parents=True, exist_ok=True)
    lines = []
    for r in rows:
        d = dest_root / r["SeriesInstanceUID"]
        d.mkdir(parents=True, exist_ok=True)
        lines.append('cp "%s" "%s/"' % (r["series_aws_url"], d.as_posix()))
    cmdfile = dest_root / "_batch.txt"
    cmdfile.write_text("\n".join(lines) + "\n", encoding="utf-8")
    proc = subprocess.run(
        [str(s5cmd()), "--no-sign-request", "--numworkers", "16",
         "run", str(cmdfile)],
        capture_output=True, text=True, errors="replace", timeout=7200)
    cmdfile.unlink(missing_ok=True)
    return {"returncode": proc.returncode, "stderr": proc.stderr[-4000:]}


# --- the run ------------------------------------------------------------------
def completed_uids() -> set[str]:
    done = set()
    if RECORDS.exists():
        with RECORDS.open(encoding="utf-8") as fh:
            for line in fh:
                try:
                    done.add(json.loads(line)["series_instance_uid"])
                except Exception:
                    continue
    return done


def run(classes: list[str] | None, standard_path: str, limit: int | None = None) -> None:
    man = pd.read_csv(MANIFEST)
    if classes:
        man = man[man.sop_class_name.isin(classes)]
    man = man[man.sop_class_name != EXCLUDED]
    done = completed_uids()
    todo = man[~man.SeriesInstanceUID.isin(done)]
    if limit:
        todo = todo.head(limit)
    print("census: %s of %s series remaining (%s already recorded)"
          % (f"{len(todo):,}", f"{len(man):,}", f"{len(done):,}"))
    if todo.empty:
        return

    dv = InProcessDicomValidator(standard_path)
    STATE.mkdir(parents=True, exist_ok=True)
    started = time.time()
    n_done = 0

    with RECORDS.open("a", encoding="utf-8") as sink:
        for start in range(0, len(todo), BATCH):
            batch = todo.iloc[start:start + BATCH].to_dict("records")
            free = paths.free_gb(CACHE)
            if free < MIN_FREE_GB:
                raise RuntimeError("aborting: %.1f GB free, floor is %.0f GB"
                                   % (free, MIN_FREE_GB))
            shutil.rmtree(WORK, ignore_errors=True)
            fetch_batch(batch, WORK)

            for r in batch:
                uid = r["SeriesInstanceUID"]
                d = WORK / uid
                files = sorted(p for p in d.rglob("*") if p.is_file()) if d.exists() else []
                if not files:
                    rec = {"series_instance_uid": uid,
                           "sop_class_name": r["sop_class_name"],
                           "analysis_result_id": r["analysis_result_id"],
                           "collection_id": r["collection_id"],
                           "status": "FETCH_FAILED", "objects": []}
                    sink.write(json.dumps(rec) + "\n")
                    n_done += 1
                    continue
                objects = []
                for f in files:
                    try:
                        prov, ds = capture(f)
                    except Exception as exc:
                        objects.append({"status": "READ_FAILED",
                                        "error": "%s: %s" % (type(exc).__name__, exc)})
                        continue
                    msgs = []
                    rec_d = floor.run_dciodvfy(f)
                    for fi in rec_d["findings"]:
                        t = floor.normalise(fi["message"])
                        msgs.append(["dciodvfy", floor.message_class_id("dciodvfy", t),
                                     fi["severity"], t])
                    try:
                        for fi in dv.validate(ds):
                            t = floor.normalise(fi["message"])
                            msgs.append(["dicom-validator",
                                         floor.message_class_id("dicom-validator", t),
                                         fi["severity"], t])
                    except Exception as exc:
                        msgs.append(["dicom-validator", "TOOL_ERROR", "TOOL_ERROR",
                                     "%s: %s" % (type(exc).__name__, exc)])
                    if r["sop_class_name"] == "Grayscale Softcopy Presentation State Storage":
                        rec_p = run_dcmpschk(f)
                        for fi in rec_p["findings"]:
                            t = floor.normalise(fi["message"])
                            msgs.append(["dcmpschk",
                                         floor.message_class_id("dcmpschk", t),
                                         fi["severity"], t])
                    prov["status"] = "OK"
                    prov["messages"] = msgs
                    prov["dciodvfy_returncode"] = rec_d["returncode"]
                    prov["iod_recognised_as"] = rec_d["iod"] or ""
                    objects.append(prov)
                sink.write(json.dumps({
                    "series_instance_uid": uid,
                    "sop_class_name": r["sop_class_name"],
                    "analysis_result_id": r["analysis_result_id"],
                    "collection_id": r["collection_id"],
                    "declared_Manufacturer": r["Manufacturer"],
                    "declared_ManufacturerModelName": r["ManufacturerModelName"],
                    "status": "OK", "objects": objects}) + "\n")
                n_done += 1
            sink.flush()
            shutil.rmtree(WORK, ignore_errors=True)
            rate = n_done / max(time.time() - started, 1e-6)
            print("  %s/%s  %.1f series/s  eta %.1f h  free %.0f GB"
                  % (f"{n_done:,}", f"{len(todo):,}", rate,
                     (len(todo) - n_done) / max(rate, 1e-9) / 3600, free),
                  flush=True)
    shutil.rmtree(WORK, ignore_errors=True)


# --- reporting ----------------------------------------------------------------
def load_records():
    with RECORDS.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


DUBIOUS_CCN = "Content Creator's Name"


def report() -> dict:
    per_class = Counter()
    per_class_objects = Counter()
    fetch_failed = Counter()
    err_objects = defaultdict(set)
    warn_objects = defaultdict(set)
    classdist = Counter()
    class_meta = {}
    prov_states = Counter()
    ccn_dubious = defaultdict(set)
    ar_key = {}
    ces_present = Counter()

    for r in load_records():
        sop = r["sop_class_name"]
        ar = r.get("analysis_result_id") or "(null)"
        per_class[sop] += 1
        if r["status"] == "FETCH_FAILED":
            fetch_failed[sop] += 1
            continue
        for o in r["objects"]:
            if o.get("status") != "OK":
                continue
            uid = o["sop_instance_uid"]
            per_class_objects[sop] += 1
            ar_key[uid] = (sop, ar)
            ces_present[(sop, bool(o.get("ContributingEquipmentSequence_present")))] += 1
            for name, _, _ in PROV_TAGS:
                prov_states[(sop, name, o.get(name + "_state", "absent"))] += 1
            seen = set()
            for validator, mcid, sev, template in o.get("messages", []):
                key = (validator, mcid)
                if (uid, key) in seen:
                    continue
                seen.add((uid, key))
                class_meta[key] = (template, sev)
                classdist[(sop, ar, validator, mcid)] += 1
                if str(sev).upper().startswith("ERROR") or sev == "FATAL":
                    err_objects[(sop, ar)].add(uid)
                elif str(sev).upper().startswith("WARN"):
                    warn_objects[(sop, ar)].add(uid)
                if DUBIOUS_CCN in template:
                    ccn_dubious[(sop, ar)].add(uid)
    return {"per_class": per_class, "per_class_objects": per_class_objects,
            "fetch_failed": fetch_failed, "err": err_objects, "warn": warn_objects,
            "classdist": classdist, "class_meta": class_meta,
            "prov_states": prov_states, "ccn": ccn_dubious,
            "ar_key": ar_key, "ces": ces_present}


def write_report(rep: dict) -> Path:
    PHASE2.mkdir(parents=True, exist_ok=True)
    objs_by = Counter()
    for uid, (sop, ar) in rep["ar_key"].items():
        objs_by[(sop, ar)] += 1

    rows = []
    for (sop, ar), n in sorted(objs_by.items(), key=lambda x: -x[1]):
        e = len(rep["err"].get((sop, ar), ()))
        w = len(rep["warn"].get((sop, ar), ()))
        c = len(rep["ccn"].get((sop, ar), ()))
        rows.append({"sop_class_name": sop, "analysis_result_id": ar, "objects": n,
                     "objects_with_error_class": e,
                     "pct_error": round(100 * e / n, 2) if n else 0,
                     "objects_with_warning_class": w,
                     "pct_warning": round(100 * w / n, 2) if n else 0,
                     "objects_with_dubious_content_creator": c,
                     "pct_dubious_content_creator": round(100 * c / n, 2) if n else 0})
    # The write-up excludes partial classes, but the CSV did not, so anything
    # reading the CSV directly could pick up a class that is half validated and
    # read it as a rate. The column makes completeness travel with the data.
    totals = class_totals()
    seen_by_class = Counter()
    for (sop, ar), n in objs_by.items():
        seen_by_class[sop] += n
    rates = pd.DataFrame(rows)
    if len(rates):
        rates["class_complete"] = rates["sop_class_name"].map(
            lambda s: bool(seen_by_class.get(s, 0) >= totals.get(s, 0) > 0))
        rates["class_series_recorded"] = rates["sop_class_name"].map(
            lambda s: int(seen_by_class.get(s, 0)))
        rates["class_series_in_manifest"] = rates["sop_class_name"].map(
            lambda s: int(totals.get(s, 0)))
    rates.to_csv(PHASE2 / "census_rates.csv", index=False)

    dist = []
    for (sop, ar, validator, mcid), n in rep["classdist"].items():
        template, sev = rep["class_meta"].get((validator, mcid), ("", ""))
        dist.append({"sop_class_name": sop, "analysis_result_id": ar,
                     "validator": validator, "message_class_id": mcid,
                     "severity_as_emitted": sev, "objects": n,
                     "message_template": template})
    pd.DataFrame(dist).sort_values(["sop_class_name", "objects"],
                                   ascending=[True, False]).to_csv(
        PHASE2 / "census_message_classes.csv", index=False)

    prov = [{"sop_class_name": s, "carrier": c, "state": st, "objects": n}
            for (s, c, st), n in rep["prov_states"].items()]
    pd.DataFrame(prov).sort_values(["sop_class_name", "carrier", "state"]).to_csv(
        PHASE2 / "census_provenance_states.csv", index=False)
    return PHASE2 / "census_rates.csv"


def class_totals() -> dict:
    man = pd.read_csv(MANIFEST, usecols=["sop_class_name"])
    return man["sop_class_name"].value_counts().to_dict()


def write_markdown(rep: dict) -> Path:
    totals = class_totals()
    seen = Counter()
    for uid, (sop, ar) in rep["ar_key"].items():
        seen[sop] += 1
    complete = [c for c in CLASS_ORDER if seen.get(c, 0) >= totals.get(c, 0) > 0]
    partial = [c for c in CLASS_ORDER
               if 0 < seen.get(c, 0) < totals.get(c, 0)]
    pending = [c for c in CLASS_ORDER if seen.get(c, 0) == 0]

    rates = pd.read_csv(PHASE2 / "census_rates.csv")
    mc = pd.read_csv(PHASE2 / "census_message_classes.csv")
    prov = pd.read_csv(PHASE2 / "census_provenance_states.csv")

    def status_table():
        lines = ["| SOP class | in manifest | validated | status |", "|---|---|---|---|"]
        for c in CLASS_ORDER:
            t, s = totals.get(c, 0), seen.get(c, 0)
            state = ("complete" if c in complete
                     else "in flight" if c in partial else "not started")
            lines.append("| %s | %s | %s | %s |" % (c, f"{t:,}", f"{s:,}", state))
        return "\n".join(lines)

    r = rates[rates.sop_class_name.isin(complete)]
    rate_rows = "\n".join(
        "| %s | %s | %s | %s | %.1f | %s | %.1f | %s |"
        % (x.sop_class_name, x.analysis_result_id, f"{x.objects:,}",
           f"{x.objects_with_error_class:,}", x.pct_error,
           f"{x.objects_with_warning_class:,}", x.pct_warning,
           f"{x.objects_with_dubious_content_creator:,}")
        for x in r.itertuples())

    top = (mc[mc.sop_class_name.isin(complete)]
           .groupby(["sop_class_name", "validator", "severity_as_emitted",
                     "message_template"])["objects"].sum().reset_index()
           .sort_values(["sop_class_name", "objects"], ascending=[True, False]))
    cls_rows = "\n".join(
        "| %s | %s | %s | %s | %s |"
        % (x.sop_class_name, x.validator, x.severity_as_emitted,
           f"{x.objects:,}", x.message_template[:150])
        for x in top.groupby("sop_class_name").head(6).itertuples())

    pv = prov[prov.sop_class_name.isin(complete)]
    piv = pv.pivot_table(index=["sop_class_name", "carrier"], columns="state",
                         values="objects", fill_value=0).reset_index()
    for col in ("absent", "empty", "non_empty"):
        if col not in piv:
            piv[col] = 0
    prov_rows = "\n".join(
        "| %s | %s | %d | %d | %d |"
        % (x.sop_class_name, x.carrier, int(x.absent), int(x.empty),
           int(x.non_empty)) for x in piv.itertuples())

    text = f"""# Phase 2 census: the eight non-Segmentation derived classes

Census, not a sample. Every object in scope is fetched, validated, recorded and
deleted. Segmentation Storage is excluded by assertion. Reproduce with
`{CMD}`.

Manifest: **291,604 series, 150.35 GB**, IDC v24. Classes run cheapest bytes
first so a usable result exists before the long pass.

## Coverage, as of this writing

{status_table()}

**Only the classes marked complete are reported below.** A class in flight
reports nothing, because a partial class would read as a rate.

## Error and warning class rates, complete classes

An object counts once for a class of message, not once per message. Rates are
gross: no floor has been subtracted, because the Phase 1 floor sets are
writer-specific and fixture-specific and do not transfer to these writers.

| SOP class | analysis_result_id | objects | with error class | pct | with warning class | pct | dubious ContentCreatorName |
|---|---|---|---|---|---|---|---|
{rate_rows}

## Leading message classes, complete classes

| SOP class | validator | severity | objects | template |
|---|---|---|---|---|
{cls_rows}

## Provenance carriers, three states

Absent, zero length and non-empty are counted separately throughout. Zero length
is a distinct finding: in the two IODs where Enhanced General Equipment is
Mandatory, Manufacturer, ManufacturerModelName, DeviceSerialNumber and
SoftwareVersions are Type 1, so a zero-length value there is a conformance
violation while an absent one in another IOD may not be.

| SOP class | carrier | absent | zero length | non-empty |
|---|---|---|---|---|
{prov_rows}

## What was dropped

Nothing within the completed classes: every series in the manifest for those
classes was fetched and validated. Fetch failures, if any, are recorded in the
records file with status FETCH_FAILED and are visible in the counts above as a
shortfall against the manifest.

Classes marked in flight or not started are exactly that, and no number is
reported for them.
"""
    p = RESULTS / "phase2_census.md"
    p.write_text(text, encoding="utf-8")
    return p


def record_ledger(rep: dict) -> None:
    totals = class_totals()
    seen = Counter()
    for uid, (sop, ar) in rep["ar_key"].items():
        seen[sop] += 1
    complete = [c for c in CLASS_ORDER if seen.get(c, 0) >= totals.get(c, 0) > 0]
    rates = pd.read_csv(PHASE2 / "census_rates.csv")
    prov = pd.read_csv(PHASE2 / "census_provenance_states.csv")

    S = dict(section="P2C", section_title="Phase 2 census, non-Segmentation classes",
             command=CMD, sop_class="eight non-Segmentation derived classes",
             validator="dciodvfy, dicom-validator, dcmpschk on GSPS only",
             validator_version="dicom3tools snapshot 20260701065818; "
                               "dicom-validator 0.8.2 edition 2026c in process; "
                               "dcmtk dcmpschk 3.7.0",
             floor="gross rates only. Phase 1 floor sets are writer-specific "
                   "and fixture-specific and do not transfer to these writers, "
                   "so nothing is subtracted and the rates are labelled gross",
             verified_on="2026-08-02")

    ledger.record_many([
        dict(id="P2C-01", claim="Phase 2 census of the eight non-Segmentation "
             "derived classes is a census, not a sample: every series in the "
             "manifest is fetched, validated and deleted.",
             status="MEASURED" if len(complete) == len(CLASS_ORDER) else "PENDING",
             value="manifest 291,604 series, 150.35 GB; complete: %s; validated "
                   "so far %s objects"
                   % (", ".join("%s %s" % (c, f"{seen.get(c, 0):,}")
                                for c in complete) or "none",
                      f"{sum(seen.values()):,}"),
             n=str(sum(seen.values())), denominator="291,604",
             source_file="results/phase2/census_rates.csv",
             dropped="nothing within completed classes; classes in flight "
                     "report no number at all",
             pinned_by_test="tests/test_census.py::test_no_partial_class_is_reported",
             status_note="Segmentation Storage is out of scope and is excluded "
             "by assertion in the manifest builder.", **S),
        dict(id="P2C-02", claim="Gross error-class and warning-class rates by "
             "SOP class and analysis result, for completed classes.",
             status="MEASURED",
             value="; ".join(
                 "%s/%s %s objects err %.1f%% warn %.1f%%"
                 % (x.sop_class_name.split()[0], x.analysis_result_id,
                    f"{x.objects:,}", x.pct_error, x.pct_warning)
                 for x in rates[rates.sop_class_name.isin(complete)].itertuples()),
             n=str(int(rates[rates.sop_class_name.isin(complete)]["objects"].sum())),
             source_file="results/phase2/census_message_classes.csv",
             dropped="nothing within completed classes",
             status_note="An object counts once per message class, not once per "
             "message, using the Phase 1 normaliser. Rates are gross.", **S),
        dict(id="P2C-03", claim="Provenance carriers are reported in three "
             "states, and zero-length values occur.",
             status="MEASURED",
             value="; ".join(
                 "%s %s zero-length %d"
                 % (x.sop_class_name.split()[0], x.carrier, int(x.objects))
                 for x in prov[(prov.state == "empty")
                               & (prov.sop_class_name.isin(complete))].itertuples()),
             source_file="results/phase2/census_provenance_states.csv",
             derived_from="STD-04",
             dropped="nothing within completed classes",
             pinned_by_test="tests/test_census.py::test_three_state_provenance",
             status_note="Zero length and absent are different findings and are "
             "never merged. Enhanced General Equipment is Mandatory in "
             "Parametric Map, so its four carriers are Type 1 there.", **S),
        dict(id="P2C-04", claim="dcmpschk reports its own success line with a "
             "severity prefix, and a naive filter records a pass as a warning.",
             status="MEASURED",
             value="dcmpschk emits 'W: Test passed.', so a prefix check for "
                   "'Test passed' misses it. The GSPS pass was recorded as a "
                   "warning class on all 1,086 Grayscale Softcopy Presentation "
                   "State objects before the fix",
             source_file="results/phase2/census_message_classes.csv",
             dropped="nothing",
             status_note="Fixed at source. The GSPS class must be re-run before "
             "its dcmpschk column is quoted; its dciodvfy and dicom-validator "
             "columns are unaffected.", **S),
    ])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--classes", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--standard-path", default=r"C:\Users\dekay\dicom-validator")
    args = ap.parse_args(argv)

    if args.manifest:
        build_manifest()
    if args.run:
        classes = [c.strip() for c in args.classes.split(",")] if args.classes else None
        run(classes, args.standard_path, args.limit)
    if args.report:
        rep = report()
        p = write_report(rep)
        md = write_markdown(rep)
        record_ledger(rep)
        print("wrote %s and %s" % (p, md))
        print("ledger: %s" % ledger.summary())
        print("objects recorded: %s"
              % f"{sum(rep['per_class_objects'].values()):,}")
        for sop, n in rep["per_class_objects"].most_common():
            print("  %-46s %8s" % (sop, f"{n:,}"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
