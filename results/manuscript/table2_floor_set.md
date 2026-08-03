# Table 2: the floor set, per writer and per message class

A known-good object trips validators. Every rate this project quotes has to name
the floor it is quoted against, and this is that floor. Reproduce with `python -m colophon.tables`.

Sources: `results/floor_set.csv` for the floor itself, and
`results/phase2/census_message_classes.csv`, snapshot 2026-08-02T04:19:05,
7,404 rows, for corpus context.

## The floor, per cell

A cell is one writer, one SOP class, one validator. Cells where a writer drew
nothing are listed with zero, not omitted: a floor of zero is the finding that
makes a single scalar floor indefensible, and an absent row would read as
missing data.

| writer | sop_class | validator | cell_single_writer | message_classes |
|---|---|---|---|---|
| dcmqi | SEG BINARY | dciodvfy | no | 1 |
| dcmqi | SEG BINARY | dicom-validator | no | 7 |
| dcmqi | TID 1500 SR | dciodvfy | no | 0 |
| dcmqi | TID 1500 SR | dicom-validator | no | 1 |
| highdicom | Parametric Map | dciodvfy | yes | 1 |
| highdicom | Parametric Map | dicom-validator | yes | 9 |
| highdicom | SEG BINARY | dciodvfy | no | 0 |
| highdicom | SEG BINARY | dicom-validator | no | 6 |
| highdicom | SEG FRACTIONAL | dciodvfy | yes | 0 |
| highdicom | SEG FRACTIONAL | dicom-validator | yes | 6 |
| highdicom | TID 1500 SR | dciodvfy | no | 0 |
| highdicom | TID 1500 SR | dicom-validator | no | 1 |

## The message classes

Message templates are normalised by `colophon.floor.normalise`, which strips
tags, UIDs, frame and item indices and quoted values, and keeps attribute names,
module names and Type designations, because those are what identify the
diagnostic rather than what varies between instances of it. The unit of count is
the distinct message class, never the raw line.

`corpus_objects` is how many objects in the census snapshot drew the same
message class. A zero there means the class was not seen in the classes the
snapshot covers, which is not the same as absence from the archive: Segmentation
Storage is outside the census scope entirely, so no Segmentation-only message
class can appear in that column whatever its true frequency. The CSV carries a
`corpus_context` column naming the SOP class and the snapshot denominator behind
each of those counts, and the full untruncated template.

