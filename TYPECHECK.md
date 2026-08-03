# Type re-verification against PS3.3 2026c

Every Type designation the manuscript relies on, re-read from **the standard
itself**. The pass that raised this question confirmed Types against a
third-party rendering last synced 2024-04-18, roughly eight editions stale.
Nothing here fetches: `dicom-validator` pre-seeds the DocBook and the parsed
module and IOD tables for PS3.3 2026c so that no measurement depends on a network
fetch, and this reads that copy. Reproduce with `python -m colophon.typecheck`.

## Result: every Type reproduces

**0 of 17 assertions failed to reproduce.**

| tag | keyword | table | module | manuscript asserts | PS3.3 2026c | reproduces |
|---|---|---|---|---|---|---|
| `(0062,0008)` | SegmentAlgorithmType | C.8.20-4 | Segment Description Macro | 1 | 1 | yes |
| `(0062,0009)` | SegmentAlgorithmName | C.8.20.2 | Segmentation Image Module, inside Segment Sequence | 1C | 1C | yes |
| `(0062,0007)` | SegmentationAlgorithmIdentificationSequence | C.8.20.2 | Segmentation Image Module, inside Segment Sequence | 3 | 3 | yes |
| `(0062,0007)` | SegmentationAlgorithmIdentificationSequence | C.8.20.5 | Height Map Segmentation Image Module, not included by the Segmentation IOD | 1C | 1C | yes |
| `(0066,002F)` | AlgorithmFamilyCodeSequence | 10-19 | Algorithm Identification Macro | 1 | 1 | yes |
| `(0066,0036)` | AlgorithmName | 10-19 | Algorithm Identification Macro | 1 | 1 | yes |
| `(0066,0031)` | AlgorithmVersion | 10-19 | Algorithm Identification Macro | 1 | 1 | yes |
| `(0066,0030)` | AlgorithmNameCodeSequence | 10-19 | Algorithm Identification Macro | 3 | 3 | yes |
| `(0066,0032)` | AlgorithmParameters | 10-19 | Algorithm Identification Macro, tag corrected from the brief | 3 | 3 | yes |
| `(0024,0202)` | AlgorithmSource | 10-19 | Algorithm Identification Macro, tag corrected from the brief | 3 | 3 | yes |
| `(0008,0070)` | Manufacturer | C.7.5.1 | General Equipment Module | 2 | 2 | yes |
| `(0008,0070)` | Manufacturer | C.7.5.2 | Enhanced General Equipment Module | 1 | 1 | yes |
| `(0008,1090)` | ManufacturerModelName | C.7.5.2 | Enhanced General Equipment Module | 1 | 1 | yes |
| `(0018,1000)` | DeviceSerialNumber | C.7.5.2 | Enhanced General Equipment Module | 1 | 1 | yes |
| `(0018,1020)` | SoftwareVersions | C.7.5.2 | Enhanced General Equipment Module | 1 | 1 | yes |
| `(0018,1020)` | SoftwareVersions | C.7.5.1 | General Equipment Module | 3 | 3 | yes |
| `(0018,A001)` | ContributingEquipmentSequence | C.12.1 | SOP Common Module | 3 | 3 | yes |

Both tags the study brief gave wrongly are confirmed corrected:
`AlgorithmParameters` is (0066,0032) and `AlgorithmSource` is (0024,0202), each
Type 3 in the Algorithm Identification Macro. The split the lead finding rests on
is confirmed: **(0062,0009) is Type 1C inside Segment Sequence and (0062,0007) is
Type 3 there**, and the 1C form of (0062,0007) exists only in the Height Map
module, which the Segmentation IOD does not include.

## But a derived claim does not reproduce

A Type can be right while a sentence built on it is wrong, and one is.

The ceiling claim was written from **Enhanced General Equipment** alone. That
module has Usage M in **2 of
the 8 IODs measured**, which is the part that reproduces:
Parametric Map Storage, Segmentation Storage.

**General Equipment is a second equipment module and it has Usage M in
8 of 8.** In it,
`Manufacturer (0008,0070)` is **Type 2**,
so it shall be present in every one of the eight, though it may be zero length.
Model, serial and software are Type
3 there, so their
absence is legal.

| SOP class | equipment module | usage | table | Manufacturer | ModelName | DeviceSerialNumber | SoftwareVersions |
|---|---|---|---|---|---|---|---|
| Segmentation Storage | Enhanced General Equipment | M | C.7.5.2 | 1 | 1 | 1 | 1 |
| Segmentation Storage | General Equipment | M | C.7.5.1 | 2 | 3 | 3 | 3 |
| Parametric Map Storage | Enhanced General Equipment | M | C.7.5.2 | 1 | 1 | 1 | 1 |
| Parametric Map Storage | General Equipment | M | C.7.5.1 | 2 | 3 | 3 | 3 |
| RT Structure Set Storage | General Equipment | M | C.7.5.1 | 2 | 3 | 3 | 3 |
| Comprehensive SR Storage | General Equipment | M | C.7.5.1 | 2 | 3 | 3 | 3 |
| Comprehensive 3D SR Storage | General Equipment | M | C.7.5.1 | 2 | 3 | 3 | 3 |
| Grayscale Softcopy Presentation State Storage | General Equipment | M | C.7.5.1 | 2 | 3 | 3 | 3 |
| Key Object Selection Document Storage | General Equipment | M | C.7.5.1 | 2 | 3 | 3 | 3 |
| Real World Value Mapping Storage | General Equipment | M | C.7.5.1 | 2 | 3 | 3 | 3 |

**Consequence.** The sentence that no object outside the two Enhanced IODs can be
non-conformant on carrier grounds is **false**: an absent Manufacturer is a Type 2
violation in all eight. The corrected ceiling has three tiers rather than one:

1. **A non-empty value** is compelled for four equipment attributes in
   **2 of 8** IODs.
2. **Presence, possibly zero length**, is compelled for Manufacturer alone in
   **8 of 8**.
3. **Nothing at all** is compelled for model, serial or software version in the
   other **6 of 8**.

That is still a ceiling and a sharper one: outside two IODs the standard compels
the existence of a manufacturer string and never compels it to mean anything.

## What a reader checks this against

`results/typecheck/docbook_quotes.json` carries the DocBook neighbourhood of each
load-bearing tag, with the nearest preceding table caption, so the parsed Types
above can be checked against the standard's own text without re-running anything.
