"""The measurement panel, fixed before the floor is measured.

Two axes, never merged into a single pass or fail.

**Axis 1, conformance.** Independent validators score an object against their
reading of the IOD. `dciodvfy` from dicom3tools, `dicom-validator` from pydicom,
`dcmpschk` from DCMTK for presentation states only, and PixelMed's
`DicomSRValidator` for structured reports. Disagreement between them is claim 2
and is data, not noise to be resolved.

**Axis 2, reference implementation parse.** The readers that consuming software
actually uses, asked to read the object. A refusal to parse is evidence of a
different kind from a validator complaint: it is what a user experiences. This
is the instrument the spine-gsps paper turned on, where `dcmp2pgm` produced zero
bytes while Orthanc and a clinical viewer accepted the same objects without
complaint.

Axis 2 is **asymmetric and informative only on failure.** dcmqi wrote 86 percent
of the objects this study measures, so dcmqi reading them back is a round trip
and not an independent test. If dcmqi cannot read objects dcmqi wrote, that is a
strong result. If it reads all of them, that establishes nothing about
conformance. The same applies with less force to highdicom. This asymmetry is
stated in Methods verbatim and the two axes are reported separately throughout.

Independence, declared rather than assumed:

- `dciodvfy` (dicom3tools), `dcmpschk` and `dcmp2pgm` (DCMTK), `dicom-validator`
  (pydicom), `highdicom`, `dcmqi` and PixelMed are seven codebases from five
  independent groups.
- `dcmpschk` and `dcmp2pgm` are both DCMTK, so a presentation state agreeing
  with itself across those two is one opinion, not two.
- `dciodvfy` and PixelMed are both David Clunie's work. They are separate
  codebases in different languages, but they are not independent authorship and
  the manuscript says so.
- The Aveiro validation service extends the dcm4che3 validator. If it is ever
  added, that shared codebase is declared or the agreement number inflates.

**It is not a four-tool panel and must never be described as one.** Coverage is
not uniform across SOP classes. Segmentation and the structured report classes
get three conformance tools, Parametric Map and RT Structure Set get two, and
the reference-parse axis ranges from one reader to three. PixelMed's
DicomInstanceValidator recognises seven IODs and only Segmentation is among the
nine classes here: on every other class it reports the IOD as unrecognized,
which is recorded as NOT CHECKED and never as passed. Methods carries the
per-class table rather than a single number, because a single number is the
easiest thing in the paper to falsify by opening the table.

This module defines the panel and captures its versions. The runners are
exercised in Phase 1, against known-good objects, to derive the floor per SOP
class before any archive object is scored.
"""
from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from . import paths


@dataclass(frozen=True)
class Tool:
    key: str
    name: str
    axis: str            # "conformance" or "reference_parse"
    provider: str        # the codebase, for the independence declaration
    binary: str | None   # attribute name on colophon.paths, or None for python
    invocation: str      # the exact command shape, pinned into the ledger
    note: str = ""


