"""Table 1 and Table 2, generated from measured artefacts rather than typed.

**Table 1, the writer census, recomputed from census output.** The version in
`results/table1_writers.md` infers a writer from the two equipment attributes
the idc-index dataframe carries, because that is all Phase 0 had. Phase 2 opened
the files, so the file meta is available. ImplementationClassUID (0002,0012) and
ImplementationVersionName (0002,0013) are written by the library that serialised
the dataset, not by whoever filled in Manufacturer, and for two of the toolkits
here their values are compile-time constants that can be read out of the
toolkit's own source. That makes the file meta the stronger evidence about who
wrote the bytes, and it makes the two sources comparable: where they name
different toolkits the object carries both claims and one of them is wrong.

The file meta is not a claim about who produced the analysis. It names the
serialising library, which for an archive that re-encodes on ingest is the last
writer rather than the first. That is the whole reason a disagreement count is
worth having.

**Completeness.** A SOP class appears in Table 1 only when the number of series
recorded in the census is at least the number the manifest holds for that class.
A partial class would read as a rate over the whole class, so partial classes
are named in a coverage table and contribute nothing else.

**Reading the census while it writes.** `_cache/census/records.jsonl` is appended
to by a running census. It is opened read-only, and any line that does not parse
is skipped and counted, because the last line of a file being appended to can be
half written. The skipped count is reported in the output and in the ledger, so
a truncated read cannot pass as a full one.

**Table 2, the floor set per writer per message class.** One row per validator
message class in each writer's floor, including the cells where a writer drew
nothing, because a floor of zero is a measurement and an absent row is not.
Cells dcmqi could not emit are marked single-writer and non-transferable rather
than left to look like agreement.

Usage:
    python -m colophon.tables
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

from . import census, floor, ledger
from .index import _fmt, _md_table
from .paths import RESULTS
from .writers import UNKNOWN_WRITER, writer_of

CMD = "python -m colophon.tables"

MANUSCRIPT = RESULTS / "manuscript"
RECORDS = census.RECORDS
MANIFEST = census.MANIFEST
FLOOR_SET = RESULTS / "floor_set.csv"
CORPUS_CLASSES = RESULTS / "phase2" / "census_message_classes.csv"
CORPUS_PROVENANCE = RESULTS / "phase2" / "census_provenance_states.csv"

TRACK = "F2"

# --- what a file-meta identity names -----------------------------------------
# Ordered. Each rule carries the basis on which it qualifies and whether that
# basis was read out of the toolkit's source or only inferred from the values
# observed, so a reader can reject one rule without rejecting the table. Only
# the source-confirmed rules are allowed to generate a disagreement.
#
# ImplementationClassUID is checked before ImplementationVersionName because it
# is a registered OID under the vendor's own arc, while the version name is a
# free-text string. Where the two name different toolkits the object is labelled
# internally inconsistent rather than silently resolved in favour of either.
FILE_META_RULES: list[dict] = [
    {"writer": "highdicom",
     "uid": "1.2.826.0.1.3680043.9.7433.1.1",
     "version_name": r"^highdicom",
     "basis": "highdicom/base.py, SOPClass.__init__ sets "
              "file_meta.ImplementationClassUID to the literal "
              "1.2.826.0.1.3680043.9.7433.1.1 and "
              "file_meta.ImplementationVersionName to f'highdicom{__version__}'. "
              "Neither is conditional and neither is settable by a caller.",
     "status": "CONFIRMED from source, highdicom 0.28.1 as installed"},
    {"writer": "PixelMed",
     "uid": "1.3.6.1.4.1.5962.99.2",
     "version_name": r"^PIXELMEDJAVA",
     "basis": "com/pixelmed/dicom/VersionAndConstants.java: uidRoot "
              "1.3.6.1.4.1.5962, uidQualifierForThisToolkit 99, "
              "uidQualifierForImplementationClassUID 2, and "
              "implementationVersionName = PIXELMEDJAVA + softwareVersion, "
              "where softwareVersion is 001. Applied by "
              "com/pixelmed/dicom/FileMetaInformation.java.",
     "status": "CONFIRMED from source, pixelmed source release 20260608"},
    {"writer": "DCMTK",
     "uid": None,
     "version_name": r"^OFFIS_DCMTK",
     "basis": "DCMTK self-identifies in ImplementationVersionName as "
              "OFFIS_DCMTK_<version>. dcmqi serialises through DCMTK, so this "
              "names the backend and not the caller.",
     "status": "asserted from observed values, NOT source confirmed"},
    {"writer": "dcm4che",
     "uid": None,
     "version_name": r"^dcm4che",
     "basis": "the toolkit's own name and release appear verbatim in "
              "ImplementationVersionName, for example dcm4che-1.4.27.",
     "status": "asserted from observed values, NOT source confirmed"},
]

# ContributingEquipmentSequence is checked only when the file meta resolves to
# nothing. It is weaker evidence about who serialised the file, because the
# sequence is part of the dataset and survives re-encoding, but it is stronger
# than nothing and highdicom's entry is a source-confirmed constant.
CES_RULES: list[dict] = [
    {"writer": "highdicom",
     "manufacturer": "Highdicom open-source contributors",
     "basis": "highdicom/base_content.py, ContributingEquipment.for_highdicom, "
              "appended unconditionally by every concrete constructor.",
     "status": "CONFIRMED from source, highdicom 0.28.1 as installed"},
]

NO_FILE_META = "no file-meta evidence"
INCONSISTENT = "file meta internally inconsistent"
UNRESOLVED = "unresolved implementation %s / %s"

# --- what the equipment attributes predict about the file meta ----------------
# A disagreement is only meaningful where the toolkit named by the equipment
# attributes has a file-meta signature we can state independently. Toolkits with
# no registered expectation are counted separately and are never scored as
# agreeing or disagreeing, because there is nothing to agree with.
EXPECTED_FILE_META: dict[str, dict] = {
    "highdicom": {"expects": "highdicom",
                  "status": "CONFIRMED from source, highdicom 0.28.1 as installed"},
    "PixelMed": {"expects": "PixelMed",
                 "status": "CONFIRMED from source, pixelmed source release 20260608"},
    "dcmqi": {"expects": "DCMTK",
              "status": "asserted from observed values, NOT source confirmed"},
}

AGREE = "agree"
DISAGREE = "disagree"
NO_EXPECTATION = "no expectation registered"
EQUIPMENT_SILENT = "equipment attributes name no toolkit"


def _rx(pattern: str):
    return re.compile(pattern, re.IGNORECASE)


def attribute_file_meta(obj: dict) -> tuple[str, str, str]:
    """Return (writer, evidence attribute, verification status) for one object.

    The evidence attribute is returned alongside the writer so that a reader can
    see which of the three carriers actually decided the label, rather than
    having to trust an aggregate.
    """
    uid = (obj.get("ImplementationClassUID") or "").strip()
    ivn = (obj.get("ImplementationVersionName") or "").strip()

    by_uid = next((r for r in FILE_META_RULES if r["uid"] and r["uid"] == uid), None)
    by_ivn = next((r for r in FILE_META_RULES
                   if r["version_name"] and ivn and _rx(r["version_name"]).search(ivn)),
                  None)
    if by_uid and by_ivn and by_uid["writer"] != by_ivn["writer"]:
        return INCONSISTENT, "ImplementationClassUID and ImplementationVersionName", \
            "conflict, not resolved here"
    if by_uid:
        return by_uid["writer"], "ImplementationClassUID (0002,0012)", by_uid["status"]
    if by_ivn:
        return by_ivn["writer"], "ImplementationVersionName (0002,0013)", by_ivn["status"]

    for item in obj.get("ContributingEquipmentSequence_items") or []:
        manufacturer = (item.get("Manufacturer") or "").strip()
        for rule in CES_RULES:
            if manufacturer == rule["manufacturer"]:
                return rule["writer"], \
                    "ContributingEquipmentSequence (0018,A001) item Manufacturer", \
                    rule["status"]

    if not uid and not ivn:
        return NO_FILE_META, "none", "no evidence"
    return (UNRESOLVED % (uid or "absent", ivn or "absent"),
            "ImplementationClassUID (0002,0012) and ImplementationVersionName (0002,0013)",
            "recorded verbatim, not resolved to a toolkit")


def verdict_of(equipment_writer: str, file_meta_writer: str) -> tuple[str, str]:
    """Return (verdict, the status of the expectation the verdict rests on)."""
    if equipment_writer == UNKNOWN_WRITER:
        return EQUIPMENT_SILENT, "not applicable"
    expectation = EXPECTED_FILE_META.get(equipment_writer)
    if expectation is None:
        return NO_EXPECTATION, "not applicable"
    if file_meta_writer == expectation["expects"]:
        return AGREE, expectation["status"]
    return DISAGREE, expectation["status"]


# --- the census read ----------------------------------------------------------
def scan(path: Path = RECORDS) -> dict:
    """One streaming pass over records.jsonl, accumulating counters only.

    Nothing is materialised. The completed census is 291,604 series and holding
    the parsed records in memory would be several gigabytes for no benefit, and
    this has to run against a file that is still growing.
    """
    stat = path.stat()
    out = {
        "path": str(path),
        "size_bytes": stat.st_size,
        "mtime": _dt.datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
        "read_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "lines_seen": 0,
        "lines_skipped": 0,
        "series": Counter(),
        "objects": Counter(),
        "not_ok_objects": Counter(),
        "cells": Counter(),
        "identity_equipment": defaultdict(Counter),
        "equipment_identity": defaultdict(Counter),
        "analysis_results": defaultdict(set),
        "collections": defaultdict(set),
        "inconsistent": 0,
    }
    with path.open(encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            out["lines_seen"] += 1
            try:
                record = json.loads(line)
            except ValueError:
                out["lines_skipped"] += 1
                continue
            if not isinstance(record, dict) or "sop_class_name" not in record:
                out["lines_skipped"] += 1
                continue
            sop = record["sop_class_name"]
            out["series"][sop] += 1
            analysis_result = record.get("analysis_result_id")
            if analysis_result is None or analysis_result != analysis_result:
                analysis_result = "(null)"
            out["analysis_results"][sop].add(str(analysis_result))
            out["collections"][sop].add(str(record.get("collection_id")))
            for obj in record.get("objects") or []:
                if obj.get("status") != "OK":
                    out["not_ok_objects"][sop] += 1
                    continue
                out["objects"][sop] += 1
                writer, evidence, status = attribute_file_meta(obj)
                if writer == INCONSISTENT:
                    out["inconsistent"] += 1
                equipment = writer_of(obj.get("Manufacturer") or None,
                                      obj.get("ManufacturerModelName") or None)
                verdict, expectation_status = verdict_of(equipment, writer)
                out["cells"][(sop, writer, evidence, status, equipment, verdict,
                              expectation_status)] += 1
                identity = ((obj.get("ImplementationClassUID") or "absent").strip(),
                            (obj.get("ImplementationVersionName") or "absent").strip())
                declared = ((obj.get("Manufacturer") or "").strip(),
                            (obj.get("ManufacturerModelName") or "").strip())
                out["identity_equipment"][(sop, identity)][declared] += 1
                # Keyed on the resolved writer, not on the raw identity, so that
                # three releases of one toolkit do not read as three writers.
                out["equipment_identity"][(sop, declared)][writer] += 1
    return out


def completeness(scanned: dict) -> pd.DataFrame:
    """Recorded series against manifest series, per SOP class.

    Completeness is judged on series rather than on objects, because the
    manifest is a list of series and the census skips a series it has already
    recorded. A class that is complete therefore stays complete and its counts
    stay fixed while the rest of the census runs.
    """
    totals = census.class_totals()
    rows = []
    for sop in census.CLASS_ORDER:
        in_manifest = int(totals.get(sop, 0))
        recorded = int(scanned["series"].get(sop, 0))
        rows.append({
            "sop_class_name": sop,
            "series_in_manifest": in_manifest,
            "series_recorded": recorded,
            "objects_recorded": int(scanned["objects"].get(sop, 0)),
            "complete": bool(in_manifest > 0 and recorded >= in_manifest),
            "state": ("complete" if in_manifest > 0 and recorded >= in_manifest
                      else "in flight" if recorded else "not started"),
        })
    return pd.DataFrame(rows)


# --- Table 1 ------------------------------------------------------------------
TABLE1_FIELDS = ["sop_class_name", "writer", "writer_evidence",
                 "writer_evidence_status", "equipment_writer", "verdict",
                 "expectation_status", "objects", "pct_of_sop_class"]


def table1(scanned: dict, complete: list[str]) -> pd.DataFrame:
    per_class = {sop: scanned["objects"][sop] for sop in complete}
    rows = []
    for key, n in scanned["cells"].items():
        sop, writer, evidence, status, equipment, verdict, expectation = key
        if sop not in per_class:
            continue
        rows.append({
            "sop_class_name": sop,
            "writer": writer,
            "writer_evidence": evidence,
            "writer_evidence_status": status,
            "equipment_writer": equipment,
            "verdict": verdict,
            "expectation_status": expectation,
            "objects": n,
            "pct_of_sop_class": round(100 * n / per_class[sop], 2),
        })
    frame = pd.DataFrame(rows, columns=TABLE1_FIELDS)
    return frame.sort_values(["sop_class_name", "objects"],
                             ascending=[True, False]).reset_index(drop=True)


def table1_by_writer(t1: pd.DataFrame) -> pd.DataFrame:
    grouped = (t1.groupby(["sop_class_name", "writer", "writer_evidence_status"])
                 .agg(objects=("objects", "sum")).reset_index())
    totals = grouped.groupby("sop_class_name")["objects"].transform("sum")
    grouped["pct_of_sop_class"] = (100 * grouped["objects"] / totals).round(2)
    return grouped.sort_values(["sop_class_name", "objects"],
                               ascending=[True, False]).reset_index(drop=True)


def disagreements(t1: pd.DataFrame) -> pd.DataFrame:
    scored = t1[t1.verdict.isin([AGREE, DISAGREE])]
    if scored.empty:
        return pd.DataFrame(columns=["sop_class_name", "equipment_writer", "writer",
                                     "verdict", "expectation_status", "objects"])
    return (scored[["sop_class_name", "equipment_writer", "writer", "verdict",
                    "expectation_status", "objects"]]
            .sort_values(["verdict", "objects"], ascending=[True, False])
            .reset_index(drop=True))


def identity_spread(scanned: dict, complete: list[str]) -> pd.DataFrame:
    """How many distinct declared equipment pairs sit behind one file-meta identity.

    A one-to-one mapping would mean the two carriers say the same thing in two
    places. A many-to-one mapping means one serialising implementation is
    carrying several different producer claims, which is the shape a re-encoding
    step leaves behind.

    Aggregated over the complete SOP classes and no others, for the same reason
    the rest of Table 1 is: a count that mixes a finished class with one still
    running is not a count of anything.
    """
    wanted = set(complete)
    merged: dict[tuple, Counter] = defaultdict(Counter)
    for (sop, identity), declared in scanned["identity_equipment"].items():
        if sop not in wanted:
            continue
        merged[identity].update(declared)
    rows = []
    for identity, declared in merged.items():
        rows.append({
            "implementation_class_uid": identity[0],
            "implementation_version_name": identity[1],
            "objects": sum(declared.values()),
            "distinct_declared_equipment_pairs": len(declared),
            # Semicolons, not pipes: a pipe in a cell ends the cell in markdown.
            "declared_equipment": "; ".join(
                "%s / %s (%s)" % (a or "(empty)", b or "(empty)", _fmt(n))
                for (a, b), n in declared.most_common()),
        })
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    return frame.sort_values("objects", ascending=False).reset_index(drop=True)


def equipment_spread(scanned: dict, complete: list[str]) -> pd.DataFrame:
    """The reverse mapping: one declared producer, more than one writer.

    Reported only where the writers are different toolkits. Several releases of
    one toolkit behind one declared producer is ordinary and says nothing; two
    different toolkits behind one declared producer says the declared value does
    not determine what wrote the file.
    """
    wanted = set(complete)
    merged: dict[tuple, Counter] = defaultdict(Counter)
    for (sop, declared), writers in scanned["equipment_identity"].items():
        if sop in wanted:
            merged[declared].update(writers)
    rows = []
    for declared, writers in merged.items():
        if len(writers) < 2:
            continue
        rows.append({
            "declared_Manufacturer": declared[0] or "(empty)",
            "declared_ManufacturerModelName": declared[1] or "(empty)",
            "objects": sum(writers.values()),
            "distinct_file_meta_writers": len(writers),
            "file_meta_writers": "; ".join("%s (%s)" % (w, _fmt(n))
                                           for w, n in writers.most_common()),
        })
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    return frame.sort_values("objects", ascending=False).reset_index(drop=True)


def _clip(value: str, limit: int) -> str:
    """Shorten for a markdown cell, and say so. The CSV always carries the whole
    value, so a truncated cell must be visibly truncated rather than look like a
    short value."""
    text = str(value)
    return text if len(text) <= limit else text[:limit].rstrip() + " ..."


def write_table1(scanned: dict, cover: pd.DataFrame, t1: pd.DataFrame,
                 spread: pd.DataFrame, reverse: pd.DataFrame) -> tuple[Path, Path]:
    MANUSCRIPT.mkdir(parents=True, exist_ok=True)
    csv_path = MANUSCRIPT / "table1_writers.csv"
    t1.to_csv(csv_path, index=False)

    complete = cover[cover.complete]
    partial = cover[~cover.complete]
    by_writer = table1_by_writer(t1)
    dis = disagreements(t1)

    n_objects = int(t1["objects"].sum())
    n_disagree = int(dis.loc[dis.verdict == DISAGREE, "objects"].sum()) if len(dis) else 0
    n_agree = int(dis.loc[dis.verdict == AGREE, "objects"].sum()) if len(dis) else 0
    n_scored = n_agree + n_disagree
    silent = t1[t1.verdict == EQUIPMENT_SILENT]
    n_silent = int(silent["objects"].sum())
    named_by_file_meta = int(silent.loc[
        ~silent.writer.str.startswith(("unresolved", NO_FILE_META)), "objects"].sum())

    cover_view = cover.copy()
    cover_view["series_in_manifest"] = cover_view["series_in_manifest"].map(_fmt)
    cover_view["series_recorded"] = cover_view["series_recorded"].map(_fmt)
    cover_view["objects_recorded"] = cover_view["objects_recorded"].map(_fmt)

    by_writer_view = by_writer.copy()
    by_writer_view["objects"] = by_writer_view["objects"].map(_fmt)
    by_writer_view["pct_of_sop_class"] = by_writer_view["pct_of_sop_class"].map(
        lambda v: "%.2f" % v)

    dis_view = dis.copy()
    if len(dis_view):
        dis_view["objects"] = dis_view["objects"].map(_fmt)

    spread_view = spread.copy()
    if len(spread_view):
        spread_view["objects"] = spread_view["objects"].map(_fmt)

    reverse_view = reverse.copy()
    if len(reverse_view):
        reverse_view["objects"] = reverse_view["objects"].map(_fmt)

    rules = "\n".join(
        "%d. `%s` equals `%s`, or `%s` matches `%s`, names **%s**. %s Status: %s"
        % (i + 1, "ImplementationClassUID (0002,0012)", r["uid"] or "n/a",
           "ImplementationVersionName (0002,0013)", r["version_name"],
           r["writer"], r["basis"], r["status"])
        for i, r in enumerate(FILE_META_RULES))
    ces_rules = "\n".join(
        "- a `ContributingEquipmentSequence (0018,A001)` item whose `Manufacturer` "
        "is exactly `%s` names **%s**. %s Status: %s"
        % (r["manufacturer"], r["writer"], r["basis"], r["status"])
        for r in CES_RULES)
    expectations = "\n".join(
        "| %s | %s | %s |" % (k, v["expects"], v["status"])
        for k, v in EXPECTED_FILE_META.items())

    text = f"""# Table 1: the writer census, computed from census output

