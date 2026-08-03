# colophon

A conformance and provenance census of AI-derived DICOM objects in the NCI
Imaging Data Commons.

A measurement study. It trains nothing, fixes nothing, and counts things.

## What it measures

IDC release v24 holds 481,750 derived-object series, 504,727 instances, 18.72 TB,
publicly downloadable with no login, no access request and no egress fee. This
repository asks three falsifiable questions about them.

1. **Conformance.** What fraction fail `dciodvfy`, `dcmpschk` and
   `dicom-validator`, measured against a stated validator floor, broken down by
   SOP class and by `analysis_result_id`.
2. **Validator disagreement.** On what fraction of objects, and on which
   attribute classes, do independent validators disagree, and in which
   direction.
3. **Provenance.** Do these objects identify their producer.

Claim 3 is the cheapest to run and it is done first, entirely from the index,
with zero bytes downloaded.

## What this archive does not contain

This repository is the harness that produces the measurements. It is not the
paper. Four things are deliberately absent, and their absence is stated here
rather than left to be inferred from a directory that is not there.

- **The assembled submission package**, `results/submission/`: the cover letter,
  the title page and its author-held field values, the two manuscript copies as
  shipped, and the Word conversions. The manuscript *sources* under
  `results/manuscript/` are here, because the ledger's `source_file` column
  points into them and an archive whose audit trail dangles is worse than one
  that carries a draft.
- **Project correspondence and working instructions.** The briefs, addendums and
  status reports that directed the work, and the agent instructions file. None of
  it produces a number. What the tooling did, and what controls make its output
  checkable, is in `results/ai_use.md`, which is here.
- **`_ref/`.** Third-party papers and a prior harness, which are not ours to
  redistribute. The prior work is cited in the reference list instead.
- **Scratch state.** Overnight run state and id scratch files.

Two test modules, `tests/test_submission.py` and `tests/test_addendum04.py`,
assert properties of the submission package. On a clone of this archive they skip
with that reason rather than failing, because the package they assert against is
not here. Every other test runs, and the ledger rows that name those two modules
still resolve to a test that exists.

## Status

| phase | what | state |
|---|---|---|
| Prior art | recorded search, queries in the ledger | done, `results/prior_art.md` |
| Phase 0 | census and provenance from the index, no downloads | done, `results/phase0_census.md`, `results/claim3_provenance.md` |
| Panel | the measurement instrument, fixed before any floor | done, `results/panel.json` |
| Phase 1 | validator floor from known-good objects, per SOP class | not started |
| Phase 2 | exhaustive validation of the six small classes | not started |
| Phase 3 | stratified sample of the large classes | not started |

## Headline so far

Both DICOM equipment-identity attributes are populated on essentially every
derived series, so the provenance question is not one of missing attributes. It
is what the present values name, and they do not agree with each other.

Declared identity partitions exhaustively into four buckets:

| what the declared pair names | series | share |
|---|---|---|
| an encoding library, and nothing else | 416,427 | 86.44 percent |
| **the producing entity, its model, and the converter** | **21,721** | **4.51 percent** |
| something else: a named model, a scanner, a planning system, a viewer | 37,454 | 7.77 percent |
| absent or NA | 6,148 | 1.28 percent |

The second row is the finding. `tcga_sbu_til_maps` declares Manufacturer
`Stony Brook University converted by Imaging Data Commons` and model
`TIL Inception-V4 2022 converted by Imaging Data Commons`. `tcga_gbm360`
declares `Gevaert Lab Converted By Imaging Data Commons` and `GBM360`. Producing
lab, producing model and converter, all three, in the equipment attributes.

So IDC already has a working convention for the thing an absence-based reading
would call missing, and applies it to 4.51 percent of its own holdings. The
claim is therefore not that the archive fails to record producers. It is that
**several incompatible conventions coexist in one archive curated by one team**,
and a consumer cannot tell from the attributes which convention an object
follows. The 378,153 TotalSegmentator series declare `QIICR` and
`https://github.com/QIICR/dcmqi`, naming TotalSegmentator nowhere. `nlst_sybil`
puts the model name in `Manufacturer` and leaves the model field absent.
`eay131_tumor_annotations` names a viewer. One encoding tool appears under six
distinct spellings across 411,865 series. Even inside the working convention,
one analysis result writes "Converted By" and the other writes "converted by".

Whether the producing analysis is recorded elsewhere in these objects, in
`ContributingEquipmentSequence` or the algorithm identification attributes, is
not answerable from the index and is measured in Phases 2 and 3. Nothing here
scores any object as non-conformant.

## Two denominators, always

`analysis_result_id` records that IDC ingested a series as an analysis computed
over another collection. 463,543 of 481,750 derived series carry one,
96.22 percent. Both numbers are reported throughout, because neither is the
AI-derived population: the attributed set includes objects contoured by people
through a viewer, and the unattributed remainder includes 3,115 RT Structure Set
series from Pinnacle, ARIA, MIM and GammaPlan, which are radiotherapy planning
contours. A claim about AI results quoted against the derived denominator counts
those.

