"""Standard-level facts, verified against primary sources, encoded as data.

Everything here was checked against PS3.3 2026c, the IHE AIR supplement, or the
source of the toolkit concerned, on 2026-08-02. Encoding them as data rather than
as prose means a Phase 2 extractor cannot quietly use a wrong tag, and a test can
assert that the manuscript and the code agree.

Three results in this module changed the study.

**The largest available claim-1 finding does not exist.** The hypothesis was
that a Segmentation declaring SegmentAlgorithmType AUTOMATIC while omitting
algorithm identification would be non-conformant, which would have covered most
of the archive. In the Segmentation IOD, SegmentationAlgorithmIdentificationSequence
(0062,0007) is Type 3 with no condition of any kind. Omitting it on an AUTOMATIC
segment is conformant and no validator can flag it. The 1C form of that sequence
exists only in the Height Map Segmentation Image Module, which the Segmentation
IOD does not include.

**Two smaller hooks survive and are real.** SegmentAlgorithmName (0062,0009) is
Type 1C, required when SegmentAlgorithmType is not MANUAL, and it compels a
free-text string only. And a present-but-incomplete (0062,0007), missing any of
its three Type 1 children, is non-conformant where an absent one is not. That
asymmetry is the defensible measurement: absence is a gap in the standard,
incompleteness is a defect in the object.

**The IHE AIR profile does carry an unconditional shall.** An earlier decision
to demote AIR entirely rested on the belief that it has no Connectathon test
case and no Gazelle test plan. That is refuted by primary sources: 22 AIR test
definitions and 31 passing Connectathon records across five events. AIR is
Trial Implementation and has been since 2020-07-16, which qualifies it, but it
is not untested and its Creator requirement is normative.

Usage:
    python -m colophon.standards
"""
from __future__ import annotations

import hashlib
import json
import sys

from . import ledger
from .paths import CACHE, RESULTS

CMD = "python -m colophon.standards"
VERIFIED_ON = "2026-08-02"
EDITION = "PS3.3 2026c"

# --- Algorithm Identification Macro, PS3.3 2026c section 10.16, Table 10-19 ---
# Two of these were wrong in the study brief. A scan built on the wrong tags
# would have scored AlgorithmSource as absent everywhere.
ALGORITHM_IDENTIFICATION_MACRO = [
    {"tag": "(0066,002F)", "keyword": "AlgorithmFamilyCodeSequence", "vr": "SQ",
     "vm": "1", "type": "1", "highdicom": "unconditional", "dcmqi": "never"},
    {"tag": "(0066,0030)", "keyword": "AlgorithmNameCodeSequence", "vr": "SQ",
     "vm": "1", "type": "3", "highdicom": "never, no constructor path exists",
     "dcmqi": "never"},
    {"tag": "(0066,0036)", "keyword": "AlgorithmName", "vr": "LO", "vm": "1",
     "type": "1", "highdicom": "unconditional", "dcmqi": "never"},
    {"tag": "(0066,0031)", "keyword": "AlgorithmVersion", "vr": "LO", "vm": "1",
     "type": "1", "highdicom": "unconditional", "dcmqi": "never"},
    {"tag": "(0066,0032)", "keyword": "AlgorithmParameters", "vr": "LT", "vm": "1",
     "type": "3", "highdicom": "if parameters given", "dcmqi": "never"},
    {"tag": "(0024,0202)", "keyword": "AlgorithmSource", "vr": "LO", "vm": "1",
     "type": "3", "highdicom": "if source given", "dcmqi": "never"},
]

# Tags the brief gave that are wrong. Recorded so a wrong tag cannot return.
WITHDRAWN_TAGS = {
    "(0066,0033)": "given in the brief as AlgorithmParameters. Not allocated "
                   "anywhere in PS3.6 Chapter 6, including retired entries. The "
                   "next allocated element after (0066,0032) is (0066,0034) "
                   "Facet Sequence. Correct tag is (0066,0032).",
    "(0066,0032) as AlgorithmSource": "given in the brief as AlgorithmSource. "
                                      "(0066,0032) is AlgorithmParameters. "
                                      "Correct tag for AlgorithmSource is "
                                      "(0024,0202).",
}

