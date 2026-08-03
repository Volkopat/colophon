"""Pin the Phase 0 numbers that ledger rows quote.

These run against the local idc-index dataframe, so they need `idc-index`
installed but no network and no validator binaries. Each test names the ledger
row it protects. If IDC issues a new index release these fail loudly, which is
the point: a count taken from a live store drifts, and the ledger says v24.
"""
from __future__ import annotations

import pytest

from colophon import index, provenance

IDC_VERSION = "v24"


@pytest.fixture(scope="module")
def idc():
    version, df = index.load_index()
    if version != IDC_VERSION:
        pytest.fail(
            "index is %s, the ledger records %s. Re-measure and restamp every "
            "row before changing this constant." % (version, IDC_VERSION))
    return df


def test_index_shape(idc):
    """Ledger P0-01."""
    assert len(idc) == 1_032_911
    assert len(idc) == idc["SeriesInstanceUID"].nunique(), "not one row per series"
    assert idc.shape[1] == 31


def test_derived_totals(idc):
    """Ledger P0-02. The headline denominator."""
    d = index.derived(idc)
    assert len(d) == 481_750
    assert int(d["instanceCount"].sum()) == 504_727


def test_derived_definition_is_the_only_one_that_matches(idc):
    """The nine-class set was recovered, not assumed. Dropping any one of the
    nine, or adding any one adjacent class, breaks both totals."""
    for name in index.DERIVED_SOP_CLASSES:
        subset = {k: v for k, v in index.DERIVED_SOP_CLASSES.items() if k != name}
        n = len(idc[idc["sop_class_name"].isin(subset)])
        assert n != 481_750, "dropping %s still gives the headline total" % name
    for name in index.ADJACENT_SOP_CLASSES:
        wider = set(index.DERIVED_SOP_CLASSES) | {name}
        n = len(idc[idc["sop_class_name"].isin(wider)])
        assert n != 481_750, "adding %s still gives the headline total" % name


def test_gsps_split(idc):
    """Ledger P0-05. Settles by count a question documentation does not."""
    g = idc[idc["sop_class_name"] == "Grayscale Softcopy Presentation State Storage"]
    assert len(g) == 1_086
    by_collection = g.groupby("collection_id").size().to_dict()
    assert by_collection == {"qiba_ct_1c": 462, "rider_lung_ct": 384,
                             "rider_pilot": 240}
    null_ar = g[g["analysis_result_id"].isna()]
    assert len(null_ar) == 462
    assert set(null_ar["collection_id"]) == {"qiba_ct_1c"}


def test_parametric_map(idc):
    """Ledger P0-06."""
    p = idc[idc["sop_class_name"] == "Parametric Map Storage"]
    assert len(p) == 691
    assert set(p["collection_id"]) == {"tcga_gbm"}
    assert set(p["analysis_result_id"]) == {"tcga_gbm360"}
    assert set(p["license_short_name"]) == {"CC BY 4.0"}


def test_every_derived_series_is_creative_commons(idc):
    """Ledger P0-07. What makes an exhaustive small-class census legal."""
    d = index.derived(idc)
    assert all(str(v).startswith("CC BY") for v in set(d["license_short_name"]))


def test_transfer_syntax_exceptions(idc):
    """Ledger P0-04. A decode failure must never be scored as non-conformance,
    so the classes that are not Explicit VR Little Endian are pinned."""
    ts = index.transfer_syntax(idc)
    odd = ts[(ts["transfer_syntax_name"] != "Explicit VR Little Endian")
             & (ts["class"] == "derived")]
    got = {(r.sop_class_name, r.transfer_syntax_name): int(r.series)
           for r in odd.itertuples()}
    assert got == {
        ("Segmentation Storage", "JPEG-LS Lossless"): 97,
        ("RT Structure Set Storage", "Implicit VR Little Endian"): 3_174,
    }