| writer | sop_class | validator | message_class_id | severity_as_emitted | shared_with | corpus_objects | message_template |
|---|---|---|---|---|---|---|---|
| highdicom | SEG BINARY | dicom-validator | 380880930b44 | ERROR | dcmqi | 0 | Module <Multi-frame Functional Groups> (TAG) (Per-Frame Functional Groups Sequence) Tag (TAG) (Plane Position Sequence) is unexpec ... |
| highdicom | SEG BINARY | dicom-validator | 6f01abd4f319 | ERROR | dcmqi | 0 | Module <Multi-frame Functional Groups> (TAG) (Shared Functional Groups Sequence) Tag (TAG) (Plane Orientation Sequence) is unexpec ... |
| highdicom | SEG BINARY | dicom-validator | 972394b5bb82 | ERROR | dcmqi | 0 | Module <Multi-frame Functional Groups> (TAG) (Per-Frame Functional Groups Sequence) Tag (TAG) (Segment Identification Sequence) is ... |
| highdicom | SEG BINARY | dicom-validator | d0eabe730084 | ERROR | dcmqi | 0 | Module <Multi-frame Functional Groups> (TAG) (Per-Frame Functional Groups Sequence) Tag (TAG) (Frame Content Sequence) is unexpect ... |
| highdicom | SEG BINARY | dicom-validator | d81147d20e87 | ERROR | dcmqi | 691 | Module <Multi-frame Functional Groups> (TAG) (Shared Functional Groups Sequence) Tag (TAG) (Pixel Measures Sequence) is unexpected |
| highdicom | SEG BINARY | dicom-validator | f782376ec325 | ERROR | dcmqi | 0 | Module <Multi-frame Functional Groups> (TAG) (Per-Frame Functional Groups Sequence) Tag (TAG) (Derivation Image Sequence) is unexp ... |
| highdicom | SEG FRACTIONAL | dicom-validator | 380880930b44 | ERROR | neither, this writer only | 0 | Module <Multi-frame Functional Groups> (TAG) (Per-Frame Functional Groups Sequence) Tag (TAG) (Plane Position Sequence) is unexpec ... |
| highdicom | SEG FRACTIONAL | dicom-validator | 6f01abd4f319 | ERROR | neither, this writer only | 0 | Module <Multi-frame Functional Groups> (TAG) (Shared Functional Groups Sequence) Tag (TAG) (Plane Orientation Sequence) is unexpec ... |
| highdicom | SEG FRACTIONAL | dicom-validator | 972394b5bb82 | ERROR | neither, this writer only | 0 | Module <Multi-frame Functional Groups> (TAG) (Per-Frame Functional Groups Sequence) Tag (TAG) (Segment Identification Sequence) is ... |
| highdicom | SEG FRACTIONAL | dicom-validator | d0eabe730084 | ERROR | neither, this writer only | 0 | Module <Multi-frame Functional Groups> (TAG) (Per-Frame Functional Groups Sequence) Tag (TAG) (Frame Content Sequence) is unexpect ... |
| highdicom | SEG FRACTIONAL | dicom-validator | d81147d20e87 | ERROR | neither, this writer only | 691 | Module <Multi-frame Functional Groups> (TAG) (Shared Functional Groups Sequence) Tag (TAG) (Pixel Measures Sequence) is unexpected |
| highdicom | SEG FRACTIONAL | dicom-validator | f782376ec325 | ERROR | neither, this writer only | 0 | Module <Multi-frame Functional Groups> (TAG) (Per-Frame Functional Groups Sequence) Tag (TAG) (Derivation Image Sequence) is unexp ... |
| highdicom | Parametric Map | dciodvfy | e4c7fa2d56f7 | Error | neither, this writer only | 482 | Error - Missing attribute Type 2C Conditional Element=<Laterality> Module=<GeneralSeries> |
| highdicom | Parametric Map | dicom-validator | 095ddfcf33c6 | ERROR | neither, this writer only | 691 | Module <Multi-frame Functional Groups> (TAG) (Shared Functional Groups Sequence) Tag (TAG) (Pixel Value Transformation Sequence) i ... |
| highdicom | Parametric Map | dicom-validator | 380880930b44 | ERROR | neither, this writer only | 0 | Module <Multi-frame Functional Groups> (TAG) (Per-Frame Functional Groups Sequence) Tag (TAG) (Plane Position Sequence) is unexpec ... |
| highdicom | Parametric Map | dicom-validator | 49e18e26dc42 | ERROR | neither, this writer only | 691 | Module <Multi-frame Functional Groups> (TAG) (Shared Functional Groups Sequence) Tag (TAG) (Frame VOI LUT Sequence) is unexpected |
| highdicom | Parametric Map | dicom-validator | 679be57db212 | ERROR | neither, this writer only | 691 | Module <Multi-frame Functional Groups> (TAG) (Shared Functional Groups Sequence) Tag (TAG) (Parametric Map Frame Type Sequence) is ... |
| highdicom | Parametric Map | dicom-validator | 6f01abd4f319 | ERROR | neither, this writer only | 0 | Module <Multi-frame Functional Groups> (TAG) (Shared Functional Groups Sequence) Tag (TAG) (Plane Orientation Sequence) is unexpec ... |
| highdicom | Parametric Map | dicom-validator | 93da22cb4196 | ERROR | neither, this writer only | 691 | Module <Multi-frame Functional Groups> (TAG) (Shared Functional Groups Sequence) Tag (TAG) (Real World Value Mapping Sequence) is ... |
| highdicom | Parametric Map | dicom-validator | d0eabe730084 | ERROR | neither, this writer only | 0 | Module <Multi-frame Functional Groups> (TAG) (Per-Frame Functional Groups Sequence) Tag (TAG) (Frame Content Sequence) is unexpect ... |
| highdicom | Parametric Map | dicom-validator | d81147d20e87 | ERROR | neither, this writer only | 691 | Module <Multi-frame Functional Groups> (TAG) (Shared Functional Groups Sequence) Tag (TAG) (Pixel Measures Sequence) is unexpected |
| highdicom | Parametric Map | dicom-validator | f782376ec325 | ERROR | neither, this writer only | 0 | Module <Multi-frame Functional Groups> (TAG) (Per-Frame Functional Groups Sequence) Tag (TAG) (Derivation Image Sequence) is unexp ... |
| highdicom | TID 1500 SR | dicom-validator | 434c42b05bff | ERROR | dcmqi | 0 | Module <SR Document Content> (TAG) (Content Sequence) / (TAG) (Content Sequence) / (TAG) (Content Sequence) / (TAG) (Referenced SO ... |
| dcmqi | SEG BINARY | dciodvfy | cc372fb8c40c | Error | neither, this writer only | 0 | Error - Missing attribute Type 2 Required Element=<ClinicalTrialCoordinatingCenterName> Module=<ClinicalTrialSeries> |
| dcmqi | SEG BINARY | dicom-validator | 380880930b44 | ERROR | highdicom | 0 | Module <Multi-frame Functional Groups> (TAG) (Per-Frame Functional Groups Sequence) Tag (TAG) (Plane Position Sequence) is unexpec ... |
| dcmqi | SEG BINARY | dicom-validator | 6f01abd4f319 | ERROR | highdicom | 0 | Module <Multi-frame Functional Groups> (TAG) (Shared Functional Groups Sequence) Tag (TAG) (Plane Orientation Sequence) is unexpec ... |
| dcmqi | SEG BINARY | dicom-validator | 6f56c1b01548 | ERROR | neither, this writer only | 0 | Module <Clinical Trial Series> Tag (TAG) (Clinical Trial Coordinating Center Name) is missing |
| dcmqi | SEG BINARY | dicom-validator | 972394b5bb82 | ERROR | highdicom | 0 | Module <Multi-frame Functional Groups> (TAG) (Per-Frame Functional Groups Sequence) Tag (TAG) (Segment Identification Sequence) is ... |
| dcmqi | SEG BINARY | dicom-validator | d0eabe730084 | ERROR | highdicom | 0 | Module <Multi-frame Functional Groups> (TAG) (Per-Frame Functional Groups Sequence) Tag (TAG) (Frame Content Sequence) is unexpect ... |
| dcmqi | SEG BINARY | dicom-validator | d81147d20e87 | ERROR | highdicom | 691 | Module <Multi-frame Functional Groups> (TAG) (Shared Functional Groups Sequence) Tag (TAG) (Pixel Measures Sequence) is unexpected |
| dcmqi | SEG BINARY | dicom-validator | f782376ec325 | ERROR | highdicom | 0 | Module <Multi-frame Functional Groups> (TAG) (Per-Frame Functional Groups Sequence) Tag (TAG) (Derivation Image Sequence) is unexp ... |
| dcmqi | TID 1500 SR | dicom-validator | 434c42b05bff | ERROR | highdicom | 0 | Module <SR Document Content> (TAG) (Content Sequence) / (TAG) (Content Sequence) / (TAG) (Content Sequence) / (TAG) (Referenced SO ... |

## Single-writer cells, non-transferable by construction

4 of the 12
cells are single-writer, because dcmqi could not emit the class at all:

- **SEG FRACTIONAL**: dcmqi itkimage2segimage offers --segmentationType <binary|labelmap> only. It has no FRACTIONAL code path, so FRACTIONAL is a highdicom-only cell.
- **Parametric Map**: dcmqi itkimage2paramap exited with 'ERROR: Conversion failed.' on the fixture under four metadata variants and both float32 and float64 input. It ships no schema in the vendored build and emits no diagnostic beyond that line. Recorded as an emission gap, not as a defect in either tool.

A floor measured in a single-writer cell describes one writer and transfers to
nobody. It is marked `cell_single_writer = yes` in the CSV and carries the reason
in `single_writer_reason`, so the cell cannot be read as agreement between two
writers who never both ran.

## Overlap between the two writers

Jaccard over sets of normalised `message_class_id`, four decimal places.

| sop_class | validator | comparable | highdicom_classes | dcmqi_classes | shared | union | jaccard | vacuous |
|---|---|---|---|---|---|---|---|---|
| SEG BINARY | dciodvfy | yes | 0 | 1 | 0 | 1 | 0.0000 | no |
| SEG BINARY | dicom-validator | yes | 6 | 7 | 6 | 7 | 0.8571 | no |
| SEG FRACTIONAL | dciodvfy | no, dcmqi cannot emit it | 0 | 0 | 0 | 0 | n/a | no |
| SEG FRACTIONAL | dicom-validator | no, dcmqi cannot emit it | 6 | 0 | 0 | 6 | n/a | no |
| Parametric Map | dciodvfy | no, dcmqi cannot emit it | 1 | 0 | 0 | 1 | n/a | no |
| Parametric Map | dicom-validator | no, dcmqi cannot emit it | 9 | 0 | 0 | 9 | n/a | no |
| TID 1500 SR | dciodvfy | yes | 0 | 0 | 0 | 0 | 1.0000 | yes |
| TID 1500 SR | dicom-validator | yes | 1 | 1 | 1 | 1 | 1.0000 | no |

The SEG BINARY value under dicom-validator is **0.8571**, that is
6 shared of 7 in the union. It is quoted to
four places on purpose. An earlier measurement put it at 1.0 and concluded that
dicom-validator's floor transfers between writers where dciodvfy's does not.
That was an artefact of this project's own parser, which captured only indented
findings and so discarded every finding on a tag without parents. Ledger row
F1-03-prev carries the retired claim and F1-10 carries the defect. With the
parser fixed the highdicom set is a strict subset of the dcmqi set and neither
validator's floor transfers.

The TID 1500 SR row under dciodvfy is marked vacuous: both sets are empty, so
the Jaccard of 1.0 is agreement that carries no information about whether the
two floors would agree if either writer drew anything.

A further caveat on the SR cell, from ledger row F1-05: both writers produce TID
1500 but not in the same SOP class. highdicom emits Comprehensive 3D SR and
dcmqi emits Enhanced SR. The comparison holds at the template level and does not
hold at the IOD level.

## What was dropped

Nothing. Six objects were emitted in Phase 1 and every one was run through both
validators, and every message class either produced is in the CSV. The corpus
context column is the only sampled quantity here, and it is bounded by the
census snapshot named above rather than by any selection made in this table.