# --- Segment-level attributes, Segmentation IOD -------------------------------
SEGMENT_ATTRIBUTES = [
    {"tag": "(0062,0008)", "keyword": "SegmentAlgorithmType", "vr": "CS",
     "type": "1", "location": "Segment Description Macro, Table C.8.20-4",
     "note": "Enumerated Values AUTOMATIC, SEMIAUTOMATIC, MANUAL"},
    {"tag": "(0062,0009)", "keyword": "SegmentAlgorithmName", "vr": "LO",
     "type": "1C", "location": "Segmentation Image Module, Table C.8.20-2",
     "condition": "Required if Segment Algorithm Type (0062,0008) is not MANUAL",
     "note": "Compels a free-text string only: no version, no family code, no "
             "source. This is the one conditional requirement in the "
             "Segmentation IOD that SegmentAlgorithmType triggers."},
    {"tag": "(0062,0007)", "keyword": "SegmentationAlgorithmIdentificationSequence",
     "vr": "SQ", "type": "3", "location": "Segmentation Image Module, Table C.8.20-2",
     "condition": None,
     "note": "Type 3 with no condition of any kind. Omitting it on an AUTOMATIC "
             "segment is conformant and no validator can flag it."},
    {"tag": "(0062,0007)", "keyword": "SegmentationAlgorithmIdentificationSequence",
     "vr": "SQ", "type": "1C",
     "location": "Height Map Segmentation Image Module, Table C.8.20-5",
     "condition": "Required if Segment Algorithm Type (0062,0008) is not MANUAL",
     "note": "NOT part of the Segmentation IOD. Table A.51-1 does not include "
             "this module. Citing this condition against a Segmentation object "
             "would be citing the wrong module."},
]

# --- Enhanced General Equipment, PS3.3 Table C.7-8b ---------------------------
# Usage M in Table A.51-1 (Segmentation IOD) and Table A.75-1 (Parametric Map
# IOD). Including the module overwrites the General Equipment Type designations.
ENHANCED_GENERAL_EQUIPMENT = [
    {"tag": "(0008,0070)", "keyword": "Manufacturer", "vr": "LO", "type": "1"},
    {"tag": "(0008,1090)", "keyword": "ManufacturerModelName", "vr": "LO", "type": "1"},
    {"tag": "(0018,1000)", "keyword": "DeviceSerialNumber", "vr": "LO", "type": "1"},
    {"tag": "(0018,1020)", "keyword": "SoftwareVersions", "vr": "LO", "type": "1"},
]
ENHANCED_GENERAL_EQUIPMENT_IODS = ["Segmentation Storage", "Parametric Map Storage"]

# --- the three reporting grades ----------------------------------------------
# Two grades would score a gap in the standard as a failure by a producer.
GRADES = {
    "non_conformant": "A stated requirement of PS3.3 is violated. Type 1 absent "
                      "or empty, or a Type 1C condition met and the attribute "
                      "absent, or a present sequence missing its Type 1 "
                      "children.",
    "conformant_but_uninformative": "Everything the standard requires is "
                                    "present, and none of it identifies the "
                                    "producing algorithm. This is the largest "
                                    "expected category and it is a gap in the "
                                    "standard, not a defect in the object.",
    "informative": "The producing algorithm is identifiable from the object "
                   "itself, by a value that is not a sentinel.",
}