Every number here is read out of the objects, not out of the index. Reproduce
with `{CMD}`.

Source: `_cache/census/records.jsonl`, {_fmt(scanned['size_bytes'])} bytes as of
{scanned['mtime']}, read at {scanned['read_at']}. The census appends to that file
while this runs, so the read is deliberately defensive: {_fmt(scanned['lines_seen'])}
lines were seen and {_fmt(scanned['lines_skipped'])} were skipped as unparseable.

This supersedes the writer census in `results/table1_writers.md`, which infers a
writer from `Manufacturer` and `ManufacturerModelName` alone because those are
the only equipment attributes the idc-index dataframe carries. That table is
provisional by its own statement. This one is not, for the classes it covers.

## Which SOP classes are in this table

A class appears only when the census has recorded at least as many series as the
manifest holds for it. Completeness is judged on series, not objects, because
the manifest is a list of series and the census skips a series it has already
recorded, so a complete class stays complete and its counts stay fixed while the
rest of the census runs.

{_md_table(cover_view, ["sop_class_name", "series_in_manifest", "series_recorded", "objects_recorded", "state"])}

**{len(complete)} of {len(cover)} classes are complete** and are the whole of this
table. The {len(partial)} classes that are not complete contribute nothing, not
even a partial count.

## The attribution rule

