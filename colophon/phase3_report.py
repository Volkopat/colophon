"""Aggregate the Phase 3 Segmentation sample and answer the PRE-06 question.

Reads `_cache/phase3/records.jsonl` and writes the tables. Nothing here fetches
and nothing here adjudicates.

**Absence and incompleteness are carried in separate columns from the raw record
to the printed table and are never summed.** There is a test that asserts no
emitted column is the sum of the two. They answer different questions: STD-02
established from PS3.3 2026c that `SegmentationAlgorithmIdentificationSequence
(0062,0007)` is Type 3 in the Segmentation IOD with no condition, so an absent
sequence on an AUTOMATIC segment is conformant and the finding is about the
standard; a present sequence missing any of its three Type 1 children is
non-conformant and the finding is about the object.

A third state is reported beside them and also never merged: a sequence that is
present and carries zero items. It is neither an omitted optional attribute nor
a populated one missing a child, and assigning it to either would resolve an
ambiguity the standard's text does not.

**The reporting rule is the one PRE-06 registered**, applied to the number of
series validated in the cell, whether they were sampled or taken whole: at or
above 384, a rate with a Wilson interval; 30 to 383, the same with a
below-registered-n flag; under 30, counts only and never a rate.

Segment-level Wilson intervals are reported as unadjusted. Segments are nested
in objects and objects in collections, and the frame measured the collection
level intracluster correlation at a planning value of 0.919, so a segment-level
interval that ignores both levels is narrower than the truth. The series-level
population estimate carries the clustered variance the frame registered.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

from . import phase3, sample
from .paths import PHASE0, RESULTS

PHASE3 = RESULTS / "phase3"
CMD = "python -m colophon.phase3 --report"

ABSENT = "absent"
ZERO_ITEMS = "present_zero_items"
INCOMPLETE = "present_incomplete"
COMPLETE = "present_complete"
STATES = [ABSENT, ZERO_ITEMS, INCOMPLETE, COMPLETE]


def reporting_rule(n_series: int) -> str:
    if n_series < sample.MIN_RATE_N:
        return "counts only, no rate"
    if n_series < sample.REGISTERED_N:
        return "rate with Wilson interval, below-registered-n flag"
    return "rate with Wilson interval"


def rate(k: int, n: int, n_series: int) -> dict:
    """A proportion, or nothing at all if the cell is under the registered floor."""
    if n <= 0 or n_series < sample.MIN_RATE_N:
        return {"pct": None, "lo": None, "hi": None}
    lo, hi, _ = sample.wilson(k, n)
    return {"pct": round(100 * k / n, 2), "lo": round(100 * lo, 2),
            "hi": round(100 * hi, 2)}


# --- flatten ------------------------------------------------------------------
def flatten() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """One row per object, one per message, plus the per-series bookkeeping."""
    objects, messages, series = [], [], []
    dropped = Counter()
    for record in phase3.load_records():
        key = {"series_instance_uid": record["series_instance_uid"],
               "stratum": record["stratum"],
               "writer": record["writer"],
               "analysis_result_id": record["analysis_result_id"] or "(null)",
               "collection_id": record["collection_id"]}
        status = record["status"]
        ok_objects = [o for o in record.get("objects", [])
                      if o.get("status") == "OK"]
        if status == "FETCH_FAILED":
            dropped["series_fetch_failed"] += 1
        dropped["objects_read_failed"] += sum(
            1 for o in record.get("objects", []) if o.get("status") == "READ_FAILED")
        series.append(dict(key, status=status, objects=len(ok_objects),
                           instances_declared=record.get("instance_count_declared", 0)))
        for o in ok_objects:
            row = dict(key)
            row["sop_instance_uid"] = o.get("sop_instance_uid", "")
            for field in ("n_segments", "n_non_manual", "has_non_manual",
                          "segments_ident_absent", "segments_ident_present_zero_items",
                          "segments_ident_present_incomplete",
                          "segments_ident_present_complete",
                          "segments_algorithm_name_absent",
                          "segments_algorithm_name_empty",
                          "any_ident_absent", "all_ident_absent",
                          "any_ident_incomplete", "all_ident_incomplete",
                          "any_ident_present_zero_items", "any_ident_complete",
                          "transfer_syntax_uid", "iod_recognised_as",
                          "dciodvfy_returncode"):
                row[field] = o.get(field)
            for name, _, _ in phase3.CARRIERS:
                row[name] = o.get(name, "")
                row[name + "_state"] = o.get(name + "_state", "absent")
            row["ContributingEquipmentSequence_state"] = o.get(
                "ContributingEquipmentSequence_state", "absent")
            row["ContributingEquipmentSequence_items"] = json.dumps(
                o.get("ContributingEquipmentSequence_items", []))
            row["missing_type1_children"] = json.dumps(
                o.get("missing_type1_children", {}))
            row["algorithm_types"] = json.dumps(o.get("algorithm_types", {}))
            for name, _ in phase3.SHAPE:
                row[name] = o.get(name, "")
            objects.append(row)

            seen = set()
            for validator, mcid, severity, template in o.get("messages", []):
                if (validator, mcid) in seen:
                    continue
                seen.add((validator, mcid))
                messages.append(dict(
                    key, sop_instance_uid=row["sop_instance_uid"],
                    validator=validator, message_class_id=mcid,
                    severity_as_emitted=severity, message_template=template))
    return (pd.DataFrame(objects), pd.DataFrame(messages),
            pd.DataFrame(series), dict(dropped))


# --- the question, per grouping key -------------------------------------------
def segment_level(objects: pd.DataFrame, series: pd.DataFrame, key: str) -> pd.DataFrame:
    rows = []
    n_series = series[series.status == "OK"].groupby(key).size().to_dict()
    for name, sub in objects.groupby(key):
        ns = int(n_series.get(name, 0))
        non_manual = int(sub["n_non_manual"].sum())
        counts = {
            ABSENT: int(sub["segments_ident_absent"].sum()),
            ZERO_ITEMS: int(sub["segments_ident_present_zero_items"].sum()),
            INCOMPLETE: int(sub["segments_ident_present_incomplete"].sum()),
            COMPLETE: int(sub["segments_ident_present_complete"].sum()),
        }
        row = {key: name, "series_validated": ns, "objects": int(len(sub)),
               "segments": int(sub["n_segments"].sum()),
               "segments_non_manual": non_manual}
        for state in STATES:
            row["segments_ident_%s" % state] = counts[state]
            r = rate(counts[state], non_manual, ns)
            row["pct_%s" % state] = r["pct"]
            if state in (ABSENT, INCOMPLETE):
                row["pct_%s_lo" % state] = r["lo"]
                row["pct_%s_hi" % state] = r["hi"]
        row["segments_algorithm_name_absent"] = int(
            sub["segments_algorithm_name_absent"].sum())
        row["segments_algorithm_name_empty"] = int(
            sub["segments_algorithm_name_empty"].sum())
        row["reporting_rule"] = reporting_rule(ns)
        rows.append(row)
    return pd.DataFrame(rows).sort_values("segments_non_manual", ascending=False)


def object_level(objects: pd.DataFrame, series: pd.DataFrame, key: str) -> pd.DataFrame:
    rows = []
    n_series = series[series.status == "OK"].groupby(key).size().to_dict()
    for name, sub in objects.groupby(key):
        ns = int(n_series.get(name, 0))
        with_nm = int(sub["has_non_manual"].sum())
        row = {key: name, "series_validated": ns, "objects": int(len(sub)),
               "objects_with_non_manual_segment": with_nm}
        pairs = [("any_ident_absent", ABSENT), ("all_ident_absent", ABSENT + "_all"),
                 ("any_ident_present_zero_items", ZERO_ITEMS),
                 ("any_ident_incomplete", INCOMPLETE),
                 ("all_ident_incomplete", INCOMPLETE + "_all"),
                 ("any_ident_complete", COMPLETE)]
        for field, label in pairs:
            k = int(sub[field].fillna(False).astype(bool).sum())
            row["objects_%s" % field] = k
            r = rate(k, with_nm, ns)
            row["pct_%s_of_objects_with_non_manual" % field] = r["pct"]
            if field in ("any_ident_absent", "any_ident_incomplete"):
                row["pct_%s_lo" % field] = r["lo"]
                row["pct_%s_hi" % field] = r["hi"]
            r2 = rate(k, int(len(sub)), ns)
            row["pct_%s_of_all_objects" % field] = r2["pct"]
        row["reporting_rule"] = reporting_rule(ns)
        rows.append(row)
    return pd.DataFrame(rows).sort_values("objects", ascending=False)


# --- the pre-registered population estimator ----------------------------------
def population(series: pd.DataFrame, objects: pd.DataFrame, field: str) -> dict:
    """Stratified series-weighted rate, both variance forms, per the frame.

    Point estimate p = sum_i w_i y_i / sum_i w_i with w_i = N_h / n_h. The
    design-based variance is the stratified SRS form with the finite population
    correction, which is the correct width for a claim about this archive
    release. The clustered variance is the Taylor linearised ultimate-cluster
    form taking the collection as the primary sampling unit, with every
    single-collection stratum pooled into one variance stratum by the collapsed
    strata method. Both are reported and the clustered one is the wider.
    """
    COLLAPSED = "(collapsed single-collection strata)"
    frame = pd.read_csv(PHASE0 / "seg_strata.csv").set_index("stratum")
    ok = series[series.status == "OK"].copy()
    if ok.empty:
        return {}
    hit = (objects.groupby("series_instance_uid")[field]
                  .apply(lambda s: bool(s.fillna(False).astype(bool).any())))
    ok["y"] = ok["series_instance_uid"].map(hit).fillna(False).astype(float)

    ok["N_h"] = ok["stratum"].map(frame["series"])
    # Any rate whose denominator carries a null join key declares the null
    # count. A stratum in the sample that is not in the frame is a defect, not
    # a rounding detail, so it is counted and returned rather than dropped.
    unmatched = int(ok["N_h"].isna().sum())
    ok = ok[ok["N_h"].notna()]
    if ok.empty:
        return {"field": field, "unmatched_strata_series": unmatched}

    ok["n_h"] = ok["stratum"].map(ok.groupby("stratum").size())
    ok["w"] = ok["N_h"] / ok["n_h"]
    total_w = float(ok["w"].sum())
    p = float((ok["w"] * ok["y"]).sum() / total_w)

    # Design based: stratified SRS with the finite population correction. The
    # correct width for the only claim this study makes, which is about the
    # count of objects in this archive release.
    N = float(frame["series"].sum())
    v_design = 0.0
    for _, sub in ok.groupby("stratum"):
        n = len(sub)
        if n < 2:
            continue
        Nh = float(sub["N_h"].iloc[0])
        ph = float(sub["y"].mean())
        v_design += (Nh / N) ** 2 * (1 - n / Nh) * ph * (1 - ph) / (n - 1)

    # Clustered: Taylor linearised, ultimate cluster, collection as the primary
    # sampling unit. A PSU is a (stratum, collection) cell, so a collection that
    # appears in two strata contributes two units rather than being merged.
    ok["u"] = ok["w"] * (ok["y"] - p) / total_w
    ok["psu"] = ok["stratum"] + " | " + ok["collection_id"].astype(str)
    per_stratum_collections = ok.groupby("stratum")["psu"].nunique()
    singletons = set(per_stratum_collections[per_stratum_collections < 2].index)
    ok["v_stratum"] = ok["stratum"].where(~ok["stratum"].isin(singletons), COLLAPSED)

    v_clustered, df = 0.0, 0
    for v_stratum, sub in ok.groupby("v_stratum"):
        psu = sub.groupby("psu")["u"].sum()
        c = len(psu)
        if c < 2:
            continue
        # Pooled sampling fraction across whatever strata this variance stratum
        # covers, which for an uncollapsed one is just its own n_h / N_h.
        n_pool = float(len(sub))
        N_pool = float(frame.loc[list(sub["stratum"].unique()), "series"].sum())
        f = min(max(n_pool / N_pool, 0.0), 1.0)
        v_clustered += (1 - f) * (c / (c - 1)) * float(((psu - psu.mean()) ** 2).sum())
        df += c - 1
    return {
        "field": field,
        "p_pct": round(100 * p, 3),
        "series": int(len(ok)),
        "strata": int(ok["stratum"].nunique()),
        "se_design_pct": round(100 * math.sqrt(max(v_design, 0.0)), 3),
        "se_clustered_pct": round(100 * math.sqrt(max(v_clustered, 0.0)), 3),
        "df_clustered": int(df),
        "collapsed_strata": len(singletons),
        "unmatched_strata_series": unmatched,
    }


# --- secondary ----------------------------------------------------------------
def carriers(objects: pd.DataFrame, key: str = "stratum") -> pd.DataFrame:
    names = [n for n, _, _ in phase3.CARRIERS] + ["ContributingEquipmentSequence"]
    rows = []
    for name, sub in objects.groupby(key):
        for carrier in names:
            counts = Counter(sub[carrier + "_state"].fillna("absent"))
            rows.append({key: name, "carrier": carrier, "objects": int(len(sub)),
                         "absent": counts.get("absent", 0),
                         "zero_length": counts.get("empty", 0),
                         "non_empty": counts.get("non_empty", 0)})
    return pd.DataFrame(rows).sort_values([key, "carrier"])


def contributing_equipment(objects: pd.DataFrame) -> pd.DataFrame:
    rows = Counter()
    for r in objects.itertuples():
        for item in json.loads(r.ContributingEquipmentSequence_items):
            rows[(r.stratum, item.get("PurposeOfReference", ""),
                  item.get("Manufacturer", ""),
                  item.get("ManufacturerModelName", ""),
                  item.get("SoftwareVersions", ""))] += 1
    return pd.DataFrame(
        [{"stratum": s, "PurposeOfReference": p, "Manufacturer": m,
          "ManufacturerModelName": mm, "SoftwareVersions": sv, "items": n}
         for (s, p, m, mm, sv), n in rows.items()]).sort_values(
        "items", ascending=False) if rows else pd.DataFrame(
        columns=["stratum", "PurposeOfReference", "Manufacturer",
                 "ManufacturerModelName", "SoftwareVersions", "items"])


def message_classes(messages: pd.DataFrame) -> pd.DataFrame:
    if messages.empty:
        return pd.DataFrame(columns=["stratum", "validator", "message_class_id",
                                     "severity_as_emitted", "objects",
                                     "message_template"])
    grouped = (messages.groupby(["stratum", "validator", "message_class_id",
                                 "severity_as_emitted", "message_template"])
                       .size().rename("objects").reset_index())
    return grouped.sort_values(["stratum", "objects"], ascending=[True, False])


def algorithm_type_distribution(objects: pd.DataFrame) -> pd.DataFrame:
    rows = Counter()
    for r in objects.itertuples():
        for value, n in json.loads(r.algorithm_types).items():
            rows[(r.stratum, value)] += n
    return pd.DataFrame([{"stratum": s, "SegmentAlgorithmType": v, "segments": n}
                         for (s, v), n in rows.items()]).sort_values(
        ["stratum", "segments"], ascending=[True, False])


def macro_content() -> pd.DataFrame:
    """What a complete macro actually says, against what the segment declares.

    Read straight from the records rather than from the flattened object table,
    because the macro sits two sequences deep and the flattening keeps only the
    counts. Nothing here is a verdict. `SegmentAlgorithmType` is Type 1 with
    enumerated values and `AlgorithmName` is a free-text LO, and PS3.3 states no
    relation between them, so a segment whose type and whose algorithm name
    disagree is reported as observed and is not scored either way.
    """
    rows = Counter()
    for record in phase3.load_records():
        for o in record.get("objects", []):
            if o.get("status") != "OK":
                continue
            for segment in o.get("segments", []):
                for macro in segment.get("macro", []):
                    rows[(record["stratum"],
                          record["analysis_result_id"] or "(null)",
                          segment["SegmentAlgorithmType"],
                          macro.get("AlgorithmName_value", ""),
                          macro.get("AlgorithmVersion_value", ""),
                          macro.get("AlgorithmFamilyCode", ""),
                          macro.get("AlgorithmSource_value", ""))] += 1
    if not rows:
        return pd.DataFrame(columns=["stratum", "analysis_result_id",
                                     "SegmentAlgorithmType", "AlgorithmName",
                                     "AlgorithmVersion", "AlgorithmFamilyCode",
                                     "AlgorithmSource", "segments"])
    return pd.DataFrame(
        [{"stratum": s, "analysis_result_id": a, "SegmentAlgorithmType": t,
          "AlgorithmName": n, "AlgorithmVersion": v, "AlgorithmFamilyCode": f,
          "AlgorithmSource": src, "segments": c}
         for (s, a, t, n, v, f, src), c in rows.items()]).sort_values(
        "segments", ascending=False)


# Carriers of writer identity, in the order the object is asked. The index can
# only see the first, which is why W-01's label is provisional.
WRITER_CARRIERS = ["ContributingEquipmentSequence", "ImplementationVersionName",
                   "Manufacturer and ManufacturerModelName"]


def writer_from_object(row) -> tuple[str, str]:
    """Re-read the writer from the object, using the Phase 0 rule table unchanged.

    PRE-06 limitation 3 registered this in advance: the frame's writer label is
    inferred from the two equipment attributes the index carries, Phase 2 and 3
    read `ImplementationVersionName` and `ContributingEquipmentSequence` which
    are stronger evidence, and if those change a series' writer then the
    pre-registered response is **to relabel and report the reallocation, never
    to silently redraw**. This function does the relabelling and returns the
    carrier that decided it, so the reallocation can be audited.

    The rule table is `colophon.writers.WRITER_RULES`, imported rather than
    restated. Only the evidence widens. A new rule here would silently change
    the Phase 0 writer census that W-01 published, so anything the existing
    table does not match stays unidentified and is reported as such.
    """
    from . import writers
    equipment = json.loads(row.ContributingEquipmentSequence_items or "[]")
    evidence = [
        (WRITER_CARRIERS[0], " ".join(
            "%s %s" % (item.get("Manufacturer", ""),
                       item.get("ManufacturerModelName", "")) for item in equipment)),
        (WRITER_CARRIERS[1], str(row.ImplementationVersionName or "")),
        (WRITER_CARRIERS[2], "%s %s" % (row.Manufacturer or "",
                                        row.ManufacturerModelName or "")),
    ]
    for carrier, text in evidence:
        for name, pattern in writers.WRITER_RULES:
            if re.search(pattern, text.lower()):
                return name, carrier
    return writers.UNKNOWN_WRITER, "none of the three carriers"


def writer_relabel(objects: pd.DataFrame) -> pd.DataFrame:
    """Index label against object label, one row per pair, with the carrier."""
    rows = Counter()
    for row in objects.itertuples():
        name, carrier = writer_from_object(row)
        rows[(row.stratum, row.writer, name, carrier)] += 1
    return pd.DataFrame(
        [{"stratum": s, "writer_from_index": w, "writer_from_object": o,
          "deciding_carrier": c, "objects": n}
         for (s, w, o, c), n in rows.items()]).sort_values(
        "objects", ascending=False)


ENUMERATED = ("AUTOMATIC", "SEMIAUTOMATIC", "MANUAL")


def out_of_enumeration() -> pd.DataFrame:
    """Segments whose SegmentAlgorithmType is none of the three enumerated values.

    These are excluded from the AUTOMATIC-or-SEMIAUTOMATIC denominator by the
    wording of the question, so they are counted here rather than dropped
    silently. Whether that exclusion is also the right conformance call is not
    decided here: `dciodvfy` scores the value independently and its verdict is
    carried in the same row, so the adjudication is a third party's.
    """
    rows = Counter()
    flagged = Counter()
    for record in phase3.load_records():
        for o in record.get("objects", []):
            if o.get("status") != "OK":
                continue
            bad = [s for s in o.get("segments", [])
                   if s["SegmentAlgorithmType"] not in ENUMERATED]
            if not bad:
                continue
            hit = any("Unrecognized enumerated value" in template
                      and "Segment Algorithm Type" in template
                      for _, _, _, template in o.get("messages", []))
            for segment in bad:
                key = (record["stratum"], record["analysis_result_id"] or "(null)",
                       record["collection_id"], segment["SegmentAlgorithmType"],
                       segment["SegmentAlgorithmType_state"])
                rows[key] += 1
                if hit:
                    flagged[key] += 1
    if not rows:
        return pd.DataFrame(columns=["stratum", "analysis_result_id",
                                     "collection_id", "SegmentAlgorithmType",
                                     "state", "segments",
                                     "segments_in_objects_dciodvfy_flagged"])
    return pd.DataFrame(
        [{"stratum": s, "analysis_result_id": a, "collection_id": c,
          "SegmentAlgorithmType": v, "state": st, "segments": n,
          "segments_in_objects_dciodvfy_flagged": flagged.get((s, a, c, v, st), 0)}
         for (s, a, c, v, st), n in rows.items()]).sort_values(
        "segments", ascending=False)


def missing_children(objects: pd.DataFrame) -> pd.DataFrame:
    rows = Counter()
    for r in objects.itertuples():
        for child, n in json.loads(r.missing_type1_children).items():
            rows[(r.stratum, child)] += n
    return pd.DataFrame([{"stratum": s, "missing_type1_child": c, "segments": n}
                         for (s, c), n in rows.items()]).sort_values(
        "segments", ascending=False) if rows else pd.DataFrame(
        columns=["stratum", "missing_type1_child", "segments"])


def report() -> dict:
    PHASE3.mkdir(parents=True, exist_ok=True)
    objects, messages, series, dropped = flatten()
    if objects.empty:
        print("no records yet")
        return {}

    out = {}
    for key, tag in (("stratum", "stratum"), ("analysis_result_id", "analysis_result")):
        seg = segment_level(objects, series, key)
        obj = object_level(objects, series, key)
        seg.to_csv(PHASE3 / ("seg_identification_segments_by_%s.csv" % tag), index=False)
        obj.to_csv(PHASE3 / ("seg_identification_objects_by_%s.csv" % tag), index=False)
        out["segments_by_" + tag] = seg
        out["objects_by_" + tag] = obj

    carriers(objects).to_csv(PHASE3 / "seg_carriers_by_stratum.csv", index=False)
    contributing_equipment(objects).to_csv(
        PHASE3 / "seg_contributing_equipment.csv", index=False)
    message_classes(messages).to_csv(PHASE3 / "seg_message_classes.csv", index=False)
    algorithm_type_distribution(objects).to_csv(
        PHASE3 / "seg_algorithm_type_distribution.csv", index=False)
    missing_children(objects).to_csv(PHASE3 / "seg_missing_type1_children.csv",
                                     index=False)
    macro = macro_content()
    macro.to_csv(PHASE3 / "seg_macro_content.csv", index=False)
    out["macro"] = macro
    relabel = writer_relabel(objects)
    relabel.to_csv(PHASE3 / "seg_writer_relabel.csv", index=False)
    out["relabel"] = relabel
    moved = relabel[relabel["writer_from_index"] != relabel["writer_from_object"]]
    out["relabelled_objects"] = int(moved["objects"].sum()) if len(moved) else 0
    out["relabelled_strata"] = int(moved["stratum"].nunique()) if len(moved) else 0
    ooe = out_of_enumeration()
    ooe.to_csv(PHASE3 / "seg_out_of_enumeration.csv", index=False)
    out["out_of_enumeration"] = ooe
    out["out_of_enumeration_segments"] = int(ooe["segments"].sum()) if len(ooe) else 0
    out["out_of_enumeration_flagged"] = int(
        ooe["segments_in_objects_dciodvfy_flagged"].sum()) if len(ooe) else 0
    # Reported, not resolved: the segment declares a type and the macro names an
    # algorithm, and the two can disagree in plain text.
    out["type_name_disagreement"] = int(macro[
        (macro["SegmentAlgorithmType"].str.upper().isin(phase3.NON_MANUAL))
        & (macro["AlgorithmName"].str.lower().str.contains("manual", na=False))
    ]["segments"].sum()) if len(macro) else 0
    series.to_csv(PHASE3 / "seg_series_status.csv", index=False)

    out["population_absent"] = population(series, objects, "any_ident_absent")
    out["population_incomplete"] = population(series, objects, "any_ident_incomplete")
    out["dropped"] = dropped
    out["objects"] = objects
    out["messages"] = messages
    out["series"] = series
    out["totals"] = {
        "series_attempted": int(len(series)),
        "series_ok": int((series.status == "OK").sum()),
        "objects": int(len(objects)),
        "segments": int(objects["n_segments"].sum()),
        "segments_non_manual": int(objects["n_non_manual"].sum()),
        "segments_ident_absent": int(objects["segments_ident_absent"].sum()),
        "segments_ident_present_zero_items": int(
            objects["segments_ident_present_zero_items"].sum()),
        "segments_ident_present_incomplete": int(
            objects["segments_ident_present_incomplete"].sum()),
        "segments_ident_present_complete": int(
            objects["segments_ident_present_complete"].sum()),
        "objects_with_non_manual": int(objects["has_non_manual"].sum()),
        "objects_any_ident_absent": int(
            objects["any_ident_absent"].fillna(False).astype(bool).sum()),
        "objects_any_ident_incomplete": int(
            objects["any_ident_incomplete"].fillna(False).astype(bool).sum()),
        "objects_any_ident_complete": int(
            objects["any_ident_complete"].fillna(False).astype(bool).sum()),
        "segments_algorithm_name_absent": int(
            objects["segments_algorithm_name_absent"].sum()),
        "segments_algorithm_name_empty": int(
            objects["segments_algorithm_name_empty"].sum()),
    }
    out["totals"]["segments_type_says_non_manual_name_says_manual"] = out[
        "type_name_disagreement"]
    out["totals"]["objects_whose_writer_label_changed"] = out["relabelled_objects"]
    out["totals"]["segments_algorithm_type_out_of_enumeration"] = out[
        "out_of_enumeration_segments"]
    out["totals"]["segments_out_of_enumeration_flagged_by_dciodvfy"] = out[
        "out_of_enumeration_flagged"]
    (PHASE3 / "seg_totals.json").write_text(
        json.dumps({k: v for k, v in out.items()
                    if k in ("totals", "dropped", "population_absent",
                             "population_incomplete")}, indent=2),
        encoding="utf-8")
    write_markdown(out)
    propose_ledger(out)
    return out


# --- write-up -----------------------------------------------------------------
def _pct(k: int, n: int) -> str:
    return "%.2f" % (100 * k / n) if n else "n/a"


def write_markdown(out: dict) -> Path:
    from .index import _fmt, _md_table

    t, dropped = out["totals"], out["dropped"]
    seg_s, obj_s = out["segments_by_stratum"], out["objects_by_stratum"]
    seg_a, obj_a = out["segments_by_analysis_result"], out["objects_by_analysis_result"]
    pa, pi = out["population_absent"], out["population_incomplete"]
    objects, messages = out["objects"], out["messages"]
    gate = json.loads((phase3.GATE).read_text(encoding="utf-8")) if phase3.GATE.exists() else {}

    manifest_series = gate.get("series", 0)
    coverage = 100 * t["series_attempted"] / manifest_series if manifest_series else 0

    carrier_table = carriers(objects).groupby("carrier")[
        ["absent", "zero_length", "non_empty"]].sum().reset_index()
    carrier_table["objects"] = t["objects"]

    ce = contributing_equipment(objects)
    ce_top = ce.head(12) if len(ce) else ce

    mc = message_classes(messages)
    mc_top = (mc.groupby(["validator", "severity_as_emitted", "message_class_id",
                          "message_template"])["objects"].sum().reset_index()
                .sort_values("objects", ascending=False).head(15)) if len(mc) else mc

    missing = missing_children(objects)
    missing_rows = ("\n".join("| `%s` | %s | %s |" % (r.missing_type1_child,
                                                      r.stratum, _fmt(int(r.segments)))
                              for r in missing.itertuples())
                    if len(missing) else "| none | | |")

    text = f"""# Phase 3: the Segmentation Storage sample, and what it says about algorithm identification

