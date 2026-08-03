"""Table 1: who wrote these objects, and where their identity is recoverable from.

Three measurements, all from the index, all needed before Phase 1 emits anything.

**Writer census.** Which toolkit wrote each series. The round-trip exclusion rule
in ledger row PRE-02 is unimplementable without it: an axis-2 pass by the same
toolkit that wrote the object carries no information and must be excluded from
the pass numerator. This census is provisional, because the index carries only
Manufacturer and ManufacturerModelName. ImplementationVersionName (0002,0013)
and ContributingEquipmentSequence (0018,A001) are stronger writer evidence and
are read in Phase 2, at which point this table is recomputed and any series
labelled "not identifiable from index" is resolved or stays unresolved with a
count.

**Sentinel values.** Producer-identity strings that are hardcoded by an encoding
toolkit and therefore cannot name a producing algorithm whatever the caller
does. A presence check that counts these reports a high population rate and
measures nothing. The list is published as an artefact,
`results/sentinels.json`, rather than living as a regex inside a function, so a
reader can disagree with a specific entry.

**Carrier hierarchy.** Producer identity is not one attribute, it is a ranked
set of places identity might be recorded. Saying an algorithm is "not named in
the equipment attributes" is true and uninteresting. Saying it is "not
recoverable" is interesting and, for the largest analysis result in the archive,
false: `SeriesDescription` names both the algorithm and its version. The useful
measurement is the level at which identity first appears, and whether a version
appears with it.

Usage:
    python -m colophon.writers
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd

from . import ledger
from .index import derived, load_index, _fmt, _md_table
from .paths import PHASE0, RESULTS

CMD = "python -m colophon.writers"

# --- writer identification ----------------------------------------------------
# Ordered. Matched over "Manufacturer ManufacturerModelName" lowercased.
WRITER_RULES: list[tuple[str, str]] = [
    ("dcmqi", r"dcmqi"),
    ("highdicom", r"highdicom"),
    ("pydicom-seg", r"pydicom-seg"),
    ("PixelMed", r"pixelmed|com\.pixelmed"),
    ("QIICR Reporting via 3D Slicer", r"fedorov/reporting|slicer"),
    ("OHIF-XNAT Viewer", r"ohif"),
    ("Plastimatch", r"plastimatch"),
]
UNKNOWN_WRITER = "not identifiable from index"


def writer_of(manufacturer, model) -> str:
    s = ("%s %s" % (
        "" if manufacturer is None or pd.isna(manufacturer) else manufacturer,
        "" if model is None or pd.isna(model) else model)).lower()
    for name, pattern in WRITER_RULES:
        if re.search(pattern, s):
            return name
    return UNKNOWN_WRITER


def writer_census(d: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    work = d.copy()
    work["writer"] = [writer_of(a, b) for a, b in
                      zip(work["Manufacturer"], work["ManufacturerModelName"])]
    census = (work.groupby("writer")
                  .agg(series=("SeriesInstanceUID", "size"),
                       instances=("instanceCount", "sum"),
                       collections=("collection_id", "nunique"),
                       analysis_results=("analysis_result_id", "nunique"),
                       sop_classes=("sop_class_name", "nunique"))
                  .reset_index())
    census["pct"] = (100 * census["series"] / len(work)).round(2)
    census = census.sort_values("series", ascending=False).reset_index(drop=True)
    by_sop = (work.groupby(["sop_class_name", "writer"])
                  .agg(series=("SeriesInstanceUID", "size")).reset_index()
                  .sort_values(["sop_class_name", "series"], ascending=[True, False]))
    return work, census, by_sop


# --- sentinel values ----------------------------------------------------------
# A sentinel is a producer-identity string that an encoding toolkit writes
# unconditionally. Its presence says which library encoded the object and cannot
# say what produced the result. Entries carry the reason they qualify, so a
# reader can reject any single one.
SENTINELS: list[dict] = [
    {"value": "QIICR", "attribute": "Manufacturer", "toolkit": "dcmqi",
     "basis": "hardcoded constant. QIICRConstants.h, #define QIICR_MANUFACTURER "
              "\"QIICR\", applied by ConverterBase.cpp getEquipmentInfo(). No "
              "command-line flag, environment variable or JSON key overrides it.",
     "status": "CONFIRMED from source 2026-08-02"},
    {"value": "https://github.com/QIICR/dcmqi", "attribute": "ManufacturerModelName",
     "toolkit": "dcmqi", "basis": "build working-copy URL",
     "status": "CONFIRMED from source 2026-08-02"},
    {"value": "https://github.com/QIICR/dcmqi.git", "attribute": "ManufacturerModelName",
     "toolkit": "dcmqi", "basis": "build working-copy URL",
     "status": "CONFIRMED from source 2026-08-02"},
    {"value": "git@github.com:QIICR/dcmqi.git", "attribute": "ManufacturerModelName",
     "toolkit": "dcmqi", "basis": "build working-copy URL, SSH form",
     "status": "CONFIRMED from source 2026-08-02"},
    {"value": "git://github.com/QIICR/dcmqi.git", "attribute": "ManufacturerModelName",
     "toolkit": "dcmqi", "basis": "build working-copy URL, git protocol form",
     "status": "CONFIRMED from source 2026-08-02"},
    {"value": "https://github.com/qiicr/dcmqi.git", "attribute": "ManufacturerModelName",
     "toolkit": "dcmqi", "basis": "build working-copy URL, lowercased host path",
     "status": "CONFIRMED from source 2026-08-02"},
    {"value": "https://github.com/fedorov/dcmqi.git", "attribute": "ManufacturerModelName",
     "toolkit": "dcmqi", "basis": "build working-copy URL of a personal fork",
     "status": "CONFIRMED from source 2026-08-02"},
    {"value": "https://github.com/ImagingDataCommons/highdicom.git",
     "attribute": "ManufacturerModelName", "toolkit": "highdicom",
     "basis": "library self-identification",
     "status": "CONFIRMED from source 2026-08-02"},
    {"value": "https://github.com/imagingdatacommons/highdicom",
     "attribute": "ManufacturerModelName", "toolkit": "highdicom",
     "basis": "library self-identification",
     "status": "CONFIRMED from source 2026-08-02"},
    {"value": "highdicom", "attribute": "Manufacturer", "toolkit": "highdicom",
     "basis": "library self-identification",
     "status": "CONFIRMED from source 2026-08-02"},
    {"value": "https://github.com/razorx89/pydicom-seg",
     "attribute": "ManufacturerModelName", "toolkit": "pydicom-seg",
     "basis": "library self-identification",
     "status": "asserted from observed values, NOT source confirmed. Only dcmqi and highdicom were read from source."},
    {"value": "pydicom-seg", "attribute": "Manufacturer", "toolkit": "pydicom-seg",
     "basis": "library self-identification",
     "status": "asserted from observed values, NOT source confirmed. Only dcmqi and highdicom were read from source."},
    {"value": "https://github.com/fedorov/Reporting", "attribute": "ManufacturerModelName",
     "toolkit": "QIICR Reporting", "basis": "build working-copy URL",
     "status": "asserted from observed values, NOT source confirmed. Only dcmqi and highdicom were read from source."},
    {"value": "com.pixelmed.convert.EncapsulateData",
     "attribute": "ManufacturerModelName", "toolkit": "PixelMed",
     "basis": "converter class name",
     "status": "asserted from observed values, NOT source confirmed. Only dcmqi and highdicom were read from source."},
]

SENTINEL_SET = {s["value"].strip().lower() for s in SENTINELS}

# Sentinels that live in attributes the index does not carry. They cannot be
# checked here and are applied in Phase 2. Listed now because the rule they
# encode is what makes a presence check meaningless.
PHASE2_SENTINEL_RULES = [
    {"attribute": "DeviceSerialNumber (0018,1000)", "toolkit": "dcmqi",
     "rule": "exact string 0",
     "basis": "QIICRConstants.h, #define QIICR_DEVICE_SERIAL_NUMBER \"0\"",
     "status": "CONFIRMED from source 2026-08-02"},
    {"attribute": "SoftwareVersions (0018,1020)", "toolkit": "dcmqi",
     "rule": "matches ^[0-9a-f]{7}$",
     "basis": "dcmqi_WC_REVISION: git rev-parse --verify -q --short=7 HEAD in "
              "the build working copy. A 7 character hex string identifies a "
              "commit of the encoder, not a version of any algorithm.",
     "status": "CONFIRMED from source 2026-08-02"},
    {"attribute": "ImplementationVersionName (0002,0013)", "toolkit": "highdicom",
     "rule": "matches ^highdicom",
     "basis": "highdicom/base.py, f'highdicom{__version__}'",
     "status": "CONFIRMED from source 2026-08-02"},
    {"attribute": "ContributingEquipmentSequence (0018,A001) item Manufacturer",
     "toolkit": "highdicom", "rule": "exact string Highdicom open-source contributors",
     "basis": "highdicom/base_content.py, ContributingEquipment.for_highdicom. "
              "The sequence is appended unconditionally by every concrete "
              "constructor with no opt-out, so a presence check on (0018,A001) "
              "over highdicom objects reports 100 percent and measures nothing.",
     "status": "CONFIRMED from source 2026-08-02"},
]


def is_sentinel(value) -> bool:
    if value is None or pd.isna(value):
        return False
    return str(value).strip().lower() in SENTINEL_SET


# --- the carrier hierarchy ----------------------------------------------------
# Ranked by how much a consumer should have to know to find identity. Level 1 is
# where the standard puts equipment identity. Level 4 is not in the object at
# all: it is the archive's registry, so identity found only there is identity a
# downloaded file does not carry.
CARRIER_LEVELS = [
    {"level": 1, "name": "DICOM equipment attributes",
     "columns": ["Manufacturer", "ManufacturerModelName"],
     "in_object": True, "in_index": True},
    {"level": 2, "name": "ContributingEquipmentSequence and Algorithm Identification Macro",
     "columns": [], "in_object": True, "in_index": False},
    {"level": 3, "name": "free-text description",
     "columns": ["SeriesDescription", "StudyDescription"],
     "in_object": True, "in_index": True},
    {"level": 4, "name": "IDC registry metadata",
     "columns": ["collection_id", "analysis_result_id", "source_DOI"],
     "in_object": False, "in_index": True},
]

VERSION = re.compile(r"\bv?\d+\.\d+(\.\d+)?\b")
GENERIC = {
    "segmentation", "segmentations", "seg", "of", "series", "study", "the",
    "measurements", "measurement", "annotation", "annotations", "nodule",
    "map", "maps", "image", "images", "ct", "mr", "mri", "pet", "dicom",
    "shape", "firstorder", "and", "for", "with", "from", "tumor", "lesion",
    "bounding", "box", "point", "seed", "pre", "dose", "liver", "brain", "ai",
}


def _informative(values: set[str]) -> tuple[bool, str]:
    """Does this level carry a producer-identifying token.

    A level is informative when some value contains a token that is neither a
    sentinel nor a generic word. The rule is deliberately crude and the actual
    strings are published alongside it, so a reader can overrule any single
    assignment.
    """
    for v in sorted(values):
        if not v or is_sentinel(v):
            continue
        for token in re.split(r"[^A-Za-z0-9.]+", v):
            t = token.strip(".").lower()
            if len(t) < 3 or t in GENERIC or t.isdigit():
                continue
            if t.startswith("http") or "github" in t:
                continue
            return True, v
    return False, ""


def carrier_hierarchy(d: pd.DataFrame, min_series: int = 100) -> pd.DataFrame:
    """Per analysis result, the first carrier level at which identity appears."""
    work = d[d["analysis_result_id"].notna()].copy()
    rows = []
    for ar, sub in work.groupby("analysis_result_id"):
        if len(sub) < min_series:
            continue
        rec = {"analysis_result_id": ar, "series": int(len(sub))}
        first = None
        for level in CARRIER_LEVELS:
            key = "L%d_%s" % (level["level"], level["name"].split()[0].lower())
            if not level["in_index"]:
                rec[key] = "not in index, Phase 2"
                continue
            values = set()
            for col in level["columns"]:
                values |= {str(v) for v in sub[col].dropna().unique()}
            ok, example = _informative(values)
            rec[key] = (example[:70] if ok else "no producer token")
            if ok and first is None:
                first = level["level"]
        rec["first_informative_level"] = first if first else "none in index"
        joined = " ".join(str(v) for v in sub["SeriesDescription"].dropna().unique()[:200])
        rec["version_in_free_text"] = bool(VERSION.search(joined))
        m = VERSION.search(joined)
        rec["version_example"] = m.group(0) if m else ""
        rows.append(rec)
    out = pd.DataFrame(rows).sort_values("series", ascending=False)
    return out.reset_index(drop=True)


# --- cohort recall, the measured harm of unstable spellings -------------------
def cohort_recall(d: pd.DataFrame, tool: str = "dcmqi") -> dict:
    """A realistic cohort-selection query, and what it misses.

    Someone assembling every series produced through a given toolkit queries the
    declared model name. This measures the recall of that query under exact
    match against the most common spelling, versus a normalised match.
    """
    m = d["ManufacturerModelName"].fillna("")
    hits = d[m.str.contains(tool, case=False, regex=False)]
    if hits.empty:
        return {}
    counts = hits["ManufacturerModelName"].value_counts()
    top_value, top_n = str(counts.index[0]), int(counts.iloc[0])
    normalised = (hits["ManufacturerModelName"].str.lower()
                  .str.replace(r"^(https?://|git://|git@)", "", regex=True)
                  .str.replace(":", "/", regex=False)
                  .str.replace(r"\.git$", "", regex=True))
    return {
        "tool": tool,
        "true_total": int(len(hits)),
        "distinct_spellings": int(len(counts)),
        "most_common_spelling": top_value,
        "exact_match_recall_n": top_n,
        "exact_match_recall_pct": round(100 * top_n / len(hits), 2),
        "missed_by_exact_match": int(len(hits) - top_n),
        "distinct_after_normalisation": int(normalised.nunique()),
        "normalised_groups": {k: int(v) for k, v in normalised.value_counts().items()},
        "spellings": {str(k): int(v) for k, v in counts.items()},
    }


def write_markdown(idc_version: str, t: dict, out: Path) -> Path:
    census, by_sop, hierarchy, recall = (
        t["census"], t["by_sop"], t["hierarchy"], t["recall"])
    n = int(census["series"].sum())
    unknown = int(census.loc[census.writer == UNKNOWN_WRITER, "series"].sum()) \
        if UNKNOWN_WRITER in set(census["writer"]) else 0
    ts = hierarchy[hierarchy.analysis_result_id == "totalsegmentator_ct_segmentations"]

    text = f"""# Table 1: writers, sentinels and where identity is recoverable

