"""Phase 1, the variant ladder: is the writer-specific floor structural?

Phase 1 measured one number, and that number is fragile. On SEG BINARY under
`dciodvfy` the two writers' floor sets are disjoint, Jaccard 0.0, but the
disjointness rests on 0 message classes against 1. A single message class on one
side of a comparison is not a robust basis for the claim that a floor does not
transfer between writers. Delete that one message and the finding evaporates.

The ladder exists to answer the only question that matters about that number: is
it a property of the writers, or a property of the one fixture they were handed?
Nine perturbations are applied to each writer's own baseline object. If the two
writers' floor sets stay disjoint, or at least stay non-equal in the same
direction, under all nine, the finding is structural. If any perturbation makes
them equal, or reverses which writer's set contains the other, the finding is an
accident of one fixture and has to be reported as one.

Design constraints, each of which exists because the alternative would have
produced a wrong answer:

**A variant is applied within a writer, never across writers.** The comparison
is always W1 variant against W2 variant, or W1 baseline against W2 baseline.
Comparing a perturbed object against an unperturbed one would measure the
perturbation, not the writer.

**The baseline is measured twice.** Once as emitted, and once after a pydicom
read and re-save with no change at all. Every variant object is a pydicom
re-save, so if re-saving alone moved a message class then every variant delta
would be confounded by the round trip. The control is not one of the nine and is
labelled as a control everywhere it appears.

**SOPInstanceUID is not changed by a variant.** The unit of count is the
distinct `(SOPInstanceUID, message_class_id)` pair, and the sets are always
formed within one `(writer, sop_class, variant, validator)` cell, so a shared
UID across variants cannot merge two cells. Minting a new UID per variant would
add a difference to the object that the variant definition does not ask for.

**A variant that does not apply to a class is recorded, not skipped.** Two of
the nine are Segmentation-only by definition. Those cells carry an explicit
NOT_APPLICABLE flag and the reason, because a missing row and a row that says
"this does not apply" read identically in a table only if the table lies.

**Nothing here adjudicates.** Message classes are counted exactly as the two
third-party validators emit them, through the Phase 1 parser and normaliser in
`colophon.floor`. Where a validator's behaviour under a variant is ambiguous,
for example when it cannot read the object at all, the ambiguity is reported and
a ledger row records it as such.

Usage:
    python -m colophon.variants                 build variants, validate, report
    python -m colophon.variants --no-build      re-validate existing variants
"""
from __future__ import annotations

import argparse
import copy
import csv
import json
import sys
from pathlib import Path

import pydicom
from pydicom.uid import DeflatedExplicitVRLittleEndian

from . import floor
from .paths import CACHE, RESULTS

CMD = "python -m colophon.variants"
FIXTURE = floor.FIXTURE
VARIANT_ROOT = CACHE / "fixture" / "variants"
STANDARD_PATH = Path(r"C:\Users\dekay\dicom-validator")

W1, W2 = floor.W1, floor.W2

# The two classes both writers emit. These are the only cells where a Jaccard
# between writers means anything. The other two are highdicom-only because
# dcmqi could not emit them at all, recorded in floor.W2_EMISSION_GAPS.
SHARED_CLASSES = ["SEG BINARY", "TID 1500 SR"]
SEG_CLASSES = {"SEG BINARY", "SEG FRACTIONAL"}

# Applied to Segmentation only, by definition of the variant.
SEG_ONLY_REASON = ("variant is defined on Segmentation functional groups and "
                   "segment attributes, which this IOD does not carry")


# --- the perturbations --------------------------------------------------------
# Each takes a mutable dataset and the class name, and edits in place. None of
# them touches SOPInstanceUID, SeriesInstanceUID or the pixel data, so the
# object stays the same object with a different conformance surface.

def _v1_copy_forward(ds, sop_class):
    """Standard Extended: a standard attribute the derived IOD does not define.

    SliceThickness is taken from the source CT rather than invented, because the
    point of the Standard Extended pattern is a real acquisition attribute
    carried forward into a derived object. Slice Thickness lives in the Image
    Plane and CT Image modules, neither of which is in the Segmentation,
    Parametric Map or SR IOD, so at the dataset root it is a standard attribute
    outside the IOD in all four classes.
    """
    src = pydicom.dcmread(FIXTURE / "ct" / "ct_000.dcm", stop_before_pixels=True)
    ds.SliceThickness = src.SliceThickness


def _v2_segid_to_shared(ds, sop_class):
    """Move SegmentIdentificationSequence from Per-Frame to Shared.

    Both writers put it per-frame. Moving it to Shared is the other legal
    placement in the Multi-frame Functional Groups module, and it is the
    placement a single-segment writer would naturally choose. On this two-segment
    fixture it also makes every frame name segment 1, which is a statement about
    the content and not only about the encoding. That is recorded here rather
    than avoided: the variant is defined at the encoding level and the validators
    are what decide whether the encoding is a finding.
    """
    shared = ds.SharedFunctionalGroupsSequence[0]
    shared.SegmentIdentificationSequence = copy.deepcopy(
        ds.PerFrameFunctionalGroupsSequence[0].SegmentIdentificationSequence)
    for item in ds.PerFrameFunctionalGroupsSequence:
        if "SegmentIdentificationSequence" in item:
            del item.SegmentIdentificationSequence


def _v3_zero_length_laterality(ds, sop_class):
    """Laterality (0020,0060) present with zero length.

    Zero length and absent are different findings and this project never merges
    them. Laterality is Type 2C in General Series, so an empty value is the
    conformant encoding when the condition does not apply and the interesting
    case is what each validator says about it in an IOD that does not include
    General Series at all.
    """
    ds.Laterality = ""


def _v4_manual_without_identification(ds, sop_class):
    """SegmentAlgorithmType MANUAL with (0062,0007) deleted.

    dcmqi's baseline already omits the identification sequence while declaring
    AUTOMATIC, so on that writer this variant changes only the declared type and
    the deletion is a no-op. That asymmetry is a property of the writers, not of
    the harness, and it is left in place rather than compensated for.
    """
    for segment in ds.SegmentSequence:
        segment.SegmentAlgorithmType = "MANUAL"
        if (0x0062, 0x0007) in segment:
            del segment[(0x0062, 0x0007)]


