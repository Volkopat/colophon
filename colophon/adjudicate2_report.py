"""Net rates under both adjudication passes, the agreement, and the write-up.

`colophon.adjudicate2` adjudicates. This module recomputes the rates under each
pass and under the consensus rule, writes ADJUDICATION2.md, and proposes the
ledger rows. Nothing here re-adjudicates and no first-pass verdict is edited.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pandas as pd

from . import adjudicate2 as a2
from .adjudicate2 import CMD, NET, OUT
from .paths import REPO, RESULTS

ADJUDICATED_CLASSES = [
    "Real World Value Mapping Storage", "Key Object Selection Document Storage",
    "Grayscale Softcopy Presentation State Storage", "Parametric Map Storage",
    "Comprehensive SR Storage", "Comprehensive 3D SR Storage",
]


def net_rates(compare: pd.DataFrame) -> pd.DataFrame:
    """Objects carrying at least one NET class, under each pass and consensus.

    The consensus column is what the registered rule produces: a class counts
    toward the numerator only where both passes independently called it net, and
    every disagreement drops to undecidable and is excluded. That can only move
    a net rate down, which is the conservative direction and is the reason a
    two-adjudicator design exists.
    """
    from . import census

    verdicts = {(r.validator, r.message_class_id):
                (r.adjudication1, r.adjudication2, r.consensus)
                for r in compare.itertuples()}

    per_class = Counter()
    hit = {k: Counter() for k in ("pass1", "pass2", "consensus")}
    cells: dict[tuple, list[int]] = {}

    for record in census.load_records():
        sop = record["sop_class_name"]
        if sop not in ADJUDICATED_CLASSES or record["status"] != "OK":
            continue
        cell = cells.setdefault((sop, record["collection_id"]), [0, 0, 0, 0])
        for obj in record.get("objects", []):
            if obj.get("status") != "OK":
                continue
            per_class[sop] += 1
            cell[0] += 1
            flags = [False, False, False]
            for validator, mcid, _sev, _template in obj.get("messages", []):
                found = verdicts.get((validator, mcid))
                if not found:
                    continue
                for i, verdict in enumerate(found):
                    if verdict == NET:
                        flags[i] = True
            for i, key in enumerate(("pass1", "pass2", "consensus")):
                if flags[i]:
                    hit[key][sop] += 1
                    cell[i + 1] += 1

    rows = []
    for sop in ADJUDICATED_CLASSES:
        n = per_class.get(sop, 0)
        if not n:
            continue
        mine = [v for (s, _c), v in cells.items() if s == sop and v[0]]
        row = {"sop_class_name": sop, "objects": n, "collections": len(mine)}
        for i, key in enumerate(("pass1", "pass2", "consensus")):
            k = hit[key].get(sop, 0)
            row["net_%s" % key] = k
            row["pct_%s" % key] = round(100 * k / n, 2)
            rates = [100 * c[i + 1] / c[0] for c in mine]
            # Boundary counts, not a median: PRE-05 condition (b) needs the
            # collection-level distribution and it is two point masses.
            row["collections_at_zero_%s" % key] = sum(1 for r in rates if r == 0)
            row["collections_at_hundred_%s" % key] = sum(1 for r in rates if r == 100)
        rows.append(row)
    return pd.DataFrame(rows)


def build() -> dict:
    compare = a2.consensus(a2.second_pass())
    blind = compare[~compare.pre_disclosed]
    return {
        "compare": compare,
        "net": net_rates(compare),
        "agreement": {
            "message_classes": int(len(compare)),
            "pre_disclosed_classes": int(compare.pre_disclosed.sum()),
            "three_way_all": a2.kappa(compare.adjudication1, compare.adjudication2),
            "three_way_blind": a2.kappa(blind.adjudication1, blind.adjudication2),
            "net_binary_all": a2.kappa(compare.net1.map(str), compare.net2.map(str),
                                       labels=("True", "False")),
            "net_binary_blind": dict(
                a2.kappa(blind.net1.map(str), blind.net2.map(str),
                         labels=("True", "False")),
                # The direction of the disagreement, not only its size. A
                # one-directional disagreement means the consensus rule discards
                # classes from one pass only, which is a fragility worth stating.
                pass1_only=int((blind.net1.astype(bool)
                                & ~blind.net2.astype(bool)).sum()),
                pass2_only=int((~blind.net1.astype(bool)
                                & blind.net2.astype(bool)).sum())),
            "crosswalk": a2.CROSSWALK,
        },
    }


def write(t: dict) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    t["compare"].to_csv(OUT / "two_pass_comparison.csv", index=False)
    t["net"].to_csv(OUT / "net_rates_two_pass.csv", index=False)
    (OUT / "agreement.json").write_text(json.dumps(t["agreement"], indent=2),
                                        encoding="utf-8")

    a, compare, net = t["agreement"], t["compare"], t["net"]
    dis = compare[compare.adjudication1 != compare.adjudication2]
    dis_rows = "\n".join(
        "| `%s` | %s | %s | %s | %s |"
        % (r.family[:86], r.adjudication1, r.adjudication2,
           f"{r.ids:,}", f"{r.obj:,}")
        for r in dis.groupby(["family", "adjudication1", "adjudication2"])
                    .agg(ids=("message_class_id", "size"), obj=("objects", "sum"))
                    .reset_index().sort_values("obj", ascending=False)
                    .head(14).itertuples()) or "| none | | | | |"

    net_rows = "\n".join(
        "| %s | %s | %s | %.2f | %s | %.2f | **%s** | **%.2f** |"
        % (r.sop_class_name, f"{r.objects:,}", f"{r.net_pass1:,}", r.pct_pass1,
           f"{r.net_pass2:,}", r.pct_pass2, f"{r.net_consensus:,}",
           r.pct_consensus)
        for r in net.itertuples())

    text = f"""# The second adjudication pass, and the agreement between the two