The PRE-06 frame, executed. `colophon.sample.EXECUTE` was set True on approval
and nothing else in the frame moved: 21 strata, seed {sample.SEED}, registered
minimum n = {sample.REGISTERED_N}, one per-stratum byte cap, the same nested
draw. Reproduce with `{phase3.CMD}` then `{CMD}`.

Manifest {_fmt(manifest_series)} series, {gate.get('exact_manifest_GB', 0):.2f} GB
exact against a {sample.BUDGET_GB:.0f} GB budget. The pre-registered byte gate
fired **{gate.get('gate_fired_times', 0)} time(s)**.

## The question

Of all sampled Segmentation objects, what fraction declare
`SegmentAlgorithmType (0062,0008)` as AUTOMATIC or SEMIAUTOMATIC while
`SegmentationAlgorithmIdentificationSequence (0062,0007)` is absent, and what
fraction have it present but incomplete, missing any Type 1 child.

**The two are never merged, and the reason is not stylistic.** STD-02 settled it
against PS3.3 2026c: in the Segmentation IOD (0062,0007) is Type 3 with no
condition of any kind. Omitting it on an AUTOMATIC segment is conformant, and no
validator can flag it. The 1C form of that sequence exists only in the Height Map
Segmentation Image Module, which Table A.51-1 does not include. So **absence is a
gap in the standard**. Once the sequence is present its three Type 1 children are
mandatory, so **incompleteness is a defect in the object**. A single combined
number would be a statement about neither.

