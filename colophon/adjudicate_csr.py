"""Track C: adjudication of the Comprehensive SR Storage census.

One SOP class, 2,118 objects, three producer groups: `dicom_sr_breast_clinical`
(1,292), `qiba_volct_1b` (364) and an unlabelled group (462). Every distinct
`message_class_id` the Phase 2 census recorded for this class is adjudicated
here into exactly one of five categories, and no message class is skipped.

    FLOOR         permitted by the standard, the validator flags it anyway. A
                  citation showing the construct is permitted is required.
    NET           a stated requirement is violated. The section and the table
                  giving the Type or the condition are required.
    NOT-IOD       not about IOD conformance at all.
    PLAUSIBILITY  a value-quality heuristic with no requirement behind it.
    UNDECIDABLE   no citation reaches it. This is the default, not a fallback
                  of last resort: a rule that does not match leaves the class
                  UNDECIDABLE and says so.

The project forbids adjudicating its own results. Nothing here decides whether
an object is good. Each rule attaches the standard's own words to a validator's
own words, and where the two do not meet, the class is UNDECIDABLE and the gap
is written down.

Two findings in this class needed the standard rather than an opinion.

**Referenced Frame Number.** `dciodvfy` raises an Error on 722 objects, and
`dicom-validator` names the same attribute on the same 722. The agreement is
not independent. `dicom-validator`'s message is `is unexpected`, which its own
`ErrorCode.TagUnexpected` documents as "Tag is not in any allowed module"; a
failed condition is a different code, `TagNotAllowed`, and renders as `is not
allowed by condition`. Its parsed model of Table C.18.4-1 lifts the four
">"-nested rows out of Referenced SOP Sequence and makes them siblings of it,
so inside that Sequence it expects only Table 10-11 and calls everything else
unexpected. That is why it also flags the nested Referenced SOP Sequence, which
Table C.18.4-1 lists as Type 3, on 826 objects. So the `dicom-validator`
messages here are FLOOR and the `dciodvfy` Error stands or falls on its own
citation, which is Table C.18.4-1 plus PS3.5 7.4.2.

**SRT.** The retired SNOMED-RT designator is present on all 2,118. PS3.16 Table
8-1 still carries the row in the pinned edition and the note contemplates
"legacy objects in archives" explicitly. No prohibition is stated anywhere the
citation chain reaches, so the message is a deprecation notice, not a
requirement, and it is FLOOR.

Usage:
    python -m colophon.adjudicate_csr
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

from .paths import CACHE, RESULTS

CMD = "python -m colophon.adjudicate_csr"
SOP_CLASS = "Comprehensive SR Storage"
EDITION = "PS3 2026c"
VERIFIED_ON = "2026-08-02"

CLASSES_CSV = RESULTS / "phase2" / "census_message_classes.csv"
RECORDS = CACHE / "census" / "records.jsonl"
OUT_CSV = RESULTS / "phase2" / "adjudication_comprehensive_sr.csv"
OUT_MD = RESULTS / "phase2" / "net_rates_comprehensive_sr.md"
OUT_LEDGER = RESULTS / "pending_ledger" / "track_c_csr.json"

FLOOR_LIKE = {"FLOOR", "NOT-IOD", "PLAUSIBILITY"}

# Classes whose NET rests on a part other than PS3.3, PS3.4 or PS3.16. The
# rubric scopes NET citations to those three parts, and a VR length overflow or
# a dictionary VM breach lives in PS3.5 and PS3.6 instead. They are reported as
# NET because the requirement is stated, exact and quotable, and every triple
# is also reported with them demoted so a reader applying the rubric strictly
# gets that number without recomputing it.
OFF_PART_RULES = {"DS_LENGTH", "VR_ROLLUP", "VM_DICTIONARY", "DV_DS_INVALID"}


# --- the rubric, one entry per rule ------------------------------------------
# Ordered. First match wins. `pattern` is matched against the message template
# exactly as the census recorded it.
RULES: list[dict] = [
    dict(
        name="SRT_DEPRECATED",
        validator="dciodvfy",
        pattern=r"^Warning - CodingSchemeDesignator is deprecated",
        adjudication="FLOOR",
        section="PS3.16 Section 8 Coding Schemes and Section 8.1 SNOMED CT; "
                "PS3.3 Section 8.2 Coding Scheme Designator and Coding Scheme Version",
        table="PS3.16 Table 8-1 Coding Schemes",
        quote='PS3.16 Table 8-1, row "SRT", Description column: "[SNOMED], using '
              'the \\"SNOMED-RT style\\" Code Values (see Section 8.1)", carrying the '
              'Note: "This Coding Scheme is deprecated. The use of \\"SNOMED-RT '
              'style\\" Code Values is no longer authorized by SNOMED except for '
              'creation by legacy devices, legacy objects in archives, and receiving '
              'systems that need to understand them." PS3.3 Section 8.2: "Standard '
              'Coding Scheme designators used in DICOM information interchange are '
              'listed in PS3.16." PS3.16 Section 8.1: "It is the responsibility of '
              'such Application Entities to convert any alphanumeric SnomedID with '
              'Coding Scheme Designator \\"SRT\\" used in old DICOM objects and '
              'services to the corresponding numeric ConceptID code."',
        rationale="SRT is still a row of the normative Table 8-1 in the pinned "
                  "edition, and the note contemplates legacy objects in archives "
                  "explicitly. The obligation PS3.16 Section 8.1 states falls on the "
                  "receiving Application Entity, not on the stored object, and "
                  "PS3.16 Annex O exists to let receivers discharge it. No shall "
                  "anywhere in the citation chain forbids a stored object from "
                  "carrying SRT. dciodvfy's own wording is that the designator is "
                  "deprecated, not that it is not permitted, and the message is "
                  "emitted at Warning severity.",
    ),
    dict(
        name="DICOMDIR",
        validator="dciodvfy",
        pattern=r"^Warning - Missing attribute or value that would be needed to "
                r"build DICOMDIR",
        adjudication="NOT-IOD",
        section="not applicable, the message is not about IOD conformance",
        table="not applicable",
        quote="",
        rationale="The canonical NOT-IOD case named in the rubric. The attribute is "
                  "wanted for a DICOMDIR directory record, which is a Media Storage "
                  "matter in PS3.10 and PS3.11, and its absence is not a statement "
                  "about the Type of the attribute in this IOD. dciodvfy emits it at "
                  "Warning severity and does not name a Type.",
    ),
    dict(
        name="REF_FRAME_NUMBER",
        validator="dciodvfy",
        pattern=r"^Error - Shall not be present for Referenced SOP Class that is "
                r"not multi-frame",
        adjudication="NET",
        section="PS3.3 Section C.18.4 Image Reference Macro, reached from Section "
                "C.17.3 SR Document Content Module via Section C.17.3.3 Document "
                "Content Macro; Type 1C requirement in PS3.5 Section 7.4.2",
        table="PS3.3 Table C.18.4-1 Image Reference Macro Attributes; included by "
              "PS3.3 Table C.17-5 Document Content Macro Attributes, which is "
              "included by PS3.3 Table C.17-4 SR Document Content Module Attributes",
        quote='PS3.3 Table C.18.4-1, row ">Referenced Frame Number", tag (0008,1160), '
              'Type 1C: "Identifies the Frame numbers within the Referenced SOP '
              'Instance to which the reference applies. The first Frame shall be '
              'denoted as Frame number 1. Required if the Referenced SOP Instance is '
              'a Multi-frame Image and the reference does not apply to all Frames, '
              'and Referenced Segment Number (0062,000B) is not present." PS3.3 '
              'Table C.17-5: "Include Table C.18.4-1 Image Reference Macro '
              'Attributes if and only if Value Type (0040,A040) is IMAGE." PS3.5 '
              'Section 7.4.2 Type 1C Conditional Data Elements: "When the specified '
              'conditions are not met, Type 1C Data Elements shall not be included '
              'in the Data Set unless it is specified that they may be present '
              'otherwise."',
        rationale="dciodvfy reports that the Referenced SOP Class is not multi-frame, "
                  "so the first clause of the three-clause condition is false and the "
                  "condition is not met. PS3.5 Section 7.4.2 then makes presence a "
                  "protocol violation unless the attribute is separately allowed to "
                  "be present otherwise, and Table C.18.4-1 carries no such "
                  "allowance for (0008,1160). The standard uses the phrase May be "
                  "present otherwise where it intends it, for example on Current "
                  "Requested Procedure Evidence Sequence (0040,A375) in Table "
                  "C.17-2, and does not use it here. Two residuals are recorded and "
                  "not resolved: the condition is written on the Referenced SOP "
                  "Instance while dciodvfy evaluates it from the Referenced SOP "
                  "Class UID, which is exact only for SOP Classes that admit no "
                  "multi-frame Instance; and no PS3.16 template text was found that "
                  "permits the attribute for a single-frame reference.",
    ),
    dict(
        name="RETIRED_PN",
        validator="dciodvfy",
        pattern=r"^Warning - Value dubious for this VR .* Retired Person Name form$",
        adjudication="PLAUSIBILITY",
        section="not applicable, no requirement is cited by the message",
        table="not applicable",
        quote="",
        rationale="Named in the rubric as a plausibility heuristic. The message is "
                  "about the shape of a PN value, a single component with no caret "
                  "delimiters, which PS3.5 Table 6.2-1 permits for VR PN. No Type "
                  "and no condition is asserted, and dciodvfy emits it at Warning "
                  "severity with the word dubious.",
    ),
    dict(
        name="EVIDENCE_SEQUENCE",
        validator="dciodvfy",
        pattern=r"^Error - Referenced SOP Instance is not listed in "
                r"CurrentRequestedProcedureEvidenceSequence or "
                r"PertinentOtherEvidenceSequence",
        adjudication="NET",
        section="PS3.3 Section C.17.2 SR Document General Module and Section "
                "C.17.2.3 Current Requested Procedure Evidence Sequence and "
                "Pertinent Other Evidence Sequence",
        table="PS3.3 Table C.17-2 SR Document General Module Attributes",
        quote='PS3.3 Table C.17-2, row "Current Requested Procedure Evidence '
              'Sequence", tag (0040,A375), Type 1C: "Full set of Composite SOP '
              'Instances, of which the creator is aware, which were created to '
              'satisfy the current Requested Procedure(s) for which this SR Document '
              'is generated or that are referenced in the Content Tree." PS3.3 '
              'Section C.17.2.3: "The intent of the Current Requested Procedure '
              'Evidence Sequence (0040,A375) is to reference all evidence created in '
              'order to satisfy the current Requested Procedure(s) for this SR '
              'Document. This shall include, but is not limited to, all current '
              'evidence referenced in the Content Tree." and "For other SOP '
              'Instances that include the SR Document General Module, this Sequence '
              'shall contain at minimum the set of Composite SOP Instances from the '
              'current Requested Procedure(s) that are referenced in the Content '
              'Tree." and "For the purposes of inclusion in the Current Requested '
              'Procedure Evidence Sequence (0040,A375) and the Pertinent Other '
              'Evidence Sequence (0040,A385), the set of Composite SOP Instances is '
              'defined to include not only the images and waveforms referenced in '
              'the Content Tree, but also all presentation states, Real World Value '
              'maps and other accompanying Composite Instances that are referenced '
              'from the Content Items."',
        rationale="Two message classes fall under this rule, one naming an image "
                  "reference and one naming a presentation state reached from an "
                  "IMAGE Content Item. Both are covered: the third quoted sentence "
                  "of Section C.17.2.3 puts presentation states referenced from "
                  "Content Items inside the set that has to be listed, and the "
                  "second uses shall for content-tree references. The Comprehensive "
                  "SR IOD includes the SR Document General Module, so Table C.17-2 "
                  "applies.",
    ),
    dict(
        name="UNRECOGNISED_CSD",
        validator="dciodvfy",
        pattern=r"^Warning - Unrecognized defined term .* of attribute "
                r"<Coding Scheme Designator>",
        adjudication="UNDECIDABLE",
        section="PS3.3 Section 8.2; PS3.16 Section 8",
        table="PS3.16 Table 8-1 Coding Schemes",
        quote='PS3.3 Section 8.2: "Other Coding Scheme designators, for both private '
              'and public Coding Schemes, may be used, in accordance with PS3.16." '
              'PS3.16 Section 8: "Additionally, any Coding Scheme may be used that '
              'has an entry in the HL7 Registry of Coding Schemes (HL7 v2 Table '
              '0396, or the equivalent online registry), in which case the HL7 '
              'Symbolic Name shall be used as the value for the Coding Scheme '
              'Designator in DICOM, as long as it does not conflict with an entry '
              'Table 8-1 and fits within the Value Representation of the DICOM '
              'Coding Scheme Designator (0008,0102) Attribute. As specified in the '
              'HL7 v2 Table 0396, local or private Coding Schemes shall be '
              'identified by an alphanumeric identifier beginning with the '
              'characters \\"99\\"."',
        rationale="The permission in PS3.3 Section 8.2 is not open: it is in "
                  "accordance with PS3.16, and PS3.16 Section 8 conditions it on an "
                  "entry in HL7 v2 Table 0396 or, for private schemes, on a leading "
                  "99. The flagged value is not a row of Table 8-1 and does not "
                  "begin with 99, and this study did not consult the HL7 registry, "
                  "so neither limb can be closed. Reported as an ambiguity rather "
                  "than resolved. dciodvfy emits it at Warning severity and asserts "
                  "no Type or condition.",
    ),
    dict(
        name="DS_LENGTH",
        validator="dciodvfy",
        pattern=r"^Error - Value invalid for this VR .* Length invalid for this VR "
                r"= \d+, expected <= 16$",
        adjudication="NET",
        section="PS3.5 Section 6.2 Value Representation",
        table="PS3.5 Table 6.2-1 DICOM Value Representations, row DS",
        quote='PS3.5 Table 6.2-1, row "DS" Decimal String, Length of Value column: '
              '"16 bytes maximum".',
        rationale="A stated, exact, quotable maximum, breached by a 17 character "
                  "value. The citation is PS3.5 rather than PS3.3, PS3.4 or PS3.16 "
                  "because the defect is an encoding-level VR length overflow and "
                  "not an IOD Type or condition, so the rubric's citation scope does "
                  "not cover it. Recorded as NET and flagged as off-part, and every "
                  "triple in the report is also given with the off-part classes "
                  "demoted to UNDECIDABLE.",
    ),
    dict(
        name="VR_ROLLUP",
        validator="dciodvfy",
        pattern=r"^Error - Dicom dataset contains invalid data values for Value "
                r"Representations$",
        adjudication="NET",
        section="PS3.5 Section 6.2 Value Representation",
        table="PS3.5 Table 6.2-1 DICOM Value Representations, row DS",
        quote='PS3.5 Table 6.2-1, row "DS" Decimal String, Length of Value column: '
              '"16 bytes maximum".',
        rationale="dciodvfy's roll-up line for the per-attribute VR errors in the "
                  "same object. Measured, not assumed: the set of objects carrying "
                  "this message is exactly the set carrying the DS length errors, "
                  "232 objects with zero on either side of the difference, so it "
                  "carries the same citation and the same off-part flag. It adds no "
                  "object to any numerator.",
    ),
    dict(
        name="VM_DICTIONARY",
        validator="dciodvfy",
        pattern=r"^Error - Bad attribute Value Multiplicity",
        adjudication="NET",
        section="PS3.6 Section 6 Registry of DICOM Data Elements; module membership "
                "in PS3.3 Section C.7.2.1 General Study Module",
        table="PS3.6 Table 6-1 Registry of DICOM Data Elements, row (0008,1030); "
              "PS3.3 Table C.7-3 General Study Module Attributes",
        quote='PS3.6 Table 6-1, row (0008,1030) Study Description, VR LO, VM "1". '
              'PS3.3 Table C.7-3, row "Study Description", tag (0008,1030), Type 3: '
              '"Institution-generated description or classification of the Study '
              'performed."',
        rationale="Two message classes fall under this rule, dciodvfy's dictionary "
                  "form and its module form, both on Study Description in the same "
                  "single object. The registry gives VM 1 and the value carries two "
                  "components. Type 3 is not a defence: PS3.5 Section 7.4.5 makes "
                  "absence permissible, not a wrong VM when present. The citation is "
                  "PS3.6 rather than PS3.3, PS3.4 or PS3.16, so the class is flagged "
                  "off-part on the same terms as the DS length classes.",
    ),
    dict(
        name="DV_REF_FRAME_UNEXPECTED",
        validator="dicom-validator",
        pattern=r"\(Referenced SOP Sequence\) Tag \(TAG\) \(Referenced Frame Number\) "
                r"is unexpected$",
        adjudication="FLOOR",
        section="PS3.3 Section C.18.4 Image Reference Macro",
        table="PS3.3 Table C.18.4-1 Image Reference Macro Attributes",
        quote='PS3.3 Table C.18.4-1 opens with the row "Include Table C.18.3-1 '
              'Composite Object Reference Macro Attributes" and then lists '
              '">Referenced Frame Number", (0008,1160), 1C. The ">" places it one '
              'level inside the Referenced SOP Sequence that Table C.18.3-1 defines: '
              '"Referenced SOP Sequence, (0008,1199), 1, References to Composite '
              'Object SOP Class/SOP Instance pairs. Only a single Item shall be '
              'included in this Sequence." PS3.3 Table C.17-5: "Include Table '
              'C.18.4-1 Image Reference Macro Attributes if and only if Value Type '
              '(0040,A040) is IMAGE."',
        rationale="The construct the message names, (0008,1160) present inside "
                  "(0008,1199) of an IMAGE Content Item, is exactly where Table "
                  "C.18.4-1 puts it, so the location is permitted and the message is "
                  "FLOOR. The message is not a condition verdict: dicom-validator "
                  "0.8.2 documents ErrorCode.TagUnexpected as Tag is not in any "
                  "allowed module and renders it as is unexpected, while a failed "
                  "condition is ErrorCode.TagNotAllowed and renders as is not "
                  "allowed by condition. Its parsed model of Table C.18.4-1, read "
                  "back from the pinned 2026c standard cache, holds (0008,1160), "
                  "(0062,000B), the nested (0008,1199), (0008,114B) and (0088,0200) "
                  "as siblings of the included Referenced SOP Sequence rather than "
                  "as its children, so inside that Sequence it expects only Table "
                  "10-11 and reports everything else as unexpected. Consequence for "
                  "the census: this message class is not independent confirmation of "
                  "dciodvfy's Referenced Frame Number Error on the same 722 objects.",
    ),
    dict(
        name="DV_NESTED_REFSOP_UNEXPECTED",
        validator="dicom-validator",
        pattern=r"\(Referenced SOP Sequence\) Tag \(TAG\) \(Referenced SOP Sequence\) "
                r"is unexpected$",
        adjudication="FLOOR",
        section="PS3.3 Section C.18.4 Image Reference Macro",
        table="PS3.3 Table C.18.4-1 Image Reference Macro Attributes",
        quote='PS3.3 Table C.18.4-1, row ">Referenced SOP Sequence", tag (0008,1199), '
              'Type 3: "Reference to a Softcopy Presentation State SOP Class/SOP '
              'Instance pair. Only a single Item is permitted in this Sequence." '
              'PS3.5 Section 7.4.5: "IODs and SOP Classes define Type 3 Data '
              'Elements that are optional Data Elements. Absence of a Type 3 Data '
              'Element from a Data Set does not convey any significance and is not a '
              'protocol violation."',
        rationale="A Type 3 attribute listed by the macro at exactly the nesting "
                  "depth the object uses, flagged as not belonging to any allowed "
                  "module. Same modelling gap as the Referenced Frame Number class, "
                  "and the clearest demonstration of it, because no condition exists "
                  "on a Type 3 attribute that could have failed.",
    ),
    dict(
        name="DV_DS_INVALID",
        validator="dicom-validator",
        pattern=r"\(Numeric Value\) has invalid value .* for VR DS$",
        adjudication="NET",
        section="PS3.5 Section 6.2 Value Representation",
        table="PS3.5 Table 6.2-1 DICOM Value Representations, row DS",
        quote='PS3.5 Table 6.2-1, row "DS" Decimal String, Length of Value column: '
              '"16 bytes maximum".',
        rationale="The same 17 character values dciodvfy reports, found "
                  "independently by a second codebase through a different route, "
                  "pydicom's VR validation rather than a dicom3tools length check. "
                  "Off-part on the same terms as the dciodvfy DS length classes.",
    ),
]

UNMATCHED = dict(
    name="UNMATCHED",
    adjudication="UNDECIDABLE",
    section="",
    table="",
    quote="",
    rationale="No adjudication rule in colophon.adjudicate_csr matched this message "
              "template. Recorded as UNDECIDABLE rather than assigned by judgement.",
)


def classify(validator: str, template: str) -> dict:
    for rule in RULES:
        if rule["validator"] != validator:
            continue
        if re.search(rule["pattern"], template):
            return rule
    return UNMATCHED


# --- inputs -------------------------------------------------------------------
def _arid(value) -> str:
    """Normalise the analysis result id.

    The census writes the unlabelled group as a JSON float NaN, which is truthy,
    so `value or "NULL"` silently keeps the NaN and splits the group across two
    keys later. This is the guard for that.
    """
    if isinstance(value, str) and value.strip():
        return value
    return "NULL"


def load_message_classes() -> list[dict]:
    with CLASSES_CSV.open(newline="", encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh) if r["sop_class_name"] == SOP_CLASS]


def load_objects() -> list[dict]:
    """One entry per object, with its distinct message classes.

    The census records file is append-only and a census process may be writing
    to it. It is opened read only and never rewritten.
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
                classes = {}
                for validator, class_id, severity, template in obj.get("messages", []):
                    classes[(validator, class_id)] = (severity, template)
                out.append(dict(
                    series_instance_uid=rec["series_instance_uid"],
                    sop_instance_uid=obj.get("sop_instance_uid", ""),
                    analysis_result_id=_arid(rec.get("analysis_result_id")),
                    collection_id=_arid(rec.get("collection_id")),
                    status=obj.get("status", ""),
                    classes=classes,
                ))
    return out