PRE-03 and addendum 02 section 5 register **two independent adjudicators, with
any disagreement staying undecidable**. The first pass used one adjudicator per
class. This is the second, reported beside the first rather than replacing it.
Reproduce with `{CMD}`.

## What this is, and what it is not

The second pass was performed by **the same LLM agent** that produced the first,
under the ordered rule table published in `colophon/adjudicate2.py`, after
re-reading the message templates without the first pass's verdict columns.

That makes it an **intra-instrument repeatability check, not an independent
human adjudication**. It establishes that the rule table is applied reproducibly
and it surfaces the classes where the reading is unstable. It does **not**
establish that either reading is correct, and it does not satisfy the intent of
two independent adjudicators, which is two people who can disagree for reasons
the instrument cannot generate. Methods carries that sentence and not a weaker
one.

**Blindness is partial, and the compromise is measured.** `MORNING_REPORT.md` is
part of the session's required reading and it discloses several first-pass
verdicts in prose. **{a['pre_disclosed_classes']:,} of {a['message_classes']:,}
message classes** match a disclosed family and are flagged `PRE_DISCLOSED`.
Agreement is reported over all classes and over the blind subset separately, and
the blind figure is the one to quote.

**Two regexes were corrected after the first comparison run.** Both failed to
match the text they were written for: the functional-group message says
`is unexpected` where the rule said `is missing`, and a literal `>` had been
written `)`. The verdicts and rationales those rules carry were not changed, only
the patterns that select them. Recorded because it is a departure from strict
blindness even though it is a coding defect rather than a revision of judgement.

## The two scales, and the crosswalk between them

The passes used different vocabularies, which is itself a result of running two.
The first has five terms and the second three: the first splits what the second
calls floor into three cases, by **why** the message is not a defect.

| first pass | second pass | meaning |
|---|---|---|
| `FLOOR` | `FLOOR` | a floor class, legal by a cited section |
| `NOT-IOD` | `FLOOR` | not a requirement of this object's IOD at all |
| `PLAUSIBILITY` | `FLOOR` | a heuristic of the validator's own, citing no Type and no condition |
| `NET` | `NET` | a genuine defect against a cited requirement |
| `UNDECIDABLE` | `UNDECIDABLE` | not adjudicable from the object and the text |

All three of the first pass's exclusion terms mean the same thing for any rate:
the class does not count toward a net numerator. The crosswalk is published here
rather than applied silently. Comparing on the second pass's coarser scale
without it measured the vocabulary rather than the judgement, and returned an
agreement of 16.62 percent that meant nothing.

## Agreement

