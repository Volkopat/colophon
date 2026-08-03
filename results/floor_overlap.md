# Phase 1, minimum scope: writer floor-set overlap

One fixture, two writers, the four classes the design nominates. Emitted,
decoded, compared, then validated. Reproduce with `python -m colophon.floor`.

## The number

| sop_class | validator | comparable | W1 classes | W2 classes | shared | union | Jaccard |
|---|---|---|---|---|---|---|---|
| SEG BINARY | dciodvfy | yes | 0 | 1 | 0 | 1 | 0.000 |
| SEG BINARY | dicom-validator | yes | 6 | 7 | 6 | 7 | 0.857 |
| SEG FRACTIONAL | dciodvfy | no, W2 cannot emit | 0 | 0 | 0 | 0 | n/a |
| SEG FRACTIONAL | dicom-validator | no, W2 cannot emit | 6 | 0 | 0 | 6 | n/a |
| Parametric Map | dciodvfy | no, W2 cannot emit | 1 | 0 | 0 | 1 | n/a |
| Parametric Map | dicom-validator | no, W2 cannot emit | 9 | 0 | 0 | 9 | n/a |
| TID 1500 SR | dciodvfy | yes | 0 | 0 | 0 | 0 | 1.000 |
| TID 1500 SR | dicom-validator | yes | 1 | 1 | 1 | 1 | 1.000 |

Jaccard is over sets of normalised `message_class_id`, not raw lines.

## Distinct message classes per object

| writer | sop_class | validator | distinct message classes |
|---|---|---|---|
| dcmqi | SEG BINARY | dciodvfy | 1 |
| dcmqi | SEG BINARY | dicom-validator | 7 |
| dcmqi | TID 1500 SR | dicom-validator | 1 |
| highdicom | Parametric Map | dciodvfy | 1 |
| highdicom | Parametric Map | dicom-validator | 9 |
| highdicom | SEG BINARY | dicom-validator | 6 |
| highdicom | SEG FRACTIONAL | dicom-validator | 6 |
| highdicom | TID 1500 SR | dicom-validator | 1 |

## What is comparable, and what is not

Two of the four nominated classes are not shared, because W2 cannot emit them:

- **SEG FRACTIONAL**: dcmqi itkimage2segimage offers --segmentationType <binary|labelmap> only. It has no FRACTIONAL code path, so FRACTIONAL is a highdicom-only cell.
- **Parametric Map**: dcmqi itkimage2paramap exited with 'ERROR: Conversion failed.' on the fixture under four metadata variants and both float32 and float64 input. It ships no schema in the vendored build and emits no diagnostic beyond that line. Recorded as an emission gap, not as a defect in either tool.

Their floors are highdicom-only and non-transferable, in the same way the
design already treats GSPS and KOS.

A third caveat applies to the SR cell. Both writers produce TID 1500, but not in
the same SOP class: highdicom emits **Comprehensive 3D SR**
(1.2.840.10008.5.1.4.1.1.88.34) and dcmqi emits **Enhanced SR**
(1.2.840.10008.5.1.4.1.1.88.22). TID 1500 may legitimately be carried in either,
so the comparison is valid at the template level, but the two objects are
scored against different IOD tables and the overlap has to be read with that in
mind.

## Tool builds

```
{
  "dciodvfy": {
    "path": "D:\\Radiology\\Spine Labeling\\tools\\dicom3tools\\dciodvfy.exe",
    "reported_version": "no version flag, pinned by sha256 and mtime",
    "snapshot": "20260701065818",
    "sha256_first_64MiB": "d931cded1048a2fdf6823bb534c722bb31513a8466107f0cf5d7037a9061f69a",
    "registered_pin": "1.00~20240118131615-1",
    "pin_satisfied": false
  },
  "dicom-validator": {
    "version": "0.8.2",
    "edition_used": "2026c"
  },
  "highdicom": {
    "version": "0.28.1",
    "pydicom": "3.0.2",
    "registered_pin": "0.28.0",
    "pin_satisfied": false
  },
  "dcmqi": {
    "tag": "v1.5.4",
    "revision": "a102298",
    "banner": "dcmqi repository URL: https://github.com/QIICR/dcmqi revision: a102298 tag: v1.5.4",
    "source": "vendored in 3D Slicer",
    "never_label_as": "1.5.6"
  }
}
```

Two registered pins are not satisfied on this machine and the deviation is
recorded rather than papered over:

- The design registers **dicom3tools 1.00~20240118131615-1**. The build present
  is snapshot **20260701065818**, the one the spine-gsps paper used. The 2024
  build predates changelog relaxations at 231003, 241003 and 241114, so it will
  flag conformant LABELMAP and TILED_FULL objects that the 2026 build does not.
  Neither appears in this fixture, so the deviation does not affect this
  measurement, but it must be closed before any corpus stratum is scored.
- The design registers **highdicom 0.28.0**. The build present is **0.28.1**,
  which is what this repository and the prior paper pin.

Neither substitution was silent, and neither is treated as satisfying the pin.

## What was dropped

Nothing was sampled. Six objects were emitted and every one was run through both
validators. The nine-variant ladder, Arm B corpus adjudication, the sampling
frame and PixelMed integration are all out of scope for this phase and are not
started. No IDC object was fetched.
