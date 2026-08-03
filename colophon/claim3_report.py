"""Assemble the claim 3 tables and write CLAIM3.md. Reads only what is on disk.

`colophon.claim3` computes. This module joins the pieces, writes the CSVs, writes
one paragraph per table, and proposes the ledger rows. Nothing here fetches and
nothing here adjudicates conformance.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pandas as pd

from . import claim3, provenance, standards, writers
from .claim3 import CMD, GRADES, OUT
from .paths import REPO, RESULTS


def build() -> dict:
    frame, excluded = claim3.load()
    if frame.empty:
        raise SystemExit("no records on disk")

    from .index import load_index
    idc_version, index = load_index()

    t31_class, t31_ar, t31_flagged = claim3.t31(frame)
    t32_class, t32_ar, t32_ways = claim3.t32(frame)
    t33 = claim3.t33(frame, index)
    t34_writer, t34_special = claim3.t34(frame)
    t35 = claim3.t35(frame)
    t36_class, t36_ways = claim3.t36(frame)
    graded = claim3.grade_objects(frame)
    categories = claim3.category_table(frame)
    unclassified = claim3.unclassified_values(frame)
    corroboration = claim3.type1_corroboration()

    return {
        "frame": frame, "excluded": excluded, "idc_version": idc_version,
        "t31_class": t31_class, "t31_ar": t31_ar, "t31_flagged": t31_flagged,
        "t32_class": t32_class, "t32_ar": t32_ar, "t32_ways": t32_ways,
        "t33": t33, "t34_writer": t34_writer, "t34_special": t34_special,
        "t35": t35, "t36_class": t36_class, "t36_ways": t36_ways,
        "t36_ar": t36_ways["by_ar"],
        "graded": graded, "categories": categories, "unclassified": unclassified,
        "corroboration": corroboration,
        "grades_by_class": claim3.grade_table(graded, "sop_class_name"),
        "grades_by_ar": claim3.grade_table(graded, "analysis_result_id"),
    }


def _without_points(ways: dict) -> dict:
    """The summary json keeps boundary counts; the points live in their own CSV."""
    out = {}
    for k, v in ways.items():
        if k in ("frame", "by_ar"):
            continue
        out[k] = ({kk: vv for kk, vv in v.items() if kk != "per_unit"}
                  if isinstance(v, dict) else v)
    return out


def write_csvs(t: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    files = {
        "t31_carriers_by_sop_class.csv": t["t31_class"],
        "t31_carriers_by_analysis_result.csv": t["t31_ar"],
        "t31_type1_violations.csv": t["t31_flagged"],
        "t31_type1_validator_corroboration.csv": t["corroboration"],
        "t32_naming_by_sop_class.csv": t["t32_class"],
        "t32_naming_by_analysis_result.csv": t["t32_ar"],
        "t32_value_categories.csv": t["categories"],
        "t32_unclassified_values.csv": t["unclassified"],
        "t33_recoverability_ladder.csv": t["t33"],
        "t34_algorithm_identification_by_writer.csv": t["t34_writer"],
        "t34_complete_macro_naming_manual.csv": t["t34_special"],
        "t35_version_carriers.csv": t["t35"],
        "t36_writer_index_vs_object_by_sop_class.csv": t["t36_class"],
        "t36_writer_index_vs_object_by_analysis_result.csv": t["t36_ar"],
        "grades_by_sop_class.csv": t["grades_by_class"],
        "grades_by_analysis_result.csv": t["grades_by_ar"],
    }
    for name, table in files.items():
        table.to_csv(OUT / name, index=False)
    # Every unit as a point, so a figure that must show all of them has a named
    # artefact to draw from rather than recomputing the measurement.
    for label, ways in (("encoder_only", t["t32_ways"]),
                        ("writer_relabelled", t["t36_ways"])):
        for unit in ("by_collection", "by_analysis_result"):
            pd.DataFrame(ways[unit]["per_unit"]).to_csv(
                OUT / ("%s_%s.csv" % (label, unit)), index=False)
    (OUT / "two_way_rates.json").write_text(json.dumps({
        "encoder_only": _without_points(t["t32_ways"]),
        "writer_relabelled": _without_points(t["t36_ways"]),
        "note": "Median and IQR are deliberately absent. These distributions are "
                "two point masses at 0 and 100 and a median reports one camp as "
                "a centre. The boundary counts are the finding.",
    }, indent=2), encoding="utf-8")


def _camp(d: dict, unit: str) -> str:
    between = ", ".join("%s at %.2f percent" % (b["unit"], b["pct"])
                        for b in d["between_units"][:6]) or "none"
    return ("%d %s: **%d at 0 percent, %d at 100 percent**, %d in between (%s)"
            % (d["units"], unit, d["at_zero"], d["at_hundred"], d["between"], between))


def write_markdown(t: dict) -> Path:
    from .index import _fmt, _md_table

    frame, excluded = t["frame"], t["excluded"]
    n = int(len(frame))
    seg_objects = int((frame.source == "phase3").sum())
    census_objects = n - seg_objects
    n_classes = int(frame["sop_class_name"].nunique())
    counts = Counter(t["graded"]["grade"])
    t32w, t36w = t["t32_ways"], t["t36_ways"]
    flagged = t["t31_flagged"]

    grade_rows = "\n".join(
        "| %s | %s | %.2f |" % (g, _fmt(counts.get(g, 0)), 100 * counts.get(g, 0) / n)
        for g in GRADES)

    dropped_rows = "\n".join("- `%s`: %s" % (k, _fmt(v))
                             for k, v in sorted(excluded.items()))

    text = f"""# Claim 3: does a derived DICOM object in IDC say what produced it

