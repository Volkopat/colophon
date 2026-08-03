"""Phase 3 sampling frame for Segmentation Storage. A proposal, not a run.

**This frame is a proposal pending approval on ledger row PRE-06. Nothing in
this module fetches, and nothing in it draws.** `EXECUTE` is False at module
level and every function that would select series or move bytes calls
`_require_execute` first, which raises. Approving the frame means closing
PRE-06 and setting `EXECUTE` deliberately in the source, not passing a flag.

Segmentation Storage is the one derived class the census could not take whole:
190,146 series and 18.58 TB, against a Phase 2 budget of under 1 GB for the six
small classes. It is a single SOP class, so the general-purpose frame the brief
sketched is unnecessary here. Stratification is by writing toolkit and
`analysis_result_id` only.

Three things drive the design and each is a measured row rather than a
preference:

**PRE-05** fixes the null threshold at a post-floor failure rate of 5 percent,
which fixes the registered minimum sample size: at n = 384 the 95 percent Wilson
half-width at p = 0.05 is 2.2 points, and 384 is the smallest n that holds it
under 2.5.

**F1-01** measured the validator floor to be writer-specific, so a post-floor
rate can only be quoted inside a stratum whose writer has a measured floor.
Stratifying by writer is what makes the subtraction well defined.

**C3-12 and C3-13** measured that series inside a collection are not independent:
removing one collection moves a rate from 86.4 to 34.81 percent. The variance
estimator therefore treats the collection as the primary sampling unit, and the
intracluster correlation is estimated from the sample rather than assumed.

Usage:
    python -m colophon.sample               print the plan, write the proposal
    python -m colophon.sample --print-only  print, write nothing
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

from .index import DERIVED_SOP_CLASSES, _fmt, _md_table, derived, load_index
from .paths import PHASE0, RESULTS
from .writers import writer_of

CMD = "python -m colophon.sample"

# --- the execution fence ------------------------------------------------------
# The frame is a design. Turning it into a draw or a fetch is a separate,
# deliberate act that follows approval of PRE-06.
#
# Lifted 2026-08-02 on approval of PRE-06. The frame above is unchanged: not one
# stratum, allocation rule, threshold or seed moved when the fence came down,
# which is the whole point of having written it while EXECUTE was False. What
# the approval buys is `draw` and `fetch_manifest`, and nothing else.
# colophon.phase3 is the only caller.
EXECUTE = True


class ExecutionBlocked(RuntimeError):
    """Raised when a draw or a fetch is attempted while EXECUTE is False."""


def _require_execute(what: str) -> None:
    if not EXECUTE:
        raise ExecutionBlocked(
            "%s is blocked. colophon.sample.EXECUTE is False. This sampling "
            "frame is a proposal pending approval on ledger row PRE-06, and no "
            "Segmentation Storage series may be drawn or fetched against it "
            "until that row is closed. Lifting the fence means editing EXECUTE "
            "in colophon/sample.py, not passing a flag." % what)


# --- fixed constants ----------------------------------------------------------
SOP_CLASS = "Segmentation Storage"

# One integer seed, used for every stratified draw in this frame and for
# nothing else. Recorded here so the draw is reproducible from the source
# rather than from a run log.
SEED = 20260802

# The registered minimum per published stratum. Carried from PRE-05 unchanged
# and not re-derived here. What it buys is computed rather than asserted: see
# `registered_n_properties`.
REGISTERED_N = 384
TARGET_P = 0.05           # the PRE-05 null threshold
WORST_CASE_P = 0.5        # the least favourable proportion
WORST_CASE_HALF_WIDTH = 0.05

# Below this, a proportion is not reported at all. Between this and
# REGISTERED_N a proportion is reported with an exact Wilson interval and a
# below-registered-n flag.
MIN_RATE_N = 30

# Hard ceiling on the fetch, in GB. The plan is required to fit with the
# sampling variability of the byte total included, not just its expectation,
# because the realised draw is a random sum of skewed series sizes.
BUDGET_GB = 150.0
HEADROOM_SIGMA = 3.0

# Held back from the planning budget. series_size_MB is the archive's own
# figure for a series, not bytes measured on disk after a fetch, and the
# difference cannot be measured before fetching. Five percent of the cap is
# reserved against it, so the plan is built against BUDGET_GB - RESERVE_GB and
# the cap itself is never the number being approached.
RESERVE_GB = 0.05 * BUDGET_GB
PLANNING_BUDGET_GB = BUDGET_GB - RESERVE_GB

Z = 1.959963984540054  # two-sided 95 percent normal quantile

# Index columns whose emptiness is an attribute-presence defect of the same
# shape as the conformance outcome. Used only to put a measured planning value
# on the intracluster correlation. They are proxies and are labelled as such.
ICC_PROXY_COLUMNS = ["BodyPartExamined", "SeriesDescription", "PatientSex",
                     "PatientAge"]

# Writers with a measured Phase 1 floor. A post-floor rate is only quotable
# inside a stratum written by one of these. F1-02 and F1-01.
WRITERS_WITH_FLOOR = ("dcmqi", "highdicom")


# --- statistics ---------------------------------------------------------------
def wilson(k: float, n: float) -> tuple[float, float, float]:
    """Wilson score interval for a binomial proportion. Returns (lo, hi, half).

    Exact in the sense that no normal approximation to the proportion itself is
    made: the interval is the set of p for which the score statistic is within
    z. It does not collapse to a point at k = 0 or k = n, which is why it is
    used here rather than Wald.
    """
    if n <= 0:
        return (float("nan"),) * 3
    p = k / n
    denom = 1.0 + Z * Z / n
    centre = (p + Z * Z / (2 * n)) / denom
    half = (Z / denom) * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n))
    return max(0.0, centre - half), min(1.0, centre + half), half


def wilson_half_width(p: float, n: float) -> float:
    return wilson(p * n, n)[2]


def smallest_n_for(p: float = WORST_CASE_P, half: float = WORST_CASE_HALF_WIDTH,
                   cap: int = 5000) -> int:
    """The smallest n whose Wilson half-width at p is at or under `half`."""
    for n in range(2, cap + 1):
        if wilson_half_width(p, n) <= half:
            return n
    raise ValueError("no n under %d reaches half-width %g at p=%g" % (cap, half, p))


def registered_n_properties(n: int = REGISTERED_N) -> dict:
    """What the registered minimum buys. Computed, not asserted.

    PRE-05 registers n and its justification, the 95 percent Wilson half-width
    at the 5 percent null threshold. That number is reproduced here rather than
    rederived, and the least favourable case is reported beside it so the
    sizing can be read without knowing which p it was set at.
    """
    return {
        "n": n,
        "half_width_pts_at_threshold": 100 * wilson_half_width(TARGET_P, n),
        "half_width_pts_worst_case": 100 * wilson_half_width(WORST_CASE_P, n),
        "wilson_minimum_worst_case": smallest_n_for(WORST_CASE_P,
                                                    WORST_CASE_HALF_WIDTH),
        "wald_worst_case": math.ceil(Z * Z * 0.25 / WORST_CASE_HALF_WIDTH ** 2),
    }


def expected_distinct_clusters(sizes, n: int) -> float:
    """Expected number of distinct collections hit by an SRS of n from a stratum.

    Exact under sampling without replacement: a collection of m_j series is
    missed with probability C(N - m_j, n) / C(N, n), computed in log space.
    """
    sizes = [int(s) for s in sizes]
    total = sum(sizes)
    if n >= total:
        return float(len(sizes))
    out = 0.0
    lg = math.lgamma
    log_den = lg(total + 1) - lg(total - n + 1)
    for m in sizes:
        rest = total - m
        if rest - n < 0:
            miss = 0.0
        else:
            miss = math.exp((lg(rest + 1) - lg(rest - n + 1)) - log_den)
        out += 1.0 - miss
    return out


def icc_anova(y, cluster) -> tuple[float, float, int]:
    """One-way random effects ICC over clusters. Returns (rho, m0, c).

    rho = (MSB - MSW) / (MSB + (m0 - 1) MSW)
    m0  = (M - sum_j m_j^2 / M) / (c - 1), the unequal cluster size adjustment.

    Returns nan for rho when the outcome has no variation, which is the honest
    answer: a degenerate outcome carries no information about clustering.
    """
    frame = pd.DataFrame({"y": np.asarray(y, dtype=float), "c": list(cluster)})
    c = frame["c"].nunique()
    m = len(frame)
    if c < 2 or frame["y"].nunique() < 2:
        return float("nan"), float("nan"), c
    grand = frame["y"].mean()
    grp = frame.groupby("c")["y"].agg(["size", "mean"])
    msb = float((grp["size"] * (grp["mean"] - grand) ** 2).sum()) / (c - 1)
    within = frame["y"] - frame.groupby("c")["y"].transform("mean")
    msw = float((within ** 2).sum()) / (m - c) if m > c else 0.0
    m0 = (m - float((grp["size"] ** 2).sum()) / m) / (c - 1)
    den = msb + (m0 - 1) * msw
    return ((msb - msw) / den if den != 0 else float("nan")), m0, c


def design_effect(m_bar: float, rho: float) -> float:
    """Kish design effect for a clustered sample of mean cluster size m_bar."""
    return 1.0 + (m_bar - 1.0) * rho


# --- the frame ----------------------------------------------------------------
def segmentation(df: pd.DataFrame) -> pd.DataFrame:
    """The Segmentation Storage population, with writer and stratum labels."""
    seg = derived(df)
    seg = seg[seg["sop_class_name"] == SOP_CLASS].copy()
    seg["writer"] = [writer_of(a, b) for a, b in
                     zip(seg["Manufacturer"], seg["ManufacturerModelName"])]
    seg["analysis_result"] = seg["analysis_result_id"].fillna("(null)")
    seg["stratum"] = seg["writer"] + " / " + seg["analysis_result"]
    return seg


def strata(seg: pd.DataFrame) -> pd.DataFrame:
    """One row per (writing toolkit, analysis_result_id) stratum."""
    rows = []
    for (writer, ar), sub in seg.groupby(["writer", "analysis_result"]):
        by_coll = sub.groupby("collection_id").size()
        size = sub["series_size_MB"]
        rows.append({
            "stratum": "%s / %s" % (writer, ar),
            "writer": writer,
            "analysis_result": ar,
            "series": int(len(sub)),
            "instances": int(sub["instanceCount"].sum()),
            "size_MB": float(size.sum()),
            "size_GB": float(size.sum()) / 1024,
            "mean_MB": float(size.mean()),
            "sd_MB": float(size.std(ddof=1)) if len(sub) > 1 else 0.0,
            "collections": int(by_coll.size),
            "largest_collection_pct": round(100 * float(by_coll.max()) / len(sub), 2),
            "patients": int(sub["PatientID"].nunique()),
            "has_floor": writer in WRITERS_WITH_FLOOR,
            "floor_measured": "yes" if writer in WRITERS_WITH_FLOOR else "no",
            "collection_sizes": sorted((int(v) for v in by_coll), reverse=True),
        })
    out = pd.DataFrame(rows).sort_values("series", ascending=False)
    return out.reset_index(drop=True)


def planning_icc(seg: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    """A measured planning value for the intracluster correlation.

    The conformance outcome cannot be observed without fetching, so its rho is
    unknown until Phase 3 runs. What can be measured now, from the index alone,
    is the collection-level clustering of attribute-presence defects, which are
    the same shape of outcome: a Type 2 attribute is empty or it is not, and a
    validator either complains or it does not.

    The provenance flag of C3-12 is deliberately not used as the proxy. Its
    within-stratum variance is exactly zero for all 21 strata, because the
    stratification is built from the same two attributes the flag is built
    from, so it measures the stratification rather than the clustering.

    Returned rho is the median across every (stratum, proxy) pair that has any
    within-stratum variation at all. It is a planning value used for sizing
    only. The reported intervals use rho estimated from the realised sample by
    `icc_anova`.
    """
    rows = []
    for (writer, ar), sub in seg.groupby(["writer", "analysis_result"]):
        if sub["collection_id"].nunique() < 2:
            continue
        for col in ICC_PROXY_COLUMNS:
            values = sub[col]
            empty = values.isna() | (values.astype(str).str.strip() == "")
            rho, m0, c = icc_anova(empty.values, sub["collection_id"].values)
            rows.append({
                "stratum": "%s / %s" % (writer, ar),
                "proxy": "%s empty" % col,
                "collections": c,
                "series": int(len(sub)),
                "rate_pct": round(100 * float(empty.mean()), 2),
                "rho": round(float(rho), 4) if rho == rho else None,
                "m0": round(float(m0), 1) if m0 == m0 else None,
            })
    table = pd.DataFrame(rows)
    observed = table["rho"].dropna().astype(float).tolist()
    return table, float(np.median(observed)) if observed else float("nan")


# --- allocation ---------------------------------------------------------------
def _cost(frame: pd.DataFrame, cap_MB: float, registered_n: int,
          min_rate_n: int) -> tuple[pd.Series, float, float]:
    """Series counts, expected MB and the sd of the realised MB, at a byte cap."""
    n = []
    for row in frame.itertuples():
        if row.series <= registered_n:
            n.append(int(row.series))
            continue
        affordable = int(cap_MB // row.mean_MB) if row.mean_MB > 0 else registered_n
        n.append(int(min(registered_n, max(min_rate_n, affordable))))
    n = pd.Series(n, index=frame.index)
    whole = frame["series"] <= registered_n
    expected = float((whole * frame["size_MB"]
                      + (~whole) * (n * frame["mean_MB"])).sum())
    var = float((((~whole) * n * (1 - n / frame["series"])
                  * frame["sd_MB"] ** 2)).sum())
    return n, expected, math.sqrt(max(var, 0.0))


def allocate(frame: pd.DataFrame, budget_gb: float = PLANNING_BUDGET_GB,
             registered_n: int = REGISTERED_N, min_rate_n: int = MIN_RATE_N,
             sigma: float = HEADROOM_SIGMA) -> pd.DataFrame:
    """Cost-capped allocation. Every stratum gets an allocation rule.

    Rule, in order:

    1. A stratum with N_h at or under the registered minimum is taken whole.
    2. Every other stratum is offered the registered minimum of 384.
    3. If that does not fit the byte budget, a single per-stratum byte cap B is
       lowered until it does. A stratum whose registered allocation costs less
       than B is unaffected, so a byte is always spent where it buys the most
       precision first, and only the expensive strata are cut.
    4. No stratum is cut below `min_rate_n`, because under that a rate is not
       reported at all and the bytes would buy nothing reportable.

    The budget is checked against the expectation plus `sigma` standard
    deviations of the realised byte total, since the draw is a random sum of
    skewed series sizes.
    """
    budget_MB = budget_gb * 1024
    lo, hi = 0.0, float(frame["mean_MB"].max()) * registered_n + 1.0

    def fits(cap):
        _, exp, sd = _cost(frame, cap, registered_n, min_rate_n)
        return exp + sigma * sd <= budget_MB

    if not fits(lo):
        raise ValueError(
            "the floor allocation of %d series per sampled stratum does not fit "
            "%.1f GB. Strata must be dropped from the frame and named."
            % (min_rate_n, budget_gb))
    if fits(hi):
        cap = hi
    else:
        for _ in range(200):
            mid = (lo + hi) / 2
            if fits(mid):
                lo = mid
            else:
                hi = mid
        cap = lo

    n, expected, sd = _cost(frame, cap, registered_n, min_rate_n)
    out = frame.copy()
    out["n"] = n.astype(int)
    out["byte_cap_MB"] = round(cap, 3)
    out["expected_MB"] = [float(r.size_MB) if r.series <= registered_n
                          else float(r.n) * r.mean_MB for r in out.itertuples()]
    out["expected_GB"] = out["expected_MB"] / 1024
    out["sampling_fraction"] = (out["n"] / out["series"]).round(6)

    rule, report = [], []
    for r in out.itertuples():
        if r.n == r.series:
            rule.append("whole stratum, N at or under the registered minimum")
        elif r.n == registered_n:
            rule.append("registered minimum, n = %d" % registered_n)
        else:
            rule.append("byte capped at %.0f MB, below the registered minimum"
                        % cap)
        if r.n < min_rate_n:
            report.append("counts only, no rate")
        elif r.n < registered_n:
            report.append("rate with Wilson interval, below-registered-n flag")
        else:
            report.append("rate with Wilson interval")
    out["allocation_rule"] = rule
    out["reporting_rule"] = report
    out.attrs["expected_MB_total"] = expected
    out.attrs["sd_MB_total"] = sd
    out.attrs["upper_MB_total"] = expected + sigma * sd
    out.attrs["byte_cap_MB"] = cap
    out.attrs["planning_budget_GB"] = budget_gb
    return out


def precision(alloc: pd.DataFrame, rho: float,
              p: float = TARGET_P) -> pd.DataFrame:
    """Per stratum, what the allocation buys, with and without clustering."""
    rows = []
    for r in alloc.itertuples():
        c_exp = expected_distinct_clusters(r.collection_sizes, int(r.n))
        m_bar = r.n / c_exp if c_exp > 0 else float(r.n)
        deff = design_effect(m_bar, rho)
        n_eff = r.n / deff if deff > 0 else float("nan")
        # The design-based width carries the finite population correction, so a
        # stratum taken whole has a width of zero: there is no sampling error
        # in a census of it. The clustered width does not carry it, because its
        # target is not the finite population.
        fpc = math.sqrt(max(0.0, 1.0 - r.n / r.series))
        rows.append({
            "stratum": r.stratum,
            "series": int(r.series),
            "n": int(r.n),
            "collections_in_stratum": int(r.collections),
            "expected_collections_sampled": round(c_exp, 2),
            "mean_series_per_sampled_collection": round(m_bar, 2),
            "design_effect": round(deff, 1),
            "n_effective": round(n_eff, 2),
            "half_width_pts_design_based": round(
                100 * fpc * wilson_half_width(p, r.n), 2),
            "half_width_pts_clustered": round(
                100 * wilson_half_width(p, max(n_eff, 1.0)), 2),
            "post_floor_quotable": bool(r.has_floor),
        })
    return pd.DataFrame(rows)


def alternatives(frame: pd.DataFrame, budget_gb: float = BUDGET_GB,
                 registered_n: int = REGISTERED_N,
                 min_rate_n: int = MIN_RATE_N) -> dict:
    """The two allocations that were rejected, costed, so the choice is visible."""
    reg_n = np.where(frame["series"] <= registered_n, frame["series"], registered_n)
    reg_MB = np.where(frame["series"] <= registered_n, frame["size_MB"],
                      reg_n * frame["mean_MB"])

    # Proportional to series, scaled to whatever the budget buys.
    total_series = int(frame["series"].sum())
    mb_per_series = float(frame["size_MB"].sum()) / total_series
    affordable = int((budget_gb * 1024) // mb_per_series)
    prop_n = np.minimum(
        frame["series"].values,
        np.floor(affordable * frame["series"].values / total_series).astype(int))
    prop_MB = prop_n * frame["mean_MB"].values
    return {
        "registered_everywhere_GB": float(reg_MB.sum()) / 1024,
        "registered_everywhere_over_budget_factor":
            round(float(reg_MB.sum()) / 1024 / budget_gb, 2),
        "registered_everywhere_worst_stratum":
            str(frame.loc[int(np.argmax(reg_MB)), "stratum"]),
        "registered_everywhere_worst_stratum_GB":
            float(np.max(reg_MB)) / 1024,
        "proportional_total_series": int(affordable),
        "proportional_GB": float(prop_MB.sum()) / 1024,
        "proportional_strata_below_min_rate_n":
            int((prop_n < min_rate_n).sum()),
        "proportional_strata_with_zero_series": int((prop_n == 0).sum()),
        "proportional_largest_share_pct":
            round(100 * float(prop_n.max()) / max(int(prop_n.sum()), 1), 1),
        "strata": int(len(frame)),
    }


# --- fenced operations --------------------------------------------------------
def draw(seg: pd.DataFrame, alloc: pd.DataFrame, seed: int = SEED) -> pd.DataFrame:
    """Select the sample. Blocked while EXECUTE is False.

    Nested by construction: each stratum is permuted once under a seed derived
    deterministically from `seed` and the stratum name, and the allocation takes
    a prefix of that permutation. Changing n_h therefore lengthens or shortens
    the same draw rather than producing a different one, and no stratum's draw
    depends on any other stratum's size.
    """
    _require_execute("a stratified draw")
    picks = []
    for r in alloc.itertuples():
        pool = (seg.loc[seg["stratum"] == r.stratum, "SeriesInstanceUID"]
                   .sort_values().to_numpy())
        child = zlib.crc32(r.stratum.encode("utf-8"))
        order = np.random.default_rng([seed, child]).permutation(len(pool))
        chosen = pool[order[:int(r.n)]]
        picks.append(pd.DataFrame({"stratum": r.stratum,
                                   "SeriesInstanceUID": chosen}))
    return pd.concat(picks, ignore_index=True)


def fetch_manifest(*args, **kwargs):
    """Turn a draw into s5cmd work. Blocked while EXECUTE is False."""
    _require_execute("a fetch manifest")
    raise NotImplementedError(
        "written after PRE-06 is approved, against colophon.fetch")


# --- output -------------------------------------------------------------------
def write_markdown(idc_version: str, t: dict, out: Path) -> Path:
    frame, alloc, prec, icc_table, alt = (
        t["strata"], t["allocation"], t["precision"], t["icc"], t["alternatives"])
    rho = t["rho"]
    n_series = int(frame["series"].sum())
    n_strata = len(frame)
    total_gb = float(frame["size_GB"].sum())
    exp_gb = alloc.attrs["expected_MB_total"] / 1024
    sd_gb = alloc.attrs["sd_MB_total"] / 1024
    up_gb = alloc.attrs["upper_MB_total"] / 1024
    cap_mb = alloc.attrs["byte_cap_MB"]
    n_total = int(alloc["n"].sum())
    whole = alloc[alloc["n"] == alloc["series"]]
    at_reg = alloc[(alloc["n"] == REGISTERED_N) & (alloc["series"] > REGISTERED_N)]
    capped = alloc[(alloc["n"] < REGISTERED_N) & (alloc["series"] > REGISTERED_N)]
    singletons = frame[frame["collections"] == 1]
    singleton_series = int(singletons["series"].sum())
    floored = alloc[alloc["has_floor"]]
    unfloored = alloc[~alloc["has_floor"]]
    rnp = registered_n_properties()

    cap_rows = "\n".join(
        "- `%s`: %s of %s series, %.2f GB of a %.2f GB stratum. Wilson "
        "half-width at p = 5 percent widens from %.2f to %.2f points."
        % (r.stratum, _fmt(int(r.n)), _fmt(int(r.series)),
           float(r.expected_GB), float(r.size_GB),
           100 * wilson_half_width(TARGET_P, REGISTERED_N),
           100 * wilson_half_width(TARGET_P, int(r.n)))
        for r in capped.itertuples()) or "- none, every stratum fits"

    icc_seen = icc_table[icc_table["rho"].notna()]

    text = f"""# PRE-06: the Segmentation Storage sampling frame