TOOLS: list[Tool] = [
    Tool("dciodvfy", "dciodvfy", "conformance", "dicom3tools", "DCIODVFY",
         "dciodvfy <file>",
         "No flags. Any added flag changes the comparison baseline and must be "
         "pinned as part of the command string."),
    Tool("dicom_validator", "dicom-validator", "conformance", "pydicom", None,
         "python -m dicom_validator.validate_iods <file>",
         "Its own README disclaims correctness and describes the package as a "
         "beta-stage proof of concept. Quoted in Methods."),
    Tool("dcmpschk", "dcmpschk", "conformance", "DCMTK", "DCMPSCHK",
         "dcmpschk <file>",
         "Presentation states only. One file per call: its verdict logic scans "
         "the whole output for a pass line, so a batched call reports pass if "
         "any single file passed."),
    Tool("pixelmed_sr", "PixelMed DicomSRValidator", "conformance", "PixelMed",
         "PIXELMED_JAR",
         "java -cp <pixelmed.jar> com.pixelmed.validate.DicomSRValidator <file>",
         "Structured reports only. In the IDC team's own SR release gate, so an "
         "audit of IDC SR that omits it uses a weaker instrument than its "
         "subject. Same author as dciodvfy: not independent authorship."),
    Tool("segimage2itkimage", "dcmqi segimage2itkimage", "reference_parse",
         "dcmqi", "SEGIMAGE2ITKIMAGE",
         "segimage2itkimage --inputDICOM <file> --outputDirectory <dir>",
         "Round trip for most of the corpus. Informative only on failure."),
    Tool("tid1500reader", "dcmqi tid1500reader", "reference_parse", "dcmqi",
         "TID1500READER",
         "tid1500reader --inputDICOM <file> --outputMetadata <json>",
         "TID 1500 structured reports. Informative only on failure."),
    Tool("paramap2itkimage", "dcmqi paramap2itkimage", "reference_parse",
         "dcmqi", "PARAMAP2ITKIMAGE",
         "paramap2itkimage --inputFileName <file> --outputDirectory <dir>",
         "Parametric Map. Informative only on failure."),
    Tool("highdicom_reader", "highdicom reader", "reference_parse", "highdicom",
         None, "highdicom.seg.segread / hd.sr.srread / pydicom.dcmread",
         "Fourth opinion. highdicom wrote about 2,000 of these objects, so it "
         "is a partial round trip for that subset only."),
    Tool("pixelmed_instance", "PixelMed DicomInstanceValidator", "conformance",
         "PixelMed", "PIXELMED_JAR",
         "java -cp <pixelmed.jar>;<lib/additional/commons-compress-1.12.jar>;"
         "<lib/additional/commons-codec-1.3.jar>;"
         "<lib/additional/saxon-he-12.5.jar>;"
         "<lib/additional/xmlresolver-5.2.2.jar> "
         "com.pixelmed.validate.DicomInstanceValidator <file>",
         "Recognises seven IODs, of which only Segmentation is in this study's "
         "population. On every other class it emits the free-text string "
         "IOD (SOP Class) unrecognized, which the harness records as NOT "
         "CHECKED and never as passed. Its shipped launcher script names "
         "saxon-he-11.5 and xmlresolver-4.6.4, which are not in the dependency "
         "release: the classpath above is the corrected one. com.pixelmed is "
         "absent from Maven Central entirely, so the jar is fetched from "
         "dclunie.com, hashed here, and archived with the release."),
    Tool("dsrdump", "DCMTK dsrdump", "reference_parse", "DCMTK", "DSRDUMP",
         "dsrdump +Pt +Pi <file>",
         "Structured report reader run with NO relaxation flags: -Er -Ev -Ec "
         "-Ee -Ei -Dv are all omitted deliberately. A nonzero exit is a "
         "relationship content constraint failure. No IDC pipeline has run "
         "this and PixelMed's template checker does not cover it, which makes "
         "it the SR arm's genuine novelty."),
    Tool("dcmp2pgm", "dcmp2pgm", "reference_parse", "DCMTK", "DCMP2PGM",
         "dcmp2pgm <presentation-state> <image> <output.pgm>",
         "Presentation state rendering. Same codebase as dcmpschk, so the two "
         "are one opinion for independence purposes."),
]