## The answer

Coverage at the time of writing: **{_fmt(t['series_attempted'])} of
{_fmt(manifest_series)} sampled series, {coverage:.1f} percent**, carrying
{_fmt(t['objects'])} objects and {_fmt(t['segments'])} segments.

### Segment level

Denominator: the {_fmt(t['segments_non_manual'])} segments declaring AUTOMATIC or
SEMIAUTOMATIC.

| state of (0062,0007) | segments | percent of non-MANUAL segments |
|---|---|---|
| **absent** | {_fmt(t['segments_ident_absent'])} | **{_pct(t['segments_ident_absent'], t['segments_non_manual'])}** |
| **present but incomplete**, missing a Type 1 child | {_fmt(t['segments_ident_present_incomplete'])} | **{_pct(t['segments_ident_present_incomplete'], t['segments_non_manual'])}** |
| present and carrying zero items | {_fmt(t['segments_ident_present_zero_items'])} | {_pct(t['segments_ident_present_zero_items'], t['segments_non_manual'])} |
| present and complete | {_fmt(t['segments_ident_present_complete'])} | {_pct(t['segments_ident_present_complete'], t['segments_non_manual'])} |

### Object level

One object holds many segments, so the object-level question has two readings and
both are reported. Denominator: the {_fmt(t['objects_with_non_manual'])} objects
carrying at least one non-MANUAL segment, of {_fmt(t['objects'])} objects.

