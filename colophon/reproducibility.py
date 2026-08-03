"""Does the figure set regenerate byte-identical. Measured, not asserted.

The submission checklist carried this row with the detail "the EPS creation
timestamp is stripped, which is the only non-deterministic byte matplotlib
writes into them". That is a mechanism and a belief about matplotlib. It is not
a diff, it names only the format that was known to pass, and the row said yes.

This builds the six figures **twice, in two separate processes, into two
separate directories**, and compares the bytes of every file in every format.
Two processes rather than two calls, because a within-process comparison shares
the font cache, the hash seed and every module-level default, which is most of
what makes rendering non-deterministic in the first place.

What it reports per format: how many files are identical, and for every file
that is not, the byte offset of the first difference and what is at it. A format
that does not reproduce is reported as not reproducing rather than dropped from
the row.

Reproduce with `python -m colophon.reproducibility`.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from .paths import RESULTS

OUT = RESULTS / "figures" / "reproducibility.json"
FORMATS = ("eps", "pdf", "png")
CMD = "python -m colophon.reproducibility"


def _build_into(directory: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ, COLOPHON_FIGURES_OUT=str(directory))
    return subprocess.run(
        [sys.executable, "-m", "colophon.figures"],
        env=env, capture_output=True, text=True,
        cwd=str(RESULTS.parent))


def _eps_into(directory: Path) -> subprocess.CompletedProcess:
    """EPS is written by the submission assembler, not by `colophon.figures`."""
    env = dict(os.environ, COLOPHON_FIGURES_OUT=str(directory),
               COLOPHON_SUBMISSION_FIGDIR=str(directory))
    code = ("from colophon import submission, figures;"
            "figures.build();"
            "submission.FIGDIR = figures.OUT;"
            "submission.figures_for_submission()")
    return subprocess.run([sys.executable, "-c", code], env=env,
                          capture_output=True, text=True, cwd=str(RESULTS.parent))


def _first_difference(a: bytes, b: bytes) -> dict:
    n = min(len(a), len(b))
    for i in range(n):
        if a[i] != b[i]:
            lo = max(0, i - 24)
            return {"offset": i,
                    "a": repr(a[lo:i + 24])[1:],
                    "b": repr(b[lo:i + 24])[1:]}
    return {"offset": n, "a": "shorter", "b": "longer",
            "note": "one file is a prefix of the other, lengths %d and %d"
                    % (len(a), len(b))}


def compare() -> dict:
    """Two builds, two directories, two processes, byte for byte."""
    with tempfile.TemporaryDirectory(prefix="colophon-repro-") as tmp:
        a, b = Path(tmp) / "a", Path(tmp) / "b"
        a.mkdir(); b.mkdir()
        runs = [_eps_into(a), _eps_into(b)]
        failed = [r for r in runs if r.returncode != 0]
        if failed:
            return {"ran": False,
                    "error": failed[0].stderr[-1200:] or failed[0].stdout[-1200:]}

        per_format, differing = {}, []
        for fmt in FORMATS:
            names = sorted(p.name for p in a.glob("*." + fmt))
            same = 0
            for name in names:
                da, db = (a / name).read_bytes(), (b / name).read_bytes()
                if da == db:
                    same += 1
                else:
                    rec = {"file": name, "format": fmt,
                           "bytes_a": len(da), "bytes_b": len(db)}
                    rec.update(_first_difference(da, db))
                    differing.append(rec)
            per_format[fmt] = {"files": len(names), "identical": same,
                               "differing": len(names) - same,
                               "reproducible": len(names) > 0 and same == len(names)}
        return {"ran": True, "formats": per_format, "differing_files": differing,
                "all_reproducible": all(v["reproducible"]
                                        for v in per_format.values()),
                "method": "two builds in two subprocesses into two temporary "
                          "directories, compared byte for byte",
                "command": CMD}


def summary(report: dict) -> str:
    if not report.get("ran"):
        return "the comparison did not run"
    bits = []
    for fmt in FORMATS:
        f = report["formats"].get(fmt)
        if not f:
            continue
        bits.append("%s %d of %d identical" % (fmt.upper(), f["identical"],
                                               f["files"]))
    text = "; ".join(bits)
    if report["differing_files"]:
        text += ". Differing: " + "; ".join(
            "%s at byte %d" % (d["file"], d["offset"])
            for d in report["differing_files"])
    return text


def main() -> int:
    report = compare()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    if not report["ran"]:
        print("the build failed:\n%s" % report["error"])
        return 1
    print(summary(report))
    for d in report["differing_files"]:
        print("  %-12s %s bytes vs %s, first difference at %d"
              % (d["file"], d["bytes_a"], d["bytes_b"], d["offset"]))
        print("      a: %s" % d["a"][:120])
        print("      b: %s" % d["b"][:120])
    print("wrote %s" % OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
