"""Track C adjudication: Real World Value Mapping and Key Object Selection.

Two classes, 20 and 40 objects, both complete in the Phase 2 census. Every
distinct message class the census recorded for them is adjudicated here into one
of five categories, and no message class is skipped. The rule table below is
keyed by a regular expression over the normalised message template, and the run
asserts that every message class id in scope matches exactly one rule, so a new
message class from a re-run fails loudly rather than being dropped.

The five categories, as fixed before the adjudication:

    FLOOR         legal by the standard, flagged anyway. Needs a citation
                  showing the construct is permitted.
    NET           a stated requirement is violated. Needs a citation to the
                  section AND table giving the Type or condition.
    NOT-IOD       the message is not about IOD conformance.
    PLAUSIBILITY  a value-quality heuristic with no requirement behind it.
    UNDECIDABLE   not adjudicable with a citation.

No citation means UNDECIDABLE. Nothing here decides an object is non-conformant
because it looks wrong: every NET carries the section and table that state the
requirement, quoted.

Triples, per class per validator:

    gross  objects with at least one message class of that severity
    floor  objects whose only such classes are FLOOR, NOT-IOD or PLAUSIBILITY
    net    objects with at least one class adjudicated NET

Usage:
    python -m colophon.adjudicate_rwv_kos
"""
from __future__ import annotations

import csv
import json
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path

from .paths import CACHE, RESULTS

CMD = "python -m colophon.adjudicate_rwv_kos"
RECORDS = CACHE / "census" / "records.jsonl"
PHASE2 = RESULTS / "phase2"
MESSAGE_CLASSES = PHASE2 / "census_message_classes.csv"
OUT_CSV = PHASE2 / "adjudication_rwv_kos.csv"
OUT_MD = PHASE2 / "net_rates_rwv_kos.md"
PENDING = RESULTS / "pending_ledger" / "track_c_rwv_kos.json"
LEDGER = RESULTS / "ledger.csv"

RWV = "Real World Value Mapping Storage"
KOS = "Key Object Selection Document Storage"
CLASSES = [RWV, KOS]

EDITION = "PS3 2026c, dicom.nema.org current output, retrieved 2026-08-02"
VALIDATOR_VERSIONS = ("dicom3tools snapshot 20260701065818; "
                      "dicom-validator 0.8.2 edition 2026c in process")