**Status: proposal. Nothing has been drawn and nothing has been fetched.**
`colophon.sample.EXECUTE` is False and every function that would select a series
or move a byte raises while it stays that way. Approving this frame means
closing ledger row PRE-06.

IDC {idc_version}, index evidence only. Reproduce with `{CMD}`.

## Why this class needs a frame at all

{SOP_CLASS} is {_fmt(n_series)} series and {total_gb / 1024:.2f} TB. The six
small classes of Phase 2 were taken whole for under 1 GB. This one cannot be,
and it is now the only one of the nine derived classes left unmeasured.

Because it is a single SOP class, the general-purpose frame the brief sketched
is unnecessary. Stratification is by **writing toolkit and
`analysis_result_id`**, and by nothing else.

Both stratifiers earn their place from a measured row rather than from taste.
Writer, because F1-01 measured the validator floor to be writer-specific, so a
post-floor rate is only defined inside a stratum of known writer. Analysis
result, because C3-13 measured that a single analysis result moves a
population rate by 49.5 points, so pooling across analysis results reports the
largest producer rather than the archive.

## The strata

{n_strata} strata, exhaustive and disjoint over the {_fmt(n_series)} series.

{_md_table(frame, ["stratum", "series", "size_GB", "mean_MB", "collections", "patients", "largest_collection_pct", "floor_measured"])}