# --- triples ------------------------------------------------------------------
def triple(objects: list[dict], validator: str, severity_kind: str,
           verdict, demote_off_part: bool = False) -> dict:
    """gross, floor, net over a set of objects, for one validator and severity.

    gross  objects carrying at least one message class of that severity
    floor  of those, the ones whose classes are all FLOOR, NOT-IOD or
           PLAUSIBILITY
    net    objects carrying at least one class adjudicated NET
    other  the remainder: no NET, but at least one UNDECIDABLE, so neither
           floor nor net. Reported rather than folded into either, because
           folding it into floor would understate and into net would overstate.
    """
    gross = net = floor = other = 0
    for obj in objects:
        cats = []
        for (val, class_id), (severity, template) in obj["classes"].items():
            if val != validator:
                continue
            if severity.upper() != severity_kind:
                continue
            cats.append(verdict(val, class_id, demote_off_part))
        if not cats:
            continue
        gross += 1
        if "NET" in cats:
            net += 1
        elif all(c in FLOOR_LIKE for c in cats):
            floor += 1
        else:
            other += 1
    n = len(objects)
    return dict(objects=n, gross=gross, floor=floor, net=net, other=other,
                pct_gross=pct(gross, n), pct_floor=pct(floor, n), pct_net=pct(net, n))