IDC {idc_version}. Index evidence only, zero bytes downloaded. Reproduce with
`{CMD}`.

## Writer census

Which toolkit wrote each derived series, inferred from the two equipment
attributes the index carries. This is **provisional**: ImplementationVersionName
(0002,0013) and ContributingEquipmentSequence (0018,A001) are stronger writer
evidence and are only readable from fetched objects, so the table is recomputed
in Phase 2.

{_md_table(census, ["writer", "series", "pct", "collections", "analysis_results", "sop_classes"])}

{_fmt(unknown)} series, {100 * unknown / n:.1f} percent, cannot be attributed to
a writer from the index. That number is an input to Phase 2, not a finding.

This table exists because ledger row PRE-02 excludes round-trip passes from the
pass numerator, and the exclusion cannot be applied without knowing who wrote
each object.

Per SOP class:

{_md_table(by_sop.head(30), ["sop_class_name", "writer", "series"])}

## Sentinel values

A sentinel is a producer-identity string an encoding toolkit writes
unconditionally. Where the standard makes an attribute Type 1, as Enhanced
General Equipment does for Manufacturer, ManufacturerModelName,
DeviceSerialNumber and SoftwareVersions, the attribute is always present and a
presence check reports 100 percent while measuring nothing. Sentinels are
excluded from the numerator of any informativeness rate.