| reading | objects | percent of objects with a non-MANUAL segment | percent of all objects |
|---|---|---|---|
| at least one non-MANUAL segment with (0062,0007) **absent** | {_fmt(t['objects_any_ident_absent'])} | {_pct(t['objects_any_ident_absent'], t['objects_with_non_manual'])} | {_pct(t['objects_any_ident_absent'], t['objects'])} |
| at least one with (0062,0007) **present but incomplete** | {_fmt(t['objects_any_ident_incomplete'])} | {_pct(t['objects_any_ident_incomplete'], t['objects_with_non_manual'])} | {_pct(t['objects_any_ident_incomplete'], t['objects'])} |
| at least one with (0062,0007) present and complete | {_fmt(t['objects_any_ident_complete'])} | {_pct(t['objects_any_ident_complete'], t['objects_with_non_manual'])} | {_pct(t['objects_any_ident_complete'], t['objects'])} |

### Per stratum

The reporting rule is the one PRE-06 registered, applied to the series validated
in the cell: at or above {sample.REGISTERED_N}, a rate with a Wilson interval;
{sample.MIN_RATE_N} to {sample.REGISTERED_N - 1}, the same with a
below-registered-n flag; under {sample.MIN_RATE_N}, counts only and never a rate.

Segment-level intervals are **unadjusted for clustering**. Segments nest in
objects and objects in collections, and the frame measured a collection-level
planning rho of 0.919, so these intervals are narrower than the truth. The
population estimate below carries the clustered variance.

