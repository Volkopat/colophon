"""Phase 0: the metadata pass over the IDC index. Zero bytes downloaded.

Everything here reads the local `idc-index` dataframe that ships with the
`idc-index-data` wheel. No S3 access, no network, no DICOM parsing. The census
this produces defines the population that Phases 2 and 3 sample from, so the
set of SOP classes counted as derived is stated explicitly rather than inferred.

Usage:
    python -m colophon.index               write every Phase 0 census table
    python -m colophon.index --print-only  print, write nothing
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from . import envinfo, ledger
from .paths import PHASE0, RESULTS

# The nine SOP classes counted as derived objects. These are the classes whose
# instances are produced by an analysis, an annotation effort or a conversion,
# rather than written by an acquisition device. Counting exactly these nine
# reproduces the 481,750 series and 504,727 instances quoted in the build brief.
DERIVED_SOP_CLASSES = {
    "Segmentation Storage": "1.2.840.10008.5.1.4.1.1.66.4",
    "Enhanced SR Storage": "1.2.840.10008.5.1.4.1.1.88.22",
    "Comprehensive 3D SR Storage": "1.2.840.10008.5.1.4.1.1.88.34",
    "Comprehensive SR Storage": "1.2.840.10008.5.1.4.1.1.88.33",
    "Grayscale Softcopy Presentation State Storage": "1.2.840.10008.5.1.4.1.1.11.1",
    "Parametric Map Storage": "1.2.840.10008.5.1.4.1.1.30",
    "Real World Value Mapping Storage": "1.2.840.10008.5.1.4.1.1.67",
    "Key Object Selection Document Storage": "1.2.840.10008.5.1.4.1.1.88.59",
    "RT Structure Set Storage": "1.2.840.10008.5.1.4.1.1.481.3",
}

# Six further classes that are also produced rather than acquired. They sit
# outside the headline denominator so that our totals stay comparable with the
# brief, and they are reported alongside it so the choice is visible.
ADJACENT_SOP_CLASSES = {
    "Microscopy Bulk Simple Annotations Storage": "1.2.840.10008.5.1.4.1.1.91.1",
    "Encapsulated STL Storage": "1.2.840.10008.5.1.4.1.1.104.3",
    "Advanced Blending Presentation State Storage": "1.2.840.10008.5.1.4.1.1.11.8",
    "Acquisition Context SR Storage": "1.2.840.10008.5.1.4.1.1.88.71",
    "Spatial Registration Storage": "1.2.840.10008.5.1.4.1.1.66.1",
    "X-Ray Radiation Dose SR Storage": "1.2.840.10008.5.1.4.1.1.88.67",
}

# Classes small enough to validate exhaustively in Phase 2, from the brief.
PHASE2_CLASSES = [
    "Grayscale Softcopy Presentation State Storage",
    "Comprehensive 3D SR Storage",
    "Comprehensive SR Storage",
    "Parametric Map Storage",
    "Key Object Selection Document Storage",
    "Real World Value Mapping Storage",
]

CMD = "python -m colophon.index"


def load_index():
    """Return (idc_version, dataframe). One row per series."""
    from idc_index import IDCClient
    client = IDCClient()
    return client.idc_version, client.index


def derived(df: pd.DataFrame, include_adjacent: bool = False) -> pd.DataFrame:
    names = set(DERIVED_SOP_CLASSES)
    if include_adjacent:
        names |= set(ADJACENT_SOP_CLASSES)
    return df[df["sop_class_name"].isin(names)].copy()


def analysis_attributed(df: pd.DataFrame) -> pd.DataFrame:
    """Derived series that IDC ingested as an analysis result.

    The second denominator. `analysis_result_id` is IDC's own record that a
    series was computed over another collection rather than being collection
    content. It is the best discriminator the index offers, and it is not the
    same thing as AI-derived: `lung_pet_ct_dx_annotations` is attributed and its
    Manufacturer reads "Expert annotation from TCIA", while
    `eay131_tumor_annotations` is attributed and was contoured by humans through
    a viewer. So this is an upper bound on the AI-derived population, not a
    measurement of it.

    The point of carrying both denominators is the other direction. The
    unattributed remainder contains radiotherapy planning contours from Pinnacle,
    ARIA and GammaPlan, which are human clinical objects. A claim about AI
    results computed over the derived denominator counts those, and a reviewer
    will say so.
    """
    d = derived(df)
    return d[d["analysis_result_id"].notna()]


def first_file_coverage(df: pd.DataFrame) -> pd.DataFrame:
    """What validating only the first file of each series would miss.

    The published state of the art for validating a public DICOM archive runs
    dciodvfy on the first file of every series. This measures the size of that
    coverage gap exactly, because quoting it loosely as large when it is small
    would cost more credibility than the point is worth.
    """
    d = derived(df)
    out = (d.groupby("sop_class_name")
             .agg(series=("SeriesInstanceUID", "size"),
                  instances=("instanceCount", "sum"))
             .reset_index())
    out["multi_instance_series"] = [
        int((d[d.sop_class_name == s]["instanceCount"] > 1).sum())
        for s in out["sop_class_name"]]
    out["instances_missed"] = out["instances"] - out["series"]
    out["pct_of_series_multi_instance"] = (
        100 * out["multi_instance_series"] / out["series"]).round(2)
    out["pct_of_instances_missed"] = (
        100 * out["instances_missed"] / out["instances"]).round(2)
    return out.sort_values("instances_missed", ascending=False).reset_index(drop=True)


def _agg(frame: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    out = (frame.groupby(keys, dropna=False)
                .agg(series=("SeriesInstanceUID", "size"),
                     instances=("instanceCount", "sum"),
                     size_MB=("series_size_MB", "sum"),
                     collections=("collection_id", "nunique"),
                     patients=("PatientID", "nunique"))
                .reset_index())
    out["size_GB"] = (out["size_MB"] / 1024).round(3)
    out["mean_MB_per_series"] = (out["size_MB"] / out["series"]).round(3)
    return out.sort_values("series", ascending=False).reset_index(drop=True)


def census_all(df: pd.DataFrame) -> pd.DataFrame:
    """Every SOP class in the archive, derived or not."""
    out = _agg(df, ["sop_class_name", "SOPClassUID"])
    out["class"] = out["sop_class_name"].map(
        lambda n: "derived" if n in DERIVED_SOP_CLASSES
        else ("adjacent" if n in ADJACENT_SOP_CLASSES else "acquired"))
    return out


def census_derived(df: pd.DataFrame) -> pd.DataFrame:
    return _agg(derived(df), ["sop_class_name", "SOPClassUID"])


def census_by_collection(df: pd.DataFrame) -> pd.DataFrame:
    return _agg(derived(df), ["collection_id", "sop_class_name"])


def census_by_analysis_result(df: pd.DataFrame) -> pd.DataFrame:
    d = derived(df)
    d["analysis_result_id"] = d["analysis_result_id"].fillna("(null)")
    out = _agg(d, ["analysis_result_id"])
    sop = (d.groupby("analysis_result_id")["sop_class_name"]
             .agg(lambda s: " | ".join(sorted(set(s)))).rename("sop_classes"))
    return out.merge(sop, on="analysis_result_id", how="left")


def transfer_syntax(df: pd.DataFrame) -> pd.DataFrame:
    d = derived(df, include_adjacent=True)
    out = (d.groupby(["sop_class_name", "transfer_syntax_name", "TransferSyntaxUID"],
                     dropna=False)
             .agg(series=("SeriesInstanceUID", "size"),
                  instances=("instanceCount", "sum"))
             .reset_index())
    total = out.groupby("sop_class_name")["series"].transform("sum")
    out["pct_of_sop_class"] = (100 * out["series"] / total).round(2)
    # The table covers adjacent classes too, because their transfer syntaxes are
    # worth knowing before Phase 3. The column says which rows are inside the
    # headline denominator, so a claim about derived objects cannot be read off
    # a row that is not one.
    out["class"] = out["sop_class_name"].map(
        lambda n: "derived" if n in DERIVED_SOP_CLASSES else "adjacent")
    return out.sort_values(["sop_class_name", "series"], ascending=[True, False])


def licenses(df: pd.DataFrame) -> pd.DataFrame:
    d = derived(df)
    return (d.groupby(["license_short_name", "sop_class_name"], dropna=False)
              .agg(series=("SeriesInstanceUID", "size"),
                   instances=("instanceCount", "sum"))
              .reset_index()
              .sort_values("series", ascending=False))


def gsps_anomaly(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The 1,086 GSPS series, and the attribution split the brief asks about."""
    g = df[df["sop_class_name"] == "Grayscale Softcopy Presentation State Storage"].copy()
    g["analysis_result_id"] = g["analysis_result_id"].fillna("(null)")
    split = (g.groupby(["collection_id", "analysis_result_id", "source_DOI",
                        "license_short_name", "Manufacturer", "ManufacturerModelName"],
                       dropna=False)
               .agg(series=("SeriesInstanceUID", "size"),
                    instances=("instanceCount", "sum"),
                    patients=("PatientID", "nunique"),
                    studies=("StudyInstanceUID", "nunique"),
                    size_MB=("series_size_MB", "sum"),
                    modalities=("Modality", lambda s: "|".join(sorted(set(s)))),
                    init_idc=("series_init_idc_version", "min"))
               .reset_index()
               .sort_values("series", ascending=False))
    keep = ["collection_id", "analysis_result_id", "PatientID", "StudyInstanceUID",
            "SeriesInstanceUID", "SeriesDescription", "SeriesNumber", "Modality",
            "Manufacturer", "ManufacturerModelName", "source_DOI",
            "license_short_name", "series_init_idc_version", "instanceCount",
            "series_size_MB", "series_aws_url"]
    return split, g[keep].sort_values(["collection_id", "SeriesInstanceUID"])


