# Table 1: the writer census, computed from census output

Every number here is read out of the objects, not out of the index. Reproduce
with `python -m colophon.tables`.

Source: `_cache/census/records.jsonl`, 242,058,765 bytes as of
2026-08-02T20:11:52, read at 2026-08-02T20:11:54. The census appends to that file
while this runs, so the read is deliberately defensive: 82,944
lines were seen and 0 were skipped as unparseable.

This supersedes the writer census in `results/table1_writers.md`, which infers a
writer from `Manufacturer` and `ManufacturerModelName` alone because those are
the only equipment attributes the idc-index dataframe carries. That table is
provisional by its own statement. This one is not, for the classes it covers.

## Which SOP classes are in this table

A class appears only when the census has recorded at least as many series as the
manifest holds for it. Completeness is judged on series, not objects, because
the manifest is a list of series and the census skips a series it has already
recorded, so a complete class stays complete and its counts stay fixed while the
rest of the census runs.

| sop_class_name | series_in_manifest | series_recorded | objects_recorded | state |
|---|---|---|---|---|
| Real World Value Mapping Storage | 20 | 20 | 20 | complete |
| Key Object Selection Document Storage | 40 | 40 | 40 | complete |
| Grayscale Softcopy Presentation State Storage | 1,086 | 1,086 | 1,086 | complete |
| Parametric Map Storage | 691 | 691 | 691 | complete |
| Comprehensive SR Storage | 2,118 | 2,118 | 2,118 | complete |
| Comprehensive 3D SR Storage | 5,408 | 5,408 | 5,408 | complete |
| RT Structure Set Storage | 19,358 | 19,358 | 19,358 | complete |
| Enhanced SR Storage | 262,883 | 54,223 | 54,223 | in flight |

**7 of 8 classes are complete** and are the whole of this
table. The 1 classes that are not complete contribute nothing, not
even a partial count.

## The attribution rule

Applied per object, in this order. The first rule that matches decides, and the
attribute that decided is recorded per row in the CSV.

1. `ImplementationClassUID (0002,0012)` equals `1.2.826.0.1.3680043.9.7433.1.1`, or `ImplementationVersionName (0002,0013)` matches `^highdicom`, names **highdicom**. highdicom/base.py, SOPClass.__init__ sets file_meta.ImplementationClassUID to the literal 1.2.826.0.1.3680043.9.7433.1.1 and file_meta.ImplementationVersionName to f'highdicom{__version__}'. Neither is conditional and neither is settable by a caller. Status: CONFIRMED from source, highdicom 0.28.1 as installed
2. `ImplementationClassUID (0002,0012)` equals `1.3.6.1.4.1.5962.99.2`, or `ImplementationVersionName (0002,0013)` matches `^PIXELMEDJAVA`, names **PixelMed**. com/pixelmed/dicom/VersionAndConstants.java: uidRoot 1.3.6.1.4.1.5962, uidQualifierForThisToolkit 99, uidQualifierForImplementationClassUID 2, and implementationVersionName = PIXELMEDJAVA + softwareVersion, where softwareVersion is 001. Applied by com/pixelmed/dicom/FileMetaInformation.java. Status: CONFIRMED from source, pixelmed source release 20260608
3. `ImplementationClassUID (0002,0012)` equals `n/a`, or `ImplementationVersionName (0002,0013)` matches `^OFFIS_DCMTK`, names **DCMTK**. DCMTK self-identifies in ImplementationVersionName as OFFIS_DCMTK_<version>. dcmqi serialises through DCMTK, so this names the backend and not the caller. Status: asserted from observed values, NOT source confirmed
4. `ImplementationClassUID (0002,0012)` equals `n/a`, or `ImplementationVersionName (0002,0013)` matches `^dcm4che`, names **dcm4che**. the toolkit's own name and release appear verbatim in ImplementationVersionName, for example dcm4che-1.4.27. Status: asserted from observed values, NOT source confirmed

If none of those match, and only then:

- a `ContributingEquipmentSequence (0018,A001)` item whose `Manufacturer` is exactly `Highdicom open-source contributors` names **highdicom**. highdicom/base_content.py, ContributingEquipment.for_highdicom, appended unconditionally by every concrete constructor. Status: CONFIRMED from source, highdicom 0.28.1 as installed

If nothing matches, the object is labelled `unresolved implementation
<ImplementationClassUID> / <ImplementationVersionName>` with the two values
recorded verbatim. It is not resolved to a toolkit and it is not merged with any
other identity.

Where `ImplementationClassUID` and `ImplementationVersionName` name different
toolkits, the object is labelled `file meta internally inconsistent` rather than resolved in favour
of either. That happened on 0 objects.

