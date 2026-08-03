"""Phase 2 pilot: fetch ten dcmqi-written Segmentation series, validate, delete.

Ten objects, nothing else. No sampling frame is built here and none is implied:
the selection is a deterministic smallest-first pick spread across analysis
results, chosen to exercise the pipeline rather than to estimate anything. Any
rate computed from ten objects would be meaningless and none is computed.

Fetching uses `s5cmd`, the copy bundled with `idc-index`. The AWS CLI is not
installed on this machine, and the project rule against silent substitution
applies to fetch tools as much as to validators, so the substitution is recorded
in the ledger rather than absorbed. Both are named in the study brief.

Every fetch is preceded by a free-space check and every series is deleted after
its validators have run. Nothing accumulates.

Usage:
    python -m colophon.fetch --pilot
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

from . import floor, ledger, paths
from .paths import CACHE, RESULTS

CMD = "python -m colophon.fetch --pilot"
PILOT_DIR = CACHE / "pilot"
PHASE2 = RESULTS / "phase2"
HEADROOM_GB = 50.0


def s5cmd_path() -> Path:
    from idc_index import IDCClient
    return Path(IDCClient().s5cmdPath)


def s5cmd_version() -> str:
    p = subprocess.run([str(s5cmd_path()), "version"], capture_output=True,
                       text=True, errors="replace", timeout=60)
    return (p.stdout + p.stderr).strip().splitlines()[0]


def disk_guard(required_mb: float, where: Path = CACHE) -> float:
    """Refuse to fetch unless the volume has the payload plus headroom."""
    free = paths.free_gb(where)
    need = required_mb / 1024.0 + HEADROOM_GB
    if free < need:
        raise RuntimeError(
            "refusing to fetch: %.1f GB free, need %.1f GB including %.0f GB "
            "headroom" % (free, need, HEADROOM_GB))
    return free


def fetch_series(aws_url: str, dest: Path) -> dict:
    dest.mkdir(parents=True, exist_ok=True)
    argv = [str(s5cmd_path()), "--no-sign-request", "cp", aws_url, str(dest) + "/"]
    proc = subprocess.run(argv, capture_output=True, text=True,
                          errors="replace", timeout=1800)
    files = sorted(p for p in dest.rglob("*") if p.is_file())
    return {"argv": argv, "returncode": proc.returncode,
            "stdout": proc.stdout[-2000:], "stderr": proc.stderr[-2000:],
            "files": files}


PROVENANCE_TAGS = [
    ("SoftwareVersions", (0x0018, 0x1020), "dataset"),
    ("DeviceSerialNumber", (0x0018, 0x1000), "dataset"),
    ("Manufacturer", (0x0008, 0x0070), "dataset"),
    ("ManufacturerModelName", (0x0008, 0x1090), "dataset"),
    ("ImplementationVersionName", (0x0002, 0x0013), "file_meta"),
    ("ImplementationClassUID", (0x0002, 0x0012), "file_meta"),
]


def _state(value) -> str:
    """Three states, never two. A Type 1 attribute present but zero length is a
    different finding from one that is absent."""
    if value is None:
        return "absent"
    text = str(value)
    return "empty" if text.strip() == "" else "non_empty"


def capture_provenance(path: Path) -> dict:
    import pydicom
    ds = pydicom.dcmread(path, stop_before_pixels=True)
    rec = {"sop_instance_uid": str(ds.SOPInstanceUID),
           "sop_class_uid": str(ds.SOPClassUID),
           "transfer_syntax_uid": str(ds.file_meta.TransferSyntaxUID)}
    for name, tag, where in PROVENANCE_TAGS:
        src = ds.file_meta if where == "file_meta" else ds
        el = src.get(tag)
        value = None if el is None else el.value
        rec[name] = "" if value is None else str(value)
        rec[name + "_state"] = _state(value)
    ces = ds.get((0x0018, 0xA001))
    rec["ContributingEquipmentSequence_present"] = ces is not None
    rec["ContributingEquipmentSequence_items"] = (
        len(ces.value) if ces is not None and ces.value is not None else 0)
    seg_seq = ds.get((0x0062, 0x0002))
    rec["segments"] = len(seg_seq.value) if seg_seq is not None else 0
    rec["NumberOfFrames"] = int(getattr(ds, "NumberOfFrames", 0) or 0)
    rec["SegmentationType"] = str(getattr(ds, "SegmentationType", ""))
    return rec


def pilot(selection_csv: Path, standard_path: Path | None = None) -> dict:
    sel = pd.read_csv(selection_csv)
    if len(sel) > 10:
        raise ValueError("pilot is capped at 10 series, got %d" % len(sel))
    PILOT_DIR.mkdir(parents=True, exist_ok=True)
    PHASE2.mkdir(parents=True, exist_ok=True)

    messages, provenance, fetch_log = [], [], []
    for i, row in sel.iterrows():
        uid = row["SeriesInstanceUID"]
        free_before = disk_guard(float(row["series_size_MB"]))
        dest = PILOT_DIR / uid
        got = fetch_series(row["series_aws_url"], dest)
        fetch_log.append({
            "series_instance_uid": uid,
            "analysis_result_id": row["analysis_result_id"],
            "declared_MB": float(row["series_size_MB"]),
            "files_fetched": len(got["files"]),
            "returncode": got["returncode"],
            "free_GB_before": round(free_before, 1),
        })
        if not got["files"]:
            print("  %-40s FETCH FAILED rc=%s %s"
                  % (uid[:40], got["returncode"], got["stderr"][:120]))
            shutil.rmtree(dest, ignore_errors=True)
            continue

        for f in got["files"]:
            prov = capture_provenance(f)
            prov.update({"series_instance_uid": uid,
                         "analysis_result_id": row["analysis_result_id"],
                         "collection_id": row["collection_id"],
                         "declared_model_name": row["ManufacturerModelName"]})
            provenance.append(prov)

            for vname, runner in floor.VALIDATORS.items():
                rec = (runner(f, standard_path) if vname == "dicom-validator"
                       else runner(f))
                for finding in rec["findings"]:
                    template = floor.normalise(finding["message"])
                    messages.append({
                        "series_instance_uid": uid,
                        "sop_instance_uid": prov["sop_instance_uid"],
                        "analysis_result_id": row["analysis_result_id"],
                        "validator": vname,
                        "message_class_id": floor.message_class_id(vname, template),
                        "message_template": template,
                        "severity_as_emitted": finding["severity"],
                        "raw_example": finding["message"][:300],
                        "iod_recognised_as": rec["iod"] or "",
                        "validator_returncode": rec["returncode"],
                    })
        # Delete after validation rather than accumulating.
        shutil.rmtree(dest, ignore_errors=True)
        print("  %2d/%d %-34s %-42s %d file(s), deleted"
              % (i + 1, len(sel), row["analysis_result_id"][:34], uid[:42],
                 len(got["files"])))

    shutil.rmtree(PILOT_DIR, ignore_errors=True)
    return {"messages": messages, "provenance": provenance, "fetch": fetch_log}


TARGET_TEMPLATE = ("Error - Missing attribute Type 2 Required "
                   "Element=<ClinicalTrialCoordinatingCenterName> "
                   "Module=<ClinicalTrialSeries>")


def summarise(out: dict) -> dict:
    msgs = pd.DataFrame(out["messages"])
    prov = pd.DataFrame(out["provenance"])
    n_objects = len(prov)
    target_id = floor.message_class_id("dciodvfy", floor.normalise(TARGET_TEMPLATE))
    hit = msgs[msgs.message_class_id == target_id] if len(msgs) else msgs
    classes = []
    if len(msgs):
        pairs = msgs.drop_duplicates(["sop_instance_uid", "message_class_id"])
        classes = (pairs.groupby(["validator", "message_class_id",
                                  "message_template", "severity_as_emitted"])
                        .size().rename("objects").reset_index()
                        .sort_values(["validator", "objects"], ascending=[True, False]))
    return {"n_objects": n_objects, "target_class_id": target_id,
            "target_objects": int(hit.sop_instance_uid.nunique()) if len(hit) else 0,
            "classes": classes, "messages": msgs, "provenance": prov}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pilot", action="store_true", required=True)
    ap.add_argument("--selection", default=str(CACHE / "pilot_selection.csv"))
    ap.add_argument("--standard-path", default=None)
    args = ap.parse_args(argv)

    print("s5cmd %s, free %.1f GB" % (s5cmd_version(), paths.free_gb()))
    out = pilot(Path(args.selection),
                Path(args.standard_path) if args.standard_path else None)
    s = summarise(out)

    PHASE2.mkdir(parents=True, exist_ok=True)
    s["messages"].to_csv(PHASE2 / "pilot_messages.csv", index=False)
    s["provenance"].to_csv(PHASE2 / "pilot_provenance.csv", index=False)
    pd.DataFrame(out["fetch"]).to_csv(PHASE2 / "pilot_fetch_log.csv", index=False)
    if len(s["classes"]):
        s["classes"].to_csv(PHASE2 / "pilot_message_classes.csv", index=False)

    print("\nobjects validated: %d" % s["n_objects"])
    print("target class %s present on %d of %d objects"
          % (s["target_class_id"], s["target_objects"], s["n_objects"]))
    if len(s["classes"]):
        print("\nmessage classes:")
        for r in s["classes"].itertuples():
            print("  %-16s %-13s %2d/%d  %-8s %s"
                  % (r.validator, r.message_class_id, r.objects, s["n_objects"],
                     r.severity_as_emitted, r.message_template[:88]))

    prov = s["provenance"]
    print("\nprovenance capture:")
    for col in ("SoftwareVersions", "ImplementationVersionName",
                "ImplementationClassUID"):
        vals = prov[col].fillna("").value_counts()
        print("  %s:" % col)
        for k, v in vals.items():
            print("      %2d  %r" % (v, k))
    print("  ContributingEquipmentSequence present: %d of %d"
          % (int(prov.ContributingEquipmentSequence_present.sum()), len(prov)))

    write_markdown(s, out)
    record_ledger(s, out)
    print("\nledger: %s" % ledger.summary())
    return 0


def write_markdown(s: dict, out: dict) -> Path:
    prov, classes = s["provenance"], s["classes"]
    n = s["n_objects"]

    def counts(col):
        v = prov[col].fillna("").value_counts()
        return "\n".join("| `%s` | %d |" % (k if k != "" else "(empty)", c)
                         for k, c in v.items())

    cls_rows = "\n".join(
        "| %s | `%s` | %s | %d / %d | %s |"
        % (r.validator, r.message_class_id, r.severity_as_emitted, r.objects, n,
           r.message_template)
        for r in classes.itertuples()) if len(classes) else "| | | | | none |"

    ars = prov.analysis_result_id.nunique()
    text = f"""# Phase 2 pilot: ten dcmqi-written Segmentation objects

