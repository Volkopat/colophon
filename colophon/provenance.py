"""Claim 3: do derived DICOM objects in IDC identify their producer.

Runs entirely from the `idc-index` dataframe. Zero bytes downloaded.

Scope, stated up front because it bounds the claim. The brief names five
provenance carriers:

    Manufacturer                     (0008,0070)   in the index
    ManufacturerModelName            (0008,1090)   in the index
    ImplementationVersionName        (0002,0013)   NOT in the index
    ContributingEquipmentSequence    (0018,A001)   NOT in the index
    algorithm identification         various       NOT in the index

Only the first two are index columns. The other three live in the objects and
can only be measured once files are fetched, which is Phase 2 and Phase 3. This
module therefore settles two of the five carriers across the whole population,
and logs the remaining three as pending rather than quietly narrowing the claim.

Nothing here decides that an object is wrong. It classifies the declared
strings against an explicit, published rule table, reports the rates, and
states which question the index cannot answer.

Usage:
    python -m colophon.provenance
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

from . import ledger
from .index import (ADJACENT_SOP_CLASSES, DERIVED_SOP_CLASSES, derived,
                    load_index, _fmt, _md_table)
from .paths import PHASE0, RESULTS

CMD = "python -m colophon.provenance"

# --- the classification rule table -------------------------------------------
# Ordered. The first pattern that matches a string wins. Every rule is a plain
# substring or regex over the lowercased value, so a reader can check any single
# assignment by eye. Categories describe what kind of entity the string names,
# not whether naming it is correct.
#
# "encoder" is a general purpose DICOM writing library: it can encode any
# analysis and does not identify which one produced the object.
# "conversion" is a string that states on its face that the object was converted
# by a party other than the one that computed the result.
# "application" is an interactive annotation or viewing program.
# "acquisition_vendor" is a scanner vendor string, which on a derived object is
# the identity of equipment that did not produce the object.
# "named_analysis" is a string that names a specific model, pipeline or study.
# "institution" names an organisation without naming what it ran.

RULES: list[tuple[str, str, str]] = [
    ("encoder", "dcmqi", r"dcmqi"),
    ("encoder", "highdicom", r"highdicom"),
    ("encoder", "pydicom-seg", r"pydicom-seg"),
    ("encoder", "pydicom", r"^pydicom\b"),
    ("encoder", "PixelMed", r"pixelmed"),
    ("encoder", "QIICR", r"^qiicr$"),
    ("encoder", "QIICR Reporting", r"fedorov/reporting"),
    ("encoder", "plastimatch", r"plastimatch"),
    ("encoder", "SUVFactorCalculator", r"suvfactorcalculator"),
    ("encoder", "XSLT", r"^xslt"),
    ("conversion", "converted by IDC", r"converted by imaging data commons"),
    ("conversion", "converted, other", r"\bconvert(ed|er|sion)\b"),
    ("conversion", "IDC", r"^idc$"),
    ("application", "OHIF", r"\bohif\b"),
    ("application", "3D Slicer", r"3d slicer|slicer community"),
    ("application", "Aperio ImageScope", r"aperio imagescope"),
    ("application", "MIM", r"^mim\b|mim software"),
    ("application", "ARIA", r"^aria\b"),
    ("application", "Pinnacle", r"pinnacle"),
    ("application", "GammaPlan", r"gammaplan"),
    ("acquisition_vendor", "GE", r"^ge\b|general electric"),
    ("acquisition_vendor", "Siemens", r"siemens"),
    ("acquisition_vendor", "Philips", r"philips"),
    ("acquisition_vendor", "Toshiba", r"toshiba"),
    ("acquisition_vendor", "Varian", r"varian"),
    ("acquisition_vendor", "Elekta", r"elekta"),
    ("acquisition_vendor", "ADAC", r"^adac"),
    ("acquisition_vendor", "PMOD", r"^pmod"),
    ("acquisition_vendor", "Leica", r"leica"),
    ("acquisition_vendor", "CoreLab Partners", r"corelab partners"),
    ("named_analysis", "Sybil", r"^sybil$"),
    ("named_analysis", "GBM360", r"gbm360"),
    ("named_analysis", "Pan-Cancer-Nuclei-Seg", r"pan-cancer-nuclei-seg"),
    ("named_analysis", "TIL model", r"\btil (inception|custom)"),
    ("named_analysis", "FNLCR RMS model", r"fnlcr_ivg_rms"),
    ("named_analysis", "DIRS2", r"^dirs2$"),
    ("named_analysis", "BMDeep", r"bmdeep"),
    ("named_analysis", "LocationDesignatorSynthesizer", r"locationdesignatorsynthesizer"),
    ("institution", "Stony Brook University", r"stony brook"),
    ("institution", "NCI/FNLCR", r"nci/fnlcr"),
    ("institution", "Stanford", r"stanford"),
    ("institution", "Erlangen / Fraunhofer MEVIS", r"erlangen|mevis"),
    ("institution", "Herrmann Lab", r"herrmann lab"),
    ("institution", "Gevaert Lab", r"gevaert"),
    ("institution", "TCIA expert annotation", r"expert annotation from tcia"),
    ("institution", "Open Health Imaging Foundation", r"open health imaging foundation"),
]


def classify(value) -> tuple[str, str]:
    """Return (category, matched_rule) for one declared string."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "absent", "null"
    s = str(value).strip()
    if s == "":
        return "absent", "empty string"
    low = s.lower()
    for category, label, pattern in RULES:
        if re.search(pattern, low):
            return category, label
    return "unclassified", s[:60]


def population(frame: pd.DataFrame, column: str, by: list[str]) -> pd.DataFrame:
    """Population rate for one attribute, nulls and empty strings counted apart."""
    work = frame.copy()
    v = work[column]
    work["_null"] = v.isna()
    work["_empty"] = (~v.isna()) & (v.fillna("").astype(str).str.strip() == "")
    work["_populated"] = ~(work["_null"] | work["_empty"])
    out = (work.groupby(by, dropna=False)
               .agg(series=("SeriesInstanceUID", "size"),
                    null=("_null", "sum"),
                    empty=("_empty", "sum"),
                    populated=("_populated", "sum"),
                    distinct_values=(column, "nunique"))
               .reset_index())
    out["pct_populated"] = (100 * out["populated"] / out["series"]).round(2)
    out["attribute"] = column
    return out.sort_values("series", ascending=False)


def value_distribution(frame: pd.DataFrame, column: str) -> pd.DataFrame:
    counts = frame[column].fillna("(null)").replace("", "(empty)").value_counts()
    rows = []
    for value, n in counts.items():
        cat, label = classify(None if value == "(null)" else
                              ("" if value == "(empty)" else value))
        rows.append({"attribute": column, "value": value, "series": int(n),
                     "pct_of_derived": round(100 * n / len(frame), 4),
                     "category": cat, "rule": label})
    return pd.DataFrame(rows)


def categorise(frame: pd.DataFrame) -> pd.DataFrame:
    """Category of the declared identity, per series, for both attributes."""
    out = frame.copy()
    for col, prefix in (("Manufacturer", "mfr"), ("ManufacturerModelName", "model")):
        applied = out[col].map(classify)
        out["%s_category" % prefix] = [c for c, _ in applied]
        out["%s_rule" % prefix] = [r for _, r in applied]
    return out