## The measurement panel

Fixed on 2026-08-01, before any floor was measured, because a panel chosen after
seeing results is not a panel. Two axes, never merged into a single pass or
fail.

**Axis 1, conformance.** `dciodvfy`, `dicom-validator`, `dcmpschk` for
presentation states, PixelMed `DicomSRValidator` for structured reports.

**Axis 2, reference implementation parse.** dcmqi `segimage2itkimage`,
`tid1500reader` and `paramap2itkimage`, the `highdicom` reader, and `dcmp2pgm`
for presentation states. A reference implementation refusing to parse is
evidence of a different kind from a validator complaint: it is what a user
experiences.

Axis 2 is **asymmetric and informative only on failure.** dcmqi is declared on
411,865 series, so dcmqi reading them back is a round trip and not a test. If
dcmqi cannot read objects dcmqi wrote, that is a strong result. If it reads all
of them, that establishes nothing. Independence is declared rather than assumed:
`dcmpschk` and `dcmp2pgm` are both DCMTK and count as one opinion, and
`dciodvfy` and PixelMed share an author.

## A prediction, recorded before Phase 1

Ledger row `PRE-01`, written before a single object was emitted or fetched:
claim 1 will return largely null. SR will pass because IDC validates its own SR
with PixelMed, and SEG will pass because dcmqi wrote it. That is the control
that makes claim 3 land rather than a failure of the study. The sentence the
paper will carry is that these objects are syntactically impeccable, validated
by the archive's own tooling, and still cannot tell you what algorithm produced
them.

If claim 1 instead returns a substantial failure rate, `PRE-01` is wrong and
stays in the ledger as a wrong prediction.

## Rules this repository is built under

- **Conformance is scored by third-party tools only.** `dciodvfy` from
  dicom3tools, `dcmpschk` from DCMTK, `dicom-validator` from pydicom, and
  `highdicom`'s reader as a fourth opinion. We build the harness around them.
  We never decide an object is non-conformant because we think it is. Where a
  validator's output is ambiguous we report the ambiguity rather than resolving
  it.
- **Every number has a ledger row.** `results/ledger.csv` carries the claim, its
  status, the exact command that produced it, the source file, the floor, and
  what the run dropped. Withdrawn claims stay in the ledger with the reason.
- **Every rate names its floor.** A known-good object built by `highdicom` still
  trips `dciodvfy` on at least one attribute. A failure rate quoted without its
  floor is not a number, and `colophon.ledger.rates_without_floor` enforces it.
- **Everything is pinned.** Tool binaries by version string where they have one
  and by sha256 where they do not, Python packages in `env/requirements.lock`,
  the IDC index version, the dicom3tools snapshot, the DICOM standard edition,
  the hardware. Written to `results/environment.json` on every run.
- **Aggregate, do not rank.** Results are reported by SOP class and by
  `analysis_result_id`. There is no leaderboard of which group ships the worst
  objects. The finding is that nobody publishes this measurement.
- **Log what was dropped.** Every phase states what it sampled, truncated or
  skipped, in the output and in the ledger. Silent truncation reads as full
  coverage.

## Reproducing

Needs Python 3.12 and the pinned validator binaries. Phase 0 needs neither the
binaries nor the network beyond installing `idc-index`, which ships the index
locally.

```
conda create -y -n colophon python=3.12
conda activate colophon
pip install -r env/requirements.lock

python -m colophon.paths          # confirm the pinned binaries resolve
python -m colophon.prior_art      # record the prior-art search
python -m colophon.index          # Phase 0 census
python -m colophon.provenance     # claim 3
python -m colophon.ledger         # ledger summary and the floor check
pytest -q
```

`python -m colophon.paths` refuses to fall back to whatever is on PATH. If a
binary is missing it says so and stops, because a different build of `dciodvfy`
or DCMTK reports different diagnostics and would make cross-phase comparison
meaningless.

## Layout

```
colophon/
  index.py        Phase 0, idc-index queries, zero downloads
  provenance.py   claim 3
  prior_art.py    the recorded prior-art search
  ledger.py       the claims ledger and its floor check
  envinfo.py      the pinning record
  paths.py        where everything lives, and the refusal to substitute binaries
results/
  ledger.csv          every claim, with its command and its floor
  environment.json    the pins
  prior_art.md        the search, with every query verbatim
  phase0_census.md    the census
  claim3_provenance.md
  ai_use.md           LLM use declaration
  phase0/*.csv        the tables behind the write-ups
```

## Prior work this extends

`spine-gsps` (Zenodo 10.5281/zenodo.21728405) supplies the validator invocation
patterns, the claims-ledger discipline and the version-pinning appendix that
this project copies. Its finding that a from-scratch conformant object still
draws one `dciodvfy` error, on a Type 2C the validator cannot evaluate, is the
reason every rate here has to carry a floor.

## Licence

MIT. The IDC data this measures is Creative Commons, per collection, recorded in
`results/phase0/licenses.csv`.