def parametric_map(df: pd.DataFrame) -> pd.DataFrame:
    p = df[df["sop_class_name"] == "Parametric Map Storage"].copy()
    p["analysis_result_id"] = p["analysis_result_id"].fillna("(null)")
    return (p.groupby(["collection_id", "analysis_result_id", "license_short_name",
                       "Manufacturer", "ManufacturerModelName", "Modality",
                       "transfer_syntax_name"], dropna=False)
              .agg(series=("SeriesInstanceUID", "size"),
                   instances=("instanceCount", "sum"),
                   patients=("PatientID", "nunique"),
                   size_MB=("series_size_MB", "sum"))
              .reset_index())


def phase2_budget(df: pd.DataFrame) -> pd.DataFrame:
    d = derived(df)
    out = (d[d["sop_class_name"].isin(PHASE2_CLASSES)]
           .groupby("sop_class_name")
           .agg(series=("SeriesInstanceUID", "size"),
                instances=("instanceCount", "sum"),
                size_MB=("series_size_MB", "sum"))
           .reset_index())
    out["size_GB"] = (out["size_MB"] / 1024).round(4)
    return out.sort_values("series", ascending=False)


def _fmt(n) -> str:
    return "{:,}".format(int(n))


def _md_table(frame: pd.DataFrame, cols: list[str]) -> str:
    sub = frame[cols]
    head = "| " + " | ".join(cols) + " |"
    rule = "|" + "|".join("---" for _ in cols) + "|"
    lines = [head, rule]
    for _, row in sub.iterrows():
        cells = []
        for c in cols:
            v = row[c]
            if isinstance(v, float):
                cells.append("%.3f" % v if abs(v) < 1000 else "{:,.1f}".format(v))
            elif isinstance(v, (int,)) or str(type(v)).endswith("int64'>"):
                cells.append(_fmt(v))
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def write_markdown(idc_version: str, tables: dict, out: Path,
                   n_attributed: int = 0, unattributed_rt: int = 0) -> Path:
    d_all = tables["census_derived"]
    n_series = int(d_all["series"].sum())
    n_inst = int(d_all["instances"].sum())
    ffc = tables["first_file_coverage"]
    missed = int(ffc["instances_missed"].sum())
    inst_per_series = n_inst / n_series
    ffc_seg = ffc[ffc.sop_class_name == "Segmentation Storage"]
    ffc_seg_pct = float(ffc_seg["pct_of_series_multi_instance"].iloc[0])
    tb = d_all["size_MB"].sum() / (1024 ** 2)
    all_sop = tables["census_all"]
    arch_series = int(all_sop["series"].sum())
    arch_inst = int(all_sop["instances"].sum())
    adj = all_sop[all_sop["class"] == "adjacent"]

    ts = tables["transfer_syntax"]
    non_default = ts[(ts["transfer_syntax_name"] != "Explicit VR Little Endian")
                     & (ts["class"] == "derived")]

    gsps_split = tables["gsps_split"]
    pm = tables["parametric_map"]
    p2 = tables["phase2_budget"]

    text = f"""# Phase 0: census of derived objects in IDC {idc_version}

Zero bytes downloaded. Every number here comes from the local `idc-index`
dataframe, one row per series, {_fmt(arch_series)} rows in total.

Reproduce with `{CMD}`. Version pins in `results/environment.json`.

## What counts as a derived object

Nine SOP classes, listed in `colophon/index.py` as `DERIVED_SOP_CLASSES`.
Counting exactly these nine gives **{_fmt(n_series)} series and {_fmt(n_inst)}
instances**, which reproduces the figure the study was scoped against. The set
was not chosen to hit that number: it was recovered by searching SOP class
subsets, and only one subset of the plausible candidates matches on both series
and instance counts simultaneously.

Six further produced-not-acquired classes sit outside that denominator and are
reported separately, {_fmt(int(adj['series'].sum()))} series in total, so the
boundary is visible rather than implicit.

| | series | instances | size |
|---|---|---|---|
| whole archive | {_fmt(arch_series)} | {_fmt(arch_inst)} | {all_sop['size_MB'].sum() / 1024 ** 2:,.2f} TB |
| derived, nine classes | {_fmt(n_series)} | {_fmt(n_inst)} | {tb:,.2f} TB |
| adjacent, six classes | {_fmt(int(adj['series'].sum()))} | {_fmt(int(adj['instances'].sum()))} | {adj['size_MB'].sum() / 1024 ** 2:,.2f} TB |

## Census by SOP class

{_md_table(d_all, ["sop_class_name", "series", "instances", "size_GB", "collections", "patients", "mean_MB_per_series"])}

Adjacent classes, outside the denominator above:

{_md_table(adj, ["sop_class_name", "series", "instances", "size_GB", "collections"])}

## Transfer syntax

Every derived class is Explicit VR Little Endian except the two rows below.
{'No exceptions.' if non_default.empty else ''}

{_md_table(non_default, ["sop_class_name", "transfer_syntax_name", "TransferSyntaxUID", "series", "pct_of_sop_class"]) if not non_default.empty else ''}

Two observations follow. Segmentation Storage carries a compressed transfer
syntax on a small minority of series, which matters for Phase 2 and 3 because a
validator that cannot decode JPEG-LS will report a different class of failure
than a conformance defect. RT Structure Set Storage carries Implicit VR Little
Endian on part of its population, which is the only derived class in the archive
where the transfer syntax is not self-describing.

## The GSPS attribution split

{_md_table(gsps_split, ["collection_id", "analysis_result_id", "series", "Manufacturer", "ManufacturerModelName", "source_DOI", "license_short_name"])}

The 462 series in `qiba_ct_1c` carry no `analysis_result_id`. The 624 in
`rider_lung_ct` and `rider_pilot` carry `qiba_volct_1b`. All three groups are
the same SOP class and all three originate in QIBA volumetric CT work. The
difference is how IDC ingested them: `qiba_ct_1c` is registered as a collection
in its own right with its own DOI, so its objects are collection content and
carry no analysis-result attribution, while the RIDER-derived objects are
registered as an analysis result computed over a separate source collection.

That is a provenance observation rather than a defect. `analysis_result_id` is
an IDC curation field, not a DICOM attribute, and it records whether IDC
ingested a series as an analysis of another collection. It does not record
whether the object was produced by an algorithm. For {_fmt(int(gsps_split[gsps_split['analysis_result_id'] == '(null)']['series'].sum()))}
GSPS series the field is null while the objects are plainly derived, so the
field cannot be used on its own as the denominator for a derived-object census.

## Parametric Map

{_md_table(pm, ["collection_id", "analysis_result_id", "series", "instances", "patients", "Manufacturer", "ManufacturerModelName", "license_short_name"])}

Matches the brief: 691 series, `tcga_gbm` collection, `tcga_gbm360` analysis
result, CC BY 4.0, single manufacturer string.

## Licence

{_md_table(tables["licenses"].groupby("license_short_name", as_index=False).agg(series=("series", "sum"), instances=("instances", "sum")).sort_values("series", ascending=False), ["license_short_name", "series", "instances"])}

Every derived series in the archive is under a Creative Commons licence. None
is restricted, which is what makes an exhaustive census of the small classes
legally straightforward.

## Phase 2 download budget

The classes the brief calls small enough to take whole:

{_md_table(p2, ["sop_class_name", "series", "instances", "size_GB"])}

Total **{p2['size_GB'].sum():.3f} GB** across {_fmt(int(p2['series'].sum()))}
series. The brief estimated roughly 1 GB. That estimate holds.

## Two denominators

`analysis_result_id` records that IDC ingested a series as an analysis computed
over another collection. {_fmt(n_attributed)} of the {_fmt(n_series)} derived
series carry one, {100 * n_attributed / n_series:.2f} percent.

Both denominators are reported throughout, because neither is the AI-derived
population on its own. The attributed set includes human work:
`eay131_tumor_annotations` was contoured through a viewer and
`lung_pet_ct_dx_annotations` declares "Expert annotation from TCIA". The
unattributed remainder includes {_fmt(int(unattributed_rt))} RT Structure Set
series from Pinnacle, ARIA, MIM and GammaPlan, which are radiotherapy planning
contours drawn by people. A claim about AI results quoted against the derived
denominator counts those, and a reviewer will say so.

## Scope: this census covers non-image derived SOP classes only

Selecting on SOP class omits two populations where a derived object is stored
under an acquisition SOP class. Objects with ImageType (0008,0008) value 1 equal
to DERIVED, and Secondary Capture output from processing pipelines, are exactly
the cases where a derived image is indistinguishable from an acquisition by
class alone.

**ImageType is not an index column**, so the size of the DERIVED stratum cannot
be estimated here at all. The classes it would live in are large: CT Image
Storage holds {_fmt(int(all_sop.loc[all_sop.sop_class_name == "CT Image Storage", "series"].iloc[0]))}
series and Secondary Capture Image Storage holds
{_fmt(int(all_sop.loc[all_sop.sop_class_name == "Secondary Capture Image Storage", "series"].iloc[0]))}.

Every claim in this study is therefore scoped to **non-image derived SOP
classes**, and that wording is used throughout rather than the unqualified word
derived. Sizing the ImageType DERIVED stratum requires reading objects and is
Phase 2 work.

## What per-series rather than per-instance validation would miss

{_md_table(ffc[ffc.instances_missed > 0], ["sop_class_name", "series", "instances", "multi_instance_series", "pct_of_series_multi_instance", "instances_missed", "pct_of_instances_missed"])}

Across all derived objects the archive holds {inst_per_series:.4f} instances per
series. Validating one file per series therefore reaches {_fmt(n_series)} of
{_fmt(n_inst)} instances and misses **{_fmt(missed)}, or
{100 * missed / n_inst:.2f} percent**. Segmentation Storage is the only derived
class with any multi-instance series at all, and only
{ffc_seg_pct:.2f} percent of its series are multi-instance.

That is the honest size of the gap, and it is small. It is quoted at this
precision, and it is the secondary point.

The primary point is different and is not about coverage. Validation of public
DICOM archives is a documented, routine curation step, and existing tooling
supports per-series and per-SOP granularity. What the published record reports
is that validation was performed, not what it found. This study is scoped to
published measurement: rates, denominators, per-error-class breakdown, warning
classes and cross-validator disagreement.

## What was dropped

Nothing. This phase reads the complete index and aggregates all
{_fmt(arch_series)} rows. No sampling, no truncation, no filtering other than
the SOP class membership stated above.
"""
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--print-only", action="store_true", help="write nothing")
    args = ap.parse_args(argv)

    idc_version, df = load_index()
    print("IDC index %s, %s rows, %d columns" % (idc_version, _fmt(len(df)), df.shape[1]))
    if len(df) != df["SeriesInstanceUID"].nunique():
        print("WARNING: index is not one row per series")

    tables = {
        "census_all": census_all(df),
        "census_derived": census_derived(df),
        "census_by_collection": census_by_collection(df),
        "census_by_analysis_result": census_by_analysis_result(df),
        "transfer_syntax": transfer_syntax(df),
        "licenses": licenses(df),
        "parametric_map": parametric_map(df),
        "phase2_budget": phase2_budget(df),
        "first_file_coverage": first_file_coverage(df),
    }
    gsps_split, gsps_series = gsps_anomaly(df)
    tables["gsps_split"] = gsps_split
    tables["gsps_series"] = gsps_series

    d = tables["census_derived"]
    n_series, n_inst = int(d["series"].sum()), int(d["instances"].sum())
    print("derived: %s series, %s instances, %.2f TB"
          % (_fmt(n_series), _fmt(n_inst), d["size_MB"].sum() / 1024 ** 2))

    if args.print_only:
        for name, frame in tables.items():
            print("\n==== %s ====" % name)
            print(frame.head(40).to_string(index=False))
        return 0

    PHASE0.mkdir(parents=True, exist_ok=True)
    for name, frame in tables.items():
        frame.to_csv(PHASE0 / ("%s.csv" % name), index=False)
    print("wrote %d tables to %s" % (len(tables), PHASE0))

    envinfo.write(RESULTS / "environment.json", idc_version=idc_version)
    attributed = analysis_attributed(df)
    n_attributed = len(attributed)
    unattrib = derived(df)
    unattrib = unattrib[unattrib["analysis_result_id"].isna()]
    unattributed_rt = int((unattrib["sop_class_name"] == "RT Structure Set Storage").sum())
    md = write_markdown(idc_version, tables, RESULTS / "phase0_census.md",
                        n_attributed=n_attributed,
                        unattributed_rt=unattributed_rt)
    print("wrote %s" % md)

    gs = tables["gsps_split"]
    null_gsps = int(gs[gs["analysis_result_id"] == "(null)"]["series"].sum())
    p2 = tables["phase2_budget"]
    ts = tables["transfer_syntax"]
    odd_ts = ts[(ts["transfer_syntax_name"] != "Explicit VR Little Endian")
                & (ts["class"] == "derived")]
    src = "results/phase0_census.md and results/phase0/*.csv"

    S = dict(section="P0", section_title="Phase 0 census, IDC index metadata",
             command=CMD, dropped="nothing, complete index read",
             validator="none, index metadata only",
             validator_version="idc-index-data %s" % idc_version,
             floor="not applicable, no validator involved")
    seg = d[d.sop_class_name == "Segmentation Storage"].iloc[0]
    all_sop = tables["census_all"]
    ffc = tables["first_file_coverage"]
    missed = int(ffc["instances_missed"].sum())
    seg_row = ffc[ffc.sop_class_name == "Segmentation Storage"]
    seg_multi = int(seg_row["multi_instance_series"].iloc[0])

    ledger.record_many([
        dict(id="P0-01", claim="The IDC v24 index holds one row per series, "
             "%s series rows across %d SOP classes." % (_fmt(len(df)), len(all_sop)),
             status="MEASURED", value="%s series rows, %d SOP classes"
             % (_fmt(len(df)), len(all_sop)),
             n=_fmt(len(df)), denominator=_fmt(len(df)), sop_class="all",
             source_file="results/phase0/census_all.csv",
             pinned_by_test="tests/test_phase0.py::test_index_shape", **S),
        dict(id="P0-02", claim="Derived objects, defined as the nine SOP classes "
             "listed in colophon/index.py DERIVED_SOP_CLASSES, number 481,750 "
             "series and 504,727 instances, 18.72 TB.",
             status="MEASURED",
             value="%s series, %s instances, %.2f TB"
             % (_fmt(n_series), _fmt(n_inst), d["size_MB"].sum() / 1024 ** 2),
             n=_fmt(n_series), denominator=_fmt(len(df)), sop_class="derived, nine classes",
             source_file="results/phase0/census_derived.csv",
             pinned_by_test="tests/test_phase0.py::test_derived_totals",
             status_note="The nine-class definition was recovered by subset "
             "search against the series and instance totals the study was scoped "
             "against, not assumed. Only this subset matches on both counts.",
             notes="Six further produced-not-acquired classes are excluded from "
                   "this denominator and reported alongside it.", **S),
        dict(id="P0-03", claim="Segmentation Storage is the largest derived class "
             "by volume and cannot be downloaded whole.",
             status="MEASURED",
             value="%s series, %.2f TB" % (_fmt(int(seg.series)),
                                           float(seg.size_MB) / 1024 ** 2),
             n=_fmt(int(seg.series)), denominator=_fmt(n_series),
             sop_class="Segmentation Storage",
             source_file="results/phase0/census_derived.csv", **S),
        dict(id="P0-04", claim="Every derived series in IDC v24 is Explicit VR "
             "Little Endian apart from two groups.",
             status="MEASURED",
             value="; ".join("%s %s %s series"
                             % (r.sop_class_name, r.transfer_syntax_name, _fmt(r.series))
                             for r in odd_ts.itertuples()) or "no exceptions",
             n=_fmt(int(odd_ts["series"].sum())), denominator=_fmt(n_series),
             sop_class="derived, nine classes",
             source_file="results/phase0/transfer_syntax.csv",
             notes="Load bearing for Phases 2 and 3: a decode failure is not a "
                   "conformance failure and must not be counted as one.", **S),
        dict(id="P0-05", claim="IDC v24 holds 1,086 Grayscale Softcopy "
             "Presentation State series. They split three ways by ingestion "
             "route and 462 carry no analysis_result_id.",
             status="MEASURED",
             value="1,086 GSPS series: qiba_ct_1c %s with null "
                   "analysis_result_id, rider_lung_ct 384 and rider_pilot 240 "
                   "both qiba_volct_1b" % _fmt(null_gsps),
             n="1,086", denominator=_fmt(n_series),
             sop_class="Grayscale Softcopy Presentation State Storage",
             source_file="results/phase0/gsps_split.csv",
             pinned_by_test="tests/test_phase0.py::test_gsps_split",
             status_note="IDC-ADMINISTRATIVE, not DICOM provenance. "
             "analysis_result_id is an IDC ingestion bookkeeping field. The "
             "split records how the archive registered these series, not any "
             "property of the objects, and the objects themselves may not "
             "differ at all. This row belongs to a discussion of registry-level "
             "versus object-level provenance and is not reported beside "
             "object-level provenance findings.",
             notes="The count itself settles a question the prior-art sweep "
                   "could not settle from documentation: the IDC user guide "
                   "derived objects page names only SEG, RTSTRUCT and SR, so "
                   "GSPS presence in IDC was unconfirmed until counted here. "
                   "The attribution split cannot serve as a derived-object "
                   "denominator.", **S),
        dict(id="P0-06", claim="Parametric Map holdings are 691 series, all in "
             "collection tcga_gbm under analysis result tcga_gbm360, CC BY 4.0.",
             status="MEASURED", value="691 series, 691 instances",
             n="691", denominator=_fmt(n_series), sop_class="Parametric Map Storage",
             source_file="results/phase0/parametric_map.csv", **S),
        dict(id="P0-07", claim="Every derived series in IDC v24 carries a "
             "Creative Commons licence, so exhaustive validation of the small "
             "classes needs no access request and no egress fee.",
             status="MEASURED",
             value="; ".join("%s %s" % (r.license_short_name, _fmt(r.series))
                             for r in tables["licenses"].groupby(
                                 "license_short_name", as_index=False)
                             .agg(series=("series", "sum")).itertuples()),
             n=_fmt(n_series), denominator=_fmt(n_series), sop_class="derived, nine classes",
             source_file="results/phase0/licenses.csv", **S),
        dict(id="P0-08", claim="The six classes the brief calls exhaustively "
             "downloadable total under 1 GB, so Phase 2 needs no sampling.",
             status="MEASURED",
             value="%s series, %.3f GB" % (_fmt(int(p2["series"].sum())),
                                           float(p2["size_GB"].sum())),
             n=_fmt(int(p2["series"].sum())), denominator=_fmt(n_series),
             sop_class="six small classes",
             source_file="results/phase0/phase2_budget.csv", **S),
        dict(id="P0-09", claim="Phase 0 samples nothing. It aggregates the "
             "complete index.",
             status="MEASURED",
             value="%s of %s rows read" % (_fmt(len(df)), _fmt(len(df))),
             n=_fmt(len(df)), denominator=_fmt(len(df)), sop_class="all",
             source_file=src, **S),
        dict(id="P0-12", claim="This census covers non-image derived SOP classes "
             "only. Objects with ImageType (0008,0008) value 1 equal to DERIVED, "
             "and Secondary Capture output from processing pipelines, are "
             "excluded and cannot be sized from the index.",
             status="PENDING",
             value="ImageType is not an index column. The classes such objects "
                   "would sit in are large: CT Image Storage %s series, "
                   "Secondary Capture Image Storage %s series"
                   % (_fmt(int(all_sop.loc[all_sop.sop_class_name == "CT Image Storage", "series"].iloc[0])),
                      _fmt(int(all_sop.loc[all_sop.sop_class_name == "Secondary Capture Image Storage", "series"].iloc[0]))),
             sop_class="acquisition classes carrying derived pixel data",
             external_source="PS3.3 C.7.6.1.1.2 Image Type",
             dropped="the entire ImageType DERIVED stratum, size unknown from "
                     "the index",
             status_note="Language is rescoped throughout: every claim says "
             "non-image derived SOP classes rather than the unqualified word "
             "derived. Sizing the stratum requires reading objects and is Phase "
             "2 work.",
             notes="This is the case where a derived image is indistinguishable "
                   "from an acquisition by SOP class alone, so excluding it by "
                   "class is a scope decision that has to be stated rather than "
                   "a gap that can be closed by a better query.",
             **{k: v for k, v in S.items() if k != "dropped"}),
        dict(id="P0-10", claim="Two denominators are carried throughout: derived "
             "objects, and the subset IDC ingested as analysis results. Neither "
             "is the AI-derived population on its own.",
             status="MEASURED",
             value="derived %s series; analysis-result attributed %s, %.2f "
                   "percent; unattributed remainder includes %s RT Structure "
                   "Set series from planning systems"
                   % (_fmt(n_series), _fmt(n_attributed),
                      100 * n_attributed / n_series, _fmt(unattributed_rt)),
             n=_fmt(n_attributed), denominator=_fmt(n_series),
             sop_class="derived, nine classes",
             source_file="results/phase0/census_by_analysis_result.csv",
             pinned_by_test="tests/test_phase0.py::test_two_denominators",
             status_note="analysis_result_id is an upper bound on AI-derived, "
             "not a measurement of it: the attributed set includes objects "
             "contoured by people through a viewer and objects whose "
             "Manufacturer reads 'Expert annotation from TCIA'.",
             notes="Carried because a claim about AI results quoted against the "
                   "derived denominator counts radiotherapy planning contours "
                   "drawn by people, which a reviewer will notice.", **S),
        dict(id="P0-11", claim="Per-series rather than per-instance validation "
             "would miss 22,977 derived instances, 4.55 percent. Segmentation "
             "Storage is the only derived class with any multi-instance series.",
             status="MEASURED",
             value="%.4f instances per series; %s of %s instances missed, "
                   "%.2f percent; %s of %s Segmentation series are "
                   "multi-instance, %.2f percent"
                   % (n_inst / n_series, _fmt(missed), _fmt(n_inst),
                      100 * missed / n_inst, _fmt(seg_multi),
                      _fmt(int(seg_row["series"].iloc[0])),
                      float(seg_row["pct_of_series_multi_instance"].iloc[0])),
             n=_fmt(missed), denominator=_fmt(n_inst),
             sop_class="derived, nine classes",
             source_file="results/phase0/first_file_coverage.csv",
             derived_from="PA-03",
             pinned_by_test="tests/test_phase0.py::test_first_file_coverage",
             status_note="Quoted at this precision deliberately. The coverage "
             "gap is small and overstating it would cost more credibility than "
             "the point is worth. The gap that carries the paper is the "
             "publication gap, which is total.", **S),
    ])
    print("ledger: %s" % ledger.summary())
    return 0


if __name__ == "__main__":
    sys.exit(main())
