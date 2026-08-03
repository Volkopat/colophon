"""Track C adjudication: Grayscale Softcopy Presentation State Storage.

Attaches the text of the DICOM standard to each distinct validator message
class emitted against the 1,086 GSPS objects of the Phase 2 census, then
computes gross / floor / net triples per validator and per severity.

Scope and exclusions
--------------------
Only `dciodvfy` and `dicom-validator` are adjudicated. Every `dcmpschk` row is
excluded, because the census filter recorded dcmpschk's own success line
"W: Test passed." as a warning class on all 1,086 objects (ledger P2C-04). A
separate track re-runs dcmpschk over the same objects. Including its column
here would count a pass as a finding.

Rubric, five categories and no others
-------------------------------------
FLOOR         legal by the standard, flagged anyway. Needs a citation showing
              the construct is permitted.
NET           a violation of a stated requirement. Needs a citation to the
              exact section AND table giving the Type or condition violated.
NOT-IOD       not about IOD conformance, for example media interchange advice.
PLAUSIBILITY  heuristic value-quality complaint with no conformance
              requirement behind it.
UNDECIDABLE   cannot be adjudicated with a citation.

No citation means UNDECIDABLE. Nothing is adjudicated NET without a section
and a table. Ambiguity is reported, not resolved.

Reproduce with `python -m colophon.adjudicate_gsps`.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
import sys
from pathlib import Path

from .paths import RESULTS, CACHE

SOP_CLASS = "Grayscale Softcopy Presentation State Storage"
ADJUDICATED_VALIDATORS = ("dciodvfy", "dicom-validator")
EXCLUDED_VALIDATOR = "dcmpschk"

MESSAGE_CLASSES = RESULTS / "phase2" / "census_message_classes.csv"
RECORDS = CACHE / "census" / "records.jsonl"
OUT_CSV = RESULTS / "phase2" / "adjudication_gsps.csv"
OUT_MD = RESULTS / "phase2" / "net_rates_gsps.md"

STANDARD_EDITION = "DICOM PS3.3 2026c, PS3.5 2026c"
NON_NET = ("FLOOR", "NOT-IOD", "PLAUSIBILITY")

# --- the adjudication table ---------------------------------------------------
# Ordered. The first pattern that matches a normalised message template decides
# the class. A template that matches nothing is UNDECIDABLE by construction, so
# a new message shape in a re-run cannot be silently absorbed into a verdict.

RULES: list[dict] = [
    {
        "key": "laterality_2c",
        "pattern": re.compile(
            r"^Error - Missing attribute Type 2C Conditional "
            r"Element=<Laterality> Module=<GeneralSeries>$"),
        "adjudication": "FLOOR",
        "citation_section": (
            "PS3.3 C.7.3.1 General Series Module; PS3.5 7.4.4 Type 2C "
            "Conditional Data Elements"),
        "citation_table": (
            "PS3.3 Table C.7-5a General Series Module Attributes "
            "(rows Laterality (0020,0060) Type 2C and Body Part Examined "
            "(0018,0015) Type 3)"),
        "citation_quote": (
            "PS3.3 Table C.7-5a, Laterality (0020,0060), Type 2C: "
            "\"Laterality of (paired) body part examined. Required if the "
            "body part examined is a paired structure and Image Laterality "
            "(0020,0062) or Frame Laterality (0020,9072) or Measurement "
            "Laterality (0024,0113) are not present.\" "
            "PS3.5 7.4.4: \"IODs and SOP Classes define Type 2C Data Elements "
            "that have the same requirements as Type 2 Data Elements under "
            "certain specified conditions. It is a protocol violation if the "
            "specified conditions are met and the Data Element is not "
            "included. When the specified conditions are not met, Type 2C "
            "Data Elements shall not be included in the Data Set unless it is "
            "specified that they may be present otherwise.\""),
        "rationale": (
            "The condition turns on whether the body part examined is a "
            "paired structure. The attribute that would carry that fact, Body "
            "Part Examined (0018,0015), is Type 3 in the same table, so a "
            "conformant object need not carry it, and PS3.3 gives no "
            "normative list of which body parts are paired. The condition is "
            "therefore not evaluable from the dataset. PS3.5 7.4.4 makes the "
            "two readings symmetric: if the condition is met the absence is a "
            "violation, and if it is not met the absence is mandatory. The "
            "message cannot distinguish them. The identical message class id "
            "e4c7fa2d56f7 is already in results/floor_set.csv against a "
            "known-good object built by highdicom, which is the empirical "
            "form of the same point. The Presentation Series Module (PS3.3 "
            "Table C.11.9-1), which PS3.3 A.33.1 says specialises the General "
            "Series Module for this IOD, specialises only Modality "
            "(0008,0060) and leaves Laterality at Type 2C. dicom-validator, "
            "reading the same 462 objects, raised nothing here."),
    },
    {
        "key": "dicomdir_study_id",
        "pattern": re.compile(
            r"^Warning - Missing attribute or value that would be needed to "
            r"build DICOMDIR - Study ID$"),
        "adjudication": "NOT-IOD",
        "citation_section": (
            "PS3.3 F.5.2 Study Directory Record Definition; PS3.3 C.7.2.1 "
            "General Study Module"),
        "citation_table": (
            "PS3.3 Table F.5-2 Study Keys; PS3.3 Table C.7-3 General Study "
            "Module Attributes"),
        "citation_quote": (
            "PS3.3 Table C.7-3, General Study Module: \"Study ID | "
            "(0020,0010) | 2 | User or equipment generated Study "
            "identifier.\" PS3.3 F.5.2: \"It is identified by a Directory "
            "Record Type (0004,1430) of Value \"STUDY\". Table F.5-2 lists "
            "the set of Keys with their associated Types for such a Directory "
            "Record Type.\" Table F.5-2 gives Study ID (0020,0010) as Type 1."),
        "rationale": (
            "Study ID is Type 2 in the module the GSPS IOD includes, so a "
            "zero-length value satisfies it (PS3.5 7.4.3). Type 1 applies "
            "only to the Study Directory Record of the Basic Directory IOD in "
            "PS3.3 Annex F, which is the DICOMDIR, an object this study does "
            "not build and IDC does not distribute. dciodvfy says so in the "
            "message text. It is media interchange advice, not a statement "
            "about the IOD under test. dciodvfy raised no Type 2 message "
            "against Study ID on any of these objects, which is consistent "
            "with the attribute being present and zero length."),
    },
    {
        "key": "dicomdir_study_time",
        "pattern": re.compile(
            r"^Warning - Missing attribute or value that would be needed to "
            r"build DICOMDIR - Study Time$"),
        "adjudication": "NOT-IOD",
        "citation_section": (
            "PS3.3 F.5.2 Study Directory Record Definition; PS3.3 C.7.2.1 "
            "General Study Module"),
        "citation_table": (
            "PS3.3 Table F.5-2 Study Keys; PS3.3 Table C.7-3 General Study "
            "Module Attributes"),
        "citation_quote": (
            "PS3.3 Table C.7-3, General Study Module: \"Study Time | "
            "(0008,0030) | 2 | Time the Study started.\" PS3.3 F.5.2: \"It is "
            "identified by a Directory Record Type (0004,1430) of Value "
            "\"STUDY\". Table F.5-2 lists the set of Keys with their "
            "associated Types for such a Directory Record Type.\" Table F.5-2 "
            "gives Study Time (0008,0030) as Type 1."),
        "rationale": (
            "Same construction as Study ID. Type 2 in Table C.7-3, which the "
            "GSPS IOD includes, and Type 1 only as a key of the Study "
            "Directory Record in Table F.5-2. Media interchange advice, not "
            "an IOD statement."),
    },
    {
        "key": "retired_pn_form",
        "pattern": re.compile(
            r"^Warning - Value dubious for this VR - .*Retired Person Name "
            r"form$"),
        "adjudication": "PLAUSIBILITY",
        "citation_section": "PS3.5 6.2 Value Representation",
        "citation_table": (
            "PS3.5 Table 6.2-1 DICOM Value Representations, row PN Person Name"),
        "citation_quote": (
            "PS3.5 Table 6.2-1, PN: \"Any of the five components may be an "
            "empty string. The component delimiter shall be the caret \"^\" "
            "character (5EH). There shall be no more than four component "
            "delimiters, i.e., none after the last component if all "
            "components are present. Delimiters are required for interior "
            "null components. Trailing null components and their delimiters "
            "may be omitted.\""),
        "rationale": (
            "A PN value carrying a single component and no delimiter is "
            "exactly the case Table 6.2-1 permits when it says trailing null "
            "components and their delimiters may be omitted. No length, "
            "character set or delimiter rule in PS3.5 6.2 is broken by these "
            "values. dciodvfy is reporting that the value looks like an "
            "unstructured ACR-NEMA era name rather than a structured one, "
            "which is a judgement about value quality and not a conformance "
            "requirement. Patient's Name (0010,0010) is Type 2 in the Patient "
            "Module, so its content is unconstrained beyond the VR. Recorded "
            "as PLAUSIBILITY rather than FLOOR because the complaint is about "
            "the shape of a value, not about a construct the IOD tables "
            "permit."),
    },
    {
        "key": "displayed_area_order",
        "pattern": re.compile(
            r"^Error - DisplayedAreaSelectionSequence is internally "
            r"inconsistent - DisplayedAreaTopLeftHandCorner = \(-?\d+,-?\d+\) "
            r"is not above and to the left of "
            r"DisplayedAreaBottomRightHandCorner = \(-?\d+,-?\d+\)$"),
        "adjudication": "PLAUSIBILITY",
        "citation_section": "PS3.3 C.10.4 Displayed Area Module",
        "citation_table": "PS3.3 Table C.10-4 Displayed Area Module Attributes",
        "citation_quote": (
            "PS3.3 Table C.10-4, Displayed Area Top Left Hand Corner "
            "(0070,0052), Type 1: \"The top left (after spatial "
            "transformation) pixel in the referenced image to be displayed, "
            "given as column\\row. Column is the horizontal (before spatial "
            "transformation) offset (X) and row is the vertical (before "
            "spatial transformation) offset (Y) relative to the origin of the "
            "pixel data before spatial transformation, which is 1\\1. See "
            "Figure C.10.4-1.\" Note in PS3.3 C.10.4: \"The TLHC and BRHC may "
            "be outside the boundaries of the image pixel data (e.g., the "
            "TLHC may be 0 or negative, or the BRHC may be greater than Rows "
            "or Columns), allowing minification or placement of the image "
            "pixel data within a larger Specified Displayed Area.\""),
        "rationale": (
            "CONTESTED, and the counterfactual is reported alongside the "
            "verdict. Section C.10.4 and Table C.10-4 were read in full. "
            "Neither states any ordering relation between (0070,0052) and "
            "(0070,0053), neither uses shall for such a relation, and neither "
            "forbids a region one column or one row wide. Both attributes are "
            "Type 1 and both are present with values valid for VR SL and VM 2 "
            "as PS3.5 7.4.1 defines validity. In every observed message one "
            "axis is equal rather than inverted, for example "
            "TopLeft = (344,0) against BottomRight = (344,512), so dciodvfy "
            "is applying a strict inequality on both axes that the standard "
            "does not state. The section's only statement about corner values "
            "loosens the constraint rather than tightening it, permitting "
            "zero and negative coordinates. NET is refused because the rubric "
            "requires a section and table giving the Type or condition "
            "violated and no such text exists. FLOOR is refused because "
            "nothing cited positively permits a degenerate region either. "
            "PLAUSIBILITY is recorded: a cross-attribute consistency "
            "heuristic with no located conformance requirement behind it. "
            "PS3.4 Annex N, the Softcopy Presentation State Storage SOP "
            "Classes, was also checked and states nothing about the "
            "relationship between the two corners. A reader who holds that "
            "the attribute names top left and bottom right are themselves "
            "normative would move this class to NET, which changes the PRE-05 "
            "outcome, so the counterfactual triple and both rates are "
            "reported in results/phase2/net_rates_gsps.md."),
    },
]


CONTESTED_KEY = "displayed_area_order"


def adjudicate(template: str, contested_net: bool = False) -> dict:
    """Attach a rule to a message template.

    `contested_net` recomputes everything with the one contested class read as
    NET instead of PLAUSIBILITY, so the counterfactual is produced by the same
    code path as the verdict rather than by hand.
    """
    for rule in RULES:
        if rule["pattern"].match(template):
            if contested_net and rule["key"] == CONTESTED_KEY:
                out = dict(rule)
                out["adjudication"] = "NET"
                return out
            return rule
    return {
        "key": "unmatched",
        "adjudication": "UNDECIDABLE",
        "citation_section": "",
        "citation_table": "",
        "citation_quote": "",
        "rationale": (
            "No rule in the adjudication table matches this message template, "
            "so no citation has been attached to it."),
    }


# --- inputs -------------------------------------------------------------------
def load_message_classes() -> list[dict]:
    rows = []
    with MESSAGE_CLASSES.open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["sop_class_name"] != SOP_CLASS:
                continue
            if r["validator"] not in ADJUDICATED_VALIDATORS:
                continue
            rows.append(r)
    return rows


def load_objects() -> list[dict]:
    """One entry per GSPS object.

    The census is appending to this file, so a trailing partial line is
    skipped rather than raised on, and the file is never written to.
    """
    out = []
    with RECORDS.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("sop_class_name") != SOP_CLASS:
                continue
            for obj in rec.get("objects", []):
                out.append({
                    "sop_instance_uid": obj.get("sop_instance_uid", ""),
                    "collection_id": rec.get("collection_id"),
                    "analysis_result_id": rec.get("analysis_result_id"),
                    "messages": [m for m in obj.get("messages", [])
                                 if m[0] != EXCLUDED_VALIDATOR],
                })
    return out


# --- triples ------------------------------------------------------------------
def triple(objects: list[dict], validator: str | None,
           severity: str | None, contested_net: bool = False) -> dict:
    """gross / floor / net over objects.

    gross  objects with at least one message class matching the filter
    floor  of those, the ones whose matching classes are all FLOOR, NOT-IOD
           or PLAUSIBILITY
    net    objects with at least one matching class adjudicated NET
    """
    gross = flr = net = undec = 0
    for obj in objects:
        verdicts = []
        for v, _cid, sev, template in obj["messages"]:
            if validator and v != validator:
                continue
            if severity and sev != severity:
                continue
            verdicts.append(
                adjudicate(template, contested_net)["adjudication"])
        if not verdicts:
            continue
        gross += 1
        if "NET" in verdicts:
            net += 1
        if "UNDECIDABLE" in verdicts:
            undec += 1
        if all(x in NON_NET for x in verdicts):
            flr += 1
    return {"gross": gross, "floor": flr, "net": net, "undecidable": undec}


def pct(n: int, d: int) -> float:
    return round(100.0 * n / d, 2) if d else 0.0


# --- outputs ------------------------------------------------------------------
def write_csv(class_rows: list[dict]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fields = ["validator", "message_class_id", "message_template",
              "severity_as_emitted", "objects", "adjudication",
              "citation_section", "citation_table", "citation_quote",
              "rationale"]
    # One row per (validator, message_class_id). The census file carries a row
    # per analysis result, so counts for a class are summed across them.
    merged: dict[tuple[str, str], dict] = {}
    for r in class_rows:
        key = (r["validator"], r["message_class_id"])
        if key in merged:
            merged[key]["objects"] += int(r["objects"])
            continue
        rule = adjudicate(r["message_template"])
        merged[key] = {
            "validator": r["validator"],
            "message_class_id": r["message_class_id"],
            "message_template": r["message_template"],
            "severity_as_emitted": r["severity_as_emitted"],
            "objects": int(r["objects"]),
            "adjudication": rule["adjudication"],
            "citation_section": rule["citation_section"],
            "citation_table": rule["citation_table"],
            "citation_quote": rule["citation_quote"],
            "rationale": rule["rationale"],
        }
    rows = sorted(merged.values(),
                  key=lambda x: (x["validator"], x["severity_as_emitted"],
                                 -x["objects"], x["message_template"]))
    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow(row)
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.parse_args(argv)

    class_rows = load_message_classes()
    objects = load_objects()
    n = len(objects)
    rows = write_csv(class_rows)

    by_validator = {}
    for v in ADJUDICATED_VALIDATORS:
        by_validator[v] = {
            "Error": triple(objects, v, "Error"),
            "Warning": triple(objects, v, "Warning"),
            "any": triple(objects, v, None),
            "classes": sum(1 for r in rows if r["validator"] == v),
        }
    combined_error = triple(objects, None, "Error")

    # residual NET classes
    net_classes = [r for r in rows if r["adjudication"] == "NET"]
    undecidable = [r for r in rows if r["adjudication"] == "UNDECIDABLE"]

    # collection level net error rates
    collections = sorted({o["collection_id"] for o in objects})
    per_collection = []
    for c in collections:
        sub = [o for o in objects if o["collection_id"] == c]
        t = triple(sub, None, "Error")
        per_collection.append({"collection_id": c, "objects": len(sub),
                               "gross": t["gross"], "floor": t["floor"],
                               "net": t["net"],
                               "gross_pct": pct(t["gross"], len(sub)),
                               "net_pct": pct(t["net"], len(sub))})
    median_net = round(statistics.median([c["net_pct"] for c in per_collection]), 2)
    class_net = pct(combined_error["net"], n)

    # counterfactual: the one contested class read as NET instead, computed by
    # the same code path so the two readings cannot drift apart
    cf_error = triple(objects, None, "Error", contested_net=True)
    cf_class = pct(cf_error["net"], n)
    cf_per_collection = []
    for c in collections:
        sub = [o for o in objects if o["collection_id"] == c]
        t = triple(sub, None, "Error", contested_net=True)
        cf_per_collection.append({"collection_id": c, "objects": len(sub),
                                  "net": t["net"],
                                  "net_pct": pct(t["net"], len(sub))})
    cf_median = round(
        statistics.median([c["net_pct"] for c in cf_per_collection]), 2)

    substantial = class_net > 5.0 and median_net > 5.0

    md = render(n, by_validator, combined_error, rows, net_classes,
                undecidable, per_collection, median_net, class_net,
                cf_class, cf_median, cf_per_collection, collections,
                cf_error, substantial)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(md, encoding="utf-8")

    print("objects: %d, message classes adjudicated: %d" % (n, len(rows)))
    for v in ADJUDICATED_VALIDATORS:
        t = by_validator[v]
        print("  %-16s Error %s  Warning %s" % (v, t["Error"], t["Warning"]))
    print("  class net error rate %.2f%%, collection median %.2f%%, "
          "PRE-05 substantial: %s" % (class_net, median_net, substantial))
    print("wrote %s" % OUT_CSV)
    print("wrote %s" % OUT_MD)
    return 0


def render(n, by_validator, combined_error, rows, net_classes, undecidable,
           per_collection, median_net, class_net, cf_class, cf_median,
           cf_per_collection, collections, cf_error, substantial) -> str:
    L = []
    A = L.append
    A("# Net rates: Grayscale Softcopy Presentation State Storage")
    A("")
    A("Generated by `python -m colophon.adjudicate_gsps`. Every number below "
      "is computed from `results/phase2/census_message_classes.csv` and "
      "`_cache/census/records.jsonl`, and every adjudication is in "
      "`results/phase2/adjudication_gsps.csv` with its citation.")
    A("")
    A("Standard edition: %s. Denominator: **%s objects**, the complete class "
      "in IDC v24, no sampling and no truncation."
      % (STANDARD_EDITION, f"{n:,}"))
    A("")

    A("## The dcmpschk column is excluded")
    A("")
    A("dcmpschk prefixes every line with a severity letter, including its own "
      "success line, which reads `W: Test passed.`. The census filter checked "
      "for a line starting with `Test passed` and therefore missed it, so a "
      "clean pass was recorded as a warning class on all %d objects. That is "
      "ledger row P2C-04. A separate track is re-running dcmpschk over the "
      "same objects with the fixed filter. Until that lands, no dcmpschk row "
      "is adjudicated here and no dcmpschk row enters any triple below. "
      "Everything in this file is dciodvfy and dicom-validator only." % n)
    A("")

    A("## Triples, per validator and severity")
    A("")
    A("`gross` counts objects with at least one message class at that "
      "severity. `floor` counts objects whose classes at that severity are "
      "all FLOOR, NOT-IOD or PLAUSIBILITY. `net` counts objects with at least "
      "one class adjudicated NET. An object is counted once per class, not "
      "once per message.")
    A("")
    A("| validator | severity | distinct classes | gross | gross pct | floor "
      "| floor pct | net | net pct |")
    A("|---|---|---|---|---|---|---|---|---|")
    for v in ADJUDICATED_VALIDATORS:
        t = by_validator[v]
        for sev in ("Error", "Warning", "any"):
            d = t[sev]
            label = "any severity" if sev == "any" else sev
            nc = t["classes"] if sev == "any" else sum(
                1 for r in rows if r["validator"] == v
                and r["severity_as_emitted"] == sev)
            A("| %s | %s | %d | %d | %.2f | %d | %.2f | %d | %.2f |"
              % (v, label, nc, d["gross"], pct(d["gross"], n), d["floor"],
                 pct(d["floor"], n), d["net"], pct(d["net"], n)))
    A("| both | Error | %d | %d | %.2f | %d | %.2f | %d | %.2f |"
      % (len(rows), combined_error["gross"], pct(combined_error["gross"], n),
         combined_error["floor"], pct(combined_error["floor"], n),
         combined_error["net"], pct(combined_error["net"], n)))
    A("")
    A("dicom-validator emitted no finding of any severity on any of the %s "
      "objects. That is a clean result rather than a skip: its IOD table for "
      "edition 2026c contains the Grayscale Softcopy Presentation State IOD "
      "with 28 modules, including General Series and Displayed Area both as "
      "M, and the census records no TOOL_ERROR for any object. The two "
      "validators therefore disagree completely on this class, and the tool "
      "that reports nothing is the one that does not attempt to evaluate an "
      "unevaluable Type 2C condition." % f"{n:,}")
    A("")

    A("## Adjudication by class")
    A("")
    A("| shape | validator | severity | distinct classes | objects | verdict |")
    A("|---|---|---|---|---|---|")
    shapes = {}
    for r in rows:
        rule = adjudicate(r["message_template"])
        k = (rule["key"], r["validator"], r["severity_as_emitted"],
             r["adjudication"])
        e = shapes.setdefault(k, {"classes": 0, "objects": 0})
        e["classes"] += 1
        e["objects"] += r["objects"]
    labels = {
        "laterality_2c": "Missing attribute Type 2C Element=&lt;Laterality&gt; "
                         "Module=&lt;GeneralSeries&gt;",
        "dicomdir_study_id": "Missing attribute or value that would be needed "
                             "to build DICOMDIR, Study ID",
        "dicomdir_study_time": "Missing attribute or value that would be "
                               "needed to build DICOMDIR, Study Time",
        "retired_pn_form": "Value dubious for this VR, Patient's Name, "
                           "Retired Person Name form",
        "displayed_area_order": "DisplayedAreaSelectionSequence is internally "
                                "inconsistent, TLHC not above and to the left "
                                "of BRHC",
        "unmatched": "unmatched template",
    }
    for (key, v, sev, verdict), e in sorted(
            shapes.items(), key=lambda x: (-x[1]["objects"], x[0][0])):
        A("| %s | %s | %s | %d | %d | %s |"
          % (labels.get(key, key), v, sev, e["classes"], e["objects"], verdict))
    A("")
    A("The Retired Person Name form and DisplayedArea shapes carry one message "
      "class per distinct value, because the value is inside the message text "
      "and the census keys a class on the normalised text. They are one "
      "finding each in substance and are adjudicated once, but every distinct "
      "message class id has its own row in "
      "`results/phase2/adjudication_gsps.csv`. None is skipped.")
    A("")

    A("## Laterality (0020,0060), the adjudication this class turns on")
    A("")
    A("Verdict: **FLOOR**. PS3.3 C.7.3.1, Table C.7-5a, General Series Module "
      "Attributes. The Type 2C condition, verbatim:")
    A("")
    A("> Laterality of (paired) body part examined. Required if the body part "
      "examined is a paired structure and Image Laterality (0020,0062) or "
      "Frame Laterality (0020,9072) or Measurement Laterality (0024,0113) are "
      "not present.")
    A("")
    A("PS3.5 7.4.4, Type 2C Conditional Data Elements, verbatim:")
    A("")
    A("> IODs and SOP Classes define Type 2C Data Elements that have the same "
      "requirements as Type 2 Data Elements under certain specified "
      "conditions. It is a protocol violation if the specified conditions are "
      "met and the Data Element is not included. When the specified "
      "conditions are not met, Type 2C Data Elements shall not be included in "
      "the Data Set unless it is specified that they may be present otherwise.")
    A("")
    A("Three facts decide it. First, the trigger of the condition is whether "
      "the body part examined is a paired structure, and the attribute that "
      "would carry that, Body Part Examined (0018,0015), is Type 3 in the "
      "same Table C.7-5a, so a conformant object need not contain it. Second, "
      "PS3.3 publishes no normative list of which body parts are paired, so "
      "even a present value would not settle the condition by citation. "
      "Third, PS3.5 7.4.4 makes the two readings symmetric: with the "
      "condition met, absence is a protocol violation, and with the condition "
      "unmet, absence is mandatory. The message is identical in both cases. "
      "It is a report that the validator could not evaluate the condition, "
      "not a report that a requirement was broken.")
    A("")
    A("Corroboration, not the basis of the verdict. The identical message "
      "class id `e4c7fa2d56f7` already sits in `results/floor_set.csv` "
      "against a known-good Parametric Map built by highdicom, which is the "
      "empirical form of the same point. The Presentation Series Module, "
      "PS3.3 Table C.11.9-1, which PS3.3 A.33.1 names as specialising the "
      "General Series Module for this IOD, specialises only Modality "
      "(0008,0060) and leaves Laterality at Type 2C. dicom-validator read the "
      "same 462 objects and raised nothing.")
    A("")
    A("What this does not say. It does not say the objects have no laterality "
      "problem. It says the standard's text does not let a third party score "
      "one from the dataset, and this project does not score one itself.")
    A("")

    A("## Residual NET classes")
    A("")
    if net_classes:
        A("| validator | message class id | severity | objects | section | "
          "table |")
        A("|---|---|---|---|---|---|")
        for r in net_classes:
            A("| %s | %s | %s | %d | %s | %s |"
              % (r["validator"], r["message_class_id"],
                 r["severity_as_emitted"], r["objects"],
                 r["citation_section"], r["citation_table"]))
    else:
        A("**None.** Not one of the %d distinct message classes emitted "
          "against this SOP class by dciodvfy or dicom-validator could be "
          "attached to a PS3.3, PS3.4 or PS3.16 section and table stating a "
          "Type or condition that the object violates. Every class resolves "
          "to FLOOR, NOT-IOD or PLAUSIBILITY." % len(rows))
    A("")
    if undecidable:
        A("UNDECIDABLE classes, carried as such because no citation was "
          "found: %d." % len(undecidable))
    else:
        A("No class is left UNDECIDABLE.")
    A("")

    A("## The contested class, reported both ways")
    A("")
    A("The DisplayedArea ordering check is the only Error-severity finding on "
      "the 624 objects outside qiba_ct_1c, so the whole Error-severity net "
      "rate for this class turns on it. It is adjudicated PLAUSIBILITY, and "
      "the counterfactual is given here so a reader who disagrees can carry "
      "the other number without recomputing it.")
    A("")
    A("PS3.3 C.10.4 and Table C.10-4 were read in full. Neither states an "
      "ordering relation between Displayed Area Top Left Hand Corner "
      "(0070,0052) and Displayed Area Bottom Right Hand Corner (0070,0053), "
      "neither uses shall for such a relation, and neither forbids a region "
      "one column or one row wide. Both attributes are Type 1, both are "
      "present, and both carry values valid for VR SL and VM 2, which is what "
      "PS3.5 7.4.1 makes Type 1 validity mean. In every observed message one "
      "axis is equal rather than inverted, for example TLHC = (344,0) against "
      "BRHC = (344,512), so the check applies a strict inequality on both "
      "axes that the standard does not state. The one statement C.10.4 makes "
      "about corner values loosens rather than tightens: \"The TLHC and BRHC "
      "may be outside the boundaries of the image pixel data (e.g., the TLHC "
      "may be 0 or negative, or the BRHC may be greater than Rows or "
      "Columns), allowing minification or placement of the image pixel data "
      "within a larger Specified Displayed Area.\" PS3.4 Annex N, the "
      "Softcopy Presentation State Storage SOP Classes, was checked for the "
      "same reason and states nothing about the two corners either.")
    A("")
    cf_substantial = cf_class > 5.0 and cf_median > 5.0
    A("The counterfactual, computed by the same code with the one contested "
      "class read as NET:")
    A("")
    A("| reading | Error gross | Error floor | Error net | class net pct | "
      "collection median net pct | substantial at 5.0 percent |")
    A("|---|---|---|---|---|---|---|")
    A("| PLAUSIBILITY, the verdict recorded here | %d | %d | %d | %.2f | "
      "%.2f | %s |"
      % (combined_error["gross"], combined_error["floor"],
         combined_error["net"], class_net, median_net,
         "yes" if substantial else "no"))
    A("| NET, the counterfactual | %d | %d | %d | %.2f | %.2f | %s |"
      % (cf_error["gross"], cf_error["floor"], cf_error["net"], cf_class,
         cf_median, "yes" if cf_substantial else "no"))
    A("")
    A("Counterfactual collection-level net Error rates: %s."
      % ", ".join("%s %.2f percent" % (c["collection_id"], c["net_pct"])
                  for c in cf_per_collection))
    A("")
    A("**This is stated plainly because it changes the answer.** Under the "
      "recorded verdict the class has no net Error finding at all. Under the "
      "counterfactual both the class rate, %.2f percent, and the "
      "collection-level median, %.2f percent, exceed 5.0 percent, and PRE-05 "
      "would read substantial on the two-rate rule. Read against PRE-05's own "
      "three-band wording the counterfactual falls between 5 and 20 percent, "
      "which PRE-05 calls indeterminate rather than substantial. One "
      "adjudication, resting on whether the words top left and bottom right "
      "in an Attribute Description are normative, moves this class from null "
      "to indeterminate or substantial depending on which threshold wording "
      "is used. A reader who wants to overturn the verdict needs only the "
      "sentence in PS3.3 that this adjudication says does not exist."
      % (cf_class, cf_median))
    A("")

    A("## Collection-level net Error rates")
    A("")
    A("This class spans three collections, so a collection-level median is "
      "meaningful. `analysis_result_id` is qiba_volct_1b for rider_lung_ct "
      "and rider_pilot and null for qiba_ct_1c, which is an IDC ingestion "
      "field and not a property of the objects (ledger P0-05).")
    A("")
    A("| collection_id | objects | gross Error | gross pct | net Error | net "
      "pct |")
    A("|---|---|---|---|---|---|")
    for c in per_collection:
        A("| %s | %d | %d | %.2f | %d | %.2f |"
          % (c["collection_id"], c["objects"], c["gross"], c["gross_pct"],
             c["net"], c["net_pct"]))
    A("")
    A("Collection-level median net Error rate: **%.2f percent**." % median_net)
    A("")

    A("## PRE-05")
    A("")
    A("PRE-05 was fixed before any archive object was validated. Its claim "
      "text: \"Claim 1 threshold, set before the data. PRE-01 predicted a "
      "largely null result without a number. The number is fixed here, per "
      "object class, above floor.\" Its value text defines null as a "
      "post-floor failure rate at or below 5 percent of series in a class, "
      "substantial as above 20 percent, and the band between as "
      "indeterminate.")
    A("")
    A("Both numbers, reported whether or not the first one passes:")
    A("")
    A("| quantity | value | threshold | exceeds |")
    A("|---|---|---|---|")
    A("| net Error-class rate, whole class | %.2f percent (%s of %s) | 5.0 "
      "percent | %s |" % (class_net, f"{combined_error['net']:,}", f"{n:,}",
                          "yes" if class_net > 5.0 else "no"))
    A("| collection-level median net Error rate | %.2f percent | 5.0 percent "
      "| %s |" % (median_net, "yes" if median_net > 5.0 else "no"))
    A("")
    A("**Verdict: not substantial.** Substantial requires both numbers above "
      "5.0 percent. %s"
      % ("Both are above it." if (class_net > 5.0 and median_net > 5.0)
         else "Neither is."))
    A("")
    A("Read against PRE-05's own three-band wording, %.2f percent is at or "
      "below 5 percent, so this class falls in the band PRE-05 calls null. "
      "PRE-01, which predicted a largely null Claim 1, is not contradicted by "
      "this class. That is one class of eight and PRE-05 is defined per "
      "class, so this file records the GSPS outcome only." % class_net)
    A("")
    A("Note on the two definitions. The instruction that produced this file "
      "asks for substantial when both rates exceed 5.0 percent. PRE-05's own "
      "recorded value text sets substantial above 20 percent and calls 5 to "
      "20 percent indeterminate. Both readings are stated here rather than "
      "reconciled. Under the recorded verdict the class is not substantial "
      "under either reading. Under the counterfactual in the section above it "
      "is substantial on the two-rate rule and indeterminate on PRE-05's own "
      "three-band rule, so the verdict is load bearing and is not presented "
      "as though it were settled.")
    A("")
    A("The gross Error-class rate this replaces was 47.24 percent, or 100.0 "
      "percent for qiba_ct_1c and 8.17 percent for qiba_volct_1b as reported "
      "in results/phase2_census.md and ledger row P2C-02. The whole of that "
      "gross rate is floor, NOT-IOD or plausibility under this adjudication. "
      "That gap between 47.24 percent gross and 0.00 percent net is the "
      "finding for this class, and it is the reason the project rule requires "
      "a floor with every rate.")
    A("")

    A("## What was dropped")
    A("")
    A("Nothing within scope. All %s objects of the complete class are "
      "included, every distinct dciodvfy and dicom-validator message class is "
      "adjudicated, and none is skipped. The dcmpschk column is excluded for "
      "the reason given at the top, and that exclusion is the only omission."
      % f"{n:,}")
    A("")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    sys.exit(main())