def test_provenance_population(idc):
    """Ledger C3-01. The finding is not absence."""
    d = index.derived(idc)
    for column in ("Manufacturer", "ManufacturerModelName"):
        pop = provenance.population(d, column, ["sop_class_name"])
        assert int(pop["empty"].sum()) == 0, (
            "%s: a zero length value would be a different failure mode from "
            "absence and the write-up says there are none" % column)
    mfr = provenance.population(d, "Manufacturer", ["sop_class_name"])
    assert int(mfr["populated"].sum()) == 481_331
    model = provenance.population(d, "ManufacturerModelName", ["sop_class_name"])
    assert int(model["populated"].sum()) == 475_812


def test_dcmqi_spellings(idc):
    """Ledger C3-04. One tool, several declared spellings."""
    d = index.derived(idc)
    sv = provenance.spelling_variants(d)
    row = sv[sv["rule"] == "dcmqi"].iloc[0]
    assert int(row["distinct_spellings"]) == 6
    assert int(row["series"]) == 411_865


def test_inheritance_requires_both_attributes_present(idc):
    """Ledger C3-07. Matching on absence scored Key Object Selection as 100
    percent inherited, which is the bug this guards."""
    frame, by_sop = provenance.acquisition_inheritance(idc)
    kos = by_sop[by_sop["sop_class_name"] == "Key Object Selection Document Storage"]
    assert int(kos["eligible"].iloc[0]) == 0
    assert int(kos["inherited_anywhere"].iloc[0]) == 0
    assert int(frame["inherited_same_collection"].sum()) == 9_971
    assert int(frame["inherited_anywhere"].sum()) == 10_491


def test_buckets_are_exhaustive(idc):
    """Ledger C3-02. The buckets have to partition the population, because a
    residual is where a counter-example hides. Reporting an encoder share
    against a named-model share left 11.5 percent unaccounted for, and the
    positive control was inside it."""
    d = index.derived(idc)
    per, buckets, _ = provenance.conventions(d)
    assert int(buckets["series"].sum()) == len(d)
    assert set(buckets["bucket"]) == set(provenance.BUCKET_ORDER)
    assert per["bucket"].isna().sum() == 0
    got = {r.bucket: int(r.series) for r in buckets.itertuples()}
    assert got == {
        "encoder_only": 416_427,
        "producer_and_converter": 21_721,
        "other": 37_454,
        "absent": 6_148,
    }


def test_positive_control(idc):
    """Ledger C3-03. The archive already demonstrates the convention that an
    absence-based reading would call missing."""
    d = index.derived(idc)
    per, _, _ = provenance.conventions(d)
    pc = per[per["bucket"] == "producer_and_converter"]
    assert len(pc) == 21_721
    assert set(pc["analysis_result_id"]) == {"tcga_sbu_til_maps", "tcga_gbm360"}
    # Producing entity, producing model and converter, all three present.
    for _, row in pc.groupby("ManufacturerModelName").head(1).iterrows():
        joined = "%s %s" % (row["Manufacturer"], row["ManufacturerModelName"])
        assert "convert" in joined.lower()
    # And the convention is not applied consistently even here.
    forms = set()
    for text in set(pc["Manufacturer"]) | set(pc["ManufacturerModelName"]):
        for form in ("Converted By", "converted by"):
            if form in str(text):
                forms.add(form)
    assert forms == {"Converted By", "converted by"}, (
        "the casing inconsistency inside the positive control is a reported "
        "finding and has changed")


def test_two_denominators(idc):
    """Ledger P0-10. Neither denominator is the AI-derived population."""
    d = index.derived(idc)
    attributed = index.analysis_attributed(idc)
    assert len(d) == 481_750
    assert len(attributed) == 463_543
    unattributed = d[d["analysis_result_id"].isna()]
    assert len(unattributed) == 18_207
    rt = unattributed[unattributed["sop_class_name"] == "RT Structure Set Storage"]
    assert len(rt) == 3_115
    # The attributed set contains human work, so it is an upper bound only.
    assert "lung_pet_ct_dx_annotations" in set(attributed["analysis_result_id"])