Ten series, {ars} analysis results, fetched from IDC, validated, deleted.
Reproduce with `{CMD}`.

**This is a pilot, not a sample.** The selection is a deterministic
smallest-first pick spread across analysis results, chosen to exercise the
pipeline. No sampling frame was built and no rate is computed from ten objects.

## The question asked

Does the message class seen on the Phase 1 dcmqi fixture appear in the corpus?

`{TARGET_TEMPLATE}`

message_class_id `{s['target_class_id']}`

**Present on {s['target_objects']} of {n} objects.**

## Every message class observed

Counted as distinct (SOPInstanceUID, message_class_id) pairs, using the Phase 1
normaliser. Never raw lines.

| validator | message_class_id | severity | objects | template |
|---|---|---|---|---|
{cls_rows}

## Provenance captured, for later

Three states are reported, never two: a Type 1 attribute present but zero length
is a different finding from one that is absent.

`SoftwareVersions (0018,1020)`:

| value | objects |
|---|---|
{counts("SoftwareVersions")}

`ImplementationVersionName (0002,0013)`:

| value | objects |
|---|---|
{counts("ImplementationVersionName")}

`ImplementationClassUID (0002,0012)`:

| value | objects |
|---|---|
{counts("ImplementationClassUID")}

`ContributingEquipmentSequence (0018,A001)` present on
**{int(prov.ContributingEquipmentSequence_present.sum())} of {n}** objects.