# Which tools apply to which SOP class. A tool that does not apply is recorded
# as not applicable rather than silently skipped, because an empty second
# opinion that reads as agreement is how a panel overstates its own breadth.
PANEL: dict[str, dict[str, list[str]]] = {
    "Segmentation Storage": {
        "conformance": ["dciodvfy", "dicom_validator", "pixelmed_instance"],
        "reference_parse": ["segimage2itkimage", "highdicom_reader"],
    },
    "Enhanced SR Storage": {
        "conformance": ["dciodvfy", "dicom_validator", "pixelmed_sr"],
        "reference_parse": ["tid1500reader", "dsrdump", "highdicom_reader"],
    },
    "Comprehensive SR Storage": {
        "conformance": ["dciodvfy", "dicom_validator", "pixelmed_sr"],
        "reference_parse": ["tid1500reader", "dsrdump", "highdicom_reader"],
    },
    "Comprehensive 3D SR Storage": {
        "conformance": ["dciodvfy", "dicom_validator", "pixelmed_sr"],
        "reference_parse": ["tid1500reader", "dsrdump", "highdicom_reader"],
    },
    "Parametric Map Storage": {
        "conformance": ["dciodvfy", "dicom_validator"],
        "reference_parse": ["paramap2itkimage", "highdicom_reader"],
    },
    "Grayscale Softcopy Presentation State Storage": {
        "conformance": ["dciodvfy", "dicom_validator", "dcmpschk"],
        "reference_parse": ["dcmp2pgm", "highdicom_reader"],
    },
    "RT Structure Set Storage": {
        "conformance": ["dciodvfy", "dicom_validator"],
        "reference_parse": ["highdicom_reader"],
    },
    "Key Object Selection Document Storage": {
        "conformance": ["dciodvfy", "dicom_validator"],
        "reference_parse": ["highdicom_reader"],
    },
    "Real World Value Mapping Storage": {
        "conformance": ["dciodvfy", "dicom_validator"],
        "reference_parse": ["highdicom_reader"],
    },
}

# Lineage, not tool count. Counting tool names overstates independence. What
# matters is how many unrelated codebases and authors are actually looking.
LINEAGES = {
    "dicom3tools": {"tools": ["dciodvfy"], "author": "David Clunie"},
    "PixelMed": {"tools": ["pixelmed_sr", "pixelmed_instance"],
                 "author": "David Clunie",
                 "note": "Separate codebase from dicom3tools, in a different "
                         "language, but the same author. Two PixelMed "
                         "validators plus dciodvfy are three tools and one "
                         "author, not three unrelated vendors."},
    "DCMTK": {"tools": ["dcmpschk", "dcmp2pgm", "dsrdump"],
              "author": "OFFIS",
              "note": "Three tools, one codebase, one opinion for independence "
                      "purposes."},
    "pydicom": {"tools": ["dicom_validator"], "author": "pydicom contributors"},
    "dcmqi": {"tools": ["segimage2itkimage", "tid1500reader", "paramap2itkimage"],
              "author": "QIICR",
              "note": "dcmqi's SEG reader is DCMTK DcmSegmentation, so for a "
                      "dcmqi-written SEG both dcmqi and any DCMTK reader are "
                      "round trips. The only independent reader left for that "
                      "population is highdicom."},
    "highdicom": {"tools": ["highdicom_reader"], "author": "highdicom contributors"},
}

# Where the panel is genuinely weak, stated in Methods rather than limitations.
WEAKNESSES = [
    {"scope": "reference parse of dcmqi-written Segmentation",
     "statement": "dcmqi's SEG reader is DCMTK DcmSegmentation, so both dcmqi "
                  "and any DCMTK reader are round trips for the 411,865 series "
                  "dcmqi wrote. The only independent reader is highdicom, which "
                  "in corruption testing silently accepted a dangling "
                  "ReferencedSegmentNumber, BINARY SegmentationType with "
                  "BitsAllocated=8, and NumberOfFrames=5 against 2 frames. The "
                  "reader axis for dcmqi-written SEG is weak and is reported as "
                  "weak.",
     "status": "corruption-testing result asserted in addendum 01, pending "
               "independent reproduction in Phase 1"},
    {"scope": "TID 1500 template conformance",
     "statement": "There is no second implementation anywhere. dicom-validator "
                  "has no Part 16 reader, dcm4che ships no SR IOD, DVTk has no "
                  "Comprehensive 3D SR definition, dcmqi tid1500reader only "
                  "warns and continues, and DCMTK's CMR library is write-side "
                  "with no CLI. If PixelMed says a TID 1500 report is "
                  "conformant, nothing can corroborate it. Template-layer "
                  "results are reported as single-opinion and never as "
                  "agreement.",
     "status": "asserted in addendum 01, pending confirmation"},
]

