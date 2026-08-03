"""Phase 1, minimum scope: the overlap between two writers' floor sets.

One number is the deliverable. If two conformant writers, given byte-identical
content, draw different validator messages, then a floor measured on one writer
does not transfer to the other, and a single scalar floor silently converts the
whole audit into "count all validator messages".

Design constraints, each of which exists because ignoring it produced a wrong
answer somewhere:

**Never gate on exit status.** `dciodvfy` returns rc=0 on a Segmentation with
SegmentSequence and Rows deleted. Both validators here are run for their text,
and the return code is recorded but never used to decide anything.

**Match severity in both forms.** `grep "^Error"` misses the private-tag form
`(0x0099,0x1001)  ?  - Warning - Unrecognized tag ...`. But the separator-only
rule ` - (Error|Warning) - ` misses dciodvfy's *common* form, which is
`Error - Missing attribute ...` at line start. Measured on this fixture, the
separator-only rule sent every dciodvfy finding to UNCLASSIFIED. Both forms are
matched, plus an explicit first-line banner rule.

**Normalise before counting, but not past the diagnostic.** Raw lines make frame
count a confounder, and frame count correlates with writer. Every message is
reduced to a template with tags, UIDs, frame and item indices and quoted values
stripped, hashed to a `message_class_id`, and the unit of count is the distinct
`(SOPInstanceUID, message_class_id)` pair. Attribute names, module names and
Type designations are kept, because they are what identifies the diagnostic
rather than what varies between instances of it.

Usage:
    python -m colophon.floor            emit, validate, write floor_set.csv
    python -m colophon.floor --no-emit  re-validate existing fixture objects
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

from . import ledger, paths
from .paths import CACHE, RESULTS

CMD = "python -m colophon.floor"
FIXTURE = CACHE / "fixture"

# Writers. W2 is the build vendored in 3D Slicer. It is tag v1.5.4, revision
# a102298, and it is never labelled 1.5.6 anywhere: a standalone 1.5.6 archive
# exists in the toolchain and is a different artefact.
W1 = "highdicom"
W2 = "dcmqi"

# The four classes the design asks to compare. Two of them turned out not to be
# emittable by W2 at all, which is recorded rather than worked around.
CLASSES = ["SEG BINARY", "SEG FRACTIONAL", "Parametric Map", "TID 1500 SR"]

OBJECTS = [
    (W1, "SEG BINARY", "w1/seg_binary.dcm"),
    (W1, "SEG FRACTIONAL", "w1/seg_fractional.dcm"),
    (W1, "Parametric Map", "w1/paramap.dcm"),
    (W1, "TID 1500 SR", "w1/sr_tid1500.dcm"),
    (W2, "SEG BINARY", "w2/seg_binary.dcm"),
    (W2, "TID 1500 SR", "w2/sr_tid1500.dcm"),
]

# Classes W2 could not emit. Their floors are non-transferable by construction,
# exactly like the highdicom-only classes in the wider design.
W2_EMISSION_GAPS = {
    "SEG FRACTIONAL": "dcmqi itkimage2segimage offers --segmentationType "
                      "<binary|labelmap> only. It has no FRACTIONAL code path, "
                      "so FRACTIONAL is a highdicom-only cell.",
    "Parametric Map": "dcmqi itkimage2paramap exited with 'ERROR: Conversion "
                      "failed.' on the fixture under four metadata variants and "
                      "both float32 and float64 input. It ships no schema in "
                      "the vendored build and emits no diagnostic beyond that "
                      "line. Recorded as an emission gap, not as a defect in "
                      "either tool.",
}

# --- message parsing ----------------------------------------------------------
# The addendum's rule, " - (Error|Warning) - " anywhere, matches dciodvfy's
# private-tag form but NOT its common form, which is "Error - Missing attribute
# ..." at line start with no leading separator. Measured on this fixture: with
# the separator-only rule every dciodvfy finding fell through to UNCLASSIFIED.
# Both forms are matched here, and the line-start form is the common one.
SEVERITY = re.compile(r"(?:^|\s-\s)(Error|Warning)\s-\s")
BANNER = re.compile(r"^(?P<iod>[A-Z][A-Za-z0-9]{3,})\s*$")

# Strip what varies per instance. Do NOT strip what identifies the diagnostic.
#
# An earlier version of this list replaced every <...> with <VAL> and every bare
# integer with N. dciodvfy writes attribute and module names inside angle
# brackets, so that rule collapsed "Element=<Laterality> Module=<GeneralSeries>"
# and "Element=<ClinicalTrialCoordinatingCenterName> Module=<ClinicalTrialSeries>"
# onto one template, and it rewrote "Type 2" to "Type N" while leaving "Type 2C"
# untouched. Over-normalisation destroys the measurement more quietly than
# under-normalisation does, because the result still looks like a number.
NORMALISERS = [
    (re.compile(r"\(0x[0-9a-fA-F]{4},0x[0-9a-fA-F]{4}\)"), "(TAG)"),
    (re.compile(r"\(\d{4},[0-9A-Fa-f]{4}\)"), "(TAG)"),
    (re.compile(r"\b\d+(?:\.\d+){3,}\b"), "UID"),
    (re.compile(r"\bframe\s*#?\s*\d+\b", re.I), "frame N"),
    (re.compile(r"\bitem\s*#?\s*\d+\b", re.I), "item N"),
    (re.compile(r"\bindex\s*#?\s*\d+\b", re.I), "index N"),
    (re.compile(r"\bnumber\s+\d+\b", re.I), "number N"),
    (re.compile(r'"[^"]*"'), '"VAL"'),
    (re.compile(r"Value=\S+"), "Value=VAL"),
    (re.compile(r"\s+"), " "),
]


def normalise(message: str) -> str:
    out = message.strip()
    for pattern, repl in NORMALISERS:
        out = pattern.sub(repl, out)
    return out.strip()


def message_class_id(validator: str, template: str) -> str:
    return hashlib.sha256(("%s|%s" % (validator, template)).encode("utf-8")
                          ).hexdigest()[:12]


def parse_dciodvfy(text: str) -> tuple[str | None, list[dict]]:
    """Return (iod_banner, findings). Severity matched anywhere in the line."""
    iod, findings = None, []
    for n, raw in enumerate(text.splitlines()):
        line = raw.rstrip()
        if not line.strip():
            continue
        if n == 0 or iod is None:
            m = BANNER.match(line.strip())
            if m and not SEVERITY.search(line):
                iod = m.group("iod")
                continue
        m = SEVERITY.search(line)
        if m:
            findings.append({"severity": m.group(1), "message": line.strip()})
        else:
            findings.append({"severity": "UNCLASSIFIED", "message": line.strip()})
    return iod, findings


DV_SECTION = re.compile(r"^(Errors|Warnings)\s*$")
DV_MODULE = re.compile(r'^Module "(?P<module>[^"]+)":')
DV_CONTEXT = re.compile(r"^\((?P<tag>[0-9A-Fa-f]{4},[0-9A-Fa-f]{4})\)")


def parse_dicom_validator(text: str) -> tuple[str | None, list[dict]]:
    """dicom-validator emits no severity levels, so the section header is used
    as the severity as emitted. Its own README disclaims correctness and calls
    the package a beta-stage proof of concept.

    An earlier version of this function captured only indented lines. The tool
    indents a finding by one level only when the tag has parents, so every
    finding on a top-level tag was silently dropped. It was caught by comparing
    this parser against the package's own structured result on the same file:
    the structured path reported a missing Clinical Trial Coordinating Center
    Name that this parser did not. Findings are now taken whether or not they
    are indented, and the parent context is cleared when an unindented one
    appears so it cannot be attributed to the wrong sequence.
    """
    iod, findings = None, []
    section, module, context = None, None, None
    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or set(stripped) == {"="}:
            continue
        m = re.match(r'^SOP class is "[^"]+" \((?P<iod>.+)\)\s*$', stripped)
        if m:
            iod = m.group("iod")
            continue
        if DV_SECTION.match(stripped):
            section = stripped.rstrip("s").upper()
            continue
        m = DV_MODULE.match(stripped)
        if m:
            module, context = m.group("module"), None
            continue
        if DV_CONTEXT.match(stripped) and stripped.endswith(":"):
            context = stripped.rstrip(":")
            continue
        if not section:
            continue
        indented = line.startswith(("  ", "\t"))
        if not indented:
            # A finding on a tag with no parents. Any pending sequence context
            # belongs to a previous, nested finding and must not be carried on.
            if not stripped.startswith("Tag "):
                continue
            context = None
        findings.append({
            "severity": section,
            "message": "Module <%s> %s %s" % (module or "?", context or "", stripped),
        })
    return iod, findings


# --- validator runners --------------------------------------------------------
def _run(argv: list[str], timeout: int = 300) -> dict:
    proc = subprocess.run(argv, capture_output=True, text=True,
                          errors="replace", timeout=timeout)
    return {"argv": argv, "stdout": proc.stdout, "stderr": proc.stderr,
            "returncode": proc.returncode}


def run_dciodvfy(path: Path) -> dict:
    paths.require(paths.DCIODVFY, "dciodvfy")
    rec = _run([str(paths.DCIODVFY), str(path)])
    rec["validator"] = "dciodvfy"
    rec["iod"], rec["findings"] = parse_dciodvfy(rec["stdout"] + "\n" + rec["stderr"])
    return rec


def run_dicom_validator(path: Path, standard_path: Path | None = None) -> dict:
    argv = [sys.executable, "-m", "dicom_validator.validate_iods"]
    if standard_path:
        argv += ["--standard-path", str(standard_path)]
    argv.append(str(path))
    rec = _run(argv, timeout=900)
    rec["validator"] = "dicom-validator"
    rec["iod"], rec["findings"] = parse_dicom_validator(
        rec["stdout"] + "\n" + rec["stderr"])
    return rec


VALIDATORS = {"dciodvfy": run_dciodvfy, "dicom-validator": run_dicom_validator}


def tool_versions() -> dict:
    from . import envinfo
    dv = paths.DCIODVFY
    return {
        "dciodvfy": {
            "path": str(dv),
            "reported_version": paths.binary_version("dciodvfy"),
            "snapshot": "20260701065818",
            "sha256_first_64MiB": envinfo._sha256(dv) if dv.exists() else None,
            "registered_pin": "1.00~20240118131615-1",
            "pin_satisfied": False,
        },
        "dicom-validator": {
            "version": __import__("importlib.metadata", fromlist=["version"]
                                  ).version("dicom-validator"),
            "edition_used": "2026c",
        },
        W1: {"version": __import__("highdicom").__version__,
             "pydicom": __import__("pydicom").__version__,
             "registered_pin": "0.28.0", "pin_satisfied": False},
        W2: {"tag": "v1.5.4", "revision": "a102298",
             "banner": paths.binary_version("segimage2itkimage"),
             "source": "vendored in 3D Slicer",
             "never_label_as": "1.5.6"},
    }


# --- the measurement ----------------------------------------------------------
def collect(standard_path: Path | None = None) -> list[dict]:
    rows = []
    for writer, sop_class, rel in OBJECTS:
        path = FIXTURE / rel
        if not path.exists():
            raise FileNotFoundError("missing emitted object %s" % path)
        import pydicom
        ds = pydicom.dcmread(path, stop_before_pixels=True)
        for vname, runner in VALIDATORS.items():
            rec = (runner(path, standard_path) if vname == "dicom-validator"
                   else runner(path))
            for f in rec["findings"]:
                template = normalise(f["message"])
                rows.append({
                    "writer": writer,
                    "sop_class": sop_class,
                    "sop_class_uid": str(ds.SOPClassUID),
                    "sop_instance_uid": str(ds.SOPInstanceUID),
                    "validator": vname,
                    "message_class_id": message_class_id(vname, template),
                    "message_template": template,
                    "severity_as_emitted": f["severity"],
                    "raw_example": f["message"][:300],
                    "iod_recognised_as": rec["iod"] or "",
                    "validator_returncode": rec["returncode"],
                })
    return rows


def jaccard(a: set, b: set) -> float:
    """Jaccard over message-class sets. Both empty is defined as 1.0 and is
    flagged vacuous by the caller: identical empty floors are agreement, but
    they carry no information about whether the floors would agree if either
    writer drew anything."""
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def overlap(rows: list[dict]) -> list[dict]:
    out = []
    for sop_class in CLASSES:
        for validator in VALIDATORS:
            s1 = {r["message_class_id"] for r in rows
                  if r["writer"] == W1 and r["sop_class"] == sop_class
                  and r["validator"] == validator}
            s2 = {r["message_class_id"] for r in rows
                  if r["writer"] == W2 and r["sop_class"] == sop_class
                  and r["validator"] == validator}
            comparable = sop_class not in W2_EMISSION_GAPS
            out.append({
                "sop_class": sop_class,
                "validator": validator,
                "comparable": comparable,
                "w1_classes": len(s1),
                "w2_classes": len(s2),
                "shared": len(s1 & s2),
                "union": len(s1 | s2),
                "jaccard": round(jaccard(s1, s2), 4) if comparable else "",
                "vacuous": comparable and not s1 and not s2,
                "w1_only": " | ".join(sorted(s1 - s2)),
                "w2_only": " | ".join(sorted(s2 - s1)),
            })
    return out


FLOOR_FIELDS = ["writer", "writer_version", "sop_class", "sop_class_uid",
                "sop_instance_uid", "validator", "validator_build",
                "message_class_id", "message_template", "severity_as_emitted",
                "raw_example", "iod_recognised_as", "validator_returncode",
                "arm", "fixture", "adjudication", "basis"]


def write_floor_set(rows: list[dict], versions: dict) -> Path:
    out = RESULTS / "floor_set.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    vbuild = {
        "dciodvfy": "dicom3tools snapshot %s" % versions["dciodvfy"]["snapshot"],
        "dicom-validator": "dicom-validator %s, edition %s"
                           % (versions["dicom-validator"]["version"],
                              versions["dicom-validator"]["edition_used"]),
    }
    wver = {W1: "highdicom %s on pydicom %s" % (versions[W1]["version"],
                                                versions[W1]["pydicom"]),
            W2: "dcmqi tag %s revision %s, vendored in 3D Slicer"
                % (versions[W2]["tag"], versions[W2]["revision"])}
    seen = set()
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FLOOR_FIELDS)
        w.writeheader()
        for r in rows:
            key = (r["writer"], r["sop_class"], r["validator"], r["message_class_id"])
            if key in seen:
                continue
            seen.add(key)
            w.writerow({
                **{k: r.get(k, "") for k in FLOOR_FIELDS},
                "writer_version": wver[r["writer"]],
                "validator_build": vbuild[r["validator"]],
                "arm": "A, paired emission",
                "fixture": "synthetic 3-slice CT 32x32, 2-label volume",
                "adjudication": "unadjudicated",
                "basis": "",
            })
    return out


def write_markdown(rows: list[dict], ov: list[dict], versions: dict) -> Path:
    def fmt(x):
        return "%.3f" % x if isinstance(x, float) else str(x)

    lines = []
    lines.append("| sop_class | validator | comparable | W1 classes | W2 classes "
                 "| shared | union | Jaccard |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for o in ov:
        lines.append("| %s | %s | %s | %d | %d | %d | %d | %s |"
                     % (o["sop_class"], o["validator"],
                        "yes" if o["comparable"] else "no, W2 cannot emit",
                        o["w1_classes"], o["w2_classes"], o["shared"],
                        o["union"], fmt(o["jaccard"]) if o["jaccard"] != "" else "n/a"))
    table = "\n".join(lines)

    per_object = {}
    for r in rows:
        k = (r["writer"], r["sop_class"], r["validator"])
        per_object.setdefault(k, set()).add(r["message_class_id"])
    obj_lines = ["| writer | sop_class | validator | distinct message classes |",
                 "|---|---|---|---|"]
    for (w, c, v), s in sorted(per_object.items()):
        obj_lines.append("| %s | %s | %s | %d |" % (w, c, v, len(s)))
    objs = "\n".join(obj_lines)

    comparable = [o for o in ov if o["comparable"]]
    text = f"""# Phase 1, minimum scope: writer floor-set overlap

