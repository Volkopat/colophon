"""Intervals for the one class that is a sample.

Seven of the eight censused classes are complete enumerations. A complete
enumeration has no sampling error, so an interval on it would not be
conservative, it would be meaningless. Segmentation is the exception: 5,941 of
190,146 series drawn under the PRE-06 frame, so every proportion computed on it
is an estimate and a reader is entitled to its precision.

What is reported, and what is not:

- The Wilson 95 percent interval on each Segmentation grade, computed with
  `sample.wilson`, the same function and the same registered reporting rule the
  Phase 3 report already applies to the identification proportions.
- Those intervals ignore clustering. Objects nest in series and series nest in
  collections, so the true interval is wider and this one is a lower bound on
  width. This is stated rather than corrected, and it is the same position
  `phase3_report` already takes on segment-level intervals.
- The design effect implied by the frame's registered planning ICC is reported
  beside it so the reader can see the magnitude of what is not corrected.

What is deliberately not done: the planning ICC of 0.919 is not applied to
produce a clustered interval. It was measured on the proxy columns in
`sample.ICC_PROXY_COLUMNS`, which are homogeneous within a collection by their
nature, and treating it as the intracluster correlation of a conformance outcome
would overstate the width as badly as ignoring clustering understates it. An
outcome-specific ICC is not computable from the shipped artefacts, because
per-series conformance outcomes are aggregated to the stratum. That is a gap and
it is named here rather than filled with the nearest available number.

Reproduce with `python -m colophon.seg_intervals`.
"""
from __future__ import annotations

import json

import pandas as pd

from . import sample
from .paths import RESULTS

OUT = RESULTS / "phase3" / "seg_intervals.json"
CMD = "python -m colophon.seg_intervals"

# The frame's registered planning value, from PRE-06. Reported for scale,
# never used to widen an interval: see the module docstring.
PLANNING_ICC = 0.919

GRADES = [("non-conformant", "non-conformant"),
          ("conformant but uninformative", "conformant but uninformative"),
          ("informative", "informative")]


def compute() -> dict:
    t2 = pd.read_csv(RESULTS / "manuscript" / "table2.csv")
    row = t2[t2["sop_class_name"].str.startswith("Segmentation")].iloc[0]
    n = int(row["objects"])

    status = pd.read_csv(RESULTS / "phase3" / "seg_series_status.csv")
    series = int(len(status))
    clusters = int(status["collection_id"].nunique())
    m_bar = series / clusters
    rho = PLANNING_ICC
    deff = sample.design_effect(m_bar, rho)

    grades = {}
    for column, label in GRADES:
        k = int(row[column])
        lo, hi, half = sample.wilson(k, n)
        grades[label] = {
            "k": k, "n": n,
            "pct": round(100.0 * k / n, 2),
            "lo": round(100.0 * lo, 2),
            "hi": round(100.0 * hi, 2),
            "half_width": round(100.0 * half, 2),
        }
    return {
        "unit": "object",
        "objects": n, "series": series, "collections": clusters,
        "mean_series_per_collection": round(m_bar, 2),
        "planning_icc": rho,
        "design_effect_at_planning_icc": round(deff, 1),
        "effective_series_at_planning_icc": round(series / deff, 1),
        "grades": grades,
        "method": "Wilson 95 percent, unadjusted for clustering",
        "not_done": ("no outcome-specific intracluster correlation, because "
                     "per-series conformance outcomes are aggregated to the "
                     "stratum in the shipped artefacts; the planning ICC is "
                     "not substituted for one"),
        "census_classes": ("the other seven classes are complete enumerations "
                           "and carry no interval, because they have no "
                           "sampling error"),
        "command": CMD,
    }


def sentence() -> str:
    """The clause the manuscript quotes, built from the computed values."""
    r = compute()
    g = r["grades"]
    parts = ", ".join(
        "%s %.2f percent (95 percent Wilson %.2f to %.2f)"
        % (label, g[label]["pct"], g[label]["lo"], g[label]["hi"])
        for _, label in GRADES)
    return (
        "Over the %d Segmentation objects: %s. These intervals are unadjusted "
        "for clustering and are therefore a lower bound on width: objects nest "
        "in series and series in %d collections, at a realised mean of %.1f "
        "series per collection, and the frame's registered planning "
        "intracluster correlation of %.3f implies a design effect of %.1f at "
        "that cluster size. That planning value was measured on proxy columns "
        "rather than on a conformance outcome, so it is reported as the "
        "magnitude of what is not corrected and is not used to widen the "
        "intervals."
        % (r["objects"], parts, r["collections"],
           r["mean_series_per_collection"], r["planning_icc"],
           r["design_effect_at_planning_icc"]))


def main() -> int:
    report = compute()
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for label, g in report["grades"].items():
        print("%-30s %5d/%d  %6.2f%%  [%.2f, %.2f]"
              % (label, g["k"], g["n"], g["pct"], g["lo"], g["hi"]))
    print("design effect at planning ICC %.3f: %.1f (n_eff %.1f series)"
          % (report["planning_icc"], report["design_effect_at_planning_icc"],
             report["effective_series_at_planning_icc"]))
    print("wrote %s" % OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