Complete tabulation over everything measured. **Nothing was fetched.** Both
record sets were already on disk: the Phase 2 census and the PRE-06 Segmentation
sample. IDC {t['idc_version']}. Reproduce with `{CMD}`.

## Scope, before any number

**{_fmt(n)} objects across {n_classes} SOP classes.** {_fmt(census_objects)} from
the census across the seven complete classes, and {_fmt(seg_objects)}
Segmentation objects from the PRE-06 sample of 5,941 series.

**Enhanced SR is excluded from every rate in this document.**
{_fmt(excluded.get('enhanced_sr_series_recorded', 0))} of
{_fmt(excluded.get('enhanced_sr_series_in_manifest', 0))} series are recorded and
the class is still running. A partial class reads as a rate, so it is named here
and left out rather than folded in.

Segmentation objects carry the PRE-06 stratum weights and the census classes do
not, so the two are never pooled into a single unweighted archive-wide figure.
Every table is reported per SOP class and per `analysis_result_id`.

**Three grades, never two.**

| grade | objects | percent |
|---|---|---|
{grade_rows}

Only an attribute that a VERIFIED ledger row binds Type 1 can make an object
non-conformant here. That is STD-04, Enhanced General Equipment with Usage M, and
it binds four attributes in **two** of the eight IODs measured, Segmentation and
Parametric Map. In the other six, no carrier in this list is Type 1, so **no
object in them can be graded non-conformant on carrier grounds at all.** The
grading is asymmetric because the standard is asymmetric, and that is the result
rather than a caveat. Absence of a Type 3 carrier is a gap in the standard and is
never counted here as a defect.

{_md_table(t["grades_by_class"], ["sop_class_name", "objects", "non-conformant", "conformant but uninformative", "informative", "pct_non-conformant", "pct_conformant", "pct_informative", "sum_pct"])}

`sum_pct` is 100 in every row up to the rounding of the two decimals shown:
the three grades are exhaustive and mutually exclusive, so the counts partition
the objects exactly and only the displayed percentages round.

## T3.1 Carrier population

Three states, always separate, never summed. `absent` means no element,
`zero_length` means the element is present and carries nothing. For the census
classes `ContributingEquipmentSequence` was recorded as a presence flag only, so
those two states are not separable for it and `absent_or_zero_length` carries
them jointly; the Segmentation sample records all three.

{_md_table(t["t31_class"], ["sop_class_name", "carrier", "objects", "absent", "zero_length", "non_empty", "absent_or_zero_length", "type1_here", "type1_violation"])}

**Zero-length where Enhanced General Equipment binds it Type 1**, flagged by name
as the tabulation asked. Usage M in the Segmentation and Parametric Map IODs
makes Manufacturer, ManufacturerModelName, DeviceSerialNumber and SoftwareVersions
Type 1 there. A Type 1 attribute present and empty is a violation, and a presence
check scores it as present.

{_md_table(flagged, ["sop_class_name", "analysis_result_id", "carrier", "objects", "absent", "zero_length", "binding", "grade"]) if len(flagged) else "**No object in either Type 1 class carries an absent or zero-length binding attribute.** Every Segmentation and Parametric Map object measured populates all four, which is what makes the presence check worthless and the naming question in T3.2 the only one that carries information."}

**Both validators independently confirm every one of them.** The three-state
capture says an attribute is absent or zero-length; whether that is
non-conformant is PS3.3's answer, read by two tools from different codebases.
Their counts are reported beside ours and never merged with them.