# Tools considered and excluded, with the reason. An excluded tool that leaves
# no trace reads as a tool nobody thought of.
EXCLUDED = [
    {
        "name": "dcm4che dcmvalidate",
        "axis": "conformance",
        "would_have_covered": "all classes, in principle",
        "reason": "Ships IOD definitions only for dicomdir, ct, mr, ct-dosesr "
                  "and xr-dosesr. Validating a Segmentation or a Comprehensive "
                  "3D SR would mean hand-authoring the IOD XML ourselves, which "
                  "is writing our own yardstick and is exactly the "
                  "self-adjudication this project forbids.",
        "consequence": "Not used. The rule that conformance is scored only by "
                       "third-party tools is what excludes it.",
    },
    {
        "name": "DVTk",
        "axis": "conformance",
        "would_have_covered": "SEG and older classes",
        "reason": "Windows only, and all 150 definition files are dated 2010. "
                  "No Comprehensive 3D SR definition and no Parametric Map "
                  "definition.",
        "consequence": "Not used. A 2010 definition set cannot score a 2024 "
                       "object against the edition it was written to.",
    },
    {
        "name": "IHE Gazelle EVS",
        "axis": "conformance",
        "would_have_covered": "all classes",
        "reason": "Wraps PixelMed and dicom3tools, both already in the panel. "
                  "It adds no independent opinion, only a web front end.",
        "consequence": "Not used. Including it would inflate the apparent size "
                       "of the panel without adding a lineage.",
    },
    {
        "name": "SimpleITK and GDCM",
        "axis": "reference_parse",
        "would_have_covered": "SEG and Parametric Map",
        "reason": "Parsed five deliberately corrupted Segmentation objects "
                  "without complaint, so they produce no signal on the failure "
                  "side, which is the only side axis 2 is informative on.",
        "consequence": "Not used. A reader that accepts everything cannot "
                       "distinguish anything.",
    },
    {
        "name": "pydicom-seg reader",
        "axis": "reference_parse",
        "would_have_covered": "Segmentation Storage, and a round trip for the "
                              "1,991 series that declare pydicom-seg",
        "reason": "pydicom-seg 0.4.1, its current release, imports "
                  "pydicom._storage_sopclass_uids, which pydicom removed in "
                  "version 3. It also pins numpy<2. Including it would mean "
                  "downgrading pydicom below 3.0.2, which is the version the "
                  "spine-gsps paper pinned, and cross-paper comparison depends "
                  "on that pin holding. Measured on 2026-08-01: import fails "
                  "with ModuleNotFoundError under pydicom 3.0.2.",
        "consequence": "Segmentation keeps two reference readers, dcmqi and "
                       "highdicom. The 1,991 pydicom-seg-written series are "
                       "read by those two instead of by their own writer, which "
                       "makes them one of the few subsets where axis 2 is not a "
                       "round trip.",
    },
    {
        "name": "Aveiro DICOM validation service",
        "axis": "conformance",
        "would_have_covered": "all SOP classes",
        "reason": "Extends the dcm4che3 validator. Adding it without declaring "
                  "the shared codebase would inflate the agreement number that "
                  "claim 2 reports.",
        "consequence": "Not used. If added later, the shared codebase is "
                       "declared and it is not counted as an independent "
                       "opinion.",
    },
]

BY_KEY = {t.key: t for t in TOOLS}


def panel_table() -> list[dict]:
    rows = []
    for sop, axes in PANEL.items():
        rows.append({
            "sop_class": sop,
            "n_conformance": len(axes["conformance"]),
            "conformance": ", ".join(BY_KEY[k].name for k in axes["conformance"]),
            "n_reference_parse": len(axes["reference_parse"]),
            "reference_parse": ", ".join(
                BY_KEY[k].name for k in axes["reference_parse"]),
        })
    return rows