`size_GB` is the sum of `series_size_MB` over the stratum, divided by 1024.
`mean_MB` is what one series costs to fetch, and it runs from
{frame['mean_MB'].min():.3f} MB to {frame['mean_MB'].max():,.1f} MB, a factor of
**{frame['mean_MB'].max() / frame['mean_MB'].min():,.0f}** across the frame. That
spread, and not the spread in series counts, is what makes a
series-proportional allocation the wrong instrument here.

`floor_measured` says whether Phase 1 emitted a conformant object with that
stratum's writer. Where it says no, a raw failure rate is reportable and a
post-floor rate is not.

{_fmt(len(singletons))} of the {n_strata} strata contain exactly one collection,
covering {_fmt(singleton_series)} series,
{100 * singleton_series / n_series:.1f} percent of the class. That fact governs
the variance section below and it is not a detail.

## The registered minimum

**n = {_fmt(REGISTERED_N)} per published stratum.** It is carried from ledger row
PRE-05 unchanged and is not rederived here. What it buys is computed rather than
asserted:

| | |
|---|---|
| 95 percent Wilson half-width at the PRE-05 threshold p = {TARGET_P:.2f} | {rnp['half_width_pts_at_threshold']:.2f} points |
| 95 percent Wilson half-width at the least favourable p = {WORST_CASE_P:.2f} | {rnp['half_width_pts_worst_case']:.2f} points |
| smallest n reaching {100 * WORST_CASE_HALF_WIDTH:.0f} points at p = {WORST_CASE_P:.2f}, Wilson | {rnp['wilson_minimum_worst_case']} |
| the same figure by the conventional Wald formula z^2 p(1-p) / e^2 | {rnp['wald_worst_case']} |