Applied per object, in this order. The first rule that matches decides, and the
attribute that decided is recorded per row in the CSV.

{rules}

If none of those match, and only then:

{ces_rules}

If nothing matches, the object is labelled `unresolved implementation
<ImplementationClassUID> / <ImplementationVersionName>` with the two values
recorded verbatim. It is not resolved to a toolkit and it is not merged with any
other identity.

Where `ImplementationClassUID` and `ImplementationVersionName` name different
toolkits, the object is labelled `{INCONSISTENT}` rather than resolved in favour
of either. That happened on {_fmt(scanned['inconsistent'])} objects.

The file meta names the library that serialised the dataset. It is the strongest
available evidence about what wrote the bytes, and it is not evidence about what
produced the analysis. For an archive that re-encodes on ingest it names the
last writer rather than the first, which is exactly why the disagreement below
is worth counting.

## Writer per SOP class

{_md_table(by_writer_view, ["sop_class_name", "writer", "writer_evidence_status", "objects", "pct_of_sop_class"])}

The full cross-tabulation, one row per SOP class, file-meta writer and
equipment-attribute writer, is in `table1_writers.csv`.

## Where the equipment attributes said nothing

{_fmt(n_silent)} of {_fmt(n_objects)} objects carry equipment attributes that the
Phase 0 rule cannot attribute to any toolkit. The file meta names a toolkit for
{_fmt(named_by_file_meta)} of them. That is the measured gain from opening the
files, and it is the number the Phase 0 table said would have to be resolved in
Phase 2.

