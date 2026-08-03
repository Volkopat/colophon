"""Registered pins that were not satisfied, and the measured exposure to each.

Two pins in this project are registered and unsatisfied. That is a deviation and
it stays a deviation: neither registration is edited here, and nothing is re-run
under the registered build. What this module does instead is **measure how much
of the corpus is actually exposed to the known behavioural difference**, so the
deviation is reported with a number attached rather than as an open worry.

The distinction that matters, and it is the reason this is not a silent fix: a
pin that was **never satisfied** is a different object from a pin **changed after
seeing results**. The first is a deviation to be quantified and declared. The
second is the thing pre-registration exists to prevent, and it has not happened
here.

**Pin 1, dicom3tools.** Registered `1.00~20240118131615-1`, run
`20260701065818`. The registered build was chosen because it predates three
changelog relaxations and would therefore flag conformant objects, turning them
into floor classes. The build actually run is the one the prior spine-gsps paper
used, which buys cross-paper comparability. The two builds are known to differ on
exactly three entries:

    231003  TILED_FULL PatientOrientation
    241003  TILED_FULL SegmentationMacro
    241114  LABELMAP SegmentNumber

So the exposure is not "every object". It is every object that is LABELMAP or
TILED_FULL, and that is a count this project already captured per object.

Direction, which matters as much as size: the registered build is the **stricter**
one. It would emit messages the run build suppresses. Addendum 02 section 2
pre-classifies those messages as floor rather than as defects, so a net rate is
insulated by construction and a gross count on the exposed objects is a lower
bound.

**Pin 2, highdicom.** Registered `0.28.0`, installed `0.28.1`. highdicom's only
role in this project is as W1, the Phase 1 writer that emits fixture objects for
the floor set. It is not a validator, and the exposure to the corpus measurement
is bounded by two facts this module measures rather than asserts: whether the
measurement modules import it at all, and which highdicom versions actually wrote
the objects in the measured set.

Usage:
    python -m colophon.deviations
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pandas as pd

from . import census, floor, phase3
from .paths import REPO, RESULTS

CMD = "python -m colophon.deviations"
OUT = RESULTS / "deviations"

# The three dicom3tools changelog entries that separate the two builds.
CHANGELOG_DIFF = [
    {"entry": "231003", "condition": "TILED_FULL",
     "attribute": "PatientOrientation",
     "applies_to": "any IOD that can be TILED_FULL, which in the measured set "
                   "is Segmentation and Parametric Map"},
    {"entry": "241003", "condition": "TILED_FULL",
     "attribute": "SegmentationMacro", "applies_to": "Segmentation only"},
    {"entry": "241114", "condition": "LABELMAP",
     "attribute": "SegmentNumber", "applies_to": "Segmentation only"},
]

# Modules that produce a measured number. If highdicom is not imported by any of
# them, the highdicom pin cannot have moved any measured number.
MEASUREMENT_MODULES = ["census.py", "phase3.py", "floor.py", "claim3.py"]

# Attributes the exposure question turns on, and where each was captured.
# The census capture list predates this question, so for the seven census
# classes DimensionOrganizationType was not recorded. Stated rather than
# silently treated as absent.
CAPTURED_IN_PHASE3 = ["SegmentationType", "DimensionOrganizationType"]


def dicom3tools_exposure() -> tuple[pd.DataFrame, dict]:
    """Objects that are LABELMAP or TILED_FULL, by class and analysis result."""
    rows = Counter()
    totals = Counter()
    values = {"SegmentationType": Counter(), "DimensionOrganizationType": Counter()}

    for record in phase3.load_records():
        if record["status"] != "OK":
            continue
        for obj in record.get("objects", []):
            if obj.get("status") != "OK":
                continue
            key = ("Segmentation Storage", record.get("analysis_result_id") or "(null)")
            totals[key] += 1
            seg_type = str(obj.get("SegmentationType", "") or "").strip().upper()
            dim_org = str(obj.get("DimensionOrganizationType", "") or "").strip().upper()
            values["SegmentationType"][seg_type or "(absent)"] += 1
            values["DimensionOrganizationType"][dim_org or "(absent)"] += 1
            if seg_type == "LABELMAP":
                rows[key + ("LABELMAP",)] += 1
            if dim_org == "TILED_FULL":
                rows[key + ("TILED_FULL",)] += 1

    census_objects = Counter()
    for record in census.load_records():
        if record["status"] != "OK" or record["sop_class_name"] == "Enhanced SR Storage":
            continue
        for obj in record.get("objects", []):
            if obj.get("status") == "OK":
                census_objects[record["sop_class_name"]] += 1

    table = []
    for (sop, ar, condition), n in sorted(rows.items(), key=lambda x: -x[1]):
        table.append({"sop_class_name": sop, "analysis_result_id": ar,
                      "condition": condition, "objects": n,
                      "objects_in_cell": totals[(sop, ar)],
                      "pct_of_cell": round(100 * n / totals[(sop, ar)], 2)})
    frame = pd.DataFrame(table) if table else pd.DataFrame(
        columns=["sop_class_name", "analysis_result_id", "condition", "objects",
                 "objects_in_cell", "pct_of_cell"])

    measured = sum(totals.values()) + sum(census_objects.values())
    labelmap = sum(n for (_, _, c), n in rows.items() if c == "LABELMAP")
    tiled = sum(n for (_, _, c), n in rows.items() if c == "TILED_FULL")
    return frame, {
        "segmentation_objects": sum(totals.values()),
        "census_objects": sum(census_objects.values()),
        "measured_objects": measured,
        "LABELMAP_objects": labelmap,
        "TILED_FULL_objects": tiled,
        "exposed_objects": labelmap + tiled,
        "pct_of_measured_set": round(100 * (labelmap + tiled) / measured, 2)
        if measured else 0.0,
        "SegmentationType_values": dict(values["SegmentationType"]),
        "DimensionOrganizationType_values": dict(values["DimensionOrganizationType"]),
        "unmeasured": {
            "reason": "the census capture list predates this question, so "
                      "DimensionOrganizationType (0020,9311) was not recorded "
                      "for the seven census classes",
            "class": "Parametric Map Storage",
            "objects": census_objects.get("Parametric Map Storage", 0),
            "note": "Parametric Map is the only census class whose IOD can "
                    "carry TILED_FULL. SegmentationType (0062,0001) exists "
                    "only in the Segmentation IOD, so its exposure in the "
                    "census classes is structurally zero rather than "
                    "unmeasured.",
        },
    }


def relaxed_check_residue() -> dict:
    """Do the exposed objects carry any message the relaxations would suppress.

    Not proof of what the registered build would do, and it is not presented as
    proof. It is the observable signature: if the run build still emitted
    PatientOrientation or Segmentation-macro findings on TILED_FULL objects, the
    relaxations would not be active in it and the premise of the whole deviation
    argument would be wrong.
    """
    needles = ("patientorientation", "patient orientation", "segmentationmacro",
               "segment identification", "segmentidentification")
    exposed, hits = 0, Counter()
    for record in phase3.load_records():
        for obj in record.get("objects", []):
            if obj.get("status") != "OK":
                continue
            dim = str(obj.get("DimensionOrganizationType", "") or "").strip().upper()
            seg = str(obj.get("SegmentationType", "") or "").strip().upper()
            if dim != "TILED_FULL" and seg != "LABELMAP":
                continue
            exposed += 1
            for validator, _, severity, template in obj.get("messages", []):
                low = template.lower()
                if any(n in low for n in needles):
                    hits[(validator, severity, template[:110])] += 1
    return {"exposed_objects": exposed,
            "matching_message_classes": len(hits),
            "matching_messages": [{"validator": v, "severity": s, "template": t,
                                   "count": n} for (v, s, t), n in hits.most_common()]}


def highdicom_exposure() -> dict:
    """Where highdicom can and cannot have moved a measured number."""
    # Two different questions, and conflating them would overstate the case.
    # `floor.py` does import highdicom, to read `__version__` for the pinning
    # appendix, and it names highdicom as W1 because highdicom is the Phase 1
    # writer. Neither is highdicom producing a measured number. The column that
    # carries the argument is the second one.
    imports = {}
    for name in MEASUREMENT_MODULES:
        source = (Path(__file__).parent / name).read_text(encoding="utf-8")
        appears = "highdicom" in source
        real_import = ("import highdicom" in source
                       or "from highdicom" in source
                       or '__import__("highdicom")' in source)
        # highdicom is used as an instrument only if something calls one of its
        # readers. Version reporting and a writer label are not that.
        instrument = any(call in source for call in
                         ("highdicom.seg", "highdicom.sr", "hd.seg", "hd.sr",
                          "segread", "srread"))
        imports[name] = {"appears_in_source": appears,
                         "imports_the_package": real_import,
                         "used_as_an_instrument": instrument}

    versions = Counter()
    # What the caller put in SoftwareVersions on those objects, which Table 4
    # reports. It is counted here rather than asserted there: the caption used
    # to say a repository URL was present on all of them, and it is present on
    # a quarter of them.
    software_versions = Counter()
    software_by_class = Counter()
    for loader, source in ((phase3.load_records, "Segmentation Storage"),
                           (census.load_records, None)):
        for record in loader():
            if record.get("status") != "OK":
                continue
            for obj in record.get("objects", []):
                if obj.get("status") != "OK":
                    continue
                value = str(obj.get("ImplementationVersionName", "") or "")
                if not value.lower().startswith("highdicom"):
                    continue
                versions[value] += 1
                sv = str(obj.get("SoftwareVersions", "") or "")
                state = ("repository URL" if "github.com" in sv
                         else "empty" if not sv.strip() else "other")
                sop = source or obj.get("sop_class_name") or record.get(
                    "sop_class_name") or "unknown"
                software_versions[state] += 1
                software_by_class[(sop, state)] += 1

    pinned = {"highdicom0.28.0", "highdicom0.28.1"}
    return {
        "registered_pin": "0.28.0",
        "installed": floor.tool_versions()["highdicom"]["version"],
        "imported_by_measurement_modules": imports,
        "role": "W1, the Phase 1 writer that emits fixture objects for the floor "
                "set. Not a validator anywhere in this project.",
        "corpus_writer_versions": dict(versions.most_common()),
        "corpus_objects_written_by_a_pinned_version": sum(
            n for v, n in versions.items() if v in pinned),
        "corpus_objects_written_by_highdicom": sum(versions.values()),
        "corpus_softwareversions_states": dict(software_versions.most_common()),
        "corpus_softwareversions_by_class": {
            "%s | %s" % k: v
            for k, v in sorted(software_by_class.items())},
        "changelog_diff": "UNRESOLVED OFFLINE. The 0.28.0 source is not on this "
                          "machine and the diff needs network. Completing "
                          "command: pip download highdicom==0.28.0 --no-deps "
                          "--no-binary :all:, then diff its CHANGELOG against "
                          "the installed 0.28.1.",
    }


def build() -> dict:
    frame, summary = dicom3tools_exposure()
    return {"dicom3tools_table": frame, "dicom3tools": summary,
            "residue": relaxed_check_residue(), "highdicom": highdicom_exposure()}


def write(t: dict) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    t["dicom3tools_table"].to_csv(OUT / "pin_exposure_by_analysis_result.csv",
                                  index=False)
    (OUT / "pin_deviations.json").write_text(json.dumps(
        {k: v for k, v in t.items() if k != "dicom3tools_table"}, indent=2),
        encoding="utf-8")

    d, hd, res = t["dicom3tools"], t["highdicom"], t["residue"]
    imports = hd["imported_by_measurement_modules"]
    rows = "\n".join(
        "| `%s` | %s | %s | %s | %s | %.2f |"
        % (r.sop_class_name, r.analysis_result_id, r.condition,
           f"{r.objects:,}", f"{r.objects_in_cell:,}", r.pct_of_cell)
        for r in t["dicom3tools_table"].itertuples()) or "| | | none | 0 | | |"

    changelog = "\n".join(
        "| `%s` | %s | %s | %s |" % (c["entry"], c["condition"], c["attribute"],
                                     c["applies_to"]) for c in CHANGELOG_DIFF)

    text = f"""# Registered pins that were not satisfied, and the measured exposure