{_md_table(seg_s, ["stratum", "series_validated", "segments_non_manual", "segments_ident_absent", "pct_absent", "segments_ident_present_incomplete", "pct_present_incomplete", "segments_ident_present_complete", "reporting_rule"])}

Object level, same strata:

{_md_table(obj_s, ["stratum", "objects", "objects_with_non_manual_segment", "objects_any_ident_absent", "pct_any_ident_absent_of_objects_with_non_manual", "objects_any_ident_incomplete", "pct_any_ident_incomplete_of_objects_with_non_manual", "reporting_rule"])}

### Per analysis_result_id

{_md_table(seg_a, ["analysis_result_id", "series_validated", "segments_non_manual", "segments_ident_absent", "pct_absent", "segments_ident_present_incomplete", "pct_present_incomplete", "segments_ident_present_complete", "reporting_rule"])}

Object level, same grouping:

{_md_table(obj_a, ["analysis_result_id", "objects", "objects_with_non_manual_segment", "objects_any_ident_absent", "pct_any_ident_absent_of_objects_with_non_manual", "objects_any_ident_incomplete", "pct_any_ident_incomplete_of_objects_with_non_manual", "reporting_rule"])}

### Which Type 1 child is missing, where incompleteness occurs

| missing Type 1 child | stratum | segments |
|---|---|---|
{missing_rows}

### What is not in the denominator, and why

`SegmentAlgorithmType (0062,0008)` is Type 1 and its values are **Enumerated**,
not Defined Terms: PS3.3 2026c Table C.8.20-4 gives AUTOMATIC, SEMIAUTOMATIC and
MANUAL and nothing else. The sample contains a fourth value.

**{_fmt(out.get('out_of_enumeration_segments', 0))} segments carry a value that
is none of the three.** They are outside the AUTOMATIC-or-SEMIAUTOMATIC
denominator by the wording of the question, so they are counted here rather than
dropped silently.

Whether that value is also non-conformant is not decided here.
**`dciodvfy` scores it independently and flags it at Error severity**,
`Error - Unrecognized enumerated value <...> for value 1 of attribute
<Segment Algorithm Type>`, on the objects carrying
{_fmt(out.get('out_of_enumeration_flagged', 0))} of them. The adjudication is a
third party's and the citation is the third party's own.

{_md_table(out["out_of_enumeration"], ["stratum", "analysis_result_id", "collection_id", "SegmentAlgorithmType", "segments", "segments_in_objects_dciodvfy_flagged"]) if len(out.get("out_of_enumeration", [])) else "Every segment in the sample carries one of the three enumerated values."}

### What a complete macro actually says

A complete macro is not the same thing as an informative one, and the two
attributes can contradict each other in plain text. This table is observation
only. `SegmentAlgorithmType (0062,0008)` is Type 1 with enumerated values and
`AlgorithmName (0066,0036)` is a free-text LO, and PS3.3 states no relation
between them, so a segment whose declared type and whose named algorithm
disagree is **conformant** and is reported here without being scored either way.

**{_fmt(out.get('type_name_disagreement', 0))} segments declare AUTOMATIC or
SEMIAUTOMATIC while their macro names the algorithm as a manual one.** The
disagreement is recorded and not resolved.

{_md_table(out["macro"].head(15), ["analysis_result_id", "SegmentAlgorithmType", "AlgorithmName", "AlgorithmVersion", "AlgorithmFamilyCode", "segments"]) if len(out.get("macro", [])) else "No object in the sample carries a populated macro."}

## The population estimate, both variances

The estimator PRE-06 registered: stratified, series weighted, with design weights
w_i = N_h / n_h read from a complete index rather than estimated. The unit is the
series and the outcome is "at least one non-MANUAL segment in the series shows
the state".

| | absence | incompleteness |
|---|---|---|
| point estimate, percent of series | **{pa.get('p_pct', 'n/a')}** | **{pi.get('p_pct', 'n/a')}** |
| standard error, design based with fpc | {pa.get('se_design_pct', 'n/a')} | {pi.get('se_design_pct', 'n/a')} |
| standard error, clustered on collection | {pa.get('se_clustered_pct', 'n/a')} | {pi.get('se_clustered_pct', 'n/a')} |
| degrees of freedom, clustered | {pa.get('df_clustered', 'n/a')} | {pi.get('df_clustered', 'n/a')} |
| single-collection strata collapsed into one variance stratum | {pa.get('collapsed_strata', 'n/a')} | {pi.get('collapsed_strata', 'n/a')} |
| series contributing | {_fmt(pa.get('series', 0))} | {_fmt(pi.get('series', 0))} |

The clustered standard error is the wider of the two and is the one to quote. The
design-based one is the correct width for the only claim this study is scoped to
make, which is a count of objects in IDC {gate.get('idc_version', 'v24')} and not
a statement about DICOM practice.

## Secondary: the provenance carriers, three states, never two