def pct(num: int, den: int) -> float:
    return round(100.0 * num / den, 2) if den else 0.0


def net_objects(objects: list[dict], verdict, demote_off_part: bool = False) -> set:
    """Objects with at least one NET class from any validator, any severity."""
    out = set()
    for obj in objects:
        for (val, class_id), _ in obj["classes"].items():
            if verdict(val, class_id, demote_off_part) == "NET":
                out.add(obj["sop_instance_uid"])
                break
    return out


# --- report -------------------------------------------------------------------
def build() -> dict:
    rows = load_message_classes()
    objects = load_objects()

    # message class -> (rule, severity, template, objects)
    per_class: dict[tuple[str, str], dict] = {}
    for r in rows:
        key = (r["validator"], r["message_class_id"])
        entry = per_class.setdefault(key, dict(
            validator=r["validator"], message_class_id=r["message_class_id"],
            severity_as_emitted=r["severity_as_emitted"],
            message_template=r["message_template"], objects=0,
            by_arid=Counter()))
        entry["objects"] += int(r["objects"])
        entry["by_arid"][_arid(r["analysis_result_id"])] += int(r["objects"])
    for entry in per_class.values():
        entry["rule"] = classify(entry["validator"], entry["message_template"])

    verdict_map = {k: v["rule"]["adjudication"] for k, v in per_class.items()}
    off_part = {k for k, v in per_class.items() if v["rule"]["name"] in OFF_PART_RULES}

    def verdict(validator: str, class_id: str, demote: bool) -> str:
        key = (validator, class_id)
        if demote and key in off_part:
            return "UNDECIDABLE"
        return verdict_map.get(key, "UNDECIDABLE")

    arids = sorted({o["analysis_result_id"] for o in objects})
    collections = sorted({o["collection_id"] for o in objects})
    validators = sorted({v for v, _ in per_class})

    triples: dict = {}
    for demote in (False, True):
        key = "demoted" if demote else "as_adjudicated"
        triples[key] = {}
        for validator in validators:
            for severity in ("ERROR", "WARNING"):
                triples[key].setdefault(validator, {})[severity] = dict(
                    overall=triple(objects, validator, severity, verdict, demote),
                    by_arid={a: triple([o for o in objects
                                        if o["analysis_result_id"] == a],
                                       validator, severity, verdict, demote)
                             for a in arids},
                )

    nets = net_objects(objects, verdict, False)
    nets_demoted = net_objects(objects, verdict, True)
    per_collection = {}
    for c in collections:
        sub = [o for o in objects if o["collection_id"] == c]
        per_collection[c] = dict(
            objects=len(sub),
            net=sum(1 for o in sub if o["sop_instance_uid"] in nets),
            net_demoted=sum(1 for o in sub if o["sop_instance_uid"] in nets_demoted),
            arids=sorted({o["analysis_result_id"] for o in sub}),
        )
        per_collection[c]["pct_net"] = pct(per_collection[c]["net"], len(sub))
        per_collection[c]["pct_net_demoted"] = pct(
            per_collection[c]["net_demoted"], len(sub))

    # Distinct objects per adjudication rule. Summing the per-class object
    # counts double counts an object that trips two classes of the same rule,
    # which the two evidence-sequence classes and the two Study Description
    # classes both do.
    per_rule_objects: dict[str, int] = {}
    for rule_name in {v["rule"]["name"] for v in per_class.values()}:
        keys = {k for k, v in per_class.items() if v["rule"]["name"] == rule_name}
        per_rule_objects[rule_name] = sum(
            1 for o in objects if keys & set(o["classes"]))

    per_arid_union = {}
    for a in arids:
        sub = [o for o in objects if o["analysis_result_id"] == a]
        n = sum(1 for o in sub if o["sop_instance_uid"] in nets)
        per_arid_union[a] = dict(objects=len(sub), net=n, pct_net=pct(n, len(sub)))

    median_collection_net = statistics.median(
        [per_collection[c]["pct_net"] for c in collections])
    median_collection_net_demoted = statistics.median(
        [per_collection[c]["pct_net_demoted"] for c in collections])

    return dict(
        per_class=per_class, objects=objects, arids=arids,
        collections=collections, validators=validators, triples=triples,
        union_net=len(nets), union_net_pct=pct(len(nets), len(objects)),
        union_net_demoted=len(nets_demoted),
        union_net_demoted_pct=pct(len(nets_demoted), len(objects)),
        per_collection=per_collection, per_arid_union=per_arid_union,
        per_rule_objects=per_rule_objects,
        median_collection_net=median_collection_net,
        median_collection_net_demoted=median_collection_net_demoted,
        n_objects=len(objects),
        n_series=len({o["series_instance_uid"] for o in objects}),
        off_part=sorted(off_part),
    )