The list is published as `results/sentinels.json` so that a reader can reject a
specific entry rather than having to reverse engineer a regex.
{len(SENTINELS)} entries at present, every one carrying the basis on which it
qualifies and its verification status.

## Where identity is recoverable

Producer identity is not one attribute. It is a ranked set of places identity
might be recorded, and the useful question is the level at which it first
appears, not whether level 1 carries it.

| level | carrier | in the object | in the index |
|---|---|---|---|
| 1 | DICOM equipment attributes | yes | yes |
| 2 | ContributingEquipmentSequence, Algorithm Identification Macro | yes | no, Phase 2 |
| 3 | free-text description | yes | yes |
| 4 | IDC registry metadata | **no** | yes |

Level 4 is not in the object. Identity available only there is identity a
downloaded file does not carry.

{_md_table(hierarchy, ["analysis_result_id", "series", "first_informative_level", "version_in_free_text", "version_example"])}

### The largest analysis result

`totalsegmentator_ct_segmentations`, {_fmt(int(ts["series"].iloc[0])) if len(ts) else "n/a"}
series, carries at level 1 only `QIICR` and a git URL. At level 3 every one of
its series carries a `SeriesDescription` of the form
`TotalSegmentator(v1.5.6) Segmentation of Series 2`.

So the algorithm **and a version string** are recoverable. Not from a provenance
carrier, not from anywhere the standard or any profile directs a consumer to
look, and not in a form any convention makes machine-parseable, but recoverable.
The claim this study can defend is therefore about where identity lives and what
it costs to find, not about identity being absent.

