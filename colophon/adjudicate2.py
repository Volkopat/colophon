"""Second adjudication pass, and the agreement between the two.

PRE-03 registers that where validators disagree the authors do not decide who is
right, and addendum 02 section 5 registers **two independent adjudicators, with
any disagreement staying undecidable**. The first pass used one adjudicator per
class. This module supplies the second and reports the agreement rather than
replacing the first.

**What this is, stated before any number.** The second pass was performed by the
same LLM agent that produced the first, under the ordered rule table published
below, after re-reading the message templates without the first pass's verdicts.
That makes it an **intra-instrument repeatability check, not an independent
human adjudication.** It establishes that the rule table is applied
reproducibly and it surfaces classes where the reading is unstable. It does not
establish that either reading is correct, and it cannot substitute for a second
human. Methods says exactly that.

**Blindness is partial and the compromise is quantified.** `MORNING_REPORT.md`
is part of the session's required reading and it discloses several first-pass
verdicts in prose: Laterality as floor, the Parametric Map `ImageType` defined
terms as floor, three Comprehensive 3D SR classes as net, and
`DisplayedAreaSelectionSequence` as plausibility. Families matching those are
flagged `PRE_DISCLOSED` and agreement is reported twice, over all families and
over the blind subset only. A blind figure that quietly included the disclosed
ones would overstate the check.

**The adjudication unit.** A message class id is too fine: 1,608 ids differ only
by the patient name embedded in the template. A message shape is too coarse: it
merges distinct attributes under one diagnostic. The unit here is the **family**,
the template with instance values collapsed and the attribute and module kept,
and every id inherits its family's verdict so no id is left unadjudicated.

Usage:
    python -m colophon.adjudicate2
"""
from __future__ import annotations

import glob
import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd

from .paths import REPO, RESULTS

CMD = "python -m colophon.adjudicate2"
OUT = RESULTS / "adjudication2"
PHASE2 = RESULTS / "phase2"

FLOOR = "FLOOR"
NET = "NET"
UNDECIDABLE = "UNDECIDABLE"

# Verdicts disclosed to this pass by MORNING_REPORT.md before it ran. Matched
# case-insensitively against the family text. Agreement on these is reported
# separately and is never counted as blind.
PRE_DISCLOSED = [
    "Laterality",
    "Image Type",
    "ClinicalTrialSiteName",
    "Clinical Trial Site Name",
    "DeidentificationMethod",
    "De-identification Method",
    "ReferencedSOPClassUID",
    "Referenced SOP Class UID",
    "DisplayedAreaSelectionSequence",
]


def family_of(template: str) -> str:
    """Collapse instance values, keep the attribute and module."""
    t = str(template)
    t = re.sub(r"PN \[\d+\] = <[^>]*>", "PN [n] = <VALUE>", t)
    t = re.sub(r"DS \[\d+\] = <[^>]*>", "DS [n] = <VALUE>", t)
    t = re.sub(r"= \(\d+,\d+\)", "= (X,Y)", t)
    t = re.sub(r"(\(TAG\) \(Content Sequence\) / )+",
               "(TAG) (Content Sequence) [xN] / ", t)
    t = re.sub(r"Length invalid for this VR = \d+, expected[^,]*",
               "Length invalid for this VR = N", t)
    return re.sub(r"\s+", " ", t).strip()