# --- the rule table -----------------------------------------------------------
# One entry per construct, not per emitted string, because dciodvfy embeds the
# offending value in the text and the census hashes the text, so twenty patients
# give twenty message class ids for one construct.
RULES = [
    {
        "name": "dicomdir_study_id",
        "pattern": r"^Warning - Missing attribute or value that would be needed "
                   r"to build DICOMDIR - Study ID$",
        "adjudication": "NOT-IOD",
        "citation_section": "PS3.3 Section F.5.2 Study Directory Record Definition, "
                            "read against PS3.3 Section C.7.2.1 General Study Module",
        "citation_table": "PS3.3 Table F.5-2 Study Keys, and PS3.3 Table C.7-3 "
                          "General Study Module Attributes",
        "citation_quote": "Table F.5-2 makes Study ID (0020,0010) Type 1 in a "
                          "directory record whose Directory Record Type (0004,1430) "
                          "has Value \"STUDY.\" Table C.7-3 gives the same attribute "
                          "in the General Study Module as Type 2, \"User or equipment "
                          "generated Study identifier.\"",
        "rationale": "The requirement quoted is a key of the Basic Directory IOD, "
                     "which is built by media interchange software, not by the "
                     "instance. Inside the IODs under test Study ID is Type 2 and may "
                     "be present with zero length. The message is advice about "
                     "building a DICOMDIR and states nothing about IOD conformance.",
    },
    {
        "name": "laterality_2c",
        "pattern": r"^Error - Missing attribute Type 2C Conditional "
                   r"Element=<Laterality> Module=<GeneralSeries>$",
        "adjudication": "FLOOR",
        "citation_section": "PS3.3 Section C.7.3.1 General Series Module",
        "citation_table": "PS3.3 Table C.7-5a General Series Module Attributes",
        "citation_quote": "Laterality (0020,0060), Type 2C: \"Laterality of (paired) "
                          "body part examined. Required if the body part examined is "
                          "a paired structure and Image Laterality (0020,0062) or "
                          "Frame Laterality (0020,9072) or Measurement Laterality "
                          "(0024,0113) are not present.\"",
        "rationale": "The condition is required only when the body part examined is a "
                     "paired structure. Whether it is paired is not carried by the "
                     "General Series Module, so the antecedent cannot be evaluated "
                     "from the dataset and absence is permitted whenever the body "
                     "part is not paired. dciodvfy raises this same class against a "
                     "known-good highdicom object in the Phase 1 floor set, "
                     "message class e4c7fa2d56f7 in results/floor_set.csv.",
    },
    {
        "name": "srt_deprecated",
        "pattern": r"^Warning - CodingSchemeDesignator is deprecated - attribute "
                   r"<CodingSchemeDesignator> = <SRT>$",
        "adjudication": "FLOOR",
        "citation_section": "PS3.16 Section 8 Coding Schemes, with PS3.3 Section 8.2 "
                            "Coding Scheme Designator and Coding Scheme Version",
        "citation_table": "PS3.16 Table 8-1 Coding Schemes",
        "citation_quote": "Table 8-1 still lists SRT, UID 2.16.840.1.113883.6.96, "
                          "SNOMED CT, described as \"SNOMED CT\" using the "
                          "\"SNOMED-RT style\" Code Values, with the note \"This "
                          "Coding Scheme is deprecated. The use of \"SNOMED-RT style\" "
                          "Code Values is no longer authorized by SNOMED except for "
                          "creation by legacy devices, legacy objects in archives, and "
                          "receiving systems that need to understand them.\" PS3.3 "
                          "Section 8.2: \"Standard Coding Scheme designators used in "
                          "DICOM information interchange are listed in PS3.16.\"",
        "rationale": "SRT remains a listed designator in the current edition. The "
                     "standard marks it deprecated, which is not a prohibition, and "
                     "no Type and no condition is stated against its use. The word "
                     "Retired does not appear in the row.",
    },
    {
        "name": "coding_scheme_designator_L",
        "pattern": r"^Warning - Unrecognized defined term <L> for value 1 of "
                   r"attribute <Coding Scheme Designator>$",
        "adjudication": "FLOOR",
        "citation_section": "PS3.3 Section 8.2 Coding Scheme Designator and Coding "
                            "Scheme Version",
        "citation_table": "none, Section 8.2 is prose. The registry it points at is "
                          "PS3.16 Table 8-1 Coding Schemes, and L is not a row there",
        "citation_quote": "\"Other Coding Scheme designators, for both private and "
                          "public Coding Schemes, may be used, in accordance with "
                          "PS3.16.\" and \"Coding Scheme designators beginning with "
                          "\"99\" and the Coding Scheme designator \"L\" are defined "
                          "in HL7 V2 to be private or local Coding Schemes.\"",
        "rationale": "The standard names the designator L explicitly, as the HL7 V2 "
                     "designator for a private or local Coding Scheme, and permits "
                     "designators beyond those listed in PS3.16. The value is outside "
                     "dciodvfy's list of known designators and inside the set the "
                     "standard allows.",
    },
    {
        "name": "retired_person_name_form",
        "pattern": r"^Warning - Value dubious for this VR - \(TAG\) PN Patient's Name "
                   r"PN \[1\] = <.+> - Retired Person Name form$",
        "adjudication": "PLAUSIBILITY",
        "citation_section": "PS3.5 Section 6.2 Value Representation",
        "citation_table": "PS3.5 Table 6.2-1 DICOM Value Representations, PN entry",
        "citation_quote": "\"The component delimiter shall be the caret \"^\" "
                          "character (5EH). There shall be no more than four component "
                          "delimiters, i.e., none after the last component if all "
                          "components are present. Delimiters are required for "
                          "interior null components. Trailing null components and "
                          "their delimiters may be omitted.\"",
        "rationale": "A PN carrying only a family name complex, with the trailing "
                     "null components and their delimiters omitted, is what the VR "
                     "definition permits. No requirement is cited by the validator "
                     "and none is violated. The complaint is that the value looks "
                     "like a pseudonym rather than a name, which is a value-quality "
                     "heuristic.",
    },
    {
        "name": "manufacturer_type2_dciodvfy",
        "pattern": r"^Error - Missing attribute Type 2 Required "
                   r"Element=<Manufacturer> Module=<GeneralEquipment>$",
        "adjudication": "NET",
        "citation_section": "PS3.3 Section C.7.5.1 General Equipment Module, with "
                            "PS3.3 Section A.35.4.3 Key Object Selection Document IOD "
                            "Module Table",
        "citation_table": "PS3.3 Table C.7-8 General Equipment Module Attributes, and "
                          "PS3.3 Table A.35.4-1 Key Object Selection Document IOD "
                          "Modules",
        "citation_quote": "Table A.35.4-1 gives the Equipment IE row \"General "
                          "Equipment, C.7.5.1, M\". Table C.7-8 gives Manufacturer "
                          "(0008,0070), Type 2, \"Manufacturer of the equipment that "
                          "produced the Composite Instances.\"",
        "rationale": "The module is Mandatory in this IOD and the attribute is Type 2, "
                     "so it shall be present in the Data Set and may be zero length. "
                     "The census records Manufacturer as absent, not zero length, on "
                     "every object in the class, and two independent validators agree. "
                     "A stated requirement is violated.",
    },
    {
        "name": "manufacturer_missing_dicom_validator",
        "pattern": r"^Module <General Equipment> Tag \(TAG\) \(Manufacturer\) is "
                   r"missing$",
        "adjudication": "NET",
        "citation_section": "PS3.3 Section C.7.5.1 General Equipment Module, with "
                            "PS3.3 Section A.35.4.3 Key Object Selection Document IOD "
                            "Module Table",
        "citation_table": "PS3.3 Table C.7-8 General Equipment Module Attributes, and "
                          "PS3.3 Table A.35.4-1 Key Object Selection Document IOD "
                          "Modules",
        "citation_quote": "Table A.35.4-1 gives the Equipment IE row \"General "
                          "Equipment, C.7.5.1, M\". Table C.7-8 gives Manufacturer "
                          "(0008,0070), Type 2, \"Manufacturer of the equipment that "
                          "produced the Composite Instances.\"",
        "rationale": "The same finding as the dciodvfy Type 2 error, reached "
                     "independently by the second validator. dicom-validator emits no "
                     "severity of its own and the census records the section header it "
                     "groups the finding under, ERROR, as the severity as emitted.",
    },
]