def _v5_extended_defined_term(ds, sop_class):
    """BodyPartExamined (0018,0015) outside the standard Defined Term list.

    A Defined Term may be extended, so this is a legal encoding and the question
    is whether a validator treats an unlisted term as a finding anyway.
    """
    ds.BodyPartExamined = "COLOPHONPHANTOM"


def _v6_private_block(ds, sop_class):
    """A correctly reserved private block, one attribute in it.

    Reserved through pydicom's private_block so the creator element is written
    at (0099,0010) and the data element inside the reserved range. A private
    attribute in a properly reserved block is conformant, and a validator that
    reports it is reporting the presence of private data rather than a defect.
    """
    block = ds.private_block(0x0099, "COLOPHON VARIANT LADDER", create=True)
    block.add_new(0x01, "LO", "variant ladder probe")


def _v7_retired_attribute(ds, sop_class):
    """A retained retired attribute, DataSetSubtype (0008,0041).

    Chosen because it is retired in PS3.3 and carries no IOD-specific meaning,
    so it perturbs all four classes the same way. A retired image attribute such
    as Image Location would have been a different perturbation in an SR than in
    a Segmentation.
    """
    ds.DataSetSubtype = "COLOPHON RETIRED"


def _v8_content_creator(ds, sop_class):
    """Populated ContentCreatorName and its identification code sequence.

    Both Segmentations already carry a populated name, so for those the variant
    is the addition of (0070,0086) plus a changed name. For the Parametric Map
    and both SRs the name is absent at baseline and this variant supplies it.
    The Person Identification Macro item is built well formed, with the Type 1
    code sequence and an institution name, so the variant is a populated field
    and not a malformed one.
    """
    ds.ContentCreatorName = "Colophon^Variant^Ladder"
    code = pydicom.Dataset()
    code.CodeValue = "COLOPHON"
    code.CodingSchemeDesignator = "99COLOPHON"
    code.CodeMeaning = "Colophon variant ladder"
    person = pydicom.Dataset()
    person.PersonIdentificationCodeSequence = pydicom.Sequence([code])
    person.InstitutionName = "Colophon"
    ds.ContentCreatorIdentificationCodeSequence = pydicom.Sequence([person])


def _v9_deflated(ds, sop_class):
    """Deflated Explicit VR Little Endian, 1.2.840.10008.1.2.1.99.

    The only variant that changes the encoding of the whole object rather than
    one attribute. It is in the ladder because a transfer syntax a tool cannot
    read produces a floor set that has nothing to do with the IOD, and the
    ladder should say so if that happens.
    """
    ds.file_meta.TransferSyntaxUID = DeflatedExplicitVRLittleEndian


VARIANTS = [
    ("V0", "baseline as emitted", None, None),
    ("V0R", "round-trip control, pydicom read and re-save, no change",
     lambda ds, sop_class: None, None),
    ("V1", "Standard Extended copy-forward of SliceThickness from the source CT",
     _v1_copy_forward, None),
    ("V2", "SegmentIdentificationSequence moved from Per-Frame to Shared",
     _v2_segid_to_shared, SEG_CLASSES),
    ("V3", "zero-length Laterality (0020,0060)", _v3_zero_length_laterality, None),
    ("V4", "SegmentAlgorithmType MANUAL with (0062,0007) absent",
     _v4_manual_without_identification, SEG_CLASSES),
    ("V5", "Extended Defined Term in BodyPartExamined (0018,0015)",
     _v5_extended_defined_term, None),
    ("V6", "well-formed private block with one private attribute",
     _v6_private_block, None),
    ("V7", "retained retired attribute DataSetSubtype (0008,0041)",
     _v7_retired_attribute, None),
    ("V8", "populated ContentCreatorName (0070,0084) and identification sequence",
     _v8_content_creator, None),
    ("V9", "Deflated Explicit VR LE, 1.2.840.10008.1.2.1.99", _v9_deflated, None),
]

# The nine the design nominates. V0 and V0R are the baseline and its control and
# are never counted as rungs of the ladder.
LADDER = [v[0] for v in VARIANTS if v[0] not in ("V0", "V0R")]

TITLES = {vid: title for vid, title, _, _ in VARIANTS}


def applicability(variant_id: str, sop_class: str) -> tuple[bool, str]:
    """Whether a variant applies to a class, and why not when it does not."""
    only = {vid: scope for vid, _, _, scope in VARIANTS}[variant_id]
    if only is None or sop_class in only:
        return True, ""
    return False, SEG_ONLY_REASON


def _slug(text: str) -> str:
    return text.lower().replace(" ", "_")


def build(rebuild: bool = True) -> list[dict]:
    """Write one file per (writer, class, variant) that applies.

    Returns the object inventory, including the cells that do not apply, so the
    caller can emit a NOT_APPLICABLE row rather than a hole in the table.
    """
    inventory = []
    for writer, sop_class, rel in floor.OBJECTS:
        source = FIXTURE / rel
        if not source.exists():
            raise FileNotFoundError(
                "missing baseline object %s. Rebuild the Phase 1 fixture before "
                "running the ladder: the ladder perturbs baselines, it does not "
                "create them." % source)
        for variant_id, title, fn, _scope in VARIANTS:
            applies, reason = applicability(variant_id, sop_class)
            if not applies:
                inventory.append({"writer": writer, "sop_class": sop_class,
                                  "variant": variant_id, "title": title,
                                  "path": None, "not_applicable": True,
                                  "reason": reason})
                continue
            if variant_id == "V0":
                inventory.append({"writer": writer, "sop_class": sop_class,
                                  "variant": variant_id, "title": title,
                                  "path": source, "not_applicable": False,
                                  "reason": ""})
                continue
            out = (VARIANT_ROOT / ("w1" if writer == W1 else "w2")
                   / _slug(sop_class) / ("%s.dcm" % variant_id))
            if rebuild or not out.exists():
                out.parent.mkdir(parents=True, exist_ok=True)
                ds = pydicom.dcmread(source)
                fn(ds, sop_class)
                ds.save_as(out, enforce_file_format=True)
            inventory.append({"writer": writer, "sop_class": sop_class,
                              "variant": variant_id, "title": title,
                              "path": out, "not_applicable": False, "reason": ""})
    return inventory


