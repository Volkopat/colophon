"""The gate. One command decides whether the package is submittable.

    python -m colophon.submit --final

It either writes the complete package and prints `READY`, or it writes nothing
and prints the ordered list of what is missing, each with the file and the field
it blocks. Exit non-zero when not ready.

Four things block it, and each is a class of defect that reached a shipped
package at least once:

1. an unfilled field, which is a placeholder that would ship as written;
2. a failing assertion, which is a venue requirement measured against the
   submitted file and not met;
3. an unmapped venue requirement, which is a hole in the checklist rather than
   a failure in the package;
4. a failing checklist row.

A draft build is the default and always writes, so the package can be read while
fields are still open.
"""
from __future__ import annotations

import argparse
import json

from . import assertions, submission, tokens
from .paths import RESULTS

OUT = RESULTS / "submission" / "gate.json"


def evaluate(final: bool) -> dict:
    blocking = []

    unfilled = tokens.unfilled()
    fields = tokens.load_fields()
    for key in unfilled:
        rec = fields[key]
        blocking.append({
            "kind": "unfilled field", "what": key,
            "files": ", ".join(rec.get("files", [])) or "unknown",
            "detail": rec.get("description", "")[:160]})

    # The package has to exist before it can be measured, so a draft is built
    # first and the assertions read that. A final build is attempted only once
    # nothing else blocks, because it raises rather than reporting.
    manifest = submission.build(final=False)
    report = assertions.run()
    for r in report["failed"]:
        blocking.append({
            "kind": "failing assertion", "what": r["name"],
            "files": ", ".join(r["artefacts"])[:90],
            "detail": "%s -- %s" % (r["value"], r["detail"][:140])})
    for e in report["errors"]:
        blocking.append({"kind": "assertion errored", "what": e["assertion"],
                         "files": "", "detail": e["error"][:160]})
    for hole in report["unmapped_requirements"]:
        blocking.append({"kind": "unmapped venue requirement", "what": hole,
                         "files": "results/submission/assertions.md",
                         "detail": "no row evaluates this"})

    checklist = (RESULTS / "submission" / "07_checklist.md").read_text(
        encoding="utf-8")
    for line in checklist.splitlines():
        if "**NO**" in line:
            blocking.append({"kind": "failing checklist row",
                             "what": line.split("|")[1].strip()[:80],
                             "files": "results/submission/07_checklist.md",
                             "detail": line.split("|")[3].strip()[:140]
                             if line.count("|") > 3 else ""})

    ready = not blocking
    if ready and final:
        manifest = submission.build(final=True)
        left = manifest["state"]["surviving_markers_in_bytes"]
        if left:
            blocking.append({"kind": "surviving placeholder",
                             "what": "%d markers" % left,
                             "files": "results/submission/",
                             "detail": "%d markers survived a final build"
                                       % left})
            ready = False

    return {"ready": ready, "final": final, "blocking": blocking,
            "assertions_evaluated": report["evaluated"],
            "assertions_passed": report["passed"],
            "fields_total": len(fields), "fields_unfilled": unfilled}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--final", action="store_true")
    args = ap.parse_args(argv)
    state = evaluate(final=args.final)
    OUT.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    if state["ready"]:
        print("READY")
        print("%d assertions evaluated, %d passed; %d fields, 0 unfilled"
              % (state["assertions_evaluated"], state["assertions_passed"],
                 state["fields_total"]))
        return 0
    print("NOT READY: %d blocking" % len(state["blocking"]))
    order = {"unfilled field": 0, "failing assertion": 1,
             "assertion errored": 2, "unmapped venue requirement": 3,
             "failing checklist row": 4, "surviving placeholder": 5}
    for i, b in enumerate(sorted(state["blocking"],
                                 key=lambda x: order.get(x["kind"], 9)), 1):
        print("%2d. %-28s %s" % (i, b["kind"], b["what"]))
        print("      file: %s" % (b["files"] or "n/a"))
        if b["detail"]:
            print("      %s" % b["detail"])
    print("\n%d assertions evaluated, %d passed"
          % (state["assertions_evaluated"], state["assertions_passed"]))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