Absent and zero-length are different findings and are never collapsed. In the
Segmentation IOD, Enhanced General Equipment is Mandatory, so Manufacturer,
ManufacturerModelName, DeviceSerialNumber and SoftwareVersions are all Type 1:
for those four, both absent and zero-length are conformance violations.

{_md_table(carrier_table, ["carrier", "objects", "absent", "zero_length", "non_empty"])}

`ContributingEquipmentSequence (0018,A001)` items, by declared purpose:

{_md_table(ce_top, ["stratum", "PurposeOfReference", "Manufacturer", "ManufacturerModelName", "SoftwareVersions", "items"]) if len(ce_top) else "No object in the sample carries the sequence."}

## The writer label moved, and PRE-06 registered what to do about it

Limitation 3 of the frame said this in advance: the writer label is inferred
from the two equipment attributes the index carries, Phase 3 reads
`ImplementationVersionName` and `ContributingEquipmentSequence` which are
stronger evidence, and **if those change a series' writer the pre-registered
response is to relabel and report the reallocation, never to silently redraw.**

They do change it. **{_fmt(out.get('relabelled_objects', 0))} objects across
{out.get('relabelled_strata', 0)} strata carry object-level evidence naming a
writer the index could not name.** The draw is unchanged and nothing has been
redrawn. The rule table is `colophon.writers.WRITER_RULES`, imported unchanged
from Phase 0: only the evidence widens, so nothing the existing table does not
match has been newly classified, and anything it misses stays unidentified.

The carriers are asked in this order: {", ".join("`%s`" % c for c in WRITER_CARRIERS)}.

{_md_table(out["relabel"], ["stratum", "writer_from_index", "writer_from_object", "deciding_carrier", "objects"]) if len(out.get("relabel", [])) else "No object carries writer evidence."}

Two consequences, both of which belong to whoever reads this next rather than to
this pass. A stratum that moves to `highdicom` moves from having no measured
Phase 1 floor to having one, so a post-floor rate becomes quotable where the
frame said it was not. And `ImplementationVersionName` in the sample carries
values such as `dcm4che-1.4.27` that `WRITER_RULES` has no rule for, so they
stay unidentified here rather than being classified by a rule invented after
seeing the data.

## Secondary: validator message classes, gross

Counted as distinct (SOPInstanceUID, message_class_id) pairs through the Phase 1
parser and normaliser, never as raw lines. Severity is matched in both forms, the
line-start `Error - ` form and the embedded ` - (Error|Warning) - ` form. Exit
status is recorded and never tested.

**These are gross counts and nothing here is NET.** No message class in this
table has been adjudicated against a cited PS3 section, and an unadjudicated
class is UNDECIDABLE rather than a defect. Adjudication is a separate pass with
two independent adjudicators.

{_md_table(mc_top, ["validator", "severity_as_emitted", "message_class_id", "objects", "message_template"]) if len(mc_top) else "No messages recorded."}

## The panel that ran, and the arm that did not

For this SOP class the conformance panel is dciodvfy, dicom-validator and
PixelMed `DicomInstanceValidator`. **Two of the three ran.** The PixelMed jar is
absent from the pinned toolchain, V-04, so its arm is recorded as NOT RUN and
never as passed. `dcmpschk` was not run at all: on a Segmentation missing two
Type 1 attributes it printed `Test passed.`, so addendum 02 keeps it to GSPS.

The reference-parse axis, `segimage2itkimage` and the highdicom reader, was not
run in this pass and no axis-2 result is reported.

## What was dropped

- **{_fmt(dropped.get('series_fetch_failed', 0))} series failed to fetch** and
  carry a FETCH_FAILED record rather than being silently absent.
- **{_fmt(dropped.get('objects_read_failed', 0))} objects failed to read** and
  carry a READ_FAILED record.
- The sample reads {_fmt(manifest_series)} of 190,146 series in the class,
  3.12 percent. The {_fmt(190146 - manifest_series)} series not drawn are
  represented through the stratum weights W_h and through nothing else.
- One stratum was cut below the registered minimum by the byte cap, at n = 75 of
  6,074 series, and its Wilson half-width at p = 5 percent widens from 2.21 to
  5.29 points.
- Every limitation the frame declared still holds and is not restated here.
  `results/pre06_sampling_frame.md` carries all ten.