# --- measurement --------------------------------------------------------------
ROW_FIELDS = ["writer", "sop_class", "variant", "variant_title", "validator",
              "message_class_id", "message_template", "severity_as_emitted",
              "sop_instance_uid", "not_applicable", "not_applicable_reason",
              "validator_returncode", "object_file"]


def measure(inventory: list[dict], standard_path: Path = STANDARD_PATH) -> list[dict]:
    """One row per (writer, class, variant, validator, message_class_id).

    Return codes are recorded and never used to decide anything. Both validators
    are run for their text.
    """
    rows = []
    for item in inventory:
        base = {"writer": item["writer"], "sop_class": item["sop_class"],
                "variant": item["variant"], "variant_title": item["title"]}
        if item["not_applicable"]:
            for vname in floor.VALIDATORS:
                rows.append({**base, "validator": vname, "message_class_id": "",
                             "message_template": "", "severity_as_emitted": "",
                             "sop_instance_uid": "", "not_applicable": "True",
                             "not_applicable_reason": item["reason"],
                             "validator_returncode": "", "object_file": ""})
            continue
        path = item["path"]
        ds = pydicom.dcmread(path, stop_before_pixels=True)
        uid = str(ds.SOPInstanceUID)
        for vname in floor.VALIDATORS:
            rec = (floor.run_dicom_validator(path, standard_path)
                   if vname == "dicom-validator" else floor.run_dciodvfy(path))
            seen = set()
            for finding in rec["findings"]:
                template = floor.normalise(finding["message"])
                mcid = floor.message_class_id(vname, template)
                # The unit is the distinct (SOPInstanceUID, message_class_id)
                # pair, so the same diagnostic on six frames is one row.
                if (uid, mcid) in seen:
                    continue
                seen.add((uid, mcid))
                rows.append({**base, "validator": vname, "message_class_id": mcid,
                             "message_template": template,
                             "severity_as_emitted": finding["severity"],
                             "sop_instance_uid": uid, "not_applicable": "False",
                             "not_applicable_reason": "",
                             "validator_returncode": rec["returncode"],
                             "object_file": str(path)})
            if not seen:
                # An empty floor set is a measurement. Without this row the cell
                # would be indistinguishable from a cell that was never run.
                rows.append({**base, "validator": vname, "message_class_id": "",
                             "message_template": "", "severity_as_emitted": "",
                             "sop_instance_uid": uid, "not_applicable": "False",
                             "not_applicable_reason": "",
                             "validator_returncode": rec["returncode"],
                             "object_file": str(path)})
    return rows


def classes(rows: list[dict], writer: str, sop_class: str, variant: str,
            validator: str) -> set[str]:
    return {r["message_class_id"] for r in rows
            if r["writer"] == writer and r["sop_class"] == sop_class
            and r["variant"] == variant and r["validator"] == validator
            and r["message_class_id"] and r["not_applicable"] == "False"}


def cell_applies(rows: list[dict], sop_class: str, variant: str) -> tuple[bool, str]:
    for r in rows:
        if r["sop_class"] == sop_class and r["variant"] == variant:
            if r["not_applicable"] == "True":
                return False, r["not_applicable_reason"]
            return True, ""
    return True, ""


def templates(rows: list[dict], ids: set[str]) -> dict[str, str]:
    out = {}
    for r in rows:
        if r["message_class_id"] in ids and r["message_class_id"] not in out:
            out[r["message_class_id"]] = "%s [%s]" % (r["message_template"],
                                                      r["severity_as_emitted"])
    return out


def compare(rows: list[dict]) -> list[dict]:
    """Jaccard per (shared class, validator, variant), plus the flip test.

    The direction of the Phase 1 finding is that W2 draws at least as much as
    W1: on SEG BINARY the sets are disjoint under dciodvfy and W1 is a strict
    subset of W2 under dicom-validator. A flip is therefore either set equality
    or W2 becoming a strict subset of W1.

    `symmetric_difference` is carried alongside the Jaccard because the Jaccard
    on its own is the wrong statistic for a ladder. Every perturbation adds the
    same attribute to both writers' objects, so it adds the same message classes
    to both sides, which inflates the intersection and drives the Jaccard toward
    1 without touching the writer-specific residue at all. The count of classes
    held by exactly one writer is the quantity that is not diluted that way.

    A cell is `testable` only if its baseline sets already differ. An equal pair
    cannot flip, and counting a rung that leaves it equal as a non-flip would
    pad the denominator with cells that were never at risk.
    """
    out = []
    for sop_class in SHARED_CLASSES:
        for variant_id, title, _, _ in VARIANTS:
            applies, reason = applicability(variant_id, sop_class)
            for validator in floor.VALIDATORS:
                testable = (classes(rows, W1, sop_class, "V0", validator)
                            != classes(rows, W2, sop_class, "V0", validator))
                if not applies:
                    out.append({"sop_class": sop_class, "variant": variant_id,
                                "variant_title": title, "validator": validator,
                                "not_applicable": True, "reason": reason,
                                "w1": 0, "w2": 0, "shared": 0, "union": 0,
                                "symmetric_difference": 0,
                                "jaccard": None, "vacuous": False,
                                "equal": False, "w2_subset_of_w1": False,
                                "w1_subset_of_w2": False, "flip": False,
                                "testable": testable,
                                "w1_only": {}, "w2_only": {}})
                    continue
                s1 = classes(rows, W1, sop_class, variant_id, validator)
                s2 = classes(rows, W2, sop_class, variant_id, validator)
                equal = s1 == s2
                out.append({
                    "sop_class": sop_class, "variant": variant_id,
                    "variant_title": title, "validator": validator,
                    "not_applicable": False, "reason": "",
                    "w1": len(s1), "w2": len(s2), "shared": len(s1 & s2),
                    "union": len(s1 | s2),
                    "symmetric_difference": len(s1 ^ s2),
                    "jaccard": round(floor.jaccard(s1, s2), 4),
                    "vacuous": not s1 and not s2,
                    "equal": equal,
                    "w2_subset_of_w1": s2 < s1,
                    "w1_subset_of_w2": s1 < s2,
                    "flip": (equal or s2 < s1) and testable,
                    "testable": testable,
                    "w1_only": templates(rows, s1 - s2),
                    "w2_only": templates(rows, s2 - s1),
                })
    return out