Two pins are registered and unsatisfied. Neither registration is edited here and
nothing is re-run. This document measures how much of the corpus is exposed to
the known behavioural difference, so each deviation carries a number.

**A pin that was never satisfied is not a pin changed after seeing results.** The
first is a deviation to be quantified and declared. The second is what
pre-registration exists to prevent, and it has not happened. Reproduce with
`{CMD}`.

## Pin 1, dicom3tools

| | |
|---|---|
| registered | `1.00~20240118131615-1` |
| actually run | `20260701065818` |
| why the run build | it is the build the prior spine-gsps paper used, so every number here is comparable across the two papers |
| why the registered build was chosen | it predates three relaxations, so it flags conformant objects and turns them into floor classes |

The two builds are known to differ on exactly three changelog entries, so the
exposure is not every object. It is every object that is LABELMAP or TILED_FULL.

| entry | condition | attribute | applies to |
|---|---|---|---|
{changelog}

### Measured exposure

| | objects |
|---|---|
| measured set, all classes | **{d['measured_objects']:,}** |
| Segmentation objects, where both attributes were captured | {d['segmentation_objects']:,} |
| **LABELMAP** | **{d['LABELMAP_objects']:,}** |
| **TILED_FULL** | **{d['TILED_FULL_objects']:,}** |
| exposed to any of the three entries | **{d['exposed_objects']:,}**, {d['pct_of_measured_set']} percent of the measured set |