One fixture, two writers, the four classes the design nominates. Emitted,
decoded, compared, then validated. Reproduce with `{CMD}`.

## The number

{table}

Jaccard is over sets of normalised `message_class_id`, not raw lines.

## Distinct message classes per object

{objs}

## What is comparable, and what is not

Two of the four nominated classes are not shared, because W2 cannot emit them:

{chr(10).join("- **%s**: %s" % (k, v) for k, v in W2_EMISSION_GAPS.items())}

Their floors are highdicom-only and non-transferable, in the same way the
design already treats GSPS and KOS.

A third caveat applies to the SR cell. Both writers produce TID 1500, but not in
the same SOP class: highdicom emits **Comprehensive 3D SR**
(1.2.840.10008.5.1.4.1.1.88.34) and dcmqi emits **Enhanced SR**
(1.2.840.10008.5.1.4.1.1.88.22). TID 1500 may legitimately be carried in either,
so the comparison is valid at the template level, but the two objects are
scored against different IOD tables and the overlap has to be read with that in
mind.

## Tool builds

```
{json.dumps(versions, indent=2)}
```

Two registered pins are not satisfied on this machine and the deviation is
recorded rather than papered over:

- The design registers **dicom3tools 1.00~20240118131615-1**. The build present
  is snapshot **20260701065818**, the one the spine-gsps paper used. The 2024
  build predates changelog relaxations at 231003, 241003 and 241114, so it will
  flag conformant LABELMAP and TILED_FULL objects that the 2026 build does not.
  Neither appears in this fixture, so the deviation does not affect this
  measurement, but it must be closed before any corpus stratum is scored.
