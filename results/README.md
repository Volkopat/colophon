# results

Every file here is evidence for a row in `ledger.csv`. The markdown write-ups
are emitted by the modules that compute the numbers, so a figure in the prose
cannot drift out of agreement with the table it came from. `tests/test_style.py`
checks that no file here is hand-typed except this one and `ai_use.md`.

## Default hardware and environment

Every `MEASURED` row in `ledger.csv` was produced on this machine unless its
`hardware` field says otherwise. Rows inherit this paragraph the way the
spine-gsps Appendix E rows do.

| | |
|---|---|
| Platform | Windows 11, 10.0.26200 |
| CPU | Intel64 Family 6 Model 198 Stepping 2, 24 logical cores |
| RAM | 63.5 GB |
| GPU | not used by any phase of this study |
| Python | 3.12.13, Anaconda build, MSC v.1942 64 bit |
| IDC index | release v24, `idc-index` 0.12.5, `idc-index-data` 24.2.2 |
| DICOM standard | PS3, 2025e |

Third-party validators, none of them built or modified by this project:

| tool | version as the binary reports it | how it is pinned |
|---|---|---|
| `dciodvfy`, dicom3tools | no version flag | snapshot 20260701065818, plus sha256 and mtime in `environment.json` |
| `dcmpschk`, DCMTK | `$dcmtk: dcmpschk v3.7.0 2025-12-15 $` | self-reported string, plus sha256 |
| `dcmdump`, DCMTK | `$dcmtk: dcmdump v3.7.0 2025-12-15 $` | self-reported string, plus sha256 |
| `dcmp2pgm`, DCMTK | `$dcmtk: dcmp2pgm v3.7.0 2025-12-15 $` | self-reported string, plus sha256 |
| `dicom-validator`, pydicom | 0.8.2 | `env/requirements.lock` |
| `highdicom` reader | 0.28.1 | `env/requirements.lock` |

These are the same binaries the spine-gsps paper used. A different build reports
different diagnostics, so substituting one would invalidate comparison across
phases and across the two papers. `colophon/paths.py` refuses to fall back to
anything on PATH and stops instead.

`environment.json` is regenerated on every run of `python -m colophon.index` and
carries the full snapshot including package versions, binary hashes and free
disk.

## Files

| file | what it is | produced by |
|---|---|---|
| `ledger.csv` | every claim, its status, its command, its floor, what it dropped | written incrementally by each module |
| `environment.json` | the pinning record | `colophon.envinfo` |
| `prior_art.md` | the recorded prior-art search, every query verbatim | `colophon.prior_art` |
| `prisma_s_appendix.md` | the search strategy reported PRISMA-S style, with the auditability rule and the gap list | `colophon.prisma` |
| `prisma_s_rows.csv` | the search table, one row per source and per query | `colophon.prisma` |
| `phase0_census.md` | the census of derived objects | `colophon.index` |
| `claim3_provenance.md` | producer identification | `colophon.provenance` |
| `ai_use.md` | LLM use declaration | hand-written, kept current |
| `phase0/*.csv` | the tables behind the write-ups | `colophon.index`, `colophon.provenance` |
| `claims_map.md` | every claim id joined to its ledger row and to the artefact carrying it, with the orphans, the uncited artefacts and the broken links | `colophon.claims_map` |
| `claims_map.csv` | the same join, one row per claim id | `colophon.claims_map` |

## Reading the ledger

`status` is one of MEASURED, VERIFIED, DERIVED, PENDING, LITERATURE, RETIRED.

A RETIRED row is a claim that was believed and is now known wrong. It is never
deleted, because the point of keeping it is that the number cannot creep back
in. `retired_reason` says why, `superseded_by` names its replacement.

`floor` is mandatory on any row quoting a rate. A failure rate without its floor
is not a number: a known-good object built by `highdicom` still trips `dciodvfy`
on at least one attribute, so a raw failure rate mixes real defects with
validator behaviour. Phase 0 rows carry "not applicable, no validator involved"
because they are metadata counts. Rows from Phase 2 onward carry a floor row id.

`dropped` is mandatory on every MEASURED row. A run that dropped nothing has to
say so, because a blank field and full coverage are indistinguishable to a
reader.