def spelling_variants(frame: pd.DataFrame) -> pd.DataFrame:
    """One encoder, many declared spellings. Counted per encoder rule."""
    tagged = categorise(frame)
    enc = tagged[tagged["model_category"].isin({"encoder", "conversion", "application"})]
    rows = []
    for rule, sub in enc.groupby("model_rule"):
        vals = sub["ManufacturerModelName"].fillna("(null)").value_counts()
        rows.append({
            "rule": rule,
            "category": sub["model_category"].iloc[0],
            "distinct_spellings": int(len(vals)),
            "series": int(len(sub)),
            "spellings": " || ".join("%s [%s]" % (k, _fmt(v)) for k, v in vals.items()),
        })
    return pd.DataFrame(rows).sort_values("series", ascending=False)


# --- the four-bucket taxonomy -------------------------------------------------
# Exhaustive and ordered: every derived series lands in exactly one bucket, and
# the buckets sum to the population. The point of exhaustiveness is that a
# residual cannot hide a counter-example, which is what happened when this was
# first reported as an encoder share against a named-model share and left 11.5
# percent of the population unaccounted for.

# A DICOM encoding library: software whose purpose is to write DICOM, which can
# encode any analysis and so identifies none.
BUCKET_ENCODER = re.compile(
    r"dcmqi|highdicom|pydicom-seg|fedorov/reporting|suvfactorcalculator", re.I)
CONVERSION = re.compile(r"convert", re.I)
# Strings that state absence rather than a value. "NA" is absence written out.
ABSENT_VALUES = {"", "NA", "N/A", "NONE", "UNKNOWN"}

# One string sits on the boundary and is recorded rather than hidden.
# Plastimatch, on one RT Structure Set series in collection lctsc, is declared as
# both Manufacturer and ManufacturerModelName. It is an image registration
# toolkit that can write DICOM rather than a library whose purpose is encoding,
# so it is counted as `other`. Counting it as an encoder moves one series and
# changes no reported figure to its stated precision.
BOUNDARY_CASES = {
    "Plastimatch": "counted as other, not encoder: a registration toolkit that "
                   "can write DICOM rather than an encoding library. 1 series.",
}

BUCKET_ORDER = ["encoder_only", "producer_and_converter", "other", "absent"]
BUCKET_LABEL = {
    "encoder_only": "encoding library only",
    "producer_and_converter": "producing entity and converter both named",
    "other": "other: named model, scanner, planning system or viewer",
    "absent": "absent or NA",
}


def bucket_of(manufacturer, model) -> str:
    """Which of the four exhaustive buckets a declared pair falls into."""
    mfr = "" if manufacturer is None or pd.isna(manufacturer) else str(manufacturer).strip()
    mod = "" if model is None or pd.isna(model) else str(model).strip()
    if mod.upper() in ABSENT_VALUES:
        return "absent"
    if BUCKET_ENCODER.search(mod):
        return "encoder_only"
    if CONVERSION.search(mfr) or CONVERSION.search(mod):
        return "producer_and_converter"
    return "other"


# --- the competing conventions ------------------------------------------------
# What a given pair is trying to say. These are the shapes actually present, not
# a normative list. Ordered: first match wins.
CONVENTION_RULES: list[tuple[str, str, str]] = [
    ("encoding library as manufacturer",
     r"^(qiicr|highdicom|pydicom-seg|pixelmed|3d slicer community)$",
     r"dcmqi|highdicom|pydicom-seg|fedorov/reporting|xslt|com\.pixelmed"),
    ("producing lab plus model plus converter", r"convert", r"."),
    ("institution as manufacturer, model named", r".", r"pan-cancer-nuclei-seg|fnlcr_ivg"),
    ("viewer or workstation as manufacturer", r".",
     r"ohif|imagescope|^mim$|^aria|pinnacle|gammaplan|external beam planning"),
    ("curator as manufacturer", r"^(idc|expert annotation from tcia)$", r"."),
]


def convention_of(manufacturer, model, inherited: bool = False,
                  analysis_result=None) -> str:
    """Name the convention a declared pair follows.

    `inherited` comes from the measured acquisition cross-reference rather than
    from a list of vendor names, so the scanner case is identified by the
    archive itself.
    """
    mfr = ("" if manufacturer is None or pd.isna(manufacturer)
           else str(manufacturer).strip()).lower()
    mod = ("" if model is None or pd.isna(model) else str(model).strip()).lower()
    model_absent = mod.upper() in ABSENT_VALUES
    if model_absent and not mfr:
        return "nothing declared"
    for label, mfr_pattern, mod_pattern in CONVENTION_RULES:
        if re.search(mfr_pattern, mfr) and re.search(mod_pattern, mod):
            return label
    if inherited:
        return "acquisition equipment as manufacturer"
    if model_absent:
        # A manufacturer that shares a distinctive token with the analysis IDC
        # attributes the series to is naming the producing model in the
        # manufacturer field, which is what nlst_sybil does with "Sybil".
        ar = ("" if analysis_result is None or pd.isna(analysis_result)
              else str(analysis_result)).lower()
        tokens = {t for t in re.split(r"[^a-z0-9]+", ar)
                  if len(t) > 2 and t not in _TOKEN_STOP}
        if tokens and any(t in mfr for t in tokens):
            return "producing model as manufacturer, model field absent"
        return "manufacturer only, model absent"
    return "unclassified convention"