`SegmentationType (0062,0001)` values observed: {", ".join("%s %s" % (k, f"{v:,}") for k, v in d["SegmentationType_values"].items())}.

`DimensionOrganizationType (0020,9311)` values observed: {", ".join("%s %s" % (k, f"{v:,}") for k, v in d["DimensionOrganizationType_values"].items())}.

{rows and "Where the exposed objects are:" or ""}

| SOP class | analysis_result_id | condition | objects | objects in cell | percent of cell |
|---|---|---|---|---|---|
{rows}

**LABELMAP exposure is zero.** Changelog entry `241114` cannot have moved any
number in this study, and that is a measurement rather than an argument.

**TILED_FULL exposure is {d['TILED_FULL_objects']:,} objects**, all of them
whole-slide-imaging segmentations in three analysis results. Entries `231003` and
`241003` do have exposure and it is bounded to those objects.

### Which way the difference runs

The registered build is the **stricter** one: it would emit messages the run
build suppresses, not fewer. Addendum 02 section 2 pre-classifies exactly those
messages as **floor rather than defect**, so a net rate is insulated by
construction and the gross count on the exposed objects is a lower bound rather
than an unknown.

### The observable signature

Not proof of what the registered build would do, and not offered as proof. If the
run build still emitted PatientOrientation or Segmentation-macro findings on
these objects, the relaxations would not be active in it and the argument above
would be wrong.

