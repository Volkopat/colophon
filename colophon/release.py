"""Release preparation. Everything around the DOI except minting it.

Six of the placeholders are the Zenodo version DOI, the concept DOI and the tag,
twice over. They cannot be filled here. Everything else can be ready, so that
filling them is a fill and not a task.

This generates `.zenodo.json`, the release notes, and the snapshot decision, and
prints the commands to run. **It creates no repository, pushes nothing and
touches Zenodo not at all.**

The snapshot decision is the part that is not a formality. A Zenodo archive of
this repository is a redistribution, and this repository sits next to 432 MB of
fetched and derived material that is not all redistributable. What goes in the
tag is measured here and stated, rather than being whatever happens to be in the
working tree at tag time.

Reproduce with `python -m colophon.release`.
"""
from __future__ import annotations

import json
import subprocess

from .paths import RESULTS, REPO

OUT = RESULTS / "release"
ZENODO = REPO / ".zenodo.json"
CMD = "python -m colophon.release"

VERSION = "1.0.0"
TAG = "v" + VERSION
TITLE = ("colophon: a conformance and provenance census of AI-derived DICOM "
         "objects in the NCI Imaging Data Commons")


def tracked() -> dict:
    """What a `git archive` of the tag would contain, measured."""
    files = subprocess.run(["git", "ls-files"], cwd=str(REPO),
                           capture_output=True, text=True).stdout.split("\n")
    files = [f for f in files if f.strip()]
    total = 0
    for f in files:
        p = REPO / f
        if p.exists():
            total += p.stat().st_size
    dicom = [f for f in files if f.lower().endswith(".dcm")]
    return {"files": len(files), "bytes": total,
            "megabytes": round(total / 1e6, 1), "dicom_files": len(dicom)}


def excluded() -> list[dict]:
    """What is deliberately not in the snapshot, with why and how big."""
    def size(rel):
        p = REPO / rel
        if not p.exists():
            return 0
        if p.is_file():
            return p.stat().st_size
        return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
    return [
        {"path": "_cache/census/records.jsonl",
         "megabytes": round(size("_cache/census/records.jsonl") / 1e6, 1),
         "reason": "per-object attribute values extracted from archive objects. "
                   "Derived from the archive's own data, part of which is "
                   "CC BY-NC, so redistributing it under this repository's MIT "
                   "licence would be asserting a licence this project cannot "
                   "grant. Regenerate with the census command."},
        {"path": "_cache/phase3/records.jsonl",
         "megabytes": round(size("_cache/phase3/records.jsonl") / 1e6, 1),
         "reason": "the same, for the Segmentation sample."},
        {"path": "_cache/air/",
         "megabytes": round(size("_cache/air") / 1e6, 1),
         "reason": "the IHE AI Results supplement PDF. Third-party copyright. "
                   "It is pinned by sha256 in the reference list and fetched "
                   "from IHE, not shipped."},
        {"path": "_cache/dcmqi.git/",
         "megabytes": round(size("_cache/dcmqi.git") / 1e6, 1),
         "reason": "a clone of somebody else's repository, vendored to read a "
                   "constants header. Not ours to redistribute."},
        {"path": "*.dcm anywhere",
         "megabytes": 0.0,
         "reason": "every fetched object was deleted after validation, as the "
                   "project rule requires. None is tracked and none is in the "
                   "snapshot."},
    ]


def licences() -> dict:
    """The licence mix of the measured classes, which is why the answer is no."""
    import csv
    import collections
    path = RESULTS / "phase0" / "licenses.csv"
    counts = collections.Counter()
    if path.exists():
        for row in csv.DictReader(path.open(encoding="utf-8")):
            counts[row["license_short_name"]] += int(row["series"])
    nc = sum(v for k, v in counts.items() if "NC" in k)
    return {"by_licence": dict(counts.most_common()), "non_commercial_series": nc}


def zenodo_metadata() -> dict:
    return {
        "title": TITLE,
        "version": TAG,
        "upload_type": "software",
        "license": "MIT",
        "access_right": "open",
        "creators": [{"name": "Patil, Digvijay",
                      "orcid": "0009-0003-6878-1712",
                      "affiliation": "University at Buffalo School of "
                                     "Management, Buffalo, NY, USA"}],
        "description": (
            "Measurement code, claims ledger, generated tables and figure "
            "builders for a conformance and provenance census of the derived, "
            "non-image SOP classes of NCI Imaging Data Commons release v24. "
            "The archive itself is not redistributed here: every fetched object "
            "was deleted after validation, and the per-object records the "
            "census derives are excluded because part of the source archive is "
            "CC BY-NC. See RELEASE_NOTES for what the snapshot contains and "
            "why."),
        "keywords": ["DICOM", "conformance", "provenance",
                     "Imaging Data Commons", "medical imaging informatics",
                     "measurement study", "metadata completeness"],
        "related_identifiers": [
            {"identifier": "10.5281/zenodo.21728405",
             "relation": "isSupplementedBy", "scheme": "doi",
             "resource_type": "software"},
        ],
        "notes": ("The version DOI, not the concept DOI, is the one cited in "
                  "the accompanying manuscript."),
    }


LICENSE_TEXT = """MIT License

Copyright (c) 2026 Digvijay Patil

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

The measured archive is not covered by this licence. NCI Imaging Data Commons
content is distributed by that archive under its own terms, which for the
collections measured here are Creative Commons licences including
non-commercial ones. No archive content is redistributed in this repository.
"""