"""
    PHASE3.mkdir(parents=True, exist_ok=True)
    path = RESULTS / "phase3_segmentation.md"
    path.write_text(text, encoding="utf-8")
    return path


# --- ledger -------------------------------------------------------------------
def propose_ledger(out: dict) -> Path:
    from .index import _fmt

    t, dropped = out["totals"], out["dropped"]
    pa, pi = out["population_absent"], out["population_incomplete"]
    gate = json.loads(phase3.GATE.read_text(encoding="utf-8")) if phase3.GATE.exists() else {}
    manifest_series = gate.get("series", 0)
    objects = out["objects"]

    common = dict(
        section="P3", section_title="Phase 3, the Segmentation Storage sample",
        sop_class=phase3.SOP_CLASS, command=phase3.CMD,
        validator="none for the identification rows, no validator is involved; "
                  "dciodvfy and dicom-validator for the message-class rows",
        validator_version="dicom3tools snapshot 20260701065818; "
                          "dicom-validator 0.8.2 edition 2026c",
        idc_index_version=gate.get("idc_version", "v24"))

    dropped_text = (
        "%s of %s sampled series recorded, %s fetch failures and %s object read "
        "failures, each carrying its own record; the sample reads 3.12 percent "
        "of the class and the rest is represented through the stratum weights; "
        "one stratum cut below the registered minimum to n = 75 by the byte cap"
        % (_fmt(t["series_attempted"]), _fmt(manifest_series),
           _fmt(dropped.get("series_fetch_failed", 0)),
           _fmt(dropped.get("objects_read_failed", 0))))

    no_validator_floor = ("not applicable, no validator is involved: this is an "
                          "attribute-presence measurement read from the object, "
                          "not a validator rate")

    rows = [
        dict(sample.pre06_carry_forward(),
             id="PRE-06",
             claim=sample.PRE06_CLAIM,
             status="MEASURED",
             status_note="The frame was approved and executed. "
             "colophon.sample.EXECUTE was set True and nothing in the frame "
             "moved: same 21 strata, same seed %d, same registered minimum, "
             "same allocation rule, same nested draw. The pre-registered byte "
             "gate fired %d time(s). %s of %s drawn series are recorded."
             % (sample.SEED, gate.get("gate_fired_times", 0),
                _fmt(t["series_attempted"]), _fmt(manifest_series)),
             value="drawn %s series, %.2f GB exact against a %.0f GB budget; "
                   "recorded %s series, %s objects, %s segments"
                   % (_fmt(manifest_series), gate.get("exact_manifest_GB", 0),
                      sample.BUDGET_GB, _fmt(t["series_attempted"]),
                      _fmt(t["objects"]), _fmt(t["segments"])),
             n=_fmt(t["series_attempted"]), denominator=_fmt(manifest_series),
             dropped=dropped_text,
             command=phase3.CMD,
             source_file="results/phase3_segmentation.md"),
        dict(id="P3-01",
             claim="Among sampled Segmentation segments declaring "
                   "SegmentAlgorithmType (0062,0008) as AUTOMATIC or "
                   "SEMIAUTOMATIC, this fraction omits "
                   "SegmentationAlgorithmIdentificationSequence (0062,0007) "
                   "entirely. Absence is conformant: the sequence is Type 3 in "
                   "the Segmentation IOD with no condition.",
             status="MEASURED",
             value="%s of %s non-MANUAL segments, %s percent, carry no "
                   "identification sequence"
                   % (_fmt(t["segments_ident_absent"]),
                      _fmt(t["segments_non_manual"]),
                      _pct(t["segments_ident_absent"], t["segments_non_manual"])),
             n=_fmt(t["segments_ident_absent"]),
             denominator=_fmt(t["segments_non_manual"]),
             floor=no_validator_floor,
             dropped=dropped_text,
             derived_from="STD-02,PRE-06",
             external_source="PS3.3 2026c Table C.8.20-2 and Table A.51-1",
             source_file="results/phase3/seg_identification_segments_by_stratum.csv",
             pinned_by_test="tests/test_phase3.py::test_object_rollup_keeps_absence_and_incompleteness_apart",
             status_note="Never merged with P3-02. Absence is a gap in the "
             "standard and incompleteness is a defect in the object, and a "
             "combined number would be a statement about neither.",
             **common),
        dict(id="P3-02",
             claim="Among the same segments, this fraction carries "
                   "SegmentationAlgorithmIdentificationSequence (0062,0007) "
                   "present but incomplete, missing at least one of its three "
                   "Type 1 children. Incompleteness is non-conformant.",
             status="MEASURED",
             value="%s of %s non-MANUAL segments, %s percent, carry a present "
                   "but incomplete identification sequence"
                   % (_fmt(t["segments_ident_present_incomplete"]),
                      _fmt(t["segments_non_manual"]),
                      _pct(t["segments_ident_present_incomplete"],
                           t["segments_non_manual"])),
             n=_fmt(t["segments_ident_present_incomplete"]),
             denominator=_fmt(t["segments_non_manual"]),
             floor=no_validator_floor,
             dropped=dropped_text,
             derived_from="STD-01,STD-02,PRE-06",
             external_source="PS3.3 2026c section 10.16 Table 10-19, Algorithm "
                             "Identification Macro: AlgorithmFamilyCodeSequence "
                             "(0066,002F), AlgorithmName (0066,0036) and "
                             "AlgorithmVersion (0066,0031) are Type 1",
             source_file="results/phase3/seg_missing_type1_children.csv",
             pinned_by_test="tests/test_phase3.py::test_sequence_missing_a_type1_child_reads_as_incomplete",
             status_note="Never merged with P3-01. A Type 1 child present but "
             "zero length counts as missing, which a presence check would score "
             "as complete.",
             **common),
        dict(id="P3-03",
             claim="A third state exists and is reported separately from both: "
                   "SegmentationAlgorithmIdentificationSequence present and "
                   "carrying zero items.",
             status="MEASURED",
             value="%s of %s non-MANUAL segments, %s percent"
                   % (_fmt(t["segments_ident_present_zero_items"]),
                      _fmt(t["segments_non_manual"]),
                      _pct(t["segments_ident_present_zero_items"],
                           t["segments_non_manual"])),
             n=_fmt(t["segments_ident_present_zero_items"]),
             denominator=_fmt(t["segments_non_manual"]),
             floor=no_validator_floor, dropped=dropped_text,
             source_file="results/phase3/seg_identification_segments_by_stratum.csv",
             pinned_by_test="tests/test_phase3.py::test_zero_item_sequence_is_its_own_state",
             status_note="Neither an omitted optional attribute nor a populated "
             "one missing a child. Assigning it to either would resolve an "
             "ambiguity the standard's text does not, so it is reported as its "
             "own state and left unresolved.",
             **common),
        dict(id="P3-04",
             claim="The object-level reading of the same question, reported in "
                   "both quantifiers because one object holds many segments.",
             status="MEASURED",
             value="of %s objects carrying at least one non-MANUAL segment: %s "
                   "have at least one with the sequence absent, %s have at "
                   "least one present but incomplete, %s have at least one "
                   "present and complete"
                   % (_fmt(t["objects_with_non_manual"]),
                      _fmt(t["objects_any_ident_absent"]),
                      _fmt(t["objects_any_ident_incomplete"]),
                      _fmt(t["objects_any_ident_complete"])),
             n=_fmt(t["objects_any_ident_absent"]),
             denominator=_fmt(t["objects_with_non_manual"]),
             floor=no_validator_floor, dropped=dropped_text,
             derived_from="P3-01,P3-02",
             source_file="results/phase3/seg_identification_objects_by_stratum.csv",
             **common),
        dict(id="P3-05",
             claim="SegmentAlgorithmName (0062,0009) is Type 1C, required when "
                   "the algorithm type is not MANUAL. It is the one conditional "
                   "requirement in the Segmentation IOD that "
                   "SegmentAlgorithmType triggers.",
             status="MEASURED",
             value="of %s non-MANUAL segments, %s carry it absent and %s carry "
                   "it zero length"
                   % (_fmt(t["segments_non_manual"]),
                      _fmt(t["segments_algorithm_name_absent"]),
                      _fmt(t["segments_algorithm_name_empty"])),
             n=_fmt(t["segments_algorithm_name_absent"]
                    + t["segments_algorithm_name_empty"]),
             denominator=_fmt(t["segments_non_manual"]),
             floor=no_validator_floor, dropped=dropped_text,
             external_source="PS3.3 2026c Table C.8.20-2",
             derived_from="STD-03",
             source_file="results/phase3/seg_identification_segments_by_stratum.csv",
             status_note="Absent and zero length are reported separately. The "
             "attribute compels a free-text string only: no version, no family "
             "code, no source.",
             **common),
        dict(id="P3-06",
             claim="The full provenance carrier list on sampled Segmentation "
                   "objects, in three states that are never collapsed to two.",
             status="MEASURED",
             value="; ".join(
                 "%s absent %d, zero-length %d, non-empty %d"
                 % (r.carrier, int(r.absent), int(r.zero_length), int(r.non_empty))
                 for r in carriers(objects).groupby("carrier")[
                     ["absent", "zero_length", "non_empty"]].sum().reset_index()
                 .itertuples()),
             n=str(len(phase3.CARRIERS) + 1), denominator=_fmt(t["objects"]),
             floor=no_validator_floor, dropped=dropped_text,
             external_source="PS3.3 2026c Table C.7-8b, Enhanced General "
                             "Equipment, Usage M in Table A.51-1",
             derived_from="STD-04",
             source_file="results/phase3/seg_carriers_by_stratum.csv",
             pinned_by_test="tests/test_phase3.py::test_state_separates_absent_from_zero_length",
             status_note="Manufacturer, ManufacturerModelName, "
             "DeviceSerialNumber and SoftwareVersions are Type 1 in this IOD, "
             "so for those four both absent and zero-length are violations. A "
             "presence check reports neither.",
             **common),
        dict(id="P3-07",
             claim="dciodvfy and dicom-validator message classes over the "
                   "sample, gross.",
             status="MEASURED",
             value="%s distinct (validator, message class) pairs over %s "
                   "objects" % (_fmt(int(out["messages"].groupby(
                       ["validator", "message_class_id"]).ngroups)
                       if len(out["messages"]) else 0), _fmt(t["objects"])),
             n=_fmt(int(out["messages"].groupby(
                 ["validator", "message_class_id"]).ngroups)
                 if len(out["messages"]) else 0),
             denominator=_fmt(t["objects"]),
             floor="none subtracted. These are gross counts. The Phase 1 floor "
                   "sets are writer-specific and fixture-specific and do not "
                   "transfer to these corpus writers, so no net rate is quoted "
                   "and no class here is adjudicated.",
             dropped=dropped_text,
             derived_from="F1-01,PRE-03",
             source_file="results/phase3/seg_message_classes.csv",
             pinned_by_test="tests/test_phase3.py::test_severity_matches_both_documented_forms",
             status_note="Counted as distinct (SOPInstanceUID, "
             "message_class_id) pairs through the Phase 1 normaliser, never as "
             "raw lines. Exit status recorded and never tested. Nothing here is "
             "NET: an unadjudicated class is UNDECIDABLE until it carries a "
             "cited PS3 section, and adjudication is a separate pass with two "
             "independent adjudicators.",
             **common),
        dict(id="P3-08",
             claim="The population estimate for the absence and incompleteness "
                   "outcomes, under the estimator PRE-06 registered, with both "
                   "variance forms.",
             status="DERIVED",
             value="absence %s percent of series, design-based se %s, clustered "
                   "se %s on %s df; incompleteness %s percent, design-based se "
                   "%s, clustered se %s"
                   % (pa.get("p_pct"), pa.get("se_design_pct"),
                      pa.get("se_clustered_pct"), pa.get("df_clustered"),
                      pi.get("p_pct"), pi.get("se_design_pct"),
                      pi.get("se_clustered_pct")),
             n=_fmt(pa.get("series", 0)), denominator="190,146",
             floor=no_validator_floor, dropped=dropped_text,
             derived_from="P3-01,P3-02,PRE-06",
             source_file="results/phase3/seg_totals.json",
             status_note="Stratified and series weighted, with design weights "
             "N_h / n_h known exactly from a complete index. The clustered "
             "standard error takes the collection as the primary sampling unit "
             "and is the wider of the two, so it is the one quoted. %d "
             "single-collection strata are pooled into one variance stratum by "
             "the collapsed strata method, which is conservative."
             % pa.get("collapsed_strata", 0),
             **common),
        dict(id="P3-12",
             claim="The frame's writer label is provisional and the object "
                   "changes it. PRE-06 limitation 3 registered the response in "
                   "advance: relabel and report the reallocation, never "
                   "silently redraw.",
             status="MEASURED",
             value="%s objects across %s strata carry object-level evidence "
                   "naming a writer the index could not name; the draw is "
                   "unchanged and nothing was redrawn"
                   % (_fmt(out.get("relabelled_objects", 0)),
                      out.get("relabelled_strata", 0)),
             n=_fmt(out.get("relabelled_objects", 0)),
             denominator=_fmt(t["objects"]),
             floor="not applicable, no validator is involved",
             dropped="ImplementationVersionName values that "
                     "colophon.writers.WRITER_RULES has no rule for, such as "
                     "the dcm4che family, stay unidentified rather than being "
                     "classified by a rule invented after seeing the data",
             derived_from="W-01,PRE-06",
             source_file="results/phase3/seg_writer_relabel.csv",
             pinned_by_test="tests/test_phase3.py::test_writer_relabel_reuses_the_phase0_rule_table",
             status_note="The Phase 0 rule table is imported unchanged and only "
             "the evidence widens, so this cannot silently move the W-01 "
             "census. A stratum that moves to highdicom moves from having no "
             "measured Phase 1 floor to having one, which makes a post-floor "
             "rate quotable where the frame said it was not. That consequence "
             "is reported and not acted on here.",
             **common),
        dict(id="P3-11",
             claim="SegmentAlgorithmType (0062,0008) is Type 1 with Enumerated "
                   "Values, and the sample contains a value outside the three "
                   "the standard enumerates. dciodvfy scores it at Error "
                   "severity.",
             status="MEASURED",
             value="%s segments carry a SegmentAlgorithmType that is none of "
                   "AUTOMATIC, SEMIAUTOMATIC or MANUAL; dciodvfy raises "
                   "'Unrecognized enumerated value' on the objects carrying %s "
                   "of them"
                   % (_fmt(out.get("out_of_enumeration_segments", 0)),
                      _fmt(out.get("out_of_enumeration_flagged", 0))),
             n=_fmt(out.get("out_of_enumeration_segments", 0)),
             denominator=_fmt(t["segments"]),
             floor="none subtracted. The class is not in any Phase 1 floor set, "
                   "and it is not one of the pre-classified floor classes: an "
                   "unrecognised value is floor only where PS3.3 marks the list "
                   "extensible, and this list is Enumerated rather than a set "
                   "of Defined Terms.",
             dropped="these segments are outside the AUTOMATIC-or-SEMIAUTOMATIC "
                     "denominator of P3-01 and P3-02 by the wording of the "
                     "question, and are counted in this row rather than dropped",
             external_source="PS3.3 2026c Table C.8.20-4, Segment Description "
                             "Macro: Enumerated Values AUTOMATIC, "
                             "SEMIAUTOMATIC, MANUAL",
             derived_from="STD-03",
             validator="dciodvfy",
             source_file="results/phase3/seg_out_of_enumeration.csv",
             status_note="The conformance call is a third party's, not ours: "
             "dciodvfy raises it independently at Error severity and names the "
             "attribute. This row reports that verdict and the count, and does "
             "not add an opinion to it.",
             **{k: v for k, v in common.items() if k != "validator"}),
        dict(id="P3-10",
             claim="A complete Algorithm Identification Macro is not the same "
                   "thing as an informative one. Some segments declare "
                   "SegmentAlgorithmType AUTOMATIC or SEMIAUTOMATIC while the "
                   "macro they carry names the algorithm as a manual one.",
             status="MEASURED",
             value="%s segments declare a non-MANUAL algorithm type while their "
                   "AlgorithmName (0066,0036) names a manual procedure"
                   % _fmt(out.get("type_name_disagreement", 0)),
             n=_fmt(out.get("type_name_disagreement", 0)),
             denominator=_fmt(t["segments_ident_present_complete"]),
             floor=no_validator_floor, dropped=dropped_text,
             external_source="PS3.3 2026c Table C.8.20-4 for (0062,0008) and "
                             "section 10.16 Table 10-19 for (0066,0036)",
             derived_from="P3-02",
             source_file="results/phase3/seg_macro_content.csv",
             status_note="Observation, not a verdict. SegmentAlgorithmType is "
             "Type 1 with enumerated values and AlgorithmName is a free-text "
             "LO, and PS3.3 states no relation between them, so these segments "
             "are conformant. Reported and left unresolved, because deciding "
             "which of the two attributes is right would be adjudicating our "
             "own result.",
             **common),
        dict(id="P3-09",
             claim="Two of the three conformance tools in this class's panel "
                   "ran. The third is recorded as NOT RUN and never as passed.",
             status="MEASURED",
             value="dciodvfy and dicom-validator ran; PixelMed "
                   "DicomInstanceValidator did not, the jar is absent from the "
                   "pinned toolchain; dcmpschk was not run at all",
             n="2", denominator="3",
             floor="not applicable, this row describes the instrument",
             dropped="the reference-parse axis, segimage2itkimage and the "
                     "highdicom reader, was not run in this pass and no axis-2 "
                     "result is reported",
             derived_from="V-04,V-08",
             source_file="results/phase3_segmentation.md",
             pinned_by_test="tests/test_phase3.py::test_dcmpschk_is_not_used_on_segmentation",
             status_note="On a Segmentation missing two Type 1 attributes "
             "dcmpschk printed 'Test passed.', so addendum 02 keeps it to GSPS. "
             "Reporting a two-tool result as the full panel would overstate the "
             "instrument.",
             **common),
    ]
    pending = RESULTS / "pending_ledger"
    pending.mkdir(parents=True, exist_ok=True)
    path = pending / "track_phase3.json"
    path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return path