So {REGISTERED_N} sits between the Wilson worst case minimum of
{rnp['wilson_minimum_worst_case']} and the Wald figure of
{rnp['wald_worst_case']} that the convention rounds from, and at the threshold
the interval it buys is {rnp['half_width_pts_at_threshold']:.2f} points wide
either side.

Allocation, by stratum size N_h:

| N_h | allocation |
|---|---|
| at or under {REGISTERED_N} | the whole stratum |
| above {REGISTERED_N} | {REGISTERED_N}, or what the byte cap allows, never below {MIN_RATE_N} |

Reporting, by the number of series actually validated n_h. This is the rule, not
a suggestion, and it is applied whether the series were sampled or taken whole:

| n_h | what is reported |
|---|---|
| at or above {REGISTERED_N} | a rate with a Wilson interval |
| {MIN_RATE_N} to {REGISTERED_N - 1} | a rate with a Wilson interval and a below-registered-n flag |
| under {MIN_RATE_N} | counts only, never a rate |

## What the registered minimum would cost everywhere

Giving every stratum its registered allocation costs
**{alt['registered_everywhere_GB']:.1f} GB**, which is
{alt['registered_everywhere_over_budget_factor']:.2f} times the
{BUDGET_GB:.0f} GB budget. One stratum accounts for most of it:
`{alt['registered_everywhere_worst_stratum']}` alone would cost
{alt['registered_everywhere_worst_stratum_GB']:.1f} GB for
{_fmt(REGISTERED_N)} series, because its mean series is
{float(frame.loc[frame.stratum == alt['registered_everywhere_worst_stratum'], 'mean_MB'].iloc[0]):,.0f} MB.

So the registered minimum does not fit everywhere and something has to give.

## The allocation that was rejected

**Proportional to series.** At the archive's mean of
{float(frame['size_MB'].sum()) / n_series:,.1f} MB per series,
{BUDGET_GB:.0f} GB buys {_fmt(alt['proportional_total_series'])} series in
total. Allocating those proportionally puts
{alt['proportional_largest_share_pct']:.1f} percent of the sample in one
stratum and leaves **{alt['proportional_strata_below_min_rate_n']} of the
{n_strata} strata under {MIN_RATE_N} series**, of which
{alt['proportional_strata_with_zero_series']} would get no series at all. It
spends the budget and returns no reportable rate for most of the frame. That is
C3-13 repeated as a sampling design.

## The allocation that is proposed

Cost-capped, in four steps, all of them stated before any draw:

1. A stratum at or under {REGISTERED_N} series is taken whole.
2. Every other stratum is offered the registered minimum of {REGISTERED_N}.
3. If that does not fit, one per-stratum byte cap B is lowered until it does. A
   stratum whose registered allocation already costs less than B is untouched,
   so precision is bought where it is cheap first and only the expensive strata
   are cut.
4. No stratum is cut below {MIN_RATE_N}, because under that no rate is reported
   and the bytes buy nothing reportable.

The cap that fits is **B = {cap_mb:,.0f} MB per stratum**.

{_md_table(alloc, ["stratum", "series", "n", "sampling_fraction", "expected_GB", "allocation_rule", "reporting_rule"])}

### The arithmetic

| | |
|---|---|
| strata | {n_strata} |
| strata taken whole | {len(whole)} |
| strata at the registered minimum | {len(at_reg)} |
| strata cut by the byte cap | {len(capped)} |
| strata reporting counts only | {int((alloc['n'] < MIN_RATE_N).sum())} |
| **series to fetch** | **{_fmt(n_total)}** of {_fmt(n_series)}, {100 * n_total / n_series:.2f} percent |
| expected bytes | **{exp_gb:.2f} GB** |
| standard deviation of the realised byte total | {sd_gb:.2f} GB |
| {HEADROOM_SIGMA:.0f} sigma upper bound on the realised total | **{up_gb:.2f} GB** |
| budget | {BUDGET_GB:.0f} GB |
| headroom at the upper bound | {BUDGET_GB - up_gb:.2f} GB |

The byte total of a draw is a random sum of skewed series sizes, so the budget
is checked against the {HEADROOM_SIGMA:.0f} sigma upper bound rather than the
expectation. Both are under {BUDGET_GB:.0f} GB.

Before any byte moves, the exact byte total of the drawn manifest is recomputed
from `series_size_MB` and compared against {BUDGET_GB:.0f} GB. If it exceeds it,
the deterministic remedy is to lower B by 5 percent and shorten the same
permutations, never to redraw, and the fact that the gate fired is recorded.

### What the byte cap costs in precision

{cap_rows}

That is the whole precision loss in the frame. Every other stratum is at its
registered allocation or taken whole.

## The estimator

**Population failure rate.** Stratified, series weighted. With
W_h = N_h / N and p_h the observed failure fraction in stratum h:

    p = sum_h W_h p_h

Equivalently the ratio form with design weights w_i = N_h / n_h for series i in
stratum h, which is what the code computes:

    p = ( sum_i w_i y_i ) / ( sum_i w_i ),    y_i in 0, 1

The weights are known exactly because N_h is read from a complete index rather
than estimated. The rate is reported by SOP class and by `analysis_result_id`,
never as a ranking of writers.