# --- the second adjudicator's rule table --------------------------------------
# Ordered, first match wins, matched as a regex against the family text.
# Every rule carries the verdict and the citation that licenses it. A family
# that matches no rule is UNDECIDABLE by construction rather than by omission,
# which is the direction the fence requires.
RULES: list[tuple[str, str, str, str, str]] = [
    # (pattern, verdict, section, table, rationale)
    (r"needed to build DICOMDIR", FLOOR, "PS3.3 C.7.2.1", "Table C.7-3",
     "An advisory about Basic Directory key attributes, not about this object's "
     "IOD. Study ID is Type 2 in General Study and may be zero length, so the "
     "object is conformant and the message describes a different use case."),
    (r"Retired Person Name form", FLOOR, "PS3.5 Section 6.2", "Table 6.2-1",
     "A single-component PN with no caret delimiters is a legal PN value. The "
     "warning is about a deprecated component form, not about conformance, and "
     "it fires on de-identified subject identifiers by construction."),
    (r"CodingSchemeDesignator is deprecated", FLOOR, "PS3.16 Section 8",
     "PS3.16 Annex D",
     "SRT is retired in favour of SCT. A retired coding scheme designator "
     "remains legal in objects encoded against the edition current when they "
     "were written, and PRE-04 forbids reporting edition drift as "
     "non-conformance."),
    (r"Unrecognized defined term .* attribute <Image Type>", FLOOR,
     "PS3.3 Section C.7.6.1.1.2", "Table C.7-9",
     "Image Type values 3 and 4 are Defined Terms. PS3.3 Section 6.2 states "
     "that a Defined Term list may be extended, so an unrecognised value is "
     "conformant."),
    (r"Unrecognized defined term .* attribute <Coding Scheme Designator>", FLOOR,
     "PS3.3 Section 8.2", "PS3.16 Section 8",
     "The Coding Scheme Designator list is extensible and private designators "
     "are permitted, so an unrecognised value is not a violation."),
    (r"Shared Functional Groups Sequence.*is (missing|empty|unexpected)", FLOOR,
     "PS3.3 Section C.7.6.16", "Table C.7.6.16-1",
     "A functional group macro may be carried in either the Shared or the "
     "Per-Frame Functional Groups Sequence. A checker that looks only in Shared "
     "reports a macro carried per-frame as missing, which is a property of the "
     "checker rather than of the object."),
    (r"Module <General> Tag \(TAG\) \((Rows|Columns|Ethnic Group)\) is unexpected",
     FLOOR, "PS3.3 Table C.7-11b", "Table C.7-1",
     "Rows and Columns are Image Pixel module attributes and Ethnic Group is "
     "Patient module Type 3. All three are legitimately present. The message is "
     "a module-attribution artefact of the checker."),
    (r"Missing attribute Type 2C Conditional Element=<Laterality>", FLOOR,
     "PS3.3 Section C.7.3.1", "Table C.7-5a",
     "Laterality is Type 2C, required if the body part examined is a paired "
     "structure. PS3.3 publishes no normative list of paired structures and "
     "Body Part Examined is Type 3 in the same table, so the condition is not "
     "evaluable from the dataset by any third party."),
    (r"Shall not be present for Referenced SOP Class that is not multi-frame",
     NET, "PS3.3 Section C.18.3", "Table C.18.3-1",
     "Referenced Frame Number is Type 1C in the Image Reference Macro, required "
     "only where the referenced instance is multi-frame. The referenced SOP "
     "Class is recorded in the same item, so the condition is evaluable and the "
     "attribute is present when not permitted."),
    (r"Missing attribute Type 2 Required Element=<ClinicalTrialSite(Name|ID)>",
     NET, "PS3.3 Section C.7.1.3", "Table C.7-2b",
     "Where the Clinical Trial Subject module is included, Clinical Trial Site "
     "Name and Site ID are Type 2 and shall be present even if zero length. "
     "Absence of a Type 2 attribute in an included module is a violation."),
    (r"Clinical Trial Site (Name|ID)\) is missing", NET, "PS3.3 Section C.7.1.3",
     "Table C.7-2b", "Same requirement as the dciodvfy form, reported by the "
     "second validator."),
    (r"Missing attribute Type 1C Conditional Element=<DeidentificationMethod",
     NET, "PS3.3 Section C.7.1.1", "Table C.7-1",
     "De-identification Method and De-identification Method Code Sequence are "
     "Type 1C, required if Patient Identity Removed is YES. That attribute is "
     "in the same module, so the condition is evaluable from the dataset."),
    (r"De-identification Method( Code Sequence)?\) is missing", NET,
     "PS3.3 Section C.7.1.1", "Table C.7-1",
     "Same requirement as the dciodvfy form, reported by the second validator."),
    (r"Missing attribute Type 2 Required Element=<Manufacturer> Module=<GeneralEquipment>",
     NET, "PS3.3 Section C.7.5.1", "Table A.35.4-1",
     "General Equipment has Usage M in the Key Object Selection Document IOD "
     "and Manufacturer is Type 2 within it, so it shall be present even if zero "
     "length. Absence is a violation of a mandatory module."),
    (r"General Equipment> Tag \(TAG\) \(Manufacturer\) is missing", NET,
     "PS3.3 Section C.7.5.1", "Table A.35.4-1",
     "Same requirement, reported by the second validator."),
    (r"Missing attribute Type 1 Required Element=<ReferencedSOPClassUID>", NET,
     "PS3.3 Section 10.8", "Table 10-11",
     "Referenced SOP Class UID is Type 1 in the SOP Instance Reference Macro. A "
     "Type 1 attribute absent is a violation with no condition to evaluate."),
    (r"Referenced SOP Class UID\) is missing", NET, "PS3.3 Section 10.8",
     "Table 10-11", "Same requirement, reported by the second validator."),
    (r"Referenced SOP Instance is not listed in CurrentRequestedProcedureEvidenceSequence",
     NET, "PS3.3 Section C.17.2.2", "Table C.17-3",
     "The evidence sequences shall list every SOP Instance referenced from the "
     "content tree. This is a relational requirement stated in the module "
     "description and evaluable entirely from the object."),
    (r"Length invalid for this VR", NET, "PS3.5 Section 6.2", "Table 6.2-1",
     "Decimal String has a maximum length of 16 bytes. A 17 byte value is an "
     "encoding violation. Cited to PS3.5 rather than PS3.3, which is recorded "
     "as an off-part citation."),
    (r"invalid data values for Value Representations", NET, "PS3.5 Section 6.2",
     "Table 6.2-1",
     "The dataset-level summary of the same VR length violation. Cited to PS3.5, "
     "recorded as an off-part citation."),
    (r"Bad attribute Value Multiplicity", NET, "PS3.6 Section 6", "PS3.6 Chapter 6",
     "Value Multiplicity is fixed by the data dictionary. A value multiplicity "
     "outside it is a violation. Cited to PS3.6, recorded as an off-part "
     "citation."),
    (r"Bad Sequence number of Items", NET, "PS3.3 Section 7.4", "PS3.6 Chapter 6",
     "A sequence required to carry one or more items carrying zero items is a "
     "violation of the module definition."),
    (r"DisplayedAreaSelectionSequence is internally inconsistent", UNDECIDABLE,
     "PS3.3 Section C.10.4", "Table C.10-4",
     "PS3.3 C.10.4 states no ordering relation between the top left hand corner "
     "and the bottom right hand corner, and in the observed cases one axis is "
     "equal rather than inverted. Without normative text the direction cannot "
     "be adjudicated, and the fence requires uncited to be undecidable."),
    (r"Missing attribute Type 1C Conditional Element=", UNDECIDABLE,
     "", "",
     "A Type 1C class whose condition this pass could not evaluate from the "
     "template alone. Undecidable rather than assigned."),
    (r"Missing attribute Type 2C Conditional Element=", UNDECIDABLE, "", "",
     "A Type 2C class whose condition this pass could not evaluate from the "
     "template alone."),
]