def write_csv(rep: dict) -> Path:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fields = ["validator", "message_class_id", "message_template",
              "severity_as_emitted", "objects", "adjudication",
              "citation_section", "citation_table", "citation_quote", "rationale"]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for key in sorted(rep["per_class"],
                          key=lambda k: (k[0], -rep["per_class"][k]["objects"], k[1])):
            e = rep["per_class"][key]
            rule = e["rule"]
            w.writerow(dict(
                validator=e["validator"], message_class_id=e["message_class_id"],
                message_template=e["message_template"],
                severity_as_emitted=e["severity_as_emitted"], objects=e["objects"],
                adjudication=rule["adjudication"],
                citation_section=rule["section"], citation_table=rule["table"],
                citation_quote=rule["quote"], rationale=rule["rationale"]))
    return OUT_CSV


def _compact(template: str, limit: int = 170) -> str:
    """Shorten a template for a table cell without losing the diagnostic.

    dicom-validator prefixes a message with one `(TAG) (Content Sequence) /`
    per level of nesting, which for these reports runs to six or eight levels
    and pushes the part that identifies the finding past any sane column width.
    The run is collapsed and the depth is stated instead.
    """
    seg = "(TAG) (Content Sequence) / "
    n = template.count(seg)
    if n > 1:
        template = template.replace(seg * n, "[Content Sequence x%d] / " % n)
    template = template.replace("|", "\\|")
    return template if len(template) <= limit else template[:limit - 3] + "..."


def _triple_row(label: str, t: dict) -> str:
    return "| %s | %s | %s (%.2f) | %s (%.2f) | %s (%.2f) | %s |" % (
        label, f"{t['objects']:,}", f"{t['gross']:,}", t["pct_gross"],
        f"{t['floor']:,}", t["pct_floor"], f"{t['net']:,}", t["pct_net"],
        f"{t['other']:,}")