| comparison | classes | agreement | Cohen's kappa |
|---|---|---|---|
| three-way, crosswalked, all classes | {a['three_way_all']['n']:,} | {a['three_way_all']['agreement']} percent | {a['three_way_all']['kappa']} |
| three-way, crosswalked, **blind subset** | {a['three_way_blind']['n']:,} | {a['three_way_blind']['agreement']} percent | **{a['three_way_blind']['kappa']}** |
| counts toward the net numerator, all classes | {a['net_binary_all']['n']:,} | {a['net_binary_all']['agreement']} percent | {a['net_binary_all']['kappa']} |
| counts toward the net numerator, **blind subset** | {a['net_binary_blind']['n']:,} | {a['net_binary_blind']['agreement']} percent | **{a['net_binary_blind']['kappa']}** |

The net-relevant binary is the comparison that matters, because it is the only
decision that reaches a published rate. Everything else is a difference in how an
exclusion is explained.

## Where the two passes disagree

| family | pass 1 | pass 2 | message classes | object hits |
|---|---|---|---|---|
{dis_rows}

The dominant disagreement is principled rather than an oversight. The first pass
adjudicated several `dicom-validator` findings inside SR content sequences as
net. The second pass declines them, because addendum 02 section 2 registers that
dicom-validator 0.8.2 emits no severity levels and demotes any 1C or 2C
condition it cannot parse to Type 3, so it **fails open** and is registered as a
second opinion rather than a rate source. Under the registered rule the
disagreement drops to undecidable and the class leaves the numerator.

## Net rates under each pass and under the consensus

A class counts toward the numerator only where **both** passes called it net.
Every disagreement drops to undecidable and is excluded, so the consensus rate
can only move down. That is the conservative direction and it is what a
two-adjudicator design is for.

| SOP class | objects | net, pass 1 | percent | net, pass 2 | percent | net, consensus | percent |
|---|---|---|---|---|---|---|---|
{net_rows}

The collection-level boundary counts PRE-05 condition (b) needs are in
`results/adjudication2/net_rates_two_pass.csv`, as counts at 0 and at 100 rather
than as a median.

## What this changes and what it does not

- **No first-pass verdict was edited.** Both adjudications are published side by
  side in `results/adjudication2/two_pass_comparison.csv`, one row per message
  class, with both citations.
- **No net rate should be quoted from a single pass now that two exist.** The
  consensus column is the one PRE-03 licenses.
- **The check is intra-instrument.** A second human adjudicator is still
  required and is still outstanding, and that is stated in Methods rather than
  in limitations.