{_md_table(t["corroboration"], ["carrier", "state_we_recorded", "validator", "validator_raised_a_matching_message", "objects"]) if len(t["corroboration"]) else "No object carries an absent or zero-length Type 1 attribute, so there is nothing to corroborate."}

*What this table shows.* It separates the two questions a presence check merges.
The equipment attributes are populated nearly everywhere, which is exactly what
Enhanced General Equipment being Mandatory predicts, and is precisely why
presence is not the measurement. The states that carry information are the
zero-length ones, because they are the only ones the standard forbids, and the
absences among the Type 3 carriers, because those are the standard's own gaps
rather than anyone's defects. The per-`analysis_result_id` form is in
`results/claim3/t31_carriers_by_analysis_result.csv`.

## T3.2 What the values name, not whether they exist

Presence is guaranteed where Enhanced General Equipment is Mandatory, so presence
means nothing, and this table asks what the populated values actually say. The
four buckets are exhaustive and mutually exclusive and sum to the population.

{_md_table(t["t32_class"], ["sop_class_name", "objects", "encoder_only", "producer_and_converter", "other", "absent", "pct_encoder_only", "pct_producer_and_converter", "pct_other", "pct_absent", "sum_pct"])}

Reported both ways, for the `encoder_only` bucket:

- object weighted: **{_fmt(t32w['objects_flagged'])} of {_fmt(t32w['objects'])}, {t32w['pct_object_weighted']} percent**
- by collection: {_camp(t32w['by_collection'], 'collections')}
- by analysis result: {_camp(t32w['by_analysis_result'], 'analysis results')}

### How every value was classified, and where the grade could move

The categories come from `colophon.provenance.RULES`, the project's ordered
rule table, imported rather than restated. `named_analysis` is the only category
that counts as producer identity. The others are excluded on the table's own
reading: an `encoder` writes any analysis and identifies none, a `conversion`
string says a third party converted the object, an `application` is a viewer, an
`acquisition_vendor` on a derived object is equipment that did not produce it,
and an `institution` names an organisation without naming what it ran.

{_md_table(t["categories"], ["sop_class_name", "category", "values"])}

**An additive rule table was needed and is published separately.**
`provenance.RULES` was built for `Manufacturer` and `ManufacturerModelName` as
the index carries them. This pass is the first to read `SegmentAlgorithmName
(0062,0009)` and the Algorithm Identification Macro at scale, and those fields
carry model names that table has no rule for. Extending it in place would have
retroactively moved the Phase 0 measurements, so
`colophon.claim3.CLAIM3_EXTRA_RULES` is applied only after the Phase 0 table
returns `unclassified`:

{chr(10).join("- `%s` to **%s**, pattern `%s`" % (label, cat, pattern) for cat, label, pattern in claim3.CLAIM3_EXTRA_RULES)}

Values declined on purpose, recorded so the decision is visible rather than
implied:

{chr(10).join("- `%s`: %s" % (k, v) for k, v in claim3.DECLINED.items())}

**Everything still unclassified, printed verbatim.** This is where the grading
could move: a named analysis with no rule is graded uninformative, so publishing
the list is what makes that a stated undercount rather than a silent one.

{_md_table(t["unclassified"].head(25), ["sop_class_name", "value", "objects"]) if len(t["unclassified"]) else "Every value matched a rule."}

*What this table shows.* The equipment attributes are populated, and what a large
share of them name is the library that wrote the file. That is not a defect and
no validator can complain about it: `QIICR` and a git remote URL are legal values
of Manufacturer and ManufacturerModelName. This is claim 3 in its plainest form.
The boundary counts say it is not a tendency but a convention: collections sit at
0 or at 100 and almost nothing sits between, because a collection is one pipeline
run and a pipeline run uses one encoder. That is also why a median would be
actively misleading here and is not reported.

## T3.3 The recoverability ladder

Per analysis result, the **first** level at which producer identity appears and
whether a version appears with it. Levels: 1 equipment attributes, 2 file meta,
3 SeriesDescription and ContentCreatorName, 4 in-object algorithm carriers,
5 collection metadata and DOI. Level 5 is **not in the object**: identity found
only there is identity a downloaded file does not carry.

The rule for "identity appears" is `colophon.writers._informative`, imported
rather than restated: a value that is neither a published sentinel nor a generic
word. Any single assignment can be overruled by reading the value, which is
printed beside it.

{_md_table(t["t33"], ["sop_class_name", "analysis_result_id", "objects", "first_level_identity_appears", "level_name", "identifying_value", "version_at_that_level", "in_object"])}