def write_markdown(rep: dict) -> Path:
    n = rep["n_objects"]
    L: list[str] = []
    L.append("# Comprehensive SR Storage: adjudicated error and warning rates")
    L.append("")
    L.append("Generated by `%s`. Standard edition %s, verified %s."
             % (CMD, EDITION, VERIFIED_ON))
    L.append("")
    L.append("Census, not a sample: %s objects in %s series, every object in the "
             "IDC v24 manifest for this SOP class. Nothing was sampled, truncated "
             "or skipped. Every one of the %d distinct (validator, "
             "message_class_id) pairs recorded for this class is adjudicated in "
             "`adjudication_comprehensive_sr.csv`."
             % (f"{n:,}", f"{rep['n_series']:,}", len(rep["per_class"])))
    L.append("")
    L.append("Definitions, fixed before the numbers:")
    L.append("")
    L.append("- **gross** objects carrying at least one message class of that "
             "severity from that validator")
    L.append("- **floor** of those, the ones whose classes are all FLOOR, NOT-IOD "
             "or PLAUSIBILITY")
    L.append("- **net** objects carrying at least one class adjudicated NET")
    L.append("- **other** no NET class, but at least one UNDECIDABLE, so neither "
             "floor nor net. Carried as its own column so it is not folded into "
             "either and quietly counted.")
    L.append("")
    L.append("Counts are objects, not messages: an object counts once for a class.")
    L.append("")

    L.append("## Triples by validator and severity")
    L.append("")
    for validator in rep["validators"]:
        for severity in ("ERROR", "WARNING"):
            t = rep["triples"]["as_adjudicated"][validator][severity]
            if t["overall"]["gross"] == 0:
                L.append("`%s` emitted no %s class on this SOP class."
                         % (validator, severity.lower()))
                L.append("")
                continue
            L.append("### %s, %s" % (validator, severity.lower()))
            L.append("")
            L.append("| group | objects | gross (pct) | floor (pct) | net (pct) | other |")
            L.append("|---|---|---|---|---|---|")
            L.append(_triple_row("all", t["overall"]))
            for a in rep["arids"]:
                L.append(_triple_row(a, t["by_arid"][a]))
            L.append("")

    L.append("## Residual NET classes")
    L.append("")
    L.append("Enumerated by rule, because 430 of the 478 message classes are NET and "
             "424 of those are one defect seen once per distinct numeric value. The "
             "objects column counts distinct objects, so a rule whose classes overlap "
             "on the same object is not double counted.")
    L.append("")
    L.append("| rule | validator | message classes | distinct objects | severity | "
             "representative template | citation |")
    L.append("|---|---|---|---|---|---|---|")
    net_rows = [(k, e) for k, e in rep["per_class"].items()
                if e["rule"]["adjudication"] == "NET"]
    grouped: dict[str, list] = defaultdict(list)
    for k, e in net_rows:
        grouped[e["rule"]["name"]].append((k, e))
    for name in sorted(grouped, key=lambda x: -rep["per_rule_objects"][x]):
        members = sorted(grouped[name], key=lambda kv: -kv[1]["objects"])
        _, head = members[0]
        cite = "%s; %s" % (head["rule"]["section"], head["rule"]["table"])
        L.append("| %s | %s | %d (e.g. `%s`) | %s | %s | %s | %s |" % (
            name, head["validator"], len(members), head["message_class_id"],
            f"{rep['per_rule_objects'][name]:,}", head["severity_as_emitted"],
            _compact(head["message_template"]), cite))
    L.append("")
    L.append("The floor column is zero for `dciodvfy` errors because no `dciodvfy` "
             "error class in this SOP class was adjudicated FLOOR, NOT-IOD or "
             "PLAUSIBILITY. That is a measured zero, not a missing measurement. The "
             "Phase 1 floor sets are writer-specific and fixture-specific and are not "
             "carried across to these writers, so no floor is subtracted from any "
             "rate above beyond the adjudication itself.")
    L.append("")

    L.append("## Two classes the census leaned on, and what the standard says")
    L.append("")
    L.append("**Referenced Frame Number (0008,1160), 722 objects, NET.** PS3.3 Table "
             "C.18.4-1 makes it Type 1C with the condition, verbatim: \"Required if "
             "the Referenced SOP Instance is a Multi-frame Image and the reference "
             "does not apply to all Frames, and Referenced Segment Number "
             "(0062,000B) is not present.\" PS3.5 Section 7.4.2 says, verbatim: "
             "\"When the specified conditions are not met, Type 1C Data Elements "
             "shall not be included in the Data Set unless it is specified that they "
             "may be present otherwise.\" Table C.18.4-1 grants no such allowance for "
             "this attribute, and the standard uses the phrase \"May be present "
             "otherwise\" elsewhere in this same IOD, on (0040,A375) in Table C.17-2, "
             "where it means it. The macro reaches these objects through Table C.17-4 "
             "and Table C.17-5, whose row reads \"Include Table C.18.4-1 Image "
             "Reference Macro Attributes if and only if Value Type (0040,A040) is "
             "IMAGE.\"")
    L.append("")
    L.append("**The second tool is not a second opinion here.** `dicom-validator` "
             "names the same attribute on the same 722 objects, and that agreement "
             "does not survive inspection. Its message is `is unexpected`, which "
             "version 0.8.2 documents as `ErrorCode.TagUnexpected`, \"Tag is not in "
             "any allowed module\". A failed condition is a different code, "
             "`ErrorCode.TagNotAllowed`, rendered as `is not allowed by condition` "
             "with the condition printed. Reading its parsed 2026c model back shows "
             "why: it holds (0008,1160), (0062,000B), the nested (0008,1199), "
             "(0008,114B) and (0088,0200) as siblings of the Referenced SOP Sequence "
             "that Table C.18.4-1 includes from Table C.18.3-1, rather than as the "
             "children the \">\" prefixes make them, so inside that Sequence it "
             "expects Table 10-11 and nothing else. The same gap makes it flag the "
             "nested Referenced SOP Sequence, a Type 3 row of Table C.18.4-1, on 826 "
             "objects. Both `dicom-validator` classes are therefore FLOOR, and the "
             "Referenced Frame Number finding rests on `dciodvfy` and the citation "
             "alone.")
    L.append("")
    L.append("**CodingSchemeDesignator SRT, 2,118 of 2,118 objects, FLOOR.** PS3.16 "
             "Table 8-1 still carries the SRT row in the pinned edition, and its Note "
             "reads, verbatim: \"This Coding Scheme is deprecated. The use of "
             "'SNOMED-RT style' Code Values is no longer authorized by SNOMED except "
             "for creation by legacy devices, legacy objects in archives, and "
             "receiving systems that need to understand them.\" PS3.16 Section 8.1 "
             "puts the resulting obligation on the receiver, verbatim: \"It is the "
             "responsibility of such Application Entities to convert any alphanumeric "
             "SnomedID with Coding Scheme Designator 'SRT' used in old DICOM objects "
             "and services to the corresponding numeric ConceptID code\", and PS3.16 "
             "Annex O exists so that they can. No requirement on the stored object "
             "was found in PS3.3 Section 8.2, PS3.16 Section 8 or PS3.16 Section 8.1. "
             "The message is emitted at Warning severity and is worded as a "
             "deprecation, not a prohibition. It changes no error triple.")
    L.append("")

    L.append("## Net rate across validators, by analysis result and by collection")
    L.append("")
    L.append("An object is net here if any validator raised any class adjudicated "
             "NET, at any severity. This is the number PRE-05 is evaluated against.")
    L.append("")
    L.append("| analysis_result_id | objects | net | pct net |")
    L.append("|---|---|---|---|")
    for a in rep["arids"]:
        d = rep["per_arid_union"][a]
        L.append("| %s | %s | %s | %.2f |" % (a, f"{d['objects']:,}",
                                              f"{d['net']:,}", d["pct_net"]))
    L.append("| **all** | %s | %s | %.2f |" % (f"{rep['n_objects']:,}",
                                               f"{rep['union_net']:,}",
                                               rep["union_net_pct"]))
    L.append("")
    L.append("| collection_id | analysis results present | objects | net | pct net |")
    L.append("|---|---|---|---|---|")
    for c in rep["collections"]:
        d = rep["per_collection"][c]
        L.append("| %s | %s | %s | %s | %.2f |" % (
            c, ", ".join(d["arids"]), f"{d['objects']:,}", f"{d['net']:,}",
            d["pct_net"]))
    L.append("")
    L.append("Collection-level median net rate: **%.2f percent** across %d "
             "collections." % (rep["median_collection_net"], len(rep["collections"])))
    L.append("")

    L.append("## PRE-05")
    L.append("")
    L.append("PRE-05, pre-registered before any archive object was validated, reads: "
             "\"null is defined as a post-floor failure rate at or below 5 percent of "
             "series in a class; substantial is defined as above 20 percent; the band "
             "between is reported as indeterminate and neither claim is made\". This "
             "class has one object per series, %s and %s, so the object rate and the "
             "series rate are the same number."
             % (f"{rep['n_objects']:,} objects", f"{rep['n_series']:,} series"))
    L.append("")
    L.append("Both required numbers, reported whether or not either passes:")
    L.append("")
    L.append("| number | value | threshold | clears |")
    L.append("|---|---|---|---|")
    L.append("| net error-class rate, this SOP class | %.2f percent (%s of %s) | "
             "above 5.0 percent | %s |"
             % (rep["union_net_pct"], f"{rep['union_net']:,}",
                f"{rep['n_objects']:,}",
                "yes" if rep["union_net_pct"] > 5.0 else "no"))
    L.append("| collection-level median net rate | %.2f percent (median of %d "
             "collections) | above 5.0 percent | %s |"
             % (rep["median_collection_net"], len(rep["collections"]),
                "yes" if rep["median_collection_net"] > 5.0 else "no"))
    substantial = (rep["union_net_pct"] > 5.0
                   and rep["median_collection_net"] > 5.0)
    L.append("")
    L.append("Conjunction required by the Track C evaluation rule, substantial if and "
             "only if both are above 5.0 percent: **%s**."
             % ("substantial" if substantial else "not substantial"))
    L.append("")
    L.append("Against PRE-05's own three bands, applied to the class-level rate on "
             "its own, the %.2f percent net rate falls in the **%s** band. The two "
             "tests disagree, and the disagreement is the finding rather than a "
             "problem with either test."
             % (rep["union_net_pct"],
                "substantial, above 20 percent" if rep["union_net_pct"] > 20.0
                else ("indeterminate, above 5 and at or below 20 percent"
                      if rep["union_net_pct"] > 5.0
                      else "null, at or below 5 percent")))
    L.append("")
    L.append("Why they disagree, stated so a reader does not have to reconstruct it: "
             "the net objects are not spread across the class. They sit in three of "
             "seven collections, and those three carry two of the three producer "
             "groups. The four collections holding `dicom_sr_breast_clinical`, "
             "1,292 of the 2,118 objects, carry one net object between them. A "
             "class-level rate of %.2f percent and a median collection rate of %.2f "
             "percent are both correct descriptions of the same data, and the "
             "collection-level gate is the one that refuses to let two producers "
             "stand in for a class. That is the non-independence the ledger already "
             "carries as C3-12."
             % (rep["union_net_pct"], rep["median_collection_net"]))
    L.append("")
    L.append("Consequence for PRE-01, recorded explicitly so its absence is not read "
             "as an oversight: this class does **not** clear PRE-05 under the "
             "conjunction, so PRE-01's prediction of a largely null claim 1 is **not** "
             "recorded as wrong on this evidence. It is also not confirmed. One SOP "
             "class in which two of three producer groups fail a Type 1C condition at "
             "71 and 100 percent, while the third is clean, is not a null result and "
             "not a substantial one either.")
    L.append("")
    L.append("PRE-05 is per object class and three of the eight classes in Phase 2 "
             "are not yet complete, so the row itself is not closed by this class "
             "alone. The verdict recorded here is the Comprehensive SR Storage limb "
             "of it.")
    L.append("")

    L.append("## Sensitivity: off-part citations")
    L.append("")
    L.append("The rubric scopes NET citations to PS3.3, PS3.4 and PS3.16. Three "
             "rules cite PS3.5 Table 6.2-1 or PS3.6 Table 6-1 instead, because a "
             "VR length overflow and a dictionary VM breach are stated there and "
             "nowhere in the IOD parts. Those classes are reported as NET and the "
             "whole calculation is repeated with them demoted to UNDECIDABLE, so a "
             "reader applying the rubric strictly does not have to recompute "
             "anything.")
    L.append("")
    L.append("| number | as adjudicated | off-part classes demoted |")
    L.append("|---|---|---|")
    L.append("| net objects, any validator | %s (%.2f pct) | %s (%.2f pct) |" % (
        f"{rep['union_net']:,}", rep["union_net_pct"],
        f"{rep['union_net_demoted']:,}", rep["union_net_demoted_pct"]))
    for validator in rep["validators"]:
        a = rep["triples"]["as_adjudicated"][validator]["ERROR"]["overall"]
        b = rep["triples"]["demoted"][validator]["ERROR"]["overall"]
        L.append("| %s error net | %s (%.2f pct) | %s (%.2f pct) |" % (
            validator, f"{a['net']:,}", a["pct_net"], f"{b['net']:,}", b["pct_net"]))
    L.append("| collection-level median net rate | %.2f pct | %.2f pct |" % (
        rep["median_collection_net"], rep["median_collection_net_demoted"]))
    L.append("")
    L.append("The %d off-part message classes, by rule:" % len(rep["off_part"]))
    L.append("")
    for name in sorted(OFF_PART_RULES):
        members = [k for k, v in rep["per_class"].items()
                   if v["rule"]["name"] == name]
        if not members:
            continue
        count = rep["per_rule_objects"][name]
        L.append("- **%s**: %d message class%s, %s distinct object%s"
                 % (name, len(members), "" if len(members) == 1 else "es",
                    f"{count:,}", "" if count == 1 else "s"))
    L.append("")

    L.append("## What was dropped")
    L.append("")
    L.append("Nothing. All %s objects the census recorded for this SOP class carry "
             "status OK, every distinct message class is adjudicated, and no message "
             "class was set aside as too rare to matter. The single object carrying "
             "the Study Description VM classes is adjudicated on the same terms as "
             "the 722." % f"{rep['n_objects']:,}")
    L.append("")
    L.append("Two corrections to the locators this track was given, recorded because "
             "citing them unchanged would have been wrong: the SR Document Content "
             "Module is Table C.17-4, not Table C.17-3, and Table C.17-3 in the "
             "pinned edition is the Hierarchical SOP Instance Reference Macro. "
             "`results/environment.json` records the standard edition as PS3 2025e "
             "while `results/standards.json` and the running dicom-validator both use "
             "2026c; every citation in this file is from 2026c and the disagreement "
             "in the environment record is reported, not repaired here.")
    L.append("")
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(L) + "\n", encoding="utf-8")
    return OUT_MD