## Where the two sources disagree

An object is scored only when the toolkit named by the equipment attributes has
a file-meta signature that can be stated independently of this corpus. There are
three such toolkits:

| equipment-attribute writer | expected file-meta writer | how the expectation was established |
|---|---|---|
{expectations}

Everything else is counted as `{NO_EXPECTATION}` and is never scored as agreeing
or disagreeing, because there is nothing to agree with.

{_md_table(dis_view, ["sop_class_name", "equipment_writer", "writer", "verdict", "expectation_status", "objects"]) if len(dis_view) else "No object in the complete classes carries an equipment attribution with a registered expectation."}

**{_fmt(n_disagree)} of {_fmt(n_scored)} scored objects disagree.** The
disagreement rests on a signature that is a compile-time constant in the named
toolkit's own source, so it is not a matter of a loose pattern: the file meta on
those objects is not the file meta that toolkit writes.

What follows from that is left open. Either something other than the named
toolkit serialised the file, or the file meta was rewritten after the named
toolkit wrote it. Nothing measured here distinguishes the two, and this table
does not choose between them.

This is the same shape as the Phase 2 pilot finding in ledger row P2P-08, where
objects declaring dcmqi in the equipment attributes carried a file-meta
implementation that was not DCMTK.

## One implementation identity, several declared producers

Aggregated over the complete classes only. Every declared pair is listed, with
its object count, because a truncated list here would hide exactly the spread
the table exists to show.

{_md_table(spread_view, ["implementation_class_uid", "implementation_version_name", "objects", "distinct_declared_equipment_pairs", "declared_equipment"]) if len(spread_view) else "n/a"}

A one-to-one mapping would mean the two carriers say the same thing twice. A
many-to-one mapping means one serialising implementation is carrying several
different producer claims.

The reverse direction holds too. These declared producers sit behind more than
one file-meta writer, counting toolkits rather than releases, so several
releases of one toolkit behind one declared producer is not listed here:

{_md_table(reverse_view, ["declared_Manufacturer", "declared_ManufacturerModelName", "objects", "distinct_file_meta_writers", "file_meta_writers"]) if len(reverse_view) else "None. Every declared producer in the complete classes sits behind exactly one file-meta writer."}

## Two caveats on the equipment-attribute rule

The Phase 0 rule is reused verbatim, from `colophon.writers.writer_of`, so that
the comparison is against the rule as registered rather than against a rule
tuned for this table. Two of its behaviours are visible here and are reported
rather than corrected:

- its pattern for QIICR Reporting is `fedorov/reporting|slicer`, and the
  `slicer` alternative matches any 3D Slicer extension URL. Objects whose
  `Manufacturer` is `https://github.com/QIICR/Slicer-SUVFactorCalculator` are
  therefore labelled `QIICR Reporting via 3D Slicer` on a substring alone.
- it was written against the index, where `Manufacturer` and
  `ManufacturerModelName` are the series-level values. Here it is fed each
  object's own values, which is the same rule on stronger input.

## What was dropped

Classes that are not complete are excluded entirely and are named in the
coverage table above with their recorded counts. Segmentation Storage is outside
the census scope altogether and appears nowhere in this table.