**Variance, clustered at the collection.** C3-12 measured that series inside a
collection are not independent, and C3-13 measured the size of the effect:
removing one collection moves a rate from 86.4 to 34.81 percent. The variance
estimator therefore treats the **collection as the primary sampling unit** inside
each stratum. Taylor linearised, ultimate cluster form, for the ratio p:

    u_i  = w_i ( y_i - p ) / sum_i w_i
    u_hj = sum over series i in collection j of stratum h of u_i
    ubar_h = ( 1 / c_h ) sum_j u_hj

    v_clustered(p) = sum_h ( 1 - f_h ) ( c_h / ( c_h - 1 ) )
                     sum_{{j=1}}^{{c_h}} ( u_hj - ubar_h )^2

with f_h = n_h / N_h the sampling fraction and c_h the number of distinct
collections that stratum h's sample actually hit. Degrees of freedom
df = sum_h ( c_h - 1 ) over strata with c_h at least 2, and the interval is
p plus or minus t(df, 0.975) times sqrt(v_clustered).

**The singleton problem, and the fix, both pre-registered.** A stratum with
c_h = 1 contributes no degrees of freedom and no variance term, and
{_fmt(len(singletons))} of the {n_strata} strata are single collection. The
collapsed strata method is used: every c_h = 1 stratum is pooled into one
variance stratum whose primary sampling units are its collections. Point
estimation is untouched. The method is conservative, that is, it charges genuine
between-stratum differences to sampling error and so overstates the width, and
its conservatism is not quantified here.

**Design based variance, reported beside it.** For the finite population target,
which is the number of non-conformant objects actually in IDC {idc_version}, the
correct variance is the stratified simple random sampling variance with the
finite population correction:

    v_design(p) = sum_h W_h^2 ( 1 - f_h ) p_h ( 1 - p_h ) / ( n_h - 1 )

Clustering does not enter it, because series were sampled directly rather than
in clusters. Both are reported. The clustered interval is the wider of the two
and is the one quoted, which is conservative. The design based interval is the
correct width for the only claim this study is scoped to make, which is a claim
about IDC {idc_version} and not about DICOM practice.

## The intracluster correlation and the design effect

Kish, per stratum, with mbar_h the mean number of sampled series per sampled
collection:

    D_h     = 1 + ( mbar_h - 1 ) rho_h
    n_eff,h = n_h / D_h

rho is estimated from the realised sample by one way analysis of variance on the
binary outcome, with the collection as the grouping factor:

    MSB = ( 1 / ( c - 1 ) ) sum_j m_j ( ybar_j - ybar )^2
    MSW = ( 1 / ( M - c ) ) sum_j sum_i ( y_ij - ybar_j )^2
    m0  = ( 1 / ( c - 1 ) ) ( M - sum_j m_j^2 / M ),   M = sum_j m_j
    rho = ( MSB - MSW ) / ( MSB + ( m0 - 1 ) MSW )

**The planning value, measured rather than assumed.** The conformance outcome
cannot be observed without fetching, so its rho is unknown until Phase 3 runs.
What can be measured now is the collection level clustering of
attribute presence defects, which are the same shape of outcome: a Type 2
attribute is empty or it is not, and a validator either complains or it does
not. Four index columns are used as proxies and are labelled as proxies.

The provenance flag of C3-12 is deliberately **not** used. Its within stratum
variance is exactly zero in all {n_strata} strata, because the stratification is
built from the same two attributes the flag is built from, so it would measure
the stratification and not the clustering. That is itself worth stating: the
frame absorbs the C3-12 clustering entirely for the provenance outcome.

{_md_table(icc_seen, ["stratum", "proxy", "collections", "series", "rate_pct", "rho", "m0"])}

Across the {len(icc_seen)} stratum by proxy pairs with any within stratum
variation, rho runs from {icc_seen['rho'].min():.3f} to
{icc_seen['rho'].max():.3f} with a median of **{rho:.3f}**. That median is the
planning value used for sizing below. It is not used in any reported interval.

### What the planning rho does to the frame

{_md_table(prec, ["stratum", "n", "collections_in_stratum", "expected_collections_sampled", "mean_series_per_sampled_collection", "design_effect", "n_effective", "half_width_pts_design_based", "half_width_pts_clustered"])}

Read the two right hand columns together. At rho = {rho:.3f} the design based
half-width of {100 * wilson_half_width(TARGET_P, REGISTERED_N):.2f} points
becomes a clustered half-width of tens of points, and for the single collection
strata the effective sample size falls to about
1 / rho = {1 / rho:.2f}, which is one collection. No amount of series level
sampling changes that. It is the same finding as C3-12, arriving as a
consequence rather than as a caveat: **the effective sample size of this frame
is bounded by its {int(frame['collections'].sum())} stratum by collection cells,
not by its {_fmt(n_total)} series.**

This is the reason the design based interval is reported beside the clustered
one and the reason the study's claims are scoped to IDC {idc_version}. A
finite population count of broken objects in one archive release is exactly
estimable from {_fmt(n_total)} series. A statement about what a toolkit does in
general is not, and none is made.

## The seed

**SEED = {SEED}.** One integer, fixed here in source, used for every stratified
draw in this frame and for nothing else.

The draw is nested. Each stratum is permuted once under a child seed derived
deterministically as `default_rng([SEED, crc32(stratum name)])`, and the
allocation takes a prefix of that permutation. Two consequences: shortening or
lengthening n_h shortens or lengthens the same draw rather than producing a
different one, and no stratum's draw depends on any other stratum's size or on
the order strata are processed in.

## What this frame does not cover

Stated here rather than in limitations, and each item names what is therefore
not claimable.

1. **One SOP class.** {SOP_CLASS} only. Enhanced SR, {_fmt(int(t['enhanced_sr_series']))}
   series, is the other large class and has no frame yet. No rate here is a rate
   for derived objects as a whole.

2. **Post-floor rates only where a floor exists.** F1-01 measured the floor to
   be writer specific, and Phase 1 emitted objects with {' and '.join(WRITERS_WITH_FLOOR)}
   only. {_fmt(int(floored['series'].sum()))} series,
   {100 * float(floored['series'].sum()) / n_series:.1f} percent, sit in strata
   with a measured floor. The other {_fmt(int(unfloored['series'].sum()))},
   {100 * float(unfloored['series'].sum()) / n_series:.1f} percent, do not, so
   for those strata a raw failure rate is reportable and a post-floor rate is
   not. The threshold in PRE-05 is defined above floor, so PRE-05 cannot be
   applied to them.

3. **The writer label is provisional.** W-01 infers it from the two equipment
   attributes the index carries, and
   {_fmt(int(frame.loc[frame.writer == 'not identifiable from index', 'series'].sum()))}
   Segmentation series,
   {100 * float(frame.loc[frame.writer == 'not identifiable from index', 'series'].sum()) / n_series:.1f}
   percent, are not attributable to a writer from the index at all. Phase 2
   reads ImplementationVersionName and ContributingEquipmentSequence, which are
   stronger evidence. If those change a series' writer the strata change, and
   the pre-registered response is to relabel and report the reallocation, not to
   silently redraw.

4. **Single collection strata generalise to nothing.** {_fmt(len(singletons))}
   strata, {_fmt(singleton_series)} series. Their rates describe one collection
   produced by one pipeline in one run. They are reported as such and no claim
   is made from them about the toolkit or the algorithm in general.

5. **Rare defects are bounded, not estimated.** At n = {REGISTERED_N} a defect
   affecting fewer than about 1 in {REGISTERED_N} series in a stratum will
   usually be absent from the sample. Zero observed failures gives an upper
   bound of {100 * wilson(0, REGISTERED_N)[1]:.2f} percent by the Wilson
   interval, and no point rate. Nothing here can find a defect class that
   occurs in a handful of objects.