# dicom-validator emits no severity levels and demotes any 1C or 2C condition it
# cannot parse to Type 3, so it fails open. Addendum 02 section 2 registers that
# it is a second opinion on 1C and 2C only and must never be a rate source.
# Every one of its findings that no rule above resolves is undecidable by that
# registered rule rather than by this pass running out of ideas.
DICOM_VALIDATOR_DEFAULT = (
    UNDECIDABLE, "addendum 02 section 2", "",
    "dicom-validator 0.8.2 emits no severity levels and demotes unparseable 1C "
    "and 2C conditions to Type 3, so it fails open and is registered as a "
    "second opinion rather than a rate source. A finding of its own that no "
    "cited rule resolves stays undecidable.")


def adjudicate(family: str, validator: str) -> dict:
    for pattern, verdict, section, table, rationale in RULES:
        if re.search(pattern, family, re.I):
            return {"adjudication2": verdict, "citation_section2": section,
                    "citation_table2": table, "rationale2": rationale,
                    "rule2": pattern}
    if validator == "dicom-validator":
        verdict, section, table, rationale = DICOM_VALIDATOR_DEFAULT
        return {"adjudication2": verdict, "citation_section2": section,
                "citation_table2": table, "rationale2": rationale,
                "rule2": "dicom-validator default"}
    return {"adjudication2": UNDECIDABLE, "citation_section2": "",
            "citation_table2": "", "rule2": "no rule matched",
            "rationale2": "No rule in the published table matches this family, "
                          "so it is undecidable by construction rather than by "
                          "omission."}


def pre_disclosed(family: str) -> bool:
    return any(needle.lower() in family.lower() for needle in PRE_DISCLOSED)


# --- the two passes -----------------------------------------------------------
BLIND_COLUMNS = ["sop_class_name", "validator", "message_class_id",
                 "message_template", "severity_as_emitted", "objects"]