def availability() -> list[dict]:
    """What is present today. Phase 1 cannot start on a class whose panel is
    incomplete, so this is checked rather than assumed."""
    out = []
    for tool in TOOLS:
        rec = {"key": tool.key, "name": tool.name, "axis": tool.axis,
               "provider": tool.provider, "invocation": tool.invocation}
        if tool.binary is None:
            rec["kind"] = "python package"
            rec["status"] = _python_status(tool.key)
        else:
            path = getattr(paths, tool.binary)
            rec["kind"] = "binary"
            rec["path"] = str(path)
            rec["status"] = "present" if Path(path).exists() else "MISSING"
            if rec["status"] == "present" and tool.binary != "PIXELMED_JAR":
                rec["version"] = paths.binary_version(_version_key(tool))
        out.append(rec)
    return out


def _version_key(tool: Tool) -> str:
    return {"DCIODVFY": "dciodvfy", "DCMPSCHK": "dcmpschk",
            "DCMP2PGM": "dcmp2pgm", "SEGIMAGE2ITKIMAGE": "segimage2itkimage",
            "TID1500READER": "tid1500reader",
            "PARAMAP2ITKIMAGE": "paramap2itkimage"}.get(tool.binary, tool.key)


def _python_status(key: str) -> str:
    import importlib.metadata as md
    package = {"dicom_validator": "dicom-validator",
               "highdicom_reader": "highdicom"}[key]
    try:
        return "present, %s %s" % (package, md.version(package))
    except Exception:
        return "MISSING"


def missing() -> list[str]:
    return [r["name"] for r in availability() if r["status"] == "MISSING"]


def describe() -> str:
    lines = ["Panel, %d tools across two axes" % len(TOOLS), ""]
    for rec in availability():
        lines.append("  %-28s %-16s %-14s %s"
                     % (rec["name"], rec["axis"], rec["provider"], rec["status"]))
    lines.append("")
    lines.append("Per SOP class:")
    for row in panel_table():
        lines.append("  %-46s conformance %d, reference parse %d"
                     % (row["sop_class"], row["n_conformance"],
                        row["n_reference_parse"]))
    gaps = missing()
    lines.append("")
    lines.append("missing: %s" % (", ".join(gaps) if gaps else "none"))
    return "\n".join(lines)


def write(path: Path | None = None) -> Path:
    out = path or (paths.RESULTS / "panel.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "axes": {
            "conformance": "independent validators scoring against the IOD",
            "reference_parse": "readers that consuming software uses, asked to "
                               "read the object. Asymmetric: informative only "
                               "on failure where the reader also wrote the "
                               "object.",
        },
        "never_merged": "The two axes are reported separately. A single pass or "
                        "fail combining them would hide which kind of evidence "
                        "produced it.",
        "tools": availability(),
        "panel_by_sop_class": panel_table(),
        "lineages": LINEAGES,
        "declared_weaknesses": WEAKNESSES,
        "excluded": EXCLUDED,
        "missing": missing(),
    }, indent=2), encoding="utf-8")
    return out


CMD = "python -m colophon.validate"