def conventions(frame: pd.DataFrame,
                inherited: pd.Series | None = None
                ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return (per-series, bucket table, convention table)."""
    d = frame.copy()
    pairs = list(zip(d["Manufacturer"], d["ManufacturerModelName"]))
    d["bucket"] = [bucket_of(a, b) for a, b in pairs]
    if inherited is None:
        inh = [False] * len(d)
    else:
        inh = list(inherited.reindex(d.index).fillna(False))
    d["convention"] = [
        convention_of(a, b, bool(i), ar)
        for (a, b), i, ar in zip(pairs, inh, d["analysis_result_id"])]

    n = len(d)
    buckets = (d.groupby("bucket")
                 .agg(series=("SeriesInstanceUID", "size"),
                      distinct_pairs=("ManufacturerModelName", "nunique"))
                 .reset_index())
    buckets["pct"] = (100 * buckets["series"] / n).round(2)
    buckets["label"] = buckets["bucket"].map(BUCKET_LABEL)
    buckets["order"] = buckets["bucket"].map(lambda b: BUCKET_ORDER.index(b))
    buckets = buckets.sort_values("order").drop(columns="order").reset_index(drop=True)

    conv = (d.groupby("convention")
              .agg(series=("SeriesInstanceUID", "size"),
                   analysis_results=("analysis_result_id", "nunique"),
                   example_manufacturer=("Manufacturer", lambda s: str(s.iloc[0])),
                   example_model=("ManufacturerModelName", lambda s: str(s.iloc[0])))
              .reset_index())
    conv["pct"] = (100 * conv["series"] / n).round(2)
    conv = conv.sort_values("series", ascending=False).reset_index(drop=True)
    return d, buckets, conv


def clustering(per_series: pd.DataFrame,
               flag: str = "encoder_only") -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Report the rate with the collection as the unit of analysis, and what
    happens when the largest contributors are removed.

    Series within a collection are not independent observations. They are
    produced by one pipeline, in one run, under one set of choices, so a
    series-weighted rate over the whole archive is a statement about which
    producer contributed the most objects at least as much as it is a statement
    about the archive. The effective sample size is closer to the number of
    collections than to the number of series.

    Three things are reported together and none of them alone:
    the series-weighted rate, the distribution of the rate across collections,
    and the leave-one-out sensitivity.
    """
    d = per_series.copy()
    d["_flag"] = d["bucket"] == flag

    by_coll = (d.groupby("collection_id")
                 .agg(series=("SeriesInstanceUID", "size"),
                      flagged=("_flag", "sum"),
                      analysis_results=("analysis_result_id", "nunique"))
                 .reset_index())
    by_coll["pct"] = (100 * by_coll["flagged"] / by_coll["series"]).round(2)
    by_coll = by_coll.sort_values("series", ascending=False).reset_index(drop=True)

    total_s = int(by_coll["series"].sum())
    total_f = int(by_coll["flagged"].sum())

    def loo(frame: pd.DataFrame, key: str) -> pd.DataFrame:
        rows = []
        for r in frame.itertuples():
            s, f = total_s - int(r.series), total_f - int(r.flagged)
            rows.append({key: getattr(r, key), "series_removed": int(r.series),
                         "series_remaining": s,
                         "pct_after_removal": round(100 * f / s, 2) if s else 0.0,
                         "shift_from_full": round(100 * f / s - 100 * total_f / total_s, 2)
                         if s else 0.0})
        return pd.DataFrame(rows)

    loo_coll = loo(by_coll.head(12), "collection_id")

    d["_ar"] = d["analysis_result_id"].fillna("(null)")
    by_ar = (d.groupby("_ar")
               .agg(series=("SeriesInstanceUID", "size"), flagged=("_flag", "sum"))
               .reset_index().rename(columns={"_ar": "analysis_result_id"})
               .sort_values("series", ascending=False).reset_index(drop=True))
    loo_ar = loo(by_ar.head(8), "analysis_result_id")

    q = by_coll["pct"].quantile([0.25, 0.5, 0.75])
    stats = {
        "flag": flag,
        "series": total_s,
        "collections": int(len(by_coll)),
        "analysis_results": int(d["analysis_result_id"].nunique()),
        "patients": int(d["PatientID"].nunique()),
        "series_weighted_pct": round(100 * total_f / total_s, 1),
        "collection_median_pct": round(float(q[0.5]), 1),
        "collection_iqr_low": round(float(q[0.25]), 1),
        "collection_iqr_high": round(float(q[0.75]), 1),
        "collections_at_zero": int((by_coll["pct"] == 0).sum()),
        "collections_at_hundred": int((by_coll["pct"] == 100).sum()),
        "largest_collection": str(by_coll["collection_id"].iloc[0]),
        "largest_collection_series": int(by_coll["series"].iloc[0]),
        "largest_collection_share": round(100 * int(by_coll["series"].iloc[0]) / total_s, 1),
        "pct_without_largest_collection": float(loo_coll["pct_after_removal"].iloc[0]),
        "largest_analysis_result": str(by_ar["analysis_result_id"].iloc[0]),
        "pct_without_largest_analysis_result": float(loo_ar["pct_after_removal"].iloc[0]),
    }
    return by_coll, pd.concat([loo_coll.assign(unit="collection"),
                               loo_ar.assign(unit="analysis_result")],
                              ignore_index=True), stats


def acquisition_inheritance(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Does a derived object declare the identity of the scanner that acquired
    the images it was computed from.

    Measured rather than guessed. An identity is called inherited when the exact
    (Manufacturer, ManufacturerModelName) pair also appears on an acquired image
    series, which is any series whose SOP class is neither derived nor adjacent.
    Two strengths are reported: the pair occurs on an acquired series in the same
    collection, which is the strong form, and the pair occurs on an acquired
    series anywhere in the archive, which is the weak form.

    This needs no vendor list, so it cannot be biased by which vendor names the
    author happened to think of.

    A series is eligible for the test only when both attributes are present.
    Matching on absence would count a series whose identity is missing as having
    inherited a missing identity, which is not the same statement. Without that
    guard the 40 Key Object Selection series, which carry neither attribute,
    score as 100 percent inherited against acquired series that also carry
    neither.
    """
    produced = set(DERIVED_SOP_CLASSES) | set(ADJACENT_SOP_CLASSES)
    acquired = df[~df["sop_class_name"].isin(produced)]
    a_mfr = acquired["Manufacturer"].fillna("").astype(str).str.strip()
    a_mod = acquired["ManufacturerModelName"].fillna("").astype(str).str.strip()
    a_ok = (a_mfr != "") & (a_mod != "")
    global_pairs = set(zip(a_mfr[a_ok], a_mod[a_ok]))
    local_pairs = set(zip(acquired["collection_id"][a_ok], a_mfr[a_ok], a_mod[a_ok]))

    d = derived(df).copy()
    dm = d["Manufacturer"].fillna("").astype(str).str.strip()
    dd = d["ManufacturerModelName"].fillna("").astype(str).str.strip()
    d["identity_eligible"] = (dm != "") & (dd != "")
    d["inherited_same_collection"] = [
        ok and t in local_pairs
        for ok, t in zip(d["identity_eligible"], zip(d["collection_id"], dm, dd))]
    d["inherited_anywhere"] = [
        ok and t in global_pairs
        for ok, t in zip(d["identity_eligible"], zip(dm, dd))]

    by_sop = (d.groupby("sop_class_name")
                .agg(series=("SeriesInstanceUID", "size"),
                     eligible=("identity_eligible", "sum"),
                     inherited_same_collection=("inherited_same_collection", "sum"),
                     inherited_anywhere=("inherited_anywhere", "sum"))
                .reset_index())
    elig = by_sop["eligible"].astype("float64").replace(0.0, float("nan"))
    by_sop["pct_of_eligible_same_collection"] = (
        100 * by_sop["inherited_same_collection"] / elig).fillna(0.0).round(2)
    by_sop["pct_of_eligible_anywhere"] = (
        100 * by_sop["inherited_anywhere"] / elig).fillna(0.0).round(2)
    return d, by_sop.sort_values("series", ascending=False)


_TOKEN_STOP = {
    "annotations", "annotation", "seg", "segmentations", "segmentation", "dicom",
    "ct", "mri", "mr", "pet", "us", "maps", "map", "tumor", "nodules", "targets",
    "expert", "zones", "hires", "clinical", "sr", "prediction", "mutation", "1b",
    "biopsy", "converted", "by", "imaging", "data", "commons", "the", "of", "and",
}


def name_agreement(frame: pd.DataFrame) -> pd.DataFrame:
    """Does the declared identity contain any distinctive token from the
    analysis result IDC attributes the series to.

    This is a string overlap test, not a judgement. A miss means the declared
    equipment strings share no distinctive token with the attributed analysis.
    It does not by itself mean the declaration is wrong.
    """
    d = frame.copy()
    d["_ar"] = d["analysis_result_id"].fillna("(null)")
    rows = []
    for ar, sub in d.groupby("_ar"):
        tokens = {t for t in re.split(r"[^a-z0-9]+", ar.lower())
                  if len(t) > 2 and t not in _TOKEN_STOP}
        declared = (sub["Manufacturer"].fillna("") + " " +
                    sub["ManufacturerModelName"].fillna("")).str.lower()
        if tokens:
            hit = declared.apply(lambda s: any(t in s for t in tokens))
        else:
            hit = pd.Series(False, index=sub.index)
        mfr = list(sub["Manufacturer"].fillna("(null)").value_counts().items())[:2]
        mod = list(sub["ManufacturerModelName"].fillna("(null)").value_counts().items())[:2]
        rows.append({
            "analysis_result_id": ar,
            "series": int(len(sub)),
            "distinctive_tokens": " ".join(sorted(tokens)) or "(none)",
            "series_with_token_match": int(hit.sum()),
            "pct_match": round(100 * hit.sum() / len(sub), 2),
            "top_Manufacturer": "; ".join("%s [%s]" % (k, _fmt(v)) for k, v in mfr),
            "top_ManufacturerModelName": "; ".join("%s [%s]" % (k, _fmt(v)) for k, v in mod),
            "sop_classes": " | ".join(sorted(set(sub["sop_class_name"]))),
        })
    return pd.DataFrame(rows).sort_values("series", ascending=False)


def write_markdown(idc_version: str, t: dict, out: Path) -> Path:
    d = t["derived"]
    n = len(d)
    cat = t["category_counts"]

    def cat_pct(col: str, category: str) -> float:
        sub = cat[(cat["attribute"] == col) & (cat["category"] == category)]
        return float(sub["pct_of_derived"].sum())

    sv = t["spelling_variants"]
    dcmqi = sv[sv["rule"] == "dcmqi"]
    na = t["name_agreement"]
    na_big = na[(na["series"] >= 100) & (na["analysis_result_id"] != "(null)")]
    no_match = na_big[na_big["pct_match"] == 0]
    inh = t["inheritance_by_sop"]
    inh_n = int(t["inherited_frame"]["inherited_same_collection"].sum())
    inh_any = int(t["inherited_frame"]["inherited_anywhere"].sum())
    inh_elig = int(t["inherited_frame"]["identity_eligible"].sum())
    pop_sop = t["population_by_sop"]

    buckets = t["buckets"]
    conv = t["conventions"]
    converter_pairs = t["converter_pairs"]
    cl = t["cluster_stats"]
    loo = t["leave_one_out"]

    def bucket_series(key: str) -> int:
        return int(buckets.loc[buckets["bucket"] == key, "series"].iloc[0])

    def bucket_pct(key: str) -> float:
        return float(buckets.loc[buckets["bucket"] == key, "pct"].iloc[0])

    headline = (
        "**%.2f percent of derived series declare a general purpose DICOM "
        "encoding library and nothing else.** The library can encode any "
        "analysis, so it identifies none. But %.2f percent name the producing "
        "entity, the producing model and the converter together, which is the "
        "case that makes the finding a conflict of conventions rather than an "
        "absence."
        % (bucket_pct("encoder_only"), bucket_pct("producer_and_converter")))
    spelling_note = (
        "A consumer grouping derived objects by declared model name gets %d "
        "groups where there is one tool."
        % (int(dcmqi["distinct_spellings"].iloc[0]) if len(dcmqi) else 0))
    nomatch_note = (
        "%s series across %d analysis results of at least 100 series share no "
        "distinctive token between the analysis IDC attributes them to and the "
        "equipment identity they declare. The unattributed group, where "
        "analysis_result_id is itself null, is excluded from that tally."
        % (_fmt(int(no_match["series"].sum())), len(no_match)))
    inherit_note = (
        "%s of the %s derived series carry both attributes and are eligible for "
        "the test. Of those, %s, %.1f percent, declare an identity that also "
        "appears on an acquired image series in the same collection. Widening "
        "the test to the whole archive gives %s, %.1f percent. Against the full "
        "derived population rather than the eligible subset the figures are "
        "%.1f and %.1f percent."
        % (_fmt(inh_elig), _fmt(n), _fmt(inh_n), 100 * inh_n / inh_elig,
           _fmt(inh_any), 100 * inh_any / inh_elig,
           100 * inh_n / n, 100 * inh_any / n))
    mfr_pop = pop_sop[pop_sop["attribute"] == "Manufacturer"]
    mod_pop = pop_sop[pop_sop["attribute"] == "ManufacturerModelName"]
    dcmqi = sv[sv["rule"] == "dcmqi"]

    text = f"""# Claim 3: producer identification in IDC {idc_version} derived objects

Population: **{_fmt(n)} derived series**, the nine SOP classes defined in
`colophon/index.py`. Zero bytes downloaded. Reproduce with `{CMD}`.

## What this settles and what it does not

The claim names five provenance carriers. Two are index columns and are settled
here across the entire population. Three are not in the index and require the
objects themselves, so they are logged as pending rather than dropped.

| carrier | tag | in index | status |
|---|---|---|---|
| Manufacturer | (0008,0070) | yes | measured, whole population |
| ManufacturerModelName | (0008,1090) | yes | measured, whole population |
| ImplementationVersionName | (0002,0013) | no | pending, needs file meta, Phase 2 and 3 |
| ContributingEquipmentSequence | (0018,A001) | no | pending, needs dataset read, Phase 2 and 3 |
| SegmentAlgorithmType | (0062,0008) | no | pending, SEG only, Phase 2 and 3 |
| SegmentAlgorithmName | (0062,0009) | no | pending, SEG only, Phase 2 and 3 |
| ContentCreatorName | (0070,0084) | no | pending, Phase 2 and 3 |
| AlgorithmIdentificationSequence | Algorithm Identification Macro | no | pending, Phase 2 and 3 |
| SR TID 4019 algorithm identification | template | no | pending, SR only, Phase 2 and 3 |

The last five are not in the brief's list of five carriers. They are added
because the published IDC AI-annotation dataset descriptors record producer
information in them, so scoring only the brief's five would report an absence
that the objects may not have. The primary measure stays the four named
equipment attributes. A secondary measure, attribution present anywhere, runs
over the alternative locations, and both numbers go in the manuscript.

IHE Radiology Technical Framework Supplement, AI Results, section 6.5.3.1
requires AI algorithm identification in ContributingEquipmentSequence, with the
Algorithm Identification Macro as the alternative. That is a published,
versioned, citable requirement, and it is the yardstick this claim is measured
against. Without it the claim is a generic complaint about metadata
completeness.

## Population rates

Both attributes are populated on almost every derived series, so the finding is
not absence. It is what the populated values name.

By SOP class, Manufacturer:

{_md_table(mfr_pop, ["sop_class_name", "series", "null", "empty", "populated", "pct_populated", "distinct_values"])}

By SOP class, ManufacturerModelName:

{_md_table(mod_pop, ["sop_class_name", "series", "null", "empty", "populated", "pct_populated", "distinct_values"])}

No derived series in the archive carries a zero length string in either
attribute. Where a value is missing it is absent from the index entirely, which
is a different failure mode from the zero length value that spine-gsps found
draws a worse validator diagnostic than absence.

## What the populated values name

Four buckets, exhaustive and mutually exclusive, summing to the population. The
rules are in `colophon/provenance.py` as plain substrings over the lowercased
value, so any single assignment can be checked by eye. The buckets describe what
kind of entity a declared pair names. They do not say whether naming it is
correct.

Exhaustiveness is the point. Reporting an encoder share against a named-model
share leaves a residual, and the residual here contains the counter-example that
changes the finding.

{_md_table(buckets, ["label", "series", "pct", "distinct_pairs"])}

{headline}

## The counter-example, and why it changes the claim

The second bucket is a positive control. {_fmt(int(bucket_series('producer_and_converter')))} series
declare the producing entity, the producing model and the converter, all three,
in the equipment attributes:

{_md_table(converter_pairs, ["Manufacturer", "ManufacturerModelName", "series"])}

IDC already has a working convention for the thing an absence-based reading of
this data would call missing, and applies it to {bucket_pct('producer_and_converter'):.1f}
percent of its own holdings. So the defensible claim is not that the archive
fails to record producers. It is that several incompatible conventions coexist
in one archive curated by one team, and a consumer cannot tell from the
attributes which convention a given object follows.

Even inside the positive control the convention is not applied consistently: one
analysis result writes "Converted By" and the other writes "converted by".

## The unit of analysis, stated before any rate is read

**Series in this archive are not independent observations.** They are produced
by one pipeline, in one run, under one set of choices, so a series-weighted rate
is a statement about which producer contributed the most objects at least as
much as it is a statement about the archive.

| | |
|---|---|
| derived series | {_fmt(cl['series'])} |
| collections | {cl['collections']} |
| analysis results | {cl['analysis_results']} |
| patients | {_fmt(cl['patients'])} |
| largest collection, `{cl['largest_collection']}` | {_fmt(cl['largest_collection_series'])} series, {cl['largest_collection_share']} percent of the census |

The effective sample size is on the order of the {cl['collections']} collections,
not the {_fmt(cl['series'])} series. Every rate in this study is therefore
reported three ways and never one.

**Series-weighted**, over the whole population: {cl['series_weighted_pct']} percent.

**Collection-level**, the collection as the unit: median
{cl['collection_median_pct']} percent, IQR {cl['collection_iqr_low']} to
{cl['collection_iqr_high']}. The distribution is not centred, it is bimodal:
{cl['collections_at_zero']} collections sit at 0 percent and
{cl['collections_at_hundred']} sit at 100 percent. A convention is adopted by a
producer and applied to everything that producer emits, so the object is the
wrong unit for asking how common a convention is.

**Leave-one-out sensitivity**:

{_md_table(loo[loo.unit == "collection"].head(6), ["collection_id", "series_removed", "series_remaining", "pct_after_removal", "shift_from_full"])}

{_md_table(loo[loo.unit == "analysis_result"].head(4), ["analysis_result_id", "series_removed", "series_remaining", "pct_after_removal", "shift_from_full"])}

Removing the single collection `{cl['largest_collection']}` moves the rate from
{cl['series_weighted_pct']} percent to
{cl['pct_without_largest_collection']} percent. Removing the single analysis
result `{cl['largest_analysis_result']}` moves it to
{cl['pct_without_largest_analysis_result']} percent.

**So the series-weighted figure is substantially one analysis result.** It is
reported because it describes the archive as it exists, which is what a consumer
downloads, and it is never reported without the collection-level distribution
and the sensitivity beside it. Percentages are given without decimal places
where no interval justifies the precision.

This is a census of one release of one archive. It licenses no inference beyond
IDC v24, and no claim in this study is stated about DICOM practice in general.

## The competing conventions

{_md_table(conv, ["convention", "series", "pct", "analysis_results", "example_manufacturer", "example_model"])}

The scanner case is not identified from a list of vendor names. It is the
measured cross-reference described below, so the archive identifies it rather
than the author.

## One tool, several spellings

The declared encoder strings are not stable. Counting distinct spellings of the
same tool, over series that declare an encoder, a conversion or an application:

{_md_table(sv, ["rule", "category", "distinct_spellings", "series"])}

The largest case in full:

{('    ' + dcmqi["spellings"].iloc[0].replace(" || ", chr(10) + "    ")) if len(dcmqi) else "    none"}

{spelling_note}

## Identity inherited from the acquisition

An identity is called inherited when the exact Manufacturer and
ManufacturerModelName pair also appears on an acquired image series, meaning a
series whose SOP class is neither derived nor adjacent. This is measured against
the archive itself, so it needs no list of vendor names and cannot be biased by
which vendors the author thought to include.

A series is eligible only when both attributes are present, because matching on
absence would count a missing identity as an inherited one.

{_md_table(inh, ["sop_class_name", "series", "eligible", "inherited_same_collection", "pct_of_eligible_same_collection", "inherited_anywhere", "pct_of_eligible_anywhere"])}

{inherit_note}

For those series the equipment identity describes the scanner that produced the
images the result was computed from, not anything that produced the result.

## Declared identity against attributed analysis

`analysis_result_id` is IDC's own record of which analysis a series came from.
Testing whether the declared equipment strings share any distinctive token with
that identifier, for analysis results of at least 100 series:

{_md_table(na_big, ["analysis_result_id", "series", "pct_match", "top_Manufacturer", "top_ManufacturerModelName"])}

{nomatch_note}

## The interpretation this measurement does not make

PS3.3 C.7.5.1 defines Manufacturer as the manufacturer of the equipment that
produced the composite instances, and ManufacturerModelName as that equipment's
model name. Conversion software is defensibly the equipment that produced a
converted instance, so declaring the encoder is a defensible reading of the
attribute. The attribute the standard provides for recording equipment that
contributed to an instance without being the creating equipment is
ContributingEquipmentSequence (0018,A001), and that attribute is not in the
index.

So this phase establishes the rates and the ambiguity. Whether the analysis that
computed a result is recorded anywhere in these objects is a question about
ContributingEquipmentSequence and the algorithm identification macros, and it is
answered by reading the objects, in Phase 2 and Phase 3. This module does not
resolve it and does not score any object as non-conformant.

## A confounder that has to be carried into Phases 2 and 3

TCIA and IDC apply PS3.15 Annex E de-identification profiles on ingest, and
attribute retention varies by profile and by submitting site. An absent
Manufacturer can mean the producer never wrote one, or that curation removed it.
The index cannot separate those two, because it carries neither
DeidentificationMethod (0012,0063) nor DeidentificationMethodCodeSequence
(0012,0064). Both are recorded per object once files are fetched, and every
attribution rate from Phase 2 onward is stratified by whether a retention
profile was declared. The Phase 0 rates above are therefore upper bounds on
absence attributable to producers.

The population rates here are high enough that this confounder does not touch
the headline: the finding is not that the attributes are missing, it is what the
present values name.

## What was dropped

Nothing. All {_fmt(n)} derived series were classified. Values matching no rule
are reported in the `unclassified` category rather than discarded, and every
distinct value with its count is in `results/phase0/provenance_values.csv`.
"""
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--print-only", action="store_true")
    args = ap.parse_args(argv)

    idc_version, df = load_index()
    d = derived(df)
    n = len(d)
    print("IDC %s, derived series: %s" % (idc_version, _fmt(n)))

    pop_sop = pd.concat([
        population(d, "Manufacturer", ["sop_class_name"]),
        population(d, "ManufacturerModelName", ["sop_class_name"]),
    ], ignore_index=True)
    ar = d.copy()
    ar["analysis_result_id"] = ar["analysis_result_id"].fillna("(null)")
    pop_ar = pd.concat([
        population(ar, "Manufacturer", ["analysis_result_id"]),
        population(ar, "ManufacturerModelName", ["analysis_result_id"]),
    ], ignore_index=True)

    values = pd.concat([value_distribution(d, "Manufacturer"),
                        value_distribution(d, "ManufacturerModelName")],
                       ignore_index=True)
    tagged = categorise(d)
    cat_rows = []
    for col, prefix in (("Manufacturer", "mfr"), ("ManufacturerModelName", "model")):
        g = (tagged.groupby("%s_category" % prefix)
                   .agg(series=("SeriesInstanceUID", "size"),
                        distinct_values=(col, "nunique"))
                   .reset_index()
                   .rename(columns={"%s_category" % prefix: "category"}))
        g["attribute"] = col
        g["pct_of_derived"] = (100 * g["series"] / n).round(3)
        cat_rows.append(g.sort_values("series", ascending=False))
    cat = pd.concat(cat_rows, ignore_index=True)

    sv = spelling_variants(d)
    na = name_agreement(d)
    inh_frame, inh_by_sop = acquisition_inheritance(df)
    conv_frame, buckets, conv = conventions(
        d, inherited=inh_frame["inherited_same_collection"])
    by_coll, loo, cluster_stats = clustering(conv_frame)
    cp = conv_frame[conv_frame["bucket"] == "producer_and_converter"]
    converter_pairs = (cp.groupby(["Manufacturer", "ManufacturerModelName"])
                         .size().rename("series").reset_index()
                         .sort_values("series", ascending=False))

    tables = {
        "provenance_population_by_sop": pop_sop,
        "provenance_population_by_analysis_result": pop_ar,
        "provenance_values": values,
        "provenance_categories": cat,
        "provenance_spelling_variants": sv,
        "provenance_name_agreement": na,
        "provenance_acquisition_inheritance": inh_by_sop,
        "provenance_buckets": buckets,
        "provenance_conventions": conv,
        "provenance_converter_pairs": converter_pairs,
        "provenance_by_collection": by_coll,
        "provenance_leave_one_out": loo,
    }
    t = dict(tables, derived=d, category_counts=cat, spelling_variants=sv,
             name_agreement=na, population_by_sop=pop_sop,
             inheritance_by_sop=inh_by_sop, inherited_frame=inh_frame,
             buckets=buckets, conventions=conv, converter_pairs=converter_pairs,
             cluster_stats=cluster_stats, leave_one_out=loo)

    if args.print_only:
        for name, frame in tables.items():
            print("\n==== %s ====" % name)
            print(frame.head(40).to_string(index=False))
        return 0

    PHASE0.mkdir(parents=True, exist_ok=True)
    for name, frame in tables.items():
        frame.to_csv(PHASE0 / ("%s.csv" % name), index=False)
    md = write_markdown(idc_version, t, RESULTS / "claim3_provenance.md")
    print("wrote %s and %d tables" % (md, len(tables)))

    def pct(attr: str, category: str) -> float:
        s = cat[(cat["attribute"] == attr) & (cat["category"] == category)]
        return float(s["pct_of_derived"].sum())

    def cnt(attr: str, category: str) -> int:
        s = cat[(cat["attribute"] == attr) & (cat["category"] == category)]
        return int(s["series"].sum())

    def bucket_n(key: str) -> int:
        return int(buckets.loc[buckets["bucket"] == key, "series"].iloc[0])

    def bucket_p(key: str) -> float:
        return float(buckets.loc[buckets["bucket"] == key, "pct"].iloc[0])

    named = na[na["analysis_result_id"] != "(null)"].sort_values(
        "series", ascending=False)
    largest_ar = str(named["analysis_result_id"].iloc[0])
    largest_n = int(named["series"].iloc[0])

    dcmqi = sv[sv["rule"] == "dcmqi"]
    na_big = na[(na["series"] >= 100) & (na["analysis_result_id"] != "(null)")]
    no_match = na_big[na_big["pct_match"] == 0]
    inh_n = int(inh_frame["inherited_same_collection"].sum())
    inh_elig = int(inh_frame["identity_eligible"].sum())
    src = "results/claim3_provenance.md and results/phase0/provenance_*.csv"

    S = dict(section="C3", section_title="Claim 3, producer identification",
             command=CMD, sop_class="derived, nine classes",
             denominator=_fmt(n), dropped="nothing, all derived series classified",
             validator="none, index metadata only",
             validator_version="idc-index-data %s" % idc_version,
             floor="not applicable, no validator involved. This claim is scored "
                   "against IHE AI Results section 6.5.3.1, not against a "
                   "validator, so it has a normative yardstick rather than a "
                   "floor.")

    ledger.record_many([
        dict(id="C3-01", claim="Manufacturer and ManufacturerModelName are "
             "populated on essentially every derived series in IDC v24, so the "
             "provenance question is not one of missing attributes.",
             status="MEASURED",
             value="Manufacturer populated on %s of %s series, "
                   "ManufacturerModelName on %s of %s"
                   % (_fmt(int(pop_sop[pop_sop.attribute == "Manufacturer"]["populated"].sum())),
                      _fmt(n),
                      _fmt(int(pop_sop[pop_sop.attribute == "ManufacturerModelName"]["populated"].sum())),
                      _fmt(n)),
             n=_fmt(int(pop_sop[pop_sop.attribute == "Manufacturer"]["populated"].sum())),
             source_file="results/phase0/provenance_population_by_sop.csv",
             pinned_by_test="tests/test_phase0.py::test_provenance_population",
             notes="Nulls and empty strings counted separately. No derived "
                   "series carries a zero length value in either attribute.", **S),
        dict(id="C3-02", claim="Declared equipment identity across the derived "
             "population partitions exhaustively into four buckets: encoding "
             "library only, producing entity and converter both named, other, "
             "and absent.",
             status="MEASURED",
             value="; ".join("%s %s (%.2f percent)"
                             % (r.label, _fmt(int(r.series)), r.pct)
                             for r in buckets.itertuples()),
             n=_fmt(int(buckets["series"].sum())),
             source_file="results/phase0/provenance_buckets.csv",
             external_source="PS3.3 C.7.5.1 General Equipment Module",
             pinned_by_test="tests/test_phase0.py::test_buckets_are_exhaustive",
             status_note="Exhaustive by construction. An encoder share reported "
             "against a named-model share leaves a residual, and the residual "
             "holds the counter-example in C3-03.",
             notes="PS3.3 C.7.5.1 permits identifying converting equipment, so "
                   "this is a measurement of what is declared, not a defect "
                   "finding. One boundary case is recorded in "
                   "colophon.provenance.BOUNDARY_CASES: Plastimatch on one "
                   "series is counted as other rather than encoder, which "
                   "changes no figure to its stated precision.", **S),
        dict(id="C3-03", claim="IDC already applies a convention that names the "
             "producing lab, the producing model and the converter together, to "
             "part of its own holdings. The finding is therefore a conflict of "
             "conventions, not an absence of producer information.",
             status="MEASURED",
             value="%s of %s series, %.2f percent, name producer and converter "
                   "both: tcga_sbu_til_maps 21,030 and tcga_gbm360 691"
                   % (_fmt(bucket_n("producer_and_converter")), _fmt(n),
                      bucket_p("producer_and_converter")),
             n=_fmt(bucket_n("producer_and_converter")),
             source_file="results/phase0/provenance_converter_pairs.csv",
             derived_from="C3-02",
             pinned_by_test="tests/test_phase0.py::test_positive_control",
             status_note="Positive control. It is what makes the claim "
             "falsifiable and fair: the archive demonstrates the capability it "
             "is being measured against.",
             notes="The convention is not applied consistently even within this "
                   "bucket: one analysis result writes 'Converted By' and the "
                   "other writes 'converted by'.", **S),
        dict(id="C3-11", claim="The largest single analysis result in the "
             "archive declares an encoding library in both equipment attributes "
             "and names the algorithm that produced it nowhere in them.",
             status="MEASURED",
             value="%s: %s series, Manufacturer QIICR, ManufacturerModelName "
                   "https://github.com/QIICR/dcmqi"
                   % (largest_ar, _fmt(largest_n)),
             n=_fmt(largest_n),
             source_file="results/phase0/provenance_name_agreement.csv",
             derived_from="C3-02,C3-05",
             pinned_by_test="tests/test_phase0.py::test_largest_analysis_result",
             status_note="Reported as an aggregate by analysis_result_id, which "
             "is what the study reports by. This is not a quality judgement and "
             "not a leaderboard: the same convention covers most of the archive "
             "and the point is that conventions differ, not that one producer "
             "is worse.", **S),
        dict(id="C3-10", claim="Several incompatible conventions for declaring "
             "equipment identity coexist in one archive curated by one team.",
             status="MEASURED",
             value="; ".join("%s %s (%.2f percent)"
                             % (r.convention, _fmt(int(r.series)), r.pct)
                             for r in conv.head(6).itertuples()),
             n=str(len(conv)),
             source_file="results/phase0/provenance_conventions.csv",
             derived_from="C3-02,C3-03,C3-07",
             status_note="The acquisition equipment convention is identified by "
             "the measured cross-reference in C3-07, not by a list of vendor "
             "names, so it cannot be biased by which vendors the author thought "
             "to include.",
             notes="This is the claim that replaces 'the archive does not record "
                   "producers'. It is harder to attack and it hands the reader a "
                   "fix rather than a complaint.", **S),
        dict(id="C3-04", claim="A single encoding tool is declared under several "
             "distinct spellings, so grouping derived objects by declared model "
             "name overcounts distinct producers.",
             status="MEASURED",
             value=("dcmqi appears under %d distinct spellings across %s series"
                    % (int(dcmqi["distinct_spellings"].iloc[0]),
                       _fmt(int(dcmqi["series"].iloc[0])))) if len(dcmqi) else "no encoder rows",
             n=_fmt(int(dcmqi["series"].iloc[0])) if len(dcmqi) else "0",
             source_file="results/phase0/provenance_spelling_variants.csv",
             pinned_by_test="tests/test_phase0.py::test_dcmqi_spellings", **S),
        dict(id="C3-05", claim="For most large analysis results the declared "
             "equipment strings share no distinctive token with the analysis "
             "that IDC attributes the series to.",
             status="MEASURED",
             value="%s series across %d analysis results of at least 100 series "
                   "have zero token overlap"
                   % (_fmt(int(no_match["series"].sum())), len(no_match)),
             n=_fmt(int(no_match["series"].sum())),
             source_file="results/phase0/provenance_name_agreement.csv",
             status_note="String overlap test, not a judgement. A miss means no "
             "shared distinctive token, not that the declaration is wrong.",
             dropped="analysis results under 100 series, and the null "
                     "analysis_result_id group, excluded from this tally and "
                     "reported in the full table", **{k: v for k, v in S.items()
                                                      if k != "dropped"}),
        dict(id="C3-06", claim="ImplementationVersionName (0002,0013), "
             "ContributingEquipmentSequence (0018,A001), SegmentAlgorithmType "
             "(0062,0008), SegmentAlgorithmName (0062,0009), ContentCreatorName "
             "(0070,0084) and the Algorithm Identification Macro cannot be "
             "measured from the index.",
             status="PENDING",
             value="7 of 9 provenance carriers unmeasured at Phase 0",
             source_file=src,
             external_source="PS3.3, Enhanced General Equipment Module and the "
                             "Algorithm Identification Macro",
             notes="These are not index columns. They require reading fetched "
                   "objects, which is Phase 2 for the small classes and Phase 3 "
                   "for the sampled ones. Logged so the claim is not silently "
                   "narrowed to the two carriers the index happens to expose. "
                   "The carrier list is wider than the brief's five because the "
                   "published IDC AI-annotation descriptors record producer "
                   "information in the SEG algorithm attributes.", **S),
        dict(id="C3-07", claim="A measurable share of derived series declare an "
             "equipment identity that also appears on acquired image series in "
             "the same collection, meaning the identity describes the scanner "
             "rather than the producer.",
             status="MEASURED",
             value="%s of %s eligible series, %.1f percent, inherited within "
                   "collection. Widening the match to the whole archive gives "
                   "%s, %.1f percent. Against all %s derived series the two "
                   "figures are %.1f and %.1f percent."
                   % (_fmt(inh_n), _fmt(inh_elig), 100 * inh_n / inh_elig,
                      _fmt(int(inh_frame["inherited_anywhere"].sum())),
                      100 * int(inh_frame["inherited_anywhere"].sum()) / inh_elig,
                      _fmt(n), 100 * inh_n / n,
                      100 * int(inh_frame["inherited_anywhere"].sum()) / n),
             n=_fmt(inh_n),
             source_file="results/phase0/provenance_acquisition_inheritance.csv",
             status_note="Measured against the archive itself by exact pair "
             "match, so it needs no vendor name list and cannot be biased by "
             "which vendors the author thought to include.", **S),
        dict(id="C3-08", claim="Claim 3 at Phase 0 samples nothing.",
             status="MEASURED",
             value="%s of %s derived series classified" % (_fmt(n), _fmt(n)),
             n=_fmt(n), source_file=src,
             notes="Values matching no rule are reported as unclassified rather "
                   "than discarded.", **S),
        dict(id="C3-12", claim="Series in this archive are not independent "
             "observations. The effective sample size is on the order of the "
             "number of collections, not the number of series, so every rate is "
             "reported series-weighted, collection-level and leave-one-out.",
             status="MEASURED",
             value="%s series across %d collections, %d analysis results and %s "
                   "patients. Series-weighted encoder rate %s percent; "
                   "collection-level median %s percent, IQR %s to %s; %d "
                   "collections at 0 percent and %d at 100 percent"
                   % (_fmt(cluster_stats["series"]), cluster_stats["collections"],
                      cluster_stats["analysis_results"], _fmt(cluster_stats["patients"]),
                      cluster_stats["series_weighted_pct"],
                      cluster_stats["collection_median_pct"],
                      cluster_stats["collection_iqr_low"],
                      cluster_stats["collection_iqr_high"],
                      cluster_stats["collections_at_zero"],
                      cluster_stats["collections_at_hundred"]),
             n=str(cluster_stats["collections"]),
             source_file="results/phase0/provenance_by_collection.csv",
             derived_from="C3-02",
             pinned_by_test="tests/test_phase0.py::test_clustering",
             status_note="Stated before any rate is read, not in limitations. "
             "The collection-level distribution is bimodal rather than centred, "
             "which is itself the finding: a convention is adopted by a producer "
             "and applied to everything that producer emits, so the object is "
             "the wrong unit for asking how common a convention is.",
             notes="This is a census of one release of one archive. It licenses "
                   "no inference beyond IDC v24 and no claim here is stated "
                   "about DICOM practice in general.", **S),
        dict(id="C3-13", claim="The series-weighted encoder rate is "
             "substantially attributable to a single collection and a single "
             "analysis result.",
             status="MEASURED",
             value="removing collection %s takes the rate from %s to %s percent; "
                   "removing analysis result %s takes it to %s percent"
                   % (cluster_stats["largest_collection"],
                      cluster_stats["series_weighted_pct"],
                      cluster_stats["pct_without_largest_collection"],
                      cluster_stats["largest_analysis_result"],
                      cluster_stats["pct_without_largest_analysis_result"]),
             n=_fmt(cluster_stats["largest_collection_series"]),
             source_file="results/phase0/provenance_leave_one_out.csv",
             derived_from="C3-12",
             pinned_by_test="tests/test_phase0.py::test_leave_one_out",
             status_note="Reported alongside the series-weighted figure and "
             "never after it. The series-weighted figure still describes the "
             "archive a consumer actually downloads, which is why it is kept.",
             **S),
        dict(id="C3-14", claim="The normative yardstick for claim 3 is PS3.3 "
             "Final Text, not the IHE AI Results profile.",
             status="PENDING",
             value="Enhanced General Equipment is Mandatory in the Segmentation "
                   "and Parametric Map IODs, making Manufacturer (0008,0070), "
                   "ManufacturerModelName (0008,1090), DeviceSerialNumber "
                   "(0018,1000) and SoftwareVersions (0018,1020) all Type 1: "
                   "four hard machine-checkable attributes",
             external_source="PS3.3, Enhanced General Equipment Module, and the "
                             "Segmentation and Parametric Map IOD module tables",
             supersedes="C3-06-air",
             status_note="Reversal. AIR is Trial Implementation, with no "
             "Connectathon test case and no Gazelle test plan, so it cannot "
             "carry a conformance claim. It is cited as evidence of intent and "
             "of a knowingly left gap, not as a requirement. Held PENDING until "
             "the module tables are read directly rather than taken from a "
             "secondary statement.",
             notes="Consequence for reporting: results are given in three "
                   "grades, never two. Non-conformant, conformant but "
                   "uninformative, and informative. Scoped to Segmentation and "
                   "Parametric Map, the two IODs where Enhanced General "
                   "Equipment is Mandatory. Everything the standard "
                   "leaves optional, ContributingEquipmentSequence being Type 3 "
                   "and Comprehensive 3D SR carrying only General Equipment so "
                   "that Manufacturer is Type 2 and model, serial and software "
                   "are Type 3, is a gap in the standard rather than vendor "
                   "non-conformance.", **S),
        dict(id="C3-06-air", claim="The IHE AI Results profile section 6.5.3.1 "
             "is the normative yardstick against which producer identification "
             "is scored.",
             status="RETIRED",
             value="withdrawn before any object was scored against it",
             retired_reason="AIR is Trial Implementation and has been for "
             "years, with no Connectathon test case and no Gazelle test plan. A "
             "profile at that status cannot carry a conformance claim. Scoring "
             "against it would also have measured a gap the standard itself "
             "leaves open rather than a failure by any producer. Replaced by "
             "C3-14, which scores against PS3.3 Final Text Type 1 requirements.",
             superseded_by="C3-14",
             notes="AIR is still cited, as evidence of intent and of a "
                   "knowingly left gap. Its Closed Issue 26 rates "
                   "ContributingEquipmentSequence as a good start, and Closed "
                   "Issue 19 declines to encode approval status and defers to "
                   "out-of-band mechanisms. Both quotes are pending retrieval "
                   "of the PDF.", **S),
        dict(id="C3-15", claim="Scoring is semantic, not presence-based, and "
             "absent, empty and non-empty are three separate counts.",
             status="MEASURED",
             value="a presence check over Type 1 attributes reports 100 percent "
                   "and measures nothing; sentinel values are published in "
                   "results/sentinels.json and excluded from every "
                   "informativeness numerator",
             derived_from="W-04,C3-14",
             source_file="results/sentinels.json",
             pinned_by_test="tests/test_phase0.py::test_provenance_population",
             status_note="Populated is defined as non-null and of length "
             "greater than zero after trimming. Manufacturer is Type 2 and may "
             "legally be zero length, and index representations collapse zero "
             "length to empty or null inconsistently, so the index null "
             "semantics are verified against opened objects in Phase 2.",
             notes="highdicom writes ContributingEquipmentSequence on every "
                   "object it produces, so a presence check on that attribute "
                   "over-reports for every highdicom object too.", **S),
        dict(id="C3-02-prev", claim="The majority of derived series declare a "
             "general purpose DICOM encoding library in ManufacturerModelName "
             "rather than the analysis that produced the result, 86.7 percent, "
             "and only 1.8 percent name a specific model, pipeline or study.",
             status="RETIRED",
             value="86.7 percent encoder against 1.8 percent named analysis",
             superseded_by="C3-02",
             retired_reason="Not false, but not exhaustive, and the omission "
             "changed the argument. Two non-complementary shares leave 11.5 "
             "percent of the population unreported, and that residual contains "
             "the 21,721 series that name producing entity, producing model and "
             "converter together. Reported this way the finding reads as 'the "
             "archive does not record producers', which the residual falsifies. "
             "Replaced by an exhaustive four-bucket partition, C3-02, and the "
             "positive control, C3-03.",
             notes="Never entered a manuscript. Kept because the 86.7 and 1.8 "
                   "figures were written into the README before the residual "
                   "was examined, and a number that reached prose once can "
                   "reach it again.", **S),
        dict(id="C3-09", claim="De-identification is a confounder on any "
             "absence-based provenance rate and cannot be resolved from the "
             "index.",
             status="PENDING",
             value="DeidentificationMethod (0012,0063) and "
                   "DeidentificationMethodCodeSequence (0012,0064) not in index",
             source_file=src,
             external_source="PS3.15 Annex E",
             notes="TCIA and IDC apply PS3.15 Annex E profiles on ingest and "
                   "retention varies by profile and submitter. An absent "
                   "Manufacturer may mean the producer never wrote one or that "
                   "curation removed it. Phase 2 and 3 record both attributes "
                   "per object and stratify every attribution rate by whether a "
                   "retention profile was declared.", **S),
    ])
    print("ledger: %s" % ledger.summary())
    return 0


if __name__ == "__main__":
    sys.exit(main())