# --- IHE AIR ------------------------------------------------------------------
AIR = {
    "title": "IHE Radiology Technical Framework Supplement, AI Results (AIR)",
    "revision": "Rev. 1.3",
    "date": "2025-08-08",
    "status": "Trial Implementation",
    "status_since": "2020-07-16",
    "url": "https://www.ihe.net/uploadedFiles/Documents/Radiology/"
           "IHE_RAD_Suppl_AIR_Rev1-3_TI_2025-08-08.pdf",
    "sha256": "33C9E86326E8946BA2DB0B37E5FEE73A865C7B11A00201B983690FCA2ED1D964",
    "retrieved": VERIFIED_ON,
    "tested": {
        "gazelle_test_definitions": 22,
        "connectathon_passing_records": 31,
        "connectathon_events": "Europe and North America 2022, Europe 2023, "
                               "2024, 2025, 2026",
    },
    "creator_requirement": {
        "locator": "Vol 3, Section 6.5.3.1, printed page 81, IHE lines 1730-1738",
        "force": "shall, unconditional",
        "text": "The Creator shall describe each algorithm that was used to "
                "generate the results in the Contributing Equipment Sequence "
                "(0018,A001). Multiple items may be included. The Creator shall "
                "encode the following details in the Contributing Equipment "
                "Sequence: Purpose of Reference Code Sequence (0040,A170) shall "
                "be (109102, DCM, \"Processing Equipment\"), Manufacturer "
                "(0008,0070), Manufacturer's Model Name (0008,1090), Software "
                "Versions (0018,1020), Device UID (0018,1002)",
    },
    "consistency_requirement": {
        "locator": "Vol 3, Section 6.5.3.1, pages 81 to 82, IHE lines 1744-1747",
        "force": "will, then a conditional shall",
        "text": "In SR instances, when an algorithm is identified in the SR Tree "
                "(typically in TID 4019 and/or TID 1004) it will also be "
                "identified in the Contributing Equipment Sequence (0018,A001). "
                "The content items, if present, shall contain the same value as "
                "the corresponding attribute shown in Table 6.5.3.1-1.",
        "note": "Cannot be cited as requiring the TID 1004 or TID 4019 content "
                "items to exist. Only that they agree if they do.",
    },
    "table_6531_1": {
        "locator": "Vol 3, Table 6.5.3.1-1, printed page 82",
        "title": "Corresponding Algorithm Identification Attributes and Content Items",
        "columns": 4,
        "note": "Four columns, not two: Contributing Equipment Sequence "
                "Attribute, Device Observer Content Item (TID 1004), Algorithm "
                "Identification Content Item (TID 4019), Algorithm "
                "Identification Sequence Attribute. Deliberately partial: "
                "SoftwareVersions has no TID 1004 counterpart, Device UID has "
                "no TID 4019 counterpart, Manufacturer has no TID 4019 "
                "counterpart.",
        # --- read from the PDF on 2026-08-02, Track G3 -----------------------
        "pdf_page": 82,          # 1 based, and equal to the printed page number
        "printed_page": 82,
        "rows": 4,               # data rows, below one header row
        "caption_verbatim": "Table 6.5.3.1-1: Corresponding Algorithm "
                            "Identification Attributes and Content Items",
        "column_headers": [
            "Contributing Equipment Sequence Attribute",
            "Device Observer Content Item (TID 1004)",
            "Algorithm Identification Content Item (TID 4019)",
            "Algorithm Identification Sequence Attribute",
        ],
        # Cells transcribed as printed. An empty cell is written as "" and is
        # empty in the document, not merely absent from an extractor's output:
        # the ruling lines say the cell exists and no text falls inside it.
        # The document opens each coded value with U+201C and closes it with a
        # plain U+0022. That asymmetry is in the source and is preserved here.
        "cells": [
            ["Manufacturer (0008,0070)",
             "(121014, DCM, “Device Observer Manufacturer\")",
             "",
             "Algorithm Source (0024,0202)"],
            ["Manufacturer’s Model Name (0008,1090)",
             "(121015, DCM, “Device Observer Model Name\")",
             "(111001, DCM, “Algorithm Name\")",
             "Algorithm Name (0066,0036)"],
            ["Software Versions (0018,1020)",
             "",
             "(111003, DCM, “Algorithm Version\")",
             "Algorithm Version (0066,0031)"],
            ["Device UID (0018,1002)",
             "(121012, DCM, “Device Observer UID\")",
             "",
             ""],
        ],
        "empty_cells": [
            "row 1 Manufacturer, column 3 TID 4019",
            "row 3 Software Versions, column 2 TID 1004",
            "row 4 Device UID, column 3 TID 4019",
            "row 4 Device UID, column 4 Algorithm Identification Sequence Attribute",
        ],
        "typography": "Opening quotation marks inside the table are U+201C. "
                      "Closing quotation marks are U+0022. The apostrophe in "
                      "Manufacturer's Model Name is U+2019. On printed page 81 "
                      "the same document uses U+0022 on both sides of "
                      "Processing Equipment.",
        # --- the central question --------------------------------------------
        "normative_force": "none of its own. The caption carries no modal verb "
                           "and the body carries no requirement column: no "
                           "Type, no Usage, no R/O/C designation and no shall, "
                           "should or will anywhere inside the grid. The table "
                           "is a correspondence map.",
        "invoking_sentence_verbatim":
            "In SR instances, when an algorithm is identified in the SR Tree "
            "(typically in TID 4019 and/or TID 1004) it will also be "
            "identified in the Contributing Equipment Sequence (0018,A001). "
            "The content items, if present, shall contain the same value as "
            "the corresponding attribute shown in Table 6.5.3.1-1.",
        "invoking_sentence_locator":
            "Vol 3, Section 6.5.3.1, printed page 81 IHE line 1744 through "
            "printed page 82, the two lines above the caption",
        "invoking_sentence_force":
            "will for the co-identification expectation, then shall for value "
            "equality. The shall is gated twice: by the scope clause In SR "
            "instances and by the condition if present. It constrains the "
            "value a content item carries, never whether the content item "
            "exists.",
        "required_of_the_creator": [
            "Nothing that the table itself adds. The five elements of the "
            "Contributing Equipment Sequence are required by the Section "
            "6.5.3.1 prose, which is captured separately in "
            "creator_requirement, and that prose stands whether or not the "
            "table exists.",
        ],
        "merely_mapped": [
            "The TID 1004 Device Observer content items",
            "The TID 4019 Algorithm Identification content items",
            "Algorithm Source (0024,0202), Algorithm Name (0066,0036) and "
            "Algorithm Version (0066,0031) of the Algorithm Identification "
            "Macro",
        ],
        "adds_requirement_beyond_6531_shall": False,
        "coverage_of_the_shall_list":
            "Four of the five elements the Section 6.5.3.1 shall names have a "
            "row: Manufacturer, Manufacturer's Model Name, Software Versions "
            "and Device UID. Purpose of Reference Code Sequence (0040,A170) "
            "has no row.",
        "ambiguity_reported_not_resolved":
            "The invoking sentence says the corresponding attribute, singular, "
            "while the table has two attribute columns: column 1, a "
            "Contributing Equipment Sequence attribute, and column 4, an "
            "Algorithm Identification Sequence attribute. The sentence does "
            "not say which. Its scope clause is In SR instances and its "
            "subject is The content items, while column 4 is introduced by the "
            "paragraph that follows the table and begins In some non-SR "
            "instances. Whether the equality obligation reaches column 4 is "
            "not stated in the document and is not decided here.",
        "second_reference":
            "Vol 1, Open and Closed Issues, printed page 16, question 26: In "
            "terms of lower level TID elements, those can be encoded in SR, "
            "maintaining the correspondences described in Table 6.5.3.1-1. "
            "Force: can. Non-normative, and it describes the table as "
            "correspondences.",
        "consequence_for_claim_3":
            "Claim 3 gains no yardstick from this table. It rests on the PS3.3 "
            "Type 1 requirements recorded at STD-03 and STD-04. The AIR "
            "Section 6.5.3.1 unconditional shall recorded at STD-06 is "
            "unchanged by this reading and remains the secondary yardstick. "
            "The table is citable as intent and as a correspondence map only.",
        # --- how it was read --------------------------------------------------
        "grid_geometry": {
            "units": "PDF user space points, origin bottom left, MediaBox "
                     "0 0 612 792",
            "vertical_rules_x": [96.6, 203.16, 309.72, 438.24, 550.92],
            "horizontal_rules_y": [476.52, 506.04, 535.56, 565.08, 594.6, 637.92],
            "note": "Five vertical rules bound four columns. Six horizontal "
                    "rules bound five rows, one header and four data rows. The "
                    "rules are drawn as thin filled rectangles in the page "
                    "content stream, so the grid is read rather than inferred "
                    "from text spacing.",
        },
        "extraction": {
            "method": "Four independent readings of the same pinned file, all "
                      "agreeing.",
            "readings": [
                "pdftotext -table, Xpdf 4.00",
                "pdftotext -lineprinter, Xpdf 4.00",
                "vector grid geometry from the page content stream, "
                "scripts/pdf_table_geometry.py, standard library only",
                "visual render of printed page 82 in the Chrome built in PDF "
                "viewer",
            ],
            "disagreeing_reading": "pdftotext -layout places (121012, DCM, "
                                   "Device Observer UID) on the Software "
                                   "Versions row. The grid geometry puts its "
                                   "baselines at y 493.44 and y 483.11, inside "
                                   "the Device UID row band of y 476.52 to "
                                   "506.04, and the visual render agrees. The "
                                   "layout reading is an artifact of unequal "
                                   "cell text heights and is wrong.",
            "reliability": "The four-column grid is now confirmed, not "
                           "reconstructed. Empty cells are reported as empty "
                           "on the strength of the ruling lines, which "
                           "establish that the cell exists, combined with the "
                           "absence of any text run whose origin falls inside "
                           "its band.",
        },
    },
}


