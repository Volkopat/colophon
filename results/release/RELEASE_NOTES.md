# Release notes, v1.0.1

First public release of the measurement harness for the manuscript
"Conformant and uninformative: producer attribution in 35,107 AI-derived DICOM
objects".

## What this release is for

The manuscript cites a **version DOI**, not a concept DOI, so that a reader
retrieves the state of the code the paper was written from. This tag is that
state.

## What the snapshot contains

**362 tracked files, 15.3 MB.** Measured with `git ls-files`, not estimated.
That is the measurement code, the tests, the claims ledger, every generated
results artefact, the six figures, the drafted Correction Proposal and the
assembled submission package.

**0 DICOM objects.** Every fetched object was deleted after validation,
which is a rule the project set before it fetched anything.

## What the snapshot deliberately excludes, and why

A Zenodo archive of a repository is a redistribution. This repository sits next
to material that is not ours to redistribute, and the exclusion is a decision
rather than an accident of what was in the working tree at tag time.

| path | size | why it is not in the snapshot |
|---|---|---|
| `_cache/census/records.jsonl` | 286.3 MB | per-object attribute values extracted from archive objects. Derived from the archive's own data, part of which is CC BY-NC, so redistributing it under this repository's MIT licence would be asserting a licence this project cannot grant. Regenerate with the census command. |
| `_cache/phase3/records.jsonl` | 56.6 MB | the same, for the Segmentation sample. |
| `_cache/air/` | 1.8 MB | the IHE AI Results supplement PDF. Third-party copyright. It is pinned by sha256 in the reference list and fetched from IHE, not shipped. |
| `_cache/dcmqi.git/` | 19.7 MB | a clone of somebody else's repository, vendored to read a constants header. Not ours to redistribute. |
| `*.dcm anywhere` | 0.0 MB | every fetched object was deleted after validation, as the project rule requires. None is tracked and none is in the snapshot. |

The licence mix of the measured classes is the reason the derived records are
out: **1,012 series of the archive are CC BY-NC**, and the per-object values the
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