# --- proposed ledger rows -----------------------------------------------------
# PRE-05 and PRE-01 are reproduced verbatim from results/ledger.csv. Only the
# fields named in `fields_changed` differ from the row already in the ledger.
PRE05_CLAIM = ("Claim 1 threshold, set before the data. PRE-01 predicted a largely "
               "null result without a number. The number is fixed here, per object "
               "class, above floor.")
PRE05_VALUE = ("null is defined as a post-floor failure rate at or below 5 percent "
               "of series in a class; substantial is defined as above 20 percent; "
               "the band between is reported as indeterminate and neither claim is "
               "made")
PRE05_STATUS_NOTE = ("Chosen before any archive object was validated so the data can "
                     "disagree with it. The floor from Phase 1 is subtracted before "
                     "the threshold is applied.")
PRE01_CLAIM = ("Pre-registered prediction. Claim 1 will return largely null: SR will "
               "pass cleanly because IDC validates its own SR with PixelMed, and SEG "
               "will pass cleanly because dcmqi wrote it. That is the control that "
               "makes claim 3 land, not a failure of the study.")


def ledger_entries(rep: dict) -> list[dict]:
    n = rep["n_objects"]
    dv = rep["triples"]["as_adjudicated"]
    dciod_e = dv["dciodvfy"]["ERROR"]["overall"]
    dciod_w = dv["dciodvfy"]["WARNING"]["overall"]
    dvv_e = dv["dicom-validator"]["ERROR"]["overall"]
    src = "results/phase2/adjudication_comprehensive_sr.csv and " \
          "results/phase2/net_rates_comprehensive_sr.md"
    common = dict(section="C-CSR", section_title="Track C, Comprehensive SR Storage "
                  "adjudication", sop_class=SOP_CLASS, idc_index_version="v24")
    measured = dict(command=CMD, source_file=src,
                    dropped="nothing: census of all %s objects in the IDC v24 "
                            "manifest for this SOP class, every distinct message "
                            "class adjudicated, none skipped" % f"{n:,}", **common)
    verified = dict(external_source="DICOM %s, dicom.nema.org" % EDITION,
                    verified_on=VERIFIED_ON, source_file=src, **common)

    entries: list[dict] = []

    entries.append(dict(
        id="C-CSR-01", status="VERIFIED",
        claim="Referenced Frame Number (0008,1160) present in an SR IMAGE Content "
              "Item whose Referenced SOP Class is not multi-frame is a genuine "
              "conformance defect, not a validator artefact.",
        value="PS3.3 Table C.18.4-1 makes (0008,1160) Type 1C, condition verbatim: "
              "Required if the Referenced SOP Instance is a Multi-frame Image and "
              "the reference does not apply to all Frames, and Referenced Segment "
              "Number (0062,000B) is not present. PS3.5 Section 7.4.2 verbatim: When "
              "the specified conditions are not met, Type 1C Data Elements shall not "
              "be included in the Data Set unless it is specified that they may be "
              "present otherwise. Table C.18.4-1 states no such allowance for this "
              "attribute.",
        n="722", denominator=str(n),
        floor="not applicable, this row is the citation rather than a rate",
        validator="dciodvfy",
        validator_version="dicom3tools snapshot 20260701065818, sha256 d931cded1048a2fd",
        status_note="The macro reaches these objects through Table C.17-4 SR Document "
                    "Content Module and Table C.17-5 Document Content Macro, whose "
                    "row reads: Include Table C.18.4-1 Image Reference Macro "
                    "Attributes if and only if Value Type (0040,A040) is IMAGE. Two "
                    "residuals recorded and not resolved: the condition is written on "
                    "the Referenced SOP Instance while dciodvfy evaluates it from the "
                    "Referenced SOP Class UID, and no PS3.16 template text permitting "
                    "the attribute for a single-frame reference was found.",
        notes="The locator supplied to this track, PS3.3 C.17.3 and Table C.17-3, is "
              "wrong for the pinned edition. The SR Document Content Module is Table "
              "C.17-4 and Table C.17-3 is the Hierarchical SOP Instance Reference "
              "Macro.",
        **verified))

    entries.append(dict(
        id="C-CSR-02", status="VERIFIED",
        claim="dicom-validator does not independently confirm the Referenced Frame "
              "Number defect. Its message on those objects is a modelling artefact "
              "and is adjudicated FLOOR.",
        value="dicom-validator 0.8.2 emits is unexpected for ErrorCode.TagUnexpected, "
              "documented in its own source as Tag is not in any allowed module. A "
              "failed condition is ErrorCode.TagNotAllowed and renders as is not "
              "allowed by condition. Its parsed 2026c model of Table C.18.4-1 holds "
              "(0008,1160), (0062,000B), the nested (0008,1199), (0008,114B) and "
              "(0088,0200) as siblings of the included Referenced SOP Sequence rather "
              "than as its children, so inside that Sequence it expects only Table "
              "10-11.",
        n="722", denominator=str(n),
        floor="not applicable, this row characterises an instrument",
        validator="dicom-validator", validator_version="dicom-validator 0.8.2, "
                                                       "edition 2026c",
        status_note="Demonstrated by the same validator flagging the nested "
                    "Referenced SOP Sequence, a Type 3 row of Table C.18.4-1, as "
                    "unexpected on 826 objects. No condition exists on a Type 3 "
                    "attribute that could have failed.",
        notes="Consequence for the manuscript: the Referenced Frame Number finding "
              "must be reported as a single-tool finding with a citation, not as two "
              "independent tools agreeing.",
        **verified))

    entries.append(dict(
        id="C-CSR-03", status="VERIFIED",
        claim="Coding Scheme Designator SRT is a deprecation notice with no "
              "requirement behind it, and is adjudicated FLOOR.",
        value="PS3.16 Table 8-1 still lists SRT in the pinned edition. Its Note "
              "verbatim: This Coding Scheme is deprecated. The use of SNOMED-RT style "
              "Code Values is no longer authorized by SNOMED except for creation by "
              "legacy devices, legacy objects in archives, and receiving systems that "
              "need to understand them. PS3.16 Section 8.1 verbatim: It is the "
              "responsibility of such Application Entities to convert any "
              "alphanumeric SnomedID with Coding Scheme Designator SRT used in old "
              "DICOM objects and services to the corresponding numeric ConceptID "
              "code.",
        n=str(n), denominator=str(n),
        floor="not applicable, this row is the citation rather than a rate",
        validator="dciodvfy",
        validator_version="dicom3tools snapshot 20260701065818, sha256 d931cded1048a2fd",
        status_note="Emitted at Warning severity on 2,118 of 2,118 objects, so it "
                    "affects no error triple. No prohibition on a stored object was "
                    "found in PS3.3 Section 8.2, PS3.16 Section 8 or PS3.16 Section "
                    "8.1, and PS3.16 Annex O exists so receivers can map the legacy "
                    "codes.",
        **verified))

    entries.append(dict(
        id="C-CSR-04", status="VERIFIED",
        claim="Referenced SOP Instances that appear in the SR Content Tree but in "
              "neither evidence Sequence violate a stated requirement.",
        value="PS3.3 Section C.17.2.3 verbatim: This shall include, but is not "
              "limited to, all current evidence referenced in the Content Tree. And: "
              "the set of Composite SOP Instances is defined to include not only the "
              "images and waveforms referenced in the Content Tree, but also all "
              "presentation states, Real World Value maps and other accompanying "
              "Composite Instances that are referenced from the Content Items. "
              "Current Requested Procedure Evidence Sequence (0040,A375) is Type 1C "
              "in Table C.17-2.",
        n="462", denominator=str(n),
        floor="not applicable, this row is the citation rather than a rate",
        validator="dciodvfy",
        validator_version="dicom3tools snapshot 20260701065818, sha256 d931cded1048a2fd",
        status_note="Two dciodvfy message classes, one naming an image reference and "
                    "one naming a presentation state reached from an IMAGE Content "
                    "Item, both on the same 462 objects of the unlabelled group. The "
                    "third quoted sentence covers the presentation state limb "
                    "explicitly.",
        **verified))

    entries.append(dict(
        id="C-CSR-05", status="MEASURED",
        claim="dciodvfy error triple for Comprehensive SR Storage, after "
              "adjudication.",
        value="gross %s of %s objects (%.2f percent), floor %s (%.2f percent), net %s "
              "(%.2f percent), other %s"
              % (f"{dciod_e['gross']:,}", f"{n:,}", dciod_e["pct_gross"],
                 f"{dciod_e['floor']:,}", dciod_e["pct_floor"],
                 f"{dciod_e['net']:,}", dciod_e["pct_net"], f"{dciod_e['other']:,}"),
        n=str(dciod_e["net"]), denominator=str(n),
        floor="%s objects (%.2f percent) carry only FLOOR, NOT-IOD or PLAUSIBILITY "
              "error classes" % (f"{dciod_e['floor']:,}", dciod_e["pct_floor"]),
        validator="dciodvfy",
        validator_version="dicom3tools snapshot 20260701065818, sha256 d931cded1048a2fd",
        status_note="other counts objects with no NET class but at least one "
                    "UNDECIDABLE class, so they are neither floor nor net and are "
                    "not folded into either.",
        derived_from="C-CSR-01,C-CSR-04", **measured))

    entries.append(dict(
        id="C-CSR-06", status="MEASURED",
        claim="dicom-validator error triple for Comprehensive SR Storage, after "
              "adjudication.",
        value="gross %s of %s objects (%.2f percent), floor %s (%.2f percent), net %s "
              "(%.2f percent), other %s"
              % (f"{dvv_e['gross']:,}", f"{n:,}", dvv_e["pct_gross"],
                 f"{dvv_e['floor']:,}", dvv_e["pct_floor"],
                 f"{dvv_e['net']:,}", dvv_e["pct_net"], f"{dvv_e['other']:,}"),
        n=str(dvv_e["net"]), denominator=str(n),
        floor="%s objects (%.2f percent) carry only FLOOR, NOT-IOD or PLAUSIBILITY "
              "error classes" % (f"{dvv_e['floor']:,}", dvv_e["pct_floor"]),
        validator="dicom-validator",
        validator_version="dicom-validator 0.8.2, edition 2026c",
        status_note="Nearly the whole gross is floor, and it is one modelling gap: "
                    "the flattening of the four nested rows of Table C.18.4-1. The "
                    "residual net is the DS length overflow, which is cited to PS3.5 "
                    "rather than PS3.3 and is reported demoted as well.",
        derived_from="C-CSR-02", **measured))

    entries.append(dict(
        id="C-CSR-07", status="MEASURED",
        claim="dciodvfy warning triple for Comprehensive SR Storage, after "
              "adjudication.",
        value="gross %s of %s objects (%.2f percent), floor %s (%.2f percent), net %s "
              "(%.2f percent), other %s"
              % (f"{dciod_w['gross']:,}", f"{n:,}", dciod_w["pct_gross"],
                 f"{dciod_w['floor']:,}", dciod_w["pct_floor"],
                 f"{dciod_w['net']:,}", dciod_w["pct_net"], f"{dciod_w['other']:,}"),
        n=str(dciod_w["net"]), denominator=str(n),
        floor="%s objects (%.2f percent) carry only FLOOR, NOT-IOD or PLAUSIBILITY "
              "warning classes" % (f"{dciod_w['floor']:,}", dciod_w["pct_floor"]),
        validator="dciodvfy",
        validator_version="dicom3tools snapshot 20260701065818, sha256 d931cded1048a2fd",
        status_note="No warning class in this SOP class is adjudicated NET. The "
                    "100 percent gross warning rate reported in the Phase 2 census "
                    "is entirely SRT, DICOMDIR and Retired Person Name form, plus "
                    "one UNDECIDABLE coding scheme designator class.",
        derived_from="C-CSR-03", **measured))

    entries.append(dict(
        id="C-CSR-08", status="MEASURED",
        claim="Net rate across both validators for Comprehensive SR Storage, by "
              "analysis result.",
        value="; ".join("%s %s of %s (%.2f percent)"
                        % (a, f"{rep['per_arid_union'][a]['net']:,}",
                           f"{rep['per_arid_union'][a]['objects']:,}",
                           rep["per_arid_union"][a]["pct_net"])
                        for a in rep["arids"])
              + "; all %s of %s (%.2f percent)" % (f"{rep['union_net']:,}", f"{n:,}",
                                                   rep["union_net_pct"]),
        n=str(rep["union_net"]), denominator=str(n),
        floor="reported per validator in C-CSR-05, C-CSR-06 and C-CSR-07; no "
              "single scalar floor is quoted for the union",
        validator="dciodvfy and dicom-validator",
        validator_version="dicom3tools snapshot 20260701065818; dicom-validator "
                          "0.8.2, edition 2026c",
        status_note="Aggregated by analysis result, not ranked. The three groups have "
                    "different producers and the differences are reported as "
                    "structure in the data, not as a league table.",
        derived_from="C-CSR-05,C-CSR-06", **measured))

    entries.append(dict(
        id="C-CSR-09", status="MEASURED",
        claim="Collection-level net rates for Comprehensive SR Storage, and their "
              "median.",
        value="median %.2f percent across %d collections: %s"
              % (rep["median_collection_net"], len(rep["collections"]),
                 "; ".join("%s %.2f percent (%s of %s)"
                           % (c, rep["per_collection"][c]["pct_net"],
                              f"{rep['per_collection'][c]['net']:,}",
                              f"{rep['per_collection'][c]['objects']:,}")
                           for c in rep["collections"])),
        n=str(rep["union_net"]), denominator=str(n),
        floor="reported per validator in C-CSR-05, C-CSR-06 and C-CSR-07",
        validator="dciodvfy and dicom-validator",
        validator_version="dicom3tools snapshot 20260701065818; dicom-validator "
                          "0.8.2, edition 2026c",
        status_note="Collection is read from _cache/census/records.jsonl, which was "
                    "opened read only. Objects and series are one to one in this "
                    "class, so the object rate and the series rate coincide.",
        derived_from="C-CSR-08", **measured))

    entries.append(dict(
        id="C-CSR-10", status="MEASURED",
        claim="Three NET rules in this class cite PS3.5 or PS3.6 rather than PS3.3, "
              "PS3.4 or PS3.16, so every triple is also reported with them demoted "
              "to UNDECIDABLE.",
        value="as adjudicated, net %s of %s (%.2f percent); with the off-part classes "
              "demoted, net %s of %s (%.2f percent). Collection-level median %.2f "
              "percent as adjudicated, %.2f percent demoted."
              % (f"{rep['union_net']:,}", f"{n:,}", rep["union_net_pct"],
                 f"{rep['union_net_demoted']:,}", f"{n:,}",
                 rep["union_net_demoted_pct"], rep["median_collection_net"],
                 rep["median_collection_net_demoted"]),
        n=str(rep["union_net_demoted"]), denominator=str(n),
        floor="see C-CSR-05 and C-CSR-06",
        validator="dciodvfy and dicom-validator",
        validator_version="dicom3tools snapshot 20260701065818; dicom-validator "
                          "0.8.2, edition 2026c",
        status_note="The three rules are the DS 16 byte maximum in PS3.5 Table 6.2-1, "
                    "dciodvfy's roll-up of it, and the Study Description VM 1 in "
                    "PS3.6 Table 6-1. Both numbers are published so a reader applying "
                    "the rubric's citation scope strictly does not have to recompute.",
        derived_from="C-CSR-05,C-CSR-06,C-CSR-08", **measured))

    substantial = (rep["union_net_pct"] > 5.0 and rep["median_collection_net"] > 5.0)
    entries.append(dict(
        id="PRE-05", status="PENDING", claim=PRE05_CLAIM, value=PRE05_VALUE,
        section="V", section_title="Panel design, fixed before Phase 1",
        sop_class="per class",
        floor="not applicable, this row defines the instrument rather than quoting a "
              "rate",
        dropped="nothing, the full panel is enumerated including tools considered and "
                "excluded",
        command="python -m colophon.validate", source_file="results/panel.json",
        derived_from="PRE-01", idc_index_version="v24",
        status_note=PRE05_STATUS_NOTE + " Comprehensive SR Storage limb evaluated "
                    "%s by %s: net error-class rate %.2f percent, %s 5.0 percent; "
                    "collection-level median net rate %.2f percent, %s 5.0 percent. "
                    "The conjunction required by the Track C evaluation rule is "
                    "therefore %s, so this class is %s. Status stays PENDING because "
                    "PRE-05 is per object class and three of the eight Phase 2 "
                    "classes are not complete."
                    % (VERIFIED_ON, CMD, rep["union_net_pct"],
                       "above" if rep["union_net_pct"] > 5.0 else "at or below",
                       rep["median_collection_net"],
                       "above" if rep["median_collection_net"] > 5.0
                       else "at or below",
                       "met" if substantial else "not met",
                       "substantial" if substantial else "not substantial"),
        notes="Both numbers, reported whether or not either passes: net error-class "
              "rate %.2f percent (%s of %s objects, one object per series); "
              "collection-level median net rate %.2f percent across %d collections. "
              "Applied on its own to the class-level rate, PRE-05's own bands put the "
              "class above 20 percent and therefore in the substantial band; the "
              "collection-level gate does not, because the net objects sit in three "
              "of seven collections and 1,292 objects from one producer group carry "
              "one net object between them. With the three off-part NET rules demoted "
              "to UNDECIDABLE the numbers are %.2f percent and %.2f percent, which "
              "changes neither verdict. Evidence: %s."
              % (rep["union_net_pct"], f"{rep['union_net']:,}", f"{n:,}",
                 rep["median_collection_net"], len(rep["collections"]),
                 rep["union_net_demoted_pct"], rep["median_collection_net_demoted"],
                 src),
        fields_changed=["status_note", "notes"]))

    if substantial:
        entries.append(dict(
            id="PRE-01", status="RETIRED", claim=PRE01_CLAIM,
            section="PRE", section_title="Pre-registered interpretation",
            value="predicted before any archive object was validated",
            sop_class="all",
            floor="to be established in Phase 1, per SOP class",
            dropped="nothing, this is a prediction over the full Phase 2 and 3 "
                    "population",
            command="python -m colophon.validate", source_file="results/panel.json",
            idc_index_version="v24",
            retired_reason="Wrong on the SR limb, by measurement. PRE-01 predicted "
                           "that SR would pass cleanly because IDC validates its own "
                           "SR with PixelMed. The Comprehensive SR Storage census is "
                           "complete at %s objects and %.2f percent of them carry at "
                           "least one message class adjudicated NET against a quoted "
                           "PS3.3 section and table, with a collection-level median "
                           "net rate of %.2f percent across %d collections. That is "
                           "above PRE-05's substantial threshold of 20 percent, not "
                           "in the null band. The largest single defect is a "
                           "population-scale Type 1C violation: Referenced Frame "
                           "Number (0008,1160) present on references to non "
                           "multi-frame SOP Classes in 722 objects, against PS3.3 "
                           "Table C.18.4-1 and PS3.5 Section 7.4.2. The prediction is "
                           "recorded as wrong rather than reworded."
                           % (f"{n:,}", rep["union_net_pct"],
                              rep["median_collection_net"], len(rep["collections"])),
            status_note="Scope of the falsification, stated exactly and neither "
                        "widened nor narrowed: the SR limb is falsified by the "
                        "Comprehensive SR Storage census. The SEG limb is untested, "
                        "because Segmentation Storage is excluded from Phase 2 by "
                        "assertion. Comprehensive 3D SR, RT Structure Set and "
                        "Enhanced SR are not complete. This row is retired on the "
                        "evidence that exists, not on the evidence that does not.",
            notes="PRE-01's own text anticipated this: if instead claim 1 returns a "
                  "substantial failure rate, this row is wrong and stays in the "
                  "ledger as a wrong prediction. It stays. Evidence: %s." % src,
            superseded_by="C-CSR-08",
            fields_changed=["status", "retired_reason", "status_note", "notes",
                            "superseded_by"]))
    else:
        entries.append(dict(
            id="C-CSR-11", status="DERIVED",
            claim="PRE-01 is not recorded as a wrong prediction on the evidence of "
                  "this SOP class, and is not confirmed by it either.",
            value="Comprehensive SR Storage does not clear PRE-05 under the "
                  "conjunction: net error-class rate %.2f percent, above 5.0 percent, "
                  "but collection-level median net rate %.2f percent, at or below 5.0 "
                  "percent. The gate requires both."
                  % (rep["union_net_pct"], rep["median_collection_net"]),
            n=str(rep["union_net"]), denominator=str(n),
            floor="see C-CSR-05 and C-CSR-06",
            validator="dciodvfy and dicom-validator",
            validator_version="dicom3tools snapshot 20260701065818; dicom-validator "
                              "0.8.2, edition 2026c",
            status_note="Written so the absence of a wrong-prediction row is a "
                        "recorded decision rather than an omission. The class-level "
                        "rate on its own sits in PRE-05's substantial band, above 20 "
                        "percent; the collection-level median does not, because the "
                        "net objects sit in three of seven collections and the four "
                        "collections holding dicom_sr_breast_clinical, 1,292 of 2,118 "
                        "objects, carry one net object between them.",
            notes="This is not a null result for the class either. Two of the three "
                  "producer groups fail a Type 1C condition at 71.43 and 100.00 "
                  "percent. PRE-01's SR limb survives only because the third group is "
                  "clean and is the largest. Evidence: %s." % src,
            derived_from="C-CSR-08,C-CSR-09,PRE-05", **measured))

    return entries


