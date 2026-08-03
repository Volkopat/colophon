"""Pin the PRE-06 Segmentation Storage sampling frame.

The frame is a proposal and the tests are the part of it that cannot drift: the
fence that stops a draw, the budget it promises to stay inside, the rule that
every stratum has one, and the seed.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from colophon import index, sample
from colophon.paths import RESULTS

IDC_VERSION = "v24"


@pytest.fixture(scope="module")
def idc():
    version, df = index.load_index()
    if version != IDC_VERSION:
        pytest.fail("index is %s, the ledger records %s" % (version, IDC_VERSION))
    return df


@pytest.fixture(scope="module")
def plan(idc):
    return sample.build(idc)


# --- the fence ----------------------------------------------------------------
# PRE-06 was approved on 2026-08-02 and the fence was lifted, so the three tests
# that asserted `EXECUTE is False` no longer describe the project. They are not
# deleted, because the mechanism they pinned still has to work: what changed is
# the state, not the guard. Each is rewritten to exercise the guard directly with
# EXECUTE forced down, which is a stronger test than the original, since the
# original passed for as long as nobody had approved anything.


def test_execute_was_lifted_deliberately_and_says_so_in_source():
    """The fence was only ever meant to come down by editing source.

    Approving PRE-06 means setting EXECUTE in `colophon/sample.py`, not passing
    a flag, so the source has to carry the record of the decision. This replaces
    the earlier assertion that EXECUTE is False, which stopped describing the
    project when the row was approved.
    """
    assert sample.EXECUTE is True
    source = Path(sample.__file__).read_text(encoding="utf-8")
    assert "EXECUTE = True" in source
    assert "PRE-06" in source
    assert "Lifted" in source, (
        "lifting the fence must leave a dated reason in source next to it")


def test_execute_guard_blocks_a_draw(monkeypatch):
    """Ledger E-07, still pinned, and the name is kept because E-07 names it.

    The guard fires before the function touches its arguments, so passing
    nonsense raises ExecutionBlocked rather than TypeError. What changed when
    PRE-06 was approved is the module-level state, not the guard, so the fence
    is forced down here and the same three entry points are exercised.
    """
    monkeypatch.setattr(sample, "EXECUTE", False)
    with pytest.raises(sample.ExecutionBlocked):
        sample.draw(None, None)
    with pytest.raises(sample.ExecutionBlocked):
        sample.fetch_manifest()
    with pytest.raises(sample.ExecutionBlocked):
        sample._require_execute("anything at all")


def test_the_guard_names_what_it_blocks_and_how_to_lift_it(monkeypatch):
    """A guard whose message does not say why is a guard someone deletes."""
    monkeypatch.setattr(sample, "EXECUTE", False)
    with pytest.raises(sample.ExecutionBlocked) as exc:
        sample.draw(None, None)
    message = str(exc.value)
    assert "PRE-06" in message
    assert "EXECUTE" in message


def test_sample_still_does_not_fetch_anything_itself():
    """The frame draws and the fetching lives elsewhere. Ledger E-07 drew the
    boundary while the fence was up and the boundary did not move when it came
    down: `colophon.phase3` fetches, `colophon.sample` does not."""
    assert not hasattr(sample, "fetch"), (
        "colophon.sample must not import a fetcher: fetching is phase3's job")
    # It names s5cmd in a docstring and must still not be able to run one.
    assert not hasattr(sample, "subprocess")
    with pytest.raises(NotImplementedError):
        sample.fetch_manifest()


def test_execution_did_not_move_the_frame():
    """Approval buys the draw and nothing else. Every registered constant is
    asserted here so that a change to any of them fails rather than quietly
    redefining what was pre-registered."""
    assert sample.SEED == 20260802
    assert sample.REGISTERED_N == 384
    assert sample.MIN_RATE_N == 30
    assert sample.BUDGET_GB == 150.0
    assert sample.TARGET_P == 0.05
    assert sample.HEADROOM_SIGMA == 3.0
    assert sample.WRITERS_WITH_FLOOR == ("dcmqi", "highdicom")


# --- the seed -----------------------------------------------------------------
def test_the_seed_is_one_fixed_integer():
    assert isinstance(sample.SEED, int)
    assert sample.SEED == 20260802, (
        "the seed is registered in results/pre06_sampling_frame.md and in "
        "ledger row PRE-06. Changing it invalidates the published frame.")


def test_the_seed_is_the_only_source_of_randomness():
    """Every draw goes through one seed and one derivation. A second seed, or a
    call to the global numpy generator, would make the draw unreproducible."""
    source = (sample.__file__.replace("\\", "/"))
    text = open(source, encoding="utf-8").read()
    assert "np.random.seed" not in text, "global numpy seeding is not reproducible"
    assert text.count("np.random.default_rng(") == 1, (
        "exactly one generator construction, seeded from SEED")
    assert "np.random.default_rng([seed, child])" in text


# --- the strata ---------------------------------------------------------------
def test_strata_partition(plan, idc):
    """Ledger E-01. The strata are exhaustive and disjoint over the class."""
    frame, seg = plan["strata"], plan["segmentation"]
    assert len(seg) == 190_146
    assert int(frame["series"].sum()) == len(seg)
    assert frame["stratum"].is_unique
    assert len(frame) == 21
    # Stratified by writing toolkit and analysis_result_id, and by nothing else.
    for row in frame.itertuples():
        assert row.stratum == "%s / %s" % (row.writer, row.analysis_result)


def test_the_cost_spread_is_what_rules_out_proportional_allocation(plan):
    """Ledger E-01, and the reason for the allocation in E-05."""
    frame = plan["strata"]
    ratio = float(frame["mean_MB"].max()) / float(frame["mean_MB"].min())
    assert ratio > 1000, (
        "if the cost per series ever becomes uniform, the cost-capped "
        "allocation stops being justified and proportional should be revisited")
    alt = plan["alternatives"]
    assert alt["proportional_strata_below_min_rate_n"] > len(frame) / 2, (
        "proportional allocation is rejected because it starves most strata")


# --- the registered minimum ---------------------------------------------------
def test_registered_n_properties():
    """Ledger E-02. n = 384 is carried from PRE-05, and what it buys is
    computed rather than asserted."""
    assert sample.REGISTERED_N == 384
    p = sample.registered_n_properties()
    assert round(p["half_width_pts_at_threshold"], 2) == 2.21, (
        "PRE-05 justifies n = 384 by this half-width. If it moves, PRE-05 has "
        "to be reopened rather than this test updated.")
    assert p["half_width_pts_worst_case"] < 5.0
    assert p["wilson_minimum_worst_case"] <= sample.REGISTERED_N
    assert sample.REGISTERED_N <= p["wald_worst_case"]


def test_wilson_is_the_interval_it_claims_to_be():
    lo, hi, half = sample.wilson(0, 384)
    assert lo == 0.0
    assert 0 < hi < 0.01, "zero failures must not give a zero-width interval"
    lo, hi, _ = sample.wilson(19.2, 384)
    assert lo < 0.05 < hi


def test_the_reporting_thresholds_are_the_registered_ones():
    assert sample.MIN_RATE_N == 30
    assert sample.TARGET_P == 0.05, "the PRE-05 null threshold"


# --- the allocation -----------------------------------------------------------
def test_every_stratum_has_a_rule(plan):
    """Ledger E-05. No stratum is left without an allocation and a reporting
    rule, and none is silently dropped."""
    frame, alloc = plan["strata"], plan["allocation"]
    assert len(alloc) == len(frame)
    assert set(alloc["stratum"]) == set(frame["stratum"])
    for row in alloc.itertuples():
        assert row.allocation_rule.strip(), "%s has no allocation rule" % row.stratum
        assert row.reporting_rule.strip(), "%s has no reporting rule" % row.stratum
        assert 1 <= row.n <= row.series
        if row.series <= sample.REGISTERED_N:
            assert row.n == row.series, "small strata are taken whole"
        else:
            assert row.n >= sample.MIN_RATE_N
            assert row.n <= sample.REGISTERED_N


def test_the_reporting_rule_matches_the_allocation(plan):
    """Under 30 reports counts only. Between 30 and 383 carries the flag."""
    for row in plan["allocation"].itertuples():
        if row.n < sample.MIN_RATE_N:
            assert row.reporting_rule == "counts only, no rate"
        elif row.n < sample.REGISTERED_N:
            assert "below-registered-n flag" in row.reporting_rule
        else:
            assert row.reporting_rule == "rate with Wilson interval"


def test_budget_holds(plan):
    """Ledger PRE-06. The whole point of the allocation is this number."""
    alloc = plan["allocation"]
    expected_gb = alloc.attrs["expected_MB_total"] / 1024
    upper_gb = alloc.attrs["upper_MB_total"] / 1024
    assert expected_gb < 150.0, "expected fetch is %.2f GB" % expected_gb
    assert upper_gb < 150.0, (
        "the %.0f sigma upper bound on the realised byte total is %.2f GB, over "
        "the 150 GB cap" % (sample.HEADROOM_SIGMA, upper_gb))
    assert upper_gb <= sample.PLANNING_BUDGET_GB + 1e-6, (
        "the plan is built against the reserved budget, not the raw cap")
    # And the arithmetic actually adds up.
    assert abs(float(alloc["expected_GB"].sum()) - expected_gb) < 1e-6
    assert int(alloc["n"].sum()) == 5_941


def test_the_budget_is_binding(plan):
    """A budget that nothing pushes against is not a budget, and the honest
    consequence of it is a stratum below the registered minimum."""
    alloc = plan["allocation"]
    cut = alloc[(alloc["n"] < sample.REGISTERED_N)
                & (alloc["series"] > sample.REGISTERED_N)]
    assert len(cut) == 1, (
        "the frame reports exactly one stratum whose precision the budget cost, "
        "and it is named in ledger row E-05")
    assert plan["alternatives"]["registered_everywhere_GB"] > 150.0


# --- clustering ---------------------------------------------------------------
def test_planning_icc(plan):
    """Ledger E-03. The planning rho is measured, and the provenance flag is
    not what it is measured on."""
    rho = plan["rho"]
    assert 0.0 < rho < 1.0
    assert round(rho, 3) == 0.919
    table = plan["icc"]
    assert int(table["rho"].notna().sum()) == 15
    assert set(table["proxy"]) <= {"%s empty" % c
                                   for c in sample.ICC_PROXY_COLUMNS}


def test_the_provenance_flag_is_degenerate_within_stratum(plan):
    """Ledger E-03. This is why C3-12's rho cannot be reused for sizing: the
    strata are built from the same attributes the flag is built from."""
    from colophon.provenance import bucket_of
    seg = plan["segmentation"]
    for stratum, sub in seg.groupby("stratum"):
        flags = {bucket_of(a, b) == "encoder_only"
                 for a, b in zip(sub["Manufacturer"],
                                 sub["ManufacturerModelName"])}
        assert len(flags) == 1, (
            "%s has within-stratum variation in the C3-12 flag, so the claim "
            "in E-03 no longer holds" % stratum)


def test_clustering_dominates(plan):
    """Ledger E-06. The effective sample size is bounded by the collections."""
    prec, frame = plan["precision"], plan["strata"]
    singletons = frame[frame["collections"] == 1]
    assert len(singletons) == 12
    worst = prec[prec["collections_in_stratum"] == 1]
    assert (worst["n_effective"] < 2).all(), (
        "a single-collection stratum cannot have an effective sample size "
        "above about 1 / rho, whatever n is")
    assert (prec["half_width_pts_clustered"]
            >= prec["half_width_pts_design_based"]).all(), (
        "the clustered interval is the wider of the two and is the one quoted")


def test_the_design_based_width_carries_the_finite_population_correction(plan):
    """A stratum taken whole has no sampling error for the finite population
    target, and the table has to say so rather than quoting a binomial width."""
    prec = plan["precision"]
    whole = prec[prec["n"] == prec["series"]]
    assert len(whole) == 7
    assert (whole["half_width_pts_design_based"] == 0.0).all()


def test_design_effect_and_icc_agree_on_a_known_case():
    """The two formulas are the load-bearing ones in the proposal, so they are
    checked against a case with a hand-computable answer."""
    # Four clusters of five, perfectly separated: rho is 1.
    y = [0] * 5 + [0] * 5 + [1] * 5 + [1] * 5
    cluster = ["a"] * 5 + ["b"] * 5 + ["c"] * 5 + ["d"] * 5
    rho, m0, c = sample.icc_anova(y, cluster)
    assert c == 4
    assert round(m0, 6) == 5.0
    assert round(rho, 6) == 1.0
    # No clustering at all: rho at or below zero.
    y = [0, 1] * 10
    cluster = ["a", "a", "b", "b", "c", "c", "d", "d", "e", "e"] * 2
    rho, _, _ = sample.icc_anova(y, cluster)
    assert rho <= 0.05
    assert sample.design_effect(1.0, 0.9) == 1.0
    assert round(sample.design_effect(11.0, 0.9), 6) == 10.0


def test_expected_distinct_clusters_is_exact_at_the_edges():
    assert sample.expected_distinct_clusters([10, 10, 10], 30) == 3.0
    assert round(sample.expected_distinct_clusters([1, 1, 1, 1], 1), 6) == 1.0
    # Ten clusters of a hundred, a sample of ten: fewer than ten collections hit.
    got = sample.expected_distinct_clusters([100] * 10, 10)
    assert 6.0 < got < 10.0


# --- the floor ----------------------------------------------------------------
def test_floor_coverage(plan):
    """Ledger E-04. A post-floor rate is only defined where a floor exists."""
    alloc = plan["allocation"]
    assert set(sample.WRITERS_WITH_FLOOR) == {"dcmqi", "highdicom"}
    with_floor = int(alloc.loc[alloc["has_floor"], "series"].sum())
    without = int(alloc.loc[~alloc["has_floor"], "series"].sum())
    assert with_floor + without == int(alloc["series"].sum())
    assert without == 39_163
    for row in alloc.itertuples():
        assert row.has_floor == (row.writer in sample.WRITERS_WITH_FLOOR)


# --- the proposal artefacts ---------------------------------------------------
def test_the_proposal_is_published():
    path = RESULTS / "pre06_sampling_frame.md"
    assert path.exists(), "run python -m colophon.sample"
    text = path.read_text(encoding="utf-8")
    assert "EXECUTE" in text and "proposal" in text
    assert str(sample.SEED) in text


def test_pre06_is_proposed_without_rewording_it():
    """A pre-registration may gain an outcome. It may not be reworded, and the
    proposal may only set the fields it is allowed to set."""
    from colophon import ledger
    path = RESULTS / "pending_ledger" / "track_e.json"
    if not path.exists():
        pytest.skip("proposals already merged into the ledger")
    rows = {r["id"]: r for r in json.loads(path.read_text(encoding="utf-8"))}
    assert "PRE-06" in rows
    prior = {r["id"]: r for r in ledger.load()}["PRE-06"]
    proposed = rows["PRE-06"]
    assert proposed["claim"] == prior["claim"], "PRE-06 was reworded"
    assert proposed["status"] == "PENDING", "the frame is a proposal, not a result"
    for field, value in proposed.items():
        if field in ("id", "claim") or field in sample.PRE06_SETTABLE:
            continue
        assert value == prior.get(field, ""), (
            "%s is not a field track E may set on PRE-06, and it does not match "
            "the value already in the ledger" % field)


def test_the_proposal_merges_cleanly():
    """The merge refuses proposals that touch a pre-registration illegally, so
    running its check is the cheapest way to prove this one does not."""
    from colophon import merge_ledger
    path = RESULTS / "pending_ledger" / "track_e.json"
    if not path.exists():
        pytest.skip("proposals already merged into the ledger")
    rows = [("track_e.json", r)
            for r in json.loads(path.read_text(encoding="utf-8"))]
    assert merge_ledger.check_protected(rows) == []
    assert merge_ledger.check_retired(rows) == []


def test_new_rows_are_e_numbered():
    path = RESULTS / "pending_ledger" / "track_e.json"
    if not path.exists():
        pytest.skip("proposals already merged into the ledger")
    ids = [r["id"] for r in json.loads(path.read_text(encoding="utf-8"))]
    assert ids[0] == "PRE-06"
    assert all(i.startswith("E-") for i in ids[1:])
    assert len(set(ids)) == len(ids)