{_fmt(scanned['lines_skipped'])} lines of `records.jsonl` were skipped as
unparseable and {_fmt(sum(scanned['not_ok_objects'].values()))} objects were
skipped because their census status was not OK. Both counts are gross, over the
whole file, not only over the complete classes.
"""
    md_path = MANUSCRIPT / "table1_writers.md"
    md_path.write_text(text, encoding="utf-8")
    return md_path, csv_path


# --- Table 2 ------------------------------------------------------------------
TABLE2_FIELDS = ["writer", "writer_version", "sop_class", "validator",
                 "message_class_id", "severity_as_emitted", "message_template",
                 "cell_single_writer", "single_writer_reason", "shared_with",
                 "cell_jaccard", "cell_comparable", "corpus_objects",
                 "corpus_context"]


def floor_cells() -> list[tuple[str, str]]:
    """Every (writer, sop_class) the fixture actually emitted.

    Taken from `colophon.floor.OBJECTS` rather than from the rows of
    floor_set.csv, because a writer that drew no messages at all produces no
    rows and would otherwise vanish from the table. A floor of zero is the most
    important cell in the whole measurement.
    """
    seen, out = set(), []
    for writer, sop_class, _ in floor.OBJECTS:
        if (writer, sop_class) not in seen:
            seen.add((writer, sop_class))
            out.append((writer, sop_class))
    return out


def corpus_context() -> dict:
    """Per message class, how many census objects drew the same class.

    Read from the census report snapshot rather than recomputed, so that Table 2
    quotes the same artefact the Phase 2 write-up quotes. The snapshot is older
    than records.jsonl, so its per-class denominators are reported with it and a
    zero is never presented as evidence of absence.
    """
    if not CORPUS_CLASSES.exists():
        return {"by_class": {}, "denominators": {}, "snapshot": "missing"}
    frame = pd.read_csv(CORPUS_CLASSES)
    denominators = {}
    if CORPUS_PROVENANCE.exists():
        prov = pd.read_csv(CORPUS_PROVENANCE)
        anchor = prov[prov.carrier == "ImplementationClassUID"]
        denominators = anchor.groupby("sop_class_name")["objects"].sum().to_dict()
    by_class: dict[str, dict[str, int]] = defaultdict(dict)
    grouped = frame.groupby(["message_class_id", "sop_class_name"])["objects"].sum()
    for (mcid, sop), n in grouped.items():
        by_class[mcid][sop] = int(n)
    stat = CORPUS_CLASSES.stat()
    return {
        "by_class": dict(by_class),
        "denominators": {k: int(v) for k, v in denominators.items()},
        "snapshot": _dt.datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
        "rows": int(len(frame)),
    }


def overlaps(rows: list[dict]) -> pd.DataFrame:
    """Jaccard per SOP class and validator, recomputed from floor_set.csv.

    Recomputed rather than parsed out of `results/floor_overlap.md`, so that the
    figure in the manuscript table and the figure in the Phase 1 write-up cannot
    drift apart. Four decimal places, because the SEG BINARY value under
    dicom-validator is 6/7 and rounding it to three hides that it is not 1.0,
    which is the value ledger row F1-03-prev was retired for.
    """
    out = []
    for sop_class in floor.CLASSES:
        for validator in floor.VALIDATORS:
            s1 = {r["message_class_id"] for r in rows
                  if r["writer"] == floor.W1 and r["sop_class"] == sop_class
                  and r["validator"] == validator}
            s2 = {r["message_class_id"] for r in rows
                  if r["writer"] == floor.W2 and r["sop_class"] == sop_class
                  and r["validator"] == validator}
            comparable = sop_class not in floor.W2_EMISSION_GAPS
            out.append({
                "sop_class": sop_class,
                "validator": validator,
                "comparable": "yes" if comparable else "no, dcmqi cannot emit it",
                "highdicom_classes": len(s1),
                "dcmqi_classes": len(s2),
                "shared": len(s1 & s2),
                "union": len(s1 | s2),
                "jaccard": ("%.4f" % floor.jaccard(s1, s2)) if comparable else "n/a",
                "vacuous": "yes" if comparable and not s1 and not s2 else "no",
            })
    return pd.DataFrame(out)


def table2(rows: list[dict], corpus: dict) -> pd.DataFrame:
    by_cell: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        by_cell[(r["writer"], r["sop_class"], r["validator"])].append(r)

    sets: dict[tuple, set] = {}
    for (writer, sop_class, validator), items in by_cell.items():
        sets[(writer, sop_class, validator)] = {i["message_class_id"] for i in items}

    ov = {(o["sop_class"], o["validator"]): o for o in overlaps(rows).to_dict("records")}
    versions = {r["writer"]: r["writer_version"] for r in rows}

    out = []
    for writer, sop_class in floor_cells():
        other = floor.W2 if writer == floor.W1 else floor.W1
        gap = floor.W2_EMISSION_GAPS.get(sop_class)
        single = gap is not None
        for validator in floor.VALIDATORS:
            cell = by_cell.get((writer, sop_class, validator), [])
            other_set = sets.get((other, sop_class, validator), set())
            summary = ov.get((sop_class, validator), {})
            base = {
                "writer": writer,
                "writer_version": versions.get(writer, ""),
                "sop_class": sop_class,
                "validator": validator,
                "cell_single_writer": "yes" if single else "no",
                "single_writer_reason": gap or "",
                "cell_jaccard": summary.get("jaccard", ""),
                "cell_comparable": summary.get("comparable", ""),
            }
            if not cell:
                out.append({**base,
                            "message_class_id": "",
                            "severity_as_emitted": "",
                            "message_template": "no message class drawn, "
                                                "this writer's floor for this "
                                                "cell is zero",
                            "shared_with": "",
                            "corpus_objects": "",
                            "corpus_context": ""})
                continue
            for item in sorted(cell, key=lambda i: i["message_class_id"]):
                mcid = item["message_class_id"]
                hits = corpus["by_class"].get(mcid, {})
                out.append({
                    **base,
                    "message_class_id": mcid,
                    "severity_as_emitted": item["severity_as_emitted"],
                    "message_template": item["message_template"],
                    "shared_with": (other if mcid in other_set
                                    else "neither, this writer only"),
                    "corpus_objects": sum(hits.values()) if hits else 0,
                    "corpus_context": "; ".join(
                        "%s %s of %s" % (sop, _fmt(n),
                                         _fmt(corpus["denominators"].get(sop, 0)))
                        for sop, n in sorted(hits.items())) or "not observed in the "
                                                               "census snapshot",
                })
    return pd.DataFrame(out, columns=TABLE2_FIELDS)


def write_table2(t2: pd.DataFrame, ov: pd.DataFrame, corpus: dict
                 ) -> tuple[Path, Path]:
    MANUSCRIPT.mkdir(parents=True, exist_ok=True)
    csv_path = MANUSCRIPT / "table2_floor_set.csv"
    t2.to_csv(csv_path, index=False)

    drawn = t2[t2.message_class_id != ""]
    per_cell = (drawn.groupby(["writer", "sop_class", "validator",
                               "cell_single_writer"])
                     .agg(message_classes=("message_class_id", "nunique"))
                     .reset_index())
    empty = t2[t2.message_class_id == ""][["writer", "sop_class", "validator",
                                           "cell_single_writer"]].copy()
    empty["message_classes"] = 0
    per_cell = pd.concat([per_cell, empty], ignore_index=True).sort_values(
        ["writer", "sop_class", "validator"]).reset_index(drop=True)
    per_cell["message_classes"] = per_cell["message_classes"].astype(int).map(str)

    detail = drawn.copy()
    detail["message_template"] = detail["message_template"].map(lambda v: _clip(v, 130))
    detail["corpus_objects"] = detail["corpus_objects"].map(
        lambda v: _fmt(v) if str(v).isdigit() else str(v))

    single_cells = t2[t2.cell_single_writer == "yes"]
    n_single = int(single_cells[["sop_class", "validator", "writer"]]
                   .drop_duplicates().shape[0])
    gaps = "\n".join("- **%s**: %s" % (k, v)
                     for k, v in floor.W2_EMISSION_GAPS.items())

    headline = ov[(ov.sop_class == "SEG BINARY")
                  & (ov.validator == "dicom-validator")].iloc[0]

    text = f"""# Table 2: the floor set, per writer and per message class

