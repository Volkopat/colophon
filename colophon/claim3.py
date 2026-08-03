"""Claim 3, complete tabulation across everything measured. No fetching.

Reads two record sets already on disk and joins nothing else: the Phase 2 census
`_cache/census/records.jsonl` and the PRE-06 Segmentation sample
`_cache/phase3/records.jsonl`. Zero bytes are downloaded. The IDC index is read
for collection metadata and DOI, which is the same local parquet every Phase 0
module uses.

**Scope, stated before any number.** Seven census classes are complete and are
reported. Enhanced SR is in flight and is **excluded from every rate**, with its
recorded count stated wherever the denominator appears, because a partial class
reads as a rate. Segmentation comes from the PRE-06 sample and carries the
frame's stratum weights, so it is never pooled with the census classes into a
single unweighted total without saying so.

**Three grades, never two.** Non-conformant, conformant but uninformative,
informative. The middle grade is the one two-grade reporting destroys, and it is
the finding: an object can satisfy every stated requirement of PS3.3 and still
not say what produced it.

**Absence of a Type 3 carrier is a gap in the standard, not a defect.** Two
bindings can make an object non-conformant here, both re-verified against PS3.3
2026c by `colophon.typecheck`. **Type 1**, Enhanced General Equipment with Usage
M, binds four equipment attributes in **two** IODs, Segmentation and Parametric
Map: absent or zero length is a violation. **Type 2**, General Equipment with
Usage M, binds Manufacturer in **all eight**: absent is a violation, zero length
is not.

An earlier version of this module graded on the Type 1 binding alone. It put the
40 Key Object Selection objects whose Manufacturer is absent into `conformant but
uninformative` while the conformance arm called all 40 net, which is a
contradiction inside one paper. The ceiling is real and it has three tiers, not
one: a meaningful value compelled in two IODs, mere presence compelled in eight,
and nothing at all compelled for model, serial or software version in six.

`ImplementationClassUID (0002,0012)` is captured and reported but is **not used
for grading**, because its Type designation is not among the standards rows
verified against a primary source in this project. It is non-empty on every
object measured, so nothing turns on it.

**Every rate is reported twice**: object weighted, and with the collection or the
analysis result as the independent unit. Median and IQR are not reported for any
of these distributions. They are two point masses at 0 and 100 and a median
reports one of the two camps as though it were a centre. The boundary counts are
given instead: how many units sit at 0, how many at 100, how many in between,
and which ones.

Usage:
    python -m colophon.claim3
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

from . import census, phase3, provenance, standards, writers
from .paths import RESULTS

CMD = "python -m colophon.claim3"
OUT = RESULTS / "claim3"

# --- scope --------------------------------------------------------------------
PARTIAL_CLASS = "Enhanced SR Storage"
SEGMENTATION = "Segmentation Storage"

# STD-04, verified against PS3.3 2026c Table C.7-8b and Usage M in Table A.51-1
# and Table A.75-1. These are the only Type 1 bindings this module grades on.
TYPE1_CLASSES = set(standards.ENHANCED_GENERAL_EQUIPMENT_IODS)
TYPE1_CARRIERS = [d["keyword"] for d in standards.ENHANCED_GENERAL_EQUIPMENT]

CARRIERS = ["Manufacturer", "ManufacturerModelName", "DeviceSerialNumber",
            "SoftwareVersions", "ImplementationVersionName",
            "ImplementationClassUID", "ContributingEquipmentSequence",
            "ContentCreatorName", "SeriesDescription"]

NOT_GRADED = ["ImplementationClassUID"]

# Type 2 binding, from the PS3.3 2026c re-verification in colophon.typecheck.
# General Equipment (Table C.7.5.1) has Usage M in all eight measured IODs and
# carries Manufacturer at Type 2, so the attribute shall be present in every one
# of them. Absent is a violation; zero length is not.
TYPE2_CARRIER = "Manufacturer"
TYPE2_ALL_IODS = True

GRADES = ["non-conformant", "conformant but uninformative", "informative"]

# The census recorded ContributingEquipmentSequence as a presence flag rather
# than in three states, so for those seven classes a sequence present with zero
# items cannot be told apart from an absent one. Declared here and repeated in
# the table rather than smoothed over.
CES_TWO_STATE_NOTE = ("census classes record ContributingEquipmentSequence as "
                      "present or not present only, so zero-length is not "
                      "separable from absent for them; the Segmentation sample "
                      "records all three states")


# --- the recoverability ladder ------------------------------------------------
# The levels are the ones the tabulation was asked for. They are not
# colophon.writers.CARRIER_LEVELS, which has four levels in a different order;
# that table stays as it is and this one is published beside it.
#
# `identity` is where a producer could be named. `version` is where a version
# could appear. A carrier can appear in both.
LADDER = [
    {"level": 1, "name": "equipment attributes",
     "identity": ["Manufacturer", "ManufacturerModelName", "DeviceSerialNumber"],
     "version": ["SoftwareVersions"], "in_object": True},
    {"level": 2, "name": "file meta",
     "identity": ["ImplementationVersionName", "ImplementationClassUID"],
     "version": ["ImplementationVersionName"], "in_object": True},
    {"level": 3, "name": "SeriesDescription and ContentCreatorName",
     "identity": ["SeriesDescription", "ContentCreatorName"],
     "version": ["SeriesDescription", "ContentCreatorName"], "in_object": True},
    {"level": 4, "name": "in-object algorithm carriers",
     "identity": ["_ces_identity", "_algorithm_identity"],
     "version": ["_ces_version", "_algorithm_version"], "in_object": True},
    {"level": 5, "name": "collection metadata and DOI",
     "identity": ["collection_id", "analysis_result_id", "source_DOI"],
     "version": [], "in_object": False},
]


def informative_value(values) -> tuple[bool, str]:
    """Does any value name something that is neither a sentinel nor generic.

    `colophon.writers._informative` is the published rule and is reused rather
    than restated, so a reader checking one assignment checks one rule.
    """
    return writers._informative({str(v) for v in values if v})


# A DICOM UID matches any version regex and is not a version. So does a 40
# character SHA1. Both appear in the carriers being searched.
UID_SHAPED = re.compile(r"^\d+(\.\d+){3,}$")
SHA_SHAPED = re.compile(r"^[0-9a-f]{7}$|^[0-9a-f]{40}$")
# An encoding library naming its own version. `highdicom0.27.0` is the
# `phase2_rules` entry in results/sentinels.json: highdicom/base.py writes
# f'highdicom{__version__}' into ImplementationVersionName. It is a version, and
# it is the version of the thing that wrote the file rather than of the thing
# that produced the result, which is the whole distinction claim 3 rests on.
ENCODER_VERSION = re.compile(
    r"^(highdicom|dcmqi|pydicom-?seg|pydicom|OFFIS_DCMTK|dcm4che)", re.I)


def has_version(values) -> tuple[bool, str, str]:
    """Does a version of the producing analysis appear.

    Returns whether one does, **the version token itself**, and the whole string
    it was found in. Returning only the string was wrong in a way that reached a
    published table: the version column of T3.3 printed
    `TotalSegmentator(v1.5.6) Segmentation of`, a SeriesDescription clipped at
    forty characters, where a reader expects `v1.5.6`. Both are kept, because
    the token alone loses the build suffix in a value like `2.3:Win64_072712`
    and the string alone is not a version.

    Three exclusions, each because the string looks like a version and is not
    one. A **sentinel** such as `highdicom0.27.0` carries the encoder's version,
    not the analysis's, and counting it would credit an object for naming the
    library that wrote it. A **UID** matches every version regex ever written.
    A **commit hash** identifies a build of the encoder, which P2P-09 established
    and which is the whole point of T3.5.
    """
    for v in values:
        text = str(v or "").strip()
        if not text or writers.is_sentinel(text):
            continue
        if UID_SHAPED.match(text) or SHA_SHAPED.match(text):
            continue
        if ENCODER_VERSION.match(text):
            continue
        match = writers.VERSION.search(text)
        if match:
            return True, match.group(0), text
    return False, "", ""


# --- load ---------------------------------------------------------------------
def _carrier_states(obj: dict, source: str) -> dict:
    out = {}
    for name in CARRIERS:
        if name == "ContributingEquipmentSequence":
            if source == "phase3":
                out[name + "_state"] = obj.get(
                    "ContributingEquipmentSequence_state", "absent")
            else:
                out[name + "_state"] = ("non_empty"
                                        if obj.get("ContributingEquipmentSequence_present")
                                        else "absent_or_zero_length")
            out[name] = ""
            continue
        out[name] = obj.get(name, "") or ""
        out[name + "_state"] = obj.get(name + "_state", "absent")
    return out


def _analysis_result(record) -> str:
    """The analysis result id, with absence normalised to one token.

    `record.get("analysis_result_id") or "(null)"` was the previous form and it
    is wrong for exactly the records that need it: a census record sourced from
    a pandas merge carries `float("nan")` rather than `None`, and NaN is truthy,
    so the `or` never fires and the value stays NaN. `pandas.groupby` then drops
    those rows silently, which is how Table 3's objects column came to sum to
    31,008 against a population of 35,107 with the 4,099 difference appearing in
    no row and no cell.
    """
    value = record.get("analysis_result_id")
    if value is None:
        return "(null)"
    text = str(value).strip()
    if not text or text.lower() in ("nan", "none", "null"):
        return "(null)"
    return text

def load() -> tuple[pd.DataFrame, dict]:
    """One row per object across both record sets, plus what was excluded."""
    totals = census.class_totals()
    complete = {c for c in census.CLASS_ORDER
                if c != PARTIAL_CLASS and totals.get(c, 0) > 0}
    rows, excluded = [], Counter()

    for record in census.load_records():
        sop = record["sop_class_name"]
        if sop == PARTIAL_CLASS:
            excluded["enhanced_sr_series_recorded"] += 1
            continue
        if sop not in complete:
            excluded["other_incomplete_class_series"] += 1
            continue
        if record["status"] != "OK":
            excluded["census_series_fetch_failed"] += 1
            continue
        for obj in record.get("objects", []):
            if obj.get("status") != "OK":
                excluded["census_objects_read_failed"] += 1
                continue
            row = {
                "source": "census", "sop_class_name": sop,
                "series_instance_uid": record["series_instance_uid"],
                "sop_instance_uid": obj.get("sop_instance_uid", ""),
                "collection_id": record["collection_id"],
                "analysis_result_id": _analysis_result(record),
                "stratum": "", "writer_from_index_label": "",
                "index_Manufacturer": record.get("declared_Manufacturer") or "",
                "index_ManufacturerModelName": record.get(
                    "declared_ManufacturerModelName") or "",
                "ces_items": json.dumps(obj.get("ContributingEquipmentSequence_items", [])),
                "segments": "[]",
            }
            row.update(_carrier_states(obj, "census"))
            rows.append(row)

    for record in phase3.load_records():
        if record["status"] != "OK":
            excluded["segmentation_series_fetch_failed"] += 1
            continue
        for obj in record.get("objects", []):
            if obj.get("status") != "OK":
                excluded["segmentation_objects_read_failed"] += 1
                continue
            row = {
                "source": "phase3", "sop_class_name": SEGMENTATION,
                "series_instance_uid": record["series_instance_uid"],
                "sop_instance_uid": obj.get("sop_instance_uid", ""),
                "collection_id": record["collection_id"],
                "analysis_result_id": _analysis_result(record),
                "stratum": record.get("stratum", ""),
                "writer_from_index_label": record.get("writer", ""),
                "index_Manufacturer": "", "index_ManufacturerModelName": "",
                "ces_items": json.dumps(obj.get("ContributingEquipmentSequence_items", [])),
                "segments": json.dumps(obj.get("segments", [])),
            }
            row.update(_carrier_states(obj, "phase3"))
            rows.append(row)

    frame = pd.DataFrame(rows)
    excluded["enhanced_sr_series_in_manifest"] = int(totals.get(PARTIAL_CLASS, 0))
    return frame, dict(excluded)


# --- the two ways every rate is reported --------------------------------------
def two_camp(frame: pd.DataFrame, unit: str, flag: str) -> dict:
    """Unit-level distribution reported by its boundaries, never by a median.

    These distributions are two point masses. A unit either has the property for
    all its objects or for none, almost always, so a median reports one camp as
    though it were a centre and an IQR of zero reads as agreement. The counts at
    0 and at 100 are the finding, and the units in between are named because
    they are the only interesting ones.
    """
    if frame.empty:
        return {"units": 0, "at_zero": 0, "at_hundred": 0, "between": 0,
                "between_units": []}
    per = frame.groupby(unit)[flag].agg(["size", "sum"])
    pct = 100 * per["sum"] / per["size"]
    between = pct[(pct > 0) & (pct < 100)]
    per_unit = pd.DataFrame({"unit": per.index.astype(str),
                             "objects": per["size"].astype(int).values,
                             "flagged": per["sum"].astype(int).values,
                             "pct": pct.round(4).values})
    return {
        "per_unit": per_unit.sort_values("pct", ascending=False).to_dict("records"),
        "units": int(len(per)),
        "at_zero": int((pct == 0).sum()),
        "at_hundred": int((pct == 100).sum()),
        "between": int(len(between)),
        "between_units": [{"unit": str(k), "pct": round(float(v), 2),
                           "objects": int(per.loc[k, "size"])}
                          for k, v in between.sort_values(ascending=False).items()],
    }


def both_ways(frame: pd.DataFrame, flag: str) -> dict:
    n = int(len(frame))
    k = int(frame[flag].sum())
    return {
        "objects": n, "objects_flagged": k,
        "pct_object_weighted": round(100 * k / n, 2) if n else None,
        "by_collection": two_camp(frame, "collection_id", flag),
        "by_analysis_result": two_camp(frame, "analysis_result_id", flag),
    }


# --- T3.1 carrier population --------------------------------------------------
def t31(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows = []
    for key, group in (("sop_class_name", frame.groupby("sop_class_name")),
                       ("analysis_result_id", frame.groupby(
                           ["sop_class_name", "analysis_result_id"]))):
        for name, sub in group:
            base = ({"sop_class_name": name, "analysis_result_id": "(all)"}
                    if key == "sop_class_name"
                    else {"sop_class_name": name[0], "analysis_result_id": name[1]})
            sop = base["sop_class_name"]
            for carrier in CARRIERS:
                counts = Counter(sub[carrier + "_state"])
                binds = sop in TYPE1_CLASSES and carrier in TYPE1_CARRIERS
                rows.append(dict(
                    base, grouping=key, carrier=carrier, objects=int(len(sub)),
                    absent=counts.get("absent", 0),
                    zero_length=counts.get("empty", 0),
                    non_empty=counts.get("non_empty", 0),
                    absent_or_zero_length=counts.get("absent_or_zero_length", 0),
                    type1_here="yes" if binds else "no",
                    type1_violation=(counts.get("absent", 0) + counts.get("empty", 0))
                    if binds else 0))
    table = pd.DataFrame(rows)
    by_class = table[table.grouping == "sop_class_name"].drop(columns="grouping")
    by_ar = table[table.grouping == "analysis_result_id"].drop(columns="grouping")

    # The flagged case the tabulation asked for by name.
    sv = frame[frame.sop_class_name.isin(TYPE1_CLASSES)]
    flagged = []
    for name, sub in sv.groupby(["sop_class_name", "analysis_result_id"]):
        for carrier in TYPE1_CARRIERS:
            counts = Counter(sub[carrier + "_state"])
            if counts.get("empty", 0) or counts.get("absent", 0):
                flagged.append({
                    "sop_class_name": name[0], "analysis_result_id": name[1],
                    "carrier": carrier, "objects": int(len(sub)),
                    "absent": counts.get("absent", 0),
                    "zero_length": counts.get("empty", 0),
                    "binding": "Type 1, Enhanced General Equipment Usage M",
                    "grade": "non-conformant"})
    return by_class, by_ar, pd.DataFrame(flagged)


# --- T3.2 what the values name ------------------------------------------------
def t32(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    work = frame.copy()
    work["bucket"] = [provenance.bucket_of(a, b) for a, b in
                      zip(work["Manufacturer"], work["ManufacturerModelName"])]
    work["sentinel_manufacturer"] = work["Manufacturer"].map(writers.is_sentinel)
    work["sentinel_model"] = work["ManufacturerModelName"].map(writers.is_sentinel)
    work["all_sentinel"] = work["sentinel_manufacturer"] & work["sentinel_model"]

    rows = []
    for name, sub in work.groupby("sop_class_name"):
        counts = Counter(sub["bucket"])
        row = {"sop_class_name": name, "analysis_result_id": "(all)",
               "objects": int(len(sub))}
        for bucket in provenance.BUCKET_ORDER:
            row[bucket] = counts.get(bucket, 0)
            row["pct_" + bucket] = round(100 * counts.get(bucket, 0) / len(sub), 2)
        row["sum_pct"] = round(sum(row["pct_" + b] for b in provenance.BUCKET_ORDER), 2)
        row["objects_all_sentinel"] = int(sub["all_sentinel"].sum())
        rows.append(row)
    by_class = pd.DataFrame(rows)

    rows = []
    for name, sub in work.groupby(["sop_class_name", "analysis_result_id"]):
        counts = Counter(sub["bucket"])
        row = {"sop_class_name": name[0], "analysis_result_id": name[1],
               "objects": int(len(sub))}
        for bucket in provenance.BUCKET_ORDER:
            row[bucket] = counts.get(bucket, 0)
            row["pct_" + bucket] = round(100 * counts.get(bucket, 0) / len(sub), 2)
        row["sum_pct"] = round(sum(row["pct_" + b] for b in provenance.BUCKET_ORDER), 2)
        rows.append(row)
    by_ar = pd.DataFrame(rows)

    work["_encoder_only"] = work["bucket"] == "encoder_only"
    return by_class, by_ar, both_ways(work, "_encoder_only")


# --- T3.3 the recoverability ladder -------------------------------------------
def _level_values(row, level: dict, index_row: dict) -> list[str]:
    values = []
    for column in level["identity"]:
        if column == "_ces_identity":
            for item in json.loads(row.ces_items or "[]"):
                values += [item.get("Manufacturer", ""),
                           item.get("ManufacturerModelName", "")]
        elif column == "_algorithm_identity":
            for segment in json.loads(row.segments or "[]"):
                values.append(segment.get("SegmentAlgorithmName", ""))
                for macro in segment.get("macro", []):
                    values += [macro.get("AlgorithmName_value", ""),
                               macro.get("AlgorithmFamilyCode", ""),
                               macro.get("AlgorithmSource_value", "")]
        elif not level["in_object"]:
            values.append(str(index_row.get(column, "") or ""))
        else:
            values.append(str(getattr(row, column, "") or ""))
    return values


def _level_versions(row, level: dict) -> list[str]:
    values = []
    for column in level["version"]:
        if column == "_ces_version":
            for item in json.loads(row.ces_items or "[]"):
                values.append(item.get("SoftwareVersions", ""))
        elif column == "_algorithm_version":
            for segment in json.loads(row.segments or "[]"):
                for macro in segment.get("macro", []):
                    values.append(macro.get("AlgorithmVersion_value", ""))
        else:
            values.append(str(getattr(row, column, "") or ""))
    return values


def t33(frame: pd.DataFrame, index: pd.DataFrame) -> pd.DataFrame:
    meta = (index.drop_duplicates("analysis_result_id")
                 .set_index("analysis_result_id")[["collection_id", "source_DOI"]]
                 .to_dict("index"))
    rows = []
    for (sop, ar), sub in frame.groupby(["sop_class_name", "analysis_result_id"]):
        index_row = dict(meta.get(ar, {}), analysis_result_id=ar)
        first_level, first_value, first_name = None, "", ""
        version_here, version_value, version_source = False, "", ""
        per_level = {}
        for level in LADDER:
            identity_values, version_values = [], []
            for row in sub.itertuples():
                identity_values += _level_values(row, level, index_row)
                version_values += _level_versions(row, level)
            # The same rule the grading uses, so the ladder and the grade table
            # cannot contradict each other. An earlier version used the
            # permissive token test and put a DICOM UID, a device serial and a
            # commit hash in the identifying-value column.
            ok, example, _rule = names_producer(identity_values)
            has_v, v_token, v_source = has_version(
                version_values + ([example] if ok else []))
            per_level[level["level"]] = "yes" if ok else "no"
            if ok and first_level is None:
                first_level, first_value = level["level"], example
                first_name = level["name"]
                version_here = has_v
                version_value, version_source = v_token, v_source
        rows.append({
            "sop_class_name": sop, "analysis_result_id": ar,
            "objects": int(len(sub)),
            "first_level_identity_appears": first_level if first_level else "none",
            "level_name": first_name or "identity does not appear at any level",
            "identifying_value": first_value[:80],
            "version_at_that_level": "yes" if version_here else "no",
            "version_value": version_value,
            "version_found_in": version_source[:80],
            "in_object": ("yes" if first_level and first_level <= 4
                          else "no, registry only" if first_level == 5
                          else "not applicable, identity appears nowhere"),
            **{"level_%d" % lv["level"]: per_level[lv["level"]] for lv in LADDER},
        })
    return pd.DataFrame(rows).sort_values(
        ["first_level_identity_appears", "objects"], ascending=[True, False])


# --- T3.4 the algorithm identification result ---------------------------------
def t34(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    seg = frame[frame.source == "phase3"]
    rows = []
    for writer, sub in seg.groupby("writer_from_index_label"):
        counts = Counter()
        objects = Counter()
        for row in sub.itertuples():
            segments = json.loads(row.segments or "[]")
            non_manual = [s for s in segments if s.get("non_manual")]
            for s in non_manual:
                counts[s["identification"]] += 1
            counts["non_manual"] += len(non_manual)
            counts["segments"] += len(segments)
            if non_manual:
                objects["with_non_manual"] += 1
                states = {s["identification"] for s in non_manual}
                if "absent" in states:
                    objects["any_absent"] += 1
                if "present_incomplete" in states:
                    objects["any_incomplete"] += 1
                if "present_complete" in states:
                    objects["any_complete"] += 1
        nm = counts["non_manual"]
        rows.append({
            "writing_toolkit": writer, "objects": int(len(sub)),
            "segments": counts["segments"], "segments_non_manual": nm,
            "seg_absent": counts["absent"],
            "pct_seg_absent": round(100 * counts["absent"] / nm, 2) if nm else None,
            "seg_present_incomplete": counts["present_incomplete"],
            "pct_seg_present_incomplete": round(
                100 * counts["present_incomplete"] / nm, 2) if nm else None,
            "seg_present_zero_items": counts["present_zero_items"],
            "seg_present_complete": counts["present_complete"],
            "objects_with_non_manual": objects["with_non_manual"],
            "objects_any_absent": objects["any_absent"],
            "objects_any_incomplete": objects["any_incomplete"],
            "objects_any_complete": objects["any_complete"],
            "grade": ("conformant but uninformative" if counts["absent"] and not
                      counts["present_incomplete"] else
                      "informative" if counts["present_complete"] and not
                      counts["absent"] else "mixed, see per-stratum table"),
        })
    by_writer = pd.DataFrame(rows).sort_values("segments_non_manual", ascending=False)

    # The row the tabulation asked for by name, carried separately because it is
    # neither absence nor incompleteness: the macro is complete and contradicts
    # the segment's own declared type.
    contradiction = Counter()
    for row in seg.itertuples():
        for segment in json.loads(row.segments or "[]"):
            if not segment.get("non_manual"):
                continue
            for macro in segment.get("macro", []):
                if "manual" in (macro.get("AlgorithmName_value", "") or "").lower():
                    contradiction[(row.writer_from_index_label,
                                   row.analysis_result_id,
                                   segment["SegmentAlgorithmType"],
                                   macro.get("AlgorithmName_value", ""))] += 1
    special = pd.DataFrame(
        [{"writing_toolkit": w, "analysis_result_id": a,
          "SegmentAlgorithmType": t, "AlgorithmName": n, "segments": c,
          "state_of_0062_0007": "present_complete",
          "grade": "conformant but uninformative",
          "basis": "PS3.3 states no relation between (0062,0008) and "
                   "(0066,0036), so the object is conformant and the "
                   "contradiction is reported, not resolved"}
         for (w, a, t, n), c in contradiction.items()])
    return by_writer, special


# --- T3.5 version carriers ----------------------------------------------------
SHA7 = re.compile(r"^[0-9a-f]{7}$")
UPSTREAM = re.compile(r"github\.com[:/]qiicr/dcmqi", re.I)
FORK = re.compile(r"github\.com[:/](?!qiicr/)([A-Za-z0-9_.-]+)/dcmqi", re.I)


# The upstream history, cloned bare so every abbreviated SHA resolves without a
# network call per lookup. Addendum 02 recorded that no 7-character prefix
# collides across the 1,374 dcmqi commits, so the abbreviation is a precise
# version carrier and this resolution is unambiguous.
DCMQI_CLONE = Path("_cache") / "dcmqi.git"


def resolve_sha(sha: str) -> dict:
    """Resolve one abbreviated SHA to its commit date and nearest tag, offline.

    A SHA that does not resolve is `orphaned`, which is a real category: the
    object was written by a build whose commit is not in the upstream history,
    a personal fork or a rebased branch.
    """
    import subprocess
    if not DCMQI_CLONE.exists():
        return {"resolved_commit_date": "NO CLONE", "nearest_tag": "NO CLONE",
                "resolution": "clone absent"}

    def git(*args):
        return subprocess.run(["git", "--git-dir", str(DCMQI_CLONE), *args],
                              capture_output=True, text=True, timeout=60)

    full = git("rev-parse", "--verify", "--quiet", sha + "^{commit}")
    if full.returncode != 0 or not full.stdout.strip():
        return {"resolved_commit_date": "", "nearest_tag": "",
                "resolution": "orphaned, not in upstream history"}
    commit = full.stdout.strip()
    date = git("show", "-s", "--format=%cI", commit).stdout.strip()
    tag = git("describe", "--tags", "--abbrev=0", commit)
    return {"resolved_commit_date": date,
            "nearest_tag": tag.stdout.strip() if tag.returncode == 0
                           else "no tag reachable",
            "resolution": "upstream"}


def t35(frame: pd.DataFrame) -> pd.DataFrame:
    rows = Counter()
    for row in frame.itertuples():
        sha = str(row.SoftwareVersions or "").strip()
        if not SHA7.match(sha):
            continue
        model = str(row.ManufacturerModelName or "").strip()
        rows[(sha, model, row.sop_class_name, row.analysis_result_id)] += 1
    out = []
    for (sha, model, sop, ar), n in rows.items():
        if UPSTREAM.search(model):
            repo = "upstream, QIICR/dcmqi"
        elif FORK.search(model):
            repo = "named fork, %s" % FORK.search(model).group(1)
        elif model:
            repo = "not a dcmqi repository URL"
        else:
            repo = "orphaned, no repository named"
        out.append({
            "SoftwareVersions_sha7": sha, "declared_repository": model[:80],
            "repository_class": repo, "sop_class_name": sop,
            "analysis_result_id": ar, "objects": n,
            **resolve_sha(sha)})
    table = pd.DataFrame(out)
    return table.sort_values("objects", ascending=False) if len(table) else table


# --- T3.6 index versus object writer identity ---------------------------------
def t36(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    work = frame.copy()
    labels, carriers_used = [], []
    for row in work.itertuples():
        equipment = " ".join(
            "%s %s" % (i.get("Manufacturer", ""), i.get("ManufacturerModelName", ""))
            for i in json.loads(row.ces_items or "[]"))
        found, carrier = writers.UNKNOWN_WRITER, "none of the three carriers"
        for name, text in (("ContributingEquipmentSequence", equipment),
                           ("ImplementationVersionName",
                            str(row.ImplementationVersionName or "")),
                           ("Manufacturer and ManufacturerModelName",
                            "%s %s" % (row.Manufacturer or "",
                                       row.ManufacturerModelName or ""))):
            hit = next((w for w, p in writers.WRITER_RULES
                        if re.search(p, text.lower())), None)
            if hit:
                found, carrier = hit, name
                break
        labels.append(found)
        carriers_used.append(carrier)
    work["writer_from_object"] = labels
    work["deciding_carrier"] = carriers_used
    work["writer_from_index"] = [
        row.writer_from_index_label if row.source == "phase3"
        else writers.writer_of(row.index_Manufacturer, row.index_ManufacturerModelName)
        for row in work.itertuples()]
    work["_relabelled"] = work["writer_from_index"] != work["writer_from_object"]

    rows = []
    for name, sub in work.groupby("sop_class_name"):
        rows.append({
            "sop_class_name": name, "analysis_result_id": "(all)",
            "objects": int(len(sub)),
            "relabelled": int(sub["_relabelled"].sum()),
            "pct_relabelled": round(100 * float(sub["_relabelled"].mean()), 2),
            "index_says_unidentifiable": int(
                (sub["writer_from_index"] == writers.UNKNOWN_WRITER).sum()),
            "object_says_unidentifiable": int(
                (sub["writer_from_object"] == writers.UNKNOWN_WRITER).sum())})
    by_class = pd.DataFrame(rows).sort_values("objects", ascending=False)

    rows = []
    for name, sub in work.groupby(["sop_class_name", "analysis_result_id"]):
        if not sub["_relabelled"].any():
            continue
        moves = Counter(zip(sub["writer_from_index"], sub["writer_from_object"],
                            sub["deciding_carrier"]))
        for (was, now, carrier), n in moves.items():
            if was == now:
                continue
            rows.append({
                "sop_class_name": name[0], "analysis_result_id": name[1],
                "writer_from_index": was, "writer_from_object": now,
                "deciding_carrier": carrier, "objects": n,
                "objects_in_cell": int(len(sub)),
                "pct_of_cell": round(100 * n / len(sub), 2)})
    by_ar = (pd.DataFrame(rows).sort_values("objects", ascending=False)
             if rows else pd.DataFrame())
    return by_class, both_ways(work, "_relabelled") | {"by_ar": by_ar,
                                                       "frame": work}


# --- grading ------------------------------------------------------------------
# Carriers in which a producing analysis could be named, pooled per object.
IDENTITY_POOL = ["Manufacturer", "ManufacturerModelName", "SeriesDescription",
                 "ContentCreatorName"]


def identity_values(row) -> list[str]:
    """Every string in an object that could name what produced it."""
    pool = [str(getattr(row, c, "") or "") for c in IDENTITY_POOL]
    for item in json.loads(getattr(row, "ces_items", "") or "[]"):
        pool += [item.get("Manufacturer", ""), item.get("ManufacturerModelName", "")]
    for segment in json.loads(getattr(row, "segments", "") or "[]"):
        pool.append(segment.get("SegmentAlgorithmName", ""))
        for macro in segment.get("macro", []):
            pool += [macro.get("AlgorithmName_value", ""),
                     macro.get("AlgorithmSource_value", "")]
    return [p for p in pool if str(p).strip()]


# Additive rules for fields the Phase 0 table never saw.
#
# `provenance.RULES` was built for `Manufacturer` and `ManufacturerModelName` as
# the index carries them. This pass is the first to read `SegmentAlgorithmName
# (0062,0009)` and the Algorithm Identification Macro at scale, and those fields
# contain model names that table has no rule for. Extending `provenance.RULES`
# itself would retroactively move the Phase 0 C3 measurements, so these rules are
# kept separate, applied only after the Phase 0 table returns `unclassified`, and
# reported with their own count so the effect of adding them is itself a number.
#
# Ordered, first match wins, matched over the lowercased value. Deliberately
# strict: a value is a named analysis only if it names a specific model or
# pipeline. Task descriptors, structure labels and report titles are not, and
# the ones declined stay in the published unclassified table where a reader can
# overrule the call.
CLAIM3_EXTRA_RULES: list[tuple[str, str, str]] = [
    ("named_analysis", "TotalSegmentator", r"totalsegmentator"),
    ("named_analysis", "nnU-Net", r"nnu-?net"),
    ("named_analysis", "Rhabdomyosarcoma Pathology CNN",
     r"rhabdomyosarcoma pathology cnn"),
    ("institution", "Frederick National Lab",
     r"frederick national lab|fnlcr"),
]

# Declined on purpose, recorded so the decision is visible rather than implied.
DECLINED = {
    "Manual Segmentation": "names a procedure, not an algorithm",
    "BPR landmark annotations": "names the task, not the model that did it",
    "BPR region annotations": "names the task, not the model that did it",
    "Standard Breast Imaging Report": "a report title. This analysis result is "
                                      "clinical records converted to SR by XSLT "
                                      "and is not an annotation at all",
    "Tumor bounding box": "names the structure, not the producer",
    "Sybil lesion bounding box": "names the structure. The producer is named "
                                 "elsewhere in the same objects and is counted "
                                 "there",
}


def classify_value(value) -> tuple[str, str, bool]:
    """(category, rule, came_from_the_additive_table)."""
    category, rule = provenance.classify(value)
    if category != "unclassified":
        return category, rule, False
    text = str(value).lower()
    for cat, label, pattern in CLAIM3_EXTRA_RULES:
        if re.search(pattern, text):
            return cat, label, True
    return "unclassified", str(value)[:60], False


def names_producer(values) -> tuple[bool, str, str]:
    """Does any value name a producing analysis, under the published rule table.

    `colophon.provenance.classify` is the project's ordered, eyeball-checkable
    rule table and it is imported rather than restated. Only the
    `named_analysis` category counts: a string that names a specific model,
    pipeline or study.

    Everything else is explicitly not producer identity, and each exclusion is
    the rule table's own reading rather than ours. An `encoder` is a library
    that can write any analysis and so identifies none. A `conversion` string
    says on its face that a third party converted the object. An `application`
    is a viewer or an annotation program. An `acquisition_vendor` on a derived
    object is the identity of equipment that did not produce it. An
    `institution` names an organisation without naming what it ran, which is
    that category's own definition in `provenance.py`.

    This is the rule that replaced a permissive token test. That test graded
    `OHIF-XNAT Viewer 3.2.0`, `GE MEDICAL SYSTEMS`, `Biograph 64`, `PixelMed`
    and `Reader1` as producer identity and returned 96 percent informative,
    which measured the presence of any non-generic word rather than the presence
    of an algorithm name.
    """
    for value in values:
        category, rule, _ = classify_value(value)
        if category == "named_analysis":
            return True, str(value)[:80], rule
    return False, "", ""


def grade_objects(frame: pd.DataFrame) -> pd.DataFrame:
    """Three grades per object. Absence of a Type 3 carrier is never a defect."""
    grades, reasons, categories = [], [], []
    for row in frame.itertuples():
        violation = ""
        if row.sop_class_name in TYPE1_CLASSES:
            for carrier in TYPE1_CARRIERS:
                state = getattr(row, carrier + "_state", "absent")
                if state in ("absent", "empty"):
                    violation = "%s %s, Type 1 here" % (carrier, state)
                    break
        # Type 2 binding, added after the PS3.3 2026c re-verification. General
        # Equipment has Usage M in all eight measured IODs and Manufacturer is
        # Type 2 in it, so an absent Manufacturer is a violation everywhere, not
        # only in the two Enhanced IODs. Zero length is legal for Type 2 and is
        # not counted. Grading on the Enhanced module alone put the 40 Key
        # Object Selection objects in `conformant but uninformative` while the
        # conformance arm called all 40 net, a contradiction inside one paper.
        if not violation and getattr(row, TYPE2_CARRIER + "_state", "") == "absent":
            violation = "%s absent, Type 2 in a module with Usage M here" % TYPE2_CARRIER
        pool = identity_values(row)
        named, value, rule = names_producer(pool)
        categories.append(";".join(sorted(
            {classify_value(v)[0] for v in pool})) or "absent")
        if violation:
            grades.append("non-conformant")
            reasons.append(violation)
        elif named:
            grades.append("informative")
            reasons.append("%s names %s" % (rule, value))
        else:
            grades.append("conformant but uninformative")
            reasons.append("no carrier names a producing analysis; every "
                           "populated value is an encoder, a converter, an "
                           "application, acquisition equipment or an institution")
    out = frame.copy()
    out["grade"] = grades
    out["grade_reason"] = reasons
    out["categories_present"] = categories
    return out


def unclassified_values(frame: pd.DataFrame) -> pd.DataFrame:
    """Every value the rule table has no rule for, printed verbatim.

    This is where the grading could move. A named analysis with no rule is
    graded uninformative, so publishing the list is what stops that being a
    silent undercount rather than a stated one.
    """
    counts = Counter()
    for row in frame.itertuples():
        for value in identity_values(row):
            category, _, _ = classify_value(value)
            if category == "unclassified":
                counts[(row.sop_class_name, str(value)[:70])] += 1
    return pd.DataFrame(
        [{"sop_class_name": s, "value": v, "objects": n}
         for (s, v), n in counts.most_common()]) if counts else pd.DataFrame(
        columns=["sop_class_name", "value", "objects"])


def type1_corroboration() -> pd.DataFrame:
    """Do the validators independently flag the Type 1 states we counted.

    This is the check that keeps the grading out of self-adjudication. The three
    state capture says an attribute is absent or zero length; whether that is
    non-conformant is PS3.3's answer, read by two third-party tools from
    different codebases. Their counts are reported beside ours and never merged
    with them, so a reader can see the agreement rather than take it on trust.

    Segmentation only: it is the only class in the tabulation whose per-object
    validator messages are on disk and whose IOD binds these attributes Type 1.
    """
    rows = Counter()
    for record in phase3.load_records():
        for obj in record.get("objects", []):
            if obj.get("status") != "OK":
                continue
            for carrier in TYPE1_CARRIERS:
                state = obj.get(carrier + "_state")
                if state not in ("absent", "empty"):
                    continue
                spaced = re.sub(r"(?<!^)(?=[A-Z])", " ", carrier)
                for validator in ("dciodvfy", "dicom-validator"):
                    hit = any(
                        v == validator and (carrier in template or spaced in template)
                        for v, _, _, template in obj.get("messages", []))
                    rows[(carrier, state, validator, hit)] += 1
    out = []
    for (carrier, state, validator, hit), n in rows.items():
        out.append({"carrier": carrier, "state_we_recorded": state,
                    "validator": validator,
                    "validator_raised_a_matching_message": hit, "objects": n})
    return pd.DataFrame(out).sort_values(
        ["carrier", "state_we_recorded", "validator"]) if out else pd.DataFrame(
        columns=["carrier", "state_we_recorded", "validator",
                 "validator_raised_a_matching_message", "objects"])


def category_table(frame: pd.DataFrame) -> pd.DataFrame:
    """What the values name, by the published category, per class."""
    counts = Counter()
    for row in frame.itertuples():
        for value in identity_values(row):
            category, _, extra = classify_value(value)
            counts[(row.sop_class_name, category)] += 1
            if extra:
                counts[(row.sop_class_name, category + " (additive rule)")] += 1
    return pd.DataFrame(
        [{"sop_class_name": s, "category": c, "values": n}
         for (s, c), n in counts.items()]).sort_values(
        ["sop_class_name", "values"], ascending=[True, False])


def grade_table(graded: pd.DataFrame, key: str) -> pd.DataFrame:
    rows = []
    group = ([("sop_class_name", g) for g in graded.groupby("sop_class_name")]
             if key == "sop_class_name" else
             [("ar", g) for g in graded.groupby(["sop_class_name",
                                                 "analysis_result_id"])])
    for _, (name, sub) in group:
        base = ({"sop_class_name": name, "analysis_result_id": "(all)"}
                if key == "sop_class_name"
                else {"sop_class_name": name[0], "analysis_result_id": name[1]})
        counts = Counter(sub["grade"])
        row = dict(base, objects=int(len(sub)))
        for g in GRADES:
            row[g] = counts.get(g, 0)
            row["pct_" + g.split()[0]] = round(100 * counts.get(g, 0) / len(sub), 2)
        row["sum_pct"] = round(sum(row["pct_" + g.split()[0]] for g in GRADES), 2)
        rows.append(row)
    return pd.DataFrame(rows)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.parse_args(argv)
    from .claim3_report import main as report_main
    return report_main()


if __name__ == "__main__":
    sys.exit(main())