AIR_PDF = CACHE / "air" / "IHE_RAD_Suppl_AIR_Rev1-3_TI_2025-08-08.pdf"


def air_sha256() -> tuple[str, str]:
    """Hash the cached AIR PDF and compare it to the recorded value.

    Returns (observed, verdict). Printing the recorded constant twice and
    calling the second copy an observation would make the integrity row
    unfalsifiable, so the comparison is done against the file if the file is
    there, and reported as a past observation if it is not.
    """
    if not AIR_PDF.exists():
        return ("not recomputed",
                "cached copy absent, so not rechecked in this run. Recorded as "
                "byte identical when fetched on %s. Refetch from the pinned "
                "URL to recheck." % AIR["retrieved"])
    h = hashlib.sha256(AIR_PDF.read_bytes()).hexdigest().upper()
    if h == AIR["sha256"]:
        return h, "match, byte identical, the document has not changed"
    return h, ("MISMATCH against the recorded %s. The document at the pinned "
               "URL changed, which is itself a finding and must be resolved "
               "before anything here is cited." % AIR["sha256"])


def air_table_markdown() -> str:
    """Render Table 6.5.3.1-1 and its normative reading from the AIR dict.

    Generated rather than typed, so the transcription in the write-up and the
    transcription the code reasons over cannot drift apart.
    """
    t = AIR["table_6531_1"]
    observed, verdict = air_sha256()
    L = []
    add = L.append
    add("# IHE AIR Table 6.5.3.1-1, read from the PDF")
    add("")
    add("Generated by `%s`. Do not edit by hand." % CMD)
    add("")
    add("## Source and integrity")
    add("")
    add("| field | value |")
    add("| --- | --- |")
    add("| document | %s |" % AIR["title"])
    add("| revision | %s, %s, %s |" % (AIR["revision"], AIR["status"], AIR["date"]))
    add("| url | %s |" % AIR["url"])
    add("| local copy | `%s` |" % AIR_PDF)
    add("| sha256 recorded | `%s` |" % AIR["sha256"])
    add("| sha256 observed at render time | `%s` |" % observed)
    add("| verdict | %s |" % verdict)
    add("| pages | 110, PDF page index equals the printed page number |")
    add("| table location | %s |" % t["locator"])
    add("")
    add("## Caption, verbatim")
    add("")
    add("> %s" % t["caption_verbatim"])
    add("")
    add("## The table, transcribed")
    add("")
    add("Four columns, five rows: one header row and %d data rows. An empty "
        "cell is printed empty in the document." % t["rows"])
    add("")
    add("| " + " | ".join(t["column_headers"]) + " |")
    add("| " + " | ".join("---" for _ in t["column_headers"]) + " |")
    for row in t["cells"]:
        add("| " + " | ".join(c if c else "*(empty)*" for c in row) + " |")
    add("")
    add("Empty cells, stated explicitly:")
    add("")
    for e in t["empty_cells"]:
        add("- %s" % e)
    add("")
    add(t["typography"])
    add("")
    add("## The sentence that invokes the table, verbatim")
    add("")
    add("> %s" % t["invoking_sentence_verbatim"])
    add("")
    add("Locator: %s." % t["invoking_sentence_locator"])
    add("")
    add("Force: %s" % t["invoking_sentence_force"])
    add("")
    add("A second reference exists. %s" % t["second_reference"])
    add("")
    add("## Normative force")
    add("")
    add("**The table has %s**" % t["normative_force"])
    add("")
    add("Required of the Creator by the table:")
    add("")
    for r in t["required_of_the_creator"]:
        add("- %s" % r)
    add("")
    add("Merely mapped, with no requirement attached anywhere in the section:")
    add("")
    for r in t["merely_mapped"]:
        add("- %s" % r)
    add("")
    add("Coverage. %s" % t["coverage_of_the_shall_list"])
    add("")
    add("Does the table add any requirement beyond the Section 6.5.3.1 shall? "
        "%s. It is purely a correspondence map."
        % ("Yes" if t["adds_requirement_beyond_6531_shall"] else "No"))
    add("")
    add("### Ambiguity, reported and not resolved")
    add("")
    add(t["ambiguity_reported_not_resolved"])
    add("")
    add("### Consequence for claim 3")
    add("")
    add(t["consequence_for_claim_3"])
    add("")
    add("## Extraction method and its reliability")
    add("")
    add(t["extraction"]["method"])
    add("")
    for r in t["extraction"]["readings"]:
        add("- %s" % r)
    add("")
    add("One reading disagreed and was resolved against the geometry. %s"
        % t["extraction"]["disagreeing_reading"])
    add("")
    add("Grid geometry, in %s:" % t["grid_geometry"]["units"])
    add("")
    add("- vertical rules at x = %s"
        % ", ".join("%.2f" % v for v in t["grid_geometry"]["vertical_rules_x"]))
    add("- horizontal rules at y = %s"
        % ", ".join("%.2f" % v for v in t["grid_geometry"]["horizontal_rules_y"]))
    add("")
    add(t["grid_geometry"]["note"])
    add("")
    add(t["extraction"]["reliability"])
    add("")
    add("Commands:")
    add("")
    add("```")
    add("curl -sSL -o _cache/air/IHE_RAD_Suppl_AIR_Rev1-3_TI_2025-08-08.pdf \\")
    add("     %s" % AIR["url"])
    add("pdftotext -table      -enc UTF-8 -f 82 -l 82 "
        "_cache/air/IHE_RAD_Suppl_AIR_Rev1-3_TI_2025-08-08.pdf -")
    add("pdftotext -lineprinter -enc UTF-8 -f 82 -l 82 "
        "_cache/air/IHE_RAD_Suppl_AIR_Rev1-3_TI_2025-08-08.pdf -")
    add("python scripts/pdf_table_geometry.py "
        "_cache/air/IHE_RAD_Suppl_AIR_Rev1-3_TI_2025-08-08.pdf 82")
    add("```")
    add("")
    add("The cached PDF is outside the repository and is not committed. Refetch "
        "it from the pinned URL and check the sha256 before rerunning.")
    add("")
    return "\n".join(L)


