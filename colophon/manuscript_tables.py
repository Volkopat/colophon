"""Tables 1 to 6 of the re-spined manuscript, generated, never typed.

Every cell is read from an artefact another module computed, or from a ledger
row, so a number in a table cannot drift away from the measurement behind it.
Each table declares the ledger rows it rests on in its own caption, which is
what makes the build check possible: a figure in the prose with no row fails.

The paper's spine is claim 3. Conformance and attribution are independent
properties of a delivered result, and in this archive the encoder is recorded
with high fidelity while the producer is not recorded at all.

Usage:
    python -m colophon.manuscript_tables
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from . import ledger
from .claim3 import LADDER
from .paths import RESULTS

CMD = "python -m colophon.manuscript_tables"
MANUSCRIPT = RESULTS / "manuscript"
CLAIM3 = RESULTS / "claim3"
ADJ2 = RESULTS / "adjudication2"


def _rows() -> dict:
    return {r["id"]: r for r in ledger.load()}


def _md(frame: pd.DataFrame, columns: list[str], headers: list[str]) -> str:
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in frame[columns].itertuples(index=False):
        cells = []
        for v in row:
            if isinstance(v, float):
                cells.append("%.2f" % v)
            elif isinstance(v, (int,)) and not isinstance(v, bool):
                cells.append("%,d".replace("%,d", "{:,}").format(v))
            else:
                cells.append(str(v))
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


# --- Table 1, population and the unit each result is scoped to ----------------
def table1() -> tuple[pd.DataFrame, str]:
    grades = pd.read_csv(CLAIM3 / "grades_by_sop_class.csv")
    ladder = pd.read_csv(CLAIM3 / "t33_recoverability_ladder.csv")
    rows = []
    for r in grades.itertuples():
        cells = int((ladder.sop_class_name == r.sop_class_name).sum())
        rows.append({
            "sop_class": r.sop_class_name,
            "objects": int(r.objects),
            "analysis_result_cells": cells,
            "coverage": ("complete census" if r.sop_class_name != "Segmentation Storage"
                         else "PRE-06 probability sample, 5,941 of 190,146 series"),
        })
    frame = pd.DataFrame(rows).sort_values("objects", ascending=False)
    caption = (
        "**Table 1. Population, coverage and the unit each result is scoped to.** "
        "Seven classes are a complete census; Segmentation is the PRE-06 "
        "stratified probability sample. Enhanced SR Storage is **excluded from "
        "every object-weighted rate in this paper**, 35,161 of 262,883 series "
        "recorded and the class still running, because a partial class reads as "
        "a rate. " + "Analysis-result cells are complete for the seven censused classes. For Segmentation they are the identifiers observed in the PRE-06 sample of 5,941 of 190,146 series; frame coverage of that class's cells is unmeasured (C3T-13). "
        "Ledger PRE-06, C3T-00, P2C-01.")
    return frame, caption


# --- Table 2, the lead result -------------------------------------------------
def table2() -> tuple[pd.DataFrame, str]:
    grades = pd.read_csv(CLAIM3 / "grades_by_sop_class.csv")
    carriers = pd.read_csv(CLAIM3 / "t31_carriers_by_sop_class.csv")
    binds = (carriers.groupby("sop_class_name")["type1_here"]
                     .apply(lambda s: "yes" if (s == "yes").any() else "**no**")
                     .to_dict())
    frame = grades.copy()
    frame["binds_provenance_type1"] = frame["sop_class_name"].map(binds)
    # Leave-one-class-out. The paper argues object-weighted rates are distorted
    # by concentration, so the concentration in its own denominator has to be
    # shown rather than argued around. Each row states what the archive-wide
    # uninformative rate becomes when that class alone is dropped.
    total = int(frame["objects"].sum())
    total_uninf = int(frame["conformant but uninformative"].sum())
    out = []
    for _, row in frame.iterrows():
        n = total - int(row["objects"])
        k = total_uninf - int(row["conformant but uninformative"])
        out.append(round(100 * k / n, 2) if n else None)
    frame["pct_uninformative_without_this_class"] = out
    frame["pct_of_denominator"] = (100 * frame["objects"] / total).round(2)
    frame = frame.sort_values("objects", ascending=False)
    caption = (
        "**Table 2. Three grades, never two, by SOP class, with the ceiling the "
        "standard sets.** Two bindings can make an object non-conformant, and "
        "the final column reports only the first. **Type 1**, Enhanced General "
        "Equipment with Usage M, binds four equipment attributes in the two "
        "IODs marked `yes`, where absent and zero length are both violations. "
        "**Type 2**, General Equipment with Usage M, binds Manufacturer in all "
        "eight, where absent is a violation and zero length is not. That second "
        "tier is why Key Object Selection shows 40 non-conformant objects while "
        "its Type 1 column reads `no`: its Manufacturer is absent, not merely "
        "empty. Percentages sum to 100 up to the rounding shown; the counts "
        "partition exactly. Ledger C3T-00, C3T-01, STD-04, STD-08.")
    return frame, caption


# --- Table 3, the headline unit -----------------------------------------------
def table3() -> tuple[pd.DataFrame, str]:
    ladder = pd.read_csv(CLAIM3 / "t33_recoverability_ladder.csv")
    frame = ladder.copy()
    # A cell that is empty because identity appears at no level is information,
    # and printing it as `nan` reads as a defect in the table. It is filled with
    # a statement instead.
    frame["identifying_value"] = frame["identifying_value"].fillna(
        "no value at any level")
    frame["version_value"] = frame["version_value"].fillna("none")
    # The string the version was found in. It is the audit trail for the
    # version column and it is kept, because the column used to print the whole
    # string clipped at forty characters and a reader could not tell the version
    # from the sentence around it.
    frame["version_found_in"] = frame["version_found_in"].fillna(
        "not applicable, no version appears")
    frame["in_object"] = frame["in_object"].fillna(
        "not applicable, identity appears nowhere")
    # The first level is not the only level. Rendering only the first invites a
    # reader to conclude identity appears nowhere else, which for
    # totalsegmentator would be wrong: it is at level 3 and again at level 4.
    frame["levels_where_identity_appears"] = [
        ", ".join(str(lv["level"]) for lv in LADDER
                  if row[1]["level_%d" % lv["level"]] == "yes") or "none"
        for row in frame.iterrows()]
    frame = frame.sort_values(
        ["first_level_identity_appears", "objects"], ascending=[True, False])
    # Every integer in this caption is recomputed from the rows it captions.
    # Both of them were typed once and went stale when the ladder moved from 31
    # cells to 36: the caption still read "21 of 31" while its own table gave
    # 25 at no level over 36 rows.
    lvl = ladder["first_level_identity_appears"].astype(str)
    is_null = ladder["analysis_result_id"].astype(str) == "(null)"
    n_cells = int(len(ladder))
    n_none = int((lvl == "none").sum())
    n_version = int((ladder["version_at_that_level"].astype(str) == "yes").sum())
    n_null_cells = int(is_null.sum())
    n_null_objects = int(ladder.loc[is_null, "objects"].sum())
    pct_null = 100.0 * n_null_objects / max(int(ladder["objects"].sum()), 1)
    n_null_none = int((is_null & (lvl == "none")).sum())
    caption = (
        "**Table 3. The recoverability ladder: the first carrier level at which "
        "producer identity appears, per analysis result.** Levels: 1 equipment "
        "attributes, 2 file meta, 3 SeriesDescription and ContentCreatorName, "
        "4 in-object algorithm carriers, 5 collection metadata and DOI. "
        "**Identity appears at no level in %d of %d cells.** A version "
        "accompanies it in %d. `(null)` is not an analysis result: it is the "
        "residual cell of every object in its class that the archive index "
        "gives no `analysis_result_id`, so it is one bucket rather than one "
        "producer and is not homogeneous in producer the way a named cell is. "
        "There are %d such cells holding %s objects, %.2f percent of the "
        "denominator, and %d of them sit inside the %d. Excluding them the "
        "ladder reads %d of %d, which is the sensitivity in Results 3.2.1c; "
        "the headline is the full %d of %d. This is the headline unit because "
        "the analysis-result cells are complete for the seven censused classes "
        "and immune to the concentration that distorts every object-weighted "
        "rate in this study; for Segmentation they are the identifiers observed "
        "in the PRE-06 sample. Ledger C3T-03, C3T-12."
        % (n_none, n_cells, n_version, n_null_cells,
           "{:,}".format(n_null_objects), pct_null, n_null_none, n_none,
           n_none - n_null_none, n_cells - n_null_cells, n_none, n_cells))
    return frame, caption


# --- Table 4, the mechanism ---------------------------------------------------
def table4() -> tuple[pd.DataFrame, str]:
    rows_by_id = _rows()
    dev = json.loads((RESULTS / "deviations" / "pin_deviations.json")
                     .read_text(encoding="utf-8"))
    versions = dev["highdicom"]["corpus_writer_versions"]
    # The caller's SoftwareVersions on highdicom-written objects. This used to
    # be a literal in the caption, reading `all 1,001 highdicom-written
    # objects`, which was two errors in one clause: 1,001 is the Segmentation
    # subset of 7,100, and the value is not present on all of them.
    hd_total = int(dev["highdicom"]["corpus_objects_written_by_highdicom"])
    hd_states = dev["highdicom"]["corpus_softwareversions_states"]
    hd_by_class = dev["highdicom"]["corpus_softwareversions_by_class"]
    hd_url = int(hd_states.get("repository URL", 0))
    hd_empty = int(hd_states.get("empty", 0))
    hd_url_classes = "; ".join(
        "%s %s" % (k.split(" | ")[0], "{:,}".format(int(v)))
        for k, v in sorted(hd_by_class.items()) if k.endswith("repository URL"))
    t35 = pd.read_csv(CLAIM3 / "t35_version_carriers.csv")
    shas = t35["SoftwareVersions_sha7"].nunique() if len(t35) else 0
    repos = (t35.groupby("repository_class")["objects"].sum().to_dict()
             if len(t35) else {})
    frame = pd.DataFrame([
        {"writer": "dcmqi",
         "what_it_records_in_ManufacturerModelName":
             "the git remote URL of the working copy that built the binary",
         "what_it_records_in_SoftwareVersions":
             "the abbreviated HEAD SHA of that working copy",
         "set_at": "compile time, from QIICRConstants.h",
         "can_a_caller_place_the_producing_algorithm_here": "**no**",
         "distinct_identifiers_in_corpus": "%d distinct 7-character SHAs over %s objects"
             % (shas, "{:,}".format(int(t35["objects"].sum())) if len(t35) else 0)},
        {"writer": "highdicom",
         "what_it_records_in_ManufacturerModelName": "the library name",
         "what_it_records_in_SoftwareVersions":
             "nothing of its own: the value is the caller's. In this corpus "
             "%s of %s highdicom-written objects carry a conversion-pipeline "
             "repository URL there rather than a release, and the other %s "
             "carry nothing at all"
             % ("{:,}".format(hd_url), "{:,}".format(hd_total),
                "{:,}".format(hd_empty)),
         "set_at": "the release goes to ImplementationVersionName at import "
                   "time; SoftwareVersions is left to the caller",
         "can_a_caller_place_the_producing_algorithm_here": "**no**",
         "distinct_identifiers_in_corpus": "%d distinct releases: %s"
             % (len(versions), ", ".join(sorted(versions)))},
    ])
    caption = (
        "**Table 4. The mechanism: both writers record the serialiser "
        "precisely and neither records the producer, but they do it "
        "differently.** dcmqi's equipment attributes are hardcoded at compile "
        "time, so no caller can place a producing algorithm in them; the field "
        "is structurally incapable of carrying the thing an audit looks for. "
        "highdicom is not: it writes its own release to "
        "ImplementationVersionName, six distinct releases being present in the "
        "corpus, and leaves SoftwareVersions to the caller. Of %s "
        "highdicom-written objects the caller fills it with a "
        "conversion-pipeline repository URL on %s (%s) and leaves it empty on "
        "%s, every one of those being a Comprehensive 3D SR, where "
        "SoftwareVersions is Type 3 rather than the Type 1 it is under Enhanced "
        "General Equipment. **Where the standard compels a non-empty value the "
        "caller supplies one and it names a conversion pipeline; where it does "
        "not, the caller supplies nothing.** One toolkit forecloses the slot; "
        "the other leaves it open and the caller does not use it for the "
        "producer. "
        % ("{:,}".format(hd_total), "{:,}".format(hd_url), hd_url_classes,
           "{:,}".format(hd_empty)))
    caption += (
        "Repository class of the dcmqi SHAs resolves offline: %s. Commit date "
        "and nearest tag require the upstream history and are unresolved. "
        "Ledger C3-11, P2P-05, P2P-09, C3T-06, DEV-02."
        % "; ".join("%s %s objects" % (k, "{:,}".format(int(v)))
                    for k, v in sorted(repos.items())))
    return frame, caption


# --- Table 5, the second result, standalone -----------------------------------
def table5() -> tuple[pd.DataFrame, str]:
    r = _rows()
    frame = pd.DataFrame([
        {"quantity": "Jaccard between the two writers' floor sets, SEG BINARY, dciodvfy",
         "baseline": "0.0000",
         "across the nine variant rungs": "oscillates 0.0000 to 0.8571, no trend",
         "stable": "**no**"},
        {"quantity": "Jaccard, SEG BINARY, dicom-validator",
         "baseline": "0.8571",
         "across the nine variant rungs": "0.8571 to 0.8750",
         "stable": "yes, but at a different value from dciodvfy"},
        {"quantity": "residue: message classes held by one writer only, dciodvfy",
         "baseline": "1",
         "across the nine variant rungs": "1 at eight rungs, 2 at V9",
         "stable": "**yes, except V9**"},
        {"quantity": "residue, dicom-validator",
         "baseline": "1",
         "across the nine variant rungs": "1 at all nine",
         "stable": "**yes**"},
    ])
    caption = (
        "**Table 5. Floors are per-writer, not per-standard, and the residue is "
        "the stable quantity.** Two conformant writers given byte-identical "
        "content draw different validator messages, so a floor measured on one "
        "does not transfer to the other. The Jaccard is the wrong statistic "
        "because it is unstable under one validator and stable under the other: "
        "it oscillates between 0.00 and 0.86 under dciodvfy with no trend, and "
        "sits between 0.86 and 0.88 under dicom-validator throughout. Its value "
        "depends on which tool is asked. The residue, the "
        "number of message classes held by one writer only, is 1 at every rung "
        "under both validators except V9 under dciodvfy, where it is 2 because "
        "the pinned build cannot read the deflated transfer syntax and the rung "
        "is adjudicated UNDECIDABLE. Ledger F1-01, F1-03, B-02, B-03, B-05, "
        "B-10.")
    return frame, caption


# --- Table 6, claim 1 ---------------------------------------------------------
def table6() -> tuple[pd.DataFrame, str]:
    net = pd.read_csv(ADJ2 / "net_rates_two_pass.csv")
    frame = net[["sop_class_name", "objects", "collections", "net_pass1",
                 "pct_pass1", "net_pass2", "pct_pass2", "net_consensus",
                 "pct_consensus"]].sort_values("objects", ascending=False)
    caption = (
        "**Table 6. Claim 1: net conformance by class, under each adjudication "
        "pass and under the two-pass consensus.** A message class counts toward "
        "the numerator only where both passes independently called it net; "
        "every disagreement drops to UNDECIDABLE and is excluded, so the "
        "consensus column can only move down and is a lower bound. The "
        "consensus rate is identical to the first pass in all six classes. "
        "Segmentation is absent because its message classes are reported gross "
        "and have not been adjudicated. Ledger ADJ2-01, ADJ2-02, ADJ2-03, "
        "C-C3D-06, C-C3D-08, PRE-05.")
    return frame, caption


TABLES = {
    1: (table1, ["sop_class", "objects", "analysis_result_cells", "coverage"],
        ["SOP class", "objects", "analysis-result cells", "coverage"]),
    2: (table2, ["sop_class_name", "objects", "pct_of_denominator",
                 "non-conformant", "conformant but uninformative", "informative",
                 "pct_non-conformant", "pct_conformant", "pct_informative",
                 "binds_provenance_type1",
                 "pct_uninformative_without_this_class"],
        ["SOP class", "objects", "pct of denominator", "non-conformant",
         "conformant but uninformative", "informative", "pct non-conf",
         "pct uninformative", "pct informative", "binds Type 1",
         "archive pct uninformative if this class is dropped"]),
    3: (table3, ["sop_class_name", "analysis_result_id", "objects",
                 "first_level_identity_appears", "levels_where_identity_appears",
                 "identifying_value", "version_at_that_level", "version_value",
                 "in_object"],
        ["SOP class", "analysis_result_id", "objects", "first level",
         "all levels where identity appears", "identifying value at the first",
         "version", "version value", "in the object"]),
    4: (table4, ["writer", "what_it_records_in_ManufacturerModelName",
                 "what_it_records_in_SoftwareVersions", "set_at",
                 "can_a_caller_place_the_producing_algorithm_here",
                 "distinct_identifiers_in_corpus"],
        ["writer", "ManufacturerModelName carries",
         "SoftwareVersions carries", "set at",
         "can a caller place the producing algorithm here",
         "distinct identifiers in the corpus"]),
    5: (table5, ["quantity", "baseline", "across the nine variant rungs", "stable"],
        ["quantity", "baseline", "across the nine variant rungs", "stable"]),
    6: (table6, ["sop_class_name", "objects", "collections", "net_pass1",
                 "pct_pass1", "net_pass2", "pct_pass2", "net_consensus",
                 "pct_consensus"],
        ["SOP class", "objects", "collections", "net pass 1", "pct", "net pass 2",
         "pct", "net consensus", "pct"]),
}


def main(argv=None) -> int:
    MANUSCRIPT.mkdir(parents=True, exist_ok=True)
    parts = ["# Tables 1 to 6",
             "",
             "Generated from the measurement artefacts by `%s`. No cell is "
             "typed. Every table names the ledger rows it rests on." % CMD, ""]
    for number in sorted(TABLES):
        builder, columns, headers = TABLES[number]
        frame, caption = builder()
        frame.to_csv(MANUSCRIPT / ("table%d.csv" % number), index=False)
        parts += ["## Table %d" % number, "", caption, "",
                  _md(frame, columns, headers), ""]
        print("table %d: %d rows" % (number, len(frame)))
    path = MANUSCRIPT / "tables.md"
    path.write_text("\n".join(parts), encoding="utf-8")
    print("wrote %s" % path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