def record_ledger() -> None:
    from . import ledger

    avail = {r["key"]: r for r in availability()}
    dcmqi_version = avail["segimage2itkimage"].get("version", "unknown")
    S = dict(section="V", section_title="Panel design, fixed before Phase 1",
             command=CMD, source_file="results/panel.json",
             dropped="nothing, the full panel is enumerated including tools "
                     "considered and excluded",
             floor="not applicable, this row defines the instrument rather than "
                   "quoting a rate")

    ledger.record_many([
        dict(id="V-01", claim="The panel has two axes. Axis 1 is conformance, "
             "scored by independent validators. Axis 2 is reference "
             "implementation parse, where the readers consuming software "
             "actually uses are asked to read the object. The two are never "
             "merged into a single pass or fail.",
             status="MEASURED",
             value="9 tools, %d SOP classes, conformance 2 to 3 tools per class "
                   "and reference parse 1 to 2" % len(PANEL),
             sop_class="all", n="9",
             pinned_by_test="tests/test_panel.py::test_every_class_has_both_axes",
             status_note="Decision taken 2026-08-01, before the floor was "
             "measured, because a panel fixed after seeing results is not a "
             "panel. Adding a second conformance validator was rejected: few "
             "IOD validators exist for SEG, SR, RTSTRUCT and Parametric Map, "
             "and dicom-validator already fills that slot.",
             notes="The instrument comes from the spine-gsps result where "
                   "dcmp2pgm produced zero bytes on objects that Orthanc and a "
                   "clinical viewer accepted without complaint. A reference "
                   "implementation refusing to parse is evidence orthogonal to "
                   "a validator complaint.", **S),
        dict(id="V-02", claim="Axis 2 is asymmetric and informative only on "
             "failure, because dcmqi wrote most of the objects it will be asked "
             "to read.",
             status="MEASURED",
             value="dcmqi is declared on 411,865 of 481,750 derived series, "
                   "85.49 percent",
             sop_class="all", n="411,865", denominator="481,750",
             derived_from="C3-04,V-01",
             status_note="Stated in Methods verbatim. If dcmqi cannot read "
             "objects dcmqi wrote, that is a strong result. If it reads all of "
             "them, that establishes nothing about conformance. The same "
             "applies with less force to highdicom on about 2,000 series.",
             **S),
        dict(id="V-03", claim="PixelMed DicomSRValidator is in the panel for all "
             "structured report classes.",
             status="MEASURED",
             value="added to Enhanced SR, Comprehensive SR and Comprehensive 3D "
                   "SR, 270,409 series",
             sop_class="SR classes", n="270,409",
             status_note="Decision taken 2026-08-01. The IDC team validates its "
             "own SR with this tool, so an audit of IDC SR that omits it uses a "
             "weaker instrument than its subject.",
             notes="Not independent authorship: PixelMed and dciodvfy are both "
                   "David Clunie's work, separate codebases in different "
                   "languages. The manuscript says so rather than counting them "
                   "as two independent opinions.", **S),
        dict(id="V-04", claim="The PixelMed jar is not yet present in the pinned "
             "toolchain, so the SR conformance arm cannot run.",
             status="PENDING",
             value="pixelmed.jar MISSING; Temurin JRE 17.0.20 present",
             sop_class="SR classes",
             status_note="Blocks Phase 2 for SR only. Every other class can "
             "proceed. Logged rather than worked around, because running SR "
             "with three tools and reporting it as the four-tool panel would "
             "overstate the instrument.",
             notes="When acquired it is pinned by version string and sha256 like "
                   "every other binary.", **S),
        dict(id="V-05", claim="pydicom-seg is excluded from the panel and the "
             "reason is recorded.",
             status="MEASURED",
             value="excluded: imports pydicom._storage_sopclass_uids, removed in "
                   "pydicom 3; also pins numpy<2",
             sop_class="Segmentation Storage",
             status_note="Including it would mean downgrading pydicom below "
             "3.0.2, the version spine-gsps pinned, and cross-paper comparison "
             "depends on that pin holding. Import failure measured 2026-08-01.",
             notes="Consequence: the 1,991 series that declare pydicom-seg are "
                   "read by dcmqi and highdicom instead of by their own writer, "
                   "making them one of the few subsets where axis 2 is not a "
                   "round trip.", **S),
        dict(id="V-06", claim="Panel independence is declared rather than "
             "assumed. Two pairs share a codebase or an author.",
             status="VERIFIED",
             value="dcmpschk and dcmp2pgm are both DCMTK, one opinion not two; "
                   "dciodvfy and PixelMed share an author; the Aveiro service "
                   "extends dcm4che3 and is excluded on those grounds",
             sop_class="all",
             external_source="tool documentation and source provenance",
             verified_on="2026-08-01", **S),
        dict(id="V-07", claim="The dcmqi readers are pinned at the build "
             "installed in the toolchain.",
             status="MEASURED",
             value=dcmqi_version,
             sop_class="SEG, SR, Parametric Map",
             status_note="A standalone dcmqi 1.5.6 archive is also present in "
             "the tools tree and is unopened. The installed 1.5.4 build is "
             "pinned because it is the one that runs today. Override with "
             "COLOPHON_DCMQI_BIN and re-pin if that changes.", **S),
        dict(id="V-08", claim="The panel is not uniform across SOP classes and "
             "is never described as an N-tool panel.",
             status="MEASURED",
             value="; ".join("%s: conformance %d, reference parse %d"
                             % (r["sop_class"], r["n_conformance"],
                                r["n_reference_parse"])
                             for r in panel_table()),
             sop_class="all", n=str(len(TOOLS)),
             pinned_by_test="tests/test_panel.py::test_panel_is_not_uniform",
             status_note="Methods carries the per-class table. A single tool "
             "count is the easiest claim in the paper to falsify by opening "
             "that table.", **S),
        dict(id="V-09", claim="Every tool considered and excluded is listed "
             "with a stated reason and a stated consequence.",
             status="MEASURED",
             value="; ".join(e["name"] for e in EXCLUDED),
             sop_class="all", n=str(len(EXCLUDED)),
             pinned_by_test="tests/test_panel.py::test_excluded_tools_carry_a_reason_and_a_consequence",
             status_note="dcm4che dcmvalidate is excluded because supplying the "
             "missing SEG and SR IOD definitions would mean authoring our own "
             "yardstick, which is the self-adjudication this project forbids.",
             **S),
        dict(id="V-10", claim="Two parts of the panel are weak and are declared "
             "weak in Methods rather than in limitations.",
             status="PENDING",
             value="reference parse of dcmqi-written Segmentation, and TID 1500 "
                   "template conformance which has no second implementation",
             sop_class="Segmentation Storage, SR classes",
             status_note="dcmqi's SEG reader is DCMTK DcmSegmentation, so for "
             "dcmqi-written SEG the only independent reader is highdicom. The "
             "corruption-testing results behind this are asserted in addendum "
             "01 and are reproduced independently in Phase 1 before being "
             "printed.",
             notes="If PixelMed says a TID 1500 report is conformant, nothing "
                   "can corroborate it, so template-layer results are reported "
                   "as single-opinion and never as agreement.", **S),
        dict(id="PRE-02", claim="Writer-aware scoring. Every axis-2 result is "
             "labelled INDEPENDENT or ROUND-TRIP. A round-trip pass carries no "
             "information and is excluded from the pass numerator. A round-trip "
             "failure is a separate named category, self-inconsistency, and is "
             "the strongest available finding.",
             status="PENDING",
             value="pre-registered before any object was validated",
             sop_class="all", derived_from="W-01,V-02",
             status_note="Keeps dcmqi and DCMTK in the panel as failure-only "
             "detectors without ever crediting them with a pass. Writer "
             "identity comes from (0002,0013), (0018,A001) and (0008,0070), "
             "with the index-only census in W-01 as the provisional input.",
             **S),
        dict(id="PRE-03", claim="Claim 2 adjudication rule. Where validators "
             "disagree, the authors do not decide which is right. Direction is "
             "defined purely tool versus tool, and every reported disagreement "
             "class cites the specific PS3.3 or PS3.16 section and table under "
             "dispute.",
             status="PENDING",
             value="pre-registered before any object was validated",
             sop_class="all",
             external_source="PS3.3 and PS3.16, section and table cited per "
                             "disagreement class",
             status_note="Deciding who is right is self-adjudication, which is "
             "the one thing this project forbids outright.", **S),
        dict(id="PRE-04", claim="Standard-edition control. One edition is "
             "pinned, dicom-validator runs with a pre-seeded --standard-path, "
             "and a sensitivity analysis runs on at least one attribute known "
             "to have changed type across editions. Edition drift is not "
             "reported as non-conformance.",
             status="PENDING",
             value="ContentCreatorName (0070,0084) is the named sensitivity "
                   "attribute: Type 2 in older editions, Type 3 in 2026c",
             sop_class="all",
             external_source="PS3.3, edition pinned in results/environment.json",
             status_note="Objects in this archive were written between 2018 and "
             "2024 against the editions current at the time. dicom-validator "
             "validates against one edition and downloads part03.xml on first "
             "run, which also makes it fail behind an egress proxy unless the "
             "path is pre-seeded.", **S),
        dict(id="PRE-05", claim="Claim 1 threshold, set before the data. PRE-01 "
             "predicted a largely null result without a number. The number is "
             "fixed here, per object class, above floor.",
             status="PENDING",
             value="null is defined as a post-floor failure rate at or below 5 "
                   "percent of series in a class; substantial is defined as "
                   "above 20 percent; the band between is reported as "
                   "indeterminate and neither claim is made",
             sop_class="per class", derived_from="PRE-01",
             status_note="Chosen before any archive object was validated so the "
             "data can disagree with it. The floor from Phase 1 is subtracted "
             "before the threshold is applied.", **S),
        dict(id="PRE-06", claim="Sampling frame, fixed before seeing which "
             "strata look interesting.",
             status="PENDING",
             value="frame, allocation, target precision, seed and compute budget "
                   "to be written into this row before any Phase 3 fetch",
             sop_class="all",
             dropped="to be specified: this row is not closed until it names "
                     "what will not be sampled",
             status_note="18.72 TB means full-corpus opening is not happening. "
             "Stratification is by SOP class and analysis result, and the "
             "collection-level non-independence in C3-12 governs the allocation: "
             "an allocation proportional to series would be an allocation "
             "proportional to one analysis result.",
             **{k: v for k, v in S.items() if k != "dropped"}),
        dict(id="PRE-07", claim="Manual verification sample. The panel is "
             "entirely automated and claim 2 needs an anchor, so a stratified "
             "random sample of order 200 series is inspected by hand against "
             "the cited Part 3 or Part 16 text and published as a supplement.",
             status="PENDING",
             value="order 200 series, stratified by object class, writing "
                   "toolkit and disagreement class, seed recorded",
             sop_class="all", derived_from="PRE-03",
             status_note="Published so a reader can check the panel rather than "
             "trust it.", **S),
        dict(id="PRE-01", claim="Pre-registered prediction. Claim 1 will return "
             "largely null: SR will pass cleanly because IDC validates its own "
             "SR with PixelMed, and SEG will pass cleanly because dcmqi wrote "
             "it. That is the control that makes claim 3 land, not a failure of "
             "the study.",
             status="PENDING",
             value="predicted before any archive object was validated",
             sop_class="all",
             command=CMD, source_file="results/panel.json",
             floor="to be established in Phase 1, per SOP class",
             dropped="nothing, this is a prediction over the full Phase 2 and 3 "
                     "population",
             section="PRE", section_title="Pre-registered interpretation",
             status_note="Recorded 2026-08-01, before Phase 1 emitted a single "
             "object and before any IDC object was fetched. If claim 1 returns "
             "null this row is the evidence that the interpretation was a "
             "prediction and not a rescue written afterwards.",
             notes="The sentence the paper will carry: these objects are "
                   "syntactically impeccable, validated by the archive's own "
                   "tooling, and still cannot tell you what algorithm produced "
                   "them. If instead claim 1 returns a substantial failure rate, "
                   "this row is wrong and stays in the ledger as a wrong "
                   "prediction."),
    ])


def main(argv=None) -> int:
    print(describe())
    out = write()
    print("\nwrote %s" % out)
    record_ledger()
    from . import ledger
    print("ledger: %s" % ledger.summary())
    return 0


if __name__ == "__main__":
    sys.exit(main())