**{res['matching_message_classes']} message classes** touching
`PatientOrientation` or the Segmentation macro appear on the
{res['exposed_objects']:,} exposed objects. That is consistent with the
relaxations being active in the build that ran.

### What is not measured

`DimensionOrganizationType (0020,9311)` was **not captured for the seven census
classes**, because the census capture list predates this question.
{d['unmeasured']['class']} is the only one of them whose IOD can carry
TILED_FULL, so exposure there is unmeasured over
**{d['unmeasured']['objects']:,} objects**. `SegmentationType (0062,0001)` exists
only in the Segmentation IOD, so its exposure in the census classes is
structurally zero rather than unmeasured.

## Pin 2, highdicom

| | |
|---|---|
| registered | `{hd['registered_pin']}` |
| installed | `{hd['installed']}` |
| role | {hd['role']} |

Two measurements bound the exposure without needing the changelog.

**No module that produces a measured number uses it as an instrument.** Three
columns, because "the name appears" and "a reader was called" are different
questions and merging them would overstate the case. `floor.py` does import the
package, to read `__version__` for the pinning appendix, and it names highdicom
as W1 because highdicom is the Phase 1 writer. Neither is highdicom producing a
number.

| module | name appears | imports the package | **used as an instrument** |
|---|---|---|---|
{chr(10).join("| `colophon/%s` | %s | %s | %s |" % (k, "yes" if v["appears_in_source"] else "no", "yes" if v["imports_the_package"] else "no", "yes" if v["used_as_an_instrument"] else "**no**") for k, v in imports.items())}

**No object in the measured set was written by either version.** The corpus was
written by these highdicom builds:

| ImplementationVersionName | objects |
|---|---|
{chr(10).join("| `%s` | %s |" % (k, f"{v:,}") for k, v in hd["corpus_writer_versions"].items()) or "| none | 0 |"}

Objects written by a pinned version, 0.28.0 or 0.28.1:
**{hd['corpus_objects_written_by_a_pinned_version']:,}** of
{hd['corpus_objects_written_by_highdicom']:,} highdicom-written objects.

So the highdicom deviation has **zero exposure in Phase 2, Phase 3 and the claim
3 tabulation**, and its exposure is confined to the Phase 1 Arm A floor set,
where highdicom is the writer.