# --- output -------------------------------------------------------------------
def write_csv(rows: list[dict]) -> Path:
    out = RESULTS / "phase1_variants.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=ROW_FIELDS)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in ROW_FIELDS})
    return out


def _flip_sentence(cmp_rows: list[dict]) -> tuple[str, list[dict]]:
    """The explicit statement the design asks for, and the rows behind it.

    The SR cell is already equal at baseline, so a variant that keeps it equal
    is not a flip of anything. Only cells whose baseline is not already equal
    can flip, and the sentence says which those are.
    """
    baseline = {(c["sop_class"], c["validator"]): c
                for c in cmp_rows if c["variant"] == "V0"}
    testable = {k for k, c in baseline.items() if c["testable"]}
    flips = [c for c in cmp_rows
             if c["variant"] in LADDER and not c["not_applicable"]
             and (c["sop_class"], c["validator"]) in testable and c["flip"]]
    degenerate = sorted("%s under %s" % k for k in baseline if k not in testable)
    if not flips:
        head = ("**No variant flips the direction of the finding.** Across the "
                "nine perturbations, on every shared cell whose baseline sets "
                "are not already equal, the two writers' floor sets never "
                "become equal and W2's set never becomes a subset of W1's.")
    else:
        head = ("**At least one variant flips the direction of the finding.** "
                + "; ".join("%s under %s at %s becomes %s"
                            % (c["sop_class"], c["validator"], c["variant"],
                               "equal" if c["equal"] else "W2 a subset of W1")
                            for c in flips) + ".")
    if degenerate:
        head += ("\n\nThe flip test is degenerate on %s, where the two writers' "
                 "sets are already equal at baseline. Those cells are reported "
                 "in the tables but they cannot flip, because there is no "
                 "direction there to reverse." % ", ".join(degenerate))
    return head, flips


def _residuals_block(cmp_rows: list[dict]) -> str:
    lines = []
    for sop_class in SHARED_CLASSES:
        for validator in floor.VALIDATORS:
            cells = [c for c in cmp_rows if c["sop_class"] == sop_class
                     and c["validator"] == validator]
            lines.append("### %s, %s" % (sop_class, validator))
            lines.append("")
            any_diff = False
            for c in cells:
                if c["not_applicable"]:
                    lines.append("- **%s** not applicable: %s"
                                 % (c["variant"], c["reason"]))
                    continue
                if not c["w1_only"] and not c["w2_only"]:
                    continue
                any_diff = True
                lines.append("- **%s**, %s" % (c["variant"],
                                               TITLES[c["variant"]]))
                for mcid, template in sorted(c["w1_only"].items(),
                                             key=lambda x: x[1]):
                    lines.append("    - %s only, `%s`: %s"
                                 % (W1, mcid, template[:220]))
                for mcid, template in sorted(c["w2_only"].items(),
                                             key=lambda x: x[1]):
                    lines.append("    - %s only, `%s`: %s"
                                 % (W2, mcid, template[:220]))
            if not any_diff:
                lines.append("- no residual classes at any applicable rung: the "
                             "two writers' sets are identical everywhere, "
                             "including the baseline")
            lines.append("")
    return "\n".join(lines)


def direction_of(c: dict) -> str:
    if c["equal"] and c["vacuous"]:
        return "equal, both sets empty"
    if c["equal"]:
        return "equal" + ("" if c["testable"] else ", as at baseline")
    if c["w2_subset_of_w1"]:
        return "W2 strict subset of W1, FLIP"
    if c["w1_subset_of_w2"]:
        return "W1 strict subset of W2"
    if c["shared"] == 0:
        return "disjoint"
    return "overlapping, neither contains the other"