The file meta names the library that serialised the dataset. It is the strongest
available evidence about what wrote the bytes, and it is not evidence about what
produced the analysis. For an archive that re-encodes on ingest it names the
last writer rather than the first, which is exactly why the disagreement below
is worth counting.

## Writer per SOP class

| sop_class_name | writer | writer_evidence_status | objects | pct_of_sop_class |
|---|---|---|---|---|
| Comprehensive 3D SR Storage | highdicom | CONFIRMED from source, highdicom 0.28.1 as installed | 5,408 | 100.00 |
| Comprehensive SR Storage | unresolved implementation 1.3.6.1.4.1.22213.1.143 / 0.5 | recorded verbatim, not resolved to a toolkit | 1,656 | 78.19 |
| Comprehensive SR Storage | dcm4che | asserted from observed values, NOT source confirmed | 462 | 21.81 |
| Grayscale Softcopy Presentation State Storage | unresolved implementation 1.3.6.1.4.1.22213.1.143 / 0.5 | recorded verbatim, not resolved to a toolkit | 624 | 57.46 |
| Grayscale Softcopy Presentation State Storage | dcm4che | asserted from observed values, NOT source confirmed | 462 | 42.54 |
| Key Object Selection Document Storage | dcm4che | asserted from observed values, NOT source confirmed | 40 | 100.00 |
| Parametric Map Storage | highdicom | CONFIRMED from source, highdicom 0.28.1 as installed | 691 | 100.00 |
| RT Structure Set Storage | unresolved implementation 1.3.6.1.4.1.22213.1.143 / 0.5 | recorded verbatim, not resolved to a toolkit | 17,901 | 92.47 |
| RT Structure Set Storage | dcm4che | asserted from observed values, NOT source confirmed | 1,432 | 7.40 |
| RT Structure Set Storage | DCMTK | asserted from observed values, NOT source confirmed | 25 | 0.13 |
| Real World Value Mapping Storage | unresolved implementation 1.3.6.1.4.1.22213.1.143 / 0.5 | recorded verbatim, not resolved to a toolkit | 20 | 100.00 |

The full cross-tabulation, one row per SOP class, file-meta writer and
equipment-attribute writer, is in `table1_writers.csv`.

## Where the equipment attributes said nothing

11,128 of 28,721 objects carry equipment attributes that the
Phase 0 rule cannot attribute to any toolkit. The file meta names a toolkit for
8,423 of them. That is the measured gain from opening the
files, and it is the number the Phase 0 table said would have to be resolved in
Phase 2.

## Where the two sources disagree

An object is scored only when the toolkit named by the equipment attributes has
a file-meta signature that can be stated independently of this corpus. There are
three such toolkits:

| equipment-attribute writer | expected file-meta writer | how the expectation was established |
|---|---|---|
| highdicom | highdicom | CONFIRMED from source, highdicom 0.28.1 as installed |
| PixelMed | PixelMed | CONFIRMED from source, pixelmed source release 20260608 |
| dcmqi | DCMTK | asserted from observed values, NOT source confirmed |

Everything else is counted as `no expectation registered` and is never scored as agreeing
or disagreeing, because there is nothing to agree with.

| sop_class_name | equipment_writer | writer | verdict | expectation_status | objects |
|---|---|---|---|---|---|
| Comprehensive 3D SR Storage | highdicom | highdicom | agree | CONFIRMED from source, highdicom 0.28.1 as installed | 96 |
| Comprehensive SR Storage | PixelMed | unresolved implementation 1.3.6.1.4.1.22213.1.143 / 0.5 | disagree | CONFIRMED from source, pixelmed source release 20260608 | 1,292 |

**1,292 of 1,388 scored objects disagree.** The
disagreement rests on a signature that is a compile-time constant in the named
toolkit's own source, so it is not a matter of a loose pattern: the file meta on
those objects is not the file meta that toolkit writes.

What follows from that is left open. Either something other than the named
toolkit serialised the file, or the file meta was rewritten after the named
toolkit wrote it. Nothing measured here distinguishes the two, and this table
does not choose between them.

This is the same shape as the Phase 2 pilot finding in ledger row P2P-08, where
objects declaring dcmqi in the equipment attributes carried a file-meta
implementation that was not DCMTK.

## One implementation identity, several declared producers

Aggregated over the complete classes only. Every declared pair is listed, with
its object count, because a truncated list here would hide exactly the spread
the table exists to show.