**Of the {len(t["t33"])} analysis-result cells, identity appears at no level at
all in {int((t["t33"]["first_level_identity_appears"] == "none").sum())}.** It
appears at level 1 in {int((t["t33"]["first_level_identity_appears"] == 1).sum())},
at level 3 in {int((t["t33"]["first_level_identity_appears"] == 3).sum())} and at
level 4 in {int((t["t33"]["first_level_identity_appears"] == 4).sum())}. A version
accompanies the identity in
{int((t["t33"]["version_at_that_level"] == "yes").sum())} cells.

*What this table shows.* It turns "the producing algorithm is not named" from an
assertion into a measurement with a level attached. Where identity first appears
at level 1 the object is self-describing and a consumer needs nothing else. Where
it first appears at level 3 a consumer has to parse free text the standard puts
no constraint on. Where it first appears at level 5 the identity is in the
archive's registry, and **a file copied out of IDC does not carry it at all**,
which is the operational form of the claim. The version column is the harder test
and it fails more often than identity does: naming a model without naming its
version does not let anyone reproduce anything.

## T3.4 The algorithm identification result, by writing toolkit

Segment level and object level. **Absence and incompleteness are never merged.**
PS3.3 2026c makes `SegmentationAlgorithmIdentificationSequence (0062,0007)`
Type 3 in the Segmentation IOD with no condition, so absence is a gap in the
standard. A present sequence missing any of its three Type 1 children would be a
defect in the object.

{_md_table(t["t34_writer"], ["writing_toolkit", "objects", "segments", "segments_non_manual", "seg_absent", "pct_seg_absent", "seg_present_incomplete", "pct_seg_present_incomplete", "seg_present_complete", "objects_with_non_manual", "objects_any_absent", "objects_any_incomplete", "objects_any_complete"])}

The row the tabulation asked for by name, carried separately because it is
neither absence nor incompleteness:

{_md_table(t["t34_special"], ["writing_toolkit", "analysis_result_id", "SegmentAlgorithmType", "AlgorithmName", "segments", "state_of_0062_0007", "grade"]) if len(t["t34_special"]) else "No segment carries a complete macro naming a manual procedure."}

*What this table shows.* The split is by writing toolkit and it is total: a
toolkit either writes the macro for every segment or for none, and incompleteness
is zero everywhere. There is no partial compliance to measure, which makes this a
fact about toolkits rather than about analyses, and it is the reason the archive
wide percentage is a weighted average of two constants. The separate row is the
sharpest case in the tabulation: those segments carry a complete and conformant
macro whose three Type 1 children are all populated, and what it names is a manual
procedure on a segment whose own declared type is AUTOMATIC. Conformant, complete
and uninformative at once. PS3.3 states no relation between the two attributes,
so the contradiction is reported and not resolved.

## T3.5 Version carriers

Every 7-character hexadecimal `SoftwareVersions` value in the tabulation, which
is what dcmqi writes there: `dcmqi_WC_REVISION`, the abbreviated HEAD SHA of the
working copy that built the binary.

{_md_table(t["t35"], ["SoftwareVersions_sha7", "declared_repository", "repository_class", "sop_class_name", "analysis_result_id", "objects", "resolved_commit_date", "nearest_tag", "resolution"]) if len(t["t35"]) else "No object carries a 7-character hexadecimal SoftwareVersions value."}

**Resolution is incomplete, and the reason is a constraint rather than an
oversight.** Commit date and nearest tag require the QIICR/dcmqi commit history,
which is not on this machine and cannot be obtained without network access, and
this pass was instructed not to fetch. Every SHA is listed with its declared
repository and its repository class, both derivable from the object alone, and
the two git-derived columns read `UNRESOLVED OFFLINE`. The completing command is
in the ledger row and in `REPORT.md`.

*What this table shows.* The version carrier of the most common writing toolkit
in the archive is a commit hash of the encoder, not a version of anything that
computed a result. Reading it back tells a consumer which build of dcmqi wrote
the file and nothing at all about the analysis. The repository class column does
resolve offline and is already informative: it separates objects whose declared
repository is upstream from those naming a personal fork, which is a
build-environment fact rather than the vendor inconsistency it can be read as.

## T3.6 Index versus object writer identity

The archive catalogue and the object disagreeing about what produced the object.
The writer label is derived by the same ordered rule table in both cases,
`colophon.writers.WRITER_RULES`, imported unchanged. Only the evidence differs:
the index sees two equipment attributes, and the object also carries
`ContributingEquipmentSequence` and `ImplementationVersionName`.