6. **The compressed transfer syntax minority is covered by accident, not by
   design, and only at n = {_fmt(int(t['compressed_n']))}.**
   {_fmt(int(t['non_default_ts_series']))} Segmentation series carry a transfer
   syntax other than Explicit VR Little Endian,
   {100 * t['non_default_ts_series'] / n_series:.3f} percent, and all of them
   are {t['compressed_syntax']} inside the single stratum
   `{t['compressed_stratum']}`. That stratum is under the registered minimum and
   is taken whole, so the frame does read every compressed object in the class.
   The rate is exact for IDC {idc_version} and carries a below-registered-n
   flag, and it rests on one collection, so nothing about compressed
   Segmentation encoding in general follows from it. P0-04 flagged that a decode
   failure is not a conformance failure, and that separation has to be applied
   by hand in this stratum because no other stratum can calibrate it.

7. **The unit is the series, not the instance.** One stratum,
   `{t['multi_instance_stratum']}`, is
   {t['multi_instance_pct']:.0f} percent multi instance and holds
   {_fmt(int(t['multi_instance_instances']))} instances across
   {_fmt(int(t['multi_instance_series']))} series. Validating one instance per
   series leaves the rest unread. P0-11 put that gap at 4.55 percent of all
   derived instances; inside {SOP_CLASS} alone, which is the only derived class
   with any multi-instance series, it is
   {t['first_file_missed_pct']:.2f} percent of
   {_fmt(int(t['seg_instances']))} instances. No instance level rate is
   estimable from this frame.

8. **Objects outside the SOP class are outside the frame.** P0-12 records that
   segmentation-like content stored under an acquisition SOP class, with
   ImageType (0008,0008) value 1 equal to DERIVED, cannot be sized from the
   index and is not in this population.

9. **Sizes are the archive's own.** `series_size_MB` is an index field, not a
   figure measured on disk. The budget check inherits whatever error it carries,
   which is why {RESERVE_GB:.1f} GB of the {BUDGET_GB:.0f} GB cap is reserved and
   the plan is built against {PLANNING_BUDGET_GB:.1f} GB.

10. **One release.** IDC {idc_version}. The strata, their sizes and the weights
    W_h are all release specific, and the frame is void on the next release.

## What was dropped

