"""Pin Table 1: writers, sentinels, carriers and the measured cost of unstable
declared names.
"""
from __future__ import annotations

import json

import pytest

from colophon import index, writers
from colophon.paths import RESULTS

IDC_VERSION = "v24"


@pytest.fixture(scope="module")
def idc():
    version, df = index.load_index()
    if version != IDC_VERSION:
        pytest.fail("index is %s, the ledger records %s" % (version, IDC_VERSION))
    return df


def test_writer_census(idc):
    """Ledger W-01. PRE-02 cannot be applied without this."""
    d = index.derived(idc)
    _, census, _ = writers.writer_census(d)
    assert int(census["series"].sum()) == len(d), "census must partition"
    by_writer = {r.writer: int(r.series) for r in census.itertuples()}
    assert by_writer["dcmqi"] == 411_865
    assert by_writer["highdicom"] == 2_097
    assert by_writer[writers.UNKNOWN_WRITER] == 47_826
    # The unknown share is an input to Phase 2, so it is pinned rather than
    # allowed to drift silently.
    assert round(100 * by_writer[writers.UNKNOWN_WRITER] / len(d), 1) == 9.9


def test_carrier_hierarchy(idc):
    """Ledger W-02. Identity is recoverable, at level 3, with a version."""
    d = index.derived(idc)
    h = writers.carrier_hierarchy(d)
    ts = h[h.analysis_result_id == "totalsegmentator_ct_segmentations"].iloc[0]
    assert int(ts["series"]) == 378_153
    assert ts["first_informative_level"] == 3, (
        "level 1 must not be informative for this analysis result, and level 3 "
        "must be: that gap is the finding")
    assert bool(ts["version_in_free_text"]) is True
    assert ts["version_example"] == "v1.5.6"


def test_carrier_level_four_is_not_in_the_object():
    """Identity available only from the registry is identity a downloaded file
    does not carry, so the distinction has to survive in the data."""
    levels = {c["level"]: c for c in writers.CARRIER_LEVELS}
    assert levels[1]["in_object"] is True
    assert levels[3]["in_object"] is True
    assert levels[4]["in_object"] is False
    assert levels[2]["in_index"] is False, "level 2 is Phase 2 work"


def test_cohort_recall(idc):
    """Ledger W-03. The measured harm of unstable spellings."""
    d = index.derived(idc)
    r = writers.cohort_recall(d, "dcmqi")
    assert r["true_total"] == 411_865
    assert r["distinct_spellings"] == 6
    assert r["exact_match_recall_n"] == 380_712
    assert r["missed_by_exact_match"] == 31_153
    assert r["exact_match_recall_pct"] == 92.44
    assert r["distinct_after_normalisation"] == 2
    # The finding only survives because the missed count is material. If this
    # ever drops to the low hundreds the claim should be withdrawn, not weakened.
    assert r["missed_by_exact_match"] > 1_000


def test_sentinels_published(idc):
    """Ledger W-04. The list is an artefact a reader can disagree with."""
    path = RESULTS / "sentinels.json"
    assert path.exists(), "run python -m colophon.writers"
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert doc["sentinels"], "empty sentinel list"
    for s in doc["sentinels"]:
        for field in ("value", "attribute", "toolkit", "basis", "status"):
            assert s.get(field, "").strip(), "%s missing %s" % (s.get("value"), field)
    # Every sentinel must actually occur in the archive, or it is a guess.
    # Checked against derived plus adjacent classes: com.pixelmed.convert
    # .EncapsulateData sits on Encapsulated STL, which is produced-not-acquired
    # but outside the headline denominator.
    d = index.derived(idc, include_adjacent=True)
    present = set(d["Manufacturer"].dropna()) | set(d["ManufacturerModelName"].dropna())
    present_lower = {str(v).strip().lower() for v in present}
    unseen = [s["value"] for s in doc["sentinels"]
              if s["value"].strip().lower() not in present_lower]
    assert not unseen, "sentinels that never occur in the archive: %s" % unseen


def test_sentinels_are_excluded_from_informativeness(idc):
    """A sentinel counted as producer identity is the whole error this list
    exists to prevent."""
    assert writers.is_sentinel("QIICR")
    assert writers.is_sentinel("https://github.com/QIICR/dcmqi")
    assert not writers.is_sentinel("TotalSegmentator")
    assert not writers.is_sentinel("GBM360")
    assert not writers.is_sentinel(None)


def test_writer_rules_are_ordered_and_total(idc):
    """Every series gets exactly one writer label, including unknown."""
    d = index.derived(idc)
    tagged, census, _ = writers.writer_census(d)
    assert tagged["writer"].isna().sum() == 0
    assert set(census["writer"]) <= (
        {name for name, _ in writers.WRITER_RULES} | {writers.UNKNOWN_WRITER})