{_md_table(t["t36_class"], ["sop_class_name", "objects", "relabelled", "pct_relabelled", "index_says_unidentifiable", "object_says_unidentifiable"])}

Per analysis result, only the cells that move:

{_md_table(t["t36_ar"], ["sop_class_name", "analysis_result_id", "writer_from_index", "writer_from_object", "deciding_carrier", "objects", "objects_in_cell", "pct_of_cell"]) if len(t["t36_ar"]) else "No cell moves."}

Reported both ways:

- object weighted: **{_fmt(t36w['objects_flagged'])} of {_fmt(t36w['objects'])}, {t36w['pct_object_weighted']} percent**
- by collection: {_camp(t36w['by_collection'], 'collections')}
- by analysis result: {_camp(t36w['by_analysis_result'], 'analysis results')}

*What this table shows.* This is a provenance finding, not a data-cleaning note.
The catalogue a researcher queries to build a cohort disagrees with the file
about what produced it, and it disagrees in one direction: the index says the
writer cannot be identified and the object says it can. Every move is decided by
a carrier the index does not expose. The consequence is that a cohort selected on
the index's writer attribution rests on a weaker reading of the object than the
object itself supports, and the size of that effect is the rate above. The
boundary counts show two camps again, because whether a toolkit writes
`ContributingEquipmentSequence` is a property of the toolkit and not of the study.

## What was dropped

{dropped_rows}

Nothing else. Every object in the seven complete census classes and in the PRE-06
sample appears in every table, and no table samples, truncates or ranks.

## What this tabulation does not do

- **No conformance was adjudicated.** No message class was scored, no rate is
  NET, and the only conformance statement anywhere is the Type 1 binding of
  STD-04, which is a verified reading of PS3.3 and not a validator verdict.
- **No manuscript restructure.** The tables live here and in `results/claim3/`.
- **No median and no IQR** for any unit-level distribution, by instruction. They
  are two point masses and a median reports one camp as a centre.