| implementation_class_uid | implementation_version_name | objects | distinct_declared_equipment_pairs | declared_equipment |
|---|---|---|---|---|
| 1.3.6.1.4.1.22213.1.143 | 0.5 | 20,201 | 10 | Open Health Imaging Foundation / OHIF-XNAT Viewer 3.2.0 (16,184); PixelMed / XSLT from di3data csv extract (1,292); Siemens Corporate Research / DIRS2 (780); Varian Medical Systems / ARIA RadOnc (520); Elekta / GammaPlan (484); Varian Medical Systems / ARIA RTM (472); MIM Software Inc. / MIM (241); (empty) / (empty) (104); CoreLab Partners, Inc. / LocationDesignatorSynthesizer (104); https://github.com/QIICR/Slicer-SUVFactorCalculator / (empty) (20) |
| 1.2.826.0.1.3680043.9.7433.1.1 | highdicom0.20.0 | 2,701 | 1 | IDC / (empty) (2,701) |
| 1.2.826.0.1.3680043.9.7433.1.1 | highdicom0.27.0 | 2,007 | 4 | Sybil / (empty) (970); Gevaert Lab Converted By Imaging Data Commons / GBM360 (691); IDC / (empty) (345); Expert annotation from TCIA / (empty) (1) |
| 1.2.40.0.13.1.1.1 | dcm4che-1.4.35 | 1,168 | 5 | ADAC / Pinnacle3 (800); (empty) / Vision 7.3 - External Beam Planning (275); MIM Software Inc. / MIM (58); ADAC / Vision 7.3 - External Beam Planning (34); Plastimatch / Plastimatch (1) |
| 1.2.826.0.1.3680043.9.7433.1.1 | highdicom0.26.1 | 1,090 | 1 | Expert annotation from TCIA / (empty) (1,090) |
| 1.2.40.0.13.1.1 | dcm4che-1.4.27 | 924 | 5 | Siemens Corporate Research / DIRS2 (462); Philips / (empty) (252); GE MEDICAL SYSTEMS / (empty) (84); TOSHIBA / (empty) (84); SIEMENS / (empty) (42) |
| 1.2.40.0.13.1.1.1 | dcm4che-1.4.34 | 304 | 2 | MIM Software Inc. / MIM (264); (empty) / (empty) (40) |
| 1.2.826.0.1.3680043.9.7433.1.1 | highdicom0.21.1 | 205 | 1 | IDC / (empty) (205) |
| 1.2.826.0.1.3680043.9.7433.1.1 | highdicom0.22.0 | 96 | 1 | Leica Biosystems / Aperio ImageScope converted with highdicom (96) |
| 1.2.276.0.7230010.3.0.3.6.9 | OFFIS_DCMTK_369 | 25 | 1 | PMOD Technologies / PMOD (25) |

A one-to-one mapping would mean the two carriers say the same thing twice. A
many-to-one mapping means one serialising implementation is carrying several
different producer claims.

The reverse direction holds too. These declared producers sit behind more than
one file-meta writer, counting toolkits rather than releases, so several
releases of one toolkit behind one declared producer is not listed here:

| declared_Manufacturer | declared_ManufacturerModelName | objects | distinct_file_meta_writers | file_meta_writers |
|---|---|---|---|---|
| Siemens Corporate Research | DIRS2 | 1,242 | 2 | unresolved implementation 1.3.6.1.4.1.22213.1.143 / 0.5 (780); dcm4che (462) |
| MIM Software Inc. | MIM | 563 | 2 | dcm4che (322); unresolved implementation 1.3.6.1.4.1.22213.1.143 / 0.5 (241) |
| (empty) | (empty) | 144 | 2 | unresolved implementation 1.3.6.1.4.1.22213.1.143 / 0.5 (104); dcm4che (40) |

## Two caveats on the equipment-attribute rule

The Phase 0 rule is reused verbatim, from `colophon.writers.writer_of`, so that
the comparison is against the rule as registered rather than against a rule
tuned for this table. Two of its behaviours are visible here and are reported
rather than corrected:

- its pattern for QIICR Reporting is `fedorov/reporting|slicer`, and the
  `slicer` alternative matches any 3D Slicer extension URL. Objects whose
  `Manufacturer` is `https://github.com/QIICR/Slicer-SUVFactorCalculator` are
  therefore labelled `QIICR Reporting via 3D Slicer` on a substring alone.
- it was written against the index, where `Manufacturer` and
  `ManufacturerModelName` are the series-level values. Here it is fed each
  object's own values, which is the same rule on stronger input.

## What was dropped

Classes that are not complete are excluded entirely and are named in the
coverage table above with their recorded counts. Segmentation Storage is outside
the census scope altogether and appears nowhere in this table.

0 lines of `records.jsonl` were skipped as
unparseable and 0 objects were
skipped because their census status was not OK. Both counts are gross, over the
whole file, not only over the complete classes.