Nothing yet, because nothing has run. The frame proposes to read
{_fmt(n_total)} of {_fmt(n_series)} series,
{100 * n_total / n_series:.2f} percent, and {100 * exp_gb / total_gb:.2f}
percent of the class by volume. The
{_fmt(n_series - n_total)} series not drawn are represented through the stratum
weights W_h and through nothing else.
"""
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return out


# PRE-06 is a pre-registration and a proposal may only record an outcome on it.
# These are the only fields this module is allowed to set. Everything else that
# PRE-06 already carries is copied back verbatim, because colophon.ledger
# replaces a row wholesale and an omitted field would be blanked rather than
# left alone.
PRE06_SETTABLE = {"status", "status_note", "value", "notes", "source_file",
                  "command", "n", "denominator", "dropped"}
PRE06_CLAIM = "Sampling frame, fixed before seeing which strata look interesting."


def pre06_carry_forward() -> dict:
    """Read PRE-06 from the ledger and return the fields that must not change.

    Restricted to colophon.merge_ledger.OUTCOME_FIELDS, because a proposal that
    names any field outside that set is refused by the merge.
    """
    from . import ledger
    from .merge_ledger import OUTCOME_FIELDS
    rows = {r["id"]: r for r in ledger.load()}
    if "PRE-06" not in rows:
        raise KeyError("PRE-06 is not in the ledger, so there is nothing to "
                       "propose an update to")
    prior = rows["PRE-06"]
    if prior["claim"].strip() != PRE06_CLAIM:
        raise ValueError(
            "the PRE-06 claim in the ledger is not the one this module "
            "reproduces. It is a pre-registration and is never reworded, so "
            "stop rather than write a proposal against a claim that moved.")
    frozen = {}
    for field, value in prior.items():
        if field in ("id", "claim") or field in PRE06_SETTABLE:
            continue
        if not (value or "").strip():
            continue
        if field not in OUTCOME_FIELDS:
            # date and idc_index_version are rewritten by the ledger writer.
            if field in ("date", "idc_index_version"):
                continue
            raise ValueError(
                "PRE-06 carries a non-empty %s, which this module may neither "
                "change nor pass through. Resolve by hand." % field)
        frozen[field] = value
    return frozen


def proposed_ledger_rows(idc_version: str, t: dict) -> list[dict]:
    """Rows for results/pending_ledger/track_e.json.

    PRE-06 is a pre-registration. Its claim is reproduced verbatim from
    results/ledger.csv, only the fields in PRE06_SETTABLE are set, and every
    other field it already carries is copied back unchanged. Everything this
    track measured that is not PRE-06 itself goes into new E-nn rows.
    """
    frame, alloc, prec = t["strata"], t["allocation"], t["precision"]
    alt, rho = t["alternatives"], t["rho"]
    n_series = int(frame["series"].sum())
    n_total = int(alloc["n"].sum())
    exp_gb = alloc.attrs["expected_MB_total"] / 1024
    up_gb = alloc.attrs["upper_MB_total"] / 1024
    singletons = frame[frame["collections"] == 1]
    unfloored = alloc[~alloc["has_floor"]]
    capped = alloc[(alloc["n"] < REGISTERED_N) & (alloc["series"] > REGISTERED_N)]
    rnp = registered_n_properties()

    common = dict(
        section="V", section_title="Panel design, fixed before Phase 1",
        sop_class=SOP_CLASS, command=CMD,
        source_file="results/pre06_sampling_frame.md",
        validator="none, index metadata only",
        validator_version="idc-index-data %s" % idc_version)

    dropped_pre06 = (
        "the frame reads %s of %s series, %.2f percent, and %.2f percent of the "
        "class by volume; not covered and named in the proposal: the compressed "
        "transfer syntax minority of %s series, the instance level rate, the "
        "ImageType DERIVED stratum of P0-12, and post-floor rates for the %s "
        "series in strata whose writer has no measured Phase 1 floor"
        % (_fmt(n_total), _fmt(n_series), 100 * n_total / n_series,
           100 * exp_gb / float(frame["size_GB"].sum()),
           _fmt(int(t["non_default_ts_series"])),
           _fmt(int(unfloored["series"].sum()))))

    rows = [
        dict(pre06_carry_forward(),
             id="PRE-06",
             claim=PRE06_CLAIM,
             status="PENDING",
             status_note="A frame is now proposed for the one class that still "
             "needs one and is published as results/pre06_sampling_frame.md. "
             "The row stays PENDING because the frame is a proposal awaiting "
             "approval: colophon.sample.EXECUTE is False and every function "
             "that would draw or fetch raises while it is. Nothing has been "
             "drawn and no Segmentation object has been fetched.",
             value="Segmentation Storage, %d strata by writing toolkit and "
                   "analysis_result_id over %s series and %.2f TB. Allocation: "
                   "registered minimum n = %d per stratum from PRE-05, strata at "
                   "or under %d taken whole, one per-stratum byte cap of %.0f MB "
                   "lowered until the budget fits, no stratum cut below %d. "
                   "Plan: %s series, %.2f GB expected, %.2f GB at the %.0f sigma "
                   "upper bound, against a %.0f GB budget. Seed %d. Estimator: "
                   "stratified series-weighted rate with a Taylor linearised "
                   "ultimate-cluster variance taking the collection as the "
                   "primary sampling unit, reported beside the stratified SRS "
                   "variance with finite population correction."
                   % (len(frame), _fmt(n_series),
                      float(frame["size_GB"].sum()) / 1024, REGISTERED_N,
                      REGISTERED_N, alloc.attrs["byte_cap_MB"], MIN_RATE_N,
                      _fmt(n_total), exp_gb, up_gb, HEADROOM_SIGMA, BUDGET_GB,
                      SEED),
             n=_fmt(n_total), denominator=_fmt(n_series),
             dropped=dropped_pre06,
             command=CMD,
             source_file="results/pre06_sampling_frame.md",
             notes="Rests on PRE-05 for the registered minimum, C3-12 and C3-13 "
                   "for the clustering, F1-01 for the writer-specific floor, "
                   "P0-03 for the population and W-01 for the writer labels. "
                   "Detail is carried in E-01 to E-07 and pinned by "
                   "tests/test_sample.py. Proportional-to-series allocation was "
                   "costed and rejected: it buys %s series in total, puts %.1f "
                   "percent of them in one stratum and leaves %d of %d strata "
                   "under %d series, so most of the frame would return no "
                   "reportable rate. Giving every stratum the registered "
                   "minimum was costed at %.1f GB, %.2f times the budget."
                   % (_fmt(alt["proportional_total_series"]),
                      alt["proportional_largest_share_pct"],
                      alt["proportional_strata_below_min_rate_n"], len(frame),
                      MIN_RATE_N, alt["registered_everywhere_GB"],
                      alt["registered_everywhere_over_budget_factor"])),
        dict(id="E-01",
             claim="Segmentation Storage partitions into %d strata by writing "
                   "toolkit and analysis_result_id, and the mean cost of one "
                   "series varies by a factor of %s across them."
                   % (len(frame), _fmt(round(float(frame["mean_MB"].max())
                                             / float(frame["mean_MB"].min())))),
             status="MEASURED",
             value="%d strata over %s series and %.2f TB; mean series size runs "
                   "from %.3f MB in %s to %.0f MB in %s"
                   % (len(frame), _fmt(n_series),
                      float(frame["size_GB"].sum()) / 1024,
                      float(frame["mean_MB"].min()),
                      str(frame.loc[frame["mean_MB"].idxmin(), "stratum"]),
                      float(frame["mean_MB"].max()),
                      str(frame.loc[frame["mean_MB"].idxmax(), "stratum"])),
             n=str(len(frame)), denominator=_fmt(n_series),
             floor="not applicable, no validator involved",
             dropped="nothing, the strata partition the complete class",
             source_file="results/phase0/seg_strata.csv",
             pinned_by_test="tests/test_sample.py::test_strata_partition",
             status_note="The spread in cost per series, not the spread in "
             "series count, is what rules out a proportional allocation.",
             **{k: v for k, v in common.items() if k != "source_file"}),
        dict(id="E-02",
             claim="The registered minimum of n = %d is carried from PRE-05 "
                   "unchanged, and what it buys is computed rather than "
                   "asserted." % REGISTERED_N,
             status="DERIVED",
             value="n = %d gives a 95 percent Wilson half-width of %.2f points "
                   "at the PRE-05 threshold p = %.2f and %.2f points at the "
                   "least favourable p = %.2f; the smallest n reaching %.0f "
                   "points at p = %.2f is %d by Wilson and %d by the "
                   "conventional Wald formula"
                   % (rnp["n"], rnp["half_width_pts_at_threshold"], TARGET_P,
                      rnp["half_width_pts_worst_case"], WORST_CASE_P,
                      100 * WORST_CASE_HALF_WIDTH, WORST_CASE_P,
                      rnp["wilson_minimum_worst_case"], rnp["wald_worst_case"]),
             n=str(REGISTERED_N), denominator="per published stratum",
             floor="not applicable, this row fixes a sample size rather than "
                   "quoting a rate",
             dropped="nothing",
             derived_from="PRE-05",
             pinned_by_test="tests/test_sample.py::test_registered_n_properties",
             status_note="PRE-05 registers the number and its justification. "
             "This row reproduces both from code so the sizing can be checked "
             "without rerunning the argument, and it does not rederive the "
             "number or move it.",
             notes="Strata of %d to %d report a rate with a Wilson interval and "
                   "a below-registered-n flag. Under %d reports counts only and "
                   "never a rate."
                   % (MIN_RATE_N, REGISTERED_N - 1, MIN_RATE_N),
             **common),
        dict(id="E-03",
             claim="The stratification absorbs the C3-12 provenance clustering "
                   "completely, so the intracluster correlation for the "
                   "conformance outcome has to be planned from a different "
                   "measurement.",
             status="MEASURED",
             value="the C3-12 encoder flag has exactly zero within-stratum "
                   "variance in all %d strata; across the %d stratum by proxy "
                   "pairs of attribute-presence defects that do vary, the "
                   "collection-level rho runs %.3f to %.3f with a median of %.3f"
                   % (len(frame), int(t["icc"]["rho"].notna().sum()),
                      float(t["icc"]["rho"].min()), float(t["icc"]["rho"].max()),
                      rho),
             n=str(int(t["icc"]["rho"].notna().sum())),
             denominator="%d stratum by proxy pairs examined"
                         % int(len(t["icc"])),
             floor="not applicable, no validator involved",
             dropped="stratum by proxy pairs with no within-stratum variation "
                     "return no rho and are excluded from the median, which is "
                     "%d of %d" % (int(t["icc"]["rho"].isna().sum()),
                                   int(len(t["icc"]))),
             derived_from="C3-12",
             source_file="results/phase0/seg_icc_proxies.csv",
             pinned_by_test="tests/test_sample.py::test_planning_icc",
             status_note="The proxies are index-observable attribute-presence "
             "indicators, not conformance outcomes, and are labelled as proxies "
             "throughout. The reported intervals will use rho estimated from "
             "the realised sample, not this planning value.",
             notes="The measured median is used for sizing only. At that value "
                   "the effective sample size of the frame is bounded by its "
                   "stratum by collection cells rather than by its series, "
                   "which is C3-12 arriving as a design consequence.",
             **{k: v for k, v in common.items() if k != "source_file"}),
        dict(id="E-04",
             claim="A post-floor failure rate is not defined for every stratum, "
                   "because the Phase 1 floor is writer specific and Phase 1 "
                   "emitted two writers.",
             status="DERIVED",
             value="%s of %s Segmentation series, %.1f percent, sit in strata "
                   "written by dcmqi or highdicom and can carry a post-floor "
                   "rate; the remaining %s, %.1f percent, can carry a raw rate "
                   "only"
                   % (_fmt(int(alloc.loc[alloc["has_floor"], "series"].sum())),
                      _fmt(n_series),
                      100 * float(alloc.loc[alloc["has_floor"], "series"].sum()) / n_series,
                      _fmt(int(unfloored["series"].sum())),
                      100 * float(unfloored["series"].sum()) / n_series),
             n=_fmt(int(unfloored["series"].sum())), denominator=_fmt(n_series),
             floor="writer specific, from F1-01 and F1-02. That is the "
                   "restriction this row states.",
             dropped="the PRE-05 threshold is defined above floor and therefore "
                     "cannot be applied to the strata without one",
             derived_from="F1-01, F1-02, PRE-05, W-01",
             pinned_by_test="tests/test_sample.py::test_floor_coverage",
             **common),
        dict(id="E-05",
             claim="One stratum cannot be given the registered minimum inside "
                   "the disk budget, and the precision it loses is stated "
                   "rather than absorbed.",
             status="DERIVED",
             value=("; ".join(
                 "%s: n = %s of %s series at %.0f MB each, %.2f GB, Wilson "
                 "half-width at p = 5 percent widens from %.2f to %.2f points"
                 % (r.stratum, _fmt(int(r.n)), _fmt(int(r.series)), r.mean_MB,
                    float(r.expected_GB),
                    100 * wilson_half_width(TARGET_P, REGISTERED_N),
                    100 * wilson_half_width(TARGET_P, int(r.n)))
                 for r in capped.itertuples())
                 or "no stratum is cut, every stratum fits at the registered "
                    "minimum"),
             n=str(len(capped)), denominator=str(len(frame)),
             floor="not applicable, this row states a precision loss rather "
                   "than a rate",
             dropped="no stratum is dropped and none falls below the %d series "
                     "needed to report a rate at all" % MIN_RATE_N,
             derived_from="PRE-05, P0-03",
             pinned_by_test="tests/test_sample.py::test_every_stratum_has_a_rule",
             **common),
        dict(id="E-06",
             claim="Under the measured planning correlation the effective "
                   "sample size of the frame is bounded by its collections, not "
                   "by its series.",
             status="DERIVED",
             value="at rho = %.3f the design effect reaches %.0f in the largest "
                   "stratum, the %d single-collection strata fall to an "
                   "effective n of about %.1f, and the design-based half-width "
                   "of %.2f points becomes a clustered half-width of %.1f to "
                   "%.1f points"
                   % (rho, float(prec["design_effect"].max()), len(singletons),
                      1 / rho,
                      100 * wilson_half_width(TARGET_P, REGISTERED_N),
                      float(prec["half_width_pts_clustered"].min()),
                      float(prec["half_width_pts_clustered"].max())),
             n=str(len(singletons)), denominator=str(len(frame)),
             floor="not applicable, this row states an interval width rather "
                   "than a rate",
             dropped="nothing",
             derived_from="C3-12, C3-13, E-03",
             pinned_by_test="tests/test_sample.py::test_clustering_dominates",
             status_note="The clustered interval is quoted because it is the "
             "wider of the two. The design-based interval with the finite "
             "population correction is reported beside it and is the correct "
             "width for the only target this study claims, a count of "
             "non-conformant objects in one archive release.",
             notes="This licenses no inference about DICOM practice and none is "
                   "made. Same scope statement as C3-12.",
             **common),
        dict(id="E-07",
             claim="No draw and no fetch has occurred. The frame is fenced in "
                   "code, not only in prose.",
             status="MEASURED",
             value="colophon.sample.EXECUTE is False; draw() and "
                   "fetch_manifest() raise ExecutionBlocked; 0 Segmentation "
                   "objects fetched, 0 bytes",
             n="0", denominator=_fmt(n_series),
             floor="not applicable, nothing was validated",
             dropped="everything, by design: the entire class is unfetched "
                     "pending approval of PRE-06",
             source_file="colophon/sample.py",
             pinned_by_test="tests/test_sample.py::test_execute_guard_blocks_a_draw",
             **{k: v for k, v in common.items() if k != "source_file"}),
    ]
    return rows


# --- entry point --------------------------------------------------------------
def build(df: pd.DataFrame) -> dict:
    seg = segmentation(df)
    frame = strata(seg)
    icc_table, rho = planning_icc(seg)
    alloc = allocate(frame)
    prec = precision(alloc, rho)
    alt = alternatives(frame)

    non_default = seg[seg["transfer_syntax_name"] != "Explicit VR Little Endian"]
    # Probability that a draw of this size contains at least one, computed
    # stratum by stratum under sampling without replacement.
    p_none = 1.0
    for r in alloc.itertuples():
        sub = seg[seg["stratum"] == r.stratum]
        k = int((sub["transfer_syntax_name"] != "Explicit VR Little Endian").sum())
        if k == 0:
            continue
        big = len(sub)
        n = int(r.n)
        if big - k - n < 0:
            p_none = 0.0
            break
        lg = math.lgamma
        p_none *= math.exp((lg(big - k + 1) - lg(big - k - n + 1))
                           - (lg(big + 1) - lg(big - n + 1)))
    if len(non_default):
        comp_stratum = str(non_default["stratum"].value_counts().index[0])
        comp_syntax = " and ".join(
            sorted(set(non_default["transfer_syntax_name"].astype(str))))
        comp_n = int(alloc.loc[alloc["stratum"] == comp_stratum, "n"].iloc[0])
    else:
        comp_stratum, comp_syntax, comp_n = "none", "none", 0

    multi = seg[seg["instanceCount"] > 1]
    multi_stratum = (multi["stratum"].value_counts().index[0] if len(multi)
                     else "none")
    multi_sub = seg[seg["stratum"] == multi_stratum]
    d_all = derived(df)
    inst = int(d_all.loc[d_all["sop_class_name"] == SOP_CLASS,
                         "instanceCount"].sum())

    return {
        "segmentation": seg,
        "strata": frame,
        "icc": icc_table,
        "rho": rho,
        "allocation": alloc,
        "precision": prec,
        "alternatives": alt,
        "non_default_ts_series": int(len(non_default)),
        "p_any_compressed": 1.0 - p_none,
        "compressed_stratum": comp_stratum,
        "compressed_syntax": comp_syntax,
        "compressed_n": comp_n,
        "seg_instances": inst,
        "multi_instance_stratum": multi_stratum,
        "multi_instance_series": int(len(multi_sub)),
        "multi_instance_instances": int(multi_sub["instanceCount"].sum()),
        "multi_instance_pct": 100 * float((multi_sub["instanceCount"] > 1).mean())
                              if len(multi_sub) else 0.0,
        "first_file_missed_pct": 100 * (inst - len(seg)) / inst if inst else 0.0,
        "enhanced_sr_series": int((d_all["sop_class_name"]
                                   == "Enhanced SR Storage").sum()),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--print-only", action="store_true", help="write nothing")
    args = ap.parse_args(argv)

    assert SOP_CLASS in DERIVED_SOP_CLASSES, "the target class left the census"

    idc_version, df = load_index()
    t = build(df)
    frame, alloc, prec = t["strata"], t["allocation"], t["precision"]
    exp_gb = alloc.attrs["expected_MB_total"] / 1024
    up_gb = alloc.attrs["upper_MB_total"] / 1024

    print("IDC %s. %s: %s series, %.2f TB, %d strata."
          % (idc_version, SOP_CLASS, _fmt(int(frame["series"].sum())),
             float(frame["size_GB"].sum()) / 1024, len(frame)))
    print()
    print(alloc[["stratum", "series", "n", "expected_GB", "allocation_rule",
                 "reporting_rule"]].to_string(index=False))
    print()
    print("registered minimum        n = %d, Wilson half-width %.2f points at "
          "p = %.2f" % (REGISTERED_N,
                        100 * wilson_half_width(TARGET_P, REGISTERED_N), TARGET_P))
    print("series to fetch           %s of %s, %.2f percent"
          % (_fmt(int(alloc["n"].sum())), _fmt(int(frame["series"].sum())),
             100 * int(alloc["n"].sum()) / int(frame["series"].sum())))
    print("expected bytes            %.2f GB" % exp_gb)
    print("%.0f sigma upper bound      %.2f GB" % (HEADROOM_SIGMA, up_gb))
    print("budget                    %.0f GB, headroom %.2f GB"
          % (BUDGET_GB, BUDGET_GB - up_gb))
    print("planning rho              %.3f, measured, %d stratum by proxy pairs"
          % (t["rho"], int(t["icc"]["rho"].notna().sum())))
    print("seed                      %d" % SEED)
    print()
    print(prec.to_string(index=False))
    print()
    print("EXECUTE is %s. No draw, no fetch, 0 bytes." % EXECUTE)

    if args.print_only:
        return 0

    PHASE0.mkdir(parents=True, exist_ok=True)
    out_frame = frame.drop(columns=["collection_sizes"])
    out_alloc = alloc.drop(columns=["collection_sizes"])
    out_frame.to_csv(PHASE0 / "seg_strata.csv", index=False)
    out_alloc.to_csv(PHASE0 / "seg_allocation.csv", index=False)
    prec.to_csv(PHASE0 / "seg_precision.csv", index=False)
    t["icc"].to_csv(PHASE0 / "seg_icc_proxies.csv", index=False)

    md = write_markdown(idc_version, t, RESULTS / "pre06_sampling_frame.md")
    print("wrote %s" % md)

    pending = RESULTS / "pending_ledger"
    pending.mkdir(parents=True, exist_ok=True)
    rows = proposed_ledger_rows(idc_version, t)
    (pending / "track_e.json").write_text(
        json.dumps(rows, indent=2), encoding="utf-8")
    print("proposed %d ledger rows to %s"
          % (len(rows), pending / "track_e.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