def write() -> list[str]:
    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / "standards.json"
    out.write_text(json.dumps({
        "edition": EDITION,
        "verified_on": VERIFIED_ON,
        "algorithm_identification_macro": ALGORITHM_IDENTIFICATION_MACRO,
        "withdrawn_tags": WITHDRAWN_TAGS,
        "segment_attributes": SEGMENT_ATTRIBUTES,
        "enhanced_general_equipment": ENHANCED_GENERAL_EQUIPMENT,
        "enhanced_general_equipment_iods": ENHANCED_GENERAL_EQUIPMENT_IODS,
        "reporting_grades": GRADES,
        "ihe_air": AIR,
    }, indent=2), encoding="utf-8")
    table = RESULTS / "ihe_air_table.md"
    table.write_text(air_table_markdown(), encoding="utf-8")
    return [str(out), str(table)]


def main(argv=None) -> int:
    for path in write():
        print("wrote %s" % path)

    S = dict(section="STD", section_title="Standard-level facts, verified",
             command=CMD, source_file="results/standards.json",
             validator="none, primary source reading",
             floor="not applicable, this section defines requirements rather "
                   "than quoting a rate",
             dropped="nothing, the full macro and module tables are encoded",
             verified_on=VERIFIED_ON)

    ledger.record_many([
        dict(id="STD-01", claim="The Algorithm Identification Macro has six "
             "attributes. Two tags used in the study brief were wrong and are "
             "withdrawn before any extractor was written.",
             status="VERIFIED",
             value="AlgorithmParameters is (0066,0032) not (0066,0033); "
                   "AlgorithmSource is (0024,0202) not (0066,0032). "
                   "(0066,0033) is not allocated anywhere in PS3.6 Chapter 6",
             sop_class="Segmentation Storage, Parametric Map Storage",
             external_source="%s section 10.16, Table 10-19" % EDITION,
             pinned_by_test="tests/test_standards.py::test_macro_tags",
             notes="An extraction built on the brief's tags would have scored "
                   "AlgorithmSource as absent on every object in the archive, "
                   "and the error would have looked like a finding.", **S),
        dict(id="STD-02", claim="SegmentationAlgorithmIdentificationSequence "
             "(0062,0007) is Type 3 in the Segmentation IOD, with no condition. "
             "A segment declaring SegmentAlgorithmType AUTOMATIC and omitting "
             "the sequence is conformant.",
             status="VERIFIED",
             value="Type 3, no condition, Segmentation Image Module Table "
                   "C.8.20-2. The 1C form exists only in the Height Map "
                   "Segmentation Image Module Table C.8.20-5, which Table "
                   "A.51-1 does not include in the Segmentation IOD",
             sop_class="Segmentation Storage",
             external_source="%s C.8.20.2 and C.8.20.5, and A.51" % EDITION,
             pinned_by_test="tests/test_standards.py::test_segmentation_hypothesis_is_dead",
             supersedes="STD-02-hyp",
             status_note="This kills the largest claim-1 result that was "
             "available. Recorded as a verified negative rather than dropped, "
             "because the hypothesis was attractive and would otherwise be "
             "reinvented.", **S),
        dict(id="STD-02-hyp", claim="Segmentation objects declaring "
             "SegmentAlgorithmType AUTOMATIC while omitting algorithm "
             "identification are non-conformant on a conditional requirement, "
             "which would be the largest claim-1 result available.",
             status="RETIRED",
             value="withdrawn before any object was scored",
             sop_class="Segmentation Storage",
             retired_reason="Refuted against %s. In the Segmentation IOD "
             "(0062,0007) is Type 3 with no condition attached, so omitting it "
             "is conformant and no validator can flag it. The condition the "
             "hypothesis relied on belongs to the Height Map Segmentation Image "
             "Module, a different module that the Segmentation IOD does not "
             "include." % EDITION,
             superseded_by="STD-02", **S),
        dict(id="STD-03", claim="Two conformance hooks survive in the "
             "Segmentation IOD and both are measurable.",
             status="VERIFIED",
             value="SegmentAlgorithmName (0062,0009) is Type 1C, required when "
                   "SegmentAlgorithmType is not MANUAL, compelling a free-text "
                   "string only; and a present (0062,0007) missing any of its "
                   "three Type 1 children, AlgorithmFamilyCodeSequence "
                   "(0066,002F), AlgorithmName (0066,0036) or AlgorithmVersion "
                   "(0066,0031), is non-conformant",
             sop_class="Segmentation Storage",
             external_source="%s Table C.8.20-2 and Table 10-19" % EDITION,
             derived_from="STD-02",
             pinned_by_test="tests/test_standards.py::test_surviving_hooks",
             status_note="The defensible measurement is the asymmetry: an "
             "absent sequence is conformant, a present but incomplete one is "
             "not. That is a claim about producers rather than about the "
             "standard.", **S),
        dict(id="STD-04", claim="Enhanced General Equipment is Mandatory in the "
             "Segmentation and Parametric Map IODs, making four equipment "
             "attributes Type 1 and third-party checkable.",
             status="VERIFIED",
             value="Manufacturer (0008,0070), ManufacturerModelName "
                   "(0008,1090), DeviceSerialNumber (0018,1000) and "
                   "SoftwareVersions (0018,1020), all Type 1, module Usage M in "
                   "Table A.51-1 and Table A.75-1",
             sop_class="Segmentation Storage, Parametric Map Storage",
             external_source="%s Table C.7-8b, A.51-1, A.75-1" % EDITION,
             pinned_by_test="tests/test_standards.py::test_enhanced_general_equipment",
             status_note="This is the primary yardstick for claim 3. An "
             "empty-or-absent rate on these four is a real conformance number, "
             "unlike a presence rate, which is 100 percent by construction.",
             **S),
        dict(id="STD-05", claim="Results are reported in three grades, never "
             "two: non-conformant, conformant but uninformative, and "
             "informative.",
             status="MEASURED",
             value="; ".join("%s: %s" % (k, v.split(".")[0]) for k, v in GRADES.items()),
             sop_class="all", derived_from="STD-02,STD-04",
             status_note="Two grades would score a gap in the standard as a "
             "failure by a producer. Most of what this study finds is expected "
             "to be grade 2, which is a statement about the standard.", **S),
        dict(id="STD-06", claim="IHE AIR imposes an unconditional shall on the "
             "Creator to populate ContributingEquipmentSequence, and it is "
             "actively tested. It is cited as a secondary yardstick, qualified "
             "by its Trial Implementation status.",
             status="VERIFIED",
             value="AIR Rev 1.3, 2025-08-08, Trial Implementation since "
                   "2020-07-16. Section 6.5.3.1 requires the Creator to encode "
                   "Purpose of Reference Code Sequence (109102, DCM, Processing "
                   "Equipment), Manufacturer, Manufacturer's Model Name, "
                   "Software Versions and Device UID. 22 Gazelle AIR test "
                   "definitions and 31 passing Connectathon records across five "
                   "events",
             sop_class="all",
             external_source=AIR["url"],
             pinned_by_test="tests/test_standards.py::test_air_is_normative_and_tested",
             supersedes="STD-06-untested",
             status_note="PS3.3 remains the primary yardstick because it is "
             "Final Text. AIR is secondary and its status is stated wherever it "
             "is cited. It cannot be cited as requiring TID 1004 or TID 4019 "
             "content items to exist: that clause uses will, and the "
             "consistency obligation applies only if the items are present.",
             **S),
        dict(id="STD-06-untested", claim="IHE AIR has no Connectathon test case "
             "and no Gazelle test plan, so it cannot carry a conformance claim.",
             status="RETIRED",
             value="withdrawn before publication",
             retired_reason="Refuted by primary sources. Gazelle Test "
             "Management holds 22 AIR test definitions with numbered steps and "
             "monitor instructions, and the IHE Connectathon results database "
             "returns 31 passing system and actor records for AIR across five "
             "consecutive events from 2022 to 2026. The Trial Implementation "
             "status is confirmed and is the part of the original claim that "
             "survives.",
             superseded_by="STD-06", **S),
    ])
    print("ledger: %s" % ledger.summary())
    return 0


if __name__ == "__main__":
    sys.exit(main())
