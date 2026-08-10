"""What the public archive contains, defined once.

The archive published to Zenodo is not this repository. It carries the harness
that produces the measurements and leaves out the paper, the correspondence that
directed the work, and third-party material that is not ours to redistribute.

That list existed twice: as a shell command typed by hand when the export was
built, and as an assumption inside several tests that a file named in the ledger
is a file on disk. The two disagreed, and the disagreement shipped: the archive
for v1.0.0 failed 17 of its own tests, because tests written against the
repository were run against the archive.

It is defined here now. `export()` builds the archive and the tests ask this
module whether a missing file is missing by design.

Reproduce with `python -m colophon.archive --export DIR`.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

from .paths import REPO

CMD = "python -m colophon.archive --export DIR"

# Paths, relative to the repository root, that the public archive does not
# carry. Each one says why, because an exclusion without a reason is
# indistinguishable from an omission.
EXCLUDED: dict[str, str] = {
    # The paper. The archive is cited as the reproduction harness, not as the
    # manuscript, and the title page carries author-held values.
    "results/submission": "the assembled submission package",
    # The instructions and correspondence that directed the work. None of it
    # produces a number; what the tooling did is in results/ai_use.md.
    "CLAUDE.md": "agent instructions",
    "COLOPHON_BRIEF.md": "the project brief",
    "COLOPHON_ADDENDUM_01.md": "project correspondence",
    "COLOPHON_ADDENDUM_02.md": "project correspondence",
    "COLOPHON_ADDENDUM_03.md": "project correspondence",
    "COLOPHON_ADDENDUM_04.md": "project correspondence",
    "MORNING_REPORT.md": "internal status report",
    "REPORT.md": "internal status report",
    # Working state.
    "scratch": "overnight run state",
    "scratch_ids.txt": "id scratch file",
    "scripts": "a helper for reading the prior paper's PDF, on no measurement path",
    # Never tracked, listed so the reason is recorded with the others.
    "_ref": "third-party papers and a prior harness, not ours to redistribute",
}


def excluded(path: str | Path) -> str | None:
    """The reason `path` is absent from the archive, or None if it belongs."""
    rel = str(path).replace("\\", "/").lstrip("./")
    for name, why in EXCLUDED.items():
        if rel == name or rel.startswith(name + "/"):
            return why
    return None


def in_archive() -> bool:
    """True when the running checkout is the archive rather than the repository.

    Keyed on the submission package, which the archive never carries and the
    repository always does once a package has been built.
    """
    return not (REPO / "results" / "submission").exists()


def export(dest: Path) -> dict:
    """Write the public archive to `dest` from the current commit."""
    dest = Path(dest)
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    tar = subprocess.run(["git", "archive", "HEAD"], cwd=REPO,
                         capture_output=True)
    if tar.returncode != 0:
        raise RuntimeError(tar.stderr.decode("utf-8", "replace")[-400:])
    subprocess.run(["tar", "-x", "-C", str(dest)], input=tar.stdout, check=True)
    removed = []
    for name in EXCLUDED:
        target = dest / name
        if target.is_dir():
            shutil.rmtree(target)
            removed.append(name)
        elif target.exists():
            target.unlink()
            removed.append(name)
    return {"dest": str(dest), "removed": removed,
            "files": sum(1 for _ in dest.rglob("*") if _.is_file()),
            "command": CMD}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--export", metavar="DIR", required=True)
    args = ap.parse_args(argv)
    report = export(Path(args.export))
    print("wrote %d files to %s" % (report["files"], report["dest"]))
    print("removed %d excluded paths: %s"
          % (len(report["removed"]), ", ".join(report["removed"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