"""
    path = REPO / "ADJUDICATION2.md"
    path.write_text(text, encoding="utf-8")
    return path


def propose_ledger(t: dict) -> Path:
    a, net = t["agreement"], t["net"]
    common = dict(section="ADJ2", section_title="Second adjudication pass",
                  command=CMD, source_file="ADJUDICATION2.md",
                  validator="dciodvfy and dicom-validator",
                  validator_version="dicom3tools snapshot 20260701065818; "
                                    "dicom-validator 0.8.2 edition 2026c",
                  sop_class="the six adjudicated classes")
    rows = [
        dict(id="ADJ2-01",
             claim="PRE-03 registers two adjudicators. A second pass was run and "
                   "the agreement between the two is reported, rather than one "
                   "replacing the other.",
             status="MEASURED",
             value="three-way crosswalked agreement %s percent, kappa %s over %s "
                   "classes; blind subset %s percent, kappa %s over %s classes"
                   % (a["three_way_all"]["agreement"], a["three_way_all"]["kappa"],
                      f"{a['three_way_all']['n']:,}",
                      a["three_way_blind"]["agreement"],
                      a["three_way_blind"]["kappa"],
                      f"{a['three_way_blind']['n']:,}"),
             n=f"{a['three_way_blind']['n']:,}",
             denominator=f"{a['message_classes']:,}",
             floor="not applicable, this row measures adjudication stability "
                   "rather than quoting a failure rate",
             dropped="%s message classes match a verdict disclosed in prose by "
                     "MORNING_REPORT.md before this pass ran, and are excluded "
                     "from the blind figure"
                     % f"{a['pre_disclosed_classes']:,}",
             derived_from="PRE-03",
             pinned_by_test="tests/test_adjudicate2.py::test_agreement_is_reported_both_ways",
             status_note="The second pass was performed by the same LLM agent as "
             "the first, under a published rule table, after a re-read without "
             "the first pass's verdicts. It is an intra-instrument "
             "repeatability check, not an independent human adjudication. It "
             "shows the rule table is applied reproducibly and surfaces "
             "unstable classes. It does not show either reading is correct, and "
             "a second human adjudicator remains outstanding.",
             notes="Two regexes were corrected after the first comparison run "
                   "because they failed to match the text they were written "
                   "for. The verdicts and rationales they carry were unchanged. "
                   "Recorded as a departure from strict blindness.",
             **common),
        dict(id="ADJ2-02",
             claim="The only adjudication decision that reaches a published rate "
                   "is binary: does a message class count toward the net "
                   "numerator. The two passes agree on that binary at this rate.",
             status="MEASURED",
             value="%s percent agreement, kappa %s over %s classes; blind subset "
                   "%s percent, kappa %s. The disagreement is one-directional: "
                   "pass 1 called net where pass 2 did not on %d classes, and "
                   "the reverse happened %d time(s)."
                   % (a["net_binary_all"]["agreement"],
                      a["net_binary_all"]["kappa"],
                      f"{a['net_binary_all']['n']:,}",
                      a["net_binary_blind"]["agreement"],
                      a["net_binary_blind"]["kappa"],
                      a["net_binary_blind"]["pass1_only"],
                      a["net_binary_blind"]["pass2_only"]),
             n=f"{a['net_binary_blind']['n']:,}",
             denominator=f"{a['message_classes']:,}",
             floor="not applicable, this row measures adjudication stability",
             dropped="same pre-disclosed exclusion as ADJ2-01",
             derived_from="ADJ2-01",
             pinned_by_test="tests/test_adjudicate2.py::test_consensus_only_keeps_agreements",
             status_note="The two passes used different vocabularies, five terms "
             "against three, and the crosswalk is published. Comparing on the "
             "coarser scale without it returned 16.62 percent, which measured "
             "the vocabulary and not the judgement. Both scales are reported.",
             **common),
        dict(id="ADJ2-03",
             claim="Net rates recomputed under the consensus rule, where a class "
                   "counts only if both passes called it net and every "
                   "disagreement drops to undecidable.",
             status="MEASURED",
             value="; ".join(
                 "%s pass1 %.2f percent, pass2 %.2f, consensus %.2f"
                 % (r.sop_class_name, r.pct_pass1, r.pct_pass2, r.pct_consensus)
                 for r in net.itertuples()),
             n=str(int(net["net_consensus"].sum())),
             denominator=str(int(net["objects"].sum())),
             floor="measured above the classes both passes agreed were floor. "
                   "Classes the passes disagreed about are undecidable and are "
                   "excluded from the numerator, so the consensus rate is a "
                   "lower bound on the single-pass rate rather than an "
                   "independent estimate of it.",
             dropped="every message class where the two passes disagreed is "
                     "excluded from the consensus numerator",
             derived_from="ADJ2-01,PRE-03,PRE-05",
             pinned_by_test="tests/test_adjudicate2.py::test_consensus_never_exceeds_either_pass",
             status_note="No first-pass verdict was edited. Both adjudications "
             "are published side by side. No net rate should be quoted from a "
             "single pass now that two exist.",
             **{k: v for k, v in common.items() if k != "source_file"},
             source_file="results/adjudication2/net_rates_two_pass.csv"),
    ]
    pending = RESULTS / "pending_ledger"
    pending.mkdir(parents=True, exist_ok=True)
    path = pending / "track_adjudicate2.json"
    path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return path


def main(argv=None) -> int:
    t = build()
    a = t["agreement"]
    print("message classes %d, pre-disclosed %d"
          % (a["message_classes"], a["pre_disclosed_classes"]))
    print("three-way  all %5.2f%% kappa %s | blind %5.2f%% kappa %s"
          % (a["three_way_all"]["agreement"], a["three_way_all"]["kappa"],
             a["three_way_blind"]["agreement"], a["three_way_blind"]["kappa"]))
    print("net binary all %5.2f%% kappa %s | blind %5.2f%% kappa %s"
          % (a["net_binary_all"]["agreement"], a["net_binary_all"]["kappa"],
             a["net_binary_blind"]["agreement"], a["net_binary_blind"]["kappa"]))
    print()
    print(t["net"][["sop_class_name", "objects", "pct_pass1", "pct_pass2",
                    "pct_consensus"]].to_string(index=False))
    print("wrote %s" % write(t))
    print("proposed %s" % propose_ledger(t))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