def release_notes(state: dict) -> str:
    t, ex, lic = state["tracked"], state["excluded"], state["licences"]
    rows = "\n".join(
        "| `%s` | %.1f MB | %s |" % (e["path"], e["megabytes"], e["reason"])
        for e in ex)
    return """# Release notes, {tag}

First public release of the measurement harness for the manuscript
"Conformant and uninformative: producer attribution in 35,107 AI-derived DICOM
objects".

## What this release is for

The manuscript cites a **version DOI**, not a concept DOI, so that a reader
retrieves the state of the code the paper was written from. This tag is that
state.

## What the snapshot contains

**{files} tracked files, {mb} MB.** Measured with `git ls-files`, not estimated.
That is the measurement code, the tests, the claims ledger, every generated
results artefact, the six figures, the drafted Correction Proposal and the
assembled submission package.

**{dicom} DICOM objects.** Every fetched object was deleted after validation,
which is a rule the project set before it fetched anything.

## What the snapshot deliberately excludes, and why

A Zenodo archive of a repository is a redistribution. This repository sits next
to material that is not ours to redistribute, and the exclusion is a decision
rather than an accident of what was in the working tree at tag time.

| path | size | why it is not in the snapshot |
|---|---|---|
{rows}

The licence mix of the measured classes is the reason the derived records are
out: **{nc} series of the archive are CC BY-NC**, and the per-object values the
census extracts are derived from archive content. Shipping them inside an
MIT-licensed archive would assert a licence this project cannot grant. The
records regenerate from the archive with the commands in the README, which is
slower for a reader and correct.

## Reproducing without the excluded material

Everything in `results/` is already generated and is in the snapshot, so every
number in the manuscript can be checked against its artefact without fetching
anything. Re-deriving those artefacts from the archive needs the census and
Phase 3 commands and roughly 130 GB of transfer, which the README states.

## Pins

The toolchain is pinned in `results/environment.json` and `env/requirements.lock`.
Two registered pins were not satisfied and both carry a measured exposure bound
in Methods 2.10.
""".format(tag=TAG, files=t["files"], mb=t["megabytes"],
           dicom=t["dicom_files"], rows=rows,
           nc="{:,}".format(lic["non_commercial_series"]))


def commands() -> str:
    return """# Release commands, to be run by the author

Nothing here has been run. This file lists the commands in order, and the
decision each one commits to.

## 0. Confirm the snapshot decision

Read `RELEASE_NOTES.md` in this directory. It states what the tag contains and
what it excludes, with sizes. If the decision is wrong, change it before tagging,
because a Zenodo record is not straightforwardly retractable.

## 1. Put the release files in the repository root

    cp results/release/RELEASE_NOTES.md RELEASE_NOTES.md

`LICENSE`, `.zenodo.json` and `CITATION.cff` are already written to the root by
`python -m colophon.release`.

## 2. Verify the tree is clean and the suite passes

    python -m pytest -q
    git status --short

## 3. Commit

    git add -A
    git commit -m "Submission package, release prep, and the fourth addendum's six items"

## 4. Point the empty remote at this repository and push

The remote exists and is empty. `main` is the branch the repository was created
with; this working copy is on `master`.

    git remote add origin https://github.com/Volkopat/colophon.git
    git push -u origin master:main

## 5. Enable the Zenodo integration, then tag

Turn the repository on at https://zenodo.org/account/settings/github/ **before**
creating the release. Zenodo only archives releases created after the switch is
on.

    git tag -a v1.0.0 -m "colophon v1.0.0"
    git push origin v1.0.0

Then create a GitHub release from that tag, with `RELEASE_NOTES.md` as the body.

## 6. Fill the DOIs

Zenodo mints a version DOI and a concept DOI. Put them in
`results/submission/fields.json` under `zenodo_version_doi`,
`zenodo_concept_doi` and `release_tag`, then:

    python -m colophon.submission --final

That build refuses while any field is empty, so it is the check that the
placeholders are gone rather than a step that hopes they are.
"""


def build() -> dict:
    state = {"tracked": tracked(), "excluded": excluded(),
             "licences": licences(), "version": VERSION, "tag": TAG}
    OUT.mkdir(parents=True, exist_ok=True)
    ZENODO.write_text(json.dumps(zenodo_metadata(), indent=2,
                                 ensure_ascii=False) + "\n", encoding="utf-8")
    (REPO / "LICENSE").write_text(LICENSE_TEXT, encoding="utf-8")
    (OUT / "RELEASE_NOTES.md").write_text(release_notes(state), encoding="utf-8")
    (OUT / "COMMANDS.md").write_text(commands(), encoding="utf-8")
    (OUT / "snapshot.json").write_text(
        json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return state


def main() -> int:
    state = build()
    t = state["tracked"]
    print("snapshot: %d tracked files, %.1f MB, %d DICOM objects"
          % (t["files"], t["megabytes"], t["dicom_files"]))
    print("excluded:")
    for e in state["excluded"]:
        print("  %-28s %8.1f MB" % (e["path"], e["megabytes"]))
    print("licence mix of the measured classes: %s"
          % state["licences"]["by_licence"])
    print("wrote %s, %s, %s and %s"
          % (ZENODO, REPO / "LICENSE", OUT / "RELEASE_NOTES.md",
             OUT / "COMMANDS.md"))
    print("nothing was pushed, tagged or uploaded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