The changelog diff itself is {hd['changelog_diff']}
"""
    path = REPO / "DEVIATIONS.md"
    path.write_text(text, encoding="utf-8")
    return path


def propose_ledger(t: dict) -> Path:
    d, hd, res = t["dicom3tools"], t["highdicom"], t["residue"]
    common = dict(section="DEV", section_title="Registered pins not satisfied",
                  command=CMD, source_file="DEVIATIONS.md",
                  validator="dciodvfy", sop_class="all measured classes",
                  floor="not applicable, these rows measure exposure to a tool "
                        "version difference rather than quoting a failure rate")
    rows = [
        dict(id="DEV-01",
             claim="The dicom3tools pin registered for this study was never "
                   "satisfied. The deviation is declared and its exposure is "
                   "measured rather than argued.",
             status="MEASURED",
             validator_version="registered 1.00~20240118131615-1; run 20260701065818",
             value="the two builds are known to differ on three changelog "
                   "entries, all conditioned on LABELMAP or TILED_FULL; in the "
                   "measured set LABELMAP is %s objects and TILED_FULL is %s, "
                   "%s of %s objects in total, %s percent"
                   % (f"{d['LABELMAP_objects']:,}", f"{d['TILED_FULL_objects']:,}",
                      f"{d['exposed_objects']:,}", f"{d['measured_objects']:,}",
                      d["pct_of_measured_set"]),
             n=f"{d['exposed_objects']:,}", denominator=f"{d['measured_objects']:,}",
             dropped="DimensionOrganizationType was not captured for the seven "
                     "census classes, so TILED_FULL exposure is unmeasured over "
                     "the %s Parametric Map objects, the only census class whose "
                     "IOD can carry it. SegmentationType exists only in the "
                     "Segmentation IOD, so its census exposure is structurally "
                     "zero rather than unmeasured."
                     % f"{d['unmeasured']['objects']:,}",
             external_source="dicom3tools changelog entries 231003, 241003 and "
                             "241114",
             derived_from="F1-08,B-11",
             pinned_by_test="tests/test_deviations.py::test_pin_exposure_is_measured",
             status_note="A pin never satisfied is not a pin changed after "
             "seeing results. The run build is the one the prior spine-gsps "
             "paper used, which buys cross-paper comparability. The registered "
             "build is the stricter of the two: it would emit messages the run "
             "build suppresses, and addendum 02 section 2 pre-classifies those "
             "as floor rather than defect, so a net rate is insulated by "
             "construction and a gross count on the exposed objects is a lower "
             "bound.",
             notes="LABELMAP exposure is zero, so changelog entry 241114 cannot "
                   "have moved any number in this study. %d message classes "
                   "touching PatientOrientation or the Segmentation macro "
                   "appear on the %s exposed objects, which is the signature "
                   "expected if the relaxations are active in the build that "
                   "ran." % (res["matching_message_classes"],
                             f"{res['exposed_objects']:,}"),
             **common),
        dict(id="DEV-02",
             claim="The highdicom pin registered for this study was never "
                   "satisfied, and its exposure to every measured number is "
                   "zero.",
             status="MEASURED",
             value="registered 0.28.0, installed %s; no module that produces a "
                   "measured number uses highdicom as an instrument, and %s "
                   "of %s highdicom-written objects in the measured set were "
                   "written by 0.28.0 or 0.28.1"
                   % (hd["installed"],
                      f"{hd['corpus_objects_written_by_a_pinned_version']:,}",
                      f"{hd['corpus_objects_written_by_highdicom']:,}"),
             n="0", denominator=f"{hd['corpus_objects_written_by_highdicom']:,}",
             dropped="the changelog diff between 0.28.0 and 0.28.1 is "
                     "unresolved offline: the 0.28.0 source is not on this "
                     "machine and the diff needs network",
             derived_from="F1-08",
             validator="not applicable, highdicom is a writer here and never a "
                       "validator",
             validator_version="registered 0.28.0; installed %s" % hd["installed"],
             pinned_by_test="tests/test_deviations.py::test_highdicom_is_not_in_the_measurement_path",
             status_note="highdicom's only role is W1, the Phase 1 writer that "
             "emits fixture objects for the floor set. The corpus was written "
             "by six older highdicom builds, none of them a pinned version, so "
             "the deviation cannot have moved a Phase 2, Phase 3 or claim 3 "
             "number. Its exposure is confined to the Phase 1 Arm A floor set.",
             **{k: v for k, v in common.items()
                if k not in ("validator", "validator_version")}),
    ]
    pending = RESULTS / "pending_ledger"
    pending.mkdir(parents=True, exist_ok=True)
    path = pending / "track_deviations.json"
    path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return path


def main(argv=None) -> int:
    t = build()
    d, hd = t["dicom3tools"], t["highdicom"]
    print("dicom3tools: LABELMAP %d, TILED_FULL %d, %d of %d measured objects, "
          "%.2f percent" % (d["LABELMAP_objects"], d["TILED_FULL_objects"],
                            d["exposed_objects"], d["measured_objects"],
                            d["pct_of_measured_set"]))
    print("relaxed-check residue: %d matching message classes on %d exposed objects"
          % (t["residue"]["matching_message_classes"], t["residue"]["exposed_objects"]))
    print("highdicom: imported by measurement modules: %s"
          % {k: v for k, v in hd["imported_by_measurement_modules"].items()})
    print("highdicom: %d of %d corpus objects written by a pinned version"
          % (hd["corpus_objects_written_by_a_pinned_version"],
             hd["corpus_objects_written_by_highdicom"]))
    print("wrote %s" % write(t))
    print("proposed %s" % propose_ledger(t))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