A known-good object trips validators. Every rate this project quotes has to name
the floor it is quoted against, and this is that floor. Reproduce with `{CMD}`.

Sources: `results/floor_set.csv` for the floor itself, and
`results/phase2/census_message_classes.csv`, snapshot {corpus['snapshot']},
{_fmt(corpus.get('rows', 0))} rows, for corpus context.

## The floor, per cell

A cell is one writer, one SOP class, one validator. Cells where a writer drew
nothing are listed with zero, not omitted: a floor of zero is the finding that
makes a single scalar floor indefensible, and an absent row would read as
missing data.

{_md_table(per_cell, ["writer", "sop_class", "validator", "cell_single_writer", "message_classes"])}

## The message classes

Message templates are normalised by `colophon.floor.normalise`, which strips
tags, UIDs, frame and item indices and quoted values, and keeps attribute names,
module names and Type designations, because those are what identify the
diagnostic rather than what varies between instances of it. The unit of count is
the distinct message class, never the raw line.

`corpus_objects` is how many objects in the census snapshot drew the same
message class. A zero there means the class was not seen in the classes the
snapshot covers, which is not the same as absence from the archive: Segmentation
Storage is outside the census scope entirely, so no Segmentation-only message
class can appear in that column whatever its true frequency. The CSV carries a
`corpus_context` column naming the SOP class and the snapshot denominator behind
each of those counts, and the full untruncated template.

{_md_table(detail, ["writer", "sop_class", "validator", "message_class_id", "severity_as_emitted", "shared_with", "corpus_objects", "message_template"])}

## Single-writer cells, non-transferable by construction

{n_single} of the {len(t2[['writer', 'sop_class', 'validator']].drop_duplicates())}
cells are single-writer, because dcmqi could not emit the class at all:

{gaps}

A floor measured in a single-writer cell describes one writer and transfers to
nobody. It is marked `cell_single_writer = yes` in the CSV and carries the reason
in `single_writer_reason`, so the cell cannot be read as agreement between two
writers who never both ran.

## Overlap between the two writers

Jaccard over sets of normalised `message_class_id`, four decimal places.

{_md_table(ov, ["sop_class", "validator", "comparable", "highdicom_classes", "dcmqi_classes", "shared", "union", "jaccard", "vacuous"])}

The SEG BINARY value under dicom-validator is **{headline['jaccard']}**, that is
{headline['shared']} shared of {headline['union']} in the union. It is quoted to
four places on purpose. An earlier measurement put it at 1.0 and concluded that
dicom-validator's floor transfers between writers where dciodvfy's does not.
That was an artefact of this project's own parser, which captured only indented
findings and so discarded every finding on a tag without parents. Ledger row
F1-03-prev carries the retired claim and F1-10 carries the defect. With the
parser fixed the highdicom set is a strict subset of the dcmqi set and neither
validator's floor transfers.

The TID 1500 SR row under dciodvfy is marked vacuous: both sets are empty, so
the Jaccard of 1.0 is agreement that carries no information about whether the
two floors would agree if either writer drew anything.

A further caveat on the SR cell, from ledger row F1-05: both writers produce TID
1500 but not in the same SOP class. highdicom emits Comprehensive 3D SR and
dcmqi emits Enhanced SR. The comparison holds at the template level and does not
hold at the IOD level.

## What was dropped