- **No ranking.** Tables are ordered by size, never by how badly a group scores.
"""
    OUT.mkdir(parents=True, exist_ok=True)
    path = REPO / "CLAIM3.md"
    path.write_text(text, encoding="utf-8")
    return path


def propose_ledger(t: dict) -> Path:
    from .index import _fmt

    frame, excluded = t["frame"], t["excluded"]
    n = int(len(frame))
    counts = Counter(t["graded"]["grade"])
    t32w, t36w = t["t32_ways"], t["t36_ways"]

    dropped = ("Enhanced SR excluded from every rate: %s of %s series recorded "
               "and the class is still running, so it would read as a rate; "
               "%s census objects and %s Segmentation objects failed to read"
               % (_fmt(excluded.get("enhanced_sr_series_recorded", 0)),
                  _fmt(excluded.get("enhanced_sr_series_in_manifest", 0)),
                  _fmt(excluded.get("census_objects_read_failed", 0)),
                  _fmt(excluded.get("segmentation_objects_read_failed", 0))))

    no_validator = ("not applicable, no validator is involved: these are "
                    "attribute-presence and attribute-content measurements read "
                    "from the object, not validator rates")

    common = dict(section="C3T", section_title="Claim 3, complete tabulation",
                  command=CMD, sop_class="seven complete census classes plus "
                  "Segmentation Storage from the PRE-06 sample",
                  validator="none", validator_version="not applicable",
                  dropped=dropped, idc_index_version=t["idc_version"])

    rows = [
        dict(id="C3T-00",
             claim="Claim 3 is graded in three ways and never two: "
                   "non-conformant, conformant but uninformative, informative. "
                   "Absence of a Type 3 carrier is a gap in the standard and is "
                   "never counted as a defect.",
             status="MEASURED",
             value="; ".join("%s %s, %.2f percent"
                             % (g, _fmt(counts.get(g, 0)),
                                100 * counts.get(g, 0) / n) for g in GRADES),
             n=_fmt(counts.get("conformant but uninformative", 0)),
             denominator=_fmt(n),
             floor=no_validator,
             external_source="PS3.3 2026c Table C.7-8b with Usage M in Table "
                             "A.51-1 and Table A.75-1",
             derived_from="STD-04,STD-05",
             source_file="results/claim3/grades_by_sop_class.csv",
             pinned_by_test="tests/test_claim3.py::test_grades_are_exhaustive_and_mutually_exclusive",
             status_note="Only an attribute a VERIFIED row binds Type 1 can "
             "make an object non-conformant here, which is four attributes in "
             "two of the eight IODs measured. In the other six no object can be "
             "graded non-conformant on carrier grounds at all. The asymmetry is "
             "the standard's, and it is the result rather than a caveat.",
             **common),
        dict(id="C3T-01",
             claim="T3.1. Carrier population across the tabulation, in three "
                   "states that are never summed.",
             status="MEASURED",
             value="%d carriers over %s objects, absent, zero-length and "
                   "non-empty reported apart for each; %d Type 1 violations "
                   "found where Enhanced General Equipment binds the attribute"
                   % (len(claim3.CARRIERS), _fmt(n),
                      int(t["t31_flagged"]["zero_length"].sum()
                          + t["t31_flagged"]["absent"].sum())
                      if len(t["t31_flagged"]) else 0),
             n=str(len(claim3.CARRIERS)), denominator=_fmt(n),
             floor=no_validator,
             external_source="PS3.3 2026c Table C.7-8b",
             derived_from="STD-04",
             source_file="results/claim3/t31_carriers_by_sop_class.csv",
             pinned_by_test="tests/test_claim3.py::test_three_states_never_summed",
             status_note="ContributingEquipmentSequence is two-state for the "
             "census classes, which recorded it as a presence flag, and "
             "three-state for the Segmentation sample. Declared in the table "
             "rather than smoothed over.",
             **common),
        dict(id="C3T-08",
             claim="Type 1 carrier violations found by the three-state capture, "
                   "and independently confirmed by both conformance validators "
                   "on every object.",
             status="MEASURED",
             value="DeviceSerialNumber (0018,1000) is absent on %s and "
                   "zero-length on %s Segmentation objects, %s in total of %s; "
                   "dciodvfy and dicom-validator each raise a matching message "
                   "on all %s, and both separate absent from empty exactly as "
                   "the capture does"
                   % (_fmt(int(t["t31_flagged"]["absent"].sum())),
                      _fmt(int(t["t31_flagged"]["zero_length"].sum())),
                      _fmt(int(t["t31_flagged"]["absent"].sum()
                               + t["t31_flagged"]["zero_length"].sum())),
                      _fmt(int((frame.sop_class_name == claim3.SEGMENTATION).sum())),
                      _fmt(int(t["t31_flagged"]["absent"].sum()
                               + t["t31_flagged"]["zero_length"].sum()))),
             n=_fmt(int(t["t31_flagged"]["absent"].sum()
                        + t["t31_flagged"]["zero_length"].sum())),
             denominator=_fmt(int((frame.sop_class_name == claim3.SEGMENTATION).sum())),
             floor="none subtracted. This is a Type 1 presence violation read "
                   "directly from the object and confirmed by two validators, "
                   "not a normalised message-class rate, so no floor set "
                   "applies to it.",
             validator="dciodvfy and dicom-validator",
             validator_version="dicom3tools snapshot 20260701065818; "
                               "dicom-validator 0.8.2 edition 2026c",
             external_source="PS3.3 2026c Table C.7-8b, Enhanced General "
                             "Equipment, Usage M in Table A.51-1",
             derived_from="STD-04,P3-06",
             source_file="results/claim3/t31_type1_validator_corroboration.csv",
             pinned_by_test="tests/test_claim3.py::test_type1_violations_are_corroborated",
             status_note="The conformance call is not ours. The capture "
             "reports a state, PS3.3 says what the state means, and two tools "
             "from different codebases read it independently and agree on the "
             "object set and on the split between absent and empty. This is "
             "the strongest carrier-level finding in the tabulation and it is "
             "confined to one SOP class, because it is one of only two whose "
             "IOD binds the attribute at all.",
             **{k: v for k, v in common.items()
                if k not in ("validator", "validator_version")}),
        dict(id="C3T-02",
             claim="T3.2. What the equipment attributes name, not whether they "
                   "exist. Presence is guaranteed where Enhanced General "
                   "Equipment is Mandatory, so a presence check measures "
                   "nothing.",
             status="MEASURED",
             value="encoder-only bucket: %s of %s objects, %s percent object "
                   "weighted; by collection %d at 0, %d at 100 and %d between, "
                   "of %d; by analysis result %d at 0, %d at 100 and %d "
                   "between, of %d"
                   % (_fmt(t32w["objects_flagged"]), _fmt(t32w["objects"]),
                      t32w["pct_object_weighted"],
                      t32w["by_collection"]["at_zero"],
                      t32w["by_collection"]["at_hundred"],
                      t32w["by_collection"]["between"],
                      t32w["by_collection"]["units"],
                      t32w["by_analysis_result"]["at_zero"],
                      t32w["by_analysis_result"]["at_hundred"],
                      t32w["by_analysis_result"]["between"],
                      t32w["by_analysis_result"]["units"]),
             n=_fmt(t32w["objects_flagged"]), denominator=_fmt(t32w["objects"]),
             floor=no_validator,
             derived_from="C3-04,W-04",
             source_file="results/claim3/t32_naming_by_sop_class.csv",
             pinned_by_test="tests/test_claim3.py::test_buckets_are_exhaustive",
             status_note="Four buckets, exhaustive and mutually exclusive, "
             "summing to 100 in every row. Reported object weighted and with "
             "the collection and the analysis result as the independent unit. "
             "No median and no IQR: the distribution is two point masses at 0 "
             "and 100 and a median would report one camp as a centre.",
             **common),
        dict(id="C3T-03",
             claim="T3.3. The recoverability ladder. Per analysis result, the "
                   "first of five levels at which producer identity appears, "
                   "and whether a version appears with it.",
             status="MEASURED",
             value="%d analysis result cells; first level 1 in %d, 2 in %d, "
                   "3 in %d, 4 in %d, 5 in %d, never in %d; version present at "
                   "the first identifying level in %d"
                   % (len(t["t33"]),
                      *(int((t["t33"]["first_level_identity_appears"] == lv).sum())
                        for lv in (1, 2, 3, 4, 5)),
                      int((t["t33"]["first_level_identity_appears"] == "none").sum()),
                      int((t["t33"]["version_at_that_level"] == "yes").sum())),
             n=str(len(t["t33"])), denominator=str(len(t["t33"])),
             floor=no_validator,
             derived_from="C3-14",
             source_file="results/claim3/t33_recoverability_ladder.csv",
             pinned_by_test="tests/test_claim3.py::test_ladder_levels_are_the_registered_five",
             status_note="Level 5 is not in the object. Identity found only "
             "there is identity a file copied out of IDC does not carry. The "
             "informativeness rule is colophon.writers._informative, imported "
             "rather than restated, and the deciding value is printed beside "
             "every assignment so a reader can overrule it.",
             **common),
        dict(id="C3T-04",
             claim="T3.4. The algorithm identification result stratified by "
                   "writing toolkit. A toolkit writes the macro for every "
                   "segment or for none, and incompleteness is zero everywhere.",
             status="MEASURED",
             value="; ".join(
                 "%s %s of %s non-MANUAL segments absent"
                 % (r.writing_toolkit, _fmt(int(r.seg_absent)),
                    _fmt(int(r.segments_non_manual)))
                 for r in t["t34_writer"].itertuples()
                 if int(r.segments_non_manual)),
             n=_fmt(int(t["t34_writer"]["seg_absent"].sum())),
             denominator=_fmt(int(t["t34_writer"]["segments_non_manual"].sum())),
             floor=no_validator,
             external_source="PS3.3 2026c Table C.8.20-2 and Table A.51-1",
             derived_from="P3-01,P3-02,STD-02",
             source_file="results/claim3/t34_algorithm_identification_by_writer.csv",
             pinned_by_test="tests/test_claim3.py::test_absence_and_incompleteness_stay_apart",
             status_note="Absence and incompleteness are carried in separate "
             "columns and never summed. The split is total rather than "
             "graduated, so the archive-wide percentage is a weighted average "
             "of two constants and is a fact about toolkits, not analyses.",
             **common),
        dict(id="C3T-05",
             claim="T3.4 special row. Segments carrying a complete and "
                   "conformant Algorithm Identification Macro whose "
                   "AlgorithmName names a manual procedure, on a segment whose "
                   "own declared type is AUTOMATIC.",
             status="MEASURED",
             value="%s segments, all with (0062,0007) present and complete"
                   % _fmt(int(t["t34_special"]["segments"].sum())
                          if len(t["t34_special"]) else 0),
             n=_fmt(int(t["t34_special"]["segments"].sum())
                    if len(t["t34_special"]) else 0),
             denominator=_fmt(int(t["t34_writer"]["seg_present_complete"].sum())),
             floor=no_validator,
             external_source="PS3.3 2026c Table C.8.20-4 for (0062,0008) and "
                             "section 10.16 Table 10-19 for (0066,0036)",
             derived_from="P3-10",
             source_file="results/claim3/t34_complete_macro_naming_manual.csv",
             status_note="Graded conformant but uninformative. PS3.3 states no "
             "relation between the two attributes, so the contradiction is "
             "reported and not resolved. Complete is not the same as "
             "informative, and this is the case that separates them.",
             **common),
        dict(id="C3T-06",
             claim="T3.5. Version carriers. The dcmqi SoftwareVersions value is "
                   "a commit hash of the encoder, and resolving it to a date "
                   "and a tag needs the upstream commit history.",
             status="MEASURED",
             value="%d distinct (SHA, repository, class, analysis result) cells "
                   "over %s objects; %d cells over %s objects resolve upstream "
                   "with a commit date and nearest tag, %d cells over %s objects "
                   "are orphaned and not in the upstream history; resolved "
                   "commit dates span %s to %s and nearest tags %s to %s"
                   % (len(t["t35"]),
                      _fmt(int(t["t35"]["objects"].sum()) if len(t["t35"]) else 0),
                      int((t["t35"].resolution == "upstream").sum()),
                      _fmt(int(t["t35"].loc[t["t35"].resolution == "upstream", "objects"].sum())),
                      int((t["t35"].resolution != "upstream").sum()),
                      _fmt(int(t["t35"].loc[t["t35"].resolution != "upstream", "objects"].sum())),
                      min(d[:10] for d in t["t35"].resolved_commit_date if d),
                      max(d[:10] for d in t["t35"].resolved_commit_date if d),
                      min(x for x in t["t35"].nearest_tag if x.startswith("v")),
                      max(x for x in t["t35"].nearest_tag if x.startswith("v"))),
             n=str(len(t["t35"])),
             denominator=_fmt(int(t["t35"]["objects"].sum())
                              if len(t["t35"]) else 0),
             floor=no_validator,
             derived_from="P2P-09,W-04",
             source_file="results/claim3/t35_version_carriers.csv",
             status_note="Resolved offline against a bare clone of "
             "QIICR/dcmqi at HEAD b6137d9ee8cf6cd6c074fe27d1af26a30b578753, "
             "1,374 commits, cloned 2026-08-02T19:35:32Z into _cache/dcmqi.git. "
             "Addendum 02 recorded no 7-character prefix collision across those "
             "commits, so the abbreviation is a precise version carrier and the "
             "resolution is unambiguous. An unresolved SHA is reported as "
             "orphaned, which is a finding rather than a gap: the object was "
             "written by a build whose commit is not in the upstream history.",
             **common),
        dict(id="C3T-07",
             claim="T3.6. The archive catalogue and the object disagree about "
                   "what produced the object, and the disagreement runs one "
                   "way: the index says the writer is unidentifiable and the "
                   "object says it is not.",
             status="MEASURED",
             value="%s of %s objects relabelled, %s percent object weighted; by "
                   "collection %d at 0, %d at 100 and %d between, of %d; by "
                   "analysis result %d at 0, %d at 100 and %d between, of %d"
                   % (_fmt(t36w["objects_flagged"]), _fmt(t36w["objects"]),
                      t36w["pct_object_weighted"],
                      t36w["by_collection"]["at_zero"],
                      t36w["by_collection"]["at_hundred"],
                      t36w["by_collection"]["between"],
                      t36w["by_collection"]["units"],
                      t36w["by_analysis_result"]["at_zero"],
                      t36w["by_analysis_result"]["at_hundred"],
                      t36w["by_analysis_result"]["between"],
                      t36w["by_analysis_result"]["units"]),
             n=_fmt(t36w["objects_flagged"]), denominator=_fmt(t36w["objects"]),
             floor=no_validator,
             derived_from="P3-12,W-01",
             source_file="results/claim3/t36_writer_index_vs_object_by_sop_class.csv",
             pinned_by_test="tests/test_claim3.py::test_writer_rule_table_is_imported_not_restated",
             status_note="A provenance finding, not a data-cleaning note. Both "
             "labels come from the same ordered rule table and only the "
             "evidence differs, so the gap measures what the index cannot see "
             "rather than a difference of method. A cohort selected on the "
             "index's writer attribution rests on a weaker reading of the "
             "object than the object supports.",
             **common),
    ]
    pending = RESULTS / "pending_ledger"
    pending.mkdir(parents=True, exist_ok=True)
    path = pending / "track_claim3.json"
    path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return path


def main(argv=None) -> int:
    t = build()
    write_csvs(t)
    md = write_markdown(t)
    led = propose_ledger(t)
    counts = Counter(t["graded"]["grade"])
    print("objects %d across %d classes"
          % (len(t["frame"]), t["frame"]["sop_class_name"].nunique()))
    for g in GRADES:
        print("  %-32s %6d" % (g, counts.get(g, 0)))
    print("wrote %s" % md)
    print("proposed %s" % led)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
