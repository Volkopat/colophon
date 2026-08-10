"""Shared guards.

Two kinds of file are absent from a clean checkout of the public archive, and
neither absence is a failure:

- the census and Phase 3 caches, which are tens of gigabytes of IDC records and
  are rebuilt by running the phase, exactly as `test_tables.py` already handles
  with "run python -m colophon.tables first";
- the paths the archive deliberately excludes, listed with their reasons in
  `colophon.archive`.

Tests written against the repository were being run against the archive, and 17
of them failed on absences that are by design. They skip with the reason now, so
a reviewer who clones the archive and runs the suite sees what is not being
checked rather than a wall of red that means nothing.
"""
from __future__ import annotations

import pytest

from colophon import archive
from colophon.paths import REPO


def need(*relative_paths: str, run: str = "") -> None:
    """Skip unless every named path is present in this checkout."""
    missing = [p for p in relative_paths if not (REPO / p).exists()]
    if not missing:
        return
    why = archive.excluded(missing[0])
    if why:
        pytest.skip("%s is not in this checkout: %s. See README, 'What this "
                    "archive does not contain'." % (missing[0], why))
    pytest.skip("%s is not in this checkout; %s"
                % (", ".join(missing), run or "build it first"))


def need_census() -> None:
    need("_cache/census/records.jsonl", "_cache/census/manifest.csv",
         run="run `python -m colophon.census` to build the cache")


def need_phase3() -> None:
    need("_cache/phase3", run="run `python -m colophon.phase3` to build the cache")


def need_submission() -> None:
    need("results/submission/fields.json")