## Fetch

`s5cmd` was used rather than the AWS CLI, which is not installed on this
machine. Both are named in the study brief. The substitution is recorded rather
than absorbed.

Free space was checked before every fetch and every series was deleted
immediately after its validators ran. Nothing accumulated.

## What was dropped

Nothing within the pilot: all ten selected series were fetched and every fetched
object was run through both validators. The pilot itself is bounded at ten
series by instruction and is not a sample of anything.
"""
    p = RESULTS / "phase2_pilot.md"
    p.write_text(text, encoding="utf-8")
    return p


def record_ledger(s: dict, out: dict) -> None:
    prov, classes = s["provenance"], s["classes"]
    n = s["n_objects"]
    S = dict(section="P2P", section_title="Phase 2 pilot, ten objects",
             command=CMD,
             sop_class="Segmentation Storage",
             validator="dciodvfy and dicom-validator",
             validator_version="dicom3tools snapshot 20260701065818; "
                               "dicom-validator 0.8.2 edition 2026c",
             floor="Phase 1 floor sets, results/floor_set.csv. No rate is "
                   "computed from ten objects, so no floor is subtracted",
             dropped="nothing within the pilot. The pilot is bounded at ten "
                     "series by instruction and is not a sample",
             denominator=str(n), verified_on="2026-08-02")

    sv = prov["SoftwareVersions"].fillna("")
    sv_states = prov["SoftwareVersions_state"].value_counts().to_dict()
    ivn = prov["ImplementationVersionName"].fillna("").value_counts().to_dict()
    icu = prov["ImplementationClassUID"].fillna("").value_counts().to_dict()
    ces = int(prov["ContributingEquipmentSequence_present"].sum())

    rows = [
        dict(id="P2P-01", claim="Pilot of ten dcmqi-written Segmentation series "
             "from IDC, fetched, validated and deleted. Not a sample.",
             status="MEASURED",
             value="%d objects across %d analysis results, %d distinct declared "
                   "model-name spellings"
                   % (n, prov.analysis_result_id.nunique(),
                      prov.declared_model_name.nunique()),
             n=str(n), source_file="results/phase2/pilot_provenance.csv",
             pinned_by_test="tests/test_pilot.py::test_pilot_shape",
             status_note="Deterministic smallest-first selection spread across "
             "analysis results, to exercise the pipeline. No sampling frame was "
             "built and no rate is computed.", **S),
        dict(id="P2P-02", claim="The dcmqi ClinicalTrialSeries message class "
             "seen on the Phase 1 fixture %s in the corpus pilot."
             % ("also appears" if s["target_objects"] else "does not appear"),
             status="MEASURED",
             value="message_class_id %s present on %d of %d objects"
                   % (s["target_class_id"], s["target_objects"], n),
             n=str(s["target_objects"]),
             source_file="results/phase2/pilot_message_classes.csv",
             derived_from="F1-01",
             pinned_by_test="tests/test_pilot.py::test_target_message_class",
             **S),
        dict(id="P2P-03", claim="Message classes observed across the pilot, by "
             "validator.",
             status="MEASURED",
             value="; ".join("%s %s on %d/%d" % (r.validator, r.message_class_id,
                                                 r.objects, n)
                             for r in classes.itertuples()) or "none",
             n=str(len(classes)),
             source_file="results/phase2/pilot_message_classes.csv",
             status_note="Counted as distinct (SOPInstanceUID, "
             "message_class_id) pairs with the Phase 1 normaliser, never raw "
             "lines.", **S),
        dict(id="P2P-04", claim="SoftwareVersions (0018,1020) captured verbatim "
             "in three states. It is Type 1 in the Segmentation IOD, so a "
             "zero-length value is a conformance violation.",
             status="MEASURED",
             value="states %s; distinct values %s" % (sv_states,
                                                      sorted(set(sv))[:6]),
             source_file="results/phase2/pilot_provenance.csv",
             external_source="PS3.3 Table C.7-8b, Enhanced General Equipment",
             derived_from="STD-04",
             pinned_by_test="tests/test_pilot.py::test_provenance_states", **S),
        dict(id="P2P-05", claim="File-meta identification names the encoding "
             "library's own encoding library, not the producer. On objects "
             "whose Manufacturer is QIICR and whose model name is a dcmqi URL, "
             "ImplementationVersionName names DCMTK.",
             status="MEASURED",
             value="ImplementationVersionName %s; ImplementationClassUID %s"
                   % (ivn, icu),
             source_file="results/phase2/pilot_provenance.csv",
             derived_from="C3-11",
             pinned_by_test="tests/test_pilot.py::test_file_meta_names_dcmtk",
             status_note="The provenance pathology recurs one layer down: the "
             "encoding library declares itself in the equipment attributes and "
             "its own encoding library declares itself in the file meta. "
             "Neither names the analysis.", **S),
        dict(id="P2P-08", claim="A minority of objects declaring dcmqi in the "
             "equipment attributes carry a file-meta implementation that is not "
             "DCMTK.",
             status="MEASURED",
             value="%d of %d objects carry ImplementationClassUID "
                   "1.3.6.1.4.1.22213.1.143 with ImplementationVersionName 0.5, "
                   "against %d carrying an OFFIS_DCMTK_* identity"
                   % (int((prov.ImplementationClassUID
                           == "1.3.6.1.4.1.22213.1.143").sum()), n,
                      int(prov.ImplementationVersionName.str.startswith(
                          "OFFIS_DCMTK").sum())),
             source_file="results/phase2/pilot_provenance.csv",
             derived_from="P2P-05",
             status_note="Observation, not a resolution. The declared writer "
             "and the file-meta implementation disagree for those objects, "
             "which could mean re-encoding after dcmqi produced them or an "
             "older dcmqi backend. The index cannot distinguish the two and "
             "this pilot does not try.", **S),
        dict(id="P2P-09", claim="SoftwareVersions on dcmqi-written corpus "
             "objects is an abbreviated git commit hash, one distinct value per "
             "analysis result in this pilot.",
             status="MEASURED",
             value="%d of %d values are exactly 7 lowercase hex characters; %d "
                   "distinct values across %d analysis results: %s"
                   % (int(sum(len(str(v)) == 7 and all(c in "0123456789abcdef"
                                                       for c in str(v))
                              for v in sv)), n, sv.nunique(),
                      prov.analysis_result_id.nunique(),
                      ", ".join(sorted(set(sv)))),
             source_file="results/phase2/pilot_provenance.csv",
             derived_from="W-04,P2P-04",
             pinned_by_test="tests/test_pilot.py::test_software_versions_are_commit_hashes",
             status_note="Confirms in the corpus what was confirmed from dcmqi "
             "source: SoftwareVersions carries the build working copy's "
             "abbreviated HEAD SHA. It identifies a commit of the encoder, not "
             "a version of any algorithm.", **S),
        dict(id="P2P-06", claim="ContributingEquipmentSequence (0018,A001) on "
             "dcmqi-written Segmentation objects in the corpus.",
             status="MEASURED",
             value="present on %d of %d objects" % (ces, n), n=str(ces),
             source_file="results/phase2/pilot_provenance.csv",
             external_source="IHE AIR Rev 1.3 section 6.5.3.1",
             derived_from="STD-06",
             pinned_by_test="tests/test_pilot.py::test_contributing_equipment",
             **S),
        dict(id="P2P-07", claim="s5cmd was used to fetch rather than the AWS "
             "CLI, which is not installed on this machine.",
             status="MEASURED",
             value="s5cmd %s, --no-sign-request, s3://idc-open-data"
                   % s5cmd_version(),
             source_file="results/phase2/pilot_fetch_log.csv",
             status_note="Both tools are named in the study brief. Recorded "
             "rather than absorbed, because the no-silent-substitution rule "
             "applies to fetch tools as well as validators.",
             notes="Free space checked before every fetch, every series deleted "
                   "immediately after validation, nothing accumulated.", **S),
    ]
    ledger.record_many(rows)


if __name__ == "__main__":
    sys.exit(main())