Nothing. Six objects were emitted in Phase 1 and every one was run through both
validators, and every message class either produced is in the CSV. The corpus
context column is the only sampled quantity here, and it is bounded by the
census snapshot named above rather than by any selection made in this table.
"""
    md_path = MANUSCRIPT / "table2_floor_set.md"
    md_path.write_text(text, encoding="utf-8")
    return md_path, csv_path


# --- ledger -------------------------------------------------------------------
PENDING = RESULTS / "pending_ledger"


def proposed_rows(scanned: dict, cover: pd.DataFrame, t1: pd.DataFrame,
                  spread: pd.DataFrame, reverse: pd.DataFrame, t2: pd.DataFrame,
                  ov: pd.DataFrame, corpus: dict) -> list[dict]:
    complete = cover[cover.complete]
    partial = cover[~cover.complete]
    by_writer = table1_by_writer(t1)
    dis = disagreements(t1)
    n_objects = int(t1["objects"].sum())
    n_disagree = int(dis.loc[dis.verdict == DISAGREE, "objects"].sum()) if len(dis) else 0
    n_agree = int(dis.loc[dis.verdict == AGREE, "objects"].sum()) if len(dis) else 0
    n_scored = n_agree + n_disagree
    silent = t1[t1.verdict == EQUIPMENT_SILENT]
    n_silent = int(silent["objects"].sum())
    named = int(silent.loc[
        ~silent.writer.str.startswith(("unresolved", NO_FILE_META)), "objects"].sum())

    dropped_t1 = ("classes not complete in the census are excluded entirely: %s. "
                  "Segmentation Storage is outside the census scope. %s "
                  "unparseable lines of records.jsonl were skipped and %s objects "
                  "with a census status other than OK were skipped."
                  % ("; ".join("%s %s of %s series recorded"
                               % (r.sop_class_name, _fmt(r.series_recorded),
                                  _fmt(r.series_in_manifest))
                               for r in partial.itertuples()) or "none",
                     _fmt(scanned["lines_skipped"]),
                     _fmt(sum(scanned["not_ok_objects"].values()))))

    # Both artefacts are named, not only the CSV. colophon.claims_map reports
    # any file under results/ that no ledger row points at, and a generated
    # write-up nobody cites is exactly the dead weight that check is for.
    T1 = dict(section=TRACK, section_title="Table 1, writer census from census output",
              command=CMD,
              source_file="results/manuscript/table1_writers.csv and "
                          "results/manuscript/table1_writers.md",
              dropped=dropped_t1,
              floor="not applicable, no validator involved",
              sop_class=", ".join(complete["sop_class_name"]),
              idc_index_version=ledger.IDC_INDEX_VERSION,
              verified_on="2026-08-02")
    T2 = dict(section=TRACK, section_title="Table 2, floor set per writer per message class",
              command=CMD,
              source_file="results/manuscript/table2_floor_set.csv and "
                          "results/manuscript/table2_floor_set.md",
              dropped="nothing. Six Phase 1 objects, both validators, every "
                      "message class either writer drew. The corpus context "
                      "column is bounded by the census snapshot named in the "
                      "table and by the exclusion of Segmentation Storage from "
                      "the census",
              floor="this table is the floor; it does not quote a rate against one",
              verified_on="2026-08-02")

    headline = ov[(ov.sop_class == "SEG BINARY")
                  & (ov.validator == "dicom-validator")].iloc[0]
    # The identity carrying the most different producer claims, not the one
    # carrying the most objects. The claim is about spread, not about volume.
    top_identity = (spread.sort_values(
        ["distinct_declared_equipment_pairs", "objects"], ascending=False).iloc[0]
        if len(spread) else None)
    # Deduplicated: one message class can sit in several cells of Table 2, and
    # listing it once per cell would inflate a count of distinct classes.
    observed_in_corpus = sorted({
        (r.validator, r.message_class_id, r.corpus_context)
        for r in t2.itertuples()
        if r.message_class_id and str(r.corpus_objects).isdigit()
        and int(r.corpus_objects) > 0})

    rows = [
        dict(id="F2-01", claim="The writer census recomputed from what the "
             "census read out of the objects, rather than inferred from the two "
             "equipment attributes the index carries.",
             status="MEASURED",
             value="; ".join(
                 "%s: %s" % (sop, ", ".join(
                     "%s %s" % (r.writer, _fmt(int(r.objects)))
                     for r in by_writer[by_writer.sop_class_name == sop].itertuples()))
                 for sop in complete["sop_class_name"]),
             n=_fmt(n_objects), denominator=_fmt(n_objects),
             derived_from="W-01",
             pinned_by_test="tests/test_tables.py::test_object_counts_match_the_census",
             status_note="Attribution is by ImplementationClassUID (0002,0012) "
             "first, then ImplementationVersionName (0002,0013), then a "
             "ContributingEquipmentSequence item, with the deciding attribute "
             "recorded per row. The highdicom and PixelMed signatures were read "
             "out of those toolkits' own source; the DCMTK and dcm4che "
             "signatures are asserted from observed values and are labelled so.",
             notes="The file meta names the library that serialised the "
                   "dataset. It is not a claim about what produced the "
                   "analysis, and for an archive that re-encodes on ingest it "
                   "names the last writer rather than the first.", **T1),
        dict(id="F2-02", claim="Opening the files attributes a writer to the "
             "large majority of objects that the index-only rule could not "
             "attribute at all.",
             status="MEASURED",
             value="%s of %s objects carry equipment attributes that name no "
                   "toolkit; the file meta names one for %s of them"
                   % (_fmt(n_silent), _fmt(n_objects), _fmt(named)),
             n=_fmt(named), denominator=_fmt(n_silent),
             derived_from="W-01",
             pinned_by_test="tests/test_tables.py::test_no_incomplete_class_in_table1",
             status_note="This is the number the Phase 0 table said would have "
             "to be resolved in Phase 2, measured for the complete classes only.",
             **T1),
        dict(id="F2-03", claim="Where both carriers name a toolkit, they "
             "disagree about who wrote the object more often than they agree.",
             status="MEASURED",
             value="%s of %s scored objects disagree: %s"
                   % (_fmt(n_disagree), _fmt(n_scored),
                      "; ".join("%s declares %s, file meta says %s, %s objects"
                                % (r.sop_class_name, r.equipment_writer, r.writer,
                                   _fmt(int(r.objects)))
                                for r in dis[dis.verdict == DISAGREE].itertuples())
                      or "none"),
             n=_fmt(n_disagree), denominator=_fmt(n_scored),
             derived_from="P2P-08",
             pinned_by_test="tests/test_tables.py::test_disagreement_rests_on_a_registered_expectation",
             status_note="An object is scored only when the toolkit named by "
             "the equipment attributes has a file-meta signature established "
             "independently of this corpus. Toolkits with no registered "
             "expectation are never scored either way.",
             notes="Observation, not a resolution. Re-encoding on ingest and a "
                   "different serialisation backend would both produce this and "
                   "nothing measured here distinguishes them.", **T1),
        dict(id="F2-04", claim="One file-meta implementation identity carries "
             "several different declared producers, which is the shape a "
             "re-encoding step leaves behind.",
             status="MEASURED",
             value=("%s / %s appears on %s objects under %d distinct declared "
                    "Manufacturer and ManufacturerModelName pairs"
                    % (top_identity["implementation_class_uid"],
                       top_identity["implementation_version_name"],
                       _fmt(int(top_identity["objects"])),
                       int(top_identity["distinct_declared_equipment_pairs"])))
                   if top_identity is not None else "no identity observed",
             n=(str(int(top_identity["distinct_declared_equipment_pairs"]))
                if top_identity is not None else "0"),
             denominator=str(len(spread)),
             pinned_by_test="tests/test_tables.py::test_identity_spread_is_reported",
             status_note="The identity is recorded verbatim and is not resolved "
             "to a toolkit. It is not any signature this project could read out "
             "of a toolkit's source, and naming it would be a guess.",
             notes="The reverse mapping holds too: %s"
                   % ("; ".join("%s / %s, %s objects, %d file-meta writers"
                                % (r.declared_Manufacturer,
                                   r.declared_ManufacturerModelName,
                                   _fmt(int(r.objects)),
                                   int(r.distinct_file_meta_writers))
                                for r in reverse.itertuples())
                      if len(reverse) else "no declared producer in the complete "
                                           "classes sits behind more than one "
                                           "file-meta writer"), **T1),
        dict(id="F2-05", claim="The Phase 1 floor set, presented per writer, per "
             "validator and per SOP class, with the cells dcmqi could not emit "
             "marked non-transferable.",
             status="MEASURED",
             value="%d cells, %d of them single-writer; %d rows carrying a "
                   "message class and %d cells whose floor is zero"
                   % (len(t2[["writer", "sop_class", "validator"]].drop_duplicates()),
                      int(t2[t2.cell_single_writer == "yes"]
                          [["writer", "sop_class", "validator"]]
                          .drop_duplicates().shape[0]),
                      int((t2.message_class_id != "").sum()),
                      int((t2.message_class_id == "").sum())),
             n=str(int(t2[t2.cell_single_writer == "yes"]
                       [["writer", "sop_class", "validator"]]
                       .drop_duplicates().shape[0])),
             denominator=str(len(t2[["writer", "sop_class", "validator"]]
                                 .drop_duplicates())),
             derived_from="F1-01, F1-04",
             pinned_by_test="tests/test_tables.py::test_single_writer_cells_are_marked",
             status_note="Cells where a writer drew nothing are listed with "
             "zero rather than omitted. A floor of zero is the finding that "
             "makes a single scalar floor indefensible and an absent row would "
             "read as missing data.", **T2),
        dict(id="F2-06", claim="The SEG BINARY overlap under dicom-validator, "
             "recomputed from floor_set.csv for the manuscript table, is the "
             "corrected value and not the retired one.",
             status="MEASURED",
             value="Jaccard %s, %s shared of %s in the union"
                   % (headline["jaccard"], headline["shared"], headline["union"]),
             n=str(int(headline["shared"])), denominator=str(int(headline["union"])),
             sop_class="Segmentation Storage, BINARY",
             validator="dicom-validator",
             validator_version="dicom-validator 0.8.2, edition 2026c",
             derived_from="F1-03, F1-10",
             pinned_by_test="tests/test_tables.py::test_seg_binary_jaccard_is_the_corrected_value",
             status_note="Recomputed from the CSV rather than parsed out of "
             "results/floor_overlap.md, so the manuscript table and the Phase 1 "
             "write-up cannot drift apart. Quoted to four places because three "
             "rounds it to 0.857 and hides that it is not 1.0, which is what "
             "F1-03-prev was retired for.", **T2),
        dict(id="F2-07", claim="Part of the Phase 1 fixture floor is drawn by "
             "corpus objects too, so those floor message classes are not "
             "artefacts of the fixture.",
             status="MEASURED",
             value="; ".join(
                 "%s %s: %s" % (validator, mcid, context)
                 for validator, mcid, context in observed_in_corpus)
                   or "no floor message class appears in the census snapshot",
             n=str(len(observed_in_corpus)),
             denominator=str(int(t2.loc[t2.message_class_id != "",
                                        "message_class_id"].nunique())),
             derived_from="F1-01, P2C-02",
             pinned_by_test="tests/test_tables.py::test_corpus_context_is_bounded",
             status_note="A zero in the corpus column is not evidence of "
             "absence. Segmentation Storage is outside the census scope, so no "
             "Segmentation-only message class can appear there whatever its "
             "true frequency, and the snapshot is older than records.jsonl.",
             **T2),
        dict(id="F2-08", claim="Table 1 covers only SOP classes the census has "
             "finished, and says which it excluded and how far they had got.",
             status="MEASURED",
             value="complete: %s; excluded: %s"
                   % ("; ".join("%s %s series" % (r.sop_class_name,
                                                  _fmt(r.series_recorded))
                                for r in complete.itertuples()),
                      "; ".join("%s %s of %s series"
                                % (r.sop_class_name, _fmt(r.series_recorded),
                                   _fmt(r.series_in_manifest))
                                for r in partial.itertuples()) or "none"),
             n=str(len(complete)), denominator=str(len(cover)),
             pinned_by_test="tests/test_tables.py::test_no_incomplete_class_in_table1",
             status_note="Completeness is judged on series against the census "
             "manifest, not on objects, because the census skips a series it "
             "has already recorded. A class that is complete stays complete and "
             "its counts stay fixed while the rest of the census runs.", **T1),
        dict(id="F2-09", claim="The census records file was read while a census "
             "was appending to it, and the read reports what it could not parse.",
             status="MEASURED",
             value="%s lines seen, %s skipped as unparseable, from a %s byte "
                   "file last modified %s"
                   % (_fmt(scanned["lines_seen"]), _fmt(scanned["lines_skipped"]),
                      _fmt(scanned["size_bytes"]), scanned["mtime"]),
             n=str(scanned["lines_skipped"]), denominator=_fmt(scanned["lines_seen"]),
             pinned_by_test="tests/test_tables.py::test_scan_reports_skipped_lines",
             status_note="The last line of a file being appended to can be half "
             "written. Skipping it silently would make a truncated read look "
             "like a complete one, so the count is reported in the table and "
             "here whether or not it is zero.", **T1),
        dict(id="F2-10", claim="The equipment-attribute rule attributes objects "
             "to QIICR Reporting on a substring match against an unrelated 3D "
             "Slicer extension.",
             status="MEASURED",
             value="%s objects whose Manufacturer is "
                   "https://github.com/QIICR/Slicer-SUVFactorCalculator are "
                   "labelled QIICR Reporting via 3D Slicer, because the "
                   "registered pattern fedorov/reporting|slicer matches any 3D "
                   "Slicer extension URL"
                   % _fmt(int(t1.loc[t1.equipment_writer
                                     == "QIICR Reporting via 3D Slicer",
                                     "objects"].sum())),
             n=str(int(t1.loc[t1.equipment_writer == "QIICR Reporting via 3D Slicer",
                              "objects"].sum())),
             denominator=_fmt(n_objects),
             derived_from="W-01",
             pinned_by_test="tests/test_tables.py::test_equipment_rule_is_reused_verbatim",
             status_note="Reported, not corrected. colophon.writers.writer_of is "
             "reused verbatim so that the comparison in Table 1 is against the "
             "rule as registered rather than against a rule tuned for this "
             "table.", **T1),
    ]
    return rows


def write_pending(rows: list[dict]) -> Path:
    unknown = {k for r in rows for k in r} - set(ledger.FIELDS)
    if unknown:
        raise ValueError("proposed ledger rows carry unknown fields: %s"
                         % sorted(unknown))
    for r in rows:
        if r["status"] == "MEASURED":
            for required in ("command", "source_file", "dropped"):
                if not str(r.get(required, "")).strip():
                    raise ValueError("MEASURED row %s has no %s" % (r["id"], required))
    PENDING.mkdir(parents=True, exist_ok=True)
    path = PENDING / "track_f2.json"
    path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return path


# --- entry point --------------------------------------------------------------
def load_floor_rows(path: Path = FLOOR_SET) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(r) for r in csv.DictReader(handle)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--no-ledger", action="store_true",
                    help="write the tables but propose no ledger rows")
    args = ap.parse_args(argv)

    scanned = scan()
    cover = completeness(scanned)
    complete = list(cover.loc[cover.complete, "sop_class_name"])
    t1 = table1(scanned, complete)
    spread = identity_spread(scanned, complete)
    reverse = equipment_spread(scanned, complete)
    md1, csv1 = write_table1(scanned, cover, t1, spread, reverse)

    rows = load_floor_rows()
    corpus = corpus_context()
    ov = overlaps(rows)
    t2 = table2(rows, corpus)
    md2, csv2 = write_table2(t2, ov, corpus)

    print("records.jsonl: %s lines, %s skipped"
          % (_fmt(scanned["lines_seen"]), _fmt(scanned["lines_skipped"])))
    print("complete classes: %d of %d" % (len(complete), len(cover)))
    for path in (md1, csv1, md2, csv2):
        print("  wrote %s" % path)
    for sop in complete:
        sub = t1[t1.sop_class_name == sop]
        print("  %-46s %6s objects" % (sop, _fmt(int(sub["objects"].sum()))))
    dis = disagreements(t1)
    if len(dis):
        n = int(dis.loc[dis.verdict == DISAGREE, "objects"].sum())
        print("equipment against file meta: %s disagreements of %s scored"
              % (_fmt(n), _fmt(int(dis["objects"].sum()))))

    if not args.no_ledger:
        pending = write_pending(
            proposed_rows(scanned, cover, t1, spread, reverse, t2, ov, corpus))
        print("  wrote %s" % pending)
    return 0


if __name__ == "__main__":
    sys.exit(main())