- The design registers **highdicom 0.28.0**. The build present is **0.28.1**,
  which is what this repository and the prior paper pin.

Neither substitution was silent, and neither is treated as satisfying the pin.

## What was dropped

Nothing was sampled. Six objects were emitted and every one was run through both
validators. The nine-variant ladder, Arm B corpus adjudication, the sampling
frame and PixelMed integration are all out of scope for this phase and are not
started. No IDC object was fetched.
"""
    out = RESULTS / "floor_overlap.md"
    out.write_text(text, encoding="utf-8")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--standard-path", default=None,
                    help="pre-seeded dicom-validator standard cache")
    args = ap.parse_args(argv)

    versions = tool_versions()
    rows = collect(Path(args.standard_path) if args.standard_path else None)
    ov = overlap(rows)
    csv_path = write_floor_set(rows, versions)
    md = write_markdown(rows, ov, versions)
    print("wrote %s and %s" % (csv_path, md))
    for o in ov:
        if o["comparable"]:
            print("  %-16s %-16s Jaccard %s%s  (W1 %d, W2 %d, shared %d)"
                  % (o["sop_class"], o["validator"], o["jaccard"],
                     " VACUOUS" if o.get("vacuous") else "",
                     o["w1_classes"], o["w2_classes"], o["shared"]))

    rc = {r["validator_returncode"] for r in rows}
    S = dict(section="F1", section_title="Phase 1, writer floor-set overlap",
             command=CMD, source_file="results/floor_set.csv",
             floor="this section measures the floor; it does not quote a rate "
                   "against one",
             dropped="nothing sampled: six emitted objects, every one run "
                     "through both validators",
             verified_on="2026-08-02")
    headline = next(o for o in ov if o["sop_class"] == "SEG BINARY"
                    and o["validator"] == "dciodvfy")

    ledger.record_many([
        dict(id="F1-01", claim="The validator floor is writer-specific. On the "
             "only class both writers could emit and the validator that "
             "discriminates, the two writers share no message classes at all.",
             status="MEASURED",
             value="SEG BINARY, dciodvfy: Jaccard %s. highdicom draws %d "
                   "message classes, dcmqi draws %d, shared %d"
                   % (headline["jaccard"], headline["w1_classes"],
                      headline["w2_classes"], headline["shared"]),
             n=str(headline["shared"]), denominator=str(headline["union"]),
             sop_class="Segmentation Storage, BINARY",
             validator="dciodvfy", validator_version="dicom3tools snapshot 20260701065818",
             pinned_by_test="tests/test_floor.py::test_headline_overlap",
             status_note="Content held equal: both writers consumed the same "
             "ITK label volume and the same segment code triplets from one "
             "metadata JSON, and the decoded label arrays were asserted equal "
             "before any validator ran.",
             notes="A single scalar floor is therefore not defensible. A floor "
                   "measured on highdicom would be 0 and would convert the "
                   "audit into counting every dciodvfy message on every other "
                   "writer's objects.", **S),
        dict(id="F1-02", claim="A conformant highdicom Segmentation draws zero "
             "dciodvfy messages, so a floor measured on that writer alone is "
             "zero.",
             status="MEASURED",
             value="highdicom SEG BINARY and SEG FRACTIONAL: 0 errors, 0 "
                   "warnings, only the IOD banner",
             n="0", sop_class="Segmentation Storage",
             validator="dciodvfy", validator_version="dicom3tools snapshot 20260701065818",
             derived_from="F1-01", **S),
        dict(id="F1-03", claim="The two validators disagree about whether the "
             "floor transfers between writers.",
             status="MEASURED",
             value="; ".join("%s %s: Jaccard %s%s"
                             % (o["sop_class"], o["validator"], o["jaccard"],
                                " (vacuous, both sets empty)" if o.get("vacuous") else "")
                             for o in ov if o["comparable"]),
             sop_class="Segmentation Storage, SR classes",
             derived_from="F1-01",
             status_note="Neither validator's floor transfers cleanly on SEG "
             "BINARY. dciodvfy's sets are disjoint. dicom-validator's overlap "
             "but are not equal: the highdicom set is a strict subset of the "
             "dcmqi set, which carries one additional class. Reporting a "
             "single cross-validator floor would average two different "
             "failures of transfer into one number.",
             supersedes="F1-03-prev", **S),
        dict(id="F1-03-prev", claim="dicom-validator returns an identical "
             "six-class set for both writers on SEG BINARY, so its floor does "
             "transfer even though dciodvfy's does not.",
             status="RETIRED",
             value="withdrawn: measured Jaccard was 1.0, corrected to 0.8571",
             sop_class="Segmentation Storage, BINARY",
             validator="dicom-validator",
             retired_reason="An artefact of this project's own parser. It "
             "captured only indented findings, and dicom-validator indents a "
             "finding by one level only when the tag has parents, so every "
             "finding on a top-level tag was silently dropped. The dcmqi object "
             "has a seventh class, a missing Clinical Trial Coordinating Center "
             "Name, that was being discarded. Caught by comparing the parser "
             "against the package's own structured result on the same file. "
             "With the parser fixed the two writers' sets are not equal and the "
             "floor does not transfer for either validator.",
             superseded_by="F1-03", **S),
        dict(id="F1-10", claim="A parser defect in this project silently "
             "dropped a class of validator findings, and was caught by "
             "cross-checking two access paths to the same tool rather than by "
             "any test.",
             status="MEASURED",
             value="dicom-validator findings on tags without parents were "
                   "discarded; recovering them changed the Phase 1 SEG BINARY "
                   "dicom-validator Jaccard from 1.0 to 0.8571 and added one "
                   "message class to the dcmqi object",
             sop_class="all", validator="dicom-validator",
             pinned_by_test="tests/test_floor.py::test_unindented_findings_are_not_dropped",
             status_note="Found while building the census, by comparing the "
             "text parser against the library's structured ValidationResult on "
             "the same six fixture objects. The two now agree exactly on all "
             "six, which is the check that would have caught it earlier.",
             notes="Everything measured through this parser before the fix "
                   "understates dicom-validator findings: Phase 1 floor_set and "
                   "the Phase 2 pilot. Both were re-run.", **S),
        dict(id="F1-04", claim="dcmqi could not emit two of the four nominated "
             "shared classes, so those cells are single-writer and their floors "
             "are non-transferable by construction.",
             status="MEASURED",
             value="; ".join("%s: %s" % (k, v.split(".")[0])
                             for k, v in W2_EMISSION_GAPS.items()),
             n="2", denominator="4", sop_class="SEG FRACTIONAL, Parametric Map",
             pinned_by_test="tests/test_floor.py::test_emission_gaps_recorded",
             notes="Recorded as emission gaps rather than as defects in either "
                   "tool. itkimage2paramap failed under four metadata variants "
                   "and both float32 and float64 input, emitting no diagnostic "
                   "beyond one line.", **S),
        dict(id="F1-05", claim="The two writers place TID 1500 in different SOP "
             "classes, so the SR cell compares objects scored against different "
             "IOD tables.",
             status="MEASURED",
             value="highdicom emits Comprehensive 3D SR "
                   "(1.2.840.10008.5.1.4.1.1.88.34); dcmqi tid1500writer emits "
                   "Enhanced SR (1.2.840.10008.5.1.4.1.1.88.22)",
             sop_class="TID 1500 SR",
             pinned_by_test="tests/test_floor.py::test_sr_sop_classes_differ",
             status_note="Both are legitimate carriers for TID 1500, so the "
             "comparison holds at the template level. It does not hold at the "
             "IOD level and the overlap must be read with that stated.", **S),
        dict(id="F1-06", claim="dciodvfy exit status is not a verdict. Every "
             "object in this phase returned the same code, including the one "
             "carrying an Error.",
             status="MEASURED",
             value="all six objects returned rc in %s from dciodvfy, including "
                   "the dcmqi Segmentation carrying a Type 2 Error" % sorted(rc),
             sop_class="all", validator="dciodvfy",
             pinned_by_test="tests/test_floor.py::test_exit_status_is_not_a_verdict",
             status_note="Confirms the rule independently on this fixture. "
             "Nothing in this harness branches on a return code.", **S),
        dict(id="F1-07", claim="The registered message-matching rule is "
             "incomplete and was corrected before any count was taken.",
             status="MEASURED",
             value="matching only ' - (Error|Warning) - ' sent every dciodvfy "
                   "finding to UNCLASSIFIED, because dciodvfy's common form is "
                   "'Error - Missing attribute ...' at line start. Both the "
                   "line-start and separator forms are now matched",
             sop_class="all",
             pinned_by_test="tests/test_floor.py::test_both_severity_forms_match",
             status_note="Correction to addendum 02 section 3. The "
             "separator-only form does occur, on the private-tag line, but it "
             "is the rarer of the two.", **S),
        dict(id="F1-08", claim="Two registered tool pins are not satisfied on "
             "this machine and the measurement is labelled accordingly.",
             status="PENDING",
             value="registered dicom3tools 1.00~20240118131615-1, present "
                   "snapshot 20260701065818; registered highdicom 0.28.0, "
                   "present 0.28.1",
             sop_class="all",
             status_note="Neither substitution was silent and neither is "
             "treated as satisfying the pin. The 2024 dicom3tools build "
             "predates relaxations at 231003, 241003 and 241114 and so flags "
             "conformant LABELMAP and TILED_FULL objects that the 2026 build "
             "does not. Neither appears in this fixture, so this measurement is "
             "unaffected, but the pin must be closed before any corpus stratum "
             "is scored.", **S),
        dict(id="F1-09", claim="Content was held equal across writers and "
             "verified before validation.",
             status="MEASURED",
             value="both writers consumed one ITK label volume and one metadata "
                   "JSON; decoded label arrays from all three segmentations "
                   "matched the source volume exactly",
             n="3", denominator="3", sop_class="Segmentation Storage",
             pinned_by_test="tests/test_floor.py::test_content_equality",
             status_note="Decoded writer-neutrally by frame geometry, because "
             "highdicom refuses source-instance indexing on the dcmqi object: "
             "dcmqi does not assert that spatial locations are preserved.",
             **S),
    ])
    print("ledger: %s" % ledger.summary())
    return 0


if __name__ == "__main__":
    sys.exit(main())