def load_first_pass() -> pd.DataFrame:
    frames = []
    for path in sorted(glob.glob(str(PHASE2 / "adjudication_*.csv"))):
        d = pd.read_csv(path)
        if "sop_class_name" not in d.columns:
            d["sop_class_name"] = Path(path).stem.replace("adjudication_", "")
        d["source_file"] = Path(path).name
        frames.append(d)
    return pd.concat(frames, ignore_index=True)


# The two passes used different scales, and that is itself a result of running
# two passes. The first has five terms and the second has three: the first
# splits what the second calls FLOOR into three cases, by *why* the message is
# not a defect.
#
#   FLOOR         a floor class, legal by a cited section
#   NOT-IOD       not a requirement of this object's IOD at all, for example a
#                 Basic Directory advisory
#   PLAUSIBILITY  a heuristic of the validator's own, citing no Type and no
#                 condition, so there is no requirement to violate
#
# All three mean the same thing for any rate: the class does not count toward a
# net numerator. The crosswalk is published here rather than applied silently,
# and agreement is reported on both scales so a reader can see which of the two
# the number depends on.
CROSSWALK = {"FLOOR": FLOOR, "NOT-IOD": FLOOR, "PLAUSIBILITY": FLOOR,
             "NET": NET, "GENUINE": NET, "UNDECIDABLE": UNDECIDABLE}

# The strict reading keeps the first pass's distinction and treats its two extra
# terms as their own category, so a coarse mapping cannot manufacture agreement.
CROSSWALK_STRICT = {"FLOOR": FLOOR, "NOT-IOD": "NOT-IOD",
                    "PLAUSIBILITY": "PLAUSIBILITY", "NET": NET,
                    "GENUINE": NET, "UNDECIDABLE": UNDECIDABLE}


def normalise_verdict(value, strict: bool = False) -> str:
    """Map the first pass's vocabulary onto this pass's, by published crosswalk."""
    text = str(value or "").strip().upper()
    table = CROSSWALK_STRICT if strict else CROSSWALK
    return table.get(text, UNDECIDABLE)


def second_pass() -> pd.DataFrame:
    first = load_first_pass()
    first["family"] = first["message_template"].map(family_of)
    rows = []
    for row in first.itertuples():
        verdict = adjudicate(row.family, row.validator)
        rows.append(dict(
            sop_class_name=row.sop_class_name, validator=row.validator,
            message_class_id=row.message_class_id,
            severity_as_emitted=row.severity_as_emitted,
            objects=row.objects, family=row.family,
            message_template=row.message_template,
            adjudication1_raw=getattr(row, "adjudication", ""),
            adjudication1=normalise_verdict(getattr(row, "adjudication", "")),
            adjudication1_strict=normalise_verdict(
                getattr(row, "adjudication", ""), strict=True),
            citation_section1=getattr(row, "citation_section", ""),
            pre_disclosed=pre_disclosed(row.family), **verdict))
    frame = pd.DataFrame(rows)
    # The decision that actually drives every published rate is binary: does
    # this class count toward the net numerator or not. Everything else is a
    # difference in how the exclusion is explained.
    frame["net1"] = frame["adjudication1"] == NET
    frame["net2"] = frame["adjudication2"] == NET
    return frame


def kappa(a: pd.Series, b: pd.Series, labels=(FLOOR, NET, UNDECIDABLE)) -> dict:
    """Cohen's kappa on the two verdict columns."""
    n = len(a)
    if n == 0:
        return {"n": 0, "agreement": None, "kappa": None}
    observed = float((a.values == b.values).sum()) / n
    expected = 0.0
    for label in labels:
        expected += (float((a == label).sum()) / n) * (float((b == label).sum()) / n)
    k = (observed - expected) / (1 - expected) if expected < 1 else float("nan")
    return {"n": int(n), "agreement": round(100 * observed, 2),
            "kappa": round(k, 4) if k == k else None,
            "expected_agreement": round(100 * expected, 2)}


def consensus(frame: pd.DataFrame) -> pd.DataFrame:
    """Keep only agreements. Any disagreement drops to UNDECIDABLE."""
    out = frame.copy()
    agree = out["adjudication1"] == out["adjudication2"]
    out["consensus"] = out["adjudication2"].where(agree, UNDECIDABLE)
    out["agreed"] = agree
    return out


def main(argv=None) -> int:
    from .adjudicate2_report import main as report_main
    return report_main()


if __name__ == "__main__":
    raise SystemExit(main())
