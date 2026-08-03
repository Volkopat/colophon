"""Which silent analysis result is the truer exemplar for Figure 3.

Figure 3's left column is an object that names nothing. The one currently drawn
is from `dicom_lidc_idri_nodules`, and every segment in it declares
SegmentAlgorithmType MANUAL. That is legitimate silence: the Type 1C condition on
Segment Algorithm Name (0062,0009) never fires, so nothing was omitted and
nothing was avoided. It is not the case the paper is about.

The case the paper is about is a **non-MANUAL** segment: the condition fires, the
standard compels a name, a name is supplied, and it identifies nothing, while the
Type 3 identification sequence beside it is absent. That object is the 34,234 in
one picture.

This module asks whether such an analysis result exists inside the 21 cells where
producer identity appears at no carrier level, and prints the candidates with the
values that decide it. It re-reads the Phase 3 records and the recoverability
ladder and computes nothing new: no object is fetched, no validator runs, and no
grade is recomputed.

Reproduce with `python -m colophon.silent_column`.
"""
from __future__ import annotations

import collections
import csv
import json
from pathlib import Path

from .paths import RESULTS, REPO

RECORDS = REPO / "_cache" / "phase3" / "records.jsonl"
LADDER = RESULTS / "claim3" / "t33_recoverability_ladder.csv"
OUT_CSV = RESULTS / "figures" / "silent_column_candidates.csv"
OUT_JSON = RESULTS / "figures" / "silent_column_check.json"

SILENT = "identity does not appear"
CARRIERS = ("Manufacturer", "ManufacturerModelName", "SoftwareVersions",
            "ImplementationVersionName", "ContentCreatorName",
            "SeriesDescription")


def silent_cells() -> list[dict]:
    with LADDER.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return [r for r in rows if r["level_name"].startswith(SILENT)]


def _blank() -> dict:
    return {"objects": 0, "segments": 0, "non_manual": 0,
            "algorithm_names": collections.Counter(),
            "identification": collections.Counter(),
            "carriers": {c: collections.Counter() for c in CARRIERS},
            "contributing_equipment": collections.Counter()}


def gather(analysis_results: set[str]) -> dict[str, dict]:
    agg: dict[str, dict] = collections.defaultdict(_blank)
    with RECORDS.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            ar = rec["analysis_result_id"]
            if ar not in analysis_results:
                continue
            a = agg[ar]
            for obj in rec["objects"] or []:
                a["objects"] += 1
                for carrier in CARRIERS:
                    a["carriers"][carrier][obj.get(carrier, "")] += 1
                a["contributing_equipment"][
                    obj.get("ContributingEquipmentSequence_state", "")] += 1
                for seg in obj.get("segments") or []:
                    a["segments"] += 1
                    if not seg.get("non_manual"):
                        continue
                    a["non_manual"] += 1
                    a["algorithm_names"][seg.get("SegmentAlgorithmName", "")] += 1
                    a["identification"][seg.get("identification", "")] += 1
    return agg


def check() -> dict:
    cells = silent_cells()
    seg_cells = {c["analysis_result_id"] for c in cells
                 if c["sop_class_name"] == "Segmentation Storage"}
    agg = gather(seg_cells)

    candidates, all_manual = [], []
    for ar in sorted(seg_cells):
        a = agg.get(ar) or _blank()
        row = {
            "analysis_result_id": ar,
            "objects": a["objects"],
            "segments": a["segments"],
            "segments_non_manual": a["non_manual"],
            "distinct_algorithm_names": len(a["algorithm_names"]),
            "algorithm_names": "; ".join(
                "%s (%d)" % (k or "(empty)", v)
                for k, v in a["algorithm_names"].most_common(4)),
            "identification_states": "; ".join(
                "%s (%d)" % (k, v) for k, v in a["identification"].most_common()),
            "Manufacturer": _top(a["carriers"]["Manufacturer"]),
            "ManufacturerModelName": _top(a["carriers"]["ManufacturerModelName"]),
            "SoftwareVersions": _top(a["carriers"]["SoftwareVersions"]),
            "ContentCreatorName": _top(a["carriers"]["ContentCreatorName"]),
            "ContributingEquipmentSequence": _top(a["contributing_equipment"]),
        }
        (candidates if a["non_manual"] else all_manual).append(row)

    # A candidate whose identification sequence is present everywhere is not a
    # silent object at all, whatever the ladder says about it, and is reported
    # separately rather than offered as an exemplar.
    usable, contradictory = [], []
    for row in candidates:
        if row["identification_states"].startswith("absent"):
            usable.append(row)
        else:
            contradictory.append(row)

    return {
        "silent_cells_total": len(cells),
        "silent_cells_segmentation": len(seg_cells),
        "cells_all_manual": [r["analysis_result_id"] for r in all_manual],
        "cells_with_non_manual_segments": [r["analysis_result_id"]
                                           for r in candidates],
        "usable_exemplars": usable,
        "silent_in_the_ladder_but_carrying_a_complete_macro": contradictory,
        "all_manual_rows": all_manual,
        "currently_drawn": "dicom_lidc_idri_nodules",
        "source": {"records": str(RECORDS), "ladder": str(LADDER)},
    }


def _top(counter: collections.Counter) -> str:
    if not counter:
        return ""
    value, n = counter.most_common(1)[0]
    extra = "" if len(counter) == 1 else " (+%d more)" % (len(counter) - 1)
    return "%s [%d]%s" % (value or "(empty)", n, extra)


FIELDS = ["analysis_result_id", "objects", "segments", "segments_non_manual",
          "distinct_algorithm_names", "algorithm_names",
          "identification_states", "Manufacturer", "ManufacturerModelName",
          "SoftwareVersions", "ContentCreatorName",
          "ContributingEquipmentSequence"]


def main() -> int:
    report = check()
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    rows = (report["usable_exemplars"]
            + report["silent_in_the_ladder_but_carrying_a_complete_macro"]
            + report["all_manual_rows"])
    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for row in rows:
            w.writerow(row)
    OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")

    print("silent cells: %d, of which Segmentation: %d"
          % (report["silent_cells_total"], report["silent_cells_segmentation"]))
    print("all MANUAL, so legitimately silent: %s"
          % ", ".join(report["cells_all_manual"]))
    print()
    print("candidates, non-MANUAL segments and no identification sequence:")
    for row in report["usable_exemplars"]:
        print("  %-42s objects %4d  non-MANUAL %5d  names: %s"
              % (row["analysis_result_id"], row["objects"],
                 row["segments_non_manual"], row["algorithm_names"]))
    if report["silent_in_the_ladder_but_carrying_a_complete_macro"]:
        print()
        print("silent in the ladder but carrying a complete macro, "
              "reported and not resolved:")
        for row in report["silent_in_the_ladder_but_carrying_a_complete_macro"]:
            print("  %-42s %s | %s"
                  % (row["analysis_result_id"], row["identification_states"],
                     row["algorithm_names"]))
    print()
    print("wrote %s and %s" % (OUT_CSV, OUT_JSON))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