def _ladder_table(cmp_rows: list[dict], sop_class: str) -> str:
    lines = ["| variant | what it changes | validator | W1 | W2 | shared | union "
             "| Jaccard | held by one writer only | direction |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for c in cmp_rows:
        if c["sop_class"] != sop_class:
            continue
        if c["not_applicable"]:
            lines.append("| %s | %s | %s | n/a | n/a | n/a | n/a | "
                         "NOT_APPLICABLE | n/a | %s |"
                         % (c["variant"], TITLES[c["variant"]], c["validator"],
                            c["reason"]))
            continue
        lines.append("| %s | %s | %s | %d | %d | %d | %d | %.4f | %d | %s |"
                     % (c["variant"], TITLES[c["variant"]], c["validator"],
                        c["w1"], c["w2"], c["shared"], c["union"],
                        c["jaccard"], c["symmetric_difference"],
                        direction_of(c)))
    return "\n".join(lines)


def _residue_block(cmp_rows: list[dict]) -> str:
    """The count of writer-specific classes, rung by rung.

    Reported separately from the Jaccard because the two answer different
    questions. The Jaccard asks how similar the floor sets are. This asks how
    many message classes one writer draws and the other does not, which is the
    quantity that decides whether a floor measured on one writer can be
    subtracted from the other's rate.
    """
    lines = ["| sop_class | validator | " + " | ".join(["V0", "V0R"] + LADDER)
             + " |",
             "|---|---|" + "---|" * (2 + len(LADDER))]
    for sop_class in SHARED_CLASSES:
        for validator in floor.VALIDATORS:
            cells = {c["variant"]: c for c in cmp_rows
                     if c["sop_class"] == sop_class and c["validator"] == validator}
            row = []
            for variant_id in ["V0", "V0R"] + LADDER:
                c = cells[variant_id]
                row.append("n/a" if c["not_applicable"]
                           else str(c["symmetric_difference"]))
            lines.append("| %s | %s | %s |" % (sop_class, validator,
                                               " | ".join(row)))
    return "\n".join(lines)


def _single_writer_table(rows: list[dict]) -> str:
    lines = ["| sop_class | variant | validator | highdicom message classes |",
             "|---|---|---|---|"]
    for sop_class in floor.W2_EMISSION_GAPS:
        for variant_id, _, _, _ in VARIANTS:
            applies, reason = applicability(variant_id, sop_class)
            for validator in floor.VALIDATORS:
                if not applies:
                    lines.append("| %s | %s | %s | NOT_APPLICABLE, %s |"
                                 % (sop_class, variant_id, validator, reason))
                    continue
                n = len(classes(rows, W1, sop_class, variant_id, validator))
                lines.append("| %s | %s | %s | %d |"
                             % (sop_class, variant_id, validator, n))
    return "\n".join(lines)


def _control_note(cmp_rows: list[dict], rows: list[dict]) -> str:
    moved = []
    for writer, sop_class, _ in floor.OBJECTS:
        for validator in floor.VALIDATORS:
            a = classes(rows, writer, sop_class, "V0", validator)
            b = classes(rows, writer, sop_class, "V0R", validator)
            if a != b:
                moved.append("%s %s under %s: %d classes as emitted, %d after "
                             "the round trip" % (writer, sop_class, validator,
                                                 len(a), len(b)))
    if not moved:
        return ("The round-trip control moved nothing. Every one of the six "
                "baseline objects draws exactly the same message classes after "
                "a pydicom read and re-save as it does as emitted, under both "
                "validators, so no variant delta below is a round-trip "
                "artefact.")
    return ("**The round-trip control moved something, and every variant delta "
            "below is confounded by it to that extent:** " + "; ".join(moved)
            + ". This is reported, not corrected.")


def write_markdown(rows: list[dict], cmp_rows: list[dict]) -> Path:
    flip_text, flips = _flip_sentence(cmp_rows)
    baseline = {(c["sop_class"], c["validator"]): c
                for c in cmp_rows if c["variant"] == "V0"}
    base_lines = ["| sop_class | validator | W1 | W2 | shared | union | Jaccard |",
                  "|---|---|---|---|---|---|---|"]
    for (sop_class, validator), c in sorted(baseline.items()):
        base_lines.append("| %s | %s | %d | %d | %d | %d | %.4f%s |"
                          % (sop_class, validator, c["w1"], c["w2"],
                             c["shared"], c["union"], c["jaccard"],
                             " (vacuous)" if c["vacuous"] else ""))

    n_objects = len({r["object_file"] for r in rows if r["object_file"]})
    na_cells = sorted({(r["sop_class"], r["variant"], r["not_applicable_reason"])
                       for r in rows if r["not_applicable"] == "True"})
    na_lines = ["| sop_class | variant | reason |", "|---|---|---|"]
    for sop_class, variant_id, reason in na_cells:
        na_lines.append("| %s | %s, %s | %s |"
                        % (sop_class, variant_id, TITLES[variant_id], reason))

    text = f"""# Phase 1 variant ladder: does the writer-specific floor survive perturbation?

Phase 1 measured Jaccard 0.0 between the two writers' floor sets on SEG BINARY
under `dciodvfy`, on one fixture, from 0 message classes against 1. This ladder
perturbs each writer's own baseline nine ways and re-measures, so the finding
either holds under perturbation or it does not. Reproduce with `{CMD}`.

Every variant is applied within a writer, to that writer's own baseline. No W1
variant is ever compared against a W2 baseline.

## Baseline, as emitted

{chr(10).join(base_lines)}

Jaccard is over sets of normalised `message_class_id`, counted as distinct
`(SOPInstanceUID, message_class_id)` pairs, never raw lines.

## Round-trip control

{_control_note(cmp_rows, rows)}

## How to read the Jaccard column

Every variant adds the same attribute to both writers' objects, so where it
draws a message it usually draws the same message class on both sides. That
inflates the intersection and pushes the Jaccard toward 1 without touching the
part of the floor set that belongs to the writer. The Jaccard therefore rises
along the ladder for a reason that has nothing to do with whether the floor
transfers.

The column headed **held by one writer only** is the size of the symmetric
difference, and it is the quantity the transfer question actually turns on: it
counts the message classes one writer draws and the other does not. It is
reported next to the Jaccard at every rung, and on its own below.

## The ladder, SEG BINARY

Both writers emit this class, so the Jaccard is a comparison rather than a
single-writer count.

{_ladder_table(cmp_rows, "SEG BINARY")}

## The ladder, TID 1500 SR

Both writers emit TID 1500, but not in the same SOP class: highdicom uses
Comprehensive 3D SR (1.2.840.10008.5.1.4.1.1.88.34) and dcmqi uses Enhanced SR
(1.2.840.10008.5.1.4.1.1.88.22). The comparison holds at the template level and
not at the IOD level.

{_ladder_table(cmp_rows, "TID 1500 SR")}

## Writer-specific residue, rung by rung

Message classes held by exactly one writer, at every rung.

{_residue_block(cmp_rows)}

The only departure from a flat row is V9 under `dciodvfy`, and the enumeration
below shows what it is: the two residual classes are the same diagnostic, a bad
value length, carrying different byte counts. The Phase 1 normaliser strips
tags, UIDs, frame indices, item indices and quoted values, and it does not strip
hexadecimal lengths, so two byte counts are two message classes. That is stated
rather than fixed, because changing the normaliser to suit one rung would change
every number Phase 1 and Phase 2 have already recorded.

## Does any variant flip the direction of the finding?

{flip_text}

## Residual classes that differ, enumerated

Every message class held by one writer and not the other, at every rung.

{_residuals_block(cmp_rows)}

## Not applicable cells

Recorded rather than skipped, so a table with a hole in it cannot read as a
table with a zero in it.

{chr(10).join(na_lines)}

## Non-transferable classes

SEG FRACTIONAL and Parametric Map are **highdicom-only** and carry no Jaccard at
any rung, because dcmqi could not emit them at all. The ladder is still run on
them, so the single-writer floor is known under perturbation, but nothing in
this section is a between-writer comparison.

{_single_writer_table(rows)}

## What was dropped

Nothing was sampled. {n_objects} objects were built or reused and every one was
run through both validators. Cells where a variant does not apply are listed
above with their reason and are not counted as measured zeros. No IDC object was
fetched and no network call was made: the ladder is local, on the Phase 1
fixture only.
"""
    out = RESULTS / "phase1_variants.md"
    out.write_text(text, encoding="utf-8")
    return out


# --- proposed ledger rows -----------------------------------------------------
PENDING = RESULTS / "pending_ledger" / "track_b.json"


def ledger_rows(rows: list[dict], cmp_rows: list[dict]) -> list[dict]:
    """Proposed rows for the claims ledger, generated from the measurement.

    Written to results/pending_ledger/track_b.json rather than to the ledger
    itself, so the merge is a deliberate step by the owner of the ledger and two
    tracks cannot race each other on one CSV.
    """
    def cell(sop_class, validator, variant):
        return next(c for c in cmp_rows if c["sop_class"] == sop_class
                    and c["validator"] == validator and c["variant"] == variant)

    flip_text, flips = _flip_sentence(cmp_rows)
    seg_dc = {v: cell("SEG BINARY", "dciodvfy", v) for v in ["V0", "V0R"] + LADDER}
    seg_dv = {v: cell("SEG BINARY", "dicom-validator", v)
              for v in ["V0", "V0R"] + LADDER}
    jac_dc = sorted({c["jaccard"] for v, c in seg_dc.items() if v in LADDER})
    jac_dv = sorted({c["jaccard"] for v, c in seg_dv.items() if v in LADDER})
    res_dc = sorted({c["symmetric_difference"] for v, c in seg_dc.items()
                     if v in LADDER})
    res_dv = sorted({c["symmetric_difference"] for v, c in seg_dv.items()
                     if v in LADDER})
    n_objects = len({r["object_file"] for r in rows if r["object_file"]})
    na_cells = sorted({(r["sop_class"], r["variant"])
                       for r in rows if r["not_applicable"] == "True"})
    deflate = seg_dc["V9"]

    control_ok = all(
        classes(rows, w, c, "V0", v) == classes(rows, w, c, "V0R", v)
        for w, c, _ in floor.OBJECTS for v in floor.VALIDATORS)

    shared = dict(
        section="B1", section_title="Phase 1 variant ladder",
        command=CMD, source_file="results/phase1_variants.csv",
        floor="this section measures the floor under perturbation; it does not "
              "quote a rate against one",
        dropped="nothing sampled: %d objects built or reused, every one run "
                "through both validators. Cells where a variant does not apply "
                "are flagged NOT_APPLICABLE with a reason and are not counted "
                "as measured zeros" % n_objects,
        validator="dciodvfy, dicom-validator",
        validator_version="dicom3tools snapshot 20260701065818; "
                          "dicom-validator 0.8.2, edition 2026c",
        verified_on="2026-08-02")

    out = [
        dict(id="B-01", claim="The Phase 1 headline reproduces under the variant "
             "harness at baseline, so the ladder measures the same object Phase 1 "
             "measured.",
             status="MEASURED",
             value="SEG BINARY, dciodvfy, V0 baseline: Jaccard %.4f, highdicom "
                   "%d message classes, dcmqi %d, shared %d"
                   % (seg_dc["V0"]["jaccard"], seg_dc["V0"]["w1"],
                      seg_dc["V0"]["w2"], seg_dc["V0"]["shared"]),
             n=str(seg_dc["V0"]["shared"]), denominator=str(seg_dc["V0"]["union"]),
             sop_class="Segmentation Storage, BINARY",
             derived_from="F1-01",
             pinned_by_test="tests/test_variants.py::test_baseline_reproduces_phase_one",
             **shared),
        dict(id="B-02", claim="The two writers' dciodvfy floor sets on SEG "
             "BINARY are never equal under any of the nine perturbations, but "
             "the Jaccard at baseline is not itself a stable quantity.",
             status="MEASURED",
             value="SEG BINARY, dciodvfy, nine variants: Jaccard %s. The "
                   "baseline value of %.4f holds at %d of the nine rungs"
                   % (("constant at %.4f" % jac_dc[0]) if len(jac_dc) == 1
                      else "ranges from %.4f to %.4f" % (jac_dc[0], jac_dc[-1]),
                      seg_dc["V0"]["jaccard"],
                      sum(1 for v in LADDER
                          if seg_dc[v]["jaccard"] == seg_dc["V0"]["jaccard"])),
             n=str(sum(1 for v in LADDER if not seg_dc[v]["equal"])),
             denominator=str(len(LADDER)),
             sop_class="Segmentation Storage, BINARY",
             derived_from="B-01",
             pinned_by_test="tests/test_variants.py::test_dciodvfy_ladder_jaccards",
             status_note="Per rung: " + "; ".join(
                 "%s %.4f (W1 %d, W2 %d, shared %d, one writer only %d)"
                 % (v, seg_dc[v]["jaccard"], seg_dc[v]["w1"], seg_dc[v]["w2"],
                    seg_dc[v]["shared"], seg_dc[v]["symmetric_difference"])
                 for v in LADDER),
             notes="The Jaccard rises along the ladder because a perturbation "
                   "applied to both writers draws the same message class on "
                   "both sides and inflates the intersection. The rise is a "
                   "property of the instrument, not evidence that the floors "
                   "converge. B-10 reports the quantity that is not diluted "
                   "that way. The headline 0.0 should therefore be quoted as "
                   "the baseline value with its ladder range, never on its own.",
             **shared),
        dict(id="B-03", claim="The dicom-validator floor sets on SEG BINARY stay "
             "unequal under every perturbation, in the same direction as at "
             "baseline.",
             status="MEASURED",
             value="SEG BINARY, dicom-validator, nine variants: Jaccard %s; "
                   "highdicom stays a strict subset of dcmqi at %d of the %d "
                   "rungs"
                   % (("constant at %.4f" % jac_dv[0]) if len(jac_dv) == 1
                      else "ranges from %.4f to %.4f" % (jac_dv[0], jac_dv[-1]),
                      sum(1 for v in LADDER if seg_dv[v]["w1_subset_of_w2"]),
                      len(LADDER)),
             n=str(sum(1 for v in LADDER if not seg_dv[v]["equal"])),
             denominator=str(len(LADDER)),
             sop_class="Segmentation Storage, BINARY",
             derived_from="F1-03",
             pinned_by_test="tests/test_variants.py::test_dicom_validator_ladder_jaccards",
             status_note="Per rung: " + "; ".join(
                 "%s %.4f (W1 %d, W2 %d, shared %d, one writer only %d)"
                 % (v, seg_dv[v]["jaccard"], seg_dv[v]["w1"], seg_dv[v]["w2"],
                    seg_dv[v]["shared"], seg_dv[v]["symmetric_difference"])
                 for v in LADDER),
             **shared),
        dict(id="B-10", claim="The writer-specific residue is the stable "
             "quantity in the ladder: the number of message classes held by "
             "exactly one writer on SEG BINARY does not change under "
             "perturbation, under either validator, except where the transfer "
             "syntax defeats the reader.",
             status="MEASURED",
             value="SEG BINARY classes held by one writer only: dciodvfy "
                   "baseline %d, ladder %s; dicom-validator baseline %d, "
                   "ladder %s"
                   % (seg_dc["V0"]["symmetric_difference"],
                      ("constant at %d" % res_dc[0]) if len(res_dc) == 1
                      else "values %s" % ", ".join(str(r) for r in res_dc),
                      seg_dv["V0"]["symmetric_difference"],
                      ("constant at %d" % res_dv[0]) if len(res_dv) == 1
                      else "values %s" % ", ".join(str(r) for r in res_dv)),
             n=str(seg_dc["V0"]["symmetric_difference"]),
             denominator=str(seg_dc["V0"]["union"]),
             sop_class="Segmentation Storage, BINARY",
             derived_from="B-02, B-03",
             pinned_by_test="tests/test_variants.py::test_residue_is_stable_under_perturbation",
             status_note="Per rung, dciodvfy: " + "; ".join(
                 "%s %d" % (v, seg_dc[v]["symmetric_difference"]) for v in LADDER)
             + ". Per rung, dicom-validator: " + "; ".join(
                 "%s %d" % (v, seg_dv[v]["symmetric_difference"]) for v in LADDER)
             + ". The one departure is V9, where the pinned dciodvfy build does "
               "not read the deflated stream and both writers acquire a "
               "read-failure class of their own; see B-05.",
             **shared),
        dict(id="B-04", claim="No variant flips the direction of the finding."
             if not flips else "At least one variant flips the direction of the "
             "finding.",
             status="MEASURED",
             value=("no cell whose baseline sets differ becomes equal or "
                    "reverses containment under any of the nine variants"
                    if not flips else
                    "; ".join("%s under %s at %s becomes %s"
                              % (c["sop_class"], c["validator"], c["variant"],
                                 "equal" if c["equal"] else "W2 subset of W1")
                              for c in flips)),
             n=str(len(flips)),
             denominator=str(sum(1 for c in cmp_rows if c["variant"] in LADDER
                                 and not c["not_applicable"] and c["testable"])),
             sop_class="Segmentation Storage BINARY, TID 1500 SR",
             derived_from="B-02, B-03",
             pinned_by_test="tests/test_variants.py::test_direction_never_flips",
             status_note="A flip is set equality or W2 becoming a strict subset "
             "of W1. The TID 1500 SR cells are equal at baseline under both "
             "validators, so the flip test is degenerate there and those cells "
             "are excluded from the numerator and the denominator of this row.",
             **shared),
        dict(id="B-05", claim="Deflated Explicit VR Little Endian is not read by "
             "the pinned dciodvfy build, so the floor set it produces under that "
             "variant describes a reader failure and not the IOD.",
             status="MEASURED",
             value="V9, SEG BINARY, dciodvfy: highdicom %d message classes, "
                   "dcmqi %d, shared %d, Jaccard %.4f. The messages include "
                   "'Dicom dataset read failed' and a bad value length on a tag "
                   "that does not exist in either object"
                   % (deflate["w1"], deflate["w2"], deflate["shared"],
                      deflate["jaccard"]),
             sop_class="all four classes in the ladder",
             validator="dciodvfy",
             validator_version="dicom3tools snapshot 20260701065818",
             pinned_by_test="tests/test_variants.py::test_deflate_is_a_reader_failure_not_an_iod_finding",
             status_note="UNDECIDABLE as a conformance measurement. The counts "
             "are reported because the ladder must report every rung, but "
             "whether the pinned build lacks deflate support or rejects this "
             "particular stream is not something this project adjudicates. "
             "dicom-validator reads the same files without complaint, which is "
             "recorded as the disagreement it is and not resolved.",
             notes="The V9 row is the one rung where the two validators' answers "
                   "come from different causes, and it should be quoted with "
                   "that stated or not quoted at all. It is also the only rung "
                   "where the writer-specific residue is not 1, and the two "
                   "residual classes there are the same bad-value-length "
                   "diagnostic with different byte counts. The Phase 1 "
                   "normaliser strips tags, UIDs and indices, not hexadecimal "
                   "lengths, so they hash to two classes. The normaliser was "
                   "not changed to suit this rung.",
             **{k: v for k, v in shared.items()
                if k not in ("validator", "validator_version")}),
        dict(id="B-06", claim="Two of the nine variants are Segmentation-only by "
             "definition and their cells on the other classes are recorded as "
             "not applicable rather than skipped.",
             status="MEASURED",
             value="; ".join("%s %s" % (c, v) for c, v in na_cells),
             n=str(len(na_cells)),
             denominator=str(len(floor.CLASSES) * len(LADDER)),
             sop_class="Parametric Map, TID 1500 SR",
             pinned_by_test="tests/test_variants.py::test_not_applicable_cells_are_recorded",
             status_note="V2 moves SegmentIdentificationSequence between "
             "functional groups and V4 edits SegmentAlgorithmType. Neither "
             "attribute exists in the Parametric Map or SR IODs.",
             **shared),
        dict(id="B-07", claim="The round-trip control shows the pydicom re-save "
             "the ladder depends on does not itself move a message class."
             if control_ok else "The round-trip control moved a message class, "
             "so every variant delta is confounded by the re-save.",
             status="MEASURED",
             value=("all six baselines draw identical message-class sets as "
                    "emitted and after a pydicom read and re-save, under both "
                    "validators" if control_ok else
                    "at least one baseline draws a different set after a "
                    "pydicom read and re-save; see the control section of "
                    "results/phase1_variants.md"),
             n="6", denominator="6", sop_class="all four classes in the ladder",
             pinned_by_test="tests/test_variants.py::test_round_trip_control_moves_nothing",
             status_note="V0R is a control, not one of the nine variants, and it "
             "is labelled as such wherever it appears.",
             **shared),
        dict(id="B-08", claim="SEG FRACTIONAL and Parametric Map carry no "
             "between-writer Jaccard at any rung of the ladder, because dcmqi "
             "could not emit them.",
             status="MEASURED",
             value="highdicom-only at all %d rungs plus baseline and control; "
                   "the ladder is run on them so the single-writer floor is "
                   "known under perturbation, but no cell is a comparison"
                   % len(LADDER),
             n="2", denominator="4",
             sop_class="SEG FRACTIONAL, Parametric Map",
             derived_from="F1-04",
             pinned_by_test="tests/test_variants.py::test_single_writer_classes_carry_no_jaccard",
             **shared),
        dict(id="B-09", claim="The TID 1500 SR cell cannot test the direction of "
             "the finding, because the two writers' sets are already equal at "
             "baseline under both validators.",
             status="MEASURED",
             value="TID 1500 SR baseline: dciodvfy Jaccard %.4f from empty sets "
                   "on both writers, dicom-validator Jaccard %.4f from one "
                   "identical class on each"
                   % (cell("TID 1500 SR", "dciodvfy", "V0")["jaccard"],
                      cell("TID 1500 SR", "dicom-validator", "V0")["jaccard"]),
             sop_class="TID 1500 SR",
             derived_from="F1-05",
             pinned_by_test="tests/test_variants.py::test_sr_baseline_is_degenerate_for_the_flip_test",
             status_note="An equal pair cannot become more equal, so a variant "
             "that leaves it equal is not evidence either way. The SR rungs are "
             "reported for completeness and excluded from the flip test.",
             **shared),
        dict(id="B-11", claim="The ladder inherits the two unsatisfied tool pins "
             "from Phase 1, so its numbers carry the same deviation.",
             status="PENDING",
             value="registered dicom3tools 1.00~20240118131615-1, present "
                   "snapshot 20260701065818; registered highdicom 0.28.0, "
                   "present 0.28.1",
             sop_class="all four classes in the ladder",
             derived_from="F1-08",
             status_note="The ladder perturbs objects emitted by the "
             "unsatisfied highdicom build and scores them with the unsatisfied "
             "dciodvfy build. Neither substitution is silent and neither is "
             "treated as satisfying the pin. Nothing in the ladder emits "
             "LABELMAP or TILED_FULL, which are where the two dicom3tools "
             "builds are known to differ, but the pin must be closed before any "
             "corpus stratum is scored against these numbers.",
             **{k: v for k, v in shared.items() if k != "floor"}),
    ]
    return sorted(out, key=lambda r: r["id"])


def write_pending_ledger(entries: list[dict]) -> Path:
    from . import ledger
    for e in entries:
        unknown = sorted(set(e) - set(ledger.FIELDS))
        if unknown:
            raise ValueError("proposed ledger row %s has unknown fields %s"
                             % (e["id"], unknown))
        if e["status"] not in ledger.VALID_STATUS:
            raise ValueError("proposed ledger row %s has status %r"
                             % (e["id"], e["status"]))
        if e["status"] == "MEASURED":
            for required in ("command", "source_file", "dropped"):
                if not (e.get(required) or "").strip():
                    raise ValueError("MEASURED row %s is missing %s"
                                     % (e["id"], required))
    PENDING.parent.mkdir(parents=True, exist_ok=True)
    PENDING.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")
    return PENDING


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--no-build", action="store_true",
                    help="re-validate existing variant objects, do not rebuild")
    ap.add_argument("--standard-path", default=str(STANDARD_PATH),
                    help="pre-seeded dicom-validator standard cache")
    args = ap.parse_args(argv)

    inventory = build(rebuild=not args.no_build)
    rows = measure(inventory, Path(args.standard_path))
    cmp_rows = compare(rows)
    csv_path = write_csv(rows)
    md = write_markdown(rows, cmp_rows)
    pending = write_pending_ledger(ledger_rows(rows, cmp_rows))
    print("wrote %s, %s and %s" % (csv_path, md, pending))

    for sop_class in SHARED_CLASSES:
        for validator in floor.VALIDATORS:
            print("  %s, %s" % (sop_class, validator))
            for c in cmp_rows:
                if c["sop_class"] != sop_class or c["validator"] != validator:
                    continue
                if c["not_applicable"]:
                    print("    %-4s NOT_APPLICABLE" % c["variant"])
                    continue
                print("    %-4s Jaccard %.4f  (W1 %d, W2 %d, shared %d, "
                      "one writer only %d)  %s%s"
                      % (c["variant"], c["jaccard"], c["w1"], c["w2"],
                         c["shared"], c["symmetric_difference"],
                         direction_of(c), "" if c["testable"]
                         else "  [degenerate, equal at baseline]"))
    flip_text, flips = _flip_sentence(cmp_rows)
    print("\n%s" % flip_text.replace("**", ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
