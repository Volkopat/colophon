"""Absence and universal claims, and whether anything computed backs them.

Item 2c of the fourth addendum was one instance of a class: a sentence asserting
that something is nowhere, written from memory, in a paper whose whole method is
that nothing is written from memory. Every defect external review found in this
package came from the same place.

This finds the rest. It reads the manuscript, the cover letter, the tables and
the figure legends, extracts every sentence that asserts an absence or a
universal, and reports for each whether a ledger row backs it and whether that
row's command establishes the absence as opposed to establishing something
adjacent to it.

**It reports. It changes nothing.** A sweep that edits as it goes cannot be read
afterwards to see what it found.

Three verdicts:

- `backed`: the sentence cites a ledger row, and that row's own value or
  claim states the same absence or universal.
- `adjacent`: the sentence cites a row, and the row establishes something
  nearby rather than the thing asserted. A row counting how many objects carry
  an attribute is adjacent to, not the same as, a claim that none does.
- `unbacked`: no ledger row is cited in the sentence at all.

The verdict is mechanical and deliberately crude. `adjacent` is not an
accusation, it is a request that a human read the row. The sweep's value is the
list, not the labels.

Reproduce with `python -m colophon.absence`.
"""
from __future__ import annotations

import csv
import json
import re

from . import ledger
from .paths import RESULTS

OUT_MD = RESULTS / "manuscript" / "absence_claims.md"
OUT_CSV = RESULTS / "manuscript" / "absence_claims.csv"
CMD = "python -m colophon.absence"

SOURCES = [
    ("results/manuscript/abstract.md", "abstract"),
    ("results/manuscript/abstract_venue.md", "abstract, venue form"),
    ("results/manuscript/introduction.md", "introduction"),
    ("results/manuscript/methods.md", "methods"),
    ("results/manuscript/results.md", "results"),
    ("results/manuscript/discussion.md", "discussion"),
    ("results/manuscript/front_matter.md", "front matter"),
    ("results/manuscript/figures.md", "figure legends"),
    ("results/manuscript/tables.md", "tables"),
    ("results/submission/00_cover_letter.md", "cover letter"),
]

# The words that make a sentence an absence or a universal claim. Ordered so the
# report can say which one fired.
TRIGGERS = [
    "in no case", "does not appear", "is not present", "no object", "not one",
    "nothing", "none", "never", "no value", "no validator", "no claim",
    "every", "all of", "always", "cannot", "zero",
]
# Words that make a trigger a figure of speech rather than a claim about the
# data. `none of the above` and `every reader` are not measurements.
NOT_A_CLAIM = re.compile(
    r"none of the (?:three|two)\b|nothing here|nothing in this section|"
    r"every reader|every one of them is|never written|"
    r"none is offered|nothing is offered", re.I)

LEDGER_ID = re.compile(r"\b([A-Z][A-Z0-9]{0,5}-[0-9]{2,4}[a-z\-]*)\b")
SENTENCE = re.compile(r"[^.!?]*[.!?]")

# What makes an absence claim a claim about the archive rather than about the
# paper's own conventions. "No leaderboard is drawn" is a rule this project set
# itself; "no object carries the sequence" is a measurement. Only the second
# kind can be wrong about the world, and separating them is what keeps the
# sweep readable instead of a long list of undifferentiated prose.
DATA_SHAPED = re.compile(
    r"\(\d{4},[0-9A-Fa-f]{4}\)"
    r"|\b\d{1,3}(?:,\d{3})+\b"
    r"|\b\d+\.\d+ percent\b"
    r"|\bSegmentation\b|\bParametric Map\b|\bComprehensive\b|\bGSPS\b"
    r"|\bKey Object Selection\b|\bRT Structure Set\b|\bReal World Value\b"
    r"|\bsegments?\b|\bobjects?\b|\bseries\b|\bcollections?\b"
    r"|\banalysis[- ]result\b|\battribute\b|\bvalidator\b")


def _sentences(text: str):
    """Sentences with their line numbers, markdown stripped enough to read."""
    for n, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith(("|", "#", "```")):
            continue
        yield n, stripped


def _blocks(text: str):
    """Paragraphs, so a sentence split across wrapped lines stays whole."""
    lines = text.splitlines()
    buf, start = [], 1
    for n, line in enumerate(lines, 1):
        if line.strip() and not line.strip().startswith(("|", "#", "```")):
            if not buf:
                start = n
            buf.append(line.strip())
        else:
            if buf:
                yield start, " ".join(buf)
            buf = []
    if buf:
        yield start, " ".join(buf)