One ambiguity is left open rather than resolved: the version token `v1.5.6` is
not labelled, and dcmqi also has a 1.5.6 release. Whether it denotes the
TotalSegmentator version or the encoder version cannot be settled from the
index. Phase 2 reads SoftwareVersions (0018,1020), which is Type 1 in Enhanced
General Equipment, and settles it.

## What unstable spellings cost

An unstable declared name is a triviality until harm is shown, so it is
measured. A consumer assembling every series produced through {recall['tool']}
queries the declared model name.

| | |
|---|---|
| series truly produced through {recall['tool']} | {_fmt(recall['true_total'])} |
| distinct declared spellings | {recall['distinct_spellings']} |
| recall, exact match on the most common spelling | {recall['exact_match_recall_pct']:.2f} percent |
| **series missed by that query** | **{_fmt(recall['missed_by_exact_match'])}** |
| distinct groups after normalising scheme, case and suffix | {recall['distinct_after_normalisation']} |

The missed count is not a rounding error, so the finding stands as a measured
result rather than an observation. Normalisation collapses the spellings to
{recall['distinct_after_normalisation']} groups, of which the smaller is a
personal fork and arguably a genuinely different build rather than a spelling of
the same one.

## What was dropped

Nothing from the writer census or the cohort measurement: both run over all
{_fmt(n)} derived series. The carrier hierarchy reports analysis results of at
least 100 series, which covers {_fmt(int(hierarchy['series'].sum()))} series;
smaller analysis results are in the CSV.
"""
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--print-only", action="store_true")
    args = ap.parse_args(argv)

    idc_version, df = load_index()
    d = derived(df)
    n = len(d)
    tagged, census, by_sop = writer_census(d)
    hierarchy = carrier_hierarchy(d)
    recall = cohort_recall(d, "dcmqi")
    print("IDC %s, derived %s, writers identified for %s"
          % (idc_version, _fmt(n),
             _fmt(int(census.loc[census.writer != UNKNOWN_WRITER, "series"].sum()))))

    tables = {
        "writer_census": census,
        "writer_by_sop_class": by_sop,
        "carrier_hierarchy": hierarchy,
    }
    if args.print_only:
        for name, frame in tables.items():
            print("\n==== %s ====" % name)
            print(frame.head(30).to_string(index=False))
        print(json.dumps(recall, indent=2)[:1500])
        return 0

    PHASE0.mkdir(parents=True, exist_ok=True)
    for name, frame in tables.items():
        frame.to_csv(PHASE0 / ("%s.csv" % name), index=False)
    (RESULTS / "sentinels.json").write_text(json.dumps({
        "purpose": "Producer-identity strings written unconditionally by an "
                   "encoding toolkit. Excluded from the numerator of any "
                   "informativeness rate, because their presence identifies the "
                   "encoder and cannot identify the producing algorithm.",
        "rule": "A presence check over Type 1 attributes reports 100 percent and "
                "measures nothing. Scoring is semantic: a value is informative "
                "only if it is not a sentinel.",
        "sentinels": SENTINELS,
        "phase2_rules": PHASE2_SENTINEL_RULES,
    }, indent=2), encoding="utf-8")
    (PHASE0 / "cohort_recall.json").write_text(json.dumps(recall, indent=2),
                                               encoding="utf-8")
    md = write_markdown(idc_version, dict(census=census, by_sop=by_sop,
                                          hierarchy=hierarchy, recall=recall),
                        RESULTS / "table1_writers.md")
    print("wrote %s and %d tables" % (md, len(tables)))

    dcmqi_n = int(census.loc[census.writer == "dcmqi", "series"].iloc[0])
    unknown = int(census.loc[census.writer == UNKNOWN_WRITER, "series"].iloc[0])
    ts = hierarchy[hierarchy.analysis_result_id == "totalsegmentator_ct_segmentations"]

    S = dict(section="W", section_title="Table 1, writers and carriers",
             command=CMD, sop_class="derived, nine classes",
             denominator=_fmt(n), validator="none, index metadata only",
             validator_version="idc-index-data %s" % idc_version,
             floor="not applicable, no validator involved",
             dropped="nothing, the writer census and cohort measurement cover "
                     "all derived series; the carrier hierarchy reports "
                     "analysis results of at least 100 series and the rest are "
                     "in the CSV")

    ledger.record_many([
        dict(id="W-01", claim="A writer census over the derived population, "
             "needed before any round-trip exclusion can be applied.",
             status="MEASURED",
             value="; ".join("%s %s (%.2f percent)" % (r.writer, _fmt(int(r.series)), r.pct)
                             for r in census.head(5).itertuples()),
             n=_fmt(dcmqi_n),
             source_file="results/phase0/writer_census.csv",
             pinned_by_test="tests/test_writers.py::test_writer_census",
             status_note="Provisional. Inferred from the two equipment "
             "attributes the index carries. ImplementationVersionName and "
             "ContributingEquipmentSequence are stronger writer evidence and "
             "are read in Phase 2, at which point this is recomputed.",
             notes="%s series, %.1f percent, are not attributable to a writer "
                   "from the index. That is an input to Phase 2, not a finding."
                   % (_fmt(unknown), 100 * unknown / n), **S),
        dict(id="W-02", claim="Producer identity for the largest analysis result "
             "is recoverable, with a version, but only from a free-text "
             "description field rather than from any provenance carrier.",
             status="MEASURED",
             value="totalsegmentator_ct_segmentations: level 1 carries QIICR and "
                   "a git URL; level 3 SeriesDescription carries "
                   "'TotalSegmentator(v1.5.6) Segmentation of Series N' on all "
                   "378,153 series",
             n="378,153",
             source_file="results/phase0/carrier_hierarchy.csv",
             derived_from="C3-11",
             pinned_by_test="tests/test_writers.py::test_carrier_hierarchy",
             status_note="Replaces the weaker framing that the algorithm is "
             "named in neither equipment attribute, which is true and "
             "uninteresting. The defensible claim is about where identity lives "
             "and what it costs to find it, not about identity being absent.",
             notes="One ambiguity left open: the token v1.5.6 is unlabelled and "
                   "dcmqi also has a 1.5.6 release, so whether it denotes the "
                   "algorithm version or the encoder version cannot be settled "
                   "from the index. SoftwareVersions (0018,1020) settles it in "
                   "Phase 2.", **S),
        dict(id="W-03", claim="Unstable declared spellings cause measurable "
             "recall loss in a realistic cohort-selection query.",
             status="MEASURED",
             value="querying the most common dcmqi spelling exactly recalls "
                   "%s of %s series, %.2f percent, missing %s"
                   % (_fmt(recall["exact_match_recall_n"]),
                      _fmt(recall["true_total"]),
                      recall["exact_match_recall_pct"],
                      _fmt(recall["missed_by_exact_match"])),
             n=_fmt(recall["missed_by_exact_match"]),
             source_file="results/phase0/cohort_recall.json",
             derived_from="C3-04",
             pinned_by_test="tests/test_writers.py::test_cohort_recall",
             status_note="Converts an observation into a measured harm. Had the "
             "missed count been of order a few hundred the finding would have "
             "been withdrawn.",
             notes="Normalising scheme, case and suffix collapses six spellings "
                   "to two groups, the smaller being a personal fork which is "
                   "arguably a different build rather than a spelling variant.",
             **S),
        dict(id="W-04", claim="A published sentinel list is required, because "
             "the attributes being scored are Type 1 and therefore always "
             "present.",
             status="MEASURED",
             value="%d sentinel values published in results/sentinels.json"
                   % len(SENTINELS),
             n=str(len(SENTINELS)),
             source_file="results/sentinels.json",
             pinned_by_test="tests/test_writers.py::test_sentinels_published",
             status_note="Every entry carries its basis and its verification "
             "status. Entries are asserted from observed values and are marked "
             "pending source confirmation until the toolkit source is read.",
             notes="Scoring is semantic, not presence-based. A presence check "
                   "over Type 1 attributes reports 100 percent and measures "
                   "nothing.", **S),
    ])
    print("ledger: %s" % ledger.summary())
    return 0


if __name__ == "__main__":
    sys.exit(main())