CLEARED = {"FLOOR", "NOT-IOD", "PLAUSIBILITY"}


def classify(template: str) -> dict:
    hits = [r for r in RULES if re.match(r["pattern"], template)]
    if len(hits) != 1:
        raise ValueError("%d rules match %r, expected exactly 1" % (len(hits), template))
    return hits[0]


# --- inputs -------------------------------------------------------------------
def read_message_classes() -> list[dict]:
    with MESSAGE_CLASSES.open(newline="", encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if r["sop_class_name"] in CLASSES]
    if not rows:
        raise RuntimeError("no message classes for the two Track C classes")
    return rows


def read_records() -> list[dict]:
    """One entry per object, with the collection it came from.

    Read only. A census process may be appending to this file.
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
                continue  # a partial trailing line from a live writer
            if rec.get("sop_class_name") not in CLASSES:
                continue
            for obj in rec.get("objects", []):
                out.append({
                    "sop_class_name": rec["sop_class_name"],
                    "collection_id": rec.get("collection_id"),
                    "series_instance_uid": rec.get("series_instance_uid"),
                    "sop_instance_uid": obj.get("sop_instance_uid"),
                    "status": obj.get("status"),
                    "messages": obj.get("messages", []),
                })
    return out


# --- triples ------------------------------------------------------------------
def triples(objects: list[dict]) -> dict:
    """(gross, floor, net) per class, per validator, per severity band.

    Both validators are reported for both classes, including where a validator
    said nothing at all. A tool that ran and found nothing is a result. A tool
    that was skipped is a different thing and is named in the prose.
    """
    out = {}
    for sop in CLASSES:
        mine = [o for o in objects if o["sop_class_name"] == sop]
        for validator in ("dciodvfy", "dicom-validator"):
            for band in ("Error", "Warning"):
                gross = fl = net = 0
                for o in mine:
                    cls = {m[1]: classify(m[3])["adjudication"]
                           for m in o["messages"]
                           if m[0] == validator and m[2].upper() == band.upper()}
                    if not cls:
                        continue
                    gross += 1
                    if any(a == "NET" for a in cls.values()):
                        net += 1
                    if all(a in CLEARED for a in cls.values()):
                        fl += 1
                out[(sop, validator, band)] = {
                    "objects": len(mine), "gross": gross, "floor": fl, "net": net}
    return out


def net_objects_any_validator(objects: list[dict], sop: str) -> tuple[int, int]:
    mine = [o for o in objects if o["sop_class_name"] == sop]
    n = 0
    for o in mine:
        if any(m[2].upper() == "ERROR" and classify(m[3])["adjudication"] == "NET"
               for m in o["messages"]):
            n += 1
    return n, len(mine)


def by_collection(objects: list[dict], sop: str) -> list[tuple[str, int, int, float]]:
    grouped = defaultdict(list)
    for o in objects:
        if o["sop_class_name"] == sop:
            grouped[o["collection_id"]].append(o)
    rows = []
    for coll in sorted(grouped):
        objs = grouped[coll]
        n = sum(1 for o in objs
                if any(m[2].upper() == "ERROR"
                       and classify(m[3])["adjudication"] == "NET"
                       for m in o["messages"]))
        rows.append((coll, n, len(objs), 100.0 * n / len(objs)))
    return rows


def series_and_objects(objects: list[dict]) -> list[tuple[str, int, int]]:
    out = []
    for sop in CLASSES:
        mine = [o for o in objects if o["sop_class_name"] == sop]
        out.append((sop, len({o["series_instance_uid"] for o in mine}), len(mine)))
    return out


def pct(n: int, d: int) -> float:
    return 0.0 if not d else round(100.0 * n / d, 2)


# --- outputs ------------------------------------------------------------------
def write_csv(rows: list[dict]) -> None:
    fields = ["sop_class_name", "validator", "message_class_id", "message_template",
              "severity_as_emitted", "objects", "adjudication", "citation_section",
              "citation_table", "citation_quote", "rationale"]
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in sorted(rows, key=lambda r: (r["sop_class_name"], r["validator"],
                                             -int(r["objects"]), r["message_class_id"])):
            w.writerow({k: r[k] for k in fields})


def write_md(rows: list[dict], tri: dict, objects: list[dict]) -> None:
    L = []
    A = L.append
    A("# Track C adjudication: Real World Value Mapping and Key Object Selection")
    A("")
    A("Generated by `%s`. Two classes, both complete in the Phase 2 census: Real "
      "World Value Mapping Storage, 20 objects, and Key Object Selection Document "
      "Storage, 40 objects. Every distinct message class the census recorded for "
      "these classes is adjudicated. None is skipped." % CMD)
    A("")
    A("Standard edition cited: %s. The census binaries are unchanged: %s."
      % (EDITION, VALIDATOR_VERSIONS))
    A("")

    A("## Adjudication counts")
    A("")
    A("A message class is one construct as the validator words it. dciodvfy embeds "
      "the offending value in the text, so one construct can produce many message "
      "class ids: twenty patient names give twenty ids for one Person Name warning.")
    A("")
    A("| SOP class | adjudication | message classes | objects with at least one |")
    A("|---|---|---|---|")
    n_classes = Counter((r["sop_class_name"], r["adjudication"]) for r in rows)
    touched = defaultdict(set)
    for o in objects:
        for m in o["messages"]:
            touched[(o["sop_class_name"],
                     classify(m[3])["adjudication"])].add(o["sop_instance_uid"])
    for sop in CLASSES:
        total = len([o for o in objects if o["sop_class_name"] == sop])
        for adj in ("FLOOR", "NET", "NOT-IOD", "PLAUSIBILITY", "UNDECIDABLE"):
            if (sop, adj) in n_classes:
                A("| %s | %s | %d | %d of %d |"
                  % (sop, adj, n_classes[(sop, adj)],
                     len(touched[(sop, adj)]), total))
    A("")
    A("No message class in either class is UNDECIDABLE. Every FLOOR carries a "
      "citation showing the construct is permitted, and every NET carries the "
      "section and the table that state the requirement.")
    A("")

    A("## Triples, per class per validator")
    A("")
    A("gross: objects with at least one message class of that severity. "
      "floor: objects whose only such classes are FLOOR, NOT-IOD or PLAUSIBILITY. "
      "net: objects with at least one class adjudicated NET.")
    A("")
    A("| SOP class | validator | severity | objects | gross | floor | net | net pct |")
    A("|---|---|---|---|---|---|---|---|")
    for (sop, validator, band), t in sorted(tri.items()):
        A("| %s | %s | %s | %d | %d | %d | %d | %.1f |"
          % (sop, validator, band, t["objects"], t["gross"], t["floor"], t["net"],
             pct(t["net"], t["objects"])))
    A("")
    A("dicom-validator ran in process on every object of both classes. On Real World "
      "Value Mapping Storage it emitted nothing at all, of either severity, which is "
      "the zero row above and not a skipped tool. dcmpschk is not run on these "
      "classes, by design, because it is written for presentation states, so it has "
      "no row here at all. highdicom's reader is not part of the census pass.")
    A("")

    A("## Residual NET classes")
    A("")
    nets = [r for r in rows if r["adjudication"] == "NET"]
    if not nets:
        A("None.")
    else:
        A("| SOP class | validator | message class | severity | objects | section | table |")
        A("|---|---|---|---|---|---|---|")
        for r in sorted(nets, key=lambda r: (r["sop_class_name"], r["validator"])):
            A("| %s | %s | %s | %s | %s | %s | %s |"
              % (r["sop_class_name"], r["validator"], r["message_class_id"],
                 r["severity_as_emitted"], r["objects"], r["citation_section"],
                 r["citation_table"]))
        A("")
        for r in sorted(nets, key=lambda r: (r["sop_class_name"], r["validator"])):
            A("**%s, %s, %s.** %s" % (r["sop_class_name"], r["validator"],
                                      r["message_class_id"], r["message_template"]))
            A("")
            A("> %s" % r["citation_quote"])
            A("")
            A(r["rationale"])
            A("")
    A("Both residual NET classes are the same defect reached by two independent "
      "validators: Manufacturer (0008,0070) absent from a Mandatory General "
      "Equipment Module. They are one finding on 40 objects, not two.")
    A("")

    A("## PRE-05")
    A("")
    A("PRE-05 was registered before any archive object was validated. Its test as "
      "applied here: a class is a substantial conformance failure if and only if "
      "(a) the net error-class rate exceeds 5.0 percent of the objects in the "
      "stratum and (b) the collection-level median net rate also exceeds 5.0 "
      "percent. Both numbers are reported for both classes, including where the "
      "first fails. The net error-class rate is the union across validators: an "
      "object counts once if any validator raised a class adjudicated NET at Error "
      "severity.")
    A("")
    A("| SOP class | net objects | objects | (a) net error rate pct | collections | "
      "(b) collection median net rate pct | (a) over 5.0 | (b) over 5.0 | verdict |")
    A("|---|---|---|---|---|---|---|---|---|")
    for sop in CLASSES:
        n, d = net_objects_any_validator(objects, sop)
        colls = by_collection(objects, sop)
        med = statistics.median([c[3] for c in colls]) if colls else 0.0
        a = pct(n, d) > 5.0
        b = med > 5.0
        verdict = ("substantial conformance failure" if a and b
                   else "not a substantial conformance failure")
        A("| %s | %d | %d | %.1f | %d | %.1f | %s | %s | %s |"
          % (sop, n, d, pct(n, d), len(colls), med, "yes" if a else "no",
             "yes" if b else "no", verdict))
    A("")
    A("Per collection, so the median is checkable:")
    A("")
    A("| SOP class | collection | net objects | objects | net rate pct |")
    A("|---|---|---|---|---|")
    for sop in CLASSES:
        for coll, n, d, p in by_collection(objects, sop):
            A("| %s | %s | %d | %d | %.1f |" % (sop, coll, n, d, p))
    A("")
    A("Each class sits in exactly one IDC collection, so the median across "
      "collections is that single collection's rate. The median is not a "
      "distribution here and should not be read as one.")
    A("")
    A("PRE-05 words its threshold as a rate over series in a class, and the triples "
      "above are over objects. In these two classes the two denominators are the "
      "same: %s. So the wording does not change the verdict."
      % "; ".join("%s, %d series and %d objects" % (sop, s, o)
                  for sop, s, o in series_and_objects(objects)))
    A("")
    A("Against the three bands PRE-05 fixed in advance, null at or below 5 percent "
      "and substantial above 20 percent with the band between reported as "
      "indeterminate: Real World Value Mapping Storage is null at 0.0 percent, and "
      "Key Object Selection Document Storage is substantial at 100.0 percent. For "
      "Key Object Selection Document Storage the prediction of a largely null "
      "result is wrong. Every object in the class omits a Type 2 attribute from a "
      "Mandatory module, and two independent validators say so.")
    A("")

    A("## What was dropped")
    A("")
    A("Nothing. Both classes are complete in the census, 20 of 20 and 40 of 40 "
      "series, every object status OK, and every distinct message class recorded "
      "for them is adjudicated in results/phase2/adjudication_rwv_kos.csv. No "
      "sampling, no truncation, no message class carried forward unresolved.")
    A("")
    A("One inconsistency is reported rather than resolved: results/environment.json "
      "pins the standard edition as PS3 2025e, and the pages cited here, served at "
      "the current output on dicom.nema.org and retrieved 2026-08-02, are labelled "
      "PS3 2026c, which is the edition results/standards.json records. The citations "
      "above are 2026c.")
    A("")
    OUT_MD.write_text("\n".join(L), encoding="utf-8")


# --- ledger -------------------------------------------------------------------
def pre05_existing() -> dict:
    with LEDGER.open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["id"] == "PRE-05":
                return r
    raise RuntimeError("PRE-05 is not in the ledger")


def ledger_rows(rows: list[dict], tri: dict, objects: list[dict]) -> list[dict]:
    common = {
        "section": "P2C",
        "section_title": "Phase 2 census, non-Segmentation classes",
        "command": CMD,
        "validator_version": VALIDATOR_VERSIONS,
        "idc_index_version": "v24",
        "verified_on": "2026-08-02",
        "pinned_by_test": "tests/test_adjudicate_rwv_kos.py"
                          "::test_every_message_class_is_adjudicated",
    }
    triples_test = "tests/test_adjudicate_rwv_kos.py::test_the_triples_are_pinned"
    pre05_test = "tests/test_adjudicate_rwv_kos.py::test_pre05_inputs_are_pinned"
    citation_test = ("tests/test_adjudicate_rwv_kos.py"
                     "::test_no_net_without_a_section_and_a_table")
    dropped = ("nothing. Both classes are complete, 20 of 20 and 40 of 40 series, "
               "and every distinct message class recorded for them is adjudicated")
    floor_note = ("the floor is the adjudication itself: FLOOR, NOT-IOD and "
                  "PLAUSIBILITY classes are named in "
                  "results/phase2/adjudication_rwv_kos.csv and subtracted from gross "
                  "to give net")

    def t(sop, validator, band):
        return tri[(sop, validator, band)]

    out = []
    rwv_e = t(RWV, "dciodvfy", "Error")
    rwv_w = t(RWV, "dciodvfy", "Warning")
    kos_e = t(KOS, "dciodvfy", "Error")
    kos_w = t(KOS, "dciodvfy", "Warning")
    kos_dv = t(KOS, "dicom-validator", "Error")

    out.append(dict(common, id="C-RWV-01", status="MEASURED", pinned_by_test=triples_test,
        claim="Real World Value Mapping Storage has no net error class. dciodvfy "
              "raises an error class on every object and the only such class is the "
              "Type 2C Laterality conditional, which is adjudicated FLOOR.",
        status_note="Gross, floor and net are object counts, not message counts. An "
                    "object counts once for a message class.",
        value="dciodvfy Error triple, gross %d, floor %d, net %d of %d objects, net "
              "0.0 percent" % (rwv_e["gross"], rwv_e["floor"], rwv_e["net"],
                               rwv_e["objects"]),
        sop_class=RWV, n=str(rwv_e["net"]), denominator=str(rwv_e["objects"]),
        floor=floor_note, dropped=dropped, validator="dciodvfy",
        source_file="results/phase2/net_rates_rwv_kos.md",
        derived_from="P2C-02"))

    out.append(dict(common, id="C-RWV-02", status="MEASURED", pinned_by_test=triples_test,
        claim="Real World Value Mapping Storage has no net warning class. Every "
              "warning class is FLOOR, NOT-IOD or PLAUSIBILITY.",
        status_note="Twenty of the warning classes are one construct, the Person Name "
                    "form warning, split across twenty patient values by the "
                    "validator's own wording.",
        value="dciodvfy Warning triple, gross %d, floor %d, net %d of %d objects"
              % (rwv_w["gross"], rwv_w["floor"], rwv_w["net"], rwv_w["objects"]),
        sop_class=RWV, n=str(rwv_w["net"]), denominator=str(rwv_w["objects"]),
        floor=floor_note, dropped=dropped, validator="dciodvfy",
        source_file="results/phase2/net_rates_rwv_kos.md",
        derived_from="P2C-02"))

    out.append(dict(common, id="C-RWV-03", status="MEASURED", pinned_by_test=triples_test,
        claim="dicom-validator emitted no finding of any severity on any Real World "
              "Value Mapping object.",
        status_note="A null result from a tool that ran, not a tool that was skipped. "
                    "dicom-validator runs in process on every object of every class "
                    "in the census.",
        value="dicom-validator, 0 findings on 20 of 20 objects, gross 0, floor 0, net 0",
        sop_class=RWV, n="0", denominator="20",
        floor="not applicable, there is no message to adjudicate",
        dropped=dropped, validator="dicom-validator",
        source_file="results/phase2/net_rates_rwv_kos.md",
        derived_from="P2C-02"))

    out.append(dict(common, id="C-RWV-04", status="VERIFIED",
        claim="The dciodvfy error class on every Real World Value Mapping object, "
              "missing Type 2C Laterality in the General Series Module, is a floor "
              "class: the condition cannot be evaluated from the dataset and absence "
              "is permitted where the body part examined is not a paired structure.",
        status_note="Corroborated independently: the same message class id, "
                    "e4c7fa2d56f7, is in the Phase 1 floor set against a known-good "
                    "highdicom Parametric Map object.",
        value="PS3.3 Table C.7-5a, Laterality (0020,0060) Type 2C: \"Required if the "
              "body part examined is a paired structure and Image Laterality "
              "(0020,0062) or Frame Laterality (0020,9072) or Measurement Laterality "
              "(0024,0113) are not present.\"",
        sop_class=RWV, n="20", denominator="20",
        floor="this row is the floor", dropped=dropped, validator="dciodvfy",
        source_file="results/phase2/adjudication_rwv_kos.csv",
        external_source="DICOM PS3.3 Section C.7.3.1, Table C.7-5a, %s" % EDITION))

    out.append(dict(common, id="C-RWV-05", status="VERIFIED",
        claim="The two coding scheme warnings on Real World Value Mapping objects, "
              "the deprecated designator SRT and the unrecognised designator L, are "
              "both floor classes. Both designators are permitted by the standard.",
        status_note="SRT is still a row in the current PS3.16 Table 8-1 and is marked "
                    "deprecated, not retired and not prohibited. L is named in PS3.3 "
                    "Section 8.2 as the HL7 V2 designator for a private or local "
                    "Coding Scheme.",
        value="SRT on 20 of 20 objects, L on 1 of 20 objects, both FLOOR",
        sop_class=RWV, n="20", denominator="20",
        floor="this row is the floor", dropped=dropped, validator="dciodvfy",
        source_file="results/phase2/adjudication_rwv_kos.csv",
        external_source="DICOM PS3.16 Section 8, Table 8-1, and DICOM PS3.3 "
                        "Section 8.2, %s" % EDITION))

    out.append(dict(common, id="C-RWV-06", status="VERIFIED",
        claim="The dciodvfy DICOMDIR warning, raised on every object of both Track C "
              "classes, is not a statement about IOD conformance. Study ID is Type 1 "
              "in a STUDY directory record and Type 2 in the General Study Module.",
        status_note="The Basic Directory IOD is built by media interchange software. "
                    "The instance is not non-conformant for failing to satisfy a "
                    "directory key.",
        value="PS3.3 Table F.5-2 makes Study ID (0020,0010) Type 1 in a STUDY "
              "directory record; PS3.3 Table C.7-3 makes it Type 2 in the General "
              "Study Module, \"User or equipment generated Study identifier.\"",
        sop_class="%s and %s" % (RWV, KOS), n="60", denominator="60",
        floor="this row is the floor", dropped=dropped, validator="dciodvfy",
        source_file="results/phase2/adjudication_rwv_kos.csv",
        external_source="DICOM PS3.3 Section F.5.2 Table F.5-2 and Section C.7.2.1 "
                        "Table C.7-3, %s" % EDITION))

    out.append(dict(common, id="C-RWV-07", status="VERIFIED",
        claim="The Retired Person Name form warning is a plausibility complaint, not "
              "a conformance finding. A PN value carrying only the family name "
              "complex is what the VR definition permits.",
        status_note="Thirty message class ids across the two classes, one construct. "
                    "The validator embeds the patient value in the message, so the "
                    "census hashes one id per distinct value.",
        value="PS3.5 Table 6.2-1, PN: \"Trailing null components and their delimiters "
              "may be omitted.\"",
        sop_class="%s and %s" % (RWV, KOS), n="60", denominator="60",
        floor="this row is the floor", dropped=dropped, validator="dciodvfy",
        source_file="results/phase2/adjudication_rwv_kos.csv",
        external_source="DICOM PS3.5 Section 6.2, Table 6.2-1, %s" % EDITION))

    out.append(dict(common, id="C-KOS-01", status="MEASURED", pinned_by_test=triples_test,
        claim="Every Key Object Selection Document object in IDC v24 carries a net "
              "error class: Manufacturer (0008,0070) is absent from a General "
              "Equipment Module that Table A.35.4-1 makes Mandatory.",
        status_note="Absent, not zero length. The census records the three states "
                    "separately and records absent on all 40 objects.",
        value="dciodvfy Error triple, gross %d, floor %d, net %d of %d objects, net "
              "100.0 percent" % (kos_e["gross"], kos_e["floor"], kos_e["net"],
                                 kos_e["objects"]),
        sop_class=KOS, n=str(kos_e["net"]), denominator=str(kos_e["objects"]),
        floor=floor_note, dropped=dropped, validator="dciodvfy",
        source_file="results/phase2/net_rates_rwv_kos.md",
        derived_from="P2C-02,P2C-03"))

    out.append(dict(common, id="C-KOS-02", status="MEASURED", pinned_by_test=triples_test,
        claim="dicom-validator reaches the same net finding on the same 40 Key Object "
              "Selection Document objects, independently of dciodvfy.",
        status_note="dicom-validator emits no severity of its own. ERROR is the "
                    "section header it groups the finding under, recorded as the "
                    "severity as emitted.",
        value="dicom-validator ERROR triple, gross %d, floor %d, net %d of %d objects, "
              "net 100.0 percent" % (kos_dv["gross"], kos_dv["floor"], kos_dv["net"],
                                     kos_dv["objects"]),
        sop_class=KOS, n=str(kos_dv["net"]), denominator=str(kos_dv["objects"]),
        floor=floor_note, dropped=dropped, validator="dicom-validator",
        source_file="results/phase2/net_rates_rwv_kos.md",
        derived_from="P2C-02"))

    out.append(dict(common, id="C-KOS-03", status="MEASURED", pinned_by_test=triples_test,
        claim="Key Object Selection Document Storage has no net warning class. Every "
              "warning class is NOT-IOD or PLAUSIBILITY.",
        status_note="The whole warning gross is the DICOMDIR advice plus the Person "
                    "Name form heuristic.",
        value="dciodvfy Warning triple, gross %d, floor %d, net %d of %d objects"
              % (kos_w["gross"], kos_w["floor"], kos_w["net"], kos_w["objects"]),
        sop_class=KOS, n=str(kos_w["net"]), denominator=str(kos_w["objects"]),
        floor=floor_note, dropped=dropped, validator="dciodvfy",
        source_file="results/phase2/net_rates_rwv_kos.md",
        derived_from="P2C-02"))

    out.append(dict(common, id="C-KOS-04", status="VERIFIED", pinned_by_test=citation_test,
        claim="Manufacturer (0008,0070) is Type 2 in the General Equipment Module and "
              "that module is Mandatory in the Key Object Selection Document IOD, so "
              "an absent Manufacturer violates a stated requirement.",
        status_note="Type 2 means present and possibly zero length. Absent is neither.",
        value="PS3.3 Table A.35.4-1 Equipment IE row \"General Equipment, C.7.5.1, "
              "M\"; PS3.3 Table C.7-8 Manufacturer (0008,0070) Type 2, \"Manufacturer "
              "of the equipment that produced the Composite Instances.\"",
        sop_class=KOS, n="40", denominator="40",
        floor="not applicable, this row is a reading of the standard rather than a "
              "rate", dropped=dropped,
        validator="dciodvfy and dicom-validator, agreeing",
        source_file="results/phase2/adjudication_rwv_kos.csv",
        external_source="DICOM PS3.3 Section A.35.4.3 Table A.35.4-1 and Section "
                        "C.7.5.1 Table C.7-8, %s" % EDITION))

    # PRE-05, per class.
    rwv_n, rwv_d = net_objects_any_validator(objects, RWV)
    kos_n, kos_d = net_objects_any_validator(objects, KOS)
    rwv_colls = by_collection(objects, RWV)
    kos_colls = by_collection(objects, KOS)
    rwv_med = statistics.median([c[3] for c in rwv_colls])
    kos_med = statistics.median([c[3] for c in kos_colls])

    out.append(dict(common, id="C-RWV-08", status="DERIVED", pinned_by_test=pre05_test,
        claim="Real World Value Mapping Storage does not meet the PRE-05 test for a "
              "substantial conformance failure. Both of its two conditions fail.",
        status_note="Both numbers are reported, including the second, which is not "
                    "reached in practice once the first fails.",
        value="(a) net error-class rate %.1f percent of %d objects, threshold 5.0, "
              "not exceeded; (b) collection-level median net rate %.1f percent across "
              "%d collection, threshold 5.0, not exceeded"
              % (pct(rwv_n, rwv_d), rwv_d, rwv_med, len(rwv_colls)),
        sop_class=RWV, n=str(rwv_n), denominator=str(rwv_d),
        floor=floor_note, dropped=dropped,
        validator="dciodvfy and dicom-validator",
        command=CMD, source_file="results/phase2/net_rates_rwv_kos.md",
        derived_from="C-RWV-01,C-RWV-03,C-RWV-04,PRE-05",
        notes="The class sits in one IDC collection, ct_vs_pet_ventilation_imaging, "
              "so the collection-level median is that collection's rate and is not a "
              "distribution."))

    out.append(dict(common, id="C-KOS-05", status="DERIVED", pinned_by_test=pre05_test,
        claim="Key Object Selection Document Storage meets the PRE-05 test for a "
              "substantial conformance failure. Both of its two conditions hold, at "
              "100 percent.",
        status_note="This is the strongest form the test can return: every object in "
                    "the stratum, and the single collection's median equal to the "
                    "object rate.",
        value="(a) net error-class rate %.1f percent of %d objects, threshold 5.0, "
              "exceeded; (b) collection-level median net rate %.1f percent across %d "
              "collection, threshold 5.0, exceeded"
              % (pct(kos_n, kos_d), kos_d, kos_med, len(kos_colls)),
        sop_class=KOS, n=str(kos_n), denominator=str(kos_d),
        floor=floor_note, dropped=dropped,
        validator="dciodvfy and dicom-validator",
        command=CMD, source_file="results/phase2/net_rates_rwv_kos.md",
        derived_from="C-KOS-01,C-KOS-02,C-KOS-04,PRE-05",
        notes="The class sits in one IDC collection, qin_breast_dce_mri, so the "
              "collection-level median is that collection's rate and is not a "
              "distribution. The finding is a single defect repeated by a single "
              "writer, not 40 independent failures, and it is reported as such."))

    # PRE-05 itself. Claim text is read from the ledger so it is exact by
    # construction, and only status, status_note and notes are changed. The
    # fields carried over are reproduced verbatim because a merge replaces the
    # whole row rather than patching it.
    prior = pre05_existing()
    carry = ["id", "section", "section_title", "claim", "value", "sop_class",
             "floor", "dropped", "command", "source_file", "derived_from"]
    pre = {k: prior[k] for k in carry}
    pre["status"] = prior["status"]
    pre["status_note"] = (
        prior["status_note"] + " Track C outcome, two of the eight classes: Real "
        "World Value Mapping Storage 0.0 percent net error rate, null band. Key "
        "Object Selection Document Storage 100.0 percent net error rate, substantial "
        "band. The row stays PENDING because six classes are not adjudicated.")
    pre["notes"] = (
        "Track C, Real World Value Mapping Storage and Key Object Selection Document "
        "Storage, adjudicated 2026-08-02. Real World Value Mapping Storage: net error "
        "rate %.1f percent, collection median %.1f percent, both below 5.0, so it "
        "does not clear the threshold and the null prediction holds. Key Object "
        "Selection Document Storage: net error rate %.1f percent, collection median "
        "%.1f percent, both above 5.0 and above the 20 percent substantial bound, so "
        "it clears the threshold and PRE-01's prediction of a largely null result is "
        "wrong for this class. The reason it is wrong: every object in the class "
        "omits Manufacturer (0008,0070), a Type 2 attribute of a module that Table "
        "A.35.4-1 makes Mandatory, and dciodvfy and dicom-validator say so "
        "independently. Evidence in results/phase2/net_rates_rwv_kos.md and "
        "results/phase2/adjudication_rwv_kos.csv, produced by %s. Warning to whoever "
        "merges: a merge replaces this row whole, so a PRE-05 proposal from another "
        "track and this one cannot both survive. Reconcile the notes by hand."
        % (pct(rwv_n, rwv_d), rwv_med, pct(kos_n, kos_d), kos_med, CMD))
    out.append(pre)
    return out


def main() -> int:
    classes = read_message_classes()
    objects = read_records()

    rows = []
    for r in classes:
        rule = classify(r["message_template"])
        rows.append({
            "sop_class_name": r["sop_class_name"],
            "validator": r["validator"],
            "message_class_id": r["message_class_id"],
            "message_template": r["message_template"],
            "severity_as_emitted": r["severity_as_emitted"],
            "objects": r["objects"],
            "adjudication": rule["adjudication"],
            "citation_section": rule["citation_section"],
            "citation_table": rule["citation_table"],
            "citation_quote": rule["citation_quote"],
            "rationale": rule["rationale"],
        })

    # Nothing may be skipped: every message class seen in the records must also
    # be in the census table, and every one must have been adjudicated.
    seen = {(o["sop_class_name"], m[0], m[1]) for o in objects for m in o["messages"]}
    tabled = {(r["sop_class_name"], r["validator"], r["message_class_id"])
              for r in rows}
    missing = seen - tabled
    if missing:
        raise RuntimeError("message classes in the records but not adjudicated: %s"
                           % sorted(missing))

    tri = triples(objects)
    write_csv(rows)
    write_md(rows, tri, objects)
    PENDING.parent.mkdir(parents=True, exist_ok=True)
    PENDING.write_text(json.dumps(ledger_rows(rows, tri, objects), indent=2),
                       encoding="utf-8")

    counts = Counter(r["adjudication"] for r in rows)
    print("adjudicated %d message classes across %d objects: %s"
          % (len(rows), len(objects), dict(counts)))
    for key, t in sorted(tri.items()):
        print("  %-38s %-16s %-8s gross %3d floor %3d net %3d of %3d"
              % (key[0][:38], key[1], key[2], t["gross"], t["floor"], t["net"],
                 t["objects"]))
    print("wrote %s" % OUT_CSV)
    print("wrote %s" % OUT_MD)
    print("wrote %s" % PENDING)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