def sweep() -> dict:
    rows = {r["id"]: r for r in ledger.load()}
    findings, scanned = [], 0
    for rel, label in SOURCES:
        path = RESULTS.parent / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for line_no, block in _blocks(text):
            for sentence in SENTENCE.findall(block) or [block]:
                s = sentence.strip()
                if not s:
                    continue
                scanned += 1
                low = s.lower()
                fired = [t for t in TRIGGERS if t in low]
                if not fired or NOT_A_CLAIM.search(s):
                    continue
                cited = [i for i in LEDGER_ID.findall(s) if i in rows]
                verdict, note = "unbacked", "no ledger row is cited in the sentence"
                if cited:
                    verdict, note = "adjacent", (
                        "cited row exists; its value does not restate the "
                        "absence, so a human should read it")
                    for rid in cited:
                        row = rows[rid]
                        blob = " ".join([row["claim"], row["value"],
                                         row["status_note"], row["notes"]]).lower()
                        if any(t in blob for t in fired):
                            verdict, note = "backed", (
                                "row %s states the same absence or universal"
                                % rid)
                            break
                kind = "data" if DATA_SHAPED.search(s) else "procedure"
                findings.append({
                    "file": rel, "section": label, "line": line_no,
                    "kind": kind,
                    "trigger": fired[0], "sentence": " ".join(s.split())[:300],
                    "ledger_rows_cited": ",".join(cited),
                    "verdict": verdict, "note": note,
                })
    counts, by_kind = {}, {}
    for f in findings:
        counts[f["verdict"]] = counts.get(f["verdict"], 0) + 1
        key = "%s/%s" % (f["kind"], f["verdict"])
        by_kind[key] = by_kind.get(key, 0) + 1
    return {"sentences_scanned": scanned, "claims_found": len(findings),
            "by_verdict": counts, "by_kind_and_verdict": by_kind,
            "unbacked_data_claims": [f for f in findings
                                     if f["kind"] == "data"
                                     and f["verdict"] == "unbacked"],
            "findings": findings,
            "sources": [s for s, _ in SOURCES], "triggers": TRIGGERS,
            "command": CMD}


def render(report: dict) -> str:
    out = [
        "# Absence and universal claims, and what backs them\n",
        "Generated by `%s`. **This sweep reports and changes nothing.**\n" % CMD,
        "%d sentences scanned across %d documents; %d assert an absence or a "
        "universal. Verdicts: %s.\n"
        % (report["sentences_scanned"], len(report["sources"]),
           report["claims_found"],
           ", ".join("%s %d" % (k, v)
                     for k, v in sorted(report["by_verdict"].items()))),
        "`backed` means the cited ledger row states the same absence. "
        "`adjacent` means a row is cited and states something nearby, which is "
        "a request that a human read it rather than an accusation. `unbacked` "
        "means the sentence cites no row, which for a rhetorical sentence is "
        "fine and for a measurement is not.\n",
        "Claims are split by **kind**. A `data` claim asserts something about "
        "the archive or the measurement and can be wrong. A `procedure` claim "
        "asserts something about what this paper does, such as that no "
        "leaderboard is drawn, and is a rule the project set itself. Counts by "
        "kind and verdict: %s.\n"
        % ", ".join("%s %d" % (k, v)
                    for k, v in sorted(report["by_kind_and_verdict"].items())),
        "| file | line | kind | verdict | trigger | rows | sentence |",
        "|---|---|---|---|---|---|---|",
    ]
    order = {"unbacked": 0, "adjacent": 1, "backed": 2}
    kind_order = {"data": 0, "procedure": 1}
    for f in sorted(report["findings"],
                    key=lambda r: (kind_order.get(r["kind"], 9),
                                   order.get(r["verdict"], 9), r["file"], r["line"])):
        out.append("| `%s` | %d | %s | %s | %s | %s | %s |"
                   % (f["file"].replace("results/", ""), f["line"], f["kind"],
                      f["verdict"], f["trigger"],
                      f["ledger_rows_cited"] or "none",
                      f["sentence"].replace("|", "/")))
    return "\n".join(out) + "\n"


def main() -> int:
    report = sweep()
    OUT_MD.write_text(render(report), encoding="utf-8")
    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(report["findings"][0]))
        w.writeheader()
        w.writerows(report["findings"])
    print("scanned %d sentences, found %d absence or universal claims"
          % (report["sentences_scanned"], report["claims_found"]))
    for key, n in sorted(report["by_kind_and_verdict"].items()):
        print("  %-22s %d" % (key, n))
    print("wrote %s and %s" % (OUT_MD, OUT_CSV))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