def write_ledger(rep: dict) -> Path:
    entries = ledger_entries(rep)
    from . import ledger as ledger_mod
    allowed = set(ledger_mod.FIELDS) | {"fields_changed"}
    for e in entries:
        unknown = set(e) - allowed
        if unknown:
            raise ValueError("pending ledger row %s has unknown keys: %s"
                             % (e["id"], sorted(unknown)))
        if e["status"] not in ledger_mod.VALID_STATUS:
            raise ValueError("bad status on %s" % e["id"])
    OUT_LEDGER.parent.mkdir(parents=True, exist_ok=True)
    OUT_LEDGER.write_text(json.dumps(dict(
        track="C", sop_class=SOP_CLASS, generated_by=CMD,
        generated_on=VERIFIED_ON, standard_edition=EDITION,
        note="Proposed rows, not merged. Keys match colophon.ledger.FIELDS. Rows "
             "whose id already exists in results/ledger.csv carry fields_changed, "
             "which lists the only fields that differ from the row already there; "
             "every other field is reproduced verbatim and must not be edited on "
             "merge. fields_changed is metadata and is not a ledger field.",
        rows=entries), indent=1), encoding="utf-8")
    return OUT_LEDGER


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.parse_args(argv)
    rep = build()

    unmatched = [k for k, v in rep["per_class"].items()
                 if v["rule"]["name"] == "UNMATCHED"]
    print("message classes adjudicated: %d" % len(rep["per_class"]))
    counts = Counter(v["rule"]["adjudication"] for v in rep["per_class"].values())
    for k in sorted(counts):
        print("  %-13s %4d classes" % (k, counts[k]))
    if unmatched:
        print("UNMATCHED, left UNDECIDABLE: %d" % len(unmatched))
        for v, c in unmatched[:20]:
            print("   %s %s %s" % (v, c, rep["per_class"][(v, c)]["message_template"][:110]))

    print("\nobjects %s in %s series" % (f"{rep['n_objects']:,}", f"{rep['n_series']:,}"))
    for validator in rep["validators"]:
        for severity in ("ERROR", "WARNING"):
            t = rep["triples"]["as_adjudicated"][validator][severity]["overall"]
            print("  %-16s %-8s gross %5d  floor %5d  net %5d  other %5d"
                  % (validator, severity.lower(), t["gross"], t["floor"], t["net"],
                     t["other"]))
    print("  union net %d (%.2f pct), collection median %.2f pct"
          % (rep["union_net"], rep["union_net_pct"], rep["median_collection_net"]))

    print("\nwrote %s" % write_csv(rep))
    print("wrote %s" % write_markdown(rep))
    print("wrote %s" % write_ledger(rep))
    return 0


if __name__ == "__main__":
    sys.exit(main())