def test_first_file_coverage(idc):
    """Ledger P0-11. Quoted precisely because overstating a small gap costs
    more than the point is worth."""
    ffc = index.first_file_coverage(idc)
    missed = int(ffc["instances_missed"].sum())
    assert missed == 22_977
    total = int(ffc["instances"].sum())
    assert round(100 * missed / total, 2) == 4.55
    assert round(total / int(ffc["series"].sum()), 4) == 1.0477
    multi = ffc[ffc["multi_instance_series"] > 0]
    assert list(multi["sop_class_name"]) == ["Segmentation Storage"], (
        "Segmentation is stated to be the only multi-instance derived class")
    assert int(multi["multi_instance_series"].iloc[0]) == 6_170


def test_largest_analysis_result(idc):
    """Ledger C3-11. The headline example of the encoding-library convention."""
    d = index.derived(idc)
    na = provenance.name_agreement(d)
    named = na[na["analysis_result_id"] != "(null)"].sort_values(
        "series", ascending=False)
    top = named.iloc[0]
    assert top["analysis_result_id"] == "totalsegmentator_ct_segmentations"
    assert int(top["series"]) == 378_153
    assert float(top["pct_match"]) == 0.0
    sub = d[d["analysis_result_id"] == "totalsegmentator_ct_segmentations"]
    assert set(sub["Manufacturer"]) == {"QIICR"}
    assert set(sub["ManufacturerModelName"]) == {"https://github.com/QIICR/dcmqi"}
    joined = " ".join(set(sub["Manufacturer"]) | set(sub["ManufacturerModelName"]))
    assert "totalsegmentator" not in joined.lower()


def test_classification_covers_the_population(idc):
    """No value is silently dropped. Unclassified is a reported category, not a
    hole, and it stays small enough that the headline is not hiding in it."""
    d = index.derived(idc)
    tagged = provenance.categorise(d)
    assert len(tagged) == len(d)
    for prefix in ("mfr", "model"):
        counts = tagged["%s_category" % prefix].value_counts()
        assert counts.sum() == len(d)
        unclassified = int(counts.get("unclassified", 0))
        assert unclassified / len(d) < 0.05, (
            "%s unclassified share is %.1f percent, too large to leave "
            "uninspected" % (prefix, 100 * unclassified / len(d)))


def test_clustering(idc):
    """Ledger C3-12. The unit of analysis, stated before any rate is read."""
    d = index.derived(idc)
    per, _, _ = provenance.conventions(d)
    by_coll, loo, stats = provenance.clustering(per)
    assert stats["collections"] == 85
    assert stats["analysis_results"] == 24
    assert int(by_coll["series"].sum()) == len(d)
    # Bimodal, not centred. If this ever becomes unimodal the framing changes.
    assert stats["collection_median_pct"] == 0.0
    assert stats["collections_at_zero"] == 44
    assert stats["collections_at_hundred"] == 27
    assert stats["collections_at_zero"] + stats["collections_at_hundred"] > (
        0.7 * stats["collections"]), "the bimodality is the finding"


def test_leave_one_out(idc):
    """Ledger C3-13. The series-weighted rate is largely one contributor."""
    d = index.derived(idc)
    per, _, _ = provenance.conventions(d)
    _, loo, stats = provenance.clustering(per)
    assert stats["largest_collection"] == "nlst"
    assert stats["largest_collection_share"] == 80.2
    assert stats["series_weighted_pct"] == 86.4
    assert stats["pct_without_largest_collection"] == 34.81
    assert stats["largest_analysis_result"] == "totalsegmentator_ct_segmentations"
    assert stats["pct_without_largest_analysis_result"] == 36.95
    # A shift this large is exactly why the series-weighted figure is never
    # reported on its own.
    assert abs(stats["series_weighted_pct"]
               - stats["pct_without_largest_collection"]) > 40
